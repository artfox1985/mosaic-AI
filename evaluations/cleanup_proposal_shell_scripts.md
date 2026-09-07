# Loeschvorschlag: Ketten-Skripte in tools/ (Stand 2026-09-07, 10:05)

**Anlass:** Nutzer 2026-09-07: *"ich denk im baum liegen deutlich mehr kettenskripte die
keiner mehr braucht."* Schritt des Generationswechsels (`/mosaic-generation-turnover`,
"obsolete Ketten-Skripte"). **Nichts wird ohne pfadgenaue Freigabe geloescht.**

**Bestand: 31 Dateien in `tools/*.sh`.** Vorschlag: 25 loeschen, 6 behalten.

**Alle 25 Kandidaten sind in git getrackt** (geprueft 2026-09-07 mit
`git ls-files --error-unmatch`). Ihr Inhalt bleibt damit ueber die Historie
rekonstruierbar; eine Loeschung nimmt nur den Baum-Platz, kein Wissen.

**Zu den Verweisen:** fast alle Kandidaten werden aus `night_run_20260902.md` (Chronik)
oder aus Preregs genannt, im Muster "gemessen mit X". Das sind HISTORISCHE Aussagen ueber
einen vergangenen Lauf, keine lebenden Zeiger -- ein Name in der Chronik bleibt richtig,
auch wenn die Datei weg ist. Die zwei Ausnahmen sind unten einzeln behandelt.

## Behalten (6)

| Datei | Warum |
| --- | --- |
| `argmax_profile.sh` | Allgemeines Tor-2a-Instrument, kein Generationsbezug; von 7 Ketten aufgerufen |
| `night_v24_chain.sh` | **Lebender Zeiger:** `.claude/skills/mosaic-generation-turnover/SKILL.md:143` verlangt, die Kette fuer G+1 "nach dem Muster night_v24_chain.sh" zu schreiben. Behalten, bis die v25-Kette existiert; dann zeigt der Skill auf diese und die alte kann mit weg |
| `night_k5_row6_special.sh` | Laeuft gerade (K5-Arm) |
| `run_longrow_teacher_arena.sh` | Benanntes Arena-Rezept, generationsunabhaengig |
| `run_lr_init_arena.sh` | dito |
| `run_v2_teacher_arena.sh` | dito (hv2-Lehrer) |

## Loeschen (25)

### a) Einmalketten fuer abgeschlossene v24-Bloecke (12)

Alle Bloecke b01 bis b06 sind gefahren, b06 ist seit 2026-09-06 Champion; die Ergebnisse
stehen in `PREREG_v24_window.md` und der Chronik.

```
tools/night_v24_b03_chain.sh
tools/night_v24_b03_fast.sh
tools/night_v24_b03_now.sh
tools/night_v24_b03_acceptance_714.sh
tools/night_v24_b04_chain.sh
tools/night_v24_b04_acceptance_744venv.sh
tools/night_v24_b05_chain.sh
tools/night_v24_b05_acceptance_wait.sh
tools/night_v24_b06_chain.sh
tools/night_v24_after_b05_chain.sh
tools/night_v24_after_b05_chain_hold.sh
tools/night_v24_acceptance_chain.sh
```

Die drei b03-Varianten (`_chain`, `_fast`, `_now`) sind Umschreibungen desselben Laufs aus
einer Nacht mit mehreren Anlaeufen -- ein Beispiel dafuer, wie der Wildwuchs entsteht.

### b) Ketten und Halter aus abgeschlossenen Vorgaengen (6)

```
tools/night_b07_chain.sh            v23-b07-Relabel-Kette; kein b07-Korpus im Baum (data/: 0 Treffer)
tools/champion_edge_b05.sh          Elo-Kante b05, eingetragen
tools/cpu_queue_after_b02.sh        Warteschlange nach b02
tools/cpu_queue_after_b04.sh        Warteschlange nach b04
tools/claude_play_hold.sh           Halter fuer die Subagent-Partien; keinerlei Verweis im Baum
tools/promote_v24_b06.sh            Promotion erledigt (b06 ist Champion)
```

### c) Einmal-Messungen und Bau-Fenster dieser Nacht, Ergebnisse registriert (7)

```
tools/hull_form_build_window.sh     Bau-Fenster Huellenform; Knopf gebaut, Wheel installiert
tools/k3f_build_window.sh           Bau-Fenster K3-F; Knopf gebaut
tools/hull_form_arm.sh              Arm-Messung Huellenform; registriert par.8.15b
tools/depth_curve_recheck.sh        Suchtiefen-Kurve; registriert par.8b
tools/temperature_material_compare.sh  Messung 3-V; registriert
tools/night_k3_knobs_champion.sh    Knopf-Kette am v23-Champion, durch die b06-Fassung ersetzt
tools/night_k3_knobs_b06.sh         Knopf-Kette b06; alle vier Arme registriert (par.8.11a, 8.14, 8.14a)
```

## Ein Nebeneffekt, der eine Doku-Zeile nachzieht

`tools/hooks/README.md:161-163` zaehlt sechs Kopien der Python-DLL-Pfadableitung und nennt
darunter `cpu_queue_after_b02.sh` und `k3f_build_window.sh`. Nach der Loeschung sind es
vier. Die Zeile ist im selben Zug nachzuziehen -- die Loeschung VERKLEINERT die
Duplikation, sie bricht nichts.

## Freigabe

Der Nutzer gibt pfadgenau frei: entweder alle drei Gruppen, einzelne Gruppen oder einzelne
Zeilen. Ohne ausdrueckliche Freigabe passiert nichts.
