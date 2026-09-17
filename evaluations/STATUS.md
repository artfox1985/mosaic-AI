# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-13, 13:10
(Generationswechsel v28 -> v29, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-13 (vor der
Neufassung zum Generationswechsel v28 -> v29)"**, die Generationsberichte v24 bis v28 ebenfalls
dort.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen.

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**UEBERGABE 2026-09-16, 22:00 (Sitzungswechsel, Kontext voll).** Anlass: eine Nacht mit zwei
Vorfaellen (Ketten-Stillstand, ueberschriebener Monolith) und der daraus folgenden
Cache-Sanierung auf Nutzer-Auftrag.

### LAEUFT

**Stand 2026-09-17, 05:05: NICHTS laeuft, die Maschine ist frei. Das v29-Programm ist bis auf die
Nutzer-Entscheide durch** (b04 negativ, Variante B negativ, b06 unterlegen; Einzelheiten unten und in
den Preregs). ~~Stand 01:40: zwei Ketten laufen parallel~~ (Chronik): (1) `tools/night_v29_b06_minimal_core.sh` -- Training
v29-b06 auf der GPU seit 01:35 (Monolith `data/.cache_fd13f54061cd_b06.h5`, Stempel geprueft), danach
wartet die Kette auf freie CPU fuer Tor 1 gegen b03 (Seeds 20261140/20261141); (2)
`tools/night_v29_rt_leaf_gates.sh` -- Kostentor Nr. 35 (an gegen aus, je 20 Paare) seit 01:35,
bei bestandenem Tor A/B Nr. 36 (200 Paare, Champion mit gegen ohne `MOSAIC_ROUND_TRANSITION_LEAF`).
**Kostentor DURCH 01:55 (par.17.8): +6,6 Prozent Wanduhr, Tor haelt; pseudo-terminale Blaetter 1,64 Prozent.
A/B laeuft seit 01:54:36, erwartet bis etwa 03:30.** **A/B DURCH 03:13 (par.17.9): NEGATIV** --
169:191 von 360, Block-z -1,13, Punkte -1,3, Strafleiste +0,8; Variante B kommt nicht ins Rezept,
Fahrplan 33-36 sind damit abgeschlossen. Werkzeug-Defekt dabei: die `[rt_leaf]`-Logzeile bricht
den Replayer (`analyze_game_log.py`), Spaltensonde fuer alle mit-Knopf-Laeufe ROT -- Reparatur
delegiert, Nachspiel nach Tor 1 von b06. **b06 TRAINIERT (02:32, 57 min; Koepfe aus). Tor 1 gegen b03 DURCH 04:54
(`minimal_strength_core` par.10.3): UNTERLEGEN, 236:294 von 530 (44,5 Prozent), McNemar p 0,011,
Block-z -2,86 -- die 5-Prozentpunkte-Marge reisst; mit b05 zusammen: mindestens einer von
ownership/opp_points/endgame traegt als Trainingssignal.** Netz-Gesundheit b04/b05/b06 GRUEN (2,60
Prozent tote Einheiten wie b03). Spaltensonde fuer die Variante-B-Laeufe nachgeholt (17.9a).
Kein Commit, solange die Tore-Kette laeuft (Wanduhr-Messung). Loeschkandidaten fuer den Nutzer:
`data/.cache_fd13f54061cd.h5` (falscher Stempel) und `models/manifest_train_v29-b06_20260917_011916.json`
(Manifest des vom Waechter abgebrochenen ersten Anlaufs).

**Der Nutzer faehrt v29-b04 selbst in seiner Shell** (ausdruecklicher Wunsch 2026-09-16:
*"gib mir den python befehl fuer b04. das werd ich in der shell fahren"*). Grund: der vorige
Lauf hing, und seine Ausgabe war nicht sichtbar, weil sie an einem gestorbenen Wrapper hing.
Der Befehl steht unten unter Schritt 1. **Die neue Sitzung startet ihn NICHT selbst** -- sie
begleitet ihn, wertet aus und faehrt danach Tor 1.

**BEOBACHTUNG DER NEUEN SITZUNG, 2026-09-16 21:30 (Lauf des Nutzers, PID 33436, Start
21:07:47, Manifest `models/manifest_train_v29-b04_20260916_210750.json`):**

* Manifest geprueft: `--cache-file data/.cache_be157f1118c0.h5` (Block `cache_file` traegt
  Schluessel be157f1118c0, 2800 Dateien, 4.538.842 Zustaende), `moon_target_source = played`,
  `policy_carriers.traeger_dateien_gesamt = 580`, Commit 6dd8cd47 (dirty). Die beiden
  Abbruchgruende Cache und Traeger sind damit ausgeraeumt.
* 21:07 bis 21:19 einkerniger Bau des Val-Caches (`.cache_dd33790fcc15.h5`, 147 Dateien,
  249.476 Zustaende, Fingerabdruck MOON_TARGET_SOURCE=played) -- CPU/Wanduhr 1,0, GPU 13 Prozent.
* **Seit etwa 21:20 Trainingsphase:** CPU/Wanduhr 5,6 (b03: 5,5), GPU 34-38 Prozent, erster
  Zwischenstand `models/alphazero_v29-b04_resume.pth` um 21:27:59. Das ist die Signatur eines
  GPU-Laufs mit `--fast-loader`; **die Device-Zeile selbst (`Starte PyTorch Training auf:`,
  `train.py:1584`) ist nur in der Shell des Nutzers sichtbar -- Nutzer 2026-09-16 21:40: "b04 laeuft auf cuda." BESTAETIGT.** Erwartung: 12
  Epochen a rund 7-8 min, Ende gegen 22:50.
* Beobachter laeuft als Hintergrundaufgabe dieser Sitzung (alle 120 s CPU-Sekunden, GPU-Last,
  neue b04-Dateien); kein eigener Start, kein Eingriff.

**b04 TRAINIERT (22:36) und TORE (a)/(b) GEMESSEN (22:45), `PREREG_moon_stack_order.md` par.12.7:**
1,48 h auf cuda, val_brier 0,17915 (Epoche 5), Manifest-Diff gegen b03 gruen. **Der Kopf hat auch
das reparierte Ziel kaum gelernt:** nll_played 0,976 gegen 0,989 bei b03 (1,2 Prozent),
Kopf-Favorit = gespielte Reihenfolge 40,1 Prozent bei allen drei Modellen, p_canonical
unveraendert 0,410; b03 und b05 sind im Mondkopf identisch (Warmstart-Kopf von v28-b02). Auf
jedem Ziel dieselbe NLL um 0,96-0,99: das Ziel ist aus dem Eingang kaum vorhersagbar. **Tor 1 DURCH (00:45, par.12.8): b04 traegt NICHT** -- Seed 1 89:121 (p 0,033, SPRT-Schranke
gerissen), Seed 2 198:202 (p 0,91); gepoolt 287:323 von 610, z -1,56. Vier-Ausgaenge-Lesart:
b05 traegt schwach, b04 nicht -> **Empfehlung `moon_loss_weight 0` ins v30-Rezept, Nutzer-Entscheid**
(Abschnitt 6 Punkt 12). Kein Elo-Eintrag. Netz-Gesundheit Punkte 1-2 fuer b04 stehen aus.

**URSACHE DES EIN-KERN-LAUFS VOM 17:32 -- Herleitung, kein Beweis:** dessen Manifest
(`..._173056.json`, inzwischen geloescht, vorher gelesen) hatte KEIN `--cache-file` und keinen
`cache_file`-Block; der Lauf suchte den Monolithen also ueber den errechneten Namen, fand ihn
wegen der Pfadform (`docs/pitfalls.md`, dritter Eintrag) nicht und baute ihn EINKERNIG in
`train.py` neu. Mit der gemessenen Rate aus `docs/measured_runtimes.md:61` (17.934 s fuer 2.228
Dateien = 8,05 s je Datei) braucht das fuer 2.800 Dateien rund 6,3 h -- nach drei Stunden also
mitten im Aufbau, ein Kern, GPU leer, kein Modell. Alle vier Symptome passen. Was fehlt: ein
Artefakt (unter `data/` liegt keine Datei mit Aenderungszeit zwischen 17:30 und 20:45, der Bau
schreibt erst am Ende) und die Konsolenausgabe des Laufs. Der zweite Versuch um 21:01 zeigte
denselben Einstieg sichtbar und wurde deshalb abgebrochen -- das ist die einzige direkte
Beobachtung. Damit ist der Punkt "Ursache ungeklaert" oben auf "Herleitung, konsistent, nicht
bewiesen" gesetzt; die Gegenprobe waere ein Lauf ohne `--cache-file` bei falschem Namen, den
niemand fahren muss.

**Abnahme-Instrument fuer Tore (a) und (b) aus par.12.1 gebaut:**
`tools/probes/moon_head_target_probe.py` (Val-Split `data/window_v29_b04_val.txt`, byte-gleich mit
b03s Val-Liste; NLL mit der Rang-Semantik des Trainings, `corpus_dataset.py:1488-1492`,
`train.py:125-149`). Trockenlauf (n = 300 Records, Grundmenge Val-Records mit mindestens zwei
Mondreihenfolgen in der Suchverteilung, Einheit nats bzw. Wahrscheinlichkeit; Artefakt
`_dry_moon_head_target_probe.json`): **b03 und b05 sind im Mondkopf praktisch identisch**
(nll_played 1,006 gegen 1,006; p_canonical 0,404 gegen 0,404; Kopf-Favorit kanonisch 36,3
Prozent beide) und liegen nur knapp unter der Gleichverteilung (1,168). **Erklaerung, am Code
geprueft:** der Encoder kodiert die Sonnenseite einer kleinen Fabrik als FARBZAEHLER
(`features.rs:1150-1158`, "5 Sun-Counts /5"), die Reihenfolge der Steine steht nicht im
Eingang -- das kanonische Label (Sonnenreihenfolge ohne die genommene Farbe) ist damit
UNLERNBAR, nicht nur konstant. b03s Kopf ist deshalb beim Warmstart-Stand von v28-b02 geblieben.
Folge fuer die Tore: (b) "Prior-Masse auf kanonisch faellt" hat bei b03 kaum Fallhoehe; das
tragende Tor ist (a), `nll_played` von b04 deutlich unter 1,006 und unter der Gleichverteilung.
Selbsttest par.12.0 je Record: 173 von 173 Labels sind die kanonische Reihenfolge einer
(Fabrik, Farbe) des Zustands, 0 Abweichungen.

**Manifeste geloescht (Nutzer-Anweisung 21:26, restic-Snapshot `8b7bda88` vorher, 67
Snapshots, Check ohne Fehler):** `models/manifest_train_v28-b03_20260911_201057.json`,
`..._v28-b04_20260911_221704.json`, `..._v29-b04_20260916_173056.json`,
`..._v29-b04_20260916_210102.json`. **Bewusst behalten:** `..._v29-b04_20260916_210750.json`,
das Manifest des laufenden Trainings -- es wird fuer den Manifest-Diff gegen b03 gebraucht.

**Delegiert (Opus, mittel):** Abnahme von `tools/cache_doctor.py` (Zahlen nachrechnen,
"verwaist"-Logik gegen den laufenden Lauf, 12 "Schluessel ohne Datei", Konventionen) und der
Namenspfad-Check des Cache-Laders (Punkt 2a, minimaler Eingriff plus pytest). Nr. 33
(Counterfactual-Sonde) folgt danach mit einer KOSTENMESSUNG bei kleinem n, nicht mit dem
Volllauf -- sims 400 / M 6 ist ungemessen, und Tor 1 braucht die CPU ab etwa 22:50 exklusiv.

### ERSTE AUFGABE DER NEUEN SITZUNG, in dieser Reihenfolge

**1. v29-b04 begleiten und abnehmen** (Fahrplan 32b, `PREREG_moon_stack_order.md` par.12.1).

Der Nutzer startet das Training. Drei Dinge in den ersten Minuten pruefen, jedes ein
Abbruchgrund -- sie sind genau die drei Punkte, die beim gescheiterten Lauf im Dunkeln lagen:

* **Device muss `cuda` sein.** Der Lauf vom 17:32 rechnete auf EINEM Kern (CPU/Wanduhr 1,0
  gegen 5,5 bei b03) bei GPU 4 Prozent und hatte nach drei Stunden kein Modell geschrieben.
  **Die Ursache ist bis heute ungeklaert** -- wer sie findet, traegt sie hier ein.
* **Cache: ERLEDIGT am 2026-09-16 21:07.** Der Lauf laeuft mit
  `--cache-file data/.cache_be157f1118c0.h5` und meldet *"Schluessel be157f1118c0 bestaetigt
  (2800 Dateien, 4538842 Zustaende). Kein Cache-Bau."* -- dieselbe Zustandszahl wie b03s
  Manifest. Der erste Versuch ohne `--cache-file` lief in den EINFAEDIGEN Cache-Neubau (genau
  die Phase, in der der Lauf vom 17:32 drei Stunden verbracht hat) und wurde abgebrochen.
  **Regel daraus: einen Cache immer ueber `--cache-file` adressieren**, nie ueber den
  Dateinamen hoffen -- der haengt an der Pfadform (siehe unten).
* **BEIDE Caches vorbauen, nicht nur den Trainings-Monolithen** (Nachtrag 2026-09-16 21:30 auf
  Nutzer-Anweisung). Der b04-Lauf hat den Trainingsanteil in 31,2 s geladen und danach den
  147-Dateien-VAL-Anteil EINKERNIG neu gebaut -- rund 20 Minuten, die niemand braucht.
  `docs/measured_runtimes.md:61` nennt die Rate: **17.934 s einkernig in `train.py` fuer 2.228
  Dateien = 8,05 s je Datei**, gegen **344 s** fuer dieselbe Menge mit
  `build_cache_incremental.py` bei 6 Arbeitern -- **Faktor 52**. Fuer 147 Dateien sind das rund
  1.183 s gegen rund 23 s (hochgerechnet aus der gemessenen Rate, nicht fuer genau diese
  Dateien gemessen).

  Vor JEDEM kuenftigen Trainingsarm also beide Anteile vorbauen und beide per `--cache-file`
  bzw. ueber den passenden Schluessel adressieren. Die Listen liegen schon:
  `data/window_v29_b04_train.txt` (2.800) und `data/window_v29_b04_val.txt` (147).

  **Und die unangenehme Lehre dahinter:** `docs/measured_runtimes.md:44` beschreibt genau
  diesen Fehler samt Loesung, seit v23 -- *"Training auf NEUER Fenster-Zusammensetzung,
  Datenaufbau EINKERNIG ... 7,42 h gesamt, davon 4,98 h Datenaufbau ... **Vermeidbar:**
  Fenster-Cache mit `build_cache_incremental.py --merge-out` parallel vorbauen, dann
  `train.py --cache-file`"*. Die Kostentabelle haette den Drei-Stunden-Lauf vom 17:32
  verhindert, wenn sie VOR dem Start gelesen worden waere. **Regel daraus: vor jedem Lauf ueber
  einer Stunde zuerst `docs/measured_runtimes.md` aufschlagen** -- sie traegt nicht nur Dauern,
  sondern in mehreren Zeilen auch den billigeren Weg.

* **`Policy-Traeger gesamt: 580`** -- steht dort 2947, fehlt das Traegermanifest (derselbe
  Fehlstart wie bei b05 am 2026-09-15, vom Nutzer an dieser Zahl erkannt). Abbrechen.

Danach **Tor 1 gegen b03**, zwei Seeds a 200 Paaren, Blockgroesse 5, OHNE Frueh-Stopp, mit
Logs; Befehle im Kettenskript `tools/night_v29_b04_moon_played_v2.sh` Schritt 4 (die **v2** ist
die gehaertete Fassung, die alte NICHT benutzen). Abnahme: Manifest-Diff gegen b03 zeigt GENAU
`moon_target_source` label -> played und den Namen, sonst nichts. Verdikt nach par.12.1; die
Lesart steht dort vorab. Danach Netz-Gesundheit Punkte 1-2 (`v29_window` par.6d).

**2. Cache-Sanierung zu Ende** (Nutzer-Auftrag 2026-09-16: *"setz die caches wirklich mal
sauber auf ... laesst sich als normaler bediener nicht mehr handhaben"*). Drei Lagen stehen
(Commit 6dd8cd4); zwei Luecken bleiben, beide in `../docs/pitfalls.md` beschrieben:

* **Der Ladepfad prueft Name gegen Inhalt nur bei `--cache-file`** (`corpus_dataset.py:909`
  ruft `verify_cache_file`), im Namenspfad gar nicht. Dort vertraut der Code dem Dateinamen.
* **GEKLAERT am 2026-09-16, und das ist der eigentliche Befund: der Schluessel haengt an der
  PFADFORM der Dateiliste.** Dieselben 2800 Dateien, dieselben Knoepfe, dieselbe Umgebung
  ergeben drei verschiedene Schluessel -- Basenames `9f2f1e01004c`, `data/x.pkl`
  `4a038a9eecbf`, absolute Pfade `be157f1118c0`. `train.py` und `window_train_split.py`
  rechnen ABSOLUT, also haengt jeder Monolith am Installationsort des Projekts;
  `build_cache_incremental.py` rechnet anders und schreibt deshalb Dateien, deren
  eingepraegter Schluessel nicht zum Dateinamen passt. EIN Datensatz trug dadurch nacheinander
  VIER Namen. Ein zweiter Fall liegt seit dem 2026-09-14 im Baum
  (`.cache_35c6bd2b9bd2.h5` traegt intern `41bfd55372ea`), das Problem ist also aelter als der
  Vorfall, der es sichtbar gemacht hat. Einzelheiten und Messung: `../docs/pitfalls.md`.

  **Zwischenschritt 2026-09-17 01:30 (nach einem zweiten Vorfall beim b06-Bau):** beide
  Zusammenfueger stempeln jetzt aus ABSOLUTEN Pfaden wie `train.py` -- damit stimmen Stempel und
  Verbraucher fuer Listen aus `window_train_split.py` ueberein. **Loeschkandidat (Nutzer):**
  `data/.cache_fd13f54061cd.h5` (1,15 GB, Stempel 4dd9f020b232, gebaut 01:19, vom Waechter
  abgelehnt); Ersatz `data/.cache_fd13f54061cd_b06.h5`. h5-Dateien sind vom Backup ausgeschlossen
  (jederzeit nachbaubar), ein restic-Beleg ist deshalb nicht noetig.

  **Die Reparatur ist benannt, aber NICHT gemacht und ein Nutzer-Entscheid:** die Dateiliste im
  Schluessel auf Basenames normalisieren (ein Datensatz ist durch seine Dateinamen bestimmt,
  nicht durch seinen Ablageort). Das entwertet JEDEN vorhandenen Monolithen auf einen Schlag
  und gehoert deshalb an einen Generationswechsel.

**3. `tools/cache_doctor.py` abnehmen.** Ein Subagent hat es am 2026-09-16 gebaut (710 Zeilen,
kompiliert); es soll je Cache zeigen, wem er gehoert, ob Name und eingepraegter Schluessel
uebereinstimmen und was verwaist ist. **Regel 0: Agenten-Befunde sind Behauptungen** -- die
tragenden Zahlen selbst nachpruefen, bevor sie irgendwo einfliessen. Committet in 40d7b0bc.

**ABNAHME 2026-09-16 21:50 (Opus-Agent, tragende Punkte vom Koordinator am Code nachgeprueft):**
die LESENDE Haelfte stimmt (h5-Attribute, Name gegen Schluessel, 12 zugeteilte Schluessel ohne
Datei alle echt, Bau-Artefakt, laufzeit-Block -- Feld fuer Feld nachgerechnet, 5 von 5
Monolithen). Die BESITZZUORDNENDE Haelfte ist falsch und darf nicht als Loeschhilfe dienen:
(D1) Val-Caches kennt die Statusleiter nicht -- `.cache_dd33790fcc15.h5` ist der Val-Cache des
LAUFENDEN v29-b04 (Schluessel nachgerechnet: `window_cache_key` der Val-Liste mit played/794 =
dd33790fcc15), `7ebef2449837` ist b01-val (755), `eaa464b44cf7` der 794/label-Val-Cache; alle
drei stehen als "verwaist" oder "nur benannt". (D2) `HEX_RE` mit `` trifft `.cache_<key>.h5`
nicht (Unterstrich), und Nennungen vorhandener Caches werden verworfen (`cache_doctor.py:402-407`).
(D3) `hat_laufzeit` wird erhoben und nie gelesen, ein laufender Lauf ist unsichtbar. (D4)
`arm_from_name` bekommt den Artefaktnamen statt der Liste. (D5) die Listen-Eindeutigkeit ist
tot, weil je Lauf eine byte-gleiche Kopie geschrieben wird (4 Trainingslisten md5-gleich).
Dazu D6-D11: Ausgabetext "Unterschied steckt in der Mitte" bei gleichen Dateien, Zahlformat
"2,372 MB" (= 2.372 MiB), "Fensterlisten: 49" zaehlt 8 Fremdlisten mit, Bau-Artefakt mit
Selbstwiderspruch (merge_out fd13f54061cd gegen cache_key 4dd9f020b232) wird nicht gemeldet,
21 deutsche lokale Bezeichner, verrottete Zeilenzitate. **REPARIERT 2026-09-16 22:00 (Opus-Agent,
alle elf Punkte; `tools/tests/test_cache_doctor.py`, 6 Tests gruen, vom Koordinator nachgefahren).**
Neuer Lauf (`cache_doctor_20260916b.json`, 66 s): `7ebef2449837` = val-cache v29-b01,
`eaa464b44cf7` = val-cache v29-b03-eval, `be157f1118c0` und `dd33790fcc15` = LAEUFT (v29-b04 seit
21:07:50, Prozessblick bestaetigt), `35c6bd2b9bd2` weiter ROT (Name ungleich Schluessel). Neuer
ROT-Befund `bau_artefakt_widerspruch`: `cache_build_incremental.json` fuehrt `merge_out`
fd13f54061cd gegen `cache_key` 4dd9f020b232 -- welches Feld den Bau beschreibt, ist eine
inhaltliche Klaerung (offen). Die zwei ROTEN `listenkonflikt`-Befunde (35c6, be157) sind die
Pfadform-Sache selbst: dieselbe Liste hat verschiedene Schluessel bekommen. Der Doktor ist damit
als Diagnose abnahmefaehig; als Loeschhilfe erst nach Nutzer-Blick auf jeden ROTEN Fall.

**4. Fahrplan Nr. 33** (`PREREG_round_transition_search_sampling.md` par.9/10, Variante B).
Die Stufe-0-Sonde dazu ist gebaut und vorregistriert (par.16,
`tools/probes/counterfactual_tiling_ranking.py`), der Volllauf steht aus. Laufbefehl und die
Begruendung der Stichprobengroesse stehen in par.16.7; **`--max-positions` ist das Soll JE
RUNDE**, nicht die Gesamtzahl (par.16.8), und der erste Volllauf faehrt `--rounds 4` allein,
weil nur dort die Wahrheitsquelle wertkopf-frei ist. Kosten bei sims=400/M=6: UNGEMESSEN.

**VARIANTE B GEBAUT (Opus-Agent, 2026-09-16 22:15; `PREREG_round_transition_search_sampling.md`
par.17, Fahrplan 33):** Knopf `MOSAIC_ROUND_TRANSITION_LEAF` (Default 0, bitidentisch, Spec-Feld
optional), Blatt-Eingriff in `make_node`, Neubefuellung im Blatt ueber `determinize_dome_pool`
(Betrachter = Suchender) plus `advance_one_chance` fuer Beutel und Chips, stellungsgebundener
Seed mit einer Zahl aus dem Suchstrom, Diagnosezeile `[rt_leaf]`, Mischstellen-Zeile in
`docs/architecture_reference.md`. 9 neue Tests gruen, vom Koordinator nachgefahren;
`cargo test --release --lib` nach dem Nachtrag des fehlenden Registratur-Eintrags
`MOSAIC_MOON_TARGET_SOURCE` (Erbe von 6dd8cd47, haette den pre-push gebrochen) komplett gruen.
**NICHT im Wheel** (Training lief): Wheel-Bau, Anker-Drift und Konservierung, Paritaets-Fixture
sind die Abnahme dieses Baus und kommen VOR Fahrplan 34 -- an einer freien Maschine, also nach
Tor 1 von b04. Zwei bewusste Abweichungen von der Prereg stehen in par.17.6 (Mischregel je
Vorrat; Seed-Verknuepfung mit einer Zahl aus dem Suchstrom statt Zustands-Hash mal Partie-Seed).

**ABNAHME DURCH UND SICHTTOR GRUEN (Opus-Agent, 2026-09-17 01:05, par.17.7; Fahrplan 33
abgenommen, 34 durch).** Das Wheel traegt den Knopf, **Kontrakt-Hash unveraendert
`39994362fba145a6`** (Manifest neu: `round_transition_leaf = 0`); Anker-Drift 22,4 s und
Anker-Konservierung 16,6 s gegen `hv4_anchor` beide GRUEN (je 1.763 Schritte), `cargo test
--release --lib` **673 gruen / 0 rot** samt `net_parity_hash_matches_champion_fixture` (Fixture
NICHT neu erzeugt), Konventionen gruen. **Sichttor par.10 GRUEN: n = 300 Blatt-Zustaende
(Runden 3 und 4, `bag_count` < 21, je 150) aus 1.647 gesehenen, 0 Verstoesse in allen drei vorab
festgelegten Kriterien**, 41,1 s. Neu im Baum: `tools/probes/round_transition_leaf_sight_gate.py`
und der ADDITIVE Diagnose-Export `round_transition_leaf_fill_diag_json` (`engine/src/lib.rs`) --
am HEAD gab es keinen Python-Einstieg in `round_transition_leaf_state`; deshalb wurde das Wheel
danach ein zweites Mal gebaut und beide Anker-Modi erneut gefahren (wieder GRUEN). **Offen in
dieser Reihenfolge: Kostentor par.5 Schritt 1 (Nr. 35), dann A/B par.9 (Nr. 36)** -- beide
ausdruecklich NICHT gestartet, sie taktet der Koordinator ein.

**FREMDER ROTER BEFUND am Rand, gemeldet und nicht untersucht (par.17.7 (f)):** die
Paritaetssonde `tools/probes/feature_parity_rust_python.py` faellt in der Korpus-Population
(298 von 300; `pygame` 733 von 733 gleich), Abweichung in Planes-Kanal 76 (Erreichbarkeit,
`features.rs:1733`). `42167aef` beruehrt `features.rs` nicht; letzte Aenderung dort ist
`36520a31` (2026-09-14), und `docs/knobs.md` nennt das Tor "bestanden 2026-09-11" -- der Befund
ist also aelter als der Variante-B-Bau. Artefakt
`evaluations/artifacts/feature_parity_rust_python.json`.

### FREIGABEN UND VERBOTE (woertlich, unveraendert gueltig)

* **Kein Push ohne Anweisung** -- Ahead-Stand im Chat melden. Stand 2026-09-16 21:30: **8 Commits** vor
  `origin/main`.
* **Loeschung nur auf pfadgenaue Nutzer-Freigabe**, mit restic-Beleg. Frage ist keine Anweisung.
* **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`. Die vier
  Alt-Manifeste (`v28-b03`, `v28-b04`, `v29-b04` vom 17:30 und 21:01) sind am 2026-09-16 21:27
  auf Nutzer-Anweisung geloescht (restic `8b7bda88`); `manifest_train_v29-b04_20260916_210750.json`
  gehoert zum laufenden Arm und wird mit ihm committet. Nach `git add -A` die zwei
  Profil-Dateien gezielt mit `git restore --staged` herausnehmen. (Vorschlag an den Nutzer,
  bisher nicht entschieden: in `.gitignore`.)
* **Messungen laufen exklusiv**, Builds zaehlen als Last; GPU und CPU duerfen parallel, zwei
  CPU-Messungen nicht. **Kein Commit waehrend eines Wanduhr-Laufs.**
* **Kettenskripte als DATEI starten** (`bash tools/x.sh`), NIE Heredoc-schreiben-und-starten in
  einem Befehl -- der Wrapper traegt sonst den Skripttext in seiner Kommandozeile, und die
  Wartebedingung findet sich selbst (32 min Stillstand am 2026-09-16, dazu die Nachbarsitzung
  blockiert; `../docs/pitfalls.md`).
* Keine neuen Netzkoepfe; nicht jeden Arm in die Elo-Leiter; Laufzeiten ins Artefakt; sechs
  Standard-Kennzahlen in jedem Messbericht; Bezeichner englisch, Inhalte deutsch.

### OFFENE NUTZER-ENTSCHEIDE

| Frage | Fundstelle |
| --- | --- |
| Dritter Seed als Stichentscheid fuer b05 (rund 75 min)? | `moon_stack_order` par.12.6, Nutzer 2026-09-16: *"den dritten seed fuer b05 heben wir uns auf falls er champion wird"* -- also nur bei Champion-Kandidatur |
| ~~Nr. 26: Claude-Partien g08-g10~~ | **ENTSCHIEDEN 2026-09-16: erst mit dem Schlussmodell (v30-Champion), als Abschluss nach den Preregs** |
| b03s Monolith neu bauen? | er ist ueberschrieben worden; Neubau rund 35 min aus den Bloecken, faellig erst wenn b03 wieder gebraucht wird |
| Dry-Artefakte `evaluations/artifacts/_dry_*.json` loeschen? | vom Sonden-Bau uebrig, Verzeichnis ist git-ignoriert |

### WAS IN DIESER SITZUNG PASSIERT IST (Kurzfassung, Einzelheiten in den Preregs)

Netz-Gesundheit Punkt 3/4 registriert (kein Befund, `moon_stack_order` par.12.6). Die acht
Review-Befunde zu par.14 abgearbeitet, drei am Code nachgeprueft; B3 aendert 14.5. Die
Counterfactual-Ranking-Sonde gebaut und vorregistriert (par.16), ihre Wahrheitsquelle als
wertkopf-frei BELEGT (`round5.rs:357` -- der Rueckfallwert ist eine exakte Punktezaehlung, kein
Netz). Zwei Betriebsvorfaelle behoben und dokumentiert. Cache-System saniert (Commit 6dd8cd4).
Der Arm v29-b04 ist abgebrochen und zu wiederholen.


Waehrend einer Messung darf nichts anderes Rechenlast erzeugen -- kein Build, kein cargo, keine
Sonde (CLAUDE.md). Ein Wheel-Neubau mitten in einer Kette liesse die Arme auf zwei Wheels laufen.

**Die v29-Erzeugung ist seit dem 2026-09-14 durch** (1.201 Dateien, 12,8 h); die Einzelheiten
und die Nebenlast-Offenlegung stehen unten. Der Vollstaendigkeit halber der Aufbau, unter dem
der Korpus entstanden ist -- Generator `v28-b02`, drei Klassen nacheinander, alle bei
**100 Sims**, `MOSAIC_STACK_DRAW_RESEARCH=1`, Spec `models/start_by_search_on.spec.json`,
`--start-slot-random-p 0.15`:

| Klasse | Seed | Soll |
| --- | --- | --- |
| `v28-b02-policy` (Sockel, policy-aktiv) | 20260920 | 400 Dateien |
| `v28-b02-value-tempc` (Schwarm, temperiert) | 20260921 | 400 Dateien |
| `v28-b02-value-excursion` (Schwarm, Ausflug) | 20260922 | 401 Dateien |

Erwartet rund 10,8 h (Hochrechnung aus gemessenen Werten; v28 lief 9,92 h). Daneben laeuft der
Cache-Waechter unter der Trainings-Umgebung. **Nichts anderes darf Rechenlast erzeugen** --
kein Build, kein cargo, keine Sonde.

> **OFFENGELEGT (2026-09-13/14, Nacht): diese Zusage ist gebrochen worden.** Waehrend der
> Erzeugung lief Nebenlast, und zwar in beide Richtungen: der Nutzer hat drei Push-Versuche
> gefahren, deren pre-push-Hook jeweils `cargo test --release` ausloest (je rund 3 min Volllast),
> und die Sitzung hat danach auf seine Frage "warum muss ich das machen?" vier weitere
> cargo-Laeufe, zwei Sonden-Selbsttests und einen Korpuslauf ueber 228 Dateien gestartet. Dazu je
> Commit der pre-commit-Hook mit 91 Tests.
>
> **Einordnung, nicht Entwarnung:** der Self-Play laeuft mit fester Simulationszahl, nicht gegen
> eine Uhr -- die Partien sollten dadurch langsamer, aber nicht anders werden. Die Regel in
> CLAUDE.md begruendet sich an einem Fall, in dem CPU-Nebenlast Partien verstuemmelt hat; ob das
> hier greift, ist NICHT geprueft. Wer den v29-Korpus auswertet, muss das wissen. Der Nutzer
> entscheidet, ob ihm das reicht oder ob die betroffenen Klassen neu erzeugt werden.

**Danach, in dieser Reihenfolge:**

1. **Tor 0 / Tor 2a je Klasse** (`corpus_sanity_check.py`, 271 s je Klasse gemessen).
2. **Offene Kleinigkeit der Sims-Kurve:** Plattenpunkte je Kriterium fuer die drei
   Teil-A-Laeufe nachfahren (das Kettenskript rief `plate_points_from_arena.py` ohne `--out`
   auf; je unter 5 s auf vorhandenen Logs).
3. ~~**Cache-Bloecke und Monolithe aufraeumen**~~ **BLOECKE ERLEDIGT 2026-09-14** auf Freigabe
   des Nutzers: 1.842 Waisen geloescht (744 MB), alle nachgezaehlt und verschwunden. Quellen
   waren v25-b01 (1.602 Bloecke) und zwoelf Messkorpora der Sims-Kurve und der c2-Ablationen.
   Kein restic-Beleg noetig -- `tools/backup_excludes.txt` schliesst `*.h5` ausdruecklich aus
   ("jederzeit nachbaubar"). **MONOLITHEN ebenfalls ERLEDIGT** (2026-09-14, nach dem Ende von b02/b03):
   acht aus der v28-Generation geloescht (4,1 GB), vier aktuelle geschuetzt. Cache-Volumen von
   5,1 auf 2,3 GB; zusammen mit den Bloecken rund 4,9 GB frei. **Schritt 4 des
   Generationswechsels ist damit vollstaendig.**
4. **Kette v29 fahren**: `tools/night_v29_chain.sh` ist GESCHRIEBEN (2026-09-13, Syntax
   geprueft) und wartet selbst auf das Ende der Erzeugung -- Manifeste, G-2-Kennzahlen, Fenster
   (Seed 20260941), Bloecke, Monolith, Training v29-b01 mit Warmstart auf `v28-b02_brierbest`.
   Sie enthaelt Tor 0 und Tor 2a bereits als Schritt 1, Punkt 1 oben ist damit abgedeckt.
   **Starten wie die Erzeugung: in einem eigenen Fenster, nicht ueber die Sitzung.**
5. **Portable Build -- als TEST, nicht als Auslieferung** (Nutzer 2026-09-13, 22:00: "Der
   portable build ist fuer mich erst relevant mit v30. Wir koennen ihn von mir aus mit v29
   testen"). Er belegt also nur, dass der Bauweg traegt; das Ergebnis wird nicht weitergegeben.
   `python tools/build_release.py` nach
   `evaluations/review/portable_build_audit_2026-09-13.md` Abschnitt C, Spec ist auf v28-b02
   umgestellt (Commit 3c81d0b). **Nur bei freier CPU** -- nicht neben Erzeugung oder Kette.
   Das RELEASE selbst gehoert zu v30 (Schlussmodell Tessa).
6. **Zwei Bauten, die VOR ihrem jeweiligen Trainingsarm stehen** (Fahrplan Nr. 5 und Nr. 15),
   beide brauchen eine freie Maschine und ihre Tore:
   - **Wheel 2 fuer den Sicht-Arm v29-b03**: Encoder-Abschnitt 16 mit P.3, P.7, P.9 und
     P.11 bis P.15. **Der CODE ist gebaut** (2026-09-13, `PREREG_stack_top_feature.md`
     par.17/17a): Rust beide Pfade, Python-Zwilling, drei Tests, plus das additive Record-Feld
     `dome_pool_view.blocks[].designs` in `serialize.rs`. **Bau, Tests und Fixtures sind
     ABGENOMMEN** (2026-09-13: 641 Tests gruen, keine Warnungen; Vertragshash jetzt
     `39994362fba145a6`, Netz-Paritaet `3c02ed8c7c55c603`, Feature-Golden-Fixture neu
     basisgelegt). OFFEN sind nur noch **Wheel-Bau plus Installation und die Anker-Drift** --
     sie brauchen ein Fenster ohne Erzeugung.
     **`config.INPUT_SIZE` steht bewusst noch auf 755** und wird im SELBEN Zug wie die
     Wheel-Installation auf 794 gesetzt: `file_cache_key.py` liest den Wert zur Laufzeit,
     eine vorzeitige 794 haette die wartende Kette 755er-Bloecke unter dem 794er-Schluessel
     ablegen lassen (Unfall vom 2026-09-11). Merkposten steht an der Zeile in `config.py`.
     **P.12 wirkt erst ab v30** (Nutzer-Entscheid 2026-09-13, par.17): der laufende
     v29-Korpus traegt `designs` nicht, die 18 Spalten sind in b03 konstant 0.
   - **Ablations-Schalter `MOSAIC_SPECIAL_PLANES_OFF` fuer v29-b02** plus Tore
     (`PREREG_special_tile_yield.md`, Fahrplan Nr. 15).
7. Danach nach Fahrplan `evaluations/v29_program_agent_plan.md` (41 Punkte).

### Architektur Mondstapel und Rueckgabestapel konkretisiert (2026-09-15, Nutzer-Auftrag)

Registriert als `PREREG_moon_stack_order.md` par.12 und `PREREG_dome_return_order.md` par.12,
im Fahrplan als 29b, 32b (neu gefasst) und 32c. Kein Bau, kein Entscheid.

**Befund mit Gewicht (am Code geprueft): das Trainingsziel des `moon`-Kopfs ist ein No-Op.**
`moon_order_target` (`self_play.rs:1331-1386`) bewertet die Permutationen mit
`solve_round_final_score`, das nur `players[pi]` liest (`tiling_solver.rs:396-404`; der
Modulkopf `:249` nennt `state.factories` als absichtlich ignoriert); das erste Element von
`permutations` ist die Identitaet, also gewinnt IMMER die kanonische Sonnenseiten-Reihenfolge.
Der Kopf trainiert mit Gewicht 1,0 (alle v28/v29-Manifeste) darauf, die kanonische Folge zu
reproduzieren. Bekannt seit 2026-08-20 (`PREREG_implementation_review_unprimed.md` Befund 2),
damals als Rezept-Entscheid an den Nutzer verwiesen und nie entschieden; par.2 der Mond-Prereg
beschrieb das Ziel bis heute als funktionierend. Folgen: der Fan-out-Prior (Stufe 1) bevorzugt
das kanonische Kind, der Stufe-1-Nullbefund ist damit erwartbar (Herleitung, nicht gemessen);
Stufe 3 haengt nicht am Prior. Nutzer 2026-09-15: "eher schlecht wenn er auf die kanonische
reihenfolge trainiert."

**Vorschlaege, nach Kosten:** (1) zwei Sonden ohne Bau am Spiel: Zugriffs-Bilanz aus den Logs
(wer nimmt den oben gelegten Stein) und Anteil nicht-kanonischer gespielter Reihenfolgen im
v29-Fenster; (2) Arm `v29-b04` mit repariertem Ziel (gespielte Reihenfolge als Label, im Record
vorhanden, kein neuer Korpus) -- **ENTSCHIEDEN 2026-09-15 zusammen mit der Ablation `v29-b05`
(`--moon-loss-weight 0`), Fahrplan 32b**; (3) fuer die Rueckgabe zuerst die Sensitivitaets-Sonde am
v29-b03, dann Streu-Korpus mit v30, dann A/B -- **R1 GEMESSEN 2026-09-15** (`dome_return_order`
12.4, andere Sitzung): der Value-Kopf reagiert auf die Typfolge (Median-Spannweite 0,019,
81 Prozent ueber 0,01, n = 300), das Henne-Ei der SICHT ist widerlegt; **Arena gezaehlt (12.5):**
nur 0,6 Rueckgaben mit Rest je Partie und Seite, Modus 1 weicht in 42 Prozent davon ab, erwartete
Wirkung rund 0,005 Siegwahrscheinlichkeit je Partie -- der par.9-Nullbefund ist Arithmetik, das
A/B taugt fuer diesen Knopf nicht als Entscheidungsinstrument. **ENTSCHIEDEN daraufhin (Nutzer):
R2 wird gebaut, Modus 1 in der v30-Erzeugung AN** (par.12.6, Abschnitt 6 Punkt 10); (4) eigene Entscheidungsknoten im Baum fuer beides
nur gebuendelt und nur nach einem Nutzer-Entscheid, den v30-Rahmen zu oeffnen (NUM_ACTIONS
406 -> 414, jeder Checkpoint verwaist). Entscheide in Abschnitt 6, Punkte 9 und 10.

### Stand 2026-09-14, 14:00 -- die v29-Arme sind gemessen

**Die Erzeugung ist durch** (1.201 Dateien, 12,8 h), **Tor 2a haelt** (0,843 gegen 0,816 volle
Spalten je Seite; die Reihe ist ueber fuenf Generationen monoton), das Fenster steht mit 2.947
Dateien, und alle drei Arme sind trainiert.

| Arm | Eingang | Besonderheit | Tor 1 | Ergebnis |
| --- | --- | --- | --- | --- |
| v29-b01 | 755 | Pflichtarm, Bezugspunkt | gegen `v28-b02` | **beide Seeds H0** -- kein Champion-Wechsel |
| v29-b03 | 794 | Sichtwerte (Abschnitt 16) | gegen b01 | **Merkmalsstand UEBERNOMMEN** (Seed 1 klar 69:41, Seed 2 Gleichstand; par.12-Regel) |
| v29-b02 | 794 | plus Spezialfeld-Ablation | gegen b03 | **praezisiert 2026-09-15** (par.10a): die Kanaele wirken auf ihren POSTEN (+0,13 bis +0,22 belegte Spezialfelder in drei Seeds), aber NICHT auf die Siegquote -- der Nachzug mit 150 Paaren ohne Frueh-Stopp steht 147:153, p 0,82 |

**Champion bleibt `v28-b02_brierbest`.** Die fehlende Kante ist am 2026-09-14 gemessen worden
(Nutzer: "ich hab noch keinen champion kandidaten aus v29 gesehen"), **Ergebnis 1:1**:

| Seed | b03 : Champion | SPRT | McNemar p | Punkte b03 / Champion |
| --- | --- | --- | --- | --- |
| 20261067 | **124 : 86** | **b03 signifikant besser** | 0,0163 | 53,38 / 50,03 |
| 20261068 | 87 : 93 | H0 (Gleichstand, nicht Niederlage) | 0,7754 | 53,61 / 53,63 |
| 20261069 | **64 : 36** | **b03 signifikant besser** | 0,0125 | 57,48 / 52,10 |

**v29-b03 IST EIN CHAMPION-KANDIDAT** (drei Seeds, alle auf demselben Wheel): zwei signifikant
dafuer, einer Gleichstand, **kein Seed dagegen**. Zusammen 275:215 in 490 Partien. In beiden
Siegseeds auch das Punkteniveau klar hoeher (+3,35 / +5,38 je Partie), im neutralen Seed gleich.

**PROMOTION ANS ENDE DER GENERATIONSARBEIT VERSCHOBEN** (Nutzer 2026-09-14: "champion werd ich
erst zum schluss der generationsarbeit machen. vielleicht kommt noch was besseres"). Der Champion
bleibt bis dahin `v28-b02_brierbest`; die drei Elo-Kanten von b03 SIND eingetragen (Register und
Champion-Rolle sind zweierlei). Grund: die offenen Knopf-Familien (Nr. 28, 30-32, 33-36) koennen
einen besseren Generator hervorbringen, und eine Promotion jetzt wuerde darauf einrasten.
**Folge fuer die Planung:** die naechste Erzeugung (und damit P.12 und die Rueckgabe-Streuung im
Korpus) kommt erst NACH dem Begleitprogramm -- kein Zeitdruck bei den Knopf-Messungen. Einzelheiten `PREREG_v29_window.md` par.9.

**MESSFEHLER GEFUNDEN 2026-09-14: b03 hat auf ablatierten Validierungsdaten validiert.**
Derselbe Schluessel-Defekt, der b02s Monolithen kostete, traf auch den Val-Cache -- und den baut
`train.py` selbst, nicht das Ketten-Skript. Gemessen an den Planes-Kanaelen: in b02s Val-Cache
(der einzige 794er, den es gibt) liegen die Kanaele 77/78 auf exakt 0,0000, waehrend b03 MIT
diesen Kanaelen trainiert hat. **Die Arena-Verdikte sind nicht betroffen** (sie messen Partien),
b01 und b02 sind sauber. Zwei Aussagen von hier sind damit zurueckgenommen -- Einzelheiten in
`PREREG_v29_window.md`, Nachtrag zur Monolith-Kollision:

1. ~~b03 hatte den schlechtesten Offline-Wert der drei Arme~~ -- **NACHGEMESSEN 2026-09-14 auf
   einem sauberen Val-Cache: 0,1796741 gegen 0,1793375 bei b01.** Der Abstand schrumpft von
   0,0018 auf 0,00034, also auf die halbe Spannweite von b03s eigenen zwoelf Epochen. **b03 ist
   offline nicht schlechter**, und damit gibt es auch keinen "Widerspruch zur Offline-Metrik"
   mehr -- b03 gewinnt die Arena und liegt offline gleichauf.
2. ~~b03 erreicht sein Optimum in Epoche 2 von 12~~ -- die zwoelf Brier-Werte liegen zwischen
   0,18114 und 0,18178, Spannweite 0,00064. Das ist eine flache Reihe ohne aufloesbare Struktur;
   Epoche 2 ist ihr zufaelliger Tiefpunkt, nicht ein Sattelpunkt. Die Nachfrage war trotzdem
   richtig -- par.6d Punkt 1 GEMESSEN (2026-09-14): **17 der 39 neuen Spalten leben, 22 sind exakt 0
   -- und beide Gruppen sind die vorhergesagten** (18x P.12, dessen Korpusfeld fehlt, plus vier
   Phasen, die im Korpus nicht vorkommen). Die lebenden Spalten sind aber schwach (0,137 im Mittel
   gegen 3,009 bei den Altspalten). Die frueher hier stehende Folgerung, das erklaere das fruehe
   Optimum, faellt mit dem Optimum weg. Punkt 2 GRUEN: tote Einheiten bei allen vier Modellen
   2,60 Prozent, kein Zuwachs.

**Monolith-Kollision BEHOBEN** (2026-09-14): der Fenster-Cache-Schluessel kannte den
Ablations-Schalter nicht, b03 hat b02s Monolithen ueberschrieben (Ergebnisse unbeschaedigt, die
naechste Wiederholung waere still falsch gewesen). Fix an der Wurzel in `window_cache_key`, aber
nur bei EINGESCHALTETEM Schalter angehaengt: der Default-Schluessel ist gemessen identisch zum
Stand davor, kein Bestandscache entwertet; drei Tests im pre-commit-Hook. Der frueher vorgelegte
Nutzer-Entscheid Weg 1 gegen Weg 2 ist damit gegenstandslos -- der Einwand gegen Weg 1
("entwertet Bestand") traf auf diese Bauform nicht zu.

**Offen aus dem Betrieb:** die Schwierigkeitsleiter ist auf v30 vertagt.

**Begleitprogramm Nr. 25 DURCH (2026-09-14): kein Knopf aus dem Zugklassen-Differential.**
`tools/probes/move_class_differential.py`, 1.343 s, n = 293 Claude-Entscheide aus g01-g07.
Roh sah die Kuppelplatzierung wie der Treffer aus (53 von 53 Abweichungen, hoechste
Wurzelwert-Differenz), **normiert traegt sie nicht**: bei Median 73 legalen Kuppelzuegen weicht
auch blindes Waehlen in 96,1 Prozent der Faelle ab. Bei Steinzuegen trifft Claude den Netzzug
dagegen klar haeufiger als blind (0,708 gegen 0,903, 5,4 SE). Die Ausgangs-Spalte ist bei sieben
Partien strukturell blind, weil der Ausgang je Partie konstant ist. Einzelheiten
`PREREG_claude_play_interface.md` par.12.

**Was daraus als Frage bleibt (nicht gebaut, nicht entschieden):** die Suche rangt bei @400 nur
16 Wurzelkandidaten (`net_mcts.rs:3180-3186`) -- bei der Kuppelplatzierung also rund 22 Prozent
der Optionen, bei Steinzuegen 84 Prozent. Ob die Wurzelbreite fuer die Kuppelphase eigens
steigen sollte, ist ein Rezept-Entscheid mit Kostentor, kein Befund dieser Sonde.

### Stand der Nacht 2026-09-13/14 (Sitzung, waehrend der Erzeugung)

Vier Fahrplanpunkte sind bearbeitet worden, alle ohne Messung:

| Nr. | Punkt | Stand |
| --- | --- | --- |
| 5 | Encoder-Abschnitt 16 (Sicht-Arm v29-b03) | **Code und Tore durch**: 39 Werte, INPUT_SIZE 794, drei neue Tests, Suite 641 gruen, drei Fixtures neu gesetzt. OFFEN: Wheel-Bau plus `config.INPUT_SIZE` auf 794 im selben Zug, dann Anker-Drift |
| 15 | Ablations-Schalter `MOSAIC_SPECIAL_PLANES_OFF` | **Bau geprueft und vollstaendig** (beide Encoder, Cache-Schluessel, Registratur, `engine_config`, `knobs.md`). OFFEN: die Tore -- sie teilen sich den Wheel-Bau mit Nr. 5, weil der Schalter per Default AUS ist |
| 20 | Netz-Gesundheit | **Sonde `tools/probes/dead_unit_probe.py` gebaut**, Selbsttest ueber drei Generationen gruen. Lauf DURCH am 2026-09-14, Punkte 1 und 2 oben |
| 23 | Korpus-Verhaltens-Audit | **Werkzeug gebaut, Selbsttest gruen** (18 Handzahlen ueber sechs Claude-Partien exakt). Der Korpuslauf kommt mit v29 |
| 22 | Schwierigkeitsleiter | Bauplan in drei Punkten berichtigt, **Schritt 1b gebaut UND ABGENOMMEN** (2026-09-14 01:35, neben dem b01-Training): sechs optionale Stilfelder, 641 Tests gruen, Paritaets-Fixture unveraendert -- das vorregistrierte Tor. Nichts installiert. Auch `models/levels/beginner.spec.json` liegt (hv3 @150) |

**RUST-STAND 2026-09-15, 05:40: Tests GRUEN, Wheel NICHT gebaut** (UEBERHOLT am Vormittag:
Diagnose-Serie par.9i um 08:08 lief auf einem neuen Wheel, das Wheel mit C3 folgte um 08:40,
Commit a4f92a5; Stand in Abschnitt 1 oben). Zwei Stuecke sind
diese Nacht dazugekommen:

* der umgebaute **Streu-Knopf der Rueckgabe** (Schwelle 3, Rundenfenster 1-4, Commit `df4b424`),
* die **Diagnose-Zeile der Mondstapel-Nachsuche** (`[moon_order] applied=N changed=M`,
  `PREREG_moon_stack_order.md` par.9g, Commit `50772fb`).

**Abgenommen ist die Testhaelfte:** `cargo test --release` mit **663 Tests gruen, 0 Fehler,
0 Warnungen**, `examples/` und `benches/` kompilieren mit (die pre-push-Falle greift also
nicht), der neue Waechter `moon_order_diagnostics_reset_on_read` laeuft durch. Dabei fielen
zwei eigene Fehler auf und wurden behoben: der Zaehler-Block stand zwischen dem
Doc-Kommentar von `moon_order_post_search` und der Funktion (Dokumentation verwaist), und ein
`///` ueber einem `thread_local!`-Makro erzeugte eine Warnung.

~~OFFEN und dem Nutzer vorgelegt: Wheel-Bau plus Installation, danach Anker-Drift~~ **ERLEDIGT 2026-09-15 vormittags** (siehe Abschnitt 1; Drift-Artefakt fuer das 08:40-Wheel noch nicht abgelegt)
(`/mosaic-anchor-invariance`, Pflicht nach jeder Engine-Aenderung). Der Austausch der
installierten Engine ist der einzige Schritt mit Rueckfallrisiko und wurde deshalb nicht
unbeaufsichtigt gefahren. Erst danach ist die Diagnose-Serie mit `moon_order_variants=2`
moeglich, die die Zahl `changed` liefert -- und an ihr haengt, ob Fahrplan 32a gebaut wird.

Der Satz, der hier stand (2026-09-14 01:35: auch Schritt 1b ist kompiliert und abgenommen,
641 Tests gruen). Das gefaehrdet die laufende Nacht nicht: weder `tools/night_v29_chain.sh` noch
`tools/night_v29_tor1_b01.sh` bauen ein Wheel (geprueft: kein maturin, kein pip install, kein
cargo darin) -- beide fahren auf dem INSTALLIERTEN Wheel, und `config.INPUT_SIZE` steht bewusst
noch auf 755. Der erste Bau gehoert an eine freie Maschine und bringt beides zugleich: Wheel fuer
Abschnitt 16 (Nr. 5) plus die Tore von Nr. 15, und danach den ersten Kompilierlauf fuer
Schritt 1b.

**Zwei Entscheide des Nutzers sind eingearbeitet:** P.12 wirkt erst ab v30 (der v29-Korpus traegt
das neue Record-Feld nicht, `PREREG_stack_top_feature.md` par.17), und die P.11-Normierung ist von
der unbelegten 4 auf die Regel-Obergrenze 10 korrigiert (`board.rs` Z.240).

**FENSTER-PINNING nicht vergessen:** Streudateien, die waehrend der Erzeugung entstehen,
gehoeren beim Fensterbau in `MOSAIC_DATA_EXCLUDE`.

### NACHT 2026-09-14/15: die Messkette und ihre sechs Verdikte

Zwei Ketten nacheinander, rund acht Stunden, alles auf dem Kontrakt `39994362fba145a6`.
**Ergebnis in einer Tabelle, Herleitungen darunter:**

| Gegenstand | Ergebnis | Folge |
| --- | --- | --- |
| Mondstapel Stufe 3 (Nachsuche) | traegt NICHT: 197:203, p 0,84, 200 Paare ohne Stopp | Verdacht in 4 von 5 Punkten ausgeraeumt; offen nur das Budget |
| Kostentor K4 | **BESTANDEN**: +4,3 Prozent gegen Schwelle 25 | Fahrplan Nr. 30 gruen |
| Arena K4, Dosis 1,0 | **SCHADET**: 20:60, p 0,0002, -14,3 Punkte, -0,95 Spalten | Prereg ENTSCHIEDEN |
| Arena K4, Dosis 0,5 | **SCHADET**: 45:85, p 0,0005, -8,3 Punkte | Fahrplan 31/32 gegenstandslos |
| Spezialfeld-Nachzug b02/b03 | Posten JA (+0,131 Felder), Siegquote NEIN: 147:153, p 0,82 | Begruendung korrigiert, Merkmal bleibt |
| Anker-Kante v29-b03 | **128:22** (85,3 Prozent), 150 Partien ohne Stopp | zweite Aufhaengung steht; Eintrag faellig |
| Value-Anteil im Tiling, 2 Dosen | traegt NICHT: 80:80 und 81:79, p 1,000 | par.8.6 GESCHLOSSEN |

**Zwei Befunde zaehlen ueber ihre eigene Messung hinaus:**

1. **Ein Rundenscore-Term macht die Suche kurzsichtig.** K4 senkt die Strafleiste (-1,57) und
   hebt volle Zeilen, waehrend Spalten (-0,84) und Spezialfelder (-0,59) einbrechen. Das ist
   die empirische Gegenprobe zur Nutzer-Frage vom 2026-09-14 ("nein er optimiert nicht nur
   runden score hoff ich mal") -- er tut es, sobald er genug Gewicht bekommt. Und es ist ein
   Argument FUER Variante B (Fahrplan 33): der Punkte-Weg ist abgeraeumt, der Geometrie-Weg
   nicht.
2. **Zwei Belege dieser Kampagne standen auf zu kleinen Stichproben.** Der Spezialfeld-Beleg
   (p = 0,0386 aus 30 Paaren mit Frueh-Stopp) loest sich bei 150 Paaren auf; K4s Dosiswahl
   stand auf einer Analogie, die eine fehlende Daempfung uebersah. Beide Male hat erst die
   groessere Stichprobe geklaert.

**Offene Nutzer-Entscheide aus dieser Nacht:** (a) ~~K4 ein Rundenprofil geben oder den Term
ruhen lassen~~ **ENTSCHIEDEN 2026-09-15: der Term RUHT** (`round_estimate_leaf_term` par.7e), (b) den kontaminierten Kostentor-Lauf wiederholen (8,5 min, das Verdikt braucht
es nicht), (c) nach dem Wheel-Bau: wird Fahrplan 32a ueberhaupt gebaut (haengt an der
Diagnose-Zahl `changed`).

#### Stufe 3 des Mondstapels traegt nicht

**197:203 auf 200 Paaren ohne Frueh-Stopp** (McNemar p 0,84, gepaarte Differenz -0,030
[-0,229, +0,169], 5.933 s bei 10 Threads, 14,833 s je Partie). Keine der sechs
Standard-Kennzahlen liegt ueber der Aufloesung. Artefakt
`moon_order_post_vs_off_s20261091.json`, Einzelheiten `PREREG_moon_stack_order.md` par.9h.

**Das Verdikt lautet nicht "die Reihenfolge ist egal"** -- die Gegenhypothese ist seit par.7
widerlegt (nur der oberste Stein je Stapel ist ziehbar) --, sondern: **die Nachsuche in dieser
Bauform und mit diesem Budget traegt nicht.** par.9d hatte vorab festgelegt, dass ein
Nullbefund hier ein Implementierungs-Verdacht ist; **vier der fuenf Pruefpunkte sind
ausgeraeumt** (Perspektive, Verdrahtung bis in den Arena-Pfad, Vollstaendigkeit der Varianten,
und die Ausloesung per Deckungsgleichheit: das Tor prueft exakt die Bedingung, die par.9b mit
12,20 je Partie gezaehlt wird -- par.9i, im Code; die frueheren 24,34 aus den Logs waren eine Ueberzaehlung, weil die Log-Zeile ein ZUSTAND ist und kein Ereignis). Offen bleibt allein das **Budget** (256 Sims je Variante =
Wurzelbreite 16).

**Die eigentlich offene Frage hat par.9d gar nicht gestellt:** nicht wie oft die Nachsuche
laeuft, sondern **wie oft sie ANDERS waehlt**. Dafuer ist die Diagnose-Zeile `[moon_order]`
gebaut (par.9g), sie liegt noch nicht im Wheel.

**Randbefund als Reihenfolge-Argument, nicht als Beleg:** die groesste Einzelabweichung sind
die vollen Spalten mit -0,0985 (rund 1,8 SE), also die langfristigste Groesse im Block,
waehrend die kurzfristigen Plattenpunkte leicht fuer die Nachsuche sprechen. Dieselbe Richtung,
die par.9e dem Prior vorwirft. Das stuetzt die Reihenfolge C vor B vor A (Fahrplan 32a/32b).

**Faellig vor Fahrplan 32a:** Wheel bauen, kleine Serie mit `moon_order_variants=2`, die beiden
Zahlen ablesen. Bleibt `changed` nahe 0, waehlt die Nachsuche fast immer den Bestand -- dann
ist nicht der Horizont der Engpass und 32a faellt, bevor es gebaut wird.

#### Kostentor K4 bestanden, Fahrplan Nr. 30 gruen

**+4,3 Prozent Wanduhr** (12,812 gegen 12,286 s je Partie) und +3,4 Prozent CPU gegen eine
Schwelle von 25 Prozent -- der Rundenschaetzer kostet ein Sechstel des Erlaubten. Artefakte
`k4_kosten_mit_s20261092.json` / `k4_kosten_ohne_s20261093.json`, Einzelheiten
`PREREG_round_estimate_leaf_term.md` par.7b. Die Schritte 31 und 32 duerfen laufen.

**OFFENGELEGT (par.7a): waehrend des `mit`-Laufs lief Nebenlast aus dieser Sitzung** -- drei
git-Commits, deren pre-commit-Hook je 98 Tests faehrt, in einem Lauf, dessen einzige Messgroesse
die Wanduhr ist. Groessenordnung 0,18 bis 0,59 Prozent des Kern-Fensters bei 43,7 Prozent
Auslastung. **Die Stoerung wirkt konservativ** (sie verteuerte die mit-Seite), +4,3 Prozent ist
also eine Obergrenze und das Verdikt haelt. Eine saubere Wiederholung kostet 8,5 min und ist
ein Nutzer-Entscheid. **Regel ab sofort in dieser Sitzung: kein Commit, solange eine Messkette
laeuft.**

**Nebenbefund, NICHT gedeutet:** zwischen den beiden Kostentor-Laeufen unterscheiden sich
Punkte (46,33 gegen 51,27) und volle Spalten (0,55 gegen 0,93) deutlich. Verschiedene Seeds bei
n = 40 -- in dieser Kampagne bewegt der Seed die Metrik 4- bis 6-mal staerker als jeder Knopf.
Die gepaarten Arena-Laeufe der Schritte 4 und 5 entscheiden das.

**Und die offene Frage aus par.9h ist beantwortet:** `k4_kosten_ohne` liefert den fehlenden
Basiswert ohne Nachsuche. Der Stufe-3-Lauf liegt mit 14,833 s je Partie **+20,7 Prozent**
darueber, obwohl nur eine der beiden Seiten die Nachsuche traegt (hochgerechnet rund +41
Prozent beidseitig, Herleitung). **Die Nachsuche hat also wirklich gerechnet** -- ihre
Wirkungslosigkeit liegt nicht daran, dass sie nie lief.

#### K4 mit voller Dosis SCHADET -- und die Ursache ist gefunden

**20:60 Siege, McNemar p = 0,00018, -14,3 Punkte und -0,95 volle Spalten je Partie**
(`k4_c10_vs_off_s20261094`, 40 Paare, gepaart, ein Spec-Feld Unterschied). Kein Nullbefund,
sondern ein Einbruch. Einzelheiten `PREREG_round_estimate_leaf_term.md` par.7c.

**Der Nebenbefund aus par.7b war damit echt und kein Seed-Effekt** -- die Vorsicht beim Lesen
war richtig, die Beobachtung auch.

**Ursache am Code belegt, und sie ist eine Dosis-Frage:** `today_value` ist eine
Siegwahrscheinlichkeit in [0,1] (Klammerung net_mcts.rs:3205-3206), der Term addiert
`C_est * tanh(..)`, bei C_est 1,0 also bis zu +-1,0 -- er kann den Value-Kopf ganz ersetzen.
Und `B` ist per Konstruktion das P90 der Differenz je Runde, also saettigt der tanh in rund
10 Prozent der Blaetter, **in jeder Runde gleich oft**. Die Dosis war mit "Betrag wie K3"
begruendet; die Analogie stimmt strukturell (gleiche Stelle, gleicher Wertebereich, K3 faehrt
c = 1,0 ohne Schaden), uebersieht aber die zweite Daempfung, die nur K3 hat: sein Shift traegt
das abfallende Rundenprofil in sich. **K4 hat keines.**

**Dosis 0,5 bestaetigt es** (par.7d): 45:85, p = 0,00054, -8,26 Punkte. Der PUNKTE-Schaden
halbiert sich grob mit der Dosis (Faktor 0,58), **der SPALTEN-Schaden nicht: davon bleiben 88
Prozent** (-0,837 gegen -0,949). Die Stoerung des Spaltenbaus saettigt also tief.

**Der Mechanismus ist damit sichtbar, und es ist der befuerchtete:** bei Dosis 0,5 sinkt die
Strafleiste um 1,57 Punkte und volle Zeilen steigen (+0,11), waehrend Spalten (-0,84) und
Spezialfelder (-0,59) einbrechen. `round_estimate_points` ist Solver-Rundenscore plus
Strafleisten-Busse -- der Term liefert genau, worauf er zeigt, und verliert alles, was ueber die
Runde hinausreicht. Das ist die empirische Gegenprobe zur Nutzer-Frage vom 2026-09-14 ("nein er
optimiert nicht nur runden score hoff ich mal"): er tut es, sobald er genug Gewicht bekommt.

**Fahrplan Nr. 31 und 32 sind damit gegenstandslos** (im Plan durchgestrichen und begruendet).
~~Offen als VORSCHLAG, Nutzer-Entscheid: K4 ein abfallendes Rundenprofil wie K3 geben (rund
1 h Bau).~~ **ENTSCHIEDEN 2026-09-15: RUHT** (par.7e, Nutzer: "lassen wir ruhen"). Das ist der naeherliegende Weg als eine kleinere Dosis -- wenn der Spaltenschaden bei
halber Dosis zu 88 Prozent bleibt, ist er bei einem Zehntel nicht automatisch weg.

**Und eine Luecke in der Prereg:** ihr Falsifikator kennt nur "traegt" und "traegt nicht". Ein
SCHADEN ist ein dritter Ausgang, den par.5 und par.10 nicht vorgesehen haben.

#### der Spezialfeld-Nachzug korrigiert seine eigene Begruendung

Der Lauf, den ich als duennste Kante der Generation angesetzt hatte, hat geliefert -- gegen das
bestehende Verdikt. `paired_gating_v29-b02_vs_v29-b03_s20261096.json`, **150 Paare ohne
Frueh-Stopp: 147:153**, McNemar p = 0,822, gepaarte Differenz -0,040 [-0,273, +0,193].

**Die Effektstaerke derselben Kante faellt monoton mit der Stichprobe:** -0,533 (30 Paare,
Frueh-Stopp, p = 0,0386) -> -0,280 (50 Paare) -> **-0,040 (150 Paare)**. Der einzige
signifikante Lauf war zugleich der kleinste und der einzige mit SPRT-Stopp. **Auf der
Siegquote traegt das Verdikt nicht.**

**Der Posten dagegen bewegt sich, und zwar konsistent:** belegte Spezialfelder +0,170 / +0,224 /
**+0,131** in den drei Seeds -- der groesste Lauf (n = 298 Bretter je Seite) liegt mitten im Feld
statt einzubrechen. Dazu +0,087 volle Spalten und +0,58 Punkte je Partie fuer b03.

**Kein Widerspruch, sondern Groessenordnung:** +0,58 Punkte gegen eine Punkte-SD von rund 17
loesen 150 Paare nicht auf. **Folge fuer die Entscheidung: keine** -- die Kanaele bleiben drin
(gebaut, kostenlos, wirken auf ihren Posten, schaden nicht). Was faellt, ist die Begruendung
"die Ablation verliert signifikant". Einzelheiten `PREREG_special_tile_yield.md` par.10a.

**Die Lehre darueber hinaus:** ein Verdikt auf 30 Paaren mit Frueh-Stopp haette hier fast einen
Merkmalssatz mit einer Zahl gerechtfertigt, die sich bei 5-facher Stichprobe aufloest. Der
Nachzug kostete 65 min.

#### Anker-Kante fuer v29-b03: 128:22, eingetragen

`anchor_edge_v29-b03_vs_hv4_anchor.json`: **128:22 in 150 Partien** (85,3 Prozent), kein
Frueh-Stopp, 1.292,8 s / 8,62 s je Partie. Aufbau wie bei der letzten Anker-Kante des
Champions: b03 @400 c_puct 1,5 mit Champion-Spec gegen das Anker-Artefakt @150 c_puct 0,3,
6 Worker. Handshake bewusst Cross-Aera (Artefakt 39648b95bbba1acf gegen Live
39994362fba145a6, `project_anchor_era_rule`), **Golden-Selbsttest ohne Abweichung**.

**Einordnung:** die bisherige Vergleichskante `v22-b05@400 gegen hv4@150` steht bei 76 Prozent
(38:12), und die war mit Frueh-Stopp, also nach oben verzerrt. b03 liegt mit 85,3 Prozent ueber
150 Partien ohne Stopp deutlich darueber. Damit haengt v29-b03 erstmals an zwei VERSCHIEDENEN
Gegnern statt nur am Champion -- die Promotions-Checkliste verlangt drei Aufhaengungen
(Gating, Anker, Champion-2).

**EINGETRAGEN 2026-09-15, 05:1x** (nach dem Ende der Ketten). Der Befehl war:

```
python tools/elo_tracker.py add --player-a v29-b03 --sims-a 400   --player-b Heuristik_hv4_anchor --sims-b 150   --wins-a 128 --wins-b 22 --n 150   --comment "Segment 2: v29-b03 @400 c_puct 1,5 (Champion-Spec) gegen Anker-Artefakt hv4_anchor @150 c_puct 0,3, frozen_referee_match 6 Worker, Seed-Basis 20261097, 150 Partien OHNE Frueh-Stopp (85,3 Prozent), Golden-Selbsttest gruen, Cross-Aera (Artefakt 39648b95bbba1acf gegen Live 39994362fba145a6); 1.293 s"
```

(Parameternamen am Werkzeug geprueft: `--player-a`/`--player-b` und `--n`.)

**Ergebnis im Register: `v29-b03@400` steht bei Elo 1402 [1353, 1456] aus 640 Partien** und
damit ERSTMALS ueber dem amtierenden Champion `v28-b02@400` (1371 [1332, 1419], 2.350 Partien).

**Zwei Einschraenkungen gehoeren zu dieser Zahl:**

1. **Die Intervalle ueberlappen deutlich** (1353-1456 gegen 1332-1419). Der Abstand von 31 Elo
   ist kein Staerkebefund.
2. **Drei von b03s vier Kanten sind frueh gestoppt** (Spalte "Frueh 3/4" im Register), ihre
   Siegquoten also nach oben verzerrt und nicht korrigiert. Die Anker-Kante von heute Nacht
   ist **die erste unverzerrte** -- 150 Partien bis zum Deckel. Der Champion hat 6 von 13
   gestoppten Kanten bei vierfacher Partienzahl.

Der Champion bleibt `v28-b02_brierbest`; die Promotion steht per Nutzer-Entscheid am Ende der
Generationsarbeit.

Kommentar mit Cross-Aera-Vermerk und Golden-Selbsttest. Die naive Ein-Kanten-Rechnung ergaebe
rund +306 Elo ueber dem auf 1000 fixierten Anker; der Registerwert kommt aus dem
Block-Bootstrap ueber alle Kanten und kann davon abweichen.

#### Value-Anteil im Tiling: zweiter Nullbefund, par.8.6 geschlossen

Der Lauf, der auf meiner Falschauskunft "ungemessen" beruhte und den der Nutzer nach der
Richtigstellung bestaetigt hat ("bleiben drin. die maschine braucht eh was zum laufen"):
**80:80 bei Dosis 0,5 und 81:79 bei Dosis 1,0**, McNemar p = 1,000 in beiden, je 80 Paare bis
zum Deckel. Keine der sechs Kennzahlen ueber der Aufloesung, und die vollen Spalten haben in
den beiden Dosen ENTGEGENGESETZTE Vorzeichen (+0,050 und -0,063) -- Rauschen, keine mit der
Dosis wachsende Wirkung. Einzelheiten `PREREG_geometric_envelope.md` par.8.6b/8.6c.

**Damit ist der Term geschlossen**, an zwei Netzen und zwei Basislinien gemessen (2026-09-04 am
v23-b01 gegen die damalige Spec, 2026-09-15 am v28-b02 gegen die Champion-Spec).

**Die Kosten belegen die alte Begruendung:** der Term ruft je Tiling-Kandidat das Netz, kostet
aber nur +2,1 und +3,6 Prozent Wanduhr, und die Seiten spielen fast identisch (5-6 Sweeps gegen
rund 70 Splits). Im Tiling gibt es kaum Kandidaten mit echter Wahl -- der Entscheid liegt im
Draft, wie par.8.6a 2026-09-04 schon sagte.

**Nicht verwechseln mit dem offenen Vorschlag bei K4:** dort FEHLT ein Rundenprofil und der Term
wirkt zu stark; hier ist der Term zu schwach, um ueberhaupt messbar zu sein.

### Stand 2026-09-15, 13:30: der `moon`-Kopf kostet Staerke -- b05 ist besser als b03

**Kette 32b/32c/29b an einem Tag durch.** Vier Messungen, drei davon gegen die Vorab-Erwartung:

| Schritt | Ergebnis |
| --- | --- |
| **par.12.0** Trainingsziel des `moon`-Kopfs | **No-Op**, am Code belegt: das Label ist immer die kanonische Reihenfolge |
| **32c** Zugriffs-Bilanz (n = 9.372) | enge Frage beantwortet (14,8 Prozent im naechsten Halbzug); **Folgerung 'Hebel klein' am 2026-09-16 ZURUECKGENOMMEN** -- ein Mondzug nimmt ALLE Oberseiten einer Farbe, 43,8 Prozent der Zuege raeumen mehrere Steine ab (par.12.3a) |
| **Korpus-Sonde b04** | Tor OFFEN: **44,1 Prozent** nicht-kanonisch gespielt (Tor war 10) |
| **R1** (29b, Sensitivitaet) | Erwartung WIDERLEGT: Spannweite Median 0,0188, Typfolge in 73,7 Prozent aenderbar |
| **v29-b05** Tor 1 gegen b03 | **427:373 aus 800 Partien**, gepoolt z = 1,98 |

**Das Verdikt zu b05** (par.12.6): das Entfernen des No-Op-Ziels macht das Netz nicht
schlechter, sondern **eher besser** -- beide Seeds und fuenf von sechs Standard-Kennzahlen
zeigen in dieselbe Richtung (Spalten +0,01/+0,10, Punkte +0,15/+1,99, Marge +0,31/+3,98).
Einzeln erreicht kein Seed die Signifikanzschwelle (p 0,159 und 0,235), gepoolt liegt es genau
darauf. **Kein Sieg, den man ohne Zusatz nennen darf** -- aber die Task-#38-Behauptung "der
moon-Kopf hilft" ist erstmals geprueft und in ihrer bisherigen Form widerlegt.

**Offene Nutzer-Entscheide:**
1. **Dritter Seed fuer b05** als Stichentscheid (rund 75 min, Praezedenz v26/v28). Ohne ihn
   traegt der Befund die Entscheidung "Kopf raus", aber keine Elo-Kante.
2. **b04 bauen?** Das Korpus-Tor ist mit 44,1 Prozent klar offen; b04 braucht Datenpfad,
   eigenen Fenster-Schluessel und einen neuen Monolith (rund 1 h Bau plus 35 min Monolith).
3. **32a (Weg C) fallen lassen?** 32c sagt, der Zugriffs-Hebel ist klein; der Knopf ist gebaut
   (Commit a4f92a5), seine Tore sind offen. Nach par.11-Nachtrag steht er ohnehin hinter 32b.

**Zwei eigene Fehler dieses Laufs, beide vom Nutzer an einer Zahl erkannt:** der erste b05-Start
lief OHNE `MOSAIC_CARRIER_MANIFEST` und haette mit 2.947 statt 580 Policy-Traegern einen
zweifaktoriellen Arm erzeugt (gestoppt, Skript um die Variable und eine Existenzpruefung
ergaenzt); und die erste Auswertung der Kennzahlen ordnete die Seiten nach Dict-Position statt
nach Namen zu, wodurch alle Vorzeichen vertauscht waren.

### Stand 2026-09-16: Netz-Gesundheit Punkt 5 -- kein Absterben, aber der Trend ist nicht messbar

**Fahrplan Nr. 20, Punkt 5 durch** (`PREREG_v29_window.md` par.9, Artefakte
`net_health_p5_generations_frozenv3.json` und `..._valsplit.json`).

`tools/offline_diagnosis.py` konnte keinen Alt-Checkpoint mehr laden -- es baute das Modell mit
der heutigen `config.INPUT_SIZE` und scheiterte an `size mismatch for flat_branch.0.weight`
(744 gegen 794). Jetzt leitet es die Breite je Checkpoint ab und KUERZT den Merkmalsvektor
darauf, genau wie es der Spielpfad tut (`net.rs:425` flach, `:989` Planes). Dass das erlaubt
ist, steht nicht nur in der Additivitaets-Notiz, sondern in drei Rust-Tests
(`features.rs:2273/2308/2511`) und in der git-Historie: die Breitensprünge `a336d72` und
`31a1321` loeschen im Bereich 0..754 keinen einzigen Wert.

**Das Ergebnis auf dem zurueckgehaltenen Satz `frozen_v3`** (n = 1.800 Zustaende, EINHEIT
Value-R2 Runde 1-4): v27-b01 0,3440 (Eingang 744), v28-b02 0,3168 (755), v29-b03 0,3296 (794).
**Kein monotoner Abbau** -- der Abstand von b03 zum aeltesten Stand ist 0,0144 und liegt unter
der Aufloesungsgrenze von rund 0,015. Die Sorge aus par.6d ("nicht dass uns der nun abstirbt
mit der Anzahl an Features") ist damit nicht bestaetigt.

**Der Trend selbst bleibt unbeantwortet, und das ist der wichtigere Befund.** Der
Default-Val-Split von `offline_diagnosis.py` liegt mit der Generation WACHSEND in den
Trainingssaetzen der verglichenen Netze (n = 360 Dateien, gegen `cli_args.file_list` der
Trainings-Manifeste: 82,2 Prozent in window_v29, 67,5 in window_v28, 32,5 in window_v27) -- und
zeigt darauf die UMGEKEHRTE Richtung (b03 vorn statt hinten). Innerhalb einer Aera kuerzt sich
das weg, deshalb bleiben Punkt 3 und 4 dort gueltig; ueber Aeren hinweg erzeugt die Reihe den
Trend, den sie zeigen soll. `frozen_v3` wiederum benachteiligt die neuen Netze doppelt (fremde
Aera, und keiner seiner 1.800 Records traegt `dome_pool_view`, also liegen 11+ Eingangswerte
auf Null). Verteilungsabstand und Generation sind auf diesen Saetzen nicht trennbar.

**Was fehlt, ist benennbar:** ein zurueckgehaltener Satz der LAUFENDEN Aera. Heute existiert
keiner -- jede der 3.603 Dateien in `data/` liegt in mindestens einem der drei Fenster. Der
Handgriff waere, vor dem Training der naechsten Generation eine Scheibe des frischen Self-Plays
zu reservieren und aus der Fensterliste zu nehmen. Das ist ein Kandidat fuer den
Generationswechsel, kein eigener Arm.

**NACHTRAG 20:40: damit ist auch die AERA-Frage von Punkt 3 beantwortet.** `v29-b01_best` traegt
**755**, nicht 794 (im Checkpoint nachgesehen) -- b03 gegen b01 ist also genau der Vergleich, den
Punkt 3 verlangt: 755 gegen 794 bei gleichem Fenster und Rezept. Auf frozen_v3 steht es 0,3337 zu
0,3296, **Abstand 0,0041** und damit unter der Aufloesungsgrenze 0,015 -- **kein Befund**, dieselbe
Groessenordnung wie beim Paar b03/b05 (0,0040). Gemessen auf CPU neben dem laufenden b04-Training
(erlaubte Paarung); zwei Staende der Tabelle liefen zur Kontrolle mit und reproduzieren die
GPU-Zahlen auf 2 mal 10^-5. Einschraenkungen: b01 gibt es nur als `_best` (Val-Loss) gegen b03s
`_brierbest`. **Die Orakel-Haelfte ist um 20:45 nachgezogen** und sagt dasselbe: Prior-Masse
auf Orakel-Top-3 +0,0002, Kendall-Tau +0,0013 fuer b03 gegen b01 (n = 915, frozen_v3-Labels,
Orakel v23-b01 @5.000 Sims, `oracle_p3_b03_vs_b01_frozenv3.json`) -- **Punkt 3 ist in beiden
Haelften durch, offen an par.6d bleibt nur Punkt 4.** `oracle_metrics.py` trug denselben
Breiten-Defekt und ist mitrepariert -- ebenso die drei Sonden `floor_action_aversion_gate`,
`long_row_prior_gate` und `saturating_score_utility_gate`, die dabei als DOPPELT tot auffielen:
sie zeigen fest auf `v21_2d_brierbest`, das der Aufraeumregel zum Opfer gefallen ist. Jetzt
ueber `MOSAIC_PROBE_MODEL` waehlbar, mit sprechendem Abbruch. Der Zuschnitt liegt seit heute als
gemeinsamer Helfer `neural_net.py::crop_features_to_model` vor. Artefakt
`net_health_p5_v29-b01_nachtrag.json`.

**Nebenher behoben:** kein Fortschrittszaehler (der 23-Minuten-Lauf war stumm), kein
`laufzeit`-Block im Artefakt, und ein Tabellenkopf, der auch im Frozen-Modus "Val-Split ...
val_frac=0.1" nannte -- also die falsche Grundmenge.

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v28-b02_brierbest`** (Promotion 2026-09-12),
**Elo 1371 [1332, 1419]** aus 2.350 Partien im LEITERSEGMENT 2 (44 Kanten, Anker `hv4_anchor`
fix 1000, Block-Bootstrap). Generator der v29-Erzeugung ist dasselbe Netz.

**NEU 2026-09-15: `v29-b03@400` fuehrt die Tabelle mit Elo 1402 [1353, 1456]** (640 Partien),
seit die Anker-Kante 128:22 eingetragen ist. Das ist KEIN Staerkebefund gegenueber dem
Champion: die Intervalle ueberlappen (1353-1456 gegen 1332-1419), und drei von b03s vier
Kanten sind frueh gestoppt und damit nach oben verzerrt -- die Anker-Kante ist seine erste
unverzerrte. Champion-Wechsel bleibt der Nutzer-Entscheid am Ende der Generationsarbeit.

Der Wert stieg am 2026-09-13 von 1353 auf 1394, weil drei neue Sims-Knoten unter dem
400er-Knoten einhaengen -- **kein neuer Staerkebefund**, sondern eine Folge der dichteren
Vernetzung. Neue Knoten: `v28-b02@100` 1298, `@200` 1289, `@600` 1389. Die Treppe
Anker -> hv4@600 -> v22@25 -> v22@100 -> v22@400 traegt.

**Eingefrorene Artefakte (nach dem Aufraeumen):** `frozen_champions/v28-b02` (amtierend,
Generator) und `v27-b01` (Vorgaenger, Champion-2-Kante); `frozen_heuristics/hv4_anchor`
(aktiver Anker), `hv2_generator` und `hv3_generator` (Sprossen, hv3 ist die Anfaenger-Stufe);
`models/restored_v22` (traegt den Leiterknoten v22-b05).

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `docs/measured_runtimes.md`)

| Aufbau | Dauer |
| --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11 (v27 / v28) | 10,25 h / 9,92 h |
| Argmax-Self-Play 200 Partien, threads 11, @100 / @400 / @600 | 791 s / 1.493 s / 2.113 s |
| Gepaarte Arena 75 Paare @100 gegen @400, threads 10, mit Logs | 1.121 s (7,5 s je Partie) |
| Gepaarte Arena 100 Paare @100 gegen @25 | 601 s (3,0 s je Partie) |
| Kette Schritte 1-6 (Kennzahlen, Manifeste, Fenster, Monolith) | rund 31 min |
| Training 12 Epochen, Fenster 2.947 Dateien | 5.117 s = 1,4 h |
| Gepaartes Gating 200 Paare @400, 10 Threads, mit `--log-games` | 86-91 min |
| Anker-Kante n=150 / Champion-2-Kante n=150 | rund 22 min / 43 min |
| Voller Build: Lib-Tests, no-run, Wheel, Install, Anker | rund 6 min |
| Anker-Drift / Konservierung | 15 s / 15 s |
| Tagesschnappschuss restic plus check | 6 s |

## 4. SPEC UND REZEPT

Champion-Spec `models/frozen_champions/v28-b02/spec.json`: `envelope_projection_mode` 1,
`envelope_search_c` 1,0, `envelope_flush_w` 0,0, `envelope_hull_form` 2, `special_row6_w` 1,0,
`score_utility_b` 20,0, Profil 1/0,92/0,67/0,33/0, `heuristik_variante` hv1.

**Die v29-Erzeugung faehrt `models/start_by_search_on.spec.json`** -- Feld fuer Feld dieselbe
Spec PLUS `start_by_search: 1` (verglichen 2026-09-13). Dazu in der Umgebung
`MOSAIC_STACK_DRAW_RESEARCH=1` und als Flag `--start-slot-random-p 0.15`.

**Engine seit Wheel 1 (2026-09-13):** P.10-Suchfix (die Wurzel-Determinisierung haelt den
oeffentlichen Typ der obersten Stapelplatte fest), Record-Feld `tiled_max_row` (P.14, wird auch
gelesen), Stapelzug-Knoepfe im Lauf-Manifest. Vertragshash `39648b95bbba1acf` unveraendert,
`input_size` 755. Netz-Paritaets-Fixture bewusst neu: `4750ffc6ec094a83`.

## 5. PREREG-BESTAND (9 OFFEN laut Index 2026-09-15, Ziel rund 7)

`python tools/generate_prereg_index.py` haelt `evaluations/PREREG_INDEX.md` aktuell; Stand
119 Dateien = **9 OFFEN** + 98 ENTSCHIEDEN + 12 UEBERHOLT. Die neun offenen sind alle aktiv
eingetaktet, keine ist liegengeblieben:

| Prereg | Was noch aussteht |
| --- | --- |
| `v29_window` | der laufende Zyklus selbst |
| `stack_top_feature` | Sicht-Arm v29-b03 (Wheel 2, INPUT_SIZE 794), dazu die zwei Regelbefunde par.16/16a |
| `special_tile_yield` | Ablations-Schalter und Arm v29-b02 |
| `difficulty_levels` | Bau waehrend der Erzeugung, Kanten nach Tor 1 |
| `claude_play_interface` | Partien g08-g10, Zugklassen-Differential |
| `moon_stack_order` | Knopf bauen, A/B am Champion |
| `dome_return_order` | Bau-Tor gruen (2026-09-15); offen ist der Korpus mit Streuung, mit der naechsten Erzeugung |
| `round_transition_search_sampling` | Variante B bauen (rund ein Tag), Sichttor, Kostentor, A/B; dazu NEU der Volllauf der Stufe-0-Sonde zu Top-K (par.16/16.7, s.u.) |
| `code_cleanup_closeout` | Stufen 2 und 3, nach der v30-Promotion |

Die Zahl liegt ueber dem Ziel, weil das v29-Begleitprogramm bewusst breit ist. Seit dem
2026-09-13 sind zwei gefallen: **`corpus_behaviour_audit`** (Korpuslauf durch, 2026-09-14) und
**`round_estimate_leaf_term`** (2026-09-15). `moon_stack_order` hat zwei von drei Stufen
gemessen (par.7, par.9h), bleibt aber offen, solange die Architektur-Hebel 32a/32b nicht
entschieden sind; `dome_return_order` bleibt ebenfalls offen -- sein Bau-Tor ist seit dem
2026-09-15 gruen, aber der Korpus mit Streuung kommt erst mit der naechsten Erzeugung. Mit
`round_transition_search_sampling` waeren es dann die angestrebten sieben.

> **KORRIGIERT 2026-09-15 (Nutzer-Nachfrage "sind alle im fahrplan genannten preregs aktuell?"):**
> hier stand, `dome_return_order` sei gefallen. Das war falsch -- sein Kopf sagt OFFEN, und der
> Koerper nennt eine offene Aufgabe. Gefallen ist stattdessen `corpus_behaviour_audit`, das in
> der Tabelle darueber noch als offen stand. Beim Nachziehen des Bestands waren zwei Namen
> genannt worden, ohne die Koepfe zu lesen.

**NEU 2026-09-16 (Nutzer-Auftrag, Counterfactual-Ranking-Sonde):** zu
`round_transition_search_sampling` ist par.16 dazugekommen - die Stufe-0-Sonde aus par.14.3 ist
vorregistriert UND gebaut (`tools/probes/counterfactual_tiling_ranking.py`). Sie fragt, ob der
Value-Kopf die Reihenfolge mehrerer Tiling-Plaene trifft und ab welcher Runde er eine exakte
lokale Entscheidung ueberstimmen darf. **Der Volllauf steht aus** (Maschine durch die b04-Kette
belegt); es gibt also noch KEIN Ergebnis, nur einen trocken geprueften Apparat. Zwei Punkte,
die andere Abschnitte beruehren:

* Der Bestand misst die Frage NICHT. `tools/tiling_value_reference_main.py:146` schneidet auf
  punktgleiche Kandidaten zu; ob das Netz einen Punktvorsprung zu Recht ueberstimmt, ist nie
  gemessen worden, obwohl der Zweig aktiv ist (`NET_TILING_TIEBREAK_ENABLED = true`,
  `tiling_solver.rs:858`, Runden 2-4 `:1603-1610`, Kriterium `punkte * P(Sieg)` `:944-964`).
* Die Lesart deckt vorab auch "das Netz rangiert systematisch FALSCH" ab (par.16.5 Ausgang 3).
  Faellt der Lauf so aus, ist das ein Befund GEGEN einen heute laufenden Engine-Zweig und damit
  ein Nutzer-Entscheid samt Anker-Invarianz, kein Tuning.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. ~~G-2-Haelfte des v29-Fensters~~ **ENTSCHIEDEN 2026-09-13, 13:20** (Nutzer: "Nimm fuer die
   g-2 das selbe was wir auch bei v28 hatten"): die AUSFLUG-Haelfte
   `selfplay_v26-b01-value-excursion_*`, 145 Dateien seed-gezogen mit 20260941. In
   `PREREG_v29_window.md` par.2 registriert und in `tools/night_v29_chain.sh` gesetzt; die 401
   Quelldateien liegen vollstaendig im Baum.

2. **Manifest meldet Spec-Felder falsch** (geprueft 2026-09-13): `engine_config` zeigt fuer
   `envelope_search_c`, `envelope_projection_mode`, `envelope_hull_form` und `special_row6_w`
   den Env-Default statt des wirksamen Spec-Werts, weil `lib.rs` Z.801/807/812/815
   `SearchConfig::from_env()` lesen. **Kein Belegverlust** -- die Spec-Datei hat genau einen
   Commit und ist unveraendert, jedes Manifest nennt ihren Pfad in `cli_args.spec`.
   **Vorschlag: Spec-Inhalt plus sha256 additiv ins Manifest** (`selfplay_manifest.py`), damit
   der Beleg nicht an der Unveraenderlichkeit einer Datei haengt. Nicht waehrend eines Laufs
   bauen: die Chunk-Prozesse importieren frisch.

3. **Sichtluecke bei den gezogenen Stapelplatten -- zwei Kanaele, zwei Reparaturen**
   (`PREREG_stack_top_feature.md` par.16 und par.16a). Die Vorderseiten sind nach Regelauskunft
   erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste verraet sie ueber die
   designabhaengige Rotationsfilterung (`game.rs` Z.402) -- betrifft die Suche, Reparatur
   beruehrt `NUM_ACTIONS`. (b) `serialize.rs` Z.375-379 serialisiert sie sofort, die Anzeige
   druckt sie (`claude_play.py` Z.721) und die Platzierungs-Vorschau rechnet damit (Z.597/656)
   -- betrifft den menschlichen Spieler, live eingetreten in Partie g07. Umfang und Prioritaet
   sind offen; beruehrt die Gueltigkeit von g02-g07.

4. ~~Cache-Bloecke und Monolithe~~ **ERLEDIGT 2026-09-14** (Abschnitt 1 Punkt 3: 1.842 Bloecke
   und acht Monolithen, rund 4,9 GB, auf Freigabe des Nutzers geloescht).

5. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
   Loeschung; am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

6. ~~Textverweise auf `hv1_anchor` nachziehen~~ **ERLEDIGT 2026-09-13, 13:35** fuer die
   Stellen, die aktiv fehlleiteten: CLAUDE.md (Anker-Invarianz nennt jetzt `hv4_anchor` als
   Fixpunkt seit der Neuverankerung), `docs/working_rules.md`, `docs/architecture_reference.md`,
   `docs/generation_naming.md`. **Offen und ein echter Befund:** drei Sonden greifen direkt auf
   das geloeschte Artefakt zu und laufen nicht mehr --
   `tools/probes/anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
   `frozen_worker_protocol_probe.py`. Sie tragen jetzt einen Hinweis statt eines kryptischen
   Abbruchs. Eine Umstellung auf `hv4_anchor` braucht NEUE Erwartungswerte (die hartkodierten
   gelten fuer hv1, z. B. `scores [27, 15], steps 159`), also einen Lauf -- Nutzer-Entscheid, ob
   das lohnt oder ob die drei als historisch entfallen. Verweise, die bewusst die VERGANGENHEIT
   beschreiben (`docs/promotion_checklist.md` Z.34, die Historien-Kommentare in
   `tools/elo_tracker.py`, das Beispiel in `tools/freeze_heuristic.py`), bleiben unveraendert.

7. ~~Skala des Rundenschaetzers~~ **GEGENSTANDSLOS 2026-09-15**: der Term schadet in beiden
   vorregistrierten Dosen (`round_estimate_leaf_term` par.7c/7d). Der Vorschlag eines
   Rundenprofils wie K3 RUHT (Nutzer 2026-09-15, par.7e); der Term ist damit abgeschlossen.

8. **Rahmen (ENTSCHIEDEN 2026-09-12, hier als Erinnerung):** v30 wird released und ist der
   Projektabschluss, Schlussmodell heisst **Tessa**. v29 traegt das Begleitprogramm, v30 nur
   noch Rezept-Knoepfe.
   **OFFEN GEHALTEN 2026-09-16, 22:00 (Nutzer):** "ich denk nach b06 sind wir fertig mit v29.
   so wie ich es momentan seh kann es gut sein dass noch ein v31 kommt damit die ganzen
   aenderungen wirklich sauber durchschlagen." Der Rahmen "v30 = letzte Generation" ist damit
   nicht mehr fest. **PRAEZISIERT vom Nutzer (22:05): ab v30 KEINE neuen Preregs mehr;
   gefahren wird nur noch Staerke ueber Generationen, gegebenenfalls mit Armen aus den JETZT
   offenen Preregs. Vorschlaege mit Wirkung erst in v31 (Weg A, R2 im Training) sind nicht aus
   dem Rennen, "wenn sie wirklich einen nutzen zeigen"** -- also nur mit gemessenem Beleg aus
   einer bestehenden Prereg, nie als neue Vorregistrierung.

9. ~~Trainingsziel des `moon`-Kopfs~~ **ENTSCHIEDEN 2026-09-15 (Nutzer: "beides")**: zwei Arme,
   `v29-b05` (b03 plus `--moon-loss-weight 0`, sofort startbar auf b03s Monolith) und `v29-b04`
   (b03 plus Ziel = gespielte Reihenfolge, nach Korpus-Sonde und Datenpfad-Bau). Tor 1 je Arm
   gegen b03. Fahrplan 32b, `PREREG_moon_stack_order.md` par.12.1, Namen in
   `docs/generation_naming.md`.

10. ~~Rueckgabe-Reihenfolge in der v30-Erzeugung~~ **ENTSCHIEDEN 2026-09-15 (Nutzer: "mit r2
    und modus 1 ein", `PREREG_dome_return_order.md` par.12.6):** R2 (geordnete eigene Designs,
    +4 Werte, INPUT_SIZE 798) wird VOR der v30-Erzeugung gebaut (Fahrplan 29c), und Modus 1
    (`return_order_mode: 1`) ist in der v30-Erzeugungs-Spec AN -- ein Korrektheitsentscheid, der
    das "bleibt aus" vom selben Vormittag ersetzt. Streu-Knopf 0,015 bleibt daneben (er greift
    nach dem Entscheider). Kostentor beim Start der Erzeugung: `s_je_partie` gegen v29. R2 ist
    neben P.12 die zweite Ausnahme vom Rahmen "v30 nur Rezept-Knoepfe".

11. ~~Marge und Zeitpunkt fuer den Minimalkern~~ **ENTSCHIEDEN 2026-09-16; GEMESSEN 2026-09-17: b06 ist
    b03 UNTERLEGEN (44,5 Prozent, p 0,011, par.10.3).** Offen daraus: **Punkt 13.** Ursprung: `v29-b06` (b03 ohne die vier
    Hilfs-Losses) gegen b03, Nichtunterlegenheit = gepoolt mindestens 45,0 Prozent auf 800
    Partien und kein Seed signifikant dagegen; Fahrplan 36a nach dem A/B von Variante B.
    `PREREG_minimal_strength_core.md` par.10, Name reserviert. **Vorpruefung durch (par.10.1):**
    die Suche liest unter der Champion-Spec policy, value und den moon-Prior; points wird mit
    Gewicht 0 gelesen, ownership/opp_points/endgame sind tot. b06 = b05 plus ownership 0, ohne
    opp_points und endgame; moon und points bleiben als Ausgaenge (positional gelesen). OFFEN
    bleibt die Aufnahme ins v30-Rezept nach dem Ergebnis.

12. **Rezept-Aufnahme `--moon-loss-weight 0`** (Fahrplan 32b, `PREREG_moon_stack_order.md`
    par.12.8): b05 schwach positiv, b04 negativ -- der Kopf ist Ballast. Aufnahme ins v30-Rezept
    ja/nein; b06 (par.10 der Minimalkern-Prereg) faehrt ihn ohnehin auf 0 mit.

13. **Strang A einzeln fahren?** (`minimal_strength_core` par.10.3 Lesart): b06 reisst die Marge,
    b05 (nur moon aus) war leicht besser -- also traegt mindestens einer von ownership /
    opp_points / endgame als Trainingssignal. Die registrierte Fortsetzung ist A.3 (drei Arme
    einzeln gegen b03, je rund 4,5 h, 13-14 h gesamt). Ohne sie: alle drei Koepfe bleiben im
    v30-Rezept, `moon_loss_weight 0` bleibt Empfehlung (Punkt 12).

14. **Variante B** (`round_transition_search_sampling` par.17.9): negativ, kommt nicht ins Rezept
    -- kein Entscheid noetig, nur zur Kenntnis. Offen dort: Stufe-0-Sonde par.16 als Diagnostik
    (fahren oder streichen).

15. **Loeschkandidaten** (pfadgenau, h5 ohne restic-Beleg noetig, Manifest klein):
    `data/.cache_fd13f54061cd.h5` (1,15 GB, falscher Stempel 4dd9f020b232),
    `models/manifest_train_v29-b06_20260917_011916.json` (abgebrochener erster b06-Anlauf).

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Stand 2026-09-15, 09:00: **17 Commits vor origin/main**, der
  Nutzer pusht selbst.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein
  Build zaehlt als Last.
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch.
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, kein
  Geviertstrich in Dateien, Bezeichner englisch.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **Replayer-Grenze Chip-Vollendung:** einzelne Partien nicht nachspielbar ("Reihe N nicht mit
  Chips komplettierbar" nach 60 Versuchen); bekannte Grenze.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe** (geprueft 2026-09-13,
  `PREREG_difficulty_levels.md` par.11). Beide enden in `select_final_root_child`, beide ohne
  Wurzelrauschen, beide mit Runde-5-Kurzschluss, und `server.py` schreibt die Champion-Spec
  beim Start in die Umgebung, weil der GUI-Pfad sie von dort liest. **Die GUI spielt heute
  immer bei 400 Sims**, weil die Presets aus ihr nicht erreichbar sind (par.2 dort: alle 33
  Mensch-Partien liefen @400) -- also genau die Einstellung, bei der die Arena misst.
  Zwei Irrtuemer von mir stehen dort korrigiert: die `or 100`/`or 300`-Ausdruecke sind tote
  Fallbacks, und die Presets im Code (60/60/150/400) sind NICHT der registrierte Zuschnitt der
  Stufenleiter (Anfaenger hv3@150, darueber Champion mit Stilmitteln, Meister wie die Arena).
  Beide Male kam die Korrektur vom Nutzer.
  **Latente Sollbruchstelle:** die Arena zieht `builder_drafting_preference` der Suche vor, der
  Serverpfad kennt den Vorzug nicht; folgenlos nur, solange
  `MOSAIC_SPALTENBAU`/`MOSAIC_PLATTENBAU` unbesetzt bleiben.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf,
  der in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt; bei Modus 2 oder 4 waeren sie exakt der
  Stack-Draw-Fall.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, und zwar
  allein ueber die VOLLENDUNG -- die Teilspalten bleiben gleich
  (`PREREG_search_depth_column_optimum.md` par.8e).
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
