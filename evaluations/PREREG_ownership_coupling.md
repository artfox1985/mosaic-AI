<!-- STATUS: OFFEN | Frage: Wie kommt der Ownership-Kopf VERNUENFTIG in die Zugwahl (Gumbel-Draft) und in das Tiling -- nachdem drei Eingriffe an Prior, Korpus und Formel nichts bewegt haben? | Beleg: offen -->

# Vorregistrierung: Kopplung des Ownership-Kopfes an Draft und Tiling

**Anlass (Nutzer-Auftrag 2026-08-18):** *"überleg dir nochmal tiefgehend wie wir
den ownership head vernünftig in die züge und ins tiling bekommen"* — und
ausdrücklich **ohne harte Rangregeln** (*"wir pfuschen nicht mit harten
rangregeln herum"*). Beide Pfade gehören zusammen und werden hier gemeinsam
behandelt.

**Was vorausgeht:** Drei Wege sind durchgemessen und keiner trägt — Regler in
Produktform (`PREREG_gate_c_consumer_sweep.md` par.15, Replikation
`PREREG_gate_c_d1_replication.md`), Policy-Destillation warm und kalt
(`PREREG_corpus_distillation.md` par.10.7/10.9), Konjunktionsform
(`PREREG_conjunction_terms.md` par.9). Was überlebt, ist die Zurechnung: der
Prior BIETET den Bauzug an (4,91x Gleichverteilungsmasse, 129/130 Held-out),
der Regler GREIFT ins Spiel ein (402/407 Partien laufen anders) — und es
entsteht keine Platte.

---

## par.1 DIE FRAGE

Nicht *ob* der Kopf etwas weiß, sondern *ob sein Wissen die Entscheidung
erreicht, an der es wirken müsste*. Zwei Entscheidungen, zwei verschiedene
Maschinen:

| Entscheidung | Wer entscheidet | Modul |
|---|---|---|
| **Draft** — welche Fliesen/Kuppelplatte nehme ich | Gumbel-Suche über Netz-Priors | `net_mcts.rs` |
| **Tiling** — WO landet die gedraftete Farbe | ein **Solver**, nicht die Suche | `tiling_solver.rs` |

Die zweite Zeile ist der Punkt, den drei Preregs übersehen haben. Sie steht als
Diagnose bereits im Code (`tiling_solver.rs:990`):

> *"WO die gedraftete Farbe landet, entscheidet der Solver, nicht die Suche —
> in Runde 1 vollstaendig plattenblind, in den Runden 2-4 wirkt der Netzwert nur
> als Faktor auf den nach Platzierungspunkten gebildeten Kandidatenwert. Ein
> Ownership-Verbraucher, der nur am Blatt haengt, erbt genau diese Blockade."*

Der Plattenbau ist eine **Tiling**-Handlung. Ein Regler, der nur am Blattwert
der Draft-Suche hängt, kann ihn strukturell nicht auslösen.

---

## par.2 VERIFIZIERTER STAND BEIDER VERBRAUCHER (2026-08-18, mit Prüfstelle)

### par.2.1 Draft-Pfad — Blattwert-Formung

`apply_ownership_shaping_full` (`net_mcts.rs:1642`), Laufzeit-Wrapper `:1711`:

```text
shift += gew[k] * tanh(e[k] / WERTUNG_SHAPING_SCALE)
out[i] = clamp(value[i] + w_own * shift, 0.0, 1.0)
```

- `e[k]` = `expected_plate_points` bzw. `..._conj` — ein **NIVEAU**, kein Zuwachs.
- `WERTUNG_SHAPING_SCALE = 50.0` (`net_mcts.rs:1059`), **gemeinsam für alle acht
  Kriterien**.
- `gew[k]` = Kriteriengewichte, je Kriterium einstellbar.
- Dosis `w_own` = `MOSAIC_OWNERSHIP_W`, Default 0,0.

### par.2.2 Die Suche ist GUMBEL, nicht PUCT

`USE_GUMBEL_SEARCH = true` (`net_mcts.rs:2869`); der PUCT-Pfad ist Legacy
(`:2525`). Wurzelentscheid: `logit + gumbel + σ(q)` mit

```text
σ(q) = (c_visit + max_N) · c_scale · q      c_visit = 50 (:2697), c_scale = 1,0 (:2727)
```

**Korrektur zur Sitzungshistorie:** in der Analyse vom 2026-08-18 wurde
zunächst PUCT behauptet und daraus argumentiert. Falsch, vom Nutzer korrigiert.
Die Schlussfolgerung "am Prior ansetzen" überlebt, aber mit anderer Begründung:
bei Gumbel wird die Wurzel-Kandidatenmenge aus der Policy **gezogen** — ein Zug
außerhalb der Top-m existiert für die Suche nicht.

### par.2.3 Tiling-Pfad — schon in der richtigen Form

- `ownership_tiling_weight()` / `MOSAIC_OWNERSHIP_TILING_W`, Default 0,0
  (`tiling_solver.rs:1006`, `:1014`).
- `ownership_marginals()` (`:1054`) ruft `scoring::marginal_plate_points` —
  **marginale Feldwerte, also bereits Inkrementform.**
- Kandidatenwert (`:1079`): `punkte(Abschluss) + w * calculate_end_scoring(...).total`
  — **ADDITIV und ausdrücklich so gebaut**, damit der Plattenwert
  Platzierungspunkte überstimmen *kann*; eine Multiplikation würde bei
  0-Punkte-Abschluss jeden Plattenwert auf 0 ziehen.
- Kriteriengewichte `MOSAIC_TILING_PLATTEN_GEW` (`:1113`), Default 1,0.
- Rundenfenster `platten_branch_applies` = **1..=4** (`:1068`).

**Und die Begründung der Kriteriengewichte dort ist derselbe Befund, den die
Draft-Seite noch nicht gezogen hat** (`:1108`, gemessen 2026-08-12):

> *"mit `.total` ueber alle Kriterien fiel der vertikale Plattenwert auf 0,35
> gegen 2,10 im Bezug. Ursache ist die Groessenordnung des Spezialfeld-Postens
> -- im Mittel -11,70. Er ueberdeckt jede Geometrie."*

---

## par.3 DIE RECHNUNG — warum k6 durchkommt und k1/k2 nicht

**Verifiziert** sind die Konstanten in par.2. **Hergeleitet** ist alles Folgende;
`max_N` ist eine ANNAHME (50 bei 400 Sims), nicht gemessen.

Δq = Änderung des geformten Blattwerts durch eine Handlung, bei Dosis D1
(`w_own` = 0,1), anschließend im Gumbel-Score um `(c_visit + max_N)·c_scale ≈ 100`
verstärkt und gegen Gumbel-Rauschen (Standardabweichung ≈ 1,28) gestellt:

| Handlung | e-Änderung | Δq | im Gumbel-Score | Anteil am Rauschen |
|---|---:|---:|---:|---|
| ein Spezialfeld mehr gefüllt (k6) | +3 | 0,0057 | 0,57 | **~45 %, wirksam** |
| eine Fliese in eine Spalte (k1) | +0,109 | 0,0002 | 0,02 | ~1,6 %, hoffnungslos |

Die Spalten-Zeile ist die Produktkollaps-Vorhersage in Wert-Einheiten: das
Inkrement eines einzelnen Feldes am Produkt von sechs Wahrscheinlichkeiten ist
~10⁻⁴ auf einer Skala, deren Rauschen ~1 ist. **Das gemeinsame `/50` bewirkt,
dass ein Kriterium mit −11,7 Niveau (k6) durchkommt und eines mit 0,9 Niveau
(k1) verschwindet** — nicht die Form, sondern die Skala.

Das deckt sich mit jeder Messung des 2026-08-17/18: k6 bewegte sich (+0,16),
die langen Ketten nie, und die Konjunktionsform half nicht, weil sie die Form
tauschte und die Skala ließ.

---

## par.4 DIE ASYMMETRIE, UM DIE ES GEHT

| | Tiling | Draft/Blatt |
|---|---|---|
| Form | **marginal** | **Niveau** |
| Skala | je Kriterium | je Kriterium **plus gemeinsames tanh(/50)** |
| Verknüpfung | additiv, überstimmungsfähig | additiv, dann `clamp(0,1)` |

Die Tiling-Seite hat 2026-08-12 genau die Lehre gezogen, die der Draft-Seite
fehlt. **Der Entwurf besteht deshalb nicht aus einer neuen Idee, sondern darin,
die Draft-Seite auf die Form zu bringen, die im selben Baum schon steht.**

---

## par.5 WAS GEAENDERT WIRD — drei Bausteine, keine Rangregel

**B1 — Inkrement statt Niveau.** Auf dem Draft-Pfad mit Φ(s′) − Φ(s) formen
statt mit Φ(s). Potentialbasiertes Shaping (Ng/Harada/Russell 1999) lässt die
optimale Politik beweisbar unverändert, liefert aber dichte Führung. Der Nutzen
ist nicht Ästhetik: heute hängen Sockel und Signal an EINEM Knopf, jede
Dosiserhöhung verstärkt vor allem den Sockel und drückt gegen `clamp` — genau
das Muster der monoton fallenden Siege in Tor C.
*Hinweis zur Umsetzung:* `marginal_plate_points` liefert Marginale JE FELD, der
Draft-Pfad braucht einen Skalar je Zug. Nicht drop-in, aber dieselbe Quelle.

**B2 — Skala je Kriterium statt gemeinsames /50.** Jedes Kriterium auf sein
eigenes typisches Inkrement normieren, damit ein 7-Punkte-Spaltenschritt und ein
3-Punkte-Spezialfeld vergleichbar ankommen. Das ist die Übertragung von
`MOSAIC_TILING_PLATTEN_GEW`s Begründung auf den Draft-Pfad.

**B3 — Auf die Wurzel-Logits, nicht nur in completed-Q.** Bei Gumbel ist der
Wurzelentscheid `logit + gumbel + σ(q)`. Das Plattensignal dort additiv
einzuspeisen ist ein weicher, dosierbarer Term im selben Raum wie die
Policy-Logits — das Rauschen kann ihn weiter überstimmen, es wird kein Rang
erzwungen. Begründung aus der Messung: der Prior bietet den Bauzug bereits
dominant an (4,91x), gespielt wird er nicht — der Wert-Backup überstimmt ihn.

**Reihenfolge:** B1+B2 gemeinsam (sie sind dieselbe Änderung an einer Stelle),
B3 getrennt danach, damit die Zurechnung erhalten bleibt.

---

## par.6 MECHANISCHE VORPRUEFUNG — vor jeder Arena-Minute

Lehre aus dem 2026-08-17: das installierte Wheel war 25 h älter als der
Engine-Code, und ohne die Prüfung hätte die Arena die alte Engine gefahren.

1. `.pyd`-Zeitstempel gegen `engine/src/*.rs` halten, Wheel bauen und
   installieren.
2. Paritätsprobe bei Default 0 — muss byte-identisch bleiben.
3. **Determinismus zuerst:** derselbe Arm zweimal auf identischen Seeds, muss
   8/8 gleich sein. Dann Reglerwirkung: muss abweichen. Umgekehrt beweist die
   zweite Prüfung nichts.
4. **Neu und hier entscheidend:** Δq je Handlung MESSEN, nicht rechnen. An
   konstruierten Stellungen den geformten Blattwert vor und nach der Handlung
   ausgeben, für k1 und k6. Erreicht das Inkrement nicht mindestens die
   Größenordnung des Gumbel-Rauschens geteilt durch die Verstärkung, ist die
   Arena Verschwendung — dann greift B2 noch nicht.

---

### par.6.1 ERGEBNIS DER VORPRUEFUNG (2026-08-18) — das Inkrement reicht NICHT

Gemessen mit `tools/probes/ownership_shift_magnitude.py`: 60 Drafting-Stellungen
aus dem Held-out-Ownership-Korpus, `b18_best` @400 Sims, derselbe Seed je
Stellung, zweimal gesucht (Regler aus / D1 mit Konjunktionsform). Die Zahlen
kommen aus `net_search_state_json_trace` (`gumbel_trace`, je Kandidat `q`,
`sigma_q`, `score`, `visits`) — also aus der Engine, nicht aus einem
Python-Nachbau der Formel.

| Groesse | Wert |
|---|---:|
| \|Delta q\| je Kandidat, Mittel / Median / max | 0,0026 / 0,0016 / 0,0202 |
| **Spannweite des Delta je Stellung** (das UNTERSCHEIDENDE Signal) | **0,0024** |
| q-Spanne der Suche selbst (Bezug) | 0,0781 |
| **Anteil** | **3,1 %** |
| Stellungen mit gewechseltem q-Bestkandidaten | **0 von 58** |

**Der Regler wirkt** (max 0,0202, also kein Wheel-/Env-Alarm), **aber er
verschiebt fast alle Kandidaten GLEICH.** Uebrig bleibt eine unterscheidende
Restgroesse von 3 % dessen, was die Suche ohnehin an Wertunterschieden erzeugt —
und sie kippt in 58 Stellungen keine einzige Wurzelentscheidung. Das ist die
Vorhersage "Niveau statt Inkrement" aus par.3, hier gemessen.

**Nach der Vorabregel in par.6 Punkt 4 ist die Arena damit gesperrt, bis B1+B2
gebaut sind.** Groessenordnung des Bedarfs: das unterscheidende Signal muesste
etwa 10- bis 30-fach wachsen, um mit der Eigen-Spreizung der Suche vergleichbar
zu sein.

**Zwei Korrekturen an par.3, beide durch die Messung:**

1. `max_N` ist **19,6**, nicht die angenommenen 50. Die Verstaerkung
   `(c_visit + max_N)·c_scale` betraegt also **69,6**, nicht 100.
2. Der Massstab "Gumbel-Rauschen 1,28" war fuer die Arena FALSCH. Dort gilt
   `add_root_noise=false` und damit `gumbel_scale=0` (`net_mcts.rs:3842`) — es
   gibt gar kein Rauschen. Richtiger Bezug ist die q-Eigenspreizung der Suche
   (0,078) bzw. die Log-Prior-Spreizung (5,58 gegen sigma_q-Spreizung 4,89,
   Verhaeltnis 0,88). Die Rauschgroesse gilt nur fuer Self-Play.

**Offener Widerspruch, ausdruecklich als ungeklaert markiert:** in der Arena
laufen 402 von 407 Partien anders als im Nullarm, hier kippt am Draft-Pol keine
einzige von 58 Wurzelentscheidungen. Zwei Erklaerungen, beide UNGEPRUEFT — der
**Tiling-Pol** (`MOSAIC_OWNERSHIP_TILING_W` = 0,3) traegt den Effekt, oder
winzige Verschiebungen kippen ueber ~100 Entscheidungen je Partie gelegentlich
doch. Das zu trennen ist die naechste Messung und aendert die Gewichtung von
B1-B3: traegt der Tiling-Pol allein, gehoert die Arbeit dorthin.

## par.7 MESSANORDNUNG

Wie `PREREG_conjunction_terms.md` par.6, damit die Zahlen daneben stehen:

| | |
|---|---|
| Checkpoint | `alphazero_v21-b18_best.onnx` @400 (140 breit, plattenfähige Policy) |
| Gegner | Champion `alphazero_v21_2d_brierbest.onnx` @400, Netz gegen Netz |
| Seeds | der 407er-Satz aus `distillation_seeds_main.txt` |
| Arme | N (Regler aus, liegt vor) · D1 Produktform (liegt vor) · **B1+B2** · danach **B1+B2+B3** |
| Blockgröße | 25 → nB=6 je Kriterium |
| Logs | `--log-games` ist PFLICHT, sonst sind k1/k2 nicht berechenbar |

---

## par.8 VORAB-ERFOLGSREGEL (wörtlich, vor der ersten Partie)

> **ERFOLG** heißt: **k1 oder k2** hebt sich signifikant auf Block-Ebene gegen
> die Produktform bei derselben Dosis (gepaart über den Seed, nB=6, zweiseitig
> p < 0,05, also |t| > 2,571) — **und** es gehen keine Siege signifikant gegen
> den Nullarm verloren (exakter zweiseitiger McNemar, p >= 0,05).

**k1/k2 und sonst nichts.** k3/k5/k6 bewegen sich schon unter der Produktform
und sind daher kein Nachweis. Diese Klausel ist gegenüber
`PREREG_conjunction_terms.md` par.7 unverändert übernommen — dort lautete sie
identisch auf k1/k2.

**NICHT-ERFOLG** heißt: k1 und k2 bleiben flach, obwohl par.6 Punkt 4 ein
Inkrement in wirksamer Größenordnung belegt hat. Dann ist die Kopplung
ausgeschlossen, und es bleibt die Ziel-Frage aus par.9.

---

## par.9 DIE UNGELOESTE FRAGE, die groesser sein kann als die Kopplung

Der Kopf sagt vorher, was **passieren wird**, nicht was **erreichbar wäre**. Er
ist auf realisierte Ownership aus Self-Play trainiert; in einem Zustand aus
normalem Spiel ist *"diese Spalte wird nicht fertig"* die RICHTIGE Vorhersage.
Als Wert benutzt, ist das selbsterfüllend: die Suche wird dorthin geführt, wo
die alte Politik schon war.

**Der Beleg, dass das kein Gedankenspiel ist:** der stärkere Kopf (w1-final)
machte den Verbraucher **inert** statt nützlicher (`PREREG_gate_c_consumer_sweep.md`
par.15, 91:91, b=c=18). Ein genaueres Beschreibungsmodell ist kein besseres
Ziel. Genau dieser Befund war bisher unerklärt.

**Zweiter Beleg, unabhängig:** bei k6 ist die Kopplung nachweislich stark genug
(par.3, ~45 % des Rauschens), und das Verhalten ist trotzdem falsch. Gemessen am
Nullarm — also mit ABGESCHALTETEM Regler — legt das Netz Spezialkuppeln bei
aktiver k6-Platte zu 62,8 % nach unten (gegen 42,3 % ohne die Platte) und räumt
die oberen Slots von 29,6 % auf 8,5 %. `docs/domain_knowledge.md` §8 verlangt
das Gegenteil: erzwungene Spezialkuppeln nach OBEN, weil sie dort an den
billigen Musterreihen hängen und fast von selbst schließen. Das Netz hat also
eine Anti-§8-Gewohnheit GELERNT; sie kommt nicht aus dem Verbraucher.

Wenn dieser Anteil überwiegt, helfen B1–B3 vor allem k1/k2, und k6 braucht eine
**Ziel-Änderung**: nicht *"wird Feld f gefüllt"*, sondern *"könnte ein Spieler,
der es anstrebt, Feld f von hier noch füllen"* — Erreichbarkeit statt
Realisierung. Das ist teuer (neue Labels) und wird erst registriert, wenn par.8
entschieden ist.

---

## par.10 ERGEBNIS (leer bei Registrierung)
