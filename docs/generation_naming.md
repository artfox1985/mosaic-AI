# Benennung der Generationen (damit der Off-by-one nicht wiederkehrt)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

**Die Regel: ein Fenster vN traegt die Partien von Champion v(N-1).** Beleg:
das v22-Fenster enthielt `v21wdl`-Partien (Generator = v21-Champion, alte
Tabelle in `PREREG_v22_window.md`).

Daraus folgt das Muster:

| | |
| --- | --- |
| Self-Play des Champions v(N-1) | fuellt **das vN-Fenster** |
| daraus trainiert | **das vN-Netz** |
| dessen Self-Play | fuellt **das v(N+1)-Fenster** |

**Der haeufige Fehler** ist, das Self-Play, das vN fuettert, "vN-Self-Play" zu
nennen. Es ist das **v(N-1)**-Self-Play. Am 2026-08-25 einmal passiert und in
zwei Preregs korrigiert.

**Sonderfall heuristischer Erzeuger:** ein Fenster kann statt von einem
Champion von einer Heuristik gefuellt werden (so beim v22-Fenster: Erzeuger
ist die Heuristik v2huelle, kein Netz). Die Zaehlung aendert sich dadurch
nicht -- benannt wird das Fenster nach dem Netz, das AUS ihm entsteht.

**Dateinamen folgen dem Erzeuger, nicht der Zielgeneration**: die Partien von
`v18_best` heissen `v18_*`. Beides zusammen ist die Stelle, an der der
Off-by-one entsteht.

**Nomenklatur der Trainingsarme** (Nutzer 2026-08-28): fortlaufend `vNN-bMM`
wie die v21-b-Serie, also `v22-b01`, `v22-b02`, ... Folgearme reihen sich
hinten ein.

## Konkrete Kette der laufenden Kampagne (Stand 2026-08-28)

Seit 2026-08-28 wird auch die konkrete Kette HIER gefuehrt (Nutzer-Entscheid);
wer eine Generation abschliesst, zieht diese Tabelle nach.

| | |
| --- | --- |
| `hv2`-Korpus (fertig, 24.000 Partien) | **das v22-Fenster** -- Erzeuger ist die Heuristik `v2huelle`, kein Champion |
| daraus trainiert (Kaltstart, Arme `v22-b01`/`v22-b02`) | **v22-Netz** |
| dessen Self-Play (12.000 Partien) | fuellt **das v23-Fenster** |
| daraus trainiert | **v23-Netz** |

Zuschnitt des v23-Fensters ist seit 2026-08-25 festgelegt
(`PREREG_v23_window.md`): 29.450 Partien, davon 12.000 aus dem v22-Self-Play
(4.000 Sockel + 8.000 Schwarm `--value-only`) und 17.450 aus hv2 (6.550
rotieren aus). Offen dort (Stand 2026-08-28): der Traeger-Manifest-GENERATOR
(Werkzeug fehlt) und die seed-bestimmte Wahl der 6.550 ausrotierenden
Partien; die Traegerfrage selbst ist auf Arm B entschieden.
