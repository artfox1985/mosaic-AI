# head_warmstart.py
"""Nutzer-Auftrag 2026-08-11: gezielte Kopf-Teiluebernahme fuer train.py.

train.py wirft beim Warm-Start (`--load`) formabweichende Tensoren bisher
komplett weg -- sie starten dann zufaellig, auch wenn ein Teil der
Information eigentlich uebertragbar waere (siehe `skipped`-Filter kurz nach
dem Aufruf von `apply_head_warmstart()` in train.py::train()). Diese Datei
behandelt zwei konkrete Faelle, in denen das der Fall ist. Eigenes Modul
(statt inline in train.py), weil train.py bereits ueber der Datei-Groessen-
Ratsche (tools/check_conventions.py, Regel 1) liegt -- ein neuer, eigener
Baustein ist der von der Ratsche selbst vorgeschlagene Ausweg (a).
"""
from config import OWNERSHIP_TARGETS


def apply_head_warmstart(old_state: dict, new_state: dict, head_warmstart: bool = True) -> dict:
    """Teiluebernahme statt Zufall bei zwei Shape-Mismatches (Details in den
    Fall-Kommentaren unten). `head_warmstart=False` (train.py-Flag
    --no-head-warmstart) schaltet beides ab, `old_state` bleibt unveraendert
    -- fuer den A/B "Warmstart gegen Zufall". Default AN: beides ist ein
    reiner Startpunkt-Fix, kein neuer Freiheitsgrad -- das bisherige
    Wegwerfen formabweichender, aber inhaltlich uebertragbarer Zeilen war
    ein Bug, keine bewusste Wahl, also gilt der Fix standardmaessig. Bei
    passenden Formen (kein Mismatch in den betroffenen Keys) aendert diese
    Funktion nichts -- additiv und still im Normalfall.

    Mutiert und gibt `old_state` zurueck (Aufrufer kann das Rueckgabeobjekt
    verwenden, muss aber nicht -- Mutation in-place fuer bestehende Keys,
    neue Keys werden per `update()` ergaenzt)."""
    if not head_warmstart:
        return old_state

    # (a) opp_points_head <- points_head: BYTE-IDENTISCHE Architektur
    # (Linear-ReLU-Linear-Tanh, siehe neural_net.py MosaicNet/Mosaic2DNet
    # __init__, Kommentar "opp_points_head ... BYTE-IDENTISCHE Architektur
    # ... zu MosaicNet") und dieselbe Aufgabe (Punkteprognose aus derselben
    # Trunk-Repraesentation `shared`) -- nur die Kopf-DEUTUNG dreht sich von
    # "eigene Punkte" auf "Gegner-Punkte". ACHTUNG: der kopierte Kopf ist
    # beim ersten Forward-Pass SYSTEMATISCH FALSCH (er sagt die EIGENEN
    # Punkte voraus, wo Gegnerpunkte gefragt sind) -- kein Ersatz fuer
    # Training, nur ein informativerer Startpunkt als Zufall (die Eingabe-
    # Features sind dieselben, nur ihre Lesart muss sich drehen statt bei
    # Null zu beginnen). Greift nur, wenn der NEUE Kopf existiert und im
    # ALTEN Checkpoint komplett fehlt (sonst laueft der normale Warmstart-
    # Pfad ohnehin schon warm).
    opp_prefix, pts_prefix = "opp_points_head.", "points_head."
    new_opp_keys = [k for k in new_state if k.startswith(opp_prefix)]
    had_opp_before = any(k.startswith(opp_prefix) for k in old_state)
    if new_opp_keys and not had_opp_before:
        mirrored = {}
        for k in new_opp_keys:
            src = pts_prefix + k[len(opp_prefix):]
            src_v = old_state.get(src)
            if src_v is None or src_v.shape != new_state[k].shape:
                mirrored = None
                break
            mirrored[k] = src_v.clone()
        if mirrored:
            old_state.update(mirrored)
            print(f"   ↺ opp_points_head aus points_head gespiegelt ({len(mirrored)} "
                  f"Tensoren) -- startet SYSTEMATISCH FALSCH (sagt zunaechst eigene statt "
                  f"Gegner-Punkte voraus), aber informativer als Zufall; ersetzt kein "
                  f"Training.")
        else:
            print(f"   ↻ opp_points_head bleibt zufaellig initialisiert (points_head im "
                  f"alten Checkpoint fehlt oder passt nicht in der Form)")

    # (b) ownership_head verbreitert (CONJUNCTIONS_PER_PLAYER gewachsen,
    # z.B. 25->34 Zeilen je Spieler): NICHT trunkieren. Layout GEPRUEFT am
    # Code (corpus_dataset.py::MosaicDataset, own_l.append-Stelle, Kommentar
    # "[0:36] Rand ich, [36:72] Rand Gegner, [72:97] Konj. ich, [97:122]
    # Konj. Gegner" -- NICHT nur aus der Tupelreihenfolge (own_p0, own_p1,
    # conj_p0, conj_p1) abgeleitet): [OWNERSHIP_TARGETS Ownership][conj_p0]
    # [conj_p1]. Ownership UND conj_p0 beginnen in alter und neuer Breite an
    # DERSELBEN Position (0 bzw. OWNERSHIP_TARGETS) -- nur conj_p1 rutscht um
    # die Breitendifferenz von conj_p0 nach hinten. Ein Kopieren der ersten N
    # Zeilen traefe Ownership/conj_p0 richtig, verdrahtete conj_p1 aber
    # falsch (Spieler-1-Werte auf Spieler-0-Indizes) -- sieht plausibel aus,
    # ist aber schlimmer als Zufall. Daher explizite Index-Abbildung statt
    # eines Slice.
    wkey, bkey = "ownership_head.2.weight", "ownership_head.2.bias"
    if (wkey in old_state and bkey in old_state
            and wkey in new_state and bkey in new_state
            and old_state[wkey].shape != new_state[wkey].shape):
        old_w, new_w = old_state[wkey], new_state[wkey]
        old_bias, new_bias = old_state[bkey], new_state[bkey]
        old_width, new_width = int(old_w.shape[0]), int(new_w.shape[0])
        old_conj, new_conj = old_width - OWNERSHIP_TARGETS, new_width - OWNERSHIP_TARGETS
        if (old_width < OWNERSHIP_TARGETS or new_width < OWNERSHIP_TARGETS
                or old_conj % 2 != 0 or new_conj % 2 != 0 or new_conj < old_conj):
            print(f"   ⚠️  {wkey}: Breite {old_width}->{new_width} passt nicht ins "
                  f"erwartete Layout [Ownership={OWNERSHIP_TARGETS}][conj_p0][conj_p1] -- "
                  f"Teiluebernahme ausgelassen, startet komplett frisch.")
        else:
            old_half, new_half = old_conj // 2, new_conj // 2
            new_w_out, new_b_out = new_w.clone(), new_bias.clone()
            # Ownership + conj_p0: identische Startposition/Breite in alt
            # und neu -> direkte Bereichsuebernahme.
            head_rows = OWNERSHIP_TARGETS + old_half
            new_w_out[:head_rows] = old_w[:head_rows]
            new_b_out[:head_rows] = old_bias[:head_rows]
            # conj_p1: alt beginnt bei OWNERSHIP_TARGETS+old_half, neu bei
            # OWNERSHIP_TARGETS+new_half -- Versatz exakt (new_half -
            # old_half) Zeilen.
            old_p1, new_p1 = OWNERSHIP_TARGETS + old_half, OWNERSHIP_TARGETS + new_half
            new_w_out[new_p1:new_p1 + old_half] = old_w[old_p1:old_p1 + old_half]
            new_b_out[new_p1:new_p1 + old_half] = old_bias[old_p1:old_p1 + old_half]
            old_state[wkey], old_state[bkey] = new_w_out, new_b_out
            n_random = new_width - head_rows - old_half
            print(f"   ↺ {wkey}/{bkey}: {head_rows + old_half} von {new_width} Zeilen "
                  f"uebernommen (Ownership 0-{OWNERSHIP_TARGETS - 1} + conj_p0 "
                  f"{OWNERSHIP_TARGETS}-{head_rows - 1} unveraendert, conj_p1 "
                  f"{old_p1}-{old_p1 + old_half - 1} -> {new_p1}-{new_p1 + old_half - 1} "
                  f"verschoben); {n_random} neue Layout-Zeilen je Spieler bleiben zufaellig.")
    return old_state
