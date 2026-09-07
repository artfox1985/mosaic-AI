<!-- STATUS: ENTSCHIEDEN | Frage: Re-Validierung von Floor-Gewicht, m-Formel und τ-Annealing in der WDL-Aera (3 Messungen) | Beleg: alle 3 Messungen H0, Status quo bestaetigt (Abschnitt "MESSUNG-3-ERGEBNIS"; tau-Annealing 112:118, p 0,78, v20-Aera, Mass war STAERKE). NACHTRAG 2026-09-07: Vorstufe 3-V GEFAHREN -- das Sampling der Zugwahl kostet dem Sockel mehr als die HAELFTE seines Spaltenbaus (0,195 gegen 0,4225 bei argmax ab Halbzug 12) und liefert dafuer praktisch keine Vielfalt (399 von 400 Endbrettern distinkt in beiden Faellen). Die 0,19 der Sockel-Klasse sind ein Temperatur-Artefakt. Arena-Wirkung offen. -->

# Vorregistrierung: Suchpfad-Nachmessungen (Floor-Gewicht, m-Formel, τ-Annealing)

**Angelegt 2026-08-06, VOR allen Laeufen** (Nutzer-Auftrag "plan ein in
die pipeline"; Quelle: Suchpfad-Verifikations-Inventar). Ausfuehrung
NACH dem v20-Champion-Gating (laufende Kampagne wird nicht angefasst,
Arena-Maschine ist dann warm). Regeln nach Sichtung von
Zwischenergebnissen nicht mehr aenderbar.

## Vorarbeit (einmalig, im Post-Kampagnen-Fenster)

Zwei Laufzeit-Knoepfe nach dem #30-Muster (Env-Var, Default =
byte-identisches Bestandsverhalten), Wheel-Neubau erst moeglich, wenn
die Self-Play-Prozesse beendet sind (DLL-Lock):
- `MOSAIC_FLOOR_SHAPING_W` (Default 0.3) -- ueberschreibt
  FLOOR_SHAPING_WEIGHT (net_mcts.rs:373).
- `MOSAIC_GUMBEL_TOP_M` (Default 0 = Formel `gumbel_top_m_for_budget`)
  -- fester Override der Wurzelbreite.
Beide mit Paritaets-Nachweis (Default-Lauf bitgleich zu vorher) und
Engine-Tests vor Einsatz.

## AMENDMENT Instrument (2026-08-07, VOR dem ersten Messlauf)

Die urspruengliche Formulierung "Modell auf BEIDEN Seiten identisch, nur
Env verschieden" ist mit den gebauten Knoepfen NICHT ausfuehrbar: die
Env-Vars sind prozessweit (OnceLock, einmalig gelesen), ein
Netz-vs-Netz-Match traegt den Wert also zwingend auf BEIDEN Seiten --
ein Spiegelmatch desselben Modells misst dann nichts. Ersatz-Instrument
= das etablierte Zwei-Arm-Muster (#30-Skalen-Korrektur,
Floor-Erstvalidierung): **je Arm ein eigener Prozess (Env gesetzt),
Champion-Netz vs Heuristik@150(dyn) -- die Heuristik liest keinen der
beiden Knoepfe, die Differenz attribuiert sauber auf die Netz-Seite.**
Identische Basis-Seeds je Spielindex ueber die Arme, fixed-n, exakter
zweiseitiger McNemar auf den diskordanten Paaren (Formel wie
paired_gating.py). Entscheidungsregeln der Messungen unveraendert.

## Messung 1 — Floor-Gewicht-Sweep in der WDL-Aera (billig, zuerst)

**Frage**: Ist 0,3 noch der richtige Wert, nachdem sich die
Value-Spreizung seit der Kalibrierung ~2x geaendert hat (WDL-Aera)?
Der 0,15/0,6-Sweep steht seit Juli als "optional" offen.
**Design (gem. Amendment oben)**: Modell = v20-Champion
(`v20_2d_opp_brierbest`, Gating gewonnen). DREI Arme a 200 Spiele
(Champion@400 vs Heuristik@150dyn, identische Seeds ueber die Arme):
W=0,3 (Kontrolle), W=0,15, W=0,6. Vergleiche 0,3-vs-0,15 und
0,3-vs-0,6 per gepaartem McNemar. Optional Bestaetigung W=0,0
(Re-Validierung des Features am neuen Kopf).
**Entscheid**: Wechsel des Defaults nur bei SPRT-H1 GEGEN 0,3 plus
Frisch-Seed-Replikation (Statistik-Regel 3); sonst bleibt 0,3 und der
Punkt gilt als WDL-re-validiert.
**Kosten**: 2-3 Gatings a ~1-2h.

## Messung 2 — m-Formel bei niedrigen Sims (billig)

**Frage**: Kostet die Budget-Formel (150 Sims -> m=9) Staerke gegenueber
fester Breite m=16? Relevanz: Schwarm-Klasse kuenftiger Kampagnen und
alle Niedrig-Sims-Presets (GUI/#31).
**Design (gem. Amendment oben)**: ZWEI Arme a 200 Spiele
(Champion@150 vs Heuristik@150dyn, identische Seeds), Arm A
`MOSAIC_GUMBEL_TOP_M=0` (Formel, m=9), Arm B `=16`; gepaarter
McNemar. Sekundaer identisch @64 Netz-Sims (m=4 vs 16), falls A
signifikant.
**Entscheid**: H0 -> Formel bestaetigt (Abweichungsnotiz der
v20-Kampagne wird geschlossen). Signifikanter Unterschied -> Formel
anpassen UND bewerten, ob der v19wdlsw-Schwarm als Value-Material
davon beruehrt ist (Value-Ziel ist sim-robust -- erwartet: nein; wird
dann aber explizit am Brier eines Schwarm-Ablations-Trainings geprueft).
**Kosten**: 1-2 Gatings a ~30-60min (150 Sims spielen schnell).

## Messung 3 — τ-Annealing (teuer, zuletzt, eigenes Go)

**Frage**: Verbessert Standard-Annealing (fruehe Zuege τ=1, spaete
argmax) die Korpus-Qualitaet gegenueber durchgehend τ=1?
**Kostenklasse (halbiert, Nutzer-Hinweis 2026-08-06)**: die
τ=1-KONTROLLE existiert bereits -- die 4.000 v19wdl-Sockel-Partien SIND
durchgehend-τ=1-Material vom selben Generator. Frisch noetig ist NUR
der Annealing-Batch: ~2.000 Sockel-Partien mit argmax ab Zug ~30
(self_play-Erweiterung im Post-Kampagnen-Fenster). Design: Arm A =
v20-Fenster unveraendert; Arm B = identisches Fenster, aber 2.000 der
4.000 Sockel-Partien (feste, seed-bestimmte Auswahl) gegen die 2.000
Annealing-Partien getauscht -- alles andere in beiden Armen identisch.
2 Trainings + 1 Gating + Brier/Orakel deskriptiv. ~0,5 Tage Maschine.
**Vorab-Festlegung**: Annealing-Schwelle Zug 30 (grob 1. Runde+),
danach argmax; R5 bleibt Alpha-Beta-exakt (unberuehrt).
**Entscheid**: Uebernahme nur bei repliziertem Arena-Vorteil.
**Gate**: eigenes Nutzer-Go vor dem Start (Kostenklasse), fruehestens
nach Messung 1+2.

## Reihenfolge in der Pipeline

v20: Cache -> Training -> Gating -> Diagnostik/Watchlist ->
**[Knoepfe bauen] -> Messung 1 -> Messung 2** -> (Nutzer-Go) Messung 3.
Parallel dazu unveraendert: frozen-Set-Neubau, #29-Instrument,
Aggressions-Neukartierung, #37.

## MESSUNG-3-ERGEBNIS (2026-08-08): H0 -- tau=1 bleibt

Arm B (t3ann_s2, 2.000 Sockel-Partien seed-bestimmt gegen v19wdlann
getauscht, sonst identisches Fenster/Rezept/Seed) vs Champion:
112:118 nach 115 Paaren, SPRT-H0, p=0,78. Deskriptiv: Alt-Messset-Brier
0,18201 (E15) im Serienband, kein Ausreisser. **Uebernahme-Regel greift
nicht -> DURCHGEHEND tau=1/Sampling bleibt Standard; der v21-Sockel
wird OHNE --tau-argmax-from-move generiert.** Der Knopf bleibt als
inertes Werkzeug. Damit sind Messung 1-3 KOMPLETT: dreimal Status quo
bestaetigt (Floor-W 0,3; m-Formel; tau=1) -- der Suchpfad ist in der
WDL-Aera vollstaendig re-validiert.

## Messung 3-V (Vorstufe): Was kostet die Temperatur an Spalten, und was an Vielfalt? (registriert 2026-09-07, 01:20, VOR der Messung; Nutzer-Freigabe "ja, fahr den vergleich nach dem arm")

**Anlass (Nutzer 2026-09-07, 01:05):** *"das self play zerstoert die spalten schon frueh.
vielleicht holen wir uns den zufall weniger ueber die temperature als mehr ueber den zufall
des spiels."* Dazu der eigene Einwand des Nutzers (01:12) mit Verweis auf
`PREREG_uncertainty_guided_selfplay.md` par.2: der Zufall des Spiels ist ALEATORISCH und
damit kein Lernsignal; wer auf aleatorische Breite auswaehlt, sucht die zufaelligsten
Stellungen auf, also die mit dem geringsten Lernwert. Der Ersatz fuer gesenkte Temperatur
muesste GERICHTET sein (Stufe 1 dort). Diese Vorstufe klaert, wie gross die zu ersetzende
Luecke ueberhaupt ist -- ohne Training, ohne Engine-Aenderung.

**WAS SCHON GEMESSEN IST, und warum das die Frage nicht erledigt:** Messung 3 oben ist
GEFAHREN (2026-08-08): Arm B mit 2.000 Sockel-Partien `--tau-argmax-from-move 30` gegen den
Champion, 112:118 nach 115 Paaren, SPRT-H0, p 0,78 -- durchgehendes Sampling blieb Standard.
Drei Unterschiede machen die Frage trotzdem offen: (a) gemessen wurde STAERKE nach einem
Training, nicht der Spaltenbau IM MATERIAL -- der Spaltenstrang der Kampagne begann erst mit
v22; (b) die Aera war v20/WDL, das heutige Netz ist v24 auf Sicht 744 mit K3-P; (c) H0 auf
115 Paaren schliesst einen Spalten-Effekt nicht aus, es sagt nur, dass die Siegquote sich
nicht bewegte. Diese Vorstufe misst darum eine ANDERE Groesse an einer BILLIGEREN Stelle;
sie kann Messung 3 nicht widerlegen und will es nicht.

**Mechanik (am Code geprueft 2026-09-07):** `drafting_policy` (`self_play.rs:349-378`)
trennt beides schon heute: das Policy-ZIEL kommt aus den Besuchszahlen der Wurzel, der
GESPIELTE Zug wird mit `play_temp` daraus gesampelt ("PLAY: moderate Temperatur ->
gespielte Aktion sampeln (Zustandsvielfalt)"). Das Sampling verdirbt also nicht die
Lernziele, sondern die Stellungen -- ein zweitbester Zug in eine halbfertige Spalte, und die
Struktur steht ab da nicht mehr. Der Regler dagegen ist gebaut:
`MOSAIC_TAU_ARGMAX_FROM_MOVE` / `--tau-argmax-from-move N` (argmax ab Halbzug N,
`net_mcts.rs:2523`), Default 0 = aus.

**Aufbau (drei Chargen, gepaart):** derselbe Generator, dieselben Seeds, dieselbe
Sockel-Konfiguration wie die v24-Erzeugung (`--sims 100`, mit Wurzelrauschen, gesampelt,
policy-aktiv, `--threads 11 --chunk 10 --per-file 10`), 200 Partien je Charge:

| Charge | `--tau-argmax-from-move` | Rolle |
| --- | --- | --- |
| A | 0 (aus) | Bestand, Kontrolle |
| B | 12 | argmax ab Halbzug 12 (rund ab Runde 2) |
| C | 30 | argmax ab Halbzug 30 (Schwelle der registrierten Messung 3) |

Generator `v24-b06_brierbest` mit Champion-Spec (der amtierende Champion; die
Generatorfrage fuer v25 ist offen, `PREREG_v25_window.md` par.11 A, und beruehrt diese
Messung nicht -- gefragt ist die Wirkung der Temperatur, nicht die des Netzes).

**Messgroessen, VOR der Messung festgelegt (je Charge):**
1. **Volle Spalten je Seite** und Seiten mit voller Spalte (`tools/corpus_sanity_check.py`),
   dazu Punkte und Strafleiste -- die Groesse, um die es dem Nutzer geht.
2. **Zustandsvielfalt** (`tools/probes/corpus_state_diversity_probe.py`, gebaut 2026-08-25
   fuer genau diese Frage): distinkte 36-Bit-Belegungsmasken der Kuppel je Runde, distinkte
   Endbretter, Masken je Partie. Das ist der Preis, den die gesenkte Temperatur kostet.
3. **Lange Reihen** begonnen/vollendet je Seite, soweit die Korpus-Sonde sie ausweist
   (Nebenbefund, keine Entscheidungsgroesse).

**Lesart, vorab festgelegt:**
- **B oder C hebt die Spalten deutlich UND verliert wenig Vielfalt** (Richtwert: Spalten
  +0,1 oder mehr, distinkte Endbretter nicht unter 90 % von A): die These des Nutzers
  traegt, und der Sockel-Betriebspunkt der v25-Erzeugung ist ein Kandidat fuer die Aenderung.
- **Spalten steigen, Vielfalt bricht ein** (Endbretter deutlich unter 90 % von A): die
  Luecke ist real und muss gerichtet ersetzt werden -- das ist der Anschluss an
  `PREREG_start_position_seeding.md` par.8 (Stufe 1 der Unsicherheits-Prereg, deren
  Faltungsbedingung durch den b03-Befund erfuellt ist: Tor 1 mit Knopf ueber zwei Seeds,
  214:146, hoechster Kuppel-Bonus 4,2).
- **Spalten bewegen sich nicht**: die Temperatur ist nicht die Ursache des Spaltenverlusts
  im Sockel, und die 0,19 der Sockel-Klasse haben einen anderen Grund. Dann faellt dieser
  Strang, und par.11 C der v25-Prereg bleibt unbeantwortet. Das waere zugleich die
  Bestaetigung des Messung-3-Befunds von 2026-08-08 auf der Materialseite.

**Verhaeltnis zur registrierten Messung 3:** traegt 3-V, ist Messung 3 NICHT automatisch
ueberholt -- sie hat gezeigt, dass Annealing die Staerke nicht bewegt, und das bleibt wahr.
Eine Wiederholung mit Training waere ein eigener Arm mit eigenem Go, weil sie zwei
Trainings plus Gating kostet (Schaetzung von 2026-08-06: rund ein halber Maschinentag).

**Was diese Messung NICHT beantwortet:** ob ein daraus trainiertes Netz staerker spielt oder
in der ARENA mehr Spalten baut (Nutzer 2026-09-07, 01:00: *"zum schluss brauch ich in der
arena mehr spalte"*). Sie misst das MATERIAL. Der Schritt von Material zu Arena ist die
registrierte Messung 3 oben (zwei Trainings plus Gating) und braucht ein eigenes Go.

**Kosten (aus `docs/measured_runtimes.md`, gemessen):** 3,365 s je Sockel-Partie bei
threads 11, also rund 11 min je Charge, 34 min fuer drei; die beiden Sonden sind
Sekunden. Laeuft exklusiv nach dem Huellenform-Arm (par.8.15 Teil B).

### MESSUNG-3-V-ERGEBNIS (gefahren 2026-09-07, 01:51-02:21; drei Chargen je 200 Partien, Generator `v24-b06` mit Champion-Spec, `--sims 100`, Wurzelrauschen an, Basis-Seed 20260931 fuer alle drei)

**Die These des Nutzers traegt, und deutlicher als die vorab festgelegte Schwelle verlangt.**

| Charge | `--tau-argmax-from-move` | volle Spalten je Seite | Punkte | Strafleiste | Seiten mit voller Spalte |
| --- | --- | --- | --- | --- | --- |
| A (Bestand) | 0 (aus) | **0,1950** (KI +-0,047) | 28,3 | 9,41 | 64 von 400 |
| B | 12 | **0,4225** (KI +-0,062) | 38,5 | 7,54 | 138 von 400 |
| C | 30 | **0,3000** (KI +-0,053) | 36,5 | 7,80 | 103 von 400 |

**Und die Vielfalt bleibt** (`state_diversity_temperature.json`, gleiche 200 Partien):

| Charge | distinkte Endbretter (von 400 Seiten) | distinkte Zustaende je Record | distinkte je Partie |
| --- | --- | --- | --- |
| A | 400 | 0,1726 | 38,3 |
| B | 399 | 0,1784 | 40,1 |
| C | 398 | 0,1758 | 39,6 |

**Bedingte Vielfalt** (`paired_corpus_divergence_probe.py`, neu gebaut fuer diese Frage;
200 gepaarte Spielindizes, bei denen Wertungsplatten, Startspieler und Auslagen-Ziehung
identisch sind): **6 von 6 moeglichen distinkten Endbrettern je Spielindex** -- bei
identischen Startbedingungen erzeugen die drei Konfigurationen durchweg verschiedene
Bretter. Divergenz-Halbzug im Median 15 (A gegen B) bzw. 39 (A gegen C), keine einzige
Partie identisch, Endbrett-Hamming-Abstand 21 bzw. 18 von 36 Bit.

**Policy-Entropie der Ziele: 0,628 / 0,644 / 0,660 nats** (A / B / C). Sie STEIGT leicht mit
mehr argmax, statt zu fallen. Die naheliegende Sorge -- argmax mache die Lernziele
einseitig -- trifft also nicht zu; die Ziele kommen ohnehin aus den Besuchszahlen und
nicht aus der Zugwahl (`self_play.rs:349-378`), und in den besser gespielten Stellungen
gibt es offenbar eher mehr gleichwertige Fortsetzungen als weniger (Deutung, nicht gemessen).

**Verdikt nach der vorab festgelegten Lesart:** Fall 1 ist eingetreten -- "Spalten deutlich
hoeher UND wenig Vielfalt verloren" (Richtwert war +0,1 Spalten und mindestens 90 % der
Endbretter). Erreicht: **+0,2275 Spalten (mehr als eine Verdopplung) bei 99,75 % der
Endbretter.** Das Sampling der ZUGWAHL kostet dem Sockel also mehr als die Haelfte seines
Spaltenbaus und liefert dafuer praktisch keine zusaetzliche Zustandsvielfalt.

**Was das fuer die 0,19 der Sockel-Klasse heisst.** Die Zahl, die in
`PREREG_v25_window.md` par.7 als "spaltenaermste Klasse des Fensters" gefuehrt wird
(0,189), ist hier mit 0,1950 unabhaengig reproduziert -- und sie ist ein Artefakt der
Temperatur, keine Eigenschaft des Materials oder des Netzes. Damit ist der Einwand des
Nutzers vom 2026-09-07, 00:5x ("keine von deinen loesungen ueberzeugt mich, du misst das
self play und nicht die arena") an der Wurzel beantwortet: es gab nichts am Mix zu
reparieren, der Betriebspunkt der Erzeugung war der Fehler.

**Offen, ausdruecklich:** ob ein aus diesem Material trainiertes Netz staerker spielt oder
in der ARENA mehr Spalten baut. Diese Messung misst das MATERIAL. Der Schritt von Material
zu Arena ist die registrierte Messung 3 oben, und die hat 2026-08-08 in der v20-Aera fuer
argmax ab Zug 30 H0 auf die STAERKE ergeben (112:118). Dass B (Zug 12) hier besser
abschneidet als C (Zug 30), war damals nicht im Bild -- gemessen wurde nur Zug 30.

**Folgefragen, die sich aus der Kurve ergeben (nichts entschieden):**
1. **Wo liegt das Optimum?** B (12) schlaegt C (30) um 0,12 Spalten. Ein vierter Punkt bei
   1 (praktisch durchgehend argmax) wuerde zeigen, ob es weiter steigt oder ob es ein
   Zwischenoptimum gibt. Kosten: rund 10 min.
2. **Wieviel Streuung braucht die Policy wirklich?** Bei durchgehendem argmax bleibt als
   Streuquelle nur das Wurzelrauschen. Die Endbretter-Zahl sagt, dass das reicht -- aber
   sie misst Bretter, nicht Policy-Abdeckung.
3. **Anschluss an das Verzweigen** (`PREREG_start_position_seeding.md` par.9/9a): wenn
   argmax die Spalten verdoppelt, ohne Vielfalt zu kosten, ist der gerichtete Ersatz der
   Streuung weniger dringend als angenommen -- aber er bleibt der Weg, um GEZIELT in
   selten besuchte Stellungen zu kommen.

### 3-V, Nachtrag: was "Wurzelrauschen" hier ist, und was daraus folgt (Nutzer-Berichtigung 2026-09-07, 03:00: "nein. es gibt kein dirichlet rauschen")

Der Koordinator hatte im Chat behauptet, die Streuung bei aktivem Wurzelrauschen komme von
Dirichlet-Rauschen auf dem Prior. **Falsch, am Code geprueft:** die Netz-Suche ist
Gumbel-basiert (`build_gumbel_tree`; der PUCT-Baum wird nicht mehr betreten, sein
Doc-Kommentar bei net_mcts.rs:4258 spricht noch von Dirichlet und ist ueberholt). Was
`add_root_noise` schaltet, sind **Gumbel-Samples je Wurzelkandidat**: `g + ln(prior)` mit
`g = sample_gumbel(rng)` (net_mcts.rs:3974); ist der Schalter aus, sind alle `g = 0` und die
Wurzelauswahl rankt deterministisch nach `ln(prior) + sigma(Q)`.

**Die Schlussfolgerung der Messung bleibt** (die Partien bleiben auch nach dem Umschaltpunkt
verschieden, 399 von 400 Endbrettern), nur die Rauschquelle heisst anders.

**Der wichtigere Punkt, der dabei sichtbar wurde:** die **Schwarm-Klasse laeuft mit
`--deterministic --no-root-noise`**, hat also GAR KEINE Rauschquelle -- weder Sampling der
Zugwahl noch Gumbel an der Wurzel. Ihre gesamte Streuung kommt aus dem Spiel (Auslagen,
Wertungsplatten, Startspieler). Und genau diese Klasse ist mit **0,748 vollen Spalten die
spaltenreichste des Fensters**, bei 8.000 Partien. Es gibt im Fenster also bereits eine
grosse Klasse, die ohne jede kuenstliche Streuung auskommt und die beste Spaltenzahl
liefert; der Sockel war die einzige Klasse, die die Zugwahl wuerfelt, und die einzige mit
0,19. Das stuetzt die Nutzer-These unabhaengig von Messung 3-V.
