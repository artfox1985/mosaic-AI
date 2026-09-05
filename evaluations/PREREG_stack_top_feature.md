<!-- STATUS: OFFEN | Frage: Sieht das Netz dasselbe wie ein Spieler am Tisch? Konkret zuerst: die offen liegende Rueckseite der obersten Kuppelstapel-Platte, die dem Netz heute fehlt. | Beleg: Stufe 0 GEFAHREN 2026-09-05 (par.10): acht Asymmetrien, alle Netz-sieht-weniger; gewichtigste NEU: Typ (Wild/Spezial) der drei ausliegenden Kuppelplatten, nicht ableitbar (Design 2 = Design 8 in den Farben, dome.rs:211/217); Stapel-Rueckseite (par.3) bestaetigt; Netz sieht nichts Verdecktes. Eingetaktet als v24-Arm v24-b04 (Sicht-Arm: Plattentyp 8, Strafleisten-Farben 10, Phantom-Anteile 12 = +30 Flachwerte, INPUT_SIZE 714 -> 744), Bau nach dem b03-Training. Kriterium Sichtgleichheit, nicht Staerke (Nutzer 2026-09-05). -->

# PREREG: Sichtgleichheit Netz/Spieler am Kuppelstapel (`stack_top_feature`)

Stand **2026-08-20**. **ENTWURF, nichts gebaut.** Alles ab par.5 steht in
Plan-Zeitform; par.2 bis par.4 sind in dieser Sitzung am Code geprueft.

## par.1 Ziel und Kriterium (Nutzer-Vorgabe 2026-08-20)

**Das Ziel ist Sichtgleichheit, nicht ein Staerkegewinn.** Das Netz soll
denselben Informationsstand haben wie ein Spieler am Tisch — nicht mehr
(kein Orakel) und nicht weniger. Ob daraus Elo folgt, ist eine SEPARATE,
nachgelagerte Frage; ein flaches Arena-Ergebnis ist kein Grund, die
Sichtgleichheit wieder herzunehmen. Das ist die etablierte Hausregel
"Korrektheit vor gemessenem Nutzen": zurueckgedreht wird nur bei einer
klaren Regression, die Rauschen nicht erklaeren kann.

Damit entfaellt ausdruecklich, was ein Staerke-Zuschnitt verlangt haette:
keine Haeufigkeitsschwelle als Baubedingung, kein Gating-Kriterium, das
ueber Bauen oder Verwerfen entscheidet.

## par.2 Das Prinzip gibt es schon — in der anderen Richtung

Die Farben eines Bonusplaettchens gehen NUR bei aufgedecktem Chip in den
Merkmalsvektor, ausdruecklich begruendet mit *"sonst versteckte
Information, die kein Spieler kennt"* (`engine/src/features.rs:154`, im
Python-Zwilling gleich gehalten). Die Sichtgleichheit ist also bereits
gebautes Hausrecht — bisher nur als Schutz davor, dass das Netz ZU VIEL
sieht. Diese Prereg zieht die zweite Haelfte nach: es soll auch nicht
weniger sehen.

## par.3 Befund am Kuppelstapel (geprueft 2026-08-20)

Was das Netz zum Stapel bekommt, in beiden Flat-Pfaden identisch:

| Merkmal | Inhalt | Pruefstelle |
| --- | --- | --- |
| `dome_pool_mask` (18) | welche Designs noch verdeckt im Stapel liegen (Menge) | `engine/src/features.rs:106` / `:502`, `engine/py/neural_net.py:55` |
| `dome_wild_remaining_frac` (1) | Wild-Anteil des Restes | `engine/src/features.rs:114` / `:514`, `engine/py/neural_net.py:61` |
| `dome_stack_count` (1) | Stapelgroesse | `engine/src/features.rs:393` / `:742` |

Alle drei sind reihenfolgeblind. `dome_stack_top_type` existiert
ausschliesslich in der Serialisierung fuers Frontend
(`engine/src/serialize.rs:269`) und wird in `features.rs` wie in
`neural_net.py` **nirgends gelesen** (Grep ueber beide Dateien, null
Treffer). Der 2D-Pfad aendert daran nichts: der Planes-Zweig haengt
denselben Flat-Vektor an (`InputLayout::PlanesPlusFlat`,
`engine/src/net.rs:118`; `flat_branch`, `engine/py/neural_net.py:2638`).

Der Spieler dagegen sieht die oberste Rueckseite jederzeit — am Tisch
physisch, in der GUI seit Commit 94b9090 auch im Ziehen-Knopf des
Stapel-Dialogs (`stackTopTypeIcon`, `static/js/app.js`). **Genau hier
sieht das Netz weniger als der Mensch.**

Zweite Luecke derselben Art: waehrend einer laufenden Ziehserie kennt der
ziehende Spieler die Rueckseiten ALLER bereits gezogenen Platten. Im
Merkmalsvektor kommt `pending_stack_draw` ueberhaupt nicht vor — es taucht
in `features.rs` nur in der Aktions-ID-Kodierung auf (Grep). Das Netz
merkt eine Ziehserie nur indirekt daran, dass `dome_pool_mask` schrumpft.

## par.4 Kein Orakel-Thema

Die 18 Designs sind ein fester, offener Satz mit je genau einem Exemplar
(`NUM_DOME_TILE_DESIGNS = 18` und 18 verschiedene `defs`-Eintraege,
`engine/src/dome.rs:198-226`). Wer Auslage und Bretter sieht, kennt den
Rest durch Subtraktion. `dome_pool_mask` ist damit **abgeleitetes
oeffentliches Wissen**, kein verdecktes — es spart dem Netz Buchfuehrung,
verraet ihm nichts Zusaetzliches. (Korrektur einer Koordinator-Aussage vom
selben Tag, die die Maske faelschlich als Orakel-Wissen eingeordnet hatte;
Nutzer-Richtigstellung.)

Verdeckt ist am Stapel allein die **Reihenfolge** — und davon liegt das
oberste Element offen. Beim Roundtrip wird die Reihenfolge sogar neu
gewuerfelt und nur die oberste Platte per Tausch an `dome_stack_top_type`
angepasst (`engine/src/serialize.rs:899-918`).

## par.5 Stufe 0 — Sicht-Inventar in BEIDE Richtungen (Plan)

Weil das Kriterium Sichtgleichheit ist und nicht ein einzelnes Loch, wuerde
zuerst ein Abgleich entstehen: **was die GUI einem Spieler zeigt** gegen
**was der Merkmalsvektor traegt**, Feld fuer Feld, mit zwei Spalten
"Netz sieht mehr" und "Netz sieht weniger". Bekannte Eintraege heute:

- Netz sieht **weniger**: oberste Stapel-Rueckseite (par.3), Rueckseiten
  der bereits gezogenen Platten waehrend einer Ziehserie (par.3).
- Netz sieht **mehr**: bislang kein Fund; der einzige Kandidat
  (`dome_pool_mask`) ist nach par.4 ableitbar, und die Chip-Farben sind
  bereits an `chip_revealed` gebunden (par.2).
- Ungeprueft und im Inventar zu klaeren: Mondstapel-Reihenfolge
  (`features.rs:337-340` codiert Positionen), Beutel-/Turmzaehler
  (`bag_colors`/`tower_colors`, im Python-Kommentar als rueckrechenbar
  begruendet, `neural_net.py:45-49`) — beide plausibel oeffentlich, aber
  nicht in dieser Sitzung belegt.

Ergebnis des Inventars ist eine Liste; **diese Prereg baut daraus nur den
Kuppelstapel-Teil** (par.6). Fuer alles Weitere entscheidet der Nutzer
getrennt.

## par.6 Stufe 1 — Der additive Zuschnitt (Plan)

Die Voraussetzung steht bereits: das Eingabe-Layout wird aus der ONNX-Datei
selbst bestimmt (`detect_layout`, `engine/src/net.rs:104-118`), nicht aus
`INPUT_SIZE` geraten.

1. **Kodierung**: zwei Werte am ENDE des Flat-Vektors,
   `[top_is_special, top_is_wild]`; leerer Stapel = `[0, 0]`. `INPUT_SIZE`
   708 -> 710, Indizes 0..707 unveraendert. One-hot statt eines
   Einzelwerts, damit "leer" nicht zwischen Special und Wild interpoliert.

   **AKTUALISIERT 2026-08-27:** die Zahlen stammen vom 2026-08-20;
   `INPUT_SIZE` steht heute bei **714** (`config.py:38`), das Merkmalspaar
   waere also 714 -> 716. Das PRINZIP ist unveraendert: Anhaengen am ENDE,
   Indizes davor bleiben Zeichen fuer Zeichen gleich. Wer die Stufe baut,
   liest den Ist-Stand ab, statt die 708 aus diesem Absatz zu uebernehmen.
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

   **NACHTRAG 2026-08-27: fuer den 2D-Pfad ist das bereits gebaut.** Seit dem
   2026-08-25 kuerzt `net::split_planes_flat_batch_src`
   (`engine/src/net.rs:972ff`, Vermerk `engine/src/lib.rs:1817`) den
   Planes-Block auf die vom MODELL deklarierte Groesse -- am Champion belegt,
   der nach der Erweiterung unveraendert weiterlaeuft. **Offen bleibt genau
   der hier beschriebene FLACHE Pfad** (`features_for_layout`). Der Baustein,
   den `PREREG_uvfa_plate_regime.md` par.2 mitbenutzt, ist damit kleiner als
   beim Anlegen dieser Prereg angenommen.
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

**Erfolgskriterium dieser Stufe (das eigentliche Kriterium der Prereg):**
das Merkmal traegt in jedem Zustand genau den Wert, den die GUI im selben
Zustand anzeigt, und Bestandsmodelle laufen byte-identisch weiter. Beides
ist pruefbar, keine Statistik noetig:

- Sichtgleichheits-Test: ueber >= 500 zufaellige Zustaende stimmt
  `[top_is_special, top_is_wild]` mit `dome_stack_top_type` aus der
  Serialisierung ueberein, inklusive leerem Stapel;
- Regressionstest: "708er-Layout bekommt weiterhin exakt den alten
  Vektor", >= 500 Zustaende, 0 Abweichungen;
- `cargo test --release` gruen, Wheel neu gebaut. Zahlengleichheit bei
  gleichen Seeds gilt dabei als ALARM, nicht als Bestaetigung.

## par.7 Stufe 2 — Netz, das es nutzen kann (Plan, nachgelagert)

Ein Merkmal ohne trainiertes Netz bleibt wirkungslos: Bestandsmodelle
bekommen es nach par.6 Punkt 2 gar nicht zu sehen. Warmstart mit
**null-initialisierten** zwei neuen Spalten in `flat_branch.0.weight`
(Eingangsbreite aus dem Checkpoint ableitbar, `neural_net.py:2825`) — das
Netz ist im ersten Schritt exakt das alte.

**Die Arena laeuft hier als Waechter, nicht als Richter.** Gepaartes
Duell gegen den Champion @400, Auswertung auf BLOCK-Ebene
(`tools/paired_arena_*`). Vorregistrierte Lesart:

- kein signifikanter Unterschied -> das neue Netz uebernimmt trotzdem den
  Merkmalsstand (Sichtgleichheit ist das Ziel, par.1);
- signifikante Regression -> Ursachensuche, NICHT stilles Zuruecknehmen
  der Sichtgleichheit; ein Merkmal, das der Spieler hat, kann das Netz
  nicht ehrlich schwaecher machen, also waere ein solcher Befund ein
  Hinweis auf einen Fehler im Bau oder im Trainingslauf.

Die Offline-Metriken werden ausdruecklich nicht als Kriterium gefuehrt:
der Wirkbereich ist schmal, unterhalb der bekannten Aufloesungsgrenze von
`value_r2_rounds_1_4`.

Fuer die EINORDNUNG (nicht als Baubedingung) waere es nuetzlich zu wissen,
wie oft die Lage ueberhaupt auftritt: Anteil der Zuege mit legalem
`dome_stack_peek` (`engine/src/game.rs:168`), Anteil der Partien mit
mindestens einer gespielten Ziehung, davon der Anteil mit aktiver
"-3 je offenes Spezialfeld"-Wertungsplatte. Eine niedrige Rate erklaert
ein flaches Arena-Ergebnis — sie widerlegt die Sichtgleichheit nicht.

## par.8 Abgrenzung

`pending_stack_draw` (par.3, zweite Luecke) gehoert sachlich zum selben
Ziel, ist hier aber bewusst NICHT mitgebaut: zwei Merkmale in einem Zug
machen jede spaetere Zuordnung unmoeglich. Es steht im Inventar (par.5)
und bekommt bei Bedarf eine eigene Stufe.

## par.9 Prioritaet

**Geparkt, Arbeitskreis "Spaeter" — dieselbe Stufe wie Task #38**
(Nutzer-Entscheid 2026-08-20). Nicht eingeplant, kein Vorrang vor der
laufenden v21-Task-Queue. Wird es angegangen, gilt die Reihenfolge
par.5 -> par.6 -> par.7 ohne Abkuerzung.

**Paket-Hinweis (Nutzer 2026-08-21):** gemeinsam mit dem geparkten Rest
von `PREREG_chance_nodes.md` (Teil B1 `MOSAIC_STACK_DRAW_CHANCE` +
Teil A1) zu heben — dieselbe blinde Zone am Kuppelstapel, zwei Seiten:
dieses Merkmal gibt dem NETZ die oberste Rueckseite, B1 gibt der SUCHE
die korrekte Ein-Schritt-Erwartung am Peek.

## Nachtrag 2026-09-05: kurz geschlossen, auf Nutzer-Anweisung WIEDER OFFEN

Am 2026-09-05 um 11:05 war diese Datei im Zuge der Prereg-Bereinigung auf
UEBERHOLT gesetzt worden (Begruendung: kein Staerkeziel). Der Nutzer hat das
um 11:15 zurueckgenommen: *"da geht es nicht um staerke sondern um
sichtgleichheit."* Sichtgleichheit ist das Kriterium dieser Prereg (par.1),
nicht Elo; sie bleibt OFFEN mit der Prioritaet aus par.9. Der Merkposten in
`docs/architecture_reference.md` verweist hierher zurueck.

## par.10 STUFE 0 GEFAHREN und Eintaktung als v24-Arm `v24-b04` (Nutzer 2026-09-05: "takte ... fuer diese generation ein")

**Sicht-Inventar (Agent, Kernpunkte vom Koordinator am Code nachgeprueft, 11:09):**
Quellen Encoder `engine/src/features.rs` (flach 85-419 JSON-Pfad, 504-782
Direktpfad, 2D 784-1055; die Planes tragen keine Zustandsinformation, die der
Flachvektor nicht auch hat), Serialisierung `engine/src/serialize.rs:239-319`,
GUI `static/js/app.js`, Regeln `docs/engine_manual.md`.

**Netz sieht WENIGER als der Mensch** (nach Gewicht):

1. **Typ der drei ausliegenden Kuppelplatten (Wild gegen Spezial, damit die
   3 Bonuspunkte und die Spezialfeld-Wertung).** `features.rs:369-390`
   kodiert je Feld nur `belegt` und `color_id`; Wild- und Spezialfelder fallen
   beide auf Farbe 0. NICHT ableitbar: Design 2 `(Tuerkis, Rot, Blau, wild)`
   und Design 8 `(Tuerkis, Rot, Blau, special)` (`engine/src/dome.rs:211/217`)
   sind in den 24 kodierten Werten identisch. Der Mensch sieht den Typ
   (`app.js:686-688, 708`). Betrifft fast jede Runde. NEU gefunden.
2. **Rueckseite der obersten Stapelplatte** (`serialize.rs:300-302`,
   `dome_stack_top_type`; in `features.rs` und `neural_net.py` null Treffer):
   par.3 gilt unveraendert.
3. Laufende Ziehserie (gezogene, noch nicht gewaehlte Platten,
   `serialize.rs:307`): nur indirekt ueber die schrumpfende 18er-Maske. par.3
   zweite Luecke, unveraendert; par.8: eigene Stufe.
4. Historie: kein Zug- oder Rundenkontext im Eingang (Mensch: 30 Logzeilen
   und Gedaechtnis). **Nutzer-Entscheid 2026-09-05, 11:30: KEIN Merkposten**
   -- alles Relevante liegt am Brett, das Log dient dem Menschen zur
   Nachschau der KI-Zuege; eine Historie im Eingang bringt nichts.
5. Farben der Strafleisten-Fliesen (`features.rs:212-213` nur Anzahl); sie
   fehlen im `bag+tower`-Zaehler. **In b04 aufgenommen (Nutzer 11:35).**
6. Phantom-Fliesen in Musterreihen (`serialize.rs:180`): GEPRUEFT 11:45, nicht
   rueckrechenbar, Netz haelt sie fuer echte Fliesen. **In b04 aufgenommen.**
7. Phasenaufloesung (`features.rs:65`: start_placement/drafting/scoring = 0),
   vermutlich durch die Zugmaske folgenlos, ungeprueft.
8. ~~Formal: nur der erste Mondstapel je Fabrik, oberste 3 Steine~~
   GEKLAERT 2026-09-05 (Nutzer: kleine Fabriken haben genau einen Stapel, die
   grosse einen Pool mit hoechstens 4 Steinen; am Code: eine kleine Fabrik
   traegt 4 Fliesen (`state.rs`, `TILES_PER_SMALL_FACTORY`), `take_from_sun`
   nimmt mindestens eine und leert die Sonnenseite (`factory.rs:42-58`), der
   Rest wird EIN Stapel mit hoechstens 3 Steinen (`place_on_moon`,
   `factory.rs:61-66`); der Pool der grossen Fabrik ist als 5 Farbzaehler
   vollstaendig kodiert). Kein Randfall, keine Luecke.

**Netz sieht MEHR:** keine verdeckte Information gefunden. `dome_pool_mask`,
`dome_wild_remaining_frac`, `bag+tower` je Farbe und die Wertungs-/Geometrie-
Aggregate sind Funktionen des oeffentlichen Zustands (Buchfuehrung, kein
Wissen); die Bonuschip-Farben haengen korrekt an `chip_revealed`
(`features.rs:154-167`). Ungeprueft: ob die Aufteilung Beutel/Turm fuer den
Menschen vollstaendig rekonstruierbar ist (kodiert wird nur die Summe).

**Eintaktung als Arm `v24-b04` (Sicht-Arm), Zuschnitt (erweitert 2026-09-05,
11:35-11:45 auf Nutzer-Anweisung um Punkte 5 und 6):** ADDITIV am Ende des
Flachvektors, Indizes 0..713 unveraendert, `INPUT_SIZE` 714 -> **744**:
- Abschnitt 12, Plattentyp (8): `[top_is_special, top_is_wild]` (leerer
  Stapel 0/0) und je Auslage-Slot `[has_special, has_wild]` (3 x 2; leerer
  Slot 0/0).
- Abschnitt 13, Strafleisten-Farben (10): je Spieler in Zugreihenfolge
  fuenf Farbzaehler /4 (Nutzer: "farben koennen wir hinzunehmen, sollte dann
  leichter sein fuers netz rueckschluesse zu ziehen welche farben im
  beutel/turm sind").
- Abschnitt 14, Phantom-Anteil je Musterreihe (12): `phantom_count /
  capacity` fuer sechs Reihen je Spieler in Zugreihenfolge. Befund am Code
  (Nutzer-Auftrag "pruef das genauer"): `features.rs:203` zaehlt `tiles` samt
  Phantomen, `phantom_count` wird nirgends kodiert; fuer die Vollendung sind
  Phantome echt, am Rundenende verschwinden sie statt in den Turm zu wandern
  (`round_end.rs:257-259`). Ohne das Merkmal haelt das Netz Phantome fuer
  echte Fliesen und ueberschaetzt Brettbestand und Ruecklauf; aus
  `chips_taken` (nur die Summe je Spieler und Runde) ist die Reihe nicht
  rueckrechenbar.
Abweichung von par.8 (ein Merkmal je Stufe) bewusst: das Kriterium ist
Sichtgleichheit, nicht Attribution; die Arena ist Waechter (par.7), und die
beiden Merkmale sind dieselbe Informationsart (Plattentyp). Ziehserie (3)
und Phasenaufloesung (7) bleiben Merkposten fuer spaetere Stufen (5 und 6 sind in
b04, 8 ist geklaert); Historie (4)
ist auf Nutzer-Entscheid kein Merkposten.

Bau (par.6 Punkte 2-5): drei Encoder-Stellen append-only (JSON-Pfad,
Direktpfad, `neural_net.py`), `features_for_layout` kuerzt den Flachteil auf
die vom Modell deklarierte Laenge (nur kuerzen, nie auffuellen),
`config.INPUT_SIZE`, Laengen-Assertion der Paritaetstests, Fingerprint
`lib.rs:642`; Sichtgleichheits-Test (>= 300 Zustaende gegen
`dome_stack_top_type`, `dome_display`-Typen, `floor` und `phantom_count`) und Regressionstest
(714er-Layout bekommt exakt den alten Vektor); `cargo test --release`, Wheel,
Anker-Invarianz (`/mosaic-anchor-invariance`), Netz-Pfad-Paritaet des Champions
(Zahlengleichheit bei gleichen Seeds ist Pflicht, nicht Alarm: das Champion-
Modell deklariert 714 und darf die neuen Werte nie sehen).

Training `v24-b04`: b01-Rezept (`PREREG_v24_window.md` par.6e), Fenster
`window_v24.txt`, Warmstart aus `v23-b01_brierbest` mit null-initialisierten
30 neuen Spalten von `flat_branch.0.weight` (par.7), Bloecke fuer das ganze
Fenster neu (`INPUT_SIZE` steckt im Block-Schluessel, rund 36 min bei 6
Workern), Monolith neu. **Einziger Faktor gegen b01: die 30 Sichtwerte.**
Abnahme wie die anderen Arme (`night_v24_acceptance_chain.sh b04`), Lesart
par.7: Gleichstand -> Merkmalsstand uebernehmen, Regression -> Fehlersuche.

**Reihenfolge und Zeitplan:** Rust-Bau und Tests, sobald die CPU frei ist;
`config.py`/`neural_net.py` und Wheel-Install erst NACH dem Start des
b03-Trainings (train.py liest `config.INPUT_SIZE` beim Start; eine Aenderung
davor liesse b03 seinen Monolithen nicht finden) und nach dem Ende des
b03-Trainings, wenn das laufende Training das Wheel geladen haelt.

