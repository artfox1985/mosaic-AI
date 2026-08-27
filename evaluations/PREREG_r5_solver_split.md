<!-- STATUS: OFFEN | Frage: Wird der R5-Loeser in einen EINGEFRORENEN Anker-Loeser (Heuristik) und einen frei entwickelbaren Netz-Loeser getrennt -- und laesst sich der Value-Kopf fuer Runde 5 gut kalibrieren (Steigungs-Metrik der R5-Kalibrierung)? | Beleg: ENTWURF 2026-08-22, Nutzer-Entscheid ("dann machen wir einen eigenen solver fuer den heuristik anker. und schauen dass wir den value kopf gut kalibrieren fuer runde 5."), nichts gebaut; Vorarbeiten par.2a (Bau-Kartierung) und par.3a (Pruefpunkt: Champion-Ownership UNTRAINIERT) am 2026-08-22 erledigt; par.2b/2c: Teil A GEBAUT und ABGENOMMEN (2026-08-23: Suite 484/0, Paritaets-Hash 8c6684ff haelt vor/nach Wheel-Neubau, Wheel installiert) -- der Anker-Loeser ist aktiv und eingefroren. Teil B: Vierer-Vergleich GEMESSEN und ENTSCHIEDEN (par.3e, 2026-08-23): Value-Kopf gewinnt (Tau 0,762 k1-aktiv), alle drei Kandidaten signifikant schlechter -> BLEND-WEG GESCHLOSSEN, Teil B nur noch ueber Trainings-Eingriffe; Praezisierung: die R5-Schwaeche ist PLATTEN-Daempfung, nicht Gesamtwert; Arm-3-Vorklaerung par.3c ERLEDIGT (Karten-Lieferant: v21-b18 empfohlen, Ownership-Ziele kennen keine Traeger-Maskierung); neuer Anlass: Strukturbefund Spalten-Vollendung (STATUS 2026-08-23). Anlass: 200-Knoten-Beschneidung als moegliche Schwachstelle; jede R5-Verbesserung wuerde sonst den Anker mitverschieben (Leiter-Reset-Falle, gerade erst bezahlt). -->

# PREREG-SKELETT: R5-Loeser-Trennung (Anker eingefroren) + R5-Value-Kalibrierung

Stand **2026-08-22. ENTWURF, nichts gebaut, Plan-Zeitform.** Reihenfolge
gegenueber der laufenden Seeding-Kette ist Nutzer-Entscheid; die
Value-Kalibrierung (Teil B) profitiert vom Seeding-Ausgang und sollte
danach zugeschnitten werden.

## par.1 Anlass, mit den drei Messfakten

1. Die 200-Knoten-Beschneidung ist real, aber gemessen klein: 5,8/9,5/
   13,1 % Zugwahl-Aenderungen bei 400/1000/4000 Knoten; 81,4 % gegen
   84,8 % Orakel-Uebereinstimmung (200 gegen 4000; round5.rs-Modulkopf).
   Verbesserungsversuche sind legitim, die Erwartung ist kalibriert.
2. Der Value-Kopf ist GENAU in Runde 5 am schlechtesten: Platten-
   Steigung 0,06-0,09 statt ~1 (r5_value_calibration, Pflicht-
   diagnostik), Kopf-Konflikte ballen sich ausschliesslich in R5.
   Ein multiplikativer Blend am exakten Blatt wuerde diesen Fehler
   importieren -- falls Blend, dann additiver Korrekturterm fuer den
   UNGESEHENEN Rest, und erst nach Teil B.
3. Der Loeser ist heute mit dem Heuristik-ANKER geteilt (mcts.rs:746ff)
   -- jeder Eingriff ueber einen prozessglobalen Knopf verschiebt den
   Anker mit (OnceLock-Falle) und entwertet die frisch verankerte
   Leiter. DESHALB der Nutzer-Entscheid: eigener, EINGEFRORENER
   Anker-Loeser.

## par.2 Teil A: die Trennung (Bau-Skizze)

- `round5_anchor.rs` = eingefrorene Kopie des heutigen Standes
  (c83fb35-Semantik inkl. Zufallsknoten); NUR der Heuristik-Pfad
  (mcts.rs) ruft ihn. "EINFRIEREN, NICHT REPARIEREN" gilt dort ab dann
  woertlich -- gleiche Philosophie wie wertung_progress/A4.
- `round5.rs` bleibt der NETZ-Loeser und darf sich entwickeln
  (Kandidaten-Arme, je einzeln und per-Agent verdrahtet, KEINE
  Env-Knoepfe fuer Seitigkeit): (a) Knotenbudget netzseitig anheben
  (200 war Tragbarkeits-, keine Suffizienzzahl), (b) Netz-Policy als
  Zugsortierung (Stage-3-Praezedenz; Recherche S2), (c) additiver
  Value-Korrekturterm (erst nach Teil B).
- **Abnahme der Trennung selbst**: byte-identisches Verhalten beider
  Loeser am Trenntag (Ordnungstests beider Fundstellen, A4-v2-Fixture
  bleibt gueltig und wechselt auf den Anker-Loeser als Pruefziel,
  Suite gruen, Paritaets-Hash haelt, Wheel neu). Danach ist der Anker
  gegen JEDE R5-Weiterentwicklung immun -- die Elo-Leiter bleibt
  stehen; nur Netz-Kanten-Interpretationen aendern sich mit dem
  jeweiligen Arm (normale Gating-Logik).
- Doppelpflege-Kosten sind der bewusste Preis; der Anker-Loeser
  bekommt einen NICHT-ANFASSEN-Kopfkommentar mit Verweis hierher.

### par.2a NACHTRAG: Bau-Vorbereitung (2026-08-22, Kartierung am Code, NICHTS gebaut; parallel zur laufenden Seeding-Generierung, reine Lesearbeit)

- **round5.rs HEAD == c83fb35** (git log: c83fb35 ist der letzte Commit,
  der die Datei anfasst). Eine heute gezogene Kopie waere also exakt die
  c83fb35-Semantik, auf der die frische Elo-Leiter steht.
- **Heuristik-Pfad (wuerde auf `round5_anchor` umgehaengt): genau drei
  Einstiege**, alle in mcts.rs -- Zeile 746 (`root_child_stats`), 777
  und 796; genutzt werden dort nur `applies`, `choose_action` und
  `choose_action_with_analysis`. Ordnungstest der Fundstelle:
  mcts.rs:1438.
- **Netz-Pfad (bliebe auf round5.rs)**: net_mcts.rs 4732/4778/4819/
  4884/5064 (alle hinter `net_solver_enabled`) plus 5550/5559
  (Orakel-/Deadline-Vergleich).
- **Alle uebrigen Konsumenten sind netz-/selfplay-seitig** und blieben
  am entwickelbaren Loeser: `exact_round5_outcome` (round_transition
  .rs/_deep.rs, self_play.rs:2914), `player_total_exact` (tiling_
  solver.rs). mcts.rs nutzt davon nichts (Grep ueber engine/src,
  2026-08-22) -- der Trennschnitt ist also klein und scharf.
- **Env-Knopf-Bestand**: `round5::net_solver_enabled` (round5.rs:180,
  OnceLock auf `MOSAIC_R5_NET_SOLVER`, Default AN) gatet nur den
  NETZ-Pfad; die drei mcts.rs-Einstiege sind ungegatet. Nach der
  Trennung waere der Anker-Pfad knopffrei fest verdrahtet (par.2-Regel
  "keine Env-Knoepfe fuer Seitigkeit").
- **Nicht parallel fahrbar**: Abnahme (Suite, Paritaets-Hash, Wheel neu)
  braucht Mehrkern-Bau und Testlaeufe -- fruehester Slot nach Ende der
  laufenden Korpus-Generierung. Baubeginn bleibt Nutzer-Entscheid
  (par.4 Punkt 1).

### par.2b NACHTRAG: Teil A VORGESCHRIEBEN, UNKOMPILIERT (2026-08-22, Sonnet-Agent; Koordinator-Nachpruefung der tragenden Punkte per diff/grep)

- Neu `engine/src/round5_anchor.rs`: Kopie von round5.rs mit exakt
  ZWEI Aenderungen (diff-verifiziert, 2 Hunks): NICHT-ANFASSEN-
  Modulkopf + `net_solver_enabled` entfernt (Anker knopffrei; die
  Funktion wird nur extern von net_mcts.rs genutzt, Grep-verifiziert).
- `engine/src/lib.rs:33` registriert das Modul; mcts.rs haengt an
  round5_anchor (drei Einstiege + Ordnungstest, `round5::` in mcts.rs
  = 0 Treffer, Grep-verifiziert); A4-v2-Fixture-Test prueft damit den
  Anker-Pfad. round5.rs/net_mcts.rs und alle uebrigen Konsumenten
  unveraendert (git status).
- **NICHT kompiliert, NICHT getestet** (Sperre wegen laufender
  Generierung). Abnahme laut par.2 steht KOMPLETT aus: cargo-Suite,
  Paritaets-Hash 8c6684ff, Wheel-Neubau, Byte-Identitaet am Trenntag.
  Bis dahin gilt der Arbeitsstand als ungeprueft.

### par.2c ABNAHME TEIL A BESTANDEN (2026-08-23; Agent-Lauf, Paritaets-Hash vom Koordinator unabhaengig nachgemessen)

- **cargo-Suite 484/0** (26 ignorierte), inkl. der round5_anchor-Tests
  (27 Treffer im Log). Pruefstelle `logs/cargo_suite_r5split_20260823.log`.
- **Paritaets-Hash HAELT:** `tools/parity_probe.py` liefert VOR dem
  Wheel-Neubau, NACH Neubau+Installation und in einer unabhaengigen
  Koordinator-Nachmessung identisch
  8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423.
  Pruefstellen `logs/r5split_parity_{before,after}_20260823.log`.
- **Wheel neu gebaut und installiert** (`python -m maturin build
  --release`, 24,4 s, Exit 0; pip force-reinstall Exit 0; Logs
  `logs/r5split_{maturin_build,pip_install}_20260823.log`). Zwei
  erwartete dead_code-Warnungen im Anker (exact_round5_outcome/
  outcome_diff ungenutzt -- konsistent mit par.2a: der Anker bedient
  nur die drei mcts.rs-Einstiege).
- **Abdeckungs-Hinweis:** die Paritaets-Sonde deckt den NETZ-Suchpfad
  (net_search_state_json); der Heuristik-Pfad ist ueber die
  A4-v2-Fixture und die Ordnungstests in der Suite abgedeckt
  (mcts.rs-Testumhaengung, par.2b). Damit sind alle par.2-Abnahme-
  punkte erbracht: der Anker ist ab jetzt gegen jede R5-Weiter-
  entwicklung immun, die Elo-Leiter steht.

## par.3 Teil B: R5-Value-Kalibrierung (Ziel-Skizze)

- **Metrik ist registriert und existiert**: die Steigung der
  r5_value_calibration (heute 0,06-0,09; "gut kalibriert" heisst
  Steigung nahe 1 OHNE Staerkeverlust). Kennlinien-Caveat 0,316 aus
  dem Alt-Befund beachten.
- Zuschnitt NACH dem Seeding-Ausgang (der Arm koennte die Daempfung
  bereits bewegen -- erst messen, dann bauen). Kandidaten, im Wissen
  um die GESCHLOSSENEN Nachbarn (Vollendbarkeits-Kalibrierungen
  uebertragen nicht; Ziel-Wechsel am Wertkopf durchgemessen):
  R5-Sample-Gewichtung im Value-Loss, rundenspezifische
  Ausgangs-Kalibrierung (Platt je Runde statt global), Nutzung des
  vorhandenen endgame_margin-Kopfs als KALIBRIER-Referenz (nicht als
  Such-Input). Auswahl + Vorabregeln beim Zuschnitt.
- **Erster Pruefschritt (Nutzer-Einsicht 2026-08-22):** die R5-Schwaeche
  ist ein KANAL-Problem (Platten-Varianz fehlt in den Daten, Bonus-
  Nichtlinearitaet, kein Selektionsdruck weil die Suche den Kopf in R5
  nie fragt), kein Schwierigkeits-Problem -- R5 hat zugleich die
  billigste exakte Supervision des Spiels (den Solver). Deshalb VOR
  jedem Trainings-Eingriff messen, ob der vorhandene
  `endgame_margin`-Kopf (destilliert den Solver-Wurzelwert, Val-MSE
  ~0,018 in den 2026-08-Trainings) auf der r5_value_calibration-Skala
  bereits die Steigung liefert, die dem Value-Kopf fehlt -- dann waere
  ER der Kandidat fuer den spaeteren Blend-Arm, ohne neues Training.
- **Erweiterung (Nutzer 2026-08-22): der Pruefschritt wird ein
  VIERER-VERGLEICH statt einer Einzelpruefung.** Fuer R5 stehen im Netz
  bereit: (1) endgame_margin (Solver-Destillat), (2) points MINUS
  opp_points (direkte Margen-Prognose in Punkten, R² ~0,52/0,51),
  (3) Ownership-Karte -> erwartete Plattenpunkte je Kriterium (die
  E_k-Maschinerie des Verbraucher-Strangs existiert; als STAERKE-Hebel
  tot, aber R5 ist der Ort, wo die Karte am berechenbarsten ist --
  direkter Angriff auf den verhungerten Platten-Kanal), (4) der
  Value-Kopf selbst. Offline auf R5-Zustaenden gegen exakte
  Solver-Grundwahrheit, gleiche Kalibrier-Skala, bester Kopf wird
  Blend-Kandidat. PRUEFPUNKT vorab: der amtierende Champion lief mit
  OWNERSHIP_WEIGHT=0 -- ob sein Ownership-Ausgang trainiert ist oder
  nur die b-Serie brauchbare Karten liefert, ist VOR dem Vergleich zu
  klaeren (Regel 0).

### par.3a NACHTRAG: PRUEFPUNKT GEKLAERT (2026-08-22, reine Datei-/Historienpruefung parallel zur Seeding-Generierung)

**Der Ownership-Ausgang des amtierenden Champions
(alphazero_v21_2d_brierbest) ist UNTRAINIERT.** Beweiskette:

1. Der ONNX-Graph HAT den Ausgang (`ownership` in der Output-Liste;
   onnx-Graph-Parse 2026-08-22).
2. Sein Trainings-Manifest (`manifest_train_v21_2d_20260809_004805.
   json`) traegt `ownership_weight: null` -> config-Default greift
   (train.py:622).
3. Der Default ist seit Einfuehrung des Kopfes durchgehend **0.0**
   (config.py:79; git -S findet nur 3b21674/2026-07-28 und
   104488f/2026-08-10, beide Staende 0.0). Bei 0.0 fliesst kein
   own_loss (train.py:1085ff).
4. Die gesamte Warm-Start-Linie lief ebenso mit `null` -> 0.0:
   v19_2d (<- v18_2d), v19_2d_opp, v20_2d_opp (Manifeste gelesen,
   2026-08-22). Der Kopf hat also NIE einen Gradienten gesehen; der
   Ausgang ist durchgeschleppte Zufallsinitialisierung.

**Folgerung fuer den Vierer-Vergleich:** Arm (3) braucht die Karte
eines b-Serie-/own_w-Modells (b18-b24: own_w 1.0-2.0; own_w01-w1:
0.1-1.0; alle Manifeste gelesen). Deren TRAEGER-Status (ownership-
tragendes Korpus, bekannte Maskierungs-Falle) ist beim Zuschnitt je
Kandidat einzeln zu pruefen. Arm (4) "Value-Kopf selbst" und Arme
(1)/(2) sind vom Befund unberuehrt.

### par.3b VORHANDENE KOPF-VERDRAHTUNGEN AM TILING-SOLVER (Nachtrag 2026-08-22, am Code verifiziert -- Kontext fuer Teil B, KEIN R5-Thema)

Zur Abgrenzung (Nutzer-Frage): das Tiling in R5 braucht keinen Kopf
(der Loeser maximiert die exakte Endwertung mit); die Kopf-Frage im
Tiling ist eine R1-4-Frage. Dort ist aber mehr verdrahtet, als live
wirkt (self_play.rs:928ff, docs/knobs.md:49-52):

| Eingang | Stand |
|---|---|
| Value-Kopf (P(Sieg) des End-Tiling-Zustands, #37-Stichentscheid) | AKTIV in Produktion (einziger live wirkende Netz-Input) |
| Points-Kopf | verdrahtet (Nutzer-Auftrag 2026-08-12), Knopf Default 0,0 |
| Ownership-Karte (marginale Feldwerte, `MOSAIC_OWNERSHIP_TILING_W`) | verdrahtet (Verbraucher-Strang), Default 0 nach dem Kampagnen-Null |
| Plattenterm exakte Endwertung (`MOSAIC_TILING_PLATTEN_W/_GEW`, ohne Netz) | verdrahtet, Default 0 |

Einordnung: die Ownership-Tiling-Kopplung fiel in der R1-4-STAERKE-
Arena mit dem Verbraucher-Strang -- das sagt nichts ueber die Karte
als R5-BEWERTER (Teil-B-Vierer-Vergleich). Kroent der Vergleich die
Ownership->E_k-Schiene, existiert die Tiling-Seite dafuer bereits
fertig gebaut; nach par.3a-Befund kaemen die Karten dann aus der
b-Serie (Champion-Ausgang untrainiert) bzw. aus einem kuenftig wieder
ownership-tragend trainierten Netz.

### par.3c ARM-3-VORKLAERUNG: KARTEN-LIEFERANT (2026-08-23, Agenten-Recherche, Kernpunkte vom Koordinator an Manifest und neural_net.py nachgeprueft)

- **Ownership-Ziele kennen KEINE Traeger-Maskierung:** Labels entstehen
  je abgeschlossener Partie aus dem letzten Record
  (neural_net.py:1008ff, _final_ownership_by_game) fuer ALLE geladenen
  Dateien; die Sieben-Laeufe-Falle war reine POLICY-Maskierung
  ("Value-, Punkte- und Ownership-Ziele liefen normal durch",
  archive/history.md). Alle vier geprueften Kandidaten (b18, b22, b24,
  own_w1) trainierten den Kopf also unmaskiert mit Gewicht 1,0 und
  Konjunktionskopf (140 Ziele).
- **Empfohlener Lieferant: v21-b18** (Manifest nachgeprueft:
  ownership_weight 1.0, conjunction_head true, Warm Start direkt vom
  Champion, KEIN Frozen Trunk, Ownership-Korpus als extra_data_dir).
  Gegenkandidaten je einzeln vorbelastet: b22 = Frozen-Trunk-Weg
  registriert NEGATIV (schlechterer Own-Val); b24 = Reach-Relabeling
  der Spalten-Atome, Zielwechsel registriert NICHT-ERFOLG; own_w1 =
  einer der policy-maskierten Laeufe (fuer die Karte egal, als
  Gesamt-Checkpoint Altlast). Alternative mit bestem gemessenem
  Own-Val: v21-b19 (0,2994; Manifest hier NICHT gelesen -- vor
  Verwendung pruefen).
- **Einsatz-Pflichten:** MOSAIC_OWNERSHIP_CONJ=1 (sonst Produktform-
  Rueckfall, net_mcts.rs:1909ff); und der Praezedenz-Caveat der
  Feld-Kopf-Messung 2026-08-18 (gemessen an b19): auch ein korrekt
  trainierter Kopf "sieht die Absicht kaum" -- fuer den
  Vierer-Vergleich zaehlt aber zunaechst nur die R5-KALIBRIER-Skala
  gegen exakte Solver-Grundwahrheit, nicht die Absichts-Frage.
- **Neuer Anlass-Kontext:** der Strukturbefund vom 2026-08-23
  (STATUS: Champion vollendet keine Spalten, 0,55 Hoehe-5-Spalten je
  Partie bleiben stehen, Erreichen zu 78 % in R4/R5) macht Teil B
  dringlicher: die Vollendungsentscheidungen fallen genau in die
  Runden der schlechtesten Value-Kalibrierung.

### par.3d VORABREGELN VIERER-VERGLEICH (registriert 2026-08-23 VOR dem Lauf; Ausfuehrung nach Stufe 0 der Horizont-Frage)

- **Stellungsstichprobe:** ~200 Runde-5-Startzustaende aus fertigen
  Partien vorhandener Korpora/Artefakte (pkl-Records mit voller
  Information), stratifiziert nach Punktedifferenz-Terzilen und
  k1-Plattenlage (k1-aktive Teilmenge separat ausgewiesen, Ziel
  >= 60 Zustaende). Stichproben-Seed und Quelldateien im Artefakt
  protokollieren.
- **Grundwahrheit:** exakter Solver-Wurzelwert je Zustand (Marge aus
  Netz-Loeser-Pfad round5.rs; NICHT der Anker -- der bleibt
  unangetastet).
- **Vier Koepfe, alle auf denselben Zustaenden:** (1) endgame_margin
  des Champions; (2) points MINUS opp_points des Champions; (3)
  E_k-Plattenpunkte aus der Ownership-Karte von v21-b18 (par.3c;
  MOSAIC_OWNERSHIP_CONJ=1 Pflicht); (4) Value-Kopf des Champions
  (WDL-Erwartungswert). Je Kopf: Rangkorrelation (Kendall-Tau) zur
  Solver-Marge und Steigung der linearen Kennlinie
  (r5_value_calibration-Muster; Kennlinien-Caveat 0,316 beachten).
- **Lesart VORAB:** primaeres Kriterium ist Tau auf der k1-aktiven
  Teilmenge; Blend-Kandidat wird nur ein Kopf, der den Value-Kopf
  dort KLAR schlaegt (gepaarte Differenz, Vorzeichentest p < 0,05).
  Schlaegt keiner den Value-Kopf, ist der Blend-Weg fuer Teil B
  geschlossen und es bleiben Trainings-Eingriffe (R5-Gewichtung,
  Platt je Runde) -- auch das waere ein registrierfaehiges Ergebnis.
- **Legalitaets-Stufe der Vollendungs-Sonde** (gleiches Lastfenster,
  danach): je Hoehe-5-Fall aus column_completion_gap_probe per Engine
  pruefen, ob im Restfenster eine legale Vollendung existierte
  (Kachelverfuegbarkeit/Platzierbarkeit); ausgewiesen wird die
  ECHTE verpasste Quote (legal moeglich und nicht gespielt) je Seite.
  QUARANTAENE-Vorgabe: Zustandsrekonstruktion ausschliesslich ueber
  den replay-exakten Pfad (PREREG_action_id_logging), NIE ueber den
  Referee-/Worker-Pfad -- der traegt bis zum gruenen Kernbeweis
  (Kapselungs-Prereg par.8d) keine Messungen.

### par.3e ERGEBNIS VIERER-VERGLEICH + VERDIKT (2026-08-23; Agent, Zahlen vom Koordinator am Artefakt `evaluations/artifacts/r5_four_head_comparison.json` nachgemessen)

200 R5-Startzustaende (70 k1-aktiv), Grundwahrheit = exakte
Solver-Wurzelmarge ueber den NETZ-Loeserpfad (ab_value):

| Kopf | Tau gesamt | Tau k1-aktiv | Steigung k1-aktiv |
|---|---|---|---|
| endgame_margin | 0,745 | 0,735 | 0,263 |
| points - opp_points | 0,748 | 0,737 | 1,131 |
| E_k-Marge (b18, Konjunktion) | 0,364 | **0,278** | 0,099 |
| **Value-Kopf (WDL)** | **0,761** | **0,762** | 0,874 |

**VERDIKT nach par.3d-Lesart: der Blend-Weg ist GESCHLOSSEN.** Kein
Kandidat schlaegt den Value-Kopf auf dem primaeren Kriterium; alle drei
sind im gepaarten Vorzeichentest SIGNIFIKANT SCHLECHTER (endgame_margin
14:56, p=4,3e-7; points-opp 22:48, p=0,0025; E_k 16:54, p=5,9e-6).
Teil B laeuft damit ueber Trainings-Eingriffe (R5-Sample-Gewichtung,
Platt je Runde), nicht ueber einen Blend.

**WICHTIGE PRAEZISIERUNG von par.1 Punkt 2:** der Value-Kopf ist in
Runde 5 NICHT allgemein schwach -- er ordnet die Solver-Marge sehr gut
(Tau 0,76) und ist auf der Gesamtwert-Skala fast richtig geeicht
(Steigung 0,87-0,89). Die registrierten 0,06-0,09 sind die
PLATTEN-Steigung: der Kopf sieht den Gesamtwert, aber nicht den
Platten-/Spaltenanteil darin. Kuenftige Formulierungen muessen das
trennen.

**Nebenbefund zum Ownership-Kanal:** die E_k-Marge aus der b18-Karte
ist der mit Abstand SCHWAECHSTE Kopf (Tau 0,278, Steigung 0,099) --
und das im Konjunktionspfad, hart gegatet (Funktion bricht bei
<140-breitem Kopf ab, statt in die Produktform zurueckzufallen). Der
Plattenkanal traegt also auch dort nichts, wo er am berechenbarsten
sein sollte (par.3-Erwartung widerlegt).

## par.4 OFFEN (Nutzer, beim Aufgreifen)

1. Zeitpunkt von Teil A (unabhaengig von Seeding baubar) gegen die
   laufende Kette.
2. Welche Netz-Loeser-Arme in welcher Reihenfolge (a/b/c), je mit
   Vorzeichen-Sonde vor jeder Arena (r5_chance-Muster; eine Arena fuer
   ~0,02-Punkte-Effekte waere eine erschlichene Freigabe).
3. Teil-B-Zuschnitt nach dem Seeding-Verdikt in
   `PREREG_start_position_seeding.md` **par.4c** (Verweis BERICHTIGT
   2026-08-27: hier stand "Seeding-par.7-Verdikt"; einen Abschnitt par.7 gibt
   es dort nicht -- nur die Zwischenueberschrift "par.7-Schwellen" innerhalb
   von par.4b, und die traegt die Schwellen, nicht das Verdikt. Das Verdikt
   steht in par.4c: Schwellen VERFEHLT, kein k1-Signal, kein Staerkepreis).
