# train.py
import sys
import argparse

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import torch
import math
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
from torch.utils.data import DataLoader


def plackett_luce_moon_loss(pred_moon, moon_targets):
    """Negative Log-Likelihood der DFS-Referenz-Reihenfolge unter einem
    Plackett-Luce-Modell über die 5 rohen Moon-Head-Scores (sequenzieller
    Softmax über die jeweils noch nicht platzierten, ursprünglich vorhandenen
    Farben — Rust-Pendant: net_mcts.rs::plackett_luce_prob, hier differenzierbar
    fürs Training). `moon_targets`: je Farbe der Rang (0=zuerst…4=zuletzt) oder
    -1 (Farbe nicht in der Restmenge dieses Samples). Gibt (B,) NLL zurück —
    Zeilen ohne jede gültige Farbe (kein Sonnenzug) liefern 0.
    Nutzt -1e9 statt -inf als Masken-Wert: nach der Max-Subtraktion in
    log_softmax bleibt eine vollständig maskierte Zeile ein wohldefiniertes
    Gleichverteilungs-Softmax (kein NaN), unabhängig davon ob ihr Beitrag
    später über `has_rank_t` verworfen wird."""
    present = moon_targets >= 0                      # (B,5) bool
    placed = torch.zeros_like(present)
    total_nll = torch.zeros(moon_targets.shape[0], device=moon_targets.device)
    for t in range(5):
        is_rank_t = present & (moon_targets == t)     # (B,5): genau 1 True je Zeile, falls Rang t existiert
        has_rank_t = is_rank_t.any(dim=1)
        avail = present & (~placed)
        masked_logits = pred_moon.masked_fill(~avail, -1e9)
        log_probs = F.log_softmax(masked_logits, dim=1)
        step_nll = -(log_probs * is_rank_t.float()).sum(dim=1)
        total_nll = total_nll + torch.where(has_rank_t, step_nll, torch.zeros_like(step_nll))
        placed = placed | is_rank_t
    return total_nll

# Unsere dynamischen Pfade aus der Config laden
from config import MODELS_DIR, DATA_DIR, NUM_ACTIONS, BATCH_SIZE, LEARNING_RATE, VALUE_WEIGHT

# Netz/Dataset (PyTorch) liegen jetzt neben der Rust-Engine in engine/py/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from neural_net import MosaicNet, MosaicDataset

def run_readiness_probe(version_name, games=40, sims=400, threads=0, seed=12345):
    """Stage-2-Reifegrad-Sonde (siehe evaluations/STAGE2_TODO.md, Abschnitt A):
    vergleicht die 0:0-Rate DESSELBEN frisch exportierten Netzes einmal mit
    DFS-Blatt (Stufe 1) und einmal mit Netz-Value-Blatt (Stufe 2), isoliert per
    kurzem Self-Play (kein Regen-Zyklus — keine pkl-Dateien, nur In-Memory-
    Auswertung). Dient als Netz-Gesundheitscheck bei JEDER Generation — auch
    nach einem Umstieg auf Stufe 2, als Sanity-Check gegen einen erneuten
    Kollaps (wie beim ersten v7-Stufe-2-Versuch: 51.8% vs. 17.5% 0:0).
    Ampel: Verhältnis 0:0(Stufe2)/0:0(Stufe1) — ≤1.5x grün, 1.5–3x gelb, >3x rot."""
    import json
    import statistics as st

    onnx_path = MODELS_DIR / f"alphazero_{version_name}.onnx"
    if not onnx_path.exists():
        print(f"  ⚠️  Sonde übersprungen: {onnx_path.name} nicht gefunden.")
        return
    try:
        import mosaic_rust as _mr
    except ImportError as e:
        print(f"  ⚠️  Sonde übersprungen (mosaic_rust nicht importierbar): {e}")
        return

    def zero_zero_stats(raw):
        # net_self_play_games liefert eine FLACHE Liste von Zug-Records (jeder
        # Schritt trägt scores/winner des fertigen Spiels) — pro game_id
        # deduplizieren, sonst gewichten längere Spiele die Rate fälschlich stärker.
        steps = json.loads(raw)
        games = {}
        for s in steps:
            gid = s.get("game_id")
            if gid is not None and "scores" in s:
                games[gid] = tuple(s["scores"])
        n = len(games)
        zz = sum(1 for sc in games.values() if sc[0] == 0 and sc[1] == 0)
        ws = st.mean(max(sc) for sc in games.values()) if n > 0 else 0.0
        return zz, n, ws

    print(f"\n{'='*55}")
    print(f"  STAGE-2-REIFEGRAD-SONDE ({games} Spiele je Stufe, {sims} Sims)")
    print(f"{'─'*55}")
    raw_s1 = _mr.net_self_play_games(model_path=str(onnx_path), n_games=games, base_sims=sims,
                                     seed=seed, num_threads=threads, dfs_leaf=True,
                                     prefix=f"{version_name}_probe_s1")
    zz1, n1, ws1 = zero_zero_stats(raw_s1)
    raw_s2 = _mr.net_self_play_games(model_path=str(onnx_path), n_games=games, base_sims=sims,
                                     seed=seed, num_threads=threads, dfs_leaf=False,
                                     prefix=f"{version_name}_probe_s2")
    zz2, n2, ws2 = zero_zero_stats(raw_s2)

    if n1 == 0 or n2 == 0:
        print(f"  ⚠️  Sonde ergebnislos: Stufe 1 lieferte {n1}, Stufe 2 {n2} Spiele "
              f"(erwartet {games} je Stufe) — Self-Play evtl. abgebrochen.")
        print(f"{'='*55}")
        return

    rate1 = zz1 / n1
    rate2 = zz2 / n2
    # Laplace-Glättung (+1 auf beide Zähler/Nenner) statt Sonderfall-Verzweigung:
    # bleibt auch bei 0 beobachteten 0:0-Spielen (in beiden oder einer Stufe)
    # wohldefiniert und dämpft Ausreißer durch kleine Stichproben (z.B. 1 vs.
    # 3 Vorkommen bei wenigen Spielen), statt sofort auf ∞/1.0 zu springen.
    ratio = (zz2 + 1) / (n2 + 1) / ((zz1 + 1) / (n1 + 1))

    if ratio <= 1.5:
        ampel = "🟢 GRÜN — Value-Head trägt, voller Stufe-2-Zyklus lohnt sich"
    elif ratio <= 3.0:
        ampel = "🟡 GELB — noch nicht reif, Trend über Generationen beobachten"
    else:
        ampel = "🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben"

    print(f"  Stufe 1 (DFS-Blatt):   0:0 {rate1*100:5.1f}% ({zz1}/{n1}) | Ø Sieger-Score {ws1:5.1f}")
    print(f"  Stufe 2 (Netz-Value):  0:0 {rate2*100:5.1f}% ({zz2}/{n2}) | Ø Sieger-Score {ws2:5.1f}")
    print(f"  Verhältnis 0:0(Stufe2/Stufe1, geglättet): {ratio:.2f}x")
    print(f"  {ampel}")
    print(f"{'='*55}")


def train(version_name, load_version=None, input_epoch=None, hidden_size=None, early_stop=True,
          probe_games=40, probe_sims=400, skip_probe=False, show_plot=True):
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
            old_state = ckpt["model_state"]
            new_state = model.state_dict()
            # strict=False allein reicht NICHT bei INPUT_SIZE-Änderungen: es
            # toleriert fehlende/zusätzliche Keys, aber KEINE Shape-Mismatches
            # bei gleichnamigen Keys (z.B. body.0.weight bei geändertem
            # INPUT_SIZE) — das würde crashen. Shape-inkompatible Keys daher
            # vorher explizit rausfiltern; der Rest (tiefere Body-Schichten,
            # alle Heads) startet weiterhin warm.
            skipped = [k for k in old_state if k in new_state and old_state[k].shape != new_state[k].shape]
            if skipped:
                print(f"   ⚠️  Shape-Mismatch, startet frisch: {', '.join(skipped)}")
                old_state = {k: v for k, v in old_state.items() if k not in skipped}
            model.load_state_dict(old_state, strict=False)
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
    total_history = []

    # ── Live-Plot (zusätzlich zur Textausgabe): Total/Policy oben, Value unten.
    # Getrennte Panels, weil Value-Loss (~0.05–0.5) sonst neben Policy-Loss
    # (~2–4) im Diagramm verschwindet. Bei fehlendem Display (headless) sauber
    # überspringen statt das Training abzubrechen.
    plot = None
    if show_plot:
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            plt.ion()
            fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
            fig.suptitle(f"Training {version_name}")
            ax_top.set_ylabel("Total / Policy Loss")
            ax_bot.set_ylabel("Value Loss")
            ax_bot.set_xlabel("Epoche")
            (line_total,) = ax_top.plot([], [], label="Total", color="tab:blue")
            (line_policy,) = ax_top.plot([], [], label="Policy", color="tab:orange")
            (line_value,) = ax_bot.plot([], [], label="Value", color="tab:green")
            ax_top.legend(loc="upper right")
            ax_bot.legend(loc="upper right")
            plot = {
                "fig": fig, "ax_top": ax_top, "ax_bot": ax_bot,
                "line_total": line_total, "line_policy": line_policy, "line_value": line_value,
                "plateau_line": None,
            }
        except Exception as e:
            print(f"⚠️  Live-Plot deaktiviert (kein Display?): {e}")
            plot = None

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

            per_sample_ce = -torch.sum(targets_p * log_probs, dim=1)   # (B,)
            # Policy-Loss NUR auf echten Drafting-Schritten (pol_w=1); Tiling/Start-
            # One-Hot-Steps (pol_w=0) macht der DFS-Solver — sie würden sonst den
            # Policy-Head mit Tiling-Aktionen fluten und die Drafting-Priors ruinieren.
            # Keine win_val-Stärke-Gewichtung mehr (Value-Target ist ±1, und die
            # Visit-Targets sind unabhängig vom Ausgang valide Policy-Ziele).
            w = pol_w
            p_loss = (per_sample_ce * w).sum() / w.sum().clamp(min=1e-6)

            # Moon-Order Loss direkt zu Policy-Loss — kein extra Hyperparameter.
            # Plackett-Luce-NLL statt MSE-auf-Rängen: der moon_order_head liefert
            # jetzt echte Präferenz-SCORES, die net_mcts.rs zur Suchzeit direkt als
            # P(Order)-Verteilung nutzt (statt einer bloßen Rang-Regression).
            moon_targets = moon_targets.to(device)
            # BUGFIX: sun_mask prüfte zuvor nur Spalte 0 (blau) auf >=0 — das
            # schloss gültige Sonnenzug-Samples aus, deren Restfarben blau nicht
            # enthielten (z.B. remaining=[gelb,rot]), und verzerrte den Loss
            # systematisch zugunsten blau-haltiger Samples. Jetzt: irgendeine Spalte.
            sun_mask = (moon_targets >= 0).any(dim=1)
            if sun_mask.any():
                moon_nll = plackett_luce_moon_loss(pred_moon, moon_targets)
                p_loss = p_loss + moon_nll[sun_mask].mean()

            loss = v_loss * VALUE_WEIGHT + p_loss
            loss.backward()
            optimizer.step()

            t_loss  += loss.item()
            t_vloss += v_loss.item()
            t_ploss += p_loss.item()
            v_preds_epoch.append(pred_v.detach().flatten().cpu())

        epoch_ploss = t_ploss / n_batches
        epoch_vloss = t_vloss / n_batches
        epoch_tloss = t_loss / n_batches
        policy_history.append(epoch_ploss)
        value_history.append(epoch_vloss)
        total_history.append(epoch_tloss)

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

        # ── Live-Plot aktualisieren (zusätzlich zur Textzeile unten) ────────
        if plot is not None:
            try:
                xs = list(range(1, len(total_history) + 1))
                plot["line_total"].set_data(xs, total_history)
                plot["line_policy"].set_data(xs, policy_history)
                plot["line_value"].set_data(xs, value_history)
                if policy_plateau_since is not None and plot["plateau_line"] is None:
                    plot["plateau_line"] = plot["ax_top"].axvline(
                        policy_plateau_since, color="red", linestyle="--", alpha=0.5, label="Plateau")
                    plot["ax_top"].legend(loc="upper right")
                for ax in (plot["ax_top"], plot["ax_bot"]):
                    ax.relim()
                    ax.autoscale_view()
                plot["fig"].canvas.draw()
                plot["fig"].canvas.flush_events()
                import matplotlib.pyplot as _plt
                _plt.pause(0.001)
            except Exception:
                plot = None  # Fenster evtl. geschlossen o.ä. — Rest ohne Plot weiterlaufen

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
        "final_policy_loss": round(final_p, 4),
        "final_value_loss":  round(final_v, 4),
        "policy_pct":        round(pct, 1),
        "load_version":      load_version,
    }
    torch.save(checkpoint, str(save_path))
    print(f"\n✅ Training beendet! Neues Model gespeichert unter:\n📂 {save_path}")

    if plot is not None:
        try:
            plot_path = MODELS_DIR / f"alphazero_{version_name}_loss.png"
            plot["fig"].savefig(str(plot_path))
            print(f"📈 Loss-Verlauf gespeichert unter:\n📂 {plot_path}")
        except Exception as e:
            print(f"⚠️  Loss-Plot konnte nicht gespeichert werden: {e}")

    # 7. ONNX direkt mitexportieren (Rust-Inferenz für Self-Play/Arena), damit
    #    kein manueller export_onnx.py-Schritt nötig ist.
    try:
        from export_onnx import export
        export(version_name)
    except Exception as e:
        print(f"⚠️  ONNX-Export übersprungen (manuell nachholbar: python export_onnx.py --version {version_name}): {e}")
        return

    # 8. Stage-2-Reifegrad-Sonde (Netz-Gesundheitscheck jeder Generation, s.
    #    evaluations/STAGE2_TODO.md Abschnitt A) — auch nach dem Umstieg auf
    #    Stufe 2 als laufender Sanity-Check gegen einen erneuten Kollaps.
    if not skip_probe:
        try:
            run_readiness_probe(version_name, games=probe_games, sims=probe_sims)
        except Exception as e:
            print(f"⚠️  Reifegrad-Sonde übersprungen: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Name der alten Version für Warm Start, z.B. v1")
    parser.add_argument("--epochs", type=int, default=15, help="Wieviele Epochen")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden Layer Größe (Standard: aus config.py)")
    parser.add_argument("--no-early-stop", action="store_true", help="Early Stopping deaktivieren")
    parser.add_argument("--probe-games", type=int, default=40,
                        help="Spiele je Stufe für die Stage-2-Reifegrad-Sonde (Standard: 40)")
    parser.add_argument("--probe-sims", type=int, default=400,
                        help="Sims/Zug für die Reifegrad-Sonde (Standard: 400)")
    parser.add_argument("--skip-probe", action="store_true",
                        help="Reifegrad-Sonde nach dem Training überspringen")
    parser.add_argument("--no-plot", action="store_true",
                        help="Live-Loss-Plot deaktivieren (z.B. ohne Display)")

    args = parser.parse_args()

    train(version_name=args.name, load_version=args.load, input_epoch=args.epochs,
          hidden_size=args.hidden, early_stop=not args.no_early_stop,
          probe_games=args.probe_games, probe_sims=args.probe_sims, skip_probe=args.skip_probe,
          show_plot=not args.no_plot)