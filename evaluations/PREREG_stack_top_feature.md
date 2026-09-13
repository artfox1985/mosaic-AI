<!-- STATUS: OFFEN | Frage: Sieht das Netz dasselbe wie ein Spieler am Tisch? | Beleg: Stufe 0 (par.10): acht Asymmetrien, vier GEBAUT (v24-b04, 714 -> 744), elf Stapelwerte (v28-b02, 755). EINGETAKTET v29-b03 (par.13/15/16): P.3, P.7, P.9, P.11-P.15 = 39 Werte, INPUT_SIZE 794 ENTSCHIEDEN (par.16: Vorderseiten erst nach dem Aufhoeren bekannt, Design-Bits bleiben draussen). NEU par.16: die AKTIONSLISTE verraet die Designs schon beim Weiterziehen (game.rs:402) -- Netz-sieht-MEHR, ungemessen. P.10-Suchfix im Code, unkompiliert; par.11 offen. -->

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
Direktpfad, `neural_net.py`), `Net::build_inputs` (`engine/src/net.rs`) kuerzt den Flachteil auf
die vom Modell deklarierte Laenge (nur kuerzen, nie auffuellen; berichtigt
2026-09-09, Audit: hier stand `features_for_layout`, die gibt aber den vollen Vektor
zurueck, die Kuerzung sitzt erst beim Bau des Eingabetensors),
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

## par.11 ZWEITE ACHSE: was WEISS die Suche (Nutzer-Auftrag 2026-09-09)

Diese Prereg fragt "sieht das Netz dasselbe wie ein Spieler am Tisch?" und hat so acht
Asymmetrien gefunden, alle Netz-sieht-weniger. Die Frage hat eine zweite Achse, die bisher
niemand gestellt hat: **was WEISS die Suche, und was vergisst sie zwischen zwei Zuegen?**

Anlass ist der Fund vom 2026-09-09 (`PREREG_dome_stack_information_sets.md`): die
Wurzel-Determinisierung mischt den ganzen Kuppelstapel und loescht damit die
Rueckgabe-Reihenfolge, die der Spieler selbst gewaehlt hat. Ein Sicht-Audit findet das
NICHT -- das Merkmal ist da, der Zustand ist da; vernichtet wird erst im Suchpfad.

**Die zweite Achse ist damit:** fuer jede Information, die ein Spieler am Tisch ueber die
Zeit AUFBAUT (gesehene Stapelplatten, gezaehlte Farben, gemerkte Rueckseiten), nachsehen,
ob der Zustand sie traegt UND ob der Suchpfad sie stehen laesst. Beides muss gelten;
Stufe 0 dieser Prereg hat nur das erste geprueft.

**Eingetaktet fuer v27** zusammen mit den drei offenen Punkten aus par.10. Der Naht-Audit
(alle Stellen, an denen Information absichtlich vernichtet wird) ist am 2026-09-09 bereits
gefahren und steht in `PREREG_dome_stack_information_sets.md` par.10 -- er ist die
Werkzeugseite dieser zweiten Achse.

## par.12 AUDIT 2026-09-09: par.7 ist so nicht falsifizierbar, par.6 zaehlt falsch

**par.7, zweiter Spiegelstrich:** Gleichstand in der Arena heisst "Merkmalsstand
uebernehmen", Regression heisst "Hinweis auf einen Fehler im Bau oder Trainingslauf".
Es gibt keinen Ausgang, unter dem der Stand NICHT uebernommen wird; die Arena ist damit
kein Waechter. Und die Begruendung ("ein Merkmal, das der Spieler hat, kann das Netz nicht
ehrlich schwaecher machen") schliesst per Definition aus, dass ein Warmstart mit
veraenderter Eingabe schlechter konvergiert. Vor Stufe 2 ist ein Ausgang zu benennen, der
den Stand verwirft (Vorschlag: Regression ueber zwei Seeds bei Blockgroesse 5, dann
Merkmal aus und Ursache suchen, nicht "Bau pruefen und trotzdem uebernehmen").

**par.6 Punkt 2:** "17 Aufrufstellen, alle in `net_mcts.rs`". Gezaehlt 2026-09-09: 26
Aufrufe von `features_for_net(` in `engine/src/net_mcts.rs` und 7 in
`engine/src/self_play.rs`. Der Engpass-Charakter (eine Funktion) haelt, die Zahl und
der Ort nicht. Zeilendrift im Altbestand (par.3/4/6) ist gross, ein Dutzend Zeiger; die
Substanz der Aussagen wurde am Code bestaetigt, die Zeilen nicht nachgezogen.

## Nachtrag 2026-09-11, 20:15: Sicht-Merkmale kommen in der Arena nicht an

Der erste Arm mit reinen Sicht-Merkmalen nach v24-b04, `v28-b02` (elf Kuppelstapel-Werte,
`PREREG_dome_stack_information_sets.md` par.15h), ist gegen `v28-b01` ein Nullbefund (207:193,
209:191, beide Deckel). Damit ist die Frage aus `PREREG_v28_window.md` par.7 Punkt 1 beantwortet:
Merkmale der Sicht-Achse allein bewegen die Staerke nicht messbar. Die Sicht-Reststufen
(par.10 P.3 laufende Ziehserie, P.7 Phasenaufloesung) werden NICHT gebaut (Nutzer-Zuschnitt v29,
`PREREG_v29_window.md` par.6). Das Kriterium dieser Prereg (Sichtgleichheit) bleibt davon
unberuehrt; offen bleiben par.11 (was WEISS die Suche) und par.12 (Verwerfungs-Ausgang).

## Nachtrag 2026-09-13, 01:00: Beutel/Turm-Aufteilung ist eine neunte Asymmetrie (Nutzerfrage)

Nutzer: "sprich es wird nicht getrennt zwischen beutel und turm?" Geprueft am Code: der Encoder
kodiert `bag_count`/65 und je Farbe die SUMME Beutel plus Turm (/13; `engine/src/features.rs`
Z.256-269 JSON-Pfad, Z.767-772 Direktpfad). Der Turm-Gesamtbestand ist daraus rechenbar, die
Aufteilung JE FARBE nicht. Der Zustand traegt sie getrennt (`serialize.rs` Z.369-371:
`bag_colors`, `tower_colors`); der Encoder-Kommentar begruendet nur die Rueckrechenbarkeit der
Summe. Die GUI zeigt dem Menschen nur Beutel gesamt und Turm gesamt (`static/js/app.js`
Z.1808-1812), keine Farben.

Warum es zaehlt: die Fabriken werden aus dem Beutel gefuellt, der Turm wird erst bei leerem Beutel
gemischt und nachgefuellt (`docs/engine_manual.md` Z.29-31, `state.rs` Z.265/314). Die
Farbverteilung der naechsten Auslage haengt an der Beutelzusammensetzung, nicht an der Summe;
relevant vor allem in den Runden 3 bis 5 bei kleinem Beutel. Die Suche braucht die Aufteilung heute
nicht (sie spielt den Rundenuebergang nicht), die Information ginge allein in den Value-Kopf.

OFFENER REGELPUNKT (Nutzer): liegt der Turm im Original offen? Das Handbuch sagt es nicht. Liegt er
offen, ist die Aufteilung fuer einen zaehlenden Spieler vollstaendig rekonstruierbar und die Luecke
eine echte Sicht-Asymmetrie (P.9), Bau wie P.5: fuenf additive Werte (Turm je Farbe /13) in einem
Sicht-Arm (v29 oder v30, neue INPUT_SIZE). Liegt er verdeckt, ist der Stand sichtgleich und der
Punkt geschlossen. Kein Bau ohne Entscheid.

Zugleich berichtigt (Koordinator, Chat 00:55): die Kurzfassung "Anlass geschlossen, fuenf
Restpunkte haengen an den Sicht-Reststufen" war zu locker. Offen sind P.3 (Ziehserie, nicht
gebaut), P.7 (Phasenaufloesung, ungeprueft), par.11 (was WEISS die Suche; ein Fall repariert, Achse
nicht abgearbeitet), par.12 (Verwerfungs-Ausgang), und jetzt P.9. Der Nachtrag 2026-09-11
begruendet das Nichtbauen von P.3/P.7 mit dem Nullbefund b02 gegen b01; par.1 dieser Datei sagt
ausdruecklich, dass ein flaches Arena-Ergebnis kein Grund ist, die Sichtgleichheit herzunehmen.
Die Prereg bleibt OFFEN, bis P.3/P.7/P.9 gebaut oder vom Nutzer ausdruecklich als "bewusst nicht
sichtgleich" entschieden sind.

## par.13 EINGETAKTET FUER v29: P.3, P.7 (Nutzer 2026-09-13, 01:00: "takte p3 und p7 fuer v29 ein") und P.9 als Vorschlag

**Regelpunkt zu P.9 GEKLAERT (Nutzer, woertlich): "der turm liegt nicht offen, es laesst sich nur
mitzaehlen am rundenende was in den turm kommt."** Damit ist die Aufteilung fuer einen zaehlenden
Spieler rekonstruierbar (alles, was in den Turm geht, ist im Moment des Abraeumens sichtbar:
Strafleiste und Ueberschuss der Musterreihen), also Information, die der Spieler ueber die Zeit
AUFBAUT, genau die Klasse von par.11. Der Zustand traegt sie (`tower_colors`), der Encoder
addiert sie weg: P.9 ist eine echte Sicht-Asymmetrie. Aufnahme in den Sicht-Arm ist VORSCHLAG
(fuenf Werte, Record-Feld vorhanden), Freigabe des Nutzers steht aus.

**Record-Lage (geprueft 2026-09-13, alle drei Felder liegen seit jeher im Record, KEIN neues
Record-Feld noetig, anders als bei `dome_pool_view` fuer v28-b02):**
- P.3: `pending_stack_draw` (`serialize.rs` Z.368, Liste der gezogenen, noch nicht gewaehlten
  Platten als `DomeTile`; Rueckweg Z.1069).
- P.7: `phase` (`serialize.rs` Z.340); der Encoder faltet heute start_placement, drafting und (im
  Direktpfad) scoring auf 0 (`features.rs` Z.62-68 und Z.716-721).
- P.9: `bag_colors`, `tower_colors` (`serialize.rs` Z.370-371).

**Zuschnitt (VORSCHLAG fuer die Bau-Registrierung, additiv nach der 2D-Encoder-Regel, Abschnitt 16
am Ende des Flachvektors, Indizes 0..754 unveraendert):**
- P.3 Ziehserie: Anzahl gezogen /18, davon Wild /18, davon Spezial /18 (das ist, was die
  Rueckseiten waehrend der Serie zeigen), plus 18 Bits "Design liegt gezogen vor mir" in
  tile_id-Reihenfolge. SICHTPUNKT, vor dem Bau zu entscheiden: die 18 Bits sind erst beim
  Stopp (Vorderseiten aufgedeckt) sichtkonform; ob der Entscheid "weiterziehen oder aufhoeren"
  (`DrawStackPeek` gegen `ChooseDrawStackSlot`, `moves.rs` Z.112-120) im Engine-Ablauf die
  Vorderseiten schon kennt, ist am Code zu pruefen; sieht er sie, ist das eine Netz-sieht-MEHR-
  Stelle und gehoert in par.10 nachgetragen. Bis dahin: 3 Werte sicher, 18 Bits bedingt.
- P.7 Phasenaufloesung: One-Hot ueber die sechs Phasen (`state.rs` Z.41-48), 6 Werte; ersetzt
  nicht den alten Wert an Index 0.., sondern kommt dazu (Altmodelle bleiben spielbar).
- P.9 Beutel/Turm: Turm je Farbe /13, 5 Werte (Beutel je Farbe folgt aus der Summe).
Summe 14 sichere plus 18 bedingte Werte: INPUT_SIZE 755 -> 769 oder 787 (STAND 01:00; ueberholt durch
par.15 Nachtrag 02:35: mit P.11 bis P.15 sind es 39 sichere Werte, 755 -> 794 oder 812).

**Arm:** `v29-b03` (Sicht-Arm, Rezept b01 plus Abschnitt 16, Warmstart mit null-initialisierten
neuen Spalten wie v24-b04, Bloecke neu unter dem neuen Schluessel), Faktor gegen b01 = allein die
Sichtwerte; Registrierung in `PREREG_v29_window.md` par.6c, Name in `docs/generation_naming.md`.
Kriterium bleibt par.1 (Sichtgleichheit); die Arena ist Waechter mit dem Verwerfungs-Ausgang aus
par.12 (Regression ueber zwei Seeds bei Blockgroesse 5 -> Merkmal aus, Ursache suchen), damit ist
par.12 mit diesem Arm erledigt.

**Zeitpunkt des Baus:** der Encoder-Anbau ist ein Wheel-Wechsel (Rust beide Pfade, Python-Zwilling
`engine/py/neural_net.py` Abschnitt 16, `config.INPUT_SIZE`, Paritaetstests, Sichtgleichheits-Test
>= 300 Zustaende gegen die drei Record-Felder, Regressionstest 755er-Layout byte-gleich,
Paritaets-Fixture des Champions unveraendert, Anker-Drift gruen). Er gehoert in ein Fenster OHNE
laufende Erzeugung, Waechter oder Kette (`PREREG_v29_window.md` par.4 Punkt 6; Praezedenz v24-b04:
Wheel-Install nie, waehrend ein Lauf das Wheel geladen haelt). Vorschlag: im Generationswechsel
nach der Sims-Neumessung und VOR dem Start der v29-Erzeugung; der Generator v28-b02 deklariert
755 und sieht die neuen Werte nie (`build_inputs` kuerzt). Alternative: nach dem Ende der
Erzeugung vor dem Training. Kosten (ANNAHME): Bau und Tore rund 2 h, Bloecke rund 26 min
(Praezedenz b02), Training wie b01.

Nicht eingetaktet: par.11 (zweite Achse, was WEISS die Suche) bleibt als eigener Punkt offen.

## par.14 CROSSCHECK FLIESENBUCHHALTUNG am Server-Log (Nutzer 2026-09-13, 01:05: "ich denk das laesst sich mitrechnen")

`tools/probes/tile_ledger_crosscheck.py` auf dem Engine-Replay von
`static/log/game_20260911_092554_seed946607.log` (Mensch gegen v27-b01@400; Dump per
`tools/analyze_game_log.py --dump-states`, 106 Entscheidungspunkte, Runden 1-5). Die Sonde benutzt
NUR oeffentliche Information (Fabriken, Musterreihen ohne Phantome, Strafleiste, belegte
Kuppelfelder; Turm als Ereignis-Ledger am Rundenwechsel; Nachfuellregel aus `state.rs`) und vergleicht
Beutel und Turm je Farbe gegen `bag_colors`/`tower_colors` der Engine.

**Ergebnis: 106 von 106 Entscheidungspunkten stimmen in Beutel UND Turm je Farbe ueberein**
(Artefakt `evaluations/artifacts/tile_ledger_crosscheck_game_20260911_092554_seed946607.json`,
n = 106, Grundmenge Entscheidungspunkte des Dumps, Einheit Fliesen je Farbe; 0,05 s). Zwei
Nachfuellungen aus dem Turm: vor Runde 4 (Beutel 2, Turm 34 nach dem Rundenende 3) und vor
Runde 5 (Beutel 15, Turm 15). Die Aufteilung ist also fuer einen zaehlenden Spieler
vollstaendig reproduzierbar, P.9 ist eine echte Sicht-Asymmetrie.

**Was der Encoder heute wegaddiert, am Beispiel Runde 3 (Zuege 47-68):** Beutel [1, 1, 0, 0, 0]
(blau, gelb, rot, schwarz, tuerkis), Turm [7, 5, 4, 2, 0]; das Netz sieht `bag_count` 2 und die
Summe [8, 6, 4, 2, 0]. Fuer die Fuellung von Runde 4 kommen die ersten 2 Fliesen sicher aus
blau/gelb, der Rest aus dem gemischten Turm plus Rundenende-Abraum; die Summe allein sagt das
nicht. Grenzen der Sonde: in dieser Partie keine Phantom-Fliesen (Chip-Vollendung) und keine
gelegte Spezialfliese; beide Faelle sind im Code behandelt (Phantome abgezogen, SPECIAL-Felder
ausgenommen), aber an diesem Log nicht geprueft.

**Abgleich "sieht/weiss das Netz es?" (Nutzer 01:35: "dann gleich es auch ab ob das netz es
weiss/sieht"), am Zustand von Zug 47 (Runde 3, Beutel [1, 1, 0, 0, 0], Turm [7, 5, 4, 2, 0],
`bag_count` 2) ueber die Python-Bindung `state_features_from_json` / `state_planes_from_json`
(755er Flachvektor plus 2D-Planes):**
- V1, gleiche Summe je Farbe, andere Aufteilung (Beutel [0, 2, 0, 0, 0], Turm [8, 4, 4, 2, 0]):
  Flachvektor an allen 755 Indizes identisch, Planes identisch. **Das Netz SIEHT die Aufteilung
  nicht.**
- V2, Beutel und Turm komplett vertauscht: nur Index 2 (`bag_count`/65, `features.rs` Z.257)
  weicht ab (0,0308 gegen 0,2769); je Farbe nichts. Das Netz sieht also den Beutel-GESAMTbestand
  und je Farbe die Summe, sonst nichts.
- Suche: `engine/src/net_mcts.rs` enthaelt keinen Treffer fuer `bag` oder `tower` (0 Treffer);
  die Suche spielt den Rundenuebergang nicht (Blatt vor dem Tiling), sie zieht nie aus dem Beutel.
  **Das Netz WEISS die Aufteilung auch ueber die Suche nicht.** Sie wirkt heute nirgends; sie
  koennte nur als Eingang des Value-Kopfs wirken (P.9, Sicht-Arm v29-b03), und erst mit einer
  Suche, die den Rundenuebergang sieht (`PREREG_round_transition_search_sampling.md`), auch dort.

**P.9 EINGETAKTET (Nutzer 2026-09-13, 01:45: "also wieder eine sichtluecke. takte es ein"):** der
Vorschlag aus par.13 wird Bestandteil des Sicht-Arms v29-b03, fuenf additive Werte (Turm je Farbe
/13, Reihenfolge wie `bag_colors`; der Beutel je Farbe folgt aus der Summe an Abschnitt 1).
Nutzer-Lesart, festgehalten: das Netz kann die Beutel/Turm-Mechanik ohne diese Werte nicht lernen,
es weiss nur "irgendwo ausserhalb des Bretts" je Farbe plus die Beutel-Gesamtzahl. Abschnitt 16
umfasst damit P.3 (3 sichere plus 18 bedingte Werte), P.7 (6) und P.9 (5): INPUT_SIZE 755 -> 769
oder 787 (STAND 01:45, ueberholt: 794/812 seit par.15 Nachtrag 02:35). Nachtrag im Kopf und in `PREREG_v29_window.md` par.6c/par.8.

## par.15 SICHTINVENTUR IN BEIDE RICHTUNGEN (Agent Opus, 2026-09-13, 01:50-02:05; Bericht `evaluations/review/sight_asymmetry_audit_2026-09-13.md`)

Nutzer-Auftrag 01:45: "lass einen agenten sicht ungleichheiten suchen; vergleich mal was dem server
game / menschen noch zur verfuegung steht und dem netz nicht bzw. umgekehrt". Vier Wege: Feld-Diff
`state_to_json` gegen Encoder-Lesestellen, GUI-Diff, Zeitachse (par.11), verdecktes Wissen der Suche.
Agenten-Befunde sind Behauptungen; die mit "GEPRUEFT" markierten hat der Koordinator am Code
nachgelesen.

| Nr. | Richtung | Befund | Pruefstelle | Stand |
| --- | --- | --- | --- | --- |
| **P.10** | Suche VERGISST oeffentliche Information | `determinize_dome_pool` mischt den unbekannten Praefix des Stapels `[..prefix_len]` INKLUSIVE Index 0; gezogen wird per `remove(0)`, Index 0 ist also die oberste Platte, deren Rueckseite laut Zustand fuer beide jederzeit sichtbar ist (`dome_stack_top_type`, Merkmal P.2 aus v24-b04). Die Wurzel wird VOR `make_node` determinisiert (`DETERMINIZE_ROOT_HIDDEN_INFO = true`), das Netz bekommt im Suchpfad einen neu gewuerfelten Typ der obersten Platte. Fehlerklasse par.11: Sicht-Audit findet es nicht, weil Zustand und Merkmal da sind. | `state.rs` Z.242-243; `game.rs` Z.187; `serialize.rs` Z.357-363; `net_mcts.rs` Z.1373, Z.1410, Z.4938-4943; `features.rs` Z.597-599 | **GEPRUEFT.** Korrektheitsfrage (CLAUDE.md "Symmetrische Defekte sieht keine Arena"): Fix = typerhaltende Permutation, Position 0 behaelt ihren Typ (Tausch mit einer typgleichen Platte im Praefix). Eintrag in `docs/architecture_reference.md` Liste. Nutzer-Entscheid: jetzt fixen (klein, Wheel-Wechsel, Paritaets-Fixture des Champions aendert sich vermutlich) oder im Generationswechsel. |
| **P.11** | Mensch > Netz | Die ANZAHL gehaltener Bonuschips fehlt: der Encoder zaehlt nur Farben ueber alle Chips (`chip_cnt`), ein Zweifarb-Chip {Blau, Rot} und zwei Einfarb-Chips {Blau}+{Rot} ergeben denselben Vektor. Die Vollendungsregel haengt an der Anzahl (2 farbgleiche ODER 3 beliebige je fehlender Fliese). `unused_chip_count` liegt im Zustand, 0 Treffer im Encoder; GUI zeigt jeden Chip einzeln. Jede Runde (2 Chips je Spieler). | `features.rs` Z.381-396; `docs/engine_manual.md` Z.158-159; `serialize.rs` Z.255; 0 Treffer `unused_chip_count` in `features.rs` | **GEPRUEFT.** Vorschlag: 2 additive Werte (Anzahl Chips je Spieler /4) in Abschnitt 16 des Sicht-Arms v29-b03. |
| **P.12** | Mensch > Netz | Design-Identitaet der Platten in FREMDEN Rueckgabe-Bloecken: `dome_pool_view` gibt fuer fremde Bloecke nur `len`/`special`/`wild`, `types` null. Der Gegner sieht laut Regel die Vorderseiten der gezogenen Platten, kennt also die Multimenge der Designs im Block, nur nicht die Reihenfolge. Suche behaelt die Multimenge (Blockmischung), der Encoder wirft sie weg. | `serialize.rs` Z.100-128; `docs/engine_manual.md` Z.86-90; `features.rs` Z.129-159 | **GEPRUEFT.** Vorschlag: 18 Bits "Design liegt in einem Block, dessen Inhalt ich kenne"; Gewicht geringer als P.11 (nur nach Stapelzuegen). |
| P.13 | Mensch > Netz | Blockstruktur des Stapels auf Summen zusammengezogen (Agent). | Bericht Abschnitt 1 | Agenten-Behauptung, NICHT nachgelesen; Teil derselben Kodierung wie P.12. |
| P.14 | Mensch > Netz | `tiled_max_row` weder serialisiert noch kodiert (Agent). | Bericht Abschnitt 1 | NICHT nachgelesen; Gewicht unklar. |
| **P.15** | Mensch > Netz (nur Tiling-Phase) | `holds_first_player_marker` wird in der Rundenwertung geloescht; der Encoder liest nur diesen Marker (`marker`), nicht `first_player_next_round`. In der Tiling-Phase weiss das Netz also nicht, wer die naechste Runde beginnt; relevant fuer Tiling-Entscheide und den Gleichstands-Tiebreak. | `round_end.rs` Z.438-441; `features.rs` Z.361/861; `serialize.rs` Z.348; 0 Treffer `first_player_next_round` in `features.rs` | **GEPRUEFT.** Vorschlag: 1 Wert (Startspieler naechste Runde = ich) in Abschnitt 16. |

Nebenbefund des Agenten (nicht nachgelesen): Kommentar `serialize.rs` Z.281-285 behauptet, der JSON-Pfad
lese `cell_reachable_mask`; `features.rs` habe dafuer 0 Treffer, der Rust-2D-Zweig rechne es neu.
Bekannte Punkte laut Agent: P.1/P.5/P.6 geschlossen, P.8 bestaetigt kein Randfall, P.2 im Encoder
geschlossen, aber in der Suche durch P.10 wieder aufgerissen, P.3/P.7/P.9 offen wie registriert.

**Folgen:** Abschnitt 16 des Sicht-Arms v29-b03 waechst um P.11 (2) und P.15 (1), P.12 (18) nach
Nutzer-Entscheid; P.10 ist KEIN Merkmal, sondern ein Suchfix (Nutzer-Entscheid zum Zeitpunkt).

**REGISTRIERT (Nutzer 2026-09-13, 02:20: "registrier das so"):** Abschnitt 16 des Sicht-Arms v29-b03
umfasst P.3 (Ziehserie, 3 sichere plus 18 bedingte Werte), P.7 (Phasenaufloesung, 6), P.9 (Turm je
Farbe, 5), **P.11 (Anzahl gehaltener Bonuschips je Spieler /4, 2)** und **P.15 (Startspieler der
naechsten Runde = Spieler am Zug, 1)**: 17 sichere Werte, INPUT_SIZE 755 -> 772, mit den 18
Design-Bits von P.3 790 (STAND 02:20, ueberholt: 39 Werte, 794/812 seit dem Nachtrag 02:35). **P.12 (18 Bits, Designs in bekannten fremden Bloecken) bleibt
Nutzer-Entscheid**, nicht Teil des Arms, bis er faellt. **P.10 ist KEIN Merkmal, sondern ein
Suchfix** (typerhaltende Permutation in `determinize_dome_pool`, Position 0 behaelt ihren Typ);
Zeitpunkt offen (jetzt oder im Generationswechsel), Eintrag in `docs/architecture_reference.md`
Naht-Liste als offener Befund. P.13/P.14 bleiben ungepruefte Behauptungen ohne Auftrag.

**NACHTRAG 02:35 (Nutzer: "pruef sie und wirf sie bei bedarf mit rein. p12 kommt mit rein"; "p10 fix kommt jetzt"):**
- **P.12 ENTSCHIEDEN:** 18 Bits "Design liegt in einem Block, dessen Inhalt ich kenne" kommen in
  Abschnitt 16.
- **P.13 GEPRUEFT** (`features.rs` Z.116-127, Z.212-245, `DOME_POOL_TOP_TYPES = 4` Z.104): eigene und
  fremde Bloecke werden je zu Laenge/Spezial/Wild addiert, Positionstypen gibt es nur fuer den
  ERSTEN eigenen Block (`own_seen`) und nur fuer 4 Positionen; Tiefe und Verschachtelung der Bloecke
  fallen weg. Am Tisch weiss der Spieler, wo sein Block liegt. Greift erst ab dem zweiten eigenen
  Block oder bei Bloecken laenger als 4, also selten. AUFGENOMMEN in kompakter Form: Tiefe des
  ersten eigenen Blocks /18 und Anzahl eigener Bloecke /6 (2 Werte); die 24-Werte-Blockliste des
  Agenten nicht.
- **P.14 GEPRUEFT** (`board.rs` Z.260 `tiled_max_row`; `serialize.rs` Z.678 nur intern, Z.1328 nur
  im exact-Pfad; `features.rs` Z.737 nur intern; Regel `docs/engine_manual.md` Z.131-134: nach einer
  tieferen Reihe sind alle Reihen darueber fuer den Rest der Phase gesperrt): der Sperrstand steht
  weder im Record noch im Eingang; in der Tiling-Phase wird das Netz als Tiebreak befragt
  (`self_play.rs` Z.1856 ff., Aktionstypen tiling/end_tiling) und kann eine vollendete, aber
  gesperrte Reihe nicht von einer noch platzierbaren unterscheiden. AUFGENOMMEN: 1 Wert je
  Spieler, (tiled_max_row + 1)/6. **Voraussetzung:** `tiled_max_row` muss als additives Feld in
  `state_to_json` (Record) VOR der v29-Erzeugung ausgegeben werden, sonst traegt der v29-Korpus es
  nicht (Praezedenz `dome_pool_view` fuer v28-b02); der Direktpfad liest es aus dem Zustand.
- **Abschnitt 16 gesamt:** P.3 (3 + 18 bedingt), P.7 (6), P.9 (5), P.11 (2), P.12 (18), P.13 (2),
  P.14 (2), P.15 (1) = 39 sichere Werte, INPUT_SIZE 755 -> 794 (812 mit den Design-Bits von P.3).
- **P.10 FIX GEBAUT (Code, 02:35; Nutzer: "p10 fix kommt jetzt"):** `state.rs`
  `determinize_dome_pool` haelt den Typ der obersten Platte vor dem Mischen fest und stellt ihn
  danach ohne RNG-Verbrauch wieder her (`restore_top_plate_type`, Tauschpartner nur aus dem Segment,
  das Position 0 enthaelt); Test `determinization_keeps_the_public_type_of_the_top_plate` (200 Seeds,
  Praefix als Multimenge erhalten). Der Diagnose-Rueckfall `MOSAIC_DOME_POOL_KNOWLEDGE=0` bleibt
  unveraendert. Der JSON-Rekonstruktionspfad (`serialize.rs` Z.1091-1101) hatte den Typ schon
  erhalten; die Suche nicht. NOCH NICHT KOMPILIERT: Build, Tests, Wheel, Paritaets-Fixture des
  Champions (aendert sich vermutlich, dann bewusst neu), Anker-Drift (Anker ist netzlos, muss gruen
  bleiben) erst nach dem Ende der laufenden Messungen (Sims-Kette, dann die wartende Kante).

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, ob das Netz denselben Informationsstand hat wie ein Spieler am Tisch. Das
Kriterium ist **Sichtgleichheit, nicht Elo** (par.1, Nutzer-Vorgabe 2026-08-20; bekraeftigt
2026-09-05: "da geht es nicht um staerke sondern um sichtgleichheit"). Ein flaches
Arena-Ergebnis ist ausdruecklich kein Grund, die Sichtgleichheit zurueckzunehmen. Der einzige
Ausgang, der den Merkmalsstand VERWIRFT, steht in **par.12** und ist mit dem Arm v29-b03
bindend: eine Regression ueber ZWEI Seeds bei Blockgroesse 5 -> Merkmal aus und Ursache suchen;
Gleichstand -> Merkmalsstand uebernehmen. Die Pruefbarkeit des Baus selbst steht in par.6 Punkt
5 und par.10: Sichtgleichheits-Test gegen die Record-Felder ueber mindestens 300 Zustaende,
Regressionstest "755er-Layout bekommt exakt den alten Vektor", Netz-Paritaets-Fixture des
Champions unveraendert (er deklariert 755 und darf die neuen Werte nie sehen), Anker-Drift
gruen. **Zahlengleichheit bei gleichen Seeds ist hier PFLICHT, nicht Alarm.**

### 2. Voraussetzungen

- **Maschine frei laut Prozessliste** (PowerShell-Zaehler wie `busy` in
  `tools/night_v28_generate.sh`); ein Wheel-Bau ist Volllast und faellt unter die
  Exklusivitaetsregel (CLAUDE.md). Der Anbau gehoert in ein Fenster OHNE laufende Erzeugung,
  Waechter oder Kette (`PREREG_v29_window.md` par.4 Punkt 6; Praezedenz v24-b04: Wheel-Install
  nie, waehrend ein Lauf das Wheel geladen haelt).
- **Ausgangsstand:** installiertes Wheel mit Kontrakt-Hash `39648b95bbba1acf`, INPUT_SIZE 755;
  Champion und Generator `v28-b02` (`models/frozen_champions/v28-b02/`), Anker
  `models/frozen_heuristics/hv4_anchor`.
- **Im Baum liegt bereits, unkompiliert** (par.15 Nachtrag 02:35, STATUS Abschnitt 1 Schritt 6):
  der P.10-Suchfix in `engine/src/state.rs` (`determinize_dome_pool` plus
  `restore_top_plate_type` plus Test
  `determinization_keeps_the_public_type_of_the_top_plate`). Er gehoert in DASSELBE Wheel wie
  das Record-Feld `tiled_max_row`.
- **Vorher durch sein muessen:** die Sims-Kette
  (`PREREG_search_depth_column_optimum.md` par.8e) und die wartende Leiter-Kante
  v28-b02@100 gegen v22-b05@25 -- beide laufen auf dem heutigen Wheel, ein Wheel-Wechsel
  dazwischen stellt sie auf eine andere Engine.
- **Record-Lage geprueft (par.13, 2026-09-13):** `pending_stack_draw` (`serialize.rs` Z.368),
  `phase` (Z.340), `bag_colors`/`tower_colors` (Z.370-371), `unused_chip_count` (Z.255),
  `dome_pool_view` (Z.100-128), `first_player_next_round` (Z.348) liegen im Record. NUR
  `tiled_max_row` fehlt und muss VOR der Erzeugung additiv in `state_to_json` (par.15 Nachtrag,
  P.14; `board.rs` Z.260, heute nur intern in `serialize.rs` Z.678 und im exact-Pfad Z.1328).

### 3. Schritte

**P1 -- Wheel 1: P.10-Suchfix und Record-Feld `tiled_max_row` (STATUS Schritt 6)**

1. **Bau (Code liegt bereits fuer P.10):** `engine/src/state.rs` `determinize_dome_pool` und
   `restore_top_plate_type` durchsehen (typerhaltende Permutation, Position 0 behaelt ihren Typ,
   Tauschpartner nur aus dem Segment, das Position 0 enthaelt, kein zusaetzlicher RNG-Verbrauch);
   der Diagnose-Rueckfall `MOSAIC_DOME_POOL_KNOWLEDGE=0` bleibt unveraendert. Zusaetzlich
   `tiled_max_row` je Spieler additiv in `state_to_json` ausgeben (`engine/src/serialize.rs`,
   Quelle `engine/src/board.rs` Z.260).
2. **Tore, in dieser Reihenfolge** (Muster und gemessene Dauern aus
   `tools/night_v28_knob_build.sh` bzw. `docs/measured_runtimes.md`):

   ```
   $env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH
   cd engine; cargo test --release --lib            # gemessen 80-85 s
   cargo test --release --no-run                    # examples/benches, gemessen 33 s
   python -m maturin build --release                # gemessen 26-34 s
   python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --out evaluations/artifacts/anchor_drift_live_wheel_<datum>_p10.json
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv --out evaluations/artifacts/anchor_conservation_artifact_wheel_<datum>_p10.json
   python -X utf8 tools/generate_knob_docs.py
   python -X utf8 tools/check_conventions.py
   ```

   **Netz-Paritaets-Fixture des Champions:** sie aendert sich durch P.10 VERMUTLICH (par.15,
   STATUS Schritt 6). Aendert sie sich, wird sie BEWUSST neu erzeugt und die Aenderung hier
   begruendet -- mit Gegenprobe ohne den Fix, nach dem Muster von
   `PREREG_code_cleanup_closeout.md` par.8 (A2). Aendert sie sich nicht, ist das ebenfalls ein
   Befund und wird notiert.
   **Anker-Drift muss GRUEN bleiben** (der Anker ist netzlos und liest `determinize_dome_pool`
   nicht). ROT ist Nutzer-Entscheid, keine Reparatur (CLAUDE.md; Stopp-Punkte unten).
   Dauer zusammen: rund 6 min (gemessen "Voller Build" 554 Tests,
   `docs/measured_runtimes.md`, Abschnitt Generation v24).
   **Bei Abbruch:** `cargo os error 32` unter OneDrive ist bekannt (gesperrte `.o`-Datei),
   Wiederholung ist regulaer gruen; `STATUS_DLL_NOT_FOUND` heisst, die Python-DLL fehlt im PATH
   (erste Zeile oben).
3. **Naht-Liste nachziehen:** P.10 steht als offener Befund in `docs/architecture_reference.md`
   ("Wo der Code Information ABSICHTLICH vernichtet") und wird dort mit dem Fix auf erledigt
   gesetzt, mit beiden Antworten (wessen Informationsmenge, was nimmt sie dem Spieler weg).

**P2 -- Sichtpunkt P.3 klaeren, VOR dem Encoder-Bau**

4. **Der Zuschnitt haengt an einer ungeklaerten Codefrage** (par.13, Spiegelstrich P.3): die 18
   Bits "Design liegt gezogen vor mir" sind erst beim Stopp (Vorderseiten aufgedeckt)
   sichtkonform. Am Code zu pruefen ist, ob der Entscheid "weiterziehen oder aufhoeren"
   (`DrawStackPeek` gegen `ChooseDrawStackSlot`, `engine/src/moves.rs` Z.112-120) die
   Vorderseiten schon kennt. Sieht er sie, ist das eine **Netz-sieht-MEHR-Stelle** und gehoert
   in par.10 nachgetragen. Ergebnis entscheidet zwischen INPUT_SIZE **794** (39 sichere Werte)
   und **812** (mit den 18 Design-Bits).
   **Schritt "Zuschnitt registrieren und Nutzer fragen":** der Agent prueft die Codestelle,
   registriert den Befund in par.15, und legt die Zahl (794 oder 812) dem Nutzer vor, statt sie
   zu waehlen. Ohne Antwort wird die konservative Fassung 794 gebaut.

**P3 -- Wheel 2: Encoder-Abschnitt 16 (Sicht-Arm v29-b03)**

5. **Bau, additiv am ENDE des Flachvektors, Indizes 0..754 unveraendert** (par.13/par.15,
   Zusammensetzung: P.3 Ziehserie 3 sichere Werte -- Anzahl gezogen /18, davon Wild /18, davon
   Spezial /18 -- plus 18 bedingte Design-Bits; P.7 Phasen-One-Hot ueber die sechs Phasen
   (`state.rs` Z.41-48), 6; P.9 Turm je Farbe /13, 5; P.11 Anzahl gehaltener Bonuschips je
   Spieler /4, 2; P.12 18 Bits "Design liegt in einem Block, dessen Inhalt ich kenne"; P.13
   Tiefe des ersten eigenen Blocks /18 und Anzahl eigener Bloecke /6, 2; P.14 (tiled_max_row +
   1)/6 je Spieler, 2; P.15 Startspieler naechste Runde = Spieler am Zug, 1).
   Betroffene Stellen, **drei Encoder-Orte append-only** (par.6 Punkt 3, par.10):
   `engine/src/features.rs` JSON-Pfad (Flachteil um Z.85-419) und Direktpfad (um Z.504-782),
   `engine/py/neural_net.py` (Python-Zwilling, Abschnitt 16); dazu `config.INPUT_SIZE`, die
   Laengen-Assertion der Paritaetstests in `features.rs` und der Vertragsstring
   `contract_canonical_string` in `engine/src/lib.rs` (er traegt die Vektorlaenge; nach A10 des
   Code-Abschlusses, `PREREG_code_cleanup_closeout.md` par.3 Punkt 8). **Nur kuerzen, nie
   auffuellen**: `Net::build_inputs` (`engine/src/net.rs`) kuerzt den Flachteil auf die vom
   MODELL deklarierte Laenge (berichtigt 2026-09-09, par.10; nicht `features_for_layout`).
6. **Tore des Encoder-Baus, Reihenfolge Bau -> Tore -> Messung:**
   (a) **Sichtgleichheits-Test** ueber mindestens 300 Zustaende: jeder neue Wert stimmt mit dem
   zugehoerigen Record-Feld ueberein (`pending_stack_draw`, `phase`, `tower_colors`,
   `unused_chip_count`, `dome_pool_view`, `tiled_max_row`, `first_player_next_round`),
   inklusive Randfaellen (leerer Stapel, keine Ziehserie, Tiling-Phase);
   (b) **Regressionstest**: ein 755er-Layout bekommt exakt den alten Vektor, 0 Abweichungen;
   (c) **Netz-Paritaets-Fixture des Champions UNVERAENDERT** (er deklariert 755);
   (d) `cargo test --release --lib`, `cargo test --release --no-run`, Wheel per
   `python -m maturin build --release` und `pip install`;
   (e) **Anker-Drift und Konservierung gruen** (`/mosaic-anchor-invariance`);
   (f) `python -X utf8 tools/check_conventions.py`; Bezeichner englisch (CLAUDE.md).
   Kosten (ANNAHME, par.13): Bau und Tore rund 2 h.
7. **Cache-Bloecke neu** unter dem neuen Schluessel (INPUT_SIZE steckt im Block-Schluessel),
   gemessen rund 26 min fuer 2.947 Dateien bei 6 Workern mit
   `MOSAIC_FEATURES_FROM_RUST=1` (`docs/measured_runtimes.md`, Abschnitt Generation v28);
   Monolith neu (gemessen 531-551 s).
8. **Training v29-b03**: Rezept b01, Warmstart mit **null-initialisierten** neuen Spalten in
   `flat_branch.0.weight` (Muster v24-b04, `train.py` Z.1685-1692), Fenster und Seed wie b01
   (20260941). Dauer gemessen: 12 Epochen rund 1,43-1,46 h.
9. **Tor 1 b03 gegen b01**, zwei Seeds, Blockgroesse 5, `--log-games` -- Befehl in
   `PREREG_v29_window.md` AGENTEN-AUFTRAG Schritt 7. Danach Spaltensonde und Plattenpunkte.
10. **Netz-Gesundheit als Pflichtteil** (`PREREG_v29_window.md` par.6d, fuenf Punkte); Punkt 2
    braucht ein neues Werkzeug `tools/probes/dead_unit_probe.py` (existiert nicht, geprueft
    2026-09-13), Bau rund eine Stunde, Schwelle vorab: mehr als das Doppelte des b01-Anteils
    ist ROT.

**P4 -- par.11, zweite Achse (NICHT eingetaktet)**

11. "Was WEISS die Suche, und was vergisst sie zwischen zwei Zuegen?" ist weiter offen (par.13
    Schlusssatz). Ein Fall ist mit P.10 repariert, die Achse nicht abgearbeitet. Die drei
    Kanaele, mit denen solche Fehler auffindbar sind, stehen in
    `PREREG_dome_stack_information_sets.md` par.11 (Sicht-Audit, Orakel-Differential,
    Anomalie-Report). **Schritt "Zuschnitt registrieren und Nutzer fragen":** kein Auftrag, kein
    Zuschnitt, keine Kosten registriert -- nicht raten, sondern vorlegen.

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Sichtgleichheits-Test "n >= 300 Zustaende, Grundmenge
  zufaellige Spielzustaende, Einheit Abweichungen je Merkmal" (Soll: 0); Regressionstest
  "n >= 300 Zustaende, Einheit abweichende Vektorindizes" (Soll: 0); Tor 1 "n = 400 Partien
  (200 Paare) je Seed, Grundmenge gepaarte Arena-Partien, Einheit Siege".
- **Die sechs Standard-Kennzahlen** (CLAUDE.md) aus den Tor-1-Logs je Seite und als Differenz.
- **Registrierung** in par.15 / einem neuen Ergebnis-Absatz dieser Datei, **Zeile-1-Kopf im
  selben Zug** nachziehen (Status bleibt OFFEN, solange Sichtgleichheit nicht erreicht ist; er
  darf erst auf ENTSCHIEDEN, wenn P.3/P.7/P.9/P.11-P.15 gebaut sind ODER der Nutzer sie
  ausdruecklich als "bewusst nicht sichtgleich" entscheidet, Nachtrag 2026-09-13, 01:00).
  Danach sofort `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1** (Schritt 6 abhaken, neuen Kontrakt-Hash und die neue INPUT_SIZE
  eintragen) und `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung** (CLAUDE.md):
  `grep -rn "INPUT_SIZE\|755\|39648b95bbba1acf\|stack_top_feature\|tiled_max_row" evaluations/ docs/ tools/ engine/ *.py`
  -- jede Fundstelle lesen. Sicher betroffen: `PREREG_v29_window.md` par.3/par.4/par.6c/par.6d,
  `docs/architecture_reference.md`, `docs/generation_loop.md`, `config.py`.
- **Laufzeiten** ins Artefakt je Lauf und als Planungsgroesse nach `docs/measured_runtimes.md`
  (Bau-Tore, Blockbau, Training, Tor 1).
- **Elo-Register**: nur, wenn b03 Champion-Kandidat wird -- dann die Kanten nach
  `docs/promotion_checklist.md`. Der Sicht-Arm selbst erzeugt keine Register-Zeile.

### 5. Stopp-Punkte fuer den Nutzer

- **INPUT_SIZE 794 oder 812** (Sichtpunkt P.3, Schritt 4): Befund vorlegen, nicht selbst waehlen.
- **Paritaets-Fixture aendert sich durch P.10**: "bewusst neu erzeugen" ist eine registrierte
  Handlung mit Begruendung und Gegenprobe -- der Agent macht sie, meldet sie aber ausdruecklich;
  eine stille Neuerzeugung ist ein Regelbruch.
- **Anker-Drift ROT: anhalten.** Nutzer-Entscheid (Anker neu setzen oder Aenderung
  zuruecknehmen), Praezedenz `PREREG_code_cleanup_closeout.md` par.7a.
- **par.11 (zweite Achse)**: kein Bau ohne Auftrag.
- **Aufnahme des Merkmalsstands ins Rezept von v30** entscheidet der Nutzer.
- **Kein Push, keine Loeschung** ohne pfadgenaue Freigabe.

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** Sims-Kette und wartende Leiter-Kante (beide auf dem heutigen Wheel), dann Wheel 1
(P.10 plus `tiled_max_row`) -- das Record-Feld MUSS vor dem Start der v29-Erzeugung im Wheel
sein, sonst traegt der v29-Korpus P.14 nicht (`PREREG_v29_window.md` par.4 Punkt 7b; Praezedenz
`dome_pool_view` fuer v28-b02). **Danach:** `/mosaic-generation-turnover`, Schwarm-Erzeugung,
dann Wheel 2 (Encoder-Abschnitt 16) im Fenster ohne Erzeugung/Waechter/Kette -- Vorschlag par.6c
ist "im Generationswechsel vor dem Start der Erzeugung", Alternative "nach dem Ende der
Erzeugung vor dem Training"; der Generator deklariert 755 und sieht die neuen Werte nie.
**Anschliessend** Bloecke, Training b03, Tor 1 gegen b01, Netz-Gesundheit (par.6d), Registrierung.
Dieser Punkt ist Arm 3 des v29-Programms (`PREREG_v29_window.md` par.6/par.6c); das
Begleitprogramm par.7 dort laeuft unabhaengig davon.

## par.16 P.3 GEKLAERT: die Vorderseiten sind erst nach dem Aufhoeren bekannt -- INPUT_SIZE 794, und eine NEUE Netz-sieht-MEHR-Stelle (2026-09-13, 10:45)

**Regelauskunft des Nutzers (autoritativ, auf die Frage aus par.13/Fahrplan Nr. 4): "die
vorderseiten sind nur bekannt nach dem aufhoeren. beim weiterziehen sind nur die rueckseiten
bekannt."** Der Code sagt dasselbe: `engine/src/game.rs` Z.134-137 und `engine/src/moves.rs`
Z.112-117 halten beide fest, dass die Rueckseite NUR den Typ zeigt (Wild/Special), nicht die
Farbanordnung.

**Folge 1 (Encoder-Zuschnitt, ENTSCHIEDEN): INPUT_SIZE 794, nicht 812.** Die 18 Design-Bits
"Design liegt gezogen vor mir" bleiben DRAUSSEN. Begruendung: derselbe Encoder kodiert den
Zustand in beiden Situationen. Nimmt man die Bits auf, sieht das Netz die Designs auch beim
Entscheid "weiterziehen oder aufhoeren", wo ein Mensch sie nicht hat -- man wuerde also eine
Sichtluecke schliessen und dabei eine neue Ueberlegenheit aufreissen. Abschnitt 16 bleibt damit
bei 39 sicheren Werten: P.3 (3), P.7 (6), P.9 (5), P.11 (2), P.12 (18), P.13 (2), P.14 (2),
P.15 (1). Der Zustand selbst leckt heute nichts: `pending_stack_draw` kommt in
`engine/src/features.rs` nur in einem Kommentar vor (Z.1435), nicht in der Kodierung.

**Folge 2 (NEUER BEFUND, gehoert zu den Netz-sieht-MEHR-Stellen von par.10): die AKTIONSLISTE
verraet die Designs, bevor der Spieler sie kennen darf.** Bei nicht-leerem `pending_stack_draw`
sind laut `game.rs` Z.140-141 keine anderen Drafting-Aktionen legal; die Liste besteht also aus
`DrawStackPeek` plus den Kandidaten aus `generate_draw_stack_moves`
(`engine/src/game.rs` Z.402-425). Diese Kandidaten sind je gezogener Platte mal freiem Slot
erzeugt und **auf mindestens eine legale Rotation gefiltert**
(`draw_stack_slot_rotation_candidates`) -- und diese Legalitaet haengt an der Farbanordnung,
also an der Vorderseite. Wer die Aktionsliste sieht, liest daraus ab, welche Designs gezogen
wurden. Der Mensch am Tisch entscheidet dagegen erst "ich hoere auf", deckt DANN auf und waehlt
DANN Platte und Slot; die Engine legt beide Schritte in eine Aktion und macht die
designabhaengige Legalitaet schon vorher sichtbar.

**Einordnung.** Das ist keine Encoder-Frage, sondern eine der Aktionsmodellierung, und damit ein
Kandidat fuer die Liste in `docs/architecture_reference.md` ("Wo der Code Information absichtlich
vernichtet" -- hier der umgekehrte Fall: wo er Information PREISGIBT). Nach der Regel aus
CLAUDE.md ("Symmetrische Defekte sieht keine Arena") ist das eine Korrektheitsfrage, keine
Elo-Frage: der Vorteil wirkt auf beide Seiten gleich und kuerzt sich in jeder Arena weg.

**NICHT gemessen und NICHT gebaut.** Offen ist, wie stark das wirkt (wie oft steht ueberhaupt
ein Weiterzieh-Entscheid an, und wie oft unterscheiden sich die Kandidatenmengen zwischen den
Designs) und was eine Reparatur kosten wuerde (Aufspaltung in "aufhoeren" und danach
"Platte/Slot waehlen" waere ein Eingriff in die Aktionsmenge und damit in `NUM_ACTIONS` --
Praezedenz `feedback_num_actions_change_breaks_old_checkpoints`). **Zuschnitt und Prioritaet
entscheidet der Nutzer**; hier steht nur der Befund.

## par.17 WHEEL 1 GEBAUT UND ABGENOMMEN (2026-09-13, 11:12-11:35)

Drei Aenderungen in einem Wheel: der **P.10-Suchfix** (`state.rs::restore_top_plate_type`, aus der
Nacht), das **Record-Feld `tiled_max_row`** (P.14, `serialize.rs`) und die beiden
**Stapelzug-Knoepfe im Lauf-Manifest** (`lib.rs::engine_config_json`, Nutzer-Anweisung, Herleitung
in `PREREG_chance_nodes.md`).

**Tore, alle gruen:**

| Tor | Ergebnis |
| --- | --- |
| `cargo test --release --lib` | 638 Tests, 0 rot (nach der Fixture-Neuerzeugung) |
| `cargo test --release --no-run --all-targets` | 16 Targets, keine Fehler |
| Wheel-Bau plus Installation | Vertragshash `39648b95bbba1acf` UNVERAENDERT, `input_size` 755 |
| Neue Manifest-Felder | `stack_draw_research` und `stack_draw_reservation` werden ausgegeben |
| Anker-DRIFT | **GRUEN** (nach dem Umbau, siehe unten) |
| Anker-KONSERVIERUNG | **GRUEN**, 1/1 Dateien feldgleich, 1.763 Schritte |
| `tools/check_conventions.py` | alle Regeln gruen |
| Python-Testsuite | 86 Tests, 0 rot |

**Das Record-Feld hat den Roundtrip-Guard gerissen, und der hat einen Code-Kommentar widerlegt.**
`serialize.rs` behauptete, der harte Default `tiled_max_row: -1` in `player_from_json` sei "fuer
JEDEN `Phase::Drafting`-Zustand exakt richtig". Der Guard zeigte in Runde 2, Phase drafting,
Werte von 1 und 2: der Wert wird nicht beim EINTRITT in Drafting zurueckgesetzt, sondern erst
beim naechsten Uebergang nach Tiling. Konsequenz: `player_from_json` LIEST das Feld jetzt
(Default -1 nur fuer Alt-Records ohne das Feld). Die dort beschriebene "geprüfte, dokumentierte
Ausnahme" ueber `estimated_score` entfaellt damit ebenfalls.

**Die Anker-Drift war zuerst ROT -- als Serialisierungs-Artefakt, nicht als Drift.** Belegt in
`evaluations/artifacts/anchor_drift_counterproof_20260913_wheel1.json`: dasselbe
Golden-Probe-Rezept mit dem Live-Wheel nachgespielt, roh weichen 1.763 von 1.763 Records ab, nach
Abzug des `game_id`-Zeitstempels UND von `tiled_max_row` sind es **0 von 1.763**;
`completed`-Felder und `scores` identisch; die Konservierung gegen dieselbe Probe war GRUEN.
Der Anker bewegt sich also nicht -- das Pruefwerkzeug kannte nur additive Felder nicht.
**Nutzer-Entscheid: Variante D** (statt die Probe neu aufzunehmen oder das Werkzeug stumpf zu
machen): der Vergleich ist jetzt NUR AUFWAERTS tolerant. Ein Feld, das der neue Lauf zusaetzlich
schreibt, wird ignoriert und im Artefakt NAMENTLICH protokolliert; ein fehlendes Feld, ein
geaenderter Wert, eine abweichende Listenlaenge oder Schrittzahl bleiben ROT. Acht Faelle sichern
das in `tools/tests/test_upward_tolerant_divergence.py`, darunter ausdruecklich der Fall
"geaenderter Wert NEBEN einem additiven Feld" -- der Zuwachs darf nichts verdecken.

**Netz-Paritaets-Fixture BEWUSST neu erzeugt:** `e1f94c44f0c7959b` (2026-09-12) ->
`4750ffc6ec094a83` (2026-09-13). Begruendung: der P.10-Fix aendert die Wurzel-Determinisierung im
NETZ-Pfad und damit die gespielten Partien -- das ist der Zweck des Fixes. Beim Anker trat das
nicht auf, weil der Heuristik-Pfad `determinize_dome_pool` nicht ruft; genau diese Asymmetrie war
in der Uebergabe vorhergesagt. Dazu kommt das additive Record-Feld, das in den Hash eingeht.
**Gegenprobe:** derselbe Test OHNE `MOSAIC_UPDATE_NET_PARITY_FIXTURE` in einem frischen Prozess
liefert denselben Hash `4750ffc6ec094a83` (10,8 s) -- die neue Fixture ist reproduzierbar.
