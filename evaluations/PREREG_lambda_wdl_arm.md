# Vorregistrierung: λ-Misch-Value-Target in der WDL-Aera (Hypothesen-Arm)

**Angelegt 2026-08-08, VOR dem Training.** Nutzer-Go am selben Tag
("starte den lambda arm").

## Status der Hypothese (ehrlich)

Der einzige arena-signifikante λ-Befund (λ=0,7 gewinnt 227:173 im
v18only-Regime, 66% root_q-Mix) stammt aus der **tanh-/Margen-Aera**.
Nutzer-Einwand 2026-08-08: ueber die WDL-Grenze ist das KEIN
Replikationsargument (der Mechanismus -- Beimischung in ein gestauchtes
Margen-Ziel unter MSE -- existiert so nicht mehr). Der Arm laeuft daher
als **neues Experiment mit offener Erwartung**. Verbleibende
Motivation: root_q ist jetzt skalengleich zum Ziel (beides
[0,1]-Gewinnwahrscheinlichkeit), λ mischt also zwei Groessen derselben
Art -- die Vorbedingung, die in der tanh-Aera fehlte.

## Arm (EIN Faktor)

`lam07_wdl_s2` = exaktes Champion-Rezept (warm `v19_2d_opp_best`,
Seed 2, lr 5e-5 cosine, 2d, wdl, opp-Kopf, KEIN endgame-Kopf, KEIN
ranking-loss) + `--value-target-lambda 0.7`. Fenster = v20-Fenster
gepinnt (identisch zum Champion und zu t35b_s2:
MOSAIC_DATA_EXCLUDE gegen v20wdlsw + v19wdlann) -> Cache-HIT, kein
Rebuild. Baseline = Champion (gleiches Fenster, λ=1,0).

**Zu protokollieren**: die vom Tool ausgegebene tatsaechliche
root_q-Fraktion (`apply_value_target_lambda` -> train_root_q_frac).
Erwartung ~57% (v16/v17 tragen kein root_q); der Alt-Sieg lag bei 66%,
das Alt-H0 bei 44% -- der Arm liegt also im uninformativen Zwischen-
bereich der ALTEN Kurve, was ihn als Aera-Replikation ohnehin
disqualifiziert (s.o.) und nur als WDL-Erstmessung zaehlt.

## Entscheidungskette

1. Offline deskriptiv: val_brier/Platt/Brier-Alt-Set (Snapshot),
   R5-Steigung. KEINE Entscheidung daraus (Aufloesungsgrenze 0/4).
2. Standard-Gating vs `v20_2d_opp_brierbest`, 200 Paare,
   Fruehstopp-Regel (kein Entscheid <150 Paare ohne
   Frisch-Seed-Replikation), no-promote.
3. H1 -> λ=0,7 wird Rezept-Kandidat (neben `--endgame-head`), Promotion
   nach Nutzer-Entscheid. H0 -> λ in der WDL-Aera GESCHLOSSEN
   (Alt-Befund gilt dann als aera-gebunden), Metriken in die
   #29-Buchfuehrung.
