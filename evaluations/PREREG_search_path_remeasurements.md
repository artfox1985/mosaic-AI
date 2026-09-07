<!-- STATUS: ENTSCHIEDEN | Frage: Re-Validierung von Floor-Gewicht, m-Formel und τ-Annealing in der WDL-Aera (3 Messungen) | Beleg: alle 3 Messungen H0, Status quo bestaetigt (Abschnitt "MESSUNG-3-ERGEBNIS"; tau-Annealing 112:118, p 0,78, v20-Aera, Mass war STAERKE). NACHTRAG 2026-09-07: Vorstufe 3-V GEFAHREN -- das Sampling der Zugwahl kostet dem Sockel mehr als die HAELFTE seines Spaltenbaus (0,195 gegen 0,4225 bei argmax ab Halbzug 12) und liefert dafuer praktisch keine Vielfalt (399 von 400 Endbrettern distinkt in beiden Faellen). Die 0,19 der Sockel-Klasse sind ein Temperatur-Artefakt. Arena-Wirkung offen -- Messung 3-W registriert (zwei Sockel-Chargen im v24-Fenster, ein Faktor, rund 12 h, Start auf Anweisung). -->

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

## Messung 3-W: traegt der Umschaltpunkt bis ins NETZ? (registriert 2026-09-07, 03:10 VOR jedem Lauf; Nutzer: "dann takte das training dafuer ein" / "oder geht das erst mit v25?")

**Die Frage, die 3-V offen laesst.** 3-V hat gemessen, dass das Sampling der Zugwahl dem
Sockel mehr als die Haelfte seines Spaltenbaus kostet, ohne Vielfalt zu kaufen. Das ist eine
Aussage ueber MATERIAL. Der Nutzer hat den entscheidenden Einwand dazu formuliert (03:05):
*"und der value head braucht keine streuung? das wundert mich."* -- und er trifft eine
Luecke, die keine der Material-Kennzahlen schliessen kann: alle drei Chargen sind
on-policy. Verschiedene Brettmuster heissen nicht Abdeckung des Zustandsraums. Ob ein
Value-Kopf, der nur sauber gespieltes Material sieht, Stellungen NACH einem Fehler noch
richtig bewertet, zeigt erst ein Training plus eine Pruefung ausserhalb der eigenen
Verteilung.

**Nachgemessen, was messbar war (2026-09-07, 03:05, dieselben drei Chargen):** die
ERGEBNIS-Streuung bleibt ebenfalls erhalten -- Punkte-SD 15,2 / 17,9 / 17,0 (A / B / C),
mittlere absolute Marge 14,5 / 15,9 / 14,3, Anteil knapper Partien (Marge <= 5) 0,23 /
0,24 / 0,24, Siegerverteilung in allen drei ausgeglichen. Das in der Literatur beschriebene
Muster "zu greedy erzeugtes Material endet in lauter knappen Partien und nimmt dem
Value-Kopf das Signal" tritt hier NICHT auf. Die Frage nach der Abdeckung bleibt davon
unberuehrt.

### Aufbau: EIN Faktor, und das v24-Fenster als Traeger

**Der Test braucht v25 NICHT** (Nutzer-Frage): das v24-Fenster liegt vollstaendig vor. Es
wird in beiden Armen benutzt, und darin werden ausschliesslich die 4.000
Sockel-NEU-Partien ersetzt -- zweimal, vom selben Generator, mit dem einzigen Unterschied
`--tau-argmax-from-move`:

| | Arm W0 (Kontrolle) | Arm W1 |
| --- | --- | --- |
| Sockel NEU (4.000, policy-aktiv, @100, Wurzelrauschen an) | `--tau-argmax-from-move 0` (Bestand) | `--tau-argmax-from-move 12` |
| Generator | `v24-b06_brierbest` mit Champion-Spec, in BEIDEN Armen | dito |
| Schwarm NEU, G-1, G-2 | v24-Bestand, in beiden Armen dieselben Dateien | dito |
| Training | b01-Rezept, Warm-Start vom Generator, 12 Epochen, `--fast-loader`, `--select-by-brier` | dito |

**Warum nicht das v24-Material als Kontrolle:** dessen Sockel stammt von `v23-b01`. Ein
Vergleich dagegen haette zwei Faktoren (Generator UND Temperatur). Beide Arme erzeugen
deshalb frisch.

### Messgroessen, VOR dem Lauf festgelegt

1. **Value ausserhalb der eigenen Verteilung -- die Kernfrage.** Auf `frozen_v3`
   (`PREREG_frozen_v3_eval_set.md`: 1.800 Zustaende, Orakel-Labels): `value_r2` je Runde
   und Brier. Bezug ist der jeweils andere Arm, nicht ein historischer Wert.
   **Aufloesungsgrenze beachten:** `value_r2` traegt nur ueber eine Luecke von rund 0,015
   ([[project_offline_metric_resolution_limit]]) -- darunter ist die Metrik stumm, und die
   Arena entscheidet.
2. **Orakel-Metriken** (`tools/oracle_metrics.py`): `prior_mass_on_oracle_top3` und
   `kendall_tau`. Sie haben die Arena 7 von 7 mal richtig vorhergesagt
   ([[project_oracle_metrics_validated]]) und sind damit das schaerfste Offline-Mass.
3. **Arena W1 gegen W0**, gepaart, beide Seiten Champion-Spec, Seed 20261012, Deckel
   200 Paare, SPRT wie Tor 1. Das ist der Entscheid.
4. **Volle Spalten** am argmax-Instrument @400 (Tor 2a, 200 Partien, Seed 20260931) je Arm
   -- ob sich der Materialvorteil ins Netz uebertraegt.
5. **Zustandsabdeckung des Materials** als Kontrolle:
   `tools/probes/paired_corpus_divergence_probe.py` ueber die beiden Sockel-Chargen
   (gleicher Seed, gepaart) und `corpus_state_diversity_probe.py` je Charge.

### Lesart, vorab

- **W1 gewinnt die Arena ODER liegt in den Orakel-Metriken vorn, bei gleichen oder
  besseren Spalten:** der Umschaltpunkt gehoert ins v25-Rezept (`PREREG_v25_window.md`
  par.13), und die Frage nach der Streuung ist beantwortet.
- **W1 verliert die Arena oder faellt im Value ausserhalb der Verteilung ab:** die
  Verengung ist real; dann braucht der Sockel eine Streuquelle, die NICHT die Zugwahl
  verdirbt -- das ist Weg C (`PREREG_start_position_seeding.md` par.9c), und er wuerde
  damit von der Kuer zur Pflicht.
- **Beides unentschieden:** der Umschaltpunkt ist eine Material-Kosmetik ohne Wirkung; dann
  entscheidet die Bequemlichkeit, und das heisst Bestand lassen.

### Kosten (gemessen, aus `docs/measured_runtimes.md`)

| Posten | Kosten |
| --- | --- |
| 2 x 4.000 Sockel-Partien @100 (3,365 s je Partie, threads 11) | 7,5 h |
| 2 Trainings (12 Epochen, `--fast-loader`, rund 4.850 s je Lauf) | 2,7 h |
| frozen_v3-Bewertung + Orakel-Metriken je Arm | Minuten |
| Arena 2 x 80 plus Instrument je Arm | rund 1,5 h |
| **Summe** | **rund 12 h** |

Zum Vergleich: eine volle v25-Erzeugung kostet allein 11,2 h. Der Test ist also
groessenordnungsgleich mit dem, was er absichert.

### Reihenfolge

**Vor der v25-Erzeugung.** Wenn W1 traegt, startet v25 mit einer belegten statt einer
plausiblen Einstellung; wenn nicht, waere der Umschaltpunkt im v25-Rezept ein Fehler, den
man erst am Ende der Generation bemerkt haette. **Start nur auf Nutzer-Anweisung** (die
Erzeugung von 8.000 Partien faellt unter den Vorbehalt "ausser der Fenster-Erzeugung").

### 3-V, vierter Punkt: k = 1 ist das Optimum, die Reihe ist monoton (gefahren 2026-09-07, 03:24-03:33)

| `--tau-argmax-from-move` | gesampelte Halbzuege | volle Spalten je Seite | Punkte | Strafleiste | Seiten mit voller Spalte |
| --- | --- | --- | --- | --- | --- |
| aus (Bestand) | alle 162 | 0,1950 (KI +-0,047) | 28,3 | 9,41 | 64 / 400 |
| **1** | **keine** | **0,5325** (KI +-0,072) | **41,5** | **6,93** | **156 / 400** |
| 12 | 11 | 0,4225 (KI +-0,062) | 38,5 | 7,54 | 138 / 400 |
| 30 | 29 | 0,3000 (KI +-0,053) | 36,5 | 7,80 | 103 / 400 |

**Die Reihe ist monoton: je frueher argmax, desto mehr Spalten, desto mehr Punkte, desto
weniger Strafleiste.** Es gibt kein Zwischenoptimum. Der beste Punkt ist der Randpunkt
k = 1, also durchgehend greedy -- die Zugwahl sampelt gar nicht mehr, die einzige Streuung
kommt aus dem Gumbel-Wurzelrauschen der Suche (par.9d der Seeding-Prereg: `add_root_noise`
ist im Sockel AN) und aus dem Spiel selbst.

**Damit ist der Nutzer-Vorschlag "argmax + C" (2026-09-07, 03:12) belegt die richtige
Wahl:** wenn das Sampling in JEDER Dosis schadet, holt man die Streuung besser aus einem
Mechanismus, der die Zugqualitaet nicht verdirbt. Fuer die v25-Arme S3 und S4
(`PREREG_v25_window.md` par.14) gilt damit **k = 1**.

**Einordnung, damit die Zahl nicht ueberdehnt wird:** 0,5325 ist die
SOCKEL-Konfiguration (@100, Wurzelrauschen an, policy-aktiv). Das argmax-Instrument
derselben Nacht misst 0,8200 bei @100 -- dort sind zusaetzlich `--deterministic` und
`--no-root-noise` gesetzt. Der Unterschied von rund 0,29 zeigt, was allein das
Wurzelrauschen der Suche noch kostet; es ist die letzte verbliebene Streuquelle im
Sockel und NICHT Gegenstand dieser Messung.
