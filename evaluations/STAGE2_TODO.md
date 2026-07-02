# Roadmap ab v7 — Stufe 1 erreicht → Stufe 2 + Features

## Status (erreicht)

**Stufe 1 ist zufriedenstellend: v7 schlägt die Heuristik klar.**

| Netz | hidden | vs. Heuristik | Ø Score (Netz:Heur) | 0:0 |
|---|---|---|---|---|
| v4 | 256 | 51 % | 23.4 : 25.0 | — |
| v5 | 256 (warm v4) | 49 % | 23.8 : 28.4 | — |
| v6 | 512 (**cold**) | 45 % | 21.6 : 27.4 | — |
| v7 | 512 (warm v6, ~790k Züge) | 61 % | 27.3 : 26.1 | ~1 % |
| **v8** | **512 (warm v7, +Chip-/Moon-Order-Features, gleiches Datenfenster wie v7)** | **60 %** | **24.7 : 23.9** | **0 %** |

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
