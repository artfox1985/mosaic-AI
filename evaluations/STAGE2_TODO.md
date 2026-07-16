# Mosaic-AI AlphaZero-Loop — Status & Fahrplan

Historische Details (alte v1-v9-Zählung vor dem Reset, Bug-Diagnosen,
verworfene Ansätze) stehen in der Git-Historie dieser Datei und in den alten
`v*_eval.md`s — hier nur der aktuelle Stand und die aktiven Regeln.

## Update (Phase 8): Kurswechsel — Stufe 2 ist jetzt der Produktions-Pfad

**Die weiter unten dokumentierte Spur-B-Schlussfolgerung ("Stufe 1 bleibt der
Produktions-Pfad") ist überholt.** Nutzer-Entscheidung, keine neue
SPRT-widerlegte Messung: "Stufe 2 ist nicht tot. Wir werden Stufe 1 sterben
lassen und Stufe 2 entsprechend anpassen. Stufe 1 ist für mich sinnlos, da
spiel ich gleich gegen die Heuristik." Stufe 1 (DFS-Solver-Blattwert) bleibt
im Code liegen (dormant, `LeafEval::Dfs` weiterhin wählbar), wird aber nicht
mehr aktiv verwendet oder weiterentwickelt. `net_mcts::ACTIVE_LEAF =
LeafEval::Net` ist jetzt der Standard (modulweite Konstante statt
durchgereichtem Parameter).

Zusammen mit dem Kurswechsel wurde die Value-Head-Architektur zurückgesetzt:
**`MosaicNet` hat wieder einen `value_head` (±1 Win/Loss, Tanh) PLUS einen
separaten `points_head`** (der alte score-Regressions-Wert, jetzt nur noch
Hilfsziel). Das unten dokumentierte "Value-Target-Formel"-Kapitel
(`tanh(own/50) − 0.1·tanh(opp/50)`, `VALUE_SCHEMA_VERSION=9`) beschreibt die
VORHERIGE Architektur und ist damit ebenfalls überholt — alle Val-R²-Zahlen
und Sweep-Ergebnisse in diesem Dokument (VALUE_WEIGHT-Sweep, Kapazitätstests,
Confounder-Check) beziehen sich auf das alte Zielformat und sind für die
neue ±1-Architektur nicht direkt übertragbar. `VALUE_WEIGHT=1.0`,
`POINTS_WEIGHT=0.5` in `config.py`.

**Neu: exakte Alpha-Beta-Suche für Runde 5** (`engine/src/round5.rs`). Ab
Runde 5 wird keine Kuppelplatte mehr gelegt und die gesamte Zufälligkeit der
Runde (Fabrik-Befüllung) ist bereits vor Rundenbeginn aufgelöst — Runde 5 ist
damit ein Full-Information-Endspiel, für das PUCT/Netz-Approximation (Stufe
1/2) durch exakte Minimax-Suche mit Alpha-Beta-Pruning ersetzt wird
(`round5::choose_action`, in allen 6 heuristik-/netzseitigen
Entry-Points von `mcts.rs`/`net_mcts.rs` verdrahtet). Blattbewertung nutzt
die EXAKTE Wertungsplatten-Endwertung (`calculate_end_scoring`) statt der
Fortschritts-Heuristik `wertung_progress`, da das Kuppelraster ab Runde 5
eingefroren ist — kein Näherungsfehler mehr in der letzten, oft
entscheidenden Runde. Zeitbudget-basiert (150ms/Entscheidung, empirisch
kalibriert, siehe Modul-Kommentar) statt eines reinen Knotenbudgets, weil die
Kosten pro Suchknoten je nach Brettkomplexität stark schwanken. Das
adressiert strukturell einen Teil der unten dokumentierten Spur-B-Beobachtung
("Stufe 1/2 strukturell blind für Rundenübergänge") — nicht durch besseres
Mehrrunden-Lernen, sondern durch exaktes Lösen der letzten, isoliert
lösbaren Runde.

**Neu: Kuppelstapel-Zieh-Mechanik regelwerkstreu nachgebaut.** Beim Ziehen
vom verdeckten Kuppelstapel zeigt die Rückseite nur den TYP (Wild/Special),
nicht die Farbanordnung — die sieht man erst, wenn man aufhört
(`Action::DrawStackPeek`/`Action::DrawStack`, sequentielles Ziehen statt
vorab festgelegtem `num_drawn`). Nicht gewählte gezogene Platten legt der
Spieler in selbst gewählter Reihenfolge zurück unter den Stapel
(`DrawFromStackMove::return_order`, Multiset-validiert wie `moon_order`).
Neues Feature `dome_wild_remaining_frac` (Wild-Anteil der noch verdeckten
Restplatten) ergänzt die bereits bestehende `dome_pool_mask` um ein
explizites Aggregat — `INPUT_SIZE` 707→708. Für die Heuristik-MCTS bewusst
NICHT nachgebaut (kein Netz nötig, Peek/Choose wird dort per einfacher
Wiederverwendung des normalen Suchloops aufgelöst, siehe
`self_play.rs::apply_chosen_action`).

**Bugfixes aus dem Server-Spiel (2026-07-16):**
- Phantom-Fliesen (per Bonuschip virtuell ergänzt) rendern jetzt korrekt am
  linken Ende der Musterreihe (zuletzt hinzugefügt, analog zur echten
  Azul-Füllrichtung rechts→links) statt am rechten Ende (`static/js/app.js`,
  Index-Mapping in der Musterreihen-Zellberechnung war invertiert).
- Kuppelstapel-Ziehungen sind jetzt durch die verfügbaren Punkte gedeckelt
  (max. so viele Ziehungen wie Punkte vorhanden, je 1 Pkt/Ziehung) —
  Ausnahme: bei 0 Punkten ist der ERSTE/Pflichtzug eines Vorgangs trotzdem
  erlaubt (Deadlock-Vermeidung, Punkte fallen nie unter 0,
  `game::validate_draw_stack_peek`).
- Rückseite (Typ) der OBERSTEN Stapelplatte ist jetzt jederzeit sichtbar
  (neues Feld `dome_stack_top_type`), nicht erst nach dem Ziehen — entspricht
  einem physischen Tisch, an dem die Rückseite immer offen liegt. Beim
  Mehrfach-Ziehen werden jetzt ALLE bisher gezogenen Rückseiten angezeigt
  (nicht nur die zuletzt gezogene), und da beide Spieler denselben
  gemeinsamen Zustand sehen (Hotseat, kein separates Per-Spieler-View), ist
  diese Information automatisch auch für den Gegenspieler sichtbar.
- Start-Kuppel-Platzierungsheuristik war in `self_play.rs` UND `py.rs`
  unabhängig dupliziert (identische Farb-Häufigkeits-Formel) — `py.rs` ruft
  jetzt `self_play::choose_start_placement` direkt auf.

98 Rust-Tests grün (inkl. neuer Tests für Runde-5-Alpha-Beta,
`return_order`-Validierung, Punkte-Deckel). Browser-verifiziert (Server-Play
End-to-End: sequentielles Ziehen, Rückseiten-Sichtbarkeit, Punkte-Deckel,
Phantom-Fliesen-Rendering).

**Offen:** Stufe 2 unter der neuen ±1-Architektur ist noch NICHT gegen einen
Champion oder gegen Heuristik gemessen worden (alle Arena-Zahlen unten
beziehen sich auf die alte Architektur). Das ist der logische nächste
Schritt, sobald wieder trainiert wird.

## Aktueller Stand (Stand: v6, siehe Masterplan unten für die nächsten Schritte)

Der erste Reset (2026-07-07, v1/v1b/v2/v2b/v2c) ist selbst überholt — das
Datenfenster wurde seitdem komplett neu aufgesetzt (~11.000 frische
Heuristik-Spiele), Zählung beginnt wieder bei v1. VALUE_WEIGHT ist final auf
**1** gesetzt (siehe Confounder-Ergebnis unten: das Gewicht ist für Stufe 1
UND Stufe 2 irrelevant, kein weiterer Sweep nötig).

**v2 ist seitdem Champion und hat vier Kandidaten (v3, v4, v5, v6) klar
abgewehrt** — alle vier kamen per SPRT-Arena (siehe Werkzeuge unten) als
"Gleich stark" zurück, keiner hat das +100-Elo-Gate gerissen:

| Netz | Fenster-Zusatz ggü. Vorgänger              | vs. v2 (Stufe 1) | vs. v2 (Stufe 2)   |
| ---- | ------------------------------------------- | ---------------- | ------------------ |
| v3   | +Champion-Self-Play (Warm-Start v2)          | Gleich stark     | —                   |
| v4   | +2300 Champion-Self-Play (Warm-Start v2)     | Gleich stark     | —                   |
| v5   | +Champion-Self-Play (Warm-Start v2)          | 39:37, 51% (Gleich stark) | —          |
| v6   | +4000 Stufe-2-Bootstrapping-Spiele (v2, Warm-Start v2) | 35:37, 49% (Gleich stark) | 45:41, 52% (Gleich stark) |
| v7   | Kuratiertes ~8800-Spiele-`v2`-Fenster (Warm-Start v2) | 42:58, 42% (Gleich stark) | — |
| v7cold | GLEICHES Fenster wie v7, Cold-Start (kein `--load`) | 23:21, 52% (Gleich stark, echte Paritaet) | — |

**Wichtiger Fund: v7 vs. v7cold direkt (Stufe 1) — 22:41, 35%, v7cold
SIGNIFIKANT stärker** (SPRT-Entscheid, kein Ressourcenlimit). Auf
IDENTISCHEM Fenster ist Cold-Start klar stärker als Warm-Start — erster
eindeutiger (nicht "Gleich stark") Ausgang in der ganzen Serie. Erklärt
plausibel, warum v3-v7 (alle Warm-Start) durchgehend bei "Gleich stark"
gegen v2 hängen blieben: Warm-Start scheint das Training in der Nähe von
v2s Gewichten festzuhalten, statt einen echt neuen, besseren Punkt zu
finden. Bei Stufe 2 zeigt sich derselbe Vorteil NICHT (v7(Stufe2) vs.
v7cold(Stufe2): 25:24, 51%, echte Paritaet) — konsistent damit, dass die
Stufe-2-Schwäche am Value-Head selbst liegt, nicht an der Policy-Qualität.
**Konsequenz: Cold-Start wird die neue Standard-Strategie für Kandidaten.**

Details je Generation in `v3_eval.md` bis `v7_eval.md` (v7cold: eigene
Eval-Datei, da kein regulärer Kandidat im bisherigen Sinn). **Wichtiger
Nebenbefund (Datenfenster-Kontrolle):** `train.py` lädt beim Training IMMER
alle `.pkl`-Dateien aus `data/` (`glob.glob(*.pkl)`, keine Filterung nach
Version/Herkunft) — es gibt keinen Mechanismus, der sicherstellt, dass nur
die in den "trainiert mit"-Listen dokumentierten Spiele tatsächlich einfließen.
v6 lud beim Training 1735 Dateien (~17.350 Spiele), deutlich mehr als die in
`v6_eval.md` dokumentierten ~13.400 — der `v2`-Self-Play-Anteil allein ist
über v3-v6 unbemerkt auf 1135 Dateien (~11.350 Spiele) angewachsen (statt der
dokumentierten 600/6000), vermutlich weil der Self-Play-Befehl mehrfach
nachgezogen wurde, ohne alte Dateien zu ersetzen. Diagnose-Daten aus der
Stufe-2-Ursachenforschung wurden zwischenzeitlich aus `data/` entfernt
(betraf v3-v6 nicht, da sie erst NACH v6 entstanden) — **vor dem v7-Training
muss der `data/`-Ordner bewusst kontrolliert werden** (siehe Masterplan
Schritt 1 unten), sonst trainiert v7 auf einem unkontrollierten Gemisch statt
dem beabsichtigten ausgedünnten Fenster.

Das ändert nichts an der Kernaussage: **die reine Fenstergröße ist als Hebel
jetzt empirisch ausgereizt** (vier Versuche, ein immer größeres/unklareres
Fenster, nie ein Erfolg) — Zeit für die nächsten Eskalationsstufen.

## Masterplan für die nächsten Generationen (ab v7)

Zwei parallele Spuren — Spur A treibt die eigentliche Spielstärke voran
(Prioritaet), Spur B ist die Stufe-2-Ursachenforschung (kein Blocker für A).

### Spur A: v7 — Champion v2 endlich herausfordern

Stufe 1 ("+2000 Spiele") ist nach vier Fehlversuchen (v3-v6) empirisch
ausgereizt (siehe oben). **Sims-Erhöhung wurde verworfen** (siehe unten,
"Verworfene Idee") — v7 testet stattdessen ISOLIERT nur eine einzige neue
Variable: ein bewusst kontrolliertes, unverwässertes Fenster, ohne
Sims-Änderung. Kein neues Self-Play nötig — genug `v2`-Spiele liegen
bereits vor, es muss nur kuratiert werden:

1. **Fenster kuratieren — konkret in `data/` (nicht nur konzeptionell):**
   `train.py` lädt beim Training ALLE `.pkl`-Dateien aus `data/` ohne
   Filterung (siehe Nebenbefund oben) — kuratieren heißt hier also: Dateien
   PHYSISCH aus `data/` entfernen (Archiv-Ordner, nicht löschen).
   - Raus: `selfplay_v1c_*`, `selfplay_s400_*` (alt, vor `v2`),
     `selfplay_v2s2_*` (Stufe-2-Bootstrapping, half v6 nicht, nicht Teil
     von Spur A), `selfplay_v2s2det_*` (Spur-B-Diagnosedaten).
   - `v2`-Pile (aktuell 1135 Dateien) auf ~800 Dateien (8000 Spiele)
     eindampfen — beliebige Teilmenge, da `v2` als Policy unveraendert ist,
     alle Spiele gleichwertig.
   - **Nutzer bereitet `data/` vor** (Stand: läuft).
   - Danach `ls data/*.pkl | wc -l` gegenchecken, BEVOR `train.py` läuft.
2. Training: `python train.py --name v7 --epochs 100 --load v2` (wie
   bisher, Warm-Start vom Champion) — **keine neuen Self-Play-Spiele, keine
   Sims-Änderung**, ausschließlich das kuratierte ~8000-Spiele-Fenster.
3. Gate: `run_net_vs_net(v7, v2, stage=1, games=100)` — SPRT-Entscheid.
4. **Trigger-Regel für danach:**
   - **v7 gewinnt** (H1a): v7 wird neuer Champion, Zyklus geht normal weiter.
   - **v7 "Gleich stark"**: zeigt, dass reine Fenster-Kontrolle (ohne
     Kontamination) allein nicht reicht — dann ernsthaft Kurswechsel
     erwägen (z.B. Cold-Start statt Warm-Start testen, um zu prüfen, ob der
     Warm-Start selbst der limitierende Faktor ist), bevor überhaupt an
     Sims gedacht wird.
   - **v7 verliert klar** (H1b): würde bedeuten, das ausgedünnte Fenster war
     zu klein/einseitig — Fenstergröße vorsichtig wieder anheben.

**Verworfene Idee: Sims auf 800-3200 erhöhen.** `dynamic_sims(base,
num_actions) = clamp(base + √actions·25, base, base·5)` addiert nur einen
von der Aktionszahl abhängigen Zuschlag zur `base` — sie skaliert NICHT
relativ zur Basis. Eine höhere `base` verteuert JEDEN Zug gleichermaßen
(nicht nur komplexe Situationen), und die ohnehin schon teuren frühen
Runden (mehr Optionen) würden zusätzlich noch den vollen höheren Sockel
obendrauf bekommen — überproportionale Laufzeit-Explosion ausgerechnet
dort, wo die Stufe-2-Untersuchung gar kein Problem gefunden hat (die
Schwäche zeigt sich eher bei bodenlastigen/späten Entscheidungen). Ohne
jede Evidenz, dass eine Sims-Erhöhung das eigentliche Plateau (vier
Kandidaten, vier verschiedene Fenster, immer "Gleich stark") überhaupt
adressiert, ist das kein guter erster Test — Fenster-Kontrolle isoliert zu
testen ist billiger und aussagekräftiger.

### Spur B: Stufe-2-Ursachenforschung — abgeschlossen (Mehrrunden-Hypothese widerlegt)

Deterministisches (`--deterministic --no-root-noise`) Stufe-2-Self-Play mit
`v2` (900 Spiele, `v2s2det`, siehe `evaluations/stage2_investigation.md`
Schritt 8/9) klärte die Symptomatik:

- [x] 0:0-Rate auf komplett rauschfreien Daten: **7.0%** — deckungsgleich
      mit den Arena-Ergebnissen (v6(Stufe2) vs. v2(Stufe2): 7.0%). Zweifach
      bestätigt (Arena + Argmax-Selfplay), kein Selfplay-Artefakt.
- [x] Value-Head-Vorhersagen über die Runden zeigen: der Value-Head erkennt
      0:0-bound Partien schon ab Runde 1, aber die Vorhersage eskaliert
      selbst im schlechtesten Fall nie ins klar Negative (bleibt bei
      0.04-0.11, während normale Partien auf 0.19→0.29 steigen) — bestätigt
      die "weiches/wenig trennscharfes Value-Signal"-Hypothese deutlich.

**Wichtige Korrektur des Gesamtbilds** (siehe
`evaluations/stage2_investigation.md`, Abschnitt oben): Stufe 2s eigentlicher
Zweck ist NICHT billigere Blattauswertung — direkt gemessen sind Stufe 1
und Stufe 2 praktisch gleich schnell (14.86s vs. 16.21s/Spiel, 10 Spiele
v2 vs. sich selbst). Der eigentliche Grund: `solve_round_final_score` löst
nur die AKTUELLE Runde exakt (null Sicht auf Runde 2-5), und die Suchbaeume
beider Stufen behandeln das Rundenende strukturell als "terminal" — die
Suche simuliert NIE über Rundengrenzen. Stufe 1 ist damit **strukturell
blind für rundenübergreifende Strategie**, unabhängig davon wie gut sie
wird. Der Value-Head (trainiert auf das tatsächliche 5-Runden-Endergebnis)
ist der einzige Baustein, der das prinzipiell könnte.

- [x] **Direkter Test durchgeführt** (`evaluations/stage2_investigation.md`
      Schritt 10, neue Rust-Funktion `stage_disagreement_study`): an jeder
      Drafting-Entscheidung eines Stufe-1-geführten Champion-Spiels (v2)
      geprüft, ob Stufe 2 argmax anders gewählt hätte; bei Abweichung
      verzweigt und beide Zweige per Rollout (Stufe-1-Fortsetzung) verglichen.
      597 Meinungsverschiedenheiten (60 Spiele, ~120/Runde):
      ```
      Runde 1: n=120  t=+0.11  (nicht signifikant)
      Runde 2: n=120  t=+0.23  (nicht signifikant)
      Runde 3: n=120  t=-4.37  (Stufe 1 signifikant besser)
      Runde 4: n=120  t=-1.42  (nicht signifikant, Trend Stufe 1)
      Runde 5: n=117  t=-2.46  (Stufe 1 signifikant besser — erwartbar: letzte
                                Runde, Stufe 1s DFS-Blatt ist dort exakt)
      ```
      **Ergebnis: Mehrrunden-Vorsicht-Hypothese widerlegt.** Gerade in Runde
      1-2, wo Weitblick am meisten zählen müsste, ist der Unterschied
      statistisch nicht von Null zu unterscheiden. In Runde 3 verliert
      Stufe 2s abweichende Wahl sogar signifikant — das Gegenteil der
      Hypothese. (Methodischer Vorbehalt: beide Zweige spielen nach der
      abweichenden Aktion mit Stufe-1-Politik weiter — testet also "hilft
      Stufe 2s Zug einmalig, wenn der Champion den Rest spielt", nicht
      "wäre eine durchgehende Stufe-2-Partie stärker"; Letzteres zeigt die
      Stufe1-vs-Stufe2-Arena ohnehin schon eindeutig, 73-93% Stufe-1-Siege.)

**Entscheidung:** Stufe 1 bleibt der Produktions-Pfad — nicht nur vorläufig
mangels Alternative, sondern weil die Mehrrunden-Foresight-Hypothese, die
Stufe 2s einzige denkbare Existenzberechtigung war, jetzt direkt getestet
und widerlegt ist. Die Value-Head-Beobachtungen aus Schritt 5-9 (weiches,
wenig trennscharfes Signal) erklären die Stufe-2-Schwäche vollständig; es
gibt kein verborgenes Mehrrunden-Können, das Stufe 1 fehlt. Spur B ist damit
inhaltlich abgeschlossen. Sollte künftig ein deutlich besser kalibrierter
Value-Head trainiert werden (Val-R² spürbar über 0.3-0.5), lohnt sich eine
Wiederholung dieses Tests — bis dahin kein weiterer Aufwand hier. Spur A
(Champion-Spielstärke) hat alleinige Priorität.

**Nachtrag (2026-07-15): Kapazitätstest durchgeführt, Ergebnis negativ.**
Nutzer-Anstoß: "dann müssen wir den Value-Head so modifizieren dass er
strategisch denkt, sonst hat das alles wenig Sinn." Neue `train.py`-Flags
`--value-hidden N` + `--skip-phase1` (erzwingt 0 Phase-1-Epochen: geladener
Trunk/Policy/Moon-Head bleiben exakt unverändert, nur Phase 2 läuft) erlauben
einen schnellen, günstigen Test ohne neues Self-Play: Value-Head von 64 auf
256 Hidden-Neuronen (4x) verbreitert, gegen denselben eingefrorenen
v7cold-Trunk neu kalibriert.

```
v7cold        (value_hidden= 64): Val-R²=0.273, bester Stand nach Epoche 1/50
v7cold_vh256  (value_hidden=256): Val-R²=0.272, bester Stand nach Epoche 1/50
```

Praktisch identisch — 4x mehr Kopf-Kapazität ändert NICHTS an der Decke, und
das Muster (bester Wert bereits nach Epoche 1, danach nur noch Verschlechterung)
bleibt exakt gleich. **Kopf-Kapazität ist damit als Ursache ausgeschlossen.**

**Zweiter Test (direkt im Anschluss, Nutzer-Anstoß "was müssen wir machen,
damit der Value-Head endlich greift"): Trunk-Hypothese direkt geprüft.**
Neuer `train.py`-Modus `--value-only` (Phase 1 trainiert den Trunk NUR mit
Value-Loss, kein Policy-/Moon-Loss fließt in den Trunk-Gradienten) — testet,
ob ein nicht vom (dominanten) Policy-Loss geformter Trunk eine höhere
Val-R²-Decke erreicht. Frischer Trunk, 60 Epochen, dasselbe Datenfenster:

```
Gemeinsam trainierter Trunk (v7cold, Policy+Value): Val-R²=0.27-0.34
Value-only-Trunk (kein Policy-Signal):              Val-R²=0.19 (Phase-1-Peak
                                                      bereits 0.25 in Epoche 1)
```

**Schlechter, nicht besser.** Auch die Trunk-Hypothese ist damit widerlegt —
den Trunk vom Policy-Signal zu befreien hilft dem Value-Fit nicht, es schadet
ihm sogar leicht (deckt sich mit der älteren Beobachtung "der Trunk profitiert
nachweislich vom Value-Signal, siehe v1 vs. v1b" — es scheint umgekehrt
genauso zu gelten: Policy hilft dem Trunk auch fürs Value-Fitting).

**Damit sind beide plausiblen Architektur-Fixes (Kopf-Kapazität, Trunk-
Dedikation) sauber ausgeschlossen.** Die verbleibende Erklärung ist
wahrscheinlicher: irreduzibles Rauschen im Trainings-Target selbst — der
finale Score hängt stark von künftigen Zufalls-Fliesenzügen ab, die zum
Entscheidungszeitpunkt prinzipiell unbekannt sind, und Val-R²≈0.2-0.3 könnte
schlicht nahe der Decke liegen, die die Zustandsfeatures + das Spielzufalls-
element überhaupt zulassen. Einzig verbleibender Hebel: das Trainings-TARGET
selbst weniger verrauscht machen (z.B. über mehrere Rollouts gemittelte
Werte statt des rohen Einzelspiel-Ergebnisses, analog zum `n_reps`-Ansatz aus
der Disagreement-Studie) — deutlich teurer, da es Self-Play-Rechenzeit
vervielfacht, und mit unsicherem Ertrag. Nächster Schritt nur auf explizite
Anfrage, da Spur A (Champion-Herausforderung) weiterhin alleinige Priorität hat.

<details>
<summary>Historie: erster Reset-Zyklus (v1/v1b/v2/v2b, überholt)</summary>

| Netz  | Fenster                              | Warm-Start | vs. Vorgänger      | vs. Heuristik | Val-R² |
| ----- | ------------------------------------- | ---------- | ------------------- | ------------- | ------ |
| v1    | 6000 Heuristik (VALUE_WEIGHT=15)      | nein       | —                    | 16:84         | —      |
| v1b   | 6000 Heuristik (VALUE_WEIGHT=2.5)     | nein       | —                    | 10:90         | —      |
| v2    | 4000 Heuristik + 6000×v1              | nein       | **63:37 vs. v1** ✅  | 31:69         | 0.16   |
| v2b   | 4000 Heuristik + 6000×v1              | ja (v1)    | 58:42 vs. v1 (Gate ✗)| —             | 0.41   |

Kernbefunde (aus dieser überholten Runde, aber weiterhin lehrreich):
- v2 schlug v1 63:37 (reißt das 60:40-Gate) — trotz massivem
  Train/Val-Overfitting (Train-R²=0.90, Val-R²=0.16). Mehr Daten halfen der
  reinen Spielstärke, auch wenn der Value-Head sie kaum generalisiert hat.
- v2b (Warm-Start) generalisierte deutlich besser (Val-R²=0.41), spielte aber
  SCHWÄCHER (58:42 statt 63:37) — Val-R² sagt nur etwas über den Value-Head
  aus, der in Stufe 1 beim Spielen gar nicht befragt wird. Was für
  Stufe-1-Stärke zählt, ist der Policy-Head, und der schien unter Warm-Start
  eher an v1s eigene (noch unausgereifte) Präferenzen anzuknüpfen, statt
  unabhängig auf dem größeren Fenster neu zu lernen.
- Stufe 2 weiterhin nicht praxistauglich — v2b hatte mit der ALTEN
  0:0-Raten-Sonde ein grünes 1.45x-Verhältnis (bester Wert der damaligen
  Historie), verlor aber 2:98 in einer echten Stufe-1-vs-Stufe-2-Partie. Die
  alte Sonde maß nur "kollabiert nicht mehr in Nichtangriffs-Partien", nicht
  "gewinnt wirklich" — seitdem durch einen direkten Arena-Test ersetzt (siehe
  Werkzeuge unten).

</details>

**Abgeschlossen (aktueller Reset-Zyklus):** VALUE_WEIGHT-Sweep (15/8/4/2) auf frischem 11.000-Spiele-
Heuristik-Fenster, je Arena vs. Heuristik (200 Sims, Early-Stop):

| Variante | vs. Heuristik   | Value Val-R² (Peak→nach Freeze) |
| -------- | --------------- | -------------------------------- |
| v1w15    | 29% (6:15, n=21)| 0.27 → -0.87                     |
| v1w8     | 10% (1:9, n=10) | 0.28 → -0.46                     |
| v1w4     | 31% (9:20, n=29)| 0.30 → -0.06                     |
| v1w2     | 10% (1:9, n=10) | 0.35 → +0.07                     |

Jedes einzelne Ergebnis ist für sich statistisch abgesichert (Early-Stop
garantiert ≥95%-Konfidenz, dass Heuristik pro Match >50% Gewinnchance hat).
Die RANGFOLGE zwischen den vier Gewichten ist damit aber nicht automatisch
mitgesichert: Zweistichproben-z-Test v1w4 (9/29=31%) vs. v1w8 (1/10=10%)
ergibt z≈1.31 — unter der 95%-Schwelle (z≥1.96), also (noch) nicht
signifikant unterscheidbar trotz des deutlich wirkenden Punkteabstands.
v1w15 (6/21=29%) vs. v1w4 (9/29=31%) sind ohnehin praktisch identisch. Sweep
zeigt also verlässlich "alle vier Gewichte verlieren gegen Heuristik", aber
NICHT verlässlich, welches der vier Gewichte am besten ist — dafür bräuchte
es größere Stichproben pro Variante oder direkte Kandidat-vs-Kandidat-Arenen.
Wichtigster Nebenbefund: **in ALLEN vier Varianten kollabiert der (per
chirurgischem Freeze fixierte) Value-Head trotzdem** (siehe Tabelle) — der
Freeze schützt nur die Head-Gewichte selbst, nicht vor dem weiterhin
driftenden gemeinsamen Trunk, der nach dem Freeze noch dutzende Epochen rein
auf Policy trainiert. **Fix:** Zwei-Phasen-Training ersetzt den Freeze (siehe
Werkzeuge unten) — Sweep-Wiederholung mit dem neuen Mechanismus steht noch
aus, `VALUE_WEIGHT` in `config.py` bleibt bis dahin unentschieden.

**Abgeschlossen:** Confounder-Check zum Sweep-Befund "v1 (Weight 15) schlägt
v1b (Weight 2.5)": weil das Stop-Kriterium erst greift, wenn Policy UND Value
plateauen, trainiert ein hoher VALUE_WEIGHT-Lauf schlicht länger (Value
plateaut später als Policy) — der scheinbare Vorteil könnte reine
Trainingsdauer sein, nicht der Value-Gradient selbst. Test: zwei epochen-
gematchte Läufe auf demselben Fenster, je exakt 50 Epochen
(`--epochs 50 --no-early-stop`), `v1b_w15_e50` (VALUE_WEIGHT=15) vs.
`v1b_w0_e50` (VALUE_WEIGHT=0, reines Policy-Training) — Details in
`evaluations/v1b_w15_e50_eval.md` / `v1b_w0_e50_eval.md`.

Ergebnisse:
- **Stufe 1 (A vs. B, 100 Spiele, kein Early-Stop): exaktes 50:50.** Kein
  messbarer Vorteil von VALUE_WEIGHT=15 gegenüber 0 bei gleicher
  Trainingsdauer — der frühere Sweep-Befund war der Confounder, nicht der
  Value-Gradient.
- Selbst der Value-Head-Kalibrierungswert (Phase 2, gegen den jeweils fixen
  Trunk) ist fast identisch: 0.24 (w15) vs. 0.22 (w0) — der rein
  policy-trainierte Trunk liefert also fast gleich gute Repräsentationen für
  die Value-Vorhersage.
- **Stufe 2 (A vs. B, 100 Spiele, kein Early-Stop): 40:60 — w0 gewinnt sogar
  leicht** (z≈2.0, knapp signifikant), trotz des minimal schlechteren
  Kalibrierungswerts. VALUE_WEIGHT ist also auch für Stufe 2 kein Hebel; wenn
  überhaupt, ist "kein Value-Gradient in Phase 1" leicht im Vorteil. 0:0-Rate
  bei Stufe 2 mit 7% weiterhin auffällig höher als bei Stufe 1 (0%) — Stufe 2
  bleibt insgesamt die schwächere Spielweise, unabhängig vom Gewicht.

**Entscheidung:** `VALUE_WEIGHT` in `config.py` auf **1** gesetzt (statt dem
zufällig gewählten alten Standard 15) — der Sweep mit dem korrigierten
Zwei-Phasen-Training (der wegen eines Skript-Bugs nur mit 15 statt ~100
Epochen lief, siehe Git-Historie) wird NICHT wiederholt, da der Confounder-
Test die eigentliche Frage bereits klar beantwortet hat: das Gewicht ist für
Stufe 1 und Stufe 2 gleichermaßen irrelevant. Nächste Generationen laufen mit
diesem Wert.

## Werkzeug-Verbesserungen dieser Session

- **Val-Split** (`train.py --val-frac`, Standard 10%, Datei- nicht
  Zug-Ebene): deckt Overfitting auf, das Train-R² allein verdeckt hätte
  (siehe v2 oben). Pro Trainingslauf neu gezogen, kein generationsübergreifend
  fixer Val-Satz (das leistet die Arena vs. Champion/Heuristik).
- **Zwei-Phasen-Training** (ersetzt das frühere chirurgische Value-Head-
  Freeze, das den Val-R²-Kollaps im Sweep NICHT verhindert hat — der Trunk
  driftete nach dem Freeze unter dem fixen Head weiter weg): Phase 1
  trainiert Value+Policy bis zum bestehenden Policy+Value-Plateau komplett
  gemeinsam (voller `VALUE_WEIGHT`, kein Freeze mehr — der Trunk profitiert
  nachweislich vom Value-Signal, siehe v1 vs. v1b). Danach Phase 2:
  Trunk/Policy/Moon-Head einfrieren, Value-Head NEU initialisieren und
  ausschließlich gegen den jetzt fixen Trunk kalibrieren (bis zu 50 Epochen,
  `--val-patience`-Patience als Stop). Kann nicht mehr kollabieren, weil sich
  der Trunk während der Kalibrierung nicht mehr bewegt.
- **Policy-Val-Loss** (`train.py`, `val_ploss_history`): zusätzlich zum
  Value-Val-R² jetzt auch Policy-Verlust auf dem nie trainierten Val-Split
  gemessen (gleiche Masking/Gewichtung wie Training) — bislang nur ein
  Nice-to-have-Signal, die Arena bleibt der eigentliche Entscheider.
- ~~`value_hidden` 128→64: die Value-Regression ist eigentlich einfach,
  weniger Kapazität dürfte dem Overfitting zusätzlich entgegenwirken.~~
  **Widerlegt** (siehe Test unten, 2026-07-15): 64→256 (4x) auf demselben
  eingefrorenen Trunk ändert die Val-R²-Decke praktisch nicht (0.273→0.272).
  Kopf-Kapazität war nicht die Ursache.
- **Direkter Stufe-1-vs-Stufe-2-Arena-Test** (`train.py::run_readiness_probe`)
  ersetzt die alte 0:0-Raten-Sonde: dasselbe Netz tritt in einer echten Partie
  gegen sich selbst an (Stufe 1 vs. Stufe 2), max. 50 Spiele, mit Early-Stop.
- **Arena-Early-Stop → truncated SPRT** (`arena.py::sprt_bounds`/
  `sprt_llr_delta`, ersetzt die fruehere Bonferroni-korrigierte
  Wiederholungstest-Loesung): zwei parallele Wald-SPRTs pro Match — H1a
  "A signifikant staerker", H1b "B signifikant staerker", je p1=0.64
  (~+100 Elo), α=0.05, β=0.10. Bricht ab, sobald EINE Seite ihre H1
  annimmt (Sieger); "Gleich stark" gilt erst, wenn BEIDE H1 verwerfen oder
  das Ressourcenlimit (Standard 100 Spiele) erreicht ist. Ein einseitiger
  Test haette knapp-eindeutige Ergebnisse faelschlich als Paritaet gemeldet
  (siehe v1c-Log, Git-Historie) — der Dual-Test behebt das. Elo-Berechnung
  ist jetzt rein sieg-/niederlage-basiert (kein Siegstaerke-Multiplikator
  mehr), korreliert direkt mit der SPRT-Gewinnwahrscheinlichkeit.
- **`net_vs_net_arena_match`**: `dfs_leaf_a`/`dfs_leaf_b` getrennt wählbar
  (z.B. Stufe 1 vs. Stufe 2 in derselben Partie, nicht nur global pro Match).
- **Self-Play-Diagnose-Flags** (`self_play.py --no-root-noise`,
  `--deterministic`, siehe `evaluations/stage2_investigation.md`): erlauben
  rauschfreies (`--deterministic`, immer meistbesuchter Zug statt
  visit-proportionalem Sampling) bzw. teilrauschfreies (`--no-root-noise`)
  Self-Play mit vollen Zug-fuer-Zug-Trajektorien fuer Diagnosezwecke — NICHT
  fuer reguläre Trainingsdaten-Generierung (weniger Zustandsvielfalt).
- **`mcts.rs`/`net_mcts.rs`**: strukturell identische Teile (Force-Reply-
  Garantie, Nachlauf-Schließung, Tiefenberechnung) in `search_common.rs`
  zusammengefasst — die tatsächlich unterschiedlichen Algorithmen (UCB1+
  Widening vs. PUCT+Policy-Masse-Cutoff) bleiben bewusst getrennt.

## Champion/Kandidat-Protokoll

- **Gate:** ein Kandidat wird nur Champion, wenn er den bisherigen Champion in
  der SPRT-Arena (siehe Werkzeuge oben) signifikant schlägt (H1a angenommen,
  ~+100 Elo / 64% Gewinnwahrscheinlichkeit). "Gleich stark" (SPRT-Ausgang
  PARITY) heißt: Champion bleibt bestehen, Kandidat wird verworfen.
- **Self-Play kommt immer vom aktuellen Champion**, nie vom zuletzt trainierten
  Netz.
- **Fenster-Größe — Soll vs. Ist:** urspruenglich gedacht als max. 2 abgelöste
  Champions (je 1 Runde à 2000 Spiele = 4000) + aktueller Champion (6000) =
  **10.000 Spiele**. **Tatsächlich ist das Fenster über v3→v6 unbemerkt auf
  ~17.000 Spiele gewachsen** (v6 lud 1735 Dateien) — teils weil die billigste
  Eskalationsstufe ("+2000 Spiele") mehrfach gezogen wurde, teils weil
  `train.py` grundsätzlich ALLE `.pkl`-Dateien aus `data/` laedt
  (`glob.glob(*.pkl)`, keine Versions-Filterung) und der `v2`-Self-Play-Anteil
  dadurch unbemerkt auf 1135 Dateien (~11.350 Spiele statt der dokumentierten
  600/6000) angewachsen ist. **Konsequenz: "Fenster" ist aktuell gleichbedeutend
  mit "was gerade in `data/` liegt"** — vor JEDEM Training muss der Ordner
  bewusst kontrolliert werden, sonst driftet die tatsaechliche Trainingsmenge
  unbemerkt von der Dokumentation weg (wie hier geschehen). Ab v7 gilt zudem:
  **Eskalationsstufe 1 gilt als ausgereizt** (siehe Masterplan unten) — nicht
  mehr automatisch ziehen, stattdessen zu Stufe 2/3 wechseln.
- **Eskalationsstufen bei erfolglosem Kandidaten, ab jetzt in dieser
  Reihenfolge (Stufe 1 gilt als verbraucht):**
  1. ~~+2000 Spiele~~ — **4x versucht (v3-v6), 4x erfolglos. Nicht mehr
     wiederholen, bevor nicht Stufe 2 probiert wurde.**
  2. **Fenster kuratieren** (v7, laufend): alte, vorreset-fremde Spiele
     sowie die Stufe-2-Bootstrapping-Beimischung rauswerfen, nur noch
     kuratierte `v2`-Champion-Qualität behalten (~8000 Spiele) — kein neues
     Self-Play nötig, genug liegt bereits vor.
  3. **Sims erhöhen — zurückgestellt, keine Evidenz dafür**: `dynamic_sims`
     skaliert nicht relativ zur Basis (siehe Masterplan Spur A, "Verworfene
     Idee") — eine höhere Basis würde JEDEN Zug (nicht nur komplexe
     Situationen) verteuern und die ohnehin teuren frühen Runden
     überproportional treffen, ohne dass wir Evidenz haben, dass das
     eigentliche Plateau (v3-v6 alle "Gleich stark") daran liegt. Nur
     erwägen, falls Stufe 2 (kuratiertes Fenster) ebenfalls scheitert, UND
     dann mit klarer Kosten-Nutzen-Abwägung, nicht blind.

## Value-Target-Formel (`engine/py/neural_net.py`, `VALUE_SCHEMA_VERSION=9`)

```
own_total = step["scores"][eigener Spieler]   # inkl. Wertungsplatten
opp_total = step["scores"][Gegner]
value = tanh(own_total / 50) − 0.1 · tanh(opp_total / 50)
```

Ziel für JEDEN Schritt der Partie (delayed reward, wie in AlphaZero) — nicht
Win/Loss ±1, sondern das tatsächliche Punkte-Endergebnis. Getrennt gesättigte
Terme: der eigene Term ist unabhängig vom Gegner voll differenzierend
(Priorität 1 "maximale eigene Punktzahl"), der Gegner-Term ist separat
gesättigt und verschiebt den Gesamtwert nur um max. ±0.1 (Priorität 2 "wenn
möglich dem Gegner schaden", begrenzter Bonus, kann nie eine eigene Einbuße
aufwiegen).

`VALUE_WEIGHT` balanciert Value- gegen Policy-Loss — der ursprüngliche Sweep
(15/8/4/2) war durch den alten Freeze-Mechanismus verfälscht; der Confounder-
Test (siehe oben, epochengematcht mit Zwei-Phasen-Training) zeigt aber klar,
dass das Gewicht weder für Stufe 1 (50:50) noch für Stufe 2 (40:60, tendenziell
sogar zugunsten Weight=0) einen Unterschied macht. Final auf **1** gesetzt,
kein weiterer Sweep nötig.

## Bekannte Bugs (in früheren Zyklen gefunden und gefixt, Referenz)

- Self-Play-Timeout: fix (30s) auf reine Heuristik-Suche kalibriert, riss bei
  höheren Sims/netzgeführter Suche → jetzt dynamisch sims-skaliert
  (`heuristic_game_timeout_secs`/`net_game_timeout_secs` in `self_play.rs`).
- BatchNorm-Crash bei Batch-Größe 1 (Restbatch einer Epoche) → `drop_last=True`.
- Tiling-Solver-Kombinatorik-Explosion (`chip_allocations`) → Node-Budget +
  Bitmasken-Signatur statt String-Dedup.
- Wertungsplatten-Blindheit + Unplaceable-Row-Blindheit in der Blattbewertung
  (`solve_round_final_score` kannte weder Wertungsplatten-Fortschritt noch
  drohende Strafleisten-Buße) → `scoring::wertung_progress` +
  `round_end::projected_unplaceable_penalty`, beide in `player_total`
  eingerechnet. Bestätigt wirksam: Anteil "konfident falscher"
  Strafleisten-Entscheidungen der Heuristik 75.9%→15.1%.
- JSON-Umweg im Netz-Feature-Pfad (`state_to_json` statt direktem Struct-Zugriff)
  kostete ~34% der Suchzeit → `state_to_features_direct`, −35 bis −48%
  Gesamt-Suchzeit.
- Force-Reply griff nicht zuverlässig (nur bei erneutem PUCT/UCB-Besuch) →
  Nachlauf-Pass am Ende von `build_tree`/`build_net_tree`.

## Offene Punkte

- **v7 (Spur A des Masterplans):** `data/` kuratiert (880 Dateien, nur `v2`,
  ~8800 Spiele). Läuft: `v7` (Warm-Start `--load v2`) UND `v7cold`
  (Cold-Start, gleiches Fenster, kein `--load`) PARALLEL — testet zusätzlich
  zur Fenster-Kontrolle, ob Warm-Start selbst der limitierende Faktor beim
  Plateau ist. Danach Gates: `v7` vs. `v2`, `v7cold` vs. `v2`, ggf. `v7` vs.
  `v7cold` direkt.
- **Stufe-2-Ursachenforschung (Spur B) inhaltlich abgeschlossen** (siehe
  `evaluations/stage2_investigation.md`): 0:0-Rate ist ein Score-Klemm-
  Mechanik-Effekt; Stufe 2 hat real ~7% davon (rauschfrei, zweifach
  bestätigt über Arena UND Argmax-Selfplay) vs. 0% bei Stufe 1; Ursache ist
  das weichere/weniger trennscharfe Value-Signal (Value-Head erkennt
  0:0-bound Partien früh, eskaliert aber nie ins klar Negative). Stufe 1
  bleibt Produktions-Pfad, gezielte Stufe-2-Kalibrierung zurückgestellt.
- Learning Rate kann noch optimiert werden.
- Ob ein Policy-Prior-Bias wie beim alten v8 (konfidente Fehlentscheidungen
  "Strafleiste statt erreichbare Reihe") in der neuen Linie auftritt, ist
  noch nicht systematisch untersucht.
