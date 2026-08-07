# Vorregistrierung: Aggressions-Stilmessung (Punkte-Raub bei gleicher Siegquote)

**Angelegt 2026-08-07, VOR dem Lauf** (Nutzer-Auftrag: "arena spiel mit
dem tendenziell besten sweep der aggressor faktoren; untersuch eigene
Punkte, Gegner-Punkte, Floor-Strafen; Ziel: eigene Gewinnquote gleich
oder besser UND dem Gegner Punkte rauben, wenn es uns nicht schadet").

## Ausgangsbefund (deskriptiv, Erst-Sweep 200 Spiele/Arm, 8 Bloecke)

Block-gepaarte Differenzen vs Kontrolle (0,0): (0,1;2,0) = Siegquote
+6pp (t~1,9), eigene Punkte +2,0; (0,2;2,0) = Gegner-Floor **+2,1
(t~4,5)**, Gegner-Punkte -1,1, Siegquote +3pp. Alle w>0-Arme senken
die eigenen Floor-Strafen. Erst-Sweep-Arena (McNemar): alle H0.

## Design (Bestaetigungslauf, frische Seeds = Replikationsregel)

`tools/paired_arena_env_ab.py`, Env `MOSAIC_POINTS_UTILITY_W,
MOSAIC_AGGR_LAMBDA`; DREI Arme a **400 Spiele** (16 Bloecke a 25),
Champion@400 vs Heuristik@150dyn, Basis-Seed 20260810:
Kontrolle (0,0), Kandidat A (0.1,2.0), Kandidat B (0.2,2.0).
Einplanung: CPU-Bahn NACH dem laufenden τ-Annealing-Batch, VOR dem
v21-Schwarm.

## Entscheidungsregeln (vorab festgelegt)

1. **Siegquoten-Wache** (primaer, je Kandidat): gepaarter McNemar vs
   Kontrolle. Ein Kandidat scheidet aus, wenn er signifikant SCHLECHTER
   ist (p<0,05 in der falschen Richtung) ODER seine Punkt-Schaetzung
   der Siegquote unter der Kontrolle liegt.
2. **Raub-Metriken** (Block-Ebene, 16 gepaarte Bloecke, t-Test):
   Gegner-Punkte-Senkung und/oder Gegner-Floor-Erhoehung mit p<0,05.
3. **Uebernahme als Live-/Stil-Preset UND ins Self-Play** (Nutzer
   2026-08-07: "ich wuerd es in das self play auch geben. schafft mehr
   diversitaet"), wenn Regel 1 bestanden UND Regel 2 erfuellt.
   Qualifizieren beide Kandidaten, gewinnt der mit der besseren
   Siegquoten-Differenz; Gleichstand -> (0.1,2.0).
   Self-Play-Umsetzung (Koordinator-Empfehlung, Veto offen):
   **Mischung 50/50** -- seed-bestimmter Anteil von 50% der Partien
   mit Preset, Rest w=0 (zwei Stile im Fenster = mehr Diversitaet als
   ein Voll-Umstieg; w=0-Haelfte bleibt Stil-Anker zu Altbestaenden).
   Gilt ab der ersten Generierung NACH dem Verdikt (in der v21-Queue:
   Schwarm und Sockel, sofern das Verdikt vor deren Start faellt).
4. Vor Einsatz in BEWERTETEN Partien braucht das gewaehlte Preset eine
   eigene Anker-Kante (Gating Champion+Preset vs Champion w=0,
   Elo-Betrugsschutz-Regel).
5. Beide Kandidaten scheitern -> w=0 bleibt; dann greift die
   ESKALATIONSLEITER unten (Nutzer 2026-08-07: "dann muessen wir uns
   was anderes ueberlegen damit wir dem gegner seinen punkteaufbau
   aktiv vermiesen").

## Eskalationsleiter bei Doppel-H0 (vorgemerkt, je eigenes Mini-Prereg)

Reihenfolge nach Kosten; jede Stufe mit demselben Instrument
(3-Arm-Stilmessung, Siegquoten-Wache + Raub-Metriken) gemessen:

- **E1 — λ-hoch-Arm** (nur Messung, 0 Code): (w=0,1; λ=5,0) --
  verschiebt den Blend Richtung reiner Gegner-Unterdrueckung
  (u_pts = f(own - λ·opp) wird opp-dominiert). Billigster Test, ob
  die Dosis-Richtung stimmt und nur der Hebelarm zu kurz war.
- **E2 — Floor-Shaping-Opp-Bias** (kleiner Env-Knopf): das verifizierte
  Floor-Shaping (`floor_shaping_delta`, symmetrisch own-opp) bekommt
  eine asymmetrische Gegner-Gewichtung (`MOSAIC_FLOOR_SHAPING_OPP_BIAS`,
  Default 1,0 = Bestand). Begruendung: die Stil-Analyse zeigt, dass der
  Raub-Effekt ueber den FLOOR-Kanal laeuft -- E2 zielt direkt darauf,
  statt ueber den Punkte-Kopf-Umweg.
- **E3 — Denial-Tie-Break an der Wurzel** (Suchpfad-Erweiterung):
  unter allen Wurzelzuegen innerhalb eines ε-Fensters um den besten
  completed-Q (z.B. ε=0,01) wird der Zug mit der niedrigsten
  prognostizierten GEGNER-Punktzahl (opp_points-Kopf) gespielt.
  Strukturell siegquoten-schonend (es werden nur quasi-gleichwertige
  Zuege getauscht) -- die Nutzer-Nebenbedingung "wenn es uns nicht
  schadet" ist hier BAUART, nicht Messhoffnung. Teuerste Stufe
  (Engine-Aenderung + Paritaets-Nachweis), aber der sauberste
  Mechanismus.

## ERGEBNIS (2026-08-07, Bestaetigungslauf 3x400, Seed 20260810)

Siegquoten: Kontrolle 296/400 (74,0%), (0,1;2,0) 305/400 (+2,25pp,
McNemar p=0,48), (0,2;2,0) 284/400 (-3pp, p=0,37).
**VERDIKT: beide Kandidaten SCHEITERN.** (0,2;2,0) faellt an Regel 1
(Punktschaetzung unter Kontrolle). (0,1;2,0) besteht Regel 1, aber
KEINE Raub-Metrik erreicht Regel 2 (16 Bloecke: Gegner-Punkte -0,57
t=-0,71; Gegner-Floor +0,68 t=+1,32; Grenze |t|>=2,13) -- alle
Richtungen stimmen, Staerke reicht nicht. Die Erst-Sweep-Signatur
Gegner-Floor +2,1 (t~4,5) bei (0,2;2,0) REPLIZIERT NICHT (+0,25,
t=0,53) -- Erst-Sweep-Artefakt, Replikationsregel bestaetigt sich.
**w bleibt 0 (ueberall, inkl. Self-Play); Regel 5 -> Eskalationsleiter
aktiv: E3 laeuft (eigenes Nutzer-Go), danach E1 (λ-hoch) als
naechste Sprosse, falls E3 nicht liefert.**

## E1-ERGEBNIS (2026-08-07, 2x400, Seed 20260812): GESCHEITERT

(0,1;5,0): Siegquote 299/400 vs Kontrolle 297/400 (Wache bestanden,
p=0,93) -- aber Raub-Metriken KOMPLETT flach (16 Bloecke: Gegner-Punkte
+0,13 t=+0,14 FALSCHE Richtung; Gegner-Floor +0,26 t=+0,47; alles
schwaecher als beim (0,1;2,0)-Arm). Die Dosis-These "mehr λ = mehr
Gegner-Unterdrueckung" materialisiert sich nicht. KEINE Uebernahme
(auch die gelockerte E3-Philosophie gaebe nichts her: Effekt = 0).
E1 zu -> naechste Sprosse E2 (Floor-Shaping-Opp-Bias).

## E2-ERGEBNIS + LEITER-ABSCHLUSS (2026-08-07, 3x400, Seed 20260813)

bias=1,5: 296/400 (-1pp, faellt an der Wache); einzige "signifikante"
Effekte des Laufs zeigen in die FALSCHE Richtung (Gegner-Punkte +1,44
t=+2,23; Gegner-Floor -0,65 t=-2,15) -- bei 10 Tests/Lauf und
Nicht-Monotonie als Rauschen/Such-Interaktion gelesen, ohnehin kein
Kandidat. bias=2,0: 302/400 (Wache bestanden), Raub-Metriken flach
(Gegner-Punkte -0,18 t=-0,29; Gegner-Floor +0,59 t=+1,24) -> kein
messbarer Effekt, keine Uebernahme.

**LEITER GESCHLOSSEN -- GESAMTVERDIKT AGGRESSIONS-PROGRAMM
2026-08-07**: der aktuelle Kopf gibt KEINEN kostenlosen Raub-Hebel
her: w/λ-Blend flach (Bestaetigungslauf), λ-hoch flach (E1), E3
signifikant schaedlich (-13,75pp bei ε=0,03), Floor-Opp-Bias flach
(E2). Alle Live-/Self-Play-Konfigurationen bleiben auf den Defaults
(w=0, λ=0, ε=0, bias=1). **Wiedervorlage-Bedingung**: neuer Anlauf
(Startkandidat (0,1;2,0)) erst, wenn eine kuenftige Kopf-Generation
den opp-/Punkte-Kopf messbar schaerft (z.B. via Endgame-Aux-Kopf,
PREREG_platten_intervention) -- Praediktor: opp-Kopf-R² deutlich
ueber den heutigen ~0,48.

## STARK-GEGNER-NACHTEST (Nutzer-Hypothese 2026-08-07/08, PREREG vor dem Lauf)

Hypothese: die Raub-/Blend-Effekte greifen evtl. erst gegen einen
Nahe-Peer (alle bisherigen Messungen liefen vs Heuristik@150).
**Design**: paired_gating Champion(+Blend w=0,1/λ=2,0 via Env) vs
`v19_2d_best` (OHNE opp-Kopf -> Blend strukturell inert auf B-Seite,
kein Zwei-Arm-Umweg noetig), Basis-Seed 313795193 = IDENTISCH zum
Champion-Gating vom 2026-08-07 (208:162, 185 Paare, per-Paar-Daten im
JSON) -> gepaarte Auswertung je pair_index ueber die beiden Laeufe
(#30-Muster), max 185 Paare, no-promote. Ein moeglicher SPRT-Fruehstopp
verkuerzt nur das gemeinsame Praefix.
**Auswertung**: (1) Siegquoten-Wache (gepaart, Blend-Lauf darf nicht
unter 208/370 fallen -- Punktschaetzung + McNemar auf diskordanten
pair_index-Paaren); (2) Raub-Metriken Block-Ebene (a/b-Scores,
avg_floor aus per_pair_scores; 37 Bloecke a 5 Paare); Uebernahme-Logik
wie gehabt (Wache = Gate, Raub = Kuer, Nutzer-Philosophie "rein wenn
es nicht schadet").
