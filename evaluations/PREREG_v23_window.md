<!-- STATUS: OFFEN | Frage: Wie wird das v23-Trainingsfenster zugeschnitten, wenn zum ersten Mal ein HEURISTIK-Lehrerkorpus und ein NETZ-Korpus in dasselbe Fenster sollen? | Beleg: ZUSCHNITT FESTGELEGT (Nutzer 2026-08-25), nichts erzeugt -- das v22-Netz existiert noch nicht. Form 29.450 Partien, neu besetzt aus v22-Self-Play und hv2-Lehrerkorpus; daraus folgt der Umfang des v22-Self-Play: 12.000 Partien (par.1/par.2). RAM unkritisch und Traegerfrage auf ARM B entschieden; OFFEN ist nur der TRAEGER-MANIFEST-GENERATOR, es gibt Leser aber kein schreibendes Werkzeug (par.3). -->

# Vorregistrierung: v23-Fenster

**Angelegt 2026-08-25**, Zuschnitt vom Nutzer festgelegt. Das v22-Netz gibt es
noch nicht; dieses Dokument legt fest, was sein Self-Play liefern muss.

## par.1 Der Zuschnitt

**Value-Klasse (23.650)**

| Posten | Quelle | Partien |
| --- | --- | --- |
| Schwarm NEU | `v22` (Self-Play des v22-Champions, `--value-only`) | 8.000 |
| Schwarm G-1 | `hv2`, policy-maskiert | 8.000 |
| Schwarm G-2 | `hv2`, policy-maskiert | 1.450 |
| Sockel-Rest G-1 | `hv2`, policy-maskiert | 2.650 |
| Sockel-Rest G-2 | `hv2`, policy-maskiert | 3.550 |

**Policy-Klasse (5.800)**

| Posten | Quelle | Partien |
| --- | --- | --- |
| Sockel NEU | `v22` (Self-Play des v22-Champions) | 4.000 |
| Sockel G-1 | `hv2`, policy-aktiv | 1.350 |
| Sockel G-2 | `hv2`, policy-aktiv | 450 |

**Summe 29.450** -- dieselbe Form wie das alte v22-Design (Policy 5.800,
Value 23.650), neu besetzt.

## par.2 Was daraus folgt

**Der v22-Self-Play-Lauf muss 12.000 Partien liefern:** 4.000 Sockel
(policy-aktiv, Voll-Such-Sims) plus 8.000 Schwarm (`--value-only`, kleine
Sims). Beide Klassen sind im NETZ-Modus verfuegbar -- anders als bei hv2, wo
`--value-only` nicht existiert.

**Aus hv2 werden 17.450 der 24.000 Partien gezogen; 6.550 rotieren aus.**
Welche 6.550, ist offen und sollte seed-bestimmt und im Manifest festgehalten
werden, nicht "die letzten Dateien" -- sonst ist die Auswahl eine
Reihenfolge-Artefakt-Falle wie das "erste N je Datei" vom selben Tag.

## par.3 Drei Punkte, die benannt gehoeren -- keiner ist geloest

**(1) G-1 und G-2 kommen aus DEMSELBEN Korpus.** Im alten Schema waren das
echte Generationen mit verschiedenen Erzeugern (v20, v19). Hier fuellen beide
Plaetze aus hv2. Die Generationenstruktur ist damit ein PLATZHALTER, der die
Form haelt -- sie liefert keine Aera-Streuung. Das ist eine bewusste
Uebergangsloesung, aber sie darf spaeter nicht als Generationen-Vielfalt
gelesen werden. Ab v24 stehen wieder zwei echte Netz-Generationen zur
Verfuegung.

**(2) Der Cache passt bequem -- die ~6-KB-Zahl war veraltet.**

**BERICHTIGUNG 2026-08-25, am selben Tag:** die erste Fassung dieses Absatzes
rechnete mit "~6 KB je Zustand" aus der Fensterstrategie vom 2026-08-06 und
kam auf ~30,1 GB, also an den Anschlag. Die Zahl stammt vom Tag VOR dem
Bitpacking (v21, 2026-08-07: planes 2.736 B -> 342 B, masks 406 B -> 51 B).

**Gemessen am echten Cache** (`hv2`-Ausschnitt, 47.046 Samples, Felder
aufsummiert):

| Posten | Groesse je Zustand |
| --- | --- |
| `states` (714 x float16) | 1.428 B |
| `policies` (406 x float16) | 812 B |
| `ownership` (72 x int8) | 72 B |
| `masks_packed` (51 x uint8) | 51 B |
| uebrige 16 Felder | ~101 B |
| **Summe flacher Cache** | **2.464 B** |
| `planes_packed` (342 B, NUR im 2D-Fenster, ZUSAETZLICH zu `states`) | 342 B |
| **2D-Fenster gesamt** | **2.806 B** |

```
5,02 Mio Zustaende x 2.806 B = 14,1 GB   (nicht 30,1 GB)
```

Gegen 34,3 GB Maschinen-RAM (neural_net.py:1207). **Der Schwarm muss NICHT
verkleinert werden.**

**Auslagern ist gemessen und verworfen.** Der Schalter existiert
(`MOSAIC_PLANES_LAZY=1`, lazy Pro-Index-HDF5), ist aber **rund 400.000-mal
langsamer je Sample** -- 205 ms gegen 0,5 Mikrosekunden. Bei Batch 256 waeren
das ~52 s je Batch fuer reine Planes-I/O; drei vermeintliche "stille
Abstuerze" beim ersten 2D-Sweep waren genau das (neural_net.py:1198-1210).
Nicht wieder vorschlagen ohne neues Regime.

**Falls es doch je knapp wird**, in dieser Reihenfolge:

* `policies` (812 B, 29 Prozent) ist der aussichtsreichste Posten: der volle
  406er-Vektor ist duenn besetzt (gemessen am hv2-Korpus: im Mittel 1,7
  Aktionen ueber 10 Prozent, 49 Prozent der Ziele auf einer Aktion
  konzentriert, und 61,8 Prozent der Draftingzuege sind ohnehin one-hot). Eine
  sparse Ablage waere aber VERLUSTBEHAFTET fuer den KL-Verlust -- das Muster
  existiert bereits bei `ranking_action_ids`/`ranking_child_q` (TOPK 8).
  Ungeprueft, nicht gebaut.
* `states` (1.428 B, 51 Prozent) ist NICHT streichbar: `Mosaic2DNet.forward`
  nimmt `x_planes` UND `x_flat` und fusioniert beide Zweige -- der flache
  Vektor ist eine lebende Eingabe, kein Altlast-Feld.
* Erst danach: den Schwarm verkleinern.

**(3) Die Policy-Ausbeute der hv2-Plaetze haengt an der Traegerfrage.** Die
1.800 hv2-Partien der Policy-Klasse tragen auf **61,8 Prozent** ihrer
Draftingzuege `policy_target_valid=false` (v2-Vorzug). Wird die Flagge
geachtet, liefern sie rund 38 Prozent ihres nominellen Policy-Materials:

| | nominell | bei geachteter Flagge |
| --- | --- | --- |
| Policy-Klasse gesamt | 5.800 | ~4.690 Partien-Aequivalente |

Das liegt noch im konservativen Sockel-Korridor (4.000-5.000), aber am
unteren Rand. **Dieses Fenster und `PREREG_v22_window.md` par.4 sind deshalb
gemeinsam zu entscheiden**, nicht nacheinander -- der Traeger-Entscheid
veraendert, wieviel Policy dieses Fenster wirklich enthaelt.

**NACHTRAG 2026-08-27: der gemeinsame Entscheid IST gefallen -- ARM B.** v22
faehrt mit `MOSAIC_IGNORE_POLICY_TARGET_VALID=1`, die Flagge wird also
IGNORIERT (`PREREG_v22_window.md` par.4b und par.4e; die Konfiguration steht
in par.3b.2 der Lehrer-Prereg als w1-Arm). Damit gilt fuer dieses Fenster:

* **Die Tabelle oben beschreibt den verworfenen Fall.** Unter Arm B liefern
  die 1.800 hv2-Partien der Policy-Klasse ihr VOLLES nominelles Material, die
  Policy-Klasse bleibt bei 5.800 -- die "~4.690 Partien-Aequivalente" sind
  keine Planungsgroesse mehr.
* **Einschraenkung, die dazugehoert:** der Entscheid ist ein RICHTUNGSENTSCHEID
  mit n=40 auf einem Viertelkorpus (par.4b dort sagt das ausdruecklich), kein
  Gating. Er legt fest, womit trainiert wird; er belegt nicht, dass Arm B
  staerker ist.
* **Offen bleibt der TRAEGER-MANIFEST-GENERATOR**, und das ist ein anderer
  Punkt als die Traegerfrage: `neural_net.py` und `train_manifest.py` LESEN
  ein Traeger-Manifest, geschrieben wird es nirgends. Die seed-bestimmte
  Auswahl der 1.800 policy-aktiven hv2-Partien aus par.1 ist ohne dieses
  Werkzeug nicht ausfuehrbar (STATUS-Abschnitt "TRAEGER-MANIFESTE").

## par.4 Wecker: was VOR dem v22-Self-Play fallen muss

Der Lauf, der die 12.000 Partien erzeugt, ist der Zeitpunkt, an dem folgende
Entscheide nicht mehr nachziehbar sind (Policy-Ziele = Besuchsverteilung):

* **Spalten-Abnahme-Tor** aus `PREREG_heuristic_v2_long_rows.md` par.3b.2 muss
  BESTANDEN sein, bevor dieser Lauf startet (verfehlt = kein Start, das
  Fenster bliebe unbesetzt).
* `MOSAIC_IMPLICIT_MINIMAX_A` -- `PREREG_implicit_minimax_backup.md` par.3a;
  die Gating-Messung gehoert VOR diesen Start.
* Risikosensitive Blatt-Utility Stufe A1 --
  `PREREG_risk_sensitive_leaf_utility.md` par.5a; label-neutral ist sie nur
  gegenueber HEURISTISCHER Erzeugung.
* `MOSAIC_STACK_DRAW_RESEARCH` -- `PREREG_chance_nodes.md`
  Entscheidungsregel 4, bisher ZWEIMAL nicht erfolgt.
* `--seed-positions` -- `PREREG_start_position_seeding.md` par.5; im
  NETZ-Pfad bereits vorhanden, also hier ohne Bauarbeit einsetzbar.
* **Startkuppel-Streuung** -- `PREREG_start_dome_choice.md` par.5/par.7
  (ergaenzt 2026-08-27). Der Startslot steckt in den PARTIEN und in den
  POLICY-ZIELEN (heute ein one-hot auf `choose_start_placement`), ist also nur
  am Generierungsstart entscheidbar. Fuer den hv2-Korpus war es zu spaet;
  fuer diesen Lauf ist es offen. Stufe 0 dort (netzfrei, gepaart) muesste
  davor laufen, sonst faellt der Entscheid per Default auf "Handheuristik".
* **`MOSAIC_STACK_DRAW_RESERVATION`** -- `PREREG_stack_draw_reservation_rule.md`
  par.5e (ergaenzt 2026-08-27). Der Knopf sitzt in `apply_chosen_action`
  (`resolve_and_apply_stack_draw`, self_play.rs:500) und wirkt damit in JEDEM
  Self-Play. **Default AUS ist entschieden** und bleibt es; die beiden
  Wiedervorlage-Bedingungen aus par.5e (Eichung von `V` an einem Punkt
  AUSSERHALB der v22-Verteilung, und ein EINSEITIGER Knopf) sind ungebaut --
  ohne sie ist der Arm nicht fahrbar, mit ihnen waere es ein Erzeugungs-Knopf.
* **`ROUND_TRANSITION_SAMPLING`** -- `PREREG_round_transition_search_sampling.md`
  (ergaenzt 2026-08-27). Ein Such-Eingriff am Blattwert des
  Rundenuebergangs; er verschiebt die Wurzel-Besuchsverteilung und damit die
  Policy-Ziele, gehoert also auf diese Liste. Reihenfolge dort ist bindend:
  ZUERST das Kostentor (Schwelle 25 Prozent Wanduhr-Aufschlag), Staerke
  danach -- der Schalter steht heute auf `false` (net_mcts.rs:84).
* **Vollendbarkeits-FILTER im Netz-Spieler** (ergaenzt 2026-08-27 aus dem
  Recherche-Abgleich). Quelle:
  `RESEARCH_heuristic_methodology_external_2026-08-25.md` Abschnitt 4.5 plus
  Uebernahme-Kandidat 1 -- Zuege in nachweislich UNVOLLENDBARE Zielzellen in
  der SUCHE ausschliessen oder abwerten. Das ist die FILTER-Haelfte von K1: auf
  der Heuristik-Seite ist sie tragend (`cell_is_completable` schneidet
  unerreichbare Zielzellen), im NETZ ist sie nie gebaut worden. Das
  Erreichbarkeits-Praedikat liegt seit Commit `29fb1f1` als Netz-Eingabe vor,
  der Filter waere also kein Neubau der Relaxation, sondern ihre Anwendung im
  Aktionsraum. **Warum auf DIESE Liste:** ein Aktionsfilter verschiebt die
  Wurzel-Besuchsverteilung und damit die Policy-Ziele -- der Entscheid faellt
  VOR dem v22-Self-Play, danach nicht mehr. Stand: UNGEBAUT, Default aus,
  Paritaets-Gate Pflicht (Champion bitgleich bei ausgeschaltetem Knopf).
* Bootstrap-Horizont -- ENTSCHIEDEN auf 2
  (`PREREG_bootstrap_horizon.md` par.9f). Die Wiederaufnahme-Bedingung ist
  seit dem hv2-Korpus erfuellt, die Wiederaufnahme aber hinter par.3b.4 der
  Lehrer-Prereg zurueckgestellt (dort par.10).
* `--rtv` (Default aus), `--pcr-full-prob` (Default aus), `--sims`,
  `--c-puct`, `--no-root-noise`, `--tau-argmax-from-move`,
  `MOSAIC_WERTUNG_STREUUNG_MAX`.

Diese Liste stammt aus der Knopf-Registry und den Preregs. Sie ist KEIN
vollstaendiger Audit der Erzeugungs-Knoepfe -- wer den Lauf startet, geht sie
durch und ergaenzt, was fehlt.

## par.4a2 Wecker VOR dem v23-TRAINING: Arm K (Bootstrap-Kohaerenz)

Nutzer-Entscheid 2026-08-29 ("takte es dort ein; wir kuemmern uns fuer v22
primaer darum, dass die Spalten gebaut werden"): der offene Arm K
(`PREREG_heuristic_v2_long_rows.md` par.3b.3, Registrierung (a) --
Summen-Normierung oder affine Versatz-Korrektur des globalen
Bootstrap-Optimismus ~+0,05 je Seite, als reine Label-Transformation im
WDL-Zweig, Cache-Key-Komponente Pflicht) wird NICHT im v22-Zyklus
entschieden, sondern faellig VOR dem v23-Training -- oder frueher, sobald
ein Konsument Absolutwerte des Value-Kopfs liest (risikosensitive
Blatt-Utility, Kalibrierungs-Schwellen). Grund der Platzierung: die
Transformation wirkt beim Labeln, und ein unkorrigierter Versatz vererbt
sich per Bootstrap in die naechste Generation.

## par.4b Wecker NACH dem v23-Training

Gegenstueck zu par.4 fuer die TRAININGS-Seite dieses Fensters: der folgende
Punkt wird nicht am Self-Play-Start faellig, sondern nach dem Training des
ersten Ownership-Kopfs auf den v22-EIGENPARTIEN (= v23).

* **Erreichbarkeits-Nachpruefung** -- eigene Prereg
  `PREREG_v23_reachability_recheck.md` (Nutzer-Entscheid 2026-08-28,
  hervorgegangen aus `PREREG_reachability_target.md` par.17): ein
  Eintretens-Kopf auf Eigenpartien spiegelt wieder die eigene Politik
  (Selbsterfuellungs-Falle). NACH dem v23-Training dort Stufe 0 fahren
  (Karten-Diagnose gegen das Vorrats-Praedikat, trainingsfrei -- braucht
  den trainierten Kopf); nur bei substanzieller Unterschaetzung folgt
  Stufe 1 (Zielwechsel am par.3b.6-Instrument der Lehrer-Prereg).
