<!-- STATUS: ENTSCHIEDEN | Frage: Holt ein kleineres `c_scale` den Spaltenbau in der Tiefe zurueck? | Beleg: NEIN (par.5, 2026-09-01): 0,5000 gegen die Kontrolle 0,5150, Schwelle 0,618 klar verfehlt, Staerke-Arm entfaellt regelgemaess. Damit ist die WURZEL-Ebene als Ort der Tiefen-Delle erledigt -- vier Eingriffe (Value lauter, leiser, Punkte-Blend, Prior/Value-Balance) bewegen sie nicht. Der Knopf `MOSAIC_GUMBEL_C_SCALE` bleibt gebaut mit Default 1,0, paritaetsgeprueft. -->

# Vorregistrierung: `c_scale` als Regler zwischen Prior und Value-Kopf

**Angelegt 2026-09-01** auf Nutzer-Auftrag ("dann mach daraus einen knopf,
damit wir uns das in der arena ansehen koennen"), VOR jeder Messung.

## par.1 Der Anlass, gemessen

`tools/gumbel_scale_calibration.py` auf `v23-b01_brierbest`, 300 Zustaende
(`PREREG_prior_blind_spot.md` par.G3):

| | @100 Sims | @400 Sims |
| --- | --- | --- |
| `delta_q_median` (Spanne der rohen q zwischen Geschwisterzuegen) | 0,0180 | 0,0168 |
| `delta_lnprior_median` | 0,665 | 0,875 |
| `max_N_median` | 35 | 96 |
| `ratio_sigma_over_prior_median` | 2,135 | **2,814** |
| `c_scale` fuer Gleichgewicht | 0,468 | **0,355** |

`sigma(q) = (50 + max_N) * c_scale * q`. Weil `max_N` mit der Suchtiefe
waechst, waechst das Uebergewicht des Value-Terms mit ihr -- **der Kopf wird
nicht klueger, nur lauter**. Der Prior traegt das Spaltenwissen (par.2l von
`search_depth_column_optimum`: bei plattenblindem Prior tritt der Tiefeneffekt
gar nicht auf). b01 baut bei 100 Sims 0,7200 volle Spalten, bei 400 nur
0,5150.

**Das ist eine Hypothese ueber den Mechanismus, keine Messung seiner
Behebbarkeit.** Diese Prereg misst Letzteres.

## par.2 Anordnung

**Arme:** `MOSAIC_GUMBEL_C_SCALE` = **1,0** (Kontrolle, Bestand) gegen
**0,36** (der gemessene Gleichgewichtswert bei 400 Sims). Nur zwei Arme; eine
Dosis-Reihe waere ein eigener Zuschnitt.

**Instrument A -- Spalten:** argmax-Self-Play @400 Sims, 200 Partien je Arm,
gleicher Seed 20260931, `--deterministic --no-root-noise`. Messweg wie in
`PREREG_r5_value_calibration.md` par.12 (letzter Record je Partie,
`col_fill_py`, Spalte voll bei fill == 6; gegen den Tor-2a-Lauf mit 0,5150
zifferngleich validiert). **Kontrolle liegt bereits vor: 0,5150.**

**Instrument B -- Staerke:** `tools/anchor_arena.py` gegen den eingefrorenen
Anker `hv1_anchor`, n=150, `--force-cross-era`, Seed-Basis 900001.
**Kontrolle liegt bereits vor: 127:23 = 84,7 Prozent** (2026-09-01).

**Warum gegen den ANKER und nicht netz-gegen-netz:** der Knopf ist
prozessglobal (OnceLock, net_mcts.rs) und damit NICHT pro Seite setzbar. In
einer Netz-gegen-Netz-Arena bekaemen ihn beide Seiten, der Effekt hoebe sich
teilweise auf. Der eingefrorene Anker laeuft in einem EIGENEN Prozess mit
eigenem Wheel und sieht die Umgebungsvariable nicht -- die Messung ist damit
sauber einseitig. (Wer den Knopf spaeter pro Seite braucht, migriert ihn nach
`SearchConfig`; Praezedenz `implicit_minimax_alpha`.)

## par.3 Entscheidungsmass, VORAB

**Beide Groessen zaehlen, und zwar in dieser Reihenfolge:**

1. **Staerke darf nicht fallen.** Arm 0,36 gegen die Kontrolle 127:23 bei
   n=150. Faellt die Siegquote signifikant (Vorzeichentest p < 0,05), ist der
   Arm ERLEDIGT -- unabhaengig davon, was die Spalten tun.
2. **Spalten muessen steigen**, sonst war die Mechanismus-Hypothese falsch:
   Schwelle **>= 0,618** volle Spalten (die halbe Delle zwischen 0,5150 und
   0,7200 -- dieselbe Schwelle wie in Phase 3, damit die beiden Messungen
   vergleichbar bleiben).

**Verdikt-Matrix:**

| Staerke | Spalten | Folge |
| --- | --- | --- |
| haelt | >= 0,618 | **Treffer**: der Regler stand falsch. Uebernahme prueft eine Gating-Kante gegen den Champion |
| haelt | < 0,618 | Mechanismus-Hypothese widerlegt; `c_scale` bleibt 1,0, Befund bleibt registriert |
| faellt | egal | TAUSCH, wie die Sims-Kurve. `c_scale` bleibt 1,0; der Befund waere dann, dass Spalten und Staerke an dieser Stelle GEGENLAEUFIG sind -- was den Leitstern betrifft und dokumentiert gehoert |

## par.4 Kosten und Abbruch

200 Partien argmax @400 kosten rund 31 min je Arm, die Anker-Kante rund
40 min. **Der Spalten-Arm laeuft ZUERST**: zeigt er nichts, ist die
Staerke-Messung ueberfluessig, weil dann nichts uebernommen wuerde.

**Was diese Prereg NICHT tut:** sie sucht kein Optimum. 0,36 ist der gemessene
Gleichgewichtspunkt, kein getunter Wert; ein Sweep waere ein eigener
Zuschnitt mit eigener Auswahlregel (Selbstbestaetigungs-Waechter).

## par.5 GEMESSEN: DER ARM TRAEGT NICHT -- Hypothese widerlegt (2026-09-01)

Instrument A (Spalten), argmax @400, 200 Partien, Seed 20260931,
`MOSAIC_GUMBEL_C_SCALE=0.36` (im Lauf-Manifest als `engine_config.gumbel_c_scale`
verzeichnet):

| Arm | volle Spalten je Seite | SE |
| --- | --- | --- |
| `c_scale = 1,0` (Kontrolle) | 0,5150 | 0,0332 |
| **`c_scale = 0,36`** | **0,5000** | 0,0364 |
| Referenz: `c_scale = 1,0` bei 100 Sims | 0,7200 | 0,0396 |

**Differenz -0,015, also Rauschen. Die Schwelle 0,618 ist klar verfehlt.**
Nach par.4 entfaellt damit Instrument B (Staerke): es war ausdruecklich an ein
positives Spalten-Ergebnis gebunden, und ohne Spalten-Gewinn gaebe es nichts
zu uebernehmen. **`c_scale` bleibt 1,0.**

**Was damit widerlegt ist -- und es war MEINE Herleitung, nicht die des
Nutzers:** die Rechnung sah sauber aus (`ratio_sigma_over_prior` 2,81 bei 400
Sims gegen 2,14 bei 100, `delta_q` nur 0,017, Gleichgewicht bei 0,36), und
daraus folgte scheinbar zwingend, dass der Value-Term den spaltentragenden
Prior uebertoent, je tiefer gesucht wird. **Setzt man das Verhaeltnis auf
Gleichgewicht, aendert sich am Spaltenbau NICHTS.** Die Groesse ist real, ihre
kausale Rolle war eine Hypothese, und sie ist gefallen.

**Damit ist die Wurzel-Ebene als Ort der Tiefen-Delle ERLEDIGT.** Vier
Eingriffe an ihr sind gemessen wirkungslos oder schaedlich:

| Eingriff | Wirkung auf volle Spalten @400 |
| --- | --- |
| `VALUE_CAL_B = 2,0` (Value lauter) | 0,3900 (-0,125, schaedlich) |
| `VALUE_CAL_B = 0,5` (Value leiser) | 0,5325 (+0,018, n.s.) |
| `POINTS_UTILITY_W = 0,1` (Punkte beimischen) | 0,4850 (-0,030, n.s.) |
| `c_scale = 0,36` (Prior/Value ins Gleichgewicht) | 0,5000 (-0,015, n.s.) |

Weder Betrag noch Balance noch Zusatzinformation am Blattwert bewegen die
Delle. **Was bleibt, liegt TIEFER im Baum**: nicht die Gewichtung der
Wurzelkandidaten, sondern was die Suche in den Fortsetzungen findet und nach
oben propagiert. Das ist die Frage, die
`PREREG_search_depth_column_optimum.md` Stufe 4 stellt -- und sie ist jetzt
enger gefasst, weil vier Wurzel-Erklaerungen ausgeschlossen sind.

**Der Knopf bleibt, mit Default 1,0.** Er kostet nichts (Paritaet an 20
Partien belegt), er ist im Manifest sichtbar, und die naechste Frage an die
Prior/Value-Balance kann ihn ohne Bau benutzen.
