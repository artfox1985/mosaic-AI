<!-- STATUS: OFFEN | Frage: Wie wird das v24-Trainingsfenster zugeschnitten? | Beleg: ZUSCHNITT VOM NUTZER FESTGELEGT (2026-09-01), nichts erzeugt. Form wie v23 (Policy 5.800, Value 23.650, Summe 29.450), neu besetzt: Netz-Anteil von v23-b01 statt v22-b05, hv2-Anteil UNVERAENDERT weiterverwendet (par.2 -- nur 12.000 Partien sind neu zu erzeugen). Begruendung des Nutzers: hv2 baut weiter die meisten Spalten, und ab wann sich die Rotation selbst verstaerkt, ist offen (par.3). Generator STEHT (par.4, 2026-09-01): b01 -- kein Arm der Generation ist belegt besser (b02/b03 75:85, b05 85:75 bei p = 0,53). -->

# Vorregistrierung: v24-Fenster

**Angelegt 2026-09-01**, Zuschnitt vom Nutzer festgelegt, waehrend der
Relabel-Arm trainierte und die b03-Entscheidungsarena lief.

## par.1 Der Zuschnitt

**Sockel (Policy-Klasse, 5.800 Partien)**

| Posten | Quelle | Partien |
| --- | --- | --- |
| Sockel NEU | `v23-b01` Self-Play, policy-aktiv | 4.000 |
| Sockel Lehrer | `hv2`, policy-aktiv | 1.800 |

**Schwarm (Value-Klasse, 23.650 Partien)**

| Posten | Quelle | Partien |
| --- | --- | --- |
| Schwarm NEU | `v23-b01` Self-Play | 8.000 |
| Schwarm Lehrer | `hv2`, policy-maskiert | 15.650 |

**Summe 29.450** -- dieselbe Form wie v22 und v23, neu besetzt.

## par.2 Was daran NEU ist -- und wie wenig davon erzeugt werden muss

**Der hv2-Anteil ist identisch mit dem von v23:** 1.800 + 15.650 = 17.450
Partien, und genau so viele stehen im v23-Fenster (1.745 Dateien a 10 Spiele,
im Trainingslog von `v23-b05` nachgezaehlt). Im Baum liegen 2.400
hv2-Dateien, das Fenster zieht davon 1.745. **Es muss also kein einziges
Lehrerspiel neu erzeugt werden**; die Traeger-Auswahl (180 Dateien =
1.800 Partien) kann aus `data/carriers_v23_hv2.txt` uebernommen werden.

**Neu zu erzeugen sind 12.000 Partien mit `v23-b01`**: 4.000 fuer den Sockel
(mit Wurzelrauschen, wie die Sockel-Erzeugung von v23) und 8.000 fuer den
Schwarm. **Mit `--per-file 10`** (`docs/working_rules.md`, in STATUS 3.3
festgehalten).

**Kostenschaetzung aus gemessenen Zahlen** (`docs/measured_runtimes.md`,
als HERLEITUNG markiert, nicht fuer diesen Zuschnitt gemessen):

| Posten | Grundlage | Dauer |
| --- | --- | --- |
| 4.000 Sockel-Partien mit Rauschen | 8,27-8,73 s je Partie, threads 11 | rund 9,3 h |
| 8.000 Schwarm-Partien | v23 fuhr 6.000 argmax + 2.000 sampled; argmax rund 0,15-0,17 Partien/s | rund 13-14 h |
| Summe | | **rund 23 h CPU** |

Der Lehreranteil kostet nichts, weil er liegt -- das ist der praktische
Hauptvorteil dieses Zuschnitts.

## par.3 Die Begruendung des Nutzers, woertlich

*"hv2 baut noch immer am meisten spalten und es ist noch nicht geklaert ab
wann sich die rotation selbst verstaerkt"*

Beides ist am Bestand belegbar: der Lehrer erreicht im Drafting-Split 0,756
volle Spalten gegen 0,044 ohne Huelle, waehrend der beste Netzstand b01 bei
0,5150 (argmax-Self-Play) bzw. 0,6456 (Arena) liegt. Und die Selbstverstaerkung
ist tatsaechlich offen: die Nacht auf den 2026-09-01 hat gezeigt, dass die
Policy-Dosis dieses Fensters einen bereits spaltenbewussten Spieler um 66
Prozent anhebt, einen Kaltstart aber nicht einmal auf den Stand des
Vorgaengers bringt (`PREREG_capacity_sim_frontier.md` par.12/13). Den Lehrer
im Fenster zu lassen, ist damit keine Vorsichtsmassnahme aus Prinzip, sondern
die Antwort auf einen gemessenen Befund.

## par.4 VORBEHALT: wer der Generator ist, steht noch nicht fest

Der Zuschnitt nennt `v23-b01`, weil er der beste Stand ist -- unter dem
ausdruecklichen Vorbehalt eines besseren v23-Kandidaten:

| Kandidat | Stand 2026-09-01 |
| --- | --- |
| `v23-b02` (Kaltstart) | gleich stark, aber ein Drittel der Spalten -- kein Generator |
| `v23-b03` (Ueberraschungs-Gewichtung) | Orakelmetriken Gleichstand (par.5 dort), erste Arena-Richtung 37:43 zurueck; zweite laeuft |
| `v23-b05` (relabelter Sockel) | gemessen: Arena 85:75 fuer b05, p = 0,53 -- nicht belegt besser (`reanalyze_label_depth` par.A1) |

**VORBEHALT AUFGELOEST (2026-09-01): `v23-b01` bleibt Generator.** Kein Arm der
Generation ist belegt besser -- b02 und b03 liegen mit 75:85 zurueck, b05 fuehrt
mit 85:75 bei p = 0,53. Bei n=160 gepaarten Partien ist +-10 Siege die
Rauschgrenze dieses Instruments; dass alle drei Arme dort landen, ist der Beleg
dafuer und nicht drei knappe Entscheidungen. Am Zuschnitt aendert sich nichts.

## par.5 Was dieser Zuschnitt NICHT beantwortet

- **Die Dosisfrage.** Ob 1.800 Lehrer-Policy-Partien das Optimum sind, ist
  ungemessen; der Wert ist aus v23 uebernommen. Eine Dosis-Reihe ist
  registriert-aber-nicht-eingetaktet (Nutzer 2026-09-01: der Kaltstart
  interessiert weniger).
- **Die Generationen-Frage.** G-1 und G-2 kommen weiterhin aus DEMSELBEN
  hv2-Korpus (par.3 des v23-Fensters benennt das bereits als offenen Punkt);
  echte Generationsvielfalt entstuende erst, wenn ein frueherer NETZ-Stand
  einen eigenen Schwarm beisteuerte.
- **Ob das Fenster ueberhaupt der Hebel ist.** Die Phase-3-Schiene
  (Betrags-Daempfung des Value-Kopfs) laeuft unabhaengig davon weiter.
