# train.py
import argparse
import torch
import math
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader

# Unsere dynamischen Pfade aus der Config laden
from config import MODELS_DIR, DATA_DIR, NUM_ACTIONS, BATCH_SIZE, LEARNING_RATE, VALUE_WEIGHT

# WICHTIG: Wir importieren das Dataset UND das Netz aus unserer neuen Datei
from agents.neural_net import MosaicNet, MosaicDataset

def train(version_name, load_version=None, input_epoch=15):
    # 1. Daten laden (Nutzt jetzt dynamisch den DATA_DIR Pfad)
    dataset = MosaicDataset(str(DATA_DIR))
    if len(dataset) == 0:
        print(f"❌ Fehler: Keine Daten im Ordner '{DATA_DIR}' gefunden!")
        return
        
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # 2. Hardware Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🚀 Starte PyTorch Training auf: {device.type.upper()}")
    
    # 3. Modell Setup
    model = MosaicNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS)
    
    # Warm Start?
    if load_version:
        load_path = MODELS_DIR / f"alphazero_{load_version}.pth"
        
        if load_path.exists():
            print(f"📥 Lade altes Model als Startpunkt: {load_path.name}")
            ckpt = torch.load(str(load_path), map_location=device)
            model.load_state_dict(ckpt["model_state"])
        else:
            print(f"⚠️ Warnung: Start-Modell '{load_path}' nicht gefunden. Trainiere von null!")
            
    model.to(device)
    
    # 4. Training Parameter
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    mse_loss = nn.MSELoss()
    
    # Epochen-Anzahl ---
    epochs = input_epoch
    if load_version:
        print(f"🔄 Warm-Start erkannt: Trainiere für {epochs} Epochen.")
    else:
        print(f"🆕 Neues Modell: Trainiere für {epochs} Epochen.")
    # --------------------------------------
    
    # 5. DIE SCHLEIFE
    n_batches = len(dataloader)
    for epoch in range(epochs):
        t_loss, t_vloss, t_ploss = 0, 0, 0
        
        for states, targets_p, targets_v, masks in dataloader:
            states    = states.to(device)
            targets_p = targets_p.to(device)
            targets_v = targets_v.to(device)
            masks     = masks.to(device)

            optimizer.zero_grad()
            pred_p, pred_v = model(states)

            # Policy Loss mit Masking:
            # Illegale Aktionen aus pred_p rausrechnen, dann renormalisieren

            masked_logits = pred_p + (masks - 1) * 1e9   # illegale Aktionen auf -inf
            log_probs = F.log_softmax(masked_logits, dim=1)
            
            v_loss = mse_loss(pred_v, targets_v)
            p_loss = -torch.sum(targets_p * log_probs) / states.size(0)

            loss = v_loss * VALUE_WEIGHT + p_loss
            loss.backward()
            optimizer.step()
            
            t_loss += loss.item()
            t_vloss += v_loss.item()
            t_ploss += p_loss.item()
            
        print(f"Epoche {epoch+1:2d}/{epochs} | Total Loss: {t_loss/n_batches:6.2f} (Value: {t_vloss/n_batches:5.2f}, Policy: {t_ploss/n_batches:5.2f})")
                   
    
    max_loss = math.log(NUM_ACTIONS)
    final_p = t_ploss / n_batches
    final_v = t_vloss / n_batches
    pct = final_p / max_loss * 100

    if pct < 8:
        quality = "⚠️  Overfitting-Verdacht"
    elif pct < 25:
        quality = "🟢 Sehr gut"
    elif pct < 40:
        quality = "🟡 Gut"
    elif pct < 70:
        quality = "🟠 Schwaches Signal"
    else:
        quality = "🔴 Nichts gelernt"

    if final_v > 0.3:
        v_quality = "🔴 Nichts gelernt"
    elif final_v > 0.1:
        v_quality = "🟠 Schwaches Signal"
    elif final_v > 0.05:
        v_quality = "🟡 Gut"
    elif final_v > 0.01:
        v_quality = "🟢 Sehr gut"
    else:
        v_quality = "⚠️  Overfitting-Verdacht"

    print(f"\n{'='*55}")
    print(f"  TRAINING SUMMARY")
    print(f"{'='*55}")
    print(f"  Epochen:       {epochs}")
    print(f"  Züge:          {len(dataset):,}")
    print(f"  Batches/Epoche:{n_batches}")
    print(f"{'─'*55}")
    print(f"  Policy Loss:   {final_p:.4f} / {max_loss:.2f} max  ({pct:.1f}%)  {quality}")
    print(f"  Value Loss:    {final_v:.4f}  {v_quality}")
    print(f"{'='*55}")
        
    # 6. Speichern
    model.cpu()
    save_path = MODELS_DIR / f"alphazero_{version_name}.pth"
    checkpoint = {
        "model_state":   model.state_dict(),
        "version":       version_name,
        "timestamp":     __import__("datetime").datetime.now().isoformat(),
        "epochs":        epochs,
        "num_games":     len(dataset),  # Züge
        "input_size":    dataset.input_size,
        "num_actions":   NUM_ACTIONS,
        "batch_size":    BATCH_SIZE,
        "lr":            LEARNING_RATE,
        "value_weight":  VALUE_WEIGHT,
        "final_policy_loss": round(final_p, 4),
        "final_value_loss":  round(final_v, 4),
        "policy_pct":    round(pct, 1),
        "load_version":  load_version,
    }
    torch.save(checkpoint, str(save_path))
    print(f"\n✅ Training beendet! Neues Model gespeichert unter:\n📂 {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Name der alten Version für Warm Start, z.B. v1")
    parser.add_argument("--epochs", type=int, default=None, help="Wieviele Epochen")
    
    args = parser.parse_args()
    
    train(version_name=args.name, load_version=args.load, input_epoch=args.epochs)