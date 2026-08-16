<!-- STATUS: OFFEN | Frage: Loest ein eingefrorener Trunk (nur ownership_head trainiert, Auswahl ueber den Ownership-Val-Verlust) den Checkpoint-Zielkonflikt aus PREREG_ownership_corpus.md §10.3 -- oder ist der eingefrorene Trunk selbst die Decke fuer die Kopfguete? | Beleg: **OFFEN, vorregistriert 2026-08-16.** Werkzeug gebaut und selbstgetestet (train.py --freeze-trunk, freeze_trunk.py, tools/freeze_trunk_selfcheck.py GRUEN inkl. Bit-Identitaets- und Nicht-vacuous-Nachweis), NICHTS gestartet -- der Start ist ein eigener Nutzer-Knopf. Zwei Arme (F1 vom besten Sweep-Checkpoint, F2 vom Champion) gegen die Bestandszahlen aus §10; Metriken = Tor A ueber tools/probes/ownership_gate_a.py auf demselben Held-out. -->

# PREREG: Trunk einfrieren, nur den Ownership-Kopf weitertrainieren

Stand 2026-08-16, PLAN. Nichts gestartet (auf der GPU laeuft der Sweep-Arm w1,
PREREG_ownership_corpus.md §10.5). Durchgehend Plan-Zeitform fuer alles, was
noch nicht gebaut/gemessen ist; was in dieser Sitzung GEBAUT wurde, steht in §6
in der Vergangenheitsform mit Pruefstelle.

Nutzer-Auftrag, direkt aus dem Tor-A-Befund. Ursprung der Idee:
PREREG_provocation.md §10 Punkt 2 (Nutzer-Vorschlag) -- **inklusive des dort
notierten Vorbehalts**, der hier als eigener messbarer Ausgang gefuehrt wird
(§5).

## §1 Fragestellung

PREREG_ownership_corpus.md §10.3 (Zahlen dort, vom Koordinator am
`ownership_gate_a_results.json` nachgerechnet) zeigt einen Zielkonflikt, der
kein Ownership-Problem ist:

| Groesse (Arm w05) | `_best` (Ep. 1) | `final` (Ep. 15) |
|---|---:|---:|
| Feld-AUC eigene | 0,709 | **0,837** |
| Konjunktion k1 / k2 / k5 (AUC) | 0,745 / 0,788 / 0,827 | **0,957 / 0,984 / 0,963** |
| E_k Spearman k1 / k2 / k5 | 0,160 / 0,266 / 0,269 | **0,332 / 0,347 / 0,408** |
| policy val_loss | **0,2138** | 0,3002 |

Der `_best`-Checkpoint faellt bei ALLEN vier Armen auf Epoche 1, weil das
Auswahlkriterium `val_combined` den Ownership-Verlust gar nicht enthaelt
(geprueft in dieser Sitzung: `train.py`, `current_metric`-Stelle -- die Formel
ist `epoch_val_ploss + value_weight*value_term + points_weight*
epoch_val_pointsloss`, kein Ownership-Term; und der Ownership-Val-Verlust
existierte bis heute nirgends im Lauf, der Val-Zweig entpackte `v_pred_own`
zwar, benutzte es aber nie). Die Policy-Verschlechterung bei Ep. 15 ist
NACHWEISLICH kein Ownership-Effekt: der Kontrollarm w0 (Gewicht 0,0) zeigt
denselben Wert 0,3002 -- reines Ueberanpassen ueber 15 Epochen.

**Frage dieses Preregs:** Loest Trunk-Einfrieren den Konflikt strukturell? Wenn
Trunk und alle uebrigen Koepfe eingefroren sind, KANN die Policy nicht mehr
ueberanpassen (bit-identisch belegt, §6), und der Kopf bekommt seine Epochen.
Erreicht er dabei die `final`-Kopfguete -- oder ist der eingefrorene Trunk
selbst die Decke?

## §2 Die zwei Arme (plus die Bestandsdaten als dritter Vergleichspunkt)

Alle Arme auf **demselben Korpus und demselben Held-out** wie der §9/§10-Sweep.
Das ist keine Absichtserklaerung, sondern eine pruefbare Bedingung, siehe §4.

| Arm | Start (`--load`) | Training | Zweck |
|---|---|---|---|
| **F1** (Haupt-Arm) | `v21_2d_own_w05_best` | `--freeze-trunk`, nur `ownership_head` | Der eigentliche Vorschlag: den Checkpoint, den wir sonst ausliefern wuerden, am Kopf nachschaerfen, ohne die Policy anzufassen |
| **F2** (Deckel-Sonde) | `v21_2d_brierbest` (Champion) | `--freeze-trunk`, nur `ownership_head` | Trunk, der NIE einen Ownership-Gradienten gesehen hat. Trennt "der Kopf reicht" von "der Trunk musste sich bewegen" (§5) |
| **J** (Bestand, laeuft nicht neu) | -- | `v21_2d_own_w05` `_best` + `final` aus §10 | Der GEMEINSAME Arm (Kopf + Trunk zusammen), Zahlen liegen bereits vor |

Arm J wird **nicht neu gerechnet**: seine Zahlen stehen in
`evaluations/ownership_gate_a_results.json` und stammen aus demselben
Held-out-Satz, den F1/F2 verwenden werden (§4). Ein Neulauf waere reine
Rechenzeit ohne Erkenntnis.

**`final` als Referenz, nicht `_best`**: die Messlatte fuer die Kopfguete ist
der `final`-Checkpoint von J (Ep. 15) -- der beste Kopf, den der gemeinsame
Weg je erzeugt hat. `_best` ist keine Latte, sondern der Zustand, den F1 als
Startpunkt uebernimmt.

## §3 Startpunkt-Entscheidung (mit Begruendung)

**Entscheidung: F1 startet von `v21_2d_own_w05_best`, F2 vom Champion
`v21_2d_brierbest`.** Alle vier Zahlen unten in dieser Sitzung direkt aus den
`.pth`-Dateien gelesen (`torch.load`, Felder `epochs` /
`final_policy_val_loss` / `final_value_val_brier` / Shape von
`ownership_head.2.weight`):

| Checkpoint | epochs | policy val_loss | Value-Brier | `ownership_head`-Breite |
|---|---:|---:|---:|---:|
| `alphazero_v21_2d_brierbest.pth` | 4 | 0,2282 | 0,1866 | **72** |
| `alphazero_v21_2d_own_w05_best.pth` | 1 | 0,2139 | 0,1883 | 140 |
| `alphazero_v21_2d_own_w05.pth` (final) | 15 | 0,3002 | 0,1905 | 140 |

Begruendung F1 = `w05_best`:

1. **Sein Policy-/Value-Zustand IST der Zustand, den wir behalten wollen.**
   policy val_loss 0,2139 ist das Optimum des Sweeps; Einfrieren konserviert
   ihn per Konstruktion (§6: bit-identisch). Das ist genau der Punkt der
   Uebung -- den guten Kopf holen, OHNE den guten Policy-Stand zu verlieren.
2. **Der Kopf hat schon eine Epoche.** Der Lauf setzt fort statt neu zu
   beginnen; keine Epoche geht dafuer drauf, das Bereits-Gelernte
   nachzuholen.
3. **Der Vergleich zu J bleibt exakt gepaart**: gleiches Gewicht (0,5),
   gleicher Korpus, gleicher Held-out, gleicher Seed -- der einzige
   Unterschied ist "Trunk friert ab Ep. 1 ein" gegen "Trunk laeuft bis Ep. 15
   mit".
4. Der Champion scheidet fuer F1 aus, weil sein `ownership_head` **72** breit
   ist (Tabelle oben) -- ein Konjunktions-Lauf von dort startet den Kopf
   zwangslaeufig FRISCH (Shape-Mismatch-Skip in `train.py`, "Shape-Mismatch,
   startet frisch"). Das waere ein zweiter Unterschied zu J und wuerde die
   Frage verwaschen. Fuer F2 ist genau dieser frische Kopf dagegen
   *erwuenscht* (§5).

**Vorab-Regel statt Nachher-Wahl** (gegen die Post-hoc-Falle): sollte der
laufende Arm w1 (§10.5 dort) den Arm w05 auf den Tor-A-Zielkriterien
schlagen, wandert F1 nach derselben Regel auf `v21_2d_own_w1_best` und
`--ownership-weight 1,0`; die Referenz J wird dann ebenfalls der w1-Satz.
Kriterium fuer "schlaegt": dieselbe Rangfolge-Regel wie §10.2/§10.4 (Feld-AUC
eigene + E_k-Spearman k1/k2/k5, Mehrheit).

## §4 Lauf-Konfiguration (fuer beide Freeze-Arme identisch)

```
python -u train.py --name v21_2d_own_f1 --load v21_2d_own_w05_best \
  --freeze-trunk --ownership-weight 0.5 --conjunction-head \
  --encoder 2d --value-head wdl --value-target-variant nortv \
  --opp-points-head --endgame-head --select-by-brier \
  --lr <s.u.> --lr-schedule cosine --epochs 100 --seed 2 \
  --value-weight 0.2 --val-frac 0.1 \
  --extra-data-dir data/ownership_corpus --no-snapshot
```

mit `MOSAIC_DATA_EXCLUDE=<v21_exclude_regex>` und
`MOSAIC_CARRIER_MANIFEST=v21` **exakt wie in §9** -- das ist die
Bedingung, ohne die der Held-out ein anderer waere: der Val-Split faellt auf
DATEI-Ebene ueber einen festen `random.Random(20260707)`-Shuffle der
sortierten Gesamtliste (geprueft: `train.py`, Split-Block; unabhaengig von
`--seed`). Eine abweichende Dateimenge verschiebt den Shuffle und damit den
Held-out; der Vergleich gegen J waere dann ungueltig.

**Eingebaute Kontrolle**: `tools/probes/ownership_gate_a.py` rekonstruiert die
Dateiliste genauso und prueft sie gegen das w0-Manifest, bevor es misst
(Modul-Docstring dort). Schlaegt diese Pruefung an, ist der Lauf nicht
vergleichbar -- das ist der Abbruchgrund, nicht eine Fussnote.

Zwei offene Regler, bewusst vorab festgelegt:

- **Lernrate**: 5e-5 wie im Sweep waere fuer einen ALLEINE trainierten
  Kopf sehr klein (der Kopf sieht sonst 15 Epochen lang nur die vom
  Gesamt-Loss gedaempften Schritte). **Festlegung: F1/F2 laufen mit
  `--lr 5e-4`** (Faktor 10), Begruendung: der Trunk ist eingefroren, ein zu
  grosser Schritt kann nichts ausser dem Kopf beschaedigen, und der Kopf ist
  mit 22.284 Parametern (gemessen, §6) ein winziges Modell. **Ungeprueft:**
  dieser Faktor ist eine Setzung, keine Messung. Wenn F1 auf dem
  Ownership-Val-Verlust nicht monoton faellt, ist die LR der erste Verdaechtige
  und ein LR-Nachlauf (5e-5) ist erlaubt -- als *derselbe* Arm mit anderem
  Regler, nicht als neuer Ausgang.
- **Epochen/Stopp**: `--epochs 100` mit Early Stopping wie im Sweep. Im
  Freeze-Modus beobachtet die Plateau-Erkennung die OWNERSHIP-Reihe statt der
  (konstanten) Policy-Reihe -- ohne diese Umstellung wuerde der Lauf nach
  10 Epochen still abbrechen, weil eine eingefrorene Policy per Definition
  plateaut (gebaut und getestet, §6).

`--select-by-brier` steht nur der Rezept-Symmetrie halber in der Zeile: im
Freeze-Modus ist es **wirkungslos** (der Value-Term geht gar nicht in die
Auswahl ein). Nebenwirkung, damit sie niemanden verwirrt: weil der Brier im
Freeze-Modus konstant ist, faellt der `_brierbest`-Nachlauf auf Epoche 1 --
die dabei evtl. geschriebene `*_brierbest.pth` ist eine Kopie des
Startzustands und ohne Bedeutung.

Kosten (Herleitung, keine Messung): pro Epoche derselbe Vorwaertsdurchlauf wie
im Sweep, aber Rueckwaerts nur durch 4 Tensoren -- die Epochenzeit sollte
unter der des Sweeps liegen. Anhaltspunkt: die Manifest-Zeitstempel der
Sweep-Arme (die beim START geschrieben werden) liegen bei 01:56 / 09:42 /
13:20 / 16:43 -- die Abstaende zwischen zwei Starts, also grob die Laufzeit
des jeweils vorigen Arms, betragen 3h38 und 3h23 (der erste Abstand enthaelt
zusaetzlich den Cache-Neubau). F1+F2 zusammen sind damit ein Halbtags-Posten,
nicht mehr.

## §5 Metriken, Ausgaenge und Vorab-Entscheidungsregel

**Metriken = dieselben wie Tor A, dasselbe Werkzeug**, wiederverwendet statt
neu geschrieben:

```
python tools/probes/ownership_gate_a.py --arms f1,f2 \
  --model-prefix alphazero_v21_2d_own_ --out evaluations/ownership_gate_frozen_results.json
```

(Die drei Schalter sind in dieser Sitzung additiv ergaenzt worden, Default =
der Sweep-Lauf von 2026-08-15 unveraendert; §6.) Gemessen werden also
unveraendert: Feld-Brier/AUC gegen Basisrate, Konjunktions-Brier/AUC je
Kriteriengruppe, E_k-Rangkorrelation (Spearman/Kendall) je Kriterium, getrennt
nach eigener und Gegner-Haelfte.

**Waechter (wie §9 Punkt 1, hier trivial pruefbar):** policy val_loss und
Value-Brier von F1 muessen EXAKT die Werte des Startpunkts sein (0,2139 /
0,1883). Nicht "ungefaehr" -- der Modus sichert Bit-Identitaet zu (§6). Jede
Abweichung ist ein Fehler im Modus, kein Messergebnis.

**Die vier moeglichen Ausgaenge, vorab benannt:**

| Ausgang | Bedingung (F1 gegen J-`final`) | Deutung | Konsequenz |
|---|---|---|---|
| **A -- geloest** | F1-Kopfguete ≥ J-`final` auf der Mehrheit von {Feld-AUC eigene, E_k k1, E_k k2, E_k k5} | Der Zielkonflikt war ein reines Checkpoint-Problem | F1 ist der Kopf-Checkpoint fuer den Verbraucher-Bau (PREREG_ownership_consumer.md) |
| **B -- Decke bestaetigt** | F1 bleibt auf der Mehrheit dieser vier Groessen unter J-`final`, aber deutlich ueber J-`_best` | Der Trunk MUSSTE sich bewegen; Einfrieren kauft die Policy mit Kopfguete | Kein F1-Ausliefern. Naechster Hebel: gemeinsames Training MIT ownership-bewusstem Auswahlkriterium (jetzt gebaut) oder Teil-Einfrieren |
| **C -- wirkungslos** | F1 ≈ J-`_best` (Kopf lernt kaum dazu) | Der Kopf allein kann nichts holen | Erst LR pruefen (§4), dann Ausgang B behandeln |
| **D -- Modus defekt** | Waechter verletzt (policy/value nicht bit-identisch) | Fehler im Werkzeug | Kein Ergebnis, Fehler suchen |

**Der Deckel-Vorbehalt als eigener Ausgang** (PREREG_provocation.md §10
Punkt 2): F2 beantwortet ihn getrennt von F1. F2s Trunk hat NIE einen
Ownership-Gradienten gesehen.

- **F2 ≈ F1** → der Trunk brauchte die Ownership-Gradienten nie; die
  Kopfguete steckt vollstaendig in den vorhandenen Merkmalen. Dann ist der
  Kopf ein reiner Auslese-Aufsatz und kann jederzeit auf JEDEN Champion
  aufgesetzt werden, ohne dessen Spielstaerke anzutasten -- die billigste
  aller Welten fuer den Verbraucher-Bau.
- **F2 deutlich unter F1** → die eine gemeinsame Epoche in `w05_best` hat den
  Trunk bereits messbar ownership-tauglicher gemacht; der Trunk ist also Teil
  der Kopfguete, und "Kopf allein" hat eine echte Decke. Zusammen mit Ausgang
  B ist das die Aussage "gemeinsam trainieren, aber richtig auswaehlen".

**Kein Staerke-Verdikt.** Wie §9 Punkt 3: dieser Lauf waehlt einen
Kopf-Checkpoint, er ist KEIN Gating, kein Champion-Anspruch, keine
Elo-Aussage. Einzel-Seed (2), damit die Paarung zu J haelt --
Seed-Varianz-Vorbehalt unveraendert gueltig.

## §6 GEBAUT in dieser Sitzung (Vergangenheitsform, mit Pruefstelle)

Vorab gepruefte Bestandslage (Auftrag "Rad nicht neu erfinden"): die aus der
Historie erinnerten Teil-Trainingsmodi `--skip-phase1` / `--value-only` /
`--value-hidden` existieren in `train.py` **nicht** -- sie stehen
ausschliesslich in `archive/history.md` und beschreiben eine
Zwei-Phasen-`train.py`, die es heute nicht mehr gibt; `--value-only` lebt nur
noch in `self_play.py` als SELF-PLAY-Modus, nicht als Trainingsmodus.
Vorhanden und wirklich verwandt war nur `--no-head-warmstart`
(`head_warmstart.py`) -- das steuert, welche Gewichte beim Warm-Start
UEBERNOMMEN werden, nicht, welche trainiert werden, und traegt hier also
nicht. Eine Phasen-/Freeze-Mechanik gab es nicht; sie ist neu.

1. **`freeze_trunk.py`** (neu, Repo-Root, Muster `head_warmstart.py`):
   `validate_freeze_args` (harte Vorab-Validierung), `TrunkFreeze`
   (requires_grad + BatchNorm-Riegel + Optimizer-Parameter + `backward_ok`),
   `OwnershipValLoss` (maskierter BCE, identische Formel wie der
   Trainings-Term), `plateau_series_for`.
2. **`train.py --freeze-trunk`** (additiv): Validierung vor jedem Daten-Laden,
   Einfrieren nach `model.to(device)`, Optimizer nur ueber die trainierbaren
   Parameter, **Auswahlkriterium = Ownership-Val-Verlust** statt
   `val_combined`, Plateau-Erkennung auf der Ownership-Reihe, Log-Spalte
   `Own-Val=… ⬅ AUSWAHLKRITERIUM`, Checkpoint-Felder `freeze_trunk` und
   `final_ownership_val_loss`, `selected_by =
   "ownership_val_loss(freeze-trunk, …)"`. Ohne Flag aendert sich nichts;
   der Ownership-Val-Verlust wird bei jedem Lauf mit Gewicht > 0 zusaetzlich
   mitgeloggt (kein Gradient, keine Auswahlwirkung).
3. **Der BatchNorm-Riegel ist tragend, nicht Deko.** `requires_grad=False`
   allein reicht NICHT: die BatchNorm-Buffer (`running_mean`/`running_var`)
   haben kein `requires_grad` und wandern im Train-Modus weiter. Gemessen
   (`tools/freeze_trunk_selfcheck.py`, Suite NAIV): ohne Riegel driftet der
   Policy-Ausgang nach 4 Schritten um max. 2,19e-2 (flach) bzw. 2,35e-2 (2D)
   -- MIT Riegel ist er bit-identisch.
4. **Sanity-Test gebaut** (`tools/freeze_trunk_selfcheck.py`, GRUEN, ohne
   Korpus/GPU in Sekunden lauffaehig): policy/value/moon/points/
   points_logits/value_wdl_logits/opp_points/endgame nach 4 echten
   Optimizer-Schritten `torch.equal`-identisch, in BEIDEN Modellklassen; alle
   BatchNorm-Buffer (6 flach / 12 in 2D) unveraendert; Gegenprobe
   "ownership HAT sich geaendert" (max |Δ| 5,8e-1 bzw. 6,6e-1), damit die
   Gleichheit nicht trivial erfuellt ist; Kontroll-Suite ohne Freeze
   (policy aendert sich, BN-Statistiken wandern); vier Guard-Faelle; die
   Meter-Formel gegen eine von Hand aufgestellte Referenz. Gemessene
   Groessen des eingefrorenen Modells (2D, Testbreite): 4 trainierte
   Tensoren / 22.284 Parameter gegen 42 eingefrorene / 236.256.
5. **`tools/probes/ownership_gate_a.py` wiederverwendbar gemacht** statt neu
   geschrieben: `--arms`, `--model-prefix`, `--out`, alle mit dem bisherigen
   Verhalten als Default; fehlt ein `final`-Checkpoint, wird er uebersprungen
   statt zu crashen.
6. **Groessen-Ratsche**: die train.py-Zeile in `tools/size_baseline.json`
   wurde bewusst neu gelegt (137.661 → 143.584 B). Ausweg (a) der Regel
   (Auslagern in ein Modul) ist genutzt -- der Loewenanteil liegt in
   `freeze_trunk.py`; die verbleibenden ~3,9 KB Integration in `train.py`
   ueberschreiten die 2-%-Toleranz trotzdem. Nur DIESE eine Zeile wurde
   angefasst, nicht `--update-size-baseline` global (das haette die
   Working-Tree-Staende anderer Dateien stillschweigend mit-legitimiert).

**NICHT gebaut / bewusst offen**: kein Trainingslauf gestartet, kein
Teil-Einfrieren (nur "alles ausser Kopf"), kein zweiter Kopf-Aufsatz, keine
Aenderung am Verbraucher.

## §7 ERGEBNIS F1 (2026-08-16): Zielkonflikt zur Haelfte geloest, Decke real

Lauf: `--freeze-trunk --load v21_2d_own_w1_best --ownership-weight 1,0
--lr 5e-4`, Early Stop Epoche 15 (Ownership-Plateau ab Ep. 10). Auswertung
mit `tools/probes/ownership_gate_a.py` auf demselben Held-out (820 Partien);
Rohzahlen `evaluations/ownership_gate_a_f1.json`. Zahlen vom Koordinator
nachgerechnet.

| Stand | Ep | policy val | value Brier | Feld-AUC | E_k k1 | k2 | k5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| w1 `_best` (= was wir sonst ausliefern wuerden) | 1 | 0,2141 | 0,1884 | 0,726 | 0,180 | 0,276 | 0,277 |
| **F1 (eingefroren)** | 15 | **0,2141** | **0,1884** | **0,780** | **0,280** | **0,314** | **0,345** |
| w1 `final` (gemeinsam, ueberangepasst) | 15 | 0,3018 | 0,1905 | 0,870 | 0,361 | 0,354 | 0,466 |

**Der Freeze-Riegel haelt exakt**: policy val_loss und value-Brier sind auf
die vierte Nachkommastelle identisch zum Startpunkt -- die Zusicherung des
Modus ist damit auch am echten Lauf belegt, nicht nur im Selbsttest.

**Ausgang 1 (Zielkonflikt geloest): TEILWEISE.** F1 hebt die Kopfguete
deutlich ueber den Checkpoint, den wir sonst nehmen muessten (Feld-AUC
+0,054; E_k k5 0,277 -> 0,345, also +25 %) -- und zwar zu **Kosten von
exakt null** auf der Spielstaerke-Seite.

**Ausgang 2 (Decke bestaetigt): JA, und zwar messbar.** F1 erreicht
w1-`final` nicht (0,780 gegen 0,870). Der Nutzer-Vorbehalt aus
PREREG_provocation.md §10 Punkt 2 ist damit bestaetigt: fuer die letzte
Wegstrecke MUSS sich der Trunk bewegen, der Kopf allein reicht nicht.

**Aufschlussreich ist, WO die Decke sitzt** (Konjunktions-AUC, F1 gegen
w1-final): die geometrischen Zielkriterien verlieren wenig -- Zeilen −0,015,
Spalten −0,065, Diagonalen −0,064, Ecken −0,062 --, aber die
FARB-abhaengigen brechen ein: farbenreiche Reihen −0,213, Wild-Layout −0,189.
Deutung (als Herleitung markiert): der eingefrorene Trunk transportiert die
Geometrie, die der Kopf braucht, aber nicht die Farbstruktur; k7 ist ohnehin
laut `neural_net.py:954` aus Ownership prinzipiell nicht lernbar und
`layout_wild` ist ein Hilfsziel. **Fuer die Kriterien, die der Verbraucher
tatsaechlich nutzt (k1/k2/k5), ist der Verlust also klein.**

### §7.1 Empfehlung: die Arena entscheiden lassen, nicht die Offline-Zahl

Statt F1 und w1-`final` offline gegeneinander abzuwaegen -- der eine hat den
besseren Kopf, der andere die intakte Policy, und beide Groessen sind
offline nicht ineinander umrechenbar -- gehen **BEIDE als Checkpoint-Arme in
Tor C** (PREREG_ownership_consumer.md §5 Punkt 5). Der Regler-Sweep misst
dann in derselben Arena, was die Kombination aus Kopfguete und Policy-Staerke
wirklich wert ist. Das ist die einzige Messung, die die Frage beantworten
kann, und sie kostet nur einen zusaetzlichen Arm.

Begruendung gegen die naheliegende Abkuerzung "nimm w1-final, der Kopf ist
besser": der Policy-Abfall 0,2141 -> 0,3018 ist real und gross (+41 %), und
Policy-Guete ist im Projekt arena-validiert (Orakel-Metriken 7/7). Ihn gegen
einen Kopf-Vorsprung zu tauschen, ohne zu messen, waere genau die Sorte
Abwaegung nach Gefuehl, die REGEL 0 verbietet.

### §7.2 Offen, nicht verfolgt

Zwischen "Trunk ganz eingefroren" und "Trunk laeuft 15 Epochen mit" liegt ein
ungetesteter Mittelweg: sanftes gemeinsames Nachtrainieren mit kleiner LR und
Early Stop auf dem Ownership-Verlust, oder ein Teil-Freeze (nur Policy-Kopf
fest, Trunk beweglich). Das ist der erste Kandidat, falls Tor C zeigt, dass
die Kopfguete tatsaechlich traegt und die Decke wehtut. **F2 (Deckel-Sonde
vom Champion) wird dadurch NICHT ueberfluessig** -- sie beantwortet die
andere Haelfte: ob ein Trunk, der nie einen Ownership-Gradienten gesehen hat,
ueberhaupt so weit kommt wie F1.
