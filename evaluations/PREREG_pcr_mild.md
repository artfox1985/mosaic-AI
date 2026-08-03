# Vorregistrierung: PCR mildes Regime (p=0,5 / cheap=300) -- Task-#14-Folgemesspunkt

**Angelegt 2026-08-03, VOR jedem Lauf dieses Arms.** Nutzer-Auftrag nach dem
negativen p=0,25/cheap=150-Ergebnis (`PREREG_pcr.md`, Orakel 0/6 +
Doku-Arena 67:83): das aggressive Regime war zu teuer fuer die Policy --
dieses Dokument misst den MILDEN Messpunkt. Praktischer Hintergrund
(Nutzer, 2026-08-03): ein klassischer v20-Self-Play-Lauf (~6000 Spiele,
2D-Generator, 600 Sims) kostet ~21h Wandzeit -- ohne eine Verbilligung
wird er nicht gestartet. Die Regeln unten duerfen nach Sichtung von
Zwischenergebnissen nicht mehr geaendert werden.

## Arme

| Arm | Suchregel | Korpus |
|---|---|---|
| `pcrkontrolle` (Baseline) | jeder Zug Voll-Suche @600 | BESTEHEND (`data_pcr_ab/`, 117 Dateien/1170 Spiele, 4h-Lauf vom 2026-08-02) -- wird WIEDERVERWENDET, kein neuer Lauf |
| `pcrmild` (neu) | `pcr_full_prob=0.5`, `pcr_cheap_sims=300` @ Generator `v19_2d_best`@600 | neuer Self-Play-Lauf, WANDZEIT-gematcht (siehe unten) |

Erwarteter Rahmen: 0,5*600+0,5*300 = 450 Sims/Entscheid (Faktor 1,33x
weniger; realer Wandzeit-Gewinn nach Fix-Overhead eher ~1,2-1,25x).
Policy-Ziel-Quote auf Entscheiden: ~50% (statt 25% im aggressiven Regime),
und die Cheap-Zuege sind mit 300 Sims deutlich verlaesslicher als mit 150.

## Wandzeit-Matching

Gleiches Prinzip wie das Original (T=4h-Aequivalent, gleiche Maschine,
gleiche Thread-Zahl 11, MASCHINE SONST IDLE -- kein paralleles Training,
keine Agenten-Builds; die Kontrolle lief unter denselben Bedingungen):

1. **Kalibrierungs-Batch**: ~30 Spiele `pcrmild`, Spiele/Stunde messen.
2. **Spielzahl-Ziel** = gemessene Rate x 4h, auf per_file=10 gerundet.
3. Voller Lauf mit diesem Ziel; tatsaechliche Wandzeit + Spiele/h werden
   berichtet (DER praktische Deliverable: implizierte Wandzeit fuer einen
   6000-Spiele-v20-Lauf mit diesem Regime).

Policy-Maske (`policy_target_valid=false` -> `policy_weight=0`) ist seit
Commit 2777cf6 in der Trainings-Pipeline aktiv und rauchtest-verifiziert.

## Training + Entscheidung (identisch zum Original-PREREG, plus Arena-Pflicht)

- 6 gepaarte Seeds `pcrmild_s1..s6` from scratch, flacher Encoder,
  Standard-Rezept -- gegen die BESTEHENDEN `pcrkontrolle_s1..s6`-Werte?
  NEIN: die alten 12 Checkpoints sind geloescht und GPU-Training ist
  nicht bit-reproduzierbar -- die 6 Kontroll-Laeufe werden NEU gefahren
  (identisches Rezept/Seeds, bestehender Kontroll-Korpus, Sandbox-
  Mechanik wie `tools/train_pcr_dose.py` -- der Treiber wird um einen
  `--mild`-Modus ergaenzt, Arm-Namen `pcrmild`/`pcrkontrolle2`, keine
  Namens-Kollision mit geloeschten Checkpoints noetig, aber saubere
  Elo-Namen).
- **Primaer**: die zwei Orakel-Metriken, gepaart, wie gehabt.
- **Arena ist diesmal PFLICHT, nicht optional** (Lehre 2026-08-03:
  Praediktoren-Konflikte an Korpus-Regime-Grenzen): bester
  `pcrmild`-Seed vs. bester `pcrkontrolle2`-Seed (je Primaermetrik),
  `paired_gating.py --no-promote-winner`, Standard-SPRT.
- **Uebernahme-Regel fuer v20**: `pcrmild` wird NUR dann fuer den
  v20-Self-Play empfohlen, wenn (a) Orakel-Metriken NICHT beide
  signifikant dagegen sprechen UND (b) die Arena keinen signifikanten
  Nachteil zeigt (SPRT-H1 fuer kontrolle = disqualifiziert) UND (c) der
  gemessene Wandzeit-Gewinn >=1,15x betraegt (darunter lohnt der
  Qualitaets-Restrisiko-Trade nicht). Fenster-Politik unveraendert:
  PCR-Spiele wandern NIE als Tail in spaetere Fenster.

## Bekannte Einschraenkungen

1. Flacher Encoder als Messproxy (wie alle Sweep-PREREGs).
2. Kontroll-Korpus stammt vom 2026-08-02 (anderer Engine-Commit als der
   neue Lauf) -- gleiche Akzeptanz wie im Original (dort lagen ebenfalls
   zwei Commits zwischen den Armen).
3. Nur EIN mildes Regime (0,5/300) -- keine Dosis-Kurve; ein weiterer
   Messpunkt waere eine neue PREREG.
4. Ein Vergleichsarm "uniform 450 Sims jeder Zug" (gleiche Ø-Sims, ohne
   Mischung) waere wissenschaftlich sauberer zur Trennung
   "Mischung vs. einfach weniger Suche" -- aus Kostengruenden bewusst
   NICHT Teil dieses Tests (waere ein dritter 4h-Lauf); als Limitation
   dokumentiert.

## Ausfuehrungsplan

1. Kalibrierungs-Batch + voller `pcrmild`-Lauf im naechsten
   IDLE-Maschinen-Fenster (nach Ende der laufenden GPU-Queue; Wandzeit-
   Fairness verlangt exklusive Maschine -- realistisch als Nachtlauf).
2. `tools/train_pcr_dose.py --mild`-Modus (additiv), 12 Laeufe,
   Diagnose, gepaarte Auswertung -> `train_pcr_mild_result.json`.
3. Arena (Pflicht), elo_tracker-Protokoll.
4. Bericht inkl. implizierter v20-Wandzeit; Checkpoints erst nach
   Ergebnis-Diskussion loeschen.
