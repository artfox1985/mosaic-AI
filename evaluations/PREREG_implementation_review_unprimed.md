<!-- STATUS: ENTSCHIEDEN | Frage: Findet ein UNGEPRIMTER Reviewer (ohne unsere Hypothesen und Verdachtsflaechen) Korrektheitsfehler in Suche, Netz-Integration, Self-Play oder Trainingszielen? | Beleg: JA (par.7, 2026-08-20): zwei mittlere Befunde, beide am Code bestaetigt (invertierte Alpha-Beta-Zugsortierung an MIN-Knoten, moon_order_target als No-Op), zwei niedrige, eine Sauber-Liste. Konsequenzen par.3. Nachtrag 2026-08-30: Befund 2 als Knopf gebaut (train.py --moon-loss-weight, v23 faehrt 0); Befund 1 weiter Nutzer-Entscheid. -->

# PREREG: Ungeprimter Implementierungs-Review der KI

Stand **2026-08-20**, **ENTWURF, nichts gestartet.** Durchgehend Plan-Zeitform.

**Anlass (Nutzer, woertlich sinngemaess):** ein zweiter Review-Track, "den du
weniger biast", der sich "den KI-Agenten an sich ansieht". Der Punkt ist
methodisch: jeder vom Koordinator gebriefte Reviewer erbt dessen
Verdachtsflaechen und Blindstellen. Die teuersten Fehler dieses Projekts
sassen wiederholt DORT, wo niemand hinsah (policy-maskierter Korpus fiel
durch eine Nutzer-Frage auf, nicht durch eine Messung). Ein ungeprimter
Blick ist die einzige Suchstrategie, die nicht von der Karte des
Koordinators begrenzt ist.

---

## par.1 AUFTRAG AN DEN REVIEWER (bewusst offen)

Pruefe die KI selbst — Suchalgorithmus, Netz-Integration, Self-Play-
Datenerzeugung, Trainingsziele, Bewertungspfade — auf KORREKTHEITSFEHLER,
insbesondere solche, die still die Spielstaerke schwaechen oder Lernsignale
verfaelschen (Perspektiven-/Vorzeichenfehler, Index-Versaetze, Lecks
verdeckter Information, RNG-/Determinismus-Probleme, Trainings-/Inferenz-
Diskrepanzen). Der Reviewer waehlt selbst, wo er tief geht.

## par.2 BIAS-SCHUTZ (der Kern dieser Registrierung)

1. **Kein Briefing ueber Verdachtsflaechen, Hypothesen oder juengste
   Aenderungen.** Der Prompt nennt nur: was das System ist, wo der Code
   liegt, was als Fehlerklasse interessiert (par.1-Wortlaut), und die
   Schutzregeln unten. KEINE Erwaehnung von k1, Ownership-Kampagne,
   par.14 oder einzelnen Dateien.
2. **Quarantaene der eigenen Schlussfolgerungen:** `evaluations/` und
   `archive/` sind fuer den Reviewer TABU, bis seine Befundliste als
   Entwurf steht; danach darf er sie lesen, ausschliesslich um Duplikate
   zu markieren ("bereits bekannt laut X"). `docs/engine_manual.md`
   (Spielregeln) ist von Anfang an erlaubt — Regeln sind Fakten, keine
   Schlussfolgerungen.
3. **Staerkstes verfuegbares Modell** (Opus), EIN Agent, grosszuegiges
   Zeitbudget — Tiefe schlaegt hier Redundanz, weil der Wert gerade in
   der unvorhersehbaren Schwerpunktwahl liegt.
4. **Belegpflicht wie ueberall:** `datei:zeile` je Behauptung, Mini-Repro
   wo moeglich (Lesesonden erlaubt), Schwere + Konfidenz je Befund.
   "Keine kritischen Befunde, geprueft wurden X/Y/Z" ist ein vollwertiges
   Ergebnis — der Auftrag verlangt ausdruecklich, nichts zu erfinden.
5. **Strikt read-only**, kein Wheel-Bau, kein Training, keine Arena;
   waehrenddessen laeuft nichts anderes (Exklusivitaets-Regel).

## par.3 VORAB-REGELN

> **VERWERTUNG:** Befunde des ungeprimten Reviewers sind Behauptungen
> (Regel 0). Jeder Befund mit Schwere "kritisch" oder "mittel" durchlaeuft
> denselben adversarialen Verifikations-Schritt wie im gezielten Review
> (`PREREG_implementation_review_targeted.md` par.3) — erst dann wird er
> verrechnet.
>
> **KONSEQUENZ-REGEL, vorab:** bestaetigte kritische Befunde werden je nach
> Traeger behandelt: beruehrt er eine abgeschlossene Messung, wird deren
> Prereg annotiert und die Messung eingeplant wiederholt; beruehrt er den
> Elo-Anker oder das Heuristik-Parameterpaket, gilt die stehende
> NICHT-ANFASSEN-Regel und der Befund wird nur protokolliert (Nutzer
> entscheidet); sonst: Fix mit eigenem Arena-Gating nach Bestandsregeln.

## par.4 WAS DIESER REVIEW NICHT ENTSCHEIDET

- Keine Strategie- oder Priorisierungsfragen.
- Kein Urteil ueber die Ownership-Kampagne — falls der Reviewer von allein
  dort landet, zaehlt das als unabhaengige Konvergenz und wird so vermerkt.
- Keine Stil-/Architektur-Empfehlungen (nur Korrektheit).

## par.5 ABGRENZUNG ZUM GEZIELTEN REVIEW

Beide Reviews koennen dieselben Stellen treffen — das ist erwuenscht:
unabhaengige Konvergenz auf denselben Befund ist der staerkste Beleg, den
dieses Format liefern kann. Sie laufen deshalb GETRENNT (keine geteilten
Zwischenstaende) und werden erst nach Abschluss beider zusammengefuehrt.

## par.6 KOSTEN

Ein Opus-Agent, grosszuegig bemessen (Richtwert 30-90 min Agentenzeit),
keine GPU. Der Nutzen haengt nicht am Erwartungswert eines Funds, sondern
an der Abdeckung der Flaechen, die auf keiner Verdachtskarte stehen.

## par.7 ERGEBNIS (2026-08-20)

Der volle Bericht liegt im Sitzungsprotokoll; hier die verrechneten Kerne.

**BESTAETIGT (Koordinator-Verifikation am Code, Regel 0):**

1. **Min-Knoten-Sortierung invertiert** (`round5.rs:366-387` sortiert
   absteigend nach `leaf_value(s, perspective)` mit wurzelfester Perspektive,
   dieselbe Liste an Max- UND Min-Knoten; `:463-466` bricht die Kinderschleife
   am Knotenbudget ab; Budget 200 = p75, greift regelmaessig). Folge: Min-Werte
   systematisch zu hoch, Gegner-Widerlegungen werden bevorzugt abgeschnitten;
   Cutoffs feuern spaetestmoeglich. Zweite Fundstelle
   `round_transition_deep.rs:311-329` (Budget 40). Die hauseigene korrekte
   Variante existiert (`self_play.rs:3398-3411`). Wirkungsgroesse UNGEMESSEN.
   **Konsequenz nach par.3 ("sonst"):** Fix mit eigenem Arena-Gating,
   eingetaktet NACH der Wiederholungs-Arena des Zielwechsels (die braucht den
   byte-identischen Engine-Stand fuer die N-Arm-Wiederverwendung). VOR dem
   Fix zu klaeren: ob der Heuristik-ANKER-Pfad round5 mitbenutzt — dann
   greift die NICHT-ANFASSEN-Regel und der Fix ist Nutzer-Entscheid.
2. **`moon_order_target` ist ein No-Op** (`self_play.rs:678-685` bewertet
   Permutationen mit `solve_round_final_score`, das ueber
   `tiling_key(&state.players[pi])` cached und auch uncached nur
   `players[pi]` liest — die Mondreihenfolge lebt in `state.factories`;
   alle Permutationen scoren identisch, `perms[0]` = rohe Beutelreihenfolge
   gewinnt; Agenten-Sonde 80/80). Der Moon-Kopf trainiert auf Rauschen und
   zieht dabei laut Task #38 potenziell ~1/3 des Policy-Gradienten. Die in
   STATUS #38 notierte Billig-Variante (eigener minus Gegner-Rundenendstand)
   waere aus demselben Grund ebenfalls ein No-Op. **Konsequenz:** Aktenlage
   in STATUS #38 korrigiert; ob und wie der Kopf ein echtes Ziel bekommt
   (oder Gewicht 0), ist eine Trainings-Rezept-Entscheidung -> Nutzer.

**PROTOKOLLIERT (niedrig):** (3) Stapelzug-Aufloeser vergleicht
unvergleichbare Skalen und `cost_so_far` kuerzt sich heraus — gemessen
dormant (0 DrawStackPeek in 56 Netzpartien). (4) Falsche Blockgroessen in
Feature-Kommentaren (`features.rs:193` "57" statt 52;
`neural_net.py:159` "81" statt 153) — kosmetisch, beim naechsten
Engine-Fix mitzunehmen.

**SAUBER-LISTE (Auszug, entlastet):** Feature-Paritaet Rust-Python exakt
0.0 ueber 873 Zustaende; action_to_id-Spiegel deckungsgleich;
Backprop-Perspektive korrekt; WDL-Skala Training-Inferenz exakt;
ONNX-Ausgaenge namensbasiert; Determinisierung verliert keine Information;
Floor-Shaping vorzeichenrichtig; Rundenende regelkonform.

**Duplikat-Abgleich:** Befund 1 und 4 NEU; Befund 2 korrigiert eine
falsche Aktenlage; Befund 3 betrifft Funktionen, die fuer einen ANDEREN
Fehler bereits markiert sind (PREREG_chance_nodes par.525-532).

**Methoden-Notiz:** die unabhaengige Konvergenz-Hoffnung (par.5) trat
nicht ein — der ungeprimte Review fand den Dosis-Saettigungs-Befund des
gezielten Reviews NICHT (er las den Ownership-Verbraucher als sauber,
was er implementierungsseitig auch ist), dafuer zwei Befunde, die auf
keiner Verdachtskarte standen. Genau das war der Zweck der Trennung.


### Nachtrag zu Befund 1 (2026-08-20, Anker-Klaerung)

Geprueft: `mcts.rs:746-747/777-778/796-797` — **auch der Heuristik-Pfad
kurzschliesst Runde 5 in denselben Loeser.** Der Elo-Anker spielt also mit
dem Min-Knoten-Fehler. Damit greift die par.3-Klausel "beruehrt den
Elo-Anker": der Fix ist NUTZER-ENTSCHEID. Empfohlener Zuschnitt, der den
Anker unangetastet laesst: Fix hinter einem Knopf (Default = ALTES
Verhalten, Task-#28-Muster) — der Anker bleibt byte-identisch, Netz-Arme
koennen den Fix per Env aktivieren und regulaer gaten; eine spaetere
Default-Umstellung waere ein eigener, vom Nutzer freizugebender Schritt
mit Neuverankerung der Elo-Leiter.


### Nachtrag zu Befund 2 (2026-08-30, Knopf gebaut)

Der par.7-Befund liess offen, "ob und wie der Kopf ein echtes Ziel bekommt
(oder Gewicht 0)" -- Nutzer-Entscheid: **v23-Training faehrt 0**. Damit das
ueberhaupt fahrbar ist, gibt es jetzt den Knopf; das ZIEL bleibt unangetastet
(kein neues Label, keine Engine-Aenderung).

**Gebaut (2026-08-30, reiner Trainings-Knopf, keine Messung):**
`train.py --moon-loss-weight` (float, Default **1.0 = byte-identisches
Bestandsverhalten**). Der Wert wandert ueber `LossSetup.moon_loss_weight`
(train.py:393) in `_train_one_epoch` und multipliziert dort den Summanden, der
bisher ungewichtet auf `p_loss` addiert wurde. Bei **0.0 wird der Term ganz
uebersprungen** -- samt Device-Transfer der `moon_targets` und der
5-Schritt-Plackett-Luce-Schleife (Muster `ranking_loss_weight`, train.py:470).
Der Kopf selbst bleibt im Modell und im ONNX-Export, nur sein
Gradientenbeitrag faellt weg; der HDF5-Cache-Key aendert sich NICHT (die Ziele
im Korpus bleiben unberuehrt). `_validate_one_epoch` rechnet den Moon-Term
ohnehin nie mit (train.py:743 verwirft `_v_pred_moon`) -- `val_combined`
bleibt darum ueber Arme hinweg vergleichbar.

**Validierung** nach dem Muster `--value-target-lambda`: harter `sys.exit`
bei allem, was nicht `>= 0` ist -- VOR jedem teuren Daten-Laden, kein stiller
Clamp. Die Form `not (w >= 0.0)` faengt `nan` mit ab. Nach oben offen, weil
ein Aufwerten des Terms denkbar bleibt.

**Manifest:** `cli_args` in `train.py` ist eine HAND-gepflegte Auswahl, KEIN
automatischer argparse-Abzug (geprueft: `train_manifest.py:239` legt das
uebergebene Dict unveraendert ab). `moon_loss_weight` ist dort eingetragen --
ohne diesen Eintrag haette das Manifest ueber den gefahrenen Arm geschwiegen,
die Fehlerklasse des `MOSAIC_IGNORE_POLICY_TARGET_VALID`-Vorfalls.

**Die im Auftrag vermutete NaN-Falle ist NICHT real** (gemessen 2026-08-30 an
einem Batch ohne jeden Sonnenzug): `plackett_luce_moon_loss` liefert dort
saubere Nullen -- sie maskiert mit `-1e9` statt `-inf`, eine vollstaendig
maskierte Zeile bleibt ein wohldefiniertes Gleichverteilungs-Softmax, und
`torch.where(has_rank_t, ...)` verwirft ihren Beitrag. NaN entsteht erst aus
`.mean()` einer LEEREN Auswahl (`moon_nll[sun_mask]` mit leerer Maske ergibt
gemessen `nan`) -- und davor steht seit jeher der `sun_mask.any()`-Guard. Das
Ueberspringen bei 0.0 ist damit eine Kosten-, keine Korrektheitsmassnahme.

**Smoke (kein Training gefahren):** `--help` zeigt das Flag;
`--moon-loss-weight -0.5` und `--moon-loss-weight nan` brechen beide mit
Exit 1 ab, bevor Daten geladen werden; die Term-Arithmetik gegengeprobt
(`w=1.0` liefert bitgleich den Bestandswert 2,082033157348633, `w=0.5` die
Haelfte, `w=0.0` den uebersprungenen Term).

**Was dieser Nachtrag NICHT entscheidet:** ob 0 dem v23-Netz nuetzt. Der
Knopf ist Infrastruktur; die Wirkung ist ungemessen und braucht ein eigenes
Gating. Befund 1 (Min-Knoten-Sortierung) bleibt unberuehrt -- er ist
Nutzer-Entscheid und wartet weiter.
