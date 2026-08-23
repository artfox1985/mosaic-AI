# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Abgeschlossenes liegt in
**`../archive/history.md`**.

---

## DAS ZIEL (Leitstern — Nutzer-Auftrag 2026-08-17: bei jeder Priorisierung im Kopf behalten)

> *"das netz spielt die basis an sich schon gut, aber nimmt keine ruecksicht auf
> die wertungsplatten. das wollen wir via injektion -> selfplay -> ownership
> head in den griff bekommen. dann sind nochmal je partie 10 punkte und mehr
> drinnen"*

1. **Ziel: ein staerkerer Spieler**, gemessen am **direkten Duell** gegen den
   Champion. Zielgroesse: **"Sieg mit vielen Punkten"** — nicht Punkte allein.
2. **Hebel: der Plattenblick.** Die Grundmechanik spielt das Netz kompetent und
   laesst 10+ Punkte je Partie liegen.

**Klausel, die schon sechs Vorschlaege aussortiert hat:** ein Plattenzuwachs,
der Siege kostet, ist KEIN Erfolg. Ein Zuwachs bei den Zaehl-Kriterien (k3/k4)
zaehlt nicht — gefragt sind die konjunktiven k1/k2/k5.

**Vor jeder Arbeit fragen: was traegt das dazu bei?** Ownership-Kopf, Korpus,
Regler, Konjunktionsterme, LR-Schedules, Traeger-Manifeste sind WERKZEUG ohne
Eigenwert. Am 2026-08-17 wurde ein Legacy-Test gestrichen, weil die Antwort auf
diese Frage "nichts" war.

---

## FOKUS-REGEL: NUR k1 (Nutzer-Entscheid 2026-08-18)

> *"mir kommt vor du switcht wild zwischen den wertungsplatten analysen herum.
> wir sollten uns wirklich mal nur auf eine wertungsplatte fokussieren"*

**Bis auf Widerruf wird ausschliesslich k1 (Vertikale Reihen, 7 Pkt je volle
Spalte) bearbeitet.** Warum k1 und nicht eine andere — alles gemessen:

| | |
|---|---|
| Wert | 7 Punkte je Spalte, 6 Geometrien |
| Kosten | **keine** — innerhalb des k1-Bauer-Arms +7,86 Gesamtpunkte, davon 7,02 aus der Platte, Rest +0,84 |
| Synergie | Platzierung zahlt den vertikalen Lauf getrennt (`round_end.rs:366`), Spaltenbau liegt auf derselben Achse wie normales Spiel |
| Luecke | Netz 20/156 Partien (13 %), Bauer 419/1000 (42 %) |
| Label | Vollendbarkeits-Sperre bestanden, traegt in Runde 3-5 |

**Was das AUSSCHLIESST**, obwohl dazu Befunde vorliegen: k2 (Diagonalen), k4
(Aeussere Felder), k5 (Eckplatten), k6 (Spezialfelder). Ihre Messungen bleiben in
den Preregs erhalten und gelten weiter, werden aber **nicht weiterverfolgt**. Erst
wenn k1 traegt, kommt k2 — so war es in
`PREREG_plate_policy_supervision.md` registriert und so bleibt es.

**Konkret heisst k1-only:**

- Erfolgsregeln nennen nur k1. (Die registrierten "k1 oder k2"-Klauseln bleiben
  gueltig, werden aber auf k1 gelesen — die strengere Lesart.)
- Der Verbraucher wird nur mit `MOSAIC_OWNERSHIP_GEW` auf k1 gefahren.
- Nebenbefunde zu anderen Kriterien werden protokolliert und NICHT verfolgt.

**Der Anlass war Drift, nicht Erkenntnis:** am 2026-08-18 sind aus k1-Messungen
heraus Analysen zu k6 (Spezialkuppel-Platzierung, Stapel-Ziehungen), k5 und k4
entstanden. Alle drei lieferten echte Befunde — und keiner davon brachte k1 voran.

---

## STAND JETZT (2026-08-23)

**Champion unveraendert:** `v21_2d_brierbest`, Elo **1215** [1170, 1259] auf
der neuen R5-Fix-Leiter (`PREREG_round5_minfix_elo_reset.md` par.5). Kanten
ueber die Fix-Grenze hinweg nie mischen; Alt-Register in
`../archive/elo_history_pre_r5fix.csv`.

**Die Plattenblick-Kette hat drei Nullbefunde in Folge – alle ohne
Staerkekosten:**

| Arm | Verdikt | Beleg |
|---|---|---|
| Ownership-VERBRAUCHER (Produktform, Konjunktionsform, hoerbare Skala, neues Ziel) | in allen gemessenen Formen negativ | `../archive/history.md`, Kapitel 2026-08-18..08-23; `PREREG_reachability_target.md` par.14/16 |
| Asymmetrisches Curriculum | kein Signal (k1-Rate 12,2 % = Grundrate), kein Siegverlust | `PREREG_asymmetric_curriculum.md` par.14-16 |
| Startpositions-Seeding, Dosis k=6 | kein k1-Signal (14,1 % gegen Schwelle 22 %), kein Staerkepreis | `PREREG_start_position_seeding.md` par.4c |

**Das erste POSITIVE Zustandssignal der Kette** steht daneben und ist der
Grund, warum der Strang nicht geschlossen ist: die Sibling-Sonde (par.4d)
liefert Tau(Value~k1-Puffer) **seedk1 +0,140 gegen N -0,185**,
Vorzeichentest 17/5/11, **p = 0,017** – auf denselben 33 Stellungen, auf
denen der Asym-Arm nicht signifikant war (`seedk1_value_sibling_check.json`).
**Mechanik bewegt sich, Verhalten (noch) nicht.** Das ist konsistent mit der
Diagnose „die Suche fragt den Kopf zu selten" (`PREREG_r5_solver_split.md`
par.3) und macht den Such-Hebel zum naechsten Kandidaten, nicht das naechste
Ziel-Experiment.

**Abgenommen und aktiv: die R5-Loeser-Trennung.** `round5_anchor.rs` ist
eingefroren und in allen drei Sucheinstiegen verdrahtet (geprueft
2026-08-23: `engine/src/mcts.rs:746`, `:777`, `:796`, Modul
`engine/src/lib.rs:33`); Paritaets-Hash 8c6684ff haelt VOR und NACH dem
Wheel-Neubau, Suite 484/0 (`logs/cargo_suite_r5split_20260823.log`,
`logs/r5split_*_20260823.log`). **Die Elo-Leiter ist ab jetzt gegen jede
R5-Weiterentwicklung immun** – der Netz-Loeser darf sich entwickeln, ohne
den Anker zu entwerten.

## NAECHSTE SCHRITTE – ALLE OFFEN, ALLE NUTZER-ENTSCHEID

Der NAECHSTE Schritt je Strang ist Nutzer-Entscheid; einzelne Straenge tragen
bereits gebaute/gemessene Teilergebnisse (siehe jeweilige Zeile). Umfaenge und
Schwellen fuer noch nicht begonnene Teile stehen je Prereg und sind vor
Baubeginn freizugeben.

| Strang | Datei | Zuschnitt |
|---|---|---|
| **Such-Hebel: Implicit-Minimax-Backup** | `PREREG_implicit_minimax_backup.md` | **GEMESSEN 2026-08-23, ERFOLG nach vorregistrierter Lesart** (par.2b): kein Staerkeverlust (304 vs 296/407 n.s.), Score-Level signifikant +2,77 (Block-t +3,83), **k1 9,0 % -> 16,0 % (+7,0 pp, p=0,090)** -- die groesste je gemessene k1-Bewegung der Netz-Seite, konsistent mit par.4d (Kopf traegt Signal, Suche macht es jetzt wirksam). Caveat: Instrument misst gegen Heuristik. Folgeschritte (alpha-Sweep, Knopf im Self-Play) = Nutzer-Entscheid |
| **R5-Netz-Loeser + R5-Value-Kalibrierung** | `PREREG_r5_solver_split.md` par.2 a/b/c, Teil B | Netz-Loeser-Arme (Budget, Policy-Sortierung, spaeter Value-Korrekturterm; je per-Agent verdrahtet, NIE per Env-Knopf) und der Vierer-Kopf-Vergleich. Zielmetrik der Kalibrierung: `r5_value_calibration`-Steigung, heute 0,06-0,09 statt ~1. **Arm 3 des Vierer-Vergleichs braucht ein b-Serie-Modell mit geprueftem Traeger-Status** – der Ownership-Ausgang des Champions ist untrainiert (Beweiskette par.3a) |
| **Seeding-Folgearm: Dosis** | `PREREG_start_position_seeding.md` | k=6 war die erste Dosis; hoehere Dosis ist der naheliegende Folgeschritt, aber nicht registriert |
| **UVFA-Regime-Eingabe** | `PREREG_uvfa_plate_regime.md` | Folge-/Kombinationsarm; par.8: Conditioning-Dropout + Leakage-Waechter sind PFLICHT. par.7-Entscheid steht aus |
| **Reihenfolge Seeding-Kette gegen R5-Strang** | – | entscheidet der Nutzer beim Aufgreifen |
| **Agenten-Kapselung (AgentSpec statt Prozess-Global)** | `PREREG_agent_encapsulation.md` | **Welle 1 (Pilot) GEBAUT UND ABGENOMMEN 2026-08-23** (par.4a): `SearchConfig`-Geruest + Migration von `MOSAIC_IMPLICIT_MINIMAX_A`, per-Seite-Spec (`spec`/`spec_a`+`spec_b`) an `net_arena_match`/`net_vs_net_arena_match`/`net_self_play_games`. Suite 498/0/26, Paritaets-Hash haelt, Spec==Env-Default bestaetigt. Naechster Schritt: die eigentliche Alpha-Sweep-Messung (par.6a Vorab-Lesart, Champion vs. Champion+alpha=0,2 netz-gegen-netz auf den 407 Seeds) -- noch nicht gelaufen. Weitere Knopf-Wellen (Schritt 2) bleiben Nutzer-Entscheid |

**Geschlossen ohne Messung (nicht neu vorschlagen):** die
Q-Skalierungs-Option (Aera-Nachmessung `gumbel_scale_calibration_v21.json`:
q:prior 1,47, kein mctx-Faktor-14; c_scale-Senkung hauseigen mit -13 % Score
vorbelastet) und jeder Suchparadigmen-Wechsel (beide externen Recherchen
`RESEARCH_plate_intent_external_2026-08-22.md` und
`RESEARCH_search_alternatives_external_2026-08-22.md`: additive Hebel zuerst,
kein Beleg-Fall fuer einen AB-Umbau).

---

## OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Stand |
|---|---|
| **Gewichtsarm 4,0** | Vorabregel hat ihn freigegeben (`PREREG_ownership_weight_new_window.md` par.7); Nutzer-Entscheid 2026-08-17: **weiter hinten geparkt** |
| **Stoerungs-Baustein Stufe 2** | gehoert zum **Moon-Order-Kopf**, keine Einzelentscheidung mehr |
| **Korpus mit hoeheren Sims nachgenerieren** | **ABGELEHNT** (Nutzer 2026-08-17) — nicht neu vorschlagen |
| **Fester Bewertungssatz** | Bauer-Satz: 300 Dateien / 3000 Partien in `data/holdout/`, fertig 2026-08-18. Details (Zusammensetzung, Abnahme, Herkunft) siehe `../archive/history.md`, Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)". |
| **Push** | NIE ohne ausdrueckliche Nutzer-Anweisung (Nutzer-Regel 2026-08-20); Stand wird als "n Commits voraus" gemeldet |
| **`logs/nacht_20260820.log`** | darf weg (Nutzer 2026-08-22); die Zwangsseiten-Map ist extrahiert nach `data/asym_corpus/zwangsseiten_map.txt`. Loeschung ist Nutzersache |
| **Asym-Korpus** | bleibt LOKAL – Trainingsinput fuer Seeding und UVFA |
| **Ownership-Korpus** | entfernt der Nutzer selbst (5b-Abschluss registriert) |
| **`tools/night_run_20260820.ps1`** | vom Nutzer geloescht, die Loeschung ist noch nicht committet |

## FALLE vom 2026-08-20 — CPU-NEBENLAST VERSTUEMMELT ARENA-PARTIEN

Zwei parallel laufende Arena-Instanzen (je `--threads 10` plus Worker):
derselbe 8-Partien-Smoke lieferte unter Last ZWEI VERSCHIEDENE Ergebnisse
(eine Partie endete 3:1 — offensichtlich abgewuergt), ohne Last dreimal
byte-identisch (auch identisch zum Vortag; das frische Wheel war NICHT die
Ursache, per Dreifach-Vergleich ausgeschlossen). **Regel: Arena-Messungen
laufen EXKLUSIV — keine zweite Arena, keine Sonden mit Suchlaeufen, kein
Training parallel.** Vorflug-Determinismus-Checks zaehlen nur, wenn sie
unter denselben Lastbedingungen laufen wie die Messung selbst (praktisch:
beide exklusiv). Belege: `paired_arena_env_reach_conj_smoke1/2.json`
(unter Last, abweichend) gegen `reach_smoke1/3/4.json` (exklusiv,
identisch).

**KALIBRIERUNGS-SMOKE EINGETAKTET (Nutzer 2026-08-22, Vorab-Regel VOR
der Messung):** Die strenge Fassung ("gar nichts parallel") wird an der
leichtesten Lastklasse kalibriert. Aufbau: derselbe 8-Partien-Smoke
zweimal EXKLUSIV (Basislinie, muss byte-identisch sein, sonst Abbruch),
dann zweimal unter definierter Ein-Kern-Nebenlast (Endlosschleife, die
Asym-Pickles laedt -- exakt die Lastklasse des Vorfalls vom 2026-08-22,
der einen Arena-Neustart kostete). Regel: alle vier byte-identisch =>
leichte Single-Thread-IO-Jobs (keine Suchlaeufe, kein Training) sind
kuenftig neben Arena-Messungen erlaubt; irgendeine Abweichung => die
strenge Regel bleibt. Ergebnis wird hier nachgetragen.
**ERGEBNIS (2026-08-22): BESTANDEN -- alle 4 Laeufe byte-identisch**
(SHA256 8837a35b... ueber cal_smoke_a1/a2/b1/b2; Stoerlast = Endlos-
Pickle-Loader, PID-kontrolliert). Damit gilt die kalibrierte Fassung:
Single-Thread-IO parallel zu Arena-Messungen erlaubt, Suchlaeufe/
Training/Mehrkern-Last weiterhin verboten. Der Not-Deckel-Umbau
(Zielbild unten) bleibt Vorrat ohne Dringlichkeit.

**ZIELBILD NOT-DECKEL (Nutzer-Entscheid 2026-08-22, Bauplan, nichts
gebaut):** Wanduhr-Deckel sollen Ergebnisse nie mehr VERAENDERN
koennen. Zwei Schichten: (1) alles Algorithmische bekommt
deterministische ARBEITS-Deckel (Knoten/Samples/Tiefe, Vorbild
round5-NODE_BUDGET) -- byte-identisch unter jeder Last; (2) die Wanduhr
bleibt nur als aeusserster Wachhund gegen echte Haenger und darf
ausschliesslich TOETEN und als ungueltig markieren (Partie wird
nachproduziert bzw. das Seed-PAAR faellt aus gepaarten Messungen),
nie beschneiden-und-weiterlaufen; jedes Feuern mit Deckel-Name im
Ergebnis-JSON gezaehlt. Nebeneffekt: wuerde auch die sync/async-
Trainingsziel-Divergenz (Async-Gate-B-Rest) aufloesen. Gebaut wird
erst, wenn der Smoke oder ein Vorfall zeigt, dass ein Deckel bindet;
erster Schritt waere dann Deckel-Telemetrie zur Taeter-Identifikation.

---

---

## TASK-INDEX (nur OFFEN/LAUFEND)

| Task | Status |
| --- | --- |
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: braucht >=6 arena-entschiedene Paare (Stand ~3); Kandidaten-Metriken werden je Gating mitgefuehrt. `PREREG_post34_package.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |
| `stack_top_feature` | geparkt, Arbeitskreis "Spaeter", gleiche Stufe wie #38 (Nutzer-Entscheid 2026-08-20). Ziel ist SICHTGLEICHHEIT Netz/Spieler, kein Staerke-A/B. `PREREG_stack_top_feature.md`, Details unten |

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT

**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die v21-Task-Queue.**
`PREREG_v22_window.md`: gleiche Form wie v21 (29.450 gesamt), juengster
Value-Posten 3.550 v19wdl-Rest + 1.450 v19wdlsw, Schwarm bleibt 74 %.
**Ab v22 ist die Rotationsregel stationaer.** Gating-H0-Vorbehalt: neuer
Batch desselben Generators braucht Suffix (`v20wdlb`).
**Hinweis 2026-08-14**: der Ownership-Korpus ist KEIN v22-Fenster -- er liegt
ausserhalb der Rotation (`data/ownership_corpus/`, additiv via
`--extra-data-dir`) und aendert diese Halde-Entscheidung nicht.

---

## GELTENDE REGELN (kompakt)

- **Das Punkte-Ziel ist NICHT `tanh(own/50)` (geprueft 2026-08-23).** Zwei
  Irrtuemer, die zusammen drei Dokumente falsch gemacht haben; beide am Code
  nachgesehen, beide korrigiert.
  1. **`points_val` ist ueberwiegend TD-geblendet.** Nach der Formelzeile
     (`neural_net.py:1647`) greifen zwei Ueberschreibungen: `:1704` setzt bei
     vorhandenem `rtv` komplett auf `own_rtv = 2·rtv[p] − 1`, `:1717`
     blendet `TD_LAMBDA·(2·bv[p] − 1) + (1 − TD_LAMBDA)·points_val` mit
     `TD_LAMBDA = 0.5` (`:717`). Kein Schalter unterdrueckt den TD-Blend
     (`value_target_variant` greift nur am rtv-Zweig).
     **Was da eingemischt wird, ist die Ausgabe des VALUE-Kopfes, nicht des
     Punkte-Kopfes:** `bootstrap_value` entsteht ueber
     `self_play.rs:1737` -> `round_transition_deep.rs:852` ->
     `net_mcts::net_leaf_eval` -> `net_mcts.rs:2411`
     `blended_leaf_win_prob(&value, ...)`, bei `w=0` also
     `calibrate_win_prob_with(value_to_win_prob(value))`. Seine Bedeutung
     haengt am Value-Kopf des GENERATORS: bei WDL-Kopf ist
     `value_out = 2·p_win − 1` (`neural_net.py:2503`), also eine
     Gewinnwahrscheinlichkeit; beim tanh-Kopf davor ist es
     `tanh((own−opp)/50)`, also eine Punkte-MARGE. Beides ist um null
     zentriert, beides ist NICHT der eigene Endstand `tanh(own/50)` -- die
     Etikettierung "Gewinnwahrscheinlichkeit" gilt aber nur fuer die
     WDL-Aera (v19wdl aufwaerts), nicht fuer v18.
     Gemessen (je eine Datei pro Generation): `round_transition_value` in
     v18/v19wdl/v19wdlsw/v20wdl/v20wdlsw **nirgends**, `bootstrap_value` in
     **82,8 bis 84,0 %** der Datensaetze. Nur Runde 5 (kein Uebergang)
     traegt das reine `tanh(own/50)`. **Folge: jede Aussage ueber die
     Verteilung des Punkte-Ziels oder ueber die Bedeutung der Kopf-Ausgabe
     muss diesen Blend mitrechnen.** Eine nachgebaute Formel misst eine
     Groesse, die kein Training je gesehen hat.
  2. **Task #12 lief NICHT am Differenzziel, sondern eigenseitig.** Der
     Verteilungskopf trainiert auf `targets_points` (`train.py:1073`), und
     `points_val` war seit db73122 (2026-07-06, "Differenzbildung durch
     getrennt gesaettigte Terme ersetzt") bis Schema 20 (08c565d,
     2026-08-10) `tanh(own/50) − 0,1·tanh(opp/50)`. Auf der Differenz liegt
     `val`, das Value-Ziel. **Folge fuer die Wiederaufnahme:** der in
     `PREREG_points_dist_bin_scale.md` behauptete Bin-Skalen-Defekt lag in
     #12 bereits vor, und die Messung kam flach heraus -- #12 ist damit ein
     Prior GEGEN die Hypothese, nicht ein neutraler Vorlauf.

  Der Irrtum stammt aus `research_value_head_alternatives_DRAFT.md` Z. 7 und
  war von dort nach `docs/concept_distributional_heads.md` und in zwei
  Preregs gewandert. Alle vier Stellen sind am 2026-08-23 korrigiert.

- **NEUER PUSH-BLOCKER seit 2026-08-21 (79de9fa): Rechnerstruktur im
  `pre-push`-Haken.** Wenn ein Push abbricht mit „RECHNERSTRUKTUR in
  gepushten Dateien", ist das kein Defekt, sondern der Waechter: eine
  hinzugefuegte/geaenderte Datei im Push-Bereich enthaelt einen absoluten
  Pfad in ein Nutzerverzeichnis (Windows- wie Git-Bash-Schreibweise), einen
  OneDrive-Pfad in den Dokumente- oder Backups-Ordner, oder den Nutzernamen
  aus der Umgebung. **Das genaue Muster steht ausschliesslich in
  `PRIVACY_PAT` (`tools/hooks/pre-push`)** -- dort als Regex mit
  Zeichenklassen notiert, was es davor bewahrt, sich selbst zu treffen. Wer
  es woanders WOERTLICH hinschreibt, macht diese Datei zum Dauerblocker;
  genau das ist beim ersten Eintragen hier passiert. Das setzt CLAUDE.md
  („Oeffentliches Repo: keine
  Rechnerstruktur", 2026-08-17) durch, das bisher nur ein Pruefbefehl zum
  Selbstausfuehren war. Geprueft wird der GEPUSHTE Stand (nicht der Working
  Tree) und nur A/C/M/R -- die Historie wird nicht umgeschrieben, Alt-Treffer
  blockieren nicht. `CLAUDE.md` ist ausgenommen. Richtige Antwort: Pfad aus
  der Umgebung beziehen (`MOSAIC_PYTHON_DIR`, `MOSAIC_BACKUP_DIR`,
  `MOSAIC_MODELS_DIR`). Nur bei echtem Fehlalarm `git push --no-verify`.
  Kosten < 1 s (gemessen 0,44 s ueber 10 Commits), laeuft VOR der
  `engine/src`-Weiche, also auch bei reinen Doku-Pushes. Details:
  `tools/hooks/README.md`.

  Gleicher Zug: `.git/hooks/pre-push` (tote Alt-Kopie ohne den
  `cygpath`-Fix) geloescht -- aktiv ist ausschliesslich `tools/hooks/` via
  `core.hooksPath`. Und die Golden-Waechter **A1-A4 sind gebaut** (geprueft
  2026-08-21: A2 `engine/src/lib.rs:583`, A3 `engine/src/features.rs:1375`,
  A4 `engine/src/mcts.rs:1271` ff.); die Hook-README behauptete bis dahin
  das Gegenteil.

- **Seed-Skala der Arena bei n=400 (gemessen 2026-08-09)**: dieselbe
  Konfiguration (k=1, Champion@600 vs Heuristik@150dyn) ergab **76,0%**
  mit Basis-Seed 20260820 und **81,75%** mit 20260828 -- **5,75
  Prozentpunkte allein durch den Seed**. Das ist groesser als die
  meisten Effekte, die wir messen (λ, k=2, Denial-Varianten liegen alle
  darunter). Folge: **ungepaarte Vergleiche zwischen zwei Laeufen sind
  wertlos**, auch wenn beide n=400 haben. Jeder A/B braucht identische
  Basis-Seeds im SELBEN Instrument; wo zwei getrennte Laeufe noetig sind
  (unterschiedliche Sim-Budgets), muss der Basis-Seed gleich gesetzt und
  die Paarung ueber den Spielindex selbst gerechnet werden.

- **Champion**: `v21_2d_brierbest` seit 2026-08-09, **Elo 1358**
  [1292, 1434] (Alt-Leiter vor dem R5-Minfix-Reset; gueltige neue
  Leiter: 1215 [1170, 1259], PREREG_round5_minfix_elo_reset par.5 –
  Kanten ueber die Fix-Grenze nie mischen) (Vorgaenger
  `v20_2d_opp_brierbest` 1295). Die
  Erst-Schaetzung nach dem Gating (1416, CI +-92) beruhte auf einer
  einzigen Gegnerkante; mit Anker- und Champion-2-Kante sinkt das
  Niveau auf 1358 und das CI wird 23% enger (+-71) -- der ABSTAND zum
  Vorgaenger (+63) bleibt. Belegt den Wert von
  Promotions-Checkliste Punkt 3+4. Gating 75:45
  (SPRT-H1 nach 60 Paaren, p=0,0059) UND Frisch-Seed-Replikation 97:63
  (H1 nach 80 Paaren, p=0,0095) -- die Fruehstopp-Regel ist damit
  erfuellt. Alt-Messset-Brier 0,18636 vs 0,18749. **Erster Champion aus
  reiner Korpus-Skalierung**: identisches Rezept, +40% Fenster
  (29.450 Partien) von einem staerkeren Generator, plus
  `--endgame-head`. champion.txt gesetzt (wirkt nach Server-Neustart).
  Generator-Naming: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.

- **Fenster-Pinning -- ZWEI Variablen, nicht eine (verschaerft
  2026-08-09 nach einem Beinahe-Fehler)**: Ein Trainingsstart im
  v21-Fenster braucht BEIDE:
  
  ```
  export MOSAIC_DATA_EXCLUDE="$(cat evaluations/v21_exclude_regex.txt)"
  export MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_v21.json"
  ```
  
  **DRITTER Beinahe-Fehler derselben Klasse (2026-08-19): die Regex-Datei
  veraltet.** Das b18-FENSTER (Korpus-Sockel-Linie: b18/b19/b23/b24) schliesst
  zusaetzlich `selfplay_v19wdlsw_` aus — `v21_exclude_regex.txt` enthaelt das
  NICHT. Ein b24-Start mit der txt-Datei lud 3371 statt 2945 Dateien (800
  v19wdlsw zu viel); aufgefallen an der Kompositions-Zeile VOR dem Cache-Bau,
  Lauf gestoppt und neu gestartet. **Regel: das Exclude fuer einen
  Wiederholungs-/Nachfolgelauf IMMER aus dem `data_exclude`-Feld des
  REFERENZ-Manifests ziehen** (materialisiert:
  `evaluations/b18_window_exclude_regex.txt` aus dem b23-Manifest), nie aus
  einer benannten txt-Datei, deren Stand niemand prueft. Fuer die
  b18-Linie gilt zudem `MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_own.json"`.
  
  `MOSAIC_CARRIER_MANIFEST` wurde beim `t_d_vw08`-Start VERGESSEN. Der
  Default ist `policy_carrier_manifest_v20.json`, also ein ANDERER
  Traeger-Satz: der Arm haette mit einer anderen Policy-Maske als
  `t_d_vw04` und als `v21_2d` trainiert und waere als Sweep-Arm wertlos
  gewesen -- ohne Fehlermeldung, nur mit plausiblen Zahlen. Der Lauf
  wurde gestoppt und korrekt neu gestartet; ein angefangener
  Falsch-Cache war noch nicht auf der Platte.
  **Verifikation ist Pflicht und zwar VOR dem Weggehen**: die
  Cache-Zeile muss `📦 Lade HDF5-Cache (2651 Dateien)` lauten.
  Steht dort `Lade Daten aus 2651 Dateien...`, ist der Cache-Schluessel
  anders -- Lauf sofort stoppen und die Ursache klaeren, NICHT einen
  Neubau durchlaufen lassen (er zementiert das falsche Fenster).
  Beweisweg fuer die Ursache (bei Bedarf wiederholbar): Cache-Key aus
  `str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+...+carriers`
  nachrechnen und mit den `data/.cache_*.h5`-Namen vergleichen -- die
  v21-Caches sind `26e304f5d2c7` (train, 2.651 Dateien) und
  `8a04a7143bbe` (val, 294). Merke: der **Cache-Key ist der einzige
  Waechter** ueber die Traeger-Wahl, das Lauf-Manifest protokolliert
  `MOSAIC_CARRIER_MANIFEST` NICHT (`engine_config`/`python_constants`
  waren zwischen richtigem und falschem Lauf identisch).
  Harmlos dagegen: die 55 archivierten v18-Dateien sind seit 10:16 aus
  `data/` heraus, `MOSAIC_DATA_EXCLUDE` schliesst nun 0 statt 55
  Dateien aus -- Split und Dateiliste sind trotzdem BEWEISBAR identisch
  (rekonstruiert und verglichen: 2.651/294 in beiden Faellen gleich).

- **NACHSCHUB BEI GATING-FEHLSCHLAG -- KORRIGIERTE FASSUNG
  (Nutzer 2026-08-09)**: Die Streichung des Nachschub-Ventils vom
  2026-08-07 war **generationsspezifisch** (v20-Zyklus, weil dort eine
  lange Nebentask-Liste offen war) und **KEINE stehende Anweisung** --
  ich hatte sie faelschlich verallgemeinert (auch in
  PREREG_v21_window.md, dort korrigiert).
  **ERSETZUNG (frischer Batch desselben Generators + Rausrotieren einer
  Alt-Generation) ist VERWORFEN** -- Nutzer-Argument, und es ist
  richtig: das ist indirekt mehr Volumen vom SELBEN Champion, waehrend
  die Diversitaet der alten Generationen aus dem Fenster fliegt. Genau
  die Generationen-Spreizung ist aber der Grund, ueberhaupt Alt-Material
  mitzufuehren.
  **Was bleibt: gezielte INJEKTION** (Sockel-Partien dazu, nichts
  verdraengt -- schont die Diversitaet). Bedingungen, damit daraus kein
  "solange nachlegen bis der Kandidat gewinnt" wird:
  
  1. Umfang und Entscheidungsregel VOR der Injektion schriftlich
     (Mini-Prereg), nicht nach dem verlorenen Gating improvisiert.
  2. Einmalig und begrenzt je Generation (Vorschlag: +2.000 Sockel),
     kein iteratives Nachlegen.
  3. Naming: derselbe Generator erzeugt ein Batch mit
     Unterscheidungs-Suffix (`v20wdlb`), sonst Datei-Kollision.
  4. Lesart des Ergebnisses: ein Sieg NACH Injektion belegt "die
     Generation brauchte mehr Policy-Material" -- NICHT, dass eine
     etwaige Rezept-Aenderung des Kandidaten gewirkt hat. Diese
     Unterscheidung muss im Verdikt stehen.
  5. Diagnostischer Rueckenwind erwuenscht (Policy-Wacht: fallen die
     Orakel-Metriken gegen die Vorgeneration, ist die Policy-Klasse der
     belegte Engpass), aber keine harte Vorbedingung -- Nutzer-Entscheid.

- **FENSTERGROESSE: FIXIERTE BASIS, Injektion ist die benannte Ausnahme
  (Nutzer-Entscheide 2026-08-09)**: 29.450 Partien / 2.945 Dateien / ~4,8 Mio.
  Zustaende bleiben die stehende Groesse. Die Rotation haelt sie
  konstant -- pro Windung 12.000 NEUE Partien (4.000 Sockel @600 +
  8.000 Schwarm @150), gleich viel altes Material rotiert raus. Folgen:
  (a) Kosten pro Generation KONSTANT (~18h Self-Play + ~3h Cache +
  ~3,5h Training), kein Anwachsen; (b) das Fenster wird mit jeder
  Windung FRISCHER statt groesser; (c) RAM/Cache-Budget stabil
  (~13 GB im Training, ~1 GB auf Platte).
  **Nicht neu aufrollen**: der Dosis-Befund ("Volumen half 6/6") ist
  eine stehende Versuchung, das Fenster generell zu vergroessern -- die
  Entscheidung dagegen ist bewusst gefallen (planbare Kosten,
  stationaeres Design ab v22). Eine DAUERHAFTE Vergroesserung braucht
  einen ausdruecklichen neuen Nutzer-Entscheid. Die einmalige,
  vorregistrierte Injektion bei Gating-Fehlschlag (s.o.) ist davon
  ausgenommen und veraendert die Basisgroesse nicht.

- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.

- **PROMOTIONS-CHECKLISTE (Nutzer-Hinweis 2026-08-09: die Kader-Praxis
  wurde bis dato nicht konsequent umgesetzt)** -- bei JEDEM
  Champion-Wechsel vollstaendig abarbeiten, nicht aus dem Gedaechtnis:
  
  1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
  2. Elo-Kante **Gating** (Champion-1) -- inkl. Replikations-Zeile, falls
     Fruehstopp <150 Paare.
  3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
     Fruehstopp** (Praezedenz v18/v19/v20-Verankerung).
  4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- **das ist der
     Punkt, der bei v20 UND v21 zunaechst fehlte**; ohne ihn ruht die
     Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating:
     CI +-90 Punkte).
  5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
     Eintrag in die #29-Buchfuehrung.
     5b. **Anzeige-Kalibrierung nachziehen**: die Platt-Parameter A/B des
     NEUEN Champions in `server.py` (`_DISPLAY_CAL_A/_B`) eintragen --
     sie sind modellspezifisch. Quelle: `tools/platt_fit.py --models
     models/alphazero_<neu>.pth`. Ohne das zeigt die GUI die
     Gewinnwahrscheinlichkeit mit der Kurve des VORGAENGERS an.
     5c. **sigma/Prior-Balance messen** (neu 2026-08-09, aus Task G):
     `tools/gumbel_scale_calibration.py --model <neu> --sims 400
     --n-states 300`, ~10 min. Der Aera-Wechsel v18->v21 hat das
     Verhaeltnis von 1,232 auf **2,287** verschoben (delta_q verdoppelt,
     delta_ln(prior) unveraendert) -- R3 liegt mit 2,972 praktisch auf
     der Wiedereroeffnungs-Schwelle. **Ueberschreitet die
     Gesamt-Kennzahl 3, oeffnet sich die c_visit/c_scale-Familie per
     REGEL wieder** (kein Ermessen). Zugleich Verfallsdatum-Waechter
     fuer die H0-Befunde der Wurzel-Regler-Familie: die wurden in einem
     anderen Balance-Regime gemessen.
  6. STATUS-Champion-Zeile + history-Kapitel.
     **Nachtrag-Schuld ERLEDIGT** (Klarstellung 2026-08-10): die v20-Kante zu
     `v19_best` lief am 2026-08-09 -- 114:76 ueber 190 Partien, SPRT-H1 nach 95
     Paaren, p=0,0043 (`elo_history.csv` Zeile 53,
     `paired_gating_v20_vs_v19best_nachtrag.json`). Die alte "fehlt"-Zeile hier
     hat mich zweimal dazu verleitet, die Messung erneut vorzuschlagen.
     **Elo-Fragen am Primaerregister `elo_history.csv` pruefen, nicht an dieser
     Datei.**

- **LOESCHEN NUR MIT EXPLIZITER RUECKFRAGE (Nutzer-Regel 2026-08-08,
  dritter Vorfall dieser Klasse -- "inakzeptabel")**: Kein Loeschen,
  Verschieben oder Ueberschreiben von Dateien, Ordnern oder Worktrees
  ohne vorherige, den KONKRETEN Pfad benennende Nutzer-Freigabe.
  Ausnahme: das eigene Scratch-Verzeichnis.
  Im Einzelnen:
  
  1. **Eine FRAGE ist keine Anweisung.** "Ist X noch aktuell?", "kann
     man X weg?", "brauchen wir X?" verlangen eine ANTWORT. Handeln
     erst nach einem Imperativ, der das Ziel nennt.
  2. Als Loeschen gelten auch: `git worktree remove`, `git checkout --`,
     `git reset --hard`, `git clean -fd`, `mv` aus dem Projekt heraus,
     `rm` auf generierte Artefakte (Caches sind KEINE Ausnahme -- die
     Freigabe vom 2026-08-08 galt fuer sechs namentlich genannte Dateien).
  3. Vor jeder freigegebenen Loeschung: Ziel ANSEHEN (Inhalt, Groesse,
     Reparse-Points bei Worktrees -- Junction-Vorfall 2026-07-24), das
     Ergebnis der Pruefung BERICHTEN, und nur dann ausfuehren.
  4. Gilt fuer Sub-Agents identisch und steht in jedem Agent-Prompt.
  5. "Aufraeumen" ist niemals selbst-autorisiert -- auch dann nicht,
     wenn etwas offensichtlich veraltet ist.

- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.

- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).

- **AUFLOESUNG SCHLAEGT SPARSAMKEIT (Nutzer-Regel 2026-08-08)**: Wenn
  eine Entscheidung an einer Differenz haengt, die UNTERHALB der
  Auflösung des Offline-Instruments liegt (Value-Seite: Brier-Gaps
  <0,015 sagten 0/4 die Arena voraus; gemessene Seed-Skala ~0,0006),
  dann darf das Offline-Mass die Entscheidung NICHT tragen -- auch nicht
  als Spar-Vorfilter ("nur gaten, wenn Brier X schlaegt"). Stattdessen
  die ARENA in die Abwaegung nehmen und die Kosten AUSRECHNEN, nicht
  schaetzen: ein Gating (~1-1,5h CPU, 200 Paare @400) ist regelmaessig
  BILLIGER als das Training, das man sich mit dem Vorfilter sparen
  wollte (~3,5h GPU) -- und es ist das einzige validierte Instrument.
  Wer auf einem blinden Mass spart, spart die billige Ressource und
  riskiert die teure Fehlentscheidung.
  **Ausnahme Policy-Seite**: die Orakel-Metriken (Prior-Masse Top-3,
  Kendall-Tau) sind arena-validiert (7/7) und DUERFEN als Vorfilter
  dienen -- so entschieden bei #35b (beide Metriken schlechter -> kein
  Gating). Der Unterschied ist der Validierungsstand, nicht die
  Bequemlichkeit.
  Zusatznutzen, den man mitnehmen soll: jedes gefahrene Gating liefert
  ein arena-ENTSCHIEDENES Paar -- die Waehrung, in der #29 (Validierung
  eines Offline-Value-Praediktors) bezahlt wird (Stand ~3, noetig >=6).

- **Aggressions-/Denial-Programm GESCHLOSSEN** (2026-08-07): alle
  Knoepfe auf Default (w=0, λ=0, ε=0, bias=1); "gate what you ship";
  Wiedervorlage nur mit messbar schaerferem opp-Kopf
  (PREREG_aggression_style_measurement/PREREG_denial_tiebreak).

- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).

- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).

- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).

- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blind_spot.md`, Tasks E/F/G dazu
  geschlossen -> history): Q-Skalierungs-Varianz ist JA protokolliert
  (`tools/gumbel_scale_calibration.py`), **Ueberlebensrate im
  Sequential Halving NEIN** -- vorhanden sind `root_child_q`,
  `root_num_actions(_considered)` und `max_depth`, aber nicht, welcher
  Kandidat welche Halbierungsphase uebersteht. Bewusst nicht
  nachgeruestet: Task E hatte zuerst zeigen muessen, ob die MENGE
  stimmt (Ergebnis: Miss-Rate 1,21%, weit unter der 5%-Schwelle).

## Architektur, Stand jetzt (aktualisiert 2026-08-06)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):

- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2`.
- **Zwei R5-Loeser seit 2026-08-23** (`PREREG_r5_solver_split.md`): der
  EINGEFRORENE Anker-Loeser `round5_anchor.rs` haengt an den drei
  Sucheinstiegen der Heuristik (`mcts.rs:746`, `:777`, `:796`) und schuetzt
  die Elo-Leiter; `round5.rs` ist der Netz-Loeser und darf sich entwickeln.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting`, Blattwert = exakter Endscore inkl.
  Wertungsplatten. **Seit 2026-08-10 EXPECTIMINIMAX, nicht mehr reines
  Alpha-Beta**: Zufallsknoten an den Aufdeck-Stellen der verdeckten
  Chip-Zuordnung (16 der 20 Chips sind aus R1-4 bekannt, unbekannt ist nur
  die Fabrik-Position der restlichen 4). Kein Pruning in Zufallsknoten
  (Star1/Star2 bewusst weggelassen). `NODE_BUDGET=200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus),
  `MOSAIC_R5_CHANCE_NODES` (**Default AN** seit 2026-08-10, `=0` stellt das
  Altverhalten her), `MOSAIC_R5_NODE_BUDGET`, `MOSAIC_R5_NET_SOLVER`
  (Default an).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):

- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`, seit
  Task #28 zusaetzlich `opp_points` (nur in Modellen, die damit trainiert
  wurden -- Engine erkennt ihn per Output-NAME und faellt sonst auf
  Bestandsverhalten zurueck). **`plate_head` wurde am 2026-08-10 gebaut und
  wieder ENTFERNT** -- der Ownership-Kopf ist der Randlayer.
  `ownership` ist seit 2026-08-10 **140 breit** (72 Feldlabels + 68
  Konjunktionen, Breite an config.py:117-118 + Label-Bauer verifiziert
  2026-08-14); `OWNERSHIP_WEIGHT` steht in `config.py` weiter auf 0 --
  der Champion-Kopf ist untrainiert. Naechster Lauf mit Gewicht 0,2 +
  `--conjunction` ist der Korpus-Trainingslauf (PREREG_ownership_corpus.md).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, **`VALUE_OPP_EPSILON = 0,0`** (war 0,1 bis Schema 19).
- **Punkte-ZIEL (Schema 20, 2026-08-10)**:
  `points_val = tanh(own_total/VALUE_SCALE)` -- der Gegner-Anteil ist
  ENTFERNT. Fuer VOR Schema 20 trainierte Modelle bedeutet ihr
  `points`-Ausgang weiter `own - 0,1*opp`; fuer die Spielstaerke belanglos,
  weil die Ausgabe im Suchpfad ohnehin verworfen wird
  (`POINTS_UTILITY_WEIGHT = 0` und `w = 0`).
- **Value-ZIEL (#34-Verdikt, Schema 17 unveraendert gueltig)**: `values_wdl`
  = TD-Blend aus Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang;
  Alt-Datei-Bootstraps werden beim Cache-Bau Platt-entstaucht
  (A=0,0051/B=1,9269), `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben
  roh. Training: `--value-head wdl --select-by-brier` (KEIN destretch-Flag
  mehr noetig). **Das Ziel ist margen-BLIND** -- Herleitung in
  `../archive/history.md` (der Abschnitt "warum das Netz nicht punktoptimiert
  spielt" ist mit den Alt-STAND-Kapiteln dorthin gewandert).
  Policy-Traeger-Manifest **`data/policy_carrier_manifest_v21.json`**
  (Default in `neural_net.py` ist noch die v20-Datei -- ein Trainingsstart
  im v21-Fenster MUSS `MOSAIC_CARRIER_MANIFEST` setzen, s. Fenster-Pinning
  oben), maskiert Alt-Dateien ausser 135 v19wdl + 45 v18, plus
  `carrier_prefixes: ["selfplay_v20wdl_"]`; alles im Cache-Key.
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> **`v21_2d_brierbest`**.

---

## Task #38 (geparkt, Arbeitskreis "Spaeter" mit #31): Moon-Head-Feinschliff (2026-08-05)

Befund aus einer Interesse-Frage des Nutzers, Code verifiziert. Der Kopf
selbst ist solide (Plackett-Luce-Faktorisierung der Mond-Reihenfolge aus
dem Policy-Raum, Labels vom exakten Rundensolver, Prior-Aufteilung in der
Expansion). Zwei nie untersuchte Punkte fuer spaeter:

1. **Loss-Gewicht**: `moon_nll` wird mit VOLLEM Gewicht 1,0 in den
   Policy-Loss addiert (train.py, `p_loss + moon_nll[sun_mask].mean()`)
   -- bei NLL ~0,5-1 gegen Policy ~1,9 beansprucht ein Teilproblem, das
   nur Sonnenzuege betrifft, potenziell ~1/3 des Policy-Gradienten. Nie
   gesweept (VALUE_WEIGHT-Blindfleck-Muster). Als Arm in einen
   kuenftigen Loss-Gewichts-Sweep.
2. **Label-Horizont** (Nutzer-Einordnung 2026-08-05, RELATIVIERT):
   Referenz maximiert den RUNDENendstand (`solve_round_final_score`).
   Da die Fabriken zu Rundenbeginn NEU befuellt werden, ist der
   Wirkhorizont einer Reihenfolge im Wesentlichen die laufende Runde --
   das Solver-Label ist also naeher am Optimum als zunaechst vermutet,
   Restpunkt sind allenfalls Randeffekte. Falls Labels je aus der Suche
   kommen (root_child_q aus #35 liefert die Q-Ordnung der Varianten ab
   v20 gratis), waere das ein billiger A/B, kein Pflichtumbau.
   Kein akuter Bedarf: Policy-Seite ist ueber die Orakel-Metriken
   arena-validiert, inkl. PL-Aufteilung.
3. **Das Label ist EGOZENTRISCH -- damit ist "Fabriken aushungern"
   strukturell unerreichbar** (Nutzer-Frage 2026-08-16 "was ist mit
   fabriken aushungern gemeint", Code am selben Tag geprueft). Die
   Mond-Stapelreihenfolge ist der EINZIGE Hebel im Spiel, mit dem man dem
   Gegner gezielt nur vergiftete Optionen hinterlaesst: bei kleinen
   Fabriken bestimmt der nehmende Spieler die Reihenfolge, und spaeter ist
   nur die OBERSTE Fliese nehmbar (docs/engine_manual.md, Phase 1 B). Wer
   das steuert, kann den Gegner in Farben zwingen, die seine Musterreihen
   ueberlaufen lassen -- Strafpunkte ohne eigenen Einsatz, und der Zwang
   ist strukturell (die Runde endet erst, wenn alles leer ist; wer keine
   gueltige Aktion hat, MUSS passen).
   **AKTENLAGE KORRIGIERT (ungeprimter Review 2026-08-20, am Code
   bestaetigt): `moon_order_target` ist ein beweisbarer NO-OP** — die
   Zielfunktion `solve_round_final_score` liest nur `players[pi]`
   (Cache-Key `tiling_key`), die Mondreihenfolge lebt aber in
   `state.factories`; alle Permutationen scoren identisch, das Label ist
   immer die rohe Beutelreihenfolge (80/80-Sonde). Der Kopf trainiert auf
   RAUSCHEN und zieht dabei potenziell ~1/3 des Policy-Gradienten (Punkt 1
   oben). Auch der unten skizzierte "billige Zuschnitt" (eigener minus
   Gegner-Rundenendstand) waere aus demselben Grund ein No-Op. Der Text
   darunter bleibt als Ideen-Protokoll stehen, seine Praemisse ("bewertet
   jede Reihenfolge") ist widerlegt. Details:
   `PREREG_implementation_review_unprimed.md` par.7.
   **FOLGE FUER DEN #38-ZUSCHNITT (Nutzer-Entscheid 2026-08-20: hier
   festgehalten, bleibt im Arbeitskreis "Spaeter"):** wenn #38 angegangen
   wird, ist die Reihenfolge jetzt klar vorgezeichnet —
   (a) **billigster erster Arm: `moon`-Loss-Gewicht 0** (ein Trainingslauf
   + Gating). Das testet Punkt 1 (Loss-Gewicht) und den No-Op-Befund in
   einem: der Kopf zieht heute bis zu ~1/3 des Policy-Gradienten fuer ein
   NACHWEISLICH konstantes Rauschziel — Gewicht 0 ist die
   Nullhypothesen-Messung, ob das Gradient-Budget woanders mehr traegt.
   (b) Ein ECHTES Reihenfolge-Ziel braucht eine Zielfunktion, die
   `state.factories` liest (Reihenfolge-bewusste Variante von
   `solve_round_final_score` oder Suche-basierte Labels via root_child_q)
   — teurer, erst nach (a) sinnvoll. (c) Der alte "billige Zuschnitt"
   (minus Gegner-Endstand) ist als No-Op gestrichen. Zusaetzlich zu (a)
   gehoert der Python-Vielfachheiten-Bug der Zielrepraesentation
   (`neural_net.py:1799-1806`, 42 % der Labels betroffen) mit behoben,
   falls je ein echtes Ziel kommt.
   **Das Netz hat den Kopf dafuer, aber nie das Ziel** (Alt-Text): `moon_order_target`
   (`self_play.rs:634`) probiert Reihenfolgen durch und bewertet jede mit
   `solve_round_final_score(state, pi)` (`tiling_solver.rs:494`) -- also
   ausschliesslich dem EIGENEN Rundenendstand. Der Gegner kommt in der
   Bewertung nicht vor. Der Kopf kann Aushungern also nicht lernen, egal
   wie gut er wird.
   **Billiger Zuschnitt, falls je angegangen**: nur das Label aendern
   (eigener Rundenendstand MINUS Gegner-Rundenendstand, oder als eigener
   Arm), Bau bleibt unberuehrt. Vorbehalt: das ist eine neue
   Stoerungs-Wette, und Stoerung hat in diesem Projekt zweimal verloren
   (k6-Kuppeldraft, Farbzaehlung v1) -- vorher gehoert eine billige
   Diagnose davor, ob die Reihenfolge-Freiheit ueberhaupt genutzt wird
   (Praezedenz #39: Rotation/Position der Startkuppel waren tote
   Freiheitsgrade). Herkunft der Idee: Reddit-Rueckfrage eines Spielers
   nach adversarialen Faellen.

## Task #39 (geparkt, Arbeitskreis "Spaeter" mit #31/#38): Startkuppel-Platzierung (2026-08-06)

Nutzer-Beobachtung "setzt sie gefuehlt immer an dieselbe Position" --
am Code bestaetigt und MECHANISCH erklaert
(`self_play.rs::choose_start_placement`): der Farb-Score ist
POSITIONS-unabhaengig (summiert nur Fabrik-Farbhaeufigkeiten je Feld),
der Eckbonus fuer alle 4 Ecken identisch (0,5), Ties behaelt der erste
Kandidat -> IMMER Ecke (0,0); die Feld-Summe ist zudem
ROTATIONS-invariant -> immer 0 Grad. Position/Rotation sind tote
Freiheitsgrade; nur die Platten-WAHL variiert. Gilt ueberall (GUI,
Arena, Self-Play; Startplatzierung ist policy-maskiert, das Netz lernt
sie nie).

**Nutzer-Einordnung (2026-08-06, schaerft den Zuschnitt)**: die Ecke an
sich ist strategisch RICHTIG (Rand/Diagonale/Eckplatten honorieren sie
alle) -- das Problem ist die MONOTONIE, nicht die Position.
**KORREKTUR (Nutzer 2026-08-06, zweite Runde)**: auch der Ecken-Rang
(3 oben / 8 unten) ist KEIN Bewertungsfehler -- Kuppelzeile 0 wird von
den SCHNELLSTEN Musterreihen (1-2, Kapazitaet 1-2 Steine) gespeist: die
obere Ecke kommt frueher in Wertung + Orthogonal-Bonus und wird
zuverlaessiger ueberhaupt komplett; die 8 Punkte unten haengen an den
traegsten Reihen (5-6). Der (0,0)-Tie-Break loest den Trade-off implizit
RICHTIG auf. Verbleibende Substanz von #39:
(1) ROTATION -- bestimmt Farb-Ausrichtung zur Brettmitte und
Sonderfeld-Lage, heute verschenkt (Score rotationsinvariant);
(2) MONOTONIE/Tie-Break -- Diversitaets-Frage (GUI-Abwechslung +
Korpus-Vielfalt), keine Staerke-Frage.
**Verbesserungs-Optionen (bei Angehen abzuwaegen)**:
a) Heuristik-Upgrade: Rotations-Bewertung + randomisierter Tie-Break
   unter nahezu gleichwertigen Kandidaten; jede Aenderung per Arena
   gegen den Bestand pruefen (die Strategie-Intuition des Koordinators
   lag hier zweimal daneben, die des Nutzers zweimal richtig).
b) Prinzipiell: Platzierung in den Aktionsraum der Suche -- ACHTUNG
   NUM_ACTIONS-Aenderung macht alte Checkpoints unbrauchbar
   ([[num-actions-change-breaks-old-checkpoints]]), teuer.
**Randbedingung**: NICHT waehrend einer laufenden Kampagne aendern
(verschiebt die Self-Play-Zustandsverteilung); fruehestens v21-Setup.
Nebenaspekt: die heutige Uniformitaet kostet auch Zustands-Diversitaet
im Korpus.

## Task #31 (vorgemerkt): Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem (2026-08-03)

**Nutzer-Auftrag**: Staerke-Skalierung fuer Mensch-Spiele; Einschaetzung
"Sims allein richten es nicht" ist KORREKT und hier besonders: (a) R5-
Alpha-Beta + Tiling-DFS spielen sim-unabhaengig exakt -- eine 20-Sims-KI
spielt trotzdem perfekte Endspiele; (b) Gumbel+Policy-Prior traegt auch
Mini-Budgets -- flacher, aber nicht menschlich-fehlbar.

**Design-Skizze (3 Hebel je Stufe)**: Sims-Budget + Endspiel-/Tiling-
Degradation (R5-Knotenbudget-Override bzw. Policy-Sampling statt Solver,
Tiling greedy statt exakt bei "leicht") + Fehler-Injektion via Root-
Temperatur-Sampling mit Q-GAP-DECKEL (nur plausible Fehler <=3-5 Punkte;
menschlich-fehlbar statt gleichmaessig-flach; loest auch Ausrechenbarkeit).
Stufen: extrem=Champion@600-800 (optional lambda_aggr als Stil),
schwer=heutiger Stand @400, mittel=~100-150 Sims + Deckel-Sampling +
reduziertes R5-Budget, leicht=~8-16 Sims + Temperatur hoeher + epsilon +
Greedy-Tiling. ABGERATEN: alte Generationen als Stufen (Wartung,
OneDrive-Risiko, Regel-Fix-Inkompatibilitaeten, "gleichmaessig schwach").

**Kalibrierung**: vorhandene Elo-Leiter + Heuristik-Anker; je Konfiguration
n=150 vs 2 Anker, Ziel-Baender ~leicht 700-800 / mittel ~1000 / schwer
~1150-1200 / extrem=Champion. Umsetzung nach Muster Task #28
(Laufzeit-Parameter + Server-Preset + GUI-Dropdown). OFFEN (Nutzer):
Ziel-Baender ok? Darf "leicht" sichtbar Endspiele verstolpern?

**GATE (Nutzer-Entscheid 2026-08-03): ZURUECKGESTELLT** -- wird erst
angegangen, wenn ein Champion existiert, der auch gute menschliche
Spieler wirklich fordert. Bis dahin bleibt die Prioritaet auf
Staerke-Arbeit (v20-Zyklus, Value-Head-Front #29/#30, lambda=0.7-
Kandidat), nicht auf Schwierigkeits-UX.

---

## `stack_top_feature` (geparkt, Arbeitskreis "Spaeter" -- gleiche Stufe wie #38): Sichtgleichheit Netz/Spieler am Kuppelstapel (2026-08-20)

Aus einer Nutzer-Frage im Anschluss an eine GUI-Aenderung ("hat diese
Information das Netz auch?"), Code am selben Tag geprueft. Vollstaendiger
Zuschnitt in `PREREG_stack_top_feature.md`, hier nur der Kern.

**Das Kriterium ist Sichtgleichheit, nicht Staerke (Nutzer-Vorgabe
2026-08-20).** Das Netz soll denselben Informationsstand haben wie ein
Spieler am Tisch -- nicht mehr und nicht weniger. Ein flaches
Arena-Ergebnis waere kein Grund, das wieder herzunehmen ("Korrektheit vor
gemessenem Nutzen"); die Arena laeuft als Waechter gegen Regression, nicht
als Richter ueber das Merkmal. Entsprechend gibt es KEINE
Haeufigkeitsschwelle als Baubedingung.

**Das Prinzip ist schon gebaut, nur in der anderen Richtung:** die Farben
eines Bonusplaettchens gehen nur bei aufgedecktem Chip ins Merkmal,
begruendet mit "sonst versteckte Information, die kein Spieler kennt"
(`engine/src/features.rs:154`). Diese Prereg zieht die zweite Haelfte nach.

**Befund.** Die Rueckseite der obersten Kuppelstapel-Platte liegt am Tisch
offen und steht seit Commit 94b9090 auch im Ziehen-Knopf des
Stapel-Dialogs. Das Netz bekommt sie nicht: `dome_stack_top_type` existiert
nur in der Frontend-Serialisierung (`engine/src/serialize.rs:269`) und wird
weder in `features.rs` noch in `neural_net.py` gelesen (Grep, null Treffer).
Zum Stapel sieht das Netz nur die Menge der Rest-Designs
(`dome_pool_mask`), den Wild-Anteil und die Stapelgroesse -- alles
reihenfolgeblind. Zweite Luecke derselben Art: `pending_stack_draw` ist gar
kein Zustandsmerkmal, waehrend einer Ziehserie kennt der Spieler die
Rueckseiten aller bereits gezogenen Platten.

**Keine Orakel-Frage.** Die 18 Designs sind ein offener Satz mit je einem
Exemplar (`engine/src/dome.rs:198-226`); wer Auslage und Bretter sieht,
kennt den Rest durch Subtraktion. `dome_pool_mask` ist damit abgeleitetes
oeffentliches Wissen. (Eine gegenteilige Koordinator-Aussage vom
2026-08-20 ist durch den Nutzer richtiggestellt.)

**Warum es additiv ginge.** Das Eingabe-Layout kommt schon heute aus der
ONNX-Datei selbst (`detect_layout`, `engine/src/net.rs:104-118`). Zwei neue
Werte ans Ende des Flat-Vektors (708 -> 710) plus eine Kuerzung auf die vom
Modell deklarierte Laenge in `features_for_layout`
(`engine/src/features.rs:952`, dem einzigen Engpass aller Inferenz) laesst
Bestandsmodelle byte-identisch weiterlaufen. Bestehende Korpora tragen das
Feld bereits, Neugenerierung waere nicht noetig.

**Erste Stufe ist ein Inventar, kein Bau:** Abgleich Feld fuer Feld,
was die GUI zeigt gegen das, was der Merkmalsvektor traegt, in BEIDE
Richtungen ("Netz sieht mehr" / "Netz sieht weniger"). Offen und im
Inventar zu klaeren sind u.a. Mondstapel-Reihenfolge und Beutel-/Turm-
zaehler.
