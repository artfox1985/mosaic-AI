import os
import sys
from pathlib import Path

# Der absolute Pfad zu deinem Hauptordner (mosaic-AI).
# Im PyInstaller-Bundle (Task #96, onedir) existiert __file__ nicht als reale
# Datei auf der Platte -- dort liegen die mitgelieferten Daten (models/, static/)
# neben der EXE (sys._MEIPASS bei onedir: der "_internal"-Ordner daneben).
if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
else:
    BASE_DIR = Path(__file__).resolve().parent

# --- DYNAMISCHE PFADE ---
# MOSAIC_DATA_DIR (additiv, 2026-08-01, Korpus-Dosis-Wirkungs-Vorstudie,
# evaluations/PREREG_corpus_dose.md): optionaler Override des Korpus-Ordners
# fuer train.py/self_play.py/server.py. Default (Env-Var NICHT gesetzt) ist
# byte-identisch zum bisherigen Verhalten -- BASE_DIR/"data". Grund: train.py
# hat keine Datei-Listen-/Teilmengen-Option, die eine STRATIFIZIERTE Ziehung
# (Zusammensetzungsverhaeltnis je Versions-Praefix erhalten) unterstuetzt
# (nur `--train-file-limit`, ein reines Zaehler-Sample mit fest verdrahtetem
# Seed). Statt train.py/neural_net.py anzufassen (siehe Auftragssperre),
# zeigt dieser Override testweise auf einen SEPARATEN Ordner mit HARDLINKS
# auf eine Teilmenge der echten Dateien (`tools/train_corpus_dose.py`) --
# data/ selbst wird dabei nie verschoben/umbenannt/geloescht (Memory
# `project_onedrive_file_disappearance`: data/ liegt unter OneDrive-Sync,
# Massenoperationen auf dem echten Ordner sind bewusst vermieden).
DATA_DIR = Path(os.environ.get("MOSAIC_DATA_DIR", str(BASE_DIR / "data")))
MODELS_DIR = BASE_DIR / "models"

# --- ORDNER AUTOMATISCH ERSTELLEN ---
# Verhindert "File Not Found"-Fehler, wenn jemand das Repo frisch klont oder
# die Ordner durch die .gitignore-Datei noch nicht existieren.
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- NETZWERK PARAMETER ---
INPUT_SIZE = 714        # state_to_tensor (564 Basis + 74 Endwertungs-/Geometrie + 46 Linien-Features; 60 je Spieler; +5 Beutel/Turm-Farbanteil; +18 Kuppelstapel-Maske; +1 wild_remaining_frac; +6 col_f_max des ziehenden Spielers)
                        # (redundantes unused_chip_colors-Feature entfernt: -10; bag_count ergänzt: +1;
                        #  floor-Normierung /7.0 -> /4.0 korrigiert (kein Dim-Effekt);
                        #  Bonuschip-Farbmaske je Fabrik ergänzt: +5*4=+20; 673 -> 664 -> 684;
                        #  wild_remaining_frac ergänzt (Wild-Anteil der verdeckten Kuppelstapel-Restplatten): 707 -> 708)
NUM_ACTIONS = 406       # action_to_id Ausgabebereich (405 = dome_stack_peek: Aktion A Schritt 1, parameterlos)
                        # (Baustein B, zweistufiger Kuppel-Suchknoten: 328 (Stone+Tiling)
                        #  + 27 choose_dome_slot (Kachel*Slot) + 36 choose_draw_stack_slot
                        #  (Pending*Slot) + 4 choose_dome_rotation (gemeinsam fuer beide
                        #  Pfade) + 6 use_chips + 4 bonus_chip + 1 dome_stack_peek = 406;
                        #  ersetzt die vorherige dome_slot_head/dome_rotation_head-
                        #  Prior-Faktorisierung, siehe net_mcts.rs::build_untried_actions)

# --- TRAININGSPARAMETER NN ---
BATCH_SIZE    = 256
HIDDEN_SIZE   = 512   # Neuronen pro Hidden Layer (2^x)
LEARNING_RATE = 0.0004
# Value-Head (Sieg/Niederlage) zurueckgeholt + neuer Punktestand-Aux-Head
# (siehe neural_net.py::VALUE_SCHEMA_VERSION). Beide Gewichte bewusst klein
# ggue. dem Policy-Loss (der bleibt das Trainingsziel, das die Suche/Self-Play
# tatsaechlich nutzt) -- reine Trunk-Zusatzsignale, kein Ersatz fuer Stufe 1/3.
# VALUE_WEIGHT 1.0 -> 0.2 (2026-07-17): v8-Sanity-Check zeigte massives
# Value-Head-Overfitting (Val-R²=-0.43, Train/Val-Loss-Verhaeltnis 48.6x,
# waehrend der Punktestand-Aux-Head mit demselben Trunk nur 2.7x zeigte,
# Val-R²=0.27 -- im historischen 0.2-0.3-Plateau). Early Stopping beobachtet
# nur das Policy-Plateau, nichts bremste das Value-Overfitting waehrend der
# 55 Epochen. Kleineres Gewicht soll den Trunk weniger stark aufs leicht
# auswendig lernbare ±1-Ziel ausrichten.
VALUE_WEIGHT  = 0.2
POINTS_WEIGHT = 0.5
# Ownership-Head (Task #9, 2026-07-28): dichtes Hilfsziel -- je Kuppelfeld
# (3x3 Slots x 4 Felder x 2 Spieler = 72, ego-perspektivisch wie alle uebrigen
# Features) binaer vorhersagen, ob es am SPIELENDE belegt sein wird. Motivation:
# der beste Checkpoint lag bei v15/v16/v17 stets bei Epoche 1-3, das Netz saugt
# den Korpus also fast sofort aus -- es fehlt lernbares SIGNAL pro Sample, nicht
# Sample-Anzahl. Statt einem Skalar (value) liefert dieser Kopf 72 Gradienten je
# Position. Gemessene Zielbalance auf 150 v16-Spielen: 40.9% belegt (41/59, kein
# Klassenungleichgewicht), alle 18 Slots am Spielende belegt (keine Maskierung
# noetig). 0.0 = Kopf aus (Bestandsverhalten byte-identisch, da der Kopf ZULETZT
# initialisiert wird und den RNG-Strom der uebrigen Module nicht verschiebt).
OWNERSHIP_TARGETS = 72
OWNERSHIP_WEIGHT  = 0.0

# Konjunktions-Erweiterung des Ownership-Kopfs (2026-08-10, Nutzer-Auftrag
# "bau in den ownership head die konjunktionen ein").
#
# Der Ownership-Kopf ist der RANDLAYER: 36 Felder je Spieler, "am Ende belegt".
# Damit sind die ADDITIVEN Wertungskriterien exakt abgedeckt -- Kriterium 4
# (Randfelder, +1 je Feld) und Kriterium 6 (Spezialfelder, -3 je leerem Feld),
# denn dort ist `Summe P(Feld)` der Erwartungswert. Die KONJUNKTIVEN Kriterien
# lassen sich daraus NICHT ableiten: `P(alle 6 Felder belegt)` ist nicht das
# Produkt der Einzelwahrscheinlichkeiten. Sie brauchen je einen eigenen
# Ausgang -- das sind diese 25 je Spieler (Reihenfolge siehe
# `neural_net.py::_conjunctions_from_dome`):
#   6 Reihen + 6 Spalten + 2 Diagonalen + 4 Eckplatten + 1 Jokerfeld-Konjunktion
#   + 6 farbenreiche Reihen  = 25,  x 2 Spieler = 50.
#
# Kriterium 7 (farbenreiche Reihen) kann prinzipiell NICHT aus `ownership`
# kommen: das dortige Ziel ist belegt/leer OHNE Farbe.
#
# Die Erweiterung ist additiv und standardmaessig AUS: bei
# `CONJUNCTION_HEAD=False` behaelt `ownership_head` exakt seine
# `OWNERSHIP_TARGETS`-Breite, Bestandscheckpoints laden unveraendert und der
# ONNX-Ausgabevertrag bleibt gleich.
# Bewusst KEIN eigenes Gewicht: die Zusatzziele haengen am selben Kopf und
# damit am selben Verlustterm wie der Randlayer, gesteuert von
# OWNERSHIP_WEIGHT. Der Loss mittelt elementweise ueber die unmaskierten
# Spalten, die 68 Zusatzziele bekommen also ~49% des Gradientenanteils
# (68 von 140) -- keine Verdraengung, aber auch keine Bevorzugung.
#
# 25..33 SIND KEINE KONJUNKTIONEN, sondern LAYOUT (2026-08-10, Nutzer-Auftrag
# "mach das"): `P(Slot s traegt am Ende eine Jokerplatte)`. Sie schliessen die
# EINZIGE Abdeckungsluecke -- Kriterium 3 ist das einzige mit einem
# ZUSTANDSABHAENGIGEN Punktwert (`2 x wild_total`), alle anderen sind konstant
# oder positionsfest. Ueber `E[wild_total] = Summe P(Slot s wild)` wird der
# Multiplikator schaetzbar, also ein Zaehler als Summe von Indikatoren --
# dieselbe Zerlegung, mit der Kriterium 3 ueberhaupt in die
# Wahrscheinlichkeitsfassung kam. Gemessene Spanne 1..8 Jokerfelder je Brett;
# mit dem AKTUELLEN wild_total zu multiplizieren verzerrt frueh nach unten.
CONJUNCTIONS_PER_PLAYER = 34
CONJUNCTION_TARGETS     = CONJUNCTIONS_PER_PLAYER * 2   # 68

# Task #12: Distributionaler Punkte-Kopf. 0 = AUS (Skalar-Regression wie bisher),
# >0 = Anzahl der Bins, ueber die der `points_head` eine VERTEILUNG der
# tanh-gestauchten Punktedifferenz vorhersagt statt eines Punktschaetzers.
#
# Idee (Bellemare et al. C51; Farebrother et al. 2024 "Stop Regressing"):
# ein Kreuzentropie-Ziel ueber Bins liefert ein reicheres Gradientensignal als
# MSE und ist gegen Ausreisser robuster -- bei identischer Schnittstelle nach
# aussen, weil weiterhin der ERWARTUNGSWERT der Verteilung als Skalar
# ausgegeben wird. `net.rs` liest out[0..3] positionsbasiert und merkt davon
# nichts; die Verteilungs-Logits haengen ZULETZT an den Ausgaben (nach
# `ownership`, gleiches Muster wie Task #9).
#
# 51 Bins = C51-Standardwert. Glaettung per HL-Gauss (Gauss-CDF-Differenzen
# ueber die Bin-Kanten) statt Two-Hot -- laut "Stop Regressing" durchweg besser.
POINTS_DIST_BINS   = 0
POINTS_DIST_SIGMA  = 0.75   # Glaettungsbreite in BIN-BREITEN (Paper-Empfehlung)
