# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom
2026-08-31 (Nutzer-Auftrag); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom
2026-08-31 (vor der Neufassung)"** -- dort steht jede Herleitung, die hier
nur noch als Verweis vorkommt, inklusive der kompletten v22-Chronologie
(Faecher-Durchgang, Schlachtplan v22->v23, Nachtprogramme, abgeloeste
Tor-Fassungen).

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

**Zahlen ohne Datum stammen aus dem Stand vom 2026-08-30 und sind in dieser
Neufassung nicht neu nachgemessen worden.**

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern kanonisch in
`../docs/`: `generation_loop.md` (die Schleife und ihre Tore),
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`,
`pitfalls.md`, `measured_runtimes.md`, `architecture_reference.md`. Wer an
diesen Inhalten etwas aendert, aendert es DORT.

---

## 1. WAS GERADE LAEUFT (Stand 2026-08-31, abends)

| Ressource | Lauf | Was damit zu tun ist |
| --- | --- | --- |
| **GPU** | `v23-b03` -- b01-Rezept plus `--surprise-alpha 0.5` | Wenn fertig: Orakelmetriken gegen b01 (das IST der Kontrollarm, gleicher Seed/Val-Pool). Entscheidungsmass steht in `PREREG_policy_surprise_weighting.md` par.5 -- **nicht** val_combined, **nicht** policy_top3 |
| **CPU** | **frei** (seit 22:42) | Zuletzt: Anker-Kante fertig (22:39, Sitzung `mosaic-ai-7f`) plus Determinismus-Probe (22:42, diese Sitzung). Naechste Kandidaten: die 200 Cache-Bloecke des Relabel-Arms, oder Warm gegen Kalt (`b02_brierbest` gegen `b01_brierbest`) |

**WARNUNG Doppellauf (2026-08-31, 22:02:55 bis 22:26):** zwei Sitzungen haben denselben
Anker-Lauf gestartet -- byte-gleiche Argumente, gleicher `--seed-base 900001`, gleiche
Zieldatei. Der zweite (Sitzung `mosaic-ai-fc`) ist auf Nutzer-Anweisung gestoppt worden und
hat nichts geschrieben; der erste laeuft weiter. Fuer rund 23 Minuten lagen 2x10 Arena-Worker
plus 2x19 eingefrorene Anker-Worker auf 12 Kernen: der `laufzeit`-Block des ueberlebenden
Laufs ist als **unter Nebenlast gemessen** zu markieren. **Lehre fuer Abschnitt 1:** die
Zeile sagt, WAS zu tun ist, aber nicht, WER es schon tut -- wer einen Lauf startet, traegt
Startzeit und Sitzungsnamen hier ein, bevor er startet.

**AUFGELOEST (22:42):** drei Seeds aus dem Lastfenster (900021/22/23, Paritaeten
erhalten) exklusiv nachgespielt -- **byte-gleich bis auf den letzten Zug**, auch die
vollen Partie-Logs (325/332/314 Zeilen, Zeile fuer Zeile). Die Ergebnisse des Laufs
sind damit FREIGEGEBEN; nebenbei ist Parallel-gegen-Seriell am Anker-Instrument
bestaetigt (Lauf 10 Prozesse, Probe 1). Der `laufzeit`-Vorbehalt bleibt. Herleitung,
nicht gemessen: dass diese drei im Fenster lagen, folgt aus der gestreiften
Blockaufteilung -- Zeitstempel je Partie gibt es nicht. Vermerk:
`artifacts/anchor_arena_v23b01_load_contamination.md`.

**Erledigt seit der letzten Fassung:** die Checkpoint-Arena des Kaltstart-Arms
(`b02_best` 33:47 `b02_brierbest`, SPRT H0, p = 0,189) -- **Kandidat ist
`v23-b02_brierbest`**, obwohl aus Epoche 1. Registriert in
`PREREG_v23_window.md` par.2h und `PREREG_capacity_sim_frontier.md` par.11.

**Danach frei:** die GPU fuer den Relabel-Arm, die CPU fuer dessen 200
Cache-Bloecke. In der CPU-Warteschlange steht ausserdem die Arm-Frage selbst:
`b02_brierbest` gegen `b01_brierbest`, Warmstart gegen Kaltstart auf demselben
Fenster. Fuer die sechs Standard-Kennzahlen dann ueber
`tools/paired_arena_env_ab.py --model-b ... --log-games` (das Tor-2b-Instrument);
`paired_gating.py` hat KEIN Log-Flag (geprueft an seiner Argumentliste), es
liefert nur Punkte, Margin und Strafleiste.

---

## 2. WAS DIE GENERATION v23 ERGEBEN HAT

**Alle vier Tore bestanden -- das v24-Self-Play ist freigegeben**
(`docs/generation_loop.md` Schritt 9). Herleitungen in
`PREREG_v23_window.md` par.2b bis par.2g.

| Tor | Ergebnis |
| --- | --- |
| 0 Korpus traegt das Signal | Symmetrie-Trennung +0,4041 (t 41,26), 5.629 von 16.000 Seiten mit voller Spalte |
| 1 Siege gegen b05 | **119:61** aus zwei unabhaengigen Seeds (Champion-Strenge erfuellt) |
| 2a Spalten im Self-Play | 0,5150 gegen 0,3100, gepaart **+0,2050** (t 4,47) |
| 2b Spalten in der Arena | 0,6456 gegen 0,4304, gepaart **+0,2152** (t 2,61) |

| Elo-Kante | Ergebnis |
| --- | --- |
| gegen **v22-b05** | 119:61 -- signifikant |
| gegen **v21** (Champion) | 219:181, p = 0,084, KI [-0,013, +0,393] -- **nicht belegt besser**, Augenhoehe. **KEINE Promotion**, v21 bleibt Champion |
| gegen **hv1** (Anker) | laeuft |

**Phase 3 gemessen, NEGATIV (par.11 der R5-Kalibrierung):** die
Betrags-Daempfung ist unveraendert -- b01 0,0859 gegen b05 0,0886 auf
denselben 139 Paaren. Der Korpus heilt sie nicht. b01 wurde also deutlich
staerker und baut 66 Prozent mehr Spalten, OHNE dass der Bewerter repariert
wurde; der Punkte-Kopf trifft dieselbe Groesse mit 0,97. **Der Eingriff ist
damit faellig**, Erfolgstest "kippt die Sims-Kurve?".

**`v23-b02` (Kaltstart):** Early Stop nach Epoche 15/40, **4,22 h** gegen
b01s 5,97 h -- ein Kaltstart kostet mit stehendem Fenster-Cache WENIGER als
ein Warmstart. Sein brierbestes Modell liegt allerdings bei Epoche 1
(par.2g) -- die Checkpoint-Arena hat es trotzdem zum Kandidaten gemacht:
**33:47 fuer `_brierbest`** (SPRT H0, Vorzeichentest p = 0,189, gepaarte
Differenz -0,350 [-0,791, +0,091], Punkte 42,33 gegen 37,53). Nicht
signifikant, aber die vorab registrierte Regel laesst hier den Punktschaetzer
entscheiden (par.2h).

---

## 3. WAS ALS NAECHSTES ZU TUN IST

**Nutzer-Zuschnitt fuer diese Generation (2026-08-31):** relabelter Sockel,
b02, b03, Phase 3 -- dann v24. Nicht in diesem Zyklus: Kuppelplatten-
Verteilung, Arm K, b04-Breite, geometrisches Gelaender (alle registriert).

### 3.1 Relabel-Arm (Daten fertig, Fenster fertig)

Fenster `data/window_v23_relab.txt` und Manifest
`policy_carrier_manifest_v23_relab.json` liegen: dieselben 2.345 Dateien wie
b01, nur die 200 Policy-Dateien durch ihre lehrer-relabelten Kopien ersetzt
(204.008 Lehrerzuege, 0 Fehler). **Ein Faktor, dieselben Partien**, b01 ist
die Kontrolle.

Es fehlen die 200 Cache-Bloecke der Kopie, dann der Lauf:

```
PYTHONIOENCODING=utf-8 python -X utf8 -u tools/build_cache_incremental.py --data-dir data/relabeled_v23 --encoder 2d --value-target-variant nortv --workers 6
```

```
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v23_relab.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v22-b05'
python -u train.py --name v23-b05 --load v22-b05 --file-list data/window_v23_relab.txt --extra-data-dir data/relabeled_v23 --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828
```

**Vor dem Start pruefen:** der Val-Pool-Regex muss die relabelten Dateien
treffen (`^selfplay_v22-b05` deckt beide Praefixe), und die
Korpus-Zusammensetzung im Log muss 200 relabelte Traeger zeigen, nicht 200
rohe.

### 3.2 Phase 3, der Eingriff

Die Diagnose ist vollstaendig: Daempfung strukturell, Punkte-Kopf sauber,
Korpus heilt nicht. Der Eingriff selbst ist in
`PREREG_r5_value_calibration.md` zu registrieren, bevor er gebaut wird.

### 3.3 Dann v24

Generator ist der beste Stand von v23 (heute: b01). Verfahren:
`docs/generation_loop.md`. Der Korpus-Zuschnitt wird in einer eigenen
`PREREG_v24_window.md` registriert -- **mit `--per-file 10`**
(`docs/working_rules.md`).

### 3.4 Belegungsplan (GPU und CPU parallel)

Regel und Thread-Budget: `../docs/working_rules.md`, Abschnitt "Auslastung".
Ein Training belegt gemessen rund EINEN Kern, der CPU-Auftrag daneben darf
also rund 10 Threads nehmen. Zwei CPU-Messungen gegeneinander bleiben
verboten, und ein unter Nebenlast gefahrener `laufzeit`-Block wird als
solcher markiert.

---

## 3. STAND JETZT

**Champion:** `v21_2d_brierbest`, Elo **1226** [1188, 1269] auf der R5-Fix-Leiter
(Stand 2026-08-31, nach Eintragung der Anker- und der Champion-Kante von b01; der
fruehere Wert 1215 stammt aus dem Fit ohne diese beiden Zeilen). Kanten ueber die
Fix-Grenze nie mischen. **Staerkster Knoten der Leiter ist inzwischen NICHT der
Champion:** `v23-b01_brierbest` steht bei 1263 -- die KI ueberlappen, die
Promotionsregel haengt an der Champion-Kante, und die war nicht signifikant.

**Bester Stand der Spalten-Linie: `v23-b01_brierbest`** (seit 2026-08-31) --
volle Spalten 0,5150 am argmax-Instrument, 119:61 gegen den Vorgaenger b05,
gegen den Champion 219:181 (nicht signifikant). **Anker-Kante gefochten
(2026-08-31, 22:39): 127:23 aus 150 = 84,7 Prozent** gegen
`Heuristik_hv1_anchor`@150, Cross-Aera, Golden-Selbsttest gruen, Ergebnisse per
Determinismus-Probe freigegeben. **ES GIBT KEIN REMIS** (Nutzer-Hinweis, Regel an
`game.rs:586` geprueft: bei Gleichstand gewinnt, wer den Startspielerstein zuletzt
nahm): der Schiedsrichter meldete drei Partien faelschlich als Remis, alle drei gehen
an b01. `frozen_referee_match.py:380` liest den Tie-Break jetzt aus dem Zustand
(`first_player_next_round`), Gegenprobe auf denselben Seeds bestaetigt es. Die
Rust-Arenen waren nie betroffen. Kennzahlen je Seite: volle Spalten 0,953 gegen
0,027, Punkte 53,97 gegen 36,13, Margin +17,84, Strafpunkte -14,31 gegen -20,17.
Elo als HERLEITUNG: rund +297 ueber dem Anker (aus 84,7 Prozent), und rund +33 ueber
v21 aus der Champion-Kante. Beide Kanten sind seit dem 2026-08-31 in
`elo_history.csv` und die Anker-Kante zusaetzlich in `arena_trends.csv`. Zum
Vergleich, ueber zwei Instrumente hinweg (Paritaet 20/20 belegt): v21 kam am Anker
auf 116 von 150 (77,3 Prozent, Remis dort nicht ausgewiesen).

**EINGETRAGEN am 2026-08-31** in `elo_history.csv` und `arena_trends.csv`.
Beim Eintragen fiel auf, dass der Tracker auf den LITERALEN Namen `Heuristik`
verankerte, waehrend die Checkliste `Heuristik_hv1_anchor` vorschreibt -- die Kante
landete dadurch in einer eigenen, freien Komponente (b01 1148 / Anker 852, Summe
exakt 2000). BEHOBEN, siehe unten; Herleitung in `PREREG_agent_encapsulation.md`
par.13.

**Die Vorbedingung ist inzwischen GEMESSEN (2026-08-31, Nutzer-Vorgabe: nicht
gegeneinander spielen lassen, sondern Zug fuer Zug vergleichen).**
`tools/verify_frozen_heuristic.py` in beiden Modi, hv1-Rezept aus dem Manifest
(10 Partien, 600 Sims, Seed 20260826):

| Modus | Verdikt | verglichen | Wanduhr |
| --- | --- | --- | --- |
| Live-Wheel (Drift) | **GRUEN** | 1.763 Schritte, Feld fuer Feld, keine Abweichung | 22,2 s |
| Artefakt-Wheel (Konservierung) | **GRUEN** | dieselben 1.763 Schritte | 13,4 s |

Dazu die Referee-Paritaet neu gefahren (`anchor_referee_parity_20260831.json`):
20/20 identisch in beiden Modi, 0 Abweichungen. **Der lebende Code spielt hv1 also
Zug fuer Zug wie das Artefakt** -- die Engine-Aenderungen seit dem Einfrieren haben
den Anker nicht bewegt. Ab jetzt Pflicht nach jeder Engine-Aenderung, als Skill
`mosaic-anchor-invariance` abgelegt.

**Nutzer-Klarstellung dazu:** die In-Process-Heuristik ist eine
ENTWICKLUNGSUMGEBUNG, kein Vergleichswert. Der Fixpunkt gehoert an das Artefakt;
"der Anker ist gedriftet" ist keine moegliche Diagnose, ein rotes Ergebnis hiesse,
der lebende Code hat sich bewegt.

**GESETZT (Nutzer-Anweisung 2026-08-31): der Anker IST das Artefakt.**
`ANCHOR_NAME = "Heuristik_hv1_anchor"` in `tools/elo_tracker.py`, dazu
`ANCHOR_ALIASES = {"Heuristik": ...}` fuer die Zeilen vor der Umbenennung.
`Heuristik_v2huelle` bleibt ein eigener Spieler. Registriert in
`PREREG_agent_encapsulation.md` par.13, Ablauf als Skill
`mosaic-anchor-invariance`, Checkliste nachgezogen.

**Die Leiter danach** (`python tools/elo_tracker.py report`, 11 Zeilen, kein
einziger "NICHT verbunden"-Vermerk mehr; eingetragen sind seither auch die
beiden Tor-1-Gatings gegen b05):

| Modell | Elo | 95%-KI | Partien |
| --- | --- | --- | --- |
| **v23-b01_brierbest@400** | **1263** | [1223, 1311] | 730 |
| v21_2d_brierbest@400 | 1227 | [1191, 1269] | 1407 |
| v20_2d_opp_brierbest@400 | 1194 | [1158, 1235] | 950 |
| v19_2d_best@400 | 1142 | [1103, 1186] | 550 |
| Heuristik_v2huelle@150 | 1137 | [1086, 1190] | 407 |
| v22-b05@400 | 1136 | [1074, 1198] | 230 |
| Heuristik_hv1_anchor@150 | 1000 | fix | 600 |

**Beide Kanten sind drin (Nutzer-Anweisung 2026-08-31, "ist ja ein valides
match"): die Champion-Kante 219:181 gegen v21 ist als 9. Zeile eingetragen** --
informativ, kein Promotionsentscheid. Sie zieht b01 von 1297 (Anker-Kante allein)
auf 1266; mit den beiden b05-Kanten dazu steht er bei **1263** ueber 730 Partien.
Anker- und Champion-Kante implizierten einzeln 1297 und rund 1259, der gemeinsame
Fit legt sich dazwischen. Die KI von b01 [1223, 1311] und v21 [1191, 1269]
ueberlappen -- dieselbe Aussage wie die
Champion-Kante selbst: Augenhoehe, nicht belegt besser, keine Promotion.

**Was noch offen BLEIBT:** der Alias faltet die Anker-Kanten vom 2026-08-20 auf ein am 2026-08-26
   eingefrorenes Artefakt. Fuer diese sechs Tage liegt kein Wheel im Baum, die
   Zug-Gleichheit ist dort also NICHT geprueft. Einzige unbelegte Fuge der
   Leiter.

Vorgaenger `v22-b05`: Elo **1136** [1074, 1198] -- und das ist eine ANDERE Zahl als
die 1084, die hier bis zum 2026-08-31 stand. Grund ist nicht eine neue Partie,
sondern die Datenlage: b05 hing bis dahin an einer einzigen fruehgestoppten Kante
(16:34 gegen v21, n=50). Mit den beiden Tor-1-Gatings gegen b01 (52:28 und 67:33)
kommen 180 Partien dazu, das Intervall schrumpft von 228 auf 124 Punkte. Der
hv2-Lehrer liegt mit **1137** jetzt gleichauf statt 40 Punkte darueber.

**Wheel:** 79-Kanal-Build (`e91cd34`), Vertragshash `efd564d87bac2722`,
Paritaets-Hash `8c6684ff...` gemessen unveraendert.

**Was ueber den Value-Kopf gemessen ist:** relativ geheilt, im Betrag
gedaempft -- und die Daempfung ist auf v23-b01 unveraendert (0,0859 gegen
b05s 0,0886, par.11). Geschwister-Tau auf b05 **+0,338** (gegen -0,08/-0,19
der plattenblinden Netze), Mensch-Orakel-Differenz praktisch null. Kriterienweise aufgeloest ist die
Daempfung BREIT, nicht spaltenspezifisch (k1 mit 0,1747 am wenigsten
gedaempft). Daraus die Betrags-Schiene als Phase 3.

**Was ueber den Spaltenbau gemessen ist:** der Korpus wirkt (b01 baut 3x so
viele Spalten wie der Champion), das Ownership-TRAININGSGEWICHT nicht (w0
gleichauf, w2,0 signifikant darunter). Der Engpass ist die VOLLENDUNG spaet,
nicht der Plattenblick. Die Suchtiefe ist ein Regler zwischen Policy
(traegt das Spaltenwissen) und Value-Kopf: Plateau 25-100 Sims bei ~0,6
vollen Spalten gegen 0,34 ab 250 -- aber ein TAUSCH (@25 verliert 11:29,
@100 verliert 33:47 n.s.). Die Erklaerung dafuer ist OFFEN; die Deutung
"der Kopf sieht Spalten nicht" ist durch die kriterienweise Zerlegung
widerlegt.

**Erzeugungs-Knoepfe, gemessen entschieden:** implicit-Minimax alpha 0,0,
Stack-Draw-Kontrollfluss EIN, Bootstrap-Horizont 2, Seed-Positionen AUS
(Quelle plattenblind), Startkuppel Handheuristik, Vollendbarkeits-Filter AUS
(ungebaut). Vollstaendig in `PREREG_v23_window.md` par.4c.
---

## 4. OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Worum es geht |
| --- | --- |
| **b04: welcher Zweig wird breiter** | Flach-Zweig `hidden_size` 512 ist ohne Bau fahrbar; Conv-Zweig `conv_channels` 48 / `conv_layers` 2 braucht zwei Flags, ein Checkpoint-Feld und eine Ableitung beim Laden -- sonst ist der Checkpoint nicht ladbar (`PREREG_capacity_sim_frontier.md` par.10) |
| **Loeschfreigaben** | `data/onpolicy_v22-b06/` (31 Dateien) und -- falls keine DAgger-Runde 3 -- `data/onpolicy_v22-b05/` (30) |
| **Messartefakte tracked?** | `evaluations/artifacts/` ist ungetrackt; Preregs zitieren die JSONs als Beleg, ein frischer Klon hat sie nicht. Zurueckdrehen: `.gitignore`-Zeile raus, `git add -f` |
| **Push** | NIE ohne ausdrueckliche Anweisung; der Ahead-Stand wird im CHAT gemeldet, nicht hier gefuehrt |

---

## 5. OFFENE STRAENGE -- abgeglichen mit dem Prereg-Index (2026-08-31)

Der Index zaehlt **22 OFFEN, 71 ENTSCHIEDEN, 8 UEBERHOLT**. Beim Abgleich
sind zwei Koepfe berichtigt worden, die gegen ihren eigenen Stand standen:
`cache_build_time` sagte "nicht in train.py verdrahtet" (`--cache-file`
existiert seit `dc40551`, train.py:2554), und `v23_reachability_recheck`
sagte "v22-Self-Play per Tor-Regel gestoppt" (es laeuft seit dem 2026-08-30).

**Am laufenden Strang, mit Platz im Fahrplan:**

| Prereg | Wo es haengt |
| --- | --- |
| `v23_window` | Fensterbau -- Abschnitt 2.2 |
| `capacity_sim_frontier` | b02/b04 -- Abschnitt 2.3 |
| `policy_surprise_weighting` | b03 -- ungebaut |
| `reanalyze_label_depth` | Relabel-Etappe: Policy per hv2-Lehrer, Value tief -- Abschnitt 2.2 |
| `r5_solver_split` | Teil B = R5-Value-Kalibrierung, Phase 3 |
| `v23_reachability_recheck` | Stufe 0 NACH dem v23-Training |
| `search_depth_column_optimum` | weitgehend beantwortet; offen bleibt die ERKLAERUNG (optionale Stufe 4) |
| `special_tile_yield` | Kanaele 77/78 gebaut, ihre Wirkung nie isoliert |
| `cache_build_time` | Hebel (3) offen; serielle Vollreferenz fehlt |
| `geometric_envelope` | Gelaender fuer die fruehen Runden -- Stufe 0 ist netzfrei und kann VOR dem v23-Training laufen |

**Registriert, nicht eingetaktet** (jeder Bau braucht vorher eine
Registrierung): `plate_policy_supervision`, `saturating_score_utility`,
`risk_sensitive_leaf_utility`, `uvfa_plate_regime`,
`uncertainty_guided_selfplay`, `start_position_seeding` (Dosis-Folgearm),
`start_dome_choice` (Stufe 0, Wiedervorlage Generation 2),
`round_transition_search_sampling` (Kostentor zuerst),
`stack_draw_reservation_rule` (Default AUS steht),
`stack_top_feature`, `chance_nodes` (Teil B1/A1 geparkt),
`floor_shaping_scale`, `rust_data_layer` (Registrierung, kein Auftrag).

**OHNE PREREG, nur Merkposten -- und darum beim Index-Abgleich durchgefallen
(berichtigt 2026-08-31):** die Neufassung hat Abschnitt 5 aus dem
Prereg-Index gebaut, und damit faellt per Konstruktion alles heraus, was
offen ist, aber keine Prereg hat. Wieder aufgenommen:

* **Einhuellende / geometrisches Gelaender: seit 2026-08-31 REGISTRIERT**
  als `PREREG_geometric_envelope.md` (Nutzer-Auftrag) -- damit ist der
  Merkposten von 2026-08-24 abgeloest. Steht in Abschnitt 5 oben bei den
  Straengen am laufenden Fahrplan.
* **#31 / #38 / #39**: geparkt, Arbeitskreis "Spaeter", Beschreibungen im
  Archiv.

Wer Abschnitt 5 kuenftig aus dem Index erzeugt, traegt diese Liste HIER
nach -- der Index kennt nur, was eine Datei hat.

**Verschoben, nicht verworfen:** Arm K (Bootstrap-Kohaerenz,
`PREREG_heuristic_v2_long_rows.md` par.3b.3/3b.3a) -- gebaut, Default aus,
ausloeserbasiert. Er korrigiert einen VERSATZ, das gemessene Problem ist eine
STEIGUNG; seine drei benannten Nutzniesser sind ungebaut; und er ist der
einzige Arm, der alle Cache-Bloecke entwertet.

---

## 6. MERKLISTE CODEPFLEGE (Audit 2026-08-27, bewusst verschoben)

**Naechstes Build-Fenster** (brauchen cargo, Paritaets-Gate): sechs Dialekte
fuer "ist dieser Bool-Knopf an?" (Befund 4); drei stille Env-Verschlucker
(13-15); Value-Spread-Pfad verkleinert den Pool still (16); toter Zweitpfad
`board.rs:184-220` mit irrefuehrenden Spaltennamen (19).

**Nach dem v23-Training:** ONNX-Paritaetspruefung nie fertiggebaut (18);
Kanalzahl als Hand-Literal im Fenster-Key (5, NICHT vor dem Training);
viermal dasselbe 95%-KI mit Entartungen (20); sieben Eigenaufloesungen von
`champion.txt`, sechs Tool-Stellen offen plus `dist/mosaic_release.spec:46`
packt eine geloeschte ONNX (21); `MosaicDataset.__init__` mit 998 Zeilen
(22); `offline_diagnosis.py` rechnet ein historisches Value-Ziel (6).

Fundstellen im Audit-Bericht; Details im Archiv-Kapitel.

---

## 7. STRUKTURBEFUNDE, die weitergelten

- **Der Champion vollendet keine Spalten**, und der Grund ist Verteilung,
  nicht Versorgung: eine volle Spalte kostet 21 Zellen, das Netz verbraucht
  42,7 und truege gleichverteilt 2,03 Spalten statt 0,10.
- **Die Dreiecksform ist die MACHBARKEITSHUELLE**, keine aesthetische Wahl:
  erlaubt ist `r + c <= 5`, also dieselben 21 Zellen.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich** -- sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je Runde
  ab. Spalten haben das Problem nicht.
- **Der Durchbruch kam vom DRAFTING, nicht vom Routing** (Split-Test, je 160
  gepaarte Partien): Huelle nur im Drafting 0,756 gegen 0,044 (t 10,29),
  Huelle nur im Routing 0,113 gegen 0,113. Die Luecke zur Summe ist eine
  Wechselwirkung -- das Routing kann nur einsortieren, was das Drafting geholt
  hat.
- **Erste unkontaminierte Referenz:** Mensch-gegen-Netz in `static/log/` --
  der Mensch schliesst 1,80 volle Spalten je Partie gegen 0,10 des Netzes,
  bei GLEICHEN Platzierungspunkten. Der Vorsprung sitzt bei den
  Spezialfliesen; der Mensch tauscht kurze Reihen gegen lange.
- **Chip-Allokation, nicht Chip-Volumen:** Mensch 0,8 Reihe-6-Chip-
  Abschluesse je Partie, v21 0,1. Kosten-gewichtete Huelle Mensch 0,84,
  Maschinen 0,54-0,62.
- **Blindzieh-Regel:** bei Wertungsplatte 6 laeuft die gebaute Stopp-Regel das
  Punktekonto leer (58-66 Prozent der Serien enden bei 0). Spaltenbau behebt
  das NICHT -- k1 zahlt quadratisch, das Spezialfeld-Defizit kostet linear -3
  je Feld.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch.
