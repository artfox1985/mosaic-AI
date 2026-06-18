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

    def ucb1(self, c: float = 1.414) -> float:
        """
        UCB1-Score: balance zwischen Exploitation (bekannt gut) und
        Exploration (wenig besucht).

        UCB1 = Q/N + c * sqrt(ln(N_parent) / N)
        """
        if self.visits == 0:
            return float('inf')
        exploit = self.value / self.visits
        explore = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploit + explore

    def best_child(self, c: float = 1.414) -> "MCTSNode":
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
        c: float = 1.414,
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

    def _mcts_search(self, env: MosaicEnv, actions: list[dict]) -> dict:
        """Führt MCTS durch und gibt die beste Aktion zurück."""
        pi = env.current_player()
        root = MCTSNode(
            action=None,
            parent=None,
            untried_actions=None,   # lazy: wird beim ersten _expand aus env befüllt
            player_who_acted=pi,
        )
        # Dummy-Parent für UCB1-Berechnung
        root.visits = 1

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

            # Eine Simulation
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)

            sims_done += 1

        # Bestes Kind: höchste Besuchsanzahl (robusteste Auswahl).
        # Bei Gleichstand in Besuchen: Q-Wert (value/visits) als Tiebreaker.
        # Das verhindert dass bei ~gleich oft erkundeten Zügen zufällig der
        # erste in der Liste gewählt wird statt der qualitativ bessere.
        if not root.children:
            return random.choice(actions)

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

        return best.action

    # ── MCTS-Phasen ───────────────────────────────────────────────────────────

    def _select(self, node: MCTSNode, env: MosaicEnv) -> MCTSNode:
        """
        Traversiere den Baum. Integriertes Progressive Widening:
        Entscheidet, ob wir absteigen, oder auf dieser Ebene eine 
        neue Aktion aus dem Heuristik-Pool freischalten.
        """
        while node.children:
            # --- 1. PROGRESSIVE WIDENING CHECK ---
            if node.remaining_actions is not None and len(node.remaining_actions) > 0:
                # SUBLINEARES WACHSTUM: Wurzel aus Besuchen.
                # Wächst anfangs moderat, flacht dann ab, um Deepening zu erzwingen!
                # Faktor 2.5 bedeutet: Bei 100 Besuchen -> +25 Aktionen, bei 400 Besuchen -> +50 Aktionen
                allowed_actions = self.max_actions + int(math.sqrt(node.visits) * 2.5)
                
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
            node = node.best_child(self.c)
            obs, _, done, _ = env.step(node.action)
            if done:
                return node
                
        return node

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
        Spiele bis rollout_depth Schritte mit Greedy-Bias.
        rollout_depth=-1 → bis Spielende
        rollout_depth=0  → sofortige Heuristik
        """
        start = time.perf_counter()
        depth = 0
        done = False

        while not done and (self.rollout_depth < 0 or depth < self.rollout_depth):
            actions = env.valid_actions()
            if not actions: 
                break
            
            # Greedy-Bias: 3 Aktionen testen, beste ausführen
            best_action = random.choice(actions)  # Fallback
            best_val = -float('inf')

            for a in random.sample(actions, min(3, len(actions))):
                test_env = env.clone()
                _, r, _, _ = test_env.step(a)
                if r > best_val:
                    best_val = r
                    best_action = a

            _, _, done, _ = env.step(best_action)
            depth += 1

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
    """
    Wie run_episode, aber übergibt die Umgebung an MCTS-Agenten.
    """
    import time
    from agents.agents import run_episode

    env = MosaicEnv(random_scoring_tiles=random_scoring_tiles)

    # Env an MCTS-Agenten übergeben
    for agent in agents:
        if isinstance(agent, MCTSAgent):
            agent.set_env(env)

    t0 = time.time()
    obs, info = env.reset(seed=seed)
    total_rewards = [0.0, 0.0]
    steps = 0
    done = False
    action_counts = []   # Anzahl valider Züge pro Step

    # Debug-Logging per Umgebungsvariable ARENA_DEBUG=1 aktivierbar.
    # Loggt vor jedem kritischen Aufruf mit Flush, sodass bei einem Hänger
    # die letzte sichtbare Zeile zeigt WO es steckenbleibt.
    import os
    _dbg = os.environ.get("ARENA_DEBUG", "") not in ("", "0")
    def _d(msg):
        if _dbg:
            print(f"    [DBG s={steps:3d} t={time.time()-t0:6.1f}s] {msg}", flush=True)

    while steps < max_steps and not done:
        _d(f"phase={env.state.phase} → valid_actions()")
        actions = env.valid_actions()
        if not actions:
            _d("keine Aktionen → break")
            break

        action_counts.append(len(actions))

        pi = env.current_player()
        agent = agents[pi]
        _d(f"P{pi} {type(agent).__name__} choose() aus {len(actions)} Aktionen "
           f"(sims={getattr(agent,'simulations','?')}, depth={getattr(agent,'rollout_depth','?')})")

        action = agent.choose(actions, obs)
        _d(f"P{pi} gewählt: {action.get('type')} → step()")
        obs, reward, done, step_info = env.step(action)
        if step_info.get("error"):
            _d(f"⚠️ step error: {step_info['error']}")
        total_rewards[pi] += reward
        steps += 1

        if verbose and steps % 20 == 0:
            print(f"  Step {steps:3d} | P{pi} {action['type']:12s} | "
                  f"reward={reward:+.1f} | scores={env.scores()}")

    scores = env.scores()
    
    # 1. Sieger nach Punkten
    if scores[0] > scores[1]:
        winner = 0
    elif scores[1] > scores[0]:
        winner = 1
    else:
        # 2. TIE-BREAKER: Bei Gleichstand gewinnt der Besitzer des Startspieler-Markers!
        # Einer der beiden Spieler muss ihn zwingend haben.
        if env.state.players[0].holds_first_player_marker:
            winner = 0
        else:
            winner = 1

    # LOG-AUSGABE FÜR DIE ARENA ---
    if verbose:
        print("\n" + "="*60)
        print("📜 ARENA SPIEL-LOG (Rundenende & Punkte)")
        print("="*60)
        log_entries = getattr(env.state, 'log', [])
        if not log_entries:
            print("Kein Log gefunden.")
        else:
            for entry in log_entries:
                print(entry)
        print("="*60 + "\n")

    avg_actions = round(sum(action_counts) / len(action_counts), 1) if action_counts else 0.0
    max_actions = max(action_counts) if action_counts else 0

    result = {
        "scores":           scores,
        "winner":           winner,
        "steps":            steps,
        "rewards":          total_rewards,
        "scoring_tile_ids": info.get("scoring_tile_ids", []),
        "scoring_names":    info.get("scoring_tile_names", []),
        "duration_s":       round(time.time() - t0, 3),
        "avg_actions":      avg_actions,
        "max_actions":      max_actions,
        "state":            env.state
    }
    
    return result

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
    _DOME_PASSTHROUGH_CAP = 10

    def _rollout(self, env):
        """Überschreibt das Rollout: Nutzt Greedy-Shaping statt Zufall!

        Dynamische Tiefe bei Kuppelzügen: Der Wert einer Kuppelplatten-
        Platzierung zeigt sich erst, wenn das Fundament steht (Steine darauf
        kommen). Eine Bewertung MITTEN in der Kuppel-Auslegung ist daher wenig
        aussagekräftig. Deshalb verbrauchen Kuppelzüge (dome/dome_stack) KEIN
        Tiefenbudget — das Rollout läuft durch sie hindurch, bis das Fundament
        gelegt ist, und erst Nicht-Kuppelzüge zählen gegen rollout_depth.
        Eine Obergrenze (_DOME_PASSTHROUGH_CAP) verhindert, dass das Rollout
        bei langen Kuppelphasen entgleist (Rechenzeit + akkumuliertes
        Greedy-Rauschen).
        """
        depth = 0
        done = False
        dome_passthrough = 0
        _DOME_TYPES = ("dome", "dome_stack")

        # Spiele weiter, solange das Tiefenbudget (für Nicht-Kuppelzüge) reicht.
        while not done and (self.rollout_depth < 0 or depth < self.rollout_depth):
            actions = env.valid_actions()
            if not actions:
                break

            # --- GREEDY-BIAS ---
            best_action = random.choice(actions) # Fallback
            best_reward = -float('inf')
            sample_actions = random.sample(actions, min(5, len(actions)))
            for a in sample_actions:
                test_env = env.clone()
                _, r, _, _ = test_env.step(a)
                if r > best_reward:
                    best_reward = r
                    best_action = a

            _, _, done, _ = env.step(best_action)

            # Kuppelzüge zählen NICHT gegen die Tiefe (Fundament durchlaufen),
            # bis zu einer Sicherheitsobergrenze.
            is_dome = best_action.get("type") in _DOME_TYPES
            if is_dome and dome_passthrough < self._DOME_PASSTHROUGH_CAP:
                dome_passthrough += 1
            else:
                depth += 1

        # --- DER MAGISCHE MOMENT: Die Heuristik übernimmt ---
        if done:
            scores = env.scores()
            return _compute_terminal_reward(scores, env.state)
        else:
            evals = evaluate_state(env.state)
            # Aktionsabhängige scale: im Frühspiel (viele Optionen) klein, damit
            # die feinen Potential-Unterschiede zwischen Drafts nicht zu nahe 0.5
            # gestaucht werden (sonst flache Policy-Targets → Strafleisten-Fluten).
            scale = _scale_for_actions(len(env.valid_actions()))
            return _diff_to_probs(evals[0] - evals[1], scale=scale)