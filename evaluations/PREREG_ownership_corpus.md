# PREREG: Ownership-Korpus — Generierungsplan (Zwei-Pole)

Stand 2026-08-14, PLAN (nichts gestartet — durchgehend Plan-Zeitform).
Nutzer-Auftrag: *"dann mach schon mal den generierungsplan für den ownership
korpus"*. Aufsetzend auf PREREG_ownership_consumer.md (Verbraucher-Entwurf,
Tor A: Kopfgüte VOR Verbraucher-Bau) und der abgeschlossenen
Generator-Kampagne (PREREG_provocation… noch PREREG_provokation.md §13–§19).

## §1 Geprüfter Ist-Stand (Generator-Sortiment, aktuelle Ära)

| Quelle | Kriterium | Niveau | Beleg |
|---|---|---|---|
| Spaltenbau (MOSAIC_SPALTENBAU, R3-Pfad) | k1 vertikal | 3,15 Ø; 8/20 Partien ≥1 volle Spalte (7×7, 1×14) | konfund_AC Arm 0, nachgerechnet |
| Plattenbauer k2 (MOSAIC_PLATTENBAU=2, mit Special-Erweiterung) | k2 diagonal | 5,65 Ø; **13/23 volle Diagonalen** | k2_special_k2seeds Arm 1, nachgerechnet |
| Heuristik (wertung_progress, Elo-Anker) | k6 spezial | −6,60 bis −11,10 — bestes k6-Niveau im Projekt | k6-JSONs, Gegner-Seite nachgerechnet |
| Beifang aller Arme | k3 mehrfarbig / k5 Ecken / äußere Felder | 5–6 / 4,2–4,8 / 10,6 | konfund_AC + special_r17, nachgerechnet |
| k0/k7 | — | Nutzer-Entscheid: verteidigen, nie anstreben — Deckung nur beiläufig | STATUS |
| k4 horizontal | — | 0,6–1,0; Nutzer: Spielarchitektur-Problem | dito |

Infrastruktur (geprüft): Standard-Fenster lädt `data/*.pkl` NICHT-rekursiv
(train.py:552) — ein Unterordner ist strukturell getrennt. Streuung
(MOSAIC_WERTUNG_STREUUNG_MAX, partie-seed-abgeleitetes Shaping-Gewicht) ist in
run_net_self_play verdrahtet. Ownership-Kopf: 72 Feld-Labels + 68
Konjunktions-Labels (config.py:78/118), Champion-Gewicht bisher 0,0.

## §2 Korpus-Aufbau: vier Arme

Ablage: `data/ownership_corpus/` (strukturell außerhalb des Standard-Fensters,
§1). Dateinamen nach Generator-Konvention (Erzeuger-Champion): `v21_own_a_*`,
`v21_own_k1_*`, `v21_own_k2_*`, `heur_own_*`.

| Arm | Aufbau | Anteil | Zweck |
|---|---|---:|---|
| A | Netz-Self-Play + Streuung, KEINE Bauer-Knöpfe | 3000 (50 %) | Basisverteilung/Kalibrierung — der Kopf muss realistische Vollendungsraten sehen, nicht nur Erfolgsfälle |
| B | wie A + MOSAIC_SPALTENBAU (R3-Pfad) | 1000 | k1-Positivbeispiele (~0,45 Spalten/Partie) |
| C | wie A + MOSAIC_PLATTENBAU=2 | 1000 | k2-Positivbeispiele (>50 % volle Diagonalen) |
| D | Heuristik-Self-Play (150 Sims) | 1000 | k6-Demonstrationen + generelle Plattenbewirtschaftung (wertung_progress); billigster Arm |
| E | wie A + k5-Bauer (MOSAIC_PLATTENBAU=5, wird gebaut) | 1000 | k5-Positivbeispiele. Nutzer-Entwurf: Spalten-PAAR-Ziel (äußeres Paar 0+1 oder 4+5) — schließt beide Ecken der Seite (8+3 = 11 = Orakel) und harmoniert mit k1 (laut scoring.rs:60-64 nicht wechselseitig ausgeschlossen); Spezialkuppeln in die unteren Ecken ((2,0)/(2,2), 8-Punkte-Seite, Nutzer-Taktik) |
| F | wie A + k6-Spezialbauer (MOSAIC_PLATTENBAU=6, Bestand) | 1000 | k6 vom Netz-Pol (Nutzer-Entscheid 2026-08-14): der bestehende Spezialbauer spielt −9,75 gegen −15,00 des nackten Netzes (§19-Anker, nachgerechnet). Zusammen mit Arm D deckt der Korpus k6 damit von BEIDEN Polen — Netz-Seite über den Bauer, Heuristik-Seite über wertung_progress (−6,60 bis −11,10) |

Bewusst KEINE nachträgliche Selektion in v1: Die Arm-Quoten ERSETZEN die
Selektion (gezielte Anreicherung statt Verzerrung der Basisrate). Eine
Selektions-Stufe (plattenreiche Partien übergewichten) bleibt als v2-Hebel
vorregistriert, falls Tor A an zu dünnem Positiv-Signal scheitert.

Nach der Generierung, VOR dem Training: **Deckungs-Bericht** je Kriterium
(Anzahl Partien mit positivem Label je Geometrie-Einheit, beide Spielerseiten
getrennt) — die Basisraten-Falle aus der Skill-Konfundierungs-Lehre.

## §3 Offene Prüfpunkte VOR dem Start (jeder einzeln, mit Prüfstelle)

1. **Policy-Ziele unter Vorzug**: Was zeichnet run_net_self_play als
   Policy-Target auf, wenn der Bauer-Vorzug die Suchentscheidung übersteuert?
   (self_play.rs, Aufzeichnungspfad lesen.) Demonstrations-Targets sind
   gewollt (Zwei-Pole-Idee), aber es muss BEKANNT sein, was im Record steht.
2. **Wirken die Bauer-Knöpfe im Self-Play auf beide Spieler?** Die Messungen
   liefen in der Arena (Netz-Seite). Für den Korpus ist beidseitiges Steuern
   in Arm B/C erwünscht — prüfen, nicht annehmen.
3. **Konjunktions-Breite**: config.py:118 sagt 68, der
   neural_net.py-Kommentar (Zeile ~1837) sagt [72:97]/[97:122] = 25 je Spieler
   — eine der beiden Angaben ist veraltet. Vor dem Training auflösen.
4. **Fenster-Verträglichkeit**: Der Trainings-Lauf braucht einen additiven
   Datei-Zugang (z. B. `--extra-data-dir`, Default leer) — kleiner
   train.py-Umbau, vorab bauen und mit leerem Default byte-identisch belegen.
5. **GPU-Verdikt §22**: Bei ≥2× Durchsatz die Arme A–C über den Async+ORT-Pfad
   fahren; sonst klassisch 8 Threads. Der Plan hängt davon NICHT ab, nur die
   Laufzeit.
6. **Leckt das Streuungs-Shaping in die Value-Labels?** (Nutzer-Auftrag
   2026-08-14; exhumiert aus der ausgemusterten P-Liste, dort nie
   beantwortet.) Arm A läuft mit MOSAIC_WERTUNG_STREUUNG_MAX > 0; das
   Shaping verschiebt die BLATTBEWERTUNGEN der Suche. Zu klären am Code:
   entstehen `bootstrap_value`/`round_transition_value` aus denselben
   (geshifteten) Netz-Blattbewertungen (round_transition_deep.rs::
   net_leaf_eval-Pfad, thread-lokales Partie-Gewicht!) — dann tragen die
   Arm-A-Records verzerrte Value-Ziele und das Shaping muss für die
   LABEL-Rechnung neutralisiert werden (oder der Befund lautet belegt
   "kein Leck"). Vor dem Start beantworten, mit datei:zeile.

### Nachträge (2026-08-14, Prüf-/Kleinbau-Sitzung — reine Prüfung + ein additiver Schalter, KEINE Generierung/Training gestartet)

**3.1 Policy-Ziele unter Vorzug — GEPRÜFT, Befund aendert die Aufgabenstellung.**
`run_net_self_play` (`engine/src/self_play.rs:2943`) ruft je Partie
`play_net_self_play_game` (`self_play.rs:2567`-2941) auf. Deren Drafting-Block
bestimmt `chosen` AUSSCHLIESSLICH ueber `net_drafting_policy(...)`
(Such-Policy) — GEPRUEFT per Volltext-Suche nach "vorzug"/"plattenbauer"/
"spaltenbau" ueber die GESAMTE Funktion (`self_play.rs:2567`-2941), ueber
`net_drafting_policy` selbst (`self_play.rs:2277`-2567) und ueber
`apply_chosen_action` (`self_play.rs:615`-~700): **null Treffer**. Der
Bauer-Vorzug (`provokation::vorzugszug`/`plattenbauer::drafting_vorzug`/
`dome_vorzug`) ist in DIESEM Pfad **gar nicht verdrahtet** — es gibt also
aktuell KEINE Uebersteuerung, die aufgezeichnet werden koennte.

**Konsequenz fuer §2 (blockierend, nicht nur informativ):** Arm B/C sind als
"wie A + MOSAIC_SPALTENBAU" / "wie A + MOSAIC_PLATTENBAU=2" beschrieben, wobei
"A" = `run_net_self_play` ist (§1: "Streuung ... ist in run_net_self_play
verdrahtet"). Da dieser Pfad die Knoepfe gar nicht liest, haetten Arm B/C
in der jetzigen Codebasis **keinerlei Effekt** — sie waeren ununterscheidbar
von Arm A. Die Vorzug-Verdrahtung muss ERST in `play_net_self_play_game`
nachgezogen werden, bevor Arm B/C gestartet werden koennen. Kein Umbau in
dieser Sitzung (Auftrag: "nur Wissen").

**3.2 Beidseitigkeit — GEPRÜFT, und uneinheitlich zwischen den bestehenden Pfaden.**
Da 3.1 zeigt, dass `run_net_self_play` den Knopf ueberhaupt nicht liest, ist
die woertliche Antwort: **aktuell wirkt er auf KEINEN der beiden Spieler**
(die Frage "einer oder beide" hat noch keinen Code-Gegenstand). Als Kontext
fuer die noetige Nachruestung (3.1) — die BEIDEN bestehenden Vorzug-Pfade im
Code widersprechen sich in der Seitigkeit:
- `play_net_game` (Arena, `self_play.rs:1572`-1863): Gate `if pi == net_board
  && actions.len() > 1` bei `self_play.rs:1627` — **einseitig**, nur die
  Netz-Seite eines Netz-vs-Heuristik-Matches.
- `play_net_vs_net_game` (`self_play.rs:1863`-2277): der Vorzug-Aufruf bei
  `self_play.rs:1927`-1929 steht OHNE `pi`-Gate im selben Codepfad, der fuer
  JEDEN aktuellen Spieler durchlaufen wird — **beidseitig**, unabhaengig
  davon, ob `pi==0` oder `pi==1`.
Fuer die Nachruestung in `play_net_self_play_game` ist `play_net_vs_net_
game`s ungegateter Aufruf (`self_play.rs:1927`-1929) das passende Vorbild,
nicht `play_net_game`s einseitiges Gate — Auftrag §2 will explizit
beidseitiges Steuern in Arm B/C.

**3.3 Konjunktions-Breite — GEPRÜFT und korrigiert: config.py hat recht, der neural_net.py-Kommentar war veraltet.**
`config.py:117`-118 (`CONJUNCTIONS_PER_PLAYER = 34`, `CONJUNCTION_TARGETS =
68`) ist die Zahl, die TATSAECHLICH fuer die Tensor-/Ausgabeschicht-Groesse
verwendet wird (`neural_net.py:1169` `self.own_targets = OWNERSHIP_TARGETS +
CONJUNCTION_TARGETS`, ebenso die Layer-Definitionen an den `nn.Linear(128,
OWNERSHIP_TARGETS + CONJUNCTION_TARGETS)`-Stellen). Der eigentliche
Label-Bauer `_conjunctions_from_dome` (`neural_net.py:932`) liefert bei
Nachzaehlen der eigenen Index-Liste im Docstring (0..5, 6..11, 12..13,
14..17, 18, 19..24, 25..33) **34 Eintraege** (6+6+2+4+1+6+9=34) — DECKUNGS-
GLEICH mit config.py, NICHT mit "25". **Zwei veraltete Stellen korrigiert**
(beide zitierten faelschlich 25 je Spieler / Slice [72:97]/[97:122]):
- `_conjunctions_from_dome`s eigener Docstring (`neural_net.py:932`-937):
  "25 Binaerlabels" → "34 Binaerlabels", mit Verweis auf config.py:117 und
  diesen §3.3-Nachtrag.
- Der Label-Layout-Kommentar im Assemblierungs-Loop (vormals bei
  `neural_net.py` Zeile ~1836-1837): "[72:97] Konj. ich, [97:122] Konj.
  Gegner" → "[72:106] Konj. ich, [106:140] Konj. Gegner" (34 je Spieler,
  Gesamtbreite `own_targets` = 72+68 = 140).
`python -m py_compile engine/py/neural_net.py`: OK.

**3.4 --extra-data-dir — GEBAUT, additiv, geprüft.** `train.py`:
- Neuer Schalter `--extra-data-dir PATH` (Default `None`), hart validiert
  (`Path(extra_data_dir).is_dir()`, sonst `sys.exit` VOR jedem Datenladen —
  gleiches Muster wie die bestehende `--value-target-lambda`-Validierung).
- Datei-Sammlung additiv NACH `MOSAIC_DATA_EXCLUDE` (das bleibt fuers
  wachsende Standard-Fenster reserviert, siehe Kommentar an der Stelle):
  `all_files = sorted(all_files + sorted(glob.glob(str(Path(extra_data_dir) /
  "*.pkl"))))`, NICHT rekursiv, gleiche `*.pkl`-Konvention wie `DATA_DIR`.
  Leer/`None` (Default) laesst `all_files` unveraendert — byte-identisch
  zum Bestand (Task-#28-Muster).
- `_cli_args`-Manifest-Dict um `"extra_data_dir": extra_data_dir` ergaenzt —
  der Zusatzpfad landet im Trainings-Manifest.
- **Beleg (isolierte Nachbildung der eingefuegten Logik mit den ECHTEN
  Modul-Konstanten `train.DATA_DIR`/`train.Path`, KEIN echter `train()`-Aufruf
  — "kein Training starten" bleibt gewahrt)**: ohne Zusatzpfad 2945 Dateien
  (`DATA_DIR` unveraendert); mit einem temporaeren Zusatzverzeichnis (1
  Dummy-`.pkl`) 2946 Dateien, exakt die eine zusaetzliche Datei, Basisliste
  dabei nachweislich unveraendert. Validierung separat GEPRUEFT: `python
  train.py --name test_validation_only_delete_me --extra-data-dir
  D:/nicht/vorhanden` bricht sofort mit Fehlermeldung ab, VOR jedem
  Manifest-/Datei-Schreibvorgang (keine Datei mit diesem Versionsnamen
  entstanden). `python train.py --help` zeigt den neuen Schalter korrekt,
  `python -m py_compile train.py`: OK.
   Laufzeit.

**3.5 Bauer-Vorzug in `run_net_self_play` verdrahtet + Wirkungs-Probe
(2026-08-14) — GEBAUT und WIRKT, beidseitig, wie erwartet.**

Behebung des 3.1-Blockers: `play_net_self_play_game`s Drafting-Block
(`self_play.rs:2693`-2695) berechnet jetzt VOR dem bestehenden
Ein-Aktion-Kurzschluss einen `vorzug_kandidat` —
`provokation::vorzugszug(&game.state).or_else(|| plattenbauer::drafting_vorzug
(&game.state)).or_else(|| plattenbauer::dome_vorzug(&game.state))` — OHNE
`pi==net_board`-Gate, exakt das Vorbild aus `play_net_vs_net_game`
(`self_play.rs:1927`-1929, siehe 3.2). Ein neuer `else if let Some(a) =
vorzug_kandidat`-Zweig (`self_play.rs:2700`-2711) macht daraus dasselbe
Demonstrations-Target (ein-hot, `prob=1.0`, `root_q=None`,
`root_child_q=[]`) wie der bestehende Ein-Aktion-Fall — die 3.1-Frage
("was steht im Record unter Vorzug") ist damit nicht mehr hypothetisch,
sondern durch den eigenen Code beantwortet.

Drei Entscheidungspunkte lt. Auftrag, GEPRUEFT einzeln:
- **Drafting-Vorzug + Kuppelwahl**: EIN gemeinsamer Aufruf-Ketten-Punkt
  (`dome_vorzug` ist Teil derselben `.or_else`-Kette wie `drafting_vorzug`,
  keine eigene Phase — GEPRUEFT per Grep, `dome_vorzug` taucht in
  `self_play.rs` ausschliesslich in Drafting-Bloecken auf, nie in einem
  eigenen `Phase::Dome`-Zweig, den es nicht gibt). Jetzt verdrahtet.
- **Tiling-Vorzug**: GEPRUEFT unveraendert gelassen, mit Begruendung: die
  Self-Play-Funktion `tiling_step` (`self_play.rs:1074`-1114) ruft
  `resolve_tiling_step(&game.state, pi, net)` auf — DIESELBE Funktion, die
  auch `play_net_vs_net_game`s Tiling-Arm nutzt (`self_play.rs:2143`-2145,
  dort `resolve_tiling_step(&game.state, pi, None)`). Beide Pfade riefen
  schon VOR diesem Umbau `crate::plattenbauer::tiling_vorzug` an KEINER
  Stelle auf (GEPRUEFT per Grep ueber `tiling_solver.rs`: nur
  `spaltenbau::vorzug_tiling_step` und ein lokales `provokation`-basiertes
  Pendant sind verdrahtet, `plattenbauer::tiling_vorzug` an keiner
  Aufrufstelle im ganzen Repo) — ein vorbestehender, von diesem Auftrag
  unabhaengiger Bestandsbefund, kein neu eingefuehrtes Verhalten. Self-Play
  ist damit fuer Tiling bereits 1:1 identisch zum Arena-Pfad (dieselbe
  Funktion, dasselbe Nicht-Verhalten) — "alle drei Entscheidungspunkte" ist
  erfuellt, der dritte Punkt einfach ohne Diff.
- `set_partie_seed`: `run_net_self_play`s `play`-Closure fehlte dieser
  Aufruf komplett (GEPRUEFT per Grep, `run_net_arena_match`/
  `run_net_vs_net_arena` haben ihn, `run_net_self_play` hatte ihn nicht).
  Nachgetragen INNERHALB der `run_with_watchdog`-inneren Closure
  (`self_play.rs:3061`, direkt neben dem bestehenden
  `set_partie_shaping_weight`-Aufruf, aus demselben Thread-Lokalitaetsgrund:
  `play_net_self_play_game` laeuft auf dem NEU gespawnten Watchdog-Thread,
  nicht auf dem aeusseren rayon-Thread). Kein Reset auf `None` noetig — der
  Thread ist neu je Partie, kein Leck ueber Partien hinweg moeglich (anders
  als bei wiederverwendeten rayon-Workern).

**Bestandsschutz**: `cargo test --lib` 417/0/20 (Baseline vor diesem Umbau
war 417/0/20 nach §20 — unveraendert, keine neuen/entfernten Tests fuer
diesen reinen Verdrahtungs-Umbau). `tools/paritaets_probe.py`: Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` haelt
(Wheel neu gebaut+installiert) — Bestandsverhalten bei unbesetzten Knoepfen
byte-identisch.

**Wirkungs-Probe** (Anti-Stillstand-Beweis, `scratchpad/wirkungsprobe_arm.py`
+ `scratchpad/wirkungsprobe_auswertung.py`): je Arm 30 Partien ueber
`mosaic_rust.net_self_play_games` (= `run_net_self_play`), Champion
`v21_2d_brierbest`, `base_sims=200`, EIN gemeinsamer Seed (20260814) ueber
alle Arme (gepaarte Anlage wie im uebrigen Auftrag), `record_rtv=false`,
`MOSAIC_WERTUNG_STREUUNG_MAX` bewusst UNGESETZT (Koordinator-Vorgabe: ein
Faktor). Jeder Arm lief in einem EIGENEN Python-Prozess (Pflicht:
`MOSAIC_SPALTENBAU`/`MOSAIC_PLATTENBAU` sind in Rust `OnceLock`-gecacht, ein
zweiter Arm im selben Prozess wuerde den ersten Knopf einfrieren). Rohdaten
(30 Spiele je Arm, Step-Records als `.pkl`, plus je Spiel der letzte
fertige Record als Zustands-Zusammenfassung) liegen unter
`data/corpus_probe/` (NICHT `data/` oder `data/ownership_corpus/`,
Messdaten-Regel) — `data/` ist gitignored, nichts davon wird committet.
Je Kriterium wurde `mosaic_rust.end_scoring_from_state_json` auf den
LETZTEN Record jeder abgeschlossenen Partie angewandt (per Konstruktion der
Zustand mit fertigem `dome_grid`, siehe `tools/scoring_tile_impact.py`-
Moduldoku — dort bereits so verifiziert, hier direkt uebernommen statt neu
hergeleitet) — UNABHAENGIG davon, ob das Kriterium in der jeweiligen Partie
tatsaechlich gezogen wurde (die Bauer-Dispatch ist ueber `MOSAIC_PLATTENBAU`
fest, nicht an `scoring_tile_ids` gekoppelt, siehe `plattenbauer.rs:236`-240).

| Arm | Knopf | Ziel-Kriterium | Ø Punkte P0 | Ø Punkte P1 | Δ vs. A (P0/P1) |
|---|---|---|---:|---:|---:|
| A | keiner | — (Bezug) | k1 0,00 / k2 0,00 / k5 3,20 / k6 −11,50 | k1 0,00 / k2 0,00 / k5 3,20 / k6 −10,90 | — |
| B | `MOSAIC_SPALTENBAU` | k1 Vertikale Reihen | **2,80** | **3,27** | +2,80 / +3,27 |
| C | `MOSAIC_PLATTENBAU=2` | k2 Diagonale | **4,33** | **2,33** | +4,33 / +2,33 |
| E | `MOSAIC_PLATTENBAU=5` | k5 Eckplatten | **8,30** | **7,93** | +5,10 / +4,73 |
| F | `MOSAIC_PLATTENBAU=6` | k6 Spezialfelder | **−8,30** | **−8,70** | +3,20 / +2,20 (weniger negativ) |

n=30 je Arm, alle 30/30 Partien vollstaendig (`completed=true`), keine
Haenger. Sanity-Nebenbefund (nicht Teil der Abnahme, nur Kontext): mittlere
Gesamtpunktzahl steigt leicht mit aktivem Knopf (A 21,0/21,5 → B 24,5/23,2 →
C 27,5/25,7 → E 27,8/24,3 → F 30,2/25,7) — kein Hinweis auf einen
Spielstaerke-Kollaps durch die Verdrahtung.

**Befund gegen die Vorab-Erwartung des Koordinators** ("B/C/E heben ihr
Kriterium deutlich ueber Arm A, Groessenordnung k1~3/k2~5-6/k5~8; F
deutlich ueber A, Groessenordnung −9,75 gegen −15,00"): **ERFUELLT fuer
B/E/F, TEILWEISE fuer C.** B trifft k1~3 fast exakt (2,80/3,27). E trifft
k5~8 fast exakt (8,30/7,93). F bewegt sich in die richtige Richtung und um
eine mit der Arena vergleichbare Groessenordnung (+2,2 bis +3,2 Punkte je
Spieler, Arena-Delta war +5,25 auf einer tieferen Basis −15,00 statt
−11,50 — die Basen sind wegen 3.6 unten verschieden, die RICHTUNG und
GROESSENORDNUNG der Verbesserung stimmen). C liegt mit 2,33-4,33 (Ø 3,33)
UNTER der Arena-Groessenordnung 5-6, aber klar und eindeutig ueber Arm As
0,00 — die Verdrahtung wirkt nachweisbar, nur schwaecher als in der Arena
erwartet (moegliche Ursache: 3.6 unten).

**3.6 Eigene Entscheidung / offene Einschraenkung (ungeprueft, als Annahme
markiert):** Diese Probe ist NICHT direkt grössenskalengleich mit den
Arena-Ankern aus PREREG_provokation.md §14-§20, aus zwei strukturellen
Gruenden, beide bewusst in Kauf genommen (Auftrag: "nur die kleine Probe,
keine neue Kalibrierung"):
1. **Bilateral statt einseitig**: Arena mass eine Seite (Netz) gegen einen
   UNGESTEUERTEN Gegner (Heuristik `--heur-sims 150`, kein Bauer-Knopf).
   Self-Play steuert BEIDE Seiten gleich (kein `pi`-Gate, s.o.) — zwei
   gleich steuernde Spieler konkurrieren um dieselben Farben/Kuppel-Zellen,
   was die pro Spieler erreichbaren Punkte gegenueber der Arena-Zahl
   druecken kann (nicht gemessen, nur plausibel).
2. **`base_sims=200` statt Arenas 400**: eigene, unbegruendete Kostenwahl
   fuer diese Probe (schneller, ausreichend um die Vorzug-UEBERSTEUERUNG
   selbst zu pruefen, da der Vorzug bei Treffer die Suche vollstaendig
   ersetzt — sims wirken nur auf die NICHT uebersteuerten Zuege).
Beides aendert nichts an der JA/NEIN-Frage dieses Auftrags (wirkt die
Verdrahtung ueberhaupt) — die beantwortet sich unabhaengig von der exakten
Groessenordnung schon durch den klaren Sprung weg von Arm As 0,00/0,00
(k1, k2) bzw. die klare Verschiebung bei k5/k6. Fuer den echten Korpus-Lauf
(§2) waeren `base_sims` und ggf. eine erneute, dann korpus-massstaebliche
Kalibrierung ein separater, spaeterer Schritt, kein Teil dieser Probe.

**Verdikt: Verdrahtung wirkt, wie im Auftrag gefordert — kein "Befund
statt Schoenreden" noetig, es gibt einen echten Effekt in allen vier
gebauten Kriterien.** Arm B/C/E/F sind fuer den echten Korpus-Lauf (§2)
freigegeben, sobald dieser gestartet wird (nicht Teil dieses Auftrags).

## §4 Training + Abnahme (Tor A aus PREREG_ownership_consumer.md)

- Warm-Start vom Champion (v21_2d_brierbest), Standard-Rezept (lr 5e-5,
  cosine), `--ownership-weight 0,2` (Präzedenz: own02-Lauf) + `--conjunction`.
- Fenster: aktuelles Standard-Fenster + `data/ownership_corpus/` (additiv).
- Während Generierung nie gleichzeitig trainieren ohne
  MOSAIC_DATA_EXCLUDE-Pinning (stehende Regel).
- **Abnahme = Kopfgüte, NICHT Arena**: je Feld Brier/AUC gegen die Basisrate
  auf Held-out-Partien (Split auf Partie-Ebene); je Kriterium Rangkorrelation
  E_k gegen tatsächliche Plattenpunkte; Bericht getrennt nach eigener und
  Gegner-Hälfte. Erst nach bestandenem Tor A wird der Verbraucher
  (PREREG_ownership_consumer.md) gebaut.
- Nebenbedingung: policy/value-Offline-Metriken des Laufs mitloggen — ein
  Einbruch dort wäre ein Warnsignal für Demonstrations-Kontamination
  (Prüfpunkt §3.1), aber KEIN Abnahmekriterium dieses Laufs.

## §5 Umfang und Kosten (Herleitung, keine Messung)

8000 Partien gesamt (Arm E und Arm F per Nutzer-Entscheid 2026-08-14 gleich
mit eingeplant; k5-Bauer hat seine Abnahme in PREREG_provokation.md §20
bestanden — 3,68 → 8,55, t=4,56; der k6-Spezialbauer ist Bestand).
Bezug: Arena-Durchsatz 248,5 Spiele/h (8 Threads, §20);
Self-Play mit Labels liegt darunter, Heuristik-Arm weit darüber. Grobschätzung
20–30 h CPU für A–C, Arm D <2 h; mit GPU-2× entsprechend die Hälfte. Läuft
unbeaufsichtigt in Etappen (Watchdog vorhanden); Umfang ist ein Regler, kein
Fixum — die Deckungszahlen aus §2 entscheiden, ob nachproduziert wird.

## §5b Lebenszyklus des Korpus (Nutzer-Entscheid 2026-08-14)

Der Korpus ist ein LEHR-Korpus, kein Dauerbestand. Archivierung (Backup-Script
deckt, lokale Kopie weg) erst, wenn BEIDE Bedingungen erfüllt sind:

1. **Tor A bestanden** — vorher kann ein Fehlschlag Nachproduktion oder den
   v2-Selektions-Hebel nötig machen (§2).
2. **Der Kreislauf ist geschlossen**: der Ownership-Verbraucher ist aktiv
   (w_own > 0 nach Regler-Sweep) UND die erste Self-Play-Generation aus
   plattenbewusstem Spiel liegt vor. Ab dann erzeugt das Spiel selbst
   plattenreiche Labels, und künftige Trainings brauchen den Lehr-Korpus
   nicht mehr — vorher würde ein Weitertrainieren des Kopfes ohne den Korpus
   die Platten-Verteilung wieder verlieren.

Lokale Löschung dann wie immer nur mit pfadgenauer Freigabe (Löschverbot).

Kein Stärke-Training: kein Gating, kein Champion-Anspruch, keine
Elo-Interpretation der beteiligten Konfigurationen. Die Bauer-Knöpfe bleiben
Diagnose-Werkzeuge (nie im Gating); ihre Partien tragen Brett-Fakten-Labels
(Nutzer-Entscheid: Ownership-Labels sind Brett-Fakten, Trainingskorpus
erlaubt).
