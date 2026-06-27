# train.py
import sys
import argparse
import torch
import math
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
from torch.utils.data import DataLoader

# Unsere dynamischen Pfade aus der Config laden
from config import MODELS_DIR, DATA_DIR, NUM_ACTIONS, BATCH_SIZE, LEARNING_RATE, VALUE_WEIGHT

# Netz/Dataset (PyTorch) liegen jetzt neben der Rust-Engine in engine/py/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from neural_net import MosaicNet, MosaicDataset

def train(version_name, load_version=None, input_epoch=None, hidden_size=None, early_stop=True, zerozero_ratio=None):
    # 1. Daten laden (Nutzt jetzt dynamisch den DATA_DIR Pfad)
    dataset = MosaicDataset(str(DATA_DIR), target_zerozero_ratio=zerozero_ratio)
    if len(dataset) == 0:
        print(f"❌ Fehler: Keine Daten im Ordner '{DATA_DIR}' gefunden!")
        return
        
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # 2. Hardware Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🚀 Starte PyTorch Training auf: {device.type.upper()}")
    
    # 3. Modell Setup
    from config import HIDDEN_SIZE as DEFAULT_HIDDEN
    hs = hidden_size if hidden_size is not None else DEFAULT_HIDDEN
    print(f"🧠 Netz-Architektur: {dataset.input_size}→{hs}→{hs}→{hs}")
    print(f"⚙️  Hyperparameter (config.py):")
    print(f"   Learning Rate : {LEARNING_RATE}")
    print(f"   Value Weight  : {VALUE_WEIGHT}")
    print(f"   Batch Size    : {BATCH_SIZE}")
    print(f"   Value-Target  : ±1 (reines Ergebnis)")
    model = MosaicNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS, hidden_size=hs)
    
    # Warm Start?
    if load_version:
        load_path = MODELS_DIR / f"alphazero_{load_version}.pth"
        
        if load_path.exists():
            print(f"📥 Lade altes Model als Startpunkt: {load_path.name}")
            ckpt = torch.load(str(load_path), map_location=device)
            # strict=False: tolerant gegenüber Head-Änderungen zwischen Versionen
            # (z.B. der entfernte Floor-Head in alten Checkpoints) — unerwartete/
            # fehlende Keys werden ignoriert, der Rest startet warm.
            model.load_state_dict(ckpt["model_state"], strict=False)
        else:
            print(f"⚠️ Warnung: Start-Modell '{load_path}' nicht gefunden. Trainiere von null!")
            
    model.to(device)
    
    # 4. Training Parameter
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    mse_loss = nn.MSELoss()
    
    # Epochen-Anzahl ---
    epochs = input_epoch
    print(f"   Epochen       : {epochs}")
    if load_version:
        print(f"🔄 Warm-Start erkannt: Trainiere für {epochs} Epochen.")
    else:
        print(f"🆕 Neues Modell: Trainiere für {epochs} Epochen.")
    # --------------------------------------
    
    # 5. DIE SCHLEIFE
    n_batches = len(dataloader)
    policy_history  = []
    value_history   = []
    plateau_window    = 5
    plateau_threshold = 0.01
    early_stop_patience = 5 if early_stop else 999999
    policy_plateau_since = None
    stopped_early = False

    for epoch in range(epochs):
        t_loss, t_vloss, t_ploss = 0, 0, 0
        v_preds_epoch = [] 
        
        for states, targets_p, targets_v, masks, moon_targets, pol_w in dataloader:
            states    = states.to(device)
            targets_p = targets_p.to(device)
            targets_v = targets_v.to(device)
            masks     = masks.to(device)
            pol_w     = pol_w.to(device)

            optimizer.zero_grad()
            pred_p, pred_v, pred_moon = model(states)

            # Policy Loss mit Masking:
            # Illegale Aktionen aus pred_p rausrechnen, dann renormalisieren

            masked_logits = pred_p + (masks - 1) * 1e9   # illegale Aktionen auf -inf
            log_probs = F.log_softmax(masked_logits, dim=1)

            v_loss = mse_loss(pred_v, targets_v)

            # Policy-Loss pro Sample mit der SPIELSTÄRKE gewichten.
            # |targets_v| = win_val (0.1 für 0:0/schwach … 1.0 für stark).
            # Dadurch prägen starke Spiele die Policy stark, 0:0-Spiele werden
            # zu schwachem Hintergrundrauschen — analog zur Value-Abstufung.
            # Ohne diese Gewichtung lernt die Policy zu 51% aus 0:0-Spielen
            # (in denen beide Spieler die Strafleiste fluten) mit vollem Gewicht.
            per_sample_ce = -torch.sum(targets_p * log_probs, dim=1)   # (B,)
            # Policy-Loss NUR auf echten Drafting-Schritten (pol_w=1); Tiling/Start-
            # One-Hot-Steps (pol_w=0) macht der DFS-Solver — sie würden sonst den
            # Policy-Head mit Tiling-Aktionen fluten und die Drafting-Priors ruinieren.
            # Keine win_val-Stärke-Gewichtung mehr (Value-Target ist ±1, und die
            # Visit-Targets sind unabhängig vom Ausgang valide Policy-Ziele).
            w = pol_w
            p_loss = (per_sample_ce * w).sum() / w.sum().clamp(min=1e-6)

            # Moon-Order Loss direkt zu Policy-Loss — kein extra Hyperparameter
            moon_targets = moon_targets.to(device)
            sun_mask = (moon_targets[:, 0] >= 0)
            if sun_mask.any():
                p_loss = p_loss + mse_loss(pred_moon[sun_mask], moon_targets[sun_mask])

            loss = v_loss * VALUE_WEIGHT + p_loss
            loss.backward()
            optimizer.step()

            t_loss  += loss.item()
            t_vloss += v_loss.item()
            t_ploss += p_loss.item()
            v_preds_epoch.append(pred_v.detach().flatten().cpu())

        epoch_ploss = t_ploss / n_batches
        epoch_vloss = t_vloss / n_batches
        policy_history.append(epoch_ploss)
        value_history.append(epoch_vloss)
        
        import torch as _t
        v_all   = _t.cat(v_preds_epoch)
        v_std   = v_all.std().item()
        v_mean  = v_all.mean().item()

        # ── Plateau-Erkennung ──────────────────────────────────────────────
        plateau_marker = ""
        policy_plateaued = False
        if len(policy_history) >= plateau_window * 2:
            recent   = sum(policy_history[-plateau_window:]) / plateau_window
            previous = sum(policy_history[-plateau_window*2:-plateau_window]) / plateau_window
            rel = (previous - recent) / previous if previous > 0 else 0
            if rel < plateau_threshold:
                policy_plateaued = True
                if policy_plateau_since is None:
                    policy_plateau_since = epoch + 1
                plateau_marker = "  🟡 PLATEAU"

        # Overfitting-Verdacht: Value sinkt, Policy plateaut
        if policy_plateaued and len(value_history) >= 3:
            v3 = value_history[-3:]
            if v3[0] > v3[1] > v3[2]:
                plateau_marker = "  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)"

        print(f"Epoche {epoch+1:2d}/{epochs} | Total Loss: {t_loss/n_batches:6.2f} "
              f"(Value: {epoch_vloss:5.2f}, Policy: {epoch_ploss:5.2f}) "
              f"| v_pred μ={v_mean:+.2f} σ={v_std:.3f}{plateau_marker}")

        # ── Early Stopping ─────────────────────────────────────────────────
        if policy_plateau_since is not None:
            since = (epoch + 1) - policy_plateau_since
            if since >= early_stop_patience:
                print(f"\n⏹️  Early Stopping: Policy plateaut seit Epoche {policy_plateau_since} "
                      f"({since} Epochen ohne Fortschritt).")
                stopped_early = True
                break

    max_loss = math.log(NUM_ACTIONS)
    final_p = epoch_ploss
    final_v = epoch_vloss
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
    print(f"{'─'*55}")
    if stopped_early:
        print(f"  ⏹️  Early Stopping nach Epoche {len(policy_history)}/{epochs}")
    if policy_plateau_since:
        print(f"  🟡 Plateau ab Epoche {policy_plateau_since}.")
        print(f"     → Für nächste Generation: mehr Sims im Self-Play.")
    else:
        print(f"  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.")
    print(f"{'='*55}")

    # 5b. Netzauslastung (Dead Neurons + Effective Rank)
    try:
        sample_batch = next(iter(dataloader))[0][:512].to(device)
        if sample_batch.shape[0] >= 2:
            cap = model.analyze_capacity(sample_batch)
            print(f"\n{'='*55}")
            print(f"  NETZAUSLASTUNG (Hidden Size: {hs})")
            print(f"{'─'*55}")
            print(f"  {'Schicht':<9} {'Dead':>11} {'Aktiv-Rate':>12} {'Eff.Rank':>15}")
            print(f"  {'─'*51}")
            for ln, m in cap.items():
                dead_str = f"{m['dead']}/{m['n_neurons']} ({m['dead_ratio']*100:.0f}%)"
                rank_str = f"{m['eff_rank']:.0f}/{m['n_neurons']} ({m['rank_pct']*100:.0f}%)"
                print(f"  {ln:<9} {dead_str:>11} {m['active_rate']*100:>11.0f}% {rank_str:>15}")
            print(f"  {'─'*51}")
            avg_dead = sum(m['dead_ratio'] for m in cap.values()) / len(cap)
            avg_rank = sum(m['rank_pct'] for m in cap.values()) / len(cap)
            if avg_dead > 0.4:
                print(f"  🔴 Viele tote Neuronen ({avg_dead*100:.0f}%) — Netz unterausgelastet.")
            elif avg_rank > 0.7:
                print(f"  🟡 Hohe Auslastung (Eff.Rank {avg_rank*100:.0f}%) — bei Plateau mehr Neuronen erwägen.")
            else:
                print(f"  🟢 Gesunde Auslastung (Dead {avg_dead*100:.0f}%, Rank {avg_rank*100:.0f}%).")
            print(f"{'='*55}")
        model.train()
    except Exception as e:
        print(f"  ⚠️  Auslastungsanalyse übersprungen: {e}")

    # 6. Speichern
    model.cpu()
    save_path = MODELS_DIR / f"alphazero_{version_name}.pth"
    actual_epochs = len(policy_history)
    checkpoint = {
        "model_state":       model.state_dict(),
        "version":           version_name,
        "timestamp":         __import__("datetime").datetime.now().isoformat(),
        "epochs":            actual_epochs,
        "epochs_requested":  epochs,
        "early_stopped":     stopped_early,
        "early_stop_epoch":  policy_plateau_since if stopped_early else None,
        "num_games":         len(dataset),  # Züge
        "input_size":        dataset.input_size,
        "num_actions":       NUM_ACTIONS,
        "hidden_size":       hs,
        "batch_size":        BATCH_SIZE,
        "lr":                LEARNING_RATE,
        "value_weight":      VALUE_WEIGHT,
        "margin_cap":        margin_cap,
        "max_winner_score":  max_winner_score,
        "final_policy_loss": round(final_p, 4),
        "final_value_loss":  round(final_v, 4),
        "policy_pct":        round(pct, 1),
        "load_version":      load_version,
    }
    torch.save(checkpoint, str(save_path))
    print(f"\n✅ Training beendet! Neues Model gespeichert unter:\n📂 {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Name der alten Version für Warm Start, z.B. v1")
    parser.add_argument("--epochs", type=int, default=15, help="Wieviele Epochen")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden Layer Größe (Standard: aus config.py)")
    parser.add_argument("--zerozero_ratio", type=float, default=None,
                        help="Ziel-Anteil 0:0-Spiele (z.B. 0.45). None = keine Reduktion")
    parser.add_argument("--no-early-stop", action="store_true", help="Early Stopping deaktivieren")

    args = parser.parse_args()

    train(version_name=args.name, load_version=args.load, input_epoch=args.epochs,
          hidden_size=args.hidden, early_stop=not args.no_early_stop,
          zerozero_ratio=args.zerozero_ratio)