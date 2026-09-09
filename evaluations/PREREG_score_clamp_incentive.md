<!-- STATUS: OFFEN | Frage: Bleibt die Anreizstruktur der Suche erhalten, wenn ein Spieler bei 0 Punkten steht und Strafen wie Kaeufe dort gratis sind? | Beleg: nichts gebaut. Befund am Code geprueft (par.2): das LABEL kennt den Unterschied, der EINGANG nicht -- score_unclamped geht nur ins Trainingsziel (corpus_dataset.py:1128), das Netz sieht im Spiel den geklammerten Wert (features.rs:689). Anlass: game_20260909_004553_seed876496 (KI ab R1 auf 0, vier Runden Strafen ohne Wirkung). Stufe 0 ist eine MESSUNG mit vorab gesetzter Abbruchschwelle (par.5). Getaktet fuer v27 nach dem Arm v27-b01. -->

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
