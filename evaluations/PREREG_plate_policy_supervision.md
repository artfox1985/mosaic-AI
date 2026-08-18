<!-- STATUS: OFFEN | Frage: Laesst sich "dieser Zug baut die Spalte" als AKTIONS-Signal aus dem Zustand lernen -- und weiss der Ownership-Kopf es schon, ohne dass es die Zugwahl erreicht? | Beleg: offen, nichts gebaut. Anlass: zwei externe Durchsichten 2026-08-18 plus die vier geschlossenen Wege am Verbraucher. -->

# PREREG: Plattenziel auf AKTIONS-Ebene — Prototyp k1, Runde 5

Stand **2026-08-18**, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

**Der Paradigmenwechsel, um den es geht** (Formulierung der zweiten externen
Durchsicht, uebernommen weil sie den Kern trifft):

> **NICHT:** Ownership → stärkerer Wert-Shift → Agent soll Platte mögen
> **SONDERN:** Plattenziel → exaktes/solverbasiertes Aktionssignal → Policy lernt, wie man die Platte baut

**Nutzer-Bedingung 2026-08-18:** k1 ist das Ideal-Experiment und bleibt der
Einstieg — 7 Punkte, sechs Felder, klare Kettenstruktur, innerhalb des
Bauer-Arms nachweislich **gratis** (+7,86 Gesamtpunkte, davon 7,02 aus der
Platte, Rest +0,84), Netz 20/156 gegen Bauer 419/1000. Erst wenn k1 traegt,
kommt k2.

---

## par.1 DIE BEIDEN EXTERNEN DURCHSICHTEN (2026-08-18, aufgenommen)

### par.1.1 Erste Durchsicht — vier Punkte

1. **Symmetrie-Falle aufloesen.** Bauer-Arme gegen Basisspiel statt gegen sich
   selbst; zusaetzlich **isolierte Value-Supervision** (Value-Kopf auf
   asymmetrischem Korpus nachziehen, Policy unangetastet). *Bewertung: der
   Isolations-Gedanke ist neu und sauberer als alles bisher Vorgeschlagene, weil
   er die Value-Frage von der Policy-Frage trennt.*
2. **Orakel-Validierung der Ordnung** ueber `sibling_ranking_diagnostic`. *Deckt
   sich mit `PREREG_ownership_coupling.md` par.6.3 Stufe 2 — siehe aber par.2
   unten, das Instrument ist kein Orakel.*
3. **Zielwechsel auf Erreichbarkeit.** *Registriert als
   `PREREG_reachability_target.md`; das dort vorgeschlagene Instrument
   (`round5.rs`) traegt fuer fruehe Runden nicht, stattdessen das vorhandene
   Vollendbarkeits-Praedikat.*
4. **Nenner je Kriterium** und **UVFA-Druck**: Loss-Maskierung, kein Gradient
   fuer k1 wenn k1 nicht ausliegt. *Die Maskierung ist neu und billig; sie trifft
   den gemessenen Defekt (k6 reagiert mit falschem Vorzeichen, k5 gar nicht).
   Nebenwirkung, zu messen: jedes Kriterium sieht nur noch die ~3/8 Partien, in
   denen es aktiv ist — bei k2 mit 2005 Positiven ein realer Datenverlust.*

**Eine methodische Korrektur:** die erste Durchsicht stuetzt Punkt 1 auf den
Kreuzarm-Vergleich (Bauer-Arme 26,7–30,3 Punkte gegen Arm A 25,5). Der ist
**konfundiert** (verschiedene Arme, verschiedene Einstellungen) und im Dossier
auch so markiert. Belastbar ist der Vergleich INNERHALB des k1-Arms.

### par.1.2 Zweite Durchsicht — der Hauptversuch

1. **Plate-Policy-Head**: dritter Kopf neben Policy und Value, auf
   **Aktionsebene** trainiert — nicht "war die Partie erfolgreich", sondern
   "welcher verfuegbare Zug erhoeht unter optimalem Spiel die Chance auf die
   aktive Platte".
2. **Plate Advantage statt Ownership**: Ziel nicht "wird Feld X am Ende mir
   gehoeren", sondern `Δ_plate(action) = optimal_final_plate_score(action) −
   optimal_final_plate_score(parent)` — und zwar **als Trainingssignal, nicht
   als Laufzeit-Regler**.
3. **Asymmetrisches Training zuerst**, Arme A/B/C, und nur den Value-Effekt
   messen.
4. **"Plate Coach"**: Ownership bleibt drin, ist aber nicht mehr der
   Verbraucher, sondern das Zwischenverstaendnis ("ich weiss, welche Struktur
   ich anstrebe"); der Coach lehrt "welche Aktion fuehrt dorthin".
5. **k1 zuerst isolieren**, k2 danach.

---

## par.2 KORREKTUR DER TRAGENDEN ANNAHME — das Geschwister-"Orakel" ist keines

Beide Durchsichten setzen voraus, dass ein exakter Solver ueber
Nachfolgezustaende vorliegt. **Geprueft, und er liegt nicht vor.**

`sibling_ranking_diagnostic` nennt `crate::mcts::evaluate` "exakter DFS-Solver
(Ground Truth)" (`self_play.rs:3819-3821`). Diese Funktion ist aber
(`mcts.rs:122`, `:80`):

    player_total = solve_round_final_score(state, pi)
                 + wertung_progress(player, scoring_tile_ids)
                 + projected_unplaceable_penalty(player)

Das ist eine **heuristische Blattbewertung**. "Exakter DFS" meint: exakte
Tiefensuche MIT dieser Blattfunktion — nicht spieltheoretisches Optimum.

**Und die Pointe: `wertung_progress` steckt darin** — der plattenbewusste
Heuristik-Term, den das Netz nie bekommen hat und der die Elo-Verankerung bei
1000 traegt. Eine Policy-Supervision aus dieser Quelle waere also
**heuristik**-abgeleitet, nicht orakel-abgeleitet. Genau die Klasse Lehrer, die
beim k1-Bauer aus gutem Grund verworfen wurde (Nutzer-Einwand 2026-08-18: eine
handgebaute Praeferenz ohne Weitblick).

**Exakt ist nur der Rundenhorizont:** `round5.rs` (Runde-5-Minimax, exakte
endaware Wertung) und die Rundenwertung selbst. *Nicht heute nachgeprueft: die
Exaktheit von `round5.rs` im Detail — sie ist aus der Modul-Doku uebernommen.*

**Folge, und sie ist die wichtigste dieser Registrierung:** die
Prototyp-Eingrenzung der zweiten Durchsicht — *"nur k1 + Runde 4/5 +
Geschwister-Orakel"* — ist richtiger, als sie begruendet wurde. Sie ist nicht der
billige Anfang, sondern **die Grenze dessen, was exakt labelbar ist.**

---

## par.3 ZWEITE KORREKTUR — der asymmetrische Korpus kann GEGEN uns lernen

Die zweite Durchsicht setzt den asymmetrischen Bauer an Platz 1. Dagegen steht
ein gemessener Umstand: der Bauer ist eine **Praeferenzschicht ohne Weitblick**,
die die Suche ueberstimmt, wo sie greift. Haertere Varianten haben die
Spielstaerke zerstoert — die Beschneidung der Aktionsmenge ergab Endstaende von
**6–15 statt 47,80** mit Strafleiste bis 23, und `ueberpraesenz_vorzug` brach die
Netz-Staerke auf **2/20** (beides `column_build.rs` Modulkopf, gemessen).

Ist der Bauer schwaecher als das Basisspiel, dann lehrt ein asymmetrischer
Korpus den Value-Kopf **das Gegenteil**: "die plattenbauende Seite verliert".
Das waere schlechter als die heutige Neutralitaet.

**Daraus wird ein anderer Versuch:** nicht Praemissen-Test, sondern
**Lehrer-Qualifikation**. Die Frage ist nicht "gewinnt Plattenbau", sondern "ist
dieser Lehrer brauchbar". Genau das ist die Lehre der AZAL-Arbeit: der Lehrer
muss BESSER sein, nicht bloss anders.

---

## par.4 DER PROTOTYP — k1, Runde 5, Geschwisterzuege, KEIN Training

**Er beantwortet zwei Fragen auf einmal**, und das ist der Grund, ihn vorne
anzustellen:

1. Die Frage der zweiten Durchsicht: *entsteht ueberhaupt ein lernbares "dieser
   Zug baut die Spalte"-Signal?*
2. Die offene Stufe 2 aus `PREREG_ownership_coupling.md` par.6.3: *ist die
   stabile Ordnung des Kopfes RICHTIG?* Bisher ist nur belegt, dass sie stabil
   ist (Kendall-Tau +0,942 bei k1, +0,943 bei k2, ueber zwei
   Determinisierungs-Seeds) — eine stabil FALSCHE Ordnung haette denselben Test
   bestanden.

**Anordnung.** Runde-5-Drafting-Stellungen aus dem Held-out-Satz, je Partie eine,
k1-Platte aktiv. Je Stellung alle Geschwisterzuege. Fuer jeden:

| Groesse | Quelle |
|---|---|
| **exaktes Label** `Δk1(action)` | exakte Endwertung nach dem Zug minus vor dem Zug, **nur die k1-Komponente** (`round5.rs`-Horizont) |
| Ordnung des Ownership-Kopfes | wie `tools/probes/sibling_order_stability.py`: `q_an − q_aus` mit `MOSAIC_OWNERSHIP_GEW` nur auf k1 (streng monoton in `e[1]`, also ordnungsgleich) |
| Ordnung der Policy | Log-Priors derselben Kandidaten aus dem Gumbel-Trace |

Gemessen wird **Kendall-Tau** zwischen exaktem Label und (a) Kopf-Ordnung,
(b) Policy-Ordnung. Dazu die Spreizung des Labels ueber die Geschwister.

---

## par.5 VORAB-ENTSCHEIDUNGSREGEL (woertlich, vor der ersten Messung)

> **(A) Traegt das Label ueberhaupt?** Ist die Spreizung von `Δk1` ueber die
> Geschwister in der Mehrheit der Stellungen **null**, gibt es auf dieser Ebene
> nichts zu lernen, und der Prototyp endet hier ohne Aussage ueber die Methode.
>
> **(B) Weiss der KOPF es?** Tau(Label, Kopf-Ordnung) signifikant **> 0**
> (einseitig, p < 0,05, ueber die Stellungen): die Information ist im Rumpf
> vorhanden und erreicht die Zugwahl nur nicht. → **Der Plate-Policy-Head ist
> der richtige naechste Bau**, denn es fehlt die Uebersetzung, nicht das Wissen.
>
> Tau **≤ 0**: die stabile Ordnung des Kopfes ist stabil **FALSCH**. Damit ist
> Stufe 2 aus `PREREG_ownership_coupling.md` par.6.3 negativ entschieden, jede
> Verstaerkung des Kopfsignals ist ausgeschlossen (auch die Nenner je
> Kriterium), und der **Zielwechsel** (`PREREG_reachability_target.md`) wird
> zum Hauptversuch.
>
> **(C) Weiss die POLICY es schon?** Tau(Label, Policy-Ordnung) wird
> mitprotokolliert, **ohne** Entscheidungsregel. Ein hoher Wert waere der
> deutlichste Beleg fuer die Dossier-Diagnose, dass der Prior Bescheid weiss und
> der Value-Backup ihn ueberstimmt.

**Jeder der drei Ausgaenge fuehrt woanders hin.** Das ist Absicht: der Prototyp
ist eine Weiche, kein Bestaetigungsversuch.

---

## par.6 WAS DER PROTOTYP NICHT ENTSCHEIDET

- **Uebertragung auf fruehe Runden.** Runde 5 ist, wo Spalten FERTIG werden; die
  Entscheidungen, die sie ermoeglichen, fallen in Runde 1-3. Ein positives
  Ergebnis in Runde 5 belegt Lernbarkeit **dort**, nicht dort, wo es zaehlt.
  Fuer die fruehen Runden bleiben nur die Heuristik (schwacher Lehrer, par.2)
  oder das Vollendbarkeits-Praedikat (obere Schranke,
  `PREREG_reachability_target.md`).
- **Ob k1-Bau siegbringend ist.** Der Kostenbefund (+0,84 Rest) ist eine
  Korrelation innerhalb eines Arms, keine Elo-Aussage.
- **Die Symmetrie-Falle.** Sie betrifft den Value-Kopf und bleibt unberuehrt.
- **Runde 1.** Der Regler ist dort gemessen bitgleich wirkungslos, Ursache
  ungeklaert.

---

## par.7 SCHLACHTPLAN — Reihenfolge und Begruendung

Abweichend vom Ranking der zweiten Durchsicht (dort: asymmetrischer Bauer
zuerst), Nutzer-Zustimmung 2026-08-18 unter der Bedingung, dass k1 der Einstieg
bleibt:

| # | Versuch | Warum diese Stelle | Risiko |
|---|---|---|---|
| **1** | **Prototyp par.4** (k1, Runde 5, exaktes Label) | einzige Quelle mit exaktem Label, kein Lehrer-Risiko, und Weiche fuer alles Weitere | gering, offline, kein Training |
| **2** | **Loss-Maskierung je Kriterium** (par.1.1 Punkt 4) | trifft den gemessenen Defekt ohne neue Daten | duenne Kriterien verlieren Daten |
| **3** | **Vollendbarkeits-Ziel** (`PREREG_reachability_target.md`) | bricht die selbsterfuellende Prophezeiung, Praedikat existiert | obere Schranke |
| 4 | **Lehrer-Qualifikation** des Bauers, dann asymmetrischer Korpus + isolierte Value-Supervision | erst wenn belegt ist, dass der Lehrer nicht schwaecher ist | Gegenlernen (par.3) |
| 5 | **Nenner je Kriterium** (`PREREG_ownership_coupling.md` B2/B4) | macht laut, was vorher richtig sein muss | verstaerkt einen Fehler 50-fach |

**Warum 1 vor 2 und 3:** es ist das einzige, dessen Label nicht auf einer
Heuristik oder einer Schranke ruht. Sagt es nein (Ausgang B mit Tau ≤ 0), sind 2
und 5 Makulatur — und das erfahren wir mit einem Offline-Versuch statt mit drei
Trainings.

**Warum 5 zuletzt:** die Nenner je Kriterium sind gemessen und stehen bereit
(k0 ~17, k1 ~1, k2 ~0,3 statt einheitlich 50). Sie wuerden ein Signal um das
~50-fache verstaerken, dessen Richtigkeit erst Versuch 1 klaert. Diese
Reihenfolge ist eine Selbstkorrektur: sie wurden zwei Stunden vorher noch als
naechster Schritt vorgeschlagen.

## par.8 ERGEBNIS (leer bei Registrierung)
