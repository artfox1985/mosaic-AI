# Vorregistrierung: λ-Misch-Target auf reinem v18-Korpus (Dosis-Vorziehung)

**Angelegt 2026-08-03, VOR dem ersten Trainingslauf.** Folge-Experiment zu
`PREREG_lambda_target.md` (dort: Offline-Signal klar, Arena-H0, Verdacht
Dosis-Verduennung bei nur 43,8% Sample-Misch-Anteil). Nutzer-Vorschlag
2026-08-03: die vorregistrierte Wiedervorlage ("wiederholen, wenn ein
groesserer Korpusanteil root_q traegt") NICHT auf v20 warten lassen,
sondern JETZT mit einem reinen v18-Korpus vorziehen. Die Regeln unten
duerfen nach Sichtung von Zwischenergebnissen nicht mehr geaendert werden.

## Design

- **Korpus**: NUR die 600 `selfplay_v18_*`-Dateien (eingefrorene
  Hardlink-Sandbox `data_lambda_sweep_v18/`, Manifest
  `train_lambda_sweep_v18only_split.json`). Erwarteter Sample-Misch-Anteil
  ~66% -- das strukturelle Maximum (Tiling-/Ein-Aktion-Schritte loggen nie
  `root_q`), 1,5x die Dosis des 900er-Sweeps. Exakter Wert wird beim
  Build gemessen und hier nachgetragen:
  > **Sample-Misch-Anteil (600 v18-Dateien): 640.246 von 974.937 Samples = 65,67%** (gemessen beim Build 2026-08-03, VOR dem ersten Trainingslauf)
- **2 Arme statt 4**: `l10v18` (λ=1,0, Baseline) vs. `l07v18` (λ=0,7 --
  bester Arm des 900er-Sweeps nach dessen vorregistrierter Regel; die
  Dosis-Wirkungs-Kurve dort war flach, ein Bestaetigungs-Arm genuegt).
  NEUE Namen, damit Modell-/Elo-Eintraege nicht mit dem 900er-Experiment
  kollidieren (dessen `lam*`-Checkpoints sind geloescht, die Elo-Historie
  traegt aber `lam07_s3_best`/`lam10_s4_best`).
- **6 gepaarte Seeds** (1..6), identisches from-scratch-Rezept wie im
  900er-Sweep (`tools/train_lambda_sweep.py --corpus v18only`).
- **Kleinerer Korpus als Feature, nicht Bug**: 600 statt 900 Dateien senkt
  die Absolutwerte aller Metriken (Dosis-Befund) -- fuer den GEPAARTEN
  λ-Vergleich irrelevant, beide Arme sehen exakt denselben Korpus.

## Entscheidungsregeln (VORAB festgelegt)

1. **Offline-Gate** (wie gehabt): gepaartes `value_r2_rounds_1_4`,
   Aufloesungsgrenze 0,015. Kein Signal ueber der Grenze -> λ ist auch bei
   ~66% Dosis offline wirkungslos -> Experiment beendet, λ gilt als
   erschoepft getestet (KEINE weitere Wiedervorlage aus Dosis-Argumenten;
   die v20-Wiedervorlage aus PREREG_lambda_target.md entfaellt damit).
2. **Arena ist der ENTSCHEIDENDE Schritt** (Lehre aus dem 900er-Sweep --
   ein Offline-Signal allein ist einordbar und reicht nicht): bei
   Offline-Signal folgt `paired_gating.py` bester `l07v18`-Seed vs. bester
   `l10v18`-Seed (je Arm bester Seed nach Primaermetrik, Praezedenz
   900er-Arena), `--sims 400 --no-promote-winner`.
3. **Nur ein arena-signifikanter Sieg** (SPRT-H1 bzw. McNemar p<0,05)
   macht λ=0,7 zum Trainings-Standard-KANDIDATEN fuer v20 (finale
   Uebernahme dann im v20-Zyklus selbst). Arena-H0/Wash bei vorhandenem
   Offline-Signal -> λ bleibt Beobachtung; danach ist der naechststaerkere
   Test NICHT mehr Dosis (Maximum erreicht), sondern ein anderes Regime
   (z.B. λ auf 2D-Warm-Start statt flach from scratch) -- das waere eine
   NEUE Vorregistrierung.
4. Orakel-Metriken sekundaer/Sanity wie gehabt (Erwartung: flach).

## Bekannte Einschraenkungen

1. Flacher from-scratch-Encoder als Proxy (Champion ist 2D warm) --
   identische Einschraenkung wie alle Sweep-PREREGs.
2. ~66% ist das Sample-Maximum; die restlichen ~34% (Tiling/Ein-Aktion)
   trainieren konstruktionsbedingt immer auf reinem z. Ein "100%-Korpus"
   existiert nicht (Praezisierung vs. die urspruengliche
   Wiedervorlage-Formulierung).
3. Der Retest bindet an v18-Selbstspiel-Daten (v18_best-Generator@600) --
   Generations-Confound gegenueber dem 900er-Fenster ist bewusst
   akzeptiert (der VERGLEICH bleibt intern gepaart und sauber).

## Ausfuehrungsplan

1. `--corpus v18only`-Modus im bestehenden Treiber (additiv, Default
   unveraendert), Build + Misch-Anteil-Messung.
2. 12 Laeufe + Diagnose + gepaarte Auswertung
   (`train_lambda_sweep_v18only_result.json`).
3. Bei Offline-Signal: Arena (Regel 2), elo_tracker-Protokoll.
4. Bericht; Aufraeumen der Checkpoints ERST nach Abschluss der
   Ergebnis-Diskussion (Lektion 2026-08-03: nicht direkt nach dem
   automatischen Verdikt loeschen).
