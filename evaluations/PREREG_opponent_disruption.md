<!-- STATUS: ENTSCHIEDEN | Frage: Stoert ein Plattenbauer-Baustein nach Runde 4 den Gegner wirksam ueber die oeffentliche Farbzaehlung (verbleibende_farben) -- bei ~gleichwertigen eigenen Zuegen die Fliese nehmen, die dem Gegner ausgeht? | Beleg: **ENTSCHIEDEN 2026-08-15, ABLEHNUNG** (eigener Abschnitt 7 Ergebnis, Verdikt in 7.5). MOSAIC_OPPONENT_DISRUPTION bleibt Default AUS und wird in KEINEM Training-, Gating- oder Korpus-Lauf aktiviert. Der Code bleibt stehen (LOESCHVERBOT); der Aufrufpfad ist erreichbar und per Default inert, deshalb kein zusaetzliches allow(dead_code). Bei Wiederaufnahme sind ZWEI Konstruktionsfehler zu BEHEBEN, nicht bloss zu messen: vorzugszug_fuer_farbe braucht eine Ueberlauf-Pruefung, und stoerungs_vorzug braucht eine echte Gleichwertigkeits-Bedingung statt einer unbedingten Uebersteuerung. Beides sind neue Bausteine. Nachfolge-Versuch mit anderem Ansatzpunkt: PREREG_opponent_disruption_v2.md. -->

# PREREG: Gegner-Stoerung ueber Farbzaehlung ("Stoerungs-Baustein")

Stand 2026-08-14, PLAN (Nutzer-Go: *"loslegen mit der vorbereitung"*).
Vorbereitungsphase: nur PREREG + Bau + `cargo test --lib`. **Keine
Arena-Messung, kein Wheel-Install** — auf der Maschine laeuft parallel der
`ownership_weight`-Sweep (die installierte `.pyd` ist gesperrt); die Messung
selbst wird erst NACH Sweep-Ende vom Koordinator freigegeben. Durchgehend
Plan-Zeitform fuer den Messteil, Ist-Zeitform nur fuer bereits Gebautes.

## §1 Herkunft und Ist-Stand (GEPRUEFT am Code)

Nutzer-Domaenenwissen, `docs/domain_knowledge.md` Abschnitt "Spielstrategie
aus Nutzer-Praxis", Punkt 4 ("BAUSTEIN (Nutzer-Auftrag): Gegner-Stoerung
ueber die Farbzaehlung", Zeilen 284-293):

> Dieselbe oeffentliche Zaehlung (`verbleibende_farben`), die die eigene
> Vollendbarkeit prueft, verraet auch, welche knappe Farbe der GEGNER fuer
> seine Struktur braucht ... Ein Bauer, der bei ~gleichwertigen eigenen
> Zuegen die Fliese nimmt, die dem Gegner ausgeht, stoert aus reiner
> Buchhaltung -- kein Kopf, keine Vorhersage. Eingeplant als
> Plattenbauer-Baustein NACH Runde 4 (erst die eigene Vollendung, dann die
> Stoerung; beides nutzt dieselbe Zaehlung).

Bereits vorhanden und wiederverwendet (kein Neubau):
- `provocation.rs::verbleibende_farben` (Zeile 588) — Gesamtvorrat minus
  ueberall SICHTBAR verbautes/ausliegendes Material je Farbe.
- `provocation.rs::noch_erreichbare_farben` (Zeile 654) — dieselbe Idee,
  aber nur ECHT verlorenes Material abgezogen (Strafleiste, platzierte
  Kuppelzellen BEIDER Spieler, PLUS Musterreihen-Fliesen des GEGNERS) —
  laut eigener Doku dort die fuer Vollendbarkeits-Fragen richtige Zahl
  (§14-Lehre: `verbleibende_farben` zaehlte Fabrik-Kacheln faelschlich als
  "verbaut" und machte tiefe Reihen systematisch scheinunvollendbar).
- `provocation.rs::geforderte_farbe` (Zeile 161) — Farbforderung einer
  Kuppelzelle fuer ein BELIEBIGES `PlayerBoard` (nicht nur `state.
  current_player`), `None` fuer Wild/Special/leeren Slot.
- `board.rs::PatternLine` (Zeile 9): `color: Option<TileColor>` (die
  Musterreihe ist auf GENAU eine Farbe festgelegt, sobald sie eine Fliese
  traegt — Spielregel, kein Modell), `capacity()`/`spaces_left()` (Zeilen
  31-42).
- `plate_builder.rs::drafting_vorzug` (Zeile 245) — der EINE Dispatch-Punkt,
  den die vereinheitlichte Spielschleife (`PREREG_unified_game_loop.md`,
  gelandet) an ALLEN VIER Spielpfaden BEIDSEITIG aufruft (verifiziert im
  Rahmen von Commit `5992f38`, "Bauer-Vorzug in run_net_self_play
  verdrahtet"). Ein Vorzug, der HIER angehaengt wird, muss `self_play.rs`
  NICHT anfassen — genau der Grund, warum dieser Auftrag ohne
  Spielschleifen-Aenderung auskommt.

## §2 Mechanismus (GEBAUT -- Zeilen unten sind der Ist-Stand nach dem Bau)

**Eingaben** (alle oeffentlich, GameState-Felder):
1. Gegner-Musterreihen: jede NICHT-volle Reihe mit `color = Some(c)` braucht
   `spaces_left()` weitere Fliesen der Farbe `c`.
2. Gegner-Kuppelraster: jede OFFENE (nicht `is_filled()`) Zelle mit
   `required_color = Some(c)` (Normal-Zelle) braucht eine Fliese der Farbe
   `c`. Wild/Special liefern `None` (siehe `geforderte_farbe`-Doku) und
   fallen damit STRUKTURELL heraus — genau die Einschraenkung, in der "die
   aktiven Wertungskriterien" implizit steckt: nur Normal-Zellen tragen
   ueberhaupt eine Farbforderung, unabhaengig davon, welche 3 der 8 Platten
   gerade gezogen sind.
3. Scharfe/Skanzitaet: `noch_erreichbare_farben(state, aktueller_spieler)`
   (Wiederverwendung, kein Neubau) — je kleiner, desto knapper.

**Ausgabe**: `gegner_bedarf(state, aktueller_spieler) -> [i64; 5]`, Summe aus
1+2 je Farbe (neue Funktion, `provocation.rs`, gleiche Struktur wie
`verbleibende_farben`).

**Zielfarbe**: unter den Farben mit `bedarf > 0` die mit dem KLEINSTEN
`noch_erreichbare_farben`-Wert (knappste), Gleichstand nach hoechstem
`bedarf`, dann nach Farbindex (stabil, keine Streuung noetig — der
Mechanismus soll deterministisch aus der Buchhaltung folgen, nicht
gewuerfelt sein).

**Zielzug**: neue Funktion `vorzugszug_fuer_farbe(state, farbe) ->
Option<Action>` (`provocation.rs`) — Kern-Kopie von `vorzugszug_fuer_spalte`
(Zeile 484) OHNE dessen Spalten-/`geforderte_farbe`-Filter (Stoerung zielt
auf IRGENDeine eigene Platzierung dieser Farbe, nicht auf eine bestimmte
Zielspalte) — unter den legalen Zuegen mit `m.take.color == farbe` gewinnt
die am weitesten gefuellte eigene Musterreihe (Tie-Break: kleinste Reihe),
identischer Tie-Break-Geschmack wie das Vorbild, aus demselben Grund dort
dokumentiert ("kein Ueberlauf-Kriterium, `TakeAction` traegt keine
Stueckzahl").

**Einhaengepunkt**: `plate_builder::drafting_vorzug` (Zeile 245) bekommt
einen `.or_else(|| stoerungs_vorzug(state))`-Zweig NACH dem bestehenden
`aktiver_bauer(...).and_then(...)`-Aufruf — exakt "NACH Runde 4" im
Sinne von "erst die eigene Vollendung [des jeweils aktiven Bauers], dann
die Stoerung [als Fallback, wenn der aktive Bauer fuer DIESEN Zug keinen
Vorschlag hat]". `stoerungs_vorzug` selbst prueft den eigenen Knopf (§3)
und `state.round_number <= 4` (Runde 5 hat ihren exakten Solver, wie beim
Vorbild `vorzugszug_fuer_spalte`) — WIRKT DAMIT AUCH OHNE gesetztes
`MOSAIC_PLATTENBAU`/`MOSAIC_SPALTENBAU`, ein eigenstaendiger Baustein, kein
Kriterium-Add-on.

**Beidseitigkeit (Nutzer-Vorgabe, explizit gewollt)**: da die
vereinheitlichte Schleife `drafting_vorzug` fuer BEIDE Spieler aufruft
(Self-Play: `NetSelfPlayAgent`, siehe §1), stoeren sich bei aktivem Knopf
BEIDE Seiten gegenseitig — kein Gate auf `pi==net_board` o.ae. Genau die
Nutzer-Spielpraxis (jeder Mensch stoert den Gegner UND wird gestoert).

## §3 Knopf

`MOSAIC_OPPONENT_DISRUPTION` — Task-#28-Muster: `OnceLock`-gecacht,
Default (unset) = AUS, jeder nicht-leere Wert ausser `"0"` = AN (gleiches
Parsing wie `column_build::aktiv_env`). Reiner Diagnose-Schalter, **niemals
im Gating** (wie alle Plattenbauer-Knoepfe seit `PREREG_provocation.md`).
Bei AUS: `stoerungs_vorzug` liefert sofort `None`, `drafting_vorzug`s
`.or_else`-Kette ist dann exakt der Bestand vor diesem Auftrag —
Bestandsschutz, per Paritaetsprobe zu pruefen (NACH Sweep-Ende, siehe §6).

## §4 Messplan (VORAB festgeschrieben -- Ausfuehrung + Zahlen in §7)

**Messgroesse (primaer)**: GEGNER-Plattenpunkte, gepaart (Knopf AN vs. AUS,
identische Seeds) — Nutzer-Zielgroesse ist STOEREN, nicht die eigene
Punktzahl. Da beide Seiten stoeren (§2, Beidseitigkeit), wird "Gegner"
bezogen auf EIN festes Brett (z.B. Spieler 0) gemessen, nicht auf
"Sieger/Verlierer" (sonst Konfundierung mit dem Spielausgang selbst).

**Nebenmessung (pflicht)**: eigene Plattenpunkte + Siegquote (McNemar) —
ein Stoerungs-Baustein, der die eigene Struktur beschaedigt oder Siege
kostet, ist kein Gewinn, selbst wenn er den Gegner drueckt (Kosten-Nutzen,
wie bei jedem anderen Baustein in `PREREG_provocation.md`).

**Replikation ist PFLICHTTEIL, nicht optional** — Lehre aus §17
(Special-Baustein-Replikation) und der Lambda-Kampagne
(`project_lambda_sweep_result`, Vorzeichenwechsel zwischen Laeufen): jeder
Erstbefund WIRD auf einem zweiten, frischen Seed-Satz repliziert, BEVOR er
als Ergebnis gilt. Gepoolte Entscheidung ueber beide Laeufe (nicht "Lauf 1
sieht gut aus, fertig"). Block-Ebene fuer alle Signifikanztests
(`feedback_arena_block_correlation`: Paar-SEs unterschaetzen sonst massiv).

**Vorab-Deutungsregel fuer das Vorzeichen-Risiko** (festgeschrieben VOR
jeder Zahl, damit keine nachtraegliche Umdeutung moeglich ist): der
k6-Kuppeldraft-Stoerkanal (`PREREG_provocation.md` §19) wirkte INVERS — der
Gegner wurde durch die vermeintliche Stoerung BESSER (-11,10 -> -6,60
eigene Spezialfeld-Punkte des GEGNERS), nicht schlechter. **Wird hier
ebenfalls beobachtet, dass der Gegner unter aktivem Knopf BESSERE
Plattenpunkte erzielt als ohne, ist das ein ABLEHNUNGS-, kein
Interpretationsfall** — kein Nachbessern der Zielfarben-Auswahl mitten in
der Messung, sondern Befund + Ablehnung + `#[allow(dead_code)]` (LOESCHVERBOT,
wie bei `kuppeldraft_vorzug_k6`).

**Arme (Entwurf, Details bei Freigabe zu praezisieren)**:
- A: Knopf aus (Referenz).
- B: Knopf an, `run_net_self_play` (beidseitig, Nutzer-Praxis-Fall).
- Optional C: Knopf an, einseitig (`MOSAIC_SPALTENBAU`-Nachbau-Aequivalent
  waere hier ein Test-Override, siehe §5) — nur falls B einen Effekt zeigt
  UND unklar ist, ob er von der eigenen oder der gegnerischen Stoerung
  kommt.

**Seeds/Sample-Groesse**: an die zuletzt genutzte Konvention dieser
Kampagne angelehnt (20-30 Partien pro Lauf, zwei Laeufe = Erst+Replik) —
exakte Zahl bei Freigabe, kein Vorgriff auf eine Messung, die noch nicht
laufen darf.

## §5 Bau (GEBAUT, dieser Auftrag)

Neue Funktionen, alle `provocation.rs` (Erweiterung der bestehenden
"Runde 3: zaehlbare Versorgung"-Sektion, gleiche Farb-Buchhaltungs-Familie):
- `disruption_aktiv_env()`/`disruption_aktiv()` (Zeilen 701/729) — Knopf-
  Lesefunktion, `OnceLock`-Cache + `#[cfg(test)]`-Thread-Local-Override
  (`set_disruption_override_for_test`), exaktes Muster `column_build::
  aktiv_env`/`ist_aktiv` (der `OnceLock` allein waere sonst prozessweit
  fuer ALLE parallelen `cargo test`-Threads fixiert).
- `gegner_bedarf(state, aktueller_spieler) -> [i64; 5]` (Zeile 753).
- `vorzugszug_fuer_farbe(state, farbe) -> Option<Action>` (Zeile 791).
- `stoerungs_vorzug(state) -> Option<Action>` (Zeile 832) — fasst die drei
  obigen zusammen: Knopf-Gate, Rundenfenster, Zielfarben-Wahl, Zielzug.

`plate_builder.rs::drafting_vorzug` (Zeile 255): `.or_else(||
crate::provocation::stoerungs_vorzug(state))`-Zweig NACH dem bestehenden
`aktiver_bauer(...).and_then(...)`-Aufruf angehaengt (§2).

**Unit-Tests** (alle `provocation.rs::vorzugszug_tests`, 5 neu):
- `gegner_bedarf_zaehlt_musterreihen_und_offene_kuppelzellen_des_gegners` —
  begonnene Musterreihe (2 offene Plaetze) + eine offene + eine GEFUELLTE
  Kuppelzelle des Gegners; erwartete Zahlen von Hand nachgerechnet.
- `stoerungs_vorzug_ist_aus_ohne_knopf` — Bestandsschutz bei Default.
- `stoerungs_vorzug_wirkt_nicht_nach_runde_4` — Bestandsschutz bei Runde 5.
- `stoerungs_vorzug_waehlt_die_vom_gegner_gebrauchte_knappe_farbe`
  (**Kill-Probe, GEPRUEFT dass sie etwas prueft**): Gegner braucht Rot UND
  Gelb, Rot ist knapp (11/13 sichtbar verbaut), Gelb reichlich — muss Rot
  waehlen. Scarcity-Sortierschluessel testweise auf eine Konstante
  sabotiert (`(erreichbar[i], ...)` → `(0i64, ...)`) → Test schlaegt
  nachweislich fehl ("bekam Gelb, erwartet Rot"); Fix restauriert → gruen.
- `drafting_vorzug_integration_ohne_stoerungs_knopf_ist_bestand` —
  Dispatch-Ebene, Knopf aus.

**`cargo test --lib`**: 415/0/18 (410 Vorher-Stand dieser Sitzung + 5 neu;
die Vorher-Zahl selbst ist NICHT die zuletzt dokumentierte Projekt-Baseline
419/0/20 — zwei parallel arbeitende Agenten aendern gerade `net.rs`/
`lib.rs`/`Cargo.toml`/`tools/check_conventions.py`, die geteilte Test-Menge
ist also ein bewegtes Ziel; entscheidend ist ausschliesslich 0 failed vor
und nach diesem Bau). `maturin build --release`: erfolgreich (Wheel liegt
in `scratchpad/target_decke/wheels/`), **NICHT installiert** — die aktive
`.pyd` gehoert dem parallel laufenden `ownership_weight`-Sweep.

## §6 Abnahme

1. Wheel-Install + `tools/parity_probe.py` — Hash `8c6684ff...` haelt (vom
   Koordinator bestaetigt, nach dem `ownership_weight`-Sweep, enthaelt
   Commit `b28a74a`). GEPRUEFT erneut vor der Messung: haelt.
2. Der volle Messplan aus §4 (Erst- + Replikationslauf, gepoolt) — siehe §7.

## §7 Ergebnis (2026-08-15) — **ABLEHNUNG**

### §7.1 Aufbau (wie vorregistriert)

`tools/paired_arena_env_ab.py --env-name MOSAIC_OPPONENT_DISRUPTION --arms 0
1 --control 0 --net-sims 400 --heur-sims 150 --threads 8 --log-games`,
Champion `v21_2d_brierbest` (Netz = Brett 0, `net_arena_match` — GEPRUEFT
einseitig: `play_net_game`s `pi==net_board`-Gate, siehe §1 — die Heuristik
liest `MOSAIC_OPPONENT_DISRUPTION` nicht, die Zuordnung "wer stoert wen" ist
damit eindeutig). Lauf 1: Basis-Seed 20260815, n=20. Lauf 2 (PFLICHT-
Replikation): Basis-Seed 20260822 (frisch), n=20. Auswertung:
`tools/probes/opponent_disruption_analysis.py` (neu, reine Analyse — liest
`PATTERNS`/`ROUND_PREFIX` aus `analyze_game_log.py` und `mcnemar_exact_p`
aus `paired_gating.py`, gleiche Wiederverwendung wie `tools/
plate_points_from_arena.py`, aber fuer die GEGNER-/Heuristik-Seite statt
der Netz-Seite ausgewertet — das bestehende Werkzeug liefert nur Netz-Zahlen).

### §7.2 Zahlen (Δ = AN minus AUS, gepaart je Seed)

| Groesse | Lauf 1 (n=20) | Lauf 2 (n=20) | GEPOOLT (n=40) |
|---|---|---|---|
| Netz-Siege AUS→AN | 17→5 | 15→7 | 32→12 |
| McNemar (b/c, p) | 1/13, p=0,0018 | 2/10, p=0,0386 | 3/23, **p=0,0001** |
| Gegner-Punkte Δ | −5,55 (t=−1,36) | −10,15 (t=−1,76) | −7,85 (t=−2,24) |
| **Gegner-Plattenpunkte Δ (Zielgroesse)** | **+0,95 (t=0,55)** | **−0,85 (t=−0,55)** | **+0,05 (t=0,04)** |
| Netz-Punkte Δ | −31,25 (t=−9,92) | −34,10 (t=−8,02) | −32,67 (t=−12,46) |
| Netz-Boden Δ | +8,35 (t=6,53) | +9,70 (t=4,87) | +9,03 (t=7,69) |

**Block-Ebene**: der Standard-`--block-size` (25) machte jeden 20-Partien-
Lauf zu GENAU EINEM Block — keine feingranulare Innerhalb-Lauf-Blockstruktur
gefahren (bewusste Zeitentscheidung, siehe §7.4). Als 2-Block-Kontrolle
(je Lauf ein Block-Mittel, unabhaengige Basis-Seeds) bestaetigt sich die
Richtung in BEIDEN Bloecken unabhaengig: Gegner-Punkte-Mittel [−5,55;
−10,15], Netz-Punkte-Mittel [−31,25; −34,10] — kein Einzelblock-Artefakt
im Sinne der Block-Korrelations-Lehre (dort war GENAU EIN Extremblock die
ganze "Signifikanz"; hier tragen BEIDE unabhaengigen Bloecke dieselbe
Richtung und Groessenordnung).

### §7.3 Diagnose (Ursache, nicht nur Befund)

Log-Inspektion (`evaluations/paired_arena_env_opp_disruption_run1.json`,
Partie Index 0, Seed 20260815): erster Zug des Netzes unter aktivem Knopf
bereits ein Ueberlauf — `"Netz: 2× gelb von F1 → Reihe 1 [1/1] (+1
Strafleiste)"` (Reihe 1 hat Kapazitaet 1, die Fabrik bot aber 2 Fliesen,
eine geht sofort auf die Strafleiste). Ursache GEPRUEFT am Code:

1. `vorzugszug_fuer_farbe` (§5) hat — wie sein Vorbild `vorzugszug_fuer_
   spalte` bewusst dokumentiert ("KEIN Ueberlauf-Kriterium ... erste
   Messung ohne") — KEINE Pruefung, ob die Fabrik MEHR Fliesen der
   Zielfarbe anbietet, als die gewaehlte Musterreihe noch Platz hat. Beim
   Vorbild ist das ein bekanntes, aber wegen der SCHMALEN Auswahlbedingung
   (nur EINE feste Zielspalte, nur wenn eine passende Zeile UEBERHAUPT
   existiert) seltener Fall. Bei `stoerungs_vorzug` ist die Auswahl VIEL
   BREITER (5 Farben, JEDE offene Gegner-Musterreihe/-Kuppelzelle zaehlt
   als Bedarf) — der Ueberlauf-Fall tritt dadurch systematisch haeufiger auf.
2. **Kein Bauer war in dieser Messung aktiv** (`MOSAIC_PLATTENBAU`/
   `MOSAIC_SPALTENBAU` unbesetzt, wie es der einseitige Vergleich
   verlangt) — `aktiver_bauer(state)` liefert daher IMMER `None`,
   `stoerungs_vorzug` ist damit NICHT bloss ein Fallback "wenn der aktive
   Bauer nichts vorschlaegt" (§2-Absicht), sondern in dieser Messung die
   EINZIGE UND DAMIT UNBEDINGTE Uebersteuerung der gesamten 400-Sim-Suche,
   sobald IRGENDEINE vom Gegner gebrauchte Farbe verfuegbar ist — praktisch
   auf fast jedem Zug. Das Netz spielt unter dem Knopf faktisch nicht mehr
   MCTS-gefuehrt, sondern ueberwiegend eine gierige Farb-Wegnahme-Heuristik
   ohne Boden-/Plattenbewusstsein.

Beide Ursachen zusammen erklaeren die Zahlen praezise: Netz-Boden verdoppelt
sich na­hezu (9,3→17,65 im Mittel, Lauf 1), Netz-Punkte brechen um ~59%
ein (55,0→23,75), und die Siegquote kollabiert entsprechend.

### §7.4 Vorab-Regel-Anwendung

- **Vorzeichen-Regel (Nutzer-/Koordinator-Vorgabe, k6-Praezedenz)**: nicht
  einschlaegig im woertlichen Sinn — der Gegner wurde NICHT besser (Gegner-
  Punkte fielen sogar leicht, −7,85 gepoolt), die Zielgroesse selbst
  (Gegner-Plattenpunkte) zeigt aber **gar keinen Effekt** (+0,05 gepoolt,
  t=0,04, Vorzeichen zwischen den beiden Laeufen sogar GEGENLAEUFIG: +0,95
  vs. −0,85) — die Stoerung erreicht ihr eigenes Ziel nicht messbar.
- **Kosten-Nutzen-Pflicht-Nebenmessung (§4, wortwoertlich vorregistriert)**:
  *"ein Stoerungs-Baustein, der die eigene Struktur beschaedigt oder Siege
  kostet, ist kein Gewinn, selbst wenn er den Gegner drueckt"* — hier
  beschaedigt er die eigene Struktur KATASTROPHAL (Boden fast verdoppelt,
  Punkte fast halbiert, Siegquote von 85%/75% auf 25%/35% eingebrochen,
  gepoolt McNemar p=0,0001) UND erreicht nicht einmal die Zielgroesse.
  **Klareres Ablehnungsbild als die vorab befuerchtete Vorzeichen-Umkehr.**
- **Replikations-Pflicht**: erfuellt — beide Laeufe (unabhaengige, frische
  Seeds) zeigen dieselbe Richtung und Groessenordnung bei Siegquote,
  Netz-Punkten und Netz-Boden; die Zielgroesse (Gegner-Plattenpunkte)
  bleibt in BEIDEN Laeufen einzeln UND gepoolt nicht signifikant von 0
  verschieden.

### §7.5 Verdikt

**ABLEHNUNG.** `MOSAIC_OPPONENT_DISRUPTION` bleibt Default AUS (Bestand,
unveraendert) und wird NICHT in irgendeinem Training/Gating/Korpus-Lauf
aktiviert. Der Code (`provocation.rs::gegner_bedarf`/`vorzugszug_fuer_
farbe`/`stoerungs_vorzug`, `plate_builder.rs::drafting_vorzug`s
`.or_else`-Zweig) bleibt STEHEN (LOESCHVERBOT) — der Knopf selbst ist
bereits per Default inert, kein zusaetzliches `#[allow(dead_code)]` noetig
(anders als bei vollstaendig entkoppeltem Code wie `kuppeldraft_vorzug_
k6`: hier bleibt der Aufruf-Pfad ERREICHBAR, nur eben standardmaessig aus).

**Falls dieser Baustein spaeter wiederaufgenommen wird**, sind ZWEI
Konstruktionsfehler zu beheben, nicht nur zu messen:
1. `vorzugszug_fuer_farbe` braucht eine Ueberlauf-Pruefung (wie viele
   Fliesen bietet die Fabrik vs. wie viel Platz hat die Zielreihe) —
   fehlt seit dem Vorbild `vorzugszug_fuer_spalte`, wird dort aber durch
   eine schmalere Auswahl kaschiert.
2. `stoerungs_vorzug` braucht eine ECHTE "bei ~gleichwertigen eigenen
   Zuegen"-Bedingung (Nutzer-Domaenenwissen, §1) statt einer unbedingten
   Uebersteuerung — z.B. nur greifen, wenn der eigene Zug NICHT schlechter
   als eine Referenz-Bewertung (Suchwert/`wertung_progress`) ist, statt
   IMMER zu feuern, sobald irgendein Bedarf existiert. Diese Messung hat
   das nie geprueft, weil ohne aktiven Bauer keine solche Referenz vorlag —
   ein GEPAARTER Test GEGEN einen aktiven Bauer (z.B. `MOSAIC_PLATTENBAU=5`
   + Stoerung als echter Fallback) waere der naechste, andere Versuch, kein
   Nachbessern DIESER Messung.

Beide Punkte sind NEUE Bausteine, kein Teil dieses Auftrags — als
`spawn_task`-wuerdiger Folgeauftrag denkbar, aber nicht hier begonnen.
