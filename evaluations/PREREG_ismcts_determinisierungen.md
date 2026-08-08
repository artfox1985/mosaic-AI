# Vorregistrierung: Mehrfach-Determinisierung (ISMCTS-k, Task #65-Reaktivierung)

**Angelegt 2026-08-08, VOR Knopf und Messung.** Nutzer-Go am selben Tag,
Einplanung NACH v21-Training + Gating + Auswertungs-Paket.

## Ausgangslage (Code verifiziert 2026-08-08)

Die Suche zieht heute EINE Stichwelt pro Zug (`NUM_DETERMINIZATIONS = 1`,
net_mcts.rs:704) -- klassisches PIMC mit der bekannten
Strategy-Fusion-Pathologie: die Suche optimiert gegen genau diese eine
moegliche Welt. Die Mehrfach-Variante ist **vollstaendig implementiert**
(Task #65: `build_determinized_forest` + `average_completed_q_policy`,
Standard-ISMCTS-Aggregation) und bei k=1 byte-identisch zum
Bestandspfad; sie ist nur nicht laufzeit-schaltbar.

**Wichtig (rechen-neutral)**: das Sims-Budget wird ueber die Welten
GESPLITTET (`split_sims_across_worlds`, Rest an Welt 1) -- k=4 bei
400 Sims sind 4 Baeume a 100 Sims, nicht 4x Rechenzeit. Der Test ist
damit ein reiner Tausch: Stichprobenvielfalt gegen Tiefe pro Welt.

**Zu erwartender Nebeneffekt (Confound, vorab benannt)**: die
Gumbel-Wurzelbreite haengt am Budget (`m = clamp(round(Sims/16), 4, 16)`)
und wird PRO WELT berechnet -- k=2 -> 200 Sims/Welt -> m=12, k=4 ->
100 Sims/Welt -> m=6. Ein etwaiger Verlust bei k=4 ist daher nicht
zwingend der Determinisierung zuzuschreiben, sondern moeglicherweise der
schmaleren Wurzel (Messung 2 fand die m-Formel allerdings staerke-neutral
bei 150 Sims/m=9 -- H0, p=0,54). Deshalb wird k=2 mitgemessen.

## Knopf

`MOSAIC_NUM_DETERMINIZATIONS` (Default 1 = byte-identisch, OnceLock/
read_f64_env-Muster wie MOSAIC_FLOOR_SHAPING_W). Wirkt an allen drei
Sucheinstiegen ueber die bestehende `NUM_DETERMINIZATIONS`-Semantik;
Paritaets-Hash vor Einsatz.

## Design

Instrument = `tools/paired_arena_env_ab.py` (Amendment-Muster: der Knopf
ist prozessweit, daher Netz-vs-Heuristik -- die Heuristik liest ihn
nicht). DREI Arme a 400 Spiele, identische Seeds, Basis-Seed 20260820:
k=1 (Kontrolle), k=2, k=4.

**AENDERUNG vor dem Lauf (Nutzer-Hinweis 2026-08-08): gemessen wird bei
600 Netz-Sims, nicht 400** -- "wir gehen bei den sockel spielen eh mit
600 sims ins rennen". Das entschaerft den oben benannten Confound
weitgehend, weil die Wurzelbreite pro Welt vom gesplitteten Budget
abhaengt (verifiziert: `split_sims_across_worlds` -> `build_net_tree` ->
`gumbel_top_m_for_budget(sims)`):

| Budget | k=1 | k=2 | k=4 |
|---|---|---|---|
| 400 Sims | 400/Welt, m=16 | 200/Welt, **m=13** | 100/Welt, **m=6** |
| 600 Sims | 600/Welt, m=16 | 300/Welt, **m=16** | 150/Welt, **m=9** |

Bei 600 Sims ist k=2 damit ein Effekt OHNE Breiten-Aenderung (m bleibt
16, weil 300/16 ueber dem Deckel liegt) -- der reine
Determinisierungs-Effekt. Und k=4 landet auf m=9, also exakt der
Konfiguration, die Messung 2 als staerke-neutral gegen m=16 gemessen hat
(H0, p=0,54). Der Confound ist damit fuer k=2 strukturell ausgeschlossen
und fuer k=4 empirisch gedeckt. Zusaetzlicher Vorteil: 600 Sims sind das
Regime, in dem die Sockel-Self-Plays tatsaechlich laufen -- ein positives
Ergebnis waere direkt auf die Korpus-Erzeugung uebertragbar.
Kosten: ~1,5x Wandzeit pro Arm (~30 min statt ~21 min), ~90 min gesamt.

## Entscheidungsregeln

1. **Default-Wechsel** (k>1 wird Standard) nur bei signifikantem
   Siegquoten-Vorteil (McNemar p<0,05) UND Frisch-Seed-Replikation --
   es ist eine Aenderung am Such-Default, dafuer gilt der volle Beleg
   (Statistik-Regel 3), nicht die gelockerte "schadet-nicht"-Logik.
2. H0 -> die Einzel-Determinisierung gilt als AUSREICHEND belegt, der
   Punkt (und damit die Imperfect-Information-Frage auf Suchebene) ist
   geschlossen; die ISMCTS-Maschinerie bleibt als inerter Pfad.
3. Deskriptiv: Scores/Floors auf Block-Ebene; zusaetzlich die
   Zeit/Spiel je Arm (Beleg der Rechen-Neutralitaet).
4. **Nicht Teil dieses Tests**: die Frage, ob k>1 die
   POLICY-ZIEL-Qualitaet im Self-Play verbessert (die Wurzelpolitik
   waere dann ein Welten-Mittel). Das waere ein eigener Korpus-Arm mit
   eigenem Prereg -- erst sinnvoll, wenn die Spielstaerke-Frage
   positiv beantwortet ist.
