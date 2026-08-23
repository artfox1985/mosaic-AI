<!-- STATUS: OFFEN | Frage: Wird die Engine von prozessglobalem Zustand geloest (AgentSpec je Seite: Modell + Such-/Blattwert-Konfiguration), sodass ein eingefrorener Champion samt Verhalten sauber gegen ein anderes Konstrukt im selben Prozess messbar ist? | Beleg: Welle 1 (SearchConfig-Geruest + Pilot-Migration MOSAIC_IMPLICIT_MINIMAX_A) GEBAUT UND ABGENOMMEN 2026-08-23 (par.4a: Suite 498/0/26, Paritaets-Hash 8c6684ff.. haelt, Spec==Env-Default bestaetigt, per-Seite-Wirkung nachgewiesen); Koordinator-Nachpruefung + Instrument-Erweiterung par.4b (Spec-Durchleitung in paired_arena_env_ab, Wirk-/Identitaets-Smoke bestanden); Pilot-Messung ENTSCHIEDEN (par.6b): Netz-gegen-Netz PARITAET (400/814), k1-Effekt der Heuristik-Messung uebertraegt sich NICHT (9,6 % beidseitig) -- Knopf bleibt Self-Play-Kandidat mit gedaempfter Erwartung; weitere Knopf-Wellen offen; Welle 3 (gefrorene Champions als eigene Engine-Prozesse, Handshake + Golden-Selbsttest, par.8) FREIGEGEBEN, Bau nach der Pilot-Messung, erstes Ziel v21 -- Frage bleibt OFFEN. -->

# PREREG-SKELETT: Agenten-Kapselung (AgentSpec statt Prozess-Global)

Stand **2026-08-23: Welle 1 (Pilot) GEBAUT UND ABGENOMMEN, siehe par.4a.**
par.1 und par.2 sind gepruefte Bestandsaufnahme (Fundstellen genannt); par.3/
par.4 beschreiben weiterhin das Zielbild/die Migrationsstrategie in
Plan-Zeitform (was noch kommen WUERDE, weitere Wellen); par.4a haelt fest,
was von Welle 1 tatsaechlich gebaut ist (Gebaut-Zeitform, geprueft).

## par.1 Anlass: drei bezahlte Kosten der Prozessglobalitaet

1. Der R5-Loeser war mit dem Heuristik-Anker geteilt; die Trennung erforderte
   eine Modul-Kopie (`round5_anchor.rs`, `PREREG_r5_solver_split.md` par.2c,
   abgenommen 2026-08-23).
2. `MOSAIC_IMPLICIT_MINIMAX_A` kann NICHT Netz-gegen-Netz gemessen werden:
   prozessweiter OnceLock, beide Seiten saehen den Knopf
   (`PREREG_implicit_minimax_backup.md` par.2b, Einordnungs-Caveat) --
   ausgerechnet beim ersten Such-Hebel mit Erfolgs-Verdikt (k1 +7,0 pp,
   Score-Block-t +3,83 gegen Heuristik).
3. Elo-Leiter-Reset nach dem round5-Minfix: eine Verhaltensaenderung hat den
   Anker mitverschoben (`PREREG_round5_minfix_elo_reset.md`).

Instrument-Behelf heute: Subprozess-je-Arm
(`tools/paired_arena_env_ab.py:6-13`, Worker mit `env=` je Arm) -- funktioniert,
erzwingt aber die Heuristik als Gegner fuer saubere Attribution.

## par.2 Kartierung (2026-08-23, Fundstellen verifiziert)

- Knopf-Registry: ~79 Eintraege (47 Aktiv, 23 Diagnose, 7 Tot, 1 Geplant;
  `engine/src/knob_registry.rs`), 9 Themenbloecke. OnceLock-Statics je Datei:
  `net_mcts.rs` 32 (Hotspot), `tiling_solver.rs` 6, `self_play.rs` 5,
  `net_ort.rs` 5, `net_batcher.rs` 5, `column_build.rs` 5, `round5.rs` 3,
  `provocation.rs` 3, uebrige <= 2.
- Pro Seite uebergebbar heute: nur Modellpfad/Sims/c_puct
  (`net_arena_match` lib.rs:238, `net_vs_net_arena_match` lib.rs:271,
  `_hybrid` lib.rs:308 zusaetzlich `hybrid_policy`/`hybrid_value`). ALLE
  Knoepfe wirken global auf beide Seiten.
- Verhaltenswirksame Konstanten ohne Env (Auswahl, gehoerten in ein Spec):
  `USE_GUMBEL_SEARCH` (net_mcts.rs:3002), `GUMBEL_C_SCALE` (:2860),
  `GUMBEL_C_VISIT` (:2830), `GUMBEL_TOP_M` (:2873), `DEFAULT_C_PUCT` (:45),
  `DECOUPLE_NET_SIMS_FROM_ACTIONS` (:3021),
  `DETERMINIZE_ROOT_HIDDEN_INFO` (:628), `NUM_DETERMINIZATIONS` (:728),
  `DIRICHLET_EPS`/`DIRICHLET_ALPHA` (:47f). Encoding-/Kontrakt-Konstanten
  bleiben global: `NUM_ACTIONS`, `INPUT_SIZE` (features.rs:18),
  `POLICY_MASS_CUTOFF` (:55).
- Natuerlicher Andockpunkt: `NetArenaAgent` (self_play.rs:1345) /
  `NetSelfPlayAgent` (:1385) / `PlayerLoopConfig` (:1468) sind BEREITS
  pro-Seite instanziierte Objekte (Netz+Sims+c_puct), tragen aber keine
  Knopfwerte.
- Aufrufkette Partie-Einstieg -> `gumbel_select_child`: 10 Signatur-Ebenen
  (lib.rs:238 -> self_play.rs:2366 -> :2281 -> :1542 -> :1352 ->
  net_mcts.rs:4865 -> :4679 -> :4259 -> :4281 -> :3335); Ebenen 3-6 tragen
  schon ein Pro-Seite-Objekt.
- Duplikations-Praezedenzfall: `round5.rs` vs `round5_anchor.rs`
  (vollstaendige Modul-Kopie).

## par.3 Zielbild (Plan, nichts gebaut)

Eine `AgentSpec` wuerde Modell + Such-/Blattwert-Konfiguration
(migrierte Knopfwerte + parametrisierte Konstanten) buendeln, pro Seite
instanziiert, angedockt am bestehenden `NetArenaAgent`/`PlayerLoopConfig`-Pfad.
Champion-Freeze wuerde eine versionierte Spec-Datei bedeuten (Format/Ablage =
Nutzer-Entscheid, par.6) plus, wo noetig, eingefrorene Code-Pfade
(`round5_anchor`-Vorbild). Der Heuristik-Anker bliebe spec-frei und
eingefroren (er ist der Elo-Nullpunkt; Vorschlags-Default, Nutzer-Entscheid).

## par.4 Migrationsstrategie (Plan: additiv, kein Big Bang)

1. Schritt 0 wuerde eine `SearchConfig`-Struct anlegen, deren Felder mit
   Defaults AUS den heutigen Env-Knoepfen befuellt wuerden (ein Konstruktor
   `from_env()`); sie wuerde durch die 10-Ebenen-Kette gereicht. Tag 1
   muesste byte-identisch bleiben (Paritaets-Hash-Gate 8c6684ff + Suite, wie
   bei der R5-Trennung).
2. Die Knopf-Migration wuerde knopf-fuer-knopf laufen, je ein Commit
   (Lesestelle global -> Config-Feld), je Migration ein Paritaets-Gate.
   Reihenfolge: zuerst der Block Suche/Blattwert (Hotspot net_mcts.rs), nur
   Status "Aktiv"; Diagnose-/Tot-Knoepfe blieben global.
3. Die Python-API wuerde additiv erweitert: `net_vs_net_arena_match` bekaeme
   optionale per-Seite-Spec-Parameter (JSON/Dict); bestehende Signaturen und
   das Subprozess-je-Arm-Instrument blieben funktionsfaehig.
4. PILOT: `MOSAIC_IMPLICIT_MINIMAX_A` waere der erste migrierte Knopf --
   unmittelbarer Messnutzen: Champion(Spec eingefroren) gegen
   Champion+alpha0,2 NETZ-GEGEN-NETZ im selben Prozess auf den 407 Seeds;
   das waere exakt die Messung, die par.2b der Minimax-Prereg heute nicht
   liefern kann.

## par.4a Welle 1: GEBAUT UND ABGENOMMEN (2026-08-23)

Schritt 0 + Schritt 3 + der Pilot (Schritt 4) sind gebaut, alle Abnahme-Gates
(par.5) gruen. Schritt 2 (Knopf-fuer-Knopf-Migration weiterer Bloecke) bleibt
offen fuer eine spaetere Welle (Nutzer-Entscheid par.6a: "Welle 1 = NUR der
Pilot").

- **`SearchConfig`** liegt in `engine/src/net_mcts.rs` (Modul-Kohaesion mit
  dem bisherigen OnceLock-Getter, keine kleinen Configs woanders im Repo
  ausgelagert -- Repo-Idiom siehe `PlayerLoopConfig`/`GameLoopConfig` in
  `self_play.rs`, jeweils im Modul ihrer Nutzung). Traegt Welle 1 GENAU
  `implicit_minimax_alpha: f64`. `SearchConfig::from_env()` liest
  `MOSAIC_IMPLICIT_MINIMAX_A` bei JEDEM Aufruf frisch (kein OnceLock-Cache
  mehr) -- der alte Getter cachte den Wert PROZESSWEIT, genau das war
  Anlass 2 (par.1); `from_env()` wird je Partie-Einstieg einmal aufgerufen
  (Konstruktion von `NetArenaAgent`/`NetSelfPlayAgent`), kein Hot-Path-Kosten.
  `SearchConfig::from_spec_file()` parst `models/<name>.spec.json`
  (`{"implicit_minimax_alpha": <Zahl>}`), unbekannte/fehlende Felder sind
  ein harter Fehler.
- **Kette durchgereicht**: `SearchConfig` haengt jetzt an `NetArenaAgent`/
  `NetSelfPlayAgent` (je ein Feld, `self_play.rs`) und wird explizit
  durchgereicht bis zur einzigen Lesestelle `gumbel_select_child`
  (`net_mcts.rs`) -- `implicit_minimax_alpha()` (der alte OnceLock-Getter)
  ist ENTFERNT, 0 Lesestellen im Suchpfad (Grep-Beleg im Abnahmebericht).
  Diagnose-/Debug-Pfade ausserhalb der drei Ziel-Pyfunktionen
  (`net_search_with_tree` fuer die Server-Debug-UI, die Stufe-3-/
  Hybrid-Diagnosewerkzeuge in `self_play.rs`) rufen `SearchConfig::from_env()`
  weiterhin lokal auf -- bewusst AUSSERHALB des Welle-1-Scopes gehalten,
  byte-identisches Bestandsverhalten.
- **Python-API**: `net_arena_match`/`net_vs_net_arena_match`/
  `net_self_play_games` (`lib.rs`) haben je ein optionales
  `spec`/`spec_a`+`spec_b`-Argument (Pfad zur Spec-Datei); `None` =
  `SearchConfig::from_env()`. Der Heuristik-Anker bleibt spec-frei
  (par.6a Entscheid 3).
- **Abnahme gruen**: `cargo test --lib` 498 bestanden/0 fehlgeschlagen/26
  ignoriert (inkl. der neuen Kronzeugen-Tests, u.a.
  `search_config_with_different_alpha_in_same_process_yields_different_selection`);
  Paritaets-Hash haelt exakt bei `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`;
  Mini-Smoke bestaetigt `spec_a=spec_b=None` byte-identisch zu
  `models/champion_frozen.spec.json` (`{"implicit_minimax_alpha": 0.0}`) auf
  beiden Seiten, gleiche Seeds; eine Gegenprobe mit `alpha=0,2` auf einer
  Seite aendert das Ergebnis nachweislich (Wirkung kommt tatsaechlich an).
- **Referenz-Spec-Datei** `models/champion_frozen.spec.json` angelegt
  (`{"implicit_minimax_alpha": 0.0}`, das eingefrorene Champion-Verhalten).

Die eigentliche Alpha-Sweep-Messung (par.6a, Vorab-Lesart) ist damit
instrumentell moeglich, aber NOCH NICHT gelaufen -- das bleibt ein separater
naechster Schritt.

### par.4b KOORDINATOR-NACHPRUEFUNG + MESS-INSTRUMENT (2026-08-23)

- Welle-1-Abnahme nachgeprueft: alle 6 search_config-Tests einzeln
  nachgefahren (inkl. Kronzeuge "zwei Alphas im selben Prozess"),
  Alt-Getter hat 0 Aufrufstellen (Grep: nur noch eine
  Doc-Kommentar-Nennung), Paritaets-Hash 8c6684ff unabhaengig
  nachgemessen, Spec-Signaturen an lib.rs:299ff verifiziert.
- Spec-Durchleitung im Arena-Instrument ergaenzt (Koordinator,
  chirurgisch): `--spec-a`/`--spec-b` in tools/paired_arena_env_ab.py
  und tools/paired_arena_arm_worker.py (nur Netz-gegen-Netz-Modus,
  Guard gegen Nutzung ohne --model-b; Artefakt-JSON traegt beide
  Spec-Pfade).
- Wirk-/Identitaets-Smoke (4 Partien, Seed 900001, 100 Sims):
  frozen/frozen == None/None IDENTISCH (Spec-Pfad = Default-Pfad);
  frozen/0,2 weicht ab (Verdrahtung wirkt end-to-end).
  Artefakte paired_arena_env_spec_smoke{,_frozen,_none}.json.
- Zweite Spec-Datei `models/champion_imm_a02.spec.json`
  ({"implicit_minimax_alpha": 0.2}).
- **Pilot-Messung nach par.6a-Lesart GESTARTET** (2026-08-23):
  Netz-gegen-Netz auf den 407 Kampagnen-Seeds, alpha-Arm auf Brett 0
  gegen frozen (Lauf 1) und getauscht (Lauf 2), 400/400 Sims,
  --log-games; Logs `logs/arena_imm_netvnet{,_swap}_20260823.log`.

## par.5 Abnahme-Gates (Plan, je Migrationsschritt)

Suite muesste gruen bleiben; der Paritaets-Hash muesste halten;
Default-Spec muesste == Env-Stand byte-identisch sein; das Wheel muesste vor
jeder Messung neu gebaut werden; Kalibrierungs-/Golden-Muster wie im Repo
etabliert muessten weiter greifen.

## par.6 OFFENE NUTZER-ENTSCHEIDE (vor Baubeginn)

1. Umfang Welle 1: nur Pilot-Knopf, oder ganzer Block Suche/Blattwert
   (32 Statics)?
2. Spec-Format und Ablage (Vorschlag: JSON neben dem Modell,
   `models/<name>.spec.json`).
3. Heuristik-Anker: spec-frei eingefroren lassen (Vorschlag) oder
   mitwandern?
4. Zeitpunkt gegenueber Alpha-Sweep/Self-Play-Einsatz des Minimax-Knopfs.

### par.6a NUTZER-ENTSCHEIDE GEFALLEN (2026-08-23)

1. **Welle 1 = NUR der Pilot**: SearchConfig-Geruest + Migration von
   `MOSAIC_IMPLICIT_MINIMAX_A`; die uebrigen Knoepfe folgen erst nach
   validiertem Geruest ("mach das").
2. **Spec-Format bestaetigt**: `models/<name>.spec.json` neben dem
   Modell.
3. **Heuristik-Anker bleibt spec-frei und eingefroren** ("kannst so
   lassen").
4. Reihenfolge damit implizit: Pilot zuerst; der Alpha-Sweep bekommt
   danach das bessere Instrument (Netz-gegen-Netz im selben Prozess).

**Vorab-Lesart der Pilot-Messung (VOR dem Lauf registriert):**
Champion (Spec eingefroren, alpha=0) gegen Champion+alpha=0,2,
Netz-gegen-Netz auf den 407 Kampagnen-Seeds, Brettwechsel-Pflicht,
--log-games. Ausgewiesen: Siege (Block-Ebene a 25) UND k1-Raten
(par.14-Instrument). Lesarten: signifikanter Sieg-Vorteil des
alpha-Arms = Gating-relevanter Befund (naechster Schritt dann
Nutzer-Entscheid); Paritaet ohne Verlust = Knopf bleibt Kandidat fuer
den Self-Play-Einsatz; signifikanter Verlust = Dosis/alpha pruefen,
kein Self-Play-Einsatz. Die Heuristik-Messung par.2b der
Minimax-Prereg bleibt davon unberuehrt gueltig.

### par.6b ERGEBNIS PILOT-MESSUNG (2026-08-23, Artefakte `paired_arena_env_imm_netvnet{,_swap}.json`; Zahlen vom Koordinator selbst erhoben)

Champion+alpha=0,2 gegen eingefrorenen Champion (Spec), Netz-gegen-
Netz, 407 Seeds + Brettwechsel, 400/400 Sims:

- **Siege: PARITAET.** alpha-Arm 201/407 (Normal) und 199/407
  (Brettwechsel), kombiniert 400/814 = 49,1 % (n.s.). Kein Gewinn,
  kein Verlust.
- **k1: der Vs-Heuristik-Effekt UEBERTRAEGT SICH NICHT.** alpha 30/312
  = 9,6 % gegen frozen 30/312 = 9,6 % (identisch; je Lauf 10,9/12,2 %
  bzw. 8,3/7,1 %). Der +7,0-pp-Befund aus par.2b der Minimax-Prereg
  war also gegnerspezifisch (Ausnutzung der Heuristik), kein
  Verhaltensgewinn gegen gleich starke Gegner. Instrument-Lehre in
  der Task-#18-Linie: der GEGNER gehoert zur Messanordnung.
- **par.6a-Verdikt: Parität ohne Verlust -> der Knopf bleibt
  SELF-PLAY-KANDIDAT** (dort spielen BEIDE Seiten mit Knopf --
  Datenverteilungs-Frage, kein Ausnutzungs-Szenario; Erwartung nach
  diesem Befund gedaempft, aber nicht widerlegt). Kein
  Gating-relevanter Befund.
- Methoden-Notiz: erste Netz-gegen-Netz-Knopfmessung im selben
  Prozess ueberhaupt -- die Welle-1-Kapselung hat ihren Zweck in der
  ersten Anwendung erfuellt (sie korrigierte das Bild des alten
  Instruments).

## par.7 Grenzen

Kein Suchparadigmen-Wechsel (bleibt geschlossen); keine Aenderung an
Encoding-/Kontrakt-Konstanten; das Env-Knopf-System bleibt fuer Diagnose
bestehen.

## par.8 ZIELBILD WELLE 3: gefrorene Champions als ladbare Artefakte (Nutzer-Richtung 2026-08-23, ENTWURF, nichts gebaut)

Nutzer-Gedanke: die Modul-Kopie zu Ende gedacht -- "die alten champs
greif ich eh nicht mehr an"; der gefrorene Champion wird als eigenes,
von der Engine geladenes Artefakt konserviert (Nutzer-Formulierung:
"als dll oder package").

**Options-Abwaegung (Koordinator):**

- **DLL-Grenze (verworfen als Vorschlag):** Rust hat keine stabile
  ABI; eine echte dynamische Bibliothek braeuchte ein C-kompatibles
  Interface fuer den GameState -- hohes Dauerrisiko fuer wenig Nutzen.
- **Empfohlene Form: eigener ENGINE-PROZESS je gefrorenem Champion**
  (Schach-Engine-Muster: persistenter Worker, Protokoll "Stellung
  rein, Zug raus"). Bausteine existieren: replay-exakter
  Zustands-Roundtrip und net_search_state_json (Paritaets-Sonde).
  Prozess-Isolation loest zugleich das OnceLock-Problem fuer
  Cross-Versions-Duelle vollstaendig. Serialisierung je Zug ist
  gegen 400-Sims-Suchen vernachlaessigbar.
- **Freeze-Artefakt** = Modell + Spec (Welle 1) + GEPINNTES Wheel.
  Neue Disziplin ab sofort noetig: beim Gating das Wheel archivieren
  (heute wird engine/target/wheels bei jedem Build ueberschrieben,
  Versionsnummer konstant 0.1.0).
- **Regel-Autoritaet:** der Schiedsrichter-Prozess (aktuelle Engine)
  fuehrt die Partie und validiert Zuege der gefrorenen Seite --
  Regel-Fixes (Praezedenz Rulebook-Audit) duerfen einen Alt-Champ nie
  still nach alten Regeln spielen lassen.
- **Kompatibilitaets-Abgleich Artefakt <-> aktuelle Engine
  (Nutzer-Anforderung 2026-08-23), zwei Schichten:**
  1. *Statischer Handshake beim Laden:* das Artefakt-Manifest traegt
     engine_version, `contract_hash` (existiert: lib.rs:649, ueber
     engine_config_json exponiert, elo_tracker liest es schon) und
     die Zustands-Schema-Version; der Referee vergleicht mit seinen
     eigenen Werten. Mismatch = harte Verweigerung per Default --
     das mechanisiert die bestehende Leiter-Regel "Kanten ueber die
     Fix-Grenze nie mischen"; bewusste Cross-Aera-Messungen nur mit
     explizitem, dokumentiertem Override.
  2. *Golden-Selbsttest im Artefakt:* beim Freeze werden N
     Probe-Stellungen samt erwarteter Antworten (Zug + Wert) INS
     Artefakt gelegt; der Referee spielt sie beim Laden nach
     (Paritaets-Sonden-Philosophie, das Artefakt bringt seine eigene
     Sonde mit). Faengt, was Versions-Stempel nicht sehen:
     ORT-/DLL-/Umgebungsdrift.
- Aufwand grob eine Groessenordnung ueber Welle 1 (Protokoll-Worker +
  Referee-Umbau der Arena + Handshake).
- **BAUBEGINN FREIGEGEBEN (Nutzer 2026-08-23, "ja das gefaellt mir"):**
  Umsetzung per Agent NACH der laufenden Pilot-Messung; erstes
  Freeze-Ziel ist der amtierende Champion **v21_2d_brierbest**.
  Engine-Artefakt dafuer liegt bereits vor: das archivierte Welle-1-
  Wheel (models/frozen_wheels/mosaic_rust_searchconfig_wave1_20260823
  .whl) ist ueber die Paritaets-Kette 8c6684ff byte-identisch zur
  R5-Fix-Aera, auf der v21s Elo 1215 gemessen ist.
