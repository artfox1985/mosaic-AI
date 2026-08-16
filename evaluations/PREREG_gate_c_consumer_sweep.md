<!-- STATUS: OFFEN | Frage: Tor C -- traegt der Ownership-Verbraucher (Blatt-Pol MOSAIC_OWNERSHIP_W + Tiling-Pol MOSAIC_OWNERSHIP_TILING_W, gemeinsam gefahren) in der Arena Plattenpunkte ein, OHNE Siege zu kosten -- und welcher Kopf (F1 eingefroren vs w1-final) traegt ihn? | Beleg: **OFFEN, vorregistriert 2026-08-16.** Nichts gefahren zum Zeitpunkt der Registrierung. Nullarm ist DERSELBE Checkpoint mit Regler 0, nicht der Champion. Drei Dosisstufen als Paare (0,1/0,3 -- 0,3/1,0 -- 1,0/3,0), hergeleitet aus den Punktskalen beider Formeln (par.3). Vorab-Erfolgsregel: Plattenpunkt-Gewinn OHNE signifikanten Sieg-Verlust; Praezedenz k6-Kuppeldraft und Stoerungs-v1. -->

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

## par.11 ERGEBNIS Stufe 1

*(leer zum Registrierungszeitpunkt)*

## par.12 ERGEBNIS Stufe 2

*(leer zum Registrierungszeitpunkt)*

## par.13 ERGEBNIS Stufe 3 (Replikation)

*(leer zum Registrierungszeitpunkt)*

## par.14 ERGEBNIS Stufe 5 (Durchsatz)

*(leer zum Registrierungszeitpunkt)*

## par.15 VERDIKT

*(leer zum Registrierungszeitpunkt)*
