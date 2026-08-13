# Vorregistrierung: λ-Misch-Value-Target-Experiment (soft-Z)

**Angelegt 2026-08-02, VOR dem ersten der 24 Trainingsläufe.** Zweck: prüfen,
ob das Mischen des Root-Suchwerts (`root_q`) in das HAUPT-Value-Target die
Zielvarianz senkt und dadurch die Netzqualität hebt — Literatur: Willemsen,
Aandewiel, van den Herik & Plaat 2021, "TD-error as initial priority in
prioritized experience replay" bzw. das dort referenzierte "soft-Z"-Verfahren
(Value-Target = gewichtete Mischung aus Spielausgang `z` und Root-Suchwert
`q_root` statt reinem `z`) — ADAPTIERT auf `q_root` = tatsächlicher
Root-Completed-Q-Wert der beim Zug durchgeführten Gumbel-Suche (siehe
Abschnitt "Datengrundlage"). Die Regeln unten dürfen nach Sichtung der
Zwischenergebnisse NICHT mehr geändert werden (Präzedenzfall
`PREREG_ownership_gumbel.md`/`PREREG_corpus_dose.md`).

---

## Abgrenzung zum rtv-Experiment (WICHTIG, keine Verwechslung)

Dieses Experiment ist **NICHT** das `round_transition_value`-Experiment
(`rtv`, Task #84/#85, Memory `project_v13_cycle_result`) und **KEIN**
Zusatz-Task oder Zusatz-Suche:

| | `rtv` (rtv-Ablation, 2026-07-24/28) | `root_q`-λ-Mix (dieses Experiment) |
|---|---|---|
| Quelle | separater rekursiver Chance-Node-Sample über mögliche Fabrik-Neubefüllungen (`round_transition.rs`), NUR bei echten Rundenübergängen (~4×/Partie) | Root-Completed-Q der **ohnehin durchgeführten** Zug-Suche (`net_mcts.rs`/Gumbel), praktisch bei **jedem** Mehr-Aktionen-Drafting-Zug |
| Zusatzkosten | ~81% der Self-Play-Kosten (Task #80) — eigener teurer Suchlauf | **keine** — reines Logging eines bereits berechneten Werts (Commit 2718b9a) |
| Wirkung im Cache-Bau | **ERSETZT** `val`/`points_val` vollständig, wo vorhanden (Teil der `VALUE_SCHEMA_VERSION`-Formel) | **verändert `values`/`points_forecast` beim Cache-Bau NICHT** — bleibt roh im Cache, Mix passiert train-zeitlich |
| Befund | `nortv` (rtv AUS) schlägt `default` (rtv AN) — rtv trug keine Stärke bei, Projektstandard ist seit 2026-07-28 `nortv` | offen — genau das prüft dieses Experiment |
| Ziel | Kosten sparen ohne Stärke zu verlieren | **Varianzreduktion des HAUPT-Value-Targets** (andere Motivation: `z` ist laut Noise-Floor-Test rundenabhängig sehr verrauscht, siehe `evaluations/value head tests.txt` Punkt 6/`TD_LAMBDA`) |

Kurz: `rtv` ist tot (Projektstandard `nortv`, rtv-Override bleibt für
`value_target_variant="nortv"` immer deaktiviert) — dieses Experiment mischt
etwas **komplett anderes, kostenloses** in das ohnehin nach `nortv`
berechnete Ziel. Kein Bezug, keine Reaktivierung von rtv.

## Frage

Senkt `target = λ·z + (1-λ)·root_q` (bei unverändertem `nortv`-Rezept, also
`z` = die aktuelle `VALUE_SCHEMA_VERSION=15`-Formel inkl. TD-Bootstrap-Blend,
OHNE rtv) die Zielvarianz genug, um `value_r2_rounds_1_4` messbar zu heben —
und überträgt sich das (falls ja) in eine Arena-Stärke, die den amtierenden
Champion schlägt?

## Datengrundlage

Seit Commit 2718b9a (2026-08-01) tragen Self-Play-Records optional das Feld
`root_q` ([0,1]-Skala wie `rtv`, Remap auf [-1,1] per `*2.0-1.0` beim
Cache-Bau, siehe `engine/py/neural_net.py::MosaicDataset` /
`ROOT_Q_CACHE_FIELDS`-Kommentar). Im aktuellen 900-Datei-Fenster (Stand
2026-08-02, `data/`) haben **nur die 600 `selfplay_v18_*`-Dateien** dieses
Feld — die 300 älteren Dateien (200 `v17` + 100 `v16`) haben es NICHT (vor
Commit 2718b9a erzeugt). Records ohne `root_q` (Ein-Aktion-Züge JEDER
Generation, Tiling-/Start-Schritte, alle `v16`/`v17`-Records): Fallback =
reines `z` (Präsenz-Maske 0), unabhängig von λ.

**Der Misch-Anteil auf SAMPLE-Ebene (nicht Datei-Ebene) wird von
`tools/train_lambda_sweep.py --build-only` exakt bestimmt** (scannt alle
`v18`-Dateien des eingefrorenen Fensters, zählt Records mit `root_q`) und in
`evaluations/train_lambda_sweep_split.json` persistiert — er ist NIEDRIGER
als der Datei-Anteil (600/900 ≈ 66,7%), weil `root_q` selbst innerhalb der
`v18`-Dateien nur bei Mehr-Aktionen-Drafting-Zügen geloggt wird (Tiling-/
Start-/Ein-Aktion-Schritte bleiben immer ohne). Der exakte Wert wird VOR dem
ersten Trainingslauf im Manifest festgehalten und hier nach dem Build-Schritt
nachgetragen (Platzhalter, bis `--build-only` gelaufen ist):

> **Sample-Misch-Anteil (gesamtes 900-Datei-Fenster): 640.246 von 1.460.731
> Samples = 43,83%** (`train_lambda_sweep_split.json::sample_root_q_frac`,
> gemessen beim `--build-only`-Schritt 2026-08-02 — nachgetragen wie oben
> vorgesehen, VOR Sichtung irgendeines Trainingsergebnisses).

## Arme

| Arm | λ | Bedeutung |
|---|---|---|
| `lam10` (Baseline) | 1.0 | reines `z`, byte-identisches Bestandsverhalten (`--value-target-lambda` Default) |
| `lam07` | 0.7 | leichter Mix |
| `lam05` | 0.5 | hälftiger Mix |
| `lam03` | 0.3 | starker Mix |

Alle 4 Arme **from scratch** (KEIN `--load`) — Präzedenzfall
`PREREG_corpus_dose.md`/`project_v14_rebuild`: ein warmgestarteter Arm gegen
from-scratch-Arme würde die λ-Frage mit der Warm-Start-Frage konfundieren.
Identisches Rezept, identische Architektur (flacher Encoder), identischer
Korpus — einziger Unterschied zwischen den 4 Armen ist `--value-target-lambda`.

## Rezept (from-scratch-Standard, identisch zum Korpus-Dosis-Vorbild)

```
python train.py --name <arm>_s<seed> --seed <seed> \
    --epochs 40 --lr 4e-4 --lr-schedule cosine \
    --value-target-variant nortv \
    --value-target-lambda <λ> \
    --no-plot --no-snapshot
```

(flacher Encoder, `--encoder` NICHT gesetzt, Bestandsdefault.)

- `--epochs 40`, `--lr 4e-4`, `--lr-schedule cosine`: from-scratch-Standard.
- `--value-target-variant nortv`: Projektstandard seit 2026-07-28, für ALLE
  4 Arme identisch — der λ-Mix wirkt AUF das `nortv`-Ergebnis, ersetzt es
  nicht.
- `--value-target-lambda`: einzige Variable zwischen den Armen (1.0/0.7/0.5/0.3).
- Kein `--train-file-limit`, kein `--exclude-round5`, kein
  `--ownership-weight`, keine `--points-dist-bins` — Bestandsdefault, für
  alle 4 Arme identisch.
- `--val-frac` Standarddefault (0,1), Val-Split-Seed `20260707` — für ALLE
  Arme identisch (derselbe eingefrorene 900-Datei-Korpus, siehe unten, also
  auch derselbe Val-Split über alle 4 Arme hinweg, anders als bei
  `PREREG_corpus_dose.md`, wo `voll`/`halb` unterschiedliche Korpusgrößen
  hatten).

## Korpus: eingefrorenes 900-Datei-Fenster (identischer Sandbox-Mechanismus)

Wie `PREREG_corpus_dose.md`: `tools/train_lambda_sweep.py` baut EINE
eingefrorene Hardlink-Sandbox `data_lambda_sweep/` (900 Dateien: 600 `v18` +
200 `v17` + 100 `v16`, Split-Manifest `evaluations/train_lambda_sweep_split.json`)
und setzt `MOSAIC_DATA_DIR` für alle 24 `train.py`-Subprozesse darauf — anders
als bei der Korpus-Dosis-Vorstudie gibt es hier nur EINE Korpusgröße (alle 4
Arme sehen denselben Korpus), die Sandbox schützt trotzdem vor Verzerrung
durch parallel laufendes Self-Play (aktuell `v19`, außerhalb des Fensters,
siehe `classify_corpus`-Logik). `data/` wird nur einmalig gelesen, nie
verschoben/umbenannt (Memory `project_onedrive_file_disappearance`).

## Seeds

**6 gepaarte Seeds** (1..6) je Arm — Memory `project_training_seed_variance`.
4 Arme × 6 Seeds = **24 Läufe gesamt**: `lam10_s1..s6`, `lam07_s1..s6`,
`lam05_s1..s6`, `lam03_s1..s6`.

## Entscheidungsmetriken (VORAB festgelegt)

### Primär (trägt die Varianzreduktions-Hypothese)

`value_r2_rounds_1_4` (klassische Metrik, `tools/offline_diagnosis.py --frozen`)
— **gepaart je Seed, `lam07`/`lam05`/`lam03` je EINZELN gegen `lam10`
(Baseline)**, 3 separate gepaarte Auswertungen (t-Test + Vorzeichentest,
identischer Code wie `train_corpus_dose.py`).

**Bekannte Auflösungsgrenze** (Memory `project_offline_metric_resolution_limit`):
`value_r2_rounds_1_4` löst erst OBERHALB ~0,015 Ø-Abstand verlässlich auf
(3/3 groß, 0/3 klein in der bisherigen Historie) — **nur Abstände über dieser
Schwelle gelten hier als Signal**, kleinere gepaarte Differenzen (auch mit
p<0,05) werden als "kein interpretierbarer Befund" behandelt, nicht als
Null-Ergebnis UND nicht als Bestätigung.

Normalerweise ist `value_r2_rounds_1_4` bei diesem Projekt nur
Sekundär-/Informativ-Metrik (die beiden Orakel-Metriken sind die einzigen
arena-validierten Prädiktoren, siehe unten) — hier ist es bewusst PRIMÄR,
weil die Hypothese direkt die Varianz des VALUE-Ziels betrifft, dessen Fit
`value_r2_rounds_1_4` unmittelbar misst; die Orakel-Metriken messen dagegen
die POLICY-Seite, die vom λ-Mix nicht direkt berührt wird (siehe unten).

### Sekundär (Sanity-Check, KEIN erwarteter Effekt)

Die zwei arena-validierten Orakel-Metriken (Memory
`project_oracle_metrics_validated`, `tools/offline_diagnosis.py::ORACLE_KEYS`):

- `prior_mass_on_oracle_top3`
- `kendall_tau_policy_vs_oracle_q`

**Erwartung: UNVERÄNDERT** zwischen den Armen — der λ-Mix wirkt ausschließlich
auf den Value-Head-Trainingsverlauf (gemeinsamer Trunk könnte theoretisch
indirekt die Policy beeinflussen, das ist der Grund, warum diese Metriken
trotzdem mitgemessen werden). Ein Ausschlag hier (in irgendeine Richtung)
wäre ein Sanity-Check-Alarm ("λ macht etwas an der Policy kaputt/besser, das
nicht die Absicht war"), KEIN Entscheidungskriterium für "λ hilft" — bei
einem Ausschlag wird die Interpretation manuell geprüft, bevor irgendeine
weitere Empfehlung ausgesprochen wird.

### Entscheidend fürs Übernehmen: Arena-Gating (ERST NACH den Offline-Ergebnissen)

**Kein automatisches Champion-Gating als Teil des Sweeps.** Ablauf:

1. Alle 24 Läufe + `offline_diagnosis --frozen` + die 3 gepaarten
   Primär-/Sekundär-Auswertungen fertigstellen.
2. **Bester λ-Arm** = der Arm unter `{lam07, lam05, lam03}` mit der größten
   POSITIVEN gepaarten Ø-Differenz auf `value_r2_rounds_1_4` gegen `lam10`
   — NUR falls diese Differenz über der 0,015-Auflösungsgrenze liegt. Liegt
   KEIN Arm über der Schwelle (alle drei ≤0,015 Abstand zur Baseline, in
   welche Richtung auch immer), gilt die Hypothese als nicht bestätigt —
   **kein Arena-Schritt**, siehe Interpretationsregeln unten.
3. Nur wenn Schritt 2 einen Arm bestimmt: **Arena-Gating des besten λ-Arms
   gegen `lam10` (Baseline)**, NICHT gegen den amtierenden Champion (das ist
   eine reine Ablations-vs-Ablations-Frage, kein Champion-Kandidat-Test) —
   `tools/paired_gating.py`, Standardeinstellung (`DEFAULT_SIMS=400`,
   `MAX_PAIRS=200` → harter Deckel 200 Paare = **400 Spiele**, McNemar-Test
   als finale Bericht-Statistik):
   ```
   python tools/paired_gating.py \
       --model-a models/alphazero_<bester_arm>_best.onnx \
       --model-b models/alphazero_lam10_best.onnx \
       --name-a <bester_arm>_best --name-b lam10_best \
       --sims 400 --no-promote-winner
   ```
   (`--no-promote-winner`: dies ist eine Ablationsentscheidung, KEIN
   Champion-Wechsel — `models/champion.txt` bleibt unberührt, unabhängig vom
   Ausgang. Ein tatsächlicher Champion-Wechsel wäre ein SEPARATER,
   nachgelagerter Schritt gegen den amtierenden Champion, außerhalb dieser
   Vorregistrierung.)
   ("400 Paare" im Auftrag ist deckungsgleich mit `paired_gating.py`s
   dokumentiertem "harter Deckel 200 Paare (= 400 Spiele)" gemeint — die
   Standardeinstellung des Tools wird unverändert übernommen, kein
   `--max-pairs`-Override.)
4. Nur ein **arena-signifikanter Sieg** (McNemar p<0,05 zugunsten des
   λ-Arms) gilt als hinreichend fürs Übernehmen von `--value-target-lambda`
   als neuen Trainings-Standard. Ein Offline-Signal OHNE Arena-Bestätigung
   bleibt eine Beobachtung, kein Rezeptwechsel (Präzedenzfall: Offline-Metriken
   sind laut Memory `project_offline_metric_resolution_limit` nicht 1:1
   arena-prädiktiv unterhalb ihrer Auflösungsgrenze; die Orakel-Metriken SIND
   validiert, aber hier nur Sekundär/Sanity, weil sie die falsche Seite des
   Netzes messen).

## Interpretationsregeln (VORAB festgelegt)

- **Kein Arm über der 0,015-Auflösungsgrenze auf `value_r2_rounds_1_4`**:
  Varianzreduktion durch `root_q`-Mix trägt (in diesem Datenregime, mit nur
  600/900 Dateien mit `root_q`) nicht messbar bei. KEIN Arena-Schritt.
  Empfehlung: Experiment ruhen lassen, bis ein größerer Anteil des Korpus
  `root_q` trägt (mehr `v18`+-Self-Play), dann wiederholen.
- **Genau ein Arm über der Schwelle, positiv**: dieser Arm geht in den
  Arena-Gating-Schritt (siehe oben).
- **Mehrere Arme über der Schwelle, positiv**: der Arm mit der GRÖSSTEN
  gepaarten Ø-Differenz geht in den Arena-Schritt (nicht automatisch der
  extremste λ-Wert — die Dosis-Wirkungs-Form ist nicht vorab bekannt).
- **Ein oder mehrere Arme über der Schwelle, aber NEGATIV** (λ-Mix
  verschlechtert `value_r2_rounds_1_4`): Hypothese widerlegt für diese
  Richtung — kein Arena-Schritt für diese Arme. Sind ALLE informativen
  Abstände negativ, gilt das Experiment als "λ<1 schadet in diesem Regime"
  (eigener, klarer Befund).
- **Sekundär-Metriken (Orakel) schlagen aus**: manuelle Prüfung VOR jeder
  weiteren Empfehlung, unabhängig vom Primärergebnis (siehe oben) — kein
  automatischer Abbruch, aber auch keine automatische Fortsetzung ohne
  Prüfung.

## Bekannte Einschränkungen, bewusst akzeptiert

1. **Nur 600/900 Dateien tragen `root_q`.** Ein Nullbefund hier schließt
   Willemsen et al.s Hypothese nicht generell aus, nur in diesem
   Übergangs-Datenregime (ein reiner `root_q`-Vollkorpus existiert erst,
   wenn `v16`/`v17` aus dem Trainingsfenster fallen).
2. **`root_q` ist nur ego-perspektivisch für den ziehenden Spieler geloggt**
   (ein Wert je Schritt, kein `own`/`opp`-Paar wie bei `rtv`) — das passt
   direkt auf die Ego-Perspektive von `values`, erfordert aber Vertrauen,
   dass `net_mcts.rs`s Root-Completed-Q an dieser Stelle tatsächlich
   konsistent aus Sicht DES ZIEHENDEN Spielers berechnet wird (Rust-seitig
   verifiziert, Commit 2718b9a — außerhalb des Python-Scopes dieses Tasks).
3. **40 Epochen sind ein Kompromiss** (identisch zu `PREREG_corpus_dose.md`
   Einschränkung 4) — nicht pro Arm nachjustiert.
4. **Kein direkter Champion-Vergleich als Teil dieser Vorregistrierung.**
   Der Arena-Schritt (falls ausgelöst) vergleicht NUR den besten λ-Arm gegen
   die λ=1.0-Baseline — nicht gegen den amtierenden Champion. Ein
   tatsächlicher Champion-Kandidat wäre ein separater Folgeschritt.
5. **Zusammensetzung nur zum Stichtag 2026-08-02 geprüft** — Universum ist
   das eingefrorene `v16`/`v17`/`v18`-Fenster (900 Dateien), analog
   `PREREG_corpus_dose.md` Einschränkung 3. Spätere Generationen (`v19`, …)
   sind per Definition außerhalb, werden von `tools/train_lambda_sweep.py`
   nur gezählt/gemeldet, ändern nichts an der Ziehung.

## Ausführungsplan

1. `tools/train_lambda_sweep.py --build-only`: Split-Manifest +
   Hardlink-Sandbox `data_lambda_sweep/` (900 Dateien) aufbauen,
   Sample-Misch-Anteil exakt bestimmen (scannt alle `v18`-Dateien), Ergebnis
   in `evaluations/train_lambda_sweep_split.json` UND oben im Abschnitt
   "Datengrundlage" nachtragen.
2. 24 Läufe sequenziell (`tools/train_lambda_sweep.py`, Vorbild
   `train_corpus_dose.py`, aber EINE Sandbox + `--value-target-lambda` statt
   zwei Sandboxes je Korpusgröße).
3. `tools/offline_diagnosis.py --frozen --model lam10_s1_best ... lam03_s6_best
   --out evaluations/offline_diagnosis_lambda_target_frozen.json`.
4. Gepaarte Auswertung (`tools/train_lambda_sweep.py` schreibt sie direkt
   mit) — 3 Vergleiche (`lam07`/`lam05`/`lam03` je vs. `lam10`) auf
   `value_r2_rounds_1_4` (primär) + den 2 Orakel-Metriken (sekundär),
   Ergebnis-JSON nach `evaluations/train_lambda_sweep_result.json`.
5. Interpretationsregel oben automatisch angewendet (rein deskriptiv, der
   Mensch entscheidet trotzdem) — bestimmt, ob Schritt 6 überhaupt läuft.
6. NUR falls Schritt 5 einen Arm bestimmt: Arena-Gating (`paired_gating.py`,
   `--no-promote-winner`) manuell anstoßen, siehe Kommando oben.
7. Bericht an den Koordinator.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- Offline klar positiv (alle 3
Arme 6/6 Seeds ueber der Aufloesungsgrenze, lam07 +0,027, p=0,0061), aber
das Arena-Gating lam07 vs lam10 verlor: 43:57, SPRT nimmt H0 an (McNemar
p=0,25). Verdikt: Offline-Signal ohne Arena-Bestaetigung bleibt Beobachtung,
kein Rezeptwechsel; λ bleibt 1,0 auf diesem 900er-Fenster (43,8%
root_q-Mix). Belegstelle: archive/history.md, Abschnitt "Lambda-Sweep
ABGESCHLOSSEN: klares Offline-Signal, KEINE Arena-Bestaetigung
(2026-08-03)", Zeile ~6969-7002; evaluations/train_lambda_sweep_result.json.
