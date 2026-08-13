# Vorregistrierung: Injektion der WERTUNGSPLATTEN (alle acht Kriterien)

**Angelegt 2026-08-11 nach Nutzer-Rüge** — *"das ist einfach ein witz. wir
wollen die wertungsplatten injizieren. nicht nur die spezialplatten."*

Diese Vorregistrierung ist der **Haupt-Sweep**.
`PREREG_injection_dose.md` (Spezialfelder, `MOSAIC_UNLOCK_SHAPING_W`) wird
damit zum **Sonderfall danach**, nicht zum ersten Lauf.

## 0. Was falsch war, damit es nicht wiederkehrt

Der Auftrag lautete von Anfang an, die **Wertungsplatten** zu injizieren. Der
Term dafür ist gebaut (`wertung_progress_alpha`, alle acht Kriterien, gegatet
auf die aktiven; verdrahtet über `apply_wertung_shaping`,
`net_mcts.rs:1634`). Ich habe trotzdem einen Sweep vorregistriert, der
`MOSAIC_WERTUNG_SHAPING_W` auf **0** lässt und nur den Spezialfeld-Kanal
dosiert — begründet mit dem größten Margen-Anteil (9,0 von 14,5 Punkten).

Das war eine Verengung auf einen Sonderfall. Der Nutzer hat sie **dreimal**
angesprochen; ich habe zweimal erklärt statt umgestellt. **Kein Bau-, sondern
ein Messplan-Fehler.**

## 1. Gegenstand

`MOSAIC_WERTUNG_SHAPING_W` (Gewicht), `MOSAIC_WERTUNG_ALPHA` (Exponent).

> **GEÄNDERT durch die KALIBRIERUNGS-METHODE unten (Nutzer-Vorgabe 2026-08-11):**
> hier stand "Exponent Default 2,0, **nicht** Gegenstand". Jetzt ist es
> umgekehrt: **α ist der Sweep-Gegenstand**, `w` wird bei 1,0 FESTGEHALTEN.
> Grund: α entscheidet, ob der Term überhaupt lenkt, und `w` hat mit
> `dP(Sieg)/dPunkt = 0,0242` eine abgeleitete Größe, α nicht.

Der Term, je Spieler absolut aus dem eigenen Brett
(`net_mcts.rs`, `apply_wertung_shaping_with`):

    für jeden Spieler i:
        pts   = wertung_progress_alpha(players[i], scoring_tile_ids, alpha)
        shift = w * tanh(pts / 50.0)
        out[i] = clamp(value[i] + shift, 0, 1)

und `wertung_progress_alpha` deckt, **gegatet auf `scoring_tile_ids`**:

| Kriterium | Form | Punktwert |
|---|---|---|
| 0 Reihen | `Σ (row_fill/6)^α` | ×3 |
| 1 Spalten | `Σ (col_fill/6)^α` | ×7 |
| 2 Diagonalen | `Σ (diag_fill/6)^α` | ×10 |
| 3 Jokerfelder | `(wild_filled/wild_total)^α` | ×2×wild_total |
| 4 Randfelder | `border_fill` | linear (additiv) |
| 5 Eckplatten | `Σ (corner_fill/4)^α` | 3/3/8/8 |
| 6 Spezialfelder | **0 hier** — hält `unlock_progress_beta` | (Doppelzählung vermieden) |
| 7 Farbreihen | `Σ (row_colors/5)^α` | ×4 |

`MOSAIC_UNLOCK_SHAPING_W` bleibt in diesem Sweep auf **0**, damit die beiden
Kanäle nicht konfundieren.

## 2. Arme — ÜBERHOLT, siehe Kalibrierungs-Methode unten

> Die w-Arme 0,1 / 0,3 unten sind durch den α-Sweep ERSETZT. Die Rechnung dazu
> bleibt gültig und ist der Grund, warum `w` überhaupt eine ableitbare Größe hat
> — nur ist `w` jetzt fest und α wandert.

### (überholter Abschnitt, Rechnung weiter gültig)

**Gerechnet, nicht übernommen** *(meine Ableitung aus den Durchsatz-Zahlen in
`docs/domain_knowledge.md`, ungemessen)*: bei ~15,7 belegten Feldern je Brett
liegt die mittlere Spaltenfüllung bei ~2,6. Mit α = 2 gibt Kriterium 1 allein

    (2,6/6)² × 7 × 6 Spalten ≈ 7,9 Punkte   ->   tanh(7,9/50) = 0,156

Bei w = 1,0 wäre die Verschiebung **0,156** — das erschlägt
Geschwister-Q-Differenzen von wenigen Hundertsteln und sättigt den auf [0,1]
geklemmten Blattwert. Liegen mehrere Kriterien gleichzeitig (es sind immer 3
Platten im Spiel), wird es größer.

| Arm | `w` | Erwartete Verschiebung | Begründung |
|---|---|---|---|
| Kontrolle | **0,0** | 0 | Bestandsverhalten |
| A | **0,1** | ~0,016 | spürbar, klar untergeordnet gegenüber Q |
| B | **0,3** | ~0,047 | Hauswert der bestehenden Shaping-Gewichte, obere Kante |

**Kein Arm bei 1,0** — anders als in `PREREG_injection_dose.md`, wo der Term
eine Größenordnung kleiner ist. Zwei Arme, Task-D-Präzedenz.

## 3. Instrument und Statistik

`tools/paired_arena_env_ab.py`, ein Prozess je Arm (Knöpfe sind prozessweit,
`OnceLock`), Champion `v21_2d_brierbest`@400 gegen **Heuristik@150(dyn)** — die
Heuristik liest keinen der Knöpfe, die Armdifferenz ist also der Netz-Seite
zuzurechnen.

    --env-name MOSAIC_WERTUNG_SHAPING_W --arms 0.0 0.1 0.3 --control 0.0
    --net-sims 400 --n-games 200 --seed 20260911 --out-prefix wertungw

**Basis-Seed 20260911 hiermit festgenagelt** (vor dem Lauf, nicht danach).

1. Gepaart über den Spielindex, identischer Basis-Seed in allen Armen.
2. **Block-Ebene als Pflichtinstrument** (8 Blöcke à 25), Block-Delta mit SE
   und t berichten.
3. Exakter zweiseitiger McNemar auf den diskordanten Paaren.
4. **Bonferroni über zwei Arme**: α = 0,025 je Arm.
5. Frühstopp unter 150 Paaren nur mit Frisch-Seed-Replikation.

## 4. Pflicht-Nebenmessung: das VERHALTEN, nicht nur die Siegquote

Gumbel zieht `GUMBEL_TOP_M = 16` Kandidaten nach Prior-Masse; die Injektion kann
nur **umordnen, was gezogen wurde**. Ein Null-Ergebnis kann also „Term
wirkungslos" ODER „Prior blockiert" heißen — ohne Verhaltenszahl nicht
unterscheidbar. Deshalb `log_games=True` (Commit `9dfeb16`) und Auswertung über
`tools/analyze_game_log.py`.

Zielgrößen mit ihren Referenzwerten aus `docs/domain_knowledge.md`:

| Größe | Mensch | KI heute |
|---|---|---|
| Nahmen-Anteil in Musterreihen 5+6 | 40,4 % | **22,7 %** |
| belegte Zellen je Rasterreihe 5/6 | — | **0,84 / 0,58** |
| Spalten vollständig | — | 0,4–1,2 % |

Der **dichte** Detektor sind die belegten Zellen je Rasterreihe (~6.300
Beobachtungen bei 200 Paaren gegen ~120 Abschlussereignisse) und der
Nahmen-Anteil. Abschlüsse allein sind zu selten, um eine Verschiebung von 20 %
zu zeigen.

### Lesart

| Verhalten | Siegquote | Verdikt |
|---|---|---|
| Zellen in Reihe 5/6 steigen | steigt | Term wirkt und rechnet sich ⇒ Dosis übernehmen |
| steigen | flach | wirkt, wandelt nicht in Siege ⇒ Dosis oder Zielkonflikt mit den Linienpositionen |
| **steigen nicht** | — | **Prior blockiert.** Kein Beleg gegen den Term; Arena-Wert ist UNTERGRENZE, Folge ist Self-Play MIT Injektion |

## 5. Vorbedingungen

1. Wheel mit `log_games` installiert, **Paritätsprobe geprüft**:
   `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` — am
   2026-08-11 selbst verifiziert. ✔
2. `log_games` muss durch die **Python-Seite** gereicht werden —
   `tools/paired_arena_arm_worker.py:41` ruft `net_arena_match` derzeit OHNE
   das Argument. **Offen**, kleine Änderung, vor dem Lauf nötig, sonst liefert
   der Sweep keine Verhaltenszahlen.
3. Die Parser-Lücken in `tools/analyze_game_log.py` (Replay bricht an der
   `↩️ … zurueck unter den Stapel`-Zeile ab) — **in Arbeit**. Die Siegquote
   hängt nicht daran, die Verhaltensmessung schon.

## 6. Was dieser Sweep NICHT entscheidet

- Keinen Champion-Wechsel (kein neuer Checkpoint).
- Nicht `MOSAIC_UNLOCK_SHAPING_W` (`PREREG_injection_dose.md`, danach).
- Nicht den Punkte-Kanal (`PREREG_points_lambda_below_tipping_point.md`).
- ~~Nicht den Exponenten α~~ — **überholt**: α IST der Gegenstand, siehe
  Kalibrierungs-Methode. Nicht entschieden werden dagegen die kalibrierten
  ENDPUNKTE (`ALPHA_KALIBRIERT`), die aus der Heuristik-Referenz gemessen sind.

---

# KALIBRIERUNGS-METHODE fuer alpha (Nutzer-Vorgabe 2026-08-11)

*"für alpha kalibrieren würd ich empfehlen gepaart mit selben seed gegen die
heuristik spielen und dort dann schauen ab wann wertungsplatten gebaut werden
und ab wann die punkte wieder kippen."*

## Warum das die statistische Kalibrierung ERSETZT, nicht ergaenzt

Die Messung in `3dcb154` hat alpha so bestimmt, dass `(fill/kap)^alpha` die
realisierte Abschlussrate trifft -- also den Proxy als SCHAETZER kalibriert.
Die Aufgabe des Terms ist aber nicht, ein guter Schaetzer zu sein, sondern gutes
SPIEL zu erzeugen. Beides faellt nur zusammen, wenn der Blattwert sonst perfekt
ist. Die Nutzer-Methode misst direkt die Zielgroesse.

**Und sie liefert zwei Schwellen aus denselben Laeufen:**

1. **Untere Schwelle -- "ab wann werden Wertungsplatten gebaut".** Zu steiles
   alpha (hoher Exponent) macht den ersten Stein einer Bahn wertlos: `0,5^6 =
   0,016`. Der Term lenkt dann nicht. Beobachtungsgroesse: Plattenabschluesse
   bzw. Plattenpunkte je Partie.
2. **Obere Schwelle -- "ab wann kippen die Punkte".** Zu flaches alpha (bzw. zu
   grosses `w`) laesst die Suche Platten jagen und dabei die BASIS zerstoeren --
   die orthogonalen Nachbarn, die 93 % des Ergebnisses tragen. Beobachtungsgroesse:
   mittlerer Endstand je Partie. Dass es einen INNEREN Optimum-Punkt geben muss,
   folgt aus der Nutzer-Strategie: *"die basis sind die orthogonalen nachbarn,
   die wertungsplatten nehmen wir so gut es geht mit"*.

Eine Siegquote allein kann diese beiden Faelle nicht trennen -- deshalb sind
BEIDE Groessen Pflicht.

## Zuschnitt

Gesweept wird der **Startwert** `alpha_0` (Runde 1), nicht die Endpunkte: die
sind gemessen (`ALPHA_KALIBRIERT`), der Startwert ist die freie Groesse und
zugleich die, die das Lenken bestimmt. Niedriger Startwert = mehr Frühlenkung.

| Arm | `MOSAIC_WERTUNG_ALPHA` | Rolle |
|---|---|---|
| A | **1,0** | linear im Fuellstand -- maximale Fruehlenkung |
| B | **2,0** | jetziger Stand |
| C | **3,0** | steiler, weniger Fruehlenkung |

`MOSAIC_WERTUNG_SHAPING_W` bleibt in diesem Sweep **fest**, sonst ist der
Kontrast konfundiert. Wert: **1,0**, begruendet aus der Messung
`dP(Sieg)/dPunkt = 0,0242` (Endmarge-SD 16,50 ueber 400 Partien) -> aequivalentes
`w = 50 x 0,0242 = 1,21`, also die Groessenordnung, in der der Term den echten
Siegwert der Punkte traegt statt ihn zu daempfen.

Kontrolle ist `w = 0` (Term aus), damit die untere Schwelle einen Nullpunkt hat.

## Beobachtungsgroessen je Arm

| Groesse | Quelle | Referenz |
|---|---|---|
| Plattenpunkte je Partie | Log (`log_games`) | Heuristik 1,99 / Champion 1,10 |
| Abschluesse Spalten/Reihen/Diagonalen | Log | Champion 0,4-1,2 % Spalten |
| **mittlerer Endstand je Partie** | `scores` -- **schon im Arena-Ergebnis, kein Log noetig** | Champion-Korpus 23,35 |
| Nahmen-Anteil Musterreihen 5+6 | Log | Mensch 40,4 % / KI 22,7 % |
| Siegquote | `winner` | -- |

## EINSCHRAENKUNG -- ein POWER-Problem, kein Gueltigkeitsproblem

**Nutzer-Korrektur 2026-08-11: *"mag sein, aber es ist die selbe
ausgangsbasis"*.** Meine erste Fassung unten klang wie ein Validitaetsmangel.
Sie ist es nicht:

- Die **Ausgangsbasis ist identisch** -- gleicher Seed, gleiche Fabriken,
  gleiche Auslage, gleiche Wertungsplatten. Alles, was danach abweicht, ist
  WIRKUNG des Eingriffs und nicht Stoerung. Genau das will ein gepaarter
  Versuch.
- Der verschobene RNG-Strom ist **unkorreliert mit der Spielqualitaet** -- kein
  Arm wird dadurch systematisch besser bedient. Das kostet PRAEZISION (die
  Paarung ist weniger eng als gemeinsame Zufallszahlen), nicht Gueltigkeit.
- `determinize_hidden_information` arbeitet auf der SUCH-Kopie des Zustands
  (`&mut GameState` des Suchbaums), nicht auf der laufenden Partie. Die Suche
  mischt also nicht das echte Material, sie verbraucht nur Ziehungen.

Die technische Beschreibung bleibt stehen, weil sie fuer das REPLAY entscheidend
ist -- dort ist sie ein hartes Hindernis, nicht bloss Varianz.

## Technischer Hintergrund

"Gepaart mit selbem Seed" ist schwaecher als es klingt: Suche und Spielzustand
teilen dasselbe RNG (`self_play.rs:1523`, `net_mcts.rs:620`,
`supply.rs:43`). Sobald ein Arm anders spielt, verschiebt sich der RNG-Strom und
damit die FLIESENVERSORGUNG -- die Arme spielen dann unterschiedliches Material,
nicht nur unterschiedliche Zuege. Der gleiche Seed bleibt eine Varianzreduktion,
ist aber KEINE gemeinsame Zufallszahlenfolge. Gilt fuer alle Sweeps dieses
Instruments.

---

## Nachtrag 2026-08-11 (abends): drei Punkte, einer davon eine Prozess-Schuld

### N1. Der kriterienweise Aufbau — NACHTRÄGLICH registriert, und das ist ein Mangel

Der Versuchsaufbau nach Nutzer-Plan (*"20 ausgesuchte spiele in denen die
vertikalen wertungsplatten aktiv sind nur mit alpha variation der vertikalen
platten"*) wurde **gefahren, bevor er hier stand**. Ich halte das ausdrücklich
als Mangel fest, statt es zu glätten: die Konfigurationen `k0`..`k7` (je
`alpha[k]=1`, Rest 2, w=1,0) und die Dosis-Reihe `w0/w003/w01/w03/uni` sind
damit **exploratorisch**, nicht konfirmatorisch. Was daraus folgt: die dort
gefundenen Effekte begründen Hypothesen, sie bestätigen keine. Eine Bestätigung
braucht frische Seeds.

Festgehalten ist der Aufbau trotzdem, weil er weiterläuft: 57 Seeds aus
`seed_auswahl_platten.json`, gepaart über den Seed, 400 Netz-Sims gegen
150 Heuristik-Sims, Kriterium 4 als Null-Kontrolle (alpha dort additiv
wirkungslos).

### N2. Self-Play: das Shaping-Gewicht JE PARTIE streuen (Nutzer-Auftrag)

> *"nimm als hinweis fürs self play mit, dass wir je spiel auch das gewicht des
> wertungsplattenshapings anpassen sollten. dann bekommt der ownership head
> ordentlich was zu sehen"* / *"dann ziehen die spiele mal mehr und mal weniger
> richtung wertungsplatten"*

Warum das sauber ist und nicht die Labels verdirbt: die Ownership-**Ziele** sind
die realisierten Endzustands-Feldlabels der 36 Kuppelfelder. Die sind bei
**jedem** `w` korrekt — variiert wird allein die Zustandsverteilung, aus der
gelernt wird, nicht die Beschriftung. Ein fester Wert erzeugt einen Korpus mit
genau einem Platten-Affinitätsniveau; der Kopf sähe nie, wie ein Brett aussieht,
das stark auf Platten spielt, und nie, wie eines aussieht, das sie ignoriert.

Umsetzung (noch nicht gebaut): `w` je Partie aus dem Partie-Seed ableiten, damit
es reproduzierbar bleibt, über einen Bereich, der von "aus" bis "deutlich
ziehend" reicht. Die Grenzen setzt die Dosis-Kurve, sobald sie einen brauchbaren
Bereich zeigt — heute zeigt sie noch keinen (siehe N3).

### N3. Der bessere Term war schon da (Nutzer-Hinweis, und er trifft)

> *"du kannst auch bei der heuristik reinschauen wie es gemacht wurde. brauchst
> nicht immer das rad neu erfinden"*

GEPRÜFT: `tiling_solver.rs:556` `solve_round_final_score_endaware` mit
`solve_rec_endaware` (`tiling_solver.rs:519-546`) rollt über `legal_steps` die
Musterreihen auf die Kuppel und maximiert am Blatt **Platzierungspunkte +
`calculate_end_scoring`** — Letzteres enthält die Wertungsplatten. Damit ist der
Musterreihen-Bezug exakt statt geschätzt: Farb-, Sperr- und Slot-Bedingungen
kommen aus dem echten Tiling, und die Ein-Fliese-pro-Musterreihe-Schranke ergibt
sich von selbst. `alpha` wird dort gegenstandslos, weil der Fortschritt
realisiert und nicht hochgerechnet wird.

Der Doku-Vorbehalt "nur für Runde 5 sinnvoll" sticht beim Shaping nicht: dort
ist `calculate_end_scoring` exakt, in Runden 1-4 eine Näherung — und eine
Injektion braucht Richtung, nicht Exaktheit. Offene Frage ist allein der PREIS
pro Blatt; das ist zu messen, nicht zu schätzen.

**Damit stehen zwei Kandidaten für denselben Zweck**, und die Messung entscheidet:
- `MOSAIC_MUSTERREIHEN_W` — nachgebaute Bereitschaft je Zelle (geschätzt, billig)
- ein noch zu bauender Knopf auf Basis von `solve_round_final_score_endaware`
  (exakt, Preis unbekannt)

---

## N4. DER ISOLIERTE AUFBAU DES NUTZERS — vorregistriert VOR dem Lauf (2026-08-11, 23:5x)

**Anlass**: Nutzer-Rueckfrage *"bist jetzt schon mal meinen sweep gefahren wo nur
ein alpha pro wertungsplatte variiert wird und die anderen gewichte auf w=0"* —
**nein, war er nicht.** Die Laeufe `k0`..`k7` variierten nur den Exponenten,
das GEWICHT stand dabei auf 1,0 fuer alle acht Kriterien gleichzeitig
(`net_mcts.rs:1104`: ein einzelner Wert in `MOSAIC_WERTUNG_SHAPING_W` verteilt
sich auf alle acht Stellen). Damit war jede Platte injiziert und die Kriterien
konfundiert. Zweiter Vorfall desselben Musters an einem Tag (vgl. *"das war aber
nicht mein testsetup"*).

### Aufbau

Je Kriterium k in 0..7 **ein** Satz Partien, und zwar nur die, in denen diese
Platte AKTIV ist (`scoring_tile_ids` enthaelt k) — 20 bis 23 Seeds, Listen in
`evaluations/seeds_je_kriterium/k<k>.txt`, abgeleitet aus `platten_w0`.

- `MOSAIC_WERTUNG_SHAPING_W` = Achterform, **0 ueberall ausser Stelle k = 1,0**
- `MOSAIC_WERTUNG_ALPHA` = Achterform, Stelle k variiert, Rest 2 (wirkungslos,
  weil Gewicht 0)
- alpha[k] in **{0,5 / 1 / 2 / 4}**. Begruendung der Spanne: fuer x<1 sinkt
  x^alpha mit steigendem alpha. alpha<1 (konkav) verteilt Gutschrift breit, schon
  eine Fliese in einer Linie zaehlt viel; alpha>1 (konvex) zahlt fast nur an
  BEINAHE fertige Linien. Die Frage *"ab welchem Wert zieht das Spiel mehr in
  diese Richtung"* braucht also Punkte auf beiden Seiten von 1.
- 400 Netz-Sims gegen 150 Heuristik-Sims, gepaart ueber den Seed.
- **Nullpunkt** ist keine eigene Bahn: `platten_w0` auf dieselben Seeds gefiltert.
- **OHNE** den Strafleisten-Gegenterm. Nicht aus Nachlaessigkeit: er ist ein
  zweiter Faktor mit eigener, inzwischen gemessener Wirkung (+2,77 Punkte,
  t=2,21) und wuerde die alpha-Ablesung konfundieren. Der Aufbau des Nutzers hat
  ihn nicht enthalten.

### Zwei Schwellen, und beide sind vorab benannt (Nutzer-Wortlaut *"ab wann wertungsplatten gebaut werden und ab wann die punkte wieder kippen"*)

1. **Zieht es?** Punkte DER PLATTE k selbst, aus der Log-Aufschluesselung
   (`tools/plattenpunkte_aus_arena.py`), gegen den Nullpunkt auf denselben Seeds.
2. **Kippt es?** Endstand gegen den Nullpunkt auf denselben Seeds.

Der gesuchte Bereich ist der, in dem (1) steigt, bevor (2) faellt. **Vorab
festgehalten: es kann sein, dass es ihn nicht gibt** — die Dosis-Kurve mit
uniformem Gewicht hatte keinen (was sanft genug war, um nicht zu schaden, war zu
sanft, um zu helfen). Dieser Aufbau kann das nur pro Kriterium anders
entscheiden, nicht die Ursache beheben: `player_scoring_features` liest die
Musterreihen nicht.

### Kriterium 4 ist die NULL-KONTROLLE

Kriterium 4 (Aeussere Felder) ist additiv und linear, alpha wirkt dort nicht.
Eine flache Reihe ueber alle vier alpha-Werte ist die Bestaetigung, dass die
Messkette sauber ist; eine nicht-flache waere ein Fehler in der Kette.

### n ist klein und das wird nicht weggeredet

20 bis 23 Partien je Zelle, 32 Zellen. Bei einer Seed-Skala von 5,75pp bei n=400
ist das explorativ: der Aufbau taugt, eine RICHTUNG und eine Groessenordnung zu
zeigen, und ein gefundenes Fenster muss auf frischen Seeds wiederholt werden,
bevor es in eine Entscheidung eingeht.

---

## N5. NUTZER-ORAKEL — Zielwerte VOR den Zahlen festgelegt (2026-08-11)

**Wortlaut**: *"ich mach uns nun das orakel: wenn der exponent gut gewählt ist,
sollten wir bei den vertikalen wertungsplatten >= 14 punkte schaffen. bei den
eckplatten >= 11. bei den diagonalen >= 1. bei den mehrfarbigen >= 8. bei den
horizontalen >= 2."*

Geprueft und festgehalten: zum Zeitpunkt dieser Eintragung existierte **keine
einzige** `paired_arena_env_iso_*.json`. Die Vorhersage ist damit echt vorab.

Groesse ist dieselbe wie in der Messtabelle: **Plattenpunkte des Netz-Spielers,
Mittel ueber die Partien, in denen diese Platte aktiv ist**, gezogen aus der
Log-Aufschluesselung durch `tools/plattenpunkte_aus_arena.py`.

| k | Kriterium | Nullpunkt (w=0, gemessen) | **Nutzer-Ziel** | Faktor | entspricht etwa |
| - | --------- | ------------------------: | --------------: | -----: | --------------- |
| 1 | Vertikale Reihen | 0,70 | **>= 14** | 20x | 2 geschlossene Spalten (je +7) |
| 5 | Eckplatten | 3,14 | **>= 11** | 3,5x | eine kleine + eine grosse Eckplatte (3+8) |
| 3 | Mehrfarbige Felder | 5,40 | **>= 8** | 1,5x | -- |
| 0 | Horizontale Reihen | 0,78 | **>= 2** | 2,6x | 2/3 einer Reihe (je +3) |
| 2 | Diagonale Reihen | 0,43 | **>= 1** | 2,3x | jede 10. Partie eine Diagonale (+10) |

Nicht benannt und damit ohne Zielwert: Farbenreiche Reihen (7), Aeussere Felder
(4, Null-Kontrolle), Spezialfelder (6).

### Was ein Fehlschlag BEDEUTET, auch vorab festgelegt

Diese Zielwerte sind mit dem Plattenterm ALLEIN vermutlich nicht erreichbar, und
das ist der Wert des Orakels: `player_scoring_features` liest ausschliesslich das
Kuppelraster und hat null Bezuege auf `pattern_lines` (geprueft). Der Term ist
damit innerhalb einer Runde fuer jeden Drafting-Zug identisch. Verfehlt der Sweep
die Ziele bei JEDEM alpha, ist das ein **Falsifikationsbefund gegen den Term**,
nicht gegen die Zielwerte -- und die Begruendung, den Musterreihen-Bezug
(`MOSAIC_ENDAWARE_W`) als Traeger zu nehmen. Trifft er sie, war meine
Struktur-Diagnose zu eng und der Exponent der fehlende Freiheitsgrad.

**Ausdruecklich kein Hintertuerchen**: >= 14 heisst >= 14, nicht "deutlich
gestiegen". Ein Teilerfolg (z.B. 3 statt 0,70 bei den vertikalen Reihen) wird als
VERFEHLT berichtet und die Steigerung getrennt genannt.

Der horizontale Zielwert ist der einzige, bei dem ich einen strukturellen
Vorbehalt anmelden muss: Rasterreihe *r* wird nur von Musterreihe *r* gefuettert
(`round_end.rs:20-22`), also hoechstens eine Fliese pro Runde. >= 2 Punkte im
Mittel (2/3 einer Reihe a +3) bleibt damit erreichbar, eine ganze Reihe waere es
ohne Spezialfeld nicht.

---

## N6. KORREKTUR DES ORAKELS — meine Umrechnung war falsch (2026-08-11)

Nutzer-Praezisierung: *"nicht zusammenrechnen. es geht um die einzelabschaetzung
je variation von alpha. dann sollten zwei reihen moeglich sein (2 spezialfliesen
im obersten raster und dann sollte es gehen wenn fokus drauf gelegt wird) und
eine diagonale."*

**Zwei Zielwerte in N5 waren ANZAHLEN von Linien, nicht Punkte.** Ich hatte sie
als Punkte gelesen und daraus Bruchteile abgeleitet ("2/3 einer Reihe", "jede 10.
Partie eine Diagonale") -- beides falsch in der Sache. In Punkten werden die Ziele
damit **haerter**:

| k | Kriterium | Nullpunkt | N5 (falsch) | **GUELTIG** | Faktor | Rechnung |
| - | --------- | --------: | ----------: | ----------: | -----: | -------- |
| 1 | Vertikale Reihen | 0,70 | >= 14 | **>= 14** | 20x | 2 Spalten a 7 |
| 2 | Diagonale Reihen | 0,43 | ~~>= 1~~ | **>= 10** | 23x | 1 Diagonale a 10 |
| 5 | Eckplatten | 3,14 | >= 11 | **>= 11** | 3,5x | 3 + 8 |
| 3 | Mehrfarbige Felder | 5,40 | >= 8 | **>= 8** | 1,5x | -- |
| 0 | Horizontale Reihen | 0,78 | ~~>= 2~~ | **>= 6** | 7,7x | 2 Reihen a 3 |

Punktwerte geprueft an `scoring.rs:165-179`: Reihe 3, Spalte 7, Diagonale 10,
Eckplatten 3/3/8/8, Spezialfelder -3 je leerem Feld.

**"Einzelabschaetzung je Variation von alpha"**: jeder Zielwert gilt fuer SEIN
Kriterium in SEINEM Sweep-Satz, bei mindestens einem der vier alpha-Werte. Nicht
summieren, nicht gegeneinander aufrechnen.

### MEIN STRUKTUR-VORBEHALT ZU DEN HORIZONTALEN REIHEN IST WIDERLEGT

Ich hatte in N5 notiert, eine ganze horizontale Reihe sei ohne Spezialfeld nicht
schliessbar, weil Rasterreihe *r* nur von Musterreihe *r* gespeist wird
(hoechstens eine Fliese je Runde, also 5 von 6 Feldern in 5 Runden). Der Nutzer
hat den Weg genannt, und er ist am Code belegt -- `dome.rs:54-59`:

    pub fn is_filled(&self) -> bool {
        match self.space_type {
            SpaceType::Special => self.placed_special,
            _ => self.placed_color.is_some(),
        }
    }

**Ein ausgeloestes Spezialfeld FUELLT die Rasterzelle.** `check_special_trigger`
(`round_end.rs:322-324`) setzt `placed_special = true`, und `is_filled` zaehlt das
fuer Special-Felder als belegt -- also auch in `row_fill`. Mit zwei Spezialfeldern
in der obersten Rasterreihe braucht diese nur noch vier Lieferungen aus
Musterreihe 0, und die hat Kapazitaet 1 (`board.rs:31-33`), wird also in jeder
Runde fertig. Zwei horizontale Reihen sind damit erreichbar.

Die ANZAHL Spezialfelder je Rasterreihe ist layoutabhaengig: jede der 9
Kuppelplatten traegt genau ein Special-Feld (`round_end.rs:318-319`: "exakt 9
Kuppelplatten tragen einen Special-Slot und es gibt exakt 9 Special-Fliesen"), und
ob es in der oberen oder unteren Haelfte der Platte sitzt, entscheidet, in welche
der beiden Rasterreihen es faellt. Bis zu drei je Rasterreihe sind moeglich.

**Folge fuer die Auswertung**: der horizontale Zielwert bekommt KEINEN Vorbehalt
mehr angehaengt. Verfehlt er, ist das ein Befund und keine Struktureigenschaft.

### HERKUNFT DER LAEUFE, damit die Akten stimmen

Nutzer-Frage *"wer hat diesen test beauftragt?"* zum `MOSAIC_ENDAWARE_W`-Term:
**ich, unbeauftragt.** Die Nutzer-Aeusserung war eine Korrektur an meinem
Vorgehen ("brauchst nicht immer das rad neu erfinden"), kein Messauftrag. Daraus
habe ich einen Knopf gebaut und drei Laeufe gestartet (`ea01`, `ea03`, `mr01`),
die Kerne belegten, WAEHREND der beauftragte isolierte Sweep noch nicht gefahren
war. Beauftragt waren: die Strafleisten-Gegenprobe (*"aber ja probier es aus"*),
der isolierte Sweep (N4) und der lambda-Sweep. Nutzer-Entscheid auf die Frage, ob
abgebrochen wird: *"nein lass nur laufen."*

---

## N7. ARBEITSAUFTRAG: Koeffizienten fuer 14 Punkte auf den vertikalen Platten (2026-08-11)

**Nutzer-Auftrag**: *"Optimiere die injektion bis wir bei den vertikalen
wertungsplatten koeffizenten gefunden haben um die 14 sonderpunkte zu erreichen.
sollte nicht so schwer sein."*

**Zuschnitt (Nutzer-Praezisierung)**: *"von den koeffizienten darfst w und alpha
angreifen. vom coder der blattbewertung her sollte nicht mehr allzu viel fehlen.
da ist die strafleiste und musterreihe ja schon drinnen."*

Also: gesucht wird ueber `w[1]` und `alpha[1]`. `MOSAIC_WERTUNG_FLOOR_W` und
`MOSAIC_TILING_W` stehen FEST auf 1,0 -- sie sind Bestandteil der Blattbewertung,
keine Stellschrauben, und 1,0 ist genau ihre Gewichtung in `mcts.rs::player_total`
(alle drei Summanden mit Koeffizient 1).

### Der Musterreihen-Traeger ist jetzt der der Heuristik

Nutzer-Entscheid *"nichts davon"* zu meinen zwei Eigenbauten, und die Messung gab
ihm recht: `MOSAIC_ENDAWARE_W` bei w=0,1 gab -0,07 Punkte (t=-0,07), bei w=0,3
-2,16 (t=-1,21); `MOSAIC_MUSTERREIHEN_W` bei w=0,1 -0,84 (t=-0,69). Keiner hob die
Plattenpunkte. Traeger ist stattdessen `MOSAIC_TILING_W` mit

    solve_round_final_score(state, pi) - state.players[pi].score

also die aus den heutigen Musterreihen erreichbaren Platzierungspunkte plus feste
Strafen -- die unveraenderte Projektfunktion. Punktestand abgezogen (Nutzer-Wahl
"nur der Tiling-Anteil"), weil er fuer alle Geschwisterzuege gleich ist und
`tanh(pts/50)` saettigen wuerde. Die Differenz ist keine Erfindung:
`tiling_solver.rs:1069` prueft genau sie.

### ZWEI EIGENE FEHLER, die dieser Abschnitt festhaelt

**1. Ungepruefte Zahl in einer Rechnung (REGEL-0-Bruch).** Ich hatte behauptet,
Kriterium 1 liefere "typisch 2 bis 6 Punkte", und daraus die `w`-Spanne
abgeleitet. Nutzer-Rueckfrage *"wie kommst darauf. sie liefert ohne
wahrscheinlichkeit 7 punkte je vollständiger reihe"*. Gemessen an den 57
Endbrettern des Nullpunkts (Spalten aus den Platzierungszeilen rekonstruiert):

| Groesse | Wert |
| ------- | ---: |
| Median  | **12,25** |
| Mittel  | 12,27 |
| 10 %-Quantil | 9,53 |
| 90 %-Quantil | 15,36 |
| Min / Max | 7,39 / 16,72 |

**Untergrenze**, nicht exakt: Spezialfelder fuellen Zellen mit
(`dome.rs:54-59`), das Log nennt aber nur die REIHE des Bonus (+N Punkte = Reihe
N), nicht die Spalte. Der echte Wert liegt hoeher.

Folge: `tanh(w * P / 50)` saettigt bei **w ~ 10** allein aus diesem Term. Die
Spanne, mit der ich gestartet war ({1, 3, 10, 20}), lag mit ihren oberen zwei
Werten in der Saettigung. Der informative Bereich liegt **unter 1**.

**2. Verwechslung der beiden Wertungsfunktionen.** `calculate_end_scoring` ist
ALLES-ODER-NICHTS (`tile.score(player)`, `scoring.rs:136`); `wertung_progress` ist
der stetige Ersatz mit quadratischer Teilgutschrift, ausdruecklich "NICHT fuer die
echte Endwertung" (Doku `scoring.rs:150-158`). Die gemessenen 0,70 sind damit
ECHTE Punkte -- 0,1 Spalten je Partie, eine Spalte in jeder zehnten. Der
Nutzer-Zielwert 14 = 2 Spalten ist dieselbe Einheit. Die 12,25 oben sind dagegen
die Groesse des SHAPING-Terms und mit den 0,70 nicht vergleichbar.

### Aufbau: vollstaendiges Raster statt Tastsuche

Erst war eine dreiphasige Tastsuche geplant (klammern, Exponent, verfeinern).
Verworfen, weil eine Zelle auf der freien Maschine **1,1 min** kostet statt der
angenommenen 5: bei diesem Preis ist ein vollstaendiges Raster billiger als die
Absicherung gegen eine Greedy-Suche, die im lokalen Optimum haengenbleibt -- und
es liefert die ganze Antwortflaeche statt eines Pfades.

- `w[1]` in {0,03 / 0,1 / 0,3 / 1 / 3}
- `alpha[1]` in {0,25 / 0,5 / 1 / 2 / 4}
- 25 Zellen, je 20 Partien (die Seeds mit aktiver vertikaler Platte), 400 gegen
  150 Sims, gepaart ueber den Seed
- Metrik: Plattenpunkte des Kriteriums 1 aus der Log-Aufschluesselung. Ziel >= 14.
- Mitberichtet je Zelle: Endstand, Gesamt-Plattenpunkte, Strafleiste, Siegquote --
  damit nicht nur "erreicht" dasteht, sondern auch, was es gekostet hat.

**Erste zwei Zellen liegen schon vor** (aus der abgebrochenen Tastsuche, Dateien
bleiben erhalten): w=1/alpha=2 und w=3/alpha=2 geben beide **vertikal 0,70**, also
exakt den Nullpunkt, bei Endstaenden von 48,90 und 46,45 gegen 53,30. Beide kosten
Punkte, ohne eine einzige Spalte zu bewegen.
