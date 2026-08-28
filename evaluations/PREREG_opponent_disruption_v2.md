<!-- STATUS: UEBERHOLT | Frage: Laesst sich die Gegner-Stoerung ueber die Farbzaehlung als Gleichwertigkeits-Tausch INNERHALB der Suche (statt als Uebersteuerung davor) so bauen, dass sie die Gegner-Plattenpunkte druckt OHNE die eigene Staerke zu kosten? | Beleg: UEBERHOLT 2026-08-18, nichts gebaut: Stufe 2 gehoert inzwischen zum Moon-Order-Kopf, die Einzelentscheidung entfaellt (§12). Die Messungen bleiben gueltig -- Stufe 1 live gefahren, Stoerfensteranteil 7,63 % bei 400 Sims, Abbruchschwelle 5 % nicht unterschritten (§11); Methodenbefund zum Offline-Ersatz: §11.4. -->

# PREREG: Gegner-Stoerung ueber Farbzaehlung, zweiter Anlauf (v2)

Stand 2026-08-16. **PLAN, nichts gebaut, nichts gemessen.** Dieses Dokument
ist das Ergebnis eines reinen Planungsauftrags; jede Aussage ueber Code ist
in dieser Sitzung an der genannten Stelle geprueft oder ausdruecklich als
Herleitung/Annahme markiert (REGEL 0, CLAUDE.md). Durchgehend Plan-Zeitform
fuer alles Vorgeschlagene; Ist-Zeitform ausschliesslich fuer Bestandscode.

Vorgaenger: `PREREG_opponent_disruption.md` (§7: **ABLEHNUNG** vom
2026-08-15). Der Bestandscode des ersten Anlaufs bleibt unangetastet
(LOESCHVERBOT); v2 ist ein NEUER Mechanismus mit NEUEM Knopf, kein
Nachbessern der abgelehnten Messung.

---

## §1 Was der erste Anlauf hinterlassen hat

Zahlen aus `PREREG_opponent_disruption.md` §7.2 (gepoolt, n=40, nicht neu
gemessen -- zitiert, nicht nachgerechnet):

- Zielgroesse **Gegner-Plattenpunkte: Δ +0,05 (t=0,04)**, Vorzeichen
  zwischen den beiden Laeufen gegenlaeufig (+0,95 / −0,85) -- kein Effekt.
- Kosten: Netz-Siege 32/40 → 12/40, McNemar **p=0,0001**; eigene Punkte
  **−32,67**; eigener Strafleisten-Boden **+9,03**.

Diagnose des Vorgaengers (§7.3), die v2 adressieren MUSS:

1. **Fehlende Ueberlauf-Pruefung** in `vorzugszug_fuer_farbe` -- die Fabrik
   bietet mehr Fliesen der Zielfarbe an, als die gewaehlte Musterreihe
   Platz hat; der Rest faellt sofort auf die Strafleiste.
2. **Bedingungsloses Feuern**: der Vorzug ersetzte die 400-Sim-Suche auf
   fast jedem Zug, statt nur bei "ungefaehr gleichwertigen" eigenen Zuegen
   zu greifen. Nutzer-Domaenenwissen (`docs/domain_knowledge.md`,
   Abschnitt "4. BAUSTEIN ... Gegner-Stoerung ueber die Farbzaehlung",
   Zeilen 285-296, in dieser Sitzung gelesen): Stoerung ist ein
   NEBENZIEL -- *"bei ~gleichwertigen eigenen Zuegen"*. Derselbe Abschnitt
   nennt "Gegner stoeren" im Pfeiler-Ranking ausdruecklich *"der
   schwaechste Pfeiler"* (Zeile 282-283).

---

## §2 Code-Pruefung: ist das Q-Abstands-Tor ueberhaupt baubar? (GEPRUEFT)

Kernfrage des Auftrags. Antwort in drei Teilen.

### §2.1 An der heutigen Uebersteuerungsstelle liegen KEINE Suchwerte vor

`plate_builder::drafting_vorzug` (`engine/src/plate_builder.rs:255-259`)
hat die Signatur `fn drafting_vorzug(state: &GameState) -> Option<Action>`
-- sie sieht ausschliesslich den Spielzustand. Kein `root_child_q`, keine
Besuchszahlen, kein Q.

Schlimmer als "nicht durchgereicht": zum Aufrufzeitpunkt EXISTIEREN die
Werte noch nicht. Beide Netz-Agenten berechnen den Vorzug VOR der Suche
und ueberspringen die Suche vollstaendig, sobald er `Some` liefert:

- `self_play.rs:1217-1222` (`NetArenaAgent`, der Arena-Pfad, ueber den
  der erste Anlauf gemessen wurde):
  `let vorzug_kandidat = ...; let chosen = vorzug_kandidat.clone().or_else(|| net_search_drafting_action(...))`
- `self_play.rs:1266-1273` (`NetSelfPlayAgent`): identisches Muster, der
  Vorzugs-Zweig setzt zusaetzlich `root_q = None`, `root_child_q = leer`
  ("keine echte Suche gelaufen", Doku `self_play.rs:1236-1238`).
- Dieselbe `.or_else`-Kette noch einmal im Hybrid-Arena-Pfad
  (`self_play.rs:2414-2418`).

**Verdikt zu Punkt 2 des Auftrags: das Q-Abstands-Tor ist an der heutigen
Stelle NICHT baubar.** Es ist dort nicht "ein fehlender Parameter", sondern
eine Kontrollfluss-Frage: wer Q vergleichen will, muss die Suche zuerst
laufen lassen -- genau das, was der Vorzug heute per Konstruktion einspart.

### §2.2 Die Groesse selbst existiert -- an einer anderen Stelle

`net_mcts::net_root_child_stats_and_policy` (`net_mcts.rs:4334-4419`)
liefert vier Rueckgabewerte, darunter `Vec<(Action, f64)>` mit der
**completed-Q je Wurzelkandidat**, laut Doku (`net_mcts.rs:4319-4333`) auf
der `[0,1]`-Gewinnwahrscheinlichkeits-Skala aus Sicht des an der Wurzel
ziehenden Spielers, ueber `children ∪ untried`. Das ist exakt die Groesse,
die ein ε-Tor braucht. Sie kostet keinen zusaetzlichen Netz-Forward (sie
faellt beim ohnehin gebauten Baum ab).

Verfuegbar ist sie im Self-Play-Pfad (`self_play.rs:2575-2576`), NICHT im
Arena-Pfad: `NetArenaAgent` ruft `net_search_drafting_action`
(`net_mcts.rs:4177-4203`), das nur `Option<Action>` zurueckgibt.

### §2.3 Der entscheidende Fund: dieses Tor ist bereits gebaut -- zweimal

`select_final_root_child` (`net_mcts.rs:3150-3156`) ist laut eigener Doku
(`net_mcts.rs:3140-3145`) *die* gemeinsame Stelle, an der ALLE Aufrufer
(Self-Play, Arena, GUI/Debug) die tatsaechlich gespielte Wurzelaktion aus
dem Suchergebnis bestimmen. Im Gumbel-Zweig laeuft dort bereits
`apply_denial_tiebreak`.

- **E3** (`apply_denial_tiebreak_with`, `net_mcts.rs:2936-2978`): unter
  allen Wurzelkindern mit `completed_q >= best_q - eps` gewinnt das mit der
  niedrigsten Gegner-Punkte-Prognose. Knopf `MOSAIC_DENIAL_TIEBREAK_EPS`,
  Default 0,0 = byte-identisches Bestandsverhalten.
- **E3b** (`denial_uncert_qualifies`, `net_mcts.rs:3015`;
  `apply_denial_tiebreak_uncert_with`, `net_mcts.rs:3047-3090`): ersetzt das
  rohe ε durch Besuchs-Gate `N(a) >= f·N(b)` plus Zwei-Anteils-
  Standardfehler-Fenster. Knoepfe `MOSAIC_DENIAL_UNCERT_Z` /
  `MOSAIC_DENIAL_MIN_VISIT_FRAC`.
- Feuerraten-Zaehler samt Python-Bindung existieren:
  `note_denial_tiebreak`/`denial_tiebreak_stats` (`net_mcts.rs:2848-2881`),
  `lib.rs:713-724` und Registrierung `lib.rs:1158-1159`.

**Damit ist die Architekturfrage entschieden**: das "nur bei ungefaehr
gleichwertig"-Tor wird NICHT neu erfunden und NICHT an `drafting_vorzug`
angebaut. v2 haengt sich in denselben Mechanismus wie E3/E3b und tauscht
ausschliesslich das RANGKRITERIUM aus -- statt "niedrigste
`opp_points`-Kopf-Prognose" (ein Netz-Schaetzwert) das Nutzer-Kriterium
"nimmt dem Gegner die knappe Farbe weg, die er braucht" (reine
oeffentliche Buchhaltung, `gegner_bedarf`, `provocation.rs:753-779`).

Das ist zugleich die ehrliche Warnung: **die Aequivalenz-Fenster-Familie
ist bereits zweimal gemessen und beide Male an der Siegquoten-Wache
gescheitert** (`PREREG_denial_tiebreak.md`, E3 −13,75pp bei ε=0,03; E3b
−4,75pp). Siehe §8.

---

## §3 Baustein A: die Ueberlauf-Pruefung (konkret, mit Pruefstelle)

**Was fehlt heute**: `vorzugszug_fuer_farbe` (`provocation.rs:791-819`)
waehlt unter allen Zuegen mit `m.take.color == farbe` die am weitesten
gefuellte eigene Musterreihe -- ohne je zu fragen, wie viele Fliesen der
Zug ueberhaupt bringt. Der Kommentar daran (`provocation.rs:786-788`) erbt
die Begruendung des Vorbilds `vorzugszug_fuer_spalte`
(`provocation.rs:524-527`): *"KEIN Ueberlauf-Kriterium: `TakeAction` traegt
keine Stueckzahl"*.

**Die Stueckzahl ist ableitbar, und die Funktion dafuer existiert schon**:
`mcts::tiles_taken(state, &m.take) -> usize` (`mcts.rs:573-595`) zaehlt
exakt, wie viele Steine ein Take-Zug entnimmt (Sonnen-Sektion, Mond-Stapel
mit passender Oberseite, globaler Mondzug ueber alle Fabriken). Sie wird
heute in `label_search_move` (`mcts.rs:631-646`) bereits fuer genau diese
Rechnung benutzt:

```
let n = tiles_taken(s, &m.take);
let remaining = row.capacity().saturating_sub(row.tiles.len());
let overflow = n.saturating_sub(remaining);
```

`capacity()`/`spaces_left()` sind `PatternLine`-Methoden
(`board.rs:31-42`), `PatternLine::add_tiles` (`board.rs:56-67`) bestaetigt
dieselbe Semantik im echten Vollzug.

**Geplante Umsetzung** (drei Zeilen Logik, kein neuer Zaehl-Code):

1. `mcts::tiles_taken` wird von `fn` auf `pub(crate) fn` gehoben
   (`mcts.rs:573`) -- Wiederverwendung statt Duplikat (CLAUDE.md).
2. Neue reine Hilfsfunktion in `provocation.rs`:
   `ueberlauf_von(state, m) -> usize` = obige drei Zeilen, `0` fuer
   Bodenzuege (`row_index == -1`).
3. Verwendung als **harter Filter, nicht als Sortierschluessel**: ein
   Stoerungs-Kandidat kommt nur in Frage, wenn
   `ueberlauf_von(state, kandidat) <= ueberlauf_von(state, basiszug)`.
   Der Basiszug ist der Suchsieger; er darf selbst ueberlaufen (das hat die
   Suche dann so bewertet), aber die Stoerung darf den Ueberlauf nie
   VERGROESSERN. Genau das ist die Nutzer-Regel "Schadensbegrenzung vor
   Stoerung" in pruefbarer Form.

**Unit-Test-Pflicht** (Kill-Probe-Standard des Vorgaengers, §5 dort): eine
Stellung, in der der Stoerzug 2 Fliesen in eine Reihe mit 1 freiem Platz
legen wuerde, muss ihn verwerfen; Sabotage des Filters muss den Test
nachweislich rot faerben, bevor er als gruen gilt.

---

## §4 Baustein B: das Gleichwertigkeits-Tor

### §4.1 Gewaehlte Variante B1 (Empfehlung): Rang-Kriterium im E3-Rahmen

**Einhaengepunkt**: `apply_denial_tiebreak`/`select_final_root_child`
(`net_mcts.rs:3124-3156`) -- also INNERHALB der Suche, nach dem Baumbau,
vor der finalen Zugwahl. Der Vorzugs-Pfad (`drafting_vorzug`,
`stoerungs_vorzug`) wird NICHT angefasst und bleibt Default AUS.

**Aequivalenz-Definition**: die E3b-Variante (`denial_uncert_qualifies`,
`net_mcts.rs:3015`) -- Besuchs-Gate plus Zwei-Anteils-SE-Fenster. Begruendung
steht in `PREREG_denial_tiebreak.md` (Zeilen 101-109) und ist die teuer
bezahlte Lehre aus E3: *"Q-Schaetzwerte sind keine Aequivalenzklassen"* --
der Suchsieger traegt Auswahl-Bias, ein rohes ε tauscht systematisch gegen
das Urteil der Suche. Ein rohes ε-Tor wird deshalb ausdruecklich NICHT
vorgeschlagen, obwohl es der naheliegendere Koordinator-Vorschlag war.

**Rang-Kriterium (VORAB festgelegt, danach nicht mehr veraendert)**: unter
den qualifizierten Kandidaten gewinnt der mit dem groessten

```
stoerwirkung(m) = min( tiles_taken(state, m.take),  bedarf_akut[farbe(m)] )
```

- `bedarf_akut` = **nur** der Musterreihen-Anteil aus `gegner_bedarf`
  (`provocation.rs:759-764`, `spaces_left()` je begonnener Gegner-Reihe),
  NICHT der Kuppelraster-Anteil (`provocation.rs:765-777`).
  **Begruendung**: der Raster-Anteil summiert bis zu 36 Zellen und aendert
  sich ueber eine Runde kaum -- er ist eine Langfrist-Forderung, keine
  akute. *(Die Zellen-Iteration ueber `0..6 x 0..6` ist geprueft;
  die Bewertung "swamped die akute Nachfrage" ist eine als solche
  markierte HERLEITUNG, keine Messung.)*
- Tie-Break 1: kleineres `noch_erreichbare_farben[farbe]`
  (`provocation.rs:654-686`) -- knappste Farbe zuerst.
- Tie-Break 2: kleinerer Kandidat-Index (stabil, deterministisch).
- Kandidat qualifiziert sich nur bei `stoerwirkung(m) > stoerwirkung(basis)`
  -- kein Tausch, der nichts gewinnt.
- Harter Filter aus §3 (Ueberlauf) wird VOR dem Rang geprueft.

**Warum `min(...)`**: eine Farbe wegzunehmen hilft nur bis zu der Menge,
die der Gegner tatsaechlich noch braucht; 5 Fliesen einer Farbe zu ziehen,
von der er 1 braucht, ist keine 5-fache Stoerung. *(Modellierungs-
Entscheidung, nicht gemessen -- deshalb vorab fixiert statt spaeter
nachjustiert.)*

**Kandidatenmenge**: nur `nodes[0].children`, exakt wie E3
(`net_mcts.rs:2921-2935`) -- `untried`-Kandidaten haben keine echte
completed-Q, nur den `v_mix`-Platzhalter.

**Knopf**: `MOSAIC_COLOR_DENIAL_Z` (neu, Default 0,0 = AUS =
byte-identisches Bestandsverhalten, `OnceLock`+`read_f64_env`-Muster wie
`net_mcts.rs:2568-2571`) plus `MOSAIC_COLOR_DENIAL_MIN_VISIT_FRAC`
(Default 0,5). Wechselseitiger Ausschluss mit E3/E3b analog
`assert_denial_tiebreak_config_not_conflicting` (`net_mcts.rs:3101-3110`):
zwei gleichzeitig aktive Tie-Break-Kriterien sind ein Konfigurationsfehler,
kein Feature. Eigene Zaehler nach dem Muster `note_denial_tiebreak`
(`net_mcts.rs:2848-2881`) mit eigener Python-Bindung (Vorbild `lib.rs:713-724`).

**Was B1 automatisch mitloest** (und was nicht): der Ueberlauf ist im
Q-Wert des Kandidaten bereits eingepreist (das Netz sieht die Strafleiste),
und ein Kandidat mit deutlich schlechterem Q faellt aus dem Fenster. Das
ist ein WEICHER Schutz auf einem Schaetzwert -- genau die Annahme, die E3
widerlegt hat. Der harte Ueberlauf-Filter aus §3 bleibt deshalb Pflicht,
zusaetzlich, nicht ersatzweise.

Ebenfalls automatisch: die Wirkung greift in ALLEN Pfaden (Self-Play,
Arena, GUI), weil `select_final_root_child` laut Doku
(`net_mcts.rs:3140-3143`) die gemeinsame Stelle ist -- kein Nachziehen von
vier Aufrufstellen, keine Aenderung an `self_play.rs`.

### §4.2 Verworfene Variante B2: Uebersteuerung NACH der Suche

Kontrollfluss in `NetArenaAgent`/`NetSelfPlayAgent` umbauen (erst suchen,
dann `stoerungs_vorzug` gegen `root_child_q` gaten).

Bewertung: **baubar, aber schlechter.** Es erfordert Aenderungen an
mindestens drei Aufrufstellen (`self_play.rs:1217-1222`, `1266-1273`,
`2414-2418`), im Arena-Pfad zusaetzlich einen Wechsel von
`net_search_drafting_action` auf `net_root_child_stats_and_policy`
(`net_mcts.rs:4334`). Dieser Wechsel ist **paritaets-riskant**: die
gespielte Aktion kommt heute aus `select_final_root_child`
(`net_mcts.rs:4202`) inklusive Denial-Tie-Break, waehrend
`net_root_child_stats_and_policy` rohe Stats liefert, aus denen der
Aufrufer selbst waehlt -- eine unbeabsichtigte Aenderung der gespielten
Zuege im AUS-Zustand waere ein stiller Bestandsschutz-Bruch. Ausserdem
verliert der Vorzugs-Pfad seinen einzigen Vorteil (die gesparte Suche),
weil jetzt IMMER gesucht werden muss. Kein Grund, diesen Weg zu gehen,
solange B1 dieselbe Semantik an einer bereits erprobten Stelle liefert.

### §4.3 Verworfene Variante B3: billiges Ersatzkriterium ohne Suchwerte

Z.B. "stoere nur, wenn der eigene Zug in dieser Runde ohnehin keine Reihe
voranbringt" -- rein aus `GameState` ableitbar, damit an `drafting_vorzug`
baubar.

Bewertung: **verworfen als Hauptweg.** Es ist ein Stellvertreter fuer
Gleichwertigkeit, kein Mass dafuer; ein Zug kann eine Reihe nicht
voranbringen und trotzdem der weitaus beste sein (Verweigerung,
Startspieler-Frage, Boden-Vermeidung). Nach der v1-Erfahrung -- eine
Heuristik ueberstimmt eine 400-Sim-Suche und die Siegquote kollabiert --
ist ein weiterer heuristischer Stellvertreter fuer "der Zug kostet nichts"
das genaue Gegenteil der gezogenen Lehre. Bleibt notiert als Rueckfalloption
NUR fuer den Fall, dass B1 an einem hier nicht vorhergesehenen technischen
Hindernis scheitert; dann mit eigener Vorregistrierung.

---

## §5 Vorab-Diagnose: die billige Messung VOR dem Bau

Ziel: die Frage *"tritt ein Q-nahes Stoerfenster ueberhaupt auf?"* soll
beantwortet sein, bevor Aufwand in Messung und Auswertung fliesst. Ein
klares Nein hier ist ein wertvolles Ergebnis.

### §5.1 Stufe 0 (kostenlos, KEIN Bau): Fensterrate aus Bestandsdaten

Die Self-Play-JSONs tragen je echtem Drafting-Entscheid `root_child_q`
parallel zu `policy` (geschrieben in `self_play.rs:1576-1578` ueber
`root_child_q_field`, `self_play.rs:2688-2692`; die Laengen-/
Reihenfolgen-Gleichheit ist per Assertion abgesichert,
`self_play.rs:2626-2631`). Eine reine Python-Auswertung ueber vorhandene
Self-Play-Dateien zaehlt daraus, in wie viel Prozent der Entscheide
mindestens ein Nicht-Sieger im Fenster liegt.

**Ehrliche Erwartung, vorab notiert**: diese Stufe wird mit hoher
Wahrscheinlichkeit bestehen -- E3b hat mit derselben Fensterdefinition
(z=1,0, f=0,5) eine Feuerrate von **36,52%** gemessen
(`PREREG_denial_tiebreak.md` Zeilen 137-143, `evaluations/artifacts/e3b_firing_rate.json`).
Stufe 0 dient deshalb primaer als **Instrumenten-Probe** (liefert der
Datensatz ueberhaupt auswertbare `root_child_q`-Felder?), nicht als echtes
Tor. Kein Besuchszaehler in den JSONs → das Besuchs-Gate ist offline nur
naeherungsweise nachbildbar; die Rate ist damit eine OBERGRENZE, und das
wird im Ergebnis so berichtet.

### §5.2 Stufe 1 (kleiner Bau, ZAEHL-MODUS ohne Tausch): die eigentliche Zahl

Gebaut wird B1 vollstaendig, aber mit einem **Trockenlauf-Schalter**: der
Tie-Break wertet aus und zaehlt, gibt aber IMMER den Basiszug zurueck. Die
gespielten Partien sind damit byte-identisch zum Bestand; gemessen wird
nur die Rate.

Gezaehlt werden drei Zahlen (drei Atomics nach dem Muster
`net_mcts.rs:2848-2863`):

| Zaehler | Bedeutung |
|---|---|
| `total` | ausgewertete Wurzelentscheidungen |
| `fenster` | davon mit >=1 qualifiziertem Nicht-Sieger (Besuchs-Gate + SE-Fenster) |
| `stoerbar` | davon mit >=1 Kandidat, der zusaetzlich den Ueberlauf-Filter (§3) besteht UND `stoerwirkung > basis` hat |

Entscheidende Groesse ist `stoerbar / total`.

**Treiber**: `tools/e3b_firing_rate.py` (existiert) wird als Vorlage
uebernommen. Sein Kopf-Kommentar (Zeilen 7-23, in dieser Sitzung gelesen)
dokumentiert die Falle, die hier genauso gilt: die Zaehler sind
prozessglobale Atomics, `self_play.py` und `paired_arena_env_ab.py` fuehren
sie im KIND-Prozess, der Elternprozess liest `(0,0)` -- das saehe wie
"Rate 0%" aus und wuerde die Abbruchregel FALSCH-POSITIV ausloesen.
`mosaic_rust.net_arena_match` dagegen threadet im selben Prozess.
**Pflicht-Plausibilitaetspruefung uebernommen**: `total > 0`, sonst
"INSTRUMENT KAPUTT" statt einer Rate.

**Umfang**: 200 Partien, Champion@400 vs Heuristik@150dyn, ein frischer
Seed (Konvention der E3b-Stufe-1-Messung).

**ABBRUCHREGEL (vorab, bindend)**: `stoerbar/total < 5%` → **v2 wird ohne
Arena-Messung geschlossen**, Ergebnis dokumentiert, kein weiterer Aufwand.
Begruendung der Schwelle: unter dieser Eingriffstiefe koennte die Arena
einen Effekt ohnehin nicht aufloesen (identische Schwelle und Begruendung
wie `PREREG_denial_tiebreak.md` Zeilen 132-135).

**Gegenwarnung, ebenfalls vorab**: eine HOHE Rate ist KEIN gutes Zeichen
und kein Vorab-Erfolg. E3b feuerte in 36,52% der Entscheidungen und
verlor trotzdem 4,75pp. Die Rate entscheidet nur, ob die Messung
aussagekraeftig sein KANN, nicht ob der Mechanismus taugt.

---

## §6 Messplan, Falsifikation und Abbruch (alles vorab bindend)

### §6.1 Aufbau

`tools/paired_arena_env_ab.py --env-name MOSAIC_COLOR_DENIAL_Z --arms 0 1
--control 0`, Champion@400 vs Heuristik@150dyn, einseitig (die Heuristik
liest den Knopf nicht -- die Zuordnung "wer stoert wen" bleibt damit
eindeutig, wie im Vorgaenger §7.1). Auswertung wieder ueber
`tools/probes/opponent_disruption_analysis.py` (Gegner-/Heuristik-Seite),
Signifikanztests **auf Block-Ebene** (`feedback_arena_block_correlation`).

### §6.2 Stichprobengroesse: mindestens 2 x 200 gepaarte Partien

Der Vorgaenger mass die Zielgroesse mit n=40 -- fuer die Zielgroesse
selbst deutlich zu wenig. **Hergeleitet aus `PREREG_opponent_disruption.md`
§7.2** (Δ=0,95 bei t=0,55, n=20; reine Arithmetik auf berichteten Zahlen,
nicht neu gemessen): SE ≈ 1,73 → SD der gepaarten Differenz ≈ 7,7. Damit
liegt die kleinste bei 80% Power und α=0,05 nachweisbare Differenz bei
n=200 gepaarten Partien bei **≈ 1,5 Gegner-Plattenpunkten**; bei n=40 waere
sie ≈ 3,4 gewesen. Da die Entscheidung auf BLOCK-Ebene faellt und
Block-SEs groesser sind als Paar-SEs, ist das eine optimistische
Untergrenze und wird als solche berichtet.

Zwei Laeufe mit unabhaengigen, frischen Basis-Seeds; **Replikation ist
Pflichtteil, nicht Option** (Lambda-Lehre: Vorzeichenwechsel zwischen
Laeufen). Entscheidung gepoolt ueber beide Laeufe.

### §6.3 Zielgroesse (unveraendert gegenueber v1)

**Gegner-Plattenpunkte, gepaart** (Knopf AN vs. AUS, identische Seeds),
bezogen auf ein festes Brett. Sekundaer deskriptiv: Gegner-Gesamtpunkte,
Gegner-Boden.

### §6.4 Kosten-Waechter: HARTES Vorab-Kriterium, nicht Nebenmessung

Der Vorgaenger fuehrte die Kosten als "Pflicht-Nebenmessung"; v2 macht sie
zum **vorrangigen Abbruchkriterium**. Ausgewertet wird die Kosten-Seite
ZUERST:

1. **McNemar auf Siege**: p < 0,05 gegen den Stoerungs-Arm → **ABBRUCH und
   ABLEHNUNG**, unabhaengig davon, was die Zielgroesse zeigt. Kein
   Abwaegen, kein "aber die Stoerung wirkt".
2. **Punktschaetzer-Wache** (Nutzer-Philosophie *"rein, wenn es nicht
   schadet"*, uebernommen aus `PREREG_denial_tiebreak.md` Zeilen 188-198):
   faellt die Siegquoten-Punktschaetzung unter die Kontrolle, gibt es
   **keine Uebernahme**, auch ohne Signifikanz. Die Beweislast liegt auf
   Schadensfreiheit, nicht auf Schadensnachweis.
3. **Eigene Punkte / eigener Boden**: auf Block-Ebene signifikant
   schlechter (zweiseitig, α=0,05) → ABBRUCH. Beim Vorgaenger waren das
   −32,67 Punkte und +9,03 Boden; jede Wiederholung dieser
   Groessenordnung beendet den Versuch sofort.

### §6.5 Vorzeichen-Regel (unveraendert uebernommen)

Erzielt der Gegner unter aktivem Knopf **bessere** Plattenpunkte als ohne,
ist das ein **ABLEHNUNGS-, kein Interpretationsfall** (k6-Praezedenz,
`PREREG_provocation.md` §19; v1 §4). Kein Nachjustieren des
Rang-Kriteriums oder der Zielfarben-Wahl mitten in der Messung.

### §6.6 Uebernahme nur bei ALLEN drei Bedingungen

- Kosten-Waechter §6.4 vollstaendig bestanden (alle drei Punkte), UND
- Zielgroesse gepoolt signifikant in der gewuenschten Richtung
  (Gegner-Plattenpunkte niedriger, Block-Ebene, α=0,05), UND
- Richtung in BEIDEN Laeufen einzeln gleich (kein Vorzeichenwechsel).

Andernfalls: Knopf bleibt Default 0, Ergebnis wird dokumentiert, Code
bleibt stehen (LOESCHVERBOT), Status-Kopf auf ENTSCHIEDEN.

### §6.7 Reihenfolge und Sperren

1. Stufe 0 (§5.1) -- kostenlos, jederzeit.
2. Bau B1 im Zaehl-Modus + `cargo test --lib` (0 failed vor und nach) +
   **Wheel neu bauen** (`feedback_wheel_neu_bauen_nach_engine_aenderung`:
   gruene `cargo test` heissen nicht, dass die Arena den Code sieht) +
   Default-Paritaetsprobe (`tools/parity_probe.py`, Hash haelt).
3. Stufe 1 (§5.2) -- Abbruchregel.
4. Erst danach Tausch-Modus scharfschalten und §6 messen.
5. Keine Messung, solange ein anderer Lauf die installierte `.pyd`
   belegt (Wheel-Install-Sperre wie im Vorgaenger).

---

## §7 Was v2 ausdruecklich NICHT tut

- **Kein Anfassen von `stoerungs_vorzug`/`vorzugszug_fuer_farbe`/
  `drafting_vorzug`** (`provocation.rs:791-858`,
  `plate_builder.rs:255-259`). Der abgelehnte Pfad bleibt Default AUS und
  unveraendert stehen. Die Ueberlauf-Pruefung aus §3 wird als neue,
  eigenstaendige Hilfsfunktion gebaut und im NEUEN Pfad benutzt; ob sie
  zusaetzlich in den alten Pfad eingehaengt wird, ist bewusst NICHT Teil
  dieses Plans (das waere ein Nachbessern einer abgelehnten Messung).
- **Kein Kombinieren mit E3/E3b** -- gegenseitiger Ausschluss per
  Konfigurations-Abbruch (§4.1).
- **Keine Aktivierung in Gating, Training oder Korpus-Generierung.**
  Reiner Diagnose-Knopf, wie alle Bausteine seit `PREREG_provocation.md`.
- **Keine Dosis-Variante als Rettung.** Scheitert B1, ist die Familie
  geschlossen; eine Wiedereroeffnung braucht einen NEUEN Mechanismus, nicht
  ein anderes z (dieselbe Regel, die sich `PREREG_denial_tiebreak.md`
  Zeilen 208-209 selbst gegeben hat).

---

## §8 Lohnt sich das ueberhaupt? -- ehrliche Einschaetzung

**Meine Einschaetzung: der Bau lohnt sich nur bis Stufe 1, und die
Erfolgswahrscheinlichkeit der vollen Messung ist niedrig.**

Was fuer einen zweiten Anlauf spricht:

- Der erste Anlauf hat sein Ziel nie fair getestet. Er hat die Suche
  ueberstimmt und das eigene Spiel zerstoert; die "+0,05 an der Zielgroesse"
  sind unter diesen Bedingungen kein Beleg fuer "Stoerung wirkt nicht",
  sondern ein Messwert aus einer kaputten Konfiguration. Die eigentliche
  Nutzer-Idee -- stoeren, wenn es nichts kostet -- war nie in der Arena.
- Die Bau-Kosten sind ungewoehnlich niedrig: Einhaengepunkt, Fenster-
  Definition, Zaehler, Python-Bindung und Mess-Treiber existieren alle
  (§2.3, §5.2). v2 ist im Kern ein ausgetauschtes Rang-Kriterium.
- Stufe 1 ist ein billiges, aussagekraeftiges Tor mit Trockenlauf und
  Paritaets-Garantie: sie kann den Punkt fuer wenig Geld schliessen.

**Das Gegenargument, das ich fuer staerker halte:**

1. **Dieselbe Architektur ist zweimal gescheitert.** E3 und E3b haben genau
   das gebaut, was hier vorgeschlagen wird -- Gleichwertigkeitsfenster an
   der Wurzel, Tausch zugunsten des Gegner-Schadens -- und haben −13,75pp
   bzw. −4,75pp gekostet. v2 aendert nur, WORAN die Stoerung gemessen wird
   (Farbzaehlung statt `opp_points`-Kopf), nicht die Bauart. Wenn der
   Verlust von der Bauart kommt (Tausch gegen das Urteil der Suche, auf
   geschaetzten Aequivalenzklassen), hilft ein anderes Rangkriterium nicht.
2. **Plausibel ist schlicht, dass Farbstoerung im 2-Spieler-Spiel zu
   schwach ist.** Eine weggenommene Fliese ist nur dann eine Stoerung,
   wenn der Gegner sie nicht anderswo bekommt und sie ihm akut fehlt --
   zwei Bedingungen, die selten gemeinsam gelten, weil mehrere Fabriken
   dieselbe Farbe anbieten und der Beutel nachliefert. Das
   Nutzer-Domaenenwissen selbst nennt "Gegner stoeren" *"der schwaechste
   Pfeiler"* und den einzigen bisher gemessenen Versuch (λ-Denial) als
   nicht repliziert (`docs/domain_knowledge.md` Zeilen 282-283).
   Das v1-Ergebnis an der Zielgroesse (0,05, Vorzeichen gegenlaeufig)
   passt zu dieser Lesart -- schwach, aber es passt.
3. **Selbst ein Erfolg an der Zielgroesse waere kein Staerkegewinn.**
   Gegner-Plattenpunkte zu druecken ist die Nutzer-Zielgroesse, nicht die
   Elo. Ein Mechanismus, der 1,5 Gegner-Plattenpunkte kostet und die
   Siegquote unveraendert laesst, hat gemessen NICHTS an der Spielstaerke
   geaendert -- er hat den Nutzer-Wunsch erfuellt. Das ist ein legitimes
   Ziel, sollte aber nicht als Staerke-Arbeit verbucht werden.

**Empfehlung**: Stufe 0 und Stufe 1 fahren (billig, mit klarer
Abbruchregel), die 2 x 200-Arena nur bei `stoerbar/total >= 5%` UND
erklaertem Nutzer-Go im vollen Wissen um die E3/E3b-Vorgeschichte. Wenn
die Zeit knapp ist und zwischen v2 und einem Staerke-Hebel gewaehlt werden
muss, gehoert die Zeit dem Staerke-Hebel: der beste realistische Ausgang
von v2 ist "stoert messbar, kostet nichts" -- ein Nutzer-Wunsch erfuellt,
kein Elo gewonnen.

---

## §9 ERGEBNIS Stufe 0 + Stufe 1 (2026-08-16)

Nutzer-Freigabe "bis Stufe 1, keinen Schritt weiter". Belegstelle:
`evaluations/artifacts/disruption_window_rate.json`, Treiber
`tools/disruption_window_rate.py`.

### §9.1 Abweichung vom vorregistrierten Verfahren -- vorab benannt

Die in §5.2 vorregistrierte Stufe 1 (Rust-Zaehlmodus + 200 Arena-Partien)
**ist NICHT gefahren worden**: sie braucht `maturin`-Bau, Wheel-Install und
einen Arena-Lauf, und alle drei waren fuer diesen Auftrag gesperrt (auf der
Maschine laeuft Sweep-Arm w1). **Gemessen wurde statt dessen ein
Offline-Ersatz** auf bereits aufgezeichneten Self-Play-Records -- kein Bau,
kein Wheel, keine Partie. Das ist eine ANDERE Messung als die
vorregistrierte; sie wird hier nicht als deren Erfuellung ausgegeben. Was
sie kostet, steht in §9.4.

**Quelle**: `data/ownership_corpus/selfplay_v21_own_a_*.pkl`, 300 Dateien
(~3000 Partien), Champion `v21_2d_brierbest`, **200 Sims**,
`add_root_noise=true`, `gumbel_top_m=16` (Manifest
`manifest_v21_own_a_20260814_141733.json`). Die spaetere Arena-Messung
liefe bei 400 Sims ohne Wurzelrauschen -- die Rate ist damit nicht
punktgenau uebertragbar.

**Auswertbare Wurzelentscheidungen: 261.270.** Davon 47.894 (18,3 %) mit
nur EINEM Kandidaten -- dort kann per Konstruktion kein Fenster entstehen.

### §9.2 Instrument und Gegenproben (VOR jeder Rate)

Drei Engine-Funktionen mussten fuer die Offline-Rechnung nach Python
portiert werden (`tiles_taken` <- `mcts.rs:573-595`, Strafleisten-Zuwachs
<- `mcts.rs:634-642`, `gegner_bedarf` <- `provocation.rs:753-779`). Eine
Portierung ist eine Behauptung, bis sie geprueft ist; der Treiber bricht
darum ab, bevor er eine Rate berichtet, wenn eine der beiden Gegenproben
nicht aufgeht:

| Gegenprobe | Ergebnis |
|---|---|
| **A -- Spiel-Log**: Stueckzahl und Strafleisten-Zuwachs gegen die vom echten Vollzug gebaute Log-Zeile (`execution.rs:38-46`) | **168 / 168 exakt**, 0 Abweichungen (nur `LARGE_FACTORY_SUN` erreicht -- das Log waechst zwischen aufeinanderfolgenden Records selten um genau eine Zeile) |
| **B -- `moon_top_counts`**: per Konstruktion exakt `tiles_taken` des globalen Mondzugs, aus einem vom Suchpfad unabhaengigen Serializer-Zweig (`serialize.rs:215-228`) | **41.918 / 41.918 exakt**, 0 Abweichungen |

Zwei weitere Instrumenten-Pruefungen:

- **Join Policy-Kandidat -> `valid_moves`** (fuer die Zugquelle, ohne die
  `tiles_taken` nicht rechenbar ist): 193.319 von 193.319 Kandidaten
  getroffen, Quelle je Schluessel eindeutig. Die naheliegende Join-Variante
  MIT `moon_order` scheitert zu 52 % -- die Suche zaehlt
  Moon-Order-Permutationen als eigene Kandidaten, `valid_moves` nicht.
  (Nebenbefund: `moon_order` steht auch an reinen SONNEN-Zuegen und ist
  KEIN Mondzug-Marker -- die Quelle steht nur in `valid_moves[].source`.)
- **untried-Abgrenzung**: nach Abzug der `v_mix`-Gruppe hatte KEINE
  einzige Entscheidung mehr als `gumbel_top_m = 16` Kandidaten
  (`verdaechtige_kandidatenmengen: 0`) -- die Trennung children/untried
  greift sauber.

### §9.3 Stufe 0 -- BESTANDEN

Anteil der Entscheidungen mit mindestens einem Nicht-Sieger im
Q-Aequivalenzfenster:

| eps | Fensterrate |
|---|---|
| 0,01 | **35,69 %** |
| 0,02 | 52,97 % |
| 0,03 | 62,20 % |

Das Instrument liefert; Stufe 0 ist bestanden. **Unabhaengige
Plausibilitaets-Kontrolle**: E3b hat mit seinem Besuchs-/SE-Fenster eine
Feuerrate von 36,52 % gemessen (`PREREG_denial_tiebreak.md` Zeilen
137-143) -- gezaehlt auf demselben Nenner-Zuschnitt (`total` enthaelt dort
wie hier auch Ein-Kandidaten-Entscheidungen, `net_mcts.rs:3056-3058`).
Da 36,52 % eine TAUSCH-Rate ist und eine Tauschrate nie ueber der
Fensterrate liegen kann, ist das E3b-Fenster mindestens so weit wie das
rohe eps=0,01-Fenster hier. Zwei voellig verschiedene Messwege
(prozessglobaler Rust-Zaehler in der Arena gegen Offline-Rechnung auf
Self-Play-Records) landen bei derselben Groessenordnung -- das spricht
fuer beide.

### §9.4 Stufe 1 (Offline-Ersatz) -- Abbruchschwelle NICHT unterschritten

Stoerfenster = Fenster-Kandidat, der (a) dem Gegner mehr von einer akut
gebrauchten Farbe wegnimmt als der Basiszug (`min(tiles_taken,
bedarf_akut)`, §4.1) UND (b) die eigene Strafleiste nicht staerker fuellt
(§3).

| eps | Stoerfenster (alle Entscheidungen) | nur Entscheidungen mit echter Wahl | ohne Strafleisten-Filter | Bedarf inkl. Kuppelzellen |
|---|---|---|---|---|
| **0,01** | **5,50 %** (14.374) | 6,74 % | 6,42 % | 5,95 % |
| 0,02 | 9,99 % (26.094) | 12,23 % | 11,66 % | 10,79 % |
| 0,03 | 13,57 % (35.458) | 16,62 % | 15,83 % | 14,52 % |

Weitere Befunde:

- **Runde 5 traegt exakt 0 bei** (36.060 Entscheidungen = 13,8 % des
  Nenners). Erwartet und strukturell: dort entscheidet der exakte
  Alpha-Beta-Solver, der Gumbel-Baum wird nie gebaut
  (`net_mcts.rs:4345-4347`). Auf die Runden 1-4 allein bezogen liegt die
  Rate bei eps=0,01 bei **6,38 %**.
- Ueber die Runden 1-4 ist die Rate flach (bei eps=0,01: 3.114 / 4.306 /
  3.459 / 3.495) -- kein Rundenfenster, in dem sich Stoerung ballt.
- Der Strafleisten-Filter aus §3 entfernt rund ein Siebtel der sonst
  qualifizierten Faelle (6,42 % -> 5,50 %). Er ist also kein Papiertiger:
  in etwa jedem siebten Stoerkandidaten HAETTE die Stoerung zusaetzlichen
  Boden gekostet -- genau der v1-Fehler.
- Der Kuppelzellen-Anteil des `gegner_bedarf` aendert die Rate kaum
  (5,95 % gegen 5,50 %). Die in §4.1 als HERLEITUNG markierte Annahme
  ("der Raster-Anteil ueberdeckt die akute Nachfrage") ist damit fuer die
  RATE widerlegt; fuer die Zielfarben-WAHL bleibt sie ungeprueft.

**Was diese Zahl NICHT ist** (Grenzen des Ersatzverfahrens):

1. Besuchszahlen sind nicht aufgezeichnet -> es ist ein ROHES eps-Fenster
   (E3-Definition), nicht das E3b-Kriterium. Nach §9.3 ist das
   E3b-Fenster eher WEITER als eps=0,01; die 5,50 % sind fuer den
   geplanten Mechanismus damit eher eine Unter- als eine Obergrenze.
2. Der Basiszug ist `argmax(completed-Q)`, nicht der tatsaechlich
   gespielte (besuchsbasierte) Zug.
3. 200 Sims mit Wurzelrauschen statt 400 ohne.

### §9.5 Verdikt nach der vorregistrierten Abbruchregel

Die Abbruchregel lautete: `stoerbar/total < 5 %` -> ohne Arena schliessen.
Bei eps=0,01 liegt der Anteil bei **5,50 %**, bei groesserem Fenster
deutlich darueber. **Die Abbruchregel greift NICHT.** Der Punkt wird also
nicht geschlossen -- v2 bleibt OFFEN.

**Hier wird gestoppt.** Die Entscheidung ueber Stufe 2 (Bau des
Zaehlmodus, danach die 2 x 200-Arena) trifft der Nutzer. Zur Einordnung
gehoert dazu, ohne Beschoenigung:

- 5,50 % ist knapp ueber der Schwelle, und die Schwelle war als
  "darunter kann die Arena es ohnehin nicht aufloesen" begruendet. Knapp
  darueber heisst nicht "gut aufloesbar", sondern "gerade eben nicht
  ausgeschlossen".
- E3b hat bei einer SECHSMAL hoeheren Eingriffstiefe (36,52 % getauschte
  Entscheidungen) keinen Gewinn erzeugt, sondern -4,75pp. Ein Mechanismus,
  der nur jede achtzehnte Entscheidung beruehrt, muesste pro Eingriff
  entsprechend mehr leisten.
- Meine Einschaetzung aus §8 aendert sich durch diese Zahlen **nicht**:
  die Fensterrate war nie das Problem, das Problem war und ist die
  Wirksamkeit des Tauschs.

### §9.6 Korrekturen am Plan (aus der Messung gelernt)

1. **§3 ist an einer Stelle falsch**: dort steht, `ueberlauf_von` liefere
   `0` fuer Bodenzuege. Ein Bodenzug legt ALLE genommenen Fliesen auf die
   Strafleiste; `0` waere die falsche Zahl und wuerde Bodenzuege als
   schadensfrei durchwinken. Der Treiber rechnet bereits korrekt
   (`floor_zuwachs`: `n` bei `row < 0`). Beim Bau ist die Funktion so und
   nicht wie in §3 beschrieben zu implementieren.
2. **Runde 5 gehoert explizit aus dem Geltungsbereich**: kein Gumbel-Baum,
   keine Wurzelkinder, kein Tie-Break. Das ist kein Mangel, sondern die
   Bestandsentscheidung fuer den exakten Solver -- in §4.1 war es nicht
   benannt.
3. Der Join Policy -> `valid_moves` darf `moon_order` NICHT verwenden
   (§9.2); wer die Offline-Auswertung spaeter wiederholt, faellt sonst
   auf 52 % Fehltreffer herein.

---

## §10 Stufe 1 (die ECHTE, vorregistrierte): GEBAUT, Messung eingetaktet

Nutzer-Auftrag 2026-08-16: den in §5.2 vorregistrierten Trockenlauf-
Zaehlmodus in der laufenden Engine nachreichen. Stand dieses Abschnitts:
**gebaut und getestet, NICHT gemessen** -- die Messung haengt an der
Maschine (siehe §10.4).

### §10.1 Was gebaut ist

| Baustein | Stelle |
|---|---|
| Zaehlkern (rein lesend, ohne Rueckgabe) | `net_mcts.rs::color_denial_probe_with` |
| Einhaengung | `net_mcts.rs::select_final_root_child`, VOR `apply_denial_tiebreak`, Rueckgabewert unveraendert |
| Aequivalenz-Kriterium | `denial_uncert_qualifies` (E3b: Besuchs-Gate + Zwei-Anteils-SE) -- wiederverwendet, nicht nachgebaut |
| Rangkriterium | `provocation.rs::stoer_bewertung` = `min(tiles_taken, gegner_bedarf_akut[farbe])` |
| Ueberlauf-Filter | `provocation.rs::strafleisten_zuwachs` (Bodenzug = volle Stueckzahl, §9.6 Punkt 1) |
| Stueckzahl | `mcts.rs::tiles_taken`, von `fn` auf `pub(crate) fn` gehoben -- wiederverwendet |
| Knoepfe | `MOSAIC_COLOR_DENIAL_PROBE_Z` (Default 0,0 = aus), `..._MIN_VISIT_FRAC` (0,5); beide in `knob_registry.rs` als `Diagnose` |
| Python-Bindung | `lib.rs::color_denial_probe_stats` / `reset_color_denial_probe_stats` |
| Treiber | `tools/color_denial_probe.py` (Messmodus + `--golden`) |

**BEWUSST eigene Knoepfe** statt `MOSAIC_DENIAL_UNCERT_Z`: dessen Setzen
wuerde den E3b-Tie-Break AKTIVIEREN und damit das Spielverhalten aendern --
genau das, was der Zaehlmodus nicht darf. Der Treiber setzt beide
E3/E3b-Regler explizit auf 0, statt auf einen sauberen Prozess zu hoffen.

### §10.2 Tests

Sechs neue Tests, alle gruen: drei zum Zaehlmodus (`z=0` zaehlt gar nichts;
Fenster+Stoerbarkeit werden erkannt; **Gegenprobe**: derselbe Aufbau mit
Zielreihe 1 statt 6 erzeugt Ueberlauf und darf NICHT als stoerbar zaehlen)
und drei zu den Provokations-Helfern (Bedarfs-Aufteilung akut/voll als
Bestandsschutz der Refaktorierung, Bodenzug-Strafleiste, Deckelung der
Stoerwirkung am Bedarf).

`cargo test --lib` im Hauptbaum: **425 passed, 0 failed, 19 ignored**
(Lauf zu einem Zeitpunkt, an dem der Baum konsistent war). Da ein zweiter
Agent parallel `net.rs`/`net_mcts.rs` umbaut (Ownership-Kopf-Verdrahtung)
und der Baum zwischenzeitlich nicht uebersetzte, sind die sechs Tests
zusaetzlich in einem ISOLIERTEN Worktree auf sauberer Basis gelaufen
(letzter gemeinsamer Stand + ausschliesslich die eigenen Hunks):
**6 passed, 0 failed**. Die dortigen 21 Fehler der Gesamtsuite sind
ausnahmslos `models/*.onnx nicht ladbar` -- im Worktree fehlt das
gitignorierte `models/`-Verzeichnis, kein Codebefund.

### §10.3 Byte-Identitaet: der Nachweis ist vorbereitet, nicht behauptet

`tools/color_denial_probe.py --golden` spielt dieselbe Partienzahl mit
demselben Seed zweimal -- Zaehler AUS und AN -- in **zwei getrennten
Kindprozessen** (die Regler sind `OnceLock`, ein Umschalten im selben
Prozess waere wirkungslos) und vergleicht die kompletten Arena-JSONs
zeichenweise. Abweichung = Fehlschlag mit Partie-Index.

Konstruktiv ist der Eingriff Null: `color_denial_probe_with` gibt nichts
zurueck, mutiert `nodes` nicht, zieht keinen Zufall und ruft kein Netz --
alle Eingaben (Besuche, completed-Q, Wurzelzustand) liegen nach dem
Baumbau bereits vor. Das ist aber ein Argument, kein Beleg; der Beleg ist
der Golden-Lauf nach dem Wheel-Install.

### §10.4 Warum die Messung noch nicht laeuft (und was sie braucht)

Das Wheel ist gebaut (`maturin build --release`, erfolgreich), aber
**NICHT installiert**. Die installierte `.pyd` ist zweifach belegt:

1. **Sweep-Arm w1** (`train.py --name v21_2d_own_w1`, PID 12532, gestartet
   00:56). Der Vorgaenger-Arm w05 lief 3 h 18 min (16:43 -> 20:01), das
   Ende ist also gegen ~04:15 zu erwarten. Ein harness-getrackter Waechter
   auf den Prozess laeuft.
2. **`server.py`** (drei Prozesse, gestartet 01:08) -- importiert
   `mosaic_rust` ebenfalls und blockiert `pip install` unabhaengig vom
   Training. Der Server wird NICHT von mir beendet; das Herunterfahren ist
   eine Nutzer-/Koordinator-Entscheidung.

**WICHTIG zur Wahl des Wheels**: es ist bewusst NICHT aus dem Hauptbaum
gebaut, sondern aus dem isolierten Worktree = letzter gemeinsamer Stand
PLUS ausschliesslich dem Zaehlmodus. Grund: der Hauptbaum traegt gerade die
halbfertige Ownership-Kopf-Verdrahtung eines anderen Agenten. Ein daraus
gebautes Wheel wuerde die Paritaetsprobe (Hash `8c6684ff...`) mit hoher
Wahrscheinlichkeit brechen -- und zwar wegen einer FREMDEN Aenderung, was
den Zaehlmodus faelschlich als Verhaltensaenderung erscheinen liesse.

### §10.5 Ablauf nach Freiwerden der `.pyd` (vorab festgeschrieben)

1. Wheel installieren (`pip install --force-reinstall --no-deps` aus dem
   Worktree-`target/wheels/`).
2. `tools/parity_probe.py` -- Hash `8c6684ff...` MUSS halten. Haelt er
   nicht, wird NICHT gemessen, sondern die Ursache geklaert.
3. `tools/color_denial_probe.py --golden --n-games 12` -- Byte-Identitaet.
4. `tools/color_denial_probe.py --n-games 200 --net-sims 400
   --heur-sims 150` (wie §5.2 vorregistriert), Ausgabe nach
   `evaluations/artifacts/color_denial_probe.json`.
5. Verdikt nach derselben Abbruchregel (<5 % -> geschlossen), dann **STOPP**
   -- Stufe 2 bleibt Nutzer-Entscheidung.

### §10.6 Der eigentliche Erkenntniswert: der Vergleich

Die Live-Zahl ist gegen den Offline-Ersatz aus §9.4 (5,50 % bei eps=0,01)
zu halten. Weichen sie ab, ist das ein Befund ueber die
Offline-Rekonstruktion, nicht ueber den Mechanismus. **Vier bekannte
Unterschiede, vorab benannt, damit keiner davon nachtraeglich als
Erklaerung erfunden wird:**

1. **Aequivalenz-Definition**: live das E3b-Kriterium (Besuchs-Gate +
   SE-Fenster), offline ein rohes eps (Besuchszahlen fehlen in den
   Records). Nach der Kalibrierung in §9.3 ist das E3b-Fenster eher WEITER
   als eps=0,01 -- erwartet wird die Live-Zahl also eher HOEHER.
2. **Basiszug**: live der echte Gumbel-Sieger (besuchsbasiert), offline
   `argmax(completed-Q)`.
3. **Sims**: live 400, offline 200.
4. **Gegner/Rauschen**: live Arena gegen Heuristik@150 ohne Wurzelrauschen,
   offline Self-Play mit Wurzelrauschen.

Eine grobe Uebereinstimmung waere eine Bestaetigung der drei nach Python
portierten Engine-Funktionen; eine grosse Abweichung waere ein Grund, die
Offline-Methodik kuenftig nicht mehr als Ersatz zuzulassen.

---

## §11 ERGEBNIS Stufe 1 (live, 2026-08-16): Abbruchregel greift NICHT

Belegstellen: `evaluations/artifacts/color_denial_probe.json` (Hauptlauf),
`evaluations/artifacts/color_denial_probe_200sims.json` (Sim-Kontrolle).
Treiber `tools/color_denial_probe.py`.

### §11.1 Voraussetzungen -- selbst geprueft, nicht uebernommen

- **Wheel installiert** (aus dem Hauptbaum, inkl. der inzwischen
  vollstaendigen Ownership-Verbraucher-Verdrahtung des anderen Agenten).
  Der isolierte Worktree-Bau aus §10.4 wurde damit hinfaellig und NICHT
  installiert.
- **Paritaetsprobe selbst gefahren**: `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`,
  Exit 0, "Defaults sind byte-identisch zum Bestand". Damit ist belegt,
  dass weder der Zaehlmodus noch der Ownership-Verbraucher (Default 0) das
  Suchverhalten anfasst.
- **Byte-Identitaets-Nachweis gefahren** (§10.3): `--golden --n-games 12`,
  Seed 20260901, Zaehler AUS gegen AN in getrennten Prozessen ->
  **BYTE-IDENTISCH**, 2127 Zeichen Arena-JSON exakt gleich. Die Zusicherung
  "reiner Zaehlmodus" ist damit belegt, nicht behauptet.

### §11.2 Die Zahlen

Champion `v21_2d_brierbest` vs Heuristik@150, je 200 Partien, z=1,0, f=0,5.

| Lauf | Entscheidungen | Fenster offen | **stoerbar** | Netz-Siege |
|---|---|---|---|---|
| **400 Sims** (vorregistriert), Seed 20260901 | 8.915 | 7.950 = **89,18 %** | 680 = **7,63 %** | 157/200 |
| 200 Sims (Kontrolle), Seed 20260902 | 8.892 | 8.315 = 93,51 % | 707 = **7,95 %** | 143/200 |

Ueber die acht Bloecke des Hauptlaufs ist die Rate stabil (7,66 / 7,43 /
8,13 / 8,17 / 7,94 / 7,86 / 7,68 / 7,63 % kumulativ) -- keine Drift, kein
Extremblock.

### §11.3 Verdikt

Die vorregistrierte Abbruchregel (`stoerbar/total < 5 %` -> ohne Arena
schliessen) **greift nicht**: 7,63 % im vorregistrierten Lauf, 7,95 % in der
Kontrolle. v2 bleibt OFFEN.

**Hier wird gestoppt.** Die Entscheidung ueber Stufe 2 (Bau des echten
Tie-Breaks, danach die 2 x 200-Arena) trifft der Nutzer. Die Einordnung aus
§9.5 gilt unveraendert: eine Rate von 7,6 % ist kein Wirksamkeitsnachweis.
E3b hat bei 36,52 % getauschten Entscheidungen -4,75pp gekostet.

### §11.4 Der Vergleich Offline gegen Live -- ein Befund ueber die Methode

| | Fenster | stoerbar |
|---|---|---|
| Offline, rohes eps=0,01 | 35,69 % | 5,50 % |
| Offline, rohes eps=0,02 | 52,97 % | 9,99 % |
| Offline, rohes eps=0,03 | 62,20 % | 13,57 % |
| **Live, E3b-Kriterium, 400 Sims** | **89,18 %** | **7,63 %** |
| Live, E3b-Kriterium, 200 Sims | 93,51 % | 7,95 % |

Drei Befunde, in dieser Reihenfolge:

1. **Die entscheidungsrelevante Zahl haelt.** 5,50 % offline gegen 7,63 %
   live -- gleiche Groessenordnung, gleiche Seite der 5 %-Schwelle. Die
   Offline-Rekonstruktion haette hier zum selben Verdikt gefuehrt.
2. **Die Fensterstatistik haelt NICHT, um den Faktor 2,5.** Das
   E3b-Fenster steht in fast NEUN von zehn Wurzelentscheidungen offen; das
   roheste getestete eps=0,03 kam auf 62 %. Die in §9.3 gezogene Schranke
   ("E3b-Fenster mindestens so weit wie eps=0,01") war richtig, aber viel
   zu schwach -- sie liess offen, wie extrem der Unterschied ist.
3. **Sims erklaeren die Luecke NICHT.** Der dritte der vier vorab
   benannten Stoerfaktoren (§10.6) ist ausgeraeumt: 200 statt 400 Sims
   bewegen die Rate um 0,32pp (7,63 -> 7,95 %), waehrend die Offline-Live-
   Luecke 2,13pp betraegt.

**Die eigentliche Lehre** ist die Kombination aus 1 und 2: das Fenster
wird um den Faktor 2,5 weiter, die Stoerbarkeit steigt aber nur um den
Faktor 1,39 -- und liegt sogar UNTER dem, was die Offline-Rechnung bei
vergleichbarer Fensterbreite vorhersagt (bei eps=0,03 und nur 62 %
Fensterrate schon 13,57 %). Der begrenzende Faktor ist also NICHT das
Aequivalenzfenster, sondern die Stoerbedingung selbst.

*(INTERPRETATION, nicht gemessen)*: plausibel macht das der Besuchs-Gate
`N(a) >= 0,5*N(b)`. Er laesst nur Kandidaten zu, die die Suche ohnehin
schon stark besucht hat -- typischerweise strukturell aehnliche Zuege
(gleiche Farbe, benachbarte Reihen), die sich in ihrer Stoerwirkung kaum
unterscheiden. Ein rohes eps ohne Besuchs-Gate laesst dagegen auch
strukturell ANDERE Zuege zu, bei denen ein Unterschied in der Stoerwirkung
wahrscheinlicher ist. Zwei Fensterdefinitionen unterscheiden sich hier also
nicht nur in der Breite, sondern in der ART der zugelassenen Kandidaten.
Diese Deutung ist NICHT geprueft; sie waere durch einen Live-Lauf mit
rohem eps (ohne Besuchs-Gate) zu testen -- nicht Teil dieses Auftrags.

**Konsequenz fuer die Methodik**: die Offline-Rekonstruktion aus vorhandenen
Records taugt als billiger Groessenordnungs-Schaetzer fuer die
Entscheidungszahl, aber NICHT als Ersatz fuer die Live-Messung, sobald eine
Aussage ueber das Fenster selbst getroffen werden soll. Wer sie kuenftig
einsetzt, sollte das ausdruecklich als Vorab-Schaetzung deklarieren -- so
wie §9.1 es getan hat.

## §12 VERDIKT: UEBERHOLT

**Eingetragen 2026-08-18 (aus dem Statuskopf in den Koerper verschoben bei
der Kopf-Kuerzung 2026-08-28).** Ersetzt das "v2 bleibt OFFEN" aus §11.3.

Die Messungen bleiben unveraendert gueltig: Stufe 0 bestanden, Stufe 1 echt
gefahren (§11), Abbruchschwelle 5 % nicht unterschritten.

OFFEN war nach §11.3 allein die **Nutzer-Entscheidung ueber Stufe 2** (Bau
des echten Tie-Breaks). Diese Einzelentscheidung entfaellt: laut STATUS.md,
Abschnitt OFFENE ENTSCHEIDUNGEN, gehoert der Stoerungs-Baustein Stufe 2
inzwischen zum **Moon-Order-Kopf** und wird nicht mehr fuer sich entschieden.

**Zustand des Bestands: nichts gebaut, kein Knopf im Code.** Der Zaehlmodus
aus Stufe 1 war Messinstrument, kein Spielverhalten.
