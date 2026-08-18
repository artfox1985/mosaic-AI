# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Abgeschlossenes liegt in
**`../archive/history.md`**.

---

## DAS ZIEL (Leitstern — Nutzer-Auftrag 2026-08-17: bei jeder Priorisierung im Kopf behalten)

> *"das netz spielt die basis an sich schon gut, aber nimmt keine ruecksicht auf
> die wertungsplatten. das wollen wir via injektion -> selfplay -> ownership
> head in den griff bekommen. dann sind nochmal je partie 10 punkte und mehr
> drinnen"*

1. **Ziel: ein staerkerer Spieler**, gemessen am **direkten Duell** gegen den
   Champion. Zielgroesse: **"Sieg mit vielen Punkten"** — nicht Punkte allein.
2. **Hebel: der Plattenblick.** Die Grundmechanik spielt das Netz kompetent und
   laesst 10+ Punkte je Partie liegen.

**Klausel, die schon sechs Vorschlaege aussortiert hat:** ein Plattenzuwachs,
der Siege kostet, ist KEIN Erfolg. Ein Zuwachs bei den Zaehl-Kriterien (k3/k4)
zaehlt nicht — gefragt sind die konjunktiven k1/k2/k5.

**Vor jeder Arbeit fragen: was traegt das dazu bei?** Ownership-Kopf, Korpus,
Regler, Konjunktionsterme, LR-Schedules, Traeger-Manifeste sind WERKZEUG ohne
Eigenwert. Am 2026-08-17 wurde ein Legacy-Test gestrichen, weil die Antwort auf
diese Frage "nichts" war.

---

## FOKUS-REGEL: NUR k1 (Nutzer-Entscheid 2026-08-18)

> *"mir kommt vor du switcht wild zwischen den wertungsplatten analysen herum.
> wir sollten uns wirklich mal nur auf eine wertungsplatte fokussieren"*

**Bis auf Widerruf wird ausschliesslich k1 (Vertikale Reihen, 7 Pkt je volle
Spalte) bearbeitet.** Warum k1 und nicht eine andere — alles gemessen:

| | |
|---|---|
| Wert | 7 Punkte je Spalte, 6 Geometrien |
| Kosten | **keine** — innerhalb des k1-Bauer-Arms +7,86 Gesamtpunkte, davon 7,02 aus der Platte, Rest +0,84 |
| Synergie | Platzierung zahlt den vertikalen Lauf getrennt (`round_end.rs:366`), Spaltenbau liegt auf derselben Achse wie normales Spiel |
| Luecke | Netz 20/156 Partien (13 %), Bauer 419/1000 (42 %) |
| Label | Vollendbarkeits-Sperre bestanden, traegt in Runde 3-5 |

**Was das AUSSCHLIESST**, obwohl dazu Befunde vorliegen: k2 (Diagonalen), k4
(Aeussere Felder), k5 (Eckplatten), k6 (Spezialfelder). Ihre Messungen bleiben in
den Preregs erhalten und gelten weiter, werden aber **nicht weiterverfolgt**. Erst
wenn k1 traegt, kommt k2 — so war es in
`PREREG_plate_policy_supervision.md` registriert und so bleibt es.

**Konkret heisst k1-only:**

- Erfolgsregeln nennen nur k1. (Die registrierten "k1 oder k2"-Klauseln bleiben
  gueltig, werden aber auf k1 gelesen — die strengere Lesart.)
- Der Verbraucher wird nur mit `MOSAIC_OWNERSHIP_GEW` auf k1 gefahren.
- Nebenbefunde zu anderen Kriterien werden protokolliert und NICHT verfolgt.

**Der Anlass war Drift, nicht Erkenntnis:** am 2026-08-18 sind aus k1-Messungen
heraus Analysen zu k6 (Spezialkuppel-Platzierung, Stapel-Ziehungen), k5 und k4
entstanden. Alle drei lieferten echte Befunde — und keiner davon brachte k1 voran.

---

## FAHRPLAN DIESER GENERATION (Nutzer-Auftrag 2026-08-18, woertlich)

> 1. *"modell erstellen dass mit dem ownership head aktiv die züge steuert und
>    den champ schlägt"*
> 2. *"anschließend mit dem neuen champ self plays (smoke test) überprüfen ob
>    hier genug diversität vorhanden ist für den ownership head"*
> 3. *"dann self plays für v22 erstellen"*

Die Reihenfolge ist bindend: **kein v22-Korpus, bevor Schritt 1 und 2 stehen.**
Der Grund ist gemessen und nicht theoretisch — ein Korpus, den ein Netz erzeugt,
das die Platten nicht steuert, enthaelt die Zielhandlung nicht, und genau daran
ist die Destillation zweimal gescheitert (`PREREG_corpus_distillation.md`
par.10.7 warm, par.10.9 kalt).

### Schritt 1 — Stand: SIEG-HAELFTE ERFUELLT, PLATTEN-HAELFTE NICHT

**Nutzer-Einwand 2026-08-18, und er ist entscheidend:** *"ja nur spielt er noch
nicht auf die wertungsplatten"*. Der Sieg allein erfuellt Schritt 1 NICHT — der
Hebel des ganzen Vorhabens ist der Plattenblick, nicht die Siegquote.

Praezisiert man, WELCHE Platten der Regler bewegt (gegen den Nullarm,
Block-Ebene, Schwelle 2,571), wird das Bild eindeutig:

| Kriterium | Δ | Block-t |
|---|---:|---:|
| **k3** Mehrfarbige Felder | +1,59 | **2,58** |
| **k5** Eckplatten | +0,34 | **2,79** |
| k1 Vertikale Reihen | −0,09 | 0,23 |
| k2 Diagonale Reihen | +0,07 | 1,00 |

Er spielt auf die **kurzen Ketten** und laesst die teuren Geometrien liegen —
dieselbe Kettenlaengen-Grenze wie in der Skalen-Rechnung
(`PREREG_ownership_coupling.md` par.3), hier in Arena-Zahlen. Die Siege kommen
mit einiger Wahrscheinlichkeit von k3/k5.

**Folge fuer die Reihenfolge, und sie ist scharf:** wuerde dieser Stand als
Champion promoviert, erzeugten seine Self-Plays k3/k5-Verhalten und weiter kein
k1/k2 — der v22-Korpus enthielte die Zielhandlung erneut nicht. Genau die Falle,
gegen die die Fahrplan-Reihenfolge gebaut ist. **Schritt 1 braucht also beides:
Sieg UND Bewegung bei k1/k2.**

#### Die Sieg-Haelfte, dokumentiert (Zurechnung fehlt)

`alphazero_v21-b18_best.onnx` @400 gegen Champion @400, 407 Seeds, keine Remis:

| Arm | Siege | gegen 50 % |
|---|---:|---|
| Regler **AUS** | 211/407 = 51,8 % | p = 0,457 — Paritaet |
| **Produktform D1** `0.1,0.3` | **236/407 = 58,0 %** | **p = 0,0013** |
| **Konjunktionsform D1** | **229/407 = 56,3 %** | **p = 0,0115** |

**Mit aktivem Kopf schlaegt `b18_best` den Champion signifikant, ohne ihn
nicht** — und "aktiv steuert" ist keine Behauptung: 402 von 407 Partien laufen
anders als im Nullarm. Zwei Vorbehalte, beide offen:

1. **Kein Brettwechsel.** Alle drei Arme liefen auf Brett 0. Der Seiteneffekt
   ist damit unkontrolliert; die DIFFERENZ zwischen den Armen ist es nicht
   (gleiche Seite, gleiche Seeds), wohl aber die absolute Aussage gegen den
   Champion. Naechste Messung: derselbe Arm mit vertauschten
   `--model`/`--model-b` und eigenem `--out-prefix`.
2. **Gepaarte Zurechnung fehlt.** Gegen den Nullarm ist der Zuwachs NICHT
   signifikant (exakter McNemar: Produktform p = 0,066, Konjunktionsform
   p = 0,2025). Der Sieg ueber den Champion steht, die Zurechnung zum Kopf
   nicht.

**NICHT FREIGEGEBEN (Nutzer 2026-08-18):** *"es ist good to know, aber noch
nicht von mir freigegeben den champion herauszufordern"*. Also **kein
Brettwechsel-Lauf, kein Gating, keine Promotion** auf diesem Stand — die Zahlen
sind Kenntnisstand, kein Auftrag. Der Grund liegt oben: die Platten-Haelfte
fehlt, und ein Champion ohne k1/k2 wuerde den v22-Korpus wieder ohne die
Zielhandlung erzeugen.

Wenn Schritt 1 spaeter freigegeben wird, waere die Reihenfolge: erst
Brettwechsel (billig, entscheidet Vorbehalt 1 und verdoppelt die Paarungen fuer
Vorbehalt 2), dann Gating.

### Schritt 2 — die Diversitaet ist GEBAUT, nicht erhofft

**Nutzer-Hinweis 2026-08-18:** *"das haben wir schon mal festgehalten. hier
variieren wir den 'zug' zur wertungsplatte mit dem seed. sprich es wird dann
eine gleichverteilung geben bei der sich die partien mal mehr und mal weniger
auf die wertungsplatten fokussieren"*. Der Mechanismus existiert und ist
verdrahtet — nachgeprueft:

| Baustein | Stelle |
|---|---|
| `MOSAIC_WERTUNG_STREUUNG_MAX`, Default **0,0 (aus)** | `net_mcts.rs:1152`, Registry `knob_registry.rs:81` |
| Ziehung: SplitMix64 aus dem Partie-Seed, **gleichverteilt in [0, max]** | `net_mcts.rs:1164` |
| Produktions-Verdrahtung im Self-Play, je Partie | `self_play.rs:3134-3136` |
| Wirkt auf | `wertung_shaping_weights()` → `[w; 8]` (`net_mcts.rs:1218`) |
| Ausgesetzt fuer Label-Rollouts (sonst Rauschen im Ziel) | `net_mcts.rs:1105 ff.` |

**Korrektur einer frueheren Formulierung in dieser Datei:** hier stand, der
Smoke Test muesse pruefen, ob der Champion "zu deterministisch" spielt. Das ist
die falsche Richtung — die Streuung erzeugt die Diversitaet aktiv, unabhaengig
davon, wie deterministisch das Netz ist. Der Smoke Test prueft, ob die
gezogene Spreizung sich in den LABELS niederschlaegt.

**Zwei Punkte, die dabei zu beachten sind (beide aus dem Code, nicht vermutet):**

1. Die Streuung dreht das **heuristische** Plattengewicht (`wertung_progress`),
   nicht das Ownership-Gewicht. Fuer Label-Diversitaet ist das richtig — die
   Partien variieren im Plattenfokus, also variieren die Ownership-Ziele mit.
2. `wertung_shaping_weights()` liefert `[w; 8]` — **derselbe** Wert fuer alle
   acht Kriterien. Die Streuung variiert also den Plattenfokus INSGESAMT, nicht
   je Kriterium. Damit kann k1/k2 weiter untersampelt bleiben, obwohl die
   Spreizung insgesamt gut aussieht. **Der Smoke Test muss deshalb die
   Positivrate von k1 und k2 EINZELN ausweisen**, nicht nur ein Diversitaetsmass
   ueber alle Kriterien. Vergleichsmassstab sind die Raten des v21-Fensters.

### Schritt 3 — v22-Korpus

Erst danach. Design liegt auf Halde (Abschnitt "v22-FENSTER"), NICHT eingeplant.

### Zwei neue Vorregistrierungen (2026-08-18) — beide OFFEN, nichts gebaut

Anlass: externe Durchsicht mit zwei ausgearbeiteten Spezifikationen. Beide sind
gepruefte Antworten auf `DOSSIER_ownership_head.md` Abschnitt 7, beide in
Plan-Zeitform, **keine** ist freigegeben.

| Datei | Greift an | Stand |
|---|---|---|
| `PREREG_asymmetric_curriculum.md` | 7(1) Wegsymmetrisierung — der Value-Kopf hat den Plattenbau nie als Vorteil gesehen | Sperre par.5 vor dem Training; **erzeugt einen Self-Play-Korpus** |
| `PREREG_reachability_target.md` par.12 (Arm P) | die Saettigung des Vollendbarkeits-Labels in Runde 1-2 | faellt in den ohnehin anstehenden Relabeling-Durchlauf |

**Die eine offene Entscheidung, die nicht beim Bauen fallen darf:** der
asymmetrische Arm erzeugt einen neuen Korpus. Der Fahrplan sperrt
Korpus-Erzeugung bis Schritt 1 und 2 stehen; Praezedenz fuer einen *Lehr*-Korpus
ausserhalb der Reihe ist `PREREG_ownership_corpus.md`. Einordnung — Lehrkorpus
(jetzt) oder Schritt 3 (spaeter) — ist **Nutzer-Entscheid und offen**
(`PREREG_asymmetric_curriculum.md` par.9).

Was aus den externen Spezifikationen **verworfen** wurde, steht mit Begruendung
in den Dateien selbst (`asymmetric_curriculum` par.8, `reachability_target`
par.13) — damit es nicht in einem halben Jahr erneut vorgeschlagen wird.

---

## STAND 2026-08-17 (Nachmittag) — Champion unveraendert `v21_2d_brierbest`

### DER BEFUND DES TAGES: der Korpus war policy-maskiert

**Der Policy-Kopf hat den Lehrkorpus in SIEBEN Trainingslaeufen nie gesehen**
(`w0`, `w01`, `w02`, `w05`, `w1`, `F1`, `F2`). Traeger ist nur, wer im
Traeger-Manifest gelistet ist oder mit `selfplay_v19wdl`/`selfplay_v20wdl`
beginnt (`neural_net.py:679`, `:667`); fuer Nicht-Traeger gilt `pol_w = 0.0`
(`:1804`). Value-, Punkte- und Ownership-Ziele liefen normal durch — die Laeufe
sahen unauffaellig aus. Details: `PREREG_corpus_distillation.md` par.10.4/10.5.

**Behoben** mit `data/policy_carrier_manifest_own.json` (Korpus traegt Policy,
Fenster nur Value). Das Trainingsmanifest protokolliert den Traegersatz jetzt
je Praefix mit (`train_manifest.py`) — diese Zeile haette den Befund am ersten
Tag gezeigt.

### Was mit korrekt getragenem Korpus herauskam

Neues Fenster: Korpus als Sockel (700 Dateien Policy-aktiv), `v19wdlsw`
ausgeduennt, Gesamtmenge exakt wie v21 (2945 Dateien).

| | Ergebnis |
|---|---|
| **`v21-b18`** (Gewicht 1,0) | bester Checkpoint Epoche 4. Gegen Champion **211/407 = 51,8 %** (p=0,49) — **Paritaet** |
| **Plattenbau von `b18`** | k1 +0,05 · k2 **0,00** · k5 −0,09 gegen den Champion. **Keine einzige Diagonale in 150 Partien** |
| **`v21-b19`** (Gewicht 2,0) | Kopf besser auf 3 von 4 Kriterien, Waechter haelt (+0,49 % gegen Schwelle 2 %) → **2,0 uebernommen** |
| **Priormasse** (`probe_column_build_prior_mass_heldout.json`) | `b18` legt auf die Bauer-Aktion **4,91x** Gleichverteilungsmasse (Champion 0,59x), in **129 von 130** Held-out-Partien vorn |

> **Die Destillation ist gelungen — sie kommt nur nicht bis aufs Brett.** Der
> Prior bietet den plattenbauenden Zug oft dominant an, und er verschwindet
> zwischen Prior und Brett. Uebrig bleiben Suche und Formel, nicht die Policy.

### Der Regler-Strang ist ABGESCHLOSSEN (negativ)

Tor C auf `b18_best` wiederholt (erstmals mit plattenfaehiger Policy), dann
frisch-Seed-repliziert: **nicht repliziert.** k5 fiel von t 2,79 auf t 1,10,
der Siegzuwachs von p 0,066 auf p 0,699. Beide Regler bleiben Default 0.
`PREREG_gate_c_d1_replication.md` par.6.

**Was UEBERLEBT und den naechsten Schritt traegt:** der k3-Zuwachs war ueber
alle drei Dosen stabil (+1,59 / +1,20 / +1,68, Block-t bis 5,65). **Das
Kriterium mit der KURZEN Konjunktion bewegt sich, die mit sechs Feldern nicht**
— die Produktkollaps-Vorhersage, aus Arena-Daten bestaetigt.

### KONJUNKTIONSTERME: GEMESSEN, NICHT-ERFOLG (2026-08-18)

`MOSAIC_OWNERSHIP_CONJ`, Default 0 = Produktform (byte-identisch), Commit
`d520672`. `scoring::expected_plate_points_conj`: konjunktive Kriterien
(k0/k1/k2/k3/k5/k7) aus den gelernten Atomen, additive k4/k6 weiter aus den
Feldlabels. Bei Kopf < 140 Rueckfall MIT Warnung. Test
`conjunction_atom_ranges_match_label_builder` nagelt die Atom-Bereiche fest.
`cargo test --release`: 447 passed, 0 failed.

**ERGEBNIS (par.9): k1 +0,14 (Block-t 0,54) · k2 +0,07 (Block-t 1,00)** —
beide weit unter der Schwelle 2,571. Siege 229/407 = 56,3 % gegen 211/407 im
Nullarm (McNemar p = 0,2025, kein Verlust), aber das war nie das Kriterium.

**Wichtig fuer die Zurechnung: das ist KEIN Nullbefund aus Wirkungslosigkeit.**
In **402 von 407 Partien** weicht der Ausgang vom Nullarm ab (in 178 kippt
sogar der Sieger), bei hoher Dosis kippen 6 von 8. Der Regler greift massiv ins
Spiel ein — er verschiebt den Plattenbau nicht. **Damit ist die Produktkollaps-Erklaerung als URSACHE widerlegt:** sie
sagte voraus, dass k1/k2 sich bewegen, sobald die Form repariert ist. Die Form
ist repariert, k1/k2 bewegen sich nicht.

**Registrierter naechster Schritt (par.7, woertlich):** *"Dann ist die Form
nicht der Engpass, sondern die Kalibrierung oder die Kandidatenauswahl — und
der naechste Schritt ist die Rangregel, nicht eine weitere Dosis."*

Die Anordnung war (Start 2026-08-17 23:59, fertig 2026-08-18 00:58) (Anordnung `PREREG_conjunction_terms.md`
par.6/par.7): `b18_best` @400 gegen Champion @400, 407 Seeds, EIN zusaetzlicher
Arm — D1 `0.1,0.3` mit `MOSAIC_OWNERSHIP_CONJ=1` —, Blockgroesse 25, mit
`--log-games`. Der Produktform-Arm bei D1 liegt schon vor
(`paired_arena_env_gate_c_b18.json`, Arm `0.1,0.3`), der Nullarm ebenfalls
(`paired_arena_env_b18best_vs_ch.json`). Ausgabe: `paired_arena_env_conj_d1_b18.json`.
**Erfolgsregel: k1 oder k2 signifikant auf Block-Ebene gegen die Produktform,
ohne Siegverlust.** k3/k5 zaehlen NICHT.

**Zwei Gueltigkeitskontrollen liefen vorher, beide dokumentiert in par.6.1:**

1. **Das Wheel war veraltet — Beinahe-Fehlschluss.** Die installierte
   `mosaic_rust.cp314-win_amd64.pyd` trug den Stand 16.08. 10:57, der
   Konjunktionscode den Stand 17.08. 11:04/11:07. Die Arena haette die ALTE
   Engine gefahren, der Konjunktionsarm waere bitgleich mit dem Produktarm
   gewesen — und ein "k1/k2 flach" haette den einzigen verbliebenen Weg
   faelschlich geschlossen. Neu gebaut 23:44:10.
2. **Determinismus zuerst, dann Reglerwirkung.** Derselbe Arm zweimal auf
   gleichen Seeds: **8/8 Partien identisch**. Konjunktionsform gegen
   Produktform: **6/8 Partien kippen**. Ohne die erste Zahl beweist die zweite
   nichts. Belege: `paired_arena_env_conj_determinism.json`,
   `paired_arena_env_conj_smoke.json`.

### ZWEI VON DREI WEGEN ZUM PLATTENBAU SIND GESCHLOSSEN

| Weg | Stand |
|---|---|
| Laufzeit-Regler in Produktform | **geschlossen, negativ** — Tor C wiederholt UND frisch-Seed-repliziert |
| Policy-Destillation | **geschlossen, negativ** — Warm Start (par.10.7) UND Cold Start (par.10.9) |
| **Aktivierung mit korrigierter Form** | **GEMESSEN, NICHT-ERFOLG** — k1 Block-t 0,54, k2 Block-t 1,00 (par.9). Die Form war nicht der Engpass |

**Alle drei Wege sind damit durchgemessen, keiner traegt.** Was ueberlebt, ist
die Zurechnung: der Prior BIETET den Zug an (4,91x), der Regler GREIFT massiv
ins Spiel ein (402/407 Partien laufen anders) — und trotzdem entsteht keine
Platte. Der
Engpass sitzt also zwischen Angebot und Auswahl, nicht in der Formel und nicht
im Prior.

**Harte Rangregeln sind AUSGESCHLOSSEN** (Nutzer 2026-08-18: *"wir pfuschen
nicht mit harten rangregeln herum"*) — der in `PREREG_conjunction_terms.md`
par.7 registrierte Satz ist damit ueberholt, soweit er eine Rangregel nennt.

### NAECHSTER SCHRITT: KOPPLUNG, nicht Formel — `PREREG_ownership_coupling.md`

Der Auftrag lautete, Draft und Tiling **gemeinsam** anzusehen. Das hat drei
Dinge ergeben, die alle drei bisherigen Preregs uebersehen haben:

1. **Das Tiling entscheidet ein SOLVER, nicht die Suche** (`tiling_solver.rs:990`,
   die Diagnose steht dort schon im Code). Der Plattenbau ist eine
   Tiling-Handlung — ein Regler, der nur am Blattwert der Draft-Suche haengt,
   kann ihn strukturell nicht ausloesen.
2. **Die Suche ist GUMBEL, nicht PUCT** (`net_mcts.rs:2869`; PUCT ist Legacy).
   Der Q-Anteil geht ueber `σ(q) = (c_visit + max_N)·c_scale·q` ein, c_visit=50,
   c_scale=1,0 — Verstaerkung ~100 gegen Gumbel-Rauschen ~1,28. **Hergeleitet**
   (max_N=50 ist Annahme): ein gefuelltes Spezialfeld erreicht ~45 % des
   Rauschens und wirkt, eine Fliese in einer Spalte ~1,6 % und wirkt nicht.
   Damit ist erklaert, warum k6 sich bewegt und k1/k2 nie — es ist die
   **Skala**, nicht die Form. Das gemeinsame `/50` (`:1059`) trifft Kriterien,
   deren Inkremente drei Groessenordnungen auseinanderliegen.
3. **Die Tiling-Seite hat die Lehre schon gezogen, die dem Draft fehlt:** dort
   marginale Werte plus Gewicht je Kriterium, ausdruecklich weil der
   Spezialfeld-Posten (−11,70) *"jede Geometrie ueberdeckt"* (`:1108`, gemessen
   2026-08-12). Der Draft-Pfad formt weiter mit dem NIVEAU.

**Beifang, gemessen am Nullarm (Regler AUS), also aus dem trainierten Netz und
nicht aus dem Verbraucher:** bei aktiver k6-Platte legt `b18` Spezialkuppeln zu
**62,8 %** nach unten (ohne die Platte 42,3 %) und raeumt die oberen Slots von
29,6 % auf **8,5 %**. `docs/domain_knowledge.md` §8 verlangt das Gegenteil. Bei
k5 dagegen **keine Reaktion** (50,2 gegen 50,1 %), obwohl §6 dort
Spezialkuppeln in die unteren Ecken will. Das Netz hat eine Anti-§8-Gewohnheit
GELERNT. Zahlen: 4,36 Spezialplatten je Spieler, 3,94 leere Spezialfelder je
Partie, **0 von 153 Partien** ohne Verlust, und von 367 Spezialfliesen lagen
298 in den Reihen 1–2 gegen **4** in den Reihen 5–6.

**Die groessere offene Frage steht in par.9 der neuen Prereg:** der Kopf sagt
vorher, was passieren WIRD, nicht was erreichbar WAERE. Zwei unabhaengige
Belege stuetzen das — der staerkere Kopf machte den Verbraucher inert (Tor C
par.15), und bei k6 ist die Kopplung stark genug und das Verhalten trotzdem
falsch.

**Cold Start `v21-b20` gegen Champion (fertig 2026-08-17 22:20):** 158/407 =
38,8 % Siege, und gepaart gegen `b18` auf Block-Ebene k1 +0,09 (t 0,27), k2
+0,13 (t 1,00), k5 +0,06 (t 0,59) — **kein Kriterium signifikant**. Eine Policy,
die NICHTS anderes gesehen hat als plattengelenktes Spiel, baut nicht mehr
Platten. **Der Prior war nicht die Blockade.** Der Cold Start ist als Fahrzeug
erledigt: schwaecher UND nicht besser bei den Platten.

**Der verbliebene Weg ist begruendet, nicht bloss uebrig:** die Priormasse zeigt,
dass `b18` den plattenbauenden Zug dominant ANBIETET (4,91x Gleichverteilung,
129/130 Partien) — er setzt sich nur nicht durch. Genau dort greift der
Verbraucher, und genau dort ist die Produktform die gemessene Bremse.

### WEG 1 (Frozen Trunk) ABGESCHLOSSEN, NEGATIV — `v21-b22`

Fertig 2026-08-18, Early Stop nach **15** von 60 Epochen. Einzelheiten in
`PREREG_lr_schedule.md`.

| | Own-Val |
|---|---:|
| `b18_best` E4 (Startpunkt) | 0,3466 |
| **`b22` Frozen Trunk, bestes (E13)** | **0,3407** |
| `b18` gemeinsames Training E15 | 0,3191 |
| `b19` E15 (Gewicht 2,0) | 0,2994 |

Der eingefrorene Rumpf gewinnt 0,0059 und steht dann (E9-E15 zusammen 0,0004).
**Weg 1 liefert den SCHLECHTEREN Kopf**, nicht den besseren — die Kopfguete
haengt an der Rumpfdarstellung, das Einfrieren spart die Policy und kostet den
Kopf. Fuer die Kopplungsarbeit bleiben `b18`/`b19` die Kandidaten.

**Beifang, er stuetzt den LR-Strang:** die LR blieb ueber alle 15 Epochen bei
5,00e-04. `ReduceLROnPlateau` (patience 2) hat NIE ausgeloest, weil sich der
Verlust je Epoche noch um 0,0001-0,0002 verbesserte — das zaehlt als
Fortschritt. Ein reaktiver Scheduler greift selbst auf einer faktisch flachen
Kurve nicht, solange sie monoton bleibt.

**Die Warnung zu `b22` bleibt gueltig:** um 23:35 meldete der Harness den Lauf
als "failed, exit code 1". Gestorben war der **Hintergrund-Wrapper der Shell**,
nicht das Training — der Prozess lief sauber zu Ende. **Regel: bei einer
"failed"-Meldung zuerst `Get-CimInstance Win32_Process` fragen, ob das Kind noch
lebt, bevor irgendwas neu gestartet wird.**

### Kalibrierung: Versatz erledigt, Steigung offen — Uebergangsweg entschieden (2026-08-18)

**In einem Satz:** die geplante Mittelwert-Korrektur ist gegenstandslos (unten
gemessen), die Steigungskorrektur bleibt offen und bekommt als Uebergang einen
ausgesperrten BAUER-Satz, bis ein plattenbewusster Champion eigene Daten
liefert.

Der Konjunktions-Kopf **rangiert gut und kalibriert schlecht** (AUC 0,83-0,91,
Brier nur 8-14 % unter der Grundrate, ueber 0,5 ueberschaetzt er) — das steht.
Die daraus abgeleitete **Massnahme** aber faellt weg.

**Gemessen** (`tools/probes/conjunction_marginal_normal_play.py`, `b19_best`,
150 Normalspiel-Dateien, 1500 Partien, 3000 Bretter): Kopf-Mittelwert gegen die
tatsaechliche Endrate derselben Partien, Runde-3-Zustaende.

| Gruppe | Kopf sagt | tatsaechlich | DELTA |
|---|---|---|---|
| Reihen k0 | 4,294 % | 4,278 % | 0,00 |
| **Spalten k1** | 0,731 % | 0,517 % | **0,35 ± 0,10** |
| Diagonalen k2 | 0,453 % | 0,117 % | 1,36 ± 0,38 (nur 7 Positive) |
| Ecken k5 | 26,692 % | 26,650 % | 0,00 |
| Joker k3 | 40,881 % | 39,800 % | 0,04 |
| farbenreich k7 | 0,955 % | 1,017 % | −0,06 |
| Layout (k3-Input) | 49,777 % | 50,000 % | −0,01 |

**Die Herleitung aus Grundraten war ein Artefakt der Referenzwahl.** Gegen die
Bauer-Arme gerechnet ergibt k1 einen Versatz von 1,58, gegen die
Trainingsmischung 0,64 (1,08 % bei 2145 Fenster- + 800 Korpus-Dateien laut
`manifest_train_v21-b19_20260817_000926.json`) — gemessen sind 0,35. Eine ungeprueft eingetragene
Konstante haette den Kopf dreifach zu stark gedaempft. **Regel daraus:** einen
Prior-Versatz nie aus Grundraten falten, wenn man ihn am Kopf selbst messen
kann; die Referenzwahl bewegt ihn um den Faktor 3.

**Nutzer-Einwand, der auch die 0,35 entwertet (2026-08-17):** die
Normalspiel-Rate stammt aus Partien von Netzen, die die Wertungsplatten NICHT
beruecksichtigen. Den Kopf darauf zu eichen hiesse, ihn auf genau das Verhalten
zu kalibrieren, das der Leitstern abschaffen will — seine Spalten-Zuversicht
wegzurechnen ist das Gegenteil des Hebels.

**Was NICHT widerlegt ist:** `PREREG_ownership_selector.md` par.9.2 hat die
Fehlkalibrierung im OBEREN Bereich gemessen (Top-Bin Spalten: vorhergesagt
0,949). Das ist eine Steigungsfrage (B != 1), kein Versatz — ein Offset haette
sie ohnehin nie behoben. `pos_weight` im Loss bleibt zurueckgestellt (kostet
einen vollen Lauf und zerstoert jeden Bestandsvergleich).

**Der obere Bereich existiert im normalen Spiel NICHT** (Nutzer-Frage
2026-08-18 "helfen extra Bauer-Self-Plays?",
`tools/probes/conjunction_reliability_by_source.py`, `b19_best`, 60 Dateien je
Quelle, Runde-3-Zustaende):

| ueber p=0,5 | normales Spiel | Bauer-Arme |
|---|---|---|
| Spalten k1 | **3** von 7200 | **106** von 7200 |
| Diagonalen k2 | **0** von 2400 | **109** von 2400 |

Fehlkalibrierung dort, in den Armen: k1 0,50-0,80 vorhergesagt 63,0 % gegen
46,2 % tatsaechlich (91 Faelle), 0,80-1,00 88,0 % gegen 60,0 % (15); k2
64,6/50,6 (77) und 86,7/50,0 (32). **k5 ist im normalen Spiel ueber die GANZE
Kennlinie richtig** (66,0/66,4 bei 393 Faellen, 92,5/91,1 bei 858) — dort ist
nichts zu holen.

**Antwort auf die Frage (sie galt dem ausgesperrten Satz, nicht dem Korpus):
ja.** Die Arme sind fuer den oberen Bereich die einzige Quelle — 150-300
Dateien geben 250-550 Faelle ueber 0,5, ~17 Partien/min (k1-Arm-Zeitstempel)
also 1,5-3 h, mit dem 4,7- bzw. 35-fachen Ertrag je Datei gegenueber
Normalspiel. Der Fit gilt dann fuer die Bauer-Verteilung, nicht fuer die
Einsatzverteilung.

**Was den Nutzen heute begrenzt:** im normalen Spiel liegen **98,3 %** der
k1-Faelle unter p=0,05, und dort ist der Kopf fast richtig (0,3/0,5 · 1,9/1,3).
Eine Steigungskorrektur wuerde kaum feuern. **Ungeprueft:** gemessen sind
Zustaende GESPIELTER Partien, nicht Suchknoten — die Suche besucht
plattenbauende Linien, die im Verlauf nie auftauchen, und koennte hoeher
liegen. Das ist der einzige Weg, auf dem die Korrektur schon heute wirkte, und
er ist mit einer Sonde auf Suchknoten pruefbar.

### NEUER STRANG: der Shaping-Nenner ist rundenblind (2026-08-18)

`WERTUNG_SHAPING_SCALE` ist fest **50** (`net_mcts.rs:1059`). Gemessen an 22
Arena-Logs (`static/log/elo/*.log`) steht nach Runde 1 ein Punktestand von **4**
auf dem Brett, nach Runde 5 von 47,6, nach Endwertung 55,7 (Mensch: 7,0 / 59,2 /
74,4). Der Nenner ist also frueh um mehr als eine Groessenordnung zu grob.

**Die Kurvenform ist staerke-invariant** — die Niveaus liegen 33 % auseinander,
die Anteile am Endstand stimmen auf 0,02 ueberein (0,083 · 0,172 · 0,327 ·
0,515 · 0,825). Genau das erlaubt ein festes Profil: der Verlauf ist
Spielstruktur, nicht Spielstaerke.

**Das Argument, das den Strang traegt:** `w` und `S` sind global austauschbar
(im linearen `tanh`-Bereich ist `w·tanh(E/S) ~ w·E/S`), je Runde aber nicht. Die
Dosisreihen variierten `w` und konnten eine RUNDENabhaengige Schieflage
strukturell nicht finden. Und die ist da: bei vergleichbarer Zielerreichung
ergibt sich heute Runde 1 ein Shift von 0,014 und Runde 5 einer von 0,139 —
Faktor 10 zugunsten der Runde, in der nur noch <= 7 Optionen offen sind
(Zug 1 der Runde 1: 195). **Der negative Dosisbefund ist damit nicht ungueltig,
aber er koennte ein Artefakt sein.**

**Vorregistriert: `PREREG_shaping_scale_per_round.md`.** Knopf statt Konstante
(Default = heutiges Verhalten), Pfad A (Wertung) zuerst, `ROUND_GAIN` fest auf
0, Erfolgsregel k1/k2 auf Block-Ebene ohne Siegverlust. **Vorbedingung vor dem
Bau:** Saettigungspruefung auf `data/holdout` — liegt das 90-%-Quantil von
`E_r/SCALE_r` unter 1,0, traegt ein gemeinsames Profil fuer beide Pfade, sonst
brauchen sie getrennte. Die Verzweigung ist vorab benannt.

**Einordnung, damit es niemand ueberschaetzt:** beide Shaping-Pfade sind per
Default AUS (`MOSAIC_WERTUNG_SHAPING_W` und `MOSAIC_OWNERSHIP_W` je 0,0). Der
Umbau repariert nichts im laufenden Spiel — er stellt die Bedingungen her, unter
denen die Injektionsmessung ueberhaupt aussagekraeftig waere.

### DER FELD-KOPF, AN DER SPALTE GEMESSEN (2026-08-18)

Nutzer-Frage: der Kopf gibt je Feld P(am Ende belegt) aus -- steigt die
Spaltenwahrscheinlichkeit, wenn ich eine Fliese lege? Sonde
`tools/probes/ownership_column_intent.py`: bei GLEICHEM Fuellstand einer Spalte
(Brettlage kontrolliert) die Kopf-Vorhersage fuer die noch leeren Felder,
gegen die tatsaechliche Vollendungsrate. Runden 2-4, 30 Dateien je Arm.

| Arm | Fuell | p_belegt | p_leer | Produktform | tatsaechlich | Faktor |
|---|---|---|---|---|---|---|
| a | 3 | 79,0 % | 27,8 % | 0,57 % | 1,1 % | 2,0x |
| **k1** | 3 | 70,5 % | 33,3 % | **1,27 %** | **21,1 %** | **16,5x** |
| a | 5 | 66,5 % | 22,2 % | 1,08 % | 15,8 % | 14,6x |
| **k1** | 5 | 61,1 % | 31,1 % | **1,77 %** | **38,9 %** | **21,9x** |

1. **Der Kopf sieht die Absicht kaum.** Bei Fuellstand 3 sagt er 27,8 % (a)
   gegen 33,3 % (k1) -- Faktor 1,2, waehrend die Wirklichkeit um Faktor **19**
   auseinanderliegt. Er ist also nicht nur "Eintreten statt Erreichbarkeit",
   er ist auch als Eintretens-Vorhersager schwach.
2. **Er weiss nicht, was sicher ist.** Bereits belegte Felder bekommen 61-86 %
   statt 100 %. GEPRUEFT: 186 von 186 belegten Feldern sind am Ende belegt.
3. **Die Produktform multipliziert sechs solcher Zahlen.** Bei Fuellstand 5
   fehlt EIN Feld: Produkt 1,77 % gegen 38,9 % echt. Fuenf der Faktoren sind
   Sicherheiten, die mit ~0,61 bepreist werden (0,61^5 = 0,085).

**DIE LUECKE, praezise:** es gibt keinen Term, der sieht, dass ein
DRAFTING-Zug eine Spalte voranbringt. Der Fortschrittsterm `wertung_progress`
koennte es, liest aber nur `build_grid` und ist damit innerhalb einer Runde
fuer jeden Drafting-Zug identisch (`archive/history.md`, Ursache am Code
geprueft) -- deshalb hob die Injektion die vertikalen Platten nur von 0,70 auf
1,05 Punkte. Der Kopf-Weg wiederum sieht die Absicht nicht. **Kandidat, gebaut
und auf Default 0: `MOSAIC_ENDAWARE_W`** (`solve_rec_endaware`,
`tiling_solver.rs:519-546`) rollt die Musterreihen auf die Kuppel aus und
maximiert Platzierungspunkte + Endwertung -- in `history.md` als "der
aussichtsreichste" der drei Kandidatenterme notiert. NICHT gemessen.

**Korrektur einer eigenen Formulierung:** die Heuristik ist NICHT der
plattenbewusste Spieler schlechthin -- bei Spalten liegt sie mit 1,2 %
Vollendung (Fuellstand 3) auf dem Niveau von Arm a. Plattenbewusst ist sie bei
den Spezialfeldern (k6), nicht bei k1.

### KALIBRIERUNG GEFITTET -- ERGEBNIS: NICHT EINBAUEN (2026-08-18)

`tools/probes/conjunction_calibration_fit.py`, `b19_best`, Fit auf 25.000
Brettern (Arme a/k1/k2/k5, je Partie ein Zustand pro Runde), Transfer auf 5.000
Brettern des `heur`-Arms. Rohzahlen: `evaluations/conjunction_calibration_fit.json`.

| Gruppe | Positive | B | A | Brier-Gewinn Fit | Gewinn Transfer |
|---|---:|---:|---:|---:|---:|
| Reihen k0 | 4535 | 1,037 | -0,136 | +0,4 % | +2,6 % |
| **Spalten k1** | 5175 | 0,921 | +0,144 | **+0,6 %** | **-6,0 %** (190 Pos) |
| **Diagonalen k2** | 2005 | 0,839 | -0,095 | **+1,3 %** | **-15,4 %** (20 Pos) |
| Ecken k5 | 28375 | 0,952 | -0,018 | 0,0 % | +0,5 % |
| Joker k3 | 9065 | 0,980 | -0,065 | +0,1 % | -0,5 % |
| farbenreich k7 | 1240 | 0,823 | -0,719 | +0,1 % | +0,3 % |

**Drei Befunde, und sie zeigen alle in dieselbe Richtung:**

1. **Die Korrektur ist winzig.** B liegt zwischen 0,82 und 1,08, der
   Brier-Gewinn im Fit-Satz bei hoechstens 1,3 %. Kein Vergleich zu den
   ~20 %, die eine echte Fehlkalibrierung hergeben wuerde.
2. **Sie uebertraegt NICHT.** Auf `heur` -- dem einzigen plattenBEWUSSTEN
   Spieler im Satz -- verschlechtert sie k1 um 6,0 % (190 Positive, belastbar)
   und k2 um 15,4 % (20 Positive, schwach). Genau die als offen markierte
   Transfer-Annahme ist damit gemessen und GEFALLEN.
3. **Die Fehlkalibrierung haengt an der RUNDE, nicht an der Gruppe.** Eigener
   Fit je Runde: k1 B = 0,71 / 0,93 / 0,94 / 1,01 / 1,02 (R1..R5), k5 0,82 ->
   1,03, k2 0,69 -> 0,92. Der Kopf ist FRUEH ueberkonfident und SPAET richtig.
   Eine Konstante je Gruppe mittelt genau diese Struktur weg.

**Entscheid: kein Knopf, kein Einbau.** 0,6 % Gewinn im Fit-Satz gegen -6 %
dort, wo es zaehlt, traegt keinen Verbraucher-Eingriff.

**AUCH DIE RUNDENABHAENGIGE VARIANTE FAELLT DURCH -- Linie geschlossen.**
Vier Varianten gegeneinander, entschieden am Transfer (V0 keine Korrektur, V1 je
Gruppe, V2 je Gruppe UND Runde, V3 Steigung je Runde ueber die Gruppen geteilt +
Versatz je Gruppe):

| | Fit-Satz vs V0 | Transfer vs V0 | k1 Transfer | k2 Transfer |
|---|---:|---:|---:|---:|
| V1 | +0,27 % | **-0,01 %** | -6,0 % | -15,4 % |
| V2 | +0,47 % | **+0,03 %** | -6,4 % | -11,5 % |
| V3 | +0,22 % | **-0,02 %** | -7,1 % | -20,7 % |

Mehr Parameter helfen NICHT -- V2 hat die meiste Freiheit und gewinnt im Fit am
meisten, im Transfer bleibt alles null. Und bei den beiden ZIELkriterien wird es
mit jeder Variante schlechter, waehrend k0/k5 (die keine Korrektur brauchen)
leicht gewinnen. Kein Rausch-, sondern ein Richtungsproblem.

**Die Erklaerung, die alles zusammenhaelt (Nutzer 2026-08-18):** *"der Kopf sagt
vorher, was passieren wird, statt was erreichbar waere."* Das Ziel ist das
Endbrett der TATSAECHLICH gespielten Partie (`_final_ownership_by_game`), also
P(Kriterium | Stellung UND weiterspielende Politik) -- eine politikabhaengige
Groesse. Drei Messungen stuetzen das: die Rundenabhaengigkeit (frueh Prognose,
spaet Ablesung), der gescheiterte Transfer auf eine andere Politik, und der
k5-Arm, der MEHR volle Spalten liefert als der k1-Arm (8,53 % gegen 6,98 %) --
gleiche Brettgeometrie, andere Absicht, anderes Label.

**Folge: kein besserer Fit, sondern ein anderes ZIEL.** Eine Groesse, die
Erreichbarkeit misst statt Eintreten. Die Bauer-Arme sind davon schon die halbe
Antwort -- sie sind das "was passiert, wenn man es versucht" zur selben Stellung.
Nicht entworfen, nur festgehalten.

**Einschraenkung zu einer frueheren Zahl:** V3s geteilte Rundensteigungen sind
mit 0,866 -> 0,990 viel milder als die 0,71 -> 1,02, die der Einzelfit fuer k1
zeigte. Der starke Rundeneffekt sitzt in den duenn besetzten Gruppen und
verschwindet fast, sobald k5/k3 mitgewichtet werden.

**Widerspruch, den ich NICHT aufloesen konnte** (ungeprueft, aber protokolliert):
auf den KORPUS-Dateien zeigte `conjunction_reliability_by_source.py` fuer k1 im
Bin 0,50-0,80 noch 63,0 % vorhergesagt gegen 46,2 % tatsaechlich (91 Faelle);
auf dem Bewertungssatz sind es 58,7 % gegen 55,8 % (373 Faelle). Die neue Zahl
ist groesser und auf ausgesperrten Daten, also die bessere -- der Abstand ist
aber zu gross fuer Rauschen. Kandidat, ungeprueft: die Korpus-Partien stammen
vom 14.08. und damit von einem ANDEREN Engine-Stand als der Bewertungssatz (das
Wheel wurde am 17.08. 23:44 neu gebaut, Commit `4ca164e`).

**WIEDERVORLAGE, mit messbarem Ausloeser (Nutzer 2026-08-17):** sobald ein
Champion die Wertungsplatten beruecksichtigt, wird die Kalibrierung wieder
legitim — dann IST das normale Spiel das Zielverhalten. Der Ausloeser steht
schon fest: die k1-Grundrate liegt heute ueber **fuenf** Generationen flach bei
~0,52 % (Chi2 2,3 bei 4 FG, p=0,68; k0 driftet dagegen klar, Chi2 40,5), und
zwar WEIL keine davon Platten baut. Der erste Champion, der es tut, hebt sie
sichtbar. **Dieser Ausschlag ist das Startsignal fuer Platt-Korrektur UND
festen Bewertungssatz** — beide dann mit genau jenem Champion erzeugt.

**Bis dahin (Nutzer-Entscheid 2026-08-18): Uebergangskalibrierung auf dem
Bauer-Satz.** Begruendung, warum das NICHT der Fehler von gestern ist: der Fit
entsteht im Regime, in das wir hineinwollen, nicht in dem, das wir verlassen.
**Zwei Vorbehalte, die mitgeschrieben gehoeren:** der Transfer auf die
Einsatzverteilung ist eine ANNAHME (eine Stellung mit p=0,88 entsteht im Arm
anders als im spaeteren Netzspiel), und der Wert ist Bereitschaft, nicht
Arena-Gewinn — bei 98,3 % der Faelle unter p=0,05 feuert die Korrektur heute
kaum. Die Alternative ist aber die Annahme, p sei richtig, und die ist am
oberen Ende um 28 Punkte widerlegt. Auslegung deshalb eher zu schwach als zu
stark, Knopf mit Default 0, Arena-A/B wie ueblich.

**Der Fit gehoert JE GRUPPE GEPOOLT, nicht je Atom (Nutzer-Befund 2026-08-18):**
die Bauer-Arme schliessen bevorzugt die AEUSSEREN Spalten — von den sechs
Spalten-Atomen liegen im Korpus genau zwei bei 1,17/1,32 %, die anderen vier
bei 2,16-3,75 % (`base_rate_conj`, 14.360 Bretter), also zwei Mittelspalten
gegen vier Aussenspalten, Faktor 2,4. Im normalen Spiel gibt es diese
Schieflage nicht, sie ist von den Armen gemacht. Ein Fit je Atom wuerde die
Arm-Geometrie erben; Poolen mittelt sie heraus. Der `k5`-Arm ist aus demselben
Grund (aeusseres Spaltenpaar als Ziel) der staerkste k1-Lieferant ueberhaupt
(8,75 % gegen 6,67 % des k1-Arms, par.5a) — er kommt als Ergaenzung mit in den
Satz, ersetzt aber die Basisverteilung nicht.

### LR-Schedules: reaktive Verfahren sind hier strukturell zu spaet

Zweimal gemessen (`b21` Warm Start, `b20` Cold Start): Optimum bei Epoche 4,
Plateau-Scheduler feuert bei 8, bester Checkpoint identisch zum konstanten
Lauf. Auch `patience=1` waere zu spaet. **Kein weiteres Nachstellen.**
`PREREG_lr_schedule.md` par.7.

Nebenbefund: bei `b21` hat die LR-Senkung den Ownership-Kopf gebremst, der noch
besser wurde — ausgeloest von `val_combined`, das den Ownership-Verlust nicht
enthaelt. **Wer `plateau` fuer ein Kopf-Training nimmt, muss ihn mit dem
Ownership-Verlust speisen** (im Freeze-Modus passiert das automatisch — genau
darum laeuft `b22` so).

Falls doch ein Schedule gewollt: **proaktiver Cosine mit `T_max` 8-10**, nicht
20 und nicht 100. `T_max` haengt am `--epochs`-Flag — deshalb war der Cosine des
Bestandsrezepts seit v12b_lr immer inert.

### Cold Start `v21-b20`: Saettigung bei Epoche 4, nicht bei 40

Erwartet waren ~40 Epochen (Nutzer-Erfahrung, vorab notiert), gemessen 4 mit
Early Stop bei 15. Bestes `policy_val` 0,4392 gegen `b18`s 0,3899. **Der
Policy-Kanal ist zu schmal: 7.000 Partien von null.** Kein Schedule repariert
das.

### OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Stand |
|---|---|
| **Gewichtsarm 4,0** | Vorabregel hat ihn freigegeben (`PREREG_ownership_weight_new_window.md` par.7); Nutzer-Entscheid 2026-08-17: **weiter hinten geparkt** |
| **Stoerungs-Baustein Stufe 2** | gehoert zum **Moon-Order-Kopf**, keine Einzelentscheidung mehr |
| **Korpus mit hoeheren Sims nachgenerieren** | **ABGELEHNT** (Nutzer 2026-08-17) — nicht neu vorschlagen |
| **Fester Bewertungssatz** | **entschieden (Nutzer 2026-08-18): der BAUER-Satz, als Uebergangskalibrierung bis Netzdaten da sind.** Zusammensetzung festgelegt: **300 Dateien / 3000 Partien** — `v21_own_a` 100 · `v21_own_k1` 50 · `v21_own_k2` 50 · `v21_own_k5` 50 · `heur_own` 50, zusammen **~3 h 5 min** (Durchsaetze aus den Zeitstempeln vom 14.08.: 10,3 / 17,2 / 19,8 / 23,0 / 50 Partien je Minute). **Ablage `data/holdout/`, Praefix `selfplay_hold_` (Nutzer 2026-08-18)** — der `data/*.pkl`-Glob ist nicht rekursiv, das IST die Sperre; nie in `--extra-data-dir` aufnehmen. Aufruf waere `--version hold --tag k1` usw. **FERTIG 2026-08-18 03:28** — 300 Dateien, 3000 Partien, **0 unvollstaendige**, 2 h 39 min. **Abnahme bestanden**, jeder Arm reproduziert seinen Korpus-Zwilling (Positivrate je Atom-Brett, Klammer = Korpus aus par.5a, dort nur 120 Partien je Arm): `a` k1 0,56 % (0,49) · k5 27,05 % (27,19) | `k1` k1 **6,98 %** (6,67) | `k2` k2 **19,25 %** (20,00) | `k5` k1 **8,53 %** (8,75) · k5 **40,02 %** (38,54) | `heur` k1 0,63 % (0,35). Damit ist auch der Nutzer-Befund praezise bestaetigt: **der k5-Arm liefert mehr volle Spalten als der k1-Arm.** Seeds je Arm im Manifest (20260818-22).

**Erzeugt am 2026-08-18 00:49-03:28** (Nutzer-Go). Rezept 1:1 aus `PREREG_ownership_corpus.md` par.7: Netz-Arme 200 Sims mit `MOSAIC_WERTUNG_STREUUNG_MAX=1.0` und Champion-ONNX, Heuristik-Arm 150 Sims ohne Streuung, 8 Threads, 10 Partien je Datei, rtv aus, Ablage ueber `MOSAIC_DATA_DIR=data/holdout`. Reihenfolge heur -> a -> k1 -> k2 -> k5.

**EINZIGE bewusste Abweichung: der Basis-Seed** (20260818..22 statt der Korpus-20260814). Gleicher Seed plus gleiches Modell plus gleiche Knoepfe haette BITGLEICHE Partien ergeben — der Bewertungssatz waere eine Kopie von Trainingsmaterial gewesen.

**Werkzeug-Fehlgriff, protokolliert:** ich habe erst ein `self_play.py --out-dir` gebaut und danach gemerkt, dass `config.py:28` laengst `MOSAIC_DATA_DIR` liest — genau den Weg, den auch die Korpus-Erzeugung genommen hat (par.7 "Ablage"). Das Flag ist auf Nutzer-Entscheid wieder zurueckgenommen; zwei Wege fuer dieselbe Sache sind auf Dauer teurer. Vierter Fall von `feedback_check_existing_tools_first`. Das ist kein neues Konstrukt, sondern das Einfrieren und Vergroessern dessen, worauf Gate A heute schon misst (`n_val_corpus_files = 82` aus dem rotierenden Val-Split). Er traegt BEIDE offenen Aufgaben: Steigungsfit B != 1 und Kopfvergleiche ueber Fenstergrenzen. **Der Normalspiel-Satz entfaellt damit** — sein Zweck war der Mittelwert, und der ist gemessen und klein. (A,B) sind modellspezifisch und werden je Champion neu gefittet, der Satz bleibt fest |
| **Push** | `main` ist lokal voraus; Suite gruen, Push moeglich |

### FALLEN, die am 2026-08-17 Zeit gekostet haben

| Falle | Regel daraus |
|---|---|
| Backticks in doppelt gequoteten Bash-Argumenten werden AUSGEFUEHRT | Text mit Backticks nur ueber Heredoc mit EINFACHEN Quotes, oder ueber eine Datei. **Zweimal passiert** |
| Zeichenklasse mit EINEM Backslash vor dem Schraegstrich trifft nur den Schraegstrich | Zwei Backslashes, und vor dem Schreiben ein Selbsttest gegen BEIDE Schreibweisen. **Zweimal passiert** |
| `TaskStop` toetet die Kind-Bash nicht zuverlaessig | Nach dem Stoppen die Prozessliste pruefen. Folge: `v21-b20` lief doppelt |
| `grep`-Pipe puffert blockweise | Hintergrundlaeufe ohne Pipe starten, sonst bleibt das Log minutenlang leer |
| Gate-A-Held-out ueberlappt `b18`/`b19`-Training zu **88 %** | Kopfvergleiche ueber Fenstergrenzen brauchen einen festen Bewertungssatz. Der Paarvergleich b18↔b19 bleibt gueltig (identischer Trainingssatz, identisch betroffen) |
| Nach einer Code-Auslagerung reicht `ast.parse` NICHT | Kurzlauf mit `--train-file-limit` fahren. Zwei `NameError` haetten `b20` sofort getoetet |
| `--promote-winner` ist bei `paired_gating.py` Default TRUE | Messlaeufe brauchen `--no-promote-winner` |

### FALLEN vom 2026-08-17 (Nacht) / 2026-08-18

| Falle | Regel daraus |
|---|---|
| **Das installierte Wheel war 25 h aelter als der Engine-Code** | Vor JEDER Arena, die neuen Engine-Code messen soll: `.pyd`-Zeitstempel gegen die `.rs`-Zeitstempel halten. Haette hier ein falsches "Konjunktionsform bringt nichts" erzeugt und den einzigen verbliebenen Weg geschlossen. Danach ZWEI Kontrollen, in dieser Reihenfolge: erst Determinismus (derselbe Arm zweimal, muss 8/8 gleich sein), dann Reglerwirkung (muss abweichen). Umgekehrt beweist die zweite nichts |
| **Harness-Meldung "failed, exit code 1" betraf den Wrapper, nicht das Training** | Bei jeder Fehlmeldung zuerst `Get-CimInstance Win32_Process` fragen, ob das Kind lebt. Sonst startet man einen 7-Stunden-Lauf neu, der noch laeuft — oder erklaert ihn faelschlich fuer tot |
| **Arena ohne `--log-games` gestartet** | Die Plattenkriterien k1/k2/k5 kommen aus den Partie-Logs (`tools/plate_points_from_arena.py`). Ohne den Schalter fehlt das Feld `log` und das vorregistrierte Erfolgskriterium ist NICHT berechenbar. Vor dem Start eine Referenzdatei aufmachen und die benoetigten Felder vergleichen |
| `nohup … &` in einem Bash-Aufruf | Der Wrapper meldet sofort "completed" und der Lauf ist nicht mehr harness-verfolgt. `run_in_background` benutzen, ohne `&`. **Steht schon im Merkzettel und ist wieder passiert** |
| Aus einem Dict mit `' '.join(...)` lesen liefert die SCHLUESSEL | Wirkte wie ein Manifest-Mangel ("`cli_args` speichert keine Werte"), war ein Lesefehler. Vor einer Mangel-Behauptung die Datenstruktur ansehen |

---

## PARTIE-REPLAY IST EXAKT (erledigt 2026-08-18) -- `PREREG_action_id_logging.md`

**Jede kuenftige Mensch-vs-KI-Partie ist Zug fuer Zug exakt nachspielbar**, weil
die Engine je Drafting-Aktion eine maschinenlesbare Zeile in die GESPEICHERTE
Logfassung schreibt (nicht in die Anzeige):

    #a {"id": 86, "p": 0, "a": {"type": "stone", "source": "LARGE_FACTORY_SUN", ...}}

Die `id` ist dieselbe, gegen die der **Policy-Kopf trainiert**
(`features.rs::action_to_id`, `NUM_ACTIONS = 406`) -- eine Log-ID ist damit
unmittelbar mit den Policy-Logits vergleichbar, nicht nur ein Replay-Schluessel.
Seither traegt auch jeder `valid_moves`-Eintrag seine `id`.

**Gemessen** (par.7 der Registrierung):

| | |
|---|---|
| frische Partie | 245/245 Zeilen exakt, **52/52 Stein-Zuege ueber die ID**, 0 ueber den Text |
| `game_20260818_200516_seed585858` | war Abbruch bei Zeile 16, **jetzt 321/321** |
| `game_20260818_195111_seed558549` | 327/327 (unveraendert) |
| alte Elo-Logs | unveraendert unreplaybar (Seed reproduziert den Fabrik-Aufbau nicht) |
| `cargo test --release` | 447 bestanden |

**Drei Dinge, die man wissen muss, bevor man darauf aufbaut:**

1. **Die ID ist NICHT eindeutig.** `moon_order` fliesst nicht ein
   (`net_mcts.rs:1824`), und Kuppel-Zuege zerfallen in Slot + Rotation --
   deshalb `id_rotation` und die kanonischen Felder als Disambiguierung. Die
   gegenteilige Annahme stand in der Registrierung und war falsch (par.7.2).
2. **Der Haken sitzt an der API-Grenze (`py.rs`), nicht in `apply_drafting`**
   (Heisspfad der Suche). Wer eine `apply_*`-Methode ergaenzt, ruft
   `log_and_apply` statt `apply_drafting`. Zwei bewusste Luecken: `apply_pass`
   (schreibt nie ins Log) und der Stapel-Zug der Netz-KI -- beide vom Textweg
   gedeckt.
3. **`tools/plate_points_from_arena.py` musste gehaertet werden.** Die
   par.4-Sperre hat einen echten Bruch gefunden: eine `#`-Zeile im
   Endwertungs-Block leerte `je_kriterium` still. Jetzt filtert der Leser
   `#`-Zeilen wie `analyze_game_log.load_log` es immer schon tat.

**Dateischnitt nebenbei:** die Report-Schicht liegt jetzt in
`tools/game_log_report.py` (`analyze_game_log.py` hatte die Groessen-Ratsche
gerissen, Nutzer-Entscheid 2026-08-18: auslagern statt Basislinie neu legen).
Reine Darstellung, kein Replay -- die drei Partien liefern unveraenderte Reports.

**Nebenbefund, korrigiert:** `analyze_game_log._run_loop` gab auf dem
Erfolgspfad ein Tupel statt des Zeilenindex zurueck -- die "wie weit kam der
Replay"-Zahl im Report war dort bedeutungslos (Altbestand, `HEAD:785`).

---

## TASK-INDEX (nur OFFEN/LAUFEND)

| Task | Status |
| --- | --- |
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: braucht >=6 arena-entschiedene Paare (Stand ~3); Kandidaten-Metriken werden je Gating mitgefuehrt. `PREREG_post34_package.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT

**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die v21-Task-Queue.**
`PREREG_v22_window.md`: gleiche Form wie v21 (29.450 gesamt), juengster
Value-Posten 3.550 v19wdl-Rest + 1.450 v19wdlsw, Schwarm bleibt 74 %.
**Ab v22 ist die Rotationsregel stationaer.** Gating-H0-Vorbehalt: neuer
Batch desselben Generators braucht Suffix (`v20wdlb`).
**Hinweis 2026-08-14**: der Ownership-Korpus ist KEIN v22-Fenster -- er liegt
ausserhalb der Rotation (`data/ownership_corpus/`, additiv via
`--extra-data-dir`) und aendert diese Halde-Entscheidung nicht.

---

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
  PREREG_v21_window.md, dort korrigiert).
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
  (PREREG_aggression_style_measurement/PREREG_denial_tiebreak).

- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).

- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).

- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).

- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blind_spot.md`, Tasks E/F/G dazu
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
  Konjunktionen, Breite an config.py:117-118 + Label-Bauer verifiziert
  2026-08-14); `OWNERSHIP_WEIGHT` steht in `config.py` weiter auf 0 --
  der Champion-Kopf ist untrainiert. Naechster Lauf mit Gewicht 0,2 +
  `--conjunction` ist der Korpus-Trainingslauf (PREREG_ownership_corpus.md).
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
3. **Das Label ist EGOZENTRISCH -- damit ist "Fabriken aushungern"
   strukturell unerreichbar** (Nutzer-Frage 2026-08-16 "was ist mit
   fabriken aushungern gemeint", Code am selben Tag geprueft). Die
   Mond-Stapelreihenfolge ist der EINZIGE Hebel im Spiel, mit dem man dem
   Gegner gezielt nur vergiftete Optionen hinterlaesst: bei kleinen
   Fabriken bestimmt der nehmende Spieler die Reihenfolge, und spaeter ist
   nur die OBERSTE Fliese nehmbar (docs/engine_manual.md, Phase 1 B). Wer
   das steuert, kann den Gegner in Farben zwingen, die seine Musterreihen
   ueberlaufen lassen -- Strafpunkte ohne eigenen Einsatz, und der Zwang
   ist strukturell (die Runde endet erst, wenn alles leer ist; wer keine
   gueltige Aktion hat, MUSS passen).
   **Das Netz hat den Kopf dafuer, aber nie das Ziel**: `moon_order_target`
   (`self_play.rs:634`) probiert Reihenfolgen durch und bewertet jede mit
   `solve_round_final_score(state, pi)` (`tiling_solver.rs:494`) -- also
   ausschliesslich dem EIGENEN Rundenendstand. Der Gegner kommt in der
   Bewertung nicht vor. Der Kopf kann Aushungern also nicht lernen, egal
   wie gut er wird.
   **Billiger Zuschnitt, falls je angegangen**: nur das Label aendern
   (eigener Rundenendstand MINUS Gegner-Rundenendstand, oder als eigener
   Arm), Bau bleibt unberuehrt. Vorbehalt: das ist eine neue
   Stoerungs-Wette, und Stoerung hat in diesem Projekt zweimal verloren
   (k6-Kuppeldraft, Farbzaehlung v1) -- vorher gehoert eine billige
   Diagnose davor, ob die Reihenfolge-Freiheit ueberhaupt genutzt wird
   (Praezedenz #39: Rotation/Position der Startkuppel waren tote
   Freiheitsgrade). Herkunft der Idee: Reddit-Rueckfrage eines Spielers
   nach adversarialen Faellen.

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
