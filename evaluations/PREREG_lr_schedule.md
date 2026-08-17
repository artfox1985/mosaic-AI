<!-- STATUS: OFFEN | Frage: Welche Einstellung fuer den adaptiven Plateau-Scheduler taugt als kuenftiges Warm-Start-Rezept -- greift factor 0.5 / patience 2 ueberhaupt, bevor das Early Stopping feuert? | Beleg: **REGISTRIERT 2026-08-17 vor dem Lauf.** EIN Arm, v21-b21 (Warm Start wie b18, nur plateau statt cosine) -- ausdruecklich eine PARAMETERSUCHE und kein Konfirmationstest, ein Seed traegt nach der Seed-Regel des Projekts kein Verdikt. Anlass ist ein Defekt: der Cosine des Standardrezepts ist INERT, weil T_max am --epochs-Flag haengt (bei 100 gesetzt, 15 gelaufen => LR faellt um 5 %) -- das Rezept seit v12b_lr hat sein Annealing nie ausgespielt. v21-b20 gehoert NICHT hierher, seine Frage ist die Plattenthematik (PREREG_corpus_distillation.md par.10.8). -->

# PREREG: Lernraten-Schedule — Plateau statt inertem Cosine

Registriert 2026-08-17, **vor beiden Laeufen**. Nutzer-Anstoss: *"gibt es nicht
auch sowas wie die technik als erster große schritte bis das plateau erreicht
wird um zu sehen wo es ca liegt und dann feinere ll auflösung in der
zielregion?"*

---

## par.1 DER ANLASS IST EIN DEFEKT, KEIN EINFALL

`CosineAnnealingLR` bekommt `T_max=epochs` (`train.py:843`) — den Wert von
`--epochs`, nicht die Zahl der gelaufenen Epochen. Alle Laeufe des
Warm-Start-Standardrezepts ("warm start + lr 5e-5 + cosine", etabliert mit
v12b_lr) liefen mit `--epochs 100` und stoppten nach ~15. Gemessen an `v21-b18`:
die LR fiel von 5,00e-05 auf 4,76e-05, also um **5 %**.

> **Das Annealing des Standardrezepts hat nie stattgefunden.** Was gemessen
> wurde, war durchgehend eine konstante Lernrate.

Aufgefallen durch einen Nutzer-Hinweis, nicht durch eine Messung.

## par.2 WAS GEBAUT WURDE

`--lr-schedule plateau` → `ReduceLROnPlateau(mode="min", factor=0.5,
patience=2)`, gespeist mit derselben Metrik, nach der auch der beste
Checkpoint gewaehlt wird (`current_metric`). Default bleibt `none`, das
Bestandsverhalten ist unberuehrt.

**Warum adaptiv:** der Scheduler braucht den Horizont nicht. Genau daran
scheitert Cosine beim Cold Start — dessen Saettigungspunkt ist unbekannt, und
ein Cosine ueber einen geratenen Horizont regelt entweder gar nicht oder zu
frueh ab.

**Warum `patience=2`:** das Early Stopping dieses Projekts feuert nach 5
Epochen ohne Fortschritt auf beiden Koepfen. Eine groessere Geduld hiesse, dass
der Lauf abbricht, bevor die LR je gesenkt wird. Greift die Senkung und kommt
wieder Fortschritt, faellt der Early-Stop-Zaehler zurueck.

**Ungeprueft:** `factor=0.5` und `patience=2` sind gaengige Startwerte, fuer
dieses Projekt **nicht gemessen**. Sie werden hier mitgetestet, nicht
validiert.

## par.3 DER ARM — UND WAS DIESER LAUF IST

**`v21-b21` ist eine PARAMETERSUCHE, kein Konfirmationstest.** Nutzer-Vorgabe:
*"b21 soll nur einstellparameter finden fuer den warmstart"*. Das steht hier,
damit hinterher niemand ein Verdikt hineinliest, das der Aufbau nicht tragen
kann — ein Arm, ein Seed, und die Projektregel zur Seed-Streuung
(`project_training_seed_variance`: der Seed bewegt die Metrik 4-6x staerker als
jeder Knopf) gilt fuer Einzelvergleiche voll.

| Arm | Start | LR | Schedule | Bezug |
|---|---|---:|---|---|
| `v21-b21` | Warm (`v21_2d_brierbest`) | 5e-5 | plateau | `v21-b18` (konstante 5e-5) |

Alles Uebrige identisch zu `b18`: neues Fenster, `--ownership-weight 1.0`,
`--conjunction-head`, 2d/wdl/nortv, opp-points, endgame, seed 2, `--epochs 60`
als Deckel (bei `plateau` ohne Wirkung auf die LR-Kurve).

`v21-b20` steht NICHT mehr in dieser Prereg. Sein Zweck ist die Plattenfrage,
nicht der Scheduler; er ist in `PREREG_corpus_distillation.md` par.10.8
registriert. Dass er mit `plateau` faehrt, ist dort ein Nebeneffekt.

## par.4 WAS ABGELESEN WIRD (vorab, damit nicht nachtraeglich ausgewaehlt wird)

Auf dem Held-out des neuen Fensters, Gate-A-Sonde auf der CPU
(`CUDA_VISIBLE_DEVICES=-1`; `""` wirkt unter Windows nicht):

1. **LR-Kurve und Epochen bis Early Stop** — hat der Scheduler ueberhaupt
   gegriffen? Das ist die eigentliche Frage einer Parametersuche.
2. `val_combined` und Policy-val_loss am besten Checkpoint, neben `b18`.
3. Kopfguete (Feld-AUC, E_k-Rang) als Beobachtung.

## par.5 WIE DAS ERGEBNIS ZU LESEN IST

**Kein Erfolgs-/Misserfolgsurteil.** Ein Einzellauf entscheidet hier nichts.
Was er liefert, ist eine **Einstellempfehlung** fuer das kuenftige
Warm-Start-Rezept, plus die Information, ob `factor=0.5`/`patience=2`
ueberhaupt im richtigen Bereich liegen.

Drei Ablesungen sind vorab benannt:

- **Der Scheduler greift nie** (LR bleibt 5e-5, Early Stopping feuert zuerst)
  → `patience=2` ist zu gross, naechster Versuch `patience=1`. **Keine Absage
  an das Verfahren.**
- **Der Scheduler greift und der Lauf laeuft laenger** → das Verfahren tut, was
  es soll; ob es besser ist, muesste ein gepaarter Mehr-Seed-Versuch zeigen.
- **Der Scheduler greift und es wird schlechter** → `factor=0.5` senkt zu hart,
  oder das Bestandsrezept war mit konstanter LR zufaellig gut bedient.

Erst wenn eine dieser Ablesungen eine Richtung nahelegt, lohnt der teure Teil:
ein gepaarter Versuch ueber mehrere Seeds. Das ist ausdruecklich NICHT Teil
dieser Prereg.

## par.5a VORAB-ABSCHAETZUNG AN `b18`s VERLAUF (2026-08-17, vor dem Lauf)

Nutzer-Anstoss: die Parameter an einem bereits gelaufenen Verlauf abschaetzen,
statt sie zu raten. `ReduceLROnPlateau` wurde dafuer mit dem echten
PyTorch-Objekt ueber `b18`s Policy-Val-Reihe gefahren
(0,40 / 0,39 / 0,39 / 0,39 / 0,39 / 0,40 / 0,40 / 0,41 / 0,41 / 0,42 / 0,43 /
0,44 / 0,44 / 0,45 / 0,46):

| `patience` | Senkungen bei Epoche | End-LR nach 15 Epochen |
|---:|---|---:|
| 1 | 4, 6, 8, 10, 12, 14 | 7,8e-07 (Faktor 64) |
| **2** | **5**, 8, 11, 14 | 3,1e-06 (Faktor 16) |
| 3 | 6, 10, 14 | 6,3e-06 (Faktor 8) |

Zum Vergleich: `b18`s bester Checkpoint lag bei **Epoche 4**, Early Stopping
feuerte nach 15.

**Was die Simulation traegt:** nur die ERSTE Senkung. Danach waere der Verlauf
ein anderer — der Scheduler greift ja in genau das ein, was er misst. Die
Folgesenkungen sind Artefakte der eingefrorenen Kurve.

**Zwei Einschraenkungen:**

1. Die Eingabe ist auf **zwei Nachkommastellen gerundet**, weil `train.py`
   bisher keinen Epochen-Verlauf speichert. Rundung erzeugt kuenstliche
   Plateaus ("0,39 → 0,39" liest der Scheduler als Stillstand), und der
   Standard-`threshold` von 1e-4 relativ verschaerft das. **Epoche 5 ist eine
   Untergrenze**, real duerfte es spaeter greifen. (Ab sofort behoben: das
   Manifest traegt den Verlauf mit voller Genauigkeit, siehe unten.)
2. Es ist EINE Kurve, kein Mittel ueber Seeds.

**Folge fuer par.5:** die dort erstgenannte Ablesung — "der Scheduler greift
nie" — ist damit die **unwahrscheinlichste** der drei. Erwartet wird die
zweite oder dritte.

**Das eigentliche Risiko, das die Abschaetzung sichtbar macht:** sobald die
Ueberanpassung einsetzt, liest der Reducer sie als Plateau und senkt **immer
weiter** — bei `patience=2` auf ein Sechzehntel. Das Problem des Laufs ist aber
keine zu hohe Lernrate, sondern Ueberanpassung auf 7.000 Policy-Partien. Ob
die Halbierung sie verlangsamt und ein neues Optimum bringt oder den Lauf nur
einfriert, kann keine Simulation sagen. Das ist die Frage von `b21`.

**Entscheidung: `patience=2` bleibt.** Die erste Senkung sitzt am Optimum;
`patience=1` schnitte schon bei Epoche 4 und damit potenziell auf einen
einzelnen Ausreisser.

**Neu gebaut (Nutzer-Anstoss im selben Zug):** das Trainingsmanifest bekommt
`epoch_history` — je Epoche LR, Policy/Value/Points-Verluste (Training UND
Validierung), Value-Brier, Ownership-Val und `val_combined`, in voller
Genauigkeit. Damit ist die naechste Abschaetzung dieser Art keine Schaetzung
mehr. Gilt ab `v21-b20`; `b18`/`b19` haben ihn noch nicht.

## par.6 ERGEBNIS (2026-08-17)

`v21-b21`, Early Stopping nach Epoche 15, bester Checkpoint Epoche 4. Erster
Lauf mit `epoch_history` im Manifest, LR also in voller Genauigkeit:

| Ep | LR | policy_val | val_combined | own_val |
|---:|---|---:|---:|---:|
| 1–7 | 5,000e-05 | 0,3974 → 0,4004 | 0,5379 → 0,5414 | 0,3702 → 0,3341 |
| **8** | **2,500e-05** ← erste Senkung | 0,4057 | 0,5466 | 0,3320 |
| 11 | 1,250e-05 | 0,4167 | 0,5579 | 0,3284 |
| 14 | 6,250e-06 | 0,4252 | 0,5665 | 0,3267 |
| 15 | 6,250e-06 | 0,4272 | 0,5685 | 0,3265 |

**Vergleich mit `b18` (konstante 5e-5) am besten Checkpoint:**

| | `b18` | `b21` |
|---|---:|---:|
| beste Epoche | 4 | 4 |
| val_combined | 0,5304 | **0,5304** |
| policy_val | 0,3899 | **0,3899** |
| own_val bei Ep 15 | **0,3200** | 0,3265 |

## par.7 EINSTELLEMPFEHLUNG

**Eine vierte Ablesung, die ich nicht vorregistriert hatte, ist eingetreten:**
der Scheduler greift — aber ERST NACH dem Optimum, und aendert deshalb nichts.
Erste Senkung Epoche 8, Optimum Epoche 4. Der beste Checkpoint ist mit `b18`
identisch, bis auf die vierte Stelle.

Meine Vorab-Abschaetzung (par.5a) hatte Epoche 5 genannt und ausdruecklich als
**Untergrenze** markiert, weil die Eingabe auf zwei Nachkommastellen gerundet
war. Richtung richtig, Betrag um drei Epochen zu frueh. Genau dafuer steht der
Epochen-Verlauf jetzt im Manifest.

**Empfehlung: `plateau` NICHT als Warm-Start-Standard.** Der Grund ist nicht
`patience` — auch `patience=1` waere zu spaet, weil `val_combined` erst ab
Epoche 5 steigt und ein reaktiver Scheduler frueher gar nicht ausloesen KANN.
Das Regime ist "schnelle Ueberanpassung, Optimum bei Epoche 4". Dagegen hilft
kein reaktives, sondern nur ein **proaktives** Verfahren.

**Was stattdessen zu versuchen waere:** ein Cosine mit `T_max` in der
Groessenordnung des tatsaechlichen Laufs, also `--epochs 8..10` statt 100. Dann
regelt die LR **durch** die Optimumsregion, statt danach. Das ist die
Praezisierung der Nutzer-Vorgabe von gestern ("--epochs auf 20 stellen"):
20 waere nach diesem Verlauf noch zu lang.

**Ein Schaden, der ausdruecklich gehoert dazu:** `b21`s Ownership-Val liegt bei
Epoche 15 mit 0,3265 SCHLECHTER als `b18`s 0,3200. Die LR-Senkungen haben den
Ownership-Kopf gebremst, der noch monoton besser wurde — ausgeloest von
`val_combined`, das den Ownership-Verlust gar nicht enthaelt (`train.py:1589`).
Ein Scheduler, der auf die Policy hoert und dabei den Kopf abwuergt, ist im
Freeze-Modus harmlos, hier aber ein echter Zielkonflikt. **Wer `plateau` je fuer
ein Kopf-Training einsetzt, muss ihn mit dem Ownership-Verlust speisen, nicht
mit val_combined.**

**Der Knopf bleibt drin** (Default `none`, nichts veraendert sich ohne
Zutun) — fuer Regime mit unbekanntem Saettigungspunkt, etwa den Cold Start
`v21-b20`, ist er weiter die richtige Wahl. Nur fuer den Warm Start nicht.

### ERGEBNIS WEG 1 — TEILABLESUNG UEBER 7 VON 60 EPOCHEN (2026-08-17)

`v21-b22`: Frozen Trunk auf `v21-b18_best`, lr 5e-4, `plateau`, 60 Epochen,
`ownership_weight` 1,0, Seed 2 (aus `manifest_train_v21-b22_20260817_220655.json`).

**Der Lauf laeuft noch** — was hier steht, ist die Ablesung der ersten sieben
Epochen, nicht das Endergebnis. Grund fuer die Luecke: der Hintergrund-Wrapper
der Shell starb (Exit 1), das Training selbst laeuft weiter (PID-Pruefung:
CPU-Zuwachs 13 s in 20 s, GPU 26 %). Verloren ist die Log-Sicht, nicht der Lauf.
Die `epoch_history` im Manifest schliesst die Luecke am Laufende.

| | Own-Val |
|---|---:|
| `b18_best` = Epoche 4, Startpunkt von `b22` | 0,3466 |
| `b22` Frozen Trunk E1 | 0,3438 |
| **`b22` E7** | **0,3414** |
| `b18` gemeinsames Training, dieselbe E7 | 0,3339 |
| `b18` E15 | 0,3191 |
| `b19` E15 (Gewicht 2,0) | 0,2994 |

Der eingefrorene Rumpf bringt den Kopf in sieben Epochen um **0,0052** voran
und flacht dabei ab (E5→E7 nur noch 0,0004 je Epoche); die LR ist nie gefallen,
weil `plateau` bei minimaler Besserung nicht ausloest. Das gemeinsame Training
schaffte im selben Fenster 0,0127 und lief weiter auf 0,3191.

**Lesart, ausdruecklich als Herleitung markiert:** die Kopfguete haengt an der
Rumpfdarstellung, nicht an der Kopfkapazitaet. Dann loest Weg 1 den
Zielkonflikt nicht, sondern tauscht die Seite — Policy erhalten, Kopf
verschenkt. Falls die restlichen 53 Epochen das bestaetigen, ist der
Frozen-Trunk-Kopf fuer den Konjunktions-Verbraucher der SCHLECHTERE Kopf, und
`b18`/`b19` bleiben die Kandidaten.

**Was das nicht sagt:** ob ein guter Ownership-Kopf ueberhaupt Plattenpunkte
eintraegt. Das entscheidet der Verbraucher, nicht der Kopf — Tor C par.15 hat
Kopfguete schon einmal als Engpass ausgeschlossen.
