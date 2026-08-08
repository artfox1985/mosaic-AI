# UEBERGABE: v21-Spirale (Self-Play -> Training -> Gating -> Auswertung)

**Stand 2026-08-08 vormittags.** Dieses Dokument ist die vollstaendige
Arbeitsanweisung fuer den naechsten Koordinator (Opus-Agent) bzw. den
Nutzer. Kontext: evaluations/STATUS.md (Regeln!), PREREG_v21_fenster.md,
PREREG_t35b_ranking.md, archive/history.md, Projekt-Memory.
ALLE Entscheidungen sind gefallen: Generator = `v20_2d_opp_brierbest`
(Champion), Fenster = 29.450 Partien (fix), τ=1 (M3-H0), Tiling-Kriterium
Bestand (#37-H0), `--endgame-head` = neues Standard-Rezept.

## 0. LAEUFT NOCH / ZUERST ABSCHLIESSEN

`t35b_s2` (Ranking-Loss-Arm, GPU) laeuft. Bei Abschluss:
```bash
python tools/offline_diagnose.py --frozen --model t35b_s2_brierbest v20_2d_opp_brierbest
```
ACHTUNG: offline_diagnose nutzt frozen_v1+alte Orakel-Labels; fuer die
PREREG-gemaesse Vorpruefung auf frozen_v2 dessen Doku pruefen (Orakel-
Pfade ggf. per CLI/Konstante auf frozen_eval_set_v2.pkl +
frozen_v2_oracle_labels.json zeigen -- kleiner Patch, Muster --set in
build_frozen_oracle_labels). Entscheidungsregeln: PREREG_t35b_ranking.md
(beide Orakel-Metriken schlechter -> KEIN Gating; sonst Gating wie in
Abschnitt 3, Modell t35b_s2_brierbest, no-promote; H1 -> Rezept-Kandidat
neben --endgame-head).

**Wheel-Sammelinstall** (sobald WEDER Server noch Training laeuft;
danach kein PYTHONPATH mehr noetig, enthaelt Chip-Logging-Fix + alle
inerten Knoepfe):
```bash
python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
```
Danach Paritaets-Probe (muss `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` liefern):
```bash
python "C:/Users/Patrick/AppData/Local/Temp/claude/D--OneDrive-Documents-Projekte-mosaic-AI/c9453d70-4f31-432e-91b3-b3e84ac5f0d4/scratchpad/paritaet_probe.py"
```
(Falls Scratch weg: Probe ist trivial rekonstruierbar -- 3 Frozen-Set-
Drafting-Zustaende R1-3, net_search_state_json @150+400, SHA256; neuer
Referenz-Hash dann einmalig neu setzen und dokumentieren.)

**v16/v17-Backup-Freigabe**: NACH dem t35b_s2-Cache (gebaut) duerfen
`data/selfplay_v16_*` + `selfplay_v17_*` ins Backup -- ABER erst
pruefen, dass kein weiterer v20-Fenster-Cache-Neubau mehr ansteht
(jedes neue Schema/Fenster-Pinning-Rebuild braeuchte sie). Messset ist
unabhaengig (altmess_90files/ Snapshot). Nutzer macht das Verschieben.

## 1. SELF-PLAYS (CPU, Reihenfolge egal, NUR mit Nutzer-Go)

Schwarm-Rest (2.090 von 8.000 existieren bereits in data/):
```bash
python -u self_play.py --mode network --model models/alphazero_v20_2d_opp_brierbest.onnx --games 5910 --sims 150 --version v20wdlsw --value-only --threads 11 --chunk 10 --seed 50260808
```
Sockel (τ=1, KEIN --tau-argmax-from-move; Tiling-Default):
```bash
python -u self_play.py --mode network --model models/alphazero_v20_2d_opp_brierbest.onnx --games 4000 --sims 600 --version v20wdl --threads 11 --chunk 10 --seed 60260808
```
Invarianten-Checks nach den ersten Dateien (Muster dieser Session):
Schwarm -> `policy_target_valid` auf Mehrfach-Aktions-Zuegen == False;
beide -> Manifest-Zusammensetzung, Chips ~4,9/Partie Groessenordnung.

## 2. v21-MANIFEST + FENSTER-PIN (einmalig, VOR dem Training)

```bash
python - <<'PY'
import glob, json, os, random, re
rng = random.Random(20260815)  # v21-Traeger-Seed, hiermit festgelegt
v19wdl = sorted(os.path.basename(f) for f in glob.glob("data/selfplay_v19wdl_*.pkl")); assert len(v19wdl)==400
v18    = sorted(os.path.basename(f) for f in glob.glob("data/selfplay_v18_*.pkl"));    assert len(v18)==600
tr_v19 = sorted(rng.sample(v19wdl, 135))          # 1.350 Traeger-Partien
rest18 = v18[:]
tr_v18 = sorted(rng.sample(rest18, 45))           # 450 Traeger-Partien
uebrig = [f for f in rest18 if f not in tr_v18]
maskiert_v18 = sorted(rng.sample(uebrig, 500))    # 5.000 maskierte Partien
raus_v18 = sorted(set(uebrig) - set(maskiert_v18)); assert len(raus_v18)==55
json.dump({"seed": 20260815, "policy_carrier_files": tr_v19 + tr_v18,
           "carrier_prefixes": ["selfplay_v20wdl_"],
           "hinweis": "v21: Traeger = 135 v19wdl + 45 v18 (gelistet) + ALLE selfplay_v20wdl_*-Sockeldateien (carrier_prefixes, Unterstrich-Grenze -> selfplay_v20wdlsw_* matcht NICHT); 55 v18-Dateien komplett raus (raus_v18)",
           "raus_v18": raus_v18},
          open("data/policy_carrier_manifest_v21.json","w",encoding="utf-8"), indent=1)
alt = "|".join(re.escape(b) for b in raus_v18)
open("evaluations/v21_exclude_regex.txt","w").write(f"selfplay_v16_|selfplay_v17_|selfplay_v19wdlann_|(?:{alt})")
print("Manifest + Exclude-Regex geschrieben")
PY
```
**Geltende Traeger-Regel (Fix 2026-08-08, `_is_policy_carrier` in
neural_net.py)**: das v21-Manifest setzt das additive Feld
`carrier_prefixes: ["selfplay_v20wdl_"]`. Ist dieses Feld VORHANDEN,
gilt NUR NOCH `basename in policy_carrier_files ODER
basename.startswith(carrier_prefixes)` -- der alte
`bootstrap_native`-Kurzschluss (der frueher JEDE `v19wdl*`/`v20wdl*`-
Datei automatisch zum Traeger gemacht haette, egal ob gelistet) greift
dann NICHT mehr. Damit tragen genau: die 135 gelisteten `v19wdl`- +
45 gelisteten `v18`-Dateien + ALLE `selfplay_v20wdl_*`-Sockeldateien
(Praefix-Match, Unterstrich ist Teil des Praefixes -> `v20wdlsw_*`
matcht nicht). Fehlt `carrier_prefixes` im Manifest (v20-Altbestand),
bleibt die alte Logik inkl. Kurzschluss unveraendert (Rueckwaerts-
Kompatibilitaet, bit-identische v20-Caches). Am ersten Cache-Log
("Policy-Traeger"-Zaehlung bzw. pol_w-Statistik) verifizieren, dass
GENAU 5.800 Partien Policy tragen (1.350 + 450 + 4.000).

## 3. v21-TRAINING + GATING

```bash
MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v21.json \
MOSAIC_DATA_EXCLUDE="$(cat evaluations/v21_exclude_regex.txt)" \
python -u train.py --name v21_2d --load v20_2d_opp_brierbest --epochs 100 --lr 5e-5 --lr-schedule cosine --seed 2 --value-weight 0.2 --value-target-variant nortv --encoder 2d --opp-points-head --value-head wdl --endgame-head
```
(Windows/PowerShell: Env-Vars entsprechend setzen. --ranking-loss-weight
NUR ergaenzen, falls t35b_s2 sein Gating GEWONNEN hat.)
Erwartung: ~4,8M Zustaende, Cache gepackt ~13 GB, Peak <20 GB, Bau ~3h,
brierbest um E4-6. Banner pruefen: 🔒-Zeile VOR dem Split, "Lade Daten
aus N Dateien" mit N == 0,9*2945 ± Rundung.

Gating (Fruehstopp-Regel: kein Entscheid <150 Paare ohne
Frisch-Seed-Replikation!):
```bash
python -u tools/paired_gating.py --model-a models/alphazero_v21_2d_brierbest.onnx --model-b models/alphazero_v20_2d_opp_brierbest.onnx --sims 400 --block-size 5 --max-pairs 200 --no-promote-winner
```
Bei H1: `python tools/set_champion.py v21_2d_brierbest` +
Elo-Eintrag MIT KADER-NAMEN (nicht Dateinamen!):
```bash
python tools/elo_tracker.py add --player-a v21_2d_brierbest --sims-a 400 --player-b v20_2d_opp_brierbest --sims-b 400 --wins-a <A> --wins-b <B> --n <N> --comment "Champion-Gating v21-Zyklus: ..."
```
Bei H0: KEIN Nachschub-Ventil (stehende Regel) -- dokumentieren,
Ursachenarbeit mit dem Nutzer.

## 4. AUSWERTUNGS-PAKET (nach dem Gating, Reihenfolge egal)

```bash
# Saettigungs-/Aera-Punkt (Snapshot-Messset, split-unabhaengig):
python -u tools/t36_curve_eval.py --models v21_2d_brierbest v21_2d --snapshot-dir altmess_90files --validate-games-json evaluations/t36_curve_eval.json --out evaluations/t36_curve_eval_v21.json
# Platt-Kalibrierung (Referenzen: v19 1,9269 / v20 0,930):
python -u tools/platt_fit.py --models models/alphazero_v21_2d_brierbest.pth --out evaluations/platt_fit_v21.json
# R5-Plattensteigung (Verlauf 0,086/0,273/0,349/0,457; Seed-Skala ~0,05):
python -u tools/r5_value_calibration.py --models models/alphazero_v21_2d_brierbest.pth --model-path-for-api models/alphazero_v19_2d_best.onnx --out evaluations/r5_value_calibration_v21.json
# Policy-Wacht (Orakel-Metriken; fuer frozen_v2 die Pfade anpassen, s. Abschnitt 0):
python -u tools/offline_diagnose.py --frozen --model v21_2d_brierbest v20_2d_opp_brierbest
```
**#29-Buchfuehrung**: je Gating-Paar Brier(Alt-Set)+R5-Steigung
notieren; Verdikt erst ab >=6 arena-ENTSCHIEDENEN Paaren (Stand: ~3).
Struktur-Watchlist: bei ~10+ frischen Nutzer-Partien vs neuen Champion
Log-Analyse wie evaluations/watchlist_v20_zwischenlese.md (Agent,
--no-oracle-Stil; Chip-Zaehlung ist nach dem Logging-Fix jetzt direkt).


## 5b. NACH-v21-QUEUE (Nutzer-Go 2026-08-08, Reihenfolge fix)

Beides erst NACH v21-Training + Gating + Auswertungs-Paket; beides
CPU-Arena. Knoepfe werden vorab gebaut (Default aus, Paritaets-Hash).

1. **E3b -- Denial-Tie-Break mit Unsicherheits-Fenster**
   (`PREREG_denial_tiebreak.md`, Abschnitt E3b). ZUERST Stufe 1:
   Feuerrate messen (`MOSAIC_DENIAL_UNCERT_Z=1.0`,
   `MOSAIC_DENIAL_MIN_VISIT_FRAC=0.5`, 200 Partien @400, Debug-Zaehler
   fired/total). **Feuerrate < 5% -> Punkt OHNE Arena geschlossen.**
   Nur darueber: Stufe 2, zwei Arme a 400 (z=0 vs z=1) via
   paired_arena_env_ab, Siegquoten-Wache = Gate.
2. **ISMCTS-k -- Mehrfach-Determinisierung**
   (`PREREG_ismcts_determinisierungen.md`): drei Arme a 400 Spiele
   (`MOSAIC_NUM_DETERMINIZATIONS` = 1/2/4), **bei 600 Netz-Sims**
   (Nutzer-Hinweis: Sockel-Regime; dadurch bleibt k=2 bei m=16 =
   confound-frei und k=4 landet auf dem als neutral gemessenen m=9),
   Basis-Seed 20260820. Rechen-neutral (Sims-Split ueber die Welten).
   Default-Wechsel NUR mit Signifikanz + Frisch-Seed-Replikation.

## 5a. OFFENES GATING AUS DER v20-AERA (zuerst, nicht vergessen!)

**λ-Arm `lam07_wdl2_s2` ist trainiert und GUELTIG, sein Gating fehlt
noch.** Er haengt NICHT an v21 (trainiert auf dem v20-Fenster, 1890
Dateien) -- idealer Slot ist das **v21-TRAININGSFENSTER**: dort ist die
GPU belegt und die CPU frei, also kollidiert er weder mit dem
Sockel-Self-Play noch mit der Nach-v21-Arena-Queue.

```bash
python -u tools/paired_gating.py --model-a models/alphazero_lam07_wdl2_s2_brierbest.onnx     --model-b models/alphazero_v20_2d_opp_brierbest.onnx --sims 400     --block-size 5 --max-pairs 200 --no-promote-winner     --out evaluations/paired_gating_lam07wdl2_vs_champion.json
```
Entscheidungsregeln: `PREREG_lambda_wdl_arm.md` (Standard-SPRT,
Fruehstopp-Regel; H1 -> λ=0,7 wird Rezept-Kandidat neben
`--endgame-head`, Promotion nach Nutzer-Entscheid; H0 -> λ in der
WDL-Aera GESCHLOSSEN). Offline-Stand (deskriptiv, KEINE Entscheidung):
Brier 0,1957 vs 0,1950 (Champion) = Paritaet, Alt-Set 0,18937 vs
0,18749, **Platt-B 0,9966 vs 0,930 = fast perfekt kalibriert** (der
einzige echte Unterschied). Val-R² 0,441 vs 0,374 ist ARTEFAKT (gegen
das λ-gemischte, glattere Ziel gemessen) und zaehlt nicht.

## 5c. NACH-v21-QUEUE, VOLLSTAENDIG (Reihenfolge + Bahnen)

Vorregistrierung aller vier Review-Tasks: `EXTERNES_REVIEW_2026-08-08.md`
(Abschnitt "VORREGISTRIERUNG A-D"), E3b/ISMCTS-k siehe 5b.

| # | Task | Bahn | Kosten |
|---|---|---|---|
| 1 | **B** Zerlegungs-Diagnose (Slot/Rotation flach vs zweistufig) | CPU leicht | ~1h |
| 2 | **A** Floor-Shaping W=0 vs 0,3 | Arena 2x400 | ~1h |
| 3 | **E3b Stufe 1** Feuerrate (Abbruch <5%) | CPU leicht | ~30min |
| 4 | **ISMCTS-k** k=1/2/4 @600 Sims | Arena 3x400 | ~1,5h |
| 5 | **C** c_visit 25/50/100 @600 Sims | Arena 3x400 | ~1,5h |
| 6 | **E3b Stufe 2** (nur bei Feuerrate >=5%) | Arena 2x400 | ~1h |
| 7 | **D** POINTS_WEIGHT 0,25/0,5/1,0 | GPU, parallel | ~10h |

Wichtig: 7 laeuft auf der GPU PARALLEL zu 1-6 (Arena ist CPU) -- aber
Fenster pinnen und die Brier-Schwelle 0,0015 fuers Gating beachten.

## 5. STEHENDE REGELN (Kurzform -- Langform in STATUS.md)

1. **Fenster-Pinning**: JEDES Training mit MOSAIC_DATA_EXCLUDE pinnen,
   solange irgendeine Generierung schreibt; Verifikation = 🔒-Zeile
   VOR dem Split + "Lade HDF5-Cache" bei erwartetem Hit.
2. **Generator-Naming**: Laeufe/Dateien nach dem GENERATOR benennen;
   Ziel-Generationen existieren erst mit trainiertem Modell.
3. **Statistik**: Scores nur block-basiert; <8pp vs Heuristik = Seed-
   Rauschen; SPRT-Fruehstopp <150 Paare braucht Replikation;
   Aufloesungsgrenze: Offline-Gaps <0,015 sagen NICHTS (Regel 0/4).
4. **Aera-Grenzen**: Alt-Aera-Befunde (tanh-Kopf) nie unreflektiert
   als Argument in der WDL-Aera verwenden -- gilt auch fuer eigene
   Begruendungen.
5. **Prozess-Disziplin**: Hintergrund-Starts NUR harness-getrackt als
   einzelner Befehl (nie `cmd &` in Ketten); Agents duerfen NIE
   loeschen/ueberschreiben ausserhalb ihres Scratch-Verzeichnisses;
   Koordinator plant/gatet, Sonnet-Agents implementieren.
6. **brierbest-Checkpoint-Politik** (arena-re-validiert); Elo nur mit
   Kader-Namen; kein Nachschub-Ventil; Backup-Korpora nie wieder;
   Heuristik-Anker-Paket nicht anfassen; alle Aggressions-/Denial-/
   τ-/Tiling-Knoepfe bleiben auf Default (alles gemessen, alles H0).

## 6. OFFENE NUTZER-ENTSCHEIDE

- Go fuer die Self-Plays (Abschnitt 1) -- ausdruecklich zurueckgestellt.
- λ-Arm (Hypothesen-Niveau, Queue-Ende) starten oder streichen.
- v16/v17-Verschiebe-Zeitpunkt (Abschnitt 0).
- E15-vs-brierbest bleibt Kuriosum (systematisch auf Alt-Set, arena-
  irrelevant) -- keine Aktion geplant.
