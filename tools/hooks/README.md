# Git-Hooks (`tools/hooks/`)

**Warum hier und nicht in `.git/hooks/`**: `.git/hooks/` ist nicht
versioniert. Diese Skripte liegen deshalb in `tools/hooks/` (reviewbar wie
normaler Code) und werden per `core.hooksPath` aktiviert.

Herleitung, Zeitbudgets und die Abgrenzung zu den (noch nicht gebauten)
Golden-Waechtern A1-A4: `evaluations/DESIGN_conventions_as_checks.md`,
Abschnitt "Entscheid: LOKALER GIT-HOOK".

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

**Budget: < 3 s.** Keine Compilierung, kein Netz, keine Korpus-/Modelldateien.

## `pre-push` -- Golden-Waechter, bedingt

Prueft, ob im zu pushenden Bereich `engine/src/` geaendert wurde. Wenn nein:
sofortiger Durchlass. Wenn ja: `cargo test --release` in `engine/`.

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
