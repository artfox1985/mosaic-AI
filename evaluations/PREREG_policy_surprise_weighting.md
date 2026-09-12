<!-- STATUS: ENTSCHIEDEN | Frage: Bringt es etwas, Trainings-Stichproben nach der Ueberraschung des Policy-Ziels zu gewichten (KL Ziel gegen Netz)? | Beleg: NEIN, zweimal. alpha 0,5 ohne Tor: v23-b03 negativ (par.9). Mit Sicherheits-Tor 0,5 (v24-b05) gegen das einfaktorielle Gegenstueck v24-b04: 97:103, SPRT H0 nach 100 Paaren, McNemar p 0,78, gepaarte Differenz -0,06 [-0,35; +0,23], Punkte 42,9 gegen 44,2 (par.12, 2026-09-12). Die Gewichtung bleibt aus (Default 0). -->

# Vorregistrierung: Policy-Surprise-Weighting

**ENTWURF 2026-08-27 aus dem Recherche-Abgleich. Nutzer-Entscheid ueber den
Bau offen, nichts gebaut.** Diese Datei registriert die Idee, den Zuschnitt
und das Entscheidungsmass, damit beides vor und nicht nach einer Messung
feststeht.

## par.1 Die Idee

Trainings-Stichproben werden im Policy-Verlust nach der **Ueberraschung** ihres
Ziels gewichtet: wie weit weicht das Policy-Ziel vom Prior ab, den das Netz an
derselben Stellung selbst vorschlaegt? Formal die KL-Divergenz
`KL(Prior || Ziel)` je Stichprobe, als Gewicht in den Policy-Verlust.

Die Begruendung der Literatur ist Dateneffizienz: Stellungen, an denen das Netz
das Ziel ohnehin schon trifft, tragen wenig Gradient, kosten aber vollen
Kapazitaets- und Rechenanteil. Stellungen, an denen Prior und Ziel
auseinanderlaufen, sind die, an denen etwas zu lernen ist.

**Quellen, beide im Repo:**

* `RESEARCH_alphazero_improvements_2026-08-01.md`, Fund 7 -- "Samples mit
  ueberraschendem Policy-Target uebergewichten; temperierter Zusatz-Policy-Head;
  optimistischer Policy-Head (40-90 Elo bei KataGo)".
* `RESEARCH_plate_intent_external_2026-08-22.md`, F2.4 (weitere belegte
  Eingriffe an derselben Stelle) und F5, Punkt 5 ("Optimistic-Policy-Kopf plus
  Policy-Surprise-Weighting").

## par.2 Warum JETZT -- und warum die alte Abwertung nicht mehr bindet

Fund 7 traegt in der Recherche die Note **NIEDRIG-MITTEL**, und die Begruendung
steht woertlich dort: "Alles Policy-Hebel -- 2x2-Attribution zeigt: bei 400
Sims traegt der Value-Head die Staerke; Policy-Verbesserungen ohne
Value-Verbesserung enden im Arena-Gleichstand."

Die Abwertung ist korrekt fuer die Aera, aus der sie stammt
([[project_hybrid_head_attribution]]): dort waren die Policy-Ziele
NETZ-Besuchsverteilungen, das Netz lernte also seine eigene, leicht
verbesserte Meinung nach. Eine bessere Anpassung an das eigene Echo ist
plausibel staerkefrei.

**In v22 ist die Lage anders, und das ist der ganze Punkt dieser
Registrierung.** Die Policy-Ziele stammen aus dem hv2-Lehrer, und der
Split-Test in `PREREG_v22_window.md` par.4f hat gemessen, dass der
**Spaltenbau ueber das DRAFTING transportiert wird**: die Huelle allein im
Drafting bringt 0,756 volle Spalten gegen 0,044 der Kontrolle (Delta +0,713,
t=10,29), waehrend das Routing allein exakt nichts bringt (0,113 gegen 0,113).
Der Drafting-Kanal ist der Policy-Kopf. Die Policy ist in dieser Generation
also nicht ein Nebenkanal neben dem Value-Kopf, sondern **der Kanal, ueber den
die einzige neue Faehigkeit ueberhaupt ins Netz kommt**.

**Als Herleitung markiert, nicht gemessen:** genau deshalb sollten die
Lehrer-Vorzugszuege die ueberraschendsten Stichproben des Korpus sein -- ein
frisch initialisiertes Netz hat keinen Prior auf Spaltenbau. Ein Gewicht, das
KL(Prior gegen Ziel) folgt, wuerde die Kapazitaet dorthin lenken. Ob das
stimmt, ist Teil der Messung und nicht ihre Voraussetzung.

## par.3 Zuschnitt, absichtlich klein

* **Ort:** `train.py`, Policy-Verlust. Dort steht bereits eine
  Maskenrechnung im Ownership-Zweig (`own_loss = (own_bce * own_m).sum() /
  own_m.sum()`), die Bauform ist also im Haus.
* **KEIN Engine-Eingriff.** Der Prior wird im Training gerechnet, nicht in der
  Suche. Damit ist der Arm label-neutral, erzeugungs-neutral und ohne
  Paritaets-Gate an der Engine fahrbar.
* **Kein Neu-Erzeugen, kein Neu-Labeln.** Derselbe Korpus, dasselbe Fenster.
* **Cache:** die Gewichtung aendert den Verlust, nicht die Zieldaten -- der
  Fenster-Cache bleibt gueltig. (Zu pruefen beim Bau: ob die
  Gewichts-Berechnung Zusatzfelder braucht; braucht sie welche, gehoert eine
  Cache-Key-Komponente dazu, gleiche Auflage wie bei Arm K der Lehrer-Prereg.)

**Offen und ausdruecklich NICHT hier entschieden:** die Form des Gewichts
(linear in KL, gedeckelt, temperiert), die Normierung ueber den Batch, und ob
der optimistische Policy-Kopf aus derselben Quelle mitgenommen wird. Das sind
eigene Entscheide beim Bau.

## par.3a DIE FORM, AUSGEARBEITET (Nutzer-Auftrag 2026-08-31)

par.3 hatte Form, Normierung und Reichweite ausdruecklich offen gelassen.
Hier werden sie entschieden -- vor dem Bau, damit nichts nachtraeglich passend
gemacht wird.

### (a) Was "Ueberraschung" genau ist -- und warum sie NICHTS kostet

Der Policy-Verlust ist bereits die Kreuzentropie je Sample
(train.py:487): `per_sample_ce = -sum(target * log_softmax(logits))`. Es gilt

```
CE(target, netz) = H(target) + KL(target || netz)
```

also **`kl_i = per_sample_ce_i - H(target_i)`**. Die Zielentropie ist eine
reine Funktion des gespeicherten Ziels und in derselben Schleife
auszurechnen. **Folge: der Arm braucht KEIN zusaetzliches Feld** -- damit
entfaellt auch die Cache-Key-Auflage, die par.3 vorsorglich verlangt hat, und
alle vorhandenen Bloecke bleiben gueltig.

Gemessen wird die Ueberraschung des LAUFENDEN Netzes, nicht die eines
eingefrorenen Priors. Das ist bewusst: der Arm soll Stichproben
uebergewichten, an denen das Netz JETZT danebenliegt.

### (b) Die Gewichtsformel

```
kl      = clamp(per_sample_ce - H(target), min=0)        # Float-Rauschen abfangen
raw     = (kl / mean_valid(kl).clamp(min=1e-6)) ** alpha
w_surp  = clamp(raw, 0.25, 4.0)
w_surp  = w_surp / mean_valid(w_surp)                    # Mittel 1 ueber gueltige Samples
w       = pol_w * rw * w_surp                            # bestehende Masken bleiben vorne
```

Vier Festlegungen, jede mit Grund:

1. **`.detach()` auf `w_surp`** -- PFLICHT. Ohne das flösse der Gradient durch
   das Gewicht, und das Netz koennte den Verlust senken, indem es das Gewicht
   dort drueckt, wo die CE hoch ist. Das waere eine Abkuerzung statt Lernen.
2. **Normierung auf Mittel 1** ueber die gueltigen Samples. Sonst aendert die
   Gewichtung die Loss-SKALA und damit die effektive Lernrate -- der Arm waere
   mit einem LR-Wechsel konfundiert, und genau solche Konfundierungen hat
   diese Kampagne mehrfach teuer bezahlt.
3. **Kappung auf [0,25; 4,0]**. Ein einzelnes Sample mit absurd hoher KL (z.B.
   ein verrauschtes Ziel) darf keinen Batch dominieren. Die Grenzen sind
   GESETZT, nicht gemessen -- als solche markiert.
4. **`alpha = 0,5` fuer den ERSTEN Arm**, nicht 1,0. Begruendung ist die in
   par.6 registrierte Grundrate: Policy-seitige Eingriffe haben hier
   wiederholt Offline-Masse bewegt und die Arena nicht. Eine milde
   Temperierung testet die Richtung, ohne Label-Rauschen voll durchzureichen.
   `alpha = 0` ist exakt das Bestandsverhalten und damit der Kontrollarm.

### (c) Reichweite: NUR der Haupt-Policy-Verlust

Nicht auf den Ranking-Loss, nicht auf den optimistischen Policy-Kopf (die
offene Frage aus par.3 wird damit mit NEIN beantwortet), nicht auf Value,
Punkte oder Ownership. Ein Arm, ein Faktor.

### (d) Der Kontrollarm existiert bereits

Faehrt b03 dasselbe Rezept wie **v23-b01** (Warmstart von b05, gleiches
Fenster, gleiche Flags) und unterscheidet sich NUR durch `alpha`, dann ist
b01 der Kontrollarm -- ohne einen zusaetzlichen Lauf. Genau dafuer wurde b01
mit festem Val-Pool und festem Seed gefahren.

### (e) Was NICHT mitentschieden ist

Eine alpha-LEITER. Mehr als ein Wert waere ein Sweep und braucht nach par.5
eine eigene Registrierung des Auswahlkriteriums -- der dort stehende
Waechter gegen Selbstbestaetigung verbietet, alpha an der Metrik zu drehen,
die den Arm beurteilt.

**Knopf:** `--surprise-alpha` (Default 0,0 = bestandsidentisch), Wert im
Trainings-Manifest wie `moon_loss_weight`.

## par.4 Frist

**Trainingsstart des v22-Kaltstarts.** Danach ist der Arm nicht verloren, aber
er wird zum **v22b**-Retrain auf demselben Korpus -- also ein zweiter
Trainingslauf statt einer Variante im ersten. Das ist kein Ausschlussgrund; es
ist der Preis, und er gehoert vor dem Entscheid genannt.

## par.4a BESTAETIGT 2026-08-31: der Arm ist v23-b03

Nutzer-Zuschnitt des v23-Zyklus (im selben Zug wie der Kaltstart-Arm,
`PREREG_capacity_sim_frontier.md` par.9): **b01 Warmstart aus den Self-Plays,
b02 Kaltstart, b03 Ueberraschungs-Gewichtung.** Damit ist die par.8-Empfehlung
angenommen und der Platz im Zyklus vergeben; par.4 ("Frist: Trainingsstart des
v22-Kaltstarts") ist erledigt -- der Arm ist nicht verfallen, er ist
verschoben und benannt.

Was das an Arbeit bedeutet: der Zuschnitt aus par.3 (Loss-Gewichtung in
train.py, kein Engine-Eingriff) ist weiterhin UNGEBAUT. Er kann gebaut
werden, waehrend b01/b02 rechnen -- der Bau ist reine Python-Arbeit am
Trainer, und das Entscheidungsmass (par.5) braucht ohnehin erst den
fertigen b01/b02-Vergleich als Bezug.

## par.5 Entscheidungsmass, VORAB festgelegt

**Primaer: die beiden validierten Orakelmetriken.**
`prior_mass_on_oracle_top3` und `kendall_tau` sagen die Arena in diesem Projekt
7/7 richtig voraus ([[project_oracle_metrics_validated]]) -- und sie sind, im
Unterschied zu `policy_top3`, gerade fuer die Policy-Seite validiert
(`policy_top3` zeigte 6/6 auf den VERLIERER).

**Bei Gleichstand: die Arena**, gepaart, Block-Ebene
([[feedback_arena_block_correlation]]).

**Ausdruecklich NICHT das Entscheidungsmass:** `val_combined` (bei
unterschiedlichen Epochenbudgets ungueltig,
[[feedback_preregister_decision_metric]]) und `policy_top3`.

**Waechter gegen die Selbstbestaetigung:** die Gewichts-Parameter duerfen NICHT
an der Metrik getunt werden, an der der Arm beurteilt wird. Wird die Form des
Gewichts variiert, ist das ein Sweep und braucht eine eigene Registrierung des
Auswahlkriteriums.

## par.6 Registriertes Risiko

Die Grundrate spricht nicht fuer den Arm: Policy-seitige Eingriffe haben in
diesem Projekt wiederholt die Offline-Masse bewegt und die Arena nicht
([[project_2d_encoder_phase2_result]]: Policy 6/6 besser, Staerke 416:384,
p=0,30). Wer den Arm faehrt, sollte das vorher wissen. Der Unterschied, auf den
diese Registrierung setzt, ist par.2 -- und wenn der Arm negativ ausfaellt,
ist DAS der Befund: dann traegt auch der Transportkanal-Zuschnitt die
Policy-Hebel nicht.

## par.8 Zeitpunkt (Nutzer-Frage 2026-08-28, Empfehlung des Koordinators, Entscheid offen)

Nutzer: *"die frage ist ob wir das schon bei v22 machen, oder erst bei echten
netz self plays."* Empfehlung: **NICHT im v22-Erstlauf** (v22-b01/b02). Die
Kampagne traegt bereits vier neue Faktoren gleichzeitig (Lehrerkorpus,
Traeger-Arm B, Ownership-Gewicht, neue Eingaben), und der w0-Kontrollarm
kontrolliert genau EINE Achse -- ein fuenfter Faktor waere unzuordenbar.
Stattdessen zwei benannte Zeitfenster:

1. **Als v22-bNN-Folgearm**, falls das Spalten-Tor (par.3b.2 der
   Lehrer-Prereg) zeigt, dass der Lehrer-Transfer SCHWACH ankommt -- genau
   dafuer ist dieser Hebel gebaut (seltene Bauzuege uebergewichten). Billig:
   gleicher Korpus, gleicher Cache, ein Loss-Knopf.
2. **Beim v23-Training** mit echten Netz-Self-Play-Zielen, wo die klassische
   Form (Suchverteilung gegen Prior) ohne Sonderfall gilt.

Im v22-Erstlauf ist der Knopf damit ausdruecklich AUS.

## par.9 GEBAUT UND GEMESSEN: `v23-b03`, alpha 0,5 (2026-09-01)

**Der Arm lief in der Nacht auf den 2026-09-01** und ist gegen die Kontrolle
`v23-b01` EINFAKTORIELL -- der Manifest-Diff der beiden `cli_args` zeigt genau
zwei Unterschiede: `name` und `surprise_alpha: None -> 0.5`.

| | Wert |
| --- | --- |
| Laufzeit | 12.948 s (3,60 h), Datenaufbau nur 45,6 s (Fenster-Cache-Treffer) |
| Epochen / Samples | 12 / 4,72 Mio |
| val_combined | 0,5202 (E1) bis 0,5293 (E11/E12) -- ausdruecklich NICHT das Entscheidungsmass (par.5) |

**Entscheidungsmass nach par.5, die beiden validierten Orakelmetriken**
(n=952 Zustaende, `frozen_v1`, Orakel aus v18):

| Metrik | v23-b03 | v23-b01 (Kontrolle) | Differenz |
| --- | --- | --- | --- |
| `prior_mass_on_oracle_top3` | 0,5244 | **0,5308** | -0,0064 fuer b03 |
| `kendall_tau` | **0,2300** | 0,2296 | +0,0004 fuer b03 |

**Gleichstand, und zwar weit unter der Aufloesung** -- eine Metrik zeigt
minimal auf die Kontrolle, die andere auf den Arm. Bezeichnend fuer die Grobheit
des Satzes an dieser Stelle: `prior_recall_at_16` ist bei BEIDEN Netzen exakt
0,8750.

**Nach par.5 entscheidet dann die Arena** (2 x 80 Partien, getauschte Rollen,
gleicher Seed 20260990, `paired_arena_env_ab`):

```
b03 75 : 85 b01   (37:43 und 38:42 in den beiden Richtungen)
Paare: b03 beide 13, geteilt 49, b01 beide 18
Vorzeichentest auf 31 informativen Paaren: p = 0,47
Punkte 45,70 gegen 49,02, Margin -3,32
```

**Standard-Kennzahlen, nachgetragen 2026-09-01** (die Erstfassung trug nur
die Siegzahl; Quelle `paired_arena_env_surprise_b03_first.json` /
`_b01_first.json`, Spalten per `tools/probes/arena_column_probe.py`,
Artefakte `columns_surprise_*.json`, 160 von 160 nachspielbar):

| Kennzahl | b03 | b01 |
| --- | --- | --- |
| volle Spalten je Seite, b03 zuerst | 0,5750 | **0,7875** |
| volle Spalten je Seite, b01 zuerst | 0,4250 | **0,4750** |
| volle Spalten gepoolt (n=160) | 0,500 | **0,631** |
| lange Reihen begonnen / vollendet je Seite | 4,19 / 2,83 | 4,30 / 2,96 |
| Strafleiste (`total_floor`) je Seite | 10,12 | 9,28 |

Punkte je Kriterium fehlen (Werkzeug-Format, siehe reanalyze par.A1). b03
baut in beiden Richtungen WENIGER Spalten als die Kontrolle (-0,13 gepoolt)
und macht mehr Strafpunkte -- das Verdikt "traegt nicht" wird dadurch
gestuetzt, nicht nur die Siegzahl.

**VERDIKT: der Arm traegt nicht.** Kein Vorteil offline, in der Arena
zurueck. Die Marge ist dieselbe, die b02 in dieselbe Richtung und b05 in die
Gegenrichtung erzeugt hat -- bei n=160 die Rauschgrenze des Instruments; ein
Beleg fuer SCHADEN ist es also ebenso wenig.

**Was mit dem Knopf geschieht:** `--surprise-alpha` bleibt gebaut und
dokumentiert, Default 0 (aus). Er wird nicht ins Standardrezept uebernommen.

**Was NICHT geprueft wurde:** andere alpha-Werte. Eine Dosis-Reihe waere ein
eigener Zuschnitt und braucht ihre eigene Registrierung -- nach dieser Messung
ohne benannten Nutzniesser.

## par.10 WIEDERVORLAGE als v24-Arm `v24-b05`: Ueberraschung nur bei sicherer Suche (Nutzer 2026-09-05, 12:19: "Dann takte den Arm ein")

**Anlass.** Nutzer-Frage: "Die Zuege, in denen Suche und Netz auseinanderdriften,
sind ja die echten Geschenke?" Am Code: der Policy-Verlust ist die
Kreuzentropie zwischen dem Gumbel-completed-Q-Ziel (geschaerft, Exponent 2)
und den maskierten Logits; sie zerfaellt in Zielentropie plus KL(Ziel gegen
Netz), die Abweichung traegt also schon ohne Zusatzgewicht den groessten
Gradienten. Die explizite Verstaerkung (par.3a, alpha 0,5) hat in v23-b03
nichts gebracht und Spalten gekostet (par.9). Hypothese (unbelegt): bei 100
Sims mit Wurzelrauschen liegen die groessten Abweichungen in derselben Ecke
wie die verrauschtesten Ziele; die Gewichtung hebt Geschenk und Laerm
zugleich.

**Der Arm.** Dieselbe Gewichtung wie par.3a, aber nur dort, wo die Suche
sicher ist: Stichproben, deren (geschaerftes) Policy-Ziel eine Top-1-
Wahrscheinlichkeit >= 0,5 hat, bekommen `(KL / Mittel)^alpha` (gekappt auf
[0,25; 4,0]); alle anderen behalten Gewicht 1; danach die bestehende
Normierung auf Mittel 1 (Loss-Skala konstant). Schalter
`--surprise-confidence-min` (train.py, Default 0,0 = kein Tor = bitidentisch
zu par.3a; zusammen mit alpha 0,0 bitidentisch zum Bestand), im
Trainingsmanifest als `cli_args.surprise_confidence_min`. Kein neues Feld,
keine Cache-Komponente (Top-1 des Ziels ist eine Funktion des gespeicherten
Ziels). Parameter: alpha 0,5 (wie v23-b03, damit der Unterschied allein das
Tor ist), Schwelle 0,5 (nach Schaerfung Exponent 2 entspricht das einem
rohen Top-1 von rund 0,71 bei zwei Kandidaten; Herleitung, nicht gemessen).

**Zuschnitt.** Rezept, Fenster, Monolith und `INPUT_SIZE` wie `v24-b04`
(744; der Python-Encoder des Sicht-Arms ist zu diesem Zeitpunkt der
Bestand). **Einziger Faktor gegen b04: das gegatete Gewicht.** Zweiter Bezug
b01 (mit b04 als Zwischenglied). Kette `tools/night_v24_b05_chain.sh`
(Training nach b04, GPU), Abnahme `tools/night_v24_acceptance_chain.sh b05`
plus Tor 1/2a ohne Knopf (`PREREG_v24_window.md` par.9b).

**Entscheidungsmass** wie par.7 (Orakelmetriken, Tor 1, Tor 2a/2b);
zusaetzlich der Anteil gegateter Stichproben je Epoche (aus dem Trainingslog
nachzutragen: wie viele Samples ueber der Schwelle lagen). Liegt er unter 10
Prozent, kann der Arm nichts zeigen und wird als "Tor zu eng" registriert,
nicht als Nullbefund.

## par.11 NACHTRAG 2026-09-09: der Arm v24-b05 ist gefahren, sein Verdikt steht woanders

`v24-b05` wurde in der Nacht 2026-09-05/06 trainiert und abgenommen
(`models/manifest_train_v24-b05_20260905_205133.json`: `surprise_alpha 0,5`,
`surprise_confidence_min 0,5`; der cli_args-Diff gegen
`manifest_train_v24-b04_20260905_165948.json` zeigt genau diese zwei Felder plus den
Namen, die Einfaktorialitaet ist also belegt). Die Ergebnisse stehen NICHT hier, sondern
in `PREREG_v24_window.md` par.9 (Tabellenzeile `v24-b05`): Tor 2a ohne Knopf 0,4825 und
mit Knopf 0,4975 volle Spalten je Seite (200 Partien @400 argmax), Tor 1 ohne Knopf 66:34
(SPRT) und repliziert 112:78, mit Knopf 219:181 ohne Entscheid; Generatorwahl in par.9c.

**Was fehlt und diesen Strang offen haelt:** der einzige saubere Vergleich fuer die
Ueberraschungsgewichtung ist b05 GEGEN b04 (gleiches Rezept, ein Faktor). Diese Kante ist
nirgends registriert, und der in par.10 verlangte Anteil gegateter Stichproben je Epoche
wurde nie aus dem Trainingslog nachgetragen. Beides waere aus den vorhandenen Modellen
und Logs nachholbar, ohne neues Training. Bis dahin: kein Verdikt.

**Eingetaktet 2026-09-11 (Nutzer):** die fehlende Kante `v24-b05` gegen `v24-b04` wird als
Schritt 6 des v28-Programms gefahren (`PREREG_v28_window.md` par.8): beide Modelle aus den
restic-Snapshots `run:v24-b05` / `run:v24-b04` in einen Sammelordner zurueckgeholt, gepaartes
Gating mit `models/k3v_off.spec.json` auf beiden Seiten (Fassung ohne Knopf wie bei den
v24-Abnahmen, `PREREG_v24_window.md` par.9), 200 Paare,
Blockgroesse 5, `--log-games`. Verdikt danach hier in par.12: traegt die Gewichtung mit
Sicherheits-Tor (Punktschaetzer und Spalten), oder nicht.

## par.12 VERDIKT 2026-09-12: die Kante b05 gegen b04 ist gefahren, sie traegt nichts

Gefahren als Schritt 6 des v28-Programms (`tools/night_surprise_edge.sh`, 06:45-07:31, 2.731 s,
10 Threads, Blockgroesse 5, `--log-games`, exklusiv; Artefakt
`paired_gating_v24-b05_vs_v24-b04_s45.json`, Seed 20261045). Beide Modelle aus den restic-
Snapshots `run:v24-b05` (73b5c104) und `run:v24-b04` (c6877ec9) nach `models/restored_v24/`
(sha256 469a1bfd... / 4109630f...), beide Seiten `models/k3v_off.spec.json`, @400.

**v24-b05 (surprise_alpha 0,5, Tor 0,5) gegen v24-b04 (ohne): 97:103, SPRT-Entscheid H0 nach
100 Paaren (LLR -3,43), McNemar p=0,784, gepaarte Differenz -0,06 [-0,347; +0,227]** (47 Splits,
25 A-Sweeps, 28 B-Sweeps); Punkte 42,9 gegen 44,2 (n=200 je Seite, Einheit Punkte je Partie).
Lesart nach par.10: die Gewichtung mit Sicherheits-Tor liefert keinen messbaren Vorteil, der
Punktschaetzer liegt sogar leicht unter dem Gegenstueck; zusammen mit dem negativen
Befund ohne Tor (par.9, v23-b03) ist der Hebel zweimal ohne Wirkung. **ENTSCHIEDEN: die
Ueberraschungsgewichtung bleibt aus** (`--surprise-alpha` Default 0, Knopf bleibt als Bestand
im Trainer, kein Arm mehr).

Randbedingungen, damit die Zahl nicht missdeutet wird: (1) beide 744er-Modelle liefen auf dem
755er-Wheel (Kuerzung auf Modellbreite, `net.rs`), beide Seiten gleich, ein symmetrischer
Umstand; (2) die Spec ohne Huelle (k3v_off) erklaert das niedrige Punkteniveau (42-44 gegen
50-54 der Champion-Kanten), auch symmetrisch; (3) die Kante liegt in KEINEM Leitersegment
(beide Knoten haben im Segment 2 keine Anker-Verbindung) und wird deshalb NICHT ins Elo-
Register eingetragen, sie ist ein Faktor-Vergleich, keine Leiterposition. Die
Standard-Kennzahlen aus den Logs (Spalten, Reihen, Strafleiste, Plattenpunkte) folgen als
Nachtrag, sobald die Maschine frei ist (Replay-Sonde nicht neben dem laufenden C2-Instrument).

**Nachtrag Standard-Kennzahlen (Replay-Sonde 2026-09-12, 12:06, exklusiv; Artefakt
`arena_columns_paired_gating_v24-b05_vs_v24-b04_s45.json`, 198 von 200 Partien replayt, 2
Divergenzen):** volle Spalten je Seite v24-b05 0,520 (+-0,103) gegen v24-b04 0,561 (+-0,107);
Teilspalten >= 4 2,07 gegen 2,20; volle Reihen 0,18 gegen 0,15; Spezialfelder belegt 1,01 gegen
1,13; Strafleiste 11,3 gegen 11,4 Punkte. Gepaart (v24-b05 minus v24-b04, 100 Paare): Sieg
-0,03 [-0,17; +0,11], Punkte -1,35 [-4,23; +1,53], Marge -2,70 [-8,46; +3,06], Platten -0,24
[-1,33; +0,86], Strafleiste -0,11. Kein Posten bewegt sich ueber sein Intervall; die Spalten
zeigen in dieselbe Richtung wie die Siege (leicht gegen die Gewichtung). Verdikt par.12
unveraendert.

