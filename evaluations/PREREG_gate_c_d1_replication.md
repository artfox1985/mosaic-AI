<!-- STATUS: OFFEN | Frage: Sind der k5-Zuwachs und der Siegzuwachs der kleinen Dosis D1 aus PREREG_gate_c_consumer_sweep.md par.16.3 echt oder Glueck? | Beleg: **REGISTRIERT 2026-08-17 vor der ersten Partie.** Frisch-Seed-Replikation, 150 NEUE Seeds (50000..50435, Ueberschneidung mit dem alten 407er-Satz = 0), alle mit k5 aktiv. Genau ZWEI Arme (N und D1) und GENAU EIN vorab benanntes Ziel (k5 auf Block-Ebene) -- damit keine Multiplizitaet, der Vorwurf gegen den Erstbefund. -->

# PREREG: Frisch-Seed-Replikation der Dosis D1 — Ziel k5

Registriert 2026-08-17, **vor der ersten Partie**. Nutzer-Freigabe: *"takte es
ein. wir können anschließend direkt in die konjunktionstherme investieren."*

---

## par.1 WAS REPLIZIERT WIRD, UND WARUM ES EINE REPLIKATION BRAUCHT

`PREREG_gate_c_consumer_sweep.md` par.16.3 hat auf `v21-b18_best` gegen den
Champion gemessen. Zwei Zahlen fielen positiv aus, und beide sind angreifbar:

| Befund | Wert | Der Angriff darauf |
|---|---|---|
| Siege D1 gegen N | 236 gegen 211 von 407, p=0,066 | knapp neben der Signifikanz |
| k5 Eckplatten D1 gegen N | +0,34, Block-t 2,79 (nB=6) | **8 Kriterien x 3 Dosen = 24 Tests** — ueberlebt keine Multiplizitaetskorrektur |

Dazu kommt ein Registrierungsfehler des Koordinators: die Erfolgsklausel fuer
jenen Lauf nannte nur k1/k2, obwohl die Originalregel k1/k2/k5 nennt (par.16.3,
offengelegt). Das Verdikt dort lautet deshalb NICHT-ERFOLG, obwohl k5 sich
bewegt hat.

**Diese Replikation raeumt beide Einwaende auf einmal aus:** ein Ziel, vorab
benannt, auf frischen Seeds.

## par.2 AUFBAU

| | |
|---|---|
| Checkpoint | `alphazero_v21-b18_best.onnx` @400 |
| Gegner | Champion `v21_2d_brierbest` @400, Netz gegen Netz |
| Seeds | **150 NEUE**, `evaluations/gate_c_repl_k5_seeds.txt` (50000..50435) |
| Seed-Auswahl | `tools/seed_selection_plates.py --kriterien 5 --pro-kriterium 150` — alle 150 Seeds haben k5 aktiv |
| Ueberschneidung mit dem 407er-Satz | **0** (geprueft) |
| Arme | **genau zwei**: N (0/0) und D1 (0,1/0,3) |
| Blockgroesse | 25 → nB=6 je Arm |

**Warum k5-selektierte Seeds:** welche Platten liegen, bestimmt allein der Seed
(`scoring_ids_for_seed`), unabhaengig vom Spielverlauf. Nur Seeds mit aktivem k5
zu spielen ist deshalb eine Auswahl VOR der Messung und keine Selektion nach
Ergebnis. Sie senkt die Kosten von 814 auf 300 Partien, weil keine Partie ohne
das Zielkriterium gespielt wird.

**Strukturelle Folge, vorab benannt:** k2 (Diagonalen) und k5 sind
Ausschlusspaar (`scoring.rs:59-65`) — in diesen 150 Partien kommt k2 **nie**
vor. k1 kann vorkommen und wird als Beobachtung ausgewiesen, ist aber
ausdruecklich **NICHT** Teil der Regel.

## par.3 VORAB-REGEL (ein Test, woertlich)

> **REPLIZIERT** heisst: **k5 steigt bei D1 gegen N signifikant auf
> Block-Ebene** (gepaart ueber den Seed, nB=6, zweiseitig p < 0,05, also
> |t| > 2,571) — **und** D1 verliert keine Siege signifikant (exakter
> zweiseitiger McNemar, p >= 0,05 zugunsten von N).

**Das ist der einzige Test.** Keine anderen Kriterien, keine anderen Dosen,
keine Korrektur noetig.

**NICHT REPLIZIERT** heisst: k5 verfehlt die Schwelle. Dann war der Erstbefund
Glueck, und Tor C bleibt in **jeder** Lesart negativ — auch in der
Originalfassung mit k1/k2/k5. Das waere ein sauberer Abschluss des
Regler-Strangs.

**Der Siegzuwachs (236:211) wird ausgewiesen, ist aber KEINE Erfolgsbedingung.**
Er war im Erstbefund p=0,066 und damit selbst unbestaetigt; ihn hier zur
Bedingung zu machen hiesse, zwei unbestaetigte Zahlen gegeneinander zu
verrechnen. Er zaehlt nur in der Sperrklausel: D1 darf keine Siege KOSTEN.

**Kein Nachziehen der Stichprobe**, keine Ausweitung auf weitere Dosen, falls
es knapp wird.

## par.4 WAS DANACH KOMMT (Nutzer-Vorgabe, unabhaengig vom Ausgang)

*"wir können anschließend direkt in die konjunktionstherme investieren."* Der
Umbau auf die gelernten Konjunktions-Ausgaenge ist damit **nicht** an diesen
Ausgang gebunden — er ist durch par.16.3 ohnehin begruendet: die Rangfolge der
Zuwaechse ueber die Kriterien ist die Rangfolge der Marginalwerte, und k1/k2
sind die einzigen, die voll kollabieren. Diese Replikation entscheidet nur, ob
der Regler in seiner HEUTIGEN Form einen belegten Nutzen hat, den man beim
Umbau nicht verlieren darf.

## par.5 ERGEBNIS (leer bei Registrierung)

## par.6 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)
