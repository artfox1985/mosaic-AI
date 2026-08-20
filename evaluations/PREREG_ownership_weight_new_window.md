<!-- STATUS: ENTSCHIEDEN | Frage: Ist ownership_weight 1,0 im NEUEN Fenster (Korpus als Policy-Sockel) noch die richtige Wahl, und haelt der Policy-Waechter dort? | Beleg: Gewicht 2,0 UEBERNOMMEN (b18 vs b19, 2026-08-17): Kopf besser auf 3 von 4 Kriterien, Policy-Waechter haelt (+0,49 % gegen Schwelle 2 %). Stale-Korrektur des Kopfes 2026-08-20. -->

# PREREG: Ownership-Gewicht im neuen Fenster — zwei Arme

Registriert 2026-08-16 um 18:20, **waehrend `v21-b18` laeuft und vor jeder
Auswertung**. Nutzer-Freigabe: *"v21-b18 bei 1,0 und v21-b19 bei 2,0, beide im
neuen fenster. genehmigt und kann gestartet werden"*.

---

## par.1 DIE FRAGE, UND WARUM SIE NEU IST

`ownership_weight` ist ein **relatives** Verlustgewicht: es wiegt den
Ownership-Verlust gegen Policy, Value und Punkte auf. Der alte Sweep
(`PREREG_ownership_corpus.md` par.9/par.10) hat ihn im ALTEN Aufbau vermessen,
in dem der Policy-Gradient aus dem v21-Fenster kam. Im neuen Fenster kommt er
zu 100 % aus dem Ownership-Korpus. Der Nenner des Verhaeltnisses ist also
ausgetauscht.

**Was vom alten Sweep bleibt** (ausdruecklich, damit es nicht doppelt gemessen
wird):

- Die **Kopfguete-Messung** ist weiter gueltig. Tor A lief auf dem
  KORPUS-Anteil des Held-outs (`n_val_corpus_files = 82`,
  `n_heldout_games = 820`, `evaluations/ownership_gate_a_f1_f2.json`) — also
  fensterunabhaengig, und der Korpus ist unveraendert.
- Der **monotone Trend** ueber fuenf Stuetzstellen (0 / 0,1 / 0,2 / 0,5 / 1,0)
  auf mehreren Zielkriterien traegt. Die Projektregel "≥6 gepaarte Seeds"
  (`project_training_seed_variance`) stammt aus EINZELNEN A/B-Vergleichen; ein
  monotoner Fuenf-Punkte-Trend ist etwas anderes und wird hier ausdruecklich
  NICHT als ungueltig behandelt. Das ist eine Zuruecknahme eines zu breiten
  Koordinator-Einwands vom selben Tag.

**Was nicht bleibt:** der Waechter. "Policy-val_loss reagiert praktisch nicht
(0,2139 -> 0,2141)" war die Zahl, auf der die stehende Nutzer-Freigabe zur
Gewichtserhoehung ruhte (`feedback_ownership_weight_may_rise`). Sie wurde an
einer fenstertrainierten Policy erhoben. Das Gewicht schlichtet aber genau den
Wettstreit zwischen Ownership-Kopf und Policy — und dessen Gegenseite ist eine
andere geworden.

**Was nie belegt war:** dass 1,0 das Optimum ist. Der alte Sweep war bis 1,0
monoton steigend; 1,0 ist ein Randwert. Deshalb der Arm bei 2,0.

---

## par.2 GEPRUEFTER IST-STAND

| Sache | Befund | Pruefstelle |
|---|---|---|
| Korpus war bisher policy-maskiert | in allen sieben Laeufen; im Cache nachweisbar (pol_w==0 waechst um 1.200.896 bei 1.179.863 zusaetzlichen Zuegen) | `PREREG_corpus_distillation.md` par.10.4/par.10.5 |
| Neuer Traegersatz | `carrier_prefixes = ["selfplay_v21_own_"]` | `data/policy_carrier_manifest_own.json` (gitignored!) |
| `heur_own` bewusst NICHT Traeger | Nutzer-Entscheid; Maskierung trifft nur die Policy, sein Value-Ziel geht weiter ein | ebd. |
| Neues Fenster | 2945 Dateien / 29.450 Partien = exakt die v21-Menge; 2651 Train / 294 Val | Startprotokoll `v21-b18` |
| Policy-Ziele | 7.000 Partien (`v21_own_a` + k1/k2/k5/k6) | mit `_is_policy_carrier` nachgerechnet |
| Value-Ziele | 29.450 Partien | ebd. |
| Ausgeduennt | `v19wdlsw` (800 Dateien) — der aeltere Schwarm, passend zur Rotationslogik | Nutzer-Vorgabe |
| Val-Split ist seed-fest | `random.Random(20260707)` auf der sortierten Dateiliste; `--seed` aendert nur Initialisierung/Reihenfolge | `neural_net.py` |
| Bester Checkpoint im alten Sweep | **Epoche 1** bei allen vier Armen | `PREREG_ownership_corpus.md:547` |

**Folge aus der vorletzten Zeile:** beide Arme sehen bei identischem Dateisatz
**exakt dasselbe Held-out**. Die Paarung ist geschenkt, ein Seed je Arm genuegt
fuer den Paarvergleich der beiden Gewichte.

---

## par.3 DIE ARME

| Arm | `ownership_weight` | sonst |
|---|---:|---|
| `v21-b18` | **1,0** | Rezept Zeile fuer Zeile wie `w1`: warm start `v21_2d_brierbest`, lr 5e-5, cosine, 100 Epochen mit Early Stop, seed 2, `--conjunction-head`, 2d, wdl, nortv, opp-points, endgame |
| `v21-b19` | **2,0** | identisch |

Einziger Unterschied ist das Gewicht. Beide laufen sequentiell auf demselben
Cache.

---


**NACHTRAG 2026-08-17 — der Cosine war in beiden Armen INERT.** Nutzer-Hinweis.
`CosineAnnealingLR` bekommt `T_max=epochs` (`train.py:843`), also den Wert von
`--epochs`. Beide Arme liefen mit `--epochs 100` und stoppten nach 15 -- die
Lernrate kroch von 5,00e-05 auf 4,76e-05, das sind 5 % ueber den ganzen Lauf.
Praktisch war es eine **konstante Lernrate**, kein Cosine.

Fuer den Vergleich b18 gegen b19 ist das **unschaedlich**: beide Arme sind
gleich betroffen, und das kopierte `w1`-Rezept lief mit demselben Defekt --
die Einfaktor-Aussage bleibt gueltig. Die Beschreibung "lr 5e-5, cosine" in
par.3 ist trotzdem irrefuehrend und steht hiermit korrigiert.

**Fuer kuenftige Warm Starts:** `--epochs` auf die erwartete Lauflaenge setzen
(rund 20), damit der Cosine tatsaechlich abregelt.

## par.4 ENTSCHEIDUNGSGROESSEN (vorab, gemessen auf dem KORPUS-Held-out)

Gemessen wird mit der Bestandssonde `tools/probes/ownership_gate_a.py` auf dem
Korpus-Anteil des Val-Splits — dieselbe Skala wie fuer `w1_best`, `F1`, `F2`,
damit die Zahlen ueber den Fensterwechsel hinweg vergleichbar bleiben. Die
val_loss-Zahlen aus den Trainingslogs sind es ausdruecklich NICHT.

**AUSFUEHRUNG AUF DER CPU** (Nutzer-Vorgabe 2026-08-16): waehrend `v21-b19`
die GPU belegt, laufen alle Auswertungen zu `v21-b18` auf der CPU. Beide Sonden
waehlen ihr Geraet ueber `DEVICE = "cuda" if torch.cuda.is_available() else
"cpu"` (`ownership_gate_a.py:86`, `ownership_route_calibration.py:73`) und
haben keinen Schalter dafuer. Erzwungen wird es per Env-Var — **geprueft, nicht
angenommen**: `CUDA_VISIBLE_DEVICES=""` wirkt unter Windows NICHT
(`is_available()` bleibt `True`), `CUDA_VISIBLE_DEVICES=-1` wirkt. Dazu die
Torch-Threads begrenzen (`OMP_NUM_THREADS`), damit der Dataloader des laufenden
Trainings Luft behaelt.

1. **Kopfguete**: Feld-AUC und E_k-Rangkorrelation (k1 Spalten, k2 Diagonalen,
   k5 Ecken), zusaetzlich die Konjunktions-AUC je Atomgruppe.
2. **WAECHTER**: Policy-val_loss auf demselben Held-out. Er ist im neuen
   Aufbau aussagekraeftiger als frueher, weil die Policy erstmals aus derselben
   Verteilung lernt, auf der sie geprueft wird.
3. Value-Brier auf demselben Held-out, als Beobachtung mitgefuehrt.

---

## par.5 VORAB-REGEL (woertlich, vor der Auswertung)

> **2,0 wird uebernommen**, wenn es die Kopfguete auf der MEHRHEIT von
> {Feld-AUC, E_k k1, E_k k2, E_k k5} gegenueber 1,0 hebt **und** der
> Policy-val_loss dabei nicht merklich steigt.

**"Nicht merklich" bekommt hier eine Zahl** — die Lehre aus der unscharfen
Abbruchregel in `PREREG_ownership_selector.md` par.5, die am selben Tag
nachtraeglich ausgelegt werden musste: **Anstieg des Policy-val_loss um mehr
als 2 % gegenueber dem 1,0-Arm = Waechter gerissen, 2,0 wird nicht
uebernommen**, unabhaengig davon, wie gut der Kopf wird.

**Bei gerissenem Waechter bleibt es bei 1,0**, und die stehende Freigabe zur
Gewichtserhoehung ist damit im neuen Fenster ausgeschoepft — das waere dann
ein gemessenes Ergebnis und keine Vorsicht.

**Kein dritter Arm ohne Befund:** ein Arm bei 4,0 kommt nur infrage, wenn 2,0
den Kopf hebt UND den Waechter haelt. Sonst ist das Optimum eingeklammert.

**Keine Arena in dieser Prereg.** Dies ist eine Trainings-/Kopfguete-Messung.
Eine Staerkeaussage verlangt das direkte Duell — die Lehre aus dem heutigen
Tag, an dem `w0_best` den Champion ueber den Heuristik-Anker deutlich schlug
und das direkte Duell 43:57 verlor.

---

## par.6 WAS DIESE MESSUNG NICHT BEANTWORTET

- **Ob der Korpus als Policy-Sockel ueberhaupt etwas bringt.** Dafuer waere ein
  Vergleich gegen den Champion noetig, und der ist eine Arena-Frage.
- **Ob 1,0 gegen 0,5 im neuen Fenster noch richtig herum liegt.** Uebernommen
  aus dem alten Sweep (par.1), nicht neu gemessen.
- **Ob die Heuristik-Partien im Value-Kopf schaden.** Sie laufen weiter mit
  (Nutzer-Entscheid "Masse > Qualitaet"); eine Value-Maske je Datei existiert
  nicht.

---

## par.7 ERGEBNIS (leer bei Registrierung)

## par.8 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)

## par.6 ERGEBNIS (2026-08-17)

Beide Arme durch, Early Stopping jeweils nach Epoche 15. Bester Checkpoint
`b18` Epoche 4, `b19` Epoche 3. Kopfguete mit `tools/probes/ownership_gate_a.py`
auf der CPU, Rohzahlen `evaluations/ownership_gate_a_b18_b19.json`.

| Metrik am besten Checkpoint | `b18` (1,0) | `b19` (2,0) | besser |
|---|---:|---:|---|
| **Feld-AUC macro** | 0,7944 | **0,8087** | b19 |
| Feld-Brier (Basis 0,1828) | 0,1379 | **0,1343** | b19 |
| **E_k k1 Spalten** | 0,3249 | **0,3273** | b19 |
| **E_k k2 Diagonalen** | 0,3387 | 0,3388 | Gleichstand |
| **E_k k5 Ecken** | 0,3974 | **0,4076** | b19 |
| Konjunktions-AUC k1 | 0,9037 | **0,9119** | b19 |
| Konjunktions-AUC k2 | 0,9032 | **0,9314** | b19 |
| Konjunktions-AUC k5 | 0,9357 | **0,9529** | b19 |
| **WAECHTER** policy_val | **0,3899** | 0,3918 | b18 |

**Zum Held-out, ausdruecklich:** die Sonde misst auf dem Split des
w0-Manifests, der mit den Trainingsdaten beider Arme ueberlappt. Fuer den
Vergleich der beiden UNTEREINANDER ist das unschaedlich — sie haben exakt
denselben Trainingssatz und sind identisch betroffen. Die Absolutwerte sind
NICHT mit `F1`/`w1` vergleichbar.

**Zur Sauberkeit des Paares:** beide Arme liefen mit `--seed 2`, also
identischer Initialisierung, identischer Datenreihenfolge und identischem
Val-Split. Der einzige Unterschied ist das Gewicht. Das ist ein sehr sauberer
Einfaktor-Vergleich — aber es bleibt EINE Realisierung. Getragen wird er
weniger von der Groesse der Einzeldifferenzen als davon, dass **acht von neun
Metriken in dieselbe Richtung zeigen** und die neunte ein Gleichstand ist.

## par.7 VERDIKT NACH DER VORAB-REGEL

Die Regel aus par.5 woertlich: *"2,0 wird uebernommen, wenn es die Kopfguete
auf der MEHRHEIT von {Feld-AUC, E_k k1, E_k k2, E_k k5} gegenueber 1,0 hebt
UND der Policy-val_loss dabei nicht merklich steigt"*, mit der Zahl
**"mehr als 2 % Anstieg = gerissen"**.

- **Kopfguete:** Feld-AUC, k1 und k5 gehen an `b19`, k2 ist ein Gleichstand
  (Differenz 0,0001 — das als Sieg zu zaehlen waere unredlich). **Drei von vier,
  Mehrheit erfuellt.**
- **Waechter:** 0,3899 → 0,3918 = **+0,49 %**, klar unter der Schwelle von 2 %.
  **Haelt.**

> **`ownership_weight = 2,0` WIRD UEBERNOMMEN.**

**Folge fuer den naechsten Arm.** par.5 sagt: *"ein Arm bei 4,0 kommt nur
infrage, wenn 2,0 den Kopf hebt UND den Waechter haelt."* Beides ist
eingetreten — **ein 4,0-Arm ist damit im Rahmen**, das Optimum ist weiterhin
nicht eingeklammert. Er ist nicht gestartet und braucht eine Nutzer-Entscheidung;
die GPU ist bis in den Nachmittag mit `b20`/`b21` belegt.

**Was das NICHT heisst:** eine Staerkeaussage. Diese Prereg misst Kopfguete und
Waechter, keine Arena. Ob der bessere Kopf am Brett etwas aendert, haengt am
Verbraucher — und der ist Gegenstand von Tor C, nicht von hier.


## SCHLIESSUNGS-NACHTRAG (2026-08-20)

Status auf **ENTSCHIEDEN** gesetzt (Nutzer-Durchsicht der offenen Registrierungen). Begruendung: Gewicht 2,0 UEBERNOMMEN (b18 vs b19, 2026-08-17): Kopf besser auf 3 von 4 Kriterien, Policy-Waechter haelt (+0,49 % gegen Schwelle 2 %). Stale-Korrektur des Kopfes 2026-08-20.
