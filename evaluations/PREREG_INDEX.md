# Index aller Vorregistrierungen (`evaluations/PREREG_*.md`)

**Angelegt 2026-08-08 als Dokumentations-Hygiene-Massnahme.** Ausgangsproblem: von
29 `PREREG_*.md`-Dateien trugen nur 6 einen eigenen Ergebnis-/Verdikt-Abschnitt
(Ueberschrift mit ERGEBNIS/VERDIKT/GESCHEITERT o.ae.); bei den uebrigen 23 stand
das Ergebnis ausschliesslich anderswo (meist `archive/history.md`, teils
`evaluations/STATUS.md`, ein Git-Commit oder eine `evaluations/*.json`-Datei) --
ein neuer Leser konnte OFFEN nicht von ENTSCHIEDEN unterscheiden. Diese 23
Dateien haben seit 2026-08-08 eine angehaengte Statusfussnote am Dateiende
(reine Ergaenzung, der urspruengliche Prereg-Text ist unveraendert).
**Stand 2026-08-13** (gepruefte Zaehlung der Tabellen-Zeilen unten: 13 OFFEN +
34 ENTSCHIEDEN + 1 UEBERHOLT): die Tabelle fasst inzwischen 48 Dateien
zusammen, nicht mehr die urspruenglichen 29 -- seit dem 2026-08-08-Anlass sind
weitere Preregs hinzugekommen (u.a. `PREREG_gpu_inferenzpfad.md`,
`PREREG_gpu_verlagerung.md`, `PREREG_plattenkopf.md`, `PREREG_such_rng_
trennen.md`, `PREREG_async_suche.md`) und mehrere der urspruenglich 23
unbelegten Dateien sind seither ENTSCHIEDEN worden (siehe Tabellen-
Belegstellen). **Hinweis**: eine 48. Datei, `PREREG_v22_fenster.md`, ist
waehrend der urspruenglichen Arbeit (2026-08-08, durch den parallel
laufenden Self-Play-/Koordinator-Prozess) neu hinzugekommen und war NICHT
Teil des urspruenglichen 29er-Bestands -- sie ist hier bewusst NICHT
aufgefuehrt und wurde nicht angefasst.

Sortierung: OFFEN zuerst, dann ENTSCHIEDEN, dann UEBERHOLT.

## NAMENSKONVENTION (verbindlich ab 2026-08-09)

**Anlass**: Nutzer-Kritik *"warum genau hast du immer wieder
unterschiedliche Nummerierung fuer die tasks. das ist verwirrend"* --
berechtigt. Es liefen drei Serien parallel, und die Buchstabenserie war
eine Erfindung des Koordinators, die eine bereits belegte Notation
ueberschrieben hat.

**REGEL: Die Vorregistrierungs-DATEI ist die Kennung.**
1. Jede Entscheidungseinheit hat genau eine `PREREG_*.md`; diese Tabelle
   ist die Registratur. Kurzform = der Datei-Slug
   (`prior_blindfleck`, `task_d_gewichte`, `plattenkopf`), NICHT ein
   Buchstabe.
2. Buchstaben/Zahlen NUR INNERHALB einer Prereg fuer deren eigene Arme
   und Stufen. Keine dokumentuebergreifende Buchstabenserie mehr.
3. Die `#NN`-Serie ist reine RUECKWAERTS-Referenz auf Alt-Befunde in
   `archive/history.md`. **Keine neuen `#NN` vergeben** -- es gibt keine
   Registratur dafuer, niemand kann pruefen was frei ist.
4. Neue Arbeit ohne Prereg bekommt auch keine Kennung. Wer eine Kennung
   braucht, schreibt die Prereg (Task D hatte bis 2026-08-09 keine,
   obwohl er ein mehrarmiges Arena-Experiment ist -- genau der Fall, den
   Regel 1 verhindert).
5. Fuer Nachschlagen im Alt-Bestand (welches Thema steckt hinter `#NN`,
   ist eine Nummer schon vergeben, gibt es Kollisionen): siehe
   `evaluations/TASK_NUMMERN_REGISTRATUR.md` (angelegt 2026-08-09, reine
   Bestandsaufnahme der bisherigen `#NN`-Serie, vergibt selbst keine
   neuen Nummern).

### Zuordnung der Alt-Buchstaben (damit Chat und Commits auffindbar bleiben)

| Alt-Kennung | Herkunft | gilt jetzt als |
|---|---|---|
| Task A (Floor-Shaping W) | Review 2026-08-08 | ohne eigene Prereg; Ergebnis in `archive/history.md` + `paired_arena_env_paired_arena_env_floorw_taskA.json` |
| Task B (Zerlegungs-Diagnose) | Review 2026-08-08 | geschlossen, ohne eigene Prereg; `archive/history.md` |
| Task C (c_visit-Sweep) | Review 2026-08-08 | zurueckgezogen; abgedeckt von `PREREG_ownership_gumbel.md` §B1 |
| Task D (Gewichts-Sweep) | Review 2026-08-08 | **`PREREG_task_d_gewichte.md`** |
| Task E / F / G | Review R2 2026-08-09 | **`PREREG_prior_blindfleck.md`** (E=Blindfleck-Rate, F=Wurzelbreite, G=c_scale-Nachmessung) |
| E1 / E2 | Eskalationsstufen | `PREREG_aggression_stilmessung.md` |
| E3 / E3b | Eskalationsstufen | `PREREG_denial_tiebreak.md` |

**Die Kollision, die das noetig gemacht hat**: "E" (Prior-Blindfleck,
Review R2) und "E3b" (Denial-Tie-Break-Eskalation) haben nichts
miteinander zu tun, sahen aber wie Geschwister aus -- der Koordinator
hat fuer die Review-Tasks Buchstaben genommen, die in den
Eskalations-Preregs laengst belegt waren.



## OFFEN (13)

| Datei | Frage (1 Zeile) | Belegstelle |
|---|---|---|
| `PREREG_ownership_verbraucher.md` | Wie kommt der Ownership-Kopf als VERBRAUCHER in Drafting (Blatt-Shift ueber erwartete Plattenpunkte E_k) und Tiling (marginale Feldwerte einmal je Zug) -- und ab welcher Kopfguete darf er steuern? | **OFFEN, vorregistriert 2026-08-13** (Nutzer-Auftrag "ueberleg dir schon mal wie wir den ownership head ins drafting und tiling miteinbeziehen"). ENTWURF, nichts gebaut. Geprueft: Kopf im Champion untrainiert (`ownership_weight` 0,0, Manifest v21_2d), kein Engine-Verbraucher (ONNX-Ausgang 4 ungelesen). Zwei-Pole-Regler `MOSAIC_OWNERSHIP_W`, Default 0 = byte-identisch (Task-#28-Muster). Reihenfolge: Generator -> Kopf-Training (+Konjunktionen) -> Tor A Kopfguete VOR Verbraucher-Bau. |
| `PREREG_async_suche.md` | Erreicht eine Suchen-ueber-Faeden-Entkopplung (Drafting-Suche als fortsetzbarer Zustandsautomat, `net_batcher.rs` als Sammel-Faden) den Batch, an dem Weg V (`PREREG_gpu_inferenzpfad.md`) strukturell scheitert? | **OFFEN, vorregistriert 2026-08-13** (Nutzer-Auftrag). Stufe 1 (Drafting-Suche als Zustandsautomat, `async`/`await`, additiv in `net_mcts.rs`/`net_batcher.rs`, `MOSAIC_ASYNC_SUCHE`) GEBAUT und Gate A BESTANDEN: 0/1148 Abweichungen sowohl ohne Sammel-Faden (bit-identisch) als auch MIT Sammel-Faden + 16-facher Nebenlaeufigkeit (finale Zugwahl). `cargo test --lib` im isolierten Worktree 387/0/20 (keine Regression). Stufe 2 (Rundenuebergaenge) und Stufe 3 (Durchsatz, Gate C >= 2,0x) OFFEN. |
| `PREREG_gpu_inferenzpfad.md` | Ueber WELCHEN Pfad erreicht die Rust-Engine die GPU -- Cross-Language-Queue zu Python/torch oder ein CUDA-faehiger Rust-Pfad? | **OFFEN, vorregistriert 2026-08-12** (Nutzer-Entscheid "erst Architektur entscheiden"). GEPRUEFTER Befund: `engine/Cargo.toml` hat als einzige Inferenz-Abhaengigkeit `tract-onnx`, tract ist CPU-only -- die Rust-Engine hat KEINEN Weg zu der GPU, deren Kennlinie (aus dem Python-Benchmark `gpu_batch_throughput.py`) den Batch-Startwert 256 begruendet. `PREREG_gpu_inferenz_batcher.md` Regel 2 hatte diese Vorregistrierung verlangt, `PREREG_gpu_verlagerung.md` hat sie uebersprungen. Haelt ausserdem fest, dass der Paritaets-Hash einen GPU-Umbau NICHT ueberleben kann -- jeder Wechsel der Inferenz-Maschinerie aendert die Zahlen; Abnahme ist ein Toleranz- und Staerkenachweis, kein Golden-Hash. |
| `PREREG_gpu_verlagerung.md` | Laesst sich die Inferenz von der CPU auf die GPU verlagern -- erreicht Verschraenkung vieler gleichzeitiger Partien den Batch, an dem die GPU gewinnt? | **OFFEN, vorregistriert 2026-08-10** (Nutzer-Richtung "weg von der cpu und hin zur gpu"). Teil 1 GEMESSEN: Speicher ist kein Engpass (1,5 MiB je Suche, Batch 512 = 0,76 GiB) ⇒ Regel 1, Weg V (Verschraenkung, suchneutral) statt Weg B (Virtual Loss, gating-pflichtig). Teil 2 GESCHLOSSEN (Commit `e1bce64`, ohne neue Messung): die Blatt-Erzeugungsrate wurde ANALYTISCH aus der vorhandenen Task-#32-Messung (`selfplay_time_profile.json`, Netz 62 % / Tiling 27 %) plus Little's Law hergeleitet -- ein eigener Null-Evaluator haette die Baumform degeneriert. Erreichbarer Batch **~140 bis ~590**, Startwert **N=256**, damit in der Gewinnzone der GPU-Kennlinie. Deckel Amdahl 2,6-5,3x. **OFFEN ist jetzt allein die UMSETZUNG von Weg V.** STALE-FALLE 2026-08-12: diese Zeile trug bis hierher noch "offen ist die Blatt-Erzeugungsrate" und hat genau dadurch einen Agenten-Auftrag ausgeloest, der die Zahl neu messen sollte -- sie lag seit `e1bce64` vor. Ein veralteter Index kostet Arbeit, nicht nur Klarheit. `evaluations/interleave_batch_probe.json` (nur Teil-1-Daten) |
| `PREREG_plattenkopf.md` | Lernt ein eigener Kopf die Endwertung je Wertungsplatte (8 Kriterien x eigene/Gegner-Seite, Verlust auf die aktiven maskiert) gut genug, um spaeter die Blattbewertung plattenbewusst zu machen? | **OFFEN, vorregistriert 2026-08-09** (Nutzer-Auftrag). Stufe A = reines Aux-Ziel mit Pflicht-Kriterium 6; Stufe B (Einbau in die Blattbewertung) ausdruecklich offen. Startet erst NACH Task D (Schema-Bump invalidiert den gemeinsamen Cache) |
| `PREREG_platzierungsseite.md` | Ist die PLATZIERUNG (welche Spalte eine fertige Musterreihe bekommt) die eigentliche Blockade fuer geschlossene Spalten -- nicht das Drafting? | **OFFEN, vorregistriert 2026-08-12** (Nutzer-Widerspruch: *"das ist die leichteste aufgabe da sie mit dem basispiel aufbau gut harmoniert"*). Befund am Code: `resolve_tiling_step` (`self_play.rs:1002`) laesst den SOLVER entscheiden, nicht die Suche. Runde 1 ist plattenblind (`tiling_solver.rs:943`, Begruendung deckt nur GELERNTE Proxys, nicht einen berechneten Plattenwert); Runde 2-4 wirkt der Netzwert nur innerhalb der nach Platzierungspunkten vorgefilterten Top-K, der Plattenwert kann einen einzelnen Platzierungspunkt also strukturell nicht ueberstimmen. Erklaert die gemessene Saettigung der Draftingseite (0,70 -> 1,75 gegen Ziel 14). Eingriff `MOSAIC_TILING_PLATTEN_W`, Default 0. Falsifikation vorab: bleiben die vertikalen Punkte unter 3, ist die Platzierung NICHT die Blockade und der naechste Verdacht ist die Versorgung. |
| `PREREG_provokation.md` | Laesst sich eine geschlossene Spalte durch BESCHNEIDUNG der Aktionsmenge gezielt provozieren -- eine Spalte je Partie? | **OFFEN, vorregistriert 2026-08-12** (Nutzer-Korrektur: *"das ist kein plan. das ist hoffen. als erstes brauchen wir eine methode gezielt spiele zu provozieren"*). Stufe 1 VOR der Streuung ins Self-Play; ich hatte die beiden Stufen verwechselt. Nutzer-kalibrierte Abnahmezahl: **>= 7,00 vertikale Plattenpunkte = eine Spalte je Partie** (heute 1,05 = 0,15). Eine Spalte sind 21 Platzierungs- PLUS 7 Plattenpunkte = 28, also rund ein Fuenftel eines guten Endstands. Der Eingriff ist eine Beschneidung der Aktionsmenge, kein neuer Bewerter -- fuenf Anlaeufe ueber die Bewertung sind gescheitert, weil eine Stellungsbewertung keine mehrrundige Farbzusage darstellen kann (`dome.rs:61-70`: jede Zelle verlangt genau eine Farbe). |
| `PREREG_punkte_lambda_unter_kipppunkt.md` | Nutzt der Punkte-Kanal, wenn lambda UNTER dem Kipppunkt liegt, ab dem die Formel 30:15 gegenueber 55:50 bevorzugt? | **OFFEN, vorregistriert 2026-08-11** (Nutzer-Auftrag "punkte optimierung eintakten, inkludiert die punkteminimierung der gegner"). Regel 2 aus `PREREG_punkte_blend_w.md` wurde AUSSCHLIESSLICH bei lambda=2,0 gemessen; der Kipppunkt liegt gerechnet bei **lambda < 0,56**, der Bereich darunter ist ungemessen. Einfaktoriell: w bleibt 0,1 wie im schaedlichen Arm, nur lambda wandert (0,1 / 0,4); der alte Arm 0.1,2.0 zaehlt bei gleichem Basis-Seed 20260902 gepaart mit. opp-Kopf am Champion GEPRUEFT vorhanden. Pflicht-Nebenmessung: die PUNKTESTAENDE, weil die Hypothese von Niveaus handelt und eine Siegquote "mehr Punkte" nicht von "Gegner gedrueckt" trennt. |
| `PREREG_such_rng_trennen.md` | Soll die Suche einen EIGENEN Zufallsstrom bekommen, damit Partien replaybar werden und gepaarte Arenen echte gemeinsame Zufallszahlen haben? | **OFFEN, vorregistriert 2026-08-11** (Nutzer-Auftrag "Instrumentenschulden eintakten"). Befund am Code: `self_play.rs:1523` gibt dasselbe `rng` an Suche UND Spielzustand, `determinize_hidden_information` (`net_mcts.rs:620`) und `Bag::refill_from_tower` (`supply.rs:43`) verbrauchen es -- Suchvolumen verschiebt also die Fliesenversorgung. **Zwei Nutzer-Entscheidungen noetig**: die Paritaetsprobe MUSS brechen (neue Basislinie), und die Elo-Leiter ueberspannt einen Sprung (der Heuristik-Anker wandert mit). **Wichtiger Vorbehalt**: macht nur KUENFTIGE Partien replaybar, nicht die 64 vorhandenen. Empfohlene Reihenfolge: erst die Injektions-Versuche fahren, dann schneiden. |
| `PREREG_injektion_wertungsplatten.md` | Nutzt es, die WERTUNGSPLATTEN (alle acht Kriterien, gegatet auf die aktiven) in die Blattbewertung zu injizieren -- und in welcher Dosis? | **OFFEN, vorregistriert 2026-08-11, HAUPT-SWEEP** (Nutzer-Ruege: "wir wollen die wertungsplatten injizieren, nicht nur die spezialplatten"). `MOSAIC_WERTUNG_SHAPING_W` 0 / 0,1 / 0,3 -- KLEINER als beim Freischalt-Term, weil der Term eine Groessenordnung groesser ist (Kriterium 1 allein ~7,9 Pkt -> tanh = 0,156, das saettigt den geklemmten Blattwert). Basis-Seed 20260911. Pflicht-Nebenmessung ueber `log_games` + `analyze_game_log.py`: Zellen je Rasterreihe und Nahmen-Anteil tiefe Reihen (dicht) statt Abschluesse (zu selten). Enthaelt in Abschnitt 0 die Dokumentation meines Messplan-Fehlers. |
| `PREREG_injektion_dosis.md` | Wie hoch muss die Wertungsplatten-Injektion in der Suche dosiert werden, damit die Spezialfeld-Freischaltung ueberhaupt angesteuert wird -- und rechnet sich das in Siege? | **OFFEN, vorregistriert 2026-08-11** (Nutzer-Auftrag "wie viel wir injizieren muessen wir an einem arena spiel verifizieren"). Sauberster Kontrast im Projekt: DERSELBE Champion, Knopf an gegen aus, kein Training ⇒ keine Trainings-Seed-Varianz. Gegenstand nur `MOSAIC_UNLOCK_SHAPING_W` (0 / 0,3 / 1,0); Freischaltrate ist PFLICHT-Nebenmessung, weil ein blockierender Prior sonst als "Term wirkungslos" fehlgelesen wird. Enthaelt die Ruecknahme meiner Blindheits-Aussage zu Task #93. |
| `PREREG_zufallsknoten.md` | Sollten wir an den Zufallspunkten mit Wahrscheinlichkeiten statt mit Stichwelten rechnen -- und darf der oeffentlich bekannte Stapel-Unterbau weiter mitgemischt werden? | **OFFEN, vorregistriert 2026-08-09** (Nutzer-Frage). Grundlage: es gibt keine private Information, also Zufallsknoten statt ISMCTS. Teil A = Korrektheit (bekannter Unterbau), Teil B = Zufallsknoten mit Kostengate, Teil C = Diagnose der Platte-6-Interaktion |
| `PREREG_bootstrap_horizont.md` | Verbessert ein tieferer Bootstrap-Horizont (3 statt 2) das Value-Ziel -- und ist der zweite Rollout je Uebergang bezahlbar? | **OFFEN, vorregistriert 2026-08-09** (Nutzer-Auftrag). Nur beim v22-Generierungsstart aenderbar (Horizont steckt in den Records, nicht im Cache-Key); Stufe 1 = Kostengate <= +25% Self-Play-Zeit, Stufe 2 = zwei Arme auf identischen Partien via doppelt geschriebener Labels |

## ENTSCHIEDEN (34)

| Datei | Frage (1 Zeile) | Belegstelle |
|---|---|---|
| `PREREG_punktekopf_epsilon.md` | Warum trug das Punkte-Ziel einen 0,1-Gegner-Anteil, und braucht es neben dem Punkte-Kopf ueberhaupt einen eigenen Gegner-Kopf? | **ENTSCHIEDEN 2026-08-10** (Nutzer-Auftrag): Anteil ENTFERNT, Schema 19->20, Epsilon auf 0. Zum Gegner-Kopf: kein Faehigkeits-Argument (die Eingabe ist perspektiv-normalisiert, ein Flip genuegt), sondern nur ein KOSTEN-Argument (zweiter Forward-Pass = 1,6-1,8x) -- und dessen Bedingung ist falsch, weil `blended_leaf_win_prob_with` bei w=0 zurueckkehrt, bevor er gelesen wird. Verdikt: reines Hilfsziel, Nutzen UNBELEGT, Messung vorgeschlagen; Praezedenz `ownership_head`. |
| `PREREG_punkte_blend_w.md` | Traegt w>0 im Punkte-Blend Arena-Staerke, jetzt mechanistisch begruendet? | **REGEL 2, GESCHLOSSEN 2026-08-10**: Kontrolle w=0 321/400 (80,25 %) gegen Arm w=0,1 300/400 (75,00 %) -- Block-Delta -5,25pp, t=-2,68, McNemar p=0,0527. Kein Gewinner, Richtung eher schaedlich; w bleibt 0. Die +6pp der Neukartierung sind mit doppelter Stichprobe NICHT reproduziert, sondern umgekehrt. Hebel muss plattenselektiv werden ⇒ Plattenkopf. `evaluations/paired_arena_env_punkte_blend_w.json` |
| `PREREG_gpu_inferenz_batcher.md` | Schlaegt die GPU bei dem Batch, der real erreichbar ist (~11-44), den CPU-Aggregatdurchsatz -- lohnt ein zentraler Inferenz-Batcher (Alt-Nummer #82)? | **REGEL 1, GESCHLOSSEN 2026-08-10**: erreichbare Punkte 11/22/44 liefern 2.581/6.197/14.060 Evals/s, alle unter der UNTEREN CPU-Schranke von 17.600 -- Verdikt robust gegen die Bandbreite. Break-even erst bei ~64-128. Vermerk: 'nur zusammen mit blatt-paralleler Auswertung sinnvoll'; die GPU ist nicht langsam, sondern ausgehungert. `evaluations/gpu_batch_throughput.json` |
| `PREREG_task_d_gewichte.md` | Traegt ein hoeheres value_weight (0,4/0,8) oder ein hoeheres points_weight (0,25) Arena-Staerke gegen die Kontrolle `v21_2d`? | **H0 2026-08-10, alle drei Arme** ⇒ Regel 5: `VALUE_WEIGHT=0,2` und der Punkte-Default bleiben, Punkt fuer die WDL-/2D-Aera geschlossen. vw04 208:192 (52,0%), vw08 92:108 (46,0%), pw025 68:82 (45,3%, SPRT-H0 nach 75 Paaren). Bild monoton: 0,4 nicht besser, 0,8 schlechter -- der aus der MSE-Aera geerbte Wert liegt offenbar nahe am Optimum. `evaluations/paired_gating_t_d_{vw04,vw08,pw025}_vs_v21.json` |
| `PREREG_punktekopf_platten.md` | Traegt der Punkte-/Gegner-Punkte-Kopf Platten-Information, und differenziert er die ZUEGE danach? | **ENTSCHIEDEN (Stufe 2)**: beide Koepfe sortieren die Wurzelkandidaten plattenabhaengig UM -- `net_points_forecast` Tau-Median 0,792, `net_opp_points_forecast` 0,640, `net_raw_value` 0,778 ⇒ alle Regel 2a (Zug-Differenzierung). Stufe-1-Gate war fehlkonstruiert und ist als ungueltig erklaert. Motiviert `PREREG_punkte_blend_w.md`. `evaluations/punktekopf_platten_stufe2.json` |
| `PREREG_ismcts_determinisierungen.md` | Verbessert Mehrfach-Determinisierung (k=1/2/4) die Spielstaerke gegen die PIMC-Strategy-Fusion? | **GESCHLOSSEN 2026-08-10 unter ZWEI Anordnungen**: Sims-Split (Budget fix) 76,0/77,3/70,0%; gleiche Tiefe je Welt (Budget waechst mit k) 81,75/77,0/73,0% -- k=4 faellt in beiden ab, im zweiten Fall mit VIERFACHEM Budget und in beiden Pflichtinstrumenten signifikant (Block-t -3,73, McNemar p=0,00262, Bonferroni inklusive). Nicht ein Tiefenverlust, sondern: das Mitteln ueber gezogene Welten schadet aktiv. `evaluations/paired_arena_env_ismcts_k.json`, `..._tiefe_k{1,2,4}.json` |
| `PREREG_prior_blindfleck.md` | Verpasst die fixe Gumbel-Wurzelmenge gute Zuege (Task E), hilft groessere Wurzelbreite (F), und wie steht die sigma/Prior-Balance in der WDL-Aera (G)? | **ENTSCHIEDEN**: E Miss-Rate 1,21% ⇒ Regel 1, F nicht eingetaktet; G Aera-Effekt bestaetigt (Verhaeltnis 1,232 -> 2,287), Schwelle 3 nicht erreicht ⇒ keine Wiedereroeffnung, aber Pflicht-Diagnostik je Champion. `evaluations/t_e_prior_blindfleck.json`, `evaluations/t_g_gumbel_scale_v21.json` |
| `PREREG_lambda_wdl_arm.md` | Traegt λ=0,7-Mix in der WDL-Aera (Zielfeld `values_wdl`) Arena-Staerke gegen den Champion? | **H0** -- Ein-Faktor-Gating 63:77 (p=0,21) gegen `v20_2d_opp_brierbest`; Brier 0,18937 vs 0,18749 (schlechter). Befund aera-gebunden; `evaluations/STATUS.md` + Statusfussnote in der Prereg-Datei |
| `PREREG_v21_fenster.md` | Fenster-/Korpus-Zuschnitt fuer die v21-Generation (Zwei-Klassen, Rotation) sowie τ-Annealing-Entscheid | **AUSGEFUEHRT** -- Fenster 29.450 Partien realisiert, `v21_2d_brierbest` ist seit 2026-08-08 Champion (Gating 75:45 p=0,0059 + Frisch-Seed 97:63 p=0,0095, Elo 1358); τ-Teilfrage H0 (τ=1 bleibt). Fenster per Nutzer-Entscheid fix ("das fenster bleibt nun so") |
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
auffindbar" im Sinne von "spurlos verschwunden".

**STALE-KORREKTUR 2026-08-13**: dieser Abschnitt behauptete bis hierher, 3
Dateien (`PREREG_lambda_wdl_arm.md`, `PREREG_ismcts_determinisierungen.md`,
`PREREG_v21_fenster.md`) seien "durchgehend GENUIN offen" -- das war zum
Anlass 2026-08-08 zutreffend, widerspricht aber der TABELLE OBEN, die alle
drei laengst unter ENTSCHIEDEN fuehrt (Zeilen `PREREG_ismcts_
determinisierungen.md`: GESCHLOSSEN 2026-08-10; `PREREG_lambda_wdl_arm.md`:
H0; `PREREG_v21_fenster.md`: AUSGEFUEHRT, Champion seit 2026-08-08). Genau
die Lage, die REGEL 0 verbietet: eine unmarkierte Behauptung, die durch die
eigene Tabelle direkt widerlegt wird. Fuer alle drei gilt seither: das
Trainings-/Arena-Ergebnis WURDE erhoben, siehe Belegstelle in der jeweiligen
Tabellenzeile oben statt an dieser Stelle.
