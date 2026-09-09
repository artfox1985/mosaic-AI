<!-- STATUS: OFFEN | Frage: Wie wird das v27-Trainingsfenster zugeschnitten -- das erste VOLLSTAENDIG stationaere, und zugleich das letzte unter dem Einfrieren? | Beleg: nichts gebaut, nichts gemessen. Zuschnitt hergeleitet aus PREREG_v25_window.md par.17 mit den tatsaechlichen Dateizahlen der v25-b01-Erzeugung; v23-b01 faellt ganz heraus, v24-b07 rutscht auf G-2 und traegt dort EINE Schwarm-Haelfte. Zwei Punkte offen und beide vom Nutzer zu entscheiden: welche Haelfte (das gemessene Kriterium trennt nicht, PREREG_v26_window par.6/par.8) und wer erzeugt (haengt an Tor 1). -->

# PREREG v27: Fensterzuschnitt

**Vorlage ist `PREREG_v25_window.md` par.17** ("Der stationaere Zustand, wenn alles
durchrotiert ist"). **v27 ist die erste Generation, in der dieser Zustand tatsaechlich
erreicht ist**: alle drei Generationen im Fenster bringen die Zwei-Haelften-Struktur des
Schwarms mit, und keine Klasse stammt mehr aus einer aelteren Erzeugungsregel.

**Und es ist das letzte Fenster unter dem Einfrieren.** `v27-b01` ist nach der
Nutzer-Praezisierung vom 2026-09-09 der letzte eingefrorene Arm; danach endet die Regel
"nur das Material aendert sich" (`PREREG_v25_window.md` par.18).

## par.1 ZUSCHNITT (hergeleitet, nicht entschieden)

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
| Schwarm G-2 | 145 aus EINER Haelfte von `v24-b07` (par.2) | 145 | 1.450 |
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

## par.2 DER EINE ECHTE ZUSCHNITT-ENTSCHEID: welche G-2-Haelfte

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

**Diese Prereg entscheidet es nicht.** Sie haelt fest, dass die Entscheidung ansteht,
was gemessen ist, und dass jede Wahl begruendbar bleibt.

## par.3 DER ZWEITE OFFENE PUNKT: wer erzeugt

**Haengt an Tor 1** (`PREREG_v26_window.md` par.8, laufender dritter Seed). Generatorwahl
und Promotion sind zwei Entscheidungen (`docs/generation_loop.md`):

* **`v26-b01` gewinnt Tor 1** -- er wird Generator, moeglicherweise auch Champion, und die
  neuen Klassen heissen `selfplay_v26-b01-*`.
* **Tor 1 faellt negativ aus** -- dann ist zu entscheiden, ob `v25-b01` ein zweites Mal
  erzeugt (das Fenster rotiert trotzdem weiter, nur mit demselben Erzeuger wie v26) oder
  ob v26 als Generation ohne Nachfolger endet. Praezedenz fuer den ersten Fall gibt es
  nicht; er waere zu begruenden.

**Beides beruehrt den Zuschnitt oben nicht** -- die Groessen stehen, nur die Praefixe der
NEUEN Klassen haengen am Erzeuger.

## par.4 WAS NICHT NEU ENTSCHIEDEN WERDEN MUSS

Erzeugungsrezept (Umschaltpunkt 1 + Weg C fuer den Sockel; glatte Temperatur + Weg C und
Weg B fuer die beiden Schwarm-Haelften, Wurzelrauschen AN in der temperierten und AUS in
der Ausflug-Haelfte, par.17), Trainingsrezept, Ziehungsregel der Abweichung, Blockgroesse 5
in jeder Arena, die beiden Tor-Flaechen. Alles registriert und bis `v27-b01` unveraendert.

**Die Korrektur aus v25 gilt fort:** `--games` zaehlt bei Weg B die Ausfluege MIT. Fuer
4.000 Identitaeten der Ausflug-Haelfte also `--games 4000`.

## par.5 DIE ERZEUGUNGSBEFEHLE FUER v27 (Generator offen, siehe par.3)

Seeds: 20260914 / 20260915 / 20260916 (v26 nahm 20260911-13). `<GEN>` ist der Generator
aus par.3, die Spec bleibt `models/v24-b07_brierbest.spec.json` -- sie ist bis v27
geschlossen und bekommt bewusst keine Kopie unter neuem Namen.

```
# 1) Traeger, 4.000 Partien -- policy-aktiv
python -u self_play.py --mode network --model models/alphazero_<GEN>_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100   --version <GEN>-policy --threads 11 --chunk 10 --per-file 10 --seed 20260914   --tau-argmax-from-move 1 --deviate-prob 1.0

# 2) Schwarm Haelfte a, 4.000 Partien -- value-only, breite Abdeckung
python -u self_play.py --mode network --model models/alphazero_<GEN>_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version <GEN>-value-tempc --threads 11 --chunk 10 --per-file 10 --seed 20260915   --action-temp 2 --deviate-prob 1.0

# 3) Schwarm Haelfte b, 4.000 Identitaeten -- value-only, unverzerrte Ziele
python -u self_play.py --mode network --model models/alphazero_<GEN>_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version <GEN>-value-excursion --threads 11 --chunk 10 --per-file 10 --seed 20260916   --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
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
