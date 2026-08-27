<!-- STATUS: OFFEN | Frage: Der Cache-Bau des Trainings dauert rund 70 min fuer 890.000 Zustaende (AUSGANGSZAHL, ueberhoeht -- par.7 weist sie selbst zurueck: sie wurde unter Nebenlast und mit OMP_NUM_THREADS=2 beobachtet; der belastbare serielle Wert sind 2,22 ms je Zustand, also ~33 min fuer dieselben 890.000) und liegt damit vor JEDER Trainingsfrage. Welche Hebel verkuerzen ihn -- und bleibt der Cache dabei BIT-IDENTISCH? | Beleg: NICHTS GEBAUT, angelegt 2026-08-25 auf Nutzer-Auftrag, Start unmittelbar nach dem Ende der v22-Erzeugung. Gemessen am hv2-Korpus: state_to_planes 1,896 ms je Zustand (85 Prozent der Merkmalskosten), state_to_tensor 0,185 ms, Unpickle 0,150 ms; Summe 2,23 ms = 33 min der beobachteten ~70. DREI HEBEL, absteigend nach erwartetem Nutzen: (1) PARALLELISIERUNG des Bau-Laufs -- neural_net.py enthaelt kein Pool/multiprocessing, die Dateien laufen nacheinander bei ~0,75 Kernen, obwohl sie unabhaengig sind; trifft die GANZE Schleife, nicht nur die Merkmale. (2) RUST-EXPORT der Bauer (features.rs hat sie, pyo3 exportiert sie nicht) -- trifft 85 Prozent von 33 der 70 min, also bestenfalls die halbe Wanduhr. (3) lzf-Kompression pruefen (115,9 MB Feldinhalt -> 7,6 MB Datei, Faktor 15). EIN GEMEINSAMES HARTES TOR fuer alle drei: BIT-IDENTITAET des erzeugten Caches gegen den heutigen Stand. Ein schnellerer, aber anderer Cache entwertet jeden Vergleich mit bestehenden Modellen; faellt die Identitaet und ist die Abweichung nicht behebbar, stirbt der jeweilige Hebel. HEBEL (1) GEBAUT UND ABGENOMMEN 2026-08-26 (par.7): 120 Dateien / 209.057 Zustaende, seriell 463,6 s gegen parallel 93,0 s = **Faktor 4,99**, und das TOR IST BESTANDEN -- alle 21 Felder bit-identisch. Zuschnitt ohne Eingriff in die Bauschleife: die Worker bauen Datei-Teilmengen mit dem Bestandscode und geben nur ihren Cache-Pfad zurueck. Einzige Aenderung an neural_net.py ist eine Zuweisung. Hochrechnung voller Korpus: seriell ~2,6 h, parallel ~31 min. Die vorab benannte Erwartung (Faktor 4-6) hat gehalten. VOLLER KORPUS GEFAHREN 2026-08-26 (par.8): 4.186.112 Zustaende in 36,1 min gegen 2,58 h seriell hochgerechnet, Faktor ~4,3; Cache 0,83 GB auf Platte, 2.811 Byte je Zustand. Dabei ZWEI Zuschnittfehler gefunden und behoben -- Blockzahl war an die Workerzahl gekoppelt (10 Bloecke ergaben 24,1 GB belegt und 0,7 GB frei, abgebrochen), und das Zusammenfuegen hielt ein Feld doppelt im RAM. Nach der Korrektur 3,9 GB. ACHTUNG: fuer den vollen Korpus ist das TOR NICHT gefahren (keine serielle Referenz); belegt ist Bit-Identitaet auf 120 Dateien. NICHT verdrahtet in train.py. Reihenfolge (1) vor (2), in par.5 begruendet. HEBEL (4) GEBAUT UND ABGENOMMEN 2026-08-26 (par.9): Cache JE DATEI, BEIDE Pflichtpruefungen bestanden -- 21/21 Felder bit-identisch gegen die serielle Referenz (120 Dateien), und jeder der sieben per-Datei-Parameter erzeugt einen MISS (file_cache_key_probe.py). Die Schluesselteilung ist ADDITIV: der Fenster-Schluessel bleibt Zeichen fuer Zeichen, der Datei-Block bekommt einen eigenen Namensraum (per_file_cache_key) mit dem AUFGELOESTEN Traegerstatus der Datei statt des Manifest-Inhalts -- kein Bestands-Cache verfaellt. Beleg fuer den Gewinn: 119 von 120 Bloecken wurden ueber ein ANDERES Fenster hinweg wiederverwendet (7,9 s statt Neubau). Kosten 0,96 s je Datei bei 6 Workern; der Lauf kann per --watch WAEHREND der Erzeugung mitlaufen. NEBENBEFUND, live und behoben: MOSAIC_CACHE_F32 stand in KEINER Key-Komponente, obwohl der Knopf den gespeicherten dtype aendert -- der Notausstieg war wirkungslos, sobald ein Cache existierte. GPU GEPRUEFT UND VERWORFEN (par.5a, Nutzer-Frage): der Bauer ist Umpacken statt Arithmetik, verzweigungslastig, und die Daten liegen als Python-Objekte im Host-RAM -- sie dorthin zu bringen IST die Arbeit. Ob (2) nach (1) noch lohnt, entscheidet eine NEUE Messung des Merkmalsanteils, nicht das Bauchgefuehl (par.5b). -->

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

## par.6 Hebel (4): Cache JE DATEI -- derselbe Umbau, eigene Auslieferung

Nutzer-Frage 2026-08-25: *"das dann noch zusaetzlich oder seperat?"* --
**zusaetzlich, und zwar auf demselben Umbau.**

Um zu parallelisieren, muss der Schleifenkoerper ohnehin in eine picklebare
Top-Level-Funktion `bau_eine_datei(pfad) -> Arrays`. Genau die braucht der
Datei-Cache auch: er ist die **Memoisierung derselben Funktion**.

```
bau_eine_datei(pfad) -> Arrays
   |-- Pool darueber        = Hebel (1), Parallelisierung
   +-- Memoisierung darauf  = Hebel (4), Cache je Datei
```

Wer beides nacheinander baut, macht den teuren Teil zweimal.

**Getrennt ausliefern, in dieser Reihenfolge -- das Risiko ist sehr ungleich
verteilt:**

* **(1) ist risikoarm.** Kein Schluessel aendert sich, der monolithische Cache
  bleibt, er entsteht nur in mehreren Prozessen. Bit-Identitaet ist die
  einzige Pruefung.
* **(4) verlangt eine SCHLUESSELTEILUNG**, und die ist die heikle Stelle.
  Heute deckt ein Schluessel alles ab; kuenftig muesste getrennt werden in
  * **je Datei**: `value_target_variant`, `encoder`, `conjunction_head`,
    Bitpacking, `ignore_ptv`, Sharpen-Exponent -- **und der
    Policy-Traeger-Status der Datei**, der pro Datei ausgewertet wird;
  * **je Fenster**: welche Dateien, Traeger-Manifest, Train/Val-Split.

  Wird das falsch geteilt, zieht ein Lauf STILL einen veralteten Datei-Cache
  -- genau die Falle, vor der die Schluessel-Kommentare in `neural_net.py` an
  mehreren Stellen warnen (*"ohne diesen String im Key wuerden
  nortv/nortv_r1 stillschweigend den default-Cache wiederverwenden"*).
  Scheitert (4), bleibt (1) trotzdem stehen.

**Der eigentliche Gewinn von (4) ist nicht die Wanduhr, sondern der kritische
Pfad.** Ein Datei-Cache kann **waehrend der Erzeugung** mitlaufen: jede fertige
`.pkl` bekommt sofort ihren Block. Ist der Korpus fertig, ist der Cache es
auch -- die Bauzeit verschwindet nicht nur, sie liegt gar nicht mehr vor dem
Training. Das ist der Unterschied zwischen "schneller" und "nicht mehr da",
und er ist groesser als alles, was (1) bis (3) zusammen holen koennen.

**Gleiches Tor wie alle anderen Hebel:** Bit-Identitaet (par.4). Fuer (4)
kommt eine zweite Pflichtpruefung dazu -- ein absichtlich veraenderter
per-Datei-Parameter MUSS einen Cache-Miss erzeugen. Ein Test, der nur zeigt,
dass gleiche Eingaben denselben Cache treffen, prueft die falsche Haelfte.


## par.7 HEBEL (1) GEBAUT UND ABGENOMMEN (2026-08-26)

**Zuschnitt ohne Eingriff in die 500-Zeilen-Bauschleife.** `MosaicDataset`
nimmt bereits eine explizite Dateiliste; die Worker bauen je eine
ZUSAMMENHAENGENDE Teilmenge mit dem UNVERAENDERTEN Bestandscode und geben nur
ihren Cache-Pfad zurueck. Der Elternprozess liest die Teil-Caches von der
Platte und fuegt feldweise zusammen. Arrays durch die Prozess-Pipe zu schicken
waere beim vollen Korpus ueber 11 GB.

Einzige Aenderung an `neural_net.py`: `self.cache_path_h5 = cache_path_h5` --
eine Zuweisung, kein Kontrollfluss.

**Messung, 120 Dateien / 209.057 Zustaende, encoder=2d, 10 Worker:**

| | Wanduhr | je Zustand |
| --- | --- | --- |
| seriell (Bestandsweg) | **463,6 s** | 2,22 ms |
| parallel (Teil-Bau) | 90,6 s | |
| parallel (Zusammenfuegen) | 2,4 s | |
| **parallel gesamt** | **93,0 s** | |
| **Beschleunigung** | **4,99x** | |

Die 2,22 ms je Zustand decken sich mit der Einzelmessung aus par.2 (2,23 ms)
-- die Vorhersage traegt.

**DAS TOR IST BESTANDEN: bit-identisch.** `cache_parity_probe.py` vergleicht
alle 21 Felder mit `np.array_equal`, keine Toleranz: identisch. Damit ist der
Hebel nicht nur schneller, sondern folgenlos fuer jeden Vergleich mit
bestehenden Modellen.

**Hochrechnung auf den vollen Korpus** (Herleitung aus dieser Messung, nicht
gemessen): 2.400 Dateien = 4,18 Mio Zustaende, also seriell rund **2,6 h**,
parallel rund **31 min**. Die frueher genannten "~5,5 h" waren zu hoch -- sie
stammten aus dem 70-Minuten-Beobachtungswert fuer 513 Dateien, der unter Last
und mit `OMP_NUM_THREADS=2` zustande kam.

**Die vorab benannte Erwartung aus par.5 war "Faktor 4-6, nicht 12".**
Gemessen 4,99 -- die Erwartung hat gehalten, und sie stand vor der Messung da.

**Nebeneffekt wie vorhergesagt:** die zehn Teil-Caches bleiben in `data/`
liegen. Ein zweiter Lauf mit derselben Blockteilung trifft sie -- der
Datei-Cache aus Hebel (4) in grober Form, ohne dessen Schluesselteilung.
Aufraeumbedarf: die `.cache_*.h5`-Dateien sind dot-praefigiert und fallen
nicht in den `*.pkl`-Glob.

**Was NICHT gemacht ist:** die Verdrahtung in `train.py`. Der parallele Bau
ist heute ein eigenstaendiges Werkzeug; das Training nutzt weiter den
seriellen Weg. Das ist Absicht -- erst soll der Hebel auf dem vollen Korpus
laufen und wieder das Tor bestehen.


## par.8 VOLLER KORPUS (2026-08-26) -- und ein Speicher-Vorfall, der den Zuschnitt korrigiert hat

**Erster Versuch: abgebrochen wegen RAM.** Mit 10 Bloecken auf 2.400 Dateien
hielt jeder Worker ein Zehntel des Korpus im Zwischenformat. Gemessen: 12
Prozesse, 24,1 GB belegt, **0,7 GB frei von 31,9**. Abgebrochen, bevor das
System zu tauschen begann.

**Die Ursache war ein Zuschnittfehler, nicht die Idee:** die erste Fassung
koppelte die Blockzahl an die Workerzahl. Das Zwischenformat kostet rund 7 KB
je Zustand (nicht die 2,8 KB des fertigen Caches), also skaliert der Bedarf
mit `Worker x Zustaende_je_Block`. Behoben: `--blocks` ist jetzt von
`--workers` getrennt, Default rund 100.000 Zustaende je Block. Wer mehr Worker
will, bekommt mehr Gleichzeitigkeit, nicht groessere Bloecke.

**Zweiter Zuschnittfehler, gleich mitbehoben:** das Zusammenfuegen las alle
Bloecke eines Feldes ein und konkatenierte -- also das Feld doppelt im RAM
(6 GB Bloecke plus 6 GB Ergebnis fuer `states`). Jetzt wird das Zielfeld mit
seiner Endform angelegt und Block fuer Block in seinen Schnitt geschrieben.

**Nach der Korrektur: 3,9 GB statt 24,1**, 21,6 GB frei.

**Ergebnis, 2.400 Dateien / 4.186.112 Zustaende, 42 Bloecke, 6 gleichzeitig:**

| | Wert |
| --- | --- |
| Teil-Bau | 2.106,3 s |
| Zusammenfuegen | 58,3 s |
| **gesamt** | **2.164,7 s = 36,1 min** |
| seriell hochgerechnet (4,186 Mio x 2,22 ms) | **2,58 h** |
| **Beschleunigung** | **~4,3x** |
| Cache auf Platte | 0,83 GB (lzf) |
| Felder unkomprimiert | 11,77 GB = **2.811 Byte je Zustand** |

Die 2.811 Byte bestaetigen die Rechnung aus `PREREG_v23_window.md` par.3(2)
(2.806 geschaetzt; Verweis BERICHTIGT 2026-08-27 -- er stand als reiner
Eigenverweis "par.3(2)" da, und par.3 DIESER Datei sind die drei Hebel) und
damit auch, dass das Trainingsfenster bequem ins RAM passt.

**WICHTIG -- was hier NICHT belegt ist:** fuer den vollen Korpus gibt es
KEINE serielle Referenz, das Tor ist hier also nicht gefahren. Belegt ist die
Bit-Identitaet auf 120 Dateien (par.7), zusaetzlich fuer den geaenderten,
streamenden Merge in beide Richtungen (gegen die serielle Referenz UND gegen
den alten Merge). Wer den vollen Cache fuer eine Champion-Entscheidung
benutzt, sollte die 2,58 h Referenz einmal fahren.

**Nebenbefund:** in `data/` liegen jetzt 57 Block-Caches mit zusammen 1,2 GB.
Sie sind dot-praefigiert und fallen nicht in den `*.pkl`-Glob; ein zweiter
Lauf mit denselben Blockgrenzen trifft sie. Nicht aufgeraeumt -- Loeschen ist
ein Nutzer-Entscheid.


## par.9 HEBEL (4) GEBAUT UND ABGENOMMEN (2026-08-26)

**Die Schluesselteilung ist ADDITIV geloest, nicht durch Umbau des
Bestandsschluessels.** par.6 nennt sie die heikle Stelle, und der naheliegende
Weg -- den vorhandenen Schluessel in "je Datei" und "je Fenster" zerlegen --
haette JEDEN Bestands-Cache entwertet: den 14-GB-Vollcache, `.par_full.h5` und
`.ref_serial.h5` inbegriffen, zusammen ueber zwei Stunden Rechenzeit. Statt
dessen bleibt der Fenster-Schluessel Zeichen fuer Zeichen unveraendert, und
der Datei-Block bekommt einen EIGENEN Namensraum: `per_file_cache_key`
(`neural_net.py`), Praefix `filecache_v1`, Dateien `.filecache_<key>.h5`.

**Was drin steht und was bewusst nicht:**

| | im Datei-Schluessel | warum |
| --- | --- | --- |
| Schema/Aktionen/Sharpen/TD_LAMBDA | ja | bestimmen den Blockinhalt |
| Encoder, Value-Ziel-Variante | ja | dito |
| Konjunktion/Reachability, Bitpacking | ja | dito |
| `ignore_ptv`, `f32` | ja | dito, beide aendern gespeicherte Werte |
| **aufgeloester Traegerstatus DIESER Datei** | **ja** | das Manifest wirkt pro Datei; zwei Manifeste mit gleichem Ergebnis fuer diese Datei duerfen denselben Block teilen |
| Manifest-INHALT, Dateiliste, Train/Val-Split | **nein** | genau daran haengt heute jeder Block unnoetig mit |

Der Traegerstatus wird mit `_is_policy_carrier` gebildet, also mit derselben
Funktion wie in der Bauschleife, und `bootstrap_native` aus derselben
Praefix-Konstante. Ein Nachbau haette genau die Drift erzeugt, gegen die die
zweite Pflichtpruefung gerichtet ist.

### Beide Pflichtpruefungen bestanden

**(a) Bit-Identitaet.** `cache_parity_probe.py data/.ref_serial.h5
data/.inc_window_ref120.h5`: 21 von 21 Feldern bit-identisch, `np.array_equal`,
keine Toleranz. Verglichen wurde gegen die BESTEHENDE serielle Referenz aus
par.7, nicht gegen einen neu gebauten Massstab.

**(b) MISS je Parameter** (`tools/probes/file_cache_key_probe.py`, netzfrei,
Sekunden): alle sieben per-Datei-Parameter erzeugen einen anderen Schluessel --
`value_target_variant`, `encoder`, `conjunction_head`, Traegerstatus,
`MOSAIC_CACHE_NOPACK`, `MOSAIC_CACHE_F32`, `MOSAIC_IGNORE_POLICY_TARGET_VALID`.
Dazu die beiden Gegenproben, ohne die (b) trivial bestuende: derselbe Aufruf
ergibt denselben Schluessel, eine andere Datei einen anderen.

Die Sonde laedt das Modul je Fall NEU. Das ist Pflicht, nicht Kosmetik:
`_IGNORE_PTV` wird einmal beim Import gelesen; wer den Knopf setzt und
dieselbe Modulinstanz befragt, misst den alten Wert und bekommt einen falschen
GRUENEN Befund.

### Der Gewinn, gemessen statt behauptet

Die erste Paritaets-Fahrt fiel durch -- mit Formunterschied, nicht
Inhaltsunterschied: 210.777 gegen 209.057 Zustaende. Ursache war die
Dateimenge, nicht der Bau: seit der Referenz liegt `probe_v2huelle_horizon.pkl`
in `data/`, sortiert sich vor alles und verdraengte die 120. Korpusdatei.
Nach `MOSAIC_DATA_EXCLUDE=^probe_` waren **119 der 120 Bloecke bereits da**;
gebaut werden musste genau einer, und der hatte die vorhergesagten 1.724
Zustaende (209.057 - 207.333).

**Vermerk 2026-08-27: der Ausschluss `^probe_` ist GEGENSTANDSLOS geworden.**
`data/probe_v2huelle_horizon.pkl` existiert nicht mehr; `data/` enthaelt
2.400 pkl = 24.000 Partien. Der Absatz bleibt als Herleitung des
Form-Unterschieds stehen, als Auflage fuer kuenftige Laeufe gilt er nicht.

Das ist zugleich der Beleg fuer den eigentlichen Gewinn: **Bloecke ueberleben
den Fensterwechsel.** Ein anderes Fenster kostete 7,9 s statt eines Neubaus.

| | Wanduhr | Bemerkung |
| --- | --- | --- |
| 120 Dateien, 117 Bloecke neu, 6 Worker | 112,6 s | 0,96 s je Datei |
| davon Zusammenfuegen | 4,2 s | |
| dieselben 120 Dateien, anderes Fenster | 7,9 s | 119 Bloecke wiederverwendet |
| Gegenprobe Memoisierung (3 Dateien, alle da) | 2,0 s | 0 neu gebaut |

**Was das NICHT heisst:** eine Beschleunigung gegen Hebel (1). Auf dem vollen
Korpus laege der Erstbau in derselben Groessenordnung wie die 36,1 min aus
par.8 -- der Gewinn liegt woanders, und par.6 hat ihn vorab benannt: der Bau
kann per `--watch` WAEHREND der Erzeugung mitlaufen, dann liegt er nicht mehr
vor dem Training. Fuer den vollen Korpus ist das Tor weiterhin NICHT gefahren
(es fehlt die serielle Referenz, 2,58 h) -- belegt ist Bit-Identitaet auf 120
Dateien, wie bei Hebel (1).

### Nebenbefund, live und behoben: MOSAIC_CACHE_F32 war wirkungslos

Beim Aufzaehlen der per-Datei-Parameter fiel auf, dass `MOSAIC_CACHE_F32` in
KEINER Key-Komponente stand, obwohl der Knopf den gespeicherten dtype von
`states`/`policies` auf float32 hebt und der Kommentar an der Schreibstelle
selbst "NICHT bit-identisch" sagt. Folge: ein Lauf mit dem Notausstieg traf
den vorhandenen float16-Cache, und der Knopf blieb still ohne Wirkung -- genau
die Fehlerklasse, gegen die `+nopack_v1` und `+ignore_ptv_v1` gebaut wurden.

Behoben mit `+f32_v1`, nach demselben Muster NUR bei gesetztem Knopf
angehaengt: der Default-Schluessel bleibt unveraendert, kein Bestands-Cache
verfaellt. Schreibweg und Schluessel lesen den Knopf jetzt durch dieselbe
Funktion (`_cache_f32_active`).

**Nicht verdrahtet in `train.py`** -- wie bei Hebel (1) Absicht: das Werkzeug
steht fuer sich, bis es auf dem vollen Korpus gelaufen ist.
