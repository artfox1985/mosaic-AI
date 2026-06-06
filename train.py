# train.py
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader

# Unsere dynamischen Pfade aus der Config laden
from config import MODELS_DIR, DATA_DIR, NUM_ACTIONS

# WICHTIG: Wir importieren das Dataset UND das Netz aus unserer neuen Datei
from agents.neural_net import MosaicNet, MosaicDataset

def train(version_name, load_version=None):
    # 1. Daten laden (Nutzt jetzt dynamisch den DATA_DIR Pfad)
    dataset = MosaicDataset(str(DATA_DIR))
    if len(dataset) == 0:
        print(f"❌ Fehler: Keine Daten im Ordner '{DATA_DIR}' gefunden!")
        return
        
    dataloader = DataLoader(dataset, batch_size=256, shuffle=True)
    
    # 2. Hardware Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🚀 Starte PyTorch Training auf: {device.type.upper()}")
    
    # 3. Modell Setup
    model = MosaicNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS)
    
    # Warm Start?
    if load_version:
        # Baut den Pfad: models/alphazero_v1.pth
        load_path = MODELS_DIR / f"alphazero_{load_version}.pth"
        
        if load_path.exists():
            print(f"📥 Lade altes Model als Startpunkt: {load_path.name}")
            model.load_state_dict(torch.load(str(load_path), map_location=device))
        else:
            print(f"⚠️ Warnung: Start-Modell '{load_path}' nicht gefunden. Trainiere von null!")
            
    model.to(device)
    
    # 4. Training Parameter
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    mse_loss = nn.MSELoss()
    
    # --- NEU: Dynamische Epochen-Anzahl ---
    if load_version:
        epochs = 10
        print(f"🔄 Warm-Start erkannt: Trainiere für {epochs} Epochen.")
    else:
        epochs = 15
        print(f"🆕 Neues Modell: Trainiere für {epochs} Epochen.")
    # --------------------------------------
    
    # 5. DIE SCHLEIFE
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

            loss = v_loss + p_loss
            loss.backward()
            optimizer.step()
            
            t_loss += loss.item()
            t_vloss += v_loss.item()
            t_ploss += p_loss.item()
            
        print(f"Epoche {epoch+1:2d}/{epochs} | Total Loss: {t_loss:6.2f} (Value: {t_vloss:5.2f}, Policy: {t_ploss:5.2f})")
        
    # 6. Speichern
    model.cpu()
    save_path = MODELS_DIR / f"alphazero_{version_name}.pth"
    torch.save(model.state_dict(), str(save_path))
    print(f"\n✅ Training beendet! Neues Model gespeichert unter:\n📂 {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Name der alten Version für Warm Start, z.B. v1")
    args = parser.parse_args()
    
    train(version_name=args.name, load_version=args.load)