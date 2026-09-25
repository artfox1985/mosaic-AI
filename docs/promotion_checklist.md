# Promotions-Checkliste (Champion-Wechsel)

**Kanonischer Ort dieser Liste seit 2026-08-28** (Nutzer-Hinweis: STATUS.md
taugt fuer Aktuelles und Offenes, dauerhaftes Prozesswissen verrottet dort
ins Archiv). Herkunft: Nutzer-Hinweis 2026-08-09 ("die Kader-Praxis wurde
bis dato nicht konsequent umgesetzt"), Langform bis dahin in
`archive/history.md` (~Z. 14402). Wer hier etwas aendert, aendert HIER --
STATUS.md verweist nur noch auf diese Datei.

**Schwesterdatei `generation_loop.md`** (2026-08-31): dort steht, wie eine
Generation zustande kommt und an welchen zwei Toren sie gemessen wird. Ein
Champion-Wechsel ist Schritt 7 jener Schleife -- und faellt nur, wenn die
Kante gegen den AMTIERENDEN Champion faellt, nicht schon beim Ratschen-Tor
gegen die Vor-Generation.

Bei JEDEM Champion-Wechsel vollstaendig abarbeiten, nicht aus dem
Gedaechtnis:

1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart). **Und die Spec muss
   fuer den Server auffindbar sein** (seit 2026-09-10): `server.py` liest
   `models/<neu>.spec.json`, sonst `models/frozen_champions/<neu ohne _brierbest>/spec.json`
   (Schritt 7), sonst meldet er laut und spielt mit Env-Defaults. Vorfall: v25-b01 bis
   v27-b01 hatten keine Datei unter dem Champion-Namen (Einfrieren: Spec blieb unter
   `v24-b07_brierbest.spec.json`), der Server kehrte still zurueck, der Browser-Champion
   spielte zwei Tage ohne Huelle. Nach dem Neustart die Konsolenzeile "Champion-Spec ..."
   lesen.
2. Elo-Kante **Gating** (gegen Champion-1) -- inkl. Replikations-Zeile,
   falls Fruehstopp unter 150 Paaren. Seit 2026-09-12 traegt die Zeile ihre
   Seed-Bloecke und den Frueh-Stopp: `elo_tracker.py add ...
   --units-from-paired-artifact <Artefakt-JSON> [--early-stop]` (paired_gating
   druckt den Zusatz am Ende); der Tracker zieht sein Intervall dann blockweise.
3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=50** (geaendert
   2026-09-19, Nutzer: der Fruehstopp sei hier vertretbar, weil die Leiter
   ueber die Sprossen mehrfach verbunden ist und das Gewicht einer einzelnen
   Kante entsprechend klein bleibt). **Umgesetzt als kleineres festes n, nicht
   als Fruehstopp:** `tools/frozen_referee_match.py` kennt kein SPRT (geprueft
   2026-09-19, nur `--n-games` ueber eine feste Seed-Liste), ein Fruehstopp
   waere dort Bauarbeit. Der Nebeneffekt ist erwuenscht: ein kleineres festes n
   verbreitert nur das Intervall, waehrend ein Stopp den Punktschaetzer nach
   oben zoege (`tools/elo_tracker.py` Z.117-120: "die Siegquote einer solchen
   Kante ist nach oben verzerrt; der Fit kann das nicht korrigieren").
   **Kosten:** rund 7 statt 21 min (gemessen 1.246/1.281 s fuer 150 Partien).
   Vorher: festes n=150 (Praezedenz v18/v19/v20-Verankerung). Seit der Kapselung:
   Anker-Identitaet in der Zeile als `Heuristik_hv4_anchor` fuehren (seit der Neuverankerung 2026-09-12; davor `Heuristik_hv1_anchor`, seit der
   Umbenennung am 2026-08-28; aeltere CSV-Zeilen tragen `Heuristik_v2huelle`
   bzw. `Heuristik` und werden NICHT umgeschrieben -- seit dem 2026-08-31 faltet
   `ANCHOR_ALIASES` in `tools/elo_tracker.py` sie auf denselben Knoten, und der
   Anker IST dieser Knoten: `ANCHOR_NAME = "Heuristik_hv4_anchor"`); die
   Knoepfe liegen in dessen `spec.json` (elo_tracker `--knobs`).

   **Die Worker-Parameter AUSDRUECKLICH setzen** (nachgetragen 2026-09-25):
   `--sims-worker 150 --c-puct-worker 0.3`. `tools/frozen_referee_match.py` hat als Default
   400 / 1,5 -- das ist die Einstellung eines NETZ-Artefakts, nicht die des Ankers. Genau so
   ist am 2026-09-12 schon einmal eine Anker-Kante falsch gelaufen
   (`archive/elo_history_segment2_anchor_mislabelled.csv`). Vorbild v32-b01:

   ```
   python -u tools/frozen_referee_match.py --artifact-dir models/frozen_heuristics/hv4_anchor --model-a models/alphazero_<neu>.onnx --spec-a models/<neu>.spec.json --sims-a 400 --c-puct-a 1.5 --sims-worker 150 --c-puct-worker 0.3 --n-games 50 --seed-base <neu> --workers 6 --force-cross-era --out evaluations/artifacts/anchor_<neu>_vs_hv4_anchor.json
   ```

   **Aera-Regel (Nutzer-Entscheid 2026-08-29): Cross-Aera ist der
   Normalfall.** Das im Artefakt mitgelieferte Wheel wird NICHT bei jedem
   Motorschritt nachgezogen -- es ist das Selbst-Invarianz-Instrument des
   Ankers (Golden-Probe/Referee-Probe: spielt er noch wie am Einfriertag?),
   kein Bestandteil der Leiter. Anker-Kanten laufen also regulaer gegen den
   jeweils aktuellen Live-Motor. Aendert sich die Engine GRUNDLEGEND
   (Anker-Golden-Probe kippt oder Spielregeln/Wertung aendern sich), hilft
   kein Nachziehen: dann spielt der Anker anders, und es braucht ohnehin
   einen Elo-Recheck mit neuem Leiter-Segment (Praezedenz: R5-Fix-Leiter,
   Kanten ueber die Fix-Grenze nie mischen).
4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- der Punkt, der bei
   v20 UND v21 zunaechst fehlte; ohne ihn ruht die Elo-Schaetzung auf zu
   wenigen Kanten (v21 nach dem Gating: CI +-90 Punkte).
5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
   Eintrag in die #29-Buchfuehrung.

   **BEFUND 2026-09-19: R5 und R4b werden seit v24-b06 NICHT mehr gefahren**,
   die Zeile oben beschreibt insoweit einen Zustand, den seit fuenf
   Generationen niemand herstellt. Beleg: das Promotions-Kapitel von v24-b06
   sagt woertlich "Nicht gemessen: R5/R4b-Sonden" (`archive/history.md`), und
   in `evaluations/artifacts/` ist das juengste `r5_value_calibration_*.json`
   vom 2026-08-31 (v23-b01). Dazu sind beide Werkzeuge auf die Alt-Aera
   voreingestellt: `tools/r5_value_calibration.py` hat
   `--model-path-for-api models/alphazero_v18_best.onnx` als Default, und
   `tools/r4b_zone_probe.py` liest einen festen `MODEL_KEY` aus einem
   vorberechneten Referenz-JSON.

   **Kein Entscheid des Koordinators, sondern eine Vorlage:** entweder die zwei
   Sonden werden auf den aktuellen Kontrakt gezogen und wieder Pflicht, oder
   die Zeile wird auf "Platt und Alt-Set-Brier" gekuerzt. Bis dahin gilt, was
   seit v24 praktiziert wird -- aber jetzt sichtbar statt stillschweigend.

   **Stand 2026-09-25:** fuer `v32-b01` auf Nutzer-Anweisung gefahren (*"r5 und r4b
   mitfahren"*), alle GEPAART gegen den Vorgaenger. Gepaart heisst: dasselbe Substrat wie beim
   Vorgaenger-Lauf -- also die Parameter aus dessen ARTEFAKT lesen, nicht aus den Defaults.
   Die Aufrufe von v32 (Rezept und Seeds wie bei v31):

   ```
   python -X utf8 -u tools/r4_value_calibration.py --models models/alphazero_<neu>.pth --sims 400 --c-puct 1.5 --n-states 72 --k-refills 16 --data-glob "data/selfplay_v30-b02-policy_*.pkl" --state-seed 20260803 --n-bootstrap 1000 --out evaluations/artifacts/r4_value_calibration_<neu>_n72.json
   python -X utf8 -u tools/r4b_zone_probe.py --r4b-json evaluations/artifacts/r4_value_calibration_<neu>_n72.json --model-key models/alphazero_<neu>.pth --out evaluations/artifacts/r4b_zone_probe_<neu>.json
   python -X utf8 -u tools/r5_value_calibration.py --eval-set evaluations/frozen_eval_set.pkl --models models/alphazero_<neu>.pth --sims 400 --c-puct 1.5 --n-states 24 --n-combos 6 --curve-n-states 233 --seed 1000 --out evaluations/artifacts/r5_value_calibration_<neu>.json
   ```

   **Paarungs-Belege, je einer:** R4 -- `game_id`, `true_margin`, `true_winprob` Zustand fuer
   Zustand identisch; R5 -- die Kennlinie (a, b) bitgleich. Kosten gemessen: R4 2.756 s
   einkernig, R4b 43 s, R5 878 s. **R4-Substrat rotiert beim v34-Wechsel heraus**
   (`selfplay_v30-b02-*`); danach ist die Reihe nur noch gepaart, wenn die 72 Zustaende vorher
   gesichert wurden.

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
   --n-states 300` (gemessen 2026-09-25: 708 s). Seit 2026-09-25 heisst die Ausgabe nach dem
   Modell; vorher schrieb jeder Lauf ohne `--out` in denselben Pfad, und das v31-Ergebnis steht
   deshalb unter `gumbel_scale_calibration.json`. Der Aera-Wechsel v18->v21 hat das Verhaeltnis
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
7. **Eingefrorenes Artefakt `models/frozen_champions/<neu>/`** (seit v21,
   `PREREG_agent_encapsulation.md` par.8): `model.onnx`, `model.pth`,
   `spec.json`, das Wheel, `manifest.json`, `golden_probe.json`
   (`tools/build_frozen_golden_probe.py --seed-base 916001`, rund 22 min
   einkernig @400), dann venv aus dem Wheel (pip lehnt umbenannte
   Wheel-Dateinamen ab: Kopie unter kanonischem Namen installieren,
   `--no-deps` reicht fuer den Champion-Worker) und der Referee-Selbsttest
   `tools/frozen_referee_match.py --artifact-dir ... --model-a <Artefakt>/model.onnx --spec-a <Artefakt>/spec.json --n-games 2`
   (Handshake, Golden-Selbsttest 10/10, zwei Echtpartien). **Das Manifest
   braucht ZWEI Felder, ohne die der Referee ohne Befund scheitert**
   (Vorfall 2026-09-04 bei v23-b01_k3p10, drei Anlaeufe):
   `name_dialect: "hv"` (sonst uebersetzt der Treiber `hv1 -> v1`, und das
   Wheel weist ab -- sichtbar nur als Broken Pipe) und
   `worker_python.interpreter_relative: "venv/Scripts/python.exe"` (sonst
   KeyError). Dazu die Wheel-sha256 und der Beleg, dass das live installierte
   Wheel dasselbe ist (`site-packages/.../direct_url.json`), sonst ist unklar,
   auf welchem Wheel die Golden Probe entstand.

   **Seit 2026-09-23 gehen `.onnx`, `.pth` und das Wheel des Artefakts NICHT ins Repo**
   (`.gitignore`, Nutzer-Entscheid); getrackt werden Spec, Manifest, Golden Probe und
   `wheel.sha256`. **Kein `git add -f`.** Pruefen mit `git check-ignore -v --no-index <pfad>` --
   ohne `--no-index` schweigt der Befehl bei getrackten Dateien.
   **Das venv braucht kein Netz:** der Worker importiert nur `mosaic_rust` (das v31-venv traegt
   nichts sonst). `python -m venv <artefakt>/venv`, dann
   `<artefakt>/venv/Scripts/python.exe -m pip install --no-index --no-deps <artefakt>/<wheel>`.
   **Zwei-Champion-Regel:** der vorvorletzte Champion faellt aus `frozen_champions/` -- nur mit
   restic-Beleg je Datei und pfadgenauer Nutzer-Freigabe; vor dem Loeschen auf echte Links
   pruefen (`LinkType` Junction/SymbolicLink, NICHT das blosse ReparsePoint-Attribut -- das
   traegt unter OneDrive fast jede Datei).

**Merkregel aus einem echten Vorfall:** Elo-Fragen am Primaerregister
`evaluations/elo_history.csv` pruefen, nicht an Chronik-Texten -- eine
veraltete "fehlt"-Zeile hat zweimal zu Doppel-Vorschlaegen derselben
Messung gefuehrt.
