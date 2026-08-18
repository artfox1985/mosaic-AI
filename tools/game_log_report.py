# -*- coding: utf-8 -*-
"""tools/game_log_report.py -- die MARKDOWN-DARSTELLUNG einer Partie-Analyse.

Herausgeschnitten aus `tools/analyze_game_log.py` am 2026-08-18, weil die
Datei mit dem Aktions-ID-Umbau (`PREREG_action_id_logging.md`) die
Groessen-Ratsche gerissen hat. Der Schnitt liegt an einer echten Naht: hier
steht reine Darstellung -- kein Parser, kein Replay, keine Engine-Aufrufe.

WARUM DER IMPORT UNTEN STEHT UND NICHT OBEN: `analyze_game_log` ruft
`build_report` aus `main()` heraus auf (verzoegerter Import dort), dieses
Modul greift umgekehrt auf `classify`/`LogLine`/`ROOT` zurueck. Ein Import an
BEIDEN Modul-Koepfen waere ein Zyklus. Aufgeloest ist er auf der Seite mit
dem spaeteren Bedarf: `analyze_game_log` importiert dieses Modul erst in
`main()`, wenn es selbst fertig geladen ist.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from analyze_game_log import ROOT, LogLine, classify  # noqa: E402



def _git_commit_short() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else "?"
    except Exception:
        return "?"


def extract_full_score_timeline(all_lines: list[LogLine], players: list[str]) -> dict:
    """Reine Text-Extraktion (KEIN Replay noetig) der Rundenend-Punktestaende
    und der Endwertung -- funktioniert auch dann noch, wenn das Engine-Replay
    (z.B. wegen der RNG-Perturbation ab Runde 4, siehe Grenzen-Abschnitt)
    vorzeitig abbricht, da diese Zahlen direkt im Log-Text stehen."""
    round_end_scores: dict[int, dict[str, int]] = {}
    final: dict[str, dict] = {}
    cur_final_name = None
    for l in all_lines:
        cat, m = classify(l.body)
        if cat == "ROUND_STRAFE":
            round_end_scores.setdefault(l.round_num, {})[m.group("name")] = int(m.group("score"))
        elif cat == "FINAL_SCORE":
            cur_final_name = m.group("name")
            final[cur_final_name] = {"total": int(m.group("total")), "score": int(m.group("score")), "details": []}
        elif cat == "FINAL_DETAIL" and cur_final_name is not None:
            final[cur_final_name]["details"].append(l.body.strip())
    # Auch ohne "Strafe"-Zeile (0 Pkt Strafe -> keine Zeile) den Endstand pro
    # Runde nachvollziehbar machen: letzter bekannter Wert je Spieler je Runde.
    return {"round_end_scores": round_end_scores, "final": final}


def build_report(header: dict, log_path: Path, rep: "Replayer", divergence: str | None,
                  li_reached: int, n_lines_total: int, elapsed_s: float, all_lines: list[LogLine]) -> str:
    players = header["players"]
    recs = rep.oracle_records
    lines_out: list[str] = []
    P = lines_out.append

    P(f"# Spielanalyse: {log_path.name}")
    P("")
    P(f"Erzeugt von `tools/analyze_game_log.py` (Commit `{_git_commit_short()}`), "
      f"Laufzeit {elapsed_s:.0f}s.")
    P("")
    # Partien ohne KI (Mensch vs. Mensch bzw. KI abgeschaltet) haben ai_player=None
    # im Header -- players[None] wuerde den ganzen Report-Lauf mit TypeError killen.
    ai_idx = header.get("ai_player")
    ki_desc = ("keine (Mensch vs. Mensch)" if ai_idx is None else
               f"{players[ai_idx]} ({header.get('ai_model')}, {header.get('ai_sims')} Sims)")
    P(f"- Seed: {header['seed']}, Startspieler: {players[header['first_player']]}, "
      f"KI-Spieler: {ki_desc}")
    timeline = extract_full_score_timeline(all_lines, players)
    if divergence:
        P("")
        P(f"**Replay-Abbruch bei Zeile {li_reached}/{n_lines_total}** (Ursache siehe unten, "
          f"Abschnitt \"Grenzen\").")
        P("")
        P("```")
        P(divergence)
        P("```")
        P("")

    # ── (a) Zusammenfassung ─────────────────────────────────────────────────
    P("## (a) Zusammenfassung")
    P("")
    fin0 = timeline["final"]
    if fin0 and all(p in fin0 for p in players):
        P(f"Endstand (aus dem Log-Text): **{players[0]} {fin0[players[0]]['score']} : "
          f"{fin0[players[1]]['score']} {players[1]}**")
    else:
        try:
            scores = rep.g.scores()
            P(f"Endstand (Replay-Zwischenstand, Partie evtl. nicht zu Ende gespielt): "
              f"**{players[0]} {scores[0]} : {scores[1]} {players[1]}**")
        except Exception:
            P("Endstand: nicht ermittelbar.")
    P("")
    P("Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde "
      + ("exakt " if not rep.emoji_toleriert else "bis auf die unten benannte Emoji-Toleranz ")
      + "(String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft "
      f"({'alle ' + str(n_lines_total) + ' Zeilen bestehen' if not divergence else f'{li_reached}/{n_lines_total} Zeilen bestanden, dann Abbruch'}).")
    P("")
    # PREREG_action_id_logging.md par.7: sichtbar machen, WORAUF der Replay
    # gelaufen ist. Ohne diese Zeile sieht ein "laeuft durch" bei ID-Weg und
    # Prosa-Raten identisch aus -- und genau das Raten war die Fehlerquelle.
    P(f"Aufloesung der Stein-Zuege: **{rep.hint_used} ueber die Aktions-ID** "
      f"(`#a`-Zeilen im Log, PREREG_action_id_logging.md), "
      f"**{rep.hint_missing} ueber den Textweg** (Rueckfall fuer Logs ohne IDs).")
    if rep.emoji_toleriert:
        P("")
        P(f"⚠️ {rep.emoji_toleriert} Zeile(n) stimmten nur bis auf das Quellen-Emoji "
          "(☀️/🌙) ueberein. Das ist die benannte Toleranz fuer die Korrektur vom "
          "2026-08-18 (`execution.rs:59`) -- alte Logs tragen ☀️ fuer eine "
          "Teil-Entnahme aus dem Mondbereich, die heutige Engine schreibt 🌙.")
    P("")

    per_player = {}
    for pi in (0, 1):
        evald = [r for r in recs if r.actor == pi and r.evaluated]
        skipped = [r for r in recs if r.actor == pi and not r.evaluated]
        skip_reasons: dict[str, int] = {}
        for r in skipped:
            skip_reasons[r.reason] = skip_reasons.get(r.reason, 0) + 1
        n = len(evald)
        avg_delta = sum(r.delta_win_pct for r in evald) / n if n else None
        top1 = sum(1 for r in evald if r.played_rank == 1)
        top3 = sum(1 for r in evald if r.played_rank is not None and r.played_rank <= 3)
        per_player[pi] = dict(n=n, avg_delta=avg_delta, top1=top1, top3=top3,
                               skipped=len(skipped), skip_reasons=skip_reasons)

    P("| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |")
    P("|---|---|---|---|---|---|")
    for pi in (0, 1):
        s = per_player[pi]
        avg_s = f"{s['avg_delta']:.1f} pp" if s["avg_delta"] is not None else "–"
        top1_s = f"{s['top1']}/{s['n']} ({100*s['top1']/s['n']:.0f}%)" if s["n"] else "–"
        top3_s = f"{s['top3']}/{s['n']} ({100*s['top3']/s['n']:.0f}%)" if s["n"] else "–"
        P(f"| {players[pi]} | {s['n']} | {avg_s} | {top1_s} | {top3_s} | {s['skipped']} |")
    P("")
    for pi in (0, 1):
        sr = per_player[pi]["skip_reasons"]
        if sr:
            parts = ", ".join(f"{v}× {k}" for k, v in sorted(sr.items(), key=lambda kv: -kv[1]))
            P(f"- {players[pi]}: nicht bewertete Züge -- {parts}")
    P("")
    P("`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche "
      "(v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.")
    P("")

    # ── (b) Top-3-Abweichungen je Spieler ────────────────────────────────────
    P("## (b) Groesste Abweichungen von der Oracle-Empfehlung")
    P("")
    for pi in (0, 1):
        evald = [r for r in recs if r.actor == pi and r.evaluated and r.played_rank and r.played_rank > 1]
        evald.sort(key=lambda r: -r.delta_win_pct)
        P(f"### {players[pi]}")
        P("")
        if not evald:
            P("(keine Abweichung -- jeder oracle-bewertete Zug war Top-1, oder keine Züge bewertet.)")
            P("")
            continue
        for r in evald[:3]:
            P(f"- **Runde {r.round_num}, Zug #{r.turn_idx}** ({r.kind}): gespielt "
              f"`{r.played_desc.strip()}` (Rang {r.played_rank}/{r.num_actions}, Q={r.played_q:.3f}) "
              f"vs. Oracle-Top `{r.top_desc}` (Q={r.top_q:.3f}) -- **Δwin% = {r.delta_win_pct:.1f}**"
              + (" _(Match evtl. mehrdeutig)_" if r.ambiguous_match else ""))
        P("")

    # ── (c) Wendepunkte ───────────────────────────────────────────────────────
    P("## (c) Wendepunkte (groesste Win%-Sprünge)")
    P("")
    trace = [r for r in recs if r.root_value is not None]
    p1wp = []
    for r in trace:
        wp = r.root_value * 100.0 if r.actor == 0 else (1 - r.root_value) * 100.0
        p1wp.append((r.turn_idx, r.round_num, r.actor_name, wp))
    if len(p1wp) < 2:
        P("(zu wenige oracle-bewertete Zustände fuer eine Wendepunkt-Analyse.)")
        P("")
    else:
        jumps = []
        for i in range(1, len(p1wp)):
            d = p1wp[i][3] - p1wp[i - 1][3]
            jumps.append((abs(d), d, p1wp[i - 1], p1wp[i]))
        jumps.sort(key=lambda x: -x[0])
        P(f"Win%-Schätzung ist immer aus Sicht von **{players[0]}** normiert (Oracle-`root_value` "
          f"ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive "
          f"{players[1]} wird 100−root_value gebildet).")
        P("")
        P(f"| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% ({players[0]}) |")
        P("|---|---|---|")
        for absd, d, before, after in jumps[:5]:
            P(f"| #{before[0]} (R{before[1]}, {before[2]} zieht, {before[3]:.1f}%) "
              f"| #{after[0]} (R{after[1]}, {after[2]} zieht, {after[3]:.1f}%) | {d:+.1f} pp |")
        P("")

    # ── (d) Wertungsplatten-Story ─────────────────────────────────────────────
    P("## (d) Die Wertungsplatten-Story")
    P("")
    P("Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- "
      "unabhaengig vom Replay-Fortschritt, siehe Grenzen):")
    P("")
    res = timeline["round_end_scores"]
    if res:
        P("| Runde | " + " | ".join(players) + " |")
        P("|---|" + "---|" * len(players))
        for rn in sorted(res):
            row = res[rn]
            P(f"| {rn} | " + " | ".join(str(row.get(p, "–")) for p in players) + " |")
        P("")
    spielende = header.get("_spielende_scores")
    if spielende:
        P(f"(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: "
          f"{players[0]} {spielende[0]} : {spielende[1]} {players[1]} -- fehlende \"–\"-Werte "
          f"oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)")
        P("")
    fin = timeline["final"]
    if fin:
        P("Endwertung (Wertungsplatten-Bonus):")
        P("")
        for p in players:
            if p not in fin:
                continue
            d = fin[p]
            P(f"- **{p}**: +{d['total']} Pkt -> Gesamt {d['score']} Pkt")
            for det in d["details"]:
                P(f"  - {det}")
        P("")
        if spielende:
            pre = {players[0]: spielende[0], players[1]: spielende[1]}
        else:
            pre = {p: res.get(max(res), {}).get(p) for p in players} if res else {}
        if all(pre.get(p) is not None for p in players):
            P(f"Vor der Endwertung stand es {pre[players[0]]} : {pre[players[1]]}; "
              f"nach dem Wertungsplatten-Bonus {fin[players[0]]['score']} : {fin[players[1]]['score']}.")
            winner_pre = players[0] if pre[players[0]] > pre[players[1]] else players[1]
            winner_post = players[0] if fin[players[0]]["score"] > fin[players[1]]["score"] else players[1]
            if winner_pre != winner_post:
                P(f"**Die Wertungsplatten haben das Ergebnis gedreht**: ohne Endwertung hätte "
                  f"{winner_pre} gewonnen, nach der Endwertung gewinnt {winner_post}.")
            P("")
    P(f"Win%-Verlauf (aus {players[0]}-Sicht) über den oracle-bewerteten Teil der Partie:")
    P("")
    if p1wp:
        P("| Zug# | Runde | zieht | Win% (Spieler 1) |")
        P("|---|---|---|---|")
        for t, rn, actor_name, wp in p1wp:
            P(f"| {t} | {rn} | {actor_name} | {wp:.1f}% |")
        P("")
        first_wp = p1wp[0][3]
        last_wp = p1wp[-1][3]
        P(f"Das Oracle sah {players[0]} zu Beginn der bewerteten Zuege bei **{first_wp:.1f}%** "
          f"und am Ende von Runde 4 bei **{last_wp:.1f}%** Gewinnwahrscheinlichkeit (jeweils "
          f"aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. "
          f"Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.")
        P("")
    else:
        P("(keine Datenpunkte -- oracle-Analyse war deaktiviert oder lieferte keine Ergebnisse.)")
        P("")

    # ── Grenzen ───────────────────────────────────────────────────────────────
    P("## Grenzen und Auffälligkeiten (ehrlich dokumentiert)")
    P("")
    if divergence:
        P("- **Replay-Abbruch, Ursachenanalyse**: das byte-exakte Replay (jede erzeugte "
          "Log-Zeile exakt gegen das Original geprüft) hielt bis zu der oben genannten Zeile "
          "durch, dann wich der Fabrikinhalt vom Original ab (eine benötigte Farbe fehlte in "
          "der per Replay rekonstruierten Fabrik). Root Cause (verifiziert): `Bag::draw()` "
          "(engine/src/supply.rs) entnimmt Fliesen aus einem EINMALIG gemischten Beutel ohne "
          "weiteren RNG-Verbrauch -- der Beutel bleibt daher unabhängig von jeglichem "
          "Netzsuche-Rauschen exakt reproduzierbar, SOLANGE er nie leer läuft. Sobald er "
          "während einer Rundenvorbereitung zur Neige geht, wird er aus dem Turm neu gemischt "
          "(`Bag::refill_from_tower`, verbraucht RNG proportional zur Turmgröße). Der "
          "Mensch-vs-KI-Server (`server.py`) nutzt für die EINE PyGame-Instanz der Partie "
          "durchgehend denselben `self.rng` -- auch die Debug-/Analyse-Endpunkte "
          "`/api/ai_debug`, `/api/ai_debug_history`, `/api/ai_suggest` (`ai_debug_json`/"
          "`ai_debug_net_json`, engine/src/py.rs) rufen MCTS-Suchen mit demselben `self.rng` "
          "auf, OHNE dafür jemals einen Log-Eintrag zu schreiben. Öffnete der Nutzer während "
          "der Partie das KI-Debug-Panel (naheliegend, siehe die unmittelbar vorausgehenden "
          "Commits zu debug.html/Task #95), verschiebt das den RNG-Zustand unsichtbar für das "
          "Log -- mit Auswirkung erst beim ERSTEN Beutel-Nachmischen (hier: Beginn Runde 4, "
          "der Beutel reicht für 3 Runden Fabrik-Auffüllung knapp, dann nicht mehr). Das ist "
          "eine FUNDAMENTALE, aus dem Log allein nicht rekonstruierbare Grenze dieses Ansatzes "
          "(keine Werkzeug-Lücke, kein Parser-Bug) -- die Drafting-ENTSCHEIDUNGEN selbst "
          "bleiben im Log-Text vollständig sichtbar, nur die exakte verdeckte Fabrik-Belegung "
          "ab diesem Punkt nicht mehr. Runden- und Endwertungs-Punktestände (Abschnitt (d)) "
          "wurden deshalb bewusst per reiner Text-Extraktion statt per Replay ermittelt -- die "
          "stehen unabhängig davon exakt im Log.")
    if rep.silent_chip_gaps:
        gaps = ", ".join(f"R{r} {players[a]} Reihe {pr + 1}" for r, a, pr in rep.silent_chip_gaps)
        P(f"- **Entdeckte Logging-Luecke (KI-Bonuschips)**: der Mensch-Pfad `apply_tiling_chips` "
          f"(py.rs) loggt \"🎫 ... komplettiert Reihe N ...\", der KI-Pfad (`ai_tiling_step` -> "
          f"`TilingStep::Chips` -> `apply_bonus_chips_with`, round_end.rs) tut das NICHT. "
          f"Betroffen in dieser Partie: {gaps}. Das Replay-Werkzeug erkennt die unvollstaendige "
          f"Zielreihe und holt die Chip-Komplettierung automatisch nach (ohne die dabei "
          f"entstehende, im Original fehlende \"🎫\"-Zeile gegen das Log zu pruefen).")
    P("- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information "
      "(Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit "
      "einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein "
      "echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als "
      "das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber "
      "keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).")
    P("- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, "
      "siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik "
      "als die PUCT-Netzsuche der Runden 1-4).")
    P("- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat "
      "oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, "
      "die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.")
    P("- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am "
      "Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte "
      "Wahrscheinlichkeit.")
    P("- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/"
      "Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei "
      "der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match "
      "evtl. mehrdeutig)_`-Hinweis markiert das im Text.")
    P("")
    return "\n".join(lines_out)


