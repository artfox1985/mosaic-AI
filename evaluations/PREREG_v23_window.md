<!-- STATUS: OFFEN | Frage: Wie wird das v23-Trainingsfenster zugeschnitten, wenn zum ersten Mal ein HEURISTIK-Lehrerkorpus und ein NETZ-Korpus in dasselbe Fenster sollen? | Beleg: ZUSCHNITT FESTGELEGT (Nutzer 2026-08-25), nichts erzeugt -- das v22-Netz existiert noch nicht. Form 29.450 Partien wie das alte v22-Design: Policy-Klasse 5.800, Value-Klasse 23.650. NEU ist die Besetzung: der Neu-Anteil kommt aus dem v22-Self-Play (4.000 Sockel + 8.000 Schwarm), ALLE aelteren Plaetze aus dem hv2-Lehrerkorpus (17.450 von 24.000, 6.550 rotieren aus). DARAUS FOLGT der Umfang des v22-Self-Play: 12.000 Partien. Drei Punkte sind benannt und nicht geloest: (1) G-1 und G-2 kommen aus DEMSELBEN Korpus, die Generationenstruktur ist also Platzhalter, keine Aera-Streuung; (2) RAM 5,02 Mio Zustaende ~30,1 GB gegen 32 GB Grenze, kein Spielraum; (3) die 1.800 hv2-Partien der POLICY-Klasse tragen auf 61,8 Prozent ihrer Draftingzuege policy_target_valid=false -- ihre Policy-Ausbeute haengt an der Traegerfrage aus PREREG_v22_window.md par.4, die Preregs sind gemeinsam zu entscheiden. -->

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

**(2) Der Cache liegt am Anschlag.** Gerechnet mit gemessenen Groessen --
Netz-Korpus 164,9 Records je Partie (`data/holdout/selfplay_hold_a_*`),
hv2 174,2 (gemessen am laufenden Korpus):

```
12.000 x 164,9  +  17.450 x 174,2  =  5,02 Mio Zustaende
bei ~6 KB je Zustand:  ~30,1 GB   (Grenze 32 GB)
```

Das ist zugleich genau die Tragfaehigkeitsgrenze, die die Fensterstrategie
seit 2026-08-06 nennt (~5 Mio Zustaende). **Kein Spielraum.** Wer einen Posten
vergroessert, muss einen anderen verkleinern.

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

## par.4 Wecker: was VOR dem v22-Self-Play fallen muss

Der Lauf, der die 12.000 Partien erzeugt, ist der Zeitpunkt, an dem folgende
Entscheide nicht mehr nachziehbar sind (Policy-Ziele = Besuchsverteilung):

* `MOSAIC_IMPLICIT_MINIMAX_A` -- `PREREG_implicit_minimax_backup.md` par.3a;
  die Gating-Messung gehoert VOR diesen Start.
* Risikosensitive Blatt-Utility Stufe A1 --
  `PREREG_risk_sensitive_leaf_utility.md` par.5a; label-neutral ist sie nur
  gegenueber HEURISTISCHER Erzeugung.
* `MOSAIC_STACK_DRAW_RESEARCH` -- `PREREG_chance_nodes.md`
  Entscheidungsregel 4, bisher ZWEIMAL nicht erfolgt.
* `--seed-positions` -- `PREREG_start_position_seeding.md` par.5; im
  NETZ-Pfad bereits vorhanden, also hier ohne Bauarbeit einsetzbar.
* Bootstrap-Horizont -- ENTSCHIEDEN auf 2
  (`PREREG_bootstrap_horizon.md` par.9f).
* `--rtv` (Default aus), `--pcr-full-prob` (Default aus), `--sims`,
  `--c-puct`, `--no-root-noise`, `--tau-argmax-from-move`,
  `MOSAIC_WERTUNG_STREUUNG_MAX`.

Diese Liste stammt aus der Knopf-Registry und den Preregs. Sie ist KEIN
vollstaendiger Audit der Erzeugungs-Knoepfe -- wer den Lauf startet, geht sie
durch und ergaenzt, was fehlt.
