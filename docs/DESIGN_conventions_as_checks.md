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
Plattenschwaeche gehoert auf die Netzseite (`PREREG_plate_head.md`).

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
  `evaluations/TASK_NUMBER_REGISTRY.md` stehen.
- **Prereg-Index-Konsistenz**: jede `PREREG_*.md` steht im
  `PREREG_INDEX.md` und umgekehrt; Zaehler in den Abschnitts-
  Ueberschriften stimmen mit der Zeilenzahl.

Diese vier Bullets sind der ENTWURFSSTAND. Spaeter dazugekommen (die
Liste im Modulkopf von `tools/check_conventions.py` ist die aktuelle):
eine Warn-Regel gegen stille Test-Skips (kein Commit-Blocker) und
2026-08-26 die Regel **Knopf-Doku aktuell** -- `docs/knobs.md` ist aus
`engine/src/knob_registry.rs` GENERIERT, und der Rust-Waechter erzwang
zwar die Registrierung jedes Knopfes, nicht aber das Mitwachsen der
abgeleiteten Tabelle.

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

## Nachtrag 2026-08-27: Regel 7, Bezeichner englisch

**Anlass, und er ist unangenehm konkret.** Eine Sitzung hat 14 Dateien mit
deutschen Funktions-, Parameter- und Variablennamen hinterlassen. Bei JEDEM
dieser Commits meldete dieser Linter "alle Regeln gruen". Die Regel steht seit
2026-08-24 in CLAUDE.md; geprueft hat sie nichts, gefunden hat sie der Nutzer.

Das ist genau die Lage, gegen die dieses Dokument gebaut wurde: eine Regel,
die nur gelesen wird, haelt nicht. Der Gegenbeweis steht daneben -- die
Gedankenstrich-Regel ist seit ihrer Aufnahme in den Haken nicht mehr gebrochen
worden.

### Zuschnitt: nur HINZUGEFUEGTE Definitionszeilen

Dieselbe Bauform wie die Groessen-Ratsche (Regel 1). Der deutsche Altbestand
ist gross (`plate_builder.rs`: 86 von 113 Funktionen); ein Waechter, der ihn
anmeckert, blockiert jeden Commit und wird nach dem zweiten Mal abgeschaltet.
Geprueft wird deshalb der Diff, nicht die Datei.

**Nur Definitionen, keine Verwendungen.** Neuer Code darf eine deutsch
benannte Bestandsfunktion aufrufen (`struktur_kennzahlen(...)`), ohne dass das
ein Verstoss ist -- sonst waere die Regel ein Umbenennungszwang fuer fremden
Bestand.

### Zwei Fehlalarm-Klassen, die beim Bau aufgefallen sind

1. **Prosa in Docstrings.** Ein Zeilen-Muster fuer Zuweisungen nimmt
   `Abweichung = Verweigerung.` aus einem Docstring fuer eine Zuweisung.
   Behoben, indem die Python-Haelfte ueber `ast` laeuft: der Parser sieht
   Zeichenketten und Kommentare gar nicht erst. Rust bleibt musterbasiert
   (kein Parser zur Hand), dort deckt das Streichen von `//` und `"..."` den
   Fall ab -- Gegenprobe: `referee.rs` und `mcts.rs` melden 0 Treffer.
2. **Teilzeichenketten.** `art` steckt in `start`, `zug` in `bezug`. Deshalb
   EXAKTER Vergleich der an `_` und CamelCase getrennten Wortteile -- mit
   einer kuratierten Ausnahmeliste langer, eindeutiger Staemme
   (`kennzahl`, `abweichung`, `aufloes`, ...), weil deutsche Komposita ohne
   Unterstrich (`quellzeilen`, `sammelaufloesend`) sonst durchrutschen.

### Ausweg

`konvention-ok: <Grund>` am Zeilenende, zeilengenau. Ein Waechter ohne Ausweg
wird beim ersten begruendeten Sonderfall im Ganzen abgeschaltet.

### Abnahme

Am historischen Fall geprueft, nicht nur synthetisch: die Fassung von
`tools/freeze_heuristic.py` aus dem Commit, der `_herkunft` und `ziel`
einfuehrte, erzeugt 6 Treffer. Der bereinigte Stand ist gruen. Und der
Waechter hat im selben Zug die deutschen Namen in seinem EIGENEN Neubau
gemeldet (`treffer`, `quellzeilen`) -- die sind daraufhin englisch geworden.

## Nachtrag 2026-08-27: Regel 1 wird WARNUNG (Nutzer-Entscheid)

Nachgezaehlt statt vermutet, auf Nutzer-Frage "was bringt mir eigentlich die
Ratsche":

| | |
| --- | --- |
| Basislinie neu gelegt | **10 x** |
| Dateien wegen der Ratsche zerlegt | **0** |

Die einzige Auslagerung im Baum (`train_manifest.py` aus `train.py`, `d8d34f5`)
nennt in ihrer Begruendung weder Groesse noch Wachstum -- sie kam aus zwei
Nutzer-Anstoessen.

**Warum das strukturell so kommt.** Wenn die Ratsche feuert, stehen zwei Wege
offen: zerlegen, oder `--update-size-baseline`. Der zweite kostet zehn
Sekunden, der erste eine Architekturentscheidung -- und die hat in diesem Repo
keinen Besitzer. Die Regel wusste das und sagte es in ihrer eigenen
Fehlermeldung: "ein Refactoring-Rueckstand, den niemand beauftragt hat".

**Der eigentliche Preis war nicht das ungebremste Wachstum.** Ein Tor, das man
regelmaessig umgeht, bringt das Umgehen bei. Zehn Basislinien-Resets sind zehn
Uebungen darin, einen roten Konventions-Check per Kommandozeile gruen zu
machen -- das faerbt auf die Tore ab, die wirklich tragen (REGEL 0,
Rechnerstruktur, Prereg-Koepfe).

**Und sie misst einen Stellvertreter fuer das Falsche.** Die Modularitaetsregel
in CLAUDE.md nennt ZUSTAENDIGKEITEN (Spiellogik / KI-Entscheidungen /
Spielzustand strikt getrennt), keine Dateigroessen. `neural_net.py` ist nicht
wegen 168 KB fragwuerdig, sondern hoechstens dann, wenn sie mehrere
Zuständigkeiten mischt. Bytes wurden gemessen, weil Bytes billig zu messen
sind.

Nach dem Massstab, den das Projekt selbst an Infrastruktur anlegt (CLAUDE.md,
"Infrastruktur bewerten": ein Vorschlag braucht einen BENANNTEN Nutzniesser),
faellt die Ratsche als Blocker durch.

**Was bleibt:** die Zahl wird weiter gemeldet, als Warnung auf stderr. Rot ist
nur noch der kaputte Fall -- `size_baseline.json` fehlt ganz, dann kann die
Warnung nicht einmal rechnen.
