import torch
import torch.nn.functional as F
import math
from agents.mcts import MCTSAgent, MCTSNode
from agents.neural_net import MosaicNet, state_to_tensor, action_to_id
from engine.serializer import serialize_state
from config import MODELS_DIR, INPUT_SIZE, NUM_ACTIONS


class AlphaZeroAgent(MCTSAgent):
    """
    Netz-Agent: nutzt dieselbe Suchmaschine wie der HeuristicMCTSAgent
    (geerbt von MCTSAgent), unterscheidet sich davon NUR über die Strategie-
    Hooks:
      _uses_priors = True      → PUCT-Selection statt UCB1
      _batch_size  > 1         → Leaf-Batching mit Virtual Loss
      _evaluate_leaves(...)    → ein Batch-Forward-Pass durchs Netz statt Rollout
      _provide_priors(...)     → Policy-Priors am Knoten setzen (inkl. Wurzel)

    Damit erbt der Netz-Agent automatisch Progressive Widening, Sim-Scaling,
    Q-Tiebreaker, Wall-Limit/Hard-Cap und das Action-Ranking — statt einer
    eigenen, parallelen Suchimplementierung.
    """
    def __init__(self, model_version="v1", input_size=INPUT_SIZE, simulations=40,
                 batch_size=16, **kwargs):
        self.model_version = model_version
        self.input_size = input_size

        super().__init__(simulations=simulations, rollout_depth=0, **kwargs)

        # ── Strategie-Hooks aktivieren ───────────────────────────────────────
        self._uses_priors = True
        self._batch_size  = max(1, int(batch_size))

        model_path = MODELS_DIR / f"alphazero_{model_version}.pth"
        if not model_path.exists():
            raise FileNotFoundError(f"Das Modell '{model_path}' wurde nicht gefunden!")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🧠 AlphaZero Agent initialisiert auf: {self.device.type.upper()}")

        ckpt = torch.load(str(model_path), map_location=self.device)
        hs = ckpt["model_state"]["body.0.weight"].shape[0]
        vh = ckpt["model_state"]["value_head.0.bias"].shape[0]
        self.model = MosaicNet(input_size=input_size, num_actions=NUM_ACTIONS,
                               hidden_size=hs, value_hidden=vh)
        # strict=False: alte Modelle (vor dem Floor-Head) haben floor_head-Gewichte
        # nicht gespeichert. Der Head wird dann zufällig initialisiert — unkritisch,
        # da er bei der Inferenz (Suche) ignoriert wird.
        self.model.load_state_dict(ckpt["model_state"], strict=False)
        self.model.to(self.device)
        self.model.eval()
        print(f"   Architektur: {input_size}→{hs}→{hs}→{hs} | Value Head: {vh}")
        print(f"   Suche: PUCT (c_puct={self._c_puct}) | Batch={self._batch_size} | "
              f"max_actions={self.max_actions} | Widening aktiv")

    # ── Hilfsfunktion: ein State durchs Netz ──────────────────────────────────
    @torch.no_grad()
    def _net_forward(self, states):
        """states: Liste von serialisierten obs → (policy_probs[B,A], values[B])."""
        tensors = [state_to_tensor(s) for s in states]
        batch = torch.stack(tensors).to(self.device)
        policy_logits, value_pred, moon_logits, _floor = self.model(batch)
        policy_probs = F.softmax(policy_logits, dim=1).cpu().numpy()
        values = value_pred.cpu().numpy().reshape(-1)
        # Moon-Logits des letzten States für agent_env zugänglich machen
        self._last_moon_logits = moon_logits[-1].cpu().numpy()
        if getattr(self, "_env", None) is not None:
            self._env._moon_logits = self._last_moon_logits
        return policy_probs, values

    # ── Hook 1: Wurzel-Priors setzen ──────────────────────────────────────────
    def _provide_priors(self, node: MCTSNode, env) -> None:
        if node.priors is not None:
            return
        try:
            obs = serialize_state(env.state)
            policy_probs, _ = self._net_forward([obs])
            node.priors = policy_probs[0]
        except Exception:
            node.priors = None  # Fallback: PUCT nutzt uniform

    # ── Hook 2: Batch-Bewertung der Leaves (Value) + Priors setzen ────────────
    def _evaluate_leaves(self, leaves: list) -> list:
        """
        Ein Batch-Forward-Pass für alle Leaves. Eingabe: (node, env)-Paare.
        Setzt gleichzeitig die Policy-Priors am jeweiligen Leaf-Knoten (Value
        und Policy kommen aus demselben Pass) und gibt die Value-Ergebnisse als
        result-Dicts zurück.
        """
        obs_list = [serialize_state(env.state) for (_node, env) in leaves]
        policy_probs, values = self._net_forward(obs_list)

        results = []
        for i, (node, env) in enumerate(leaves):
            # Policy-Priors am Leaf-Knoten setzen (für dessen künftige Kinder)
            if node.priors is None:
                node.priors = policy_probs[i]
            # Value → Win-Prob aus Sicht des Spielers am Zug
            v = float(values[i])
            win_prob = (v + 1.0) / 2.0
            curr = env.current_player()
            if curr == 0:
                results.append({0: win_prob, 1: 1.0 - win_prob})
            else:
                results.append({0: 1.0 - win_prob, 1: win_prob})
        return results

    @torch.no_grad()
    def evaluate_raw(self, obs, actions=None):
        """Reine Netz-Auswertung ohne MCTS — für Debugging/Visualisierung."""
        import numpy as np
        self.model.eval()
        tensor_state = state_to_tensor(obs).unsqueeze(0).to(self.device)
        policy_logits, value_pred, moon_logits, _floor = self.model(tensor_state)
        policy_probs = F.softmax(policy_logits[0], dim=0).cpu().numpy()
        v = float(value_pred.item())
        result = {
            "value":       v,
            "win_prob":    (v + 1.0) / 2.0,
            "policy_full": policy_probs,
        }
        if actions:
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

    def reset_for_new_game(self):
        pass