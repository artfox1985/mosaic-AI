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
| A1 | Testbestand als Regressionsnetz | `cargo test --release` (Zaehlung: der Lauf selbst; Attribut-Zaehlung Stand 2026-08-27: 518 `#[test]` / 23 `#[ignore` in `engine/src`) |
| A2 | Laufzeit-Vertragsstempel | `engine/src/lib.rs:647` (`contract_stamp_input`-Doku), Stempel exponiert in `engine_config_json()` (`lib.rs:741`) |
| A3 | Feature-Golden-Hash | `engine/src/features.rs:1473` (`feature_golden_hash_matches_fixture`) |
| A4 | Heuristik-Anker-Verhaltenstest | `engine/src/mcts.rs:1521` (`heuristic_anchor_choices_match_fixture`), plus `mcts.rs:1612` fuer die R5/v2-Variante |

Die Fundstellen sind `datei:zeile` und driften mit jedem Refactoring -- der
stabile Teil ist der Testname bzw. der Dateiname. Zwischen 2026-08-21 und
2026-08-26 sind alle vier verrutscht (A3 um 98 Zeilen, A4 um 250), ohne dass
etwas kaputt war.

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

**Budget: < 3 s.** Keine Compilierung, kein Netz, keine Korpus-/Modelldateien.

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
