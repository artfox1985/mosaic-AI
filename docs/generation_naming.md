# Benennung der Generationen (damit der Off-by-one nicht wiederkehrt)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

**Die Regel: ein Fenster vN traegt die Partien von Champion v(N-1).** Beleg:
das v22-Fenster enthielt `v21wdl`-Partien (Generator = v21-Champion, alte
Tabelle in `PREREG_v22_window.md`).

Daraus folgt das Muster:

| | |
| --- | --- |
| Self-Play des Champions v(N-1) | fuellt **das vN-Fenster** |
| daraus trainiert | **das vN-Netz** |
| dessen Self-Play | fuellt **das v(N+1)-Fenster** |

**Der haeufige Fehler** ist, das Self-Play, das vN fuettert, "vN-Self-Play" zu
nennen. Es ist das **v(N-1)**-Self-Play. Am 2026-08-25 einmal passiert und in
zwei Preregs korrigiert.

**Sonderfall heuristischer Erzeuger:** ein Fenster kann statt von einem
Champion von einer Heuristik gefuellt werden (so beim v22-Fenster: Erzeuger
ist die Heuristik `hv2`, kein Netz). Die Zaehlung aendert sich dadurch
nicht -- benannt wird das Fenster nach dem Netz, das AUS ihm entsteht.

**Dateinamen folgen dem Erzeuger, nicht der Zielgeneration**: die Partien von
`v18_best` heissen `v18_*`. Beides zusammen ist die Stelle, an der der
Off-by-one entsteht.

## `v22-b03` bleibt UNBELEGT -- die b-Serie hat eine Luecke (Nutzer 2026-08-30)

Die laufende Kette ist `v22-b01, b02, b04, b05, b06` -- **b03 fehlt und
wird nicht nachbesetzt.** Der Name war fuer den Surprise-Weighting-Arm
(`PREREG_policy_surprise_weighting.md`) reserviert; dessen
Entscheidungsmass verlangt aber Policy-Ziele aus einer SUCHE, nicht aus
dem Lehrer -- die gibt es erst mit dem v23-Fenster. **Der Arm heisst
darum `v23-b03`, sobald er faellt.**

Merkregel daraus: ein reservierter Name gehoert der GENERATION, in der
der Arm tatsaechlich faehrt, nicht der, in der die Idee registriert
wurde. Wer eine Luecke in einer b-Serie findet, sucht hier nach ihrer
Begruendung statt nach verlorenen Modellen.

## Der v23-Zyklus ist vorab benannt (Nutzer 2026-08-31)

| Arm | Was |
| --- | --- |
| `v23-b01` | Warmstart aus den v22-b05-Self-Plays (Standardrezept) |
| `v23-b02` | **Kaltstart** -- oeffnet das Rumpfbreiten-Fenster (`PREREG_capacity_sim_frontier.md` par.9); b01 gegen b02 misst nebenbei Warm- gegen Kaltstart auf DEMSELBEN Fenster, was nie gemessen wurde |
| `v23-b03` | Ueberraschungs-Gewichtung (`PREREG_policy_surprise_weighting.md` par.4a) -- der oben reservierte Name, jetzt belegt |
| `v23-b04` | **vorregistriert** (Nutzer 2026-08-31): Kaltstart mit ANDERER Rumpfbreite, der eigentliche Frontier-Punkt (`PREREG_capacity_sim_frontier.md` par.10). Welcher Zweig verbreitert wird, ist offen -- `hidden_size` geht ohne Bau, der Conv-Zweig braucht erst Flags und eine Checkpoint-Ableitung |
| `v23-b05` | **Relabel-Arm** (nachgetragen 2026-09-01, gefahren 2026-09-01): dieselben Fensterdateien wie b01, die 200 Policy-Dateien durch hv2-lehrer-relabelte Kopien ersetzt (`PREREG_reanalyze_label_depth.md` par.A1). b04 blieb unbelegt (Zweig-Entscheid offen), darum die Luecke |
| `v23-b06` | **Kaltstart mit dem b01-Rezept** (`PREREG_capacity_sim_frontier.md` par.14, gefahren 2026-09-02): trennt Startgewicht von Lernraten-Rezept. Ergebnis: 0,18 volle Spalten, 65:95 gegen b01 -- der Kaltstart ist die Ursache, die Linie traegt das Spaltenwissen |
| `v23-b07` | **Reanalyze-Arm** (`PREREG_reanalyze_label_depth.md` par.A4, eingetaktet 2026-09-02): dieselben Partien wie b01, Draft-Policy-Ziele mit dem Generator selbst bei 400 Sims nachgerechnet; b05 war der Lehrer-Relabel, b07 ist Reanalyze im engeren Sinn. Ergebnis (par.A5, 2026-09-03): 75:85 gegen b01, 0,445 volle Spalten gegen 0,515, Orakel knapp vorn -- keine Staerke, weniger Spalten; b01 bleibt Generator |
| spaeter | **Arm K** (Bootstrap-Kohaerenz, `MOSAIC_BOOTSTRAP_COHERENCE=sum1`): bewusst NACH b04 eingetaktet (Nutzer 2026-08-31), weil er als einziger Arm alle Cache-Bloecke entwertet. Nummer folgt der Ausfuehrungsreihenfolge |

Der Zuschnitt steht VOR dem ersten Lauf, damit die Namen nicht nachtraeglich
vergeben werden -- die b03-Luecke oben ist genau daraus entstanden.

## Heuristik-Varianten heissen `hv1` / `hv2` (Nutzer-Anweisung 2026-08-28)

Die Heuristik-Varianten hiessen bis zum 2026-08-28 `v1` und `v2huelle`. Das
kollidierte mit der Netz-Zaehlung (`v21`, `v22`) und passte nicht zum
Korpus-Tag `selfplay_hv2_*`. Seither gilt durchgaengig **`h` = Heuristik**:
`v1` -> **`hv1`**, `v2huelle` -> **`hv2`**; die Artefaktverzeichnisse heissen
`models/frozen_heuristics/hv1_anchor` und `.../hv2_generator`.

**Der Live-Code kennt nur die neuen Namen** -- `hv1` ist der einzige spielbare
Wert, ein Alt-Name ist ein harter Fehler mit Hinweis (`lib.rs`,
`net_mcts.rs::from_spec_file`). Die Alt-Namen leben nur noch an ZWEI Stellen:
in historischen Dokumenten (Preregs, `archive/`, bestehende Zeilen in
`elo_history.csv` -- die werden NICHT umgeschrieben) und in
`tools/frozen_name_dialect.py`. Dort sitzt die Uebersetzung an der
Prozessgrenze: die Wheels der beiden am 2026-08-26 eingefrorenen Artefakte
kennen nur `v1`/`v2huelle`, also uebersetzt der Treiber beim Sprechen mit
ihnen zurueck -- deterministisch am Manifest-Feld `name_dialect`
(`"hv"` = neues Wheel, fehlend/`"legacy"` = altes), NICHT per stillem zweitem
Versuch. Neu eingefrorene Artefakte schreiben `name_dialect: "hv"`.

**Nomenklatur der Trainingsarme** (Nutzer 2026-08-28): fortlaufend `vNN-bMM`
wie die v21-b-Serie, also `v22-b01`, `v22-b02`, ... Folgearme reihen sich
hinten ein.

## Konkrete Kette der laufenden Kampagne (Stand 2026-08-28)

Seit 2026-08-28 wird auch die konkrete Kette HIER gefuehrt (Nutzer-Entscheid);
wer eine Generation abschliesst, zieht diese Tabelle nach.

| | |
| --- | --- |
| `hv2`-Korpus (fertig, 24.000 Partien) | **das v22-Fenster** -- Erzeuger ist die Heuristik `hv2`, kein Champion |
| daraus trainiert (Kaltstart, Arme `v22-b01`/`v22-b02`) | **v22-Netz** |
| dessen Self-Play (12.000 Partien) | fuellt **das v23-Fenster** |
| daraus trainiert (Arme `v23-b01`/`b02`/`b03`/`b05`) | **v23-Netz**; bester Stand `v23-b01_brierbest` (Tor 1 und Tor 2 bestanden, 2026-08-31) |
| dessen Self-Play (12.000 Partien, `selfplay_v23-b01-*`) | fuellt **das v24-Fenster** (`PREREG_v24_window.md` par.6, hv2-Anteil unveraendert) |
| daraus trainiert: `v24-b01` (Standard), `v24-b02` (lambda 0,7), `v24-b03` (Seeding-Schwarm); dazu drei Such-Knoepfe ohne Training (Margen-Saettigung, Risiko-Utility, Gelaender) -- `PREREG_v24_window.md` par.8 | **v24-Netz** |
| Champion der Generation: `v24-b07` (dasselbe Netz wie `v24-b06`, nur andere Spec: Huellenform 2 und K5) | **v24-Netz**, Elo 1311 |
| dessen Self-Play (12.004 Partien, `selfplay_v24-b07-*`) | fuellt **das v25-Fenster** (`PREREG_v25_window.md` par.1) |
| daraus trainiert: `v25-b01` (Warmstart, Spec unveraendert) | **v25-Netz**, Champion seit 2026-09-08, Elo 1376 |
| dessen Self-Play (`selfplay_v25-b01-policy`, `-value-tempc`, `-value-excursion`) | fuellt **das v26-Fenster** (`PREREG_v26_window.md` par.1) -- noch nicht erzeugt |

Zuschnitt des v23-Fensters ist seit 2026-08-25 festgelegt
(`PREREG_v23_window.md`): 29.450 Partien, davon 12.000 aus dem v22-Self-Play
(4.000 Sockel + 8.000 Schwarm `--value-only`) und 17.450 aus hv2 (6.550
rotieren aus). Beides ist seit 2026-08-31 ERLEDIGT: Rotation seed-gezogen
(20260920, `data/window_v23_hv2.txt`), Traeger-Manifest mit 380 Eintraegen
(`data/policy_carrier_manifest_v23.json`, `PREREG_v23_window.md` par.2a).
Dieser Absatz stand bis zum 2026-09-01 auf dem Stand vom 2026-08-30.

## Reservierte Namen fuer v26 (Generationswechsel 2026-09-09)

Die Erzeugung schreibt drei Klassen, benannt nach ihrem GENERATOR `v25-b01`
(`feedback_selfplay_naming_convention`): `selfplay_v25-b01-policy_*`,
`selfplay_v25-b01-value-tempc_*`, `selfplay_v25-b01-value-excursion_*`. Die Befehle stehen
woertlich in `PREREG_v26_window.md` par.7, die Seeds sind 20260911 / 20260912 / 20260913.

**Trainingsarme: `v26-b01` aufwaerts.** Weil die Spec bis v27 eingefroren ist
(`PREREG_v25_window.md` par.18), unterscheiden sich die Arme nur im Trainingsrezept, nicht
in Knoepfen -- ein Knopf-Suffix ist in v26 also nicht zu erwarten.

## Champion-Namen bleiben reine `vN-bXX` (Nutzer-Anweisung 2026-09-06, 20:40)

Der Champion vom 2026-09-04 hiess `v23-b01_k3p10` (Netz plus Knopf-Suffix), und die
Promotion vom 2026-09-06 hat das Muster als `v24-b06_k3p10` fortgeschrieben. Nutzer,
woertlich: *"Bleib bei reinem vN-bXX."* Ab jetzt:

* **Modell-, Spec- und Artefaktnamen tragen KEINEN Knopf-Suffix.** Der Champion heisst
  `v24-b06`; seine Such-Knoepfe stehen in `models/v24-b06.spec.json`, nirgends im Namen.
  `models/champion.txt` traegt den reinen Namen.
* **Elo-Knoten duerfen einen Knopf-Zusatz tragen**, weil das Register Knoten als
  `Name@Sims` fuehrt und dasselbe Netz mit und ohne Knopf zwei verschieden starke Spieler
  sind (b06: 1261 ohne, 1309 mit K3-P). Der Zusatz ist eine Messgroesse des Registers,
  kein Name des Netzes; die `knobs`-Spalte traegt die Spec.
* `_best` / `_brierbest` sind Checkpoint-Auswahlen von train.py (Rezeptbestandteil
  `--select-by-brier`), keine Knopf-Suffixe; das Champion-Modell `alphazero_<name>.onnx`
  ist die gewaehlte Auswahl (fuer v24-b06: `_brierbest`, Epoche 4).

## v28 (reserviert 2026-09-10, Generationswechsel Schritt 6)

Self-Play-Klassen nach dem Generator: `selfplay_v27-b01-policy_*`, `-value-tempc_*`,
`-value-excursion_*` (Seeds 20260917 / 20260918 / 20260919, `PREREG_v28_window.md` par.5).
Trainingsarme: **`v28-b01`** (Rezept unveraendert, Warmstart `v27-b01_brierbest`, Seed 20260937)
und **`v28-b02`** (Variante B: Merkmale aus dem Record-Feld `dome_pool_view`, sonst wie b01,
gleicher Seed). Weitere Arme ab `v28-b03` nur mit eigener Registrierung. Kein Knopf-Suffix
im Namen (Regel oben).
