<!-- STATUS: OFFEN | Frage: Lernt der Value-Kopf den Spaltenwert, wenn Self-Play von HALBFERTIGEN Spalten-Stellungen aus FREI weiterspielt (Startpositions-Seeding, KataGo-startPoses-Muster) -- also On-Policy-Wertdaten statt erzwungener Trajektorien? | Beleg: komplette Kette durchgemessen (par.2-4c): Bausteine 1-3 gebaut/abgenommen, Training v21-seedk1 (Warm Start, Best=Epoche 1), Arena-Verdikt 2026-08-23 (par.4c): KEIN k1-Signal (14,1 %/Swap 13,5 % < 22-%-Schwelle; nominell hoechste je gemessene Netz-Rate), KEIN Siegverlust (220/407 u. 199/407 gg. Champion, gg. Kontrollarm asymN n.s.). Mechanik-Sonde par.4d: ERSTES POSITIVES Zustandssignal (Tau +0,14 vs N -0,19, p=0,017) -- Mechanik bewegt, Verhalten (noch) nicht. Folgearme = Nutzer-Entscheid. Primaerarm des Policy-Seiten-Zuschnitts (Nutzer-Freigabe der Reihenfolge 2026-08-22); Anlass: RESEARCH_plate_intent_external F1/F4 (Startzustandsverteilung ist der belegteste Strukturhebel; Off-Policy-Diagnose erklaert das Asym-Null par.14/15). Stellungsquelle: der vorhandene Asym-Korpus. -->

# PREREG-SKELETT: Startpositions-Seeding -- frei weiterspielen ab halbfertigen Spalten

Stand **2026-08-23: komplette Kette durchgemessen** (Ergebnisse in
par.2/par.3/par.4a-4c; Verdikt par.4c). par.1/par.4 unten sind der
originale Planungstext von 2026-08-22.

## par.1 Anlass und Mechanismus

Das Asym-Curriculum scheiterte an einem jetzt benannten Strukturfehler
(par.14-16 der Asym-Prereg): erzwungene Trajektorien liefern den Wert
einer Politik, die das Netz nie spielt (Off-Policy-Value-Fehler), und
Klon-Ziele im Prior koennen sich gegen das Wert-Backup nicht
durchsetzen. Startpositions-Seeding dreht den Spiess um: die seltene
Situation (halbfertige Spalte) wird zur AUSGANGSLAGE, und ab dort
spielen BEIDE Seiten frei mit dem aktuellen Netz. Der Wert des
Weiterbauens vs. Abbrechens wird damit erstmals on-policy erhoben --
die Labels beschreiben eine Politik, die das Netz tatsaechlich spielt.
Produktions-Praezedenz laut Recherche: KataGo startPoses/hintPoses;
RGSC (+77/+89 Elo). (Agenten-Befunde mit Quellen, Report F1/F4.)

**Verifikations-Nachtrag zum Recherche-Kontext (Koordinator, am Code
geprueft 2026-08-22):** die mctx-Faktor-14-Rechnung des Reports gilt
fuer UNSERE Engine nicht -- GUMBEL_C_SCALE=1,0 statt mctx 0,1, und die
hauseigene Task-#18-Kalibrierung (net_mcts.rs:2795ff) misst
sigma(q):ln(prior) mit Verhaeltnis-Median 1,23, also praktisch
Gleichgewicht. Die Report-Option "Q-Skalierung temperieren" ist
zusaetzlich hauseigen vorbelastet: c_scale 0,3 senkte den absoluten
Score beider Seiten um ~13 % (Task-#18-Gegenprobe). Sie wird deshalb
NICHT gemessen; dieser Absatz ist ihre dokumentierte Schliessung.
**Aera-Nachmessung (2026-08-22, Nutzer-Rueckfrage):** die Kalibrierung
wurde auf v21_2d_brierbest wiederholt
(`evaluations/gumbel_scale_calibration_v21.json`, 216 Stellungen @400):
q wiegt das **1,47-Fache** des Priors (v18-Aera: 1,23), je Runde
1,30-1,46 (R4: 2,92), Gleichgewicht laege bei c_scale~0,68. Die
Schliessung ist damit auf der aktuellen Aera bestaetigt: kein
Faktor-14-Ungleichgewicht, Temperieren ist nicht der Hebel.

## par.2 Baustein 1: Stellungssatz

- Quelle: `data/asym_corpus/selfplay_v21_asymS_*.pkl` (bleibt lokal,
  Nutzer-Entscheid 2026-08-22). Kandidaten: Zustaende der ZWANGSSEITE
  (Map `zwangsseiten_map.txt`) mit Spaltenfortschritt, z. B.
  max(col_fill) in {3,4,5} und Runde in {2,3,4}; Ziehung stratifiziert
  ueber Runde und Fortschritt, dedupliziert je Partie (hoechstens eine
  Stellung je Partie), Zielumfang ~1.000-2.000 Startstellungen.
- Kuratierungs-Bericht VOR der Generierung (Verteilung Runde x
  Fortschritt x aktive Platten), analog Deckungs-Bericht des
  Ownership-Korpus.

**ERGEBNIS BAUSTEIN 1 (2026-08-22, `tools/seed_position_curation.py`;
Python-Spaltenzaehlung gegen die Engine verifiziert, 500/500
identisch):** 7.797/8.000 Zwangspartien mit Kandidat; Auswahl 1.500
Stellungen (`data/seed_positions/seed_positions_v1.jsonl`, Seed
20260822, hoechstens eine je Partie), Bericht
`evaluations/seed_positions_curation_report.json`. Verteilung: R2
duenn (90/9/0 fuer p3/p4/p5 -- vollstaendig uebernommen,
dokumentierte Schieflage), R3/R4 quotiert 183-276 je Stratum;
k1-aktiv 567/1500 (37,8 % ~ 3/8). Restlaenge ab Startpunkt: Mittel
43,6 % einer Vollpartie. **Kostenrechnung fuer par.6** (Durchsatz
0,21-0,29 Vollpartien/s): k=4 -> 6.000 Partien in 2,5-3,5 h; k=6 ->
9.000 in 3,8-5,2 h; k=8 -> 12.000 in 5,0-6,9 h.

## par.3 Baustein 2: Engine-Faehigkeit "Start ab Stellung"

**ERGEBNIS BAUSTEIN 2 (2026-08-22, gebaut + abgenommen):** additiver
Pfad `--seed-positions` (self_play.py -> net_self_play_games ->
run_net_self_play mit globalem Stellungs-Offset gegen die
Chunk-Wiederholungs-Falle; unified_game_loop startet am
deserialisierten Zustand). Zuordnung als [seed_position]-Logzeile.
Abnahme: Suite 466/0 (neuer Determinismus-/Terminierungs-Test);
Paritaets-Hash 8c6684ff... HAELT (Default aus = byte-identisch);
Netz-Smoke 2x4 Partien ab echten Korpus-Stellungen BYTE-IDENTISCH
(SHA256 gleich, Startrunde 2, alle bis Runde 5 + Winner-Stempel).
**Echter Nebenbefund dabei (gefixt):** json_to_state untertreibt
`dome_tiles_placed_this_round` (can_place_dome-Ableitung 0|2) -- der
geseedete Spieler durfte eine Kuppel zu viel beginnen und
execute_dome_move riss am Token-Verbrauch. Korrektur
(tokens==Kuppeln-Invariante) bewusst NUR im Seeding-Pfad
(`seed_state_fixup`), damit Paritaetssonde/Frozen-Set-Basislinien
unberuehrt bleiben; fuer Peek-Historien konservativ-legal.

Urspruenglicher Planungstext: Self-Play kann heute nur ab Spielbeginn starten (setup_new_game).
Noetig: ein additiver Pfad, der eine serialisierte Stellung als
Partie-Start laedt (Roundtrip existiert: Serializer + replay-exakte
Zustaende), Seeds/Manifest wie gehabt, Kennzeichnung der Records
(neues additives Feld `seeded_from`), damit Auswertungen Start- von
Normal-Partien trennen koennen. Golden-/Paritaets-Gates wie ueblich:
Default aus = byte-identisch.

## par.4 Baustein 3: Korpus + Training + Messung

- Korpus: je Startstellung k freie Partien (k=4-8, beide Seiten
  aktuelles Netz, 200 Sims, rtv aus) -> ~8.000-16.000 Partien,
  Ablage eigener Ordner (nicht-rekursiver Glob, Traeger-Frage explizit:
  policy-tragend JA, die Partien sind on-policy).
- Training: Standardrezept, Warm Start Champion, Fenster = b18-Regex +
  Seeding-Korpus (+ Asym-N als Value-Material? -> beim Start
  entscheiden, EIN Faktor bleibt die Regel).
- Messung: exakt das Asym-par.7-Muster auf den 407 Kampagnen-Seeds
  (Nullarm, Brettwechsel-Pflicht): k1-Rate auf k1-aktiven Partien
  >= 30 % Ziel / >= 22 % Signal, UND kein signifikanter Siegverlust
  gegen eine Kontrolle (Kontrollarm: gleiches Rezept ohne
  Seeding-Korpus ODER der vorhandene v21-asymN-Arm auf denselben
  Seeds -- beim Start festlegen). Mechanik-Sonde
  `asym_value_sibling_check` zusaetzlich (within-Vergleich).

## par.4a ERGEBNIS BAUSTEIN 3: KORPUS GENERIERT + TRAINING GESTARTET (2026-08-23)

**Korpus fertig** (Log `logs/seed_corpus_gen_20260822.log`, in dieser Sitzung
geprueft): 9.000/9.000 Partien, 900 Dateien (`data/seed_corpus/*.pkl`,
ausgezaehlt: 900), 642.999 Zuege, Dauer 15.049,7 s (rund 4,2 h) --
Log-Endzeile "Fertig: 9000 Spiele, 642999 Zuege nach 15049.7s". Exit ohne
Fehler: keine Treffer auf error/traceback/exception/hang/abbruch im
kompletten Log. Befehl (aus der 2026-08-22-Uebergabe, `evaluations/STATUS.md`):

    $env:MOSAIC_DATA_DIR = "data/seed_corpus"
    python -u self_play.py --mode network --model models/alphazero_v21_2d_brierbest.onnx `
      --games 9000 --sims 200 --version v21_seedk1 --threads 8 `
      --seed 20260824 --seed-positions data/seed_positions/seed_positions_v1.jsonl

**Stellungs-Zuordnung gesichert** (`data/seed_corpus/seed_position_map.txt`,
in dieser Sitzung ausgezaehlt): 9.000 Zeilen, genau 1.500 verschiedene
`idx`-Werte (0 bis 1499) a exakt 6 Partien -- die k=6-Zyklik aus par.6.1
haelt exakt, keine Abweichung.

**Nebenbefund (erwartbar, in dieser Sitzung nachgerechnet):** die
Dateigroesse einer 10-Partien-Datei haengt systematisch von der Startrunde
ab -- ueber alle 900 Dateien Korrelation (Mittelwert der Startrunde der 10
Partien gegen Dateigroesse) r=-0,98 (fruehe Dateien, Startrunde 2, rund
11-13 MB; spaete Dateien, Startrunde rund 3,3-3,6, rund 5-7 MB), weil die
Stellungsdatei stratenweise nach Runde sortiert ist und die Zuordnung
Partie i -> idx (i mod 1500) je Datei benachbarte, also rundenaehnliche idx
buendelt (R2-Starts mit langer Restpartie, spaetere Runden mit kurzer
Restpartie).

**Training v21-seedk1 gestartet** 2026-08-23 01:19 (Manifest
`models/manifest_train_v21-seedk1_20260823_011959.json`, in dieser Sitzung
gelesen). Warm Start Champion bestaetigt an der Logzeile "Warm-Start
erkannt: Trainiere fuer 20 Epochen" (`logs/train_v21_seedk1_20260823.log:44`
-- in dieser Sitzung nachgezaehlt; eine fruehere Notiz nannte Zeile 41, das
ist NICHT die nachgezaehlte Zeile). Flags = asymS-Muster (`cli_args` im
Manifest: epochs 20, seed 2, lr 5e-5, lr_schedule cosine, encoder 2d,
value_head wdl, opp_points_head an, endgame_head an, value_target_variant
nortv) plus `extra_data_dir=data/seed_corpus`. Fenster: b18-Regex schliesst
800 von 2.945 Dateien vor dem Split aus (Logzeile). Traeger-Manifest
`policy_carrier_manifest_seedk1.json` aktiv, Cache-Zeile verifiziert:
v21_seedk1 900/900 policy-tragend, Gesamtkomposition laut
`corpus_composition` im Manifest 900 v21_seedk1 + 800 v20wdlsw + 545 v18 +
400 v19wdl + 400 v20wdl = 3.045 Dateien. Ladung in zwei Tranchen: 2.741
Trainings- + 304 Val-Dateien (dateiweiser 90/10-Split), 3.717.089 Zuege
(Logzeile "Datensatz geladen"), neuer HDF5-Cache `.cache_811fbb510c2e.h5`.

## par.4b ARENA-RUNBOOK (Plan, vorbereitet 2026-08-23)

**Nichts hiervon ist ausgefuehrt** -- das Training laeuft noch, der
Checkpoint existiert nicht. Dieser Absatz haelt den Ablauf fest, der beim
Trainingsende ansteht.

### Erwarteter Checkpoint-Name

Abgeleitet aus dem Namensmuster der Asym-Arme in `models/`: das
Trainings-Manifest der Asym-Kontrolle traegt `"version": "v21-asymN"` und
die dazugehoerigen Checkpoints heissen `alphazero_v21-asymN_best.onnx` /
`_brierbest.onnx` / `.pth` (in dieser Sitzung per `ls models` und
`json.load(...)["version"]` geprueft). Das seedk1-Manifest traegt exakt
denselben Feldnamen mit Wert `"version": "v21-seedk1"`
(`models/manifest_train_v21-seedk1_20260823_011959.json:2`) --
Baustein-fuer-Baustein dasselbe Muster. Erwarteter Name also:
**`models/alphazero_v21-seedk1_best.onnx`** (analog `_brierbest.onnx`,
`.pth`). Geprueft: die Datei existiert noch nicht (`ls models` ohne
Treffer, 2026-08-23) -- das ist der erwartete Zustand waehrend das
Training laeuft, keine Annahme ueber den Trainingsausgang.

### Arena-Invokation (Plan, S-Muster exakt uebernommen)

Fundstelle des Musters: `PREREG_asymmetric_curriculum.md` par.13/par.14
(Instrument `paired_arena_env_ab.py`, Null-Knopf-Muster, 400/400 Sims,
`--log-games`, drei sequenzielle Laeufe inkl. Brettwechsel-Arm). Die
exakte Befehlszeile ist aus den Feldern der drei Asym-Artefakte
(`evaluations/paired_arena_env_asym_nullarm_{s,n,s_swap}.json`, in dieser
Sitzung per `json.load` ausgelesen: `env_name`, `arms`, `control`, `model`,
`model_b`, `net_sims`, `sims_b`, `seeds`) rekonstruiert; `--help` des Skripts
in dieser Sitzung gegengeprueft. Uebertragen auf seedk1 waere das:

    # (1) v21-seedk1_best gegen Champion, Brett 0 = seedk1
    python tools/paired_arena_env_ab.py --env-name MOSAIC_OWNERSHIP_W --arms 0 --control 0 `
      --model models/alphazero_v21-seedk1_best.onnx --model-b models/alphazero_v21_2d_brierbest.onnx `
      --net-sims 400 --sims-b 400 --seeds evaluations/seeds_asym_407.txt `
      --out-prefix seedk1_nullarm --log-games

    # (2) Brettwechsel-Arm (Pflichtteil, par.7/S-Muster): vertauschte --model/--model-b
    python tools/paired_arena_env_ab.py --env-name MOSAIC_OWNERSHIP_W --arms 0 --control 0 `
      --model models/alphazero_v21_2d_brierbest.onnx --model-b models/alphazero_v21-seedk1_best.onnx `
      --net-sims 400 --sims-b 400 --seeds evaluations/seeds_asym_407.txt `
      --out-prefix seedk1_nullarm_swap --log-games

`models/champion.txt` zeigt heute (2026-08-23, geprueft) auf
`v21_2d_brierbest`, also `models/alphazero_v21_2d_brierbest.onnx` --
identisch zum `model_b` der drei Asym-Artefakte. Der `--env-name
MOSAIC_OWNERSHIP_W --arms 0 --control 0`-Teil ist ein Null-Knopf-Leerlauf
(Instrument-Pflichtparameter ohne inhaltliche Wirkung, exakt wie in den drei
Asym-Artefakten uebernommen) und kein Seeding-spezifischer Regler.

**Kontrollarm auf denselben Seeds** (Nutzer-Entscheid par.6.2: der
vorhandene v21-asymN): dessen Artefakt liegt bereits vor
(`evaluations/paired_arena_env_asym_nullarm_n.json`, `model =
models/alphazero_v21-asymN_best.onnx`, dieselben 407 Seeds aus
`evaluations/seeds_asym_407.txt`) -- **kein neuer Lauf noetig**, der
Vergleich zieht die dort bereits gemessenen k1-Raten/Siegquoten heran.

### Auswertung (Plan, Instrument-Muster par.14)

1. k1-Raten aus den Endwertungs-Zeilen der `--log-games`-Partie-Logs
   ("Vertikale Reihen: X Pkt", Schwelle >= 7 = mindestens eine volle
   Spalte) -- exakt das par.14-Instrument, gleicher Nenner (k1-aktive
   Partien) wie beim Asym-Null, damit direkt vergleichbar.
2. Block-Ebene-Statistik (Block-t, nicht Paar-SE) fuer die k1-Raten-
   Differenz und fuer die Siegquote gegen den Champion -- Regel
   `feedback_arena_block_correlation`.
3. Vergleich der seedk1-k1-Rate gegen die bereits vorliegende
   v21-asymN-k1-Rate (9,6 % eigene Seite, k1-aktiv, par.14-Tabelle) auf
   denselben 407 Seeds.
4. Sonde `tools/probes/asym_value_sibling_check.py` zusaetzlich (within-
   Vergleich, Teilfrage-B-Analogon): die Datei wird NICHT veraendert, aber
   fuer einen seedk1-Lauf waeren die `MODELS`-Pfade
   (`tools/probes/asym_value_sibling_check.py:45-48`) so zu setzen:
   `"seedk1": "models/alphazero_v21-seedk1_best.onnx"` anstelle von `"S"`,
   `"N": "models/alphazero_v21-asymN_best.onnx"` unveraendert (derselbe
   Kontrollarm wie im Haupt-Arena-Vergleich, par.6.2) -- die
   Stellungsbasis (`probe_sibling_succ_k1_w1.0.json`) und die
   Tau-Auswertung bleiben unveraendert.

### par.7-Schwellen (uebernommen aus par.6.3, Plan-Verdikt erst nach der Arena)

- **Erfolg:** k1-Rate auf k1-aktiven Partien >= 30 % (Ziel) bzw. >= 22 %
  (Signalschwelle), UND kein signifikanter Siegverlust gegen den
  Kontrollarm v21-asymN auf denselben 407 Seeds.
- **Misserfolg:** k1-Rate < 22 % ODER signifikanter Siegverlust.
- Seeds: exakt `evaluations/seeds_asym_407.txt` (407 Zeilen, geprueft),
  Brettwechsel-Pflicht wie in par.13/par.14 des Asym-Curriculums.

## par.4c ERGEBNIS ARENA + VERDIKT (2026-08-23, Koordinator; Instrument-Zahlen von Agent erhoben und vom Koordinator unabhaengig nachgezaehlt, bit-gleich)

**par.6-Schwellen VERFEHLT: kein k1-Signal, kein Staerkepreis.**

- **k1-Rate (par.14-Instrument der Asym-Prereg, Nenner 156 k1-aktive
  Partien, Schwelle Vertikale Reihen >= 7):** seedk1 **22/156 = 14,1 %**
  (Brettwechsel **21/156 = 13,5 %**) -- unter der 22-%-Signalschwelle.
  Referenzen auf denselben Seeds: Champion-Gegenseite 13/156 = 8,3 %
  (Swap 17/156 = 10,9 %), Kontrollarm asymN 15/156 = 9,6 %, Grundrate
  20/156 = 12,8 %, asymS damals 19/156 = 12,2 %. Nominell die hoechste
  je gemessene Netz-Rate, aber der Abstand zur Grundrate ist 2 Partien.
- **Staerke (Artefakte `paired_arena_env_seedk1_nullarm{,_swap}.json`):**
  220/407 gegen den Champion (Block-t +2,18, nB=16 a 25; Binomial
  p=0,113), Brettwechsel 199/407 -- der Ueberschuss traegt den
  Brettwechsel nicht. Gegen den Kontrollarm asymN (205/407, dieselben
  Seeds): McNemar exakt p=0,303, Block-t +1,48, n.s. **Kein
  signifikanter Siegverlust, nominell leicht positiv.**
- Instrument-Validierung: die Nachimplementierung reproduziert die
  registrierten par.14-Zahlen des asymN-Laufs bit-genau (15/156 und
  14/156). Dokumentierte Instrument-Caveats: Blockzahl nB=16 (halbe-
  Blockgroesse-Regel) gegen nB=17 im par.14-Text -- Diskrepanz
  ausgewiesen, aendert kein Verdikt (beide Vergleiche n.s. bzw.
  marginal); Skripte im Sitzungs-Scratchpad, Formeln aus
  `paired_arena_env_ab.py`/`plate_points_from_arena.py`.
### par.4d MECHANIK-SONDE (2026-08-23, Koordinator-Lauf): ERSTES POSITIVES ZUSTANDSSIGNAL

`asym_value_sibling_check` (Modellpfade auf seedk1_best angepasst,
Ausgabe nach `evaluations/seedk1_value_sibling_check.json`, damit das
Asym-Artefakt erhalten bleibt; dieselben 33 gepaarten Stellungen wie
Asym-par.15): **Tau(Value~k1-Puffer) seedk1 +0,140 gegen N -0,185,
Differenz +0,325 (sd 0,809, t +2,30), Vorzeichentest 17/5/11,
p=0,017.** Zum Vergleich Asym-par.15: S -0,08 gegen N -0,19, p=0,108
(n.s.). Der seedk1-Value-Kopf ordnet Geschwister erstmals POSITIV und
signifikant nach k1-Puffer -- das On-Policy-Seeding hat auf
Zustandsebene gelehrt, was das Behavior-Cloning (Asym par.16) nicht
konnte. Einordnung: sekundaeres Instrument, n=33; das
Verhaltens-Verdikt par.4c bleibt "kein Signal". Die Kombination
(Mechanik positiv, Verhalten unbewegt) passt zur par.3-Diagnose der
R5-Prereg: die Suche fragt den Kopf zu selten/zu schwach -- Folgearme
(Dosis, UVFA, Minimax-Knopf) setzen genau dort an.

- **Einordnung:** der On-Policy-Hebel (KataGo-startPoses-Muster) hat in
  der k=6-Dosis die k1-Rate nicht ueber die Signalschwelle bewegt --
  dritter Nullbefund der Plattenblick-Kette am Value-Kopf, erneut bei
  null Staerkekosten. Offen bleibt die Mechanik-Sonde
  (`asym_value_sibling_check`, par.4-Pflichtteil); Folgearme (UVFA,
  Dosis) sind Nutzer-Entscheide.

## par.5 Verhaeltnis zu den Nachbar-Zuschnitten

- **UVFA (`PREREG_uvfa_plate_regime.md`)**: Kombinations-/Folgearm.
  Seeding erzeugt die Daten, UVFA macht das Regime unterscheidbar --
  kombinierbar, aber nie im selben Mess-Arm einfuehren (ein Faktor).
- **Implicit-Minimax-Knopf (`PREREG_implicit_minimax_backup.md`)**:
  paralleler SUCH-Hebel, eigene Messung.
- Das Wanduhr-/Exklusiv-Regelwerk und die Fenster-Pinning-Regeln
  gelten unveraendert.

## par.6 NUTZER-ENTSCHEIDE (gefallen 2026-08-22, "nimm deine Vorschlaege")

1. **k=6**: 9.000 Partien (~3,8-5,2 h) auf den 1.500 Stellungen
   (Zuordnung: Partie i -> Stellung i mod 1500, zyklisch -- ergibt bei
   Abbruch die Stall-Regel-freundliche Gleichverteilung).
2. **Kontrollarm: der vorhandene v21-asymN** (gleiches Fenster bis auf
   den Korpus; ein frisches Kontroll-Training entfaellt).
3. **Schwellen: Asym-par.7 uebernommen** (k1-Rate auf k1-aktiven
   Partien >= 30 % Ziel / >= 22 % Signal bei keinem signifikanten
   Siegverlust; 407 Kampagnen-Seeds, Brettwechsel-Pflicht).

**Zuschnitts-Detail zu par.3, VOR dem Bau geaendert:** statt des dort
skizzierten Record-Felds `seeded_from` wird die Zuordnung als
**Log-Zeile** geschrieben (`[seed_position] game_id=... idx=...`),
exakt dem Greif-Zaehler-Praezedenzfall folgend (Record-Schema hat
mehrere Python-Konsumenten; der Seeding-Korpus liegt ohnehin in einem
EIGENEN Ordner, jede Partie dort ist per Konstruktion geseedet -- ein
Per-Step-Feld waere redundant). Die Log-Zeilen werden wie die
Zwangsseiten-Map als Datei neben dem Korpus gesichert.
