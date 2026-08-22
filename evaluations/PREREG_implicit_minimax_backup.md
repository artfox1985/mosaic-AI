<!-- STATUS: OFFEN | Frage: Hebt eine Implicit-Minimax-Beimischung im Backup (Q = (1-alpha)*Q_MC + alpha*v_minimax, alpha~0,2) die Ausdrucksfaehigkeit langer Linien in unserer Gumbel-Suche -- messbar an k1-Baurate und Staerke? | Beleg: ENTWURF 2026-08-22, nichts gebaut. Paralleler Such-Hebel des Policy-Seiten-Zuschnitts (Nutzer-Freigabe der Reihenfolge 2026-08-22); Quelle: RESEARCH_search_alternatives_external S4/S6 Option O1 (Baier/Winands-Linie, in Brettspielen belegt, Netz unveraendert). -->

# PREREG-SKELETT: Implicit-Minimax-Backup als Laufzeit-Knopf

Stand **2026-08-22. ENTWURF, nichts gebaut, Plan-Zeitform.**

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

## par.3 Grenzen

Behandelt NICHT die Datenseite (das leistet
`PREREG_start_position_seeding.md`); Kombinationsmessungen erst, wenn
beide Einzelhebel gemessen sind.
