# Vorregistrierung: λ-Misch-Value-Target in der WDL-Aera (Hypothesen-Arm)

**Angelegt 2026-08-08, VOR dem Training.** Nutzer-Go am selben Tag
("starte den lambda arm").

## Status der Hypothese (ehrlich)

Der einzige arena-signifikante λ-Befund (λ=0,7 gewinnt 227:173 im
v18only-Regime, 66% root_q-Mix) stammt aus der **tanh-/Margen-Aera**.
Nutzer-Einwand 2026-08-08: ueber die WDL-Grenze ist das KEIN
Replikationsargument (der Mechanismus -- Beimischung in ein gestauchtes
Margen-Ziel unter MSE -- existiert so nicht mehr). Der Arm laeuft daher
als **neues Experiment mit offener Erwartung**. Verbleibende
Motivation: root_q ist jetzt skalengleich zum Ziel (beides
[0,1]-Gewinnwahrscheinlichkeit), λ mischt also zwei Groessen derselben
Art -- die Vorbedingung, die in der tanh-Aera fehlte.

## Arm (EIN Faktor)

`lam07_wdl_s2` = exaktes Champion-Rezept (warm `v19_2d_opp_best`,
Seed 2, lr 5e-5 cosine, 2d, wdl, opp-Kopf, KEIN endgame-Kopf, KEIN
ranking-loss) + `--value-target-lambda 0.7`. Fenster = v20-Fenster
gepinnt (identisch zum Champion und zu t35b_s2:
MOSAIC_DATA_EXCLUDE gegen v20wdlsw + v19wdlann) -> Cache-HIT, kein
Rebuild. Baseline = Champion (gleiches Fenster, λ=1,0).

**Zu protokollieren**: die vom Tool ausgegebene tatsaechliche
root_q-Fraktion (`apply_value_target_lambda` -> train_root_q_frac).
Erwartung ~57% (v16/v17 tragen kein root_q); der Alt-Sieg lag bei 66%,
das Alt-H0 bei 44% -- der Arm liegt also im uninformativen Zwischen-
bereich der ALTEN Kurve, was ihn als Aera-Replikation ohnehin
disqualifiziert (s.o.) und nur als WDL-Erstmessung zaehlt.

## Entscheidungskette

1. Offline deskriptiv: val_brier/Platt/Brier-Alt-Set (Snapshot),
   R5-Steigung. KEINE Entscheidung daraus (Aufloesungsgrenze 0/4).
2. Standard-Gating vs `v20_2d_opp_brierbest`, 200 Paare,
   Fruehstopp-Regel (kein Entscheid <150 Paare ohne
   Frisch-Seed-Replikation), no-promote.
3. H1 -> λ=0,7 wird Rezept-Kandidat (neben `--endgame-head`), Promotion
   nach Nutzer-Entscheid. H0 -> λ in der WDL-Aera GESCHLOSSEN
   (Alt-Befund gilt dann als aera-gebunden), Metriken in die
   #29-Buchfuehrung.

## ERSTLAUF UNGUELTIG (2026-08-08): λ war im WDL-Modus INERT

`lam07_wdl_s2` lieferte Metriken bit-nah identisch zum Champion
(Value-Brier 0,1967 vs 0,1967; Value-Loss 0,551 vs 0,551; Val-R² 0,374
vs 0,374; Early Stop ebenfalls E15). Ursache (Koordinator-verifiziert):
`apply_value_target_lambda` mischt `root_q` in `self.values` (altes
tanh-Margen-Ziel), der WDL-Kopf trainiert aber gegen `values_wdl`.
Die Mischung lief also korrekt -- **ins Leere**. Das Log ("55,8% der
Samples haben root_q") war irrefuehrend, weil es das Zielfeld nicht
nannte.

**Lehrsatz**: bei Aera-Wechseln muessen auch die STELLSCHRAUBEN auf das
neue Ziel umgezogen werden, nicht nur die Ziel-Definition selbst. Das
ist die zweite Auspraegung derselben Klasse wie der
Traeger-Kurzschluss (bootstrap_native) -- Alt-Code, der unter neuen
Semantiken still etwas anderes tut als sein Name behauptet.

**Konsequenz**: Fix (Mischung auf `values_wdl` mit Skalen-Rueckrechnung
`p_root=(root_q+1)/2`, Log nennt das Feld) beauftragt; danach
Wiederholung des Arms unter identischem Rezept/Seed. Das ungueltige
Modell `lam07_wdl_s2*` bleibt als Dokument liegen, wird NICHT gegatet
und NICHT in die Elo-Tabelle eingetragen. Die 55,8%-Messung der
root_q-Fraktion bleibt gueltig (sie beschreibt den Korpus, nicht die
Mischung).

## WIEDERHOLUNG `lam07_wdl2_s2` (2026-08-08, gueltig)

Fix committet (5976700): Log nennt jetzt das Zielfeld --
**"λ=0.7 auf Zielfeld 'values_wdl' -- 55.8% der Samples gemischt"**,
Cache-HIT auf 1890 Dateien (v20-Fenster, identisch zum Champion).
Fehlstart-Notiz: der erste Wiederholungs-Versuch lief mit dem alten
Exclude-Regex `selfplay_v20wdlsw_|...` -- der inzwischen GESTARTETE
Sockel schreibt `selfplay_v20wdl_*` und fiel NICHT darunter
(Unterstrich-Grenze), Fenster wuchs auf 1926 Dateien, Cache-Miss.
Sofort gestoppt, Regex auf `selfplay_v20wdl|selfplay_v19wdlann_`
verallgemeinert (deckt Sockel UND Schwarm), neu gestartet.
**Regel-Verscharfung: Exclude-Regex bei JEDEM Start neu aus dem
IST-Bestand ableiten -- generierende Tags aendern sich waehrend der
Kampagne (hier: Schwarm fertig, Sockel neu).**

---
**STATUS (Stand 2026-08-08): OFFEN** -- `lam07_wdl2_s2` ist gueltig
trainiert (Zielfeld `values_wdl` verifiziert; Offline: Brier-Paritaet,
Platt-B 0,9966 vs Champion 0,930), aber das entscheidende Arena-Gating
gegen `v20_2d_opp_brierbest` wurde bislang NICHT durchgefuehrt (kein
Ergebnis in archive/history.md oder in einer JSON-Datei auffindbar).
Der Nutzer hat die Frage zusaetzlich a priori auf "kein
Replikationskandidat" heruntergestuft (Aera-Grenzen-Argument, der
tanh-Aera-Befund uebertraegt sich vermutlich nicht auf den WDL-Kopf) --
das Gating bleibt aber der offene, ausstehende Schritt. Belegstelle:
evaluations/STATUS.md, Abschnitt "OFFENES GATING (v20-Aera, hat
Vorrang)" ("λ-Arm `lam07_wdl2_s2`: ... Gating steht aus") und Zeile 20
("λ ... UMGESTUFT").

## Gegner-Festlegung KORRIGIERT (2026-08-09, nach Nutzer-Rueckfrage
## "auf welches Fenster wurde der lambda arm trainiert?")

Erster Nachtrag von heute (Gegner = neuer Champion v21) war FALSCH
gedacht und ist hiermit zurueckgezogen. Manifest-Befund
(`models/manifest_train_lam07_wdl2_s2_20260808_154809.json`):

| | λ-Arm `lam07_wdl2_s2` | `v20_2d_opp` (Champion bis 2026-08-09) | `v21_2d` (neuer Champion) |
|---|---|---|---|
| Fenster | v20-Fenster, 21.000 Partien | **identisch** | v21-Fenster, 29.450 |
| Warm-Start | v19_2d_opp_best | **identisch** | v20_2d_opp_brierbest |
| Seed / VW / Koepfe | 2 / 0,2 / ohne endgame | **identisch** | 2 / 0,2 / MIT endgame |
| λ | **0,7** | 1,0 | 1,0 |

Gegen `v20_2d_opp_brierbest` ist es damit ein **EIN-FAKTOR-Vergleich**
(nur λ), gegen `v21_2d_brierbest` waeren es DREI gleichzeitig
veraenderte Faktoren (λ + Fenster +40% + Endgame-Kopf) -- daraus
liesse sich nichts ueber λ lernen.

**Gegner ist daher `v20_2d_opp_brierbest`** (no-promote; ein Gating
gegen einen Nicht-mehr-Champion ist zulaessig, weil hier eine
REZEPT-Frage entschieden wird, keine Champion-Frage).

**Entscheidungsregeln (praezisiert)**: H1 -> λ=0,7 hilft im WDL-Ziel,
λ wird Rezept-Kandidat; die Promotion-Frage braucht dann einen
EIGENEN λ-Arm auf dem v21-Fenster (dann Ein-Faktor gegen v21).
H0 -> λ ist in der WDL-Aera GESCHLOSSEN, und diesmal ist das ein
echtes Verdikt, weil der Vergleich sauber ist.
## (zurueckgezogener erster Nachtrag, 2026-08-09 -- Dokumentation)

Champion-Wechsel vor dem Gating: der Arm tritt jetzt gegen
`v21_2d_brierbest` an (Elo 1416), nicht mehr gegen
`v20_2d_opp_brierbest`. Die Prereg-Formulierung ("gegen den amtierenden
Champion") bleibt damit unveraendert gueltig, die Latte liegt aber
hoeher. Zu beachten bei der Auswertung: der λ-Arm wurde auf dem
v20-FENSTER trainiert, der neue Champion auf dem v21-Fenster (+40%
Volumen) -- ein H0 waere daher NICHT als λ-Verdikt lesbar, sondern als
Fenster-Effekt. **Konsequenz: das λ-Gating misst nur noch, ob λ den
Fenster-Rueckstand ueberkompensiert; ein saubereres λ-Verdikt braeuchte
einen Arm auf dem v21-Fenster.** Entscheidungsregel daher praezisiert:
H1 -> λ ist ein starker Rezept-Kandidat (er schlaegt trotz kleinerem
Fenster); H0 -> KEIN λ-Verdikt, sondern "unentschieden, konfundiert",
und die Frage wandert als v21-Fenster-Arm in die Task-D-Familie.

## ERGEBNIS (2026-08-09): H0 -- λ in der WDL-AERA GESCHLOSSEN

Ein-Faktor-Gating gegen `v20_2d_opp_brierbest` (identisches Fenster,
Rezept, Warm-Start, Seed -- nur λ=0,7 vs 1,0): **63:77**, SPRT-H0 nach
70 Paaren, p=0,21, gepaarte Differenz -0,20 [-0,47, +0,07]. Die
Richtung zeigt sogar leicht GEGEN λ.

Weil der Vergleich sauber ist (ein Faktor), ist das ein echtes Verdikt
und nicht bloss ein Unentschieden: **λ=0,7 hilft im WDL-Ziel nicht.**
Der Alt-Befund (λ=0,7 gewinnt 227:173 im v18only-Regime, tanh-Aera) ist
damit als AERA-GEBUNDEN bestaetigt -- genau die Nutzer-Warnung vom
2026-08-08 ("das kannst so nicht mehr vergleichen, wir haben jetzt einen
binaeren value head"). λ wird NICHT ins Rezept aufgenommen, ein
v21-Fenster-Arm entfaellt.

Bemerkenswert bleibt der Kalibrierungs-Nebenbefund: der λ-Arm hatte
**Platt-B 0,9966** (Champion 0,930), also praktisch perfekte
Kalibrierung -- ohne Staerkegewinn. Das trennt die beiden Dinge klar:
Kalibrierung ist nicht Spielstaerke. Als eigenstaendiger Hebel bleibt
das notiert (etwa fuer #31-Schwierigkeitsstufen, wo kalibrierte
Gewinnwahrscheinlichkeiten fuer die Praesentation wertvoller sind als
Staerke), NICHT als Champion-Kandidat.
