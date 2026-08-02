"""
Mosaic-AI -- Spielerprofile mit Elo-Rating (Server-Game, lokal).
====================================================================

Nutzer-Feature (2026-08-02): mehrere lokale Spielerprofile, jeweils mit
eigenem Elo-Rating (Start 1000). Nach jedem ABGESCHLOSSENEN Spiel (Phase
'end' via /api/end_scoring erreicht) wird das Profil-Rating des Menschen
per Standard-Elo aktualisiert -- KI-Ratings sind FIXE Anker (Bradley-Terry-
Fit aus evaluations/elo_history.csv, siehe `estimate_ai_anchor`) und werden
NIE veraendert. Abgebrochene Spiele (kein /api/end_scoring erreicht) bleiben
automatisch ungewertet -- es gibt keinen expliziten "Abbruch"-Zustand, das
Rating wird schlicht nur bei echtem Spielende angefasst.

Elo-Mathematik (ln(10)/400-Skala) ist 1:1 aus tools/elo_tracker.py
uebernommen (LN10_OVER_400) -- NICHT neu erfunden, siehe Memory-Regel
"Check existing tools first". Der KI-Anker selbst kommt ebenfalls aus
`tools/elo_tracker.py::fit_all`/`load_rows` (Bradley-Terry-Fit ueber den
kompletten Arena-Graphen), NICHT aus einer eigenen Nebenrechnung.

Persistenz-Ort (Design-Entscheidung): `player_profiles.json` im
PROJEKTROOT, NICHT unter data/. `data/` ist per Konvention der
Trainings-Korpus (Self-Play-Spiele fuers Netz-Training, riesig, git-
ignoriert, klar abgegrenzte Ordnerstruktur mit data_lambda_sweep/ etc.).
Spielerprofile sind Nutzer-/Laufzeit-Zustand des Server-Games, kein
Trainingsartefakt -- eine Vermischung wuerde die Korpus-Ordnung aufweichen.
Eine einzelne kleine JSON-Datei neben server.py (analog zu models/
champion.txt als "eine Datei = ein Zustand"-Pattern) ist einfacher als ein
eigenes profiles/-Verzeichnis fuer eine einzige Datei.
"""
from __future__ import annotations

import json
import math
import os
import uuid
from datetime import datetime as _dt
from pathlib import Path

from tools.elo_tracker import (
    LN10_OVER_400,
    fit_all,
    load_rows,
    node_key as _anchor_node_key,
)

# Isolation (Vorfall 2026-08-02): eine Testserver-Instanz hat versehentlich
# gegen dieselbe Datei wie der Live-Server geschrieben und mitten in einer
# echten Partie das Profil des Users geleert -- Test-/Zweitinstanzen MUESSEN
# ab jetzt per MOSAIC_PROFILES_PATH einen eigenen Pfad setzen (Scratchpad/
# Temp). Default bleibt unveraendert der Projektroot (Live-Server-Verhalten).
_env_path = os.environ.get("MOSAIC_PROFILES_PATH")
PROFILES_PATH = Path(_env_path) if _env_path else (Path(__file__).resolve().parent / "player_profiles.json")
# Selbstheilung (Vorfall 2026-08-02): bei jedem erfolgreichen Save wird
# zusaetzlich eine .bak geschrieben (siehe _save_profiles) -- beim Laden
# einer leeren/beschaedigten Hauptdatei wird sie bevorzugt statt sofort mit
# einem leeren Profil-Set zu starten (siehe _load_profiles_raw).
BAK_PATH = PROFILES_PATH.with_name(PROFILES_PATH.name + ".bak")

DEFAULT_RATING = 1000.0
MAX_HISTORY_ENTRIES = 50  # pro Profil in der JSON behalten (Datei bleibt klein)

# ── K-Faktor: FEST, K=40 (finaler User-Entscheid 2026-08-02) ───────────────
# Vier verworfene Zwischenstaende vor dieser finalen Fassung:
#   1. Spielzaehler-Ansatz ("K=32 fuer die ersten N gewerteten Spiele, danach
#      16") -- `games_rated` bleibt trotzdem im Profil/in der Historie als
#      reine Statistik erhalten (nicht mehr Teil der K-Berechnung).
#   2. Differenzbasiert, EINSEITIG (Bonus nur wenn Spieler UNTER dem Gegner
#      liegt).
#   3. Differenzbasiert, SYMMETRISCH (Bonus in beide Richtungen bei grosser
#      Differenz).
#   4. Fester K=20.
# Begruendung des Users fuer den Wechsel auf einen festen K-Faktor: die
# Standard-Elo-Formel skaliert den Punktetausch ueber den ERWARTUNGSWERT
# (E_A = 1/(1+10^((R_B-R_A)/400))) bereits von selbst -- bei grossem
# Rating-Abstand ist (S_A - E_A) selbst schon nahe 0 oder nahe 1, ein
# zusaetzlich variabler K-Faktor obendrauf ist unnoetig. K=40 (statt 20)
# nach nochmaligem Ueberlegen des Users gewaehlt -- FIDE-Neueinsteiger-Niveau
# (der Weltschachbund nutzt K=40 fuer Spieler mit <30 gewerteten Partien bzw.
# unter 2300 Elo), passend zu einem Spieler, der gerade erst startet und
# zuegig ein aussagekraeftiges Rating aufbauen soll.
K_FACTOR = 40.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Standard-Elo-Erwartungswert, ln(10)/400-Skala (identisch zu
    tools/elo_tracker.py -- reine Import-Uebernahme der Konstante):
    E_A = 1/(1+10^((R_B-R_A)/400))."""
    return 1.0 / (1.0 + math.exp(-LN10_OVER_400 * (rating_a - rating_b)))


# ── KI-Anker (Bradley-Terry-Fit aus evaluations/elo_history.csv) ────────────
# Einmal beim Serverstart berechnet (siehe `refresh_anchor_table`, von
# server.py beim Modul-Import aufgerufen) -- reine Lesezugriffe danach, kein
# Recompute pro Request (der Fit inkl. Bootstrap-CI ist server.py hier NICHT
# noetig, nur die reinen Elo-Punktschaetzer aus `fit_all`).
_anchor_cache: dict | None = None

# Sims-Tier-Diskont fuer KI-Gegner OHNE direkte Arena-Kante bei GENAU dieser
# Sims-Zahl (z.B. DIFFICULTY_PRESETS "medium"/"hard" = Champion bei 60/150
# Sims -- die Arena misst Champion-Kanten ausschliesslich bei 400 Sims).
# GESCHAETZT, NICHT empirisch validiert -- im Projekt existieren keine
# Sims-Sweep-Arena-Daten (gleiches Modell bei mehreren Sims-Stufen
# gegeneinander/gegen Anker gemessen). Bewusst konservativ und monoton
# fallend gewaehlt, damit ein Spieler-Rating gegen eine leichtere KI-Stufe
# nicht kuenstlich hoch ausfaellt (Unterschaetzung ist der sichere Fehler
# hier, keine Ueberschaetzung). In der UI werden Schaetzwerte mit "~"
# gekennzeichnet (siehe `estimate_ai_anchor`-Rueckgabe `is_estimate`).
_SIMS_TIER_DISCOUNT = [
    (400, 0),
    (200, 25),
    (100, 60),
    (0, 100),
]


def _tier_discount(sims: int) -> int:
    for threshold, discount in _SIMS_TIER_DISCOUNT:
        if sims >= threshold:
            return discount
    return _SIMS_TIER_DISCOUNT[-1][1]


def refresh_anchor_table() -> dict:
    """Liest evaluations/elo_history.csv neu ein und fitted die Elo-Tabelle
    (tools/elo_tracker.py::fit_all -- WIEDERVERWENDET, nicht neu erfunden).
    Wird von server.py einmal beim Start aufgerufen; kann bei Bedarf erneut
    aufgerufen werden (z.B. falls die CSV sich waehrend der Serverlaufzeit
    aendert), ist aber sonst nicht noetig."""
    global _anchor_cache
    rows = load_rows()
    fitted, *_ = fit_all(rows)
    _anchor_cache = fitted  # {node_key: (elo|None, connected_to_anchor: bool)}
    return _anchor_cache


def _anchor_table() -> dict:
    if _anchor_cache is None:
        return refresh_anchor_table()
    return _anchor_cache


def estimate_ai_anchor(identity: str, sims: int):
    """Liefert (elo, is_estimate, source_node) fuer einen KI-Gegner
    `identity@sims` (identity z.B. "v19_2d_best" oder "Heuristik", NIEMALS
    bereits mit "@sims" versehen -- sonst entsteht ein von der Arena-Kante
    verschiedener Doppel-Suffix-Knoten, siehe Datenwarnung unten).

    1. Existiert eine DIREKTE Arena-Kante fuer exakt diese Sims-Zahl (per
       Bradley-Terry ans Anker-Netz angebunden) -> exakter Wert, is_estimate=False.
    2. Sonst: beste bekannte Sims-Stufe DERSELBEN Identity im Graphen finden
       (bevorzugt 400, da das die ueberwiegende Arena-Konvention ist),
       Sims-Tier-Diskont-Differenz anwenden -> Schaetzwert, is_estimate=True.
    3. Keine einzige Arena-Kante fuer diese Identity vorhanden (z.B. frisch
       trainiertes/unbekanntes Modell) -> (None, True, None), Aufrufer
       muss das Spiel dann als ungewertet behandeln (kein Anker vorhanden).

    Datenwarnung (nicht Teil dieses Features, nur zur Einordnung): die CSV
    enthaelt einen historischen Eintrag mit player_b="Heuristik@150" UND
    sims_b=150 (statt player_b="Heuristik"), der einen eigenen Knoten
    "Heuristik@150@150" erzeugt, verschieden vom echten fixen Anker
    "Heuristik@150" (node_key("Heuristik", 150)). Solange `identity` hier
    IMMER der reine Modellname ohne "@" ist (so wie es DIFFICULTY_PRESETS/
    _ai_model in server.py liefern), betrifft das diese Funktion nicht."""
    fitted = _anchor_table()
    exact_key = _anchor_node_key(identity, sims)
    hit = fitted.get(exact_key)
    if hit is not None and hit[0] is not None:
        return hit[0], False, exact_key

    candidates = []
    for node, (elo, connected) in fitted.items():
        if elo is None or not connected or "@" not in node:
            continue
        name, s = node.rsplit("@", 1)
        if name != identity:
            continue
        try:
            candidates.append((int(s), elo))
        except ValueError:
            continue
    if not candidates:
        return None, True, None

    # Bevorzugt sims=400 (haeufigste Arena-Bedingung), sonst die naechste
    # tatsaechlich vermessene Sims-Stufe.
    candidates.sort(key=lambda x: (x[0] != 400, abs(x[0] - 400)))
    base_sims, base_elo = candidates[0]
    est = base_elo - (_tier_discount(sims) - _tier_discount(base_sims))
    return est, True, _anchor_node_key(identity, base_sims)


# ── Persistenz (atomares Schreiben, OneDrive-Vorsicht) ──────────────────────

def _atomic_write_json(path: Path, data: dict) -> None:
    """Write-temp-then-rename (siehe MEMORY.md 'OneDrive file disappearance')
    -- direktes Ueberschreiben kann bei einer OneDrive-Sync-Unterbrechung
    eine leere/korrupte Datei hinterlassen. Temp-Datei im SELBEN Verzeichnis
    (os.replace ist nur innerhalb desselben Volumes atomar) mit PID im Namen
    (kollisionsfrei bei parallelen Prozessen, z.B. zwei Testserver-Instanzen)."""
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomar unter Windows (>=Py3.3) wie POSIX


def _save_profiles(data: dict) -> None:
    """Speichert die Hauptdatei UND eine .bak-Kopie (gleiche atomare
    Technik) -- Selbstheilung (Vorfall 2026-08-02): geht die Hauptdatei
    spaeter verloren/kaputt (Test-Kollision, OneDrive-Sync, o.ae.), liefert
    .bak beim naechsten Laden die letzte bekannte gute Version zurueck,
    statt dass ALLE Profile+Historie unwiederbringlich weg sind. Ein
    Backup-Schreibfehler ist NICHT fatal (Hauptsache ist die Hauptdatei),
    wird aber geloggt."""
    _atomic_write_json(PROFILES_PATH, data)
    try:
        _atomic_write_json(BAK_PATH, data)
    except OSError as e:
        print(f"WARNUNG player_profiles: Backup-Schreibversuch fehlgeschlagen ({e}) -- "
              f"Hauptdatei {PROFILES_PATH.name} wurde trotzdem erfolgreich gespeichert.")


def _try_load_json(path: Path) -> dict | None:
    """Laedt+validiert eine Profile-JSON-Datei. None bei fehlender Datei
    ODER ungueltigem Inhalt -- der Aufrufer entscheidet, ob/wie er das
    meldet (unterschiedlich fuer Haupt- vs. Backup-Datei, siehe unten)."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("profiles"), dict):
            return data
    except Exception:
        pass
    return None


def _load_profiles_raw() -> dict:
    data = _try_load_json(PROFILES_PATH)
    if data is not None:
        return data

    # Hauptdatei fehlt/ist leer/beschaedigt. Selbstheilung (Vorfall
    # 2026-08-02): NICHT sofort mit einem leeren Profil-Set weitermachen --
    # erst das Backup versuchen. Existierte die Hauptdatei (aber war
    # kaputt), wird sie zur Seite gelegt (Forensik, NICHT ueberschrieben)
    # und eine Warnung geloggt; fehlte sie schlicht (normaler Erststart),
    # ist das kein Fehlerfall und bleibt still.
    main_existed = PROFILES_PATH.exists()
    if main_existed:
        print(f"WARNUNG player_profiles: {PROFILES_PATH.name} ist vorhanden, aber leer/"
              f"beschaedigt/kein gueltiges Profil-Format -- versuche Backup {BAK_PATH.name}.")
        try:
            PROFILES_PATH.replace(PROFILES_PATH.with_name(PROFILES_PATH.name + ".corrupt"))
        except OSError as e:
            print(f"WARNUNG player_profiles: kaputte Datei konnte nicht zur Seite gelegt werden ({e}).")

    bak_data = _try_load_json(BAK_PATH)
    if bak_data is not None:
        print(f"player_profiles: Selbstheilung -- Profile aus Backup {BAK_PATH.name} wiederhergestellt "
              f"(werden beim naechsten erfolgreichen Speichern automatisch nach {PROFILES_PATH.name} "
              f"zurueckgeschrieben).")
        return bak_data

    if main_existed:
        print("WARNUNG player_profiles: kein nutzbares Backup gefunden -- starte mit leerem Profil-Set.")
    return {"version": 1, "profiles": {}}


# ── Öffentliche API ──────────────────────────────────────────────────────────

def list_profiles() -> list[dict]:
    data = _load_profiles_raw()
    return [
        {
            "id": pid,
            "name": p["name"],
            "rating": round(p["rating"], 1),
            "games_rated": p["games_rated"],
        }
        for pid, p in sorted(data["profiles"].items(), key=lambda kv: kv[1]["name"].lower())
    ]


def create_profile(name: str) -> dict:
    name = (name or "").strip()
    if not name:
        raise ValueError("Name darf nicht leer sein.")
    if len(name) > 40:
        raise ValueError("Name zu lang (max. 40 Zeichen).")
    data = _load_profiles_raw()
    pid = uuid.uuid4().hex[:12]
    profile = {
        "id": pid,
        "name": name,
        "rating": DEFAULT_RATING,
        "created": _dt.now().isoformat(timespec="seconds"),
        "games_rated": 0,
        "history": [],
    }
    data["profiles"][pid] = profile
    _save_profiles(data)
    return {"id": pid, "name": name, "rating": DEFAULT_RATING, "games_rated": 0}


def get_profile(pid: str) -> dict | None:
    return _load_profiles_raw()["profiles"].get(pid)


def apply_result(pid: str, opponent_label: str, opponent_rating: float,
                  opponent_is_estimate: bool, result: float,
                  hints_used: bool, seed=None, log=None) -> dict:
    """Aktualisiert EIN Profil nach einem GEWERTETEN Spiel. `result`:
    1.0=Sieg, 0.0=Niederlage, 0.5=Unentschieden (aktuell laut Regelwerk NIE
    erreichbar -- game.rs::determine_winner loest jeden Gleichstand per
    Startspieler-Marker-Tie-Break eindeutig auf, siehe Vollaudit-Kommentar
    dort; das Feld bleibt trotzdem fuer kuenftige Regelaenderungen). `seed`/
    `log` (Nutzer-Erweiterung 2026-08-02): Spiel-Seed + Log-Dateiname als
    Referenz, damit eine gewertete Partie spaeter nachvollzogen werden kann
    (`log` zeigt auf die ARCHIVIERTE Kopie unter static/log/elo/, siehe
    server.py::_archive_rated_game_log -- das Original bleibt zusaetzlich in
    static/log/ liegen, wird NICHT verschoben). Gibt den fertigen Historien-
    Eintrag zurueck (fuers API-Response).

    `hints_used` sollte hier IMMER False sein -- User-Entscheid 2026-08-02:
    sobald KI-Tipps genutzt wurden, ist die Partie komplett ungewertet
    (siehe `record_unrated` statt hier aufzurufen). Der Parameter bleibt
    trotzdem bestehen (Historien-Feld, defensiv falls der Aufrufer sich
    irrt) -- server.py::_apply_elo_for_finished_game ruft bei
    hints_used=True NICHT diese Funktion auf, sondern `record_unrated`."""
    data = _load_profiles_raw()
    profile = data["profiles"].get(pid)
    if profile is None:
        raise KeyError(pid)

    rating_before = profile["rating"]
    k = K_FACTOR
    expected = expected_score(rating_before, opponent_rating)
    delta = k * (result - expected)
    rating_after = rating_before + delta

    entry = {
        "date": _dt.now().isoformat(timespec="seconds"),
        "opponent": opponent_label,
        "opponent_rating": round(opponent_rating, 1),
        "opponent_is_estimate": opponent_is_estimate,
        "result": result,
        "rating_before": round(rating_before, 1),
        "rating_after": round(rating_after, 1),
        "delta": round(delta, 1),
        "k_factor": round(k, 1),
        "hints_used": hints_used,
        "rated": True,
        "seed": seed,
        "log": log,
    }

    profile["rating"] = rating_after
    profile["games_rated"] = profile.get("games_rated", 0) + 1
    profile.setdefault("history", []).insert(0, entry)
    profile["history"] = profile["history"][:MAX_HISTORY_ENTRIES]

    _save_profiles(data)
    return entry


def record_unrated(pid: str, opponent_label: str, opponent_rating: float | None,
                    opponent_is_estimate: bool, result: float, seed=None, log=None) -> dict:
    """Schreibt einen Historien-Eintrag OHNE das Rating zu aendern (User-
    Entscheid 2026-08-02: Partien, in denen KI-Tipps genutzt wurden, sind
    fuer ALLE beteiligten Profile komplett ungewertet, nicht nur markiert --
    `hints_used`-Feld existierte vorher schon, hat aber bloss vermerkt,
    NICHT die Wertung abgeschaltet). `games_rated` bleibt unveraendert --
    die Historie dient hier reiner Transparenz ("das hast du gespielt"),
    nicht der Rating-Grundlage. `seed`/`log`: siehe apply_result-Doku --
    `log` zeigt hier auf die UNVERAENDERTE Datei in static/log/ (ungewertete
    Partien werden NICHT nach static/log/elo/ archiviert). Gibt den Eintrag
    zurueck (fuers API-Response, Frontend zeigt statt einer Rating-Aenderung
    einen Hinweistext)."""
    data = _load_profiles_raw()
    profile = data["profiles"].get(pid)
    if profile is None:
        raise KeyError(pid)

    rating = profile["rating"]
    entry = {
        "date": _dt.now().isoformat(timespec="seconds"),
        "opponent": opponent_label,
        "opponent_rating": round(opponent_rating, 1) if opponent_rating is not None else None,
        "opponent_is_estimate": opponent_is_estimate,
        "result": result,
        "rating_before": round(rating, 1),
        "rating_after": round(rating, 1),
        "delta": 0.0,
        "k_factor": None,
        "hints_used": True,
        "rated": False,
        "seed": seed,
        "log": log,
    }

    profile.setdefault("history", []).insert(0, entry)
    profile["history"] = profile["history"][:MAX_HISTORY_ENTRIES]

    _save_profiles(data)
    return entry
