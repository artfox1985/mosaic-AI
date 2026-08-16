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

## par.6 ERGEBNIS (leer bei Registrierung)

## par.7 EINSTELLEMPFEHLUNG (leer bei Registrierung)
