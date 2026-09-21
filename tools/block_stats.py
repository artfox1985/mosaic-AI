# -*- coding: utf-8 -*-
"""tools/block_stats.py -- Blockmittel fuer Arena-Auswertungen, EINE Bauform.

CLAUDE.md ("Arena-Block-Korrelation", Nutzer-Anweisung 2026-08-04) verlangt jede
Score-Analyse auf BLOCK-Ebene: auf Partie-Ebene sind die Standardfehler massiv
unterschaetzt, weil die Partien eines Blocks korreliert sind (gemeinsamer
Worker-Prozess, benachbarte Seeds). Der Block IST die Laufeinheit des
Orchestrators (`--block-size`), und die Reihenfolge ist die des Laufs, nicht die
sortierte Seed-Reihenfolge.

ANLASS FUER DIESE SAMMELSTELLE (Durchsicht 2026-09-21, par.8h Fund 3): dieselbe
Zusammenfassung stand viermal im Baum, mit DREI verschiedenen Regeln fuer den
angebrochenen letzten Block:

  * `plate_points_from_arena.block_mean` -- zaehlt ihn ab halber Blockgroesse mit
  * `probes/env_ab_swap_eval.blocks`     -- zaehlt ihn IMMER mit
  * `probes/arena_block_sd_probe.block_sd` -- laesst ihn IMMER weg
  * `probes/corpus_behaviour_audit.blocks` -- vierte Fassung

**Gemessen, bevor vereinheitlicht wurde:** von allen Gating-Artefakten im Baum
hat genau EINES einen Rest bei Blockgroesse 5, und das ist ein Rauchtest mit
n = 2. Der Grund ist strukturell -- `paired_gating` wertet je Block aus und
stoppt darum immer auf einer Blockgrenze. Die Divergenz war also LATENT: keine
registrierte Zahl haengt an ihr, und die Vereinheitlichung aendert keine. Sie
schliesst die Falle, bevor ein Werkzeug mit nicht blockbuendigen Daten
hineinlaeuft.

**Die gewaehlte Regel ist die von `plate_points_from_arena`**, weil sie als
einzige begruendet war: ein angebrochener Block zaehlt mit, aber nur wenn er
mindestens die halbe Blockgroesse traegt -- sonst waere ein 1-Partie-Rest ein
vollwertiger Datenpunkt mit der Streuung einer Einzelpartie.

Nutzung aus `tools/`:      from block_stats import block_means
Nutzung aus `tools/probes/`: sys.path.insert(0, str(_ROOT / "tools")) davor,
                             wie in `probes/cache_parity_probe.py:63`.
"""
from __future__ import annotations

import math


def block_means(values: list[float], block: int) -> list[float]:
    """Werte in LAUFREIHENFOLGE zu Blockmitteln zusammenfassen.

    Der angebrochene letzte Block zaehlt mit, wenn er mindestens
    `max(1, block // 2)` Werte traegt; sonst faellt er weg.
    """
    if block < 1:
        raise ValueError(f"Blockgroesse muss >= 1 sein, war {block}")
    threshold = max(1, block // 2)
    out: list[float] = []
    for i in range(0, len(values), block):
        chunk = values[i:i + block]
        if len(chunk) >= threshold:
            out.append(sum(chunk) / len(chunk))
    return out


def block_t(values: list[float], block: int) -> tuple[list[float], float, float]:
    """Blockmittel, ihr Mittelwert und der t-Wert gegen 0.

    Rueckgabe `(blocks, mittel, t)`. `t` ist 0.0, wenn weniger als zwei Bloecke
    vorliegen oder die Streuung 0 ist -- beides sind keine auswertbaren Faelle,
    und ein `inf` im Artefakt waere schlechter als eine erkennbare 0.
    """
    blocks = block_means(values, block)
    n = len(blocks)
    if n < 2:
        return blocks, (blocks[0] if blocks else 0.0), 0.0
    m = sum(blocks) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in blocks) / (n - 1))
    return blocks, m, (m / (sd / math.sqrt(n)) if sd > 0 else 0.0)
