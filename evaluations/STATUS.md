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

## 1. WAS GERADE LAEUFT (ZWISCHENBERICHT 2026-09-07, 06:05; Nutzer-Auftrag "fahr einfach durch und bereite mir einen zwischenbericht vor")

**Champion unveraendert: `v24-b06`** (Elo 1309, Modell `alphazero_v24-b06_brierbest.onnx`,
Spec `models/v24-b06_brierbest.spec.json`). **Maschine ist FREI, nichts laeuft.**
**Der Push ist offen: 84 Commits vor origin/main, Build gruen, Anker gruen.**
Chronik der Nacht: `night_run_20260902.md` ab dem Eintrag 2026-09-06, 22:35.

### Die vier Messergebnisse der Nacht, in der Reihenfolge ihrer Tragweite

**1. Die Erzeugung wirft mehr als die Haelfte des Spaltenbaus weg -- durch das Sampling der
Zugwahl** (`PREREG_search_path_remeasurements.md`, Messung 3-V). Vier Chargen zu je 200
Sockel-Partien, gleicher Generator, gleicher Seed, nur der Umschaltpunkt variiert:

| Umschaltpunkt | volle Spalten je Seite | Punkte | Strafleiste |
| --- | --- | --- | --- |
| aus (Bestand) | 0,1950 | 28,3 | 9,41 |
| 30 | 0,3000 | 36,5 | 7,80 |
| 12 | 0,4225 | 38,5 | 7,54 |
| **1 (durchgehend greedy)** | **0,5325** | **41,5** | **6,93** |

Die Reihe ist monoton, es gibt kein Zwischenoptimum. **Und die Vielfalt bleibt:** 399 von
400 Endbrettern distinkt (gegen 400 im Bestand), Zustandsvielfalt je Record unveraendert,
Policy-Entropie der Ziele sogar leicht hoeher. Auch die Ergebnisstreuung bleibt (Punkte-SD
15,2 gegen 17,9, Anteil knapper Partien identisch). **Damit ist die 0,19 der
Sockel-Klasse, die den ganzen v25-Streit um die Traeger-Kennzahl ausgeloest hatte, als
Temperatur-Artefakt erledigt** -- am Mix war nichts zu reparieren.

**2. Die Huellenform mit zweiter Zelle in Zeile 6 traegt, ueber zwei Seeds**
(`PREREG_geometric_envelope.md` par.8.15b/8.15c). Arm gegen Champion-Spec am selben Netz:

| | Seed 20261014 | Seed 20261013 | gepoolt |
| --- | --- | --- | --- |
| Siege | 85:75 | 92:68 | **177:143** (p 0,065) |
| volle Spalten (beide Richtungen) | 0,787 / 0,700 gegen 0,625 / 0,550 | 0,838 / 0,863 gegen 0,613 / 0,350 | vier von vier darueber |
| Kuppel-Bonus | 4,7 / 4,6 gegen 3,8 / 3,6 | 4,5 / 5,0 gegen 3,4 / 2,3 | **hoechster je gemessener Netz-Wert (5,0)** |

Die Siege sind knapp nicht signifikant, die Spalten eindeutig (groesste Differenz 0,863
gegen 0,350, weit ausserhalb der Block-SD-Spannweite identischer Aufbauten). Es ist der
erste Baustein seit K3-P, der Spalten HEBT statt sie zu kosten. Vorher waren alle vier
Knopf-Arme der Nacht negativ: K3-P2 71:89, K3-F 1,0 74:86, K3-F 0,5 77:83, beide 69:91.

**3. Der Betriebspunkt der Erzeugung ist bestaetigt, das Niveau ist gestiegen**
(`PREREG_search_depth_column_optimum.md` par.8b). Suchtiefen-Kurve am heutigen Champion:
@100 0,8200, @250 0,5075, @400 0,4975. Plateau weiter bei 100, Absturz so steil wie vor
drei Generationen; alle Punkte liegen 0,16 bis 0,20 hoeher als bei `v22-b05` (konfundiert:
anderes Netz UND Champion-Knopf). **Prozessregel-Antwort (par.8c): nicht je Generation
nachmessen, nur bei Aera-Wechseln** -- die Form hat sich ueber drei Generationen nicht
bewegt.

**4. Die gemessene Huelle bestaetigt die hergeleitete** (`geometric_envelope` par.8.15a).
Ueber 1.004 Endbretter: bei Kosten 56 deckt sich die haeufigkeitsoptimale Zellmenge in 20
von 21 Zellen mit dem Dreieck. Die zweite Zelle in Zeile 6 ist **Mensch-Verhalten** (0,909
gegen 0,362 der Netze) -- also ein ZIEL, keine Beschreibung des Ist-Zustands.

### Was gebaut und geprueft wurde

**`cargo test --release --lib`: 538 Tests, 0 rot.** Wheel installiert, Kontrakt unveraendert
`20b442a8164f748d`, **Anker-Drift und Konservierung je GRUEN** (1.763 Schritte).

| Baustein | Was | Prereg |
| --- | --- | --- |
| Huellenform | `envelope_hull_form` 1/2 als Spec-Pflichtfeld, alle Suchpfade | `geometric_envelope` par.8.15 |
| Pass-Zeile | `⏭️ <Name>: passt` plus `#a`-Zeile in beiden Pfaden | `action_id_logging` S2 (Luecke geschlossen) |
| Chip-Verbrauch | `(3 Plättchen: rot, gelb+blau, schwarz)` in der Vollendungs-Zeile | `pitfalls.md`-Nachtrag |
| Symbol | ueberall 🎴 statt 🎫 | Nutzer 2026-09-07, 01:30 |
| **Weg C** | eine Abweichung je Partie, aus breit gezogenen Kandidaten netzgefiltert | `start_position_seeding` par.9c/9e |
| **Aktionsabhaengige Temperatur** | `--action-temp`, Staffel wie im Heuristik-Pfad | `v25_window` par.14 |

**Replay-Nachweis in beide Richtungen:** das Altlog `claude_play/g01/game.log` (altes
Symbol, keine Pass-Zeile, kein Chip-Zusatz) laeuft ohne Divergenz durch, 5 Chip-Zeilen ueber
die neuen Toleranzen; die frischen Arena-Logs der Replikation ebenso. Der Replayer NUTZT die
Chip-Angabe jetzt, statt die Wahl zu raten -- der Vorfall vom 2026-08-29 kann fuer neue Logs
nicht wiederkehren.

### Was der Nutzer entscheiden muss

| # | Frage | Stand / Empfehlung | Kosten |
| --- | --- | --- | --- |
| 1 | **Huellenform 2 in die Champion-Spec?** | Spalten belegt (2 Seeds), Siege p 0,065. Entweder Gating mit SPRT wie K3-P am 2026-09-04, oder direkt in die v25-Erzeugung und die Staerke dort mitmessen | Gating rund 1,2 h |
| 2 | **Value-Klasse 8.000/0 oder 7.000/1.000** (par.11 B) | Empfehlung 8.000/0; nach Messung 3-V waeren die 1.000 gesampelten die einzige verrauschte Klasse und tragen laut Messung keine Vielfalt | 0 |
| 3 | **G-1-Sockel neu erzeugen?** (par.13a) | Empfehlung V1: die 1.350 Traeger neu, mit dem ALTEN Generator und neuem Betriebspunkt -- hebt die Traeger-Kennzahl von 0,392 auf 0,447 | +1,3 h |
| 4 | **Schwarm-Arm** (par.15) | Nutzer-Vorschlag: variable Temperatur 0,8-0,2 plus Weg C. Eigener Faktor, gehoert in einen eigenen Arm NACH den fuenf Sockel-Armen | Bau: eine Zeile in `action_temp_for` plus Knopfwert |
| 5 | **Messung 3-W** (Umschaltpunkt bis in die Arena) | registriert, rund 12 h -- entfaellt, wenn die fuenf v25-Arme ohnehin gefahren werden, weil S1 gegen S3 dieselbe Frage beantwortet | -- |

**Bereits entschieden in dieser Nacht:** Generator v25 = `v24-b06` mit Champion-Spec
(par.14a); Umschaltpunkt k = 1 und Abweichungsrate 1,0 (par.14b); Armstruktur S1 bis S5
(par.14); die neun Subagent-Partien pausiert bis v25.

### Was als Naechstes zu tun ist

1. **Push** (84 Commits, frei -- Build und Anker gruen).
2. **Zweite Maschine versorgen:** gleicher Commit UND gleiches Wheel; Pruefzeile und die
   fertigen Befehle stehen in `PREREG_v25_window.md` par.14c. Erwartet:
   `744 20b442a8164f748d 1 0.0`.
3. **Entscheid 1 (Huellenform)**, weil er in die Generator-Spec der Erzeugung eingeht.
4. **K5 "Reihe-6-Spezialfeld"** (`special_tile_yield` par.9) -- nicht gebaut. Es war
   bewusst hinter die Huellenform gestellt: mit zwei Huellenzellen in Zeile 6 hat das
   Spezialfeld zwei Zielplaetze, und der Kuppel-Bonus der Form (bis 5,0) liefert bereits
   einen Teil dessen, wofuer K5 gedacht war.
5. **Der Punkt bei 150 Sims** der Suchtiefen-Kurve fehlt (par.8c), rund 25 min -- nur
   noetig, wenn jemand den Betriebspunkt feiner ausloten will.

### Vorbehalte und eigene Fehler dieser Nacht (Regel 0)

- **Vier Koordinator-Fehler, alle im Chat berichtigt und in der Chronik vermerkt:** (a) "die
  tau-Messung wurde nie gefahren" -- falsch, Messung 3 lief am 2026-08-08 (H0 auf STAERKE,
  nicht auf Spalten); (b) "Weg B entspricht KataGos Branching" -- falsch, KataGo erzeugt
  keine zweite Trajektorie; (c) "die Streuung kommt von Dirichlet-Rauschen" -- falsch, die
  Suche ist Gumbel-basiert; (d) "der Schwarm ist rauschfrei und trotzdem spaltenreich, also
  braucht es keine Streuung" -- die Kennzahl der falschen Klasse, vom Nutzer korrigiert.
- **Ein Regelbruch:** die Kurven-Messung wurde mit umgeleiteter Ausgabe gestartet statt
  harness-getrackt. Der Lauf selbst war sauber und exklusiv; Sichtbarkeit wurde nachgeruestet.
- **Session-Ausfall 04:30-05:30** durch ein Rate-Limit. In der Zeit lief nichts; die alte
  Knopf-Kette am v23-Champion ist in ihren Deckel gelaufen, OHNE zu messen.
- **Ungemessen bleibt die Kernfrage:** ob ein aus dem besseren Material trainiertes Netz
  staerker spielt. Alle Zahlen oben sind Material- oder Suchkennzahlen. Der Schritt zur
  Arena kostet ein Training plus Gating.
- **`models/attic_20260906_k3p10_copies/`** liegt weiter, Loeschung nur auf pfadgenaue
  Freigabe. Ebenso `venv_measure_hullform/` (von mir angelegt, leer, nicht mehr gebraucht).
- **`static/`** traegt Aenderungen des Nutzers (GUI), von mir nicht angefasst und nicht
  committet.

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
