<!-- STATUS: OFFEN | Frage: Korrigiert eine laufzeitgelernte Bias-Tabelle je Zustandsklasse (KataGo Subtree Value Bias) systematische Netzfehler in der 400-Sim-Suche, bei unveraendertem Netz und reproduzierbarer Arena? | Beleg: nichts gebaut, nichts gemessen; registriert 2026-10-05 auf Nutzer-Anweisung (par.1-par.4). -->

# Vorregistrierung: Subtree Value Bias Correction (Suchknopf, Spieler-Identitaet)

**Angelegt 2026-10-05 01:0x auf Nutzer-Anweisung.** Herkunft: `RESEARCH_plate_intent_external_2026-08-22.md` F2.4
(Z. 243-250) und `RESEARCH_search_alternatives_external_2026-08-22.md` S4.4 (Z. 364-372): KataGo bucketet Knoten
nach lokalen Mustern, mittelt je Bucket den beobachteten Fehler zwischen Netz-Erstbewertung und tieferer Suche und
zieht ihn im Suchnutzen ab, NodeUtility(n) = NNUtility(n) - lambda * ObsBias(Bucket(n)), lambda rund 0,35; "30
bis 60 Elo". Einordnung im Projekt (S4.4): unser R5-Befund (Plattendaempfung des Wertkopfs) IST ein systematischer
Fehler; das Analogon zum lokalen Muster waere ein Bucket je Wertungsplatten-Konfiguration. Vorab benannt
(`RESEARCH_plate_intent` Z. 601): "bricht Reproduzierbarkeit", weil die Tabelle ueber Suchen hinweg lernt.

## par.1 Bauform (Vorgabe; Details nach Code-Lesung VOR dem Bau hier nachzutragen)

* Spec-Feld `subtree_bias_lambda` (0,0 = Bestand byte-gleich), Bucket-Definition als zweites Feld
  (`subtree_bias_bucket`: 1 = Wertungsplatten-Konfiguration plus Runde; weitere nur nach Messung).
* **Reproduzierbarkeit ist Pflicht:** die Tabelle lebt JE PARTIE und JE SEITE (Reset beim Partiestart), wird in
  deterministischer Reihenfolge aktualisiert (nach Abschluss jeder Suche, nicht nebenlaeufig aus den Threads), und
  zwei Laeufe gleicher Seeds muessen byte-gleich sein (Determinismus-Probe). Eine Tabelle ueber Partien hinweg
  (KataGo-Form) ist ausgeschlossen, weil die gepaarte Arena sonst nicht mehr gepaart ist.
* Beobachteter Bias = Differenz zwischen Netzwert des Knotens bei Expansion und seinem spaeteren Suchwert nach n
  Besuchen (Mindestbesuche als Konstante, z. B. 8); Abzug nur bei Knoten, deren Bucket mindestens m Beobachtungen
  hat.
* Pflichtabnahmen wie `PREREG_tree_reuse.md` par.2.

## par.2 Messung (Tor, vorab)

Wie `PREREG_tree_reuse.md` par.3: gleiches Netz, gleiche Spec, nur der Knopf (lambda 0,35, Bucket 1), 400 Sims
beide, Seeds 20261600/20261601, Stufenregel, Kriterium Tor 1. Zusatzbericht: R5-Kalibrierung mit und ohne Knopf
(`tools/r5_value_calibration.py`, gepaart), weil die Plattendaempfung die benannte Zielgroesse ist.

## par.3 Kosten und Erwartung (HERLEITUNG)

Bau rund ein Tag (Engine; die Bucket-Definition ist die eigentliche Arbeit), Arena 2 x 1,5 h. Erwartung des
Koordinators (Schaetzung): die systematischen Fehler, die der Mechanismus korrigiert, sind bei uns in Runde 5 am
groessten, und dort rechnet die Netzsuche @400 schon mit eigenem Budget; die Wirkung in Runde 1-4 ist ungemessen.

## par.4 Offen (Nutzer-Entscheide vor dem Bau)

Bucket-Definition; Mindestbesuche; ob der Knopf auch in der Erzeugung wirkt; Reihenfolge gegen
`PREREG_tree_reuse.md` und `PREREG_variance_scaled_cpuct.md` (Vorschlag: Tree Reuse zuerst, dann die beiden).
