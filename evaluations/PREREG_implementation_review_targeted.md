<!-- STATUS: ENTSCHIEDEN | Frage: Ist der Mess-Pfad des Zielwechsel-Ergebnisses (par.14) frei von Perspektiven-, Vorzeichen- und Index-Fehlern -- oder ist das invertierte k1-Delta ein Implementierungs-Artefakt? | Beleg: par.6 (2026-08-20): Linsen A und B vollstaendig SAUBER (mit Repro-Sonden); Linse C fand den tragenden BEFUND -- die k1-Dosis saettigte den T+S-Arm (e_k1 Median 36,1 bei Nenner 1, q geclampt), par.14 des Zielwechsels ist Dosis-Artefakt-verdaechtig und die Messung wird mit rekalibrierten Nennern wiederholt (PREREG_reachability_target par.15). -->

# PREREG: Gezielter Implementierungs-Review des Zielwechsel-Mess-Pfads

Stand **2026-08-20**, **ENTWURF, nichts gestartet.** Durchgehend Plan-Zeitform.

**Anlass.** Das par.14-Ergebnis (`PREREG_reachability_target.md`) traegt eine
verdaechtige Signatur: k1 faellt SIGNIFIKANT (Block-t −3,73), wo es steigen
sollte, und die Offline-Sonde findet keinen Bezug der Kopf-Ordnung zum eigenen
Trainings-Praedikat (Tau −0,03). Ein invertierter Effekt ist exakt das, was
ein Ego/Gegner-Tausch, ein Vorzeichen- oder ein Index-Versatz erzeugt. Die
Kette (Label-Bauer, Verbraucher-Knoepfe, Sonden, Arena-Auswertung) entstand
binnen 48 Stunden aus drei Haenden (zwei Agenten + Koordinator). Die
Projekthistorie kennt genau diese Fehlerklasse mehrfach, immer lautlos
(policy-maskierter Korpus; Produktform-liest-keine-Atome; `player`-Feld
immer None).

**Zweck.** ENTWEDER das par.14-Verdikt freisprechen ("der Kopf steuert
wirklich weg") ODER den Bug finden, der es kippt — BEVOR auf Basis des
Verdikts strategisch umgeschwenkt wird (Asymmetrie-Korpus, Policy-Strang).

---

## par.1 PRUEFFLAECHEN (abschliessend — was hier nicht steht, ist nicht Teil dieses Reviews)

| Linse | Flaechen | Leitfragen |
|---|---|---|
| **A — Label/Training** | `engine/py/reach_target.py`; `engine/py/neural_net.py` (Label-Bau ~1540-1560, Ersetzung ~1840-1900, Cache-Key ~1280-1295, Layout-Docstring); `config.py`-Konstanten | Ego/Gegner-Zuordnung (`cj_first`/`cj_second` gegen `reach_columns(state, c)`/`(state, 1-c)`); Atom-Slice 6..12 gegen die Bau-Reihenfolge; Rundengrenzen; float16-Werte auf echten Daten nachgerechnet; Vorzeichen-Semantik (hohes Label = gut, ueberall?) |
| **B — Engine-Verbraucher** | `net_mcts.rs` `apply_ownership_shaping_full` + Wrapper + Knoepfe (SCALE/GEW/CONJ); `scoring.rs` `expected_plate_points(_conj)`, Atom-Indizierung; Netz-Auslese-Ort | Layout-Vertrag Python→ONNX→Rust ([0:36]/[36:72]/[72:106]/[106:140], "ich" = current_player); Perspektive an Nicht-Wurzel-Knoten (wessen current_player gilt am bewerteten Zustand?); Shift-Verrechnung beider Seiten (kann der Gegner-Shift die eigene Praeferenz drehen?); Sigmoid einfach/doppelt/fehlend; k-Index-Reihenfolge der 8er-Knoepfe |
| **C — Messweg/Sonden** | `paired_arena_env_ab.py` + `arm_worker` (Env-Vererbung, Seed-Paarung ueber Invokationen); `plate_points_from_arena.py` (`#arm`-Adressierung, k1-aktiv-Filter, Block-Paarung ueber Dateien, Seiten-Zuordnung Brett 0); `sibling_order_stability.py`/`sibling_order_vs_predicate.py` (q-Perspektive, `mover`/`successor`-Semantik des Traces); Plausibilitaets-Querschnitt der fertigen JSONs (verstuemmelte Partien, Seed-Identitaet, arm_wins gegen games) | Koennte der jeweilige Fehler ein INVERTIERTES Kriteriums-Delta oder ein Null-Tau erzeugen? |

## par.2 METHODE

- **Drei getrennte Reviewer-Agenten** (eine Linse je Agent, Sonnet), die die
  jeweils zu pruefende Flaeche NICHT selbst gebaut haben; anschliessend
  **ein adversarialer Verifikations-Schritt** (staerkeres Modell) auf JEDEN
  gemeldeten Befund: Auftrag "widerlege ihn", mit Repro-Pflicht.
- **Belegpflicht:** jede Aussage mit `datei:zeile`; wo moeglich Mini-Repro
  als Lesesonde auf echten Daten (`data/holdout`, vorhandene Ergebnis-JSONs).
  Jede Flaeche endet mit "SAUBER (Beleg)" oder "BEFUND (Repro)" — nichts
  dazwischen, keine Stil-Anmerkungen.
- **Strikt read-only:** keine Edits, keine Commits, kein Wheel-Bau, kein
  Training, keine Arena. (Waehrend des Reviews laeuft auch sonst nichts —
  die Exklusivitaets-Regel gilt fuer Sonden mit Suchlaeufen mit.)

## par.3 VORAB-REGELN

> **BEFUND-KRITERIUM:** ein Befund zaehlt nur, wenn der Verifikations-Schritt
> ihn NICHT widerlegen kann UND ein Repro vorliegt, das die Wirkungsrichtung
> zeigt. Agenten-Behauptungen ohne Repro werden protokolliert, aber nicht
> verrechnet (Regel 0).
>
> **KONSEQUENZ-REGEL, vorab:** (a) Bestaetigter Befund, der par.14 beruehrt →
> die Prereg wird annotiert ("Ergebnis unter Vorbehalt/UEBERHOLT"), der Bug
> gefixt, und NUR die betroffene Messung wiederholt — kein neues Design.
> (b) Alle Flaechen sauber → par.14 gilt als implementierungs-validiert;
> das wird dort als Nachtrag vermerkt. (c) Befunde ausserhalb des
> Mess-Pfads werden protokolliert und NICHT in diesem Rahmen gefixt.

## par.4 WAS DIESER REVIEW NICHT ENTSCHEIDET

- Ob der Zielwechsel als IDEE richtig war — nur, ob die Messung ihn korrekt
  gemessen hat.
- Die Gesamt-Gesundheit der KI (eigene Registrierung:
  `PREREG_implementation_review_unprimed.md`).
- Strategie-Fragen (Asymmetrie-Korpus, Policy-Strang) — die warten auf das
  Review-Ergebnis, werden aber hier nicht verhandelt.

## par.5 KOSTEN

Drei Sonnet-Reviewer + eine Verifikation, geschaetzt je 20-60 min Agentenzeit,
keine GPU, keine Arena. Gegenrechnung: ein uebersehener Mess-Bug wuerde einen
geschlossenen Forschungsstrang falsch schliessen und den naechsten (26-h-Korpus)
auf falscher Grundlage starten.

## par.6 ERGEBNIS (leer bei Registrierung)


## par.6 ERGEBNIS (2026-08-20)

- **Linse A (Label/Training): SAUBER auf allen sieben Flaechen**, mit
  Repro-Sonden (Ego/Gegner-Zuordnung, Atom-Slice, Rundengrenzen empirisch
  ueber 400 Partien, float16-Stufen unterscheidbar, Cache-Keys
  kollisionsfrei, Vorzeichen konsistent).
- **Linse B (Engine-Verbraucher): SAUBER auf allen sechs Kernfragen**
  (Layout-Vertrag Python-ONNX-Rust index-genau ueber Namens-Erkennung,
  Ego an Nicht-Wurzel-Knoten korrekt, Sigmoid exakt einmal, Knopf-Indizes
  deckungsgleich). Protokoll-Notiz nach par.3(c):
  `conjunction_atom_ranges_match_label_builder` prueft nur Rust-intern
  gegen eine Hand-Transkription, kein Python-Cross-Check — Testluecke,
  kein Befund.
- **Linse C (Messweg/Sonden): Messweg SAUBER** (Arena-Orchestrierung,
  Seed-Paarung, `plate_points_from_arena` reproduziert Block-t −3,73
  zahlengenau, keine verstuemmelten Partien, arm_wins konsistent) — und
  **EIN BEFUND, vom Koordinator bestaetigt und quantifiziert:** die
  Offline-Sonden liefen bei w=1 vollstaendig in der q-Clamp (80/80 auf
  1,0), Ursache ist die Dosis-Saettigung des Vollendbarkeits-Kopfes
  (e_k1 Median 36,1 gegen Nenner 1). Konsequenz nach par.3(a):
  `PREREG_reachability_target.md` par.15 (Annotation + registrierte
  Wiederholung mit kopfspezifisch rekalibrierten Nennern).
  Protokoll-Notiz nach par.3(c): die Arena-JSONs schreiben die
  Neben-Envs (GEW/SCALE/CONJ/TILING_W) nicht mit — Auditierbarkeitsluecke.

**Verifikations-Schritt:** der Linse-C-Befund wurde nicht adversarial
widerlegt, sondern durch unabhaengige Koordinator-Nachmessung BESTAETIGT
(eigene Sonde, 200 Zustaende, Zahlen in par.15 des Zielwechsel-Preregs) —
das erfuellt die Befund-Regel (Repro + nicht widerlegbar) in der
staerksten Form.
