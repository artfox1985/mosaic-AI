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

## §4 Training + Abnahme (Tor A aus PREREG_ownership_consumer.md)

- Warm-Start vom Champion (v21_2d_brierbest), Standard-Rezept (lr 5e-5,
  cosine), `--ownership-weight 0,2` (Präzedenz: own02-Lauf) + `--conjunction`.
- Fenster: aktuelles Standard-Fenster + `data/ownership_corpus/` (additiv).
- Während Generierung nie gleichzeitig trainieren ohne
  MOSAIC_DATA_EXCLUDE-Pinning (stehende Regel).
- **Abnahme = Kopfgüte, NICHT Arena**: je Feld Brier/AUC gegen die Basisrate
  auf Held-out-Partien (Split auf Partie-Ebene); je Kriterium Rangkorrelation
  E_k gegen tatsächliche Plattenpunkte; Bericht getrennt nach eigener und
  Gegner-Hälfte. Erst nach bestandenem Tor A wird der Verbraucher (P4)
  gebaut.
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
