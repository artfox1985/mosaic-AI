=========================================================
  Mosaic-AI — How to Run the Game
=========================================================

Note: the game interface itself is in German for now. This file, and the
rules manual next to it, are in English.

STARTING
--------
1. Unpack this folder anywhere you like (if you haven't already).
2. Double-click "Mosaic-AI.exe".
3. A console window opens briefly and shows the address the game is running
   on (normally http://127.0.0.1:5000). Your default browser then opens
   with the game automatically.
4. If no browser opens: type the address shown in the console window into a
   browser by hand (Chrome, Edge, Firefox, ...).

QUITTING
--------
Just close the console window, or press Ctrl+C inside it.

WINDOWS SMARTSCREEN
-------------------
Windows does not know this program and may show a blue warning on first
start ("Windows protected your PC" / SmartScreen). That is normal for small
programs without a commercial code-signing certificate. Click "More info",
then "Run anyway".

SHARING A GAME LOG
------------------
Every game automatically writes a log file to the folder
"_internal\static\log" (next to the EXE). You can also download it straight
from the game via the "📄 Log" button in the top bar. If you would like to
send a game back for analysis: attach the file
game_<date>_<time>_seed<...>.log from that folder (or the one downloaded via
the Log button) — it can be evaluated directly with tools/analyze_game_log.py
in the project.

RULES
-----
The full rules are in "engine_manual.md" in this folder (open it with a text
editor or any Markdown viewer). It is written for players and describes every
rule; if you hit a technical passage, you can safely skip it.

AI STRENGTH
-----------
There are no preset difficulty levels yet — they are on the roadmap. Instead,
the "Gegen KI spielen" (play against AI) dialog exposes the two raw controls:

- "Modell-Version" (model version): which opponent plays. Leave it at the
  default for the bundled champion network, or type "heuristic" to face the
  handcrafted heuristic AI instead — clearly weaker, and it needs no network.
- "Simulationen" (simulations): how much the AI thinks per move. Default 400
  is full strength; lower numbers play faster and somewhat weaker.

Fair warning if you are looking for an easy game: turning the simulations
down does NOT give you a beginner opponent. The final round is played by an
exact solver rather than the network, so the AI's endgame stays essentially
perfect at any setting. Real difficulty levels — ones that also dial back the
endgame and let the AI make plausible human-sized mistakes — are planned but
not built yet.

TEACHER MODE
------------
When you start a game in "Gegen KI spielen" (play against the AI) mode, you
can additionally pick a teacher level:
- Off:              no help (default).
- Candidates:       a "💡 Tipp" button in the top bar highlights the best
                    moves on the board on request, without revealing numbers.
- + Evaluations:    the same highlighting, plus an estimated win probability
                    per candidate.
- + Coach feedback: after each of your moves, a short note shows how it
                    compared to the best move; at the end of the game you get
                    a summary (average deviation, hit rate, biggest misses).
Teacher mode runs the same AI analysis as the opponent AI and therefore needs
a moment to think as well (typically 1-3 seconds per hint or piece of
feedback). If the AI is set to "Easy" (heuristic, no neural network), the
teacher falls back to a coarser heuristic estimate — a note in the hint
window will tell you so.

Note: using AI hints marks the game as unrated (it no longer counts toward
your Elo rating).

KNOWN LIMITATIONS
-----------------
- Port 5000 is preferred; if it is taken, the program automatically looks for
  a free port and shows it in the console window.
- This is a local development server (Flask) for home use — it is not meant
  to be exposed to the internet.
