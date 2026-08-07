# Vorregistrierung: Suchpfad-Nachmessungen (Floor-Gewicht, m-Formel, τ-Annealing)

**Angelegt 2026-08-06, VOR allen Laeufen** (Nutzer-Auftrag "plan ein in
die pipeline"; Quelle: Suchpfad-Verifikations-Inventar). Ausfuehrung
NACH dem v20-Champion-Gating (laufende Kampagne wird nicht angefasst,
Arena-Maschine ist dann warm). Regeln nach Sichtung von
Zwischenergebnissen nicht mehr aenderbar.

## Vorarbeit (einmalig, im Post-Kampagnen-Fenster)

Zwei Laufzeit-Knoepfe nach dem #30-Muster (Env-Var, Default =
byte-identisches Bestandsverhalten), Wheel-Neubau erst moeglich, wenn
die Self-Play-Prozesse beendet sind (DLL-Lock):
- `MOSAIC_FLOOR_SHAPING_W` (Default 0.3) -- ueberschreibt
  FLOOR_SHAPING_WEIGHT (net_mcts.rs:373).
- `MOSAIC_GUMBEL_TOP_M` (Default 0 = Formel `gumbel_top_m_for_budget`)
  -- fester Override der Wurzelbreite.
Beide mit Paritaets-Nachweis (Default-Lauf bitgleich zu vorher) und
Engine-Tests vor Einsatz.

## AMENDMENT Instrument (2026-08-07, VOR dem ersten Messlauf)

Die urspruengliche Formulierung "Modell auf BEIDEN Seiten identisch, nur
Env verschieden" ist mit den gebauten Knoepfen NICHT ausfuehrbar: die
Env-Vars sind prozessweit (OnceLock, einmalig gelesen), ein
Netz-vs-Netz-Match traegt den Wert also zwingend auf BEIDEN Seiten --
ein Spiegelmatch desselben Modells misst dann nichts. Ersatz-Instrument
= das etablierte Zwei-Arm-Muster (#30-Skalen-Korrektur,
Floor-Erstvalidierung): **je Arm ein eigener Prozess (Env gesetzt),
Champion-Netz vs Heuristik@150(dyn) -- die Heuristik liest keinen der
beiden Knoepfe, die Differenz attribuiert sauber auf die Netz-Seite.**
Identische Basis-Seeds je Spielindex ueber die Arme, fixed-n, exakter
zweiseitiger McNemar auf den diskordanten Paaren (Formel wie
paired_gating.py). Entscheidungsregeln der Messungen unveraendert.

## Messung 1 — Floor-Gewicht-Sweep in der WDL-Aera (billig, zuerst)

**Frage**: Ist 0,3 noch der richtige Wert, nachdem sich die
Value-Spreizung seit der Kalibrierung ~2x geaendert hat (WDL-Aera)?
Der 0,15/0,6-Sweep steht seit Juli als "optional" offen.
**Design (gem. Amendment oben)**: Modell = v20-Champion
(`v20_2d_opp_brierbest`, Gating gewonnen). DREI Arme a 200 Spiele
(Champion@400 vs Heuristik@150dyn, identische Seeds ueber die Arme):
W=0,3 (Kontrolle), W=0,15, W=0,6. Vergleiche 0,3-vs-0,15 und
0,3-vs-0,6 per gepaartem McNemar. Optional Bestaetigung W=0,0
(Re-Validierung des Features am neuen Kopf).
**Entscheid**: Wechsel des Defaults nur bei SPRT-H1 GEGEN 0,3 plus
Frisch-Seed-Replikation (Statistik-Regel 3); sonst bleibt 0,3 und der
Punkt gilt als WDL-re-validiert.
**Kosten**: 2-3 Gatings a ~1-2h.

## Messung 2 — m-Formel bei niedrigen Sims (billig)

**Frage**: Kostet die Budget-Formel (150 Sims -> m=9) Staerke gegenueber
fester Breite m=16? Relevanz: Schwarm-Klasse kuenftiger Kampagnen und
alle Niedrig-Sims-Presets (GUI/#31).
**Design (gem. Amendment oben)**: ZWEI Arme a 200 Spiele
(Champion@150 vs Heuristik@150dyn, identische Seeds), Arm A
`MOSAIC_GUMBEL_TOP_M=0` (Formel, m=9), Arm B `=16`; gepaarter
McNemar. Sekundaer identisch @64 Netz-Sims (m=4 vs 16), falls A
signifikant.
**Entscheid**: H0 -> Formel bestaetigt (Abweichungsnotiz der
v20-Kampagne wird geschlossen). Signifikanter Unterschied -> Formel
anpassen UND bewerten, ob der v19wdlsw-Schwarm als Value-Material
davon beruehrt ist (Value-Ziel ist sim-robust -- erwartet: nein; wird
dann aber explizit am Brier eines Schwarm-Ablations-Trainings geprueft).
**Kosten**: 1-2 Gatings a ~30-60min (150 Sims spielen schnell).

## Messung 3 — τ-Annealing (teuer, zuletzt, eigenes Go)

**Frage**: Verbessert Standard-Annealing (fruehe Zuege τ=1, spaete
argmax) die Korpus-Qualitaet gegenueber durchgehend τ=1?
**Kostenklasse (halbiert, Nutzer-Hinweis 2026-08-06)**: die
τ=1-KONTROLLE existiert bereits -- die 4.000 v19wdl-Sockel-Partien SIND
durchgehend-τ=1-Material vom selben Generator. Frisch noetig ist NUR
der Annealing-Batch: ~2.000 Sockel-Partien mit argmax ab Zug ~30
(self_play-Erweiterung im Post-Kampagnen-Fenster). Design: Arm A =
v20-Fenster unveraendert; Arm B = identisches Fenster, aber 2.000 der
4.000 Sockel-Partien (feste, seed-bestimmte Auswahl) gegen die 2.000
Annealing-Partien getauscht -- alles andere in beiden Armen identisch.
2 Trainings + 1 Gating + Brier/Orakel deskriptiv. ~0,5 Tage Maschine.
**Vorab-Festlegung**: Annealing-Schwelle Zug 30 (grob 1. Runde+),
danach argmax; R5 bleibt Alpha-Beta-exakt (unberuehrt).
**Entscheid**: Uebernahme nur bei repliziertem Arena-Vorteil.
**Gate**: eigenes Nutzer-Go vor dem Start (Kostenklasse), fruehestens
nach Messung 1+2.

## Reihenfolge in der Pipeline

v20: Cache -> Training -> Gating -> Diagnostik/Watchlist ->
**[Knoepfe bauen] -> Messung 1 -> Messung 2** -> (Nutzer-Go) Messung 3.
Parallel dazu unveraendert: frozen-Set-Neubau, #29-Instrument,
Aggressions-Neukartierung, #37.
