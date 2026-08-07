# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`** (zuletzt ausgelagert 2026-08-07: der komplette
v20-Zyklus -- Training, Champion-Gating, Auswertungs-Paket, Engine-Fenster,
Suchpfad-Messungen 1+2, Zonen-Probe -- als "KAPITEL 2026-08-07").

---

## TASK-INDEX (Stand 2026-08-06)

| Nr | Titel | Status | Details |
|---|---|---|---|
| — | **v20-KAMPAGNE (Zwei-Klassen, WDL-Generator)** | **GATING GEWONNEN 2026-08-07 — `v20_2d_opp_brierbest` = CHAMPION (Elo 1349)** | `PREREG_v20_kampagne.md` |
| #34 | Sieg/Niederlage-Ziel (WDL) | **ABGESCHLOSSEN**: Verdikt = WDL + entstauchter Blend + brierbest; Arena ziel-invariant (8 Gatings), Platt-B 0,97 | history |
| #36 | Saettigung ueber Spielzahl | **BEANTWORTET**: Value log-linear hungrig (~0,0012 Brier/Verdopplung), Policy im Warm-Start-Regime satt (flach ab <=2.020 Partien) | history |
| #14 | PCR | **AUFGEGANGEN in Design C**: alle 3 Wiedereroeffnungs-Bedingungen erfuellt (Durchsatz 1,37x), die Wette ist im Zwei-Klassen-Schwarm strukturell besser umgesetzt -- klassisches PCR-mild obsolet | history |
| #35 | root_child_q-Logging | Engine erledigt (Default AN); **#35b Ranking-Loss: Daten liegen vor** (v20-Sockel, Filter = policy_target_valid) -- GPU-Bahn-Kandidat | history |
| #37 | Tiling-Auswahlkriterium (`punkte*P` vs reines P) | vorgemerkt v20-Aera, Arena-entschieden | unten |
| — | R4b/Endspiel-Zone | **URSACHE GEFUNDEN 2026-08-07**: Trunk traegt die Info (Probe R²=0,91), Koepfe/Ziele nutzen sie nicht -> Ziel-Problem; Leitbefund fuer die Platten-Intervention | history |
| — | #29-Instrument | Orakel-Referenzen neu nach frozen-Set-Neubau (v20-Aera); Validierung braucht arena-differenzierte Paare | PREREG_nach34_paket |
| — | Aggressions-Neukartierung | **ERLEDIGT 2026-08-07: alle 3 Arme H0** (Kontrolle 149/200 vs 154/161/155; p=0,59/0,17/0,54) -> **w bleibt UEBERALL 0**, Punkt zu bis zur naechsten Kopf-Generation; (0,1;2,0)-Richtung (+6pp, p=0,17) deskriptiv notiert -- erster Kandidat, falls ein kuenftiger opp-Kopf schaerfer wird. Nutzer-Partien FREIGEGEBEN (Preset w=0 = verankerte Konfig) | `paired_arena_env_aggr_neukartierung.json` |
| — | λ (Value-Target-Mix) | vertagt: am echten v20-Mischanteil neu bewerten | history |
| — | U1+U2 Defensiv-Fixes | **ERLEDIGT 2026-08-07** (Commit 2cd364e, Tests) | history |
| #31 | Schwierigkeitsstufen | geparkt (Arbeitskreis "Spaeter") | unten |
| #38 | Moon-Head-Feinschliff | geparkt (Arbeitskreis "Spaeter") | unten |
| #9 #12 #27 #28 #29 #30 | Aux-/Kalibrier-Serie | alle geschlossen (Details history) | history |

## NAECHSTE SCHRITTE (v20-Aera)

**v20-Zyklus ABGESCHLOSSEN 2026-08-07** -- Champion `v20_2d_opp_brierbest`
(Elo 1349, Gating 208:162 vs v19_2d_best p=0,0178), Auswertungs-Paket
und Suchpfad-Messungen 1+2 komplett; ALLE Details in
`../archive/history.md` "KAPITEL 2026-08-07". Kurzmerker fuers Arbeiten:
Floor-W=0,3 und m-Formel WDL-re-validiert; R5-Steigung 0,349 + Trunk-
Probe R²=0,91 -> Platten-Intervention via Aux-Kopf gerechtfertigt;
Checkpoint-Umkehrung E15/E5 zwischen neuem Val und Alt-Messset.

**LAUFEND (Parallel-Betrieb, Nutzer-Go "dann los")**:
1. CPU-Bahn (nach App-Neustart-Abbruch 2026-08-07 vormittags alle
   Hintergrundaufgaben WIEDER AUFGENOMMEN): **LAEUFT: τ-Annealing-Rest
   1.900 @600 (`v19wdlann`, 100 Partien ueberlebten den Abbruch;
   Tail-Regenerierung, frischer Seed)** -> danach
   **Aggressions-STILMESSUNG (PREREG_aggression_stilmessung.md;
   Nutzer-Auftrag "Punkte rauben ohne Siegquoten-Schaden"; 3 Arme a
   400: Kontrolle/(0.1,2.0)/(0.2,2.0); Erst-Sweep-Deskriptiv:
   Gegner-Floor +2,1 (t~4,5) bei (0.2,2.0))** ->
   **Denial-Tie-Break-Messung (E3, PREREG_denial_tiebreak.md --
   Nutzer-Go unabhaengig vom w/λ-Ausgang; 3 Arme ε=0/0,01/0,03;
   Implementierung beim Agent)** -> v21-Schwarm 8.000 @150
   (`v20wdlsw`) -> v21-Sockel gemaess τ-Verdikt.
   **v21-Fenster FIX: PREREG_v21_fenster.md** (29.450 Partien;
   RAM-Vorbedingung Bitpacking, Agent laeuft).
2. GPU-Bahn: pi_ctrl_s3 (Kontroll-Seed, laeuft) -> danach
   **Endgame-Arm** `pi_endgame_s2` (--endgame-head, Seed 2 = gepaart
   zum Champion-Lauf; Schema-18-Cache baut sich beim Start; NICHT
   parallel zu pi_ctrl starten -- RAM-Budget 32 GB!).
3. Koordinator-Bahn: PREREG_platten_intervention.md EINGEFROREN
   (Nutzer-Go), Schema 18 committet (a871123); τ-Annealing-Erweiterung
   beim Agent (MOSAIC_TAU_ARGMAX_FROM_MOVE), Go liegt vor.

**OFFEN (Reihenfolge = Nutzer-Prioritaet)**:
- τ-Annealing-Korpus-A/B (Messung 3, eigenes Nutzer-Go, ~0,5 Tage).
- Platten-Intervention (ENTWURF-Prereg, Nutzer-Go).
- frozen-Set-Neubau -> #29-Instrument (Orakel-Labels = CPU, ans Ende
  der CPU-Bahn).
- #37; λ (am echten v20-Mischanteil); Fenster-Rotations-A/B fuer v21.
- Struktur-Watchlist: wartet auf bewertete Partien des Nutzers gegen
  den neuen Champion (nach der Neukartierung).

## OFFENE ENTSCHEIDUNGEN & GELTENDE REGELN

- **Champion**: `v20_2d_opp_brierbest` seit 2026-08-07 (Gating 208:162
  vs `v19_2d_best`, p=0,0178; Nutzer-Vorab-Entscheid "naechste
  Generation wechselt auf v20_2d_opp"). Erster Champion der WDL-Aera,
  opp-Kopf damit in der Linie. Self-Play-Generator kuenftiger
  Kampagnen = dieser Champion (Namenskonvention: Dateien nach dem
  GENERATOR benennen, also `selfplay_v20wdl_*`).
- **v20-Kampagnen-Design**: Option C (Zwei-Klassen, Nutzer-Idee) wurde
  umgesetzt und hat den Zyklus gewonnen -- Design-Details in
  `PREREG_v20_kampagne.md`, Diskussions-Historie in history
  ("AUSGELAGERT aus STATUS 2026-08-07"). Merkregel bleibt: Backup-/
  Alt-Regel-Korpora NIE wieder; Dateien nach dem GENERATOR benennen.
- **λ (Value-Target-Mix)**: bis nach #34 ZURUECKGESTELLT -- #34 aendert
  `z` auf eine Gewinnwahrscheinlichkeit, damit mischt λ zwei Groessen
  derselben Art. Befundlage: gewinnt bei 65,7% root_q-Mix, verliert bei
  43,8% (zweimal, quer ueber Regime) -> **Korpus-Mischanteil entscheidet**.
  v20-Fenster entweder root_q-rein bauen oder λ neu messen.
  **Engine-Audit F1: das λ07_opp-Gating (33:47) lief mit w=0,1 und
  opp-Modell auf Kandidatenseite -- der Kandidat spielte mit
  ownership-Logit im Blend, das Ergebnis ist KONTAMINIERT und zaehlt
  nicht als λ-Beleg (weder dafuer noch dagegen).**
- **Aggressions-Blend: UEBERALL AUF 0 / INAKTIV (Nutzer 2026-08-05,
  nach Engine-Audit F1)**: "wir wissen ja nicht was er tut" -- alle
  Blend-Messungen waren ungueltig (ownership-Logit statt Gegner-Prognose
  gelesen). Konkret: Engine-Env-Defaults bleiben 0; die fruehere
  Arena-Konvention w=0,1/λ_aggr=2,0 ist AUFGEHOBEN (Gatings laufen ohne
  Blend); kein Serverstart-Default; **GUI-Slider ENTFERNT** (2026-08-05,
  im Browser verifiziert). Der Engine-Knopf (set_aggression_params,
  POST /api/aggression, Env-Vars) bleibt als inertes Werkzeug fuer die
  Neukartierung im v20-Zyklus -- nichts ruft ihn mehr auf. "Gate what
  you ship" gilt weiter und heisst jetzt: ausgeliefert wird OHNE Blend,
  also wird auch ohne Blend gegatet.
- **Tiling-Cache**: Default AN seit 2026-08-05 (-20,1% Self-Play-Wandzeit,
  bitgleich); `MOSAIC_TILING_CACHE=0` schaltet ab.
- **Statistik-Regeln**: (1) Score-basierte Arena-Auswertungen IMMER auf
  Block-Ebene (Paar-SEs unterschaetzen massiv); Win-SPRT milder betroffen,
  Block-Zahlen trotzdem mitberichten. (2) Netz-vs-Heuristik: Effekte <8pp
  liegen im Seed-Satz-Rauschen. (3) **SPRT-Fruehstopps unter ~150 Paaren
  zaehlen NICHT ohne Frisch-Seed-Replikation** (t12-Falsch-Positiv
  2026-08-06: H1 bei n=80, Replikation ueber 400 Partien = Paritaet).
- **Elo-Betrugsschutz (GUI, 2026-08-06)**: gewertete Spiele NUR gegen
  KI-Konfigurationen mit direkter Arena-Kante (`is_estimate=False`) --
  Sims-Tier-Schaetzwerte werten nicht mehr (Farming-Luecke geschlossen).
  Abbruch-Verhalten (verlorene Partie neu starten vermeidet
  Elo-Verlust): NUTZER-ENTSCHEID 2026-08-06 -- bleibt so, kein Fix.
  Zukunftsoffen: sobald #31-Kalibrierung Preset-Konfigurationen (z.B.
  champion@60) per Arena verankert, werden sie automatisch ehrlich
  wertbar.
- **Kein validierter Offline-Praediktor fuer die Value-Seite** (#29
  gescheitert, value_r2 viermal widerlegt) -> jede Value-Aenderung
  braucht ein Arena-Gating. **Nach #34 neu zu pruefen** (siehe unten).

## MENSCH-vs-KI-BEFUND (Nutzer-Anstoss 2026-08-06): 9 gewertete Partien analysiert

Nutzer schlaegt v19_2d_best@400 **8:1** (Log-Analyse
static/log/, Profil artfox). Die KI ist im Kleinen minimal besser
(3,47 vs 3,30 Pkt je Kuppel-Legung) und verliert ueber zwei
STRUKTURELLE Strategien, die sie nicht spielt:
1. **Chip-Spezial-Maschine**: Mensch 1,9 Chip-Reihenabschluesse und
   10,8 Spezialpunkte je Partie, KI 0,0 / 0,4. Der Tiling-Solver KANN
   chippen (TilingStep::Chips existiert) -- aber die Drafting-Policy
   baut nie chipbare tiefe Reihen auf (R5+R6-Nahmen: Mensch 37%, KI
   22%). Mechanistisch = die bekannte Platten-Kaskaden-Blindheit des
   Value-Kopfs, erstmals als Spielfolge sichtbar.
2. **Tempo**: Startspielerstein-Nahmen 34:7 fuer den Menschen -- die KI
   bewertet das Startrecht systematisch zu niedrig (-2 wirken im alten
   Punkte-Margen-Value teurer als das Tempo wert ist?).
3. Startkachel: Mensch variiert ((0,0)@0/270, (2,0)@180), KI klemmt
   deterministisch (#39).

**MECHANIK-AUFKLAERUNG (2026-08-06, zwei Korrekturen)**:
1. Nutzer-Design-Punkt bestaetigt: die Suche braucht die Tiling-Phase
   NICHT zu sehen -- "chip-abschliessbar" ist eine ZUSTANDSEIGENSCHAFT,
   und sie ist BEREITS als expliziter Netz-Input kodiert (Chip-Farb-
   Zaehler + Abschliessbarkeits-Flag je Musterreihe, state_to_tensor).
2. Koordinator-Irrtum "selbstverstaerkende Schleife" ZURUECKGEZOGEN:
   der Korpus ist VOLL mit Chip-Abschluessen -- gemessen 4,92/Partie
   (v18-Korpus, 400 Partien) und 4,85/Partie (frische v19wdl-Sockel,
   200 Partien). Die KI chippt im Self-Play routiniert.

**DIAGNOSE, DRITTE ITERATION (Nutzer-Selbstauskunft 2026-08-06)**: die
Tempo-/Denial-Deutung war ebenfalls die des Koordinators, nicht die des
Spielers. Nutzer: "wuerde den Startspielerstein nicht ueberbewerten" --
die 34:7-Marker-Statistik ist mutmasslich NEBENPRODUKT des mondlastigen
Sammelstils (19,9 Mond-Nahmen/Partie; der Stein geht zwangsweise an die
erste GF-Mond-Nahme), kein Tempo-Kauf. Das TATSAECHLICHE Spielkonzept
(woertlich festgehalten als Strategie-Dossier):
- Kern: ORTHOGONALE Reihen (Kreuz-Aufbau fuer Linienboni) + hoeherwertige
  SPEZIALFELDER; Chips/Spezials sind Teil dieses Strukturplans.
- Wertungsplatten als BONUS, selektiv: VERTIKAL immer gerne (~2 Spalten
  werden voll); ECKPLATTEN normal 1x3 + 1x8 erreichbar; DIAGONALE
  zwiegespalten (widerspricht dem orthogonalen Aufbau); HORIZONTAL und
  FARBENREICH bringen wenig extra; MEHRFARBIG ok.
- Spezialfeld-Taktik (NUR bei aktiver Spezialfelder-Wertungsplatte
  Nr. 7, Nutzer-Praezisierung 2026-08-06): Spezial-Kuppeln in die
  ERSTEN (schnellen) Reihen, Wild-Kuppeln AGGRESSIV nehmen -- die
  Taktik ist an die -3-je-leeres-Spezialfeld-Wertung gebunden, nicht
  generisch.
Die KI-Chip-Duerre gegen den Menschen ist damit eher Folge dessen
STRUKTUR-Vorsprungs (Kreuze + Spezial-Timing) als aktiven Denials.

**Verwertung (final geschnitten)**: (a) v20-Watchlist gegen Menschen:
Struktur-Metriken (Kreuz-/Spaltenaufbau, Spezial-Unlock-Timing,
Wild-Kuppel-Anteil, Chip-Oekonomie unter Druck) statt Tempo;
(b) Denial-/Aggressions-Neukartierung v20-Aera behaelt ihren Wert, aber
ohne die Mensch-Belegt-Behauptung; (c) das Strategie-Dossier ist
Referenzmaterial fuer #31 (Stil-Stufen) und kuenftige Eval-Arbeit.
Elo-Anmerkung zu #31 GESTRICHEN (Nutzer: pendelt sich selbst ein).

## SUCHPFAD-VERIFIKATIONS-INVENTAR (Agent-Audit, Nutzer-Auftrag 2026-08-06)

Alle aktiven Modifikatoren/Konstanten im Netz-Suchpfad gegen
STATUS/history abgeglichen (Kernbelege stichprobenverifiziert).
**Pointe: der Nutzer-Verdachtsfall Floor-Shaping ist als FEATURE der
bestverifizierte Shaping-Term im Code** (gepaarter A/B +14pp, McNemar
p=0,0075, history:1104-1137; plus v10-Ablation). Offen daran nur:
der GEWICHTS-Wert 0,3 (0,15/0,6-Sweep nie gefahren) und die
Re-Validierung in der WDL-Aera (Additiv auf einer Achse, deren
Spreizung sich ~2x geaendert hat).

**UNVERIFIZIERT + AKTIV (Ertrag, nach Relevanz):**
1. **`gumbel_top_m_for_budget`** (net_mcts.rs:1724): bei 150 Sims ->
   m=9 statt 16 -- nie staerke-gemessen; **der laufende v20-Schwarm
   spielt damit** (Milderung: Policy maskiert, Value-Ziel =
   Bootstrap+Ausgang, root_q ungenutzt; 16-vs-8-Wash bei 400 Sims
   deutet auf geringe Sensitivitaet). Nachmessung im Nach-v20-Fenster.
2. **tau=1-Besuchs-Sampling ohne Annealing** (ganze Partie,
   self_play.rs:2031): Design-Entscheid, nie A/B vs Annealing.
3. **Heuristik-Anker-Parameterpaket** (SELF_PLAY_C, Temperaturleiter,
   visits^(1/tau)*q^2 u.a.): definiert den Elo-Anker@200 --
   NICHT-ANFASSEN-Regel (jede Aenderung entwertet die Elo-Leiter,
   Praezedenz #21-Neuverankerung).
4. Startkuppel-Heuristik (= #39, geparkt), `GUMBEL_C_VISIT=50` (nur
   indirekt via c_scale gedeckt), Bootstrap-Label-Budgets
   (Horizont 2/Budget 40, wirken auf Labels, nicht Live-Staerke;
   dort lebt auch POLICY_MASS_CUTOFF=0.95 weiter, im Livepfad tot).

**TEIL-VERIFIZIERT** (Offline-/Aequivalenz-Belege, keine isolierte
Staerke-Messung): #20-Tiebreak (Referenz-validiert, Kriterium = #37),
PL-Moon-Split (via Orakel-Instrument), DETERMINIZE (Korrektheit schlaegt
Messwert, dokumentiert), DECOUPLE_NET_SIMS, Gumbel-Umstieg selbst
(nur "nicht schlechter" bei n=100, danach System-Ko-Evolution),
completed-Q-Ziel, VALUE_SCALE=50 (Nutzer-Fixpunkt), R5-/Tiling-Budgets
(Aequivalenz- bzw. Haenger-kalibriert).

**VERIFIZIERT/INERT**: Floor-Shaping-Feature, c_scale (2x), TOP_M@400,
endaware, NUM_DET=1, Tiling-Cache; alle Aus-Schalter mit Beleg
(VALUE_SHRINK, PLATE/TILING_SHAPING, POINTS_UTILITY, MIRROR,
STACK_PEEK, CAL_A/B, Aggression w=0); Dirichlet/c_puct = tote Knoepfe
im Legacy-Pfad. Details: Agent-Report 2026-08-06 (Transkript).

**Nach-v20-Kandidatenliste daraus** (billige Ein-Faktor-Gatings, wenn
die Arena-Maschine warm ist): Floor-Gewicht 0,15/0,3/0,6 in der
WDL-Aera; m(150)-Formel-Messung; tau-Annealing-A/B. KEINE Aenderung
vor dem v20-Gating (laufende Kampagne nicht kontaminieren).

## Task #37 (NEU, Nutzer 2026-08-05): Tiling-Auswahlkriterium fuer die naechste Generation

**Frage**: Welches Kriterium waehlt unter den Top-12-Tiling-Abschluessen
(Task-#20-Kopplung, `tiling_solver.rs::best_first_step_valued`):
(a) Bestand `punkte * P(Sieg)`, (b) reines P(Sieg)-Ranking,
(c) P(Sieg) mit Punkte-Tiebreak nur bei nahezu gleichem P?

**Hintergrund** (Diskussion 2026-08-05): Mit dem kalibrierten WDL-Kopf
fliesst die Punkte-Information beim Produkt ZWEIMAL ein -- einmal korrekt
dosiert via P(Sieg|Folgezustand), einmal als eigener Faktor mit
willkuerlichem Wechselkurs (ob die bessere Siegchance sich durchsetzt,
haengt vom absoluten Punkteniveau ab). Mit dem ALTEN Margen-Kopf war das
Produkt in sich stimmig und wirkte wegen der Stauchung de facto als
reiner Punkte-Stichentscheid -- der kalibrierte Kopf spreizt ~2x weiter
und kann Punktunterschiede real ueberstimmen (stille
Verhaltensverschiebung ohne Codeaenderung).

**GEGENARGUMENT, vorab notiert**: der Punkte-Faktor wirkt derzeit als
robuster PRIOR, der Value-Rauschen baendigt (Kopf nach 2-3 Epochen noch
verrauscht) -- moeglicherweise ist das Produkt genau deshalb praktisch
robust. Entscheid daher NUR per Arena, nicht am Schreibtisch.

**Zuschnitt**: v20-Aera (reifer WDL-Kopf im Champion), Arena-A/B der
Varianten (a) vs (b), ggf. (c) als dritter Arm; Laufzeit-Schalter analog
Task-#30-Muster, damit kein Rebuild je Arm noetig ist. Bis dahin bleibt
(a) Bestandsverhalten.

### Abgeschlossene Ergebnis-Bloecke -> history

#36-Saettigungskurve, Nach-#34-Paket (#9/#12/#29) und PCR-#14-
Wiedereroeffnungspruefung: vollstaendig nach `../archive/history.md`
verschoben ("AUSGELAGERT aus STATUS 2026-08-07"); Kurzfassungen stehen
im Task-Index oben.

## Architektur, Stand jetzt (aktualisiert 2026-08-06)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):
- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2`.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting` mit exaktem Alpha-Beta
  (`NODE_BUDGET=200`), Blattwert = exakter Endscore inkl. Wertungsplatten.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):
- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`
  (inert, Gewicht 0), seit Task #28 zusaetzlich `opp_points` (nur in
  Modellen, die damit trainiert wurden -- Engine erkennt ihn per
  Output-NAME und faellt sonst auf Bestandsverhalten zurueck).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `VALUE_OPP_EPSILON = 0,1`, `TD_LAMBDA = 0,5`.
- **Value-ZIEL (#34-Verdikt, Schema 17)**: `values_wdl` = TD-Blend aus
  Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang; Alt-Datei-
  Bootstraps werden beim Cache-Bau Platt-entstaucht (A=0,0051/B=1,9269),
  `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben roh. Training:
  `--value-head wdl --select-by-brier` (KEIN destretch-Flag mehr noetig).
  Policy-Traeger-Manifest `data/policy_carrier_manifest_v20.json`
  maskiert Alt-Dateien ausser 135 v18 + 45 v17 (im Cache-Key).
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> `v19_2d_best`.

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
