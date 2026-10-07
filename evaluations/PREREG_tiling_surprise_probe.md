<!-- STATUS: OFFEN | Frage: Wie gut antizipiert das Netz, was der Tiling-Loeser am Rundenende tut (Kennzahl "Tiling-Ueberraschung" je Runde), und liegt dort ein Hebel fuer eine Mini-Suche ueber das Tiling mit Netzbewertung? | Beleg: nichts gebaut, nichts gemessen; registriert 2026-10-06 auf Nutzer-Anweisung ("Registrier das, da koennen wir uns evtl. eine Mini suche + netz daraus bauen"). Diagnose-Sonde, kein Arm. -->

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

## par.4 Folgeidee (Nutzer): Mini-Suche ueber das Tiling plus Netz

Erst nach par.2. Zeigt die Sonde eine grosse, systematische Ueberraschung in bestimmten Runden, ist der Hebel eine
kleine Suche am Rundenende: die Top-k Tiling-Alternativen des Loesers (heute Top-12 im Huellen-Pfad) mit dem Netz am
S_post bewerten und die Wahl nach Netzwert statt nur nach exakten Punkten treffen, NUR am echten Rundenende der
gespielten Partie (nicht im Suchblatt wie Variante B). Vorab zu klaeren, bevor registriert wird: Unterschied zu
`envelope_tiling_value_w` (dort Margen-Anteil im Score, gemessen 0), zu `MOSAIC_NET_TILING_TIEBREAK` (nur punktgleiche
Tilings) und zu Variante B; und ob die Sonde ueberhaupt Spielraum zeigt (sonst entfaellt der Bau).

## par.5 Offen

1. Exakte Zustandskonstruktion S_post ohne Zufall (Engine-Einstieg) -- Agent liest vor dem Bau.
2. Perspektive bei Spielerwechsel am Rundenende (wer beginnt die naechste Runde) -- beide Zustaende aus Sicht des
   Spielers bewerten, dessen Record S_pre ist.
3. Ob der Punktekopf die Rundenpunkte des Tilings direkt mitschaetzt (Endstand) -- dann ist seine Ueberraschung die
   schaerfere Kennzahl.
