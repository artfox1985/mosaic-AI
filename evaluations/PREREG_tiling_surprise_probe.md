<!-- STATUS: ENTSCHIEDEN | Frage: Wie gut antizipiert das Netz, was der Tiling-Loeser am Rundenende tut (Kennzahl "Tiling-Ueberraschung" je Runde), und liegt dort ein Hebel fuer eine Mini-Suche ueber das Tiling mit Netzbewertung? | Beleg: GEMESSEN 2026-10-08 (par.3b, 4.551 Paare, 3 Netze): Wertkopf-Ueberraschung im Mittel +0,009 (v34-b01) -> +0,001 (b02/b10), Betrag 0,06 (Streuung; Eingabe traegt die Rundenpunkte exakt), sinkt mit CI je Generation. Kein systematischer Spielraum fuer die Mini-Suche (par.4); Empfehlung: nicht bauen (Nutzer-Entscheid). -->

# PREREG: Tiling-Ueberraschung (Diagnose-Sonde) und Mini-Suche ueber das Tiling

Registriert 2026-10-06 23:xx. Nutzer-Anlass (Chat): *"Das einzige was dann meiner Meinung nach noch fehlt. Ist das
Wissen des Netzes was der tiling solver macht. Bzw. Die direkte synergie. [...] evtl. Eine Kennzahl die vorhersagt wie
gut das Netz weiss was der tiling solver macht."* Auf den Vorschlag der Sonde: *"Registrier das, da koennen wir uns
evtl. Eine Mini suche + netz daraus bauen."*

## par.1 Stand (geprueft 2026-10-06, `self_play.rs:2706-2735`, `docs/knobs.md`, Champion-Spec)

Der Tiling-Loeser waehlt den Tiling-Zug primaer nach exakten Punkten (`best_first_step_exact_or_valued_envelope`,
`tiling_solver.rs`). Das Netz haengt an drei Stellen daran: (a) Netz-Stichentscheid zwischen punktgleichen Tilings in
Runde 2 bis 4 (`MOSAIC_NET_TILING_TIEBREAK`, an = Bestand, `PREREG_round_transition_search_sampling.md` par.16.10/11);
(b) Value-Anteil im Tiling-Score ueber die vorhergesagte Endmarge (`envelope_tiling_value_w`, 0,0 im Champion,
`PREREG_geometric_envelope.md` par.8.6); (c) Ownership-Feldwerte (`MOSAIC_OWNERSHIP_TILING_W`, 0,0, Konsument-Arena
negativ laut Register). Umgekehrt bekommt das Netz die Tiling-Projektion der laufenden Runde als 90 Eingabemerkmale
(Indizes 794-884, Variante C, seit v30 im Rezept, `PREREG_round_transition_search_sampling.md` par.18.12). Was dem Netz
NICHT vorgerechnet wird, ist die Wirkung des Loesers in spaeteren Runden auf noch nicht gezogene Steine.

Schon gemessen und NICHT zu wiederholen: Variante B (Tiling im Suchblatt aufloesen) war negativ
(`PREREG_round_transition_search_sampling.md` par.17.9). Eine Mini-Suche nach par.4 muss benennen, was sie anders macht.

## par.2 Kennzahl "Tiling-Ueberraschung"

Je Partie und Runde r in 1..4 zwei Zustaende aus dem Record-Strom und dem Engine-Replay: `S_pre` = Zustand nach dem
LETZTEN Drafting-Zug der Runde (Record-Zustand plus angewandte Record-Aktion), VOR dem Tiling; `S_post` = Zustand nach
dem Tiling des Loesers, VOR der neuen Auslage (kein Zufall dazwischen; Engine: `round_transition.rs`, Zustand "pre
chance", vgl. `resolve_to_pre_chance_stops_before_final_end_tiling`). Beide aus Sicht desselben Spielers bewertet.

- `surprise_value(r)` = v_net(S_post) - v_net(S_pre), Gewinnwahrscheinlichkeit des Wertkopfs; berichtet Mittel,
  Standardabweichung und mittlerer Betrag je Runde, dazu dasselbe fuer den Punktekopf (`points`) und den
  Gegnerpunkte-Kopf.
- Referenz: dieselbe Differenz mit dem Suchwert `root_q` an S_pre statt v_net (sofern vorhanden) und, als Nullpunkt,
  die Differenz der EXAKTEN Rundenpunkte des Loesers (Punkte vorher/nachher), damit "Ueberraschung" vom bloss
  anderen Niveau nach dem Tiling getrennt ist.
- Lesung: ein Netz, das den Loeser antizipiert, hat einen mittleren Betrag nahe der Val-Aufloesung (Brier-CI-Breite
  rund 0,0015, par.12f der v35-Prereg) und eine kleine Streuung; ein grosser Betrag oder ein systematisches Vorzeichen
  (das Netz unterschaetzt oder ueberschaetzt das Tiling) zeigt an, wo Information fehlt. Vergleich zwischen Netzen
  (v34-b01, v35-b02, b03) auf denselben Zustaenden: sinkt die Ueberraschung von Generation zu Generation, lernt das Netz
  den Loeser; bleibt sie, ist sie ein Hebel.

**Grundmenge und Einheit:** alle Partien des b02-Val-Satzes (120 Dateien, rund 1.200 Partien, je 4 Rundenuebergaenge
= rund 4.800 Paare S_pre/S_post je Spieler) auf dem b02-Val-Satz, damit nichts aus dem Training stammt; Einheit
Gewinnwahrscheinlichkeit (Wertkopf) bzw. Punkte (Punktekoepfe). Block-Bootstrap ueber Dateien fuer CIs wie in
`checkpoint_val_eval.py`.

## par.3 Bau und Kosten (HERLEITUNG)

Werkzeug `tools/probes/tiling_surprise_probe.py`: liest die Val-Dateien, stellt S_pre/S_post ueber die Engine her
(PyO3-Einstieg fuer Zustandsaufbau, Aktion anwenden und Tiling-Aufloesung; VOR dem Bau pruefen, welche Einstiege
`mosaic_rust` dafuer exportiert, sonst eine additive Exportfunktion), bewertet beide Zustaende mit dem Netz (cuda,
Batch), schreibt Artefakt mit `laufzeit`. Kosten: rund 10.000 Netzbewertungen je Netz, Minuten; drei Netze unter einer
Viertelstunde. Kein Arm, keine Arena. Bau erst nach dem Ende der laufenden Ketten (kein Build daneben).

## par.3a Bau (2026-10-08, gebaut, ungemessen)

Werkzeug `tools/probes/tiling_surprise_probe.py`, Tests `tools/tests/test_tiling_surprise_probe.py` (18 Tests,
Attrappen fuer Auszug, Perspektive, Differenz, Datei-Bootstrap). Artefakt
`evaluations/artifacts/tiling_surprise_probe.json` (alle Netze gemeinsam, `laufzeit`, Fortschritt je Datei).
Pruefstellen am Code, in dieser Sitzung gelesen:

1. **Zustaende ohne Engine-Replay (par.5 Punkt 1).** Self-Play schreibt im Tiling JEDEN Loeser-Schritt als
   Record (`self_play.rs:6750-6775`), Record-Zustand = Zustand VOR dem Schritt (`self_play.rs:2774`,
   angewandt `:2794-2804`). Damit ist `S_pre` = erster Tiling-Record der Runde (davor steht ein
   Drafting-Record derselben Runde) und `S_post` = letzter Tiling-Record, dessen Aktion das ZWEITE
   `end_tiling` ist: das erste setzt nur den Spieler um (`game.rs:1412-1421`), erst das zweite ruft
   `execute_end_tiling` (Strafen, Rundenwechsel, Neubefuellung; `game.rs:1423-1424`, ab `:1429`). Das ist
   der "pre chance"-Zustand aus `round_transition.rs:108-118`, aber mit dem GESPIELTEN Loeser
   (`resolve_tiling_step_with_variant`). `resolve_to_pre_chance` (`round_transition.rs:137-178`) loest mit
   `best_first_step_exact` und wuerde ein anderes Tiling messen als das gespielte; der Bau nimmt deshalb den
   Record. An 10 Val-Dateien (100 Partien, 377 Partie-Runden) geprueft: Tiling-Records je Runde
   zusammenhaengend, genau zwei `end_tiling`, letzter Record `end_tiling`, Folge-Record in Runde r+1.
   Ausflugspartien (`*_x1`) beginnen spaet; ihre fruehen Runden zaehlen als `round_absent`.
   **Kein Engine-Einstieg fehlt**, kein Wheel-Neubau noetig. Gebraucht werden nur `state_features_from_json`
   und `state_planes_from_json` (`lib.rs:1997`, `lib.rs:2084`); fehlt einer im geladenen Wheel, bricht die
   Sonde mit Namen ab (`require_exports`). Ein Einstieg "Aktion anwenden" existiert NICHT
   (`#[pyfunction]`-Liste in `lib.rs`; `py.rs` traegt nur die Klasse `PyGame`), wird hier aber nicht gebraucht.
2. **Strafen.** In `S_post` sind sie noch offen. Nullpunkt darum doppelt: `*_tiling_points` (Stand S_post
   minus S_pre) und `*_settled_points` (Stand des ersten Records der Runde r+1 minus S_pre, inkl. Strafen,
   geklemmt: der Record traegt nur `score`, `serialize.rs:276`, `board.rs:329-332`).
3. **Perspektive (par.5 Punkt 2).** Encoder rechnet ego aus `current_player` (`features.rs:857-860`, Planes
   `features.rs:1866-1872`). In S_pre und S_post steht fast immer der andere Spieler am Zug (377 von 377
   Partie-Runden der Stichprobe). Festgehalten wird die Perspektive, indem `current_player` im JSON auf den
   bewerteten Spieler gesetzt wird (Vorbild Encoder-Test `features.rs:2402-2404`); `estimated_score`
   (`serialize.rs:252`, gelesen `features.rs:865`) und `chippable_tiling_rows` (beide Spieler,
   `serialize.rs:758-783`) sind perspektivneutral. Jedes Paar wird aus BEIDEN Perspektiven bewertet
   (Teilmenge `all`); `last_drafter` ist die woertliche Lesart von par.2.
4. **Was die Koepfe schaetzen (par.5 Punkt 3).** `value` = 2*P(Sieg)-1 (`export_onnx.py:30-36`,
   `neural_net.py:2380-2385`). `points` zielt auf tanh(eigener ENDSTAND/50) (`corpus_dataset.py:1659-1674`,
   `VALUE_SCALE` `neural_net.py:1357`), schaetzt die Rundenpunkte des Tilings also mit; wo der Record
   `bootstrap_value` traegt, wird aber mit `TD_LAMBDA` 0,5 eine Gewinnwahrscheinlichkeit eingemischt
   (`corpus_dataset.py:1738-1745`, `neural_net.py:1359-1365`; kein `MOSAIC_TD_LAMBDA` in den Manifesten
   v34-b01, v35-b02, v35-b10). In der Stichprobe tragen 3.620 von 4.631 Tiling-Records `bootstrap_value`.
   Die Punkte-Umrechnung 50*atanh ist darum HERLEITUNG; Rohwerte stehen daneben (`*_raw`). Ausgewiesen
   wird die OLS-Steigung der Punkte-Ueberraschung gegen die Tiling-Punkte (0 = vorweggenommen,
   1 = nicht vorweggenommen). Zusaetzlich: die EINGABE traegt die exakte Rundenprojektion schon selbst
   (`estimated_score` = optimale Tiling-Punkte plus feste Strafen, `tiling_solver.rs:611-613`); die Sonde
   berichtet `projection_gap_own` = gesetzte Rundenpunkte minus `estimated_score(S_pre)`.
5. **root_q-Referenz.** Tiling-Records tragen kein `root_q`; Referenz ist der letzte Drafting-Record der
   Runde MIT `root_q`, auf die Perspektive gedreht (1 - root_q fuer den anderen Spieler, Remis
   vernachlaessigt), mit Abstand `root_q_lag`.
6. **Netz.** `--backend torch` (Default) laedt `.pth` ueber `build_model_from_checkpoint` auf cuda, falls
   verfuegbar; `--backend onnx` nur CPU (onnxruntime 1.27.0 ohne CUDA-Provider, in dieser Sitzung
   abgefragt). Statistik: Summen je Datei, gepoolt, Datei-Block-Bootstrap wie
   `checkpoint_val_eval.py:487-503`; Netzvergleiche gepaart (gleiche Ziehungen), Referenz ist das erste
   Netz in `--models`. Standard-Kennzahlen je Runde und Sitz an S_post plus Endstand/Marge je Sitz.
   Die Spec wird nur protokolliert (rohe Netzbewertung liest keinen Suchknopf).

Rauchtest ohne Netz (`--no-net --max-files 3`, KEIN Befund): n = 240 Paar-Perspektiven (30 Partien x 4
Runden x 2), Grundmenge die ersten 3 Dateien der b02-Val-Liste, Einheit Punkte: `projection_gap_own` R1-4
Mittel 0,00 (Datei-CI -0,04 bis 0,06), d. h. die Eingabe `estimated_score` sagt die gesetzten Rundenpunkte
in dieser Stichprobe fast exakt voraus. HERLEITUNG fuer die Lesung von par.2: die Ueberraschung des Punktekopfs IN DER
LAUFENDEN RUNDE misst dann eher, ob das Netz seine eigene Eingabe benutzt, als ob es den Loeser kennt.

Aufruf (Koordinator, exklusiv):
`python -X utf8 -u tools/probes/tiling_surprise_probe.py --models alphazero_v34-b01_brierbest
alphazero_v35-b02_brierbest alphazero_v35-b10_brierbest --spec models/v34-b01_brierbest.spec.json
--val-list data/window_v35_b02_val.txt`

## par.3b ERGEBNIS DER SONDE (2026-10-08 15:56-15:58, `tools/probes/tiling_surprise_probe.py`, exklusiv, torch cuda)

**Grundmenge:** die 120 Dateien des b02-Val-Satzes (`data/window_v35_b02_val.txt`), 1.200 Partien, **4.551 Paare S_pre/S_post**
(R1 1.053, R2 1.123, R3 1.175, R4 1.200; 249 Partie-Runden fehlen, Ausflugspartien, die spaet beginnen), drei Netze auf denselben
Zustaenden, 54.612 Netzbewertungen, 95,0 s Wanduhr (0,79 s je Datei). Teilmenge `last_drafter` (Sicht des Spielers des letzten
Drafting-Records, die woertliche Lesart von par.2); Einheit Wertkopf: Gewinnwahrscheinlichkeit (P = (v + 1)/2), Punktekopf:
Punkte (50 x atanh, HERLEITUNG wegen des Bootstrap-Blends im Ziel, par.3a). CIs: Datei-Block-Bootstrap, 1.000 Ziehungen.
Artefakt `evaluations/artifacts/tiling_surprise_probe.json`.

**Nullpunkte:** gesetzte Rundenpunkte des Loesers je Paar im Mittel 10,3 (R1 2,4, R2 8,3, R3 13,4, R4 16,0); `projection_gap_own`
(gesetzte Punkte minus `estimated_score` an S_pre) **-0,02 [-0,04; +0,00]**, Betrag 0,08: die Eingabe traegt die exakten
Rundenpunkte der laufenden Runde praktisch vollstaendig (Variante C, par.1). `root_q_lag` 1,18 Records.

**Wertkopf, Ueberraschung v(S_post) - v(S_pre):**

| Runde | v34-b01 Mittel [CI] / Betrag | v35-b02 Mittel / Betrag | v35-b10 Mittel / Betrag |
| --- | --- | --- | --- |
| R1 | -0,0074 [-0,0104; -0,0048] / 0,036 | -0,0115 [-0,0141; -0,0087] / 0,035 | -0,0097 [-0,0123; -0,0071] / 0,034 |
| R2 | +0,0126 [+0,0080; +0,0173] / 0,065 | +0,0043 [-0,0001; +0,0085] / 0,062 | +0,0052 [+0,0009; +0,0094] / 0,061 |
| R3 | +0,0240 [+0,0186; +0,0294] / 0,072 | +0,0129 [+0,0072; +0,0184] / 0,073 | +0,0090 [+0,0037; +0,0141] / 0,071 |
| R4 | +0,0054 [-0,0006; +0,0113] / 0,073 | -0,0026 [-0,0079; +0,0026] / 0,070 | -0,0024 [-0,0079; +0,0027] / 0,068 |
| **R1-4** | **+0,0090 [+0,0067; +0,0113] / 0,062** (sd 0,085) | **+0,0010 [-0,0012; +0,0032] / 0,061** | **+0,0007 [-0,0016; +0,0028] / 0,059** |

Referenz `root_q`(S_pre) statt v_net: Betrag rund 0,10 bei allen drei Netzen (R1-4 0,099 / 0,098 / 0,098), Mittel -0,014 / -0,012 /
-0,019; die Suche an S_pre weicht von v_net(S_post) staerker ab als das Netz von sich selbst (1,2 Records Abstand, anderes Mass).

**Gepaart gegen v34-b01 (dieselben Paare, dieselben Bootstrap-Ziehungen), R1-4, Wertkopf:** b02 minus b01 Mittel **-0,0080
[-0,0091; -0,0068]**, Betrag -0,0013 [-0,0025; -0,0000]; b10 minus b01 Mittel **-0,0083 [-0,0093; -0,0072]**, Betrag **-0,0031
[-0,0044; -0,0017]**.

**Lesung (par.2):** (1) Das systematische Vorzeichen ist klein und bei den v35-Netzen praktisch weg: v34-b01 unterschaetzt in R2/R3
die Wirkung des Tilings um 1,3 bis 2,4 Punkte Gewinnwahrscheinlichkeit und ueberschaetzt sie in R1 um 0,7; b02 und b10 liegen ueber
R1-4 bei +0,001 und +0,0007 (CI ueber 0 hinweg), die Rundenmuster bleiben (R1 negativ, R3 positiv), aber halbiert. (2) Der mittlere
Betrag (rund 6 Punkte Gewinnwahrscheinlichkeit, sd 8,5) ist um ein Vielfaches groesser als die Val-Aufloesung, sinkt aber nur um 0,3
Punkte von b01 zu b10 (CI unter 0): das ist ueberwiegend Streuung der Bewertung an aufeinanderfolgenden Zustaenden, kein fehlendes
Wissen ueber den Loeser, denn die Eingabe traegt die Rundenpunkte exakt (`projection_gap_own` rund 0). (3) **Die Ueberraschung sinkt
von Generation zu Generation** (Mittel und Betrag, beide mit CI): das Netz lernt den Loeser, der Fenster-Effekt @400 (b02) und die
Policy-Traeger (b10) nehmen den systematischen Teil weg.

**Punktekopf** (Einheit Punkte, HERLEITUNG): Ueberraschung R1-4 Mittel +0,81 (b01) / +0,23 (b02) / +0,31 (b10), Betrag 4,47 / 4,54
/ 4,27; gepaart b10 minus b01 Betrag -0,20 [-0,29; -0,11]. Ein Betrag von rund 4,4 Punkten bei exakt bekannten Rundenpunkten
heisst: der Punktekopf nutzt die Projektion in der Eingabe nicht vollstaendig und wird bei der Umstellung auf die neue Runde
(Musterreihen leer, Projektion 0) neu geeicht; das ist eine Frage der Eingabenutzung, nicht des Loeserwissens (Agenten-Lesung
par.3a, hier bestaetigt).

**Antwort auf par.4 (Mini-Suche ueber Top-k Tilings mit Netzbewertung):** die Sonde zeigt **keinen systematischen Spielraum**:
der Loeser handelt in R1-4 im Mittel so, wie das Netz es erwartet (Bias der v35-Netze unter 0,01 Gewinnwahrscheinlichkeit, kleiner
als der gemessene Fenster-Effekt b02 gegen b01 von 0,008 in dieser Groesse); eine Netzwahl zwischen punktgleichen oder punktnahen
Tilings koennte nur den Streuanteil (0,06) bewegen, und der ist Bewertungsrauschen, nicht Loeserwissen. Vorschlag des Koordinators:
die Mini-Suche NICHT bauen (Nutzer-Entscheid); was bleibt, ist der Hinweis auf den Punktekopf (Eingabenutzung), ein Diagnosebefund
ohne Rezeptfolge.

## par.4 Folgeidee (Nutzer): Mini-Suche ueber das Tiling plus Netz

Erst nach par.2. Zeigt die Sonde eine grosse, systematische Ueberraschung in bestimmten Runden, ist der Hebel eine
kleine Suche am Rundenende: die Top-k Tiling-Alternativen des Loesers (heute Top-12 im Huellen-Pfad) mit dem Netz am
S_post bewerten und die Wahl nach Netzwert statt nur nach exakten Punkten treffen, NUR am echten Rundenende der
gespielten Partie (nicht im Suchblatt wie Variante B). Vorab zu klaeren, bevor registriert wird: Unterschied zu
`envelope_tiling_value_w` (dort Margen-Anteil im Score, gemessen 0), zu `MOSAIC_NET_TILING_TIEBREAK` (nur punktgleiche
Tilings) und zu Variante B; und ob die Sonde ueberhaupt Spielraum zeigt (sonst entfaellt der Bau).

## par.5 Offen

1. Exakte Zustandskonstruktion S_post ohne Zufall (Engine-Einstieg) -- Agent liest vor dem Bau.
   BEANTWORTET par.3a Punkt 1: aus dem Record-Strom, kein Einstieg noetig.
2. Perspektive bei Spielerwechsel am Rundenende (wer beginnt die naechste Runde) -- beide Zustaende aus Sicht des
   Spielers bewerten, dessen Record S_pre ist.
   BEANTWORTET par.3a Punkt 3.
3. Ob der Punktekopf die Rundenpunkte des Tilings direkt mitschaetzt (Endstand) -- dann ist seine Ueberraschung die
   schaerfere Kennzahl.
   BEANTWORTET par.3a Punkt 4: Ziel ist der Endstand, aber mit Bootstrap-Blend; Eingabe traegt die Projektion.
