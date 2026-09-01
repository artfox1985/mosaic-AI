<!-- STATUS: OFFEN | Frage: Ist das Netz fuer sein Rechenbudget zu KLEIN -- und wo liegt bei fixem WANDUHR-Budget das Optimum aus Netzgroesse und Sim-Budget? | Beleg: Kaltstart-Arm gemessen. **par.12/13: gleich stark, aber nur ein DRITTEL der Spalten** (b01 0,62 gegen 0,17 fuer `_brierbest` und 0,56 gegen 0,23 fuer `_best`, Staerke 85:75 bzw. 92:68) -- der Checkpoint erklaert es nicht, das Spaltenwissen sitzt in der LINIE, nicht im Korpus allein. Frontier selbst weiter OFFEN: Breiten-Arm b04, Zweig-Entscheid beim Nutzer (par.10), Kostentor zuerst (par.5). -->

# Vorregistrierung: Kapazitaets-Sim-Frontier

**ENTWURF 2026-08-27 aus dem Recherche-Abgleich. Nutzer-Entscheid ueber den
Bau offen, nichts gebaut.**

## par.1 Die Frage

Nicht "hilft ein groesseres Netz?", sondern: **wo liegt bei FIXEM
Wanduhr-Budget das Optimum aus Rumpfbreite und Sim-Budget?** Ein groesseres
Netz kostet je Zug mehr Inferenz und kauft damit Sims ab; ein kleineres Netz
sucht tiefer und weiss je Blatt weniger. Die beiden Groessen sind nicht
unabhaengig einstellbar, und genau deshalb ist ein Einzel-A/B die falsche
Bauform.

Der Zuschnitt der Literatur ist eine **Frontier**: 2-3 Netzgroessen mal 2-3
Sim-Budgets, alle Paarungen auf DASSELBE Wanduhr-Budget je Partie normiert,
gepaart gemessen. Was verglichen wird, ist nicht "Netz A gegen Netz B", sondern
die Huellkurve.

## par.2 Quellenlage (beide im Repo, in dieser Sitzung nachgelesen)

`RESEARCH_alphazero_improvements_2026-08-01.md`:

* **Fund 11** (Jones 2021, "Scaling Scaling Laws with Board Games"):
  Train- und Test-Compute sind log-linear gegeneinander eintauschbar (~10x
  Trainings-Compute ersetzt ~15x Test-Compute). Uebertragbarkeit dort
  **MITTEL-HOCH als Entscheidungsrahmen**, mit der ausdruecklichen Empfehlung,
  "512-hidden-MLP + 400-600 Sims gegen groesseres Netz + weniger Sims" als
  kleine Frontier bei fixem Arena-Zeitbudget zu messen statt als Einzel-A/Bs.
  Aufwand dort als NIEDRIG eingeschaetzt, weil `arena.py` existiert.
* **Fund 12** (Neumann/Gros 2022/2023 plus "AlphaZero Neural Scaling and
  Zipf's Law" 2024): Elo skaliert als Potenzgesetz in der Parameterzahl
  (Exponent ~0,88 auf Connect Four/Pentago), die optimale Netzgroesse waechst
  mit Compute hoch 0,63. Kernaussage: **die meisten publizierten
  AlphaZero-Agenten sind fuer ihr Compute-Budget zu klein.** Die Recherche
  haelt im selben Absatz den Gegenbefund fest -- Folgearbeiten zeigen
  Inverse-Scaling-Faelle, groesser ist NICHT garantiert besser. Beides gehoert
  in diese Registrierung, nicht nur die guenstige Haelfte.

## par.3 Warum das JETZT registriert werden muss

**Der Rumpf ist nur bei einem KALTSTART frei.** Ein Warmstart laedt einen
Checkpoint, und ein Checkpoint fixiert die Rumpfbreite -- das
Warm-Start-Standardrezept (v12b und alles danach) sperrt das Fenster also per
Konstruktion. Kaltstarts sind selten: der v22-Kaltstart
(`PREREG_heuristic_v2_long_rows.md` par.3b.2, Nutzer-Entscheid 2026-08-27) ist
der erste seit dem v14-Neubau.

**Damit ist die Registrierung selbst der Zweck dieser Datei.** Der Arm ist
realistisch erst beim NAECHSTEN Kaltstart fahrbar -- er soll den laufenden
nicht aufhalten. Aber wenn er nicht JETZT registriert ist, faellt die Frage
beim naechsten Kaltstart wieder still zugunsten des Bestands aus, und zwar
unbemerkt. Das ist dieselbe Mechanik, die `PREREG_bootstrap_horizon.md` par.9a
fuer den Bootstrap-Horizont beschreibt: "wer die Frage offen laesst,
entscheidet sie faktisch zugunsten des Bestands".

## par.4 Was den Arm NICHT schliesst

**Das Head-Widening-Negativ betrifft ihn nicht.**
[[project_stage2_value_head_capacity_test]] hat Kopf-Verbreiterung UND
Rumpf-Dedizierung am VALUE-Kopf ausgeschlossen (0,272 und 0,19 gegen eine
Baseline von 0,27-0,34; Deutung: irreduzibles Zielrauschen). Die Recherche
sagt zu genau dieser Abgrenzung: der Fund "widerspricht nicht dem
Head-Widening-Negativergebnis (dort nur Value-Head verbreitert, hier Trunk +
angepasstes Sim-Budget)". Das ist ein anderer Eingriffsort und ein anderes
Budget-Regime.

**Der Vollstaendigkeit halber, weil es sonst hinterher als Ueberraschung
kommt:** [[feedback_value_head_capacity]] warnt vor dem Reflex, einen
plateauenden Kopf zu verkleinern, ohne auf Kapazitaets-Hunger zu pruefen.
Dieser Arm ist die Gegenrichtung derselben Frage, eine Ebene tiefer.

## par.5 KOSTENTOR, Pflicht und ZUERST

**Vor jeder Staerkemessung wird die CPU-Inferenz gegengerechnet.** Die
Gegenrechnung ist in diesem Projekt keine Formalie: 2D kostet heute bereits
Faktor **1,8** gegen die flache Ablesung, remessen und nicht geschaetzt
([[project_2d_inference_optimization]]) -- und dieselbe Memory-Notiz haelt
fest, dass die Wanduhr die FLOP-Rechnung dort **zweimal** geschlagen hat.
Folge fuer diesen Arm:

1. Gemessen wird **Wanduhr je Zug**, nicht Parameterzahl und nicht FLOPs.
2. Die Frontier wird auf **gleiche Wanduhr je Partie** normiert. Eine
   Konfiguration, die mehr Zeit bekommt, ist kein Frontier-Punkt, sondern ein
   Messfehler.
3. Reisst eine Netzgroesse das Zeitbudget so weit, dass ihr Sim-Budget unter
   die Aufloesungsgrenze der Arena faellt, faellt sie aus der Frontier -- das
   wird BERICHTET, nicht durch Budget-Aufstockung geheilt.

## par.6 Was noch offen ist (kein Entscheid dieser Datei)

* Die konkreten Rumpfbreiten und Sim-Budgets der Frontier.
* Ob die 2D-Architektur oder die flache die Traegerarchitektur ist.
* Der Umgang mit der Trainingskosten-Seite: eine groessere Rumpfbreite kostet
  auch im Training, und Fund 11 handelt gerade vom Tausch zwischen beiden
  Budgets. Diese Registrierung fixiert nur das TEST-Budget.

## par.7 Entscheidungsmass, vorab

**Arena, gepaart, Block-Ebene** -- die Frage IST eine Staerkefrage bei fixem
Budget, und Offline-Masse haben Architektur-Staerke in diesem Projekt schon
einmal falsch vorhergesagt (Orakelmetriken 0/1 als
ARCHITEKTUR-Staerkepraediktor, [[project_2d_encoder_phase2_result]]).
Kennzahlen je Frontier-Punkt sind die sechs Standard-Kennzahlen (CLAUDE.md),
plus der Laufzeit-Block im Artefakt jedes Laufs.

## par.8 Zeitpunkt (Nutzer 2026-08-28)

Nutzer: *"seh ich auch eher erst bei v23 oder v24."* Damit ist der Zeitpunkt
entschieden: NICHT im v22-Zyklus. Die Registrierung bleibt trotzdem jetzt
stehen, damit das Kaltstart-Fenster beim naechsten Anlass nicht wieder
unbemerkt zufaellt (par.3) -- wer v23/v24 plant, prueft an dieser Stelle, ob
der Lauf ein Kaltstart wird, und entscheidet DANN ueber den Bau.

## par.9 KALTSTART-ARM FUER v23 EROEFFNET (Nutzer-Entscheid 2026-08-31)

Nutzer: *"ich haette fuer diesen prereg einen arm mit coldstart eroeffnet.
der braucht nicht wirklich laenger als der warmstart"* -- und im selben Zug
die Arm-Benennung: **v23-b01 Warmstart aus den Self-Plays, v23-b02 Kaltstart,
v23-b03 Ueberraschungs-Gewichtung** (`PREREG_policy_surprise_weighting.md`
par.8, deren Arm-Name damit bestaetigt ist).

Damit faellt der par.8-Vorbehalt weg: der Punkt ist nicht still zugunsten des
Bestands entschieden, sondern ausdruecklich.

**Die Kostenaussage, an den Manifesten geprueft (2026-08-31):** die drei
v22-Kaltstarts liefen mit Epochenbudget 40 und Early Stop --
b01 **5,43 h** (19.536,6 s, darin 2,55 h In-Train-Cache-Bau; Stop bei E17),
b02 **2,56 h** (9.223,5 s, Cache-Treffer; Stop bei E16), b04 **2,52 h**
(9.056,5 s). Mit vorgebautem Cache -- den der laufende Co-Bau liefert --
kostet ein Kaltstart auf dem vollen Fenster also rund **2,5 h**.
**Die Gegenseite ist NICHT gemessen:** einen Warmstart auf dem VOLLEN Fenster
gibt es in der jungen Historie nicht; die einzigen Warmstarts sind die
DAgger-Afterburner auf 600 Zusatzpartien (b05 634 s, b06 472 s) und damit
kein Vergleichsmass. Die Nutzer-Einschaetzung ist mit dem Vorliegenden
vertraeglich -- die Kosten je Epoche haengen am Korpus, nicht am Startmodus,
der Unterschied ist allein die Epochenzahl -- aber sie ist eine
EINSCHAETZUNG, bis b01 die fehlende Zahl liefert. **Nebennutzen des Plans:
b01 gegen b02 misst Warmstart gegen Kaltstart auf DEMSELBEN Fenster, eine
Frage, die dieses Projekt nie sauber gemessen hat.**

**Was der Kaltstart-Arm liefert und was NICHT:** er OEFFNET das
Rumpfbreiten-Fenster (par.3), er MISST die Frontier nicht. Ein Kaltstart bei
unveraenderter Breite ist kein Frontier-Punkt. Die Breiten-Variation braucht
mindestens einen zweiten Kaltstart mit anderer Rumpfbreite plus die auf
Wanduhr normierte Arena aus par.5/par.7 -- und die konkreten Breiten sind
weiter offen (par.6). Ob b02 auf der Bestandsbreite oder gleich breiter
faehrt, ist der naechste Entscheid; die saubere Bauform ist erst b01/b02 auf
gleicher Breite (ein Faktor: Startmodus), die Breite danach als eigener Arm --
sonst tragen zwei Aenderungen ein Ergebnis.

## par.10 b02 faehrt die BESTANDSBREITE, b04 ist der Breiten-Arm (Nutzer-Entscheid 2026-08-31)

Nutzer: *"mach die bestands rumpfbreite und registrier b04 vor fuer die andere
breite."* Damit steht der Zuschnitt:

| Arm | Startmodus | Breite | Was er misst |
| --- | --- | --- | --- |
| `v23-b01` | Warmstart | Bestand | Referenz; liefert nebenbei die nie gemessene Warmstart-Zahl auf vollem Fenster |
| `v23-b02` | **Kaltstart** | **Bestand** | EIN Faktor gegen b01: der Startmodus. Kein Frontier-Punkt, aber der saubere Bezugspunkt fuer b04 |
| `v23-b04` | Kaltstart | **andere Breite** | der eigentliche Frontier-Punkt; gegen b02 gepaart, auf gleiche Wanduhr normiert (par.5) |

**WELCHE Breite -- am Code geprueft 2026-08-31, und die Antwort ist nicht eine
Zahl, sondern zwei Knoepfe.** `Mosaic2DNet` (neural_net.py:1579-1581) hat
einen Conv-Zweig und einen Flach-Zweig:

* **Flach-Zweig `hidden_size` = 512** (config.py:53). Fahrbar OHNE Bau:
  `--hidden` existiert (train.py:2302), und der Lader holt die Breite aus dem
  Checkpoint-Feld `hidden_size` (neural_net.py:1799) -- ein abweichend breites
  Netz laedt also.
* **Conv-Zweig `conv_channels` = 48, `conv_layers` = 2**
  (neural_net.py:1581). **Nicht fahrbar ohne Bau:** es gibt keine CLI-Flags
  dafuer, die Werte stehen in KEINEM Checkpoint-Feld, und
  `build_model_from_checkpoint` leitet nur `planes_channels` aus
  `conv.0.weight` ab (Eingangsdimension), nicht die Ausgangsbreite. Ein
  conv-breiterer Checkpoint waere heute schlicht nicht ladbar.

**Daraus die Auflage fuer b04, damit sie nicht erst im Lauf auffaellt:** faellt
die Wahl auf den CONV-Zweig, gehoert ein kleiner Bau davor -- zwei Flags,
beide Werte ins Checkpoint-Dict, Ableitung beim Laden nach dem Muster von
`hidden_size`/`planes_channels`, dazu ONNX-Export und Paritaets-Gate. Faellt
sie auf `hidden_size`, ist b04 ohne Bau fahrbar. **Welcher Zweig die
interessantere Breite ist, ist NICHT entschieden** -- inhaltlich spricht fuer
den Conv-Zweig, dass die raeumliche Struktur (Spalten, Nachbarschaften) genau
dort verarbeitet wird und der Kampagnen-Engpass raeumlich ist; fuer
`hidden_size` spricht, dass es null Bauarbeit kostet. Beides ist eine
EINSCHAETZUNG, keine Messung.

**Unveraendert gilt par.5:** das Kostentor kommt ZUERST -- Wanduhr je Zug
gemessen, Frontier auf gleiche Wanduhr je Partie normiert. Eine Breite, die
ihr Sim-Budget unter die Arena-Aufloesung druckt, faellt aus der Frontier und
wird berichtet, nicht durch Budget-Aufstockung geheilt.

## par.11 v23-b02 IST GEBAUT -- und sein Kandidat ist `_brierbest` (2026-08-31)

**Der Kaltstart-Arm steht.** Early Stop nach Epoche 15 von 40, Laufzeit
**4,22 h** (Manifest `models/manifest_train_v23-b02_20260831_170152.json`),
davon 32 s Datenaufbau, weil der Fenster-Cache von b01 traf.

**Damit ist die par.9-Einschaetzung gemessen und BESTAETIGT, in der starken
Form:** ein Kaltstart auf dem vollen Fenster kostet mit stehendem Cache nicht
etwa gleich viel wie der Warmstart, sondern WENIGER -- 4,22 h gegen b01s
5,97 h. Die in par.9 als fehlend markierte Gegenzahl (Warmstart auf vollem
Fenster) liefert b01 damit ebenfalls.

**Checkpoint-Auswahl (Registrierung in `PREREG_v23_window.md` par.2g/par.2h):**
`_best` gegen `_brierbest`, beide @400, 33:47 aus 40 Paaren, SPRT H0,
Vorzeichentest p = 0,189, gepaarte Differenz -0,350 [-0,791, +0,091], Punkte
37,53 gegen 42,33. Nach der vorab registrierten Regel (interne Auswahl, kein
Tor -- ohne Verdikt entscheidet der Punktschaetzer) ist der Kandidat des Arms
**`v23-b02_brierbest`**, obwohl er aus Epoche 1 stammt.

**Was damit noch NICHT gemessen ist:** die Arm-Frage selbst. `v23-b02_brierbest`
gegen `v23-b01_brierbest` (Warm gegen Kalt, ein Faktor, dasselbe Fenster)
steht aus. Und die Frontier misst dieser Arm ohnehin nicht -- dafuer ist b04
zustaendig (par.10), dessen Breiten-Entscheid weiter beim Nutzer liegt.

## par.12 WARM GEGEN KALT GEMESSEN: gleich stark, aber NICHT gleich gebaut (2026-09-01)

Die Arm-Frage aus par.9/par.10 ist gefahren: `v23-b02_brierbest` (Kaltstart)
gegen `v23-b01_brierbest` (Warmstart), beide @400, **dasselbe Fenster, ein
Faktor**. Gepaart mit getauschten Rollen auf DENSELBEN Seeds (Basis 20260980,
2 x 80 Partien, `paired_arena_env_ab --log-games`, threads 10), wie der
Tor-2b-Praezedenzfall.

**Staerke: kein Unterschied.**

```
b01 85 : 75 b02 aus 160 Partien
Paare: b01 beide 26, geteilt 33, b02 beide 21
gepaarte Differenz +0,125, 95%-KI [-0,212, +0,462]
Vorzeichentest auf 47 informativen Paaren: p = 0,56
Punkte 47,04 gegen 44,04, Margin +3,01
```

**Spalten: Faktor 3,7 -- und zwar in BEIDEN Rollen** (`arena_column_probe`,
160 von 160 Partien nachspielbar, 0 Divergenzen):

| Lauf | b01 | b02 |
| --- | --- | --- |
| A = b02 | 0,625 (SE 0,086) | 0,125 (SE 0,037) |
| A = b01 | 0,613 (SE 0,086) | 0,212 (SE 0,046) |
| Mittel | **0,619** | **0,169** |

**Das ist der Befund: derselbe Korpus, dieselbe Breite, dieselbe Staerke --
und trotzdem baut der Kaltstart kaum Spalten.** Die Deutung "der Korpus
wirkt" (par.2b des Fensters, b01 gegen den Champion) ist damit zu praezisieren:
der Korpus allein reicht NICHT. Was b01 traegt, kommt aus dem Warmstart, also
aus der Linie v22-b05, die bereits auf dem Spaltenkorpus trainiert war.

**Der Konfundierer, und er ist ernst:** b02s Kandidat ist sein
BRIERBESTER Checkpoint, und der liegt bei **Epoche 1** (par.2g des
Fensters). Ein praktisch untrainierter Policy-Kopf wuerde ebenfalls wenige
Spalten bauen -- ohne dass der Startmodus etwas damit zu tun haette. Die
interne Checkpoint-Arena hat `_brierbest` zwar vor `_best` gesetzt (47:33),
aber nicht signifikant (p = 0,19), und sie hat auf SIEGE geschaut, nicht auf
Spalten.

**Vorab registrierte Aufloesung (gefahren im selben Zug):** DIESELBE Arena
noch einmal, nur mit `v23-b02_best` statt `_brierbest` -- gleicher Gegner
(b01), gleicher Seed 20260980, beide Rollen, `--log-games`, danach
`arena_column_probe`. Faellt `_best` deutlich hoeher aus, war es der
Checkpoint; bleibt er unten, ist es der Startmodus.

**Warum diese Bauform und nicht das argmax-Instrument** (das zuerst hier
stand): die Zahl muss mit den 0,619 gegen 0,169 vergleichbar sein, die die
Frage aufgeworfen haben -- dasselbe Instrument, derselbe Gegner, dieselben
Seeds. Ein Self-Play-Wert waere mit den Tor-2a-Zahlen vergleichbar, aber nicht
mit dieser Messung, und er kostet das Doppelte (2 x 200 Partien gegen
2 x 80).

**Was in beiden Faellen schon feststeht:** ein Kaltstart auf dem vollen
Fenster ist billiger (4,22 h gegen 5,97 h, par.11) und gleich stark -- aber er
ist KEIN Ersatz fuer die Linie, solange die Spalten das Ziel sind.
Artefakte: `paired_arena_env_warm_vs_cold_b0{1,2}first.json`,
`warm_vs_cold_columns_b0{1,2}first.json`.

## par.13 KONFUNDIERER AUSGERAEUMT: es ist der Startmodus, nicht der Checkpoint (2026-09-01)

Dieselbe Arena noch einmal, nur mit `v23-b02_best` statt `_brierbest` --
gleicher Gegner, gleicher Seed 20260980, beide Rollen, `--log-games`.

**Staerke:**

```
b01 92 : 68 b02_best aus 160 Partien
Paare: b01 beide 26, geteilt 40, b02 beide 14
gepaarte Differenz +0,300, 95%-KI [-0,005, +0,605]
Vorzeichentest auf 40 informativen Paaren: p = 0,081
Punkte 45,38 gegen 38,34, Margin +7,03
```

**Spalten je Partie und Seite:**

| Vergleich | b01 | b02-Checkpoint |
| --- | --- | --- |
| gegen `_brierbest` (Epoche 1) | 0,619 | **0,169** |
| gegen `_best` | 0,563 | **0,225** |

**Damit ist die Frage entschieden: der Checkpoint erklaert es nicht.** Der
Wechsel von Epoche 1 auf den besten Checkpoint hebt den Spaltenbau von 0,169
auf 0,225 -- eine Bewegung in der erwarteten Richtung, aber sie schliesst
nicht einmal ein Fuenftel der Luecke zu b01s rund 0,6. **Beide** b02-Staende
bauen rund ein Drittel dessen, was der Warmstart baut.

**Der Befund lautet also:** auf DEMSELBEN Fenster, mit DERSELBEN Breite, bei
statistisch nicht unterscheidbarer bis leicht unterlegener Spielstaerke baut
ein Kaltstart nur ein Drittel der Spalten. Das Spaltenwissen sitzt nicht im
Korpus allein, sondern in der LINIE -- b01 erbt es aus v22-b05, das seinerseits
auf dem Spaltenkorpus trainiert wurde.

**Nebenbefund, konsistent mit der Checkpoint-Arena:** `_best` steht gegen b01
schlechter da als `_brierbest` (68 gegen 75 Siege), was die dortige Auswahl
(47:33 fuer `_brierbest`) im Vorzeichen bestaetigt -- diesmal aus einer
unabhaengigen Stichprobe.

**Was das fuer die Kampagne heisst** (Deutung, ausdruecklich als solche
markiert): ein Kaltstart ist billiger und kostet keine Staerke, aber er
verliert die strukturelle Eigenschaft, um die der ganze Zyklus gefuehrt wird.
Wer die Spalten will, faehrt Warmstarts -- und die naechste Generation muss
sich fragen, ob der Korpus die Eigenschaft ueberhaupt LEHRT oder sie nur
ERHAELT.
