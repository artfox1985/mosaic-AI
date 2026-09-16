<!-- STATUS: OFFEN | Frage: Kann ein kleinerer Standardkern aus Netz, Suche und Konfiguration mindestens gleich stark werden wie das heutige v29-Rezept, und welche Teile duerfen deshalb entfallen? | Beleg: Neu angelegt 2026-09-15; kein Bau und keine Messung. Die vier Stränge und ihre Tore stehen in par.2-5. -->

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
