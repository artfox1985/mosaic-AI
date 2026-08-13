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
