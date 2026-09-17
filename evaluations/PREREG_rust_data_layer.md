<!-- STATUS: ENTSCHIEDEN | Frage: Wird die Python/Rust-Naht an der Datenschicht konsolidiert -- Merkmalsbauer als EINE Wahrheit in Rust (Teil A), Rohformat aus Rust (Teil B)? | Beleg: TEIL A GEBAUT UND BEWAEHRT (par.7/par.8), TEIL B ohne Ausloeser. Paritaets-Tor rot nur auf ALT-Records (par.9/par.9a): 2 von 300 Zustaenden, Ursache der A2-Phantom-Fix vom 2026-09-12, gespeichert gegen frisch gerechnet. Weg (1) GEBAUT (par.9b, Nutzer 2026-09-17): Formelversion und MOSAIC_FEATURES_FROM_RUST in BEIDEN Cache-Schluesseln; Alt-Caches orphaned, Neubau ab v29-b08 (Kette 36e). -->

# Vorregistrierung: Datenschicht in Rust (Merkmalsbauer und Rohformat)

**Angelegt 2026-08-28**, nichts gebaut. Anlass ist eine Nutzer-Frage nach dem
idealen Python/Rust-Setup, nicht ein akuter Engpass. Diese Datei ist eine
**Registrierung**: sie haelt Zuschnitt, Tore und Ausloese-Bedingungen fest,
damit die Entscheidung spaeter nicht neu erfunden wird.

## par.1 Anlass: die Sprachaufteilung stimmt, die GRENZE ist teuer

Die heutige Aufteilung -- Suche, Spiellogik und Merkmalsbau in Rust, Training
und Auswertung in Python/Torch -- ist nicht Gewohnheit, sondern gemessen. Die
Gegenprobe ist gefahren und geschlossen: der beste GPU-Weg erreichte **1,255x**
gegen ein vorab gesetztes Tor von 2,0x
(`PREREG_gpu_inference_path.md`), und die Wanduhr von `tract` hat die
FLOP-Rechnung zweimal geschlagen. Diese Prereg schlaegt also **keine**
Verschiebung der Sprachgrenze vor.

Teuer ist etwas anderes: **die Naht selbst.** Zwei Kosten sind belegt.

**(a) Jede Eingabe-Erweiterung ist ein Dreifachbau.** Ein neuer Kanal muss in
`engine/src/features.rs` (Direct-Pfad der Suche), in `engine/py/neural_net.py`
(Zwilling fuer den Cache-Bau) und in den Paritaets-Fixtures nachgezogen
werden. Der Kanalbau 77 -> 79 vom 2026-08-27 (`e91cd34`, Spezialfeld-Ertrag
und Abstand zur Ausloesung) beruehrte genau diese drei Stellen.

**(b) Die Drift-Fehlerklasse ist nicht theoretisch.** Im selben Bau haette das
Bitpacking die beiden neuen, **wertetragenden** Kanaele still auf 0/1
kollabiert. Gefangen hat es nicht ein Waechter, sondern der Umstand, dass
gerade jemand an dieser Stelle baute; der Waechter (wertetragender Kanal vor
der Binaergrenze) entstand erst als Folge. Zwei Fassungen desselben Bauers
sind eine dauerhafte Einladung fuer diese Fehlerklasse.

## par.2 TEIL A: Merkmalsbauer-Export nach Rust

**Dieser Teil ist der UMZUG von Hebel (2) aus `PREREG_cache_build_time.md`
par.3.** Die dort registrierten Bedingungen gelten unveraendert weiter; sie
werden hier nicht gelockert, sondern nur an den Ort gestellt, an dem sie
inhaltlich hingehoeren.

**Zuschnitt:** die Bauer in `engine/src/features.rs` werden per `pyo3` nach
Python exportiert; `mosaic_rust` kennt heute keinen Merkmals-Einstieg. Rust
wird damit **die einzige Wahrheit**. Der Python-Zwilling
(`engine/py/neural_net.py`: `state_to_planes` :405, `_board_channels` :372,
`state_to_tensor` :45) degradiert zum **Test-Orakel** -- oder entfaellt, wenn
die Fixture-Maschinerie die Absicherung allein traegt.

Der Unterschied zur Fassung in der Cache-Prereg ist die Absicht: dort war der
Export ein **Opt-in neben** der Python-Fassung, hier ist das Ziel, den
Zwilling als PRODUKTIVEN Pfad **abzuschaffen**. Das Tor bleibt dasselbe.

### Die Vorbedingung wandert mit

`PREREG_cache_build_time.md` par.5b legt vorab fest: **nach Hebel (1) wird der
Merkmalsanteil an der NEUEN Wanduhr erneut gemessen**; ist er nicht mehr der
dominante Posten, entfaellt der Export als Zeit-Hebel -- ein Nullbefund, kein
Fehlschlag. Diese Regel gilt hier weiter.

Die Zahlen der Quell-Prereg, zitiert statt neu erfunden (par.2 und par.5b
dort, gemessen 2026-08-25 an 400 Zustaenden aus hv2):

| Posten | je Zustand | Anteil der Merkmalszeit |
| --- | --- | --- |
| `state_to_planes` | 1,896 ms | **85 %** |
| `state_to_tensor` | 0,185 ms | 8 % |
| Unpickle | 0,150 ms | 7 % |
| Summe | 2,23 ms | |

2,23 ms x 890.000 Zustaende = 33 min; beobachtet wurden damals ~70 min.

**Diese 85 Prozent sind der Stand VOR Hebel (1) und (4).** Beide sind seither
gebaut und abgenommen (par.7 bis par.9 der Quell-Prereg: Faktor 4,99 auf 120
Dateien, 36,1 min fuer den vollen Korpus, Datei-Cache mit eigener
Schluesselteilung). Was danach vom Merkmalsanteil uebrig ist, ist **ungemessen**
-- die Hochrechnung in par.5b (~7 von ~14 min, dann ~1 von ~8) ist als
Hochrechnung markiert und taugt nicht als Beleg.

### Hartes Tor, unveraendert

1. **BIT-IDENTITAET des erzeugten Caches gegen den Python-Bauer**, Feld fuer
   Feld, `np.array_equal`, keine Toleranz -- und zwar **VOR** der Umstellung
   des Produktivpfades, nicht danach.
2. **Paritaets-Hash** (`engine/tests/fixtures`, Regenerator hinter
   `MOSAIC_UPDATE_FEATURE_FIXTURE=1`) unveraendert, plus die Suite gruen.
3. Der Schalter gehoert **NICHT** in den Cache-Schluessel: sind beide
   Fassungen bit-identisch, MUSS derselbe Schluessel herauskommen -- sonst
   waeren alle bestehenden Caches wertlos.

**Kill-Kriterium:** stellt sich Bit-Identitaet nicht her und laesst sich die
Abweichung nicht auf einen behebbaren Unterschied zurueckfuehren, stirbt Teil
A. Ein "fast gleicher" Cache ist schlechter als ein langsamer.

### Benannte Nutzniesser (Infrastruktur-Regel verlangt das)

1. **Jede kuenftige Eingabe-Erweiterung.** Offen sind mindestens das
   Slot-Ziel, die Huellen-Gewichtung und `PREREG_stack_top_feature.md`. Jede
   davon kostet heute den Dreifachbau aus par.1(a).
2. **Der Cache-Bau**, in dem Umfang, den die Neumessung noch ausweist.
3. **Die Abschaffung der Zwillings-Drift-Fehlerklasse.** Beleg ist der
   Bitpacking-Vorfall vom 2026-08-27; er ist der teuerste der drei Posten,
   weil ein stiller Kanal-Kollaps sich nicht als Fehler meldet, sondern als
   schwaechere Messung.

## par.3 TEIL B: spaltenorientiertes Rohformat, von Rust geschrieben

**Heutiger Zustand:** der Rohstand ist gzip-Pickle von Python-Dicts. Der
Kompressionsfaktor **35,4** (STATUS.md, gemessen an 12 ordnungsfrei gezogenen
Dateien, Spanne 35,1-35,7; 34,70 GB -> 0,98 GB fuer 2.401 Dateien) misst
genau die Redundanz eines zeilenweisen Objektformats. Auf der Leseseite kostet
das Unpickle **0,150 ms je Zustand** (`PREREG_cache_build_time.md` par.2), und
danach folgt jedes Mal dieselbe Neuinterpretation der Dicts.

**Vorschlag:** ein spaltenorientiertes Format, von Rust geschrieben und von
beiden Seiten gelesen. Die Schreibseite faellt bei Teil A ohnehin fast an.

### Design-Pflichten, aus teuren Lektionen

**(a) Das Format speichert ROHE Zustaende verlustfrei -- keine Merkmale.**
Als `INPUT_SIZE` am 2026-08-25 von 708 auf 714 ging, war jeder bestehende
Cache wertlos, und **nur die pkl** erlaubten den Neubau (STATUS.md). Der
77->79-Kanalbau wirkte aus demselben Grund rueckwirkend auf den gesamten
Bestandskorpus. Diese Faehigkeit darf ein neues Rohformat nicht verlieren --
ein Format, das Merkmale einfriert, ist ein Cache und kein Rohstand.

**(b) Die pkl bleiben Rohstand, bis zwei Belege da sind.** Erstens ein
**voller Roundtrip** (pkl -> Format -> feldidentische Records) auf dem
GESAMTEN Korpus, nicht auf einem Ausschnitt. Zweitens ein bestandener
**Regenerations-Test ueber eine Eingabe-Erweiterung**: aus dem neuen Format
muss ein Cache mit einem zusaetzlichen Kanal gebaut werden koennen, ohne den
Korpus neu zu erzeugen. Erst wenn beides steht, ist ueber die pkl zu reden --
und auch dann ist ihr Loeschen ein Nutzer-Entscheid.

**(c) Die Formatwahl ist ein Bau-Entscheid mit Benchmark-Tor, kein
Vorab-Geschmack.** Arrow/Parquet gegen ein eigenes HDF5-Schema wird an
gemessenen Zahlen entschieden (Lesezeit je Zustand, Platte, Schreibzeit,
Abhaengigkeiten auf beiden Seiten), nicht vorab in dieser Datei festgelegt.

### Benannte Nutzniesser

Jede Sonde und jeder Cache-Bau zahlt heute Unpickle plus Neuinterpretation der
Dicts, auch dort, wo nur wenige Felder gebraucht werden -- ein
spaltenorientiertes Format laesst den Rest ungelesen.

## par.4 AUSLOESE-BEDINGUNGEN (Nutzer-Formulierung 2026-08-28)

Der Nutzer hat den Zeitpunkt selbst festgelegt, und diese Formulierung wird
hier als Registrierung uebernommen: *"Kein akuter Posten -- erst, wenn wieder
eine Messung an der Ladezeit haengt."*

**Teil B startet**, wenn eine der beiden Bedingungen erfuellt ist:

* eine **konkret benannte** Messung, deren Wanduhr erkennbar vom Laden und
  Parsen dominiert wird. Richtwert: **Lade-/Parse-Anteil ueber 25 Prozent des
  Laufs, im Artefakt belegt** (`laufzeit`-Block), nicht geschaetzt; **oder**
* Teil A wird ohnehin gebaut und die Schreibseite faellt mit ab.

**Teil A startet** fruehestens **NACH dem v22-Zyklus** -- nicht waehrend der
laufenden Kampagne, weil ein Eingriff am Merkmalspfad jede Messung darin
kontaminieren wuerde -- und nur nach der Neumessung des Merkmalsanteils aus
par.2.

**Bis dahin ist diese Prereg eine Registrierung, kein Arbeitsauftrag.** Wer
sie als Aufgabenliste liest, hat sie falsch gelesen.

## par.5 Was diese Prereg NICHT ist

* **Kein GPU-Wiedereinstieg.** Der Weg ist geschlossen bis zu einem groesseren
  Netz (`PREREG_gpu_inference_path.md`); dieser Vorschlag beruehrt ihn nicht
  und darf nicht als Hintertuer dorthin benutzt werden.
* **Kein Ersatz der Torch-Trainingsseite.** Training, Auswertung und
  Sonden bleiben in Python.
* **Keine Aenderung an Zielen, Labels oder Verlusten.** Rein
  traegerseitige Infrastruktur.

**Erfolgsmass:** Irrtumskosten, nicht Elo. Konkret -- Drift zwischen zwei
Merkmalsfassungen wird strukturell unmoeglich statt nur getestet, und eine
Eingabe-Erweiterung kostet einen Bau statt drei. Beides taucht in keinem
Elo-Wert auf. Die Gegenprobe, die die Infrastruktur-Regel verlangt: wenn zum
Ausloesezeitpunkt keine Eingabe-Erweiterung ansteht und keine Messung an der
Ladezeit haengt, ist der Bau **nicht** faellig -- dann ist er Aufraeumen, und
Aufraeumen konkurriert mit Spielstaerke um dieselbe Zeit.

## par.6 EINGETAKTET (Nutzer 2026-09-11, 00:10): Teil A als Bauschritt von Variante B

Der Audit vom 2026-09-09 hatte diese Prereg als Registrierung ohne Nutzniesser gefuehrt; die
Sperre "nach v22" war abgelaufen, die Vorbedingung aus par.2 (Merkmalsanteil nach den Hebeln
neu messen) nie erfuellt, und Teil B ohne Ausloeser (v27-b01-Training: Datenaufbau 35,4 s von
5.116,7 s, also 0,7 % gegen die 25 %-Schwelle aus par.4). Was sie dennoch traegt, steht in
par.1: nicht die Ladezeit, sondern die GRENZE ist teuer, jede Eingabe-Erweiterung ist ein
Dreifachbau. Mit Variante B (`PREREG_v28_window.md` par.8, elf neue Werte) steht genau das an.
**Nutzer-Entscheid: Teil A wird als Bauschritt von Variante B gefahren** -- Merkmal einmal in
Rust, pyo3-Export der beiden Bauer, Python-Zwilling nur noch Test-Orakel, hartes Tor aus
par.2 unveraendert (Bit-Identitaet VOR der Umstellung, `np.array_equal`; Schalter
`MOSAIC_FEATURES_FROM_RUST` NICHT im Cache-Schluessel; Kill-Kriterium bei nicht herstellbarer
Identitaet). **Dieser Punkt ist UEBERHOLT seit par.9b (2026-09-17): der Schalter steht in
BEIDEN Cache-Schluesseln**, weil die Bit-Identitaet auf Alt-Records nicht mehr gilt.
Verdikt hier, sobald das Tor gefahren ist. Teil B bleibt ohne Ausloeser liegen
und wird beim naechsten Bestandsabgleich UEBERHOLT, falls die Schwelle weiter verfehlt wird.

## par.7 TEIL A: TOR BESTANDEN (2026-09-11, 14:46)

Wheel mit INPUT_SIZE 755 gebaut und installiert (Variante B, `PREREG_v28_window.md` par.9);
`tools/probes/feature_parity_rust_python.py` (Konstruktor-Aufruf berichtigt: `PyGame` nimmt ein
Tupel) auf zwei Grundmengen: 733 Zustaende aus 4 Heuristik-Partien @30 (alle mit
`dome_pool_view`, Seeds ab 20260911) und 300 Zustaende aus 3 Sockel-Dateien
`selfplay_v26-b01-policy_*.pkl` (ohne das Feld, Null-Pfad). Ergebnis: Flachvektor 755 gleich
1.033/1.033, Planes gleich 1.033/1.033, `np.array_equal` ohne Toleranz; 16,0 s, 1 Thread.
Artefakt `evaluations/artifacts/feature_parity_rust_python.json`. Anker-Drift auf demselben
Wheel GRUEN (1.763 Schritte, `anchor_drift_live_wheel_20260911_varB.json`). Damit ist die
Umstellung des Blockbaus auf den Rust-Bauer freigegeben; die v28-b02-Kette
(`tools/night_v28_b02.sh`) setzt `MOSAIC_FEATURES_FROM_RUST=1`. Der Python-Zwilling bleibt als
Test-Orakel im Baum. Verdikt fuer Teil A folgt mit dem b02-Training (Blockbau-Laufzeit gegen
den Python-Pfad als Nebenbefund); Teil B bleibt ohne Ausloeser.

## par.8 VERDIKT TEIL A (2026-09-11): ENTSCHIEDEN, Bauweg bewaehrt

Der Rust-Merkmalsbauer hat den Blockbau des v28-Fensters unter dem 755er-Schluessel getragen
(2.947 Bloecke in 26 min, 6 Worker, `docs/measured_runtimes.md`), das Paritaetstor war
bit-identisch (par.7), der Arm v28-b02 wurde damit trainiert und gemessen (Nullbefund in der
Arena, `PREREG_v28_window.md` par.10; das ist ein Befund ueber das MERKMAL, nicht ueber den
Bauweg). Erfolgsmass laut par.5 sind Irrtumskosten, nicht Elo: jede weitere Merkmalserweiterung
wird einmal in `features.rs` gebaut und ueber das Paritaetstor freigegeben; der Python-Zwilling
bleibt Test-Orakel. Teil B (Rohformat aus Rust) bleibt ohne Ausloeser (Datenaufbau 34 s von
5.262 s beim v28-b02-Training). Kopf auf ENTSCHIEDEN.


## par.9 Paritaets-Tor am 2026-09-14: flach GRUEN, Planes zwei Abweichungen -- und warum

Gefahren nach dem Wheel von Encoder-Abschnitt 16 (INPUT_SIZE 794). Grundmenge wie beim
bestandenen Tor: 733 pygame-Zustaende aus 4 Partien plus 300 Korpus-Zustaende aus
`data/selfplay_v26-b01-policy_*.pkl`.

**Flachvektor: GRUEN in beiden Populationen** (733/733 und 300/300), nachdem ein Fehler im
Python-Zwilling behoben war: er zaehlte die Blocktiefe aus P.13 ab dem ersten bekannten Block,
`features.rs` ab dem Stapelanfang (also einschliesslich des unbekannten Praefix). Das Tor hat ihn
gefangen -- Index 789, Rust 7/18 gegen Python 0. Genau dafuer ist es da.

**Planes: 2 von 300 Korpus-Zustaenden weichen ab** (pygame 733/733 gleich). Immer derselbe Kanal:
**76, Erreichbarkeit je Zelle** (`features.rs` Z.1680), Beispiel Zelle (5,1), Python 0,0 gegen
Rust 1,0.

**Ursache, am Code belegt und NICHT bei den Aenderungen dieser Woche:**

- Der Python-Zwilling LIEST das Feld `cell_reachable_mask` aus dem Record
  (`neural_net.py` Z.781), Rust RECHNET es neu aus dem rekonstruierten Zustand.
- Die Rechnung haengt an `provocation::remaining_colors` bzw. `still_reachable_colors`.
- **Diese Funktion ist am 2026-09-12 geaendert worden** (Commit 2a0cf4b, "Code-Abschluss Stufe 1",
  148 Zeilen in `provocation.rs`): der **A2-Phantom-Fix** zieht die Phantom-Fliesen der
  Gegner-Reihen ab, die nie gezogen worden sind.
- Die v26-Records stammen vom 2026-09-09 und tragen den Stand DAVOR. Python liest die alte Zahl,
  Rust rechnet die neue -- die Abweichung ist der erwartete Effekt eines Korrektheits-Fixes auf
  Alt-Records, kein Regressionsbefund.

**Folge fuer das Tor selbst:** es vergleicht eine GESPEICHERTE Groesse gegen eine NEU GERECHNETE.
Sobald eine Formel hinter einer gespeicherten Groesse korrigiert wird, kann es auf Korpora aus der
Zeit davor nicht mehr bestehen -- und zwar dauerhaft, nicht nur einmal. Das ist eine Eigenschaft
der Bauform, keine Regression. **Wer das Tor kuenftig fuer eine Abnahme braucht, fahre es auf
FRISCHEN Zustaenden** (die pygame-Population tut genau das und ist gruen) oder schliesse die
betroffenen Kanaele mit Begruendung aus. Der Vorschlag ist hier NICHT umgesetzt, weil er das Tor
aendert -- das ist ein Nutzer-Entscheid.

**Nicht geprueft:** ob die 2 von 300 wirklich alle auf den Phantom-Fall zurueckgehen. Der Beleg
ist die Kette Formel-Aenderung -> Alt-Record, nicht eine Zustand-fuer-Zustand-Analyse.

## par.9a NACHGEPRUEFT (2026-09-17): es ist der Phantom-Fall, Zustand fuer Zustand -- und der Flachvergleich ist an dieser Stelle blind

par.9 liess ausdruecklich offen, "ob die 2 von 300 wirklich alle auf den Phantom-Fall
zurueckgehen". Sie tun es. Ausgeloest hat die Nachpruefung der Lauf vom 2026-09-17
(`evaluations/artifacts/feature_parity_rust_python.json`, Sonde erneut rot), gemeldet als
fremder Befund in `PREREG_round_transition_search_sampling.md` par.17.7 (f) und in STATUS.

**Geprueft** (einkernige Diagnoseskripte im Scratchpad, kein Wheel-Bau, Prozessliste vorher leer):

1. Kreuztabelle ueber die GANZE Korpus-Grundmenge (n = 300 Zustaende aus 3 Dateien
   `data/selfplay_v26-b01-policy_*.pkl`, Einheit Zustaende): 9 Zustaende tragen
   `phantom_count > 0`, abweichend sind 2 (Index 101 und 265) -- beide gehoeren zu diesen 9.
   Jede Abweichung ist genau 1 Wert in Kanal 76; kein anderer Kanal ist beteiligt.
2. Zustand 101 nachgerechnet: Zelle (5,1) fordert blau, Musterreihe 5 haelt 3 blau, es fehlen
   also 3. Ohne Phantom-Abzug bleiben 2 blau uebrig (nicht erreichbar, 0.0), mit Abzug 3
   (erreichbar, 1.0) -- die Schwelle liegt exakt dazwischen. Der ziehende Spieler haelt
   1 Phantom-Blau in Reihe 1.
3. Haerter als die Zeitreihe: das MITGESPEICHERTE Feld `col_f_max` (`serialize.rs` Z.233-235,
   aus derselben `remaining`-Variablen wie die Maske) trifft in beiden Zustaenden die ALTE
   Formel exakt (12 von 12 Spaltenwerten) und die neue in keinem. Die Records sind also
   nachweislich ohne Phantom-Abzug geschrieben, nicht nur ihrem Datum nach.
4. Gegenprobe auf NEUEN Records (n = 600 Zustaende aus 6 Dateien
   `data/selfplay_v28-b02-value-tempc_20260913_*.pkl`, erzeugt nach dem Fix): 15 Zustaende
   mit `phantom_count > 0`, 0 Abweichungen.

**Keiner der drei Kandidaten liegt falsch.** Der Rust-Bauer rechnet nach heutiger Formel, der
Python-Zwilling liest, was im Record steht, und die Rekonstruktion ist unbeteiligt:
`remaining_colors` liest Fabriken, grosse Fabrik, Musterreihen, Strafleiste und Kuppelraster,
und die kommen vollstaendig aus dem JSON (Mondstapel MIT Farben, `serialize.rs` Z.205 und
Z.950); Beutel und Turm liest sie ausdruecklich nicht. Der feste Seed 0 in `json_to_state` ist
damit unbeteiligt. Auch der `dome_pool_view`-Verdacht aus par.17.7 (f) ist widerlegt: das Feld
fehlt in ALLEN 300 Alt-Zustaenden, abweichend sind 2.

**NEU, nicht in par.9: der Flachvergleich ist an dieser Stelle strukturell blind.** Dieselbe
Formel steckt im Flachvektor, als `col_f_max` (6 Werte; `features.rs` Z.907 LIEST sie aus dem
Record, `features.rs` Z.1371 RECHNET sie frisch). Die Sonde meldet flach 300/300 gruen -- aber
nur, weil sie dort ZWEIMAL die gespeicherte Groesse vergleicht: der Python-Zwilling liest
`col_f_max`, und der pyo3-Export `state_features_from_json` ruft den JSON-Pfad, der ebenfalls
liest. In beiden betroffenen Zustaenden weicht der Wert tatsaechlich ab (`col_f_max[1]`: Record
5, frische Formel 6). Fuer die Planes gibt es in Rust keinen JSON-Pfad (`state_planes_from_json`
geht immer ueber `state_to_planes_direct`) -- nur deshalb faellt die Klasse dort auf. Ein Tor,
das den `direct`-Pfad nie anfasst, kann sie nicht sehen.

**Trainingsdaten: ja, beruehrt -- aber nicht durch einen falschen Wert, sondern durch eine
nicht unterscheidbare Semantik.** Die Kette, jedes Glied geprueft:

- Der Blockbau ruft die WEICHE `state_to_planes` (`corpus_dataset.py` Z.1269), also entscheidet
  `MOSAIC_FEATURES_FROM_RUST` ueber den Inhalt der gecachten Planes: gesetzt = frisch gerechnet,
  ungesetzt = Maske aus dem Record.
- Der Schalter steht in KEINEM Schluesselbestandteil (`file_cache_key.py` Z.128-180 fuer den
  Block, `corpus_dataset.py` Z.489-616 fuers Fenster) -- bewusst so (`docs/knobs.md` Z.202), aber
  die Begruendung "beide Bauer sind bit-identisch" gilt auf Alt-Records seit dem 2026-09-12
  nicht mehr.
- Bloecke werden MEMOISIERT, nicht neu gebaut (`build_cache_incremental.py` Z.134-137). Ein Arm
  erbt damit die Semantik dessen, der den Block zuerst gebaut hat, unabhaengig von der eigenen
  Schalterstellung.
- Innerhalb von v29 stand der Schalter uneinheitlich (`grep -c`): `night_v29_b02_b03.sh` Z.25
  setzt ihn auf 1, `night_v29_chain.sh`, `night_v29_b04_moon_played_v2.sh` und
  `night_v29_b06_minimal_core.sh` setzen ihn nicht.
- Das v29-Fenster traegt 1.746 von 2.947 Dateien mit Zeitstempel VOR dem 2026-09-12 (selbst
  gezaehlt gegen `data/window_v29.txt`, Einheit Dateien), darunter die 400 Sockel
  `selfplay_v26-b01-policy_*`.
- Kein Block ist am 2026-09-12, 09-15 oder 09-17 gebaut worden (14.846 Dateien
  `data/.filecache_*.h5`, Zaehlung je Bautag: 09-09 208, 09-10 1.009, 09-11 3.587, 09-13 1.098,
  09-14 5.997, 09-16 2.947). Der b06-Monolith vom 2026-09-17 hat also ausschliesslich
  vorhandene Bloecke zusammengefuegt.
- ABGELEITET, nicht gemessen: die 4.804 Bloecke vom 09-09 bis 09-11 entstanden unter INPUT_SIZE
  755 (par.7) und sind unter dem heutigen 794 (`config.py` Z.49) nicht mehr adressierbar, weil
  `INPUT_SIZE` im Blockschluessel steht.

**Groessenordnung des Effekts:** betroffen sind nur Zustaende aus Records von vor dem
2026-09-12, und dort nur die mit Phantom-Fliesen an genau dieser Schwelle: 2 von 300 Zustaenden
(0,67 Prozent), je 1 Wert von 2.844. Das ist kein Grund, Bloecke zu verwerfen; es ist ein Grund,
die Semantik nicht raten zu muessen.

**Was daraus folgt, als Vorschlag, NICHT umgesetzt (Nutzer-Entscheid):** entweder eine
FORMEL-VERSION in den Schluessel (dann trennen sich alte und neue Semantik sauber, um den Preis
eines Neubaus), oder die gespeicherten Felder `cell_reachable_mask`/`col_f_max` aufgeben und
ueberall frisch rechnen (dann gibt es die Klasse nicht mehr, um den Preis der Rechenzeit je
Zustand), oder par.9s Vorschlag folgen und das Tor auf frische Zustaende beschraenken (dann
bleibt die Klasse bestehen, wird aber nicht mehr gemeldet). Die dritte Variante ist die
billigste und die einzige, die nichts repariert.

## par.9b ENTSCHIEDEN (Nutzer 2026-09-17, "ja mach das"): Weg (1) aus par.9a ist GEBAUT

Der Nutzer hat die erste der drei Varianten aus par.9a gewaehlt: eine FORMEL-VERSION der
Merkmalsberechnung geht in BEIDE Cache-Schluessel, und `MOSAIC_FEATURES_FROM_RUST` wird in
jeder Kette einheitlich gesetzt. Damit raet niemand mehr, welche Semantik in einem Block
oder Monolithen liegt: sie steht im Schluessel.

**Was gebaut ist (Dateien und Zeilen, Stand 2026-09-17):**

- `config.py` Z.65-87: `FEATURE_FORMULA_VERSION = "a2phantom-20260912"`, additiv, mit der
  Regel im Kommentar – wer eine Merkmalsformel aendert, die eine GESPEICHERTE Groesse
  betrifft (heute `cell_reachable_mask`, `col_f_max`), zieht diese Version im selben Zug
  hoch. `INPUT_SIZE` unberuehrt.
- `engine/py/file_cache_key.py` Z.43-68: `_features_from_rust_key()` liest
  `MOSAIC_FEATURES_FROM_RUST` SELBST aus der Umgebung (Muster `_moon_target_source_key()`,
  Semantik wie `neural_net.py` Z.98: exakt "1"). Z.208-221: der Block-Schluessel haengt
  `|featfmt_<VERSION>` und `|featsrc_rust` bzw. `|featsrc_record` UNBEDINGT an.
- `engine/py/corpus_dataset.py` Z.625-648: derselbe Anteil im Fenster-Schluessel
  (`+featfmt_...`, `+featsrc_rust`/`+featsrc_record`), ebenfalls unbedingt.
- `mosaic_env_fingerprint` (`corpus_dataset.py`) brauchte KEINE Aenderung: er erhebt alle
  gesetzten `MOSAIC_*`-Variablen automatisch, `MOSAIC_FEATURES_FROM_RUST` also mit.
- `engine/src/knob_registry.rs` Z.160 (Doku-Text, kein Verhalten) und daraus neu erzeugt
  `docs/knobs.md` Z.202: der Knopf ist nicht mehr als "NICHT im Cache-Schluessel"
  registriert, die alte Begruendung ("beide Bauer bit-identisch") steht mit ihrem
  Verfallsdatum dabei.
- `tools/tests/test_cache_key_feature_formula_version.py` (neu, unittest): Formelversion und
  Merkmalsquelle aendern BEIDE Schluessel, plus die Marker im Schluesselmaterial.
- Ketten: `tools/night_v29_b06_minimal_core.sh` und `tools/night_v29_b04_moon_played_v2.sh`
  setzen `export MOSAIC_FEATURES_FROM_RUST=1` im Kopfblock; die Regel dazu steht in
  `docs/working_rules.md` (Abschnitt "Training und Korpus"). Historische `night_v29_*`-Skripte
  sind unberuehrt.

**Gemessene Folge (Beispielschluessel, Liste `data/selfplay_test-{a_0001,a_0002,b_0001}.pkl`,
Einheit Fenster-Schluessel, Knoepfe auf Default):** `bea417f31e0e` -> `ba128e934a4a`.
Nachgeprueft, dass sich NICHTS ausser den zwei neuen Markern bewegt hat: das
Schluesselmaterial ohne `+featfmt_*+featsrc_record` ergibt exakt den alten Wert. Auf einer
zweiten Liste mit `encoder=2d`, `nortv`: Block `8d676c734796` -> `0ddea578fc5d` (ungesetzt)
bzw. `67d0e8b89c62` (`=1`), Fenster `3d455d48d960` -> `9251bb7d23bc` bzw. `ee6e64631180`.
VORHER waren die beiden Schalterstellungen schluesselgleich – genau der Befund aus par.9a.

**Gewollte Folge, vom Nutzer so entschieden:** alle vorhandenen Bloecke und Monolithe sind
unter den neuen Schluesseln nicht mehr adressierbar. Der Neubau faellt mit dem
INPUT_SIZE-Wechsel fuer den Arm v29-b07 ohnehin an. Der eingefrorene Default-Schluessel in
`tools/tests/test_window_cache_key_planes_ablation.py` ist entsprechend nachgezogen (der
Waechter verlangt dafuer ausdruecklich einen Prereg-Eintrag – das ist dieser hier).

**Was Weg (1) NICHT tut:** er repariert das Paritaets-Tor nicht. Das Tor vergleicht auf
Alt-Records weiter eine gespeicherte gegen eine neu gerechnete Groesse und ist im
Flachvektor fuer dieselbe Klasse blind (par.9a). Wer es fuer eine Abnahme braucht, fahre es
auf FRISCHEN Zustaenden; die Beschraenkung des Tors bleibt der offene Nutzer-Entscheid aus
par.9.
