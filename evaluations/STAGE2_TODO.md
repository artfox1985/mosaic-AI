# Roadmap ab v7 — Stufe 1 erreicht → Stufe 2 + Features

## Status (erreicht)

**Stufe 1 ist zufriedenstellend: v7 schlägt die Heuristik klar.**

| Netz | hidden | vs. Heuristik | Ø Score (Netz:Heur) | 0:0 |
|---|---|---|---|---|
| v4 | 256 | 51 % | 23.4 : 25.0 | — |
| v5 | 256 (warm v4) | 49 % | 23.8 : 28.4 | — |
| v6 | 512 (**cold**) | 45 % | 21.6 : 27.4 | — |
| v7 | 512 (warm v6, ~790k Züge) | 61 % | 27.3 : 26.1 | ~1 % |
| v8 | 512 (warm v7, +Chip-/Moon-Order-Features, gleiches Datenfenster wie v7) | 60 % | 24.7 : 23.9 | 0 % |
| v9 | 512 (warm v8, Fenster v3+2000×v4+2000×v8) | 57 % | 25.5 : 25.2 | 0 % |
| v10 | 512 (warm v9, Fenster 2000×v4+v8+v9, v3 raus) | 47 % ⚠️ | 23.6 : 26.4 | 0 % |
| **v11** | **512 (warm v10, gleiches Fenster, Value-Target auf Punkte-Marge umgestellt)** | **55 %** | **24.6 : 26.1** | **0 %** |

v10 fiel erstmals unter 50 % — monotoner Abwärtstrend v7→v10 (61→60→57→47 %),
begleitet von steigendem Value-Loss (0.057→0.098→0.110→0.120). Arena-Gate gegen
v9 nur knapp bestanden (51:49, im Rauschbereich). Siehe Abschnitt D für Diagnose
und Lösungskonzept (Value-Target-Umstellung).

### ⟲ Sauberer Neustart (2026-07-02)

Rückblickend hat kein Netz nach v8 seinen direkten Vorgänger statistisch
signifikant geschlagen (v9 vs. v8: 54:46 z=0.8; v10 vs. v9: 51:49 z=0.2; v11 vs.
v10: 45:55 z=-1.0 — alle im Rauschbereich bei n=100). Neuer Gate-Maßstab:
**≥60:40 (z≈2.0, ~95%-Niveau)** für einen echten Champion-Wechsel. Alle
Self-Play-Daten und Checkpoints (v1-v11 der alten Zählung) gelöscht, Neustart
mit nur den reinen Heuristik-Bootstrap-Daten (`data/archive/selfplay_s100_*.pkl`,
300 Dateien / 3000 Spiele, 100 Sims). Die Tabelle unten zählt ab hier neu bei v1.
Details zum Value-Target-Fix (Partie-Endergebnis statt Win/Loss) weiterhin in
Abschnitt D.

**Champion/Kandidat-Protokoll:** Self-Play wird immer vom aktuellen Champion
generiert, nicht vom zuletzt trainierten Netz. Ein Kandidat wird nur dann neuer
Champion, wenn er den bisherigen Champion mit ≥60:40 schlägt — sonst bleibt der
Champion bestehen und generiert weitere Self-Play-Runden, wodurch sein Anteil im
Trainingsfenster mit jedem gescheiterten Kandidaten wächst.

| Netz | hidden | Champion? | vs. Heuristik | Ø Score (Netz:Heur) | vs. Vorgänger | Ø Score (vs. Vorgänger) |
|---|---|---|---|---|---|---|
| v1 | 512 (cold, 3000 Bootstrap-Spiele) | ja (einzige Option) | 43 % | 19.5 : 25.4 | — | — |
| v2 | 512 (warm v1, Bootstrap+2000×v1) | **nein — v1 bleibt** | 43 % | 22.2 : 27.9 | 51:49 (v2, z=0.2) | 19.6 : 16.9 |

v2 hat v1 im direkten Duell NICHT signifikant geschlagen (51:49, weit unter der
60:40-Schwelle) — trotz leicht besserem Ø-Score. v1 bleibt Champion, generiert
eine zweite Self-Play-Runde (2000 weitere Spiele, kumulativer Netz-Pool → 4000).

**⚠️ Kritischer Bug gefunden und gefixt:** der 30s-Wallclock-Hänger-Schutz in
`self_play.rs` war auf reine Heuristik-Suche kalibriert — netzgeführte Suche
(ONNX-Inferenz pro Simulation) ist deutlich langsamer, wodurch Self-Play-
Partien bei 400 Sims systematisch VOR Rundenende abgeschnitten wurden. Prüfung
ergab: nur **35 von 2000 v1-Self-Play-Partien (1.8%) erreichten Runde 5**. Da
`apply_end_scoring()` nur bei echtem Spielende läuft, waren die aufgezeichneten
`scores`/`winner` dieser Partien kein echtes Ergebnis, sondern Zufalls-
Schnappschüsse — das untergrub das komplette Punkte-Marge-Value-Target. Fix:
separate Timeouts, `NET_GAME_TIMEOUT_SECS=180` für alle netzbeteiligten
Partien (vorher 30s für alle). **Die obige v2-Zeile beruht auf den
korrumpierten Daten und ist mit Vorsicht zu genießen** — v1-Self-Play wird mit
dem Fix neu generiert, v2 wird auf den sauberen Daten neu trainiert und die
Gate-Arena wiederholt.

**v11 (nach Value-Target-Umstellung, Details Abschnitt D Punkt 0): gegen Heuristik
wieder über 50 % (55 %, bester Wert seit v8) und Ø-Score steigt (24.6 vs. v10s
23.6) — ABER gegen den direkten Vorgänger v10 verliert v11 45:55 (Ø-Score 21.4 vs.
23.4), das klassische Arena-Gate ("schlägt den Vorgänger") ist damit NICHT
bestanden. Kollaps-Raten bleiben stabil bis leicht verbessert. Gemischtes
Ergebnis — Details und Interpretation in v11_eval.md und Abschnitt D.**

- v7 übertrifft die Heuristik **erstmals auch im Ø-Score** (27.3 > 26.1), Elo 1049:951,
  0:0 ~1 %. v7 ≈ v5 im Direktduell (Nicht-Transitivität, ok) — Benchmark ist die
  Heuristik, dort ist v7 klar vorn.
- **v8 liegt praktisch gleichauf mit v7** (60 % vs. 61 %, Marge +0.8 vs. +1.2) —
  kein klarer Sprung, aber auch kein Rückschritt. Nachvollziehbar: die neue
  Eingangsschicht (Chip-/Moon-Order-Features) startet bei `INPUT_SIZE`-Änderungen
  frisch (s. Learnings) und muss sich erst wieder einspielen. **Vorsicht bei der
  finalen Elo-Zeile** (v8 992 : Heuristik 1008, wirkt wie eine Niederlage): bei
  Spiel #92 stand es noch 1080:920 für v8, eine kurze Pechsträhne mit mehreren
  Strength-1.0-Niederlagen am Ende hat die pfadabhängige Elo verzerrt — Sieganteil
  (60:40) und Ø-Score (24.7 > 23.9) sind hier die robusteren Kennzahlen.
  **Weiter mit v8** als Ausgangspunkt für v9.

## Learnings (validiert)
- **Größeres Netz hilft — aber nur WARM.** 256 gedeckelt (~49–51 %); 512 **cold**
  (v6) fiel ab (45 %); 512 **warm + mehr Daten** (v7) liefert den Sprung (61 %).
  Regel: großes Netz nie kalt starten; `--load` vom Vorgänger + mehr Daten.
  → Punkt „größeres Netz" damit **erledigt** (v7 ist das 512er).
- ±1-Value-Target, rohe Visit-Targets (N/ΣN), DFS-Blatt (Stufe 1), breites
  DFS-verankertes Fenster, v4/v7 als starke Daten-Generatoren.
- Hänger-Schutz: 30s-Wall-Clock je Partie in allen `play_*`-Schleifen (committet).
- **Erster Stufe-2-Versuch (v7, `--stage 2`) ist kollabiert: 51.8 % 0:0-Spiele
  vs. 17.5 % mit demselben Netz + DFS-Blatt** (isolierender Diagnose-Lauf, kein
  Bug — v7s Value-Head ist als Endergebnis-Klassifikator brauchbar, Loss 0.057,
  aber noch nicht präzise genug als Blattbewertung mitten in der Suche). Siehe
  Abschnitt A — Umstieg jetzt über eine Reifegrad-Sonde statt zu raten.
- **Warm-Start bricht bei `INPUT_SIZE`-Änderungen**, wenn nicht abgefangen:
  `strict=False` toleriert fehlende/zusätzliche Keys, aber KEINE Shape-
  Mismatches bei gleichnamigen Keys (`body.0.weight`). `train.py` filtert
  solche Keys jetzt vorher raus — Rest (Bias, tiefere Schichten, alle Heads)
  bleibt warm-startbar. Bei jeder künftigen `INPUT_SIZE`-Änderung gilt das
  weiterhin (committet, mit State-Dict-Vergleich verifiziert).
- **Alte `.onnx`-Modelle sind nach einer `INPUT_SIZE`-Änderung endgültig tot fürs
  Self-Play/Netz-vs-Netz** (feste Graph-Shape, kein Toleranzmechanismus wie
  `strict=False`) — betrifft nur das Spielen, nicht das `.pth` (Warm-Start bleibt
  möglich) und nicht bereits erzeugte Self-Play-`.pkl`-Daten (rohe States, werden
  frisch kodiert). v7.onnx kann seitdem weder Self-Play generieren noch gegen v8
  antreten — kein Bug, erwartete Konsequenz.
- **Reifegrad-Sonde kann sich zwischen Generationen verschlechtern, auch wenn
  die Spielstärke gleich bleibt.** v8s Faktor lag bei 9.33× (v7: ~3×) — die
  frisch initialisierte Eingangsschicht muss die wertrelevanten Signale nach
  einer `INPUT_SIZE`-Änderung erst neu extrahieren lernen. Kein Alarmsignal,
  aber: nach einem Repräsentationsumbruch (neue Features, Netzvergrößerung)
  eher MEHR Stufe-1-Generationen einplanen, bevor man erneut auf Grün hofft.
  **Korrektur/Einschränkung:** ein Großteil des scheinbaren Rückschritts ist
  Messrauschen, kein echter Effekt — v8s Stufe-1-Basisrate war mit 3 % (3/100)
  viel niedriger als v7s ~17.5–14 % (7/40 bzw. eine frühere Messung), und bei so
  wenigen 0:0-Ereignissen ist die Ratio extrem instabil: ±1 Spiel Unterschied in
  der Stufe-1-Stichprobe verschiebt sie (Laplace-geglättet) zwischen 4.8× und
  14.5×. Mit Glättung: v8 ≈ 7.25× statt roh 9.33×, v7 ≈ 2.68× statt 2.96× — die
  Richtung (v8 schlechter) bleibt, das Ausmaß ist aber deutlich unsicherer als
  die Rohzahlen suggerieren. **Folge für die Sonde selbst:** je sauberer die
  Netze spielen (niedrigere 0:0-Basisrate), desto MEHR Spiele braucht die Sonde
  für ein verlässliches Signal — 40 (train.py-Default) oder auch 100 reichen bei
  einstelliger Prozent-Basisrate nicht mehr für ein präzises Verhältnis, auch
  wenn die Entscheidung „noch nicht reif" davon in diesem Fall nicht berührt war
  (alle plausiblen Werte lagen klar über der 3×-Schwelle).
- **Die Ratio allein kann in die Irre führen — die ABSOLUTE Stufe-2-0:0-Rate
  gehört immer danebengestellt.** Verlauf über die Generationen: v7 51.8 %
  (110 Spiele) → v8 28.0 % (100 Spiele) → **v9 75.0 %** (40 Spiele, 95%-CI
  ~62–88 %) — kein monotoner Trend, v9 ist in absoluten Zahlen das bisher am
  stärksten degenerierte Stufe-2-Self-Play, obwohl seine Ratio (4.43×) besser
  aussah als v8s (~7.25×). Grund: die Ratio normiert nur gegen die jeweilige
  Stufe-1-Basisrate, die selbst stark schwankt (v7 ~17.5 %, v8 3 %, v9 15 %) —
  „Ratio verbessert sich" ist NICHT dasselbe wie „Stufe-2-Qualität verbessert
  sich". Beide Kennzahlen künftig gemeinsam berichten, nicht nur die Ratio.
- **Die finale Elo-Zeile kann täuschen** (pfadabhängig, von einer kurzen
  Pechsträhne am Ende verzerrbar — bei v8 sichtbar: Peak 1080:920 bei Spiel
  #92, Endstand 992:1008 trotz 60:40-Sieganteil). Sieganteil + Ø-Score sind
  die robusteren Kennzahlen für den Generationen-Vergleich.

## A) Stufe 2 — Netz-Value-Blatt (nächster Hauptschritt, jetzt mit Reifegrad-Sonde)

**Status: v8 fertig, Gate bestanden (knapp gleichauf mit v7, s. Status-Tabelle),
Reifegrad-Sonde ROT (9.33× roh / ~7.25× geglättet — v7 lag bei ~2.7–3×; die
genaue Größe der Verschlechterung ist wegen v8s niedriger Stufe-1-Basisrate
[3 %] unsicher, die Richtung — noch nicht reif — aber robust, s. Learnings).**
Entscheidung: **in Stufe 1 bleiben.** v8 erzeugt jetzt 2000 Stufe-1-Self-Play-
Spiele; v9 trainiert darauf
(Fenster **v3+2000×v4+2000×v8**, v2 komplett raus, v4 halbiert) und wiederholt
die Sonde. Der folgende Ablauf gilt weiterhin für den Umstieg, sobald die Sonde
grün ausschlägt — **nicht mehr blind versuchen** (der v7-Versuch kostete einen
vollen Self-Play-Zyklus, bevor der Kollaps auffiel).

### Reifegrad-Sonde (nach jeder Stufe-1-Generation, die das Heuristik-Gate besteht)
Läuft automatisch nach jedem `train.py`-Lauf (`run_readiness_probe`, Default
**100 Spiele je Stufe**, 400 Sims — auf 100 angehoben, da 40 Spiele bei niedrigen
0:0-Basisraten [v9: 15 %/75 %] eine zu schwache Absicherung waren, s. Learnings).
Manuell (falls nötig) äquivalent:

```
python self_play.py --mode network --model alphazero_<gen>.onnx --stage 1 \
    --games 100 --sims 400 --version <gen>_probe_s1 --threads 0
python self_play.py --mode network --model alphazero_<gen>.onnx --stage 2 \
    --games 100 --sims 400 --version <gen>_probe_s2 --threads 0
# 0:0-Rate + Ø Sieger-Score je Lauf vergleichen; Probe-Daten danach löschen
# (kein Regen-Zyklus, reine Messung).
```

**Ampel** (Verhältnis 0:0(Stufe2) / 0:0(Stufe1) — normalisiert aufs jeweilige
Stufe-1-Grundrauschen der Generation):
- **≤ ~1.5×** → Value-Head trägt, voller Stufe-2-Zyklus lohnt sich.
- **1.5×–3×** → noch nicht reif, Trend über Generationen beobachten, Stufe 1
  weiter iterieren.
- **> 3×** (v7: 3.7×/2.96× — 51.8 % vs. 17.5 %; **v8: 9.33× roh / ~7.25×
  geglättet — 28.0 % vs. 3.0 %, Basisrate niedrig → Zahl unsicher, s. Learnings**)
  → klar nicht reif, keinen Stufe-2-Zyklus starten, Probe bei der nächsten Gen
  wiederholen. **Bei niedriger Stufe-1-Basisrate (einstellige %) die Ratio per
  Laplace-Glättung berechnen und die Sonde mit mehr Spielen laufen lassen** —
  sonst kann ±1 Spiel das Ergebnis um mehrere hundert Prozent verschieben.

### Bei Grün: voller Stufe-2-Zyklus
- Self-Play groß mit `--stage 2` (`dfs_leaf=False`), z. B. 1500–2000 Spiele.
  Mehrrunden-Weitblick statt der Ein-Runden-Myopie des DFS; Stage-2-Sims sind
  billiger (Netz-Forward statt Netz-Forward+DFS pro Sim).
- Training warm vom Reifegrad-Netz (`--load <gen> --hidden 512`).
- Erste Stufe-2-Generation: **Mix** aus Stufe-1-Restfenster (reduziert) + den
  neuen Stufe-2-Daten — verhindert, dass die DFS-myopischen Alt-Targets die
  neuen Mehrrunden-Targets zahlenmäßig erschlagen. Über folgende Gens den
  Stufe-1-Anteil schrittweise rausrollen.
- **Arena-Gating**: die neue Gen nur übernehmen, wenn sie den Vorgänger schlägt;
  sonst **zurück auf Stufe 1** für die nächste Generation — kein zweiter
  blinder Stufe-2-Versuch in Folge.

### Bei Gelb/Rot
Normale Stufe-1-Daten erzeugen (wie bisher), nächste Generation trainieren,
Sonde dort wiederholen. Iterieren, bis Grün.

## B) Feature-Upgrades (Repräsentation) — ✅ ERLEDIGT (in v8 eingeflossen)
Ursprünglich als „erst nach eingependelter Stufe 2" geplant, aber vorgezogen
und direkt gemeinsam mit v8 umgesetzt:
1. **Bonuschip-Farben pro Fabrik** — 5-dim Farbmaske je kleiner Fabrik, NUR wenn
   `chip_revealed=true` (sonst versteckte Information). `INPUT_SIZE` 664→684.
   Verifiziert: verdeckte Chips liefern Null-Maske trotz echter Farben im
   rohen JSON, aufgedeckte matchen exakt. (Commit `fddc221`)
2. **Moon-Order aktiv wählen, suche-getrieben (Geminis Ansatz)** — umgesetzt
   OHNE `NUM_ACTIONS` aufzublähen: 482-dim Head bleibt auf Farbe+Reihe
   beschränkt (maskierte Softmax über eindeutige IDs), Permutations-Priors
   kommen separat aus dem `moon_order_head` per **Plackett-Luce** (sequenzieller
   Softmax über die 5 rohen Farb-Scores), kombiniert beim Expandieren eines
   `SmallFactorySun`-Knotens: `P(Zug) = P(Basis) × P(Order)`. Lokal in
   `net_mcts.rs::build_untried_actions` (pur testbar, 4 neue Tests), `generate_valid_moves`
   unverändert (betrifft nur die Netz-Suche). `moon_order_head`-Loss von
   MSE-Rang-Regression auf Plackett-Luce-NLL umgestellt (`train.py`); dabei
   einen echten Bug gefunden+behoben (`sun_mask` prüfte nur Spalte „blau").
   End-to-end verifiziert: Self-Play erkundet aktiv mehrere Moon-Order-
   Varianten (bis zu 6/Gruppe). (Commits `c01c305`, `c27b951`)

Damit sind auch die Chip-/Moon-Order-Daten in v8 bereits die volle Baseline für
die Reifegrad-Sonde oben — kein separater Feature-Rollout mehr nötig.

## C) Daten/Fenster (Begleitthema)
- DFS-verankerte Daten → altes bleibt brauchbar, breites Fenster günstig.
- **Korrektur:** Das Fenster wurde von v4 bis v8 tatsächlich NIE fortbewegt —
  v5/v6/v7/v8 trainierten alle auf demselben v2+v3+4000×v4-Fenster (der geplante
  v7-Self-Play-Beitrag scheiterte an der `INPUT_SIZE`-Inkompatibilität, s.
  Learnings, und wurde nie Teil des Fensters). **v9 ist der erste echte
  Fenster-Fortschritt**: v2 komplett raus, v4 halbiert (4000→2000), dazu
  2000×v8 — verhindert, dass die neuen v8-Daten von der alten v4-Masse
  erschlagen werden.
- Ab ~Gen 5 (jetzt erreicht) die **älteste** Generation rausrollen; fürs 512er
  Richtung **3000–5000 Spiele** im Fenster (v7 lief auf ~790k Züge / ~5000 Spiele).

## D) Einseitige Kollapse — Diagnose & Lösungskonzept

**Klarstellung des eigentlichen Ziels** (wichtig für alles Folgende): Heuristik
schlagen war nie das Ziel selbst, sondern ein Proxy/Nebeneffekt. Das eigentliche
Ziel: **hohe absolute Punktzahl, menschen-kompetitiv (gute Menschen erreichen
60+).** Ein Spiel, in dem eine Seite nahe 0 Punkte macht, ist fragwürdig für
diese Seite — unabhängig davon, wer "gewonnen" hat. Bisher gab es dafür nur den
beidseitigen 0:0-Indikator; einseitige Blowouts (eine Seite ≤5, andere ≥15)
wurden nie erfasst.

### Diagnose (an allen vollständigen Arena-Logs v7–v10 gemessen, je 100 Spiele)

**vs. Heuristik:**
| Gen | Ø Score | Max | Einseitig (eine ≤5, andere ≥15) | davon: Netz kollabiert | Heuristik kollabiert |
|---|---|---|---|---|---|
| v7 | 27.3:26.1 | 74 | 20 % | 10 % | 10 % |
| v8 | 24.7:23.9 | 70 | 11 % | 6 % | 5 % |
| v9 | 25.5:25.2 | 62 | 22 % | **15 %** | 7 % |
| v10 | 23.6:26.4 | 65 | 18 % | **11 %** | 7 % |

**Netz-vs-Netz (zum Vergleich):**
| Matchup | Ø Score | Einseitig | Irgendeine Seite ≤5 |
|---|---|---|---|
| v9 vs. v8 | 14.9:16.1 | 17 % | 35 % |
| v10 vs. v9 | 13.1:12.4 | 20 % | **46 %** |

**Drei Kernbefunde:**
1. **Die einseitige Kollaps-Rate (11–22 %) ist über alle Generationen persistent
   vorhanden — kein neues v10-Problem, aber bisher nie gemessen.**
2. **Netz-vs-Netz-Spiele kollabieren strukturell viel häufiger** (Ø-Score fast
   halbiert, "irgendeine Seite ≤5" fast verdoppelt ggü. Netz-vs-Heuristik).
   Self-Play-artige Matchups sind ein deutlich instabileres Umfeld als das Spiel
   gegen einen strukturell andersartigen Gegner.
3. **Ab v9 kippt die Balance beim Netz-vs-Heuristik-Kollaps klar zulasten des
   Netzes** (15 %/11 % vs. Heuristiks 7 %/7 % — bei v7/v8 noch ausgeglichen
   ~10/10, 6/5). Timt exakt mit dem Sieganteil-Einbruch — es ist also nicht
   "die Heuristik wird relativ stärker", sondern **das Netz selbst wird
   kollaps-anfälliger.**

**Ursachen-Kette (Arbeitshypothese, gut gestützt):** Das Trainingsfenster besteht
ausschließlich aus Netz-Self-Play (nie echten Heuristik-Spieldaten, s. Learnings).
Je mehr das Fenster sich zu reinem, jüngerem Self-Play verengt (v2/v3 raus, v4
könnte folgen), desto mehr übernimmt die trainierte Policy die kollaps-anfällige
Dynamik aus Netz-vs-Netz-Spielen — sichtbar als **erzwungenes Floor-Dumping**
(Strafleisten-Bias-Check zeigt konsistent 0 Fälle mit legaler Reihen-Alternative
bei Floor-Top-Wahl — das ist also situativ erzwungen, nicht vermeidbare
Fehlentscheidung im Moment; das Problem entsteht früher im Draft).

### Lösungskonzept

0. **Kernfix — Value-Target von Win/Loss auf Partie-Endergebnis-Punkte
   umgestellt (bereits umgesetzt):** Punkte 1–4 unten sind alles Diagnose-/
   Diversitäts-Maßnahmen, greifen aber nicht den eigentlichen Grund an, warum
   das Netz Marge nicht lernt: das Value-Target war `±1` (Sieger/Verlierer),
   also sind ein 30:29- und ein 60:0-Sieg für den Trainings-Loss IDENTISCH —
   nirgends ein Signal "größerer Vorsprung ist besser" bzw. "knapp verlieren
   ist besser als kollabieren". Widerspricht direkt dem Ziel ("schlussendlich
   gewinnt, wer die meisten Punkte macht").
   Fix in `engine/py/neural_net.py` (`VALUE_SCHEMA_VERSION = 8`):
   ```
   own_total = step["scores"][eigener Spieler]   # inkl. Wertungsplatten
   opp_total = step["scores"][Gegner]
   value = tanh((own_total − 0.5 · opp_total) / 50)
   ```
   als Ziel für JEDEN Schritt der Partie — klassisches AlphaZero-Prinzip
   (delayed reward): der Zielwert für einen Runde-1-Zustand ist derselbe wie
   für den letzten Zug, nämlich wie das Spiel am Ende wirklich ausging.
   `step["scores"]` enthält die Wertungsplatten-Endwertung bereits
   (`apply_end_scoring()` in Rust rechnet sie vor dem Serialisieren ein).
   **Zwischenstände verworfen (Nutzer-Korrektur):** ursprünglich war hier ein
   dichtes Zwischensignal geplant (`own.score + own.estimated_score`, exakte
   DFS-Projektion NUR der laufenden Runde). Das wurde bewusst wieder
   entfernt: die Heuristik maximiert bereits gierig die Rundenpunkte, hat
   aber keine Weitsicht (kein strategischer Board-Aufbau, keine
   Wertungsplatten-Berücksichtigung). Ein Rundenprojektions-Ziel hätte dem
   Netz genau diesen gierigen Rundenoptimum-Bias beigebracht — Runde 1/2
   bewusst suboptimal spielen, um durch strategischen Aufbau in Runde 3/4
   viel mehr zu holen, wäre damit NICHT belohnt worden, weil der Zielwert
   für Runde-1-Zustände Runde 3/4 gar nicht kennt. Das reine
   Partie-Endergebnis als Ziel lernt automatisch, dass ein scheinbar
   suboptimaler früher Zustand gut ist, WENN er zuverlässig zu einem
   starken Endergebnis führt — das ist genau die Weitsicht, die der
   Heuristik fehlt.
   Gewichtung (0.5) auf die gegnerische Seite statt reiner Differenz: ein
   10:5 und ein 65:60 (beide Marge 5) wären bei reiner Differenz identisch
   bewertet, obwohl 65:60 absolut deutlich mehr erreichte Punkte sind
   (own−0.5·opp: 10−2.5=7.5 vs. 65−30=35 — klar unterschieden).
   **Kompromiss:** die Gewichtung macht das Target nicht mehr exakt
   antisymmetrisch (`value(p0) ≠ -value(p1)`), was der Zero-Sum-Annahme der
   Suche (`net_mcts.rs`: 1 Netzquery aus Sicht des Ziehenden, Gegnerwert wird
   als `1 - win` angenommen) nur noch näherungsweise entspricht. Akzeptiert,
   weil das eigentliche Ziel (hohe absolute Punktzahl statt nur "irgendwie
   gewinnen") das explizit verlangt.
   Auswirkung: keine Self-Play-Regeneration nötig (Rohdaten enthalten
   `scores`/`winner` bereits pro Schritt), nur ein HDF5-Cache-Rebuild beim
   nächsten Training (`VALUE_SCHEMA_VERSION` im Cache-Key). Gewicht (0.5)
   und Skala sind erste Ansätze, ggf. nach weiteren Messungen nachjustieren.
   **Skala nachträglich auf 50 korrigiert** (ursprünglich 25, aus der
   Streuung damaliger Spieldaten abgeleitet): Heuristik und Netz spielen
   beide noch schwach, jede aus AKTUELLEN Spieldaten abgeleitete Skala hätte
   nur diese Schwäche festgeschrieben statt das echte Punktepotenzial
   abzubilden. Neu kalibriert an einem groben menschlichen Referenzwert
   (ab ~100 Punkten gilt ein Ergebnis als sehr gut): bei own≈100 gegen einen
   soliden Gegner (opp≈40) ergibt own−0.5·opp≈80, Skala 50 legt den
   tanh-Arg an diesem Punkt auf ~1.6 (tanh≈0.92) — informativ, nicht schon
   voll gesättigt.
   **Verifiziert an v11 (warm-start v10, gleiches Fenster) — gemischtes
   Ergebnis:** vs. Heuristik deutlich verbessert (55 % Siege, bester Wert
   seit v8, vs. v10s 47 %; Ø-Score 24.6 vs. v10s 23.6). Kollaps-Raten
   stabil/leicht verbessert (one-sided 15 % vs. v10s 18 %). ABER: das
   klassische Arena-Gate ("schlägt den direkten Vorgänger") ist NICHT
   bestanden — v11 verliert 45:55 gegen v10, auch im Ø-Score (21.4 vs. 23.4).
   Einordnung: v10 selbst hatte im Vorgänger-Duell (v9) nur hauchdünn
   gewonnen (51:49) und war schon damals als instabiles Signal markiert
   (siehe v10-Zeile oben) — direkte Netz-vs-Netz-Duelle scheinen generell
   nicht-transitiv/verrauscht zu sein. Nach den erweiterten Kriterien aus
   Punkt 3 (Ø-Score, Kollaps-Rate statt nur Win/Loss) spricht mehr für v11
   als dagegen, aber das reine Win/Loss-Gate widerspricht dem. Details in
   `v11_eval.md`. **Ob v11 die neue Baseline wird, ist ein Nutzer-Call.**
   Nebenbefund: `VALUE_WEIGHT` musste ebenfalls auf 2.5 hochskaliert werden
   (0.5 vorher), weil das neue Target eine ~4.6x kleinere Streuung hat als
   das alte ±1-Ziel (an ~27k echten Schritten gemessen: std≈0.22 vs. 1.0) —
   sonst hätte der Value-Head unter dem neuen Target kaum noch trainiert.
   Zusätzlich musste Early-Stopping in `train.py` entkoppelt werden (stoppt
   jetzt erst, wenn Policy UND Value plateauen, nicht nur Policy) — der erste
   v11-Trainingsversuch brach ab, während der Value-Head noch mitten in der
   Konvergenz war (v_pred σ 0.154→0.174 wachsend), was zu einer sichtbar
   schlechteren Stage-2-Sonde führte (56 % statt 39 % 0:0-Rate). Nach dem Fix
   lief das Training alle 100 Epochen durch, σ wuchs weiter auf 0.190, und
   die Stage-2-Sonde normalisierte sich wieder auf v10-Niveau (40 %).
   **Nachtrag — `VALUE_WEIGHT` mit hochskaliert (config.py, 0.5 → 2.5):** das
   neue Target hat eine deutlich kleinere charakteristische Streuung als das
   alte ±1-Ziel (Stichprobe über ~27k reale Self-Play-Schritte: std≈0.22 vs.
   1.0 vorher, Faktor ~4.6). Ohne Anpassung von `VALUE_WEIGHT`
   (`loss = v_loss·VALUE_WEIGHT + p_loss`) wäre der Value-Loss-Beitrag zum
   Gesamtloss weiter geschrumpft und der Value-Head faktisch kaum noch
   trainiert worden — das genaue Gegenteil vom Zweck dieser Änderung. 2.5
   ist ebenfalls ein erster Ansatz (grob am Streuungs-Verhältnis kalibriert,
   nicht exakt hergeleitet), an den frühen v11-Epochen (Value:Policy-Anteil
   im Log) zu verifizieren/nachjustieren.
1. **Diversität ins Self-Play zurückbringen (ergänzend, nicht Ersatz für 0):** einen Anteil der
   Self-Play-Partien als **Netz-vs-Heuristik** generieren (analog `play_net_game`
   in `self_play.rs`, Aufzeichnung für die Netz-Seite), NICHT um "Heuristik
   schlagen" zum Ziel zu machen, sondern als Mittel gegen die Selbstähnlichkeits-
   Kollaps-Dynamik — ein strukturell andersartiger Sparringspartner bricht die
   "beide Seiten teilen dieselben blinden Flecken"-Dynamik auf.
2. **Neue Standard-Kennzahl: einseitige Kollaps-Rate** (eine Seite ≤5, andere
   ≥15) in die reguläre Arena-/Sonden-Auswertung aufnehmen, neben 0:0-Rate und
   Sieganteil — hätte den v9-Knick schon 1 Generation früher sichtbar gemacht,
   statt erst nachträglich per Log-Analyse.
3. **Arena-Gate erweitern:** "Sieg gegen Vorgänger" (Win/Loss) allein hat den
   v10-Rückschritt nicht verhindert (51:49 "bestanden", aber Robustheit sank).
   Gate um Ø-Score-Marge UND Kollaps-Rate ergänzen — bei „schlussendlich gewinnt,
   wer die meisten Punkte macht" sollte die Punktzahl/Robustheit stärker
   gewichtet werden als reines Win/Loss.
4. **Optional/später — Root-Cause im Draft:** untersuchen, WANN im Spiel sich
   die erzwungenen Floor-Situationen anbahnen (z. B. Farb-Hortung früh im Draft,
   die später Musterreihen-Konflikte erzwingt) — würde eine gezieltere Korrektur
   als reine Datendiversität ermöglichen.

## Gating / Verifikation
- Je Generation: `run_net_arena(v_neu vs Heuristik, 200/200, 100)` +
  `run_net_vs_net(v_neu vs Vorgänger)`; übernehmen nur bei Sieg gegen den Vorgänger.
- Vor jedem vollen Stufe-2-Zyklus zusätzlich: **Reifegrad-Sonde** (Abschnitt A) —
  nur bei grüner Ampel den großen Self-Play+Training-Zyklus starten.
- Feature-Änderung: `len(state_to_tensor(sample)) == INPUT_SIZE`, Rust/Python-Parität
  bit-genau, `cargo test` grün, `MosaicDataset` baut fehlerfrei.
- 0:0-Indikator beobachten (~1 % Arena / ~14 % Self-Play, stabil); falls steigend →
  gezielter 0:0-Sonderfall (Draw=0), nicht die alte abgestufte Skala.

## Offene Baustelle
- Seltener Nicht-Terminierungs-Bug (~1/800 Partien, durch 30s-Timeout abgefangen,
  Root-Cause offen) — irgendwann sauber diagnostizieren.
