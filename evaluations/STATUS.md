# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Alles Entschiedene und
jede ausfuehrliche Herleitung liegt in `../archive/history.md`; der
vollstaendige Stand vor dieser Neufassung steht dort im Kapitel
"Vollstaendiger STATUS-Stand vom 2026-08-25".

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

Neu gefasst am **2026-08-25** (Nutzer-Auftrag: STATUS war mit 1180 Zeilen
schwer lesbar geworden).

---

## DAS ZIEL (Leitstern)

Ein **staerkerer Spieler**, gemessen am direkten Duell. Der benannte Hebel ist
der **Plattenblick**: rund 10 Punkte je Partie bleiben liegen. Bei jeder
Priorisierung gilt die Frage -- was traegt das dazu bei?

## FOKUS-REGEL: NUR k1 (Nutzer-Entscheid 2026-08-18)

Gemessen wird auf **Kriterium 1** (vertikale Reihen, 7 Punkte je Spalte).
Andere Kriterien nur, wenn ein Zuschnitt sie ausdruecklich braucht -- dann mit
Begruendung.

---

## STAND JETZT (2026-08-25)

**Champion:** `v21_2d_brierbest`, Elo **1215** [1170, 1259] auf der
R5-Fix-Leiter. Kanten ueber die Fix-Grenze nie mischen.

**Es laeuft nichts.** Maschine frei. Die Parallelsitzung (`mosaic-ai-97`) hat
ihren Strang uebergeben und ist beendet.

**Wheel-Stand:** neu gebaut und installiert am 2026-08-25 nach der
Feature-Erweiterung; Paritaets-Hash `8c6684ffba06cf3e...` unveraendert, Suite
525/0.

### Heute fertig geworden

| Strang | Ergebnis | wo es steht |
| --- | --- | --- |
| **Erreichbarkeits-Eingaben fuers Netz** | GEBAUT und ABGENOMMEN. `INPUT_SIZE` 708 auf 714, `NUM_PLANES_CHANNELS` 76 auf 77; Champion rechnet bitgleich weiter | Commit `29fb1f1`, Abschnitt "Architektur" |
| **Artefakt-Umzug** | 176 JSON nach `evaluations/artifacts/`, 145 Code- und 158 Dokument-Verweise nachgezogen; danach auf Nutzer-Entscheid **aus dem Tracking genommen** | Commits `4e967e1`, `4a43b8d` |
| **Blindzieh-Regel: Urteil** | Die gebaute Stopp-Regel zieht ZU OFT -- rund 10 verschenkte Punkte je betroffenem Stapelzug | `PREREG_stack_draw_reservation_rule.md` par.5b |
| **Strafleisten-Aversion: Nachmessung** | Der registrierte Nullwert war eine Eigenschaft der RUNDE 1, nicht des Champions | `PREREG_floor_action_aversion.md` par.14 |
| **Heuristik v2 / Prio-Huelle** | Lehrer-Test positiv: Siegquote 0,373 gegen 0,256 und 0,128, volle Spalten 0,798 gegen 0,086, dabei weniger Strafpunkte | `PREREG_heuristic_v2_long_rows.md` par.10, par.18 |

---

## TRAEGER-MANIFESTE: archiviert, und das ist in Ordnung (2026-08-25)

`data/` enthaelt kein `policy_carrier_manifest_*.json` mehr. **Nutzer:
bewusst archiviert.** Mein erster Vermerk stellte das als Verlust dar -- das
war halb falsch und ist hiermit berichtigt:

* Die archivierten Manifeste listen **v18/v20/v21-Dateien**. Fuer v23 werden
  sie nicht gebraucht; dessen Fenster maskiert **hv2**-Dateien.
* Auf die Laeufe dieser Nacht wirkt das Fehlen nicht: fuer den homogenen
  hv2-Korpus ist "jede Datei traegt Policy" die richtige Semantik.

**Was fehlt, ist der ERZEUGER -- aber nicht seine Regel.** Im Baum LESEN
`neural_net.py:1284` und `train_manifest.py` das Traeger-Manifest; geschrieben
wird es nirgends. Das aufgeloeste `carrier_report.py` (bb23ecd, spaeter in
`train_manifest.py` eingegliedert) war ebenfalls nur ein BERICHT, ohne eine
einzige schreibende Stelle.

**BERICHTIGUNG einer eigenen Fehlannahme (2026-08-25):** daraus hatte ich
geschlossen, das Manifest sei von Hand entstanden. Falsch -- die
v20-Kampagnen-Prereg dokumentiert *"Seed 20260806, zeitlich gestreute
Auswahl"*, und die Datei traegt ihre Herkunft im Kopf (`"seed"`, `"design"`).
Es wurde ERZEUGT, das Skript wurde nur nie committet.

**Damit ist die Aufgabe klein:** aus Seed plus dokumentierter Regel ("zeitlich
gestreute Auswahl") laesst sich der Erzeuger rekonstruieren, statt ihn neu zu
erfinden. Fuer v23 waeren es rund 180 von 1.745 hv2-Dateien.

**Vor der v23-Kampagne zu klaeren**, nicht dringend. Ohne das Werkzeug ist der
registrierte Zuschnitt nicht ausfuehrbar, und "jede Datei traegt Policy" waere
still ein anderer Zuschnitt als der beschlossene.

## NACHTLAUF 2026-08-25/26 -- was fertig ist

**1. Der v22-Korpus steht.** 24.000 Partien, 17:27 bis 01:52, **8,43 h** bei
47,5 Partien/min. Laufzeit REKONSTRUIERT aus Manifest-Start und der mtime der
letzten Datei (der Lauf begann vor dem `laufzeit`-Einbau) und im Manifest
`data/manifest_hv2_20260825_172710.json` nachgetragen.

**2. Sanity-Check ueber alle 24.020 Partien** (die 20 aus
`probe_v2huelle_horizon.pkl` zaehlen mit -- fuer ein Training auszuschliessen):

| Kennzahl | voller Korpus | Pilot (200) | Lehrer-Test |
| --- | --- | --- | --- |
| volle Spalten | **0,732 ± 0,007** | 0,741 | 0,798 |
| k1-Punkte / Anteil | +5,29 / 53,1 % | 5,67 / 55,7 % | – |
| Strafleistensteine | 5,15 | 5,09 | – |
| Eigene Punkte | 46,06 | 47,05 | – |
| k6 Spezialfelder | −9,90 | −9,77 | – |

Der Korpus haelt, was der Pilot versprach, jetzt mit engen Intervallen.

**3. Cache-Bau parallelisiert** (`PREREG_cache_build_time.md` par.7/par.8):
voller Korpus in **36,1 min** statt 2,58 h seriell, Faktor ~4,3.
Bit-Identitaet auf 120 Dateien belegt; fuer den vollen Korpus NICHT gefahren
(braeuchte 2,58 h serielle Referenz). Der fertige Cache liegt als
`data/.par_full.h5`, 0,83 GB, 4.186.112 Zustaende.

**Naechste Schritte, in dieser Reihenfolge:**

1. **Entscheiden, ob die serielle Referenz gefahren wird** (2,58 h). Noetig,
   bevor der volle Cache eine Champion-Entscheidung traegt.
2. **Das v22-Training** -- und zwar in der Konfiguration aus
   `PREREG_v22_window.md` par.4e: Arm B (`MOSAIC_IGNORE_POLICY_TARGET_VALID=1`)
   **plus `OWNERSHIP_WEIGHT > 0`**, mit w0-Kontrollarm. Beide Naechte-Arme
   liefen ohne das Gewicht und konnten deshalb strukturell keine Spalten
   bauen.
3. `data/` enthaelt 57 Block-Caches (1,2 GB) aus dem parallelen Bau plus
   `.ref_serial.h5`, `.par_test*.h5`. Aufraeumen ist ein Nutzer-Entscheid.

---

## KORPUS-DATEIEN KOMPRIMIERT (2026-08-26)

Nutzer-Frage nach doppeltem Speicherplatz durch den Cache. Die Messung dreht
sie um: **nicht der Cache war gross, sondern die pkl.**

| | vorher | jetzt |
| --- | --- | --- |
| pkl (2.401 Dateien) | **34,70 GB** | **0,98 GB** |
| Block-Caches (64) | – | 1,29 GB |
| voller Cache | – | 0,89 GB |
| Testartefakte | – | 0,16 GB |
| **`data/` gesamt** | **34,70** | **3,32 GB** |

gzip-6, **Faktor 35,4** (gemessen an 12 ordnungsfrei gezogenen Dateien,
Spanne 35,1-35,7). Umpacken 523 s, jede Datei einzeln gegen ihre
Originalbytes geprueft VOR dem Ersetzen.

**Der Dateiname bleibt `.pkl`** -- am Namen haengen Cache-Schluessel,
`MOSAIC_DATA_EXCLUDE`-Regexe und alle Globs; eine Umbenennung haette alle drei
STILL gebrochen. Erkannt wird am Inhalt (gzip-Magic), siehe `corpus_io.py`.

**Dreifach abgenommen mit dem Bit-Identitaets-Tor:** Cache aus komprimierten
Kopien, Cache aus dem umgepackten Bestand, und der parallele Bau selbst --
alle drei bit-identisch zur seriellen Referenz.

**Die pkl bleiben der Rohstand und werden NICHT durch den Cache ersetzt.** Als
`INPUT_SIZE` am 2026-08-25 von 708 auf 714 ging, war jeder bestehende Cache
unbrauchbar und nur die pkl erlaubten den Neubau. Die offenen Preregs
(Spezialfeld-Eingaben, Slot-Ziel, Huellen-Gewichtung) wuerden dasselbe wieder
ausloesen.

**Aufraeumbar, Nutzer-Entscheid:** die 64 Block-Caches (1,29 GB) sind
Nebenprodukt der Bau-Versuche mit verschiedenen Blockteilungen; nur die 42 des
vollen Laufs sind wiederverwendbar. Dazu `.ref_serial.h5`, `.par_test*.h5`,
`.gz_check.h5` (0,16 GB) aus den Abnahmen.

---

## SITZUNGSUEBERGABE 2026-08-26

**Der v22-Korpus ist FERTIG und ausgewertet, der Cache liegt gebaut bereit.**
Was jetzt ansteht, ist das Training -- und dabei eine Konfiguration, die in
beiden Naechte-Armen gefehlt hat.

### 1. Das naechste Training: Arm B PLUS Ownership-Gewicht

**Nicht "Arm B".** Beide Arme der Nacht liefen mit `OWNERSHIP_WEIGHT = 0` und
konnten deshalb STRUKTURELL keine Spalten bauen -- der Ownership-Pol ist der
einzige gebaute Kanal, der im Tiling Sofortpunkte gegen Struktur eintauschen
kann (`PREREG_v22_window.md` par.4e). Die richtige Konfiguration ist:

```
MOSAIC_IGNORE_POLICY_TARGET_VALID=1   (Traeger-Arm B, Richtungsbefund par.4b)
--ownership-weight <w0>               (par.3b der Lehrer-Prereg, w > 0)
```

plus **w0-Kontrollarm auf DEMSELBEN Korpus** -- ohne ihn sind Kopfwirkung und
Korpuswechsel konfundiert.

Beim Warmstart von einem Zwischenmodell: `MOSAIC_VAL_POOL` setzen
(`PREREG_v22_window.md` par.6), sonst ist der Val-Split zu rund 21 Prozent
vom Startmodell schon gesehen.

### 1b. ERLEDIGT 2026-08-26: Cache je Datei (Hebel 4)

`PREREG_cache_build_time.md` par.9. **Beide Pflichtpruefungen bestanden** --
21/21 Felder bit-identisch gegen die serielle Referenz, und jeder der sieben
per-Datei-Parameter erzeugt einen MISS. Die Schluesselteilung ist ADDITIV: der
Fenster-Schluessel bleibt unangetastet (kein Bestands-Cache verfaellt), der
Datei-Block bekommt einen eigenen Namensraum mit dem AUFGELOESTEN
Traegerstatus der Datei statt des Manifest-Inhalts.

Werkzeug: `tools/build_cache_incremental.py`, mit `--watch` waehrend der
Erzeugung mitlaufend. Belegter Gewinn: 119 von 120 Bloecken ueberlebten einen
Fensterwechsel (7,9 s statt Neubau).

**Nebenbefund, behoben:** `MOSAIC_CACHE_F32` stand in keiner Key-Komponente,
obwohl der Knopf den gespeicherten dtype aendert -- der Notausstieg war
wirkungslos, sobald ein Cache existierte.

**Noch nicht:** volle Korpus-Paritaet (es fehlt die serielle Referenz, 2,58 h)
und die Verdrahtung in `train.py`. Beides wie bei Hebel (1) bewusst offen.

### 1c. REPRODUKTIONSBEWEIS: der Erzeuger IST reproduzierbar (berichtigt 2026-08-26)

**Ergebnis: der heutige Build erzeugt den v22-Korpus BIT-GENAU.** 10 Partien
mit dem Rezept aus `cli_args` des Korpus-Manifests, Seed 20260826, verglichen
gegen `data/selfplay_hv2_20260825_1727_g10.pkl`: 1733 Schritte, Feld fuer Feld
gleich. `git_dirty: true` war verhaltensneutral.

**Dieser Abschnitt sagte bis zur Berichtigung das Gegenteil, und der Grund war
ein Fehler von mir, kein Befund am Code:** in keinem der ersten drei
Reproduktionslaeufe war `--heuristik-variante v2huelle` gesetzt. Der Default
ist `v1` (`self_play.py:637`). Gemessen wurde also v1 gegen einen
v2huelle-Korpus, und die Differenz (1755 gegen 1733 Schritte) wurde dem
unversionierten Anteil zugeschrieben. Der Commit `b54b41d` traegt den falschen
Stand; er bleibt in der Historie, die Berichtigung liegt obendrauf.

**Was aus dem alten Abschnitt STEHEN bleibt** -- es hing nicht an den Laeufen:

* Im Erzeugungsfenster (25.08. 17:16 bis 26.08. 01:52, 34 Commits) hat KEIN
  Commit `engine/src` angefasst.
* Das Modell ist md5-identisch zur eingefrorenen Kopie (`86bc9bddf604ea77`).
* Build auf `dbf6a08` und HEAD erzeugen Feld fuer Feld dasselbe.

**Was NICHT stehen bleibt:** "der heutige Build ist ein anderer Spieler", und
alles, was daraus ueber Neuerzeugung des Korpus folgte.

**Folge fuer das Einfrieren:** ein v2-Artefakt konserviert den ECHTEN Erzeuger,
keine Rekonstruktion. Die Frage, ob v22 auf einem Korpus ohne reproduzierbaren
Erzeuger trainiert wird, stellt sich nicht mehr.

**Nebenprodukt des Fehllaufs**, weil er sonst nur Rechenzeit waere: die
1000-Partien-Fahrt ist ein sauberer v1-gegen-v2huelle-Vergleich unter
SELF-PLAY-Bedingungen (600 Sims, mit Netz), gepaart auf Dateiebene ueber 100
Bloecke. Volle Spalten **0,737 gegen 0,050**, Punkte **46,0 gegen 20,5**,
Strafsteine **5,2 gegen 10,4**, hoechste Spalte 5,44 gegen 4,22. Artefakt:
`evaluations/artifacts/generator_drift.json` (dort als Drift etikettiert --
es ist keine, siehe oben).

### 1d. HEURISTIK-KAPSELUNG GEBAUT (2026-08-26)

`PREREG_agent_encapsulation.md` par.9. Beide Heuristiken liegen als
vollstaendige Agenten-Artefakte vor und sind VERSIONIERT:

| Artefakt | Rolle | Inhalt |
| --- | --- | --- |
| `models/frozen_heuristics/v1_anchor/` | Elo-Anker | Wheel, Spec, Manifest, Golden Probe (6,8 MB) |
| `models/frozen_heuristics/v2huelle_generator/` | v22-Erzeuger | dazu `tiling_net.onnx` als Kopie (16 MB) |

`heuristik_variante` ist jetzt ein Spec-PFLICHTfeld (Name, kein Default,
unbekannter Name = harter Fehler). Golden Probe ist ein SELF-PLAY-Lauf aus dem
eigenen Wheel, byte-verglichen -- die Welle-3-Drafting-Sonde waere fuer eine
Heuristik eine halbe Probe, weil der Referee das Tiling selbst und auf V1
aufloest (`referee.rs:312` -> `self_play.rs:1207`).

**Staerkster Beleg:** die Golden Probe des Generators ist Feld fuer Feld
identisch mit `data/selfplay_hv2_20260825_1727_g10.pkl`. Das Artefakt IST der
Erzeuger.

Werkzeuge: `tools/freeze_heuristic.py`, `tools/verify_frozen_heuristic.py`
(zwei getrennte Modi: Drift gegen aktuelles Wheel, Konservierung gegen das
Artefakt-Wheel).

**REFEREE-PFAD GESCHLOSSEN** (par.10, vier Bausteine): ein gefrorener Agent
trifft dort jetzt ALLE Entscheidungen selbst -- Startsetzung, Drafting,
Platzierung. Getrennt wurden Regel-Autoritaet (bleibt beim Referee und prueft
hart) und Entscheidungs-Autoritaet (gehoert dem Agenten). Wirkung belegt:
v1 `[27,15]` gegen v2huelle `[63,27]` aus derselben Startlage.

Sonden: `frozen_agent_referee_probe.py` (laeuft es / wirkt die Variante /
prallt Unsinn ab) und `frozen_worker_protocol_probe.py` (echter
Worker-Prozess, alle drei Anfragearten, ohne Modell).

**Noch nicht:**

* Entfernen der Quell-Konservierung -- `round5_anchor.rs` (1664 Zeilen) und
  die Varianten-Faedelung (111 Stellen, davon 103 blosse Weitergabe, 5 echte
  Verzweigungen). Der Weg ist jetzt frei, der Schritt gehoert in eigene
  Commits.
* Artefakt GEGEN Artefakt ueber `frozen_referee_match.py`: der Treiber faehrt
  "aktuelle Engine gegen EIN Artefakt", seine A-Seite verlangt ein Modell.
  Fuer zwei gefrorene Heuristiken braucht es einen netzlosen In-Process-Zweig
  oder einen zweiten Worker.

**REIHENFOLGE, die nicht vertauscht werden darf** (par.10a): `round5_anchor.rs`
schuetzt den Elo-Anker im IN-PROCESS-Pfad, und die Arenen benutzen weiter genau
den. Das Modul zu entfernen, BEVOR die Arenen den Anker aus dem Artefakt
beziehen, liesse den Anker still wandern -- genau das, wogegen es gebaut wurde.

**ANKER-TOR GRUEN** (par.10b): der Referee-Pfad spielt **20 von 20** Partien
identisch zu `net_arena_match` -- auch mit der Heuristik-Seite vollstaendig
extern. Die Umstellung verschiebt den Anker also nicht.

Zuvor war es 0 von 6, und die Ursache war EIN Schalter: die Arena traegt je
Seite `apply_via_chosen_action` (Netz `true` = Sammelaufloesung des
Stapelzugs, Heuristik `false` = nur der Peek, Slot und Rotation werden
gesucht). Der Referee kannte das nicht und gab der Heuristik das
Netz-Verhalten. Wer den Referee mit dem Arena-Pfad vergleicht, MUSS
`set_apply_modes((True, False))` setzen.

Merkposten: es gibt DREI In-Process-Pfade -- `play_arena_game` (Heuristik
gegen Heuristik), `unified_game_loop` (Netz gegen Heuristik, **hier haengt der
Anker**) und `RefereeGame`.

**Treiber traegt die Heuristik** (par.10a): aktuelle Engine gegen gefrorene
Heuristik laeuft, mit Handshake, Golden-Selbsttest in der Artefakt-venv und
externer Platzierung. Beide Artefakte tragen `protokoll.kinds` und wurden mit
dem vollstaendigen Wheel neu eingefroren; die Golden Probe des Generators ist
weiterhin Feld fuer Feld identisch mit der ersten Korpusdatei.

### 2. Offen, mit Kosten

| Punkt | Kosten | wofuer noetig |
| --- | --- | --- |
| Serielle Referenz fuer den vollen Cache | 2,58 h | bevor der Cache eine Champion-Entscheidung traegt |
| Traeger-Manifest-Generator | klein | `PREREG_v23_window.md` verlangt 1.800 von 17.450 hv2-Partien policy-aktiv; es gibt nur Leser, kein Werkzeug. Regel ist dokumentiert (Seed + zeitlich gestreute Auswahl) |
| ~~Split-Test Routing gegen Drafting~~ ERLEDIGT 2026-08-26 | 3x 22 s | `PREREG_v22_window.md` par.4f: **Drafting 0,756, Routing allein 0,000** -- par.4c hatte das Gegenteil vorhergesagt |
| Gewichtsfenster der Huelle | Messung | `PREREG_heuristic_v2_long_rows.md` par.3b.1 -- existiert ein `w`, das kleine Punktunterschiede ueberstimmt, aber nie Strafpunkte akzeptiert? |

### 3. Zustand des Baums

* **49+ Commits ungepusht** (Nutzer-Regel: Push ist ein eigener Entscheid).
* `CLAUDE.md` ist seit Sitzungsbeginn modifiziert, **nicht von dieser Sitzung**.
* `data/` enthaelt neben den 2.400 `.pkl` auch 57 Block-Caches, `.par_full.h5`,
  `.ref_serial.h5`, `.par_test*.h5` -- zusammen rund 2 GB. Aufraeumen ist ein
  Nutzer-Entscheid, ich habe nichts geloescht.
* `models/` enthaelt vier untrackte Trainings-Manifeste, darunter eines von
  einem abgebrochenen Testlauf (`valpooltest`).

### 4. Der methodische Faden dieser Sitzung

Er gehoert in die Uebergabe, weil er sich durchzieht und die naechste Sitzung
Zeit sparen kann: **aus dem Vorhandensein eines Feldes folgt nicht seine
Wirksamkeit.** Fuenfmal an einem Tag falsch geschlossen -- `tiling_net:
Some(net)` heisst nicht "das Netz steuert das Tiling", `--heuristik-variante`
in der Signatur heisst nicht, dass die Variante ankommt, "kein Schreiber im
Baum" heisst nicht "von Hand erzeugt". Jedes Mal war die Antwort ein Blick auf
Default, Reichweite und Aufrufer -- und jedes Mal hat der Nutzer sie gefunden,
nicht ich.

---

## STAPELZUG: Korpus und Netz-Self-Play loesen ihn VERSCHIEDEN auf (2026-08-26)

Beim Nachgehen der Anker-Frage (par.10b) aufgefallen, am Code geprueft:

| Pfad | `apply_via_chosen_action` | Stapelzug |
| --- | --- | --- |
| `play_heuristic_self_play_game` (self_play.rs:2255) | `false` | nur der Peek, Slot/Rotation werden **gesucht** |
| `play_net_self_play_game` (:3879/:3886) | **beide `true`** | **sammelaufgeloest**, `best_eval_for_tile` waehlt |
| `play_net_game_variante` (Arena) | Netz `true`, Heuristik `false` | gemischt |
| `play_net_vs_net_game` (Gating) | beide `true` | sammelaufgeloest |

**Der v22-Korpus entsteht also anders, als das Netz spielt.** Die
Heuristik-Self-Play-Partien loesen Stapelzuege per Suche auf, die
Netz-Self-Play-Partien per fester Heuristik.

**Was `best_eval_for_tile` (self_play.rs:444) tut:** erschoepfende Ein-Zug-
Bewertung ueber alle leeren Slots x vier Rotationen, bewertet mit
`scoring_progress + bonus_points + Anzahl Wild-Felder`. Keine Suche, kein
Gegner, keine Zukunft. `scoring_progress` ist der Elo-Anker-Term.

**Die Folge fuer die Trainingsziele** benennt der Code selbst
(`MOSAIC_STACK_DRAW_RESEARCH`-Kommentar): die Suche bewertet die Wurzelaktion
"Ziehen", ausgefuehrt wird danach eine Fortsetzung, die sie nie gesehen hat
(bis zu 20 weitere Zuege zu je -1 Punkt). Das Policy-Ziel vergleicht "Ziehen"
also gegen die anderen Wurzelzuege auf falscher Grundlage, und der
Folgezustand, aus dem Value- und Ownership-Ziele gebildet werden, stammt aus
der blinden Heuristik.

**Haeufigkeit, gemessen** (8 Partien, Netz@100 gegen Heuristik@150): **13,1
Stapelzieh-Ereignisse je Partie, 7,6 Prozent aller Schritte**. Caveat: die
Zaehlung erfasst jedes einzelne Ziehen, und eine Sammelaufloesung erzeugt
mehrere -- die Zahl der betroffenen WURZEL-Entscheidungen ist kleiner.

**ES GIBT DAFUER SCHON EINE PREREG:** `PREREG_chance_nodes.md`. Ihre
Entscheidungsregel 4 verlangt den Kontrollfluss-Knopf "ins naechste
Self-Play", und das war zweimal nicht erfolgt. **Sie ist seit v22 erfuellt --
ohne dass der Knopf je gesetzt wurde** (dort par.13, gemessen 2026-08-26): der
Erzeuger ist auf die Heuristik gewechselt, die ohnehin per Entscheidung
aufloest. Im Korpus stehen `choose_draw_stack_slot` in 2,5 Prozent der
Datensaetze (gegen "0 von 16.322" im Bestandskorpus) und tragen dabei zu
**100 Prozent** ein gueltiges Policy-Ziel.

**NICHT angefasst.** Die reparierte Abbruchregel liegt bereits als Knopf
daneben (`MOSAIC_STACK_DRAW_RESERVATION`,
`PREREG_stack_draw_reservation_rule.md` par.5b, Default AUS). Offen bleibt der
Kontrollfluss im NETZ-Self-Play -- eine Arena-Frage.

**Sie ist seit heute billiger:** der Anker liegt als Artefakt vor, und der
Knopf beruehrt ohnehin nur die NETZ-Seite (die Heuristik-Seite der Ankerarena
traegt `false`). Ein Umschalten aendert den SPIELER, nicht den MASSSTAB.

**Was sich durch die Kapselung geaendert hat:** der Anker liegt jetzt als
Artefakt vor und ist gegen eine Aenderung an dieser Stelle geschuetzt. Die
Frage, ob die Sammelaufloesung im Netz-Self-Play bleiben soll, ist damit
billiger zu stellen als vorher.

## OFFEN, nach Reihenfolge

### 1. v22-Korpus mit dem v2-Lehrer -- NUTZER: "muessen wir noch was vorbereiten"

Der wichtigste offene Punkt und Voraussetzung fuer mehrere andere. Der Korpus
**ist** die Heuristik v2 (Nutzer-Klarstellung 2026-08-25), also ein
spaltenkompetenter Erzeuger (0,798 volle Spalten je Partie gegen 0,086).

Entscheide stehen bereits in `PREREG_heuristic_v2_long_rows.md` par.3b:
Ownership-Kopf **einschalten** statt umbauen, plus **w0-Kontrollarm auf
DEMSELBEN Korpus**. Ohne den Kontrollarm sind Kopf und Korpuswechsel
konfundiert und der Effekt ist nicht zuordenbar -- das ist die eine Bedingung,
die nicht wegfallen darf.

**Was daran haengt:** der Realisierungsabschlag und der Plattenwert der
Blindzieh-Regel (heute an v20 geeicht, mit Vorbehalt), der Shaping-Kopf
(par.3b) und die Einhuellende im 2D-Encoder -- alle drei waeren auf
plattenblindem Spiel geeicht, solange dieser Korpus fehlt.

#### Vorbereitung, in dieser Reihenfolge (Nutzer-Entscheid 2026-08-25)

Kriterium fuer "gehoert davor": es aendert, WAS der Generator tut, oder es ist
spaeter nur durch Neu-Erzeugen korrigierbar. Alles andere misst auf dem Korpus
und gehoert danach.

| # | Punkt | Stand |
| --- | --- | --- |
| 1 | **Blindzieh-Reparatur entscheiden** | **ERLEDIGT 2026-08-25: kein Staerkegewinn**, Knopf bleibt AUS. Korpus kann mit dem Bestand erzeugt werden (`PREREG_stack_draw_reservation_rule.md` par.5d) |
| 2 | **Heuristik-Variante bis ins Self-Play durchreichen** | **ERLEDIGT 2026-08-25, im zweiten Anlauf.** Der erste Durchreich-Commit erreichte den Erzeugungspfad nicht (Verbraucher nur im Arena-Zweig); ein 200-Partien-Korpus war bitgleich mit v1. Behoben in ZWEI Haelften: Tiling (`224cc42`) und Draft-Vorzug (`61b2fff`). **Abnahme jetzt auf dem AUFZEICHNENDEN Pfad** (`heuristik_variante_reaches_the_recording_self_play_path`). Wirkung am 200-Partien-Piloten: volle Spalten **0,755 ± 0,080** gegen 0,050 (v1) -- reproduziert den Lehrer-Test (0,798) im Rauschen. k1 von 5,1 % auf **55,7 %** der Partien, Strafleiste 10,30 auf 5,09 Steine, Punkte 20,9 auf 47,1. Vorzugs-Records tragen `policy_target_valid=false` (Feuerrate **61,9 %** der Draftingzuege mit echter Wahl); die Flagge steht JE RECORD, die Trainingsseite kann sie achten oder ignorieren -- der Korpus ist in beide Richtungen brauchbar |
| 3 | **Arena-Threadzahl geradeziehen** | **ERLEDIGT 2026-08-25.** EINE Konvention (`self_play::thread_plan`): `0` = alle Kerne, `1` = sequenziell, `n` = n Threads. Vier Arena-Einstiege umgestellt. Abnahme: dieselben 12 Seeds sequenziell gegen 11 Threads -> **Ergebnisse identisch**, 44,5 s auf 13,0 s (3,4x) |
| 4 | **Bootstrap-Horizont 2 gegen 3** | **ERLEDIGT 2026-08-25: Horizont 3 VERWORFEN** (Verdikt gilt; der Messkorpus war aber V1, nicht v2huelle -- par.9g). Gepaart auf 200 v2huelle-Zustaenden trifft er den echten Ausgang schlechter (Brier +0,0567 ± 0,0254, Null klar ausgeschlossen) und kostet Faktor 1,63. Die Labels unterscheiden sich dabei sehr wohl (51 % ueber 0,01) -- die Frage war echt, nur die Antwort negativ. **v22 laeuft mit Horizont 2.** `PREREG_bootstrap_horizon.md` par.9f |
| 5 | **Erzeugung mit dem HEUTIGEN Wheel** | erfuellt, darf nicht rueckwaerts passieren |

**Zu 1:** `resolve_and_apply_stack_draw` sitzt in `apply_chosen_action` und
laeuft damit in JEDEM Self-Play, auch im heuristischen. In den ~39 Prozent
Partien mit Kriterium 6 verbrennt die Bestandsfassung rund 11 Punkte je Partie
und treibt 58-66 Prozent der Ziehserien auf Punktestand 0. Das landet in den
Scores, den Trajektorien und damit in den **Value-Labels**. Wird v22 mit dem
Defekt erzeugt, traegt ihn jedes daraus trainierte Netz mit.

**Zu 2 (erledigt):** der Self-Play-Einstieg war auf V1 festgenagelt; nur die
Arena nahm die Variante als Parameter. Jetzt durchgereicht, mit Vorgabe "v1"
auf jeder Ebene -- Bestandsaufrufer bleiben byte-identisch (Paritaets-Hash
`8c6684ff...` haelt, Suite 526/0). Die Bestandssignatur
`run_self_play_with_net_labels` ist BEWUSST unveraendert geblieben und
delegiert; daneben steht `..._variante`. Grund: `engine/examples/` ruft sie
auf, und der pre-push-Hook kompiliert die Beispiele mit.
**Belegt statt angenommen:** gleicher Seed, `v1` gegen `v2huelle` -> die
Partien unterscheiden sich; ein ungueltiger Wert wird abgewiesen statt still
auf v1 zu fallen. Die Variante steht ausserdem in den Metadaten der erzeugten
Dateien -- sonst waere spaeter nicht feststellbar, womit ein Korpus entstand.
**ENTSCHIEDEN 2026-08-25 (Nutzer): v22 wird mit `v2huelle` erzeugt.**
Gestuetzt durch beide Messungen -- der Lehrer-Test (par.10.1) gibt der Huelle
0,798 volle Spalten gegen 0,086, und der Phasenfaktor `v2huellephase` ist in
par.11.1 als H0 negativ entschieden (n=160, volle Spalten 0,812 gegen 0,787,
t=0,39, Siegquote 0,500). Es gibt also keinen gemessenen Grund, die Kampagne
an den juengeren Arm zu binden.

**Zu 3:** ein 814-Partien-Lauf kostet sequenziell 2 h 48 min statt 35 min. Bei
einer Korpus-Kampagne ist das kein Schoenheitsfehler.

**Zu 5:** erst seit 2026-08-25 schreibt `serialize_player` `col_f_max` und
`cell_reachable_mask` ins Zustands-JSON. Ein frueher erzeugter Korpus haette
die Felder nicht, und die zwei neuen Eingaben waeren auf ihm tote Nullen --
die Rueckfallwerte sind 0,0. Aktuell erfuellt; wer das Wheel zurueckdreht,
zerstoert es still.

### 2. Reparatur der Blindzieh-Stopp-Regel (EINGETAKTET 2026-08-25)

Eingriff in den DEFAULT-Pfad, deshalb ausdruecklich eingetaktet.

**Der Defekt:** `self_play.rs:517-534` vergleicht `avg_remaining_type_value`
(Typmittelwert in [1, 3]) gegen `best_eval_for_tile` (absolutes Brettniveau,
mit Kriterium 6 stark negativ). Zwei Einheiten, ein Vergleich -- sobald das
Niveau negativ ist, ist die Weiterzieh-Bedingung fast immer erfuellt.

**Die Reparatur, ohne neue Formel:** `best_eval_for_tile` nimmt eine beliebige
Platte, also auch eine aus dem Restpool. Damit laesst sich beides in derselben
Einheit rechnen -- weiterziehen, solange
`E[max(best_eval(V_next) − max(best_eval(gezogene)), 0)] > 1`, Erwartungswert
ueber die Pool-Platten des Typs, den die sichtbare Rueckseite ansagt.

**Vorab zu klaeren:** (a) Kosten -- `best_eval_for_tile` laeuft ueber Slots
mal Rotationen, ueber den ganzen Restpool je Entscheidung ist das deutlich
teurer als der heutige Mittelwert; zu messen, BEVOR die Regel scharf gestellt
wird. (b) Knopf mit Default AUS, damit die Arena beide Arme fahren kann.

**ABNAHME GEFAHREN 2026-08-25 (par.5d): KEIN Staerkegewinn.** 200 gepaarte
Partien, Champion@400 gegen Heuristik@150. Netz-Siege 151/200 gegen 141/200
(McNemar p=0,1539), Punkteniveau −0,97 ± 1,59; in der Platte-6-Teilmenge
(n=76) −1,26 ± 3,34. Kein Arm ist besser, der Knopf bleibt auf Default AUS.

**Zwei Lehren daraus, beide korrigierend:**

1. **Meine Begruendung fuer den Plattensatz-Schnitt war falsch.** Hier stand,
   ohne Kriterium 6 "kann kein Unterschied entstehen" -- es entsteht einer
   (−0,80 Punkte, zwei gekippte Partien). Ohne Kriterium 6 ist das Brettniveau
   zwar positiv, aber `avg_remaining_type_value` liegt in [1, 3]; bei kleinem
   `max_drawn` zieht auch die Bestandsregel weiter. Richtig: der Unterschied
   ist dort SELTEN, nicht unmoeglich.
2. **Der erwartete Punktegewinn bleibt aus**, obwohl die Bestandsregel
   nachweislich 9-13 mal zieht, wo die optimale Regel 1 sagt. Damit steht die
   BEWERTUNG einer Kuppelplatte zur Debatte, nicht die Stopp-Regel: entweder
   waren die gekauften Platten ihren Preis wert (das `V` aus par.5b ist zu
   niedrig), oder die Reparatur zieht jetzt zu wenig. Beide Zweige brauchen
   ein `V`, das an realisierten Punkten geeicht ist -- also das v22-Korpus.

### 3. Arena-Threadzahl geradeziehen -- ERLEDIGT 2026-08-25

`threads = 0` hiess in `run_heuristic_v1_vs_v2_arena` ALLE KERNE und in
`run_net_vs_heuristic_v2_arena` SEQUENZIELL. Dieselbe Sonde mit derselben Zahl
lief also einmal 12-fach und einmal einfach -- am Lehrer-Test sichtbar als
19,8 CPU-Minuten in 20,4 Wanduhr-Minuten bei 12 Kernen, Faktor 1,0.

**Gebaut:** `self_play::thread_plan` als EINE Konvention -- `0` = globaler
Pool (alle Kerne), `1` = sequenziell, `n` = eigener Pool. Umgestellt sind
VIER Arena-Einstiege; es waren vier und nicht zwei, die erwartete Trefferzahl
im Umbau-Skript hat die beiden uebersehenen gefunden. Die Self-Play-Einstiege
bleiben unberuehrt: dort heisst `0` schon "alle Kerne", und `1` baut einen
Pool mit einem Thread statt sequenziell zu laufen -- verhaltensgleich, im
Doc-Kommentar festgehalten, damit die Asymmetrie nicht fuer ein Versehen
gehalten wird.

**Abnahme, gemessen statt angenommen:** dieselben 12 Seeds,
`net_vs_heuristic_v2_arena` einmal mit `threads=1` und einmal mit
`threads=11` -- **Ergebnisse byte-identisch**, 44,5 s gegen 13,0 s (Faktor
3,4). Das war noetig, weil die Umstellung fuer die Netz-Arenen die Bedeutung
von `threads=0` von "sequenziell" auf "alle Kerne" dreht: jeder
Bestandsaufrufer mit 0 laeuft ab jetzt parallel.

### 4. JSON-Umzug: Restentscheid

Die Artefakte liegen jetzt in `evaluations/artifacts/` und sind **ungetrackt**
(`.gitignore`). Folge: ein frischer Klon hat die Messartefakte nicht, und
Preregs zitieren sie als Beleg. Bei deterministischen Sonden ist ein Lauf
wiederholbar (belegt: der Wiederholungslauf des Strafleisten-Tors war
byte-identisch), bei allem mit Netz-Zufall nicht ohne Weiteres.
Zurueckdrehen: `.gitignore`-Zeile entfernen und
`git add -f evaluations/artifacts`.

### 5. Weitere offene Straenge

| Strang | Datei | Zuschnitt |
| --- | --- | --- |
| **Shaping-Kopf statt Ownership-Kopf** | `PREREG_heuristic_v2_long_rows.md` par.3b | Vorregistriert, nicht gebaut. Sagt die Dreiecks-Abweichung voraus; zwei Kanaele, Abkling-Kurve. Braucht erst das v22-Korpus |
| **Einhuellende im 2D-Encoder** | – | Nutzer-Frage 2026-08-24, nicht registriert. Zusaetzliche Eingabeebene "Dreiecks-Zugehoerigkeit je Zelle"; additiv moeglich, aber nach par.3b |
| **R5-Netz-Loeser + R5-Value-Kalibrierung** | `PREREG_r5_solver_split.md` par.2, Teil B | Netz-Loeser-Arme und Vierer-Kopf-Vergleich. Zielmetrik `r5_value_calibration`-Steigung, heute 0,06-0,09 statt ~1. Arm 3 braucht ein b-Serie-Modell mit gepruefter Traegerschaft |
| **Seeding-Folgearm: Dosis** | `PREREG_start_position_seeding.md` | k=6 war die erste Dosis; hoehere Dosis naheliegend, nicht registriert |
| **UVFA-Regime-Eingabe** | `PREREG_uvfa_plate_regime.md` | par.8: Conditioning-Dropout und Leakage-Waechter sind PFLICHT. par.7-Entscheid steht aus |
| **Saettigende Score-Utility** | `PREREG_saturating_score_utility.md` | Tor gefahren, Verdikt DAZWISCHEN -- **Nutzer-Entscheid offen**: sigma-Kopf auf `points_val` oder auf ein TD-unberuehrtes Ziel |
| **Agenten-Kapselung: Ausbau** | `PREREG_agent_encapsulation.md` par.4 | Entschieden und gruen; offen nur der planbare Ausbau der restlichen ~31 Knoepfe ins SearchConfig, je Knopf ein Commit mit Paritaets-Gate |
| **#29-Instrument** | `PREREG_post34_package.md` | WARTET AUF POWER: braucht mindestens 6 arena-entschiedene Paare (Stand ~3) |
| **Rundenuebergang bemustern** | `PREREG_round_transition_search_sampling.md` | Nichts gemessen. Zusatz aus der externen Recherche: robuste Aggregatoren (Median, gestutztes/winsorisiertes Mittel) statt des arithmetischen |
| **Risikosensitive Blatt-Utility** | `PREREG_risk_sensitive_leaf_utility.md` | Nichts gemessen; `points_dist` ist abgeschaltet, der Champion traegt den Kopf nicht |
| **Blindziehung: Suche und Merkmale** | `PREREG_chance_nodes.md` Teil B1, `PREREG_stack_top_feature.md` | Beide geparkt. B1 gibt der SUCHE die korrekte Peek-Bewertung, das Merkmal gibt dem NETZ die sichtbare Rueckseite |
| #31 / #38 / #39 | – | geparkt, Arbeitskreis "Spaeter"; Beschreibungen im Archiv |
| **v22-Fenster** | `PREREG_v22_window.md` | **NEU GEFASST 2026-08-25, ENTSCHIEDEN.** Der alte Rotations-Zuschnitt war fuer einen NETZ-Erzeuger gebaut und ist hinfaellig -- das v22-Fenster IST jetzt der v2-Lehrer-Korpus (24.000 Partien, eine Klasse, kein Altbestand). Frueher stand hier ausdruecklich "nicht zu verwechseln mit dem Lehrer-Korpus"; das gilt nicht mehr |

**Geschlossen, nicht neu vorschlagen:** Q-Skalierungs-Option, jeder
Suchparadigmen-Wechsel (zwei externe Recherchen), Mehrfach-Determinisierung
(`PREREG_ismcts_determinizations.md`: k=4 faellt unter zwei Anordnungen
signifikant ab), Phasenfaktor, Vollendbarkeits-Relaxation im Routing und die
zwei Punktekarten (`PREREG_heuristic_v2_long_rows.md` par.11-16),
`PREREG_long_row_payoff.md` B1, `PREREG_bootstrap_horizon.md` (beide Arme).

---

## OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Stand |
| --- | --- |
| **v22 vorbereiten** | Nutzer-Ansage 2026-08-25: "dafuer muessen wir noch was vorbereiten" -- was genau, ist offen |
| **Saettigende Score-Utility** | Verdikt DAZWISCHEN, kein Automatismus vorgesehen |
| **Stoerungs-Baustein Stufe 2** | gehoert zum Moon-Order-Kopf, keine Einzelentscheidung mehr |
| **Push** | NIE ohne ausdrueckliche Anweisung; Stand wird als "n Commits voraus" gemeldet |
| **Asym-Korpus** | bleibt lokal, Trainingsinput fuer Seeding und UVFA |
| **Fester Bewertungssatz** | 300 Dateien / 3000 Partien in `data/holdout/`, fertig 2026-08-18 |

---

## STRUKTURBEFUNDE, die weitergelten

- **Der Champion vollendet keine Spalten**, und der Grund ist Verteilung, nicht
  Versorgung: eine volle Spalte kostet 21 Zellen, das Netz verbraucht 42,7 und
  truege gleichverteilt 2,03 Spalten statt 0,10.
- **Die Dreiecksform ist die MACHBARKEITSHUELLE, keine aesthetische Wahl.**
  Erlaubt ist `r + c <= 5`, also 21 Zellen -- dieselbe 21, die eine volle
  Spalte kostet.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich**: sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je Runde
  ab -- fuenf Steine fuer sechs Zellen. Spalten haben das Problem nicht.
- **BERICHTIGT 2026-08-26 (gemessen): der Durchbruch kommt vom DRAFTING, das
  Routing allein traegt nichts.** Bis hierher stand hier "der Durchbruch kam
  vom Platzierungs-ROUTING". Der Split-Test (`PREREG_v22_window.md` par.4f,
  je 160 gepaarte Partien) zerlegt die vollen Spalten so:
  Huelle nur im Drafting **0,756** gegen 0,044 (t 10,29), Huelle nur im
  Routing **0,113 gegen 0,113** (delta 0,000), gekoppelt 0,975 gegen 0,062.
  Die Luecke von +0,199 zur Summe ist eine WECHSELWIRKUNG: das Routing kann
  nur einsortieren, was das Drafting geholt hat -- ohne passende Steine laeuft
  `v2_tiling_preference` ins Leere.
  Richtig bleibt der Mechanismus-Satz dahinter: `best_first_step_inner` waehlt
  nach reinen Sofortpunkten (`tiling_solver.rs:49-56`) und wirft Draft-seitige
  Absicht weg -- nur ist das die kleinere Haelfte.
- **Erste unkontaminierte Referenz**: zehn Mensch-gegen-Netz-Partien in
  `static/log/`, der Mensch gewinnt 8 von 9 und schliesst **1,80 volle
  Spalten** je Partie gegen 0,10 des Netzes. Platzierungspunkte sind dabei ein
  Gleichstand (54,9 gegen 55,8) -- der Vorsprung sitzt bei den Spezialfliesen.
- **Realisierungsprofil eines plattenbewussten Spielers** (dieselben zehn
  Partien, Platzierungen je Rasterreihe): Mensch 3,60 / 3,30 / 3,20 / 2,60 /
  2,30 / 1,70 gegen Netz 4,70 / 4,70 / 3,30 / 2,30 / 1,10 / 0,50. **Gleiche
  Summe, andere Verteilung** -- der Mensch tauscht kurze Reihen gegen lange
  (Reihe 5 und 6: Faktor 2,7 bzw. 2,9 gegenueber dem v20-Selbstspiel).
- **B1-Vorgabe fuer jeden Nachfolge-Arm**: wer die Initiierung hebt, ohne die
  Vollendungsquote deutlich ueber 0,53 zu bringen, wiederholt B1.
- **Blindzieh-Regel**: bei Wertungsplatte 6 (Code-Index 6, Spezialfelder --
  das EINZIGE negative Kriterium) laeuft die gebaute Stopp-Regel das
  Punktekonto leer. Ohne Platte 6 haben 92-95 Prozent der Ziehserien Tiefe 1
  (bei Mensch gegen KI 25 von 25); mit ihr enden 58-66 Prozent der Serien bei
  Punktestand 0. Auf konstruierten Brettern zieht sie 9 bis 13 mal, wo die
  optimale Regel 1 sagt. **Spaltenbau behebt das NICHT** -- Kriterium 1 zahlt
  quadratisch `7*(f/6)^2`, das Spezialfeld-Defizit kostet linear -3 je Feld;
  eine volle Spalte gleicht gerade zwei leere Spezialfelder aus.
- **Methodische Lehre**: aus "Eingriff X in Richtung Y verliert" folgt NICHT
  "Y ist falsch" -- nur, dass X in diesem Zustand verliert. Es fehlt die
  Kontrollgruppe: ein Agent, der Y KANN.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch, drei in der
  Parallelsitzung und eine hier (Kriterium 6 "startet bei -27": falsch,
  `special_empty` zaehlt nur Spezialfelder auf bereits GELEGTEN Platten).

---

## BENENNUNG DER GENERATIONEN (damit der Off-by-one nicht wiederkehrt)

**Ein Fenster vN traegt die Partien von Champion v(N-1).** Beleg: das
v22-Fenster enthielt `v21wdl`-Partien (Generator = v21-Champion, alte Tabelle
in `PREREG_v22_window.md`). Daraus folgt fuer die laufende Kette:

| | |
| --- | --- |
| `hv2`-Korpus (laeuft) | **das v22-Fenster** -- Erzeuger ist die Heuristik, nicht ein Champion |
| daraus trainiert | **v22-Netz** |
| dessen Self-Play | fuellt **das v23-Fenster** |
| daraus trainiert | **v23-Netz** |

Zuschnitt des v23-Fensters ist seit 2026-08-25 festgelegt (`PREREG_v23_window.md`): 29.450 Partien, davon **12.000 aus dem v22-Self-Play** (4.000 Sockel + 8.000 Schwarm `--value-only`) und **17.450 aus hv2** (6.550 rotieren aus). Damit steht auch der Umfang des v22-Self-Play-Laufs fest. Drei offene Punkte dort: G-1/G-2 kommen aus DEMSELBEN Korpus (Platzhalter, keine Aera-Streuung), der Cache ist UNKRITISCH (gemessen 2.806 B je Zustand statt der veralteten 6 KB -> ~14,1 GB gegen 34,3 GB), und die Policy-Ausbeute der hv2-Plaetze haengt an der Traegerfrage.

Der haeufige Fehler ist, das Self-Play, das v23 fuettert, "v23-Self-Play" zu
nennen. Es ist das **v22**-Self-Play. Am 2026-08-25 einmal passiert und in
zwei Preregs korrigiert.

---

## LAUFZEITEN (gemessen, nicht geschaetzt)

Planungsgroessen. Die belastbaren Zahlen stehen je Lauf im Artefakt
(`laufzeit`-Block, Pflichtfeld seit 2026-08-25). Wer eine Zeile ergaenzt,
traegt GEMESSENES ein.

| Aufbau | Umfang | Threads | Wanduhr |
| --- | --- | --- | --- |
| Heuristik gegen Heuristik, 150 Sims (`v2_envelope_arena.py`) | 160 Partien | 0 = alle 12 Kerne | **21,9 s** |
| dito, Rauchtest | 20 Partien | alle Kerne | **4,1 s** |
| Netz@400 gegen Heuristik@150 (`v2_teacher_arena.py`), je Partie | – | 0 = **sequenziell** | **12,357 s** |
| dito | – | 11 | **2,575 s** |
| dito, voller Lauf | 814 Partien | 0 = sequenziell | ~2 h 48 min |
| dito | 814 Partien | 11 | ~35 min |
| Strafleisten-Tor (`floor_action_aversion_gate.py`), 240 Stellungen, sims=200 | – | – | **~7 min** |
| Heuristik-Self-Play `v2huelle`, 600 Basis-Sims, Netz-Labels | 200 Partien | 11 | **239 s** = 50 Partien/min |
| dito, `v1` (Vorzug feuert nicht, Suche laeuft voll) | 200 Partien | 11 | **331 s** = 36 Partien/min |
| `cargo test --release --lib` (volle Suite) | 527 Tests | – | **~65 s** |
| `cargo test --release` (alle Ziele, exklusiv, 2026-08-26) | 553 Tests | – | **97,1 s** |
| Datei-Cache erstbauen (`build_cache_incremental.py`) | 120 Dateien | 6 Worker | **112,6 s** = 0,96 s je Datei |
| Split-Arm Heuristik (`v2_envelope_arena.py --tiling`) | 160 Partien | 0 = alle Kerne | **~22 s** |
| dito, Bloecke liegen schon (anderes Fenster) | 120 Dateien | 6 | **7,9 s** |
| Wheel-Bau (`maturin build --release`) plus Installation | – | – | **~30 s** |

**Parallelisierung ist ergebnisneutral, gemessen statt angenommen** (20 Seeds
beidseitig): Siegquote 0,450, volle Spalten 1,200 und Punkte 55,0 in BEIDEN
Faellen identisch, bei 4,8-fachem Tempo. Grund:
`PREREG_search_rng_split.md` -- jede Partie haengt an ihrem eigenen,
abgeleiteten Suchstrom.

---

## STELLUNGSVIELFALT DES LEHRER-KORPUS (gemessen 2026-08-25)

Anlass war eine Sorge, die sich als unbegruendet erwiesen hat: der v2-Vorzug
setzt den Zug OHNE Suche und umgeht damit `play_temp` (self_play.rs:374) auf
61,8 Prozent der Draftingzuege. `play_temp` existiert genau fuer
Zustandsvielfalt (0,7 / 0,4 / 0,15 je nach Aktionszahl; das AUFGEZEICHNETE
Ziel laeuft separat mit festem `TARGET_TEMP = 0,15`).

Gemessen auf je 200 Partien, Brett-Vielfalt als (Runde, 36-Bit-Fuellmaske):

| | v2huelle | v1 |
| --- | --- | --- |
| distinkte Zustaende | **6.164** | 6.008 |
| davon mehrfach vorkommend | **36,1 %** | 48,9 % |
| distinkte je Partie | **40,9** | 37,4 |

**Der Lehrer-Korpus hat MEHR verschiedene Stellungen, nicht weniger**
(Faktor 1,026) und deutlich weniger Wiederholungen. Grund: v1 wirft die
Haelfte seiner Steine auf die Strafleiste (10,30 gegen 5,04 Steine je Partie)
-- was dort landet, erreicht das Brett nie. v1-Bretter bleiben leerer
(Fuellstand 2,49 gegen 2,92) und haben damit weniger moegliche
Konfigurationen. Der Vorzug nimmt Vielfalt bei der Zugwahl weg und gibt mehr
zurueck, weil er das Brett ueberhaupt erst fuellt.

**Grenze der Aussage:** gemessen ist BRETT-Vielfalt, nicht
Trajektorien-Vielfalt. Fuer den Value-Kopf -- den Grund, warum v22 existiert
-- ist das die richtige Groesse; ueber die Breite der Policy-Exploration sagt
sie nichts. Sonde `tools/probes/corpus_state_diversity_probe.py`, Artefakt
`evaluations/artifacts/corpus_state_diversity.json`.

---

## FALLEN (aus echten Vorfaellen)

- **CPU-Nebenlast verstuemmelt Arena-Partien** (2026-08-20). Derselbe
  8-Partien-Smoke lieferte unter Last zwei verschiedene Ergebnisse (eine
  Partie endete 3:1), ohne Last dreimal byte-identisch. **Arena-Messungen
  laufen EXKLUSIV** -- keine zweite Arena, keine Sonde mit Suchlauf, kein
  Training, auch kein `cargo`-Lauf. Determinismus-Checks zaehlen nur unter
  denselben Lastbedingungen wie die Messung.
- **"Erste N je Datei" ist ein stiller Rundenfilter** (2026-08-25). Sonden,
  die je Datei die ersten N qualifizierenden Datensaetze nehmen, ziehen
  Fruehspiel-Stellungen -- Datensaetze stehen in Zugreihenfolge.
  `floor_action_aversion_gate.py` hatte dadurch 268 von 280 Stellungen in
  Runde 1 und ein daraus abgeleitetes Verdikt, das nur fuer Runde 1 galt;
  repariert (`rounds=`/`seed=`, Bestandsauswahl byte-identisch erhalten).
  **Gleiches Muster, gleiche Wirkung, NICHT repariert:
  `long_row_init_knob_effect.py` misst ausschliesslich Runde 1** (alle 240
  Stellungen). Gegenprobe: `long_row_prior_gate.py` hat dasselbe Muster, aber
  einen groesseren Deckel und ist unauffaellig (12/105/82/61) -- die Falle
  haengt am Verhaeltnis Deckel zu Trefferdichte.
- **Python schreibt auf Windows still CRLF** (2026-08-25). Ein Skript mit
  `write_text` wandelte in 137 Dateien LF in CRLF; in einer Datei waren das
  971 Byte Zuwachs bei zwei geaenderten Zeilen. `git diff` zeigte wegen der
  Normalisierung weiter zwei Zeilen -- aufgefallen ist es nur an der
  Datei-Groessen-Ratsche. Wer so ein Skript schreibt: `newline` auf LF setzen.
- **Totes Wheel: Zahlengleichheit bei gleichen Seeds ist ALARM** (2026-08-25).
  Eine gepaarte 200-Partien-Arena lieferte NULL diskordante Paare, Block fuer
  Block identisch. Das war kein "kein Effekt", sondern ein Wheel ohne den
  gemessenen Knopf: Wheel 13:14, Knopf-Einbau 13:28. Neun Minuten Messzeit auf
  totem Code. Wer einen Knopf misst, prueft VORHER, ob das installierte Modul
  ihn kennt -- und zwar mit `knob_registry_json()`, nicht mit
  `engine_config_json()`: letzteres listet nur ausgewaehlte Werte und meldete
  auch nach korrektem Neubau "nicht bekannt". **Ein negatives Ergebnis aus
  einem ungeprueften Instrument ist kein Befund.**
- **Prereg-Koepfe veralten gegen ihren eigenen Koerper** (2026-08-25, zweimal
  an einem Tag). `PREREG_chance_nodes` behauptete ein Merkmal, das es nicht
  gibt; `PREREG_heuristic_v2_long_rows` fuehrte par.11 als "ungemessen",
  waehrend par.11.1 laengst das Ergebnis trug. Beide Male hat der Kopf einen
  Leser in die Irre gefuehrt. Die Pflegeregel ist nicht Kosmetik.
- **Wheel nach Engine-Aenderung neu bauen.** `cargo test` gruen heisst nicht,
  dass Python den neuen Code sieht. `maturin develop` scheitert hier (kein
  Virtualenv); der Weg ist `maturin build --release` plus
  `pip install --force-reinstall --no-deps`.
- **Backticks in doppelten Quotes** werden von der Shell ausgefuehrt --
  Markdown-Code-Spans verschwinden spurlos aus Text, der ueber `python -c`
  oder `git -m` geschrieben wird. Heredoc mit einfachen Quotes benutzen.

---

## GELTENDE REGELN (kompakt)

Langform samt Herleitung: `../archive/history.md`, Kapitel "Vollstaendiger
STATUS-Stand vom 2026-08-25", Abschnitt "GELTENDE REGELN".

**Messen und Auswerten**

- **Score-Auswertungen IMMER auf Block-Ebene.** Paar-SEs werden sonst massiv
  unterschaetzt.
- **Aufloesung schlaegt Sparsamkeit.** Bei n=400 streut dieselbe Konfiguration
  um 5,75 Prozentpunkte; der Seed bewegt die Metrik 4- bis 6-mal staerker als
  jeder Knopf.
- **Value-Aenderungen brauchen Arena-Gating** -- es gibt keinen validierten
  Offline-Praediktor.
- **Sechs Standard-Kennzahlen in JEDEM Messbericht**: Reihen-, Spalten- und
  Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte, Margin.
- **Laufzeit ins Artefakt**, nicht nur nach STATUS: `laufzeit`-Block mit
  `wanduhr_s`, `cpu_s`, `threads`, `s_je_partie`.
- **Lange Laeufe nie in eine Pipe**, keine eigene Umleitung; Fortschritt mit
  `flush` sichtbar machen.

**Training und Korpus**

- **Fenster-Pinning: ZWEI Variablen**, nicht eine -- Trainings waehrend
  laufender Generierung immer pinnen (Split-Shift, Cache-Neubau,
  Kontamination).
- **Traeger-Status vor jeder Policy-Aussage pruefen.** Korpora sind per
  Default NICHT policy-traeger.
- **Backup- und Alt-Regel-Korpora kommen NIE wieder ins Training.**
- **Promotions-Checkliste** und **Nachschub bei Gating-Fehlschlag**: Langform
  im Archiv, hier nur der Merkposten, dass beides existiert und gilt.
- **Nie auf plattenblindes Normalspiel eichen.** Kalibrierung und Zielraten
  nicht gegen die Verteilung heutiger Netze, wenn genau deren Verhalten das
  Ziel ist.

**Arbeitsweise**

- **Loeschen nur mit expliziter, pfadgenauer Rueckfrage.** Eine Frage ist
  keine Anweisung.
- **Push nie ohne ausdrueckliche Anweisung.**
- **Parallele Sitzungen: Spurdisziplin.** Fremde Straenge und Preregs nicht
  abarbeiten; `git add` pfadgenau statt verzeichnisweit (am 2026-08-25 sind
  drei fremde Dateien in einen Commit gerutscht).
- **Prereg-Kopf und Index**: wer ein Ergebnis registriert, zieht den
  Zeile-1-Kopf im selben Zug nach und laesst
  `python tools/generate_prereg_index.py` laufen. Gueltige Status:
  OFFEN / ENTSCHIEDEN / UEBERHOLT.
- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** -- es definiert die
  Elo-Leiter.
- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte Gegner.

---

## ARCHITEKTUR (Referenz, Stand 2026-08-25)

**Such- und Engine-Seite** (`engine/src/net_mcts.rs`)

- `ACTIVE_LEAF = LeafEval::Net`; Stufe 1 (DFS-Blatt) liegt dormant, Rueckfall
  ist ausgeschlossen (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv: `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`, `ROUND_TRANSITION_SAMPLING = false`,
  `SHUFFLE_STACK_PEEK_IN_SEARCH = false`, `bootstrap_horizon_rounds = 2`.
- **Zwei R5-Loeser**: der eingefrorene `round5_anchor.rs` haengt an den drei
  Heuristik-Sucheinstiegen und schuetzt die Elo-Leiter; `round5.rs` ist der
  Netz-Loeser und darf sich entwickeln. Runde 5 ist **Expectiminimax** mit
  Zufallsknoten an den Chip-Aufdeckstellen; `NODE_BUDGET = 200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl -- **kein geloestes Endspiel**
  (~3 Halbzuege, Orakel-Uebereinstimmung 81,4 Prozent).
- **Der Stapelzug wird gesammelt aufgeloest**
  (`self_play.rs::resolve_and_apply_stack_draw`, Default-Pfad): die Suche
  bewertet EINEN Peek, danach zieht eine handgeschriebene Schleife weiter und
  waehlt Platte, Slot und Rotation selbst -- Kosten und Ergebnis weichen vom
  Bewerteten ab. Siehe offener Punkt 2.

**Netz- und Trainingsseite** (`config.py`, `engine/py/neural_net.py`)

- **`INPUT_SIZE = 714`** (seit 2026-08-25: plus 6 `col_f_max`),
  **`NUM_PLANES_CHANNELS = 77`** (plus 1 Ebene Erreichbarkeit, Kanal 76),
  `NUM_ACTIONS = 406`.
- Beide neuen Groessen werden in `serialize::serialize_player` **einmal**
  gerechnet und ins Zustands-JSON geschrieben; der Rust-JSON-Pfad und Python
  LESEN sie, nur `state_to_features_direct` rechnet selbst (bewacht von den
  `direct_matches_json_path_*`-Tests). Kosten als Bitmaske: plus 0,27 Prozent
  je Korpus statt plus 3,80 Prozent als Liste.
- **Altmodelle bleiben bitgleich**: `net::split_planes_flat_batch_src` kuerzt
  den Planes-Block auf die Modellbreite und liest den Flat-Block ab der
  Quell-Grenze; neue Groessen haengen am ENDE ihres Blocks. Am Champion
  belegt (Paritaets-Hash unveraendert), nicht hergeleitet.
- Champion-Encoder ist **2D** (`Mosaic2DNet`); der flache `MosaicNet` bleibt
  Parallel- und Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`,
  `opp_points`. `ownership` ist 140 breit, `OWNERSHIP_WEIGHT = 0` -- der
  Champion-Kopf ist **untrainiert**.
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, `VALUE_OPP_EPSILON = 0,0`.
- **Value-Ziel ist margen-BLIND** (`values_wdl`, TD-Blend aus
  Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang). Training:
  `--value-head wdl --select-by-brier`.
- Champion: `models/champion.txt` zeigt auf `v21_2d_brierbest`.

**Konstanten mit Fallstrick**

- `bonus_points` in `dome.rs` ist ein **Diskriminator** (Special = 3,
  Wild = 0), KEIN Punktwert -- der echte Spezialfeld-Wert ist die Rasterreihe
  1 bis 6.
- `special_empty` zaehlt nur Spezialfelder auf **bereits gelegten** Platten.
- Die Handbuch-Nummerierung der Wertungsplatten ist um eins gegen die
  Code-Indizes verschoben: Handbuch 7 = Code 6 = Spezialfelder.
