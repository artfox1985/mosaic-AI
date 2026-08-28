# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Alles Entschiedene und
jede ausfuehrliche Herleitung liegt in `../archive/history.md`; der
vollstaendige Stand vor dieser Neufassung steht dort im Kapitel
"Vollstaendiger STATUS-Stand vom 2026-08-25"; was zwischen dem 2026-08-25 und
dem 2026-08-28 abgeschlossen wurde, im Kapitel "2026-08-25 bis 2026-08-28:
v22-Vorbereitung, Kapselung, Kanaele, Entstauchung".

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

Neu gefasst am **2026-08-25** (Nutzer-Auftrag: STATUS war mit 1180 Zeilen
schwer lesbar geworden).

**Entflechtung am 2026-08-28** (Nutzer-Hinweis: STATUS ist kein
Langzeitgedaechtnis -- dauerhaftes Prozesswissen verrottet hier ins Archiv).
Kanonisch liegen ab jetzt in `../docs/`:
`promotion_checklist.md`, `working_rules.md`, `pitfalls.md`,
`generation_naming.md`, `measured_runtimes.md`, `architecture_reference.md`.
Die betreffenden Abschnitte unten sind auf einen Verweis eingedampft; wer an
diesen Inhalten etwas aendert, aendert es DORT.

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

## STAND JETZT (2026-08-28)

**Champion:** `v21_2d_brierbest`, Elo **1215** [1170, 1259] auf der
R5-Fix-Leiter -- unveraendert. Kanten ueber die Fix-Grenze nie mischen.

**Wheel-Stand:** 79-Kanal-Build (Schlachtplan-Schritt 1a, `e91cd34`),
Vertragshash `efd564d87bac2722`; der Paritaets-Hash `8c6684ff...` ist
gemessen unveraendert.

**Es laeuft: NEUSTART der Ownership-Pol-Konsument-Arena (par.3b.6)** --
w05/w10/w20 sequenziell auf freier Maschine (Nutzer-Freigabe 2026-08-28,
"andere last ist durch"). Maschine NICHT frei: kein Build, kein Test, keine
Sonde nebenher. Der Auswerter nimmt seit dem Neustart je Partie-Nummer nur
die NEUESTE Datei (Erstlauf-Reste mischen nicht mehr). Historie des
abgebrochenen Erstlaufs: Registriert 2026-08-28
(`PREREG_heuristic_v2_long_rows.md` par.3b.6): MOSAIC_OWNERSHIP_TILING_W-Sweep
(w 0 / 0,5 / 1,0 / 2,0) mit dem b01-Kopf, argmax-Instrument des Spalten-Tors.
Der erste Anlauf wurde am 2026-08-28 GESTOPPT, weil parallel fremde
Nutzer-Last auf dem Rechner lief (EXKLUSIV-Regel). Lastbeginn per
Datei-mtimes datiert: Blockdauern konstant 118-133 s bis w05-Block 4
(22:24), ab w05-Block 5 (~22:25) ansteigend 164 -> 358 s. Stand je Arm:

* w00 (21:55-22:16): KOMPLETT, alle 10 Bloecke 118-133 s -- SAUBER.
  Zusaetzlich gilt der registrierte Reproduktions-Waechter (0,2975 aus
  par.3b.2) als Gegenprobe bei der Auswertung.
* w05 (22:16-22:52): KOMPLETT (g200 da), aber Bloecke 5-10 lastkontaminiert
  -> wird auf stiller Maschine KOMPLETT neu gefahren. Beifang der sauberen
  Bloecke 1-4: der Knopf kostet praktisch keinen Durchsatz (128-133 s wie
  w00). Byte-Vergleich Bloecke 1-4 alt gegen neu = gratis
  Determinismus-Gegenprobe.
* w10 (22:52-23:32): bis g140 gelaufen, durchgehend unter Last (~300 s je
  Block) -> verwerfen, komplett neu.
* w20: NIE GESTARTET.

Vor dem Neustart muessen die kontaminierten pkl weg (NUR mit pfadgenauer
Nutzer-Freigabe) oder die Auswertung filtert nach Lauf-Zeitstempel -- der
Auswerter (tools/probes/ownership_tiling_consumer_eval.py) globt heute je
Praefix und wuerde sonst zwei Laeufe mischen.

Loeschung von data/-Dateien nur mit pfadgenauer Nutzer-Freigabe. (Die
serielle Cache-Referenz, Tor 2b, ist GRUEN abgeschlossen -- A0-Tabelle.)

**Warum dieser Schritt** (par.3b.5 Weg-Wahl Punkt 1): der v22-Zyklus hat geliefert: b01 baut 3x so viele Spalten wie der Champion -- der Korpus wirkt. Aber das Ownership-TRAININGSGEWICHT traegt nicht (w0 fast gleichauf), und die Platzierung verschenkt das fast vollstaendig geerbte Draft-Erbe. KEIN v22-Self-Play, bis ein Konsument die Vollendung hebt. Der Tiling-Pol lief bisher NIE mit einem spaltenbewussten Kopf (Gate-C-Nullmessungen: plattenblinde Koepfe).

**16 Commits vor `origin/main`** (`git rev-list --count origin/main..HEAD`,
gezaehlt 2026-08-28), nicht gepusht -- Push ist ein eigener Nutzer-Entscheid.

---

## TRAEGER-MANIFEST-GENERATOR fehlt (offener Kern)

`data/` enthaelt kein `policy_carrier_manifest_*.json` mehr (Nutzer: bewusst
archiviert; die alten listen v18/v20/v21-Dateien). Fuer v23 wird ein NEUES
gebraucht: `PREREG_v23_window.md` par.1 verlangt **1.800 policy-aktive
hv2-Partien** (Sockel G-1 1.350 + G-2 450) neben 15.650 policy-maskierten aus
demselben Korpus -- also eine seed-bestimmte AUSWAHL, rund **180 von 1.745
hv2-Dateien**.

Im Baum gibt es nur LESER (`neural_net.py:1284`, `train_manifest.py`), keinen
Schreiber. Die REGEL ist dokumentiert (Seed plus "zeitlich gestreute
Auswahl"), der Erzeuger also rekonstruierbar statt neu zu erfinden.

**Vor der v23-Kampagne zu klaeren**, nicht dringend. Ohne das Werkzeug ist der
registrierte Zuschnitt nicht ausfuehrbar, und "jede Datei traegt Policy" waere
still ein anderer Zuschnitt als der beschlossene.

---

## MERKLISTE UND OFFENE POSTEN (Reste der Sitzungsuebergabe 2026-08-26)

Die Uebergabe-Bloecke vom 2026-08-26 sind erledigt und ausgelagert
(Verweiszeilen oben). Offen geblieben sind die beiden folgenden Abschnitte;
ihre Nummerierung bleibt unveraendert, weil andere Notizen sie so zitieren.

### 1e. CODEPFLEGE-AUDIT 2026-08-27: die VERSCHOBENEN Befunde (Merkliste)

Das 25-Punkte-Audit ist zur Haelfte umgesetzt (`97126a2`, S-Fixes). Der Rest
ist BEWUSST verschoben und hier festgehalten, damit er nicht im
Chat-Scrollback verrottet. Fundstellen-Details stehen im jeweiligen Befund
des Audit-Berichts (Agenten-Lauf 2026-08-27); die Nummern sind dessen
Zaehlung.

**Naechstes Build-Fenster (brauchen cargo, Paritaets-Gate):**

| Befund | Kern                                                                                                                                                                                                                                                                               | Risiko                                                        |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| neu | `build_cache_incremental.py --merge-out` bekommt `--file-list`: exakte Fenster-/Train-Teilmengen aus den per-Datei-Bloecken zu einem Monolithen fuegen, den `train.py --cache-file` per Schluessel-Waechter annimmt. FRIST: VOR dem v22-Self-Play (dann laeuft `--watch` dort mit, und jedes Rotationsfenster v23+ baut in Minuten statt ~40 min Monolith-Neubau je Fenster). Nutzer-Auftrag 2026-08-28 | ohne das ist das rotierende 3-Generationen-Fenster an den Monolith-Neubau gekettet |
| neu    | `MOSAIC_CARRIER_MANIFEST`-Default zeigt auf die bewusst archivierte `data/policy_carrier_manifest_v20.json` (seit der v20-Kampagne nie umgestellt). Fix: Default = LEER, wer ein Manifest will, setzt es explizit; Registratur-Eintrag nachziehen (Nutzer-Auftrag 2026-08-28) | Default sieht nach Bedeutung aus, ist aber tot |
| 4      | SECHS Dialekte fuer "ist dieser Bool-Knopf an?" (shaping.rs:999, state.rs:209, tiling_solver.rs:374/386, net_mcts.rs:230): `X=true` schaltet je nach Knopf AN oder AUS. Fix: ein `read_bool_env` neben `read_f64_env`, ~18 Stellen                                                 | ein A/B-Arm laeuft still als Kontrollarm                      |
| 13-15  | Drei stille Env-Verschlucker: `MOSAIC_INTERLEAVE_BATCH_MAX` ausser Range (net_batcher.rs:249), `MOSAIC_R5_NODE_BUDGET=0`/Tippfehler (round5.rs:199), `MOSAIC_PLATTENKOPF_GAMES`-Parse (scoring.rs:1508) -- alle fallen wortlos auf den Default                                     | Messung glaubt Knopf X, faehrt Default                        |
| 16     | Value-Spread-Pfad verkleinert bei eval-Fehlern still den Pool und liefert bei Serialisierungsfehler "{}" (self_play.rs:4607/4666)                                                                                                                                                  | plausibel-aber-falsch                                         |
| 19     | Toter Zweitpfad board.rs:184-220 + `DOME_TILES_EACH` (state.rs:19, null Nutzer, doppelt belegt): `completed_cols`/`is_col_complete` heissen wie die Spaltenbau-Wahrheit, SIND sie aber nicht (die lebt in scoring.rs:709-712). Loeschen oder `#[allow(dead_code)]` mit Begruendung | der naechste Spaltenbau-Bearbeiter greift zum falschen Symbol |

**Nach dem v22-Training:**

| Befund | Kern                                                                                                                                                                                                                                                                                   | Risiko                                                      |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 18     | ONNX-Paritaetspruefung NIE fertiggebaut: 56 `models/*.onnx.ref.txt` (export_onnx.py schreibt sie) + `py.rs:123 net_eval_raw` mit NULL Aufrufern. Entscheid: Vergleichsschritt fertigbauen ODER beide Haelften abraeumen -- der heutige Zustand sieht aus wie Absicherung und ist keine | Schein-Schutz                                               |
| 5      | Fenster-Cache-Key traegt die Kanalzahl nur als Hand-Literal `+enc2d_v2` (corpus_dataset.py:426), der Datei-Key rechnet sie aus den Konstanten. Fix = Selbstbedienung auch im Fenster-Key. NICHT vor dem Training (wuerde den frischen Cache entwerten)                                 | naechster Kanal-Schritt zieht still den alten Fenster-Cache |
| 20     | Viermal dasselbe 95%-KI mit drei Entartungen (u.a. Breite 0,0 bei n<2 = perfekte Schein-Praezision); eine gemeinsame Funktion                                                                                                                                                          | Zufallsbefund besteht als signifikant                       |
| 21     | Sieben Eigenaufloesungen von `models/champion.txt`; nur arena.py traegt die Audit-V2-Haertung gegen fehlendes ONNX                                                                                                                                                                     | OneDrive-Dateiverlust-Klasse                                |
| 22     | `MosaicDataset.__init__` = 998 Zeilen; Schnitt in drei Phasen (Schluessel, Cache-Lesen, Korpus-Bau) -- Nahtbreite VOR dem Schnitt auszaehlen (stehende Regel)                                                                                                                          | Wartbarkeit                                                 |
| 6      | `tools/offline_diagnosis.py` rechnet ein historisches Value-Ziel (Docstring seit `97126a2` ehrlich); echte Loesung = Zielbildung aus corpus_dataset herausziehen und teilen                                                                                                            | Metrik misst Altziel                                        |

(Befund 25, absolute Pfade in den Artefakt-Schreibern, steht bereits in der
Tabelle unten bei den drei JSONs.)

### 2. Offen, mit Kosten

| Punkt                                                                                                                                                                                                                                                                                                        | Kosten  | wofuer noetig                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Drei getrackte JSONs mit absoluten Pfadfragmenten repo-relativ machen: `evaluations/frozen_referee_match_v1_anchor.json`, `..._v2huelle_generator.json`, `models/frozen_champions/v21_2d_brierbest/golden_probe.json` (Fund 2026-08-27 per breitem Privacy-Grep; bereits gepusht, kein Nutzername enthalten) | klein   | oeffentliches Repo. Gehoert in die Kapselungs-Spur: bei der golden_probe.json im EINGEFRORENEN Artefakt vorher klaeren, ob verify-Tooling sie hasht (Praezedenz: golden_probe-Manifest-Sanierung 25a632f)                                                                                                                                                                                                                                            |
| Serielle Referenz fuer den vollen Cache                                                                                                                                                                                                                                                                      | 2,58 h  | bevor der Cache eine Champion-Entscheidung traegt                                                                                                                                                                                                                                                                                                                                                                                                    |
| Traeger-Manifest-Generator                                                                                                                                                                                                                                                                                   | klein   | `PREREG_v23_window.md` verlangt 1.800 von 17.450 hv2-Partien policy-aktiv; es gibt nur Leser, kein Werkzeug. Regel ist dokumentiert (Seed + zeitlich gestreute Auswahl)                                                                                                                                                                                                                                                                              |
| ~~Split-Test Routing gegen Drafting~~ ERLEDIGT 2026-08-26                                                                                                                                                                                                                                                    | 3x 22 s | `PREREG_v22_window.md` par.4f: **Drafting 0,756, Routing allein 0,000** -- par.4c hatte das Gegenteil vorhergesagt                                                                                                                                                                                                                                                                                                                                   |
| Gewichtsfenster der Huelle                                                                                                                                                                                                                                                                                   | Messung | `PREREG_heuristic_v2_long_rows.md` par.3b.1 -- existiert ein `w`, das kleine Punktunterschiede ueberstimmt, aber nie Strafpunkte akzeptiert? **Klarstellung 2026-08-27: dieses `w` ist das ROUTING-Gewicht der Huelle auf den Ownership-Marginalen im Tiling-Loeser (die Verbraucherseite), NICHT das Trainings-Loss-Gewicht `OWNERSHIP_WEIGHT` / `--ownership-weight` aus par.3b und par.3b.2. Zwei verschiedene `w`, zwei verschiedene Messungen** |
| Blindzieh-Stopp-Regel gegenpruefen                                                                                                                                                                                                                                                                           | Arena   | `PREREG_stack_draw_reservation_rule.md` par.5b sagt "zieht zu oft, ~10 Punkte je betroffenem Stapelzug". Knopf `MOSAIC_STACK_DRAW_RESERVATION` ist gebaut, Default AUS. Seit der Kapselung billig: der Anker liegt als Artefakt vor                                                                                                                                                                                                                  |
| Kontrollfluss im NETZ-Self-Play                                                                                                                                                                                                                                                                              | Arena   | `MOSAIC_STACK_DRAW_RESEARCH=1`. Beruehrt nur die NETZ-Seite -- aendert den SPIELER, nicht den MASSSTAB                                                                                                                                                                                                                                                                                                                                               |

---

## NAECHSTE SCHRITTE (Stand 2026-08-26, nach Prioritaet)

### BERICHTIGT: kein OneDrive-Verlust, der Nutzer raeumte auf (2026-08-28)

Die "verschwundenen" Dateien in models/ waren beabsichtigtes Aufraeumen des
Nutzers -- meine Fehldiagnose (und die ONNX-Wiederherstellung) kam ihm
zuvor. Aufgeloest: die 29 Alt-Trainingsmanifeste sind jetzt ordentlich per
git rm entfernt (`fc92b97`). ENTSCHIEDEN (Nutzer): die Champion-`.pth`
liegt jetzt als `model.pth` IM frozen-Artefakt, UNVERSIONIERT (globale
*.pth-Ignore-Regel greift; Schutz = Backup-Ordner, Praezedenz venv/). Die
ONNX bleibt getrackt (Byte-Beweisstueck; Re-Export aus .pth ist nicht
byte-stabil). Kuenftige Einfrierungen legen die .pth mit ab
(freeze-Werkzeug-Nachzug auf der 1e-Merkliste). WEITER OFFEN:
champion.txt und 9 Suite-Tests laden aus models/ -- soll models/ leer
werden, muessen sie auf den Artefakt-Pfad umziehen (Build-Fenster).

### UMBENENNUNG hv1/hv2: GEBAUT, Wheel-Neubau ausstehend

Alles traegt die neue Nomenklatur (`f5c60da`, Dialekt-Uebersetzung fuer die
gefrorenen Wheels via tools/frozen_name_dialect.py). **Bis zum Wheel-Neubau
ist der Live-Pfad gesperrt** (installiertes Wheel kennt nur "v1", Specs
sagen "hv1"). Naechstes Fenster: maturin + Paritaets-Hash + Suite gruen +
Golden-Selbsttests beider Artefakte + frozen_agent_referee_probe
(Erwartungen [27,15]/159 und [63,27]/163 muessen unveraendert treffen).

### KAMPAGNEN-ZIEL (Nutzer 2026-08-28, nach dem b01-Peek)

**"Ich will schlussendlich einen sauberen Netz-Generator, der auf Spalten
spielt."** Das ist das Erfolgskriterium dieser Kampagne -- nicht, ob v22
v21 schlaegt (Gating laeuft informativ). Jeder der vorbereiteten Wege wird
daran gemessen, ob er das Netz dem Spaltenspiel naeher bringt:

| Weg | Stand | prueft/hebt |
| --- | --- | --- |
| Orakel-Treue-Diagnose (prior_mass/tau gegen den Lehrer) | Werkzeug vorhanden | WO der Verlust sitzt: Draft-Erbe oder Tiling |
| Surprise-Weighting (waere v22-b03) | Entwurf registriert | Draft-Erbe schaerfen, falls Treue niedrig |
| `MOSAIC_OWNERSHIP_TILING_W` mit b01-Kopf | Knopf gebaut, nie richtig bedingt gefahren | Tiling-ABSICHT zur Spielzeit |
| Stufe 2: 2D-Ablesung des Ownership-Kopfs | registriert (par.3b Stufenplan) | Kopf-Geometrie statt flacher Projektion |
| Vollendungs-Filter in der Suche | Wecker-Liste v23 | den Vollendungs-Engpass direkt |
| Arm K / Arm L (Label-Qualitaet) | Entwurf/Reserve | Value-Ziel-Hygiene |

b01-Peek als Anlass: 0,275 volle Spalten (2,5x Champion, weit unter
Lehrer 0,73; lastkontaminiert, n=20) -- Bau bis >=4 da (1,52), Vollendung
fehlt.

### A0. SCHLACHTPLAN v22 -> v23 (Nutzer-Auftrag 2026-08-27) und Nachtstand

Der Plan der Nacht 2026-08-27/28, mit Ist-Stand je Schritt -- damit eine
naechste Sitzung mitten im Ablauf uebernehmen kann:

| #   | Schritt                                                                                                                                                                                                                                                                                                                                 | Stand                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0   | Phase 0: Doku-Audit, 13 Preregs + STATUS berichtigt                                                                                                                                                                                                                                                                                     | ERLEDIGT (`936fc40`)                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 1a  | Spezialfeld-Kanaele 77->79 (additiv, Paritaets-Hash haelt)                                                                                                                                                                                                                                                                              | ERLEDIGT (`e91cd34`)                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 1b  | Entstauchung -> Alt-Mechanik, nativ als Default (Blockliste)                                                                                                                                                                                                                                                                            | ERLEDIGT (`4a775e1`)                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 1c  | train.py-Hygiene: --lr-t-max, Val-Pool-Waechter, Traeger-Flag im Manifest                                                                                                                                                                                                                                                               | ERLEDIGT (`dc40551`); Manifest-Felder am ersten echten Lauf gegenpruefen                                                                                                                                                                                                                                                                                                                                                                                      |
| 1d  | Stufe-0-Sonde (par.3b.3): Daempfungs-Verdikt                                                                                                                                                                                                                                                                                            | ERLEDIGT: NICHT bestaetigt (oberster Bin -0,015 gg. +0,05); Arm L bleibt Reserve, TD_LAMBDA 0,5. Beifang: v21-Bootstrap global ~5-7 pp zu optimistisch                                                                                                                                                                                                                                                                                                        |
| 2a | 79er-Cache parallel auf nativ-Kodierung | ERLEDIGT 2026-08-28 (37,7 min, data/.par_full_79.h5, 916 MB) |
| 2b | Serielle Referenz + Bit-Vergleich = Cache-Tor | ERLEDIGT 2026-08-28: GRUEN, 21/21 Felder ueber 4,19 Mio Zustaende bit-identisch (cache_parity_full_79.json, 98 s). Ein Windows-Update-Reboot um 03:00 kostete einen Anlauf |
| 2c  | Cache-Verdrahtung in train.py                                                                                                                                                                                                                                                                                                           | GEBAUT (`--cache-file` + harter Schluessel-Waechter, Stempel in beiden Bau-Werkzeugen, tools/stamp_cache_key.py; Ladelauf UNGETESTET). BEFUND: der Voll-Cache passt per Design nicht auf Laeufe mit Val-Split (anderer Fenster-Schluessel, Waechter lehnt korrekt ab) -- v22-b01/b02 fahren den klassischen In-Train-Bau (~2,3 h, einmal; b02 trifft denselben Schluessel). --cache-file nutzt, wer --val-frac 0 faehrt oder ein exakt passendes Fenster baut |
| 3 | v22-KALTSTART b01/b02 | ERLEDIGT 2026-08-28: b01 E17 (best E7, brierbest E1, Own-Val 0,394), b02 E16 (best E6, brierbest E1); Cache-Treffer sparte b02 den Datenaufbau (31,5 s). Endgame-Loss 0,0000 trotz Flag -- Ziel fehlt im hv2-Korpus, offener Pruefpunkt |
| 4 | Spalten-Tor + par.3b.4 + par.3b.5 | ERLEDIGT 2026-08-28: Tor 1(b) BESTANDEN (b01 0,297 gg. Champion 0,102, t 5,55), Tor 1(a) VERFEHLT (gg. w0 +0,037, t 1,53) => KEIN v22-Self-Play nach Regel. Symmetrie TRENNT (+0,573, t 93). Treue LESART 3: Draft-Erbe da (Masse 0,81->0,60, Lift 28x), die PLATZIERUNG verschenkt es. Alles in der Lehrer-Prereg registriert |
| 5 | Wecker-Liste vor dem v22-Self-Play | AUSGESETZT -- Start per Tor-Regel gestoppt. NEUER NAECHSTER SCHRITT: Ownership-Pol-Konsument-Arena (MOSAIC_OWNERSHIP_TILING_W-Sweep mit b01-Kopf, argmax-Instrument; par.3b.5 Weg-Wahl). Traegt er, kommen Start und Weckerliste zurueck |

**Offene NUTZER-Entscheide, nachts nicht angefasst:** (a) Anker-Artefakt
neu einfrieren oder Cross-Aera messen (Vertragshash `efd564d8...`;
Empfehlung: neu einfrieren, Beweisfuehrung = Golden-Probe-Bytevergleich
als Traeger, A4-Fixture als Beigabe), (b) Sanierung der drei gepushten
JSONs mit Pfadfragmenten (Tabelle in Abschnitt 2), (c) jeder Push.

### A. Der Leitstern-Pfad -- das Einzige, was den Spieler staerker macht

**Das v22-Training steht weiterhin aus.** Alles an diesem Tag war
Infrastruktur; kein Zug ist dadurch besser geworden. Konfiguration
unveraendert (Herleitung: Archiv-Kapitel 2026-08-25 bis 2026-08-28,
Abschnitt 1): `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` PLUS
`--ownership-weight 1.0` (w1-Arm), dazu der **w0-Kontrollarm auf demselben
Korpus**. **KALTSTART** (Nutzer 2026-08-27), bei Bedarf Afterburner;
`MOSAIC_VAL_POOL` nur im Afterburner-Fall. Gating gegen Anker und v21 laeuft
als Standard-Messung, entscheidet aber nicht den Self-Play-Start.

Vorbereitet ist dafuer inzwischen das Meiste: der Korpus ist reproduzierbar
(Archiv-Kapitel, Abschnitt 1c), sein Erzeuger eingefroren (Abschnitt 1d), und
der Cache laesst sich waehrend der Erzeugung mitbauen (Abschnitt 1b).

**Einschraenkung, ergaenzt 2026-08-27 -- "alles" war zu viel:**

* **Der parallele Cache-Bau ist NICHT in `train.py` verdrahtet.** Er ist ein
  eigenstaendiges Werkzeug; `train.py` kennt keinen Cache-Pfad-Parameter und
  baut weiter SERIELL. Wer das Training einfach startet, zahlt also rund
  2,6 h Vorlauf statt der 36,1 min -- die 36,1 min bekommt nur, wer den Cache
  vorher mit dem Werkzeug baut. Das ist Absicht
  (`PREREG_cache_build_time.md` par.7/par.9: "Nicht verdrahtet ... bis es auf
  dem vollen Korpus gelaufen ist"), aber es ist kein erledigter Punkt.
* **Die serielle Referenz fuer den vollen Cache fehlt** (2,58 h). Belegt ist
  Bit-Identitaet auf 120 Dateien, nicht auf den 4,19 Mio Zustaenden. Solange
  sie fehlt, traegt der volle Cache keine Champion-Entscheidung.

**Spalten-Abnahme-Tor (par.3b.2 der Lehrer-Prereg, registriert 2026-08-27).**
Zwischen Training und Self-Play-Start steht ein vorregistriertes Tor mit zwei
harten Bedingungen: volle Spalten je Partie im w1-Arm signifikant ueber dem
w0-Arm UND ueber der neu gemessenen Champion-Referenz, dazu Vollendungsquote
signifikant ueber 0,53 bei Punktschaetzung mindestens 0,60. Tor 1 verfehlt =
kein Self-Play-Start. Herleitung, Instrument und Folgewege stehen in der
Prereg, nicht hier.

### C. Billig und offen

| Punkt                                   | Kosten  | Warum jetzt billiger als frueher                                                                                                                            |
| --------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Blindzieh-Stopp-Regel gegenpruefen      | Arena   | Vorhersage quantifiziert (~10 Pkt je Stapelzug), Knopf gebaut, Anker als Artefakt geschuetzt                                                                |
| Kontrollfluss im Netz-Self-Play         | Arena   | beruehrt nur die NETZ-Seite -- Spieler, nicht Massstab                                                                                                      |
| Traeger-Manifest-Generator              | klein   | `PREREG_v23_window.md` braucht ihn; Regel ist dokumentiert                                                                                                  |
| Gewichtsfenster der Huelle              | Messung | `PREREG_heuristic_v2_long_rows.md` par.3b.1 -- das ROUTING-Gewicht im Tiling-Loeser, NICHT `OWNERSHIP_WEIGHT` aus par.3b/par.3b.2 (Klarstellung 2026-08-27) |
| Serielle Referenz fuer den vollen Cache | 2,58 h  | bevor der Cache eine Champion-Entscheidung traegt                                                                                                           |

### C2. Wheels leben ab jetzt IM Artefakt (Nutzer-Entscheid 2026-08-26)

`models/frozen_wheels/` ist **entfernt**. Der Ordner war das Nebenprodukt
EINER Nacht: der Kernbeweis (par.8f) war sechs Diagnoserunden rot, und jede
brauchte ein installierbares Wheel -- zehn Stueck zwischen 23.08. 17:50 und
24.08. 02:29, von denen genau EINES gefahren wird.

Das gefahrene (`mosaic_rust_wave3g_20260824.whl`) liegt jetzt im
v21-Artefakt. Vorher trug das Artefakt nur die Provenienz-Kopie
(`searchconfig_wave1`) und NICHT das Wheel, das seine venv ausfuehrt -- ginge
der Ordner verloren, waere die venv nicht wiederherstellbar gewesen. Belegt
statt angenommen: der sha256 der kopierten Datei entspricht dem in
`venv/.../direct_url.json`.

**Regel ab jetzt: ein Wheel liegt im Artefakt, das es ausfuehrt** --
`frozen_heuristics/<name>/` oder `frozen_champions/<name>/`. Kein
Sammelordner, in dem Sackgassen und Gefahrenes nebeneinander liegen.

Gegenprobe nach dem Loeschen: Referee-Lauf gruen, und v21s venv meldet
weiterhin `contract_hash a169ebf0a4451e08` gegen `a3f61f246d9bbf5c` des
aktuellen Builds -- zwei Engine-Versionen nebeneinander, genau wofuer die
Kapselung gebaut wurde.

### D. Was NICHT ansteht

* **v2 weiterentwickeln.** Nutzer-Entscheid 2026-08-26: "v2 ist durch". Es ist
  eingefroren, weil es fertig ist.
* **Artefakt gegen Artefakt ausbauen.** Es laeuft (par.10a); ein Messlauf
  braucht nur die Parallelisierung aus B.1.

---

## STAPELZUG: Korpus und Netz-Self-Play loesen ihn VERSCHIEDEN auf (2026-08-26)

Beim Nachgehen der Anker-Frage (par.10b) aufgefallen, am Code geprueft:

| Pfad                                                | `apply_via_chosen_action`      | Stapelzug                                         |
| --------------------------------------------------- | ------------------------------ | ------------------------------------------------- |
| `play_heuristic_self_play_game` (self_play.rs:2255) | `false`                        | nur der Peek, Slot/Rotation werden **gesucht**    |
| `play_net_self_play_game` (:3879/:3886)             | **beide `true`**               | **sammelaufgeloest**, `best_eval_for_tile` waehlt |
| `play_net_game_variante` (Arena)                    | Netz `true`, Heuristik `false` | gemischt                                          |
| `play_net_vs_net_game` (Gating)                     | beide `true`                   | sammelaufgeloest                                  |

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
Self-Play", und das war zweimal nicht erfolgt. **Sie ist seit v22 fuer den
HEURISTIK-Korpus erfuellt -- ohne dass der Knopf je gesetzt wurde**
(dort par.13, gemessen 2026-08-26; Einschraenkung praezisiert 2026-08-27, sie
gilt NICHT fuer das kommende v22-Self-Play, s. uebernaechster Absatz): der
Erzeuger ist auf die Heuristik gewechselt, die ohnehin per Entscheidung
aufloest. Im Korpus stehen `choose_draw_stack_slot` in 2,5 Prozent der
Datensaetze (gegen "0 von 16.322" im Bestandskorpus) und tragen dabei zu
**100 Prozent** ein gueltiges Policy-Ziel.

**NICHT angefasst.** Die reparierte Abbruchregel liegt bereits als Knopf
daneben (`MOSAIC_STACK_DRAW_RESERVATION`,
`PREREG_stack_draw_reservation_rule.md` par.5b, Default AUS). Offen bleibt der
Kontrollfluss im NETZ-Self-Play -- eine Arena-Frage.

**Und genau da liegt die Grenze der Erfuellung (praezisiert 2026-08-27):** das
NETZ-Self-Play loest Stapelzuege weiter GESAMMELT auf
(`play_net_self_play_game`, self_play.rs:3879/3886, beide
`apply_via_chosen_action = true`). Der naechste Erzeugerlauf ist aber genau
ein Netz-Self-Play -- das des v22-Champions, das das v23-Fenster fuellt. Fuer
IHN ist Regel 4 unerfuellt, und der Wecker auf der Liste in
`PREREG_v23_window.md` par.4 bleibt scharf. Erfuellt ist die Regel allein fuer
den heuristisch erzeugten hv2-Korpus.

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

**Vorbereitung, fuenf Punkte (Nutzer-Entscheid 2026-08-25): ERLEDIGT
2026-08-25 -- Herleitung in `../archive/history.md` (Kapitel 2026-08-25 bis
2026-08-28).** Abgehakt sind: Blindzieh-Reparatur entschieden (kein
Staerkegewinn, Knopf AUS), Heuristik-Variante bis in den AUFZEICHNENDEN
Self-Play-Pfad durchgereicht, Arena-Threadzahl auf EINE Konvention gezogen,
Bootstrap-Horizont 3 verworfen (v22 faehrt Horizont 2), Erzeugung mit dem
heutigen Wheel.

### 4. JSON-Umzug: Restentscheid

Die Artefakte liegen jetzt in `evaluations/artifacts/` und sind **ungetrackt**
(`.gitignore`). Folge: ein frischer Klon hat die Messartefakte nicht, und
Preregs zitieren sie als Beleg. Bei deterministischen Sonden ist ein Lauf
wiederholbar (belegt: der Wiederholungslauf des Strafleisten-Tors war
byte-identisch), bei allem mit Netz-Zufall nicht ohne Weiteres.
Zurueckdrehen: `.gitignore`-Zeile entfernen und
`git add -f evaluations/artifacts`.

### 5. Weitere offene Straenge

| Strang                                     | Datei                                                           | Zuschnitt                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Shaping-Kopf statt Ownership-Kopf**      | `PREREG_heuristic_v2_long_rows.md` par.3b                       | Vorregistriert, nicht gebaut. Sagt die Dreiecks-Abweichung voraus; zwei Kanaele, Abkling-Kurve. Braucht erst das v22-Korpus                                                                                                                                                                                                                                                                                   |
| **Einhuellende im 2D-Encoder**             | –                                                               | Nutzer-Frage 2026-08-24, nicht registriert. Zusaetzliche Eingabeebene "Dreiecks-Zugehoerigkeit je Zelle"; additiv moeglich, aber nach par.3b                                                                                                                                                                                                                                                                  |
| **R5-Netz-Loeser + R5-Value-Kalibrierung** | `PREREG_r5_solver_split.md` par.2, Teil B                       | Netz-Loeser-Arme und Vierer-Kopf-Vergleich. Zielmetrik `r5_value_calibration`-Steigung, und die ist GETRENNT zu lesen (praezisiert 2026-08-27, par.3e verlangt das): **Platten-Steigung 0,06-0,09**, **Gesamtwert-Steigung 0,87-0,89** -- der Kopf ist auf der Gesamtskala fast richtig geeicht und sieht nur den Platten-/Spaltenanteil nicht. Arm 3 braucht ein b-Serie-Modell mit gepruefter Traegerschaft |
| **Seeding-Folgearm: Dosis**                | `PREREG_start_position_seeding.md`                              | k=6 war die erste Dosis; hoehere Dosis naheliegend, nicht registriert                                                                                                                                                                                                                                                                                                                                         |
| **UVFA-Regime-Eingabe**                    | `PREREG_uvfa_plate_regime.md`                                   | par.8: Conditioning-Dropout und Leakage-Waechter sind PFLICHT. par.7-Entscheid steht aus                                                                                                                                                                                                                                                                                                                      |
| **Saettigende Score-Utility**              | `PREREG_saturating_score_utility.md`                            | Tor gefahren, Verdikt DAZWISCHEN -- **Nutzer-Entscheid offen**: sigma-Kopf auf `points_val` oder auf ein TD-unberuehrtes Ziel                                                                                                                                                                                                                                                                                 |
| **Agenten-Kapselung: Ausbau**              | `PREREG_agent_encapsulation.md` par.4                           | Entschieden und gruen; offen nur der planbare Ausbau der restlichen ~31 Knoepfe ins SearchConfig, je Knopf ein Commit mit Paritaets-Gate                                                                                                                                                                                                                                                                      |
| **#29-Instrument**                         | `PREREG_post34_package.md`                                      | WARTET AUF POWER: braucht mindestens 6 arena-entschiedene Paare (Stand ~3)                                                                                                                                                                                                                                                                                                                                    |
| **Rundenuebergang bemustern**              | `PREREG_round_transition_search_sampling.md`                    | Nichts gemessen. Zusatz aus der externen Recherche: robuste Aggregatoren (Median, gestutztes/winsorisiertes Mittel) statt des arithmetischen                                                                                                                                                                                                                                                                  |
| **Risikosensitive Blatt-Utility**          | `PREREG_risk_sensitive_leaf_utility.md`                         | Nichts gemessen; `points_dist` ist abgeschaltet, der Champion traegt den Kopf nicht                                                                                                                                                                                                                                                                                                                           |
| **Blindziehung: Suche und Merkmale**       | `PREREG_chance_nodes.md` Teil B1, `PREREG_stack_top_feature.md` | Beide geparkt. B1 gibt der SUCHE die korrekte Peek-Bewertung, das Merkmal gibt dem NETZ die sichtbare Rueckseite                                                                                                                                                                                                                                                                                              |
| #31 / #38 / #39                            | –                                                               | geparkt, Arbeitskreis "Spaeter"; Beschreibungen im Archiv                                                                                                                                                                                                                                                                                                                                                     |
| **v22-Fenster**                            | `PREREG_v22_window.md`                                          | **NEU GEFASST 2026-08-25, ENTSCHIEDEN.** Der alte Rotations-Zuschnitt war fuer einen NETZ-Erzeuger gebaut und ist hinfaellig -- das v22-Fenster IST jetzt der v2-Lehrer-Korpus (24.000 Partien, eine Klasse, kein Altbestand). Frueher stand hier ausdruecklich "nicht zu verwechseln mit dem Lehrer-Korpus"; das gilt nicht mehr                                                                             |

**Geschlossen, nicht neu vorschlagen:** Q-Skalierungs-Option, jeder
Suchparadigmen-Wechsel (zwei externe Recherchen), Mehrfach-Determinisierung
(`PREREG_ismcts_determinizations.md`: k=4 faellt unter zwei Anordnungen
signifikant ab), Phasenfaktor, Vollendbarkeits-Relaxation im Routing und die
zwei Punktekarten (`PREREG_heuristic_v2_long_rows.md` par.11-16),
`PREREG_long_row_payoff.md` B1, `PREREG_bootstrap_horizon.md` (beide Arme).

---

## OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt                          | Stand                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| **v22 vorbereiten**            | Nutzer-Ansage 2026-08-25: "dafuer muessen wir noch was vorbereiten" -- was genau, ist offen |
| **Saettigende Score-Utility**  | Verdikt DAZWISCHEN, kein Automatismus vorgesehen                                            |
| **Stoerungs-Baustein Stufe 2** | gehoert zum Moon-Order-Kopf, keine Einzelentscheidung mehr                                  |
| **Push**                       | NIE ohne ausdrueckliche Anweisung; Stand wird als "n Commits voraus" gemeldet               |
| **Asym-Korpus**                | bleibt lokal, Trainingsinput fuer Seeding und UVFA                                          |
| **Fester Bewertungssatz**      | 300 Dateien / 3000 Partien in `data/holdout/`, fertig 2026-08-18                            |

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

## BENENNUNG DER GENERATIONEN

**Vollstaendig kanonisch in `../docs/generation_naming.md`** (Nutzer-Entscheid
2026-08-28: auch die konkrete Kette der laufenden Kampagne wird dort gefuehrt,
nicht mehr hier).

---

## LAUFZEITEN

**Kanonisch in `../docs/measured_runtimes.md`** (seit 2026-08-28 aus STATUS
entflochten) -- Planungsgroessen je Aufbau, samt Threads-Konvention und der
Pflegeregel "wer eine Zeile ergaenzt, traegt GEMESSENES ein". Die belastbaren
Zahlen stehen ohnehin je Lauf im Artefakt (`laufzeit`-Block, Pflichtfeld seit
2026-08-25).



---

## FALLEN (aus echten Vorfaellen)

**Kanonisch in `../docs/pitfalls.md`** (seit 2026-08-28 aus STATUS
entflochten): CPU-Nebenlast, "erste N je Datei" als stiller Rundenfilter,
stilles CRLF, totes Wheel, veraltete Prereg-Koepfe, Wheel-Neubau, Backticks in
doppelten Quotes -- dazu die 2026-08-26/27 dazugekommenen Faelle (fehlendes
Flag = Default, falsche Referenz, Feld-vorhanden-heisst-nicht-wirksam,
Verschiebung sieht wie Neubau aus, umgangenes Tor).

---

## GELTENDE REGELN

**Kanonisch in `../docs/working_rules.md`** (seit 2026-08-28 aus STATUS
entflochten): Messen und Auswerten (Block-Ebene, Aufloesung, Arena-Gating fuer
Value-Aenderungen, Sechs-Kennzahlen-Pflicht, Laufzeit ins Artefakt, keine
Pipes), Training und Korpus (Fenster-Pinning, Traeger-Status, Alt-Korpora,
Promotions-Checkliste, Eich-Verbot auf plattenblindes Spiel) und Arbeitsweise
(Loeschen, Push, Spurdisziplin, Prereg-Kopf, Anker-Paket, Elo-Betrugsschutz).
Regeln, die schon in `../CLAUDE.md` stehen, sind dort nur verwiesen, nicht
kopiert. Langform samt Herleitung weiterhin `../archive/history.md`, Kapitel
"Vollstaendiger STATUS-Stand vom 2026-08-25".

---

## ARCHITEKTUR (Referenz)

**Kanonisch in `../docs/architecture_reference.md`** (seit 2026-08-28 aus
STATUS entflochten): Such- und Engine-Seite, Netz- und Trainingsseite samt
aktiven Konstanten, sowie die "Konstanten mit Fallstrick". Pflegeregel: wer die
Architektur aendert, zieht die Datei im selben Zug nach und setzt ihr
Stand-Datum neu. **Beim Uebertrag berichtigt:** der STATUS-Stand nannte
`NUM_PLANES_CHANNELS = 77`, gebaut sind **79** (features.rs:813, geprueft
2026-08-28) -- Schritt 1a des Schlachtplans (`e91cd34`) war nicht nachgezogen.
