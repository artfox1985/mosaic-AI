<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird der Zwei-Pole-Korpus für das Ownership-Kopf-Training generiert — welche Arme, Quoten, Ablage, Prüfpunkte und welches Kopfgüte-Tor? | Beleg: Tor A BESTANDEN (par.10.4, 2026-08-15/16): der Kopf schlaegt die Basisrate auf allen Geometrien; Korpus erzeugt, Deckung gegeben. Der Statuskopf hinkte dem eigenen par.10 nach (Stale-Korrektur 2026-08-20). -->

# PREREG: Ownership-Korpus — Generierungsplan (Zwei-Pole)

Stand 2026-08-14, PLAN (nichts gestartet — durchgehend Plan-Zeitform).
Nutzer-Auftrag: *"dann mach schon mal den generierungsplan für den ownership
korpus"*. Aufsetzend auf PREREG_ownership_consumer.md (Verbraucher-Entwurf,
Tor A: Kopfgüte VOR Verbraucher-Bau) und der abgeschlossenen
Generator-Kampagne (PREREG_provocation… noch PREREG_provocation.md §13–§19).

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
(Such-Policy) — GEPRUEFT per Volltext-Suche nach "vorzug"/"plate_builder"/
"column_build" ueber die GESAMTE Funktion (`self_play.rs:2567`-2941), ueber
`net_drafting_policy` selbst (`self_play.rs:2277`-2567) und ueber
`apply_chosen_action` (`self_play.rs:615`-~700): **null Treffer**. Der
Bauer-Vorzug (`provocation::vorzugszug`/`plate_builder::drafting_vorzug`/
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
`provocation::vorzugszug(&game.state).or_else(|| plate_builder::drafting_vorzug
(&game.state)).or_else(|| plate_builder::dome_vorzug(&game.state))` — OHNE
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
  schon VOR diesem Umbau `crate::plate_builder::tiling_vorzug` an KEINER
  Stelle auf (GEPRUEFT per Grep ueber `tiling_solver.rs`: nur
  `column_build::vorzug_tiling_step` und ein lokales `provocation`-basiertes
  Pendant sind verdrahtet, `plate_builder::tiling_vorzug` an keiner
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
diesen reinen Verdrahtungs-Umbau). `tools/parity_probe.py`: Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` haelt
(Wheel neu gebaut+installiert) — Bestandsverhalten bei unbesetzten Knoepfen
byte-identisch.

**Wirkungs-Probe** (Anti-Stillstand-Beweis, `tools/probes/effect_probe_arm.py`
+ `tools/probes/effect_probe_eval.py`): je Arm 30 Partien ueber
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
fest, nicht an `scoring_tile_ids` gekoppelt, siehe `plate_builder.rs:236`-240).

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
Arena-Ankern aus PREREG_provocation.md §14-§20, aus zwei strukturellen
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

**3.7 Streuungs-Shaping leckte in die Value-Labels — GEPRUEFT, JA, und
BEHOBEN (§3 Punkt 6, 2026-08-14).** Reine Code-Pruefung wie beauftragt,
Befund vor Umbau:

- **Kette, GEPRUEFT datei:zeile (Zeilen VOR diesem Fix, siehe naechster
  Punkt fuer die Fix-Stellen)**: `run_net_self_play`s Watchdog-Closure
  setzt `set_partie_shaping_weight(Some(partie_gewicht_aus_seed(...)))`
  thread-lokal (`self_play.rs::run_net_self_play`s Watchdog-Closure, Zeile
  zum Pruefzeitpunkt 3038, zum Zeitpunkt dieses Nachtrags bereits nach 3542
  verschoben — ein anderer Agent refaktoriert self_play.rs parallel
  [Golden-Record-Harness], Zeilenangaben dort daher bewusst nur als
  Funktions-/Aufrufname zitiert, nicht als Zeilennummer; self_play.rs selbst
  WURDE FUER DIESEN FIX NICHT ANGEFASST). `wertung_shaping_weights()`
  (`net_mcts.rs:1172`-1177 vor diesem Fix) liest DIESEN Thread-Wert VOR dem
  prozessweiten Env-Cache, `apply_wertung_shaping` (`net_mcts.rs:1458`-1463
  vor diesem Fix) nutzt ihn, `net_leaf_eval` (`net_mcts.rs:1905` vor diesem
  Fix) wendet es ueber den Kommentar bei `net_mcts.rs:2009`-2012 ("gilt
  also unveraendert fuer jeden `net_leaf_eval`-Aufrufer (Chance-Node-
  Sampling in `round_transition_deep.rs`/`self_play.rs` eingeschlossen)")
  bedingungslos an. `round_transition_deep.rs::bootstrap_value_after_rounds`
  (Zeile 719 vor dem Fix) und `continue_through_round{2,3,4}` (vormals
  Zeilen 577/606/635, `make_round_end_eval` eingeschlossen) riefen
  `net_leaf_eval` OHNE Zwischenschritt auf — alles auf DEMSELBEN Thread wie
  die Partie selbst (kein `thread::spawn`/`rayon::spawn` in
  `round_transition_deep.rs`/`round_transition.rs`, GEPRUEFT per Grep), also
  erbte die Label-Rechnung den vollen Thread-Zustand. (Alle vier
  Zeilenangaben sind Vor-Fix-Stand; der Fix selbst verschiebt sie um die
  neu eingefuegte Funktion, siehe Repo fuer den aktuellen Stand.)
- **Gemessen, nicht nur hergeleitet**: mit `MOSAIC_TAU`-neutralem Testaufbau
  (`round_transition_deep.rs::bootstrap_value_after_rounds_ignores_partie_
  streuung`, Modell `alphazero_v10_best.onnx`, Seed 51/4242) lieferte
  `bootstrap_value_after_rounds` VOR dem Fix `[0,5109; 0,4213]` ohne und
  `[0,5583; 0,4860]` MIT `set_partie_shaping_weight(Some(1.0))` — derselbe
  Zustand, derselbe RNG-Seed, ein Unterschied von +0,047/+0,065 Value-Punkten
  einzig durch den Partie-Wuerfelwurf. Provisorisch mit einem lokal
  vorhandenen Modell verifiziert (`alphazero_v10_best.onnx` selbst fehlt in
  diesem Checkout, `.gitignore`), Testdatei zitiert wieder das Standard-
  Modell wie der bestehende Determinismus-Test daneben (self-skip ohne
  `models/`, dokumentiertes Bestandsmuster).
- **Fix (`net_mcts.rs` + `round_transition_deep.rs`, KEIN self_play.rs-
  Antasten)**: neue Funktion `net_mcts::with_partie_streuung_suspended`
  (RAII-Guard, setzt `PARTIE_GEWICHT` fuer die Dauer von `f` auf `None` und
  restauriert danach, auch bei Panic) — angewandt als Wrapper um den
  GESAMTEN Funktionskoerper von `bootstrap_value_after_rounds` und
  `continue_through_round{2,3,4}` (vier Stellen, `round_transition_deep.rs`).
  Der PROZESSWEITE Basiswert (`MOSAIC_WERTUNG_SHAPING_W`, konstant ueber
  alle Partien) bleibt bewusst UNVERAENDERT wirksam — das ist die
  bestehende, in `net_leaf_eval`s eigener Doku ausdruecklich gewollte
  Kopplung, nicht Gegenstand von Punkt 6 und hier nicht angetastet; nur die
  ZUFAELLIGE Partie-zu-Partie-Streuung wird fuer die Label-Rechnung
  neutralisiert. Kein Baustein aus round_transition_deep.rs' Task-#71-Deckel
  (Zeit-/Knoten-Budgets) beruehrt.
- **Test, GEPRUEFT dass er etwas pruefte** (nicht vacuous): Fix testweise
  entfernt (Wrapper durch eine sofort aufgerufene Passthrough-Closure
  ersetzt) → derselbe neue Test schlaegt fehl, exakt mit den zwei oben
  zitierten Werten. Fix restauriert → Test gruen. `cargo test --lib`:
  418/0/20 (417 Bestand + 1 neuer Test). `tools/parity_probe.py`: Hash
  `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` haelt
  (Wheel neu gebaut+installiert) — Bestandsverhalten bei unbesetzten
  Knoepfen unveraendert, der Fix wirkt nur, wenn `PARTIE_GEWICHT` ueberhaupt
  `Some` ist.
- **Tragweite fuer den Korpus**: betrifft Arm A/B/C/E/F (alle laufen mit
  Streuung, §1/§2), NICHT Arm D (Heuristik-Self-Play, kein Netz-Leaf-Eval).
  `round_transition_value` (rtv, nur bei `record_rtv=true` aufgezeichnet)
  war GLEICHERMASSEN betroffen (`sample_round_transition_for_round`,
  `self_play.rs`, ruft dieselben `continue_through_round{2,3,4}` auf) und
  ist mit demselben Fix mitbehoben, ohne self_play.rs anzufassen.

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
mit eingeplant; k5-Bauer hat seine Abnahme in PREREG_provocation.md §20
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

**ARCHIVIERT (Nutzer-Entscheid 2026-08-22):** Bedingung 2 ist durch die
endgueltige Schliessung des Ownership-Verbraucher-Strangs (STATUS
2026-08-20, alle Formen negativ) unerfuellbar geworden; der Nutzer hat
die Klausel damit fuer ueberholt erklaert. Begleitbefunde zum Zeitpunkt:
kein aktives Training referenziert den Korpus mehr (Asym-Fenster an den
Cache-Zeilen geprueft, OWNERSHIP_WEIGHT=0.0 im Standardrezept), seine
R4/R5-Labels liegen VOR der round5-Fix-Grenze (c83fb35), und der
Asym-Korpus (16.000 Partien, Fix-Engine) ist der frische Nachfolger.
Backup-Abdeckung vom Nutzer bestaetigt; Entfernung des lokalen Ordners
`data/ownership_corpus/` durch den Nutzer selbst.

Kein Stärke-Training: kein Gating, kein Champion-Anspruch, keine
Elo-Interpretation der beteiligten Konfigurationen. Die Bauer-Knöpfe bleiben
Diagnose-Werkzeuge (nie im Gating); ihre Partien tragen Brett-Fakten-Labels
(Nutzer-Entscheid: Ownership-Labels sind Brett-Fakten, Trainingskorpus
erlaubt).

## §7 STARTVOLLZUG (2026-08-14, Nutzer-GO vom Vortag, Bedingungen erfuellt)

Bedingungen bei Start: Wirkungsprobe bestanden (§3.5), Schleifen-Refactor
abgenommen (PREREG_unified_game_loop.md §5), 2b abgenommen
(PREREG_deterministic_labels.md §4), GPU-Verdikt §22 gefallen: **Regel 3
verfehlt** (beste Zelle N=64 ORT-CUDA 1,545x, N=128 ORT 1,47x -- die reale
Ankunftsverteilung haelt die synthetischen Voll-Batches nicht; Zellen von mir
am JSONL nachgerechnet) -> **Pfad: klassisch 8 Threads** (Vorab-Regel §3.5).
Das liegengelassene 1,5x ist dokumentiert, die Vorab-Regel gilt.

Start-Konfiguration (Entscheidungen beim Vollzug, hier festgeschrieben):

- **Sims 200 fuer die Netz-Arme A/B/C/E/F** -- exakt die Stufe, auf der die
  Wirkungsprobe die Bauer-Niveaus VERIFIZIERT hat (k1 2,80 / k5 8,30, §3.5);
  400er-Arena-Niveaus waren vergleichbar, 200 halbiert die Kosten. Arm D
  (Heuristik) 150 Sims wie vorregistriert.
- **Streuung**: MOSAIC_WERTUNG_STREUUNG_MAX=1,0 in den Netz-Armen -- volle
  Spanne vom Netz-Pol (Gewicht 0) bis zur vollen Injektion (1,0), das
  Zwei-Pole-Spektrum je Partie-Wuerfelwurf. Label-Seite ist seit 1b61f9c
  gegen das Streuungs-Shaping abgeschirmt (Pruefpunkt 6).
- **Reihenfolge**: D (Pipeline-Probe, billigster Arm) -> A -> B -> C -> E ->
  F, je Arm sequentiell auf 8 Threads. rtv bleibt AUS (Standard seit v13).
- **Ablage**: MOSAIC_DATA_DIR=data/ownership_corpus (config.py:28),
  Basis-Seed 20260814, 10 Partien je Datei, Versionsnamen heur_own /
  v21_own_a / v21_own_k1 / v21_own_k2 / v21_own_k5 / v21_own_k6.
- Danach: Deckungs-Bericht (§2) VOR jedem Training; Training ist ein
  eigener Nutzer-Startknopf.

## §8 DECKUNGS-BERICHT (2026-08-14, vor jedem Training; volle Zahlen:
## evaluations/artifacts/ownership_corpus_coverage_report.json, exakt mit den
## Trainings-Label-Bauern _conjunctions_from_dome/_ownership_from_dome gerechnet)

8000/8000 Partien vollstaendig (0 unvollstaendige). Positive Partien je Seite
(p0/p1 nahezu symmetrisch -- die beidseitige Verdrahtung traegt; hier p0):

| Einheit | Basisrate Arm A (3000) | bester Anreicherungs-Arm | Hebung |
|---|---|---|---|
| SPALTEN voll (k1, +7) | 95 (3,2 %) | B: 419/1000 (42 %); E: 391 mit 506 EINHEITEN (Paare!) | ~13x |
| Diagonalen (k2, +10) | 11 (0,4 %) | C: 398/1000 (40 %) | ~100x |
| 8er-Ecken (k5) | 6 (0,2 %) | E: 546/1000 (55 %) | ~270x |
| 3er-Ecken (k5) | 2786 (93 %) | ueberall dicht | -- |
| Zeilen voll (k0) | 764 (25 %) | F: 394/1000 | -- |
| alle Joker (k3) | 1193 (40 %) | ueberall dicht | -- |
| Farbreihen (k7) | 191 (6 %) | Basisrate reicht (verteidigen-only) | -- |
| offene Specials Oe (k6) | 3,72 | F: 3,01 (bester), D-Heuristik 4,01 | Spektrum |

Bemerkenswert: Arm E liefert 506 Spalten-EINHEITEN in 391 Partien -- das
Spaltenpaar-Ziel erzeugt regelmaessig ZWEI volle Spalten je Partie (die
56-Punkte-Vision des Nutzers, als Trainingsmaterial). Die 8er-Ecken waren
vor Arm E im Korpus praktisch nicht existent (16 Partien in 4000) und sind
jetzt mit >1200 Einheiten vertreten.

**VERDIKT: Deckung gegeben, kein Kriterium duenn, beide Seiten symmetrisch --
der v2-Selektions-Hebel (§2) wird NICHT gebraucht. Der Korpus ist bereit;
das Training (warm-start, --ownership-weight 0,2 --conjunction
--extra-data-dir) ist der naechste NUTZER-Startknopf.**

## §9 TRAININGS-SWEEP ownership_weight (Nutzer-Auftrag 2026-08-14, vorab festgelegt)

Statt des Einzellaufs (0,2) ein Vier-Arm-Sweep, alle auf identischem Fenster
(v21-Standard + --extra-data-dir data/ownership_corpus), identischem Rezept
(v21: warm-start v21_2d_brierbest, lr 5e-5 cosine, WDL, 2D, nortv,
opp/endgame-Kopf, --select-by-brier), identischem Seed (2) und geteiltem
Cache:

| Arm | ownership_weight | Zweck |
|---|---|---|
| w0 | 0,0 | KONTROLLE: isoliert den Fenster-Effekt (neue 8000 Partien) vom Ownership-Loss-Effekt auf Policy/Value |
| w01 | 0,1 + --conjunction-head | leichte Dosis |
| w02 | 0,2 + --conjunction-head | Praezedenz-Dosis (own02-Lauf) |
| w05 | 0,5 + --conjunction-head | hohe Dosis |

**Entscheidungsregel (vorab)**: (1) Waechter: Arme, deren Policy-/Value-
Offline-Metriken (val_policy, Brier) gegen den w0-Arm NICHT wesentlich
abfallen, bleiben im Rennen (der w0-Arm ist der Vergleich, NICHT der alte
Champion -- das Fenster hat sich geaendert). (2) Unter den verbliebenen
entscheidet die KOPFGUETE nach Tor A (PREREG_ownership_consumer.md):
Brier/AUC je Feld gegen Basisrate + Rangkorrelation E_k je Kriterium auf
dem gemeinsamen Held-out. (3) Seed-Varianz-Vorbehalt (stehende Lehre:
Einzel-Seed-A/Bs sind fuer STAERKE-Aussagen uninterpretierbar): dieser
Sweep waehlt das Gewicht fuer den ERSTEN Tor-A-Anlauf, er ist KEIN
Staerke-Verdikt und KEIN Champion-Gating -- Staerke kommt erst mit dem
Verbraucher-Sweep (Tor C) und dann mit Arena-Disziplin.

Reihenfolge: nach den §23-GPU-Zellen (GPU-Konkurrenz), Arme sequentiell
w0 -> w01 -> w02 -> w05 (der w0-Arm baut den Cache). Pinning je Arm:
MOSAIC_DATA_EXCLUDE=v21_exclude_regex + MOSAIC_CARRIER_MANIFEST=v21;
Cache-NEUBAU ist beim ersten Arm ERWARTET (neue Dateimenge), danach
muessen die Arme "Lade HDF5-Cache" zeigen -- ein zweiter Neubau waere
der Alarm.

## §10 TOR-A-ERGEBNIS (2026-08-15/16) — der Kopf lernt die Geometrien

Messung: `tools/probes/ownership_gate_a.py`, 820 Held-out-Partien / 14.360
Bretter aus dem Val-Split (identisch ueber alle Arme: gleicher Seed 2,
gleiche Dateiliste). Rohzahlen: `evaluations/artifacts/ownership_gate_a_results.json`.
Alle Zahlen unten vom Koordinator am JSON nachgerechnet.

### §10.1 Waechter (§9 Punkt 1): kein Arm faellt durch

| Arm | policy val_loss | value Brier |
|---|---:|---:|
| w0 (Kontrolle) | 0,2138 | 0,1884 |
| w01 | 0,2139 | 0,1884 |
| w02 | 0,2138 | 0,1883 |
| w05 | 0,2139 | 0,1883 |

Der Ownership-Verlust kostet Policy/Value **nichts** (Unterschiede in der
4. Nachkommastelle). Alle Arme bleiben im Rennen.

### §10.2 Kopfguete: monoton im Gewicht, w05 gewinnt durchgehend

Feld-Ebene (36 eigene Felder, AUC; Basisraten-Prädiktor = 0,500):
w0 **0,502** (= blind, wie erwartet bei Gewicht 0) · w01 0,687 · w02 0,692 ·
w05 **0,709**. Feld-Brier w05 0,1631 gegen Basisrate 0,1828.

E_k-Rangkorrelation (Spearman, Mittelspiel-Prognose gegen tatsaechliche
Plattenpunkte am Ende) — die eigentliche Tor-A-Frage:

| Kriterium | w0 | w01 | w02 | w05 |
|---|---:|---:|---:|---:|
| Spalten k1 | −0,030 | 0,133 | 0,144 | **0,160** |
| Diagonalen k2 | −0,012 | 0,256 | 0,259 | **0,266** |
| Ecken k5 | 0,011 | 0,260 | 0,263 | **0,269** |
| Joker k3 | 0,018 | 0,166 | 0,163 | **0,172** |
| Zeilen k0 | 0,029 | 0,216 | 0,220 | **0,229** |
| Farbreihen k7 | −0,009 | 0,073 | 0,072 | 0,068 |

w0 liegt erwartungsgemaess bei 0 (untrainierter Kopf) — das validiert die
Messung selbst. Einzige Ausnahme der Monotonie ist k7, das laut
`neural_net.py:954` aus Ownership prinzipiell nicht lernbar ist.

### §10.3 ENTSCHEIDENDER NEBENBEFUND: die Checkpoint-Wahl ist das Nadeloehr

Bei ALLEN vier Armen faellt der `_best`-Checkpoint auf **Epoche 1** (Training
lief bis 15, Early Stop) — Auswahlkriterium ist `val_combined`, das den
Ownership-Verlust **gar nicht enthaelt**. Der gemessene Kopf hatte also genau
eine Epoche Training. Der `final`-Checkpoint (Epoche 15) desselben Laufs:

| Groesse (w05) | best (Ep. 1) | final (Ep. 15) |
|---|---:|---:|
| Feld-AUC eigene | 0,709 | **0,837** |
| Konjunktion Spalten k1 (AUC) | 0,745 | **0,957** |
| Konjunktion Diagonalen k2 | 0,788 | **0,984** |
| Konjunktion Ecken k5 | 0,827 | **0,963** |
| E_k Spearman k1 / k2 / k5 | 0,160 / 0,266 / 0,269 | **0,332 / 0,347 / 0,408** |
| policy val_loss | 0,2138 | 0,3002 |

Die Policy-Verschlechterung bei Epoche 15 ist **KEIN Ownership-Effekt**: der
Kontrollarm w0 (Gewicht 0,0) zeigt mit 0,3002 exakt denselben Wert — es ist
reines Ueberanpassen ueber 15 Epochen. Damit steht fest: weder `best`
(Kopf untertrainiert) noch `final` (Policy ueberangepasst) ist der richtige
Checkpoint.

### §10.4 VERDIKT & EMPFEHLUNG

**Tor A ist BESTANDEN**: der Kopf schlaegt die Basisrate auf allen
Ownership-lernbaren Kriterien deutlich, und E_k traegt echte
Vorhersagekraft (bis 0,41 Spearman) — er darf steuern.

**Gewicht: w05 (ownership_weight 0,5)** — bester Arm auf jedem Zielkriterium,
ohne Waechter-Kosten. VORBEHALT: der Trend ist ueber 0,1/0,2/0,5 monoton
steigend, das Optimum liegt also moeglicherweise OBERHALB von 0,5; der Sweep
ist nach oben nicht abgeschlossen.

**Vor dem Verbraucher-Bau zu klaeren (neuer, kleiner Arbeitsgang):** ein
ownership-bewusstes Auswahlkriterium bzw. ein Zwischen-Checkpoint. Der
naheliegende Weg — Trunk einfrieren und NUR den Kopf weitertrainieren (der
Nutzer-Vorschlag aus PREREG_provocation.md §10 Punkt 2) — loest genau diesen
Zielkonflikt: die Policy kann dann nicht ueberanpassen, waehrend der Kopf
seine 15 Epochen bekommt.

**Seed-Varianz-Vorbehalt (§9 unveraendert):** Einzel-Seed-Sweep. Dies waehlt
das Gewicht fuer den ersten Verbraucher-Anlauf, es ist KEIN Staerke-Verdikt.

### §10.5 NACHTRAG: fuenfter Arm w1 (ownership_weight 1,0)

**Post-hoc-Erweiterung, ehrlich als solche markiert** (Nutzer-Entscheid
2026-08-16 nach Sichtung von §10.2): der Sweep war mit vier Armen
vorregistriert; der beobachtete MONOTONE Anstieg ueber 0,1/0,2/0,5 macht
0,5 zu einem Randwert, nicht zu einem Optimum. Der Zusatzarm klaert, ob der
Anstieg weitergeht oder kippt.

Rezept **identisch** zu den vier Bestandsarmen (Warm-Start v21_2d_brierbest,
lr 5e-5 cosine, WDL, 2D, nortv, opp/endgame-Kopf, --select-by-brier,
--conjunction-head, --extra-data-dir, Seed 2) -- bewusst OHNE die in §10.3
empfohlene Auswahlkriterium-Aenderung, weil ein abweichendes Rezept den
Armvergleich zerstoeren wuerde. Der Checkpoint-Zielkonflikt aus §10.3 bleibt
also auch hier bestehen und wird wie bei den anderen Armen ueber die
zusaetzliche `final`-Messung sichtbar gemacht.

Auswertung mit demselben `tools/probes/ownership_gate_a.py` auf demselben
Held-out-Satz. Deutungsregel vorab: steigt w1 weiter, ist das Optimum immer
noch nicht eingeklammert (dann waere ein weiterer Arm faellig oder die
Gewichtsfrage als "nach oben offen, praktisch gedeckelt" zu schliessen);
faellt w1 gegen w05 ab, ist 0,5 als Optimum bestaetigt.

### §10.6 w1-ERGEBNIS: der Trend haelt -- und die Gewichtsfrage wandert weiter

Gemessen mit demselben `ownership_gate_a.py` auf demselben Held-out
(820 Partien, Dateilisten-Kontrolle bestanden). Rohzahlen:
`evaluations/artifacts/ownership_gate_a_w1.json`.

| Arm | Feld-AUC (best/final) | E_k k1 (final) | k2 | k5 | policy val_loss (best) |
|---|---|---:|---:|---:|---:|
| w05 | 0,709 / 0,837 | 0,332 | 0,347 | 0,408 | 0,2139 |
| **w1** | **0,726 / 0,870** | **0,361** | **0,354** | **0,466** | 0,2141 |

w1 gewinnt **jedes** Zielkriterium und jede Konjunktionsgruppe (Ecken
0,963 -> 0,981, Layout 0,910 -> 0,973). Der Waechter bleibt praktisch
unbewegt (policy 0,2139 -> 0,2141, Brier unveraendert 0,1884) -- die dritte
Nachkommastelle ist der erste zarte Hinweis auf Kosten, mehr nicht.

**Damit ist das Optimum WEITERHIN nicht eingeklammert.** Die ehrliche Lesart:
der Sweep hat gezeigt, dass mehr Ownership-Gewicht im gemeinsamen Training
bis 1,0 nur nuetzt, aber er hat kein Maximum gefunden.

**Trotzdem KEIN w2-Arm.** Begruendung, warum die Frage ihren Gegenstand
verliert: im Frozen-Trunk-Modus (PREREG_frozen_trunk_head.md) trainiert NUR
noch der Kopf. Das Ownership-Gewicht skaliert dann ausschliesslich den
Gradienten des einzigen lernenden Teils -- es wird faktisch zu einem zweiten
Lernraten-Faktor und verliert seine Bedeutung als Abwaegung zwischen Koepfen.
Die Abwaegung, die der Sweep messen sollte ("wie viel Kopf vertraegt die
Policy"), existiert dort nicht mehr. Ein w2-Arm im gemeinsamen Training
wuerde also eine Frage weiter verfolgen, die der naechste Schritt ohnehin
aufloest. Sollte Frozen-Trunk scheitern (Ausgang "Decke bestaetigt"), kommt
die Gewichtsfrage zurueck -- dann mit w2 als erstem Arm.

**Folge fuer F1**: die Vorab-Regel aus PREREG_frozen_trunk_head.md §3
("sollte w1 den Arm w05 schlagen, wandert F1 auf `v21_2d_own_w1_best` und
`--ownership-weight 1,0`") ist damit ausgeloest -- nach der dort genannten
Mehrheitsregel sogar einstimmig. F1 startet entsprechend, Referenz J ist der
w1-Satz.


## SCHLIESSUNGS-NACHTRAG (2026-08-20)

Status auf **ENTSCHIEDEN** gesetzt (Nutzer-Durchsicht der offenen Registrierungen). Begruendung: Tor A BESTANDEN (par.10.4, 2026-08-15/16): der Kopf schlaegt die Basisrate auf allen Geometrien; Korpus erzeugt, Deckung gegeben. Der Statuskopf hinkte dem eigenen par.10 nach (Stale-Korrektur 2026-08-20).
