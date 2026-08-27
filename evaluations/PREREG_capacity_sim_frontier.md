<!-- STATUS: OFFEN | Frage: Ist das Netz fuer sein Rechenbudget zu KLEIN -- und wo liegt bei fixem WANDUHR-Budget das Optimum aus Netzgroesse (Rumpfbreite) und Sim-Budget? | Beleg: ENTWURF 2026-08-27 aus dem Recherche-Abgleich, Nutzer-Entscheid ueber den Bau offen, NICHTS GEBAUT und nichts gemessen. Quellen: RESEARCH_alphazero_improvements_2026-08-01.md Fund 11 (Jones 2021, Train- und Test-Compute log-linear eintauschbar; empfiehlt ausdruecklich eine kleine FRONTIER statt Einzel-A/Bs) und Fund 12 (Neumann/Gros; Elo als Potenzgesetz in der Parameterzahl, optimale Netzgroesse waechst mit Compute^0,63, Kernaussage "die meisten publizierten AlphaZero-Agenten sind fuer ihr Compute-Budget zu klein" -- mit dem Gegenbefund Inverse Scaling, groesser ist nicht garantiert besser). Warum die Registrierung JETZT faellt und nicht beim Lauf: nur ein KALTSTART oeffnet das Rumpfbreiten-Fenster; ein Warmstart sperrt es per Checkpoint-Kompatibilitaet. Das Head-Widening-Negativ ([[project_stage2_value_head_capacity_test]]) betraf NUR den Value-Kopf, nicht den Rumpf, und schliesst diesen Arm daher nicht. Realistisch fahrbar erst beim NAECHSTEN Kaltstart -- registriert werden muss es jetzt, sonst ist das Fenster wieder zu, unbemerkt. KOSTENTOR PFLICHT: CPU-Inferenz-Gegenrechnung, 2D kostet heute bereits Faktor 1,8 ([[project_2d_inference_optimization]]). -->

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
