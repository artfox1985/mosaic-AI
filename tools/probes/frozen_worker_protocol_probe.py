# -*- coding: utf-8 -*-
"""Prueft das erweiterte Worker-Protokoll gegen einen ECHTEN Worker-Prozess.

Nicht in-process nachgestellt, sondern der Prozess, der spaeter auch laeuft --
inklusive JSON-Zeilen ueber stdin/stdout und der UTF-8-Grenze, an der
Windows' cp1252-Default schon einmal deutsche Fehlermeldungen verstuemmelt hat.

Gefahren wird gegen `v1_anchor`, und das ist Absicht: das Artefakt hat KEIN
model.onnx. Ein Worker, der ueber den Netzpfad antwortet, koennte es gar nicht
bedienen -- die Sonde belegt also zugleich den netzlosen Weg.

Geprueft:
  * alle drei Anfragearten werden beantwortet (drafting, tiling,
    start_placement)
  * eine UNBEKANNTE Art wird abgewiesen, nicht still als drafting gelesen.
    Ein Rueckfall waere ein unsichtbarer Zugwechsel -- dieselbe Fehlerklasse
    wie ein fehlendes CLI-Flag, das zum Default wird.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "py"))
import mosaic_rust as mr  # noqa: E402

ART = ROOT / "models/frozen_heuristics/v1_anchor"

proc = subprocess.Popen(
    [sys.executable, "-X", "utf8", str(ROOT / "tools/frozen_champion_worker.py"), str(ART),
     "--sims", "150", "--c-puct", "0.3"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8", bufsize=1)


def ask(req):
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("Worker weg. stderr:\n" + proc.stderr.read())
    r = json.loads(line)
    if not r.get("ok"):
        raise RuntimeError(f"Worker-Fehler: {r.get('error')}")
    return r


rg = mr.RefereeGame(("A", "B"), 0, 4242, None)
gesehen = set()
guard = 0
while len(gesehen) < 3 and guard < 500:
    guard += 1
    st = rg.advance_to_decision(None, None, [1])
    if st == "game_over":
        break
    if st == "start_placement":
        pi = rg.pending_start_placement_player()
        p = ask({"kind": "start_placement", "state": rg.state_json(),
                 "pi": pi, "game_seed": rg.game_seed()})["placement"]
        rg.start_placement_apply_external(json.dumps(p))
        if "start_placement" not in gesehen:
            print(f"  start_placement -> {json.dumps(p)}")
        gesehen.add("start_placement")
        continue
    if st == "tiling":
        s = ask({"kind": "tiling", "state": rg.state_json()})["step"]
        rg.tiling_apply_external(json.dumps(s))
        if "tiling" not in gesehen:
            print(f"  tiling          -> {json.dumps(s)}")
        gesehen.add("tiling")
        continue
    a = ask({"kind": "drafting", "state": rg.state_json(),
             "seed": rg.pending_search_seed()})["action"]
    rg.drafting_apply_external(json.dumps(a))
    if "drafting" not in gesehen:
        print(f"  drafting        -> {json.dumps(a, ensure_ascii=False)[:80]}")
    gesehen.add("drafting")

print(f"\nBeantwortete Anfragearten: {sorted(gesehen)}")

# Gegenprobe: unbekannte Art MUSS scheitern, nicht still als drafting gelten.
try:
    ask({"kind": "quatsch", "state": rg.state_json(), "seed": 1})
    print("ROT -- unbekannte Anfrageart wurde angenommen")
    ok = False
except RuntimeError as e:
    print(f"unbekannte Art abgewiesen: {str(e)[:90]}...")
    ok = True

proc.stdin.close()
proc.wait(timeout=10)
ok = ok and gesehen == {"drafting", "tiling", "start_placement"}
print("\nGRUEN" if ok else "\nROT")
sys.exit(0 if ok else 1)
