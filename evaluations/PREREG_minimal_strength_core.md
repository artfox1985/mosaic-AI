<!-- STATUS: OFFEN | Frage: Kann ein kleinerer Standardkern aus Netz, Suche und Konfiguration mindestens gleich stark werden wie das heutige v29-Rezept, und welche Teile duerfen deshalb entfallen? | Beleg: par.10 Marge 5 pp. b06 UNTERLEGEN (10.3: 44,5 Prozent, Block-z -2,86). Zweierpaket b08 (ownership 0, ohne endgame) HAELT (10.6: 405:395 von 800, Block-z +0,33). **ENTSCHIEDEN 2026-09-17: v30-Rezept ohne endgame-Kopf, ownership-Loss 0, opp_points bleibt (Traeger per Differenz).** Strang A abgeschlossen, Strang B/C erledigt. -->

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
