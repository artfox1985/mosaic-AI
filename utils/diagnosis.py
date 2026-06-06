# diagnose.py — for sanity check of training data

# zero-mask rows — sollte 0 sein
# policy leak — sollte < 1e-6 sein
# p_loss first batch — sollte ln(410) ~6 sein

import sys, torch, glob, pickle
sys.path.insert(0, '.')
from agents.neural_net import MosaicDataset, MosaicNet
from config import DATA_DIR, INPUT_SIZE, NUM_ACTIONS
import torch.nn.functional as F
from torch.utils.data import DataLoader

dataset = MosaicDataset(str(DATA_DIR))
print(f'Steps: {len(dataset)}, input_size={dataset.input_size}')

loader = DataLoader(dataset, batch_size=32, shuffle=False)
states, targets_p, targets_v, masks = next(iter(loader))

print(f'mask zeros per row: min={masks.sum(1).min():.0f} max={masks.sum(1).max():.0f} mean={masks.sum(1).mean():.1f}')
print(f'zero-mask rows: {(masks.sum(1)==0).sum().item()}')
print(f'policy leak: {(targets_p*(1-masks)).sum(1).max().item():.6f}')

model = MosaicNet(input_size=INPUT_SIZE, num_actions=NUM_ACTIONS)
pred_p, _ = model(states)
masked_logits = pred_p + (masks - 1) * 1e9
log_probs = F.log_softmax(masked_logits, dim=1)
p_loss = -torch.sum(targets_p * log_probs) / states.size(0)
print(f'p_loss first batch: {p_loss.item():.4f}')
print(f'nan: {torch.isnan(log_probs).any().item()}  inf: {torch.isinf(log_probs).any().item()}')