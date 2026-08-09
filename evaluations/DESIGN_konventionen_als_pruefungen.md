# Konventionen in Pruefungen ueberfuehren (CI + Golden-Waechter)

**Angelegt 2026-08-09.** Nutzer-Auftrag: *"Konventionen in Prüfungen
überführen — CI plus die Golden-Wächter aus dem Plan"*, nach dem
Agenten-Review zum Champion-Staerkevertrag.

Kein Experiment, daher keine Vorregistrierung -- aber die Regeln, die
hier erzwingbar werden, sind Entscheidungsregeln, deshalb dieses
Design-Dokument als einzige Quelle fuer die Umsetzung.

## Verifizierter Ausgangsstand (nicht aus dem Review uebernommen)

| Behauptung | Befund |
|---|---|
| `train.py` 133 KB, `server.py` 74, `self_play.py` 41 | bestaetigt (132/74/41) |
| Python-Seite verletzt die Modularitaetsregel | bestaetigt, **schlimmer als behauptet**: groesste Datei ist `engine/py/neural_net.py` mit **152 KB**, im Review nicht erwaehnt |
| Elo "1358 [1292,1434]" praeziser zitiert als belegt | bestaetigt: `evaluations/elo_history.csv` hat die Spalten `date,player_a,sims_a,player_b,sims_b,wins_a,wins_b,n,comment` -- **kein CI, keine Kontrakt-Spalte**. Das Intervall entsteht erst beim Berichten und faellt beim Zitieren weg |
| CI vorhanden | **nein**, aber Remote `artfox1985/mosaic-AI` existiert ⇒ Actions moeglich |
| `version()` / `engine_config_json()` als Vertragsstempel | **untauglich**: `version()` liefert statisch `0.1.0` (nie erhoeht), `engine_config_json()` hat 20 Schluessel, aber weder `input_size` noch `num_planes_channels` noch eine Vertragsversion |

## Entscheid: LOKALER GIT-HOOK statt GitHub Actions (Nutzer 2026-08-09)

*"lokaler githook würde schon reichen denk ich"* -- richtig fuer dieses
Repo, und in einem Punkt sogar BESSER: ein lokaler Hook sieht `models/`
und `data/` (beide gitignored), Actions koennte das nie. Die im ersten
Entwurf noetige Trennung "CI kann nur textnahe Regeln" entfaellt damit.

**Die neue harte Grenze ist LAUFZEIT.** Ein Hook, der bei jedem Commit
eine halbe Minute kostet, wird mit `--no-verify` umgangen -- dasselbe
Versagensmuster wie ein Waechter, der ohne Grund bellt. Daher ein
Zeitbudget als Entwurfsvorgabe:

| Haken | Budget | Inhalt |
|---|---|---|
| `pre-commit` | **< 3 s** | nur textnahe Pruefungen (A5). Keine Compilierung, kein Netz, keine Daten |
| `pre-push` | < 90 s | `cargo test --release` inkl. der Golden-Waechter (A1-A4), und NUR wenn `engine/src` im Push geaendert wurde |
| manuell | beliebig | Paritaets-Probe vor jeder Wheel-Installation (B1). Bleibt bewusst manuell: sie braucht `models/` UND das INSTALLIERTE Wheel, gehoert also an den Installationsschritt, nicht an einen Commit |

**Versionierung der Hooks**: `.git/hooks/` ist nicht versioniert. Die
Skripte liegen daher in `tools/hooks/` und werden per
`git config core.hooksPath tools/hooks` aktiviert -- ein Befehl, keine
Kopiererei, und der Hook-Inhalt ist reviewbar wie normaler Code. Der
Installationsbefehl gehoert in README und Uebergabe.

**Was ein Hook NICHT leisten kann und was daraus folgt**: er laeuft nur
auf diesem Rechner und ist mit `--no-verify` abschaltbar. Er ist damit
ein Werkzeug gegen VERSEHEN, nicht gegen Absicht -- das genuegt hier,
weil genau die heutigen Vorfaelle Versehen waren (vergessene
Umgebungsvariable, veraltetes Wheel, Regler im toten Zweig).

## Stufe A -- Golden-Waechter (im `pre-push`-Haken, s.o.)

**A1 `cargo test --release`** -- Bestand (311 Tests) als Regressionsnetz.

**A2 Laufzeit-Vertragsstempel** (meine Ergaenzung zum Review-Plan, weil
der die heute zweimal eingetretene Fehlerklasse nicht abdeckt): ein
Hash ueber die Vertragskonstanten (`INPUT_SIZE`, `NUM_PLANES_CHANNELS`,
`NUM_ACTIONS`, Kopf-Reihenfolge) wird beim Bauen eingebacken und ueber
`engine_config_json()` **exponiert**. Jedes Werkzeug kann dann das
INSTALLIERTE Binary fragen, welchen Vertrag es implementiert.
Begruendung aus dem Ist-Betrieb: heute war das installierte Wheel
(2026-08-07) aelter als `net_mcts.rs` (2026-08-08), die E3b-Regler
fehlten im Modul -- und ein `grep` auf die Quelle sah gesund aus.
Zweiter Fall: `POLICY_MASS_CUTOFF` existiert, ist im genommenen Zweig
aber unerreichbar. Ein Golden-Hash, der gegen den AKTUELLEN Build
laeuft, sieht keinen von beiden.

**A3 Feature-Golden-Hash** (Review-Plan Stufe 0, mit einer Aenderung):
**quantisiert statt bitgenau.** Bitgenaue f32-Hashes koennen bei einem
rustc-/LLVM-Wechsel oder anderem `target-cpu` kippen, ohne dass sich
die Semantik aendert -- dann bellt der Waechter ohne Grund und wird
ignoriert. Genau das ist heute unserer Paritaets-Probe passiert (sie
hasht die volle JSON-Antwort und brach an drei rein additiven Feldern).
Also: auf ~1e-6 runden, Toolchain-Version im Fixture-Kopf vermerken,
Toolchain-Wechsel als legitimes Neu-Basislegen behandeln.
**Pflicht-Gegenprobe**: eine Feature-Zeile testweise aendern muss den
Test rot machen -- ein Waechter, von dem niemand gesehen hat, dass er
fehlschlagen kann, ist wertlos.

**A4 Heuristik-Anker-Verhaltenstest** (Review-Plan Stufe 3). Der
wichtigste Gewinn dieser Stufe: **die Heuristik ist netzfrei**, ihr
Golden-Test laeuft also vollstaendig in CI. Feste Seeds, feste
Zustaende, die GEWAEHLTEN Zuege als Fixture. Damit wird
"Heuristik-Anker-Parameterpaket: NICHT ANFASSEN" von einer STATUS-Zeile
zu einer Pruefung -- und deckt `mcts.rs`, `scoring.rs::wertung_progress`
und `tiling_solver.rs` gemeinsam ab, was ein Konstanten-Hash nicht
koennte.
**Ausdruecklich Einfrieren, nicht Reparieren**: der grobe
Kriterium-6-Term (`scoring.rs:178`) bleibt im Anker stehen. Ein Massstab
wird nicht verbessert, sonst entwertet er die Leiter. Die
Plattenschwaeche gehoert auf die Netzseite (`PREREG_plattenkopf.md`).

**A5 Konventions-Linter** (`tools/check_conventions.py`, laeuft im
`pre-commit`-Haken, Budget < 3 s), je Regel eine eigene Pruefung mit
sprechender Fehlermeldung:
- **Datei-Groessen-RATSCHE**, nicht Obergrenze. Aktuelle Groessen als
  Basislinie einchecken; rot wird nur das WACHSTUM einer bereits zu
  grossen Datei. Begruendung: eine harte Grenze waere am ersten Tag auf
  vier Dateien rot und wuerde abgeschaltet -- die Ratsche stoppt die
  Blutung, ohne ein Refactoring zu erzwingen, das niemand beauftragt
  hat.
- **Doku-Sprachkonvention**: README.md englisch, STATUS.md/history.md
  deutsch (Heuristik ueber Stopwort-Anteil, Schwelle grosszuegig).
- **Keine neuen `#NN`**: jede `#NN` in geaendertem Code/Doku muss in
  `evaluations/TASK_NUMMERN_REGISTRATUR.md` stehen.
- **Prereg-Index-Konsistenz**: jede `PREREG_*.md` steht im
  `PREREG_INDEX.md` und umgekehrt; Zaehler in den Abschnitts-
  Ueberschriften stimmen mit der Zeilenzahl.

## Stufe B -- manuelle Gatter (an den Installationsschritt gebunden)

**B1 Paritaets-Probe ins Repo holen und reparieren.** Sie liegt heute in
`C:\...\Temp\claude\...\c9453d70-...\scratchpad\paritaet_probe.py`, also
im Temp-Verzeichnis einer Sitzung vom 2. August -- obwohl STATUS und
Uebergabe sie als Freigabe-Kriterium jeder Wheel-Installation fuehren.
Wird das Verzeichnis aufgeraeumt, ist das Instrument weg. Nach
`tools/paritaet_probe.py`, und die Kennzahl wird eine
**entscheidungsrelevante Projektion** (`ai_action` + Besuchszahlen je
Zug) statt des Rohstrings, damit additive Felder keinen Fehlalarm mehr
ausloesen. Beide Hashes werden berichtet (Projektion = Gatter, Rohstring
= Zusatzinfo).

**B2 Elo-Buchfuehrung ehrlich machen.** `elo_history.csv` bekommt die
Spalten `elo_a_ci_low`, `elo_a_ci_high`, `contract`. Bestandszeilen
bekommen leere CI-Felder und `contract=pre1` -- **kein Backfill**,
dieselbe Ehrlichkeit wie beim bewusst unterlassenen Rueckfuellen der
Heuristik-Matches (`tools/elo_tracker.py` Z. 30-38). `elo_tracker`
warnt, wenn ein Fit Kanten verschiedener Kontrakte mischt.
Zusatzregel fuer STATUS: **eine Elo-Zahl wird nie ohne ihr CI
zitiert.** Anlass ist der Ist-Fall: 1358 klingt praezise, das CI
[1292, 1434] ist 142 Punkte breit.

## Was NICHT Teil davon ist

- Kein Refactoring der grossen Python-Dateien. Die Ratsche stoppt das
  Wachstum; ein Zerschneiden von `neural_net.py` (152 KB) waere ein
  eigenes Vorhaben mit eigenem Risiko und ist nicht beauftragt.
- Keine Aenderung an Suchverhalten oder Feature-Werten. Stufe A und B
  sind verhaltensneutral -- Bedingung dafuer, dass die Elo-Leiter den
  Umbau uebersteht.
- Keine Crate/Wheel je Aera (Review-Begruendung uebernommen: die
  gepaarte Arena braucht beide Netze im selben Prozess).
- Keine `FeatureVersion`-Enum-Vorratsarbeit (Review-Stufe 2) -- erst
  beim ersten realen Bruch, sonst ein Enum mit einer Variante.

## Reihenfolge

**A5 + Haken-Gerüst zuerst** -- der Konventions-Linter ist reiner Text,
braucht keinen Wheel-Neubau und ist damit sofort und ohne freies
Maschinen-Fenster lieferbar; er deckt zugleich die meisten heute nur
appellativen Regeln ab. Danach A2 (Vertragsstempel, billigster Schritt
gegen die real eingetretene Fehlerklasse), dann A3/A4 (Golden-Waechter,
brauchen einen Wheel-Neubau und damit ein freies Fenster), dann B1, dann
B2. A5/B2 beruehren nur `tools/` + `evaluations/`, A2-A4 nur
`engine/src` -- die beiden Straenge koennen parallel laufen.
