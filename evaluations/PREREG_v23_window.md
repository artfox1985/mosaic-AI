<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird das v23-Trainingsfenster zugeschnitten, wenn zum ersten Mal ein HEURISTIK-Lehrerkorpus und ein NETZ-Korpus in dasselbe Fenster sollen? | Beleg: GEBAUT UND GEFAHREN. 29.450 Partien wie in par.1 (17.450 hv2 + 12.000 v22-b05, alle drei Laeufe @100 Sims; par.4c berichtigt 2026-09-01), Auswahl seed-gezogen (par.2a), Traeger-Manifest 380 Eintraege. Alle vier Tore bestanden (par.2b-2e), Champion-Kante Augenhoehe ohne Promotion (par.2f). Alle Arme gemessen (b02/b03/b05, par.2h), keiner belegt besser: b01 ist Generator fuer v24. -->

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
Welche 6.550, war offen und sollte seed-bestimmt festgehalten werden, nicht
"die letzten Dateien" -- sonst ist die Auswahl eine Reihenfolge-Artefakt-Falle
wie das "erste N je Datei" vom selben Tag.

**ENTSCHIEDEN UND AUSGEFUEHRT 2026-08-31 (Nutzer: "such dir per seed
zufaellig welche aus"):** `tools/generate_carrier_manifest.py --pattern
"selfplay_hv2_*.pkl" --n-files 1745 --seed 20260920 --list-out
data/window_v23_hv2.txt`. Die dokumentierte Regel des Werkzeugs ist
seed-zufaellig MIT zeitlicher Streuung (je Zeit-Stratum eine Datei); bei
1.745 aus 2.400 sind die Straten 1-2 Dateien breit, die Auswahl ist also
praktisch gleichverteilt und zugleich ueber die Erzeugungszeit gestreut.
**Determinismus gegengeprueft:** ein zweiter Lauf mit denselben Argumenten
liefert eine byte-gleiche Liste. 2.400 hv2-Dateien a 10 Partien = 24.000;
1.745 Dateien = 17.450 Partien, 655 Dateien = 6.550 rotieren aus -- die Zahlen
gehen glatt auf. Die Liste liegt in `data/` (ungetrackt); reproduzierbar ist
sie aus Regel plus Seed.

## par.2a FENSTER GEBAUT UND GEZAEHLT (2026-08-31)

Das Fenster steht als explizite Dateiliste `data/window_v23.txt`: **1.745
hv2-Dateien** (Seed 20260920) plus **600 v22-b05-Dateien** = 2.345 Dateien.
Vom Trainingslauf selbst nachgezaehlt und gegen par.1 geprueft:

| Praefix | Dateien | Partien | Policy-Traeger |
| --- | --- | --- | --- |
| hv2 | 1.745 | 17.450 | 180 |
| v22-b05-value-argmax | 300 | 6.000 | 0 |
| v22-b05-value-sampled | 100 | 2.000 | 0 |
| v22-b05-policy | 200 | 4.000 | 200 |
| **Summe** | **2.345** | **29.450** | 380 |

Das ist par.1 auf die Partie genau -- 29.450, davon 12.000 aus dem
v22-Self-Play. Die Generationenstruktur ist wie registriert besetzt: NEU ist
v22-b05, **G-1 und G-2 kommen beide aus hv2** (Nutzer-Bestaetigung
2026-08-31; par.3 haelt fest, dass das ein bewusster Platzhalter ist).

**Zwei Werkzeuge mussten dafuer nachgeruestet werden:**

1. **`train.py --file-list`.** Der Trainer kannte nur `glob(data/*.pkl)`
   minus `MOSAIC_DATA_EXCLUDE`. Eine seed-gezogene Rotation von 1.745 aus
   2.400 Dateien waere als Regex ein Ausdruck aus 655 Alternativen gewesen --
   unlesbar und im Manifest unbrauchbar. Jetzt gibt es das Gegenstueck zu
   `build_cache_incremental --file-list`, mit hartem Abbruch bei fehlenden
   Eintraegen: ein stillschweigend kleineres Fenster ist genau die
   Fehlerklasse, gegen die das Fenster-Pinning gebaut ist.
2. **Partienzahl je Praefix bei TEILMENGEN berichtigt**
   (`train_manifest.corpus_composition`). Die kumulative Rechnung ueber die
   `g`-Suffixe stimmt fuer vollstaendige Laeufe, aber nicht fuer ein
   rotierendes Fenster: faellt eine Datei heraus, erbt ihre Nachfolgerin die
   Spanne, und die Summe bleibt `max(g)`. Der erste b01-Lauf hat hv2 deshalb
   noch als "24000 Spiele" ausgewiesen statt 17.450. Der Ersatz nimmt die
   Datei-Granularitaet (kleinster positiver g-Abstand) mal der Dateizahl; die
   alte Zahl bleibt als `games_cumulative` mit einem `subset_of_run`-Merker
   im Manifest stehen. **Das b01-Manifest vom 2026-08-31 traegt noch die alte
   Zahl** -- der Lauf war beim Fix schon gestartet.

## par.2b ERGEBNIS v23-b01 -- TOR 2a BESTANDEN (2026-08-31)

**Training:** Warmstart von `v22-b05` auf dem Fenster oben, 12 Epochen,
lr 5e-5 mit Cosine, `--moon-loss-weight 0`, Endgame-Kopf an, Val-Pool auf
die neuen Partien beschraenkt. Laufzeit 21.488,8 s (5,97 h), davon 12.434,5 s
Datenaufbau. Kandidat ist `v23-b01_brierbest` (Epoche 5, val_brier 0,1934);
Plateau ab Epoche 10.

**Tor 2a (Spaltenbau im Self-Play), argmax-Instrument @400, je 200 Partien,
GLEICHER Seed 20260931 -- also gepaart:**

| Kennzahl je Partie und Seite | `v23-b01_brierbest` | `v22-b05` |
| --- | --- | --- |
| **volle Spalten** | **0,5150** | 0,3100 |
| Seiten mit >= 1 voller Spalte | 168 / 400 | 95 / 400 |
| eigene Punkte | 46,80 | 42,10 |
| Strafleiste | 5,74 Steine | 6,61 |
| volle Reihen | 0,147 | 0,233 |

**Gepaarte Differenz +0,2050 +- 0,0898 (SE 0,0458, t +4,47, 200 Paare)** --
plus 66 Prozent Spaltenbau, das Konfidenzintervall haelt die Null deutlich
draussen. Tor 2a verlangt "nicht unter dem Vorgaenger"; erreicht ist das
Doppelte des Geforderten.

**Warum BEIDE Seiten frisch gemessen wurden:** die registrierte Referenz
0,3375 stammt vom 2026-08-29, also von VOR dem Stack-Draw-Entscheid, der seit
dem 2026-08-30 in jeder Erzeugung steckt. Ein Vergleich dagegen haette den
Knopf mitgemessen. Nebenbefund: die frische b05-Messung liegt bei 0,310, der
Knopf bewegt die Groesse also kaum -- das wusste man vorher aber nicht.

**Zwei Beobachtungen ohne Torfunktion:** b01 tauscht REIHEN gegen Spalten
(0,147 gegen 0,233) -- die registrierte Richtung, denn eine volle Rasterzeile
ist ohne Spezialfliese unmoeglich. Und der Spaltenbau kostet hier nichts: 4,7
Punkte MEHR bei 0,9 Strafsteinen weniger. Das unterscheidet ihn vom
Sims-Tausch, wo mehr Spalten Staerke gekostet haben.

**Offen bleiben Tor 1** (gepaartes Gating in Champion-Strenge, laeuft) **und
Tor 2b** (Spalten gegen Widerstand, Arena mit --log-games plus
`tools/probes/arena_column_probe.py`). Erst beide zusammen geben das
v24-Self-Play frei.

## par.2c TOR 1 BESTANDEN -- in Champion-Strenge, mit Replikation (2026-08-31)

`v23-b01_brierbest` gegen `v22-b05`, beide @400, gepaartes Gating
(`tools/paired_gating.py`, Blockgroesse 5, `--no-promote-winner`):

| Lauf | Seed | Ergebnis | Paare | Vorzeichentest | gepaarte Differenz |
| --- | --- | --- | --- | --- | --- |
| 1 | 20260940 | 52:28 | 40 | p = 0,0005 | +0,600 [+0,312, +0,888] |
| 2 (Replikation) | 20260941 | 67:33 | 50 | p = 0,0015 | +0,680 [+0,315, +1,045] |
| zusammen | -- | **119:61** | 90 | -- | -- |

Beide Laeufe erreichen die obere SPRT-Schranke, beide unter 150 Paaren --
**deshalb war die Replikation Pflicht** (Champion-Strenge,
`docs/generation_loop.md` Tor 1; Praezedenz ist die b05-Kante, die mit 25
Paaren fruehstoppte und nur informativ verbucht wurde). Mit zwei
unabhaengigen Seeds ist die Auflage erfuellt.

**Beifang aus Lauf 1:** A-Sweeps 12, **B-Sweeps 0** -- b05 hat in keinem
einzigen Paar beide Partien gewonnen. In Lauf 2 dann 22 zu 5.

**Falle beim Aufsetzen abgefangen:** `--promote-winner` steht per Default auf
AN und haette `models/champion.txt` auf b01 gesetzt, sobald der SPRT
signifikant ausfaellt. Das waere eine stille Promotion gegen die eigene
Trennung gewesen (Champion ist v21; b01-gegen-b05 ist das Ratschen-Tor).
Beide Laeufe mit `--no-promote-winner`.

## par.2d TOR 2b BESTANDEN -- Spalten auch GEGEN Widerstand (2026-08-31)

Gemessen mit `tools/probes/arena_column_probe.py` aus den Partie-Logs zweier
Arenen b01 gegen b05 (je 80 Partien @400, `--log-games`, Basis-Seed
20260951), also aus der Brettgeometrie und **unabhaengig von den
Wertungsplatten** -- Nutzer-Vorgabe: "Ich brauch keine k1 Punkte."

| | volle Spalten je Seite |
| --- | --- |
| `v23-b01_brierbest` | **0,6456** |
| `v22-b05` | 0,4304 |

**Gepaart je Partie ueber beide Laeufe: +0,2152 +- 0,1616 (SE 0,0825,
t +2,61, n=158).** Beide Seiten stammen aus DERSELBEN Partie, die Paarung ist
also exakt.

**Der Vorsprung ist praktisch derselbe wie im Self-Play** (+0,215 gegen
+0,205) -- der Spaltenbau ueberlebt den Widerstand eines Gegners. Genau das
war die Luecke, die Tor 2a allein nicht schliessen konnte.

**Drei Vorbehalte, die dazugehoeren:**

1. **Schwaechere Signifikanz als im Self-Play** (t 2,61 gegen 4,47) -- 158
   statt 400 Partien, und die beiden Orientierungen streuen erheblich
   (Orientierung 1: 0,5443 gegen 0,5316, praktisch gleichauf; Orientierung 2:
   0,7468 gegen 0,3291). Die Heterogenitaet ist bei diesen SEs mit Rauschen
   vertraeglich, aber sie ist da.
2. **Je eine Partie pro Lauf war nicht replaybar** (Chip-Vollendung), die
   Zahlen stehen auf 79 von 80 je Orientierung. Von der Sonde ausgewiesen,
   nicht still uebersprungen.
3. **Beide Netze bauen gegen einen GEGNER mehr Spalten als gegen sich
   selbst** (0,646 gegen 0,515 bzw. 0,430 gegen 0,310). Unerklaert, als
   Beobachtung festgehalten -- eine Erklaerung waere ein eigener Strang.

**Ueberfluessiger Aufwand, benannt:** die zweite Orientierung war nicht
noetig. `run_net_vs_net_arena` alterniert den Startspieler bereits innerhalb
eines Laufs (self_play.rs:2722), das Brett ist nur ein Etikett. Der Swap-Lauf
hat eine Verzerrung neutralisiert, die die Engine schon neutralisiert -- er
hat die Stichprobe verdoppelt, aber nicht aus dem Grund, aus dem er gefahren
wurde.

## par.2e GESAMTVERDIKT v23: ALLE VIER TORE STEHEN

| Tor | Ergebnis |
| --- | --- |
| 0 Korpus traegt das Signal | Symmetrie-Trennung +0,4041, t 41,26; 5.629 Seiten mit voller Spalte |
| 1 Siege gegen den Vorgaenger | 119:61 aus zwei unabhaengigen Seeds |
| 2a Spalten im Self-Play | +0,2050, t +4,47 |
| 2b Spalten in der Arena | +0,2152, t +2,61 |

**Damit ist das v24-Self-Play freigegeben** (`docs/generation_loop.md`,
Schritt 9). NICHT freigegeben ist die Promotion: die faellt erst mit der
Kante gegen `v21_2d_brierbest` (1215), und die steht noch aus.

## par.2f CHAMPION-KANTE: AUGENHOEHE, NICHT UEBERHOLT (2026-08-31)

`v23-b01_brierbest` gegen `v21_2d_brierbest`, beide @400, 200 Paare (harter
Deckel erreicht):

```
219:181 (54,75 Prozent), KEIN SPRT-Entscheid (LLR +0,741)
Vorzeichentest p = 0,0842
gepaarte Differenz +0,190, 95%-KI [-0,013, +0,393]
```

**Lesart:** b01 fuehrt, aber das KI schliesst die Null ein -- **nicht belegt
besser**, und ebenso wenig schlechter. **v21 bleibt Champion**, die Promotion
faellt nicht. Das ist genau die Trennung, die
`docs/generation_loop.md` am selben Tag festgeschrieben hat: die Tore geben
das v24-Self-Play frei, die Promotion haengt an dieser Kante.

**Warum kein SPRT-Verdikt:** das Instrument testet H1 p = 0,65 gegen H0
p = 0,5, ist also auf rund +100 Elo geeicht. Ein echter Vorsprung von ~5
Prozentpunkten endet dort am Deckel ohne Entscheid -- das heisst NICHT
"gleich stark", sondern "ein +100-Elo-Vorsprung ist nicht belegt".

**Groessenordnung, als Herleitung markiert:** 54,75 Prozent entsprechen rund
**+33 Elo** ueber v21. Die Linie startete diese Generation mit b05 bei 1084
gegen 1215 -- sie hat also einen Rueckstand von 131 Punkten geschlossen und
liegt jetzt im Bereich des Champions. Die belastbare Verankerung liefert erst
die Anker-Kante.

## par.2g v23-b02 (KALTSTART): fertig, mit einem Checkpoint-Problem

Early Stop nach **Epoche 15 von 40** (Plateau auf Policy UND Brier seit E10,
Patience 5). Laufzeit **4,22 h**, davon 32 s Datenaufbau -- der Fenster-Cache
von b01 traf, was die 3,45 h Aufbau erspart hat. **Damit ist die nie
gemessene Zahl da:** ein Kaltstart auf vollem Fenster kostet gegenueber dem
Warmstart (5,97 h) NICHT mehr, sondern weniger, sobald der Cache steht.

**Aber:** b02s brierbestes Modell liegt bei **Epoche 1** (val_brier 0,1881
gegen b01s 0,1934 bei E5). Dasselbe Muster zeigten die v22-Kaltstarts (dort
ebenfalls brierbest bei E1), und es ist heikel: `--select-by-brier` wurde
laut eigener Hilfe eingefuehrt, damit die Auswahl NICHT "einen praktisch
untrainierten frischen Kopf" nimmt -- bei einem Kaltstart tut sie nach einer
Epoche womoeglich genau das. Bezeichnend: v22 hat den Kaltstart b04 ueber
`_best` weitergefuehrt, nicht ueber brierbest.

**Vorab registrierte Aufloesung (Nutzer-Freigabe 2026-08-31):** eine kurze
gepaarte Arena `v23-b02_best` gegen `v23-b02_brierbest` entscheidet, welcher
Checkpoint der Kandidat des Arms ist; dieser tritt dann gegen b01 an. Es ist
eine INTERNE Auswahl, kein Tor -- gibt der SPRT kein Verdikt, entscheidet der
Punktschaetzer. So scheitert die Warm-gegen-Kalt-Frage nicht an einer
Checkpoint-Regel statt am Startmodus.

## par.2h CHECKPOINT-ARENA AUFGELOEST: Kandidat ist `_brierbest` (2026-08-31)

Die in par.2g vorab registrierte interne Auswahl ist gefahren:
`v23-b02_best` gegen `v23-b02_brierbest`, beide @400, gepaartes Gating
(Block 5, Deckel 100 Paare, Seed 20260970, threads 10).

```
33:47 aus 40 Paaren, SPRT-Entscheid H0 (LLR -3,157)
Vorzeichentest p = 0,189
gepaarte Differenz -0,350, 95%-KI [-0,791, +0,091]
Punkte 37,53 gegen 42,33; Strafpunkte 11,68 gegen 11,80
```

**Lesart nach der Vorab-Regel** (interne Auswahl, kein Tor; ohne Verdikt
zugunsten von A zaehlt der Punktschaetzer): beide Kennzahlen zeigen auf
`_brierbest`, die Marge ist NICHT signifikant. **Kandidat des Kaltstart-Arms
ist `v23-b02_brierbest`.** Das SPRT-Verdikt H0 heisst hier "kein Beleg, dass
`_best` besser ist" -- das Instrument testet gegen p = 0,65, also rund
+100 Elo; es ist kein Beleg fuer Gleichstand.

**Die Sorge aus par.2g ist damit nicht bestaetigt** (ein brierbester
Checkpoint aus Epoche 1 spielt hier nicht schlechter, numerisch besser) --
widerlegt ist sie ebenso wenig, dazu ist die Marge zu klein.

Artefakt: `artifacts/gating_b02_best_vs_brierbest.json`; `laufzeit` 1.235,7 s
Wanduhr / 5.160,9 s CPU / threads 10 / 15,45 s je Partie. **Unter Nebenlast
gemessen** (das b03-Training lief seit 21:33 auf der GPU) -- die 15,45 s je
Partie liegen darum ueber den 12,2-13,7 s der Gatings vom selben Tag und sind
als Planungsgroesse nach oben abgerundet, nicht nach unten.

**Zu den sechs Standard-Kennzahlen:** das Artefakt traegt Punkte, Margin und
Strafleiste; Reihen-, Spalten- und Plattenpunkt-Kennzahlen fehlen, weil der
Lauf ohne Partie-Logs gefahren wurde. Das ist hier vertretbar, weil die
Entscheidungsmetrik dieser INTERNEN Auswahl vorab die Siegzahl war; fuer die
eigentliche Arm-Frage (b02_brierbest gegen b01) sind sie zu erheben.

~~**Offen bleibt die Arm-Frage selbst:** `v23-b02_brierbest` gegen
`v23-b01_brierbest` -- Warmstart gegen Kaltstart auf demselben Fenster.~~
**ERLEDIGT 2026-09-01:** gleich stark (85:75 fuer b01), aber b02 baut nur ein
Drittel der Spalten (`PREREG_capacity_sim_frontier.md` par.12/13, mit dem
dort nachgetragenen Vorbehalt zum Lernraten-Rezept). Auch b03 und b05 sind
gemessen; kein Arm ist belegt besser, b01 ist Generator fuer v24
(`PREREG_v24_window.md` par.4).

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

## par.4c WECKER-ABARBEITUNG (registriert 2026-08-30, VOR dem Start; Nachtprogramm-Fahrplan)

Jeder Punkt der par.4-Liste bekommt hier einen BEWUSSTEN Entscheid; wo
eine Messung noetig ist, faehrt sie das Nachtprogramm (Kochrezept
evaluations/night_run_20260830.md) VOR dem Erzeugungsstart.

| Wecker | Entscheid |
| --- | --- |
| Spalten-Abnahme-Tor par.3b.2 | REVIDIERT und erfuellt -- Lehrer-Prereg par.3b.12 (neue Startbedingung 3/3 gruen, Waechter nach Erzeugung bindend) |
| MOSAIC_IMPLICIT_MINIMAX_A | GEMESSEN 2026-08-30 (Minimax-Prereg par.3b, je 200 Partien): alpha 0,2 senkt die Zustandsabdeckung (0,990) und laesst die Zielschaerfe unbewegt -> **alpha 0,0**, gemessener Entscheid, nicht Rueckfall |
| Risk-Utility A1 | NICHT einbauen fuer Generation 1 -- ungebaut, kein unbeaufsichtigter Nacht-Engine-Bau; Frist ist damit durch bewussten Entscheid gewahrt, Wiedervorlage Generation 2 |
| MOSAIC_STACK_DRAW_RESEARCH | GEMESSEN 2026-08-30 (chance_nodes par.15, 100 gepaarte Partien): kein Staerkeverlust (68:77, Punkte-Block-t 2,04) und 136/136 Slot-Ziele gueltig -> **EIN, in der Umgebung BEIDER Erzeugungslaeufe** (keine Spec-Entsprechung, prozessweiter OnceLock) |
| --seed-positions | AUS fuer Generation 1: seed_positions_v1.jsonl stammt aus PLATTENBLINDEN Zustaenden (Asym-Aera) -- die Wiedervorlage-Bedingung der Seeding-Prereg verlangt eine plattenbewusste Quelle; Neu-Kuratierung aus hv2/b05-Zustaenden als benannter Gen-2-Posten |
| Startkuppel-Streuung | Handheuristik BLEIBT fuer Generation 1 (bewusster Entscheid statt Default-Verfall); start_dome Stufe 0 bleibt offen fuer Gen 2 |
| MOSAIC_STACK_DRAW_RESERVATION | AUS (steht entschieden) |
| ROUND_TRANSITION_SAMPLING | false (Schritt-0-Entscheid weiter offen, bewusst) |
| Vollendbarkeits-FILTER | AUS fuer Generation 1 (ungebaut, kein Nacht-Bau); prioritaerer Gen-2-Kandidat |
| Bootstrap-Horizont | 2 (steht) |
| --rtv / --pcr-full-prob | AUS (Standard seit v13 bzw. PCR negativ) |
| --sims / Klassen | ~~Sockel 4.000 @400 mit Root-Noise; Schwarm 8.000 --value-only (v20-Konvention, pcr_cheap_sims 150)~~ **BERICHTIGT 2026-09-01: gefahren wurden ALLE DREI Laeufe mit `--sims 100`** (Manifeste `data/manifest_v22-b05-*.json`, Feld `cli_args.sims`; Betriebspunkt aus `PREREG_search_depth_column_optimum.md`, Sims-Probe vor dem Schwarm). Der Schwarm lief `--value-only` (erkennbar an `pcr_full_prob 0.0`, `pcr_cheap_sims 100`), der Sockel ohne. Diese Zeile stand bis zur Pruefung am 2026-09-01 unberichtigt und hat `PREREG_v24_window.md` par.2 eine falsche Referenz geliefert |
| --no-root-noise / --deterministic / --tau-argmax-from-move | **UEBERHOLT durch Zuschnitt D** (Lehrer-Prereg par.3b.12, Nutzer "mach D"): die Nacht-Leiter hat gezeigt, dass JEDE fruehe Zug-Stochastik die Vollendung auf 0,07-0,11 drueckt. Gefahren wird jetzt Value-argmax (6.000, --no-root-noise --deterministic) + Value-gesampelt (2.000) + Policy voll gesampelt (4.000) |
| MOSAIC_WERTUNG_STREUUNG_MAX | Default (unveraendert) |
| Moon-Kopf | Trainings-Rezept-Entscheid: Gewicht 0 ab dem v23-Training (No-Op-Ziel, train.py:513); Flag-Bau VOR dem Training, nicht heute Nacht |

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

**GEBAUT 2026-08-30, Default AUS** (Registrierung und Begruendung der
gewaehlten Form in `PREREG_heuristic_v2_long_rows.md` par.3b.3, Abschnitt
"ARM K GEBAUT"): Knopf `MOSAIC_BOOTSTRAP_COHERENCE=sum1`, Summen-Normierung
der beiden Bootstrap-Werte vor dem TD-Blend, Cache-Key-Komponente in beiden
Namensraeumen, Manifest-Feld `bootstrap_coherence`, Abnahmesonde
`tools/probes/bootstrap_coherence_probe.py` (Lauf steht aus, Maschine ist
bis zum Erzeugungsende belegt). Damit ist der Wecker BAUSEITIG erledigt;
offen bleibt nur der Arm-Entscheid (mit oder ohne) fuer das v23-Training.

## par.4a3 WECKERLISTE VOR DEM v23-TRAINING (Durchsicht aller offenen Preregs, 2026-08-31)

Gegenstueck zu par.4/par.4c, aber fuer den TRAININGS-Start statt den
Erzeugungs-Start. Anlass ist die Nutzer-Frage "sonst ist nichts zu tun vor dem
training?"; durchgesehen wurden alle 23 Preregs mit Statuskopf OFFEN plus die
Wecker-Verweise der entschiedenen. Was hier NICHT steht, ist geprueft und
gehoert nicht auf die Liste (implicit-Minimax, Stack-Draw, Seed-Positionen,
Startkuppel, Round-Transition-Sampling, Vollendbarkeits-Filter,
Bootstrap-Horizont: alle in par.4c bewusst entschieden, Fristen gewahrt).

| Wecker | Quelle | Stand |
| --- | --- | --- |
| **Korpus-Waechter** (Symmetrie-Trennung Value-Klasse, >= 1.500 Seiten mit voller Spalte) | Lehrer-Prereg par.3b.12 | BINDEND, faellt direkt nach dem Lauf |
| **Arm K** -- mit oder ohne Summen-Normierung trainieren | par.4a2 | gebaut, Default aus. **EINGETAKTET 2026-08-31 (Nutzer): SPAET, nach b04** -- b01 bis b04 fahren ohne ihn, damit die vorhandenen Bloecke gueltig bleiben; Arm K zahlt den Block-Neubau dann allein (Lehrer-Prereg par.3b.3, Abschnitt EINTAKTUNG) |
| **Moon-Gewicht 0** | par.4c-Zeile Moon-Kopf | Flag existiert (train.py:2460); nur noch am Aufruf zu setzen |
| **Kaltstart oder Warmstart?** | `PREREG_capacity_sim_frontier.md` par.9/par.10 | **ENTSCHIEDEN 2026-08-31 (Nutzer): BEIDES als eigene Arme, gleiche Breite** -- b01 Warmstart, b02 Kaltstart auf BESTANDSBREITE (ein Faktor), b04 vorregistriert als Breiten-Arm. Kaltstart ~2,5 h mit vorgebautem Cache. Der Conv-Zweig braucht fuer b04 erst zwei Flags und eine Checkpoint-Ableitung (par.10) |
| **Endgame-Kopf-Flag** | STATUS-Zeile zum v22-Kaltstart (b01/b02) | **wird mit diesem Training erstmals scharf.** Auf hv2 war die Endgame-Maske komplett 0 (root_q schreibt nur der NetSelfPlayAgent); im neuen Korpus ist root_q da -- gezaehlt am 2026-08-31: 2.332 von 3.538 Records, davon 314 R5-Drafting. Der offene Flag-Entscheid (konstant lassen vs. false auf Heuristik-Korpora) betrifft jetzt ein Ziel, das tatsaechlich lernt |
| **Policy-Ueberraschungs-Gewichtung** | `PREREG_policy_surprise_weighting.md` par.4a | **v23-b03**, vom Nutzer 2026-08-31 im Zyklus-Zuschnitt bestaetigt. Ungebaut (Loss-Gewichtung in train.py); baubar, waehrend b01/b02 rechnen |
| **Relabeling-Etappe** | `PREREG_reanalyze_label_depth.md` par.4a | registriert: flach spielen, POLICY per hv2-Lehrer relabeln, VALUE tief nachlabeln. Reihenfolge-Auflage siehe unten |
| **Fenster-Zuschnitt** | par.2/par.2a | **ERLEDIGT 2026-08-31**: 1.745 von 2.400 hv2-Dateien seed-gezogen (20260920), Liste in `data/window_v23.txt`, vom Trainingslauf auf die Partie genau gegengezaehlt |
| **Traeger-Manifest** | par.1 dieser Datei | par.1 will hv2 ueberwiegend policy-maskiert; entwertet die 2.400 liegenden hv2-Bloecke. Die NEUE Value-Klasse braucht dafuer kein Manifest (sie maskiert sich ueber `policy_target_valid`, gezaehlt 2026-08-31: 2.332 von 2.578 Drafting-Records) |
| **Monolith gegen Val-Split** | `PREREG_cache_build_time.md` Hebel 4 | `train.py --cache-file` prueft den FENSTER-Schluessel; ein Lauf mit `--val-frac > 0` bildet einen anderen Schluessel und der Waechter lehnt korrekt ab. Wer den Monolithen nutzen will, faehrt `--val-frac 0` oder baut ihn passend |

**TRAEGER-FALLE, am Code geprueft 2026-08-31 -- wer ein Manifest einfuehrt,
maskiert versehentlich die NEUE Policy-Klasse mit.** `_is_policy_carrier`
(corpus_dataset.py) kennt drei Faelle: kein Manifest -> jede Datei traegt;
Manifest OHNE `carrier_prefixes` -> Traeger ist, wer gelistet ist ODER unter
den eingefrorenen v20-Kurzschluss faellt; Manifest MIT `carrier_prefixes` ->
gelistet oder Praefix-Treffer. Der Kurzschluss ist
`V20_CARRIER_SHORTCUT_PREFIXES = ("selfplay_v19wdl", "selfplay_v20wdl")`
(neural_net.py:796) -- die v22-b05-Dateien fallen NICHT darunter, und
`tools/generate_carrier_manifest.py` schreibt `carrier_prefixes` bewusst
nicht. Ein Manifest, das nur die 180 hv2-Traegerdateien listet, setzt damit
`pol_w = 0` fuer den GESAMTEN neuen Korpus -- auch fuer die 200 Dateien der
Policy-Klasse, um die das ganze Fenster gebaut ist. **Auflage:** das
v23-Manifest listet die Policy-Klasse ausdruecklich mit (180 hv2 + 200
b05-policy = 380 Eintraege), oder es traegt
`carrier_prefixes: ["selfplay_v22-b05-policy_"]`. Vor dem Training gegen
`policy_carriers.traeger_dateien_je_praefix` im Trainingsmanifest pruefen.

**REIHENFOLGE-AUFLAGE, am Code geprueft 2026-08-31 (sonst still falsch
trainiert):** `tools/relabel_drafts_with_teacher.py` schreibt die pkl IN
PLACE (Zeile 138, `dump_records(path, recs)`), und
`tools/build_cache_incremental.py` erkennt einen vorhandenen Block ALLEIN am
Dateinamen -- kein mtime-, kein Inhaltsvergleich. Wer eine Korpusdatei
relabelt, NACHDEM ihr Block gebaut ist, traniert still auf den alten
Policy-Zielen. Der DAgger-Lauf ist dem nur entkommen, weil er in einem
eigenen Verzeichnis unter eigenem Praefix lief (`data/onpolicy_v22-b05/`,
Praefix `dagger-b04`). **Regel fuer diesen Zyklus:** relabeln auf eine Kopie
mit eigenem Praefix, ODER die betroffenen `.filecache_*.h5` im selben Zug
loeschen. Ein Waechter dagegen (Quellgroesse/mtime im Block-Attribut, Warnung
bei Abweichung) ist NICHT gebaut -- benannt, nicht entschieden.

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
