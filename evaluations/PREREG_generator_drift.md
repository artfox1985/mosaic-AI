<!-- STATUS: UEBERHOLT | Frage: Wie gross ist die Drift zwischen dem heutigen Build und dem v22-Korpus-Erzeuger? | Beleg: ZURUECKGEZOGEN/GEGENSTANDSLOS 2026-08-26, am Tag der Anlage (par.5): die Voraussetzung war ein MESSFEHLER -- in den Laeufen fehlte --heuristik-variante v2huelle (Default v1). Korrekt gefahren reproduziert der heutige Build den Korpus bit-genau, 1733 Schritte Feld fuer Feld; es gibt keine Drift zu messen. Die Datei bleibt als Beleg stehen, wie der Fehler entstand (par.3 gegen par.5). -->

# Vorregistrierung: Wie gross ist die Erzeuger-Drift?

**Angelegt 2026-08-26, VOR dem Lauf.** Die Entscheidungsregel steht unten und
wird nicht nachtraeglich ausgelegt.

## par.1 Die Lage

`data/manifest_hv2_20260825_172710.json` weist den Erzeuger als Commit
`dbf6a086dc9f` mit `git_dirty: true` aus. Der Reproduktionstest (STATUS.md
Abschnitt 1c) hat gezeigt:

| Vergleich | Ergebnis |
| --- | --- |
| zwei frische Laeufe, HEAD | identisch, 1755 Schritte, Feld fuer Feld |
| HEAD gegen Korpus | ABWEICHUNG (1755 gegen 1733 Schritte) |
| Build auf `dbf6a08` gegen Korpus | ABWEICHUNG, dieselbe wie HEAD |
| Build auf `dbf6a08` gegen HEAD | identisch, Feld fuer Feld |

Dazu: im Erzeugungsfenster (25.08. 17:16 bis 26.08. 01:52, 34 Commits) hat
KEIN Commit `engine/src` angefasst -- die Engine-Quelle ist damit ueber das
ganze Fenster ausgeschlossen, nicht nur an den Endpunkten. Das Modell ist
md5-identisch zur eingefrorenen Kopie. Uebrig bleibt der unversionierte
Anteil, und der ist weg.

## par.2 Die Frage, die davon NICHT beantwortet ist

**Schrittverschieden und verhaltensgleich schliessen sich nicht aus.** Zwei
Spieler koennen an einer Stelle anders waehlen und dennoch dieselbe Staerke
und dasselbe Strukturprofil haben. Ohne diese Zahl ist die Wahl zwischen
"hinnehmen" und "Korpus neu erzeugen" (8,4 h) ein Bauchgefuehl.

## par.3 Zuschnitt

* **Rezept woertlich** aus `cli_args` des Korpus-Manifests: `sims 600`,
  `threads 11`, `chunk 10`, `per_file 10`, `c_puct 1.5`,
  `add_root_noise true`, `deterministic false`, `tau_argmax_from_move 0`,
  `record_rtv false`, Modell `alphazero_v21_2d_brierbest.onnx`,
  `heuristik_variante v2huelle`.
* **Seed 20260826 wie im Korpus.** Damit tragen die Partien dieselben
  Spielindizes und Startbedingungen -- ein unabhaengiger Seed braeuchte ein
  Vielfaches an Partien fuer dieselbe Schaerfe.
* **n = 1000 Partien**, verglichen gegen die ERSTEN 1000 Korpuspartien
  (Dateien 1-100). Der Chunk-Seed ist `base_seed + chunk_idx`, die
  Zuordnung Datei-zu-Datei ist damit exakt.
* **Auswertung mit `tools/corpus_sanity_check.py` auf BEIDEN Seiten** --
  gleicher Codepfad, gleiche Statistik.
* **Differenz auf BLOCK-Ebene** (Datei = Block, 100 Bloecke je Arm), nicht je
  Partie: Paar-SEs werden auf Partie-Ebene massiv unterschaetzt (stehende
  Regel seit 2026-08-04).
* **Alle sechs Standard-Kennzahlen** (CLAUDE.md 2026-08-23), Laufzeitblock ins
  Artefakt, exklusiver Lauf.

### Warum n=1000 und nicht 500

Gemessen an den ersten 50 Korpusdateien: volle Spalten **0,761 je Seite,
SD 0,803**. Daraus 95%-KI bei 500 Partien (1000 Seiten) rund **+-0,050**, auf
Block-Ebene **+-0,055**. Eine Entscheidungsregel "Delta unter 0,05 heisst
gleich" laege damit AUF der eigenen Aufloesungsgrenze: ein wahres Delta von
0,09 koennte als 0,04 gemessen werden und den Freispruch ausloesen. Bei n=1000
halbiert sich die Varianz, das KI der DIFFERENZ liegt bei rund +-0,05, und die
Regel unten ist erreichbar statt dekorativ.

Kosten: 1,59 s je Partie (gemessen 2026-08-26, threads 11), also rund
**27 Minuten** gegen 8,4 h Neuerzeugung.

## par.4 ENTSCHEIDUNGSREGEL (vor dem Lauf festgelegt)

Entscheidungsmass ist **volle Spalten je Seite**, gepaart auf Block-Ebene.
Geprueft wird als **Aequivalenz**, nicht als Nullhypothese -- "nicht
signifikant verschieden" ist kein Beleg fuer Gleichheit.

* **VERHALTENSGLEICH**, wenn das 95%-KI der Block-Differenz **vollstaendig
  innerhalb von +-0,10** liegt. Dann ist der heutige Build als Fortschreiber
  des Korpus unbedenklich, und das Einfrieren kann auf ihm aufsetzen.
* **MATERIELL VERSCHIEDEN**, wenn das 95%-KI **die +-0,10 verlaesst** und der
  Punktschaetzer betragsmaessig darueber liegt. Dann steht Neuerzeugung zur
  Debatte -- Entscheidung bei den Nutzern, nicht hier.
* **UNENTSCHIEDEN** in jedem anderen Fall (KI ueberlappt die Grenze). Dann
  wird gemeldet, nicht ausgelegt.

Die 0,10 sind gesetzt, nicht hergeleitet: sie sind rund 13 Prozent des
Korpus-Niveaus von 0,761 und liegen ueber der erreichbaren Aufloesung. Ein
engerer Wert waere nicht messbar, ein weiterer nicht aussagekraeftig.

**Waechter gegen den Tunnelblick:** faellt eine der uebrigen fuenf
Standard-Kennzahlen um mehr als 10 Prozent ihres Korpus-Werts auseinander,
gilt der Lauf als UNENTSCHIEDEN, auch wenn die vollen Spalten die
Aequivalenzgrenze halten. Der Korpus ist nicht nur seine Spaltenzahl.


## par.5 ZURUECKGEZOGEN (2026-08-26, am Tag der Anlage)

**Die Voraussetzung dieser Prereg war ein Messfehler.** par.1 stuetzt sich auf
"HEAD gegen Korpus: ABWEICHUNG". In den drei Laeufen dahinter fehlte
`--heuristik-variante v2huelle`; `self_play.py:637` setzt dann `v1`. Gemessen
wurde v1 gegen einen v2huelle-Korpus.

Korrekt gefahren, gleiches Rezept, gleicher Seed: **1733 Schritte, Feld fuer
Feld gleich** zur ersten Korpusdatei. Der heutige Build IST der Erzeuger. Es
gibt keine Drift zu messen.

**Der Lauf selbst ist nicht wertlos** (nachgetragen 2026-08-28 aus dem
Zeile-1-Statuskopf): die 1000 Partien (24,8 min) sind als Vergleich
`v1` gegen `v2huelle` unter Self-Play-Bedingungen verwertbar und in
`STATUS.md` Abschnitt 1c festgehalten.

**Warum die Datei stehen bleibt statt geloescht zu werden:** die
Entscheidungsregel in par.4 war richtig gebaut -- Aequivalenz statt
Nullhypothese, Grenze ueber der gemessenen Aufloesung, Waechter gegen den
Tunnelblick. Sie hat nur eine Frage beantwortet, die es nicht gab. Und par.3
zeigt den Fehler im Original: das Rezept steht dort woertlich richtig,
inklusive `heuristik_variante v2huelle`. Zwischen Vorregistrierung und
Kommandozeile ist es verlorengegangen.

**Die Lehre, in einem Satz:** ein fehlendes Flag meldet sich nicht, es ist ein
Default. Das Manifest DES EIGENEN LAUFS haette es sofort gezeigt -- es fuehrt
`cli_args.heuristik_variante` als Feld. Ab jetzt: vor der Auswertung das
erzeugte Manifest gegen das Referenz-Manifest halten, nicht erst danach.
