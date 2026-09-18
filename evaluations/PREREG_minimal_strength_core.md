<!-- STATUS: ENTSCHIEDEN | Frage: Kann ein kleinerer Standardkern aus Netz, Suche und Konfiguration mindestens gleich stark werden wie das heutige v29-Rezept, und welche Teile duerfen deshalb entfallen? | Beleg: JA: v29-b09 (moon 0, ownership 0, ohne endgame, opp_points bleibt) haelt gegen b03 (10.10: 416:384), besteht die drei Champion-Kanten (10.13) und ist seit 2026-09-18 Champion (10.18); Generator v29-b11 = b09 mit 414er-Kopf (10.17: 212:138 gegen b09). Straenge A/B/C erledigt, v30-Rezept in STATUS Abschnitt 4. Offen nur Ausfuehrung (v30-Kaltstart in PREREG_v30_window). -->

# Vorregistrierung: Minimaler Staerkekern

## par.1 Ziel und Grenze

Diese Prereg registriert eine Vereinfachungsrichtung, keine Behauptung, dass
weniger Code automatisch besser spielt. Ein Teil darf nur dann aus dem
Standardrezept oder dem produktiven Suchpfad fallen, wenn sein eigener
Verbraucher nachweislich fehlt oder eine vorab festgelegte Vergleichsmessung
keine relevante Regression zeigt. Alte Checkpoints, Artefakte und ihre
Vertraege werden durch keinen der Schritte entfernt oder umgeschrieben.

**Primaerziel:** ein schlankeres Rezept fuer eine spaetere Generation als
v29, mit mindestens derselben Spielstaerke gegen einen vor dem Lauf
festgelegten Bezugspunkt. Die Vereinfachung selbst ist ein zweites Ziel:
weniger trainierte Ausgaben, weniger Sonderpfade oder eine einzige
Konfigurationsquelle.

**Nicht Ziel dieser Prereg:** neue Koepfe, eine groessere Aktionsmenge oder
eine neue Handheuristik. Eine neue Komponente ist nur zulaessig, wenn sie
einen hier benannten bestehenden Proxy oder Sonderpfad vollstaendig ersetzt.

## par.2 Strang A: Hilfskopf-Budget

### A.1 Ausgangslage

Das aktuelle Rezept von `v29-b05` traegt `moon_loss_weight = 0`, aber
`ownership_weight = 1`, `opp_points_head = true` und `endgame_head = true`
im Trainingsmanifest. Die Suche verwendet den Ownership-Verbraucher bei
Defaultgewicht 0; Gegnerpunkte werden bei Punkte-Nutzgewicht 0 nicht als
Blatt-Utility verwendet. Das beweist NICHT, dass ihre Trainingsgradienten
nutzlos sind. Es begruendet nur eine isolierte Messung jedes Kopfes.

Der Moon-Strang wird nicht hier dupliziert: `PREREG_moon_stack_order.md`
par.12.1/12.5 hat bereits b04 mit echtem gespielten Label und b05 ohne
Moon-Loss registriert. Seine Reihenfolge kann die langfristige
Standardarchitektur entscheiden.

### A.2 Hypothesen

1. Ein Hilfskopf ohne nachweisbaren Gewinn fuer den gemeinsamen Rumpf kann
   aus neuen Standardmodellen entfallen, ohne die Arena-Staerke relevant zu
   verschlechtern.
2. Falls ein Kopf bleibt, ist sein Nutzen als **Trainingssignal** zu
   dokumentieren; ein derzeit auf 0 stehender Suchverbraucher ist kein
   Ersatzbeleg.

### A.3 Kandidaten und Reihenfolge

| Kandidat | Arm gegen denselben Bezug | Erwartung | Vereinfachung bei Uebernahme |
| --- | --- | --- | --- |
| Moon | zuerst b04 gegen b05 nach `moon_stack_order` par.12.5 | offen: echtes Label kann den Kopf rechtfertigen | bei b05-Vorteil Moon-Loss 0; ein spaeter Ausbau oder Entfernen erst nach eigener Entscheidungsregel |
| Ownership | identisches Rezept, nur `--ownership-weight 0` | ungeprueft fuer den heutigen v29-Rumpf | Ownership-Loss und spaeter der ungenutzte Output als eigener Schnitt pruefbar |
| Gegnerpunkte | identisches Rezept, nur ohne `--opp-points-head` | ungeprueft fuer den heutigen v29-Rumpf | ein ONNX-Output, Cache-Ziele und Rust-Sonderbehandlung weniger |
| Endgame | identisches Rezept, nur ohne `--endgame-head` | ungeprueft fuer den heutigen v29-Rumpf | ein ONNX-Output und R5-Hilfsziel weniger |

Die Kandidaten sind **einzeln**, nicht faktoriell, zu messen. Ein faktorieller
Sweep wuerde bei derselben Rechenzeit mehr Wechselwirkungen als Antworten
erzeugen. Ein Kopf wird nicht wegen eines alten H0-Befunds entfernt: H0 ist
kein Nichtunterlegenheitsbeleg.

### A.4 Tore und Lesart

Vor dem ersten Arm legt der Nutzer die Nichtunterlegenheitsmarge fest. Ohne
diese Zahl darf kein Kopf als "gleich stark" oder als entfernbar gelten.
Jeder Arm verwendet denselben Korpus, Warmstart, Trainingsseed, Val-Pool und
alle uebrigen Flags wie sein Bezug. Die Manifest-Differenz muss genau den
betreffenden Kopf bzw. dessen Gewicht zeigen.

* Offline-Tor: der betroffene Kopf ist wirklich aus bzw. sein Verlust ist
  null; keine Form-, Cache- oder Maskenabweichung ausser der registrierten.
* Arena-Tor: zwei Seeds, je 200 Paare, Blockgroesse 5, kein Frueh-Stopp,
  `--log-games`; Einheit Sieg auf gepaarten Arena-Partien. Die sechs
  Standard-Kennzahlen werden aus denselben Logs berichtet.
* Uebernahme: nur wenn die vorab gewaehlte Nichtunterlegenheitsregel haelt
  und kein Seed einen vorab definierten Richtungsnachteil zeigt. Andernfalls
  bleibt der Kopf oder sein Ausfall wird wiederholt.

Ein positiver Ausfall-Arm ist noch KEINE Berechtigung, den Code sofort zu
loeschen. Erst nach der Rezeptentscheidung folgt ein separater,
bestandserhaltender Aufraeum-Schnitt unter `PREREG_code_cleanup_closeout.md`.

## par.3 Strang B: Ausgefuehrte und bewertete Stapelaktion angleichen

### B.1 Ausgangslage

Die Architekturreferenz beschreibt fuer `DrawStackPeek` einen Unterschied:
Die Suche bewertet einen Peek; anschliessend waehlt eine handgeschriebene
Fortsetzung Platte, Slot und Rotation. Korpus- und Netz-Self-Play verwenden
zudem nicht denselben `apply_via_chosen_action`-Pfad. Das ist eine
Codeaussage, kein gemessener Staerkeverlust.

### B.2 Hypothese

Ein gemeinsamer Ausfuehrungs- und Protokollpfad verringert Label-/Replay-
Mehrdeutigkeit. Falls der gemessene Unterschied zwischen bewerteter und
ausgefuehrter Folgehandlung relevant ist, kann die Suchqualitaet steigen,
ohne einen Kopf oder den Aktionsraum zu erweitern.

### B.3 Reihenfolge und Tore

1. **Trace vor Bau:** Fuer jede `DrawStackPeek`-Entscheidung wird die
   bewertete Folgehandlung und die tatsaechlich ausgefuehrte
   Platte-Slot-Rotationsfolge protokolliert. Zu berichten sind n,
   Grundmenge und Einheit getrennt fuer Arena, Netz-Self-Play und Korpus.
2. **Stopp:** Sind Suchbewertung, Ausfuehrung und gespeicherte Aktion bereits
   derselben Folgehandlung zuordenbar, endet der Strang ohne Umbau.
3. **Bau nur bei Abweichung:** Bestehende Zustandsuebergaenge werden von
   Suche, Self-Play und Replay gemeinsam benutzt; kein neuer Policy-Kopf und
   keine Kreuzprodukt-Action-ID. Der Umbau braucht Golden-Replay, Netz-
   Paritaet, Anker-Drift und Konservierung.
4. **Messung:** Erst nach gruener Korrektheitsabnahme ein Arena-A/B mit zwei
   Seeds und je 200 Paaren. Ein symmetrischer Korrektheitsfehler wird nicht
   mit Elo legitimiert oder verworfen.

## par.4 Strang C: Rundenuebergang ersetzt nur einen Proxy

`PREREG_round_transition_search_sampling.md` registriert bereits Tiling im
Blatt plus hoechstens eine Neubefuellung. Dieser Strang eroeffnet keine
zweite Implementierung. Er setzt nur eine zusaetzliche Annahmeregel:

* Wenn Variante B ihren Kosten- und Arena-Test besteht, muss vor ihrer
  Aufnahme ins Rezept genau benannt werden, welchen bestehenden
  Rundenuebergangs-Proxy sie ersetzt oder deutlich vereinfacht.
* Bleibt sie neben allen bisherigen Huelle-/Shaping-Mechanismen bestehen,
  ist sie ein Komplexitaetszuwachs und wird hier nicht als
  Vereinfachungserfolg gewertet.
* Der Ersatz erfolgt erst nach einem getrennten Abstell-A/B des Proxys. Die
  neue Variante und der entfernte Proxy werden niemals im selben Arm
  untrennbar veraendert.

Die Regel vermeidet, dass eine bessere, aber nur schwer erklaerbare Suche
mehrere Mechanismen aufeinander stapelt.

## par.5 Strang D: Eine typsichere Laufkonfiguration

Die Architekturreferenz nennt mehrere Bool-Dialekte und stille Env-Fallbacks.
Das ist primaer ein Risiko fuer Mess- und Reproduzierbarkeit, nicht ein
direkter Elo-Hebel. Vorgeschlagen ist daher kein v30-Experiment, sondern ein
Spaetabschluss nach der letzten Generation unter
`PREREG_code_cleanup_closeout.md`:

1. Ein Parser fuer Bool-, Zahl- und Enum-Werte, unbekannte Werte brechen den
   Lauf vor seinem ersten Spiel ab.
2. Eine normalisierte `SearchConfig` und `TrainingConfig` je Prozess; Specs
   sind die Quelle, Env-Variablen nur explizite, im Manifest sichtbare
   Overrides.
3. Dieselbe normalisierte Konfiguration wird in Training, Self-Play,
   Arena-Artefakt und ONNX-Metadaten abgelegt.

**Tor:** Bestehende Specs und eingefrorene Artefakte laden ohne implizite
Wertveraenderung; fuer Defaultkonfigurationen halten Netz-Paritaet sowie
Anker-Drift/Konservierung. Eine abweichende Normalform ist ein Stopp, kein
stiller Fallback.

## par.6 Abhaengigkeiten und Nutzerentscheidungen

1. b04/b05 aus `PREREG_moon_stack_order.md` zuerst vollstaendig entscheiden.
   Die unmittelbare Zugriffsrate auf einen Mondstein misst nicht seinen
   strategischen Wert fuer die spaetere Fliesenverfuegbarkeit; sie ist daher
   kein Ausmusterungsgrund fuer den Moon-Mechanismus.
2. Vor Strang A: Nutzer entscheidet die Nichtunterlegenheitsmarge sowie den
   Bezugspunkt. Keine implizite Ableitung aus H0.
3. Strang B ist ein Korrektheitsaudit und darf nach Maschinenlage als
   Dokumentations-/Trace-Bau vorbereitet, aber nicht neben einer Messung
   gebaut werden.
4. Strang C bleibt ausschliesslich in seiner bestehenden Prereg.
5. Strang D ist Abschlussarbeit nach der letzten Generation; es ist kein
   Grund, eine laufende Rezeptmessung zu unterbrechen.

## par.7 Registrierung

Kein Lauf, kein Code und kein Champion-Wechsel sind durch diese Prereg
freigegeben. Ergebnisse werden in den jeweiligen Quell-Preregs registriert
und hier nur als knappe Entscheidung nachgetragen. Nach jeder Aenderung des
Statuskopfs laeuft `python tools/generate_prereg_index.py`.

## par.8 REVIEW (2026-09-16, Subagent)

Fachliches Review der ganzen Datei. Kein Bau, keine Messung; alle Code- und
Manifest-Stellen in dieser Sitzung nachgesehen.

**B1. Die Frage traegt, ist aber heute nicht ausfuehrbar, und die Aufloesung
deckelt, was ueberhaupt waehlbar ist.** par.1 stellt eine
Nichtunterlegenheits-Frage, ueberlaesst aber Marge UND Bezugspunkt dem Nutzer
(A.4, par.6 Punkt 2), waehrend die Kampagne bei identischer Konfiguration 5,75
Prozentpunkte Streuung bei n = 400 misst (CLAUDE.md, "Infrastruktur
bewerten"); bei zwei Seeds a 200 Paaren, also 800 Partien je Kandidat, ist
eine Marge unter rund 5 Prozentpunkten nicht belegbar. Vorschlag: in A.4 die
UNTERE Grenze der zulaessigen Margen benennen, damit der Nutzer keine Zahl
waehlen kann, die das Instrument nicht traegt.

**B2. A.1 ist am Manifest geprueft und stimmt.**
`models/manifest_train_v29-b05_20260915_093924.json`, `cli_args`:
`moon_loss_weight 0.0`, `ownership_weight 1.0`, `opp_points_head true`,
`endgame_head true`; die drei Flags gibt es (`train.py:2961`, `:3061`,
`:3072`). Auch die Gegnerpunkte-Aussage traegt: `opp_points` geht nur ueber
`blended_leaf_win_prob` in die Blatt-Utility (`net_mcts.rs:2539-2541`,
`:2582-2587`), und `points_utility_w()` hat Default 0,0 (`net_mcts.rs:169`,
Doku `:611-612`: Early-Out, byte-identisches Bestandsverhalten).

**B3. "Der Ownership-Verbraucher" ist Singular, es sind ZWEI.** Blatt-Regler
`ownership_weight()` / `MOSAIC_OWNERSHIP_W`, Default 0 (Test
`net_mcts.rs:13313-13315`), und Tiling-Routing `ownership_tiling_weight()` /
`MOSAIC_OWNERSHIP_TILING_W`, Default 0 (`tiling_solver.rs:1067-1076`);
`docs/architecture_reference.md:200-203` warnt ausdruecklich, dass das
Routing-Gewicht nicht das Trainings-Loss-Gewicht ist. Vorschlag: beide in A.3
benennen, weil der Ausfall-Arm beide Verbraucher auf Dauer schliesst.

**B4. Der Endgame-Kandidat hat einen Vorbefund, der die Lesart praegt, und er
fehlt.** `docs/architecture_reference.md:204-208`: das endgame-Ziel ist
`root_q` in der R5-Drafting-Zone (`corpus_dataset.py:1000-1012`), und `root_q`
schreibt nur der `NetSelfPlayAgent` (`self_play.rs:1324`) - ein
Heuristik-Korpus traegt es strukturell nicht, die Maske ist dort komplett 0.
Vorschlag: den Anteil maskierter Samples im v29-Fenster als billige Vorstufe
VOR dem Trainingsarm messen (Minuten, kein Bau); das ist dieselbe Bauform,
mit der par.12.0/12.1 von `moon_stack_order` den moon-Kopf erledigt hat.

**B5. Die Moon-Zeile in A.3 zitiert falsch und ist ueberholt.** Registriert ist
in `PREREG_moon_stack_order.md` 12.1 der Bezugspunkt **b03** fuer BEIDE Arme
("Bezugspunkt beide Male b03"); "b04 gegen b05" ist dort nur einer von vier
Ausgaengen. Inzwischen ist par.12.5 registriert (b05 gegen b03: 427:373 aus
800 Partien, z = 1,98), 12.0 nennt das Trainingsziel einen No-Op und 12.3b den
Hebel haeufig, aber flach (51,8 Prozent der Entscheide, Median EIN Stein).
Zusatz-Falle: jene Datei traegt "par.12.5" ZWEIMAL (Ergebnisabsatz und
Reihenfolge-Abschnitt), ein blosser Verweis auf 12.5 ist nicht eindeutig.
Vorschlag: Zeile auf "b05 gegen b03, entschieden" umschreiben und den Verweis
in Arm-Definition (12.1) und Ergebnis (12.5) trennen.

**B6. A.4 deckt nicht alle Ausgaenge ab.** Vorregistriert sind
"Nichtunterlegenheit haelt -> Uebernahme" und "sonst bleibt der Kopf"; der
Ausgang "der Kopf-Ausfall ist SIGNIFIKANT BESSER" hat keine Lesart, obwohl er
in dieser Kampagne gerade eingetreten ist (moon b05, 427:373). Vorschlag:
dritte Lesart eintragen - ein solcher Ausfall ist kein Vereinfachungs-, sondern
ein Staerkebefund, bekommt eine eigene bXX-Identitaet
(`feedback_measured_identity_gets_own_bxx`) und eine Elo-Kante statt nur einer
Rezeptzeile.

**B7. Die Kosten stehen nirgends, obwohl sie gemessen vorliegen.** Je Kandidat:
Training 1,43 h (`docs/measured_runtimes.md`, "Training v28-b01", 5.156,6 s)
plus zwei Seeds a 200 Paaren mit Logs zu 86-91 min (ebenda, 5.182-5.446 s),
zusammen rund 4,5 h; die drei Kopf-Kandidaten sind damit rund 13-14 h
Maschinenzeit, ohne Moon-Strang und ohne Strang B. Vorschlag: diese Zeile in
par.6 aufnehmen, damit die Margen-Entscheidung (B1) gegen einen Preis faellt.

**B8. Strang B ist entscheidbar, bis auf ein Wort.** B.1 zitiert die
Architekturreferenz korrekt (`docs/architecture_reference.md:43-52`:
Stapelzug gesammelt aufgeloest, `apply_via_chosen_action` je Pfad verschieden;
Feld `referee.rs:443`, Verzweigung `:950`), und der Stopp in B.3 Punkt 2 ist
binaer und damit brauchbar - aber "falls der gemessene Unterschied relevant
ist" (B.2) hat keine Zahl. Vorschlag: "relevant" durch den Anteil abweichender
Folgehandlungen ersetzen (Grundmenge `DrawStackPeek`-Entscheidungen, Einheit
Anteil), Schwelle vorab.

**B9. Strang C steht in Spannung zum eingetakteten Fahrplan.** par.4 wertet
Variante B nur als Vereinfachungserfolg, wenn sie einen bestehenden Proxy
ersetzt; `PREREG_round_transition_search_sampling.md` par.12/13 begruendet B
aber mit DREI zusaetzlichen Nutzniessern und nennt keinen abzuloesenden Proxy,
und Schritt 33 des v29-Programms (`evaluations/v29_program_agent_plan.md:157`)
ist der Bau, nicht die Abloesung. Vorschlag: par.4 ausdruecklich als
NACHGELAGERTE Buchhaltung kennzeichnen, kein Veto gegen den gebauten Arm -
sonst liest sich die Regel als Aufnahmebedingung.

**B10. Strang D ist gut belegt, aber keiner Prereg zugeordnet, die ihn traegt.**
Der Befund stimmt (`docs/architecture_reference.md:188-197`: SECHS Bool-
Dialekte an `shaping.rs:999`, `state.rs:209`, `tiling_solver.rs:374/386`,
`net_mcts.rs:230`; drei stille Env-Verschlucker `net_batcher.rs:249`,
`round5.rs:199`, `scoring.rs:1508`), aber die Kandidatenliste von
`PREREG_code_cleanup_closeout.md` par.4 (Stufe 2) enthaelt den typsicheren
Parser NICHT. Vorschlag: dort aufnehmen oder Strang D hier als eigene Stufe
mit eigenen Toren fuehren, statt ihn an eine Prereg zu delegieren, die ihn
nicht kennt.

**Gesamturteil:** Die Richtung ist sauber abgegrenzt und die Sperren gegen
voreiliges Loeschen sind richtig gesetzt, aber ohne bezifferte Margen-Untergrenze
(B1), ohne die Kostenzeile (B7) und mit der ueberholten Moon-Zeile (B5) ist die
Prereg heute eine Absichtserklaerung und noch kein ausfuehrbarer Messplan.

## par.9 STELLUNGNAHME DES KOORDINATORS (2026-09-16, Nutzer: "im kern stimmt es schon. mir kommt ebenfalls vor wir sind zu komplex unterwegs")

Kein Bau, kein Entscheid; Vorschlag zur Reihenfolge, damit aus der Absichtserklaerung (par.8
Gesamturteil) ein Messplan wird.

**Zustimmung im Kern, mit drei Zahlen statt eines Gefuehls:** `docs/knobs.md` Z.9 zaehlt **125
Knoepfe (66 aktiv, 48 diagnose, 10 tot)**; das Netz exportiert **8 ONNX-Ausgaben** (policy, value,
moon, points, ownership, value_wdl_logits, opp_points, endgame_margin -- am Modell
`alphazero_v29-b03_brierbest.onnx` gelesen); und der moon-Kopf hat seit dem 2026-08-20 mit
Gewicht 1,0 auf ein Ziel trainiert, das nicht nur konstant, sondern **unlernbar** war (die
Sonnenseite steht als Farbzaehler im Eingang, `features.rs:1150-1158`; `moon_stack_order`
par.12.0). Die Komplexitaet zeigt sich nicht im Elo, sondern in den Betriebsvorfaellen dieser
Woche (drei Ketten-Stillstaende, ein ueberschriebener Monolith, ein kontaminierter Val-Cache,
alle in `docs/pitfalls.md`). Das ist genau die Irrtumskosten-Rechnung aus CLAUDE.md.

**Wo ich die Reihenfolge von Strang A umdrehen wuerde:** A.3 misst die Koepfe EINZELN, rund 4,5 h
je Kandidat (par.8 B7), also 13-14 h fuer drei. Billiger und naeher an der Frage des Nutzers
ist EIN Minimalkern-Arm zuerst:

* **`v29-b06` = Rezept b03 mit allen Hilfs-Losses aus** (`--moon-loss-weight 0`,
  `--ownership-weight 0`, ohne `--opp-points-head`, ohne `--endgame-head`), sonst identisch
  (Fenster, Warmstart, Seed 20260941, 12 Epochen). Vorher am Code pruefen, welche Ausgaben die
  Champion-Spec in der SUCHE konsumiert (`score_utility_b 20` liest vermutlich den points-Kopf;
  Regel 0: nachsehen, nicht raten) -- diese Ausgaben bleiben, alles andere faellt.
* Bezug b03, Tor wie A.4 (zwei Seeds, 200 Paare, ohne Frueh-Stopp, Logs), Marge vom Nutzer, mit
  der Untergrenze aus par.8 B1 (unter rund 5 Prozentpunkten ist bei 800 Partien nichts
  belegbar). Kosten rund 4,5 h.
* **Lesart vorab:** haelt b06 die Marge, ist die Vereinfachung EN BLOC in v30 uebernehmbar und
  A.3 entfaellt; faellt b06 durch, wird A.3 einzeln gefahren, um den tragenden Kopf zu finden;
  ist b06 signifikant BESSER, gilt B6 (Staerkebefund, eigene Identitaet, Elo-Kante).
* Der Widerspruch zu A.3 ("einzeln, nicht faktoriell") ist keiner: der Minimalkern ist kein
  faktorieller Sweep, sondern die Baseline aus `docs/external_relaunch_plan_2026-09-16.md`
  Punkt 2 -- gemessen im heutigen System statt in einem Relaunch.

**Zur Moon-Zeile in A.3 (par.8 B5):** ueberholt. Stand: b05 (Kopf aus) gegen b03 427:373 aus 800
Partien, z = 1,98 (`moon_stack_order` par.12.6 "ARM v29-b05 GEMESSEN"); b04 (repariertes Ziel)
gemessen 2026-09-17: 287:323 gegen b03, ein Seed signifikant dagegen, gepoolt z -1,56 -- b04 traegt nicht (`moon_stack_order` par.12.8). Bezugspunkt beider Arme ist b03, nicht "b04 gegen b05".

**Zum Relaunch-Dokument:** der Kernsatz ("ist das, was die Suche bewertet, exakt das, was
ausgefuehrt, geloggt und trainiert wird?") ist die richtige Leitfrage, und Strang B (Trace vor
Bau) setzt sie um. Ein Relaunch selbst steht nicht an -- v30 ist der Abschluss
(`project_v30_release_close`). Was davon OHNE Relaunch geht: der Minimalkern-Arm oben, Strang B
als Trace, und ein Knopf-Abbau als Stufe 2 von `code_cleanup_closeout` (Kandidaten: die 10 toten
und die 51 "beantwortet, Default aus"-Knoepfe aus `docs/knobs.md`; Loeschen erst nach der
letzten Generation, Liste vorher). Der unsicherheitsbewusste Tiling-Selector des Dokuments ist
par.14 (Top-K) der Rundenuebergangs-Prereg und kommt, wenn ueberhaupt, nach Variante B.

**Was ich nicht vorschlage:** irgendetwas davon vor dem Ende von b04 und Variante B (Nr. 33-36)
zu starten. Beide Messungen sind eingetaktet, und ein Minimalkern-Arm braucht dieselbe GPU
und dieselben Arena-Stunden.

## par.10 ENTSCHIEDEN (Nutzer 2026-09-16, 21:55): Marge 5 Prozentpunkte, `v29-b06` nach Variante B

Nutzer woertlich: *"marge 5 prozentpunkte, b06 nach variante b eintakten"*. Damit sind die zwei
offenen Groessen aus par.6 Punkt 2 und par.9 gesetzt:

**Arm `v29-b06` (Minimalkern):** Rezept b03 mit allen Hilfs-Losses aus -- `--moon-loss-weight 0`,
`--ownership-weight 0`, ohne `--opp-points-head`, ohne `--endgame-head` -- sonst identisch
(Fenster `window_v29.txt`, Warmstart `v28-b02_brierbest`, Seed 20260941, 12 Epochen, 794,
`--select-by-brier`, `--fast-loader`). **Vor dem Start am Code pruefen, welche ONNX-Ausgaben die
Champion-Spec in der SUCHE liest** (`score_utility_b 20`, `envelope_*`; Kandidat ist der
points-Kopf) -- diese bleiben im Rezept, der Manifest-Diff gegen b03 muss GENAU die
abgeschalteten Koepfe und den Namen zeigen. Bezugspunkt b03; Val-Split, Monolith und
Val-Cache von b03 (`--cache-file`, beide Anteile vorbauen -- Lehre aus dem b04-Lauf).

**Nichtunterlegenheits-Regel, aus der Nutzer-Zahl formalisiert (Koordinator, VOR dem Lauf):**
Tor wie A.4 -- zwei Seeds a 200 Paare, Blockgroesse 5, KEIN Frueh-Stopp, `--log-games`,
Champion-Spec beidseitig, Einheit Sieg auf gepaarten Partien.

1. Gepoolt ueber beide Seeds (n = 800 Partien) liegt die Siegquote von b06 bei **mindestens
   45,0 Prozent** (Marge 5 Prozentpunkte gegen 50,0).
2. **Kein Seed** zeigt einen signifikanten Nachteil fuer b06 (McNemar p < 0,05 GEGEN b06).
3. Die sechs Standard-Kennzahlen aus denselben Logs; ein Einbruch bei vollen Spalten oder
   Spezialfeldern, der in BEIDEN Seeds dasselbe Vorzeichen traegt, wird als Richtungsnachteil
   im Sinne von A.4 gewertet und vorgelegt, auch wenn Punkt 1 haelt.

Lesart: 1 und 2 halten -> die Vereinfachung ist en bloc fuer v30 uebernehmbar (Nutzer-Entscheid
zur Aufnahme bleibt), A.3 entfaellt. 1 oder 2 reisst -> A.3 einzeln, um den tragenden Kopf zu
finden. b06 SIGNIFIKANT besser (gepoolt McNemar p < 0,05 fuer b06) -> Staerkebefund nach par.8
B6: eigene Identitaet, Elo-Kante nur auf Anweisung. Zur Aufloesung: 800 Partien tragen eine
Marge von 5 Prozentpunkten gerade (par.8 B1), eine kleinere nicht.

**Eintaktung:** NACH Variante B, also nach Fahrplan Nr. 36 (A/B), als Nr. 36a. Kosten rund 4,5 h
(Training 1,43 h, Tor 1 zwei Seeds a 86-91 min, gemessen). Name `v29-b06` in
`docs/generation_naming.md` reserviert.

### 10.1 VORPRUEFUNG DURCH (2026-09-16, 23:40, Lese-Agent, tragende Stellen vom Koordinator nachgeprueft): was die Suche unter der Champion-Spec liest

| Ausgabe | Leser | unter `frozen_champions/v28-b02/spec.json` | Folge fuer b06 |
| --- | --- | --- | --- |
| `policy` | Prior, `net_mcts.rs:2526-2531` | tragend | bleibt |
| `value` | Blattwert `net_mcts.rs:2607-2610`, Tiling-Stichentscheid `self_play.rs:2223-2228` | tragend | bleibt |
| **`moon`** | **Plackett-Luce-Prior des Fan-outs, `net_mcts.rs:2553-2564`, bei `moon_order_variants = 1` (Default, Spec setzt das Feld nicht)** | **AKTIV, rund 20 Entscheide je Partie** | Kopf bleibt als Ausgang und wird GELESEN; `--moon-loss-weight 0` schaltet nur den Loss ab -- exakt die Lage von b05, dessen Tor 1 gegen b03 genau das gemessen hat (par.12.6 der Mond-Prereg). Kein neuer Konfundierer gegenueber b05 |
| `points` | gelesen (`net_mcts.rs:2671/2677`), aber `POINTS_UTILITY_WEIGHT 0`, `score_utility_c 0` (`:3382` uebersprungen) | gelesen, Gewicht 0 | Ausgang muss bleiben (positional `out[3]`, `net.rs:471`); Loss ist nicht Teil von b06 |
| `ownership` | Blatt `shaping.rs:969-971` und Tiling `self_play.rs:2330-2341`, beide Gewicht 0; Huelle nur Modus 3 (`envelope.rs:1245-1252`), Spec faehrt Modus 1 | tot | `--ownership-weight 0`; Ausgang bleibt (Export unbedingt, Paritaets-Fixture verlangt nichtleeren Vektor `net_batcher.rs:418-424`) |
| `opp_points` | nur bei `score_utility_c`, Denial-Eps, Tiling-Punkteblend > 0 | tot | `--opp-points-head` weglassen: Kopf wird nicht konstruiert (`train.py:1646-1655`), Engine erkennt per Namen (`net.rs:859-873`) |
| `endgame_margin`, `value_wdl_logits` | kein Leser in `engine/src` (grep) | tot | `--endgame-head` weglassen; WDL-Logits bleiben (Teil des value-Kopfs) |

**Korrekturen an par.10:** `score_utility_b = 20` liest KEINEN Kopf -- es ist der Nenner in
`score_utility_term` (`net_mcts.rs:2746-2747`) und bei `score_utility_c = 0` inert; die Vermutung
"points-Kopf" in par.9/par.10 war falsch. Die ersten vier Ausgaben werden POSITIONAL gelesen
(`net.rs:468-471`), ein ONNX ohne `moon` oder `points` wuerde still verrutschen -- deshalb duerfen
diese beiden Koepfe nur auf Gewicht 0, nicht weg.

**Rezept `v29-b06`, praezisiert:** = b05 (`--moon-loss-weight 0`) plus `--ownership-weight 0`, ohne
`--opp-points-head`, ohne `--endgame-head`; sonst b03. Der Vergleich gegen b03 misst damit den
Minimalkern gegen den vollen Kopfsatz; der Vergleich gegen b05 (falls gewuenscht, Nutzer-Entscheid)
wuerde die drei Koepfe jenseits von moon isolieren. Der Warmstart `v28-b02_brierbest` traegt die
weggelassenen Koepfe als ueberzaehlige Gewichte, die `train.py:1657-1670` ignoriert.

### 10.2 Nachtrag zu Strang C (par.4), 2026-09-17: Variante B traegt nicht

`PREREG_round_transition_search_sampling.md` par.17.9: A/B am Champion negativ (169:191, Block-z
-1,13). Die Regel aus par.4 ("nur als Vereinfachungserfolg, wenn sie einen Proxy ersetzt") wird
damit nicht gebraucht -- es gibt nichts aufzunehmen. Strang C ist erledigt; der Knopf bleibt mit
Default 0 im Code (Registratur: Diagnose) und ist ein Kandidat fuer die Knopf-Aufraeumung in
Stufe 2 des Code-Abschlusses.

### 10.3 ARM v29-b06 GEMESSEN (2026-09-17, 04:54): der Minimalkern ist UNTERLEGEN, die Marge reisst

**Training** (`tools/night_v29_b06_minimal_core.sh`, Manifest `models/manifest_train_v29-b06_20260917_013522.json`):
b03-Rezept mit `--moon-loss-weight 0`, `--ownership-weight 0`, ohne `--opp-points-head`, ohne
`--endgame-head`; Monolith `data/.cache_fd13f54061cd_b06.h5` (label/794, Stempel geprueft), Val-Cache
`eaa464b44cf7`, cuda, 12 Epochen, 4.538.842 Samples, **rund 57 min** (01:35-02:32; b03 1,38 h -- die
weggelassenen Koepfe sparen sichtbar Zeit). `alphazero_v29-b06_brierbest.onnx`. Erster Anlauf um
01:19 vom `--cache-file`-Waechter abgebrochen (Pfadform-Stempel, `docs/pitfalls.md`), Manifest
`..._011916.json` ist Loeschkandidat.

**Tor 1 gegen b03** (Champion-Spec beidseits, 400 Sims, Blockgroesse 5, `--log-games`, SPRT-Schranken
alpha = beta = 0,001, Deckel 200 Paare; beide Seeds haben die untere Schranke gerissen):

| Groesse | Seed 20261140 | Seed 20261141 |
| --- | --- | --- |
| Siege b06 : b03 | **111 : 139** (250 Partien, 125 Paare) | **125 : 155** (280 Partien, 140 Paare) |
| SPRT | H0, LLR -7,07 | H0, LLR -7,61 |
| McNemar p (einzeln) | 0,087 | 0,077 |
| gepaarte Differenz | -0,224 | -0,214 |
| volle Spalten b06 / b03 | 0,87 / 0,98 (-0,11) | 0,91 / 1,05 (-0,14) |
| Spalten >= 4 | 2,18 / 2,25 | 2,15 / 2,26 |
| Zeilen voll | 0,12 / 0,13 | 0,16 / 0,15 |
| Strafleiste | 8,24 / 9,07 (-0,83) | 8,26 / 7,99 (+0,28) |
| Spezialfelder belegt | 1,33 / 1,27 | 1,28 / 1,25 |
| eigene Punkte | 51,73 / 52,33 (-0,60) | 50,66 / 53,91 (-3,25) |
| Margin | -1,20 | -6,51 |
| Replay | 244 von 250 | 280 von 280 |
| Laufzeit | 2.876 s, 11,5 s je Partie | 3.013 s, 10,8 s je Partie |

**Gepoolt: 236 : 294 von 530 Partien = 44,5 Prozent** (Regel par.10 Punkt 1: mindestens 45,0);
46 A-Sweeps gegen 75 B-Sweeps, **McNemar exakt p = 0,011**; Block-Ebene 53 Bloecke a 10 Partien,
Siegdifferenz **-1,09 je Block, SE 0,38, z = -2,86**.

### Verdikt

**Die Nichtunterlegenheit reisst, und zwar signifikant:** Punkt 1 (44,5 unter 45,0 Prozent) faellt,
Punkt 2 haelt formal (kein Seed einzeln unter 0,05), aber beide Seeds zeigen dieselbe Richtung und
gepoolt ist der Nachteil signifikant (p 0,011, Block-z -2,86). Fuenf der sechs Kennzahlen liegen in
beiden Seeds gegen b06 (volle Spalten, Spalten >= 4, Zeilen-Fuellung, Punkte, Marge); nur die
Spezialfelder und in Seed 1 die Strafleiste sprechen fuer b06. **Der Minimalkern ist dem vollen
Kopfsatz um rund 5,5 Prozentpunkte unterlegen.**

**Was damit gemessen ist, im Verbund mit b05:** b05 (nur moon-Loss aus) lag gegen b03 bei 427:373
(z +1,98); b06 (moon UND ownership aus, opp_points und endgame weg) liegt bei 236:294 (z -2,86).
**Mindestens einer der drei Koepfe ownership / opp_points / endgame traegt als TRAININGSSIGNAL fuer
den gemeinsamen Rumpf** -- obwohl die Suche unter der Champion-Spec keinen von ihnen liest
(par.10.1). Das ist genau der Fall, den A.2 Hypothese 2 vorab benannt hat ("Nutzen als
Trainingssignal, ein Suchverbraucher auf 0 ist kein Ersatzbeleg"). Welcher Kopf es ist, sagt b06
nicht.

**Lesart aus par.10 ("1 oder 2 reisst -> A.3 einzeln, um den tragenden Kopf zu finden"):** die
Einzelmessung ist damit die registrierte Fortsetzung, kostet aber rund 4,5 h je Kandidat
(par.8 B7, drei Kandidaten 13-14 h) und ist ein Trainingsarm je Kopf. **Ob sie gefahren wird, ist
Nutzer-Entscheid** -- der Nutzer hat b06 als Abschluss von v29 benannt (2026-09-16, 22:00), und die
Regel "ab v30 nur Arme aus offenen Preregs" liesse A.3 zu, verlangt sie aber nicht. Ohne A.3 gilt
fuer das v30-Rezept: alle drei Koepfe bleiben; `moon_loss_weight 0` bleibt die Empfehlung aus
`moon_stack_order` par.12.8 (b05).

**Netz-Gesundheit (`v29_window` par.6d Punkte 1-2, nach Tor 1 gefahren, 04:58):** tote Einheiten der
Flachvektor-Schichten auf frozen_v3 (1.800 Zustaende): b06 2,60 Prozent, b04 2,60, b05 2,60, Referenz
b03 2,60 -- GRUEN (Schwelle 5,21; `dead_units_v29_b04_b05_b06.json`). Spaltennormen der 39 neuen
Eingaenge (755..793) in `flat_branch.0.weight`: b03 Mittel 0,137 (17 lebend), b04 0,251 (18), b05
0,231 (17), b06 0,258 (17), Altspalten je rund 3,02 -- die neuen Spalten leben in allen Armen
gleich schwach, kein Arm hat sie abgestellt oder aufgeblasen.

Kein Elo-Eintrag (Arm gegen Arm; Register nur auf Anweisung). Artefakte
`tor1_v29-b06_vs_b03_s20261140.json`, `_s20261141.json`, `arena_columns_tor1_v29-b06_vs_b03_s*.json`,
`plate_points_tor1_b06_s*.json`.

### 10.4 ENTSCHIEDEN (Nutzer 2026-09-17): statt A.3 einzeln ein ZWEIERPAKET -- Arm `v29-b08`

Nutzer woertlich: *"dann pack die tendenziell am wenigsten tragenden koepfe in ein paket zusammen
(2er paket zb) und fahr sie gegen b03. ich will noch nicht alle einzeln fahren."*

**Auswahl der zwei Koepfe, aus der Aktenlage (kein neues Messen):**

* **ownership** -- das Trainingsgewicht hat in v22 gemessen nichts getragen (w0-Arm 0,260 gegen
  0,297 volle Spalten, t 1,53; `project_v22_cycle_result`), beide Suchverbraucher stehen auf 0
  (par.10.1). Hinweis zur Vorgeschichte: der Nutzer hatte am 2026-08-11 festgelegt, dass der
  Ownership-KOPF bleibt ("der ownership head kommt so oder so. die frage ist nur mit welchem
  faktor") -- das ist mit diesem Arm vereinbar: der Ausgang bleibt, nur der Loss geht auf 0, wie
  schon bei b06.
* **endgame** -- kein Leser in der Suche (par.10.1), Ziel `root_q` nur aus Netz-Self-Play in der
  Runde-5-Zone (par.8 B4), fuer Heuristik-Korpora komplett maskiert. Nie isoliert gemessen.
* **opp_points bleibt drin** -- dichtes Ziel an jedem Zustand (Gegnerpunkte), der plausibelste
  Traeger fuer den Rumpf unter den drei.
* **moon bleibt wie bei b03 (Gewicht 1,0)**, damit der Vergleich b08 gegen b03 NUR das Paket misst;
  moon ist mit b05 schon einzeln gemessen.

**Arm `v29-b08`** = b03-Rezept mit `--ownership-weight 0` und OHNE `--endgame-head`, sonst identisch
(Fenster `window_v29.txt`, Warmstart `v28-b02_brierbest`, Seed 20260941, 12 Epochen, 794,
`--select-by-brier`, `--fast-loader`, `--opp-points-head`, moon-Loss 1,0). Manifest-Diff gegen
b03 muss GENAU `ownership_weight`, `endgame_head`, `cache_file` und den Namen zeigen.

**Daten:** neue Bloecke und neuer Monolith unter dem Schluessel MIT Formel-Version und
`MOSAIC_FEATURES_FROM_RUST=1` (Weg (1) aus `rust_data_layer` par.9a/9b, Nutzer-Entscheid vom selben
Tag) -- die erste Kette, die den neuen Schluessel benutzt; Bauzeit wird gemessen und in
`docs/measured_runtimes.md` eingetragen. Val-Cache entsteht neu (der alte `eaa464b44cf7` ist unter
dem neuen Schluessel nicht mehr adressierbar); BEIDE Anteile per `--cache-file` bzw. ueber den
gepruefen Namenspfad. ACHTUNG Vergleichbarkeit: b03 wurde auf Bloecken mit teils ALTER
Formel-Semantik trainiert (par.9a: 1.746 Dateien vor dem 2026-09-12), b08 auf einheitlich frischen
Planes -- der Unterschied ist 0,67 Prozent der Alt-Zustaende in einem Kanal (par.9a) und wird
als bekannter, kleiner Konfundierer im Verdikt genannt, nicht weggerechnet.

**Tor und Lesart wie par.10 (Marge 5 Prozentpunkte):** gepoolt >= 45,0 Prozent auf 800 Partien
(zwei Seeds a 200 Paare, ohne Frueh-Stopp) und kein Seed signifikant dagegen.
Ausgaenge: haelt b08 -> ownership und endgame sind entbehrlich, der Traeger aus b06 ist
opp_points (Herleitung ueber Differenz, nicht Messung), v30-Rezept ohne die beiden; reisst b08 ->
mindestens einer der beiden traegt, dann Einzelmessung NUR dieser zwei (2 x 4,5 h) als naechster
Schritt, Nutzer-Entscheid; b08 signifikant besser -> Staerkebefund (par.8 B6).

**Kette:** `tools/night_v29_b08_head_pair.sh` (Muster b06), wartet auf freie CPU (Sonde) und startet
erst, wenn der Schluessel-Umbau (par.9b) im Baum ist. Fahrplan 36e.

### 10.5 Lauf v29-b08 (2026-09-17)

* **Bloecke und Monolith** unter dem neuen Schluessel `421448d12eb8` (Formel-Version, FROM_RUST=1):
  09:34:12 bis 10:06:56, **1.964 s** fuer 2.800 Dateien mit 6 Workern plus Merge, exklusiv; Stempel
  im Monolithen gleich dem Schluessel des Splits (Kette Schritt 2). Trainingsliste byte-gleich mit
  der von b03.
* **Manifest-Diff b08 gegen b03** (`manifest_train_v29-b08_20260917_100659.json` gegen
  `manifest_train_v29-b03_20260914_111513.json`, alle `cli_args`): GENAU `ownership_weight` 0,0 gegen
  1,0, `endgame_head` False gegen True, `cache_file` gesetzt gegen None, `name`; dazu
  `moon_target_source` 'label' gegen None, ein Feld, das es zu b03s Zeit noch nicht gab und dessen
  Default 'label' ist (`PREREG_moon_stack_order.md` par.12.7: b03 und b05 rechnen dasselbe Ziel).
  Alles andere identisch, einschliesslich Seed 20260941 und Warmstart.
* Training seit 10:06:56 auf der GPU, daneben als CPU-Auftrag das Kompilat von Variante C und dem
  Stichentscheid-Knopf (10:12 bis etwa 10:30): die Trainingsdauer ist GEBREMST und geht so markiert
  in `docs/measured_runtimes.md`.
* **Training v29-b08 DURCH 11:21:12, Exit 0: 4.456 s = 74 min** (10:06:56 bis 11:21:12, CUDA, GEBREMST:
  daneben 10:12-10:14 das Kompilat von Variante C, und der Val-Cache-Bau lief einkernig; b06 ohne diese
  Last 57 min). Bestes `val_brier` **0,1794 in Epoche 6** (letzte 0,1797; b03 0,17967, b04 0,17915 --
  alle drei innerhalb der Aufloesung, `moon_stack_order` par.12.7), Val-R2 Value 0,545, Policy-Val 0,40;
  Plateau-Marker ab Epoche 10. Export `models/alphazero_v29-b08_brierbest.onnx` (flat_input 794, 79 Planes,
  11.320.948 Byte). **Tor 1 gegen b03 laeuft seit 11:21:33** (Seed 20261160 zuerst, dann 20261161), Ende
  erwartet gegen 14:30 (2 x 80-93 min gemessen).

### 10.6 Tor 1 v29-b08 gegen b03 GEMESSEN (2026-09-17, 11:21-13:58): das Zweierpaket HAELT

Aufbau wie par.10.4: `alphazero_v29-b08_brierbest.onnx` gegen `alphazero_v29-b03_brierbest.onnx`, Champion-Spec
beidseits, 400 Sims, zwei Seeds a 200 Paare ohne Frueh-Stopp (SPRT-Schranken +-6,91 nie erreicht), Blockgroesse
5, 10 Threads, `--log-games`, exklusiv (keine Nebenlast). Grundmenge Partien, Einheit Siege.

| Groesse | Seed 20261160 | Seed 20261161 | gepoolt |
| --- | --- | --- | --- |
| Siege b08 : b03 | 210 : 190 | 195 : 205 | **405 : 395 von 800 = 50,6 %** |
| Sweeps b08 / b03 (Paare) | 46 / 33 | 56 / 64 | 102 / 97, exakter Vorzeichentest p 0,78 |
| Diff je Paar, KI95 | +0,100 [-0,098; +0,298] | -0,050 [-0,243; +0,143] | |
| Block-Ebene (80 Bloecke a 10 Partien) | | | Siegdiff b08 minus b03 **+0,125 je Block, SE 0,38, z = +0,33** |
| Laufzeit | 4.606,9 s | 4.605,4 s | 11,5 s je Partie |

**Verdikt nach par.10.4:** gepoolt 50,6 Prozent, weit ueber der 45,0-Prozent-Marge, kein Seed signifikant
dagegen (p 0,37 und 0,68) -> **HAELT: ownership-Loss und endgame-Kopf sind zusammen entbehrlich.** Kein
Staerkebefund (z +0,33). Mit b06 (par.10.3, 44,5 Prozent, z -2,86) folgt per Differenz, NICHT per Messung:
**der Traeger aus der Dreiergruppe ist opp_points** (Herleitung; b06 hatte zusaetzlich moon 0, das nach b05
kein Traeger ist).

**Sechs Standard-Kennzahlen** (Mittel je Seite ueber beide Seeds; Quellen `arena_columns_tor1_v29-b08_vs_b03_s*.json`,
794 von 800 Partien nachgespielt, und `plate_points_tor1_b08_s*.json`, Grundmenge Bretter je Modell):

| Kennzahl | b08 | b03 | Diff |
| --- | --- | --- | --- |
| Reihen: volle Zeilen je Partie / lange Reihen vollendet | 0,107 / 3,01 | 0,132 / 3,02 | -0,025 / -0,01 |
| Spalten: volle Spalten / max. Hoehe / >= 3 / >= 4 | 0,947 / 5,65 / 3,14 / 2,24 | 0,986 / 5,67 / 3,23 / 2,26 | -0,039 / -0,02 / -0,08 / -0,02 |
| Strafleiste gesamt (Strafpunkte je Partie, `boden`) | 8,39 | 8,20 | +0,19 |
| Plattenpunkte gesamt / je Kriterium | 7,34; Spezialfelder -10,78, Vertikale 7,02, Mehrfarbige 2,64, Eckplatten 8,55, Aeussere 10,45 | 7,78; -10,29, 7,05, 2,82, 8,72, 10,57 | -0,44; -0,49, -0,03, -0,18, -0,16, -0,11 |
| Eigene Punkte | 52,65 | 53,33 | -0,68 |
| Marge | -0,68 | +0,68 | -1,36 |

Lesart: die Siege sind gleich, das Punkteniveau liegt einen halben Punkt tiefer, getragen vom Posten
Spezialfelder (-0,49) und den Spalten (-0,04 volle Spalten). Das ist die gleiche Richtung wie bei b06, nur
viel flacher, und innerhalb der Seed-Streuung (Seed 1 +0,03 Punkte, Seed 2 -1,38). Kein Handlungsbedarf, aber
ein Merkposten fuer die Rezeptwahl: wer die beiden Koepfe streicht, gibt womoeglich einen halben Punkt
Spezialfelder her.

**Netz-Gesundheit (par.10.1 Vorpruefung) fuer b08:** nicht gesondert gefahren; das Rezept aendert nur
Loss-Gewicht und einen entfernten Kopf, die Ownership-Ausgangsschicht wird mit Gewicht 0 nicht mehr trainiert
(wie b06, dort gruen).

**Rezeptfolge ENTSCHIEDEN (Nutzer 2026-09-17, "dann streiche sie"):** v30 ohne `--endgame-head` und mit
`--ownership-weight 0` (die Ausgabe bleibt, Nutzer-Festlegung 2026-08-11), `--opp-points-head` bleibt.
Der Punkte-Merkposten (-0,7, Spezialfelder -0,5, innerhalb der Seed-Streuung) ist zur Kenntnis genommen und
wird bei der v30-Abnahme ueber die sechs Kennzahlen mitgelesen. Damit ist Strang A dieser Prereg
abgeschlossen; offen bleibt nur der Kopf-Zeiger fuer `moon_loss_weight` (moon_stack_order par.12.8).

### 10.7 Arm `v29-b09` = das v30-Rezept auf dem v29-Fenster (Nutzer 2026-09-17, registriert VOR dem Bau)

Nutzer woertlich: *"dann warten wir auf b07 und fahren mit dem staerksten arm. v29-b09 nehmen wir ebenfalls
mit und schauen wie er sich schlaegt."* Kein neuer Prereg-Arm im Sinne der v30+-Regel, sondern die
Zusammenfuehrung dreier entschiedener Knoepfe auf einem Netz:

* `--moon-loss-weight 0` (b05 gegen b03 427:373 von 800, z 1,98; `PREREG_moon_stack_order.md` par.12.8),
* `--ownership-weight 0` und OHNE `--endgame-head` (b08 gegen b03 405:395, par.10.6, Nutzer-Entscheid "dann
  streiche sie"),
* `--opp-points-head` bleibt; Warmstart `v28-b02_brierbest`, Seed 20260941, 12 Epochen, `--select-by-brier`,
  `--fast-loader`, Fenster `window_v29.txt`, sonst b03.
* **INPUT_SIZE nach dem b07-Verdikt** (`round_transition_search_sampling` par.18): traegt Variante C, dann 884
  mit Abschnitt 17 (Monolith `790ac07353a6` liegt), sonst 794 (Monolith `421448d12eb8` liegt). Die Kette liest
  `config.INPUT_SIZE` und findet ueber den Fenster-Schluessel den passenden Monolithen.

**Messung:** Tor 1 gegen b03, zwei Seeds (20261220/20261221) a 200 Paare ohne Frueh-Stopp, Blockgroesse 5,
Champion-Spec beidseits, `--log-games`, sechs Kennzahlen. Lesart: b09 misst, ob die drei Knoepfe ZUSAMMEN das
halten, was sie einzeln gezeigt haben (Erwartung aus b05 und b08: mindestens gleich, eher leicht besser); reisst
b09 die 5-Prozentpunkte-Marge, wirken die Knoepfe nicht additiv und das v30-Rezept wird vor der Erzeugung neu
entschieden. Zusaetzlich geht b09 als Kandidat in die Champion-Kanten (STATUS Abschnitt 6 Punkt 18) neben dem
staerksten Einzelarm, und er ist **Rueckfall 2 fuer das v30-Training** (Warmstart von b09, falls Kaltstart und
Afterburner das Gating nicht bestehen; `round_transition_search_sampling` 18.11, Nutzer 2026-09-17).

**Kette:** `tools/night_v29_b09_v30_recipe.sh` (Muster b08; `bash -n` gruen; NICHT gestartet). Start nach dem
b07-Verdikt und dem Setzen von `config.INPUT_SIZE`; Training rund 1 h (GPU, Monolith liegt), Tor 1 2 x rund
77 min exklusiv. Fahrplan 36g.

### 10.8 Lauf v29-b09 (2026-09-17, ab 19:55)

* Kette `tools/night_v29_b09_v30_recipe.sh` mit `MOSAIC_CHAIN_NO_WAIT=1` neben dem K6-A/B gestartet (erlaubte
  Nebenlast: GPU-Training plus ein CPU-Auftrag). `config.INPUT_SIZE` 884 (18.11), Schluessel `790ac07353a6` wie b07,
  Trainingsliste byte-gleich; **Split plus Merge der liegenden Bloecke 827 s** (kein Blockbau, nur Zusammenfuegen,
  neben dem A/B), Stempel geprueft.
* **Manifest-Diff b09 gegen b03** (`manifest_train_v29-b09_20260917_200920.json`, `cli_args`): `cache_file` 'data/.cache_790ac07353a6.h5' gegen None; `endgame_head` False gegen True; `moon_loss_weight` 0.0 gegen 1.0; `moon_target_source` 'label' gegen None; `name` 'v29-b09' gegen 'v29-b03'; `ownership_weight` 0.0 gegen 1.0. Engine
  `input_size` 884. Alles andere identisch (Seed 20260941, Warmstart `v28-b02_brierbest`, 12 Epochen).
* Training auf CUDA seit 20:09:20; Warmstart-Zeile `755 -> 884, 129 neue Spalten null-initialisiert` wie bei b07.
  Danach wartet die Kette vor Tor 1 auf das Ende des K6-A/B.
* **Training v29-b09 DURCH 21:21:30, Exit 0: 4.330 s = 72 min** (20:09:20 bis 21:21:30, CUDA, GEBREMST: daneben
  das K6-A/B mit 10 Threads). Bestes `val_brier` **0,1785 in Epoche 4** (letzte 0,1786; b07 0,1779, b03 0,17967,
  b08 0,1794 -- alle innerhalb der Aufloesung), Val-R2 Value 0,550, Policy-Val 0,40; Policy-Loss 0,74 statt 1,53
  bei b07/b08, weil der Mond-Loss (Gewicht 0) nicht mehr in die Summe geht -- kein Qualitaetsunterschied, andere
  Summe. Export `models/alphazero_v29-b09_brierbest.onnx` (884). **Tor 1 gegen b03 wartet seit 21:21:30 auf das
  Ende des K6-A/B**, dann exklusiv (Seeds 20261220/20261221).

### 10.9 Kette fuer die Champion-Kanten (geschrieben 2026-09-17, nicht gestartet)

Auftrag: STATUS Abschnitt 6 Punkt 18 (Nutzer 2026-09-17: *"dann warten wir auf b07 und fahren mit dem
staerksten arm. v29-b09 nehmen wir ebenfalls mit"*). Kette `tools/night_champion_edges_v29.sh`,
`bash -n` gruen, NICHT gestartet. Sie fuehrt die beiden Kandidaten **`v29-b07`** und **`v29-b09`**
(beide INPUT_SIZE 884, `config.py:49`) durch die drei Aufhaengungen der Promotions-Checkliste
(`docs/promotion_checklist.md` Punkte 2-4), Reihenfolge b07 zuerst, je Kandidat a) Gating, b) Anker,
c) Champion-2.

**Stufe 0, Vorbedingungen und Warten.** Modelle, Champion-Spec, die zwei Artefakt-Verzeichnisse
`models/frozen_heuristics/hv4_anchor` und `models/frozen_champions/v27-b01` (je mit `venv/`), die vier
Werkzeuge. Wheel-Probe wie in `tools/night_k6_w025_ab.sh`: `engine_config_json()` muss
`special_unlock_w` kennen (das 884er Wheel vom 2026-09-17, 19:37), dazu `INPUT_SIZE = 884` in
`config.py`. Danach Warteschleife auf ZWEI Bedingungen, Poll 120 s mit Meldung je Poll: CPU frei
(gehaerteter PowerShell-Filter mit der Namensbedingung auf python, Muster `night_k6_w025_ab.sh`) UND
`evaluations/artifacts/k6_w025_vs_off_s20261211.json` vorhanden. Die zweite Bedingung ist der Punkt:
ohne sie startet die Kette neben der WARTENDEN K6-Kette und nimmt ihr die Maschine weg.
`MOSAIC_CHAIN_NO_WAIT=1` ueberspringt die Schleife.

**Stufe a) Gating gegen Champion-1** (`tools/paired_gating.py`): `models/alphazero_v28-b02_brierbest.onnx`,
Champion-Spec `models/frozen_champions/v28-b02/spec.json` BEIDSEITS, 400 Sims, c_puct 1,5, Blockgroesse 5,
`--max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001`, `--threads 10 --log-games --no-promote-winner`.
Spec und Flags sind uebernommen von der b03-Kante gegen den Champion (`PREREG_v29_window.md` par.9,
"Flags bitgleich zur b01-Kante"; Skript `tools/night_v29_tor1_b03_vs_champion.sh`); der Unterschied ist
gewollt: par.9 lief mit alpha = beta = 0,05 und drei frueh gestoppten Seeds, hier laeuft der Deckel von
200 Paaren. Zwei Seeds je Kandidat (b07 20261230/20261231, b09 20261240/20261241), Artefakte
`gating_<kandidat>_vs_v28-b02_s<seed>.json`, danach `tools/probes/arena_column_probe.py --artifact` und
`tools/plate_points_from_arena.py ... --block 5`.

**Stufe b) Anker-Kante** (`tools/frozen_referee_match.py`): 1:1 der Aufruf, der
`evaluations/artifacts/anchor_edge_v29-b03_vs_hv4_anchor.json` erzeugt hat
(`tools/night_v29_anchor_edge_b03.sh:42-54`, am Artefakt gegengelesen: `sims_a` 400, `c_puct_a` 1,5,
`sims_worker` 150, `c_puct_worker` 0,3, `n_games` 150, `workers` 6, `force_cross_era` true,
`spec_a` = Champion-Spec). Neu sind nur Modell, Seed-Basis und Ausgabename
`anchor_edge_<kandidat>_vs_hv4_anchor.json`. Festes n=150 ohne Frueh-Stopp ist Checkliste Punkt 3.

**Stufe c) Champion-2-Kante** gegen das Artefakt `v27-b01` @400: Form der Kante des amtierenden
Champions, am Artefakt `champion2_v28-b02_vs_v26-b01.json` abgelesen (`sims_worker` 400,
`c_puct_worker` 1,5, `n_games` 150, 6 Prozesse, `force_cross_era`, `spec_a` = die damalige
Champion-Spec) und in `PREREG_code_cleanup_closeout.md` (Abschnitt "Champion-2-Kante (Promotion
Schritt 4)") registriert. **n=150 ist belegt, nicht geschaetzt** -- auch `STATUS.md` Abschnitt 3 fuehrt
"Anker-Kante n=150 / Champion-2-Kante n=150". Artefakte
`champion2_<kandidat>_vs_v27-b01_s<seed-basis>.json`.

**Kein INPUT_SIZE-Fallback noetig.** `tools/frozen_referee_match.py` kennt keinen input_size-Schalter
(grep ohne Treffer), und die Engine schneidet den Flachteil auf die Modellbreite
(`engine/src/net.rs:979`, `split_planes_flat_batch_src`: Planes ab 0 auf die Modellbreite, Flachteil ab
der QUELL-Grenze). Das Artefakt v27-b01 ist 744 (`models/frozen_champions/v27-b01/manifest.json`, Feld
`input_size`) und bringt sein eigenes Wheel mit. Praezedenz: die Kante v28-b02 (damals 755) gegen v26-b01
(744) lief ohne Zusatzflag.

**Spec-Nebenbefund, der eine Wahl erledigt:** `models/frozen_champions/v27-b01/spec.json` ist Feld fuer
Feld INHALTSGLEICH mit `models/frozen_champions/v28-b02/spec.json` (verglichen 2026-09-17). Fuer die
Champion-2-Kante gibt es also keine Spec-Entscheidung, die das Ergebnis verschiebt.

**Seeds.** Gating aus dem Auftrag. Die beiden Anker-Seed-Basen (b07 20261600, b09 20261700) sind HIER
gewaehlt, damit die je 150 fortlaufenden Seeds nicht in die Spanne der b03-Anker-Kante fallen
(20261097 bis 20261246; `--seed-base` erzeugt `n_games` fortlaufende Seeds,
`tools/frozen_referee_match.py:598-599`). Die Champion-2-Basen 20261250 und 20261251 stehen im Auftrag;
ihre Spannen teilen 149 von 150 Seeds, die zwei Kanten sind damit faktisch gepaart -- lesbar, aber
bewusst festgehalten, damit niemand es fuer Zufall haelt.

**Kennzahlen.** Die sechs Standard-Kennzahlen (CLAUDE.md) laufen auf den vier Gating-Artefakten. Auf den
vier frozen-Kanten laufen sie NICHT, und das ist begruendet statt weggelassen: `arena_column_probe.py`
braucht je Partie `names`/`first_player`/`game_seed` aus `--log-games` (Docstring `_replay_end_state`),
`frozen_referee_match` schreibt je Partie nur `scores`/`winner`/`steps`/`seed`/`first_player`/`board_a`/`log`
(am Artefakt `anchor_edge_v29-b03_vs_hv4_anchor.json` nachgesehen). Was dort ablesbar ist -- eigene Punkte
und Margin -- rechnet die Kette in Stufe Z selbst aus `games[].scores` und `games[].board_a`
(`board_a` ist der Sitzindex von Seite A, `tools/frozen_referee_match.py:338`); Reihen-, Spalten- und
Strafleistenauslastung bleiben in diesen zwei Stufen unmessbar.

**Stufe Z.** Die Kette DRUCKT je Kandidat die fertigen `tools/elo_tracker.py add`-Zeilen mit den Zahlen
aus den Artefakten (`--player-a/--player-b/--n`, `--knobs spec:frozen_champions/v28-b02/spec.json`, beim
Gating `--units-from-paired-artifact`, `--early-stop` nur wenn `done_pairs < 200`) und fuehrt sie NICHT
aus; dazu Laufzeiten. Der Koordinator prueft und traegt ein (Regel 0).

**Kosten.** Gating 200 Paare @400 mit Logs: gemessen 4.606,9 s = 77 min
(`evaluations/artifacts/tor1_v29-b08_vs_b03_s20261160.json`, `laufzeit.wanduhr_s`), Planungsgroesse
STATUS Abschnitt 3 86-91 min, vier Laeufe. Anker-Kante n=150, 6 Worker: gemessen 1.292,8 s = 22 min
(`anchor_edge_v29-b03...`, `elapsed_s`; `docs/measured_runtimes.md:197` nennt 1.441-1.491 s), zwei Laeufe.
Champion-2-Kante n=150: gemessen 2.516 s und 2.578 s (`docs/measured_runtimes.md:202` und `:241`), zwei
Laeufe. **ANNAHME: Summe rund 7,5 bis 8 h exklusiv** -- alle gemessenen Zahlen stammen von Kandidaten mit
kleinerem Eingang, dass 884 die Kanten nicht teurer macht, ist unbelegt.

**Offene Punkte fuer den Koordinator.**

1. **`v29-b07` ist gesetzt, nicht aus einem Verdikt abgeleitet.** Der Auftrag nennt beide Kandidaten
   namentlich; die Kette prueft kein "staerkster Arm"-Kriterium. Faellt b07s Tor 1 gegen b03 anders aus
   als in STATUS Abschnitt 6 Punkt 20 vermerkt (dort: b07 traegt, Block-z +2,40), muss der Kandidatensatz
   vor dem Start geaendert werden.
2. **Die frozen-Artefakte tragen keinen `laufzeit`-Block** (nur `elapsed_s`, `total_steps`, `s_per_step`),
   anders als es CLAUDE.md fuer Messartefakte verlangt. Die Kette liest deshalb `elapsed_s` und rechnet
   `s je Partie` selbst. Ob `tools/frozen_referee_match.py` den Block nachtraegt, ist ein eigener
   Entscheid -- eine Aenderung daran beruehrt ein Werkzeug, das in den Anker-Kanten haengt.
3. **Eine Replikationszeile ist nicht vorgesehen** (Checkliste Punkt 2: noetig "falls Fruehstopp unter 150
   Paaren"). Mit alpha = beta = 0,001 und Deckel 200 sollte kein Stopp fallen; falls doch, ist die
   Replikation nachzuziehen und `--early-stop` zu setzen (die Kette druckt das Flag dann selbst).
4. **Kein `set_champion`, kein Einfrieren, keine Pflicht-Diagnostik in dieser Kette.** Checkliste Punkte 1
   und 5-7 laufen erst nach dem Nutzer-Entscheid; die Abschlussausgabe listet sie.

### 10.10 Tor 1 v29-b09 gegen b03 GEMESSEN (2026-09-17/18, 21:34-00:24): das v30-Rezept HAELT, flach positiv

Aufbau 10.7: `alphazero_v29-b09_brierbest.onnx` (884; moon 0, ownership 0, ohne endgame) gegen
`alphazero_v29-b03_brierbest.onnx` (794), Champion-Spec beidseits, 400 Sims, zwei Seeds a 200 Paare ohne
Frueh-Stopp, Blockgroesse 5, 10 Threads, exklusiv auf dem 884-Wheel mit K6-Knopf (Default 0). Grundmenge Partien,
Einheit Siege.

| Groesse | Seed 20261220 | Seed 20261221 | gepoolt |
| --- | --- | --- | --- |
| Siege b09 : b03 | 213 : 187 | 203 : 197 | **416 : 384 von 800 = 52,0 Prozent** |
| Vorzeichentest | p 0,25 | p 0,84 | Sweeps 110 / 94, p 0,29 |
| Diff je Paar, KI95 | +0,130 [-0,074; +0,334] | +0,030 [-0,161; +0,221] | |
| eigene Punkte b09 / b03 | 52,66 / 51,26 | 54,03 / 52,71 | +1,37 |
| **Block-Ebene** | | | 80 Bloecke, Siegdiff **+0,40 je Block, SE 0,39, z = +1,03** |
| Laufzeit | 4.912,1 s (12,28 s je Partie) | 5.090,3 s (12,73 s je Partie) | |

**Verdikt nach 10.7:** Marge haelt mit Abstand (52,0 gegen 45,0 Prozent), kein Seed dagegen, Block-z +1,03 nicht
signifikant -> **die drei Knoepfe wirken zusammen mindestens neutral, eher leicht positiv; das v30-Rezept ist
auf dem v29-Fenster bestaetigt.** Einordnung gegen die Einzelarme: b05 (nur moon 0) 53,4 Prozent, b08 (ownership 0,
ohne endgame) 50,6 Prozent, b07 (nur 884) 54,0 Prozent, b09 (alles ausser der Projektion neu, plus 884) 52,0
Prozent -- alle innerhalb der Seed-Streuung voneinander; die Knoepfe sind nicht additiv im Sinne einer Summe der
Einzeleffekte, aber auch nicht gegenlaeufig. Fuer den Kaltstart in v30 (18.11) ist das die Basislinie, die er
mindestens erreichen muss.

**Sechs Standard-Kennzahlen** (Mittel je Seite ueber beide Seeds; `arena_columns_tor1_v29-b09_vs_b03_s*.json`,
`plate_points_tor1_b09_s*.json`):

| Kennzahl | b09 | b03 | Diff |
| --- | --- | --- | --- |
| Reihen: volle Zeilen / lange Reihen vollendet | 0,144 / 3,02 | 0,130 / 3,05 | +0,014 / -0,03 |
| Spalten: volle / >= 3 | 0,925 / 3,19 | 0,966 / 3,21 | -0,041 / -0,02 |
| **Strafleiste gesamt** | **7,81** | 8,97 | **-1,16** (`penalty_log` +1,80) |
| Plattenpunkte je Kriterium | Eckplatten 8,85, Mehrfarbige 2,06, Vertikale 7,05, Spezialfelder -10,47 | 8,49, 2,64, 7,15, -10,45 | +0,36, **-0,57**, -0,11, -0,03 |
| Spezialfelder belegt / Kuppelbonus | 1,29 / 5,32 | 1,27 / 5,30 | +0,02 / +0,02 |
| Eigene Punkte / Marge | 53,35 / +1,37 | 51,98 / -1,37 | +1,37 / +2,73 |

Lesart: b09 gewinnt seine 1,4 Punkte fast ganz ueber die Strafleiste (-1,16 Strafpunkte, der groesste
Strafleisten-Effekt aller v29-Arme) und gibt bei den mehrfarbigen Feldern (-0,57) und den vollen Spalten (-0,04)
etwas ab. Das ist ein anderes Profil als b07 (Spalten +0,05, Strafleiste -0,37): ohne die Hilfs-Losses spielt
das Netz vorsichtiger. Merkposten fuer die v30-Abnahme: die Spalten-Kennzahl darf im Kaltstart nicht weiter
sinken.

**Folgen:** Fahrplan 36g DURCH; b09 ist Kandidat 2 fuer die Champion-Kanten (Kette 10.9 laeuft an) und Rueckfall 2
fuer das v30-Training (18.11) ist damit gedeckt.

### 10.11 Champion-Kanten v29-b07 GEMESSEN (2026-09-18, 01:48-05:36), Kette 10.9, exklusiv

| Kante | Form | Ergebnis | Laufzeit |
| --- | --- | --- | --- |
| Gating gegen Champion-1 `v28-b02_brierbest` @400, Seed 20261230 | 200 Paare, Champion-Spec beidseits | b07 **204 : 196**, p 0,77 | 4.898 s |
| Gating, Seed 20261231 (Replikation) | 200 Paare | b07 **214 : 186**, p 0,18 | 4.896 s |
| Gating gepoolt | 800 Partien, 80 Bloecke | **418 : 382 = 52,3 Prozent, Block-z +1,17** | |
| Anker-Kante hv4_anchor @150 (c_puct 0,3) gegen b07 @400, Seed-Basis 20261600 | 150 Partien ohne Stopp, Cross-Aera | b07 **129 : 21 = 86,0 Prozent** (b03: 128:22) | 1.246 s |
| Champion-2-Kante gegen `v27-b01` @400, Seed-Basis 20261250 | 150 Partien ohne Stopp | b07 **81 : 69 = 54,0 Prozent** | 2.388 s |

Grundmenge Partien, Einheit Siege. Alle drei Aufhaengungen liegen vor; keine ist gegen b07. **Lesart:** b07 ist
gegen den Champion nicht signifikant besser (52,3 Prozent, z +1,17; b03 hatte 56,1 Prozent auf 490 Partien in
drei Seeds, `v29_window` par.9), gegen den Anker gleich stark wie b03 (86,0 gegen 85,3 Prozent), gegen v27-b01
mit 54,0 Prozent vorn. Die Elo-Zeilen druckt die Kette am Ende (Stufe Z); Eintrag nach Pruefung durch den
Koordinator. Promotion ist Nutzer-Entscheid (Checkliste Punkte 5-7 danach: Pflicht-Diagnostiken, STATUS,
Einfrieren).

### 10.12 Generator-Identitaet v29-b10 und Abnahme-Kette (geschrieben 2026-09-18, nicht gestartet)

**Entscheid (Nutzer 2026-09-18, "ja nimm es so in die kette auf").** Generator der v30-Erzeugung
wird der Champion-Kandidat `v29-b07` (884 Eingaenge, 406er-Policy) mit auf 414 GEPOLSTERTEM
Policy-Kopf: acht Nullzeilen im Gewicht und acht Nullen im Bias, ohne einen Trainingsschritt.
Weil das ein anderes Artefakt ist als `v29-b07_brierbest`, bekommt es nach
`feedback_measured_identity_gets_own_bxx` einen eigenen Namen: **`v29-b10`** (reserviert in
`docs/generation_naming.md`).

**Warum ueberhaupt polstern.** Das Wheel traegt NUM_ACTIONS 414 (Mondknoten 406-410, Rueckgabe
411-413; Weg A / R3, par.12.6/12.10 in `PREREG_moon_stack_order.md`, par.12.7/12.8 in
`PREREG_dome_return_order.md`) und INPUT_SIZE 888 (R2 / P.16 `designs_ordered`). Das Tor der
neuen Suchknoten liest die Policy-Breite aus dem ONNX (`engine/src/net.rs`, `policy_width()` /
`detect_policy_width`); ein 406er-Netz faellt kanonisch zurueck, die neuen Knoten blieben also
ungenutzt und die Erzeugung ohne sie. Die Polsterung macht den Kopf 414 breit, ohne das alte
Verhalten zu aendern: nach dem maskierten log_softmax sind die acht neuen Aktionen
gleichverteilte, nicht bevorzugte Masse, und fuer die 406 alten Aktionen ist b10 exakt b07.

**Werkzeug: `tools/pad_policy_head_export.py`** (geschrieben 2026-09-18, `py_compile` gruen, NICHT
gelaufen). Laedt `models/alphazero_v29-b07_brierbest.pth` (`['model_state']`), polstert
(1) den Policy-Ausgang auf `config.NUM_ACTIONS` an dim=0, Gewicht UND Bias, und (2) den
Flach-Eingang (`flat_branch.0.weight`) auf `config.INPUT_SIZE` mit Nullspalten hinten. Beide
Bauformen sind aus `train.py` uebernommen: Eingang `train.py:1684-1702` ("Additive
Eingabe-Erweiterung"), Ausgang `train.py:1699-1729` ("Additive AUSGABE-Erweiterung des
Policy-Kopfs"). Danach baut es das Modell mit `neural_net.build_model_from_checkpoint`
(neural_net.py:2382), prueft die State-Dict STRIKT gegen das Modell (Key-Mengen und Formen; der
Lader selbst arbeitet mit `strict=False`, neural_net.py:2441, und wuerde eine vergessene
Polsterung still als zufaelligen Kopf durchlassen -- der Vorfall bei v6, `export_onnx.py:76-79`),
schreibt `models/alphazero_v29-b10.pth` und exportiert ueber `export_onnx.export`, also GENAU die
Routine, die `train.py:2704-2707` fuer jedes `_brierbest.onnx` aufruft. Damit stimmen opset (13),
Eingabenamen (`planes`, `state`) und Ausgabenreihenfolge; die `.ref.txt` schreibt dieselbe Routine
mit (`export_onnx.py:255-263`). Ausgabe: alte/neue Breiten, Pfade, sha256, `laufzeit`; Artefakt
`evaluations/artifacts/pad_policy_head_v29-b10.json`. `--dry-run` druckt nur die Formen.

**Kette: `tools/night_v30_wheel_acceptance.sh`** (`bash -n` gruen, alle sechs eingebetteten
Python-Bloecke `py_compile` gruen, NICHT gestartet). Stufen mit Zeitstempel und Exit, STOPP bei Rot:

| Stufe | Inhalt | Tor / STOPP |
| --- | --- | --- |
| 0 | `config.py` traegt `INPUT_SIZE = 888` und `NUM_ACTIONS = 414` (setzt der Koordinator), Wheel neuer als `engine/src/net_mcts.rs`, Quell-`.pth` und Spec da, `warte_frei` | ABBRUCH vor jeder Last |
| 1 | `pip install --force-reinstall --no-deps`, dann Vertrag aus `engine_config_json()` (lib.rs:753): `input_size` 888 (:768), `num_actions` 414 (:771), `contract_hash` == `6ef829e564c58bd5` (Literal lib.rs:2548-2553), `return_order_mode` vorhanden, plus `config`-Seite | STOPP 12 |
| 2 | Anker-Drift und -Konservierung, `hv4_anchor`, Leitersegment 2 | STOPP 20 / 21 |
| 3 | `tools/probes/feature_parity_rust_python.py` | STOPP nur bei LAENGENfehler (30) |
| 4 | Polsterung und Export (Werkzeug oben), dann Engine-Kontrolle: `mosaic_rust.onnx_eval` (lib.rs:653-661) auf dem neuen ONNX, `len(policy)` muss 414 sein | STOPP 40-43 |
| 5 | **Kostentor**: b10 gegen sich selbst, `models/v30_generation.spec.json` beidseits, 2 x 20 Paare (Seeds 20261260/20261261), 400 Sims, Blockgroesse 5, 10 Threads, `--log-games`. Referenz **12,0 s je Partie** (`docs/measured_runtimes.md` Zeile 187: Tor 1 b07 gegen b03 auf dem 884-Wheel, Seed 20261191, 200 Paare, 10 Threads, Logs, exklusiv), Schwelle +25 Prozent. Verdikt `evaluations/artifacts/v30_wheel_kostentor_verdikt.txt` | Riss = STOPP 3, Nutzer-Entscheid |
| 6 | **A/B gepolstert gegen ungepolstert**: A `v29-b10`, B `v29-b07_brierbest`, Spec beidseits, 400 Sims, 200 Paare, Blockgroesse 5, SPRT 0,001, Seed 20261270, `--no-promote-winner`; danach `arena_column_probe` und `plate_points_from_arena`. Artefakt `evaluations/artifacts/ab_v29-b10_vs_b07_s20261270.json` | Marge 5 pp: >= 45,0 Prozent HAELT, sonst STOPP 60 |
| 7 | **Wiedervorlage-Probe**: 20 Partien Self-Play mit dem Generator (Argumente der Sockel-Klasse aus `tools/night_v30_generate.sh`), dann Pruefung der `data/selfplay_v29-b10-probe_*.pkl` | STOPP 70 / 71 bei (a) oder (b) |

**Wie Stufe 7 die neuen Knoten nachweist (Feldnamen mit Pruefstelle).** Der Record traegt den
Zustand unter `state`, das Policy-Ziel unter `policy` als Liste von
`{"action": <Aktions-Dict>, "prob": ...}` und die Maske unter `valid_actions` als Liste von
Aktions-Dicts (Pruefstelle: die Zeilen `m.insert("state"/"policy"/"valid_actions")` in
`engine/src/self_play.rs`; kein Zeilenanker, weil die Datei am 2026-09-18 parallel bearbeitet
wird). **Ein Feld namens `policy_target` gibt es im Record NICHT** -- gemeint ist dieses `policy`;
`policy_target_valid` daneben ist ein Gueltigkeits-FLAG, nicht das Ziel. Die Aktions-ID entsteht
erst in Python aus dem Dict: `neural_net.action_to_id` (neural_net.py:976), `choose_moon_top` ->
406-410 (:1060), `choose_return_first` -> 411-413 (:1066). P.16 `designs_ordered` steckt
geschachtelt in `dome_pool_view.blocks[*]` (`serialize.rs:119/167`) und wird deshalb am JSON-Text
des Zustands gesucht, dieselbe Bauform wie `first_record_check` in
`tools/night_v30_generate.sh:68-70`. Die Probe zaehlt je ID-Bereich (406-410 Mond, 411-413
Rueckgabe, 328-354 und 355-390 Kuppel-/Stapel-Slot, 391-394 Rotation, 405 Stapel-Blick) getrennt
fuer `policy` und `valid_actions`, Grundmenge Records dieser Probe, Einheit Vorkommen.
(a) kein `designs_ordered` in irgendeinem Record oder (b) keine einzige ID >= 406 ist STOPP: dann
waere die Erzeugung nutzlos und das Merkmal fiele eine Generation zurueck
(`feedback_record_field_must_precede_generation`). (c) leere `policy` an einem neuen Knoten ist
BEFUND, kein Stopp -- der Value-Anteil bleibt gueltig.

**Lesart des A/B.** Erwartet ist Gleichstand, weil die acht Nullzeilen das alte Netz nicht
veraendern. Haelt b10 die 5-Prozentpunkte-Marge, ist er der Generator; reisst sie, ist der
gepolsterte Kopf als Generator nicht abgenommen und die Erzeugung bleibt ungestartet
(Nutzer-Entscheid).

**ANNAHME, ungeprueft:** der Kostentor-Aufschlag wird spuerbar sein, weil die Mond- und
Rueckgabeknoten ZUSAETZLICHE Suchen sind; deshalb die 25-Prozent-Schwelle statt einer engeren.
Ob und wie stark, ist offen, bis Stufe 5 gelaufen ist.

**Messdateien:** `data/selfplay_v29-b10-probe_*.pkl` aus Stufe 7 gehoeren beim Bau des
v30-Fensters in `MOSAIC_DATA_EXCLUDE` (`feedback_window_pinning_during_generation`).

**Freigabe nach gruener Kette:** `MOSAIC_V30_GENERATOR=models/alphazero_v29-b10.onnx
MOSAIC_V30_GEN_NAME=v29-b10 bash tools/night_v30_generate.sh`, aber erst nach dem
Generationswechsel (`/mosaic-generation-turnover`).

### 10.13 Champion-Kanten v29-b09 GEMESSEN (2026-09-18, 05:36-09:21), Kette 10.9, exklusiv -- und der Vergleich der Kandidaten

| Kante | b09 | b07 (10.11) |
| --- | --- | --- |
| Gating gegen v28-b02, Seed 1 / Seed 2 | 210:190 / 213:187 | 204:196 / 214:186 |
| Gating gepoolt (800 Partien) | **423:377 = 52,9 Prozent** | 418:382 = 52,3 Prozent |
| Anker hv4@150, 150 Partien | 128:21+1 = **128:22 = 85,3 Prozent**, Punkte 59,3 gegen 41,9 | 129:21 = 86,0 Prozent, Punkte 58,8 gegen 42,1 |
| Champion-2 gegen v27-b01, 150 Partien | **90:60 = 60,0 Prozent**, Punkte 54,2 gegen 50,5 | 81:69 = 54,0 Prozent, Punkte 54,5 gegen 51,6 |
| Tor 1 gegen b03 (10.10 / 18.12) | 416:384, Block-z +1,03 | 432:368, Block-z +2,40 |

Grundmenge Partien, Einheit Siege; Handshakes bewusst Cross-Aera, Golden-Selbsttest ohne Abweichung bei allen
vier Referee-Kanten. Laufzeiten: Gating 4.778 / 4.855 s, Anker 1.281 s, Champion-2 2.340 s. Die acht Elo-Zeilen
sind nach Pruefung gegen die Artefakte am 09:35 ins Register eingetragen (`tools/elo_tracker.py add`, Segment 2).
**Champion-2-Kanten von b07 und b09 teilen 149 von 150 Seeds** (Basen 20261250/20261251) und sind damit
faktisch gepaart: auf denselben Startbedingungen gegen v27-b01 gewinnt b09 90, b07 81 -- ein Hinweis, kein Tor.

**Lesart:** beide Kandidaten bestehen alle drei Aufhaengungen; gegen den Champion sind sie gleich (52,9 gegen
52,3 Prozent, beide nicht signifikant), gegen den Anker gleich, gegen v27-b01 liegt b09 vorn. Der einzige
signifikante Befund der Serie bleibt b07 gegen b03 (Block-z +2,40); b09 gegen b03 ist flach. **Empfehlung des
Koordinators: b07 als Champion** (der belegte Stärkebefund; b09s Vorsprung bei v27-b01 liegt in der
Seed-Streuung), Generator b10 = b07 mit 414er-Kopf (10.12). Gegenposition, ehrlich: b09 traegt das v30-Rezept
und ist in keiner Kante schlechter; wer den Generator mit dem Trainingsrezept gleichziehen will, nimmt b09.
Nutzer-Entscheid (Checkliste Punkte 5-7 danach).

**Leiter nach den Eintraegen (09:40, `elo_tracker.py report`, Segment 2, Block-Bootstrap):** v29-b03 1382 [1342; 1431]
(640 Partien, 3 von 4 Kanten Frueh-Stopp), **v29-b09 1366 [1329; 1408]** (1.100 Partien, unverzerrt), **v29-b07 1357
[1318; 1401]** (1.100), v28-b02 1349 [1315; 1385] (3.950), v27-b01 1308 [1272; 1344]. Alle Intervalle ueberlappen;
die Leiter trennt die beiden Kandidaten nicht.

### 10.14 Abnahme des 414/888-Wheels (2026-09-18, 09:31-09:55): Tore 1-4 gruen, KOSTENTOR GERISSEN, Kette gestoppt

Kette `tools/night_v30_wheel_acceptance.sh` (10.12). **Gruen:** Installation, Manifest-Export `input_size` 888 /
`num_actions` 414 / Vertragshash `6ef829e564c58bd5`; Anker-Drift und -Konservierung; Paritaetssonde (Flachvektor 888
in 1.033 von 1.033 Zustaenden gleich, Planes nur der Kanal-76-Altbefund); Polsterung `v29-b10` (Policy-Kopf
`policy_head.2` 406 -> 414, Eingang 884 -> 888, `models/alphazero_v29-b10.onnx`, die Engine laedt ihn mit
`policy_width` 414, Artefakt `pad_policy_head_v29-b10.json`).

**Kostentor (b10 gegen sich selbst, `v30_generation.spec.json` beidseits, 2 x 20 Paare, 400 Sims, 10 Threads):**
17,11 s je Partie (Seed 20261260, 09:33-09:44) und 15,26 s (Seed 20261261, 09:44-09:55), Mittel 16,18 s gegen die
Referenz 12,0 s (Tor 1 b07, 884-Wheel) -> **+34,9 Prozent, Schwelle +25, GERISSEN** (Exit 3, A/B und
Record-Stichprobe nicht gestartet). Vorbehalt zum ersten Seed: parallel lief 09:40-09:4x der Elo-Report mit
Block-Bootstrap (Koordinator-Nebenlast, ein Kern); der zweite Seed ist sauber und liegt mit **+27 Prozent**
ebenfalls ueber der Schwelle.

**Ursache (Herleitung am Code, keine Messung je Knoten):** mit offenem 414er-Tor entscheidet die Schleife den
Stapelzug als eigene Suchknoten (Slot, Rueckgabe, Rotation) und den Mondknoten, jeder mit vollen `base_sims`
(`net_effective_sims` entkoppelt Sims von der Aktionszahl, `net_mcts.rs:4122/4146`). In ARENEN ohne
`MOSAIC_STACK_DRAW_RESEARCH` sind Slot und Rotation damit NEUE Suchen (bei 406er-Netzen loest der Resolver in
einem Stueck); in der ERZEUGUNG (Research-Knopf an) wurden Slot und Rotation schon in v29 einzeln gesucht -- dort
kommen nur Mond- und Rueckgabeknoten hinzu. Der gemessene Aufschlag ist also die Obergrenze fuer Arenen, nicht die
Erwartung fuer die Erzeugung (ungemessen; die 20-Partien-Stichprobe der Kette wuerde sie liefern).

**Nutzer-Entscheid (STATUS Abschnitt 6 Punkt 24).**

### 10.15 ENTSCHIEDEN (Nutzer 2026-09-18, 10:05): "Weiter mit a und b09"

1. **Champion = `v29-b09`** (10.10, 10.13: Tor 1 gegen b03 416:384, Gating 423:377, Anker 128:22, Champion-2 90:60;
   Leiter 1366 [1329; 1408]). Promotion nach Checkliste Punkte 5-7 im Generationswechsel; b07 bleibt gemessener
   Arm mit dem signifikanten Einzelbefund gegen b03 (18.12).
2. **Kostentor-Riss hingenommen (Weg a aus 10.14)**; Budget-Knopf fuer die Hilfsknoten als Wiedervorlage v31.
3. **Generator = `v29-b11`** = b09 gepolstert (Policy 406 -> 414, Eingang 884 -> 888), Kette
   `tools/night_v30_acceptance_b11.sh` mit `SKIP_WHEEL_GATES=1`: Polsterung, Engine-Kontrolle (policy_width 414),
   A/B b11 gegen b09 (200 Paare, Seed 20261271, Marge 5 Prozentpunkte), Record-Stichprobe 20 Partien (Seed
   20260928, `designs_ordered`, IDs >= 406, `policy`-Eintraege). Das Kostentor aus 10.14 gilt architekturgleich
   (ANNAHME, b10 und b11 sind dieselbe Netzform). Danach `/mosaic-generation-turnover` und
   `MOSAIC_V30_GENERATOR=models/alphazero_v29-b11.onnx MOSAIC_V30_GEN_NAME=v29-b11 bash tools/night_v30_generate.sh`.

### 10.16 Promotions-Kette v29-b09 (geschrieben 2026-09-18, nicht gestartet)

Auftrag: 10.15 Punkt 1 (Nutzer 2026-09-18, 10:05, "Weiter mit a und b09"). Kette
`tools/night_v29_b09_promotion.sh`, `bash -n` gruen, NICHT gestartet. Sie arbeitet die noch
OFFENEN Punkte von `docs/promotion_checklist.md` ab; die drei Elo-Kanten (Punkte 2, 3, 4) sind
durch und in 10.13 registriert und fehlen hier bewusst.

**Vorlage.** `tools/night_v28_freeze.sh` und `tools/night_v28_promotion.sh` (Promotion v28-b02 am
2026-09-12, 03:48-06:45). Beide Skripte sind im Aufraeumen `3688817b` geloescht worden und wurden
fuer diese Kette aus der Historie gelesen; ihre Aufrufe von `set_champion`, `cargo test`,
`cp`/`venv`/`pip`, `build_frozen_golden_probe`, `frozen_referee_match`, `platt_fit` und
`gumbel_scale_calibration` sind 1:1 uebernommen, nur mit neuem Namen. Belegstellen zur
Reihenfolge und zu den Zahlen des damaligen Laufs: `archive/history.md` Z. ~18218-18232 und
`PREREG_code_cleanup_closeout.md` Abschnitt "Pflicht-Diagnostiken (Schritte 5b/5c)".

**Stufe 0 Vorbedingungen und Warten.** Modell `.onnx`/`.pth`, Trainings-Manifest, Live-Wheel,
Vorlage-Artefakt `models/frozen_champions/v28-b02` samt `venv/`, die fuenf Werkzeuge, beide
Zustandssaetze; `models/frozen_champions/v29-b09/` darf NICHT existieren (ein gemessenes Artefakt
wird nie ueberschrieben). Dann die gehaertete Warteschleife aus `tools/night_k6_w025_ab.sh:27`
(Namensbedingung auf `python`, dazu `cargo`/`rustc`), Poll 120 s mit Meldung je Poll,
`MOSAIC_CHAIN_NO_WAIT=1` ueberspringt sie. Die Schleife ist hier nicht nur wegen der Messungen
noetig: Stufe 4 ist ein `cargo`-Bau und damit Volllast ueber viele Kerne.

**Stufe 1, Punkt 1.** `python -X utf8 tools/set_champion.py v29-b09_brierbest`. Argumentform am
Werkzeug geprueft: ein positionales `name` OHNE `alphazero_`-Praefix und `.onnx`-Suffix, das
Werkzeug validiert die Existenz von `models/alphazero_<name>.onnx` (`tools/set_champion.py:28-34,
47-50`). Die SPEC setzt `set_champion.py` NICHT (es schreibt nur `models/champion.txt`, Z. 40).
Auffindbar wird sie durch Stufe 5: `server.py::_resolve_champion_spec` streift `_brierbest` ab und
findet `models/frozen_champions/v29-b09/spec.json` (`server.py:257-266`). Die Kette druckt beide
Kandidatenpfade und den ausdruecklichen Hinweis, dass zwischen Stufe 1 und Stufe 5 KEIN
Server-Neustart fallen darf: in diesem Fenster gibt es keine Spec, und der Server kehrte still zu
Env-Defaults zurueck (Vorfall v25-b01 bis v27-b01, Checkliste Punkt 1).

**Stufe 2, Punkt 5b (Platt).** Zwei Fits auf `models/alphazero_v29-b09_brierbest.pth`:
`--eval-set evaluations/frozen_eval_set_v3.pkl` (Anzeige) und `evaluations/frozen_eval_set.pkl`
(Trend), Artefakte `platt_fit_v29-b09_v3.json` und `platt_fit_v29-b09.json` -- dieselbe Form wie
bei v28-b02. **Zum Verteilungs-Caveat:** `tools/platt_fit.py` kennt als Quelle NUR `--eval-set`
(`tools/platt_fit.py:39`), einen Schalter auf frische Partien gibt es nicht; vorhanden sind
`frozen_eval_set.pkl` (v12-Aera), `_v2` und `_v3` (b01-Aera, 1.800 Zustaende, 360 je Runde,
`PREREG_frozen_v3_eval_set.md:129`), `data/holdout/` existiert NICHT (geprueft 2026-09-18). Dass
`_v3` fuer die v29-Aera "zeitgemaess" ist, ist damit eine ANNAHME und kein Beleg; ein
v29-Zustandssatz ist offen. Die Kette DRUCKT A, B und Brier beider Fits samt der beiden Zeilen
`_DISPLAY_CAL_A/_B` und traegt sie NICHT in `server.py` ein (Koordinator).

**Stufe 3, Punkt 5c (sigma/Prior).** `tools/gumbel_scale_calibration.py --model v29-b09_brierbest
--sims 400 --n-states 300 --out evaluations/artifacts/gumbel_scale_calibration_v29-b09.json`.
**Argumentform korrigiert gegenueber dem Auftrag:** `--model` nimmt einen NAMEN, keinen Pfad; das
Werkzeug baut `models/alphazero_<name>.onnx` selbst (`tools/gumbel_scale_calibration.py:85` und
`:98`). Einen `--eval-set`-Schalter gibt es nicht, Zustandssatz und Orakel-Labels sind fest
verdrahtet (Z. 65/66). Die Kette druckt die Kennzahl, die Vergleichswerte (v28-b02 2,222,
v27-b01 2,161, v26-b01 2,270) und die Regel als Zeile: ueber 3 oeffnet sich die
`c_visit/c_scale`-Familie per Regel, kein Ermessen.

**Stufe 4, Punkt 5d (Paritaets-Fixture).** Erst Schreiblauf mit
`MOSAIC_UPDATE_NET_PARITY_FIXTURE=1`, dann derselbe Test in einem frischen Prozess ohne die
Variable; rot heisst STOPP. `--lib` ist richtig: der Test liegt in der Bibliothek
(`engine/src/self_play.rs:8848`), nicht unter `engine/tests/`. Der PATH bekommt vorher das
Python-Verzeichnis (sonst `STATUS_DLL_NOT_FOUND`, CLAUDE.md). Die Stufe steht NACH Stufe 1, weil
die Fixture `models/champion.txt` folgt.

**Stufe 5, Punkt 7 (Artefakt).** `model.onnx`, `model.pth`, `spec.json` als Kopie der
Champion-Spec `models/frozen_champions/v28-b02/spec.json` mit einem Feld-fuer-Feld-Vergleich als
Tor (b09 IST mit dieser Spec gemessen: `tools/night_champion_edges_v29.sh:96`,
`tools/night_v29_b09_v30_recipe.sh:89`), Wheel-Kopie, `wheel.sha256`, Live-Beleg aus
`direct_url.json`, venv, Vorab-Manifest, Golden Probe (`--seed-base 916001`), Referee-Selbsttest
mit 2 Echtpartien. Das Manifest traegt die zwei Pflichtfelder `name_dialect: "hv"` und
`worker_python.interpreter_relative` (ohne sie scheitert der Referee ohne Befund, Vorfall
2026-09-04). `numpy` und `onnxruntime` werden nachinstalliert, weil die Vorlage-venv beide traegt
(nachgesehen in `models/frozen_champions/v28-b02/venv/Lib/site-packages`).

*Eine bewusste Abweichung von der v28-Vorlage:* die Wheel-Kopie im Artefakt traegt den
KANONISCHEN Dateinamen `mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl` (v28:
`mosaic_rust_knobs_20260912.whl`), und die venv wird AUS DIESER KOPIE installiert statt aus
`engine/target/wheels/`. Grund steht in der Checkliste selbst (Punkt 7: pip lehnt umbenannte
Wheel-Dateinamen ab, also Kopie unter kanonischem Namen installieren); dazu haengt das Artefakt
sonst an einem Pfad, den der naechste Wheel-Bau ueberschreibt.

*Netzbreite gegen Motorbreite, benannt statt verschwiegen:* b09 ist 884 Eingaenge / 406 Aktionen
(`models/manifest_train_v29-b09_20260917_200920.json`, `engine_config.input_size`/`num_actions`;
Kontrakt zur Trainingszeit `cfd94509f0aab102`), das installierte Wheel vom 2026-09-18, 09:30 ist
888/414 (`config.py:49`/`:57`). Das Manifest fuehrt beide Paare getrennt, und `contract_hash` ist
der des LEBENDEN Wheels: gegen ihn prueft der Handshake
(`tools/frozen_referee_match.py:144-155`), und Artefakt-Wheel und Live-Wheel sind hier dasselbe
(sha256 `da24f156eda89563...`, gelesen 2026-09-18). Ein `--force-cross-era` ist deshalb NICHT
noetig.

**Stufe 6.** Die Kette druckt die faelligen Registrierungen: `server.py`-Eintrag, STATUS-
Champion-Zeile, history-Kapitel, Promotions-Absatz hier samt Zeile-1-Kopf und
`generate_prereg_index.py`, Vervollstaendigung des Manifests nach dem Feldbild von v28-b02,
Laufzeiten nach `docs/measured_runtimes.md` -- und den UNGEKLAERTEN Punkt (siehe unten). Danach
eine Gegenprobe, die `server.py:257-266` nachbildet und zeigt, dass die Champion-Spec jetzt
gefunden wird.

**Kosten (Planung).** Platt 12 s + 9 s, sigma/Prior 787 s
(`docs/measured_runtimes.md:206`, je v28-b02); venv 24 s, Golden Probe **1.450 s** einkernig @400,
Referee-Selbsttest 78 s (`docs/measured_runtimes.md:211`; die Checkliste nennt "rund 22 min" fuer
die Golden Probe, gemessen sind 24 min). Stufe 4 ist in keiner Zeile der Kostentabelle eigens
ausgewiesen: ANNAHME 10-25 min fuer die zwei `cargo`-Laeufe, davon der Grossteil Bauzeit.
Summe ANNAHME rund 50-70 min Wanduhr, exklusiv. Alle gemessenen Zahlen stammen vom 755er Modell
auf dem damaligen Wheel; dass 884/888 sie nicht verschiebt, ist ANNAHME.

**OFFEN, nicht still weggelassen: die #29-Buchfuehrung** (Checkliste Punkt 5). Eine Datei dieses
Namens gibt es im Baum NICHT; gegreppt ueber `evaluations/` und `docs/` am 2026-09-18 finden sich
nur VERWEISE (`docs/promotion_checklist.md:55`, `PREREG_lambda_wdl_arm.md:46`,
`PREREG_t35b_ranking.md:26`, `PREREG_task_d_weights.md:106/112/132/163`). Die Frage selbst ist
Task #29 und liegt in `evaluations/PREREG_value_rank_metric.md` (Zeile 1: ENTSCHIEDEN, die
Rangmetrik ist NICHT validiert). ANNAHME: gemeint ist, die Offline-Kennzahlen des Siegers dort
oder in der Fenster-Prereg festzuhalten, damit spaeter eine echte Vorhersage geprueft werden
kann. Wohin, ist ein Nutzer-Entscheid; die Kette druckt den Punkt samt dieser Lage.

### 10.17 A/B v29-b11 gegen v29-b09 und Record-Stichprobe GEMESSEN (2026-09-18, 12:22-13:49): der Generator steht

**A/B (Kette `tools/night_v30_acceptance_b11.sh`, `SKIP_WHEEL_GATES=1`):** `v29-b11` (b09 mit 414er-Kopf, offenes Tor:
Mond-, Rueckgabe-, Slot- und Rotationsknoten als eigene Suchen mit Gleichverteilungs-Prior) gegen
`v29-b09_brierbest` (406er-Kopf: Aufloeser in einem Stueck, `return_order_mode 1`, kanonische Mondreihenfolge),
beide mit `models/v30_generation.spec.json`, 400 Sims, Blockgroesse 5, Seed 20261271, 10 Threads, exklusiv.
**SPRT hat H1 bei 175 Paaren angenommen** (LLR ueber +6,91).

| Groesse | Wert |
| --- | --- |
| Siege b11 : b09 | **212 : 138 von 350 = 60,6 Prozent** |
| Sweeps b11 / b09 | 63 / 26; McNemar p 0,00011 |
| **Block-Ebene** | 35 Bloecke, **z = +3,94** |
| eigene Punkte b11 / b09 | 57,38 / 53,34 (**+4,0**) |
| Laufzeit | 5.040,5 s, 14,4 s je Partie (b11-Seite traegt die Zusatzsuchen) |

**Lesart, mit dem Konfundierer vorneweg:** dasselbe Netz, dieselben Gewichte fuer alle 406 alten Aktionen -- der
Unterschied ist allein, dass die Suche den Stapelzug (Slot, Rueckgabe, Rotation) und die Mondreihenfolge als eigene
Knoten entscheidet. Das kostet +35 Prozent Wanduhr (10.14), also ist der Gewinn zum Teil mehr Rechnung je Partie;
wie viel davon "mehr Suche" und wie viel "bessere Entscheidung" ist, trennt dieser Aufbau nicht (ein Kontroll-A/B
b09 @540 Sims gegen b09 @400 waere die Trennung; nicht gefahren, v30+-Regel). Fuer die Erzeugung ist das ohne
Belang: der Generator spielt so, wie der Korpus es tragen soll. **Marge haelt weit, b11 ist der Generator.**
Nebenbefund fuer STATUS Punkt 19: die neuen Knoten sind kein reiner Korrektheitsentscheid mehr, sie tragen
gemessen Staerke -- der bisher groesste Einzeleffekt der Kampagne, wenn auch konfundiert mit Rechenzeit.

**Record-Stichprobe (Self-Play 20 Partien @100, `v29-b11-probe`, Seed 20260928, 3.941 Records, 79,6 s = 3,98 s je
Partie gegen 3,18 in der v28-Erzeugung = +25 Prozent, `manifest_v29-b11-probe_20260918_134726.json`):** die
Kette brach an der Auswertung ab (`pickle.load` auf gzip-Dateien, Exit 1 -- Werkzeugfehler, nicht Befund); der
Koordinator hat die Pruefung mit `gzip.open` nachgeholt (Grundmenge Records, Einheit Vorkommen in
`valid_actions` / `policy`, IDs ueber `neural_net.action_to_id`):

| Pruefpunkt | Ergebnis |
| --- | --- |
| P.16 `designs_ordered` im Zustand | 792 von 3.941 Records (nur wo ein eigener Block liegt) -- **vorhanden** |
| Mondknoten 406-410 | 1.035 in `valid_actions`, **905 in `policy`** |
| Rueckgabeknoten 411-413 | 20 / **20** (selten, wie 12.5 erwartet: rund 0,5 je Partie und Seite) |
| Slot 328-390 / Rotation 391-394 / Peek 405 | 15.172 / 1.280 (policy 1.280) / 1.271 |
| Records mit neuem Knoten (>= 406) | 479, **alle 479 mit nicht-leerer `policy`** |

**Wiedervorlage aus STATUS Punkt 21 damit GRUEN:** der v30-Korpus wird die Knoten mit Lernziel tragen. Die
Probe-Dateien `data/selfplay_v29-b11-probe_*.pkl` sind Messdateien (MOSAIC_DATA_EXCLUDE beim Fensterbau).
**Freigabe fuer `MOSAIC_V30_GENERATOR=models/alphazero_v29-b11.onnx MOSAIC_V30_GEN_NAME=v29-b11 bash
tools/night_v30_generate.sh` nach dem Generationswechsel.** Erwartete Erzeugungskosten aus der Probe: rund
+25 Prozent gegen v28 (ANNAHME aus 20 Partien), also rund 12,5 h fuer 3 x 4.000.

### 10.18 Promotion v29-b09 DURCH (2026-09-18, 13:54-14:32, Kette 10.16, dritter Anlauf)

Zwei Anlaeufe scheiterten am Python-Lader nach dem Kontraktwechsel (Policy-Breite aus config statt Checkpoint;
Zwilling ohne Eingangs-Schnitt) -- beides behoben (`neural_net.py`, `docs/pitfalls.md`), 141 Python-Tests gruen.

| Checkliste | Ergebnis |
| --- | --- |
| 1 `set_champion.py` | `models/champion.txt` = `v29-b09_brierbest` |
| 5b Platt-Fit (frozen_v3 = Anzeige) | **A -0,0513 / B 0,6488**, Brier 0,255 (v28-b02: -0,0539 / 0,6684 / 0,225); Trend frozen_v1 A 0,384 / B 0,607; in `server.py` eingetragen |
| 5c sigma/Prior-Balance (400 Sims, 300 Zustaende) | Median **1,83**, IQR [0,66; 5,91], Mittel 11,9 -- unter 3, die c_visit/c_scale-Familie bleibt geschlossen |
| 5d Netz-Paritaets-Fixture | neu `01e627ef5e520619` (3 Partien, 8 Sims), frischer Prozess gruen |
| 7 Artefakt `models/frozen_champions/v29-b09/` | model.onnx/.pth, spec.json (= Champion-Spec), Wheel 414/888 (sha256 `da24f156eda89563...`, identisch mit dem Live-Wheel laut `direct_url.json`), manifest.json, venv, Golden-Probe (22 min, Seed-Basis 916001), Referee-Selbsttest: Handshake ok (`6ef829e564c58bd5` beidseits), Golden 10/10, zwei Echtpartien |
| Laufzeit gesamt | 13:54:47 bis 14:32:29 = 38 min |

Merkposten: der Champion spielt mit 406er-Policy auf dem 414er-Wheel kanonisch (kein neuer Knoten); die Kanten
der Leiter sind damit weiter vergleichbar. Die #29-Buchfuehrung (Offline-Kennzahlen des Siegers) hat keine
Datei; die Kennzahlen stehen hier und in 10.10 (val_brier 0,1785, Val-R2 0,550).
