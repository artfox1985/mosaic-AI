<!-- STATUS: OFFEN | Frage: Wie kommt der Ownership-Kopf VERNUENFTIG in die Zugwahl (Gumbel-Draft) und in das Tiling -- nachdem drei Eingriffe an Prior, Korpus und Formel nichts bewegt haben? | Beleg: offen -->

# Vorregistrierung: Kopplung des Ownership-Kopfes an Draft und Tiling

> **FOKUS-REGEL (Nutzer 2026-08-18):** ab hier wird ausschliesslich **k1**
> bearbeitet. Registrierte "k1 oder k2"-Klauseln bleiben gueltig, werden aber auf
> k1 gelesen (strengere Lesart). Begruendung und Umfang: `evaluations/STATUS.md`,
> Abschnitt "FOKUS-REGEL".


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

**B4 — ORDINAL statt BETRAG (Nutzer-Vorschlag 2026-08-18). Ersetzt B1 und B2.**

*Begruendung aus der Messung:* der Kopf **rangiert gut und beziffert schlecht** —
Konjunktions-AUC 0,83-0,91 bei einem Brier nur 8-14 % unter der Grundrate
(`PREREG_ownership_selector.md` par.9.2, zitiert in `scoring.rs:486`). Ein
Signal mit diesem Profil als BETRAG zu verwenden ist die falsche Richtung, und
genau das tut der Verbraucher seit dem ersten Tag.

*Mechanik:* fuer die m Wurzelkandidaten die Plattenerwartung des Kopfes je
Kandidat bilden, in den **zentrierten Perzentilrang** in [-1, +1] umrechnen und
`w · Rang` additiv auf den Logit geben. `w = 0` ist bitgenau Bestandsverhalten.

*Warum das B1 UND B2 ueberfluessig macht:*

- **B2 (Skala je Kriterium) entfaellt**, weil eine Rangtransformation
  skalenfrei ist. k1s Unterschied von ~10⁻⁴ und k4s grosser Unterschied werden
  zur selben ordinalen Spreizung. Es muss keine Normierungskonstante je
  Kriterium geschaetzt werden — es gibt keine Skala mehr.
- **B1 (Inkrement statt Niveau) entfaellt ebenfalls**, und zwar exakt, nicht
  naeherungsweise: unter den Geschwistern EINES Knotens ist Φ(s) eine
  gemeinsame Konstante, also ist die Rangfolge von Φ(s′) identisch mit der
  Rangfolge von Φ(s′) − Φ(s). Der Rang implementiert die Inkrementform gratis.
  Das gilt, weil B4 an der WURZEL ansetzt (wie B3) und nicht am Blatt.

*Verhaeltnis zu B3:* B4 ist die ordinale Fassung von B3 — dieselbe Stelle
(Wurzel-Logits), dieselbe additive, dosierbare Form, nur der ORDNUNGSanteil des
Kopfsignals statt seines Betrags.

*Abgrenzung zur verworfenen Rangregel:* es wird nichts erzwungen. Prior und
Wert koennen den Term ueberstimmen, `w` dosiert ihn, und er ist ein Merkmal im
selben Raum wie die Policy-Logits — nicht die Anweisung "nimm den
plattenbauenden Zug".

*Unabhaengiges Argument:* in diesem Projekt haben die ORDINALEN Masse die Arena
vorhergesagt (Kendall-Tau und Prior-Masse auf die Orakel-Top-3, 7 von 7,
`project_oracle_metrics_validated`), waehrend die kardinalen R²-Masse es nicht
taten.

**DAS RISIKO, und es ist ernst:** heute schuetzt die winzige Groesse davor,
Unsinn einzuspeisen — ist der k1-Unterschied zwischen Geschwistern reines
Zahlenrauschen, richtet ein Term von 10⁻⁴ keinen Schaden an. Die
Rangtransformation nimmt genau diesen Schutz weg und skaliert Rauschen auf
VOLLE Staerke. Aus einem harmlosen Nullsignal wuerde ein kraeftiges
Falschsignal. Deshalb die Sperre in par.6.3.

**Reihenfolge (ERSETZT 2026-08-18):** zuerst die Sperre par.6.3, dann **B4**,
danach erst entscheiden, ob B3 in kardinaler Form ueberhaupt noch gebraucht
wird. B1 und B2 sind durch B4 aufgehoben — nicht verworfen, sondern subsumiert.

*(historisch, vor B4:)* B1+B2 gemeinsam (sie sind dieselbe Änderung an einer Stelle),
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

### par.6.2 KORREKTUR VON par.6.1 (2026-08-18) — die Sonde mass die falsche Groesse

**Nutzer-Einwand, und er traegt:** *"es müssen entscheidungen am draft pool wie
auch am tiling pool kippen. tiling kann nur das legen was drafting vorbereitet
hat."* Genau daran zerbricht par.6.1s Lesart.

**Der Fehler:** die Sonde verglich den argmax von `q`. Gumbel waehlt aber ueber
`score = logit + sigma_q`. Das "0 von 58 Wurzelwechseln" beantwortet damit eine
Frage, die niemand gestellt hat, und die Folgerung "der Draft ist inert" war
falsch.

**In-situ gemessen an den Arena-Logs** (b18-Seite, Nullarm gegen Konjunktion D1,
407 gepaarte Partien, Draft-Folge = gezogene Fliesen UND gelegte Kuppelplatten):

| | |
|---|---:|
| Draft-Entscheidungen je Partie | 17,8 |
| Partien mit ABWEICHENDER Draft-Folge | **400 / 407** |
| erste Abweichung, Median / Mittel | 4 / 4,95 |
| Kipp-Rate je Draft-Entscheidung (hergeleitet, geometrisch) | **~17 %** |

**Der Draft kippt also, rund jede sechste Entscheidung.** Damit loest sich auch
der "offene Widerspruch" aus par.6.1 auf — es brauchte keinen Tiling-Pol als
Erklaerung, und der dortige Satz "traegt der Tiling-Pol allein, gehoert die
Arbeit dorthin" ist gegenstandslos.

**Was daraus folgt, ist eine bessere Diagnose als die alte:** die STAERKE reicht,
die RICHTUNG stimmt nicht. Der Regler lenkt 17 % der Draft-Entscheidungen um,
und er lenkt sie nachweislich dorthin, wo ein brauchbares Marginal existiert —
k3 +1,59 (Block-t 2,58) und k5 +0,34 (Block-t 2,79) heben sich signifikant. Bei
k1/k2 ist das Marginal am Produkt von sechs Feldwahrscheinlichkeiten praktisch
null, also fuehrt kein Kipp dorthin.

**B1 und B2 ueberleben, mit GEAENDERTER Begruendung.** Nicht mehr "das Signal ist
zu schwach" — es ist stark genug, um Verhalten zu aendern. Sondern: **der Anteil
von k1/k2 am Signal ist ~0.** B2 (Skala je Kriterium) ist damit nicht die
Lautstaerke-Schraube, sondern die Verteilungs-Schraube. B1 (Inkrement statt
Niveau) bleibt richtig, weil der gemeinsame Sockel die unterscheidende
Restgroesse klein haelt (gemessen: 0,0024 von 0,0026 mittlerer Verschiebung ist
Sockel).

**Was von par.6.1 GUELTIG bleibt:** die beiden Korrekturen an par.3 — `max_N` ist
19,6 statt 50 (Verstaerkung 69,6 statt 100), und der Massstab "Gumbel-Rauschen
1,28" gilt in der Arena nicht, weil `add_root_noise=false` die Samples
abschaltet. Ebenso gueltig: die gemessene Aufteilung des Reglerbeitrags in einen
fast gemeinsamen Sockel und eine kleine unterscheidende Restgroesse.

### par.6.3 SPERRE VOR B4 — traegt die Geschwister-ORDNUNG ueberhaupt Signal?

Die AUC 0,83-0,91 gilt fuer die Vorhersage, OB ein Feld gefuellt wird. Sie sagt
NICHTS darueber, ob der Kopf die Geschwisterzuege EINES Knotens sinnvoll ordnet.
Genau das braucht B4 aber, und genau dort liegt sein Risiko.

**Stufe 1 — Stabilitaet (billig, kann die Idee sofort toeten).** Dieselbe
Kandidatenmenge zweimal bewerten, mit unterschiedlichem
Determinisierungs-Seed der verdeckten Information. Gemessen wird Kendall-Tau
zwischen den beiden k1- bzw. k2-Ordnungen.

> **VORAB-REGEL:** liegt das mittlere Tau der k1-Ordnung ueber die Stellungen
> nicht **signifikant ueber 0** (einseitig, p < 0,05), ist die Ordnung
> seed-instabil und damit Rauschen. **Dann wird B4 NICHT gebaut** — die
> Rangtransformation wuerde dieses Rauschen auf volle Staerke heben.

Zusaetzlich als Nebenbedingung protokollieren: die numerische Spreizung der
k1-Erwartung ueber die Geschwister. Liegt sie im Bereich der
Gleitkomma-Aufloesung, ist die Ordnung schon deshalb bedeutungslos.

**Stufe 2 — Informativitaet (nur wenn Stufe 1 haelt).** Kendall-Tau zwischen der
Kopf-Ordnung der Geschwister und der ORAKEL-Ordnung derselben Geschwister
(Orakel = tatsaechliches Endbrett-Ergebnis des jeweiligen Kandidaten). Vorbild
und Werkzeugkette: dieselbe, mit der `kendall_tau` als Arena-Praediktor
validiert wurde.

> **VORAB-REGEL:** Tau der k1-Ordnung gegen das Orakel muss signifikant > 0
> sein. Ist es das nicht, ordnet der Kopf die ZUEGE nicht, auch wenn er die
> FELDER gut ordnet — und B4 haette nichts zu transportieren.

**Warum diese Sperre vor dem Bauen kommt und nicht danach:** sie ist billig
gegen einen Arena-Arm, und sie beantwortet die einzige Frage, an der B4 haengt.
Dasselbe Muster hat par.6 Punkt 4 fuer die Arena schon einmal richtig gemacht.

#### par.6.3.1 ERGEBNIS STUFE 1 fuer k1 (2026-08-18): BESTANDEN

`tools/probes/sibling_order_stability.py`, `b18_best` @400 Sims. 40 Stellungen
aus **40 verschiedenen Partien**, je eine, ab **Runde 2**, k1-Platte aktiv.
Kopf-Erwartung je Kandidat als `q_an - q_aus` bei `MOSAIC_OWNERSHIP_GEW` nur auf
k1 — streng monoton in `e[1]`, also ordnungsgleich, ohne
`expected_plate_points` nachzubauen.

| | k1 |
|---|---:|
| Kandidaten je Stellung | 12,0 |
| **Kendall-Tau zwischen zwei Determinisierungs-Seeds** | **+0,942** (std 0,102) |
| t gegen 0 | +58,2 (Schwelle 1,68) |
| numerische Spreizung des Deltas | 1,07e-03 |

Beide Bedingungen halten: die Ordnung uebersteht eine komplette Neuziehung der
verdeckten Information nahezu unveraendert, und die Spreizung liegt dreizehn
Groessenordnungen ueber der Gleitkomma-Aufloesung. **Es ist kein Zahlenrauschen,
das eine Rangtransformation verstaerken wuerde.**

**Die inhaltliche Aussage:** der Kopf HAT bei k1 eine stabile Meinung darueber,
welcher Geschwisterzug besser ist — sie ist nur so klein beziffert (1,07e-03 auf
einer q-Eigenspreizung von 0,078, par.6.1), dass sie in der Wertaddition
untergeht. Genau die Konstellation, fuer die B4 gebaut waere.

**Vorbehalt, der bleibt:** Stufe 1 zeigt STABILITAET, nicht RICHTIGKEIT. Eine
stabil falsche Ordnung bestuende diesen Test genauso. Dafuer ist Stufe 2 da.

##### Zwei Methodenfehler auf dem Weg, beide korrigiert

1. **Pseudoreplikation.** Der erste Sampler nahm die ersten n Drafting-
   Stellungen in DATEIREIHENFOLGE — alle 40 kamen aus EINER Partie mit fester
   Plattenkombination (7,1,6). Das damals gemeldete "Tau +0,629, t +12,78" ist
   damit **zurueckgezogen**: 36 korrelierte Stellungen sind keine 36
   Stichproben. Nebenwirkung derselben Ursache: k2 war in jener Stichprobe NIE
   aktiv, das "kein verwertbares Paar" war ein Konstruktionsfehler und kein
   Nullbefund. Jetzt: nach `game_id` gruppiert, eine Stellung je Partie,
   Kriterium muss in `scoring_tile_ids` liegen.
2. **OnceLock.** `MOSAIC_OWNERSHIP_W` wird EINMAL je Prozess gelesen. Der erste
   Versuch fuhr alle vier Laeufe mit derselben Dosis, das Delta war ueberall
   null. Zwei Dosen brauchen zwei Prozesse — steht jetzt im Sonden-Kopf.

##### BEIFANG, nicht gesucht: der Regler ist in RUNDE 1 wirkungslos

Auf 40 von 40 Runde-1-Stellungen ist `q` mit und ohne Regler **bitgleich**
(Delta exakt 0,000). Ab Runde 2 wirkt er (Spreizung ~1e-03). **Ursache
UNGEPRUEFT** — ein Rundentor an `apply_ownership_shaping_full` gibt es nicht.

Die Parallele ist auffaellig: `tiling_solver.rs:990` sagt ueber die
TILING-Seite *"in Runde 1 vollstaendig plattenblind"*. Gilt dasselbe fuer den
Draft-Pol, ist der Verbraucher in der GANZEN ersten Runde auf beiden Seiten
abwesend. Das ist kein Detail: die Kuppelplatten-Wahl der ersten Runde legt
fest, welche Spezialfelder man sich einhandelt, und `docs/domain_knowledge.md`
§8 haengt genau daran. **Eigene Messung noetig, bevor daraus etwas gefolgert
wird.**

#### par.6.3.2 ERGEBNIS STUFE 1 fuer k2 (2026-08-18): BESTANDEN — Stufe 1 damit vollstaendig

Gleiche Anordnung wie par.6.3.1, 40 Stellungen aus 40 verschiedenen Partien ab
Runde 2, k2-Platte aktiv (Korpus `selfplay_v21_own_*`, k2 liegt in 230 von 600
geprueften Partien — der frueher gemeldete Fehlschlag lag allein am alten
Sampler).

| | k1 | k2 |
|---|---:|---:|
| Kandidaten je Stellung | 12,0 | 11,8 |
| **Kendall-Tau ueber zwei Determinisierungs-Seeds** | **+0,942** | **+0,943** |
| t gegen 0 | +58,2 | +50,4 |
| numerische Spreizung des Deltas | 1,07e-03 | **3,73e-04** |

> **VORAB-REGEL par.6.3 Stufe 1: fuer k1 UND k2 BESTANDEN.** B4 ist nicht durch
> Rauschen gesperrt.

**Die letzte Zeile ist das Argument fuer B4 in einer Zahl:** k2 ordnet genauso
stabil wie k1 (Tau 0,943 gegen 0,942), bei **einem Drittel der Groesse**. Betrag
und Information laufen auseinander. Eine Wertaddition sieht nur den Betrag und
verschenkt die Information; eine Rangtransformation sieht nur die Ordnung und
nimmt sie mit. Das ist keine Herleitung mehr, sondern gemessen — und es ist das
vierte unabhaengige Argument fuer B4, neben dem AUC-Brier-Profil, dem Wegfall von
B1/B2 und der Gegenstandslosigkeit des Nenners.

**Bezug zu `PREREG_shaping_scale_per_round.md` (parallele Sitzung, 2026-08-18):**
dort wird derselbe Mangel von der anderen Seite angegangen — `WERTUNG_SHAPING_SCALE`
ist fest 50, waehrend der Punktestand nach Runde 1 bei 4 liegt (22 Arena-Logs:
Anteil des Endstands 8,3 % nach Runde 1, 32,7 % nach Runde 3). Die beiden Wege
schliessen sich nicht aus: **jener justiert den Betrag rundenweise, B4 verzichtet
auf den Betrag.** Traegt B4, bleibt der rundenabhaengige Nenner nur fuer den
HEURISTISCHEN Pol noetig, nicht fuer den Ownership-Pol.

**WAS JETZT NOCH FEHLT — Stufe 2.** Stabilitaet ist nicht Richtigkeit. Eine
stabil falsche Ordnung haette beide Tests bestanden. Vor dem Bauen von B4 fehlt
also der Vergleich der Kopf-Ordnung gegen die ORAKEL-Ordnung derselben
Geschwister, mit der Vorabregel aus par.6.3 Stufe 2.

#### par.6.4 ERGEBNIS: `E` IST RUNDENKONSTANT — der Nenner ist ~50x zu gross (2026-08-18)

`tools/probes/shaping_scale_e_distribution.py`, `b18_best`, 600 Drafting-
Zustaende aus **600 verschiedenen Partien** des Held-out-Satzes `data/holdout`
(je Partie und Runde einer), 120 je Runde. Feldindizierung aus `scoring.rs:422/432`
uebernommen, nicht geraten.

| Runde | Median E(k0) | Median E(k1) | Median E(k2) | 90 %-E/SCALE_r max |
|---|---:|---:|---:|---:|
| 1 | 1,362 | 0,082 | 0,038 | 0,397 |
| 2 | 1,335 | 0,081 | 0,026 | 0,217 |
| 3 | 1,403 | 0,082 | 0,025 | 0,135 |
| 4 | 1,375 | 0,097 | 0,025 | 0,099 |
| 5 | 1,174 | 0,116 | 0,023 | 0,057 |

**Drei Befunde:**

1. **`E` waechst ueber die Runden NICHT** (k2 faellt sogar). Der Grund ist
   strukturell: `wertung_progress` (Pfad A) misst FORTSCHRITT und waechst
   naturgemaess, der Ownership-Kopf (Pfad B) prognostiziert den ENDZUSTAND und
   wird im Verlauf *schaerfer*, nicht *groesser*.
2. **Der Nenner ist fuer Pfad B um Groessenordnungen zu gross.** `tanh(0,082/50)`
   = 0,0016 gegen eine q-Eigenspreizung der Suche von 0,078 (par.6.1) — Faktor
   ~50 zu leise, **in jeder Runde**.
3. **Damit ist B2 bezifferbar statt geschaetzt.** Damit der Shift die
   Groessenordnung der Suche erreicht, muesste der Nenner je Kriterium etwa
   **k0 ~17, k1 ~1, k2 ~0,3** lauten statt einheitlich 50.

**Die Runde-1-Frage aus par.6.3.1 ist beantwortet — negativ:** `E` ist dort
NICHT null (Median k1 0,082, wie in allen Runden). Die gemessene Bitgleichheit
von `q` mit und ohne Regler in Runde 1 hat also eine ANDERE Ursache als ein
verschwindendes `E`, und ein rundenabhaengiger Nenner wuerde sie NICHT heilen.
Ursache weiterhin ungeklaert.

**FOLGE FUER `PREREG_shaping_scale_per_round.md` (parallele Sitzung):** deren
par.6-Saettigungsregel ist ERFUELLT (alle 90-%-Quantile unter 0,40, Grenze 1,0).
Aber deren **Praemisse trifft fuer Pfad B nicht zu**: sie setzt `E ~ 0,7` in
Runde 1 auf `E ~ 7` in Runde 5 an (Faktor 10, aus dem PUNKTESTAND je Runde
abgeleitet) und leitet daraus ab, das Profil *"vergleichmaessigt den Einfluss
ueber die Runden"*. Gemessen ist `E` fuer Pfad B rundenkonstant — mit `SCALE_r`
wuerde der Shift bei k1 in Runde 1 auf 0,0195 steigen und in Runde 5 auf 0,0028
fallen, also **siebenfach zugunsten der frueher Runden kippen** statt zu
vergleichmaessigen. Fuer Pfad A (Fortschrittsgroesse) bleibt die Herleitung
plausibel. **Empfehlung: getrennte Profile, und fuer Pfad B statt eines
Rundenprofils eine Skala JE KRITERIUM** (Punkt 3 oben).

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
