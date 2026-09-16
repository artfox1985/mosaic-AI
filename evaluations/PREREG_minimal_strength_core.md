<!-- STATUS: OFFEN | Frage: Kann ein kleinerer Standardkern aus Netz, Suche und Konfiguration mindestens gleich stark werden wie das heutige v29-Rezept, und welche Teile duerfen deshalb entfallen? | Beleg: Angelegt 2026-09-15, Review par.8. **ENTSCHIEDEN 2026-09-16 (par.10): Nichtunterlegenheitsmarge 5 Prozentpunkte (gepoolt ueber 800 Partien, kein Seed signifikant dagegen); Minimalkern-Arm v29-b06 (b03 ohne moon/ownership/opp_points/endgame) NACH Variante B als Fahrplan 36a, Bezug b03.** Strang B Trace vor Bau, Strang D Abschlussarbeit. Kein Bau, keine Messung bisher. -->

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
laeuft heute Nacht gegen b03. Bezugspunkt beider Arme ist b03, nicht "b04 gegen b05".

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
