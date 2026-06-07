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
        self.model = MosaicNet(input_size=input_size, num_actions=NUM_ACTIONS)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.to(self.device)
        self.model.eval()

        # Knoten der zuletzt expandiert wurde — verbindet _expand → _rollout
        self._last_expanded: MCTSNode | None = None

    def _expand(self, node: MCTSNode, env) -> MCTSNode:
        """Wie Basisklasse, merkt sich aber den neuen Knoten für _rollout."""
        child = super()._expand(node, env)
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
            policy_logits, value_pred = self.model(tensor_state)

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

    def reset_for_new_game(self):
        """Kein globaler Cache mehr — Priors leben am Knoten. No-op für Kompatibilität."""
        self._last_expanded = None