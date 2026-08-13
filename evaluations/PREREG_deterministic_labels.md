# PREREG: Deterministische Trainingslabels (Task-#71-Not-Deckel, "Baustein 2b")

Stand 2026-08-14, PLAN (Nutzer-Go: *"go, häng es als 2b an"*). Läuft NACH der
Schleifen-Vereinheitlichung (PREREG_unified_game_loop.md) und VOR der
Korpus-Generierung (PREREG_ownership_corpus.md). Durchgehend Plan-Zeitform.

## §1 Geprüfter Ist-Stand

- Task #71 hat die PRIMÄREN Abbruchkriterien der Rundenübergangs-Bewertung
  bereits deterministisch gemacht (`POLICY_NODE_BUDGET` als "PRIMÄRER
  Cutoff", round_transition_deep.rs:188).
- Wall-Clock-Deadlines existieren aber weiter als "Not-Deckel" auf JEDER
  Ebene (`overall_deadline`/`heuristic_deadline`/Sample-Deadlines,
  round_transition_deep.rs:412-:597) — und wenn einer feuert, ist das dem
  Label NICHT anzusehen: ein gekapptes `bootstrap_value`/
  `round_transition_value` sieht aus wie ein volles.
- Beleg der Wirkung: Gate B (PREREG_async_search.md) fand Spielverlauf
  bit-identisch, aber Trainingsziel-Felder sync↔async divergent — die Deckel
  binden je nach Ausführungsgeschwindigkeit. Dieselbe Mechanik macht
  Produktions-Labels von der MASCHINENLAST abhängig.

## §2 Stufen (vorab festgelegt)

**Stufe 1 — Feuerraten-Messung (Diagnose, kein Verhaltenseingriff):**
Zähler je Not-Deckel-Stelle (Diagnose-Ausgabe analog batcher_diagnostics),
~50-Partien-Probe über run_net_self_play unter normaler Last. Bericht:
Feuerrate je Stelle. Deutung vorab: Rate ≈ 0 → Makel im Sync-Normalbetrieb
theoretisch (dann wirkt Stufe 2 nur als Versicherung); Rate > 0 → Anteil
heute betroffener Labels ist beziffert.

**Stufe 2 — Ehrliche Deckel:**
1. Not-Deckel feuert ⇒ betroffenes Trainingsziel-Feld bekommt den
   DETERMINISTISCHEN Fallback (reiner Spielausgang statt lastabhängigem
   Teilergebnis) — Labels sind dann entweder voll deterministisch oder
   ehrlich-konservativ, nie heimlich maschinenabhängig. BEWUSST ohne neues
   Record-Feld: ein Schema-Bump würde den gemeinsamen HDF5-Cache
   invalidieren (Kostenpunkt aus der Plattenkopf-Planung).
2. Not-Deckel auf Ausnahme-Niveau heben (~10× heutige Kalibrierung) — als
   reine Hänger-Versicherung; der äußere Watchdog existiert zusätzlich.

## §3 Abnahme

1. Unbelastete Maschine: Golden-Labels VOR/NACH der Änderung identisch auf
   festen Seeds (die deterministischen Budgets binden zuerst, kein Deckel
   feuert ⇒ nichts darf sich ändern).
2. Unter Last (künstliche CPU-Last oder Async-Pfad): Labels jetzt identisch
   zum unbelasteten Lauf ODER nachweislich auf Fallback gesetzt — nie ein
   drittes, lastabhängiges Ergebnis.
3. Paritäts-Hash, cargo test, Wheel-Neubau wie immer.
4. Gate-B-Retest der Trainingsziel-Felder (sync↔async) als Abschluss: die
   §-Divergenz aus PREREG_async_search.md muss damit verschwinden oder
   vollständig als Fallback-Fälle erklärbar sein.
