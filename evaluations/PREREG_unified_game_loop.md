# PREREG: Vereinheitlichte Spielschleife (Architektur-Fahrplan Punkte 1+2)

Stand 2026-08-14, PLAN (Nutzer-Auftrag: *"dann räum die vier spielschleifen
auf solang die generierung noch nicht läuft"*). Durchgehend Plan-Zeitform.
Die Generierung des Ownership-Korpus (PREREG_ownership_corpus.md) wartet
auf diese Abnahme — ein Refactor während der Generierung würde den Korpus
über zwei Code-Stände verschmieren.

## §1 Geprüfter Ist-Stand: vier Pfade, dieselbe Schleife viermal

| Pfad | Stelle | Rolle |
|---|---|---|
| `play_one_game` | self_play.rs (11 Parameter seit RNG-Schnitt) | Heuristik-Self-Play / Probe |
| `play_net_game` | self_play.rs:1572-1863 | Arena Netz-gegen-Heuristik |
| `play_net_vs_net_game` | self_play.rs:1863-2277 | Hybrid-Arena |
| `play_net_self_play_game` | self_play.rs:2567-2941 | PRODUKTION (run_net_self_play) |

Die motivierende Fehlerklasse ist AKTENKUNDIG (PREREG_ownership_corpus.md
§3.1/§3.2): der Bauer-Vorzug war in zwei Pfaden verdrahtet (einmal einseitig,
einmal beidseitig) und im Produktionspfad GAR NICHT — ein stiller
Wirkungslos-Start der Korpus-Arme B/C/E/F wäre die Folge gewesen. Divergenz
zwischen Kopien derselben Schleife ist kein Einzelfall, sondern die
Grundeigenschaft von Kopien.

## §2 Zielbild

EINE parametrisierte Schleife + Spieler-Abstraktion (Fahrplan Punkt 2):
Zugquelle je Spieler (Heuristik-MCTS / Netz-Suche / Netz-Suche+Vorzug) als
Trait-Objekt, Aufzeichnungs-/Label-Pfade als Konfiguration, nicht als Kopie.
Die vier öffentlichen Einstiege bleiben als dünne Wrapper erhalten
(API-Kompatibilität zu py.rs/lib.rs und allen Tools).

## §3 Abnahme (vorab festgelegt, hart)

1. **Golden-Records ZUERST**: VOR jeder Code-Änderung je Pfad N=8 feste
   Seeds spielen und die vollständigen Records (Spielverlauf UND
   Trainingsziel-Felder) archivieren. Nach dem Refactor identische Seeds:
   **bit-identisch, 0 Abweichungen** (Gate-B-Methodik; seit dem RNG-Schnitt
   möglich). Ein Refactor, der ein Bit im Spielverlauf ändert, ist keiner.
2. Paritäts-Hash unverändert (Heuristik-Anker `player_total`/
   `wertung_progress` bleiben unberührt).
3. cargo test --lib grün, Wheel neu gebaut+installiert, Paritätsprobe auf
   dem installierten Wheel.
4. Verhaltens-Knöpfe: alle Diagnose-Knöpfe (MOSAIC_SPALTENBAU,
   MOSAIC_PLATTENBAU, Streuung) wirken nach dem Refactor in ALLEN Pfaden
   gleich dokumentiert — die Seitigkeit (einseitig im Arena-Pfad
   Netz-gegen-Heuristik, beidseitig sonst) wird als explizite Konfiguration
   getragen, nicht als Pfad-Zufall.

## §4 Außerhalb des Zuschnitts

- Der Async-Zwilling in wt_async2 (Messstand Stufe 3) — bleibt unangetastet;
  bei späterer Übernahme muss er auf die vereinheitlichte Schleife rebasen
  (Schnittstellen-Hinweis, kein Arbeitspaket hier).
- Baustein 2b (deterministische Labels) ist eine EIGENE Entscheidungseinheit:
  PREREG_deterministic_labels.md — läuft NACH dieser Abnahme, vor der
  Generierung.

## §5 Abnahme-Protokoll (ERGEBNIS, 2026-08-14)

### §5.1 Aufbau

Harness: `engine/examples/golden_game_loop_capture.rs` (Commit 7512412),
spielt über die ÖFFENTLICHEN `run_*`-Einstiege (damit sind die dünnen
Wrapper mitgeprüft). Seed 20260814, N=8 Partien je Pfad, `num_threads=1`,
Modell `alphazero_v21_2d_brierbest.onnx`. Konfigurationen:

| Kürzel | Einstieg | Konfiguration |
|---|---|---|
| p1 | `run_self_play` (play_one_game pur) | sims=32, c=SELF_PLAY_C |
| p1n | `run_self_play_with_net_labels` | sims=32, rtv=an |
| p2 | `run_net_arena_match` (play_net_game) | 24/24 sims, log_games=true |
| p3 | `run_net_vs_net_arena` (play_net_vs_net_game) | 24/24, log_games=true |
| p4 | `run_net_self_play` (play_net_self_play_game) | 60 sims, noise=an, rtv=an, PCR=aus |

Knopf-Läufe (p2/p3/p4, rtv=aus, je EIGENER Prozess wegen OnceLock-Env-
Cache): `MOSAIC_SPALTENBAU=1` bzw. `MOSAIC_PLATTENBAU=5`.

### §5.2 Basislinien-Stabilität (Doppellauf VOR dem Refactor)

- A vs. A2: p1/p1n/p2/p3 **byte-identisch**; p4: 30/1308 Records
  abweichend, ALLE ausschließlich im Feld `round_transition_value`
  (0/1308 ohne dieses Feld) — die bekannte Wall-Clock-Komponente
  (Task #71, Gate-B-Präzedenz im `sync_only_repeatability`-Test).
- SB vs. SB2 und PB vs. PB2: alle byte-identisch (rtv dort aus;
  `bootstrap_value` ist auf dieser Maschine stabil).
- Daraus abgeleiteter p4-Maßstab: 0 Bit in ALLEN Feldern außer
  `round_transition_value`; rtv wird gegen die Basislinien-Instabilität
  bewertet.
- Zwischenbefund zu Commit 1b61f9c (Streuungs-Leck-Fix, anderer Agent,
  landete zwischen Basislinien-Capture und Refactor): bei Streuung-aus
  empirisch No-Op — der Replay nach Schritt 1 reproduzierte p1n/p4
  (inkl. aller Label-Felder außer der bekannten rtv-Instabilität)
  byte-identisch über den Commit hinweg.

### §5.3 Golden-Replay-Ergebnisse (0/8-Zählung je Pfad)

Nach Schritt 1 (nur play_net_game umgestellt): p1, p1n, p2, p3 byte-
identisch; p2-Knopfläufe byte-identisch; p4 nur-rtv (Basislinie).

Nach Schritt 4 (ALLE vier Pfade umgestellt), Replay vs. Golden-A:

| Lauf | Ergebnis |
|---|---|
| p1 | **byte-identisch** (19 244 303 Bytes) — 0/8 Partien abweichend |
| p1n | **byte-identisch** (19 445 483 Bytes) — 0/8 |
| p2 | **byte-identisch** (150 591 Bytes, inkl. Volllog) — 0/8 |
| p3 | **byte-identisch** (156 536 Bytes, inkl. Volllog) — 0/8 |
| p4 | 1308/1308 Records; 30 abweichend, ALLE nur `round_transition_value`; **0/1308 im Spielgeschehen + bootstrap_value + Policy-Targets** — exakt die §5.2-Basislinien-Instabilität |
| p2/p3/p4 mit MOSAIC_SPALTENBAU=1 | **alle byte-identisch** |
| p2/p3/p4 mit MOSAIC_PLATTENBAU=5 | **alle byte-identisch** |

### §5.4 Tests / Wheel / Parität

- `cargo test --lib` nach JEDEM Schritt: 418 passed / 0 failed /
  20 ignored; nach Schritt 4 warnungsfrei.
- Wheel neu gebaut (`maturin build --release`) und installiert
  (`pip install --force-reinstall --no-deps`).
- `tools/parity_probe.py` auf dem installierten Wheel:
  `PARITAETS-HASH: 8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`
  — „OK -- Defaults sind byte-identisch zum Bestand."

### §5.5 Gebaute Struktur

`self_play.rs::unified_game_loop` + `DraftingAgent`-Trait mit vier
Implementierungen (`HeuristicSelfPlayAgent`, `HeuristicArenaAgent`,
`NetArenaAgent{vorzug}`, `NetSelfPlayAgent{vorzug}`) und
`GameLoopConfig { timeout_secs, seed_from_steps, game_seed,
move_heartbeat, labels: Option<LabelSamplingConfig{net, record_rtv,
profiled}>, mode: Records|Summary, players: [PlayerLoopConfig{agent,
tiling_net, apply_via_chosen_action, column_build_trace}; 2] }`.

- Seitigkeit des Vorzugs = explizites `vorzug`-Feld der Netz-Agenten
  (§3.4 erfüllt): `play_net_game` nur Netz-Seite (einseitig),
  `play_net_vs_net_game`/`play_net_self_play_game` beidseitig.
- Die historisch unterschiedlichen Such-Seed-Zähler (Arena: Alle-
  Schritte-Zähler; Self-Play: 1-basierter Drafting-Zähler) sind als
  `seed_from_steps` explizit konfiguriert.
- Alle vier öffentlichen Einstiege bestehen als dünne Wrapper mit
  UNVERÄNDERTER Signatur; `drafting_step` (einziger Aufrufer war
  play_one_game) ist in Agent+Schleife aufgegangen.
- Commits: 7512412 (Harness), 307caa4 (Schritt 1), 96e7a9a (Schritt 2),
  a9450b1 (Schritt 3), c14068f (Schritt 4).
