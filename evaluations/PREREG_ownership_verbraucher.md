# PREREG: Ownership-Kopf als Verbraucher in Drafting und Tiling

Stand 2026-08-13, ENTWURF (nichts hiervon ist gebaut — durchgehend Plan-Zeitform).
Nutzer-Auftrag: *"überleg dir dann auch schon mal wie wir den ownership head ins
drafting und tiling miteinbeziehen"*. Kontext: Zwei-Pole-Architektur
(PREREG_provokation.md) — Netz-Pol und Platten-Heuristik-Pol, der
Ownership-Verbraucher ist der RUNTIME-REGLER dazwischen.

## §1 Geprüfter Ist-Stand

- **Kopf-Layout** (neural_net.py:1836-1837, :2366-2367): 72 Binärausgaben =
  2 Spieler × 36 Kuppelfelder (3×3 Slots × 4 Felder), ego-perspektivisch —
  `[0:36]` ich, `[36:72]` Gegner, je Feld "am Spielende belegt?". Optionale
  Konjunktions-Erweiterung `--conjunction` (train.py:2046-2055): `[72:97]`
  konjunktive Wertungskriterien ich, `[97:122]` Gegner; die ADDITIVEN
  Kriterien 4 und 6 deckt schon der Randlayer.
- **Kopf ist blind**: Champion v21_2d_brierbest wurde mit `ownership_weight:
  null` → Config-Default 0,0 = "Kopf aus" trainiert
  (models/manifest_train_v21_2d_20260809_004805.json; train.py:2059).
  Die Gewichte des Kopfes sind untrainiert.
- **Kein Verbraucher**: ONNX-Ausgang 4 (ownership) wird engine-seitig nirgends
  gelesen (Befund der Architektur-Durchsicht, STATUS.md P4).
- **Vorbild-Muster**: Task #28 (`blended_leaf_win_prob`, net_mcts.rs:1775-1780) —
  Regler-Default 0 → Early-Out, byte-identisches Bestandsverhalten; Test
  net_mcts.rs:7545 sichert den Default.

## §2 Entwurf Verbraucher 1: Drafting (Blattbewertung)

Am Blatt liegt die Ownership-Karte des Netzes ohnehin vor (gleicher
Forward-Pass). Daraus würde je Kriterium eine ERWARTETE Plattenpunktzahl
berechnet:

    E_k = Σ_{Geometrie g von k} punkte_k · Π_{Feld f in g} p_own(f)

(für konjunktive Geometrien: Spalten k1, Diagonalen k2, Ecken k5, …;
die additiven k4/k6 direkt als Σ p·punkte). Einspeisung in DIESELBE
Shift-Form wie der Heuristik-Pol:

    shift += w_own · Σ_k gew_k · tanh(E_k / 50)

- `w_own` = neuer Knopf `MOSAIC_OWNERSHIP_W`, Default 0,0 (Early-Out,
  byte-identisch — Task-#28-Muster). Das ist der Zwei-Pole-Regler.
- `gew_k` teilt sich die 8-wertige Semantik mit MOSAIC_WERTUNG_SHAPING_W.
- Unterschied zum Heuristik-Pol: `wertung_progress_per_kriterium` misst den
  IST-Fortschritt, E_k die vom Netz PROGNOSTIZIERTE Vollendung — das Produkt
  Π p bestraft tote Spalten (ein Feld p≈0 → E≈0) von selbst; genau die
  Zielwechsel-Logik, die der Spaltenbauer in Runde 4 als Buchhaltung
  nachbauen muss.

## §3 Entwurf Verbraucher 2: Tiling (Wurzel, einmal je Zug)

Der Tiling-Solver darf keinen Netz-Aufruf je Kandidat kosten. Stattdessen:
aus der WURZEL-Ownership-Karte (liegt nach der Suche vor) einmalig je Zug
marginale Feldwerte ableiten:

    wert(f) = Σ_k gew_k · [E_k mit p_own(f):=1] − E_k

(für konjunktive Geometrien = punkte_k · Π über die ÜBRIGEN Felder — der Wert
eines Feldes steigt, je voller seine Spalte/Diagonale schon ist). Diese
36 Feldwerte gingen als KOMPLEMENT in `best_first_step_platten_valued`
(tiling_solver.rs) ein, analog `zellen_wert` im Spaltenbauer — Routing zu
Feldern, deren Geometrien das Netz für vollendbar hält.

## §4 Gegner-Hälfte → Störungs-Baustein

`[36:72]` liefert E_k^gegner gratis. Der Störungs-Baustein (Farbzählung,
domain_knowledge.md §4) bekäme damit ein gelerntes Komplement: Drafting-Malus
proportional zum marginalen Feldwert des GEGNERS für die gezogene Farbe.
Eigenes Gewicht, eigener Arm — nicht mit der Eigen-Hälfte verrechnen.

## §5 Reihenfolge und Tore (vorab festgelegt)

1. **Generator zuerst** (läuft, Spalten-Runde 4): ohne plattenreiche Partien
   lernt der Kopf die Geometrien nie — im Bestandskorpus schafft das Netz
   ~0,3 Spalten/Partie.
2. **Kopf trainieren**: `ownership_weight > 0` + `--conjunction` auf dem
   Zwei-Pole-Korpus (Netz-Pol + Heuristik-Pol + Streuung).
3. **Tor A — Kopfgüte VOR Verbraucher-Bau**: Brier/AUC je Feld auf
   Held-out-plattenreichen Partien gegen die Basisrate; zusätzlich E_k gegen
   tatsächliche Plattenpunkte (Rangkorrelation je Kriterium). Ein blinder
   Kopf darf nicht steuern.
4. **Tor B — Bestandsschutz**: `w_own=0` byte-identisch (Test wie
   net_mcts.rs:7545); Heuristik-Anker unberührt.
5. **Tor C — Regler-Sweep**: w_own-Raster in der Arena, Messgrößen
   Plattenpunkte je Kriterium + Endstand-Marge (die Nutzer-Zielgröße),
   Block-Ebene, Orakel-Schwellen aus PREREG_provokation.md.
6. Verdrahtung (net.rs Ausgang 4 durch tract/ORT/Batcher reichen) kann als
   P4 VOR dem Training gebaut werden — Verbraucher tot bei Default 0.

## §6 Offene Punkte

- Exakte Feld-Indexierung `[0:36]` ↔ Slot/Feld-Koordinaten vor dem Bau aus
  dem Label-Bauer (`_ownership_from_dome`, neural_net.py:882) ablesen, nicht
  herleiten.
- Kriterium 7 (farbenreiche Reihen) kann laut neural_net.py:954 NICHT aus
  ownership kommen — bleibt beim Heuristik-Pol. k0/k7 sind ohnehin
  "verteidigen, nie anstreben" (Nutzer-Entscheid).
- Kalibrierung der tanh-Skala (50) für E_k prüfen — E_k ist punkteskaliert
  wie P_term, sollte passen; messen statt annehmen.
