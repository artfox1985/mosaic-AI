# Vorregistrierung: Injektion der WERTUNGSPLATTEN (alle acht Kriterien)

**Angelegt 2026-08-11 nach Nutzer-Rüge** — *"das ist einfach ein witz. wir
wollen die wertungsplatten injizieren. nicht nur die spezialplatten."*

Diese Vorregistrierung ist der **Haupt-Sweep**.
`PREREG_injektion_dosis.md` (Spezialfelder, `MOSAIC_UNLOCK_SHAPING_W`) wird
damit zum **Sonderfall danach**, nicht zum ersten Lauf.

## 0. Was falsch war, damit es nicht wiederkehrt

Der Auftrag lautete von Anfang an, die **Wertungsplatten** zu injizieren. Der
Term dafür ist gebaut (`wertung_progress_alpha`, alle acht Kriterien, gegatet
auf die aktiven; verdrahtet über `apply_wertung_shaping`,
`net_mcts.rs:1634`). Ich habe trotzdem einen Sweep vorregistriert, der
`MOSAIC_WERTUNG_SHAPING_W` auf **0** lässt und nur den Spezialfeld-Kanal
dosiert — begründet mit dem größten Margen-Anteil (9,0 von 14,5 Punkten).

Das war eine Verengung auf einen Sonderfall. Der Nutzer hat sie **dreimal**
angesprochen; ich habe zweimal erklärt statt umgestellt. **Kein Bau-, sondern
ein Messplan-Fehler.**

## 1. Gegenstand

`MOSAIC_WERTUNG_SHAPING_W` (Gewicht), `MOSAIC_WERTUNG_ALPHA` (Exponent,
Default 2,0 — **nicht** Gegenstand, Präzedenz `wertung_progress`).

Der Term, je Spieler absolut aus dem eigenen Brett
(`net_mcts.rs`, `apply_wertung_shaping_with`):

    für jeden Spieler i:
        pts   = wertung_progress_alpha(players[i], scoring_tile_ids, alpha)
        shift = w * tanh(pts / 50.0)
        out[i] = clamp(value[i] + shift, 0, 1)

und `wertung_progress_alpha` deckt, **gegatet auf `scoring_tile_ids`**:

| Kriterium | Form | Punktwert |
|---|---|---|
| 0 Reihen | `Σ (row_fill/6)^α` | ×3 |
| 1 Spalten | `Σ (col_fill/6)^α` | ×7 |
| 2 Diagonalen | `Σ (diag_fill/6)^α` | ×10 |
| 3 Jokerfelder | `(wild_filled/wild_total)^α` | ×2×wild_total |
| 4 Randfelder | `border_fill` | linear (additiv) |
| 5 Eckplatten | `Σ (corner_fill/4)^α` | 3/3/8/8 |
| 6 Spezialfelder | **0 hier** — hält `unlock_progress_beta` | (Doppelzählung vermieden) |
| 7 Farbreihen | `Σ (row_colors/5)^α` | ×4 |

`MOSAIC_UNLOCK_SHAPING_W` bleibt in diesem Sweep auf **0**, damit die beiden
Kanäle nicht konfundieren.

## 2. Arme — und sie sind KLEINER als beim Freischalt-Term

**Gerechnet, nicht übernommen** *(meine Ableitung aus den Durchsatz-Zahlen in
`docs/domaenenwissen.md`, ungemessen)*: bei ~15,7 belegten Feldern je Brett
liegt die mittlere Spaltenfüllung bei ~2,6. Mit α = 2 gibt Kriterium 1 allein

    (2,6/6)² × 7 × 6 Spalten ≈ 7,9 Punkte   ->   tanh(7,9/50) = 0,156

Bei w = 1,0 wäre die Verschiebung **0,156** — das erschlägt
Geschwister-Q-Differenzen von wenigen Hundertsteln und sättigt den auf [0,1]
geklemmten Blattwert. Liegen mehrere Kriterien gleichzeitig (es sind immer 3
Platten im Spiel), wird es größer.

| Arm | `w` | Erwartete Verschiebung | Begründung |
|---|---|---|---|
| Kontrolle | **0,0** | 0 | Bestandsverhalten |
| A | **0,1** | ~0,016 | spürbar, klar untergeordnet gegenüber Q |
| B | **0,3** | ~0,047 | Hauswert der bestehenden Shaping-Gewichte, obere Kante |

**Kein Arm bei 1,0** — anders als in `PREREG_injektion_dosis.md`, wo der Term
eine Größenordnung kleiner ist. Zwei Arme, Task-D-Präzedenz.

## 3. Instrument und Statistik

`tools/paired_arena_env_ab.py`, ein Prozess je Arm (Knöpfe sind prozessweit,
`OnceLock`), Champion `v21_2d_brierbest`@400 gegen **Heuristik@150(dyn)** — die
Heuristik liest keinen der Knöpfe, die Armdifferenz ist also der Netz-Seite
zuzurechnen.

    --env-name MOSAIC_WERTUNG_SHAPING_W --arms 0.0 0.1 0.3 --control 0.0
    --net-sims 400 --n-games 200 --seed 20260911 --out-prefix wertungw

**Basis-Seed 20260911 hiermit festgenagelt** (vor dem Lauf, nicht danach).

1. Gepaart über den Spielindex, identischer Basis-Seed in allen Armen.
2. **Block-Ebene als Pflichtinstrument** (8 Blöcke à 25), Block-Delta mit SE
   und t berichten.
3. Exakter zweiseitiger McNemar auf den diskordanten Paaren.
4. **Bonferroni über zwei Arme**: α = 0,025 je Arm.
5. Frühstopp unter 150 Paaren nur mit Frisch-Seed-Replikation.

## 4. Pflicht-Nebenmessung: das VERHALTEN, nicht nur die Siegquote

Gumbel zieht `GUMBEL_TOP_M = 16` Kandidaten nach Prior-Masse; die Injektion kann
nur **umordnen, was gezogen wurde**. Ein Null-Ergebnis kann also „Term
wirkungslos" ODER „Prior blockiert" heißen — ohne Verhaltenszahl nicht
unterscheidbar. Deshalb `log_games=True` (Commit `9dfeb16`) und Auswertung über
`tools/analyze_game_log.py`.

Zielgrößen mit ihren Referenzwerten aus `docs/domaenenwissen.md`:

| Größe | Mensch | KI heute |
|---|---|---|
| Nahmen-Anteil in Musterreihen 5+6 | 40,4 % | **22,7 %** |
| belegte Zellen je Rasterreihe 5/6 | — | **0,84 / 0,58** |
| Spalten vollständig | — | 0,4–1,2 % |

Der **dichte** Detektor sind die belegten Zellen je Rasterreihe (~6.300
Beobachtungen bei 200 Paaren gegen ~120 Abschlussereignisse) und der
Nahmen-Anteil. Abschlüsse allein sind zu selten, um eine Verschiebung von 20 %
zu zeigen.

### Lesart

| Verhalten | Siegquote | Verdikt |
|---|---|---|
| Zellen in Reihe 5/6 steigen | steigt | Term wirkt und rechnet sich ⇒ Dosis übernehmen |
| steigen | flach | wirkt, wandelt nicht in Siege ⇒ Dosis oder Zielkonflikt mit den Linienpositionen |
| **steigen nicht** | — | **Prior blockiert.** Kein Beleg gegen den Term; Arena-Wert ist UNTERGRENZE, Folge ist Self-Play MIT Injektion |

## 5. Vorbedingungen

1. Wheel mit `log_games` installiert, **Paritätsprobe geprüft**:
   `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` — am
   2026-08-11 selbst verifiziert. ✔
2. `log_games` muss durch die **Python-Seite** gereicht werden —
   `tools/paired_arena_arm_worker.py:41` ruft `net_arena_match` derzeit OHNE
   das Argument. **Offen**, kleine Änderung, vor dem Lauf nötig, sonst liefert
   der Sweep keine Verhaltenszahlen.
3. Die Parser-Lücken in `tools/analyze_game_log.py` (Replay bricht an der
   `↩️ … zurueck unter den Stapel`-Zeile ab) — **in Arbeit**. Die Siegquote
   hängt nicht daran, die Verhaltensmessung schon.

## 6. Was dieser Sweep NICHT entscheidet

- Keinen Champion-Wechsel (kein neuer Checkpoint).
- Nicht `MOSAIC_UNLOCK_SHAPING_W` (`PREREG_injektion_dosis.md`, danach).
- Nicht den Punkte-Kanal (`PREREG_punkte_lambda_unter_kipppunkt.md`).
- Nicht den Exponenten α (Default 2,0, Präzedenz `wertung_progress`).
