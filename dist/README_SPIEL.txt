=========================================================
  Mosaic-AI — Spielanleitung (Programm)
=========================================================

STARTEN
-------
1. Diesen Ordner an einen beliebigen Ort entpacken (falls noch nicht geschehen).
2. Datei "Mosaic-AI.exe" doppelklicken.
3. Ein Konsolenfenster öffnet sich kurz und zeigt an, unter welcher Adresse
   das Spiel läuft (normalerweise http://127.0.0.1:5000). Der Standard-
   Browser öffnet sich danach automatisch mit dem Spiel.
4. Falls sich kein Browser öffnet: die im Konsolenfenster angezeigte
   Adresse von Hand in einen Browser eingeben (Chrome, Edge, Firefox, ...).

BEENDEN
-------
Einfach das Konsolenfenster schließen, oder darin Strg+C drücken.

WINDOWS-SMARTSCREEN-HINWEIS
----------------------------
Windows kennt dieses Programm nicht und zeigt beim ersten Start evtl. eine
blaue Warnung ("Windows hat den Computer geschützt" / SmartScreen). Das ist
normal bei kleinen, nicht kommerziell signierten Programmen. Auf
"Weitere Informationen" klicken und dann "Trotzdem ausführen" wählen.

SPIEL-LOG TEILEN
-----------------
Jede Partie erzeugt automatisch eine Log-Datei im Ordner
"_internal\static\log" (neben der EXE). Diese Datei lässt sich auch direkt
im Spiel über den Button "📄 Log" (oben in der Kopfleiste) herunterladen.
Wer eine Partie zur Analyse zurückschicken möchte: einfach die Datei
game_<datum>_<zeit>_seed<...>.log aus diesem Ordner (oder über den
Log-Button heruntergeladen) anhängen — sie kann direkt mit
tools/analyze_game_log.py im Projekt ausgewertet werden.

SPIELREGELN
-----------
Die vollständige Spielanleitung liegt als "engine_manual.md" in diesem
Ordner (einfach mit einem Texteditor oder Markdown-Viewer öffnen). Sie
richtet sich in erster Linie an Spieler und beschreibt alle Regeln;
sollten dort auch technische Abschnitte auftauchen, können diese
gefahrlos übersprungen werden.

SCHWIERIGKEITSGRADE
--------------------
- Leicht:  einfache Heuristik-KI (kein neuronales Netz nötig)
- Mittel/Schwer/Experte: neuronales Netz "v16_best" mit steigender
  Bedenkzeit (mehr Suchsimulationen je Zug)

LEHRER-MODUS
------------
Beim Start einer Partie "Gegen KI spielen" gibt es zusätzlich eine
Lehrer-Stufe zu wählen:
- Aus:               keine Hilfe (Standard).
- Kandidaten:        ein "💡 Tipp"-Button in der Kopfleiste markiert auf
                     Wunsch die besten Zugmöglichkeiten auf dem Brett,
                     ohne Zahlen zu verraten.
- + Bewertungen:     dieselbe Markierung, zusätzlich mit geschätzter
                     Gewinnwahrscheinlichkeit je Kandidat.
- + Coach-Feedback:  nach jedem eigenen Zug zeigt ein kurzer Hinweis, wie
                     gut er im Vergleich zum besten Zug war; am Spielende
                     gibt es eine Bilanz (Durchschnittsabweichung, Trefferquote,
                     größte Ausreißer).
Der Lehrer-Modus nutzt dieselbe KI-Analyse wie die Gegner-KI und braucht
daher ebenfalls kurz Bedenkzeit (typisch 1-3 Sekunden je Tipp/Feedback).
Ist die KI auf "Leicht" (Heuristik, kein neuronales Netz), fällt der Lehrer
auf eine gröbere Heuristik-Schätzung zurück — ein Hinweis dazu erscheint
dann im Tipp-Fenster.

BEKANNTE EINSCHRÄNKUNGEN
-------------------------
- Der Port 5000 wird bevorzugt; ist er belegt, sucht das Programm
  automatisch einen freien Port und zeigt ihn im Konsolenfenster an.
- Es handelt sich um einen lokalen Entwicklungsserver (Flask) für den
  Hausgebrauch, nicht für den Betrieb über das Internet gedacht.
