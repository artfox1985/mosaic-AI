<!-- STATUS: OFFEN | Frage: Wie wird das v22-Trainingsfenster zugeschnitten (Zwei-Klassen-Rotation, 29.450 Partien, stationaere Rotationsregel ab v22)? | Beleg: OFFEN, angelegt 2026-08-08 als reines Design-Dokument auf Halde (Nutzer-Entscheid 2026-08-08 im Kasten am Dateianfang: kein v22-Self-Play vor Abarbeitung der v21-Task-Queue); Zuschnitt fixiert, damit er nicht neu diskutiert werden muss. Bisher bewusst nicht im Index gefuehrt, seit der Generator-Umstellung mit aufgenommen. -->

# Vorregistrierung: v22-Fenster (Nutzer-Zuschnitt 2026-08-08)

**Angelegt VOR der v22-Generierung.** Zuschnitt vom Nutzer festgelegt;
der juengste Value-Posten ist eine bewusste Nutzer-Entscheidung (siehe
"Begruendung" unten).

> **NICHT EINGEPLANT (Nutzer-Entscheid 2026-08-08): "v22 laesst du mal
> weg. keine self plays in die richtung. als erstes v21 tasks
> abarbeiten."** Dieses Dokument ist damit ein reines DESIGN-Dokument
> auf Halde -- es wird NICHT ausgefuehrt, solange die v21-Task-Queue
> (B, A, E3b, ISMCTS-k, D) nicht abgearbeitet ist. Kein
> v22-Self-Play, keine Generierung, keine Vorbereitung. Der Zuschnitt
> ist festgehalten, damit er nicht neu diskutiert werden muss, wenn der
> Zeitpunkt kommt.

## Fenster (29.450 Partien, 2.945 Dateien -- identische Form wie v21)

| Klasse | Quelle | Partien | Dateien | Sims | Policy |
|---|---|---|---|---|---|
| Sockel NEU | `v21wdl` (Generator = v21-Champion) | 4.000 | 400 | 600 | aktiv |
| Sockel-Traeger Gen-1 | `v20wdl` (Manifest) | 1.350 | 135 | 600 | aktiv |
| Sockel-Traeger Gen-2 | `v19wdl` (Manifest) | 450 | 45 | 600 | aktiv |
| Schwarm NEU | `v21wdlsw` (`--value-only`) | 8.000 | 800 | 150 | maskiert |
| Schwarm Gen-1 | `v20wdlsw` (komplett) | 8.000 | 800 | 150 | maskiert |
| Sockel-Rest Gen-1 | `v20wdl` (Nicht-Traeger) | 2.650 | 265 | 600 | maskiert |
| **Sockel-Rest Gen-2** | `v19wdl` (Nicht-Traeger, VOLLSTAENDIG) | **3.550** | 355 | 600 | maskiert |
| **Schwarm-Rest Gen-2** | `v19wdlsw` (Auffuellung) | **1.450** | 145 | 150 | maskiert |

Policy-Klasse 5.800 | Value-Klasse 23.650 | Summe 29.450.
Vollstaendig ROTIERT AUS: `v18` (und alles Aeltere), sowie 6.550 der
8.000 `v19wdlsw`-Partien.

## Begruendung des juengsten Postens (Nutzer-Entscheid)

Der 5.000er-Posten der aeltesten Stufe wird NICHT aus dem
Gen-2-Schwarm gefuellt, sondern zuerst aus dem Gen-2-SOCKEL-Rest
(3.550 Partien @600, vollstaendig) und nur zum Auffuellen aus dem
Gen-2-Schwarm (1.450 @150). Wirkung auf den Schwarm-Anteil der
Value-Klasse:

| Variante | Schwarm-Anteil der Value-Klasse |
|---|---|
| v21 (Ist) | 16.000 / 23.650 = 68% |
| v22 mit 5.000 Gen-2-Schwarm | 21.000 / 23.650 = 89% |
| **v22 wie gewaehlt** | **17.450 / 23.650 = 74%** |

Damit bleibt der Anteil naeherungsweise stabil statt Richtung 90% zu
laufen. Die Value-ZIELE sind sim-robust (Bootstrap = Forward-Pass am
Rundenuebergang, plus Ausgang) -- der Grund fuer die Wahl ist die
ZUSTANDSVERTEILUNG: ein ueberwiegend aus 150-Sim-Partien bestehendes
Fenster kalibriert den Value-Kopf auf schwaechere Trajektorien, waehrend
der Champion mit 400-600 Sims spielt. Volumen bleibt bei 29.450
(Dosis-Befund: Volumen half 6/6).

## Rotationsregel ab v22 (stationaer, gilt fuer alle Folgegenerationen)

Ab v22 ist die Fensterform selbstaehnlich -- v21 war die letzte
Uebergangsgeneration (v18 war noch kein Zwei-Klassen-Korpus und lieferte
seine 5.000 daher komplett aus Voll-Such-Partien):

- Policy: 4.000 neuer Sockel + 1.350 Gen-1-Sockel (135 Dateien,
  seed-bestimmt) + 450 Gen-2-Sockel (45 Dateien).
- Value: 8.000 neuer Schwarm + 8.000 Gen-1-Schwarm + Gen-1-Sockel-Rest
  (2.650) + Gen-2-Sockel-Rest (3.550) + Gen-2-Schwarm-Auffuellung auf
  23.650 (1.450).
- Gen-3 und aelter rotieren vollstaendig aus; Backup-Bestaende kehren
  nie zurueck.

## Umsetzung

`data/policy_carrier_manifest_v22.json` mit
`carrier_prefixes: ["selfplay_v21wdl_"]` (Unterstrich-Grenze!) plus der
seed-bestimmten Traeger-Liste (135 `v20wdl`- + 45 `v19wdl`-Dateien),
Traeger-Seed hiermit auf **20260901** festgelegt. Fenster-Pin per
`MOSAIC_DATA_EXCLUDE` gegen alles, was NICHT im Fenster ist (v18,
`v19wdlann`, die 6.550 nicht genutzten `v19wdlsw`-Partien, sowie alle
waehrend der Generierung noch wachsenden Tags) -- Regex bei jedem
Trainings-Start NEU aus dem Ist-Bestand ableiten (stehende Regel).

## Vorbehalt: was passiert, wenn das v21-Gating H0 ergibt?

Dann gibt es KEINEN v21-Champion, und der Generator bleibt
`v20_2d_opp_brierbest`. Die Namenskonvention (Dateien nach dem
GENERATOR) wuerde die neuen Partien wieder `v20wdl*` nennen und mit dem
Bestand KOLLIDIEREN. Festlegung fuer diesen Fall: neuer Batch desselben
Generators erhaelt ein Unterscheidungs-Suffix (`v20wdlb` /
`v20wdlbsw`), und die Rotationsregel verschiebt sich um eine
Generation (Gen-1 = v20-Erstbatch, Gen-2 = v19). Das ist eine
Namens-, keine Design-Aenderung.
