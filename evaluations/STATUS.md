# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`** (juengstes Kapitel: "2026-08-13/14:
Generator-Kampagne abgeschlossen, GPU-Rundlauf geloest, Korpus-Plan").

---

## STAND 2026-08-14

**Champion unveraendert: `v21_2d_brierbest`, Elo 1358** [1292, 1434].
Paritaets-Hash `8c6684ff...` haelt (nach jedem Wheel-Neubau geprueft).
**AERA-REGEL seit dem RNG-Schnitt (`fe1e306`)**: Alt-Aera-Messwerte (auch
Generator-Benchmarks wie das fruehere 5,95) sind KEINE gueltigen
Vergleichsanker mehr -- gleiche Seeds erzeugen andere Partie-Verlaeufe
(Karten identisch, Nachfuellungen auf neuem Strom; Beleg history-Kapitel).

### Geltender Rahmen: Zwei-Pole -> Ownership-Kette (vollstaendig vorregistriert)

Basispol = Netz, Plattenpol = Bauer-Heuristiken/Heuristik; Regler = kuenftiges
Konsumenten-Gewicht des Ownership-Kopfs (`MOSAIC_OWNERSHIP_W`, zur Laufzeit
sweepbar). Die Kette:

- **`PREREG_ownership_corpus.md`** -- Lehr-Korpus, 6 Arme / 8000 Partien nach
  `data/ownership_corpus/`; Deckungs-Bericht VOR Training; Lebenszyklus par.5b.
  **Nutzer-GO erteilt**, bedingt auf die Startsequenz unten.
- **`PREREG_ownership_consumer.md`** -- Verbraucher (Blatt-Shift ueber E_k +
  marginale Feldwerte im Tiling-Solver, beides Default 0). **Tor A (Kopfguete:
  Brier/AUC je Feld gegen Basisrate, Rangkorrelation E_k) kommt VOR dem Bau.**
- **Abschaltkriterium der Injektion** (unveraendert gueltig): (1) steigt die
  Prior-Masse auf den Zielzuegen ueber Generationen? (2) haelt die Rate bei
  gesenktem Gewicht? Beides ja -> destilliert, Injektion kann runter.
  Messmittel: Raten je Partie + Heuristik-Kante, NICHT Geschwister-Arena.

### STARTSEQUENZ zur Korpus-Generierung

| # | Schritt | Stand |
|---|---|---|
| 1 | Vorzug-Verdrahtung (beidseitig) + 5x30-Wirkungsprobe je Arm | **ERLEDIGT** (5992f38; Probe: k1 2,80 / k5 8,30 nahe Arena-Niveau, Korpus-Prereg §3.5) |
| 2 | `PREREG_unified_game_loop.md` -- vier Schleifen vereinheitlicht | **ERLEDIGT** (307caa4..d9c49e6; Golden-Records 0 Bit alle Pfade, §5-Protokoll) |
| 3 | `PREREG_deterministic_labels.md` ("2b") -- Not-Deckel ehrlich | **ERLEDIGT** (3fcfed1; unter 12x CPU-Stress 0/1956 byte-identisch, §4; sync<->async-Gate-B-Retest offen bis wt_async2 frei) |
| 4 | GPU-Verdikt `PREREG_gpu_inferenzpfad.md` par.22 (N=64/128 tract/ORT) | **AGENT LAEUFT** (N=128-Zelle nach Detached-Prozess-Tod neu gestartet); bestimmt nur den Pfad (>=2,0x -> Async+ORT, sonst 8 Threads) |
| 5 | Generierung 8000 -> Deckungs-Bericht -> (eigener Startknopf) Training warm-start, `--ownership-weight 0,2 --conjunction --extra-data-dir` -> Tor A | **WARTET NUR NOCH auf 4** -- auch Arm D (pfadunabhaengig) zurueckgehalten, um die laufenden Partien/h-Zellen nicht zu verfaelschen. Ablage via MOSAIC_DATA_DIR=data/ownership_corpus (config.py:28) |

### Generator-Sortiment (aktuelle Aera, alle Zahlen nachgerechnet)

| Kriterium | Generator | Niveau | Status |
|---|---|---|---|
| k1 vertikal | Spaltenbau R3-Pfad (`MOSAIC_SPALTENBAU`) | 3,15 (8/20 Partien >=1 Spalte) | aktiv; Sicherheitsnetz/Jackpot/Special = Diagnose-Knoepfe AUS (par.15-17) |
| k2 diagonal | Plattenbauer + Special-Erweiterung (`MOSAIC_PLATTENBAU=2`) | 5,65 (13/23 volle Diagonalen) | UEBERNOMMEN par.18 |
| k5 Ecken | Spaltenpaar-Bauer (`MOSAIC_PLATTENBAU=5`) | 8,55 (13/22 >=11; 8er-Ecken erschlossen) | UEBERNOMMEN par.20 (staerkste der Kampagne) |
| k6 spezial | Heuristik (Referenz, Arm D) + Spezialbauer (Arm F, -9,75) | Heuristik -6,60..-11,10 | Kuppeldraft ABGELEHNT par.19 |
| k3/k4 | Beifang aller Arme | 5-6 / 10,6 | reicht |
| k0/k7 | nur Basisrate | 0,6-1,0 / 0,0 | Nutzer-Entscheid: verteidigen, nie anstreben; k7 aus Ownership nicht lernbar |

### GPU/Async-Front

Rundlauf-Engpass GELOEST (Condvar-Park/Wake statt recv_timeout,
net_batcher.rs:318; par.21: N=1 0,946x, N=16 0,979x -- vorher 0,053x).
Batch-Fuellung war nie das Problem (99,7 % bei N=128). Async-Architektur:
Gate A+B bestanden (Spielgeschehen bit-identisch). Offen: par.22
(Entscheidungszelle N=128 ORT gegen Regel 3 >=2,0x) und die
Trainingsziel-Divergenz -> Schritt 3 der Startsequenz.

### Offene Punkte ausserhalb der Startsequenz

| Punkt | Stand |
|---|---|
| **Dateinamen Welle 2** | TEILMENGE 1 ERLEDIGT 2026-08-14 (Tabelle am Ende von archive/history.md): column_build.rs, plate_builder.rs, provocation.rs, PREREG_provocation.md, seeds_per_criterion/, seed_selection_plates.*, provocation_acceptance.json, column_build_trace.py, plate_points_from_arena.py, game_manual_GUI.pptx (Lock war weg). OFFEN Teilmenge 2 (bis GPU-Agent fertig): PREREG_gpu_inferenzpfad->PREREG_gpu_inference_path, gpu_*-Dateien, async_gpu_stufe3_probe.jsonl (stufe->stage), paritaets_probe.py->parity_probe.py, gpu_inferenzpfad_ipc_roundtrip.py, data/gpu_messung/ |
| **Stoerungs-Baustein Farbzaehlung** | Nutzer-Auftrag steht (domain_knowledge.md Punkt 4); Messgroesse Gegner-Plattenpunkte gepaart + Frisch-Seed-Replikation; sinnvoll NACH dem Schleifen-Refactor (ein Einbauort statt vier) |
| **Architektur-Fahrplan Rest** | (1) PREREG_INDEX generieren statt von Hand (der A5-Hook prueft nur Konsistenz), (2) stille Test-Skips verbieten, (3) MOSAIC_*-Knopf-Registratur. Punkte 4+5 sind jetzt PREREG_unified_game_loop.md (Startsequenz Schritt 2) |
| **Torch-IPC-Reste (Weg A)** | Entfernung freigegeben, war wegen Datei-Konflikt uebersprungen -- nach dem Refactor nachholen |
| **Bootstrap-Horizont / Zufallsknoten / Stapelzug** | **ENTSCHIEDEN 2026-08-14 (Nutzer: "beibehalten")**: der Korpus-Start laeuft mit Horizont 2 und allen Defaults -- keine Zusatzvariablen im Lehr-Korpus. Die Preregs (bootstrap_horizon, chance_nodes) bleiben fuer einen KUENFTIGEN Fenster-Generierungsstart (v22) geparkt, nicht geschlossen |
| **Kopf-Warmstart Index-Abbildung** | fuer den Korpus-Trainingslauf pruefen: Champion-Checkpoint traegt den 140er-Kopf (untrainiert) -- Warm-Start formgleich, Abbildungsfrage stellt sich nur bei Alt-Checkpoints (122er). Kurzcheck vor dem Training |
| **Formungsterm Arm A/B** | Kontrast (gezaehlte Felder vs. Ownership-Marginale) geht im Consumer-Tor-C-Sweep auf -- kein eigener Task mehr |
| ~~"P0-P6"-Bezeichnung~~ | **AUSGEMUSTERT 2026-08-14** (Nutzer: obsolet; die Zuschreibung "Nutzer-Nomenklatur" war zudem falsch -- es war Koordinator-Nummerierung, nie verschriftlicht). Die Kette ist vollstaendig durch die Preregs abgedeckt (corpus/consumer + Abschaltkriterium oben). Verstreute "P4"-Erwaehnungen in alten Preregs meinen den Verbraucher-Bau |

---

## TASK-INDEX (nur OFFEN/LAUFEND)

| Task | Status |
| --- | --- |
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: braucht >=6 arena-entschiedene Paare (Stand ~3); Kandidaten-Metriken werden je Gating mitgefuehrt. `PREREG_post34_package.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT

**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die v21-Task-Queue.**
`PREREG_v22_window.md`: gleiche Form wie v21 (29.450 gesamt), juengster
Value-Posten 3.550 v19wdl-Rest + 1.450 v19wdlsw, Schwarm bleibt 74 %.
**Ab v22 ist die Rotationsregel stationaer.** Gating-H0-Vorbehalt: neuer
Batch desselben Generators braucht Suffix (`v20wdlb`).
**Hinweis 2026-08-14**: der Ownership-Korpus ist KEIN v22-Fenster -- er liegt
ausserhalb der Rotation (`data/ownership_corpus/`, additiv via
`--extra-data-dir`) und aendert diese Halde-Entscheidung nicht.

---

## GELTENDE REGELN (kompakt)

- **Seed-Skala der Arena bei n=400 (gemessen 2026-08-09)**: dieselbe
  Konfiguration (k=1, Champion@600 vs Heuristik@150dyn) ergab **76,0%**
  mit Basis-Seed 20260820 und **81,75%** mit 20260828 -- **5,75
  Prozentpunkte allein durch den Seed**. Das ist groesser als die
  meisten Effekte, die wir messen (λ, k=2, Denial-Varianten liegen alle
  darunter). Folge: **ungepaarte Vergleiche zwischen zwei Laeufen sind
  wertlos**, auch wenn beide n=400 haben. Jeder A/B braucht identische
  Basis-Seeds im SELBEN Instrument; wo zwei getrennte Laeufe noetig sind
  (unterschiedliche Sim-Budgets), muss der Basis-Seed gleich gesetzt und
  die Paarung ueber den Spielindex selbst gerechnet werden.

- **Champion**: `v21_2d_brierbest` seit 2026-08-09, **Elo 1358**
  [1292, 1434] (Vorgaenger `v20_2d_opp_brierbest` 1295). Die
  Erst-Schaetzung nach dem Gating (1416, CI +-92) beruhte auf einer
  einzigen Gegnerkante; mit Anker- und Champion-2-Kante sinkt das
  Niveau auf 1358 und das CI wird 23% enger (+-71) -- der ABSTAND zum
  Vorgaenger (+63) bleibt. Belegt den Wert von
  Promotions-Checkliste Punkt 3+4. Gating 75:45
  (SPRT-H1 nach 60 Paaren, p=0,0059) UND Frisch-Seed-Replikation 97:63
  (H1 nach 80 Paaren, p=0,0095) -- die Fruehstopp-Regel ist damit
  erfuellt. Alt-Messset-Brier 0,18636 vs 0,18749. **Erster Champion aus
  reiner Korpus-Skalierung**: identisches Rezept, +40% Fenster
  (29.450 Partien) von einem staerkeren Generator, plus
  `--endgame-head`. champion.txt gesetzt (wirkt nach Server-Neustart).
  Generator-Naming: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.

- **Fenster-Pinning -- ZWEI Variablen, nicht eine (verschaerft
  2026-08-09 nach einem Beinahe-Fehler)**: Ein Trainingsstart im
  v21-Fenster braucht BEIDE:
  
  ```
  export MOSAIC_DATA_EXCLUDE="$(cat evaluations/v21_exclude_regex.txt)"
  export MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_v21.json"
  ```
  
  `MOSAIC_CARRIER_MANIFEST` wurde beim `t_d_vw08`-Start VERGESSEN. Der
  Default ist `policy_carrier_manifest_v20.json`, also ein ANDERER
  Traeger-Satz: der Arm haette mit einer anderen Policy-Maske als
  `t_d_vw04` und als `v21_2d` trainiert und waere als Sweep-Arm wertlos
  gewesen -- ohne Fehlermeldung, nur mit plausiblen Zahlen. Der Lauf
  wurde gestoppt und korrekt neu gestartet; ein angefangener
  Falsch-Cache war noch nicht auf der Platte.
  **Verifikation ist Pflicht und zwar VOR dem Weggehen**: die
  Cache-Zeile muss `📦 Lade HDF5-Cache (2651 Dateien)` lauten.
  Steht dort `Lade Daten aus 2651 Dateien...`, ist der Cache-Schluessel
  anders -- Lauf sofort stoppen und die Ursache klaeren, NICHT einen
  Neubau durchlaufen lassen (er zementiert das falsche Fenster).
  Beweisweg fuer die Ursache (bei Bedarf wiederholbar): Cache-Key aus
  `str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+...+carriers`
  nachrechnen und mit den `data/.cache_*.h5`-Namen vergleichen -- die
  v21-Caches sind `26e304f5d2c7` (train, 2.651 Dateien) und
  `8a04a7143bbe` (val, 294). Merke: der **Cache-Key ist der einzige
  Waechter** ueber die Traeger-Wahl, das Lauf-Manifest protokolliert
  `MOSAIC_CARRIER_MANIFEST` NICHT (`engine_config`/`python_constants`
  waren zwischen richtigem und falschem Lauf identisch).
  Harmlos dagegen: die 55 archivierten v18-Dateien sind seit 10:16 aus
  `data/` heraus, `MOSAIC_DATA_EXCLUDE` schliesst nun 0 statt 55
  Dateien aus -- Split und Dateiliste sind trotzdem BEWEISBAR identisch
  (rekonstruiert und verglichen: 2.651/294 in beiden Faellen gleich).

- **NACHSCHUB BEI GATING-FEHLSCHLAG -- KORRIGIERTE FASSUNG
  (Nutzer 2026-08-09)**: Die Streichung des Nachschub-Ventils vom
  2026-08-07 war **generationsspezifisch** (v20-Zyklus, weil dort eine
  lange Nebentask-Liste offen war) und **KEINE stehende Anweisung** --
  ich hatte sie faelschlich verallgemeinert (auch in
  PREREG_v21_window.md, dort korrigiert).
  **ERSETZUNG (frischer Batch desselben Generators + Rausrotieren einer
  Alt-Generation) ist VERWORFEN** -- Nutzer-Argument, und es ist
  richtig: das ist indirekt mehr Volumen vom SELBEN Champion, waehrend
  die Diversitaet der alten Generationen aus dem Fenster fliegt. Genau
  die Generationen-Spreizung ist aber der Grund, ueberhaupt Alt-Material
  mitzufuehren.
  **Was bleibt: gezielte INJEKTION** (Sockel-Partien dazu, nichts
  verdraengt -- schont die Diversitaet). Bedingungen, damit daraus kein
  "solange nachlegen bis der Kandidat gewinnt" wird:
  
  1. Umfang und Entscheidungsregel VOR der Injektion schriftlich
     (Mini-Prereg), nicht nach dem verlorenen Gating improvisiert.
  2. Einmalig und begrenzt je Generation (Vorschlag: +2.000 Sockel),
     kein iteratives Nachlegen.
  3. Naming: derselbe Generator erzeugt ein Batch mit
     Unterscheidungs-Suffix (`v20wdlb`), sonst Datei-Kollision.
  4. Lesart des Ergebnisses: ein Sieg NACH Injektion belegt "die
     Generation brauchte mehr Policy-Material" -- NICHT, dass eine
     etwaige Rezept-Aenderung des Kandidaten gewirkt hat. Diese
     Unterscheidung muss im Verdikt stehen.
  5. Diagnostischer Rueckenwind erwuenscht (Policy-Wacht: fallen die
     Orakel-Metriken gegen die Vorgeneration, ist die Policy-Klasse der
     belegte Engpass), aber keine harte Vorbedingung -- Nutzer-Entscheid.

- **FENSTERGROESSE: FIXIERTE BASIS, Injektion ist die benannte Ausnahme
  (Nutzer-Entscheide 2026-08-09)**: 29.450 Partien / 2.945 Dateien / ~4,8 Mio.
  Zustaende bleiben die stehende Groesse. Die Rotation haelt sie
  konstant -- pro Windung 12.000 NEUE Partien (4.000 Sockel @600 +
  8.000 Schwarm @150), gleich viel altes Material rotiert raus. Folgen:
  (a) Kosten pro Generation KONSTANT (~18h Self-Play + ~3h Cache +
  ~3,5h Training), kein Anwachsen; (b) das Fenster wird mit jeder
  Windung FRISCHER statt groesser; (c) RAM/Cache-Budget stabil
  (~13 GB im Training, ~1 GB auf Platte).
  **Nicht neu aufrollen**: der Dosis-Befund ("Volumen half 6/6") ist
  eine stehende Versuchung, das Fenster generell zu vergroessern -- die
  Entscheidung dagegen ist bewusst gefallen (planbare Kosten,
  stationaeres Design ab v22). Eine DAUERHAFTE Vergroesserung braucht
  einen ausdruecklichen neuen Nutzer-Entscheid. Die einmalige,
  vorregistrierte Injektion bei Gating-Fehlschlag (s.o.) ist davon
  ausgenommen und veraendert die Basisgroesse nicht.

- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.

- **PROMOTIONS-CHECKLISTE (Nutzer-Hinweis 2026-08-09: die Kader-Praxis
  wurde bis dato nicht konsequent umgesetzt)** -- bei JEDEM
  Champion-Wechsel vollstaendig abarbeiten, nicht aus dem Gedaechtnis:
  
  1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
  2. Elo-Kante **Gating** (Champion-1) -- inkl. Replikations-Zeile, falls
     Fruehstopp <150 Paare.
  3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
     Fruehstopp** (Praezedenz v18/v19/v20-Verankerung).
  4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- **das ist der
     Punkt, der bei v20 UND v21 zunaechst fehlte**; ohne ihn ruht die
     Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating:
     CI +-90 Punkte).
  5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
     Eintrag in die #29-Buchfuehrung.
     5b. **Anzeige-Kalibrierung nachziehen**: die Platt-Parameter A/B des
     NEUEN Champions in `server.py` (`_DISPLAY_CAL_A/_B`) eintragen --
     sie sind modellspezifisch. Quelle: `tools/platt_fit.py --models
     models/alphazero_<neu>.pth`. Ohne das zeigt die GUI die
     Gewinnwahrscheinlichkeit mit der Kurve des VORGAENGERS an.
     5c. **sigma/Prior-Balance messen** (neu 2026-08-09, aus Task G):
     `tools/gumbel_scale_calibration.py --model <neu> --sims 400
     --n-states 300`, ~10 min. Der Aera-Wechsel v18->v21 hat das
     Verhaeltnis von 1,232 auf **2,287** verschoben (delta_q verdoppelt,
     delta_ln(prior) unveraendert) -- R3 liegt mit 2,972 praktisch auf
     der Wiedereroeffnungs-Schwelle. **Ueberschreitet die
     Gesamt-Kennzahl 3, oeffnet sich die c_visit/c_scale-Familie per
     REGEL wieder** (kein Ermessen). Zugleich Verfallsdatum-Waechter
     fuer die H0-Befunde der Wurzel-Regler-Familie: die wurden in einem
     anderen Balance-Regime gemessen.
  6. STATUS-Champion-Zeile + history-Kapitel.
     **Nachtrag-Schuld ERLEDIGT** (Klarstellung 2026-08-10): die v20-Kante zu
     `v19_best` lief am 2026-08-09 -- 114:76 ueber 190 Partien, SPRT-H1 nach 95
     Paaren, p=0,0043 (`elo_history.csv` Zeile 53,
     `paired_gating_v20_vs_v19best_nachtrag.json`). Die alte "fehlt"-Zeile hier
     hat mich zweimal dazu verleitet, die Messung erneut vorzuschlagen.
     **Elo-Fragen am Primaerregister `elo_history.csv` pruefen, nicht an dieser
     Datei.**

- **LOESCHEN NUR MIT EXPLIZITER RUECKFRAGE (Nutzer-Regel 2026-08-08,
  dritter Vorfall dieser Klasse -- "inakzeptabel")**: Kein Loeschen,
  Verschieben oder Ueberschreiben von Dateien, Ordnern oder Worktrees
  ohne vorherige, den KONKRETEN Pfad benennende Nutzer-Freigabe.
  Ausnahme: das eigene Scratch-Verzeichnis.
  Im Einzelnen:
  
  1. **Eine FRAGE ist keine Anweisung.** "Ist X noch aktuell?", "kann
     man X weg?", "brauchen wir X?" verlangen eine ANTWORT. Handeln
     erst nach einem Imperativ, der das Ziel nennt.
  2. Als Loeschen gelten auch: `git worktree remove`, `git checkout --`,
     `git reset --hard`, `git clean -fd`, `mv` aus dem Projekt heraus,
     `rm` auf generierte Artefakte (Caches sind KEINE Ausnahme -- die
     Freigabe vom 2026-08-08 galt fuer sechs namentlich genannte Dateien).
  3. Vor jeder freigegebenen Loeschung: Ziel ANSEHEN (Inhalt, Groesse,
     Reparse-Points bei Worktrees -- Junction-Vorfall 2026-07-24), das
     Ergebnis der Pruefung BERICHTEN, und nur dann ausfuehren.
  4. Gilt fuer Sub-Agents identisch und steht in jedem Agent-Prompt.
  5. "Aufraeumen" ist niemals selbst-autorisiert -- auch dann nicht,
     wenn etwas offensichtlich veraltet ist.

- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.

- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).

- **AUFLOESUNG SCHLAEGT SPARSAMKEIT (Nutzer-Regel 2026-08-08)**: Wenn
  eine Entscheidung an einer Differenz haengt, die UNTERHALB der
  Auflösung des Offline-Instruments liegt (Value-Seite: Brier-Gaps
  <0,015 sagten 0/4 die Arena voraus; gemessene Seed-Skala ~0,0006),
  dann darf das Offline-Mass die Entscheidung NICHT tragen -- auch nicht
  als Spar-Vorfilter ("nur gaten, wenn Brier X schlaegt"). Stattdessen
  die ARENA in die Abwaegung nehmen und die Kosten AUSRECHNEN, nicht
  schaetzen: ein Gating (~1-1,5h CPU, 200 Paare @400) ist regelmaessig
  BILLIGER als das Training, das man sich mit dem Vorfilter sparen
  wollte (~3,5h GPU) -- und es ist das einzige validierte Instrument.
  Wer auf einem blinden Mass spart, spart die billige Ressource und
  riskiert die teure Fehlentscheidung.
  **Ausnahme Policy-Seite**: die Orakel-Metriken (Prior-Masse Top-3,
  Kendall-Tau) sind arena-validiert (7/7) und DUERFEN als Vorfilter
  dienen -- so entschieden bei #35b (beide Metriken schlechter -> kein
  Gating). Der Unterschied ist der Validierungsstand, nicht die
  Bequemlichkeit.
  Zusatznutzen, den man mitnehmen soll: jedes gefahrene Gating liefert
  ein arena-ENTSCHIEDENES Paar -- die Waehrung, in der #29 (Validierung
  eines Offline-Value-Praediktors) bezahlt wird (Stand ~3, noetig >=6).

- **Aggressions-/Denial-Programm GESCHLOSSEN** (2026-08-07): alle
  Knoepfe auf Default (w=0, λ=0, ε=0, bias=1); "gate what you ship";
  Wiedervorlage nur mit messbar schaerferem opp-Kopf
  (PREREG_aggression_style_measurement/PREREG_denial_tiebreak).

- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).

- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).

- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).

- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blind_spot.md`, Tasks E/F/G dazu
  geschlossen -> history): Q-Skalierungs-Varianz ist JA protokolliert
  (`tools/gumbel_scale_calibration.py`), **Ueberlebensrate im
  Sequential Halving NEIN** -- vorhanden sind `root_child_q`,
  `root_num_actions(_considered)` und `max_depth`, aber nicht, welcher
  Kandidat welche Halbierungsphase uebersteht. Bewusst nicht
  nachgeruestet: Task E hatte zuerst zeigen muessen, ob die MENGE
  stimmt (Ergebnis: Miss-Rate 1,21%, weit unter der 5%-Schwelle).

## Architektur, Stand jetzt (aktualisiert 2026-08-06)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):

- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2`.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting`, Blattwert = exakter Endscore inkl.
  Wertungsplatten. **Seit 2026-08-10 EXPECTIMINIMAX, nicht mehr reines
  Alpha-Beta**: Zufallsknoten an den Aufdeck-Stellen der verdeckten
  Chip-Zuordnung (16 der 20 Chips sind aus R1-4 bekannt, unbekannt ist nur
  die Fabrik-Position der restlichen 4). Kein Pruning in Zufallsknoten
  (Star1/Star2 bewusst weggelassen). `NODE_BUDGET=200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus),
  `MOSAIC_R5_CHANCE_NODES` (**Default AN** seit 2026-08-10, `=0` stellt das
  Altverhalten her), `MOSAIC_R5_NODE_BUDGET`, `MOSAIC_R5_NET_SOLVER`
  (Default an).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):

- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`, seit
  Task #28 zusaetzlich `opp_points` (nur in Modellen, die damit trainiert
  wurden -- Engine erkennt ihn per Output-NAME und faellt sonst auf
  Bestandsverhalten zurueck). **`plate_head` wurde am 2026-08-10 gebaut und
  wieder ENTFERNT** -- der Ownership-Kopf ist der Randlayer.
  `ownership` ist seit 2026-08-10 **140 breit** (72 Feldlabels + 68
  Konjunktionen, Breite an config.py:117-118 + Label-Bauer verifiziert
  2026-08-14); `OWNERSHIP_WEIGHT` steht in `config.py` weiter auf 0 --
  der Champion-Kopf ist untrainiert. Naechster Lauf mit Gewicht 0,2 +
  `--conjunction` ist der Korpus-Trainingslauf (PREREG_ownership_corpus.md).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, **`VALUE_OPP_EPSILON = 0,0`** (war 0,1 bis Schema 19).
- **Punkte-ZIEL (Schema 20, 2026-08-10)**:
  `points_val = tanh(own_total/VALUE_SCALE)` -- der Gegner-Anteil ist
  ENTFERNT. Fuer VOR Schema 20 trainierte Modelle bedeutet ihr
  `points`-Ausgang weiter `own - 0,1*opp`; fuer die Spielstaerke belanglos,
  weil die Ausgabe im Suchpfad ohnehin verworfen wird
  (`POINTS_UTILITY_WEIGHT = 0` und `w = 0`).
- **Value-ZIEL (#34-Verdikt, Schema 17 unveraendert gueltig)**: `values_wdl`
  = TD-Blend aus Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang;
  Alt-Datei-Bootstraps werden beim Cache-Bau Platt-entstaucht
  (A=0,0051/B=1,9269), `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben
  roh. Training: `--value-head wdl --select-by-brier` (KEIN destretch-Flag
  mehr noetig). **Das Ziel ist margen-BLIND** -- siehe Abschnitt STAND,
  "warum das Netz nicht punktoptimiert spielt".
  Policy-Traeger-Manifest **`data/policy_carrier_manifest_v21.json`**
  (Default in `neural_net.py` ist noch die v20-Datei -- ein Trainingsstart
  im v21-Fenster MUSS `MOSAIC_CARRIER_MANIFEST` setzen, s. Fenster-Pinning
  oben), maskiert Alt-Dateien ausser 135 v19wdl + 45 v18, plus
  `carrier_prefixes: ["selfplay_v20wdl_"]`; alles im Cache-Key.
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> **`v21_2d_brierbest`**.

---

## Task #38 (geparkt, Arbeitskreis "Spaeter" mit #31): Moon-Head-Feinschliff (2026-08-05)

Befund aus einer Interesse-Frage des Nutzers, Code verifiziert. Der Kopf
selbst ist solide (Plackett-Luce-Faktorisierung der Mond-Reihenfolge aus
dem Policy-Raum, Labels vom exakten Rundensolver, Prior-Aufteilung in der
Expansion). Zwei nie untersuchte Punkte fuer spaeter:

1. **Loss-Gewicht**: `moon_nll` wird mit VOLLEM Gewicht 1,0 in den
   Policy-Loss addiert (train.py, `p_loss + moon_nll[sun_mask].mean()`)
   -- bei NLL ~0,5-1 gegen Policy ~1,9 beansprucht ein Teilproblem, das
   nur Sonnenzuege betrifft, potenziell ~1/3 des Policy-Gradienten. Nie
   gesweept (VALUE_WEIGHT-Blindfleck-Muster). Als Arm in einen
   kuenftigen Loss-Gewichts-Sweep.
2. **Label-Horizont** (Nutzer-Einordnung 2026-08-05, RELATIVIERT):
   Referenz maximiert den RUNDENendstand (`solve_round_final_score`).
   Da die Fabriken zu Rundenbeginn NEU befuellt werden, ist der
   Wirkhorizont einer Reihenfolge im Wesentlichen die laufende Runde --
   das Solver-Label ist also naeher am Optimum als zunaechst vermutet,
   Restpunkt sind allenfalls Randeffekte. Falls Labels je aus der Suche
   kommen (root_child_q aus #35 liefert die Q-Ordnung der Varianten ab
   v20 gratis), waere das ein billiger A/B, kein Pflichtumbau.
   Kein akuter Bedarf: Policy-Seite ist ueber die Orakel-Metriken
   arena-validiert, inkl. PL-Aufteilung.

## Task #39 (geparkt, Arbeitskreis "Spaeter" mit #31/#38): Startkuppel-Platzierung (2026-08-06)

Nutzer-Beobachtung "setzt sie gefuehlt immer an dieselbe Position" --
am Code bestaetigt und MECHANISCH erklaert
(`self_play.rs::choose_start_placement`): der Farb-Score ist
POSITIONS-unabhaengig (summiert nur Fabrik-Farbhaeufigkeiten je Feld),
der Eckbonus fuer alle 4 Ecken identisch (0,5), Ties behaelt der erste
Kandidat -> IMMER Ecke (0,0); die Feld-Summe ist zudem
ROTATIONS-invariant -> immer 0 Grad. Position/Rotation sind tote
Freiheitsgrade; nur die Platten-WAHL variiert. Gilt ueberall (GUI,
Arena, Self-Play; Startplatzierung ist policy-maskiert, das Netz lernt
sie nie).

**Nutzer-Einordnung (2026-08-06, schaerft den Zuschnitt)**: die Ecke an
sich ist strategisch RICHTIG (Rand/Diagonale/Eckplatten honorieren sie
alle) -- das Problem ist die MONOTONIE, nicht die Position.
**KORREKTUR (Nutzer 2026-08-06, zweite Runde)**: auch der Ecken-Rang
(3 oben / 8 unten) ist KEIN Bewertungsfehler -- Kuppelzeile 0 wird von
den SCHNELLSTEN Musterreihen (1-2, Kapazitaet 1-2 Steine) gespeist: die
obere Ecke kommt frueher in Wertung + Orthogonal-Bonus und wird
zuverlaessiger ueberhaupt komplett; die 8 Punkte unten haengen an den
traegsten Reihen (5-6). Der (0,0)-Tie-Break loest den Trade-off implizit
RICHTIG auf. Verbleibende Substanz von #39:
(1) ROTATION -- bestimmt Farb-Ausrichtung zur Brettmitte und
Sonderfeld-Lage, heute verschenkt (Score rotationsinvariant);
(2) MONOTONIE/Tie-Break -- Diversitaets-Frage (GUI-Abwechslung +
Korpus-Vielfalt), keine Staerke-Frage.
**Verbesserungs-Optionen (bei Angehen abzuwaegen)**:
a) Heuristik-Upgrade: Rotations-Bewertung + randomisierter Tie-Break
   unter nahezu gleichwertigen Kandidaten; jede Aenderung per Arena
   gegen den Bestand pruefen (die Strategie-Intuition des Koordinators
   lag hier zweimal daneben, die des Nutzers zweimal richtig).
b) Prinzipiell: Platzierung in den Aktionsraum der Suche -- ACHTUNG
   NUM_ACTIONS-Aenderung macht alte Checkpoints unbrauchbar
   ([[num-actions-change-breaks-old-checkpoints]]), teuer.
**Randbedingung**: NICHT waehrend einer laufenden Kampagne aendern
(verschiebt die Self-Play-Zustandsverteilung); fruehestens v21-Setup.
Nebenaspekt: die heutige Uniformitaet kostet auch Zustands-Diversitaet
im Korpus.

## Task #31 (vorgemerkt): Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem (2026-08-03)

**Nutzer-Auftrag**: Staerke-Skalierung fuer Mensch-Spiele; Einschaetzung
"Sims allein richten es nicht" ist KORREKT und hier besonders: (a) R5-
Alpha-Beta + Tiling-DFS spielen sim-unabhaengig exakt -- eine 20-Sims-KI
spielt trotzdem perfekte Endspiele; (b) Gumbel+Policy-Prior traegt auch
Mini-Budgets -- flacher, aber nicht menschlich-fehlbar.

**Design-Skizze (3 Hebel je Stufe)**: Sims-Budget + Endspiel-/Tiling-
Degradation (R5-Knotenbudget-Override bzw. Policy-Sampling statt Solver,
Tiling greedy statt exakt bei "leicht") + Fehler-Injektion via Root-
Temperatur-Sampling mit Q-GAP-DECKEL (nur plausible Fehler <=3-5 Punkte;
menschlich-fehlbar statt gleichmaessig-flach; loest auch Ausrechenbarkeit).
Stufen: extrem=Champion@600-800 (optional lambda_aggr als Stil),
schwer=heutiger Stand @400, mittel=~100-150 Sims + Deckel-Sampling +
reduziertes R5-Budget, leicht=~8-16 Sims + Temperatur hoeher + epsilon +
Greedy-Tiling. ABGERATEN: alte Generationen als Stufen (Wartung,
OneDrive-Risiko, Regel-Fix-Inkompatibilitaeten, "gleichmaessig schwach").

**Kalibrierung**: vorhandene Elo-Leiter + Heuristik-Anker; je Konfiguration
n=150 vs 2 Anker, Ziel-Baender ~leicht 700-800 / mittel ~1000 / schwer
~1150-1200 / extrem=Champion. Umsetzung nach Muster Task #28
(Laufzeit-Parameter + Server-Preset + GUI-Dropdown). OFFEN (Nutzer):
Ziel-Baender ok? Darf "leicht" sichtbar Endspiele verstolpern?

**GATE (Nutzer-Entscheid 2026-08-03): ZURUECKGESTELLT** -- wird erst
angegangen, wenn ein Champion existiert, der auch gute menschliche
Spieler wirklich fordert. Bis dahin bleibt die Prioritaet auf
Staerke-Arbeit (v20-Zyklus, Value-Head-Front #29/#30, lambda=0.7-
Kandidat), nicht auf Schwierigkeits-UX.
