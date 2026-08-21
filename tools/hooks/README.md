# Git-Hooks (`tools/hooks/`)

**Warum hier und nicht in `.git/hooks/`**: `.git/hooks/` ist nicht
versioniert. Diese Skripte liegen deshalb in `tools/hooks/` (reviewbar wie
normaler Code) und werden per `core.hooksPath` aktiviert.

Herleitung und Zeitbudgets: `evaluations/DESIGN_conventions_as_checks.md`,
Abschnitt "Entscheid: LOKALER GIT-HOOK".

Die Golden-Waechter A1-A4 aus dem Design-Dokument sind **gebaut** (Stand
2026-08-21 geprueft) und laufen als Teil von `cargo test --release`, also im
`pre-push`-Haken:

| | Waechter | Fundstelle |
|---|---|---|
| A1 | Testbestand als Regressionsnetz | `cargo test --release` (483 Tests) |
| A2 | Laufzeit-Vertragsstempel | `engine/src/lib.rs:583`, exponiert in `engine_config_json()` |
| A3 | Feature-Golden-Hash | `engine/src/features.rs:1375` (`feature_golden_hash_matches_fixture`) |
| A4 | Heuristik-Anker-Verhaltenstest | `engine/src/mcts.rs:1271` ff., 200 Simulationen gegen Fixture |

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

1. Datei-Groessen-Ratsche (`tools/size_baseline.json`, Schwelle 40 KB)
2. Doku-Sprachkonvention (README.md englisch, STATUS.md/history.md deutsch)
3. Keine neuen `#NN`-Task-Nummern (gegen `evaluations/TASK_NUMBER_REGISTRY.md`)
4. Prereg-Index-Konsistenz (`evaluations/PREREG_*.md` <-> `PREREG_INDEX.md`)
5. Stille Test-Skips (`warn_silent_test_skips`) -- **nur Warnung, kein
   Commit-Blocker.** Sucht fruehe `return` direkt hinter einer
   Voraussetzungs-Pruefung: ein stiller Skip besteht leer-gruen und prueft
   nichts. Die Heuristik ist grob, Nicht-Test-Treffer sind zu ignorieren.

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

**Budget: < 90 s**, aber nur wenn `engine/src/` betroffen ist -- sonst < 1 s.

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
