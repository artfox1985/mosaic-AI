---
name: mosaic-messlauf
description: Ablauf fuer jeden Messlauf in diesem Projekt - Arena, Self-Play, Gating, Sonde, Trainingslauf. Nutze das, BEVOR du einen Lauf startest, und noch einmal beim Auswerten. Deckt ab - Staffelstab und Exklusivitaet, Lauf-Manifest gegen Referenz, Start ohne Pipe mit sichtbarem Fortschritt, laufzeit-Block im Artefakt, die sechs Standard-Kennzahlen, Auswertung auf Block-Ebene.
---

# Messlauf

Dieser Ablauf ist der Zusammenzug von Regeln, deren Wortlaut in `CLAUDE.md`,
`docs/working_rules.md` und `docs/pitfalls.md` steht. **Bei Widerspruch gilt
dort, nicht hier.** Diese Datei ist der Ablauf, nicht die Quelle.

## Vor dem Start

1. **Staffelstab.** Eine Messung laeuft EXKLUSIV. Sag im Chat an, dass du
   misst. Laeuft eine Parallelsitzung, warte. Nebenlast heisst CPU-Last, nicht
   Absicht: `cargo build`, `cargo test`, `maturin build`, `pip install` und
   jede andere Sonde zaehlen dazu, auch "nur schnell". Dateien lesen und
   schreiben ist unbedenklich, ein `git commit` ist ein Grenzfall.
   Wortlaut: `CLAUDE.md`, "Messungen laufen EXKLUSIV".
2. **Wheel aktuell?** Nach jeder Engine-Aenderung neu bauen. Zahlengleichheit
   bei gleichen Seeds nach einer Aenderung ist ALARM, kein Erfolg.
3. **Lauf-Manifest gegen das Referenz-Manifest halten** (`cli_args` diffen).
   Ein fehlendes Flag meldet sich nicht -- es ist ein Default.
4. **Ist die Referenz die richtige?** Die falsche Referenz ist so teuer wie
   die falsche Messung. Bei Anker-Messungen: ueber `tools/anchor_arena.py`,
   nicht ueber die In-Process-Heuristik.
5. **Vorregistrierung.** Steht die Entscheidungsmetrik vorher fest? Wenn der
   Lauf etwas entscheiden soll, gehoert er in eine Prereg (Skill
   `mosaic-prereg`).

## Beim Start

**NIE in eine Pipe, NIE mit eigener Umleitung.** Beides nimmt dem Harness die
Ausgabe, puffert bis zum Ende, verschluckt den Exit-Code, und PowerShell
bricht die Pipeline bei `Select-Object -First N` sogar frueh ab.

```bash
python -u tools/probes/x.py
```

Mit `run_in_background`, ohne `| tail`, ohne `> log`. Der Lauf braucht einen
Fortschrittszaehler mit `flush=True` -- ein stummer Lauf ist ein Lauf, dessen
Stand niemand kennt, und geschaetzte Restzeiten sind kein Ersatz.

## Ins Artefakt, nicht nach STATUS

Jeder Lauf schreibt seine Dauer in sein eigenes Ergebnis-JSON:

```
"laufzeit": {"wanduhr_s": ..., "cpu_s": ..., "threads": ..., "s_je_partie": ...}
```

`threads` ist Pflicht (die Konvention: `0` = alle Kerne, `1` = sequenziell,
`n` = n Threads). Die Planungsgroesse -- und NUR die -- kommt danach nach
`docs/measured_runtimes.md`.

## Im Bericht: die sechs Standard-Kennzahlen

Zusaetzlich zu dem, was die Prereg verlangt, je Seite und wo sinnvoll als
Differenz zwischen den Armen:

1. Reihenauslastung
2. Spaltenauslastung (volle Spalten, max. Hoehe, Teilspalten >= 3 / >= 4)
3. Strafleistenauslastung (Ueberlaeufe, Strafpunkte)
4. Punkte je Wertungsplatte, je Kriterium aufgeschluesselt
5. eigene Punkte (absolutes Niveau)
6. Margin zum Gegner

**Erst pruefen, dann bauen** -- vorhandene Quellen: `tools/analyze_game_log.py`,
`tools/plate_points_from_arena.py`, `tools/probes/column_build_structural_probe.py`,
`column_completion_gap_probe.py`, `tools/probes/row_preference_probe.py`.
Fehlt eine Groesse, wird ihr Fehlen im Bericht begruendet -- stilles Weglassen
ist ein Regelbruch.

## Auswerten

- **Score-Auswertungen IMMER auf Block-Ebene.** Paar-SEs werden sonst massiv
  unterschaetzt.
- **Aufloesung schlaegt Sparsamkeit.** Bei n=400 streut dieselbe Konfiguration
  um 5,75 Prozentpunkte; der Seed bewegt die Metrik 4- bis 6-mal staerker als
  jeder Knopf. Eine n=100-Marge ist ohne Signifikanz kein Sieg.
- **Value-Aenderungen brauchen Arena-Gating** -- es gibt keinen validierten
  Offline-Praediktor.
- **Aus "Eingriff X in Richtung Y verliert" folgt NICHT "Y ist falsch"** --
  es fehlt die Kontrollgruppe: ein Agent, der Y KANN.
- **Ergebnis registrieren**: Prereg-Koerper UND Zeile-1-Kopf im selben Zug,
  danach `python tools/generate_prereg_index.py` (Skill `mosaic-prereg`).

## Danach

Sag im Chat an, dass die Maschine frei ist -- in EINER Nachricht. Wer die
Exklusivitaets-Zusage bricht, meldet es SOFORT und ungefragt: die andere
Sitzung muss entscheiden koennen, ob ihr Lauf kontaminiert ist.
