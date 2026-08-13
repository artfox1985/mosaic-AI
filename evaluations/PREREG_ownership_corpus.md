# PREREG: Ownership-Korpus — Generierungsplan (Zwei-Pole)

Stand 2026-08-14, PLAN (nichts gestartet — durchgehend Plan-Zeitform).
Nutzer-Auftrag: *"dann mach schon mal den generierungsplan für den ownership
korpus"*. Aufsetzend auf PREREG_ownership_consumer.md (Verbraucher-Entwurf,
Tor A: Kopfgüte VOR Verbraucher-Bau) und der abgeschlossenen
Generator-Kampagne (PREREG_provocation… noch PREREG_provokation.md §13–§19).

## §1 Geprüfter Ist-Stand (Generator-Sortiment, aktuelle Ära)

| Quelle | Kriterium | Niveau | Beleg |
|---|---|---|---|
| Spaltenbau (MOSAIC_SPALTENBAU, R3-Pfad) | k1 vertikal | 3,15 Ø; 8/20 Partien ≥1 volle Spalte (7×7, 1×14) | konfund_AC Arm 0, nachgerechnet |
| Plattenbauer k2 (MOSAIC_PLATTENBAU=2, mit Special-Erweiterung) | k2 diagonal | 5,65 Ø; **13/23 volle Diagonalen** | k2_special_k2seeds Arm 1, nachgerechnet |
| Heuristik (wertung_progress, Elo-Anker) | k6 spezial | −6,60 bis −11,10 — bestes k6-Niveau im Projekt | k6-JSONs, Gegner-Seite nachgerechnet |
| Beifang aller Arme | k3 mehrfarbig / k5 Ecken / äußere Felder | 5–6 / 4,2–4,8 / 10,6 | konfund_AC + special_r17, nachgerechnet |
| k0/k7 | — | Nutzer-Entscheid: verteidigen, nie anstreben — Deckung nur beiläufig | STATUS |
| k4 horizontal | — | 0,6–1,0; Nutzer: Spielarchitektur-Problem | dito |

Infrastruktur (geprüft): Standard-Fenster lädt `data/*.pkl` NICHT-rekursiv
(train.py:552) — ein Unterordner ist strukturell getrennt. Streuung
(MOSAIC_WERTUNG_STREUUNG_MAX, partie-seed-abgeleitetes Shaping-Gewicht) ist in
run_net_self_play verdrahtet. Ownership-Kopf: 72 Feld-Labels + 68
Konjunktions-Labels (config.py:78/118), Champion-Gewicht bisher 0,0.

## §2 Korpus-Aufbau: vier Arme

Ablage: `data/ownership_corpus/` (strukturell außerhalb des Standard-Fensters,
§1). Dateinamen nach Generator-Konvention (Erzeuger-Champion): `v21_own_a_*`,
`v21_own_k1_*`, `v21_own_k2_*`, `heur_own_*`.

| Arm | Aufbau | Anteil | Zweck |
|---|---|---:|---|
| A | Netz-Self-Play + Streuung, KEINE Bauer-Knöpfe | 3000 (50 %) | Basisverteilung/Kalibrierung — der Kopf muss realistische Vollendungsraten sehen, nicht nur Erfolgsfälle |
| B | wie A + MOSAIC_SPALTENBAU (R3-Pfad) | 1000 | k1-Positivbeispiele (~0,45 Spalten/Partie) |
| C | wie A + MOSAIC_PLATTENBAU=2 | 1000 | k2-Positivbeispiele (>50 % volle Diagonalen) |
| D | Heuristik-Self-Play (150 Sims) | 1000 | k6-Demonstrationen + generelle Plattenbewirtschaftung (wertung_progress); billigster Arm |

Bewusst KEINE nachträgliche Selektion in v1: Die Arm-Quoten ERSETZEN die
Selektion (gezielte Anreicherung statt Verzerrung der Basisrate). Eine
Selektions-Stufe (plattenreiche Partien übergewichten) bleibt als v2-Hebel
vorregistriert, falls Tor A an zu dünnem Positiv-Signal scheitert.

Nach der Generierung, VOR dem Training: **Deckungs-Bericht** je Kriterium
(Anzahl Partien mit positivem Label je Geometrie-Einheit, beide Spielerseiten
getrennt) — die Basisraten-Falle aus der Skill-Konfundierungs-Lehre.

## §3 Offene Prüfpunkte VOR dem Start (jeder einzeln, mit Prüfstelle)

1. **Policy-Ziele unter Vorzug**: Was zeichnet run_net_self_play als
   Policy-Target auf, wenn der Bauer-Vorzug die Suchentscheidung übersteuert?
   (self_play.rs, Aufzeichnungspfad lesen.) Demonstrations-Targets sind
   gewollt (Zwei-Pole-Idee), aber es muss BEKANNT sein, was im Record steht.
2. **Wirken die Bauer-Knöpfe im Self-Play auf beide Spieler?** Die Messungen
   liefen in der Arena (Netz-Seite). Für den Korpus ist beidseitiges Steuern
   in Arm B/C erwünscht — prüfen, nicht annehmen.
3. **Konjunktions-Breite**: config.py:118 sagt 68, der
   neural_net.py-Kommentar (Zeile ~1837) sagt [72:97]/[97:122] = 25 je Spieler
   — eine der beiden Angaben ist veraltet. Vor dem Training auflösen.
4. **Fenster-Verträglichkeit**: Der Trainings-Lauf braucht einen additiven
   Datei-Zugang (z. B. `--extra-data-dir`, Default leer) — kleiner
   train.py-Umbau, vorab bauen und mit leerem Default byte-identisch belegen.
5. **GPU-Verdikt §22**: Bei ≥2× Durchsatz die Arme A–C über den Async+ORT-Pfad
   fahren; sonst klassisch 8 Threads. Der Plan hängt davon NICHT ab, nur die
   Laufzeit.

## §4 Training + Abnahme (Tor A aus PREREG_ownership_consumer.md)

- Warm-Start vom Champion (v21_2d_brierbest), Standard-Rezept (lr 5e-5,
  cosine), `--ownership-weight 0,2` (Präzedenz: own02-Lauf) + `--conjunction`.
- Fenster: aktuelles Standard-Fenster + `data/ownership_corpus/` (additiv).
- Während Generierung nie gleichzeitig trainieren ohne
  MOSAIC_DATA_EXCLUDE-Pinning (stehende Regel).
- **Abnahme = Kopfgüte, NICHT Arena**: je Feld Brier/AUC gegen die Basisrate
  auf Held-out-Partien (Split auf Partie-Ebene); je Kriterium Rangkorrelation
  E_k gegen tatsächliche Plattenpunkte; Bericht getrennt nach eigener und
  Gegner-Hälfte. Erst nach bestandenem Tor A wird der Verbraucher (P4)
  gebaut.
- Nebenbedingung: policy/value-Offline-Metriken des Laufs mitloggen — ein
  Einbruch dort wäre ein Warnsignal für Demonstrations-Kontamination
  (Prüfpunkt §3.1), aber KEIN Abnahmekriterium dieses Laufs.

## §5 Umfang und Kosten (Herleitung, keine Messung)

6000 Partien gesamt. Bezug: Arena-Durchsatz 248,5 Spiele/h (8 Threads, §20);
Self-Play mit Labels liegt darunter, Heuristik-Arm weit darüber. Grobschätzung
20–30 h CPU für A–C, Arm D <2 h; mit GPU-2× entsprechend die Hälfte. Läuft
unbeaufsichtigt in Etappen (Watchdog vorhanden); Umfang ist ein Regler, kein
Fixum — die Deckungszahlen aus §2 entscheiden, ob nachproduziert wird.

## §6 Was dieser Korpus NICHT ist

Kein Stärke-Training: kein Gating, kein Champion-Anspruch, keine
Elo-Interpretation der beteiligten Konfigurationen. Die Bauer-Knöpfe bleiben
Diagnose-Werkzeuge (nie im Gating); ihre Partien tragen Brett-Fakten-Labels
(Nutzer-Entscheid: Ownership-Labels sind Brett-Fakten, Trainingskorpus
erlaubt).
