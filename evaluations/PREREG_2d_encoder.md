<!-- STATUS: ENTSCHIEDEN | Frage: Traegt der 2D-Conv-Encoder from-scratch mehr zur Netzstaerke bei als das flache MLP (Task #11, Phase 2)? | Beleg: Orakel 6/6 fuer 2D, aber Arena-Gating 416:384 (Wash, p=0,30); `archive/history.md` Z. ~6660-6741 -->

# Vorregistrierung: 2D-Encoder from-scratch vs. Flach-Netz from-scratch (Task #11, Phase 2)

**Angelegt 2026-07-30, VOR dem ersten der 12 Trainingsläufe.** Zweck: den
fairen Architektur-Vergleich (docs/design_2d_encoder.md Abschnitt 8) mit einer
im Voraus festgelegten Auswertungsregel fahren, statt hinterher eine Metrik zu
wählen, die zum gewünschten Ergebnis passt. Die Regeln unten dürfen nach
Sichtung der Ergebnisse NICHT mehr geändert werden (Präzedenzfall
`PREREG_ownership_gumbel.md`: ein nachträglicher Metrikwechsel — `val_combined`
statt der vorregistrierten Metrik — hätte beim `lr1e5`-Arm zur falschen
Entscheidung geführt).

---

## Frage

Trägt die 2D-Struktur (Conv-Zweig auf `state_to_planes`, siehe
`docs/design_2d_encoder.md`) MEHR zur Netzstärke bei als das bestehende
flache 708-Feature-MLP — **from scratch, identisches Rezept, identischer
Korpus**? Motivation (design_2d_encoder.md Abschnitt 1): der dokumentierte
blinde Fleck bei den 8 Wertungsplatten (Reihen-/Spalten-/Diagonalen-/Rand-/
Eckengeometrie), die über Generationen hinweg fast nie geschlossen werden.

## Arme

| Arm | Netz | Encoder |
|---|---|---|
| `fs_flat` | `MosaicNet` | `--encoder flat` (Bestandsarchitektur) |
| `fs_2d`   | `Mosaic2DNet` | `--encoder 2d` (Conv 76→48×2 + Flach-Zweig, siehe design_2d_encoder.md Abschnitt 5/10) |

Beide Arme **from scratch** (KEIN `--load`) — Präzedenzfall v14 (Memory
`project_v14_rebuild`): eine from-scratch-Distillation lag bei GLEICHER
Architektur ~220 Elo unter der Warm-Start-Linie, rein weil Warm-Start
Trainings-Epochen "spart". Ein 2D-Netz ohne Warm-Start-Äquivalent (es gibt
keinen 2D-Checkpoint zum Warmstarten) gegen den warmgestarteten Flach-Champion
zu testen würde die Architektur-Frage mit der Warm-Start-Frage konfundieren.
Der einzig faire Vergleich: beide from scratch, gleicher Korpus, gleiches
Rezept.

## Rezept (from-scratch-Standard)

Identisch für beide Arme bis auf `--encoder` und `--seed`:

```
python train.py --name <arm>_s<seed> --encoder <flat|2d> --seed <seed> \
    --epochs 40 --lr 4e-4 --lr-schedule cosine \
    --value-target-variant nortv \
    --no-plot --no-snapshot
```

- `--epochs 40`, `--lr 4e-4`, `--lr-schedule cosine`: from-scratch-Standard
  (KEIN Warm-Start-Feintuning-Rezept wie `--lr 5e-5`, das setzt einen bereits
  trainierten Trunk voraus).
- `--value-target-variant nortv`: Projektstandard seit 2026-07-28 (v13-Zyklus,
  Memory `project_v13_cycle_result`), unverändert für beide Arme.
- Kein `--train-file-limit`, kein `--exclude-round5`, kein `--ownership-weight`
  (Kopf bleibt aus, `OWNERSHIP_WEIGHT=0.0` aus config.py), keine
  `--points-dist-bins` — alles Bestandsdefault, für beide Arme identisch.
- `--val-frac` Standarddefault (0,1), Val-Split-Seed 20260707 (train.py-
  Konstante) — für BEIDE Arme identisch (Val-Split hängt nicht von `--seed`
  ab), macht die Val-Metriken zusätzlich vergleichbar (nicht der Punkt hier,
  aber ein Nebenprodukt).
- **Korpus**: alle 900 Dateien in `data/` (voller aktueller Stand,
  2026-07-30), für BEIDE Arme UND alle 12 Läufe identisch. Voraussetzung
  geprüft: kein `self_play.py`-Prozess läuft parallel (sonst würde `data/`
  während des Sweeps wachsen und die Läufe wären nicht mehr auf demselben
  Korpus — Präzedenzfall `tools/train_seed_sweep.py`-Dokumentation).

## Seeds

**6 gepaarte Seeds** (1..6) je Arm — Memory `project_training_seed_variance`:
Seed bewegt die Metrik 4-6× stärker als jeder einzelne Hyperparameter-Knopf,
ein Single-Run-A/B ist hier nicht interpretierbar. n=6 ist zugleich die
Mindestzahl, ab der der exakte Vorzeichentest überhaupt p<0,05 erreichen kann
(p = 2·(1/2)⁶ = 0,03125 bei einheitlicher Richtung).

12 Läufe gesamt: `fs_flat_s1..s6`, `fs_2d_s1..s6`.

## Entscheidungsmetriken (VORAB festgelegt)

### Primär (traegt die Struktur-Hypothese)

Die zwei einzigen gegen die Arena VALIDIERTEN Prädiktoren (Memory
`project_oracle_metrics_validated`, `tools/offline_diagnosis.py::ORACLE_KEYS`,
7/7 auf entschiedenen Gating-Paaren, Binomial p=0,0156):

- `prior_mass_on_oracle_top3`
- `kendall_tau_policy_vs_oracle_q`

Berechnet mit `tools/offline_diagnosis.py --frozen --model <12 Checkpoints>`
(Oracle-Referenz: v16_best, unverändert — die 2D-Checkpoints sind NICHT die
Oracle-Quelle, kein Selbstbezugs-Vorteil). Je Arm+Seed der **beste Checkpoint**
(`*_best.pth`, per `val_combined`-Auswahl innerhalb des Laufs — train.pys
Bestandslogik, unverändert).

Ausgewertet **gepaart** (Seed s in `fs_2d` gegen Seed s in `fs_flat`):

- **Gepaarter t-Test**, zweiseitig, α = 0,05 (Präzedenzfall
  `PREREG_ownership_gumbel.md`: t-Test ist bei gepaarten Differenzen
  trennschärfer als der Vorzeichentest; kein scipy im Projekt, t-Verteilung
  per Reihenentwicklung/Kontinuierter-Bruch-Näherung der regularisierten
  unvollständigen Betafunktion berechnet, kein neues Paket).
- **Exakter zweiseitiger Vorzeichentest** wird zusätzlich berichtet
  (dieselbe Formel wie `tools/train_seed_sweep.py::sign_test_p`), ist aber
  NICHT der Primärtest — nur ergänzende Information.

### Sekundär/entscheidend fürs Weitermachen: direktes Gating

Bester `fs_2d`-Checkpoint (nach Primärmetrik gewählt) vs. bester
`fs_flat`-Checkpoint in der ECHTEN Arena (400 gepaarte Partien, McNemar
exakt, Muster `tools/paired_arena_plate_ab.py`). **Läuft NICHT der
Ausführende dieser Vorregistrierung** (Rust-Wheel-Install nötig, siehe
Sicherheitsregel 1 im Auftrag) — läuft der Koordinator NACH Freigabe des
Wheels. Hier nur als Schritt dokumentiert, kein Teil der Läufe/Auswertung
dieses Dokuments.

## Abbruchregel (VORAB festgelegt)

**Ist `fs_2d` auf BEIDEN Orakel-Metriken gepaart schlechter (Ø-Differenz < 0,
Richtung egal ob signifikant)**, ist die Struktur-Hypothese für DIESES Design
widerlegt — kein Gating nötig, der Punkt ist geschlossen (analog zum
Ownership-Kopf-Präzedenzfall: eine Metrik, die den falschen Weg zeigt, muss
nicht durch die teure Arena bestätigt werden, um sie zu verwerfen).

**Ist `fs_2d` auf MINDESTENS EINER der beiden Metriken gepaart besser** (egal
ob p<0,05), lohnt sich das Gating — unabhängig vom Signifikanzergebnis des
t-Tests (ein Trend bei n=6 ist noch kein Beweis, aber auch keine Widerlegung;
das Gating selbst ist der eigentliche Beleg für/gegen Spielstärke).

**Ist `fs_2d` auf beiden Metriken gepaart besser UND p<0,05 auf mindestens
einer**, ist das ein starker Befund für die Struktur-Hypothese — Gating hat
dann hohe Priorität.

## Bekannte Einschränkungen, bewusst akzeptiert

1. **40 Epochen sind ein Kompromiss**: das from-scratch-Standardrezept ist
   nicht notwendigerweise für BEIDE Architekturen gleich gut kalibriert (die
   2D-Architektur hat mehr Parameter im Conv-Zweig, könnte andere
   Epochenzahl/LR brauchen). Wird NICHT nachträglich pro Arm angepasst (das
   würde die Fairness aufheben) — ein Ergebnis "2D braucht mehr Epochen"
   wäre dann ein Folge-Experiment, keine Korrektur dieses Laufs.
2. **Checkpoint-Auswahl** (`val_combined = p_loss + VALUE_WEIGHT*v_loss +
   POINTS_WEIGHT*points_loss`) ist für beide Architekturen dieselbe Formel,
   aber nicht direkt validiert, dass sie für `Mosaic2DNet` genauso gut den
   arena-starken Checkpoint trifft wie für `MosaicNet`.
3. **Analyse der Netzauslastung** (`analyze_capacity`) existiert nur für
   `MosaicNet` — `Mosaic2DNet` überspringt diesen Diagnoseblock (kein
   Blocker, reine Zusatzdiagnose ohne Einfluss auf Training/Checkpoint-Wahl).
4. Die Rundenzuordnung `value_r2_rounds_1_4` (klassische Metrik) wird
   MITBERECHNET und mitberichtet, ist aber laut Memory
   `project_offline_metric_resolution_limit` erst oberhalb ~0,015 Abstand
   auflösend (3/3 groß, 0/3 klein) — dient hier nur als Zusatzinformation,
   NICHT als Entscheidungsmetrik.

## Ausführungsplan

1. 12 Läufe sequenziell (kein `self_play.py` parallel, siehe oben) —
   `tools/train_2d_vs_flat_fs.py` (neu, Vorbild `tools/train_seed_sweep.py`,
   aber OHNE `--load`, MIT `--encoder`-Durchreichung). Reihenfolge: je Seed
   ein Paar (`fs_flat_s<n>` dann `fs_2d_s<n>`), damit ein Zwischenstand nach
   jedem fertigen Paar sinnvoll ist. `--no-snapshot` (Ablationslauf, kein
   Champion) `--no-plot` (kein Display nötig).
2. Nach allen 12 Läufen: `tools/offline_diagnosis.py --frozen --model
   fs_flat_s1_best fs_2d_s1_best ... --out
   evaluations/offline_diagnosis_2d_vs_flat_fs_frozen.json` (Orakel-Metriken
   AKTIV, `--no-oracle` NICHT gesetzt).
3. Gepaarte Auswertung (`tools/train_2d_vs_flat_fs.py` schreibt sie direkt
   mit, kein separates Skript nötig) — Tabelle je Seed + Zusammenfassung
   (Ø-Differenz, t-Test, Vorzeichentest) für beide Orakel-Metriken.
4. Bericht an den Koordinator (Stopp-Punkt M4, siehe Auftrag) — kein Gating,
   kein Wheel-Install, keine Arena durch den Ausführenden dieser
   Vorregistrierung.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- Beide Orakel-Metriken 6/6
signifikant fuer `fs_2d` (`prior_mass_on_oracle_top3` +0,0100, p=0,0019;
`kendall_tau` +0,0149, p=0,0046). Das anschliessende Arena-Gating
(`fs_2d_s2_best` vs `fs_flat_s3_best`, 400 Partien) ergab jedoch 416:384,
McNemar p=0,30 -- kein nachweisbarer Staerkeunterschied (Wash). Konsequenz:
`fs_2d_s2_best` wurde als `alphazero_v18_2d` designiert (2D-Warm-Start-
Anker fuer v19); Orakel-Metriken gelten seither nur 0/1 als
ARCHITEKTUR-Staerke-Praediktor (bleiben 7/7 fuer Generationenvergleiche).
Belegstelle: archive/history.md, Zeile ~6660-6741 ("PREREG-Ergebnis" /
"Arena-Gating" / "ENTSCHEIDUNGEN (Nutzer)");
evaluations/train_2d_vs_flat_fs_result.json.
