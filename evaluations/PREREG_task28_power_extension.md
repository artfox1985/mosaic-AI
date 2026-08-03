# Vorregistrierung: Task-#28-Power-Erweiterung -- Konfirmation des la20-Denial-Effekts

**Angelegt 2026-08-03, NACH Sichtung des Erst-Sweeps (la20: Gegnerpunkte
-6,16, p=0,078 bei n=75 Paaren), VOR jeder weiteren Partie.** Nutzer-Auftrag:
mehr Power vor dem PCR-Nachtlauf. WICHTIG zur Testintegritaet: die
Erst-Stichprobe wurde bereits ausgewertet -- eine simple Verlaengerung und
gepoolte Auswertung waere Optional Stopping (Alpha-Inflation). Deshalb:

## Design (VORAB festgelegt)

- **NUR zwei Arme** (Power-Konzentration auf den staerksten Kontrast):
  `la00` (w=0,1, lambda_aggr=0) und `la20` (w=0,1, lambda_aggr=2,0), beide
  `v19_2d_opp_best` vs. fixen `v19_2d_best` (w=0) -- identisches Setup wie
  der Erst-Sweep.
- **150 FRISCHE Paare je Arm** (300 Spiele/Arm), NEUER Basis-Seed
  **30260803** (disjunkt von 20260803), identische Seed-Liste zwischen den
  beiden Armen, kein Fruehstopp (sprt_alpha/beta 1e-9, max_pairs 150).
- **Primaertest: NUR die frischen Paare** (unabhaengige Konfirmation,
  unkontaminiert vom Erst-Blick): gepaarter t-Test der GEGNERPUNKTE
  la20 vs la00 je Seed-Paar, zweiseitig, alpha=0,05. Power-Kalkuel: bei
  wahrem Effekt ~-6 und SE~2,4 (aus Erst-Streuung skaliert) ist t~2,5
  erwartbar.
- **Guardrail unveraendert**: Win-Paar-Differenz la20 vs la00, exakter
  Vorzeichentest; signifikant schlechter -> disqualifiziert.
- **Sekundaer berichtet (nicht entscheidend)**: gepoolte Schaetzung ueber
  alle 225 Paare (Erst+frisch) mit dem Hinweis auf die Erst-Blick-
  Kontamination; eigene Punkte; Floor.

## Interpretationsregeln

- Frische Stichprobe p<0,05 UND Guardrail OK -> Denial-Effekt bei w=0,1/
  lambda=2 KONFIRMIERT; la20 wird die dokumentierte GUI-Empfehlung
  ("aggressiver Modus"), Task #28 endgueltig positiv abgeschlossen.
- p>=0,05 -> Effekt bleibt unbestaetigt; KEINE weitere Verlaengerung
  (zwei Anlaeufe reichen) -- naechster legitimer Schritt waere ein
  w-Sweep als NEUE Vorregistrierung, nicht mehr Paare.
- Guardrail gerissen -> la20 disqualifiziert, unabhaengig vom p-Wert.

## Ausfuehrung

Nach dem laufenden R4-Lauf (CPU-Ruhe), VOR Wheel-Install und PCR-Nachtlauf.
Kosten: 2 x 150 Paare ~ 2 x 20-25 min. Auswertungs-Code identisch zum
Erst-Sweep (per_pair_scores, gleiche Statistikfunktionen).
