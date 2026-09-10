<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird das v27-Trainingsfenster zugeschnitten -- das erste VOLLSTAENDIG stationaere, und zugleich das letzte unter dem Einfrieren? | Beleg: Erzeugung durch (par.7), Tor 2a HAELT (0,777 gegen 0,737), Training v27-b01 durch (par.8), Tor 1 BESTANDEN (par.9: 59:31 SPRT, 222:178 Deckel p 0,033), Tor 2b HAELT (par.10: 1,005 gegen 0,855), PROMOTION 2026-09-10 vollstaendig (Anker 127:23, Champion-2 gegen v25-b01-Artefakt 92:58, Elo 1405 [1361, 1453] aus 790, Artefakt models/frozen_champions/v27-b01). Letzter eingefrorener Arm; das Einfrieren ist beendet. -->

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

**Kosten, gemessen an der v26-Erzeugung** (Primaerquelle sind die `laufzeit`-Bloecke der
drei Manifeste `data/manifest_v25-b01-*.json`, je 4.000 Partien bei threads 11): Nr. 1
11.077,9 s = 3,08 h (2,769 s je Partie), Nr. 2 10.161,0 s = 2,82 h (2,540 s), Nr. 3
8.837,9 s = 2,45 h (2,207 s je Identitaet) -- zusammen **30.076,8 s = 8,4 h**. Berichtigt
2026-09-09: vorher standen hier '2,62 s', '3,5 h' und 'rund 9 h', uebernommen aus
`docs/measured_runtimes.md`, wo der v25-Schaetzwert als Messung gefuehrt war. Die
v26-Laeufe waren schneller als die v25-Werte, weil der Cache-Waechter seinen Rueckstand
abgearbeitet hatte und die CPU freigab.

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

## par.7 ERZEUGUNG DURCH, TOR 2a EX POST (2026-09-10)

**Erzeugung** (Nutzer-Freigabe 2026-09-09, 21:50; `tools/night_v27_generate.sh`): alle
drei Klassen Exit 0, `selfplay_v26-b01-policy_*` 400 Dateien, `-value-tempc_*` 400,
`-value-excursion_*` 401 (4.003 Identitaeten). Laufzeit aus den Manifesten 36.912 s =
10,25 h, 23 % ueber der v26-Erzeugung bei gleicher Konfiguration
(`docs/measured_runtimes.md`, Abschnitt v27; Ursache nicht gemessen).

**Tor 2a ex post** (Praezedenz `docs/generation_loop.md`, Abschnitt Tor 2; Kette Schritt 1,
`tools/corpus_sanity_check.py`, Einheit volle Spalten je Seite, je 4.000 Partien = 8.000
Seiten, KI 95 %):

| Klasse | volle Spalten je Seite | Punkte | Strafleiste |
| --- | --- | --- | --- |
| `selfplay_v25-b01-policy_*` (Bezug, Generator v25-b01) | 0,737 +-0,017 | 44,2 | 6,41 |
| **`selfplay_v26-b01-policy_*` (Generator v26-b01)** | **0,777 +-0,017** | 45,3 | 6,25 |
| `selfplay_v26-b01-value-tempc_*` | 0,463 +-0,015 | 37,1 | 7,56 |
| `selfplay_v26-b01-value-excursion_*` (8.006 Seiten) | 0,858 +-0,018 | 47,1 | 5,57 |

**Tor 2a HAELT**: 0,777 gegen 0,737, Punktschaetzer darueber, Konfidenzintervalle getrennt
(0,760 gegen 0,754 an den Raendern). Dritte Generation in Folge mit steigender
Traeger-Kennzahl (0,637 / 0,737 / 0,777). Nebenbefund: die Ausflug-Klasse ist mit 0,858
die spaltenreichste Klasse des Fensters, die temperierte mit 0,463 die aermste; fuer die
G-2-Frage der naechsten Generation (par.2, Rolle gegen Zahl) ist das ein weiterer Punkt
auf der Seite der Ausflug-Haelfte.

**Fenster** (Kette Schritte 2 bis 6, 08:29): Traeger-Manifest 580 = 400 + 135 + 45,
G-2-Schwarm 145 aus den 400 `v24-b07-value-tempc`, `data/window_v27.txt` 2.947 Dateien
(par.1 sagte 2.946; die neue Ausflug-Klasse liefert 401 statt 400, wie in par.1
angekuendigt nicht ausgeglichen), Bloecke lagen vom Waechter vollstaendig vor,
Trainingsanteil-Schluessel `9934367b3d82`, Monolith `data/.cache_9934367b3d82.h5`.
Training `v27-b01` folgt in der Kette (Warmstart `v26-b01_brierbest`, eingefrorenes Rezept).

## par.8 TRAINING v27-b01 DURCH (2026-09-10, 08:40-10:05)

Kette Schritt 7, eingefrorenes Rezept (Warmstart `v26-b01_brierbest`, 12 Epochen, lr 5e-05
cosine, lambda 0,7, Seed 20260933), Manifest `models/manifest_train_v27-b01_20260910_084002.json`:
Laufzeit 5.116,7 s (Datenaufbau 35,4 s), Exit 0, Modell-Snapshot ins restic-Repo diesmal
erfolgreich (Marke `run:v27-b01`; der Fix vom 2026-09-09 hat gehalten, kein
`.snapshot_pending`). `_brierbest` ist **Epoche 3** (val_brier 0,1873), Plateau ab Epoche 10,
Policy-Val 0,395 am Ende.

| Arm | brierbest-Epoche | val_brier | Val-Pool |
| --- | --- | --- | --- |
| v25-b01 | 9 | 0,1912 | `^selfplay_v24-b07-` |
| v26-b01 | 10 | 0,1919 | `^selfplay_v25-` |
| v27-b01 | 3 | 0,1873 | `^selfplay_v26-` |

**Die Brier-Werte sind NICHT ueber die Arme vergleichbar** (je ein anderer Val-Pool; die
Entscheidungsmetrik ist die Arena). Auffaellig ist nur der fruehe Bestpunkt: der Value-Kopf
gewinnt auf dem v27-Fenster nach drei Epochen nichts mehr, waehrend v25/v26 bis Epoche 9/10
gingen. Ob das Saettigung des Materials oder Zufall des Val-Pools ist, entscheidet Tor 1.

**Naechste Schritte** (STATUS Abschnitt 1, Plan ab 09:00, verschoben auf nach dem Wheel-Bau
fuer die Logzeilen-Aenderung): Anker-Invarianz, Rauchtest `--log-games`, Tor 2b fuer
v26-b01 gegen v25-b01 nachholen, dann Tor 1 `v27-b01` gegen `v26-b01` mit Logs.

## par.9 TOR 1 BESTANDEN (2026-09-10, 11:38-13:24): v27-b01 gegen v26-b01

Gepaartes Gating (`tools/paired_gating.py`, beide Seiten Champion-Spec
`models/v24-b07_brierbest.spec.json`, nur das NETZ verglichen, @400, Blockgroesse 5, 10
Threads, erstmals MIT `--log-games`, damit Tor 2b aus denselben Partien kommt):

| Seed | Ergebnis | Paare | McNemar p | gepaarte Differenz [95 %-KI] | Punkte | Strafleiste | Dauer |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261034 | **59:31**, SPRT-Entscheid fuer v27-b01 (LLR +3,013) | 45 | 0,0125 | +0,62 [+0,19; +1,05] | 55,6 gegen 49,5 | 8,83 gegen 8,29 | 1.140 s |
| 20261035 (Replikation) | **222:178**, Deckel ohne SPRT-Entscheid (LLR +0,61) | 200 | 0,0334 | +0,22 [+0,03; +0,41] | 53,2 gegen 49,9 | 9,18 gegen 8,31 | 5.182 s |

Artefakte `paired_gating_v27-b01_vs_v26-b01_s34.json` / `_s35.json` (mit 90 bzw. 400
Partie-Logs). **Kein dritter Seed** (Nutzer 2026-09-10, 13:20: "Brauchst keinen dritten
seed wenn v27 positiv und kein nullentscheid ist"): beide Seeds liegen fuer v27-b01 vorn,
der volle Lauf ist fuer sich signifikant. Verzerrungsfrei ist der Deckel-Lauf allein
(222:178 = 55,5 %); der Fruehstopp-Lauf stoppte, WEIL er vorne lag, und wird nicht
gepoolt gefuehrt. Beide Kanten stehen im Elo-Register (2026-09-10).

**Was das fuer das Einfrieren heisst:** dritte Generation in Folge, in der nur das Material
rotierte, und dritte Generation in Folge mit Tor 1 fuer den neuen Arm (v25-b01 gegen v24-b07
182:118 gepoolt; v26-b01 gegen v25-b01 436:364 verzerrungsfrei; v27-b01 gegen v26-b01
222:178 verzerrungsfrei). Der Materialeffekt ist damit dreimal belegt; das Einfrieren endet
mit der Promotion dieses Arms (par.6). Tor 2b und Wertungsplatten-Punkte folgen aus den
Logs (Promotionsskript `tools/night_v27_promotion.sh`, Schritt 0).

## par.10 PROMOTIONSMESSUNGEN v27-b01 (2026-09-10, 13:27-14:48, `tools/night_v27_promotion.sh`)

**Tor 2b aus den Tor-1-Logs** (`arena_column_probe.py`, Einheit volle Spalten je Seite):

| Lauf | v27-b01 | v26-b01 | replayt / divergiert |
| --- | --- | --- | --- |
| Seed 20261034 (90 Partien) | 1,089 +-0,163 | 0,700 +-0,159 | 90 / 0 |
| **Seed 20261035 (400 Partien)** | **1,005 +-0,077** | **0,855 +-0,074** | 394 / 6 (Chip-Vollendung nicht nachspielbar, bekannte Replayer-Grenze) |

**Tor 2b HAELT** (Intervalle im vollen Lauf getrennt). Punkte 53,1 gegen 49,9, Strafleiste
9,21 gegen 8,28 (v27-b01 zahlt mehr Strafe), Reihen voll 0,147 gegen 0,150.

**Wertungsplatten-Punkte je Kriterium** (`plate_points_from_arena.py`, Mittel ueber Partien
mit aktiver Platte, Klammer = Zahl der Partien): das Werkzeug wertet EIN Brett aus und kennt
die Modellzuordnung `side_names` nicht; die Zahlen unten sind deshalb ueber BEIDE Modelle
gemischt (n = 200 Partien je Artefakt) und taugen nur als Niveau, nicht als Vergleich.
Seed 20261035: Diagonale 0,49 (81), Eckplatten 8,17 (72), Farbenreiche Reihen 0,53 (75),
Horizontale Reihen 0,62 (73), Mehrfarbige Felder 2,26 (70), Spezialfelder -10,54 (74),
Vertikale Reihen 5,82 (89), Aeussere Felder 10,64 (66). Zum Vergleich s33 (v26 gegen v25):
Spezialfelder -10,57, Vertikale 5,27, Aeussere 10,71. **Offen:** das Werkzeug um
`side_names` erweitern, sonst bleibt Standard-Kennzahl 4 je Modell unmessbar.

**Anker-Kante** (`anchor_arena.py`, n = 150 fest, 6 Worker, Cross-Aera, 1.333 s):
**127:23**, exakt wie v26-b01 (v25-b01 und v24-b07: 126:24). Gesaettigt wie erwartet.
Kennzahlen v27-b01 gegen den Anker: volle Spalten je Partie **1,373** (v26-b01 1,267,
v25-b01 1,307), Punkte 57,1, Margin +17,5, Strafpunkte -18,0.

**Champion-2-Kante gegen das EINGEFRORENE Artefakt v25-b01** (`frozen_referee_match.py`,
dessen Wheel, Handshake gruen 20b442a8164f748d, Golden-Selbsttest 10/10 ohne Abweichung,
150 Partien, 6 Prozesse, Seed-Basis 20261050, 2.578 s): **92:58**.

**sigma/Prior-Balance** (`gumbel_scale_calibration.py`, 300 Zustaende, n_used 233):
Gesamt **2,161** (v26-b01 2,270, v25-b01 2,792), je Runde 1,76 / 2,45 / 1,84 / **2,88**.
Die Familie bleibt zu (Schwelle 3). Der Runde-4-Ausreisser von v26-b01 (8,537) ist bei
v27-b01 verschwunden; die Nachschau aus STATUS ist damit erledigt.

**Anzeige-Kalibrierung** (`platt_fit.py`, je 1.440 Zustaende): frozen_v3 (Anzeige)
A -0,0476, B 0,6853, Brier 0,22379 (v26-b01: -0,0732 / 0,6736 / 0,22486); frozen_v1
(Trend) A +0,4010, B 0,6335, Brier 0,25135. In `server.py` eingetragen.

Elo-Kanten aller vier Messungen im Register; Leiterstand nach dem Report in STATUS.
