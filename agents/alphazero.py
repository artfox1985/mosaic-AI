import torch
import math
from agents.mcts import MCTSAgent, MCTSNode
from agents.neural_net import MosaicNet, state_to_tensor, action_to_id
from engine.serializer import serialize_state
from config import MODELS_DIR

class AlphaZeroAgent(MCTSAgent):
    """
    Der finale Meister-Agent. Nutzt MCTS (mit der AlphaZero PUCT Formel) und 
    bewertet alle Knotenpunkte blitzschnell mit dem Neuronalen Netz auf der GPU!
    """
    def __init__(self, model_version="v1", input_size=129, simulations=40, **kwargs):
        self.model_version = model_version
        self.input_size = input_size
        
        
        super().__init__(simulations=simulations, rollout_depth=0, **kwargs)

        # Dynamischer Pfad-Aufbau: models/alphazero_v1.pth
        model_path = MODELS_DIR / f"alphazero_{model_version}.pth"

        if not model_path.exists():
            raise FileNotFoundError(f"Das Modell '{model_path}' wurde nicht gefunden!")

        # --- 1. CUDA & GERÄT SETUP ---
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🧠 AlphaZero Agent initialisiert auf: {self.device.type.upper()}")

        # --- 2. DAS GEHIRN LADEN ---
        self.model = MosaicNet(input_size=input_size, num_actions=400)
        # map_location sorgt dafür, dass es keinen Crash gibt (falls Modell auf CPU gespeichert wurde)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval() 

        # Zwischenspeicher für das "halbe" Gehirn: Die Policy!
        self.node_priors = {}

    def _rollout(self, env):
        """
        Fragt das Netz nach der Gewinnwahrscheinlichkeit (Value)
        UND speichert die Zug-Wahrscheinlichkeiten (Policy) für später.
        """
        # 1. Ist das Spiel vielleicht schon komplett vorbei?
        if env.state.phase in ("end", "final"):
            scores = env.scores()
            if scores[0] > scores[1]: return {0: 1.0, 1: 0.0}
            elif scores[1] > scores[0]: return {0: 0.0, 1: 1.0}
            else:
                p0_wins = 1.0 if env.state.players[0].holds_first_player_marker else 0.0
                return {0: p0_wins, 1: 1.0 - p0_wins}

        # 2. BEREIT FÜR DAS NETZ
        obs = serialize_state(env.state)
        # --- TENSOR AUF DIE GRAFIKKARTE SCHIEBEN ---
        tensor_state = state_to_tensor(obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            # DAS GANZE GEHIRN: Policy (Welcher Zug?) und Value (Wer gewinnt?)
            policy_pred, value_pred = self.model(tensor_state)

        # --- NEU: POLICY SPEICHERN ---
        # Wir merken uns, welche Züge das Netz hier für gut hielt
        # (Wird sofort danach in der PUCT-Formel in _select genutzt)
        state_str = str(obs) 
        self.node_priors[state_str] = policy_pred[0].cpu().numpy()

        # 3. VALUE UMRECHNEN
        v = value_pred.item()
        win_prob = (v + 1.0) / 2.0

        curr_pi = env.current_player()
        if curr_pi == 0:
            return {0: win_prob, 1: 1.0 - win_prob}
        else:
            return {0: 1.0 - win_prob, 1: win_prob}

    def _select(self, node: MCTSNode, env) -> MCTSNode:
        """
        ÜBERSCHREIBT DIE NORMALE MCTS-FORMEL!
        Nutzt AlphaZero's PUCT: Kombiniert den MCTS-Suchwert (Q) mit der 
        Intuition des Neuronalen Netzes (P).
        """
        while node.is_fully_expanded() and node.children:
            c_puct = 1.5  # AlphaZero Standardwert für Exploration
            best_score = -float('inf')
            best_child = None

            # Die Intuition (Policy) für dieses Brett aus dem Speicher holen
            obs = serialize_state(env.state)
            priors = self.node_priors.get(str(obs), None)

            # Policy Normalisierung ---
            # Wir berechnen die Summe der Wahrscheinlichkeiten ALLER legalen Züge
            valid_p_sum = 0.0
            if priors is not None:
                for child in node.children:
                    valid_p_sum += priors[action_to_id(child.action)]
            # ----------------------------------          

            for child in node.children:
                # 1. Q-Value: Was hat die Simulation bisher gezeigt? (Exploitation)
                q = child.value / child.visits if child.visits > 0 else 0.0

                # 2. P-Value: Was sagt das Bauchgefühl des Netzes? (Prior)
                if priors is not None:
                    a_id = action_to_id(child.action)
                    p = priors[a_id] / valid_p_sum
                else:
                    p = 1.0 / len(node.children)

                # 3. DIE MAGISCHE ALPHAZERO PUCT-FORMEL
                u = q + c_puct * p * math.sqrt(node.visits) / (1 + child.visits)

                if u > best_score:
                    best_score = u
                    best_child = child

            node = best_child
            env.step(node.action)

        return node