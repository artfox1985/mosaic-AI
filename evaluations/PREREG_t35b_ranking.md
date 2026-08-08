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

## ERGEBNIS (2026-08-08): Orakel-Vorpruefung NEGATIV -> kein Gating

Training `t35b_s2` (Champion-Rezept + ranking-loss-weight 1.0, v20-Fenster
gepinnt): Early Stop E15, brierbest E?, Value-Brier 0,1963 (Champion
0,1967 -- Paritaet). Der Ranking-Loss ARBEITET mechanisch: 0,3807 ->
0,3741 ueber die Epochen, Val-Ranking-Accuracy **0,740**. Policy-Val-Loss
sogar besser als der Champion (0,47 vs 0,49).

**Orakel-Vorpruefung (frozen_v1 + validierte Labels, 7/7-Instrument)**:
Prior-Masse auf Orakel-Top-3 **0,6882 vs 0,7098** (klar schlechter),
Kendall-Tau 0,3586 vs 0,3588 (gleichauf/minimal schlechter). Damit ist
die vorregistrierte Bedingung "BEIDE schlechter -> KEIN Gating"
erfuellt: **Arena gespart, #35b GESCHLOSSEN.**

**Lehrsatz (wichtig fuers Archiv)**: der Ranking-Loss verbessert
ausgerechnet die Metrik, die NICHT arena-validiert ist
(Policy-Val-CE auf dem Besuchs-Softmax-Ziel), und verschlechtert die
arena-validierte (Orakel-Top-3-Masse). Er richtet die Policy an der
Geschwister-Q-Rangfolge aus -- und die zeigt offenbar teilweise woanders
hin als der Orakel-Referenzzug. Wiedervorlage nur mit anderer
Referenz-Rangfolge (z.B. Orakel-Q statt root_child_q) oder kleinerem
Gewicht; Knopf bleibt (Default 0), Schema 19 bleibt (Felder kosten 36 B).
