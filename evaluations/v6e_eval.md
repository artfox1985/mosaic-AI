trainiert mit

- --games 2000 --mode network --version v1b --sims 400 --stage 1
- --games 2000 --mode network --version v1c --sims 400 --stage 1
- --games 2000 --mode network --version v4 --sims 400 --stage 1
- --games 2000 --mode network --version v4b --sims 400 --stage 1
- -- load v4

512 neuronen pro hidden layer

Value weight 15

learning rate 0.001

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v6e --epochs 100 --load v4
📦 Lade HDF5-Cache (800 Dateien)...
Datensatz geladen: 1210259 Züge. (Features pro Zug: 684) — 15.9s
 Value-Ziel-Streuung: σ=0.185 (Varianz=0.0342, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️ Hyperparameter (config.py):
 Learning Rate : 0.001
 Value Weight : 15
 Batch Size : 256
 Value-Target : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v4.pth
 ⚠️ Shape-Mismatch, startet frisch: policy_head.0.weight, policy_head.0.bias
 Epochen : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche 1/100 | Total Loss: 3.16 (R²=+0.34, Policy: 2.82) | v_pred μ=+0.10 σ=0.109
Epoche 2/100 | Total Loss: 2.96 (R²=+0.39, Policy: 2.65) | v_pred μ=+0.10 σ=0.118
Epoche 3/100 | Total Loss: 2.87 (R²=+0.44, Policy: 2.58) | v_pred μ=+0.10 σ=0.124
Epoche 4/100 | Total Loss: 2.79 (R²=+0.47, Policy: 2.52) | v_pred μ=+0.10 σ=0.129
```

Nach Epoche 4 liegt die Policy im Vergleich zu V6d (2.43) deutlich höher -> Abbruch und zurück zu LR 0.0006


