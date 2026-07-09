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
import glob
import random
import copy
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

def run_readiness_probe(version_name, games=50, sims=200, threads=0, seed=12345):
    """Stage-2-Reifegrad-Test (siehe evaluations/STAGE2_TODO.md, Abschnitt A):
    dasselbe frisch trainierte Netz tritt DIREKT gegeneinander an — Stufe 1
    (DFS-Blatt) vs. Stufe 2 (Netz-Value-Blatt), max. `games` Partien, mit
    Early-Stop (siehe arena.py::early_stop_wins_needed). Ersetzt den alten
    0:0-Raten-Vergleich aus zwei GETRENNTEN Self-Play-Läufen: der maß nur
    "kollabiert Stufe 2 nicht mehr in Nichtangriffs-Partien", nicht "gewinnt
    Stufe 2 tatsächlich" — v2b hatte dort ein grünes 1.45x-Verhältnis, verlor
    aber 2:98 in einer echten Stufe-1-vs-Stufe-2-Partie. Diese direkte Arena
    ist aussagekräftiger UND (dank Early-Stop) meist schneller als die alten
    2×100 Self-Play-Spiele."""
    onnx_path = MODELS_DIR / f"alphazero_{version_name}.onnx"
    if not onnx_path.exists():
        print(f"  ⚠️  Stufen-Vergleich übersprungen: {onnx_path.name} nicht gefunden.")
        return
    try:
        from arena import run_net_vs_net
    except ImportError as e:
        print(f"  ⚠️  Stufen-Vergleich übersprungen (arena.py nicht importierbar): {e}")
        return

    print(f"\n{'='*55}")
    print(f"  STUFE 1 vs. STUFE 2 (max. {games} Spiele, {sims} Sims, Early-Stop)")
    print(f"{'─'*55}")
    model = str(onnx_path)
    run_net_vs_net(model, model, sims_a=sims, sims_b=sims, stage_a=1, stage_b=2,
                   games=games, threads=threads, seed=seed,
                   name_a=f"{version_name}(Stufe1)", name_b=f"{version_name}(Stufe2)")
    print(f"{'='*55}")


def train(version_name, load_version=None, input_epoch=None, hidden_size=None, early_stop=True,
          probe_games=100, probe_sims=400, skip_probe=False, show_plot=True, val_frac=0.1,
          val_overfit_patience=8):
    # 1. Daten laden (Nutzt jetzt dynamisch den DATA_DIR Pfad)
    # Val-Split auf DATEI-Ebene (nicht Zug-Ebene!): Zuege derselben Partie sind
    # stark korreliert, ein Zug-Split wuerde nahezu identische Zustaende in
    # Training UND Validierung streuen und ein zu gutes Val-R² vortaeuschen.
    # Bewusst PRO TRAININGSLAUF neu gezogen (kein ueber Generationen fixer
    # Val-Satz) -- das Val-R² soll nur beantworten "ueberfittet DIESES Modell
    # auf sein eigenes aktuelles Fenster", nicht als generationsuebergreifendes
    # Benchmark dienen (das leistet schon die Arena vs. Champion/Heuristik).
    all_files = sorted(glob.glob(str(DATA_DIR / "*.pkl")))
    val_files = []
    train_files = None  # None == MosaicDataset laedt wie bisher den ganzen Ordner
    if val_frac > 0 and len(all_files) >= 10:
        shuffled = all_files[:]
        random.Random(20260707).shuffle(shuffled)
        n_val = max(1, round(len(shuffled) * val_frac))
        val_files = sorted(shuffled[:n_val])
        train_files = sorted(shuffled[n_val:])

    dataset = MosaicDataset(str(DATA_DIR), files=train_files)
    if len(dataset) == 0:
        print(f"❌ Fehler: Keine Daten im Ordner '{DATA_DIR}' gefunden!")
        return

    val_dataset = None
    if val_files:
        val_dataset = MosaicDataset(str(DATA_DIR), files=val_files)
        print(f"   Val-Split: {len(train_files)} Trainings-Dateien / {len(val_files)} Val-Dateien "
              f"({len(dataset):,} / {len(val_dataset):,} Züge)")

    # drop_last=True: ohne das kann die letzte Batch einer Epoche zufällig auf
    # Größe 1 fallen (Datensatzgröße mod BATCH_SIZE == 1) — BatchNorm im Netz
    # verlangt >1 Sample pro Kanal im Training und crasht sonst hart.
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    val_dataloader = (DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
                      if val_dataset is not None else None)

    # Ziel-Varianz einmalig vorab bestimmen: die rohe Value-MSE ist wegen der
    # tanh(.../VALUE_SCALE)-Stauchung auf absoluter Skala kaum aussagekräftig
    # (aktuell std≈0.19 — das ist aber kein Spielziel-Merkmal, im Gegenteil:
    # Ziel ist eine MÖGLICHST GROSSE Punktedifferenz, u.a. durch gezieltes
    # Stören des Gegners. Die geringe Streuung spiegelt nur den aktuellen,
    # noch schwachen Spielstand von Heuristik/frühen Netz-Generationen wider,
    # nicht eine inhärente Eigenschaft des Spiels) und ändert sich über
    # Epochen hinweg sichtbar zu wenig, um Fortschritt zu erkennen (weder im
    # Log noch im Plot). Ein R² = 1 − MSE/Var(Ziel) (Varianzaufklärung ggü.
    # der trivialen Mittelwert-Baseline) ist skalenunabhängig und bewegt sich
    # sichtbar zwischen 0 (nicht besser als Mittelwert-Vorhersage) und 1
    # (perfekt) — unabhängig davon, ob die Ziel-Streuung mit stärkerem Spiel
    # künftig noch wächst.
    target_var = dataset.values.var().item()
    target_std = target_var ** 0.5
    print(f"   Value-Ziel-Streuung: σ={target_std:.3f} (Varianz={target_var:.4f}, "
          f"zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)")

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
    from neural_net import VALUE_SCALE, VALUE_OPP_EPSILON
    print(f"   Value-Target  : tanh(eigen/{VALUE_SCALE:.0f}) - {VALUE_OPP_EPSILON}*tanh(gegner/{VALUE_SCALE:.0f}) (Endergebnis statt Win/Loss)")
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
    value_r2_history = []
    val_r2_history  = []
    val_ploss_history = []
    plateau_window    = 5
    plateau_threshold = 0.01
    early_stop_patience = 5 if early_stop else 999999
    policy_plateau_since = None
    stopped_early = False
    stop_reason = None
    total_history = []

    # ── Val-R²-Tracking (nur fuer die Zusammenfassung/Phase 2 unten) ────────
    # Phase 1 trainiert Value+Policy bewusst GEMEINSAM ueber die volle
    # Laufzeit (kein Zwischen-Freeze mehr) -- ein frueherer Versuch, den
    # Value-Head mittendrin einzufrieren, liess ihn trotzdem kollabieren
    # (Val-R² z.B. 0.27->-0.87), weil der gemeinsame Trunk danach noch dutzende
    # Epochen rein auf Policy weitertrainierte und wegdriftete. Value bleibt
    # also aktiv (das hilft dem Trunk/der Policy nachweislich, siehe v1 vs.
    # v1b), auch wenn er dabei ueberfittet -- die eigentliche Kalibrierung
    # eines GENERALISTISCHEN Value-Heads passiert danach in Phase 2, auf dem
    # dann fertigen, unbeweglichen Trunk.
    best_val_r2 = float("-inf")
    best_val_epoch = None

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
            ax_bot.set_ylabel("Value R² (ggü. Mittelwert-Baseline)")
            ax_bot.set_xlabel("Epoche")
            (line_total,) = ax_top.plot([], [], label="Total", color="tab:blue")
            (line_policy,) = ax_top.plot([], [], label="Policy", color="tab:orange")
            (line_value,) = ax_bot.plot([], [], label="Value R² (Train)", color="tab:green")
            (line_val,) = ax_bot.plot([], [], label="Value R² (Val)", color="tab:red", linestyle="--")
            ax_top.legend(loc="upper right")
            ax_bot.legend(loc="upper right")
            plot = {
                "fig": fig, "ax_top": ax_top, "ax_bot": ax_bot,
                "line_total": line_total, "line_policy": line_policy, "line_value": line_value,
                "line_val": line_val,
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
            # Keine separate win_val-Stärke-Gewichtung mehr nötig — die Marge steckt
            # bereits im Value-Target selbst (siehe neural_net.py, tanh-Endergebnis-Target);
            # die Visit-Targets sind unabhängig vom Ausgang valide Policy-Ziele.
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
        epoch_r2 = 1 - epoch_vloss / target_var if target_var > 0 else 0.0
        value_r2_history.append(epoch_r2)
        total_history.append(epoch_tloss)

        # ── Validierung (Value-Head) auf dem NIE trainierten Datei-Split ────
        # Reiner Forward-Pass ohne Gradient -- kostet nur einen Bruchteil einer
        # Trainings-Epoche (val_frac der Datenmenge, kein backward()). Nutzt
        # dieselbe target_var (Trainings-Baseline) fuer einen vergleichbaren
        # Maßstab statt einer je Epoche neu berechneten Val-eigenen Varianz.
        epoch_val_r2 = None
        epoch_val_ploss = None
        if val_dataloader is not None:
            model.eval()
            val_vloss_sum, val_ploss_sum, val_batches = 0.0, 0.0, 0
            with torch.no_grad():
                for v_states, v_targets_p, v_targets_v, v_masks, _vmoon, v_pol_w in val_dataloader:
                    v_states = v_states.to(device)
                    v_targets_p = v_targets_p.to(device)
                    v_targets_v = v_targets_v.to(device)
                    v_masks = v_masks.to(device)
                    v_pol_w = v_pol_w.to(device)
                    v_pred_p, v_pred_v, _ = model(v_states)
                    val_vloss_sum += mse_loss(v_pred_v, v_targets_v).item()
                    # Gleiche Masking/Gewichtung wie im Training (siehe oben) --
                    # sonst waere der Val-Policy-Loss nicht vergleichbar.
                    v_masked_logits = v_pred_p + (v_masks - 1) * 1e9
                    v_log_probs = F.log_softmax(v_masked_logits, dim=1)
                    v_per_sample_ce = -torch.sum(v_targets_p * v_log_probs, dim=1)
                    v_p_loss = (v_per_sample_ce * v_pol_w).sum() / v_pol_w.sum().clamp(min=1e-6)
                    val_ploss_sum += v_p_loss.item()
                    val_batches += 1
            model.train()
            epoch_val_vloss = val_vloss_sum / max(val_batches, 1)
            epoch_val_r2 = 1 - epoch_val_vloss / target_var if target_var > 0 else 0.0
            epoch_val_ploss = val_ploss_sum / max(val_batches, 1)
        val_r2_history.append(epoch_val_r2)
        val_ploss_history.append(epoch_val_ploss)

        # Nur zur Beobachtung/Zusammenfassung: ab wann startet der Val-R²-
        # Verfall? (Kein Trigger mehr -- Value trainiert bewusst bis zum Ende
        # von Phase 1 mit, siehe Kommentar oben.)
        if epoch_val_r2 is not None and epoch_val_r2 > best_val_r2 + 0.005:
            best_val_r2 = epoch_val_r2
            best_val_epoch = epoch + 1

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
                plateau_marker = "  🟡 POLICY-PLATEAU"

        # Value plateaut separat prüfen (gleiche Fenster-Logik) — seit dem
        # Punkte-Marge-Target (VALUE_SCHEMA_VERSION, deutlich geringere
        # Zielstreuung als das alte ±1-Ziel) konvergiert Value oft langsamer
        # als Policy. Früher wurde NUR auf Policy-Plateau early-gestoppt, was
        # den Value-Head mitten in der Konvergenz abschneiden konnte.
        value_plateaued = False
        if len(value_history) >= plateau_window * 2:
            v_recent   = sum(value_history[-plateau_window:]) / plateau_window
            v_previous = sum(value_history[-plateau_window*2:-plateau_window]) / plateau_window
            v_rel = (v_previous - v_recent) / v_previous if v_previous > 0 else 0
            if v_rel < plateau_threshold:
                value_plateaued = True

        if policy_plateaued and value_plateaued:
            if policy_plateau_since is None:
                policy_plateau_since = epoch + 1
            plateau_marker = "  🟡 PLATEAU (Policy+Value)"
        elif policy_plateaued and len(value_history) >= 3:
            v3 = value_history[-3:]
            if v3[0] > v3[1] > v3[2]:
                plateau_marker = "  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)"

        # ── Live-Plot aktualisieren (zusätzlich zur Textzeile unten) ────────
        if plot is not None:
            try:
                xs = list(range(1, len(total_history) + 1))
                plot["line_total"].set_data(xs, total_history)
                plot["line_policy"].set_data(xs, policy_history)
                plot["line_value"].set_data(xs, value_r2_history)
                if val_dataloader is not None:
                    plot["line_val"].set_data(xs, val_r2_history)
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

        val_str = f" | Val-R²={epoch_val_r2:+.2f}" if epoch_val_r2 is not None else ""
        val_p_str = f" | Policy-Val={epoch_val_ploss:5.2f}" if epoch_val_ploss is not None else ""
        print(f"Epoche {epoch+1:2d}/{epochs} | Total Loss: {t_loss/n_batches:6.2f} "
              f"(R²={epoch_r2:+.2f}, Policy: {epoch_ploss:5.2f}){val_str}{val_p_str} "
              f"| v_pred μ={v_mean:+.2f} σ={v_std:.3f}{plateau_marker}")

        # ── Early Stopping (nur bei Policy+Value-Plateau) ───────────────────
        if policy_plateau_since is not None:
            since = (epoch + 1) - policy_plateau_since
            if since >= early_stop_patience:
                print(f"\n⏹️  Early Stopping: Policy+Value plateaut seit Epoche {policy_plateau_since} "
                      f"({since} Epochen ohne Fortschritt).")
                stopped_early = True
                stop_reason = "plateau"
                break

    # ── Phase 2: Value-Kalibrierung auf dem fertigen, unbeweglichen Trunk ──
    # Trunk/Policy-Head haben sich in Phase 1 GEMEINSAM mit dem Value-Loss
    # entwickelt (das hilft der Policy ueber den geteilten Trunk, siehe v1 vs.
    # v1b), der Value-Head selbst hat dabei aber nie speziell auf den FINALEN
    # Trunk-Stand gepasst -- er ist einem sich staendig bewegenden Ziel
    # hinterhergejagt. Jetzt: Trunk/Policy/Moon einfrieren (aendern sich nicht
    # mehr), Value-Head NEU (von 0) gegen die jetzt FIXEN Trunk-Features
    # trainieren, mit dem Val-Split als Stop-Kriterium -- kann nicht mehr
    # kollabieren, weil sich der Trunk waehrend dieser Phase nicht mehr bewegt.
    calib_best_val_r2 = float("-inf")
    calib_best_epoch = None
    if val_dataloader is not None:
        print(f"\n{'='*55}")
        print(f"  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)")
        print(f"{'─'*55}")

        for p in model.body.parameters():
            p.requires_grad = False
        for p in model.policy_head.parameters():
            p.requires_grad = False
        for p in model.moon_order_head.parameters():
            p.requires_grad = False

        # Value-Head NEU initialisieren -- der Phase-1-Stand ist ein
        # Kompromiss ueber einen sich bewegenden Trunk, kein sauberer Fit auf
        # den jetzt finalen, fixen Trunk.
        fresh = MosaicNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS, hidden_size=hs)
        model.value_head.load_state_dict(fresh.value_head.state_dict())
        model.value_head.to(device)

        calib_optimizer = optim.Adam(model.value_head.parameters(), lr=LEARNING_RATE)
        calib_patience = val_overfit_patience
        calib_tolerance = 0.005
        calib_max_epochs = 50
        calib_best_state = None

        for calib_epoch in range(calib_max_epochs):
            model.train()
            for states, _tp, targets_v, _m, _mo, _pw in dataloader:
                states = states.to(device)
                targets_v = targets_v.to(device)
                with torch.no_grad():
                    shared = model.body(states)
                pred_v = model.value_head(shared)
                v_loss = mse_loss(pred_v, targets_v)
                calib_optimizer.zero_grad()
                v_loss.backward()
                calib_optimizer.step()

            model.eval()
            val_vloss_sum, val_batches = 0.0, 0
            with torch.no_grad():
                for v_states, _vp, v_targets_v, _vm, _vmoon, _vpw in val_dataloader:
                    v_states = v_states.to(device)
                    v_targets_v = v_targets_v.to(device)
                    shared = model.body(v_states)
                    pred_v = model.value_head(shared)
                    val_vloss_sum += mse_loss(pred_v, v_targets_v).item()
                    val_batches += 1
            model.train()
            calib_val_r2 = 1 - (val_vloss_sum / max(val_batches, 1)) / target_var if target_var > 0 else 0.0

            if calib_val_r2 > calib_best_val_r2 + calib_tolerance:
                calib_best_val_r2 = calib_val_r2
                calib_best_epoch = calib_epoch + 1
                calib_best_state = copy.deepcopy(model.value_head.state_dict())

            print(f"  Kalibrierung {calib_epoch+1:2d}/{calib_max_epochs} | Val-R²={calib_val_r2:+.3f}"
                  + (f"  (bislang bester: Epoche {calib_best_epoch})" if calib_best_epoch else ""))

            if calib_best_epoch is not None and (calib_epoch + 1) - calib_best_epoch >= calib_patience:
                print(f"  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche {calib_best_epoch} "
                      f"nicht mehr verbessert (Bestwert {calib_best_val_r2:.3f}).")
                break

        if calib_best_state is not None:
            model.value_head.load_state_dict(calib_best_state)
            print(f"  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt "
                  f"(Epoche {calib_best_epoch}, Val-R²={calib_best_val_r2:.3f}).")
        print(f"{'='*55}")

        for p in model.parameters():
            p.requires_grad = True
    else:
        print("  ⚠️  Value-Kalibrierung übersprungen (kein Val-Split verfügbar).")

    max_loss = math.log(NUM_ACTIONS)
    final_p = epoch_ploss  # Policy-Head aendert sich in Phase 2 nicht

    # final_v: nach Phase 2 (falls gelaufen) den TATSAECHLICH gespeicherten
    # Value-Head-Stand neu ausmessen (auf den Trainingsdaten), nicht den
    # Phase-1-Zwischenstand vor der Kalibrierung.
    if val_dataloader is not None and calib_best_epoch is not None:
        model.eval()
        tloss_sum, tbatches = 0.0, 0
        with torch.no_grad():
            for states, _tp, targets_v, _m, _mo, _pw in dataloader:
                states = states.to(device)
                targets_v = targets_v.to(device)
                shared = model.body(states)
                pred_v = model.value_head(shared)
                tloss_sum += mse_loss(pred_v, targets_v).item()
                tbatches += 1
        model.train()
        final_v = tloss_sum / max(tbatches, 1)
    else:
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

    # R² statt absoluter MSE-Schwellen: die Value-MSE allein ist wegen der
    # tanh-Stauchung der Zielskala (siehe target_var oben) nicht
    # generationsübergreifend vergleichbar — R² = 1 - MSE/Var(Ziel) schon.
    final_r2 = 1 - final_v / target_var if target_var > 0 else 0.0
    if final_r2 > 0.97:
        v_quality = "⚠️  Overfitting-Verdacht"
    elif final_r2 > 0.7:
        v_quality = "🟢 Sehr gut"
    elif final_r2 > 0.4:
        v_quality = "🟡 Gut"
    elif final_r2 > 0.15:
        v_quality = "🟠 Schwaches Signal"
    else:
        v_quality = "🔴 Nichts gelernt"

    # Val-R² (auf nie trainierten Dateien) -- die eigentliche Antwort auf die
    # Overfitting-Frage, die final_r2 (Trainingsdaten selbst) nicht geben kann.
    # Nach Phase 2 der Kalibrierungs-Bestwert (kollabiert nicht mehr, da der
    # Trunk dabei fix war); ohne Val-Split/Kalibrierung der letzte Phase-1-Wert.
    if val_dataloader is not None and calib_best_epoch is not None:
        final_val_r2 = calib_best_val_r2
    else:
        final_val_r2 = None
        for v in reversed(val_r2_history):
            if v is not None:
                final_val_r2 = v
                break
    val_gap = (final_r2 - final_val_r2) if final_val_r2 is not None else None

    print(f"\n{'='*55}")
    print(f"  TRAINING SUMMARY")
    print(f"{'='*55}")
    print(f"  Epochen:       {epochs}")
    print(f"  Züge:          {len(dataset):,}"
          + (f"  (+{len(val_dataset):,} Val, nie trainiert)" if val_dataset is not None else ""))
    print(f"  Batches/Epoche:{n_batches}")
    print(f"{'─'*55}")
    print(f"  Policy Loss:   {final_p:.4f} / {max_loss:.2f} max  ({pct:.1f}%)  {quality}")
    final_val_ploss = None
    for v in reversed(val_ploss_history):
        if v is not None:
            final_val_ploss = v
            break
    if final_val_ploss is not None:
        policy_val_gap = final_val_ploss - final_p
        print(f"  Policy Val-Loss: {final_val_ploss:.4f}  (Gap ggü. Train: {policy_val_gap:+.4f})")
    print(f"  Value Loss:    {final_v:.4f}  (R²={final_r2:.2f} ggü. Mittelwert-Baseline)  {v_quality}")
    if final_val_r2 is not None:
        if val_gap > 0.3:
            gap_marker = "⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich"
        elif val_gap > 0.15:
            gap_marker = "🟡 spürbarer Train/Val-Abstand — im Auge behalten"
        else:
            gap_marker = "🟢 Train/Val nah beieinander"
        print(f"  Value Val-R²:  {final_val_r2:.2f}  (Gap ggü. Train: {val_gap:+.2f})  {gap_marker}")
    print(f"{'─'*55}")
    if best_val_epoch is not None:
        print(f"  ℹ️  Phase 1 Val-R² war in Epoche {best_val_epoch} am besten ({best_val_r2:.2f}), "
              f"danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).")
    if calib_best_epoch is not None:
        print(f"  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche {calib_best_epoch}, "
              f"Val-R²={calib_best_val_r2:.2f} — Wert oben spiegelt diesen kalibrierten Value-Head wider.")
    if stopped_early:
        print(f"  ⏹️  Early Stopping (Policy+Value-Plateau) nach Epoche {len(policy_history)}/{epochs}")
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
        "stop_reason":       stop_reason,
        "early_stop_epoch":  policy_plateau_since if stopped_early else None,
        "best_val_r2":       round(best_val_r2, 4) if best_val_r2 > float("-inf") else None,
        "calib_best_epoch":  calib_best_epoch,
        "calib_best_val_r2": round(calib_best_val_r2, 4) if calib_best_epoch is not None else None,
        "num_games":         len(dataset),  # Züge
        "input_size":        dataset.input_size,
        "num_actions":       NUM_ACTIONS,
        "hidden_size":       hs,
        "batch_size":        BATCH_SIZE,
        "lr":                LEARNING_RATE,
        "value_weight":      VALUE_WEIGHT,
        "final_policy_loss": round(final_p, 4),
        "final_value_loss":  round(final_v, 4),
        "final_value_r2":    round(final_r2, 4),
        "final_val_r2":      round(final_val_r2, 4) if final_val_r2 is not None else None,
        "final_policy_val_loss": round(final_val_ploss, 4) if final_val_ploss is not None else None,
        "val_frac":          val_frac,
        "num_val_games":     len(val_dataset) if val_dataset is not None else 0,
        "value_target_var":  round(target_var, 4),
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
    parser.add_argument("--probe-games", type=int, default=50,
                        help="Max. Spiele für den direkten Stufe-1-vs-Stufe-2-Vergleich, "
                             "mit Early-Stop meist weniger (Standard: 50)")
    parser.add_argument("--probe-sims", type=int, default=200,
                        help="Sims/Zug für den Stufenvergleich (Standard: 200)")
    parser.add_argument("--skip-probe", action="store_true",
                        help="Stufe-1-vs-Stufe-2-Vergleich nach dem Training überspringen")
    parser.add_argument("--no-plot", action="store_true",
                        help="Live-Loss-Plot deaktivieren (z.B. ohne Display)")
    parser.add_argument("--val-frac", type=float, default=0.1,
                        help="Anteil der Spiele-DATEIEN (nicht Züge), der als Val-Split nie "
                             "trainiert wird (Standard: 0.1). 0 deaktiviert den Split.")
    parser.add_argument("--val-patience", type=int, default=8,
                        help="Epochen ohne Val-R²-Verbesserung in Phase 2 (Value-Kalibrierung), "
                             "bevor diese abgebrochen wird und der Value-Head auf den besten "
                             "Kalibrierungs-Stand zurückgesetzt wird (Standard: 8). Phase 1 "
                             "(Policy+Value gemeinsam) ist davon unberuehrt und stoppt nur ueber "
                             "das Policy+Value-Plateau-Kriterium.")

    args = parser.parse_args()

    train(version_name=args.name, load_version=args.load, input_epoch=args.epochs,
          hidden_size=args.hidden, early_stop=not args.no_early_stop,
          probe_games=args.probe_games, probe_sims=args.probe_sims, skip_probe=args.skip_probe,
          show_plot=not args.no_plot, val_frac=args.val_frac, val_overfit_patience=args.val_patience)