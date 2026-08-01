# Recherche-Bericht: Verbesserungen für AlphaZero-artige Systeme — Übertragbarkeit auf Mosaic

*Erstellt 2026-08-01 durch Recherche-Agent (Web-Survey), kuratiert im Kontext der 2D-Encoder-Kampagne (Task #11).
Bewertungsmaßstab: eigene Empirie — gestorbene Experimente (Ownership p=0.22, HL-Gauss-Punkte-Kopf p=0.10, rtv-Labels, Head-Widening), 2×2-Hybrid-Attribution (Value-Head trägt Stärke bei 400 Sims), Value-R² ~0.1 in frühen Runden (mutmaßlich Zielrauschen durch Stochastik).*

Vorab eine Einordnung, die sich durch die ganze Recherche zieht: Unser Kernproblem (Value-R² ~0.1 in frühen Runden, Value-Head trägt nachweislich die Stärke) ist in der Literatur gut adressiert — aber fast alle relevanten Hebel drehen an der **Varianz des Value-Ziels**, nicht an der Netzarchitektur. Das passt zu unseren gestorbenen Experimenten (Ownership, HL-Gauss, Head-Widening), die alle an der Kapazitäts-/Architekturschraube drehten.

---

## Schwerpunkt 1: Value-Target-Qualität

**1. „Value targets in off-policy AlphaZero: a new greedy backup" (Willemsen, Baier, Kaisers, 2021, Neural Computing and Applications)**
[Paper (Springer)](https://link.springer.com/article/10.1007/s00521-021-05928-5) | [ALA2020-PDF](https://ala2020.vub.ac.be/papers/ALA2020_paper_18.pdf)
Systematisiert die Familie der AlphaZero-Value-Targets in einem 3D-Raum (Bootstrap-Tiefe, Greediness, On/Off-Policy): Original-z (Spielausgang), soft-Z (Root-MCTS-Wert), A0C und ein neues „greedy backup" (A0GB), das den Wert des besten statt des explorierten Pfads zurückpropagiert. Kernbefund: z ist durch Explorationszüge und (bei uns zusätzlich) Zufall **verzerrt UND hochvariant**; Suchwert-Targets senken die Varianz deutlich.
**Übertragbarkeit: HOCH.** Direkt auf unser Kernproblem gemünzt. Wichtige Abgrenzung zum gestorbenen rtv-Experiment: rtv waren *zusätzliche* Labels aus *extra* Suche (83% der Self-Play-Kosten). Hier geht es um das **Mischen des ohnehin berechneten Root-Suchwerts in das Haupt-Target** (λ·z + (1−λ)·q_root) — null Zusatzkosten im Self-Play, ein anderer Mechanismus (Varianzreduktion des Haupt-Targets statt Zusatz-Task). Der Oracle-Blog ([Lessons From AlphaZero Part 4](https://medium.com/oracledevs/lessons-from-alphazero-part-4-improving-the-training-target-6efba2e71628)) berichtet dieselbe Idee unabhängig mit positivem Effekt bei Connect Four.
**Aufwand: NIEDRIG** (Root-Q wird bei uns via completed-Q schon berechnet; nur Label-Pipeline + ein Hyperparameter λ).

**2. MuZero Reanalyze / ReZero — Relabeling alter Daten mit frischem Netz**
[MuZero Unplugged / Reanalyse (arXiv 2104.06294)](https://arxiv.org/pdf/2104.06294) | [ReZero (arXiv 2404.16364)](https://arxiv.org/abs/2404.16364)
Alte Replay-Positionen werden mit dem aktuellen Netz + frischer Suche neu gelabelt (Value und Policy), statt die alten, von schwächeren Netzen erzeugten Targets weiterzuverwenden. ReZero (2024) beschleunigt das per Backward-View-Wiederverwendung und zeigt es auch auf Brettspielen.
**Übertragbarkeit: HOCH.** Passt exakt zur Replay-Window-Strategie (5000 aktuelle + 2×1000 alte Spiele): Die 2000 Alt-Champion-Spiele tragen veraltete Value-Labels. Wir haben einen perfekten Simulator — Reanalyze ist bei uns nur „Suche auf gespeicherten States", kein gelerntes Modell nötig. Billige Variante: nur die Alt-Spiele mit dem aktuellen Champion bei reduzierten Sims (z.B. 64–100 Gumbel-Sims) neu labeln.
**Aufwand: MITTEL** (Batch-Relabeling-Tool über der bestehenden Rust-Engine; kein Trainings-Code-Umbau).

---

## Schwerpunkt 2: Stochastische Spiele / Chance-Knoten

**3. Stochastic MuZero (Antonoglou et al., ICLR 2022)**
[OpenReview-PDF](https://openreview.net/pdf?id=X6D9bAHhBQ1) | [Erklär-Blog des Mitautors](https://www.julian.ac/blog/2022/05/15/planning-in-stochastic-environments-with-a-learned-model/)
Führt **Afterstates** ein (Zustand nach Aktion, vor Zufallsauflösung) und modelliert Chance-Knoten explizit im Baum; an Chance-Knoten wird per Prior gesampelt, Werte werden erwartungstreu zurückpropagiert. SOTA auf 2048 und Backgammon.
Zur Kernfrage „senkt explizite Chance-Knoten-Modellierung das Value-Zielrauschen?": **Ja, aber indirekt.** Das Rauschen im *Outcome-Label z* bleibt irreduzibel. Was sinkt, ist die Varianz von **Suchwert-Labels**: Ein Root-Wert, der an Chance-Knoten über mehrere Auslosungen mittelt (Expectimax-artig), ist ein deutlich rauschärmeres Label als ein einzelner Spielausgang. Chance-Knoten-Modellierung und Suchwert-Targets (Fund 1) verstärken sich gegenseitig.
**Übertragbarkeit: MITTEL-HOCH.** Chance-Knoten bei Rundenübergängen sind im Engine-Modell vorhanden, kein gelerntes Modell nötig. Übertragbarer Teil: (a) Audit, ob unsere Chance-Knoten im Backup erwartungstreu mitteln statt einen Sample-Pfad zu nehmen, (b) ein **Afterstate-Value** (Bewertung nach eigenem Zug, vor Nachziehstapel-Auflösung) als Trainings-/Suchgröße.
**Aufwand: MITTEL** (Audit + ggf. Backup-Änderung in net_mcts.rs; Afterstate-Head wäre größer).

**4. Gumbel + Stochastik: „An Empirical Analysis of Gumbel MuZero on Stochastic and Deterministic Einstein Würfelt Nicht!" (TAAI 2023) und „On Reinforcement Learning for the Game of 2048" (Guei et al., 2022)**
[Springer-Kapitel](https://link.springer.com/chapter/10.1007/978-981-97-1711-8_25) | [arXiv 2212.11087](https://arxiv.org/pdf/2212.11087) | [mctx-Issue zur Kombination](https://github.com/google-deepmind/mctx/issues/66)
Beide Arbeiten kombinieren Gumbel-Suche mit Stochastic-MuZero-Chance-Knoten. Bemerkenswert auf 2048: Training mit nur **3 Simulationen** schlug 16 und 50 Sims — in stark stochastischen Spielen kann tiefe Suche im Training weniger wert sein als mehr Spiele, weil der Zufall tiefe Pläne entwertet.
**Übertragbarkeit: MITTEL.** Bestätigt, dass Gumbel-Top-M mit Chance-Knoten sauber koexistiert (relevant für GUMBEL_TOP_M=16). Der 3-Sims-Befund motiviert ein Experiment „weniger Sims, mehr Spiele pro Generation" — billig testbar, verwandt mit Fund 6.
**Aufwand: NIEDRIG** (reine Hyperparameter-Variation im Self-Play).

**5. Determinisierung / Information-Set-Sampling**
[„Efficiently Training Neural Networks for Imperfect Information Games by Sampling Information Sets" (2024)](https://www.researchgate.net/publication/382079672_Efficiently_Training_Neural_Networks_for_Imperfect_Information_Games_by_Sampling_Information_Sets)
**Übertragbarkeit: NIEDRIG.** Unsere verdeckten Nachziehstapel sind symmetrisch verdeckt — das ist Stochastik, keine asymmetrische Information. v8d-Befund (Value-Head sieht keine Hidden-Info, 0.0 Spread) bestätigt: kein Leck, kein Handlungsbedarf. Nur als Negativ-Abgrenzung aufgeführt.

---

## Schwerpunkt 3: KataGo-Techniken jenseits Ownership/Score

Quellen: [KataGo-Paper „Accelerating Self-Play Learning in Go" (arXiv 1902.10565)](https://arxiv.org/pdf/1902.10565) | [KataGoMethods.md (laufend gepflegt, mit Elo-Angaben)](https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md)

**6. Playout Cap Randomization (PCR)** — Zufällig pro Zug zwischen voller Suche (Policy-Qualität) und billiger Suche (mehr Spiele → mehr Value-Samples) wechseln; nur Voll-Such-Züge liefern Policy-Targets, alle liefern Value-Targets. In-Paper-Ablation klar positiv; unabhängige Übernahmen u.a. in [ChessCoach](https://chrisbutner.github.io/ChessCoach/high-level-explanation.html); eine breite unabhängige wissenschaftliche Replikation existiert **nicht** — Community-Konsens plus solide Erstautor-Ablation.
**Übertragbarkeit: HOCH.** Adressiert exakt die Diagnose: Value-Head ist der Engpass, Value-Training braucht *viele Spielausgänge*, nicht tiefe Suchen. Bei gleichem Compute-Budget deutlich mehr als 6000 Spiele → mehr unabhängige z-Samples → weniger effektives Zielrauschen im Aggregat. Kollidiert mit keinem gestorbenen Experiment. (= Task #14.)
**Aufwand: NIEDRIG-MITTEL** (Sim-Budget pro Zug randomisieren + Policy-Target-Maske; Vorlauf: GUMBEL_TOP_M laufzeit-skalierbar).

**7. Policy Surprise Weighting / Auxiliary Soft Policy / Optimistic Policy** — Samples mit überraschendem Policy-Target übergewichten; temperierter Zusatz-Policy-Head; optimistischer Policy-Head (40–90 Elo bei KataGo).
**Übertragbarkeit: NIEDRIG-MITTEL.** Alles Policy-Hebel — 2×2-Attribution zeigt: bei 400 Sims trägt der Value-Head die Stärke; Policy-Verbesserungen ohne Value-Verbesserung enden im Arena-Gleichstand (frisch bestätigt durch fs_2d vs fs_flat). Nur nachrangig.

**8. Uncertainty-Weighted Playouts + Dynamic cPUCT (~75 Elo bei KataGo)** — Netz sagt die erwartete Fehlergröße der eigenen Value-Schätzung vorher; unsichere Knoten zählen im Backup weniger. Setzt bei KataGo auf „short-term value targets" auf — rtv-ähnlich.
**Übertragbarkeit: MITTEL, mit Warnung.** Die Idee einer strukturellen, rundenabhängigen Unsicherheit passt zu Mosaic (Runde 1 verrauscht, Runde 5 fast deterministisch). rtv-freie Variante: Unsicherheits-Head auf den **Residualfehler gegen z** (heteroskedastische Regression), keine Zusatz-Suche. rtv-Nähe macht es zum Reserve-Experiment, nicht zum Erstkandidaten.
**Aufwand: MITTEL-HOCH** (neuer Head + Suchintegration in Rust).

**9. Subtree Value Bias Correction (30–60 Elo bei KataGo)** — Online-Korrektur systematischer Netz-Fehler pro lokalem Zugmuster.
**Übertragbarkeit: NIEDRIG.** Lebt von Gos lokaler Musterstruktur; Mosaic-Züge haben keine vergleichbare lokale Äquivalenzklassen-Struktur.

---

## Schwerpunkt 4: Dateneffizienz (EfficientZero-Linie)

**10. EfficientZero V2 (ICML 2024 Spotlight) / LightZero (NeurIPS 2023)**
[arXiv 2403.00564](https://arxiv.org/pdf/2403.00564) | [LightZero (arXiv 2310.08348)](https://arxiv.org/pdf/2310.08348) | [LightZero-Repo](https://github.com/opendilab/LightZero)
**Übertragbarkeit: NIEDRIG.** Die Säulen (Self-Supervised-Konsistenz, Value-Prefix) reparieren Probleme des *gelernten* Modells — wir haben einen perfekten Simulator. Einzig übertragbar: adaptive Off-Policy-Korrektur der n-Step-Targets — wird von Reanalyze (Fund 2) dominiert. LightZero als Benchmark-Referenz nützlich.

---

## Schwerpunkt 5: Kleine Netze / CPU-Inferenz

**11. „Scaling Scaling Laws with Board Games" (Andy L. Jones, 2021)**
[arXiv 2104.03113](https://arxiv.org/abs/2104.03113)
AlphaZero auf Hex bis 9×9: Train- und Test-Compute gegeneinander eintauschbar nach Log-Linear-Beziehung (~10× Trainings-Compute ersetzt ~15× Test-Compute).
**Übertragbarkeit: MITTEL-HOCH als Entscheidungsrahmen.** Für „512-hidden-MLP + 400–600 Sims vs. größeres Netz + weniger Sims" die richtige Messmethodik: kleine Frontier (2–3 Netzgrößen × 2–3 Sim-Budgets bei fixem Arena-Zeitbudget) statt Einzel-A/Bs.
**Aufwand: NIEDRIG** (nur Arena-Läufe, arena.py existiert).

**12. „Scaling Laws for a Multi-Agent RL Model" (Neumann & Gros, 2022/2023) + „AlphaZero Neural Scaling and Zipf's Law" (2024)**
[arXiv 2210.00849](https://arxiv.org/abs/2210.00849) | [arXiv 2412.11979](https://arxiv.org/html/2412.11979)
Elo skaliert als Potenzgesetz in Parameterzahl (Exponent ~0.88 auf Connect Four/Pentago); optimale Netzgröße wächst mit Compute^0.63. Zentrale Aussage: **die meisten publizierten AlphaZero-Agenten sind für ihr Compute-Budget zu klein.** Folgearbeit zeigt aber Inverse-Scaling-Fälle — größer ist nicht garantiert besser.
**Übertragbarkeit: MITTEL-HOCH.** Unser 708→512-MLP ist mutmaßlich unterdimensioniert fürs investierte Compute. Gegenrechnung: CPU-Inferenz macht Netzvergrößerung teuer in Sims — gehört mit Fund 11 in EIN Frontier-Experiment. Widerspricht nicht dem Head-Widening-Negativergebnis (dort nur Value-Head verbreitert, hier Trunk + angepasstes Sim-Budget).

---

## Top-3-Empfehlungen als konkrete Experimente

**Empfehlung 1: Gemischtes Value-Target λ·z + (1−λ)·q_root (Fund 1, Kosten: fast null)**
Root-completed-Q wird im Self-Play ohnehin berechnet — mitloggen, Value-Target als Mischung labeln (Arme λ∈{1.0 (Baseline), 0.7, 0.5, 0.3}). NICHT das gestorbene rtv-Experiment: keine Zusatz-Suche, kein Zusatz-Head, sondern Varianzreduktion des Haupt-Targets durch einen Wert, der an den Chance-Knoten bereits über Zufallszweige mittelt.
*Erfolgskriterium (prä-registriert, ≥6 gepaarte Seeds):* value_r2_rounds_1_4 steigt um >0.015 gegenüber Baseline (validierte Auflösungsgrenze), danach Arena-Gating ≥200 Spiele gegen den Champion mit Signifikanztest.

**Empfehlung 2: Playout Cap Randomization (Fund 6 = Task #14, Kosten: niedrig-mittel)**
Pro Zug mit p=0.25 volle Suche (600 Sims, Policy+Value-Target), mit p=0.75 Kurzsuche (z.B. 100 Sims, nur Value-Target). Ziel: bei gleichem Wall-Clock-Budget ~2–3× mehr Spiele pro Generation.
*Erfolgskriterium:* Spiele/Stunde ≥2×, value_r2_rounds_1_4 nicht schlechter, Arena-Gating gegen einen mit identischem Compute-Budget klassisch trainierten Kontrollarm.

**Empfehlung 3: Reanalyze-light für das Replay-Fenster (Fund 2, Kosten: mittel)**
Die ~2000 Alt-Champion-Spiele im Fenster vor jedem Training mit dem aktuellen Champion bei 64–100 Gumbel-Sims neu labeln (Value; Policy optional).
*Erfolgskriterium:* A/B mit identischem Fenster, einziger Unterschied relabeled vs. original; Entscheidung über val_combined bei GLEICHEM Epoch-Budget beider Arme (prä-registriert), dann Arena.

**Bewusst NICHT empfohlen:** EfficientZero-Komponenten (reparieren gelernte Modelle), Subtree Value Bias Correction (Go-spezifisch), Determinisierungs-Techniken (symmetrische Stochastik, kein Info-Leck), reine Policy-Hebel als Erstmaßnahme (2×2-Attribution). KataGo-Unsicherheits-Head als Reserve, nur in der rtv-freien Variante.
