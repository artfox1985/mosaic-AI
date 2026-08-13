# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`**.

---

## STAND 2026-08-13

**Champion unveraendert: `v21_2d_brierbest`, Elo 1358** [1292, 1434]. Kein
Gating gelaufen, kein Modell gewechselt. Paritaets-Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` haelt
(mehrfach nach jedem Wheel-Neubau geprueft). Die vollstaendige Nacht-Herleitung
(Provokations-Messung Spaltenbau, GPU-Weg-A/B-Messreihe, λ/Punkte-Kanal,
Injektions-Messung der Wertungsplatten, Ownership-Kopf-Zuschnitt,
Spezialpunkte-Korrektur, methodische Lehren) liegt in `../archive/history.md`,
Kapitel "2026-08-11/13: Wertungsplatten-Nacht, GPU-Weg-B, Zwei-Pole". Verdikte
vom 2026-08-10 selbst: Kapitel "2026-08-10" davor im selben Dokument.

### NACHTRAG 2026-08-13: RNG-Schnitt Suche/Partie umgesetzt (PREREG_such_rng_trennen.md)

Vollstaendig umgesetzt, freigegeben durch Nutzer-Entscheidungen §8 der Prereg
(Elo-Sprung wird nur vermerkt, Basislinie neu gesetzt sobald der Hash bricht).
Kern: `net_mcts::derive_search_seed(game_seed, move_index)` (SplitMix64,
zweistufig gemischt) liefert je Such-/Entscheidungsschritt einen EIGENEN,
deterministischen RNG -- Aufruf-Verdrahtung in `self_play.rs` (7 Spielschleifen:
`play_one_game`, `play_arena_game`, `play_net_game`, `play_net_vs_net_game`,
`play_net_self_play_game`, jeweils inkl. PCR-Muenzwurf/`moon_order_target`) und
`py.rs::PyGame` (`ai_drafting_step`/`ai_drafting_net_step`, neues Feld
`move_seq`). `mcts.rs`/`net_mcts.rs` selbst UNVERAENDERT (nur Verdrahtung an
den Aufrufstellen) -- der Heuristik-Bewertungspfad (`player_total`/
`wertung_progress`) ist nicht angefasst.

**Befund unterwegs (REGEL 0, Analyse statt Basislinie verschoben)**: der
tatsaechliche sims-proportionale RNG-Verbrauch sitzt in `mcts.rs`s
Heuristik-MCTS (`expand_and_backprop`s Widening-Tie-Break,
`rank_actions_cheap`s Shuffle -- ECHT pro Simulation), NICHT in der
Netz-Gumbel-Suche (`net_mcts.rs::sample_gumbel`/`determinize_hidden_information`
sind root-einmalig, unabhaengig von `sims`). Der §5-Test musste deshalb
umgebaut werden (Details unten) -- betrifft nur die Testkonstruktion, der
Schnitt selbst deckt beide Suchpfade gleich.

**§5-Test** (`shadow_search_volume_does_not_shift_factory_supply_stream`,
self_play.rs): echte Zuege sims-unabhaengig auf `actions[0]` fixiert (sonst
waere Entscheidungsvarianz mit dem RNG-Befund verwechselt worden -- erste
Testfassung schlug deshalb fehl, siehe Commit-Historie), eine verworfene
"Schatten"-Heuristiksuche mit sims=1 bzw. 400 daneben. VOR dem Fix (Gegenprobe,
geteilter RNG statt `search_rng`): Fabrikinhalte weichen exakt in Runde 4 ab.
NACH dem Fix: 0 Abweichungen ueber alle Rundenwechsel.

**Paritaetshash haelt UNVERAENDERT** (`8c6684ff...`, s.o.) -- ENTGEGEN der
Prereg-§4a-Erwartung ("Hash MUSS brechen"). Geprueft: die Sonde haengt
ausschliesslich an `net_search_state_json` (lib.rs), einem Einzelaufruf-Pfad
mit eigenem frischen `rng` pro Aufruf, der nie Teil einer fortlaufenden
Partie-Schleife war -- der behobene Fehler trat dort strukturell nicht auf.
Kommentar dazu in `tools/paritaets_probe.py` ergaenzt; keine neue Basislinie
noetig, weil sich nichts geaendert hat.

**Replay-Kreuzvalidierung**: 5 frische `--log-games`-Arena-Partien
(`net_arena_match`, net_sims=40 vs. heur_sims=40) -> `tools/analyze_game_log.py
--no-oracle`: **5/5 Exit 0**, keine Divergenz, kein Runde-4-Abbruch mehr
(vorher 5/5 Arena-Partien betroffen). Elo-Sprung-Vermerk in
`evaluations/elo_history.csv` (Zeile nach dem Muster der Engine-Aera-Zeile 24)
traegt exakt diese 5 Partien (3:2), ausdruecklich als duenne
Kreuzvalidierungs-Charge markiert, keine Staerkeaussage.

**Async-Gate-B-Nachprobe** (`sync_only_repeatability_after_rng_split`,
`#[ignore]`, self_play.rs -- Nachstellung des `wt_async`-Befunds im
Hauptbaum): `play_net_self_play_game` viermal gegen sich selbst, identischer
Seed, `record_rtv=true`. Ergebnis: **0/4 Spielgeschehen-Abweichungen, 0/4
volle Abweichungen** (letztere schliessen `round_transition_value`/
`bootstrap_value` mit ein und duerften an der separaten Wall-Clock-Komponente
aus Task #71 haengen -- traten hier aber gar nicht auf). Die im
`wt_async`-Befund dokumentierte Instabilitaet ("Sync weicht von sich selbst
ab") ist damit, soweit sie am geteilten RNG hing, behoben.

**Bewusst NICHT umgestellt** (bewusste Entscheidung, ausserhalb des
vorregistrierten Kerns, dokumentiert statt stillschweigend liegen gelassen):
`play_net_vs_net_hybrid_game`, `play_stage3_vs_stage1_game`,
`sibling_ranking_diagnostic` (alle drei reine Diagnose-/Forschungswerkzeuge,
kein Self-Play-/Gating-Pfad) sowie `round_transition.rs`/
`round_transition_deep.rs`s Rundenuebergangs-/Bootstrap-Sampling (additive
Trainingsziele auf einem Zustands-Klon, beeinflussen nie den gespielten Zug
oder die echte Fabrikversorgung, siehe §5-Testkommentar).

**Was NICHT ins Archiv gehoert, weil es heute (2026-08-13) neu und noch offen
ist**: die Produktionsmessung von GPU-Weg-B (NACHTRAG direkt unten) und die
Zwei-Pole-Architektur als geltender Plan (danach).

### NACHTRAG 2026-08-13: Weg B (ORT-CUDA) über den ECHTEN Self-Play-Pfad NICHT GEDECKT

`PREREG_gpu_inferenzpfad.md` §19 (volle Zahlen:
`evaluations/gpu_inferenzpfad_selfplay_e2e_wegb.json`). Erste Messung über den
Produktionspfad selbst (`self_play.py`, nicht ein Beispiel-Binary): Batcher+
ORT-CUDA bei 8 Threads (die einzige beidseitig belastbare Zelle, 40/40 gegen
23/40 echte Partien) ist **3,4x LANGSAMER** als der Bestand (2190,3s gg. 638,4s
für dieselben 40 Partien) -- Regel-3-Faktor 0,29x/0,17x, klar unter 1,0x, weit
unter der 2,0x-Schwelle. Das trotz nahezu gesättigtem Batch (14,64 von 16) --
die §9-Erwartung ("Weg B hat die Kostenposten von Weg A nicht, sollte also
gewinnen") trägt hier NICHT, Ursache ungeklärt (Kandidaten: `Mutex<Session>`
als serialisierendes Nadelöhr, `Session::run()`-Kosten unter echter statt
synthetischer Ankunftsrate). Bei 64 Threads sind BEIDE Arme durch den
Chunk-Hänger-Notdeckel degeneriert (3/40 bzw. 0/40 echte Partien) --
diese Zelle liefert keinen verwertbaren Faktor. Verdrahtung selbst (Batcher im
Suchpfad, ORT-CUDA-Rangfolge) war bereits vollständig vorhanden, nicht neu
gebaut. Nächster Schritt liegt beim Nutzer: Ursachenzerlegung (BatcherStats
hat bisher keine Latenzverteilung je `eval_batch`-Aufruf) oder Weg B als
erledigt einstufen.

### AKTUALISIERUNG 2026-08-13: Zwei-Pole-Architektur ist der geltende Rahmen

**ENTSCHIEDEN 2026-08-13 (Nutzer)**: k0/k7 bekommen KEINEN eigenen Bauer --
Spieloekonomie, nicht Fehlschlag (`docs/domain_knowledge.md` Abschnitt 7; deckt
sich mit §13: k7 Stopp-Regel, k0 negativ). Beilaeufige Korpus-Abdeckung wird
im Piloten per Grundraten-Gate geprueft.

**OFFEN, Nutzer-Auftrag 2026-08-13**: Plattenbauer k6 (Spezialfelder) Runde 2 als
KUPPELDRAFT-Strategie (`docs/domain_knowledge.md` Abschnitt 8: Joker horten und nach
unten, erzwungene Spezialkuppeln nach oben, Joker-Priorisierung als Stoerkanal).

**OFFEN, Nutzer-Auftrag 2026-08-13**: Plattenbauer k2 (Diagonalen) und k5 (Ecken)
Runde 2 mit der Nutzer-Taktik aus `docs/domain_knowledge.md` Abschnitte 5-6
(Spezial-/Joker-Kuppelwahl als Kern statt Farbenjagd; k2 muss zusaetzlich den
Sieg-Verlust aus §13 beheben). Nach Spalten-Runde 4.

**OFFEN, Nutzer-Auftrag 2026-08-13**: Gegner-Stoerung ueber die Farbzaehlung als
Plattenbauer-Baustein NACH Runde 4 (Spezifikation + Belegstand:
`docs/domain_knowledge.md`, Abschnitt "Spielstrategie aus Nutzer-Praxis" Punkt 4).


Die vorausgehende Provokations-Messung ist UEBERHOLT und liegt jetzt in
`../archive/history.md`, Kapitel "2026-08-11/13: Wertungsplatten-Nacht,
GPU-Weg-B, Zwei-Pole". Stand von dort, `PREREG_provokation.md` §9-§10:
**vier Generator-Mechanismen enden alle bei 0,30 Spalten/Partie** (Injektion, Beschneidung, Vorzug, Vorzug beide Haelften); die
Beschneidung zerstoert das Spiel, die Vorzuege nicht. Nutzer-Entscheid: der
**Spaltenbau-Spieler** wird gebaut (Agent laeuft) -- Pol B der Zwei-Pole-
Architektur (Netz = Basispol, Wertungsheuristik = Plattenpol, Regler = kuenftiges
Konsumenten-Gewicht des Ownership-Kopfs, zur Laufzeit sweepbar). Moegliche Folge:
je Platte eine eigene Heuristik, parametrisiert statt achtfach gebaut.

GPU dazu: Weg B gedeckt (10,4-21,0x Inferenz auf dem synthetischen Pfad),
Verdrahtung von Batcher+ORT in `run_net_self_play` war schon vorhanden; Mess-
Partien gehen nach `data/gpu_messung/` (Nutzer-Anweisung, Unterordner = kein
Trainingsfenster). **UEBERHOLT durch den NACHTRAG oben**: §19 ist inzwischen
gelaufen (echter Self-Play-Pfad statt Beispiel-Binary) und zeigt 3,4x
LANGSAMER, Regel-3 NICHT erfuellt -- Entscheidung ueber das weitere Vorgehen
steht beim Nutzer aus (Ursachenzerlegung oder Weg B als erledigt einstufen).

### Such-RNG-Trennung: entscheidungsreif, NICHT gebaut

`PREREG_such_rng_trennen.md` §8. Nutzer-Entscheide liegen vor: **Elo-Sprung wird
nur vermerkt** (kein Neuverankern), Paritäts-Basislinie wird neu gesetzt und der
alte Hash daneben dokumentiert. Umsetzung ausdrücklich NACH den laufenden
Messvorhaben, weil sie die Vergleichsgrundlage verschiebt.

---

## TASK-INDEX (nur OFFEN/LAUFEND, Stand 2026-08-10)

| Task                                          | Status                                                                                                                                                                                                                                                                                                                                                                            |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: Validierung braucht arena-ENTSCHIEDENE Paare; die WDL-Aera hat bisher nur ~3 (v20>v19, E3-Arme signifikant schlechter) -- unter dem 6-Paar-Standard der Policy-Orakel-Validierung. Kandidaten-Metriken (Brier auf frozen_v2, R5-Steigung) werden ab jetzt je Gating MITGEFUEHRT; Verdikt, sobald >=6 entschiedene Paare vorliegen. `PREREG_nach34_paket.md` |
| #31 / #38 / #39                               | geparkt (Arbeitskreis "Spaeter", Details unten)                                                                                                                                                                                                                                                                                                                                   |

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

**Der Inhalt dieses Abschnitts steht jetzt in `../docs/domain_knowledge.md`**
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

---

**Verschraenkung mit der Zwei-Pole-Architektur (Praezisierung 2026-08-13)**:
Stufe 1 (Injektion) und Stufe 2 (Destillation) unten sind der Weg zum
**Basispol** (Netz); Stufe 3 (Ownership-Kopf als Konsument im Blatt) ist genau
das **Regler**-Stueck der Zwei-Pole-Architektur oben -- derselbe
"Konsumenten-Gewicht des Ownership-Kopfs, zur Laufzeit sweepbar". Der
**Plattenpol** (Wertungsheuristik, Spaltenbau-Spieler) laeuft parallel und
unabhaengig von diesen drei Stufen.

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

#### OFFEN

**Die folgenden drei Zeilen (Spaltenbau, Ownership-Kette, Aufraeumliste) sind
Nutzer-Diktat vom 2026-08-13 (dieser Auftrag). Ich habe sie in dieser Sitzung
NICHT gegen Code oder Log verifiziert -- Stand markiert als ungeprueft, keine
Fundstelle belegt, vor Weiterarbeit am Original pruefen (REGEL 0). Die
GPU-Zeile dagegen IST in dieser Sitzung geprueft -- siehe NACHTRAG oben.**

| Punkt | Stand |
| ----- | ----- |
| **Spaltenbau-Spieler, Runde 2** | Pol B der Zwei-Pole-Architektur (s.o.), zweite Bauschleife mit drei beschlossenen Aenderungen: Wild-Farben aktiv bedienen, Spezialfelder umbepreisen, Zielspalte je Seed streuen + ein Verteilungs-Gate. *Ungeprueft/Nutzer-Diktat.* |
| **GPU-Produktionsmessung** | **Gelaufen, negativ** (geprueft am NACHTRAG-Abschnitt oben, `PREREG_gpu_inferenzpfad.md` §19): Batcher+ORT-CUDA ist bei 8 Threads 3,4x LANGSAMER als der Bestand ueber den echten Self-Play-Pfad (2190,3s gg. 638,4s / 40 Partien), Regel-3-Faktor 0,29x/0,17x, weit unter der 2,0x-Schwelle. 64 Threads liefert wegen des Chunk-Haenger-Notdeckels keinen verwertbaren Wert. Entscheidung offen: Ursachenzerlegung (`Mutex<Session>`? `Session::run()` unter echter Ankunftsrate?) oder Weg B als erledigt einstufen -- Nutzer-Entscheid ausstehend. |
| **Ownership-Kette P0-P6** | Nutzer-Bezeichnung fuer die Phasenkette des Ownership-Kopfs. In diesem Dokument bisher als Drei-Stufen-Rahmen gefuehrt (Injektion -> Destillation -> Kopf-Konsum im Blatt, Abschnitt oben). Ob P0-P6 dieselbe Kette feiner unterteilt oder zusaetzliche Phasen meint: *ungeprueft, in dieser Sitzung nicht aufgeloest.* |
| **Aufraeumliste, eingetaktet** | Gating-Test-Fix; `PREREG_INDEX.md`-Konsistenz (Praezedenzfall in `../archive/history.md` Kapitel 2026-08-11/13 -- ein veralteter Index hatte dort bereits einen unnoetigen Agenten-Auftrag ausgeloest); 8 Compiler-Warnungen; Mess-JSON-Eindampfung; tote Knoepfe entfernen (`MOSAIC_ENDAWARE_W`/`MOSAIC_MUSTERREIHEN_W`, gemessen wirkungslos, s. Archiv-Kapitel; Torch-IPC-Reste von GPU-Weg-A, verworfen, s. Archiv-Kapitel); tote Streuungs-Verdrahtung entfernen. Die ersten beiden Punkte sind jetzt Teil 1+2 des ARCHITEKTUR-FAHRPLANS unten, nicht mehr getrennt zu verfolgen. |

**Such-RNG-Trennung**: entscheidungsreif, NICHT gebaut -- eigener Abschnitt
oben.

#### ARCHITEKTUR-FAHRPLAN (Nutzer-Freigabe 2026-08-13)

**Nutzer-Diktat, in dieser Sitzung NICHT gegen Code verifiziert (REGEL 0) --
Prioritaet ist Schaden-pro-Aufwand, absteigend:**

1. **PREREG_INDEX generieren statt von Hand fuehren** -- maschinenlesbarer
   Status-Kopf in den PREREG-Dateien, Index wird per Skript erzeugt,
   Konventions-Checker prueft Status-Parsing (klein; verhindert
   Fehl-Auftraege wie die veraltete GPU-Zeile, s. METHODISCHE-LEHRE-Kapitel
   in `../archive/history.md`, 2026-08-11/13).
2. **Stille Test-Skips verbieten** -- Tests mit fehlender Voraussetzung
   muessen failen oder `#[ignore]` mit Grund tragen, nie leer "passed"
   (klein; Anlassfall `load_test_net_for_gating`, dessen Fix ohnehin
   eingetaktet ist).
3. **MOSAIC_\*-Knopf-Registratur** (`knoepfe.rs`: Name/Default/Status/
   Prereg-Verweis; Doku und Paritaetsprobe generieren daraus) (mittel).
4. **Gemeinsame Partieschleife** statt sechs Kopien (`run_self_play`/
   `with_net_labels`/`net_self_play`/`arena_match`/`net_arena_match`/
   `net_vs_net`) -- Wurzel beider Verdrahtungsfehler dieser Woche (gross).
5. **Spieler-Abstraktion** (Drafting-Entscheidung -> Kuppelwahl -> Tiling
   als komponierbare Schicht statt Hakenketten) (gross).

**Wichtig**: Punkte 4 und 5 werden NICHT vorsorglich gebaut, sondern als
TRAGENDE STRUKTUR des naechsten grossen Bauschritts -- der parametrisierten
Wertungsplatten-Heuristiken (Zwei-Pole-Architektur, Abschnitt oben) -- gleich
mitgezogen.

**Zusaetzlicher offener Punkt: Vorregistrierung Async-Suchumbau.**
Nutzer-Begruendung: Self-Play-Durchsatz IST der Engpass. Stufenplan mit
Entscheidungsgleichheits-Gate und Regel-3-Gate (>= 2,0x gegen 225,6 Spiele/h);
Arena-Boost nur fuer Messlaeufe, Gating bleibt reproduzierbar -- §18-Spannung
vermerkt, Nutzer-Veto vorbehalten.

**Die folgenden Zeilen standen schon vor dieser Entruempelung offen und sind
unveraendert:**

| Punkt                                                                   | Stand                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Formungsterm Arm A/B**                                                | Arm A = `wertung_progress` ins Netz-Blatt (Zaehler = belegte Felder). Arm B = derselbe Term, Zaehler + Ownership-Marginalen der OFFENEN Felder. Eine Zeile Unterschied; der Kontrast isoliert den Kopf-Beitrag. Kontrolle auf dem aktuellen Brett ist PFLICHT, sonst ist ein Sieg nicht interpretierbar (Task #5 hat Formung auf dem aktuellen Brett als folgenlos gemessen).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Zufallsknoten INNERHALB der Runde                                       | Kuppelstapel als aufgezaehlter Knoten am Aufdecken, Kostentor in Runde 1. Danach kann der Shuffle raus (Determinismus-Gewinn). `MOSAIC_STACK_DRAW_CHANCE`, Default aus -- gehoert ins naechste Self-Play.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Stapelzug fuers NETZ                                                    | braucht Self-Play mit den Infos; laut Nutzer-Entscheid hinter der v21-Queue. Wird jetzt ueber die Wahrscheinlichkeit geloest, nicht als eigener Task.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Bootstrap-Horizont                                                      | gegatet auf Generierungsstart, keine Batcher-Entlastung (+25 % gelten unveraendert)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Kopf-Warmstart statt Zufall** (Nutzer-Idee 2026-08-11)                | Bei neuen/verbreiterten Koepfen wirft `train.py:771` formabweichende Tensoren weg (`skipped = ...shape != ...shape`) -> sie starten ZUFAELLIG. Zwei Faelle: (a) **`opp_points_head` aus `points_head` initialisieren** -- gleiche Form, direktes Kopieren; der Kopf muss dann nur lernen, den Gegner-Teil der Repraesentation zu lesen statt den Ich-Teil, statt bei Null anzufangen. (b) **verbreiterten `ownership_head` teilweise uebernehmen** -- heute wurden ALLE 140 Zeilen neu gewuerfelt, auch die 122 mit unveraenderter Bedeutung. **ACHTUNG, Trunkierung waere FALSCH**: der Vektor ist `[72 Ownership][34 conj_p0][34 conj_p1]` (vorher `[72][25][25]`), also muessen die alten Indizes 97-121 auf **106-130** abgebildet werden, nicht auf 97-121 -- ein abgeschnittenes Kopieren verdrahtet Spieler 1 falsch und sieht dabei plausibel aus. Braucht eine Index-Abbildung. Verkettungsreihenfolge vor der Umsetzung PRUEFEN (aus `neural_net.py:1020-1023` abgeleitet, nicht gelesen). `--reinit-points-head` macht das GEGENTEIL (Task #12, fairer Kontrollarm) und ist kein Vorbild. Blockiert nichts Laufendes -- Arbeit fuer die naechste Generation. |
| **ALPHA je Kriterium -- was noch offen ist** (Nutzer: *"da werden wir noch ein wenig feintuning brauchen"*) | **RICHTIGGESTELLT 2026-08-11**: der Eintrag nannte fuenf Provisorien zu kalibrierten Zielwerten -- die sind mit `d658a23` AUSGEBAUT, drei der fuenf sind damit gegenstandslos. (1) "Endpunkte grob aufgeloest" ist durch einen haerteren Befund ersetzt: der Fit ist UNMOEGLICH, nicht ungenau -- `Mittel(x^alpha) > Rate` gilt fuer JEDES alpha, weil eine abgeschlossene Linie x=1 hat und `1^alpha = 1` bleibt. (2) Jokerfelder und Farbreihen sind inzwischen GEMESSEN (Rate 0,430 / 344 Ereignisse bzw. 0,016 / 77). (5) betraf die Endpunkte, die es nicht mehr gibt. **OFFEN bleiben zwei**: die Rundenanhebung (`MOSAIC_WERTUNG_ROUND_GAIN`, Default 0) ist LINEAR angenommen, nicht gemessen; und `P(vollstaendig | fuellstand, runde)` bleibt das Objekt, das alpha ersetzen wuerde -- laut Nutzer-Entscheid Aufgabe des OWNERSHIP-KOPFS (Schaetzer), nicht der Injektion (Lenker). Die alpha-Werte werden jetzt je Kriterium von Hand gesetzt; welche taugen, bestimmt der 20er-Versuch empirisch. Messbasis fuer den Kopf-Vergleich: `logs/kalibrierung_alle_kriterien.log`. |
| **Gepaarte Arena-Vergleiche sind schwaecher als angenommen** | `self_play.rs:1523` gibt DASSELBE `rng` an die Suche wie an den Spielzustand; `determinize_hidden_information` (`net_mcts.rs:620`) verbraucht es, `Bag::refill_from_tower` (`supply.rs:43`) ebenso. Aendert ein Knopf das Spiel, aendert sich die Zahl der Suchen -> der RNG-Strom -> die **Fliesenversorgung**. "Gleicher Spielindex, gleiche Startbedingungen" gilt nur bis zur ersten Suche. Entwertet die geschlossenen Befunde (Floor-Shaping, `w>0`, `GUMBEL_TOP_M`) nicht, gehoert aber in die Bewertung JEDES kuenftigen Sweeps. Derselbe Mechanismus macht Arena-/Self-Play-Partien **nicht replaybar** (am Code belegt: Replay bricht in Runde 4 ab, auch bei `net_sims=1`). Folge: ereignisbasierte Log-Zahlen sind brauchbar (so arbeitete die Watchlist), endbrettbasierte nicht. Fix waere ein eigener, deterministisch geseedeter Such-RNG -- Architekturaenderung ueber vier Dateien, NICHT gebaut. |
| `player_profiles.json.bak` | **AUFGEKLAERT 2026-08-13**: von MIR geloescht, mit pfadgenauer Nutzer-Freigabe ("die loeschkandidaten koennen weg"), im Commit "Aufraeumen nach Review-Freigabe". Der Housekeeping-Agent kannte den parallelen Commit nicht und hat das Fehlen korrekt als ungeklaert gemeldet -- kein Raetsel, kein Regelverstoss. |
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
