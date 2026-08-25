# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Alles Entschiedene und
jede ausfuehrliche Herleitung liegt in `../archive/history.md`; der
vollstaendige Stand vor dieser Neufassung steht dort im Kapitel
"Vollstaendiger STATUS-Stand vom 2026-08-25".

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

Neu gefasst am **2026-08-25** (Nutzer-Auftrag: STATUS war mit 1180 Zeilen
schwer lesbar geworden).

---

## DAS ZIEL (Leitstern)

Ein **staerkerer Spieler**, gemessen am direkten Duell. Der benannte Hebel ist
der **Plattenblick**: rund 10 Punkte je Partie bleiben liegen. Bei jeder
Priorisierung gilt die Frage -- was traegt das dazu bei?

## FOKUS-REGEL: NUR k1 (Nutzer-Entscheid 2026-08-18)

Gemessen wird auf **Kriterium 1** (vertikale Reihen, 7 Punkte je Spalte).
Andere Kriterien nur, wenn ein Zuschnitt sie ausdruecklich braucht -- dann mit
Begruendung.

---

## STAND JETZT (2026-08-25)

**Champion:** `v21_2d_brierbest`, Elo **1215** [1170, 1259] auf der
R5-Fix-Leiter. Kanten ueber die Fix-Grenze nie mischen.

**Es laeuft nichts.** Maschine frei. Die Parallelsitzung (`mosaic-ai-97`) hat
ihren Strang uebergeben und ist beendet.

**Wheel-Stand:** neu gebaut und installiert am 2026-08-25 nach der
Feature-Erweiterung; Paritaets-Hash `8c6684ffba06cf3e...` unveraendert, Suite
525/0.

### Heute fertig geworden

| Strang | Ergebnis | wo es steht |
| --- | --- | --- |
| **Erreichbarkeits-Eingaben fuers Netz** | GEBAUT und ABGENOMMEN. `INPUT_SIZE` 708 auf 714, `NUM_PLANES_CHANNELS` 76 auf 77; Champion rechnet bitgleich weiter | Commit `29fb1f1`, Abschnitt "Architektur" |
| **Artefakt-Umzug** | 176 JSON nach `evaluations/artifacts/`, 145 Code- und 158 Dokument-Verweise nachgezogen; danach auf Nutzer-Entscheid **aus dem Tracking genommen** | Commits `4e967e1`, `4a43b8d` |
| **Blindzieh-Regel: Urteil** | Die gebaute Stopp-Regel zieht ZU OFT -- rund 10 verschenkte Punkte je betroffenem Stapelzug | `PREREG_stack_draw_reservation_rule.md` par.5b |
| **Strafleisten-Aversion: Nachmessung** | Der registrierte Nullwert war eine Eigenschaft der RUNDE 1, nicht des Champions | `PREREG_floor_action_aversion.md` par.14 |
| **Heuristik v2 / Prio-Huelle** | Lehrer-Test positiv: Siegquote 0,373 gegen 0,256 und 0,128, volle Spalten 0,798 gegen 0,086, dabei weniger Strafpunkte | `PREREG_heuristic_v2_long_rows.md` par.10, par.18 |

---

## OFFEN, nach Reihenfolge

### 1. v22-Korpus mit dem v2-Lehrer -- NUTZER: "muessen wir noch was vorbereiten"

Der wichtigste offene Punkt und Voraussetzung fuer mehrere andere. Der Korpus
**ist** die Heuristik v2 (Nutzer-Klarstellung 2026-08-25), also ein
spaltenkompetenter Erzeuger (0,798 volle Spalten je Partie gegen 0,086).

Entscheide stehen bereits in `PREREG_heuristic_v2_long_rows.md` par.3b:
Ownership-Kopf **einschalten** statt umbauen, plus **w0-Kontrollarm auf
DEMSELBEN Korpus**. Ohne den Kontrollarm sind Kopf und Korpuswechsel
konfundiert und der Effekt ist nicht zuordenbar -- das ist die eine Bedingung,
die nicht wegfallen darf.

**Was daran haengt:** der Realisierungsabschlag und der Plattenwert der
Blindzieh-Regel (heute an v20 geeicht, mit Vorbehalt), der Shaping-Kopf
(par.3b) und die Einhuellende im 2D-Encoder -- alle drei waeren auf
plattenblindem Spiel geeicht, solange dieser Korpus fehlt.

#### Vorbereitung, in dieser Reihenfolge (Nutzer-Entscheid 2026-08-25)

Kriterium fuer "gehoert davor": es aendert, WAS der Generator tut, oder es ist
spaeter nur durch Neu-Erzeugen korrigierbar. Alles andere misst auf dem Korpus
und gehoert danach.

| # | Punkt | Stand |
| --- | --- | --- |
| 1 | **Blindzieh-Reparatur entscheiden** (gepaarte Arena, beide Arme) | Knopf gebaut, Arme fahrbar -- Entscheid steht aus |
| 2 | **Heuristik-Variante bis ins Self-Play durchreichen** | NICHT gebaut, blockiert alles Weitere |
| 3 | **Arena-Threadzahl geradeziehen** | eingetaktet, nicht gebaut |
| 4 | **Bootstrap-Horizont 2 gegen 3** auf einem kleinen v2-Ausschnitt | eingetaktet, `PREREG_bootstrap_horizon.md` par.9 |
| 5 | **Erzeugung mit dem HEUTIGEN Wheel** | erfuellt, darf nicht rueckwaerts passieren |

**Zu 1:** `resolve_and_apply_stack_draw` sitzt in `apply_chosen_action` und
laeuft damit in JEDEM Self-Play, auch im heuristischen. In den ~39 Prozent
Partien mit Kriterium 6 verbrennt die Bestandsfassung rund 11 Punkte je Partie
und treibt 58-66 Prozent der Ziehserien auf Punktestand 0. Das landet in den
Scores, den Trajektorien und damit in den **Value-Labels**. Wird v22 mit dem
Defekt erzeugt, traegt ihn jedes daraus trainierte Netz mit.

**Zu 2:** der Self-Play-Einstieg ist auf V1 festgenagelt
(`heuristik_variante: HeuristikVariante::V1`, `self_play.rs:2201`); nur die
Arena nimmt die Variante als Parameter. Ohne das Durchreichen gibt es keine
v2-Partien und damit weder Punkt 4 noch die Kampagne selbst.

**Zu 3:** ein 814-Partien-Lauf kostet sequenziell 2 h 48 min statt 35 min. Bei
einer Korpus-Kampagne ist das kein Schoenheitsfehler.

**Zu 5:** erst seit 2026-08-25 schreibt `serialize_player` `col_f_max` und
`cell_reachable_mask` ins Zustands-JSON. Ein frueher erzeugter Korpus haette
die Felder nicht, und die zwei neuen Eingaben waeren auf ihm tote Nullen --
die Rueckfallwerte sind 0,0. Aktuell erfuellt; wer das Wheel zurueckdreht,
zerstoert es still.

### 2. Reparatur der Blindzieh-Stopp-Regel (EINGETAKTET 2026-08-25)

Eingriff in den DEFAULT-Pfad, deshalb ausdruecklich eingetaktet.

**Der Defekt:** `self_play.rs:517-534` vergleicht `avg_remaining_type_value`
(Typmittelwert in [1, 3]) gegen `best_eval_for_tile` (absolutes Brettniveau,
mit Kriterium 6 stark negativ). Zwei Einheiten, ein Vergleich -- sobald das
Niveau negativ ist, ist die Weiterzieh-Bedingung fast immer erfuellt.

**Die Reparatur, ohne neue Formel:** `best_eval_for_tile` nimmt eine beliebige
Platte, also auch eine aus dem Restpool. Damit laesst sich beides in derselben
Einheit rechnen -- weiterziehen, solange
`E[max(best_eval(V_next) − max(best_eval(gezogene)), 0)] > 1`, Erwartungswert
ueber die Pool-Platten des Typs, den die sichtbare Rueckseite ansagt.

**Vorab zu klaeren:** (a) Kosten -- `best_eval_for_tile` laeuft ueber Slots
mal Rotationen, ueber den ganzen Restpool je Entscheidung ist das deutlich
teurer als der heutige Mittelwert; zu messen, BEVOR die Regel scharf gestellt
wird. (b) Knopf mit Default AUS, damit die Arena beide Arme fahren kann.

**Abnahme:** gepaarte Arena, Block-Ebene, SPRT auf informativen Paaren
(`tools/paired_gating.py`), **getrennt nach Plattensatz** -- in Partien ohne
Kriterium 6 ist die Ziehtiefe in allen drei untersuchten Regimen 1, dort kann
kein Unterschied entstehen.

### 3. Arena-Threadzahl geradeziehen (EINGETAKTET 2026-08-25, nicht gebaut)

`threads = 0` heisst in `run_heuristic_v1_vs_v2_arena` ALLE KERNE und in
`run_net_vs_heuristic_v2_arena` SEQUENZIELL (`self_play.rs:2866`,
`if num_threads <= 1`). Dieselbe Sonde mit derselben Zahl laeuft also einmal
12-fach und einmal einfach; am Lehrer-Test gemessen: 19,8 CPU-Minuten in 20,4
Wanduhr-Minuten bei 12 Kernen, Faktor 1,0.

**Vorsicht:** die Bedeutung von `0` umzudrehen aendert still JEDE
Bestandsaufrufstelle. Sauber ist ein gemeinsamer Helfer mit EINER
dokumentierten Konvention plus Nachweis der Ergebnisgleichheit auf einer
Stichprobe -- Partien sind je Seed unabhaengig, das ist zu ZEIGEN, nicht
anzunehmen.

### 4. JSON-Umzug: Restentscheid

Die Artefakte liegen jetzt in `evaluations/artifacts/` und sind **ungetrackt**
(`.gitignore`). Folge: ein frischer Klon hat die Messartefakte nicht, und
Preregs zitieren sie als Beleg. Bei deterministischen Sonden ist ein Lauf
wiederholbar (belegt: der Wiederholungslauf des Strafleisten-Tors war
byte-identisch), bei allem mit Netz-Zufall nicht ohne Weiteres.
Zurueckdrehen: `.gitignore`-Zeile entfernen und
`git add -f evaluations/artifacts`.

### 5. Weitere offene Straenge

| Strang | Datei | Zuschnitt |
| --- | --- | --- |
| **Shaping-Kopf statt Ownership-Kopf** | `PREREG_heuristic_v2_long_rows.md` par.3b | Vorregistriert, nicht gebaut. Sagt die Dreiecks-Abweichung voraus; zwei Kanaele, Abkling-Kurve. Braucht erst das v22-Korpus |
| **Einhuellende im 2D-Encoder** | – | Nutzer-Frage 2026-08-24, nicht registriert. Zusaetzliche Eingabeebene "Dreiecks-Zugehoerigkeit je Zelle"; additiv moeglich, aber nach par.3b |
| **R5-Netz-Loeser + R5-Value-Kalibrierung** | `PREREG_r5_solver_split.md` par.2, Teil B | Netz-Loeser-Arme und Vierer-Kopf-Vergleich. Zielmetrik `r5_value_calibration`-Steigung, heute 0,06-0,09 statt ~1. Arm 3 braucht ein b-Serie-Modell mit gepruefter Traegerschaft |
| **Seeding-Folgearm: Dosis** | `PREREG_start_position_seeding.md` | k=6 war die erste Dosis; hoehere Dosis naheliegend, nicht registriert |
| **UVFA-Regime-Eingabe** | `PREREG_uvfa_plate_regime.md` | par.8: Conditioning-Dropout und Leakage-Waechter sind PFLICHT. par.7-Entscheid steht aus |
| **Saettigende Score-Utility** | `PREREG_saturating_score_utility.md` | Tor gefahren, Verdikt DAZWISCHEN -- **Nutzer-Entscheid offen**: sigma-Kopf auf `points_val` oder auf ein TD-unberuehrtes Ziel |
| **Agenten-Kapselung: Ausbau** | `PREREG_agent_encapsulation.md` par.4 | Entschieden und gruen; offen nur der planbare Ausbau der restlichen ~31 Knoepfe ins SearchConfig, je Knopf ein Commit mit Paritaets-Gate |
| **#29-Instrument** | `PREREG_post34_package.md` | WARTET AUF POWER: braucht mindestens 6 arena-entschiedene Paare (Stand ~3) |
| **Rundenuebergang bemustern** | `PREREG_round_transition_search_sampling.md` | Nichts gemessen. Zusatz aus der externen Recherche: robuste Aggregatoren (Median, gestutztes/winsorisiertes Mittel) statt des arithmetischen |
| **Risikosensitive Blatt-Utility** | `PREREG_risk_sensitive_leaf_utility.md` | Nichts gemessen; `points_dist` ist abgeschaltet, der Champion traegt den Kopf nicht |
| **Blindziehung: Suche und Merkmale** | `PREREG_chance_nodes.md` Teil B1, `PREREG_stack_top_feature.md` | Beide geparkt. B1 gibt der SUCHE die korrekte Peek-Bewertung, das Merkmal gibt dem NETZ die sichtbare Rueckseite |
| #31 / #38 / #39 | – | geparkt, Arbeitskreis "Spaeter"; Beschreibungen im Archiv |
| **v22-Fenster (Rotation)** | `PREREG_v22_window.md` | Design auf Halde, nicht eingeplant. NICHT zu verwechseln mit dem v2-Lehrer-Korpus unter Punkt 1 |

**Geschlossen, nicht neu vorschlagen:** Q-Skalierungs-Option, jeder
Suchparadigmen-Wechsel (zwei externe Recherchen), Mehrfach-Determinisierung
(`PREREG_ismcts_determinizations.md`: k=4 faellt unter zwei Anordnungen
signifikant ab), Phasenfaktor, Vollendbarkeits-Relaxation im Routing und die
zwei Punktekarten (`PREREG_heuristic_v2_long_rows.md` par.11-16),
`PREREG_long_row_payoff.md` B1, `PREREG_bootstrap_horizon.md` (beide Arme).

---

## OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Stand |
| --- | --- |
| **v22 vorbereiten** | Nutzer-Ansage 2026-08-25: "dafuer muessen wir noch was vorbereiten" -- was genau, ist offen |
| **Saettigende Score-Utility** | Verdikt DAZWISCHEN, kein Automatismus vorgesehen |
| **Stoerungs-Baustein Stufe 2** | gehoert zum Moon-Order-Kopf, keine Einzelentscheidung mehr |
| **Push** | NIE ohne ausdrueckliche Anweisung; Stand wird als "n Commits voraus" gemeldet |
| **Asym-Korpus** | bleibt lokal, Trainingsinput fuer Seeding und UVFA |
| **Fester Bewertungssatz** | 300 Dateien / 3000 Partien in `data/holdout/`, fertig 2026-08-18 |

---

## STRUKTURBEFUNDE, die weitergelten

- **Der Champion vollendet keine Spalten**, und der Grund ist Verteilung, nicht
  Versorgung: eine volle Spalte kostet 21 Zellen, das Netz verbraucht 42,7 und
  truege gleichverteilt 2,03 Spalten statt 0,10.
- **Die Dreiecksform ist die MACHBARKEITSHUELLE, keine aesthetische Wahl.**
  Erlaubt ist `r + c <= 5`, also 21 Zellen -- dieselbe 21, die eine volle
  Spalte kostet.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich**: sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je Runde
  ab -- fuenf Steine fuer sechs Zellen. Spalten haben das Problem nicht.
- **Der Durchbruch kam vom Platzierungs-ROUTING, nicht von Bewertungstermen.**
  `best_first_step_inner` waehlt nach reinen Sofortpunkten
  (`tiling_solver.rs:49-56`) und warf jede Draft-seitige Absicht wieder weg.
- **Erste unkontaminierte Referenz**: zehn Mensch-gegen-Netz-Partien in
  `static/log/`, der Mensch gewinnt 8 von 9 und schliesst **1,80 volle
  Spalten** je Partie gegen 0,10 des Netzes. Platzierungspunkte sind dabei ein
  Gleichstand (54,9 gegen 55,8) -- der Vorsprung sitzt bei den Spezialfliesen.
- **Realisierungsprofil eines plattenbewussten Spielers** (dieselben zehn
  Partien, Platzierungen je Rasterreihe): Mensch 3,60 / 3,30 / 3,20 / 2,60 /
  2,30 / 1,70 gegen Netz 4,70 / 4,70 / 3,30 / 2,30 / 1,10 / 0,50. **Gleiche
  Summe, andere Verteilung** -- der Mensch tauscht kurze Reihen gegen lange
  (Reihe 5 und 6: Faktor 2,7 bzw. 2,9 gegenueber dem v20-Selbstspiel).
- **B1-Vorgabe fuer jeden Nachfolge-Arm**: wer die Initiierung hebt, ohne die
  Vollendungsquote deutlich ueber 0,53 zu bringen, wiederholt B1.
- **Blindzieh-Regel**: bei Wertungsplatte 6 (Code-Index 6, Spezialfelder --
  das EINZIGE negative Kriterium) laeuft die gebaute Stopp-Regel das
  Punktekonto leer. Ohne Platte 6 haben 92-95 Prozent der Ziehserien Tiefe 1
  (bei Mensch gegen KI 25 von 25); mit ihr enden 58-66 Prozent der Serien bei
  Punktestand 0. Auf konstruierten Brettern zieht sie 9 bis 13 mal, wo die
  optimale Regel 1 sagt. **Spaltenbau behebt das NICHT** -- Kriterium 1 zahlt
  quadratisch `7*(f/6)^2`, das Spezialfeld-Defizit kostet linear -3 je Feld;
  eine volle Spalte gleicht gerade zwei leere Spezialfelder aus.
- **Methodische Lehre**: aus "Eingriff X in Richtung Y verliert" folgt NICHT
  "Y ist falsch" -- nur, dass X in diesem Zustand verliert. Es fehlt die
  Kontrollgruppe: ein Agent, der Y KANN.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch, drei in der
  Parallelsitzung und eine hier (Kriterium 6 "startet bei -27": falsch,
  `special_empty` zaehlt nur Spezialfelder auf bereits GELEGTEN Platten).

---

## LAUFZEITEN (gemessen, nicht geschaetzt)

Planungsgroessen. Die belastbaren Zahlen stehen je Lauf im Artefakt
(`laufzeit`-Block, Pflichtfeld seit 2026-08-25). Wer eine Zeile ergaenzt,
traegt GEMESSENES ein.

| Aufbau | Umfang | Threads | Wanduhr |
| --- | --- | --- | --- |
| Heuristik gegen Heuristik, 150 Sims (`v2_envelope_arena.py`) | 160 Partien | 0 = alle 12 Kerne | **21,9 s** |
| dito, Rauchtest | 20 Partien | alle Kerne | **4,1 s** |
| Netz@400 gegen Heuristik@150 (`v2_teacher_arena.py`), je Partie | – | 0 = **sequenziell** | **12,357 s** |
| dito | – | 11 | **2,575 s** |
| dito, voller Lauf | 814 Partien | 0 = sequenziell | ~2 h 48 min |
| dito | 814 Partien | 11 | ~35 min |
| Strafleisten-Tor (`floor_action_aversion_gate.py`), 240 Stellungen, sims=200 | – | – | **~7 min** |
| `cargo test --release --lib` (volle Suite) | 525 Tests | – | **~72 s** |
| Wheel-Bau (`maturin build --release`) plus Installation | – | – | **~30 s** |

**Parallelisierung ist ergebnisneutral, gemessen statt angenommen** (20 Seeds
beidseitig): Siegquote 0,450, volle Spalten 1,200 und Punkte 55,0 in BEIDEN
Faellen identisch, bei 4,8-fachem Tempo. Grund:
`PREREG_search_rng_split.md` -- jede Partie haengt an ihrem eigenen,
abgeleiteten Suchstrom.

---

## FALLEN (aus echten Vorfaellen)

- **CPU-Nebenlast verstuemmelt Arena-Partien** (2026-08-20). Derselbe
  8-Partien-Smoke lieferte unter Last zwei verschiedene Ergebnisse (eine
  Partie endete 3:1), ohne Last dreimal byte-identisch. **Arena-Messungen
  laufen EXKLUSIV** -- keine zweite Arena, keine Sonde mit Suchlauf, kein
  Training, auch kein `cargo`-Lauf. Determinismus-Checks zaehlen nur unter
  denselben Lastbedingungen wie die Messung.
- **"Erste N je Datei" ist ein stiller Rundenfilter** (2026-08-25). Sonden,
  die je Datei die ersten N qualifizierenden Datensaetze nehmen, ziehen
  Fruehspiel-Stellungen -- Datensaetze stehen in Zugreihenfolge.
  `floor_action_aversion_gate.py` hatte dadurch 268 von 280 Stellungen in
  Runde 1 und ein daraus abgeleitetes Verdikt, das nur fuer Runde 1 galt;
  repariert (`rounds=`/`seed=`, Bestandsauswahl byte-identisch erhalten).
  **Gleiches Muster, gleiche Wirkung, NICHT repariert:
  `long_row_init_knob_effect.py` misst ausschliesslich Runde 1** (alle 240
  Stellungen). Gegenprobe: `long_row_prior_gate.py` hat dasselbe Muster, aber
  einen groesseren Deckel und ist unauffaellig (12/105/82/61) -- die Falle
  haengt am Verhaeltnis Deckel zu Trefferdichte.
- **Python schreibt auf Windows still CRLF** (2026-08-25). Ein Skript mit
  `write_text` wandelte in 137 Dateien LF in CRLF; in einer Datei waren das
  971 Byte Zuwachs bei zwei geaenderten Zeilen. `git diff` zeigte wegen der
  Normalisierung weiter zwei Zeilen -- aufgefallen ist es nur an der
  Datei-Groessen-Ratsche. Wer so ein Skript schreibt: `newline` auf LF setzen.
- **Wheel nach Engine-Aenderung neu bauen.** `cargo test` gruen heisst nicht,
  dass Python den neuen Code sieht. `maturin develop` scheitert hier (kein
  Virtualenv); der Weg ist `maturin build --release` plus
  `pip install --force-reinstall --no-deps`.
- **Backticks in doppelten Quotes** werden von der Shell ausgefuehrt --
  Markdown-Code-Spans verschwinden spurlos aus Text, der ueber `python -c`
  oder `git -m` geschrieben wird. Heredoc mit einfachen Quotes benutzen.

---

## GELTENDE REGELN (kompakt)

Langform samt Herleitung: `../archive/history.md`, Kapitel "Vollstaendiger
STATUS-Stand vom 2026-08-25", Abschnitt "GELTENDE REGELN".

**Messen und Auswerten**

- **Score-Auswertungen IMMER auf Block-Ebene.** Paar-SEs werden sonst massiv
  unterschaetzt.
- **Aufloesung schlaegt Sparsamkeit.** Bei n=400 streut dieselbe Konfiguration
  um 5,75 Prozentpunkte; der Seed bewegt die Metrik 4- bis 6-mal staerker als
  jeder Knopf.
- **Value-Aenderungen brauchen Arena-Gating** -- es gibt keinen validierten
  Offline-Praediktor.
- **Sechs Standard-Kennzahlen in JEDEM Messbericht**: Reihen-, Spalten- und
  Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte, Margin.
- **Laufzeit ins Artefakt**, nicht nur nach STATUS: `laufzeit`-Block mit
  `wanduhr_s`, `cpu_s`, `threads`, `s_je_partie`.
- **Lange Laeufe nie in eine Pipe**, keine eigene Umleitung; Fortschritt mit
  `flush` sichtbar machen.

**Training und Korpus**

- **Fenster-Pinning: ZWEI Variablen**, nicht eine -- Trainings waehrend
  laufender Generierung immer pinnen (Split-Shift, Cache-Neubau,
  Kontamination).
- **Traeger-Status vor jeder Policy-Aussage pruefen.** Korpora sind per
  Default NICHT policy-traeger.
- **Backup- und Alt-Regel-Korpora kommen NIE wieder ins Training.**
- **Promotions-Checkliste** und **Nachschub bei Gating-Fehlschlag**: Langform
  im Archiv, hier nur der Merkposten, dass beides existiert und gilt.
- **Nie auf plattenblindes Normalspiel eichen.** Kalibrierung und Zielraten
  nicht gegen die Verteilung heutiger Netze, wenn genau deren Verhalten das
  Ziel ist.

**Arbeitsweise**

- **Loeschen nur mit expliziter, pfadgenauer Rueckfrage.** Eine Frage ist
  keine Anweisung.
- **Push nie ohne ausdrueckliche Anweisung.**
- **Parallele Sitzungen: Spurdisziplin.** Fremde Straenge und Preregs nicht
  abarbeiten; `git add` pfadgenau statt verzeichnisweit (am 2026-08-25 sind
  drei fremde Dateien in einen Commit gerutscht).
- **Prereg-Kopf und Index**: wer ein Ergebnis registriert, zieht den
  Zeile-1-Kopf im selben Zug nach und laesst
  `python tools/generate_prereg_index.py` laufen. Gueltige Status:
  OFFEN / ENTSCHIEDEN / UEBERHOLT.
- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** -- es definiert die
  Elo-Leiter.
- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte Gegner.

---

## ARCHITEKTUR (Referenz, Stand 2026-08-25)

**Such- und Engine-Seite** (`engine/src/net_mcts.rs`)

- `ACTIVE_LEAF = LeafEval::Net`; Stufe 1 (DFS-Blatt) liegt dormant, Rueckfall
  ist ausgeschlossen (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv: `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`, `ROUND_TRANSITION_SAMPLING = false`,
  `SHUFFLE_STACK_PEEK_IN_SEARCH = false`, `bootstrap_horizon_rounds = 2`.
- **Zwei R5-Loeser**: der eingefrorene `round5_anchor.rs` haengt an den drei
  Heuristik-Sucheinstiegen und schuetzt die Elo-Leiter; `round5.rs` ist der
  Netz-Loeser und darf sich entwickeln. Runde 5 ist **Expectiminimax** mit
  Zufallsknoten an den Chip-Aufdeckstellen; `NODE_BUDGET = 200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl -- **kein geloestes Endspiel**
  (~3 Halbzuege, Orakel-Uebereinstimmung 81,4 Prozent).
- **Der Stapelzug wird gesammelt aufgeloest**
  (`self_play.rs::resolve_and_apply_stack_draw`, Default-Pfad): die Suche
  bewertet EINEN Peek, danach zieht eine handgeschriebene Schleife weiter und
  waehlt Platte, Slot und Rotation selbst -- Kosten und Ergebnis weichen vom
  Bewerteten ab. Siehe offener Punkt 2.

**Netz- und Trainingsseite** (`config.py`, `engine/py/neural_net.py`)

- **`INPUT_SIZE = 714`** (seit 2026-08-25: plus 6 `col_f_max`),
  **`NUM_PLANES_CHANNELS = 77`** (plus 1 Ebene Erreichbarkeit, Kanal 76),
  `NUM_ACTIONS = 406`.
- Beide neuen Groessen werden in `serialize::serialize_player` **einmal**
  gerechnet und ins Zustands-JSON geschrieben; der Rust-JSON-Pfad und Python
  LESEN sie, nur `state_to_features_direct` rechnet selbst (bewacht von den
  `direct_matches_json_path_*`-Tests). Kosten als Bitmaske: plus 0,27 Prozent
  je Korpus statt plus 3,80 Prozent als Liste.
- **Altmodelle bleiben bitgleich**: `net::split_planes_flat_batch_src` kuerzt
  den Planes-Block auf die Modellbreite und liest den Flat-Block ab der
  Quell-Grenze; neue Groessen haengen am ENDE ihres Blocks. Am Champion
  belegt (Paritaets-Hash unveraendert), nicht hergeleitet.
- Champion-Encoder ist **2D** (`Mosaic2DNet`); der flache `MosaicNet` bleibt
  Parallel- und Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`,
  `opp_points`. `ownership` ist 140 breit, `OWNERSHIP_WEIGHT = 0` -- der
  Champion-Kopf ist **untrainiert**.
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, `VALUE_OPP_EPSILON = 0,0`.
- **Value-Ziel ist margen-BLIND** (`values_wdl`, TD-Blend aus
  Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang). Training:
  `--value-head wdl --select-by-brier`.
- Champion: `models/champion.txt` zeigt auf `v21_2d_brierbest`.

**Konstanten mit Fallstrick**

- `bonus_points` in `dome.rs` ist ein **Diskriminator** (Special = 3,
  Wild = 0), KEIN Punktwert -- der echte Spezialfeld-Wert ist die Rasterreihe
  1 bis 6.
- `special_empty` zaehlt nur Spezialfelder auf **bereits gelegten** Platten.
- Die Handbuch-Nummerierung der Wertungsplatten ist um eins gegen die
  Code-Indizes verschoben: Handbuch 7 = Code 6 = Spezialfelder.
