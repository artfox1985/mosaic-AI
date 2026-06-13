import torch
import torch.nn.functional as F
import math
from agents.mcts import MCTSAgent, MCTSNode
from agents.neural_net import MosaicNet, state_to_tensor, action_to_id
from engine.serializer import serialize_state
from config import MODELS_DIR, INPUT_SIZE, NUM_ACTIONS


class AlphaZeroAgent(MCTSAgent):
    """
    Der finale Meister-Agent. Nutzt MCTS (mit der AlphaZero PUCT-Formel) und
    bewertet alle Knotenpunkte blitzschnell mit dem Neuronalen Netz auf der GPU.

    Die Policy-Priors werden direkt am MCTSNode gespeichert (node.priors),
    nicht in einem globalen Cache — das vermeidet RAM-Leaks, doppelte
    Serialisierung und fragile String-Keys.
    """
    def __init__(self, model_version="v1", input_size=INPUT_SIZE, simulations=40, **kwargs):
        self.model_version = model_version
        self.input_size = input_size

        super().__init__(simulations=simulations, rollout_depth=0, **kwargs)

        model_path = MODELS_DIR / f"alphazero_{model_version}.pth"
        if not model_path.exists():
            raise FileNotFoundError(f"Das Modell '{model_path}' wurde nicht gefunden!")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🧠 AlphaZero Agent initialisiert auf: {self.device.type.upper()}")

        ckpt = torch.load(str(model_path), map_location=self.device)
        # Architektur direkt aus Gewichten lesen — 100% zuverlässig
        hs = ckpt["model_state"]["body.0.weight"].shape[0]   # z.B. 256 oder 512
        vh = ckpt["model_state"]["value_head.0.bias"].shape[0]  # z.B. 64 oder 128
        self.model = MosaicNet(input_size=input_size, num_actions=NUM_ACTIONS,
                               hidden_size=hs, value_hidden=vh)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.to(self.device)
        self.model.eval()
        print(f"   Architektur: {input_size}→{hs}→{hs}→{hs} | Value Head: {vh}")

        # Knoten der zuletzt expandiert wurde — verbindet _expand → _rollout
        self._last_expanded: MCTSNode | None = None

    def _expand(self, node: MCTSNode, env) -> MCTSNode:
        """
        Wie Basisklasse aber ohne Action-Sampling:
        Alle validen Aktionen werden in den Baum aufgenommen.
        Policy-Priors (PUCT) übernehmen die Priorisierung.
        """
        import random as _rnd
        # Lazy Init ohne Sampling — alle Aktionen
        if node.untried_actions is None:
            node.untried_actions = list(env.valid_actions())

        if not node.untried_actions:
            self._last_expanded = node
            return node

        action = node.untried_actions.pop(
            _rnd.randrange(len(node.untried_actions))
        )
        obs, _, done, _ = env.step(action)

        child = MCTSNode(
            action=action,
            parent=node,
            untried_actions=None,
            player_who_acted=env.current_player(),
        )
        node.children.append(child)
        self._last_expanded = child
        return child

    def _rollout(self, env):
        """
        Fragt das Netz nach der Gewinnwahrscheinlichkeit (Value) und speichert
        die Policy-Priors (Softmax über Logits) direkt am zuletzt expandierten Knoten.
        """
        # 1. Spiel bereits vorbei?
        if env.state.phase in ("end", "final"):
            scores = env.scores()
            if scores[0] > scores[1]:
                return {0: 1.0, 1: 0.0}
            elif scores[1] > scores[0]:
                return {0: 0.0, 1: 1.0}
            else:
                p0 = 1.0 if env.state.players[0].holds_first_player_marker else 0.0
                return {0: p0, 1: 1.0 - p0}

        # 2. Netz-Auswertung
        obs = serialize_state(env.state)
        tensor_state = state_to_tensor(obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            policy_logits, value_pred, moon_logits = self.model(tensor_state)
            self._last_moon_logits = moon_logits[0].cpu().numpy()
            # Für _apply_action in agent_env.py zugänglich machen
            if self._env is not None:
                self._env._moon_logits = self._last_moon_logits

        # Policy: Logits → Wahrscheinlichkeiten (Softmax), am Knoten speichern
        policy_probs = F.softmax(policy_logits[0], dim=0).cpu().numpy()
        if self._last_expanded is not None:
            self._last_expanded.priors = policy_probs

        # 3. Value umrechnen (Tanh-Output [-1,1] → Win-Prob [0,1])
        v = value_pred.item()
        win_prob = (v + 1.0) / 2.0

        curr_pi = env.current_player()
        if curr_pi == 0:
            return {0: win_prob, 1: 1.0 - win_prob}
        else:
            return {0: 1.0 - win_prob, 1: win_prob}

    def _select(self, node: MCTSNode, env) -> MCTSNode:
        """
        AlphaZero PUCT: Kombiniert Suchwert Q mit Netz-Prior P.
        Priors werden vom Knoten gelesen (node.priors), nicht aus globalem Cache.
        """
        c_puct = 1.5

        while node.is_fully_expanded() and node.children:
            # Priors des AKTUELLEN Knotens (für seine Kinder gültig)
            priors = node.priors

            # Summe der Prior-Wahrscheinlichkeiten aller legalen Kinder
            valid_p_sum = 0.0
            if priors is not None:
                for child in node.children:
                    valid_p_sum += priors[action_to_id(child.action)]

            best_score = -float('inf')
            best_child = None

            for child in node.children:
                q = child.value / child.visits if child.visits > 0 else 0.0

                if priors is not None:
                    p = priors[action_to_id(child.action)] / (valid_p_sum + 1e-8)
                else:
                    p = 1.0 / len(node.children)

                u = q + c_puct * p * math.sqrt(node.visits) / (1 + child.visits)

                if u > best_score:
                    best_score = u
                    best_child = child

            node = best_child
            env.step(node.action)

        return node

    def _mcts_search(self, env, actions) -> dict:
        """
        Batch-Inferenz: Alle Simulationen parallel bis Leaf, dann gebatcht
        durch das Netz. Ein Forward-Pass statt N einzelner Calls.
        """
        import time
        pi       = env.current_player()
        root     = MCTSNode(action=None, parent=None, untried_actions=None,
                            player_who_acted=pi)
        root.visits = 1
        # AlphaZero: kein Action-Sampling — Policy-Priors übernehmen die Priorisierung
        # Alle validen Aktionen in den Baum statt max_actions=20
        root.untried_actions = list(actions)

        t_start   = time.time()
        sims_done = 0
        batch_size = min(self.simulations, 16)  # Batch-Größe

        while True:
            if self.time_limit_s is not None:
                if time.time() - t_start >= self.time_limit_s:
                    break
            else:
                if sims_done >= self.simulations:
                    break

            # ── Phase 1: batch_size Simulations bis Leaf ──────────────────
            leaves = []  # (node, sim_env, done)
            for _ in range(min(batch_size, self.simulations - sims_done)):
                sim_env = env.clone()
                node    = self._select(root, sim_env)
                node    = self._expand(node, sim_env)

                # Spiel bereits beendet?
                if sim_env.state.phase in ("end", "final"):
                    scores = sim_env.scores()
                    if scores[0] > scores[1]:
                        result = {0: 1.0, 1: 0.0}
                    elif scores[1] > scores[0]:
                        result = {0: 0.0, 1: 1.0}
                    else:
                        p0 = 1.0 if sim_env.state.players[0].holds_first_player_marker else 0.0
                        result = {0: p0, 1: 1.0 - p0}
                    self._backpropagate(node, result, pi)
                    sims_done += 1
                else:
                    leaves.append((node, sim_env))

            if not leaves:
                continue

            # ── Phase 2: Batch-Inferenz ────────────────────────────────────
            tensors = []
            for _, sim_env in leaves:
                obs = serialize_state(sim_env.state)
                tensors.append(state_to_tensor(obs))

            batch = torch.stack(tensors).to(self.device)
            with torch.no_grad():
                policy_logits, value_preds, moon_logits_batch = self.model(batch)
                policy_probs_batch = F.softmax(policy_logits, dim=1).cpu().numpy()
                value_preds_np     = value_preds.cpu().numpy()
                # Moon logits für den aktuellen State (letzter im Batch)
                self._last_moon_logits = moon_logits_batch[-1].cpu().numpy()
                if self._env is not None:
                    self._env._moon_logits = self._last_moon_logits

            # ── Phase 3: Priors setzen + Backprop ─────────────────────────
            for i, (node, sim_env) in enumerate(leaves):
                # Policy-Priors am expandierten Knoten speichern
                if node.priors is None:
                    node.priors = policy_probs_batch[i]

                # Value → Win-Prob
                v        = float(value_preds_np[i].item() if hasattr(value_preds_np[i], "item") else value_preds_np[i].flat[0])
                win_prob = (v + 1.0) / 2.0
                curr     = sim_env.current_player()
                if curr == 0:
                    result = {0: win_prob, 1: 1.0 - win_prob}
                else:
                    result = {0: 1.0 - win_prob, 1: win_prob}

                self._backpropagate(node, result, pi)
                sims_done += 1

        # Beste Aktion
        if not root.children:
            return __import__('random').choice(actions)

        best = max(root.children, key=lambda n: n.visits)
        self.stats = {
            "simulations": sims_done,
            "best_visits": best.visits,
            "best_q":      best.value / best.visits if best.visits else 0,
            "tree_size":   sum(1 for _ in self._iter_nodes(root)),
        }
        return best.action

    def reset_for_new_game(self):
        """Kein globaler Cache mehr — Priors leben am Knoten. No-op für Kompatibilität."""
        self._last_expanded = None

    @torch.no_grad()
    def evaluate_raw(self, obs, actions=None):
        """
        Reine NETZ-Auswertung OHNE MCTS — für Debugging/Visualisierung.

        Returns dict:
          - value:     roher Value-Head Output [-1, 1]
          - win_prob:  (value+1)/2 → [0, 1] aus Sicht des aktuellen Spielers
          - policy_full: np.array[NUM_ACTIONS] — Softmax über alle Aktionen
          - per_action: (falls actions übergeben) Liste von
                        {action, prob, prob_renormalized} nur für gültige Aktionen,
                        absteigend nach prob sortiert.
        """
        import numpy as np
        self.model.eval()
        tensor_state = state_to_tensor(obs).unsqueeze(0).to(self.device)
        policy_logits, value_pred, moon_logits = self.model(tensor_state)
        policy_probs = F.softmax(policy_logits[0], dim=0).cpu().numpy()
        v = float(value_pred.item())

        result = {
            "value":       v,
            "win_prob":    (v + 1.0) / 2.0,
            "policy_full": policy_probs,
        }

        if actions:
            # Nur gültige Aktionen herausziehen + über diese renormalisieren
            entries = []
            valid_sum = 0.0
            for a in actions:
                aid = action_to_id(a)
                p = float(policy_probs[aid]) if 0 <= aid < len(policy_probs) else 0.0
                entries.append({"action": a, "prob": p})
                valid_sum += p
            for e in entries:
                e["prob_renormalized"] = (e["prob"] / valid_sum) if valid_sum > 1e-12 else 0.0
            entries.sort(key=lambda e: e["prob"], reverse=True)
            result["per_action"] = entries

        return result