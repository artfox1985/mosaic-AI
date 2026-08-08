# Index aller Vorregistrierungen (`evaluations/PREREG_*.md`)

**Angelegt 2026-08-08 als Dokumentations-Hygiene-Massnahme.** Ausgangsproblem: von
29 `PREREG_*.md`-Dateien trugen nur 6 einen eigenen Ergebnis-/Verdikt-Abschnitt
(Ueberschrift mit ERGEBNIS/VERDIKT/GESCHEITERT o.ae.); bei den uebrigen 23 stand
das Ergebnis ausschliesslich anderswo (meist `archive/history.md`, teils
`evaluations/STATUS.md`, ein Git-Commit oder eine `evaluations/*.json`-Datei) --
ein neuer Leser konnte OFFEN nicht von ENTSCHIEDEN unterscheiden. Diese 23
Dateien haben seit 2026-08-08 eine angehaengte Statusfussnote am Dateiende
(reine Ergaenzung, der urspruengliche Prereg-Text ist unveraendert). Diese
Tabelle fasst den Stand aller 29 Dateien zusammen. **Hinweis**: eine 30.
Datei, `PREREG_v22_fenster.md`, ist waehrend dieser Arbeit (2026-08-08, durch
den parallel laufenden Self-Play-/Koordinator-Prozess) neu hinzugekommen und
war NICHT Teil des urspruenglichen 29er-Bestands -- sie ist hier bewusst
NICHT aufgefuehrt und wurde nicht angefasst.

Sortierung: OFFEN zuerst, dann ENTSCHIEDEN, dann UEBERHOLT.

## OFFEN (3)

| Datei | Frage (1 Zeile) | Belegstelle |
|---|---|---|
| `PREREG_lambda_wdl_arm.md` | Traegt λ=0,7-Mix in der WDL-Aera (Zielfeld `values_wdl`) Arena-Staerke gegen den Champion `v20_2d_opp_brierbest`? | `lam07_wdl2_s2` gueltig trainiert, Arena-Gating steht aus -- kein Ergebnis in `archive/history.md` oder JSON auffindbar; `evaluations/STATUS.md`, Abschnitt "OFFENES GATING (v20-Aera, hat Vorrang)" |
| `PREREG_ismcts_determinisierungen.md` | Verbessert Mehrfach-Determinisierung (k=1/2/4, rechen-neutral via Sims-Split) bei 600 Netz-Sims die Spielstaerke gegen die PIMC-Strategy-Fusion? | Knopf vorbereitet, Messung steht in der "NACH-v21-QUEUE" (Nutzer-Go 2026-08-08), noch nicht gelaufen; `evaluations/STATUS.md`, Abschnitt "NACH-v21-QUEUE", Punkt 2 |
| `PREREG_v21_fenster.md` | Fenster-/Korpus-Zuschnitt fuer die v21-Generation (Zwei-Klassen, Rotation) sowie τ-Annealing-Entscheid fuer den Sockel | Fenster-Zuschnitt selbst fix entschieden; τ-Teilfrage GESCHLOSSEN (H0, τ=1 bleibt); die eigentliche Fenster-Befuellung/Training/Gating vom Nutzer 2026-08-08 zurueckgestellt; `evaluations/STATUS.md`, Zeile 15-16 |

## ENTSCHIEDEN (25)

| Datei | Frage (1 Zeile) | Belegstelle |
|---|---|---|
| `PREREG_aggression_stilmessung.md` | Hebt der Aggressions-Blend (w/λ) die eigene Punktzahl/Gegner-Floor bei gleicher Siegquote, auch gegen einen starken Gegner? | Eigener Ergebnis-Abschnitt in der Datei ("STARK-GEGNER-ERGEBNIS", "E1-/E2-ERGEBNIS"): keine Uebernahme, Blend inert |
| `PREREG_denial_tiebreak.md` | Verbessert ein Denial-Tie-Break an der Wurzel (ε-Fenster, niedrigste Gegner-Punktprognose) das Spiel ohne Schaden? | Eigener Ergebnis-Abschnitt in der Datei ("ERGEBNIS ... E3 GESCHEITERT") |
| `PREREG_platten_intervention.md` | Hebt ein Endgame-/Wertungsplatten-Aux-Kopf die R5-Plattenkalibrierung, und schlaegt er den Champion in der Arena? | Eigener Ergebnis-Abschnitt in der Datei ("ARENA-ERGEBNIS: H0"); Kopf wird Trainings-Upgrade, Champion unveraendert |
| `PREREG_suchpfad_nachmessungen.md` | Re-Validierung von Floor-Gewicht, m-Formel und τ-Annealing in der WDL-Aera (3 Messungen) | Eigener Ergebnis-Abschnitt in der Datei ("MESSUNG-3-ERGEBNIS"); alle 3 Messungen H0, Status quo bestaetigt |
| `PREREG_t35b_ranking.md` | Verbessert ein Ranking-Loss-Arm (Task #35b, WDL-Aera) die Orakel-validierten Policy-Metriken? | Eigener Ergebnis-Abschnitt in der Datei ("ERGEBNIS: Orakel-Vorpruefung NEGATIV -> kein Gating"), #35b geschlossen |
| `PREREG_t37_tiling_kriterium.md` | Ist reines P(Sieg)-Ranking beim Tiling-Abschluss besser als das Bestandskriterium punkte*P(Sieg) (Task #37)? | Eigener Ergebnis-Abschnitt in der Datei ("ERGEBNIS: H0 -- #37 GESCHLOSSEN") |
| `PREREG_2d_encoder.md` | Traegt der 2D-Conv-Encoder from-scratch mehr zur Netzstaerke bei als das flache MLP (Task #11, Phase 2)? | Orakel 6/6 fuer 2D, aber Arena-Gating 416:384 (Wash, p=0,30); `archive/history.md` Z. ~6660-6741 |
| `PREREG_corpus_dose.md` | Hilft mehr Self-Play-Korpus (900 vs 450 Dateien) bei unveraenderter Suchtiefe der Netzqualitaet (Vorstudie Task #14)? | Orakel 6/6 UND Arena bestaetigt (479:321, p<0,0001); `archive/history.md` Z. ~6746-6821 |
| `PREREG_pcr.md` | Lohnt sich Playout-Cap-Randomization (p=0,25/cheap=150) bei gleichem Wandzeit-Budget (Task #14)? | Negativ, Orakel 0/6, Doku-Arena 67:83 (H0); `archive/history.md` Z. ~7008-7063 |
| `PREREG_pcr_mild.md` | Erfuellt ein milderes PCR-Regime (p=0,5/cheap=300) das Wandzeit-Kriterium (>=1,15x)? | Verfehlte 1,15x (nur 1,118x) -> Training/Arena dieser Prereg nie gelaufen; `archive/history.md` Z. ~7226-7256 |
| `PREREG_value_scale_correction.md` | Hebt eine monotone Value-Skalen-Korrektur (Task #30, `MOSAIC_VALUE_CAL_A/B`) die Spielstaerke? | Erstlauf +6pp n.s., Replikation zeigte KEINEN Effekt; `archive/history.md` Z. ~7461-7489 und ~9431-9457 |
| `PREREG_r5_value_calibration.md` | Reagiert der Value-/Punkte-Kopf in Runde 5 proportional richtig auf Wertungsplatten-Aenderungen (Task #27)? | Unterkalibrierung bestaetigt (Steigung 0,06-0,09 statt ~1); `archive/history.md` Z. ~7065-7089 |
| `PREREG_v20_kampagne.md` | Gewinnt der v20-WDL-Kandidat (Zwei-Klassen-Self-Play) das Champion-Gating gegen `v19_2d_best`? | Gewonnen 208:162, p=0,0178, neuer Champion seit 2026-08-07; `archive/history.md` Z. ~9847, ~10250 |
| `PREREG_ownership_gumbel.md` | Teil A: wird der Ownership-Kopf (Task #9) Standard? Teil B: bleibt Gumbel-c_scale bei 1,0 (Task #18)? | Teil A bereits im Dateitext entschieden (bleibt 0,0); Teil B c_scale bleibt 1,0 trotz hoeherer Siegquote bei 0,3 (Score-Einbruch beidseits); `archive/history.md` Z. ~6133-6210 |
| `PREREG_aggressions_neukartierung.md` | Zeigt einer der 3 (w,λ)-Blend-Arme einen signifikanten Staerkegewinn gegen die w=0-Kontrolle (v20-Aera, F1-gefixt)? | Alle 3 Arme H0 (149/154/161/155 von je 200), w bleibt ueberall 0; `evaluations/paired_arena_env_aggr_neukartierung.json` |
| `PREREG_task28_aggression.md` | Senkt ein opp-Punkte-Kopf + λ_aggr-Blend die Gegnerpunkte ohne Siegquotenverlust (Task #28, Hauptmessung)? | Beide Gates bestanden, aber kein Arm p<0,05 (bester -6,16 Punkte, p=0,078); `archive/history.md` Z. ~7140-7183 |
| `PREREG_task34_erosion_arms.md` | Welcher Mechanismus (Label-Smoothing vs entstauchter Bootstrap-Blend) mildert die WDL-Erosion am besten (Task #34)? | Entstauchter Blend gewinnt (Peak 0,1971, Erosion +0,005) -> #34-Zielkonfiguration; `archive/history.md` Z. ~9185-9229 |
| `PREREG_task36_value_saturation.md` | Saettigt der Value-Kopf mit mehr Self-Play-Partien, oder bleibt er "spielhungrig" (Task #36)? | "Spielhungrig" bestaetigt (monotone Verbesserung ueber 202/405/810 Dateien); v20-Budget nicht gekuerzt; `archive/history.md` Z. ~9965-9998 |
| `PREREG_nach34_paket.md` | Tragen Aux-Koepfe (Arm 1 `t12_dist`, Arm 2 `t9_own`) am neuen #34-WDL-Ziel zur Staerke bei? | Beide Arme geschlossen (t9_own Paritaet, t12_dist Seed-Rauschen in Replikation); `archive/history.md` Z. ~10005-10039 |
| `PREREG_r4_value_calibration.md` | Wie kalibriert ist der Value-/Punkte-Kopf am Runde-4-Ende gegen gesampelte exakte Ground Truth (Task #27-Folge)? | "Kein Befund" (R² negativ), zusaetzlich Methoden-Alarm (Vorzeichen-Anker nur 9/24) -> Folge-Messung "R4b" initiiert; Git-Commit `cb4773d`, kein Prosa-Absatz in history.md |
| `PREREG_lambda_target.md` | Senkt ein λ-Mix aus Spielausgang und Root-Completed-Q (900er-Fenster) die Value-Zielvarianz und die Arena-Staerke? | Offline 6/6 positiv, Arena verloren (43:57, H0); `archive/history.md` Z. ~6969-7002 |
| `PREREG_lambda_v18only.md` | Wiederholt sich der λ=0,7-Effekt auf reinem v18-Korpus (65,67% root_q-Mix)? | Arena gewonnen (227:173, p=0,0101) -> v20-Standard-Kandidat, spaeter durch WDL-Aera-Grenze relativiert; `archive/history.md` Z. ~7107-7138 |
| `PREREG_lambda_ceiling_and_gating.md` | Welches lambda_aggr ist sicher, und schlaegt v19_2d_opp@(w=0,1,lambda) den Champion? | Kein Staerkebeleg (205:195, p=0,68), keine Promotion; `archive/history.md` Z. ~7315-7351 |
| `PREREG_lambda07_opp_candidate.md` | Schlaegt der Kandidat v19_2d_opp_l07 (900er-Fenster) den Champion im Arena-Gating? | Verloren (33:47, H0, p=0,167); `archive/history.md` Z. ~7374-7416 |
| `PREREG_value_rank_metric.md` | Validiert die Value-Rangmetrik `value_kendall_tau_vs_oracle_q` (Task #29) gegen arena-entschiedene Paare? | Nicht validiert (2/6 Richtungen korrekt, Zufallsniveau); `archive/history.md` Z. ~7532-7567 |

## UEBERHOLT (1)

| Datei | Frage (1 Zeile) | Belegstelle |
|---|---|---|
| `PREREG_task28_power_extension.md` | Konfirmiert eine frische Stichprobe den la20-Denial-Effekt, und wo liegt der Kipppunkt (λ in {0;0,5;1;2;3;5})? | Praemisse (realer Effekt) entfiel: der scheinbare Widerspruch der Konfirmationsstichprobe war ein Block-Korrelations-Artefakt, kein echter Effekt in irgendeine Richtung -- Kipppunkt-Kartierung dadurch gegenstandslos gestrichen; `archive/history.md` Z. ~7278-7313 |

---

## Faelle ohne auffindbares Ergebnis

Bei **keiner** der 23 neu befussnoteten Dateien war die Lage "kein Ergebnis
auffindbar" im Sinne von "spurlos verschwunden" -- die 3 als OFFEN markierten
Dateien (`PREREG_lambda_wdl_arm.md`, `PREREG_ismcts_determinisierungen.md`,
`PREREG_v21_fenster.md`) sind durchgehend GENUIN offen: das jeweilige
Trainings-/Arena-Ergebnis wurde nachweislich noch nicht erhoben (bestaetigt
durch `evaluations/STATUS.md`, das sie explizit als laufend/ausstehend
fuehrt), nicht weil eine Spur verloren ging. Das sind fuer den Koordinator die
interessanten Faelle: bei `lambda_wdl_arm` und `v21_fenster` ist das trainierte
Modell bzw. der Fenster-Zuschnitt bereits vorhanden, nur das Gating fehlt noch.
