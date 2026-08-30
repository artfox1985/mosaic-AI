---
name: mosaic-prereg
description: Ablauf fuer Vorregistrierungen in diesem Projekt - eine neue PREREG_*.md anlegen oder ein Ergebnis/Verdikt in einer bestehenden registrieren. Nutze das, sobald ein Messergebnis feststeht oder ein Bau vorregistriert werden soll. Deckt ab - Zeile-1-Statuskopf, gueltige Status, Laengenbegrenzung, die HEADER_SEARCH_LIMIT-Falle, und den Index-Generator.
---

# Prereg anlegen oder ein Ergebnis registrieren

Wortlaut der Regeln: `CLAUDE.md`, Abschnitt "Prereg-Statuskopf und Index".
Diese Datei ist der Ablauf.

## Beim Registrieren eines Ergebnisses

**Beides im SELBEN Zug, sonst gar nicht:**

1. Das Ergebnis in den Dateikoerper (Herleitung, Zahlen, Bedingungen,
   Stichprobenumfang).
2. Den **Zeile-1-Statuskopf nachziehen** -- den ueberholten Teil ERSETZEN,
   nicht ergaenzen.
3. Sofort laufen lassen:

```bash
python tools/generate_prereg_index.py
```

Nicht auf den pre-commit-Hook warten: der prueft nur und blockt erst beim
Commit.

## Der Kopf ist ein STATUS, keine Chronik

- Gueltige Status: **OFFEN / ENTSCHIEDEN / UEBERHOLT**.
- Ein Verdikt-Satz plus Absatz-Verweise (par.X), hoechstens ein oder zwei
  tragende Zahlen. Richtwert: **unter ~600 Zeichen**.
- Herleitungen, Nebenbefunde, Chronologie gehoeren NUR in den Dateikoerper.
- Beim Kuerzen sicherstellen, dass jedes gestrichene Faktum im Koerper steht
  (sonst dorthin verschieben, nicht loeschen).

## Die stille Falle

`HEADER_SEARCH_LIMIT = 4096` (`tools/generate_prereg_index.py`). Waechst
Zeile 1 darueber hinaus, faellt die Datei **STILL** aus dem Index -- der
Generator meldet nur "ohne parsebaren Status-Kopf". Am 2026-08-25 ist das
passiert, nach einer Nacht, in der bei jedem neuen Ergebnis hinten angehaengt
wurde (4229 Zeichen).

Zweite Falle: **Koepfe veralten gegen ihren eigenen Koerper.** Ein Audit am
2026-08-23 fand vier Preregs, deren Kopf noch "OFFEN / nichts gebaut" sagte,
waehrend der Koerper laengst das registrierte Ergebnis trug.

## Der Tabellenteil des Index wird NIE von Hand editiert

`evaluations/PREREG_INDEX.md` ist generiert. Wer dort etwas aendern will,
aendert den Kopf der Quelldatei und laesst den Generator laufen.

## Fuer Agenten-Auftraege

Die Regel gehoert in JEDEN Prompt, der Prereg-Registrierungen schreiben laesst
-- inklusive des Generator-Aufrufs.
