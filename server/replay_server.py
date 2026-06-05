import glob
import pickle
import copy
from flask import Flask, jsonify, request, send_file
from engine.scoring import ALL_SCORING_TILES

app = Flask(__name__, static_folder=".")
replay_data = []

@app.route('/')
def index():
    return send_file('static/replay.html')

@app.route('/api/scoring_tiles')
def get_scoring_tiles():
    # Wird vom Frontend für den "Aktive Ziele" Button benötigt
    tiles = [{"id": t.id, "name": t.name, "description": t.description, "emoji": t.emoji} for t in ALL_SCORING_TILES]
    return jsonify({"ok": True, "tiles": tiles})

@app.route('/api/replay/load')
def load_data():
    global replay_data
    files = glob.glob("data/*.pkl")
    if not files:
        return jsonify({"error": "Keine Trainingsdaten (.pkl) im Ordner 'data' gefunden!"}), 404
    
    # Wir laden einfach die neueste Datei aus deinem Self-Play
    test_file = files[-1] 
    print(f"Lade Replay aus Datei: {test_file}")
    
    with open(test_file, "rb") as f:
        replay_data = pickle.load(f)
        
    return jsonify({"max_steps": len(replay_data)})

@app.route('/api/replay/state')
def get_state():
    step = int(request.args.get('step', 0))
    if 0 <= step < len(replay_data):
        # Das serialisierte JSON-Dict direkt aus den Daten holen
        state_dict = copy.deepcopy(replay_data[step]["state"])
        
        # 🧠 ABSOLUTER JACKPOT: Wir injizieren die KI-Gedanken ins UI-Logbuch!
        policy = replay_data[step]["policy"]
        if policy:
            # Sortiere die Züge nach Wahrscheinlichkeit
            sorted_policy = sorted(policy, key=lambda x: x["prob"], reverse=True)
            top_moves = []
            for p in sorted_policy[:3]: # Zeige die Top 3 Züge
                t = p["action"].get("type", "")
                prob = p["prob"] * 100
                top_moves.append(f"{t} ({prob:.0f}%)")
                
            log_msg = f"🧠 MCTS KI denkt: {', '.join(top_moves)}"
            
            if "log" not in state_dict:
                state_dict["log"] = []
            state_dict["log"].append(log_msg)
            
        return jsonify({"state": state_dict})
    
    return jsonify({"error": "Ungültiger Schritt"}), 400

if __name__ == "__main__":
    print("\n🚀 Replay-Viewer gestartet!")
    print("Öffne deinen Browser unter: http://localhost:5000\n")
    app.run(port=5000)
