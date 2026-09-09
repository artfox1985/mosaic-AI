<!-- STATUS: OFFEN | Frage: Wie wird das v27-Trainingsfenster zugeschnitten -- das erste VOLLSTAENDIG stationaere, und zugleich das letzte unter dem Einfrieren? | Beleg: nichts gebaut. Zuschnitt hergeleitet aus PREREG_v25_window.md par.17, nachgerechnet an den Bestandszahlen: 580 Traeger + 2.366 Schwarm = 2.946 Dateien, Seed 20260933, Val-Pool ^selfplay_v26-. Erstes VOLLSTAENDIG stationaeres Fenster und letztes unter dem Einfrieren. Beide Zuschnitt-Entscheide sind vom Nutzer gefallen (2026-09-09): Generator v26-b01 (par.3, unabhaengig von Tor 1), G-2-Posten = temperierte Haelfte (par.2, Kriterium trennte nicht, entschieden auf der Rolle). Offen ist nur noch die Erzeugung selbst. -->

# PREREG v27: Fensterzuschnitt

**Vorlage ist `PREREG_v25_window.md` par.17** ("Der stationaere Zustand, wenn alles
durchrotiert ist"). **v27 ist die erste Generation, in der dieser Zustand tatsaechlich
erreicht ist**: alle drei Generationen im Fenster bringen die Zwei-Haelften-Struktur des
Schwarms mit, und keine Klasse stammt mehr aus einer aelteren Erzeugungsregel.

**Und es ist das letzte Fenster unter dem Einfrieren.** `v27-b01` ist nach der
Nutzer-Praezisierung vom 2026-09-09 der letzte eingefrorene Arm; danach endet die Regel
"nur das Material aendert sich" (`PREREG_v25_window.md` par.18).

## par.1 ZUSCHNITT (hergeleitet; die zwei Entscheide dazu in par.2 und par.3)

G = v26-Erzeugung, G-1 = `v25-b01`, G-2 = `v24-b07`. `v23-b01` faellt aus der Rotation.

**Sockel (Policy-Klasse, Traeger)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Sockel NEU | v26-Erzeugung, policy-aktiv | 400 | 4.000 |
| aus G-1 | 135 der 400 `selfplay_v25-b01-policy_*` (seed-bestimmt) | 135 | 1.350 |
| aus G-2 | 45 der 400 `selfplay_v24-b07-policy_*` (seed-bestimmt) | 45 | 450 |
| **Summe** | | **580** | **5.800** |

**Schwarm (Value-Klasse, policy-maskiert)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Schwarm NEU | v26, temperiert plus Ausfluege | 800 | 8.000 |
| Schwarm G-1, Haelfte a | alle 400 `selfplay_v25-b01-value-tempc_*` | 400 | 4.000 |
| Schwarm G-1, Haelfte b | alle 401 `selfplay_v25-b01-value-excursion_*` | 401 | 4.010 |
| Sockel-Rest G-1 | die 265 uebrigen `selfplay_v25-b01-policy_*` | 265 | 2.650 |
| Sockel-Rest G-2 | 355 der `selfplay_v24-b07-policy_*` | 355 | 3.550 |
| Schwarm G-2 | 145 der 400 `selfplay_v24-b07-value-tempc_*` (par.2, entschieden) | 145 | 1.450 |
| **Summe** | | **2.366** | **23.660** |

**Fenster gesamt 2.946 Dateien, 29.460 Partien** -- dieselbe Groesse wie v25 (2.947) und
v26 (2.948), die Zusammensetzung ist eine andere. Die Abweichung um eine Datei kommt aus
der Ausflug-Klasse, die je Lauf 400 oder 401 Dateien liefert; sie ist ohne Bedeutung und
wird NICHT ausgeglichen.

**SEED der seedbestimmten Auswahlen: 20260933** (v26 nahm 20260929, v25 20260925). Er
steuert beide Ziehungen: die 135 aus G-1 und 45 aus G-2 fuer den Sockel sowie die 145 fuer
den G-2-Schwarm.

**Val-Pool wandert auf `^selfplay_v26-`** (in v26: `^selfplay_v25-`). Wie dort gehoert er
in den Kopf der Kette, nicht in die Erinnerung.

## par.2 WELCHE G-2-HAELFTE (entschieden)

Ab v27 rutscht `v24-b07` auf G-2, und dort steht EIN Posten von 145 Dateien fuer beide
Schwarm-Haelften zusammen. **Nutzer-Entscheid (v26-Prereg par.6): kein Split** -- 145
Dateien auf zwei Klassen aufgeteilt machen aus zwei klaren Beitraegen zwei zu kleine.

**Gemessen wurde, und das Kriterium trennt nicht** (`PREREG_v26_window.md` par.6, Artefakte
`g2_swarm_choice_*.json`): distinkte Endbretter je Seite 0,9935 gegen 0,9741, die bedingte
Vielfalt saettigt bei BEIDEN am Maximum (4 von 4). Ein Unterschied von 0,02 traegt keine
Entscheidung.

**Was die Messung ungeplant zeigt:** die Ausflug-Haelfte liefert bei gleicher Partienzahl
die doppelte Zahl an Records (330,0 gegen 164,5 Schritte je Partie) und eine hoehere
Policy-Entropie (0,6436 gegen 0,5945). Wer nach Wertzielen je Datei zaehlt statt nach
Vielfalt, waehlt den Ausflug.

**Drei Lesarten, damit der Entscheid nicht im Nebel faellt:**

1. **Ausflug** -- mehr Wertziele je Datei, unverzerrte Ziele (Weg B, ohne Wurzelrauschen),
   und die hoehere Spaltenrate (0,768 gegen 0,367 volle Spalten je Seite, gemessen im
   selben Durchgang). Kostet Abdeckungsbreite.
2. **Temperiert** -- Abdeckung ist die klassische Rolle von G-2, und das
   Koordinator-Vorurteil aus par.6 der v26-Prereg zeigte dorthin. Nach den Zahlen ist es
   ein Vorurteil geblieben.
3. **Anderes Kriterium messen** -- wenn die Wahl es wert ist: der Beitrag zum
   Value-Ziel liesse sich als Ablation fahren (zwei Fenster, sonst identisch). Kostet ein
   volles Trainings- und Gating-Paar, also rund 4 h, und faellt damit in dieselbe
   Groessenordnung wie der Nutzen.

**ENTSCHIEDEN 2026-09-09 (Nutzer): die TEMPERIERTE Haelfte.** *"wir nehmen die
temperierte haelfte fuer den g-2 posten."* Der G-2-Schwarm besteht damit aus 145 Dateien
`selfplay_v24-b07-value-tempc_*`, seed-gezogen mit 20260933; die Ausflug-Dateien der
Generation v24-b07 rotieren ersatzlos hinaus.

**Was gegen die Wahl sprach, bleibt aktenkundig** -- nicht um sie infrage zu stellen,
sondern damit ein spaeterer Leser die Lage kennt: die Ausflug-Haelfte haette bei gleicher
Dateizahl doppelt so viele Records geliefert (330,0 gegen 164,5 Schritte je Partie) und
kommt aus spaltenreicherem Material (0,768 gegen 0,367 volle Spalten je Seite). Dagegen
steht die Rolle von G-2: Abdeckung, und die liefert die temperierte Haelfte per
Erzeugungsregel (glatte Temperatur, Wurzelrauschen an). Das gemessene Kriterium hat
zwischen beiden nicht getrennt, die Entscheidung faellt also auf der Rolle, nicht auf der
Zahl -- und das ist hier der richtige Grund, weil die Zahl nichts hergibt.

**Folge fuer die Kette:** die Auswahl zieht aus `selfplay_v24-b07-value-tempc_*.pkl`
(400 Kandidaten, 145 gezogen), nicht mehr aus `value-*`.

## par.3 WER ERZEUGT (entschieden)

**ENTSCHIEDEN 2026-09-09 (Nutzer): `v26-b01` erzeugt.** *"ich sag mal v26 wird
erzeugen."* Die neuen Klassen heissen damit `selfplay_v26-b01-policy_*`,
`-value-tempc_*`, `-value-excursion_*`.

**Das ist unabhaengig von Tor 1, und zwar regelkonform:** Generatorwahl und Promotion sind
zwei Entscheidungen (`docs/generation_loop.md`). Fuer die Generatorwahl reicht "nicht
schlechter", und das ist belegt -- 210:190 im vollen Lauf, 85:55 im zweiten, in keinem der
beiden liegt v26-b01 hinten. Praezedenz ist v25-b01, der als Generator gewaehlt wurde,
bevor seine Promotion feststand.

**Was offen bleibt, ist allein die PROMOTION:** faellt der dritte Seed negativ aus, erzeugt
`v26-b01` trotzdem, aber `v25-b01` bleibt Champion -- und die Elo-Leiter bekommt keine
neue Kante. Der Zuschnitt oben ist davon unberuehrt.

**Der Zuschnitt oben ist davon unberuehrt** -- die Groessen stehen, und die Praefixe der
neuen Klassen sind mit dem Generator jetzt festgelegt.

## par.4 WAS NICHT NEU ENTSCHIEDEN WERDEN MUSS

Erzeugungsrezept (Umschaltpunkt 1 + Weg C fuer den Sockel; glatte Temperatur + Weg C und
Weg B fuer die beiden Schwarm-Haelften, Wurzelrauschen AN in der temperierten und AUS in
der Ausflug-Haelfte, par.17), Trainingsrezept, Ziehungsregel der Abweichung, Blockgroesse 5
in jeder Arena, die beiden Tor-Flaechen. Alles registriert und bis `v27-b01` unveraendert.

**Die Korrektur aus v25 gilt fort:** `--games` zaehlt bei Weg B die Ausfluege MIT. Fuer
4.000 Identitaeten der Ausflug-Haelfte also `--games 4000`.

## par.5 DIE ERZEUGUNGSBEFEHLE FUER v27 (Generator offen, siehe par.3)

Seeds: 20260914 / 20260915 / 20260916 (v26 nahm 20260911-13). Generator ist `v26-b01`
(par.3), die Spec bleibt `models/v24-b07_brierbest.spec.json` -- sie ist bis v27
geschlossen und bekommt bewusst keine Kopie unter neuem Namen.

```
# 1) Traeger, 4.000 Partien -- policy-aktiv
python -u self_play.py --mode network --model models/alphazero_v26-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100   --version v26-b01-policy --threads 11 --chunk 10 --per-file 10 --seed 20260914   --tau-argmax-from-move 1 --deviate-prob 1.0

# 2) Schwarm Haelfte a, 4.000 Partien -- value-only, breite Abdeckung
python -u self_play.py --mode network --model models/alphazero_v26-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version v26-b01-value-tempc --threads 11 --chunk 10 --per-file 10 --seed 20260915   --action-temp 2 --deviate-prob 1.0

# 3) Schwarm Haelfte b, 4.000 Identitaeten -- value-only, unverzerrte Ziele
python -u self_play.py --mode network --model models/alphazero_v26-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version v26-b01-value-excursion --threads 11 --chunk 10 --per-file 10 --seed 20260916   --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
```

**Kosten, gemessen an der v26-Erzeugung** (nicht geschaetzt, `docs/measured_runtimes.md`):
Nr. 1 rund 3,0 h bei 2,62 s je Partie, Nr. 2 rund 3,5 h, Nr. 3 rund 2,5 h (8.838 s
gemessen) -- zusammen **rund 9 h**. Die v26-Laeufe waren schneller als die v25-Werte, weil
der Cache-Waechter seinen Rueckstand abgearbeitet hatte und die CPU freigab.

**Cache-Waechter mitlaufen lassen** (`build_cache_incremental.py --watch --workers 3`),
**zwingend unter `MOSAIC_IGNORE_POLICY_TARGET_VALID=1`**: die Variable steht im
Datei-Schluessel, ohne sie landen die Bloecke in einem Namensraum, den das Training nie
adressiert (Vorfall 2026-09-09, 2.680 tote Bloecke, `docs/pitfalls.md`).

## par.6 WAS NACH v27-b01 KOMMT (nur als Zeiger)

Mit `v27-b01` endet das Einfrieren. Was danach ansteht, ist bereits vorregistriert und
gehoert NICHT in diesen Zuschnitt:

* `PREREG_dome_stack_information_sets.md` -- der Kuppelstapel-Umbau (Korrektheits-Fix,
  haengt nicht an einer Messung), mit PRE-Lauf als Basislinie.
* `PREREG_score_clamp_incentive.md` -- die Null-Klammer, Stufe 0 ist eine reine Messung.
* `PREREG_stack_top_feature.md` par.7/par.10/par.11 -- die restlichen Sicht-Stufen und die
  zweite Achse (was WEISS die Suche).
