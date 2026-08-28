# Promotions-Checkliste (Champion-Wechsel)

**Kanonischer Ort dieser Liste seit 2026-08-28** (Nutzer-Hinweis: STATUS.md
taugt fuer Aktuelles und Offenes, dauerhaftes Prozesswissen verrottet dort
ins Archiv). Herkunft: Nutzer-Hinweis 2026-08-09 ("die Kader-Praxis wurde
bis dato nicht konsequent umgesetzt"), Langform bis dahin in
`archive/history.md` (~Z. 14402). Wer hier etwas aendert, aendert HIER --
STATUS.md verweist nur noch auf diese Datei.

Bei JEDEM Champion-Wechsel vollstaendig abarbeiten, nicht aus dem
Gedaechtnis:

1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
2. Elo-Kante **Gating** (gegen Champion-1) -- inkl. Replikations-Zeile,
   falls Fruehstopp unter 150 Paaren.
3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
   Fruehstopp** (Praezedenz v18/v19/v20-Verankerung). Seit der Kapselung:
   Anker-Identitaet in der Zeile als `Heuristik_hv1_anchor` fuehren (seit der
   Umbenennung am 2026-08-28; aeltere CSV-Zeilen tragen `Heuristik_v2huelle`
   bzw. `Heuristik` und werden NICHT umgeschrieben); die
   Knoepfe liegen in dessen `spec.json` (elo_tracker `--knobs`).
4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- der Punkt, der bei
   v20 UND v21 zunaechst fehlte; ohne ihn ruht die Elo-Schaetzung auf zu
   wenigen Kanten (v21 nach dem Gating: CI +-90 Punkte).
5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
   Eintrag in die #29-Buchfuehrung.

   5b. **Anzeige-Kalibrierung nachziehen**: Platt-Parameter A/B des NEUEN
   Champions in `server.py` (`_DISPLAY_CAL_A/_B`) eintragen -- sie sind
   modellspezifisch (gemessene Drift: v19 B=1,93 / t34 0,97 / v21 0,906).
   Quelle: `python tools/platt_fit.py --models models/alphazero_<neu>.pth`.
   Ohne das zeigt die GUI die Gewinnwahrscheinlichkeit mit der Kurve des
   VORGAENGERS an.
   **Zusatz 2026-08-28 (Verteilungs-Caveat):** der Fit lief bisher auf
   `evaluations/frozen_eval_set.pkl` (frozen_v1, Zustaende der v12-Aera).
   Ab dem ersten spaltenbewussten Champion beides fahren: B auf dem
   Frozen-Set weiter als TRENDMETRIK protokollieren, den ANZEIGE-Fit aber
   auf zeitgemaessen Zustaenden rechnen (Kandidat: `data/holdout/` oder
   frische Partien der neuen Aera).

   5c. **sigma/Prior-Balance messen** (seit 2026-08-09, aus Task G):
   `tools/gumbel_scale_calibration.py --model <neu> --sims 400
   --n-states 300`, ~10 min. Der Aera-Wechsel v18->v21 hat das Verhaeltnis
   von 1,232 auf 2,287 verschoben; R3 lag mit 2,972 praktisch auf der
   Schwelle. **Ueberschreitet die Gesamt-Kennzahl 3, oeffnet sich die
   c_visit/c_scale-Familie per REGEL wieder** (kein Ermessen) -- zugleich
   Verfallsdatum-Waechter fuer die H0-Befunde der Wurzel-Regler-Familie
   (in anderem Balance-Regime gemessen).

   5d. **Netz-Paritaets-Fixture neu erzeugen** (seit 2026-08-28):

   ```
   $env:MOSAIC_UPDATE_NET_PARITY_FIXTURE=1
   cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture
   ```

   Danach die Variable loeschen und denselben Test noch einmal fahren – er
   muss in einem FRISCHEN Prozess gruen sein (das ist zugleich die Probe,
   dass der Hash ueber Prozessgrenzen haelt). Die Fixture
   (`engine/tests/fixtures/net_parity_champion.txt`) folgt dem EINEN
   amtierenden Champion aus `models/champion.txt`; **Alt-Fixturen verfallen
   mit ihrem Champion**, ihr Hash wird nicht weitergeschleppt. Ohne diesen
   Schritt schlaegt der Suite-Test nach dem Champion-Wechsel fehl – mit
   genau dieser Anleitung in der Fehlermeldung. Nachfolger der
   `tools/parity_probe.py`-Aera (deren Soll-Hash `8c6684ff...` hing an
   `v20_2d_opp_brierbest` und ist am 2026-08-28 geschlossen worden).

6. STATUS-Champion-Zeile + history-Kapitel nachziehen.

**Merkregel aus einem echten Vorfall:** Elo-Fragen am Primaerregister
`evaluations/elo_history.csv` pruefen, nicht an Chronik-Texten -- eine
veraltete "fehlt"-Zeile hat zweimal zu Doppel-Vorschlaegen derselben
Messung gefuehrt.
