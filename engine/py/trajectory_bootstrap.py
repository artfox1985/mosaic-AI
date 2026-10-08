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


def is_support_record(record) -> bool:
    """Darf `record` als Stuetzstelle eines Trajektorien-Bootstraps dienen?

    Dieselben zwei Bedingungen, die `trajectory_bootstrap_lookup` seit b03
    stellt (ohne Seite und Runde, die dort hinzukommen): `root_q` vorhanden
    (fehlt bei Ein-Aktion-Zuegen und Tiling-Records) und `dice_phase` nicht
    True (Wuerfelphase, PREREG_asymmetric_selfplay.md par.5d). Die Varianten
    b11 bis b15 (PREREG_v35_window.md par.19) benutzen genau diese Menge.
    """
    return record.get("dice_phase") is not True and record.get("root_q") is not None


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
    later_index = trajectory_bootstrap_lookup_index(records_of_game, index, horizon_rounds)
    if later_index is None:
        return None
    return float(records_of_game[later_index]["root_q"])


def trajectory_bootstrap_lookup_index(records_of_game, index, horizon_rounds) -> int | None:
    """Position (in `records_of_game`) des Records, dessen `root_q`
    `trajectory_bootstrap_lookup` liefert, oder None. Gleiche Suche, gleiche
    Bedingungen, gleiche Fehler; die Konfidenz-Variante (b15, par.19.5)
    braucht den Record selbst, nicht nur seinen Wert."""
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
        return later_index
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


def _positions_by_game(game_data) -> list:
    """Positionen je `game_id` in Dateireihenfolge (wie `trajectory_bootstrap_values`)."""
    positions_by_game: dict = {}
    for file_index, record in enumerate(game_data):
        positions_by_game.setdefault(record.get("game_id"), []).append(file_index)
    return list(positions_by_game.values())


def _check_unit_interval(name, value) -> float:
    value = float(value)
    if not (math.isfinite(value) and 0.0 <= value <= 1.0):
        raise ValueError(f"{name}={value!r} muss eine endliche Zahl in [0, 1] sein")
    return value


# --- par.19.1/par.19.2 (Arme v35-b11, v35-b12): TD(lambda) ueber den echten Pfad ---

def trajectory_lambda_lookup(records_of_game, index, traj_lambda, opponent=False) -> float | None:
    """Gewichtetes Mittel der Suchwerte ALLER spaeteren Stuetzstellen der
    Partie (Referenzform, explizite Summe; die Datei-Variante
    `trajectory_lambda_values` rechnet dasselbe rekursiv).

    PREREG_v35_window.md par.19.1 (b11, `opponent=False`): Stuetzstellen sind
    die spaeteren Records DERSELBEN Seite mit `is_support_record`; der j-te
    (j = 1 ist die naechste eigene Suchstellung, auch in derselben Runde)
    bekommt das Gewicht lambda^(j-1), Wert `root_q`.

    par.19.2 (b12, `opponent=True`): Stuetzstellen sind die spaeteren
    `is_support_record`-Records BEIDER Seiten; der h-te bekommt das Gewicht
    lambda^((h-1)/2) (Halbzug-Schritte), Wert `root_q` bei gleicher Seite,
    `1 - root_q` bei der Gegenseite. Die Spiegelung setzt voraus, dass
    `root_q` aus Sicht des jeweils Ziehenden gespeichert ist: Wurzelknoten mit
    `player_who_acted = root_state.current_player` (engine/src/net_mcts.rs:
    7328/7333), Rueckpropagation `value[player_who_acted]` (net_mcts.rs:5274),
    `root_q = nodes[0].value / visits` (net_mcts.rs:8659); der Record traegt
    `player` daneben (engine/src/self_play.rs:6663).

    Normiert: Summe(Gewicht x Wert) / Summe(Gewicht), Ergebnis im Record-Raum
    [0,1]. Ohne jede spaetere Stuetzstelle None (Aufrufer nimmt den Ausgang,
    wie b03). Der Ausgang selbst ist KEIN Summand (par.19.1 woertlich: Mittel
    der Suchwerte, Ausgang nur als Rueckfall). lambda in [0, 1]; lambda = 0
    heisst nur die erste Stuetzstelle (0^0 = 1), lambda = 1 das ungewichtete
    Mittel.
    """
    traj_lambda = _check_unit_interval("traj_lambda", traj_lambda)
    player = records_of_game[index]["player"]
    numerator = 0.0
    denominator = 0.0
    count = 0
    for later in records_of_game[index + 1:]:
        if not is_support_record(later):
            continue
        same_side = later.get("player") == player
        if not same_side and not opponent:
            continue
        count += 1
        q = float(later["root_q"])
        value = q if same_side else 1.0 - q
        exponent = (count - 1) / 2.0 if opponent else float(count - 1)
        weight = traj_lambda ** exponent
        numerator += weight * value
        denominator += weight
    if count == 0:
        return None
    return numerator / denominator


def trajectory_lambda_values(game_data, traj_lambda, opponent=False) -> list:
    """`trajectory_lambda_lookup` fuer jeden Record einer Korpusdatei, in
    O(n) je Partie statt O(n^2): rueckwaerts ueber die Partie laufen und je
    Blickrichtung p die Summen S_p = Summe(g^(m-1) x Wert_p) und D_p =
    Summe(g^(m-1)) fortschreiben (g = lambda ohne, sqrt(lambda) mit
    Gegnerstellungen). Kommt eine Stuetzstelle s hinzu, wird
    S_p <- Wert_p(s) + g x S_p und D_p <- 1 + g x D_p; ohne Gegnerstellungen
    nur fuer p = Seite von s. Ergebnis gleich der Referenzform bis auf
    Gleitkomma-Rundung (Test `tools/tests/test_trajectory_bootstrap.py`).

    Gruppierung nach `game_id` in Dateireihenfolge wie
    `trajectory_bootstrap_values`; die Gewichte haengen hier an der
    Reihenfolge der Records (j-te spaetere Stuetzstelle), die Schreiber legen
    sie in Zugreihenfolge ab. Spielerindizes muessen 0 oder 1 sein.
    """
    traj_lambda = _check_unit_interval("traj_lambda", traj_lambda)
    step = math.sqrt(traj_lambda) if opponent else traj_lambda
    out: list = [None] * len(game_data)
    for positions in _positions_by_game(game_data):
        sums = [0.0, 0.0]
        weights = [0.0, 0.0]
        for file_index in reversed(positions):
            record = game_data[file_index]
            player = record["player"]
            if player not in (0, 1):
                raise ValueError(f"player={player!r} -- erwartet 0 oder 1")
            if weights[player] > 0.0:
                out[file_index] = sums[player] / weights[player]
            if not is_support_record(record):
                continue
            q = float(record["root_q"])
            for side in ((0, 1) if opponent else (player,)):
                value = q if side == player else 1.0 - q
                sums[side] = value + step * sums[side]
                weights[side] = 1.0 + step * weights[side]
    return out


# --- par.19.3 (Arm v35-b13): Mittel aus Trajektorie und Rollout ---

def mixed_bootstrap_value(trajectory_value, rollout_value, mix) -> float:
    """bvp = mix x Trajektorie + (1 - mix) x Rollout (par.19.3).

    `trajectory_value`: was b03 als bvp einsetzt, also `root_q` des spaeteren
    Records oder, ohne solchen, der Ausgang. `rollout_value`: der gespeicherte
    Netz-Rollout `bootstrap_value[p]`, genau wie der Bestandszweig ihn als bvp
    nimmt (roh, bzw. entstaucht fuer die Blockliste). mix in [0, 1].
    """
    mix = _check_unit_interval("mix", mix)
    return mix * float(trajectory_value) + (1.0 - mix) * float(rollout_value)


# --- par.19.5 (Arm v35-b15): Gewichtung nach Verlaesslichkeit der spaeteren Suche ---

def root_child_q_gap(record) -> float | None:
    """Abstand bestes minus zweitbestes Kind-Q aus `root_child_q` (Record-Raum).

    `root_child_q` ist die Liste der completed-Q je Wurzelkandidat, parallel
    zu `policy` (engine/src/self_play.rs:8676-8681, Werte aus
    net_mcts.rs `root_completed_q_raw`), aus Sicht des Ziehenden wie `root_q`
    (Kind-Werte akkumulieren unter `player_who_acted` = Zieher an der Wurzel,
    net_mcts.rs:5124-5133). Rueckgabe:

    - None, wenn das Feld fehlt (Aufrufer entscheidet; die Bauschleife bricht
      dann hart ab, siehe `trajectory_confidence_values`);
    - None auch bei weniger als zwei Eintraegen: es gibt kein zweitbestes
      Kind. Im b02-Fenster kommt das nicht vor (0 von 1.514.238
      Drafting-Stuetzstellen, evaluations/artifacts/
      traj_conf_scale_calibration_v35_b02.json, side_counts);
    - sonst q_(1) - q_(2) >= 0 nach absteigender Sortierung; gleiche
      Spitzenwerte ergeben 0. Achtung Runde-5-Loeser-Zweig: dort traegt JEDER
      Eintrag denselben Wert root_q (engine/src/net_mcts.rs:8641-8650), der
      Abstand ist also 0 -- ob dieser Zweig in einer Erzeugung aktiv war, ist
      hier nicht gepruefte Sache des Aufrufers.
    """
    child_q = record.get("root_child_q")
    if child_q is None:
        return None
    values = sorted((float(v) for v in child_q), reverse=True)
    if len(values) < 2:
        return None
    return values[0] - values[1]


def confidence_weight(gap, scale) -> float:
    """w = clip(gap / s, 0, 1) (par.19.5). `scale` endlich und > 0."""
    scale = float(scale)
    if not (math.isfinite(scale) and scale > 0.0):
        raise ValueError(f"scale={scale!r} muss eine endliche Zahl > 0 sein")
    return min(1.0, max(0.0, float(gap) / scale))


def confidence_bootstrap_value(later_q, weight, outcome) -> float:
    """bvp = w x root_q_spaeter + (1 - w) x Ausgang (par.19.5)."""
    weight = _check_unit_interval("weight", weight)
    return weight * float(later_q) + (1.0 - weight) * float(outcome)


def trajectory_confidence_values(game_data, horizon_rounds, scale) -> list:
    """Je Record (root_q_spaeter, w) des b03-Treffers
    (`trajectory_bootstrap_lookup_index`, Obergrenze `horizon_rounds`) oder
    None ohne Treffer (Aufrufer nimmt den Ausgang).

    w aus `root_child_q_gap` des SPAETEREN Records ueber `confidence_weight`.
    Hat der spaetere Record weniger als zwei Kind-Eintraege, gibt es keine
    Rangfolge, an der sich Unsicherheit ablesen liesse: w = 1, also genau der
    b03-Wert (Festlegung beim Bau 2026-10-08, als offene Entscheidung an den
    Koordinator gemeldet; im b02-Fenster 0 Faelle). Fehlt `root_child_q` auf einem
    spaeteren Record mit `root_q` (Erzeugung mit MOSAIC_ROOT_CHILD_Q=0 oder
    Alt-Datei), harter Fehler statt eines still gewaehlten Gewichts.
    """
    out: list = [None] * len(game_data)
    for positions in _positions_by_game(game_data):
        records_of_game = [game_data[i] for i in positions]
        for game_index, file_index in enumerate(positions):
            later_index = trajectory_bootstrap_lookup_index(records_of_game, game_index, horizon_rounds)
            if later_index is None:
                continue
            later = records_of_game[later_index]
            if later.get("root_child_q") is None:
                raise ValueError(
                    "Record mit root_q, aber ohne root_child_q (game_id "
                    f"{later.get('game_id')!r}, Runde {_round_of(later)}) -- Konfidenz-Bootstrap "
                    "nicht bestimmbar (MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE)")
            gap = root_child_q_gap(later)
            weight = 1.0 if gap is None else confidence_weight(gap, scale)
            out[file_index] = (float(later["root_q"]), weight)
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


def format_trajectory_counts(counts: dict, horizon_rounds, label=None) -> list:
    """Druckzeilen der Zaehlung, eine Kopfzeile plus eine Zeile je Runde.

    `label` (par.19, Varianten b11 bis b15): Quelle und Knoepfe als Zusatz der
    Kopfzeile; None laesst die bisherige Kopfzeile stehen. `horizon_rounds`
    None (Quelle trajectory_lambda, keine Obergrenze) laesst die Obergrenze weg.
    """
    head = "Trajektorien-Bootstrap"
    if horizon_rounds is not None:
        head += f" (Obergrenze {horizon_rounds})"
    if label:
        head += f" [{label}]"
    lines = [f"🔧 {head} je Runde, nur "
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
