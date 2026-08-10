# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`** (ausgelagert 2026-08-09; dritte Runde 2026-08-10, siehe Kapitel dort. Erste Runde:
TASK-INDEX-Zeilen Platten-Intervention/τ-Annealing/v21-Fenster-Altstand/
Messset-Snapshot-Teil/#35b/λ/#37/frozen-Set-Neubau, Abschnitt NAECHSTE
SCHRITTE, Abschnitt OFFENES GATING (λ-Arm), Review-Punkte B+C; zweite
Runde: TASK-INDEX-Zeile Messset-Snapshot+v16/v17-Freigabe (jetzt
komplett erledigt), Review-Zeile A + Abgelehnt/erledigt-Sammelnotiz,
kompletter Abschnitt "AUS EXTERNEM REVIEW R2 2026-08-09" (E/F/G),
NACH-v21-QUEUE Punkt 1/E3b).

---

## TASK-INDEX (nur OFFEN/LAUFEND, Stand 2026-08-10)

| Task | Status |
|---|---|
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: Validierung braucht arena-ENTSCHIEDENE Paare; die WDL-Aera hat bisher nur ~3 (v20>v19, E3-Arme signifikant schlechter) -- unter dem 6-Paar-Standard der Policy-Orakel-Validierung. Kandidaten-Metriken (Brier auf frozen_v2, R5-Steigung) werden ab jetzt je Gating MITGEFUEHRT; Verdikt, sobald >=6 entschiedene Paare vorliegen. `PREREG_nach34_paket.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

**UEBERGABE_v21_spirale.md GELOESCHT 2026-08-10** (Nutzer-Auftrag). Zwei einmalige Inhalte sind vorher wortgetreu nach `archive/history.md` gesichert: der Generator des v21-Traegermanifests samt Seed 20260815 (die Manifest-DATEI in `data/` bleibt, ohne den Block waere nur die HERLEITUNG verloren) und die R5-Plattensteigungs-Reihe 0,086/0,273/0,349/0,457. Alles Uebrige war Dublette zu STATUS bzw. abgearbeitete Queue.

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT
**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die
v21-Task-Queue abarbeiten.** Der Zuschnitt ist nur festgehalten, damit
er spaeter nicht neu diskutiert werden muss.

`PREREG_v22_fenster.md`: gleiche Form wie v21 (5.800 Policy / 23.650
Value / 29.450 gesamt), alles altert eine Stufe. Juengster Value-Posten
= **3.550 v19wdl-Rest (@600, vollstaendig) + 1.450 v19wdlsw** statt
5.000 Schwarm -> Schwarm-Anteil bleibt bei 74% statt auf 89% zu
steigen. **Ab v22 ist die Rotationsregel stationaer** (v21 war die
letzte Uebergangsgeneration). Vorbehalt fuer v21-Gating-H0: neuer
Batch desselben Generators braucht ein Suffix (`v20wdlb`).


### WERTUNGSPLATTEN-ANTEIL -- Domaenenwissen ausgelagert 2026-08-11

**Der Inhalt dieses Abschnitts steht jetzt in `../docs/domaenenwissen.md`**
(Nutzer-Entscheid: STATUS traegt "nur AKTUELLES und OFFENES" und wird
regelmaessig in die History geleert -- Domaenenwissen dort wird mitarchiviert).
Dort: Punktquellen und ihre Verwechslungsfalle, Plattenwerte samt
Index-Verschiebung Handbuch/Code, Versorgungszahlen, Musterreihen-Durchsatz,
Slot-Gradient, Mensch-gegen-Champion-Posten.

**Was hier bleibt, ist die ENTSCHEIDUNGSRELEVANTE Folge**: die 7-%-Zahl war ein
Mittelwert ueber schwaches Self-Play und hat mich zu einer falschen Priorisierung
gebracht. Im obersten Fuenftel sind es 24,7 %, beim Nutzer 28 %; der Mittelwert
ist klein, WEIL das Defizit im Self-Play symmetrisch ist. Und die Platten sind
kein getrennter Topf -- eine geschlossene Spalte bringt 21 Platzierungspunkte
PLUS 7 Plattenpunkte. Der Plattenterm ist deshalb **kein kleinerer Hebel neben**
der rundenuebergreifenden Planung, sondern deren einzige verfuegbare Umsetzung:
`w` ist eine echte Sweep-Frage, und der Term gehoert nach dem Training ins
GATING.

### STAND 2026-08-10 NACHTS

**Champion unveraendert: `v21_2d_brierbest`, Elo 1358** [1292, 1434].
Verdikte des Tages liegen in `../archive/history.md`, Kapitel 2026-08-10
(Task D, ISMCTS-k, Punkte-Blend `w>0`, #82, GPU-Verlagerung T1+T2,
R5-Chip-Leck, Schema 20, `plate_head` entfernt, Kriterium-3-Multiplikator,
Wheel+Golden-Waechter, Plattenkopf-Strang, Konfundierungs-Muster).

#### LAEUFT JETZT

| Bahn | Was | Dauer |
|---|---|---|
| **CPU+GPU** | `train.py --name v21_2d_own02 --load v21_2d_brierbest --encoder 2d --value-head wdl --select-by-brier --conjunction-head --ownership-weight 0.2 --lr 5e-5 --lr-schedule cosine --seed 20260910`, mit `MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v21.json` | Cache-Neubau ~3 h (Schema 20 + `+conj_v2` gebuendelt), dann Training ~3,5 h |
| **offline** | Agent: Formungsterm in den Netz-Pfad (eigene Funktion neben `wertung_progress`, Knopf `MOSAIC_WERTUNG_SHAPING_W` Default 0) | -- |

**Fenster verifiziert**: 2.945 Dateien in `data/` = der vorregistrierte
v21-Zuschnitt dateigenau (545 v18, 400 v19wdl, 400 v20wdl, 800 v19wdlsw,
800 v20wdlsw), davon 2.651 Train / 294 Val. **Anzeigefehler beachten**: die
Spielzahl im Log wird aus dem `_g<N>`-Zaehler im DATEINAMEN geschaetzt und
meldet fuer v18 6.000 statt der vorregistrierten 5.450 -- Gesamtsumme im Log
30.000 statt 29.450. Keine Fensterdrift, die Dateizahl passt exakt.

#### OWNERSHIP-KOPF -- Zuschnitt vollstaendig entschieden (Nutzer 2026-08-10)

Der Kopf hat **zwei unabhaengige Verwendungen**, und die erste stand von
Anfang an in `config.py`, wurde aber nie gemessen:

1. **HILFSZIEL** (Original-Begruendung): die besten Checkpoints lagen bei
   v15/v16/v17 stets in Epoche 1-3 -- es fehlt lernbares SIGNAL je Sample,
   nicht Sample-Anzahl. Der Kopf liefert 140 Gradienten je Position statt
   eines Skalars. **Laeuft jetzt** mit Gewicht 0,2. Kein Sweep
   (Task-D-Praezedenz: alle Arme H0); Aufwand gehoert in >=6 gepaarte Seeds.
   Entschieden an Prior-Masse Top-3 + Kendall-Tau (7/7), nicht `val_brier`.
2. **AUSLESE fuer die Blattbewertung** -- Spezifikation in
   `PREREG_plattenkopf.md`. **Zuletzt**, weil erst nach einer
   Verhaltensaenderung beantwortbar (s.u.).

**Aufbau** (`neural_net.py`, `_ownership_from_dome` + `_conjunctions_from_dome`):
ein gemeinsamer Kopf `Linear(hidden,128) -> ReLU -> Linear(128,140)`, rohe
Logits, `BCEWithLogits`, **elementweises Mittel ueber die unmaskierten
Spalten** (-1 = maskiert), kein eigenes Gewicht fuer die Zusatzziele.
Bewusst ZULETZT deklariert -> Gewicht 0 ist byte-identisch zum Stand ohne Kopf.

- **Block 1, 72 Feldlabels** (36 je Spieler): "Feld am Ende belegt",
  slot_row-major dann space_index, ego-perspektivisch. Rasterabbildung
  `grid[sr*2 + si//2][sc*2 + si%2]` wie `scoring.rs::build_grid`. Deckt die
  ADDITIVEN Kriterien 4 (+1 je Randfeld) und 6 (-3 je leerem Spezialfeld)
  exakt ab, weil dort `Summe P(Feld)` der Erwartungswert ist.
- **Block 2, 68 Zusatzziele** (34 je Spieler): 0-5 Reihe voll (+3), 6-11
  Spalte voll (+7), 12-13 Diagonale voll (+10), 14-17 Eckplatte voll
  (+3/+3/+8/+8), 18 alle Jokerfelder (2 x wild_total), 19-24 Reihe mit >=5
  Farben (+4), **25-33 Layout** (Slot traegt Jokerplatte -> E[wild_total]).
  Damit sind alle acht Kriterien abgedeckt.

**Gemessener Zustand** (`tools/atom_skill_check.py`, bedingt gerechnet):
Block 1 ist gesund -- **0 von 36 Feldern entartet**, niedrigste Grundrate
0,072. Block 2 ist zur Haelfte tot -- 16 von 34 konstant, und zwar genau die
teuren: Diagonalen 0,000, Spalte 1 0,004, Reihen 5/6 0,000, untere Eckslots
0,002/0,004. Wo die Konjunktion tot ist, LEBT die Zelle: Diagonale 0,428/0,321,
Spalte 1 0,421. **Traeger sind die Zellen, nicht die Konjunktionen.**

**Die toten Spalten bleiben drin** (Nutzer-Entscheid) -- sie kosten nichts
(gesaettigte BCE-Spalten liefern keinen Gradienten), ein Ausbau wuerde
Kopfbreite und ONNX-Vertrag aendern, und sie sind ein **kostenloser
Fortschrittsmesser**: Grundrate 0,000 heisst "kommt in diesem Korpus nicht
vor". Steigt sie, hat sich das Verhalten geaendert -- arena-unabhaengig, ohne
Training, je neuem Korpus einmal auslesen.

#### DER EIGENTLICHE BEFUND: der Formungsterm existiert und das Netz hat ihn nie bekommen

`scoring.rs:160` `wertung_progress` ist der vollstaendige
Wertungsplatten-Formungsterm: gegatet auf die AKTIVEN Platten, je Geometrie
einzeln summiert, konvex mit Exponent 2, additive Kriterien linear.

**KORREKTUR 2026-08-10 (Agent-Fund, selbst am Code geprueft): das Netz hat
ihn NICHT "nie bekommen".** Ich hatte "haengt ausschliesslich an `mcts.rs:82`,
dem Heuristik-Pfad" behauptet -- falsch. Es gibt **Task #93 "Plattenshaping"**
in `net_mcts.rs`: `PLATE_SHAPING_ENABLED = false` (Kompilierzeit),
`PLATE_SHAPING_WEIGHT = 0.3`, A/B nicht signifikant (p=0,71), deshalb aus.

Zwei Gruende, warum dieses p=0,71 die EGO-Fassung nicht vorwegnimmt:

1. **#93 ist MARGINAL, nicht absolut.** `plate_shaping_marginal =
   plate_shaping_delta(kind) - plate_shaping_delta(eltern)` -- es verschiebt
   den Knotenwert um den Zuwachs GENAU DES LETZTEN ZUGS. Ein Blatt tief im
   Baum bekommt keine Gutschrift fuer den angesammelten Fortschritt seines
   Pfades. Eine Stellungsbewertung braucht aber den GESAMTSTAND ("diese Spalte
   steht bei 5/6"), nicht den letzten Schritt. Differenzformen sind
   potentialbasiert und lassen die optimale Politik strukturell unberuehrt --
   #93 konnte in dieser Form gar nicht wirken. (Herleitung, nicht gemessen.)
2. **#93 ist `mine - theirs`, gegatet, mit dem pauschalen
   `-3 * special_empty`** -- genau die drei Eigenschaften, die das
   Spezialfeld-Loch verfehlen. Und gemessen wurde gegen ein Geschwisternetz
   mit demselben blinden Fleck (wie das 97:103 in `elo_history.csv` Zeile 48).

Die Plattenluecke (Heuristik 1,99 Plattenpunkte je Partie gegen 1,10 beim
Champion) bleibt bestehen -- die Erklaerung ist aber nicht "Term fehlt",
sondern "Term liegt in einer Form vor, die den Stand nicht bewertet".

#### SPEZIALPUNKTE SIND REIHENABHAENGIG (1..6), NICHT 3 -- Nutzer-Ruege 2026-08-11

*"die spezialpunkte richten sich nach der reihe in der sie aktiviert werden.
notier dir das irgendwo fett. das hat schon so oft zu missverstaendnissen
gefuehrt."*

`round_end.rs::check_special_trigger`:

    let pattern_row = slot_row * 2 + sp_idx / 2;
    let bonus = (pattern_row + 1) as i32;      // 1..6, NICHT 3

Handbuch Abschnitt 5 bestaetigt es. **`bonus_points = 3` in `dome.rs` ist NUR
der Typ-Diskriminator** Special (`>0`) gegen Wild (`=0`) -- kein Punktwert, und
laut `PREREG_zufallsknoten.md` darf das Feld auch NICHT umgestellt werden (die
Platte kennt ihren Slot nicht, der Wert entsteht erst bei der Platzierung).
`board.rs::place_special_tile` gibt die flache 3 zurueck und ist dort schon als
**toter Code ohne Aufrufer** notiert.

**Strategisch ist das der Kern**: untere Slot-Reihe = Rasterreihen 5/6 = **5
und 6 Punkte**, obere = 1 und 2 Punkte. Das Spezialfeld bleibt unten in ~84 %
der Partien leer, oben in ~13 % -- **die KI laesst die teuersten liegen.**
Watchlist konsistent gelesen: Nutzer 10,3 Punkte auf 3,1 Freischaltungen =
**3,3 je Freischaltung**, KI 1,3 auf 0,6 = **2,2**. Eine Rechnung
"Freischaltungen x 3" ist falsch.

**ZWEI GETRENNTE PUNKTQUELLEN -- nicht verwechseln (ich habe es getan,
Nutzer-Ruege 2026-08-11):**

1. **⭐ Kuppel-Bonus = GRUNDWERTUNG**, `check_special_trigger`, Wert
   **1..6 je Rasterreihe**, zahlt IMMER unabhaengig von den aktiven Platten.
2. **Wertungsplatte 7 (Code-Index 6) = ENDWERTUNG**, Handbuch woertlich:
   *"⭐ Spezialfelder: -3 Pkt. je leer gebliebenem Spezialfeld"* -- **FLACH,
   Reihe egal**, zahlt nur wenn die Platte liegt.

`6 => -3.0 * sf.special_empty` in `wertung_progress` ist damit **KORREKT und
kein Fehler** -- ich hatte es als eingeebneten Wert bezeichnet, das war falsch.
`wertung_progress` bleibt unangetastet, weil es der Elo-Anker ist UND weil es
richtig rechnet.

Der neue Unlock-Term gewichtet entsprechend **zweigeteilt**: Bonus-Anteil
ungegatet mit `(reihe + 1)`, Kriterium-6-Anteil gegatet und flach 3.
Der Tiling-Solver rechnet korrekt (Test
`solver_counts_special_bonus_and_neighbor`: "Special-Bonus = Reihennummer").

#### OWNERSHIP-KOPF: KOMMT, offen ist nur der FAKTOR (Nutzer 2026-08-11)

*"wichtig der ownership head kommt so oder so. die frage ist nur mit welchem
faktor."* -- Die Existenzfrage ist damit entschieden und nicht wieder
aufzurollen. `OWNERSHIP_WEIGHT` ist die offene Groesse; laeuft derzeit mit 0,2.
Das ist eine EIGENE Sweep-Frage, getrennt von der Injektions-Dosis
(`PREREG_injektion_dosis.md`).

#### DREI STUFEN UND DAS ABSCHALTKRITERIUM (Nutzer-Diktat 2026-08-10/11)

Nutzer-Fassung: *"wir muessen nun der suche die realisierte groesse injizieren
damit ueberhaupt einmal die zuege in richtung der wertungsplatten angesteuert
werden. irgendwann mal lernt der ownership head, wird weitsichtiger und nimmt
einfluss auf das netz. dann koennen wir die (kurzblickende) injektion wieder
abschalten"* -- im Kern richtig, mit zwei Praezisierungen unten.

**Stufe 1 -- INJEKTION (die realisierte Groesse, nicht die Vorhersage).**
Die Suche maximiert Belegung, die im BRETT steht: `wertung_progress_alpha`
(Commit `40eb39b`, `MOSAIC_WERTUNG_SHAPING_W`) plus der gestufte
Spezialfeld-Freischaltterm (`MOSAIC_UNLOCK_SHAPING_W`), beide Default 0,
absolut und **JE SPIELER** (nicht ego-only -- Nutzer-Korrektur 2026-08-11:
*"du betrachtest bitte den ownership label vom gegner mit. die gumbal suche soll
ruhig auch die halbzuege des gegners sauber mit den ownership labels
betrachten."*).
GEPRUEFT an `net_mcts.rs:1188-1191`: `for i in 0..2` mit `state.players[i]`,
`out[i] = value[i] + shift` -- jeder Index aus dem EIGENEN Brett, kein
Cross-Term, keine Antisymmetrie. Ego-only wuerde der Suche unterstellen, der
GEGNER ignoriere die Platten -- die Self-Play-Blindheit innerhalb der Suche.
Ausdruecklich NICHT `mine - theirs`: eine Differenz verliert das Niveau (55:50
waere schlechter als 30:15) und war die Form von Task #93.
Freischaltwert GEPRUEFT an `scoring.rs:305-306`: `(sr*2 + sp_idx/2) + 1`, also
**1..6**; Kriterium-6-Anteil (`scoring.rs:320-322`) gegatet auf Platte 6 und
flach -3. `wertung_progress` bitgenau unberuehrt (`git diff 40eb39b..HEAD` auf
`scoring.rs` zeigt nur `+`-Zeilen). Commit `63a2eb0` + Folgecommit des Agenten;
Testzahl 344 gruen ist SEINE Angabe, von mir noch nicht nachgeprueft (laeuft vor
dem Wheel-Install).
**Kein Kopf beteiligt** -- die 36 Ownership-Labels sind
Brettfakten, exakt berechenbar. Das ist die Leiter aus dem Bootstrap-Kreis:
Suche realisiert -> Partien enthalten gefuellte Felder -> die Labels variieren
ueberhaupt erst -> der Kopf kann sie lernen.

**Stufe 2 -- DESTILLATION, und hier sitzt die Abschaltbarkeit.** NICHT der
Ownership-Kopf macht die Injektion entbehrlich, sondern der **POLICY-Kopf**:
sein Ziel ist die Besuchsverteilung, und die hat die Injektion verschoben. Er
lernt also, die Freischaltzuege von sich aus vorzuschlagen. Das funktioniert
sogar bei margen-blindem Value-Ziel -- der Policy-Kanal kopiert die Suche und
braucht das Siegsignal nicht.

**Stufe 3 -- OWNERSHIP-KOPF als HORIZONT-VERLAENGERUNG (Arm B).**
**Praezisierung**: dass der Kopf lernt, nimmt von sich aus KEINEN Einfluss --
er ist ein Ausgang. Seine Ausgabe muss im Blatt GELESEN werden, und das ist ein
eigener Bauschritt (heute liest die Blattbewertung `policy/value/moon/points/
opp_points`, fuer `ownership` gibt es keinen Konsumenten). Die Injektion sieht
nur so weit wie die Suche; die Marginalen reichen darueber hinaus -- das ist der
eigentliche Beitrag des Kopfes, nicht das Ansteuern selbst. Er ist damit die
zweite Stufe des Ausbaus, nicht das tragende Teil.

**ABSCHALTKRITERIUM (messbar, nicht nach Gefuehl):**
1. Steigt die **Prior-Masse des Netzes auf den Freischaltzuegen** von
   Generation zu Generation?
2. **Haelt die Freischaltrate, wenn das Gewicht gesenkt wird?**
Beides ja -> die Injektion ist destilliert und kann runter. Bricht die Rate mit
dem Gewicht zusammen -> das Verhalten haengt noch am Geruest, es bleibt stehen.

**MESSMITTEL, nicht die Arena-Siegquote gegen ein Geschwisternetz.** Beide
vorliegenden Null-Ergebnisse zu Platten-Interventionen sind gegen Netze mit
DEMSELBEN blinden Fleck gemessen -- Task #93 bei p=0,71 und das Gating in
`elo_history.csv` Zeile 48 bei 97:103, p=0,76. Gegen Gegner, die die
Spezialfelder ebenfalls liegen lassen, kann die Arena 9 Punkte je Partie nicht
sehen. Direkt zu messen sind deshalb **Freischaltrate und Spezialpunkte je
Partie** (Zielwerte aus der Watchlist: Nutzer 3,1 Freischaltungen und 10,3
Spezialpunkte, KI heute 0,6 und 1,3); als Arena-Kante taugt die **Heuristik**,
die mit `-3 * special_empty` wenigstens einen Spezialfeld-Term hat.

`wertung_progress` **NICHT ANFASSEN** -- es haengt am Elo-Anker. Das variable
alpha gehoert in eine eigene Funktion daneben (Schutz durch Konstruktion,
nicht durch eine Bedingung; `.powi(2)` und `.powf(2.0)` sind nicht garantiert
bitgleich).

**Reihenfolge** (umgekehrt zur naheliegenden): der Formungsterm braucht den
Kopf NICHT -- er lebt von den GEZAEHLTEN Feldern, `(k + (6-k)*p)/6` steigt mit
k fuer jedes p < 1. Also aendert er das Verhalten, dadurch fuellen sich die
Konjunktionen, und ERST DANN ist die Auslese ueber die Marginalen eine
beantwortbare Frage.

#### WARUM DAS NETZ NICHT PUNKTOPTIMIERT SPIELT (Nutzer-Frage 2026-08-10)

Nicht ein fehlender Kopf, sondern **das Ziel kennt die Marge nicht**. Das
Value-Ziel ist `values_wdl`/`wdl_outcome`, also Gewinnwahrscheinlichkeit: ein
Sieg mit einem Punkt zaehlt wie einer mit vierzig. Dazu die Selbstspiel-Falle
-- lassen beide Seiten die Platten liegen, kostet Liegenlassen keine
Gewinnwahrscheinlichkeit. Und `POINTS_UTILITY_WEIGHT = 0` samt `w = 0`
verwerfen BEIDE Punkte-Koepfe in der Blattbewertung: die Information wird
berechnet und weggeworfen.

Die Leiter kann das nicht sehen -- Heuristik-Anker und Vorgaenger-Champions
lassen die Platten ebenfalls liegen. Der Einzige, der es bestraft, ist der
Nutzer (7:3 gegen einen Champion mit Elo 1358).

Historische Ironie: VOR Schema 17 war das Ziel `tanh((own-opp)/SCALE)`, also
eine Marge. Der WDL-Wechsel hat v20 zum ersten WDL-Champion gemacht, war im
Gating also besser -- besser im Gewinnen gegen Gegner, die die Marge ebenfalls
ignorieren. Zurueck zur Marge ist deshalb der falsche Schluss; sie muss
DANEBEN stehen, nicht dagegen. Einziger Kanal dafuer:
`MOSAIC_POINTS_UTILITY_W` mit lambda <= 0,5 -- **nie gemessen**, alle
getesteten Arme lagen bei lambda >= 1,0 und damit jenseits des Kipppunkts, ab
dem die Formel 30:15 gegenueber 55:50 bevorzugt.

#### OFFEN

| Punkt | Stand |
|---|---|
| **lambda-Arm** `MOSAIC_POINTS_UTILITY_W=0.1` + `MOSAIC_AGGR_LAMBDA=0.1` | nie gemessen, braucht den opp-Kopf; Arena, deshalb NICHT parallel zum Cache-Neubau |
| **Formungsterm Arm A/B** | Arm A = `wertung_progress` ins Netz-Blatt (Zaehler = belegte Felder). Arm B = derselbe Term, Zaehler + Ownership-Marginalen der OFFENEN Felder. Eine Zeile Unterschied; der Kontrast isoliert den Kopf-Beitrag. Kontrolle auf dem aktuellen Brett ist PFLICHT, sonst ist ein Sieg nicht interpretierbar (Task #5 hat Formung auf dem aktuellen Brett als folgenlos gemessen). |
| **Wheel + Paritaetsprobe** | nach dem Agenten-Commit faellig; **nicht** waehrend des laufenden Trainings installieren. Probe muss `8c6684ff...` liefern. |
| Zufallsknoten INNERHALB der Runde | Kuppelstapel als aufgezaehlter Knoten am Aufdecken, Kostentor in Runde 1. Danach kann der Shuffle raus (Determinismus-Gewinn). `MOSAIC_STACK_DRAW_CHANCE`, Default aus -- gehoert ins naechste Self-Play. |
| Stapelzug fuers NETZ | braucht Self-Play mit den Infos; laut Nutzer-Entscheid hinter der v21-Queue. Wird jetzt ueber die Wahrscheinlichkeit geloest, nicht als eigener Task. |
| Bootstrap-Horizont | gegatet auf Generierungsstart, keine Batcher-Entlastung (+25 % gelten unveraendert) |
| GPU-Verlagerung Weg V | Umsetzung offen, Startwert N=256 |
| `player_profiles.json.bak` | untracked, gemeldet, NICHT angefasst |

(#29 und #31/#38/#39 stehen im TASK-INDEX oben bzw. unten im Detail.)

## GELTENDE REGELN (kompakt)

- **Seed-Skala der Arena bei n=400 (gemessen 2026-08-09)**: dieselbe
  Konfiguration (k=1, Champion@600 vs Heuristik@150dyn) ergab **76,0%**
  mit Basis-Seed 20260820 und **81,75%** mit 20260828 -- **5,75
  Prozentpunkte allein durch den Seed**. Das ist groesser als die
  meisten Effekte, die wir messen (λ, k=2, Denial-Varianten liegen alle
  darunter). Folge: **ungepaarte Vergleiche zwischen zwei Laeufen sind
  wertlos**, auch wenn beide n=400 haben. Jeder A/B braucht identische
  Basis-Seeds im SELBEN Instrument; wo zwei getrennte Laeufe noetig sind
  (unterschiedliche Sim-Budgets), muss der Basis-Seed gleich gesetzt und
  die Paarung ueber den Spielindex selbst gerechnet werden.

- **Champion**: `v21_2d_brierbest` seit 2026-08-09, **Elo 1358**
  [1292, 1434] (Vorgaenger `v20_2d_opp_brierbest` 1295). Die
  Erst-Schaetzung nach dem Gating (1416, CI +-92) beruhte auf einer
  einzigen Gegnerkante; mit Anker- und Champion-2-Kante sinkt das
  Niveau auf 1358 und das CI wird 23% enger (+-71) -- der ABSTAND zum
  Vorgaenger (+63) bleibt. Belegt den Wert von
  Promotions-Checkliste Punkt 3+4. Gating 75:45
  (SPRT-H1 nach 60 Paaren, p=0,0059) UND Frisch-Seed-Replikation 97:63
  (H1 nach 80 Paaren, p=0,0095) -- die Fruehstopp-Regel ist damit
  erfuellt. Alt-Messset-Brier 0,18636 vs 0,18749. **Erster Champion aus
  reiner Korpus-Skalierung**: identisches Rezept, +40% Fenster
  (29.450 Partien) von einem staerkeren Generator, plus
  `--endgame-head`. champion.txt gesetzt (wirkt nach Server-Neustart).
  Generator-Naming: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.
- **Fenster-Pinning -- ZWEI Variablen, nicht eine (verschaerft
  2026-08-09 nach einem Beinahe-Fehler)**: Ein Trainingsstart im
  v21-Fenster braucht BEIDE:
  ```
  export MOSAIC_DATA_EXCLUDE="$(cat evaluations/v21_exclude_regex.txt)"
  export MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_v21.json"
  ```
  `MOSAIC_CARRIER_MANIFEST` wurde beim `t_d_vw08`-Start VERGESSEN. Der
  Default ist `policy_carrier_manifest_v20.json`, also ein ANDERER
  Traeger-Satz: der Arm haette mit einer anderen Policy-Maske als
  `t_d_vw04` und als `v21_2d` trainiert und waere als Sweep-Arm wertlos
  gewesen -- ohne Fehlermeldung, nur mit plausiblen Zahlen. Der Lauf
  wurde gestoppt und korrekt neu gestartet; ein angefangener
  Falsch-Cache war noch nicht auf der Platte.
  **Verifikation ist Pflicht und zwar VOR dem Weggehen**: die
  Cache-Zeile muss `📦 Lade HDF5-Cache (2651 Dateien)` lauten.
  Steht dort `Lade Daten aus 2651 Dateien...`, ist der Cache-Schluessel
  anders -- Lauf sofort stoppen und die Ursache klaeren, NICHT einen
  Neubau durchlaufen lassen (er zementiert das falsche Fenster).
  Beweisweg fuer die Ursache (bei Bedarf wiederholbar): Cache-Key aus
  `str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+...+carriers`
  nachrechnen und mit den `data/.cache_*.h5`-Namen vergleichen -- die
  v21-Caches sind `26e304f5d2c7` (train, 2.651 Dateien) und
  `8a04a7143bbe` (val, 294). Merke: der **Cache-Key ist der einzige
  Waechter** ueber die Traeger-Wahl, das Lauf-Manifest protokolliert
  `MOSAIC_CARRIER_MANIFEST` NICHT (`engine_config`/`python_constants`
  waren zwischen richtigem und falschem Lauf identisch).
  Harmlos dagegen: die 55 archivierten v18-Dateien sind seit 10:16 aus
  `data/` heraus, `MOSAIC_DATA_EXCLUDE` schliesst nun 0 statt 55
  Dateien aus -- Split und Dateiliste sind trotzdem BEWEISBAR identisch
  (rekonstruiert und verglichen: 2.651/294 in beiden Faellen gleich).
- **NACHSCHUB BEI GATING-FEHLSCHLAG -- KORRIGIERTE FASSUNG
  (Nutzer 2026-08-09)**: Die Streichung des Nachschub-Ventils vom
  2026-08-07 war **generationsspezifisch** (v20-Zyklus, weil dort eine
  lange Nebentask-Liste offen war) und **KEINE stehende Anweisung** --
  ich hatte sie faelschlich verallgemeinert (auch in
  PREREG_v21_fenster.md, dort korrigiert).
  **ERSETZUNG (frischer Batch desselben Generators + Rausrotieren einer
  Alt-Generation) ist VERWORFEN** -- Nutzer-Argument, und es ist
  richtig: das ist indirekt mehr Volumen vom SELBEN Champion, waehrend
  die Diversitaet der alten Generationen aus dem Fenster fliegt. Genau
  die Generationen-Spreizung ist aber der Grund, ueberhaupt Alt-Material
  mitzufuehren.
  **Was bleibt: gezielte INJEKTION** (Sockel-Partien dazu, nichts
  verdraengt -- schont die Diversitaet). Bedingungen, damit daraus kein
  "solange nachlegen bis der Kandidat gewinnt" wird:
  1. Umfang und Entscheidungsregel VOR der Injektion schriftlich
     (Mini-Prereg), nicht nach dem verlorenen Gating improvisiert.
  2. Einmalig und begrenzt je Generation (Vorschlag: +2.000 Sockel),
     kein iteratives Nachlegen.
  3. Naming: derselbe Generator erzeugt ein Batch mit
     Unterscheidungs-Suffix (`v20wdlb`), sonst Datei-Kollision.
  4. Lesart des Ergebnisses: ein Sieg NACH Injektion belegt "die
     Generation brauchte mehr Policy-Material" -- NICHT, dass eine
     etwaige Rezept-Aenderung des Kandidaten gewirkt hat. Diese
     Unterscheidung muss im Verdikt stehen.
  5. Diagnostischer Rueckenwind erwuenscht (Policy-Wacht: fallen die
     Orakel-Metriken gegen die Vorgeneration, ist die Policy-Klasse der
     belegte Engpass), aber keine harte Vorbedingung -- Nutzer-Entscheid.
- **FENSTERGROESSE: FIXIERTE BASIS, Injektion ist die benannte Ausnahme
  (Nutzer-Entscheide 2026-08-09)**: 29.450 Partien / 2.945 Dateien / ~4,8 Mio.
  Zustaende bleiben die stehende Groesse. Die Rotation haelt sie
  konstant -- pro Windung 12.000 NEUE Partien (4.000 Sockel @600 +
  8.000 Schwarm @150), gleich viel altes Material rotiert raus. Folgen:
  (a) Kosten pro Generation KONSTANT (~18h Self-Play + ~3h Cache +
  ~3,5h Training), kein Anwachsen; (b) das Fenster wird mit jeder
  Windung FRISCHER statt groesser; (c) RAM/Cache-Budget stabil
  (~13 GB im Training, ~1 GB auf Platte).
  **Nicht neu aufrollen**: der Dosis-Befund ("Volumen half 6/6") ist
  eine stehende Versuchung, das Fenster generell zu vergroessern -- die
  Entscheidung dagegen ist bewusst gefallen (planbare Kosten,
  stationaeres Design ab v22). Eine DAUERHAFTE Vergroesserung braucht
  einen ausdruecklichen neuen Nutzer-Entscheid. Die einmalige,
  vorregistrierte Injektion bei Gating-Fehlschlag (s.o.) ist davon
  ausgenommen und veraendert die Basisgroesse nicht.
- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.
- **PROMOTIONS-CHECKLISTE (Nutzer-Hinweis 2026-08-09: die Kader-Praxis
  wurde bis dato nicht konsequent umgesetzt)** -- bei JEDEM
  Champion-Wechsel vollstaendig abarbeiten, nicht aus dem Gedaechtnis:
  1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
  2. Elo-Kante **Gating** (Champion-1) -- inkl. Replikations-Zeile, falls
     Fruehstopp <150 Paare.
  3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
     Fruehstopp** (Praezedenz v18/v19/v20-Verankerung).
  4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- **das ist der
     Punkt, der bei v20 UND v21 zunaechst fehlte**; ohne ihn ruht die
     Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating:
     CI +-90 Punkte).
  5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
     Eintrag in die #29-Buchfuehrung.
  5b. **Anzeige-Kalibrierung nachziehen**: die Platt-Parameter A/B des
     NEUEN Champions in `server.py` (`_DISPLAY_CAL_A/_B`) eintragen --
     sie sind modellspezifisch. Quelle: `tools/platt_fit.py --models
     models/alphazero_<neu>.pth`. Ohne das zeigt die GUI die
     Gewinnwahrscheinlichkeit mit der Kurve des VORGAENGERS an.
  5c. **sigma/Prior-Balance messen** (neu 2026-08-09, aus Task G):
     `tools/gumbel_scale_calibration.py --model <neu> --sims 400
     --n-states 300`, ~10 min. Der Aera-Wechsel v18->v21 hat das
     Verhaeltnis von 1,232 auf **2,287** verschoben (delta_q verdoppelt,
     delta_ln(prior) unveraendert) -- R3 liegt mit 2,972 praktisch auf
     der Wiedereroeffnungs-Schwelle. **Ueberschreitet die
     Gesamt-Kennzahl 3, oeffnet sich die c_visit/c_scale-Familie per
     REGEL wieder** (kein Ermessen). Zugleich Verfallsdatum-Waechter
     fuer die H0-Befunde der Wurzel-Regler-Familie: die wurden in einem
     anderen Balance-Regime gemessen.
  6. STATUS-Champion-Zeile + history-Kapitel.
  **Nachtrag-Schuld ERLEDIGT** (Klarstellung 2026-08-10): die v20-Kante zu
  `v19_best` lief am 2026-08-09 -- 114:76 ueber 190 Partien, SPRT-H1 nach 95
  Paaren, p=0,0043 (`elo_history.csv` Zeile 53,
  `paired_gating_v20_vs_v19best_nachtrag.json`). Die alte "fehlt"-Zeile hier
  hat mich zweimal dazu verleitet, die Messung erneut vorzuschlagen.
  **Elo-Fragen am Primaerregister `elo_history.csv` pruefen, nicht an dieser
  Datei.**
- **LOESCHEN NUR MIT EXPLIZITER RUECKFRAGE (Nutzer-Regel 2026-08-08,
  dritter Vorfall dieser Klasse -- "inakzeptabel")**: Kein Loeschen,
  Verschieben oder Ueberschreiben von Dateien, Ordnern oder Worktrees
  ohne vorherige, den KONKRETEN Pfad benennende Nutzer-Freigabe.
  Ausnahme: das eigene Scratch-Verzeichnis.
  Im Einzelnen:
  1. **Eine FRAGE ist keine Anweisung.** "Ist X noch aktuell?", "kann
     man X weg?", "brauchen wir X?" verlangen eine ANTWORT. Handeln
     erst nach einem Imperativ, der das Ziel nennt.
  2. Als Loeschen gelten auch: `git worktree remove`, `git checkout --`,
     `git reset --hard`, `git clean -fd`, `mv` aus dem Projekt heraus,
     `rm` auf generierte Artefakte (Caches sind KEINE Ausnahme -- die
     Freigabe vom 2026-08-08 galt fuer sechs namentlich genannte Dateien).
  3. Vor jeder freigegebenen Loeschung: Ziel ANSEHEN (Inhalt, Groesse,
     Reparse-Points bei Worktrees -- Junction-Vorfall 2026-07-24), das
     Ergebnis der Pruefung BERICHTEN, und nur dann ausfuehren.
  4. Gilt fuer Sub-Agents identisch und steht in jedem Agent-Prompt.
  5. "Aufraeumen" ist niemals selbst-autorisiert -- auch dann nicht,
     wenn etwas offensichtlich veraltet ist.
- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.
- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).
- **AUFLOESUNG SCHLAEGT SPARSAMKEIT (Nutzer-Regel 2026-08-08)**: Wenn
  eine Entscheidung an einer Differenz haengt, die UNTERHALB der
  Auflösung des Offline-Instruments liegt (Value-Seite: Brier-Gaps
  <0,015 sagten 0/4 die Arena voraus; gemessene Seed-Skala ~0,0006),
  dann darf das Offline-Mass die Entscheidung NICHT tragen -- auch nicht
  als Spar-Vorfilter ("nur gaten, wenn Brier X schlaegt"). Stattdessen
  die ARENA in die Abwaegung nehmen und die Kosten AUSRECHNEN, nicht
  schaetzen: ein Gating (~1-1,5h CPU, 200 Paare @400) ist regelmaessig
  BILLIGER als das Training, das man sich mit dem Vorfilter sparen
  wollte (~3,5h GPU) -- und es ist das einzige validierte Instrument.
  Wer auf einem blinden Mass spart, spart die billige Ressource und
  riskiert die teure Fehlentscheidung.
  **Ausnahme Policy-Seite**: die Orakel-Metriken (Prior-Masse Top-3,
  Kendall-Tau) sind arena-validiert (7/7) und DUERFEN als Vorfilter
  dienen -- so entschieden bei #35b (beide Metriken schlechter -> kein
  Gating). Der Unterschied ist der Validierungsstand, nicht die
  Bequemlichkeit.
  Zusatznutzen, den man mitnehmen soll: jedes gefahrene Gating liefert
  ein arena-ENTSCHIEDENES Paar -- die Waehrung, in der #29 (Validierung
  eines Offline-Value-Praediktors) bezahlt wird (Stand ~3, noetig >=6).
- **Aggressions-/Denial-Programm GESCHLOSSEN** (2026-08-07): alle
  Knoepfe auf Default (w=0, λ=0, ε=0, bias=1); "gate what you ship";
  Wiedervorlage nur mit messbar schaerferem opp-Kopf
  (PREREG_aggression_stilmessung/PREREG_denial_tiebreak).
- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).
- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).
- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).
- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blindfleck.md`, Tasks E/F/G dazu
  geschlossen -> history): Q-Skalierungs-Varianz ist JA protokolliert
  (`tools/gumbel_scale_calibration.py`), **Ueberlebensrate im
  Sequential Halving NEIN** -- vorhanden sind `root_child_q`,
  `root_num_actions(_considered)` und `max_depth`, aber nicht, welcher
  Kandidat welche Halbierungsphase uebersteht. Bewusst nicht
  nachgeruestet: Task E hatte zuerst zeigen muessen, ob die MENGE
  stimmt (Ergebnis: Miss-Rate 1,21%, weit unter der 5%-Schwelle).

## Architektur, Stand jetzt (aktualisiert 2026-08-06)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):
- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2`.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting`, Blattwert = exakter Endscore inkl.
  Wertungsplatten. **Seit 2026-08-10 EXPECTIMINIMAX, nicht mehr reines
  Alpha-Beta**: Zufallsknoten an den Aufdeck-Stellen der verdeckten
  Chip-Zuordnung (16 der 20 Chips sind aus R1-4 bekannt, unbekannt ist nur
  die Fabrik-Position der restlichen 4). Kein Pruning in Zufallsknoten
  (Star1/Star2 bewusst weggelassen). `NODE_BUDGET=200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus),
  `MOSAIC_R5_CHANCE_NODES` (**Default AN** seit 2026-08-10, `=0` stellt das
  Altverhalten her), `MOSAIC_R5_NODE_BUDGET`, `MOSAIC_R5_NET_SOLVER`
  (Default an).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):
- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`, seit
  Task #28 zusaetzlich `opp_points` (nur in Modellen, die damit trainiert
  wurden -- Engine erkennt ihn per Output-NAME und faellt sonst auf
  Bestandsverhalten zurueck). **`plate_head` wurde am 2026-08-10 gebaut und
  wieder ENTFERNT** -- der Ownership-Kopf ist der Randlayer.
  `ownership` ist seit 2026-08-10 **140 breit** (72 Feldlabels + 68
  Zusatzziele, Cache-Suffix `+conj_v2`); `OWNERSHIP_WEIGHT` steht in
  `config.py` weiter auf 0, der erste Lauf MIT Gewicht (0,2) laeuft seit
  2026-08-10 nachts. Aufbau und gemessener Zustand oben im Abschnitt STAND.
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, **`VALUE_OPP_EPSILON = 0,0`** (war 0,1 bis Schema 19).
- **Punkte-ZIEL (Schema 20, 2026-08-10)**:
  `points_val = tanh(own_total/VALUE_SCALE)` -- der Gegner-Anteil ist
  ENTFERNT. Fuer VOR Schema 20 trainierte Modelle bedeutet ihr
  `points`-Ausgang weiter `own - 0,1*opp`; fuer die Spielstaerke belanglos,
  weil die Ausgabe im Suchpfad ohnehin verworfen wird
  (`POINTS_UTILITY_WEIGHT = 0` und `w = 0`).
- **Value-ZIEL (#34-Verdikt, Schema 17 unveraendert gueltig)**: `values_wdl`
  = TD-Blend aus Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang;
  Alt-Datei-Bootstraps werden beim Cache-Bau Platt-entstaucht
  (A=0,0051/B=1,9269), `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben
  roh. Training: `--value-head wdl --select-by-brier` (KEIN destretch-Flag
  mehr noetig). **Das Ziel ist margen-BLIND** -- siehe Abschnitt STAND,
  "warum das Netz nicht punktoptimiert spielt".
  Policy-Traeger-Manifest **`data/policy_carrier_manifest_v21.json`**
  (Default in `neural_net.py` ist noch die v20-Datei -- ein Trainingsstart
  im v21-Fenster MUSS `MOSAIC_CARRIER_MANIFEST` setzen, s. Fenster-Pinning
  oben), maskiert Alt-Dateien ausser 135 v19wdl + 45 v18, plus
  `carrier_prefixes: ["selfplay_v20wdl_"]`; alles im Cache-Key.
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> **`v21_2d_brierbest`**.

---

## Task #38 (geparkt, Arbeitskreis "Spaeter" mit #31): Moon-Head-Feinschliff (2026-08-05)

Befund aus einer Interesse-Frage des Nutzers, Code verifiziert. Der Kopf
selbst ist solide (Plackett-Luce-Faktorisierung der Mond-Reihenfolge aus
dem Policy-Raum, Labels vom exakten Rundensolver, Prior-Aufteilung in der
Expansion). Zwei nie untersuchte Punkte fuer spaeter:
1. **Loss-Gewicht**: `moon_nll` wird mit VOLLEM Gewicht 1,0 in den
   Policy-Loss addiert (train.py, `p_loss + moon_nll[sun_mask].mean()`)
   -- bei NLL ~0,5-1 gegen Policy ~1,9 beansprucht ein Teilproblem, das
   nur Sonnenzuege betrifft, potenziell ~1/3 des Policy-Gradienten. Nie
   gesweept (VALUE_WEIGHT-Blindfleck-Muster). Als Arm in einen
   kuenftigen Loss-Gewichts-Sweep.
2. **Label-Horizont** (Nutzer-Einordnung 2026-08-05, RELATIVIERT):
   Referenz maximiert den RUNDENendstand (`solve_round_final_score`).
   Da die Fabriken zu Rundenbeginn NEU befuellt werden, ist der
   Wirkhorizont einer Reihenfolge im Wesentlichen die laufende Runde --
   das Solver-Label ist also naeher am Optimum als zunaechst vermutet,
   Restpunkt sind allenfalls Randeffekte. Falls Labels je aus der Suche
   kommen (root_child_q aus #35 liefert die Q-Ordnung der Varianten ab
   v20 gratis), waere das ein billiger A/B, kein Pflichtumbau.
Kein akuter Bedarf: Policy-Seite ist ueber die Orakel-Metriken
arena-validiert, inkl. PL-Aufteilung.

## Task #39 (geparkt, Arbeitskreis "Spaeter" mit #31/#38): Startkuppel-Platzierung (2026-08-06)

Nutzer-Beobachtung "setzt sie gefuehlt immer an dieselbe Position" --
am Code bestaetigt und MECHANISCH erklaert
(`self_play.rs::choose_start_placement`): der Farb-Score ist
POSITIONS-unabhaengig (summiert nur Fabrik-Farbhaeufigkeiten je Feld),
der Eckbonus fuer alle 4 Ecken identisch (0,5), Ties behaelt der erste
Kandidat -> IMMER Ecke (0,0); die Feld-Summe ist zudem
ROTATIONS-invariant -> immer 0 Grad. Position/Rotation sind tote
Freiheitsgrade; nur die Platten-WAHL variiert. Gilt ueberall (GUI,
Arena, Self-Play; Startplatzierung ist policy-maskiert, das Netz lernt
sie nie).

**Nutzer-Einordnung (2026-08-06, schaerft den Zuschnitt)**: die Ecke an
sich ist strategisch RICHTIG (Rand/Diagonale/Eckplatten honorieren sie
alle) -- das Problem ist die MONOTONIE, nicht die Position.
**KORREKTUR (Nutzer 2026-08-06, zweite Runde)**: auch der Ecken-Rang
(3 oben / 8 unten) ist KEIN Bewertungsfehler -- Kuppelzeile 0 wird von
den SCHNELLSTEN Musterreihen (1-2, Kapazitaet 1-2 Steine) gespeist: die
obere Ecke kommt frueher in Wertung + Orthogonal-Bonus und wird
zuverlaessiger ueberhaupt komplett; die 8 Punkte unten haengen an den
traegsten Reihen (5-6). Der (0,0)-Tie-Break loest den Trade-off implizit
RICHTIG auf. Verbleibende Substanz von #39:
(1) ROTATION -- bestimmt Farb-Ausrichtung zur Brettmitte und
Sonderfeld-Lage, heute verschenkt (Score rotationsinvariant);
(2) MONOTONIE/Tie-Break -- Diversitaets-Frage (GUI-Abwechslung +
Korpus-Vielfalt), keine Staerke-Frage.
**Verbesserungs-Optionen (bei Angehen abzuwaegen)**:
a) Heuristik-Upgrade: Rotations-Bewertung + randomisierter Tie-Break
   unter nahezu gleichwertigen Kandidaten; jede Aenderung per Arena
   gegen den Bestand pruefen (die Strategie-Intuition des Koordinators
   lag hier zweimal daneben, die des Nutzers zweimal richtig).
b) Prinzipiell: Platzierung in den Aktionsraum der Suche -- ACHTUNG
   NUM_ACTIONS-Aenderung macht alte Checkpoints unbrauchbar
   ([[num-actions-change-breaks-old-checkpoints]]), teuer.
**Randbedingung**: NICHT waehrend einer laufenden Kampagne aendern
(verschiebt die Self-Play-Zustandsverteilung); fruehestens v21-Setup.
Nebenaspekt: die heutige Uniformitaet kostet auch Zustands-Diversitaet
im Korpus.

## Task #31 (vorgemerkt): Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem (2026-08-03)

**Nutzer-Auftrag**: Staerke-Skalierung fuer Mensch-Spiele; Einschaetzung
"Sims allein richten es nicht" ist KORREKT und hier besonders: (a) R5-
Alpha-Beta + Tiling-DFS spielen sim-unabhaengig exakt -- eine 20-Sims-KI
spielt trotzdem perfekte Endspiele; (b) Gumbel+Policy-Prior traegt auch
Mini-Budgets -- flacher, aber nicht menschlich-fehlbar.

**Design-Skizze (3 Hebel je Stufe)**: Sims-Budget + Endspiel-/Tiling-
Degradation (R5-Knotenbudget-Override bzw. Policy-Sampling statt Solver,
Tiling greedy statt exakt bei "leicht") + Fehler-Injektion via Root-
Temperatur-Sampling mit Q-GAP-DECKEL (nur plausible Fehler <=3-5 Punkte;
menschlich-fehlbar statt gleichmaessig-flach; loest auch Ausrechenbarkeit).
Stufen: extrem=Champion@600-800 (optional lambda_aggr als Stil),
schwer=heutiger Stand @400, mittel=~100-150 Sims + Deckel-Sampling +
reduziertes R5-Budget, leicht=~8-16 Sims + Temperatur hoeher + epsilon +
Greedy-Tiling. ABGERATEN: alte Generationen als Stufen (Wartung,
OneDrive-Risiko, Regel-Fix-Inkompatibilitaeten, "gleichmaessig schwach").

**Kalibrierung**: vorhandene Elo-Leiter + Heuristik-Anker; je Konfiguration
n=150 vs 2 Anker, Ziel-Baender ~leicht 700-800 / mittel ~1000 / schwer
~1150-1200 / extrem=Champion. Umsetzung nach Muster Task #28
(Laufzeit-Parameter + Server-Preset + GUI-Dropdown). OFFEN (Nutzer):
Ziel-Baender ok? Darf "leicht" sichtbar Endspiele verstolpern?

**GATE (Nutzer-Entscheid 2026-08-03): ZURUECKGESTELLT** -- wird erst
angegangen, wenn ein Champion existiert, der auch gute menschliche
Spieler wirklich fordert. Bis dahin bleibt die Prioritaet auf
Staerke-Arbeit (v20-Zyklus, Value-Head-Front #29/#30, lambda=0.7-
Kandidat), nicht auf Schwierigkeits-UX.
