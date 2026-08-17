<!-- STATUS: OFFEN | Frage: Hebt der Verbraucher die Zielkriterien k1/k2, wenn E_k aus den GELERNTEN Konjunktions-Ausgaengen kommt statt aus dem Produkt der 36 Feldwahrscheinlichkeiten? | Beleg: **ENTWURF 2026-08-17, nichts gebaut.** Anlass ist gemessen, nicht hergeleitet: in Tor C par.16.3 ist die Rangfolge der Plattenzuwaechse EXAKT die Rangfolge der Marginalwerte -- Joker (kurze Kette, laengenskalierte Auszahlung) +1,59, Ecken (4 Felder) +0,34, Diagonalen (6) +0,07, Spalten (6) -0,09. k1/k2 sind die einzigen, die voll kollabieren. Nutzer-Auftrag: "fokussier dich mal auf die konjunktionsterme". -->

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

## par.9 ERGEBNIS (leer bei Registrierung)

## par.10 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)
