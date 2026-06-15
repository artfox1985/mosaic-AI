"""
Prüft eine Trainings-pkl: Anzahl Züge, ob das chippable-Feld vorhanden ist
UND ob es jemals befüllt ist (echtes Signal vs. nur leere Listen), plus die
Tensor-Länge die der aktuelle Code daraus erzeugt.

Aufruf aus dem Projekt-Root:
    python utils/check_pkl.py data/selfplay_xyz.pkl [weitere.pkl ...]
"""
import pickle, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def check(pkl_path):
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    name = Path(pkl_path).name
    if not data:
        print(f"  {name}: LEER")
        return

    # Über ALLE Züge prüfen: Feld vorhanden? Jemals befüllt?
    n = len(data)
    field_present = 0
    field_nonempty = 0
    tiling_states = 0
    for step in data:
        st = step.get("state", {})
        if "chippable_tiling_rows" in st:
            field_present += 1
            ctr = st.get("chippable_tiling_rows") or []
            if ctr:
                field_nonempty += 1
        if st.get("phase") == "tiling":
            tiling_states += 1

    # Tensor-Länge an einem Sample
    try:
        from agents.neural_net import state_to_tensor
        tlen = len(state_to_tensor(data[0].get("state", {})))
    except Exception as e:
        tlen = f"FEHLER: {e}"

    print(f"  {name}")
    print(f"    Züge gesamt:                 {n}")
    print(f"    Feld vorhanden:              {field_present}/{n}")
    print(f"    Feld BEFÜLLT (echtes Signal): {field_nonempty}/{n}")
    print(f"    davon Tiling-Phase-States:    {tiling_states}/{n}")
    print(f"    Tensor-Länge (akt. Code):     {tlen}")
    if field_present == n and field_nonempty > 0:
        print(f"    → ✅ Neue Daten mit echtem chippable-Signal")
    elif field_present == n:
        print(f"    → ⚠️ Feld da, aber nie befüllt (evtl. kaum Chip-Situationen)")
    elif field_present == 0:
        print(f"    → 🔴 Alte Daten (vor chippable-Feature)")
    else:
        print(f"    → ⚠️ GEMISCHT — Datei enthält alte UND neue States")


if __name__ == "__main__":
    paths = sys.argv[1:]
    if not paths:
        print("Nutzung: python utils/check_pkl.py datei1.pkl [datei2.pkl ...]")
        sys.exit(1)
    for p in paths:
        check(p)