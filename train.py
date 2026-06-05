# train.py
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# WICHTIG: Wir importieren das Dataset UND das Netz aus unserer neuen Datei
from agents.neural_net import MosaicNet, MosaicDataset

def train(version_name, load_model_path=None):
    # 1. Daten laden (Nutzt jetzt die importierte Klasse)
    dataset = MosaicDataset("data")
    if len(dataset) == 0:
        print("Fehler: Keine Daten gefunden!")
        return
        
    dataloader = DataLoader(dataset, batch_size=256, shuffle=True)
    
    # 2. Hardware Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🚀 Starte PyTorch Training auf: {device.type.upper()}")
    
    # 3. Modell Setup
    model = MosaicNet(input_size=dataset.input_size, num_actions=400)
    
    # Warm Start?
    if load_model_path:
        print(f"Lade altes Gehirn als Startpunkt: {load_model_path}")
        model.load_state_dict(torch.load(load_model_path, map_location=device))
        
    model.to(device)
    
    # 4. Training Parameter
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    mse_loss = nn.MSELoss()
    epochs = 15  
    
    # 5. DIE SCHLEIFE
    for epoch in range(epochs):
        t_loss, t_vloss, t_ploss = 0, 0, 0
        
        for states, targets_p, targets_v in dataloader:
            states = states.to(device)
            targets_p = targets_p.to(device)
            targets_v = targets_v.to(device)
            
            optimizer.zero_grad()
            pred_p, pred_v = model(states)
            
            v_loss = mse_loss(pred_v, targets_v)
            p_loss = -torch.sum(targets_p * torch.log(pred_p + 1e-8)) / states.size(0)
            
            loss = v_loss + p_loss
            loss.backward()
            optimizer.step()
            
            t_loss += loss.item()
            t_vloss += v_loss.item()
            t_ploss += p_loss.item()
            
        print(f"Epoche {epoch+1:2d}/{epochs} | Total Loss: {t_loss:6.2f} (Value: {t_vloss:5.2f}, Policy: {t_ploss:5.2f})")
        
    # 6. Speichern
    model.cpu()
    save_path = f"alphazero_{version_name}.pth"
    torch.save(model.state_dict(), save_path)
    print(f"\n✅ Training beendet! Gespeichert als '{save_path}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Pfad zum alten Modell (Warm Start)")
    args = parser.parse_args()
    
    train(version_name=args.name, load_model_path=args.load)