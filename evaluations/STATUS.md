# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom
2026-08-31 (Nutzer-Auftrag); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom
2026-08-31 (vor der Neufassung)"** -- dort steht jede Herleitung, die hier
nur noch als Verweis vorkommt, inklusive der kompletten v22-Chronologie
(Faecher-Durchgang, Schlachtplan v22->v23, Nachtprogramme, abgeloeste
Tor-Fassungen).

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

**Zahlen ohne Datum stammen aus dem Stand vom 2026-08-30 und sind in dieser
Neufassung nicht neu nachgemessen worden.**

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern kanonisch in
`../docs/`: `generation_loop.md` (die Schleife und ihre Tore),
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`,
`pitfalls.md`, `measured_runtimes.md`, `architecture_reference.md`. Wer an
diesen Inhalten etwas aendert, aendert es DORT.

---

## 1. WAS GERADE LAEUFT (UEBERGABE 2026-09-06, 00:36; Anlass: Kontextfenster der Sitzung vom 2026-09-05 zu 75 % voll)

**Champion:** `v23-b01_k3p10` (Elo 1292). **Generation v24 in der Abnahme, fuenf
Arme:** b01, b02, b04, b05 trainiert; b03 (714er-Arm) trainiert gerade neu
(Verlust durch Maschinen-Neustart 2026-09-05 16:04). Alle Zahlen:
`PREREG_v24_window.md` par.9/9a/9b; Chronik `night_run_20260902.md` (ab
Eintrag 16:04 des 2026-09-05 ist alles von der uebergebenden Sitzung).

**Stand der Arme (Kurzform, Details par.9):**
- v24-b01: Tor 1 mit Knopf gerissen (83:107), ohne Knopf 216:184 (kein
  Entscheid); Tor 2a mit Knopf 0,443, ohne 0,518; Tor 2b gehalten (93:67).
  Knopf-Dosis C 0,5 = 0,450: Schalter, kein Regler (par.9b).
- v24-b02 (lambda 0,7): Tor 1 ohne Knopf 209:161 (SPRT), mit Knopf 101:69 und
  91:59 (zwei Seeds, Champion-Strenge); Tor 2a mit Knopf 0,525 (Bezug 0,555,
  KI schliesst ein), ohne 0,430 gerissen; Tor 2b gerissen (Siege 87:73, aber
  Spalten 0,550/0,475 gegen 0,688/0,562). Staerker, spaltenaermer.
- v24-b04 (Sicht 744): Tor 2a ohne Knopf 0,4125 (gerissen), mit Knopf 0,5325;
  Tor 1 ohne Knopf 218:182 (kein Entscheid); Tor 1 MIT Knopf 135:135 (H0) und Replikation
  221:179 (kein SPRT-Entscheid, p 0,046), gepoolt 356:314 -- Ratsche nicht genommen;
  Tor 2b GEHALTEN (92:68, Spalten 0,684/0,738 gegen 0,608/0,525, Kuppel-Bonus 3,9/4,3
  gegen 3,6/3,9). Abnahme komplett 03:04.
- v24-b05 (b04 plus Ueberraschungsgewichtung): trainiert (brierbest Epoche 4,
  0,1925); Abnahme laeuft seit 03:08. Tor 2a ohne Knopf 0,4825 (Bezug 0,510, KI
  schliesst ein; b04 0,4125); **Tor 1 ohne Knopf 66:34 nach 50 Paaren, SPRT fuer b05**
  (p 0,004) und Replikation 112:78 (p 0,021), gepoolt 178:112, Champion-Strenge ohne
  Knopf erfuellt (09:58); Tor 2a mit Knopf 0,4975
  (Bezug 0,555, KI schliesst ein; Knopf hebt nur +0,015); Tor 1 mit Knopf 219:181 (kein
  SPRT-Entscheid, p 0,067); Tor 2b GEHALTEN (98:62, Spalten 0,650/0,557 gegen 0,500/0,570).
  Abnahme komplett 05:54 -- einziger Arm mit Tor 1 (ohne Knopf) UND Tor 2b.
- v24-b03 (Seeding-Schwarm, 714): trainiert 00:27-01:56 mit `--fast-loader` (5.344 s,
  `_brierbest` Epoche 4, 0,1868); Abnahme laeuft seit 05:55. Tor 2a ohne Knopf 0,490
  (Bezug 0,510, KI schliesst ein); Tor 1 ohne Knopf 215:185 (kein Entscheid, p 0,155);
  Tor 2a mit Knopf 0,5025 (Bezug 0,555, KI schliesst ein); **Tor 1 MIT Knopf 75:45 nach 60
  Paaren, SPRT fuer b03** (p 0,008) und Replikation 139:101 (p 0,016), gepoolt 214:146 --
  Champion-Strenge mit Knopf erfuellt. Tor 2b: 83:77, Spalten 0,675/0,628 gegen 0,575/0,692
  (gleichauf), Kuppel-Bonus 4,2 gegen 3,5-3,6. Abnahme komplett 09:20. **ALLE FUENF ARME
  ABGENOMMEN.**

**LAEUFT (Hintergrundaufgaben der alten Sitzung; laufen als eigene Prozesse
weiter, auch wenn die Sitzung endet -- ausser dem nackten Training, siehe
`pitfalls.md` "Harness-Stopp"):**

| Lauf | Werkzeug | Start | Stand 00:36 | erwartetes Ende | liest | Artefakte |
| --- | --- | --- | --- | --- | --- | --- |
| ~~Training v24-b03 (714, fast-loader)~~ | `tools/night_v24_b03_fast.sh` | 00:27 | **FERTIG 01:56** (5.344 s, `_brierbest` Epoche 4 0,1868; config.py wieder 744, `git diff config.py` leer; Manifest mit Lader-Nachtrag committet) | -- | `data/window_v24_b03.txt`, Monolith `.cache_299283d4df61.h5`, config.py mit INPUT_SIZE 714 | `models/alphazero_v24-b03*.onnx`, Manifest `manifest_train_v24-b03_20260906_002718.json`; **setzt config.py am Ende auf 744 zurueck** |
| ~~Abnahme b04~~ | `tools/night_v24_b04_acceptance_744venv.sh` (venv_measure744, 744er-Wheel) | 21:49 | **FERTIG 03:04**, alle Tore in par.9 registriert | rund 02:30 | `models/alphazero_v24-b04_brierbest.onnx`, Champion-Spec, `k3v_off.spec.json` | `tor2a_v24b04*.json`, `paired_gating_result_v24-b04_*`, `paired_arena_env_v24b04_*`, `columns_v24b04_*`, `points_v24b04_vs_b01_s14.json` |
| ~~Tiling-Geometrie-Sonde~~ | `tools/cpu_queue_after_b04.sh` | 22:31 | **FERTIG 03:07** (9,8 s + 70 s), registriert par.8.12a / 8.14 | rund 02:45 | `static/log/game_*.log`, `paired_arena_env_v24b01_vs_b01_*_s14.json` | `tiling_geometry_probe_human.json`, `tiling_geometry_probe_arena.json` |
| ~~Abnahme b05~~ | `tools/night_v24_b05_acceptance_wait.sh` | 00:24 | **FERTIG 05:54** (03:08-05:54), alle Tore in par.9 | -- | `models/alphazero_v24-b05_brierbest.onnx` | `tor2a_v24b05*.json`, `paired_gating_result_v24-b05_*`, `paired_arena_env_v24b05_*`, `points_v24b05_vs_b01_s14.json` |
| **Champion-Kante b05 (A)** | `tools/champion_edge_b05.sh` | 11:48 | **FERTIG 13:20**: 58:72 (H0) und 144:146 (H0), gepoolt 202:218 -- b05 gleichauf mit dem Champion, kein Kandidat; beide Kanten im Register | rund 2 x 70 min, bis rund 14:30 | `models/alphazero_v24-b05_brierbest.onnx`, beide Specs | `paired_gating_result_v24-b05nk_vs_v23-b01_k3p10_s12.json`, `_s13.json` |
| **Training v24-b06 (B)** | `tools/night_v24_b06_chain.sh` (nacktes train.py darin) | 11:48 | **Training FERTIG 13:07** (4.845 s, `_brierbest` Epoche 4, 0,1926); Kette wartet auf das Ende von A und faehrt dann `night_v24_acceptance_chain.sh b06` plus Kuppel-Bonus | Abnahme rund 3 h nach A (Start rund 13:30, Ende rund 16:30) | `data/window_v24.txt`, Monolith `.cache_85a75d76dfab.h5` | `models/alphazero_v24-b06*`, `manifest_train_v24-b06_*`, `tor2a_v24b06*`, `paired_gating_result_v24-b06_*`, `paired_arena_env_v24b06_*`, `points_v24b06_vs_b01_s14.json` |
| Abnahme b03 (714) | `tools/night_v24_b03_acceptance_714.sh` (venv_measure714, Champion-Artefakt-Wheel, byte-identisch zum alten Live-Wheel) | 20:58 (wartet) | **FERTIG 09:20** (05:55-09:20, 3 h 25 min); Wartemuster kannte Sonde, `cpu_queue_after_b04` und b05-Wartelauf NICHT -- deshalb hielt `tools/night_v24_after_b05_chain_hold.sh` (seit 00:53, Prozess nur wartend) es fest, bis Sonde und b05-Abnahme durch sind (Chronik 00:53) | Start rund 06:45, Ende rund 10:45 | `models/alphazero_v24-b03_brierbest.onnx` | `tor2a_v24b03*.json`, `paired_gating_result_v24-b03_*`, `paired_arena_env_v24b03_*`, `points_v24b03_vs_b01_s14.json` |

**Baum:** gepusht 2026-09-06 10:12 (origin/main = bc4f1b1, Nutzer); danach nur die Hook-Kuratierung offen.
`config.py` steht seit 01:56 wieder auf 744 (`git diff config.py` leer; das b03-Training hat es
selbst zurueckgesetzt). Die GPU ist frei.
Wheel 744 (Kontrakt `20b442a8164f748d`, mit K3-P2, Default aus) ist in der Basis installiert;
Anker-Drift darunter GRUEN (2026-09-05 21:45). Mess-venvs: `venv_measure714/`, `venv_measure744/`
(gitignored).

### ERSTE AUFGABE DER NEUEN SITZUNG

**Nutzer-Freigaben und Verbote, woertlich:** 2026-09-03 *"mach im programm
selbststaendig weiter, ausser der fenster erzeugung"*; 2026-09-05 *"kein Push"*
(steht seit Tagen); Loeschungen nur auf pfadgenaue Freigabe; die v25-ERZEUGUNG
startet NUR auf ausdrueckliche Nutzer-Anweisung; b03 bleibt 714 (*"lass b03 auf
714"*); Bash-Ausgaben knapp (head/tail/grep, Read mit offset), lange Laeufe
ohne Pipe; Uhrzeiten ABLESEN (`date`), nicht fortschreiben (zweimal falsch am
2026-09-05).

1. **WATCHER auf die fuenf Laeufe oben** (nicht neu starten, sie laufen!):
   Prozessliste pruefen (`Get-CimInstance Win32_Process`, Muster `train.py`,
   `night_v24_`, `cpu_queue_`, `paired_`), nicht die Task-Meldungen. Bei
   Stillstand > 30 min ohne neue Artefakt-Datei: Chronik-Eintrag, Nutzer
   fragen. **Ergebnisse SOFORT registrieren** (Lehre 2026-09-05): je Tor in
   die par.9-Tabelle (`PREREG_v24_window.md`), Tor-1-Kanten ins Elo-Register
   (`tools/elo_tracker.py add`, Knopf = eigener Knoten `v24-bXX_k3p10` gegen
   `v23-b01_k3p10`, ohne Knopf `v24-bXX` gegen `v23-b01_brierbest`, Knoepfe
   per `--knobs "spec:..."`), Kuppel-Bonus aus `points_v24bXX_vs_b01_s14.json`.
2. ~~b03-Training beobachten~~ ERLEDIGT 01:56: 5.344 s, rund 440 s je Epoche
   (`measured_runtimes.md`), config zurueck auf 744, Manifest committet.
3. ~~Tiling-Geometrie-Sonde auswerten~~ **REGISTRIERT 03:12** (`geometric_envelope`
   par.8.12a: Mensch laesst Punkte liegen, kauft an G4/Gline aber keine
   Nachbarschaft; par.8.14: Reihe 6 bei den Netzen in 57-58 % der Episoden
   blockiert, blockierte 6er werden zu 15 % voll gegen 48-65 %, Aussen-Legen
   an 61-73 % der blockierten Rundenenden moeglich). Offen: Klassifikation
   Chip-Vollendung/Raeumung (Rest 35-56 %), Sonden-Fassung 2 im naechsten
   CPU-freien Fenster (80 s). Alter Text: Ergebnis in `PREREG_geometric_envelope.md` par.8.12
   (Mensch gegen KI gegen Loeser: Anteil punkt-bester Abschluss, Punktkosten
   und Nachbarschaftsgewinn des geometrie-besten). **Die Sonde ist am
   2026-09-06 00:58 um das Reihen-Alter ERGAENZT** (par.8.13/8.14: Praedikat
   ja / ja_wartend / nein je gebundener Reihe 5/6 und Rundenende, Episoden mit
   Alter, voll oder am Ende offen, Aussen-Legen moeglich; additiv in
   try/except, synthetisch getestet, kein Engine-Lauf) -- der eingereihte Lauf
   (`cpu_queue_after_b04.sh`) faehrt sie mit; Block `reihen_alter` im selben
   Artefakt. Beide Teile auswerten und in par.8.12 UND par.8.14 registrieren;
   DANN K3-F bauen (Nutzer 00:50).
4. ~~Mini-Fenster-Test Fall D (Pause)~~ **GRUEN 02:00** (alle Faelle A-E
   bitgleich, `working_rules.md`). Offen beim Nutzer: `--fast-loader` als
   Default (Volllauf b03: 440 s je Epoche gegen 16 min, bitgleich).
5. ~~Vorlage Generatorwahl~~ **GESTELLT 09:24** (`PREREG_v24_window.md` par.9c):
   Gabelung an der Knopf-Frage -- Erzeugung MIT K3-P: b03 (214:146 mit Knopf,
   Spalten gleichauf, Kuppel-Bonus 4,2); OHNE K3-P: b05 (66:34, zweiter Seed
   laeuft, Tor 2b gehalten). b02 staerkster Beleg, aber spaltenaermer. **Nutzer 09:40:
   "744er bleibt fix drinnen"** -- Kandidaten damit b04/b05; Records tragen die 744er-
   Schluessel (geprueft, par.9c). **Nutzer 11:40: Generator v25 = b05, Erzeugung OHNE
   K3-P** (v25 par.4). **Nutzer 11:48: "self plays eigentlich nur mit champion" -> A: Champion-Kante
   b05 in Spielkonfiguration: 202:218 gepoolt, GLEICHAUF, kein Champion-Beleg (13:20); B: v24-b06
   (b02-Rezept auf 744) trainiert, Abnahme laeuft seit 13:22: Tor 2a ohne Knopf 0,475; Tor 1 ohne Knopf 216:184 ohne Entscheid; Tor 2a mit Knopf 0,4975 (15:25); Tor 1 mit Knopf laeuft.** Erzeugung startet NUR auf
   Anweisung, nach dem Champion-Entscheid.
6. **Danach VORLAGE v25-Zuschnitt** (`PREREG_v25_window.md` par.9/9a): Traeger-
   Kennzahl v24 0,356 gegen Fenster 0,624; v25 nach par.1 rechnerisch 0,23.
   Hebel: Sockel-Betriebspunkt (Pilot: 400 Sockel-Partien in 2-3 Rausch-
   Einstellungen, rund 2-3 h CPU, NUR mit Nutzer-Freigabe, es ist Erzeugung
   im Kleinen), Traeger-Anteile, argmax policy-tragend. Value-Klasse 8.000/0
   bleibt OFFEN (Nutzer nicht ueberzeugt).
7. **Such-Knoepfe am v24-Siegernetz, Reihenfolge K3-P2, K4, Variante B**
   (`geometric_envelope` par.8.11/8.13/8.14, `round_estimate_leaf_term`
   par.4/5, `round_transition_search_sampling` par.7): K3-P2 ist gebaut und
   im Wheel (Spec `models/k3p2_c10.spec.json`); vor dem Verdikt die Zahl der
   offenen langen Reihen mit gegen ohne Knopf (par.8.13). K4-Skala gemessen
   (P90 3/8/10/12 je Runde; Entscheid je Runde oder eine offen). **K3-F
   (par.8.14) als Code GEBAUT 03:25 nach der Reihen-Alter-Messung** (Nutzer
   00:50: "bau k3 f nach der messung"). **10:06: cargo test GRUEN (523), Wheel
   gebaut und installiert, Specs tragen `envelope_flush_w: 0.0`, Anker-Drift und
   Konservierung GRUEN** (par.8.14). Offen: Messung K3-P2 / K3-F / beide am
   Siegernetz (Dosis-Vorschlag w_flush 1,0 und 0,5, Nutzer-Entscheid), Spec
   `models/k3f_*.spec.json` dafuer noch anzulegen.
   Vorher par.12b Rauschboden messen (Block-Bootstrap auf frozen_v3), sonst
   nur Tor 1/2.

**Test- und Hook-Audit (Subagent Opus, 2026-09-06 10:23, Befunde nachgeprueft) -- vom Nutzer
entschieden und UMGESETZT (11:05, cargo test 523 gruen, 16 Python-Tests gruen):** (a) Regel-5-
Fehlalarm: Cargo-Feature `plate_shaping`, `PLATE_SHAPING_ENABLED = cfg!(feature)`, Paritaetstest
per `#[cfg(not(feature))]` statt Laufzeit-Skip; (b) fuenf ignore-Tests auf
`test_champion_model_path()` umgezogen; (c) train.py: neun Schluessel in `_cli_args` nachgetragen
(acht Verhaltens-Flags plus `epoch_checkpoint`), Test `tools/tests/test_train_manifest_flags.py`;
(d) `tools/tests/test_tiling_geometry_probe.py`, `test_spec_add_field.py`, pre-commit faehrt
`unittest discover tools/tests`; (e) `tools/parity_probe.py` geloescht (Freigabe 10:30). Vorher
bereits: Groessen-Basislinie nachgezogen, Regel 8 (lebende Specs gegen KNOWN_FIELDS),
`tools/hooks/python_dll_path.sh`. Das installierte Wheel (10:06) bleibt gueltig: die
Rust-Aenderungen betreffen Tests und einen const-Ausdruck mit demselben Wert (false).

8. **Spiel-Interface Claude gegen Netz** (`PREREG_claude_play_interface.md`, Nutzer-
   Auftrag 12:30): `tools/claude_play.py` gebaut 13:12, Entscheide par.8 komplett
   (10 Partien 5/5, Champion @400, Tiling selbst, keine Uebereinstimmungsmessung,
   Weg 2 Rueckfall, Werkzeug bleibt). Offen: Rauchtest gegen Heuristik im
   CPU-freien Fenster, dann die erste Partie; Protokoll je Partie in par.7.

9. **Netzauslastung** (13:35): Kapazitaetscheck fuer 2D-Netze nachgeruestet
   (`Mosaic2DNet.analyze_capacity`, train.py, `tools/probes/net_capacity_probe.py`);
   b05 GRUEN (Dead 2 %, Eff.Rank 61 %), identisch mit v23-b01/b03/b04/b06 samt
   denselben 42 toten fusion2-Einheiten: Warmstart-Linie, Trunk bewegt sich kaum.

10. **Knopf-Messkette am Champion** (`tools/night_k3_knobs_champion.sh`, gestartet 13:33,
    wartet hinter b06): Rauschboden par.12b Punkte 1-2, dann K3-P2, K3-F 1,0, K3-F 0,5,
    beide; rund 3,7 h ab rund 16:30. Registrierung par.8.11 / 8.14 / 12b je Arm.

**Offene Nutzer-Entscheide (Fundstellen):** K4-Skala je Runde oder gemeinsam
(`round_estimate_leaf_term` par.4); ~~K3-F jetzt bauen oder nach Messung~~ ENTSCHIEDEN 2026-09-06 00:50: nach der Messung
(`geometric_envelope` par.8.14); par.12a/12b Messgroessen und Rauschboden
(`geometric_envelope`); v25 Value-Klasse 8.000/0 (`v25_window` par.9/9a);
`--fast-loader` als Default; Push.

**Blockaden:** Anker ROT, Kettenfehler, unerwarteter Manifest-Diff, zweite
CPU-Last neben einer Messung -> anhalten, Zustand sichern, Nutzer fragen.
Nach jedem Schritt Chronik (`night_run_20260902.md` fortschreiben oder
`night_run_20260906.md` anlegen), STATUS Abschnitt 1 nachziehen, committen
(deutsch, Warum in der Beschreibung, Co-Authored-By: Claude Fable 5.1
<noreply@anthropic.com>). Skills: `/mosaic-measurement-run`, `/mosaic-prereg`,
`/mosaic-anchor-invariance`, `/mosaic-generation-turnover` (vor v25-Self-Play),
`/mosaic-handover`.

### Was seit der Uebergabe von 2026-09-03 09:00 passiert ist (Kurzform; Chronik ab 09:08)

Relabel durch, b07 trainiert und abgenommen (par.A5: keine Staerke, weniger
Spalten, b01 bleibt Generator). K1 gebaut, gemessen, repliziert, Champion-
Kante: ENTSCHIEDEN, kein Rezept (par.15-17). K3 Raster-Form wirkungslos
(par.9); Nutzer: "die Huelle wird kommen, Hebel gesucht"; K3-P (projiziertes
Brett) gebaut, traegt (8.7a-d: gepoolt 191:129, Betriebspunkt @100 0,775
gegen 0,726 Spalten); Huellen-Bauer als Uebersteuerung unbrauchbar (8.8);
8.6 Value im Tiling Nullbefund (8.6a); K3-R/K3-O gebaut und gemessen (8.9a,
Konstruktionsfehler 8.9b als v24-Wiedervorlage). Material-Pilot (v24 par.7):
Tor 0 vorab belegt. Champion-Kante K3-P 38:12 und 221:179 -> Promotion
v23-b01_k3p10 (par.11, Elo 1292). Aufraeumen (Chronik 19:45). Alle Zahlen in
den Preregs und der Tabelle in Abschnitt 1 der Uebergabe von 07:00 (Chronik).

### Stand der v24-Vorbereitung (vollstaendig registriert)

`PREREG_v24_window.md` par.6 (Rezept) und par.8 (Arme b01/b02/b03, Knoepfe
K1/K3; K2 gegenstandslos), `generation_loop.md` (Gleichstandsregel),
`start_position_seeding` par.7 (b03-Kuratierung), `saturating_score_utility`
par.14 (K1 baureif), `geometric_envelope` par.8 (K3 baureif, 8.6 offen).
Index: 18 OFFEN, 79 ENTSCHIEDEN, 8 UEBERHOLT. Chronik der letzten Naechte:
`night_run_20260901.md`, `night_run_20260902.md`.


### Was die Nacht 2026-09-01/02 ergeben hat (Chronik: `night_run_20260901.md`)

1. **Relabel-Arm b05 auf 240 Paaren: Nullbefund.** 246:234 fuer b05, p = 0,65,
   der dritte Seed dreht um; Spalten 0,676 gegen 0,642, KI schliesst Null ein.
   Weder Gewinn noch Schaden. **b01 bleibt Generator fuer v24**, jetzt per
   Nullbefund statt per nachtraeglicher Gleichstandsregel
   (`reanalyze_label_depth` par.A3).
2. **Kaltstart ist die Ursache, nicht das Lernraten-Rezept.** `v23-b06`
   (Kaltstart mit exakt dem b01-Rezept) baut 0,18 volle Spalten und verliert
   65:95 gegen b01 (p = 0,024). "Spaltenwissen sitzt in der LINIE" ist damit
   einfaktoriell belegt (`capacity_sim_frontier` par.14b).
3. **Stufe 4 komplett.** Teil A auf 200 distinkten Zustaenden (0,825 gegen
   0,490 Verwerfung, 70:3); Teil B: die tiefere Suche verwirft
   spaltenrelevante Vorschlaege im GLEICHEN Anteil wie alle anderen, nur
   doppelt so oft insgesamt -- Spaltenverlust als Nebenwirkung, kein gezieltes
   Verwerfen (`search_depth_column_optimum` par.7, ENTSCHIEDEN).
4. **Spreizung des Value-Kopfs im Tiling gemessen:** b01 0,048/0,065 gegen
   plattenblind 0,018, aber die multiplikative Form kippt in 1 von 142 bzw. 4
   von 192 Stellungen einen Punktvorsprung. Form A tot, B oder C Pflicht
   (`geometric_envelope` par.3f).
5. **Phase 3 auf Block-Ebene bestaetigt** (t 3,25 und -2,87 fuer die beiden
   signifikanten Arme; `r5_value_calibration` par.12), **Reachability
   zifferngleich reproduziert** (par.7 dort).
6. **Hebel 3 der Cache-Prereg abgenommen:** Zusammenfuegen 344 s statt 4,98 h,
   Datenaufbau im Training 31 s. Zwei Bedingungen waren vorher unbekannt
   (Monolith fuer den TRAININGSANTEIL, Block-Bau unter der Trainings-Umgebung;
   `cache_build_time` par.12, Werkzeug `tools/window_train_split.py`).
7. **Blockgroesse 5 ist Default in allen fuenf Arena-Werkzeugen** (Nutzer,
   zweiter Vorfall; `working_rules.md`, `pitfalls.md`).

### Prereg-Bestand

Stand 2026-09-05, 18:22: **11 OFFEN** (`policy_surprise_weighting` fuer b05 und `geometric_envelope` mit Schliesskriterium par.12 wieder offen (17:43); NEU `round_estimate_leaf_term`, Such-Knopf K4, Nutzer-Auftrag 18:20). Stand 11:15 war: **8 OFFEN**: `v24_window`, `v25_window`,
`start_position_seeding`, `special_tile_yield`, `start_dome_choice`,
`round_transition_search_sampling`, `rust_data_layer`, `stack_top_feature`
(Nutzer: Sichtgleichheit, kein Staerkeziel, bleibt offen). Am 2026-09-05 vier
auf ENTSCHIEDEN und vier auf UEBERHOLT/gefaltet gesetzt (`PREREG_INDEX.md`).

### Was als Naechstes ansteht

| Was | Kosten | Anmerkung |
| --- | --- | --- |
| ~~Generatorwahl-Regel bei Gleichstand~~ | -- | ENTSCHIEDEN 2026-09-02 (Nutzer): Staerke schliesst aus, Spaltenprofil entscheidet, sonst Amtsinhaber (`docs/generation_loop.md`, "Generatorwahl unter Armen") |
| ~~Reanalyze-Arm `v23-b07`~~ | -- | ABGENOMMEN 2026-09-03 (`reanalyze_label_depth` par.A5): 75:85 gegen b01, Spalten 0,445 gegen 0,515 -- keine Staerke, weniger Spalten; b01 bleibt Generator. Reanalyze geht NICHT ins v24-Rezept |
| **v24-Erzeugung** | 11,9 h bei threads 11 | Rezept vollstaendig in `PREREG_v24_window.md` par.6; Generator `v23-b01_brierbest`. Startet NUR auf Nutzer-Anweisung |
| Vor dem v24-Training: Monolith fuer den Trainingsanteil | rund 45 min | `tools/window_train_split.py` -> `build_cache_incremental.py --merge-out` unter der Trainings-Umgebung (`cache_build_time` par.12) |
| ~~b04-Zweig~~ | -- | GEPARKT 2026-09-02 (Nutzer): das Problem sitzt im Value-Kopf, nicht in Policy, Breite oder Merkmalsform (`capacity_sim_frontier` par.15). Der Fahrplan traegt die These ab jetzt als Arbeitshypothese |
| Merkposten: `--select-by-brier` bei Kaltstarts | -- | b02 und b06 haben `_brierbest` in Epoche 1 mit BESSEREM Brier als b01 bei schwaecherem Spiel; der b05-Val-Pool misst nicht, was in der Arena zaehlt (`capacity_sim_frontier` par.14b) |
| Push | -- | nie ohne Anweisung; Commits der Nacht sind lokal |

## 2. WAS DIE GENERATION v23 ERGEBEN HAT

**Alle vier Tore bestanden -- das v24-Self-Play ist freigegeben**
(`docs/generation_loop.md` Schritt 9). Herleitungen in
`PREREG_v23_window.md` par.2b bis par.2g.

| Tor | Ergebnis |
| --- | --- |
| 0 Korpus traegt das Signal | Symmetrie-Trennung +0,4041 (t 41,26), 5.629 von 16.000 Seiten mit voller Spalte |
| 1 Siege gegen b05 | **119:61** aus zwei unabhaengigen Seeds (Champion-Strenge erfuellt) |
| 2a Spalten im Self-Play | 0,5150 gegen 0,3100, gepaart **+0,2050** (t 4,47) |
| 2b Spalten in der Arena | 0,6456 gegen 0,4304, gepaart **+0,2152** (t 2,61) |

| Elo-Kante | Ergebnis |
| --- | --- |
| gegen **v22-b05** | 119:61 -- signifikant |
| gegen **v21** (Champion) | 219:181, p = 0,084, KI [-0,013, +0,393] -- **nicht belegt besser**, Augenhoehe. **KEINE Promotion**, v21 bleibt Champion |
| gegen **hv1** (Anker) | 127:23 aus 150 (84,7 Prozent), eingetragen (Abschnitt 4) |

**Phase 3 gemessen, NEGATIV (par.11 der R5-Kalibrierung):** die
Betrags-Daempfung ist unveraendert -- b01 0,0859 gegen b05 0,0886 auf
denselben 139 Paaren. Der Korpus heilt sie nicht. b01 wurde also deutlich
staerker und baut 66 Prozent mehr Spalten, OHNE dass der Bewerter repariert
wurde; der Punkte-Kopf trifft dieselbe Groesse mit 0,97. **Der Eingriff ist
damit faellig**, Erfolgstest "kippt die Sims-Kurve?".

**`v23-b02` (Kaltstart):** Early Stop nach Epoche 15/40, **4,22 h** gegen
b01s 5,97 h -- ein Kaltstart kostet mit stehendem Fenster-Cache WENIGER als
ein Warmstart. Sein brierbestes Modell liegt allerdings bei Epoche 1
(par.2g) -- die Checkpoint-Arena hat es trotzdem zum Kandidaten gemacht:
**33:47 fuer `_brierbest`** (SPRT H0, Vorzeichentest p = 0,189, gepaarte
Differenz -0,350 [-0,791, +0,091], Punkte 42,33 gegen 37,53). Nicht
signifikant, aber die vorab registrierte Regel laesst hier den Punktschaetzer
entscheiden (par.2h).

---

## 3. WAS ALS NAECHSTES ZU TUN IST

**Nutzer-Zuschnitt fuer diese Generation (2026-08-31):** relabelter Sockel,
b02, b03, Phase 3 -- dann v24. **Stand 2026-09-01: alle vier erledigt**, es
bleibt v24 (Abschnitt 1, Rezept in `PREREG_v24_window.md` par.6). Nicht in diesem Zyklus: Kuppelplatten-
Verteilung, Arm K, b04-Breite, geometrisches Gelaender (alle registriert).

### 3.1 Relabel-Arm: GEFAHREN (2026-09-01)

`v23-b05` (Policy-Klasse per hv2-Lehrer relabelt, sonst wie b01): Arena auf
240 Paare verlaengert (2026-09-02): **246:234 fuer b05, p = 0,65**, dritter
Seed 75:85; Spalten 0,676 gegen 0,642, KI [-0,06, +0,13]. Weder Gewinn noch
Schaden, b01 bleibt Generator (par.A3). Herleitung `PREREG_reanalyze_label_depth.md` par.A1; die dortige
Zeile-1-Frage (Spielen gegen Labeln bei Suchtiefe) ist damit NICHT gemessen,
gefahren wurde die Lehrer-Variante. Laufzeit 7,42 h, davon 4,98 h einkerniger
Datenaufbau (`cache_build_time` par.11).

### 3.2 Phase 3: GESCHLOSSEN ohne Bau (2026-09-01)

Stufe 0 der Prereg (`PREREG_r5_value_calibration` par.12) hat die Praemisse
GEPRUEFT, bevor etwas gebaut wurde -- und sie faellt:

| Arm (je 200 Partien, argmax, Seed 20260931) | volle Spalten | gegen Kontrolle |
| --- | --- | --- |
| @100 Sims | **0,7200** | +0,205 (t 3,97) |
| @400 Sims (Kontrolle) | 0,5150 | -- |
| @400, `VALUE_CAL_B=2,0` | 0,3900 | -0,125 (t -2,7) |
| @400, `VALUE_CAL_B=0,5` | 0,5325 | +0,018 (n.s.) |
| @400, `POINTS_UTILITY_W=0,1` | 0,4850 | -0,030 (n.s.) |

**Die Delle gibt es auch bei b01** (0,205, vorher nur an b05 gemessen), **aber
keine Einstellung des Value-Kopfs holt sie zurueck.** Verstaerken schadet,
Daempfen tut nichts, Punkte-Beimischung tut nichts. Die Betrags-Daempfung ist
damit ein registrierter Befund OHNE benannten Nutzniesser -- der Eingriff
entfaellt, der Trainingslauf ist gespart. Die Ursachenfrage erbt
`PREREG_search_depth_column_optimum` Stufe 4: sie liegt nicht in der Skalierung
des Blattwerts und nicht in fehlender Punkte-Information, sondern in dem, was die
tiefere Suche mit den Kandidaten TUT.

**Nebenbefund zu einem Nutzer-Einwand:** die vier fruher geschlossenen Wege am
Verbraucher wurden alle auf plattenBLINDEM v21 gemessen. Der billigste davon
(Punkte-Blend) ist hier auf b01 wiederholt worden und traegt auch dort nicht --
fuer die SPALTEN. Fuer die Staerke sagt der Arm nichts, die alte Schliessung war
eine Staerke-Messung.

### 3.2b Die Tiefen-Delle: vier Wurzel-Eingriffe gemessen, alle wirkungslos

| Eingriff (b01, argmax @400, je 200 Partien) | volle Spalten |
| --- | --- |
| Kontrolle | 0,5150 |
| `VALUE_CAL_B = 2,0` | 0,3900 (-0,125, schaedlich) |
| `VALUE_CAL_B = 0,5` | 0,5325 (n.s.) |
| `POINTS_UTILITY_W = 0,1` | 0,4850 (n.s.) |
| `MOSAIC_GUMBEL_C_SCALE = 0,36` | 0,5000 (n.s.) |
| zum Vergleich: 100 statt 400 Sims | **0,7200** |

Weder Betrag noch Balance noch Zusatzinformation am Blattwert bewegen die Delle --
nur die Suchtiefe selbst tut es. **Was bleibt, liegt tiefer im Baum:** was die Suche
in den Fortsetzungen findet und nach oben propagiert (`search_depth_column_optimum`
Stufe 4). Die quantitativ saubere Erklaerung ueber das sigma/Prior-Verhaeltnis (2,81)
ist gepruft und WIDERLEGT -- sie steht in `prior_blind_spot` par.G3 als solche
markiert.

**Neuer Knopf, bleibt:** `MOSAIC_GUMBEL_C_SCALE` (Default 1,0, paritaetsgeprueft an
20 Partien, im Lauf-Manifest sichtbar). Er kostet nichts und macht die naechste
Frage an die Prior/Value-Balance ohne Bau messbar.

### 3.3 Dann v24 -- Zuschnitt STEHT (2026-09-01)

`PREREG_v24_window.md` ist angelegt und der Generator entschieden: **b01**,
weil kein Arm belegt besser ist. Form wie v23, neu besetzt:

| Klasse | Posten | Partien |
| --- | --- | --- |
| Sockel (Policy) | `v23-b01` Self-Play | 4.000 |
| Sockel (Policy) | `hv2`, policy-aktiv | 1.800 |
| Schwarm (Value) | `v23-b01` Self-Play | 8.000 |
| Schwarm (Value) | `hv2`, policy-maskiert | 15.650 |

**Summe 29.450.** Der hv2-Anteil ist identisch mit dem von v23 (1.745 Dateien
a 10 Partien) und wird UNVERAENDERT weiterverwendet -- **es muss kein einziges
Lehrerspiel neu erzeugt werden**, die Traegerauswahl kommt aus
`data/carriers_v23_hv2.txt`. Neu sind allein die 12.000 b01-Partien, mit
`--per-file 10` (`docs/working_rules.md`). Verfahren: `docs/generation_loop.md`.

**Die Daten der Vorgeneration sind archiviert** (Nutzer, 2026-09-01): in
`data/` stehen nur noch die 1.745 hv2-Dateien des Fensters plus ihre Bloecke.
Alles andere liegt im Archiv, samt einer README, die festhaelt, welche
Korpora BELEGE laufender Preregs sind (frozen_v3-Quelle, die vier
Phase-3-Arme, der Tor-2a-Referenzlauf).

### 3.4 Belegungsplan (GPU und CPU parallel)

Regel und Thread-Budget: `../docs/working_rules.md`, Abschnitt "Auslastung".
Ein Training belegt gemessen rund EINEN Kern, der CPU-Auftrag daneben darf
also rund 10 Threads nehmen. Zwei CPU-Messungen gegeneinander bleiben
verboten, und ein unter Nebenlast gefahrener `laufzeit`-Block wird als
solcher markiert.

---

## 4. STAND JETZT

**Champion seit 2026-09-04, 19:33: `v23-b01_k3p10`** (= `v23-b01_brierbest`
mit K3-P: projiziertes Huellen-Potential, Modus 1, C_HULL 1,0, Spec
`models/v23-b01_k3p10.spec.json`; Server-Default `models/champion.txt`, die
GUI uebernimmt die Spec beim Start in die Env-Knoepfe). Elo **1292**
[1253, 1335] auf der R5-Fix-Leiter (`elo_tracker.py report`, alle Knoten mit
dem Anker verbunden) aus vier Kanten: Gating 38:12 und 221:179 gegen v21,
Anker 128:22 (n=150, Cross-Aera), Champion-2 32:8 gegen v22-b05 (v20 nicht im
Baum). Vorgaenger `v21_2d_brierbest` 1232 [1199, 1265]; `v23-b01_brierbest`
ohne Knopf 1263 [1226, 1305]. Anzeige-Kalibrierung server.py A=-0,1080 /
B=0,5587 (frozen_v3); sigma/Prior-Balance 2,92 (unter der 3er-Schwelle, Runde
3 3,88); Paritaets-Fixture `a274e3ad68f4ad91` (frischer Prozess gruen).
Promotion nach `docs/promotion_checklist.md`, Artefakt
`models/frozen_champions/v23-b01_k3p10/`. Kanten ueber die Fix-Grenze nie
mischen.

**Bester Stand der Spalten-Linie: `v23-b01_brierbest`** (seit 2026-08-31) --
volle Spalten 0,5150 am argmax-Instrument, 119:61 gegen den Vorgaenger b05,
gegen den Champion 219:181 (nicht signifikant). **Anker-Kante gefochten
(2026-08-31, 22:39): 127:23 aus 150 = 84,7 Prozent** gegen
`Heuristik_hv1_anchor`@150, Cross-Aera, Golden-Selbsttest gruen, Ergebnisse per
Determinismus-Probe freigegeben. **ES GIBT KEIN REMIS** (Nutzer-Hinweis, Regel an
`game.rs:586` geprueft: bei Gleichstand gewinnt, wer den Startspielerstein zuletzt
nahm): der Schiedsrichter meldete drei Partien faelschlich als Remis, alle drei gehen
an b01. `frozen_referee_match.py:380` liest den Tie-Break jetzt aus dem Zustand
(`first_player_next_round`), Gegenprobe auf denselben Seeds bestaetigt es. Die
Rust-Arenen waren nie betroffen. Kennzahlen je Seite: volle Spalten 0,953 gegen
0,027, Punkte 53,97 gegen 36,13, Margin +17,84, Strafpunkte -14,31 gegen -20,17.
Elo als HERLEITUNG: rund +297 ueber dem Anker (aus 84,7 Prozent), und rund +33 ueber
v21 aus der Champion-Kante. Beide Kanten sind seit dem 2026-08-31 in
`elo_history.csv` und die Anker-Kante zusaetzlich in `arena_trends.csv`. Zum
Vergleich, ueber zwei Instrumente hinweg (Paritaet 20/20 belegt): v21 kam am Anker
auf 116 von 150 (77,3 Prozent, Remis dort nicht ausgewiesen).

**EINGETRAGEN am 2026-08-31** in `elo_history.csv` und `arena_trends.csv`.
Beim Eintragen fiel auf, dass der Tracker auf den LITERALEN Namen `Heuristik`
verankerte, waehrend die Checkliste `Heuristik_hv1_anchor` vorschreibt -- die Kante
landete dadurch in einer eigenen, freien Komponente (b01 1148 / Anker 852, Summe
exakt 2000). BEHOBEN, siehe unten; Herleitung in `PREREG_agent_encapsulation.md`
par.13.

**Die Vorbedingung ist inzwischen GEMESSEN (2026-08-31, Nutzer-Vorgabe: nicht
gegeneinander spielen lassen, sondern Zug fuer Zug vergleichen).**
`tools/verify_frozen_heuristic.py` in beiden Modi, hv1-Rezept aus dem Manifest
(10 Partien, 600 Sims, Seed 20260826):

| Modus | Verdikt | verglichen | Wanduhr |
| --- | --- | --- | --- |
| Live-Wheel (Drift) | **GRUEN** | 1.763 Schritte, Feld fuer Feld, keine Abweichung | 22,2 s |
| Artefakt-Wheel (Konservierung) | **GRUEN** | dieselben 1.763 Schritte | 13,4 s |

Dazu die Referee-Paritaet neu gefahren (`anchor_referee_parity_20260831.json`):
20/20 identisch in beiden Modi, 0 Abweichungen. **Der lebende Code spielt hv1 also
Zug fuer Zug wie das Artefakt** -- die Engine-Aenderungen seit dem Einfrieren haben
den Anker nicht bewegt. Ab jetzt Pflicht nach jeder Engine-Aenderung, als Skill
`mosaic-anchor-invariance` abgelegt.

**Nutzer-Klarstellung dazu:** die In-Process-Heuristik ist eine
ENTWICKLUNGSUMGEBUNG, kein Vergleichswert. Der Fixpunkt gehoert an das Artefakt;
"der Anker ist gedriftet" ist keine moegliche Diagnose, ein rotes Ergebnis hiesse,
der lebende Code hat sich bewegt.

**GESETZT (Nutzer-Anweisung 2026-08-31): der Anker IST das Artefakt.**
`ANCHOR_NAME = "Heuristik_hv1_anchor"` in `tools/elo_tracker.py`, dazu
`ANCHOR_ALIASES = {"Heuristik": ...}` fuer die Zeilen vor der Umbenennung.
`Heuristik_v2huelle` bleibt ein eigener Spieler. Registriert in
`PREREG_agent_encapsulation.md` par.13, Ablauf als Skill
`mosaic-anchor-invariance`, Checkliste nachgezogen.

**Die Leiter danach** (`python tools/elo_tracker.py report`, 11 Zeilen, kein
einziger "NICHT verbunden"-Vermerk mehr; eingetragen sind seither auch die
beiden Tor-1-Gatings gegen b05):

| Modell | Elo | 95%-KI | Partien |
| --- | --- | --- | --- |
| **v23-b01_brierbest@400** | **1263** | [1223, 1311] | 730 |
| v21_2d_brierbest@400 | 1227 | [1191, 1269] | 1407 |
| v20_2d_opp_brierbest@400 | 1194 | [1158, 1235] | 950 |
| v19_2d_best@400 | 1142 | [1103, 1186] | 550 |
| Heuristik_v2huelle@150 | 1137 | [1086, 1190] | 407 |
| v22-b05@400 | 1136 | [1074, 1198] | 230 |
| Heuristik_hv1_anchor@150 | 1000 | fix | 600 |

**Beide Kanten sind drin (Nutzer-Anweisung 2026-08-31, "ist ja ein valides
match"): die Champion-Kante 219:181 gegen v21 ist als 9. Zeile eingetragen** --
informativ, kein Promotionsentscheid. Sie zieht b01 von 1297 (Anker-Kante allein)
auf 1266; mit den beiden b05-Kanten dazu steht er bei **1263** ueber 730 Partien.
Anker- und Champion-Kante implizierten einzeln 1297 und rund 1259, der gemeinsame
Fit legt sich dazwischen. Die KI von b01 [1223, 1311] und v21 [1191, 1269]
ueberlappen -- dieselbe Aussage wie die
Champion-Kante selbst: Augenhoehe, nicht belegt besser, keine Promotion.

**Was noch offen BLEIBT:** der Alias faltet die Anker-Kanten vom 2026-08-20 auf ein am 2026-08-26
   eingefrorenes Artefakt. Fuer diese sechs Tage liegt kein Wheel im Baum, die
   Zug-Gleichheit ist dort also NICHT geprueft. Einzige unbelegte Fuge der
   Leiter.

Vorgaenger `v22-b05`: Elo **1136** [1074, 1198] -- und das ist eine ANDERE Zahl als
die 1084, die hier bis zum 2026-08-31 stand. Grund ist nicht eine neue Partie,
sondern die Datenlage: b05 hing bis dahin an einer einzigen fruehgestoppten Kante
(16:34 gegen v21, n=50). Mit den beiden Tor-1-Gatings gegen b01 (52:28 und 67:33)
kommen 180 Partien dazu, das Intervall schrumpft von 228 auf 124 Punkte. Der
hv2-Lehrer liegt mit **1137** jetzt gleichauf statt 40 Punkte darueber.

**Wheel:** 79-Kanal-Build (`e91cd34`), Vertragshash `efd564d87bac2722`,
Paritaets-Hash `8c6684ff...` gemessen unveraendert.

**Was ueber den Value-Kopf gemessen ist:** relativ geheilt, im Betrag
gedaempft -- und die Daempfung ist auf v23-b01 unveraendert (0,0859 gegen
b05s 0,0886, par.11). Geschwister-Tau auf b05 **+0,338** (gegen -0,08/-0,19
der plattenblinden Netze), Mensch-Orakel-Differenz praktisch null. Kriterienweise aufgeloest ist die
Daempfung BREIT, nicht spaltenspezifisch (k1 mit 0,1747 am wenigsten
gedaempft). Daraus die Betrags-Schiene als Phase 3.

**Was ueber den Spaltenbau gemessen ist:** der Korpus wirkt (b01 baut 3x so
viele Spalten wie der Champion), das Ownership-TRAININGSGEWICHT nicht (w0
gleichauf, w2,0 signifikant darunter). Der Engpass ist die VOLLENDUNG spaet,
nicht der Plattenblick. Die Suchtiefe ist ein Regler zwischen Policy
(traegt das Spaltenwissen) und Value-Kopf: Plateau 25-100 Sims bei ~0,6
vollen Spalten gegen 0,34 ab 250 -- aber ein TAUSCH (@25 verliert 11:29,
@100 verliert 33:47 n.s.). Die Erklaerung dafuer ist OFFEN; die Deutung
"der Kopf sieht Spalten nicht" ist durch die kriterienweise Zerlegung
widerlegt.

**Erzeugungs-Knoepfe, gemessen entschieden:** implicit-Minimax alpha 0,0,
Stack-Draw-Kontrollfluss EIN, Bootstrap-Horizont 2, Seed-Positionen AUS
(Quelle plattenblind), Startkuppel Handheuristik, Vollendbarkeits-Filter AUS
(ungebaut). Vollstaendig in `PREREG_v23_window.md` par.4c.
---

## 5. OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Worum es geht |
| --- | --- |
| **b04: welcher Zweig wird breiter** | Flach-Zweig `hidden_size` 512 ist ohne Bau fahrbar; Conv-Zweig `conv_channels` 48 / `conv_layers` 2 braucht zwei Flags, ein Checkpoint-Feld und eine Ableitung beim Laden -- sonst ist der Checkpoint nicht ladbar (`PREREG_capacity_sim_frontier.md` par.10) |
| ~~frozen_v3: woher die Zustaende~~ ERLEDIGT 2026-09-01 | Weg (b) gefahren: 400 frische Sockel-Partien (24,2 min), Satz und zwei Orakel-Label-Saetze gebaut (`PREREG_frozen_v3_eval_set.md` par.7-9). Quelldateien liegen im restic-Backup (`archive_pre_v24/`) |
| ~~Generatorwahl bei Gleichstand der Arme~~ | ENTSCHIEDEN 2026-09-02: dreistufig, Staerke schliesst aus, Spaltenprofil entscheidet, sonst Amtsinhaber (`docs/generation_loop.md`) |
| ~~Loeschfreigaben~~ ERLEDIGT 2026-09-01 | `data/onpolicy_v22-b05/` und `-b06/` auf Nutzer-Freigabe geloescht (je 31 Dateien, 32 + 34 MB). Vorher geprueft: KEINE Fenster- oder Traegerdatei verweist darauf. Die Preregs `heuristic_v2_long_rows` (DAgger-Runden) und `v23_window` zitieren sie im TEXT -- die Herleitungen bleiben lesbar, die Rohpartien sind weg |
| **Messartefakte tracked?** | `evaluations/artifacts/` ist ungetrackt; Preregs zitieren die JSONs als Beleg, ein frischer Klon hat sie nicht. Zurueckdrehen: `.gitignore`-Zeile raus, `git add -f` |
| **Push** | NIE ohne ausdrueckliche Anweisung; der Ahead-Stand wird im CHAT gemeldet, nicht hier gefuehrt |

---

## 6. OFFENE STRAENGE -- abgeglichen mit dem Prereg-Index (2026-08-31, nachgefuehrt 2026-09-01)

Der Index zaehlt (Stand 2026-09-01 abends, aus dem Generator) **20 OFFEN, 77 ENTSCHIEDEN, 8 UEBERHOLT** (`search_depth_column_optimum` ist wieder OFFEN, `frozen_v3_eval_set` und `v23_reachability_recheck` sind ENTSCHIEDEN)****.
Koepfe, die gegen ihren eigenen Koerper standen, sind an drei Tagen berichtigt
worden: am 2026-08-31 `cache_build_time` und `v23_reachability_recheck`, am
2026-09-01 frueh `policy_surprise_weighting`, `cache_build_time` (Hebel 3
hat einen Nutzniesser) und `r5_solver_split`, am 2026-09-01 abends bei der
Pruefung aller geaenderten Preregs `prior_blind_spot` (Kopf behauptete die
widerlegte Erklaerung), `heuristic_v2_long_rows` (Erzeugung "laeuft"),
`v23_window` (Arm-Frage offen), `search_depth_column_optimum` (jetzt OFFEN,
Stufe 4), `capacity_sim_frontier`, `reanalyze_label_depth`,
`policy_surprise_weighting` (Kennzahlen).

**Am laufenden Strang, mit Platz im Fahrplan:**

| Prereg | Wo es haengt |
| --- | --- |
| ~~`v23_window`~~ | ENTSCHIEDEN: Fenster gebaut, alle Tore und alle Arme gemessen |
| `capacity_sim_frontier` | Warm gegen Kalt einfaktoriell belegt (b06, par.14b: 0,18 Spalten, 65:95); b04 wartet auf den Zweig-Entscheid (Abschnitt 5) |
| ~~`policy_surprise_weighting`~~ | ENTSCHIEDEN 2026-09-01: b03 traegt nicht (Orakel Gleichstand, Arena 75:85) |
| `reanalyze_label_depth` | ENTSCHIEDEN 2026-09-03 (par.A5): Lehrer-Relabel b05 Nullbefund (par.A3), Reanalyze b07 keine Staerke und weniger Spalten -- b01 bleibt Generator; Teil B ohne Verbraucher bei lambda 1,0 |
| ~~`r5_solver_split`~~ | Teil B war Phase 3 -- GESCHLOSSEN ohne Bau (2026-09-01) |
| ~~`v23_reachability_recheck`~~ | ENTSCHIEDEN 2026-09-01: 14,64 Prozent tot-kartiert gegen 13,89 beim Vorgaenger, Stufe 1 wird NICHT eroeffnet; Quelldateien im restic-Backup |
| ~~`search_depth_column_optimum`~~ | ENTSCHIEDEN 2026-09-02: Stufe 4 komplett (par.6b, par.7); Tiefen-Delle beschrieben, nicht behoben |
| `special_tile_yield` | Kanaele 77/78 gebaut, ihre Wirkung nie isoliert |
| `cache_build_time` | Hebel (3) hat seit 2026-09-01 einen Nutzniesser: **4,98 h** einkerniges Zusammenfuegen bei neuer Fenster-Zusammensetzung (par.11). Die vermisste serielle Vollreferenz liegt damit auch vor |
| `frozen_v3_eval_set` | ENTSCHIEDEN und GEBAUT 2026-09-01 (Satz 1.800 Zustaende, Orakel aus b01 und v21, Zirkularitaet belegt, par.7-9). Nachgetragen: die Bruecke gilt nur fuer Runden 1-4; Quelldateien im restic-Backup; Artefakte ohne `laufzeit`-Block |
| `geometric_envelope` | K3 GEBAUT 2026-09-03 (par.8.2/8.3, Anker und Paritaet GRUEN), Messung nach par.8.4 offen; par.8.6 (Value-Anteil im Tiling, Vorpruefung bestanden) wartet auf den Nutzer |

**Registriert, nicht eingetaktet** (jeder Bau braucht vorher eine
Registrierung): `plate_policy_supervision`, `saturating_score_utility`,
`risk_sensitive_leaf_utility`, `uvfa_plate_regime`,
`uncertainty_guided_selfplay`, `start_position_seeding` (Dosis-Folgearm),
`start_dome_choice` (Stufe 0, Wiedervorlage Generation 2),
`round_transition_search_sampling` (Kostentor zuerst),
`stack_draw_reservation_rule` (Default AUS steht),
`stack_top_feature`, `chance_nodes` (Teil B1/A1 geparkt),
`floor_shaping_scale`, `rust_data_layer` (Registrierung, kein Auftrag).

**OHNE PREREG, nur Merkposten -- und darum beim Index-Abgleich durchgefallen
(berichtigt 2026-08-31):** die Neufassung hat Abschnitt 5 aus dem
Prereg-Index gebaut, und damit faellt per Konstruktion alles heraus, was
offen ist, aber keine Prereg hat. Wieder aufgenommen:

* **Einhuellende / geometrisches Gelaender: seit 2026-08-31 REGISTRIERT**
  als `PREREG_geometric_envelope.md` (Nutzer-Auftrag) -- damit ist der
  Merkposten von 2026-08-24 abgeloest. Steht in Abschnitt 5 oben bei den
  Straengen am laufenden Fahrplan.
* **#31 / #38 / #39**: geparkt, Arbeitskreis "Spaeter", Beschreibungen im
  Archiv.

Wer Abschnitt 5 kuenftig aus dem Index erzeugt, traegt diese Liste HIER
nach -- der Index kennt nur, was eine Datei hat.

**Verschoben, nicht verworfen:** Arm K (Bootstrap-Kohaerenz,
`PREREG_heuristic_v2_long_rows.md` par.3b.3/3b.3a) -- gebaut, Default aus,
ausloeserbasiert. Er korrigiert einen VERSATZ, das gemessene Problem ist eine
STEIGUNG; seine drei benannten Nutzniesser sind ungebaut; und er ist der
einzige Arm, der alle Cache-Bloecke entwertet.

---

## 7. MERKLISTE CODEPFLEGE (Audit 2026-08-27, bewusst verschoben)

**Naechstes Build-Fenster** (brauchen cargo, Paritaets-Gate): sechs Dialekte
fuer "ist dieser Bool-Knopf an?" (Befund 4); drei stille Env-Verschlucker
(13-15); Value-Spread-Pfad verkleinert den Pool still (16); toter Zweitpfad
`board.rs:184-220` mit irrefuehrenden Spaltennamen (19).

**Nach dem v23-Training:** ONNX-Paritaetspruefung nie fertiggebaut (18);
Kanalzahl als Hand-Literal im Fenster-Key (5, NICHT vor dem Training);
viermal dasselbe 95%-KI mit Entartungen (20); sieben Eigenaufloesungen von
`champion.txt`, sechs Tool-Stellen offen plus `dist/mosaic_release.spec:46`
packt eine geloeschte ONNX (21); `MosaicDataset.__init__` mit 998 Zeilen
(22); `offline_diagnosis.py` rechnet ein historisches Value-Ziel (6).

Fundstellen im Audit-Bericht; Details im Archiv-Kapitel.

---

## 8. STRUKTURBEFUNDE, die weitergelten

- **Der Champion vollendet keine Spalten**, und der Grund ist Verteilung,
  nicht Versorgung: eine volle Spalte kostet 21 Zellen, das Netz verbraucht
  42,7 und truege gleichverteilt 2,03 Spalten statt 0,10.
- **Die Dreiecksform ist die MACHBARKEITSHUELLE**, keine aesthetische Wahl:
  erlaubt ist `r + c <= 5`, also dieselben 21 Zellen.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich** -- sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je Runde
  ab. Spalten haben das Problem nicht.
- **Der Durchbruch kam vom DRAFTING, nicht vom Routing** (Split-Test, je 160
  gepaarte Partien): Huelle nur im Drafting 0,756 gegen 0,044 (t 10,29),
  Huelle nur im Routing 0,113 gegen 0,113. Die Luecke zur Summe ist eine
  Wechselwirkung -- das Routing kann nur einsortieren, was das Drafting geholt
  hat.
- **Erste unkontaminierte Referenz:** Mensch-gegen-Netz in `static/log/` --
  der Mensch schliesst 1,80 volle Spalten je Partie gegen 0,10 des Netzes,
  bei GLEICHEN Platzierungspunkten. Der Vorsprung sitzt bei den
  Spezialfliesen; der Mensch tauscht kurze Reihen gegen lange.
- **Chip-Allokation, nicht Chip-Volumen:** Mensch 0,8 Reihe-6-Chip-
  Abschluesse je Partie, v21 0,1. Kosten-gewichtete Huelle Mensch 0,86,
  Lehrer 0,68 (berichtigt 2026-09-03: die zweite Huelle war falsch
  gespiegelt, `heuristic_v2_long_rows` par.3b.14); Netz-Werte 0,54-0,62
  stammen noch aus der falschen Rechnung und sind vermutlich zu niedrig.
- **Blindzieh-Regel:** bei Wertungsplatte 6 laeuft die gebaute Stopp-Regel das
  Punktekonto leer (58-66 Prozent der Serien enden bei 0). Spaltenbau behebt
  das NICHT -- k1 zahlt quadratisch, das Spezialfeld-Defizit kostet linear -3
  je Feld.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch.
