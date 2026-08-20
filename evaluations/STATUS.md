# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Abgeschlossenes liegt in
**`../archive/history.md`**.

---

## DAS ZIEL (Leitstern — Nutzer-Auftrag 2026-08-17: bei jeder Priorisierung im Kopf behalten)

> *"das netz spielt die basis an sich schon gut, aber nimmt keine ruecksicht auf
> die wertungsplatten. das wollen wir via injektion -> selfplay -> ownership
> head in den griff bekommen. dann sind nochmal je partie 10 punkte und mehr
> drinnen"*

1. **Ziel: ein staerkerer Spieler**, gemessen am **direkten Duell** gegen den
   Champion. Zielgroesse: **"Sieg mit vielen Punkten"** — nicht Punkte allein.
2. **Hebel: der Plattenblick.** Die Grundmechanik spielt das Netz kompetent und
   laesst 10+ Punkte je Partie liegen.

**Klausel, die schon sechs Vorschlaege aussortiert hat:** ein Plattenzuwachs,
der Siege kostet, ist KEIN Erfolg. Ein Zuwachs bei den Zaehl-Kriterien (k3/k4)
zaehlt nicht — gefragt sind die konjunktiven k1/k2/k5.

**Vor jeder Arbeit fragen: was traegt das dazu bei?** Ownership-Kopf, Korpus,
Regler, Konjunktionsterme, LR-Schedules, Traeger-Manifeste sind WERKZEUG ohne
Eigenwert. Am 2026-08-17 wurde ein Legacy-Test gestrichen, weil die Antwort auf
diese Frage "nichts" war.

---

## FOKUS-REGEL: NUR k1 (Nutzer-Entscheid 2026-08-18)

> *"mir kommt vor du switcht wild zwischen den wertungsplatten analysen herum.
> wir sollten uns wirklich mal nur auf eine wertungsplatte fokussieren"*

**Bis auf Widerruf wird ausschliesslich k1 (Vertikale Reihen, 7 Pkt je volle
Spalte) bearbeitet.** Warum k1 und nicht eine andere — alles gemessen:

| | |
|---|---|
| Wert | 7 Punkte je Spalte, 6 Geometrien |
| Kosten | **keine** — innerhalb des k1-Bauer-Arms +7,86 Gesamtpunkte, davon 7,02 aus der Platte, Rest +0,84 |
| Synergie | Platzierung zahlt den vertikalen Lauf getrennt (`round_end.rs:366`), Spaltenbau liegt auf derselben Achse wie normales Spiel |
| Luecke | Netz 20/156 Partien (13 %), Bauer 419/1000 (42 %) |
| Label | Vollendbarkeits-Sperre bestanden, traegt in Runde 3-5 |

**Was das AUSSCHLIESST**, obwohl dazu Befunde vorliegen: k2 (Diagonalen), k4
(Aeussere Felder), k5 (Eckplatten), k6 (Spezialfelder). Ihre Messungen bleiben in
den Preregs erhalten und gelten weiter, werden aber **nicht weiterverfolgt**. Erst
wenn k1 traegt, kommt k2 — so war es in
`PREREG_plate_policy_supervision.md` registriert und so bleibt es.

**Konkret heisst k1-only:**

- Erfolgsregeln nennen nur k1. (Die registrierten "k1 oder k2"-Klauseln bleiben
  gueltig, werden aber auf k1 gelesen — die strengere Lesart.)
- Der Verbraucher wird nur mit `MOSAIC_OWNERSHIP_GEW` auf k1 gefahren.
- Nebenbefunde zu anderen Kriterien werden protokolliert und NICHT verfolgt.

**Der Anlass war Drift, nicht Erkenntnis:** am 2026-08-18 sind aus k1-Messungen
heraus Analysen zu k6 (Spezialkuppel-Platzierung, Stapel-Ziehungen), k5 und k4
entstanden. Alle drei lieferten echte Befunde — und keiner davon brachte k1 voran.

---

## FAHRPLAN DIESER GENERATION (Nutzer-Auftrag 2026-08-18, woertlich)

> 1. *"modell erstellen dass mit dem ownership head aktiv die züge steuert und
>    den champ schlägt"*
> 2. *"anschließend mit dem neuen champ self plays (smoke test) überprüfen ob
>    hier genug diversität vorhanden ist für den ownership head"*
> 3. *"dann self plays für v22 erstellen"*

Die Reihenfolge ist bindend: **kein v22-Korpus, bevor Schritt 1 und 2 stehen.**
Der Grund ist gemessen und nicht theoretisch — ein Korpus, den ein Netz erzeugt,
das die Platten nicht steuert, enthaelt die Zielhandlung nicht, und genau daran
ist die Destillation zweimal gescheitert (`PREREG_corpus_distillation.md`
par.10.7 warm, par.10.9 kalt).

### Schritt 1 — Stand: SIEG-HAELFTE ERFUELLT, PLATTEN-HAELFTE NICHT

**Nutzer-Einwand 2026-08-18, und er ist entscheidend:** *"ja nur spielt er noch
nicht auf die wertungsplatten"*. Der Sieg allein erfuellt Schritt 1 NICHT — der
Hebel des ganzen Vorhabens ist der Plattenblick, nicht die Siegquote.

Praezisiert man, WELCHE Platten der Regler bewegt (gegen den Nullarm,
Block-Ebene, Schwelle 2,571), wird das Bild eindeutig:

| Kriterium | Δ | Block-t |
|---|---:|---:|
| **k3** Mehrfarbige Felder | +1,59 | **2,58** |
| **k5** Eckplatten | +0,34 | **2,79** |
| k1 Vertikale Reihen | −0,09 | 0,23 |
| k2 Diagonale Reihen | +0,07 | 1,00 |

Er spielt auf die **kurzen Ketten** und laesst die teuren Geometrien liegen —
dieselbe Kettenlaengen-Grenze wie in der Skalen-Rechnung
(`PREREG_ownership_coupling.md` par.3), hier in Arena-Zahlen. Die Siege kommen
mit einiger Wahrscheinlichkeit von k3/k5.

**Folge fuer die Reihenfolge, und sie ist scharf:** wuerde dieser Stand als
Champion promoviert, erzeugten seine Self-Plays k3/k5-Verhalten und weiter kein
k1/k2 — der v22-Korpus enthielte die Zielhandlung erneut nicht. Genau die Falle,
gegen die die Fahrplan-Reihenfolge gebaut ist. **Schritt 1 braucht also beides:
Sieg UND Bewegung bei k1/k2.**

#### Die Sieg-Haelfte, dokumentiert (Zurechnung fehlt)

`alphazero_v21-b18_best.onnx` @400 gegen Champion @400, 407 Seeds, keine Remis:

| Arm | Siege | gegen 50 % |
|---|---:|---|
| Regler **AUS** | 211/407 = 51,8 % | p = 0,457 — Paritaet |
| **Produktform D1** `0.1,0.3` | **236/407 = 58,0 %** | **p = 0,0013** |
| **Konjunktionsform D1** | **229/407 = 56,3 %** | **p = 0,0115** |

**Mit aktivem Kopf schlaegt `b18_best` den Champion signifikant, ohne ihn
nicht** — und "aktiv steuert" ist keine Behauptung: 402 von 407 Partien laufen
anders als im Nullarm. Zwei Vorbehalte, beide offen:

1. **Kein Brettwechsel.** Alle drei Arme liefen auf Brett 0. Der Seiteneffekt
   ist damit unkontrolliert; die DIFFERENZ zwischen den Armen ist es nicht
   (gleiche Seite, gleiche Seeds), wohl aber die absolute Aussage gegen den
   Champion. Naechste Messung: derselbe Arm mit vertauschten
   `--model`/`--model-b` und eigenem `--out-prefix`.
2. **Gepaarte Zurechnung fehlt.** Gegen den Nullarm ist der Zuwachs NICHT
   signifikant (exakter McNemar: Produktform p = 0,066, Konjunktionsform
   p = 0,2025). Der Sieg ueber den Champion steht, die Zurechnung zum Kopf
   nicht.

**NICHT FREIGEGEBEN (Nutzer 2026-08-18):** *"es ist good to know, aber noch
nicht von mir freigegeben den champion herauszufordern"*. Also **kein
Brettwechsel-Lauf, kein Gating, keine Promotion** auf diesem Stand — die Zahlen
sind Kenntnisstand, kein Auftrag. Der Grund liegt oben: die Platten-Haelfte
fehlt, und ein Champion ohne k1/k2 wuerde den v22-Korpus wieder ohne die
Zielhandlung erzeugen.

Wenn Schritt 1 spaeter freigegeben wird, waere die Reihenfolge: erst
Brettwechsel (billig, entscheidet Vorbehalt 1 und verdoppelt die Paarungen fuer
Vorbehalt 2), dann Gating.

### Schritt 2 — die Diversitaet ist GEBAUT, nicht erhofft

**Nutzer-Hinweis 2026-08-18:** *"das haben wir schon mal festgehalten. hier
variieren wir den 'zug' zur wertungsplatte mit dem seed. sprich es wird dann
eine gleichverteilung geben bei der sich die partien mal mehr und mal weniger
auf die wertungsplatten fokussieren"*. Der Mechanismus existiert und ist
verdrahtet — nachgeprueft:

| Baustein | Stelle |
|---|---|
| `MOSAIC_WERTUNG_STREUUNG_MAX`, Default **0,0 (aus)** | `net_mcts.rs:1152`, Registry `knob_registry.rs:81` |
| Ziehung: SplitMix64 aus dem Partie-Seed, **gleichverteilt in [0, max]** | `net_mcts.rs:1164` |
| Produktions-Verdrahtung im Self-Play, je Partie | `self_play.rs:3134-3136` |
| Wirkt auf | `wertung_shaping_weights()` → `[w; 8]` (`net_mcts.rs:1218`) |
| Ausgesetzt fuer Label-Rollouts (sonst Rauschen im Ziel) | `net_mcts.rs:1105 ff.` |

**Korrektur einer frueheren Formulierung in dieser Datei:** hier stand, der
Smoke Test muesse pruefen, ob der Champion "zu deterministisch" spielt. Das ist
die falsche Richtung — die Streuung erzeugt die Diversitaet aktiv, unabhaengig
davon, wie deterministisch das Netz ist. Der Smoke Test prueft, ob die
gezogene Spreizung sich in den LABELS niederschlaegt.

**Zwei Punkte, die dabei zu beachten sind (beide aus dem Code, nicht vermutet):**

1. Die Streuung dreht das **heuristische** Plattengewicht (`wertung_progress`),
   nicht das Ownership-Gewicht. Fuer Label-Diversitaet ist das richtig — die
   Partien variieren im Plattenfokus, also variieren die Ownership-Ziele mit.
2. `wertung_shaping_weights()` liefert `[w; 8]` — **derselbe** Wert fuer alle
   acht Kriterien. Die Streuung variiert also den Plattenfokus INSGESAMT, nicht
   je Kriterium. Damit kann k1/k2 weiter untersampelt bleiben, obwohl die
   Spreizung insgesamt gut aussieht. **Der Smoke Test muss deshalb die
   Positivrate von k1 und k2 EINZELN ausweisen**, nicht nur ein Diversitaetsmass
   ueber alle Kriterien. Vergleichsmassstab sind die Raten des v21-Fensters.

### Schritt 3 — v22-Korpus

Erst danach. Design liegt auf Halde (Abschnitt "v22-FENSTER"), NICHT eingeplant.

### Zwei neue Vorregistrierungen (2026-08-18) — beide OFFEN, nichts gebaut

Anlass: externe Durchsicht mit zwei ausgearbeiteten Spezifikationen. Beide sind
gepruefte Antworten auf `DOSSIER_ownership_head.md` Abschnitt 7, beide in
Plan-Zeitform, **keine** ist freigegeben.

| Datei | Greift an | Stand |
|---|---|---|
| `PREREG_asymmetric_curriculum.md` | 7(1) Wegsymmetrisierung — der Value-Kopf hat den Plattenbau nie als Vorteil gesehen | Sperre par.5 vor dem Training; **erzeugt einen Self-Play-Korpus** |
| `PREREG_reachability_target.md` par.12 (Arm P) | die Saettigung des Vollendbarkeits-Labels in Runde 1-2 | **Vorab-Sperre BESTANDEN 2026-08-19**, Stauchung CAP 12 festgelegt; faellt in den ohnehin anstehenden Relabeling-Durchlauf |

**Die eine offene Entscheidung, die nicht beim Bauen fallen darf:** der
asymmetrische Arm erzeugt einen neuen Korpus. Der Fahrplan sperrt
Korpus-Erzeugung bis Schritt 1 und 2 stehen; Praezedenz fuer einen *Lehr*-Korpus
ausserhalb der Reihe ist `PREREG_ownership_corpus.md`. Einordnung — Lehrkorpus
(jetzt) oder Schritt 3 (spaeter) — ist **Nutzer-Entscheid und offen**
(`PREREG_asymmetric_curriculum.md` par.9).

Was aus den externen Spezifikationen **verworfen** wurde, steht mit Begruendung
in den Dateien selbst (`asymmetric_curriculum` par.8, `reachability_target`
par.13) — damit es nicht in einem halben Jahr erneut vorgeschlagen wird.

---

## STAND 2026-08-20 — ZIELWECHSEL GEMESSEN: NICHT-ERFOLG, mit umgekehrtem Vorzeichen

> **KORREKTUR, noch am selben Tag (Implementierungs-Review, par.15 der
> Prereg): das T+S-Verdikt unten ist ein DOSIS-ARTEFAKT-VERDACHT und
> traegt NICHT als Ziel-Aussage.** Der Vollendbarkeits-Kopf liefert
> e_k1 Median **36,1** (Konjunktionsform) gegen 0,26 beim
> Realisierungs-Kopf — mit dem am alten Kopf kalibrierten Nenner 1 war
> der T+S-Arm **wertblind** (Shift 1,0, q auf 1,0 geclampt, 100 % der
> Zustaende): die Suche spielte Prior + Rauschen. Auch die beiden
> Offline-Tau-Werte sind entwertet (q lag in 80/80 Faellen auf der
> Clamp-Grenze). **Gueltig bleiben:** b24-Null 221/407 (Zielwechsel
> kostet keine Staerke), S gegen N flach, alle Linsen-Freisprueche.
> **WIEDERHOLUNG GEFAHREN (noch am 2026-08-20, par.16): NICHT-ERFOLG,
> diesmal ohne Artefakt.** Nenner S' 3,3 / T+S' 463, Saettigungs-Wache
> bestanden (Clamp 0,0 %). k1 flach (T+S' gegen S' +0,23, Block-t 1,11;
> gegen eigenen Nullarm −0,05) — aber KEIN Siegverlust: **T+S' 233/407,
> nominell bester Arm der Kampagne** (gegen b24-Null p=0,169, n.s.).
> Korrekt dosiertes Vollendbarkeits-Shaping ist kostenlos, nur
> k1-wirkungslos. Endverdikt nach par.7-Klausel: das Ziel ist nicht der
> Engpass; es bleibt die Policy-Seite. Der Ownership-Verbraucher-Strang
> ist damit ENDGUELTIG durchgemessen. Die Zahlen darunter bleiben als
> Protokoll des ersten Laufs stehen.

Der Vollendbarkeits-Kopf (`v21-b24`, Arm P) ist trainiert, offline geprueft
und in der registrierten N/S/T+S-Arena gemessen (par.14 der Prereg, alle
Zahlen dort). Kurzfassung:

| Arm | Siege | k1-Punkte |
|---|---:|---:|
| N (b18, Regler aus) | 211/407 | 0,90 |
| S (b18, hoerbare Skala) | 214/407 | 0,85 |
| b24-Null (neues Ziel, Regler aus) | **221/407** | — |
| **T+S (neues Ziel, hoerbare Skala)** | **194/407** | **0,18** |

- **T+S gegen S: k1 −0,67 Punkte, Block-t −3,73** — signifikant in die
  FALSCHE Richtung; dazu Siegverlust (McNemar p=0,0045) und mehr
  Strafleiste (+1,83, Block-t 2,87). Nur die Spezialfelder profitieren
  (+0,56, Block-t 7,00) — wieder das Kurze-Kette-Muster.
- **S gegen N: flach** (k1 t −0,18, Siege p=0,84) — die hoerbare Skala
  allein bewegt beim alten Ziel nichts. Damit sind Skala UND Ziel als
  Engpass-Erklaerungen GEMESSEN und GEFALLEN.
- **Der Zielwechsel allein kostet keine Staerke** (b24-Null 221/407,
  numerisch ueber b18-Null auf denselben Seeds) — der Schaden entsteht
  erst, wenn der Kopf die Suche steuert.
- **Die Offline-Sonde hatte es angekuendigt:** Kopf-Ordnung seed-stabil
  (Tau +0,970), aber OHNE Bezug zum eigenen Trainings-Praedikat
  (Tau −0,03 gegen die Puffer-Summe der Nachfolgezustaende). Der Kopf
  lernt das Ziel auf Zustands-Ebene (own_val fiel monoton 0,407→0,361),
  unterscheidet aber die Geschwister eines Knotens nicht danach —
  dieselbe Fehlerklasse wie der Feld-Kopf-Befund vom 18.08. („sieht die
  Absicht kaum").

**Damit ist der Ownership-VERBRAUCHER-Strang in allen gemessenen Formen
negativ** (Produktform, Konjunktionsform, hoerbare Skala, neues Ziel).
Was laut par.7-Registrierung bleibt: die **Policy-Seite**
(orakel-abgeleitete Supervision, AZAL-Muster) als letzter unversuchter
Strang — und unabhaengig davon das **asymmetrische Curriculum** am
VALUE-Kopf (von diesem Ergebnis unberuehrt; Rechnungen liegen, Umfang ist
Nutzer-Entscheid).

Zwei am 2026-08-20 gefangene Fallen stehen in der Fallen-Tabelle
(Produktform liest keine Atome → `MOSAIC_OWNERSHIP_CONJ=1` Pflicht in
Ownership-Armen; Arena nur EXKLUSIV fahren).

---

*(Abgeschlossen und nach `../archive/history.md` verschoben: STAND 2026-08-19 — Orakel-Abstand in Menschenpartien, Schritt-2-Vorpruefungen (Saettigung + Arm-P-Sperre), Werkzeug-Stand 2026-08-19. Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)".)*

---

*(Abgeschlossen und nach `../archive/history.md` verschoben: STAND 2026-08-17 (Nachmittag) — Korpus policy-maskiert, Regler-Strang, Konjunktionsterme, "Zwei von drei Wegen", Ownership-Kopplung, Frozen Trunk b22, Kalibrierung (inkl. "Kalibrierung gefittet"), Feld-Kopf-Messung, Shaping-Nenner-Strang, LR-Schedules, Cold-Start-Saettigung b20. Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)".)*

## OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Stand |
|---|---|
| **Gewichtsarm 4,0** | Vorabregel hat ihn freigegeben (`PREREG_ownership_weight_new_window.md` par.7); Nutzer-Entscheid 2026-08-17: **weiter hinten geparkt** |
| **Stoerungs-Baustein Stufe 2** | gehoert zum **Moon-Order-Kopf**, keine Einzelentscheidung mehr |
| **Korpus mit hoeheren Sims nachgenerieren** | **ABGELEHNT** (Nutzer 2026-08-17) — nicht neu vorschlagen |
| **Fester Bewertungssatz** | Bauer-Satz: 300 Dateien / 3000 Partien in `data/holdout/`, fertig 2026-08-18. Details (Zusammensetzung, Abnahme, Herkunft) siehe `../archive/history.md`, Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)". |
| **Push** | NIE ohne ausdrueckliche Nutzer-Anweisung (Nutzer-Regel 2026-08-20); Stand wird als "n Commits voraus" gemeldet |

*(Abgeschlossen und nach `../archive/history.md` verschoben: die beiden Fallen-Tabellen vom 2026-08-17 (Zeitkosten) und vom 2026-08-17 (Nacht) / 2026-08-18. Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)".)*

## FALLE vom 2026-08-20 — CPU-NEBENLAST VERSTUEMMELT ARENA-PARTIEN

Zwei parallel laufende Arena-Instanzen (je `--threads 10` plus Worker):
derselbe 8-Partien-Smoke lieferte unter Last ZWEI VERSCHIEDENE Ergebnisse
(eine Partie endete 3:1 — offensichtlich abgewuergt), ohne Last dreimal
byte-identisch (auch identisch zum Vortag; das frische Wheel war NICHT die
Ursache, per Dreifach-Vergleich ausgeschlossen). **Regel: Arena-Messungen
laufen EXKLUSIV — keine zweite Arena, keine Sonden mit Suchlaeufen, kein
Training parallel.** Vorflug-Determinismus-Checks zaehlen nur, wenn sie
unter denselben Lastbedingungen laufen wie die Messung selbst (praktisch:
beide exklusiv). Belege: `paired_arena_env_reach_conj_smoke1/2.json`
(unter Last, abweichend) gegen `reach_smoke1/3/4.json` (exklusiv,
identisch).

---

*(Abgeschlossen und nach `../archive/history.md` verschoben: PARTIE-REPLAY IST EXAKT (`PREREG_action_id_logging.md`), erledigt 2026-08-18. Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)".)*

---

## TASK-INDEX (nur OFFEN/LAUFEND)

| Task | Status |
| --- | --- |
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: braucht >=6 arena-entschiedene Paare (Stand ~3); Kandidaten-Metriken werden je Gating mitgefuehrt. `PREREG_post34_package.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT

**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die v21-Task-Queue.**
`PREREG_v22_window.md`: gleiche Form wie v21 (29.450 gesamt), juengster
Value-Posten 3.550 v19wdl-Rest + 1.450 v19wdlsw, Schwarm bleibt 74 %.
**Ab v22 ist die Rotationsregel stationaer.** Gating-H0-Vorbehalt: neuer
Batch desselben Generators braucht Suffix (`v20wdlb`).
**Hinweis 2026-08-14**: der Ownership-Korpus ist KEIN v22-Fenster -- er liegt
ausserhalb der Rotation (`data/ownership_corpus/`, additiv via
`--extra-data-dir`) und aendert diese Halde-Entscheidung nicht.

---

## GELTENDE REGELN (kompakt)

- **Seed-Skala der Arena bei n=400 (gemessen 2026-08-09)**: dieselbe
  Konfiguration (k=1, Champion@600 vs Heuristik@150dyn) ergab **76,0%**
  mit Basis-Seed 20260820 und **81,75%** mit 20260828 -- **5,75
  Prozentpunkte allein durch den Seed**. Das ist groesser als die
  meisten Effekte, die wir messen (λ, k=2, Denial-Varianten liegen alle
  darunter). Folge: **ungepaarte Vergleiche zwischen zwei Laeufen sind
  wertlos**, auch wenn beide n=400 haben. Jeder A/B braucht identische
  Basis-Seeds im SELBEN Instrument; wo zwei getrennte Laeufe noetig sind
  (unterschiedliche Sim-Budgets), muss der Basis-Seed gleich gesetzt und
  die Paarung ueber den Spielindex selbst gerechnet werden.

- **Champion**: `v21_2d_brierbest` seit 2026-08-09, **Elo 1358**
  [1292, 1434] (Vorgaenger `v20_2d_opp_brierbest` 1295). Die
  Erst-Schaetzung nach dem Gating (1416, CI +-92) beruhte auf einer
  einzigen Gegnerkante; mit Anker- und Champion-2-Kante sinkt das
  Niveau auf 1358 und das CI wird 23% enger (+-71) -- der ABSTAND zum
  Vorgaenger (+63) bleibt. Belegt den Wert von
  Promotions-Checkliste Punkt 3+4. Gating 75:45
  (SPRT-H1 nach 60 Paaren, p=0,0059) UND Frisch-Seed-Replikation 97:63
  (H1 nach 80 Paaren, p=0,0095) -- die Fruehstopp-Regel ist damit
  erfuellt. Alt-Messset-Brier 0,18636 vs 0,18749. **Erster Champion aus
  reiner Korpus-Skalierung**: identisches Rezept, +40% Fenster
  (29.450 Partien) von einem staerkeren Generator, plus
  `--endgame-head`. champion.txt gesetzt (wirkt nach Server-Neustart).
  Generator-Naming: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.

- **Fenster-Pinning -- ZWEI Variablen, nicht eine (verschaerft
  2026-08-09 nach einem Beinahe-Fehler)**: Ein Trainingsstart im
  v21-Fenster braucht BEIDE:
  
  ```
  export MOSAIC_DATA_EXCLUDE="$(cat evaluations/v21_exclude_regex.txt)"
  export MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_v21.json"
  ```
  
  **DRITTER Beinahe-Fehler derselben Klasse (2026-08-19): die Regex-Datei
  veraltet.** Das b18-FENSTER (Korpus-Sockel-Linie: b18/b19/b23/b24) schliesst
  zusaetzlich `selfplay_v19wdlsw_` aus — `v21_exclude_regex.txt` enthaelt das
  NICHT. Ein b24-Start mit der txt-Datei lud 3371 statt 2945 Dateien (800
  v19wdlsw zu viel); aufgefallen an der Kompositions-Zeile VOR dem Cache-Bau,
  Lauf gestoppt und neu gestartet. **Regel: das Exclude fuer einen
  Wiederholungs-/Nachfolgelauf IMMER aus dem `data_exclude`-Feld des
  REFERENZ-Manifests ziehen** (materialisiert:
  `evaluations/b18_window_exclude_regex.txt` aus dem b23-Manifest), nie aus
  einer benannten txt-Datei, deren Stand niemand prueft. Fuer die
  b18-Linie gilt zudem `MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_own.json"`.
  
  `MOSAIC_CARRIER_MANIFEST` wurde beim `t_d_vw08`-Start VERGESSEN. Der
  Default ist `policy_carrier_manifest_v20.json`, also ein ANDERER
  Traeger-Satz: der Arm haette mit einer anderen Policy-Maske als
  `t_d_vw04` und als `v21_2d` trainiert und waere als Sweep-Arm wertlos
  gewesen -- ohne Fehlermeldung, nur mit plausiblen Zahlen. Der Lauf
  wurde gestoppt und korrekt neu gestartet; ein angefangener
  Falsch-Cache war noch nicht auf der Platte.
  **Verifikation ist Pflicht und zwar VOR dem Weggehen**: die
  Cache-Zeile muss `📦 Lade HDF5-Cache (2651 Dateien)` lauten.
  Steht dort `Lade Daten aus 2651 Dateien...`, ist der Cache-Schluessel
  anders -- Lauf sofort stoppen und die Ursache klaeren, NICHT einen
  Neubau durchlaufen lassen (er zementiert das falsche Fenster).
  Beweisweg fuer die Ursache (bei Bedarf wiederholbar): Cache-Key aus
  `str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+...+carriers`
  nachrechnen und mit den `data/.cache_*.h5`-Namen vergleichen -- die
  v21-Caches sind `26e304f5d2c7` (train, 2.651 Dateien) und
  `8a04a7143bbe` (val, 294). Merke: der **Cache-Key ist der einzige
  Waechter** ueber die Traeger-Wahl, das Lauf-Manifest protokolliert
  `MOSAIC_CARRIER_MANIFEST` NICHT (`engine_config`/`python_constants`
  waren zwischen richtigem und falschem Lauf identisch).
  Harmlos dagegen: die 55 archivierten v18-Dateien sind seit 10:16 aus
  `data/` heraus, `MOSAIC_DATA_EXCLUDE` schliesst nun 0 statt 55
  Dateien aus -- Split und Dateiliste sind trotzdem BEWEISBAR identisch
  (rekonstruiert und verglichen: 2.651/294 in beiden Faellen gleich).

- **NACHSCHUB BEI GATING-FEHLSCHLAG -- KORRIGIERTE FASSUNG
  (Nutzer 2026-08-09)**: Die Streichung des Nachschub-Ventils vom
  2026-08-07 war **generationsspezifisch** (v20-Zyklus, weil dort eine
  lange Nebentask-Liste offen war) und **KEINE stehende Anweisung** --
  ich hatte sie faelschlich verallgemeinert (auch in
  PREREG_v21_window.md, dort korrigiert).
  **ERSETZUNG (frischer Batch desselben Generators + Rausrotieren einer
  Alt-Generation) ist VERWORFEN** -- Nutzer-Argument, und es ist
  richtig: das ist indirekt mehr Volumen vom SELBEN Champion, waehrend
  die Diversitaet der alten Generationen aus dem Fenster fliegt. Genau
  die Generationen-Spreizung ist aber der Grund, ueberhaupt Alt-Material
  mitzufuehren.
  **Was bleibt: gezielte INJEKTION** (Sockel-Partien dazu, nichts
  verdraengt -- schont die Diversitaet). Bedingungen, damit daraus kein
  "solange nachlegen bis der Kandidat gewinnt" wird:
  
  1. Umfang und Entscheidungsregel VOR der Injektion schriftlich
     (Mini-Prereg), nicht nach dem verlorenen Gating improvisiert.
  2. Einmalig und begrenzt je Generation (Vorschlag: +2.000 Sockel),
     kein iteratives Nachlegen.
  3. Naming: derselbe Generator erzeugt ein Batch mit
     Unterscheidungs-Suffix (`v20wdlb`), sonst Datei-Kollision.
  4. Lesart des Ergebnisses: ein Sieg NACH Injektion belegt "die
     Generation brauchte mehr Policy-Material" -- NICHT, dass eine
     etwaige Rezept-Aenderung des Kandidaten gewirkt hat. Diese
     Unterscheidung muss im Verdikt stehen.
  5. Diagnostischer Rueckenwind erwuenscht (Policy-Wacht: fallen die
     Orakel-Metriken gegen die Vorgeneration, ist die Policy-Klasse der
     belegte Engpass), aber keine harte Vorbedingung -- Nutzer-Entscheid.

- **FENSTERGROESSE: FIXIERTE BASIS, Injektion ist die benannte Ausnahme
  (Nutzer-Entscheide 2026-08-09)**: 29.450 Partien / 2.945 Dateien / ~4,8 Mio.
  Zustaende bleiben die stehende Groesse. Die Rotation haelt sie
  konstant -- pro Windung 12.000 NEUE Partien (4.000 Sockel @600 +
  8.000 Schwarm @150), gleich viel altes Material rotiert raus. Folgen:
  (a) Kosten pro Generation KONSTANT (~18h Self-Play + ~3h Cache +
  ~3,5h Training), kein Anwachsen; (b) das Fenster wird mit jeder
  Windung FRISCHER statt groesser; (c) RAM/Cache-Budget stabil
  (~13 GB im Training, ~1 GB auf Platte).
  **Nicht neu aufrollen**: der Dosis-Befund ("Volumen half 6/6") ist
  eine stehende Versuchung, das Fenster generell zu vergroessern -- die
  Entscheidung dagegen ist bewusst gefallen (planbare Kosten,
  stationaeres Design ab v22). Eine DAUERHAFTE Vergroesserung braucht
  einen ausdruecklichen neuen Nutzer-Entscheid. Die einmalige,
  vorregistrierte Injektion bei Gating-Fehlschlag (s.o.) ist davon
  ausgenommen und veraendert die Basisgroesse nicht.

- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.

- **PROMOTIONS-CHECKLISTE (Nutzer-Hinweis 2026-08-09: die Kader-Praxis
  wurde bis dato nicht konsequent umgesetzt)** -- bei JEDEM
  Champion-Wechsel vollstaendig abarbeiten, nicht aus dem Gedaechtnis:
  
  1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
  2. Elo-Kante **Gating** (Champion-1) -- inkl. Replikations-Zeile, falls
     Fruehstopp <150 Paare.
  3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
     Fruehstopp** (Praezedenz v18/v19/v20-Verankerung).
  4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- **das ist der
     Punkt, der bei v20 UND v21 zunaechst fehlte**; ohne ihn ruht die
     Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating:
     CI +-90 Punkte).
  5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
     Eintrag in die #29-Buchfuehrung.
     5b. **Anzeige-Kalibrierung nachziehen**: die Platt-Parameter A/B des
     NEUEN Champions in `server.py` (`_DISPLAY_CAL_A/_B`) eintragen --
     sie sind modellspezifisch. Quelle: `tools/platt_fit.py --models
     models/alphazero_<neu>.pth`. Ohne das zeigt die GUI die
     Gewinnwahrscheinlichkeit mit der Kurve des VORGAENGERS an.
     5c. **sigma/Prior-Balance messen** (neu 2026-08-09, aus Task G):
     `tools/gumbel_scale_calibration.py --model <neu> --sims 400
     --n-states 300`, ~10 min. Der Aera-Wechsel v18->v21 hat das
     Verhaeltnis von 1,232 auf **2,287** verschoben (delta_q verdoppelt,
     delta_ln(prior) unveraendert) -- R3 liegt mit 2,972 praktisch auf
     der Wiedereroeffnungs-Schwelle. **Ueberschreitet die
     Gesamt-Kennzahl 3, oeffnet sich die c_visit/c_scale-Familie per
     REGEL wieder** (kein Ermessen). Zugleich Verfallsdatum-Waechter
     fuer die H0-Befunde der Wurzel-Regler-Familie: die wurden in einem
     anderen Balance-Regime gemessen.
  6. STATUS-Champion-Zeile + history-Kapitel.
     **Nachtrag-Schuld ERLEDIGT** (Klarstellung 2026-08-10): die v20-Kante zu
     `v19_best` lief am 2026-08-09 -- 114:76 ueber 190 Partien, SPRT-H1 nach 95
     Paaren, p=0,0043 (`elo_history.csv` Zeile 53,
     `paired_gating_v20_vs_v19best_nachtrag.json`). Die alte "fehlt"-Zeile hier
     hat mich zweimal dazu verleitet, die Messung erneut vorzuschlagen.
     **Elo-Fragen am Primaerregister `elo_history.csv` pruefen, nicht an dieser
     Datei.**

- **LOESCHEN NUR MIT EXPLIZITER RUECKFRAGE (Nutzer-Regel 2026-08-08,
  dritter Vorfall dieser Klasse -- "inakzeptabel")**: Kein Loeschen,
  Verschieben oder Ueberschreiben von Dateien, Ordnern oder Worktrees
  ohne vorherige, den KONKRETEN Pfad benennende Nutzer-Freigabe.
  Ausnahme: das eigene Scratch-Verzeichnis.
  Im Einzelnen:
  
  1. **Eine FRAGE ist keine Anweisung.** "Ist X noch aktuell?", "kann
     man X weg?", "brauchen wir X?" verlangen eine ANTWORT. Handeln
     erst nach einem Imperativ, der das Ziel nennt.
  2. Als Loeschen gelten auch: `git worktree remove`, `git checkout --`,
     `git reset --hard`, `git clean -fd`, `mv` aus dem Projekt heraus,
     `rm` auf generierte Artefakte (Caches sind KEINE Ausnahme -- die
     Freigabe vom 2026-08-08 galt fuer sechs namentlich genannte Dateien).
  3. Vor jeder freigegebenen Loeschung: Ziel ANSEHEN (Inhalt, Groesse,
     Reparse-Points bei Worktrees -- Junction-Vorfall 2026-07-24), das
     Ergebnis der Pruefung BERICHTEN, und nur dann ausfuehren.
  4. Gilt fuer Sub-Agents identisch und steht in jedem Agent-Prompt.
  5. "Aufraeumen" ist niemals selbst-autorisiert -- auch dann nicht,
     wenn etwas offensichtlich veraltet ist.

- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.

- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).

- **AUFLOESUNG SCHLAEGT SPARSAMKEIT (Nutzer-Regel 2026-08-08)**: Wenn
  eine Entscheidung an einer Differenz haengt, die UNTERHALB der
  Auflösung des Offline-Instruments liegt (Value-Seite: Brier-Gaps
  <0,015 sagten 0/4 die Arena voraus; gemessene Seed-Skala ~0,0006),
  dann darf das Offline-Mass die Entscheidung NICHT tragen -- auch nicht
  als Spar-Vorfilter ("nur gaten, wenn Brier X schlaegt"). Stattdessen
  die ARENA in die Abwaegung nehmen und die Kosten AUSRECHNEN, nicht
  schaetzen: ein Gating (~1-1,5h CPU, 200 Paare @400) ist regelmaessig
  BILLIGER als das Training, das man sich mit dem Vorfilter sparen
  wollte (~3,5h GPU) -- und es ist das einzige validierte Instrument.
  Wer auf einem blinden Mass spart, spart die billige Ressource und
  riskiert die teure Fehlentscheidung.
  **Ausnahme Policy-Seite**: die Orakel-Metriken (Prior-Masse Top-3,
  Kendall-Tau) sind arena-validiert (7/7) und DUERFEN als Vorfilter
  dienen -- so entschieden bei #35b (beide Metriken schlechter -> kein
  Gating). Der Unterschied ist der Validierungsstand, nicht die
  Bequemlichkeit.
  Zusatznutzen, den man mitnehmen soll: jedes gefahrene Gating liefert
  ein arena-ENTSCHIEDENES Paar -- die Waehrung, in der #29 (Validierung
  eines Offline-Value-Praediktors) bezahlt wird (Stand ~3, noetig >=6).

- **Aggressions-/Denial-Programm GESCHLOSSEN** (2026-08-07): alle
  Knoepfe auf Default (w=0, λ=0, ε=0, bias=1); "gate what you ship";
  Wiedervorlage nur mit messbar schaerferem opp-Kopf
  (PREREG_aggression_style_measurement/PREREG_denial_tiebreak).

- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).

- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).

- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).

- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blind_spot.md`, Tasks E/F/G dazu
  geschlossen -> history): Q-Skalierungs-Varianz ist JA protokolliert
  (`tools/gumbel_scale_calibration.py`), **Ueberlebensrate im
  Sequential Halving NEIN** -- vorhanden sind `root_child_q`,
  `root_num_actions(_considered)` und `max_depth`, aber nicht, welcher
  Kandidat welche Halbierungsphase uebersteht. Bewusst nicht
  nachgeruestet: Task E hatte zuerst zeigen muessen, ob die MENGE
  stimmt (Ergebnis: Miss-Rate 1,21%, weit unter der 5%-Schwelle).

## Architektur, Stand jetzt (aktualisiert 2026-08-06)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):

- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2`.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting`, Blattwert = exakter Endscore inkl.
  Wertungsplatten. **Seit 2026-08-10 EXPECTIMINIMAX, nicht mehr reines
  Alpha-Beta**: Zufallsknoten an den Aufdeck-Stellen der verdeckten
  Chip-Zuordnung (16 der 20 Chips sind aus R1-4 bekannt, unbekannt ist nur
  die Fabrik-Position der restlichen 4). Kein Pruning in Zufallsknoten
  (Star1/Star2 bewusst weggelassen). `NODE_BUDGET=200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus),
  `MOSAIC_R5_CHANCE_NODES` (**Default AN** seit 2026-08-10, `=0` stellt das
  Altverhalten her), `MOSAIC_R5_NODE_BUDGET`, `MOSAIC_R5_NET_SOLVER`
  (Default an).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):

- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`, seit
  Task #28 zusaetzlich `opp_points` (nur in Modellen, die damit trainiert
  wurden -- Engine erkennt ihn per Output-NAME und faellt sonst auf
  Bestandsverhalten zurueck). **`plate_head` wurde am 2026-08-10 gebaut und
  wieder ENTFERNT** -- der Ownership-Kopf ist der Randlayer.
  `ownership` ist seit 2026-08-10 **140 breit** (72 Feldlabels + 68
  Konjunktionen, Breite an config.py:117-118 + Label-Bauer verifiziert
  2026-08-14); `OWNERSHIP_WEIGHT` steht in `config.py` weiter auf 0 --
  der Champion-Kopf ist untrainiert. Naechster Lauf mit Gewicht 0,2 +
  `--conjunction` ist der Korpus-Trainingslauf (PREREG_ownership_corpus.md).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, **`VALUE_OPP_EPSILON = 0,0`** (war 0,1 bis Schema 19).
- **Punkte-ZIEL (Schema 20, 2026-08-10)**:
  `points_val = tanh(own_total/VALUE_SCALE)` -- der Gegner-Anteil ist
  ENTFERNT. Fuer VOR Schema 20 trainierte Modelle bedeutet ihr
  `points`-Ausgang weiter `own - 0,1*opp`; fuer die Spielstaerke belanglos,
  weil die Ausgabe im Suchpfad ohnehin verworfen wird
  (`POINTS_UTILITY_WEIGHT = 0` und `w = 0`).
- **Value-ZIEL (#34-Verdikt, Schema 17 unveraendert gueltig)**: `values_wdl`
  = TD-Blend aus Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang;
  Alt-Datei-Bootstraps werden beim Cache-Bau Platt-entstaucht
  (A=0,0051/B=1,9269), `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben
  roh. Training: `--value-head wdl --select-by-brier` (KEIN destretch-Flag
  mehr noetig). **Das Ziel ist margen-BLIND** -- siehe Abschnitt STAND,
  "warum das Netz nicht punktoptimiert spielt".
  Policy-Traeger-Manifest **`data/policy_carrier_manifest_v21.json`**
  (Default in `neural_net.py` ist noch die v20-Datei -- ein Trainingsstart
  im v21-Fenster MUSS `MOSAIC_CARRIER_MANIFEST` setzen, s. Fenster-Pinning
  oben), maskiert Alt-Dateien ausser 135 v19wdl + 45 v18, plus
  `carrier_prefixes: ["selfplay_v20wdl_"]`; alles im Cache-Key.
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> **`v21_2d_brierbest`**.

---

## Task #38 (geparkt, Arbeitskreis "Spaeter" mit #31): Moon-Head-Feinschliff (2026-08-05)

Befund aus einer Interesse-Frage des Nutzers, Code verifiziert. Der Kopf
selbst ist solide (Plackett-Luce-Faktorisierung der Mond-Reihenfolge aus
dem Policy-Raum, Labels vom exakten Rundensolver, Prior-Aufteilung in der
Expansion). Zwei nie untersuchte Punkte fuer spaeter:

1. **Loss-Gewicht**: `moon_nll` wird mit VOLLEM Gewicht 1,0 in den
   Policy-Loss addiert (train.py, `p_loss + moon_nll[sun_mask].mean()`)
   -- bei NLL ~0,5-1 gegen Policy ~1,9 beansprucht ein Teilproblem, das
   nur Sonnenzuege betrifft, potenziell ~1/3 des Policy-Gradienten. Nie
   gesweept (VALUE_WEIGHT-Blindfleck-Muster). Als Arm in einen
   kuenftigen Loss-Gewichts-Sweep.
2. **Label-Horizont** (Nutzer-Einordnung 2026-08-05, RELATIVIERT):
   Referenz maximiert den RUNDENendstand (`solve_round_final_score`).
   Da die Fabriken zu Rundenbeginn NEU befuellt werden, ist der
   Wirkhorizont einer Reihenfolge im Wesentlichen die laufende Runde --
   das Solver-Label ist also naeher am Optimum als zunaechst vermutet,
   Restpunkt sind allenfalls Randeffekte. Falls Labels je aus der Suche
   kommen (root_child_q aus #35 liefert die Q-Ordnung der Varianten ab
   v20 gratis), waere das ein billiger A/B, kein Pflichtumbau.
   Kein akuter Bedarf: Policy-Seite ist ueber die Orakel-Metriken
   arena-validiert, inkl. PL-Aufteilung.
3. **Das Label ist EGOZENTRISCH -- damit ist "Fabriken aushungern"
   strukturell unerreichbar** (Nutzer-Frage 2026-08-16 "was ist mit
   fabriken aushungern gemeint", Code am selben Tag geprueft). Die
   Mond-Stapelreihenfolge ist der EINZIGE Hebel im Spiel, mit dem man dem
   Gegner gezielt nur vergiftete Optionen hinterlaesst: bei kleinen
   Fabriken bestimmt der nehmende Spieler die Reihenfolge, und spaeter ist
   nur die OBERSTE Fliese nehmbar (docs/engine_manual.md, Phase 1 B). Wer
   das steuert, kann den Gegner in Farben zwingen, die seine Musterreihen
   ueberlaufen lassen -- Strafpunkte ohne eigenen Einsatz, und der Zwang
   ist strukturell (die Runde endet erst, wenn alles leer ist; wer keine
   gueltige Aktion hat, MUSS passen).
   **AKTENLAGE KORRIGIERT (ungeprimter Review 2026-08-20, am Code
   bestaetigt): `moon_order_target` ist ein beweisbarer NO-OP** — die
   Zielfunktion `solve_round_final_score` liest nur `players[pi]`
   (Cache-Key `tiling_key`), die Mondreihenfolge lebt aber in
   `state.factories`; alle Permutationen scoren identisch, das Label ist
   immer die rohe Beutelreihenfolge (80/80-Sonde). Der Kopf trainiert auf
   RAUSCHEN und zieht dabei potenziell ~1/3 des Policy-Gradienten (Punkt 1
   oben). Auch der unten skizzierte "billige Zuschnitt" (eigener minus
   Gegner-Rundenendstand) waere aus demselben Grund ein No-Op. Der Text
   darunter bleibt als Ideen-Protokoll stehen, seine Praemisse ("bewertet
   jede Reihenfolge") ist widerlegt. Details:
   `PREREG_implementation_review_unprimed.md` par.7.
   **FOLGE FUER DEN #38-ZUSCHNITT (Nutzer-Entscheid 2026-08-20: hier
   festgehalten, bleibt im Arbeitskreis "Spaeter"):** wenn #38 angegangen
   wird, ist die Reihenfolge jetzt klar vorgezeichnet —
   (a) **billigster erster Arm: `moon`-Loss-Gewicht 0** (ein Trainingslauf
   + Gating). Das testet Punkt 1 (Loss-Gewicht) und den No-Op-Befund in
   einem: der Kopf zieht heute bis zu ~1/3 des Policy-Gradienten fuer ein
   NACHWEISLICH konstantes Rauschziel — Gewicht 0 ist die
   Nullhypothesen-Messung, ob das Gradient-Budget woanders mehr traegt.
   (b) Ein ECHTES Reihenfolge-Ziel braucht eine Zielfunktion, die
   `state.factories` liest (Reihenfolge-bewusste Variante von
   `solve_round_final_score` oder Suche-basierte Labels via root_child_q)
   — teurer, erst nach (a) sinnvoll. (c) Der alte "billige Zuschnitt"
   (minus Gegner-Endstand) ist als No-Op gestrichen. Zusaetzlich zu (a)
   gehoert der Python-Vielfachheiten-Bug der Zielrepraesentation
   (`neural_net.py:1799-1806`, 42 % der Labels betroffen) mit behoben,
   falls je ein echtes Ziel kommt.
   **Das Netz hat den Kopf dafuer, aber nie das Ziel** (Alt-Text): `moon_order_target`
   (`self_play.rs:634`) probiert Reihenfolgen durch und bewertet jede mit
   `solve_round_final_score(state, pi)` (`tiling_solver.rs:494`) -- also
   ausschliesslich dem EIGENEN Rundenendstand. Der Gegner kommt in der
   Bewertung nicht vor. Der Kopf kann Aushungern also nicht lernen, egal
   wie gut er wird.
   **Billiger Zuschnitt, falls je angegangen**: nur das Label aendern
   (eigener Rundenendstand MINUS Gegner-Rundenendstand, oder als eigener
   Arm), Bau bleibt unberuehrt. Vorbehalt: das ist eine neue
   Stoerungs-Wette, und Stoerung hat in diesem Projekt zweimal verloren
   (k6-Kuppeldraft, Farbzaehlung v1) -- vorher gehoert eine billige
   Diagnose davor, ob die Reihenfolge-Freiheit ueberhaupt genutzt wird
   (Praezedenz #39: Rotation/Position der Startkuppel waren tote
   Freiheitsgrade). Herkunft der Idee: Reddit-Rueckfrage eines Spielers
   nach adversarialen Faellen.

## Task #39 (geparkt, Arbeitskreis "Spaeter" mit #31/#38): Startkuppel-Platzierung (2026-08-06)

Nutzer-Beobachtung "setzt sie gefuehlt immer an dieselbe Position" --
am Code bestaetigt und MECHANISCH erklaert
(`self_play.rs::choose_start_placement`): der Farb-Score ist
POSITIONS-unabhaengig (summiert nur Fabrik-Farbhaeufigkeiten je Feld),
der Eckbonus fuer alle 4 Ecken identisch (0,5), Ties behaelt der erste
Kandidat -> IMMER Ecke (0,0); die Feld-Summe ist zudem
ROTATIONS-invariant -> immer 0 Grad. Position/Rotation sind tote
Freiheitsgrade; nur die Platten-WAHL variiert. Gilt ueberall (GUI,
Arena, Self-Play; Startplatzierung ist policy-maskiert, das Netz lernt
sie nie).

**Nutzer-Einordnung (2026-08-06, schaerft den Zuschnitt)**: die Ecke an
sich ist strategisch RICHTIG (Rand/Diagonale/Eckplatten honorieren sie
alle) -- das Problem ist die MONOTONIE, nicht die Position.
**KORREKTUR (Nutzer 2026-08-06, zweite Runde)**: auch der Ecken-Rang
(3 oben / 8 unten) ist KEIN Bewertungsfehler -- Kuppelzeile 0 wird von
den SCHNELLSTEN Musterreihen (1-2, Kapazitaet 1-2 Steine) gespeist: die
obere Ecke kommt frueher in Wertung + Orthogonal-Bonus und wird
zuverlaessiger ueberhaupt komplett; die 8 Punkte unten haengen an den
traegsten Reihen (5-6). Der (0,0)-Tie-Break loest den Trade-off implizit
RICHTIG auf. Verbleibende Substanz von #39:
(1) ROTATION -- bestimmt Farb-Ausrichtung zur Brettmitte und
Sonderfeld-Lage, heute verschenkt (Score rotationsinvariant);
(2) MONOTONIE/Tie-Break -- Diversitaets-Frage (GUI-Abwechslung +
Korpus-Vielfalt), keine Staerke-Frage.
**Verbesserungs-Optionen (bei Angehen abzuwaegen)**:
a) Heuristik-Upgrade: Rotations-Bewertung + randomisierter Tie-Break
   unter nahezu gleichwertigen Kandidaten; jede Aenderung per Arena
   gegen den Bestand pruefen (die Strategie-Intuition des Koordinators
   lag hier zweimal daneben, die des Nutzers zweimal richtig).
b) Prinzipiell: Platzierung in den Aktionsraum der Suche -- ACHTUNG
   NUM_ACTIONS-Aenderung macht alte Checkpoints unbrauchbar
   ([[num-actions-change-breaks-old-checkpoints]]), teuer.
**Randbedingung**: NICHT waehrend einer laufenden Kampagne aendern
(verschiebt die Self-Play-Zustandsverteilung); fruehestens v21-Setup.
Nebenaspekt: die heutige Uniformitaet kostet auch Zustands-Diversitaet
im Korpus.

## Task #31 (vorgemerkt): Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem (2026-08-03)

**Nutzer-Auftrag**: Staerke-Skalierung fuer Mensch-Spiele; Einschaetzung
"Sims allein richten es nicht" ist KORREKT und hier besonders: (a) R5-
Alpha-Beta + Tiling-DFS spielen sim-unabhaengig exakt -- eine 20-Sims-KI
spielt trotzdem perfekte Endspiele; (b) Gumbel+Policy-Prior traegt auch
Mini-Budgets -- flacher, aber nicht menschlich-fehlbar.

**Design-Skizze (3 Hebel je Stufe)**: Sims-Budget + Endspiel-/Tiling-
Degradation (R5-Knotenbudget-Override bzw. Policy-Sampling statt Solver,
Tiling greedy statt exakt bei "leicht") + Fehler-Injektion via Root-
Temperatur-Sampling mit Q-GAP-DECKEL (nur plausible Fehler <=3-5 Punkte;
menschlich-fehlbar statt gleichmaessig-flach; loest auch Ausrechenbarkeit).
Stufen: extrem=Champion@600-800 (optional lambda_aggr als Stil),
schwer=heutiger Stand @400, mittel=~100-150 Sims + Deckel-Sampling +
reduziertes R5-Budget, leicht=~8-16 Sims + Temperatur hoeher + epsilon +
Greedy-Tiling. ABGERATEN: alte Generationen als Stufen (Wartung,
OneDrive-Risiko, Regel-Fix-Inkompatibilitaeten, "gleichmaessig schwach").

**Kalibrierung**: vorhandene Elo-Leiter + Heuristik-Anker; je Konfiguration
n=150 vs 2 Anker, Ziel-Baender ~leicht 700-800 / mittel ~1000 / schwer
~1150-1200 / extrem=Champion. Umsetzung nach Muster Task #28
(Laufzeit-Parameter + Server-Preset + GUI-Dropdown). OFFEN (Nutzer):
Ziel-Baender ok? Darf "leicht" sichtbar Endspiele verstolpern?

**GATE (Nutzer-Entscheid 2026-08-03): ZURUECKGESTELLT** -- wird erst
angegangen, wenn ein Champion existiert, der auch gute menschliche
Spieler wirklich fordert. Bis dahin bleibt die Prioritaet auf
Staerke-Arbeit (v20-Zyklus, Value-Head-Front #29/#30, lambda=0.7-
Kandidat), nicht auf Schwierigkeits-UX.
