"""
Log-Analyse: Zählt Häufigkeit von Aktionstypen aus Self-Play PKL-Dateien
oder direkt aus einem Text-Log.
"""
import sys
import re
from pathlib import Path
from collections import Counter

def analyze_text_log(text: str):
    """Zählt Aktionen aus einem Arena/Self-Play Text-Log."""
    patterns = {
        "Kuppel vom Stapel":  r"📦.*?vom Stapel gezogen",
        "Kuppel vom Display": r"Kachel \d+ → Slot \(\d+,\d+\)",
        "Sonnenzug":          r"☀️.*?→ Reihe \d+",
        "Sonnenzug Straf":    r"☀️.*?→ Strafleiste",
        "Mondzug → Reihe":    r"🌙.*?→ Reihe \d+",
        "Mondzug → Straf":    r"🌙.*?→ Strafleiste",
        "Strafleiste voll":   r"⚠️.*?Strafleiste voll",
        "Strafe gesamt":      r"⚠️.*?Strafleiste \(Slots",
        "Bonusplättchen":     r"Bonusplättchen von Fabrik",
        "Tiling":             r"🎯.*?\+\d+ Pkt",
    }

    counts = Counter()
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text)
        counts[name] = len(matches)

    print("=== LOG ANALYSE ===")
    print(f"{'Aktion':<25} {'Anzahl':>8}")
    print("─" * 35)
    for name, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{name:<25} {count:>8}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        # Aus stdin lesen
        print("Log-Text eingeben (Strg+Z/Strg+D zum Beenden):")
        text = sys.stdin.read()
    analyze_text_log(text)
