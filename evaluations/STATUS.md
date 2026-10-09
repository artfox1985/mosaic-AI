# Mosaic-AI – Status: Projektabschluss

**Stand 2026-10-09 abends. Projektabschluss.** v35 war die letzte Generation (Nutzer 2026-10-04: *"v34 hat das
projektziel meiner meinung nach bereits erreicht"*); ihr Ergebnis `v35-b16` ist seit 2026-10-09 Champion und traegt
den Anzeigenamen **Tessa**. Eine v36 gibt es nicht. Dieses Dokument traegt nur noch den Endstand und die offenen
Nutzer-Entscheide.

Neufassung vom 2026-10-09 (`/mosaic-generation-turnover` Schritt 6, Projektabschluss). Der vollstaendige Stand davor
liegt in `../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-10-09 (vor der Neufassung zum
Projektabschluss)"**, davor das Kapitel **"Generationsbericht v35 und Promotion v35-b16 (2026-10-04 bis 2026-10-09)"**.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach, prueft, ob ein anderer Abschnitt dadurch
falsch wird, und greppt nach den Konsumenten (CLAUDE.md, Rueckwaerts-Pruefung). **Prozesswissen steht NICHT hier**,
sondern in `../docs/` (`generation_loop.md`, `promotion_checklist.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`).

---

## 1. WAS GERADE LAEUFT

**Nichts. Maschine frei.** Der letzte Lauf war die Promotionskette `tools/v35_promotion_chain.sh` (2026-10-09
12:06:52 bis 16:33:23, `PREREG_v35_window.md` par.22a); danach nur Handarbeit (`set_champion.py`, `server.py`,
Paritaets-Fixture, Register) und der Commit `a3fa6be3` (16:50:03). Keine Kette, kein Wecker, keine Erzeugung
vorgesehen.

Der Spielprozess des Nutzers, der ab 09:52 neben den Laeufen lief (par.21a, par.22a), ist beendet (Prozessliste
2026-10-09 17:0x). Vor einer neuen Messung gilt wie immer: Maschine exklusiv (CLAUDE.md).

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v35-b16_brierbest`** (seit 2026-10-09 16:4x, par.22a), Spec
`models/v35-b16_brierbest.spec.json`, byte-gleich `v34-b01_brierbest.spec.json` (sha256 `721e08f0...`;
Startkuppel-Suche, Runde 5 per Netz, Tree Reuse aus). Anzeigename **Tessa**. Der Server zieht Champion, Spec und
Anzeige-Kalibrierung erst nach einem Neustart (par.22a, 5b).

| Modell | Elo | KI95 | Quelle |
| --- | --- | --- | --- |
| **v35-b16@400 (Champion, Tessa)** | **1660** | **[1607; 1713]** | 1.050 Partien, 2 von 5 Kanten frueh gestoppt (par.22a) |
| v34-b01@400 (Vorgaenger) | 1575 | [1527; 1624] | vorher 1595; die neuen Kanten verschieben die Leiter (par.22a) |
| v32-b01@400 | 1450 | [1405; 1497] | par.22a |
| Heuristik `hv4_anchor`@150 (Anker) | 1000 | fix | Leitersegment 2 |

Stand des Fits 2026-10-09 (`elo_tracker.py report`, 92 Zeilen, kein Knoten ohne Ankerverbindung; par.22a).

**Kanten von v35-b16** (alle 2026-10-09, Register `evaluations/elo_history.csv`):

| Kante | Ergebnis | Verweis |
| --- | --- | --- |
| Tor 1 gegen v34-b01, Seeds 20261600/01 | 135:75 und 154:86, gepoolt **289:161 = 64,2 %**, Block-z +6,63, beide SPRT-Stopp | par.20a/20b |
| Replikation bis zum Deckel, Seed 20261603 | **249:151 = 62,3 %**, 200 Paare, Block-z +5,07 | par.22a |
| Anker `hv4_anchor` @150 | **46:4** (n = 50) | par.22a |
| Champion-2 gegen das Artefakt `v32-b01` | **107:43 = 71,3 %** (n = 150) | par.22a |

**Diagnostiken, gepaart gegen v34-b01** (par.22a): Brier-Regel haelt (frozen_v3 0,22688 gegen 0,22806); sigma/Prior
2,03, unter 3; R4/R4b/R5 in der Richtung leicht schwaecher, ohne Intervall. Anzeige-Kalibrierung in `server.py`
A = -0,0312 / B = 0,5870 (par.22a, 5b). Paritaets-Fixture neu erzeugt am 2026-10-09, Hash `f9892cce9c5176f0`
(`engine/tests/fixtures/net_parity_champion.txt`; par.22a Nachtrag 5d, frischer Prozess gruen).

**Artefakte:** `models/frozen_champions/v35-b16/` (Wheel `cd8995bf...`, Golden Probe 10 Sonden / 40 Partien, venv
ohne Netz, Referee-Selbsttest gruen; par.22a) und als Vorgaenger `models/frozen_champions/v34-b01/` (Promotion
2026-10-03, `PREREG_v34_window.md` par.10e). `frozen_champions/v32-b01` faellt nach der Zwei-Champion-Regel heraus
(Abschnitt 5). `.onnx`, `.pth` und Wheels der Artefakte sind NICHT im Repo.

## 3. ERGEBNIS DER SCHLUSSREIHE v35

Gegner ist der damalige Champion `v34-b01` (Tor 1, gepaartes Gating @400, gepoolt ueber die Seeds), sofern nicht
anders vermerkt; "Schnellblick" = 2 x 50 Paare (par.19.0). Alle Messungen 2026-10-04 bis 2026-10-09.

| Arm | Hebel | Ergebnis | Verweis |
| --- | --- | --- | --- |
| b01 | Fenster aus den fuenf v34-b01-Klassen, Wertmaske | 208:192 = 52,0 %, Block-z +0,92, ein Seed, nicht entschieden | par.11c |
| b02 | Fenster komplett @400 mit Modus 2 neu erzeugt (11.000 Partien) | 596:454 = 56,8 %, Block-z +4,07 | par.12e |
| b03 | Wertziel: Trajektorien-Bootstrap k = 1 | 381:269 = 58,6 %, Block-z +5,12 | par.13b |
| b05 | Trajektorien-Bootstrap k = 2 | 451:349 = 56,4 %, Block-z +3,88 | par.13d |
| b06 | Trajektorien-Bootstrap k = 3 | 455:345 = 56,9 %, Block-z +3,83 | par.13f |
| b04 | Wertziel: Margen-Bootstrap b = 20 | 674:526 = 56,2 %, Block-z +3,98; schlechtester Brier, kein Hebel ueber b02 | par.14c |
| b07 | lambda 1,0 (kein Suchwert-Anteil) | 418:382 = 52,25 %, Block-z +1,26: traegt NICHT | par.15b |
| b08 | EMA der Checkpoints | kein Tor 1, Vorab-Test negativ | par.16a |
| b08b | EMA, Auswahl am eigenen Brier-Minimum | Schnellblick gegen b02 92:108 = 46,0 %, Block-z -0,98 | par.16c |
| **b10** | Schwarm als Policy-Traeger (1.200 statt 400), keine Erzeugung | **420:270 = 60,9 %, Block-z +6,22** | par.18b |
| **b09** | +4.000 Policy-Partien @400 | **390:270 = 59,1 %, Block-z +4,15** | par.17c |
| b11 | TD(lambda) ueber den Pfad, lambda 0,5 | Schnellblick gegen b02 78:122 = 39,0 %, Block-z -3,93 | par.19.1a |
| b12 | wie b11 plus Gegnerstellungen | gegen b02 97:103 = 48,5 %, Block-z -0,43 | par.19.2a |
| b13 | halb Trajektorie k = 1, halb Rollout | gegen b02 105:95 = 52,5 %, Block-z +0,86 | par.19.3a |
| b14a | TD_LAMBDA 0,7, Trajektorie k = 1 | gegen b02 98:102 = 49,0 %, Block-z -0,35 | par.19.4a |
| b14b | value-target-lambda 0,5, Trajektorie k = 1 | gegen b02 94:106 = 47,0 %, Block-z -0,78 | par.19.4b |
| b15 | Konfidenzgewichtung s = 0,01224 | Schnellblick 108:92 = 54,0 %; volle Breite gegen b02 351:379 = 48,1 %, Block-z -1,12 | par.19.5b/19.5d |
| **b16** | **b09-Fenster, alle 1.600 Dateien Policy-Traeger (b10 + b09 gestapelt)** | **289:161 = 64,2 %, Block-z +6,63; Replikation 62,3 %, Block-z +5,07: CHAMPION** | par.20b, par.22a |
| b17 | v34-b01 plus Tree-Reuse-Spec (gleiches Netz) | 637:563 = 53,1 %, Block-z +2,22: traegt knapp | `PREREG_tree_reuse.md` par.3c |
| b18 | b16 plus Tree-Reuse-Spec | Schnellblick gegen b16 102:98 = 51,0 %, Block-z +0,29: nicht spannend | `PREREG_tree_reuse.md` par.3e |
| b19 | b16 plus Trajektorien-Bootstrap k = 1 | Schnellblick gegen b16 104:96 = 52,0 %, Block-z +0,54: kein Hebel | par.21a |
| Sonde | Tiling-Ueberraschung des Wertkopfs | kein systematischer Spielraum, Mini-Suche nicht gebaut | `PREREG_tiling_surprise_probe.md` par.3b |

"par." ohne Dateinamen = `PREREG_v35_window.md`. **Lehre:** der Hebel sass bei den Policy-Traegern (b10, b09, gestapelt
b16); keine Wertziel-Variante und keine Gewichtsmittelung legte Belegbares auf das @400-Fenster (par.13-16
Zusammenfassung, par.19.6); Tree Reuse traegt auf v34-b01 knapp, auf b16 nicht sichtbar.

## 4. PREREG-BESTAND (Stand 2026-10-09 abends: 4 OFFEN; Ziel rund 7 erreicht)

`PREREG_INDEX.md` (generiert, Stand-Zeile im Tabellenteil): **137 Dateien = 4 OFFEN + 119 ENTSCHIEDEN + 14 UEBERHOLT** (`v35_window` am Abend auf ENTSCHIEDEN gesetzt, par.22a Nachtrag 5d).
Die vier OFFEN-Koepfe gegen die Zeile 1 der Dateien geprueft:

| Prereg | Was noch aussteht |
| --- | --- |
| `asymmetric_selfplay` | Sonden gefahren; offen war laut STATUS vom 2026-10-03 nur die Zusammensetzung des v35-Sockels. Der Sockel ist seit 2026-10-04 erzeugt (`PREREG_v35_window.md` par.10a), die Frage damit praktisch beantwortet (HERLEITUNG; Kopf nicht nachgezogen) |
| `difficulty_levels` | ganze Leiter der GUI-Stufen auf den letzten Champion vertagt, jetzt also auf Tessa = v35-b16 |
| `subtree_value_bias` | nichts gebaut, nichts gemessen (registriert 2026-10-05) |
| `variance_scaled_cpuct` | nichts gebaut, nichts gemessen (registriert 2026-10-05) |

**Am Projektende** koennen offene Preregs als "nicht mehr verfolgt" geschlossen werden (Kopf mit Verdikt-Satz, danach
`python tools/generate_prereg_index.py`). Entscheid beim Nutzer, je Datei; das gilt besonders fuer `difficulty_levels`,
das als einzige der vier noch einen Nutzen fuer die GUI haette.

## 5. OFFENE NUTZER-ENTSCHEIDE

1. **Loeschungen nach `docs/closeout_deletion_inventory.md`** (Vorlage vom 2026-10-09, Gruppen 3.1-3.7, Summen 3.8): Trainingscaches
   und Korpora in `data/`, Zwischenstaende und Nebenstaende in `models/` (darunter `v35-b02`, `v35-b10`),
   `frozen_heuristics/hv2_generator`, Ketten-Skripte, Release-Zip, `engine/target`. Je Gruppe restic-Beleg (bei `*.h5`
   und `engine/target` gibt es keinen: unwiederbringlich) und pfadgenaue Freigabe.
2. **Zwei-Champion-Regel:** `models/frozen_champions/v32-b01` ist Loeschkandidat (amtierend v35-b16, Vorgaenger v34-b01;
   par.22a). Nur mit restic-Beleg und pfadgenauer Freigabe.
3. **Direkte Kante b16 gegen b10** (2 x 200 Paare, rund 4 h, HERLEITUNG par.20b): fuer die Promotion nicht noetig; sie
   wuerde nur klaeren, ob b16 ueber b10 addiert oder Seed-Glueck ist.
4. **Claude-Partien g13/g14 gegen Tessa** (Nutzer 2026-10-08: erst gegen das finale Modell; das ist jetzt v35-b16).
5. **Server-Neustart**, damit die Anzeige Champion, Spec und Kalibrierung von v35-b16 zieht (par.22a, 5b). Ob er seit
   16:4x erfolgt ist: ungeprueft.
6. **Offene Preregs** (Abschnitt 4): schliessen als "nicht mehr verfolgt" oder weiterfuehren.
7. **Push** (Abschnitt 7).
8. Aeltere Punkte aus dem frueheren Abschnitt 6 (Code-Review 2 #17-#19, Budget-Knopf der Hilfsknoten, Gruppe B des
   Aufraeumens, Sichtluecke bei gezogenen Stapelplatten, `-Deep`-Lauf der Backup-Verifikation u. a.) stehen woertlich
   im Archivkapitel vom 2026-10-09; ohne Gegenwort gelten sie am Projektende als nicht mehr verfolgt (Vorschlag, kein
   Entscheid).

## 6. VERWEISE UND LAUFZEITEN (gemessen)

| Was | Wo |
| --- | --- |
| Kostentabelle aller Laeufe | `../docs/measured_runtimes.md` (v35 ab Abschnitt "v35-Fenster, Training und Tor 1, gemessen am 2026-10-04") |
| Promotions-Checkliste | `../docs/promotion_checklist.md` |
| Loesch-Inventar zum Abschluss | `../docs/closeout_deletion_inventory.md` |
| Projektueberblick | `../docs/project_overview.md` |
| Englische Darstellung | `../README.md`, Abschnitt "Current Status" |
| Herleitungen v35 und Promotion | `PREREG_v35_window.md` par.9-22a |
| Chronik bis zur Neufassung | `../archive/history.md`, Kapitel "Generationsbericht v35 und Promotion v35-b16" und "Vollstaendiger STATUS-Stand vom 2026-10-09" |

Planungsgroessen aus v35 (exklusiv, sofern nicht vermerkt; Quelle `docs/measured_runtimes.md` und die genannten Absaetze):

| Aufbau | Dauer | Quelle |
| --- | --- | --- |
| Erzeugung @400, Modus 2, 11 Threads | 5,20-6,92 s je Partie; v35-b02 11.000 Partien 18,9 h | measured_runtimes, Erzeugung v35-b02 (2026-10-05) |
| Training Warmstart 12 Epochen, cuda | 1.676,8 s (2,04 M Samples, b02) bis 2.086,8 s (2,83 M, b16) | measured_runtimes; par.20b |
| Tor 1 je Seed, 200 Paare @400, 10 Threads | 7.100-7.300 s (17,5-18,2 s je Partie) | measured_runtimes, Arm-Kette 2026-10-06/07 |
| Schnellblick 2 x 50 Paare | 3.319 s (b18, 2026-10-09) | `PREREG_tree_reuse.md` par.3e |
| Arm ohne Erzeugung und Blockbau (b16) | 3,0 h | par.20b |
| Promotionskette v35-b16 | 4 h 27 min (Replikation 7.397 s, Bloecke 1-9 GEBREMST) | par.22a |

## 7. PUSH-STAND

**25 Commits vor `origin/main`, NICHT gepusht** (`git rev-list --count origin/main..HEAD` am 2026-10-09; letzter Commit
`a3fa6be3`, 2026-10-09 16:50:03). Kein Push ohne Anweisung. Vor einem Push: `cargo test --release --no-run` (CLAUDE.md,
pre-push-Hook) und der Pfad-/Namens-Pruefbefehl aus CLAUDE.md.

Im Arbeitsbaum, nicht committet: `player_profiles.json` (veraendert, Server-Seite) und `player_profiles.json.bak`
(unverfolgt); beide nie committen. Die Neufassung von `evaluations/STATUS.md` und das Kapitelpaar in `archive/history.md` sind mit dem
Abschluss-Commit vom 2026-10-09 abends eingecheckt.
