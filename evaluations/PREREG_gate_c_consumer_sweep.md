<!-- STATUS: ENTSCHIEDEN | Frage: Tor C -- traegt der Ownership-Verbraucher (Blatt-Pol MOSAIC_OWNERSHIP_W + Tiling-Pol MOSAIC_OWNERSHIP_TILING_W, gemeinsam gefahren) in der Arena Plattenpunkte ein, OHNE Siege zu kosten -- und welcher Kopf (F1 eingefroren vs w1-final) traegt ihn? | Beleg: **NEGATIV ENTSCHIEDEN 2026-08-16, 970 Partien** (par.15). Kein Arm hebt die Zielkriterien k1/k2/k5 -- gepoolt n=243 auf F1: k1 +0,22 (t 0,73), k2 -0,11, k5 +0,09. Siege fallen monoton mit der Dosis (98/89/86/84), D2 p=0,043 und D3 p=0,049 signifikant. Der staerkere Kopf w1-final macht den Verbraucher inert (91:91, b=c=18) statt nuetzlich -- Kopfguete ist NICHT der Engpass. Erklaerung (Herleitung): das Marginal der konjunktiven Kriterien ist ~0, solange die Spalte nicht fast fertig ist. Beide Regler bleiben auf Default 0. Beifang: F1 gegen w1-final bei Regler aus p=0,360, F1 bleibt Checkpoint der Wahl. -->

# PREREG: TOR C — Regler-Sweep des Ownership-Verbrauchers in der Arena

Stand 2026-08-16. **Registriert VOR der ersten Partie.** Alles, was noch nicht
gemessen ist, steht in Plan-Zeitform; die Ergebnisabschnitte (ab par.10) sind
zum Registrierungszeitpunkt leer.

Rahmen: `PREREG_ownership_consumer.md` par.5 Punkt 5 ("Tor C — Regler-Sweep").
Vorgelagert abgeschlossen: Tor A (`PREREG_ownership_corpus.md` par.10/par.10.6),
Tor B (`PREREG_ownership_consumer.md`-Nachtrag, byte-identisch bei Regler 0),
sowie die Frozen-Trunk-Sonde F1 (`PREREG_frozen_trunk_head.md` par.7 mit der
dortigen Empfehlung par.7.1: **beide Checkpoints gehen in Tor C**).

Tragende Nutzer-Anweisung 2026-08-16: *"nur im drafting auf die wertungsplatten
hinarbeiten ist nur die halbe miete"* — der HAUPT-ARM faehrt deshalb **beide
Haelften gemeinsam**, nicht die Drafting-Haelfte allein. Beleg dafuer, dass die
Drafting-Haelfte allein saettigt: `PREREG_placement_side.md` par.11 (1,75
vertikale Plattenpunkte gegen Nutzer-Ziel 14).

---

## par.1 Die zwei Fragen (und welche die primaere ist)

**(a) PRIMAER — Wirkt der Verbraucher?**
Derselbe Checkpoint, Regler aus gegen Regler an. Kein Checkpoint-Wechsel im
Vergleich, damit die Differenz sauber auf den Verbraucher attribuiert.

**(b) SEKUNDAER — Welcher Kopf traegt?**
`v21_2d_own_f1` (Policy intakt, Kopf mittel) gegen `v21_2d_own_w1` final
(Policy −41 %, Kopf stark), je bei ihrer besten Reglerstufe. Diese Frage ist
erst dann interessant, wenn (a) ueberhaupt einen Effekt zeigt — sie wird
deshalb NACHGELAGERT und nur bedingt gefahren (par.4, Stufe 2).

---

## par.2 Geprueft in dieser Sitzung (Ist-Stand mit Pruefstelle)

| Sache | Befund | Pruefstelle |
|---|---|---|
| Blatt-Formel | `shift_i = w_own · SUM_k gew_k · tanh(E_k/50)`, danach `clamp(value+shift, 0, 1)` | `engine/src/net_mcts.rs`, Doku zu `apply_ownership_shaping_full` (Z. ~1594-1600) |
| Blatt-Regler | `MOSAIC_OWNERSHIP_W`, Default 0,0, `OnceLock` (prozessweit einmal gelesen) | `net_mcts.rs:1528-1530` |
| Kriterienmaske Blatt | `MOSAIC_OWNERSHIP_GEW`, Default alle 1,0; Stelle 7 wirkungslos | `net_mcts.rs:1547-1564` |
| Tiling-Formel | `punkte + w · plattendelta + w_own · SUM_{f neu belegt} wert(f)`, in R2-4 danach `· p_win` | `tiling_solver.rs:1224-1290` (`best_first_step_platten_valued`) |
| Tiling-Regler | `MOSAIC_OWNERSHIP_TILING_W`, Default 0,0 | `tiling_solver.rs:1006-1015` |
| Kriterienmaske Tiling | GETEILT mit dem Heuristik-Pol: `MOSAIC_TILING_PLATTEN_GEW`, Default alle 1,0 | `tiling_solver.rs:1054-1060` |
| Rundenfenster Tiling-Pol | nur Runden 1-4 | `tiling_solver.rs::platten_branch_applies` |
| Ein Vorwaertspass je Tiling-Zug | ja, auf dem Wurzelzustand, nur wenn `w_own != 0` | `self_play.rs:1042-1070`, `:1093-1100` |
| Arena-Pfad traegt beide Pole | ja: Netz-Seite `tiling_net: Some(net)`, Heuristik-Seite `None` | `self_play.rs::play_net_game` (`tiling_net: Some(net)` / `None`), `:1696` |
| Wheel kennt die Knoepfe | ja, `mosaic_rust.cp314-win_amd64.pyd` (16.08.2026 10:57) enthaelt alle drei Knopfnamen | Byte-Suche im installierten `.pyd` |
| Wertungsplatten je Partie | **genau 3**, aus vier paarweise ausschliessenden Paaren gezogen | `scoring.rs:89` (`sample_valid_scoring_ids`), Aufrufe mit `n=3` u.a. `self_play.rs:2288` |
| Ausschluss-Paare | (0,7) (6,3) (4,1) (2,5) — **k1 und k4 nie zusammen, k2 und k5 nie zusammen, k6 und k3 nie zusammen** | `scoring.rs:60-65` |
| F1-Checkpoint | `models/alphazero_v21_2d_own_f1.onnx`, ownership-Ausgang Breite 140 | ONNX-Kopfliste; Identitaet ueber `ownership_gate_a_f1.json` (`checkpoint: alphazero_v21_2d_own_f1.pth`, 15 Epochen) |
| F1-Guete | policy val 0,2141, value-Brier 0,1884, Feld-AUC 0,780; E_k-Spearman k1 0,280 / k2 0,314 / k5 0,345 | `evaluations/ownership_gate_a_f1.json` |
| w1-final-Checkpoint | `models/alphazero_v21_2d_own_w1.onnx`, ownership-Ausgang Breite 140 | ONNX-Kopfliste |
| w1-final-Guete | policy val 0,3018, Feld-AUC 0,870, E_k k1 0,361 / k2 0,354 / k5 0,466 | `PREREG_ownership_corpus.md` par.10.6, `ownership_gate_a_w1.json` |
| Champion taugt nicht als Traeger | `alphazero_v21_2d_brierbest.onnx` hat ownership-Breite **72** und einen untrainierten Kopf | ONNX-Kopfliste + `PREREG_ownership_consumer.md` par.1 |

**Ungeprueft / uebernommen:** die Kopfguete-Zahlen von F1 und w1 stammen aus
Tor A, sind hier nur aus den JSONs abgelesen und nicht neu berechnet.

---

## par.3 HERLEITUNG DER REGLERSTUFEN (kein Startraster von der Stange)

Die Aufgabenstellung nennt "0,3–1,0" ausdruecklich als Herleitung, nicht als
Messung. Hier die eigene Herleitung, getrennt je Pol, weil die beiden Pole
**verschiedene natuerliche Einheiten** haben.

### par.3.1 Was in die Formeln eingeht (Punktskala, geprueft)

`E_k` und die marginalen Feldwerte sind in ENDWERTUNGS-PUNKTEN skaliert und
benutzen dieselben Konstanten wie die echte Endwertung — 3 (Zeilen) / 7
(Spalten) / 10 (Diagonalen) / 2·n (Joker) / +1 je Randfeld / 3,3,8,8 (Ecken) /
−3 je leerem Spezialfeld (`scoring.rs::expected_plate_points`, Z. 466-533,
gegen `scoring.rs::wertung_progress`, Z. 160-183 — identischer Satz).

Gemessener Nullpunkt derselben Groessen (Champion@400 gegen Heuristik@150,
n=20, **in dieser Sitzung nachgerechnet** mit
`tools/plate_points_from_arena.py aus --praefix platten` auf
`evaluations/paired_arena_env_platten_aus.json`):

| Kriterium | Punkte am Nullpunkt | `tanh(E/50)` |
|---|---:|---:|
| Spezialfelder k6 | **−11,70** | −0,229 |
| Mehrfarbige Felder k3 | +8,67 | +0,171 |
| Eckplatten k5 | +3,00 | +0,060 |
| Vertikale Reihen k1 | +1,05 | +0,021 |
| Horizontale Reihen k0 | +0,50 | +0,010 |
| Diagonale Reihen k2 | 0,00 | 0,000 |
| Farbenreiche Reihen k7 | 0,00 | 0,000 |

(Aeussere Felder k4 kam in diesem Satz nicht vor — k4 und k1 schliessen sich
aus und alle 20 Partien trugen k1. Aus dem Messprotokoll 2026-08-11
**uebernommen, hier nicht nachgerechnet**: k4 ≈ +9,45.)

### par.3.2 Blatt-Pol `MOSAIC_OWNERSHIP_W` — natuerliche Einheit 0,3

Drei Argumente, alle auf dieselbe Groessenordnung:

1. **Klemm-Argument.** Der Shift wird auf einen Blattwert in [0,1] addiert und
   dann geklemmt. Mit hoechstens 3 aktiven Kriterien und den Zahlen aus
   par.3.1 liegt `|SUM_k tanh(E_k/50)|` typisch bei 0,05–0,3. Bei `w_own = 1`
   sind das Shifts bis 0,3 Gewinnwahrscheinlichkeit — die Klemme frisst dann
   die Unterscheidbarkeit der Blaetter.
2. **Praezedenz gleicher Form und gleicher Skala.** Der Heuristik-Pol
   (`MOSAIC_WERTUNG_SHAPING_W`) benutzt dieselbe `tanh(·/50)`-Form mit dem
   Gewicht AUSSEN. Sein Haupt-Sweep begruendete das Raster 0 / 0,1 / 0,3
   woertlich damit, dass ein einzelnes Kriterium mit ~7,9 Punkten schon
   `tanh = 0,156` liefert und "den geklemmten Blattwert saettigt"
   (`PREREG_scoring_plate_injection.md`, Statuskopf).
3. **Gegenzeuge.** `PREREG_placement_side.md` par.11 fuhr die Draftingseite in
   allen Zellen auf `w=1` — ohne Schaden, aber auch ohne Gewinn. Die
   Obergrenze 1,0 ist damit als *gefahren* belegt, nicht als sicher.

→ **Einheit u_D = 0,3.** Raster ein Faktor 3 darunter und darueber: **0,1 /
0,3 / 1,0**.

### par.3.3 Tiling-Pol `MOSAIC_OWNERSHIP_TILING_W` — natuerliche Einheit 1,0

Der Term steht direkt neben `punkte` (Platzierungspunkte des
Tiling-Abschlusses), also in derselben Einheit. Entscheidend ist, wie gross
`SUM_{f neu belegt} wert(f)` gegen die Punktdifferenz zweier Kandidaten ist.

Die Marginale sind **(1−p_f)-gedaempft** — das faellt aus der Definition
`wert(f) = [E_k mit p_f:=1] − E_k` (scoring.rs:567) und ist der Grund, warum
der Term nicht so gross wird, wie die reinen Punktkonstanten nahelegen:

| Kriterium | `wert(f)` | Obergrenze je Feld |
|---|---|---:|
| k4 Randfelder (additiv) | `(1−p_f)·1` fuer die 20 Randfelder, 0 innen | 1,0 |
| k6 Spezialfelder (additiv) | `(1−p_f)·3` je Spezialfeld | 3,0 |
| k1 Spalten | `7·(1−p_f)·PROD(uebrige 5)` | 7,0 |
| k2 Diagonalen | `10·(1−p_f)·PROD(uebrige 5)` | 10,0 |
| k5 Ecken | `pts·(1−p_f)·PROD(uebrige 3)`, `pts` aus 3/3/8/8 | 8,0 |
| k0 Zeilen | `3·(1−p_f)·PROD(uebrige 5)` | 3,0 |
| k3 Joker | `2n·(1−p_f)·PROD(uebrige Joker)` | 2n |
| k7 | 0 (nicht aus ownership ableitbar) | 0 |

Realistisch belegt ein Tiling-Abschluss wenige Felder neu; die konjunktiven
Produkte sind ausser bei fast fertigen Geometrien nahe 0. Der Term wird also
von den beiden ADDITIVEN Kriterien getragen und liegt bei `w_own = 1`
typisch im Bereich einiger weniger Punkte — **dieselbe Groessenordnung wie
die Platzierungspunkt-Differenz zweier Kandidaten** (Bezug: der 5/6→6/6-Schritt
im Heuristik-Pol ist 2,14 Punkte und wurde dort ausdruecklich als "genug, um
einen einzelnen Platzierungspunkt zu ueberstimmen" bewertet,
`tiling_solver.rs`-Doku zu `platten_wert`).

Praezedenz fuer die Spannweite: der Schwester-Regler `MOSAIC_TILING_PLATTEN_W`
(gleicher Additionsplatz, gleiche Einheit) wurde 0,3 / 1 / 3 / 10 gefahren
(`PREREG_placement_side.md` par.11).

→ **Einheit u_T = 1,0.** Raster **0,3 / 1,0 / 3,0**.

### par.3.4 Die drei Dosisstufen (Paare, weil der Hauptarm beide Haelften faehrt)

| Stufe | `MOSAIC_OWNERSHIP_W` | `MOSAIC_OWNERSHIP_TILING_W` | Deutung |
|---|---:|---:|---|
| **N** (Nullarm) | 0 | 0 | derselbe Checkpoint, Verbraucher tot (byte-identisch, Tor B) |
| **D1** Tastdosis | 0,1 | 0,3 | ein Drittel der jeweiligen Einheit — Stichentscheid-Rolle |
| **D2** Einheitsdosis | 0,3 | 1,0 | je Pol genau die hergeleitete natuerliche Einheit |
| **D3** Ueberdosis-Sonde | 1,0 | 3,0 | dreifache Einheit — soll die Obergrenze SEHEN, nicht gewinnen |

Beide Pole bewegen sich innerhalb einer Stufe um denselben Faktor relativ zu
ihrer EIGENEN Einheit. Das ist der Punkt der Paarbildung: eine Stufe ist eine
Dosis, kein Zufallspaar zweier Zahlen.

**Kriteriengewichte bleiben in allen Armen auf Default (alle 1,0).** Eine
Isolierung auf k1/k2/k5 waere ein zweiter Freiheitsgrad und ist ausdruecklich
NICHT Teil dieses Preregs — sie kaeme erst, wenn eine Dosis traegt.

---

## par.4 VERSUCHSPLAN (gestuft, damit die Zellenzahl nicht explodiert)

Gemeinsam fuer alle Stufen: `tools/paired_arena_env_ab.py` mit
`--env-name MOSAIC_OWNERSHIP_W,MOSAIC_OWNERSHIP_TILING_W` (der Orchestrator
setzt komma-getrennt mehrere Env-Vars je Arm, `paired_arena_env_ab.py:91-96`),
Netz@400 gegen **Heuristik@150(dyn)**, `--threads 11` (Sync-Standard seit
`PREREG_gpu_inference_path.md` par.23: 11 Faeden = 528,5 Partien/h gegen 248,5
bei 8), `--block-size 25`, `--log-games` (die Plattenpunkte muessen aus
DENSELBEN Partien kommen wie die Siege).

**Seed-Saetze** (vorab gezogen, `tools/seed_selection_plates.py`, spielt keine
Partie — nur `PyGame`-Konstruktion je Seed):

- Haupt: `evaluations/seed_selection_gate_c_main.json` — **121 Seeds** aus
  [1000,2200), jedes der 8 Kriterien in >= 45 Partien aktiv.
- Replikation: `evaluations/seed_selection_gate_c_repl.json` — **122 Seeds**
  aus [5000,6200), disjunkt zum Hauptsatz, gleiche Abdeckung.

Warum eine ausgewogene Abdeckung und keine fortlaufende Spanne: die
Zielgroesse der Kampagne sind die Plattenpunkte JE KRITERIUM (k1/k2/k5), und
ein Kriterium liegt natuerlicherweise nur in 3/8 der Partien. Die Auswahl
garantiert >= 45 statt zufaellig ~45 und weicht damit kaum von der
natuerlichen Rate (37,5 %) ab — sie wird auf ALLE Arme identisch angewandt,
ist also kein Arm-Effekt.

### Stufe 0 — Kostenprobe und Nicht-Vakuitaets-Schirm (12 Seeds, alle 4 Zellen)

Zweck, vorab und ausschliesslich:
1. Partien/Stunde messen, um n und Laufzeit der Hauptstufe zu belegen statt zu
   schaetzen.
2. Pruefen, dass jede Dosisstufe ueberhaupt WIRKT. Der billigste Test dafuer
   ist die Zahlengleichheit bei gleichen Seeds
   (`PREREG_placement_side.md`: "bei einem Null-Befund zuerst die FORM des
   Eingriffs pruefen, nicht die Dosis").

**Vorab-Regel Stufe 0** (bindend, wird NICHT als Staerkeaussage gelesen —
n=12 traegt keine):
- Sind die 12 Endstaende einer Dosisstufe **exakt gleich** denen des Nullarms,
  ist die Stufe vakuum. Sie wird dann durch das **Dreifache** ihrer Werte
  ersetzt, und die Ersetzung wird hier protokolliert, bevor Stufe 1 startet.
- Bricht D3 den Endstand um mehr als 10 Punkte je Partie ein, wird D3 aus
  Stufe 1 gestrichen (Rechenzeit sparen) und das als "Obergrenze gesehen"
  vermerkt.
- Alles andere aus Stufe 0 ist NICHT auswertbar und wird nicht gedeutet.

### Stufe 1 — HAUPTMESSUNG auf F1 (4 Arme x 121 Seeds = 484 Partien)

Checkpoint `models/alphazero_v21_2d_own_f1.onnx`. Arme: **N, D1, D2, D3**.

**Warum F1 und nicht w1-final als Traeger der Hauptmessung:** F1 ist der
Checkpoint, den wir ohne diesen Versuch ausliefern wuerden (Policy 0,2141 =
unveraendert zum Startpunkt, Tor-A-Kopf 0,780). Sein Nullarm ist damit ein
real interessanter Bezug, nicht nur eine Rechengroesse. w1-final hat den
staerkeren Kopf, aber +41 % Policy-Verlust — eine dort gefundene Dosis waere
mit dem Policy-Defizit vermengt.

### Stufe 2 — Kopf-Traeger (bedingt, 2 Arme x 121 Seeds = 242 Partien)

**Nur wenn Stufe 1 eine Dosis D\* mit Plattenpunkt-Gewinn liefert.**
Checkpoint `models/alphazero_v21_2d_own_w1.onnx`, Arme **N und D\***, DIESELBEN
121 Seeds. Auswertbare Vergleiche danach:
- w1-N gegen F1-N = reiner **Checkpoint-Effekt** (Policy-Verlust gegen
  Kopfguete, ohne Verbraucher),
- w1-D\* gegen w1-N = **Verbraucher-Effekt auf dem starken Kopf**,
- die Differenz der beiden Verbraucher-Effekte = **traegt die Kopfguete?**

### Stufe 3 — REPLIKATION (Pflicht, 2 Arme x 122 frische Seeds = 244 Partien)

Sieger-Arm und SEIN Nullarm auf `seed_selection_gate_c_repl.json`. Kein neuer
Freiheitsgrad, keine neue Dosis. Entscheidung wird **gepoolt** ueber Haupt- und
Replikationssatz getroffen (Lehre aus dem Lambda-Sweep und
`PREREG_ownership_corpus.md` par.17-Analogon: eine einzelne Arena-Marge ist
kein Befund).

### Stufe 4 — Zerlegung (bedingt und nachrangig, 2 Arme)

Nur falls Stufe 1+3 einen tragenden Arm liefern: D\* nur Blatt-Pol
(`w_own, 0`) und D\* nur Tiling-Pol (`0, w_tile`), um zu sehen, welche Haelfte
den Effekt traegt. Beantwortet **nicht** die Hauptfrage und wird nur gefahren,
wenn die Hauptfrage positiv beantwortet ist.

### Stufe 5 — Durchsatz-Nebenmessung (erst bei freier GPU, par.8)

---

## par.5 MESSGROESSEN UND AUSWERTUNG

Primaer (die Zielgroesse der Kampagne):
1. **Plattenpunkte je Kriterium**, insbesondere **k1 (Vertikale Reihen),
   k2 (Diagonale Reihen), k5 (Eckplatten)** — Mittel ueber die Partien, in
   denen die Platte aktiv war.
2. **Plattenpunkte gesamt** (Summe der Endwertung ohne Platzierungspunkte).

Gleichrangig als Waechter (die Nutzer-Zielgroesse "Sieg mit vielen Punkten"):
3. **Siege** gegen Heuristik@150, exakter zweiseitiger McNemar auf den
   diskordanten Paaren.
4. **Endstand-Marge** (Punkte des Netzes).
5. **Strafleiste** (`total_floor` des Netzes).

**Auswertungsebene: BLOCK, nicht Partie.** Stehende Regel seit 2026-08-04
(Paar-SEs auf Partie-Ebene sind massiv unterschaetzt, Extremblock-Artefakte).
Blockgroesse 25 → 5 volle Bloecke je 121-Seed-Arm (letzter Block 21). Der
t-Wert wird ueber die BLOCK-Mittel der gepaarten Differenzen gebildet.
Werkzeug: `tools/plate_points_from_arena.py`, um `--block` erweitert (die
Partie-Ebene bleibt zusaetzlich sichtbar, damit der Unterschied der beiden
Ebenen im Protokoll steht).

McNemar bleibt auf Partie-Ebene — er ist ein exakter Test auf diskordanten
Paaren und kennt kein SE, das die Blockkorrelation unterschaetzen koennte.

---

## par.6 VORAB-ERFOLGSREGEL (woertlich, vor der ersten Partie)

Nutzer-Zielgroesse ist **"Sieg mit vielen Punkten"**. Daraus folgt eine
ZWEISEITIGE Regel, und beide Seiten sind bindend:

> **ERFOLG** heisst: die Plattenpunkte der Zielkriterien (k1/k2/k5) steigen
> gegen den Nullarm desselben Checkpoints — **und** die Siege fallen dabei
> nicht signifikant (McNemar p >= 0,05 zugunsten des Nullarms). Ein
> Plattenpunkt-Gewinn, der signifikant Siege kostet, ist **KEIN Erfolg**.
>
> **UMGEKEHRT** gilt: ein Sieg-Gewinn ohne Plattenpunkt-Gewinn ist **kein
> Beleg fuer den Verbraucher**. Er waere ein interessanter Nebenbefund
> (irgendetwas an der Blatt-/Tiling-Bewertung hat sich verbessert), aber die
> Frage dieses Preregs — traegt der Ownership-Kopf die Wertungsplatten-Agenda
> — bliebe unbeantwortet und muesste so berichtet werden.
>
> **NICHT-ERFOLG** ist alles uebrige, insbesondere: Plattenpunkte flach
> innerhalb der Blockstreuung; oder Endstand-Marge signifikant negativ.

Praezedenzen, an denen genau diese Regel schon einmal entschieden hat und die
sie hier begruenden:
- **k6-Kuppeldraft**: hob Plattenpunkte, kostete Siege → verworfen.
- **Stoerungs-v1** (`PREREG_opponent_disruption.md`): dasselbe Muster.
- **Strafleisten-Gegenterm** (`project_plattenpunkte_aufschluesselung`):
  +1,37 Plattenpunkte gesamt, davon alles aus mehrfarbigen Feldern, vertikale
  Reihen unveraendert — deshalb wird hier JE KRITERIUM entschieden und nicht
  auf der Summe.

**Abbruchregel innerhalb Stufe 1:** faellt ein Arm nach 3 von 5 Bloecken um
mehr als 15 Prozentpunkte Siegquote unter den Nullarm, wird er abgebrochen und
als "Obergrenze gesehen" protokolliert. Die uebrigen Arme laufen weiter.

---

## par.7 WAS DIESES PREREG NICHT BEANTWORTET

- Ob eine **Kriterien-Isolierung** (`MOSAIC_OWNERSHIP_GEW` /
  `MOSAIC_TILING_PLATTEN_GEW` auf nur k1/k2/k5) mehr traegt als die volle
  Maske. Zweiter Freiheitsgrad, eigener Versuch.
- Ob der Verbraucher im **Self-Play** (Korpus-Erzeugung) nuetzt. Das ist eine
  andere Frage mit anderen Kosten (par.8) und braucht erst ein positives
  Tor C.
- Die **Gegner-Haelfte** `[36:72]` (`PREREG_ownership_consumer.md` par.4).
- Ob ein **Mittelweg zwischen F1 und w1-final** (sanftes gemeinsames
  Nachtrainieren, `PREREG_frozen_trunk_head.md` par.7.2) besser waere.
- Die **F2-Deckelsonde** — sie laeuft parallel auf der GPU und ist nicht Teil
  dieses Versuchs.

---

## par.8 NEBENMESSUNG DURCHSATZ (Stufe 5, erst bei freier GPU)

Der Tiling-Pol kostet **einen zusaetzlichen Netz-Vorwaertspass je Tiling-Zug**
auf dem Wurzelzustand (`self_play.rs:1042-1070`; die harte Bedingung "kein
Netz-Aufruf je KANDIDAT" ist eingehalten). Vor irgendeinem 8000er-Self-Play
muss der Preis bekannt sein.

- **Messgroesse**: Partien/Stunde, `MOSAIC_OWNERSHIP_TILING_W = 0` gegen
  `= D*`, sonst identische Konfiguration, 11 Faeden, 40 Partien je Arm
  (dieselbe Groesse wie der Traeger-Sweep in
  `PREREG_gpu_inference_path.md` par.23, damit die Zahlen vergleichbar sind).
- **In SELF-PLAY, nicht in der Arena** (Praezisierung 2026-08-16, noch vor der
  Messung eingetragen): die Entscheidung, die die Zahl tragen soll, ist ein
  8000er-Self-Play. Dort spielen BEIDE Seiten mit Netz, der Zusatzpass faellt
  also doppelt so oft an wie in der Arena (dort hat nur die Netzseite
  `tiling_net: Some(net)`, `self_play.rs::play_net_game`). Eine Arena-Messung
  wuerde den Preis systematisch unterschaetzen. Konfiguration daher wie die
  Korpus-Erzeugung: `self_play.py --mode network --sims 200 --threads 11`
  (`PREREG_ownership_corpus.md` par.7: "Sims 200 fuer die Netz-Arme"), Ablage
  ueber `MOSAIC_DATA_DIR` in ein Wegwerf-Verzeichnis, damit `data/` unberuehrt
  bleibt.
- Der DRITTE Arm ist `MOSAIC_OWNERSHIP_W = D*` **allein** (Tiling-Pol aus).
  Er trennt die beiden Kostenanteile: der Blatt-Pol darf strukturell nichts
  kosten (siehe Vorab-Deutung unten), der Tiling-Pol muss etwas kosten.
- **Bedingung**: **erst wenn die GPU frei ist.** Zum Registrierungszeitpunkt
  laeuft `train.py --name v21_2d_own_f2` (PID 17612, geprueft per
  `Get-CimInstance Win32_Process`) und die Maschine steht bei 100 % CPU-Last
  (6C/12T Ryzen 3600X, geprueft). Eine Durchsatzmessung unter dieser Last
  misst Fremdlast, nicht den Knopf — das ist genau der Fehler, der die
  par.20-22-Zahlen im GPU-Prereg verzerrt hat.
- Die **gepaarten Arena-Stufen 0-4 duerfen** unter der Trainingslast laufen:
  beide Arme sind gleich betroffen, die Paarung haelt. Nur die
  Wandzeit-Aussage haelt nicht.
- **Vorab-Deutung**: der Blatt-Pol kostet strukturell **nichts** (er liest die
  Ownership-Karte des ohnehin laufenden Blatt-Passes). Steigt die Wandzeit
  trotzdem auch bei reinem Blatt-Pol, ist das ein Befund ueber die
  Implementierung, nicht ueber die Kosten des Verfahrens.

---

## par.9 Rohdaten-Ablage

| Datei | Inhalt |
|---|---|
| `evaluations/seed_selection_gate_c_main.json` | Hauptseed-Satz (121) |
| `evaluations/seed_selection_gate_c_repl.json` | Replikationsseed-Satz (122) |
| `evaluations/gate_c_seeds_main.txt` | derselbe Satz zeilenweise fuer `--seeds` |
| `evaluations/gate_c_seeds_repl.txt` | dito |
| `evaluations/paired_arena_env_gate_c_s0.json` | Stufe 0 |
| `evaluations/paired_arena_env_gate_c_f1.json` | Stufe 1 |
| `evaluations/paired_arena_env_gate_c_w1.json` | Stufe 2 |
| `evaluations/paired_arena_env_gate_c_repl.json` | Stufe 3 |

Die `paired_arena_env_*.json` sind **gitignoriert** (`.gitignore:78`, Anlass:
57 Dateien / 43,7 MB in einer Nacht bei 1,8 % verwertbarer Fraktion). Sie
bleiben lokal; die eingedampfte, VERSIONIERTE Form entsteht am Ende ueber
`python -X utf8 tools/arena_compact.py --muster "gate_c_*"` →
`evaluations/arena_compact.jsonl`.

---

## par.10 ERGEBNIS Stufe 0 — beide Vorab-Bedingungen erfuellt, Raster bleibt

Gefahren 2026-08-16, 12 Seeds `900000..900011` (BEWUSST ausserhalb beider
Versuchssaetze, damit Stufe 0 keine Hauptdaten anfasst), F1 @400 gegen
Heuristik@150, 11 Faeden. Roh: `evaluations/paired_arena_env_gate_c_s0.json`.

### Kostenprobe (Punkt 1 der Stufe-0-Regel)

| Arm | Wandzeit 12 Partien | Partien/h |
|---|---:|---:|
| N `0,0` | 50,1 s | 862 |
| D1 `0.1,0.3` | 47,8 s | 904 |
| D2 `0.3,1.0` | 44,9 s | 962 |
| D3 `1.0,3.0` | 48,2 s | 896 |

**≈ 900 Partien/h — und zwar UNTER der laufenden F2-Trainingslast.** Damit
kostet Stufe 1 (484 Partien) rund 32 min, Stufe 2 und Stufe 3 je rund 16 min.
Der Versuchsplan ist damit als Ganzes bezahlbar; eine Verkleinerung von n zur
Kostenersparnis ist nicht noetig und findet nicht statt.

Nebenbemerkung, KEIN Durchsatzbefund: dass D2/D3 hier nicht langsamer sind als
N, ist bei n=12 unter Fremdlast nicht aussagekraeftig. Die Durchsatzfrage
bleibt vollstaendig bei Stufe 5 (par.8).

### Nicht-Vakuitaets-Schirm (Punkt 2 der Stufe-0-Regel)

| Arm | Partien mit IDENTISCHEM Ergebnis zum Nullarm | mittl. Endstand Netz |
|---|---:|---:|
| N `0,0` | 12/12 (per Definition) | 51,67 |
| D1 `0.1,0.3` | **2/12** | 57,92 |
| D2 `0.3,1.0` | **0/12** | 54,25 |
| D3 `1.0,3.0` | **0/12** | 48,25 |

- **Keine Stufe ist vakuum.** Die Ersetzungsregel ("Verdreifachen, falls
  bit-identisch") greift bei keiner Stufe. Das Raster aus par.3.4 bleibt
  unveraendert.
- **D3 bricht nicht ein**: −3,42 Punkte gegen den Nullarm, die Streichgrenze
  lag bei −10. D3 bleibt in Stufe 1.

### Zusatzprobe: beide Pole feuern EINZELN (nicht vorregistriert, nachgetragen)

Anlass: `paired_arena_env_ab.py` verwirft `stderr` der Worker bei Erfolg
(`:133-137` — `proc.stderr` wird nur im Fehlerfall gelesen). Eine Warnung
"Ownership-Kopf unbrauchbar" (`net_mcts::warn_ownership_head_unusable_once`,
`self_play::warne_unbrauchbaren_ownership_kopf_einmal`) waere damit UNSICHTBAR
gewesen, und der Verbraucher haette sich still wie `w=0` verhalten. Deshalb
direkt am Worker nachgeprueft, 4 Seeds, stderr mitgelesen:

| Konfiguration | Warnung auf stderr | Endstaende | identisch zum Nullarm |
|---|---|---|---:|
| `W=0, T=0` (Bezug) | — | 95 / 42 / 48 / 59 | — |
| **nur Blatt** `W=0.3, T=0` | **keine** | 47 / 13 / 34 / 54 | **0/4** |
| **nur Tiling** `W=0, T=1.0` | **keine** | 42 / 38 / 48 / 59 | **2/4** |

Beide Pole sind also einzeln wirksam und der Kopf wird von beiden als
brauchbar erkannt (Breite 140 >= 72). Die Endstaende dieser 4 Seeds werden
NICHT gedeutet — n=4.

**Determinismus-Gegenprobe** (fuer die Paarung tragend): der Nullarm liefert
in einem voellig getrennten Prozess bitgleich dieselben Endstaende wie in
Stufe 0 ([95,33] / [42,30] / [48,18] / [59,27]). Die gepaarte Anlage steht
also nicht auf einer Annahme.

### Was aus Stufe 0 NICHT gelesen wird

Die Siegzahlen (10 / 11 / 10 / 8 von 12) und die Endstands-Differenzen sind
nach der vorab festgelegten Regel **nicht auswertbar** und gehen in kein
Verdikt ein. Sie stehen hier nur, weil sie in der Rohdatei stehen.

## par.11 ERGEBNIS Stufe 1 — NICHT-ERFOLG nach der Vorab-Regel, und zwar deutlich

4 Arme x 121 Seeds = 484 Partien, F1 @400 gegen Heuristik@150, 11 Faeden,
Bloecke a 25. Roh: `evaluations/paired_arena_env_gate_c_f1.json` (gitignoriert,
kompakte Form in `arena_compact.jsonl`). Auswertung
`tools/plate_points_from_arena.py --block 25`.

### par.11.1 Der Waechter: die Siege fallen MONOTON mit der Dosis

| Arm | Siege | McNemar gegen N | ΔMarge (Block, t) | ΔPlatten gesamt (Block, t) |
|---|---:|---:|---:|---:|
| **N** `0,0` | **98/121** (81,0 %) | — | — | — |
| D1 `0.1,0.3` | 89/121 (73,6 %) | b=10 / c=19, **p = 0,136** | −2,27 (t −1,49) | +0,74 (t 2,72) |
| D2 `0.3,1.0` | 86/121 (71,1 %) | b=9 / c=21, **p = 0,043** | −4,60 (t −1,39) | +0,06 (t 0,16) |
| D3 `1.0,3.0` | 84/121 (69,4 %) | b=15 / c=29, **p = 0,049** | −5,53 (t −2,73) | +1,20 (t 4,00) |

**98 → 89 → 86 → 84 ist streng monoton fallend in der Dosis.** Das ist der
tragende Befund, nicht der einzelne p-Wert: drei unabhaengige Dosisstufen
ordnen sich in der Richtung, die die Vorab-Regel als Schaden definiert.

Auf BLOCK-Ebene ist der Verlust kein Extremblock-Artefakt (stehende Regel
2026-08-04) — die gepaarte Sieg-Differenz je Block:

| Arm | B1 | B2 | B3 | B4 | B5 | Summe |
|---|---:|---:|---:|---:|---:|---:|
| D1 | +1 | −4 | 0 | −3 | −3 | −9 |
| D2 | −2 | −4 | −3 | +1 | −4 | −12 |
| D3 | −2 | −7 | 0 | −1 | −4 | −14 |

Je Arm sind **4 von 5 Bloecken negativ**. Die Abbruchregel aus par.6 hat nie
gegriffen (Schwelle bei Block 3 war 50/75; die Arme standen bei 59/75, 53/75,
53/75) — die Arme sind alle vollstaendig gelaufen.

### par.11.2 Die Zielgroesse: k1 und k2 bewegen sich NICHT, k5 nur bei Ueberdosis

Plattenpunkte JE KRITERIUM, gepaart gegen N, Mittel ueber die Partien mit
aktiver Platte (n = 45-47 je Kriterium; t auf Partie-Ebene):

| Kriterium | Nullpunkt N | D1 | D2 | D3 |
|---|---:|---:|---:|---:|
| **k1 Vertikale Reihen** (Zielkriterium) | 1,04 | **+0,00** (t 0,00) | **−0,15** (t −0,30) | **+0,00** (t 0,00) |
| **k2 Diagonale Reihen** (Zielkriterium) | 0,44 | **−0,22** (t −1,00) | **−0,22** (t −0,57) | **−0,44** (t −1,43) |
| **k5 Eckplatten** (Zielkriterium) | 3,07 | +0,00 (t 0,00) | +0,24 (t 1,05) | **+0,96** (t 2,98) |
| k0 Horizontale Reihen | 1,13 | −0,13 | −0,07 | −0,13 |
| k3 Mehrfarbige Felder | 5,17 | +1,30 (t 1,19) | +0,04 | +2,04 (t 1,59) |
| k4 Aeussere Felder | 9,20 | +0,40 (t 1,56) | +0,31 (t 1,42) | +0,51 (t 2,24) |
| k6 Spezialfelder | −11,40 | +0,47 | +0,07 | +0,20 |
| k7 Farbenreiche Reihen | 0,44 | +0,18 | +0,00 | +0,09 |

**Die Zielkriterien der Kampagne bewegen sich nicht.** k1 steht bei allen drei
Dosen exakt auf dem Nullpunkt; k2 geht in ALLEN drei Dosen zurueck, monoton
mit der Dosis. Nur k5 steigt — und nur in der Ueberdosis D3, die 14 Siege
kostet.

**Woher der Plattenpunkt-Gewinn stattdessen kommt**: k3 (Mehrfarbige Felder)
und k4 (Aeussere Felder). Das sind genau die beiden ZAEHL-Kriterien. Der
Vorbehalt aus `project_plattenpunkte_aufschluesselung` ("ein Term, der die
Summe hebt, kann das ueber mehrfarbige Felder tun ... ohne eine einzige Spalte
zu schliessen") trifft hier woertlich zu — deshalb steht in par.6 die Regel,
je Kriterium zu entscheiden und nicht auf der Summe.

**Methodischer Vorbehalt, ehrlich**: die Block-Ebene traegt bei den
Je-Kriterium-Zahlen NICHT. Mit 45 Partien je Kriterium und Blockgroesse 25
bleiben nur 2 Bloecke; die dort ausgewiesenen t-Werte (bis 24,0) sind
Artefakte von n_Block=2 und werden hier nicht verwendet. Die oben genannten
t-Werte sind Partie-Ebene und damit die OPTIMISTISCHE Lesart — sie
unterschaetzen die Streuung, und selbst so bewegt sich k1/k2 nicht.

### par.11.3 Der Mechanismus stimmt, das Ziel nicht

Bemerkenswert und mit der Herleitung in par.3.3 konsistent: **k4 steigt in
allen drei Dosen** (+0,40 / +0,31 / +0,51, monoton in D3). k4 ist genau das
Kriterium mit dem DETERMINISTISCHEN marginalen Feldwert `(1−p_f)·1` je
Randfeld — der Tiling-Pol routet also nachweislich dorthin, wohin die Formel
zeigt. Der Verbraucher ist nicht kaputt; er lenkt auf die Kriterien, deren
Marginale gross und sicher sind (Randfelder, Ecken), und bezahlt das mit
Platzierungspunkten (ΔMarge −2,3 bis −5,5).

Die konjunktiven Zielkriterien k1/k2 bekommen dagegen fast nie ein Signal:
ihr Marginal ist `7·(1−p_f)·PROD(uebrige 5)` bzw. `10·(1−p_f)·PROD(uebrige 5)`
und damit ~0, solange die Spalte/Diagonale nicht fast fertig ist — und
fast-fertige Spalten sind der Zustand, den das Netz laut
`PREREG_placement_side.md` par.9 gerade NICHT erreicht (36 von 57 Partien bei
5/6). **Der Verbraucher kann die Spaltenluecke nicht schliessen, weil sein
Signal erst entsteht, wenn sie fast geschlossen ist.** Das ist eine
Herleitung aus Formel plus Messung, kein separat gemessener Befund.

### par.11.4 Verdikt Stufe 1 nach der Vorab-Regel aus par.6

| Arm | Zielkriterien k1/k2/k5 hoch? | Siege nicht signifikant runter? | **Urteil** |
|---|---|---|---|
| D1 | **nein** (0,00 / −0,22 / 0,00) | ja (p = 0,136) | **NICHT-ERFOLG** |
| D2 | nein | **nein** (p = 0,043) | **NICHT-ERFOLG** |
| D3 | nur k5 (+0,96) | **nein** (p = 0,049) | **NICHT-ERFOLG** — exakt das k6-Kuppeldraft-Muster |

**Kein Arm erfuellt die Vorab-Erfolgsregel.** D3 ist der Praezedenzfall in
Reinform: Plattenpunkte hoch (+1,20 gesamt, k5 +0,96), Siege signifikant
runter. Genau daran sind k6-Kuppeldraft und Stoerungs-v1 gescheitert, und
genau dafuer stand die Regel vorher fest.

## par.12 NACHTRAG zur Bedingung von Stufe 2 (geschrieben VOR dem Lauf)

Stufe 2 war in par.4 an "**nur wenn** Stufe 1 eine Dosis D\* mit
Plattenpunkt-Gewinn liefert" gebunden. Nach par.11.4 ist diese Bedingung
**nicht erfuellt** — nach dem Buchstaben des Preregs waere Stufe 2 gestrichen.

**Sie wird trotzdem gefahren, und zwar als FALSIFIKATIONS-Probe statt als
Sieger-Bestaetigung.** Ehrlich als Abweichung markiert, mit Begruendung und
mit einer Entscheidungsregel, die VOR dem Lauf hier steht:

**Warum die Abweichung vertretbar ist**, und warum sie kein Nachfischen ist:
1. Der Negativbefund aus Stufe 1 ist mit der KOPFGUETE konfundiert. F1 hat
   Feld-AUC **0,780**, w1-final **0,870**, E_k-Spearman k5 0,345 gegen 0,466
   (par.2). Ein Verbraucher, der von einem mittelmaessigen Kopf gesteuert
   wird, kann aus zwei ganz verschiedenen Gruenden schaden.
2. Die Frage ist NICHT neu erfunden: sie steht als Frage (b) in par.1 dieses
   Preregs und als ausdrueckliche Empfehlung in
   `PREREG_frozen_trunk_head.md` par.7.1 ("**BEIDE gehen als Checkpoint-Arme
   in Tor C**"). Sie zu streichen, weil (a) negativ ausfiel, waere die
   Verletzung einer aelteren Festlegung.
3. Stufe 1 HAT einen Effekt gezeigt — einen monoton dosisabhaengigen. Die in
   par.1 genannte Vorbedingung ("erst interessant, wenn (a) ueberhaupt einen
   Effekt zeigt") ist damit im Wortsinn erfuellt; nur ist das Vorzeichen ein
   anderes als erhofft.
4. Kosten: 242 Partien ≈ 16 min (par.10). Der Preis, diese Frage offen zu
   lassen, ist hoeher.

**Arme**: `N = 0,0` und **D1 `0.1,0.3`** auf
`models/alphazero_v21_2d_own_w1.onnx`, dieselben 121 Seeds.
D1, weil es die einzige Dosis ohne signifikanten Sieg-Verlust ist und
weil bei staerkerem Kopf die kleinste Dosis die groesste Chance hat.

**Entscheidungsregel, vorab:**

> **A — Der Kopf war das Problem**: w1-D1 hebt k1/k2/k5 gegen w1-N *und*
> verliert die Siege nicht signifikant (McNemar p >= 0,05). Dann geht
> **w1-D1 in Stufe 3 (Replikation)**, und das Verdikt von Tor C lautet
> "Verbraucher traegt, aber erst ab Kopfguete ~0,87".
>
> **B — Der Verbraucher ist das Problem**: w1-D1 zeigt dasselbe Muster wie
> F1-D1 (k1/k2 flach oder negativ, Siege runter). Dann ist der Negativbefund
> NICHT kopfguetebedingt, **Tor C schliesst negativ**, und Stufe 3/4 entfallen
> — es gibt keinen Sieger zu replizieren.
>
> **C — Uneindeutig** (Zielkriterien hoch, Siege signifikant runter, oder
> umgekehrt): wie B behandeln (kein Erfolg), aber im Verdikt getrennt
> ausweisen.

Als Beifang faellt der **reine Checkpoint-Vergleich w1-N gegen F1-N** an
(gleiche Seeds, Regler beidseitig aus): er beantwortet die in
`PREREG_frozen_trunk_head.md` par.7.1 gestellte Frage, ob der Policy-Verlust
von +41 % oder die Kopfguete von +0,09 AUC in der Arena schwerer wiegt —
unabhaengig vom Verbraucher.

## par.12.1 ERGEBNIS Stufe 2 — AUSGANG B: der Kopf war NICHT das Problem

2 Arme x 121 Seeds = 242 Partien auf `alphazero_v21_2d_own_w1.onnx`
(Feld-AUC 0,870), dieselben Seeds wie Stufe 1. Roh:
`evaluations/paired_arena_env_gate_c_w1.json`.

| Groesse | w1-N `0,0` | w1-D1 `0.1,0.3` | Delta (Block, t) |
|---|---:|---:|---:|
| Siege | 91/121 | **91/121** | b=18 / c=18, **McNemar p = 1,000** |
| Endstand-Marge | 12,29 | 13,31 | +0,77 (t 0,30) |
| Plattenpunkte gesamt | 3,97 | 3,42 | **−0,57 (t −1,09)** |

Je Kriterium, gepaart (Partie-Ebene; Block-Ebene traegt hier nicht, nB=2):

| Kriterium | w1-N | Delta D1 | t |
|---|---:|---:|---:|
| **k1 Vertikale Reihen** | 1,19 | +0,15 | 0,33 |
| **k2 Diagonale Reihen** | 0,00 | +0,22 | 1,00 |
| **k5 Eckplatten** | 3,47 | −0,07 | −0,30 |
| k3 Mehrfarbige Felder | 6,39 | −1,48 | −1,41 |
| k0 Horizontale Reihen | 1,40 | −0,27 | −1,27 |
| k4 Aeussere Felder | 9,38 | −0,11 | −0,35 |
| k6 Spezialfelder | −11,53 | −0,07 | −0,16 |

**Auf dem STARKEN Kopf ist der Verbraucher schlicht wirkungslos.** Die Siege
sind exakt gleich (91:91, b=c=18 — die perfekte Nullverteilung), die
Plattenpunkte gehen leicht ZURUECK, und keines der drei Zielkriterien
bewegt sich ausserhalb des Rauschens.

**Damit greift Ausgang B der Vorab-Regel aus par.12**: der Negativbefund aus
Stufe 1 ist NICHT kopfguetebedingt. Eine Steigerung der Feld-AUC von 0,780 auf
0,870 und des E_k-Spearman k5 von 0,345 auf 0,466 dreht das Vorzeichen nicht —
sie macht den Verbraucher nur harmloser, nicht nuetzlicher. **Tor C schliesst
negativ; Stufe 4 (Zerlegung) entfaellt**, weil es keinen tragenden Effekt zu
zerlegen gibt.

Praezisierung gegenueber dem Wortlaut von Ausgang B: dort stand "k1/k2 flach
oder negativ, **Siege runter**". Die Siege gehen hier NICHT runter, sie stehen
still. Nach par.12 Ausgang C ist das getrennt auszuweisen, und das ist es
hiermit: **auf F1 schadet der Verbraucher, auf w1-final ist er inert.** Beides
ist NICHT-ERFOLG nach par.6, aber es sind zwei verschiedene Befunde und sie
werden nicht zu einem verschmolzen.

### par.12.2 Beifang: der Checkpoint-Vergleich (Antwort auf frozen_trunk par.7.1)

Beide Nullarme, gleiche Seeds, Regler beidseitig aus — der reine
Checkpoint-Vergleich, den `PREREG_frozen_trunk_head.md` par.7.1 von Tor C
verlangt hat:

| | F1 (Policy 0,2141 / AUC 0,780) | w1-final (Policy 0,3018 / AUC 0,870) |
|---|---:|---:|
| Siege | **98/121** | 91/121 |
| Endstand-Marge | **14,57** | 12,29 |
| Plattenpunkte gesamt | 3,45 | 3,97 |

McNemar w1 gegen F1: b=18 / c=25, **p = 0,360** — **kein signifikanter
Unterschied.** F1 fuehrt um 7 Partien und 2,28 Punkte Marge, beides innerhalb
des Rauschens (Marge t −1,05 auf Blockebene).

**Lesart, mit Vorsicht formuliert**: der Kopf-Vorsprung von w1-final zahlt
sich in der Arena NICHT aus, und sein Policy-Verlust von +41 % kostet ihn
auch nicht nachweisbar etwas. Die Frage aus par.7.1 ("was ist die Kombination
aus Kopfguete und Policy-Staerke wirklich wert?") hat damit die Antwort:
**bei dieser Aufloesung nichts von beidem messbar** — und weil F1 den intakten
Policy-Verlust hat und in der Punktschaetzung vorn liegt, bleibt **F1 der
Checkpoint der Wahl**. Das ist eine Praeferenz nach Punktschaetzung plus
Vorsichtsargument, KEIN signifikanter Befund.

## par.13 NACHTRAG Stufe 3: die Replikation bekommt ein neues Ziel (vor dem Lauf)

par.4 machte die Replikation zur Pflicht "fuer den Sieger-Arm". **Es gibt
keinen Sieger.** Die Pflicht faellt damit nach dem Buchstaben weg — aber die
Begruendung dahinter (Lambda-Lehre: eine einzelne Arena-Marge ist kein
Befund) gilt fuer einen Negativbefund genauso.

**Die Replikation wird deshalb umgewidmet, statt gestrichen**, und zielt auf
die eine Zelle, an der das Verdikt noch wackeln koennte:

> **Ziel: F1, Arme N `0,0` und D1 `0.1,0.3`, auf den 122 FRISCHEN Seeds aus
> `evaluations/gate_c_seeds_repl.txt`.**

Warum genau diese Zelle und keine andere:
- D1 ist der **einzige Arm mit unentschiedener Waechter-Lage**: −9 Siege bei
  p = 0,136. D2 und D3 sind bereits signifikant negativ, D3 zusaetzlich durch
  die Monotonie gestuetzt — dort wuerde eine Replikation nichts entscheiden.
- Die tragende NEGATIV-Aussage ("k1 bewegt sich nicht, k2 geht zurueck") steht
  bisher auf EINEM Seed-Satz. Ein Nullbefund auf einem zweiten, disjunkten
  Satz ist die billigste Versicherung gegen ein Seed-Satz-Artefakt.
- Kosten 244 Partien ≈ 16 min.

**Entscheidungsregel, vorab, GEPOOLT ueber beide Seed-Saetze (n = 243):**

> **Der Waechter**: exakter McNemar auf allen 243 gepaarten Partien. Wird
> D1 dort signifikant (p < 0,05) schlechter, gilt: **auch die kleinste Dosis
> kostet Siege**, und Tor C schliesst nicht nur "ohne Nutzen", sondern
> "mit Schaden auf allen Dosen".
> Bleibt es ueber p >= 0,05, lautet der Befund fuer D1 "kein nachweisbarer
> Schaden, aber auch kein Nutzen" — die Monotonie 98/89/86/84 bleibt als
> Indiz bestehen und wird als solches, nicht als Beleg, berichtet.
>
> **Die Zielgroesse**: bleibt k1/k2/k5 auf dem frischen Satz null oder
> negativ, ist der Negativbefund repliziert und Tor C ist geschlossen.
> Sollte D1 dort UNERWARTET k1/k2/k5 signifikant heben, waere das ein
> Widerspruch zum Hauptsatz — dann wird KEIN Erfolg ausgerufen, sondern der
> Widerspruch berichtet und ein dritter Satz gefordert.

## par.13.1 ERGEBNIS Stufe 3 — der Nullbefund repliziert, der Schaden ist nicht belegbar

2 Arme x 122 frische Seeds = 244 Partien, F1, Seeds `5000..5241` (disjunkt zum
Hauptsatz). Roh: `evaluations/paired_arena_env_gate_c_repl.json`.

| Groesse | N `0,0` | D1 `0.1,0.3` | Delta (Block, t) |
|---|---:|---:|---:|
| Siege | 92/122 | 87/122 | b=20 / c=25, **p = 0,552** |
| Endstand-Marge | 11,62 | 10,93 | −0,80 (t −0,45) |
| Plattenpunkte gesamt | 2,57 | 2,81 | +0,20 (t 0,28) |
| k1 Vertikale Reihen | 0,57 | +0,43 | t 1,14 |
| k2 Diagonale Reihen | 0,00 | +0,00 | t 0,00 |
| k5 Eckplatten | 3,27 | +0,18 | t 0,68 |

**Der Plattenpunkt-Gewinn aus dem Hauptsatz repliziert NICHT**: +0,74
(Block-t 2,72) im Hauptsatz gegen +0,20 (Block-t 0,28) hier. Genau dafuer war
die Replikation da — und genau dieser Fall ist eingetreten. Die Sieg-Richtung
repliziert (−5 nach −9), aber wieder ohne Signifikanz.

### par.13.2 GEPOOLTE ENTSCHEIDUNG (n = 243, beide Seed-Saetze, F1, D1 gegen N)

Die vorab festgelegte Entscheidungsebene aus par.13:

| Groesse | Delta (Partie) | t | Delta (Block, nB=10) | t | Urteil |
|---|---:|---:|---:|---:|---|
| **Siege** | b=30 / c=44 | — | — | **McNemar p = 0,130** | kein belegbarer Schaden |
| Endstand-Marge | −1,41 | −1,05 | −1,46 | −1,31 | flach |
| Plattenpunkte gesamt | +0,50 | 1,37 | +0,45 | 1,41 | flach |
| Strafleiste | −0,13 | −0,26 | −0,11 | −0,23 | flach |

Je Kriterium, gepoolt (Partie-Ebene, n je Kriterium 90-96):

| Kriterium | Nullpunkt | Delta D1 | t |
|---|---:|---:|---:|
| **k1 Vertikale Reihen** | +0,80 | +0,22 | 0,73 |
| **k2 Diagonale Reihen** | +0,22 | −0,11 | −1,00 |
| **k5 Eckplatten** | +3,17 | +0,09 | 0,61 |
| k0 Horizontale Reihen | +0,90 | +0,07 | 0,47 |
| k3 Mehrfarbige Felder | +4,86 | +0,44 | 0,57 |
| k4 Aeussere Felder | +9,33 | +0,23 | 1,44 |
| k6 Spezialfelder | −11,64 | **+0,55** | **2,12** |
| k7 Farbenreiche Reihen | +0,62 | −0,18 | −0,94 |

**Nach der Vorab-Regel aus par.13:**
- Der Waechter bleibt ueber p >= 0,05 (0,130). Der Befund fuer D1 lautet
  damit woertlich wie vorab formuliert: **"kein nachweisbarer Schaden, aber
  auch kein Nutzen"**. Die Monotonie 98/89/86/84 aus Stufe 1 bleibt als
  **Indiz** bestehen und wird nicht zum Beleg befoerdert.
- Die Zielgroesse bleibt auf dem frischen Satz null. **Der Negativbefund ist
  repliziert, Tor C ist geschlossen.**

**Der einzige nominal signifikante Einzelwert ist k6 (+0,55, t 2,12) — und
er wird hier NICHT als Befund verkauft.** Er ist einer von acht gleichzeitig
geprueften Kriterien; bei acht Tests ist ein Treffer bei p<0,05 die
Erwartung, nicht die Ausnahme. Interessant ist er trotzdem als Richtungs-
Hinweis, weil k6 dasjenige Kriterium mit dem groessten deterministischen
Marginal ist (`(1−p_f)·3` je Spezialfeld, par.3.3) und mit −11,64 der
groesste Einzelposten im Endstand. Wenn irgendwo eine Fortsetzung ansetzt,
dann dort — mit einer eigenen Vorregistrierung und einer Kriterien-Isolierung
auf k6 statt der vollen Maske.

## par.14 Stufe 5 (Durchsatz) — NICHT GEMESSEN, dafuer strukturell eingegrenzt

**Nicht gefahren, mit zwei Gruenden, beide vorab in par.8 angelegt:**

1. **Die GPU ist nicht frei.** `train.py --name v21_2d_own_f2` laeuft
   durchgehend (PID 17612, zuletzt 27 % GPU-Auslastung, 3075 s CPU-Zeit,
   geprueft per `nvidia-smi` und `Get-CimInstance Win32_Process`). par.8 macht
   die freie Maschine zur Bedingung — eine Messung jetzt waere Fremdlast.
2. **Die Ausloesebedingung ist entfallen.** Der Satz, der die Messung
   motiviert hat, war "bevor jemand damit ein 8000er-Self-Play startet". Nach
   par.15 startet niemand eins. Auf ein leeres Ergebnis eine Stunde
   Maschinenwartezeit zu setzen, waere die falsche Reihenfolge.

**Die Messung bleibt vorregistriert** (par.8, inkl. der Praezisierung
Self-Play statt Arena und des dritten Arms) und ist faellig, sobald der
Verbraucher je wiederbelebt wird.

### par.14.1 Was stattdessen belegt ist: eine OBERE SCHRANKE aus dem Code

Ausdruecklich eine **HERLEITUNG**, keine Wandzeitmessung — die beiden
Eingangszahlen sind aber in dieser Sitzung gemessen bzw. am Code geprueft.

Geprueft am Code:
- Der Zusatzpass faellt **einmal je Tiling-Zug** an, und nur in **Runde 1-4**
  (`self_play.rs::ownership_tiling_marginals`, zwei Kostengates vor dem
  Netz-Aufruf: `w_own == 0` und `platten_branch_applies`).
- **Derselbe Tiling-Zug bezahlt im Bestand schon bis zu
  `MAX_TILING_LEAVES = 400` Vorwaertspaesse** (`tiling_solver.rs:622`), sobald
  der Netz-Stichentscheid aktiv ist — das ist er in Runde 2-4
  (`best_first_step_platten_valued`, `(2..=4).contains(..)`). In Runde 1 ist
  der Bestand dagegen bei 0 Netz-Paessen fuer diesen Zug, dort ist der
  Zusatzpass der ERSTE.

Gemessen in dieser Sitzung, aus den Stufe-1-Partie-Logs (n=121 je Arm):
- **32,5 Drafting-Suchen** des Netzes je Partie (je 400 Sims).
- **17,7 gewertete Tiling-Schritte** des Netzes je Partie (untere Schranke
  fuer die Zahl der `resolve_tiling_step`-Aufrufe — nicht gewertete
  Platzierungen sind darin nicht enthalten).
- Beide Zahlen sind zwischen den Armen praktisch identisch (32,5/32,7/32,9
  und 17,7/17,8/17,6), der Regler aendert die Partiestruktur also nicht.

Rechnung: Zusatzpaesse je Partie ≈ 4/5 x (18 bis 35) ≈ **15 bis 28**.
Netz-Paesse je Partie im Bestand ≈ 32,5 x 400 ≈ **13 000** allein aus dem
Drafting, plus die Kandidaten-Paesse der Tiling-Stichentscheide.

→ **Obere Schranke des Mehraufwands: ~0,25 % der Netz-Vorwaertspaesse je
Partie.** Selbst wenn ein Einzelpass (Batchgroesse 1) fuenfmal ineffizienter
ist als ein Pass im gebatchten Suchlauf, bleibt der Aufschlag unter 2 %.

**Der Blatt-Pol kostet strukturell null zusaetzliche Paesse** — er liest die
Ownership-Karte des ohnehin gerechneten Blatt-Passes
(`net_mcts::apply_ownership_shaping_full`); nur `expected_plate_points` kommt
als reine CPU-Arithmetik dazu.

**Nicht verwendbar** waren die Blockwandzeiten aus Stufe 1 (71-94 s je 25
Partien, ueber alle Arme durchmischt): sie liefen unter der F2-Last, in der
Arena spielt nur EINE Seite mit Netz, und die Partielaenge haengt selbst vom
Arm ab. Drei Konfundierungen auf einmal — sie werden hier bewusst nicht zu
einer Durchsatzaussage verrechnet.

## par.15 VERDIKT: Tor C schliesst NEGATIV

**970 Partien** (Stufe 0: 48, Stufe 1: 484, Stufe 2: 242, Stufe 3: 244),
zwei Checkpoints, drei Dosisstufen, zwei disjunkte Seed-Saetze.

### Die Antwort auf Frage (a): der Verbraucher wirkt, aber nicht auf das Ziel

**Kein Arm auf keinem Checkpoint hebt die Zielkriterien k1/k2/k5.** Gepoolt
ueber 243 Partien auf F1 bei der einzigen unschaedlichen Dosis: k1 +0,22
(t 0,73), k2 −0,11 (t −1,00), k5 +0,09 (t 0,61). Auf w1-final bei derselben
Dosis: k1 +0,15, k2 +0,22, k5 −0,07 — alle im Rauschen.

Was der Verbraucher stattdessen tut, in aufsteigender Dosis:
- **D1** (0,1 / 0,3): nichts Belegbares. Siege gepoolt p = 0,130, Marge und
  Plattenpunkte flach.
- **D2** (0,3 / 1,0): **Siege signifikant runter** (p = 0,043), Plattenpunkte
  unveraendert. Reiner Verlust.
- **D3** (1,0 / 3,0): Plattenpunkte hoch (+1,20 gesamt, k5 +0,96), **Siege
  signifikant runter** (p = 0,049). Das ist exakt das k6-Kuppeldraft-Muster,
  auf das die Vorab-Regel aus par.6 gerichtet war.

### Die Antwort auf Frage (b): nicht der Kopf, der Verbraucher

Der staerkere Kopf (w1-final, Feld-AUC 0,870 gegen 0,780) dreht nichts um: er
macht den Verbraucher **inert** (91:91 Siege, b=c=18) statt nuetzlich. Ausgang
B der Vorab-Regel aus par.12. Eine weitere Kopfverbesserung ist damit **kein
aussichtsreicher Hebel** fuer diesen Verbraucher.

### Warum — die Erklaerung, die der Versuch mitliefert

Der Verbraucher ist nicht defekt. Er lenkt nachweislich dorthin, wohin seine
Formel zeigt: **k4 (Aeussere Felder) steigt in allen drei Dosen** auf F1
(+0,40 / +0,31 / +0,51), und k4 ist genau das Kriterium mit dem
DETERMINISTISCHEN marginalen Feldwert `(1−p_f)·1`. Auch k5 bewegt sich, sobald
die Dosis gross genug ist (+0,96 bei D3).

Die konjunktiven Zielkriterien k1/k2 bekommen dagegen praktisch nie ein
Signal. Ihr Marginal ist `7·(1−p_f)·PROD(uebrige 5)` bzw.
`10·(1−p_f)·PROD(uebrige 5)` — nahe 0, solange die Spalte nicht fast
vollstaendig ist. **Der Verbraucher kann die Spaltenluecke nicht schliessen,
weil sein Signal erst entsteht, wenn sie fast geschlossen ist.** Und genau
"fast geschlossen" ist der Zustand, den das Netz laut
`PREREG_placement_side.md` par.9 nicht erreicht (36 von 57 Partien bei 5/6).
Das ist eine HERLEITUNG aus Formel plus Messung, kein eigener Messbefund —
sie erklaert die Zahlen, sie beweist nicht ihre Ursache.

Damit reiht sich Tor C in denselben Befund ein wie
`PREREG_placement_side.md` par.11: die Spaltenluecke ist **keine
Bewertungsfrage** — weder Drafting-Lenkung noch plattenbewusste Platzierung
noch ein gelernter Ownership-Prior bewegen sie.

### Was das fuer die Kampagne heisst

1. **`MOSAIC_OWNERSHIP_W` und `MOSAIC_OWNERSHIP_TILING_W` bleiben auf Default
   0.** Sie sind gebaut, getestet, dokumentiert und byte-identisch bei 0 —
   sie bleiben als Werkzeug stehen, kommen aber nicht in den Standardpfad.
2. **Kein 8000er-Self-Play mit dem Verbraucher.**
3. **F1 bleibt der Checkpoint** der Ownership-Reihe: nicht signifikant besser
   als w1-final (p = 0,360), aber vorn in der Punktschaetzung (98 gegen 91
   Siege, Marge 14,57 gegen 12,29) UND mit intakter Policy. Damit ist die
   Frage aus `PREREG_frozen_trunk_head.md` par.7.1 beantwortet — mit der
   ehrlichen Einschraenkung, dass die Arena bei n=121 keinen der beiden
   Effekte aufloest.
4. **Der Mittelweg aus `PREREG_frozen_trunk_head.md` par.7.2** (sanftes
   gemeinsames Nachtrainieren) verliert seine Begruendung: er sollte die
   Kopf-Decke heben, und Stufe 2 zeigt, dass eine hoehere Kopfguete nichts
   bringt.
5. **Was offen bleibt und die einzige sichtbare Fortsetzung waere**: k6
   (Spezialfelder). Es ist mit −11,64 der groesste Einzelposten im Endstand,
   hat das groesste deterministische Marginal (`(1−p_f)·3`), und ist der
   einzige gepoolt nominal signifikante Wert (+0,55, t 2,12) — **ausdruecklich
   nicht als Befund verkauft**, weil er einer von acht gleichzeitig
   geprueften Kriterien ist. Eine Fortsetzung muesste die Kriterienmaske auf
   k6 ISOLIEREN (`MOSAIC_OWNERSHIP_GEW` / `MOSAIC_TILING_PLATTEN_GEW`) statt
   die volle Maske zu fahren, und braucht eine eigene Vorregistrierung.

### Was dieses Prereg NICHT sagt

- Nicht, dass der Ownership-Kopf nutzlos ist. Er ist als LERNZIEL
  unangetastet (Tor A: AUC 0,870, `PREREG_ownership_corpus.md` par.10.6) —
  gemessen wurde hier nur seine Tauglichkeit als Laufzeit-STEUERSIGNAL in
  diesen zwei Einspeisungsformen.
- Nicht, dass eine andere Einspeisungsform scheitern muesste. Die
  Injektions-Kampagne hat viermal gezeigt, dass die FORM entscheidet
  (`PREREG_placement_side.md` par.11).
- Nichts ueber Self-Play-Nutzen, Gegner-Haelfte `[36:72]` oder
  Kriterien-Isolierung — alle drei stehen unveraendert in par.7.
