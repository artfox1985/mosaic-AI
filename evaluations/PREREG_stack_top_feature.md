<!-- STATUS: UEBERHOLT | Frage: Sieht das Netz dasselbe wie ein Spieler am Tisch? Konkret zuerst: die offen liegende Rueckseite der obersten Kuppelstapel-Platte, die dem Netz heute fehlt. | Beleg: Nichts gebaut; Ziel war Sichtgleichheit (offen liegende Rueckseite der obersten Stapelplatte), kein Staerkeziel. Geparkt seit 2026-08-20; als Merkposten nach docs/architecture_reference.md verschoben (2026-09-05). Nutzer-Entscheid 2026-09-05: UEBERHOLT. -->

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

## VERDIKT (2026-09-05, Nutzer-Entscheid: "durchfuehren wie vorgeschlagen")

UEBERHOLT als Prereg, erhalten als Merkposten: Sichtgleichheit zwischen Spieler und Netz bleibt ein berechtigtes Ziel, hat aber kein Staerke-Kriterium und keinen Arm. Das Sicht-Inventar (par.5) und der additive Input-Zuschnitt (par.6) stehen als Merkposten in docs/architecture_reference.md; wer sie baut, registriert neu.
