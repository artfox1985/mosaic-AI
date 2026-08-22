<!-- STATUS: OFFEN | Frage: Wird der R5-Loeser in einen EINGEFRORENEN Anker-Loeser (Heuristik) und einen frei entwickelbaren Netz-Loeser getrennt -- und laesst sich der Value-Kopf fuer Runde 5 gut kalibrieren (Steigungs-Metrik der R5-Kalibrierung)? | Beleg: ENTWURF 2026-08-22, Nutzer-Entscheid ("dann machen wir einen eigenen solver fuer den heuristik anker. und schauen dass wir den value kopf gut kalibrieren fuer runde 5."), nichts gebaut. Anlass: 200-Knoten-Beschneidung als moegliche Schwachstelle; jede R5-Verbesserung wuerde sonst den Anker mitverschieben (Leiter-Reset-Falle, gerade erst bezahlt). -->

# PREREG-SKELETT: R5-Loeser-Trennung (Anker eingefroren) + R5-Value-Kalibrierung

Stand **2026-08-22. ENTWURF, nichts gebaut, Plan-Zeitform.** Reihenfolge
gegenueber der laufenden Seeding-Kette ist Nutzer-Entscheid; die
Value-Kalibrierung (Teil B) profitiert vom Seeding-Ausgang und sollte
danach zugeschnitten werden.

## par.1 Anlass, mit den drei Messfakten

1. Die 200-Knoten-Beschneidung ist real, aber gemessen klein: 5,8/9,5/
   13,1 % Zugwahl-Aenderungen bei 400/1000/4000 Knoten; 81,4 % gegen
   84,8 % Orakel-Uebereinstimmung (200 gegen 4000; round5.rs-Modulkopf).
   Verbesserungsversuche sind legitim, die Erwartung ist kalibriert.
2. Der Value-Kopf ist GENAU in Runde 5 am schlechtesten: Platten-
   Steigung 0,06-0,09 statt ~1 (r5_value_calibration, Pflicht-
   diagnostik), Kopf-Konflikte ballen sich ausschliesslich in R5.
   Ein multiplikativer Blend am exakten Blatt wuerde diesen Fehler
   importieren -- falls Blend, dann additiver Korrekturterm fuer den
   UNGESEHENEN Rest, und erst nach Teil B.
3. Der Loeser ist heute mit dem Heuristik-ANKER geteilt (mcts.rs:746ff)
   -- jeder Eingriff ueber einen prozessglobalen Knopf verschiebt den
   Anker mit (OnceLock-Falle) und entwertet die frisch verankerte
   Leiter. DESHALB der Nutzer-Entscheid: eigener, EINGEFRORENER
   Anker-Loeser.

## par.2 Teil A: die Trennung (Bau-Skizze)

- `round5_anchor.rs` = eingefrorene Kopie des heutigen Standes
  (c83fb35-Semantik inkl. Zufallsknoten); NUR der Heuristik-Pfad
  (mcts.rs) ruft ihn. "EINFRIEREN, NICHT REPARIEREN" gilt dort ab dann
  woertlich -- gleiche Philosophie wie wertung_progress/A4.
- `round5.rs` bleibt der NETZ-Loeser und darf sich entwickeln
  (Kandidaten-Arme, je einzeln und per-Agent verdrahtet, KEINE
  Env-Knoepfe fuer Seitigkeit): (a) Knotenbudget netzseitig anheben
  (200 war Tragbarkeits-, keine Suffizienzzahl), (b) Netz-Policy als
  Zugsortierung (Stage-3-Praezedenz; Recherche S2), (c) additiver
  Value-Korrekturterm (erst nach Teil B).
- **Abnahme der Trennung selbst**: byte-identisches Verhalten beider
  Loeser am Trenntag (Ordnungstests beider Fundstellen, A4-v2-Fixture
  bleibt gueltig und wechselt auf den Anker-Loeser als Pruefziel,
  Suite gruen, Paritaets-Hash haelt, Wheel neu). Danach ist der Anker
  gegen JEDE R5-Weiterentwicklung immun -- die Elo-Leiter bleibt
  stehen; nur Netz-Kanten-Interpretationen aendern sich mit dem
  jeweiligen Arm (normale Gating-Logik).
- Doppelpflege-Kosten sind der bewusste Preis; der Anker-Loeser
  bekommt einen NICHT-ANFASSEN-Kopfkommentar mit Verweis hierher.

## par.3 Teil B: R5-Value-Kalibrierung (Ziel-Skizze)

- **Metrik ist registriert und existiert**: die Steigung der
  r5_value_calibration (heute 0,06-0,09; "gut kalibriert" heisst
  Steigung nahe 1 OHNE Staerkeverlust). Kennlinien-Caveat 0,316 aus
  dem Alt-Befund beachten.
- Zuschnitt NACH dem Seeding-Ausgang (der Arm koennte die Daempfung
  bereits bewegen -- erst messen, dann bauen). Kandidaten, im Wissen
  um die GESCHLOSSENEN Nachbarn (Vollendbarkeits-Kalibrierungen
  uebertragen nicht; Ziel-Wechsel am Wertkopf durchgemessen):
  R5-Sample-Gewichtung im Value-Loss, rundenspezifische
  Ausgangs-Kalibrierung (Platt je Runde statt global), Nutzung des
  vorhandenen endgame_margin-Kopfs als KALIBRIER-Referenz (nicht als
  Such-Input). Auswahl + Vorabregeln beim Zuschnitt.

## par.4 OFFEN (Nutzer, beim Aufgreifen)

1. Zeitpunkt von Teil A (unabhaengig von Seeding baubar) gegen die
   laufende Kette.
2. Welche Netz-Loeser-Arme in welcher Reihenfolge (a/b/c), je mit
   Vorzeichen-Sonde vor jeder Arena (r5_chance-Muster; eine Arena fuer
   ~0,02-Punkte-Effekte waere eine erschlichene Freigabe).
3. Teil-B-Zuschnitt nach dem Seeding-par.7-Verdikt.
