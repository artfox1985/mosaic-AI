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

def _diff_to_probs(diff: float) -> dict[int, float]:
    """Normalisiert eine Punktedifferenz auf Win-Wahrscheinlichkeiten via Sigmoid."""
    scale = 10.0
    safe_diff = max(min(diff, 200.0), -200.0)
    p0 = 1.0 / (1.0 + math.exp(-safe_diff / scale))
    return {0: p0, 1: 1.0 - p0}

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
        max_actions: int = 20,
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
            hi = max(base, int(base * 3))
            return max(base, min(hi, int(math.sqrt(num_actions) * 10)))
        return base

    def choose(self, actions: list[dict], obs: dict) -> dict:
        """
        Wählt die beste Aktion via MCTS.
        Benötigt die MosaicEnv-Instanz — wird über obs['_env'] übergeben
        oder muss via set_env() gesetzt werden.
        """
        if len(actions) == 1:
            return actions[0]

        env = getattr(self, '_env', None)
        if env is None:
            # Fallback: zufällig wenn keine Umgebung verfügbar
            return random.choice(actions)

        return self._mcts_search(env, actions)

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

        while True:
            # Abbruchbedingung
            if self.time_limit_s is not None:
                if time.time() - t_start >= self.time_limit_s:
                    break
            else:
                if sims_done >= sim_target:
                    break

            # Eine Simulation
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)

            sims_done += 1

        # Bestes Kind: höchste Besuchsanzahl (robusteste Auswahl)
        if not root.children:
            return random.choice(actions)

        best = max(root.children, key=lambda n: n.visits)

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
        Traversiere den Baum entlang UCB1-maximaler Kinder bis zu einem
        Knoten der noch unerkundete Aktionen hat.
        """
        while node.is_fully_expanded() and node.children:
            node = node.best_child(self.c)
            obs, _, done, _ = env.step(node.action)
            if done:
                return node
        return node

    def _expand(self, node: MCTSNode, env: MosaicEnv) -> MCTSNode:
        """
        Wähle eine unerkundete Aktion, führe sie aus und füge
        einen neuen Kindknoten hinzu.

        untried_actions wird lazy befüllt: beim ersten Expand eines Knotens
        werden die gültigen Aktionen frisch aus dem aktuellen env-Zustand
        generiert. Das verhindert dass veraltete Aktionen (z.B. Kacheln die
        bereits platziert wurden) ausgeführt werden.
        """
        # Lazy Init: frisch aus aktuellem env-Zustand befüllen
        # Progressive Widening: starte mit max_actions, erweitere mit mehr Besuchen
        if node.untried_actions is None:
            all_actions = env.valid_actions()
            # Erste Welle: max_actions
            sampled = self._sample_actions(all_actions)
            node.untried_actions = sampled
            # Restliche Aktionen für spätere Erweiterung aufbewahren
            remaining = [a for a in all_actions if a not in sampled]
            node.remaining_actions = remaining if remaining else []
        
        # Progressive Widening: neue Aktionen freischalten wenn Knoten oft besucht
        if node.remaining_actions:
            # Alle k Besuche eine neue Aktion hinzufügen
            k = max(3, self.max_actions // 4)
            extra = max(0, node.visits // k - (self.max_actions - len(node.untried_actions)))
            if extra > 0 and node.remaining_actions:
                for _ in range(min(extra, len(node.remaining_actions))):
                    node.untried_actions.append(node.remaining_actions.pop(0))

        if not node.untried_actions:
            return node

        action = node.untried_actions.pop(
            random.randrange(len(node.untried_actions))
        )
        # WICHTIG: Spieler VOR dem step auslesen — step() wechselt den Spieler,
        # danach würde env.current_player() den FOLGE-Spieler liefern und der
        # Knotenwert würde aus der falschen Perspektive verbucht.
        mover = env.current_player()
        obs, _, done, _ = env.step(action)

        if done:
            child = MCTSNode(
                action=action,
                parent=node,
                untried_actions=[],
                player_who_acted=mover,
            )
        else:
            child = MCTSNode(
                action=action,
                parent=node,
                untried_actions=None,  # lazy: beim nächsten _expand befüllt
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

    def _sample_actions(self, actions: list[dict]) -> list[dict]:
        """
        Samplet max_actions Aktionen mit Typ-Priorisierung:
        tiling > end_tiling > bonus_chip > stone > dome > dome_stack > pass
        Innerhalb jedes Typs wird zufällig gemischt.
        """
        if len(actions) <= self.max_actions:
            return list(actions)

        priority = {"tiling":8,"end_tiling":7,"bonus_chip":6,"stone":4,"dome":3,"dome_stack":2,"pass":1}
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
        if len(result) < self.max_actions and remaining:
            random.shuffle(remaining)
            result.extend(remaining[:self.max_actions - len(result)])

        return result[:self.max_actions]

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

    while steps < max_steps and not done:
        actions = env.valid_actions()
        if not actions:
            break

        action_counts.append(len(actions))

        pi = env.current_player()
        agent = agents[pi]

        action = agent.choose(actions, obs)
        obs, reward, done, step_info = env.step(action)
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
    }
    
    return result

def evaluate_state(state) -> dict[int, float]:
    """
    Bewertet den aktuellen Spielstand heuristisch, ohne ihn bis zum Ende zu spielen.
    Spiegelt exakt das Reward-Shaping des Neuronalen Netzes wider!
    """
    from engine.serializer import _estimate_round_score
    
    evaluations = {}
    for pi in [0, 1]:
        p = state.players[pi]
        
        # 1. Echte Punkte + Schätzung (NUR Strafen/Marker — die Reihen-Punktwerte
        #    stecken jetzt im potential über den complete_bonus, also include_rows=False
        #    um Doppelzählung zu vermeiden)
        base_score = p.score
        est_score = _estimate_round_score(p, include_rows=False)
        
        # 2. Potenzial des Boards laden (Unsere neue Funktion!)
        potential = get_player_potential(p)
            
        evaluations[pi] = base_score + est_score + potential

    # --- Tie-Breaker Bonus ---
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

    def _rollout(self, env):
        """Überschreibt das Rollout: Nutzt Greedy-Shaping statt Zufall!"""
        depth = 0
        done = False

        # Spiele noch 'rollout_depth' Züge GREEDY weiter, um taktische Fehler zu vermeiden
        while not done and (self.rollout_depth < 0 or depth < self.rollout_depth):
            actions = env.valid_actions()
            if not actions:
                break
            
            # --- GREEDY-BIAS ---
            # Statt random.choice() testen wir ein paar Aktionen kurz an
            best_action = random.choice(actions) # Fallback
            best_reward = -float('inf')
            
            # Wir testen max 5 Aktionen (Performance-Schutz für MCTS)
            sample_actions = random.sample(actions, min(5, len(actions)))
            
            for a in sample_actions:
                test_env = env.clone()
                # Teste den Zug und schau, was das Shaping-System dazu sagt
                _, r, _, _ = test_env.step(a)
                if r > best_reward:
                    best_reward = r
                    best_action = a
            
            # Führe die beste Aktion in der echten Rollout-Umgebung aus
            _, _, done, _ = env.step(best_action)
            depth += 1

        # --- DER MAGISCHE MOMENT: Die Heuristik übernimmt ---
        if done:
            scores = env.scores()
            return _compute_terminal_reward(scores, env.state)
        else:
            evals = evaluate_state(env.state)
            return _diff_to_probs(evals[0] - evals[1])