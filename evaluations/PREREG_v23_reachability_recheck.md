<!-- STATUS: OFFEN | Frage: Untersagt der erste auf SELF-PLAY-Eigenpartien trainierte spaltenkompetente Ownership-Kopf (v23) Zellen, die laut Vorrats-Praedikat noch vollendbar waeren -- und lohnt dann der Zielwechsel auf Vollendbarkeit am Konsument-Instrument? | Beleg: NICHTS GEMESSEN. Ausloeser noch nicht eingetreten, aber NAEHER (Stand 2026-08-31): das v22-Self-Play laeuft seit dem 2026-08-30 (Tor-Revision par.3b.12 hat die alte Stopp-Regel abgeloest), v23 ist nicht trainiert. Registriert 2026-08-28 auf Nutzer-Entscheid als eigene Prereg (vorher par.17 der Erreichbarkeits-Prereg); faellig NACH dem v23-Training. -->

# PREREG: Erreichbarkeits-Nachpruefung am v23-Kopf (Wiedervorlage aus PREREG_reachability_target.md par.17)

Stand **2026-08-28**, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

## par.1 ANLASS UND AUSLOESER

`PREREG_reachability_target.md` par.16 hat den Zielwechsel des
Ownership-Kopfs (Vollendbarkeit statt Eintreten) als NICHT-ERFOLG
geschlossen -- gemessen in einer Aera, in der alle Koepfe auf spaltenarmem
Spiel trainiert waren. Die dortige Diagnose bleibt aber strukturell wahr:
ein Eintretens-Ziel auf EIGENPARTIEN ist selbsterfuellend (der Kopf spiegelt
die eigene Politik). b01 ist davon nicht betroffen (Lehrerkorpus); der erste
betroffene Kopf wird **v23** sein, sobald er auf dem v22-Self-Play-Korpus
trainiert wird.

**Ausloeser dieser Prereg: das abgeschlossene v23-Training** (der erste
Ownership-Kopf auf einem spaltenkompetenten SELF-PLAY-Korpus). Nicht
frueher -- die Stufe-0-Diagnose befragt die KARTE des trainierten Kopfs;
vor dem Training gibt es nichts zu messen. Wecker-Anker:
`PREREG_v23_window.md` par.4b.

## par.2 STUFE 0 (trainingsfrei): Karten-Diagnose

Frage: unterschaetzt v23s Eintretens-Karte die Vollendbarkeit? Messgroesse:
Anteil der Spaltenzellen, die das Vorrats-Praedikat
(`ist_zelle_vollendbar`, column_build.rs:563, Pruefstelle bei Ausfuehrung
neu verifizieren) noch erlaubt, deren Karten-Wahrscheinlichkeit aber unter
einer vorab festzulegenden Schwelle liegt ("vom Kopf als tot kartiert").
Bezugsgroessen: dieselbe Diagnose auf b01s Kopf (Lehrerkorpus-Kopf, gleiche
Zustaende) als Vergleichsarm. Block-SE auf Dateiebene. Schwellen und
Zustandsstichprobe werden VOR dem Lauf in dieser Datei nachregistriert
(sie haengen von v23s tatsaechlicher Kartenverteilung ab -- eine heute
gewaehlte Schwelle wuerde gegen eine unbekannte Verteilung raten).

Faellt die Unterschaetzung klein aus: Wiedervorlage schliesst OHNE Training,
das Eintretens-Ziel bleibt bestaetigt nicht der Engpass.

## par.3 STUFE 1 (nur nach positiver Stufe 0): Zielwechsel am Konsument-Instrument

Zielwechsel-Arm wie in `PREREG_reachability_target.md` par.14/16, aber:

* auf dem spaltenkompetenten v22-Self-Play-Korpus statt der Alt-Aera,
* gemessen am inzwischen validierten KONSUMENT-Instrument
  (`PREREG_heuristic_v2_long_rows.md` par.3b.6: Tiling-Pol, argmax,
  Block-t ueber Dateibloecke) statt der damaligen Shaping-Arme.

Dritter Arm, in der Alt-Aera nie getestet: **Rollenteilung statt
Zielwechsel** -- Eintretens-Karte als WERT (graduierte Absicht), hartes
Vorrats-Praedikat als MASKE (nachweislich tote Zellen exakt auf 0).

Abgrenzung: der Vollendbarkeits-FILTER im Aktionsraum
(`PREREG_v23_window.md` par.4, Wecker-Liste) filtert ZUEGE in der Suche;
hier geht es um FELDWERTE im Tiling-Konsumenten.

## par.4 WAS DIESE PREREG NICHT IST

Keine Wiedereroeffnung von `PREREG_reachability_target.md` -- deren par.16
bleibt ENTSCHIEDEN (die dortige Frage war die Alt-Aera-Frage). Diese Datei
traegt die NEUE Frage der neuen Aera und wird nach dem v23-Training
konkretisiert (Schwellen, Stichprobe), dann gefahren.
