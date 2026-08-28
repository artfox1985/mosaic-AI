<!-- STATUS: ENTSCHIEDEN | Frage: Wie stark sind eigener und gegnerischer Endpunktestand tatsaechlich korreliert, und wie gross ist der Fehler, den die Unabhaengigkeitsannahme in P(Sieg) erzeugt? | Beleg: KOMPLETT GEFAHREN 2026-08-24 (score_correlation_probe.json): r +0,2973 (Gleichtakt); MAE_eng 0,0390 -> nach par.5 Kennzahl, weder widerlegt noch belegt, kein Bau-Argument. Details par.5/par.6. -->

# Vorregistrierung: Korrelation von eigenem und gegnerischem Endstand

**Angelegt 2026-08-23, VOR jeder Messung.**

## par.1 Anlass

Ein Architektur-Entwurf (Verteilungskoepfe auf eigene Punkte, Gegnerpunkte
und deren Differenz) stuetzte sich auf die Behauptung:

> Eigener und gegnerischer Endpunktestand sind stark korreliert, weil beide
> Seiten aus denselben Fabriken bedient werden. Deshalb laesst sich P(Sieg)
> nicht aus den beiden Randverteilungen falten, und die Differenz braucht
> einen eigenen Kopf.

Diese Behauptung ist **ungeprueft**. Sie ist zugleich billig pruefbar: die
noetigen Zahlen liegen in jedem abgeschlossenen Self-Play-Korpus, es braucht
kein Training und keine Arena. Und sie ist entscheidungsrelevant, denn sie
ist die einzige Begruendung fuer einen dritten Kopf.

Nebennutzen, unabhaengig vom Kopf-Entwurf: das Vorzeichen der Korrelation
sagt etwas ueber das Spiel selbst. Ein positives Vorzeichen heisst
Gleichtakt (in angebotsreichen Partien punkten beide viel), ein negatives
heisst Verdraengung (was ich nehme, fehlt dem Gegner). Dieses Verhaeltnis
ist fuer den Denial-Strang und fuer die Frage "eigenes Brett bauen gegen
Gegner stoeren" eine Kennzahl, die es bisher nicht gibt.

## par.2 Datenbasis

- Abgeschlossene Partien (`completed`) aus dem aktuellen Self-Play-Korpus.
- Je Partie **genau ein** Zahlenpaar (X, Y) = Endstand beider Seiten,
  ungeclampt (`scores_unclamped`), damit die Deckelung die Streuung nicht
  kuenstlich staucht.
- Kein Positions-Sampling. Die Frage ist eine Partie-Frage, keine
  Stellungs-Frage.

Wenn moeglich zusaetzlich derselbe Satz aus einem Heuristik-Korpus, als
Kontrast zu netzgenerierten Partien.

## par.3 Zu berechnen

1. Pearson- und Spearman-Korrelation von X und Y, mit Konfidenzintervall.
2. `Var(X)`, `Var(Y)`, `Var(D)` mit D = X − Y, sowie die daraus implizierte
   Kovarianz `Cov(X,Y) = (Var(X) + Var(Y) − Var(D)) / 2` als Gegenprobe zur
   direkt berechneten Kovarianz. Beide muessen uebereinstimmen; eine
   Abweichung ist ein Rechenfehler, kein Befund.
3. Die empirische Verteilung von D.
4. Die **gefaltete** Verteilung von D unter Unabhaengigkeitsannahme, also
   die Faltung der empirischen Randverteilungen von X und −Y.
5. Die Abweichung zwischen beiden, ausgedrueckt in
   Siegwahrscheinlichkeit: `P_empirisch(D > 0)` gegen
   `P_gefaltet(D > 0)`, und dieselbe Groesse bedingt auf Zwischenstaende
   (siehe par.4).

**Wichtig, sonst misst Punkt 5 das Falsche** (nachgetragen 2026-08-23): die
Faltung in Punkt 4 ist eine GLOBALE Konstruktion ueber die unbedingten
Randverteilungen. Fuer den bedingten Vergleich in par.4 muss sie **je
Schicht neu gebildet** werden, aus den bedingten Randverteilungen
`P(X | Zwischenstand)` und `P(Y | Zwischenstand)`. Wer die globale Faltung
gegen bedingte Empirie stellt, misst den Bedingungseffekt und nicht die
Abhaengigkeit -- und bekommt einen grossen `MAE_eng`, der nichts belegt.

## par.4 Die eigentliche Groesse: Fehler dort, wo es zaehlt

Ein globaler Vergleich von `P(D > 0)` ueber alle Partien ist zu grob, weil
er ueber Partien mittelt, in denen die Sache laengst entschieden ist. Die
Unabhaengigkeitsannahme schadet dort, wo die Entscheidung eng ist.

Gemessen wird deshalb der Fehler **bedingt auf den Zwischenstand**:
Partien werden nach dem Punktestand am Ende jeder Runde geschichtet, und
innerhalb jeder Schicht wird die empirische gegen die gefaltete
Siegwahrscheinlichkeit gestellt (Faltung je Schicht, siehe par.3).
Berichtet wird der mittlere absolute Fehler ueber die Schichten, deren wahre
Siegwahrscheinlichkeit zwischen 0,30 und 0,70 liegt.

Begruendung der Fensterwahl: ausserhalb dieses Bereichs aendert ein Fehler
in der Siegwahrscheinlichkeit die Zugwahl praktisch nicht mehr.

**Verhaeltnis zu par.2** (nachgetragen 2026-08-23). Par.2 verlangt genau ein
Zahlenpaar je Partie; die Schichtung hier laeuft ueber vier bis fuenf
Rundenenden, dieselbe Partie taucht also in mehreren Schichten auf. Das ist
zulaessig, **solange je Runde getrennt ausgewertet und berichtet wird** --
dann ist jede Schicht eine eigene bedingte Schaetzung mit einem Paar je
Partie. Ueber Runden zu poolen ist NICHT zulaessig: dann geht jede Partie
vier- bis fuenffach ein, und Waechter 1 ist gebrochen. Der Kennwert
`MAE_eng` aus par.5 ist entsprechend **je Runde** zu bilden; wo eine einzige
Zahl gebraucht wird, ist es das Maximum ueber die Runden, nicht der
Mittelwert -- die Runde mit dem groessten Fehler entscheidet, ob die
Unabhaengigkeitsannahme irgendwo schadet.

## par.5 Entscheidungsregeln, vorab festgelegt

Sei `MAE_eng` der mittlere absolute Fehler in Siegwahrscheinlichkeit aus
par.4.

- **`MAE_eng` < 0,02**: Die Unabhaengigkeitsannahme traegt. Die Behauptung
  aus par.1 ist **widerlegt**, ein eigener Differenzkopf braucht eine andere
  Begruendung als die Korrelation. Wird so im Entwurf vermerkt.
- **0,02 <= `MAE_eng` < 0,05**: Effekt vorhanden, aber in derselben
  Groessenordnung wie die Arena-Aufloesung. Kein Bau-Argument; als Kennzahl
  archiviert.
- **`MAE_eng` >= 0,05**: Die Behauptung ist belegt und beziffert. Das ist
  eine notwendige, keine hinreichende Bedingung fuer einen dritten Kopf:
  Task #12 hat einen Verteilungskopf auf die Differenz zweimal gemessen
  (2026-07-29 am alten Ziel, Nach-#34-Paket Arm 1 am WDL-Ziel), beide Male
  ohne Arena-Beleg. Ein positiver Ausgang hier eroeffnet den Kopf **nicht**
  wieder, er liefert nur die fehlende Begruendung fuer den Fall, dass er aus
  anderem Anlass wieder aufgemacht wird.

Die Schwelle 0,02 ist a priori gesetzt und nicht aus den Daten abgeleitet.
Begruendung: sie liegt unterhalb dessen, was die gepaarte Arena bei den
ueblichen Paarzahlen aufloest.

### ERGEBNIS (2026-08-24): KENNZAHL, kein Bau-Argument -- Behauptung weder widerlegt noch belegt

Gefahren mit `tools/probes/score_correlation_probe.py`, Artefakt
`score_correlation_probe.json`. Zwei Korpora: netzgenerierte Stichprobe
(stratifiziert wie das Bin-Skalen-Tor, jede 12. Datei je Generation,
248/2945 Dateien, **2.480 abgeschlossene Partien**, 0 wegen inkonsistentem
Backfill verworfen) und der komplette Heuristik-Korpus
(`data/holdout/selfplay_hold_heur_*.pkl`, 50 Dateien, 500 Partien).

**par.3, netzgeneriert:**

| Groesse | Wert |
|---|---|
| Var(X) / Var(Y) / Var(D) | 285,89 / 282,39 / **399,32** |
| Cov direkt / ueber Var-Formel | 84,4777 / 84,4777 -- **Rechenprobe stimmt** (Waechter 3) |
| Pearson r | **+0,2973**, Block-Bootstrap-95-%-KI [0,259; 0,334] (500 Resamples ueber die 248 Dateien, Waechter 1) |
| Spearman rho | +0,313 |
| P_empirisch(D>0) / P_gefaltet(D>0), global | 0,4841 / 0,4926 (Abweichung 0,0085) |

**Vorzeichen positiv: Gleichtakt**, nicht Verdraengung (par.1-Nebennutzen).
In angebotsreichen Partien punkten beide Seiten mehr, nicht auf Kosten des
Gegners -- ein erstmals bezifferter Befund fuer den Denial-Strang.

**par.4, die eigentliche Entscheidungsgroesse -- bedingt auf den
Zwischenstand** (Marge aus `state.players[i].score`, live gefuehrt, GECLAMPT
-- `scores_unclamped` ist auf jeder Partie final zurueckgeschrieben und fuer
den Zwischenstand ungeeignet, siehe Werkzeug-Kopf. Schichtung: Quantil-Bins
je Runde, bis zu 10, Mindestbelegung 15 Partien je Bucket -- eine
IMPLEMENTIERUNGSENTSCHEIDUNG, die die Prereg offengelassen hatte, hier
transparent statt stillschweigend getroffen):

| Runde | n | Buckets im Fenster [0,30; 0,70] | MAE dieser Runde |
|---|---|---|---|
| 1 | 2.480 | 8 von 8 | 0,0157 |
| 2 | 2.480 | 8 von 10 | 0,0231 |
| 3 | 2.480 | 5 von 10 | 0,0199 |
| 4 | 2.480 | 4 von 10 | **0,0390** |

**`MAE_eng` = Maximum ueber die Runden = 0,0390** (Runde 4).

**Verdikt nach par.5, wortgetreu: 0,02 <= 0,0390 < 0,05 -- KENNZAHL, KEIN
Bau-Argument.** Weder Widerlegung noch Beleg. Die Unabhaengigkeitsannahme
schadet in der Groessenordnung der Arena-Aufloesung selbst -- ein Effekt,
der da ist, aber zu klein, um allein einen dritten Kopf zu begruenden.

**Heuristik-Korpus, zum Vergleich:** Pearson r +0,2585 (KI [0,182; 0,342]),
`MAE_eng` 0,0345 -- **derselbe Tier, dasselbe Muster.** Der Effekt ist nicht
spezifisch fuer netzgenerierte Partien.

**par.9-Gegenprobe:** `Var(D) = 399,32` auf dieser netzgenerierten
Stichprobe (Fenster: 248 Dateien ueber v18/v19wdl/v19wdlsw/v20wdl/v20wdlsw,
gemessen 2026-08-24), also `std(D) ≈ 19,98`. Das liegt bemerkenswert nah an
`MARGIN_SCALE = 20` aus `PREREG_saturating_score_utility.md` par.6a --
aber die beiden Groessen sind NICHT dasselbe Objekt: die Referenz dort ist
die RMS-Marge aus neun Mensch-gegen-v21-Partien (~21, einseitig, Mensch
gewinnt 8/9, Streuung um +16,7 statt um null), hier ist es die
STANDARDABWEICHUNG der signierten, um null zentrierten Marge im
Self-Play (zwei gleich starke Netze). Die Naehe ist eine Beobachtung, kein
Beleg fuer irgendetwas -- **kein Anlass, `MARGIN_SCALE` zu drehen**, wie
par.9 selbst festlegt.

**Rechenprobe (Waechter 3):** hat auf beiden Korpora exakt gestimmt.

## par.6 Waechter

1. **Ein Paar je Partie.** Mehrere Stellungen derselben Partie sind kein
   unabhaengiger Beleg. Die Konfidenzintervalle werden zusaetzlich per
   Block-Bootstrap ueber Korpusdateien gebildet, nicht nur ueber Paare, weil
   Score-Analysen im Projekt schon einmal an unterschaetzten Paar-SEs
   gescheitert sind.
2. **Ungeclampte Werte.** Mit geclampten Endstaenden waere `Var` an den
   Raendern gestaucht und die Korrelation verzerrt.
3. **Rechenprobe.** Die zwei Wege zur Kovarianz in par.3.2 muessen
   uebereinstimmen, bevor irgendeine Zahl weitergegeben wird.
4. **Politikabhaengigkeit ausweisen.** Das Ergebnis gilt fuer die Verteilung
   der Partien, die heutige Netze erzeugen. Es ist **keine** Eigenschaft des
   Spiels. Bei einem plattenbewussten Champion ist die Messung zu
   wiederholen, weil sich dann die Punkteverteilung selbst verschiebt.

## par.7 Aufwand und Werkzeug

Reine Auswertung vorhandener Pickles, kein Training, keine Arena, keine
Engine-Aenderung.

Einlesepfad, am 2026-08-23 nachgesehen: `tools/selfplay_diversity_report.py`
ist wiederverwendbar, aber **nicht unveraendert**. Es liest den Endstand aus
dem geklemmten Feld (`:79`, `last.get("scores")`); par.2 verlangt
`scores_unclamped`. Das Feld ist vorhanden -- in je einer Stichprobe pro
Generation (v18, v19wdl, v19wdlsw, v20wdl, v20wdlsw) tragen es 100 % der
Datensaetze. Ebenfalls nachgesehen, damit es niemand erneut herausfinden
muss: eine Korpusdatei ist eine FLACHE Liste von Schritt-Datensaetzen, nicht
eine Liste von Partien; die Partiezuordnung laeuft ueber `game_id`, der
Abschluss ueber `completed`, der Endstand steht im letzten Datensatz je
`game_id`.

## par.8 Was NICHT Gegenstand ist

- Der Bau eines dritten Kopfes. Diese Prereg misst nur seine Voraussetzung.
- Die Frage, ob eine entstauchte Bin-Skala den Verteilungskopf rettet. Das
  ist eine eigene, bisher ungemessene Frage.
- Die Konsumptionsseite (gesaettigte, integrierte Score-Utility), siehe
  `PREREG_saturating_score_utility.md`.

## par.9 Nachgelagerte Verwendung (nachgetragen 2026-08-23)

`PREREG_saturating_score_utility.md` par.6a baut einen Margen-Kopf mit
eigener Skala `MARGIN_SCALE`. Deren Wert ist dort **als Referenz gesetzt**
(20), nicht aus dem Korpus abgeleitet -- aus demselben Grund, aus dem
`VALUE_SCALE = 50` nie aus Spieldaten kam (`neural_net.py:502-509`): eine
aus der Verteilung heutiger Netze gezogene Skala schreibt deren Schwaeche
fest.

Ein Zwischenstand desselben Tages hatte `MARGIN_SCALE = std(D)` gesetzt und
diese Prereg damit zur Bau-Voraussetzung gemacht. Das ist zurueckgenommen.

Was bleibt: **`Var(D)` ist die GEGENPROBE zur Referenzsetzung.** Weicht die
Self-Play-Streuung stark von der Referenz ab (neun
Mensch-gegen-v21-Partien: RMS-Marge ~21), ist das ein eigenstaendiger Befund
ueber den Abstand zwischen Netzspiel und gutem Spiel -- und kein Anlass, die
Skala zu drehen.

Am Programm dieser Prereg aendert das nichts: `Var(D)` war ohnehin als
Gegenprobe zur Kovarianz zu rechnen, `MAE_eng` bleibt die
Entscheidungsgroesse. Zu berichten ist `Var(D)` ueber abgeschlossene
Partien, ungeclampt, **mit Angabe des Fensters** -- die Zahl ist
politikabhaengig (Waechter 4), und wer sie weiterverwendet, muss wissen,
aus welchem Korpus sie stammt.
