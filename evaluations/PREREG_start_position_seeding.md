<!-- STATUS: OFFEN | Frage: Lernt der Value-Kopf den Spaltenwert, wenn Self-Play von HALBFERTIGEN Spalten-Stellungen aus FREI weiterspielt (Startpositions-Seeding, KataGo-startPoses-Muster) -- also On-Policy-Wertdaten statt erzwungener Trajektorien? | Beleg: ENTWURF 2026-08-22, nichts gebaut. Primaerarm des Policy-Seiten-Zuschnitts (Nutzer-Freigabe der Reihenfolge 2026-08-22); Anlass: RESEARCH_plate_intent_external F1/F4 (Startzustandsverteilung ist der belegteste Strukturhebel; Off-Policy-Diagnose erklaert das Asym-Null par.14/15). Stellungsquelle: der vorhandene Asym-Korpus. -->

# PREREG-SKELETT: Startpositions-Seeding -- frei weiterspielen ab halbfertigen Spalten

Stand **2026-08-22. ENTWURF, nichts gebaut, Plan-Zeitform.** Baubeginn,
Umfaenge und Schwellen-Bestaetigung sind Nutzer-Entscheid (par.6).

## par.1 Anlass und Mechanismus

Das Asym-Curriculum scheiterte an einem jetzt benannten Strukturfehler
(par.14-16 der Asym-Prereg): erzwungene Trajektorien liefern den Wert
einer Politik, die das Netz nie spielt (Off-Policy-Value-Fehler), und
Klon-Ziele im Prior koennen sich gegen das Wert-Backup nicht
durchsetzen. Startpositions-Seeding dreht den Spiess um: die seltene
Situation (halbfertige Spalte) wird zur AUSGANGSLAGE, und ab dort
spielen BEIDE Seiten frei mit dem aktuellen Netz. Der Wert des
Weiterbauens vs. Abbrechens wird damit erstmals on-policy erhoben --
die Labels beschreiben eine Politik, die das Netz tatsaechlich spielt.
Produktions-Praezedenz laut Recherche: KataGo startPoses/hintPoses;
RGSC (+77/+89 Elo). (Agenten-Befunde mit Quellen, Report F1/F4.)

**Verifikations-Nachtrag zum Recherche-Kontext (Koordinator, am Code
geprueft 2026-08-22):** die mctx-Faktor-14-Rechnung des Reports gilt
fuer UNSERE Engine nicht -- GUMBEL_C_SCALE=1,0 statt mctx 0,1, und die
hauseigene Task-#18-Kalibrierung (net_mcts.rs:2795ff) misst
sigma(q):ln(prior) mit Verhaeltnis-Median 1,23, also praktisch
Gleichgewicht. Die Report-Option "Q-Skalierung temperieren" ist
zusaetzlich hauseigen vorbelastet: c_scale 0,3 senkte den absoluten
Score beider Seiten um ~13 % (Task-#18-Gegenprobe). Sie wird deshalb
NICHT gemessen; dieser Absatz ist ihre dokumentierte Schliessung.
**Aera-Nachmessung (2026-08-22, Nutzer-Rueckfrage):** die Kalibrierung
wurde auf v21_2d_brierbest wiederholt
(`evaluations/gumbel_scale_calibration_v21.json`, 216 Stellungen @400):
q wiegt das **1,47-Fache** des Priors (v18-Aera: 1,23), je Runde
1,30-1,46 (R4: 2,92), Gleichgewicht laege bei c_scale~0,68. Die
Schliessung ist damit auf der aktuellen Aera bestaetigt: kein
Faktor-14-Ungleichgewicht, Temperieren ist nicht der Hebel.

## par.2 Baustein 1: Stellungssatz

- Quelle: `data/asym_corpus/selfplay_v21_asymS_*.pkl` (bleibt lokal,
  Nutzer-Entscheid 2026-08-22). Kandidaten: Zustaende der ZWANGSSEITE
  (Map `zwangsseiten_map.txt`) mit Spaltenfortschritt, z. B.
  max(col_fill) in {3,4,5} und Runde in {2,3,4}; Ziehung stratifiziert
  ueber Runde und Fortschritt, dedupliziert je Partie (hoechstens eine
  Stellung je Partie), Zielumfang ~1.000-2.000 Startstellungen.
- Kuratierungs-Bericht VOR der Generierung (Verteilung Runde x
  Fortschritt x aktive Platten), analog Deckungs-Bericht des
  Ownership-Korpus.

**ERGEBNIS BAUSTEIN 1 (2026-08-22, `tools/seed_position_curation.py`;
Python-Spaltenzaehlung gegen die Engine verifiziert, 500/500
identisch):** 7.797/8.000 Zwangspartien mit Kandidat; Auswahl 1.500
Stellungen (`data/seed_positions/seed_positions_v1.jsonl`, Seed
20260822, hoechstens eine je Partie), Bericht
`evaluations/seed_positions_curation_report.json`. Verteilung: R2
duenn (90/9/0 fuer p3/p4/p5 -- vollstaendig uebernommen,
dokumentierte Schieflage), R3/R4 quotiert 183-276 je Stratum;
k1-aktiv 567/1500 (37,8 % ~ 3/8). Restlaenge ab Startpunkt: Mittel
43,6 % einer Vollpartie. **Kostenrechnung fuer par.6** (Durchsatz
0,21-0,29 Vollpartien/s): k=4 -> 6.000 Partien in 2,5-3,5 h; k=6 ->
9.000 in 3,8-5,2 h; k=8 -> 12.000 in 5,0-6,9 h.

## par.3 Baustein 2: Engine-Faehigkeit "Start ab Stellung"

Self-Play kann heute nur ab Spielbeginn starten (setup_new_game).
Noetig: ein additiver Pfad, der eine serialisierte Stellung als
Partie-Start laedt (Roundtrip existiert: Serializer + replay-exakte
Zustaende), Seeds/Manifest wie gehabt, Kennzeichnung der Records
(neues additives Feld `seeded_from`), damit Auswertungen Start- von
Normal-Partien trennen koennen. Golden-/Paritaets-Gates wie ueblich:
Default aus = byte-identisch.

## par.4 Baustein 3: Korpus + Training + Messung

- Korpus: je Startstellung k freie Partien (k=4-8, beide Seiten
  aktuelles Netz, 200 Sims, rtv aus) -> ~8.000-16.000 Partien,
  Ablage eigener Ordner (nicht-rekursiver Glob, Traeger-Frage explizit:
  policy-tragend JA, die Partien sind on-policy).
- Training: Standardrezept, Warm Start Champion, Fenster = b18-Regex +
  Seeding-Korpus (+ Asym-N als Value-Material? -> beim Start
  entscheiden, EIN Faktor bleibt die Regel).
- Messung: exakt das Asym-par.7-Muster auf den 407 Kampagnen-Seeds
  (Nullarm, Brettwechsel-Pflicht): k1-Rate auf k1-aktiven Partien
  >= 30 % Ziel / >= 22 % Signal, UND kein signifikanter Siegverlust
  gegen eine Kontrolle (Kontrollarm: gleiches Rezept ohne
  Seeding-Korpus ODER der vorhandene v21-asymN-Arm auf denselben
  Seeds -- beim Start festlegen). Mechanik-Sonde
  `asym_value_sibling_check` zusaetzlich (within-Vergleich).

## par.5 Verhaeltnis zu den Nachbar-Zuschnitten

- **UVFA (`PREREG_uvfa_plate_regime.md`)**: Kombinations-/Folgearm.
  Seeding erzeugt die Daten, UVFA macht das Regime unterscheidbar --
  kombinierbar, aber nie im selben Mess-Arm einfuehren (ein Faktor).
- **Implicit-Minimax-Knopf (`PREREG_implicit_minimax_backup.md`)**:
  paralleler SUCH-Hebel, eigene Messung.
- Das Wanduhr-/Exklusiv-Regelwerk und die Fenster-Pinning-Regeln
  gelten unveraendert.

## par.6 OFFENE NUTZER-ENTSCHEIDE

1. Umfaenge (Stellungszahl, k, Korpusgroesse) nach der Kostenrechnung
   beim Start (Durchsatz-Referenz: 0,21-0,29 Partien/s je nach Arm,
   par.12 Asym).
2. Kontrollarm-Wahl (frisches Kontroll-Training vs. vorhandener
   v21-asymN).
3. Schwellen-Bestaetigung (uebernommen aus Asym-par.7) und Startzeitpunkt.
