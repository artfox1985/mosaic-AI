<!-- STATUS: OFFEN | Frage: Macht eine mit der empirischen Nutzenvarianz des Knotens skalierte Explorationskonstante (KataGo-Form, ohne Unsicherheitskopf) die 400-Sim-Suche staerker, bei unveraendertem Netz? | Beleg: nichts gebaut, nichts gemessen; registriert 2026-10-05 auf Nutzer-Anweisung (par.1-par.4). -->

# Vorregistrierung: Varianz-skalierte Exploration in der Suche (Suchknopf, Spieler-Identitaet)

**Angelegt 2026-10-05 01:0x auf Nutzer-Anweisung** (*"die anderen 3 kandidaten kannst auch eintakten als eigene
arme"*). Herkunft: `RESEARCH_search_alternatives_external_2026-08-22.md` S4.4 (Z. 360-366): KataGo gewichtet
Playouts nach der vom Netz vorhergesagten Unsicherheit UND skaliert cPUCT dynamisch mit der empirischen Utility-
Varianz eines Knotens; beides zusammen "etwa 75 Elo staerker als das Vorgaengerrelease" (Quellenmarke [28] dort).

## par.1 Abgrenzung

Die erste Haelfte (Unsicherheit aus dem NETZ) braucht einen Unsicherheitskopf; der ist nach dem stehenden
Entscheid "Keine neuen Koepfe" (Memory, Suchknoepfe haben die bessere Bilanz) ausgeschlossen. Registriert wird NUR
die zweite Haelfte: die Explorationskonstante je Knoten mit der beobachteten Varianz der Kindwerte skalieren
(hohe Varianz = mehr Exploration, niedrige = mehr Ausbeutung), ohne Netzaenderung. Der Elo-Beleg gilt fuer beide
Haelften zusammen; fuer die zweite allein gibt es keine getrennte Zahl (Einschraenkung vorab benannt).

## par.2 Bauform (Vorgabe; Details nach Code-Lesung VOR dem Bau hier nachzutragen)

* Spec-Feld `cpuct_variance_scale` (0,0 = Bestand byte-gleich; > 0 = Staerke der Skalierung), Env-Rueckfall,
  Registratur und `docs/knobs.md`. Formel nach KataGo-Vorbild (Quelle lesen und hier mit Formel und Pruefstelle
  eintragen): c_eff = c_puct * sqrt(1 + k * var_utility(Knoten)) oder die dort dokumentierte Form; var ueber die
  bisherigen Rueckgabewerte des Knotens, numerisch stabil (Welford).
* Wirkung unterhalb der Wurzel (PUCT-Selektion); an der Wurzel laeuft Gumbel/Sequential Halving unveraendert.
  Zu klaeren: ob die Selektion unterhalb der Wurzel bei uns PUCT ist (`net_mcts.rs`, Pruefstelle nachtragen).
* Pflichtabnahmen wie `PREREG_tree_reuse.md` par.2 (byte-gleich aus, Anker, Fixture, Determinismus, Kostentor).

## par.3 Messung (Tor, vorab)

Wie `PREREG_tree_reuse.md` par.3: gleiches Netz `v34-b01_brierbest`, gleiche Spec, nur der Knopf (Arme k in
0,5 und 1,0, Nutzer-Entscheid vor dem Lauf, zuerst EIN Arm), 400 Sims beide, Seeds 20261600/20261601 a 200 Paare,
Stufenregel; Kriterium Tor 1. Zuordnung: dem Knopf allein.

## par.4 Kosten und Erwartung (HERLEITUNG)

Bau rund ein halber bis ein Tag (Engine, Wheel-Runde, Abnahmen), Arena 2 x 1,5 h. Erwartung des Koordinators
(Schaetzung): unter Tree Reuse, weil der externe Beleg die Haelfte mit dem Kopf einschliesst und unsere
Wurzelselektion Gumbel ist, nicht PUCT.
