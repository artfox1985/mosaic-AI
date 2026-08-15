<!-- STATUS: ENTSCHIEDEN | Frage: Zeigt einer der 3 (w,λ)-Blend-Arme einen signifikanten Staerkegewinn gegen die w=0-Kontrolle (v20-Aera, F1-gefixt)? | Beleg: Alle 3 Arme H0 (149/154/161/155 von je 200), w bleibt ueberall 0; `evaluations/paired_arena_env_aggr_remapping.json` -->

# Vorregistrierung: Aggressions-Neukartierung (v20-Aera)

**Angelegt 2026-08-07, VOR allen Laeufen.** Vorgezogen in der CPU-Bahn
(Nutzer: "ich starte meine spiele fruehestens nach der aggressions
neukartierung"). Regeln nach Sichtung von Zwischenergebnissen nicht
mehr aenderbar.

## Kontext

Der Aggressions-Blend (`MOSAIC_POINTS_UTILITY_W` w +
`MOSAIC_AGGR_LAMBDA` λ: Blattwert = (1-w)·P(Sieg) + w·u_pts mit
u_pts = f(own - λ·opp)) steht seit dem Engine-Audit UEBERALL auf 0
("wir wissen ja nicht was er tut"): das λ07_opp-Gating lief vor dem
F1-Fix mit einem falsch extrahierten opp-Kopf. Jetzt liegen vor:
F1-gefixte Engine (namensbasierte opp_head-Extraktion), ein Champion
MIT opp-Kopf (`v20_2d_opp_brierbest`) und ein kalibrierter
WDL-Value-Kopf (Platt-B 0,93) -- die Kartierung ist erstmals sauber
moeglich.

## Design

Instrument = `tools/paired_arena_env_ab.py` (Amendment-Muster der
Suchpfad-Messungen: je Arm ein eigener Prozess, Champion@400 vs
Heuristik@150dyn, identische Basis-Seeds ueber die Arme, exakter
zweiseitiger McNemar auf diskordante Paare; die Heuristik liest keinen
der Regler -> saubere Attribution auf die Netz-Seite).

VIER Arme a 200 Spiele (w, λ):
- **(0, 0)** Kontrolle = aktueller Stand
- **(0.1, 1.0)** symmetrische Punkte-Marge
- **(0.1, 2.0)** historische Konvention (gegnerdrueckend)
- **(0.2, 2.0)** staerkerer Blend

Basis-Seed 20260809. Kosten ~40 min.

## Entscheidungsregeln (vorab festgelegt)

1. **Rated-/Server-Preset bleibt w=0**, ausser ein Arm zeigt
   signifikanten STAERKE-Gewinn (McNemar p<0,05 gegen Kontrolle) UND
   besteht die Frisch-Seed-Replikation (Statistik-Regel 3).
2. Ein replizierter Gewinner wird NICHT direkt Preset: er braucht erst
   eine eigene Anker-Kante (Gating Champion+Konfig vs Champion w=0),
   damit bewertete Partien Elo-regelkonform bleiben
   (Betrugsschutz-Regel: rated nur gegen direkt verankerte
   KI-Konfigurationen).
3. Alle H0 -> Kartierung dokumentiert "kein Staerke-Argument fuer
   w>0"; w bleibt ueberall 0, der Punkt gilt als geschlossen bis zur
   naechsten Kopf-Generation. KEINE Style-Interpretation aus diesem
   Instrument (Aggressions-Aesthetik ist hier nicht messbar).
4. Deskriptiv mitgefuehrt (keine Entscheidungsmetrik): Punktedifferenz
   und Floor-Strafen je Arm.

## Freigabe-Hinweis

Nach Abschluss (egal welches Ergebnis) ist die Nutzer-Wartebedingung
erfuellt: bewertete Partien gegen den Champion koennen starten --
Preset gemaess Regel 1-3.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- alle 3 Arme H0 gegen die
Kontrolle (0,0: 149/200 vs Heuristik): (0.1,1.0) 154/200, p=0,59;
(0.1,2.0) 161/200, p=0,169; (0.2,2.0) 155/200, p=0,54. Kein signifikanter
Staerkegewinn -> w bleibt ueberall 0, der Punkt gilt als geschlossen bis
zur naechsten Kopf-Generation; die (0,1;2,0)-Richtung ist deskriptiv
(+6pp) fuer kuenftige Kopf-Generationen vermerkt, keine
Style-Interpretation. Belegstelle: evaluations/paired_arena_env_aggr_remapping.json
(Felder `arm_wins`, `comparisons`); Commit b5123df.
