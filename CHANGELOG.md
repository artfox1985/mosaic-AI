# Changelog

## v1.1-alpha31 (2026-09-21)

No engine behaviour change against `v1.0-alpha31`: the anchor still reproduces
its reference run move for move, and the contract hash is unchanged.

### The reason this release exists

**The cache-key defect described under v1.0-alpha31 is fixed.** The key now
carries each chip's colour set as a bitmask in hand order, which is immune to
the order *within* a chip while keeping the order *across* chips that the
greedy fallback depends on. That is the one behaviour-relevant change; it
affects which memoised tiling result is returned, so a game may now follow a
different line than under v1.0.

### Everything else
- Bundles are named `Mosaic-AI_v<version>-alpha<generation>.zip`, so a version
  bump is visible in the file name instead of overwriting a shipped one.
- Repository cleanup: 62 raw `pickle.load` sites in 61 tools moved to
  `corpus_io` (43 of them were failing outright on gzip corpora); the exact
  two-sided binomial test consolidated from 18 copies under four names into one
  module, with all 126 recorded McNemar p-values reproducing exactly; spec
  fields mapped to engine knobs in one place, guarded by a test that reads
  `KNOWN_FIELDS` out of the Rust source; the "is the machine free" guard fixed
  in the one of five copies that could not see a running `cargo` build.
- Nine dead `engine/examples/` probes and three stale end-to-end scripts
  removed. The HTTP routes of `server.py` have no automated coverage as a
  result -- the scripts were red because their own move choice predates the
  node types added in `v30`.
- Tool tests 147 -> 206.

### Measurements added after the tag

Two probes that had not run since `v24-b06` were brought back and run against
the final champion.

- **Round-4-end calibration (R4b).** The old finding, "both heads blind to
  exact round-4-end information, R2 ~ 0", no longer holds: the value head
  reaches R2 = 0.414 against an exact ground truth, and the sign anchor hits
  71.4% where it used to be a coin flip at 50.0%. New finding in its place: the
  points head now *overshoots* -- it spreads with sd 40.2 against a true 18.8.
- **A probe of where the information is lost** answers that cleanly: a linear
  read-out of the 512-wide trunk recovers LOO-R2 = 0.940 against a ceiling of
  0.983, while the same probe on the raw input recovers 0.087. The
  representation is there and the read-out destroys it -- and that was already
  true for the v20-era model (trunk 0.912). The bottleneck is neither the
  encoder nor trunk capacity.
- **Round-5 calibration (R5)**, and this one is a genuinely paired comparison:
  same frozen eval set, same settings, and the fitted curve came out
  bit-identical to the historical runs. The value head's damping shrank from
  0.086 to 0.146 -- smaller, but nowhere near the unbiased 1.0. Its points head
  moved from 0.973 to 1.088, the same sign change as in R4b.

None of these changed a line of engine code; they are measurements of the
shipped champion. Details and caveats (most of the comparisons are *not*
paired) in `evaluations/PREREG_r4_value_calibration.md` and
`PREREG_r5_value_calibration.md`.

## v1.0-alpha31 (2026-09-20)

Compared to **v0.1-alpha21** (2026-08-15). 1,274 commits, ten generations
(`v22` through `v31`), 69 new pre-registrations.

### Playing strength

The champion went from `v21_2d_brierbest` to **`v31-b01`**, shown in the game as
**Tessa**. On the current ladder both stand measured against the same fixed
point (`models/frozen_heuristics/hv4_anchor`, Heuristic@150 = 1000):

| | Elo | 95% CI | rated games |
| --- | --- | --- | --- |
| `v21_2d_brierbest@400` | 1193 | [1150, 1236] | 500 |
| `v31-b01@400` | 1458 | [1414, 1510] | 1,000 |

**+265 Elo, non-overlapping intervals.** Read the two numbers off the same
table, not off the two READMEs: the v21 release reported Elo 1358 against the
*previous* anchor, and ratings are not comparable across an anchor boundary.
Earlier segments are kept in `archive/elo_history_pre_*.csv`.

`v31-b01` was promoted on four edges, none of them stopped early: 461:339 over
two seeds against the previous champion, 45:5 against the anchor, and 79:71
against `v29-b09` two generations back. That last edge sits well below what the
other two predict; it is recorded as an open anomaly rather than smoothed over.

`v31` was called the final generation when this tag was cut. It is not:
`v32` was released to proceed on 2026-09-22.

### Engine and rules

- **Dome-stack information sets.** The search used to reshuffle the whole dome
  stack on every call, forgetting the order it had itself chosen when putting
  tiles back. Fixed; the search now keeps what a player legitimately knows. A
  human playing the GUI found this, not the measurement pipeline -- an error in
  a *shared* world model cancels out between two agents and costs zero Elo at
  any sample size. Places where the code discards information on purpose are
  now listed in `docs/architecture_reference.md`.
- **Two engine corrections moved the anchor's own moves** and each opened a new
  ladder segment: the min-node move ordering in the round-5 solver (2026-08-21,
  `PREREG_round5_minfix_elo_reset.md`) and the phantom-tile fix, which re-anchored
  the ladder on `hv4_anchor` (2026-09-12). Ratings are not comparable across such
  a boundary; the old registers are kept as
  `archive/elo_history_pre_r5fix.csv` and `archive/elo_history_pre_phantomfix.csv`.
  Since the second segment the anchor ships its own wheel, so an engine change
  can no longer move the fixed point, and every change is checked against it move
  by move.
- **Bonus chips are canonical.** Colour pairs such as black/blue and blue/black
  were distinct objects; they are one now, in the engine and in the GUI.

### Model input and action space

- `INPUT_SIZE` **708 -> 888**: stack-top and plate-type visibility, floor-line
  colours, phantom shares, a 39-value sight block, a 90-value tiling projection
  and the player's own ordered designs. The encoder stays additive, so older
  ONNX models remain loadable.
- `NUM_ACTIONS` **406 -> 414**: choosing which colour to take off the moon stack
  (406-410) and which tile to return first (411-413) are explicit decision nodes
  now instead of being resolved implicitly.

### Questions settled

- **Cold start costs strength.** `v30-b01` and `v30-b02` trained on the same
  replay window, same monolith, same seed and same recipe, differing in one
  factor: 404:396 = 50.50% cold (block-z +0.28, H0) against 443:297 = 59.86%
  warm (block-z +5.36). A gap of 9.36 percentage points
  (`PREREG_v30_window.md` par.9).

### Measurement discipline

- **The anchor cannot drift any more.** Since the second ladder segment the
  anchor ships its own wheel, and every engine change is checked against it move
  by move before any rating is compared across it.
- Every measurement run records its own wall-clock, CPU time, thread count and
  per-unit cost in its artifact, because `STATUS.md` gets trimmed and durations
  kept only there rot.
- 701 library tests and 22 tool-test files, run by the pre-commit hook.

### Packaging

- Engine version **0.1.0 -> 1.0.0**, in both version sources
  (`engine/Cargo.toml` and `engine/pyproject.toml`) -- maturin reads the
  latter, the Rust code the former, and setting only one of them has no effect.
- Portable bundle built from `models/champion.txt`, named
  `Mosaic-AI_<champion>_<date>.zip`.
- Substantial GUI work: 3,044 lines added and 375 removed across the frontend
  and `server.py`.

### Known issue in this tag

The tiling solver's cache key treats two hands holding the same multiset of
bonus chips in a different order as equal. It only bites above
`CHIP_ALLOC_CAP` (14) held chips, where the exact enumeration falls back to a
greedy one that picks by hand index; below that the key is correct. It affects
which memoised tiling result is returned, not which moves are legal.
