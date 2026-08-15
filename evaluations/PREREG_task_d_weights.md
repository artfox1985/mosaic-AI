<!-- STATUS: ENTSCHIEDEN | Frage: Traegt ein hoeheres value_weight (0,4/0,8) oder ein hoeheres points_weight (0,25) Arena-Staerke gegen die Kontrolle `v21_2d`? | Beleg: **H0 2026-08-10, alle drei Arme** ⇒ Regel 5: `VALUE_WEIGHT=0,2` und der Punkte-Default bleiben, Punkt fuer die WDL-/2D-Aera geschlossen. vw04 208:192 (52,0%), vw08 92:108 (46,0%), pw025 68:82 (45,3%, SPRT-H0 nach 75 Paaren). Bild monoton: 0,4 nicht besser, 0,8 schlechter -- der aus der MSE-Aera geerbte Wert liegt offenbar nahe am Optimum. `evaluations/paired_gating_t_d_{vw04,vw08,pw025}_vs_v21.json` -->

# Vorregistrierung: Task D -- Loss-Gewichte (value_weight / points_weight)

**Angelegt 2026-08-09, NACH dem Training von `t_d_vw04` aber VOR jedem
Gating und vor jeder Auswertung.** Nachgezogene Vorregistrierung: die
Regeln standen bisher nur in einer STATUS-Tabellenzeile, obwohl Task D
ein mehrarmiges Experiment mit Arena-Entscheid ist. Was hier steht, ist
inhaltlich der Nutzer-Zuschnitt vom 2026-08-08 ("ARENA entscheidet"),
nur praezise und vollstaendig. **Kein Arm ist bisher gegated**, die
Regeln sind also noch unbelastet von Ergebnissen. Offengelegt: die
OFFLINE-Zahl von `t_d_vw04` war beim Schreiben bekannt (val_brier
0,1863, brierbest Epoche 4) -- sie ist per Zuschnitt DESKRIPTIV und
darf keine Entscheidung tragen, genau deshalb steht sie hier.

## Frage

`VALUE_WEIGHT = 0,2` stammt aus der MSE-Aera und wurde beim Wechsel auf
den BCE-/WDL-Kopf nie nachgezogen. Gemessene Loss-Anteile im aktuellen
Rezept: **Policy 90,1% / Value 6,5% / Aux 3,4%** -- obwohl die
Hybrid-Attribution (2x2, 400 Sims) die STAERKE dem VALUE-Kopf
zuschreibt. Nach oben ist das Gewicht ungemessen.

## Arme (alle auf dem v21-Fenster, sonst identisches Champion-Rezept)

Basis fuer alle: `--load v20_2d_opp_brierbest --epochs 100 --lr 5e-5
--lr-schedule cosine --seed 2 --value-target-variant nortv --encoder 2d
--opp-points-head --value-head wdl --endgame-head`, dazu ZWINGEND
`MOSAIC_DATA_EXCLUDE` (v21-Regex) **und**
`MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v21.json`
(Zwei-Variablen-Regel, siehe STATUS -- der zweite Knopf wurde bei vw08
einmal vergessen und haette den Arm wertlos gemacht).

| Arm | Aenderung | Stand |
|---|---|---|
| **Kontrolle** | `v21_2d` selbst (value_weight 0,2 / points_weight Default) | existiert, KEIN eigenes Training noetig |
| `t_d_vw04` | `--value-weight 0.4` | trainiert 2026-08-09, brierbest E4 |
| `t_d_vw08` | `--value-weight 0.8` | laeuft 2026-08-09 |
| `t_d_pw025` | `--points-weight 0.25` | offen |

Die Kontrolle ist das v21-Training selbst -- damit drei statt vier
Trainings, und der Vergleich ist ein EIN-FAKTOR-Vergleich (nur das
jeweilige Gewicht), weil Fenster, Startpunkt, Seed und alle anderen
Schalter identisch sind. Verifikations-Pflicht je Arm: die Cache-Zeile
muss `Lade HDF5-Cache (2651 Dateien)` lauten; steht dort `Lade Daten
aus`, ist der Arm NICHT vergleichbar und wird verworfen, nicht
"trotzdem mitgenommen".

## Entscheidung: die ARENA, nicht der Brier

Begruendung (Nutzer 2026-08-08, jetzt stehende Regel): der Brier-Abstand
zwischen diesen Armen liegt voraussichtlich unter der
Offline-Aufloesungsgrenze (~0,015 fuer Value-R², Seed-Skala beim Brier
~0,0006), und ein Gating kostet ~1,5h CPU gegen ~3,5h GPU je Training --
die Arena ist billiger UND das einzige arena-validierte Instrument auf
der Value-Seite.

1. **Je Arm ein Gating gegen die Kontrolle `v21_2d`**, `tools/paired_gating.py`,
   Standard-SPRT (H0 0,5 / H1 0,65, α=β=0,05, Deckel 200 Paare),
   400 Sims beidseitig, je Arm ein eigener Basis-Seed (dokumentiert).
2. **Fruehstopp-Regel gilt**: eine H1-Entscheidung unter 150 Paaren
   braucht eine Frisch-Seed-Replikation, sonst ist sie kein Verdikt
   (Lehre t12-Falsch-Positiv).
3. **Score-Analyse auf Block-Ebene** (stehende Regel: Paar-SEs
   unterschaetzen massiv).
4. **Ein Sieger tritt zusaetzlich gegen den Champion an**
   (`v21_2d_brierbest`). Erst diese Kante entscheidet ueber eine
   Rezept-Aenderung; ein Sieg gegen die Kontrolle allein aendert das
   Standard-Rezept NICHT.
5. **Alle H0** ⇒ `VALUE_WEIGHT = 0,2` und der Punkte-Default bleiben,
   der Punkt gilt fuer die WDL-/2D-Aera als geschlossen. Das ist ein
   vollwertiges Ergebnis: es belegt, dass der aus der MSE-Aera geerbte
   Wert im neuen Regime nicht schaedlich ist.
6. **Zwei Arme gewinnen** ⇒ es wird NICHT kombiniert (vw+pw zusammen
   waere ein neuer, unvermessener Arm); der staerkere Arm geht in die
   Champion-Kante, die Kombination ist allenfalls ein spaeterer eigener
   Task.

### KLARSTELLUNG vor dem ersten Gating (2026-08-09) -- Zweideutigkeit in meinem eigenen Zuschnitt

Beim Ansetzen des ersten Gatings faellt auf, dass "Kontrolle = `v21_2d`
selbst" nicht eindeutig ist: es gibt drei v21-Checkpoints
(`v21_2d` = letzte Epoche, `v21_2d_best` = val_combined-bester,
`v21_2d_brierbest` = Brier-bester). Die ARME werden alle nach
`_brierbest` ausgewaehlt. Gegen `v21_2d` (letzte Epoche) zu gaten wuerde
die Gewichtsaenderung mit der CHECKPOINT-AUSWAHLREGEL konfundieren --
zwei Faktoren statt einem.

**Festlegung: Kontrolle ist `v21_2d_brierbest`** -- identische
Auswahlregel auf beiden Seiten, damit bleibt es ein Ein-Faktor-Vergleich.

**Folge: Regel 4 ist damit gegenstandslos und wird gestrichen.** Sie
verlangte, ein Sieger trete "zusaetzlich gegen den Champion
(`v21_2d_brierbest`)" an -- das ist derselbe Gegner. Ein Sieg gegen die
Kontrolle IST damit ein Sieg gegen den amtierenden Champion, also der
strengste moegliche Test; ein zweiter Schritt entfaellt. Das macht den
Sweep strenger, nicht laxer: es gibt keine Zwischenstufe mehr, gegen die
ein Arm "gewinnen" koennte, ohne den Champion zu schlagen.

Die uebrigen Regeln (Standard-SPRT, Fruehstopp-Replikation,
Block-Ebene, alle-H0-Lesart, keine Kombination zweier Sieger) bleiben
unveraendert. Diese Klarstellung erfolgt VOR jedem gefahrenen Gating.

## Deskriptiv mitgefuehrt (KEINE Entscheidungsmetrik)

Je Arm, fuer die #29-Buchfuehrung (Offline-Praediktor braucht
arena-ENTSCHIEDENE Paare -- Task D liefert bis zu drei davon):
Alt-Messset-Brier (`tools/t36_curve_eval.py --snapshot-dir
data/altmess_90files`), Orakel-Metriken auf frozen_v2
(`tools/oracle_metrics.py`), Platt-B, R5-Plattensteigung. Diese Zahlen
werden VOR dem jeweiligen Gating erhoben und protokolliert, damit die
#29-Validierung eine echte Vorhersage pruefen kann und keine
Nachher-Erzaehlung.

### Erhobene deskriptive Werte (protokolliert VOR dem jeweiligen Gating)

| Arm | Alt-Messset-Brier (90-Dateien-Snapshot, 146.187 Zustaende / 900 Partien) |
|---|---|
| Kontrolle `v21_2d_brierbest` | **0,18636** |
| `t_d_vw04_brierbest` | **0,18488** (−0,00148, also besser) |

Gueltigkeits-Nachweis der Messung: der Kontrollwert 0,18636 reproduziert
EXAKT den bei der Champion-Promotion protokollierten Alt-Set-Brier --
Snapshot, Werkzeug und Pfad sind also unveraendert.

Einordnung, ausdruecklich OHNE Entscheidungscharakter: die Seed-Skala
dieser Kennzahl liegt bei ~0,0006 (aus dem v20-Kontroll-Seed-Paar), der
Abstand ist damit rund 2,5 Seed-Sigma. Das ist ein deskriptiver Hinweis
zugunsten von `value_weight=0,4`, **kein Verdikt** -- die Offline-Metrik
hat unterhalb von ~0,015 Value-R² 0/4 richtig vorhergesagt, und genau
deshalb entscheidet hier die Arena (Punkt 1-4 oben). Der Wert ist
festgehalten, damit die #29-Buchfuehrung spaeter eine echte VORHERSAGE
pruefen kann: Brier sagt vw04 vorn -- stimmt das Gating zu?

## Kosten

3 Trainings a ~3,5h GPU (davon 1 fertig, 1 laeuft) + bis zu 3 Gatings a
~1,5h CPU + ggf. 1 Champion-Kante. Die Gatings konkurrieren mit
E3b Stufe 2 und ISMCTS-k um die CPU-Bahn und laufen daher sequenziell.

---
## ERGEBNIS Arm `t_d_vw04` (value_weight 0,4) -- 2026-08-09: H0

Gepaartes Gating gegen die Kontrolle/den Champion `v21_2d_brierbest`,
400 Sims beidseitig, Basis-Seed 20260830, Standard-SPRT.
Belegstelle `evaluations/paired_gating_t_d_vw04_vs_v21.json`.

| Groesse | Wert |
|---|---|
| Ergebnis | **208:192** (52,0%) aus 400 Spielen / 200 Paaren |
| SPRT | **kein Entscheid**, harter Deckel erreicht (LLR -1,862, Schranken ±2,944) |
| Exakter Paar-Vorzeichentest | p=0,4657 |
| Gepaarte Differenz je Paar | +0,080, 95%-KI **[-0,108, +0,268]** |

**Entscheid: H0 fuer diesen Arm** -- `value_weight=0,4` zeigt keinen
Staerkevorteil. Der Punktschaetzer liegt zwar in seine Richtung (52%),
das KI schliesst die Null aber klar ein.

**Und damit ist die Brier-Vorhersage geprueft und NICHT bestaetigt.**
Der Alt-Set-Brier hatte vw04 mit 0,18488 gegen 0,18636 vorn gesehen,
rund 2,5 Seed-Sigma. Die Arena bestaetigt das nicht. Zur Fairness: sie
WIDERLEGT es auch nicht -- die Richtung stimmt, nur die Groesse ist
weit von Signifikanz entfernt. Fuer die #29-Buchfuehrung heisst das:
dieses Paar ist **UNENTSCHIEDEN** und zaehlt damit NICHT als
arena-entschiedenes Paar. Die Prereg-Erwartung, Task D liefere "bis zu
drei" solcher Paare, ist damit in Frage gestellt: kommen alle drei Arme
unentschieden zurueck, liefert der Sweep KEINES -- ein Planungsmangel,
der hier festgehalten wird, weil #29 seit Wochen auf Power wartet.

**Keine Verlaengerung auf 400 Paare.** Eine solche Regel existiert, aber
sie wurde ausdruecklich NUR fuer das v21-Champion-Gating vorab
festgelegt ("bei UNDECIDED_CAP mit positiver Punktschaetzung
Verlaengerung auf 400 Paare am selben Basis-Seed"). Task D hat keine
Verlaengerungsregel. Sie jetzt einzufuehren, NACHDEM der positive
Punktschaetzer sichtbar ist, waere genau die nachtraegliche
Regelanpassung, gegen die Vorregistrierungen da sind. Ob die
Verlaengerung zur STEHENDEN Regel wird, ist eine Grundsatzfrage fuer
kuenftige Gatings und wird nicht an diesem Arm entschieden.

## ERGEBNIS Arm `t_d_vw08` (value_weight 0,8) -- 2026-08-09: H0 (SPRT-Entscheid)

Gleicher Aufbau, Basis-Seed 20260831. Belegstelle
`evaluations/paired_gating_t_d_vw08_vs_v21.json`.

| Groesse | Wert |
|---|---|
| Ergebnis | **92:108** (46,0%) aus 200 Spielen / 100 Paaren |
| SPRT | **H0 angenommen** nach 100 Paaren (LLR -4,740 <= untere Schranke -2,944) |
| Exakter Paar-Vorzeichentest | p=0,3123 |
| Gepaarte Differenz je Paar | -0,160, 95%-KI [-0,431, +0,111] |

Saubererer Ausgang als bei vw04: hier hat der SPRT wirklich entschieden
statt am Deckel zu verhungern. Zur Lesart: "H0 angenommen" heisst **kein
Beleg, dass vw08 besser ist** -- nicht "vw08 ist schlechter". Das KI
schliesst die Null ein, auch wenn der Punktschaetzer negativ liegt.

**Fruehstopp-Replikation nicht erforderlich**: Regel 2 verlangt sie fuer
eine **H1**-Entscheidung unter 150 Paaren, weil dort die
Falsch-Positiven teuer sind (Lehre t12). Ein H0-Stopp behauptet keinen
Champion-Wechsel und traegt dieses Risiko nicht.

**Block-Ebene hier nicht auswertbar**: der Fruehstopp nach 100 Paaren
laesst nur 4 Bloecke a 25 -- zu wenig fuer eine belastbare Block-SE. Das
wird so festgehalten statt eine Scheinzahl zu rechnen; die
Stopp-Entscheidung ist ohnehin der vorregistrierte SPRT.

### Zwischenstand des Sweeps (2 von 3 Armen)

| Arm | value/points | Quote gegen Champion | Verdikt |
|---|---|---|---|
| `t_d_vw04` | vw 0,4 | 52,0% (208:192) | H0, Deckel |
| `t_d_vw08` | vw 0,8 | 46,0% (92:108) | H0, SPRT |
| `t_d_pw025` | pw 0,25 | trainiert noch | offen |

Bild bisher **monoton und in sich konsistent**: 0,2 (Kontrolle) ist nicht
schlechter als 0,4, und 0,8 liegt darunter. Das stuetzt die Lesart von
Regel 5 -- der aus der MSE-Aera geerbte Wert 0,2 ist im WDL-Regime nicht
bloss unschaedlich, sondern liegt offenbar nahe am Optimum. Endgueltig
erst nach `pw025`.
