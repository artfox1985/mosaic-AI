# Vorregistrierung: v20-Kampagne (Zwei-Klassen-Self-Play, WDL-Aera)

**Angelegt 2026-08-06, VOR dem Start der Self-Plays** (Nutzer startet die
Laeufe selbst). Design vollstaendig vom Nutzer entschieden; Regeln nach
Sichtung von Zwischenergebnissen nicht mehr aenderbar.

## Design (Option C, Nutzer 2026-08-06)

**Generator: `t34_wdldestretch_brierbest`** (WDL-Kopf, Arena-Paritaet zum
Champion belegt 65:75/p=0,52) -- liefert ab sofort NATIVE
[0,1]-Bootstraps und P(Sieg)-`root_child_q` fuer #35b.

| Klasse | Tag/Quelle | Partien | Sims | Policy | Value |
|---|---|---|---|---|---|
| Sockel | `v19wdl` (neu) | 4.000 | 600 | aktiv | aktiv |
| Schwarm | `v19wdlsw` (neu) | 8.000 | 150 (`--value-only`) | maskiert | aktiv |
| Alt-Traeger | 135 v18- + 45 v17-Dateien (Manifest) | 1.800 | — | aktiv | aktiv |
| Alt-Value | restliche v18/v17/v16-Dateien | ~7.200 | — | maskiert | aktiv |
| **Summe** | | **~21.000** | | **5.800** | **~21.000** |

- Schwarm-Implementierung (Nutzer-Einwand "Epsilon ist nicht sauber",
  behoben): expliziter **`--value-only`-Modus** in self_play.py --
  intern `pcr_full_prob=0.0` ("kein Zug voll", Rust-seitig exakt
  definiert), `--sims` wird das Budget jedes Zugs, alle Policy-Ziele
  `policy_target_valid=false`. #35b filtert auf dasselbe Flag.
- Alt-Maskierung: `data/policy_carrier_manifest_v20.json` (Seed 20260806,
  zeitlich gestreute Auswahl), Cache-Bau maskiert Nicht-Traeger
  (Schema 17, Manifest-Inhalt im Cache-Key).
- **Schema 17**: `values_wdl` blendet Alt-Datei-Bootstraps
  Platt-ENTSTAUCHT (A=0,0051/B=1,9269), `v19wdl*`-Bootstraps (WDL-Generator) ROH.
  `--wdl-bootstrap-destretch` darf mit Schema-17-Caches NICHT mehr
  gesetzt werden (Doppel-Streckung).
- **Backup-Altbestaende bleiben aussen** (Nutzer: Verlaeufe tragen die
  alte Policy; Value-Kalibrierung auf aktueller Zustandsverteilung).
- Aggressions-Blend bleibt in der KAMPAGNE AUS (w=0; Neukartierung ist
  eigener Schritt NACH dem v20-Gating, mit F1-gefixter Engine).

## Training (nach Kampagnen-Ende)

Warm von `v19_2d_opp_best` (Nutzer-Entscheid 2026-08-04: opp-Kopf kommt
ueber v20 in die Linie), 2D, Champion-Rezept (lr 5e-5, cosine),
`--value-head wdl --select-by-brier` (KEIN destretch-Flag, Schema 17
regelt), doppeltes Early Stopping, `_brierbest` wird mitgesichert.
Hinweis: opp-Kopf-Warm-Start trifft WDL-Shape-Mismatch am Value-Kopf ->
Value startet frisch (bekannt, unkritisch: Peak liegt bei E2-4).

## Entscheid & Auswertung (VORAB festgelegt)

1. **Champion-Gating**: v20-Kandidat vs `v19_2d_best`, Standard-SPRT bis
   200 Paare, OHNE Blend. **Kein Fruehstopp-Entscheid unter n=150 Paaren
   ohne Frisch-Seed-Replikation** (Lehre t12-Falsch-Positiv). Bei
   Gating-Fehlschlag: Nachschub-Ventil (weitere `v20wdl`-Sockel-Partien
   generieren, Neutraining) VOR jeder Design-Revision.
2. **Policy-Wacht**: Orakel-Metriken des Kandidaten vs v19-Referenz --
   faellt prior_mass/kendall_tau messbar, ist der 4000er-Sockel zu klein
   (erste Messung der Fortschritts-Untergrenze; Erhalts-Knie liegt
   <=2.020, t36-Kurve).
3. **Saettigungs-Nachfit**: 4. Stuetzpunkt (~21k Value-Partien) in den
   Potenzgesetz-Fit -- entscheidet log-linear vs Knick.
4. **Pflicht-Diagnostiken** am Kandidaten: Platt-B, R5-Platten-Steigung
   (0,273 -> ?), R4b-Wiederholung (N=72-Protokoll), Brier auf neuem
   Val-Split (Split aendert sich mit dem Fenster -- dokumentieren).
5. **Danach, eigene Schritte**: frozen-Set-Neubau (v20-Aera) ->
   #29-Instrument; Aggressions-Neukartierung (F1-gefixt); #37
   Tiling-Kriterium; λ-Frage am echten Mischanteil.

## Kosten-Schaetzung

Sockel 4.000@600 ~10-11h; Schwarm 8.000@150 ~8-9h (Netz ~81% der Zeit,
150/600-Sims ~2,5x billiger je Partie); Cache-Neubau Schema 17 ~1h;
Training ~40min; Gating ~1-2h. Gesamt ~22h Maschine.

**NAMENS-KORREKTUR (Nutzer 2026-08-06, vor dem Cache-Bau)**: Tags sind
`v19wdl`/`v19wdlsw` -- Dateien heissen nach dem GENERATOR (v19-Aera-
Modell), nicht nach der Ziel-Generation (Konvention; zweiter
Koordinator-Fehler dieser Art, diesmal ohne Schaden gefangen:
WDL_GENERATOR_PREFIXES haette sonst die nativen Bootstraps der neuen
Dateien faelschlich entstaucht).

**ABWEICHUNGS-NOTIZ (2026-08-06, waehrend des Schwarm-Laufs erkannt)**:
Der Schwarm laeuft via `gumbel_top_m_for_budget` mit Wurzelbreite m=9
(150 Sims) statt m=16 -- diese Formel ist nie staerke-gemessen
(Suchpfad-Inventar). Bewusst NICHT abgebrochen: Policy der
Schwarm-Partien ist maskiert, das Value-Ziel (Bootstrap+Ausgang) ist
sim-/breiten-robust, und der 16-vs-8-Wash bei 400 Sims spricht gegen
grosse Effekte. Nachmessung der m-Formel steht auf der
Nach-v20-Kandidatenliste.
