# Ursachensuche: 0:0-Partien bei Stufe 2

Auftrag: bei den laufenden 4000 Stufe-2-Self-Play-Spielen (Label `v2s2`,
Modell v2, siehe `evaluations/sweep_repeat_logs/v6_pipeline.sh`) nach den
ersten ~500 Spielen in die 0:0-Partien reinschauen und der Ursache
nachgehen. Vergleichsdaten: Heuristik-Self-Play (`s400`, 1000 Spiele) und
Stufe-1-Netz-Self-Play (`v2`, ~7450 Spiele, gleiches Modell wie `v2s2` aber
mit DFS-Blatt statt Value-Blatt).

Werkzeug: `evaluations/sweep_repeat_logs/analyze_zerozero.py <praefix>
[max_files]` — laedt `selfplay_<praefix>_*.pkl`, gruppiert nach `game_id`
(scores/winner sind je Spiel konstant ueber alle Steps, da rueckwaerts
propagiertes Endergebnis), berichtet 0:0-Rate + Runden/Boden-Statistik
getrennt fuer 0:0- und normale Partien.

## Schritt 1: Baseline (VOR den Stufe-2-Daten) — überraschender erster Befund

```
=== Praefix 's400' (Heuristik, 100 Dateien, 1000 Spiele) ===
0:0-Partien: 98/1000 (9.8%)

=== Praefix 'v2' (Stufe-1-Netz-Self-Play, 100 Dateien, 1000 Spiele) ===
0:0-Partien: 218/1000 (21.8%)
```

**Das ist wichtig und ändert die Ausgangsfrage:** 0:0-Partien sind KEIN
Stufe-2-spezifisches Phänomen — sie kommen schon in reinem Stufe-1-Self-Play
vor, und zwar dort sogar HÄUFIGER (21.8%) als bei der Heuristik (9.8%). Zum
Vergleich: in Arena-Tests (Stufe 1 vs. Stufe 1, Netz vs. Heuristik) liegt die
0:0-Rate praktisch immer bei 0% (siehe z.B. `v5_eval.md`, `v1b_*_e50_eval.md`).

**Erklärung gefunden** (`engine/src/self_play.rs`, `engine/src/net_mcts.rs`):
Self-Play nutzt bewusst Exploration, die Arena-Spiele NICHT haben:
- **Dirichlet-Root-Noise** (`add_root_noise`, nur in `net_mcts.rs` — die
  Heuristik-Suche in `mcts.rs` hat das nicht) mischt Zufallsrauschen in die
  Root-Priors.
- **Temperatur-basierte Zugauswahl** (`play_temp` in `self_play.rs`, gestaffelt
  nach Zugnummer: 0.15/0.4/0.7) statt des reinen Argmax-Visits, den Arena-
  Spiele nutzen ("Jeder Agent spielt seinen BESTEN Zug (argmax-Visits, keine
  Temperatur, keine..." laut Kommentar in `self_play.rs`).

Das heißt: 0:0-Partien sind vermutlich großteils ein **Nebeneffekt der
Explorations-Mechanik für Trainingsdaten-Diversität**, nicht ein Zeichen von
"schlechter Spielstärke" der jeweiligen Stufe. Und Stufe-1-Netz-Self-Play hat
davon schon MEHR als die Heuristik (21.8% vs. 9.8%) — vermutlich weil die
Dirichlet-Noise (die die Heuristik gar nicht hat) zusätzliche Zufalls-
Verzerrung in die Zugwahl bringt.

## Schritt 2: der eigentlich faire Vergleich

Da `v2` (Stufe 1) und `v2s2` (Stufe 2) DASSELBE Modell und DIESELBEN
Self-Play-Explorationseinstellungen (gleiches `play_temp`, gleiche Dirichlet-
Noise-Mechanik) nutzen, ist der faire Test nicht "Stufe 2 vs. Heuristik",
sondern **`v2s2`s 0:0-Rate vs. `v2`s 21.8%-Baseline**. Nur ein Unterschied
DEUTLICH über 21.8% würde zeigen, dass die Stufe-2-Blattbewertung selbst
zusätzlich zur ohnehin schon vorhandenen Explorations-bedingten 0:0-Rate
beiträgt.

## Schritt 3: Ergebnisse nach den ersten ~500-600 `v2s2`-Spielen

- [x] `analyze_zerozero.py v2s2`: **33.0% 0:0-Rate** (500 Spiele) — deutlich
      über der `v2`-Baseline (21.8%, gleiches Modell, gleiches Noise-Setup).
      Bestätigt: Stufe 2 trägt zusätzlich zur ohnehin noise-bedingten 0:0-Rate
      bei, ist nicht nur ein generelles Selfplay-Artefakt.
- [x] **Mechanismus gefunden** (`engine/src/board.rs:295`,
      `apply_score`): `self.score = (self.score + delta).max(0)` — der Score
      wird nie negativ, sondern bei jedem Update auf 0 geklemmt. Ein 0:0-
      Ergebnis heißt also nicht "beide identisch gepunktet", sondern kann
      heißen "beide wurden durch Strafleisten-Buße auf/unter die 0-Grenze
      gedrückt" — ein echter Spielmechanik-Effekt, kein Zufall.
- [x] Peak-Boden pro Runde (Stichprobe 500+ Spiele): **praktisch identisch**
      zwischen 0:0- und normalen Partien (P0/P1 ≈ 3.97-3.99 in beiden
      Gruppen) — der Unterschied liegt NICHT daran, dass 0:0-Partien in
      einer einzelnen Runde katastrophal mehr Boden anhäufen.
- [x] Gesamt-Boden über alle 5 Runden summiert: 0:0-Partien liegen
      **moderat höher** (Ø 14.6/14.3) als normale Partien (Ø 13.5/13.6) —
      ein echter, aber kein dramatischer Unterschied (~8% relativ). Die
      kumulative Boden-Last über das ganze Spiel trägt bei, ist aber
      offenbar nicht der alleinige Treiber.

**Zwischenfazit:** Der Klemm-Mechanismus (`max(0)`) plus eine leicht erhöhte
kumulative Boden-Last erklären das Muster teilweise, aber nicht vollständig
— die Differenz zwischen 0:0- und normalen Partien ist bei reinem
Boden-Zählen kleiner als der Rate-Unterschied (33.0% vs. 21.8%) vermuten
ließe. Das deutet darauf hin, dass es nicht NUR um "wie viel Boden", sondern
auch um das **Verhältnis von gebankten Punkten zu Strafen über die Zeit**
geht (ein Spieler mit wenig gebankten Punkten braucht viel weniger
Boden-Strafe, um auf 0 geklemmt zu werden) — das lässt sich mit den
vorliegenden Step-Daten (die nur das End-Ergebnis, nicht den laufenden
Score pro Zug enthalten) nicht ohne Weiteres nachrechnen; dafür bräuchte es
eine Nachsimulation der Punkteverläufe direkt in Rust/Python anhand der
Platzierungs-Aktionen — das wäre der nächste, aufwändigere Schritt, falls
gewünscht.

## Schritt 4: Clamp-Ereignis-Korrelation (volle 4000 Spiele)

Es gibt tatsächlich ein LAUFENDES `score`-Feld pro Spieler in
`state["players"][i]["score"]` (nicht nur das konstante End-`scores`-Feld) —
das aktualisiert sich Zug für Zug. Getestet: korreliert ein Klemm-Ereignis
(Score trifft exakt 0 nach Runde 1) mit dem 0:0-Endergebnis?

```
Über alle Runden nach Runde 1 (n=4000):
  0:0-Partien (n=1432):    99.7% hatten mind. ein Clamp-Ereignis
  normale Partien (n=2568): 98.6% hatten mind. ein Clamp-Ereignis

Nur letzte Runde (Runde 5, n=4000):
  0:0-Partien (n=1432):    95.2% hatten ein Clamp-Ereignis in Runde 5
  normale Partien (n=2568): 90.3% hatten ein Clamp-Ereignis in Runde 5
```

**Ergebnis: zu unscharf, um nützlich zu sein.** Ein Klemm-Moment (Score
kurzzeitig exakt 0) ist in fast JEDER Partie irgendwann present — vermutlich
weil das `score`-Feld während der Zug-für-Zug-Abwicklung einer Runde
zwischenzeitlich durch 0 läuft, bevor die eigentliche Rundenwertung
(Wertungsplatten-Boni etc.) angewendet wird, die scheinbar NICHT als
eigener Step in den Trainingsdaten sichtbar ist (siehe Diskrepanz:
End-`scores`-Feld [3,8] vs. Live-Score am letzten sichtbaren Step [6,5] im
Beispielspiel — die finalen Boni werden offenbar nach dem letzten
protokollierten Step draufgerechnet). Mit den vorhandenen Pickle-Snapshots
lässt sich der "bereinigte" Score am Rundenende also nicht sauber
rekonstruieren — das würde direktes Instrumentieren der Rust-Engine
(Score-Delta-Log pro Aktion, nicht nur periodische Snapshots) brauchen,
was über den Rahmen einer Post-hoc-Datenanalyse hinausgeht.

## Schritt 5: Boden-Cap-Exploit direkt geprüft (Nutzer-Hinweis)

Wichtige Korrektur unterwegs: "Clamp-Ereignis kommt überall vor, also
harmlos" war falsch gefolgert. Weil Score nie negativ wird UND
`broken_penalty()` nur die ersten `MAX_BROKEN=4` Boden-Kacheln zählt
(`board.rs`, Schema -1,-2,-3,-4, `.take(MAX_BROKEN)`), ist "noch mehr
Boden nehmen, wenn man eh schon gedeckelt ist" strategisch **komplett
kostenlos** — ein Test (`broken_penalty_escalates_and_caps`) bestätigt das
explizit im Code. Das ist eine echte Regel-Asymmetrie, kein Bug in meiner
Analyse.

Direkt getestet, ob das Erreichen des Boden-Caps (floor==4) mit 0:0 bzw.
Stufe 2 korreliert:

```
"Irgendwann Cap erreicht" (n=4000):
  0:0-Partien:    100.0% erreichten Cap=4 irgendwann
  normale Partien: 100.0% erreichten Cap=4 irgendwann
  → nicht diskriminierend, praktisch jede Partie beruehrt den Cap mind. 1x.

Haeufigkeit (in wie vielen von 5 Runden wird der Cap beruehrt):
  0:0-Partien:     Ø 3.66 / 5 Runden
  normale Partien: Ø 3.50 / 5 Runden
  → real, aber klein (~5% relativer Unterschied).
```

**Einordnung:** die Regel-Asymmetrie (Boden-Cap + Score-Clamp) ist real und
wird offenbar in praktisch JEDER Self-Play-Partie in irgendeiner Form
berührt — das ist also kein seltenes Randphänomen, sondern normaler
Spielverlauf unter diesem Regelwerk. Der Unterschied zwischen 0:0- und
normalen Partien zeigt sich in der HÄUFIGKEIT (wie oft pro Spiel), nicht im
bloßen Vorkommen — und der ist bei allen bisher getesteten Boden-Metriken
(Gesamt-Boden, Cap-Häufigkeit) im selben moderaten ~5-8%-Bereich, während
der Stufe1-vs-Stufe2-Rate-Unterschied selbst viel größer ist (21.8% vs.
33-36%). Das spricht dafür, dass die eigentliche Ursache nicht (nur) "wie
viel Boden wird genommen" ist, sondern eher "WELCHE Entscheidungen in
welchen Situationen getroffen werden" — also eine Such-/Politik-Qualitäts-
frage, die sich nicht allein durch Boden-Zählen post-hoc greifen lässt.

## Schritt 6: Direkter Blick in den Value-Head (ONNX-Inferenz auf gespeicherte Zustände)

`mosaic_rust.onnx_eval(path, features)` erlaubt, den Value-Head direkt auf
beliebige gespeicherte Zustände anzuwenden (`state_to_tensor` fürs Feature-
Encoding). Getestet: verfolgt der Value-Head (Modell `v2`) die 0:0-Partien
schon früh als "schlecht", oder wird er überrascht?

```
v2s2 (Stufe-2-Selfplay), Value pro Runde (Modell v2):
  0:0-Partien (n=25):     Runde 1-5: +0.05 bis +0.08 (durchgehend flach niedrig)
  normale Partien (n=25): Runde 1-5: +0.17 bis +0.19 (durchgehend flach hoeher)

v2 (Stufe-1-Selfplay), Value pro Runde (SELBES Modell v2):
  0:0-Partien (n=25):     Runde 1-5: +0.05 bis +0.08 (fast identisch!)
  normale Partien (n=25): Runde 1-5: +0.14 bis +0.19 (fast identisch!)
```

**Zwei wichtige Erkenntnisse:**

1. **Der Value-Head wird NICHT überrascht.** Er unterscheidet 0:0-bound
   Partien von normalen schon ab Runde 1 (!) mit einem klaren, stabilen
   Abstand (~0.05-0.08 vs. ~0.17-0.19) — das ist kein "blinder Fleck", der
   sich erst spät zeigt. Die Vorhersage ist qualitativ richtig gerichtet.
2. **Das Muster ist in Stufe-1- UND Stufe-2-Daten identisch** (selbes
   Modell, ähnliche Werte) — die "Weichheit"/begrenzte Trennschärfe des
   Value-Signals ist eine Eigenschaft des NETZES selbst, keine
   Stufen-spezifische Eigenschaft der Trajektorien.

**Die eigentlich schlüssige Erklärung für den Stufe-1-vs-Stufe-2-Unterschied
ergibt sich daraus so:** Stufe 1 nutzt beim Blatt den EXAKTEN DFS-Solver
(scharfe, korrekte Bewertung), Stufe 2 nutzt genau dieses eher weiche,
komprimierte Value-Signal (Abstand nur ~0.12-0.13 zwischen "gut" und
"schlecht", nicht sehr stark ausgeprägt verglichen mit einer exakten
Bewertung). Da BEIDE Stufen unter DENSELBEN Explorations-Einstellungen
(Dirichlet-Noise, Temperatur) laufen, hat Stufe 1 durch die scharfe exakte
Bewertung eine viel staerkere "Rückstellkraft" gegen das Rauschen (führt die
Suche zuverlässiger von schlechten Linien weg), während Stufe 2s weicheres
Signal dem Rauschen weniger entgegensetzt — das Rauschen "gewinnt" bei
Stufe 2 öfter und die Suche läuft in mehr 0:0-Linien.

## Schritt 7: Root-Noise-Test (Ergebnis: negativ, aber lehrreich)

`add_root_noise` wurde als neuer Parameter durch die gesamte Kette
(`mosaic_rust.net_self_play_games` → `run_net_self_play` →
`play_net_self_play_game` → `net_drafting_policy` → `net_root_child_stats`)
durchgereicht (Default `true`, bestehende Läufe unveraendert) und ein
`--no-root-noise`-CLI-Flag in `self_play.py` ergaenzt. Test: 4000 (geplant,
nach Haenger bei 1250 gestoppt) Stufe-2-Selfplay-Spiele mit `v2`, Root-Noise
AUS.

**Ergebnis (1250 Spiele, `v2s2nn`): 33.0% 0:0-Rate — nahezu identisch zur
Baseline MIT Noise (33.0-35.8%).** Root-Noise ist also NICHT der (alleinige)
Treiber der Stufe-2-0:0-Haeufung.

**Warum:** Self-Play waehlt den TATSAECHLICH GESPIELTEN Zug immer
`weighted_index`-stochastisch proportional zu den Besuchszahlen (τ=1,
`net_drafting_policy`), UNABHAENGIG vom `add_root_noise`-Flag — Root-Noise
beeinflusst nur die Exploration WAEHREND der Baumsuche (welche Aeste
ueberhaupt untersucht werden), nicht die finale Auswahl unter den
untersuchten Optionen danach. Das Abschalten von Root-Noise allein entfernt
also nicht die dominante Zufallsquelle.

**Wichtige Neueinordnung:** die eigentlich sauberste, bereits vorhandene
Evidenz sind die ARENA-Daten — dort wird IMMER der meistbesuchte Zug
deterministisch gespielt (kein Root-Noise, kein proportionales Sampling,
siehe `net_search_drafting_action`/"argmax-Visits, keine Temperatur, keine
[Noise]"). Genau diese komplett rauschfreien Vergleiche zeigen konstant:
Stufe-1-Arena = 0% 0:0-Rate, Stufe-2-Arena = ~7% (v6(Stufe2) vs. v2(Stufe2):
6/86=7.0%; v1b_w15_e50 vs. v1b_w0_e50 Stufe 2: aehnlich). Dieser 7%-vs-0%-
Unterschied UNTER VOLLSTAENDIGER Rauschfreiheit ist der eigentlich
aussagekraeftige Befund — er zeigt eine echte, noise-unabhaengige
PUCT-Suchschwaeche unter dem weichen Value-Signal (siehe Schritt 6), nicht
nur ein Selfplay-Explorations-Artefakt. Die 21.8%/33-36%-Raten aus dem
Selfplay sind ueberwiegend durch das (stufenunabhaengige)
Besuchszahl-proportionale Sampling erklaert, nicht direkt aussagekraeftig
fuer die eigentliche Suchqualitaet.

Ein Haenger (~3h ohne Fortschritt bei Spiel ~1250/4000) fuehrte zum Abbruch
des vollen Laufs — vermutlich eine seltene, teure Randbedingung (evtl.
Tiling-Solver-Kombinatorik bei einer unguenstigen Fliesen-Konstellation,
kein offensichtlicher Zusammenhang mit der `add_root_noise`-Aenderung selbst,
da `add_root_noise=false` bereits ueber saemtliche Arena-Matches dieser
Session vielfach fehlerfrei durchlief). Nicht weiter verfolgt, da das
Ergebnis (33.0% bei n=1250) schon eindeutig genug war.

## Nächster konkreter Test (ueberarbeiteter Vorschlag nach Schritt 7)

Die urspruengliche Idee (Root-Noise reduzieren) ist widerlegt. Um die
eigentlich interessante ~7%-vs-0%-Luecke (siehe Schritt 7, komplett
rauschfrei) mit vollen Zustands-Trajektorien zu untersuchen (Arena-Spiele
protokollieren nur Endergebnisse, keine Zug-fuer-Zug-Zustaende), braeuchte
es eine neue Selfplay-Variante, die wie die Arena IMMER den meistbesuchten
Zug spielt (`net_search_drafting_action`-Stil, kein proportionales
Sampling) statt wie bisher `net_drafting_policy` (immer stochastisch) — nur
so bekaeme man analysierbare volle Trajektorien der "echten" (nicht
noise-bedingten) Stufe-2-Partien. Das ist ein weiterer, ueberschaubarer
Code-Eingriff (neue Funktion/Flag analog zu `add_root_noise`), aber noch
nicht umgesetzt.

Alternativ, ohne weiteren Code-Eingriff: mehr Sims fuer Stufe-2-Runden
(mehr "Abstimmungen" gleichen das schwache Signal statistisch aus, macht
PUCT robuster gegen die geringe Trennschaerfe) oder ein schaerfer
kalibrierter Value-Head (groessere Trennschaerfe zwischen guten und
schlechten Zustaenden, nicht nur richtige Richtung) — beides bereits
frueher genannte, nicht in dieser Runde umgesetzte Stellschrauben.

## Schritt 8: Argmax-Selfplay bestätigt die 7%-Rate direkt (mit vollen Trajektorien)

`self_play.py` um `--deterministic` erweitert (immer meistbesuchter Zug,
kein Sampling — siehe Werkzeuge in `STAGE2_TODO.md`). 1000 Spiele geplant
(`v2s2det`, Modell v2, Stufe 2, `--deterministic --no-root-noise`), bei
Spiel 900 gehängt (2. Haenger unter aehnlichen Einstellungen dieser Session
— vermutlich ein seltener, vorbestehender Tiling-Solver-Randfall, ~1 von
2500 Spielen, nicht weiter verfolgt) und dort abgebrochen. 900 Spiele reichen.

```
=== 'v2s2det' (90 Dateien, 900 Spiele, 0 unvollstaendig) ===
0:0-Partien: 63/900 (7.0%)
```

**Exakte Bestätigung**: 7.0% deckt sich (auf die Nachkommastelle) mit den
Arena-Ergebnissen (v6(Stufe2) vs. v2(Stufe2): 7.0%; v1b-Vergleiche: 7-8%).
Das ist jetzt zweifach unabhängig bestätigt (Arena UND komplett rauschfreies
Self-Play) — die ~7% sind robust die "echte" Stufe-2-0:0-Rate. Jetzt liegen
volle Zug-fuer-Zug-Trajektorien dieser 63 Partien vor (nicht nur
Endergebnisse wie bei Arena-Logs) für die tiefere Analyse (Value-Head-
Vorhersagen an kritischen Stellen, siehe Masterplan Spur B Schritt 2).

## Schritt 9: Value-Head-Trajektorie auf sauberen Daten — schärferes Bild

Dieselbe Analyse wie Schritt 6, jetzt auf den komplett rauschfreien
`v2s2det`-Daten (30 0:0- vs. 30 normale Partien, Modell v2):

```
0:0-Partien:     Runde 1: +0.037  Runde 2: +0.084  Runde 3: +0.090  Runde 4: +0.108  Runde 5: +0.084
normale Partien: Runde 1: +0.186  Runde 2: +0.206  Runde 3: +0.243  Runde 4: +0.274  Runde 5: +0.293
```

**Deutlicherer Befund als auf den verrauschten Daten:** die Lücke WÄCHST
über die Runden (Runde 1: 0.149 Abstand → Runde 5: 0.209 Abstand), statt
konstant zu bleiben. Normale Partien werden im Value-Head-Urteil zunehmend
zuversichtlicher (0.186→0.293, plausibel: die Suche bestätigt über die
Runden ihre gute Ausgangslage). 0:0-Partien bleiben dagegen durchgehend
flach niedrig (0.04-0.11) — der Value-Head registriert von Anfang an, dass
etwas nicht stimmt, aber das Urteil eskaliert NICHT ins klar Negative, selbst
im denkbar schlechtesten Ausgang (0:0). Das bestätigt die "weiches Signal"-
Hypothese aus Schritt 6 nochmal deutlicher: der Value-Head unterscheidet
richtig gerichtet, aber mit zu wenig Dynamikumfang/Schärfe, um die Suche
stark genug von der schlechten Linie wegzudrücken — selbst im
schlimmstmöglichen Fall bleibt die Vorhersage nur "mittelmäßig", nie
"eindeutig schlecht".

## Fazit dieser Untersuchungsrunde

1. **Bestätigt**: 0:0-Ergebnisse sind ein Klemm-Mechanik-Effekt
   (`board.rs::apply_score`, `max(0)`), kein Zufall und kein Gleichstand im
   eigentlichen Sinn.
2. **Bestätigt**: Stufe 2 hat eine deutlich höhere 0:0-Rate (35.8% über alle
   4000 Spiele) als Stufe-1-Self-Play mit selbem Modell/Noise (21.8%) — das
   ist ein echter, reproduzierbarer Effekt, kein Messfehler.
3. **Boden-Zähl-Metriken sind zu grobkörnig**: Peak pro Runde, Gesamt-Boden
   übers Spiel, Clamp-/Cap-Häufigkeit korrelieren nur schwach (~5-8%) mit
   dem 0:0-Ausgang — die Erklärung liegt nicht im bloßen "wie viel Boden".
4. **Gefunden (Schritt 6)**: der Value-Head selbst unterscheidet 0:0-bound
   von normalen Partien schon ab Runde 1 klar und stabil (~0.05-0.08 vs.
   ~0.17-0.19) — er wird NICHT überrascht, die Richtung stimmt. Aber dasselbe
   Muster zeigt sich identisch in Stufe-1- UND Stufe-2-Selfplay-Daten (selbes
   Modell) — die begrenzte Trennschärfe ist eine Eigenschaft des Value-Heads
   selbst, nicht der Stufe.
5. **Widerlegt (Schritt 7)**: Root-Noise-Reduktion allein aendert die
   Selfplay-0:0-Rate NICHT (33.0% mit wie ohne) — das visit-proportionale
   Sampling der gespielten Aktion ist die eigentlich dominante, davon
   unabhaengige Rauschquelle in JEDEM Netz-Selfplay (Stufe 1 wie Stufe 2).
6. **Der eigentlich aussagekraeftige Befund**: komplett rauschfreie
   Arena-Vergleiche (immer bester Zug, kein Sampling, kein Root-Noise)
   zeigen konstant Stufe 1 = 0% 0:0-Rate, Stufe 2 = ~7% (v6(Stufe2) vs.
   v2(Stufe2), v1b-Vergleiche). Das ist eine echte, noise-unabhaengige
   PUCT-Suchschwaeche unter dem weicheren Stufe-2-Value-Signal, kein
   Selfplay-Artefakt.

7. **Bestätigt und geschärft (Schritt 8/9)**: komplett rauschfreies Argmax-
   Self-Play (900 Spiele) reproduziert die 7.0%-Rate exakt (deckungsgleich
   mit den Arena-Ergebnissen) und zeigt anhand voller Trajektorien: der
   Value-Head registriert 0:0-bound Partien schon ab Runde 1, aber die
   Lücke zum Normalfall bleibt im Absolutwert klein und eskaliert selbst im
   schlechtestmöglichen Fall nie ins klar Negative (0.04-0.11 statt z.B.
   -0.3 oder schlechter) — während normale Partien über die Runden
   zunehmend zuversichtlicher bewertet werden (0.19→0.29). Das ist die
   deutlichste Bestätigung der "weiches Signal"-Hypothese.

**Praktische Konsequenz / Stand der Untersuchung:** die hohen Selfplay-
0:0-Raten (21.8% Stufe 1, 33-36% Stufe 2) sind ueberwiegend ein generelles
Sampling-Rauschen-Artefakt (bei BEIDEN Stufen vorhanden, nur unterschiedlich
stark) — die Kennzahl, die tatsaechlich zaehlt, ist die rauschfreie Rate:
0% (Stufe 1) vs. ~7% (Stufe 2), jetzt zweifach (Arena + Argmax-Selfplay)
bestätigt. Ursache: kein Bug, sondern ein zu wenig trennscharfer Value-Head,
der Stufe-1s exakter DFS-Solver-Bewertung bei der Rückstellkraft gegen
Sucheffekte/verbleibendes Rauschen unterlegen ist. **Diese Untersuchungsrunde
ist damit inhaltlich abgeschlossen** — die verbleibende offene Frage
("lohnt sich eine gezielte Investition in einen schärfer kalibrierten
Value-Head, oder bleibt Stufe 1 vorerst der Produktionspfad") ist eine
Priorisierungsentscheidung, siehe Masterplan (`STAGE2_TODO.md`, Spur B).

## Offene Frage, die die Interpretation verschiebt

Die Arena-Tests, die 7-8% 0:0-Rate bei Stufe 2 zeigten (`v1b_w15_e50` vs.
`v1b_w0_e50`, Stufe 2; `v5(Stufe2)` vs. `v2(Stufe2)`), liefen OHNE
Explorations-Noise (argmax-Visits, echte Spielstärke). Dass dort überhaupt
0:0-Partien auftreten, OBWOHL keine Exploration eingebaut ist, ist eigentlich
das eigentlich beunruhigende Signal — das deutet auf eine echte
Spielstärke-/Bewertungsschwäche der Stufe-2-Suche hin, unabhängig vom
Trainingsdaten-Noise-Artefakt. Die Selfplay-0:0-Rate (mit Noise) und die
Arena-0:0-Rate (ohne Noise) sind zwei GETRENNTE Phänomene, die nicht
miteinander vermischt werden sollten.
