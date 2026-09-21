# shellcheck shell=bash
# tools/lib/cpu_free.sh -- "ist die Maschine frei?", EINE Bauform.
#
# CLAUDE.md ("Messungen laufen EXKLUSIV") verlangt, dass waehrend einer Arena,
# eines Self-Plays oder einer netzgestuetzten Sonde nichts anderes Rechenlast
# erzeugt -- **und ein Build zaehlt dazu**. Jede Nachtkette wartet deshalb vor
# ihrem ersten Schritt auf eine freie Maschine.
#
# ANLASS FUER DIESE SAMMELSTELLE (Durchsicht 2026-09-21, par.8h Fund 5): die
# Warteschleife stand fuenfmal im Baum, in vier verschiedenen Bauformen -- und
# EINE davon war defekt. `tools/night_v31_generate.sh` verundete
#
#     CommandLine -match '...|[c]argo|[m]aturin'   UND   Name -match 'python'
#
# Ein `cargo.exe` heisst nicht `python.exe`, also hat diese Kopie einen
# laufenden Build NIE gesehen -- an genau der Stelle, an der CLAUDE.md sagt,
# dass ein Build Messlast ist. `night_v31_chain.sh` hatte den Zusatz
# `-or Name -match '^(cargo|rustc)'` schon; die Erzeugungskette nicht.
#
# Die drei Haertungen, jede aus einem Vorfall:
#
#   1. **Der Klammer-Trick** (`[s]elf_play`) verhindert, dass die Suche die
#      eigene PowerShell-Kommandozeile findet. Ohne ihn wartet die Kette auf
#      sich selbst -- dreimal passiert, zuletzt, weil ein Heredoc den Start in
#      die Kommandozeile des Wrappers legte.
#   2. **Cargo/rustc/maturin werden am PROZESSNAMEN erkannt**, nicht an der
#      Kommandozeile und nie verundet mit `python`. Das ist der Fund oben.
#   3. **Eine leere oder unlesbare Antwort gilt als BELEGT.** Lieber einmal
#      zu lange warten als einen Messlauf in fremde Last legen.
#
# Nutzung:
#     . "$(dirname "$0")/lib/cpu_free.sh"
#     wait_for_free_cpu "v32-Kette"                 # Standardmuster
#     wait_for_free_cpu "Arena" 180                 # Deckel: 180 Ticks
#     BUSY_PATTERN='[t]rain\.py' wait_for_free_cpu "nur Training"
#
# Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.

# Vereinigung der Muster aller fuenf Aufrufer. Der Klammer-Trick steht in
# JEDEM Alternativ-Zweig, sonst greift er fuer die uebrigen nicht.
: "${BUSY_PATTERN:=[s]elf_play\.py|[t]rain\.py|[p]aired_gating|[p]aired_arena|[f]rozen_referee|[b]uild_cache|[w]indow_train_split|[o]ffline_diagnosis|[d]ead_unit_probe|[a]rgmax_profile}"
# Sekunden zwischen zwei Blicken.
: "${CPU_POLL_SECONDS:=60}"

# Zahl der belegenden Prozesse; 999 heisst "keine lesbare Antwort" (= belegt).
cpu_busy_count() {
  local pattern="${1:-$BUSY_PATTERN}" out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '$pattern' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc|maturin)' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in
      ''|*[!0-9]*) sleep 5 ;;
      *) echo "$out"; return 0 ;;
    esac
  done
  echo 999
}

cpu_is_free() {
  [ "$(cpu_busy_count "$@")" = "0" ]
}

# wait_for_free_cpu <Beschriftung> [Deckel in Ticks] [Muster]
# Rueckgabe 0 = frei, 65 = Deckel erreicht (der Aufrufer entscheidet, ob das
# ein Abbruch ist -- eine Kette bricht ab, ein Bericht darf weiterlaufen).
wait_for_free_cpu() {
  local label="${1:-Lauf}" cap="${2:-0}" pattern="${3:-$BUSY_PATTERN}" tick=0 n
  echo "########## $label WARTET auf eine freie Maschine $(date +%F' '%H:%M:%S)"
  while :; do
    n=$(cpu_busy_count "$pattern")
    [ "$n" = "0" ] && { echo "   Maschine frei ($(date +%H:%M:%S))"; return 0; }
    tick=$((tick + 1))
    if [ "$cap" -gt 0 ] && [ "$tick" -gt "$cap" ]; then
      echo "STOPP: $label hat $cap Ticks ohne freie Maschine gewartet"
      return 65
    fi
    [ $((tick % 5)) -eq 1 ] && echo "   belegt: $n Prozess(e) ($(date +%H:%M:%S))"
    sleep "$CPU_POLL_SECONDS"
  done
}
