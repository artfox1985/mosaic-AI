# Design-Dokument: 2D-Encoder (Task #11, Phase 1 + 2)

Status: Phase 1 (Kompatibilitätsschicht + Skelett) abgeschlossen. Phase 2
(Zwei-Input-Training, siehe Abschnitt 10) läuft. Dieses Dokument begründet die
Design-Entscheidungen für den 2D-Encoder-Zweig, der additiv NEBEN dem
bestehenden flachen 708-Feature-Netz entsteht (siehe `feedback`/Memory
"2D-Encoder muss additiv sein": bestehende ONNX-Modelle v1..v18 müssen ladbar
UND spielbar bleiben — Arena, Gating, Kader, Server).

## 10. Phase-2-Entscheidung (2026-07-29/30): Zwei-Input statt Ein-Input

Die in Abschnitt 6 offen gelassene Frage 3 ist ENTSCHIEDEN, GEGEN die
Phase-1-Annahme: der Export nutzt **zwei ONNX-Graph-Inputs** (`planes`
`[batch,76,6,6]`, `state` `[batch,708]`), nicht einen kombinierten Rang-4-
Tensor. Grund: eine Latenz-Messung (`examples/latency_2d_vs_flat.rs`,
Commit 4992e7a) zeigte, dass ein Voll-Broadcast des nicht-räumlichen Rests in
Zusatzkanäle (die ursprünglich in Abschnitt 6 skizzierte Alternative)
`eval_pair` auf das **6,5-fache** verlangsamt hätte — bei 400 Sims/Zug im
Self-Play inakzeptabel. Reine Conv-Kosten (76 Kanäle, 2 Lagen à 48 Kanäle,
6×6 räumlich) sind dagegen günstig (gemessen 1,46× ggü. dem rein flachen
Pfad) — kein Engpass.

Konsequenzen:
- `net.rs::InputLayout` bekommt eine dritte Variante `PlanesPlusFlat{c,h,w,flat}`
  (Task #11 Phase 2). `detect_layout` erkennt sie an ZWEI ONNX-Graph-Inputs
  (Input 0 = Rang 4/Planes, Input 1 = Rang 2/Flat — jede andere Kombination/
  Reihenfolge ist ein harter Fehler). `eval`/`eval_pair` nehmen weiterhin
  EINEN zusammenhängenden `&[f32]`-Puffer je Sample (Konvention: Planes-Teil
  gefolgt vom Flat-Teil), intern in zwei Tensoren gesplittet
  (`Net::build_inputs`/`split_planes_flat_batch`).
- Der Flach-Zweig bekommt den KOMPLETTEN bestehenden 708er-Vektor
  (`state_to_tensor`/`state_to_features_direct` UNVERÄNDERT) statt eines
  reduzierten "nicht-räumlichen Rests" — Redundanz zum Kuppel-Anteil des
  Flach-Vektors bewusst akzeptiert: kein neues Feature-Engineering, der
  Flach-Zweig bleibt byte-identisch zum `MosaicNet`-Input.
- `Mosaic2DNet.forward(x_planes, x_flat)`: `x_flat` ist im Phase-1-Skelett
  optional (Nullen-Default) geblieben, ist im Phase-2-Trainingspfad aber
  PFLICHT (siehe `train.py --encoder 2d`).
- Rust-Zwilling `features::state_to_planes_direct`/`state_to_features_2d_direct`
  ergänzt (Phase 1 hatte nur den Python-Pfad `neural_net.py::state_to_planes`,
  kein Rust-Äquivalent). Paritätstest (`examples/planes_parity.rs` +
  Python-Vergleich) bestätigt exakte Übereinstimmung (Toleranz 0) über 60
  echte Zustände aus `evaluations/frozen_eval_set.pkl`, gestreut über alle
  5 Runden.
- Der ONNX-Zwei-Input-Roundtrip (`examples/net_2d_probe_two_input.rs`) belegt
  die komplette Kette Python-Export -> `Net::load_auto` -> `eval`/`eval_pair`
  ohne Wheel-Install. Bestehende Ein-Input-Pfade (Flat, Planes) bleiben
  nachweislich byte-identisch (`net_load_auto_backcompat.rs` weiterhin grün
  gegen `alphazero_v17_best.onnx`/`alphazero_v18_best.onnx`).

## 1. Motivation

Der dokumentierte blinde Fleck des Projekts: die acht Wertungsplatten mit
Reihen-/Spalten-/Diagonalen-Geometrie (siehe `engine/src/scoring.rs`,
`wertung_progress`/`score_*`) werden über Generationen hinweg fast nie
geschlossen (0 Horizontale Reihen, 1 Vertikale Reihen, 2 Diagonale Reihen,
7 Farbenreiche Reihen). Das flache 708-Feature-Netz bekommt die Kuppel als
`3×3 Slots × 4 Spaces × 17 Rohwerte` linearisiert (`state_to_tensor`
Abschnitt 6) — ein MLP muss "Zeile 3 des 6×6-Rasters ist eine Zeile" erst aus
708 unstrukturierten Zahlen lernen. Translations-invariante Convolution
allein würde dieses Problem NICHT automatisch lösen: Mosaic-Wertung ist
positions-*spezifisch* (Ecken zählen 3 bzw. 8 Punkte je nach Position,
Rand zählt, Diagonalen sind exakte Diagonalen), nicht translationsinvariant
wie z. B. "irgendeine 3-in-einer-Reihe". Deshalb ergänzt der Entwurf die
Convolution explizit um konstante, positionsspezifische Geometrie-Kanäle
(Abschnitt 3) statt sich allein auf die Faltung zu verlassen.

## 2. Brett-Geometrie: 6×6-Gitter je Spieler

Quelle: `engine/src/scoring.rs::build_grid` — bereits im bestehenden Code die
kanonische Umrechnung: Kuppel-Slot `(sr, sc) ∈ {0,1,2}²`, Space-Index
`si ∈ {0,1,2,3}` innerhalb des 2×2-Kuppelplättchens (Reihenfolge TL, TR, BL,
BR wie in der JSON-`spaces`-Liste) →
`grid_row = sr*2 + si/2`, `grid_col = sc*2 + si%2`.
Damit ergibt sich pro Spieler ein natives **6×6-Gitter** — exakt die
Wertungsgeometrie aus `engine_manual.md` §2 ("3×3-Raster... jede Platte aus
2×2 Feldern... 6×6-Wertungsraster").

Zwei Spieler, ego-geordnet (erst der Spieler am Zug, dann der Gegner —
dieselbe Konvention wie in `state_to_tensor` Abschnitt 5/6, damit das
Value-Ziel unverändert "aus Sicht des aktiven Spielers" bleibt): zwei
6×6-Planes-Blöcke, nebeneinander in der Kanal-Dimension (nicht als
zusätzliche Batch- oder Spatial-Dimension — beide Bretter sind unabhängige
Informationsquellen, keine räumliche Nachbarschaft zwischen ihnen).

## 3. Kanal-Vorschlag (Board-Encoding)

Pro Spieler-Brett (6×6), Vorschlag für Phase 2 (ANZAHL/AUFTEILUNG NICHT in
Stein gemeißelt, siehe offene Fragen):

| Gruppe | Kanäle | Inhalt |
|---|---|---|
| Slot vorhanden | 1 | 1.0 falls das 2×2-Kuppelplättchen an dieser Slot-Position bereits liegt (mid-game können Slots leer/nicht existent sein), sonst 0.0 — je Feld dupliziert aus dem 3×3-Slot-Flag |
| Belegte Farbe (one-hot) | 5 | blau/gelb/rot/schwarz/türkis, 1.0 am belegten Feld, sonst überall 0 |
| Belegt (Special) | 1 | `placed_special` (weiße Spezialfliese liegt) |
| Geforderte Farbe (one-hot) | 5 | `required_color` bei NORMAL-Feldern, sonst überall 0 (WILD/SPECIAL haben keine feste Farbe) |
| Feldtyp (one-hot) | 3 | NORMAL / WILD / SPECIAL — redundant zur "geforderte Farbe leer"-Information, aber explizit macht die Unterscheidung WILD (jede Farbe ok) vs. "kein Slot" robuster ohne Rückschluss aus Abwesenheit |
| Locked | 1 | nur für SPECIAL relevant (0=offen, 1=noch gesperrt) |
| **Zwischensumme** | **16** | pro Spieler |

Macht **32 Kanäle** für beide Spieler-Bretter zusammen. Das ist ein
Vorschlag, kein Commitment — siehe offene Frage zum Kanalbudget (Abschnitt
6). Die Werte sind 1:1 aus denselben Rohfeldern abgeleitet wie
`state_to_tensor` Abschnitt 6 (`FILLED_ID_MAP`, `COLOR_ID_MAP`, `TYPE_MAP`,
`locked`) — nur räumlich angeordnet statt linearisiert, damit KEINE neue
Informationsquelle entsteht, nur eine andere Struktur derselben Information
(hält Phase-2-Vergleiche fair, siehe Abschnitt 5).

## 4. Positions-Ebenen: Wertungsgeometrie + Gating

Kern-Idee gegen den blinden Fleck (Abschnitt 1): konstante Kanäle, die JEDER
Zelle mitteilen, zu welcher Wertungsgeometrie sie gehört — UND ob diese
Geometrie in DIESER Partie überhaupt eine der 3 aktiven Wertungsplatten ist
(`scoring_tile_ids`, siehe `state_to_tensor` Abschnitt 2). Ohne Gating müsste
das Netz erst die 8-dim `scoring_tile_ids`-Maske (flacher Zweig) mit der
räumlichen Geometrie (Conv-Zweig) mental verknüpfen — das Gating nimmt ihm
genau diese Verknüpfung vorweg, an der Stelle, wo sie am nützlichsten ist
(pro Zelle, nicht global).

Mapping Wertungsplatten-ID → Geometrie (Quelle: `scoring.rs::wertung_progress`
match-Arme, IDs = `ALL_SCORING_TILES`-Index):

| Tile-ID | Kriterium | Geometrie-Maske |
|---|---|---|
| 0 | Horizontale Reihen (3 Pkt/Reihe) | 6 Zeilen-Masken |
| 1 | Vertikale Reihen (7 Pkt/Reihe) | 6 Spalten-Masken |
| 2 | Diagonale Reihen (10 Pkt/Diagonale) | 2 Diagonal-Masken |
| 3 | Wild-Felder | *kein* Geometrie-Kanal nötig — WILD-Feldtyp ist bereits Teil des Belegungs-Encodings (Abschnitt 3), keine zusätzliche raumbezogene Struktur |
| 4 | Äußere Felder (Rand, 1 Pkt/Feld) | 1 Rand-Maske (äußerer Ring des 6×6) |
| 5 | Eckplatten (3 bzw. 8 Pkt je nach Ecke) | 4 Ecken-Masken (je 2×2-Slot (0,0)/(0,2)/(2,0)/(2,2)) — bewusst 4 EINZELNE Masken statt 1 gemeinsamer, weil die Punktwerte pro Ecke ungleich sind (oben 3, unten 8) |
| 6 | Spezialfelder (−3 Pkt je leer) | *kein* Geometrie-Kanal nötig — SPECIAL-Feldtyp + `locked` sind bereits im Belegungs-Encoding |
| 7 | Farbenreiche Reihen (4 Pkt/Reihe) | dieselben 6 Zeilen-Masken wie Tile 0 (gleiche Geometrie, andere Formel — beide können unabhängig aktiv sein) |

Konstante Roh-Masken (ohne Gating, damit das Netz Geometrie auch dann
"sieht", wenn sie gerade nicht scored): 6 Zeilen + 6 Spalten + 2 Diagonalen +
1 Rand + 4 Ecken = **19 Kanäle**, geteilt zwischen beiden Spielern (die
Geometrie ist brettunabhängig identisch, keine Verdopplung nötig).

Gegatete Varianten (Maske × 0/1-Flag "ist zugehörige Tile-ID aktiv"), je
EINMAL für Zeilen-Gate(Tile 0) + Zeilen-Gate(Tile 7) getrennt (unterschiedliche
Formeln, beide können gleichzeitig aktiv sein), plus Spalten/Diagonalen/Rand/
Ecken je einmal: 6+6+6+2+1+4 = **25 Kanäle**. Auch diese sind
brettunabhängig (Wertungsplatten gelten für beide Spieler gleich), keine
Verdopplung.

**Zwischensumme Geometrie: 19 (roh) + 25 (gegatet) = 44 Kanäle.**

## 5. Nicht-räumlicher Rest + Fusion

Fabriken (4× klein + 1× groß), Beutel/Turm-Farbanteile, Bonusplättchen/Chips,
Scores/`estimated_score`, Musterreihen, Mond-Stapel, Kuppel-Display,
Kuppel-Stapel-Restbestand: bleiben FLACH, exakt wie bisher in
`state_to_tensor` (KEINE natürliche 2D-Struktur — eine Fabrik ist eine
Menge, keine Geometrie). Der 2D-Encoder ERSETZT `state_to_tensor` nicht,
sondern läuft parallel dazu.

Späte Fusion: kleiner Conv-Stack (Vorschlag 2–3 Lagen 3×3, 32–64 Kanäle,
BatchNorm+ReLU wie der bestehende Trunk) auf den ~76 Board-Kanälen
(32 Belegung + 44 Geometrie, siehe oben) → `flatten` (6×6×Kanäle) → `concat`
mit dem Output des bestehenden flachen Zweigs (oder einer eigenen kleinen
Flach-Vorverarbeitung des nicht-räumlichen Rests) → bestehende Trunk-Breite
512 (`HIDDEN_SIZE`) → bestehende Köpfe (`policy_head`, `value_head`,
`moon_order_head`, `points_head`, `ownership_head`) UNVERÄNDERT, gleiche
Ausgabereihenfolge, gleiche `net.rs`-Positionsindizes `out[0..3]`. `net.rs`
liest weiterhin nur `out[0..3]` (policy/value/moon/points) und bleibt davon
komplett unberührt — der 2D-Zweig ist reine Feature-Extraktion vor dem
gemeinsamen Trunk, keine Kopf-Änderung.

## 6. ONNX-Export-Plan

Analog zu `export_onnx.py`, aber mit ZWEI Inputs statt einem (`state` bleibt
für den Flach-Zweig, neu: `planes` für den Conv-Zweig) ODER — einfacher,
näher an der bestehenden `Net::load_auto`-Rang-Erkennung (Teil A) — EIN
Input mit Rang 4 `[batch, C, 6, 6]`, falls sich der nicht-räumliche Rest
ebenfalls sinnvoll in Zusatzkanälen unterbringen lässt (offene Frage, siehe
Abschnitt 7). Für Phase 1 wurde bewusst der EIN-Input-Rang-4-Fall
implementiert (`InputLayout::Planes{c,h,w}`), weil `load_auto` dann rein aus
der Tensor-Form entscheiden kann, ohne ein zusätzliches Manifest-Feld für
"wie viele Inputs hat dieses Modell" zu brauchen. Zwei-Input-Modelle sind
in `Net::load_auto`/`detect_layout` NICHT vorgesehen — falls Phase 2 sich
für einen echten Zwei-Input-Export entscheidet, braucht `detect_layout`
eine Erweiterung (siehe offene Frage).

- `dynamic_axes`: wie bisher `{0: "batch"}` auf ALLEN Ein-/Ausgängen (sonst
  bricht `eval_pair`s fester Batch=2-Plan auf Graph-Ebene, siehe
  `export_onnx.py`-Kommentar zum selben Thema).
- `opset_version=13`, `dynamo=False` — unverändert, gleiche Werte wie
  `export_onnx.py::export`, damit die tract-Kompatibilität nicht neu
  validiert werden muss.
- Ausgabereihenfolge/-namen (`policy, value, moon, points, ownership[,
  points_dist]`) bleiben BYTE-IDENTISCH — `Mosaic2DNet` (Teil C) hat exakt
  dieselben Köpfe wie `MosaicNet`.

## 7. Cache-Key-Plan

`MosaicDataset.__init__` (`engine/py/neural_net.py`) hasht bereits
`INPUT_SIZE + NUM_ACTIONS + VALUE_SCHEMA_VERSION + POLICY_TARGET_SHARPEN_EXPONENT
+ TD_LAMBDA + value_target_variant + "+rounds_v1+own_v1"` in den
HDF5-Cache-Key (siehe Kommentar dort zum `TD_LAMBDA`-Vorfall: ein
vergessenes Hash-Feld ließ einen Sweep stillschweigend denselben Cache
wiederverwenden, ohne etwas zu messen — dieselbe Falle gilt hier). Ein
`encoder_variant`-Flag (analog zu `value_target_variant`, Werte z. B.
`"flat"` / `"planes_v1"`) MUSS in den Hash-String aufgenommen werden, plus
ein Suffix-Marker `"+enc2d_v1"` (gleiches Muster wie `"+rounds_v1+own_v1"`)
für den Tag, an dem sich das Planes-Tensor-Schema selbst ändert (z. B.
Kanalzahl/-reihenfolge). Der HDF5-Cache bekäme ein zusätzliches Dataset
`planes` der Form `[N, C, 6, 6]` NEBEN dem bestehenden `states`
(`[N, 708]`) — beide Datasets koexistieren im selben Cache-File, ein Sample
liefert weiterhin EIN `(states[i], planes[i], ...)`-Tupel. Kein HDF5-Bau in
Phase 1 (Stopp-Linie).

## 8. Fairer Maßstab für Phase 2

**2D-from-scratch GEGEN FLACH-from-scratch auf identischem Korpus** — NICHT
gegen den warmgestarteten aktuellen Champion (v18_best). Präzedenzfall v14
(Memory `project_v14_rebuild`): eine from-scratch-Distillation lag bei
gleicher Architektur ~220 Elo unter der Warm-Start-Linie, rein weil
Warm-Start Trainings-Epochen "spart", die from-scratch erst nachholen muss
— ein 2D-Netz OHNE Warm-Start-Äquivalent (es gibt keinen 2D-Checkpoint zum
Warmstarten) gegen den warmgestarteten Flach-Champion zu testen würde die
Architektur-Frage mit der Warm-Start-Frage konfundieren und mit hoher
Wahrscheinlichkeit fälschlich gegen 2D ausfallen, unabhängig vom
tatsächlichen architektonischen Wert. Der faire Vergleich: beide Zweige
from-scratch, gleicher Korpus (gleiches `data/`-Fenster), gleiche
Trainings-Hyperparameter (LR, Epochen-Budget, Sonstiges), gleiche
Zufalls-Seeds über mehrere Wiederholungen (Memory
`project_training_seed_variance`: Seed bewegt die Metrik 4–6× stärker als
jeder einzelne Knopf — ein Single-Run-A/B ist hier nicht interpretierbar,
mindestens ~6 gepaarte Seeds wie im Seed-Varianz-Befund). Erst nach
gewonnenem from-scratch-Vergleich lohnt sich die Frage, wie ein
2D-Warmstart-Pfad aussehen könnte (z. B. Flach-Trunk-Gewichte für den
gemeinsamen Teil übernehmen, Conv-Zweig zufällig init) — das ist NICHT Teil
von Phase 2, sondern eine mögliche Phase 3.

## 9. Offene Fragen

1. **Nicht gelegte Slots**: Ein 3×3-Slot kann midgame fehlen (Kuppelplatte
   noch nicht gezogen). Vorschlag oben: alle Sub-Kanäle 0, "Slot vorhanden"-
   Kanal 0 — funktional äquivalent zu "leerer Rand" bei klassischem Conv-
   Padding, ABER hier ECHTE Spielinformation (nicht nur Padding-Artefakt).
   Muss das Netz das unterscheiden können von "Slot vorhanden, aber alle 4
   Felder noch leer"? Aktuell JA über den "Slot vorhanden"-Kanal, aber nicht
   weiter validiert (kein Trainingslauf in Phase 1).
2. **Kanalzahl-Budget vs. Inferenzlatenz bei 400 Sims Self-Play**: 32
   (Belegung) + 44 (Geometrie) = 76 Input-Kanäle in den Conv-Stack, plus
   32–64 Kanäle in den Hidden-Conv-Lagen — bei 6×6 räumlich klein (deutlich
   billiger als typische CNN-Bildgrößen), aber Self-Play läuft mit 400 Sims/
   Zug und die aktuelle `eval_pair`-Batch=2-Optimierung (Paket 1) ist
   explizit auf den bestehenden flachen Graphen zugeschnitten — noch NICHT
   gemessen, ob tract den Conv-Zweig bei Batch=1/2 ähnlich günstig optimiert
   wie den reinen MLP-Pfad. Erste Messung gehört in Phase 2, bevor
   Self-Play-Kosten grob geschätzt werden.
3. **Ein Input (Rang 4) vs. zwei Inputs (Flach + Planes getrennt)**: Phase 1
   hat sich für "ein Input, Rang 4" entschieden, weil `load_auto`s
   Rang-basierte Erkennung dann ausreicht. Falls sich in Phase 2
   herausstellt, dass der nicht-räumliche Rest schlecht in Zusatzkanäle
   passt (z. B. weil er nicht sauber auf 6×6 broadcastet), müsste
   `detect_layout` einen "zwei Inputs"-Fall lernen — nicht in Phase 1
   vorweggenommen, um die Kompatibilitätsschicht nicht unnötig zu
   verkomplizieren, bevor der Bedarf feststeht.
4. **Gating-Granularität**: Abschnitt 4 gated pro Zelle mit einem globalen
   0/1-Flag (aktive Tile-ID ja/nein). Eine kontinuierliche Variante (z. B.
   aktueller Punktestand der Platte statt binärem Flag) wurde NICHT
   verfolgt — Phase 1 ist Skelett, keine Feature-Feinjustierung.
5. **Eckplatten-Gewichtsasymmetrie (3 vs. 8 Punkte)**: die 4 Ecken-Masken
   sind gleich stark (alle 1.0 wo befüllt), die Punktwert-Asymmetrie muss
   das Netz selbst aus dem Value-/Points-Ziel lernen (kein Channel kodiert
   den Gewichtungsfaktor explizit) — bewusste Vereinfachung, Alternative
   (Masken direkt mit Punktwert skaliert, z. B. 3.0/8.0 statt 1.0) nicht
   geprüft.
