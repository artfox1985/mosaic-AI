<!-- STATUS: OFFEN | Frage: Wird die Python/Rust-Naht an der Datenschicht konsolidiert -- Merkmalsbauer als EINE Wahrheit in Rust (Teil A) und ein von Rust geschriebenes, spaltenorientiertes Rohformat (Teil B)? | Beleg: NICHTS GEBAUT, angelegt 2026-08-28 auf Nutzer-Frage nach dem idealen Python/Rust-Setup. Die Sprachaufteilung selbst ist gemessen richtig und steht nicht zur Debatte (GPU-Wege geschlossen: bester Weg 1,255x gegen Tor 2,0x, PREREG_gpu_inference_path.md; tract schlug die FLOP-Rechnung zweimal). Teuer ist die GRENZE: jede Eingabe-Erweiterung ist heute ein Dreifachbau -- Rust-Direct-Pfad, Python-Zwilling, Paritaetstests; der 77->79-Kanalbau vom 2026-08-27 (e91cd34) war exakt das. Und die Drift-Fehlerklasse ist real: dort haette das Bitpacking die wertetragenden Kanaele still auf 0/1 kollabiert, gefangen nur vom Neubau-Kontext. TEIL A (par.2) ist der UMZUG von Hebel 2 aus PREREG_cache_build_time.md: features.rs-Bauer per pyo3 exportieren, Rust wird einzige Wahrheit, der Python-Zwilling (neural_net.py state_to_planes:405 / _board_channels:372 / state_to_tensor:45) degradiert zum Test-Orakel oder entfaellt. Die dortige VORBEDINGUNG wandert MIT (par.5b der Quell-Prereg): der Merkmalsanteil wird NEU gemessen, bevor gebaut wird -- die alten 85 Prozent von 33 min gelten fuer den seriellen Stand vor Hebel 1 und 4. HARTES TOR unveraendert: BIT-IDENTITAET des Caches gegen den Python-Bauer VOR der Umstellung, plus Paritaets-Hash und Suite. TEIL B (par.3): spaltenorientiertes Rohformat, von Rust geschrieben, statt gzip-Pickle von Python-Dicts (Faktor 35,4 Kompression zeigt die Redundanz, STATUS.md; Unpickle 0,150 ms je Zustand, PREREG_cache_build_time.md par.2). PFLICHT dabei: das Format speichert ROHE Zustaende verlustfrei, nicht Merkmale -- beim INPUT_SIZE-Wechsel 708->714 erlaubten NUR die pkl den Neubau. AUSLOESE-BEDINGUNGEN (par.4, Nutzer-Formulierung 2026-08-28): "Kein akuter Posten -- erst, wenn wieder eine Messung an der Ladezeit haengt." Teil B startet bei benannter Messung mit Lade-/Parse-Anteil ueber 25 Prozent der Wanduhr (im Artefakt belegt) oder als Beifang von Teil A; Teil A fruehestens NACH dem v22-Zyklus und nur nach der Neumessung. Bis dahin ist dies eine REGISTRIERUNG, kein Arbeitsauftrag. Erfolg wird in IRRTUMSKOSTEN gemessen (frueher erkennbare Drift, kuerzere Bauzeiten), nicht in Elo. -->

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
