# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`** (ausgelagert 2026-08-09, erste Runde:
TASK-INDEX-Zeilen Platten-Intervention/τ-Annealing/v21-Fenster-Altstand/
Messset-Snapshot-Teil/#35b/λ/#37/frozen-Set-Neubau, Abschnitt NAECHSTE
SCHRITTE, Abschnitt OFFENES GATING (λ-Arm), Review-Punkte B+C; zweite
Runde: TASK-INDEX-Zeile Messset-Snapshot+v16/v17-Freigabe (jetzt
komplett erledigt), Review-Zeile A + Abgelehnt/erledigt-Sammelnotiz,
kompletter Abschnitt "AUS EXTERNEM REVIEW R2 2026-08-09" (E/F/G),
NACH-v21-QUEUE Punkt 1/E3b).

---

## TASK-INDEX (nur OFFEN/LAUFEND, Stand 2026-08-09)

| Task | Status |
|---|---|
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: Validierung braucht arena-ENTSCHIEDENE Paare; die WDL-Aera hat bisher nur ~3 (v20>v19, E3-Arme signifikant schlechter) -- unter dem 6-Paar-Standard der Policy-Orakel-Validierung. Kandidaten-Metriken (Brier auf frozen_v2, R5-Steigung) werden ab jetzt je Gating MITGEFUEHRT; Verdikt, sobald >=6 entschiedene Paare vorliegen. `PREREG_nach34_paket.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

**UEBERGABE-DOKUMENT (2026-08-08): `evaluations/UEBERGABE_v21_spirale.md`** -- vollstaendige Kommandos + Regeln fuer die v21-Spirale, geschrieben fuer den naechsten Koordinator; dort zuerst lesen.

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT
**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die
v21-Task-Queue abarbeiten.** Der Zuschnitt ist nur festgehalten, damit
er spaeter nicht neu diskutiert werden muss.

`PREREG_v22_fenster.md`: gleiche Form wie v21 (5.800 Policy / 23.650
Value / 29.450 gesamt), alles altert eine Stufe. Juengster Value-Posten
= **3.550 v19wdl-Rest (@600, vollstaendig) + 1.450 v19wdlsw** statt
5.000 Schwarm -> Schwarm-Anteil bleibt bei 74% statt auf 89% zu
steigen. **Ab v22 ist die Rotationsregel stationaer** (v21 war die
letzte Uebergangsgeneration). Vorbehalt fuer v21-Gating-H0: neuer
Batch desselben Generators braucht ein Suffix (`v20wdlb`).

### AUS EXTERNEM REVIEW 2026-08-08 (`EXTERNES_REVIEW_2026-08-08.md`)

| Task | Kurz |
|---|---|
| **D: GEWICHTS-SWEEP (erweitert)** | **Vorregistrierung nachgezogen 2026-08-09 VOR jedem Gating: `PREREG_task_d_gewichte.md`** (Regeln standen bisher nur in dieser Tabellenzeile -- fuer ein mehrarmiges Arena-Experiment zu wenig). Loss-Anteile gemessen: Policy 90,1%, **Value nur 6,5%** -- obwohl die Hybrid-Attribution die Staerke dem VALUE-Kopf zuschreibt; VALUE_WEIGHT=0,2 stammt aus der MSE-Aera und wurde beim BCE-Wechsel nie nachgezogen, nach OBEN ist ungemessen. 4 Arme: Kontrolle, vw04, vw08, pw025. **ARENA entscheidet** (Nutzer: Gating ~1,5h CPU < Training ~3,5h GPU und das einzige validierte Instrument): je Arm Gating vs Kontrolle `v21_2d`, Sieger zusaetzlich vs Champion; Brier/Orakel nur deskriptiv -- liefert zugleich die #29 fehlenden entschiedenen Paare |

### NACHTPROTOKOLL 2026-08-10 (Nutzer schlaeft, Auftrag "keinen Leerlauf")

**Fertig geworden, mit Verdikt:**

| Punkt | Ergebnis |
|-------|----------|
| **Punkte-Blend `w>0`** | **REGEL 2, GESCHLOSSEN**: Kontrolle 321/400 (80,25 %) gegen Arm 300/400 (75,00 %), Block-Delta -5,25pp bei t=-2,68, McNemar p=0,0527. w bleibt 0, Richtung eher schaedlich. Die +6pp der Aggressions-Neukartierung sind mit doppelter Stichprobe UMGEKEHRT -- Lehrstueck zur Seed-Skala. |
| **#82 GPU-Batcher** | **REGEL 1, GESCHLOSSEN**: erreichbare Batches 11/22/44 liefern 2.581/6.197/14.060 Evals/s, alle unter der unteren CPU-Schranke 17.600. Die GPU ist nicht langsam, sondern ausgehungert (Break-even ~64-128). |
| **GPU-Verlagerung** (neu vorregistriert) | Teil 1+2 geschlossen: Speicher ist kein Engpass (1,5 MiB je Suche), erreichbarer Batch analytisch **140-590** ⇒ Gewinnzone. Weg V (Verschraenkung, suchneutral) statt Virtual Loss. Startwert N=256. |
| **Wheel + Golden-Waechter** | installiert, Paritaet BEWIESEN (`8c6684ff...`), A2-Vertragsstempel `a169ebf0a4451e08` erstmals am installierten Binary befragbar. |
| **Runde 5** | Zufallsknoten SCHARF -- die Suche ist jetzt Expectiminimax. Versatz null gemessen (-0,47 Pkt, SE 0,66, t=-0,71 ueber 43 Abweichungen). |
| **Plattenkopf-Rauchtest** | **c6 traegt (Skill +0,574), c3 NICHT (-0,036 und fallend)**. Gebaut wird nur c6; c3 bleibt offen, nicht verworfen. |

**PLATTENKOPF STUFE A ABGESCHLOSSEN UND REPLIZIERT.** c6-Skill **+0,637**
(v20-Korpus, 2.537 Partien) und **+0,655** (v19-Korpus, 2.530 Partien);
c3 bei +0,004 / -0,008, also ohne Skill ⇒ **c3 bleibt draussen**. Der
inhaltliche Kern ist der **Slot-Gradient**: ein Spezialfeld bleibt in der
unteren Slot-Reihe in ~84 % der Partien leer, in der oberen in ~13 % --
monoton, und ueber zwei Generator-Aeren praktisch deckungsgleich, also
Spielstruktur statt Champion-Verhalten. Das bestaetigt die Nutzer-Taktik
("keine Spezialkuppeln in Slot-Reihe 3") quantitativ und begruendet die
Slot-weise Fassung: ein Aggregat wuerde den Gradienten verschlucken, genau
wie die Heuristik mit ihrem pauschalen `-3 * special_empty`.
Vorbehalt: alle Platt-Steigungen liegen unter 1 (0,44-0,81), der Kopf ist
uebermuetig ⇒ Platt-Parameter je Slot sind fuer Stufe B PFLICHT.
Logs: `logs/plattenkopf_stufeA.log`, `logs/plattenkopf_stufeA_v19.log`.

**MODELLSEITE GEBAUT**: `plate_head` (9 Logits) in beiden Modellklassen,
additiv, Default aus, Ausgabe zuletzt im Tupel, Praesenz aus dem Checkpoint.
Champion laedt unveraendert. Der Groessen-Ratschen-Waechter hat den ersten
Versuch abgelehnt -- Antwort war Kuerzung statt neuer Basislinie, die Datei
ist jetzt netto kleiner als vorher.

**Laeuft jetzt (CPU):** Label-Dump ueber den GESAMTEN Korpus nach
`data/plate_labels_v1.json` (Partie -> 9 Atome je Spieler + aktive Platten).
Log: `logs/plattenkopf_labels_dump.log`. Die Labels braucht JEDE
Verdrahtungsvariante, deshalb zuerst.

**ENTSCHEIDUNG FUER DEN MORGEN -- zwei Wege fuer die Verdrahtung:**
1. **Seitendatei** (laeuft gerade): `train.py` liest `plate_labels_v1.json`
   und verbindet ueber `game_id`. Beruehrt den gemeinsamen Cache-Pfad NICHT.
   Haken: der HDF5-Cache fuehrt `game_id` moeglicherweise nicht mit -- das
   ist VOR dem Bau zu pruefen.
2. **In den Cache**, mit Key-Suffix `+plate_v1` nur bei gesetztem Flag
   (Muster `+enc2d_v1`). Sauberer im Datenfluss, aber eine Aenderung am
   gemeinsamen Cache-Bau. **KEIN `VALUE_SCHEMA_VERSION`-Bump** -- der wuerde
   den vorhandenen v21-Cache entwerten, ohne Not.

Ich habe Weg 2 heute Nacht bewusst NICHT begonnen: `MosaicDataset` ist die
delikateste verbleibende Stelle, und ein Fehler dort haette eine
Cache-Neubau-Nacht gekostet. Danach in beiden Faellen: Verlustterm in
`train.py` mit Maskierung auf Partien mit aktiver Platte 6, dann
Integrationsprobe auf ~10 Dateien und 1 Epoche, DANN der volle Lauf.

**Frueherer Stand (Stufe A lief noch):** Stufe A des Plattenkopfs --
400 Dateien, bis 300.000 Zustaende, Schnitt nach Partie, Fruehstopp, plus
**Kalibrierung je Slot** (Platt-Steigung), die die Vorregistrierung als
Entscheidungsgroesse verlangt. Log: `logs/plattenkopf_stufeA.log`.

**BEWUSST NICHT gestartet: der volle Plattenkopf-Nachtlauf.** Er haette
verlangt, `neural_net.py` und `train.py` unbeaufsichtigt umzubauen und danach
6,5 h Maschinenzeit auf ungetesteten Integrationscode zu setzen. Ein
subtiler Fehler dort haette die Nacht UND den Trainingspfad gekostet.
Stattdessen laeuft die Messung, die der Vorregistrierung ohnehin fehlt und
die das Integrationsrisiko fast auf null senkt: traegt der Rumpf c6, ist der
Rest Verdrahtung.

**Fuer den Morgen vorbereitet, noch nicht ausgefuehrt:**
1. Kopf `plate_c6` (9 Ausgaben) in `neural_net.py`, additiv hinter einem
   Flag, Default aus -- Bestandspfad byte-identisch.
2. Labels ueber `tools/plattenkopf_labels.py` in den Cache-Bau; Cache-Key
   bekommt `+plate_v1` NUR bei gesetztem Flag, damit der vorhandene
   v21-Cache NICHT entwertet wird (kein `VALUE_SCHEMA_VERSION`-Bump).
3. Erst Mini-Cache auf ~10 Dateien + 1 Epoche als Integrationsprobe, dann
   der volle Lauf.

**Fehler dieser Nacht, protokolliert:** Hintergrundlauf durch `tail`
geleitet (puffert bis Prozessende -- die Arena sah tot aus, lief aber);
Handzerlegung der Blatt-Erzeugungsrate ergab 120 % Inferenzanteil und war
ungueltig; ein Null-Evaluator waere der falsche Ersatz gewesen (degenerierte
Suche), und `profiling.rs` hatte die Zahl seit Task #32 laengst -- zweimal an
einem vorhandenen Werkzeug vorbeigebaut.

### LAUFENDE QUEUE (Stand 2026-08-10 nachts)

| Bahn | laeuft jetzt | danach |
|---|---|---|
| **CPU** | **Punkte-Blend `w>0`** (`PREREG_punkte_blend_w.md`, 2x400 @400, Basis-Seed 20260902, Arme `0,2.0` / `0.1,2.0`) | Plattenkopf-Gating |
| **GPU** | frei (Batcher-Probe erledigt) | Plattenkopf: Cache-Neubau (~3h) + Training (~3,5h) |
| **offline** | Plattenkopf-Code: Kopf in `neural_net.py`, Label-Einbau ueber `tools/plattenkopf_labels.py`, Schema-Bump | -- |

**PLATTENKOPF EINGETAKTET** (Nutzer 2026-08-10, "danach eintakten"), Reihenfolge:
1. Kopf + Labels + Schema-Bump schreiben -- **kostet keine Maschinenzeit**, laeuft
   parallel zum Blend-Gating.
2. Cache-Neubau, sobald die CPU-Bahn frei ist (der Bump invalidiert den gemeinsamen
   Cache; die Sperre dafuer war Task D und ist gefallen).
3. Training, Rezept wie der Champion (warm-start, lr 5e-5, cosine,
   `--value-head wdl --select-by-brier`).
4. **BEIDE** Auswertungen: Arena-Gating vs Champion UND Brier-Skill-Score je
   Kriterium. Eine allein ist nicht interpretierbar -- ein Arena-Null liesse offen,
   ob der Kopf nichts gelernt hat oder es gelernt hat und nicht hilft.

Grundraten liegen vor (800 Endbretter, Champion-Partien): Kriterium 6 bei 83,3 %
leeren Spezialfeldern (Mittelband ⇒ tragfaehig), Kriterium 3 bei 42,0 %,
Jokerfelder 1..8. Labels sind minimal veraltet (letzter Datensatz = letzter
Tiling-Schritt) -- tragbar fuer die Probe, nicht fuer einen Champion-Kandidaten.

**WHEEL: installiert 2026-08-10, Paritaet BEWIESEN.** Neubau aus den heutigen
Quellen, `tools/paritaets_probe.py` liefert `8c6684ff...` (156 Diagnose-Vorkommen
ausgeblendet, Begruendung im Skript). A2 ist damit erstmals am INSTALLIERTEN Binary
befragbar: `contract_hash = a169ebf0a4451e08`, wie festgenagelt; der Elo-Tracker
schreibt ihn ab jetzt je Zeile mit. A3/A4 laufen in `cargo test` (321 gruen).

**#82 GPU-Batcher GESCHLOSSEN 2026-08-10** (Regel 1): erreichbare Batches 11/22/44
liefern 2.581/6.197/14.060 Evals/s, alle unter der unteren CPU-Schranke 17.600;
Break-even erst bei ~64-128. Die GPU ist nicht langsam, sondern ausgehungert --
lohnt nur mit blatt-paralleler Auswertung. **Folge**: das Kostentor des
Bootstrap-Horizonts bekommt keine Entlastung, +25 % gelten unveraendert.

**RUNDE 5 IST JETZT EXPECTIMINIMAX** (scharf seit 2026-08-10): Zufallsknoten an den
Aufdeck-Stellen der verdeckten Chip-Zuordnung. Versatz null ist GEMESSEN
(-0,47 Pkt, SE 0,66, t=-0,71 ueber 43 Abweichungen aus 1371 Entscheidungen), nicht
per Anker-Kante behauptet -- eine Arena mit +-4,4pp Auflösung kann 0,02 Pkt/Partie
nicht entscheiden. `MOSAIC_R5_CHANCE_NODES=0` stellt das Altverhalten her.

**Task D (Gewichts-Sweep) ABGESCHLOSSEN 2026-08-10: alle drei Arme H0.**
`vw04` 208:192 (52,0%), `vw08` 92:108 (46,0%), `pw025` 68:82 (45,3%,
SPRT-H0 nach 75 Paaren). Damit greift **Regel 5** der Vorregistrierung:
`VALUE_WEIGHT = 0,2` und der Punkte-Default bleiben, der Punkt gilt fuer
die WDL-/2D-Aera als geschlossen. Bild monoton und konsistent -- 0,4 nicht
besser, 0,8 schlechter. Champion bleibt `v21_2d_brierbest`.

**ISMCTS-k ABGESCHLOSSEN 2026-08-10**: k=1/2/4 rechenneutral 81,75% /
77,00% / 73,00%; k=4 in BEIDEN Pflichtinstrumenten signifikant negativ
(Block-t -3,73, exakter McNemar p=0,0026, Bonferroni inklusive). Der
Nutzer-Einwand gegen k=2 ist damit beantwortet, ohne dass die Schliessung
auf dem schwachen Arm ruht.

**WHEEL: gebaut+getestet, NICHT installiert.** Alle Engine-Aenderungen vom
2026-08-10 sind mit ausgeschalteten Knoepfen verhaltensneutral, 327 Tests
gruen -- aber die Python-Seite laeuft noch auf der Engine vom 2026-08-09.
Beide Bahnen und der Server sind frei, die Bedingung ist also erfuellt:
1. `python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl`
2. Paritaets-Probe MUSS `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` liefern.
3. Danach Golden-Waechter A2-A4 (bereits im Code, `DESIGN_konventionen_als_pruefungen.md`).

**NEU OFFEN aus dem 2026-08-10-Block (`PREREG_zufallsknoten.md`):**

| Punkt | Stand |
|---|---|
| R5-Zufallsknoten (Weg A) | **gebaut**, `MOSAIC_R5_CHANCE_NODES` Default AUS. Scharfschalten braucht eine Anker-KANTE als Aequivalenzpruefung -- Nutzer-Entscheid offen, da das Leck nachweislich keine Zugwahl aendert (0/247) |
| Teil E, Rest | "weicht ab" in "kostet Punkte" umrechnen; das Orakel teilt die Bewertungsfunktion des Loesers, 81,4 % gegen 51,7 % ist deshalb kein neutraler Vergleich |
| Zufallsknoten INNERHALB der Runde | der eigentliche Architektur-Punkt: Kuppelstapel als aufgezaehlter Knoten am Aufdecken, Kostentor in Runde 1, Teil A1 fällt mit ab. Danach kann der Shuffle raus (Determinismus-Gewinn) |
| Stapelzug fuers NETZ | braucht Self-Play mit `MOSAIC_STACK_DRAW_RESEARCH=1`, dann Training, dann Gating -- eine ganze Generierung, laut Nutzer-Entscheid hinter der v21-Queue |

**Instrument-Schulden**: Paritaets-Probe liegt noch im Scratchpad einer
alten Sitzung statt in `tools/`; `elo_history.csv` fehlen CI-Spalten und
`contract`; `UEBERGABE_v21_spirale.md` ist vom 2026-08-08; v20 fehlt die
Elo-Kante zu `v19_best` (Champion-2 seiner Generation).

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
  PREREG_v21_fenster.md, dort korrigiert).
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
  Nachtrag-Schuld: v20 fehlt die Kante zu `v19_best` (Champion-2 seiner
  Generation) -- billig nachholbar, Nutzer-Entscheid.
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
  (PREREG_aggression_stilmessung/PREREG_denial_tiebreak).
- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).
- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).
- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).
- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blindfleck.md`, Tasks E/F/G dazu
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
  `round_number>=5 && phase==Drafting` mit exaktem Alpha-Beta
  (`NODE_BUDGET=200`), Blattwert = exakter Endscore inkl. Wertungsplatten.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):
- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`
  (inert, Gewicht 0), seit Task #28 zusaetzlich `opp_points` (nur in
  Modellen, die damit trainiert wurden -- Engine erkennt ihn per
  Output-NAME und faellt sonst auf Bestandsverhalten zurueck).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `VALUE_OPP_EPSILON = 0,1`, `TD_LAMBDA = 0,5`.
- **Value-ZIEL (#34-Verdikt, Schema 17)**: `values_wdl` = TD-Blend aus
  Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang; Alt-Datei-
  Bootstraps werden beim Cache-Bau Platt-entstaucht (A=0,0051/B=1,9269),
  `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben roh. Training:
  `--value-head wdl --select-by-brier` (KEIN destretch-Flag mehr noetig).
  Policy-Traeger-Manifest `data/policy_carrier_manifest_v20.json`
  maskiert Alt-Dateien ausser 135 v18 + 45 v17 (im Cache-Key).
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> `v19_2d_best`.

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
