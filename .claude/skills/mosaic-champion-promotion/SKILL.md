---
name: mosaic-champion-promotion
description: Ablauf beim Champion-Wechsel in diesem Projekt - neues Netz wird amtierender Champion. Nutze das, sobald ein Kandidat das Gating bestanden hat. Deckt ab - set_champion, die drei Elo-Kanten (Gating, Anker, Champion-2), Pflicht-Diagnostiken, Anzeige-Kalibrierung in server.py, sigma-Prior-Waechter, Netz-Paritaets-Fixture, Nachziehen von STATUS und Historie.
---

# Champion-Wechsel

**Die Liste ist `docs/promotion_checklist.md`. Lies sie, bevor du anfaengst,
und arbeite sie dort ab -- nicht aus dem Gedaechtnis und nicht aus dieser
Datei.** Sie ist der kanonische Ort; diese Datei nennt nur den Ablauf und die
Stellen, an denen es in der Vergangenheit schiefging.

## Der Ablauf in sechs Schritten

1. `tools/set_champion.py <neu>`
2. Elo-Kante **Gating** gegen Champion-1
3. Elo-Kante **Anker** (`Heuristik_hv1_anchor`), festes n=150 ohne Fruehstopp
4. Elo-Kante **Champion-2** (Vorvorgaenger, @400)
5. Pflicht-Diagnostiken am Sieger, inklusive 5b Anzeige-Kalibrierung,
   5c sigma/Prior-Balance und 5d Netz-Paritaets-Fixture
6. STATUS-Champion-Zeile und history-Kapitel nachziehen

## Die Stellen, an denen es schiefging

- **Schritt 4 fehlte bei v20 UND v21.** Ohne die Champion-2-Kante ruht die
  Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating: CI +-90 Punkte).
  Das ist der am haeufigsten vergessene Schritt.
- **5b vergessen heisst: die GUI zeigt die Gewinnwahrscheinlichkeit mit der
  Kurve des VORGAENGERS.** Die Platt-Parameter sind modellspezifisch
  (gemessene Drift: v19 B=1,93 / t34 0,97 / v21 0,906).
- **5d vergessen heisst: der Suite-Test schlaegt fehl** -- mit der Anleitung
  in der Fehlermeldung. Alt-Fixturen verfallen mit ihrem Champion.
- **Elo-Fragen am Primaerregister `evaluations/elo_history.csv` pruefen**,
  nicht an Chronik-Texten. Eine veraltete "fehlt"-Zeile hat zweimal zu
  Doppel-Vorschlaegen derselben Messung gefuehrt.
- **Cross-Aera ist der Normalfall** (Nutzer-Entscheid 2026-08-29): das
  Anker-Wheel wird NICHT bei jedem Motorschritt nachgezogen. Aendert sich die
  Engine grundlegend, hilft kein Nachziehen -- dann braucht es einen
  Elo-Recheck mit neuem Leiter-Segment, und Kanten ueber die Fix-Grenze werden
  nie gemischt.

## Randbedingungen

- Jede Kante ist ein Messlauf: Skill `mosaic-measurement-run` gilt (Exklusivitaet,
  laufzeit-Block, Block-Ebene).
- Ein Wheel und die `.pth` liegen IM Artefakt, das sie ausfuehren
  (`frozen_champions/<name>/`), kein Sammelordner.
- Das Heuristik-Anker-Parameterpaket wird NICHT angefasst -- es definiert die
  Elo-Leiter.
