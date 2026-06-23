# Offensiv-Spiel: Repräsentation/Architektur statt Heuristik-Terme

## Context

Die Heuristik-Erweiterung (Terme G/H/I in `agents/shaping.py`) ist umgesetzt und **hat ihr
Ziel erreicht**, aber ein tieferes Problem freigelegt:

**Was die G/H/I-Terme gebracht haben** (gemessen an frischen s100-Self-Play-Daten):

- Ø offene Reihen **2,83 → 1,96**, an Floor-Stellungen **3,41 → 2,09** (Buildup-Drift behoben,
  Floor jetzt „strukturell" statt Über-Öffnen).
- 0:0-Rate **58% → 30%**.

**Das verbleibende, eigentliche Problem — Offensive (datenbelegt):**
| Messung | Wert | Deutung |
|---|---|---|
| Platten belegt / Nachbarpaare | 9/9, 12/12 (Maximum) | Dome-Struktur komplett & verbunden — *nicht* das Problem |
| Gefüllte Spaces | ~12/36 | Agent legt Steine |
| **Punkte pro gelegtem Stein** | **0,82** | Steine stehen ISOLIERT → ~1 Pkt, Floor frisst den Rest |
| Ø Siegerscore | 9,8 (sollte 40–70+) | — |

Punkte entstehen nur aus **orthogonalen Linien** auf dem 6×6-Dome
([round_end.py `score_placed_tile`](engine/round_end.py:332)). Der Agent baut keine Linien,
weil das eine **mehrstufige Farb-Geometrie-Planung** über Drafting (Plattenwahl/-rotation +
welche Reihen) und Tiling (wohin der Stein) erfordert.

**Entscheidung des Users:** Keine weiteren Heuristik-Terme („nicht weiter forcieren"). Ein
anderer Ansatz.

**Die eigentliche Decke (aus Code-Analyse):** Das Netz ist ein **flaches MLP**
([neural_net.py `MosaicNet`](agents/neural_net.py:481), input→hidden×3). Der Dome wird als
**162 flache Features** ohne Nachbarschafts-Induktion und **ohne Linien-Features** eingespeist
([state_to_tensor Abschnitt 6](agents/neural_net.py:114)). Ein flaches MLP kann „diesen Space
füllen verlängert eine Linie auf Länge 4 → +4" praktisch nicht repräsentieren. Das
Value-Target ist bereits outcome-basiert ([compute_win_val](agents/neural_net.py:255)) — aber
die Funktionsklasse kann die Linien-Strategie nicht ausdrücken. **Darum half kein
Bewertungs-Hebel: das Problem ist Repräsentation/Architektur, nicht die Belohnung.**

**Ziel:** Dem Lerner die räumliche Linien-Information geben, sodass das (bereits
outcome-basierte) Lernen offensives Cluster-Bauen selbst entdecken kann.

## Ansatz — zweistufig, billig zuerst

### Stufe 1 (empfohlen zuerst — billige Falsifikation): Linien-Geometrie als Features

Erweitere `state_to_tensor` ([neural_net.py:12](agents/neural_net.py:12)) um explizite
räumliche Features pro Spieler (me + enemy), abgeleitet aus dem 6×6-Belegungsraster (das
`_estimate_row_values` in [serializer.py:64](engine/serializer.py:64) bereits aufbaut — Logik
wiederverwenden):

- **Linienlängen-Histogramm:** Anzahl horizontaler/vertikaler Linien der Länge 2/3/4/5/6
  (gefüllte zusammenhängende Spaces).
- **Linien-Potential:** je leerem, farblich noch bedienbarem Space — um wie viel würde Füllen
  eine Linie verlängern (max h+v), aggregiert pro Reihe/Spalte.
- **Cluster-Kennzahl:** Σ Linienlänge² (belohnt das Netz indirekt für lange Linien, sobald es
  den Zusammenhang Score↔Feature über echte Outcomes lernt).

Konsequenzen: `INPUT_SIZE` ([config.py:18](config.py:18)) wächst → Netz muss **von Null** neu
trainiert werden (kein Warm-Start über die Schichtgrenze). `state_to_tensor` ist die einzige
Pflicht-Änderung; `MosaicNet` bleibt unverändert. Damit testen wir mit minimalem Aufwand, ob
Repräsentation die Decke ist.

### Stufe 2 (nur falls Stufe 1 hilft, aber nicht reicht): räumlicher CNN-Zweig

Den Dome als `6×6×C`-Planes (belegt, required_color one-hot, type/locked) aufbereiten und einen
kleinen Conv-Zweig in `MosaicNet.body` einführen, dessen Output mit den flachen Features
konkateniert wird. Größerer Eingriff (Architektur + Tensor-Reshape), echte räumliche
Induktion. Erst nach Messung von Stufe 1 entscheiden.

## Kritische Dateien

- `agents/neural_net.py` — `state_to_tensor` (Stufe 1), ggf. `MosaicNet` (Stufe 2).
- `config.py` — `INPUT_SIZE` anpassen.
- Wiederverwenden: 6×6-Raster-Aufbau aus `engine/serializer.py:_estimate_row_values`,
  Linien-Zählung analog `engine/round_end.py:_count_line`.

## Verifikation

1. **Feature-Sanity:** `state_to_tensor` auf ein paar gespeicherte States anwenden, neue
   Feature-Länge == neuer `INPUT_SIZE`, Linien-Features auf einem Board mit bekannter Linie
   manuell gegenprüfen.
2. **Frische Daten + Training:** s100-MCTS-Self-Play (Heuristik mit G/H/I) → `train.py --name vX`
   von Null. Value-Loss soll konvergieren.
3. **Arena/Score-Messung (Hauptmetrik):** `arena.py` AlphaZero vX vs. HeuristicMCTS. Vergleich
   gegen heute: **Punkte pro gelegtem Stein** (>1,0 = Linien entstehen), **Ø Siegerscore**
   (Ziel deutlich >9,8), **0:0-Rate**. Mess-Skript dafür existiert sinngemäß bereits (die
   read-only pkl-Analyse aus dieser Session — Platten-/Stein-/Punkte-pro-Stein-Auswertung).

## Offener Punkt (separat)

Die G/H/I-Heuristik-Änderung ist lokal committet (HEAD, 2 Commits vor `origin/main`), aber
**noch nicht gepusht**; ein PR war angefragt, wurde aber durch diese Analyse unterbrochen.
`gh` ist auf diesem Rechner nicht installiert → PR-Erstellung braucht entweder `gh`-Installation
oder manuelles Pushen + PR über die GitHub-Weboberfläche.
