<!-- STATUS: OFFEN | Frage: Bleibt die Anreizstruktur unter null erhalten -- die Null-Klammer macht bei Stand 0 Strafen wie Kaeufe wirkungslos? | Beleg: Stufe 0 GEMESSEN 2026-09-10 (par.10): Korpus 39 % der Partien je Seite mit Stand 0, geschluckte Strafe Median 0 (Mittel 0,5 Punkte), aber 3,1 GRATIS-Ziehungen je Partie und Seite (bedingt Median 8, Max 35); Mensch-Logs: Mensch 3 %, KI 13 %. Schwelle aus par.5 NICHT unterschritten, Strang bleibt offen; Gewicht liegt auf der Kaufseite (par.9). Stufe 1 erst nach dem POST-Lauf des Kuppelstapel-Umbaus. -->

# PREREG: Die Null-Klammer und die Anreizstruktur

**Aufgemacht 2026-09-09 auf Nutzer-Auftrag** ("ja mach die Prereg dafuer auf und takte sie
fuer v27 ein"). Abgespalten von `PREREG_dome_stack_information_sets.md` par.9, wo der
Strang benannt, aber ausdruecklich nicht behandelt wurde.

## par.1 DIE FRAGE

Ein Punktestand kann nie unter null fallen. Das ist Regel und bleibt Regel. Die Frage ist
eine andere: **sieht die Suche unterhalb der Klammer noch einen Unterschied zwischen
"schlecht" und "desastroes" -- und wenn nein, was kostet das?**

Es geht NICHT darum, die Spielregel zu aendern. Es geht darum, was der Suche und dem Netz
gezeigt wird.

## par.2 DER BEFUND, am Code geprueft (2026-09-09)

| Stueck | Befund | Pruefstelle |
| --- | --- | --- |
| Der sichtbare Punktestand klemmt | `self.score = (self.score + delta).max(0)` | `engine/src/board.rs:344-346` |
| Ein Schattenzaehler existiert und faengt STRAFEN voll | `score_unclamped += delta`, ungeklemmt | `engine/src/board.rs:346` |
| Bei KAEUFEN faengt er bewusst NICHT | `apply_paid_cost` zieht `max(delta, -score)` von BEIDEN ab: was man nicht hat, zahlt man nicht | `engine/src/board.rs:362-365` |
| Er ist reines Trainingsmaterial | "niemals fuers sichtbare Spiel/Regelwerk gelesen"; geschrieben in die Self-Play-Records | `engine/src/board.rs:248-254`, `engine/src/self_play.rs:2902` |
| Das Trainingsziel nutzt ihn | `scores_src = step.get("scores_unclamped", step["scores"])` | `engine/py/corpus_dataset.py:1128` |
| **Das Netz sieht im Spiel den GEKLAMMERTEN Wert** | `f.push(p.score as f32 / 100.0)` | `engine/src/features.rs:689` |

**Die Luecke in einem Satz:** das LABEL kennt den Unterschied, der EINGANG nicht. Ein Netz,
das auf ungeklemmten Margen trainiert wurde, muss zur Spielzeit aus dem Brett erraten, wie
tief es steht, weil sein eigener Punktestand die Information nicht mehr traegt.

## par.3 DER ANLASS

`static/log/game_20260909_004553_seed876496.log` (Nutzer-Befund: "sehr traurig fuer die
KI"). Die KI zahlte in R1 vier Punkte fuer Stapelziehungen und stand ab da auf 0. Danach:

| Runde | Strafe laut Log | Wirkung auf den Punktestand |
| --- | --- | --- |
| R1 | -2 | keine (Z. 103) |
| R2 | -6 | keine (Z. 209) |
| R3 | -12 | keine (Z. 304) |
| R4 | -10 | keine (Z. 387) |

Endstand 0 gegen 69. **Ungepruefte Herleitung, ausdruecklich als solche markiert:** dass die
Klammer diese Strafen VERURSACHT hat, ist nicht gezeigt -- eine schwache Stellung erzeugt
Strafen auch ohne sie. Genau deshalb steht am Anfang eine Messung und kein Umbau.

## par.4 WAS DER STRANG NICHT IST

* **Keine Regelaenderung.** Der Punktestand bleibt bei null geklammert, in der Anzeige wie
  in der Wertung.
* **Kein Eingriff in `scoring_progress`** (`engine/src/scoring.rs:160`). Diese Funktion ist
  der Elo-Anker der Kampagne und wird nicht angefasst; jeder Kandidat unten haelt sich
  davon fern.
* **Nicht der Stapel-Strang.** Die Kaufseite der Klammer (Ziehungen sind bei 0 gratis)
  gehoert dort hin (`PREREG_dome_stack_information_sets.md` par.4b); hier geht es um die
  Anreizseite.

## par.5 STUFE 0: MESSEN, BEVOR IRGENDETWAS GEBAUT WIRD

Ohne diese drei Zahlen ist jede Bauentscheidung geraten. Alle drei sind aus vorhandenen
Self-Play-Records zu holen, ohne neue Erzeugung (`scores` und `scores_unclamped` liegen je
Record vor, Korpus-Abdeckung 100 % gemessen 2026-08-23).

1. **Wie oft steht ein Spieler ueberhaupt auf 0?** Anteil der Partien mit mindestens einem
   Halbzug bei Punktestand 0, je Seite. GRUNDMENGE: Partien des Korpus. EINHEIT: Anteil.
2. **Wie lange steht er dort?** Halbzuege bei Stand 0 je Partie, Median und oberes Dezil.
   GRUNDMENGE: Halbzuege, EINHEIT: Halbzuege je Partie -- nicht je Spieler verwechseln
   (`move_number` zaehlt beide, Regel 0 Zusatz 2).
3. **Wie viel Strafe schluckt die Klammer?** Summe `score - score_unclamped` am Partieende,
   je Seite. EINHEIT: Punkte. Das ist der Betrag, ueber den die Suche im Spiel nichts weiss.

**Vorregistrierte Schwelle:** liegt (1) unter 5 % der Partien UND (3) im Median unter 3
Punkten, ist der Strang erledigt und wird als UEBERHOLT geschlossen -- dann ist die Falle
real, aber zu selten, um Aufwand zu rechtfertigen. Diese Schwelle steht VOR der Messung
hier, damit sie hinterher nicht verhandelt wird.

## par.6 KANDIDATEN (erst nach Stufe 0 zu bewerten)

**a) Den ungeklemmten Stand ins Merkmal.** Ein zusaetzlicher Wert je Spieler, additiv ans
Ende (2D-Encoder-Regel, Alt-ONNX bleiben spielbar). Billigster Eingriff, aendert keine
Regel, keine Wertung. Frage dabei: bekommt das Netz damit Information, die ein MENSCH am
Tisch auch hat? Der Mensch sieht die Strafleiste und weiss, was sie gekostet haette --
also ja, mit derselben Begruendung wie die Sicht-Arme in
`PREREG_stack_top_feature.md`.

**b) Blattwert auf die MARGE statt den absoluten Stand.** Beruehrt den Suchpfad tiefer und
ueberschneidet sich mit `PREREG_saturating_score_utility.md` (K1, `score_utility_c`, heute
Default 0). Vor einem eigenen Bau ist zu pruefen, ob der dortige Knopf die Frage schon
beantwortet.

**c) Nichts tun, mit Beleg.** Siehe die Schwelle in par.5.

## par.7 WIE ENTSCHIEDEN WIRD

**Stufe 0 entscheidet ueber die Existenz des Strangs**, nicht die Arena. Erst wenn die drei
Zahlen die Schwelle reissen, wird gebaut.

**Danach, falls gebaut:** gepaartes Gating gegen dasselbe Netz ohne die Aenderung,
block-size 5, zwei unabhaengige Seeds, SPRT. **Zusaetzlich diagnostisch und vorab benannt:**
Strafpunkte je Partie in der Teilmenge der Partien, in denen ein Spieler auf 0 stand -- die
Zahl muss fallen, sonst hat der Umbau sein Ziel verfehlt, egal was die Arena sagt.

**Waechter:** ein neues Merkmal aendert `INPUT_SIZE`; die Anker-Frage und
`/mosaic-anchor-invariance` gelten wie bei jeder Engine-Aenderung.

## par.8 TAKTUNG (Nutzer 2026-09-09)

**Eingetaktet fuer v27, NACH dem Arm `v27-b01`** -- dem letzten eingefrorenen
(`PREREG_v25_window.md` par.18, praezisiert am 2026-09-09). Damit liegt der Strang im
selben Fenster wie der Stapel-Umbau
(`PREREG_dome_stack_information_sets.md`), und das ist kein Zufall: beide beruehren
dieselbe Waehrung. Wer den Optionswert des Stapelwissens einbaut, sollte wissen, ob die
Punkte, mit denen es bezahlt wird, unterhalb von null noch etwas bedeuten.

**Stufe 0 ist davon ausgenommen und darf frueher laufen:** sie liest nur vorhandene
Records, aendert nichts und braucht kein offenes Fenster. Bedingung ist allein eine freie
Maschine.

## par.9 AUDIT 2026-09-09 (vor Stufe 0)

Drei Punkte, die Stufe 0 so, wie sie in par.5 steht, ins Leere laufen liessen:

1. **Grundmenge.** par.5 misst auf Self-Play-Partien und haengt die Abbruchschwelle
   daran. Im Self-Play spielen zwei gleich starke Kopien; die Klammer-Falle entsteht aber,
   wenn eine Seite weit zurueckliegt. Der Anlass war 69:0 gegen einen Menschen. Die 23
   Mensch-Logs in `static/log/` (in `PREREG_dome_stack_information_sets.md` par.13a der
   tragende Beleg) gehoeren als ZWEITE Grundmenge in Stufe 0, mit eigener Zahl; die
   Schwelle "UEBERHOLT" darf nur fallen, wenn BEIDE Grundmengen unter ihr liegen.
2. **Kennzahl (3) sieht die Kauf-Seite nicht.** `score - score_unclamped` enthaelt per
   Bau nur Strafen: `apply_paid_cost` (`engine/src/board.rs:361-364`) bucht bei Kaeufen
   auf beiden Zaehlern nur den bezahlten Betrag. Die gratis gezogenen Platten, der
   auffaellige Posten des Anlassspiels, stehen in keiner der drei Zahlen. Stufe 0 braucht
   eine vierte: Ziehungen bei Punktestand 0 je Partie und Seite. Eigentuemer dieser Zahl
   ist nach Absprache mit `dome_stack` par.14 Punkt 1 festzulegen; bis dahin faellt sie
   zwischen die beiden Preregs.
3. **`scores` und `scores_unclamped` sind Endstaende, keine Zwischenstaende.** Beide
   werden am Partieende berechnet und in JEDEN Record zurueckgeschrieben
   (`engine/src/self_play.rs:2899-2913`). Kennzahl (1) und (2) ("Halbzuege bei Stand 0")
   sind daraus nicht berechenbar; sie brauchen den Schritt-Zustand `players[i].score`
   aus dem serialisierten `state` je Record (vorhanden, in par.5 nicht benannt). Der
   Startpunktestand ist 5 (`board.rs:302-303`, Agentenbefund), fuer Kennzahl (1) relevant.

Nebenbefund fuer par.6a: `score_unclamped` ist eine Mischgroesse, ungeklemmte Strafen
(`board.rs:344-346`) bei geklemmten Kaeufen (`:361-364`). Als Merkmal ist das eine
Konvention, kein "Stand ohne Klammer"; vor dem Bau benennen.

## par.10 STUFE 0 GEMESSEN (2026-09-10, 16:10-16:40): Schwelle NICHT unterschritten, Gewicht liegt auf der Kaufseite

Werkzeug `tools/probes/score_clamp_stage0_probe.py`, Artefakt
`evaluations/artifacts/score_clamp_stage0.json` (laufzeit 359,9 s einkernig, durch Fremdlast
gebremst; ein identischer Vorlauf brauchte 283 s bei gleichen Zahlen). Zwei Grundmengen nach
par.9: (a) Korpus `selfplay_v26-b01-policy_*` (4.000 Partien, je Seite), (b) alle 30 Mensch-Logs
in `static/log/` (par.9 nannte 23; es sind 30, alle mit KI als Spieler 1). Ziehungserkennung
im Korpus ueber die `📦`-Logzeilen des Folge-Records (Gegenprobe Pool-Rueckgang 10/10 exakt,
0 Log-Luecken in 4.000 Partien); in den Logs ueber den fortgeschriebenen Punktestand
(0 Widersprueche an allen "-> Gesamt"-Zeilen).

| Kennzahl (Einheit) | Korpus Sp. 0 | Korpus Sp. 1 | Mensch (n = 30) | KI in den Logs (n = 30) |
| --- | --- | --- | --- | --- |
| (1) Partien mit Halbzug bei Stand 0 (Anteil) | **0,393** [0,377; 0,408] | **0,390** | 0,033 (1/30) | **0,133** (4/30) [0,053; 0,297] |
| (2) Halbzuege bei 0 je Partie, Median / p90 | 0 / 18 | 0 / 17 | 0 / (Max 10) | 0 / (Max 53) |
| (2) bedingt auf betroffene Partien, Median | 12 (n = 1.570) | 11,5 (n = 1.558) | 10 (n = 1) | 14,5 (n = 4) |
| (3) geschluckte Strafe, Median / Mittel (Punkte) | 0 / 0,53 | 0 / 0,52 | 0 / 0,07 | 0 / 0,27 |
| (3) bedingt auf Partien mit > 0, Median / Max | 3 / 23 (15,2 %) | 3 / 14 (14,5 %) | 2 (3,3 %) | 8 (3,3 %) |
| (4) GRATIS-Ziehungen je Partie, Mittel / Anteil >= 1 | **3,09 / 0,336** | **3,12 / 0,336** | 0,03 / 0,033 | 1,97 / 0,133 |
| (4) bedingt, Median / Max | 8 / 35 | 8 / 34 | 1 | 14 / 18 |
| Ziehungen gesamt je Partie, Median / Mittel | 3 / 6,9 | 3 / 7,0 | 2 / 2,4 | 2,5 / 5,2 |

Lage im Spielverlauf (Teilstichprobe 200 Korpus-Partien): Anteil der Halbzuege bei Stand 0 je
Runde 5,5 / 8,7 / 11,4 / 4,2 / 0,4 Prozent; kein reiner Runde-1-Effekt des Startguthabens.

**Verdikt nach par.5** (UEBERHOLT nur bei (1) < 5 % UND (3)-Median < 3): **keine der beiden
Grundmengen unterschreitet die Schwelle.** Korpus (1) = 39 %, Faktor 8 ueber der Schwelle; in
den Logs unterschreitet die Mensch-Seite beides, die KI-Seite nicht (13 %, Wilson-Untergrenze
5,3 %). Der Strang bleibt OFFEN.

**Was die Messung verschiebt:** geschluckt wird kaum STRAFE (Median 0, Mittel 0,5 Punkte je
Partie und Seite), verschenkt werden ZIEHUNGEN: im Korpus 3,1 Gratis-Ziehungen je Partie und
Seite, in betroffenen Partien Median 8, Maximum 35; in den Mensch-Partien zieht die KI bedingt
14 gratis, der Mensch 1. Kennzahl (3) haette das nie gezeigt (par.9 Punkt 2). Damit gehoert
die Kaufseite in DIESEN Strang, und die Stufe-1-Kandidaten aus par.6 sind an der Ziehung zu
messen, nicht an der Strafe. Nebenbefund zum Anlassspiel: die Klammer schluckte dort 8 der
33 Strafpunkte; die Strafen in R2 (-6) und R4 (-10) waren wirksam. Die Tabelle in par.3
("Wirkung: keine") beschreibt den angezeigten Stand, nicht die Wirkung.

**Ungeprueft:** Kausalitaet (die Sonde zaehlt); Halbzug-Einheit der beiden Grundmengen ist
nicht identisch (Korpus Kuppelzug = 2 Records; Kennzahl (1) ist davon robust, (2) nur
eingeschraenkt vergleichbar); die KI-Seite der Logs sind vier Netze (v21 13, v23-b01 9,
v25-b01 1, v26-b01 7 Partien). Kopplung zum Kuppelstapel-Strang: Gratis-Ziehungen kaufen
Wissen ueber den Stapel; mit Variante A (`dome_stack` par.7) nutzt die Suche dieses Wissen
erstmals, dadurch koennte die Zahl der Ziehungen bei 0 STEIGEN. Vor Stufe 1 hier deshalb erst
den POST-Lauf des Kuppelstapel-Umbaus abwarten und (4) dort nachmessen.
