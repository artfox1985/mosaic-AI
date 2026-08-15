<!-- STATUS: OFFEN | Frage: Stoert ein Plattenbauer-Baustein nach Runde 4 den Gegner wirksam ueber die oeffentliche Farbzaehlung (verbleibende_farben) -- bei ~gleichwertigen eigenen Zuegen die Fliese nehmen, die dem Gegner ausgeht? | Beleg: OFFEN, vorregistriert 2026-08-14 (Nutzer-Go 'loslegen mit der vorbereitung'). Vorbereitungsphase: nur PREREG + Bau + cargo test --lib; Messplan §4 vorab festgeschrieben, NICHT gefahren -- Messung und Abnahme (§6) erst NACH Ende des parallel laufenden ownership_weight-Sweeps (Wheel-Install bis dahin gesperrt). -->

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

## §4 Messplan (VORAB festgeschrieben, NICHT gefahren)

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

## §6 Abnahme (NACH Sweep-Ende, nicht Teil dieses Auftrags)

1. Wheel-Install + `tools/paritaets_probe.py` — Hash muss halten (Knopf
   unset = Bestand).
2. Der volle Messplan aus §4 (Erst- + Replikationslauf, gepoolt).
3. Ergebnis-Nachtrag in dieser Datei (§7, noch nicht vorhanden).
