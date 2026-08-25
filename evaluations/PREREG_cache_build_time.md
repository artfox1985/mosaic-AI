<!-- STATUS: OFFEN | Frage: Der Cache-Bau des Trainings dauert rund 70 min fuer 890.000 Zustaende und liegt damit vor JEDER Trainingsfrage. Welche Hebel verkuerzen ihn -- und bleibt der Cache dabei BIT-IDENTISCH? | Beleg: NICHTS GEBAUT, angelegt 2026-08-25 auf Nutzer-Auftrag, Start unmittelbar nach dem Ende der v22-Erzeugung. Gemessen am hv2-Korpus: state_to_planes 1,896 ms je Zustand (85 Prozent der Merkmalskosten), state_to_tensor 0,185 ms, Unpickle 0,150 ms; Summe 2,23 ms = 33 min der beobachteten ~70. DREI HEBEL, absteigend nach erwartetem Nutzen: (1) PARALLELISIERUNG des Bau-Laufs -- neural_net.py enthaelt kein Pool/multiprocessing, die Dateien laufen nacheinander bei ~0,75 Kernen, obwohl sie unabhaengig sind; trifft die GANZE Schleife, nicht nur die Merkmale. (2) RUST-EXPORT der Bauer (features.rs hat sie, pyo3 exportiert sie nicht) -- trifft 85 Prozent von 33 der 70 min, also bestenfalls die halbe Wanduhr. (3) lzf-Kompression pruefen (115,9 MB Feldinhalt -> 7,6 MB Datei, Faktor 15). EIN GEMEINSAMES HARTES TOR fuer alle drei: BIT-IDENTITAET des erzeugten Caches gegen den heutigen Stand. Ein schnellerer, aber anderer Cache entwertet jeden Vergleich mit bestehenden Modellen; faellt die Identitaet und ist die Abweichung nicht behebbar, stirbt der jeweilige Hebel. Reihenfolge (1) vor (2) ist eine Umpriorisierung gegenueber dem ersten Entwurf, in par.5 begruendet. GPU GEPRUEFT UND VERWORFEN (par.5a, Nutzer-Frage): der Bauer ist Umpacken statt Arithmetik, verzweigungslastig, und die Daten liegen als Python-Objekte im Host-RAM -- sie dorthin zu bringen IST die Arbeit. Ob (2) nach (1) noch lohnt, entscheidet eine NEUE Messung des Merkmalsanteils, nicht das Bauchgefuehl (par.5b). -->

# Vorregistrierung: Zeit des Cache-Baus

**Angelegt 2026-08-25**, nichts gebaut. Nutzer-Auftrag: **Start unmittelbar
nach dem Ende der v22-Erzeugung**, Nutzer-Freigabe *"alles was uns hier zeit
spart hilft"*.

## par.1 Warum das kein Nebenschauplatz ist

Der Cache-Bau liegt **vor jeder Trainingsfrage**. Am 2026-08-25 hat genau er
die Entscheidung erzwungen, den Traeger-A/B als Richtungstest auf einem
Viertelkorpus zu fahren statt voll -- nicht weil die Frage klein war, sondern
weil zweimal 5 Stunden Vorlauf nicht in die Nacht passten.

**Nutzniesser benannt** (Infrastruktur-Regel verlangt das):

* jedes v22- und v23-Training;
* **jeder Traeger-Arm doppelt**, weil
  `MOSAIC_IGNORE_POLICY_TARGET_VALID` im Cache-Schluessel steht;
* jeder Fenster-Zuschnitt-Versuch, aus demselben Grund.

## par.2 Wo die Zeit hingeht (gemessen 2026-08-25, 400 Zustaende aus hv2)

| Posten | je Zustand | Anteil der Merkmalszeit |
| --- | --- | --- |
| `state_to_planes` | **1,896 ms** | **85 %** |
| `state_to_tensor` | 0,185 ms | 8 % |
| Unpickle | 0,150 ms | 7 % |
| Summe | **2,23 ms** | |

2,23 ms x 890.000 Zustaende = **33 min**. Beobachtet wurden **~70 min**. Die
Differenz ist die uebrige Record-Schleife (Policy-Vektor, Ownership, Ranking,
Bitpacking, numpy-Aufbau) plus das lzf-komprimierte HDF5-Schreiben, gemessen
unter Last mit `OMP_NUM_THREADS=2`.

**Diese Aufteilung bestimmt die Reihenfolge der Hebel** -- ein Hebel, der nur
die Merkmale trifft, kann hoechstens die halbe Wanduhr holen.

## par.3 Die drei Hebel

### (1) Parallelisierung -- erwartet der groesste

`neural_net.py` enthaelt **kein** `Pool`, kein `multiprocessing`; die Dateien
werden nacheinander abgearbeitet, gemessen bei rund 0,75 Kernen. Sie sind
**unabhaengig**: jede erzeugt ihren eigenen Array-Block, am Ende wird
konkateniert.

* Trifft die **ganze** Schleife, nicht nur die Merkmale.
* **Kein Paritaetsrisiko in der Rechnung** -- derselbe Code, nur in mehreren
  Prozessen.
* Zu beachten: deterministische Reihenfolge beim Zusammenfuegen (nach
  Dateinamen sortiert), und Speicher -- N Prozesse halten N Teilbloecke.
* **Der Aufwand steckt im Zuschnitt**, nicht in der Idee: der Schleifenkoerper
  muss in eine picklebare Top-Level-Funktion, und das ist ein Eingriff in den
  kritischsten Datenpfad des Projekts. Genau dafuer ist das Tor in par.4 da.

### (2) Rust-Export der Merkmalsbauer

`state_to_tensor` (neural_net.py:39) und `state_to_planes` (:380) sind reines
Python; `engine/src/features.rs` hat dieselben Bauer -- sie wurden am
2026-08-25 sogar gemeinsam erweitert (`INPUT_SIZE` 708 -> 714,
`NUM_PLANES_CHANNELS` 76 -> 77). Nach Python exportiert sind sie nicht,
`dir(mosaic_rust)` kennt keinen Merkmals-Einstieg.

* **Nur der Export**, kein Umbau: beide Fassungen bleiben, die Python-Fassung
  wird zur Referenz der Paritaetspruefung.
* **Opt-in**, nicht Default -- Bestandslaeufe unveraendert, Umstellung
  rueckholbar.
* **Der Schalter gehoert NICHT in den Cache-Schluessel.** Das ist der Test:
  sind beide bit-identisch, MUSS derselbe Schluessel herauskommen, sonst
  waeren bestehende Caches wertlos.
* Es gibt bereits eine Paritaets-Maschinerie (`engine/tests/fixtures`,
  Regenerator hinter `MOSAIC_UPDATE_FEATURE_FIXTURE=1`); sie prueft heute die
  Rust-Seite gegen eine eingefrorene Erwartung, hier kaeme die Kreuzpruefung
  Rust-gegen-Python dazu.

### (3) lzf-Kompression pruefen -- klein, aber billig zu messen

Der Schnappschuss-Cache: 115,9 MB Feldinhalt -> **7,6 MB Datei**, Faktor 15.
So viel Kompression kostet Schreib-CPU. `compression=None` waere schneller,
kostet aber Platte: bei 4,18 Mio Zustaenden grob 11 GB statt 0,8. Eine
Messung von zehn Minuten, kein Umbau.

## par.4 DAS GEMEINSAME TOR: Bit-Identitaet

**Fuer alle drei Hebel gilt dasselbe Kriterium, und es ist nicht
"schneller".** Ein Cache, der schneller entsteht, aber andere Zahlen enthaelt,
entwertet jeden Vergleich mit bestehenden Modellen und jede Messung, die auf
ihnen aufbaut.

Zu pruefen, in dieser Reihenfolge:

1. **Feld fuer Feld bit-identisch** gegen den heutigen Stand auf demselben
   Korpusausschnitt -- `states`, `planes_packed`, `masks_packed`,
   `policies`, `policy_weights`, `ownership`. Nicht "innerhalb Toleranz":
   die Felder sind uint8-gepackt bzw. float16, Gleichheit ist exakt pruefbar.
2. **Dieselbe Pruefung auf Sonderfaellen**: leeres Brett, Runde 5, gesetzte
   Startkuppel, gefuelltes Spezialfeld, Record mit
   `policy_target_valid=false`.
3. Erst danach die Zeitmessung, mit `laufzeit`-Block ins Artefakt.

**Kill-Kriterium je Hebel:** stellt sich Bit-Identitaet nicht her und laesst
sich die Abweichung nicht auf einen behebbaren Unterschied zurueckfuehren,
**stirbt dieser Hebel**. Ein "fast gleicher" Cache ist schlechter als ein
langsamer.

## par.5 Reihenfolge -- und warum sie gegenueber dem ersten Entwurf getauscht ist

Der erste Entwurf dieser Prereg (2026-08-25, gleicher Tag) fuehrte den
Rust-Export als Hauptsache. **Das war falsch priorisiert**, und die eigene
Messung in par.2 zeigt es: der Export trifft 85 Prozent von 33 der 70
Minuten, also hoechstens die halbe Wanduhr. Die Parallelisierung trifft alles
-- und sie ist billiger zu bauen, weil sie die Rechnung nicht anfasst.

Reihenfolge damit: **(1), dann (3) als Beifang derselben Messung, dann (2).**

**Erwartung vorab benannt, damit sie nicht hinterher passend gemacht wird:**
(1) skaliert nicht linear -- Prozessstart, Serialisierung der Teilbloecke und
das serielle HDF5-Schreiben bleiben. Realistisch ist ein Faktor 4-6 auf 12
Kernen, nicht 12. (2) bringt danach nochmal einen kleineren Anteil, weil (1)
seinen Gewinn schon mitgenommen hat. Wer nach beiden eine Zehnfach-Wanduhr
erwartet, wird enttaeuscht sein.

## par.5a GPU: geprueft und verworfen (Nutzer-Frage 2026-08-25)

Nutzer: *"koennen wir das auch ueber die gpu machen? die schlaeft die meiste
zeit"*. Die Beobachtung stimmt, der Schluss traegt hier aber nicht.

`state_to_planes` (neural_net.py:380ff) besteht aus Dict-Zugriffen,
Set-Mitgliedschaft, Verzweigungen und Schleifen ueber einzelne Zellen -- 11
Schleifen-/Verzweigungszeilen allein in den ersten 48. Es ist **Umpacken,
keine Arithmetik**. Drei Gruende:

1. Die Daten liegen als Python-Objekte im Host-RAM. Um sie auf die GPU zu
   bekommen, muesste man sie erst in Tensoren kodieren -- und das IST die
   Arbeit.
2. Verzweigungslastig und winzig je Element; eine GPU ist eine
   Durchsatzmaschine fuer gleichfoermige Rechnung.
3. Die vielen kleinen `torch.zeros`/`cat`-Aufrufe wuerden je ein Kernel-Start
   (~10 us Overhead). Bei 77 Kanaelen a 36 Zellen waere das auf der GPU
   vermutlich LANGSAMER als auf der CPU.

**Was an der Beobachtung dennoch stimmt:** die GPU schlaeft, weil der Engpass
im CPU-seitigen Datenpfad sitzt. Die Antwort ist, diesen Pfad schneller zu
machen (Hebel 1 und 2), nicht ihn zu verschieben. Auch Pipelining -- Cache-Bau
gegen erste Epochen ueberlappen -- hilft wenig, solange der Bau 3,5-mal so
lang dauert wie das Training: das Training wuerde verhungern.

## par.5b Entscheidungsregel fuer Hebel (2), nach der Messung von (1)

Nutzer-Frage: bleibt der Rust-Export nach der Parallelisierung relevant?
**Nicht obsolet -- die Hebel multiplizieren sich -- aber der absolute Gewinn
schrumpft:**

| Stand | Wanduhr | davon Merkmale |
| --- | --- | --- |
| heute | 70 min | 33 |
| nach (1), Faktor 5 angenommen | ~14 min | ~7 |
| zusaetzlich mit (2) | ~8 min | ~1 |

Die Tabelle ist eine HOCHRECHNUNG auf dem gemessenen Anteil, keine Messung.

**Regel, vorab festgelegt:** nach (1) wird der Merkmalsanteil an der neuen
Wanduhr ERNEUT gemessen. Ist er weiterhin der dominante Posten, wird (2)
gebaut. Wird der Rest von HDF5-Schreiben und Record-Schleife dominiert, ist
(2) die Paritaets-Pruefung nicht wert und entfaellt -- ein Nullbefund, kein
Fehlschlag.

## par.6 Der strukturelle Hebel, bewusst NICHT in diesem Zuschnitt

Der Cache-Schluessel haengt an der **gesamten Dateiliste**. Jede Aenderung --
ein Traeger-Arm, ein anderer Fensterzuschnitt, eine neue Datei -- baut alles
neu. Ein Cache **je Datei** plus billiger Merge wuerde jeden Folgelauf fast
umsonst machen: nur neue Dateien kosten.

Das ist der einzige Ansatz, der das Problem **abschafft** statt es zu
verkleinern -- und zugleich der invasivste (die pro-Datei-Groessen wie
`value_target_variant` muessten in den Datei-Schluessel). **Nicht Teil dieses
Zuschnitts**, aber hier festgehalten, damit er nicht vergessen wird, falls
sich die Kampagne als wiederholungslastig erweist.
