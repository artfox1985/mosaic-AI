# Projekt-Richtlinien für Claude

## REGEL 0: Geprüft oder markiert. Kein Drittes. (Nutzer-Anweisung 2026-08-11)

Jede Sachaussage über Code, Regeln, Zahlen oder Messungen ist entweder

- **geprüft in dieser Sitzung**, mit genannter Prüfstelle (`datei:zeile`,
  Handbuch-Abschnitt, Log-Zeile), oder
- **ausdrücklich als ungeprüft / Annahme / Herleitung markiert.**

Eine unmarkierte Behauptung ist ein Regelbruch. Diese Regel entstand nach sieben
Flüchtigkeitsfehlern an einem Tag, die jeweils ein einziger Grep verhindert
hätte — einer davon hätte zu einer "Reparatur" am Elo-Anker geführt.

Die vier Auslöser, an denen es jedes Mal schiefging:

1. **Verhalten von Code**: erst lesen, dann sagen. Nicht aus dem Gedächtnis,
   nicht aus `STATUS.md`, nicht aus einer Vorregistrierung.
2. **Agenten-Befunde sind Behauptungen**, keine Fakten. Die tragende Zahl selbst
   nachprüfen, bevor sie weitergegeben oder verrechnet wird.
3. **Spielregeln**: in `docs/engine_manual.md` oder in den Code schauen, nie
   ableiten.
4. **Zahlen**: eine ungeprüfte Zahl geht in keine Rechnung. Eine Rechnung, die
   "ungefähr passt", ist kein Beleg, sondern ein Zufall.

Zusatz: **Plan und Zustand nie in derselben Zeitform** — "würde addieren" für
Geplantes, "addiert" nur für Gebautes-und-Aktives.

## Token-Optimierung & Kommunikations-Regeln

- **Kein Boilerplate** Wiederhole niemals den gesamten Dateikontent. Gib nur den geänderten Funktionsblock oder die spezifischen Zeilen aus.
- **Diff-Format** Verwende bei komplexeren Änderungen ein prägnantes Format (z.B. In Datei X, ändere Zeile Y zu Z).
- **Direktes Schreiben** Wenn du eine Datei bearbeitest, schreibe die Änderung direkt in die Datei. Verzichte auf die Anzeige des vollständigen Codes im Chat.
- **Kontext-Fokus** Antworte direkt auf die Aufgabe. Erkläre nur kurz die Logik, wenn es für das Verständnis der Änderung notwendig ist.

## Gedankenstrich-Regel (Nutzer-Anweisung 2026-08-21, gelockert am selben Tag)

- Der Geviertstrich (U+2014, "langer" Gedankenstrich) ist im CHAT
  weiterhin erlaubt, in DOKUMENTEN und Repo-Dateien (README, STATUS,
  Preregs, docs/, Kommentare) nicht mehr.
- Der Halbgeviertstrich (U+2013, "–") ist ueberall OK (Nutzer-Lockerung
  2026-08-21; so umgesetzt in docs/engine_manual.md).
- Ersatz fuer U+2014 je nach Kontext: Halbgeviertstrich, Komma,
  Doppelpunkt, Semikolon oder Klammern. Zahlenbereiche bekommen den
  einfachen Bindestrich (z.B. 10-273).
- Bestand wird bei Gelegenheit mit-migriert (README ist am 2026-08-21
  bereinigt), keine Grossaktion ueber alle Altdateien.

## Diagramm-Format: SVG (Nutzer-Anweisung 2026-08-21)

- Diagramme werden als **SVG** erstellt, nicht als PNG.
- PNG-Exporte stoesst der Nutzer bei Bedarf selbst an; nicht ungefragt
  mitgenerieren.

## Prereg-Statuskopf und Index (Nutzer-Anweisung 2026-08-23)

- Jede `evaluations/PREREG_*.md` traegt in Zeile 1 den parsebaren
  Status-Kopf (`<!-- STATUS: ... -->`); `evaluations/PREREG_INDEX.md`
  wird daraus GENERIERT (tools/generate_prereg_index.py). Der
  Tabellenteil des Index wird NIE von Hand editiert.
- **Wer ein Ergebnis oder Verdikt in einer Prereg registriert, zieht
  IM SELBEN ZUG den Zeile-1-Kopf nach** (gleiche Pflegeregel wie bei
  STATUS.md). Diese Regel entstand, nachdem ein Audit am 2026-08-23
  vier Preregs fand, deren Koepfe noch "OFFEN / nichts gebaut" sagten,
  waehrend der Dateikoerper laengst das registrierte Ergebnis trug.
- **Der Kopf ist ein STATUS, keine Chronik.** `HEADER_SEARCH_LIMIT = 4096`
  (tools/generate_prereg_index.py): waechst Zeile 1 darueber hinaus, faellt
  die Datei STILL aus dem Index -- der Generator meldet nur "ohne parsebaren
  Status-Kopf". Am 2026-08-25 ist das passiert, nach einer Nacht, in der bei
  jedem neuen Ergebnis hinten angehaengt wurde (4229 Zeichen). Wer ein
  Ergebnis nachtraegt, ERSETZT den ueberholten Teil, statt ihn zu ergaenzen;
  die Herleitung steht ohnehin im Dateikoerper.
- **Sobald sich ein Prereg-Kopf aendert: sofort
  `python tools/generate_prereg_index.py` laufen lassen** – nicht erst
  auf den pre-commit-Hook warten (der prueft nur, blockt aber erst
  beim Commit). Gilt auch fuer Agenten-Auftraege: die Regel gehoert in
  jeden Prompt, der Prereg-Registrierungen schreibt.

## Standard-Kennzahlen jedes Messberichts (Nutzer-Anweisung 2026-08-23)

**Zusaetzlich** zu dem, was die jeweilige Prereg verlangt, will der Nutzer in
JEDEM Messbericht (Arena, Sonde, Gating, Self-Play-Abnahme) diese sechs
Kennzahlen sehen – je Seite und, wo sinnvoll, als Differenz zwischen den Armen:

1. **Reihenauslastung** – wie weit die Musterreihen/Brett-Zeilen gefuellt
   werden (Verteilung der Zugziele und Fuellstaende, nicht nur Vollendungen).
2. **Spaltenauslastung** – volle Spalten, maximale Spaltenhoehe, Teilspalten
   (>= 3 / >= 4) je Partie.
3. **Strafleistenauslastung** – wie oft und wie stark die Strafleiste bedient
   wird (Ueberlaeufe, Strafpunkte).
4. **Erreichte Punkte je Wertungsplatte** – aufgeschluesselt je aktivem
   Kriterium, nicht nur k1.
5. **Eigene Punkte** – absolutes Score-Niveau (Task-#18-Lehre: die Siegquote
   allein verdeckt Niveau-Verschiebungen).
6. **Margin zum Gegner** – Punktedifferenz, nicht nur Sieg/Niederlage.

Warum: die Kampagne hat mehrfach Effekte erst ueber diese Randgroessen
verstanden (Gegner-Spezifitaet des Minimax-Knopfs, der Vollendungs-Engpass,
die Reihen-Praeferenz). Sie kosten nichts extra, wenn die Partien ohnehin mit
`--log-games` laufen.

**Vorhandene Quellen (erst pruefen, dann bauen):** `tools/analyze_game_log.py`
(Regexe fuer Reihe/Strafleiste-Ziele, Ueberlauf, Endwertung),
`tools/plate_points_from_arena.py` (Punkte je Kriterium),
`tools/probes/column_build_structural_probe.py` und
`column_completion_gap_probe.py` (Spaltenauslastung, Vollendungsluecken),
`tools/probes/row_preference_probe.py` (Reihenwahl); Punkte/Margin stehen in
den Arena-Artefakten (`scores`, plus `scores_unclamped` in Self-Play-Records).
Fehlt eine Groesse im konkreten Kontext, wird sie ergaenzt oder ihr Fehlen im
Bericht begruendet – stilles Weglassen ist ein Regelbruch.

## Bezeichner-Konvention: Code ist ENGLISCH (Nutzer-Anweisung 2026-08-24)

- **Alle Bezeichner im Code sind englisch**: Funktionen, Methoden, Typen,
  Structs, Enums und ihre Varianten, Konstanten, Felder, lokale Variablen,
  Testnamen. Gilt fuer Rust wie fuer Python.
- Das gilt auch fuer NEUEN Code in Modulen, deren Bestand noch deutsch heisst.
  Wer an so einem Modul arbeitet, benennt die beruehrten Bezeichner im selben
  Zug mit um; ein englischer Neubau neben deutschem Bestand ist der Zustand,
  den diese Regel abschafft.
- **Unberuehrt bleibt die Inhaltssprache**: Kommentare, Doc-Kommentare,
  Commit-Nachrichten, STATUS.md, Preregs und Chat bleiben deutsch, README
  bleibt englisch. Dateinamen bleiben englisch (Regel unten).
- Fachbegriffe des Spiels werden uebersetzt, nicht durchgereicht:
  Musterreihe -> `pattern_line`, Kuppel(platte) -> `dome (tile)`,
  Wertungsplatte -> `scoring_tile`, Strafleiste -> `floor_line`,
  Spalte/Zeile -> `column`/`row`, Zielzelle -> `target_cell`,
  Vorzug(szug) -> `preference`, Bauer -> `builder`.

Anlass: der Layer um `plate_builder.rs`, `column_build.rs` und
`provocation.rs` war zu grossen Teilen deutsch benannt (86 von 113, 43 von 73,
34 von 51 Funktionen), und neu gebaute Bausteine haben die Konvention
fortgeschrieben statt sie zu brechen.

## Dateinamen-Konvention (Nutzer-Anweisung 2026-08-13)

- **Neue Dateien und Verzeichnisse werden IMMER englisch benannt** (Code,
  Tools, Docs, Preregs, Messprotokolle). Der Alt-Bestand deutscher Namen
  wird auf Englisch migriert.
- Die Sprachregel für INHALTE bleibt unberührt: README englisch; STATUS,
  Commits, Kommentare, Chat deutsch.

## Entwicklungs-Standards (Brettspiel-Logik)

- **Modularität** Halte Spiellogik, KI-Entscheidungen und Spielzustand strikt getrennt.
- **Zustandsverwaltung** Änderungen am Spielbrett müssen immer validiert werden, bevor sie den Zustand aktualisieren.
- **Fehlerbehandlung** Implementiere defensive Programmierung für alle Benutzer- und KI-Eingaben.
- **KI-Gegner** Priorisiere Lesbarkeit und Wartbarkeit der Heuristiken gegenüber komplexen, schwer debugbaren Optimierungen.

## Laufzeiten messen, nicht schätzen (Nutzer-Anweisung 2026-08-25)

**Jeder Messlauf schreibt seine Dauer in sein eigenes Artefakt.** Geschätzte
Restzeiten sind wertlos; in der Nacht vom 2026-08-25 lagen drei davon daneben,
während ein 814-Partien-Lauf über 99 Minuten ohne ablesbaren Fortschritt lief.

Pflichtfelder im Ergebnis-JSON jedes Laufs:

```
"laufzeit": {"wanduhr_s": ..., "cpu_s": ..., "threads": ..., "s_je_partie": ...}
```

`threads` gehört dazu, weil dieselbe Zahl in zwei Arena-Einstiegen
Verschiedenes bedeutet (`run_heuristic_v1_vs_v2_arena`: `0` = alle Kerne;
`run_net_vs_heuristic_v2_arena`: `<= 1` = sequenziell). Ohne sie ist
`wanduhr_s` nicht vergleichbar.

**Warum ins ARTEFAKT und nicht (nur) nach STATUS.md:** STATUS.md wird
regelmässig gekürzt (zuletzt 882 auf 659 Zeilen). Laufzeiten dort verrotten
oder verschwinden; im Artefakt des Laufs können sie nicht von ihm driften.

**STATUS.md trägt davon nur die Planungsgrösse** — eine kurze Kostentabelle
"welcher Aufbau kostet wie lange", damit die nächste Sitzung einen Lauf
einplanen kann, ohne ihn erst zu starten. Abschnitt "Laufzeiten (gemessen)".

**Dazu Pflicht bei allem, was länger als ein Werkzeugaufruf dauert:** ein
Fortschrittszähler mit `flush=True` (siehe Abschnitt "Lange Läufe NIE in eine
Pipe"). Eine Dauer, die man erst am Ende erfährt, hilft beim nächsten Lauf,
aber nicht beim laufenden.

## Infrastruktur bewerten: Irrtumskosten, nicht Elo (Nutzer-Anweisung 2026-08-25)

Wenn ein Vorschlag den Spieler nicht stärker macht, ist „wie viel Elo bringt
das?" die falsche Frage. Die richtige lautet: **wie viel billiger macht es,
sich zu irren?**

Der Nutzen von Messinfrastruktur taucht in keinem Elo-Wert auf. Er zeigt sich
darin, dass ein falscher Weg früher, mit weniger Partien und weniger
Rechenzeit als falsch erkennbar wird. Präzedenzfall:
`PREREG_search_rng_split.md` hat keinen einzigen Zug verbessert – aber vorher
galt „gleicher Spielindex, gleiche Startbedingungen" nur bis zur ersten Suche;
gepaarte Arenen waren nominell gepaart, nicht tatsächlich.

**Der Beleg, dass der Engpass hier wirklich beim Messen sitzt** (und die Regel
damit kein Freibrief ist): 5,75 Prozentpunkte Streuung bei n=400 für
IDENTISCHE Konfiguration, und der Seed bewegt die Metrik 4- bis 6-mal stärker
als jeder Knopf. Unter dieser Auflösung kauft man Zufallsbefunde.

**Und die Gegenprobe, damit die Regel nicht jede Infrastrukturarbeit
schönredet:** genau so kann man sich in Messgenauigkeit einrichten und die
härtere Frage vermeiden, ob überhaupt Ideen da sind, die stark genug sind, um
gemessen zu werden. Ein Infrastruktur-Vorschlag braucht deshalb einen
BENANNTEN Nutznießer – eine konkrete Messung, die dadurch möglich oder
schärfer wird –, nicht „hilft künftig allgemein".

## Messungen laufen EXKLUSIV — und ein Build ist Nebenlast (2026-08-25)

**Während eine Arena, ein Self-Play oder eine netz-/suchgestützte Sonde läuft,
darf nichts anderes Rechenlast erzeugen.** CPU-Nebenlast verstümmelt Partien
nichtdeterministisch; die Signatur, an der es einmal aufgefallen ist, war ein
Endstand von 3:1. Determinismus-Prüfungen gelten nur unter den
Lastbedingungen, unter denen gemessen wurde.

**Nebenlast heißt CPU-Last, nicht Absicht.** Das ist die Stelle, an der die
Regel am 2026-08-25 gebrochen wurde: `cargo test --release` und `cargo build`
wurden als „nur Bauen, keine Messung" verbucht und liefen gegen den Lauf einer
Parallelsitzung. Ein Build ist Volllast über viele Kerne — er zählt.

Dazu gehören ausdrücklich:

- `cargo build` / `cargo test` (rayon, viele Kerne)
- `python -m maturin build`, `pip install` des Wheels
- jede Sonde, jedes Trainings- oder Auswertungsskript
- auch „nur schnell" — die Dauer ändert nichts an der Art

**Nicht davon betroffen:** Dateien lesen und schreiben, Dokumentation, greps.
Ein `git commit` ist ein Grenzfall (der pre-commit-Hook scannt das Repo) —
im Zweifel bis nach dem Lauf aufheben.

**Bei parallelen Sitzungen gilt ein ausdrücklicher Staffelstab.** Wer misst,
sagt es an; wer wartet, fasst nichts an; wer fertig ist, gibt die Maschine
in EINER Nachricht frei. Und wer die Zusage bricht, meldet es SOFORT und
ungefragt — die andere Sitzung muss entscheiden können, ob ihr Lauf
kontaminiert ist. Ein wiederholter Lauf ist billiger als ein stiller
Messfehler im Artefakt.

**Spurenlage, falls es doch passiert ist:** Kompilier-Überlappung lässt sich
an `target/release/.fingerprint` mit `find -newermt` datieren. Ein `cargo
test` aus dem Cache erzeugt dagegen CPU-Last OHNE Spur im Dateisystem — der
Verdacht ist dadurch nicht ausräumbar, nur durch Wiederholung. Byte-gleiche
Artefakte belegen dann beides auf einmal: keine Kontamination und
Determinismus unter sauberen Bedingungen.

## Lange Läufe NIE in eine Pipe (Nutzer-Anweisung 2026-08-25)

**Kein `| tail`, `| head`, `| grep`, `| Select-Object` hinter einem Build, Test,
Training oder Messlauf.** Die Pipe puffert, bis der Prozess endet: solange
sieht man NICHTS — auch keine Fortschrittszeilen, auch nicht mit `python -u`.
Bei einem Lauf über Stunden heißt das, man kann weder Fortschritt noch
Führung noch Partienzahl ablesen, bis alles vorbei ist.

Zwei weitere Schäden derselben Bauform:

- **Der Exit-Code verschwindet.** In der Pipe zählt der Status des LETZTEN
  Glieds; ein abgestürzter Build hinter `| tail` sieht grün aus.
- **PowerShell bricht die Pipeline früh ab.** `... | Select-Object -First N`
  stoppt das native Programm, sobald N Zeilen da sind — Ergebnis ist ein
  Phantom-Fehler, der dreimal falsch diagnostiziert wurde.

**Stattdessen:** `run_in_background` OHNE Pipe und OHNE Umleitung starten.
Dann landet die Ausgabe direkt in der Aufgaben-Datei des Harness, und der
Nutzer sieht in den Hintergrundaufgaben, dass sich etwas tut. Eine eigene
Umleitung (`> datei.log`) ist genauso schlecht wie eine Pipe -- sie nimmt dem
Harness die Ausgabe weg.

**Nutzer-Anweisung 2026-08-25: in den Hintergrundaufgaben muss Fortschritt
SICHTBAR sein.** Ein Lauf, der stumm bleibt, ist ein Lauf, dessen Stand
niemand kennt -- und geschätzte Restzeiten sind kein Ersatz (drei Schätzungen
in einer Nacht lagen daneben). Also: `python -u`, `flush=True` an jeder
Fortschrittszeile, keine Pipe, keine Umleitung.

```
python -u tools/probes/x.py > logs/x.out 2>&1
```

**Und die andere Hälfte des Problems:** eine Sonde, die nur am Ende druckt,
ist auch bei sauberem Start blind. Wer einen Lauf über mehr als ein paar
Minuten baut, gibt ihm einen Fortschrittszähler mit `flush=True` — sonst ist
die einzige Antwort auf „wie steht's?" ein Achselzucken.

Anlass: der Lehrer-Test am 2026-08-25 lief 27 Minuten ohne jede ablesbare
Zwischeninformation, weil er als `python -u ... 2>&1 | tail -26` gestartet
wurde. Die Regel stand vorher nur im Gedächtnis und hat dort nicht gegriffen.

## Push scheitert am pre-push-Hook: examples/ und benches/ (wiederkehrend)

Der pre-push-Hook laeuft `cargo test --release`, und das kompiliert **auch
`engine/examples/*.rs` und `engine/benches/*.rs`**. Ein Signaturwechsel an
einem oeffentlichen `run_*`- oder `net_search_*`-Einstieg bricht darum den
Push, obwohl `cargo build` und der Wheel-Build gruen waren.

**Regel: Wer eine oeffentliche Engine-Signatur aendert, sucht im SELBEN Zug
alle Aufrufer in `engine/examples/` und `engine/benches/` und zieht sie nach.**
Pruefbefehl vor dem Push (aus `engine/`):

```
cargo test --release --no-run
```

Fuer neue Pflichtparameter, die Bestandsverhalten erhalten sollen, ist in den
Beispielen `SearchConfig::from_env()` der richtige Wert (net_mcts.rs:368: kein
Cache, byte-identisch zum frueheren Env-Getter) – nicht `default()`.

**Zweite Stolperfalle beim selben Befehl:** `cargo test --release` bricht mit
`STATUS_DLL_NOT_FOUND` (0xc0000135) ab, wenn die Python-DLL nicht im PATH ist.
Vorher in der Shell voranstellen:

```
$env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH
```

## Worktrees & git-crypt (Stolperfalle)

`git worktree add` scheitert in diesem Repo am git-crypt-Smudge-Filter
(git-crypt findet seinen Schlüssel unter `.git/worktrees/<name>/` nicht).
Workaround — Worktree mit umgangenem Filter anlegen:

```
git -c filter.git-crypt.smudge=cat -c filter.git-crypt.clean=cat -c filter.git-crypt.required=false worktree add <pfad> <branch>
```

Im Worktree enthält `player_profiles.json` dann Ciphertext — für Engine-/
Tool-Arbeit egal, aber die Datei dort NIE bearbeiten oder committen.

## STATUS.md ist das Übergabedokument (Nutzer-Entscheid 2026-08-17)

`evaluations/STATUS.md` ist die **einzige** Quelle für den aktuellen Stand —
kein Artifact, keine Kopie, keine zweite Ansicht. Der Grund ist gemessen und
nicht theoretisch: an einem einzigen Tag haben drei überholte, aber plausible
Quellen Zeit gekostet (ein Code-Kommentar statt der Primärquelle, ein
„GÜLTIG"-Etikett an einer Messung, deren Voraussetzung weggefallen war, und
eine Sonden-Skala, die zu 88 % im Trainingssatz lag).

**Pflege-Regel:** Wer einen Befund erzeugt, trägt ihn im selben Zug in
STATUS.md nach — und prüft dabei, ob ein *anderer* Abschnitt dadurch falsch
wird. Genau das ist zweimal passiert: oben stand noch „beide Wege negativ",
während weiter unten schon der Befund stand, der das widerlegt. Für einen
Menschen ein Schönheitsfehler, für die nächste Sitzung eine Falschaussage.

## Öffentliches Repo: keine Rechnerstruktur (Nutzer-Entscheid 2026-08-17)

Das Repo ist öffentlich. **Neue Dateien enthalten keine absoluten Pfade und
keinen Nutzernamen.** Wo ein maschinenabhängiger Pfad gebraucht wird, kommt er
aus der Umgebung, mit Ableitung als Fallback — Vorbilder im Baum:
`MOSAIC_PYTHON_DIR` (tools/hooks/pre-push, sonst aus `sys.executable`),
`MOSAIC_BACKUP_DIR` (tools/mosaic_backup.ps1, sonst `$env:OneDrive`),
`MOSAIC_MODELS_DIR` (engine/examples, sonst relativ zum Crate).

**Die Historie wird NICHT umgeschrieben.** Ältere Commits enthalten noch
Vorname und einen Python-Installationspfad; ein `filter-repo` plus Force-Push
würde jeden Klon invalidieren, und bei atomaren Commits müsste man gezielt
danach suchen. Nutzer-Abwägung: mehr Kosmetik als Nutzen. Nicht neu vorschlagen.

**Prüfbefehl** vor dem Pushen neuer Dateien:

```
git ls-files -z | xargs -0 grep -lIE "Patrick|OneDrive.(Documents|Backups)"
```

Beim Bereinigen solcher Pfade per Regex: eine Zeichenklasse braucht ZWEI
Backslashes vor dem Schrägstrich (`[\/]`). Mit einem escapt er den
Schrägstrich, trifft nur Vorwärtsschrägstriche und lässt jeden Windows-Pfad
still stehen — dieser Fehler ist am 2026-08-17 zweimal passiert.

## Subagenten: Opus, Aufwand mittel (Nutzer-Anweisung 2026-08-26)

- **Subagenten laufen mit Modell Opus bei mittlerem Aufwand** (`model: "opus"`,
  Reasoning-Effort medium). Ersetzt die fruehere Sonnet-Vorgabe vom 2026-07-21.
- Die Arbeitsteilung bleibt unveraendert: der Koordinator plant, prueft und
  entscheidet; Ausfuehrung (Code-Kartierung, Doku-Entwuerfe, Beleg-Greps,
  Umbauten) geht wo immer moeglich an Subagenten.
- Regel 0 gilt weiter: Agenten-Befunde sind Behauptungen; tragende Zahlen
  selbst nachpruefen.

## Workflow-Präferenzen

- Bevor du große Refactorings durchführst, skizziere kurz den Plan (1-2 Sätze).
- Führe Änderungen schrittweise durch (Atomic CommitsEdits).
- Für Commits gilt: Kurzbeschreibung im Titel, dann in der Beschreibung das warum. Das was steckt im diff der Dateien.
- Wenn Unklarheiten bei den Spielregeln bestehen, frage kurz nach, anstatt Annahmen zu treffen.
- Schau in vorhandene scripts ob dort bereits relevante funktionen vorhanden sind bevor du was neues baust (zb arena.py war schon da, aber du hast dir selbst noch eine gebaut)
