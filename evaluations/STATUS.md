# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-19
(Generationswechsel v30 -> v31, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-19 (vor der
Neufassung zum Generationswechsel v30 -> v31)"**, der **"Generationsbericht v30 (2026-09-18
bis 2026-09-19)"** als Kapitel davor, die Generationsberichte v24 bis v29 weiter oben.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen. Wer ein Ergebnis
registriert, greppt nach seinen KONSUMENTEN (CLAUDE.md, Rueckwaerts-Pruefung).

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**STAND 2026-09-25 -- der Champion-Wechsel `v31-b01` -> `v32-b01` ist abgeschlossen.**
Der fruehere Abschnitt 1 (Stand 2026-09-23) steht woertlich in `../archive/history.md`.

**LAEUFT: NICHTS.**

**FERTIG: Promotion `v32-b01_brierbest`**, alle Punkte von `docs/promotion_checklist.md`,
vollstaendig in `PREREG_v32_window.md` **par.11**. Elo **1480 [1431; 1529]** gegen 1450 des
Vorgaengers; Champion-2 94:56 trifft die transitive Erwartung; R4, R4b, R5, Platt und sigma/Prior
auf Nutzer-Anweisung gefahren und alle GEPAART gegen v31. Spec unveraendert (Startkuppel-Suche
erst ab v33, `PREREG_start_dome_choice.md` par.12). `frozen_champions/` traegt `v31-b01` und
`v32-b01`; `v30-b02` ist geloescht (restic `4137c235`).

**FERTIG im selben Zug** (Wheel live `46b5dfed...`, Paketversion 1.1.0 unveraendert; Anker-Drift
und -Konservierung gruen, 693 Lib-Tests gruen):

* **Die GUI-KI spielt wie gemessen** (`PREREG_dome_return_order.md` par.14-14b). `py.rs` setzte
  das Tor `extended_action_nodes` nie; die Browser-KI wich bei Mondstapel, Stapelzug und Rueckgabe
  vom gemessenen Agenten ab. Rauchtest gruen.
* **Das Lauf-Manifest traegt Spec-Inhalt und sha256** (`selfplay_manifest.py` `spec_file`), noetig,
  sobald v33 zwei Specs faehrt (siehe unten). Erledigt damit Abschnitt 6 Punkt 7.
* **Der pre-push-Haken laesst bei unbekannter Basis nicht mehr still durch.** Erreichbar war das
  bei einem Force-Push, dessen Remote-Stand lokal fehlt; dann haetten beide Waechter ungeprueft
  durchgewinkt. (Beim Push-Versuch vom 2026-09-25 lief der Haken gar nicht: Git hat den
  Nicht-Fast-Forward clientseitig abgewiesen.)
* `frozen_referee_match.py` und `gumbel_scale_calibration.py` schreiben ihren `laufzeit`-Block.

### WAS JETZT ANSTEHT (v33)

1. **Nutzer-Entscheid vor der Erzeugung: WELCHE Schwarm-Klasse ohne Huellenknopf laeuft**
   (`PREREG_geometric_envelope.md` par.14d). Entschieden ist: der Sockel bleibt ganz und
   huellen-an, EINE der beiden Schwarm-Klassen (`value-tempc` oder `value-excursion`, je 4.000)
   faehrt mit `envelope_search_c 0,0` -- also eine zweite Spec-Datei fuer genau diese Klasse.
2. **`/mosaic-generation-turnover` VOR dem v33-Self-Play.** Generator `v32-b01` ist eingefroren.
   Rotation: G = `v32-b01`, G-1 `v31-b01` (die v32-Erzeugung), G-2 `v30-b02` (die v31-Erzeugung);
   **`v29-b11` faellt heraus.** Seeds nach dem Vierer-Schritt HERGELEITET, beim Anlegen der
   v33-Prereg zu pruefen: Erzeugung 20260942/43/44, Fenster 20260957.
3. **Champion-Spec der Generation v33:** `start_by_search: 1` eintragen (par.12, Wiedervorlage).
4. **Push** der umgeschriebenen Historie: nur als Force-Push, Befehl in Abschnitt 7.

**Vormerken fuer den v34-Wechsel:** R4 und R4b stehen fuer die Paarung auf
`data/selfplay_v30-b02-policy_*` (72 Zustaende, Seed 20260803). Diese Generation rotiert beim
v34-Wechsel heraus -- wer die Zeitreihe weiter gepaart fuehren will, sichert vorher die 72
Zustaende, sonst endet die Vergleichbarkeit mit dem Korpus.

### FREIGABEN UND VERBOTE (woertlich)

* Nutzer 2026-09-25: *"2 und 3 machen, bei 4 nimm a. fuer 1 machst 4000 schwarm spiele ohne
  huellenknopf. welche von den 2 x 4000 wir nehmen koennen wir uns noch ueberlegen"*.
* Nutzer 2026-09-25: *"v30-b02 kannst loeschen"* -- ausgefuehrt und verbraucht. Jede weitere
  Loeschung braucht restic-Beleg UND neue pfadgenaue Freigabe.
* **Kein Push ohne Anweisung.** Nie committen: `player_profiles.json`, `player_profiles.json.bak`.
* **Kein Commit waehrend eines Wanduhr-Laufs.** Messungen exklusiv; ein Build zaehlt als Last --
  und ein `grep -rn` ueber `data/` auch (Vorfall 2026-09-25, Champion-2-Kante, per Wiederholung
  als folgenlos belegt).

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v32-b01_brierbest`** (Promotion 2026-09-25), nach aussen
**Tessa** (der Anzeigename steht fest in `static/js/app.js`, er wandert mit jedem Champion mit).
**Elo 1480 [1431; 1529]** aus 1.000 Partien im Leitersegment 2, Anker `hv4_anchor` fix 1000,
Bradley-Terry mit Block-Bootstrap. **Keine seiner vier Kanten ist frueh gestoppt.**

Vier Kanten tragen ihn: Gating gegen `v31-b01` 434:366 ueber zwei Seeds (Block-z +2,37, aber nur
EIN Seed einzeln signifikant: +3,26 gegen +0,10), Anker @150 mit n = 50 auf 43:7, Champion-2 gegen
`v30-b02` 94:56 (binomial p = 0,0024) -- die Champion-2-Kante trifft diesmal die transitive
Erwartung (61,7 hergeleitet, 62,7 gemessen). Herleitung: `PREREG_v32_window.md` par.11.

| Modell | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| **v32-b01@400 (Champion, Tessa)** | **1480** | **[1431; 1529]** | **1.000** |
| v31-b01@400 | 1450 | [1406; 1496] | 1.800 |
| v30-b02@400 | 1411 | [1371; 1453] | 1.890 |
| Heuristik_hv4_anchor@150 (Anker) | 1000 | fix | 1.700 |

Die uebrigen Knoten stehen im Bericht von `tools/elo_tracker.py report`; das Primaerregister ist
`evaluations/elo_history.csv`.

**Engine-Stand:** Paketversion **1.1.0**, Vertragshash `6ef829e564c58bd5`, 888/414. Live ist seit
2026-09-25 das Wheel `46b5dfed...` (GUI-Tor, `PREREG_dome_return_order.md` par.14b); gemessen und
eingefroren wurde `v32-b01` auf `e11ea6d5...`. Beide tragen dieselbe Versionsnummer -- die Version
geht weder in den Hash noch in einen Cache-Schluessel noch in den Handshake ein, und das Artefakt
identifiziert sein Wheel ueber den sha256. Anker-Drift und -Konservierung ueber den Wechsel gruen.

**Eingefrorene Artefakte:** `models/frozen_champions/` traegt genau `v31-b01` und `v32-b01`
(Zwei-Champion-Regel). **`v30-b02` ist am 2026-09-25 geloescht**, Beleg restic-Snapshot
`4137c235` (7 von 7 sicherungswuerdigen Dateien mit gleicher Groesse; das `venv/` ist per
`backup_excludes.txt` ausgenommen und aus dem mitgesicherten Wheel neu baubar). Seine Kanten
stehen unveraendert im Register. **Seit dem 2026-09-23 sind `.onnx`, `.pth` und Wheels der
Artefakte NICHT im Repo** -- getrackt werden Spec, Manifest, Golden Probe und `wheel.sha256`.

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `../docs/measured_runtimes.md`)

| Aufbau | Dauer | Anmerkung |
| --- | --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11, 888/414 | **13,86 h** (v30) | 9,92 h (v28) / 12,8 h (v29); Sockel 18.984 s, temperiert 16.184 s, Ausflug 14.744 s |
| Erzeugungskosten je Partie @100, Policy-Klasse | 3,183 (v28) / 3,943 (v29) / **4,746** (v30) | +20,4 Prozent gegen v29, +49,1 Prozent gegen v28 |
| Blockbau fuers Fenster, Bloecke vom Waechter vorgebaut | 4 s plus **611 s** Merge | v30-Kette |
| Blockbau 2.800 Dateien plus Merge, 6 Worker, 884 | 2.144 s = 35,7 min | +9,2 Prozent gegen 794 |
| Training Warmstart 12 Epochen, 4,89 Mio Samples, 888/414 | **5.573 s = 1,55 h** (gebremst) | v30-b02, lief neben der b01-Arena; exklusiv frueher 57 min |
| Training KALTSTART 12 Epochen, 888/414 | **3.652 s = 1,01 h** | v30-b01; die alte ANNAHME 2,3-2,6 h stammte aus einer anderen Encoder-Aera |
| Tor 1 je Seed, 200 Paare @400, 10 Threads, mit Logs | **5.719 s** exklusiv / 6.940-7.468 s gebremst | 14,3 s je Partie exklusiv, 17,4-18,7 s gebremst |
| Anker-Kante n = 50 | **430 s** | seit 2026-09-19 die Groesse der Promotionsliste; n = 150 war 1.250-1.280 s |
| Champion-2-Kante n = 150 | **2.489 s = 41,5 min** | |
| Champion-Kanten je Kandidat gesamt | rund 3,5 h | 2 x Gating plus Anker plus Champion-2 |
| Promotion nach Checkliste (inkl. Golden-Probe 22 min) | 38 min | v29-Messung |
| Netz-Gesundheit komplett (Normen, tote Einheiten, offline, Platt) | rund 30 min | v30 |
| Voller Build: Lib-Tests, `--no-run`, Fixtures, Wheel | rund 5 min | `--no-run` allein 56 s |
| Anker-Drift / Anker-Konservierung | 22,4 s / 16,6 s | je 1.763 Schritte |
| Tagesschnappschuss restic plus check | 6-7 s | |

## 4. SPEC UND REZEPT

**Champion-Spec** `models/frozen_champions/v30-b02/spec.json`. **Erzeugungs-Spec**
`models/v30_generation.spec.json` (= `start_by_search_on.spec.json` plus `return_order_mode: 1`);
sie traegt auch die v31-Erzeugung.

**Engine-Stand:** INPUT_SIZE **888**, NUM_ACTIONS **414**, Vertragshash `6ef829e564c58bd5`
(unveraendert durch Gruppe A des Aufraeumens). Suchknoten: Mond 406-410, Rueckgabe 411-413,
Slot und Rotation als eigene Knoten mit Policy-Ziel. **Die Rueckgabe-Streuung sitzt seit
2026-09-19 im KNOTEN-Weg** (`self_play.rs`, eigener Seed-Unterscheider), die Maske dazu in
`engine/py/corpus_dataset.py` als eigene Bedingung auf `return_order_randomized` -- nicht ueber
`policy_target_valid`, weil beide Ketten `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` fahren.

**Das v30-Rezept, belegt:** b03-Rezept mit `--moon-loss-weight 0`, `--ownership-weight 0` mit
`--ownership-head-2d`, ohne `--endgame-head`, `--opp-points-head` bleibt, 12 Epochen, lr 5e-05
cosine mit `--lr-t-max 12`, lambda 0,7, `--select-by-brier`, `--fast-loader`.

**Was v30 daran entschieden hat:** der KALTSTART ist widerlegt. Gleiches Fenster, gleicher
Monolith, gleicher Seed, gleiches Rezept, einziger Unterschied der Start -- 404:396 kalt gegen
443:297 warm, **9,36 Prozentpunkte**. Fuer v31 heisst das: **Warmstart von
`v30-b02_brierbest`**, kein Kaltstart mehr ohne eigenen Anlass.

**v31-Fenster** (`PREREG_v31_window.md` par.1): 2.947 Dateien aus `v30-b02` neu (1.201),
`v29-b11` als G-1 und `v28-b02` als G-2; `v27-b01` ist herausrotiert und geloescht. Seed
20260949, Val-Pool `^selfplay_v30-`, 580 Traeger. Die acht neuen Knoten sind erstmals in den
beiden juengsten Generationen belegt, also rund 81,6 Prozent des Fensters (HERLEITUNG aus par.1,
nicht am Korpus nachgezaehlt).

## 5. PREREG-BESTAND (2 OFFEN laut Index 2026-09-22; Ziel rund 7)

| Prereg | Was noch aussteht |
| --- | --- |
| `v32_window` | der laufende Zyklus selbst; Erzeugung laeuft seit 2026-09-22 |
| `difficulty_levels` | ganze Leiter auf den letzten Champion vertagt |

Am 2026-09-22 geschlossen: `claude_play_interface` (zehn Partien gespielt, Anzeige-Fix par.13
gebaut). Davor bereits auf ENTSCHIEDEN gezogen und darum aus der Tabelle raus: `v31_window`,
`dome_return_order`, `code_cleanup_closeout`.

Beim Generationswechsel am 2026-09-19 nachgezogen: die Koepfe von `v30_window` (auf
ENTSCHEIDEN), `code_cleanup_closeout` (Gruppe A) und `dome_return_order` (Dosis 0,81), danach
`python tools/generate_prereg_index.py`.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. **Ein oder zwei Arme fuer v31** (`PREREG_v31_window.md` par.5 Punkt 2). v30 fuhr kalt und
   warm; der Warmstart gewann mit 9,36 Punkten Abstand, die Kaltstart-Frage ist damit
   beantwortet. Ein zweiter Arm braucht also einen ANDEREN Faktor, sonst reicht einer.

2. **Budget-Knopf fuer die Hilfsknoten** (Slot, Rotation, Rueckgabe, Mond). Die Kosten sind
   hingenommen (Nutzer 2026-09-18: "wenn es was bringt stoert mich der mehraufwand nicht"); offen
   ist allein die WIRKUNG, und v31 ist der erste Zyklus, in dem sie beantwortbar ist: in v30
   waren die Knoten mit 40,8 Prozent Fensterabdeckung vorregistriert unterbelegt, jetzt sind es
   rund 81,6 Prozent. Trennung aus dem Lernstoff: der **Mondknoten** traegt in 11,64 Prozent der
   Sockel-Records ein Policy-Ziel, der **Rueckgabeknoten in 0,18 Prozent**.

3. **Gruppe B des Aufraeumens**, drei Punkte, je eigener Entscheid: der Wrapper
   `resolve_and_apply_stack_draw` (ein Test ruft ihn auf) und die drei Spec-Felder aus
   `KNOWN_FIELDS` (drei rote Tests, Alt-Specs duerfen sie tragen), beide
   `PREREG_code_cleanup_closeout.md` par.8d; dazu die **Kanonisierung der Bonuschip-Farben**
   (par.8e): fuenf zweifarbige Kombinationen liegen je zweimal im Pool, bei zweien ist die
   Reihenfolge zwischen den Zwillingen vertauscht (`dome.rs:250-273`, Quelle
   `docs/bonus_chips_colors.csv`). Wertung und Netz-Eingabe sind davon unberuehrt (Bitmaske bzw.
   Farb-Flags); Arbeit kostet es in `round5.rs:281` (ein Zufallsast zu viel) und
   `tiling_solver.rs:331` (Cache-Fehlgriffe). **Die Chip-Kanonisierung ist in Anzeige UND Engine gebaut** (2026-09-19/20, CHANGELOG
   v1.0-alpha31, `PREREG_code_cleanup_closeout.md` par.8e); offen sind nur die beiden anderen
   Teile, der Wrapper und die drei Spec-Felder.

4. **ERLEDIGT: die Golden Probe des Ankers ist nicht mehr dauerhaft ROT.** Weg (a) ist seit dem
   2026-09-20 gebaut (Commit `a9302ecb`, *"Drift-Pruefer normalisiert Bonuschip-Farben, eng
   begrenzt"*: `_first_divergence` ordnet nur die Felder `colors` und `unused_chip_colors`, nur
   Listen reiner Zeichenketten). Dieser Eintrag stand danach noch fuenf Tage als offen hier; der
   Nutzer hat am 2026-09-25 (a) bestaetigt, und die Anker-Drift ist am selben Tag ueber 1.763
   Schritte gruen.

5. **R5- und R4b-Sonden der Promotionsliste:** fuer `v32-b01` auf Nutzer-Anweisung gefahren
   (*"r5 und r4b mitfahren"*, 2026-09-25), alle GEPAART gegen v31; die Aufrufe stehen jetzt in
   `docs/promotion_checklist.md` Punkt 5. OFFEN bleibt nur, ob sie ab v33 Pflicht sind oder je
   Promotion erfragt werden.

6. **Push der umgeschriebenen Historie.** GitHub steht auf `165d1243`, lokal umgeschrieben als
   `7b128e35` -- es liegt dort also nichts, was hier fehlt. Ein normaler Push wird abgewiesen (so
   geschehen 2026-09-25); **NIE `git pull`**, das holte die alte Historie samt 227 MB zurueck.
   Befehl in Abschnitt 7. Der Nutzer pusht selbst.

### Aeltere, weiterhin offene Punkte (unveraendert uebernommen)

6. **Brier-Regel:** bei `v30-b02` gerissen (0,26196 gegen 0,25507 auf `frozen_v1`), bei `v31-b01`
   gestreift (0,22919 gegen 0,22804 auf `frozen_v3`). **Bei `v32-b01` haelt sie**: 0,22864 gegen
   0,22919, im selben Lauf gemessen, und v31 reproduziert dabei seinen Wert exakt
   (`PREREG_v32_window.md` par.11). Offen bleibt der Grundsatzpunkt: `frozen_eval_set` stammt aus
   einer aelteren Verteilung.

7. **ERLEDIGT 2026-09-25: das Manifest traegt die Spec.** `engine_config` meldet weiterhin den
   Env-Default (bewusst unveraendert, damit alte und neue Manifeste diffbar bleiben), daneben steht
   jetzt `spec_file` mit Pfad, sha256 und Inhalt (`selfplay_manifest.py`, vier Tests). Anlass zum
   Bau war v33, das zwei Specs faehrt (`PREREG_geometric_envelope.md` par.14d).

8. **Sichtluecke bei den gezogenen Stapelplatten** (`stack_top_feature` par.16/16a): die
   Vorderseiten sind erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste verraet sie ueber die
   Rotationsfilterung (`game.rs` Z.402) -- betrifft die Suche, Reparatur beruehrt `NUM_ACTIONS`.
   (b) `serialize.rs` Z.375-379 serialisiert sie sofort, die Anzeige druckt sie -- betrifft den
   menschlichen Spieler, eingetreten in Partie g07.

9. **Paritaets-Tor und Alt-Records** (`rust_data_layer` par.9/9a): Kanal 76 weicht auf Records
   von vor dem A2-Fix ab, weil das Tor eine GESPEICHERTE gegen eine frisch gerechnete Groesse
   haelt. Offen: gespeicherte Felder aufgeben oder das Tor auf frische Zustaende beschraenken.

10. **Drei Sonden zeigen auf das geloeschte Artefakt `hv1_anchor`**
    (`anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
    `frozen_worker_protocol_probe.py`). Umstellung auf `hv4_anchor` braucht neue
    Erwartungswerte, also einen Lauf. Lohnt das, oder entfallen die drei als historisch?

11. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
    Loeschung; zuletzt am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

12. **Rahmen:** v30 ist released, das Schlussmodell heisst **Tessa**, und v31 laeuft, "damit die
    ganzen aenderungen wirklich sauber durchschlagen". Ab v30 keine neuen Preregs; Arme nur aus
    den jetzt offenen Preregs, Aufnahme ins Rezept per Nutzer-Entscheid.

13. **Kleinkram:** die Dry-Artefakte `evaluations/artifacts/_dry_*.json` vom Sonden-Bau koennen
    weg (Verzeichnis ist git-ignoriert).

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe. Frage ist keine
  Anweisung. `.h5`-Dateien sind per `tools/backup_excludes.txt` nicht im Backup, weil
  regenerierbar -- fuer sie gibt es keinen Snapshot-Beleg.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein Build
  zaehlt als Last. **Kein Commit waehrend eines Wanduhr-Laufs.**
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`. Nach `git add -A` die zwei
  Profil-Dateien gezielt mit `git restore --staged` herausnehmen.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch. **Auch eine reine Kommentaraenderung zaehlt** (Verstoss
  2026-09-20 am `corpus_dataset.py` waehrend des Cache-Waechters, folgenlos geblieben): das
  Risiko ist das Schreibfenster, nicht der Inhalt -- ein Worker, der genau dann importiert,
  sieht eine halbe Datei.
- **Knoepfe, die self_play.py kennt, gehen als CLI-Flag hinein**, nicht ueber die Umgebung:
  `self_play.py` setzt die Variable aus seinem eigenen Default neu (Z.236-240).
- **Kettenskripte als DATEI starten** (`bash tools/x.sh`), NIE Heredoc-schreiben-und-starten in
  einem Befehl.
- **Lange Laeufe nie in eine Pipe und ohne eigene Umleitung**, mit Fortschritt (`python -u`,
  `flush=True`).
- **Vor dem Self-Play der naechsten Generation: `/mosaic-generation-turnover`** -- der Ablauf
  gehoert VOR den Start, nicht daneben (Vorfall 2026-09-19).
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, sechs
  Standard-Kennzahlen in jedem Messbericht, kein Geviertstrich in Dateien, Bezeichner englisch,
  Inhalte deutsch.
- **Eingefrorene Netze sind NICHT mehr im Repo** (Nutzer-Entscheid 2026-09-23, Umschrieb am
  selben Tag gefahren: 227,5 -> 33,7 MiB). Champions behalten Spec, Manifest und Golden Probe
  und bleiben identifizierbar; ihre `.onnx`/`.pth`/`.whl` und die Heuristiken GANZ liegen nur
  noch im Arbeitsbaum und in restic. Ein frischer Klon hat damit kein lauffaehiges Netz -- der
  Nutzer stellt eines bereit, wenn es gebraucht wird. **Kein `git add -f`** fuer kuenftige
  Champions. Die Elo-Zahlen der Heuristik-Knoten stehen im Register `elo_history.csv`.
  Der Umschrieb hat JEDEN Commit-Hash ersetzt: bestehende Klons sind ungueltig, und der noch
  ausstehende Push ist ein Force-Push (nur auf Anweisung). **Nie `git pull`** -- das holte die
  alte Historie samt 227 MB als Merge zurueck. Mit Lease auf den am 2026-09-25 per
  `git ls-remote` gepruefte GitHub-Stand (lokal `7b128e35`, in `.git/filter-repo/commit-map`):
  `git push --force-with-lease=main:165d1243de1485092b0d2b70541ce93f365e01e7 origin main`.
  **Lokal ist das Repo derzeit wieder 227 MiB gross:** die Desktop-App hat `origin` am
  2026-09-23 um 18:49, zehn Minuten nach dem Umschrieb, im Hintergrund geholt
  (`refs/remotes/origin/main` = `165d1243`), und damit die alte Historie zurueck in den Pack
  gezogen. Gemergt ist nichts. NACH dem Force-Push schrumpft es erst wieder mit
  `git reflog expire --expire=now --all` und `git gc --prune=now`.
- Keine neuen Netzkoepfe; nicht jeden Arm in die Elo-Leiter.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Arena-Logs tragen keine `#a`-Zeilen**, weil die im PyGame-Pfad geschrieben werden
  (`py.rs:781`). Der Replayer riet dort die Rueckgabe-Reihenfolge kanonisch und divergierte in
  15-18 Prozent der Partien. Repariert ueber den Endzustand im Artefakt (`score_geo`,
  `dome_grid`); Tor 2b ist ab der naechsten Arena wieder verwendbar. Server- und Mensch-Logs
  waren nie betroffen.
- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **SPRT stoppt zwischen Nachbar-Generationen nicht** (beide v30-b01-Laeufe `UNDECIDED_CAP_REACHED`),
  bei groesserem Abstand sehr wohl. Beim Gating bleibt der Stopp aktiv und zieht unter 150 Paaren
  eine Replikation nach; nur die Anker-Kante faehrt ohne ihn.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe.** Beide enden in `select_final_root_child`,
  ohne Wurzelrauschen, mit Runde-5-Kurzschluss. Die GUI spielt immer bei 400 Sims. Latente
  Sollbruchstelle: die Arena zieht `builder_drafting_preference` der Suche vor, der Serverpfad
  kennt den Vorzug nicht.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf, der
  in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, allein ueber
  die VOLLENDUNG; die Teilspalten bleiben gleich.
- **Kein zurueckgehaltener Satz der laufenden Aera:** jede Datei in `data/` liegt in mindestens
  einem Fenster, deshalb ist der Trend ueber die Generationen nicht von der Verteilungsnaehe
  trennbar. Der Handgriff waere, vor dem v31-Training eine Scheibe des frischen Self-Plays zu
  reservieren und aus der Fensterliste zu nehmen.
- **Pfadform der Dateiliste im Cache-Schluessel:** Stempel und Verbraucher stimmen ueberein, die
  eigentliche Reparatur (Normalisierung auf Basenames) entwertet jeden Monolithen und ist
  Nutzer-Entscheid an einem Generationswechsel.
- **Python-Werkzeuge nach einem Kontraktwechsel:** `tools/offline_diagnosis.py`,
  `tools/oracle_metrics.py` und `tools/probes/*_gate.py` uebergeben `num_actions` noch explizit
  und laden Alt-Checkpoints darum nicht.
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
