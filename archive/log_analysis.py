"""
Log-Analyse: Zählt Häufigkeit von Aktionstypen aus einem Arena/Self-Play Text-Log.
"""
import sys, re
from pathlib import Path
from collections import Counter, defaultdict

def analyze_text_log(text: str):
    lines = text.splitlines()

    counts   = Counter()
    per_round = defaultdict(Counter)
    cur_round = 0

    last_was_stack = False
    for line in lines:
        # Aktuelle Runde
        m = re.match(r'\[R(\d+)\]', line)
        if m:
            cur_round = int(m.group(1))

        # Kuppelplatten — Startplatte
        if re.search(r'Startkachel \d+ → \(\d+,\d+\)', line):
            counts['Kuppel Startplatte'] += 1
            per_round[cur_round]['Kuppel Startplatte'] += 1

        # Kuppelplatten — vom Stapel gezogen (📦 Zeile)
        elif re.search(r'📦.*?vom Stapel gezogen', line):
            counts['Kuppel vom Stapel'] += 1
            per_round[cur_round]['Kuppel vom Stapel'] += 1
            last_was_stack = True

        # Kuppelplatten — gelegt (Kachel X → Slot)
        # Stapel-Platten werden hier NICHT nochmal gezählt (bereits als Stapel erfasst)
        elif re.search(r'Kachel \d+ → Slot \(\d+,\d+\)', line):
            if last_was_stack:
                last_was_stack = False  # gehört zum vorherigen Stapelzug
            else:
                counts['Kuppel vom Display'] += 1
                per_round[cur_round]['Kuppel vom Display'] += 1

        # Sonnenzüge
        if re.search(r'☀️.*?→ Reihe \d+', line):
            counts['Sonnenzug → Reihe'] += 1
        if re.search(r'☀️.*?→ Strafleiste', line):
            counts['Sonnenzug → Straf'] += 1

        # Mondzüge
        if re.search(r'🌙 Spieler.*?→ Reihe \d+', line):
            counts['Mondzug → Reihe'] += 1
        if re.search(r'🌙 Spieler.*?→ Strafleiste', line):
            counts['Mondzug → Straf'] += 1

        # Strafleiste
        if re.search(r'⚠️.*?Strafleiste \(Slots', line):
            counts['Strafe (Strafleiste)'] += 1
        if re.search(r'⚠️.*?Strafleiste voll', line):
            counts['Strafleiste voll → Turm'] += 1

        # Bonusplättchen
        if re.search(r'Bonusplättchen von Fabrik', line):
            counts['Bonusplättchen genommen'] += 1
            per_round[cur_round]['Bonusplättchen genommen'] += 1

        # Tiling
        if re.search(r'🎯.*?\+\d+ Pkt', line):
            counts['Tiling (Punkte)'] += 1

        # Chip-Tiling
        if re.search(r'🎫.*?Bonus-Chips', line):
            counts['Tiling via Chips'] += 1

        # Unplatzierbar
        if re.search(r'unplatzierbar', line):
            counts['Unplatzierbar → Straf'] += 1

    # Kuppelplatten total
    total_dome = (counts['Kuppel Startplatte']
                + counts['Kuppel vom Display']
                + counts['Kuppel vom Stapel'])

    print("=== LOG ANALYSE ===")
    print(f"{'Aktion':<30} {'Anzahl':>8}")
    print("─" * 40)

    order = [
        'Kuppel Startplatte',
        'Kuppel vom Display',
        'Kuppel vom Stapel',
        'Sonnenzug → Reihe',
        'Sonnenzug → Straf',
        'Mondzug → Reihe',
        'Mondzug → Straf',
        'Strafe (Strafleiste)',
        'Strafleiste voll → Turm',
        'Bonusplättchen genommen',
        'Tiling (Punkte)',
        'Tiling via Chips',
        'Unplatzierbar → Straf',
    ]
    for name in order:
        print(f"{name:<30} {counts[name]:>8}")

    print("─" * 40)
    print(f"{'Kuppelplatten TOTAL':<30} {total_dome:>8}  (erwartet: 2×9=18 bei 2 Spielern)")
    print(f"{'Bonusplättchen TOTAL':<30} {counts['Bonusplättchen genommen']:>8}  (erwartet: 20)")

    print()
    print("=== PRO RUNDE ===")
    print(f"{'Runde':<6} {'Kuppel Display':>15} {'Kuppel Stapel':>14} {'Bonus':>6} {'Tiling':>7}")
    print("─" * 50)
    for r in sorted(per_round.keys()):
        c = per_round[r]
        print(f"R{r:<5} {c['Kuppel vom Display']:>15} "
              f"{c['Kuppel vom Stapel']:>14} "
              f"{c['Bonusplättchen genommen']:>6} "
              f"{counts.get('Tiling (Punkte)', 0):>7}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        print("Log-Text eingeben (Strg+Z/Strg+D zum Beenden):")
        text = sys.stdin.read()
    analyze_text_log(text)