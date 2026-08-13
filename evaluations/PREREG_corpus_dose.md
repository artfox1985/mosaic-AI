# Vorregistrierung: Korpus-Dosis-Wirkungs-Messung (Vorstudie zu Task #14)

**Angelegt 2026-08-01, VOR dem ersten der 12 Trainingsläufe.** Zweck: klären,
ob MEHR Self-Play-Spiele in der aktuellen Engine-Ära (v15/v16/v17, seit dem
Regelwerk-Audit 82e8a88) die Netzqualität messbar heben — bevor Zeit in
Task #14 (Playout-Cap-Randomisierung, STATUS.md "Test B", 2026-07-28)
investiert wird. Die Regeln unten dürfen nach Sichtung der Ergebnisse NICHT
mehr geändert werden (Präzedenzfall `PREREG_ownership_gumbel.md`: ein
nachträglicher Metrikwechsel hätte beim `lr1e5`-Arm zur falschen Entscheidung
geführt).

---

## Frage

Hilft schlicht MEHR Korpus (bei unveränderter Suchtiefe/Engine-Ära) der
Netzqualität überhaupt — unabhängig davon, WIE die zusätzlichen Spiele
erzeugt wurden? Motivation: Task #14 wettet darauf, dass mehr, aber
schwächere Trajektorien (Playout-Capping, weniger Sims/Zug) den Verlust an
Such-Qualität pro Spiel durch schiere Menge wettmachen. Diese Vorstudie
prüft nur die halbe Frage — "hilft Menge überhaupt, bei GLEICHER
Suchtiefe/GLEICHEM Rechenaufwand pro Zug" — nicht den eigentlichen
Tradeoff aus Task #14 (siehe Abschnitt "Einschränkung" unten).

## Arme

| Arm | Korpus | Dateien |
|---|---|---|
| `voll` | kompletter aktueller Korpus (2026-08-01) | 900 (600 `v17` + 200 `v16` + 100 `v15`) |
| `halb` | stratifizierte Hälfte, Zusammensetzungsverhältnis erhalten | 450 (300 `v17` + 100 `v16` + 50 `v15`) |

Beide Arme **from scratch** (KEIN `--load`) — Präzedenzfall v14 (Memory
`project_v14_rebuild`) und `PREREG_2d_encoder.md`: ein warmgestarteter Arm
gegen einen from-scratch-Arm würde die Korpusgrößen-Frage mit der
Warm-Start-Frage konfundieren. Beide Arme from scratch, gleiches Rezept,
gleiche Netzarchitektur (flacher Encoder) — einziger Unterschied ist die
Korpusgröße.

## Stratifizierte Ziehung des Halb-Arms

`halb` ist **keine** einfache Zufallsziehung aus allen 900 Dateien, sondern
zieht **je Versions-Präfix (`v15`/`v16`/`v17`) separat genau die Hälfte**
(300/100/50 von 600/200/100) — das Zusammensetzungsverhältnis (6:2:1) bleibt
dadurch exakt erhalten, statt nur im Erwartungswert einer uniformen Ziehung
zu gelten. Fester Seed `20260801` (`tools/train_corpus_dose.py::STRATIFY_SEED`),
unabhängig von train.py's eigenen Seeds (Val-Split-Seed `20260707`,
Task-#69-Subsample-Seed `20260708`). Die Ziehung wird einmalig berechnet und
als Manifest persistiert (`evaluations/train_corpus_dose_split.json`), damit
ein Wiederaufnahme-Lauf nach Unterbrechung exakt denselben Split verwendet.

Beide Halb-Arm-Seeds (`halb_s1`..`halb_s6`) trainieren auf **demselben**
450-Dateien-Korpus — nur die Trainings-Randomisierung (Gewichts-Init,
Batch-Shuffle über `--seed`) unterscheidet die 6 Seeds, exakt wie beim
`voll`-Arm und wie im `fs_flat`/`fs_2d`-Vorbild.

## Technische Umsetzung (Datei-Teilmenge ohne Kopien)

**Geprüft:** `train.py` hat bereits ein Datenmengen-Flag,
`--train-file-limit <N>` (Task #69, "Daten-Skalierungs-Ablation") — es kappt
`train_files` (den Nach-Val-Split-Pool) auf `N` Dateien per uniformer
Zufallsauswahl mit einem **fest verdrahteten** Seed (`20260708`), OHNE
Stratifizierung nach Versions-Präfix. Das reicht für diese Vorstudie NICHT:
das Zusammensetzungsverhältnis soll exakt erhalten bleiben (siehe oben), und
der Seed ist nicht durchreichbar. Eine echte Datei-LISTEN-Option existiert
in `train.py` nicht.

**Lösung — additiver Env-Var-Override in `config.py`, `train.py` bleibt
unangetastet:**

```python
DATA_DIR = Path(os.environ.get("MOSAIC_DATA_DIR", str(BASE_DIR / "data")))
```

(Default unverändert, byte-identisches Verhalten, wenn die Env-Var nicht
gesetzt ist — betrifft `train.py`, `self_play.py`, `server.py` gleichermaßen,
aber nur, wenn `MOSAIC_DATA_DIR` explizit gesetzt wird.)

`tools/train_corpus_dose.py` baut für **BEIDE** Arme einen **separaten,
eingefrorenen** Ordner mit **Hardlinks** (`os.link`, gleiches NTFS-Volume,
kein zusätzlicher Speicherplatz, kein Kopieraufwand): `data_dose_voll/` (alle
900 Manifest-Dateien) und `data_dose_halb/` (die 450 gezogenen Dateien), und
setzt `MOSAIC_DATA_DIR` für die `train.py`-Subprozesse beider Arme auf den
jeweiligen Sandbox-Ordner.

**Nachbesserung 2026-08-01 (Koordinator-Review):** ursprünglich lief der
`voll`-Arm ohne Override direkt gegen den echten `data/`-Ordner. Das kollidiert
mit parallel laufendem Self-Play (z.B. v19-Self-Play schreibt neue Dateien
nach `data/`) auf zwei Arten: (a) der Korpus wäre zwischen den 6
`voll`-Seeds nicht mehr identisch, sobald neue Dateien während des Sweeps
dazukommen — die Messung wäre ungültig; (b) die alte Sicherheitsprüfung
brach hart ab, sobald ein `self_play.py`-Prozess lief, was den Sweep in der
Praxis blockiert hätte. Seit der Nachbesserung sieht `train.py` bei
**keinem** der beiden Arme den echten `data/`-Ordner direkt — beide laufen
gegen ihre eigene eingefrorene Sandbox, `data/` wird nur EINMALIG gelesen,
um die Sandboxes aufzubauen. Die Sicherheitsprüfung wurde entsprechend
entschärft: kein Abbruch mehr bei laufendem Self-Play, stattdessen wird vor
jedem Sweep-Start geprüft, dass (1) alle 900 Manifest-Dateien noch real in
`data/` existieren und (2) beide Sandboxes exakt zum Manifest passen — Anzahl
UND Datei-Identität je Datei über `os.stat().st_ino` (NTFS-Hardlinks teilen
sich den physischen Datei-Index; ein Treffer beweist, dass die Sandbox
wirklich denselben Byte-Inhalt referenziert, nicht nur zufällig gleich
benannt ist). Nach dem gesamten Sweep (alle 12 Läufe) werden beide Sandboxes
inklusive ihrer je eigenen HDF5-Caches (`train.py`/`MosaicDataset` legt den
Cache in das Verzeichnis, auf das `MOSAIC_DATA_DIR` zeigt) wieder entfernt —
der echte `data/`-Ordner bleibt dabei zu jedem Zeitpunkt unangetastet.

**Warum nicht Kopien / warum nicht `data/` selbst verschieben:** `data/`
liegt unter OneDrive-Synchronisation (Memory
`project_onedrive_file_disappearance`: getrackte Dateien sind schon einmal
spurlos verschwunden, `data/` ist gitignored und damit unnötig verwundbar).
Hardlinks in einem NEUEN, separaten Ordner sind rein additiv — die 900
echten Dateien in `data/` werden zu keinem Zeitpunkt verschoben, umbenannt
oder gelöscht, nur zusätzliche Verzeichniseinträge (NTFS-Referenzzähler)
angelegt. Physische Kopien der 900 Dateien wären zwar laut Auftrag ebenfalls
akzeptabel gewesen ("wenn nötig"), sind hier aber unnötig, da die
Hardlink-Lösung sauber funktioniert.

## Rezept (from-scratch-Standard, identisch zum fs-Vorbild)

Identisch für beide Arme bis auf Korpusgröße (`MOSAIC_DATA_DIR`) und
`--seed`:

```
python train.py --name <arm>_s<seed> --seed <seed> \
    --epochs 40 --lr 4e-4 --lr-schedule cosine \
    --value-target-variant nortv \
    --no-plot --no-snapshot
```

(flacher Encoder, `--encoder` NICHT gesetzt, Bestandsdefault — billig, keine
2D-Frage hier.)

- `--epochs 40`, `--lr 4e-4`, `--lr-schedule cosine`: from-scratch-Standard,
  identisch zu `PREREG_2d_encoder.md`.
- `--value-target-variant nortv`: Projektstandard seit 2026-07-28 (v13-Zyklus,
  Memory `project_v13_cycle_result`), unverändert für beide Arme.
- Kein `--train-file-limit` (die Korpusgröße wird stattdessen über
  `MOSAIC_DATA_DIR` gesteuert, siehe oben — die beiden Mechanismen wären
  sonst verwirrend überlagert), kein `--exclude-round5`, kein
  `--ownership-weight`, keine `--points-dist-bins` — alles Bestandsdefault,
  für beide Arme identisch.
- `--val-frac` Standarddefault (0,1), Val-Split-Seed `20260707`
  (train.py-Konstante) — für BEIDE Arme identisch (der Val-Split wird
  INNERHALB des jeweils sichtbaren Korpus gezogen: 10% von 900 bzw. 10% von
  450 — dadurch ist auch der Val-Split zwischen den Armen NICHT identisch,
  das ist eine bewusst akzeptierte Einschränkung, siehe unten).
- **Kein Blocker mehr bei laufendem Self-Play** (Nachbesserung 2026-08-01,
  siehe Abschnitt "Technische Umsetzung"): beide Arme laufen gegen
  eingefrorene Hardlink-Sandboxes, `data/`-Wachstum während des Sweeps ist
  unschädlich. Geprüft wird stattdessen, dass die 900 Manifest-Dateien noch
  real existieren und beide Sandboxes konsistent zum Manifest sind.

## Seeds

**6 gepaarte Seeds** (1..6) je Arm — Memory `project_training_seed_variance`:
Seed bewegt die Metrik 4-6× stärker als jeder einzelne Hyperparameter-Knopf,
ein Single-Run-A/B ist nicht interpretierbar. n=6 ist zugleich die
Mindestzahl, ab der der exakte Vorzeichentest überhaupt p<0,05 erreichen
kann (p = 2·(1/2)⁶ = 0,03125 bei einheitlicher Richtung).

12 Läufe gesamt: `voll_s1..s6`, `halb_s1..s6`.

## Entscheidungsmetriken (VORAB festgelegt)

### Primär (trägt die Dosis-Wirkungs-Hypothese)

Die zwei einzigen gegen die Arena VALIDIERTEN Prädiktoren (Memory
`project_oracle_metrics_validated`, `tools/offline_diagnosis.py::ORACLE_KEYS`,
7/7 auf entschiedenen Gating-Paaren, Binomial p=0,0156):

- `prior_mass_on_oracle_top3`
- `kendall_tau_policy_vs_oracle_q`

Berechnet mit `tools/offline_diagnosis.py --frozen --model <12 Checkpoints>`
(Oracle-Referenz: `v16_best`, unverändert — keiner der 12 Checkpoints ist die
Oracle-Quelle, kein Selbstbezugs-Vorteil). Je Arm+Seed der **beste
Checkpoint** (`*_best.pth`, per `val_combined`-Auswahl innerhalb des Laufs —
train.pys Bestandslogik, unverändert; fällt ein Lauf ohne Plateau bis zum
Epochen-Deckel durch, existiert nur `alphazero_<name>.pth` ohne separates
`_best.pth` — `tools/train_corpus_dose.py` behandelt das identisch zum
`fs_flat`/`fs_2d`-Vorbild).

Ausgewertet **gepaart** (Seed s in `halb` gegen Seed s in `voll`):

- **Gepaarter t-Test**, zweiseitig, α = 0,05 (Präzedenzfall
  `PREREG_ownership_gumbel.md`/`PREREG_2d_encoder.md`: t-Test ist bei
  gepaarten Differenzen trennschärfer als der Vorzeichentest; kein scipy im
  Projekt, t-Verteilung per Kettenbruch-Näherung der regularisierten
  unvollständigen Betafunktion berechnet, identischer Code wie
  `tools/train_2d_vs_flat_fs.py`).
- **Exakter zweiseitiger Vorzeichentest** wird zusätzlich berichtet
  (dieselbe Formel wie `tools/train_seed_sweep.py::sign_test_p`), ist aber
  NICHT der Primärtest — nur ergänzende Information.

### Sekundär/informativ

`value_r2_rounds_1_4` (klassische Metrik) wird MITBERECHNET und
mitberichtet, ist aber laut Memory `project_offline_metric_resolution_limit`
erst oberhalb ~0,015 Abstand auflösend (3/3 groß, 0/3 klein) — dient hier nur
als Zusatzinformation, NICHT als Entscheidungsmetrik.

## Interpretationsregeln (VORAB festgelegt) — was folgt für Task #14

**Ist `voll` auf BEIDEN Orakel-Metriken gepaart schlechter oder gleich**
(Ø-Differenz ≤ 0, unabhängig von Signifikanz): schiere Korpusmenge trägt in
der aktuellen Engine-Ära NICHTS (mehr) zur Netzqualität bei, der Korpus ist
in Bezug auf Menge bereits gesättigt. **Für Task #14**: der zentrale Wetteinsatz
von Playout-Capping — mehr, aber schwächere Trajektorien schlagen durch
schiere Menge — wird unwahrscheinlicher. Task #14 (Test B2, echtes neues
Self-Play mit reduzierten Sims) sollte NICHT ohne weitere Prüfung
priorisiert werden; die erwartete Auszahlung sinkt.

**Ist `voll` auf MINDESTENS EINER der beiden Metriken gepaart besser** (egal
ob p<0,05): ein Trend, dass Menge etwas beiträgt — spricht tendenziell FÜR
Task #14s Grundannahme (mehr Spiele helfen), sagt aber NICHTS darüber aus,
ob schwächere Trajektorien (Playout-Capping) den gleichen Nutzen bringen wie
zusätzliche vollwertige Spiele (siehe Einschränkung unten). Test B2 bleibt
sinnvoll, aber die eigentliche Frage ("reicht MEHR schwächere Menge, um
weniger, aber bessere Spiele zu schlagen") bleibt offen und braucht das
echte, gleich-rechenzeit-faire B2-Experiment aus STATUS.md.

**Ist `voll` auf BEIDEN Metriken gepaart besser UND p<0,05 auf mindestens
einer**: starker Befund, dass Korpusmenge (bei unveränderter Suchqualität)
messbar hilft — erhöht die Priorität von Task #14 deutlich, weil damit die
Menge-hilft-Grundannahme bestätigt ist und nur noch die
Trajektorienqualitäts-Frage (B2) offen bleibt.

## Bekannte Einschränkungen, bewusst akzeptiert

1. **Das ist NICHT der Task-#14-Tradeoff.** Task #14 tauscht Suchtiefe
   (weniger Sims/Zug) gegen mehr Spiele **bei gleicher Rechenzeit**
   (STATUS.md "Fairness-Kriterium: Vergleich bei gleicher Rechenzeit, nicht
   gleicher Spielzahl"). Diese Vorstudie testet nur, ob mehr Spiele **bei
   UNVERÄNDERTER Suchtiefe** (kein Playout-Capping, alle 900/450 Dateien
   stammen aus der normalen Produktions-Suche) überhaupt etwas bringen — die
   Richtung "hilft Menge überhaupt?", nicht "lohnt sich der Tausch
   Suchqualität-gegen-Menge?". Ein positiver Befund hier ist notwendig, aber
   NICHT hinreichend für eine Task-#14-Entscheidung.
2. **Ungleicher Val-Split zwischen den Armen.** Der Val-Split (10%) wird
   INNERHALB des jeweils sichtbaren Korpus gezogen (900 bzw. 450 Dateien) —
   `voll` validiert auf 90 Dateien, `halb` auf 45. Die Val-Metriken selbst
   sind dadurch zwischen den Armen nicht direkt vergleichbar; die
   Primärmetriken (Orakel, `--frozen`) umgehen das, weil sie auf demselben
   eingefrorenen `evaluations/frozen_eval_set.pkl` laufen, unabhängig vom
   Trainingskorpus.
3. **Zusammensetzung nur zum Stichtag 2026-08-01 geprüft — Universum ist
   explizit das eingefrorene v15/v16/v17-Fenster, spätere Generationen
   (v19, …) sind per Definition ausserhalb.** `tools/train_corpus_dose.py`
   klassifiziert `data/` NUR nach den drei erwarteten Präfixen; Dateien mit
   anderen Präfixen (z.B. die parallel laufende v19-Self-Play-Kampagne)
   gehören nicht zum Messfenster, werden beim Split-Aufbau nur gezählt/
   gemeldet (Konsolen-Info) und ändern nichts an der Ziehung. Weicht die
   Zusammensetzung INNERHALB des Fensters selbst vom Stand 900/600/200/100
   ab (z.B. versehentlich gelöschte v15/v16/v17-Dateien), bricht das Skript
   weiterhin hart ab statt still auf veränderter Grundgesamtheit zu ziehen —
   manuelle Prüfung nötig, KEINE automatische Neuziehung.
4. **40 Epochen sind ein Kompromiss** (identisch zu `PREREG_2d_encoder.md`
   Einschränkung 1): das from-scratch-Standardrezept ist nicht
   notwendigerweise für beide Korpusgrößen gleich gut kalibriert (der
   `halb`-Arm sieht pro Epoche halb so viele Positionen). Wird NICHT
   nachträglich pro Arm angepasst (würde die Fairness aufheben) — ein
   Ergebnis "halb braucht andere Epochenzahl" wäre ein Folge-Experiment.
5. **Kein direktes Arena-Gating vorgesehen.** Anders als
   `PREREG_2d_encoder.md` (dort folgt nach den Orakel-Metriken ein
   Arena-Schritt) ist diese Vorstudie eine reine Entscheidungsgrundlage für
   die Task-#14-Priorisierung, kein Kandidat für den Champion-Slot — `halb`
   ist per Konstruktion nie besser als `voll` als Champion-Kandidat (weniger
   Daten, sonst identisch), ein Gating von `halb` gegen den amtierenden
   Champion ist nicht sinnvoll.

## Ausführungsplan

1. Stratifizierte Ziehung berechnen + als
   `evaluations/train_corpus_dose_split.json` persistieren (einmalig, fester
   Seed `20260801`) — das Manifest friert BEIDE Dateimengen ein
   (`voll_files`: alle 900, `halb_files`: die 450 gezogenen).
2. Beide Hardlink-Sandboxen aufbauen: `data_dose_voll/` (900 Dateien) und
   `data_dose_halb/` (450 Dateien), je gegen das Manifest konsistenzgeprüft
   (Anzahl + `st_ino`-Hardlink-Identität).
3. 12 Läufe sequenziell — `tools/train_corpus_dose.py` (neu, Vorbild
   `tools/train_2d_vs_flat_fs.py`, aber OHNE `--encoder`-Durchreichung, STATT
   DESSEN `MOSAIC_DATA_DIR`-Env-Var je Subprozess, für BEIDE Arme). Da beide
   Arme gegen ihre eingefrorene Sandbox laufen, ist paralleles Self-Play
   (z.B. v19) unschädlich — kein Blocker mehr (Nachbesserung 2026-08-01,
   siehe "Technische Umsetzung"). `--no-snapshot` (Ablationslauf, kein
   Champion), `--no-plot`. Nach allen 12 Läufen werden beide Sandboxen
   inkl. HDF5-Caches entfernt, `data/` bleibt unangetastet.
4. Nach allen 12 Läufen: `tools/offline_diagnosis.py --frozen --model
   voll_s1_best halb_s1_best ... --out
   evaluations/offline_diagnosis_corpus_dose_frozen.json`.
5. Gepaarte Auswertung (`tools/train_corpus_dose.py` schreibt sie direkt mit,
   kein separates Skript) — Tabelle je Seed + Zusammenfassung (Ø-Differenz,
   t-Test, Vorzeichentest) für beide Orakel-Metriken, Ergebnis-JSON nach
   `evaluations/train_corpus_dose_result.json`.
6. Bericht an den Koordinator — Interpretationsregel oben automatisch
   angewendet (rein deskriptiv, der Mensch entscheidet trotzdem).

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- Beide Orakel-Metriken 6/6
gepaart fuer `voll`: `prior_mass_on_oracle_top3` +0,0221 (p=0,0013),
`kendall_tau` +0,0189 (p=0,0067) -- rund 2x der 2D-Encoder-Effektgroesse.
Zusaetzlich in der echten Arena bestaetigt: `voll_s3_best` 479:321 gegen
`halb_s3_best`, McNemar p<0,0001. Konsequenz: Task #14
(Playout-Cap-Randomisierung) stieg deutlich in der Prioritaet (dort dann
negativ ausgegangen, siehe `PREREG_pcr.md`). Belegstelle:
archive/history.md, Abschnitt "Korpus-Dosis-Messung (2026-08-01)" /
"ERGEBNIS" / "Nachtrag Dosis-Arena", Zeile ~6746-6821;
evaluations/train_corpus_dose_result.json.
