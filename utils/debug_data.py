import os
import glob
import pickle

def debug_training_data(data_dir="data"):
    # Finde alle Pickle-Dateien im Ordner
    files = glob.glob(os.path.join(data_dir, "*.pkl"))
    if not files:
        print(f"Keine Dateien im Ordner '{data_dir}/' gefunden.")
        return

    # Wir nehmen für die Stichprobe einfach die allererste Datei
    test_file = files[0]
    print(f"🔍 Öffne Stichprobe: {test_file}\n")

    with open(test_file, "rb") as f:
        game_data = pickle.load(f)

    print(f"Anzahl der gespeicherten Züge (States) in dieser Datei: {len(game_data)}\n")

    chip_uses = 0
    dome_placements = 0
    rotations_used = {0: 0, 90: 0, 180: 0, 270: 0}

    # Wir iterieren durch jeden einzelnen gespeicherten Spielstand
    for step_idx, step in enumerate(game_data):
        
        # Die 'policy' ist eine Liste aller Züge, die der Agent in dieser
        # Situation im MCTS-Baum simuliert und bewertet hat.
        for p in step["policy"]:
            action = p["action"]
            t = action.get("type")

            # 1. Wurden Bonus-Chips in Betracht gezogen?
            if t == "bonus_chip":
                chip_uses += 1
                
            # 2. Wurden Kuppelplatten (aus Auslage oder Stapel) in Betracht gezogen?
            elif t in ["dome", "dome_stack"]:
                dome_placements += 1
                rot = action.get("rotation", 0)
                if rot in rotations_used:
                    rotations_used[rot] += 1
                else:
                    rotations_used[rot] = 1

    # --- AUSWERTUNG DRUCKEN ---
    print("📊 --- ERGEBNISSE DER DEBUG-LUPE --- 📊")
    print(f"Bonus-Chips vom Agenten bewertet: {chip_uses} mal")
    print(f"Kuppelplatten vom Agenten bewertet: {dome_placements} mal")
    print("Verteilung der Rotationen bei den Kuppelplatten:")
    for r, count in rotations_used.items():
        print(f"  - {r}° : {count} mal")

    print("\nFazit:")
    non_zero_rotations = sum(v for k, v in rotations_used.items() if k != 0)
    
    if chip_uses > 0 and non_zero_rotations > 0:
        print("✅ ALLES PERFEKT! Dein Heuristik-Agent hat die Chips und Rotationen fleißig genutzt.")
        print("   Du musst KEINE neuen Daten generieren, das Training kann sofort starten!")
    else:
        print("⚠️ ACHTUNG! Entweder wurden keine Chips genutzt oder alle Platten lagen auf 0°.")
        print("   Irgendetwas in der Agent_env.py scheint diese Züge zu blockieren.")

if __name__ == "__main__":
    debug_training_data()
