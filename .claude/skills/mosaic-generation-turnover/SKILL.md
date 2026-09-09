---
name: mosaic-generation-turnover
description: Generationswechsel VOR dem Start des Self-Plays der naechsten Generation (Nutzer-Auftrag 2026-09-05). Nutze das, sobald die Abnahmen einer Generation durch sind und die Erzeugung der naechsten ansteht, oder wenn der Nutzer "Generationswechsel", "aufraeumen vor v25" oder "vor dem Self-Play" sagt. Deckt ab - Maschine frei und Reihenfolge, daily-Snapshot ins restic-Repo mit Beleg, Loeschen obsoleter Ketten-Skripte in tools/, Loeschen nicht mehr gebrauchter Self-Plays, Bloecke und Monolithe (nur mit restic-Beleg und pfadgenauer Freigabe), Modelle nur nach Ruecksprache, STATUS-Neufassung mit Auslagerung nach archive/history.md, Preregs, Laufzeiten, Namen, Anker, Einfrieren des Generators, Startbedingungen der Erzeugung.
---

# Generationswechsel: Aufraeumen und Uebergabe vor dem naechsten Self-Play

**Warum ein eigener Ablauf.** Zwischen zwei Generationen sammeln sich
Ketten-Skripte, Messkorpora, Bloecke fuer tote Fenster, Zwischenmodelle und
ein STATUS, der die ganze Kampagne traegt. Jeder Posten davon hat schon
einmal Zeit gekostet: verwaiste Bloecke (83 MB, unauffindbar, `pitfalls.md`),
Streudateien im data-Glob (b05-Konfundierung), ein STATUS mit 882 Zeilen, zwei
Sitzungen, die dieselbe Kette doppelt starteten. Die Erzeugung der naechsten
Generation laeuft 12 Stunden exklusiv; was vorher nicht sauber ist, bleibt
es waehrenddessen.

**Regeln, die hier gelten und NICHT in diesem Skill stehen** (CLAUDE.md ist
die Quelle): Loeschung nur auf pfadgenaue Nutzer-Freigabe, kein Push ohne
Anweisung, Messungen exklusiv, Prereg-Kopf im selben Zug wie das Ergebnis,
Laufzeiten im Artefakt, Regel 0 (geprueft oder markiert).

## Reihenfolge (bindend, jeder Schritt haengt am vorigen)

### 0. Maschine frei, Baum sauber, alles registriert

- Prozessliste pruefen, nicht die Task-Meldungen (Falle 2026-09-05):
  ```
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'train.py|self_play|paired_|night_v24|cpu_queue|cargo|maturin' } | Select-Object ProcessId,Name,CommandLine"
  ```
  Nichts davon darf laufen. Verwaiste Ketten (Parent weg) erst beenden,
  wenn ihre Artefakte da sind.
- `git status --short` leer; `git rev-list --count origin/main..main` melden.
  Push NUR auf Anweisung.
- Jedes Ergebnis der Generation steht in seiner Prereg (par.9-Tabelle der
  Fenster-Prereg: alle Arme, alle Tore, Generatorwahl), im Elo-Register
  (`tools/elo_tracker.py show`) und in der Chronik. Fehlt eines: erst
  nachtragen, dann weiter. Der Generator der naechsten Generation ist per
  Nutzer-Entscheid benannt (Generatorwahl-Regel `docs/generation_loop.md`).

### 1. Einfrieren, was Referenz wird

- Der gewaehlte Generator wird Referenz (Gegner der naechsten Tore, Traeger
  des Rezepts): Artefakt nach dem Muster `models/frozen_champions/<name>/`
  mit Modell, Spec, **Wheel** (ein Wheel liegt IM Artefakt, `working_rules.md`),
  Manifest, Golden-Probe. Ausloeser ist die Rollenuebernahme, nicht "sieht
  fertig aus" (`feedback_freeze_when_it_becomes_a_reference`).
- Wurde die Engine seit dem letzten Anker-Check geaendert oder das Wheel
  gewechselt: `/mosaic-anchor-invariance` (Drift-Pruefung gegen
  `models/frozen_heuristics/hv1_anchor`). ROT ist Nutzer-Entscheid, kein
  Reparaturauftrag.
- Champion-Wechsel steht an? Dann `/mosaic-champion-promotion` VOR diesem
  Ablauf, nicht nebenher.

### 2. Daily-Snapshot ins restic-Repo, mit Beleg

- Tageslauf: `tools/mosaic_backup.ps1` (Schalter in `docs/backup_restore.md`,
  Tag `daily`, Sicherungswurzel aus `MOSAIC_BACKUP_DIR`). Danach
  `tools/verify_backup.ps1` (fuenf Stufen) und `restic snapshots --tag daily`;
  die Snapshot-ID in die Chronik.
- **Vor JEDER Loeschung unten:** `restic find --snapshot <id> "<Muster>"` fuer
  jede zu loeschende Gruppe, Trefferzahl gegen die Dateizahl im Baum halten,
  beides in die Chronik. Ohne diesen Beleg wird nichts geloescht (Praezedenz
  2026-09-04 21:15, Snapshot d775926d).

### 3. Obsolete Ketten-Skripte in tools/ loeschen

- Obsolet ist ein Skript, wenn (a) sein Lauf beendet ist, (b) seine Ergebnisse
  in Prereg und Chronik stehen und (c) es an eine konkrete Generation gebunden
  ist (Namen mit `night_v<G>_*`, `cpu_queue_*`, `*_chain.sh` mit fester
  Armliste). Generische Werkzeuge (`argmax_profile.sh`, Sonden, Tests) bleiben.
- Liste dem Nutzer vorlegen (Pfad, Zweck, Ergebnis-Verweis), dann `git rm`;
  die Git-Historie behaelt sie. Skills und Docs, die eines der Skripte
  nennen, im selben Zug nachziehen (`tools/check_conventions.py` Regel 6
  prueft nur Skill-Verweise, keine Skript-Verweise).

### 4. Self-Plays, Bloecke und Monolithe der toten Fenster loeschen

- Zuerst die Fensterliste der NAECHSTEN Generation bauen (Prereg par.1 der
  neuen Fenster-Prereg, `tools/generate_carrier_manifest.py --pick`,
  `window_v<G+1>.txt`). Alles in `data/`, was weder dort steht noch
  Referenz ist, ist Kandidat. Referenz bleibt IMMER: `frozen_v3`,
  Mensch-Logs (`static/log/`), die Traeger-Manifeste, Korpora laufender
  Preregs.
- Kandidaten-Klassen, je als Gruppe mit `restic find` belegt:
  Messkorpora (`selfplay_tor2a-*`, `selfplay_pilot*`, Sonden-Korpora),
  Self-Play-Klassen, die aus der Rotation fallen (G-3 und aelter,
  `docs/window_generation.svg`), deren Manifeste (`manifest_*.json`).
- Bloecke und Monolithe: `python tools/cache_inventory.py --orphans` NACH
  der Korpus-Loeschung, dann `--print-delete-list`; Monolithe `.cache_*.h5`
  toter Fenster (Schluessel in den Trainings-Manifesten der Arme, Feld
  `cache_file`). Das Werkzeug loescht NICHTS, die Liste geht an den Nutzer.
- Loeschen erst nach pfadgenauer Freigabe. Danach `cache_inventory.py
  --orphans` noch einmal: muss leer sein.
- Fenster-Pinning fuer die Erzeugung setzen (`MOSAIC_DATA_EXCLUDE`,
  `feedback_window_pinning_during_generation`), damit Streudateien, die
  waehrend des Laufs entstehen, nicht still ins Fenster laufen.

### 5. Modelle: NUR nach Ruecksprache

- Liste vorlegen, nie selbst entscheiden: je Modell Name, Rolle (Champion,
  Anker, Generator, Arm, Zwischenstand), Elo-Knoten, Prereg-Verweis,
  Groesse. Kandidaten fuer die Loeschung sind Arme ohne Rolle (`_best`,
  `_brierbest`, `.pth`, `.onnx`, `.ref.txt`, `_loss.png`) und liegen
  gebliebene `*_resume.pth`/`*.stop`. Nie: Champion, Anker-Artefakte,
  eingefrorene Artefakte, Generator, Elo-Knoten mit Kanten.
- Vorher `restic snapshots --tag run:<name>` je Modell (train.py sichert
  jeden Lauf als Snapshot) -- ohne Marke kein Loeschvorschlag.

### 6. STATUS neu schreiben, Historie aktualisieren

- Den vollstaendigen alten STATUS als Kapitel
  `# Vollstaendiger STATUS-Stand vom <Datum> (vor der Neufassung)` ans Ende
  von `archive/history.md` (Praezedenz 2026-08-25 und 2026-08-31), dazu ein
  Kapitel mit dem Generationsbericht (Arme, Tore, Generatorwahl, Zahlen mit
  Prereg-Verweis).
- STATUS Neufassung: Abschnitt 1 "Was gerade laeuft" (leer bis auf die
  Erzeugung), Champion und Elo, Prereg-Bestand (Ziel rund 7 OFFEN,
  `project_open_preregs_target_seven`), Kostentabelle "Laufzeiten
  (gemessen)" aus den Artefakten der Generation nach `docs/measured_runtimes.md`
  uebertragen, offene Nutzer-Entscheide, Push-Stand. Zahlen ohne Datum
  markieren. Prozesswissen NICHT in STATUS, sondern in `docs/`
  (`feedback_status_is_not_longterm_memory`).
- Preregs: alle Koepfe der Generation nachgezogen, dann
  `python tools/generate_prereg_index.py`; ENTSCHIEDENE der Generation mit
  Verdikt-Absatz; neue Fenster-Prereg fuer G+1 mit par.1 Zuschnitt, par.6
  Rezept (Befehle, Knoepfe, Spec-Dateien, Val-Pool-Regex, Startgewicht) und
  Pflichtpruefungen (Manifest-Diff gegen Referenz, Stack-Draw-Kontrolle,
  Tor 0) -- VOR dem Start.
- `docs/generation_naming.md`: Namen der naechsten Arme vorab reservieren;
  `docs/knobs.md` per `tools/generate_knob_docs.py` frisch, falls Knoepfe
  dazukamen; `docs/measured_runtimes.md` um die Laufzeiten der Generation.

### 7. Startbedingungen der Erzeugung

- Der Nutzer gibt die Erzeugung ausdruecklich frei (Stand seit 2026-09-03:
  "ausser der Fenstererzeugung"); der Skill endet mit der Vorlage, nicht mit
  dem Start.
- Vor dem Start: Wheel installiert und Kontrakt-Hash im Manifest; Spec-
  Dateien der Knoepfe liegen; Referee-Selbsttest/Golden-Probe gruen;
  Plattenplatz (`data/` und Sicherungswurzel) reicht fuer rund 1.200
  Dateien plus Bloecke; keine Nebenlast; die App, an der die Sitzung haengt,
  bleibt offen (Harness-Stopp 2026-09-05), lange Laeufe ueber Ketten-Skripte.
- Kette fuer G+1 nach dem Muster `night_v26_chain.sh` schreiben (Manifest,
  Fenster, Monolith, Trainings-Arme), MIT gehaerteter Wartebedingung
  (leere Prozessantwort = belegt) und `--resume`-Hinweis fuer jedes
  Training. **Keine eigene Chronikdatei anlegen** (Nutzer 2026-09-09): das
  Inhaltliche gehoert in die Prereg, der Stand in STATUS.md, die Chronik nach
  `archive/history.md`. Die frueheren `night_run_<Datum>.md` waren eine zweite
  Chronik neben `history.md` und sind dorthin aufgeloest worden.

## Was dieser Ablauf NICHT ist

- Keine Messung: es wird nichts gefahren ausser Anker-Drift und Golden-Probe.
- Kein Champion-Wechsel (eigener Skill), keine Prereg-Verdikte im Vorbeigehen
  (`/mosaic-prereg`).
- Keine Loeschung ohne restic-Beleg UND pfadgenaue Freigabe, auch nicht von
  "offensichtlichem" Muell -- Frage ist keine Anweisung.
