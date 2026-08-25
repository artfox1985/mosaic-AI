<!-- STATUS: ENTSCHIEDEN | Frage: Hebt der Verbraucher die Zielkriterien k1/k2, wenn E_k aus den GELERNTEN Konjunktions-Ausgaengen kommt statt aus dem Produkt der 36 Feldwahrscheinlichkeiten? | Beleg: **ENTSCHIEDEN 2026-08-18, NICHT-ERFOLG.** Gebaut (MOSAIC_OWNERSHIP_CONJ, Default 0 = Produktform byte-identisch, Commit d520672, cargo test --release 447 passed) und gefahren (b18_best @400 gegen Champion @400, 407 Seeds, Arm D1, Blockgroesse 25): k1 +0,14 (Block-t 0,54) und k2 +0,07 (Block-t 1,00) gegen die vorregistrierte Schwelle 2,571 -- Erfolgsregel aus par.7 gerissen. Siege 229/407 = 56,3 % gegen 211/407 im Nullarm (McNemar p = 0,2025, kein Verlust), war aber nie das Kriterium. KEIN Nullbefund aus Wirkungslosigkeit: in 402 von 407 Partien weicht der Ausgang vom Nullarm ab, in 178 kippt der Sieger -- damit ist die Produktkollaps-Erklaerung als URSACHE widerlegt, die Form war nicht der Engpass. Der in par.7 registrierte naechste Schritt (Rangregel) ist durch Nutzer-Entscheid 2026-08-18 ausgeschlossen; Nachfolger ist PREREG_ownership_coupling.md (Skala statt Form). -->

# PREREG: Konjunktionsterme — E_k aus dem gelernten Kopf statt aus dem Produkt

Stand 2026-08-17, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

---

## par.1 DER ANLASS IST EINE MESSUNG

`PREREG_gate_c_consumer_sweep.md` par.16.3, Zuwachs je Kriterium bei Dosis D1
gegen den Nullarm, gegenuebergestellt dem analytischen Marginalwert bei p=0,5:

| Kriterium | Kette | Auszahlung | Marginal | gemessener Zuwachs |
|---|---:|---:|---:|---:|
| k3 Joker | 1..8 (`config.py:116`) | **2·N** | 1,00 (N=2) … 0,19 (N=6) | **+1,59** |
| k5 Ecken | 4 | 8 | 0,500 | **+0,34** (t 2,79) |
| k2 Diagonalen | 6 | 10 | 0,156 | +0,07 |
| k1 Spalten | 6 | 7 | 0,109 | −0,09 |

**Die Rangfolge stimmt Zeile fuer Zeile.** Der Produktzerfall ist damit keine
Herleitung mehr, sondern die gemessene Ursache dafuer, dass k1 und k2 sich nie
bewegen: ein Produkt ueber sechs Faktoren < 1 kollabiert, und nur k3 entgeht
dem, weil seine Auszahlung mit der Kettenlaenge waechst.

**Und der Kopf schaetzt genau das Fehlende bereits.** Er wird seit dem
Sweep mit 68 Zusatzzielen trainiert, die die Konjunktionen DIREKT vorhersagen
(`config.py:117`, `neural_net.py::_conjunctions_from_dome`). Der Verbraucher
liest sie nicht: `apply_ownership_shaping_full` (`net_mcts.rs:1655`) nutzt nur
`[0:72]` und rekonstruiert sie durch Multiplikation. Der Kommentar dort nennt
sie selbst "heute UNGENUTZT".

## par.2 GEPRUEFTER IST-STAND (Quellen, nicht hergeleitet)

| Sache | Befund | Pruefstelle |
|---|---|---|
| Kopfbreite mit Konjunktionen | 140 = 72 Feld + 68 Konjunktion | `config.py:117-118` |
| Aufteilung | `[0:36]` Feld ich, `[36:72]` Feld Gegner, `[72:106]` Konj. ich, `[106:140]` Konj. Gegner | `neural_net.py:1840-1841` |
| Atome je Spieler | **34** | `config.py:117` |
| Atom-Reihenfolge | 0..5 Reihen (+3) · 6..11 Spalten (+7) · 12..13 Diagonalen (+10) · 14..17 Ecken (3/3/8/8) · 18 alle Joker · 19..24 farbenreiche Reihen (+4) · **25..33 LAYOUT** | `neural_net.py::_conjunctions_from_dome` Docstring |
| 25..33 sind KEINE Konjunktionen | `P(Slot s traegt am Ende eine Jokerplatte)` — daraus `E[wild_total] = SUM P(Slot wild)` | `config.py:108-116` |
| Jokerfelder je Brett | gemessene Spanne **1..8** | `config.py:116` |
| Champion ist 72 breit | `ownership_weight: null` → Kopf aus | `manifest_train_v21_2d_20260809_004805.json` |
| Verbraucher liest nur `[0:72]` | Produktform, Konjunktionen ungenutzt | `net_mcts.rs:1620-1638` |

## par.3 DIE ENTSCHEIDUNG, DIE HIER FAELLT: WELCHES KRITERIUM ZIEHT UM

**Nicht alle.** Die 36 Feldlabels sind fuer die ADDITIVEN Kriterien exakt —
dort kollabiert nichts, und ein Umzug waere eine Verschlechterung:

| Kriterium | Form | Quelle NACH dem Umbau | Begruendung |
|---|---|---|---|
| **k0** Reihen (+3) | konjunktiv | Atome 0..5 | Produkt ueber 6 |
| **k1** Spalten (+7) | konjunktiv | **Atome 6..11** | die Zielgroesse |
| **k2** Diagonalen (+10) | konjunktiv | **Atome 12..13** | die Zielgroesse |
| **k3** Joker (2·N) | konjunktiv | Atom 18, Punktwert `2 · SUM(Atome 25..33)` | erstmals mit geschaetztem N statt dem aktuellen |
| k4 Randfelder (+1/Feld) | **additiv** | Feldlabels `[0:36]` | exakt, kein Kollaps |
| **k5** Ecken (3/3/8/8) | konjunktiv | Atome 14..17, **je Ecke einzeln** | die 8-Punkt-Ecken sind die seltenen |
| k6 Spezialfelder (−3/leer) | **additiv** | Feldlabels `[0:36]` | exakt |
| **k7** farbenreiche Reihen (+4) | konjunktiv | Atome 19..24 | **erstmals ueberhaupt ausdrueckbar** — aus Feldlabels prinzipiell nicht (`config.py:95`) |

Zwei Punkte daran sind mehr als Umsortieren:

**k3 bekommt seinen Punktwert geschaetzt statt gezaehlt.** Bisher multipliziert
`expected_plate_points` mit dem AKTUELLEN `wild_total`, was frueh im Spiel nach
unten verzerrt. Die Layout-Atome liefern `E[wild_total]`.

**k7 wird ueberhaupt erst darstellbar.** Aus Feldlabels ist "Reihe hat >= 5
Farben" nicht ableitbar (das Ziel dort ist belegt/leer ohne Farbe). k0/k7 sind
per Nutzer-Entscheid "verteidigen, nie anstreben" — sie ziehen deshalb mit um,
aber ihr Gewicht bleibt auf dem Bestandswert.

## par.4 WAS GEBAUT WIRD

**Ein Knopf, eine Formumschaltung — keine Dosis.** `MOSAIC_OWNERSHIP_CONJ`,
Default **0** = Produktform, byte-identisches Bestandsverhalten (Task-#28-Muster).

### par.4.1 Drafting (Blattshift)

`E_k = punkte_k · p_atom` statt `punkte_k · PROD p_f`, je Kriterium ueber seine
Atome summiert. Der Rest der Kette bleibt unberuehrt: derselbe `tanh(E_k/50)`,
dieselben `gew_k`, derselbe Einspeisepunkt.

### par.4.2 Tiling (marginale Feldwerte)

Hier liegt die einzige echte Schwierigkeit: der Loeser braucht Werte JE FELD,
eine Konjunktionsausgabe liefert einen Wert je GEOMETRIE. Geplant ist eine
Aufteilung statt eines Produkts:

```text
wert(f) = SUM_k gew_k · punkte_k · p_k^conj · (1 - p_f) / SUM_{g in Geometrie} (1 - p_g)
```

Der Kriteriumswert wird also auf die noch FEHLENDEN Felder verteilt,
proportional dazu, wie stark sie fehlen. Wohldefiniert, kein Netzaufruf je
Kandidat, und es kollabiert nicht. **Ungeprueft:** ob diese Aufteilung besser
routet als das Produkt — sie ist plausibel, nicht gemessen.

### par.4.3 Rueckfall bei 72er-Koepfen

Der amtierende Champion hat keinen Konjunktionsteil. Bei Kopfbreite < 140
faellt der Verbraucher auf die Produktform zurueck, mit `warn_once` — nicht
still. Sonst wuerde ein Knopf, der beim einen Checkpoint wirkt und beim anderen
nicht, als Dosiseffekt fehlgelesen.

## par.5 VORBEHALT, DER VORAB DASTEHEN MUSS

**Der Kopf rangiert hervorragend und kalibriert schlecht.** Gemessen
(`PREREG_ownership_selector.md` par.9.2): Konjunktions-AUC 0,83-0,91, aber der
Brier liegt nur **8-14 %** unter der Grundrate; ueber 0,5 ueberschaetzt er
deutlich. `E_k = punkte_k · p_atom` benutzt ihn als WERT und erbt damit genau
die schwache Seite.

Das ist kein Grund, es nicht zu bauen — die Produktform ist nachweislich
schlechter, und ein ueberschaetzter Wert auf der richtigen Geometrie schlaegt
einen kollabierten auf allen. Aber es begrenzt die Erwartung, und es ist der
Grund, warum die Rangregel (par.9.3 dort) als eigener, spaeterer Schritt
geplant ist: ein Rang ist kalibrierungsfrei.


## par.5a URSACHENMESSUNG ZUR KALIBRIERUNG (2026-08-17, vor dem Bau)

Nutzer-Auftrag: Massnahmen gegen die schlechte Kalibrierung ueberlegen, bevor
gebaut wird. Sonde `tools/probes/conjunction_base_rates.py` -- Positivraten der
ENDZUSTANDS-Labels je Quelle, 12 Dateien und 120 Partien je Praefix:

| Quelle | Spalten k1 | Diagonalen k2 | Ecken k5 |
|---|---:|---:|---:|
| Fenster v18/v19wdl/v19wdlsw/v20wdl/v20wdlsw | 0,21–0,62 % | 0,00–0,42 % | 26–27 % |
| `v21_own_a` (Netz, ungelenkt) | 0,49 % | 0,00 % | 27,19 % |
| **`v21_own_k1`** Spaltenbauer | **6,67 %** | 0,00 % | 23,33 % |
| **`v21_own_k2`** Diagonalenbauer | 0,69 % | **20,00 %** | 25,10 % |
| **`v21_own_k5`** Eckenbauer | **8,75 %** | 0,62 % | **38,54 %** |
| `v21_own_k6` | 0,76 % | 0,62 % | 28,12 % |
| `heur_own` | 0,35 % | 0,21 % | 17,19 % |

> **Die Verteilungsverschiebung ist belegt.** Die Bauer-Arme haben bei genau
> den Zielkriterien die **11- bis 48-fache** Positivrate von normalem Spiel.
> Der Kopf lernt Spaltenvollendung praktisch ausschliesslich aus Bauer-Partien
> und wird auf Stellungen benutzt, in denen sie fast nie vorkommt. Wenn er
> sicher ist, ist er zu sicher -- genau das gemessene Bild (par.5).

**Massnahme, daraus folgend: nachgelagerte Platt-Korrektur je Atomgruppe.**
Zwei Parameter (A_g, B_g) auf einem sauberen Held-out gefittet, in der Engine
vor der Verwendung als Wert angewandt. Vorbild im Baum:
`neural_net.py::_destretch_prob` (Platt-Streckung mit A=0,0051, B=1,9269 fuer
gestauchte Alt-Kopf-Wahrscheinlichkeiten) -- die Idiomatik existiert, sie ist
bisher nur datenseitig und nicht inferenzseitig.

**Voraussetzung, die noch fehlt:** ein dauerhaft aus JEDEM Training
ausgesperrter Bewertungssatz. Ohne ihn wird auf Trainingsdaten gefittet und die
Korrektur macht es schlimmer. Steht in STATUS auf der Warteschlange.

> **ZURUECKGESTELLT am 2026-08-17 — nicht verworfen.** Der Versatz
> ist am Kopf selbst gemessen statt aus Grundraten gefaltet
> (`tools/probes/conjunction_marginal_normal_play.py`, b19_best, 3000 Bretter):
> k1 0,35 Log-Odds, k0/k5/k3/k7/Layout praktisch null. Der aus den Grundraten
> hergeleitete Wert (1,58 gegen die Bauer-Arme, 0,49 gegen die
> Trainingsmischung) war ein Artefakt der Referenzwahl. Die Fehlkalibrierung
> aus par.5 sitzt im OBEREN Bereich — eine Steigungsfrage, die ein Versatz
> nicht behebt. Und die Normalspiel-Rate stammt von Netzen ohne Plattenblick;
> darauf zu kalibrieren arbeitet dem Leitstern entgegen.
>
> **Wiedervorlage mit messbarem Ausloeser (Nutzer 2026-08-17):** sobald ein
> Champion die Platten beruecksichtigt, ist das normale Spiel das
> Zielverhalten und die Korrektur wieder legitim. Die k1-Grundrate liegt heute
> ueber fuenf Generationen flach (p=0,68), weil keine davon Platten baut — der
> erste, der es tut, hebt sie sichtbar. STATUS.md, Abschnitt "Kalibrierung".

**Zurueckgestellt: `pos_weight` im Ownership-Loss.** Der Loss ist schlichtes
maskiertes BCE ohne Klassengewichtung (`train.py:1082`), und bei 2,4 %
Grundrate ist das die mechanische Mitursache. Aber es kostet einen vollen
Trainingslauf und macht jeden Bestandsvergleich (b18/b19/f1/w1) unvergleichbar,
weil der Kopf ein anderer wird. Erst wenn eine Platt-Korrektur NICHT reicht.

**Ein Trugschluss, ausgeraeumt:** das `tanh(E_k/50)` absorbiert die
Ueberschaetzung NICHT. Bei k1 (7 Punkte) und p=0,95 statt echten 0,73 ergibt
das tanh(0,133) gegen tanh(0,102), also 0,132 gegen 0,102 -- wir arbeiten im
linearen Bereich, die 30 % Ueberschaetzung kommen zu 30 % durch.

## par.5b LAYOUT-ATOME: EIGENER VERDACHT GEPRUEFT UND VERWORFEN

Die Sonde zeigte die Layout-Atome bei **exakt 50,00 %** in jeder Quelle. Das
sah nach einem strukturellen Konstantwert aus -- und haette par.3s Vorschlag
gekippt, `E[wild_total]` daraus zu schaetzen. Nachgemessen an 120 Brettern:

| Slots mit Wild-Feld je Brett | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|
| Bretter | 3 | 14 | 43 | 43 | 14 | 3 |

**Die Zahl variiert (2..7)**, die Verteilung ist symmetrisch um 4,5 -- die
exakten 50 % sind ein Symmetrieartefakt der Mittelung, kein Konstantwert. Der
Verdacht ist damit ausgeraeumt.

Zwei Praezisierungen fallen dabei an:
- **Wild-Slots und Wild-FELDER stimmen 1:1 ueberein** (alle gemessenen Paare
  sind (n,n)). `E[wild_total] = SUM P(Slot wild)` ist also exakt und nicht nur
  naeherungsweise richtig.
- **Der Nutzen kommt von NOCH NICHT GELEGTEN Slots.** `expected_plate_points`
  zaehlt heute nur Wild-Felder in gelegten Slots (`scoring.rs:489`), fruehe
  Stellungen unterschaetzen also. Die Layout-Atome sagen das ENDlayout voraus --
  echte Vorhersage, nicht Ablesen einer sichtbaren Groesse. Der k3-Umbau aus
  par.3 bleibt damit begruendet.

## par.6 MESSANORDNUNG

Wie Tor C par.16, damit die Zahlen direkt daneben stehen:

| | |
|---|---|
| Checkpoint | `alphazero_v21-b18_best.onnx` @400 (140 breit, plattenfaehige Policy) |
| Gegner | Champion @400, Netz gegen Netz |
| Seeds | der 407er-Satz aus `distillation_seeds_main.txt` |
| Arme | N (Regler aus) · **D1 mit Produktform** · **D1 mit Konjunktionsform** |
| Blockgroesse | 25 → nB=6 je Kriterium |

Der Produktform-Arm bei D1 liegt bereits vor (par.16.3), muss also nicht neu
gespielt werden — es kommt **ein** Arm hinzu.

### par.6.1 GUELTIGKEITSKONTROLLE VOR DER MESSUNG (2026-08-17, 23:44)

Zwei Kontrollen, beide VOR der ersten gewerteten Partie, weil ohne sie ein
Nicht-Erfolg nicht interpretierbar waere.

**1. Das Wheel war veraltet — Beinahe-Fehlschluss.** Die installierte
Erweiterung `mosaic_rust.cp314-win_amd64.pyd` trug den Stand **2026-08-16
10:57**, der Konjunktionscode in `scoring.rs` / `net_mcts.rs` den Stand
**2026-08-17 11:04 / 11:07**. Die Arena haette die ALTE Engine gefahren: der
Konjunktionsarm waere bitgleich mit dem Produktarm gewesen, das Ergebnis
"k1/k2 flach" — und damit haette die Messung den einzigen verbliebenen Weg
faelschlich geschlossen. Neu gebaut und installiert 23:44:10.

**2. Determinismus zuerst, dann Reglerwirkung.** Ein Differenztest ueber 8
Seeds, hohe Dosis `1.0,3.0`, `b18_best` gegen Champion je @400:

| Kontrolle | Ergebnis | Belegdatei |
|---|---|---|
| derselbe Arm zweimal, gleiche Seeds | **8/8 Partien identisch** (Sieger, Punktstaende, Bodenreihen) | `paired_arena_env_conj_determinism.json` |
| Konjunktionsform gegen Produktform | **6/8 Partien kippen** (b=3/c=3) | `paired_arena_env_conj_smoke.json` |

Die Reihenfolge ist der Punkt: ohne die erste Zeile beweist die zweite nichts,
weil Abweichungen dann auch aus Nichtdeterminismus kommen koennten. Erst
zusammen belegen sie, dass `MOSAIC_OWNERSHIP_CONJ` die Engine erreicht und das
Spiel wirklich veraendert.

**Regelbezug:** genau der Fall aus dem Merkzettel *"Wheel nach
Engine-Aenderung neu bauen"* — gruene `cargo test` heissen nicht, dass die
Arena den Code sieht, und Zahlengleichheit bei gleichen Seeds ist ALARM, kein
Befund. Der Merkzettel hat hier gehalten.

## par.7 VORAB-ERFOLGSREGEL (woertlich, vor der ersten Partie)

> **ERFOLG** heisst: die Konjunktionsform hebt **k1 oder k2** signifikant auf
> Block-Ebene gegen die Produktform bei derselben Dosis (gepaart ueber den
> Seed, nB=6, zweiseitig p < 0,05) — **und** verliert dabei keine Siege
> signifikant gegen den Nullarm (exakter zweiseitiger McNemar, p >= 0,05).

**k1/k2 und sonst nichts.** Das ist diesmal Absicht und keine Verkuerzung: k1
und k2 sind genau die Kriterien, die unter der Produktform kollabieren, und
damit die einzigen, an denen sich der Umbau messen laesst. Ein Zuwachs bei k3
oder k5 waere KEIN Erfolg — die bewegen sich schon unter der Produktform.

**Explizit gegen den Fehler vom Vortag:** die Klausel nennt hier k1/k2 und
behauptet NICHT, aus einer aelteren Regel unveraendert uebernommen zu sein. Am
2026-08-17 hatte ich in Tor C par.16 "k1 oder k2" geschrieben und als
"unveraendert" bezeichnet, obwohl das Original k1/k2/k5 nannte — und
ausgerechnet k5 bewegte sich.

**NICHT-ERFOLG** heisst: k1 und k2 bleiben flach. Dann ist die Form nicht der
Engpass, sondern die Kalibrierung oder die Kandidatenauswahl — und der naechste
Schritt ist die Rangregel, nicht eine weitere Dosis.

## par.8 REIHENFOLGE

1. Bau hinter `MOSAIC_OWNERSHIP_CONJ=0` (byte-identisch, Paritaets-Hash haelt).
2. **Tor B**: Paritaetsprobe bei Default, wie `net_mcts.rs:7545`.
3. Atom-Zuordnung gegen den Label-Bauer testen, nicht gegen diese Prereg —
   ein Indexfehler wuerde als Dosiseffekt fehlgelesen (`scoring.rs`-Tests
   `plattenkopf_conjunction_atoms_match_spec` als Vorbild).
4. Erst dann die Arena.

## par.9 ERGEBNIS (2026-08-18) — NICHT-ERFOLG, die Form ist nicht der Engpass

Gefahren wie in par.6 registriert, Gueltigkeitskontrollen in par.6.1.
Rohdaten `evaluations/artifacts/paired_arena_env_conj_d1_b18.json`, Arm `0.1,0.3,1`.

**Die Zielkriterien, gepaart gegen die Produktform bei derselben Dosis D1**
(Block-Ebene, nB=6, Schwelle |t| > 2,571):

| Kriterium | Produktform | Konjunktionsform | Delta | Block-t |
|---|---:|---:|---:|---:|
| **k1** Vertikale Reihen | 0,85 | 0,94 | **+0,14** | **0,54** |
| **k2** Diagonale Reihen | 0,07 | 0,13 | **+0,07** | **1,00** |
| Plattenpunkte gesamt | 3,86 | 3,85 | +0,03 | 0,16 |

Beide weit unter der Schwelle. **Nebenbedingung erfuellt** (und nur die):
229/407 = 56,3 % gegen 211/407 im Nullarm, diskordant b=98/c=80, exakter
McNemar **p = 0,2025** — kein Siegverlust, tendenziell ein Gewinn.

> **VERDIKT nach par.7: NICHT-ERFOLG.** k1 und k2 bleiben flach.

**Was das NICHT ist: ein Nullbefund aus Wirkungslosigkeit.** Der Regler
veraendert das Spiel deutlich — der Differenztest in par.6.1 zeigt bei hoher
Dosis 6 von 8 gekippten Partien, und bei D1 weicht der Ausgang in **402 von 407
Partien** vom Nullarm ab (in 178 kippt sogar der Sieger). Die Form greift also
massiv ins Spiel ein, sie verschiebt nur den Plattenbau nicht.

**Damit ist die Produktkollaps-Erklaerung als URSACHE widerlegt.** Sie sagte
voraus: das Marginal der konjunktiven Kriterien ist ~0, weil sechs Feld-
Wahrscheinlichkeiten multipliziert werden — behebe die Form, und k1/k2 bewegen
sich. Die Form ist behoben (Atome statt Produkt, `expected_plate_points_conj`),
k1/k2 bewegen sich nicht. Die Vorhersage ist gefallen.

**Naechster Schritt, so registriert (par.7, woertlich):** *"Dann ist die Form
nicht der Engpass, sondern die Kalibrierung oder die Kandidatenauswahl — und
der naechste Schritt ist die Rangregel, nicht eine weitere Dosis."* Eine
Dosis-Reihe auf der Konjunktionsform ist damit vorab ausgeschlossen.


### par.9.1 NACHTRAG (2026-08-18): gegen den NULLARM gerechnet — die additiven Kriterien bewegen sich

par.9 vergleicht gegen die Produktform, wie vorregistriert. Der Vergleich gegen
den **Nullarm** (Regler ganz aus) war nicht Teil der Erfolgsregel und wurde
zunaechst uebersehen. Er zeigt das Deutlichste der ganzen Messreihe.

Block-Ebene, nB=6, Schwelle |t| > 2,571, gepaart ueber dieselben 407 Seeds:

| Kriterium | Delta | Block-t | Kettenlaenge |
|---|---:|---:|---|
| **Plattenpunkte gesamt** | **+0,94** | **4,53** | — |
| **k4 Aeussere Felder** | **+0,33** | **4,01** | **additiv, 1 Feld** |
| k3 Mehrfarbige Felder | +1,24 | 1,94 | kurz |
| k5 Eckplatten | +0,27 | 1,89 | kurz |
| k6 Spezialfelder | +0,30 | 1,67 | additiv |
| k2 Diagonalen | +0,13 | 1,58 | 6 Felder |
| **k1 Vertikale Reihen** | **+0,05** | **0,11** | **6 Felder** |
| Marge | +1,51 | 1,32 | — |

**Zwei Befunde, die par.9 nicht hatte:**

1. **Die Plattenpunkte insgesamt steigen signifikant** (+0,94, t 4,53) — das
   staerkste Signal der Reihe. Der Regler kauft Plattenpunkte ein, nur nicht
   die vorregistrierten. Das Urteil NICHT-ERFOLG bleibt davon unberuehrt, es war
   auf k1/k2 gestellt und ist es zurecht.
2. **Die Rangfolge ist exakt die Kettenlaenge.** Signifikant wird k4 "Aeussere
   Felder" — 1 Punkt je Randfliese, die kuerzestmoegliche Kette. Danach die
   kurzen Ketten, dann nichts mehr.

**Und die schaerfste Beobachtung:** k4 und k6 sind genau die beiden Kriterien,
die `expected_plate_points_conj` NICHT aus Atomen rechnet, sondern additiv aus
`p_own` weiterlaufen laesst (Zweig `4 | 6` in `scoring.rs`). Die additiven
bewegen sich, die konjunktiven nicht — **unabhaengig davon, ob sie als Produkt
oder als gelernte Atome gerechnet werden.** Damit ist die Marginal-These ueber
den vollen Kriteriensatz bestaetigt statt an zwei Beispielen, und die
Formumschaltung ist als Ursache endgueltig ausgeschieden: sie aendert nichts
daran, dass eine Kette aus sechs Feldern je Zug ein Marginal nahe null hat.

## par.10 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)
