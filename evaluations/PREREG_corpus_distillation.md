<!-- STATUS: UEBERHOLT | Frage: Bauen die auf dem Ownership-Korpus trainierten Netze VON SELBST mehr Wertungsplatten als der Champion? | Beleg: **MESSUNG HINFAELLIG, 2026-08-16 (par.10.4)**: der Policy-Kopf hat den Korpus NIE gesehen. Unter BEIDEN Traeger-Manifesten (policy_carrier_manifest_v20/_v21) sind alle Korpusdateien policy-MASKIERT -- sie beginnen nicht mit WDL_GENERATOR_PREFIXES und sind nicht namentlich gelistet (neural_net.py:679/:667, mit der Funktion selbst nachgerechnet). "Ausgang 2 -- Destillation ausgeblieben" ist damit die mechanische Folge eines Filters, kein Befund ueber Destillation. GUELTIG BLEIBEN: das direkte Duell w0_best 43:57 gegen den Champion (par.10.3, reine Spielstaerke) und die Block-H-Rohzahlen (par.8.4) -- deren Unterschiede entstanden ueber Value-Kopf und Trunk-Drift, nicht ueber die Policy. Lehre: der Traeger-Status jeder neuen Korpus-Quelle gehoert in die Ist-Stand-Tabelle jeder Prereg mit Policy-Aussage. -->

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
| Durchsatz Netz gegen Heuristik | **2,83 s/Partie** (24 Partien / 67,9 s, 11 Faeden) | Kostenprobe par.6, `evaluations/artifacts/paired_arena_env_dist_probe.json` |
| Durchsatz Netz gegen Netz | **11,95 s/Partie** (12 Partien / 143,4 s, 11 Faeden) = 4,2x | Kostenprobe par.6, `evaluations/artifacts/paired_arena_env_dist_nn_probe.json` |

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
Partien aktiv (`evaluations/artifacts/seed_selection_distillation_main.json`,
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

## par.7a NACHTRAG 2026-08-16, 14:00 — ABWEICHUNG VON par.4.1 (Koordinator)

Der erste Messlauf ist an der Dimensionierung gescheitert: von vier H-Armen
lief nur der Champion-Arm, Block N gar nicht. Beim Neuansatz faellt auf, dass
**zwei der vier Arme bereits gespielt sind**. Geprueft, nicht angenommen:

| Datei | Modell | n | Bedingungen | Seeds im 407er-Satz |
|---|---|---:|---|---:|
| `paired_arena_env_gate_c_f1.json#0,0` | `own_f1` | 121 | net 400 / heur 150 / Regler 0 | **121 von 121** |
| `paired_arena_env_gate_c_w1.json#0,0` | `own_w1` (final) | 121 | net 400 / heur 150 / Regler 0 | **121 von 121** |

Diese beiden Arme werden **wiederverwendet statt nachgespielt**.

**Der Preis dafuer steht hier und wird nicht weggelassen: diese zwei Arme sind
NICHT blind.** Ihre Siegquote (F1: 98/121) und ihre Plattenpunkte (3,45) waren
bekannt, als die Wiederverwendung entschieden wurde. Daraus folgt bindend:

1. **Der tragende Vergleich sind die drei BLINDEN Arme** — `champion`,
   `w0_best`, `w1_best`, je n=407, identische Seed-Liste, alle drei zum
   Zeitpunkt dieses Nachtrags ungemessen. Nur sie koennen das Verdikt in
   par.10 begruenden.
2. `f1` und `w1`-final gehen als **Zusatzarme bei n=121** ein und duerfen
   einen Ausgang stuetzen, aber keinen tragen.
3. Die saubere Ein-Faktor-Zerlegung bleibt **`w0_best` gegen `w1_best`**
   (Manifeste unterscheiden sich allein im `ownership_weight` 0,0 / 1,0).
   `champion` gegen `w0_best` bleibt doppeldeutig (Korpus ODER
   Weitertraining) — der fehlende Kontrollarm "Weitertraining ohne Korpus"
   ist ein GPU-Lauf und in der Warteschlange, nicht in dieser Messung.

**Die beiden Kostenproben aus par.6 tragen weiterhin nichts** — hier
nachgerechnet, damit die Zahlen nicht als Vorbefund weiterwandern:

- Champion 14/24 gegen F1 19/24 auf **identischen** Seeds und identischem
  Anziehenden: diskordant 8 zu 3, **exakter McNemar p = 0,227**. Kein Befund.
- Netz gegen Netz F1-gegen-Champion 4:8 bei n=12, Anziehende sauber 6/6
  verteilt: ebenfalls kein Befund — und die Richtung ist der Heuristik-Probe
  **entgegengesetzt**. Genau deshalb entscheidet keine von beiden.

## par.8 ERGEBNIS BLOCK H — 2 von 4 Armen (Lauf abgebrochen)

**Was gelaufen ist:** `champion` und `w0_best`, je 407 Partien. Der `w1_best`-Arm
starb mitten im Lauf (keine Datei — der Orchestrator schreibt erst nach dem
letzten Block), `f1` wurde nie gestartet. **Damit gibt es genau EINE der drei
registrierten Paarungen.** Rohdaten: `evaluations/artifacts/paired_arena_env_dist_h_ch.json`,
`..._dist_h_w0.json` (je ~10 MB, per `.gitignore:78` nicht versioniert);
Kennzahlen versioniert in `evaluations/artifacts/distillation_block_h_partial.json`.

### par.8.1 Absolut (Block-Mittel; der Restblock von 7 Partien faellt nach der Blockregel raus)

| | Champion | W0_best |
|---|---:|---:|
| Siege / n | 296/407 | **333/407** |
| Plattenpunkte gesamt (Block-SE) | 2,420 (0,566) | 3,40 |
| k1 Vertikale Reihen (n=156) | 0,653 (0,225) | 0,90 |
| k2 Diagonale Reihen (n=150) | 0,067 (0,067) | 0,27 |
| k5 Eckplatten (n=150) | 3,253 (0,113) | 3,37 |

### par.8.2 Registrierte Paarung W0 gegen Champion (n=407, gepaart, Block-Ebene)

| Groesse | Delta | t(Block) | p(Block) | nB |
|---|---:|---:|---:|---:|
| Siege 333:296 | b=85 / c=48 | — | **McNemar 0,0017** | — |
| Plattenpunkte gesamt | +0,99 | 2,91 | **0,011** | 16 |
| Endstand-Marge | +4,73 | 4,60 | **0,000** | 16 |
| Strafleiste | −1,62 | −3,09 | **0,007** | 16 |
| **ZIEL k1 Vertikale Reihen** | +0,27 | 0,94 | 0,391 | 6 |
| **ZIEL k2 Diagonale Reihen** | +0,20 | 1,17 | 0,296 | 6 |
| **ZIEL k5 Eckplatten** | +0,11 | 0,62 | 0,564 | 6 |
| k0 Horizontale Reihen | +0,04 | 0,25 | 0,813 | 6 |
| k3 Mehrfarbige Felder | +1,99 | 3,27 | 0,022 | 6 |
| k4 Aeussere Felder | +0,06 | 0,17 | 0,873 | 6 |
| k6 Spezialfelder | −0,12 | −0,67 | 0,530 | 6 |
| k7 Farbenreiche Reihen | +0,08 | 0,75 | 0,490 | 6 |

Die 6 Bloecke je Kriterium sind erreicht — der Zweck der Stichprobe aus par.5
ist eingeloest, die Je-Kriterium-Zahlen stehen hier auf der Block-Ebene und
nicht wie in Tor C auf einer nicht tragenden nB=2.

### par.8.3 Zwei Einordnungen, die das Bild sonst verzerren

1. **Der Plattenzuwachs kommt aus dem ZAEHL-Kriterium.** k3 (+1,99) traegt ihn
   praktisch allein; die konjunktiven Zielkriterien k1/k2 bewegen sich nicht.
   Das ist woertlich das Muster aus Tor C par.11.2 — dort stiegen ebenfalls k3
   und k4, und k1/k2 nicht. Der Vorbehalt aus
   `project_plattenpunkte_aufschluesselung` ("ein Term, der die Summe hebt,
   kann das ueber mehrfarbige Felder tun, ohne eine einzige Spalte zu
   schliessen") trifft erneut zu.
2. **k3 ist eines von 8 getesteten Kriterien.** p=0,022 haelt einer
   Bonferroni-Schranke (0,05/8 = 0,00625) **nicht** stand. Eine Korrektur war
   nicht vorregistriert, deshalb steht hier der Nominalwert — aber er traegt
   keine Einzelaussage.

### par.8.4 NACHTRAG 2026-08-16, 15:20 — die fehlenden Arme sind nachgeholt

Der Koordinator hat `w1_best` und `f1` auf **demselben 407-Seed-Satz** mit
demselben Aufruf nachgezogen (14:37–15:20). Block H ist damit **vollstaendig**;
alle vier Arme sind ueber den Seed gepaart, der Anziehende ist je Seed in allen
Armen identisch (geprueft, nicht angenommen).

| Arm | Siege | Marge | Platten | Boden | k1 | k2 | k5 | k3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CH | 296/407 | 11,26 | 2,42 | 10,49 | 0,63 | 0,07 | 3,25 | 3,50 |
| **W0** | **333/407** | **15,99** | **3,40** | **8,87** | 0,90 | 0,27 | 3,37 | 5,49 |
| W1 | 321/407 | 13,89 | 2,84 | 9,89 | 0,85 | 0,20 | 3,33 | 4,13 |
| F1 | 321/407 | — | — | — | — | — | — | — |

**Paarungen (exakter McNemar, n=407):**

| Paarung | nur A | nur B | p |
|---|---:|---:|---:|
| W0 gegen CH | 85 | 48 | **0,0017** |
| W1 gegen CH | 75 | 50 | **0,0314** |
| F1 gegen CH | 75 | 50 | **0,0314** |
| **W1 gegen W0** | 48 | 60 | 0,2898 |
| **F1 gegen W1** | **0** | **0** | 1,0000 |

**F1 und W1 spielen auf allen 407 Seeds Zug fuer Zug gleich — null diskordante
Paare.** Das ist keine Messung, sondern eine Tautologie mit Beleg-Wert: F1 hat
nur den Ownership-Kopf trainiert, und bei `MOSAIC_OWNERSHIP_W=0` wird der nie
gelesen. Der BatchNorm-Riegel aus `PREREG_frozen_trunk_head.md` (ohne den das
Einfrieren still falsch gewesen waere) ist damit **live in der Arena
bestaetigt**, nicht nur im Selbsttest.

**W1 gegen CH je Kriterium** (Block-Ebene, nB=6): k1 +0,19 (t 0,55) · k2 +0,13
(t 1,58) · k5 +0,07 (t 0,40) · k3 +0,57 (t 1,00) · k7 +0,21 (t 1,58) · uebrige
|t| < 1,2. **Kein Kriterium signifikant, alle drei Zielkriterien wieder
innerhalb der Aufloesung.** Block-Ebene gesamt: Marge +2,79 (t 2,22), Platten
+0,38 (t 1,40), Boden −0,55 (t −1,06).

## par.9 ERGEBNIS BLOCK N — NICHT GELAUFEN

Kein einziger Lauf. Die CPU war durchgehend von Block H belegt (6 Kerne / 12
logisch, 11 Faeden, 100 % Last, dazu das parallele F2-Training). Die in par.4.2
begruendete Frage — ob der Plattenvorteil gegen den plattenblinden Champion
sichtbar wird, wo er gegen die Heuristik im symmetrischen Kanal verschwindet —
ist damit **unbeantwortet**. Ausgang 4 konnte nicht geprueft werden.

## par.10 VERDIKT NACH DER VORAB-REGEL

Angewandt wird die Regel aus par.7 in ihrem Wortlaut vor der ersten
Entscheidungspartie, auf die eine gemessene Paarung.

**Verhaeltnis zu par.7a:** dort ist festgelegt, dass nur die drei BLINDEN Arme
(`champion`, `w0_best`, `w1_best`) ein Verdikt tragen duerfen. Das ist hier
eingehalten — beide hier ausgewerteten Arme waren zum Zeitpunkt ihres Laufs
ungemessen. Es fehlt der dritte: `w1_best`. Damit fehlt genau die
Ein-Faktor-Zerlegung aus par.7a Punkt 3 (`w0_best` gegen `w1_best`), und das
Verdikt unten steht auf zwei statt drei blinden Armen. Die Zusatzarme `f1` und
`w1`-final aus par.7a sind hier NICHT verrechnet.

**Ausgang 1 (DESTILLATION HAT GEGRIFFEN) — greift NICHT.** Er verlangt einen
signifikanten Zuwachs auf k1/k2/k5. Keines der drei ist signifikant.

**Ausgang 2 (DESTILLATION IST AUSGEBLIEBEN) — GREIFT.** Die Regel verlangt,
dass die Differenz innerhalb der in par.5 ausgewiesenen Aufloesung liegt.
Vorab ausgewiesen: k1 0,85 / k2 0,48 / k5 0,31. Gemessen: +0,27 / +0,20 /
+0,11 — **alle drei innerhalb**. Der Korpus hat auf den Zielkriterien nichts
in die Policy destilliert. Nach par.7 ist das ausdruecklich ein tragender
Architektur-Befund: zusammen mit dem negativen Tor C bekommt die
Zwei-Pole-Architektur den Plattenbau auf KEINEM ihrer beiden Wege in das
Spiel — weder ueber den Regler noch ueber die Destillation.
**Einschraenkung:** belegt ist das fuer W0. Fuer w1_best und f1 fehlt die
Messung; es bleibt moeglich, dass der Ownership-VERLUST (den W0 nicht hat)
die Zielkriterien bewegt.

**Ausgang 3 (SIEGE OHNE PLATTEN) — GREIFT EBENFALLS.** W0 gewinnt signifikant
mehr (333:296, McNemar p=0,0017), bei +4,73 Marge und −1,62 Strafleiste, ohne
die Zielkriterien zu heben. Par.7 dazu woertlich: **kein Beleg fuer die
Plattenagenda**, aber ein Staerkebefund und ein Gating-Kandidat. Die
Gating-Entscheidung selbst kann dieser Versuch NICHT treffen — dafuer waere
Block N noetig gewesen (Netz gegen Netz), und der ist nicht gelaufen.

**Zur Zerlegungsfrage aus par.1**, soweit die eine Paarung sie beantwortet:
**W0 hat `ownership_weight` 0,0** (par.2). Der Staerkegewinn entsteht also
**ohne den Ownership-Verlust**. Ob W1 etwas draufsetzt, ist offen. Der in
par.3 vorregistrierte Konfund bleibt bindend: gegenueber dem Champion
unterscheidet W0 sich in ZWEI Dingen, Korpus UND 100 weitere Epochen — die
Aussage lautet **"Korpus oder Weitertraining"**, nicht "Korpus".

### par.10.1 Was als naechstes zu messen waere (nicht gemessen, keine Empfehlung)

1. ~~`w1_best` und `f1` auf demselben 407-Seed-Satz~~ — **erledigt 15:20,
   par.8.4.**
2. Block N wie in par.4.2 registriert — die Gating-Frage zu Ausgang 3.

### par.10.2 VERDIKT NACH VOLLSTAENDIGEM BLOCK H (2026-08-16, 15:20)

Alle drei blinden Arme aus par.7a liegen jetzt vor. Das Verdikt oben wird
dadurch **nicht umgestossen, sondern verschaerft**:

**Ausgang 2 gilt fuer BEIDE Korpus-Arme.** Was oben nur fuer W0 belegt war,
gilt auch fuer W1: k1 +0,19 / k2 +0,13 / k5 +0,07, alle drei innerhalb der
vorab ausgewiesenen Aufloesung 0,85 / 0,48 / 0,31. Die in par.10 offen
gelassene Moeglichkeit — "es bleibt moeglich, dass der Ownership-VERLUST die
Zielkriterien bewegt" — ist damit **gemessen und verneint**.

**Die Ein-Faktor-Zerlegung aus par.3 ist eingeloest, und sie faellt negativ
aus.** W1 gegen W0 unterscheidet sich in genau einem Manifest-Feld
(`ownership_weight` 1,0 gegen 0,0), ist also vom Korpus/Epochen-Konfund frei.
Ergebnis: W1 ist auf **jeder** Messgroesse schlechter als W0 — Siege 321
gegen 333 (p=0,29), Marge 13,89 gegen 15,99, Platten 2,84 gegen 3,40,
Strafleiste 9,89 gegen 8,87. Einzeln ist keine Differenz signifikant, aber die
Richtung ist ueber alle vier Groessen einheitlich.

> **Der Ownership-Verlust im Training traegt nichts bei.** Nicht zur Staerke,
> nicht zu den Zielkriterien. Er kostet nominal.

Das ist die dritte unabhaengige Absage an denselben Baustein und trifft die
stehende Nutzer-Freigabe zur Gewichtserhoehung (`ownership_weight > 1,0`,
2026-08-16) an der Wurzel: der Sweep war auf den OFFLINE-Kriterien monoton
steigend, aber der Arm mit dem hoechsten Gewicht ist in der Arena der
schwaechere. Eine weitere Erhoehung waere eine Extrapolation entlang einer
Kennlinie, die am gemessenen Ende bereits in die falsche Richtung zeigt.
**Das ist kein Widerruf der Freigabe** — die Entscheidung liegt beim Nutzer —
sondern der Befund, den er dabei kennen sollte.

**Ausgang 3 gilt fuer beide Korpus-Arme**, W0 staerker als W1. Der
Gating-Kandidat ist damit eindeutig **W0_best** — und zwar der Arm OHNE
Ownership-Verlust. Die Gating-Entscheidung bleibt offen: sie verlangt das
DIREKTE Duell (par.4.2 / `paired_gating.py`), nicht den indirekten Vergleich
ueber die Heuristik. Die Kostenprobe aus par.6 ist die Mahnung dazu — F1 schlug
den Champion indirekt und verlor direkt 4:8 (n=12, kein Befund, aber die
richtige Warnung).

### par.10.3 NACHTRAG 2026-08-16, 17:00 — DAS DIREKTE DUELL IST GEFAHREN, UND ES KIPPT AUSGANG 3

`evaluations/artifacts/paired_gating_w0best_vs_champion.json`, `tools/paired_gating.py`,
`--no-promote-winner` (der Default haette `models/champion.txt` selbsttaetig
umgeschrieben, `paired_gating.py:473`). Beide @400 Sims, Brett-Tausch je Paar.

| | Wert |
|---|---:|
| **W0_best gegen Champion** | **43 : 57** (100 Partien, 50 Paare) |
| SPRT-Verdikt | **H0** nach 50 Paaren (LLR −3,251, Schranke −2,944) |
| Vorzeichentest (Bericht, nicht die Stoppregel) | p = 0,2100 |
| Gepaarte Differenz | −0,280, 95 %-KI [−0,652, +0,092] |
| Durchschnittspunkte | W0 **45,44** gegen CH 44,77 |
| Strafleiste | W0 14,69 gegen CH 14,32 |

**Was das heisst und was nicht.** Die SPRT-Alternative war p=0,65, also ein
grosser Vorsprung; H0 anzunehmen heisst *"kein Beleg fuer einen solchen
Vorsprung"*, nicht *"W0 ist schlechter"*. Der Vorzeichentest (p=0,21) und das
Konfidenzintervall (schliesst 0 ein) sagen: **kein signifikanter Unterschied in
beide Richtungen.** Nominal liegt W0 hinten. **Der Champion bleibt.**

**Der eigentliche Befund ist die Nicht-Transitivitaet.** Gegen die Heuristik
schlaegt W0 den Champion um 37 Partien bei p=0,0017 (par.8.4). Direkt gegen ihn
liegt er hinten. Beides ist gemessen, beides ist gepaart, und beides gilt — der
Vergleich UEBER EINEN DRITTEN GEGNER sagt die Kopf-an-Kopf-Staerke nicht
vorher. Die n=12-Sonde aus par.6 hatte genau darauf gedeutet und wurde
zu Recht nicht als Befund verkauft; jetzt steht es bei n=100.

**Konsequenz fuer den Sprachgebrauch im Projekt:** ein Arm, der nur im
Heuristik-Anker vorne liegt, ist **kein Gating-Kandidat**, sondern ein
Kandidat fuer ein Gating. Der Satz oben ("der Gating-Kandidat ist damit
eindeutig W0_best") war in dieser Hinsicht zu stark und wird hiermit
eingeschraenkt statt geloescht — er stand vor dem Duell.

Kurios und unerklaert: W0 macht im direkten Duell **mehr** Punkte im Schnitt
(45,44 gegen 44,77) und gewinnt trotzdem seltener. Das ist mit diesen Daten
nicht aufgeloest und ausdruecklich als offen markiert.
3. Ein Arm "Weitertraining OHNE Korpus", der den Konfund aus par.3 aufloest.
   Existiert nicht und muesste trainiert werden.

### par.10.4 NACHTRAG 2026-08-16, 18:00 — DIESE MESSUNG IST HINFAELLIG

**Der Policy-Kopf hat den Ownership-Korpus nie gesehen.** Damit beantwortet
diese Vorregistrierung ihre Primaerfrage aus par.1 nicht -- weder positiv noch
negativ.

Geprueft am Code, nicht vermutet (`engine/py/neural_net.py:679`
`_is_policy_carrier`, `:667` `WDL_GENERATOR_PREFIXES`, `:1244`
`MOSAIC_CARRIER_MANIFEST`): eine Datei traegt nur dann Policy-Ziele, wenn ihr
Basename im Traeger-Manifest gelistet ist oder mit einem Traeger-Praefix
beginnt. Andernfalls wird ihre Policy MASKIERT und der Value-Ausgang trotzdem
benutzt.

Nachgerechnet mit der Funktion selbst, gegen beide vorhandenen Manifeste:

| Datei | `policy_carrier_manifest_v20.json` (Default) | `..._v21.json` |
|---|---|---|
| `selfplay_v20wdl_...` | Traeger | Traeger |
| `selfplay_v20wdlsw_...` | **Traeger** | maskiert |
| `selfplay_v21_own_k1_...` | **MASKIERT** | **MASKIERT** |
| `selfplay_v21_own_a_...` | **MASKIERT** | **MASKIERT** |
| `selfplay_heur_own_...` | **MASKIERT** | **MASKIERT** |

Die Korpusdateien erfuellen keine der beiden Bedingungen: sie beginnen nicht
mit `selfplay_v19wdl`/`selfplay_v20wdl` (`WDL_GENERATOR_PREFIXES`), und
namentlich gelistet sind sie auch nicht. **Unter BEIDEN Manifesten maskiert** --
welches bei `w0`/`w1` aktiv war, ist in keinem Trainingsmanifest protokolliert,
aber fuer diesen Befund auch gleichgueltig.

**Was das fuer par.10/par.10.2 heisst:**

- **"Ausgang 2 -- Destillation ist ausgeblieben" ist KEIN Befund ueber
  Destillation.** Der Korpus hat den Policy-Kopf nie erreicht; dass die
  Zielkriterien sich nicht bewegten, ist die mechanische Folge und keine
  Aussage ueber die Lernbarkeit des Plattenbaus.
- **Die Ein-Faktor-Zerlegung W0 gegen W1 bleibt gueltig**, aber sie misst etwas
  Engeres als angenommen: den Ownership-Verlust bei ansonsten gleichem
  VALUE-/OWNERSHIP-Training -- nicht bei gleichem Policy-Training, denn
  Policy-Training auf dem Korpus gab es in keinem der beiden Arme.
- **Die Staerkeunterschiede zum Champion (par.8.4) bleiben gemessen** und
  entstanden ueber Value-Kopf und Trunk-Drift, nicht ueber die Policy.
- **par.10.3 (direktes Duell 43:57) bleibt unberuehrt** -- das ist eine reine
  Spielstaerkemessung.

**Was in par.2 gefehlt hat.** Der Ist-Stand-Abschnitt hat vierzehn Punkte
geprueft, darunter Reglerdefaults und Seed-Determinismus, aber nicht die
Frage, ob die Trainingsdaten des Arms ueberhaupt Policy-Ziele beitragen.
**Kuenftig gehoert der Traeger-Status jeder neuen Korpus-Quelle in die
Ist-Stand-Tabelle jeder Prereg, die eine Policy-Aussage machen will.**

**Wie es aufgefallen ist:** nicht durch eine Messung, sondern durch die
Nutzer-Frage *"welchen grund gab es das den v20 korpus mitzutrainieren"*.
Sie fuehrte in `PREREG_v21_window.md` (Zwei-Klassen-Fenster) und von dort in
die Traegerlogik. Zwei meiner Zwischenbehauptungen dabei waren falsch und
wurden vom Nutzer korrigiert -- zuletzt die Aussage, der Sockel SEI das
Policy-Material: das gilt nur unter dem v21-Manifest, unter dem Default traegt
der Schwarm ebenfalls.

### par.10.5 REICHWEITE: SIEBEN MODELLE, NICHT EINE MESSUNG

Auf die Nutzer-Frage *"entwertet es wirklich nur ein ergebnis? gab es nur ein
modell mit dem 38000er fenster?"* -- nein. Ausgezaehlt ueber alle
`models/manifest_train_*.json` mit gesetztem `extra_data_dir`: **sieben real
trainierte Modelle** haben den Korpus gesehen (`w0`, `w01`, `w02`, `w05`, `w1`,
`F1`, `F2`; `c1`/`c2`/`f3` wurden abgebrochen). In allen sieben war die
Korpus-Policy maskiert.

**Was die Maskierung genau tut** (`neural_net.py:1804`, abgelesen):

```text
if not file_policy_carrier:
    pol_w = 0.0
```

Sie setzt **allein das Policy-Gewicht** auf 0. Value-, Punkte-, root_q- und
Ownership-Ziele laufen unveraendert durch. Daraus die Dreiteilung:

| | Status |
|---|---|
| Jede Aussage "der Korpus hat die Policy geformt / nicht geformt" | **HINFAELLIG** -- betrifft nicht nur diese Prereg, sondern die Praemisse der Kampagne (Lehrkorpus -> Policy lernt Plattenbau) |
| Tor A (Kopfguete), `PREREG_ownership_corpus.md` par.10 | **GUELTIG** -- Ownership-Ziele waren nie maskiert, der Kopf hat aus dem Korpus gelernt (AUC 0,83-0,91, w0-Kontrolle 0,502) |
| Tor C (Laufzeit-Regler), par.10.3 (direktes Duell), Frozen-Trunk-Riegel | **GUELTIG** -- reine Spielstaerke- bzw. Mechanikmessungen |

**Die neue Lesart, und sie ist die wichtigste.** Der Korpus hat den
**VALUE-Kopf** gefuettert: 8000 Partien, davon 4000 Bauer-Partien, in denen
absichtlich schlechter gespielt wurde, um Platten zu bauen. Der Value-Kopf ist
in diesem Projekt der gemessen strkketragende (2x2-Kopftausch,
`project_hybrid_head_attribution`: 57,5 % gegen 49,2 %). Die sieben Modelle
haben also **Siegwahrscheinlichkeiten einer absichtlich verzerrten Politik
gelernt und dafuer keinerlei Policy-Signal zurueckbekommen.**

Dazu passt, ohne dass es damit bewiesen waere: `w0_best` verliert das direkte
Duell 43:57 (par.10.3), obwohl es den Champion ueber den Heuristik-Anker
deutlich schlaegt (par.8.4). **HYPOTHESE, ausdruecklich ungeprueft:** der
Korpus hat den Value-Kopf verschlechtert. Pruefbar, indem man den Value-Kopf
eines Korpus-Arms und den des Champions auf DEMSELBEN Held-out vergleicht --
nicht auf dem jeweils eigenen Val-Split, der bei Korpus-Armen anders
zusammengesetzt ist.

### par.10.6 NACHTRAG 2026-08-16 abends — TOR C IST DOCH BETROFFEN (Nutzer-Einwand)

In par.10.4/par.10.5 steht Tor C in der Spalte "GUELTIG". **Das ist zu weit
gefasst**, Nutzer-Einwand: *"er ist durchgefallen weil wir kein modell hatten
das am richtigen korpus trainiert war"*.

Der Grund traegt. Der Verbraucher steuert nicht den KOPF, sondern die SUCHE:
er verschiebt den Blattwert in Richtung der Geometrien, die der Kopf fuer
vollendbar haelt. WELCHE Zuege ueberhaupt bewertet werden, bestimmt aber der
Policy-Prior. Eine Policy, die den Plattenbau nie gesehen hat — und keine der
Tor-C-Vehikel (`f1`, `w1`) hatte ihn gesehen, siehe par.10.4 — schlaegt den
plattenbauenden Zug nicht vor, und dann kann kein Blatt-Shift ihn waehlen.

**Praezisierte Reichweite:**

| | |
|---|---|
| "Der Laufzeit-Regler nuetzt nichts" | **NICHT belegt** |
| "Der Laufzeit-Regler nuetzt nichts bei einer Policy, die den Plattenbau nicht kennt" | belegt (98/89/86/84 Siege ueber die Dosisstufen) |

**Was unberuehrt bleibt** (damit die Korrektur nicht ueberschiesst): die
Produktform kollabiert rechnerisch, unabhaengig von jeder Policy
(Marginalwert k1 0,109 gegen k6 1,50, `PREREG_ownership_selector.md` par.1.3),
und die gemessenen Feuerraten sind Eigenschaften des KOPFES, nicht der Policy
(par.9.3 dort).

**Folge:** Tor C ist auf `v21-b18_best` zu WIEDERHOLEN, sobald dieser vorliegt
— dem ersten Checkpoint, dessen Policy zu 100 % aus plattengelenktem Spiel
gelernt hat. Der Regler liegt gebaut in der Engine (Default 0), das Dosisraster
existiert. Erst dann waeren beide Haelften beisammen: eine Policy, die Spalten
bauen KANN, und ein Kopf, der sagt, WELCHE.

### par.10.7 DIE PRIMAERFRAGE IST BEANTWORTET (2026-08-17) — NEGATIV

par.10.4 hatte festgestellt, dass diese Prereg ihre Primaerfrage nicht
beantworten KONNTE, weil der Policy-Kopf den Korpus nie gesehen hat. Mit
`v21-b18` gibt es erstmals einen Checkpoint, dessen Policy-Gradient zu **100 %**
aus dem Korpus kommt (Traegersatz `policy_carrier_manifest_own.json`, 700
Dateien / 7.000 Partien; zum Vergleich hatte der Champion 580 Dateien / 5.800
Partien Sockel — es ist also MEHR, nicht weniger).

**Messung:** `v21-b18_best` gegen den Champion, Netz gegen Netz, beide @400,
407 Seeds, alle Regler aus, Brett-Tausch je Block.
`evaluations/artifacts/paired_arena_env_b18best_vs_ch.json`.

| | `b18_best` | Champion | Delta |
|---|---:|---:|---:|
| Siege | **211/407 = 51,8 %** | 196/407 | Binomial p=0,488; Block-Ebene t=0,88 (nB=16) |
| **k1 vertikale Reihen** | 0,90 | 0,85 | **+0,05** |
| **k2 Diagonalen** | **0,00** | 0,07 | **−0,07** |
| **k5 Eckplatten** | 3,48 | 3,57 | **−0,09** |
| k0 / k3 / k4 / k6 / k7 | 1,50 / 4,12 / 9,61 / −12,10 / 0,35 | 1,56 / 4,24 / 9,51 / −11,92 / 0,48 | alle |Delta| <= 0,18 |

> **Die Destillation uebertraegt den Plattenbau NICHT.** Kein Zielkriterium
> bewegt sich. `b18` hat in 150 Partien **keine einzige Diagonale** geschlossen
> — mit einer Policy, die ausschliesslich aus plattengelenktem Spiel gelernt
> hat.

**Was der Lauf trotzdem zeigt:** die Umstellung kostet **nichts**. Paritaet
gegen den Champion (p=0,49) bei einem Policy-Kanal, der auf eine schmale,
absichtlich suboptimale Verteilung umgestellt wurde und dessen Suchtiefe von
400-600 auf 200 Sims faellt. Das ist die Vorbedingung dafuer, `b18` als
Generator einzusetzen — er produziert keine schlechteren Partien.

**Offen bleibt die Zurechnung**: liegt es am Korpus oder am Prior aus 30.000
Partien, der im Warm Start in den Gewichten steckt? Genau das misst der Cold
Start `v21-b20` (`PREREG_lr_schedule.md` par.6).

**Nicht beantwortet ist damit die Reglerfrage.** Der Verbraucher war in dieser
Messung AUS (`MOSAIC_OWNERSHIP_W=0`). Tor C auf `b18_best` bleibt faellig und
ist jetzt zum ersten Mal fair — die Policy kann den plattenbauenden Zug
vorschlagen, auch wenn sie ihn von sich aus nicht waehlt.

### par.10.8 `v21-b20` COLD START — der letzte offene Punkt der Destillationsfrage

Registriert 2026-08-17 vor dem Lauf. Nutzer-Vorgabe: *"fuer b20 will ich nur
die wertungsplatten thematik wissen"* — der Plateau-Scheduler ist bei diesem
Lauf ein **Nebeneffekt**, den wir mitnehmen, keine Fragestellung.

**Die Frage, und es ist die letzte offene der Destillation:** par.10.7 hat
gezeigt, dass eine Policy mit 100 % Korpus-Gradient den Plattenbau nicht
uebertraegt. Offen blieb die Zurechnung — liegt es am Korpus, oder am Prior
aus 30.000 Partien, der beim Warm Start bereits in den Gewichten steckt?
`v21-b20` startet ohne `--load`. Seine Policy kennt nichts anderes als
plattengelenktes Spiel.

**Aufbau:** identisch zu par.10.7 — gegen den Champion, beide @400, derselbe
407-Seed-Satz, alle Regler aus, `--log-games`. Nur so sind die Plattenzahlen
direkt neben die von `b18` zu stellen.

**Messgroesse: Plattenpunkte je Kriterium (k1/k2/k5).** Die Siege werden
ausgewiesen, tragen hier aber nichts: ein From-Scratch-Aufbau lag in diesem
Projekt schon einmal bei Elo 884 gegen einen 1100er-Champion, ein deutlicher
Arena-Verlust ist eingeplant und sagt ueber die Plattenfrage nichts.

**VORAB-REGEL:**

> Hebt `b20` k1 oder k2 deutlich ueber `b18` (das bei k1 0,90 und k2 0,00
> liegt), war der PRIOR die Blockade — dann ist der Korpus lehrfaehig und der
> Warm Start hat ihn ueberstimmt.
>
> Bleiben k1 und k2 auch bei `b20` auf `b18`-Niveau, ist die Zurechnung
> geklaert und die **Policy-Destillation als Weg abgeschlossen**: dann lehrt
> der Korpus den Plattenbau nicht, unabhaengig vom Prior. Der Plattenbau
> muesste dann ueber die AKTIVIERUNG des Kopfes kommen, nicht ueber die
> Policy.

Beide Ausgaenge sind verwertbar; der zweite schliesst einen Strang, statt ihn
offen zu lassen.

**Erwarteter Saettigungspunkt, vorab festgehalten (Nutzer-Erfahrung
2026-08-17):** aeltere Cold Starts in diesem Projekt plateauten nach rund
**40 Epochen**. Das Budget von 60 ist danach bemessen, nicht geraten. Damit ist
auch die Auswertung interpretierbar: plateaut `b20` bei ~40, war die
Dimensionierung richtig; plateaut er schon bei 10, stimmt etwas anderes nicht
(zu kleiner Policy-Kanal, zu hohe LR, oder Early Stopping greift auf dem
falschen Kopf).

**Laufzeitfolge:** rund 17 min je Epoche, also etwa **11-12 Stunden** bis zum
erwarteten Plateau. `v21-b21` haengt dahinter und kommt entsprechend spaet.

### par.10.9 ERGEBNIS COLD START (2026-08-17) — DER PRIOR WAR NICHT DIE BLOCKADE

`v21-b20_best` gegen den Champion, 407 Seeds, alle Regler aus, identische
Anordnung wie par.10.7. Rohdaten `evaluations/artifacts/paired_arena_env_b20best_vs_ch.json`.

| | `b18` (Warm Start) | `b20` (Cold Start) |
|---|---:|---:|
| Siege gegen Champion | 211/407 = 51,8 % | **158/407 = 38,8 %** |
| k1 vertikale Reihen | 0,90 | 1,03 |
| k2 Diagonalen | 0,00 | 0,13 |
| k5 Eckplatten | 3,48 | 3,54 |

Gepaart ueber dieselben Seeds, Block-Ebene (nB=6, Schwelle |t| > 2,571):
**k1 +0,09 (t 0,27) · k2 +0,13 (t 1,00) · k5 +0,06 (t 0,59)**. Kein Kriterium
signifikant.

> **VERDIKT nach der Vorabregel:** *"Bleiben k1 und k2 auch bei `b20` auf
> `b18`-Niveau, ist die Zurechnung geklaert und die Policy-Destillation als Weg
> abgeschlossen."* Genau das ist eingetreten.

**Was damit geklaert ist.** Eine Policy, die **nichts anderes gesehen hat** als
plattengelenktes Spiel — kein Warm Start, kein Prior aus 30.000 Partien — baut
nicht mehr Platten als eine, die den Korpus obendrauf bekam. Der Prior war also
nicht die Blockade. Der Korpus lehrt den Plattenbau nicht **auf dem Weg ueber
die Policy**, unabhaengig davon, was vorher in den Gewichten stand.

**Und der Cold Start ist als Fahrzeug erledigt:** er ist deutlich schwaecher
(38,8 % gegen 51,8 %) und dabei nicht besser bei den Platten. Beides zusammen
schliesst ihn aus.

**Was NICHT widerlegt ist**, und es ist der einzige verbliebene Weg: die
**Aktivierung** des Kopfes. Die Priormassen-Messung (par.16.2 in
`PREREG_gate_c_consumer_sweep.md`) zeigt, dass `b18` den plattenbauenden Zug oft
dominant ANBIETET (4,91x Gleichverteilungsmasse, 129 von 130 Held-out-Partien).
Er setzt sich nur nicht durch. Genau dort greift der Verbraucher — und genau
dort ist die Produktform die gemessene Bremse.

**Damit sind zwei der drei Wege zum Plattenbau geschlossen:**

| Weg | Stand |
|---|---|
| Laufzeit-Regler in Produktform | **geschlossen, negativ** (par.16.3 + Replikation) |
| Policy-Destillation | **geschlossen, negativ** (par.10.7 Warm Start + par.10.9 Cold Start) |
| **Aktivierung mit korrigierter Form** (Konjunktionsterme) | **GEBAUT, NICHT GEMESSEN** — `PREREG_conjunction_terms.md` |
