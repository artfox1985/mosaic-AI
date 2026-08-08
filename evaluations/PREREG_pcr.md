# Vorregistrierung: Playout-Cap-Randomization (PCR, Task #14)

**Angelegt 2026-08-02, VOR jedem Self-Play-Lauf dieses Experiments.** Reiner
Entwurf -- der Ausfuehrende dieser Vorregistrierung startet KEINEN der unten
beschriebenen Laeufe selbst (Auftragsgrenze: Task #14 ist engine-seitig
begrenzt auf `engine/src` + Tests). Zweck wie bei den Vorbild-Dokumenten
(`PREREG_2d_encoder.md`, `PREREG_corpus_dose.md`, Praezedenzfall
`PREREG_ownership_gumbel.md`): die Auswertungsregeln VOR der ersten Messung
festlegen, damit hinterher keine Metrik gewaehlt wird, die zum gewuenschten
Ergebnis passt. Die Regeln unten duerfen nach Sichtung der Ergebnisse NICHT
mehr geaendert werden.

---

## Hintergrund

Task #14 wurde bereits am 2026-07-28 als Test spezifiziert (STATUS.md,
Abschnitt "Task #14 als Test spezifiziert: Playout-Cap-Randomisierung") --
KataGo-Vorbild: ein Teil der Self-Play-Zuege bekommt nur eine guenstige,
verkuerzte Suche statt der vollen Suche, in der Hoffnung, dass die dadurch
gewonnene Spielmenge (mehr Value-Samples/Stunde) den Qualitaetsverlust bei
den Policy-Zielen (nur der Voll-Suche-Anteil liefert ein verlaessliches
Policy-Ziel) mehr als aufwiegt.

**Vorstudie `PREREG_corpus_dose.md` (2026-08-01/02) hat bereits einen Teil
der Grundannahme geprueft** (siehe STATUS.md, Abschnitt zur Korpus-Dosis-
Wirkungs-Messung): "hilft schlicht MEHR Korpus bei UNVERAENDERTER Suchtiefe
ueberhaupt?" -- Ergebnis dort bestimmt, ob dieses PCR-Experiment ueberhaupt
mit erhoehter oder gesenkter Prioritaet gefahren wird (siehe dortige
Interpretationsregeln). Diese Vorregistrierung deckt NUR die zweite,
eigentliche Task-#14-Frage ab: **lohnt sich der Tausch Suchqualitaet-gegen-
Menge**, bei gleichem Rechenaufwand (nicht: bei UNVERAENDERTER Suchtiefe wie
in der Vorstudie)?

**Engine-seitige Voraussetzung ist seit 2026-08-02 erfuellt** (dieser
Auftrag, `engine/src/self_play.rs`/`engine/src/net_mcts.rs`/
`engine/src/lib.rs`, noch ungebauter Wheel):

- `net_mcts::gumbel_top_m_for_budget(sims)` ersetzt die vorher feste
  `GUMBEL_TOP_M=16`-Konstante durch `clamp(round(sims/16), 4, 16)` -- bei
  400/600 Sims weiterhin exakt M=16 (Regressionstest
  `gumbel_top_m_for_budget_unchanged_at_400_and_600_sims`), bei kleineren
  Cheap-Budgets automatisch schmaler (z.B. `sims=150` -> M=9).
- `self_play::run_net_self_play`/`play_net_self_play_game` haben einen
  additiven `pcr_full_prob: Option<f64>`-Parameter (Default `None` = AUS,
  byte-identisches Verhalten zum Vor-PCR-Zustand) + `pcr_cheap_sims: u32`.
  Bei aktivem PCR wird pro echtem Drafting-Entscheid ein Muenzwurf aus dem
  spieleigenen RNG-Strom gezogen (`self_play::pcr_decide_full`, isoliert
  unit-getestet); das Ergebnis wird additiv als `"policy_target_valid":
  true/false` je Zug-Record gespeichert. `root_q` (seit dem v19-Auftrag
  vorhanden) wird in BEIDEN Zweigen (voll UND cheap) geschrieben -- jede
  Suche hat eine Wurzel, unabhaengig von der Suchqualitaet.
- Alle Aenderungen additiv, `cargo test` gruen (195 bestanden, 1 vorbestehend
  ignoriert), inkl. eines Rauchtests mit `pcr_full_prob=0.25` gegen einen
  real vorhandenen Checkpoint.

## Frage

Bei **gleichem Wandzeit-Budget** je Arm: erzeugt ein PCR-Self-Play-Lauf
(Anteil `p` der Zuege mit Voll-Suche, Rest mit Cheap-Suche) einen Korpus, der
zu einem **staerkeren** Netz fuehrt als ein klassischer Self-Play-Lauf
(jeder Zug Voll-Suche), trotz des Policy-Ziel-Qualitaetsverlusts auf dem
Cheap-Anteil?

## Arme

| Arm | Self-Play-Generator | Suchregel |
|---|---|---|
| `kontrolle` | `v19_2d_best` @ 600 Sims | klassisch -- JEDER Drafting-Zug Voll-Suche (600 Sims) |
| `pcr` | `v19_2d_best` @ 600 Sims (voll) / 150 Sims (cheap) | PCR -- `p=0.25` Voll-Suche, `p=0.75` Cheap-Suche (`pcr_full_prob=0.25`, `pcr_cheap_sims=150`) |

**Generator ist in BEIDEN Armen `v19_2d_best`** (amtierender Champion seit
dem v19-Zyklus, siehe STATUS.md) -- keine Generator-Konfundierung, einziger
Unterschied ist die Suchregel je Zug.

**Wandzeit-Budget, nicht Spielzahl, ist der Fairness-Anker** (identisches
Kriterium wie im urspruenglichen STATUS.md-Testentwurf 2026-07-28: "Vergleich
bei gleicher Rechenzeit, nicht gleicher Spielzahl" -- sonst misst man
trivial "weniger Daten ist schlechter"). **Vorschlag: T=4h je Arm**, auf
derselben Maschine, gleiche Thread-Zahl, sequenziell (nicht parallel) gegen
denselben `v19_2d_best`-Checkpoint gefahren, damit keine Ressourcen-
Konkurrenz die Wandzeit-Messung selbst verfaelscht. Beide Laeufe schreiben in
getrennte Datei-Praefixe (siehe Abschnitt "Fenster-Politik ab v20" unten fuer
die Praefix-Konvention, die auch fuer DIESES Mess-Experiment gilt, nicht nur
fuer den spaeteren Produktions-Einsatz).

## Erwarteter quantitativer Rahmen (aus STATUS.md, 2026-07-28, Test A/B)

Reine Sim-Zahl je Zug: `0,25 * 600 + 0,75 * 150 = 262,5` statt `600` --
Faktor **~2,29x weniger Sims/Zug** (die im urspruenglichen STATUS.md-Entwurf
genannten 2,67x nutzten `cheap=100` statt der hier konkret implementierten
`cheap=150`; mit 150 statt 100 ist der Sim-Faktor kleiner, aber die Cheap-
Suche pro Zug etwas verlaesslicher). Der tatsaechliche Wandzeit-Gewinn ist
KLEINER als 2,29x (STATUS.md-Kommentar: ein fixer Sim-unabhaengiger Anteil
`a` je Zug -- Tiling-DFS, Spiellogik, Feature-Extraktion, ONNX-Overhead --
daempft die Skalierung).

**Policy-Ziel-Durchsatz** (nur der Voll-Anteil liefert ein verlaessliches
`policy`-Ziel, `policy_target_valid=true`): bei `p=0,25` sinkt die Policy-
Ziel-Zahl je Spiel auf ~25% des Baseline-Werts. Kombiniert mit dem
(gedaempften) Wandzeit-Gewinn ergibt sich ein grober Richtwert von
**~0,57-0,6x Policy-Ziel-Durchsatz je Stunde** (2,29x mehr Spiele/Stunde ×
0,25 Policy-Ziele/Spiel ≈ 0,57 -- OBERE Schranke, da die reale
Wandzeit-Skalierung durch `a` schwaecher als 2,29x ausfaellt, der reale Wert
also eher NOCH niedriger liegt). **Das ist eine Herleitung aus den
STATUS.md-Kennzahlen, KEINE eigene Messung dieser Vorregistrierung** -- Test
A (STATUS.md, "Zeitgewinn", drei kurze Batches bei sims ∈ {100,400,600}) ist
die vorgesehene Methode, den tatsaechlichen Faktor direkt zu messen, bevor
der 4h-Lauf gestartet wird.

**Value-/`root_q`-Ziel-Durchsatz** steigt dagegen um den vollen (gedaempften)
Wandzeit-Faktor (~2,29x oder weniger) -- JEDER Zug, voll oder cheap, liefert
`root_q` + die Spielausgang-Labels (`scores`/`winner`/`round_transition_value`/
`bootstrap_value`), unabhaengig von `policy_target_valid`. Das ist der
eigentliche Wetteinsatz von Task #14: mehr, aber teils schwaechere
Value-Masse gegen weniger, aber durchgaengig verlaessliche Policy-Masse.

## Nach dem Self-Play: 6 gepaarte Flach-Encoder-Seeds je Korpus (Dosis-Methodik)

Vorbild `tools/train_corpus_dose.py` (nicht `tools/train_2d_vs_flat_fs.py` --
hier ist NICHT die Encoder-Architektur die Variable, sondern der
Self-Play-Korpus; die Sandbox-/Hardlink-/`MOSAIC_DATA_DIR`-Mechanik aus
`train_corpus_dose.py` passt direkter):

1. Aus `kontrolle` UND `pcr` je einen eingefrorenen Hardlink-Sandbox-Ordner
   bauen (`data_pcr_kontrolle/`, `data_pcr_pcr/`), analog
   `train_corpus_dose.py`s `data_dose_voll/`/`data_dose_halb/`-Muster --
   `data/` selbst bleibt unangetastet.
2. **6 gepaarte Seeds** (1..6) je Korpus, **flacher Encoder, from scratch**
   (kein `--encoder 2d`, kein `--load`) -- selbes from-scratch-Standardrezept
   wie `PREREG_2d_encoder.md`/`PREREG_corpus_dose.md`:
   ```
   python train.py --name <arm>_s<seed> --seed <seed> \
       --epochs 40 --lr 4e-4 --lr-schedule cosine \
       --value-target-variant nortv \
       --no-plot --no-snapshot
   ```
   12 Laeufe gesamt: `pcrkontrolle_s1..s6`, `pcrpcr_s1..s6`.
3. Neues Treiber-Skript `tools/train_pcr_dose.py` (noch nicht geschrieben --
   Teil der Ausfuehrung, nicht dieser Vorregistrierung), Vorbild
   `tools/train_corpus_dose.py`, inkl. dessen Nachbesserung vom 2026-08-01
   (Sandbox-Isolation statt hartem Abbruch bei parallel laufendem
   Self-Play).

## Entscheidungsmetriken (VORAB festgelegt)

### Primaer

Die zwei validierten Praediktoren (Memory `project_oracle_metrics_validated`,
`tools/offline_diagnose.py::ORACLE_KEYS`):

- `prior_mass_on_oracle_top3`
- `kendall_tau_policy_vs_oracle_q`

Berechnet mit `tools/offline_diagnose.py --frozen --model <12 Checkpoints>`.
**Orakel-Referenz: die seit dem v19-Zyklus aktuellen `frozen_v1_oracle_labels_v18.json`**
(STATUS.md, v19-Abschnitt: Umstellung von der fruehereren v16-Quelle auf
v18-Labels) -- nicht `v16_best` wie in den beiden aelteren PREREG-Dokumenten,
die vor der Umstellung geschrieben wurden.

Je Arm+Seed der beste Checkpoint (`*_best.pth`, `val_combined`-Auswahl,
Bestandslogik). Gepaarte Auswertung (Seed s in `pcr` gegen Seed s in
`kontrolle`):

- **Gepaarter t-Test**, zweiseitig, α=0,05 (Praezedenzfall
  `PREREG_ownership_gumbel.md`/`PREREG_2d_encoder.md`/`PREREG_corpus_dose.md`
  -- kein scipy, Kettenbruch-Naeherung der regularisierten unvollstaendigen
  Betafunktion, identischer Code wie `tools/train_2d_vs_flat_fs.py`).
- Exakter zweiseitiger Vorzeichentest zusaetzlich berichtet, NICHT der
  Primaertest.

### Sekundaer/informativ

- `value_r2_rounds_1_4` -- mitberechnet, aber laut Memory
  `project_offline_metric_resolution_limit` erst oberhalb ~0,015 Abstand
  aufloesend, keine Entscheidungsgrundlage.
- Tatsaechlich gemessener Sim-Faktor + Wandzeit-Faktor aus Test A (siehe
  oben) -- prueft die Herleitung im Abschnitt "Erwarteter quantitativer
  Rahmen" nachtraeglich gegen die Realitaet.
- Tatsaechliche `policy_target_valid`-Quote im `pcr`-Korpus (Soll ~25%,
  Toleranzband analog zum Rauchtest dieses Auftrags: die 4-Spiele-Probe ergab
  eine plausible Quote nahe 25% bei `p=0,25`).

## Abbruch-/Fortsetzungsregel (VORAB festgelegt)

**Ist `pcr` auf BEIDEN Orakel-Metriken gepaart schlechter** (Ø-Differenz < 0,
Richtung egal ob signifikant): der Tausch Suchqualitaet-gegen-Menge lohnt
sich fuer dieses Design nicht -- kein Arena-Gating noetig, Task #14 wird
NICHT produktiv eingesetzt (analog Ownership-Kopf-/2D-Encoder-Praezedenzfall).

**Ist `pcr` auf MINDESTENS EINER Metrik gepaart besser** (unabhaengig von
Signifikanz): das Arena-Gating (naechster Schritt) lohnt sich.

**Ist `pcr` auf BEIDEN Metriken gepaart besser UND p<0,05 auf mindestens
einer**: starker Befund fuer Task #14 -- Arena-Gating hat hohe Prioritaet,
Uebergang in den Produktionsbetrieb (siehe "Fenster-Politik ab v20" unten)
wird vorbereitet.

## Bestaetigungsschritt: Arena des Siegers

Bester `pcr`-Checkpoint (nach Primaermetrik) vs. bester `kontrolle`-Checkpoint
in der echten Arena (400 gepaarte Partien, McNemar exakt, Muster
`tools/paired_arena_plate_ab.py`) -- **laeuft NICHT der Ausfuehrende dieser
Vorregistrierung** (Rust-Wheel-Install noetig), sondern der Koordinator nach
Freigabe. Nur als Schritt dokumentiert, kein Teil der Laeufe/Auswertung
dieses Dokuments.

## Bekannte Einschraenkungen, bewusst akzeptiert

1. **Flacher Encoder als Messproxy, obwohl der Champion 2D ist.** Analog
   `PREREG_corpus_dose.md`s Wahl (dort: billige, schnelle Vorstudie): die 12
   Trainingslaeufe dieser Vorregistrierung nutzen bewusst den flachen
   Encoder, NICHT `Mosaic2DNet`, obwohl `v19_2d_best` (2D) der amtierende
   Champion UND der Self-Play-Generator BEIDER Arme ist. Grund: Trainingszeit
   (2D ist laut Task-#11-Kostenanalyse, STATUS.md, ~30x wall-clock teurer
   from scratch) und Konsistenz mit den beiden bestehenden PREREG-Vorbildern.
   **Risiko**: die Policy-/Value-Ziel-Qualitaetsfrage koennte architekturabhaengig
   sein (der 2D-Encoder koennte z.B. robuster oder empfindlicher gegenueber
   dem Cheap-Suche-Rauschanteil sein als der flache) -- ein Ergebnis hier ist
   NICHT automatisch auf den 2D-Encoder uebertragbar. Eine 2D-Bestaetigung
   waere ein Folge-Experiment, kein Teil dieser Vorregistrierung.
2. **Policy-Ziel-Durchsatz-Schaetzung (~0,57-0,6x/Stunde) ist eine
   Herleitung, keine Messung.** Basiert auf STATUS.md-Kennzahlen vom
   2026-07-28 (100 v16-Spiele, andere Engine-Generation, `cheap=100` statt
   des hier implementierten `cheap=150`) UND auf der Annahme, dass sich die
   durchschnittliche Zug-/Spiellaenge unter PCR nicht qualitativ aendert
   (unbestaetigt -- eine schwaechere Cheap-Suche koennte z.B. systematisch
   laengere/kuerzere Partien erzeugen, was die Rechnung verschiebt). Test A
   (Sim-Faktor direkt aus drei kurzen Batches messen) ist Teil des
   Ausfuehrungsplans, genau um diese Herleitung vor dem teuren 4h-Lauf zu
   pruefen.
3. **40 Epochen, `--value-target-variant nortv`, Val-Split-Seed 20260707**
   sind unveraendert das from-scratch-Standardrezept, nicht neu fuer diesen
   Korpustyp kalibriert (identische Einschraenkung wie in
   `PREREG_2d_encoder.md`/`PREREG_corpus_dose.md`).
4. **`v19_2d_best`@600 als Generator bindet das Ergebnis an DIESEN
   Checkpoint-Stand.** Eine spaetere Champion-Generation koennte andere
   Policy-/Value-Charakteristika haben (schaerfere/flachere Priors), was die
   PCR-Kosten-Nutzen-Abwaegung verschieben kann -- dieses Ergebnis ist keine
   fuer alle Zukunft gueltige Konstante.
5. **Kein Ownership-Kopf (Task #9) aktiv.** STATUS.md notiert, dass der
   PCR-Handel "deutlich guenstiger" wuerde, sobald Task #9 landet (72 statt 1
   Value-Label je Position). Diese Vorregistrierung misst PCR OHNE
   Ownership-Kopf -- ein spaeteres, positives PCR-Ergebnis MIT Ownership-Kopf
   waere kein Widerspruch zu einem hier evtl. negativen Ergebnis, sondern ein
   anderer Messpunkt.

## Fenster-Politik ab v20 (Koordinator-Entscheid, 2026-08-02 -- betrifft NUR den Produktions-Einsatz nach einem positiven A/B, nicht die Messung selbst)

Diese Regeln greifen ERST, wenn (a) das A/B-Experiment oben abgeschlossen
ist, (b) die Abbruch-/Fortsetzungsregel fuer `pcr` positiv ausfaellt und (c)
das Arena-Gating bestaetigt. Sie betreffen die KAMPAGNEN-Planung ab dem
naechsten Zyklus (v20), nicht diese Vorregistrierung selbst -- kein
Engine-Code, reine Prozess-/Dateibenennungsregel:

1. **Regel**: Alt-Champion-Tails im Replay-Fenster (siehe Memory
   `project_replay_window_strategy`) bestehen IMMER aus Voll-Suche-Spielen.
   PCR-Spiele dienen NUR der eigenen Generation als frische Value-Masse und
   wandern NIE als Tail in spaetere Fenster.
2. **Mechanik** (kein Engine-Code, reine Kampagnen-Planung): jede Generation
   faehrt ab v20 zwei Self-Play-Kampagnen mit getrennten Datei-Praefixen --
   ein kleiner klassischer Block (~1000-2000 Spiele voll @600 Sims, Praefix
   z.B. `selfplay_v20full_`) + ein PCR-Bulk-Block (Praefix
   `selfplay_v20pcr_`). Die Fenster-Rotation der JEWEILS NAECHSTEN Generation
   zieht ihre Alt-Champion-Tails NUR aus den `*full_`-Dateien.
3. **Fuer v20 selbst ist die Regel automatisch erfuellt**: alle heute
   vorhandenen Datei-Bestaende (`selfplay_v18_*`, `selfplay_v19_*`, etc.)
   sind Vor-PCR/reine Voll-Suche -- es gibt noch keine PCR-Dateien, die
   faelschlich als Tail einfliessen koennten.
4. **Nebeneffekte, zu dokumentieren, sobald die Zwei-Kampagnen-Struktur
   produktiv laeuft**:
   - Der Voll-Suche-Block daempft den Policy-Ziel-Rueckgang des PCR-Bulks
     (siehe Abschnitt "Erwarteter quantitativer Rahmen" oben -- der
     PCR-Bulk allein saehe eine ~0,57-0,6x-Policy-Ziel-Durchsatzrate, der
     kombinierte Korpus aus beiden Bloecken weniger stark).
   - Die Praefix-Trennung haelt die Zusammensetzungs-Manifeste sauber (analog
     `train_corpus_dose.py`s Praefix-Klassifizierung nach Versions-Praefix --
     ein Fenster-Rotationsskript kann `*full_`/`*pcr_` unterscheiden, ohne
     jede Datei einzeln nach `policy_target_valid`-Quote inspizieren zu
     muessen).

## Ausfuehrungsplan (noch NICHT gestartet)

1. Wheel-Build + -Aktivierung mit den PCR-Aenderungen (Koordinator, nicht
   Teil dieses Auftrags).
2. Test A (Sim-/Wandzeit-Faktor direkt messen, drei kurze Batches je
   sims ∈ {150, 600} plus die Kontroll-/PCR-Mischung) -- prueft die Herleitung
   im Abschnitt "Erwarteter quantitativer Rahmen", BEVOR der teure 4h-Lauf
   gestartet wird.
3. `kontrolle`- und `pcr`-Self-Play, je T=4h, `v19_2d_best`@600 Sims,
   getrennte Datei-Praefixe (siehe "Fenster-Politik ab v20" fuer die
   Praefix-Konvention).
4. 6 gepaarte Flach-Encoder-Seeds je Korpus (`tools/train_pcr_dose.py`, noch
   zu schreiben, Vorbild `tools/train_corpus_dose.py`).
5. `tools/offline_diagnose.py --frozen --model pcrkontrolle_s1_best
   pcrpcr_s1_best ... --out evaluations/offline_diagnose_pcr_dose_frozen.json`.
6. Gepaarte Auswertung (t-Test + Vorzeichentest fuer beide Orakel-Metriken),
   Ergebnis-JSON nach `evaluations/train_pcr_dose_result.json`.
7. Bei positivem Ergebnis (siehe Abbruch-/Fortsetzungsregel): Arena-Gating
   des Siegers, danach Uebergang in den produktiven Zwei-Kampagnen-Betrieb ab
   v20 (Fenster-Politik oben).
8. Bericht an den Koordinator -- kein Gating, kein Wheel-Install, keine
   Arena durch den Ausfuehrenden dieser Vorregistrierung.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN (negativ)** -- 12 Laeufe, beide
Orakel-Metriken 0/6 fuer `pcr` (schlechter): `prior_mass` -0,0262
(p=0,0008), `kendall_tau` -0,0211 (p=0,0020) -> nach Abbruchregel kein
Gating, v20-Self-Play blieb klassisch. Bestaetigt durch Doku-Arena:
`pcrpcr` 67:83 gegen `pcrkontrolle`, SPRT-H0, McNemar p=0,26. Am
2026-08-06 wurde Task #14 formal WIEDER eroeffnet, aber als NEUES
Experiment (neues Value-Ziel nach #34, neu gemessener
Tiling-Cache-Durchsatz 1,371x) -- keine Neulesung dieser Zahlen.
Belegstelle: archive/history.md, Abschnitt "PCR-A/B ABGESCHLOSSEN: Task
#14 wird NICHT produktiv eingesetzt", Zeile ~7008-7063; Wiedereroeffnung
Zeile ~10041-10094; evaluations/train_pcr_dose_result.json.
