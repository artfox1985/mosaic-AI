"""
self_play.py — Self-Play Datengenerierung für Mosaic-AI

Unterstützt zwei Modi:
  --mode mcts      Verwendet HeuristicMCTSAgent (kein Netz, für erste Generation)
  --mode network   Verwendet AlphaZeroAgent (mit trainiertem Netz)

Verwendung:
  python self_play.py --mode mcts    --games 1500 --sims 50  --version v0
  python self_play.py --mode network --games 1500 --sims 40  --version v1
"""
import os
import time
import copy
import pickle
import random
from datetime import datetime
import argparse

from agents.agent_env import MosaicEnv
from agents.mcts import MCTSNode, HeuristicMCTSAgent
from config import MODELS_DIR, DATA_DIR, INPUT_SIZE, NUM_ACTIONS


# ---------------------------------------------------------------------------
# Gemeinsame Self-Play Logik
# ---------------------------------------------------------------------------

class SelfPlayMixin:
    """
    Mixin für Self-Play: erweitert einen MCTS-Agenten um search_and_get_policy.
    Führt alle Simulationen durch und gibt Policy + gewählte Aktion zurück.
    Temperature steuert Schärfe der Policy:
      temp=1.0 → proportional zu Visits (explorativ)
      temp=0.5 → moderater Fokus
      temp=0.1 → fast deterministisch
      temp=0.0 → argmax
    """

    def _selfplay_sim_count(self, num_actions: int) -> int:
        """Dynamische Sim-Zahl für Self-Play — immer play-Modus.
        Gibt im Frühspiel (viele Aktionen) mehr Sims für schärfere Policy-Targets,
        skaliert mit sqrt(num_actions) * 10, begrenzt auf [base, base*3]."""
        import math
        return max(self.simulations,
                   min(self.simulations * 3, int(math.sqrt(num_actions) * 10)))

    def search_and_get_policy(self, env, actions, temp=1.0):
        pi = env.current_player()

        # Dynamische Sim-Zahl je nach Aktionsanzahl
        sim_count = self._selfplay_sim_count(len(actions))

        # Root-Knoten mit untried_actions=None initialisieren, damit _expand
        # beim ersten Besuch die reward-basierte Sortierung (beste Züge zuerst)
        # durchführt. Wenn hier mit vorbefüllten untried_actions gearbeitet wird,
        # überspringt _expand die Initialisierung komplett → alle Aktionen landen
        # ungefiltert im Baum, die Reward-Sortierung greift nie.
        root = MCTSNode(
            action=None,
            parent=None,
            untried_actions=None,
            player_who_acted=pi
        )
        root.visits = 1

        # Alle Simulationen durchführen
        for _ in range(sim_count):
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)

        if not root.children:
            action = random.choice(actions)
            return action, [{"action": action, "prob": 1.0}]

        if temp == 0.0:
            best = max(root.children, key=lambda c: c.visits)
            policy = [{"action": c.action, "prob": 1.0 if c is best else 0.0}
                      for c in root.children]
            policy = [p for p in policy if p["prob"] > 0.0]
            return best.action, policy

        # Cache leeren — Priors gelten nur für diesen Zug
        if hasattr(self, 'node_priors'):
            self.node_priors.clear()
        elif hasattr(self, '_az') and hasattr(self._az, 'node_priors'):
            self._az.node_priors.clear()

        # Temperature-gewichtete Policy: visits^(1/temp), zusätzlich mit dem
        # Q-Wert (Exploitation) gewichtet.
        #
        # Hintergrund: Die Suche nutzt UCB1 mit c=1.414 (volle Exploration für
        # Spielstärke). Dadurch sind die reinen Besuchszahlen im Frühspiel sehr
        # flach (viele Optionen werden explorativ etwa gleich oft besucht),
        # selbst wenn die Q-Werte klar zwischen guten und schlechten Drafts
        # unterscheiden. Würde das Target nur aus Besuchen gebildet, lernte das
        # Netz diese flache (uninformative) Verteilung — und flutete im Frühspiel.
        #
        # Lösung: Das Target zusätzlich mit dem Q-Wert gewichten. So fließt die
        # diskriminierende Information aus den Q-Werten ins Lernsignal, OHNE die
        # Suche selbst gieriger zu machen (c bleibt unverändert, Spielstärke
        # bleibt erhalten). Q wird auf [0,1] genutzt (Win-Prob aus dem Rollout)
        # und mild verschärft, damit gute Züge klar mehr Gewicht bekommen.
        total_visits = sum(c.visits for c in root.children)
        if total_visits == 0:
            action = random.choice(actions)
            return action, [{"action": action, "prob": 1.0}]

        def _q_weight(c):
            q = (c.value / c.visits) if c.visits else 0.0
            # q liegt ~[0,1] (Win-Prob aus Sicht des ziehenden Spielers).
            # Mild verschärfen: q^2 hebt gute Züge an, ohne schlechte ganz
            # auszulöschen (Exploration im Target bleibt erhalten).
            return max(q, 1e-6) ** 2

        raw = [(c, (c.visits ** (1.0 / temp)) * _q_weight(c)) for c in root.children]
        total_raw = sum(r for _, r in raw)
        if total_raw <= 0:
            # Fallback: reine Besuche, falls Q-Gewichte degenerieren
            raw = [(c, c.visits ** (1.0 / temp)) for c in root.children]
            total_raw = sum(r for _, r in raw)
        policy = [{"action": c.action, "prob": r / total_raw} for c, r in raw]

        chosen_action = random.choices(
            [p["action"] for p in policy],
            weights=[p["prob"] for p in policy]
        )[0]

        return chosen_action, policy


class MCTSSelfPlayAgent(SelfPlayMixin, HeuristicMCTSAgent):
    """MCTS-basierter Self-Play Agent (kein neuronales Netz)."""
    def __init__(self, simulations=50, rollout_depth=5, max_actions=10, **kwargs):
        super().__init__(simulations=simulations, rollout_depth=rollout_depth,
                         max_actions=max_actions, **kwargs)


class NetworkSelfPlayAgent(SelfPlayMixin):
    """AlphaZero-basierter Self-Play Agent (mit trainiertem Netz)."""
    def __init__(self, model_version: str, simulations=40, **kwargs):
        from agents.alphazero import AlphaZeroAgent
        # Wir erben nicht von AlphaZeroAgent sondern wrappen ihn
        # damit SelfPlayMixin._sample_actions etc. verfügbar sind
        self._az = AlphaZeroAgent(
            model_version=model_version,
            input_size=INPUT_SIZE,
            simulations=simulations,
            **kwargs
        )
        # Delegiere alle MCTS-Methoden an den AlphaZero-Agent
        self.simulations = simulations
        self._select = self._az._select
        self._expand = self._az._expand
        self._rollout = self._az._rollout
        self._backpropagate = self._az._backpropagate
        self._sample_actions = self._az._sample_actions

    def set_env(self, env):
        self._az.set_env(env)


# ---------------------------------------------------------------------------
# Spiel-Loop
# ---------------------------------------------------------------------------

def play_one_game(agent, margin_cap: int = 15, max_winner_score: int = 40, game_id: str = "unknown"):
    """Spielt ein Spiel und gibt Trainingsdaten zurück."""
    env = MosaicEnv()
    obs, info = env.reset()

    if hasattr(agent, 'set_env'):
        agent.set_env(env)

    history = []
    steps = 0

    while True:
        actions = env.valid_actions()
        if not actions:
            break

        current_player = env.current_player()

        # Aktionsbasierte Temperatur (statt zugbasiert):
        # Mosaic ist rundenbasiert — in JEDER Runde gibt es früh viele offene
        # Optionen (Fundament legen, auf das man später hinspielt) und spät
        # wenige, zielgerichtete Züge. Die Temperatur sollte daher an der Zahl
        # der verfügbaren Aktionen hängen, nicht an der Gesamtzugzahl:
        #   - VIELE Aktionen  → höhere Temperatur: die frühen Fundament-
        #     Entscheidungen der Runde explorieren (mehrere Wege sind sinnvoll).
        #   - WENIGE Aktionen → niedrige Temperatur: späte, scharfe Züge gezielt
        #     auf das aufgebaute Fundament zuspitzen.
        n_actions = len(actions)
        if n_actions > 50:
            temp = 0.7
        elif n_actions > 15:
            temp = 0.4
        else:
            temp = 0.15

        # Startkuppel-Platzierung: nur MILDE Temperature. Genug Variation, damit
        # das Netz verschiedene (auch suboptimale) Starts sieht und lernt sie
        # zu kompensieren — aber nicht so viel, dass durchweg schlechte Starts
        # entstehen, die das Lernsignal verrauschen.
        if env.state.phase == "start_placement":
            temp = 0.3

        if len(actions) == 1:
            action = actions[0]
            policy = [{"action": action, "prob": 1.0}]
        else:
            action, policy = agent.search_and_get_policy(env, actions, temp=temp)

        # Moon-Order Target: nur für kleine Manufakturen (f_idx 0-3)
        moon_order_target = None
        f_idx_check = action.get("factory_index", 5)
        if action.get("type") == "stone" and f_idx_check <= 3:
            from itertools import permutations as _perms
            import random as _rand
            from agents.mcts import evaluate_state as _eval
            state_now = env.state
            factories = state_now.factories
            f_idx = f_idx_check
            color = action.get("color", "")
            if f_idx < len(factories):
                remaining = [t for t in factories[f_idx].sun_tiles
                             if (t.value if hasattr(t,"value") else str(t)) != color]
                if remaining:
                    perms = list(_perms(remaining))
                    if len(perms) > 6:
                        perms = _rand.sample(perms, 6)
                    best_score = -float("inf")
                    best_order = None
                    from engine.moves import Move, TakeAction, PlaceAction, TakeSource
                    for perm in perms:
                        import copy as _copy
                        test_game = _copy.deepcopy(env._game)
                        try:
                            color_obj = next(
                                (t for t in factories[f_idx].sun_tiles
                                 if (t.value if hasattr(t,"value") else str(t)) == color), None)
                            if color_obj is None: continue
                            f_id = factories[f_idx].factory_id
                            move = Move(
                                take=TakeAction(source=TakeSource.SMALL_FACTORY_SUN,
                                               color=color_obj, factory_id=f_id,
                                               moon_order=list(perm)),
                                place=PlaceAction(row_index=action.get("row", -1)),
                            )
                            test_game.apply(move)
                            score = _eval(test_game.state).get(current_player, 0.0)
                            if score > best_score:
                                best_score = score
                                best_order = perm
                        except Exception:
                            continue
                    if best_order is not None:
                        moon_order_target = [
                            t.value if hasattr(t,"value") else str(t)
                            for t in best_order
                        ]

        history.append({
            "state":              copy.deepcopy(obs),
            "player":             current_player,
            "policy":             policy,
            "valid_actions":      actions,
            "moon_order_target":  moon_order_target,
        })

        obs, reward, done, step_info = env.step(action)
        steps += 1

        if done:
            break

    scores = env.scores()
    winner = (
        0 if scores[0] > scores[1] else
        1 if scores[1] > scores[0] else
        0 if env.state.players[0].holds_first_player_marker else 1
    )

    training_data = []
    for step in history:
        training_data.append({
            "game_id":          game_id,
            "state":             step["state"],
            "policy":            step["policy"],
            "valid_actions":     step["valid_actions"],
            "moon_order_target": step.get("moon_order_target"),
            # Rohe Spielergebnis-Daten — value wird im Dataset on-the-fly berechnet
            "scores":            list(scores),
            "winner":            winner,
            "player":            step["player"],
        })

    # win_val nur für Konsolenausgabe
    margin       = abs(scores[0] - scores[1])
    winner_score = scores[winner]
    if margin == 0 and winner_score < 5:
        win_val = 0.1
    else:
        margin_part = min(0.45, (margin / margin_cap) * 0.45)
        score_part  = min(0.45, (winner_score / max_winner_score) * 0.45)
        win_val     = min(1.0, 0.1 + margin_part + score_part)

    return training_data, winner, scores, steps, win_val


# ---------------------------------------------------------------------------
# Datengenerierung
# ---------------------------------------------------------------------------

def generate_data(mode: str, num_games: int, simulations: int, version_name: str, rollout_depth: int = 0, tag: str = None, margin_cap: int = 15, max_winner_score: int = 40):
    """
    Generiert Self-Play Trainingsdaten.

    mode:         'mcts' oder 'network'
    num_games:    Anzahl zu spielender Partien
    simulations:  MCTS-Simulationen pro Zug (Basis; play-Modus skaliert im
                  Frühspiel auf bis zu 3× für schärfere Policy-Targets)
    version_name: Versionsname für Dateinamen und Modell-Laden
    """
    if mode == "mcts":
        print(f"🚀 Starte MCTS Self-Play: {num_games} Spiele (Sims: {simulations}"
              f" | depth={rollout_depth} | play)")
        agent = MCTSSelfPlayAgent(simulations=simulations, rollout_depth=rollout_depth)
    elif mode == "network":
        model_file = MODELS_DIR / f"alphazero_{version_name}.pth"
        if not model_file.exists():
            print(f"❌ Modell nicht gefunden: {model_file}")
            return
        print(f"🚀 Starte Network Self-Play: {num_games} Spiele "
              f"(Sims: {simulations} | Model: {model_file.name} | play)")
        agent = NetworkSelfPlayAgent(model_version=version_name, simulations=simulations)
    else:
        print(f"❌ Unbekannter Modus: {mode}. Verwende 'mcts' oder 'network'.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_training_data = []
    t_start = time.time()
    
    # Einmaliger Run-Prefix für diese gesamte Ausführung
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i in range(num_games):
        t0 = time.time()
        print(f"Spiele Partie {i+1}/{num_games}... ", end="", flush=True)

        # Eindeutige ID für dieses spezifische Spiel generieren
        file_tag = f"_{tag}" if tag else ""
        current_game_id = f"{version_name}{file_tag}_{run_timestamp}_g{i+1}"

        game_data, winner, scores, steps, win_val = play_one_game(agent, margin_cap=margin_cap, max_winner_score=max_winner_score, game_id=current_game_id)
        all_training_data.extend(game_data)
        duration = time.time() - t0

        print(f"Fertig in {duration:.1f}s | "              f"Scores: {scores[0]}:{scores[1]} | "              f"Züge: {steps}")

        if (i + 1) % 10 == 0 or (i + 1) == num_games:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            file_tag = f"_{tag}" if tag else ""
            filename = DATA_DIR / f"selfplay_{version_name}{file_tag}_{timestamp}_g{i+1}.pkl"
            with open(filename, "wb") as f:
                pickle.dump(all_training_data, f)
            print(f"💾 {len(all_training_data)} Züge gespeichert in '{filename}'")
            all_training_data = []

    print(f"\n✅ Fertig nach {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mosaic-AI Self-Play Datengenerierung")
    parser.add_argument("--mode",    type=str, required=True,
                        choices=["mcts", "network"],
                        help="'mcts' für MCTS-only, 'network' für AlphaZero-Netz")
    parser.add_argument("--games",   type=int, default=100,
                        help="Anzahl Spiele")
    parser.add_argument("--sims",    type=int, default=100,
                        help="MCTS-Simulationen pro Zug (Basis; play-Modus skaliert "
                             "im Frühspiel auf bis zu 3×)")
    parser.add_argument("--version", type=str, required=True,
                        help="Versionsname, z.B. v0 oder v1")
    parser.add_argument("--tag",      type=str, default=None,
                        help="Optionaler Tag für parallele Läufe (z.B. 'a', 'b')")
    parser.add_argument("--margin_cap",       type=int, default=15,
                        help="Margin ab dem win_val=1.0 (Standard: 15)")
    parser.add_argument("--max_winner_score", type=int, default=40,
                        help="Normalisierung Winner-Score Komponente (Standard: 40)")
    parser.add_argument("--depth",   type=int, default=None,
                        help="Rollout-Tiefe (0=Heuristik, 1=1 Schritt, 5=5 Schritte)")
    parser.add_argument("--terminals", type=int, default=1,
                        help="Anzahl paralleler Terminals (teilt --games auf, vergibt Tags a/b/c...)")
    args = parser.parse_args()

    if args.mode == 'mcts' and args.depth is None:
        parser.error("--depth ist bei --mode mcts erforderlich")
    rollout_depth = args.depth if args.depth is not None else 0

    # --- Parallele Terminals ---
    if args.terminals > 1:
        import subprocess, sys, os, string
        n = args.terminals
        base = args.games // n
        rest = args.games % n
        tags = list(string.ascii_lowercase)
        print(f"🚀 Starte {n} parallele Terminals "
              f"(je ~{base} Spiele, Tags {tags[0]}–{tags[n-1]})")
        procs = []
        for i in range(n):
            games_i = base + (1 if i < rest else 0)
            if games_i == 0:
                continue
            tag_i = (args.tag or "") + tags[i]
            cmd = [
                sys.executable, os.path.abspath(__file__),
                "--mode", args.mode,
                "--games", str(games_i),
                "--sims", str(args.sims),
                "--version", args.version,
                "--tag", tag_i,
                "--margin_cap", str(args.margin_cap),
                "--max_winner_score", str(args.max_winner_score),
            ]
            if args.depth is not None:
                cmd += ["--depth", str(args.depth)]
            if os.name == "nt":
                CREATE_NEW_CONSOLE = 0x00000010
                p = subprocess.Popen(cmd, creationflags=CREATE_NEW_CONSOLE)
            else:
                logf = open(f"selfplay_terminal_{tag_i}.log", "w")
                p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)
            procs.append((tag_i, games_i, p))
            print(f"   ↳ Terminal {i+1}: Tag '{tag_i}', {games_i} Spiele (PID {p.pid})")
        print(f"\n✅ Alle {len(procs)} Terminals gestartet. Warte auf Abschluss...")
        for tag_i, games_i, p in procs:
            p.wait()
            print(f"   ✓ Terminal Tag '{tag_i}' fertig ({games_i} Spiele)")
        print("🎉 Alle Terminals abgeschlossen.")
        sys.exit(0)

    generate_data(
        mode=args.mode,
        num_games=args.games,
        simulations=args.sims,
        version_name=args.version,
        tag=args.tag,
        rollout_depth=rollout_depth,
        margin_cap=args.margin_cap,
        max_winner_score=args.max_winner_score,
    )