<!-- STATUS: ENTSCHIEDEN | Frage: Hebt eine Implicit-Minimax-Beimischung im Backup (Q = (1-alpha)*Q_MC + alpha*v_minimax, alpha~0,2) die Ausdrucksfaehigkeit langer Linien in unserer Gumbel-Suche -- messbar an k1-Baurate und Staerke? | Beleg: Gebaut und abgenommen (par.1a); Arena-Erfolg gegen die Heuristik (par.2b) als GEGNERSPEZIFISCH widerlegt (par.2c). Der Self-Play-Arm ist am 2026-08-30 gefahren und NEGATIV: alpha 0,2 senkt die Zustandsabdeckung (Verhaeltnis 0,990, beide Seeds gleichgerichtet) und laesst die Zielschaerfe praktisch unbewegt (Entropie 0,2670 auf 0,2647). ENTSCHEID fuer die v22-b05-Erzeugung: alpha 0,0 (par.3b). -->

# PREREG-SKELETT: Implicit-Minimax-Backup als Laufzeit-Knopf

Stand **2026-08-23: gebaut, abgenommen und gemessen** (par.1a, par.2a,
par.2b); par.1/par.2 unten sind der originale Planungstext.

## par.1 Idee und Zuschnitt

Backup-Variante statt Netz- oder Datenaenderung: je Knoten wird neben
dem MC-Mittel ein Minimax-propagierter Wert gefuehrt und als
Q = (1-alpha)*Q_MC + alpha*v_minimax gemischt (Literatur-Empfehlung
alpha~0,2; in Brettspielen real belegt, Report S4). Erhofft: seltene,
aber konsistent gute Linien (Spaltenabschluss) werden nicht mehr vom
Mittel ueber schwache Geschwister-Fortsetzungen verwaessert.

- **Laufzeit-Knopf** `MOSAIC_IMPLICIT_MINIMAX_A` (Name beim Bau,
  Registry-Pflicht), Default 0 = byte-identisches Bestandsverhalten
  (Golden-/Paritaets-Gates wie ueblich).
- Implementierung im Backup-Pfad von net_mcts.rs, additiv; KEINE
  Aenderung am Heuristik-Anker (mcts.rs bleibt unberuehrt).

**Herkunft und Einordnung** (2026-08-28 aus dem Statuskopf hierher verschoben,
damit sie beim Kuerzen nicht verlorengeht): Quelle ist
`RESEARCH_search_alternatives_external`, Abschnitte S4/S6, dort Option O1.
Der Knopf ist der PARALLELE Such-Hebel zum Zuschnitt auf der Policy-Seite;
die Reihenfolge der beiden hat der Nutzer am 2026-08-22 freigegeben.

### par.1a GEBAUT + ABGENOMMEN (2026-08-23; Sonnet-Agent, Koordinator-Nachpruefung: Diff-Hotspots gelesen, alle 8 neuen Tests nachgefahren, Paritaet unabhaengig nachgemessen)

- Knopf `MOSAIC_IMPLICIT_MINIMAX_A` aktiv (net_mcts.rs, Getter ~Z.344;
  Registry-Eintrag knob_registry.rs, docs/knobs.md regeneriert).
- **Drei Bau-Entscheide, am Code belegt:** (1) Perspektive: `im_value:
  [f64;2]` folgt exakt der Q_MC-Konvention (Kinder teilen die
  Perspektive des Ziehers; Minimax waehlt per `im_value[mover]` und
  uebernimmt den VOLLEN Vektor). (2) Chance-Knoten: es gibt KEINE als
  Baumknoten -- Determinisierung vor dem Baumbau, Rundenuebergaenge
  werden bei Knotenerzeugung in den Blattwert gemittelt; reiner
  Minimax-Baum, keine Erwartungswert-Sonderbehandlung noetig.
  (3) Mischungsort minimal-invasiv: NUR `gumbel_select_child`
  (Tiefe >= 1) mischt via `completed_q_per_candidate_mixed`;
  Policy-Targets, Wurzel-Sequential-Halving und
  `gumbel_final_root_action` bleiben auf reinem Q_MC.
- **Abnahme:** Suite 492/0 (8 neue Tests, u. a. exakte Identitaet bei
  alpha=0 und Wirkungsnachweis bei alpha=0,5); Wheel neu gebaut und
  installiert; Paritaets-Hash 8c6684ff... haelt (Agent + unabhaengige
  Koordinator-Messung).
- **Dokumentierte Einschraenkungen (erste Verdachtspunkte bei
  Nullwirkung):** Wurzel-Entscheidung selbst mischt nicht (Wirkung
  nur indirekt ueber die Sim-Verteilung in den Teilbaeumen);
  unbesuchte Kandidaten bleiben ungemischt; OnceLock verhindert
  alpha-Wechsel im selben Prozess (Tests auf der reinen Funktion,
  Muster calibrate_win_prob_with).

## par.2 Messanordnung (EIN Faktor)

1. Vorzeichen-Sonde nach dem r5_chance-Muster: Entscheidungs-
   Abweichungen und Punktversatz an-vs-aus auf festen Seeds, bevor
   eine Arena laeuft.
2. Paired Arena `paired_arena_env_ab.py --env-name <Knopf> --arms 0 0.2
   --control 0` auf den 407 Kampagnen-Seeds, `--log-games`; ausgewiesen
   werden Siege (Block-Ebene) UND k1-Rate (Endwertungs-Parsing wie
   Asym-par.14).
3. Erfolgslesart VORAB: primaer kein Staerkeverlust bei alpha=0,2;
   eine k1-Raten-Hebung ist Bonus-Befund, kein Gate. Task-#18-Lehre
   beachten: bei engine-weiten Aenderungen zaehlt der absolute
   Score-Level mit, nicht nur die Siegquote.

### par.2a ERGEBNIS VORZEICHEN-SONDE (2026-08-23, `tools/probes/implicit_minimax_sign_probe.py`, Artefakt `evaluations/artifacts/implicit_minimax_sign_probe.json`)

30 gepaarte Partien Champion@400 gegen Heuristik@150 auf identischen
Seeds, alpha 0 vs 0,2 in getrennten Prozessen (OnceLock):

- **Wirkung real und frueh:** 30/30 Partien divergieren, Erstabweichung
  Median Log-Index 35,5 (min 5). Der par.1a-Verdachtspunkt (nur
  indirekte Wirkung ueber Teilbaeume) ist damit entkraeftet.
- **Richtung positiv, n=30 unterpowert:** Netz-Punktversatz +3,23
  (sd 14,5; t 1,22, n.s.), Heuristik-Seite -0,3 (flach) -- der
  ABSOLUTE Score-Level steigt (Task-#18-Kriterium erfuellt, kein
  c_scale-Muster). Siege 23 -> 27 von 30; alle 4 Siegwechsel in
  Richtung alpha=0,2, keiner dagegen.
- Freigabe-Lesart par.2(1): Sonde zeigt Wirkung -> die Arena
  (--arms 0 0.2, 407 Kampagnen-Seeds) ist gerechtfertigt und wurde
  gestartet (2026-08-23, `logs/arena_imm_a02_20260823.log`).
- Dokumentierte Sonden-Caveats (Agent, als ungeprueft markiert): die
  Divergenz-Zaehlung laeuft ueber ALLE Log-Zeilen (Drafting und
  Tiling); ob Tiling-Entscheidungen denselben gemischten
  Selektionspfad durchlaufen, ist NICHT am Code nachgeprueft, und die
  Erstabweichung ist nicht zeilenweise auf den Netz-Zug attribuiert
  (indirekte RNG-Effekte moeglich). Fuer die Freigabe-Frage
  unerheblich (Wirkung ja/nein), fuer Mechanik-Deutungen beachten.
  Nenner-Hinweis: 100 % auf Partie-Ebene ist NICHT mit den 3,1 %
  Einzelentscheidungen der r5_chance-Vorlage vergleichbar.

### par.2b ERGEBNIS ARENA + VERDIKT (2026-08-23, Artefakt `evaluations/artifacts/paired_arena_env_imm_a02.json`, Log `logs/arena_imm_a02_20260823.log`; Instrument-Zahlen vom Koordinator selbst erhoben)

407 Kampagnen-Seeds, Champion@400 gegen Heuristik@150, alpha 0 vs 0,2
in getrennten Prozessen, gepaart je Spielindex:

- **Siege:** 296/407 (aus) gegen 304/407 (an), +8; McNemar b=69/c=61,
  p=0,539 (n.s.). **Kein Staerkeverlust -- das primaere par.2-Kriterium
  ist ERFUELLT.**
- **Absoluter Score-Level (Task-#18-Kriterium): SIGNIFIKANT POSITIV.**
  Netz-Score 48,43 -> 51,20 (+2,77 im Mittel; Block-t +3,83, nB=16 a
  25). Kein c_scale-Muster; der Knopf hebt das eigene Punkteniveau.
- **k1-Bonus-Befund: die groesste je gemessene k1-Bewegung auf der
  Netz-Seite.** 14/156 = 9,0 % (aus) -> 25/156 = 16,0 % (an), +7,0 pp
  auf identischen k1-aktiven Partien (Nenner 156 wie par.14 Asym);
  Heuristik-Gegenseite flach (11,5 -> 12,2 %). Gepaart: McNemar
  b=23/c=12, p=0,090; Block-t +1,96 -- knapp unter Signifikanz,
  Richtung konsistent mit Sonde (par.2a) und Sieg-Delta.
- **VERDIKT nach vorregistrierter Lesart par.2(3): ERFOLG.** Kein
  Staerkeverlust (primaer), Score-Level signifikant positiv, k1-Hebung
  als gerichteter, knapp nicht signifikanter Bonus. Zusammen mit dem
  Sibling-Befund (Seeding-Prereg par.4d: der Kopf traegt k1-Signal)
  stuetzt das die Diagnose-Kette: der Such-Hebel macht das
  Kopf-Signal verhaltenswirksam.
- Einordnungs-Caveat (vorab bekannt): das Instrument misst gegen die
  HEURISTIK; eine Netz-gegen-Netz-Staerkeaussage liefert es nicht
  (prozessweiter Knopf, beide Seiten saehen ihn). Konsequenzen
  (alpha-Sweep, Knopf im Self-Play der naechsten Generation,
  Kombination mit Seeding-Daten) sind Nutzer-Entscheide.

### par.2c NACHTRAG NETZ-GEGEN-NETZ (2026-08-23, via Agenten-Kapselung Welle 1; Details PREREG_agent_encapsulation.md par.6b)

Die erste Netz-gegen-Netz-Messung (alpha=0,2 gegen frozen, 407 Seeds
+ Brettwechsel) zeigt PARITAET (400/814) und ein vollstaendiges
Verschwinden des k1-Effekts (9,6 % beidseitig, identische Zaehler).
**Der par.2b-Befund ist damit als GEGNERSPEZIFISCH eingeordnet**
(Ausnutzung der Heuristik, kein Verhaltensgewinn gegen gleich starke
Gegner). par.2b bleibt als Messung gueltig; seine Verallgemeinerung
ist widerlegt. Self-Play-Einsatz bleibt Kandidat (beidseitiger Knopf
= Datenverteilungs-Frage), Erwartung gedaempft.

## par.3 Grenzen

> **Nummerierungs-Anmerkung (2026-08-27):** diese Datei traegt ZWEI
> Abschnitte "par.3" -- diesen hier und weiter unten "par.3 EINGETAKTET fuer
> den v22-Zyklus". Externe Verweise auf `par.3a` meinen den unteren
> (das Eingetaktete) samt seiner Praezisierung. Nicht umnummeriert, weil auf
> die Bezeichner bereits verwiesen wird.

Behandelt NICHT die Datenseite (das leistet
`PREREG_start_position_seeding.md`); Kombinationsmessungen erst, wenn
beide Einzelhebel gemessen sind.


## par.3 EINGETAKTET fuer den v22-Zyklus (Nutzer 2026-08-25)

**Zuerst eine Abgrenzung, die den Zuschnitt bestimmt: dieser Knopf kann die
v22-ERZEUGUNG nicht beeinflussen.** `mix_q_with_implicit_minimax` sitzt in der
Selektion der Gumbel-Baumsuche (net_mcts.rs:3376, Alpha aus
`SearchConfig::implicit_minimax_alpha`). Die v22-Partien werden heuristisch
gespielt; das Netz liefert nur die Rundenuebergangs-Labels, und deren Pfad
(`round_transition_deep`) benutzt `net_leaf_eval` und
`drafting_action_priors`, aber KEINE Gumbel-Selektion. Der Knopf steht also
nicht im Label-Pfad -- ein Eingriff waehrend des laufenden Korpus waere
wirkungslos, nicht schaedlich.

**Was damit eingetaktet ist:** der Arm gehoert an das v22-NETZ (das aus dem
hv2-Lehrerkorpus trainierte), nicht an den Korpus selbst. Zwei Stellen, an denen er wirkt und an denen er zu messen ist:

1. **Gating/Arena von v23** -- dort ist er heute schon live (Default 0,0 = aus,
   pro Seite ueberschreibbar per `models/<name>.spec.json`). Das ist die
   billigste Messung: kein Bau, ein Konfigurationsfeld.
2. ~~**Das NAECHSTE netz-basierte Self-Play** (also nach v23, nicht v22)~~ --
   **BERICHTIGT durch par.3a (Vermerk 2026-08-27):** die Klammer stimmt
   nicht. Der naechste netz-basierte Self-Play-Lauf ist das
   **v22-SELF-PLAY** -- der Lauf, der das v23-FENSTER fuellt (Konvention:
   Fenster vN traegt die Partien von Champion v(N-1)). Er kommt also VOR v23,
   nicht danach. Daraus die Auflage aus par.3a: die Gating-Messung gehoert
   VOR den Start dieses Laufs, sonst faellt der Erzeugungs-Entscheid per
   Default auf 0,0. Der in par.2c offen gebliebene Punkt bleibt dieser Lauf.

**Erwartung ausdruecklich gedaempft, und das gehoert vor den Lauf und nicht
danach:** par.2b war ein Erfolg nach vorregistrierter Lesart (k1 9,0 auf
16,0 Prozent, Score +2,77 signifikant), aber par.2c hat gezeigt, dass der
k1-Effekt GEGNERSPEZIFISCH ist und sich auf Netz-gegen-Netz nicht uebertraegt.
Wer hier einen Wiederholungstreffer erwartet, hat par.2c nicht gelesen.

**Entscheidungsmass:** Staerke in der gepaarten Arena, Block-Ebene. Die
k1-Baurate ist BEGLEITEND zu berichten, aber nicht das Kriterium -- sie war
schon einmal die groesste je gemessene Netz-Bewegung, ohne dass Staerke folgte.


### par.3a PRAEZISIERUNG (Nutzer 2026-08-25): fuer das v22-SELF-PLAY ist er ein Wecker

Nutzer-Einwand: *"aber die v23 erzeugung wird sie nutzen"*. Trifft zu, und
par.3 hat das zu beilaeufig behandelt.

**Benennung, damit der Off-by-one nicht wiederkehrt:** ein Fenster vN traegt die
Partien von Champion v(N-1) -- das v22-Fenster enthielt `v21wdl`-Partien. Der
Lauf, der das v23-FENSTER fuellt, ist also das SELF-PLAY DES v22-CHAMPIONS.

Das Self-Play, das das v23-FENSTER fuellt, faehrt der v22-CHAMPION (Konvention: Fenster vN traegt die Partien von Champion v(N-1) -- das v22-Fenster enthielt `v21wdl`). Es laeuft ueber `net_self_play_games`, also durch
die Gumbel-Suche -- genau dort, wo `mix_q_with_implicit_minimax` sitzt. Damit
gilt fuer diesen Knopf beim NAECHSTEN Korpus dasselbe wie fuer den
Bootstrap-Horizont: **er ist nur am Generierungsstart entscheidbar.** Die
Policy-Ziele sind die Wurzel-Besuchsverteilung; wer die Selektion aendert,
aendert die Ziele und die besuchten Zustaende mit, und beides ist spaeter
nicht nachtraeglich zu setzen.

**Daraus eine Reihenfolge-Auflage, die sonst still verfaellt:** die
Gating-Messung muss VOR dem Start des v22-Self-Play laufen (also des Laufs, der
das v23-Fenster erzeugt). Passiert sie
danach, ist der Erzeugungs-Entscheid bereits per Default (0,0 = aus) gefallen
-- dasselbe Vergiss-Muster, das `PREREG_chance_nodes.md` Entscheidungsregel 4
zweimal getroffen hat.

**Und eine inhaltliche Trennung, die par.3 verwischt hat: Gating-Arm und
Self-Play-Arm messen NICHT dasselbe.**

* **Gating** misst Staerke gegen einen anderen Gegner. Dort ist der Effekt
  gemessen und gegnerspezifisch (par.2b gegen par.2c).
* **Self-Play** ist Netz gegen sich selbst. Ein symmetrischer Such-Eingriff
  kann sich in den ERGEBNISSEN aufheben -- par.2c hat fuer Netz-gegen-Netz
  genau das gezeigt. Was er nicht aufhebt, sind die POLICY-ZIELE und die
  Zustandsverteilung des erzeugten Korpus. Der Self-Play-Arm ist deshalb keine
  Staerkefrage, sondern eine **Korpus-Frage**, und sein Mass ist ein anderes:
  Zielschaerfe und Zustandsabdeckung, gemessen wie beim v22-Korpus
  (`tools/corpus_sanity_check.py`, `tools/probes/corpus_state_diversity_probe.py`),
  plus die Orakelmetriken am daraus trainierten Netz.

Wer den Self-Play-Arm an der Siegquote misst, misst die falsche Groesse und
bekommt mit hoher Wahrscheinlichkeit eine Null, die nichts bedeutet.

**Kein Bau noetig, auch hier nicht:** `SearchConfig` ist an
`net_self_play_games` pro Seite ueber `models/<name>.spec.json`
ueberschreibbar (Knopf-Registry, `MOSAIC_IMPLICIT_MINIMAX_A`). Der Arm kostet
eine Konfigurationsdatei und die Partien.

### par.3b ERGEBNIS SELF-PLAY-ARM + ENTSCHEID (2026-08-30, Nachtprogramm; Artefakt `evaluations/artifacts/implicit_minimax_gating_b05.json`, Werkzeug `tools/probes/implicit_minimax_selfplay_corpus_eval.py`)

**Anordnung.** Je Arm 200 Partien Self-Play von `alphazero_v22-b05.onnx`
@400 Sims mit Root-Noise, aufgeteilt auf die zwei Seeds 20260910 und 20260911
(je 100) -- dieselben Seeds in BEIDEN Armen, damit die Startbedingungen je
Spielindex gepaart sind und der Seed nicht mit dem Arm verwechselt werden
kann. Der Knopf kam ueber `models/champion_frozen.spec.json` (alpha 0,0) und
`models/champion_imm_a02.spec.json` (alpha 0,2) an den Lauf, also auf dem in
par.3a verlangten Weg und nicht per Umgebungsvariable. Partienzahl und Seeds
nennt par.3a nicht; sie sind als Annahme des Nachtprogramms ausgewiesen
(Kochrezept N1.2).

**Zwei Dinge mussten dafuer gebaut werden**, beide additiv und im Default
byte-identisch: `self_play.py --spec` (die pyo3-Seite nahm `spec` seit Welle 1,
der Treiber reichte es nicht durch -- der registrierte Weg war vom Repo aus
nicht fahrbar), und `spec`/`pcr_*`/`seed_positions` im Lauf-Manifest. Dass der
Knopf ankommt, ist belegt statt angenommen: gleicher Seed 777,
`--no-root-noise --deterministic`, 336 Zuege bei alpha 0,0 gegen 326 bei 0,2.

**Ergebnis, je Arm 200 Partien / rund 32.200 Records mit Policy-Ziel:**

| Groesse | alpha 0,0 | alpha 0,2 |
| --- | --- | --- |
| distinkte (Runde, Brettmaske) | 3.087 | 3.057 (Verhaeltnis 0,990) |
| distinkte je Record | 0,0957 | 0,0949 |
| distinkte Endbretter (von 400 Seiten) | 220 | 220 |
| Top-1-Masse des Policy-Ziels | 0,8992 | 0,9010 |
| Entropie des Policy-Ziels | 0,2670 | 0,2647 |
| effektiver Traeger | 1,558 | 1,546 |

Beide Seeds zeigen dieselbe Richtung (Zustands-Verhaeltnis 0,985 und 0,995),
die Bewegung ist also kein Seed-Ausreisser -- aber sie ist auch kein Gewinn:
die Zustandsabdeckung faellt leicht, die Zielschaerfe bewegt sich um 0,2 bis
0,9 Prozent relativ, und die Zahl distinkter Endbretter ist auf beiden Seiten
gleich. Beilaeufig, nicht das Kriterium: volle Spalten je Partie und Seite
0,0825 gegen 0,0500 und eigene Punkte 18,89 gegen 18,00, beides zuungunsten
von alpha 0,2.

**ENTSCHEID: alpha 0,0 fuer die v22-b05-Erzeugung.** Das registrierte Mass
(par.3a: Zielschaerfe UND Zustandsabdeckung) zeigt auf keiner der beiden
Haelften eine Verbesserung; die Abdeckung geht in beiden Seeds zurueck. Die
Rueckfall-Regel aus `PREREG_v23_window.md` par.4c ("ohne auswertbares Ergebnis
bleibt der Default 0,0") haette dasselbe ergeben -- hier ist es aber ein
gemessener Entscheid, kein Verfall.

**Was NICHT gemessen ist:** das dritte Glied der par.3a-Kette, die
Orakelmetriken an einem aus dem jeweiligen Korpus trainierten Netz. Das
braeuchte zwei Trainingslaeufe auf Vollkorpora. Wer den Knopf spaeter wieder
aufmacht, faengt dort an, nicht bei einer Wiederholung dieser Messung.

**Erzeugte Messdaten** (Loeschkandidaten, nichts davon gehoert ins
v23-Fenster): `data/selfplay_imxb05a00_s1*.pkl` und
`data/selfplay_imxb05a02_s1*.pkl`, je 10 Dateien a 200 Partien, zusammen rund
40 MB, plus die vier `data/manifest_imxb05a0*.json`. Beim Fensterbau per
`MOSAIC_DATA_EXCLUDE` auf `selfplay_imxb05` ausschliessen.
