# Vorregistrierung: Value-Rangmetrik gegen das Orakel (Task #29)

**Angelegt 2026-08-03, VOR der ersten Tau-Berechnung.** Zweck wie bei den
Vorbild-Dokumenten (`PREREG_pcr.md`, `PREREG_lambda_target.md`,
Praezedenzfall `PREREG_ownership_gumbel.md`): Metrik-Design UND
Validierungsregeln VOR der ersten Messung festlegen. Diese Datei darf nach
Sichtung der Ergebnisse NICHT mehr geaendert werden.

Auftragsgrenze dieses Durchlaufs: nur die PREREG + das Werkzeug + ein
`--smoke`-Lauf (2 Modelle, 30 Orakel-Zustaende, reine Plausibilitaetspruefung).
Die volle historische Validierung startet der Koordinator separat.

## Hintergrund (STATUS.md, "Task #29", 2026-08-03)

Nutzer-These nach Dreifach-Evidenz desselben Tages: `value_r2_rounds_1_4` ist
vermutlich nicht der richtige Hebel fuer Arena-Staerke.

1. v11-TD-Bootstrap hob R1/R2-R² -- keine Staerke.
2. Lambda-Sweep: 6/6 Seeds offline positiv, Arena SPRT-H0 (kein Sieg).
3. PCR: `value_r2` +0,04, Arena-Trend negativ.

Gleichzeitig traegt der Value-Kopf nachweislich die Staerke (2×2-Kopftausch
bei 400 Sims, Memory `project_hybrid_head_attribution`: P=v10/V=v12 → 57,5%,
P=v12/V=v10 → 49,2%). Arbeitshypothese: die Suche konsumiert LOKALE Ordnung
von Geschwister-/Blattzustaenden, nicht globale Ausgangs-Vorhersage -- R²
misst die falsche Eigenschaft. Konsistent damit: beide bislang arena-
validierten Praediktoren (`prior_mass_on_oracle_top3`,
`kendall_tau_policy_vs_oracle_q`, STATUS.md "Orakel-Metriken validiert:
7/7", Binomial p=0,0156) sind Ordnungs-Metriken auf der POLICY-Seite. Diese
PREREG ueberträgt dieselbe Ordnungs-Logik auf die VALUE-Seite.

## Metrik-Design

### `value_kendall_tau_vs_oracle_q`

Fuer jeden orakel-gelabelten frozen-Zustand (`frozen_v1_oracle_labels_v18.json`,
v18_best-Quelle, 5000 Sims, 1185 Zustaende, Runde 1-4 auswertbar): die vom
Orakel betrachteten Wurzelkandidaten-Aktionen nehmen, je Kandidat den
VALUE-KOPF-Rohwert des zu pruefenden Netzes auf dem resultierenden
AFTERSTATE einholen, Kendall-Tau (tau-a, dieselbe Implementierung wie
`oracle_metrics.py::_kendall_tau_a`) zwischen dieser Rangfolge und der
Orakel-Q-Ordnung (`mcts_q` je Kandidat) bilden, dann ueber alle Zustaende
mitteln. Exaktes Analogon zu `kendall_tau_policy_vs_oracle_q`, nur auf der
Value- statt der Policy-Seite. Gleiche Mindestgroesse wie dort: ein Zustand
zaehlt nur mit `>=3` vom Orakel betrachteten Kandidaten (sonst ist Tau nicht
sinnvoll definiert).

Runde 5 wird ausgeschlossen (identische Begruendung wie ueberall sonst im
Projekt: `round5.rs` umgeht das Netz komplett, exakte Alpha-Beta-Suche).

### Afterstate-Beschaffung -- gepruefte Optionen, in der vorgegebenen Reihenfolge

**(1) Generischer "wende Aktion auf state_json an"-Python-Binding.**
`engine/src/lib.rs` durchsucht (`grep -n "pyfunction"`): es gibt
`advance_after_tiling_json(state_json, seed)`, aber die wendet NUR den
Rundenuebergang TILING→naechste DRAFTING an (Nachfuell-Chance-Knoten), keine
einzelne Drafting-Aktion. Eine generische Drafting-Aktions-Anwendung auf
einen freistehenden `state_json` existiert NICHT als Python-Binding (nur
`PyGame`-Instanzmethoden wie `apply_stone`/`apply_dome`/... auf einem
LEBENDEN, inkrementell aufgebauten Spielzustand -- nicht auf einem beliebigen
gespeicherten Frozen-Set-Zustand). Option (1) entfaellt.

**(2) `net_search_state_json_trace` mit kleinem Sim-Budget.** Jeder
Wurzelkandidat wird beim Baumaufbau SOFORT bei Expansion ausgewertet
(`net_mcts.rs::make_node`) und dieser Wert unveraendert als `net_leaf_value`
im `moves`-Array zurueckgegeben (`net_mcts.rs:3208`,
`"net_leaf_value": node.leaf_value[node.player_who_acted]`) --
**unabhaengig vom Sim-Budget** (auch bei `sims=1` bereits vorhanden, da bei
der Root-Expansion berechnet, nicht erst durch Rueckwaerts-Propagierung).
Skala/Perspektive ist IDENTISCH zu `mcts_q` (`value_to_win_prob`/
`blended_leaf_win_prob`, `[0,1]`-Sieg-Wahrscheinlichkeit, aus Sicht des
Spielers, der den Zug gemacht hat) -- direkt vergleichbar mit der Orakel-
`mcts_q`-Spalte, ohne Skalen-Anpassung (fuer Kendall-Tau ohnehin irrelevant,
da rangbasiert).

Das ist zugleich die vom Auftrag vorgeschlagene TRUESTE Messung: exakt der
Wert, den die Suche selbst an den Wurzelkindern sieht, kein separater
Rekonstruktionspfad. GEPRUEFT (empirisch, `frozen_v1_oracle_labels_v18.json`
+ `models/alphazero_v18_best.onnx` und `models/alphazero_v17_best.onnx`,
2026-08-03):

- Bei `sims=400` (Produktions-Standard) ist `gumbel_top_m_for_budget(400) =
  16 = GUMBEL_TOP_M` -- dieselbe Kandidatenzahl-Obergrenze, mit der auch die
  Orakel-Labels selbst gebaut wurden (5000 Sims → ebenfalls
  `m_prime=16`, geclampt).
  - `v18_best` (= Orakel-Quelle) gegen 5 Beispielzustaende: Ueberlappung
    Kandidat-Wurzelkinder ∩ Orakel-Kandidaten = 100% bei `sims>=400`
    (bei `sims=200` nur 88-96%, `m_prime` dort noch 13 statt 16 --
    **deshalb `sims=400` als Default, nicht kleiner**).
  - `v17_best` (ECHTER, unabhaengiger Test -- nicht die Orakel-Quelle, ein
    schwaecheres Vorgaenger-Netz) gegen 30 Zustaende: mittlere
    Ueberlappungsquote 97,6% der Orakel-Kandidatenmenge, Minimum 88,9%,
    0 Zustaende mit absoluter Ueberlappung `<3` (bei ausreichend grosser
    Orakel-Kandidatenmenge je Zustand).
  - Laufzeit: ~0,53 s je Zustand+Modell bei `sims=400` (CPU, `tract`/ONNX) --
    fuer die geplante volle Validierung (Groessenordnung 1000 Zustaende ×
    N Modelle) unproblematisch, fuer den `--smoke`-Lauf trivial (~30 s fuer
    2×30).

Damit ist (2) fuer ALLE Modelle mit vorhandener `.onnx`-Datei nutzbar (auch
alte Checkpoints, sofern die Gewichtsdatei ueberhaupt existiert) -- die
harte Anforderung aus dem Auftrag ("muss fuer BELIEBIGE historische
ONNX-Checkpoints berechenbar sein"). `Net::load_auto` (`engine/src/net.rs`)
laedt ausschliesslich ueber `tract_onnx` -- kein `.pth`-Pfad, `.onnx` ist
also ohnehin die einzig moegliche Eingabe fuer diesen Suchpfad. Option (2)
wird verwendet, Option (3) (Python-seitige Aktionsanwendung) entfaellt
dadurch ersatzlos.

### Bekannte Einschraenkung: Kandidatenmengen-Ueberlappung

Die Wurzelkinder-Auswahl (`top-m` Gumbel Sequential-Halving) richtet sich
nach dem PRIOR DES GEPRUEFTEN Netzes selbst, nicht nach dem Orakel-Prior --
bei einem Netz, dessen Policy stark von der Orakel-Quelle (v18_best)
abweicht, KOENNTE die Ueberlappung kleiner ausfallen als in den beiden oben
gemessenen Faellen (v18_best: Orakel-Quelle selbst, mechanisch 100%;
v17_best: direkter Vorgaenger, 97,6% -- beide aus derselben Warm-Start-Linie
wie das Orakel). Ein wirklich ENTFERNTES/schwaches Netz (v14-Aera oder
aelter) konnte NICHT getestet werden, weil dessen Gewichte seit dem
Datenverlust vom 2026-07-24 nicht mehr vorliegen (siehe Abschnitt
"Validierbare historische Paare" unten) -- die Ueberlappungsquote fuer
architektonisch/generationsmaessig weit entfernte Netze ist also
UNGEPRUEFT. Die Implementierung faengt das ab, statt blind zu rechnen: pro
Zustand wird nur die tatsaechliche Schnittmenge (Kandidat-Wurzelkinder ∩
Orakel-Kandidaten) verwendet, ein Zustand mit `<3` ueberlappenden Kandidaten
wird uebersprungen (identische Schwelle wie die Policy-Tau-Metrik), und die
Ausgabe berichtet die mittlere Ueberlappungsquote + Anzahl uebersprungener
Zustaende explizit -- eine kuenftige Validierung mit einem sehr abweichenden
Netz wuerde eine niedrige Quote SICHTBAR machen statt sie zu verschleiern.

## Berechnungs-Schnittstelle (fuer den spaeteren Vollauf)

`tools/value_rank_metric.py::compute_for_model(model_name, oracle_labels,
states_by_idx, sims=400, c_puct=1.5)` -- EIN Aufruf pro Modell, liefert eine
Liste von Pro-Zustand-Ergebnissen (analog `oracle_metrics.py::
compute_for_model`); `aggregate(...)` fasst zu `overall`/`by_round`
zusammen. Der Koordinator kann die volle historische Validierung spaeter
mit einem einzigen CLI-Aufruf anstossen:

```
python tools/value_rank_metric.py --validate
```

(iteriert automatisch ueber alle ENTSCHIEDENEN Gating-Paare mit vorhandenen
`.onnx`-Dateien, siehe naechster Abschnitt -- kein manuelles Modell-Listing
noetig, wird aber per `--models`/`--pairs` ueberschreibbar gehalten).

## Validierungsregeln (identische Prozedur wie `tools/offline_vs_arena.py`)

Wiederverwendet (Import, kein Nachbau): `offline_vs_arena.load_gatings`
(Gating-Dateien einlesen, Dubletten/Mehrfachbloecke zusammenfassen, McNemar
exakt je Paar) sowie `binom_p_two_sided`/`pearson`/`spearman`/`perm_p` fuer
die Korrelationsberichte. Ein Gating-Paar gilt als ENTSCHIEDEN bei
McNemar-p < 0,05 (Standardwert von `offline_vs_arena.py`, `--min-pairs 50`).

**Zusaetzlicher Filter gegenueber `offline_vs_arena.py`**: nur Paare, bei
denen BEIDE Modelle noch eine `.onnx`-Datei unter `models/` besitzen (die
Rangmetrik braucht die Engine-Suche, nicht nur eine `.pth`-Gewichtsdatei).

### Validierbare historische Paare (Stand 2026-08-03, per Skript ausgegeben)

Ermittelt durch `offline_vs_arena.load_gatings(min_pairs=50)` gefiltert auf
`.onnx`-Verfuegbarkeit beider Modelle:

| A vs B | Paare | Siegquote A | McNemar p | entschieden? |
|---|---|---|---|---|
| l07v18_s6_best vs l10v18_s3_best | 200 | 0,568 | 0,0101 | JA |
| pcrpcr_s5_best vs pcrkontrolle_s6_best | 75 | 0,447 | 0,2559 | nein |
| v18_best vs v17_best | 125 | 0,584 | 0,0086 | JA |
| v19_2d_best vs v19_best | 50 | 0,640 | 0,0094 | JA |
| v19_2d_opp_best vs v19_2d_best | 200 | 0,522 | 0,4215 | nein |
| v19_best vs v18_best | 75 | 0,640 | 0,0011 | JA |

**4 aktuell entschiedene UND auswertbare Paare.** Alle uebrigen 23
historischen Gating-Paare (v10..v17_lrfix-Aera, `fs_*`/`opp_*`/`lam*`/
`voll`/`halb`-Ablationen) haben mindestens ein Modell ohne vorliegende
`.onnx`-Datei -- ueberwiegend die v10..v16-Generation (Datenverlust
2026-07-24, Memory `project_onedrive_file_disappearance`) sowie diverse
Ablations-Checkpoints, deren Gewichte nach Abschluss des jeweiligen
Experiments nicht dauerhaft aufbewahrt wurden.

### Erfolgskriterium (VORAB festgelegt, exakt wie bei den Orakel-Metriken)

Referenzniveau: die beiden validierten Orakel-Metriken bestanden mit 7/7
Richtungstreffern, Binomial p=0,0156.

- **Bestanden ("VALIDIERT")**: alle Richtungen auf den entschiedenen,
  auswertbaren Paaren korrekt UND Binomial-p < 0,05.
- **Sonst: "NICHT VALIDIERT"** (auch bei z.B. 3/4 korrekt).

**Wichtiger Vorbehalt, VORAB dokumentiert (nicht erst nach dem Ergebnis):**
mit den aktuell nur **4** verfuegbaren entschiedenen Paaren ist
p<0,05 SELBST BEI 4/4 KORREKTEN RICHTUNGEN STRUKTURELL UNERREICHBAR
(`binom_p_two_sided(4,4) = 2/2^4 = 0,125`). Der exakte Vorzeichentest
erreicht p<0,05 erst ab `n=6` (6/6 → p=0,03125). Ein Ergebnis "NICHT
VALIDIERT" bei diesem Stand kann also entweder (a) an der Metrik selbst
liegen oder (b) allein an der zu kleinen Stichprobe -- die Ausgabe des
Werkzeugs berichtet BEIDES getrennt (Trefferquote UND ob n strukturell
ausreicht), damit diese zwei Faelle nicht verwechselt werden. Eine
abschliessende Aussage braucht entweder mehr erhaltene `.onnx`-Dateien aus
kuenftigen Ablationen oder zusaetzliche entschiedene Gating-Paare aus dem
laufenden/kommenden Zyklus.

### Sekundaer, nicht entscheidend: Trennschaerfe vs. `value_r2_rounds_1_4`

Auf denselben Paaren wird zusaetzlich (informativ) berichtet, wie oft/mit
welchem p `value_r2_rounds_1_4` (aus den vorhandenen
`offline_diagnose_*_frozen.json`, ueber `offline_vs_arena.load_offline()`
eingelesen) dieselben Paare richtig vorhersagt -- die eigentliche Frage
hinter Task #29 ("schlaegt die Rangmetrik den globalen R²?"), aber laut
Aufgabenstellung NICHT das Erfolgskriterium.

## `--smoke`-Lauf (Teil dieses Auftrags, GPU/CPU-leicht)

`python tools/value_rank_metric.py --smoke`: 2 Modelle (Default
`v18_best`/`v17_best`, beide `.onnx` vorhanden), 30 Orakel-Zustaende
(erste 30 auswertbaren Zustaende aus `frozen_v1_oracle_labels_v18.json`,
Runde 1-4, `>=3` Kandidaten), `sims=400`. Plausibilitaetspruefungen (keine
Entscheidungsmetrik, nur Rauchtest):

1. Tau je Zustand liegt in `[-1,1]`.
2. Die Verteilung ist nicht degeneriert (nicht konstant `0` oder `NaN` fuer
   alle Zustaende -- haette ein Bug in der ID-Zuordnung/Ueberlappung zur
   Folge).
3. `v18_best` (Champion relativ zu `v17_best`, Gating 125 Paare, 58,4%,
   entschieden) wird erwartbar (nicht garantiert bei n=30) einen hoeheren
   mittleren Tau zeigen als `v17_best`.

## Offene Fragen (nicht Teil dieses Auftrags)

1. Ueberlappungsquote fuer architektonisch weit entfernte/sehr schwache
   Netze (v14-Aera oder aelter) bleibt ungeprueft, da keine `.onnx`-Datei
   mehr vorliegt.
2. Nur 4 entschiedene, auswertbare Paare aktuell -- das Erfolgskriterium
   ist mit dieser Stichprobe im besten Fall (4/4) bei p=0,125, NICHT
   signifikant. Erst mit `n>=6` entschiedenen Paaren ist p<0,05 ueberhaupt
   erreichbar.
3. R5-Teilmenge optional gegen exakte `ab_value` (STATUS.md-Planskizze,
   Schritt 1) ist NICHT Teil dieser PREREG/dieses Werkzeugs -- Runde 5 wird
   hier konsequent ausgeschlossen (wie ueberall sonst), ein separates
   R5-spezifisches Rangmass waere ein eigenes Vorhaben.
4. Bei bestandener Validierung: Schritt 3 aus der STATUS.md-Planskizze
   (Ranking-orientierte Trainingsziele, Paarvergleichs-/Margin-Loss) ist
   ausdruecklich ein SEPARATES, spaeteres Vorhaben mit eigener PREREG.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- Die volle Validierung (6
entschiedene Paare) ergab NICHT VALIDIERT: nur 2/6 Richtungen korrekt
(p=0,69), Zufallsniveau, sogar schlechter als das globale
`value_r2_rounds_1_4` (3/6). Die Ordnungs-These auf der Value-Seite ist in
dieser Operationalisierung widerlegt. Achtung Verwechslungsgefahr: dies ist
NICHT dieselbe Frage wie `PREREG_t35b_ranking.md` (dort: Ranking-LOSS als
Trainingsziel, separat "GESCHLOSSEN"). Das aktuelle `evaluations/STATUS.md`
fuehrt "#29-Instrument" als OFFEN -- das betrifft eine NEUE Wiederaufnahme
unter der WDL-Aera (neue frozen_v2-Labels), nicht diese bereits
beantwortete Frage. Belegstelle: archive/history.md, Abschnitt "Task #29
ERGEBNIS: Value-Rangmetrik NICHT VALIDIERT (2026-08-04)", Zeile
~7532-7567; evaluations/value_rank_metric_validation.json.
