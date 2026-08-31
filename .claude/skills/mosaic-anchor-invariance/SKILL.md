---
name: mosaic-anchor-invariance
description: Nach JEDER Aenderung an der Spiel-Engine pruefen, ob der eingefrorene Elo-Anker noch dieselben Zuege macht. Nutze das nach jedem Engine-Commit und jedem Wheel-Neubau, vor jeder Anker-Kante, und bevor eine Elo-Zahl ueber die Aenderung hinweg verglichen wird. Deckt ab - Drift-Pruefung gegen Konservierungs-Pruefung, der Befehl je Frage, was ROT bedeutet, warum Vertragshash und Golden-Selbsttest die Frage NICHT beantworten, die Namensfalle in der Leiter.
---

# Anker-Invarianz: macht der Anker noch dieselben Zuege?

**Warum ueberhaupt.** Die ganze Elo-Leiter haengt an EINEM Fixpunkt:
`Heuristik@150` ist per Definition 1000 (`tools/elo_tracker.py:111-115`). Ein
Anker, der nach einer Engine-Aenderung anders spielt, entwertet jede
Elo-Aussage ueber diese Aenderung hinweg -- und zwar STILL, weil kein anderer
Mechanismus es meldet. Der Anker ist eingefroren, damit er sich nicht bewegt;
geprueft werden muss, ob der LEBENDE Code sich von ihm entfernt hat.

**Nutzer-Vorgabe 2026-08-31:** *"bei jeder Spielengine-Aenderung kurzen
Proberun mit hv1 auf dem Live-Wheel und dann mit demselben Seed auf dem
Artefakt-Wheel -- dann siehst eh gleich, ob andere Zuege rauskommen."*

## Die zwei Fragen, die NICHT dieselbe sind

`tools/verify_frozen_heuristic.py` hat dafuer zwei Modi (Zeilen 9-23):

| Frage | Befehl | Rot heisst |
| --- | --- | --- |
| **Drift**: erzeugt der heutige Stand noch dasselbe wie das Artefakt? | (Default, aktuelles Wheel) | der heutige Code hat sich vom Anker entfernt |
| **Konservierung**: spielt das Artefakt noch so wie am Einfriertag? | `--venv` (Wheel aus dem Artefakt) | Umgebungsdrift (ORT, DLL, Interpreter); das Artefakt selbst ist unbrauchbar |

**Beide sind nuetzlich, sie beantworten NICHT dasselbe, und ein Bericht, der
sie vermengt, ist wertlos.**

```bash
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor
```

```bash
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor --venv
```

Das Rezept liegt im Manifest des Artefakts (hv1, 10 Partien, 600 Sims, Seed
20260826, threads 11, c_puct 1,5, Root-Noise an). Verglichen wird Record fuer
Record ueber `corpus_io` -- nicht auf Dateibytes, weil Korpusdateien
komprimiert geschrieben werden; `game_id` traegt einen Zeitstempel und ist
ausgenommen. Der Lauf deckt Drafting, Tiling UND Runde 5 ab.

## Der Vergleichspunkt ist das ARTEFAKT, nicht der lebende Code

**Nutzer-Klarstellung 2026-08-31:** *"die In-Process-Heuristik ist kein guter
Vergleichswert. die ist eigentlich eine Entwicklungsumgebung."*

Das ist keine Feinheit, es dreht die Leserichtung des Tests um:

* Der lebende Heuristik-Pfad im Repo wird WEITERENTWICKELT. Er ist Werkstatt,
  nicht Massstab. Er darf sich aendern, ohne dass irgendetwas kaputt ist.
* Der Fixpunkt der Leiter gehoert deshalb an das eingefrorene ARTEFAKT -- an
  das Ding, das sich per Konstruktion nicht bewegen kann.
* Folge: **"der Anker ist gedriftet" ist keine moegliche Diagnose.** Zeigt der
  Drift-Lauf Rot, hat sich der LEBENDE Code bewegt. Das ist eine Aussage ueber
  die Werkstatt, nicht ueber den Anker.
* Folge: Anker-Kanten werden gegen das Artefakt gefochten, nie gegen den
  In-Process-Pfad. Ein Vergleich mit dem lebenden Pfad taugt als
  AENDERUNGS-MELDER (hat sich das Verhalten bewegt?), nicht als Eichung.

Damit ist auch klar, welcher der beiden Modi unten der wichtigere ist: die
**Konservierung** (`--venv`) haelt die Leiter; die **Drift**-Pruefung sagt nur,
wie weit die Werkstatt inzwischen woanders steht.

## Ablauf nach einer Engine-Aenderung

1. **Wheel neu bauen.** Ohne das prueft der Lauf den alten Stand -- und
   Zahlengleichheit nach einer Aenderung waere dann ALARM, kein Erfolg.
2. **Drift-Lauf fahren** (Default-Modus), exklusiv wie jede Messung, ohne
   Pipe, mit `--out` fuer das Artefakt.
3. **Gruen:** die Aenderung hat den Anker nicht bewegt. Elo-Zahlen bleiben
   ueber sie hinweg vergleichbar. Ergebnis vermerken, fertig.
4. **Rot:** KEINE Reparatur. Das ist ein Nutzer-Entscheid -- Anker bewusst neu
   setzen und ein neues Leitersegment aufmachen, oder die Aenderung
   zuruecknehmen. Praezedenz: die R5-Fix-Grenze; Kanten ueber die Grenze
   werden nie gemischt.

## Was die Frage NICHT beantwortet (dreimal gepruefter Irrtum)

* **Der Handshake im Referee.** Er vergleicht Vertragshashes, und die decken
  ausschliesslich `INPUT_SIZE`, `NUM_PLANES_CHANNELS`, `NUM_ACTIONS` und die
  Kopf-Reihenfolge (`engine/src/lib.rs:639-648`) -- also den
  Netz-Ein-/Ausgabevertrag. Der hv1-Anker ist NETZLOS (Manifest `typ:
  heuristik`, kein `model.onnx`; `tools/frozen_champion_worker.py:89-92`
  behandelt das ausdruecklich). Rot dort heisst nicht "Anker bewegt", gruen
  hiesse nicht "Anker steht". Fuer eingefrorene NETZ-Champions ist die
  Pruefung dagegen einschlaegig.
* **Der Golden-Selbsttest im Referee.** Er laeuft mit dem Interpreter des
  ARTEFAKTS (`tools/frozen_referee_match.py:162-172`) -- Konservierung,
  ausdruecklich kein Drift-Test. Eine Anker-Kante kann also gruen anlaufen,
  waehrend die Drift-Frage offen ist.
* **Ein Match Anker gegen Anker.** Zwei identische Spieler ergeben per
  Konstruktion 50 Prozent, und 50 Prozent unterscheiden "identisch" nicht von
  "verschieden, aber gleich stark". Identitaet ist eine Zug-Frage, keine
  Staerke-Frage (Nutzer 2026-08-31).

## Beim Eintragen der Anker-Kante

**Seit 2026-08-31 ist der Anker das ARTEFAKT:** `ANCHOR_NAME =
"Heuristik_hv1_anchor"` (`tools/elo_tracker.py`), Zeilen vor der Umbenennung
(`Heuristik`) werden per `ANCHOR_ALIASES` auf denselben Knoten gefaltet.
`Heuristik_v2huelle` ist NICHT aliasiert -- das ist der hv2-Lehrer, ein
anderer Spieler.

Davor verankerte der Tracker auf den literalen Namen `Heuristik`, waehrend die
Promotions-Checkliste `Heuristik_hv1_anchor` vorschrieb: jede Anker-Kante
erzeugte einen ZWEITEN, freien Knoten, und `_mm_fit` zentrierte die ankerlose
Komponente auf das geometrische Mittel. Die gedruckten Zahlen trugen dann nur
ihre Differenz (2026-08-31: b01 1148 / Anker 852, Summe exakt 2000).

**Der Pruefschritt bleibt trotzdem Pflicht:** nach JEDER Anker-Eintragung
`python tools/elo_tracker.py report` lesen und auf `NICHT mit Anker
verbunden!` pruefen. Steht der Vermerk irgendwo, ist die betroffene Zahl keine
Leiterposition, sondern eine freie Normierung.

**Die eine unbelegte Fuge, die dabei bekannt bleibt:** der Alias faltet die
Anker-Kanten vom 2026-08-20 auf das am 2026-08-26 eingefrorene Artefakt. Dass
sich der Anker in diesen sechs Tagen nicht bewegt hat, ist NICHT gemessen -- im
Baum liegt kein Wheel jener Tage. Wer eines findet, kann die Fuge mit genau
diesem Skill schliessen.

## Kosten -- GEMESSEN, nicht geschaetzt (2026-08-31)

| Modus | Wanduhr | verglichen |
| --- | --- | --- |
| Drift (aktuelles Wheel) | **22,2 s** | 1.763 Schritte, Feld fuer Feld |
| Konservierung (`--venv`) | **13,4 s** | dieselben 1.763 Schritte |

Verglichen wird jedes Feld jedes Records; ausgenommen ist ausschliesslich
`game_id` (traegt einen Zeitstempel, `generator_repro_probe.IDENTITY_FIELDS`).
Eine Abweichung wird NAMENTLICH gemeldet -- Schritt-Index und Feldname --,
weil "die Policy driftet" und "eine Zugwahl kippt" verschiedene Befunde sind.

**Eine halbe Minute je Engine-Aenderung.** Es gibt keinen Grund, das nicht
jedes Mal zu fahren. Die Alternative ist, eine stille Ankerverschiebung erst
zu bemerken, wenn Elo-Zahlen ueber Wochen nicht mehr zusammenpassen.

## Erstlauf dieser Regel (2026-08-31, Motor `efd564d87bac2722`)

Beide Modi GRUEN, 1.763 Schritte ohne eine einzige Abweichung. Der lebende
Code spielt hv1 also Zug fuer Zug wie das Artefakt -- die Engine-Aenderungen
seit dem Einfrieren (2026-08-26) haben den Anker NICHT bewegt. Artefakte:
`evaluations/artifacts/anchor_drift_live_wheel_20260831.json` und
`anchor_conservation_artifact_wheel_20260831.json`.
