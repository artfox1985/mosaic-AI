# Vorregistrierung: Erosions-Arme A/B (Task #34, Nutzer-Go 2026-08-05)

**Angelegt VOR den Laeufen.** Befundlage: der Value-Fit des harten Ziels
erodiert nach Epoche ~2-3 (wdlhard: Brier 0,1970 -> 0,2440, Val-R²
negativ; Blend-Arm mild 0,1990 -> 0,2030; tanh-Kontrolle flach).
Diagnose: (1) Memorisierung (Train-Loss 0,60 -> 0,39 bei steigendem
Val-Brier; ~1 Bit je Partie), (2) Gradienten-Dominanz von Policy+Punkte
im Trunk (~15:1), (3) ausgelutschtes 900er-Fenster (auch Policy-Val
steigt ab E1). Der TD-Blend wirkt als Label-Smoothing-Stabilisator, ist
aber kontaminiert (Audit Befund 1).

## Arme (je Mechanismus-Hypothese EINER)

Beide: warm von `v19_2d_best`, 2D, Seed 2, Champion-Rezept (lr 5e-5,
cosine, `--select-by-brier`, doppeltes Early Stopping, VALUE_WEIGHT 0,2),
900er-Fenster, KEIN Cache-Neubau.

| Arm | Flag | Ziel | Hypothese |
|---|---|---|---|
| **A `t34_wdlsmooth`** | `--wdl-hard-only --wdl-label-smooth 0.1` | hart, Labels 0,95/0,05 | Erosion = Memorisierung; weiche Labels deckeln Konfidenz |
| **B `t34_wdldestretch`** | `--wdl-bootstrap-destretch` | Blend, Bootstrap Platt-entstaucht (A=0,0051, B=1,9269) | Blend-Stabilisator sauber statt kontaminiert |

Bekannte Naeherung (Arm B, VORAB benannt): EIN globaler Platt-Fit
(v19_2d_best, `value_calibration_fit.json` "full") fuer Bootstrap-Werte,
die von v16-v18-Generatoren stammen -- deren Fits sind aehnlich, aber
nicht identisch (Kontroll-Reihe B~1,91-1,93). Rekonstruktion
`bv = (t - 0,5y)/0,5` ist exakt (Unit-Test im Commit).

## Auswertung (VORAB festgelegt)

1. **Primaer, je Arm gegen den zugehoerigen Referenz-Arm** (A vs
   `t34_wdlhard`, B vs `t34_wdl02`): Brier-PEAK (brierbest-Epoche) und
   **Erosions-Delta** (final minus Peak). Hypothese bestaetigt, wenn das
   Erosions-Delta deutlich schrumpft OHNE schlechteren Peak.
   Aufloesungsvorbehalt: Val-Split ~900 Partien, Unterschiede < ~0,005
   Brier sind nicht interpretierbar.
2. **Platt-B** beider Arme (deskriptiv).
3. **Arena** (entscheidend, wie immer): der beste WDL-Arm des Tages
   (nach Peak-Brier + Erosionsbild) geht ins Gating gegen `t34_tanh`
   und `v19_2d_best` -- zusaetzlich zu den bereits laufenden
   wdlhard_brierbest-Gatings. Keine Promotion (Nutzer-Regel: Champion
   bleibt bis v20).
4. Seed-Vorbehalt: Einzel-Seed-Vergleiche; Kurven-FORM (Erosion ja/nein)
   gilt als robuster als Niveau-Differenzen. Bei widerspruechlichem Bild
   Replikation mit Seed 3/6 VOR jeder Uebernahme.

## Einordnung

Ergebnis fliesst ins #34-VERDIKT (Zielkonfiguration fuer v20:
hard+smooth vs entstauchter Blend vs Bestands-Blend). Aggressions-Blend-
Neukartierung ist davon getrennt und kommt erst im naechsten Korpus
(Nutzer-Entscheid 2026-08-05 nach Audit-F1).

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- beide Hypothesen bestaetigt:
Label-Smoothing (Arm A) daempft die Erosion um ~60% (wdlsmooth +0,018 vs
wdlhard +0,047), aber der entstauchte Bootstrap-Blend (Arm B,
`t34_wdldestretch`) schlaegt beide -- bester Peak (Brier 0,1971), mildeste
Erosion (+0,005), hoechstes Val-R² (0,346). Ergebnis floss direkt ins
finale #34-VERDIKT: v20-Zielkonfiguration = WDL + entstauchter
Bootstrap-Blend. Belegstelle: archive/history.md, Abschnitt "Erosions-Arme
(PREREG_task34_erosion_arms.md) -- ERGEBNIS 2026-08-05", Zeile
~9185-9200; "#34-VERDIKT (FINAL 2026-08-05)", Zeile ~9221-9229.
