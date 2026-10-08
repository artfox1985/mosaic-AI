# -*- coding: utf-8 -*-
"""Schluessel EINER Korpusdatei fuer den Datei-Cache (Hebel 4).

Vorregistriert in `evaluations/PREREG_cache_build_time.md` par.6, abgenommen
in par.9. EIGENES Modul, aus zwei Gruenden: der Schluessel ist ein
abgeschlossener Vertrag mit genau einer Aufgabe, und `neural_net.py` liegt mit
165 KB laengst ueber der Groessen-Schwelle aus CLAUDE.md -- die Ratsche in
`tools/check_conventions.py` hat den Anbau dort zu Recht abgelehnt.

Die Konstanten kommen bewusst erst BEIM AUFRUF aus `neural_net`/`config`
(lokale Importe unten), nicht beim Import dieses Moduls: `INPUT_SIZE` haengt
an der Engine-Konfiguration, und der Schluessel muss dieselbe Bindungszeit
sehen wie die Bauschleife. Nebenbei vermeidet es den Ringschluss --
`neural_net` re-exportiert `per_file_cache_key`.
"""


def _moon_target_source_key() -> str:
    """Liest `MOSAIC_MOON_TARGET_SOURCE` fuer den BLOCK-Schluessel.

    `PREREG_moon_stack_order.md` par.12.1, Arm v29-b04. Der Schalter entscheidet,
    woher das Ziel des `moon`-Kopfs kommt: "label" (Bestand, das No-Op-Feld
    `moon_order_target`) oder "played" (die von der Suche bevorzugte Reihenfolge
    aus der policy-Verteilung).

    WARUM AUCH HIER und nicht nur im Fenster-Schluessel: die BLOECKE tragen
    `moon_order_targets` bereits (`corpus_dataset.py` speichert das Dataset je
    Datei). Kennt der Block-Schluessel den Schalter nicht, benutzt ein
    b04-Lauf die Bloecke von b03 -- mit den LABEL-Zielen, also genau dem
    No-Op, das der Arm abschaffen soll. Derselbe Fehler wie 2026-09-14 bei
    `MOSAIC_SPECIAL_PLANES_OFF`, nur umgekehrt: dort fehlte der Fenster-, hier
    fehlte beinahe der Block-Schluessel
    (`feedback_feature_knob_belongs_in_both_cache_keys`).

    Ungueltige Werte gelten als Bestand -- ein Tippfehler darf keinen stillen
    dritten Datensatz erzeugen.
    """
    import os
    v = (os.environ.get("MOSAIC_MOON_TARGET_SOURCE") or "label").strip().lower()
    return v if v in ("label", "played") else "label"


def _features_from_rust_key() -> bool:
    """Liest `MOSAIC_FEATURES_FROM_RUST` fuer BEIDE Cache-Schluessel.

    `PREREG_rust_data_layer.md` par.9a, Nutzer-Entscheid 2026-09-17 (Weg (1)).
    Der Schalter entscheidet, WELCHER Bauer den Inhalt der gecachten Planes und
    des Flachvektors liefert: gesetzt = `features.rs` rechnet frisch, ungesetzt
    = der Python-Zwilling LIEST die gespeicherten Felder aus dem Record
    (`neural_net.py` Z.781 fuer `cell_reachable_mask`).

    WARUM ER JETZT IM SCHLUESSEL STEHT: bis zum 2026-09-17 stand er bewusst in
    KEINEM (`docs/knobs.md`), Begruendung "beide Bauer sind bit-identisch".
    Das gilt auf ALT-Records seit dem 2026-09-12 nicht mehr: der A2-Phantom-Fix
    hat `provocation::remaining_colors` geaendert, und die Records von davor
    tragen die alte Zahl, waehrend Rust die neue rechnet (par.9a: 2 von 300
    Zustaenden, Planes-Kanal 76). Weil Bloecke MEMOISIERT werden
    (`build_cache_incremental.py` Z.134-137), erbte ein Arm sonst die Semantik
    dessen, der den Block zuerst gebaut hat -- unabhaengig von der eigenen
    Schalterstellung. Innerhalb von v29 stand der Schalter uneinheitlich.

    Aus der Umgebung GELESEN, kein Parameter: Holschuld an einer Stelle statt
    Bringschuld an sieben (`tools/tests/test_cache_key_knobs_are_env_coupled.py`,
    Vorfall `moon_target_source` vom 2026-09-16). Dieselbe Semantik wie
    `neural_net.py` Z.98 -- exakt "1", nichts sonst.
    """
    import os
    return os.environ.get("MOSAIC_FEATURES_FROM_RUST") == "1"


def _special_planes_off_key() -> bool:
    """Liest `MOSAIC_SPECIAL_PLANES_OFF` fuer den Cache-Schluessel.

    Eigene kleine Funktion statt Import aus `neural_net`, weil dieses Modul
    bewusst importarm bleibt (siehe Kopf: `INPUT_SIZE` wird erst IN der
    Funktion importiert, damit der Schluessel nicht an der Import-Reihenfolge
    haengt). Dieselbe Semantik wie dort und wie in Rust: gesetzt und nicht "0".
    """
    import os
    v = os.environ.get("MOSAIC_SPECIAL_PLANES_OFF", "")
    return bool(v) and v != "0"


def _final_margin_key() -> bool:
    """Liest `MOSAIC_CACHE_FINAL_MARGIN` fuer BEIDE Cache-Schluessel.

    E2-Arm (`PREREG_evaluator_pretests.md` par.4/par.8a, `PREREG_v34_window.md`
    par.3): die Margen-Schwellen brauchen die rohe Endmarge je Zustand,
    `scores_unclamped[p] - scores_unclamped[1-p]` aus Sicht des Ziehers. Kein
    Bestandsfeld traegt sie: `endgame_margin` ist trotz des Namens der exakte
    R5-Wurzelwert (`root_q`, corpus_dataset.py Bauschleife, Schema 18), und
    `values`/`points_forecast`/`opp_points_forecast` sind tanh-gestaucht UND mit
    `bootstrap_value` TD-geblendet, also nicht eindeutig rueckrechenbar.

    Gesetzt = die Bauschleife schreibt das Zusatzfeld `final_margin`. Das
    aendert den BLOCK-Inhalt, darum steht der Knopf hier UND im
    Fenster-Schluessel (`feedback_feature_knob_belongs_in_both_cache_keys`).
    Nur angehaengt, wenn gesetzt: alle vorhandenen Bloecke und Monolithen
    behalten ihren Schluessel. Aus der Umgebung gelesen, kein Parameter
    (Holschuld, `test_cache_key_knobs_are_env_coupled.py`). Exakt "1", nichts
    sonst; train.py setzt ihn selbst aus `--margin-thresholds`.
    """
    import os
    return os.environ.get("MOSAIC_CACHE_FINAL_MARGIN") == "1"


def _supply_demand_key() -> bool:
    """Liest `MOSAIC_SUPPLY_DEMAND_FEATURES` fuer BEIDE Cache-Schluessel (E4-Arm).

    `PREREG_v34_window.md` par.3: mit dem Knopf traegt jeder Block 936 statt 888
    Flachwerte (Angebots-Bedarfs-Block, `engine/src/supply_demand.rs`). Die Breite
    steht schon als `str(INPUT_SIZE)` im Schluessel; der Marker steht trotzdem da,
    weil er die FORMEL versioniert (`_v1`) und weil die Breite beim Import von
    `config` gebunden wird, der Knopf aber hier zur Aufrufzeit. Die Gleichlauf-
    Pruefung in `supply_demand_features.supply_demand_key` bricht ab, wenn beide
    auseinanderlaufen (`feedback_feature_knob_belongs_in_both_cache_keys`).
    Nur ANGEHAENGT, wenn gesetzt: alle vorhandenen Bloecke behalten ihren Schluessel.
    """
    from supply_demand_features import supply_demand_key
    return supply_demand_key()


def _aggr_own_q_eps_key() -> str | None:
    """Liest `MOSAIC_AGGR_OWN_Q_EPS` fuer BEIDE Cache-Schluessel (Klasse S).

    `PREREG_asymmetric_selfplay.md` par.3/par.3a: Records der Stoerer-Seite
    (`player == aggr_side`) mit `own_q_gap > eps` bekommen Policy-Gewicht 0
    (`corpus_dataset.asymmetric_policy_masked`). Das aendert `policy_weights` im
    BLOCK, darum steht der Knopf hier UND im Fenster-Schluessel
    (`feedback_feature_knob_belongs_in_both_cache_keys`) -- ein zweites eps auf
    demselben Korpus waere sonst ein Datensatz mit dem Namen des ersten.

    Rueckgabe: `None` = Maske aus (ungesetzt oder leer, Bestand, kein Marker),
    sonst die KANONISCHE Schreibweise `repr(float(eps))`, damit "0.02" und
    "0.020" denselben Schluessel bekommen. Ungueltig (keine endliche Zahl) ist
    ein harter Fehler: ein Tippfehler darf weder still "aus" noch einen dritten
    Datensatz erzeugen. Aus der Umgebung gelesen, kein Parameter (Holschuld,
    `test_cache_key_knobs_are_env_coupled.py`).
    """
    import math
    import os
    raw = (os.environ.get("MOSAIC_AGGR_OWN_Q_EPS") or "").strip()
    if not raw:
        return None
    try:
        eps = float(raw)
    except ValueError:
        eps = float("nan")
    if not math.isfinite(eps):
        raise ValueError(f"MOSAIC_AGGR_OWN_Q_EPS={raw!r} ist keine endliche Zahl")
    return repr(eps)


def _mask_dice_trigger_key() -> bool:
    """Liest `MOSAIC_MASK_DICE_TRIGGER` fuer BEIDE Cache-Schluessel (Klasse W).

    `PREREG_asymmetric_selfplay.md` par.3a F2 (Bauplan 7 (b)): der Ausloeser-Record
    (`dice_trigger: true`) behaelt im Bestand sein Policy-Ziel; der Knopf nimmt es
    optional weg. Aendert `policy_weights` im Block, also beide Schluessel. Exakt
    "1", nichts sonst; nur dann ein Marker.
    """
    import os
    return os.environ.get("MOSAIC_MASK_DICE_TRIGGER") == "1"


def _mask_dice_phase_value_key() -> bool:
    """Liest `MOSAIC_MASK_DICE_PHASE_VALUE` fuer BEIDE Cache-Schluessel (Klasse W).

    `PREREG_asymmetric_selfplay.md` par.5d (Eroeffnungs-Wuerfel): Records aus der
    Wuerfelphase (`dice_phase: true`, beide Seiten) bekommen KEIN Wertziel. Mit
    Knopf schreibt die Bauschleife das Zusatzfeld `value_weights` (0 auf diesen
    Records, sonst 1), train.py nimmt es in den Gewichtsweg der Wertverluste. Das
    aendert den BLOCK-Inhalt, also beide Schluessel
    (`feedback_feature_knob_belongs_in_both_cache_keys`). Exakt "1", nichts sonst;
    nur dann ein Marker, ohne Knopf bleibt jeder vorhandene Schluessel.
    """
    import os
    return os.environ.get("MOSAIC_MASK_DICE_PHASE_VALUE") == "1"


BOOTSTRAP_HORIZON_ROUNDS_ALLOWED = (1, 2, 3)
BOOTSTRAP_SOURCES = ("trajectory", "trajectory_lambda", "margin")
# par.19.1 (Arm v35-b11): Default von MOSAIC_BOOTSTRAP_TRAJ_LAMBDA, wenn die
# Quelle trajectory_lambda ohne eigenes lambda gesetzt ist.
BOOTSTRAP_TRAJ_LAMBDA_DEFAULT = "0.5"
# par.19.4 (Arm v35-b14): Bestandswert des TD-Blends (bis 2026-10-08 die
# Konstante `neural_net.TD_LAMBDA = 0.5`). Ohne MOSAIC_TD_LAMBDA genau dieser
# Wert -- `str(0.5)` steht seit jeher in beiden Schluesseln, der Bestand
# bleibt also bitgleich.
TD_LAMBDA_DEFAULT = 0.5


def _canonical_number(value: float) -> str:
    """Kanonischer Marker-String einer Zahl: `repr(float)` ohne ein
    abschliessendes ".0" ("20" statt "20.0", "0.5", "12.5"), damit "0.50" und
    "0.5" denselben Schluessel bekommen und zwei Werte zwei."""
    canonical = repr(float(value))
    if canonical.endswith(".0"):
        canonical = canonical[:-2]
    return canonical


def _parse_number(raw: str, name: str, *, low: float, high: float | None,
                  low_inclusive: bool, rule: str) -> str:
    """Prueft eine Zahl aus der Umgebung und gibt sie kanonisch zurueck.
    `rule` ist der Klartext der erlaubten Menge fuer die Fehlermeldung."""
    import math
    try:
        value = float(raw)
    except ValueError:
        value = float("nan")
    ok = math.isfinite(value) and (value >= low if low_inclusive else value > low)
    if high is not None:
        ok = ok and value <= high
    if not ok:
        raise ValueError(f"{name}={raw!r} ungueltig -- erlaubt: {rule}.")
    return _canonical_number(value)


def _bootstrap_source_config():
    """Liest und prueft `MOSAIC_BOOTSTRAP_SOURCE` mit ALLEN seinen Parametern.

    EINE Pruefstelle fuer alle Quellen, damit die Schluessel-Leser darunter
    (`_bootstrap_trajectory_horizon_key`, `_bootstrap_trajectory_suffix_key`,
    `_bootstrap_trajectory_lambda_key`, `_bootstrap_margin_scale_key`) und die
    Bauschleife (`_bootstrap_variant_config`) nie verschiedene Lesarten
    derselben Umgebung haben. Rueckgabe:

    - `None`: Bestand (alles ungesetzt oder leer), kein Marker.
    - `("trajectory", k, extras)`: par.12a, Arm v35-b03; k in 1..3, Pflicht.
      `extras` = {"mix": str|None, "conf_scale": str|None}: par.19.3 (b13,
      `MOSAIC_BOOTSTRAP_TRAJ_MIX`, Zahl in [0, 1]) und par.19.5 (b15,
      `MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE`, Zahl > 0); hoechstens einer gesetzt.
    - `("trajectory_lambda", lambda, extras)`: par.19.1, Arm v35-b11; lambda aus
      `MOSAIC_BOOTSTRAP_TRAJ_LAMBDA` (Zahl in [0, 1], Default "0.5"),
      `extras` = {"opponent": bool} aus `MOSAIC_BOOTSTRAP_TRAJ_OPPONENT`
      (par.19.2, b12; "1" an, "0" oder leer aus).
    - `("margin", b, {})`: par.14, Arm v35-b04; b = Skala in Punkten, endliche
      Zahl > 0, Pflicht.

    Zahlen stehen KANONISCH im Tupel (`_canonical_number`), damit "20" und
    "20.0" denselben Schluessel bekommen und zwei Werte zwei.

    Harte Fehler statt stillem Default: unbekannte Quelle, fehlender oder
    ungueltiger Pflichtparameter, und jeder Parameter, der zur gesetzten Quelle
    nicht gehoert oder ohne Quelle gesetzt ist (ein verwaister Parameter waere
    ein Knopf, der unbemerkt nichts tut). MIX und CONF_SCALE zusammen sind
    ebenfalls ein Fehler: ihre Kombination ist nicht registriert.
    """
    import os
    source = (os.environ.get("MOSAIC_BOOTSTRAP_SOURCE") or "").strip().lower()
    raw_horizon = (os.environ.get("MOSAIC_BOOTSTRAP_HORIZON_ROUNDS") or "").strip()
    raw_scale = (os.environ.get("MOSAIC_BOOTSTRAP_MARGIN_SCALE") or "").strip()
    raw_lambda = (os.environ.get("MOSAIC_BOOTSTRAP_TRAJ_LAMBDA") or "").strip()
    raw_opponent = (os.environ.get("MOSAIC_BOOTSTRAP_TRAJ_OPPONENT") or "").strip()
    raw_mix = (os.environ.get("MOSAIC_BOOTSTRAP_TRAJ_MIX") or "").strip()
    raw_conf = (os.environ.get("MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE") or "").strip()
    if raw_opponent not in ("", "0", "1"):
        raise ValueError(
            f"MOSAIC_BOOTSTRAP_TRAJ_OPPONENT={raw_opponent!r} ungueltig -- erlaubt '1' (an), '0' oder leer (aus).")
    opponent = raw_opponent == "1"
    # Welche Parameter zu welcher Quelle gehoeren (Name, gesetzt?, Quelle).
    params = (
        ("MOSAIC_BOOTSTRAP_HORIZON_ROUNDS", raw_horizon, "trajectory"),
        ("MOSAIC_BOOTSTRAP_TRAJ_MIX", raw_mix, "trajectory"),
        ("MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE", raw_conf, "trajectory"),
        ("MOSAIC_BOOTSTRAP_TRAJ_LAMBDA", raw_lambda, "trajectory_lambda"),
        ("MOSAIC_BOOTSTRAP_TRAJ_OPPONENT", "1" if opponent else "", "trajectory_lambda"),
        ("MOSAIC_BOOTSTRAP_MARGIN_SCALE", raw_scale, "margin"),
    )
    if not source:
        for name, raw, owner in params:
            if raw:
                raise ValueError(
                    f"{name}={raw!r} ist gesetzt, aber MOSAIC_BOOTSTRAP_SOURCE nicht -- ohne "
                    f"'{owner}' waere der Parameter wirkungslos.")
        return None
    if source not in BOOTSTRAP_SOURCES:
        raise ValueError(
            f"MOSAIC_BOOTSTRAP_SOURCE={source!r} unbekannt -- erlaubt sind {BOOTSTRAP_SOURCES} "
            "(ungesetzt = Bestand, Netz-Rollout bootstrap_value).")
    for name, raw, owner in params:
        if raw and owner != source:
            raise ValueError(
                f"{name}={raw!r} gehoert zur Quelle '{owner}', nicht zu '{source}' -- dort waere "
                "er wirkungslos.")
    if source == "trajectory":
        try:
            horizon = int(raw_horizon)
        except ValueError:
            horizon = None
        if horizon not in BOOTSTRAP_HORIZON_ROUNDS_ALLOWED:
            raise ValueError(
                f"MOSAIC_BOOTSTRAP_HORIZON_ROUNDS={raw_horizon!r} ungueltig -- bei "
                f"MOSAIC_BOOTSTRAP_SOURCE=trajectory Pflicht, erlaubt {BOOTSTRAP_HORIZON_ROUNDS_ALLOWED}.")
        if raw_mix and raw_conf:
            raise ValueError(
                "MOSAIC_BOOTSTRAP_TRAJ_MIX und MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE sind beide gesetzt -- "
                "die Kombination ist nicht registriert (PREREG_v35_window.md par.19.3/par.19.5).")
        mix = (_parse_number(raw_mix, "MOSAIC_BOOTSTRAP_TRAJ_MIX", low=0.0, high=1.0,
                             low_inclusive=True, rule="endliche Zahl in [0, 1]")
               if raw_mix else None)
        conf = (_parse_number(raw_conf, "MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE", low=0.0, high=None,
                              low_inclusive=False, rule="endliche Zahl > 0 (Q-Abstand)")
                if raw_conf else None)
        return ("trajectory", horizon, {"mix": mix, "conf_scale": conf})
    if source == "trajectory_lambda":
        traj_lambda = _parse_number(raw_lambda or BOOTSTRAP_TRAJ_LAMBDA_DEFAULT,
                                    "MOSAIC_BOOTSTRAP_TRAJ_LAMBDA", low=0.0, high=1.0,
                                    low_inclusive=True, rule="endliche Zahl in [0, 1]")
        return ("trajectory_lambda", traj_lambda, {"opponent": opponent})
    # source == "margin"
    scale = _parse_number(raw_scale, "MOSAIC_BOOTSTRAP_MARGIN_SCALE", low=0.0, high=None,
                          low_inclusive=False,
                          rule="bei MOSAIC_BOOTSTRAP_SOURCE=margin Pflicht, endliche Zahl > 0 (Punkte)")
    return ("margin", scale, {})


def _bootstrap_variant_config() -> dict | None:
    """Die Varianten-Parameter fuer die BAUSCHLEIFE (corpus_dataset.py), aus
    derselben Pruefstelle wie die Schluessel (`_bootstrap_source_config`).

    None ohne Quelle, sonst {"source", "horizon", "mix", "conf_scale",
    "traj_lambda", "opponent", "margin_scale"} mit None fuer alles, was zur
    Quelle nicht gehoert; Zahlen als float (die Marker tragen den kanonischen
    String)."""
    config = _bootstrap_source_config()
    if config is None:
        return None
    source, param, extras = config
    out = {"source": source, "horizon": None, "mix": None, "conf_scale": None,
           "traj_lambda": None, "opponent": False, "margin_scale": None}
    if source == "trajectory":
        out["horizon"] = param
        out["mix"] = None if extras["mix"] is None else float(extras["mix"])
        out["conf_scale"] = None if extras["conf_scale"] is None else float(extras["conf_scale"])
    elif source == "trajectory_lambda":
        out["traj_lambda"] = float(param)
        out["opponent"] = bool(extras["opponent"])
    else:
        out["margin_scale"] = float(param)
    return out


def td_lambda_from_env() -> float:
    """`MOSAIC_TD_LAMBDA` (par.19.4, Arm v35-b14): Gewicht des Bootstraps im
    TD-Blend `TD_LAMBDA * Bootstrap + (1 - TD_LAMBDA) * Ausgang`, bis
    2026-10-08 die Konstante `neural_net.TD_LAMBDA = 0.5`.

    Gelesen EINMAL beim Import von `neural_net` (dort `TD_LAMBDA =
    td_lambda_from_env()`); alle Verbraucher (Bauschleife, beide Schluessel,
    train.py, Trainings-Manifest) lesen den Namen von dort und sehen damit
    denselben Wert. Ungesetzt oder leer: `TD_LAMBDA_DEFAULT` (0.5, Bestand
    bitgleich). Sonst endliche Zahl in (0, 1]; 0 ist verboten, weil
    `train.py::_destretch_wdl_target` durch TD_LAMBDA teilt. Harter Fehler
    statt stillem Rueckfall.
    """
    import os
    raw = (os.environ.get("MOSAIC_TD_LAMBDA") or "").strip()
    if not raw:
        return TD_LAMBDA_DEFAULT
    return float(_parse_number(raw, "MOSAIC_TD_LAMBDA", low=0.0, high=1.0, low_inclusive=False,
                               rule="endliche Zahl in (0, 1]"))


def td_lambda_marker(td_lambda: float) -> str | None:
    """Marker-Teil fuer BEIDE Schluessel: None beim Bestandswert 0.5, sonst
    "tdlambda<wert>" (kanonisch). Bekommt den WIRKSAMEN Wert (den Namen
    `TD_LAMBDA` aus `neural_net`), nicht die Umgebung -- so koennen Marker und
    Bauschleife nicht auseinanderlaufen. Der Wert steht zusaetzlich seit jeher
    als `str(TD_LAMBDA)` im Material; der Marker macht die Abweichung vom
    Bestand im Material lesbar, wie bei den anderen Arm-Knoepfen."""
    if float(td_lambda) == TD_LAMBDA_DEFAULT:
        return None
    return "tdlambda" + _canonical_number(td_lambda)


def _bootstrap_trajectory_horizon_key() -> int | None:
    """Obergrenze k des Trajektorien-Bootstraps fuer BEIDE Cache-Schluessel.

    `PREREG_v35_window.md` par.12a (Nutzer-Entscheid 2026-10-05, Arm v35-b03):
    die Quelle des TD-Bootstraps im WDL-Wertziel wird vom gespeicherten
    Netz-Rollout (`bootstrap_value`) auf den Suchwert `root_q` des ersten
    spaeteren Records derselben Seite mindestens k Runden spaeter umgestellt
    (`trajectory_bootstrap.trajectory_bootstrap_lookup`). Das aendert
    `values_wdl` im BLOCK, also beide Schluessel
    (`feedback_feature_knob_belongs_in_both_cache_keys`).

    Rueckgabe: `None` = nicht diese Quelle (Bestand oder 'margin'), sonst k.
    Pruefung und harte Fehler: `_bootstrap_source_config`.
    """
    config = _bootstrap_source_config()
    return config[1] if config is not None and config[0] == "trajectory" else None


def _bootstrap_margin_scale_key() -> str | None:
    """Skala b des Margen-Bootstraps fuer BEIDE Cache-Schluessel.

    `PREREG_v35_window.md` par.14 (Arm v35-b04): Bootstrap im WDL-Wertziel ist
    sigmoid(Endmarge / b) mit der realisierten Endmarge aus Sicht des Ziehers
    (`trajectory_bootstrap.margin_bootstrap_value`). Aendert `values_wdl` im
    BLOCK, also beide Schluessel.

    Rueckgabe: `None` = nicht diese Quelle, sonst b als kanonischer String
    (Marker `bootstrapmargin_b<b>_v1`). Pruefung: `_bootstrap_source_config`.
    """
    config = _bootstrap_source_config()
    return config[1] if config is not None and config[0] == "margin" else None


def _bootstrap_trajectory_suffix_key() -> str:
    """Marker-Zusatz der Quelle 'trajectory' fuer BEIDE Cache-Schluessel.

    `PREREG_v35_window.md` par.19.3 (Arm v35-b13, `MOSAIC_BOOTSTRAP_TRAJ_MIX`)
    und par.19.5 (Arm v35-b15, `MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE`): beide
    aendern `values_wdl` im BLOCK. Der Zusatz steht im Marker
    `bootstraptraj_h<k><zusatz>_v1` VOR "_v1": "" (b03/b05/b06, Marker
    unveraendert), "_mix<m>" oder "_conf<s>" (kanonische Zahl). Ausserhalb
    der Quelle 'trajectory' immer "". Pruefung: `_bootstrap_source_config`.
    """
    config = _bootstrap_source_config()
    if config is None or config[0] != "trajectory":
        return ""
    extras = config[2]
    if extras["mix"] is not None:
        return "_mix" + extras["mix"]
    if extras["conf_scale"] is not None:
        return "_conf" + extras["conf_scale"]
    return ""


def _bootstrap_trajectory_lambda_key() -> str | None:
    """Marker-Teil der Quelle 'trajectory_lambda' fuer BEIDE Cache-Schluessel.

    `PREREG_v35_window.md` par.19.1 (Arm v35-b11): Bootstrap im WDL-Wertziel
    ist das lambda-gewichtete Mittel der Suchwerte aller spaeteren eigenen
    Stuetzstellen (`trajectory_bootstrap.trajectory_lambda_values`), par.19.2
    (Arm v35-b12) zusaetzlich die Gegnerstellungen gespiegelt. Aendert
    `values_wdl` im BLOCK, also beide Schluessel.

    Rueckgabe: None = nicht diese Quelle, sonst "l<lambda>" bzw.
    "l<lambda>_opp1" (Marker `bootstraptrajlambda_l<lambda>[_opp1]_v1`).
    Pruefung: `_bootstrap_source_config`.
    """
    config = _bootstrap_source_config()
    if config is None or config[0] != "trajectory_lambda":
        return None
    return "l" + config[1] + ("_opp1" if config[2]["opponent"] else "")


def per_file_cache_key(basename: str, *, value_target_variant: str, encoder: str,
                       conjunction_head: bool, bootstrap_native: bool) -> str:
    """Schluessel EINER Korpusdatei (PREREG_cache_build_time.md par.6, Hebel 4).

    EIGENER NAMENSRAUM, nicht der Fenster-Schluessel: dieser hier deckt nur
    ab, was den INHALT eines Datei-Blocks bestimmt. Was das FENSTER bestimmt
    -- welche Dateien, das Traeger-Manifest als Ganzes, der Train/Val-Split --
    steht bewusst NICHT drin, denn genau daran haengt heute jeder Datei-Block
    unnoetig mit: ein neues Fenster verwirft sonst Bloecke, deren Inhalt sich
    nicht geaendert hat.

    **DER TRAEGERSTATUS IST SEIT 2026-08-31 NICHT MEHR TEIL DES SCHLUESSELS**
    (Nutzer-Auftrag). Vorher war er "die eine Stelle, an der das Manifest doch
    einfliesst" -- und genau das war teuer: er aenderte den BLOCK-INHALT
    (`pol_w` wurde beim Bauen auf 0 gesetzt), also entwertete jeder
    Traeger-Wechsel den gesamten Bestand. Beim v23-Fenster waeren das rund
    2.600 Bloecke gewesen, obwohl sich an den DATEN nichts aendert.

    Neue Aufteilung: der Block ist **traegeragnostisch** -- er traegt `pol_w`
    nach der datei-inhaerenten Regel (Drafting/Tiling/`policy_target_valid`)
    --, und die Traeger-Maske wird beim ZUSAMMENFUEGEN des Fensters angewandt
    (`build_cache_parallel.merge(..., mask_parts=...)`). Damit ist der
    Traegerstatus eine FENSTER-Eigenschaft wie die Dateiliste, also genau
    dort, wo der Kopf dieser Datei ihn ohnehin verortet.

    **Warum das den Bestand NICHT entwertet:** das Material behaelt das
    Literal `|carrier=1`. Alle vorhandenen Bloecke sind ohne Manifest gebaut,
    also mit `carrier=1` -- ihre Hashes bleiben exakt dieselben. Ein etwaiger
    Alt-Block mit `carrier=0` traegt einen Hash, den diese Funktion nie mehr
    erzeugt: er wird nicht falsch gelesen, sondern gar nicht mehr adressiert.

    `bootstrap_native` (2026-08-27, PREREG_heuristic_v2_long_rows.md par.3b.3
    Punkt 3) ist nach derselben Regel gebaut: der AUFGELOESTE Status DIESER
    Datei, nicht die Blockliste. Er ist eine ZIELDEFINITION -- er entscheidet,
    ob in `values_wdl` der rohe oder der Platt-entstauchte Bootstrap steckt,
    und das wird VOR dem Caching eingerechnet. Ohne ihn traefe ein Lauf nach
    der Semantik-Umkehr ("nativ ist Default") still die Bestands-Bloecke mit
    den ENTSTAUCHTEN hv2-Zielen. Bildung beim Aufrufer:
    `not basename.startswith(neural_net.LEGACY_STRETCHED_PREFIXES)`.

    Alles Uebrige ist per Datei wirksam und steht darum hier: Schema- und
    Aktionszahlen, Sharpen-Exponent, TD_LAMBDA, Value-Ziel-Variante, Encoder,
    Konjunktions-/Reachability-Ziele, Bitpacking, ignore_ptv, f32,
    Arm-K-Bootstrap-Kohaerenz.
    """
    # LOKALE Importe wie in `MosaicDataset.__init__` (dort Zeile "from config
    # import INPUT_SIZE"): `INPUT_SIZE` haengt an der Engine-Konfiguration und
    # ist modulweit bewusst nicht gebunden, `hashlib` wird ebenfalls erst dort
    # geholt. Beides hier nachzubauen statt oben zu importieren haelt die
    # Bindungszeit identisch -- sonst koennte der Schluessel eine andere
    # INPUT_SIZE sehen als die Bauschleife.
    from config import INPUT_SIZE, FEATURE_FORMULA_VERSION
    import hashlib
    import os
    # LAZY, nicht oben: `neural_net` re-exportiert diesen Namen, ein Import auf
    # Modulebene waere ein Ringschluss. Und er ist inhaltlich richtig hier --
    # so sieht der Schluessel dieselben Werte wie die Bauschleife im selben
    # Prozess, statt einen Stand von der Importzeit einzufrieren.
    import neural_net as _nn

    NUM_ACTIONS = _nn.NUM_ACTIONS
    VALUE_SCHEMA_VERSION = _nn.VALUE_SCHEMA_VERSION
    POLICY_TARGET_SHARPEN_EXPONENT = _nn.POLICY_TARGET_SHARPEN_EXPONENT
    TD_LAMBDA = _nn.TD_LAMBDA
    REACH_K1_MIN_ROUND = _nn.REACH_K1_MIN_ROUND
    REACH_BUF_CAP = _nn.REACH_BUF_CAP
    reach_target_k1_active = _nn.reach_target_k1_active
    reach_buffer_mode = _nn.reach_buffer_mode
    _IGNORE_PTV = _nn._IGNORE_PTV
    import corpus_dataset as _cd
    _cache_f32_active = _cd._cache_f32_active

    material = (
        "filecache_v1|" + basename
        + "|" + str(INPUT_SIZE) + "|" + str(NUM_ACTIONS) + "|" + str(VALUE_SCHEMA_VERSION)
        + "|" + str(POLICY_TARGET_SHARPEN_EXPONENT) + "|" + str(TD_LAMBDA)
        + "|" + str(value_target_variant) + "|" + str(encoder)
        # Ablations-Schalter der Spezialfeld-Kanaele (PREREG_special_tile_yield.md
        # par.6 P1, Arm v29-b02). MUSS im Schluessel stehen: b02 trainiert auf
        # DEMSELBEN Fenster und DEMSELBEN Seed wie b01, nur mit zwei Kanaelen
        # weniger. Ohne den Schluesselanteil lieferten die Bloecke aus dem
        # b01-Lauf stillschweigend die eingeschalteten Kanaele, und die Ablation
        # haette exakt denselben Eingang gemessen wie der Arm, gegen den sie
        # antritt. Dieselbe Fehlerklasse hat am 2026-09-09 2.680 tote Bloecke
        # erzeugt (docs/pitfalls.md). Nur angehaengt, wenn gesetzt -- so bleibt
        # der Hash aller vorhandenen Bloecke unveraendert.
        + ("|specialoff" if _special_planes_off_key() else "")
        # Literal statt Parameter (2026-08-31, Begruendung im Kopf): haelt den
        # Hash aller vorhandenen Bloecke stabil, waehrend der Traegerstatus aus
        # dem Block-Inhalt herauswandert.
        + "|carrier=1"
        + "|bsnative=" + ("1" if bootstrap_native else "0")
        + "|rounds_v1+own_v1"
    )
    if encoder == "2d":
        # Die Kanalzahl bestimmt den INHALT jedes Datei-Blocks (Breite des
        # planes-Datasets UND, seit den Spezialfeld-Kanaelen, das Packlayout).
        # Sie stand bis 2026-08-27 in KEINER Key-Komponente -- `str(encoder)`
        # ist nur "2d" und bleibt bei 77 wie bei 79 gleich. Ein 79er-Lauf
        # haette damit die 77er-Bloecke des Bestands wiederverwendet.
        material += f"|planes{_nn.NUM_PLANES_CHANNELS}_bin{_nn.NUM_BINARY_PLANES_CHANNELS}"
    if conjunction_head:
        material += "|conj_v2"
        if reach_target_k1_active():
            material += f"|reachk1_r{REACH_K1_MIN_ROUND}_v1"
            if reach_buffer_mode():
                material += f"|reachbuf_cap{REACH_BUF_CAP}_v1"
    material += "|nopack_v1" if os.environ.get("MOSAIC_CACHE_NOPACK") == "1" else "|bitpack_v1"
    if _IGNORE_PTV:
        material += "|ignore_ptv_v1"
    if _cache_f32_active():
        material += "|f32_v1"
    # Arm K (PREREG_heuristic_v2_long_rows.md par.3b.3): wirkt je Record im
    # WDL-Ziel, also je DATEI -- gehoert damit in diesen Namensraum genauso
    # wie in den Fenster-Schluessel. Gleiche Quelle wie die Bauschleife
    # (corpus_dataset), damit Schluessel und Bauweg nicht auseinanderlaufen.
    _bs_coherence = _cd._bootstrap_coherence_mode()
    if _bs_coherence != "off":
        material += "|bscoh_" + _bs_coherence + "_v1"
    # par.12.1 Arm b04: nur ANHAENGEN, wenn vom Bestand abweichend -- sonst
    # waeren alle vorhandenen Bloecke entwertet.
    _mts = _moon_target_source_key()
    if _mts != "label":
        material += f"|moontarget_{_mts}_v1"
    # Merkmals-FORMEL und Merkmals-QUELLE (2026-09-17, Nutzer-Entscheid Weg (1)
    # aus PREREG_rust_data_layer.md par.9a). UNBEDINGT angehaengt, anders als die
    # Arm-Schalter oben -- und das ist der gewollte Preis: alle vorhandenen
    # Bloecke sind unter dem neuen Schluessel nicht mehr adressierbar. Der Neubau
    # faellt fuer den Arm v29-b07 mit dem INPUT_SIZE-Wechsel ohnehin an.
    #
    # Warum BEIDE Teile: die VERSION trennt alte von neuer Formel (ein Block aus
    # der Zeit vor dem A2-Phantom-Fix traegt andere `cell_reachable_mask`- und
    # `col_f_max`-Werte), die QUELLE trennt die beiden Bauer, die auf Alt-Records
    # seit dem 2026-09-12 nicht mehr bit-identisch sind (`_features_from_rust_key`).
    # Beides gehoert in BEIDE Schluessel: der Block traegt die Planes, das Fenster
    # den Monolithen (`feedback_feature_knob_belongs_in_both_cache_keys`).
    material += "|featfmt_" + str(FEATURE_FORMULA_VERSION)
    material += "|featsrc_rust" if _features_from_rust_key() else "|featsrc_record"
    # E2-Arm: Zusatzfeld `final_margin` im Block (`_final_margin_key`). Nur
    # ANGEHAENGT, wenn gesetzt -- der Hash jedes vorhandenen Blocks bleibt.
    if _final_margin_key():
        material += "|finalmargin_v1"
    # E4-Arm: Angebots-Bedarfs-Block im Flachvektor (`_supply_demand_key`). Nur
    # ANGEHAENGT, wenn gesetzt -- der Hash jedes vorhandenen Blocks bleibt.
    if _supply_demand_key():
        material += "|supplydemand_v1"
    # Klasse S/W (PREREG_asymmetric_selfplay.md par.3/par.3a): Policy-Masken der
    # asymmetrischen Records. Nur ANGEHAENGT, wenn gesetzt -- der Hash jedes
    # vorhandenen Blocks bleibt.
    _aggr_eps = _aggr_own_q_eps_key()
    if _aggr_eps is not None:
        material += "|aggrownq_eps" + _aggr_eps + "_v1"
    if _mask_dice_trigger_key():
        material += "|maskdicetrigger_v1"
    # par.5d: Wertmaske der Wuerfelphase (Zusatzfeld `value_weights` im Block).
    if _mask_dice_phase_value_key():
        material += "|maskdicephasevalue_v1"
    # par.12a (Arm v35-b03): Bootstrap-Quelle im WDL-Ziel aus der echten
    # Trajektorie. Nur ANGEHAENGT, wenn gesetzt -- der Hash jedes vorhandenen
    # Blocks bleibt.
    # par.19.3/par.19.5 (Arme v35-b13/b15): Zusatz `_mix<m>` bzw. `_conf<s>`
    # vor "_v1"; ohne diese Knoepfe leer, der b03-Marker bleibt.
    _traj_horizon = _bootstrap_trajectory_horizon_key()
    if _traj_horizon is not None:
        material += ("|bootstraptraj_h" + str(_traj_horizon)
                     + _bootstrap_trajectory_suffix_key() + "_v1")
    # par.19.1/par.19.2 (Arme v35-b11/b12): lambda-Mittel ueber den echten Pfad.
    # Nur ANGEHAENGT, wenn gesetzt.
    _traj_lambda = _bootstrap_trajectory_lambda_key()
    if _traj_lambda is not None:
        material += "|bootstraptrajlambda_" + _traj_lambda + "_v1"
    # par.14 (Arm v35-b04): Margen-Bootstrap, Skala b im Marker. Nur ANGEHAENGT,
    # wenn gesetzt.
    _margin_scale = _bootstrap_margin_scale_key()
    if _margin_scale is not None:
        material += "|bootstrapmargin_b" + _margin_scale + "_v1"
    # par.19.4 (Arm v35-b14): MOSAIC_TD_LAMBDA. Der wirksame Wert steht seit
    # jeher als str(TD_LAMBDA) oben im Material; der Marker kommt nur bei
    # Abweichung vom Bestand 0.5 dazu, der Hash jedes vorhandenen Blocks bleibt.
    _td_marker = td_lambda_marker(TD_LAMBDA)
    if _td_marker is not None:
        material += "|" + _td_marker + "_v1"
    return hashlib.md5(material.encode()).hexdigest()[:12]
