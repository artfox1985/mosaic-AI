# Loeschvorschlag zum Generationswechsel v25 -> v26 (2026-09-09)

**ERLEDIGT 2026-09-09:** der Nutzer hat A, B, C, D und E freigegeben; alles unten ist
geloescht. Bilanz: **11.154 MiB frei** (B 611 Dateien / 607,4 MiB, C 1.746 / 679,3 MiB,
D 12 / 6.576,7 MiB, E 50 / 324,6 MiB, dazu 7.553 Waisen-Bloecke / 2.965,9 MiB).
`data/` faellt von 19,69 auf 9,12 GiB. Gegenprobe `tools/cache_inventory.py --orphans`:
**0 Waisen** bei 6.402 verbliebenen Bloecken und 3.002 Korpusdateien.

Schritte 3, 4 und 5 des Ablaufs `/mosaic-generation-turnover`. **Nichts wird ohne
pfadgenaue Freigabe geloescht.** Schritt 4 wurde vor v25 bewusst uebersprungen und ist
jetzt faellig, deshalb ist die Liste laenger als beim letzten Mal.

**Belegstand vor jeder Loeschung:** Tages-Snapshot **6dd4d988** vom 2026-09-09
(`tools/mosaic_backup.ps1`, 7.725 Dateien / 9,279 GiB, `check` ohne Fehler), dazu der
Modell-Snapshot **028989fb** (`run:v25-b01`). Fuer jede Korpus-Gruppe unten steht die
Trefferzahl aus `restic find --snapshot 6dd4d988 "<Muster>"` gegen die Dateizahl im Baum.

## A) Ketten-Skripte (Schritt 3)

| Datei | Lauf | Warum obsolet |
| --- | --- | --- |
| `tools/night_v24_chain.sh` | v24-Kette, 2026-09-04/05 | Sie war als **Muster fuer die v25-Kette** aufgehoben; `tools/night_v25_chain.sh` steht seit 2026-09-08. Der Skill `mosaic-generation-turnover` verweist auf sie und wird im selben Zug auf die v25-Kette umgehaengt. |

**Bewusst NICHT vorgeschlagen:** `night_v25_chain.sh` (Muster fuer die v26-Kette) und die
drei Erzeugungsskripte `night_v25_socket.sh`, `night_v25_excursion.sh`,
`night_v25_arena.sh` plus `night_v25_train.sh`. Ihre Laeufe sind durch und registriert,
sie sind also nach der Regel obsolet -- aber sie sind die Arbeitsvorlage fuer die drei
v26-Befehle aus `PREREG_v26_window.md` par.7. Vorschlag: sie fallen, sobald die v26-Kette
geschrieben ist. Wenn der Nutzer sie schon jetzt weghaben will, ist das eine Zeile.

## B) Messkorpora (Schritt 4) -- 573 Dateien, 607,3 MiB

Alle Laeufe beendet, alle Ergebnisse in Prereg und Chronik; keiner dieser Praefixe steht
im v25-Fenster oder im Zuschnitt fuer v26 (`PREREG_v26_window.md` par.1).

| Muster | Dateien im Baum | im Snapshot 6dd4d988 | Groesse | Herkunft |
| --- | --- | --- | --- | --- |
| `data/selfplay_tor2a-*.pkl` | 280 | 280 | 304,2 MiB | Tor-2a-Instrument, 14 Arme v22 bis v24 |
| `data/selfplay_k3-*-v24b06_*.pkl` | 100 | 100 | 107,5 MiB | K3-Arme (P2, F05, F10, P2F10, Huelle 2) |
| `data/selfplay_temp?-tau*.pkl` | 80 | 80 | 76,2 MiB | Temperatur-Messreihe A-D |
| `data/selfplay_depth*-v24b06_*.pkl` | 60 | 60 | 64,7 MiB | Suchtiefen-Kurve 100/250/400 |
| `data/selfplay_k5w10-v24b06_*.pkl` | 20 | 20 | 21,9 MiB | K5-Arm |
| `data/selfplay_hf2-v24b06_*.pkl` | 20 | 20 | 21,5 MiB | Huellenform-2-Arm |
| `data/selfplay_smoke*.pkl` | 13 | 13 | 11,5 MiB | Rauchproben Weg B/C und Aktions-Temperatur |

Dazu die zugehoerigen `data/manifest_<praefix>_*.json` (je Gruppe eines bis vierzehn,
zusammen unter 100 KB) -- sie beschreiben genau diese Korpora und werden mit ihnen
sinnlos.

## C) Der hv2-Korpus -- 1.745 Dateien, 679,2 MiB (eigene Entscheidung)

`data/selfplay_hv2_*.pkl`, im Snapshot vollstaendig (1.745 von 1.745). **v26 ist das erste
Fenster ohne den plattenblinden Lehrer** (`PREREG_v26_window.md` par.2), der Korpus faellt
also aus der Rotation.

**Was daran haengt** (Rueckwaerts-Pruefung, geprueft per grep):

- `tools/probes/bootstrap_coherence_probe.py:170` nimmt als Vorgabe die erste
  `data/selfplay_hv2_*.pkl` und meldet ROT, wenn keine da ist; `--file` ueberschreibt.
- `tools/probes/action_count_profile_probe.py:16` fuehrt die hv2-Gruppe im
  Aufruf-Beispiel.
- Die nennenden Preregs (`heuristic_v2_long_rows`, `agent_encapsulation`, v23/v24/v25-
  Fenster) sind alle ENTSCHIEDEN; die Verweise sind Chronik.

Kein Blocker, aber der Grund, warum diese Gruppe nicht bei B steht: sie ist die einzige,
deren Loeschung ein lebendes Werkzeug auf seinen Ausweichpfad zwingt.

## D) Bloecke und Monolithe (Schritt 4)

- **Waisen jetzt: 0** (`python tools/cache_inventory.py --orphans`, 13.955 Bloecke,
  5.495 MB, 5.320 Korpusdateien). Erst NACH einer Korpus-Loeschung entstehen Waisen; dann
  `--print-delete-list`, danach `--orphans` noch einmal (muss leer sein).
- **Monolithe: 12 Dateien, 6,42 GiB.** Vier grosse `.cache_*.h5` (1.230,3 / 1.133,9 /
  1.126,8 / 1.111,8 MiB), sechs kleine, dazu `.par_full_79.h5` (874,1 MiB) und
  `.ref_serial_79.h5` (873,8 MiB) aus dem Cache-Parallelbau.
  **Geprueft: KEIN Trainings-Manifest in `models/` nennt ein `cache_file`** -- die
  Zuordnung Monolith-zu-Fenster ist aus den Manifesten also nicht lesbar. Alle `.h5` sind
  nach `tools/backup_excludes.txt` bewusst NICHT gesichert, weil sie aus dem Korpus
  nachgebaut werden koennen. Wer sie loescht, kauft Wiederaufbauzeit fuer Platz; das
  v25-Fenster hat dafuer 69 s Datenaufbau gebraucht (`laufzeit.datenaufbau_s` im
  Trainings-Manifest), der Monolith-Bau steht in der Kette davor.

## E) Modelle (Schritt 5) -- Vorlage, keine Empfehlung

**Belegt:** jeder Arm hat seinen eigenen restic-Stand (`restic snapshots --tag
models-snapshot`): `run:v24-b01` cf4519e3, `run:v24-b02` ac8be02c, `run:v24-b03` 73ce7625,
`run:v24-b04` c6877ec9, `run:v24-b05` 73b5c104, `run:v24-b06` f003e008, `run:v25-b01`
028989fb.

Kandidaten waeren die Arme ohne Rolle: `models/alphazero_v24-b0[1-5]*` (50 Dateien,
324,6 MiB; je Arm `.onnx`, `_best`, `_brierbest`, die `.pth` dazu, `.ref.txt`,
`_loss.png`).

**Nicht loeschbar und nicht in der Liste:** `v25-b01` (Champion und Generator fuer v26),
`v24-b06` und `v24-b07` (Elo-Knoten mit Kanten), alles unter `models/frozen_champions/`
und `models/frozen_heuristics/`, `models/engine_test.onnx` (Test-Fixture), die
`*.spec.json`.

**Einschraenkung, die der Nutzer kennen muss:** die v24-Arme sind Elo-Knoten mit Kanten in
`elo_history.csv` (b01 bis b05 haben je zwei bis vier Zeilen). Geloescht sind sie als
Zahlen weiter da, aber nicht mehr nachspielbar, ohne sie aus restic zu holen.
