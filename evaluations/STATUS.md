# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-13, 13:10
(Generationswechsel v28 -> v29, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-13 (vor der
Neufassung zum Generationswechsel v28 -> v29)"**, die Generationsberichte v24 bis v28 ebenfalls
dort.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen.

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**Stand 2026-09-15, 00:30: zwei Messketten laufen hintereinander, sonst nichts.**

| Kette | Inhalt | Stand |
| --- | --- | --- |
| `tools/night_v29_20260914.sh` | 1. A/B Mondstapel-Nachsuche (Stufe 3) - 2./3. Kostentor K4 mit/ohne - 4./5. Arena K4 zwei Dosen - 6. Nachzug b02 gegen b03 ohne Frueh-Stopp | **Schritte 1-5 DURCH** (Verdikte unten), Schritt 6 (Nachzug b02/b03) laeuft |
| `tools/night_v29_envelope_value_ab.sh` | wartet auf die erste; dann Anker-Kante v29-b03 gegen hv4_anchor, dann Value-Anteil im Tiling in zwei Dosen (par.8.6b) | wartend, Prozessabfrage alle 5 min |

**Nichts anderes darf Rechenlast erzeugen** -- kein Build, kein cargo, keine Sonde. Das gilt
besonders fuer den Wheel-Bau: beide Ketten fahren auf dem Kontrakt `39994362fba145a6`, ein
Neubau mitten darin liesse die Arme auf zwei verschiedenen Wheels laufen.

**Die v29-Erzeugung ist seit dem 2026-09-14 durch** (1.201 Dateien, 12,8 h); die Einzelheiten
und die Nebenlast-Offenlegung stehen unten. Der Vollstaendigkeit halber der Aufbau, unter dem
der Korpus entstanden ist -- Generator `v28-b02`, drei Klassen nacheinander, alle bei
**100 Sims**, `MOSAIC_STACK_DRAW_RESEARCH=1`, Spec `models/start_by_search_on.spec.json`,
`--start-slot-random-p 0.15`:

| Klasse | Seed | Soll |
| --- | --- | --- |
| `v28-b02-policy` (Sockel, policy-aktiv) | 20260920 | 400 Dateien |
| `v28-b02-value-tempc` (Schwarm, temperiert) | 20260921 | 400 Dateien |
| `v28-b02-value-excursion` (Schwarm, Ausflug) | 20260922 | 401 Dateien |

Erwartet rund 10,8 h (Hochrechnung aus gemessenen Werten; v28 lief 9,92 h). Daneben laeuft der
Cache-Waechter unter der Trainings-Umgebung. **Nichts anderes darf Rechenlast erzeugen** --
kein Build, kein cargo, keine Sonde.

> **OFFENGELEGT (2026-09-13/14, Nacht): diese Zusage ist gebrochen worden.** Waehrend der
> Erzeugung lief Nebenlast, und zwar in beide Richtungen: der Nutzer hat drei Push-Versuche
> gefahren, deren pre-push-Hook jeweils `cargo test --release` ausloest (je rund 3 min Volllast),
> und die Sitzung hat danach auf seine Frage "warum muss ich das machen?" vier weitere
> cargo-Laeufe, zwei Sonden-Selbsttests und einen Korpuslauf ueber 228 Dateien gestartet. Dazu je
> Commit der pre-commit-Hook mit 91 Tests.
>
> **Einordnung, nicht Entwarnung:** der Self-Play laeuft mit fester Simulationszahl, nicht gegen
> eine Uhr -- die Partien sollten dadurch langsamer, aber nicht anders werden. Die Regel in
> CLAUDE.md begruendet sich an einem Fall, in dem CPU-Nebenlast Partien verstuemmelt hat; ob das
> hier greift, ist NICHT geprueft. Wer den v29-Korpus auswertet, muss das wissen. Der Nutzer
> entscheidet, ob ihm das reicht oder ob die betroffenen Klassen neu erzeugt werden.

**Danach, in dieser Reihenfolge:**

1. **Tor 0 / Tor 2a je Klasse** (`corpus_sanity_check.py`, 271 s je Klasse gemessen).
2. **Offene Kleinigkeit der Sims-Kurve:** Plattenpunkte je Kriterium fuer die drei
   Teil-A-Laeufe nachfahren (das Kettenskript rief `plate_points_from_arena.py` ohne `--out`
   auf; je unter 5 s auf vorhandenen Logs).
3. ~~**Cache-Bloecke und Monolithe aufraeumen**~~ **BLOECKE ERLEDIGT 2026-09-14** auf Freigabe
   des Nutzers: 1.842 Waisen geloescht (744 MB), alle nachgezaehlt und verschwunden. Quellen
   waren v25-b01 (1.602 Bloecke) und zwoelf Messkorpora der Sims-Kurve und der c2-Ablationen.
   Kein restic-Beleg noetig -- `tools/backup_excludes.txt` schliesst `*.h5` ausdruecklich aus
   ("jederzeit nachbaubar"). **MONOLITHEN ebenfalls ERLEDIGT** (2026-09-14, nach dem Ende von b02/b03):
   acht aus der v28-Generation geloescht (4,1 GB), vier aktuelle geschuetzt. Cache-Volumen von
   5,1 auf 2,3 GB; zusammen mit den Bloecken rund 4,9 GB frei. **Schritt 4 des
   Generationswechsels ist damit vollstaendig.**
4. **Kette v29 fahren**: `tools/night_v29_chain.sh` ist GESCHRIEBEN (2026-09-13, Syntax
   geprueft) und wartet selbst auf das Ende der Erzeugung -- Manifeste, G-2-Kennzahlen, Fenster
   (Seed 20260941), Bloecke, Monolith, Training v29-b01 mit Warmstart auf `v28-b02_brierbest`.
   Sie enthaelt Tor 0 und Tor 2a bereits als Schritt 1, Punkt 1 oben ist damit abgedeckt.
   **Starten wie die Erzeugung: in einem eigenen Fenster, nicht ueber die Sitzung.**
5. **Portable Build -- als TEST, nicht als Auslieferung** (Nutzer 2026-09-13, 22:00: "Der
   portable build ist fuer mich erst relevant mit v30. Wir koennen ihn von mir aus mit v29
   testen"). Er belegt also nur, dass der Bauweg traegt; das Ergebnis wird nicht weitergegeben.
   `python tools/build_release.py` nach
   `evaluations/review/portable_build_audit_2026-09-13.md` Abschnitt C, Spec ist auf v28-b02
   umgestellt (Commit 3c81d0b). **Nur bei freier CPU** -- nicht neben Erzeugung oder Kette.
   Das RELEASE selbst gehoert zu v30 (Schlussmodell Tessa).
6. **Zwei Bauten, die VOR ihrem jeweiligen Trainingsarm stehen** (Fahrplan Nr. 5 und Nr. 15),
   beide brauchen eine freie Maschine und ihre Tore:
   - **Wheel 2 fuer den Sicht-Arm v29-b03**: Encoder-Abschnitt 16 mit P.3, P.7, P.9 und
     P.11 bis P.15. **Der CODE ist gebaut** (2026-09-13, `PREREG_stack_top_feature.md`
     par.17/17a): Rust beide Pfade, Python-Zwilling, drei Tests, plus das additive Record-Feld
     `dome_pool_view.blocks[].designs` in `serialize.rs`. **Bau, Tests und Fixtures sind
     ABGENOMMEN** (2026-09-13: 641 Tests gruen, keine Warnungen; Vertragshash jetzt
     `39994362fba145a6`, Netz-Paritaet `3c02ed8c7c55c603`, Feature-Golden-Fixture neu
     basisgelegt). OFFEN sind nur noch **Wheel-Bau plus Installation und die Anker-Drift** --
     sie brauchen ein Fenster ohne Erzeugung.
     **`config.INPUT_SIZE` steht bewusst noch auf 755** und wird im SELBEN Zug wie die
     Wheel-Installation auf 794 gesetzt: `file_cache_key.py` liest den Wert zur Laufzeit,
     eine vorzeitige 794 haette die wartende Kette 755er-Bloecke unter dem 794er-Schluessel
     ablegen lassen (Unfall vom 2026-09-11). Merkposten steht an der Zeile in `config.py`.
     **P.12 wirkt erst ab v30** (Nutzer-Entscheid 2026-09-13, par.17): der laufende
     v29-Korpus traegt `designs` nicht, die 18 Spalten sind in b03 konstant 0.
   - **Ablations-Schalter `MOSAIC_SPECIAL_PLANES_OFF` fuer v29-b02** plus Tore
     (`PREREG_special_tile_yield.md`, Fahrplan Nr. 15).
7. Danach nach Fahrplan `evaluations/v29_program_agent_plan.md` (41 Punkte).

### Stand 2026-09-14, 14:00 -- die v29-Arme sind gemessen

**Die Erzeugung ist durch** (1.201 Dateien, 12,8 h), **Tor 2a haelt** (0,843 gegen 0,816 volle
Spalten je Seite; die Reihe ist ueber fuenf Generationen monoton), das Fenster steht mit 2.947
Dateien, und alle drei Arme sind trainiert.

| Arm | Eingang | Besonderheit | Tor 1 | Ergebnis |
| --- | --- | --- | --- | --- |
| v29-b01 | 755 | Pflichtarm, Bezugspunkt | gegen `v28-b02` | **beide Seeds H0** -- kein Champion-Wechsel |
| v29-b03 | 794 | Sichtwerte (Abschnitt 16) | gegen b01 | **Merkmalsstand UEBERNOMMEN** (Seed 1 klar 69:41, Seed 2 Gleichstand; par.12-Regel) |
| v29-b02 | 794 | plus Spezialfeld-Ablation | gegen b03 | **praezisiert 2026-09-15** (par.10a): die Kanaele wirken auf ihren POSTEN (+0,13 bis +0,22 belegte Spezialfelder in drei Seeds), aber NICHT auf die Siegquote -- der Nachzug mit 150 Paaren ohne Frueh-Stopp steht 147:153, p 0,82 |

**Champion bleibt `v28-b02_brierbest`.** Die fehlende Kante ist am 2026-09-14 gemessen worden
(Nutzer: "ich hab noch keinen champion kandidaten aus v29 gesehen"), **Ergebnis 1:1**:

| Seed | b03 : Champion | SPRT | McNemar p | Punkte b03 / Champion |
| --- | --- | --- | --- | --- |
| 20261067 | **124 : 86** | **b03 signifikant besser** | 0,0163 | 53,38 / 50,03 |
| 20261068 | 87 : 93 | H0 (Gleichstand, nicht Niederlage) | 0,7754 | 53,61 / 53,63 |
| 20261069 | **64 : 36** | **b03 signifikant besser** | 0,0125 | 57,48 / 52,10 |

**v29-b03 IST EIN CHAMPION-KANDIDAT** (drei Seeds, alle auf demselben Wheel): zwei signifikant
dafuer, einer Gleichstand, **kein Seed dagegen**. Zusammen 275:215 in 490 Partien. In beiden
Siegseeds auch das Punkteniveau klar hoeher (+3,35 / +5,38 je Partie), im neutralen Seed gleich.

**PROMOTION ANS ENDE DER GENERATIONSARBEIT VERSCHOBEN** (Nutzer 2026-09-14: "champion werd ich
erst zum schluss der generationsarbeit machen. vielleicht kommt noch was besseres"). Der Champion
bleibt bis dahin `v28-b02_brierbest`; die drei Elo-Kanten von b03 SIND eingetragen (Register und
Champion-Rolle sind zweierlei). Grund: die offenen Knopf-Familien (Nr. 28, 30-32, 33-36) koennen
einen besseren Generator hervorbringen, und eine Promotion jetzt wuerde darauf einrasten.
**Folge fuer die Planung:** die naechste Erzeugung (und damit P.12 und die Rueckgabe-Streuung im
Korpus) kommt erst NACH dem Begleitprogramm -- kein Zeitdruck bei den Knopf-Messungen. Einzelheiten `PREREG_v29_window.md` par.9.

**MESSFEHLER GEFUNDEN 2026-09-14: b03 hat auf ablatierten Validierungsdaten validiert.**
Derselbe Schluessel-Defekt, der b02s Monolithen kostete, traf auch den Val-Cache -- und den baut
`train.py` selbst, nicht das Ketten-Skript. Gemessen an den Planes-Kanaelen: in b02s Val-Cache
(der einzige 794er, den es gibt) liegen die Kanaele 77/78 auf exakt 0,0000, waehrend b03 MIT
diesen Kanaelen trainiert hat. **Die Arena-Verdikte sind nicht betroffen** (sie messen Partien),
b01 und b02 sind sauber. Zwei Aussagen von hier sind damit zurueckgenommen -- Einzelheiten in
`PREREG_v29_window.md`, Nachtrag zur Monolith-Kollision:

1. ~~b03 hatte den schlechtesten Offline-Wert der drei Arme~~ -- **NACHGEMESSEN 2026-09-14 auf
   einem sauberen Val-Cache: 0,1796741 gegen 0,1793375 bei b01.** Der Abstand schrumpft von
   0,0018 auf 0,00034, also auf die halbe Spannweite von b03s eigenen zwoelf Epochen. **b03 ist
   offline nicht schlechter**, und damit gibt es auch keinen "Widerspruch zur Offline-Metrik"
   mehr -- b03 gewinnt die Arena und liegt offline gleichauf.
2. ~~b03 erreicht sein Optimum in Epoche 2 von 12~~ -- die zwoelf Brier-Werte liegen zwischen
   0,18114 und 0,18178, Spannweite 0,00064. Das ist eine flache Reihe ohne aufloesbare Struktur;
   Epoche 2 ist ihr zufaelliger Tiefpunkt, nicht ein Sattelpunkt. Die Nachfrage war trotzdem
   richtig -- par.6d Punkt 1 GEMESSEN (2026-09-14): **17 der 39 neuen Spalten leben, 22 sind exakt 0
   -- und beide Gruppen sind die vorhergesagten** (18x P.12, dessen Korpusfeld fehlt, plus vier
   Phasen, die im Korpus nicht vorkommen). Die lebenden Spalten sind aber schwach (0,137 im Mittel
   gegen 3,009 bei den Altspalten). Die frueher hier stehende Folgerung, das erklaere das fruehe
   Optimum, faellt mit dem Optimum weg. Punkt 2 GRUEN: tote Einheiten bei allen vier Modellen
   2,60 Prozent, kein Zuwachs.

**Monolith-Kollision BEHOBEN** (2026-09-14): der Fenster-Cache-Schluessel kannte den
Ablations-Schalter nicht, b03 hat b02s Monolithen ueberschrieben (Ergebnisse unbeschaedigt, die
naechste Wiederholung waere still falsch gewesen). Fix an der Wurzel in `window_cache_key`, aber
nur bei EINGESCHALTETEM Schalter angehaengt: der Default-Schluessel ist gemessen identisch zum
Stand davor, kein Bestandscache entwertet; drei Tests im pre-commit-Hook. Der frueher vorgelegte
Nutzer-Entscheid Weg 1 gegen Weg 2 ist damit gegenstandslos -- der Einwand gegen Weg 1
("entwertet Bestand") traf auf diese Bauform nicht zu.

**Offen aus dem Betrieb:** die Schwierigkeitsleiter ist auf v30 vertagt.

**Begleitprogramm Nr. 25 DURCH (2026-09-14): kein Knopf aus dem Zugklassen-Differential.**
`tools/probes/move_class_differential.py`, 1.343 s, n = 293 Claude-Entscheide aus g01-g07.
Roh sah die Kuppelplatzierung wie der Treffer aus (53 von 53 Abweichungen, hoechste
Wurzelwert-Differenz), **normiert traegt sie nicht**: bei Median 73 legalen Kuppelzuegen weicht
auch blindes Waehlen in 96,1 Prozent der Faelle ab. Bei Steinzuegen trifft Claude den Netzzug
dagegen klar haeufiger als blind (0,708 gegen 0,903, 5,4 SE). Die Ausgangs-Spalte ist bei sieben
Partien strukturell blind, weil der Ausgang je Partie konstant ist. Einzelheiten
`PREREG_claude_play_interface.md` par.12.

**Was daraus als Frage bleibt (nicht gebaut, nicht entschieden):** die Suche rangt bei @400 nur
16 Wurzelkandidaten (`net_mcts.rs:3180-3186`) -- bei der Kuppelplatzierung also rund 22 Prozent
der Optionen, bei Steinzuegen 84 Prozent. Ob die Wurzelbreite fuer die Kuppelphase eigens
steigen sollte, ist ein Rezept-Entscheid mit Kostentor, kein Befund dieser Sonde.

### Stand der Nacht 2026-09-13/14 (Sitzung, waehrend der Erzeugung)

Vier Fahrplanpunkte sind bearbeitet worden, alle ohne Messung:

| Nr. | Punkt | Stand |
| --- | --- | --- |
| 5 | Encoder-Abschnitt 16 (Sicht-Arm v29-b03) | **Code und Tore durch**: 39 Werte, INPUT_SIZE 794, drei neue Tests, Suite 641 gruen, drei Fixtures neu gesetzt. OFFEN: Wheel-Bau plus `config.INPUT_SIZE` auf 794 im selben Zug, dann Anker-Drift |
| 15 | Ablations-Schalter `MOSAIC_SPECIAL_PLANES_OFF` | **Bau geprueft und vollstaendig** (beide Encoder, Cache-Schluessel, Registratur, `engine_config`, `knobs.md`). OFFEN: die Tore -- sie teilen sich den Wheel-Bau mit Nr. 5, weil der Schalter per Default AUS ist |
| 20 | Netz-Gesundheit | **Sonde `tools/probes/dead_unit_probe.py` gebaut**, Selbsttest ueber drei Generationen gruen. Lauf DURCH am 2026-09-14, Punkte 1 und 2 oben |
| 23 | Korpus-Verhaltens-Audit | **Werkzeug gebaut, Selbsttest gruen** (18 Handzahlen ueber sechs Claude-Partien exakt). Der Korpuslauf kommt mit v29 |
| 22 | Schwierigkeitsleiter | Bauplan in drei Punkten berichtigt, **Schritt 1b gebaut UND ABGENOMMEN** (2026-09-14 01:35, neben dem b01-Training): sechs optionale Stilfelder, 641 Tests gruen, Paritaets-Fixture unveraendert -- das vorregistrierte Tor. Nichts installiert. Auch `models/levels/beginner.spec.json` liegt (hv3 @150) |

**RUST-STAND 2026-09-15, 05:40: Tests GRUEN, Wheel NICHT gebaut.** Zwei Stuecke sind
diese Nacht dazugekommen:

* der umgebaute **Streu-Knopf der Rueckgabe** (Schwelle 3, Rundenfenster 1-4, Commit `df4b424`),
* die **Diagnose-Zeile der Mondstapel-Nachsuche** (`[moon_order] applied=N changed=M`,
  `PREREG_moon_stack_order.md` par.9g, Commit `50772fb`).

**Abgenommen ist die Testhaelfte:** `cargo test --release` mit **663 Tests gruen, 0 Fehler,
0 Warnungen**, `examples/` und `benches/` kompilieren mit (die pre-push-Falle greift also
nicht), der neue Waechter `moon_order_diagnostics_reset_on_read` laeuft durch. Dabei fielen
zwei eigene Fehler auf und wurden behoben: der Zaehler-Block stand zwischen dem
Doc-Kommentar von `moon_order_post_search` und der Funktion (Dokumentation verwaist), und ein
`///` ueber einem `thread_local!`-Makro erzeugte eine Warnung.

**OFFEN und dem Nutzer vorgelegt: Wheel-Bau plus Installation, danach Anker-Drift**
(`/mosaic-anchor-invariance`, Pflicht nach jeder Engine-Aenderung). Der Austausch der
installierten Engine ist der einzige Schritt mit Rueckfallrisiko und wurde deshalb nicht
unbeaufsichtigt gefahren. Erst danach ist die Diagnose-Serie mit `moon_order_variants=2`
moeglich, die die Zahl `changed` liefert -- und an ihr haengt, ob Fahrplan 32a gebaut wird.

Der Satz, der hier stand (2026-09-14 01:35: auch Schritt 1b ist kompiliert und abgenommen,
641 Tests gruen). Das gefaehrdet die laufende Nacht nicht: weder `tools/night_v29_chain.sh` noch
`tools/night_v29_tor1_b01.sh` bauen ein Wheel (geprueft: kein maturin, kein pip install, kein
cargo darin) -- beide fahren auf dem INSTALLIERTEN Wheel, und `config.INPUT_SIZE` steht bewusst
noch auf 755. Der erste Bau gehoert an eine freie Maschine und bringt beides zugleich: Wheel fuer
Abschnitt 16 (Nr. 5) plus die Tore von Nr. 15, und danach den ersten Kompilierlauf fuer
Schritt 1b.

**Zwei Entscheide des Nutzers sind eingearbeitet:** P.12 wirkt erst ab v30 (der v29-Korpus traegt
das neue Record-Feld nicht, `PREREG_stack_top_feature.md` par.17), und die P.11-Normierung ist von
der unbelegten 4 auf die Regel-Obergrenze 10 korrigiert (`board.rs` Z.240).

**FENSTER-PINNING nicht vergessen:** Streudateien, die waehrend der Erzeugung entstehen,
gehoeren beim Fensterbau in `MOSAIC_DATA_EXCLUDE`.

### NACHT 2026-09-14/15: die Messkette und ihre sechs Verdikte

Zwei Ketten nacheinander, rund acht Stunden, alles auf dem Kontrakt `39994362fba145a6`.
**Ergebnis in einer Tabelle, Herleitungen darunter:**

| Gegenstand | Ergebnis | Folge |
| --- | --- | --- |
| Mondstapel Stufe 3 (Nachsuche) | traegt NICHT: 197:203, p 0,84, 200 Paare ohne Stopp | Verdacht in 4 von 5 Punkten ausgeraeumt; offen nur das Budget |
| Kostentor K4 | **BESTANDEN**: +4,3 Prozent gegen Schwelle 25 | Fahrplan Nr. 30 gruen |
| Arena K4, Dosis 1,0 | **SCHADET**: 20:60, p 0,0002, -14,3 Punkte, -0,95 Spalten | Prereg ENTSCHIEDEN |
| Arena K4, Dosis 0,5 | **SCHADET**: 45:85, p 0,0005, -8,3 Punkte | Fahrplan 31/32 gegenstandslos |
| Spezialfeld-Nachzug b02/b03 | Posten JA (+0,131 Felder), Siegquote NEIN: 147:153, p 0,82 | Begruendung korrigiert, Merkmal bleibt |
| Anker-Kante v29-b03 | **128:22** (85,3 Prozent), 150 Partien ohne Stopp | zweite Aufhaengung steht; Eintrag faellig |
| Value-Anteil im Tiling, 2 Dosen | traegt NICHT: 80:80 und 81:79, p 1,000 | par.8.6 GESCHLOSSEN |

**Zwei Befunde zaehlen ueber ihre eigene Messung hinaus:**

1. **Ein Rundenscore-Term macht die Suche kurzsichtig.** K4 senkt die Strafleiste (-1,57) und
   hebt volle Zeilen, waehrend Spalten (-0,84) und Spezialfelder (-0,59) einbrechen. Das ist
   die empirische Gegenprobe zur Nutzer-Frage vom 2026-09-14 ("nein er optimiert nicht nur
   runden score hoff ich mal") -- er tut es, sobald er genug Gewicht bekommt. Und es ist ein
   Argument FUER Variante B (Fahrplan 33): der Punkte-Weg ist abgeraeumt, der Geometrie-Weg
   nicht.
2. **Zwei Belege dieser Kampagne standen auf zu kleinen Stichproben.** Der Spezialfeld-Beleg
   (p = 0,0386 aus 30 Paaren mit Frueh-Stopp) loest sich bei 150 Paaren auf; K4s Dosiswahl
   stand auf einer Analogie, die eine fehlende Daempfung uebersah. Beide Male hat erst die
   groessere Stichprobe geklaert.

**Offene Nutzer-Entscheide aus dieser Nacht:** (a) K4 ein Rundenprofil geben oder den Term
ruhen lassen, (b) den kontaminierten Kostentor-Lauf wiederholen (8,5 min, das Verdikt braucht
es nicht), (c) nach dem Wheel-Bau: wird Fahrplan 32a ueberhaupt gebaut (haengt an der
Diagnose-Zahl `changed`).

#### Stufe 3 des Mondstapels traegt nicht

**197:203 auf 200 Paaren ohne Frueh-Stopp** (McNemar p 0,84, gepaarte Differenz -0,030
[-0,229, +0,169], 5.933 s bei 10 Threads, 14,833 s je Partie). Keine der sechs
Standard-Kennzahlen liegt ueber der Aufloesung. Artefakt
`moon_order_post_vs_off_s20261091.json`, Einzelheiten `PREREG_moon_stack_order.md` par.9h.

**Das Verdikt lautet nicht "die Reihenfolge ist egal"** -- die Gegenhypothese ist seit par.7
widerlegt (nur der oberste Stein je Stapel ist ziehbar) --, sondern: **die Nachsuche in dieser
Bauform und mit diesem Budget traegt nicht.** par.9d hatte vorab festgelegt, dass ein
Nullbefund hier ein Implementierungs-Verdacht ist; **vier der fuenf Pruefpunkte sind
ausgeraeumt** (Perspektive, Verdrahtung bis in den Arena-Pfad, Vollstaendigkeit der Varianten,
und die Ausloesung per Deckungsgleichheit: das Tor prueft exakt die Bedingung, die par.9b mit
12,20 je Partie gezaehlt wird -- par.9i, im Code; die frueheren 24,34 aus den Logs waren eine Ueberzaehlung, weil die Log-Zeile ein ZUSTAND ist und kein Ereignis). Offen bleibt allein das **Budget** (256 Sims je Variante =
Wurzelbreite 16).

**Die eigentlich offene Frage hat par.9d gar nicht gestellt:** nicht wie oft die Nachsuche
laeuft, sondern **wie oft sie ANDERS waehlt**. Dafuer ist die Diagnose-Zeile `[moon_order]`
gebaut (par.9g), sie liegt noch nicht im Wheel.

**Randbefund als Reihenfolge-Argument, nicht als Beleg:** die groesste Einzelabweichung sind
die vollen Spalten mit -0,0985 (rund 1,8 SE), also die langfristigste Groesse im Block,
waehrend die kurzfristigen Plattenpunkte leicht fuer die Nachsuche sprechen. Dieselbe Richtung,
die par.9e dem Prior vorwirft. Das stuetzt die Reihenfolge C vor B vor A (Fahrplan 32a/32b).

**Faellig vor Fahrplan 32a:** Wheel bauen, kleine Serie mit `moon_order_variants=2`, die beiden
Zahlen ablesen. Bleibt `changed` nahe 0, waehlt die Nachsuche fast immer den Bestand -- dann
ist nicht der Horizont der Engpass und 32a faellt, bevor es gebaut wird.

#### Kostentor K4 bestanden, Fahrplan Nr. 30 gruen

**+4,3 Prozent Wanduhr** (12,812 gegen 12,286 s je Partie) und +3,4 Prozent CPU gegen eine
Schwelle von 25 Prozent -- der Rundenschaetzer kostet ein Sechstel des Erlaubten. Artefakte
`k4_kosten_mit_s20261092.json` / `k4_kosten_ohne_s20261093.json`, Einzelheiten
`PREREG_round_estimate_leaf_term.md` par.7b. Die Schritte 31 und 32 duerfen laufen.

**OFFENGELEGT (par.7a): waehrend des `mit`-Laufs lief Nebenlast aus dieser Sitzung** -- drei
git-Commits, deren pre-commit-Hook je 98 Tests faehrt, in einem Lauf, dessen einzige Messgroesse
die Wanduhr ist. Groessenordnung 0,18 bis 0,59 Prozent des Kern-Fensters bei 43,7 Prozent
Auslastung. **Die Stoerung wirkt konservativ** (sie verteuerte die mit-Seite), +4,3 Prozent ist
also eine Obergrenze und das Verdikt haelt. Eine saubere Wiederholung kostet 8,5 min und ist
ein Nutzer-Entscheid. **Regel ab sofort in dieser Sitzung: kein Commit, solange eine Messkette
laeuft.**

**Nebenbefund, NICHT gedeutet:** zwischen den beiden Kostentor-Laeufen unterscheiden sich
Punkte (46,33 gegen 51,27) und volle Spalten (0,55 gegen 0,93) deutlich. Verschiedene Seeds bei
n = 40 -- in dieser Kampagne bewegt der Seed die Metrik 4- bis 6-mal staerker als jeder Knopf.
Die gepaarten Arena-Laeufe der Schritte 4 und 5 entscheiden das.

**Und die offene Frage aus par.9h ist beantwortet:** `k4_kosten_ohne` liefert den fehlenden
Basiswert ohne Nachsuche. Der Stufe-3-Lauf liegt mit 14,833 s je Partie **+20,7 Prozent**
darueber, obwohl nur eine der beiden Seiten die Nachsuche traegt (hochgerechnet rund +41
Prozent beidseitig, Herleitung). **Die Nachsuche hat also wirklich gerechnet** -- ihre
Wirkungslosigkeit liegt nicht daran, dass sie nie lief.

#### K4 mit voller Dosis SCHADET -- und die Ursache ist gefunden

**20:60 Siege, McNemar p = 0,00018, -14,3 Punkte und -0,95 volle Spalten je Partie**
(`k4_c10_vs_off_s20261094`, 40 Paare, gepaart, ein Spec-Feld Unterschied). Kein Nullbefund,
sondern ein Einbruch. Einzelheiten `PREREG_round_estimate_leaf_term.md` par.7c.

**Der Nebenbefund aus par.7b war damit echt und kein Seed-Effekt** -- die Vorsicht beim Lesen
war richtig, die Beobachtung auch.

**Ursache am Code belegt, und sie ist eine Dosis-Frage:** `today_value` ist eine
Siegwahrscheinlichkeit in [0,1] (Klammerung net_mcts.rs:3205-3206), der Term addiert
`C_est * tanh(..)`, bei C_est 1,0 also bis zu +-1,0 -- er kann den Value-Kopf ganz ersetzen.
Und `B` ist per Konstruktion das P90 der Differenz je Runde, also saettigt der tanh in rund
10 Prozent der Blaetter, **in jeder Runde gleich oft**. Die Dosis war mit "Betrag wie K3"
begruendet; die Analogie stimmt strukturell (gleiche Stelle, gleicher Wertebereich, K3 faehrt
c = 1,0 ohne Schaden), uebersieht aber die zweite Daempfung, die nur K3 hat: sein Shift traegt
das abfallende Rundenprofil in sich. **K4 hat keines.**

**Dosis 0,5 bestaetigt es** (par.7d): 45:85, p = 0,00054, -8,26 Punkte. Der PUNKTE-Schaden
halbiert sich grob mit der Dosis (Faktor 0,58), **der SPALTEN-Schaden nicht: davon bleiben 88
Prozent** (-0,837 gegen -0,949). Die Stoerung des Spaltenbaus saettigt also tief.

**Der Mechanismus ist damit sichtbar, und es ist der befuerchtete:** bei Dosis 0,5 sinkt die
Strafleiste um 1,57 Punkte und volle Zeilen steigen (+0,11), waehrend Spalten (-0,84) und
Spezialfelder (-0,59) einbrechen. `round_estimate_points` ist Solver-Rundenscore plus
Strafleisten-Busse -- der Term liefert genau, worauf er zeigt, und verliert alles, was ueber die
Runde hinausreicht. Das ist die empirische Gegenprobe zur Nutzer-Frage vom 2026-09-14 ("nein er
optimiert nicht nur runden score hoff ich mal"): er tut es, sobald er genug Gewicht bekommt.

**Fahrplan Nr. 31 und 32 sind damit gegenstandslos** (im Plan durchgestrichen und begruendet).
**Offen als VORSCHLAG, Nutzer-Entscheid:** K4 ein abfallendes Rundenprofil wie K3 geben (rund
1 h Bau). Das ist der naeherliegende Weg als eine kleinere Dosis -- wenn der Spaltenschaden bei
halber Dosis zu 88 Prozent bleibt, ist er bei einem Zehntel nicht automatisch weg.

**Und eine Luecke in der Prereg:** ihr Falsifikator kennt nur "traegt" und "traegt nicht". Ein
SCHADEN ist ein dritter Ausgang, den par.5 und par.10 nicht vorgesehen haben.

#### der Spezialfeld-Nachzug korrigiert seine eigene Begruendung

Der Lauf, den ich als duennste Kante der Generation angesetzt hatte, hat geliefert -- gegen das
bestehende Verdikt. `paired_gating_v29-b02_vs_v29-b03_s20261096.json`, **150 Paare ohne
Frueh-Stopp: 147:153**, McNemar p = 0,822, gepaarte Differenz -0,040 [-0,273, +0,193].

**Die Effektstaerke derselben Kante faellt monoton mit der Stichprobe:** -0,533 (30 Paare,
Frueh-Stopp, p = 0,0386) -> -0,280 (50 Paare) -> **-0,040 (150 Paare)**. Der einzige
signifikante Lauf war zugleich der kleinste und der einzige mit SPRT-Stopp. **Auf der
Siegquote traegt das Verdikt nicht.**

**Der Posten dagegen bewegt sich, und zwar konsistent:** belegte Spezialfelder +0,170 / +0,224 /
**+0,131** in den drei Seeds -- der groesste Lauf (n = 298 Bretter je Seite) liegt mitten im Feld
statt einzubrechen. Dazu +0,087 volle Spalten und +0,58 Punkte je Partie fuer b03.

**Kein Widerspruch, sondern Groessenordnung:** +0,58 Punkte gegen eine Punkte-SD von rund 17
loesen 150 Paare nicht auf. **Folge fuer die Entscheidung: keine** -- die Kanaele bleiben drin
(gebaut, kostenlos, wirken auf ihren Posten, schaden nicht). Was faellt, ist die Begruendung
"die Ablation verliert signifikant". Einzelheiten `PREREG_special_tile_yield.md` par.10a.

**Die Lehre darueber hinaus:** ein Verdikt auf 30 Paaren mit Frueh-Stopp haette hier fast einen
Merkmalssatz mit einer Zahl gerechtfertigt, die sich bei 5-facher Stichprobe aufloest. Der
Nachzug kostete 65 min.

#### Anker-Kante fuer v29-b03: 128:22, eingetragen

`anchor_edge_v29-b03_vs_hv4_anchor.json`: **128:22 in 150 Partien** (85,3 Prozent), kein
Frueh-Stopp, 1.292,8 s / 8,62 s je Partie. Aufbau wie bei der letzten Anker-Kante des
Champions: b03 @400 c_puct 1,5 mit Champion-Spec gegen das Anker-Artefakt @150 c_puct 0,3,
6 Worker. Handshake bewusst Cross-Aera (Artefakt 39648b95bbba1acf gegen Live
39994362fba145a6, `project_anchor_era_rule`), **Golden-Selbsttest ohne Abweichung**.

**Einordnung:** die bisherige Vergleichskante `v22-b05@400 gegen hv4@150` steht bei 76 Prozent
(38:12), und die war mit Frueh-Stopp, also nach oben verzerrt. b03 liegt mit 85,3 Prozent ueber
150 Partien ohne Stopp deutlich darueber. Damit haengt v29-b03 erstmals an zwei VERSCHIEDENEN
Gegnern statt nur am Champion -- die Promotions-Checkliste verlangt drei Aufhaengungen
(Gating, Anker, Champion-2).

**EINGETRAGEN 2026-09-15, 05:1x** (nach dem Ende der Ketten). Der Befehl war:

```
python tools/elo_tracker.py add --player-a v29-b03 --sims-a 400   --player-b Heuristik_hv4_anchor --sims-b 150   --wins-a 128 --wins-b 22 --n 150   --comment "Segment 2: v29-b03 @400 c_puct 1,5 (Champion-Spec) gegen Anker-Artefakt hv4_anchor @150 c_puct 0,3, frozen_referee_match 6 Worker, Seed-Basis 20261097, 150 Partien OHNE Frueh-Stopp (85,3 Prozent), Golden-Selbsttest gruen, Cross-Aera (Artefakt 39648b95bbba1acf gegen Live 39994362fba145a6); 1.293 s"
```

(Parameternamen am Werkzeug geprueft: `--player-a`/`--player-b` und `--n`.)

**Ergebnis im Register: `v29-b03@400` steht bei Elo 1402 [1353, 1456] aus 640 Partien** und
damit ERSTMALS ueber dem amtierenden Champion `v28-b02@400` (1371 [1332, 1419], 2.350 Partien).

**Zwei Einschraenkungen gehoeren zu dieser Zahl:**

1. **Die Intervalle ueberlappen deutlich** (1353-1456 gegen 1332-1419). Der Abstand von 31 Elo
   ist kein Staerkebefund.
2. **Drei von b03s vier Kanten sind frueh gestoppt** (Spalte "Frueh 3/4" im Register), ihre
   Siegquoten also nach oben verzerrt und nicht korrigiert. Die Anker-Kante von heute Nacht
   ist **die erste unverzerrte** -- 150 Partien bis zum Deckel. Der Champion hat 6 von 13
   gestoppten Kanten bei vierfacher Partienzahl.

Der Champion bleibt `v28-b02_brierbest`; die Promotion steht per Nutzer-Entscheid am Ende der
Generationsarbeit.

Kommentar mit Cross-Aera-Vermerk und Golden-Selbsttest. Die naive Ein-Kanten-Rechnung ergaebe
rund +306 Elo ueber dem auf 1000 fixierten Anker; der Registerwert kommt aus dem
Block-Bootstrap ueber alle Kanten und kann davon abweichen.

#### Value-Anteil im Tiling: zweiter Nullbefund, par.8.6 geschlossen

Der Lauf, der auf meiner Falschauskunft "ungemessen" beruhte und den der Nutzer nach der
Richtigstellung bestaetigt hat ("bleiben drin. die maschine braucht eh was zum laufen"):
**80:80 bei Dosis 0,5 und 81:79 bei Dosis 1,0**, McNemar p = 1,000 in beiden, je 80 Paare bis
zum Deckel. Keine der sechs Kennzahlen ueber der Aufloesung, und die vollen Spalten haben in
den beiden Dosen ENTGEGENGESETZTE Vorzeichen (+0,050 und -0,063) -- Rauschen, keine mit der
Dosis wachsende Wirkung. Einzelheiten `PREREG_geometric_envelope.md` par.8.6b/8.6c.

**Damit ist der Term geschlossen**, an zwei Netzen und zwei Basislinien gemessen (2026-09-04 am
v23-b01 gegen die damalige Spec, 2026-09-15 am v28-b02 gegen die Champion-Spec).

**Die Kosten belegen die alte Begruendung:** der Term ruft je Tiling-Kandidat das Netz, kostet
aber nur +2,1 und +3,6 Prozent Wanduhr, und die Seiten spielen fast identisch (5-6 Sweeps gegen
rund 70 Splits). Im Tiling gibt es kaum Kandidaten mit echter Wahl -- der Entscheid liegt im
Draft, wie par.8.6a 2026-09-04 schon sagte.

**Nicht verwechseln mit dem offenen Vorschlag bei K4:** dort FEHLT ein Rundenprofil und der Term
wirkt zu stark; hier ist der Term zu schwach, um ueberhaupt messbar zu sein.

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v28-b02_brierbest`** (Promotion 2026-09-12),
**Elo 1371 [1332, 1419]** aus 2.350 Partien im LEITERSEGMENT 2 (44 Kanten, Anker `hv4_anchor`
fix 1000, Block-Bootstrap). Generator der v29-Erzeugung ist dasselbe Netz.

**NEU 2026-09-15: `v29-b03@400` fuehrt die Tabelle mit Elo 1402 [1353, 1456]** (640 Partien),
seit die Anker-Kante 128:22 eingetragen ist. Das ist KEIN Staerkebefund gegenueber dem
Champion: die Intervalle ueberlappen (1353-1456 gegen 1332-1419), und drei von b03s vier
Kanten sind frueh gestoppt und damit nach oben verzerrt -- die Anker-Kante ist seine erste
unverzerrte. Champion-Wechsel bleibt der Nutzer-Entscheid am Ende der Generationsarbeit.

Der Wert stieg am 2026-09-13 von 1353 auf 1394, weil drei neue Sims-Knoten unter dem
400er-Knoten einhaengen -- **kein neuer Staerkebefund**, sondern eine Folge der dichteren
Vernetzung. Neue Knoten: `v28-b02@100` 1298, `@200` 1289, `@600` 1389. Die Treppe
Anker -> hv4@600 -> v22@25 -> v22@100 -> v22@400 traegt.

**Eingefrorene Artefakte (nach dem Aufraeumen):** `frozen_champions/v28-b02` (amtierend,
Generator) und `v27-b01` (Vorgaenger, Champion-2-Kante); `frozen_heuristics/hv4_anchor`
(aktiver Anker), `hv2_generator` und `hv3_generator` (Sprossen, hv3 ist die Anfaenger-Stufe);
`models/restored_v22` (traegt den Leiterknoten v22-b05).

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `docs/measured_runtimes.md`)

| Aufbau | Dauer |
| --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11 (v27 / v28) | 10,25 h / 9,92 h |
| Argmax-Self-Play 200 Partien, threads 11, @100 / @400 / @600 | 791 s / 1.493 s / 2.113 s |
| Gepaarte Arena 75 Paare @100 gegen @400, threads 10, mit Logs | 1.121 s (7,5 s je Partie) |
| Gepaarte Arena 100 Paare @100 gegen @25 | 601 s (3,0 s je Partie) |
| Kette Schritte 1-6 (Kennzahlen, Manifeste, Fenster, Monolith) | rund 31 min |
| Training 12 Epochen, Fenster 2.947 Dateien | 5.117 s = 1,4 h |
| Gepaartes Gating 200 Paare @400, 10 Threads, mit `--log-games` | 86-91 min |
| Anker-Kante n=150 / Champion-2-Kante n=150 | rund 22 min / 43 min |
| Voller Build: Lib-Tests, no-run, Wheel, Install, Anker | rund 6 min |
| Anker-Drift / Konservierung | 15 s / 15 s |
| Tagesschnappschuss restic plus check | 6 s |

## 4. SPEC UND REZEPT

Champion-Spec `models/frozen_champions/v28-b02/spec.json`: `envelope_projection_mode` 1,
`envelope_search_c` 1,0, `envelope_flush_w` 0,0, `envelope_hull_form` 2, `special_row6_w` 1,0,
`score_utility_b` 20,0, Profil 1/0,92/0,67/0,33/0, `heuristik_variante` hv1.

**Die v29-Erzeugung faehrt `models/start_by_search_on.spec.json`** -- Feld fuer Feld dieselbe
Spec PLUS `start_by_search: 1` (verglichen 2026-09-13). Dazu in der Umgebung
`MOSAIC_STACK_DRAW_RESEARCH=1` und als Flag `--start-slot-random-p 0.15`.

**Engine seit Wheel 1 (2026-09-13):** P.10-Suchfix (die Wurzel-Determinisierung haelt den
oeffentlichen Typ der obersten Stapelplatte fest), Record-Feld `tiled_max_row` (P.14, wird auch
gelesen), Stapelzug-Knoepfe im Lauf-Manifest. Vertragshash `39648b95bbba1acf` unveraendert,
`input_size` 755. Netz-Paritaets-Fixture bewusst neu: `4750ffc6ec094a83`.

## 5. PREREG-BESTAND (9 OFFEN laut Index 2026-09-15, Ziel rund 7)

`python tools/generate_prereg_index.py` haelt `evaluations/PREREG_INDEX.md` aktuell; Stand
119 Dateien = **9 OFFEN** + 98 ENTSCHIEDEN + 12 UEBERHOLT. Die neun offenen sind alle aktiv
eingetaktet, keine ist liegengeblieben:

| Prereg | Was noch aussteht |
| --- | --- |
| `v29_window` | der laufende Zyklus selbst |
| `stack_top_feature` | Sicht-Arm v29-b03 (Wheel 2, INPUT_SIZE 794), dazu die zwei Regelbefunde par.16/16a |
| `special_tile_yield` | Ablations-Schalter und Arm v29-b02 |
| `difficulty_levels` | Bau waehrend der Erzeugung, Kanten nach Tor 1 |
| `claude_play_interface` | Partien g08-g10, Zugklassen-Differential |
| `corpus_behaviour_audit` | Werkzeug ungebaut, Korpuslauf danach |
| `moon_stack_order` | Knopf bauen, A/B am Champion |
| `dome_return_order` | A/B Modus 1 gegen 0 ueber den Referee |
| ~~`round_estimate_leaf_term`~~ | **ENTSCHIEDEN 2026-09-15**: Kostentor bestanden (+4,3 Prozent), aber beide Dosen schaden hochsignifikant (par.7c/7d). Fahrplan 31/32 gegenstandslos. Offen nur noch als VORSCHLAG: Rundenprofil wie K3 |
| `round_transition_search_sampling` | Variante B bauen (rund ein Tag), Sichttor, Kostentor, A/B |
| `code_cleanup_closeout` | Stufen 2 und 3, nach der v30-Promotion |

Die Zahl liegt ueber dem Ziel, weil das v29-Begleitprogramm bewusst breit ist. Seit dem
2026-09-13 sind zwei gefallen: `dome_return_order` und `round_estimate_leaf_term` (beide
2026-09-15). `moon_stack_order` hat zwei von drei Stufen gemessen (par.7, par.9h), bleibt aber
offen, solange die Architektur-Hebel 32a/32b nicht entschieden sind. Mit
`round_transition_search_sampling` waeren es dann die angestrebten sieben.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. ~~G-2-Haelfte des v29-Fensters~~ **ENTSCHIEDEN 2026-09-13, 13:20** (Nutzer: "Nimm fuer die
   g-2 das selbe was wir auch bei v28 hatten"): die AUSFLUG-Haelfte
   `selfplay_v26-b01-value-excursion_*`, 145 Dateien seed-gezogen mit 20260941. In
   `PREREG_v29_window.md` par.2 registriert und in `tools/night_v29_chain.sh` gesetzt; die 401
   Quelldateien liegen vollstaendig im Baum.

2. **Manifest meldet Spec-Felder falsch** (geprueft 2026-09-13): `engine_config` zeigt fuer
   `envelope_search_c`, `envelope_projection_mode`, `envelope_hull_form` und `special_row6_w`
   den Env-Default statt des wirksamen Spec-Werts, weil `lib.rs` Z.801/807/812/815
   `SearchConfig::from_env()` lesen. **Kein Belegverlust** -- die Spec-Datei hat genau einen
   Commit und ist unveraendert, jedes Manifest nennt ihren Pfad in `cli_args.spec`.
   **Vorschlag: Spec-Inhalt plus sha256 additiv ins Manifest** (`selfplay_manifest.py`), damit
   der Beleg nicht an der Unveraenderlichkeit einer Datei haengt. Nicht waehrend eines Laufs
   bauen: die Chunk-Prozesse importieren frisch.

3. **Sichtluecke bei den gezogenen Stapelplatten -- zwei Kanaele, zwei Reparaturen**
   (`PREREG_stack_top_feature.md` par.16 und par.16a). Die Vorderseiten sind nach Regelauskunft
   erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste verraet sie ueber die
   designabhaengige Rotationsfilterung (`game.rs` Z.402) -- betrifft die Suche, Reparatur
   beruehrt `NUM_ACTIONS`. (b) `serialize.rs` Z.375-379 serialisiert sie sofort, die Anzeige
   druckt sie (`claude_play.py` Z.721) und die Platzierungs-Vorschau rechnet damit (Z.597/656)
   -- betrifft den menschlichen Spieler, live eingetreten in Partie g07. Umfang und Prioritaet
   sind offen; beruehrt die Gueltigkeit von g02-g07.

4. **Cache-Bloecke und Monolithe** (knapp 7 GB): Waisen-Inventar nach der Erzeugung, Liste
   dann zur Freigabe.

5. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
   Loeschung; am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

6. ~~Textverweise auf `hv1_anchor` nachziehen~~ **ERLEDIGT 2026-09-13, 13:35** fuer die
   Stellen, die aktiv fehlleiteten: CLAUDE.md (Anker-Invarianz nennt jetzt `hv4_anchor` als
   Fixpunkt seit der Neuverankerung), `docs/working_rules.md`, `docs/architecture_reference.md`,
   `docs/generation_naming.md`. **Offen und ein echter Befund:** drei Sonden greifen direkt auf
   das geloeschte Artefakt zu und laufen nicht mehr --
   `tools/probes/anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
   `frozen_worker_protocol_probe.py`. Sie tragen jetzt einen Hinweis statt eines kryptischen
   Abbruchs. Eine Umstellung auf `hv4_anchor` braucht NEUE Erwartungswerte (die hartkodierten
   gelten fuer hv1, z. B. `scores [27, 15], steps 159`), also einen Lauf -- Nutzer-Entscheid, ob
   das lohnt oder ob die drei als historisch entfallen. Verweise, die bewusst die VERGANGENHEIT
   beschreiben (`docs/promotion_checklist.md` Z.34, die Historien-Kommentare in
   `tools/elo_tracker.py`, das Beispiel in `tools/freeze_heuristic.py`), bleiben unveraendert.

7. **Skala des Rundenschaetzers** (`round_estimate_leaf_term`): Vorschlag (a) je Runde,
   (b) 9,25 auf Zuruf. Aus dem v28-Programm uebernommen, unveraendert offen.

8. **Rahmen (ENTSCHIEDEN 2026-09-12, hier als Erinnerung):** v30 wird released und ist der
   Projektabschluss, Schlussmodell heisst **Tessa**. v29 traegt das Begleitprogramm, v30 nur
   noch Rezept-Knoepfe.

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Stand 2026-09-13, 13:10: **30 Commits vor origin/main**, der
  Nutzer pusht selbst.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein
  Build zaehlt als Last.
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch.
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, kein
  Geviertstrich in Dateien, Bezeichner englisch.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **Replayer-Grenze Chip-Vollendung:** einzelne Partien nicht nachspielbar ("Reihe N nicht mit
  Chips komplettierbar" nach 60 Versuchen); bekannte Grenze.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe** (geprueft 2026-09-13,
  `PREREG_difficulty_levels.md` par.11). Beide enden in `select_final_root_child`, beide ohne
  Wurzelrauschen, beide mit Runde-5-Kurzschluss, und `server.py` schreibt die Champion-Spec
  beim Start in die Umgebung, weil der GUI-Pfad sie von dort liest. **Die GUI spielt heute
  immer bei 400 Sims**, weil die Presets aus ihr nicht erreichbar sind (par.2 dort: alle 33
  Mensch-Partien liefen @400) -- also genau die Einstellung, bei der die Arena misst.
  Zwei Irrtuemer von mir stehen dort korrigiert: die `or 100`/`or 300`-Ausdruecke sind tote
  Fallbacks, und die Presets im Code (60/60/150/400) sind NICHT der registrierte Zuschnitt der
  Stufenleiter (Anfaenger hv3@150, darueber Champion mit Stilmitteln, Meister wie die Arena).
  Beide Male kam die Korrektur vom Nutzer.
  **Latente Sollbruchstelle:** die Arena zieht `builder_drafting_preference` der Suche vor, der
  Serverpfad kennt den Vorzug nicht; folgenlos nur, solange
  `MOSAIC_SPALTENBAU`/`MOSAIC_PLATTENBAU` unbesetzt bleiben.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf,
  der in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt; bei Modus 2 oder 4 waeren sie exakt der
  Stack-Draw-Fall.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, und zwar
  allein ueber die VOLLENDUNG -- die Teilspalten bleiben gleich
  (`PREREG_search_depth_column_optimum.md` par.8e).
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
