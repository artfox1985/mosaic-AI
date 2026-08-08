# Vorregistrierung Task #36: Saettigt der Value-Kopf ueber die Spielzahl?

**Angelegt 2026-08-05, VOR jedem Lauf.** Nutzer-Entscheid gleichen Tags:
die v20-Kampagne startet erst, wenn Spiel- und Sim-Budget belegt sind --
#36 liefert die Spielzahl-Seite und liegt damit auf dem KRITISCHEN PFAD.
Regeln nach Sichtung von Zwischenergebnissen nicht mehr aenderbar.

## Frage

Wird der Value-Kopf mit mehr Self-Play-Partien weiter besser (dann sind
mehr Partien der billigste Value-Hebel), oder saettigt er wie die Policy
(dann kann das v20-Budget sinken oder in Qualitaet fliessen)?

## Warum das jetzt sauber messbar ist (und vorher nicht)

- Mass: **Brier gegen den ROHEN Ausgang** (`wdl_outcome`) -- das einzige
  unkontaminierte Value-Feld im Bestandskorpus (Audit 2026-08-05,
  Befund 1). Kein v20 noetig.
- Ziel: `--value-head wdl --wdl-hard-only` -- trainiert ohne den
  Alt-Netz-Bootstrap, also die sauberste heute verfuegbare Konfiguration.
  (Sollte das #34-Verdikt fuer v20 eine ANDERE Zielkonfiguration waehlen,
  wird die Kurve dort einmal nachgeprueft -- die FORM-Frage "saettigt er?"
  gilt als robust gegenueber der Blend-Wahl, das ist eine benannte
  Annahme dieser PREREG.)

## Design

- **Festes, arm-uebergreifendes Validierungsset**: die bestehenden 90
  Val-Dateien des 900er-Fensters (Seed 20260707-Split) sind fuer ALLE
  Groessen ausgeschlossen und dienen als gemeinsames Messset (~900
  Partien). NICHT pro Groesse neu splitten -- sonst misst jede Groesse
  auf einem anderen Set.
- **Trainingspools**: aus den verbleibenden 810 Dateien stratifiziert
  (Generationen-Anteile erhalten, Muster `train_corpus_dose.py`):
  **202 / 405 / 810 Dateien** (Viertel / Haelfte / voll).
- **Seeds**: je Groesse 3 gepaarte Seeds (2, 3, 6 -- Lehre
  [[project-training-seed-variance]]; volle 6 nur, falls die Kurvenform
  zwischen den Seeds widerspruechlich ist).
- Warm-Start `v19_2d_best`, Champion-Rezept (lr 5e-5, cosine,
  `--select-by-brier`, doppeltes Early Stopping), `VALUE_WEIGHT=0,2`.

**AMENDMENT 2026-08-05, VOR dem ersten Lauf** (das #34-Verdikt fiel
zwischen PREREG und Start): Ziel-Konfiguration = **`--value-head wdl
--wdl-bootstrap-destretch`** (die beschlossene v20-Konfiguration) statt
`--wdl-hard-only` -- gemessen wird die Saettigung des Ziels, das v20
tatsaechlich trainiert. Der rohe `wdl_outcome` bleibt die BEWERTUNGS-
Groesse (Brier), unveraendert sauber.
**Umsetzungsdetails, vorab festgelegt**: (a) Messset-Erzwingung ueber
EXTERNE Brier-Auswertung: die 90 Val-Dateien (Seed-20260707-Split) sind
aus ALLEN Trainings-Sandboxes ausgeschlossen; Brier je Checkpoint
(brierbest + final) wird nach dem Training per separatem Skript auf
diesen 90 Dateien gerechnet (train.py-interner Val-Split steuert nur das
Early Stopping und darf je Groesse abweichen). (b) Subsets als
Hardlink-Sandboxes (`data_t36_202/`, `data_t36_405/`) nach dem
`train_corpus_dose.py`-Muster, stratifiziert per Praefix, Ziehungs-Seed
20260805. (c) Effektive Trainingsmengen sind ~90% der Poolgroessen
(interner Val-Split) -- proportional ueber alle Groessen, daher fuer die
Kurven-FORM unerheblich. (d) Namen `t36_g<pool>_s<seed>`.
- Je Groesse eigener HDF5-Cache (Partien-Ebene; Sample-Subsampling ist
  ungueltig, weil das Value-Ziel per Partie definiert ist).

## Auswertung (VORAB festgelegt)

1. **Primaer: Brier-Kurve** ueber die drei Groessen, je Punkt Mittel der
   3 Seeds, Unsicherheit per Bootstrap ueber PARTIEN des Messsets
   (Block-Lektion; Aufloesungsgrenze ~0,005 ist dokumentiert und Teil
   der Interpretation).
2. **Sekundaer: Policy-Kurve** (beide Orakel-Metriken) auf denselben
   Armen -- die beiden Saettigungskurven werden uebereinandergelegt.
   Entscheidend ist die FORM, nicht der Absolutwert.
3. **Leseregeln**:
   - "Value-Kopf ist spielhungrig" = Brier(810) besser als Brier(202)
     ausserhalb des Bootstrap-KI UND monotone Ordnung der drei Punkte
     in >=2 der 3 Seeds.
   - "saettigt" = Differenz innerhalb des KI oder nicht monoton.
   - Kein Arena-Gating in #36 (es wird eine MESSGROESSE erhoben, kein
     Kandidat gekuert); jede Budget-Entscheidung fuer v20, die daraus
     folgt, wird separat dokumentiert.
4. **Konsequenz-Vorbindung**: "spielhungrig" stuetzt PCR-Bedingung (ii)
   und spricht fuer volles/hoeheres v20-Spielbudget; "saettigt" schliesst
   PCR endgueltig (Bedingung ii verletzt) und erlaubt ein kleineres
   v20-Spielbudget zugunsten von Qualitaet (Sims) oder Wandzeit.

## Kosten

2 zusaetzliche Caches (~50 min je) + 9 Trainings (~35 min je) ≈ ~7h,
parallelisierbar mit laufenden Arena-Messungen (GPU vs CPU getrennt).
Start: nach dem #34-Verdikt (Zielkonfiguration bestaetigt), Caches
duerfen frueher gebaut werden (zielunabhaengig).

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- die Brier-Auswertung ueber
die 202/405/810-Dateien-Pools zeigt monotone Verbesserung in allen 3
Seeds (0,19934 -> 0,19813 -> 0,19695, log-linear, ~0,0012 Brier je
Verdopplung), ausserhalb des Bootstrap-Konfidenzintervalls -> der
Value-Kopf ist "spielhungrig" gemaess der vorregistrierten Leseregel
(saettigt NICHT). Die Policy-Gegenkurve bleibt dagegen flach
(daten-gesaettigt). Konsequenz: das v20-Spielbudget wurde NICHT gekuerzt;
PCR-Bedingung (ii) damit erfuellt. Belegstelle: archive/history.md,
Abschnitt "Task #36 ERGEBNIS (2026-08-06): Value-Kopf saettigt NICHT --
Spielzahl ist ein echter Hebel", Zeile ~9965-9998.
