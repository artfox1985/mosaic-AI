"""
Mosaic-AI — Monte Carlo Tree Search (MCTS) Agent

Implementiert UCT (Upper Confidence Bound for Trees), die Standardvariante
wie sie in AlphaGo und ähnlichen Systemen als Suchalgorithmus verwendet wird.

Ablauf pro Zug:
  1. Selection   — folge UCB1-Score im Baum bis zu einem unerkundeten Knoten
  2. Expansion   — füge einen neuen Kindknoten hinzu
  3. Simulation  — spiele zufällig bis zum Spielende (Rollout)
  4. Backprop    — propagiere das Ergebnis zurück zum Wurzelknoten

Verwendung:
  agent = MCTSAgent(simulations=200, c=1.4)
  action = agent.choose(valid_actions, observation)
"""
from __future__ import annotations
import math
import time
import random
from typing import Any

import pickle

from agents.agent_env import MosaicEnv
from agents.agents import BaseAgent, RandomAgent
from agents.shaping import get_player_potential

# Watchdog-Timeout für choose(): Hartes Sekunden-Limit pro Zug. Eine normale
# MCTS-Suche braucht <1s; selbst 200 Sims sind in ~0.2s fertig. 30s ist also
# eine sehr großzügige Obergrenze die nur bei einem echten Hänger greift.
# Plattformübergreifend via Thread-Watchdog (Windows hat kein signal.alarm).
_CHOOSE_WATCHDOG_S = 30

def _diff_to_probs(diff: float, scale: float = 10.0) -> dict[int, float]:
    """Normalisiert eine Punktedifferenz auf Win-Wahrscheinlichkeiten via Sigmoid.

    scale steuert die Schärfe: kleine scale = scharfe Diskriminierung kleiner
    Differenzen, große scale = nur große Differenzen werden klar getrennt.
    Default 10.0 passt für echte Score-Differenzen (Endstand). Für die
    Potential-Bewertung im Rollout wird eine kleinere, aktionsabhängige scale
    übergeben (siehe _scale_for_actions), da dort die Differenzen viel kleiner
    sind und scale=10 sie sonst zu nahe 0.5 stauchen würde.
    """
    safe_diff = max(min(diff, 200.0), -200.0)
    p0 = 1.0 / (1.0 + math.exp(-safe_diff / scale))
    return {0: p0, 1: 1.0 - p0}


def _scale_for_actions(num_actions: int) -> float:
    """Aktionsabhängige Sigmoid-scale für die Potential-Bewertung im Rollout.

    Kalibriert an den real gemessenen evaluate_state-Differenzen je Spielphase:
    früh (viele Aktionen) ~1.9, mittel ~4.9, spät ~6.6. Die scale ist so
    gewählt, dass die typische Differenz der jeweiligen Phase eine klare
    Win-Prob (~0.72) ergibt — also scharf genug diskriminiert, ohne zu sättigen.
    Im Frühspiel (viele Optionen) ist die scale klein, damit die feinen
    Draft-Unterschiede (sauber vs. Strafleiste) nicht plattgedrückt werden.
    """
    if num_actions > 50:
        return 2.0
    if num_actions > 15:
        return 5.0
    return 7.0

def _compute_terminal_reward(scores: list[int], state) -> dict[int, float]:
    """
    Berechnet den terminalen Reward aus Spielstand und Startspielerstein.
    Gibt Win-Wahrscheinlichkeiten {0: p0, 1: p1} zurück.
    """
    if scores[0] == 0 and scores[1] == 0:
        diff = 1.0 if state.players[0].holds_first_player_marker else -1.0
    else:
        diff = (scores[0] - scores[1]) * 1.5

    return _diff_to_probs(diff)
# ── MCTS-Knoten ───────────────────────────────────────────────────────────────

class MCTSNode:
    """
    Ein Knoten im MCTS-Baum.

    Jeder Knoten entspricht einem Spielzustand nach einer bestimmten Aktion.
    """

    __slots__ = (
        'action', 'parent', 'children',
        'visits', 'value',
        'untried_actions', 'player_who_acted',
        'priors', 'remaining_actions',
        'virtual_loss',
    )

    def __init__(
        self,
        action: dict | None,
        parent: "MCTSNode | None",
        untried_actions: list[dict],
        player_who_acted: int,
    ):
        self.action          = action          # Aktion die zu diesem Knoten führte
        self.parent          = parent
        self.children:  list["MCTSNode"] = []
        self.visits:    int   = 0
        self.value:     float = 0.0            # kumulierter Reward aus Sicht von player_who_acted
        self.untried_actions    = list(untried_actions) if untried_actions is not None else None
        self.remaining_actions: list = []
        self.player_who_acted = player_who_acted
        self.priors          = None            # NN-Policy-Priors (nur AlphaZero), lazy gesetzt
        self.virtual_loss    = 0                # temporäre Strafe für Leaf-Batching

    def _eff_visits(self) -> int:
        """Besuche inkl. Virtual Loss (für Leaf-Batching)."""
        return self.visits + self.virtual_loss

    def _eff_value(self) -> float:
        """Wert inkl. Virtual Loss: jede virtuelle Strafe zieht den Mittelwert
        Richtung Niederlage (−1 pro virtuellem Besuch)."""
        return self.value - self.virtual_loss

    def ucb1(self, c: float = 0.3) -> float:
        """
        UCB1-Score: balance zwischen Exploitation (bekannt gut) und
        Exploration (wenig besucht).

        UCB1 = Q/N + c * sqrt(ln(N_parent) / N)
        """
        n = self._eff_visits()
        if n == 0:
            return float('inf')
        parent_n = self.parent._eff_visits() if self.parent else 1
        exploit = self._eff_value() / n
        explore = c * math.sqrt(math.log(max(parent_n, 1)) / n)
        return exploit + explore

    def puct(self, c_puct: float, prior: float, parent_visits: int) -> float:
        """
        PUCT-Score (AlphaZero): Q + c_puct * P * sqrt(N_parent) / (1 + N_child).
        Nutzt effektive (virtual-loss-bereinigte) Statistiken.
        """
        n = self._eff_visits()
        q = (self._eff_value() / n) if n > 0 else 0.0
        u = c_puct * prior * math.sqrt(max(parent_visits, 1)) / (1 + n)
        return q + u

    def best_child(self, c: float = 0.3) -> "MCTSNode":
        return max(self.children, key=lambda n: n.ucb1(c))

    def is_fully_expanded(self) -> bool:
        # None bedeutet "noch nicht initialisiert" → noch nicht expandiert
        return self.untried_actions is not None and len(self.untried_actions) == 0

    def is_terminal(self) -> bool:
        return len(self.children) == 0 and self.is_fully_expanded()

    def __repr__(self) -> str:
        q = self.value / self.visits if self.visits else 0
        return (f"MCTSNode(action={self.action['type'] if self.action else 'root'}, "
                f"N={self.visits}, Q={q:.3f})")


# ── MCTS-Agent ────────────────────────────────────────────────────────────────

class MCTSAgent(BaseAgent):
    """
    MCTS-Agent mit UCT (Upper Confidence Bound for Trees).

    Args:
        simulations: Anzahl Simulationen pro Zug. Mehr = stärker aber langsamer.
                     Empfehlung: 50-200 für schnelles Spiel, 500+ für starkes Spiel.
        c:           Explorations-Konstante. Höher = mehr Exploration.
                     Standard: sqrt(2) ≈ 1.414
        rollout_depth: Max Tiefe eines Rollouts. -1 = bis zum Spielende.
        time_limit_s:  Zeitlimit pro Zug in Sekunden (überschreibt simulations wenn gesetzt).
        verbose:       Gibt nach jedem Zug Statistiken aus.
    """

    def __init__(
        self,
        simulations: int = 200,
        c: float = 0.3,
        rollout_depth: int = 30,
        time_limit_s: float | None = None,
        max_actions: int = 10,
        verbose: bool = False,
        dynamic_sims: str | None = None,
    ):
        self.simulations   = simulations
        self.c             = c
        self.rollout_depth = rollout_depth
        self.time_limit_s  = time_limit_s
        self.max_actions   = max_actions   # max Aktionen pro Knoten (Progressive Widening)
        self.verbose       = verbose
        self.dynamic_sims  = dynamic_sims  # None | "selfplay" | "play"
        self._rollout_agent = RandomAgent()

        # ── Vereinheitlichte Suchmaschine: Strategie-Hooks ───────────────────
        # Heuristik- und Netz-Agent teilen dieselbe Suche (Widening, Sim-Scaling,
        # Q-Tiebreaker, Limits). Sie unterscheiden sich NUR über diese Hooks:
        #   _batch_size       : 1 = sequentiell (Heuristik), >1 = Leaf-Batch (Netz)
        #   _uses_priors      : False = UCB1-Selection, True = PUCT mit node.priors
        #   _evaluate_leaves  : wie ein Blatt bewertet wird (Rollout vs. Netz-Value)
        #   _provide_priors   : setzt node.priors (No-Op bei Heuristik)
        # Default = Heuristik-Verhalten (batch_size 1, kein Prior) → die Basis-
        # klasse spielt exakt wie bisher.
        self._batch_size   = 1
        self._uses_priors  = False
        self._c_puct       = 1.5      # nur relevant wenn _uses_priors

        # Dirichlet-Wurzel-Noise (AlphaZero-Standard): zwingt die Suche, an der
        # Wurzel auch nicht-favorisierte Züge zu probieren. Bricht die gegen-
        # seitige Blockade zweier identischer Netze im Self-Play (0:0-Rate) und
        # diversifiziert die Trainingsdaten. NUR im Self-Play aktivieren — in
        # Arena/echtem Spiel will man die unverrauschte Netzstärke. Wirkt nur
        # wenn _uses_priors (Netz-Agent); beim Heuristik-Agent ohne Priors No-Op.
        self._add_root_noise = False
        self._dirichlet_eps  = 0.25   # Noise-Anteil ε
        self._dirichlet_alpha = 0.3   # Streuung α

        # Statistiken
        self.stats: dict = {}

    def _compute_dynamic_sims(self, num_actions: int) -> int:
        """
        Passt die Sim-Zahl an die Anzahl gültiger Aktionen an.
        Die Aktionszahl fällt im Rundenverlauf stark (z.B. 184 → 8),
        was wir nutzen, statt fix gleich viele Sims pro Zug zu nehmen.

        Modi:
          "selfplay" → EFFIZIENZ: bei wenig Aktionen Sims sparen
                       (schnellere Datengenerierung, ~halbe Gesamtzeit).
                       sims = clamp(actions * 0.35, 15, base)
          "play"     → STÄRKE: Budget umverteilen, früh (viele Optionen)
                       mehr Suche. sqrt-Kopplung, moderat.
                       sims = clamp(sqrt(actions) * 10, 40, base*scale)
        """
        import math
        base = self.simulations
        if self.dynamic_sims == "selfplay":
            return max(15, min(base, int(num_actions * 0.35)))
        if self.dynamic_sims == "play":
            # base als Untergrenze-Anker, Obergrenze etwas höher für frühe Züge
            hi = max(base, int(base * 5))
            target = int(base + (math.sqrt(num_actions) * 25))
            
            return max(base, min(hi, target))
        return base

    def choose(self, actions: list[dict], obs: dict) -> dict:
        """
        Wählt die beste Aktion via MCTS.
        Benötigt die MosaicEnv-Instanz — wird über obs['_env'] übergeben
        oder muss via set_env() gesetzt werden.

        Thread-Watchdog: Falls die MCTS-Suche aus irgendeinem Grund hängt
        (seltener, zustandsabhängiger Bug der sich über viele Spiele aufbaut),
        läuft sie in einem Worker-Thread. Kommt nach _CHOOSE_WATCHDOG_S
        Sekunden kein Ergebnis, wird der Thread verworfen (läuft als Daemon
        im Hintergrund aus) und eine zufällige gültige Aktion zurückgegeben,
        damit das Spiel weiterläuft statt ein ganzes Turnier zu blockieren.

        Plattformübergreifend (Windows + Linux) — nutzt threading statt
        signal.alarm, das es unter Windows nicht gibt (kein SIGALRM).
        """
        if len(actions) == 1:
            return actions[0]

        # Shortcut: Wenn end_tiling verfügbar ist und KEINE anderen Tiling-Züge
        # mehr offen sind, direkt zurückgeben — kein MCTS nötig und kein Risiko
        # dass die Suche end_tiling falsch bewertet.
        # Sind gleichzeitig tiling/use_chips verfügbar, wird end_tiling aus der
        # MCTS-Suche herausgehalten (in _sample_actions mit -inf bewertet).
        action_types = set(a.get("type") for a in actions)
        if "end_tiling" in action_types and not (
            action_types & {"tiling", "use_chips"}
        ):
            return next(a for a in actions if a.get("type") == "end_tiling")

        env = getattr(self, '_env', None)
        if env is None:
            # Fallback: zufällig wenn keine Umgebung verfügbar
            return random.choice(actions)

        import threading as _threading

        result_box = {}

        def _worker():
            try:
                result_box["action"] = self._mcts_search(env, actions)
            except Exception as e:
                result_box["error"] = e

        t = _threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(_CHOOSE_WATCHDOG_S)

        if t.is_alive():
            # Watchdog: Suche hängt. Thread läuft als Daemon aus, wir machen weiter.
            print(f"⚠️ [MCTS] Watchdog: choose() nach {_CHOOSE_WATCHDOG_S}s nicht "
                  f"fertig ({len(actions)} Aktionen, phase={env.state.phase}) "
                  f"— zufällige Aktion gewählt. Bitte melden falls dies auftritt.",
                  flush=True)
            return random.choice(actions)

        if "error" in result_box:
            raise result_box["error"]
        return result_box.get("action", random.choice(actions))

    def set_env(self, env: MosaicEnv) -> None:
        """Setzt die aktuelle Spielumgebung für den Agenten."""
        self._env = env

    def _mcts_search(self, env: MosaicEnv, actions: list[dict], return_root: bool = False):
        """Führt MCTS durch und gibt die beste Aktion zurück.
        Mit return_root=True zusätzlich die Wurzel (für Self-Play-Policy-Target)."""
        pi = env.current_player()
        root = MCTSNode(
            action=None,
            parent=None,
            untried_actions=None,   # lazy: wird beim ersten _expand aus env befüllt
            player_who_acted=pi,
        )
        # Dummy-Parent für UCB1-Berechnung
        root.visits = 1

        # Wurzel-Aktionen sofort befüllen (sonst wäre root.priors nutzlos, weil
        # PUCT erst greift wenn Kinder da sind). Ranking via _sample_actions wie
        # in _expand.
        ranked = self._sample_actions(list(actions), env)
        root.untried_actions   = ranked[:self.max_actions]
        root.remaining_actions = ranked[self.max_actions:]

        # Netz-Agent: Wurzel-Priors setzen (Heuristik: No-Op). Ohne das würde
        # PUCT an der Wurzel auf uniform zurückfallen → die gelernte Policy würde
        # an der wichtigsten Stelle ignoriert.
        self._provide_priors(root, env)

        # Dirichlet-Wurzel-Noise (nur Self-Play, nur Netz-Agent mit Priors).
        if self._add_root_noise and self._uses_priors and root.priors is not None:
            self._apply_root_noise(root, list(actions))

        t_start = time.time()
        sims_done = 0

        # Dynamische Sim-Zahl je nach Aktionsanzahl (falls aktiviert)
        sim_target = self._compute_dynamic_sims(len(actions))

        import os as _os
        _mcts_dbg = _os.environ.get("ARENA_DEBUG", "") not in ("", "0")
        # Hartes Sicherheitslimit gegen Hänger: selbst wenn eine innere Phase
        # nie terminiert oder sim_target absurd ist, bricht die Suche nach dem
        # 100-fachen des Sim-Ziels (mind. 100k) ab. Greift IMMER (nicht nur im
        # Debug-Modus), damit ein einzelnes Spiel nie ein ganzes Turnier blockiert.
        _hard_cap = max(100_000, (sim_target or 0) * 100)
        # Absolute Zeit-Notbremse: Selbst wenn eine EINZELNE Simulation hängt
        # (dann zählt sims_done nicht hoch und _hard_cap greift nie), bricht
        # die Suche nach 60s ab. Garantiert dass kein Spiel je ewig hängt.
        _wall_limit = 60.0

        while True:
            # Abbruchbedingung
            if self.time_limit_s is not None:
                if time.time() - t_start >= self.time_limit_s:
                    break
            else:
                if sims_done >= sim_target:
                    break

            # Zeit-Notbremse (greift immer, schützt vor hängender Einzelsim)
            if time.time() - t_start >= _wall_limit:
                print(f"⚠️ [MCTS] Zeit-Notbremse nach {_wall_limit}s! "
                      f"sims_done={sims_done}/{sim_target}, actions={len(actions)}, "
                      f"phase={env.state.phase} — breche Suche ab. "
                      f"Bitte melden falls dies auftritt.", flush=True)
                break

            if sims_done >= _hard_cap:
                # Sollte nie passieren — wenn doch, liegt ein Bug in einer
                # inneren Phase vor. Warnen (immer) und sauber abbrechen.
                print(f"⚠️ [MCTS] HARD CAP {_hard_cap} erreicht nach {time.time()-t_start:.1f}s! "
                      f"sim_target={sim_target}, actions={len(actions)}, "
                      f"phase={env.state.phase} — breche Suche ab (Hänger-Schutz). "
                      f"Bitte melden falls dies auftritt.", flush=True)
                break

            # ── Leaf-Sammlung (Batch) ────────────────────────────────────────
            # batch_size=1 → exakt sequentiell (Heuristik). batch_size>1 → mehrere
            # Leaves gleichzeitig sammeln (Netz-Batch-Inferenz). Virtual Loss
            # verhindert, dass alle Sims im Batch denselben Pfad wählen.
            n_collect = min(self._batch_size, sim_target - sims_done) if self.time_limit_s is None else self._batch_size
            n_collect = max(1, n_collect)

            collected = []  # (leaf_node, sim_env, path)
            terminal_done = []  # (leaf_node, result) — Spielende, sofort bewertbar

            for _ in range(n_collect):
                sim_env = env.clone()
                leaf = self._select(root, sim_env)
                leaf = self._expand(leaf, sim_env)

                # Pfad Wurzel→Leaf für Virtual-Loss-Rücknahme + Backprop merken
                path = []
                n = leaf
                while n is not None:
                    path.append(n)
                    n = n.parent

                # Terminal? → echtes Ergebnis, kein Netz/Rollout nötig
                if sim_env.state.phase in ("end", "final"):
                    result = self._terminal_result(sim_env)
                    terminal_done.append((leaf, path, result))
                else:
                    # Virtual Loss auf den ganzen Pfad legen (nur bei Batching >1)
                    if self._batch_size > 1:
                        for nd in path:
                            nd.virtual_loss += 1
                    collected.append((leaf, sim_env, path))

            # ── Terminal-Leaves sofort backpropagieren ───────────────────────
            for leaf, path, result in terminal_done:
                self._backpropagate(leaf, result, pi)
                sims_done += 1

            # ── Nicht-terminale Leaves bewerten (Hook: Rollout ODER Netz-Batch)
            if collected:
                leaf_envs = [(c[0], c[1]) for c in collected]  # (node, env)
                results = self._evaluate_leaves(leaf_envs)  # Liste von result-Dicts
                for (leaf, sim_env, path), result in zip(collected, results):
                    # Virtual Loss zurücknehmen
                    if self._batch_size > 1:
                        for nd in path:
                            nd.virtual_loss -= 1
                    self._backpropagate(leaf, result, pi)
                    sims_done += 1

        # Bestes Kind: höchste Besuchsanzahl (robusteste Auswahl).
        # Bei Gleichstand in Besuchen: Q-Wert (value/visits) als Tiebreaker.
        # Das verhindert dass bei ~gleich oft erkundeten Zügen zufällig der
        # erste in der Liste gewählt wird statt der qualitativ bessere.
        if not root.children:
            return (random.choice(actions), None) if return_root else random.choice(actions)

        best = max(root.children,
                   key=lambda n: (n.visits,
                                  n.value / n.visits if n.visits else 0.0))

        if self.verbose:
            elapsed = time.time() - t_start
            q = best.value / best.visits if best.visits else 0
            top3 = sorted(root.children, key=lambda n: n.visits, reverse=True)[:3]
            print(f"\n[MCTS] {sims_done} Sims in {elapsed*1000:.0f}ms | "
                  f"Best: {best.action['type']} N={best.visits} Q={q:.3f}")
            for n in top3:
                q_n = n.value/n.visits if n.visits else 0
                print(f"       {n.action['type']:12s} N={n.visits:4d} Q={q_n:.3f}")

        self.stats = {
            "simulations": sims_done,
            "best_visits": best.visits,
            "best_q": best.value / best.visits if best.visits else 0,
            "tree_size": sum(1 for _ in self._iter_nodes(root)),
        }

        return (best.action, root) if return_root else best.action

    # ── MCTS-Phasen ───────────────────────────────────────────────────────────

    def _select(self, node: MCTSNode, env: MosaicEnv) -> MCTSNode:
        """
        Traversiere den Baum. Integriertes Progressive Widening:
        Entscheidet, ob wir absteigen, oder auf dieser Ebene eine 
        neue Aktion aus dem Pool freischalten.

        Selection-Kriterium: UCB1 (Heuristik) oder PUCT mit node.priors (Netz).
        Beide nutzen virtual-loss-bereinigte Statistiken (Leaf-Batching).
        """
        while node.children:
            # --- 1. PROGRESSIVE WIDENING CHECK ---
            if node.remaining_actions is not None and len(node.remaining_actions) > 0:
                # SUBLINEARES WACHSTUM: Wurzel aus Besuchen.
                # Wächst anfangs moderat, flacht dann ab, um Deepening zu erzwingen!
                allowed_actions = self.max_actions + int(math.sqrt(node._eff_visits()) * 2.5)

                current_actions = len(node.children) + len(node.untried_actions)

                if current_actions < allowed_actions:
                    node.untried_actions.append(node.remaining_actions.pop(0))
                    return node

            # --- 2. SIND NOCH FREIGESCHALTETE ZÜGE UNVERSUCHT? ---
            if node.untried_actions:
                return node # _expand kümmert sich um den Test

            # --- 3. ABSTIEG ZUM KIND ---
            # Für die aktuelle Anzahl an Besuchen ist dieser Knoten "vollständig".
            # Wir steigen tiefer in den Baum ab.
            node = self._best_child(node)
            obs, _, done, _ = env.step(node.action)
            if done:
                return node

        return node

    def _best_child(self, node: MCTSNode) -> MCTSNode:
        """Wählt das beste Kind: PUCT wenn Priors aktiv, sonst UCB1."""
        if self._uses_priors and node.priors is not None:
            from agents.neural_net import action_to_id
            parent_visits = node._eff_visits()
            # Prior-Normalisierung über die legalen Kinder
            valid_p_sum = 0.0
            for ch in node.children:
                valid_p_sum += node.priors[action_to_id(ch.action)]
            valid_p_sum = valid_p_sum or 1.0

            def _score(ch):
                p = node.priors[action_to_id(ch.action)] / valid_p_sum
                return ch.puct(self._c_puct, p, parent_visits)
            return max(node.children, key=_score)
        # Default: UCB1
        return node.best_child(self.c)

    def _expand(self, node: MCTSNode, env: MosaicEnv) -> MCTSNode:
        # Lazy Init: Beim allerersten Aufruf befüllen
        if node.untried_actions is None:
            all_actions = env.valid_actions()
            is_root = node.parent is None
            ranked = self._sample_actions(all_actions, env if is_root else None)
            node.untried_actions = ranked[:self.max_actions]
            node.remaining_actions = ranked[self.max_actions:]
            
        if not node.untried_actions:
            return node

        # Ziehe eine freigeschaltete Aktion
        action = node.untried_actions.pop(
            random.randrange(len(node.untried_actions))
        )
        
        mover = env.current_player()
        obs, _, done, _ = env.step(action)

        child = MCTSNode(
            action=action,
            parent=node,
            untried_actions=[] if done else None,
            player_who_acted=mover,
        )

        node.children.append(child)
        return child

    def _rollout(self, env: MosaicEnv) -> dict[int, float]:
        """
        Blattbewertung. rollout_depth ist projektweit 0 → keine Ausspiel-Schleife,
        sofortige terminale Bewertung des aktuellen Zustands. (Die Heuristik-
        Subklasse überschreibt dies mit Greedy-Shaping.)
        """
        scores = env.scores()
        return _compute_terminal_reward(scores, env.state)

    def _backpropagate(
        self,
        node: MCTSNode,
        result: dict[int, float],
        root_player: int,
    ) -> None:
        """
        Propagiere das Rollout-Ergebnis zurück bis zur Wurzel.
        Jeder Knoten wird aus Sicht des Spielers bewertet der den Zug gemacht hat.
        """
        while node is not None:
            node.visits += 1
            # Wert aus Sicht des Spielers der zu diesem Knoten geführt hat
            node.value += result.get(node.player_who_acted, 0.0)
            node = node.parent

    # ── Strategie-Hooks (von Subklassen überschrieben) ────────────────────────

    def _terminal_result(self, sim_env: MosaicEnv) -> dict[int, float]:
        """Ergebnis eines beendeten Spiels (Win/Loss/Tie über Score)."""
        from engine.game import determine_winner
        w = determine_winner(sim_env.state)
        return {w: 1.0, 1 - w: 0.0}

    def _evaluate_leaves(self, leaves: list) -> list[dict[int, float]]:
        """
        Bewertet eine Liste nicht-terminaler Leaves. Eingabe: Liste von
        (node, env)-Paaren. Basis (Heuristik): pro Leaf ein Greedy-Rollout.
        Subklassen (Netz) überschreiben dies mit einem Batch-Forward-Pass und
        setzen dabei node.priors.
        """
        return [self._rollout(env) for (_node, env) in leaves]

    def _provide_priors(self, node: MCTSNode, env: MosaicEnv) -> None:
        """Setzt node.priors (No-Op bei Heuristik; Netz überschreibt)."""
        pass

    def _apply_root_noise(self, root: MCTSNode, actions: list[dict]) -> None:
        """
        Mischt Dirichlet-Noise auf die Wurzel-Priors der legalen Aktionen:
            P(a) = (1-ε)·P_netz(a) + ε·noise(a)
        Nur die Action-IDs der legalen Züge werden verrauscht — der Rest des
        Prior-Vektors bleibt unangetastet (irrelevant, da nie expandiert).
        """
        try:
            from agents.neural_net import action_to_id
            import numpy as _np
            ids = [action_to_id(a) for a in actions]
            ids = [i for i in ids if 0 <= i < len(root.priors)]
            if len(ids) < 2:
                return
            noise = _np.random.dirichlet([self._dirichlet_alpha] * len(ids))
            eps = self._dirichlet_eps
            for idx, aid in enumerate(ids):
                root.priors[aid] = (1.0 - eps) * root.priors[aid] + eps * noise[idx]
        except Exception:
            pass  # Noise ist optional — bei Fehler einfach ohne weiter

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _sample_actions(self, actions: list[dict], env: "MosaicEnv" = None) -> list[dict]:
        """
        Wählt die besten max_actions Aktionen aus.

        Wenn env übergeben wird, werden die Aktionen nach ihrem Shaping-Reward
        (dieselbe Größe, die der Greedy-Rollout als "gut" bewertet) sortiert und
        die besten zuerst genommen. So landen die vielversprechendsten Züge im
        Suchbaum, statt zufällig ausgewählter — wichtig, weil bei vielen Optionen
        (z.B. ~100 Kuppelplatzierungen) sonst der beste Zug fast nie in den Baum
        kommt und die Suche ihn nie finden kann.

        Ohne env (Fallback) wird die alte typ-priorisierte Zufallsauswahl genutzt.

        Gibt die VOLLSTÄNDIGE Aktionsliste sortiert zurück (beste zuerst), damit
        der Aufrufer die ersten max_actions als erste Welle nimmt und den Rest
        (ebenfalls nach Güte sortiert) für Progressive Widening aufhebt.
        """
        if len(actions) <= self.max_actions:
            return list(actions)

        if env is not None:
            # Aktionen nach Güte sortieren.
            # Dome-Aktionen: score_dome_action() nutzen (Shaping-Reward ist
            # bei dome ~0 weil der Wert zukunftsbezogen ist).
            # Stone/andere: normaler Shaping-Reward via clone+step.
            #
            # SKALIERUNGS-PROBLEM: score_dome_action() gibt Werte ~1-8 zurück
            # (Summe über 4 Spaces × Reihen-Wahrscheinlichkeit × Reihen-Punkte),
            # während Stone-Shaping-Rewards typisch ~-2 bis +2 liegen.
            # Ohne Normalisierung verdrängen Dome-Aktionen alle Stone-Züge aus
            # den Top-max_actions → KI sieht nur Kuppelplatten und ignoriert
            # komplett das Stein-Drafting.
            #
            # Lösung: Separate Quoten. Die Top-max_actions werden aufgeteilt:
            # - dome_quota Plätze für die besten Kuppelzüge
            # - der Rest für die besten Stone/anderen Züge
            # So landet immer ein Mix beider Typen in der Suche.
            #
            # end_tiling: -inf wenn andere Tiling-Züge offen (500-Züge-Bug-Fix).
            from agents.shaping import score_dome_action
            has_other_tiling = any(
                a.get("type") in ("tiling", "use_chips")
                for a in actions
            )
            state = env.state
            pi = env.current_player()
            player = state.players[pi]

            dome_scored = []
            other_scored = []

            for a in actions:
                try:
                    t = a.get("type")
                    if t == "end_tiling" and has_other_tiling:
                        r = -float("inf")
                        other_scored.append((r, a))
                    elif t in ("dome", "dome_stack"):
                        r = score_dome_action(a, player, state)
                        dome_scored.append((r, a))
                    else:
                        te = env.clone()
                        _, r, _, _ = te.step(a)
                        other_scored.append((r, a))
                except Exception:
                    other_scored.append((-float("inf"), a))

            dome_scored.sort(key=lambda x: x[0], reverse=True)
            other_scored.sort(key=lambda x: x[0], reverse=True)
            # wenn nur einer vorhanden, bekommt er alle Plätze.
            if dome_scored and other_scored:
                dome_quota  = max(1, self.max_actions // 2)
                other_quota = max(1, self.max_actions - dome_quota)
            elif dome_scored:
                dome_quota  = self.max_actions
                other_quota = 0
            else:
                dome_quota  = 0
                other_quota = self.max_actions

            top = ([a for _, a in dome_scored[:dome_quota]] +
                   [a for _, a in other_scored[:other_quota]])
            remaining = ([a for _, a in dome_scored[dome_quota:]] +
                         [a for _, a in other_scored[other_quota:]])
            # remaining ebenfalls nach Score sortiert für Progressive Widening
            remaining.sort(key=lambda a: next(
                (s for s, x in dome_scored + other_scored if x is a), -float("inf")
            ), reverse=True)
            return top + remaining

        # Fallback ohne env: typ-priorisierte Zufallsauswahl.
        # end_tiling bekommt NIEDRIGSTE Priorität wenn andere Tiling-Züge offen sind,
        # damit es nie ausgewählt wird solange platzierbare Reihen vorhanden sind.
        has_other_tiling_fb = any(
            a.get("type") in ("tiling", "use_chips") for a in actions
        )
        priority = {
            "tiling":     8,
            "use_chips":  7,
            "end_tiling": 0 if has_other_tiling_fb else 6,  # last resort wenn andere offen
            "bonus_chip": 6,
            "stone":      4,
            "dome":       3,
            "dome_stack": 2,
            "pass":       1,
        }
        by_type: dict[str, list] = {}
        for a in actions:
            by_type.setdefault(a["type"], []).append(a)

        # Sortiere Typen nach Priorität
        sorted_types = sorted(by_type.keys(), key=lambda t: priority.get(t, 0), reverse=True)

        result = []
        per_type = max(1, self.max_actions // len(sorted_types))
        for t in sorted_types:
            pool = by_type[t]
            random.shuffle(pool)
            result.extend(pool[:per_type])
            if len(result) >= self.max_actions:
                break

        # Falls noch Platz: fülle mit weiteren zufälligen Aktionen auf
        remaining = [a for a in actions if a not in result]
        random.shuffle(remaining)
        if len(result) < self.max_actions and remaining:
            take = self.max_actions - len(result)
            result.extend(remaining[:take])
            remaining = remaining[take:]

        # Vollständige Liste zurückgeben: erst die ausgewählten (erste Welle),
        # dann der Rest (für Progressive Widening) — konsistent mit dem env-Pfad,
        # damit _expand korrekt in [:max_actions] und [max_actions:] aufteilen kann.
        return result + remaining

    def _iter_nodes(self, node: MCTSNode):
        yield node
        for child in node.children:
            yield from self._iter_nodes(child)


# ── MCTSAgent in run_episode integrieren ─────────────────────────────────────

def run_episode_mcts(
    agents: list[BaseAgent],
    seed: int | None = None,
    random_scoring_tiles: bool = True,
    max_steps: int = 500,
    verbose: bool = False,
) -> dict:
    """Dünner Wrapper um run_episode: erzeugt das Env (mit random_scoring_tiles)
    und delegiert an den einheitlichen Spiel-Loop. set_env für MCTS-Agenten
    übernimmt run_episode selbst (hasattr-Guard).

    Beibehalten für Rückwärtskompatibilität (arena.py ruft diese Signatur).
    """
    from agents.agents import run_episode
    env = MosaicEnv(random_scoring_tiles=random_scoring_tiles)
    return run_episode(env, agents, seed=seed, max_steps=max_steps, verbose=verbose)


def evaluate_state(state) -> dict[int, float]:
    """
    Bewertet den aktuellen Spielstand heuristisch, ohne ihn bis zum Ende zu spielen.
    Spiegelt exakt das Reward-Shaping des Neuronalen Netzes wider!
    """
    from engine.serializer import _estimate_round_score

    round_number = getattr(state, "round_number", 1)
    scoring_tile_ids = getattr(state, "scoring_tile_ids", [])

    evaluations = {}
    for pi in [0, 1]:
        p = state.players[pi]

        # Echte Punkte + Schätzung (Reihen-Punkte stecken im potential via
        # complete_bonus → include_rows=False verhindert Doppelzählung)
        base_score = p.score
        est_score = _estimate_round_score(p, include_rows=False)

        # Potenzial mit Runde + aktiven Wertungsplatten
        potential = get_player_potential(
            p,
            round_number=round_number,
            scoring_tile_ids=scoring_tile_ids,
        )

        evaluations[pi] = base_score + est_score + potential

    # Tie-Breaker
    if evaluations[0] == evaluations[1]:
        if state.players[0].holds_first_player_marker:
            evaluations[0] += 0.1
        else:
            evaluations[1] += 0.1

    return evaluations



class HeuristicMCTSAgent(MCTSAgent):
    """
    Ein MCTS-Agent, der NICHT mehr zufällig bis zum Ende spielt,
    sondern das Brett nach wenigen Schritten (oder sofort) intelligent bewertet.
    Nutzt Greedy-Bias mit Shaping-Rewards für die Rollouts!
    """
    def __init__(self, simulations=200, rollout_depth=3, **kwargs):
        super().__init__(simulations=simulations, rollout_depth=rollout_depth, **kwargs)

    # Obergrenze für "gratis" durchlaufene Kuppelzüge im Rollout (Schutz gegen
    # zu lange/teure Rollouts bei ausgedehnten Kuppelphasen; gemessener Median
    # einer Kuppelphase ~9, Max ~15).
    def _rollout(self, env):
        """Blattbewertung des Heuristik-Agents: Greedy-Shaping über evaluate_state.

        rollout_depth ist projektweit 0 → kein Ausspielen, sofortige Bewertung
        des aktuellen Zustands. Die Potential-Differenz beider Spieler wird über
        eine aktionsabhängige Skala in Win-Wahrscheinlichkeiten übersetzt.

        (Früher lief hier optional ein tiefenbegrenztes Greedy-Rollout mit
        Kuppel-Passthrough. Da rollout_depth nie > 0 genutzt wird, ist diese
        Schleife entfallen — sie wäre toter Code gewesen.)
        """
        evals = evaluate_state(env.state)
        # Aktionsabhängige scale: im Frühspiel (viele Optionen) klein, damit
        # die feinen Potential-Unterschiede zwischen Drafts nicht zu nahe 0.5
        # gestaucht werden (sonst flache Policy-Targets → Strafleisten-Fluten).
        scale = _scale_for_actions(len(env.valid_actions()))
        return _diff_to_probs(evals[0] - evals[1], scale=scale)