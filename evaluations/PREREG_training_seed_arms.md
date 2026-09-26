<!-- STATUS: UEBERHOLT | Frage: Traegt der Trainings-Seed so viel Staerke, dass mehrere Seed-Arme je Generation den Sprung vergroessern? | Beleg: ZURUECKGEZOGEN am Tag der Anlage (par.6). Widerspricht dem Nutzer-Entscheid vom 2026-09-10 (Seed gleich innerhalb einer Generation), der Seed-Sweep vom 2026-07-28 hat die Frage schon bearbeitet, und die Mehrkosten (+2,1 h Training, +6 h Tor 1) kaufen mehr als 4.000 Self-Play-Partien. Nichts gefahren. -->

# Vorregistrierung: Seed-Arme je Generation

**Angelegt 2026-09-25**, Vorschlag 1 aus der Nutzer-Frage nach groesseren Generationsspruengen
(*"Registrieren das so vor und takte es ein. Bei Bedarf auch eigene prereg."*). Geschwister:
`PREREG_value_readout.md` (Vorschlaege 2 und 3), `PREREG_v33_window.md` par.2a (Vorschlag 4).

## par.1 WARUM

**Jede Generation trainiert genau EINEN Arm mit EINEM Trainings-Seed**, und der Sprung, den Tor 1
misst, enthaelt damit das Glueck oder Pech dieses Seeds. CLAUDE.md haelt fest, dass der Seed die
Metrik 4- bis 6-mal staerker bewegt als jeder Knopf. **Ob das auch fuer den TRAININGS-Seed bei
Warmstart gilt, ist hier nicht belegt** -- die CLAUDE.md-Zahl steht im Kontext der Arena-Streuung.
Genau das misst par.3.

**Was der Seed bei Warmstart ueberhaupt aendert** (am Code geprueft 2026-09-25): `train.py --seed`
setzt `torch.manual_seed` und `random.seed` (`train.py:1578`) -- Initialisierung und
Batch-Reihenfolge; beim Warmstart bleibt die Batch-Reihenfolge (plus Dropout, falls aktiv). Die
**Val-Aufteilung haengt NICHT daran**: sie zieht mit festem `random.Random(20260707)`
(`train.py:1430`). Arme mit verschiedenem Seed sehen also exakt dieselben Trainings- und
Val-Dateien. Der Vergleich ist in diesem Punkt sauber.

## par.2 DER GEGENEINWAND, gleich mit

**Auswahl ueberschaetzt den Sieger (Winner's Curse).** Wer den besten von drei Armen nach einer
verrauschten Messung nimmt, misst an genau diesem Arm einen zu hohen Sprung. Darum trennt par.3
die AUSWAHL von der BEWERTUNG: das Verdikt faellt auf frischen Seeds.

**Auflosung:** ein Tor-1-Seed mit 200 Paaren hat 40 Bloecke; bei der v32-Block-sd von 0,1605 liegt
der Standardfehler des Anteils bei rund **2,5 Prozentpunkten** je Arm, der einer DIFFERENZ zweier
Arme bei rund 3,6 (Herleitung, nicht gemessen). Nur Seed-Effekte in dieser Groessenordnung sind
ueberhaupt aufloesbar -- kleinere wuerden von der Auswahl ohnehin nicht getroffen.

## par.3 DESIGN (ab v34)

1. **Drei Arme** `v34-b01`, `-b02`, `-b03`: dasselbe Fenster, derselbe Monolith, dasselbe Rezept,
   derselbe Warmstart. **Einziger Unterschied `train.py --seed`**: Fensterseed, +1, +2. Kosten:
   zwei Trainings mehr (v32: 63 min je Training).
2. **Offline, fuer alle drei:** die gegen die Arena validierten Orakel-Metriken
   (`prior_mass_on_oracle_top3`, `kendall_tau_policy_vs_oracle_q`; `tools/oracle_metrics.py`) und
   rho(r) des Value-Kopfs (`tools/probes/value_head_reliability_probe.py`). **Vorbehalt:** die
   Orakel-Metriken standen 7/7 fuer GENERATIONEN-Vergleiche, aber 0/1 als Architektur-Praediktor
   (`PREREG_2d_encoder.md`, Stand 2026-08-08); fuer Geschwister-Arme sind sie UNGEPRUEFT.
3. **Eine gemeinsame Tor-1-Runde:** alle drei Arme gegen den Champion auf DEMSELBEN Seed A, 200
   Paare. Dieselben Partie-Seeds je Block machen die drei Arme blockweise GEPAART.
4. **Auswahl:** der Arm mit dem hoechsten Block-z auf Seed A.
5. **Verdikt fuer den Ausgewaehlten auf zwei FRISCHEN Seeds** (plus Stufenregel,
   `PREREG_v33_window.md` par.2a, falls sie dann Regel ist). Seed A zaehlt fuer das Verdikt NICHT.

**Kosten gegen heute:** heute 1 Training + 2 Tor-1-Seeds. Nach par.3: 3 Trainings + 3 Seed-A-Laeufe
+ 2 frische Seeds, also DREI Tor-1-Laeufe mehr -- rund **+2,1 h Training und +6,0 h Tor 1** je
Generation (Herleitung aus v32: 63 min je Training, 7.251 s je Tor-1-Seed). Das ist ein einmaliger Preis fuer die Antwort; siehe
par.4 fuer den billigen Dauerbetrieb.

## par.4 LESEREGEL, VORAB

**A -- Traegt der Trainings-Seed Staerke?** Friedman-Test ueber die 40 gemeinsamen Bloecke von
Seed A (je Block die drei Anteile der Arme; gepaart, weil die Bloecke dieselben Partie-Seeds
tragen). **p < 0,05: der Seed ist ein Hebel.** Sonst: die Arme sind in dieser Aufloesung
gleich stark; die Auswahl lohnt nicht, und ab v35 wird wieder EIN Arm trainiert.

**B -- Sortiert die Offline-Metrik die Arme richtig?** Stimmt die Rangfolge nach Orakel-Metrik
bzw. rho(r) mit der Rangfolge nach Seed A ueberein, ist eine billige Vorauswahl moeglich: dann
kuenftig drei Trainings, Auswahl OFFLINE, Tor 1 nur fuer den Besten -- Mehrkosten nur die zwei
Trainings. Stimmt sie nicht, ist die Vorauswahl nur ueber die Arena zu haben, und A entscheidet,
ob sich das lohnt. **Mit drei Armen ist B nur ein Anhaltspunkt** (eine von sechs Rangfolgen
stimmt per Zufall); belastbar wird es erst ueber mehrere Generationen.

**Zu bauen:** der Friedman-Test ueber die Blockanteile (die Blockanteile liefert
`tools/gating_block_z.py`). Zu pruefen VOR dem Einsatz: ob drei gleichzeitige Tor-1-Laeufe
gegen denselben Champion sequenziell laufen muessen (Exklusivitaet: ja, CLAUDE.md).

## par.5 ERGEBNISSE (noch leer)

## par.6 ZURUECKGEZOGEN (2026-09-25, am Tag der Anlage)

**Nutzer:** *"Mehrkosten sind kritisch abzuwaegen. In +6h kann ich mehr als 4000 self plays fahren.
... Stelle sicher dass du nichts faehrst was nicht schon bereits getestet wurde. Und ja wir haben
bereits viel getestet."*

Nachgeprueft, bevor irgendetwas lief -- und die Pruefung haette VOR dem Vorschlag stehen muessen:

* **Seed-Sweep 2026-07-28** (`archive/history.md` ab Z.5848, `tools/train_seed_sweep.py`): 4 Arme x
  6 Seeds, gepaart; schon damals wurde fuer v18 der beste Seed ausgewaehlt (Z.6331).
* **Nutzer-Entscheid 2026-09-10** (`archive/history.md` Z.17879): Trainings-Seed "variabel je
  Generation, gleich innerhalb einer Generation" (`docs/generation_loop.md`). Seed-Arme innerhalb
  EINER Generation widersprechen dem direkt.
* **Kosten gegen den belegten Hebel:** +2,1 h Training und +6,0 h Tor 1 je Generation entsprechen
  mehr als 4.000 zusaetzlichen Self-Play-Partien (v32: 4.000 Partien in rund 4,5 h). Mehr Korpus
  ist in Orakel UND Arena belegt (`PREREG_corpus_dose.md`: 479:321, p < 0,0001) -- die Seed-Auswahl
  nicht.
