<!-- STATUS: OFFEN | Frage: Wie wird das v32-Fenster zugeschnitten, und welches Rezept faehrt der erste Arm? | Beleg: par.1 ZUSCHNITT steht (Rotationsregel, Bestand am 2026-09-22 gezaehlt: neu v31-b01, G-1 v30-b02, G-2 v29-b11; v28-b02 geloescht). par.6 REZEPT ist OFFEN -- Startgewicht, Knoepfe und die Dosis der Rueckgabe-Streuung sind Nutzer-Entscheide und muessen VOR dem Start stehen. Nichts erzeugt, nichts trainiert. -->

# Vorregistrierung: das v32-Fenster

**Angelegt 2026-09-22** im Generationswechsel v31 -> v32 (Nutzer: *"du faehrst v32"*), nach dem
Ablauf `/mosaic-generation-turnover`. Die Generation v31 ist abgeschlossen: `v31-b01` hat Tor 1
getragen (461:339 aus 800, Block-z +4,24) und ist seit dem 2026-09-20 Champion.

**Diese Datei ist beim Anlegen UNVOLLSTAENDIG und soll es sein.** par.1 ist mechanisch aus der
Rotationsregel herleitbar und steht darum schon; par.6 traegt Entscheide, die dem Nutzer gehoeren.
Der Ablauf verlangt beide VOR dem Start der Erzeugung.

## par.1 ZUSCHNITT (Rotationsregel, Bestand am 2026-09-22 gezaehlt)

G = v32-Erzeugung durch **`v31-b01_brierbest`**; G-1 = `v30-b02` (die v31-Erzeugung);
G-2 = `v29-b11` (die v30-Erzeugung). **`v28-b02` ist aus der Rotation gefallen** und am
2026-09-22 mit pfadgenauer Freigabe geloescht (1.201 Dateien, 1,34 GB; restic-Beleg im Snapshot
`bb2d8bad`, 1.201 Treffer).

**Die Generatorwahl ist hier ohne Konkurrenz:** v31 hatte EINEN Arm. Die Stufenregel aus
`docs/generation_loop.md` ("Generatorwahl unter Armen") greift erst ab zwei Kandidaten; es gilt
die Grundregel "Generator = bester Stand von N-1", und der ist zugleich Champion.

| Generation | Klasse | Dateien | Partien | Policy-Ziel |
| --- | --- | --- | --- | --- |
| `v31-b01` (neu) | policy | noch zu erzeugen | | **ja** |
| `v31-b01` (neu) | value-tempc | noch zu erzeugen | | nein |
| `v31-b01` (neu) | value-excursion | noch zu erzeugen | | nein |
| `v30-b02` (G-1) | policy | 400 | 4.000 | Anteil offen |
| `v30-b02` | value-tempc | 400 | 4.000 | nein |
| `v30-b02` | value-excursion | 401 | 4.010 | nein |
| `v29-b11` (G-2) | policy | 400 | 4.000 | Anteil offen |
| `v29-b11` | value-tempc | 400 | 4.000 | nein |
| `v29-b11` | value-excursion | 401 | 4.010 | nein |

**Im Baum liegen damit heute 2.404 Altdateien** (gezaehlt 2026-09-22), dazu kommen die neuen
Klassen. Die Seed-Ziehung fuer die Traeger-Anteile der Alt-Klassen (bei v31: 135 von 400 bzw. 45
von 400) folgt dem Muster aus `PREREG_v31_window.md` par.1 und wird beim Fensterbau festgelegt.

**SEED: 20260953** (Vierer-Schritt aus `docs/generation_loop.md`: v29 20260941, v30 20260945,
v31 20260949).
**Val-Pool `^selfplay_v31-`** -- das Muster trifft ausschliesslich die neuen Klassen.

## par.2 TORE

Wie `PREREG_v31_window.md` par.2, solange par.6 nichts anderes festlegt. **Tor 1** gegen den
besten Stand der eigenen Linie (`v31-b01`), **Tor 2a** `sp_voll` der neuen Klassen gegen die des
Vorgaengers, **Tor 2b** Replay-Kontrolle.

## par.3 EIN UNTERSCHIED ZU ALLEN FRUEHEREN FENSTERN, der benannt gehoert

Die Alt-Klassen `v30-b02` und `v29-b11` sind unter dem Wheel **1.0.0 oder frueher** erzeugt
worden, die neuen Klassen laufen unter **1.1.0**. Dazwischen liegt die Berichtigung des
Tiling-Cache-Schluessels (`PREREG_code_cleanup_closeout.md` par.8h): bis 1.0.0 warf der Schluessel
zwei Haende mit derselben Chip-Multimenge in anderer Reihenfolge zusammen, sobald mehr als
`CHIP_ALLOC_CAP` (14) Chips gehalten wurden.

**Was das ist und was nicht:** ein Fehler in der MEMOISIERUNG, nicht in der Spielregel -- betroffen
ist, welches Tiling-Ergebnis aus dem Cache kommt, nicht welche Zuege legal sind. Der Kontrakt
(`6ef829e564c58bd5`) ist unveraendert, der Anker reproduziert seinen Referenzlauf Zug fuer Zug.
Die Haeufigkeit des Regimes ist UNGEMESSEN.

**Folge fuer dieses Fenster:** die drei Generationen im Fenster sind nicht unter bitgleichen
Engines entstanden. Das ist kein Aera-Bruch im Sinne der Elo-Leiter (der Anker haelt), aber es
gehoert in den Bericht, statt still hingenommen zu werden. Wer aus diesem Fenster eine Aussage
ueber Merkmals-Wirkungen zieht, hat diesen Unterschied als Nebenfaktor.

## par.6 REZEPT -- OFFEN, Nutzer-Entscheide

**Nichts davon ist entschieden. Der Ablauf verlangt sie VOR dem Start.**

1. **Startgewicht.** Warmstart von `v31-b01_brierbest` oder Kaltstart? Die Kaltstart-Frage ist in
   v30 einfaktoriell beantwortet (404:396 kalt gegen 443:297 warm, 9,36 Punkte, `PREREG_v30_window.md`
   par.9) -- der Warmstart ist der belegte Weg, ein Kaltstart braeuchte einen eigenen Grund.
2. **Knoepfe und Spec der Erzeugung.** Uebernahme der v31-Spec oder Aenderungen. Hierher gehoert
   auch, ob `return_order_mode` aus dem Default 0 geholt wird.
3. **Dosis der Rueckgabe-Streuung `MOSAIC_RETURN_ORDER_RANDOM_P`.** **Der Wert 0,81 ist an der
   v30-Erzeugung geeicht** (17,75 Prozent der Partien mit Gelegenheit). An der v31-Erzeugung
   gemessen sind es **28,0 Prozent** (Sockel; `PREREG_dome_return_order.md` par.13, Nachtrag
   2026-09-22). Bei unveraenderter Dosis streut v32 in deutlich mehr Partien als die 15 Prozent,
   fuer die 0,81 gerechnet wurde. Nach derselben Rechnung laegen rund **0,54** an --
   **Herleitung aus der Messung, keine Entscheidung.**
4. **Zahl der Arme.** v31 hatte einen. Ein zweiter Arm braucht einen benannten Faktor und eine
   eigene Registrierung (`docs/generation_naming.md`).
5. **Val-Pool-Regex und Traeger-Anteile** der Alt-Klassen.

## par.7 PFLICHTPRUEFUNGEN VOR DEM START

Aus dem Ablauf, unveraendert:

* **Manifest-Diff gegen die Referenz** -- das erzeugte `cli_args` gegen das der v31-Erzeugung
  halten. Ein fehlendes Flag meldet sich nicht, es ist ein Default
  (`feedback_run_manifest_gegen_referenz`).
* **Erster Record der neuen Erzeugung aufmachen** und nachweisen, dass die Knoten und Felder
  darin stehen, die getragen werden sollen -- dieselbe Wiedervorlage wie bei P.12/P.16
  (`feedback_record_field_must_precede_generation`).
* **Stack-Draw-Kontrolle** und **Tor 0**.
* **Fenster-Pinning** (`MOSAIC_DATA_EXCLUDE`) setzen, damit Streudateien, die waehrend des Laufs
  entstehen, nicht still ins Fenster laufen (`feedback_window_pinning_during_generation`).
* **Wheel installiert, Kontrakt-Hash im Manifest.** Stand 2026-09-22: Wheel **1.1.0**,
  Hash `6ef829e564c58bd5`, Anker-Drift gruen ueber 1.763 Schritte.
* **Plattenplatz.** Nach der Loeschung am 2026-09-22 liegt `data/` bei 4,6 GB; die neuen Klassen
  brauchen rund 1,3 GB plus Bloecke.

## par.8 KOSTEN (aus `docs/measured_runtimes.md`, damit der Start planbar ist)

Die v31-Erzeugung lief **14,66 h** ueber alle drei Klassen. Das Training des ersten Arms lief
warm in **58 min**. Der Fensterbau und der Monolith kommen dazu; der Monolith des v31-Fensters
liegt bei 1,48 GB und wird fuer v32 neu gebaut (die beiden v31-Monolithen sind darum erst NACH
dem Fensterbau Loeschkandidaten, `PREREG_code_cleanup_closeout.md` ist dafuer nicht zustaendig).
