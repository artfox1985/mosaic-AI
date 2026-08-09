# Vorregistrierung: Reagiert der PUNKTE-Kopf auf die Wertungsplatten?

**Angelegt 2026-08-09, VOR der Messung.** Anlass: Nutzer-Partie
`game_20260809_115404_seed704874` (Grundpunkte 51:51, Endwertung 18
gegen -2, also 69:49 -- Diagonalen 10:0, leere Spezialfelder -3 gegen
-12). Nutzer-Argument, das den Task ausloest: *"eigentlich sollte der
point head auch reagieren. durch die kombination aus wertungsplatten zum
schluss und strategischem aufbau der reihen/spalten während den runden
maximieren wir die punkteanzahl"* -- und das ist strukturell gedeckt:
das Trainingsziel des Punkte-Kopfes ist
`own_total = step["scores"][Spieler]`, laut Kommentar in
`engine/py/neural_net.py:474` **bereits inklusive Wertungsplatten**.
Der Kopf ist also darauf trainiert, die Platten einzupreisen. Gemessen
wurde das nie: alle bisherigen Platten-Instrumente lesen `root_value`.

## Die GEGNER-Richtung ist gleichrangig Teil des Tasks

Nutzer-Ergaenzung (2026-08-09): *"weil es geht dann auch anders herum.
ich kann schauen dass mein gegner seine wertungsplatten nicht erreicht
oder strafpunkte durch die -3 platte bekommt."* Das ist strukturell
genauso gedeckt wie die eigene Richtung -- und wir haben dafuer einen
eigenen Kopf: `opp_points_head` (Task #28) mit dem Ziel
`opp_points_val = tanh(opp_total / VALUE_SCALE)`, wobei `opp_total`
aus derselben `step["scores"]`-Quelle stammt wie `own_total` und damit
**ebenfalls die Wertungsplatten enthaelt** (inkl. der -3 je leerem
Spezialfeld, Platte 6). `opp_points_forecast` liegt in `value_debug`
bereits vor.

Die Gegner-Richtung wird deshalb in BEIDEN Stufen gleichrangig
mitgemessen (nicht als Beigabe), mit denselben Schwellen. Zwei
Anschluesse, die davon abhaengen:

- **Der Aggressions-Blend** (`MOSAIC_POINTS_UTILITY_W` w,
  `MOSAIC_AGGR_LAMBDA` λ) ist der EINZIGE gebaute Weg, ueber den der
  opp-Kopf die Suche beeinflusst -- er steht nach der Neukartierung
  ueberall auf w=0, weil alle drei Arme H0 ergaben. Diese Messung war
  aber auf die allgemeine PUNKTE-MARGE gerichtet, nicht auf
  plattenspezifisches Verhindern. Ergibt Stufe 2 fuer den opp-Kopf eine
  ZUG-DIFFERENZIERUNG nach Platten, ist das ein NEUES Argument fuer
  w>0 und kein Wiederaufguss -- dann aber mit eigener Vorregistrierung
  und Arena-Entscheid, nicht durch Analogieschluss.
- **E3b** (laeuft gerade als Stufe 2) waehlt unter gleichwertigen
  Kandidaten den mit der NIEDRIGSTEN Gegner-Punkteprognose. Das ist
  bereits Verhinderung -- aber ueber die GESAMT-Prognose, nicht
  plattenspezifisch. Ein plattenbewusster Zuschnitt waere die
  schaerfere Variante; ob er lohnt, entscheidet erst dieses Ergebnis
  zusammen mit dem E3b-Verdikt.

## Was schon bekannt ist (und die Fallgrube definiert)

| Befund | Quelle |
|---|---|
| `mcts_visits` aendert sich bei Plattenwechsel NIE (JS 0,0 in 124/124) | Teil 3 (v16), in v21 reproduziert |
| Die TATSAECHLICHE Zugwahl kippt aber in **29,0%** (36/124) der Faelle | `plate_rank_invariance_v21.json`; v16 29,8%, v17 23,4% -- aera-stabil |
| Mechanismus: Sequential Halving laesst die Top-2 mit GLEICHEN Besuchszahlen enden, `gumbel_final_root_action` entscheidet dann per `ln(prior) + sigma(Q)` | Task #5, 2026-07-27 |
| Value-Kopf reagiert auf Plattenkombinationen: Streuung 0,0694 vs Seed-Rauschboden 0,0147 = **4,7x** | `scoring_tile_sensitivity_v21.json` |
| Der gebaute `PLATE_SHAPING`-Hebel blieb folgenlos (+2,4pp, n.s.) -- Begruendung in der Historie: **globaler Root-Value-Shift, der sich im Ranking wegkuerzt** | Task #5 Teil 1c |

**Die Fallgrube ist damit benannt**: eine Groesse, die sich bei
Plattenwechsel bewegt, aber ALLE Kandidatenzuege gemeinsam bewegt
(NIVEAU-Verschiebung), ist fuer die Zugwahl wertlos -- sie kuerzt sich
im Ranking weg. Genau daran ist Plate-Shaping gescheitert, und genau
das kann die 4,7x-Zahl des Value-Kopfes ebenfalls sein (unentschieden,
weil bisher nur an der WURZEL gemessen). Eine Messung, die nur
"reagiert der Punkte-Kopf ueberhaupt?" beantwortet, wiederholte diesen
Fehler. Deshalb zwei Stufen, und die ENTSCHEIDUNG liegt in Stufe 2.

## Stufe 1 (jetzt, KEIN Code noetig): traegt der Kopf Platten-Information?

`value_debug` aus `net_search_state_json_trace` enthaelt bereits
`points_forecast` und `opp_points_forecast` (`RootValueDebug`,
`net_mcts.rs`). Erhebung additiv im BESTEHENDEN Lauf von
`tools/plate_rank_invariance.py` (16 Zustaende x 8 Kombinationen,
Champion @400 Sims, Seed 1000) -- derselbe Suchlauf, der die Kipprate
misst, kein zusaetzliches Rechenbudget.

- Groesse: Spannweite von `points_forecast` ueber die 8 Kombinationen je
  Zustand.
- Rauschboden: dieselbe Kombination mit zwei verschiedenen Seeds (der
  Seed mischt die ECHT verdeckte Information neu -- identisches
  Protokoll wie beim `root_value`-Rauschboden).
- **Kennzahl: Verhaeltnis Platten-Spannweite / Seed-Rauschboden**, plus
  dieselbe Zahl fuer `opp_points_forecast` und (als Referenz)
  `raw_value`.

**Regel 1a**: Verhaeltnis **>= 3** ⇒ der Punkte-Kopf traegt
Platten-Information, Stufe 2 wird gefahren.
**Regel 1b**: Verhaeltnis **< 3** ⇒ der Kopf hat die Platten trotz
plattenhaltigem Ziel NICHT gelernt. Das ist ein eigenstaendiger Befund
und verschiebt die Frage auf die TRAININGSSEITE (Credit-Assignment),
nicht auf die Suche. Stufe 2 entfaellt.
**Regel 1c (Vorab-Warnung, keine Entscheidung)**: Ein Bestehen von
Stufe 1 heisst NICHT, dass der Kopf ein Hebel ist -- siehe Fallgrube.
Ein positives Stufe-1-Ergebnis darf NICHT als "Punkte-Kopf
beruecksichtigt die Platten" berichtet werden, sondern nur als
"Punkte-Kopf traegt Platten-Information an der Wurzel".

---
### ERGEBNIS Stufe 1 (2026-08-09): GATE WAR FEHLKONSTRUIERT -- Zahlen nur deskriptiv

Lauf: Champion, 400 Sims, Seed 1000 (Rauschboden-Seed 2000), 16 Zustaende
x 8 Kombinationen. Belegstelle `evaluations/punktekopf_platten_stufe1.json`.
Kipprate im selben Lauf unveraendert reproduziert (36/124 = 29,03%),
Altverhalten also intakt.

| Groesse | Median Platten-Spannweite | Median Seed-Rauschboden |
|---|---|---|
| `points_forecast` | 0,208 | **0,0 exakt** |
| `opp_points_forecast` | 0,182 | **0,0 exakt** |
| `raw_value` (Referenz) | 0,134 | **0,0 exakt** |

**Mein Fehler, klar benannt**: Ich habe den Rauschboden aus dem
`root_value`-Protokoll uebernommen ("dieselbe Kombination, zwei Seeds"),
ohne zu pruefen, ob er auf die neue Zielgroesse ueberhaupt anwendbar ist.
Er ist es NICHT. `root_value` ist eine SUCHBAUM-Statistik und haengt
ueber simulierte Zukunfts-Ziehungen echt am Seed. Die `value_debug`-
Felder stammen dagegen aus `compute_root_value_debug`, einem EINZELNEN
deterministischen Netz-Forward-Pass auf dem Wurzelzustand -- und
`features_for_net` kodiert die verdeckte Information als aggregierte
Zaehler/Masken (`features.rs` ~101-147), nicht als geordnete Liste. Die
seed-getriebene Neumischung aendert die Netz-EINGABE damit ueberhaupt
nicht. Der Nenner ist strukturell Null, das Verhaeltnis rechnerisch
unendlich, und **Regel 1a ist damit trivial fuer ALLE drei Groessen
erfuellt, auch fuer `raw_value`** -- ein Gate, das nichts trennt, ist
kein Gate. Es wird hiermit als ungueltig erklaert und nicht als
bestanden berichtet.

**Was trotzdem verwertbar ist** (deskriptiv): alle drei Spannweiten sind
klar von Null verschieden, beide Punkte-Koepfe tragen also
Platten-Information an der Wurzel -- und zwar nicht weniger als der
Value-Kopf. Vorbehalt gegen einen direkten Groessenvergleich: die drei
Koepfe haben unterschiedliche Zielskalen (`raw_value` = tanh der Marge,
`points_forecast` = tanh(own) - ε·tanh(opp)), die Spannweiten sind also
nicht dimensionsgleich. "0,208 > 0,134" heisst NICHT "der Punkte-Kopf
reagiert staerker".

**Kein Widerspruch zur 4,7x-Zahl von heute**: die stammt aus
`scoring_tile_sensitivity.py` und misst `root_value` (Suchstatistik,
echter Seed-Rauschboden 0,0147). Hier wird `value_debug.raw_value`
gemessen (Forward-Pass, Rauschboden 0). Zwei verschiedene Groessen,
beide Messungen korrekt.

**Konsequenz fuer den Ablauf**: Die Screening-Funktion von Stufe 1
entfaellt -- sie sollte entscheiden, ob Stufe 2 lohnt, kann das aber
nicht leisten. Da alle drei Groessen Platten-Information tragen, ist
Stufe 2 ohnehin die einzige Messung, die die eigentliche Frage
beantwortet. **Stufe 2 ist ab hier der ALLEINIGE Entscheidungspunkt**;
die Regeln 2a/2b bleiben unveraendert gueltig (sie waren nie an Stufe 1
kalibriert). Wer spaeter einen echten Rauschboden fuer eine
Forward-Pass-Groesse braucht: der Seed taugt dafuer nicht, es braeuchte
eine andere Stoerung (z.B. Vergleich ueber Plattenkombinationen, die in
den aktiven Kriterien aequivalent sind).

## Stufe 2 (ALLEINIGER Entscheidungspunkt): NIVEAU oder ZUG-DIFFERENZIERUNG?

### AMENDMENT vor dem Stufe-2-Lauf: das Nebenkriterium war wieder degeneriert

Stufe 2 nennt als zweites Kriterium "zentrierte Spannweite >= 3x
Rauschboden". Derselbe Fehler wie in Stufe 1: die Kopf-Ausgaben stammen
aus einem deterministischen Forward-Pass, ihr Seed-Rauschboden ist
strukturell **Null**, das Verhaeltnis also unendlich und das Kriterium
wertlos. Wird hiermit ersetzt -- VOR dem Lauf, es ist nichts gemessen.

**Ersatz: skalenfrei gegen den KANDIDATEN-Abstand messen**, nicht gegen
ein Rauschen. Je Zustand und Kombinationspaar:
`mean_i |zentriert_A(i) - zentriert_B(i)| / std_i(zentriert_A(i))` --
also: wie stark verschiebt ein Plattenwechsel die Kandidaten
GEGENEINANDER, verglichen damit, wie weit die Kandidaten ohnehin
auseinanderliegen? Ein Wert von 0,02 heisst irrelevant, 0,5 heisst
entscheidend. Diese Groesse braucht keinen Rauschboden.

**Primaere Entscheidungsmetrik bleibt der Kendall-Tau** der
Kandidaten-Reihenfolge (Median ueber Zustaende) -- er ist von sich aus
skalenfrei und war vom Nebenkriterium nie abhaengig. Regeln 2a/2b gelten
unveraendert, nur mit der neuen Nebengroesse:
- **2a**: Tau-Median < 0,9 UND relative Verschiebung >= 0,2
- **2b**: Tau-Median >= 0,9 ODER relative Verschiebung < 0,2

Die 0,2-Schwelle ist gesetzt, nicht abgeleitet -- sie sagt "ein
Plattenwechsel muss die Kandidaten um mindestens ein Fuenftel ihres
eigenen Abstands verschieben, um als zug-differenzierend zu gelten".
Vorab festgelegt, damit sie nicht nach Ergebnissicht gewaehlt wird.


Braucht eine **additive** Rust-Ergaenzung: die je Kandidat vom Netz
berechneten Kopf-Ausgaben (`value` / `points` / `opp_points` am
KINDzustand) im `gumbel_trace` mitprotokollieren. Der Suchlauf
evaluiert diese Kinder ohnehin, es fehlt nur die Aufzeichnung.
Bedingungen: neue Felder additiv, Default-Verhalten byte-identisch,
**Paritaets-Hash muss
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`
bleiben**, Tests gruen.

Auswertung je Zustand und Kombination: Vektor der Kopf-Ausgaben ueber
die Kandidaten in **NIVEAU** (Mittelwert) und **ZENTRIERT**
(Vektor minus Mittelwert -- nur dieser Teil ist rangrelevant) zerlegen.

- **Entscheidungsmetrik: Kendall-Tau der Kandidaten-Reihenfolge nach
  `points_forecast` zwischen den Plattenkombinationen** (Median ueber
  Zustaende), plus Spannweite des ZENTRIERTEN Anteils gegen denselben
  Seed-Rauschboden.
- **Regel 2a**: Tau-Median **< 0,9** UND zentrierte Spannweite
  **>= 3x** Rauschboden ⇒ der Punkte-Kopf differenziert die ZUEGE nach
  Platten. Dann ist er ein echter Hebel-Kandidat, und der Folgeschritt
  ist eine eigene Vorregistrierung fuer sein Gewicht im Suchpfad
  (heute traegt der Value-Kopf den Backup) -- mit Arena-Entscheid, kein
  Offline-Verdikt.
- **Regel 2b**: Tau-Median **>= 0,9** ODER zentrierte Spannweite
  **< 3x** ⇒ der Kopf ist plattenbewusst, aber nur im NIVEAU. Dann ist
  er als Suchpfad-Hebel TOT (derselbe Grund wie bei Plate-Shaping),
  und der Punkt wird geschlossen mit der Konsequenz: die Plattenwirkung
  muss zug-differenzierend ins TRAINING gebracht werden.
- **Pflicht-Beigabe**: dieselbe Zerlegung fuer `raw_value`. Damit ist
  nachtraeglich geklaert, ob die heute gemessenen 4,7x des Value-Kopfes
  Niveau oder Differenzierung sind -- eine offene Frage, die diese
  Messung gratis mitbeantwortet.

## KANDIDAT fuer den Fall von Regel 2b (Nutzer-Befund 2026-08-09)

Nutzer: *"das ist aber erst gültig nach spielende. ich mein du kannst
dir eine wahrscheinlichkeit ausrechnen dass diese wertungsplatte aktiv
sein wird."* -- gemeint ist nicht die Platten-IDENTITAET (die ist ab
Runde 1 gezogen und steckt als One-hot in der Eingabe), sondern ob die
Platte am Ende ZUBEISST. Am Code bestaetigt und praezisiert:

`scoring.rs::wertung_progress` rechnet fuer Platte 6
`-3.0 * sf.special_empty` (Zeile 178), und `special_empty` zaehlt
**jedes nicht belegte Spezialfeld, auch die GESPERRTEN**
(`special.iter().filter(|sp| !sp.is_filled())`, Zeile 407). Spezialfelder
starten gesperrt und leer ⇒ der Term meldet ab dem ersten Zug die
MAXIMALE Strafe und kann sich nur verbessern. Der Kommentar bei Zeile
156 begruendet das ausdruecklich damit, die additiven Platten 4 und 6
braeuchten "keinen Fortschritts-Ersatz" -- fuer Platte 4 richtig (jede
Randfliese ist gebucht, monoton steigend), fuer Platte 6 falsch.

Die Folge ist keine Verzerrung (bei `plate_shaping_delta` kuerzt sich
ein symmetrischer Sockel weg), sondern **Blindheit fuer den
entscheidenden Zwischenschritt**: der Term bewegt sich erst, wenn eine
weisse Fliese tatsaechlich liegt. Dass man die drei anderen Felder einer
Kuppelplatte fuellt und das Spezialfeld damit ueberhaupt FREISCHALTET
(`dome.rs::try_unlock_special`), ist im Signal nichts wert -- obwohl das
die Handlung ist, die ueber die -12 in der Nutzer-Partie entschieden hat.
Fuer Reihen/Spalten/Diagonalen macht dieselbe Funktion es laengst
richtig (quadrierte Fuellgrade), nur bei Platte 6 fehlt es.

Reichweite: `wertung_progress` haengt NICHT im Leerlauf -- es steckt in
`mcts.rs:82`, also in der Blattbewertung der HEURISTIK, gegen die alle
Arena-Messungen laufen (im Netzpfad nur ueber das abgeschaltete
Plate-Shaping).

### Zuschnitt des Kandidaten (Nutzer-Praezisierung 2026-08-09)

*"das passt gut für die heuristik denk ich. für unseren net agent
brauchen wir vermutlich wirklich eine wahrscheinlichkeit die wir dann in
die blattbewertung miteinbauen können."*

Diese Trennung hat eine wichtige Nebenwirkung, die FUER sie spricht:
bleibt `wertung_progress` (und damit die Heuristik-Blattbewertung in
`mcts.rs:82`) UNVERAENDERT und bekommt nur der NETZPFAD den neuen Term,
dann bleibt der **Arena-Massstab fix** -- alle bisherigen Arena-Zahlen
bleiben vergleichbar. Das loest den Vorbehalt aus dem Abschnitt oben.

Definition der Wahrscheinlichkeit -- **empirisch kalibrieren, nicht
handtunen**: gesucht ist P(Spezialfeld am SPIELENDE noch leer), bedingt
auf beobachtbare Groessen (Runde, Anzahl fehlender Felder auf der
zugehoerigen Kuppelplatte, Sperrzustand). Diese Wahrscheinlichkeit ist
NICHT zu schaetzen, sondern **auszuzaehlen**: das v21-Fenster enthaelt
29.450 Partien mit Endzustaenden. Eine Haeufigkeitstabelle ueber
(Runde, fehlende Felder) liefert die Kurve datengetrieben, rein offline,
ohne Arena- oder GPU-Budget. Damit ist es kein geratener Ersatzterm wie
die quadrierten Fuellgrade, sondern eine gemessene Groesse -- und die
Auszaehlung ist zugleich der billigste Vorab-Test, ob es ueberhaupt
etwas zu holen gibt: ist P(leer) schon in Runde 2 nahe 0 oder nahe 1,
traegt das Merkmal keine Information.

Einbau dann nach dem Standardmuster des Projekts: `MOSAIC_*`-Knopf mit
**Default 0 = byte-identisches Bestandsverhalten**, Paritaets-Hash haelt,
Arena-A/B mit eigener Vorregistrierung. Ausdruecklich mitzudenken:
**Doppelzaehlungs-Risiko** -- der Value-Kopf ist auf plattenhaltige
Ergebnisse trainiert und reagiert messbar (4,7x Rauschboden). Ein
zusaetzlicher expliziter Plattenterm kann die Gewinnwahrscheinlichkeit
verzerren (Platt-B als Waechter mitmessen), weshalb der Gewichts-Knopf
und nicht ein fest verdrahteter Term der richtige Weg ist.

**Reihenfolge, bewusst so:** Dieser Kandidat wird NICHT gebaut, solange
Stufe 2 offen ist. Zeigt Stufe 2 fuer den Punkte-Kopf eine
Zug-Differenzierung (Regel 2a), braucht es kein handgebautes Merkmal --
dann ist der Hebel, dem Kopf Gewicht zu geben. Erst bei Regel 2b wird
eine Erwartungs-Formel fuer Platte 6 der richtige Weg, und dann mit
eigener Vorregistrierung (Aenderung an der Heuristik-Blattbewertung
verschiebt den Arena-MASSSTAB -- das muss vorher bedacht und
dokumentiert werden, sonst sind Vor- und Nach-Messungen nicht
vergleichbar).

## Was NICHT Teil dieses Tasks ist

- Kein Plate-Shaping-Wiederaufguss (2026-07-27 gemessen, folgenlos, und
  der Grund ist strukturell verstanden).
- Keine Encoder-Aenderung. Die Beobachtung "6 von 8 Platten haben eine
  gattierte 2D-Ebene, die Platten 3 (Mehrfarbige Felder) und 6
  (Spezialfelder) nicht" ist notiert, aber KEIN Befund: die Diagonalen
  (Platte 2) HABEN eine Ebene und gingen in der Nutzer-Partie trotzdem
  0:10 verloren -- das spricht gegen die Encoder-Erklaerung als
  Hauptursache.
- Keine Aenderung an Suchreglern. Die Wurzel-Regler-Familie hat in
  dieser Sitzung zweimal H0 und einmal Schaden geliefert.

---
## ERGEBNIS Stufe 2 (2026-08-09): REGEL 2a fuer ALLE DREI Groessen -- zug-differenzierend

`tools/punktekopf_stufe2.py`, Champion, 400 Sims, Seed 1000, 16 Zustaende
x 8 feste Kombinationen; 12 nutzbar (3x Runde 5 ohne Netz, 1x nur ein
Kandidat). Belegstelle `evaluations/punktekopf_platten_stufe2.json`.

| Groesse | Tau-Median | Relative Verschiebung | Regel |
|---|---|---|---|
| `net_points_forecast` | 0,792 | 0,261 | **2a** |
| `net_opp_points_forecast` | 0,640 | 0,396 | **2a** |
| `net_raw_value` | 0,778 | 0,345 | **2a** |

**Warum der Tau hier belastbar ist**: der Forward-Pass ist
deterministisch, bei identischer Kombination waere Tau **exakt 1,0**.
Jeder Wert darunter ist eine echte, plattenverursachte Umsortierung --
kein Rauschboden noetig, und damit die erste Platten-Metrik heute ohne
degeneriertes Nebenkriterium.

### KORREKTUR meiner eigenen Erzaehlung

Ich habe heute mehrfach behauptet, die Plattenwirkung komme als
NIVEAU-Verschiebung an und kuerze sich im Ranking weg. **Das ist fuer den
Value-Kopf widerlegt** (Tau 0,778). Die 4,7x-Zahl aus der
Wurzel-Messung konnte zwischen Niveau und Differenzierung nicht
unterscheiden -- ich habe die Unentschiedenheit als Niveau gelesen und
daraus eine Erklaerung gebaut, die die Messung nicht hergab.

Warum `PLATE_SHAPING` dann trotzdem folgenlos blieb: der Shaping-TERM war
level-artig (globale Differenz `wertung_progress(P0)-wertung_progress(P1)`,
identisch fuer alle Kandidaten eines Knotens). Dass ein hinzugefuegter
globaler Term sich wegkuerzt, sagt nichts darueber, ob der GELERNTE
Value-Kopf differenziert. Ich habe beides gleichgesetzt -- zwei
verschiedene Dinge.

### Der eigentliche Befund: ein gemessenes, aber UNGENUTZTES Signal

Der Punkte-Kopf sortiert die Zuege plattenabhaengig um (Tau 0,792), der
Gegner-Kopf noch staerker (0,640). **Beide haben in der Suche derzeit das
Gewicht Null**: `points_utility_w = 0.0` und `points_utility_weight =
0.0` (Engine-Konfig, nach der Aggressions-Neukartierung ueberall auf 0).
Ihre plattenbezogene Zug-Differenzierung wird also berechnet und
verworfen.

Damit ist der Anschluss aus dem Abschnitt "Die GEGNER-Richtung" erfuellt:
das war die vorab benannte Bedingung, unter der w>0 ein **NEUES**
Argument bekommt und kein Wiederaufguss ist. Die Neukartierung hatte die
allgemeine Punkte-Marge getestet, nicht plattenspezifische
Differenzierung. Der naechste Schritt ist damit eine eigene
Vorregistrierung fuer w>0 mit Arena-Entscheid -- nicht der
Analogieschluss, dass es schon helfen werde.

### Was an der Messung wackelt (vom Agenten gemeldet, hier uebernommen)

- n=12 Zustaende; Streuung je Zustand gross (Tau 0,138-1,0, relative
  Verschiebung 0,017-1,068). Die Medianwerte tragen, einzelne Zustaende
  nicht.
- Zwei der zwoelf Zustaende haben nach Kandidaten-Angleichung nur 2
  Kandidaten -- dort kann Tau nur ±1 annehmen. Grob aufgeloest, aber
  nicht falsch.
- Die Aggregations-REIHENFOLGE (je Zustand ueber Kombinationspaare
  mitteln, dann Median ueber Zustaende) war eine Praezisierung des
  Agenten; mein Amendment liess sie offen. Im JSON dokumentiert.
- Ausrichtung der Kandidaten ueber `description`, weil `action_id`
  zwischen Aufrufen nachweislich instabil ist.
- Ein Zustand zeigt Tau 0,554 bei relativer Verschiebung 0,017 -- die
  beiden Metriken erfassen verschiedene Aspekte und stimmen nicht immer
  ueberein. Die Regel verlangt beide, das ist hier die konservative
  Seite.
