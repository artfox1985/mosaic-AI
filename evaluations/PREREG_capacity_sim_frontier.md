<!-- STATUS: OFFEN | Frage: Ist das Netz fuer sein Rechenbudget zu KLEIN -- und wo liegt bei fixem WANDUHR-Budget das Optimum aus Netzgroesse (Rumpfbreite) und Sim-Budget? | Beleg: Kaltstart-Arm v23-b02 GEBAUT (par.11): 4,22 h gegen b01s 5,97 h, also BILLIGER als der Warmstart; Kandidat `_brierbest` (33:47, SPRT H0). Die Frontier misst das nicht -- offen bleiben die Arm-Frage b02 gegen b01 und der Breiten-Arm b04, dessen Zweig der Nutzer waehlt (par.10: `hidden_size` ohne Bau, Conv-Zweig braucht Flags plus Checkpoint-Ableitung). Kostentor Pflicht und zuerst (par.5). -->

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
