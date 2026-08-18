<!-- STATUS: OFFEN | Frage: Bewertet der Champion die plattenbauenden Zuege eines Menschen systematisch FALSCH -- also mit dem falschen Vorzeichen, nicht nur zu leise? | Beleg: n=1 Partie (2026-08-18), Nutzer generiert weitere. -->

# PREREG: Der Orakel-Abstand in Menschenpartien

Stand **2026-08-18**, **ENTWURF.** Eine Partie liegt vor, der Nutzer erzeugt
weitere. Die Auswertungsregel wird HIER festgelegt, bevor die restlichen Partien
existieren.

> **FOKUS-REGEL (Nutzer 2026-08-18):** ausschliesslich **k1**. Andere Kriterien
> werden protokolliert, nicht verfolgt. Siehe `evaluations/STATUS.md`.

---

## par.1 DIE FRAGE, UND WARUM SIE NEU IST

Alle bisherigen Messungen dieser Kampagne setzen voraus, der Plattenwert sei
**zu leise**: der Verbraucher liefert ~3 % der q-Eigenspreizung
(`PREREG_ownership_coupling.md` par.6.1), der Nenner ist ~50x zu gross (par.6.4).
Daraus folgte durchgehend die Reparatur "lauter drehen".

**Die Anlassmessung stellt das in Frage.** Sie deutet darauf hin, dass der
Champion die plattenbauenden Zuege nicht bloss schwach unterscheidet, sondern
**deutlich negativ** bewertet. Ein zu leises Signal dreht man lauter; ein falsch
gerichtetes nicht.

---

## par.2 DIE ANLASSMESSUNG (n=1, 2026-08-18)

`static/log/game_20260818_214620_seed632335.log`, Mensch gegen Champion
`v21_2d_brierbest` @400, Platten **[3, 5, 1]**. Replay laeuft vollstaendig durch
(101 Entscheidungspunkte), Orakel-Modus von `tools/analyze_game_log.py` mit
demselben Champion @400.

| | Grundpunkte | k3 | k5 | k1 | Endstand |
|---|---:|---:|---:|---:|---:|
| **Mensch** | 66 | 6 | 11 | **14** | **97** |
| KI | 56 | **0** | 3 | **0** | 59 |

| | bewertete Zuege | Ø Δwin% zum Orakel-Top | Top-1 | Top-3 |
|---|---:|---:|---:|---:|
| Mensch | 33 | **3,7 pp** | 42 % | 64 % |
| KI | 43 | 1,3 pp | 49 % | 65 % |

**Die drei groessten Abweichungen des Menschen sind Farbsammel-Zuege:**

| Zug | gespielt | Rang beim Netz | Δwin% |
|---|---|---:|---:|
| R3 #49 | `3 (1+2)× gelb von F1, GF → Reihe 2` (+1 Strafleiste) | 15/40 | **−17,5** |
| R3 #54 | `3 (1+1+1)× schwarz von F1, F2, GF → Reihe 3` | 8/10 | **−13,8** |
| R4 #71 | `Kachel 2 → Slot (0,2)` | 13/37 | −13,7 |

**Der Mensch gewann 97:59.**

**Ein Detail, das die Deutung traegt:** bei Zug #65 (Runde 4) springt die
Siegwahrscheinlichkeit des Menschen auf **95,7 %**. Das Netz erkennt also die
gewonnene STELLUNG — nur nicht die ZUEGE, die dorthin fuehren. Das ist eine
Zuordnungs-Schwaeche im Wortsinn.

---

## par.3 DER KONFUND, DER DIE MESSUNG SONST WERTLOS MACHT

**Der Mensch koennte schlicht staerker sein.** Dann waere ein positiver
Δwin%-Abstand kein Plattenbefund, sondern ein Staerkebefund — das Netz
unterschaetzt jeden Zug eines besseren Spielers.

**Deshalb ist die Erfolgsregel eine DIFFERENZ innerhalb desselben Spielers**
(par.5): plattenrelevante Zuege gegen nicht-plattenrelevante Zuege DESSELBEN
Menschen in DERSELBEN Partie. Damit faellt die allgemeine Spielstaerke heraus.

Zweiter Konfund: **die Q-Schaetzung des Netzes schwankt stark.** In der
Anlasspartie liegen die groessten Zug-zu-Zug-Spruenge bei ±20 pp. Einzelne
Δwin%-Werte sind daher wenig wert; nur Mittelwerte ueber viele Zuege zaehlen.

---

## par.4 MESSANORDNUNG

**Datenquelle:** Menschenpartien gegen den Champion, gespielt ueber die App.
Voraussetzung: die Partie muss **replaybar** sein (`tools/analyze_game_log.py`
laeuft ohne Divergenz durch). Nicht replaybare Partien werden gezaehlt und
ausgeschlossen, nicht repariert.

**Auswertung je Partie:** Orakel-Modus mit dem Champion @400, derselbe wie der
Gegner in der Partie.

**Klassifikation der Menschen-Zuege** — operativ, vor der Messung festgelegt:

Ein Drafting-Zug heisst **k1-relevant**, wenn die genommene Farbe von mindestens
einer noch **unvollstaendigen und noch vollendbaren** Spalte des Ziehenden
gebraucht wird. Vollendbarkeit kommt aus
`mosaic_rust.plate_completability_json` (Wrapper um
`column_build::ist_spalte_vollendbar`), der Farbbedarf aus den offenen Zellen
dieser Spalten. Alle uebrigen bewerteten Zuege heissen **neutral**.

*Warum diese Definition:* sie ist aus dem Zustand berechenbar, braucht keine
Absichtsunterstellung, und sie benutzt genau das Praedikat, das auch das
Vollendbarkeits-Ziel speist (`PREREG_reachability_target.md`).

---

## par.5 VORAB-ERFOLGSREGEL (woertlich, vor der zweiten Partie)

> **BESTAETIGT** heisst: ueber mindestens **5 replaybare Partien** ist der
> mittlere Δwin% der **k1-relevanten** Menschen-Zuege signifikant groesser als
> der der **neutralen** Zuege desselben Menschen — gepaart je Partie,
> einseitig, p < 0,05. Zusaetzlich muss der Effekt in der **Mehrheit der
> Einzelpartien** dasselbe Vorzeichen haben.
>
> **NICHT BESTAETIGT** heisst: kein signifikanter Unterschied. Dann bewertet das
> Netz Menschenzuege allgemein schlechter (Staerke-Effekt), und die Kampagne
> bleibt bei "zu leise" statt "falsch gerichtet".

**Getrennt zu protokollieren, ohne Entscheidungsregel:** Endstand und
Plattenaufschluesselung je Partie, die Runde des Spaltenabschlusses, und die
Zuege mit dem groessten Einzelabstand.

**Mindestens 5 Partien**, weil bei ~30 bewerteten Menschen-Zuegen je Partie und
einer Q-Schwankung von ±20 pp ein einzelner Lauf nichts traegt.

---

## par.6 WAS DIESE MESSUNG NICHT ENTSCHEIDET

- **Ob der Plattenbau siegbringend ist.** Sie misst die BEWERTUNG des Netzes,
  nicht den Wert der Zuege. Der Kostenbefund dazu steht in
  `DOSSIER_ownership_head.md` Abschnitt 6a.
- **Ob eine Reparatur hilft.** Sie benennt die Richtung des Fehlers, nicht das
  Mittel.
- **Etwas ueber k2/k3/k5/k6.** Fokus-Regel; die Zahlen werden protokolliert.
- **Etwas ueber Runde 5.** Dort laeuft der exakte Loeser und wird vom Werkzeug
  bewusst nicht orakel-bewertet.

## par.7 ERGEBNIS (leer bei Registrierung, n=1 in par.2 als Anlass)

---

## par.8 UEBERGABE — fuer einen anderen Agenten

**Was schon steht (alles committet, Suite gruen):**

| Was | Stand |
|---|---|
| Replay + Zustands-Dump | `tools/analyze_game_log.py --dump-states` (Commit `21697ac`) |
| Orakel-Modus | im selben Werkzeug, `--model`/`--sims` |
| Vollendbarkeits-Praedikat nach Python | `mosaic_rust.plate_completability_json(state_json, player)` (Commit `7aefdac`) |
| Log-Emoji folgt der Quelle | Commits `9c92c66`, `86c1144` |
| GF-Mondbereich nicht mehr klickbar | Commits `266e29c`, `47d36f7` |

**Die zwei Befehle je Partie:**

    python -X utf8 tools/analyze_game_log.py --log static/log/<datei>.log         --no-oracle --dump-states <ziel>.jsonl

    python -X utf8 tools/analyze_game_log.py --log static/log/<datei>.log         --model models/alphazero_v21_2d_brierbest.onnx --sims 400         --out evaluations/game_analysis_<seed>_champion.md

Der erste liefert die Zustaende je Entscheidungspunkt (JSONL mit `turn`, `round`,
`kind`, `state`), der zweite den Orakel-Bericht mit Ø Δwin%, Top-1/Top-3 und den
groessten Abweichungen. **Der Orakel-Lauf dauert Minuten** — im Hintergrund
fahren.

**Was NOCH ZU BAUEN ist:** die Klassifikation aus par.4. Sie braucht je
bewertetem Menschen-Zug die genommene Farbe und den Zustand davor (beides im
Dump), dazu `plate_completability_json` fuer die noch vollendbaren Spalten und
deren offene Zellen. Ergebnis je Partie: zwei Mittelwerte (k1-relevant vs
neutral) und deren gepaarte Differenz.

**Nicht wieder aufrollen — heute geklaert und belegt:**

- Warum alte Elo-Logs nicht replaybar sind: der GF-Mond-Teilzug der alten UI
  (siehe `PREREG_action_id_logging.md` par.1). Nicht reparieren, ausschliessen.
- Warum das Log-Emoji frueher irrefuehrte: `execute_move` schrieb es hart auf
  Sonne. Behoben.
- Ob die Engine gegen das Regelwerk protokolliert: nein
  (`factory.rs::take_from_sun` haelt die Regel ein und zitiert sie).
- Ob ein veralteter Server-Prozess schuld war: nein, geprueft.

**Beruehrungspunkt mit anderen Arbeiten:** `PREREG_action_id_logging.md` baut
gerade IDs ins Log. Danach wird der Replay exakt statt heuristisch — die Befehle
oben bleiben gleich, nur die Ausschlussquote sollte fallen.
