<!-- STATUS: OFFEN | Frage: Hebt eine Implicit-Minimax-Beimischung im Backup (Q = (1-alpha)*Q_MC + alpha*v_minimax, alpha~0,2) die Ausdrucksfaehigkeit langer Linien in unserer Gumbel-Suche -- messbar an k1-Baurate und Staerke? | Beleg: GEBAUT + ABGENOMMEN 2026-08-23 (par.1a: Suite 492/0, Paritaets-Hash haelt, Knopf registriert); ERFOLG nach vorregistrierter Lesart (par.2b, 2026-08-23): kein Staerkeverlust (304 vs 296/407 n.s.), Score-Level SIGNIFIKANT +2,77 (Block-t +3,83), k1 9,0 % -> 16,0 % (+7,0 pp, p=0,090 knapp n.s., groesste je gemessene Netz-Bewegung). ABER par.2c (Netz-gegen-Netz via Kapselung): Paritaet, k1-Effekt gegnerspezifisch, uebertraegt sich nicht; Self-Play-Einsatz bleibt Kandidat mit gedaempfter Erwartung. Paralleler Such-Hebel des Policy-Seiten-Zuschnitts (Nutzer-Freigabe der Reihenfolge 2026-08-22); EINGETAKTET fuer den v22-Zyklus 2026-08-25 (par.3), aber NICHT fuer die Erzeugung: der Knopf sitzt in der Gumbel-Selektion (net_mcts.rs:3376) und steht damit NICHT im Label-Pfad des heuristischen v22-Self-Play (round_transition_deep nutzt net_leaf_eval und drafting_action_priors, keine Gumbel-Selektion). Zu messen am v23-NETZ: erst im Gating (dort heute schon live, Default 0,0), dann im naechsten netz-basierten Self-Play. Entscheidungsmass ist STAERKE auf Block-Ebene, die k1-Baurate nur begleitend -- sie war schon einmal die groesste je gemessene Bewegung ohne folgende Staerke. Quelle: RESEARCH_search_alternatives_external S4/S6 Option O1. -->

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

**Was damit eingetaktet ist:** der Arm gehoert an das v23-NETZ, nicht an den
Korpus. Zwei Stellen, an denen er wirkt und an denen er zu messen ist:

1. **Gating/Arena von v23** -- dort ist er heute schon live (Default 0,0 = aus,
   pro Seite ueberschreibbar per `models/<name>.spec.json`). Das ist die
   billigste Messung: kein Bau, ein Konfigurationsfeld.
2. **Das NAECHSTE netz-basierte Self-Play** (also nach v23, nicht v22) -- das
   ist der in par.2c offen gebliebene Punkt.

**Erwartung ausdruecklich gedaempft, und das gehoert vor den Lauf und nicht
danach:** par.2b war ein Erfolg nach vorregistrierter Lesart (k1 9,0 auf
16,0 Prozent, Score +2,77 signifikant), aber par.2c hat gezeigt, dass der
k1-Effekt GEGNERSPEZIFISCH ist und sich auf Netz-gegen-Netz nicht uebertraegt.
Wer hier einen Wiederholungstreffer erwartet, hat par.2c nicht gelesen.

**Entscheidungsmass:** Staerke in der gepaarten Arena, Block-Ebene. Die
k1-Baurate ist BEGLEITEND zu berichten, aber nicht das Kriterium -- sie war
schon einmal die groesste je gemessene Netz-Bewegung, ohne dass Staerke folgte.
