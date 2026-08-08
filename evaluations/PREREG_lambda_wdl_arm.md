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
