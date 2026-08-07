# Watchlist v20: Struktur-Zwischenlese (10 Mensch-vs-KI-Partien)

Nutzer `artfox` vs Champion `v20_2d_opp_brierbest@400`, alle 10 in
`player_profiles.json` gewerteten Partien vom 2026-08-07 (15:58–22:11 Uhr).
Reine Log-Text-Auswertung (`static/log/game_*.log`), **kein** Replay, **kein**
Netz-/Oracle-Aufruf (Vorgabe: die Maschine trägt parallel ein GPU-Training).

## 0. Partie-Zuordnung

Alle 10 Logs vollständig vorhanden — keine Zuordnungslücke.

| # | Datum (Profil) | Log | Ergebnis (artfox) | Endstand Mensch:KI |
|---|---|---|---|---|
| 1 | 2026-08-07 15:58 | game_20260807_154952_seed18255.log | Niederlage | 67:83 |
| 2 | 2026-08-07 16:11 | game_20260807_155826_seed522327.log | Sieg | 83:66 |
| 3 | 2026-08-07 16:23 | game_20260807_161301_seed241740.log | Niederlage | 59:86 |
| 4 | 2026-08-07 16:34 | game_20260807_162358_seed442202.log | Niederlage | 60:89 |
| 5 | 2026-08-07 16:44 | game_20260807_163507_seed772053.log | Sieg | 60:32 |
| 6 | 2026-08-07 17:08 | game_20260807_165821_seed869051.log | Sieg | 80:47 |
| 7 | 2026-08-07 21:25 | game_20260807_212505_seed913547.log | Sieg | 100:52 |
| 8 | 2026-08-07 21:39 | game_20260807_213912_seed913547.log | Sieg | 94:64 |
| 9 | 2026-08-07 21:49 | game_20260807_214939_seed913547.log | Sieg | 93:53 |
| 10 | 2026-08-07 22:00 | game_20260807_220005_seed786897.log | Sieg | 59:38 |

**Bilanz: Mensch 7:3** (Endpunkte-Summe 755:610, Ø-Differenz +14,5 Pkt/Partie
für den Menschen). Zum Vergleich v19-Ära (history.md): 8:1.

## 1. Methode & gefundene Parserprobleme

Regex-Patterns aus `tools/analyze_game_log.py::PATTERNS` nachgebaut (keine
Engine-Importe, reine Textklassifikation). Dabei zwei Probleme am
Original-Werkzeug entdeckt und in der eigenen Kopie korrigiert:

1. **Marker-Emoji veraltet**: `PATTERNS["MARKER"]` erwartet `🏁`, die
   aktuellen Logs nutzen durchgängig `❖` (`❖ ... : Startspielerstein
   genommen (−2 Pkt am Rundenende ...)`). Mit dem Original-Regex würde
   `tools/analyze_game_log.py` diese Zeile nicht als Marker überspringen,
   sondern als unbekannte Aktionszeile werten → `ReplayDivergence`. Getroffen
   in **allen 10** Logs (je 3–5× pro Partie).
2. **`FINAL_SCORE`-Regex akzeptiert keine negative Endwertung**:
   `Endwertung (?P<total>\d+) Pkt` matcht nicht bei z. B.
   `KI: Endwertung -12 Pkt → Gesamt: 38 Pkt` (passiert, wenn die
   Spezialfelder-Wertungsplatte aktiv ist und Felder leer bleiben). Betrifft
   **2 von 10** Logs (`..._165821_...`, `..._220005_...`); dort hätte das
   Original-Tool den KI-Endwertungsblock beim Parsen der Wertungsplatten-Story
   ausgelassen bzw. bei vollem Replay mit Abbruch reagiert.
3. **Bekannte, im Tool selbst dokumentierte Lücke bestätigt**: der KI-Pfad
   loggt Chip-Reihenabschlüsse (`🎫 ... komplettiert Reihe N`) nie (nur der
   Mensch-Pfad tut das explizit). Ich habe das über
   Musterreihen-Füllstand-Tracking aus den `[fill/cap]`-Angaben der
   Sonne/Mond-Nahme-Zeilen kompensiert: Wenn eine Reihe beim `🎯`-Score-Event
   laut letztem bekannten Füllstand noch nicht voll war und keine explizite
   `🎫`-Zeile vorausging, zähle ich das als "stiller" Chip-Abschluss. Das ist
   eine **Text-Näherung, keine Engine-Verifikation** — siehe Befund 3 unten,
   dort mit Vorsicht interpretiert.

Keine weiteren Emoji-/Format-Abweichungen gefunden (alle übrigen Symbole
🌙 🎯 ☀️ 🎴 ⚠️ 📦 ⭐ 🎫 🏆 stimmen mit den Tool-Patterns überein, stichprobenartig
gegen 3 Logs verifiziert).

## 2. Kennzahlen (Summe über 10 Partien / Ø je Partie)

| Metrik | Mensch (Summe / Ø) | KI (Summe / Ø) |
|---|---|---|
| Startspielerstein-Nahmen | 40 / 4,0 | 10 / 1,0 |
| Chip-Reihenabschlüsse gesamt (explizit + inferiert) | 23 / 2,3 | 20\* / 2,0\* |
| ... davon explizit geloggt (🎫) | 23 / 2,3 | 0 (Logging-Lücke) |
| ... davon inferiert (still) | 0 | 20\* / 2,0\* |
| Spezialpunkte (⭐ Kuppel-Bonus) | 103 / 10,3 | 13 / 1,3 |
| Special-Feld-Freischaltungen (Anzahl) | 31 / 3,1 | 6 / 0,6 |
| Special-Unlock in Runde 2 (Partien) | 9 / 10 | 0 / 10 |
| Special-Unlock überhaupt nie (Partien) | 1 / 10 | 6 / 10 |
| Kuppel-Legungen | 175 / 17,5 | 172 / 17,2 |
| Punkte je Kuppel-Legung | — / 3,53 | — / 3,51 |
| Legungen mit Vertikal-Bonus (Anteil) | 94/175 = 53,7 % | 91/172 = 52,9 % |
| Vertikal-Bonuspunkte | 310 / 31,0 | 259 / 25,9 |
| Horizontal-Bonuspunkte | 264 / 26,4 | 304 / 30,4 |
| R5+R6-Nahmen-Anteil (an allen Reihen-Nahmen) | 132/327 = 40,4 % | 68/300 = 22,7 % |
| Kuppel-Legungen in R5/R6 | 37 / 3,7 | 13 / 1,3 |
| Mond-Nahmen | 232 / 23,2 | 191 / 19,1 |
| Sonne-Nahmen | 117 / 11,7 | 133 / 13,3 |
| Wild-Kuppel-Anteil (Stapel-Peeks mit Wild-Rückseite) | 19/30 = 63,3 % | 17/34 = 50,0 % |
| Stapel-Peeks gesamt | 30 / 3,0 | 34 / 3,4 |
| Bonuschips genommen | 100 / 10,0 | 100 / 10,0 |
| Chip-Verbrauchsquote (genutzt/genommen) | 23,0 % | 20,0 %\* |
| Strafleisten-Summe (Gesamt-Minuspunkte) | 152 / 15,2 | 105 / 10,5 |

\* KI-Chip-Werte sind Text-Inferenz (Füllstand-Lücken-Methode, siehe Abschnitt 1), nicht direkt geloggt.

Wertungsplatte "Spezialfelder" (Dossier-Platte Nr. 7, docs/engine_manual.md
Punkt 7) war in **3 von 10** Partien aktiv (#5, #6, #10) — in allen drei
gewinnt der Mensch (n=3, keine belastbare Aussage möglich).

## 3. Dreifach-Vergleich mit der v19-Ära (Zahlen aus archive/history.md, Abschnitt "MENSCH-vs-KI-BEFUND", 9 Partien)

| Metrik | v19: Mensch | v20: Mensch | v19: KI | v20: KI |
|---|---|---|---|---|
| Sieg-Quote gg. Champion | 8:1 (88,9 %) | 7:3 (70,0 %) | — | — |
| Chip-Reihenabschlüsse/Partie | 1,9 | 2,3 | 0,0 (Log-Text) | 2,0\* (korrigiert) |
| Spezialpunkte/Partie | 10,8 | 10,3 | 0,4 | 1,3 |
| Startspielerstein-Nahmen (Verhältnis) | 34:7 (4,86:1) | 40:10 (4:1) | — | — |
| R5+R6-Nahmen-Anteil | 37 % | 40,4 % | 22 % | 22,7 % |
| Punkte je Kuppel-Legung | 3,30 | 3,53 | 3,47 | 3,51 |
| Mond-Nahmen/Partie | ~19,9 | 23,2 | (nicht berichtet) | 19,1 |

\* siehe Kernbefund 3 — mutmaßlich teilweise derselbe Mess-Artefakt wie die alte
0,0-Zahl, nicht zwingend eine echte Verhaltensänderung der KI.

## 4. Kernbefunde

**Befund 1 — Sieg-Quote gegen den Champion sinkt spürbar.**
8:1 (v19) → 7:3 (v20), Endpunkte-Differenz im Schnitt +14,5 statt (laut
v19-Text) deutlich höher. *Deutung*: v20 ist insgesamt der stärkere Gegner;
das allein sagt noch nichts über welche der unten stehenden Struktur-Elemente
dafür ursächlich sind. n=10, kein Signifikanztest möglich (zu wenige Partien
für einen belastbaren Anteilsvergleich).

**Befund 2 — Special-Unlock-Timing bleibt praktisch unverändert: v20 hat diese
Lücke NICHT geschlossen.** Der Mensch schaltet in 9 von 10 Partien bereits in
Runde 2 ein Spezialfeld frei; die KI tut das nur in 4 von 10 Partien, nie vor
Runde 4, und in 6 von 10 Partien gar nicht. Das deckt sich direkt mit dem
Dossier-Punkt "Spezial-Kuppeln in die ERSTEN (schnellen) Reihen" — dieses
Element funktioniert für den Menschen weiter und bleibt ein struktureller
KI-Rückstand.

**Befund 3 — Die alte "Chip-Dürre" (KI 0,0/Partie) war wahrscheinlich zum Teil
ein Mess-Artefakt, nicht (nur) ein Verhaltensbefund.** Mit der in Abschnitt 1
beschriebenen Füllstand-Inferenz (kompensiert die dokumentierte KI-Logging-
Lücke bei Chip-Abschlüssen) liegt die KI in den v20-Logs bei ~2,0
Chip-Reihenabschlüssen/Partie — nahe am Menschen (2,3). Da dieselbe
Logging-Lücke bereits damals im Code existierte, ist unklar, wie viel vom
Sprung 0,0→2,0 echte Verbesserung von v20 ist und wie viel allein der
korrigierten Messmethode zuzuschreiben ist. **Empfehlung** (keine Handlung in
diesem Auftrag): die 9 v19-Logs mit derselben Füllstand-Inferenz nachmessen,
um einen echten Vorher/Nachher-Vergleich zu bekommen.

**Befund 4 — Der frühere kleine KI-Vorteil bei Punkten/Kuppel-Legung ist
verschwunden.** v19: KI 3,47 vs. Mensch 3,30 (KI leicht voraus). v20: KI 3,51
vs. Mensch 3,53 (Parität, Mensch marginal vorn). *Deutung*: könnte auf eine
v20-Architektur-Eigenschaft hindeuten, ist aber bei n=10 nicht von Rauschen
zu unterscheiden.

**Befund 5 — Die "Kreuz-Aufbau"-Dossier-Erklärung ist bei der reinen
Vertikal-Bonus-RATE nicht klar belegt, wohl aber beim R5+R6-Anteil.** Der
Anteil der Kuppel-Legungen mit Vertikal-Bonus ist zwischen Mensch (53,7 %) und
KI (52,9 %) fast identisch — beide bauen pro Legung ähnlich oft eine Vertikale.
Der R5+R6-Nahmen-Anteil dagegen bleibt seit v19 nahezu unverändert asymmetrisch
(Mensch ~40 %, KI ~23 %) — dieser spezifische Struktur-Unterschied (nicht die
allgemeine "baut Kreuze" -Fähigkeit) ist die stabile, v20-unabhängige Lücke.

**Befund 6 — Startspielerstein-Verhältnis bleibt stabil bei ~4:1, stützt die
Nutzer-Einordnung als Nebenprodukt.** v19: 34:7 (4,86:1); v20: 40:10 (4:1).
Beide Werte liegen in derselben Größenordnung wie der moon-lastige Sammelstil
des Menschen (v19: 19,9 Mond-Nahmen/Partie; v20: 23,2) — konsistent mit der
protokollierten Nutzer-Selbstauskunft ("würde den Startspielerstein nicht
überbewerten"), ohne dass hier eine neue Aussage über Absicht getroffen wird.

## Caveats

- **n=10** (bzw. 9 für die v19-Vergleichszahlen) — jede Prozentangabe ist eine
  Punktschätzung ohne Signifikanztest; Einzelpartien-Ausreißer (z. B. Partie 4
  ohne jede Special-Freischaltung auf beiden Seiten) können Mittelwerte
  spürbar verschieben.
- Chip-Reihenabschlüsse der KI sind **Text-Inferenz**, keine Engine-
  Bestätigung (siehe Befund 3).
- Wertungsplatten-IDs im Log sind 0-indiziert (Log-ID + 1 = Nummer in
  `docs/engine_manual.md`, Abschnitt "Die 8 Wertungsplatten") — gegen die 4
  bekannten Ausschluss-Paare verifiziert.
- Keine Aussagen über Nutzer-Absichten über das wörtliche Dossier hinaus;
  alle Deutungen sind als solche markiert und bleiben auf Messwerte gestützt.
