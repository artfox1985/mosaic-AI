# Vorregistrierung: Task #35b -- Ranking-Loss-Arm (WDL-Aera)

**Angelegt 2026-08-08, VOR dem Training.** Implementierung committet
(a9d149a, Schema 19, --ranking-loss-weight, Default 0 bit-identisch).

## Arm

`t35b_s2` = exaktes Champion-Rezept (warm v19_2d_opp_best, Seed 2,
lr 5e-5 cosine, wdl, opp-Kopf, KEIN endgame-Kopf -- ein Faktor!) +
`--ranking-loss-weight 1.0` (der in der Implementierungs-Verifikation
getestete Wert: endlicher, fallender Loss, keine Instabilitaet;
Dosis-Folgearm nur bei Anzeichen von Policy-CE-Verdraengung).
Fenster = v20-Fenster gepinnt (MOSAIC_DATA_EXCLUDE gegen v20wdlsw +
v19wdlann); Schema-19-Cache-Neubau beim Start (~2,5h, CPU frei).

## Entscheidungskette (Policy-Seite -> validierte Praediktoren nutzbar!)

1. **Orakel-Vorpruefung** (frozen_v2 + frozen_v2_oracle_labels):
   prior_mass_on_oracle_top3 + kendall_tau vs Champion (beide Metriken
   arena-validiert 7/7). BEIDE schlechter -> KEIN Gating (prognostizierter
   Verlierer, Arena gespart), Arm dokumentiert. Sonst:
2. Standard-Gating vs Champion (Fruehstopp-Regel). H1 -> Ranking-Loss
   wird Rezept-Kandidat der naechsten Generation (wie endgame_head);
   H0 -> dokumentieren, Metriken fuer die #29-Buchfuehrung mitnehmen.
3. Deskriptiv: Ranking-Accuracy (Val), Brier-Alt-Set, Platt.
