#!/bin/bash
# Wartet auf das fertige v5-Modell (Poll alle 10 Minuten), startet danach
# automatisch die Arena v5 vs v2 (SPRT, 100 Spiele, Stufe 1).
set -e
cd "D:/Archiv/Documents/Projekte/mosaic-AI"

echo "$(date) Warte auf models/alphazero_v5.onnx (Check alle 10 Min)..."
while [ ! -f "models/alphazero_v5.onnx" ]; do
  sleep 600
done
echo "$(date) v5 gefunden. Starte Arena v5 vs v2..."

python -c "
from arena import run_net_vs_net
run_net_vs_net('models/alphazero_v5.onnx', 'models/alphazero_v2.onnx',
               sims_a=200, sims_b=200, stage=1, games=100, threads=0, seed=None,
               chunk=10, c_puct=1.5, name_a='v5', name_b='v2')
"
echo "$(date) FERTIG."
