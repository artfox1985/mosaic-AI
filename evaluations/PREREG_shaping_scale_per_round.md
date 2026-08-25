<!-- STATUS: ENTSCHIEDEN | Frage: Ist die Wirkungslosigkeit der Wertungsplatten-Injektion ein Artefakt eines rundenblinden Nenners? `WERTUNG_SHAPING_SCALE` ist fest 50, der Punktestand nach Runde 1 liegt bei 4. | Beleg: par.13 (2026-08-20): NEIN -- Profil-Arena gefahren (Dosis 0,3, 407 Seeds, Vorflug bestanden): k1 -0,23 (Block-t -1,27), k2 +0,13 (t 1,58), Siege 284:295 (p=0,34). par.8-Klausel greift: der rundenblinde Nenner ist als Erklaerung ausgeschieden, die Injektionslinie ist ohne neue Idee zu Ende gemessen. -->

# PREREG: Rundenabhängiger `WERTUNG_SHAPING_SCALE`

Stand 2026-08-18, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

---

## par.1 DER ANLASS IST EINE MESSUNG

Der Shaping-Shift lautet `w · tanh(E / WERTUNG_SHAPING_SCALE)` mit einem festen
Nenner von **50**. Gemessen an 22 Arena-Logs (`static/log/elo/*.log`, Mensch
gegen KI, Modelle `v19_2d_best` und `v20_2d_opp_brierbest`, 400 Sims) steht
folgender Punktestand nach der jeweiligen Runde auf dem Brett:

| Runde | Mensch | KI | Anteil KI | Anteil Mensch | Mittel |
|---|---:|---:|---:|---:|---:|
| 1 | 7,0 | 4,0 | 0,072 | 0,094 | **0,083** |
| 2 | 13,3 | 9,2 | 0,165 | 0,179 | **0,172** |
| 3 | 23,0 | 19,2 | 0,345 | 0,309 | **0,327** |
| 4 | 37,7 | 29,2 | 0,524 | 0,507 | **0,515** |
| 5 | 59,2 | 47,6 | 0,855 | 0,796 | **0,825** |
| nach Endwertung | 74,4 | 55,7 | 1,000 | 1,000 | — |

**Der Nenner 50 ist damit rundenblind und früh um mehr als eine Größenordnung
zu grob:** nach Runde 1 stehen 4 Punkte im Buch, geteilt wird durch 50.

**Und die Kurvenform ist stärke-invariant.** Die Niveaus liegen 33 %
auseinander (55,7 gegen 74,4), die Anteile stimmen auf 0,02 überein. Der
Verlauf ist damit Spielstruktur und nicht Spielstärke — das ist die
Voraussetzung dafür, ein festes Profil überhaupt eintragen zu dürfen.

**Caveat zur Messung:** die Zeilen-n schwanken zwischen 14 und 22, weil nicht in
jeder Runde je Spieler eine punktewirksame Zeile fällt. Die Größenordnung
trägt, die zweite Stelle nicht.

## par.2 GEPRÜFTER IST-STAND (Quellen, nicht hergeleitet)

| Sache | Befund | Prüfstelle |
|---|---|---|
| Nenner | `const WERTUNG_SHAPING_SCALE: f64 = 50.0` | `net_mcts.rs:1059` |
| Verbrauchsstelle A | Wertungs-Pfad, `let bei = \|x\| (x/SCALE).tanh()` | `net_mcts.rs:1456` |
| Verbrauchsstelle B | Ownership-Pfad, `gew[k] * (e[k]/SCALE).tanh()` | `net_mcts.rs:1699` |
| Weitere Vorkommen | zwei Tests bauen die Formel nach | `net_mcts.rs:7565`, `:9760` |
| Pfad A speist sich aus | ENGINE-Größen (Fortschritt, Freischaltung, Strafleiste, Tiling) — kein Netz | `net_mcts.rs:1462-1480` |
| Pfad B speist sich aus | Ownership-Kopf, `E_k` | `net_mcts.rs:1683-1693` |
| Kopf-Blend benutzt die Skala NICHT | eigene Knöpfe, kein `tanh`, kein /50 | `net_mcts.rs:2089-2110` |
| Gewicht Pfad A | `MOSAIC_WERTUNG_SHAPING_W`, Default **0,0** | `knob_registry.rs:76` |
| Gewicht Pfad B | `MOSAIC_OWNERSHIP_W`, Default **0,0** | `knob_registry.rs:82` |
| Rundenzahl verfügbar | Pfad A liest `state.round_number` bereits; Pfad B bekommt `state` | `net_mcts.rs:1468` |
| `MOSAIC_WERTUNG_ROUND_GAIN` | Default 0,0, ausserhalb von `docs/knobs.md` **nirgends gesetzt** | `knob_registry.rs:78`, Repo-Grep |

**Beide Shaping-Pfade sind per Default AUS.** Dieser Umbau repariert damit
nichts im laufenden Spiel — er stellt die Bedingungen her, unter denen eine
Wiederholung der Injektionsmessung aussagekräftig wäre.

## par.3 DAS ARGUMENT: `w` UND `S` SIND GLOBAL AUSTAUSCHBAR, JE RUNDE NICHT

Im linearen Bereich des `tanh` gilt `w · tanh(E/S) ~ w · E/S`. Ein global zu
großes `S` lässt sich durch ein größeres `w` exakt ausgleichen — und genau das
haben die Dosisreihen abgesucht (`PREREG_scoring_plate_injection.md`), sie
variierten `w`.

Was ein über die Partie konstantes `w` **nicht** kann, ist eine
rundenabhängige Schieflage beheben. Die ist da (Herleitung aus par.1, nicht
gemessen): bei vergleichbarer Zielerreichung ergibt sich heute

- Runde 1, `E ~ 0,7`: `tanh(0,7/50) = 0,014`
- Runde 5, `E ~ 7`: `tanh(7/50) = 0,139`

**Faktor 10 zugunsten der Runde, in der laut `docs/domain_knowledge.md` nur
noch ≤ 7 Optionen offen sind** — während in Zug 1 der Runde 1 noch 195 zur Wahl
stehen. Das Shaping ist am schwächsten, wo die Entscheidungen fallen.

Das macht den negativen Dosisbefund **nicht ungültig**. Es benennt einen
Mechanismus, durch den er ein Artefakt sein könnte.

---

## par.3a KORREKTUR DER PRAEMISSE FUER PFAD B (gemessen 2026-08-18, andere Sitzung)

**Die Rundenschieflage aus par.3 gilt fuer Pfad A, fuer Pfad B NICHT.** par.3
leitet den Verlauf `E ~ 0,7` (Runde 1) auf `E ~ 7` (Runde 5) aus dem
PUNKTESTAND je Runde ab. Fuer den Ownership-Pfad ist das nachgemessen worden und
trifft nicht zu.

`tools/probes/shaping_scale_e_distribution.py`, `b18_best`, 600 Drafting-
Zustaende aus 600 verschiedenen Partien von `data/holdout`, 120 je Runde,
Feldindizierung aus `scoring.rs:422/432`:

| Runde | Median E(k0) | Median E(k1) | Median E(k2) |
|---|---:|---:|---:|
| 1 | 1,362 | 0,082 | 0,038 |
| 3 | 1,403 | 0,082 | 0,025 |
| 5 | 1,174 | 0,116 | 0,023 |

**`E` ist fuer Pfad B rundenkonstant** — bei den Diagonalen faellt es sogar. Der
Grund ist strukturell: `wertung_progress` (Pfad A) misst FORTSCHRITT und waechst
naturgemaess mit dem Punktestand; der Ownership-Kopf (Pfad B) prognostiziert den
ENDZUSTAND und wird im Verlauf *schaerfer*, nicht *groesser*.

**Folge fuer das Profil:** mit `SCALE_r` wuerde der Shift bei k1 in Runde 1 auf
`tanh(0,082/4,2)` = 0,0195 steigen und in Runde 5 auf `tanh(0,116/41,2)` = 0,0028
fallen — **siebenfach zugunsten der frueher Runden gekippt**, nicht
vergleichmaessigt wie par.4 erwartet. Das kann als Absicht gewollt sein (par.3
argumentiert ja mit den 195 Optionen in Runde 1), ist dann aber eine ANDERE
Begruendung als "Vergleichmaessigung" und gehoert so benannt.

**par.6 Saettigungspruefung: fuer die Geometrie-Kriterien ERFUELLT.** Alle
90-%-Quantile von `E_r / SCALE_r` liegen unter **0,40** (Maximum: k0 in Runde 1),
klar unter der Grenze 1,0. Die dort vorab benannte Verzweigung "getrennte
Profile" wird damit NICHT durch Saettigung ausgeloest — wohl aber durch die
Praemissen-Differenz oben.

**Was fuer Pfad B stattdessen bezifferbar ist:** der Nenner ist nicht rundenweise,
sondern KRITERIENWEISE falsch. `tanh(0,082/50)` = 0,0016 gegen eine
q-Eigenspreizung der Suche von 0,078 — Faktor ~50 zu leise, in jeder Runde.
Damit der Shift die Groessenordnung der Suche erreicht, waeren Nenner von etwa
**k0 ~17, k1 ~1, k2 ~0,3** noetig statt einheitlich 50. Einzelheiten und Belege:
`PREREG_ownership_coupling.md` par.6.4.

**Fuer Pfad A ist nichts davon widerlegt.** Die Fortschrittsgroesse waechst
tatsaechlich, dort bleibt die Herleitung aus par.3 plausibel — sie ist nur nicht
gemessen (Pfad-A-Verteilung von `E` je Runde fehlt weiterhin, siehe par.6).

## par.4 DAS PROFIL

`SCALE_r = WERTUNG_SHAPING_SCALE · profil_r` mit dem Mittel aus par.1:

| Runde | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| `profil_r` | 0,083 | 0,172 | 0,327 | 0,515 | 0,825 |
| `SCALE_r` | 4,2 | 8,6 | 16,3 | 25,8 | 41,3 |

`WERTUNG_SHAPING_SCALE` bleibt als globaler Bezug stehen und wird **nicht**
gesenkt — Nutzer-Entscheid 2026-08-18: die 50 zeigen auf das Ziel, nicht auf den
Ist-Stand, und wachsen mit der Spielstärke von selbst hinein.

**Erwartete Wirkung (Herleitung, nicht gemessen):** Runde 1 `tanh(0,7/4,2) =
0,165` statt 0,014, Runde 5 `tanh(7/41,3) = 0,168` statt 0,139. Das Profil
**vergleichmäßigt** den Einfluss über die Runden, statt ihn früh verschwinden zu
lassen.

## par.5 WAS GEBAUT WIRD

**Ein Knopf, keine neue Konstante.** `MOSAIC_WERTUNG_SCALE_PROFILE`, Default
**aus** = flacher Nenner 50 für alle Runden, byte-identisches Bestandsverhalten
(Task-#28-Muster). Gesetzt = die fünf Werte aus par.4.

**Warum ein Knopf und keine einkompilierte Tabelle:** dieses Projekt hat schon
einmal einkompilierte kalibrierte Zielwerte je Kriterium wieder ausgebaut, weil
ihre Herleitung nicht trug (`net_mcts.rs:1280-1282`). Eine Tabelle ohne
Abschaltbarkeit wäre derselbe Fehler ein zweites Mal.

**Zwingend mitregistriert:** `MOSAIC_WERTUNG_ROUND_GAIN` bleibt in allen Armen
auf **0**. Er hebt die Alphas rundenabhängig an und zöge damit an derselben
Schraube; zwei Rundenhebel gleichzeitig wären nicht trennbar.

## par.6 VORBEDINGUNG — SÄTTIGUNGSPRÜFUNG VOR DEM BAU

Ein kleinerer Nenner bringt Sättigung mit sich: läuft `tanh` gegen 1, so
unterscheidet der Term die Geschwisterzüge nicht mehr, und das ist genau die
Störung, an der die Dosisreihe bei `w ~ 10` gescheitert ist.

Die beiden Pfade arbeiten dabei in **verschiedenen Bereichen**: Pfad B liegt
heute bei `E ~ 0,7` (gemessen 2026-08-18) und damit tief im linearen Bereich,
Pfad A kann zweistellig werden (ungeprüft). Ein gemeinsames Profil könnte Pfad A
früh in die Sättigung schieben.

**Zu messen VOR jeder Zeile Code**, auf dem vorhandenen Bewertungssatz
`data/holdout`, ohne neuen Lauf: die **Verteilung von `E` je Pfad und je
Runde**. Entscheidungsregel:

- Liegt das 90-%-Quantil von `E_r / SCALE_r` in beiden Pfaden unter **1,0**,
  trägt ein gemeinsames Profil.
- Liegt es darüber, bekommen die Pfade getrennte Profile, oder Pfad A wird auf
  einen flacheren Verlauf gesetzt. Diese Verzweigung ist damit VORAB benannt
  und keine nachträgliche Anpassung.

## par.6a ERGEBNIS DER SÄTTIGUNGSPRÜFUNG, PFAD A (2026-08-19)

`tools/probes/shaping_scale_pfad_a_e.py`, 600 Drafting-Zustände aus
`data/holdout` (je (Partie, Runde) einer, 120 je Runde), Quelle der Größen:
neuer Read-only-Export `mosaic_rust.wertung_shaping_e_json` (rechnet exakt die
Terme aus `net_mcts.rs:1462-1487`, Laufzeit-Alphas, `round_gain = 0`).
Rohzahlen: `evaluations/artifacts/probe_shaping_e_distribution_pfad_a.json`.

> **par.6, Pfad A: ERFÜLLT.** Alle 90-%-Quantile von `E_r / SCALE_r` liegen
> unter **0,32** (Maximum: k3 in Runde 4 mit 0,31; die Zielkriterien k1/k2
> maximal 0,20/0,14). Zusammen mit dem Pfad-B-Ergebnis aus par.3a (< 0,40)
> ist die Vorbedingung beidseitig erfüllt: **ein gemeinsames Profil trägt**,
> die Verzweigung "getrennte Profile" wird nicht ausgelöst.

Drei Nebenbefunde, gemessen und geprüft:

1. **`wertung_progress` wächst je Kriterium monoton mit der Runde** (k1-Median
   0,00 → 0,78 → 1,94 → 4,08 → 6,61) — die par.3-Prämisse gilt für Pfad A
   also wirklich, im Gegensatz zu Pfad B (par.3a). **Aber: in Runde 1 ist
   JEDER Pfad-A-Term exakt 0** (alle Kriterien, unlock, floor, tiling; 120
   Zustände) — das Kuppelraster ist in Runde 1 vor dem Rundenende leer, und
   `wertung_progress` liest nur `build_grid`. Ein Rundenprofil kann Runde 1
   für Pfad A also NICHT heilen — dort gibt es nichts zu skalieren; der
   kleinste wirksame Nenner ist der von Runde 2.
2. **`floor_penalty` und `tiling_potenzial` sind in den Holdout-Stichproben
   fast durchgehend 0.** Geprüft, kein Exportfehler: `projected_unplaceable_
   penalty` misst kommende Strafpunkte aus UNPLATZIERBAREN Musterreihen
   (`round_end.rs:115-124`), nicht die aktuelle Strafleiste — unplatzierbare
   Reihen sind in Self-Play-Zuständen selten. An Mensch-Partie-Zuständen
   liefert der Export Werte > 0.
3. **KORRIGIERT (2026-08-19, Regel-0-Fund bei der Umsetzung, am Code
   verifiziert):** hier stand zunächst, `floor_penalty` fahre „mit
   Default-Gewicht 0,3 IMMER mit". Das war eine **Verwechslung zweier
   Knöpfe**: die 0,3 gehören zu `MOSAIC_FLOOR_SHAPING_W`
   (`floor_shaping_delta`, Korrektur am Netz-Blattwert, `net_mcts.rs:403`)
   — die läuft NICHT durch die Pfad-A-Closure. Der Strafleisten-Term in
   `apply_wertung_shaping_full` hängt an `MOSAIC_WERTUNG_FLOOR_W`, Default
   **0,0** (`net_mcts.rs:1306`). **Per Default ist damit KEIN Pfad-A-Term
   live; der Profil-Knopf ändert kein Produktionsverhalten.** Strafleisten-
   und Tiling-Term sind bei der Umsetzung trotzdem auf den flachen Nenner
   gepinnt (Schutz, falls je `MOSAIC_WERTUNG_FLOOR_W` und das Profil
   gleichzeitig gesetzt werden).

## par.7 MESSANORDNUNG

**Zuerst Pfad A (Wertungs-Pfad).** Er ist der Pfad, in dem die Injektion schon
einmal gemessen wurde, also der einzige mit Vergleichspunkt — und er hängt nicht
am Ownership-Kopf, dessen Schwäche am 2026-08-18 mehrfach belegt wurde.

- Gepaarte Arena über dieselben Seeds, `tools/paired_arena_env_ab.py`
- Kontrollarm: Profil **aus**, `MOSAIC_WERTUNG_SHAPING_W` auf der Dosis, die in
  `PREREG_scoring_plate_injection.md` gemessen wurde
- Versuchsarm: Profil **an**, dieselbe Dosis
- Blockgröße 25, Auswertung auf **Block-Ebene** (Paar-SEs unterschätzen
  massiv, Memory `feedback_arena_block_correlation`)
- `--log-games` für die Verhaltens-Nebenmessung

## par.8 VORAB-ERFOLGSREGEL (vor der ersten Partie)

**Erfolg:** `k1` ODER `k2` bewegt sich gegen den Kontrollarm signifikant auf
Block-Ebene (nB=6, Schwelle |t| > 2,571), **ohne Siegverlust** (McNemar über
die diskordanten Paare, p >= 0,05 gegen eine Verschlechterung).

**Nicht-Erfolg:** beide flach. Dann ist der rundenblinde Nenner als Erklärung
für den negativen Dosisbefund ausgeschieden, und die Injektionslinie ist ohne
neue Idee zu Ende gemessen — **keine weitere Dosis- oder Profilvariante.**

**Ausdrücklich KEIN Erfolgskriterium:** ein Zuwachs bei `k3`/`k4`. Der Leitstern
in STATUS.md schliesst die Zähl-Kriterien aus; gefragt sind die konjunktiven.

## par.9 WAS DIESER VERSUCH NICHT ENTSCHEIDET

- **Nicht** Pfad B (Ownership). Der bekommt eine eigene Frage, erst nach par.6.
- **Nicht** den globalen Wert 50. Er bleibt.
- **Nicht** `MOSAIC_WERTUNG_ROUND_GAIN`. Er bleibt 0.
- **Nicht** die Form des Profils. Die fünf Werte stammen aus par.1 und werden
  in diesem Versuch nicht angepasst — eine Profil-Suche wäre ein eigener
  Versuchsplan und ist hiermit vorab ausgeschlossen.

## par.10 ERGEBNIS (leer bei Registrierung)


## par.11 EINTAKTUNG (2026-08-20)

Nutzer-Entscheid: *"wir messen es zu ende, aber nicht jetzt."* Reihenfolge: erst die beiden Implementierungs-Reviews (PREREG_implementation_review_*), dann dieser Pfad-A-Arena-Lauf als letzter offener Test der Injektionslinie. Nur Pfad A -- die Pfad-B-Anwendung des Profils ist mit dem par.14-Verdikt des Zielwechsels gegenstandslos.


## par.12 KONKRETISIERUNG VOR DEM START (2026-08-20, vor der ersten Partie)

Die Reviews sind abgeschlossen (Bedingung aus par.11), der Lauf startet.
Festlegungen, die par.7 offen liess:

- **Dosis: `MOSAIC_WERTUNG_SHAPING_W = 0.3`** — die hoechste Dosis des
  gemessenen Haupt-Sweeps (`PREREG_scoring_plate_injection.md`, Arme
  0/0,1/0,3), damit der Vergleichspunkt maximal traegt.
- **Arm-Variable: `MOSAIC_WERTUNG_SCALE_PROFILE`** {0 = Kontrollarm
  flacher Nenner 50, 1 = Profil 4,2/8,6/16,3/25,8/41,3}; Dosis in beiden
  Armen identisch ueber die Eltern-Umgebung.
- Instrument wie im Haupt-Sweep: `paired_arena_env_ab.py`,
  Champion-Netz gegen Heuristik@150(dyn), Netz-Sims 400. Seeds: der
  407er-Satz (`distillation_seeds_main.txt`), Blockgroesse 25,
  `--log-games` (Pflicht fuer k1).
- Vorflug: Determinismus (2x8 identisch) + Reglerwirkung (Profil-Arm
  weicht ab; Achtung: in Runde 1 ist Pfad-A-E exakt 0, die Wirkung muss
  also aus R2+ kommen).
- Erfolgsregel unveraendert par.8, Fokus-Lesart k1.


## par.13 ERGEBNIS (2026-08-20): NICHT-ERFOLG — die Injektionslinie ist zu Ende gemessen

Anordnung nach par.12 (Dosis 0,3, Profil-Knopf als Arm-Variable, 407
Seeds, Champion@400 gegen Heuristik@150dyn, Block 25, log-games).
Vorflug bestanden (Determinismus 2x8 identisch; Profil-Wirkung ja).
Rohdaten `paired_arena_env_pfada_profil.json`.

| | Kontrollarm (flach 50) | Profil-Arm |
|---|---:|---:|
| Siege | 295/407 | 284/407 (McNemar p=0,34) |
| k1 Delta (Block-t) | — | **−0,23 (−1,27)** |
| k2 Delta (Block-t) | — | +0,13 (+1,58) |

Kein Kriterium naehert sich der Schwelle 2,571; kein Siegverlust, kein
Gewinn. **par.8, woertlich registriert:** *"Dann ist der rundenblinde
Nenner als Erklaerung fuer den negativen Dosisbefund ausgeschieden, und
die Injektionslinie ist ohne neue Idee zu Ende gemessen — keine weitere
Dosis- oder Profilvariante."* Zusammen mit dem par.16-Endverdikt des
Zielwechsels sind damit BEIDE Shaping-Pfade (A ueber den Fortschritt,
B ueber den Kopf) abschliessend negativ.
