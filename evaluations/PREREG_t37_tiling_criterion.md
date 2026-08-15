<!-- STATUS: ENTSCHIEDEN | Frage: Ist reines P(Sieg)-Ranking beim Tiling-Abschluss besser als das Bestandskriterium punkte*P(Sieg) (Task #37)? | Beleg: Eigener Ergebnis-Abschnitt in der Datei ("ERGEBNIS: H0 -- #37 GESCHLOSSEN") -->

# Vorregistrierung: Task #37 -- Tiling-Auswahlkriterium (punkte*P vs reines P)

**Angelegt 2026-08-08, VOR dem Messlauf.** Knopf: MOSAIC_TILING_SELECT
(0 = Bestand punkte*P(Sieg), byte-identisch, Paritaets-Hash belegt;
1 = reines P(Sieg)-Ranking; Wirksamkeit auf identischen Seeds belegt).
Hinweis Auftragskorrektur: das BESTANDSkriterium ist bereits punkte*P
(Task-#20-Erbe); #37 fragt, ob reines P besser waere -- der
Implementierungs-Agent hat die verdrehte Auftrags-Paraphrase anhand
der History korrigiert.

## Design

Zwei-Arm-A/B (#30-Muster; der Tiling-Solver ist prozessglobal und
wirkt auf BEIDE Seiten jedes Matches -- gemessen wird der Netto-Effekt
auf die Champion-Siegquote bei symmetrischer Anwendung):
tools/paired_arena_env_ab.py, Champion@400 vs Heuristik@150dyn,
2 Arme a 400 Spiele, identische Seeds, Basis-Seed 20260814,
Arm A MOSAIC_TILING_SELECT=0 (Kontrolle), Arm B =1.

## Entscheidungsregeln

1. Kriterium-Wechsel (Default auf Modus 1) NUR bei signifikantem
   Siegquoten-Vorteil (McNemar p<0,05) UND Frisch-Seed-Replikation
   (Statistik-Regel 3) -- Default-Aenderungen brauchen den vollen Beleg.
2. H0 -> Bestand bestaetigt, #37 GESCHLOSSEN (der Punktefaktor bleibt).
3. Deskriptiv mitgefuehrt: Scores/Floors auf Block-Ebene (16 Bloecke).
4. Instrument-Vorbehalt dokumentiert: Netz-vs-Heuristik; ein
   Nahe-Peer-Nachtest nur, falls Modus 1 hier gewinnt (dann VOR der
   Uebernahme, Zwei-Arm symmetrisch vs v19_2d_best).

## ERGEBNIS (2026-08-08): H0 -- #37 GESCHLOSSEN

Modus 0 (Bestand punkte*P) 284/400 vs Modus 1 (reines P) 292/400,
diskordant 30:22, McNemar p=0,33. Regel 2 greift: Bestand bestaetigt,
der Punktefaktor bleibt Default; kein Nahe-Peer-Nachtest noetig
(nur bei Modus-1-Sieg vorgesehen). MOSAIC_TILING_SELECT bleibt als
inerter Knopf fuer kuenftige Regime.
