<!-- STATUS: OFFEN | Frage: Lernt der Value-Kopf den Spaltenwert, wenn Self-Play von HALBFERTIGEN Spalten-Stellungen aus FREI weiterspielt (Startpositions-Seeding, KataGo-startPoses-Muster) -- also On-Policy-Wertdaten statt erzwungener Trajektorien? | Beleg: Kette v1 durchgemessen: Arena kein k1-Signal, kein Siegverlust (par.4c); Mechanik-Sonde erstes POSITIVES Zustandssignal (p = 0,017, par.4d). **Wiedervorlage registriert als v24-Arm b03 (par.7, 2026-09-03):** 1.500 Stellungen aus der b01-Value-Klasse, k = 4, 6.000 Seeding-Partien als Zusatz-Schwarm, Regel und Werkzeugaenderung festgelegt; laeuft nach der v24-Erzeugung. -->

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
RGSC (+77/+89 Elo). (Agenten-Befunde mit Quellen,
`RESEARCH_plate_intent_external` Report F1/F4: die Startzustandsverteilung
ist dort der belegteste Strukturhebel, und die Off-Policy-Diagnose erklaert
das Asym-Null aus par.14/15 jener Prereg.)

**Rolle im Gesamtplan** (aus dem Statuskopf hierher gezogen 2026-08-28):
dieser Zuschnitt ist der **Primaerarm des Policy-Seiten-Zuschnitts**,
Nutzer-Freigabe der Reihenfolge 2026-08-22. Stellungsquelle ist der
vorhandene Asym-Korpus (par.2).

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
(`evaluations/artifacts/gumbel_scale_calibration_v21.json`, 216 Stellungen @400):
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
`evaluations/artifacts/seed_positions_curation_report.json`. Verteilung: R2
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

**Nachgetragen aus dem Statuskopf (2026-08-28):** der beste Checkpoint
dieses Laufs stammt aus **Epoche 1**.

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
(`evaluations/artifacts/paired_arena_env_asym_nullarm_n.json`, `model =
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
Ausgabe nach `evaluations/artifacts/seedk1_value_sibling_check.json`, damit das
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


## par.5 REIHENFOLGE ENTSCHIEDEN (Nutzer 2026-08-25): erst v22, dann Seeding

Zur Wahl standen: v22 ohne Seeding, Seeding zuerst in den mcts-Pfad bauen,
oder v22 jetzt und Seeding als eigener Arm danach. **Der Nutzer hat den
dritten Weg gewaehlt.**

**Der inhaltliche Grund, nicht nur der terminliche:** das Verdikt aus par.4c
(kein k1-Signal) ist an PLATTENBLINDEM Spiel erhoben -- der Korpus, aus dem
die geseateten Stellungen stammen, und die Netze, die ab dort weiterspielten,
konnten beide keine Spalten. Genau davor warnt die stehende Regel, Zielraten
nicht gegen die Verteilung heutiger Netze zu eichen, wenn deren Verhalten das
Ziel IST. Ein plattenbewusster Korpus ist die Voraussetzung, unter der eine
Wiedervorlage ueberhaupt etwas anderes zeigen kann. Seit dem 2026-08-25 gibt
es einen: der v2-Lehrer erreicht im Self-Play **0,755 volle Spalten** gegen
0,050 (v1), und k1 wird in 55,7 statt 5,1 Prozent der Partien erreicht.

**Was VOR einer Wiederaufnahme gebaut werden muss** (heute nicht vorhanden):
`--seed-positions` ist auf `--mode network` beschraenkt, und das ist kein
blosser Waechter. Der Waechter steht in `self_play.py:772`, aber der
mcts-Einstieg `self_play_games_with_net_labels` kennt den Parameter
`seed_positions_path` gar nicht -- nur `net_self_play_games` hat ihn
(`self_play.py:193` gegen `self_play.py:196`). Ein Lehrer-Korpus ab geseateten
Stellungen ist damit Engine-Arbeit, kein Flag.

**Material liegt bereit:** `data/seed_positions/seed_positions_v1.jsonl`
(22,8 MB, 2026-08-22). Der Dosis-Folgearm (k=6 war die erste Dosis) bleibt
unregistriert und wartet weiter auf einen eigenen Zuschnitt.

**Wiedervorlage-Bedingung:** nach der v22-Kampagne, mit dem dann vorliegenden
plattenbewussten Korpus als Stellungsquelle UND als Vergleichsanker. Der
Vergleich gegen die alten Zahlen aus par.4c ist dann ausdruecklich KEIN
gepaarter Vergleich -- verschiedene Regime, verschiedene Stellungsquelle.

## par.7 WIEDERVORLAGE als v24-Arm `v24-b03`: Kuratierungsregel des Seeding-Schwarms (registriert 2026-09-03, VOR der Erzeugung)

Die Wiedervorlage-Bedingung aus dem unteren par.5 ist erfuellt: es gibt eine
plattenbewusste Linie (`v23-b01`, 0,515 volle Spalten am argmax-Instrument,
Elo 1263), und v24 wird aus ihr erzeugt (`PREREG_v24_window.md` par.6/par.8).
b03 ist der Arm, der das positive Zustandssignal aus par.4d (Tau +0,14 gegen
-0,19, p = 0,017) unter plattenbewussten Bedingungen wiederholt -- diesmal als
ZUSATZ zum Fenster, nicht als eigener Korpus.

**Stellungsquelle (neu, Nutzer-Bedingung "plattenbewusst"):** die Value-Klasse
der v24-Erzeugung selbst, `selfplay_v23-b01-value-argmax_*` (6.000 Partien
b01 @100, argmax, ohne Rauschen; par.6b der v24-Prereg). Nicht der Sockel
(gesampelt) und nicht die alten Asym-Korpora. Damit sind Stellungsquelle und
Weiterspiel-Netz dieselbe Linie; der Vergleich zu par.4c ist ausdruecklich
kein gepaarter (unteres par.5).

**Kandidaten, Auswahl, Umfang** (Regel aus par.2, ohne Zwangsseite):
- Zustand des Spielers AM ZUG (beide Seiten kommen vor), Runde in {2, 3, 4},
  `max(col_fill)` des Spielers am Zug in {3, 4, 5}; Spaltenzaehlung in Python
  mit Pflicht-Gegenprobe gegen `mosaic_rust.plate_completability_json`
  (`--verify 500`, 0 Abweichungen oder Abbruch, wie 2026-08-22).
- Stratifiziert ueber Runde x Fortschritt (9 Straten), hoechstens EINE
  Stellung je Partie, deterministisch mit Seed **20260912**.
- Zielumfang **1.500 Stellungen** wie v1; Kuratierungs-Bericht VOR der
  Erzeugung (Verteilung Runde x Fortschritt x aktive Platten, k1-aktiv-Anteil,
  Restlaenge) als `seed_positions_curation_report_v2.json`, Satz als
  `data/seed_positions/seed_positions_v2.jsonl`.
- Werkzeug: `tools/seed_position_curation.py` bekommt `--korpus-glob` und
  den Modus "Spieler am Zug statt Zwangsseite" (kleine Aenderung, Muster
  bleibt; die Zwangsseiten-Map wird dann nicht gelesen).

**Erzeugung des Seeding-Schwarms:** `self_play.py --mode network --model
models/alphazero_v23-b01_brierbest.onnx --sims 100 --value-only
--seed-positions data/seed_positions/seed_positions_v2.jsonl --per-file 10
--threads 11 --chunk 10 --seed 20260913 --version v23-b01-seedvalue`, mit
`MOSAIC_STACK_DRAW_RESEARCH=1`; **k = 4 Fortsetzungen je Stellung, also
6.000 Partien** (Dosis wie der kleinste Arm aus par.2, Kosten-Herleitung: rund
3,65 s je Partie bei threads 11 wie die v23-Value-Klasse, Restlaenge rund 44
Prozent einer Vollpartie, also grob 3 h). Gesampelt mit Wurzelrauschen, weil
vier Fortsetzungen derselben Stellung sonst identisch waeren. Das
`--value-only`-Flag haelt die Policy-Ziele ungueltig; die Partien sind reiner
Value-Stoff, wie der uebrige Schwarm.

**Fenster b03** = Fenster b01 (par.1 der v24-Prereg, 29.450 Partien) PLUS die
6.000 Seeding-Partien als weitere Value-Klasse (Dateiliste
`data/window_v24_b03.txt`, Traeger-Manifest unveraendert, weil die Klasse
keine Policy traegt). **Einziger Faktor gegen b01: der Zusatz-Schwarm.** Dass
damit auch die Datenmenge steigt, ist Teil des Faktors und wird nicht
getrennt (Dosis-Folgearm bleibt unregistriert).

**Entscheidungsmass:** wie fuer jeden v24-Arm Tor 1 (Arena gegen b01,
Champion-Strenge), Tor 2a/2b (Spalten) und die Generatorwahl-Regel; dazu die
Mechanik-Sonde aus par.4d (Geschwister-Tau des Value-Kopfs auf denselben 33
Stellungen), weil dort das einzige positive Signal herkam. Lesart: hebt b03
die Spalten oder die Siege gegen b01, traegt on-policy Wertstoff aus
halbfertigen Spalten; bewegt sich nur der Tau, ist es wieder "Mechanik
bewegt, Verhalten nicht" (par.4d), und der Dosis-Folgearm wird registriert.

**Reihenfolge:** Kuratierung erst NACH der v24-Erzeugung (die Quelle entsteht
dort), Seeding-Schwarm danach (rund 3 h CPU), b03-Training nach b01 und b02.

**Nachtrag 2026-09-05, 11:05 (gefahren in der Nacht 2026-09-04/05; der
Schreibversuch vom 2026-09-04 23:58 war hinter einem gescheiterten Commit
nicht ausgefuehrt worden, Chronik):** Werkzeug
`tools/seed_position_curation.py --mode am-zug --korpus-glob ... --out-set
... --out-report ...` (Seite = `state.current_player`, im Korpus identisch
mit `record.player`); Kette `tools/night_v24_b03_chain.sh`. **Kuratierung
(06:12-06:27):** Quelle 600 argmax-Dateien, 5.998 Partien mit Kandidat,
`--verify 500` 0 Abweichungen, **1.500 Stellungen**, Seiten 734/766, k1 aktiv
549, Restlaenge im Mittel 0,439 (Median 0,450); Straten r2_p3 184, r2_p4 8,
r2_p5 0, r3_p3 234, r3_p4 246, r3_p5 188, r4_p3 174, r4_p4 212, r4_p5 254
(`seed_positions_curation_report_v2.json`). **Seeding-Schwarm (06:28-08:56):**
6.000 Partien in 8.908,1 s = 1,485 s je Partie bei threads 11
(`manifest_v23-b01-seedvalue_20260905_062758.json`), 600 Dateien
`selfplay_v23-b01-seedvalue_*`. **Abweichung vom Befehl oben, registriert:**
zusaetzlich `MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0`, weil
der Schwarm der vierte Lauf derselben Erzeugung ist und `PREREG_v24_window.md`
par.6b' den Knopf fuer alle Laeufe der Generation setzt; ohne Knopf waere er
ein zweiter Faktor gegen b01. Fenster b03 `data/window_v24_b03.txt` 3.545
Dateien, 600 Bloecke in 300,6 s, Monolith 3.368 Trainingsdateien Schluessel
299283d4df61 in 672,7 s. Training v24-b03 nach b02 (Kette).

## par.8 GEFALTET: Unsicherheits-gefuehrtes Seeding (aus PREREG_uncertainty_guided_selfplay.md, 2026-09-05)

Die Prereg zum unsicherheits-gefuehrten Self-Play ist am 2026-09-05 auf
UEBERHOLT gesetzt und hierher gefaltet (Nutzer-Entscheid). Ihr Kern: statt
kuratierter oder zufaelliger Startstellungen die waehlen, bei denen das Netz
nachweislich unsicher ist UND die Unsicherheit die Zugwahl kippen kann;
Tor G (taugt das Mass?), Stufe 1 als Offline-Warteschlange aus
`root_q`/`root_child_q` (in 65,2 % der Datensaetze vorhanden), Waechter und
Entscheidungsmetrik stehen dort in par.3, 4, 6, 7. **Bedingung fuer die
Wiederaufnahme:** der b03-Befund (par.7) zeigt, dass Seeding Verhalten bewegt
(Tor 1 oder Tor 2 fuer b03, nicht nur der Tau). Traegt b03 nicht, ist auch
die Auswahlregel der Startstellungen kein Hebel, und der Baustein bleibt
gefaltet.

## par.9 VERZWEIGEN (Branching): Machbarkeit am Code geprueft (2026-09-07, 01:50; Nutzer-Auftrag "schau ob branching auch fuer uns baubar waere")

**Woher die Frage kommt.** Nutzer 01:05: das Self-Play zerstoert die Spalten frueh, der
Zufall sollte weniger aus der Temperatur und mehr aus dem Spiel kommen; 01:25 praezisiert:
argmax spielen, dann x Zuege mit Temperatur simulieren, dann wieder argmax -- "so sieht das
Netz beides". Externer Stand (Web-Recherche 2026-09-07, Quelle
[Wu 2019, arXiv:1902.10565](https://arxiv.org/pdf/1902.10565)): **KataGo macht genau das.**
In 5 % der Partien wird nach r Zuegen verzweigt (r exponentiell verteilt), 3 bis 10 Zuege
werden GLEICHVERTEILT gezogen, jeder bekommt EINE Netzbewertung, der beste davon wird
gespielt; ein zufaelliges Viertel dieser Zweige laeuft rekursiv einen Zug weiter. Zweck laut
Paper: ein kleiner Anteil Trainingsdaten darueber, wie man auf Zuege antwortet, die eine
volle Suche nie spielen wuerde. **Unsere eigene Recherche
(`RESEARCH_alphazero_improvements_2026-08-01.md`) hat aus derselben Arbeit die Playout Cap
Randomization als Fund 6 uebernommen (gebaut, A/B negativ), das Verzweigen aber nicht --
das Wort kommt dort nicht vor (geprueft: 0 Treffer).**

**Der wichtige Unterschied zur Temperatur:** KataGo streut BREIT und filtert sofort mit
einer einzelnen Netzbewertung. Es erzwingt keinen erkennbar schlechten Zug, sondern nur
einen ungewoehnlichen. Temperatur-Sampling nimmt dagegen den zweitbesten Zug in Kauf -- und
genau das zerstoert die halbfertige Spalte (Anlass von Messung 3-V,
`PREREG_search_path_remeasurements.md`).

### Baubarkeit: JA, und billiger als `PREREG_uncertainty_guided_selfplay.md` par.5 annimmt

Dort steht, echtes Verzweigen "bricht die heutige lineare Erzeugungsschleife (unabhaengige
Partien auf Kerne verteilt) und braucht eine Warteschlange plus Arbeiter" und sei "der
groesste Engineering-Posten des Zuschnitts". **Am Code geprueft (2026-09-07) stimmt das so
nicht**, weil der Zweig synchron in derselben Rayon-Closure laufen kann:

| Baustein | Stand | Aufwand |
| --- | --- | --- |
| Partie ab beliebigem Zustand starten | **liegt fertig**: `GameLoopConfig.start_state: Option<GameState>` (self_play.rs:1737), Bestandspfad des Seedings, mit b03 abgenommen | 0 |
| Zustand mitten in der Partie klonen | **`GameState` ist `Clone`** (state.rs:45) | 0 |
| Nebenausgabe aus der Schleife heraus | Muster liegt vor: `vorzug_greift: Option<&Cell<[u64;2]>>` (self_play.rs:1730) -- analog `branch_states: Option<&RefCell<Vec<GameState>>>` | klein |
| Zweig spielen und Records anhaengen | in der `play`-Closure von `run_net_self_play` (self_play.rs:2244-2266) NACH der Hauptpartie, gleicher Thread, gleicher abgeleiteter Seed; `game_id` `{prefix}_g{i}_b{j}` | klein |
| Parallelisierung | **unberuehrt** -- `into_par_iter().map(play)` bleibt, der Zweig ist Teil derselben Aufgabe | 0 |

**Geschaetzt (nicht gemessen): 60 bis 100 Zeilen Rust plus zwei Python-Flags und
Manifest-Felder, dazu Tests.** Keine Warteschlange, kein Arbeiter-Pool, kein neuer Prozess.
Der Grund, warum par.5 teurer schaetzte: dort war an ASYNCHRONES Verzweigen gedacht (Zweige
in eine Warteschlange, andere Arbeiter holen sie ab). Synchron im selben Thread ist die
Reihenfolge egal, weil die Partien ohnehin unabhaengig sind.

### Kosten in Rechenzeit

Ein Zweig ist eine Restpartie. Gemessen am Seeding-Schwarm (par.7): Restlaenge rund 44 %
einer Vollpartie bei Verzweigung in Runde 2 bis 4, rund 3,65 s je Partie bei threads 11.
Bei KataGos Rate von 5 % waeren das rund +2 % Wanduhr; bei einem Zweig je Partie rund
+44 %. Die Dosis ist also ein freier Regler, kein Sprung.

### Vier Entscheidungen VOR einem Bau (keine davon getroffen)

1. **Wo verzweigen?** Zufaellig wie KataGo, oder gezielt -- nach Spaltenfortschritt (wie die
   b03-Kuratierung, par.7) oder nach Unsicherheit (gefaltete Prereg, Stufe 1). Der
   Waechter aus `PREREG_uncertainty_guided_selfplay.md` par.6 gilt unveraendert: NUR
   epistemisch auswaehlen, nie auf aleatorische Breite.
2. **Wie abweichen?** KataGo-Form (breit ziehen, mit einer Netzbewertung filtern) oder
   Temperatur-Sampling. Fuer unser Spaltenproblem spricht die KataGo-Form, weil sie den
   offensichtlich schlechten Zug ausschliesst.
3. **Was liefert der Zweig?** Value-only wie der Seeding-Schwarm, oder auch Policy-Ziele.
   Die Zwei-Klassen-Struktur des Fensters (`PREREG_v25_window.md` par.1) legt value-only
   nahe; Policy-Ziele aus Zweigen waeren eine eigene Frage.
4. **Determinismus.** Der Zweig-Seed MUSS aus `partie_seed` abgeleitet werden (Muster
   `PREREG_search_rng_split.md`), sonst ist die Erzeugung nicht mehr reproduzierbar.

### Ein Einwand, der vorab benannt gehoert

**Haupt- und Nebenpartie teilen Wertungsplatten, Startspieler und die halbe Vorgeschichte.**
Die Records eines Zweigs sind damit hoch korreliert mit denen seiner Hauptpartie -- die
Zahl der Records steigt schneller als die Zahl der UNABHAENGIGEN Stichproben. Das ist
dieselbe Falle, die im Projekt fuer Arena-Auswertungen als Block-Korrelation bekannt ist
([[feedback_arena_block_correlation]], `working_rules.md`). Folge fuer jede spaetere
Bewertung: Zweige und ihre Hauptpartie bilden EINEN Block, und Fehlerbalken werden ueber
Bloecke gerechnet, nicht ueber Records. Fuer das TRAINING ist die Korrelation kein Fehler
(mehr Stellungen aus derselben Gegend sind genau der Zweck), fuer jede Messung an diesem
Material schon.

**Stand: nichts gebaut, nichts entschieden.** Die Reihenfolge bleibt: erst Messung 3-V
(was kostet die Temperatur an Spalten und an Vielfalt), dann die Wahl zwischen
"Temperatur senken und gerichtet ersetzen" (Verzweigen, dieser Absatz) und "Temperatur
lassen".

### par.9a PRAEZISIERUNG DES NUTZERS (2026-09-07, 02:20): der Zweig hat ZWEI Phasen

**Nutzer, woertlich:** *"ich spiele argmax zug -> simuliere die naechsten zuege via
temperature (nur fuer die exploration) -> simuliere die naechsten zuege via argmax ->
spiele den naechsten argmax zug. so haette ich es ca. im kopf gehabt."*

par.9 oben hat den Zweig als DURCHGEHEND verrauscht beschrieben. Das war zu grob. Der
Entwurf des Nutzers ist zweiphasig, und der Unterschied ist inhaltlich:

| | Zweig durchgehend Temperatur (par.9 oben) | Zweig zweiphasig (Nutzer) |
| --- | --- | --- |
| Abweichung | ueber die ganze Restpartie | nur die ersten k Zuege |
| Rest der Fortsetzung | gesampelt | argmax |
| Value-Ziel des Zweigs | Wert von SCHLECHTEM Spiel | Wert der abgewichenen Stellung unter GUTEM Spiel |
| Bezug zur Literatur | -- | genau der Punkt von Willemsen/Baier/Kaisers (`RESEARCH_alphazero_improvements_2026-08-01.md` Fund 1): `z` ist durch Explorationszuege im Pfad verzerrt |

**Die zweite Form ist die richtige**, und zwar aus demselben Grund, aus dem die
Zielmischung ueberhaupt gebaut wurde: ein Ergebnis, in dessen Pfad Explorationszuege
liegen, misst nicht den Wert der Stellung. Wird nach der Abweichung sauber ausgespielt,
ist das Ziel wieder die gesuchte Groesse.

**Bausteine: vollstaendig vorhanden, keine neue Mechanik noetig.**
- Zweig ab Stellung: `GameLoopConfig.start_state` (par.3/par.7, mit b03 abgenommen).
- Umschaltpunkt Temperatur -> argmax: `MOSAIC_TAU_ARGMAX_FROM_MOVE` /
  `--tau-argmax-from-move` (net_mcts.rs:2523; zaehlt echte Drafting-Halbzuege, 1-basiert).
  Ein Zweig, der bei Halbzug `m` abzweigt und `tau_argmax_from_move = m + k` bekommt,
  spielt GENAU k Zuege mit Temperatur und danach argmax.
- Saubere Hauptlinie: derselbe Regler auf einen frueher Wert.

**BERICHTIGUNG (Nutzer 02:35): das sind ZWEI WEGE, keine Praezisierung eines einzigen.**
Woertlich: *"das war keine praezisierung, sondern nun haben wir zwei moegliche wege. welche
die sinnvollere ist kann ich schwer abschaetzen."* Die Unterscheidung, und die Abwaegung
des Koordinators dazu, stehen in par.9b unten. Der urspruengliche Absatz bleibt als
Beschreibung von WEG B stehen:

**Weg B (Nutzer 02:30): die Hauptlinie wird gar nicht beruehrt.**
Woertlich: *"meine idee war: Stellung A -> simulation mit temperature (exploration) ->
zurueck zu Stellung A -> simulation via argmax -> Stellung B."* Der Zweig ist also ein
AUSFLUG: von Stellung A wird explorativ simuliert, dann kehrt die Erzeugung nach A zurueck
und spielt von dort mit argmax weiter nach B. Die Hauptpartie bleibt vollstaendig sauber,
der Zweig ist eine zusaetzliche Datenquelle und keine Abzweigung der gespielten Linie.
**BERICHTIGT 02:40 (Nutzer-Frage "ist b nun das katago branching?"): NEIN, und die Aussage
"das entspricht KataGos Seitenpartien genauer" war falsch** -- siehe par.9c, wo Anhang D des
Papers nachgelesen ist. KataGo erzeugt KEINE zweite Trajektorie. An der
Baubarkeit (par.9) aendert Weg B nichts: die dort beschriebene Bauform klont den Zustand und spielt den
Zweig in derselben Rayon-Closure -- die Hauptpartie laeuft davon unberuehrt weiter. Was sich
aendert, ist die Erwartung an die Kosten: der Ausflug kommt ZUSAETZLICH zur vollen
Hauptpartie, waehrend eine Abzweigung sie ersetzt haette.

**Neue Frage, die der zweiphasige Entwurf aufwirft:** liefern die k Temperatur-Zuege selbst
Trainingsdaten, oder nur die argmax-Fortsetzung? Der Nutzer sagt "nur fuer die
exploration" -- dann waeren ihre Records auszuschliessen, und das Material bestuende aus
sauber gespielten Stellungen, die lediglich an einer ungewoehnlichen Stelle beginnen.
KataGo verfaehrt sinngemaess so (die zufaellig gewaehlten Zuege werden gespielt, die
Trainingsdaten kommen aus dem, was folgt). **Offen, vor einem Bau zu entscheiden**, zusammen
mit k (Zahl der Temperatur-Zuege), der Verzweigungsrate und der Frage aus par.9 Punkt 3
(value-only oder policy-tragend).

### par.9b ZWEI WEGE, und welcher zuerst (Koordinator-Abwaegung 2026-09-07, 02:35, auf Nutzer-Frage "welche die sinnvollere ist kann ich schwer abschaetzen. dafuer hab ich dich")

| | **Weg A: eine Linie, phasenweise verrauscht** | **Weg B: Ausflug, Hauptlinie sauber** |
| --- | --- | --- |
| Trajektorien je Partie | eine | zwei (Hauptpartie + Ausflug) |
| Wo die Streuung sitzt | ausschliesslich in den ersten k Halbzuegen | an frei waehlbarer Stelle, auch spaet |
| Zusatzkosten | **keine** (die Partie laeuft ohnehin) | eine Restpartie je Ausflug (5 % Rate ~ +2 % Wanduhr) |
| Mechanik | `--tau-argmax-from-move k` -- **fertig, im Wheel** | `start_state` + Klon in der Erzeugungs-Closure -- **zu bauen** (par.9) |
| Stand | **GEMESSEN 2026-09-07 (Messung 3-V):** k=11 verdoppelt die Spalten (0,4225 gegen 0,1950) bei unveraenderter Vielfalt | b03 hat die OFFLINE-Fassung gefahren (par.7): hoechster Kuppel-Bonus der Generation (4,2 gegen 3,5-3,6) |
| Literatur | AlphaZero-Standard (erste 30 Halbzuege sampeln, dann greedy) | KataGo-Seitenpartien (Wu 2019, 5 % der Partien) |

**Empfehlung: A sofort, B als naechster Bau.** Begruendung:

1. **A ist gemessen, kostenlos und repariert den Betriebspunkt.** Der Regler liegt im Wheel,
   die Messung liegt vor, und der Effekt ist gross (mehr als eine Verdopplung der Spalten
   im Sockel). Es gibt keinen Grund, darauf zu warten.
2. **A hat aber eine strukturelle Grenze, und sie liegt genau dort, wo der Engpass der
   Kampagne sitzt.** Seine Streuung endet nach k Halbzuegen; alles danach ist die
   Konvergenz des Generators auf sein eigenes Optimum. Der Strukturbefund lautet aber
   **Engpass VOLLENDUNG SPAET** ([[project_column_completion_structural_weakness]]) -- der
   Value-Kopf braucht Stellungen aus den spaeten Runden mit halbfertigen Spalten, und die
   erzeugt A nur zufaellig, nicht gezielt.
3. **B ist der einzige Weg, gezielt dorthin zu kommen** -- und die Kampagne hat dafuer
   bereits einen positiven Datenpunkt: der Seeding-Schwarm b03 (par.7) hat genau das
   offline gemacht (Stellungen aus R2-4 mit Spaltenfortschritt 3-5, von dort weiterspielen)
   und den hoechsten Kuppel-Bonus aller sechs v24-Arme erzeugt.

**Was die Empfehlung kippen wuerde:** wenn A in der ARENA Staerke kostet. Dann waere die
Vielfalt aus dem Partieanfang nicht ersetzbar durch "einfach weniger sampeln", und B wuerde
von der Kuer zur Pflicht, weil die Streuung dann anderswo herkommen muss. Die alte
Messung 3 (2026-08-08, Umschaltpunkt 30) war auf Staerke H0 -- sie kannte den hier besseren
Punkt 12 aber nicht. **Die Arena-Frage zu A ist damit der naechste Entscheid, nicht die
Wahl zwischen A und B.**

### par.9c WAS KATAGO WIRKLICH MACHT -- am Paper nachgelesen (2026-09-07, 02:40; Anhang D, ar5iv-Fassung von arXiv:1902.10565)

**Anlass:** Nutzer-Frage *"ist b nun das katago branching?"* Der Koordinator hatte in par.9a
behauptet, Weg B entspreche KataGos Seitenpartien. **Das ist falsch.** Der Wortlaut aus
Anhang D:

> "In 5% of games, the game is branched after the first r turns where r is drawn from an
> exponential distribution with mean 0.025*b^2. Between 3 and 10 moves are chosen uniformly
> at random, each given a single neural net evaluation, and the best one is played."

und danach: *"the game is then played to completion as normal"*. Ausgewertet:

1. **EINE Trajektorie, keine Nebenpartie.** Der abweichende Zug ERSETZT den, den die Suche
   gespielt haette; die Partie laeuft von dort normal weiter. KataGos "branch" ist eine
   Abweichung IN der Partie, kein Ausflug daneben.
2. **Genau EIN Zug weicht ab** (rekursiv wird bei einem zufaelligen Viertel ein weiterer
   angehaengt), nicht k Zuege.
3. **Die Abweichung ist nicht Temperatur:** 3 bis 10 Zuege werden GLEICHVERTEILT gezogen,
   jeder bekommt EINE Netzbewertung, der BESTE davon wird gespielt. Breit ziehen, billig
   filtern -- kein offensichtlich schlechter Zug.
4. **Die Stelle ist zufaellig, exponentiell verteilt** -- meist frueh, mit langem Schwanz
   bis in die spaete Partie.
5. **Policy UND Value:** an der Stelle wird eine volle Suche gefahren, die ein
   Policy-Trainingsziel liefert; Value-/Score-/Ownership-Ziele entstehen normal.

**Damit sind es DREI Wege, nicht zwei:**

| | Trajektorien | Wo abgewichen wird | Wie | Wie lang | Zusatzkosten | Stand bei uns |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | eine | nur Partieanfang | Temperatur (Besuchsverteilung) | k Zuege | keine | **gemessen** (Messung 3-V: Spalten verdoppelt) |
| **B** (Nutzer) | zwei | frei waehlbar | Temperatur | k Zuege | eine Restpartie je Ausflug | Mechanik da (par.7/9), Auswahlregel offen |
| **C** (KataGo) | eine | zufaellige Stelle, exponentiell | breit ziehen, EINE Netzbewertung filtert | ein Zug | keine | nicht gebaut |

**Geaenderte Empfehlung (ersetzt par.9b Punkt 3 der Reihenfolge, nicht seine Begruendung):
A, dann C, dann B.**
- **A zuerst**: gemessen, gratis, repariert den Betriebspunkt.
- **C vor B**: C kostet ebenfalls NICHTS (eine Linie) und schliesst genau die Luecke von A --
  Streuung auch in SPAETEN Stellungen, weil die Abweichungsstelle exponentiell verteilt ist
  statt auf den Anfang beschraenkt. Dazu vermeidet die Filterung per Netzbewertung den
  offensichtlich schlechten Zug, der bei uns die Spalte zerstoert (Messung 3-V).
- **B danach**: sein Alleinstellungsmerkmal ist das ZIELEN (Stelle waehlbar, z.B. nach
  Unsicherheit oder Spaltenfortschritt). Das ist teurer und lohnt erst, wenn zufaelliges
  Streuen nachweislich nicht reicht.

**Baukosten C (geschaetzt, nicht gemessen):** in der Draft-Phase der Erzeugungsschleife mit
Wahrscheinlichkeit p an Halbzug r: n Kandidaten aus `valid_drafting_actions` ziehen, je EINE
Netzbewertung (die Engine hat den Vorwaertspass ohnehin), den besten spielen statt des
Suchergebnisses. Rund 40 Zeilen in `unified_game_loop`, zwei Flags, ein Manifest-Feld.
Deutlich weniger als B, weil weder Zustands-Klon noch zweite Partie noetig sind.

### par.9d KATAGOS TEMPERATUR-POLITIK -- und ein vierter Kandidat (2026-09-07, 03:15; Nutzer-Frage "hat katago das auch wie arm 3 gemacht oder hast dir das selbst hergeleitet?")

**Ehrliche Zuordnung zuerst: hergeleitet.** Arm 3 (Umschaltpunkt PLUS Weg C) entstand aus der
Mechanik -- C ersetzt genau einen Zug und kann deshalb nur zusaetzlich zu A wirken, nicht
statt A. Die Nutzer-Frage hat die Gegenprobe ausgeloest; sie faellt zugunsten der
Herleitung aus, deckt aber einen Unterschied auf.

**Nachgelesen (ar5iv-Fassung von arXiv:1902.10565):**
- **KataGo fuehrt beides gleichzeitig:** die abklingende Temperatur laeuft in ALLEN Partien,
  das Verzweigen (Anhang D) kommt in 5 % davon zusaetzlich dazu. Arm 3 entspricht damit der
  Praxis.
- **Die Temperatur-Politik ist aber eine ANDERE als unsere.** Wortlaut: *"moves are selected
  proportionally to the target-pruned MCTS playout distribution raised to the power of 1/T
  where T is a temperature constant. T begins at 0.8 and decays smoothly to 0.2, with a
  halflife in turns equal to the width of the board b."*

| | KataGo | unser Regler `--tau-argmax-from-move` |
| --- | --- | --- |
| Form | glatt abklingend | harter Schalter |
| Startwert | T = 0,8 (bereits geschaerft) | T = 1,0 (ungeschaerfte Besuchsverteilung) |
| Endwert | **T = 0,2 -- nie null, es wird bis zum Schluss gesampelt** | **argmax, also T = 0** |
| Zeitskala | Halbwertszeit = Brettbreite (19 von rund 230 Zuegen, also rund 8 %) | fester Halbzug k |

**Auf unsere Partielaenge umgerechnet:** 8 % von 162 Drafting-Halbzuegen sind rund 13 -- die
Halbwertszeit liegt also nahe an dem Umschaltpunkt, der bei uns am besten gemessen hat (12,
Messung 3-V).

**Vierter Kandidat (Weg D): glatt abklingende Temperatur statt hartem Schalter.** Sie hebt
die Schaerfe frueh an, ohne die Streuung je ganz abzuschalten. Das ist genau die Antwort auf
den Nutzer-Einwand vom 03:05 ("und der value head braucht keine streuung?"): Messung 3-V
zeigt, dass WENIGER Sampling mehr Spalten bringt -- sie zeigt NICHT, dass GAR KEIN Sampling
das Optimum ist. Der noch fehlende Punkt bei k = 1 wuerde das auch nicht klaeren, weil er die
harte Form behaelt.

**Bau (geschaetzt, nicht gemessen):** `drafting_policy` (self_play.rs) bekommt `play_temp`
bereits als Parameter -- heute ein fester Wert. Ein Env-Knopf mit Start-, End- und
Halbwertszeit-Wert, der `play_temp` je Halbzug berechnet, ist kleiner als Weg C: keine
Kandidatenziehung, keine Netzbewertung, nur eine Formel vor einem bestehenden Aufruf.
Default = Bestandswert, damit bitidentisch.

**Nicht entschieden, und bewusst NICHT in die v25-Armstruktur genommen** -- drei Arme
messen bereits zwei Faktoren; ein vierter Arm braucht einen eigenen Entscheid.
