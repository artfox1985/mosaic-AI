# Mosaic-AI AlphaZero-Loop — Status & Fahrplan

Historische Details (alte Zählung vor dem Neustart, Bug-Diagnosen, verworfene
Ansätze) stehen in der Git-Historie dieser Datei und in den `v*_eval.md`s —
hier nur der aktuelle Stand und die aktiven Regeln.

## Aktueller Stand

**Champion: v4.** v5 konnte v4 nicht schlagen (45:55). v4 generiert aktuell
eine weitere Self-Play-Runde (v4b); v6 wird als nächster Kandidat trainiert.

| Netz | Fenster | Champion? | vs. Heuristik | Ø Score (Netz:Heur) | vs. Champion | Ø Score |
|---|---|---|---|---|---|---|
| v1 | 3000 Bootstrap-Spiele (cold) | ja (einzige Option) | 43 % | 19.5:25.4 | — | — |
| v2 | Bootstrap+2000×v1 | nein — v1 bleibt | 44 % | 19.6:28.4 | 50:50 (z=0.0) | 20.5:17.6 |
| v3 | Bootstrap+2000×v1+2000×v1b | nein — v1 bleibt | 47 % | 25.6:29.9 | 53:47 (z=0.6) | 22.1:19.6 |
| **v4** | v1+v1b+v1c (6000, kein Bootstrap) | **✅ neuer Champion** | 48 % | 22.3:25.5 | **65:35 (z=3.0)** | 19.7:15.2 |
| v5 | v1b+v1c+v4 (gleitend) | nein — v4 bleibt | 47 % | 22.9:25.7 | 45:55 (z=-1.0) | 20.0:24.0 |

Trend: durchgehender Fortschritt v1→v4 (mehr Daten half sichtbar auf jeder
Achse), v5 der erste Ausreißer ohne Fortschritt — vom Champion/Kandidat-
Protokoll erwartet, kein Alarmsignal.

**Stage 2 (Netz-Value als Suchblatt): weiterhin 🔴 ROT** bei allen Generationen
(Ratio 3.4×–5.1×, siehe Reifegrad-Sonde unten). Bleibt in Stufe 1 (DFS-Blatt).

## Champion/Kandidat-Protokoll

- **Gate:** ein Kandidat wird nur Champion, wenn er den bisherigen Champion mit
  **≥60:40** (z≈2.0, n=100) schlägt. Knappere Ergebnisse sind statistisch
  Rauschen — Champion bleibt bestehen und generiert weitere Self-Play-Runden.
- **Self-Play kommt immer vom aktuellen Champion**, nie vom zuletzt trainierten
  Netz.
- **Fenster-Größe:** max. 2 abgelöste Champions (je 1 repräsentative Runde à
  2000 Spiele = 4000) + aktueller Champion (bis zu 3 Runden à 2000 = 6000).
  Macht max. **10.000 Spiele** gesamt. Rollierend: älteste Runde fällt raus,
  sobald eine neue dazukommt (gilt sowohl zwischen Champions als auch innerhalb
  der Runden des aktuellen Champions).
- **Wenn ein Kandidat mit vollen 10.000 Spielen den Champion immer noch nicht
  schlägt**, zwei Eskalationsstufen, günstigste zuerst:
  1. **Fenster ausdünnen** (billig, kein neues Self-Play nötig): die 4000
     Spiele der alten Champions reduzieren (z. B. auf 2000 oder weniger),
     sodass der aktuelle Champion relativ mehr Gewicht im Fenster bekommt, und
     mit dieser Zusammensetzung neu trainieren — nur ein Trainingslauf, keine
     neue Self-Play-Generation.
  2. **Erst wenn das auch nicht reicht: Sims für die Champion-Runden erhöhen**
  (z. B. 800 statt 400), sequenziell älteste zuerst austauschen — teuer
  (braucht eine neue, mehrstündige Self-Play-Runde), aber ein echter
  Qualitätsgewinn: mehr Sims verbessert die Suche selbst (schärfere, genauere
  Zielverteilung), reine Wiederholung bei gleicher Sim-Zahl reduziert nur
  Stichprobenrauschen, hebt
  aber nicht die Qualitätsdecke an.

## Value-Target (aktuelle Formel, `engine/py/neural_net.py`)

```
own_total = step["scores"][eigener Spieler]   # inkl. Wertungsplatten
opp_total = step["scores"][Gegner]
value = tanh((own_total − 0.5 · opp_total) / 50)
```
Ziel für JEDEN Schritt der Partie (delayed reward, wie in AlphaZero) — nicht
Win/Loss ±1, sondern das tatsächliche Punkte-Endergebnis. Gewichtung 0.5 auf
die Gegnerseite statt reiner Differenz, damit z. B. 65:60 höher bewertet wird
als 10:5 (gleiche Marge, aber absolut sehr unterschiedliche Leistung). Skala
50 ist an einem groben menschlichen Referenzwert kalibriert (~100 Punkte =
sehr gut), nicht an aktuellen (noch schwachen) Spieldaten.

`VALUE_WEIGHT = 2.5` (config.py) balanciert Value- gegen Policy-Loss — nötig,
weil das neue Target eine ~4.6× kleinere Streuung hat als das alte ±1-Ziel.

## Stage-2-Reifegrad-Sonde

Läuft automatisch nach jedem `train.py`-Lauf (100 Spiele je Stufe, 400 Sims):
vergleicht die 0:0-Rate desselben Netzes mit DFS-Blatt (Stufe 1) vs.
Netz-Value-Blatt (Stufe 2).

Ampel (Verhältnis 0:0(Stufe2)/0:0(Stufe1), Laplace-geglättet):
- ≤1.5× → 🟢 Value-Head trägt, voller Stufe-2-Zyklus lohnt sich
- 1.5–3× → 🟡 noch nicht reif
- \>3× → 🔴 klar noch nicht reif, in Stufe 1 bleiben

Bei Grün: Self-Play mit `--stage 2`, warm vom Reifegrad-Netz, Mix aus
Stufe-1-Restfenster + neuen Stufe-2-Daten, Arena-Gate wie gewohnt (Champion-
Protokoll gilt genauso für Stufe 2).

## Bekannte Bugs (in diesem Zyklus gefunden und gefixt)

- **Self-Play-Timeout zu knapp für netzgeführte Suche** (30s war auf reine
  Heuristik-Suche kalibriert) → separate Timeouts, `NET_GAME_TIMEOUT_SECS=180`.
- **BatchNorm-Crash bei Batch-Größe 1** (Restbatch einer Epoche zufällig Größe
  1) → `drop_last=True`.
- **Tiling-Solver-Kombinatorik-Explosion**: `chip_allocations` kann pro Aufruf
  bis zu 2^14 Teilmengen prüfen, wird rekursiv sehr oft aufgerufen → Node-Budget
  eingeführt (200.000 zu hoch, auf 2.000 korrigiert) + Performance-Fix
  (Bitmasken-Signatur statt String-Dedup).
- **Speicher-Nadelöhr beim Datensatz-Laden**: Zwischen-Listen wurden nicht
  freigegeben, bevor der HDF5-Cache geschrieben wurde → `del` direkt nach
  Konvertierung.
- **Completion-Check**: `self_play.py` prüft jetzt automatisch je `.pkl`-Datei,
  ob alle Partien wirklich Runde 5 erreicht haben (`completed`-Feld aus Rust),
  warnt sichtbar bei Abbrüchen.

Wahrscheinlich betraf der Timeout-Bug auch die GESAMTE alte Zählung vor dem
Neustart (v4-v11) — nicht mehr rekonstruierbar, da die Daten gelöscht sind.

## Offene Punkte

- Stage 2 weiterhin rot — keine Prognose, wann sich das ändert.
- Fenster-Ausdünnung (statt harter Champion-Grenzen) als mögliche Verfeinerung,
  falls ein Champion ungewöhnlich lange durchhält — noch nicht nötig.
