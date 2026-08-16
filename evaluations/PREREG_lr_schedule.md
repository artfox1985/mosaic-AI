<!-- STATUS: OFFEN | Frage: Bringt ein adaptiver Plateau-Scheduler (grob bis zum Plateau, dann feiner) mehr als die faktisch konstante Lernrate des Bestandsrezepts -- im Warm Start und im Cold Start? | Beleg: **REGISTRIERT 2026-08-17, vor beiden Laeufen.** Anlass: der Cosine des Bestandsrezepts ist INERT (T_max haengt an --epochs, bei 100 gesetzt und 15 gelaufen faellt die LR um 5 %) -- das Standardrezept seit v12b_lr hat sein Annealing nie ausgespielt. Zwei Arme: v21-b20 (Cold Start, lr 4e-4, plateau) und v21-b21 (Warm Start wie b18, nur plateau statt cosine). -->

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

## par.3 DIE ARME

| Arm | Start | LR | Schedule | Vergleich gegen |
|---|---|---:|---|---|
| `v21-b20` | **Cold** (kein `--load`) | 4e-4 | plateau | kein Bestandsarm — Erkundung |
| `v21-b21` | Warm (`v21_2d_brierbest`) | 5e-5 | plateau | **`v21-b18`** (einfaktoriell) |

Alles Uebrige identisch: neues Fenster (Korpus als Policy-Sockel, 2945
Dateien), `--ownership-weight 1.0`, `--conjunction-head`, 2d/wdl/nortv,
opp-points, endgame, seed 2, `--epochs 60` als Deckel (bei `plateau` ohne
Wirkung auf die LR-Kurve, anders als bei Cosine).

**`b21` gegen `b18` ist sauber einfaktoriell**: b18s Cosine war inert, also
vergleicht man "konstante 5e-5" gegen "5e-5 mit Plateau-Senkung". Beide sehen
dasselbe Held-out (seed-fester Val-Split, identischer Dateisatz).

## par.4 ENTSCHEIDUNGSGROESSEN

Gemessen auf dem Held-out des neuen Fensters, mit der Gate-A-Sonde auf der
CPU (`CUDA_VISIBLE_DEVICES=-1`, geprueft: `""` wirkt unter Windows nicht):

1. **`val_combined` am besten Checkpoint** — die Groesse, nach der der
   Checkpoint ohnehin gewaehlt wird, und die der Scheduler direkt optimiert.
2. **Policy-val_loss** am besten Checkpoint.
3. **Kopfguete** (Feld-AUC, E_k-Rang k1/k2/k5) — als Beobachtung.
4. **Epochen bis Early Stop** und die LR-Kurve — zeigt, ob der Scheduler
   ueberhaupt gegriffen hat.

## par.5 VORAB-REGEL

> **`plateau` wird neues Warm-Start-Standardrezept**, wenn `b21` ein besseres
> `val_combined` am besten Checkpoint erreicht als `b18` **und** der
> Policy-val_loss dabei nicht steigt.

**Wenn der Scheduler gar nicht greift** (LR bleibt ueber den ganzen Lauf bei
5e-5, weil Early Stopping vorher feuert), ist das **kein Ergebnis ueber
Plateau-Scheduling**, sondern ein Befund ueber `patience` — dann waere
`patience=1` der naechste Versuch, nicht die Verwerfung des Verfahrens. Das
steht hier vorab, damit es hinterher nicht als Absage gelesen wird.

**Fuer `b20` gibt es keine Erfolgsregel** — es ist ein Erkundungslauf. Seine
Frage ist eine andere (par.6), und seine Zahlen sind mit keinem Warm-Start-Arm
vergleichbar.

## par.6 WAS `b20` BEANTWORTEN SOLL (Cold Start)

Nutzer-Frage: baut eine Policy, die **nie etwas anderes gesehen hat** als
plattengelenktes Spiel, die Wertungsplatten von selbst? `b18` hat das mit
Warm Start **verneint** (`PREREG_corpus_distillation.md` par.10.7: gegen den
Champion k1 +0,05, k2 −0,07, k5 −0,09 — nichts). Die offene Frage war, ob das
am Korpus liegt oder am Prior aus 30.000 Partien, der in den Gewichten steckt.

**Erwartungsmanagement, vorab:** ein From-Scratch-Aufbau ist hier schon einmal
gefahren worden — v14 landete bei Elo 884 gegen einen 1100er-Champion. `b20`
wird die Arena voraussichtlich deutlich verlieren. **Die tragende Messgroesse
sind deshalb die Plattenpunkte je Kriterium, nicht die Siege.** Ein schwaches
Netz, das k1 und k2 anspielt, beantwortet die Frage sauberer als ein starkes,
bei dem man nie weiss, ob der Prior oder der Korpus gesprochen hat.

## par.7 ERGEBNIS (leer bei Registrierung)

## par.8 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)
