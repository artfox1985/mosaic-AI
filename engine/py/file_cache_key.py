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


def per_file_cache_key(basename: str, *, value_target_variant: str, encoder: str,
                       conjunction_head: bool, policy_carrier: bool,
                       bootstrap_native: bool) -> str:
    """Schluessel EINER Korpusdatei (PREREG_cache_build_time.md par.6, Hebel 4).

    EIGENER NAMENSRAUM, nicht der Fenster-Schluessel: dieser hier deckt nur
    ab, was den INHALT eines Datei-Blocks bestimmt. Was das FENSTER bestimmt
    -- welche Dateien, das Traeger-Manifest als Ganzes, der Train/Val-Split --
    steht bewusst NICHT drin, denn genau daran haengt heute jeder Datei-Block
    unnoetig mit: ein neues Fenster verwirft sonst Bloecke, deren Inhalt sich
    nicht geaendert hat.

    DIE EINE STELLE, an der das Manifest doch einfliesst, ist `policy_carrier`
    -- der AUFGELOESTE Traegerstatus DIESER Datei (`_is_policy_carrier`), nicht
    der Manifest-Inhalt. Zwei Manifeste, die fuer diese Datei dasselbe
    ergeben, duerfen denselben Block benutzen; eines, das den Status kippt,
    darf es nicht. Wer hier den Manifest-Inhalt einsetzt, baut den heutigen
    Zustand nach; wer den Status weglaesst, baut die stille Falle aus par.6.

    Der Aufrufer muss `policy_carrier` mit `_is_policy_carrier` bilden (nicht
    von Hand), sonst koennen Schluessel und Bauschleife auseinanderlaufen.

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
    from config import INPUT_SIZE
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
        + "|carrier=" + ("1" if policy_carrier else "0")
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
    return hashlib.md5(material.encode()).hexdigest()[:12]
