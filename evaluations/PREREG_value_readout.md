<!-- STATUS: UEBERHOLT | Frage: Verliert der Value-Kopf Information, die sein Trunk traegt -- und ist der Hebel das Kopf-Training oder mehr Value-Material? | Beleg: ZURUECKGEZOGEN am Tag der Anlage (par.6). Jeder Zweig, den die Diagnose oeffnen koennte, ist schon gefahren (eingefrorener Trunk, Nachlabeln, Kapazitaet, lambda, Punkte-Kopf); die Antwort der Kampagne auf den gedaempften Kopf ist die Huelle. Das Volumen ist ein belegter Hebel, keine Testfrage (corpus_dose, task36). Nichts gefahren. -->

# Vorregistrierung: Liest der Value-Kopf aus, was der Trunk weiss?

**Angelegt 2026-09-25** auf Nutzer-Frage *"Sonst noch Ideen um die Generationensprunge
groesser/signifikanter zu gestalten?"* und Auftrag *"Registrieren das so vor und takte es ein.
Bei Bedarf auch eigene prereg."* Diese Prereg traegt zwei der vier Vorschlaege: die
Auslese-Diagnose (Stufe 1) und das Value-Volumen (Stufe 2b). Die anderen beiden stehen in
`PREREG_v33_window.md` par.2a (Stufenregel Tor 1) und `PREREG_training_seed_arms.md`.

## par.1 WARUM: zwei Sonden, dasselbe Bild

**R4b, am 2026-09-25 zum zweiten Mal** (`PREREG_v32_window.md` par.11, gepaart gegen v31 auf
denselben 72 Zustaenden am Ende von Runde 4): eine LINEARE Auslese des 512-breiten Trunks
erreicht fuer die exakte Marge **LOO-R2 0,940** bei einer Decke von 0,983; die Koepfe des Netzes
realisieren auf der Margenskala **-2,28**. Dieselbe Sonde auf der rohen Eingabe: 0,087. Die
Information ist also im Trunk, und die Koepfe verlieren sie. Bei v31 genauso (0,940 / -2,18),
bei der v20-Aera ebenfalls (Trunk 0,912).

**R5, gepaart:** die Steigung des Value-Kopfs gegen die exakte Runde-5-Kennlinie liegt bei
**0,177** (v31: 0,146), unverzerrt waere 1,0. Der Kopf ist um rund den Faktor 6 gedaempft.

**Was das NICHT belegt:** beide Sonden stehen im ENDSPIEL (Ende Runde 4 bzw. Runde 5), und in
Runde 5 rechnet die Suche ohnehin exakt (`round5.rs`). Ob der Kopf auch im MITTELSPIEL
Information verschenkt -- dort, wo er die Suche wirklich fuehrt --, ist UNGEMESSEN. Das ist die
Frage von Stufe 1.

**Randbedingung (Nutzer 2026-09-14): keine neuen Koepfe.** Nichts hier baut einen. Die Frage ist,
ob das TRAINING des bestehenden Kopfes die Information verschenkt.

## par.2 STUFE 1: Trunk-Sonde neben dem Kopf, je Runde

**Werkzeug:** `tools/probes/value_head_reliability_probe.py` misst schon rho(r) des Value-Kopfs je
Runde auf `frozen_v3` (1.800 Zustaende, 360 je Runde), gegen Marge, Sieg und Orakel-Wurzelwert
@5000 (1.144 Labels, Runden 1-4), mit Block-Bootstrap (36 Bloecke a 10 je Runde) und der
95-Prozent-Spanne der DIFFERENZ zweier Ziehungen DESSELBEN Netzes als Rauschboden. **Zu bauen:**
daneben eine Trunk-Sonde -- das 512-breite `fusion`-Embedding derselben Zustaende (Extraktion
wie in `tools/r4b_zone_probe.py`), Ridge-Regression auf dieselben Ziele, Kreuzvalidierung
BLOCKWEISE (Leave-one-block-out ueber die 36 Bloecke je Runde, damit korrelierte Zustaende nicht
zwischen Anpassung und Pruefung geteilt werden).

**Modell:** `v32-b01_brierbest` (Champion). **Substrat:** `frozen_v3` wie im Werkzeug.

**Messgroesse je Runde r und Ziel:** Delta(r) = Spearman(Sonde, Ziel) - Spearman(Kopf, Ziel),
beide auf denselben ausgehaltenen Bloecken.

**Kriterium, VORAB festgelegt:**

* **Auslese-Verlust in Runde r:** Delta(r) liegt ueber der oberen Grenze der 95-Prozent-Spanne,
  die das Werkzeug fuer die Differenz zweier Ziehungen desselben Netzes ausgibt.
* **Befund "Kopf verliert im Mittelspiel":** Auslese-Verlust in mindestens ZWEI der Runden 1-4,
  fuer das Ziel Orakel-Wurzelwert (das rauschaermste der drei). Marge und Sieg werden
  berichtet, entscheiden aber nicht.
* **Sonst:** "kein nachweisbarer Verlust im Mittelspiel" -- dann ist der R4b-Befund
  endspiel-spezifisch.

**Vorbehalte, vorab benannt:** (1) Die Sonde wird auf dem Ziel angepasst, gegen das sie
gemessen wird; der Kopf auf einer Mischung (`--value-target-lambda 0,7`, WDL). Ein Delta kann
also auch aus dem ZIEL kommen, nicht nur aus Kapazitaet oder Training -- genau das trennt
Stufe 2a. (2) 1.800 Zustaende aus `frozen_v3`, einer aelteren Verteilung
(`frozen_eval_set_v3.pkl`); ein zweites Substrat ist `data/window_v32_val.txt` (147 Dateien, am
2026-09-25 vollstaendig vorhanden; nur Ergebnis-Ziele, keine Orakel-Labels) -- berichtet, nicht
entscheidend.

**Kosten:** UNGEMESSEN. Das Werkzeug nennt "Minuten" fuer die Kodierung; die Extraktion des
Embeddings kam bei R4b fuer 72 Zustaende samt Ridge auf 42,5 s. Laufzeit-Block ins Artefakt.

## par.3 WANN (eingetaktet)

Nach der v33-Erzeugung und ihren Pflichtpruefungen (`PREREG_v33_window.md` par.9), in der
Luecke VOR dem Start der v33-Kette -- die Maschine ist dann ohnehin frei, bis der Nutzer die
Kette freigibt. Der Bau der Sonde (Werkzeugerweiterung) kann vorher geschrieben werden; laufen
darf er nicht neben der Erzeugung.

## par.4 STUFE 2: der Zweig haengt am Befund von Stufe 1

**2a -- "Kopf verliert im Mittelspiel":** der Hebel ist das Training des bestehenden Kopfes.
Kandidaten, KEINER davon entschieden (Rezept-Knoepfe gehoeren dem Nutzer): `--value-target-lambda`
1,0 statt 0,7 (die b-Serie fuhr 1,0 -- laut Kampagnen-Gedaechtnis, hier NICHT nachgelesen), die
Punkte-Streckung (`--destretch-a/-b`; der Punkte-Kopf von `v31-b01` ueberschoss in R4b die
Streuung um den Faktor 2,1, sd 40,2 gegen 18,8 -- fuer `v32-b01` nicht nachgerechnet), Kopf-eigene Lernrate. Gemessen als warme
Arme auf demselben Fenster und Monolithen wie der Referenzarm, Tor 1 gegen den Champion. Vorher
die Sonde aus Stufe 1 AN DIESEN ARMEN wiederholen: sie muss den Verlust kleiner zeigen, sonst hat
der Knopf nicht getroffen, was er treffen sollte.

**2b -- "kein nachweisbarer Verlust":** der Hebel ist Material. **Task #36 (2026-08-06,
`archive/history.md` ab Z.9965):** der Value-Kopf saettigt NICHT; 202 -> 405 -> 810 Dateien
monoton in allen drei Seeds, jede Verdopplung rund 0,0012 Brier, log-linear ohne Knick.
**Vorbehalt:** gemessen in einer aelteren Encoder-Aera auf einem anderen Messset; ob es heute
noch traegt, ist die Frage des Arms. **Entwurf fuer v34:** ein Arm mit 4.000 zusaetzlichen
Schwarm-Partien im Fenster gegen den Referenzarm mit gleichem Trainings-Seed; einziger
Unterschied das Volumen. Kosten rund 4,5 h Erzeugung (v32: 4 h 34 bzw. 4 h 52 je Schwarm-Klasse)
plus ein Training. Welche Schwarm-Klasse aufgestockt wird, ist offen.

**Beides schliesst sich nicht aus.** Stufe 1 entscheidet, welcher Hebel ZUERST gezogen wird.

## par.5 ERGEBNISSE (noch leer)

## par.6 ZURUECKGEZOGEN (2026-09-25, am Tag der Anlage)

**Nutzer:** *"Die value head Thematik zieht sich bereits durch das ganze Projekt. Stelle sicher dass
du nichts faehrst was nicht schon bereits getestet wurde."* Nachgeprueft ueber die Koepfe der
Preregs: **22 entschiedene Vorregistrierungen** beruehren den Value- oder Punkte-Kopf. Fuer diese
Prereg zaehlen:

| Zweig dieser Prereg | schon gefahren | Ergebnis |
| --- | --- | --- |
| Stufe 1: liest der Kopf aus, was der Trunk traegt? | `PREREG_r4_value_calibration.md` par.21 (v20 und v31), heute v32 | Trunk traegt, Koepfe verlieren -- dreimal dasselbe Bild. Eine Mittelspiel-Fassung waere eine neue MESSFORM, aber ohne Entscheid dahinter (siehe die Zeilen darunter). |
| 2a: den Kopf allein nachtrainieren | `PREREG_frozen_trunk_head.md` | NEGATIV (2026-08-18): der eingefrorene Trunk ist die Decke, das gemeinsame Training liefert den besseren Kopf. **Berichtigt 2026-09-25:** dort wurde der OWNERSHIP-Kopf auf eingefrorenem Trunk trainiert, nicht der Value-Kopf (Zeile 1 der Prereg); fuer den Value-Kopf ist die Frage damit nur per Analogie, nicht gemessen beantwortet |
| 2a: bessere Ziele durch tieferes Labeln | `PREREG_reanalyze_label_depth.md` | NEGATIV (2026-09-03): Arena 75:85, Value-Kopf unbewegt |
| 2a: mehr Kapazitaet | `PREREG_capacity_sim_frontier.md` | geparkt (Nutzer 2026-09-02): "das Problem sitzt im Value-Kopf" |
| 2a: lambda, Punkte-Streckung, Lernrate | Lambda-Sweep (`archive/history.md` Z.7118: lambda 0,7 gegen 1,0 227:173, seither Standard), `PREREG_points_*` (vier Preregs), `PREREG_lr_schedule.md` | entschieden, im Rezept |
| die Betrags-Daempfung ueberhaupt | `PREREG_geometric_envelope.md` | beantwortet durch eine SUCHSEITIGE Korrektur, die Huelle -- Rezeptbestandteil |
| 2b: mehr Value-Material | `PREREG_task36_value_saturation.md`, `PREREG_corpus_dose.md` | BELEGT: der Value-Kopf saettigt nicht; mehr Korpus traegt in Orakel und Arena (479:321, p < 0,0001) |

**Folge:** Stufe 1 wird nicht gefahren, 2a ist erschoepft. **2b ist keine Testfrage, sondern eine
Rezeptfrage** -- wie viele Partien je Generation das Budget wert sind. Sie steht als Vorlage in
`STATUS.md` Abschnitt 6 und gehoert in par.6 der v34-Fenster-Prereg, nicht hierher.
