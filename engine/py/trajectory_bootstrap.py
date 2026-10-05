# -*- coding: utf-8 -*-
"""TD-Bootstrap aus der ECHTEN Trajektorie (Knopf `MOSAIC_BOOTSTRAP_SOURCE=trajectory`).

Nutzer-Entscheid 2026-10-05 ("mach mir auch b03 in verschiedenen tiefen"),
Grundlage `evaluations/PREREG_v35_window.md` par.12a: der heutige Bootstrap
(`bootstrap_value`) ist ein SIMULIERTER Netz-Rollout und liegt im Brier gegen
den Ausgang praktisch auf dem rohen Netzwert JETZT; der Suchwert `root_q` eines
echten spaeteren Records derselben Seite trifft den Ausgang dort besser.

Dieses Modul ist bewusst torch-frei (nur Standardbibliothek), damit die reine
Suchfunktion ohne Netz- und Cache-Umgebung testbar ist
(`tools/tests/test_trajectory_bootstrap.py`). Der Knopf selbst wird in
`file_cache_key._bootstrap_trajectory_horizon_key` gelesen (BEIDE
Cache-Schluessel), die Bauschleife (`corpus_dataset.MosaicDataset.__init__`)
ruft `trajectory_bootstrap_values` einmal je Korpusdatei.

Was der Knopf aendert und was nicht: NUR `values_wdl` (das WDL-Wertziel) auf
Records mit gespeichertem `bootstrap_value` in vollstaendigen Partien; die
Blend-Formel `TD_LAMBDA * bvp + (1 - TD_LAMBDA) * Ausgang` bleibt, nur `bvp`
kommt aus einer anderen Quelle. Unberuehrt: die tanh-Ziele (`values`,
`points`, `opp_points`), `wdl_outcome`, das `root_q`-Feld (und damit die
λ-Mischung in `apply_value_target_lambda`, die danach in train.py laeuft),
Masken und `value_weights`.

Zweite Quelle (par.14, Arm v35-b04, `MOSAIC_BOOTSTRAP_SOURCE=margin`):
`margin_bootstrap_value` -- sigmoid(Endmarge / b) mit der realisierten
Endmarge aus Sicht des Ziehers; dieselbe Record-Menge und dieselbe
Blend-Formel, nur eine andere Quelle fuer `bvp`.

Val-Satz: train.py baut Train- und Val-Datensatz (und ihre Caches) ueber
dieselbe Bauschleife, der Knopf wirkt also auf beide gleich. Der Val-Brier
rechnet trotzdem gegen den UNGEBLENDETEN Ausgang `wdl_outcome`
(train.py:1046-1051, Maske `wdl_outcome >= 0`), nicht gegen das Ziel -- er
bleibt damit zwischen einem Arm mit und einem ohne Knopf vergleichbar;
`val_vloss` dagegen nicht (anderes Ziel).
"""
from __future__ import annotations

import math


def _round_of(record) -> int:
    """Runde eines Records aus `state.round`; fehlt sie, harter Fehler.

    Ohne Runde laesst sich der Abstand nicht bestimmen, und ein stiller
    Rueckfall auf "kein spaeterer Record" verschoebe das Ziel unbemerkt auf den
    Ausgang.
    """
    rd = (record.get("state") or {}).get("round")
    if rd is None:
        raise ValueError("Record ohne state.round -- Trajektorien-Bootstrap nicht bestimmbar")
    return int(rd)


def trajectory_bootstrap_lookup(records_of_game, index, horizon_rounds) -> float | None:
    """Suchwert des ersten spaeteren Records derselben Seite mindestens
    `horizon_rounds` Runden spaeter, oder None.

    `records_of_game`: die Records EINER Partie (gleiche `game_id`) in der
    Reihenfolge, in der sie in der Datei stehen. `index`: Position des
    Records r in dieser Liste. Gesucht wird der ERSTE Record s hinter r mit

    - `s["player"] == r["player"]` (gleiche Seite, `root_q` ist aus Sicht des
      Ziehers -- dieselbe Lesart wie die λ-Mischung in
      `MosaicDataset.apply_value_target_lambda`),
    - `s.state.round >= r.state.round + horizon_rounds`,
    - `s["root_q"]` vorhanden (fehlt bei Ein-Aktion-Zuegen),
    - `s["dice_phase"]` nicht True (Wuerfelphase: kuenftige Wuerfelplatten,
      die der Zustand nicht zeigt, PREREG_asymmetric_selfplay.md par.5d).

    Rueckgabe ist `root_q` von s im RECORD-Raum, also eine Gewinnwahr-
    scheinlichkeit in [0,1] (der Remap auf [-1,1] passiert erst beim Cache-Bau
    fuer das `root_q`-Feld, corpus_dataset.py "root_q_l.append(... * 2.0 - 1.0)";
    hier wird nichts remappt).

    DIE TIEFE k IST EINE OBERGRENZE, KEIN PFLICHTABSTAND (Nutzer-Hinweis
    2026-10-05: "r4->r5 braucht wenn ueberhaupt nur eine"). Die wirksame Tiefe
    ist min(k, verbleibende Runden): gibt es keinen solchen Record mehr, weil
    das Partieende naeher als k Runden liegt (z. B. ab Runde 4 bei k = 2, ab
    Runde 3 bei k = 3), ist die Rueckgabe None, und der Aufrufer setzt den
    ECHTEN AUSGANG als Bootstrap ein. Das ist dort die beste Quelle, kein
    Notbehelf: der Ausgang ist der Wert, den jeder spaetere Suchwert nur
    schaetzt.

    Aufwand: lineare Suche ab `index + 1`, sie endet am ersten Treffer. Weil
    die Runden in der Datei aufsteigen, liegt der Treffer nach den Records von
    hoechstens k Runden; ohne Treffer laeuft sie bis zum Partieende, das dann
    ohnehin nah ist. Korrektheit haengt NICHT an der aufsteigenden Ordnung.
    """
    if not isinstance(horizon_rounds, int) or horizon_rounds < 1:
        raise ValueError(f"horizon_rounds={horizon_rounds!r} muss eine ganze Zahl >= 1 sein")
    record = records_of_game[index]
    player = record["player"]
    target_round = _round_of(record) + horizon_rounds
    for later_index in range(index + 1, len(records_of_game)):
        later = records_of_game[later_index]
        if later.get("player") != player:
            continue
        if later.get("dice_phase") is True:
            continue
        root_q = later.get("root_q")
        if root_q is None:
            continue
        if _round_of(later) < target_round:
            continue
        return float(root_q)
    return None


def trajectory_bootstrap_values(game_data, horizon_rounds) -> list:
    """`trajectory_bootstrap_lookup` fuer jeden Record einer Korpusdatei.

    `game_data`: die flache Record-Liste einer Datei (`load_records`). Die
    Records werden nach `game_id` gruppiert, innerhalb der Gruppe in
    Dateireihenfolge (stabil; die Schreiber legen die Records einer Partie
    ohnehin zusammenhaengend und in Zugreihenfolge ab, die Gruppierung macht
    das Ergebnis davon aber unabhaengig). Ein Ausflug traegt eine eigene
    `game_id` und ist damit eine eigene Partie.

    Rueckgabe: Liste gleicher Laenge wie `game_data`, je Record der spaetere
    Suchwert in [0,1] oder None (kein spaeterer Record innerhalb der Partie,
    Aufrufer nimmt den Ausgang).
    """
    positions_by_game: dict = {}
    for file_index, record in enumerate(game_data):
        positions_by_game.setdefault(record.get("game_id"), []).append(file_index)
    out: list = [None] * len(game_data)
    for positions in positions_by_game.values():
        records_of_game = [game_data[i] for i in positions]
        for game_index, file_index in enumerate(positions):
            out[file_index] = trajectory_bootstrap_lookup(records_of_game, game_index, horizon_rounds)
    return out


def add_trajectory_counts(total: dict, part) -> dict:
    """Summiert eine Zaehlung {runde: [spaeterer Record, Ausgang, ohne
    bootstrap_value]} in `total` (in place, auch zurueckgegeben). `part`
    None (Block lag schon, nichts gebaut) aendert nichts. Runden-Schluessel
    werden auf int normiert (aus JSON/pickle koennen sie als str kommen)."""
    if not part:
        return total
    for rd, counts in part.items():
        slot = total.setdefault(int(rd), [0, 0, 0])
        for i in range(3):
            slot[i] += int(counts[i])
    return total


def format_trajectory_counts(counts: dict, horizon_rounds) -> list:
    """Druckzeilen der Zaehlung, eine Kopfzeile plus eine Zeile je Runde."""
    lines = [f"🔧 Trajektorien-Bootstrap (Obergrenze {horizon_rounds}) je Runde, nur "
             f"vollstaendige Partien -- spaeterer Record / Ausgang / ohne bootstrap_value:"]
    for rd in sorted(counts):
        later, outcome, no_bv = counts[rd]
        lines.append(f"   Runde {rd}: {later} / {outcome} / {no_bv}")
    return lines


def margin_bootstrap_value(final_margin, scale) -> float:
    """Margen-Bootstrap (par.14, Arm v35-b04): sigmoid(final_margin / scale).

    `final_margin`: realisierte Endmarge in Punkten aus Sicht des Ziehers,
    genau wie `corpus_dataset.final_margin_of_step` sie rechnet
    (`scores_unclamped[p] - scores_unclamped[1-p]`, Rueckfall `scores`).
    `scale`: b in Punkten, endlich und > 0. Marge 0 ergibt 0,5, Marge +b
    ergibt sigmoid(1), Marge -b ergibt 1 - sigmoid(1).

    Harte Fehler: Skala <= 0 oder nicht endlich, Marge nicht endlich (NaN heisst
    "Ausgang unbekannt", dort gibt es keinen Blend und der Aufrufer darf diese
    Funktion nicht erreichen). Numerisch stabil fuer grosse |Marge / b|.
    """
    scale = float(scale)
    if not (math.isfinite(scale) and scale > 0.0):
        raise ValueError(f"scale={scale!r} muss eine endliche Zahl > 0 sein")
    final_margin = float(final_margin)
    if not math.isfinite(final_margin):
        raise ValueError(f"final_margin={final_margin!r} ist keine endliche Zahl (Ausgang unbekannt?)")
    x = final_margin / scale
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def format_margin_counts(counts: dict, scale) -> list:
    """Druckzeilen der Margen-Zaehlung (gleiche Slots wie beim Trajektorien-
    Modus; die mittlere Spalte "Ausgang" bleibt hier immer 0, weil jeder Record
    mit bekanntem Ausgang auch eine Marge hat)."""
    lines = [f"🔧 Margen-Bootstrap (b = {scale} Punkte) je Runde, nur vollstaendige "
             f"Partien -- Marge / Ausgang / ohne bootstrap_value:"]
    for rd in sorted(counts):
        margin, outcome, no_bv = counts[rd]
        lines.append(f"   Runde {rd}: {margin} / {outcome} / {no_bv}")
    return lines
