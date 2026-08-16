<!-- STATUS: OFFEN | Frage: Bauen die auf dem Ownership-Korpus trainierten Netze VON SELBST mehr Wertungsplatten als der Champion -- ohne jeden Regler? Und traegt das der Korpus oder der Ownership-Verlust? | Beleg: laeuft (registriert 2026-08-16 vor der ersten Entscheidungspartie) -->

# PREREG: Destillations-Messung — hat der Ownership-Korpus die POLICY geformt?

Stand 2026-08-16. **Registriert VOR der ersten Entscheidungspartie.** Alles,
was noch nicht gemessen ist, steht in Plan-Zeitform; die Ergebnisabschnitte
(ab par.8) sind zum Registrierungszeitpunkt leer.

Anlass: Nutzer-Auftrag nach dem negativen Tor C
(`PREREG_gate_c_consumer_sweep.md`).

---

## par.1 DIE FRAGE, DIE DIE ZWEI-POLE-ARCHITEKTUR TRAEGT

Tor A hat die **Kopf-Guete** gemessen (sagt der Ownership-Kopf die Feldbesitze
vorher?). Tor C hat den **Regler** gemessen (nuetzt es, den Kopf zur Laufzeit
in Blatt- und Tiling-Bewertung einzuspeisen?) — negativ, und zwar monoton
schaedlich: 98 / 89 / 86 / 84 Siege ueber die Dosisstufen, zwei davon
signifikant.

Nie gemessen wurde die dritte Moeglichkeit, und es ist die billigste:
**vielleicht braucht es gar keinen Regler.** Der Korpus enthaelt 3000
Bauer-Partien; wenn die Policy daraus das Planen gelernt hat, spielt das Netz
den Plattenbau von sich aus — bei allen Knoepfen auf Default.

> **Primaerfrage:** Machen die auf `data/ownership_corpus` trainierten
> Checkpoints bei **allen Reglern aus** mehr Plattenpunkte auf den
> Zielkriterien k1/k2/k5 als der Champion, der denselben Korpus nie gesehen
> hat?
>
> **Zerlegungsfrage:** Falls ja — kommt es vom **Korpus** (dann muesste auch
> `w0` mit Ownership-Gewicht 0 es zeigen) oder vom **Ownership-Verlust**
> (dann nur `w1`/`f1`)?
>
> **Sichtbarkeitsfrage** (par.4.2): haengt die Antwort am GEGNER?

Die Diagnose aus Tor C par.11.3 ist der Grund, warum diese Frage nicht schon
beantwortet ist: der Verbraucher **stupst an, er plant nicht**. Sein Signal
(`7·(1−p_f)·PROD(uebrige 5)` fuer k1) ist ~0, solange die Spalte nicht fast
fertig ist. Plattenbau verlangt aber Planung ab Zug 1. Genau das kann eine
Policy koennen und ein Blatt-Shift nicht.

---

## par.2 GEPRUEFT IN DIESER SITZUNG (Ist-Stand mit Pruefstelle)

| Sache | Befund | Pruefstelle |
|---|---|---|
| Champion | `v21_2d_brierbest` | `models/champion.txt` |
| Champion hat den Korpus NIE gesehen | `corpus_composition` = nur `v18`/`v19wdl`/`v19wdlsw`/`v20wdl`/`v20wdlsw`; **kein** `extra_data_dir`, **kein** `v21_own_*`, **kein** `heur_own` | `models/manifest_train_v21_2d_20260809_004805.json` |
| `w0` = Korpus, Ownership-Verlust AUS | `load: v21_2d_brierbest`, `extra_data_dir: data/ownership_corpus`, `ownership_weight: 0.0` | `models/manifest_train_v21_2d_own_w0_20260815_015638.json` |
| `w1` = Korpus, Ownership-Verlust AN | identische Zeile, nur `ownership_weight: 1.0` | `models/manifest_train_v21_2d_own_w1_20260816_005618.json` |
| `f1` = Frozen-Trunk auf `w1_best` | `load: v21_2d_own_w1_best`, `freeze_trunk: true`, `lr 5e-4`, `ownership_weight 1.0` | `models/manifest_train_v21_2d_own_f1_20260816_042601.json` |
| Blatt-Regler Default | `MOSAIC_OWNERSHIP_W`, Default **0,0**, `OnceLock` | `engine/src/net_mcts.rs:1529` |
| Tiling-Regler Default | `MOSAIC_OWNERSHIP_TILING_W`, Default **0,0** | `engine/src/tiling_solver.rs:1014` |
| Partie ist allein durch `game_seed` bestimmt | `play`-Closure zieht `game_seed` aus der Seed-Liste, seedet `StdRng`, zieht daraus die Platten; `num_threads` waehlt nur den rayon-Pool | `engine/src/self_play.rs:2274-2308` |
| Startspieler | `first = i % 2`, `i` = Index INNERHALB des Worker-Aufrufs | `engine/src/self_play.rs:2289` |
| Wertungsplatten je Partie | genau 3, aus 4 paarweise ausschliessenden Paaren | `engine/src/scoring.rs:89` (`sample_valid_scoring_ids`) |
| Ausschluss-Paare | (0,7) (6,3) (4,1) (2,5) — **k2 und k5 kommen NIE zusammen vor**, k1 und k4 auch nicht | `engine/src/scoring.rs:59-65` (`MUTUALLY_EXCLUSIVE_PAIRS`) |
| Heuristik hat einen eigenen Plattenterm | `wertung_progress` | `engine/src/scoring.rs:160` |
| Netz-gegen-Netz kann Seeds und Logs | `net_vs_net_arena_match(..., log_games, seeds)` | `engine/src/lib.rs:268` (Signatur) |
| Durchsatz Netz gegen Heuristik | **2,83 s/Partie** (24 Partien / 67,9 s, 11 Faeden) | Kostenprobe par.6, `evaluations/paired_arena_env_dist_probe.json` |
| Durchsatz Netz gegen Netz | **11,95 s/Partie** (12 Partien / 143,4 s, 11 Faeden) = 4,2x | Kostenprobe par.6, `evaluations/paired_arena_env_dist_nn_probe.json` |

**Ungeprueft / uebernommen:** die Korpus-Zusammensetzung (3000 Bauer-Partien,
Trefferquoten 42 % / 40 % / 55 %) stammt aus `PREREG_ownership_corpus.md` §8
und ist hier nicht nachgerechnet. Die Guete-Zahlen der Checkpoints (policy val,
Feld-AUC) sind aus Tor A/Tor C uebernommen.

---

## par.3 DIE ARME — UND WAS SIE TRENNEN (und was nicht)

| Arm | ONNX | Korpus? | Ownership-Verlust? |
|---|---|---|---|
| **CH** Champion | `alphazero_v21_2d_brierbest.onnx` | nein | — |
| **W0** | `alphazero_v21_2d_own_w0_best.onnx` | **ja** | **0,0** |
| **W1** | `alphazero_v21_2d_own_w1_best.onnx` | **ja** | **1,0** |
| **F1** | `alphazero_v21_2d_own_f1.onnx` | ja (Trunk eingefroren aus `w1_best`) | 1,0 |

Die Zerlegung, die daraus faellt:

- **CH gegen W0** = Wirkung des KORPUS auf die Policy.
- **W0 gegen W1** = Wirkung des OWNERSHIP-VERLUSTS, bei identischem Rezept
  (die beiden Manifeste unterscheiden sich in genau einem Feld,
  `ownership_weight` 0,0 gegen 1,0 — par.2).
- **W1 gegen F1** = Wirkung des Frozen-Trunk-Nachtrainings der Koepfe.

**Der Konfund, ehrlich benannt:** W0/W1/F1 haben gegenueber CH *zwei*
Unterschiede — den Korpus UND 100 weitere Epochen Training. Ein Arm
"Weitertraining OHNE Korpus" existiert nicht und wird hier nicht erzeugt.
Ein CH-gegen-W0-Unterschied ist deshalb **"Korpus oder Weitertraining"**, nicht
"Korpus". Die W0-gegen-W1-Zerlegung ist von diesem Konfund frei, weil beide
Arme dieselbe Epochenzahl auf demselben Korpus haben.

Alle Arme laufen mit **allen Knoepfen auf Default** — `MOSAIC_OWNERSHIP_W` und
`MOSAIC_OWNERSHIP_TILING_W` ungesetzt (Default 0,0, par.2), keine
Bauer-Knoepfe. Es geht ausschliesslich darum, was die trainierten Netze von
sich aus spielen.

---

## par.4 MESSANORDNUNG — ZWEI BLOECKE MIT VERSCHIEDENEN GEGNERN

### par.4.1 Block H — gegen Heuristik@150 (der etablierte Anker)

Netz@400 gegen Heuristik@150(dyn), `--threads 11`, `--block-size 25`,
`--log-games`. Vier Arme, je ein eigener Orchestrator-Lauf mit **identischer
Seed-Liste** (`tools/paired_arena_env_ab.py`, ein einziger Env-Arm `0` = alle
Knoepfe Default). Gepaart ueber den Seed.

### par.4.2 Block N — Korpus-Netz gegen Champion (Nutzer-Einwand 2026-08-16)

**Die Gegnerwahl ist selbst eine Variable.** Der Grund ist die
**Sichtbarkeit des Effekts im Ergebnis, NICHT Ressourcenkonkurrenz.**

Das ist die Stelle, an der eine erste, falsche Begruendung ausdruecklich
ERSETZT und nicht ergaenzt wird — sie lautete "gegen die Heuristik sind die
Platten umkaempft, wer eine Spalte baut, streitet mit dem Gegner um dieselben
Farben". Das ist falsch: jeder Spieler hat seine EIGENE Kuppel mit eigenen
Kuppelplatten, individuell aus der Auslage gezogen, Position und Rotation frei
(`docs/engine_manual.md:40-42`, `:65`, `:80`). Welche Farben eine Spalte
verlangt, bestimmt also das individuelle Plattenlayout; die Farbanforderungen
beider Spieler sind verschieden. Geteilt sind die KRITERIEN, nicht die Farben.
Gegenzeuge gegen ein Nachschub-Argument: "Farbe nie verfuegbar, waehrend Zeile
offen" wurde mit **0 %** gemessen (`PREREG_provocation.md:815`) — Farbknappheit
ist in diesem Spiel nicht der Engpass.

Der richtige Grund, **in dieser Sitzung nachgemessen** (gate-C-Rohlogs, F1-Arm
bei Reglern aus, n=121, `tools/plate_points_from_arena.py` mit der neuen
Seiten-Wahl `@1`):

| | F1 (Netz) | Heuristik | k1 | k5 | k6 |
|---|---:|---:|---:|---:|---:|
| Plattenpunkte gesamt | 3,45 | **2,72** | 1,04 / **1,04** | 3,07 / **3,82** | −11,40 / **−12,07** |

Die Heuristik sammelt also praktisch **dieselben** Plattenpunkte wie das Netz
— auf k1 exakt gleich viel, auf k5 sogar mehr. Der Plattenkanal ist gegen sie
weitgehend **symmetrisch** und entscheidet deshalb wenig: was das Netz an
Platten gewinnt, gewinnt die Heuristik in aehnlicher Hoehe auch, der
Punkte-VORSPRUNG bleibt klein. Der Champion dagegen ignoriert die Platten;
gegen ihn schlaegt jeder Plattenpunkt voll auf die Differenz durch.

Aufbau: beide Netze @400, alle Regler aus, **Brett-Tausch je Seed** (zwei
Laeufe mit vertauschten Modellen bei identischer Seed-Liste und identischem
`--block-size`; da `first = i % 2` nur vom Index im Block abhaengt, startet je
Seed in Lauf 1 die eine und in Lauf 2 die andere Seite — das
`paired_gating.py`-Muster, hier ohne SPRT und ohne Auto-Promotion, weil die
Stichprobe fest ist). **Plattenpunkte BEIDER Seiten** werden getrennt
ausgewiesen.

Paarungen: **F1 gegen CH** (der Checkpoint, den wir ohne diesen Versuch
ausliefern wuerden — Tor C par.4) und **W1 gegen CH**. Vorab festgelegt, nicht
nach Block H ausgewaehlt.

**W0 gegen CH** ist ein optionaler dritter Lauf (par.7) und wird nur gefahren,
wenn Block H und die beiden ersten Paarungen durch sind.

### par.4.3 Werkzeuge — was erweitert wurde statt neu gebaut

- `tools/paired_arena_arm_worker.py`: `--model-b`/`--sims-b` schalten auf
  `net_vs_net_arena_match`. Ohne die Schalter byte-identisches
  Bestandsverhalten. Kein zweiter Worker, weil Seed-Liste, Block-Schnitt,
  `--log-games` und Ausgabeformat bei beiden Arena-Funktionen identisch sind.
- `tools/paired_arena_env_ab.py`: reicht beide Schalter durch.
- `tools/plate_points_from_arena.py`: Token-Form `kuerzel[#arm][@seite]`;
  `@0`/`@1` erzwingt den BRETT-Index statt der Namensregel. Ohne `@` unveraendert.
  (Die Namensregel liefert bei "NetzA"/"NetzB" immer Brett 0 — die Gegenseite
  waere sonst unsichtbar, und genau die ist hier die Frage.)

---

## par.5 STICHPROBEN-HERLEITUNG (aus vorhandenen Zahlen, nicht geraten)

**Quelle der Streuung:** Tor C hat zwei VERSCHIEDENE Modelle (F1 und w1-final)
bei Reglern aus auf DEMSELBEN 121-Seed-Satz gespielt. Deren gepaarte Differenz
ist genau die Groesse, die hier zu messen ist — eine echte
Zwischen-Modell-Paardifferenz, keine Ersatzgroesse.

Gerechnet aus `paired_arena_env_gate_c_f1.json#0,0` gegen
`paired_arena_env_gate_c_w1.json#0,0`:

| Groesse | n | SD der Paardifferenz | Korrelation der Arme |
|---|---:|---:|---:|
| k1 Vertikale Reihen | 47 | **3,718** | −0,03 |
| k2 Diagonale Reihen | 45 | **2,084** | (Arm konstant) |
| k5 Eckplatten | 45 | **1,372** | −0,04 |
| Plattenpunkte gesamt | 121 | 6,425 | +0,81 |
| Endstand-Marge | 121 | 24,616 | +0,10 |
| Siege (diskordante Paare) | 121 | b=18 / c=25 → Rate **0,355** | — |

Bemerkenswert und wichtig fuer die Rechnung: **je Kriterium bringt die
Seed-Paarung fast nichts** (Korrelation ≈ 0). Auf der Summe dagegen viel
(+0,81). Die Stichprobe muss sich also am ungepaarten Fall je Kriterium
orientieren.

**Zieleffekt, begruendet statt gesetzt:** eine geschlossene Spalte ist 7
Punkte wert, eine Diagonale 10, eine Eckplatte 3 bzw. 8
(`PREREG_gate_c_consumer_sweep.md` par.3.1). Ein Zuwachs von **+1,0
Plattenpunkt je Kriterien-Partie** heisst also: **eine zusaetzlich
geschlossene Spalte in jeder 7. Partie**. Weniger als das waere kein
Destillations-Befund, sondern Rauschen mit Vorzeichen; der Nullpunkt selbst
liegt bei k1 auf 1,04.

**Noetige Stichprobe** (80 % Macht, alpha 0,05 zweiseitig, `n = 7,849·SD²/d²`):

| Kriterium | n fuer d=1,0 |
|---|---:|
| k1 | **109** Kriterien-Partien |
| k2 | 35 |
| k5 | 15 |

**k1 bestimmt die Stichprobe: 109.** Gewaehlt werden **150** Kriterien-Partien
— nicht aus Vorsicht, sondern weil die Entscheidungsebene die BLOCK-Ebene ist
(stehende Regel seit 2026-08-04): 150 / 25 = **6 Bloecke je Kriterium**. Tor C
hatte dort 2 und musste die Block-Ebene je Kriterium ausdruecklich fuer
untragbar erklaeren (par.11.2). Das wird hier nicht wiederholt.

**Seed-Satz:** `tools/seed_selection_plates.py --seed-start 1000 --seed-count
4000 --pro-kriterium 150` → **407 Seeds**, jedes der 8 Kriterien in >= 150
Partien aktiv (`evaluations/seed_selection_distillation_main.json`,
`evaluations/distillation_seeds_main.txt`). Der gate-C-Hauptsatz ist als MENGE
darin enthalten; die ersten 99 Seeds stehen in identischer Reihenfolge, danach
weicht die Greedy-Auswahl ab.

**Damit aufloesbar** (80 % Macht):

| Groesse | n | aufloesbares d |
|---|---:|---:|
| k1 | 150 | **0,85** |
| k2 | 150 | 0,48 |
| k5 | 150 | 0,31 |
| Plattenpunkte gesamt | 407 | 0,89 |
| Endstand-Marge | 407 | 3,42 Punkte |
| Siege (McNemar) | 407 | ca. **8,3 Prozentpunkte** |

Block N: **200 Seeds** je Paarung, mal 2 Brett-Orientierungen = 400 Partien →
ca. 148 Kriterien-Partien, also dieselbe Aufloesung wie Block H. Die
Reduktion von 407 auf 200 ist eine reine Kostenentscheidung (Netz gegen Netz
kostet 4,2x, par.2); sie ist hier als solche benannt und wird nicht als
Methodik verkauft.

**Laufzeit-Voranschlag** (aus den gemessenen Durchsaetzen, par.2):
Block H 4 x 407 x 2,83 s ≈ **77 min**; Block N 2 x 2 x 200 x 11,95 s ≈
**2,7 h**.

---

## par.6 KOSTENPROBEN (bereits gelaufen, KEINE Entscheidungsdaten)

Zwei kleine Laeufe VOR dieser Registrierung, ausschliesslich um den Durchsatz
zu messen und die Werkzeugkette zu pruefen — nach dem Stufe-0-Muster von Tor C.
Sie werden **nicht** als Staerke- oder Plattenaussage gelesen und gehen in
keine Auswertung ein:

- `dist_probe`: CH gegen Heuristik, 24 Seeds → 2,83 s/Partie.
- `dist_nn_probe`: F1 gegen CH, 12 Seeds → 11,95 s/Partie; bestaetigt, dass die
  Seiten-Wahl `@0`/`@1` beide Bretter getrennt ausweist.

---

## par.7 VORAB-ERFOLGSREGEL (woertlich, vor der ersten Entscheidungspartie)

Nutzer-Zielgroesse bleibt **"Sieg mit vielen Punkten"**. Die Regel ist
zweiseitig, und beide Seiten sind bindend.

> **DESTILLATION HAT GEGRIFFEN** heisst: ein Korpus-Arm hebt die
> Zielkriterien **k1/k2/k5** signifikant gegen den Champion (Block-Ebene,
> Blockgroesse 25) — **und** verliert dabei keine Siege signifikant
> (exakter zweiseitiger McNemar, p >= 0,05 zugunsten des Champions).
>
> **Ein Plattenzuwachs, der Siege kostet, ist KEIN Erfolg.** Das ist zum
> vierten Mal dieselbe Regel und zum vierten Mal aus demselben Grund:
> k6-Kuppeldraft, Stoerungs-v1 und Tor C D2/D3 haben alle drei Platten
> gehoben und Siege bezahlt.

**Ausgang 2 — DESTILLATION IST AUSGEBLIEBEN.** Kommen die Korpus-Netze auf
DIESELBEN Plattenpunkte wie der Champion (Differenz innerhalb der in par.5
ausgewiesenen Aufloesung), dann hat der Korpus **nur den Kopf gefuettert,
nicht die Policy**. Das ist ausdruecklich ein **tragender Befund fuer die
Architektur**, kein Nullergebnis: zusammen mit dem negativen Tor C hiesse es,
dass die Zwei-Pole-Architektur den Plattenbau auf KEINEM ihrer beiden Wege in
das Spiel bekommt — weder ueber den Regler noch ueber die Destillation. So
wird es dann auch berichtet.

**Ausgang 3 — SIEGE OHNE PLATTEN.** Gewinnt ein Korpus-Arm signifikant mehr,
ohne die Zielkriterien zu heben, ist das **kein Beleg fuer die
Plattenagenda**. Es waere ein Staerkebefund (und, falls er gegen den Champion
haelt, ein Gating-Kandidat), aber die Frage dieses Preregs bliebe unbeantwortet
und muesste so berichtet werden.

**Ausgang 4 — DER EFFEKT HAENGT AM GEGNER** (vorab benannt, damit er nicht
hinterher erklaert wird). Zeigt sich ein Plattenvorteil **nur gegen den
Champion und nicht gegen die Heuristik**, heisst das **NICHT** "Platten sind
gegen starke Gegner wertlos". Es heisst: gegen einen plattenbewussten Gegner
ist der Plattenkanal weitgehend **symmetrisch** und entscheidet deshalb wenig
— gegen einen plattenblinden ist er ein echter Netto-Vorteil. Das ist ein
Befund ueber die **MESSANORDNUNG**, nicht ueber die Spielstaerke. Die
Nachmessung in par.4.2 (Heuristik 2,72 gegen Netz 3,45 Plattenpunkte) ist der
Grund, warum dieser Ausgang vorab dasteht.

**Auswertungsebene: BLOCK, nicht Partie** (stehende Regel seit 2026-08-04).
Blockgroesse 25. Die Partie-Ebene wird zusaetzlich ausgewiesen, damit der
Unterschied der beiden Ebenen im Protokoll steht. McNemar bleibt auf
Partie-Ebene (exakter Test auf diskordanten Paaren, kein SE, das die
Blockkorrelation unterschaetzen koennte).

**Kein Nachziehen der Stichprobe.** n steht in par.5 und wird nicht erhoeht,
weil ein Ergebnis knapp verfehlt wird.

---

## par.8 ERGEBNIS BLOCK H (leer bei Registrierung)

## par.9 ERGEBNIS BLOCK N (leer bei Registrierung)

## par.10 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)
