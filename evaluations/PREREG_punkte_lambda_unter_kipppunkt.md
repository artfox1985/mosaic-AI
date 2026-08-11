# Vorregistrierung: Punkte-Optimierung mit λ UNTER dem Kipppunkt

**Angelegt 2026-08-11, Nutzer-Auftrag** — *"dann kannst auch die punkte
optimierung eintakten (inkludiert die punkteminimierung der gegner)"*.

Geht zurück auf die ältere Nutzer-Frage: *"können wir gleichzeitig unsere punkte
maximieren und die gegnerpunkte minimieren (ohne differenzrechnung der beiden,
weil sonst ist 55 vs. 50 schlechter als 30 vs 15)"*.

## 1. Warum ein geschlossener Punkt wieder aufgeht

`PREREG_punkte_blend_w.md` schloss `w>0` mit **Regel 2**: Kontrolle 321/400
(80,25 %) gegen Arm 300/400 (75,00 %), Block-Delta −5,25pp, t = −2,68.

**Beide Arme liefen bei λ = 2,0** (dort dokumentiert: Kontrolle
`w=0, lambda=2.0`, Arm `w=0.1, lambda=2.0`). Die Formel ist
(`opp_aware_points_utility`, `net_mcts.rs`):

    own_pts  = pts_raw + VALUE_OPP_EPSILON * opp_raw     // ε=0 seit Schema 20
    combined = (own_pts − lambda_aggr * opp_raw).clamp(-1, 1)

Bei λ = 1 ist das eine reine Differenz, bei λ = 2 dominiert der Gegnerterm.
**Der Kipppunkt für den Nutzer-Fall lässt sich ausrechnen** *(meine Rechnung,
nicht gemessen; `pts_raw = tanh(punkte/VALUE_SCALE)`, `VALUE_SCALE = 50`)*:

    55:50  ->  tanh(1,10) = 0,8005   gegen   tanh(1,00) = 0,7616
    30:15  ->  tanh(0,60) = 0,5370   gegen   tanh(0,30) = 0,2913
    0,8005 − 0,7616·λ  >  0,5370 − 0,2913·λ   <=>   0,2635 > 0,4703·λ
    =>  λ < 0,56

**Gemessen wurde bei λ = 2,0 also nicht "helfen Punkte", sondern "hilft es,
30:15 gegenüber 55:50 zu bevorzugen".** Dass das schadet, bestätigt die Formel,
nicht die Nutzlosigkeit des Kanals. Der Bereich λ < 0,56 — der einzige, in dem
die Formel das tut, was der Nutzer verlangt hat — ist **nie gemessen worden**.

Das ist ausdrücklich KEINE Aufhebung von Regel 2 für λ ≥ 1, sondern die
Feststellung, dass ihr Gültigkeitsbereich schmaler ist als die Zeile suggeriert.

## 2. Vorbedingung: GEPRÜFT, der Champion trägt den opp-Kopf

`combined` braucht `opp_points`; ohne den Kopf greift der Kurzschluss
`if opp_points.is_empty()`. Geprüft an den ONNX-Ausgängen:

    v21_2d_brierbest      -> policy, value, moon, points, ownership,
                             value_wdl_logits, opp_points, endgame_margin
    v20_2d_opp_brierbest  -> ... opp_points

Der Champion trägt ihn. **Kein Training nötig**, der Sweep läuft am Bestand.

## 3. Arme — EIN Faktor, und ein Arm ist schon gemessen

Instrument `tools/paired_arena_env_ab.py` im **Mehr-Var-Modus**
(`--env-name MOSAIC_POINTS_UTILITY_W,MOSAIC_AGGR_LAMBDA`), Champion
`v21_2d_brierbest`@400 vs Heuristik@150(dyn), **Basis-Seed 20260902, n=400,
16 Blöcke à 25** — identisch zum historischen Lauf, damit dessen Arm gepaart
mitzählt statt nur erinnert zu werden.

| Arm | `w,λ` | Status |
|---|---|---|
| Kontrolle | `0,0.1` | w=0 kurzschliesst vor λ ⇒ blanker Champion |
| **A** | `0.1,0.1` | NEU — gleiche Dosis wie der schädliche Arm, nur λ geändert |
| **B** | `0.1,0.4` | NEU — knapp unter dem Kipppunkt 0,56 |
| (C) | `0.1,2.0` | **bereits gemessen**: 300/400, weit jenseits des Kipppunkts |

Der Zuschnitt ist bewusst **einfaktoriell**: `w` bleibt auf 0,1 wie im
gemessenen Arm, nur λ wandert. Damit ist der Kontrast genau die
Kipppunkt-Hypothese und nicht zusätzlich eine Dosisfrage. Zwei neue Arme, nicht
mehr — Task-D-Präzedenz (vier Arme, alle H0) und Seed-Skala 5,75pp bei n=400.

## 4. Pflicht-Nebenmessung: die PUNKTESTÄNDE, nicht nur die Siegquote

Die Hypothese handelt von **Niveaus** (55:50 gegen 30:15). Eine Siegquote kann
nicht unterscheiden, ob ein Arm gewinnt, weil er mehr Punkte macht, oder weil er
den Gegner drückt. Deshalb je Arm zusätzlich:

- **mittlerer eigener Endstand** und **mittlerer Gegner-Endstand**
- deren **Differenz** und deren **Summe** (die Summe trennt "beide hoch" von
  "beide niedrig" — genau der Unterschied, um den es dem Nutzer geht)

`scores` liegt im Arena-Ergebnis je Partie schon vor
(`tools/paired_arena_arm_worker.py`, Modulkopf), das kostet nichts.

### Lesart

| Siegquote | Summe der Endstände | Verdikt |
|---|---|---|
| steigt | steigt oder gleich | Kanal wirkt wie gewollt ⇒ Dosis übernehmen |
| steigt | **fällt** | gewonnen durch Drücken statt Punkten — λ trotz Rechnung zu hoch, kleiner testen |
| flach | steigt | mehr Punkte, kein Siegvorteil — Kanal ist neutral, Regel 2 gilt weiter |
| flach/fällt | fällt | Regel 2 gilt auch unter dem Kipppunkt ⇒ endgültig geschlossen |

## 5. Statistik

1. Gepaart über den Spielindex, **identischer Basis-Seed 20260902** in allen
   Armen (und im historischen Arm C).
2. **Block-Ebene als Pflichtinstrument** (16 Blöcke à 25,
   `feedback_arena_block_correlation`) — Block-Delta mit SE und t berichten.
3. Exakter zweiseitiger McNemar auf den diskordanten Paaren.
4. **Bonferroni über die zwei NEUEN Arme**: α = 0,025 je Arm. Arm C zählt als
   bereits erhoben, nicht als dritter Test.
5. Frühstopp unter 150 Paaren nur mit Frisch-Seed-Replikation.

## 6. Verhältnis zu den Injektions-Sweeps

Drei getrennte Kanäle, drei getrennte Vorregistrierungen, **keine gemeinsamen
Läufe**:

- `MOSAIC_UNLOCK_SHAPING_W` — Spezialfelder (`PREREG_injektion_dosis.md`)
- `MOSAIC_WERTUNG_SHAPING_W` — Wertungsplatten-Kriterien (eigene Prereg offen)
- `MOSAIC_POINTS_UTILITY_W`/`AGGR_LAMBDA` — Basis/Platzierung, **diese Datei**

Der Punkte-Kanal ist der einzige, der auf die **93 %** des Ergebnisses wirkt
(Platzierungspunkte); die anderen zwei bedienen die Wertungsplatten. Alle drei
gleichzeitig zu drehen wäre nicht interpretierbar.

## 7. Was dieser Sweep NICHT entscheidet

- Keinen Champion-Wechsel (kein neuer Checkpoint).
- Nicht die Frage, ob der `opp_points`-Kopf als **Hilfsziel** den Rumpf
  verbessert (`PREREG_punktekopf_epsilon.md`, nie gemessen) — hier wird nur
  seine Laufzeit-Verwendung geprüft.
- Nicht `VALUE_OPP_EPSILON`: bleibt 0 (Schema 20).
