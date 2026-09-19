# Git-Hooks (`tools/hooks/`)

**Warum hier und nicht in `.git/hooks/`**: `.git/hooks/` ist nicht
versioniert. Diese Skripte liegen deshalb in `tools/hooks/` (reviewbar wie
normaler Code) und werden per `core.hooksPath` aktiviert.

Herleitung und Zeitbudgets: `docs/DESIGN_conventions_as_checks.md`,
Abschnitt "Entscheid: LOKALER GIT-HOOK".

Die Golden-Waechter A1-A4 aus dem Design-Dokument sind **gebaut** (Stand
2026-08-26 geprueft, Fundstellen und Zahlen an diesem Tag nachgezogen) und
laufen als Teil von `cargo test --release`, also im `pre-push`-Haken:

| | Waechter | Fundstelle |
|---|---|---|
| A1 | Testbestand als Regressionsnetz | `cargo test --release` (Zaehlung: der Lauf selbst; Attribut-Zaehlung Stand 2026-09-06: 548 `#[test]` / 23 `#[ignore]` in `engine/src`, davon 2 mit Begruendungstext am Attribut) |
| A2 | Laufzeit-Vertragsstempel | `engine/src/lib.rs:639` (`contract_canonical_string`, Doku ab `lib.rs:618`), Hash in `contract_hash()` (`lib.rs:681`), exponiert in `engine_config_json()` (`lib.rs:715`) |
| A3 | Feature-Golden-Hash | `engine/src/features.rs:2021` (`feature_golden_hash_matches_fixture`) |
| A4 | Heuristik-Anker-Verhaltenstest | `engine/src/mcts.rs:1392` (`heuristic_anchor_choices_match_fixture`), plus `mcts.rs:1484` (`heuristic_anchor_r5_choice_matches_fixture_v2`) fuer die R5/v2-Variante |

Die Fundstellen sind `datei:zeile` und driften mit jedem Refactoring -- der
stabile Teil ist der Testname bzw. der Dateiname. Zwischen 2026-08-21 und
2026-08-26 sind alle vier verrutscht (A3 um 98 Zeilen, A4 um 250), ohne dass
etwas kaputt war.

Am 2026-09-06 waren alle vier erneut verrutscht (A3 um 548 Zeilen, A4 um 129),
und A2 zeigte zusaetzlich auf einen Namen, den es nicht mehr gibt
(`contract_stamp_input` -> `contract_canonical_string`). Die Zeilen oben sind an
diesem Tag nachgezogen.

## Aktivierung

```sh
git config core.hooksPath tools/hooks
```

Einmalig, lokal pro Repo-Kopie (nicht global, nicht automatisch durch Git
selbst gesetzt). Ohne diesen Befehl tut keiner der beiden Haken etwas.

Deaktivieren: `git config --unset core.hooksPath`.

## `pre-commit` -- Konventions-Linter (Baustein A5)

Ruft `python tools/check_conventions.py --staged` auf und bricht den Commit
bei Exit != 0 ab. Prueft nur die gestagten Dateien:

Die Nummern sind die des Linters (`REGEL n` in seinen Meldungen), nicht die
Reihenfolge des Laufs:

1. Datei-Groessen-Ratsche (`tools/size_baseline.json`, Schwelle 40 KB) --
   **seit 2026-08-27 nur noch WARNUNG, kein Commit-Blocker** (Nutzer-Entscheid).
   Sie war zehn Auslesungen lang rot und hat null Zerlegungen bewirkt: wer sie
   traf, legte die Basislinie neu, weil das zehn Sekunden kostet und eine
   Zerlegung eine Architekturentscheidung ist, die niemand beauftragt hatte.
   Ein Tor, das man routinemaessig umgeht, bringt das Umgehen bei. Die Zahl
   bleibt sichtbar, der Zwang faellt. ROT bleibt nur der kaputte Fall:
   `tools/size_baseline.json` fehlt ganz.
2. Doku-Sprachkonvention (README.md englisch, STATUS.md/history.md deutsch) --
   blockt.
3. Keine neuen `#NN`-Task-Nummern (gegen `evaluations/TASK_NUMBER_REGISTRY.md`)
   -- blockt.
4. Prereg-Index-Konsistenz (`evaluations/PREREG_*.md` <-> `PREREG_INDEX.md`) --
   blockt.
5. Stille Test-Skips (`warn_silent_test_skips`) -- **nur Warnung, kein
   Commit-Blocker.** Sucht fruehe `return` direkt hinter einer
   Voraussetzungs-Pruefung: ein stiller Skip besteht leer-gruen und prueft
   nichts. Die Heuristik ist grob, Nicht-Test-Treffer sind zu ignorieren.
   Laeuft als letzte Pruefung, traegt aber die Nummer 5.
6. Knopf-Doku aktuell (`docs/knobs.md` <-> `engine/src/knob_registry.rs`) --
   blockt. Die Tabelle ist GENERIERT; wer die Registratur aendert, laesst
   `python tools/generate_knob_docs.py` laufen und committet die Doku mit.
   Greift nur, wenn eine der beiden Dateien gestagt ist (gemessen 4 ms).
   Ergaenzt 2026-08-26: der Rust-Waechter erzwingt, dass jeder Knopf im Code
   REGISTRIERT ist, aber nichts erzwang, dass die abgeleitete Tabelle
   mitwaechst.
7. Bezeichner ENGLISCH (CLAUDE.md 2026-08-24) -- **blockt.** Geprueft werden
   NUR HINZUGEFUEGTE Definitionszeilen (gleicher Zuschnitt wie Regel 1): der
   deutsche Altbestand blockt nichts, ein neuer deutscher Name schon. Python
   ueber `ast` (sieht Strings und Kommentare gar nicht), Rust ueber Muster.
   Ausweg je Zeile: `konvention-ok: <Grund>` ans Zeilenende.
   Regel 5 kennt diesen Ausweg NICHT -- dort sind die Auswege `panic!`
   oder `#[ignore = "Grund"]`.
8. Spec-Pflichtfelder (`models/*.spec.json` <-> `KNOWN_FIELDS` in
   `engine/src/net_mcts.rs`, `SearchConfig::from_spec_file`) -- **nur Warnung,
   kein Commit-Blocker.** Geprueft wird in BEIDE Richtungen: ein fehlendes
   Pflichtfeld und ein unbekanntes Feld weist das Wheel gleich hart ab, und
   zwar erst beim naechsten Partie-Start -- der Lauf stirbt also spaeter und
   woanders als der Commit. Kein Blocker, weil das Nachziehen an ein
   ZEITFENSTER gebunden ist (Docstring `tools/spec_add_field.py`: erst wenn
   kein Lauf mehr auf dem alten Wheel darauf zugreift, aber vor der
   Installation des neuen) -- ein Blocker verhinderte genau den Commit, der
   das Feld einfuehrt. Eingefrorene Artefakte (`models/frozen_*/**`) sind
   ausgenommen. **Gemessen 2026-09-06: 3,5 ms** bei 8 lebenden Specs.
   Handgriff: `python tools/spec_add_field.py <feld> <wert> [--check]`.

**Zur Nummerierung:** die **6 ist doppelt vergeben** (Knopf-Doku und
Skill-Verweis, `check_claude_md_skill_refs`). Historisch gewachsen, bewusst
nicht umnummeriert -- die Nummern werden in Meldungen, `docs/` und
Commit-Nachrichten zitiert.

**Budget: < 3 s.** Keine Compilierung, kein Netz, keine Korpus-/Modelldateien.
**Gemessen 2026-09-06** (voller Repo-Lauf ohne `--staged`, also die teuerste
Form): 3,6 s. Der Hook-Modus prueft weniger.

## Was `pre-push` NICHT sehen kann (Vorfall 2026-09-07)

**`cargo` prueft den ARBEITSBAUM, nicht die gepushten Commits.** Ist der Arbeitsbaum
schmutzig, kann ein kaputter Push gruen aussehen. Genau das ist passiert:
`engine/src/net_mcts.rs` war beim Commit durchgerutscht (Dateien einzeln aufgezaehlt statt
`git add -A`), der gepushte Stand rief `action_temp_mode` auf, ohne es zu definieren -- und
`cargo test --release` lief mit 549 gruenen Tests durch, weil der Arbeitsbaum die Datei
trug. Auf origin lag rund eine Viertelstunde ein Stand, der nicht kompiliert.

Der Haken warnt seitdem, wenn `engine/src/` oder `self_play.py` schmutzig sind. **Es ist
bewusst nur eine Warnung**: ein schmutziger Arbeitsbaum beim Pushen ist normal und meistens
harmlos, und ein Blocker wuerde zum `--no-verify` erziehen
([[feedback_gate_that_is_bypassed_teaches_bypassing]]). Wer die Warnung sieht, hat zwei
Sekunden Zeit zu pruefen, ob die schmutzige Datei zum Push gehoert haette.

**Die vollstaendige Pruefung waere, den gepushten Commit in einen temporaeren Baum
auszuchecken und DORT zu bauen.** Nicht gebaut: das kostet einen zweiten
Kompilierdurchgang je Push, und die Warnung faengt den realen Fall (vergessene Datei)
zuverlaessig genug.

## `pre-push` -- zwei Pruefungen

### 1. Rechnerstruktur-Waechter (laeuft IMMER)

Das Repo ist oeffentlich; CLAUDE.md (Nutzer-Entscheid 2026-08-17) verbietet
absolute Pfade und den Nutzernamen in neuen Dateien. Bisher stand dort nur ein
Pruefbefehl zum Selbstausfuehren -- ein Handgriff, den man vergisst. Jetzt
bricht der Haken den Push ab, wenn im **gepushten Stand** (nicht im Working
Tree) eine hinzugefuegte oder geaenderte Datei ein Nutzerpfad-Muster enthaelt:
ein absoluter Pfad in ein Nutzerverzeichnis (Windows- wie Git-Bash-
Schreibweise), ein OneDrive-Pfad in den Dokumente- oder Backups-Ordner, sowie
der Nutzername aus der Umgebung (`$USERNAME`/`$USER`, deshalb steht kein
konkreter Name im Skript).

**Das Muster selbst steht nur an einer Stelle: `PRIVACY_PAT` in `pre-push`.**
Dort ist es ein Regex mit Zeichenklassen und trifft sich deshalb nicht selbst.
Wer es in eine Doku WOERTLICH ausschreibt, macht genau diese Datei zum
Dauerblocker -- beim Bau ist das zweimal passiert (in einem Kommentar in
`pre-push` und in `evaluations/STATUS.md`). Gegenprobe fuer neue Doku:

```sh
PAT="$(sed -n "s/^PRIVACY_PAT='\(.*\)'\$/\1/p" tools/hooks/pre-push)"
git grep -I -l -E -e "$PAT" HEAD -- .
```

Nur `A/C/M/R`-Dateien des Push-Bereichs -- die Historie wird laut CLAUDE.md
NICHT umgeschrieben, Alt-Treffer duerfen also nicht blockieren. `CLAUDE.md`
selbst ist ausgenommen, dort steht der Pruefbefehl im Text.

**Budget: < 1 s** (gemessen 0,44 s ueber 10 Commits).

### 2. Golden-Waechter, bedingt

Prueft, ob im zu pushenden Bereich `engine/src/` geaendert wurde. Wenn nein:
sofortiger Durchlass. Wenn ja: `cargo test --release` in `engine/` (A1-A4,
siehe Tabelle oben).

**Budget: < 90 s** laut Design-Dok, aber nur wenn `engine/src/` betroffen ist
-- sonst < 1 s. **Gemessen 2026-08-26 (exklusiver Lauf): 97 s reine
Testlaufzeit**, dazu die Kompilierung bei kaltem `target/`. Das Budget ist
damit knapp gerissen; kein Handlungsbedarf, aber die Zahl steht hier, statt
geschaetzt zu werden (CLAUDE.md "Laufzeiten messen, nicht schaetzen").

## `python_dll_path.sh` ENTFALLEN (2026-09-20)

Die Sammelstelle fuer die Python-DLL-Herleitung ist geloescht: sie hatte zuletzt
NULL Aufrufer. Die vier Skripte, fuer die sie am 2026-09-06 extrahiert wurde,
sind mit den Generationswechseln weggefallen, und `pre-push` hat sie nie
gesourct -- er traegt die Herleitung inline (Z.150-174). Die Falle selbst
(`STATUS_DLL_NOT_FOUND`, 0xc0000135) bleibt damit bewacht; die Herleitung steht
zusaetzlich in CLAUDE.md. Befund und Beleg: `PREREG_code_cleanup_closeout.md`
par.8f/8g. Die Historie behaelt die Datei.

## Fehlalarm? `--no-verify`

Beide Haken laufen nur lokal und sind mit dem Standard-Git-Ausweg
abschaltbar:

```sh
git commit --no-verify
git push --no-verify
```

Das ist beabsichtigt (siehe Design-Dok): ein Haken, der bei jedem
Fehlalarm eine Debatte erzwingt, wird irgendwann pauschal umgangen. Diese
Haken sind ein Werkzeug gegen VERSEHEN, nicht gegen Absicht.

## Python-Tests im pre-commit (seit 2026-09-06)

Nach dem Konventions-Check faehrt `pre-commit` `python -m unittest discover -s
tools/tests -p "test_*.py"` (rund 0,3 s, rot blockiert). Dort liegen nur Tests
ohne Wheel, Korpus oder Netz: `test_train_manifest_flags.py` (jedes argparse-Flag
von train.py mit Verhaltenswirkung steht in `_cli_args`, Ausnahmen namentlich),
`test_tiling_geometry_probe.py` (Reihen-Alter-Sonde, reine Logik),
`test_spec_add_field.py`. Der Shell-Test `train_resume_pause_test.sh` (GPU,
Minuten, Handstart) ist am 2026-09-20 entfallen -- seine Fixtures waren tot
(`PREREG_code_cleanup_closeout.md` par.8f/8g).
