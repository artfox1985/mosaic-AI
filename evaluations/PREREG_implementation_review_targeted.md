<!-- STATUS: OFFEN | Frage: Ist der Mess-Pfad des Zielwechsel-Ergebnisses (par.14) frei von Perspektiven-, Vorzeichen- und Index-Fehlern -- oder ist das invertierte k1-Delta ein Implementierungs-Artefakt? | Beleg: offen, nichts gestartet. Anlass: invertiertes Vorzeichen ist die typische Bug-Signatur; die Kette entstand in 48 h aus drei Haenden. -->

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
