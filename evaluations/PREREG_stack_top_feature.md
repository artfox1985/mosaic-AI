<!-- STATUS: OFFEN | Frage: Traegt es zur Staerke bei, wenn das Netz die offen liegende Rueckseite der obersten Kuppelstapel-Platte als Merkmal bekommt (additiv, ohne Bestandsmodelle zu brechen)? | Beleg: nichts gebaut. Anlass: Nutzer-Frage 2026-08-20 im Anschluss an die GUI-Aenderung am Stapel-Dialog (Commit 94b9090). Prioritaet: geparkt, Arbeitskreis "Spaeter" wie Task #38. -->

# PREREG: Oberste Stapel-Rueckseite als Netz-Merkmal (`stack_top_feature`)

Stand **2026-08-20**. **ENTWURF, nichts gebaut.** Alles ab par.4 steht in
Plan-Zeitform; par.2/par.3 sind in dieser Sitzung am Code geprueft.

## par.1 Anlass

Der Ziehen-Knopf im Stapel-Dialog zeigt seit Commit 94b9090 die Rueckseite
der Platte, die als naechstes kaeme (`stackTopTypeIcon`, `static/js/app.js`).
Nutzer-Rueckfrage im selben Zug: *"hat diese information das netz auch?"*
Die Pruefung sagt nein — und zwar an einer Stelle, an der der Mensch am
Tisch mehr sieht als die KI.

## par.2 Befund (geprueft 2026-08-20)

Was das Netz zum Kuppelstapel bekommt, in beiden Flat-Pfaden identisch:

| Merkmal | Inhalt | Pruefstelle |
| --- | --- | --- |
| `dome_pool_mask` (18) | welche Designs noch verdeckt im Stapel liegen (Menge) | `engine/src/features.rs:106` / `:502`, `engine/py/neural_net.py:55` |
| `dome_wild_remaining_frac` (1) | Wild-Anteil des Restes | `engine/src/features.rs:114` / `:514`, `engine/py/neural_net.py:61` |
| `dome_stack_count` (1) | Stapelgroesse | `engine/src/features.rs:393` / `:742` |

`dome_stack_top_type` existiert ausschliesslich in der Serialisierung fuers
Frontend (`engine/src/serialize.rs:269`) und wird in `features.rs` wie in
`neural_net.py` **nirgends gelesen** (Grep ueber beide Dateien, null Treffer).
Der 2D-Pfad aendert daran nichts: der Planes-Zweig haengt denselben
Flat-Vektor an (`InputLayout::PlanesPlusFlat`, `engine/src/net.rs:118`;
`flat_branch`, `engine/py/neural_net.py:2638`).

Verdeckt ist damit allein die **Reihenfolge** des Stapels — und genau davon
liegt das oberste Element offen auf dem Tisch. Beim Roundtrip wird die
Reihenfolge sogar neu gewuerfelt und nur die oberste Platte per Tausch an
`dome_stack_top_type` angepasst (`engine/src/serialize.rs:899-918`).

## par.3 Kein Orakel-Thema, sondern eine Luecke

Die 18 Designs sind ein fester, offener Satz mit je genau einem Exemplar
(`NUM_DOME_TILE_DESIGNS = 18` und 18 verschiedene `defs`-Eintraege,
`engine/src/dome.rs:198-226`). Wer Auslage und Bretter sieht, kennt den Rest
durch Subtraktion. `dome_pool_mask` ist also **abgeleitetes oeffentliches
Wissen**, kein verdecktes — es spart dem Netz Buchfuehrung, verraet ihm
nichts Zusaetzliches. (Korrektur einer Koordinator-Aussage vom selben Tag,
die die Maske faelschlich als Orakel-Wissen eingeordnet hatte;
Nutzer-Richtigstellung.)

Uebrig bleibt eine Asymmetrie in die andere Richtung: das Netz spielt hier
mit **weniger** Information als ein Mensch. Relevanzfall ist die Wertungs-
platte "-3 je offenes Spezialfeld" — genau die Begruendung, mit der
`dome_wild_remaining_frac` seinerzeit eingefuehrt wurde
(`engine/src/serialize.rs:58`), naemlich abzuschaetzen ob die naechste Platte
eher Wild oder Special ist. Beim Ziehen ist das keine Schaetzung mehr.

## par.4 Der additive Zuschnitt (Plan)

Die Voraussetzung steht bereits: das Eingabe-Layout wird aus der ONNX-Datei
selbst bestimmt (`detect_layout`, `engine/src/net.rs:104-118`), nicht aus
`INPUT_SIZE` geraten.

1. **Kodierung**: zwei Werte am ENDE des Flat-Vektors,
   `[top_is_special, top_is_wild]`; leerer Stapel = `[0, 0]`. `INPUT_SIZE`
   708 -> 710, Indizes 0..707 unveraendert. One-hot statt eines Einzelwerts,
   damit "leer" nicht zwischen Special und Wild interpoliert.
2. **Die eine Stelle, an der Additivitaet entsteht**: `features_for_layout`
   (`engine/src/features.rs:952`) ignoriert die deklarierte Laenge heute
   (`Flat(_)`, `PlanesPlusFlat { .. }`) und baut immer den vollen Vektor. Es
   wuerde auf die vom MODELL deklarierte Laenge kuerzen — ein
   708er-Bestandsmodell bekommt `feats[..708]`, ein 710er-Neumodell beide
   neuen Werte. **Nur kuerzen, nie auffuellen**: verlangt ein Modell mehr,
   als der Encoder liefert, soll das hart scheitern statt still Nullen zu
   schieben. Einziger Engpass — saemtliche Inferenz laeuft ueber
   `features_for_net` (17 Aufrufstellen, alle `engine/src/net_mcts.rs`),
   keine zweite Feature-Quelle; die erwartete Puffergroesse kommt aus
   `layout.flat_len()` (`engine/src/net.rs:397`).
3. **Drei Encoder-Stellen, jeweils append-only**: JSON-Pfad
   `features.rs:122`, Direktpfad `features.rs:520`, `neural_net.py:65`.
   Der 2D-Zweig braucht nichts Eigenes, er waechst mit.
4. **Korpora bleiben brauchbar** (geprueft): die gespeicherten Zustaende
   tragen das Feld bereits (Wert `wild` im ersten Zustand von
   `data/ownership_corpus/.progress_v21_own_a_20260814_141733_c43.jsonl`),
   und Merkmale werden ohnehin erst beim Laden aus dem JSON gerechnet
   (`neural_net.py:1557`). Der Cache-Schluessel enthaelt `INPUT_SIZE`
   (`neural_net.py:1258`), der Rebuild loest sich selbst aus.
   Python-Fallback fuer Altbestand ohne Feld: `[0, 0]`.
5. **Mitzuziehen**: `config.INPUT_SIZE`, die Laengen-Assertion der
   Paritaetstests (`features.rs:1059`), der Fingerprint in `lib.rs:552`
   (enthaelt `INPUT_SIZE=`) — und danach **Wheel neu bauen**, sonst sieht
   die Arena den Code nicht.

## par.5 Stufe 0 — Diagnose VOR dem Bau, mit vorregistrierter Schwelle

Praezedenz #39 (Rotation/Position der Startkuppel waren tote Freiheits-
grade) und der Alt-Vorbehalt aus #38: erst messen, ob die Freiheit
ueberhaupt genutzt wird. Auf 200 Champion-Self-Play-Partien wuerde gezaehlt:

- (a) Anteil der Zuege, in denen `dome_stack_peek` legal ist
  (Bedingung: Stapel nicht leer, `engine/src/game.rs:168`),
- (b) Anteil der Partien mit mindestens einer gespielten `dome_stack_peek`,
- (c) darunter der Anteil mit aktiver "-3 je offenes Spezialfeld"-Wertungs-
  platte, also der Fall mit der klarsten Wirkrichtung.

**Abbruchregel, vorregistriert**: liegt (b) unter 10 %, wird nicht gebaut
und diese Prereg auf ENTSCHIEDEN/tot gesetzt. Die 10 % sind gesetzt, nicht
hergeleitet — Begruendung: unter dieser Rate kann ein Merkmal, das nur in
dieser Situation etwas sagt, in einer 400-Partien-Arena keinen Effekt
zeigen, der vom Rauschen zu trennen waere.

## par.6 Stufe 1 — Bau plus Regressionsgate

Erst der Kuerzungs-Mechanismus (par.4 Punkt 2) MIT Test
"708er-Layout bekommt weiterhin exakt den alten Vektor" (>= 500 zufaellige
Zustaende, 0 Abweichungen), dann das Merkmal. **Gate**: Bestands-Champion
laedt und spielt unveraendert; `cargo test --release` gruen; Wheel neu
gebaut, und Zahlengleichheit bei gleichen Seeds gilt als ALARM, nicht als
Bestaetigung.

## par.7 Stufe 2 — Trainingsarm und Entscheidungsmass

Warmstart mit **null-initialisierten** zwei neuen Spalten in
`flat_branch.0.weight` (Eingangsbreite ist aus dem Checkpoint ableitbar,
`neural_net.py:2825`): das Netz ist im ersten Schritt exakt das alte, damit
misst der A/B das Merkmal und nicht einen Neuanfang.

**Vorregistriertes Entscheidungsmass: die Arena, nichts anderes.** Gepaartes
Gating gegen den Champion @400 mit der Haus-Blockanalyse
(`tools/paired_arena_*`), Auswertung auf BLOCK-Ebene. Die Offline-Metriken
werden ausdruecklich NICHT als Kriterium gefuehrt: das Merkmal wirkt nur in
einem schmalen Ausschnitt der Partie, unterhalb der bekannten Aufloesungs-
grenze von `value_r2_rounds_1_4`.

## par.8 Kosten, Risiken, Vorbehalte

- Zwei Werte von 710. Der Bau ist klein; teuer ist ausschliesslich der
  Trainings- plus Arena-Durchgang.
- "Billig" ist kein Argument fuer einen Gewinn. Erwartung ehrlich benannt:
  schmaler Wirkbereich, plausibel H0.
- Das Merkmal beantwortet NICHT, was waehrend einer laufenden Ziehserie
  passiert: `pending_stack_draw` ist in `features.rs` nur in der
  Aktions-ID-Kodierung praesent, nicht als Zustandsmerkmal (Grep). Ein
  zweiter additiver Block koennte das nachtragen — bewusst NICHT Teil
  dieser Prereg, damit der A/B ein Merkmal misst und nicht zwei.

## par.9 Prioritaet

**Geparkt, Arbeitskreis "Spaeter" — dieselbe Stufe wie Task #38**
(Nutzer-Entscheid 2026-08-20). Nicht eingeplant, kein Vorrang vor der
laufenden v21-Task-Queue. Wird es angegangen, gilt die Reihenfolge
par.5 -> par.6 -> par.7 ohne Abkuerzung.
