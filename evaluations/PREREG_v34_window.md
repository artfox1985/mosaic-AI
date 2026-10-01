<!-- STATUS: OFFEN | Frage: Wie wird das v34-Fenster zugeschnitten und erzeugt (letzte Generation dieser Architektur), und traegt ein Arm? | Beleg: ENTWURF 2026-09-27. ENTSCHIEDEN (Nutzer): Zuschnitt in b04-Form (par.1), dritte Klasse Weg C mit Huellenknopf, Generator v33-b01 (par.5). Sockel bleibt bei 100 Sims. Stufenregel gilt (par.2). E1 an, Runde 5 per Netz (par.5). Smoke-Lauf gruen nach Waechter-Fix je Klasse (par.7a); Kostentor: Runde 5 per Netz +11,5 % je Partie, Sockel 2,73 s je Partie (par.8a). Nichts erzeugt. -->

# Vorregistrierung: das v34-Fenster

**Angelegt 2026-09-27 als ENTWURF**, vor dem Generationswechsel v33 -> v34
(`/mosaic-generation-turnover`). **v34 ist die letzte Generation dieser Such- und Netzarchitektur**
(Nutzer 2026-09-27: *"Mir scheint wir kommen mit unserer aktuellen Suche und Netz Architektur an die
Decke. Somit werden wir v34 noch fahren und uns dann ueberlegen welche alternativen Ansaetze es
gibt"*). Sie faehrt das Paket der v33-Generation (par.3); danach werden alternative Ansaetze
geprueft, keine v35 im selben Rahmen.

Stand v33 (`PREREG_v33_window.md`): `v33-b01` hat Tor 1 formal getragen (420:380 = 52,50 %, Block-z
+1,41, par.10), die Fensterarme b02/b03/b04 sind davon nicht unterscheidbar (par.6d), `v33-b02`
verfehlt Tor 1 gegen den Champion (405:395, par.6e). **Keine Promotion** (Nutzer 2026-09-27),
Champion bleibt `v32-b01`.

## par.1 ZUSCHNITT: b04-Form (ENTSCHIEDEN 2026-09-27)

**Nutzer:** *"Ok, dann Takte es so ein"* auf den Vorschlag, den Zuschnitt von `v33-b04` zu
uebernehmen (`PREREG_v33_window.md` par.6c/par.6d): **die ganze v34-Erzeugung plus aus aelteren
Generationen NUR die Policy-Traeger des Traeger-Manifests**; das policy-maskierte Altmaterial
(alte Sockel-Nichttraeger, alte Schwarm-Klassen) faellt weg. Begruendung: vier Arme
ununterscheidbar, b04 ist das kleinste Fenster (1.381 statt 2.947 Dateien bei b01; Ersparnis an
Bloecken, Monolith und Training UNGEMESSEN, die b04-Trainingszeit lief unter Nebenlast), und das
v34-Paket wird nicht durch Altmaterial ohne die neuen Knoepfe verduennt.

| Generation | Klasse | ins Fenster | Policy-Ziel |
| --- | --- | --- | --- |
| G (v34-Erzeugung, neu) | policy | alle (Soll 400) | ja |
| G | value-wegc (Weg C, Huellenknopf an, par.5 Punkt 2) | alle (Soll 400) | nein |
| G | value-excursion (KL-Abzweig) | alle (Soll rund 400) | nein |
| G-1 (v33-Erzeugung, `v32-b01-*`) | policy | NUR Traeger | ja |
| G-2 (v32-Erzeugung, `v31-b01-*`) | policy | NUR Traeger | ja |

Traeger-Zahlen aus `tools/generate_carrier_manifest.py --pick` -> `data/policy_carrier_manifest_v34.json`;
v33 hatte 135 aus G-1 und 45 aus G-2 (`PREREG_v33_window.md` par.1), fuer v34 UNGEPRUEFT bis zum
Lauf des Werkzeugs. Die Kette bricht ab, wenn das Fenster Nicht-Traeger aus G-1/G-2 enthaelt.

**Trainings-Seed 20260961** (Vierer-Schritt, `docs/generation_loop.md`: v33 20260957), alle Arme
derselbe. **Val-Pool:** nur Dateien der G-Erzeugung, Muster nach dem Versionsnamen (par.5 Punkt 1).

## par.2 TORE

Wie `PREREG_v33_window.md` par.2: **Tor 1** gegen den besten Stand der eigenen Linie (den
Generator), Seeds 20261600/20261601 a 200 Paare, Blockgroesse 5, *"z >= +1,96 oder gepoolt >= 52,5
Prozent ohne Gegenbefund"*, Block-z ueber `tools/gating_block_z.py`. **Tor 2a** `sp_voll` des neuen
Sockels gegen den v33-Sockel (Nicht-Unterlegenheit), **Tor 2b** volle Spalten im Tor-1-Lauf.
**Champion-Kante** gegen `v32-b01` berichtet (`docs/generation_loop.md`, Falle 1), falls der
Generator nicht der Champion ist. **Stufenregel gilt** (par.5 Punkt 4): loest GENAU EINER der beiden
Seeds einzeln Block-z >= +1,96 aus, laeuft Seed 20261602 mit identischen Einstellungen; Verdikt auf
dem gepoolten Block-z ueber alle gelaufenen Seeds, Kriterium unveraendert
(`PREREG_v33_window.md` par.2a).

## par.3 DAS PAKET: was sich gegenueber v33 aendert

| Aenderung | Quelle | Stand |
| --- | --- | --- |
| Fenster b04-Form | par.1 | entschieden |
| Ausflug zweigt nach Rundenprofil x Policy-Diskrepanz ab (`MOSAIC_EXCURSION_KL_WEIGHT` 1), Record-Feld `branch_kl` | `PREREG_targeted_branching.md` par.7 | Quelltext gebaut, NICHT kompiliert |
| Ausflug mischt die verdeckte Welt am Abzweig neu (`excursion_reshuffle`) | Code-Review #14 | gebaut, Wheel f27f8ff6 |
| Spiegelknopf, Stichentscheide 50:50 (`tie_mirror_p` 0,5) | `PREREG_tie_mirror.md` | gebaut |
| getrennte Label-RNG (`label_rng_split`) | Code-Review #13 | gebaut |
| Einpass-Konsum in der Suche (`single_pass_other_val`) | `PREREG_evaluator_pretests.md` par.5b | **AN** (Nutzer 2026-10-01): A/B 415:385, z +1,04 (par.8d dort), Kostentor -39,4 % je Partie; Env `MOSAIC_SINGLE_PASS_OTHER_VAL=1` im Rezept, damit auch die Label-Pfade ihn lesen |
| Runde 5 per Netz statt Loeser (`r5_net_solver` 0) | `PREREG_r5_net_vs_solver.md` | **AN** (Nutzer 2026-10-01): A/B 495:305, z +10,17 (par.6a dort); Env `MOSAIC_R5_NET_SOLVER=0` im Rezept. R5-Policy-Ziele werden Besuchsverteilungen; das Label 4->5 (`exact_round5_outcome`) laeuft weiter ueber den Loeser |
| Trainings-Arm E2 (Margen-Schwellen am WDL-Logit) | `PREREG_evaluator_pretests.md` par.8a, STATUS 6.17 | Bau offen (rund ein halber Tag) |
| Trainings-Arm E4 (Angebots-Bedarfs-Abschnitt im Encoder, additiv) | `PREREG_evaluator_pretests.md` par.8c | Bau offen (1-2 Tage laut Recherche-Bericht) |

**Zuordnung, vorab benannt:** die Erzeugungs-Knoepfe fahren gemeinsam; ein Tor-1-Gewinn des
Grundarms ist dem Paket zuzuschreiben, keinem Einzelknopf. Einzeln lesbar sind nur die Trainings-Arme
E2/E4 gegen den Grundarm (gleiches Fenster, gleicher Seed) und die Offline-Pruefung des
KL-Abzweigs (`PREREG_targeted_branching.md` par.7a).

**Vor der Erzeugung zu pruefen (Record-Feld-Regel):** brauchen E2 oder E4 ein Merkmal, das NICHT
aus den heutigen Records rekonstruierbar ist, muss das Feld VOR der Erzeugung in die Records.
E2 liest Endstand/Marge (heute in den Records, `scores`, `scores_unclamped`), E4 rechnet aus dem
Zustand; beides UNGEPRUEFT, wird vor dem Start am Code geprueft.
**Geprueft 2026-09-27:** E2 braucht die Endmarge je Partie, die Records tragen `scores` und
`scores_unclamped` (`engine/src/self_play.rs:4954-4991`); E4 rechnet aus dem Record-Zustand, der
E4-Vortest lief genau so auf v33-Records (`PREREG_evaluator_pretests.md` par.5c, Einschraenkung:
Records mit offener Wahl rekonstruiert `json_to_state` nicht, par.5c). **Kein neues Record-Feld
vor der Erzeugung noetig**; die E4-Einschraenkung ist beim Encoder-Bau zu loesen (dort liegt der
Zustand, nicht das JSON, vor -- beim Bau pruefen).

## par.4 ABNAHMEN DER ERZEUGUNG (je Klasse)

* **Manifest-Diff** gegen die v33-Erzeugung (`manifest_v32-b01-*`): erwartet `model`, `seed`,
  `version`, `spec` (falls der Generator wechselt), `recipe`, die neuen `engine_config`-Schluessel
  (`tie_mirror_p`, `label_rng_split`, `excursion_reshuffle`, `excursion_kl_weight`, ggf.
  `single_pass_other_val`, `r5_net_solver`) und `mosaic_env`. Jede weitere Abweichung stoppt.
* **Waechter `expect_engine_config`** aus dem Rezept gegen die Chunk-Prozesse (gebaut, b00a9e09).
* **Smoke-Lauf** mit gesetzten Knoepfen vor dem Start (STATUS 3e).
* **Tor 0** je Klasse, **Tor 2a** am Sockel.
* **Spiegelknopf:** Anteil `tie_mirrored` je Klasse nahe 50 % (Binomial-CI ueberdeckt 0,5).
* **KL-Abzweig:** Abnahme nach `PREREG_targeted_branching.md` par.7 (Median der Werkzeug-KL am
  ersten Ausflug-Record ueber dem 75-%-Quantil aller Drafting-Stellen).

## par.5 OFFENE ENTSCHEIDE (vor dem Start, Nutzer)

1. **Generator: ENTSCHIEDEN 2026-09-27 `v33-b01`** (Nutzer: *"Generator is v33-b01"*). Rezept
   eingetragen: `models/alphazero_v33-b01_brierbest.onnx`, Spec `models/v33_generation.spec.json`
   (byte-gleiche Kopie von `v32_generation.spec.json`, sha256 `4a3f9db3...` beide geprueft),
   Versionen `v33-b01-<Klasse>`, Seeds 20260946 / 47 / 48. Vorlage war: nach `docs/generation_loop.md` ("Generator = bester Stand von N-1", Tor 1 ist das
   Ratschen-Tor, nicht das Champion-Tor) ist das **`v33-b01`**: es hat Tor 1 formal getragen, b02
   nicht, b03/b04 hatten keins. Die Nicht-Promotion betrifft den Champion, nicht den Generator.
   Alternative `v32-b01` (Champion): dann traegt die Erzeugung dieselben Versionsnamen wie die
   v33-Erzeugung (`v32-b01-policy` ...), Namenskonflikt, eigenes Muster noetig. **Vorschlag:
   `v33-b01`** (Versionen `v33-b01-<Klasse>`, Val-Pool `^selfplay_v33-b01-`).
2. **Schwarm-Klasse: ENTSCHIEDEN 2026-09-27** (Nutzer: *"Mach weg c (mit aktiviertem
   huellenknopf)"*): dritte Klasse ist **`value-wegc`** (Weg C: argmax-Spiel mit einer Abweichung
   an zufaelliger Stelle, value-only, wie `v33-b03`) statt `value-tempc-nohull`, **Huellenknopf
   AN** (Spec wie Sockel und Ausflug, `envelope_search_c` 1,0 in `models/v32_generation.spec.json:6`,
   geprueft 2026-09-27; beim Generatorwechsel die byte-gleiche Spec unter dem Generatornamen).
   Gruende: die Vielfaltssonde fand fuer den temperierten Schwarm nur +1,1 %
   (`PREREG_v33_window.md` par.9, "falscher Ort"); Tor 0 0,598 volle Spalten je Seite gegen 0,974
   bei Weg C (b03); Weg C ist die Vergleichsbasis der KL-Abnahme (`PREREG_targeted_branching.md`
   par.4/par.7). **Vorbehalt:** als ERSATZ der dritten Klasse ist Weg C ungemessen; b03 hat ihn nur
   ZUSAETZLICH ins Fenster gelegt (ohne messbaren Beitrag).
3. **E1 / R5 in der Erzeugung: ENTSCHIEDEN 2026-10-01** (Nutzer: *"E1 an, Runde 5 mit Netz, Seed 2 nicht
   wiederholen"*): beide an, ueber das `env` des Rezepts (`models/v34.recipe.json`), Waechter
   `expect_engine_config` single_pass_other_val true / r5_net_solver false. **Vor dem Start:** Kostentor
   der Erzeugung mit beiden Knoepfen (Muster E1-Kostentor, je 100 Partien), weil die Netzsuche in
   Runde 5 bei 100 Sims ungemessen kostet.
4. **Stufenregel fuer Tor 1: ENTSCHIEDEN 2026-09-27, gilt auch fuer v34** (Nutzer: *"Ja gilt"*),
   Wortlaut par.2. Vorlage war: (dritter Seed bei Widerspruch): galt fuer v33, ob sie Pflicht wird,
   sollte nach dem Einsatz entschieden werden (`PREREG_v33_window.md` par.2a). Bei v33 loeste sie
   nicht aus.
5. **Warmstart** der Arme: vom Generator (v33-Praxis: warm vom Generator `v32-b01`).
6. **Sims des Sockels** (Nutzer-Frage 2026-09-27: *"ob wir mehr sims fuer den sockel andenken
   sollen"*). Heute 100. Bestand, am Kopf der Preregs gelesen 2026-09-27:
   * `PREREG_search_depth_column_optimum.md` par.8e (2026-09-13, Champion v28-b02): Staerke
     saettigt bei 400 (@100 45:105, @200 53:97, @600 74:76 jeweils gegen @400); der KORPUS verliert
     mit der Tiefe monoton volle Spalten (1,098 / 0,958 / 0,895 / 0,820 je Seite bei 100 / 200 /
     400 / 600, @100 gegen @400 z +3,74), nur ueber die Vollendung. Betriebspunkt 100 blieb;
     Sockel @100 4,40 h gegen @400 8,29 h.
   * `PREREG_reanalyze_label_depth.md` par.A5 (2026-09-03, v23): 200 Policy-Dateien mit @400
     nachgelabelt, Arena 75:85 (p 0,55), argmax-Spalten 0,445 gegen 0,515, Value-Kopf unbewegt.
   Die Befunde stammen von v28 bzw. v23, also sechs bzw. elf Generationen zurueck; ob sie fuer
   v33-b01 noch gelten, ist UNGEMESSEN.
   **ENTSCHIEDEN 2026-09-27: 100 Sims wie bisher** (Nutzer: *"Lass ihn mal bei 100 sims"*), kein
   Sims-Arm.

## par.6 REZEPT

Erzeugung: `models/v34.recipe.json` (Rezeptdatei, `docs/working_rules.md`), Aufruf je Klasse
`python -X utf8 -u self_play.py --recipe models/v34.recipe.json --class <klasse>`, als Kette
`tools/night_v34_generate.sh` (noch zu schreiben). Platzhalter bis zum Entscheid par.5: `model`,
je Klasse `version` und `seed` (Vorschlag 20260946 / 47 / 48 im Vierer-Schritt nach v33 42 / 43 /
44), `excursion_kl_weight` 1 in der Ausflug-Klasse. 3 x 4.000 Partien, 100 Sims, 11 Threads wie v33.

Training: Referenz-Manifest des v33-Grundarms (`models/manifest_train_v33-b01_*.json`), Rezept
unveraendert (warm, 12 Epochen, lr 5e-5 cosine, WDL, nortv, lambda 0,7, `--select-by-brier`);
erwartete Manifest-Abweichungen `load`, `name`, `file_list`, `cache_file`, `seed`, `val_pool`.

## par.7 VORPRUEFUNGEN VOR DEM START

### par.7a Smoke-Lauf des Rezepts (2026-10-01, exklusiv, Wheel 1.1.0)

`MOSAIC_DATA_DIR=data/probe_v34smoke python -X utf8 -u self_play.py --recipe models/v34.recipe.json
--class <klasse> --games 20 --version smoke-v34-<klasse>`, je Klasse nacheinander.

**Erster Versuch ROT, Rezeptfehler gefunden:** `expect_engine_config` war rezeptweit und trug
`excursion_kl_weight: 1`, das nur die Ausflug-Klasse setzt; der Waechter brach `policy` vor dem
ersten Spiel ab (`excursion_kl_weight: erwartet 1, Engine meldet 0`), ohne Spur in `data/`.
**Behoben:** Waechter-Erwartung je Klasse (`classes.<name>.expect_engine_config` ergaenzt bzw.
ueberschreibt die rezeptweite, `tools/recipe_config.py::expected_engine_config`, eingehaengt in
`self_play.py`, `train.py`, `tools/paired_gating.py`; 4 neue Tests, Rezept-Tests 104 gruen). Im
Rezept erwartet `value-excursion` 1, `policy` und `value-wegc` erwarten 0 (faengt auch ein
Env-Leck). Rezept-sha256 danach `5ca42e9b1592...`.

**Zweiter Versuch GRUEN** (Grundmenge je Klasse 20 angeforderte Partien, Einheit Partie):

| Klasse | Waechter | Partien (Haupt / Ausflug) | Records | `tie_mirrored` True / False (Partien) | `branch_kl` | s je Partie (n = 20) |
| --- | --- | --- | --- | --- | --- | --- |
| policy | gruen, 6 Knoepfe | 20 / 0 | 3.953 | 11 / 9 | auf 0 Records | 2,54 |
| value-wegc | gruen, 6 Knoepfe | 20 / 0 | 3.979 | 8 / 12 | auf 0 Records | 2,61 |
| value-excursion | gruen, 6 Knoepfe | 10 / 10 | 3.275 | 6 / 14 | auf genau 10 Records = erster Record jedes Ausflugs, Werte 0,09-3,92 | 1,90 |

Manifest je Klasse: `recipe` mit `path`, `sha256`, `class`, `content`, `overrides` (nur `games` und
`version`, wie gewollt), `engine_config_check` (Abweichungen leer), `mosaic_env`
(`MOSAIC_R5_NET_SOLVER=0`, `MOSAIC_SINGLE_PASS_OTHER_VAL=1`, `MOSAIC_STACK_DRAW_RESEARCH=1`, dazu
`MOSAIC_DATA_DIR` des Smokes); `engine_config` meldet die sechs erwarteten Werte. `tie_mirrored` ist
je Partie einheitlich und in allen 60 Partien gesetzt (25 True). **Keine Planungsgroesse:** n = 20
je Klasse, die Ausflug-Klasse zaehlt Ausfluege als Partien mit. Die Smoke-Dateien liegen in
`data/probe_v34smoke` (Loeschliste des Generationswechsels).

## par.8 KOSTEN

### par.8a Kostentor der Erzeugung, GEMESSEN 2026-10-01 (par.5 Punkt 3, exklusiv, Wheel 1.1.0)

`bash tools/v34_cost_gate.sh`: Generator `v33-b01`, Spec `v33_generation.spec.json`, Flags der
Klasse `policy` aus dem Rezept (ohne `--recipe`, damit der Loeser-Arm nicht am Waechter scheitert),
E1 in BEIDEN Armen an, Seed 20261698, 11 Threads, 100 Sims. Grundmenge je Arm 100 Partien,
Einheit Sekunden Wanduhr je Partie (Manifest `laufzeit`, `data/probe_v34costgate`).

| Arm | `r5_net_solver` (engine_config) | Partien | Zuege | Wanduhr | s je Partie |
| --- | --- | --- | --- | --- | --- |
| Loeser in Runde 5 | True | 100 | 19.840 | 244,6 s | 2,446 |
| Netz in Runde 5 (v34-Rezept) | False | 100 | 19.907 | 272,7 s | 2,727 |

**Ergebnis: Runde 5 per Netz kostet in der Sockel-Einstellung +11,5 % je Partie** (+0,28 s). Ein
Lauf je Arm, keine Streuung gemessen. Netzzeit je Runde-5-Entscheidung @100 als HERLEITUNG:
28,1 s Mehr-Wanduhr x 11 Threads auf 3.223 Records mit Runde 5 im Netz-Arm (zaehlt alle
Record-Arten der Runde) ergibt rund 0,1 s Faden-Zeit mehr je Runde-5-Record; nicht je echter
Entscheidung gemessen (`PREREG_r5_net_vs_solver.md` par.6b).

**Planungszahl Erzeugung (HERLEITUNG):** v33 12,99 h; E1 -39,4 % (Kostentor v33, Sockel) und
R5-Netz +11,5 % (hier, Sockel) ergeben multiplikativ rund 12,99 x 0,606 x 1,115 = 8,8 h, WENN
beide Faktoren fuer alle drei Klassen gelten (UNGEPRUEFT fuer Weg C und Ausflug). Direkter
Anhalt: der Sockel mit beiden Knoepfen lief hier 2,73 s je Partie, 4.000 Partien also rund
3,0 h fuer die Sockel-Klasse.

### par.8b Herleitungen vor der Messung (Stand 2026-09-27)


* Erzeugung v33: 12,99 h fuer 3 x 4.000 Partien (`PREREG_v33_window.md` par.9). Mit E1 rund
  7,9 h, WENN die -39,4 % des Kostentors (gemessen nur an der Sockel-Einstellung, je 100 Partien)
  fuer alle Klassen gelten; UNGEPRUEFT fuer Weg C und Ausflug. Weg C lief bei b03 20:02-00:44 fuer
  4.000 Partien, 10 Threads, UNTER NEBENLAST (keine Planungsgroesse).
* Tor 1 rund 3,4 h (2 x 40 Bloecke a rund 150 s).
