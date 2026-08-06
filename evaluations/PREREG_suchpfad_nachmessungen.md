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

## Messung 1 — Floor-Gewicht-Sweep in der WDL-Aera (billig, zuerst)

**Frage**: Ist 0,3 noch der richtige Wert, nachdem sich die
Value-Spreizung seit der Kalibrierung ~2x geaendert hat (WDL-Aera)?
Der 0,15/0,6-Sweep steht seit Juli als "optional" offen.
**Design**: Modell = v20-Champion (bzw. bester v20-Kandidat, falls
Gating H0). Zwei gepaarte Gatings à 200 Paare, identische Seeds je
Paar, Modell auf BEIDEN SeITEN identisch, nur Env verschieden:
W=0,3 vs W=0,15 und W=0,3 vs W=0,6. Optional Bestaetigung W=0,3 vs
W=0,0 (Re-Validierung des Features am neuen Kopf).
**Entscheid**: Wechsel des Defaults nur bei SPRT-H1 GEGEN 0,3 plus
Frisch-Seed-Replikation (Statistik-Regel 3); sonst bleibt 0,3 und der
Punkt gilt als WDL-re-validiert.
**Kosten**: 2-3 Gatings a ~1-2h.

## Messung 2 — m-Formel bei niedrigen Sims (billig)

**Frage**: Kostet die Budget-Formel (150 Sims -> m=9) Staerke gegenueber
fester Breite m=16? Relevanz: Schwarm-Klasse kuenftiger Kampagnen und
alle Niedrig-Sims-Presets (GUI/#31).
**Design**: gepaartes Gating, SELBES Modell beidseitig @150 Sims,
Seite A `MOSAIC_GUMBEL_TOP_M=0` (Formel, m=9), Seite B `=16`;
200 Paare. Sekundaer identisch @64 Sims (m=4 vs 16), falls A signifikant.
**Entscheid**: H0 -> Formel bestaetigt (Abweichungsnotiz der
v20-Kampagne wird geschlossen). Signifikanter Unterschied -> Formel
anpassen UND bewerten, ob der v19wdlsw-Schwarm als Value-Material
davon beruehrt ist (Value-Ziel ist sim-robust -- erwartet: nein; wird
dann aber explizit am Brier eines Schwarm-Ablations-Trainings geprueft).
**Kosten**: 1-2 Gatings a ~30-60min (150 Sims spielen schnell).

## Messung 3 — τ-Annealing (teuer, zuletzt, eigenes Go)

**Frage**: Verbessert Standard-Annealing (fruehe Zuege τ=1, spaete
argmax) die Korpus-Qualitaet gegenueber durchgehend τ=1?
**Achtung Kostenklasse**: τ wirkt NUR auf die Self-Play-Zugwahl --
das ist ein KORPUS-Experiment, kein Gating: 2 Batches a ~2.000
Sockel-Partien (τ=1 vs annealed ab Zug ~30), 2 gepaarte Trainings
(identisches Rezept/Fenster bis auf den Batch), Gating der beiden Arme
gegeneinander + Brier/Orakel deskriptiv. ~1 Tag Maschine.
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
