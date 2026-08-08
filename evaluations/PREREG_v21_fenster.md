# Vorregistrierung: v21-Fenster (Zwei-Klassen, Rotation)

**Angelegt 2026-08-07. Fenster-Zuschnitt = NUTZER-VORSCHLAG (woertlich
"fuer den sockel 4000 v20, 1350 v19wdl, 450 v18 / fuer den schwarm
8000 v20sw, 8000 v19wdlsw, 5000 v18 (policy maskiert)").** Zwei
Detail-Festlegungen unten sind Koordinator-Empfehlung mit offenem
Nutzer-Veto; der Rest ist fix.

## Fenster

| Klasse | Quelle | Partien | Sims | Policy | Value |
|---|---|---|---|---|---|
| Sockel NEU | `v20wdl` (Generator = `v20_2d_opp_brierbest`) | 4.000 | 600 | aktiv | aktiv |
| Sockel-Traeger alt | `v19wdl` (135 Dateien, seed-bestimmt) | 1.350 | 600 | aktiv | aktiv |
| Sockel-Traeger aelter | `v18` (45 Dateien, seed-bestimmt) | 450 | 400 | aktiv | aktiv |
| Schwarm NEU | `v20wdlsw` (`--value-only`) | 8.000 | 150 | maskiert | aktiv |
| Schwarm alt | `v19wdlsw` (komplett) | 8.000 | 150 | maskiert | aktiv |
| Alt-Value | `v18` (500 Dateien, DISJUNKT von den 45 Traeger-Dateien) | 5.000 | 400 | maskiert | aktiv |
| Alt-Value | `v19wdl`-Rest (265 Dateien) | 2.650 | 600 | maskiert | aktiv |

**Praezisierung (Nutzer 2026-08-07)**: die 450 Traeger-Partien sind
ZUSAETZLICH zu den 5.000 maskierten -- insgesamt **5.450 v18-Partien**
im Training (545 von 600 v18-Dateien; 55 Dateien bleiben draussen,
seed-bestimmte Auswahl im Manifest). Gesamtfenster damit 29.450
Partien.

Rotations-Logik: jede Generation altert eine Stufe (v19wdl uebernimmt
die 1.350er-Traegerrolle, v18 die 450er); **v16/v17 rotieren komplett
raus** (Nutzer-Zuschnitt). Value-Fenster waechst ~21.000 -> ~29.450.

Beide frueheren Detail-Empfehlungen sind durch die Nutzer-Praezisierung
ERSETZT: v19wdl-Rest (2.650) ist als maskiertes Value-Material vom
Nutzer BESTAETIGT; die 450 v18-Traeger sind SEPARATE Dateien (nicht
Teilmenge der 5.000) -- kein offenes Veto mehr, der Zuschnitt ist fix.

Umsetzung wie v20: `policy_carrier_manifest_v21.json` (Traeger-Dateien
+ Seed), Manifest-Inhalt im Cache-Key. Dateien nach dem GENERATOR
benannt (`selfplay_v20wdl_*`/`selfplay_v20wdlsw_*` -- Praefix-Match
haelt die native Bootstrap-Behandlung in Schema>=17 automatisch
korrekt). Backup-/Alt-Regel-Korpora bleiben AUSSEN (stehende Regel).

**Traeger-Mechanismus (Fix 2026-08-08)**: das Manifest setzt zusaetzlich
`carrier_prefixes: ["selfplay_v20wdl_"]` -- damit entscheidet
`_is_policy_carrier` (neural_net.py) NUR ueber `policy_carrier_files`
(die gelisteten 135 v19wdl- + 45 v18-Dateien) plus Praefix-Treffer (alle
`selfplay_v20wdl_*`-Sockeldateien); der alte `bootstrap_native`-
Kurzschluss, der frueher pauschal ALLE `v19wdl*`-Dateien zu Traegern
gemacht haette (400 statt 135), ist damit fuer v21 abgeschaltet. Ohne
`carrier_prefixes` (v20-Manifest) bleibt die Alt-Logik unveraendert.

## Generierungs-Reihenfolge (CPU-Bahn, kritischer Pfad)

1. **LAEUFT**: τ-Annealing-Batch 2.000 @600 (`v19wdlann`, Messung 3)
   -- dessen Verdikt entscheidet, ob der v21-SOCKEL mit
   `--tau-argmax-from-move 30` generiert wird.
2. v20-SCHWARM 8.000 @150 `--value-only --version v20wdlsw`
   (Generator = v20-Champion; die Partien SIND v20-Self-Plays und
   fuellen das v21-Fenster -- Namens-Konvention!)
   (τ-unabhaengig; Schwarm-Klasse bleibt durchgehend τ=1 --
   Value-Ziele sind zugwahl-robust, und die τ-Messung betrifft die
   Policy-Traeger-Qualitaet).
3. v20-SOCKEL 4.000 @600 `--version v20wdl`, τ gemaess Messung-3-Verdikt
   (Uebernahme nur bei repliziertem Arena-Vorteil, sonst τ=1).

## RAM-Voraussetzung (Nutzer-Einwand 2026-08-07) -- ERFUELLT

**Bitpacking ist umgesetzt und validiert (Commit 34b150b)**: planes/
masks 1-Bit-gepackt, 2,69 KB/Zustand gemessen, 100% bit-identisch
gegen den ungepackten Pfad (beide Encoder, end-to-end durch den
DataLoader), Batch-Unpack im Benchmark SCHNELLER als die Baseline.
v21-Hochrechnung: ~13,2 GB Cache -- passt komfortabel in 32 GB.
Der urspruengliche Wortlaut bleibt unten als Kontext stehen.

## (urspruenglicher Wortlaut)

Der Zuschnitt (~4,8 M Zustaende) wuerde im heutigen Cache-Format
~21,5 GB Cache / ~28-29 GB Trainings-Peak kosten -- zu knapp fuer
32 GB. **Voraussetzung fuer das v21-Training ist daher das
Planes-/Masken-BITPACKING** (planes sind strikt binaer: 2.736 -> 342 B,
masks 406 -> 51 B; Ziel ~2,6 KB/Zustand => ~12,5 GB Cache, Peak
~19-20 GB), verlustfrei, mit eigenem Cache-Key und
bit-identischer Validierung gegen den ungepackten Pfad
(Escape: MOSAIC_CACHE_NOPACK=1). Faellt das Bitpacking durch die
Validierung, wird stattdessen das Fenster beschnitten (zuerst der
5.000er-v18-Block) -- Nutzer-Entscheid dann neu.

## Gating-Verlaengerungsregel (VORAB festgelegt 2026-08-08)

Die Gating-Margen schrumpfen ueber die Generationen (v18->v19: 64%,
v19_2d->v19: 64%, v20->v19: 56,2%). Unser SPRT prueft H0=50% gegen
H1=65% -- ein real ~53%-Kandidat wird davon konstruktionsgemaess
abgelehnt (Power-Mangel, nicht Fehlen von Fortschritt). Damit das nicht
erst beim Anblick eines knappen Ergebnisses diskutiert wird, gilt
vorab:

1. Standard-Gating bis 200 Paare (Fruehstopp-Regel unveraendert:
   kein Entscheid <150 Paare ohne Frisch-Seed-Replikation).
2. Endet es **UNDECIDED_CAP_REACHED mit POSITIVER Punktschaetzung**
   (gepaarte Differenz > 0), wird auf **demselben Basis-Seed** auf
   400 Paare verlaengert -- Praezedenzfall v17-Zyklus (dort:
   UNDECIDED bei 200 Paaren/p=0,053 -> Verlaengerung -> SPRT-H1 nach
   375 Paaren, Bloecke 1-8 reproduzierten exakt). Die SPRT-Schranken
   bleiben unveraendert; die Verlaengerung erhoeht nur die Power.
3. Endet es UNDECIDED mit negativer oder Null-Punktschaetzung, oder
   erreicht es die H0-Schranke: KEINE Verlaengerung, H0 gilt
   (kein Nachschub-Ventil, keine dritte Runde).
4. Kein Absenken von H1 nach dem Sehen von Daten. Wollen wir kuenftig
   generell kleinere Gewinne aufloesen, ist das eine eigene
   Vorab-Entscheidung fuer die NAECHSTE Generation (H1=0,58 braeuchte
   grob 3,5x mehr Paare, ~600-700, also ~3-4h Arena).

## Training/Gating

Champion-Rezept (warm, lr 5e-5 cosine, wdl, brierbest-Politik,
Schema 18); Kopf-Konfiguration (mit/ohne `--endgame-head`) gemaess dem
Verdikt der Platten-Intervention VOR dem v21-Training. Gating vs
`v20_2d_opp_brierbest`, Standard-SPRT bis 200 Paare, Fruehstopp-Regel
(kein Entscheid <150 Paare ohne Frisch-Seed-Replikation). Kein
Nachschub-Ventil (stehende Nutzer-Regel). Auswertungs-Paket wie v20
(Policy-Wacht, Platt, R5, R4b, Saettigungspunkt auf dem
90-Dateien-Altmessset, Struktur-Watchlist sobald Nutzer-Partien
vorliegen). Fenster-Rotations-A/B (Memory-Punkt fuer v21) gilt durch
diesen Zuschnitt als DESIGN-UMGESETZT; ein separater A/B-Arm nur auf
expliziten Nutzer-Wunsch.

---
**STATUS (Stand 2026-08-08): OFFEN** -- der Fenster-/Korpus-Zuschnitt
selbst ist fix entschieden (kein offenes Veto mehr, siehe Datei). Die
eine bereits gelaufene Teilfrage (τ-Annealing fuer den Sockel) ist
GESCHLOSSEN: Messung 3 ergab H0 (112:118, p=0,78) -> τ=1 bleibt, der
v21-Sockel wird ohne Annealing generiert. Die eigentliche Fenster-
Befuellung/Training/Gating wurde vom Nutzer am 2026-08-08 ausdruecklich
ZURUECKGESTELLT ("nicht so auf die self plays stuerzen"); 2.090 bereits
generierte Schwarm-Partien liegen in `data/`, die Generierung startet
erst nach Abarbeitung der offenen Task-Liste. Kein Trainings- oder
Gating-Ergebnis fuer v21 existiert bislang. Belegstelle:
evaluations/STATUS.md, Zeile 15 ("τ-Annealing ... GESCHLOSSEN
2026-08-08") und Zeile 16 ("v21-Fenster fuellen | ZURUECKGESTELLT ...").
