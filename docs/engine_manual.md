# 🎲 Mosaic – Rules of Play

This document describes the rules **as the engine actually implements them**.
Where the physical game leaves a case open, the engine's chosen reading is
marked as such. German terms are kept for every element that the in-game UI
labels in German (the interface is German for now); each is glossed in English
on first use.

> **Attribution:** Mosaic is a private, non-commercial reimplementation of the
> *Azul Duel* ruleset (game design by Michael Kiesling, © Plan B Games / Next
> Move Games). The game design is not ours – this repository contributes the
> engine, the neural network and the training pipeline. Not affiliated with or
> endorsed by the publisher.

## 1. Overview & Objective

Mosaic is an abstract, tactical tile-laying game for exactly two players over
exactly 5 rounds. You collect coloured tiles, stage them in your
**Musterreihen** (pattern rows) and then transfer them onto your personal
**Kuppel** (dome), a growing 6×6 grid. Points come from two sources: placing
tiles during the game, and the final scoring driven by the
**Wertungsplatten** (scoring plates). Highest total wins.

## 2. Components

* **Tiles:** 65 normal tiles in 5 colours – blau, gelb, rot, schwarz, türkis
  (blue, yellow, red, black, turquoise) – exactly 13 per colour. A separate
  reserve holds 9 **Spezialfliesen** (special tiles).
* **Beutel & Turm (bag & tower):** all 65 normal tiles start shuffled in the
  bag; discarded tiles go to the tower, which refills the bag when it runs
  empty. If bag and tower together cannot fill the **Fabriken** (factories),
  the round starts with partly filled or empty ones – and the Bonuschips of
  any factory that started empty are revealed immediately. (Tiles resting on
  a Kuppel leave the cycle for good, so this state is reachable.)
* **Fabriken:** 4 small ones (4 tiles each on their Sonnenseite / sun side)
  and 1 large one (5 tiles).
* **Player board:** 6 Musterreihen with capacities rising from 1 to 6 tiles
  top to bottom; a **Strafleiste** (penalty floor) with 4 slots worth −1 to
  −4 at the end of a round; and the Kuppel, a 3×3 arrangement of slots. Each
  **Kuppelplatte** (dome plate) covers a slot with 2×2 cells, so a filled
  Kuppel forms the 6×6 scoring grid.
* **Kuppelplatten:** 18 in total, each carrying 3 colour cells plus one
  special cell. On 9 plates that cell is a locked **Spezialfeld** (special
  field, see section 5); on the other 9 it is a **Wildfeld** (wild field)
  that accepts any colour when a tile is placed on it. 3 plates lie face up
  in the display, the rest form the face-down draw stack. The display is
  **not** refilled during a round – the only exception is right after the
  opening placements – and is topped back up to 3 during round preparation.
* **Bonuschips (bonus tiles):** each round, 1 face-down chip is placed on
  each of the 4 small Fabriken (20 in the supply, 4 per round over 5 rounds).
  A chip is revealed as soon as its factory has been emptied.
* **Starting score:** each player begins the game with **5 points**.

## 3. Setup

* At the start of every round the small Fabriken are refilled with 4 tiles
  each and the large one with 5 tiles, drawn fresh from the bag; the
  **Startspielerstein** (start player marker) sits with the large factory.
* **Large factory, monochrome case:** if all 5 drawn tiles happen to share a
  colour, they go back and are redrawn until at least two colours are
  present. Should bag and tower be unable to produce two colours at all, the
  monochrome fill stands – and whoever takes those 5 identical tiles receives
  the Startspielerstein.
* **Opening placement (before round 1 only):** each player places one
  starting Kuppelplatte, the non-start player first. This placement is free,
  position and rotation are unrestricted, and it counts neither as a regular
  turn nor against the two plates owed for round 1 (section 4A).

## 4. Round Structure

Every round runs through two consecutive phases: Drafting (taking tiles) and
Tiling (placing them on the Kuppel).

### Phase 1: Drafting

Players alternate turns, each taking exactly one of four actions. A player
with no legal action **must** pass – passing by choice is not allowed – after
which the opponent may take several turns in a row.

**A) Place a Kuppelplatte.** In rounds 1–4 each player owes exactly 2 plate
placements, and the drafting phase does not end before both players have
placed theirs; in round 5 no plates are placed at all. A plate can be taken
for free from the face-up display, or drawn blind from the stack.
*Drawing from the stack:* every single draw costs 1 point and may be repeated
as often as you like – the plate backs reveal only the type (Wild or Special).
When you stop drawing, the fronts are turned up, you keep and place one plate,
and the rest go back under the stack in any order you choose. At a score of 0
further draws are effectively free, because a score can never drop below zero.
*(The physical rules leave this case open; the engine resolves it consistently
with the never-below-zero rule.)* Placed plates are permanent; position and
rotation are free.

**B) Take tiles from a Sonnenseite.** Take every tile of one colour from the
sun side of a single factory and assign them to exactly one Musterreihe. The
factory's remaining tiles then move to its moon side – as a stack on a small
factory, or into the moon pool of the large one. On a small factory, **the
taking player decides the stack order** of those leftovers, which matters:
only the top tile of a moon stack can be taken later.

**C) Take tiles from the Mondbereich.** Collect every *topmost* tile of one
chosen colour across the moon areas of *all* factories at once – one tile per
stack, plus every tile of that colour from the large factory's moon pool.

**D) Take a revealed Bonuschip** from an emptied factory. Each player takes
exactly 2 per round; since all 4 chips get revealed and the round only ends
once none are left, this is an obligation rather than an option.

**Placement rules**

* Tiles that no longer fit the chosen Musterreihe – or whose colour clashes
  with it – fall onto the Strafleiste. Placing tiles there voluntarily is
  also allowed.
* Once all 4 Strafleiste slots are occupied, further tiles drop into the
  tower.
* The Startspielerstein is awarded **only** on the first take from the large
  factory's **Mondbereich** – a sun-side take leaves it where it is – and it
  cannot be declined. Its holder opens the next round but takes a fixed −2 at
  round end. (Sole exception: after a forced monochrome fill it travels with
  the sun-side take of those 5 identical tiles.) Since the round ends only
  when the large factory is completely empty, marker included, someone takes
  it every round.

### Phase 2: Tiling

At the end of the round the completed Musterreihen are resolved.

* Rows are worked strictly top to bottom (1 through 6). If a row's colour
  matches an available cell on a Kuppelplatte, it *must* be placed. Once a
  lower row has been placed, every row above it is locked for the rest of the
  phase.
* Each completed row sends exactly one tile to the Kuppel; the rest of that
  row goes to the tower.
* **Rows that cannot be placed:** if all 3 Kuppelplatten of a row's dome row
  are already assigned and none offers a matching free cell, the row – even
  an incomplete one – must be cleared, and its tiles fall toward the
  Strafleiste and tower. If that dome row still has empty plate slots,
  however, **the tiles stay and carry over into the next round**; a later
  matching plate (or the slots filling up) decides their fate.
* Incomplete rows under no such pressure simply remain for the next round.

**Scoring a placement**

* A tile with no orthogonal neighbour scores 1 point.
* A tile that joins a contiguous line scores that line's full length –
  **colour is irrelevant here**, every occupied cell counts, Spezialfliesen
  included. A horizontal line of length *h* (>1) pays *h* points, a vertical
  line of length *v* (>1) pays *v* points, and a tile completing both is paid
  for both.

**Spending Bonuschips**

* An incomplete Musterreihe holding at least 1 tile may be completed with
  chips – entirely optional.
* Each missing cell costs either 2 chips matching the row's colour exactly,
  or 3 chips of any colour; costs may be mixed across several missing cells,
  and a two-coloured chip counts as matching if it shows the row's colour.
  The top-down rule applies here too: locked rows can no longer be filled.

### Round-End Settlement

* The Strafleiste pays out −1, −2, −3 and −4 for its occupied slots.
* The Startspielerstein costs a further −2.
* A player's total can never fall below 0 through penalties – the floor
  applies to every settlement against the running total.

## 5. Spezialfliesen & Spezialfelder

* 9 of the 18 Kuppelplatten carry a locked Spezialfeld.
* It unlocks only in the Tiling phase, and only once the plate's other three
  regular cells are filled.
* A Spezialfliese from the separate reserve is then placed there
  **immediately and automatically** – there is no choice involved. The
  reserve of 9 can never run dry, as there are exactly 9 Spezialfelder in
  play.
* **Scoring:** the Spezialfliese immediately pays points equal to the grid
  row it lands in (1 to 6). It earns no line bonus of its own, but counts as
  an ordinary occupied cell in the lines of neighbouring tiles.

## 6. Game End & Final Scoring

The game ends after round 5, and the Wertungsplatten are settled. Exactly 3 of
the 8 possible plates are in play. They come in 4 mutually exclusive pairs
(physically: 4 double-sided plates, one side chosen at random per pair, of
which 3 enter the game), so at most one plate per pair can ever apply.

**The 8 Wertungsplatten**

| #   | Plate                  | Scores                                                                                                              | Excludes |
| --- | ---------------------- | ------------------------------------------------------------------------------------------------------------------- | -------- |
| 1   | ↔️ Horizontale Reihen  | 3 pts per complete horizontal row                                                                                   | 8        |
| 2   | ↕️ Vertikale Reihen    | 7 pts per complete vertical column                                                                                  | 5        |
| 3   | ↗️ Diagonale Reihen    | 10 pts per complete diagonal (max. 2)                                                                               | 6        |
| 4   | 🌈 Mehrfarbige Felder  | 2 pts per Wildfeld – but only if *all* of them are filled                                                           | 7        |
| 5   | ⬜ Äußere Felder        | 1 pt per tile on the outer edge of the Kuppel                                                                       | 2        |
| 6   | 🔲 Eckplatten          | 3 pts per completed upper corner plate, 8 pts per completed lower one (all 4 cells)                                 | 3        |
| 7   | ⭐ Spezialfelder        | −3 pts per Spezialfeld left empty                                                                                   | 4        |
| 8   | 🎨 Farbenreiche Reihen | 4 pts per horizontal row holding at least 5 different colours (Spezialfliesen count as no colour; gaps are allowed) | 1        |

The highest total after final scoring wins. A tie goes to the player holding
the Startspielerstein – that is, whoever took it in round 5, and as noted in
Phase 1, someone always does.
