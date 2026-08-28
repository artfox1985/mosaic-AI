<!-- STATUS: ENTSCHIEDEN | Frage: Sind der k5-Zuwachs und der Siegzuwachs der kleinen Dosis D1 aus PREREG_gate_c_consumer_sweep.md par.16.3 echt oder Glueck? | Beleg: ENTSCHIEDEN 2026-08-17, NICHT REPLIZIERT (par.5, par.6): k5 gepaart Block-t 1,10 gegen die Vorabregel Betrag t > 2,571, Siege 81:77 (p=0,699) -- beide positiven Zahlen des Erstbefunds sind zusammengebrochen. Damit ist der Regler-Strang abgeschlossen, Tor C bleibt in jeder Lesart negativ, beide Regler auf Default 0. -->

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

## par.5 ERGEBNIS (2026-08-17)

150 frische Seeds (50000..50435, Ueberschneidung mit dem alten Satz 0), alle
mit k5 aktiv, zwei Arme, `first_player` je Seed identisch (geprueft).
Rohdaten `evaluations/artifacts/paired_arena_env_gate_c_repl_k5.json`.

| | N (0/0) | D1 (0,1/0,3) |
|---|---:|---:|
| Siege | 77/150 = 51,3 % | 81/150 = 54,0 % |
| McNemar D1 gegen N | — | b=32 c=28, **p=0,699** |
| **k5 Eckplatten, gepaart** | Bezug | **+0,19, Block-t 1,10 (nB=6)** |

Gegenueberstellung zum Erstbefund (`PREREG_gate_c_consumer_sweep.md` par.16.3):

| | Erstbefund, 407 Seeds | Replikation, 150 frische Seeds |
|---|---:|---:|
| k5, Block-t | +0,34, **t 2,79** | +0,19, **t 1,10** |
| Siege | 236:211, p=0,066 | 81:77, p=0,699 |

## par.6 VERDIKT NACH DER VORAB-REGEL

Die Regel aus par.3 verlangt |t| > 2,571 auf k5. Gemessen: **t = 1,10**.

> **NICHT REPLIZIERT.**

par.3 sagt woertlich, was das bedeutet: *"Dann war der Erstbefund Glueck, und
Tor C bleibt in JEDER Lesart negativ -- auch in der Originalfassung mit
k1/k2/k5."* Genau das ist eingetreten. **Beide** positiven Zahlen des
Erstbefunds sind zusammengebrochen, die Plattenzahl wie die Siege.

**Nebenwirkung, die ich ausdruecklich festhalte:** mein Registrierungsfehler
in Tor C par.16 -- die Erfolgsklausel auf k1/k2 verkuerzt und faelsch als
"unveraendert" bezeichnet, obwohl das Original k1/k2/k5 nennt -- war damit
**ergebnisneutral**. Haette ich die schmeichelhafte Lesart gewaehlt und k5 als
Erfolg gezaehlt, staende jetzt ein widerlegter Befund im Protokoll. Die
strengere Auslegung hat nichts gekostet und einen Fehlschluss verhindert.

**Der Regler-Strang ist damit abgeschlossen.** Der Laufzeit-Verbraucher in
seiner heutigen Form (Produkt der Feldwahrscheinlichkeiten) hebt die
Zielkriterien nicht -- weder bei plattenblinder Policy (Originalsweep) noch bei
plattenfaehiger (par.16.3 + diese Replikation). Beide Regler bleiben auf
Default 0.

**Was vom Erstbefund UEBERLEBT**, und es traegt den naechsten Schritt: der
Zuwachs bei **k3** war ueber alle drei Dosen stabil (+1,59 / +1,20 / +1,68,
Block-t bis 5,65) und ist damit kein Rauschen. Die Aussage lautet also
praeziser als vorher: **das Kriterium mit der KURZEN Konjunktion bewegt sich,
die mit sechs Feldern nicht.** Das ist die Produktkollaps-Vorhersage, und sie
begruendet `PREREG_conjunction_terms.md` weiterhin -- nur nicht mehr ueber k5,
sondern ueber den Kontrast k3 gegen k1/k2.
