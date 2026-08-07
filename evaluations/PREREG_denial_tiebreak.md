# Vorregistrierung: Denial-Tie-Break an der Wurzel (E3, eigenstaendig)

**Angelegt 2026-08-07, VOR Implementierung und Messung.** Nutzer-Go am
selben Tag ("takten den test ein"), UNABHAENGIG vom Ausgang der
w/λ-Stilmessung (E3 war urspruenglich Stufe 3 der Eskalationsleiter in
PREREG_aggression_stilmessung.md).

## Mechanismus

Unter allen WURZEL-Kandidaten, deren completed-Q innerhalb eines
ε-Fensters um den besten Wurzelzug liegt (quasi-gleichwertige Zuege),
spielt die Suche den Zug mit der NIEDRIGSTEN prognostizierten
Gegner-Punktzahl (opp_points-Kopf, Task #28 / F1-gefixte Extraktion).
Die Nutzer-Nebenbedingung "dem Gegner Punkte rauben, wenn es uns
nicht schadet" ist damit BAUART: getauscht wird nur innerhalb des
Aequivalenzfensters.

## Implementierung (Env-Knopf-Muster, Commit 2cd364e)

- `MOSAIC_DENIAL_TIEBREAK_EPS` (f64, Default 0,0 = AUS =
  byte-identisches Bestandsverhalten; OnceLock/read_f64_env).
- Wirkt bei der FINALEN Wurzelzug-Wahl der Netz-Suche (Gumbel-Pfad);
  ε auf der completed-Q-Skala ([0,1]-Gewinnwahrscheinlichkeit).
- Gegner-Punkte-Prognose je Wurzelkind aus dessen ohnehin berechneter
  Netz-Evaluation (kein zusaetzlicher Forward-Pass; falls das im
  Baum nicht ohne Zusatzkosten verfuegbar ist, ist EIN zusaetzlicher
  Batch-Forward ueber die <=m Fenster-Kandidaten erlaubt -- Kosten
  dokumentieren).
- Modelle OHNE opp-Kopf: Knopf inert + einmalige Warnung (Muster
  `warn_missing_opp_head_once`).
- R5 bleibt Alpha-Beta-exakt (round5.rs unangetastet); Default-
  Paritaets-Nachweis (Hash-Probe) + Engine-Tests vor Einsatz.

## Messung (Instrument der Stilmessung, eigene Seeds)

DREI Arme a 400 Spiele (Champion@400 vs Heuristik@150dyn, Basis-Seed
20260811): Kontrolle (ε=0), ε=0,01, ε=0,03. Auswertung identisch zur
Stilmessung: Siegquoten-Wache (McNemar; Punkt-Schaetzung darf nicht
unter die Kontrolle fallen), Raub-Metriken auf Block-Ebene (16 Bloecke:
Gegner-Punkte ↓ / Gegner-Floor ↑, p<0,05). Zusaetzlich deskriptiv:
wie oft feuert der Tie-Break (Anteil getauschter Zuege, aus einem
Debug-Zaehler oder Stichproben-Traces).

**Erwartung/Lesart**: Siegquote ~unveraendert (Bauart); entscheidend
ist allein die Raub-Signatur. ε=0,03 aggressiver, aber naeher an der
Grenze, wo "quasi-gleichwertig" nicht mehr stimmt -- faellt die
Siegquote dort, gilt nur ε=0,01.

## Einordnung / Kombination

- Queue: CPU nach der w/λ-Stilmessung (deren Verdikt zuerst).
- Kombination mit einem etwaigen w/λ-Preset wird ERST gemessen, wenn
  BEIDE einzeln bestanden haben (eigenes Mini-Prereg; keine
  ungemessenen Kombi-Presets).
- Uebernahme-Ziel bei Bestehen: Live-/Stil-Preset UND Self-Play
  (Diversitaets-Entscheid des Nutzers gilt sinngemaess; Anker-Kante
  vor bewertetem Einsatz).
