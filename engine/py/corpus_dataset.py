# -*- coding: utf-8 -*-
"""Die KORPUS-Pipeline: aus Partiedateien wird ein Trainingsdatensatz.

Herausgeloest aus `neural_net.py` am 2026-08-27. Die Datei hiess "neural_net"
und trug zu 40 Prozent etwas anderes: `MosaicDataset` allein war 1.161 von
2.933 Zeilen. Der Name versprach die Netze, drin lag der Datenweg.

ABHAENGIGKEIT EINSEITIG: dieses Modul importiert aus `neural_net`, nie
umgekehrt. Geprueft vor dem Schnitt -- die Netze benutzen nichts aus der
Datenseite, `MosaicDataset` benutzt kein Netz. Ein Rueckexport in
`neural_net` waere bequemer fuer alte Aufrufstellen, haette aber einen
Importzyklus erzeugt, der nur wegen der Reihenfolge im Dateikoerper haelt.

Verhaltensneutral: der Rumpf ist zeilenweise der bisherige. Belegt gegen
denselben Trainingslauf wie B (`--train-file-limit 6 --epochs 2 --seed 4242`),
dessen `epoch_history` bitgleich bleiben muss.
"""

import os
import glob
from corpus_io import load_records_fh as _load_records_fh
import re
import json
import math
import pickle
import statistics
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from file_cache_key import per_file_cache_key  # noqa: F401
from reach_target import (REACH_ATOMS, REACH_K1_MIN_ROUND, REACH_BUF_CAP,
                          reach_columns, reach_target_k1_active,
                          reach_buffer_mode, reach_buffer_columns)
from config import (NUM_ACTIONS, HIDDEN_SIZE, OWNERSHIP_TARGETS,
                    CONJUNCTION_TARGETS, CONJUNCTIONS_PER_PLAYER,
                    POINTS_DIST_BINS)

from neural_net import (  # einseitig, siehe Modulkopf
    DESTRETCH_A,
    DESTRETCH_B,
    NUM_BINARY_PLANES_CHANNELS,
    NUM_PLANES_CHANNELS,
    PLANES_BINARY_BITS,
    PLANES_PACKED_ROW_BYTES,
    PLANES_RAW_VALUE_BYTES,
    POLICY_TARGET_SHARPEN_EXPONENT,
    RANKING_TOPK,
    TD_LAMBDA,
    VALUE_SCALE,
    VALUE_SCHEMA_VERSION,
    VALUE_TARGET_VARIANTS,
    LEGACY_STRETCHED_PREFIXES,
    V20_CARRIER_SHORTCUT_PREFIXES,
    _IGNORE_PTV,
    _conjunctions_from_dome,
    _ownership_from_dome,
    action_to_id,
    state_to_planes,
    state_to_tensor,
)


# Codepflege-Audit 2026-08-27 (Befund-1-Haertung): Merker je Manifest-Pfad,
# damit der Hinweis auf ein FEHLENDES Traeger-Manifest genau einmal je Pfad
# und Prozess im Log steht statt bei jedem Datensatz-Aufbau erneut.
_CARRIER_MANIFEST_NOTICE_SHOWN: set = set()


def _destretch_prob(p: float) -> float:
    """Platt-Streckung einer gestauchten Alt-Kopf-'Wahrscheinlichkeit'."""
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    z = math.log(p / (1.0 - p))
    return 1.0 / (1.0 + math.exp(-(DESTRETCH_A + DESTRETCH_B * z)))


def _cache_f32_active() -> bool:
    """MOSAIC_CACHE_F32: float32 statt float16 fuer states/policies im Cache.

    EINE Quelle fuer Key und Schreibweg -- vorher las nur der Schreibweg den
    Knopf, und der Key wusste nichts davon (Befund 2026-08-26).
    """
    return os.environ.get("MOSAIC_CACHE_F32") == "1"


def _is_policy_carrier(basename, carrier_set, carrier_prefixes, v20_wdl_generator):
    """Entscheidet, ob eine Self-Play-Datei Policy-Ziele traegt (pol_w>0-Vorfrage).

    Schema 17 (v20) hatte hier einen Kurzschluss: JEDE Datei eines
    WDL-Generators trug automatisch Policy, egal ob sie im Manifest gelistet
    war -- fuer v20 harmlos (dort SOLLTEN alle v19wdl-Sockel-Dateien tragen),
    fuer v21 falsch (nur ein Teilsatz der v19wdl-Dateien soll Traeger sein).

    `v20_wdl_generator` traegt genau diesen eingefrorenen Kurzschluss und
    kommt aus `V20_CARRIER_SHORTCUT_PREFIXES`. Bis 2026-08-27 war das
    dieselbe Groesse wie das Entstauchungs-Flag `bootstrap_native`; seit der
    Semantik-Umkehr dort (nativ ist Default, siehe
    `LEGACY_STRETCHED_PREFIXES`) sind es ZWEI Fragen mit zwei Konstanten.
    Wer sie wieder zusammenlegt, macht mit dem umgedrehten Flag still ALLE
    Dateien zu Policy-Traegern.

    - `carrier_set is None` (kein Manifest gefunden): JEDE Datei traegt
      (Bestandsverhalten, manifest-unabhaengig).
    - `carrier_prefixes is None` (Manifest OHNE das neue Feld = v20-Schema):
      Alt-Verhalten EXAKT erhalten, inkl. WDL-Generator-Kurzschluss --
      Rueckwaerts-Kompatibilitaet/bit-identische v20-Caches sind Pflicht.
    - `carrier_prefixes` vorhanden (auch als leere Liste; v21+-Schema): der
      Kurzschluss wird NICHT mehr benutzt. Traeger ist nur,
      wer im `carrier_set` gelistet ist ODER dessen Basename mit einem der
      Praefixe beginnt (str.startswith -- "selfplay_v20wdl_" matcht NICHT
      "selfplay_v20wdlsw_...", der Unterstrich ist Teil des Praefixes).
    """
    if carrier_set is None:
        return True
    if carrier_prefixes is None:
        return v20_wdl_generator or basename in carrier_set
    return basename in carrier_set or basename.startswith(tuple(carrier_prefixes))


def _ranking_topk_pairs(action_ids, qs, k):
    """Waehlt bis zu `k` (Aktions-ID, Q)-Paare aus `zip(action_ids, qs)` --
    bei <=k Paaren werden ALLE unveraendert (Original-Reihenfolge)
    uebernommen, bei >k Paaren die `k` mit der GROESSTEN Abweichung vom
    Median-Q (siehe RANKING_CACHE_FIELDS-Kommentar oben: das sind die
    informativsten Paare fuer den |dq|>Margin-Filter des Ranking-Loss,
    nicht die ersten `k` in Sucheihenfolge). Reine Hilfsfunktion, isoliert
    unit-testbar."""
    n = len(action_ids)
    if n <= k:
        return list(zip(action_ids, qs))
    median_q = statistics.median(qs)
    order = sorted(range(n), key=lambda i: abs(qs[i] - median_q), reverse=True)[:k]
    return [(action_ids[i], qs[i]) for i in order]


def _final_ownership_by_game(game_data) -> dict:
    """game_id -> (own_p0, own_p1, conj_p0, conj_p1) aus dem LETZTEN Record des
    Spiels. Das `dome_grid` aendert sich nach Abschluss der Tiling-Phase nicht
    mehr (Nachweis siehe tools/scoring_tile_impact.py), der letzte Record
    traegt also den finalen Kuppelzustand. Unvollstaendige Spiele -> None
    (Ziel wird dann als -1 markiert und im Loss maskiert).

    Die Konjunktionen (`_conjunctions_from_dome`) kommen aus demselben
    Endbrett und derselben `completed`-Pruefung -- sie werden IMMER berechnet;
    ob sie ins Ziel wandern, entscheidet `MosaicDataset.own_targets`."""
    last_by_gid = {}
    for step in game_data:
        last_by_gid[step["game_id"]] = step
    out = {}
    for gid, last in last_by_gid.items():
        if not last.get("completed"):
            out[gid] = None
            continue
        players = last["state"]["players"]
        out[gid] = (_ownership_from_dome(players[0]["dome_grid"]),
                    _ownership_from_dome(players[1]["dome_grid"]),
                    _conjunctions_from_dome(players[0]["dome_grid"]),
                    _conjunctions_from_dome(players[1]["dome_grid"]))
    return out


# ── Bitpacking planes/masks (RAM-Optimierung v21, 2026-08-07) ──────────────
# PREREG_v21_window.md, Abschnitt "RAM-Voraussetzung": das ~4,8-Mio-Zustaende-
# Fenster passt im heutigen Cache-Format (planes uint8 [76,6,6]=2.736 B,
# masks uint8 [406]=406 B) nicht mehr komfortabel in 32 GB RAM. `masks` ist
# STRIKT binaer, `planes` war es bis 2026-08-27 ebenfalls --
# np.packbits/np.unpackbits packt 8 Bits verlustfrei in 1 Byte.
#
# SEITHER GILT DAS NUR NOCH FUER DIE ERSTEN `NUM_BINARY_PLANES_CHANNELS`
# planes-Kanaele: die zwei Spezialfeld-Kanaele tragen Werte 1..6 bzw. 0..3.
# Fuer sie ist `_pack_planes` (unten) zustaendig, NICHT `_pack_bits`.
#
# LAYOUT (exakt): pro Sample wird das Feld zuerst C-kontiguos auf 1D
# geflacht (planes [79,6,6] -> [2844], masks ist bereits 1D [406]),
# anschliessend `np.packbits(..., axis=-1)` -- NumPy-Standard-Bitreihenfolge
# 'big': Bit-Index 0 des flachen Arrays landet im HOECHSTWERTIGEN Bit (0x80)
# des ERSTEN Ausgabe-Bytes. masks: 406 Bit / 8 = 50,75 -> 51 Byte (letztes
# Byte hat 2 Padding-Nullbits). Entpacken mit `np.unpackbits(..., count=K)`
# schneidet das Padding exakt wieder ab -- `count` ist deshalb
# Pflichtparameter, kein optionales Detail.
#
# planes ZWEITEILIG (seit 2026-08-27): die ersten 77*36 = 2.772 Bit werden
# gepackt (-> 346,5 -> 347 Byte, letztes Byte mit 4 Padding-Nullbits), die
# restlichen 2*36 = 72 Werte haengen ROH (uint8) dahinter -> 419 Byte je
# Sample. Die Grenzkonstanten stehen in `neural_net.py`
# (PLANES_BINARY_BITS / PLANES_PACKED_BINARY_BYTES / PLANES_RAW_VALUE_BYTES /
# PLANES_PACKED_ROW_BYTES) und werden von beiden Seiten benutzt.
def _pack_bits(arr: np.ndarray) -> np.ndarray:
    """Bitpackt ein striktes 0/1-uint8-Array entlang der letzten Achse.
    [..., K] -> [..., ceil(K/8)]. Siehe Kopf-Kommentar fuer das exakte
    Layout (Bitreihenfolge 'big', Padding-Konvention)."""
    return np.packbits(arr, axis=-1)


def _pack_planes(arr: np.ndarray) -> np.ndarray:
    """Packt einen planes-Block [N,C,6,6] uint8 -> [N,PLANES_PACKED_ROW_BYTES].

    NICHT einfach `_pack_bits` auf alles: `np.packbits` liest jeden Wert != 0
    als gesetztes Bit. Seit den zwei Spezialfeld-Kanaelen (Ertrag 1..6,
    Abstand 0..3, `neural_net.py::state_to_planes`) ist der Block NICHT mehr
    durchweg binaer -- ein Voll-Pack haette diese Werte still auf 0/1
    plattgedrueckt, ohne Fehlermeldung und ohne Absturz.

    Aufteilung: die ersten `NUM_BINARY_PLANES_CHANNELS` Kanaele werden wie
    bisher bitgepackt, die wertetragenden Kanaele dahinter bleiben ROH
    (uint8). Umkehrfunktion: `neural_net.py::unpack_planes_batch` -- beide
    Seiten benutzen dieselben Grenzkonstanten aus `neural_net`.
    """
    n = len(arr)
    assert arr.shape[1:] == (NUM_PLANES_CHANNELS, 6, 6), (
        f"_pack_planes erwartet [N,{NUM_PLANES_CHANNELS},6,6], bekam {arr.shape}")
    flat = arr.reshape(n, -1)
    binary_part = flat[:, :PLANES_BINARY_BITS]
    # Waechter statt Vertrauen: EIN voller uint8-Reduktionslauf (Sekunden auf
    # dem vollen Korpus) gegen einen stillen Datenfehler, der sonst erst
    # Messungen spaeter auffiele. Feuert, sobald jemand einen wertetragenden
    # Kanal VOR die Grenze legt.
    if n and int(binary_part.max()) > 1:
        raise ValueError(
            f"_pack_planes: die ersten {NUM_BINARY_PLANES_CHANNELS} planes-Kanaele muessen "
            f"strikt binaer sein, gefunden wurde der Wert {int(binary_part.max())}. "
            "Ein wertetragender Kanal gehoert HINTER NUM_BINARY_PLANES_CHANNELS "
            "(neural_net.py), sonst drueckt np.packbits ihn still auf 0/1.")
    packed = _pack_bits(binary_part)
    if PLANES_RAW_VALUE_BYTES:
        packed = np.concatenate([packed, flat[:, PLANES_BINARY_BITS:]], axis=-1)
    assert packed.shape[1] == PLANES_PACKED_ROW_BYTES, (
        f"_pack_planes: Zeilenbreite {packed.shape[1]} != PLANES_PACKED_ROW_BYTES "
        f"{PLANES_PACKED_ROW_BYTES} -- Grenzkonstanten und Packen laufen auseinander")
    return packed


def _resolve_planes_h5_path(cache_path_h5: str) -> str:
    """DIAGNOSE-Override (2026-07-31, Task #11 Phase 2, fs_2d_s1-Absturz-
    Untersuchung): wenn `MOSAIC_PLANES_H5_DIR` gesetzt ist, wird der lazy
    Planes-HDF5-Handle (`MosaicDataset._open_planes_h5`) aus DIESEM Ordner
    statt aus `cache_path_h5`s eigentlichem Ordner geoeffnet (gleicher
    Dateiname, nur andere Directory) -- Ausschlusstest, ob ein
    stundenlang offen gehaltener h5py-Handle auf eine OneDrive-synchronisierte
    Datei (`data/` liegt unter OneDrive, siehe Memory
    "OneDrive-Dateiverschwinde-Vorfaelle") die stillen Abstuerze verursacht.
    Standardverhalten (Env-Var NICHT gesetzt) ist UNVERAENDERT: `cache_path_h5`
    selbst. NUR die Planes-Datei ist betroffen -- die uebrigen (Flach-)Felder
    bleiben auf dem regulaeren `data_dir`-Pfad, da nur der 2D-Pfad je
    abgestuerzt ist."""
    override_dir = os.environ.get("MOSAIC_PLANES_H5_DIR")
    if not override_dir:
        return cache_path_h5
    resolved = os.path.join(override_dir, os.path.basename(cache_path_h5))
    print(f"⚠️  DIAGNOSE-Override MOSAIC_PLANES_H5_DIR aktiv: Planes werden aus "
          f"'{resolved}' gelesen statt '{cache_path_h5}'.")
    return resolved


class MosaicDataset(Dataset):
    def __init__(self, data_dir="data", files=None, value_target_variant="default", encoder="flat",
                 conjunction_head=False, cache_path_override=None):
        """`files`: optionale explizite Dateiliste (z.B. ein Train- oder
        Val-Split desselben `data_dir`) -- ohne Angabe werden wie bisher ALLE
        `*.pkl` im Ordner geladen. Der Cache-Key haengt von der tatsaechlich
        uebergebenen Liste ab, Train- und Val-Split bekommen also automatisch
        getrennte HDF5-Caches im selben Ordner.

        `value_target_variant`: siehe VALUE_TARGET_VARIANTS oben (Task #84,
        rtv-Ablation Phase 1) -- steuert, ob/wo der rtv-Override beim
        Target-Bau ignoriert wird. Standard "default" reproduziert exakt das
        Bestandsverhalten.

        `encoder`: Task #11 Phase 2. "flat" (Standard) ist bzgl. `states`/
        `policies`/etc. Bestandsverhalten -- ABER `masks` ist seit der
        Bitpacking-Aenderung (RAM-Optimierung v21, s.u.) NICHT mehr
        byte-identisch zum Vor-v21-Verhalten (Cache-Key/-Inhalt/
        `__getitem__`-Tupel-INHALT aendert sich; die Tupel-FORM/-POSITION
        bleibt gleich). "2d" ergaenzt ein zusaetzliches `planes`-HDF5-Dataset
        ([N,NUM_PLANES_CHANNELS,6,6], `neural_net.py::state_to_planes`) NEBEN
        den bestehenden Datasets -- der Cache-Key bekommt dafuer den Suffix
        "+enc2d_v2" (siehe docs/design_2d_encoder.md Abschnitt 7), ein
        Flach-Cache derselben Dateiliste bleibt davon unberuehrt (eigener
        Dateiname). Speicherformat uint8 statt float32: die ersten
        `NUM_BINARY_PLANES_CHANNELS` Kanaele sind binaer (One-Hot-Belegung +
        0/1-Geometriemasken, siehe design_2d_encoder.md Abschnitt 3/4), die
        zwei Spezialfeld-Kanaele dahinter tragen kleine ganze Zahlen
        (Ertrag 1..6, Abstand 0..3).

        BITPACKING (RAM-Optimierung v21, 2026-08-07, PREREG_v21_window.md
        "RAM-Voraussetzung"): sowohl `masks` (406 Bit/Sample) als auch
        `planes` (NUR "2d") STANDARDMAESSIG gepackt im Cache (siehe
        `_pack_bits`/`_pack_planes` oben fuer das exakte Layout; masks
        406 B -> 51 B, planes 2.844 B -> 419 B = 347 gepackte + 72 rohe
        Bytes). `__getitem__` liefert dann die
        GEPACKTEN Bytes (kuerzere letzte Dimension) statt der entpackten
        Werte -- das Entpacken passiert bewusst NICHT hier pro Sample,
        sondern EINMAL pro Batch in train.py (`unpack_masks_batch`/
        `unpack_planes_batch`, Benchmark-Begruendung dort), NOCH VOR dem
        Device-Move. `self.bitpacked` (bool, nach dem Laden/Bauen gesetzt)
        zeigt Aufrufern, ob dieser Schritt noetig ist. Escape-Hatch
        `MOSAIC_CACHE_NOPACK=1` erzwingt das alte unkomprimierte Format
        (eigener Cache-Key-Suffix, siehe dort) -- dann liefert `__getitem__`
        weiterhin die vollen [406]/[79,6,6]-Werte wie vor v21 und
        `self.bitpacked` ist False."""
        from config import INPUT_SIZE
        import hashlib, time
        import h5py

        if encoder not in ("flat", "2d"):
            raise ValueError(f"Unbekannter encoder={encoder!r} -- erlaubt: 'flat', '2d'")
        self.encoder = encoder
        # Zielbreite des `ownership`-Vektors: Randlayer, optional erweitert um
        # die konjunktiven Kriterien (siehe `_conjunctions_from_dome`). Ueberall
        # unten statt der nackten Konstante benutzt, damit beide Faelle
        # denselben Codepfad nehmen.
        self.conjunction_head = bool(conjunction_head)
        self.own_targets = OWNERSHIP_TARGETS + (CONJUNCTION_TARGETS if conjunction_head else 0)
        # Planes-Ladeverhalten (Task #11 Phase 2, Historie 2026-07-31):
        # STANDARD ist seit 2026-07-31 wieder komplett ins RAM (`_planes_eager_tensor`,
        # siehe `_maybe_load_planes_eager`) -- ein 30s-Vergleichsmesswert auf dem
        # echten 1,3-Mio-Sample-Cache zeigte lazy Pro-Index-h5py-Zugriffe als
        # ~400.000x langsamer (205ms/Sample vs. 0,5µs/Sample), was drei
        # vermeintliche "stille Abstuerze" beim ersten from-scratch-2D-Sweep
        # tatsaechlich erklaert (kein Crash, sondern ein Prozess, der bei
        # Batch=256 ~52s/Batch fuer reine Planes-I/O gebraucht haette und beim
        # Task-Management beendet wurde) -- KEIN Speicherproblem: die Maschine
        # hat 34,3 GB RAM, ein Planes-Split braucht ~3,6 GB. `MOSAIC_PLANES_LAZY=1`
        # schaltet den lazy Pro-Index-HDF5-Zugriff optional wieder ein --
        # NUR fuer echt knappe RAM-Verhaeltnisse gedacht (siehe
        # `_maybe_load_planes_eager`-Docstring fuer die Kosten-Abwaegung).
        self._planes_h5_path = None
        self._planes_h5_file = None
        self._planes_eager_tensor = None
        self._planes_dataset_name = None  # 'planes' oder 'planes_packed' (RAM-Optimierung v21)
        self.bitpacked = False  # True, sobald masks/planes gepackt geladen/gebaut werden (unten)

        if value_target_variant not in VALUE_TARGET_VARIANTS:
            raise ValueError(
                f"Unbekannte value_target_variant={value_target_variant!r} -- "
                f"erlaubt: {VALUE_TARGET_VARIANTS}"
            )

        # Cache-Datei basierend auf Dateiliste + INPUT_SIZE
        # TD_LAMBDA fehlte hier bisher im Hash (Retrain-Sweep-Audit,
        # 2026-07-22): der TD-Bootstrap-Blend wird in `val`/`points_val`
        # VOR dem Caching eingerechnet (siehe unten), ein Lambda-Sweep haette
        # also stillschweigend den Cache der ersten je Dateiliste gebauten
        # Lambda-Variante wiederverwendet und NICHTS gemessen. Jetzt Teil des
        # Keys, gleiche Stelle wie POLICY_TARGET_SHARPEN_EXPONENT.
        # value_target_variant (Task #84) genau dieselbe Falle: der rtv-
        # Override wird ebenfalls VOR dem Caching eingerechnet -- ohne diesen
        # String im Key wuerden "nortv"/"nortv_r1" stillschweigend den
        # "default"-Cache derselben Dateiliste wiederverwenden.
        files = sorted(files) if files is not None else sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
        # MOSAIC_DATA_EXCLUDE (2026-08-07, Fenster-Pinning): Regex, der
        # Dateien VOR Key-Bildung und Training ausschliesst. Noetig, weil
        # data/ waehrend laufender Generierungen WAECHST (Vorfall: der
        # pi_ctrl_s3-Neustart glob-te frisch gelandete v19wdlann-Dateien
        # mit ein -> Cache-Voll-Neubau + kontaminiertes Kontroll-Fenster).
        # Der gefilterte Datei-Liste steckt via `str(files)` ohnehin im
        # Cache-Key -- gleicher Filter => gleicher Key => Cache-Hit.
        _excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
        if _excl:
            _n0 = len(files)
            files = [f for f in files if not re.search(_excl, os.path.basename(f))]
            print(f"🔒 MOSAIC_DATA_EXCLUDE={_excl!r}: {_n0 - len(files)} von {_n0} Dateien ausgeschlossen.")
        # "+rounds_v1" (Task #15 B, 2026-07-28): der Cache fuehrt jetzt zusaetzlich
        # die Rundennummer je Sample mit (fuer rundenselektive Loss-Gewichtung,
        # z.B. --exclude-round5). Der Marker erzwingt einen einmaligen Rebuild
        # aller Alt-Caches, statt sie stillschweigend ohne das Feld zu laden.
        # "+enc2d_v1" (Task #11 Phase 2): NUR im 2D-Modus angehaengt, siehe
        # `encoder`-Doku oben -- der Flach-Modus-Key bleibt dadurch UNVERAENDERT,
        # bestehende Flach-Caches werden also nicht ungueltig.
        # Schema 17: Policy-Traeger-Manifest (v20-Zwei-Klassen-Fenster).
        # Fehlt die Datei -> None = Bestandsverhalten (alle Dateien tragen
        # Policy). Inhalt geht in den Cache-Key ein (anderer Traeger-Satz =
        # anderer Cache).
        # MOSAIC_CARRIER_MANIFEST (2026-08-08, v21-Uebergabe): Dateiname des
        # Traeger-Manifests, Default = v20-Bestand. Inhalt steckt via
        # policy_carrier_set ohnehin im Cache-Key.
        # `carrier_prefixes` (2026-08-08, v21-Fix): additives, OPTIONALES
        # Manifest-Feld -- Liste von Dateinamen-Praefixen, die (zusaetzlich
        # zum `policy_carrier_set`) als Traeger gelten. Ist das Feld
        # VORHANDEN (auch als leere Liste), schaltet `_is_policy_carrier`
        # den `bootstrap_native`-Kurzschluss ab (siehe Funktionskommentar
        # dort) -- notwendig, weil der Kurzschluss fuer v21 ALLE
        # `selfplay_v19wdl_*`-Dateien zu Traegern macht, obwohl nur ein
        # seed-bestimmter Teilsatz tragen soll. Fehlt das Feld (v20-Manifest,
        # kein Rebuild-Zwang): None -> Alt-Verhalten EXAKT erhalten.
        manifest_path = os.path.join(
            data_dir,
            os.environ.get("MOSAIC_CARRIER_MANIFEST", "policy_carrier_manifest_v20.json"))
        policy_carrier_set = None
        carrier_prefixes = None
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as mf:
                _manifest = json.load(mf)
                policy_carrier_set = frozenset(_manifest["policy_carrier_files"])
                if "carrier_prefixes" in _manifest:
                    carrier_prefixes = list(_manifest["carrier_prefixes"])
        else:
            # Codepflege-Audit 2026-08-27, Befund 1: das Fehlen der Datei ist ein
            # STILLER Semantik-Wechsel -- ohne Manifest traegt JEDE Korpusdatei
            # Policy (siehe Kommentarblock oben). Das ist gewolltes
            # Bestandsverhalten, aber es gehoert ins Log, damit ein versehentlich
            # fehlendes/verschobenes Manifest nicht als Normalfall durchgeht.
            # Reiner Hinweis, KEIN Verhaltenswechsel.
            if manifest_path not in _CARRIER_MANIFEST_NOTICE_SHOWN:
                _CARRIER_MANIFEST_NOTICE_SHOWN.add(manifest_path)
                print(f"ℹ️  Traeger-Manifest {manifest_path} nicht gefunden -- "
                      f"Bestandsverhalten: jede Datei traegt Policy", flush=True)

        cache_key_material = (
            str(files) + str(INPUT_SIZE) + str(NUM_ACTIONS) + str(VALUE_SCHEMA_VERSION)
            + str(POLICY_TARGET_SHARPEN_EXPONENT) + str(TD_LAMBDA) + str(value_target_variant)
            + "+rounds_v1+own_v1"
            # "+bsnative_default_v1" (2026-08-27, PREREG_heuristic_v2_long_rows.md
            # par.3b.3 Punkt 3): der bootstrap_native-Status ist eine
            # ZIELDEFINITION je Datei -- er entscheidet, ob `values_wdl` den
            # rohen oder den Platt-entstauchten Bootstrap eingeblendet
            # bekommt, und das passiert VOR dem Caching (gleiche Falle wie
            # TD_LAMBDA und value_target_variant oben). Die Umkehr auf
            # "nativ ist Default" aendert diesen Status fuer JEDE Datei
            # ausserhalb von LEGACY_STRETCHED_PREFIXES; ohne diesen Marker
            # wuerde ein v22-Lauf still den Bestandscache mit den
            # ENTSTAUCHTEN hv2-Zielen weiterbenutzen. Die Blockliste steht
            # mit im Marker, damit auch eine spaetere Aenderung an IHR den
            # Cache entwertet.
            + "+bsnative_default_v1:" + ",".join(sorted(LEGACY_STRETCHED_PREFIXES))
        )
        if policy_carrier_set is not None:
            cache_key_material += "+carriers:" + ",".join(sorted(policy_carrier_set))
        if carrier_prefixes is not None:
            # Eigene Komponente (nicht Teil von "+carriers:"): sonst wuerden
            # zwei Manifeste mit identischem policy_carrier_set aber
            # unterschiedlichen carrier_prefixes denselben Cache treffen
            # (Fenster-Kollision, siehe Auftrag Punkt 3).
            cache_key_material += "+carrier_prefixes:" + ",".join(sorted(carrier_prefixes))
        if encoder == "2d":
            # "+enc2d_v2" (2026-08-27, PREREG_special_tile_yield.md par.4a):
            # NUM_PLANES_CHANNELS 77 -> 79 UND ein neues Packlayout
            # (`_pack_planes`: 419 statt 347 Byte je Zeile). Der Marker MUSS
            # mitziehen -- die Kanalzahl steckt in KEINER anderen
            # Key-Komponente (geprueft 2026-08-27: `cache_key_material` fuehrt
            # INPUT_SIZE, aber nicht NUM_PLANES_CHANNELS). Ohne den Bump
            # traefe ein 79er-Lauf den 77er-Bestandscache.
            cache_key_material += "+enc2d_v2"
        # Konjunktions-Erweiterung (2026-08-10): die 25 Zusatzlabels je Spieler
        # haengen HINTEN an den `ownership`-Vektor. Eigener Suffix, NUR wenn
        # aktiv -- Muster "+enc2d_v1". Bewusst KEIN VALUE_SCHEMA_VERSION-Bump:
        # die Konjunktionen sind ein optionales Zusatzfeld, ein Bump wuerde den
        # vorhandenen v21-Cache ohne Not entwerten. Der Suffix verhindert
        # zugleich das stille Wiederverwenden eines Alt-Caches, dessen
        # `ownership`-Dataset nur OWNERSHIP_TARGETS breit ist (das Ziel waere
        # dann vollstaendig maskiert und der Kopf lernte nichts -- ohne
        # Fehlermeldung).
        if conjunction_head:
            cache_key_material += "+conj_v2"
            if reach_target_k1_active():
                # Eigener Cache, sonst wuerden alte Realisierungs-Labels still
                # weiterverwendet (Muster wie "+enc2d_v1").
                cache_key_material += f"+reachk1_r{REACH_K1_MIN_ROUND}_v1"
                if reach_buffer_mode():
                    # Arm P (par.12): eigener Zusatz-Key, sonst wuerden
                    # boolesche Runde-1-2-Labels aus einem Alt-Cache (reine
                    # k1-Variante) still weiterverwendet.
                    cache_key_material += f"+reachbuf_cap{REACH_BUF_CAP}_v1"
        # Bitpacking (RAM-Optimierung v21, PREREG_v21_window.md "RAM-
        # Voraussetzung"): planes/masks werden ab jetzt STANDARDMAESSIG
        # bitgepackt gespeichert (siehe `_pack_bits`-Kommentar oben) --
        # eigener Suffix erzwingt einen Rebuild ALLER Alt-Caches (flat UND
        # 2d, masks sind in beiden Modi betroffen), kein stilles
        # Fehlinterpretieren des alten unkomprimierten Formats. Escape-Hatch
        # MOSAIC_CACHE_NOPACK=1 (Muster wie MOSAIC_CACHE_F32) erzwingt exakt
        # das alte Format -- eigener Suffix, damit die beiden Formate nie
        # denselben Cache-Key treffen (falls die Bitpack-Validierung mal
        # durchfaellt und zurueckgeschaltet werden muss).
        cache_nopack = os.environ.get("MOSAIC_CACHE_NOPACK") == "1"
        cache_key_material += "+nopack_v1" if cache_nopack else "+bitpack_v1"
        if _IGNORE_PTV:
            cache_key_material += "+ignore_ptv_v1"
        # MOSAIC_CACHE_F32 (Befund 2026-08-26): der Knopf entscheidet ueber den
        # gespeicherten dtype von states/policies (float32 statt float16, siehe
        # `_f` weiter unten) und der Kommentar dort sagt selbst "NICHT
        # bit-identisch" -- er stand aber in KEINER Key-Komponente. Ein Lauf
        # mit dem Notausstieg traf damit den vorhandenen float16-Cache und der
        # Knopf blieb still wirkungslos, also genau die Fehlerklasse, gegen die
        # "+nopack_v1"/"+ignore_ptv_v1" gebaut sind. NUR bei gesetztem Knopf
        # angehaengt: der Default-Key (float16) bleibt unveraendert, kein
        # Bestands-Cache verfaellt.
        if _cache_f32_active():
            cache_key_material += "+f32_v1"
        cache_key = hashlib.md5(cache_key_material.encode()).hexdigest()[:12]
        cache_path_h5 = os.path.join(data_dir, f".cache_{cache_key}.h5")
        cache_path_pt = os.path.join(data_dir, f".cache_{cache_key}.pt")
        # `cache_path_override` (Hebel 4, PREREG_cache_build_time.md par.6):
        # der Datei-Cache braucht einen EIGENEN Schluessel-Namensraum
        # (`per_file_cache_key`), nicht den Fenster-Schluessel oben. Statt die
        # Schluesselbildung hier zu verzweigen -- was den Fenster-Schluessel
        # anfassbar machen wuerde und damit jeden Bestands-Cache gefaehrdet --
        # nimmt der Aufrufer den fertigen Pfad mit. Default None = die Zeilen
        # darueber gelten unveraendert, Bestandsverhalten bit-identisch.
        #
        # Der `.pt`-Zweig bleibt bewusst am Fenster-Schluessel: er ist der
        # Altformat-Lesepfad, und ein Datei-Cache wird nie als .pt geschrieben.
        if cache_path_override is not None:
            cache_path_h5 = cache_path_override
        # Nach aussen sichtbar fuer den parallelen Bau
        # (PREREG_cache_build_time.md Hebel 1): die Worker bauen je eine
        # Datei-Teilmenge und geben nur DIESEN Pfad zurueck, statt die
        # Arrays durch die Prozess-Pipe zu schicken -- beim vollen Korpus
        # waeren das ueber 11 GB. Reine Zuweisung, kein Kontrollfluss.
        self.cache_path_h5 = cache_path_h5

        if os.path.exists(cache_path_h5):
            # HDF5 Cache laden — deutlich schneller als .pt
            print(f"📦 Lade HDF5-Cache ({len(files)} Dateien)...")
            t0 = time.time()
            with h5py.File(cache_path_h5, 'r') as hf:
                self.states             = torch.from_numpy(hf['states'][:])
                self.policies           = torch.from_numpy(hf['policies'][:])
                self.values             = torch.from_numpy(hf['values'][:])
                # Bitpacking (RAM-Optimierung v21): selbstbeschreibend ueber
                # den Dataset-Namen (nicht ueber den aktuellen Env-Var-Stand)
                # -- `self.bitpacked` steuert unten in `__getitem__`/train.py,
                # ob masks/planes noch gepackt sind (Entpacken passiert dann
                # EINMAL pro Batch, siehe `unpack_masks_batch`/
                # `unpack_planes_batch`). 'masks_packed' vorhanden <=> Cache
                # wurde OHNE MOSAIC_CACHE_NOPACK=1 gebaut.
                self.bitpacked = 'masks_packed' in hf
                if self.bitpacked:
                    self.masks = torch.from_numpy(hf['masks_packed'][:])  # [N,51] uint8, gepackt
                else:
                    self.masks = torch.from_numpy(hf['masks'][:])         # [N,406] uint8, Bestandsformat
                self.moon_order_targets = torch.from_numpy(hf['moon_order_targets'][:])
                if 'policy_weights' in hf:
                    self.policy_weights = torch.from_numpy(hf['policy_weights'][:])
                else:  # alter Cache ohne Gewicht → alle 1.0
                    self.policy_weights = torch.ones(len(self.states), dtype=torch.float32)
                if 'points_forecast' in hf:
                    self.points_forecast = torch.from_numpy(hf['points_forecast'][:])
                else:  # alter Cache ohne Aux-Ziel → 0.0 (wird durch VALUE_SCHEMA_VERSION eh selten erreicht)
                    self.points_forecast = torch.zeros_like(self.values)
                if 'rounds' in hf:
                    self.rounds = torch.from_numpy(hf['rounds'][:])
                else:  # kann durch den Schema-Marker im Cache-Key eigentlich nicht auftreten
                    self.rounds = torch.zeros(len(self.states), dtype=torch.int8)
                if 'ownership' in hf:
                    self.ownership = torch.from_numpy(hf['ownership'][:])
                else:
                    self.ownership = torch.full((len(self.states), self.own_targets), -1, dtype=torch.int8)
                if 'root_q' in hf:
                    self.root_q = torch.from_numpy(hf['root_q'][:])
                    self.root_q_mask = torch.from_numpy(hf['root_q_mask'][:])
                else:
                    # Alt-Cache ohne root_q (siehe ROOT_Q_CACHE_FIELDS-Kommentar
                    # oben) -- Maske komplett 0, identisch zu
                    # value_target_lambda=1.0 (Bestandsverhalten).
                    self.root_q = torch.zeros(len(self.states), dtype=torch.float32)
                    self.root_q_mask = torch.zeros(len(self.states), dtype=torch.float32)
                if 'opp_points_forecast' in hf:
                    self.opp_points_forecast = torch.from_numpy(hf['opp_points_forecast'][:])
                    self.opp_points_mask = torch.from_numpy(hf['opp_points_mask'][:])
                else:
                    # Alt-Cache ohne den Task-#28-Kopf (siehe
                    # OPP_POINTS_CACHE_FIELDS-Kommentar oben) -- Maske
                    # komplett 0, `values`/`points_forecast` bleiben unberuehrt.
                    self.opp_points_forecast = torch.zeros_like(self.values)
                    self.opp_points_mask = torch.zeros(len(self.states), dtype=torch.float32)
                if 'values_wdl' in hf:
                    self.values_wdl = torch.from_numpy(hf['values_wdl'][:])
                    self.wdl_outcome = torch.from_numpy(hf['wdl_outcome'][:])
                else:
                    # Task #34 (WDL_CACHE_FIELDS-Kommentar oben): kann durch
                    # den VALUE_SCHEMA_VERSION=16-Marker im Cache-Key
                    # eigentlich nicht auftreten (jeder Cache mit passendem
                    # Key wurde vom neuen Baucode geschrieben) -- defensiver
                    # Fallback trotzdem, gleiches Muster wie bei `rounds`.
                    # 0.5 = neutral/uninformativ (kein Ziel bekannt),
                    # -1.0 = "Ausgang unbekannt" (identisch zur Ownership-
                    # Konvention), NICHT 0.0 (das waere ein erfundenes
                    # "Niederlage"-Label).
                    self.values_wdl = torch.full_like(self.values, 0.5)
                    self.wdl_outcome = torch.full_like(self.values, -1.0)
                if 'endgame_margin' in hf:
                    self.endgame_margin = torch.from_numpy(hf['endgame_margin'][:])
                    self.endgame_mask = torch.from_numpy(hf['endgame_mask'][:])
                else:
                    # Schema 18 (ENDGAME_CACHE_FIELDS): defensiver Fallback
                    # wie bei values_wdl -- Maske komplett 0, Ziel neutral 0.5.
                    self.endgame_margin = torch.full_like(self.values, 0.5)
                    self.endgame_mask = torch.zeros(len(self.states), dtype=torch.float32)
                if 'ranking_action_ids' in hf:
                    self.ranking_action_ids = torch.from_numpy(hf['ranking_action_ids'][:])
                    self.ranking_child_q    = torch.from_numpy(hf['ranking_child_q'][:])
                    self.ranking_mask       = torch.from_numpy(hf['ranking_mask'][:])
                else:
                    # Schema 19 (RANKING_CACHE_FIELDS): defensiver Fallback,
                    # kann durch den VALUE_SCHEMA_VERSION=19-Marker im
                    # Cache-Key eigentlich nicht auftreten (gleiches Muster
                    # wie bei endgame_margin/values_wdl) -- Maske komplett 0,
                    # IDs -1 (kein belegter Slot), Q 0.0.
                    self.ranking_action_ids = torch.full((len(self.states), RANKING_TOPK), -1, dtype=torch.int16)
                    self.ranking_child_q    = torch.zeros((len(self.states), RANKING_TOPK), dtype=torch.float16)
                    self.ranking_mask       = torch.zeros(len(self.states), dtype=torch.float32)
                if self.encoder == "2d":
                    # Bitpacking (RAM-Optimierung v21): Dataset-Name
                    # selbstbeschreibend, unabhaengig vom `self.bitpacked`-
                    # Wert oben (der ueber `masks_packed` bestimmt wird) --
                    # beide werden zwar immer gemeinsam im selben Bauschritt
                    # geschrieben, die getrennte Pruefung ist defensiv gegen
                    # Cache-Korruption (klarer Fehler statt stillem Fallback).
                    if 'planes_packed' in hf:
                        self._planes_dataset_name = 'planes_packed'
                    elif 'planes' in hf:
                        self._planes_dataset_name = 'planes'
                    else:
                        raise RuntimeError(
                            f"HDF5-Cache {cache_path_h5} hat den '+enc2d_v2'-Key, aber weder "
                            f"'planes' noch 'planes_packed' -- Cache-Korruption? Datei loeschen "
                            f"und neu bauen lassen."
                        )
                    # RAM-Fix: NICHT `hf['planes...'][:]` (voller Einlese-Sog),
                    # nur den Pfad merken -- `_open_planes_h5` oeffnet lazy
                    # einen eigenen, separaten Handle (dieser `with`-Block
                    # schliesst `hf` gleich).
                    self._planes_h5_path = _resolve_planes_h5_path(cache_path_h5)
                else:
                    self._planes_h5_path = None
                    self._planes_dataset_name = None
            print(f"Datensatz geladen: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        elif os.path.exists(cache_path_pt):
            # Alten .pt Cache laden und nach HDF5 migrieren -- kann fuer
            # encoder="2d" praktisch nie greifen (der "+enc2d_v2"-Key-Suffix
            # existiert erst seit Task #11 Phase 2, ein .pt-Cache mit diesem
            # Key kann also nicht vorliegen), aber defensiv statt eines
            # stillen `planes=None` trotzdem hart pruefen.
            if self.encoder == "2d":
                raise RuntimeError(
                    f"Alter .pt-Cache {cache_path_pt} passt zum '+enc2d_v2'-Key -- das kann "
                    f"eigentlich nicht vorkommen (der Suffix ist neuer als jeder .pt-Cache). "
                    f"Cache-Datei loeschen und neu bauen lassen."
                )
            print(f"📦 Migriere .pt → HDF5 Cache...")
            t0 = time.time()
            bundle = torch.load(cache_path_pt, weights_only=False)
            self.states             = bundle["states"] if isinstance(bundle["states"], torch.Tensor) else torch.stack(bundle["states"])
            self.policies           = bundle["policies"] if isinstance(bundle["policies"], torch.Tensor) else torch.stack(bundle["policies"])
            self.values             = bundle["values"] if isinstance(bundle["values"], torch.Tensor) else torch.stack(bundle["values"])
            self.masks              = bundle["masks"] if isinstance(bundle["masks"], torch.Tensor) else torch.stack(bundle["masks"])
            mot = bundle.get("moon_order_targets")
            if mot is None:
                mot = [torch.full((5,), -1.0) for _ in self.states]
            self.moon_order_targets = mot if isinstance(mot, torch.Tensor) else torch.stack(mot)
            self.policy_weights = torch.ones(len(self.states), dtype=torch.float32)  # Legacy → 1.0
            self.points_forecast = torch.zeros_like(self.values)  # Legacy .pt kennt kein Aux-Ziel
            self.rounds = torch.zeros(len(self.states), dtype=torch.int8)  # Legacy .pt kennt keine Runden
            self.ownership = torch.full((len(self.states), self.own_targets), -1, dtype=torch.int8)
            # Legacy .pt stammt aus einer Aera lange vor root_q (Commit
            # 2718b9a) -- Maske komplett 0, siehe ROOT_Q_CACHE_FIELDS-Kommentar.
            self.root_q = torch.zeros(len(self.states), dtype=torch.float32)
            self.root_q_mask = torch.zeros(len(self.states), dtype=torch.float32)
            # Legacy .pt kennt auch keinen Task-#28-Kopf -- gleiches
            # Fallback-Muster wie root_q oben.
            self.opp_points_forecast = torch.zeros_like(self.values)
            self.opp_points_mask = torch.zeros(len(self.states), dtype=torch.float32)
            # Legacy .pt stammt lange vor Schema 18 -- gleiches Muster.
            self.endgame_margin = torch.full_like(self.values, 0.5)
            self.endgame_mask = torch.zeros(len(self.states), dtype=torch.float32)
            # Legacy .pt stammt lange vor Task #34 -- gleiches Fallback-Muster
            # wie root_q/opp_points oben (siehe WDL_CACHE_FIELDS-Kommentar).
            self.values_wdl = torch.full_like(self.values, 0.5)
            self.wdl_outcome = torch.full_like(self.values, -1.0)
            # Legacy .pt stammt lange vor Schema 19 -- gleiches Fallback-
            # Muster wie endgame_margin oben (siehe RANKING_CACHE_FIELDS-
            # Kommentar): Maske komplett 0, IDs -1, Q 0.0.
            self.ranking_action_ids = torch.full((len(self.states), RANKING_TOPK), -1, dtype=torch.int16)
            self.ranking_child_q    = torch.zeros((len(self.states), RANKING_TOPK), dtype=torch.float16)
            self.ranking_mask       = torch.zeros(len(self.states), dtype=torch.float32)
            # Als HDF5 speichern
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',              data=self.states.numpy(),              compression='lzf')
                hf.create_dataset('policies',            data=self.policies.numpy(),            compression='lzf')
                hf.create_dataset('values',               data=self.values.numpy(),              compression='lzf')
                hf.create_dataset('masks',               data=self.masks.numpy(),               compression='lzf')
                hf.create_dataset('moon_order_targets',  data=self.moon_order_targets.numpy(),  compression='lzf')
                hf.create_dataset('policy_weights',      data=self.policy_weights.numpy(),      compression='lzf')
                hf.create_dataset('points_forecast',     data=self.points_forecast.numpy(),     compression='lzf')
                hf.create_dataset('rounds',              data=self.rounds.numpy(),              compression='lzf')
                hf.create_dataset('ownership',           data=self.ownership.numpy(),           compression='lzf')
                hf.create_dataset('root_q',              data=self.root_q.numpy(),              compression='lzf')
                hf.create_dataset('root_q_mask',         data=self.root_q_mask.numpy(),         compression='lzf')
                hf.create_dataset('opp_points_forecast', data=self.opp_points_forecast.numpy(), compression='lzf')
                hf.create_dataset('opp_points_mask',     data=self.opp_points_mask.numpy(),     compression='lzf')
                hf.create_dataset('values_wdl',          data=self.values_wdl.numpy(),          compression='lzf')
                hf.create_dataset('wdl_outcome',         data=self.wdl_outcome.numpy(),         compression='lzf')
                hf.create_dataset('endgame_margin',      data=self.endgame_margin.numpy(),      compression='lzf')
                hf.create_dataset('endgame_mask',        data=self.endgame_mask.numpy(),        compression='lzf')
                hf.create_dataset('ranking_action_ids',  data=self.ranking_action_ids.numpy(),  compression='lzf')
                hf.create_dataset('ranking_child_q',     data=self.ranking_child_q.numpy(),     compression='lzf')
                hf.create_dataset('ranking_mask',        data=self.ranking_mask.numpy(),        compression='lzf')
            os.remove(cache_path_pt)
            self._planes_h5_path = None  # kann hier nur "flat" sein, s.o. Guard
            print(f"Datensatz geladen + migriert: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        else:
            print(f"Lade Daten aus {len(files)} Dateien...")
            t0 = time.time()
            _CIDX = {'blau':0,'gelb':1,'rot':2,'schwarz':3,'türkis':4}
            states_l, policies_l, values_l, masks_l, moon_l = [], [], [], [], []
            polw_l = []  # Policy-Loss-Gewicht je Sample (1=Drafting, 0=Tiling/Start)
            points_l = []  # Aux-Ziel: Punktestand-Prognose (siehe VALUE_SCHEMA_VERSION oben)
            rounds_l = []  # Rundennummer je Sample (Task #15 B: rundenselektive Loss-Gewichtung)
            own_l = []     # Ownership-Ziel je Sample (Task #9): 72 Binaerlabels, -1 = unbekannt
            root_q_l = []       # λ-Misch-Experiment: roher Root-Suchwert, remapped [-1,1]
            root_q_mask_l = []  # 1.0 = root_q vorhanden (echte Suche geloggt), sonst 0.0
            opp_points_l = []       # Task #28: reine Gegner-Punkteprognose (siehe OPP_POINTS_CACHE_FIELDS)
            opp_points_mask_l = []  # 1.0 = echter Wert (scores/winner vorhanden), sonst 0.0
            endgame_l = []       # Schema 18: exakter R5-Wurzelwert [0,1] (ENDGAME_CACHE_FIELDS)
            endgame_mask_l = []  # 1.0 = R5-Drafting mit root_q, sonst 0.0
            ranking_ids_l = []   # Schema 19: Top-K Geschwister-Aktions-IDs (RANKING_CACHE_FIELDS)
            ranking_q_l = []     # Schema 19: zugehoerige Q-Werte, [0,1], fp16
            ranking_mask_l = []  # Schema 19: 1.0 = Geschwister-Set vorhanden UND pol_w>0
            value_wdl_l = []    # Task #34: Gewinnwahrscheinlichkeit [0,1] (siehe WDL_CACHE_FIELDS)
            wdl_outcome_l = []  # Task #34: roher Spielausgang 0.0/1.0, -1.0 = unbekannt
            # Task #11 Phase 2: Planes-Puffer NUR im 2D-Modus gesammelt (leere
            # Liste bei encoder="flat" -> keine zusaetzliche Rechenzeit/Speicher
            # im Bestandsverhalten). uint8 (0/1) statt float32, siehe
            # `encoder`-Doku oben -- binaere Kanaele plus die zwei
            # wertetragenden Spezialfeld-Kanaele am Ende.
            planes_l = [] if self.encoder == "2d" else None

            for f in files:
                # `bootstrap_value` ist eine NATIVE [0,1]-Gewinnwahrschein-
                # lichkeit -- das ist seit 2026-08-27 der DEFAULT. Nur die
                # tanh-Aera-Praefixe der Blockliste liefern eine gestauchte
                # Marge, die unten Platt-entstaucht wird (Begruendung der
                # Umkehr an `LEGACY_STRETCHED_PREFIXES` in neural_net.py).
                bootstrap_native = not os.path.basename(f).startswith(LEGACY_STRETCHED_PREFIXES)
                # ZWEITE, unabhaengige Frage: der eingefrorene v20-Traeger-
                # Kurzschluss (siehe `_is_policy_carrier`). Eigene Konstante,
                # damit die Umkehr oben ihn nicht mitdreht.
                v20_wdl_generator = os.path.basename(f).startswith(V20_CARRIER_SHORTCUT_PREFIXES)
                # Policy-Traeger-Regel (siehe pol_w-Kommentar unten und
                # `_is_policy_carrier`-Doku oben): ohne Manifest traegt jede
                # Datei Policy (Bestandsverhalten); mit v20-Manifest (kein
                # `carrier_prefixes`-Feld) nur v20wdl*-Dateien und gelistete
                # Alt-Dateien (Alt-Verhalten, Rueckwaerts-kompatibel); mit
                # v21-Manifest (`carrier_prefixes` gesetzt) nur die
                # gelisteten Dateien plus explizite Praefix-Treffer -- der
                # v20-Kurzschluss greift dann NICHT mehr.
                file_policy_carrier = _is_policy_carrier(
                    os.path.basename(f), policy_carrier_set, carrier_prefixes, v20_wdl_generator)
                with open(f, "rb") as file:
                    # corpus_io: erkennt gzip am INHALT (Magic-Bytes), nicht an
                    # der Endung -- Bestandsdateien und komprimierte liegen
                    # nebeneinander, und der Dateiname bleibt `.pkl`, weil
                    # Cache-Schluessel, MOSAIC_DATA_EXCLUDE und alle Globs an
                    # ihm haengen.
                    game_data = _load_records_fh(file)
                    final_own = _final_ownership_by_game(game_data)
                    reach_k1 = self.conjunction_head and reach_target_k1_active()
                    reach_buf = reach_k1 and reach_buffer_mode()
                    # Arm P (par.12): stetige Puffer-Ziele in Runde 1-2
                    # sprengen int8 (nur 0/1 bisher noetig) -- float16 traegt
                    # die Stauchung verlustarm. -1-Maskierung (fo is None)
                    # bleibt in float16 exakt, BCE-with-logits (train.py)
                    # nimmt ohnehin weiche Ziele und maskiert mit `>= 0`.
                    own_dtype = np.float16 if reach_buf else np.int8
                    for step in game_data:
                        states_l.append(state_to_tensor(step["state"]).numpy())
                        if planes_l is not None:
                            planes_l.append(state_to_planes(step["state"]).numpy().astype(np.uint8))
                        # λ-Misch-Value-Target-Experiment (siehe ROOT_Q_CACHE_FIELDS-
                        # Kommentar oben): root_q ist ein Roh-Feld je Schritt,
                        # UNABHAENGIG davon, ob die Partie abgeschlossen ist (anders
                        # als val/points_val unten) -- daher hier, VOR dem
                        # scores/winner-Zweig, extrahiert. [0,1]-Skala wie rtv,
                        # Remap auf [-1,1] beim Cache-Bau (*2.0-1.0). Fehlt bei
                        # Ein-Aktion-Zuegen und in Dateien ohne dieses Feld
                        # (Commit 2718b9a, v18 aufwaerts) -- dann Maske 0.
                        rq = step.get("root_q")
                        if rq is not None:
                            root_q_l.append(float(rq) * 2.0 - 1.0)
                            root_q_mask_l.append(1.0)
                        else:
                            root_q_l.append(0.0)
                            root_q_mask_l.append(0.0)
                        # Schema 18 (ENDGAME_CACHE_FIELDS): in der R5-Drafting-
                        # Zone ist root_q der EXAKTE Minimax-Wurzelwert
                        # (round5.rs via net_mcts.rs-R5-Zweig, [0,1]-Skala) --
                        # als eigenes Aux-Ziel `endgame_margin` gefuehrt.
                        # Unabhaengig von `completed` gueltig (der AB-Wert
                        # haengt nicht vom Partieausgang ab). Ausserhalb der
                        # Zone bzw. ohne root_q (v16/v17, Ein-Aktion-Zuege):
                        # Maske 0.
                        _st = step["state"]
                        if (rq is not None and _st.get("round") == 5
                                and _st.get("phase") == "drafting"):
                            endgame_l.append([float(rq)])
                            endgame_mask_l.append(1.0)
                        else:
                            endgame_l.append([0.0])
                            endgame_mask_l.append(0.0)
                        # Schema 19 (RANKING_CACHE_FIELDS, Task #35b): additives
                        # `root_child_q`-JSON-Feld -- GLEICHE Reihenfolge/Laenge
                        # wie `step["policy"]` (self_play.rs-Vertrag, siehe
                        # dortigen root_child_q_field-Kommentar). Braucht
                        # mindestens 2 Geschwister, um ueberhaupt ein Paar bilden
                        # zu koennen. Die finale `ranking_mask` haengt ZUSAETZLICH
                        # von `pol_w` ab (Tiling/Start/`policy_target_valid=False`)
                        # -- `pol_w` wird aber erst weiter unten berechnet, daher
                        # hier nur die Rohwerte sammeln (`_rk_ids`/`_rk_q`/
                        # `_rk_avail`) und den Append ZUSAMMEN mit `polw_l.append`
                        # weiter unten nachziehen (gleiche Loop-Iteration,
                        # Reihenfolge der Listen bleibt dadurch synchron).
                        rcq = step.get("root_child_q")
                        _rk_ids = np.full(RANKING_TOPK, -1, dtype=np.int16)
                        _rk_q = np.zeros(RANKING_TOPK, dtype=np.float16)
                        _rk_avail = 0.0
                        if rcq is not None and len(rcq) >= 2:
                            _act_ids = [action_to_id(pe["action"]) for pe in step["policy"]]
                            _pairs = _ranking_topk_pairs(_act_ids, [float(q) for q in rcq], RANKING_TOPK)
                            for _i, (_aid, _q) in enumerate(_pairs):
                                _rk_ids[_i] = _aid
                                _rk_q[_i] = _q
                            _rk_avail = 1.0
                        # Audit-F2 (2026-08-05): Rust stempelt `scores`/`winner`
                        # auch bei TIMEOUT-ABBRUCH bedingungslos (self_play.rs,
                        # dortiger Kommentar verspricht faelschlich einen
                        # Downstream-Filter, der nie existierte -- self_play.py
                        # WARNT nur). Der -1-Sentinel-Zweig unten war damit auf
                        # Rust-Korpora UNERREICHBAR und Abbruch-Zwischenstaende
                        # wurden zu harten Sieg-Labels. `game_completed` sperrt
                        # unten wdl_outcome (Sentinel -1) und opp_points_mask
                        # (0); die weichen val/points-Ziele behalten den
                        # Zwischenstand (dokumentierte Restunsicherheit, kein
                        # erfundenes HARTES Label). Fehlendes Feld = Alt-Korpus
                        # = vertrauenswuerdig; nur explizites False sperrt.
                        # Aktueller 900er-Korpus: 0% betroffen (Stichprobe 90
                        # Dateien) -- Korrektheits-Fix fuer kuenftige
                        # Kampagnen, kein Label-Shift, daher KEIN Schema-Bump.
                        game_completed = step.get("completed", True) is not False
                        if "scores" in step and "winner" in step:
                            p = step["player"]
                            scores_src = step.get("scores_unclamped", step["scores"])
                            own_total = float(scores_src[p])
                            opp_total = float(scores_src[1 - p])
                            # Weiches, symmetrisches Margin-Ziel statt hartem
                            # ±1 (siehe VALUE_SCHEMA_VERSION=13-Kommentar oben)
                            # -- dieselbe own_total/opp_total-Information wie
                            # bisher, nur nicht mehr an den Raendern
                            # gesaettigt/binarisiert.
                            val = math.tanh((own_total - opp_total) / VALUE_SCALE)
                            # Punktestand-Formel bleibt als separates Aux-Ziel
                            # erhalten (bereits inkl. Wertungsplatten).
                            # Schema 20 (Nutzer 2026-08-10): REIN own, kein
                            # Gegner-Anteil mehr. Der 0,1-Term war nur ueber
                            # `opp_aware_points_utility` rueckgewinnbar, und der
                            # Pfad ist hinter `w == 0.0` toter Code.
                            points_val = math.tanh(own_total / VALUE_SCALE)
                            # Task #28 (PREREG_task28_aggression.md, "Minimal-
                            # invasiver Zuschnitt" Punkt 2): eigenstaendiger
                            # Aux-Ziel-Track fuer den additiven
                            # `opp_points_head` -- spiegelt JEDEN Zweig, der
                            # oben in `points_val` den own-seitigen Term
                            # (tanh(own_total/SCALE) -> own_rtv ->
                            # TD-Blend mit own_bootstrap) bildet, 1:1 auf den
                            # opp-Groessen. NUR durch diese Spiegelung gilt
                            # `points_val == own-Term - EPSILON*opp_points_val`
                            # in JEDEM Zweig (Induktion ueber rtv-/Bootstrap-
                            # Override) -- und damit algebraisch exakt
                            # `own_pts (= own-Term) = points_pred +
                            # VALUE_OPP_EPSILON * opp_pred` bei perfekter
                            # Kopf-Vorhersage. opp_points_val ist ausdruecklich
                            # NICHT `val` gespiegelt (dessen Basis ist die
                            # MARGIN (own-opp)/SCALE, nicht own_total allein).
                            opp_points_val = math.tanh(opp_total / VALUE_SCALE)
                            # Audit-F2: Abbruch-Zwischenstand ist kein echter
                            # Endpunktestand -- Maske 0 (Konvention wie im
                            # Legacy-Zweig unten).
                            opp_points_mask = 1.0 if game_completed else 0.0
                            # Rundenübergangs-Ziel (siehe round_transition.rs/
                            # self_play.rs::play_net_self_play_game): über
                            # mehrere Chance-Node-Samples (verschiedene mögliche
                            # Fabrik-Neubefüllungen) gemittelte NETZ-
                            # Gewinnwahrscheinlichkeit ([0,1], nicht Punkte --
                            # daher NICHT in die own_total/opp_total-Formel
                            # oben eingesetzt, sondern direkt auf den
                            # tanh-Wertebereich [-1,1] reskaliert). Nur
                            # vorhanden, wenn dieser Schritt tatsächlich einen
                            # Rundenübergang erreicht hat (nicht Runde 5, keine
                            # abgebrochenen Partien) -- sonst Fallback auf die
                            # obigen Formeln (hartes ±1 bzw. Punktestand).
                            #
                            # Ab Version 12 ersetzt own_rtv sowohl `val` (das
                            # Hauptziel, das net_mcts.rs tatsächlich für PUCT
                            # liest) als auch `points_val` -- own_rtv ist
                            # bereits exakt auf `val`s Skala (2*win_prob-1),
                            # daher direkt übernommen statt über die
                            # own_total/opp_total-Punkteformel geschickt.
                            rtv = step.get("round_transition_value")
                            # Task #84 (rtv-Ablation Phase 1): Variante kann
                            # den Override komplett ("nortv") oder nur fuer
                            # Runde-1-Zustaende ("nortv_r1") unterdruecken --
                            # Rundenzuordnung identisch zu
                            # offline_diagnosis.py::load_val_samples
                            # (`step["state"]["round"]`).
                            if rtv is not None and value_target_variant == "nortv":
                                rtv = None
                            elif (rtv is not None and value_target_variant == "nortv_r1"
                                  and int(step["state"].get("round", 0)) == 1):
                                rtv = None
                            if rtv is not None:
                                own_rtv = float(rtv[p]) * 2.0 - 1.0
                                opp_rtv = float(rtv[1 - p]) * 2.0 - 1.0
                                val = own_rtv
                                points_val = own_rtv  # Schema 20: rein own
                                opp_points_val = opp_rtv  # Task #28: spiegelt own_rtv-Override
                            # Punkt 6 (VALUE_SCHEMA_VERSION=15): TD-Bootstrap-
                            # Blend, siehe Kommentar oben -- mischt HINEIN
                            # (ersetzt `val`/`points_val` nicht komplett wie
                            # `rtv`), da der kurze Horizont eine andere,
                            # naehere Groesse schaetzt als das bisherige Ziel.
                            bv = step.get("bootstrap_value")
                            if bv is not None:
                                own_bootstrap = float(bv[p]) * 2.0 - 1.0
                                opp_bootstrap = float(bv[1 - p]) * 2.0 - 1.0
                                points_bootstrap = own_bootstrap  # Schema 20: rein own
                                val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * val
                                points_val = TD_LAMBDA * points_bootstrap + (1.0 - TD_LAMBDA) * points_val
                                # Task #28: identischer TD-Blend, opp-Seite
                                # (gleiches TD_LAMBDA, gleiche Blend-Formel).
                                opp_points_val = (TD_LAMBDA * opp_bootstrap
                                                  + (1.0 - TD_LAMBDA) * opp_points_val)
                            # Task #34 (VALUE_SCHEMA_VERSION=16, WDL_CACHE_FIELDS):
                            # eigenstaendiges, PARALLELES Ziel -- UNABHAENGIG von
                            # `val`/`rtv` oben (der rtv-Zweig bleibt bewusst
                            # unangetastet, siehe Kopf-Kommentar). Hartes
                            # Sieg/Niederlage-Label plus derselbe TD-Blend-Formel
                            # wie oben, ABER `bv[p]` NICHT auf [-1,1] remappen --
                            # `bootstrap_value` ist bereits eine [0,1]-
                            # Gewinnwahrscheinlichkeit, hier direkt geblendet
                            # (macht den Blend semantisch kohaerent, siehe
                            # STATUS.md "Bonus-Befund").
                            # Audit-F2: nur ECHTE Ausgaenge liefern ein hartes
                            # Label; Abbruch -> Sentinel -1 (wie der Legacy-
                            # Zweig unten) und value_wdl = weiche Projektion
                            # statt eines erfundenen harten Anteils.
                            if game_completed:
                                wdl_outcome_val = 1.0 if int(step["winner"]) == p else 0.0
                                value_wdl = wdl_outcome_val
                                if bv is not None:
                                    # Nativ ist der DEFAULT (2026-08-27):
                                    # entstaucht wird nur der tanh-Aera-
                                    # Bootstrap der Blockliste, alles andere
                                    # bleibt roh (siehe
                                    # `LEGACY_STRETCHED_PREFIXES`).
                                    bvp = float(bv[p])
                                    if not bootstrap_native:
                                        bvp = _destretch_prob(bvp)
                                    value_wdl = TD_LAMBDA * bvp + (1.0 - TD_LAMBDA) * wdl_outcome_val
                                value_wdl = min(1.0, max(0.0, value_wdl))
                            else:
                                wdl_outcome_val = -1.0
                                value_wdl = min(1.0, max(0.0, (val + 1.0) * 0.5))
                        else:
                            val = float(step["value"])
                            points_val = val
                            # Task #28: unvollstaendige Partie (kein scores/
                            # winner) -- gleicher Fallback-PFAD wie points_val
                            # (`points_val = val`), aber hier Maske 0 statt
                            # eines erfundenen Werts (PREREG-Vorgabe: "Maske 0
                            # statt eines erfundenen Werts").
                            opp_points_val = 0.0
                            opp_points_mask = 0.0
                            # Task #34: kein echtes Sieg/Niederlage-Label
                            # vorhanden -- grobe Projektion der alten
                            # tanh-Marge auf [0,1] als bestmoegliche Naeherung
                            # (kein erfundenes hartes Label), `wdl_outcome`
                            # bekommt den "unbekannt"-Sentinel -1.0 (analog zur
                            # Ownership-Konvention).
                            value_wdl = (val + 1.0) * 0.5
                            wdl_outcome_val = -1.0
                        values_l.append([val])
                        points_l.append([points_val])
                        opp_points_l.append([opp_points_val])
                        opp_points_mask_l.append(opp_points_mask)
                        value_wdl_l.append([value_wdl])
                        wdl_outcome_l.append([wdl_outcome_val])

                        t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        for pe in step["policy"]:
                            t_policy[action_to_id(pe["action"])] += pe["prob"]
                        s = t_policy.sum()
                        if s > 0: t_policy /= s
                        if POLICY_TARGET_SHARPEN_EXPONENT != 1.0:
                            t_policy = np.power(t_policy, POLICY_TARGET_SHARPEN_EXPONENT, dtype=np.float32)
                            s2 = t_policy.sum()
                            if s2 > 0: t_policy /= s2
                        policies_l.append(t_policy)

                        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        moves = step.get("valid_actions") or step["state"].get("valid_moves", [])
                        for move in moves:
                            mask[action_to_id(move)] = 1.0
                        # Selbstkonsistenz: die tatsächlich gespielten Policy-Aktionen
                        # sind per Definition legal — immer in die Maske aufnehmen.
                        # Verhindert Policy-Leaks (Target-Masse auf maskierter Aktion →
                        # explodierender Policy-Loss), falls valid_actions unvollständig ist.
                        for pe in step["policy"]:
                            mask[action_to_id(pe["action"])] = 1.0
                        masks_l.append(mask)

                        moon_target = np.full(5, -1.0, dtype=np.float32)
                        moon_order = step.get("moon_order_target", None)
                        if moon_order:
                            for rank, color_name in enumerate(moon_order):
                                c_idx = _CIDX.get(color_name, -1)
                                if c_idx >= 0:
                                    moon_target[c_idx] = float(rank)
                        moon_l.append(moon_target)

                        # Policy-Loss nur für ECHTE Drafting-Schritte: Tiling/Start-
                        # Steps sind one-hot Solver-/Heuristik-Züge, die das Netz nie
                        # vorhersagen muss (Tiling macht der DFS-Solver). Sie fluten
                        # sonst den Policy-Head mit Tiling-Aktionen → das Netz legt
                        # auch in der Drafting-Phase Masse auf (illegale) Tiling-IDs
                        # und die Drafting-Priors verkommen zu Rauschen.
                        phase = step["state"].get("phase")
                        is_start = any(pe["action"].get("is_start") for pe in step["policy"])
                        pol_w = 1.0 if (phase == "drafting" and not is_start) else 0.0
                        # Schema 17 / v20-Zwei-Klassen-Fenster: liegt ein
                        # Policy-Traeger-Manifest vor, tragen ALT-Dateien nur
                        # dann Policy-Ziele, wenn sie darin gelistet sind --
                        # alle uebrigen Alt-Dateien sind reines Value-Material
                        # (Nutzer-Design 2026-08-06: 1350 v18- + 450
                        # v17-Partien Policy-aktiv). v20wdl*-Dateien regeln
                        # sich selbst ueber `policy_target_valid` (Schwarm).
                        if not file_policy_carrier:
                            pol_w = 0.0
                        # PCR (Task #14): Cheap-Suche-Zuege tragen ein explizites
                        # `policy_target_valid=false` (self_play.rs, Feld nur bei
                        # aktivem PCR vorhanden) -- ihr Visit-Ziel stammt aus einer
                        # verkuerzten Suche und ist als Policy-Ziel unzuverlaessig
                        # (PREREG_pcr.md). Maske 0 wie Tiling/Start-Schritte; das
                        # Value-/Punkte-/root_q-Ziel bleibt unmaskiert. Feld fehlt
                        # (None) in allen Nicht-PCR-Korpora -> dort byte-identisch.
                        # MOSAIC_IGNORE_POLICY_TARGET_VALID (2026-08-25,
                        # PREREG_v22_window.md par.4): setzt genau DIESE
                        # Maskierung aus -- der Traeger-A/B-Arm. Im v22-Korpus
                        # tragen 61,8 Prozent der Draftingzuege die Flagge, weil
                        # sie Vorzugszuege des v2-Lehrers sind; ob der
                        # Policy-Kopf sie sehen soll, ist die offene Frage. Die
                        # ANDEREN Nullsetzungen (Tiling/Start, Traeger-Manifest,
                        # PCR) bleiben unberuehrt -- sonst waere es ein anderer
                        # Arm als der registrierte. Default aus =
                        # bestandsidentisch; der Schalter steht im Cache-Key,
                        # sonst zoege der zweite Lauf still den ersten Cache.
                        if step.get("policy_target_valid") is False and not _IGNORE_PTV:
                            pol_w = 0.0
                        polw_l.append(np.float32(pol_w))
                        # Schema 19 (RANKING_CACHE_FIELDS): finale Maske erst
                        # HIER moeglich -- `pol_w` (inkl. aller obigen
                        # Sonderfaelle: Tiling/Start, Policy-Traeger-Manifest,
                        # PCR) ist jetzt final berechnet. `_rk_avail` kam aus
                        # dem `root_child_q`-Block oben (gleiche Loop-Iteration).
                        ranking_ids_l.append(_rk_ids)
                        ranking_q_l.append(_rk_q)
                        ranking_mask_l.append(np.float32(_rk_avail if pol_w > 0.0 else 0.0))
                        rounds_l.append(np.int8(step["state"].get("round", 0)))
                        # Ego-Perspektive: erst der Spieler am Zug, dann der
                        # Gegner -- dieselbe Reihenfolge wie in state_to_tensor
                        # (`me = players[curr_pi]`, dann `enemy`). Die FUELLUNG
                        # stammt aus dem Endzustand DES SPIELS, gilt also fuer
                        # alle Schritte dieser Partie.
                        fo = final_own.get(step["game_id"])
                        if fo is None:
                            own_l.append(np.full(self.own_targets, -1, dtype=own_dtype))
                        else:
                            c = step["state"].get("current_player", 0)
                            first, second = (fo[0], fo[1]) if c == 0 else (fo[1], fo[0])
                            vec = first + second
                            if self.conjunction_head:
                                # Gleiche Ego-Reihenfolge wie oben, HINTEN
                                # angehaengt -> Layout des erweiterten Kopfs:
                                # [0:36] Rand ich, [36:72] Rand Gegner,
                                # [72:106] Konj. ich, [106:140] Konj. Gegner
                                # (34 je Spieler, GEPRUEFT gegen config.py:117
                                # CONJUNCTIONS_PER_PLAYER=34 -- diese Zeile
                                # sagte frueher faelschlich [72:97]/[97:122]
                                # = 25, siehe PREREG_ownership_corpus.md §3.3).
                                cj_first, cj_second = (fo[2], fo[3]) if c == 0 else (fo[3], fo[2])
                                rd = int(step["state"].get("round") or 0)
                                if reach_k1 and rd >= REACH_K1_MIN_ROUND:
                                    # KOPIEREN ist Pflicht: fo[2]/fo[3] werden
                                    # EINMAL je Partie gebildet und von allen
                                    # Schritten geteilt -- direktes Ueberschreiben
                                    # wuerde alle Folgeschritte verderben.
                                    ego = reach_columns(step["state"], c)
                                    geg = reach_columns(step["state"], 1 - c)
                                    if ego is not None and geg is not None:
                                        cj_first, cj_second = list(cj_first), list(cj_second)
                                        cj_first[REACH_ATOMS] = ego
                                        cj_second[REACH_ATOMS] = geg
                                elif reach_buf and 1 <= rd < REACH_K1_MIN_ROUND:
                                    # Arm P (par.12): Runde 1-2 traegt hier
                                    # sonst die konstante 1 (100 %/98,8 %
                                    # vollendbar, par.10) -- der stetige
                                    # Puffer schliesst genau diese Luecke.
                                    # Gleiches Kopieren-Muster, gleiche
                                    # None-Absicherung: bei None (fehlendes
                                    # Wheel) bleibt das Realisierungs-Label
                                    # stehen.
                                    ego = reach_buffer_columns(step["state"], c)
                                    geg = reach_buffer_columns(step["state"], 1 - c)
                                    if ego is not None and geg is not None:
                                        cj_first, cj_second = list(cj_first), list(cj_second)
                                        cj_first[REACH_ATOMS] = ego
                                        cj_second[REACH_ATOMS] = geg
                                vec = vec + cj_first + cj_second
                            own_l.append(np.array(vec, dtype=own_dtype))

            # RAM-Fix (2026-07-31): jede *_l-Liste wird SOFORT nach ihrer
            # *_np-Konvertierung freigegeben (statt alle Listen bis nach der
            # letzten Konvertierung inkl. `planes_np` mitzuschleppen) -- senkt
            # die Transientspitze waehrend des Cache-Baus, an der Liste UND
            # fertiges Array je Feld kurzzeitig gleichzeitig im Speicher
            # standen. Bei ~1,3 Mio. Zuegen (voller Korpus) sind `states_l`/
            # `policies_l`/`masks_l`/`planes_l` allein je mehrere GB (Python-
            # Objekt-Overhead pro Listenelement kommt oben drauf) -- ein
            # realer from-scratch-2D-Lauf auf dem vollen Korpus ist mit der
            # alten Reihenfolge (ein Sammel-`del` ganz am Ende) vermutlich an
            # genau dieser Spitze bzw. der anschliessenden Dauerlast
            # gestorben (spurlos, kein Traceback, siehe `_open_planes_h5`).
            # RAM-Optimierung v20 (2026-08-06, Nutzer-Auftrag): das
            # 21k-Partien-Fenster (~3,4 Mio Zustaende) wuerde in float32
            # ~35-40 GB RSS kosten (gemessen: 12,1 KB/Zustand bei 9k Partien,
            # 32 GB Maschine). Kompakte Typen druecken das auf ~6 KB/Zustand:
            # - states/policies -> float16 (Eingaben/Soft-Targets; Quantisierung
            #   ~6e-4 relativ, weit unter Seed-Rauschen; NICHT bit-identisch,
            #   Notausstieg MOSAIC_CACHE_F32=1),
            # - masks -> uint8 (0/1, EXAKT),
            # - planes waren bereits uint8, ownership bereits int8.
            # train.py castet je Batch nach dem Device-Move auf float32.
            _f = np.float32 if _cache_f32_active() else np.float16
            states_np    = np.array(states_l,    dtype=_f);         del states_l
            policies_np  = np.array(policies_l,  dtype=_f);         del policies_l
            values_np    = np.array(values_l,    dtype=np.float32); del values_l
            masks_np     = np.array(masks_l,     dtype=np.uint8);   del masks_l
            moon_np      = np.array(moon_l,      dtype=np.float32); del moon_l
            polw_np      = np.array(polw_l,      dtype=np.float32); del polw_l
            points_np    = np.array(points_l,    dtype=np.float32); del points_l
            rounds_np    = np.array(rounds_l,    dtype=np.int8);    del rounds_l
            own_np       = np.array(own_l,       dtype=own_dtype); del own_l
            root_q_np      = np.array(root_q_l,      dtype=np.float32); del root_q_l
            root_q_mask_np = np.array(root_q_mask_l, dtype=np.float32); del root_q_mask_l
            opp_points_np      = np.array(opp_points_l,      dtype=np.float32); del opp_points_l
            opp_points_mask_np = np.array(opp_points_mask_l, dtype=np.float32); del opp_points_mask_l
            value_wdl_np    = np.array(value_wdl_l,    dtype=np.float32); del value_wdl_l
            wdl_outcome_np  = np.array(wdl_outcome_l,  dtype=np.float32); del wdl_outcome_l
            endgame_np      = np.array(endgame_l,      dtype=np.float32); del endgame_l
            endgame_mask_np = np.array(endgame_mask_l, dtype=np.float32); del endgame_mask_l
            ranking_ids_np  = np.array(ranking_ids_l,  dtype=np.int16);   del ranking_ids_l
            ranking_q_np    = np.array(ranking_q_l,    dtype=np.float16); del ranking_q_l
            ranking_mask_np = np.array(ranking_mask_l, dtype=np.float32); del ranking_mask_l
            planes_np    = None
            if planes_l is not None:
                planes_np = np.array(planes_l, dtype=np.uint8)
                del planes_l

            # Bitpacking (RAM-Optimierung v21, PREREG_v21_window.md "RAM-
            # Voraussetzung"): `masks` ist striktes 0/1 (`_pack_bits`),
            # `planes` nur in seinem binaeren Vorderteil (`_pack_planes`) --
            # verlustfrei in beiden Faellen (masks 406->51 B,
            # planes 2844->419 B je Sample, exaktes Layout siehe
            # `_pack_bits`-Kopf-Kommentar oben). `cache_nopack` (bereits Teil
            # des Cache-Keys, s.o.) erzwingt als Notausstieg das alte
            # unkomprimierte Format 1:1. `masks_np`/`planes_np` werden ab hier
            # durch die (ggf. gepackte) Speicherform ERSETZT -- alles danach
            # (HDF5-Schreiben, `self.masks`) bleibt dadurch unabhaengig vom
            # Packmodus unveraendert einfach.
            self.bitpacked = not cache_nopack
            planes_orig_shape = (NUM_PLANES_CHANNELS, 6, 6)
            if self.bitpacked:
                masks_np = _pack_bits(masks_np)  # [N,406] -> [N,51]
                if planes_np is not None:
                    # `_pack_planes`, NICHT `_pack_bits`: der Block ist seit den
                    # zwei Spezialfeld-Kanaelen nicht mehr durchweg binaer.
                    planes_np = _pack_planes(planes_np)  # [N,79,6,6] -> [N,419]

            print(f"Datensatz geladen: {len(states_np)} Züge. "
                  f"(Features pro Zug: {states_np.shape[1]}) — {time.time()-t0:.1f}s")
            print(f"💾 Speichere HDF5-Cache...")
            _masks_key = 'masks_packed' if self.bitpacked else 'masks'
            _planes_key = 'planes_packed' if self.bitpacked else 'planes'
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',               data=states_np,    compression='lzf')
                hf.create_dataset('policies',             data=policies_np,  compression='lzf')
                hf.create_dataset('values',               data=values_np,    compression='lzf')
                hf.create_dataset(_masks_key,             data=masks_np,     compression='lzf')
                if self.bitpacked:
                    hf[_masks_key].attrs['orig_count'] = NUM_ACTIONS
                hf.create_dataset('moon_order_targets',   data=moon_np,      compression='lzf')
                hf.create_dataset('policy_weights',       data=polw_np,      compression='lzf')
                hf.create_dataset('points_forecast',      data=points_np,    compression='lzf')
                hf.create_dataset('rounds',               data=rounds_np,    compression='lzf')
                hf.create_dataset('ownership',            data=own_np,       compression='lzf')
                hf.create_dataset('root_q',               data=root_q_np,      compression='lzf')
                hf.create_dataset('root_q_mask',          data=root_q_mask_np, compression='lzf')
                hf.create_dataset('opp_points_forecast',  data=opp_points_np,      compression='lzf')
                hf.create_dataset('opp_points_mask',      data=opp_points_mask_np, compression='lzf')
                hf.create_dataset('values_wdl',           data=value_wdl_np,     compression='lzf')
                hf.create_dataset('wdl_outcome',          data=wdl_outcome_np,   compression='lzf')
                hf.create_dataset('endgame_margin',       data=endgame_np,       compression='lzf')
                hf.create_dataset('endgame_mask',         data=endgame_mask_np,  compression='lzf')
                hf.create_dataset('ranking_action_ids',   data=ranking_ids_np,   compression='lzf')
                hf.create_dataset('ranking_child_q',      data=ranking_q_np,     compression='lzf')
                hf.create_dataset('ranking_mask',         data=ranking_mask_np,  compression='lzf')
                if planes_np is not None:
                    hf.create_dataset(_planes_key,        data=planes_np,    compression='lzf')
                    if self.bitpacked:
                        hf[_planes_key].attrs['orig_shape'] = planes_orig_shape
            print(f"✅ Cache gespeichert: {cache_path_h5}")
            # RAM-Fix: `planes_np` (die groesste Einzelstruktur, ~3,6 GB beim
            # vollen Korpus, dank Bitpacking jetzt ~450 MB) wird NACH dem
            # Schreiben verworfen statt als `self.planes` fuer die gesamte
            # Trainingsdauer im RAM zu bleiben -- `_open_planes_h5` liest ab
            # jetzt lazy aus der gerade geschriebenen Datei, identisch zum
            # Cache-Lade-Pfad oben.
            # Hinweis: `_resolve_planes_h5_path` liest hier NUR den Pfad um --
            # die Datei selbst wird weiterhin unter `cache_path_h5` (regulaerer
            # Ort) geschrieben; ein Override muesste die frisch geschriebene
            # Datei zusaetzlich manuell an den Override-Ort kopieren.
            self._planes_dataset_name = _planes_key if planes_np is not None else None
            self._planes_h5_path = _resolve_planes_h5_path(cache_path_h5) if planes_np is not None else None
            del planes_np

            self.states             = torch.from_numpy(states_np)
            self.policies           = torch.from_numpy(policies_np)
            self.values             = torch.from_numpy(values_np)
            self.masks              = torch.from_numpy(masks_np)
            self.moon_order_targets = torch.from_numpy(moon_np)
            self.policy_weights     = torch.from_numpy(polw_np)
            self.points_forecast    = torch.from_numpy(points_np)
            self.rounds             = torch.from_numpy(rounds_np)
            self.ownership          = torch.from_numpy(own_np)
            self.root_q             = torch.from_numpy(root_q_np)
            self.root_q_mask        = torch.from_numpy(root_q_mask_np)
            self.opp_points_forecast = torch.from_numpy(opp_points_np)
            self.opp_points_mask     = torch.from_numpy(opp_points_mask_np)
            self.values_wdl          = torch.from_numpy(value_wdl_np)
            self.wdl_outcome         = torch.from_numpy(wdl_outcome_np)
            self.endgame_margin      = torch.from_numpy(endgame_np)
            self.endgame_mask        = torch.from_numpy(endgame_mask_np)
            self.ranking_action_ids  = torch.from_numpy(ranking_ids_np)
            self.ranking_child_q     = torch.from_numpy(ranking_q_np)
            self.ranking_mask        = torch.from_numpy(ranking_mask_np)
            # `self._planes_h5_path` wurde oben bereits gesetzt (RAM-Fix) --
            # kein `self.planes`-Tensor mehr hier.

        self.input_size = self.states.shape[1] if len(self.states) > 0 else 100
        self.value_target_variant = value_target_variant
        self._maybe_load_planes_eager()

    def _maybe_load_planes_eager(self):
        """Laedt den kompletten Planes-HDF5-Inhalt EINMALIG ins RAM
        (`self._planes_eager_tensor`) -- Task #11 Phase 2, seit 2026-07-31
        STANDARDVERHALTEN (vorher lazy als Standard, siehe Historie unten).

        GEMESSENER GRUND FUER DIE UMKEHR: `hf['planes'][idx]`-Einzelzugriffe
        auf den lzf-komprimierten Cache sind ~400.000x langsamer als ein
        In-RAM-Indexzugriff nach einmaligem Voll-Read (205 ms/Sample lazy vs.
        0,5 µs/Sample in-RAM, gemessen auf dem echten 1,3-Mio-Sample-2D-
        Trainingscache) -- bei Batch=256 macht das ~52 s/Batch allein fuer
        Planes-I/O, ein Epoche-1-Batch-100-Herzschlag waere erst nach ~87 min
        faellig gewesen. Die drei vermeintlichen "stillen Abstuerze" des
        lazy-Pfads (2026-07-31) waren mit hoher Wahrscheinlichkeit KEINE
        Abstuerze, sondern kriechend langsame, technisch weiterlaufende
        Prozesse, die beim Task-Management (Stop/Resume) beendet wurden --
        nicht ein Speicherproblem, das laut System-RAM-Log (34,3 GB, 3,6 GB
        Planes je Split) nie real existiert hat.

        `MOSAIC_PLANES_LAZY=1` schaltet auf den lazy Pro-Index-HDF5-Zugriff
        zurueck -- NUR fuer echt knappe RAM-Verhaeltnisse gedacht (Faktor
        ~400.000x langsamer nachweislich in Kauf zu nehmen, wenn 3,6 GB/Split
        nicht ins RAM passen). Kein Effekt bei encoder="flat" (kein
        `_planes_h5_path`)."""
        if self._planes_h5_path is None:
            return
        if os.environ.get("MOSAIC_PLANES_LAZY") == "1":
            print(f"ℹ️  MOSAIC_PLANES_LAZY=1: Planes bleiben lazy (h5py-Pro-Index-Zugriff) -- "
                  f"NUR fuer knappe RAM-Verhaeltnisse gedacht, ~400.000x langsamer als in-RAM "
                  f"(gemessen 2026-07-31, siehe Docstring).")
            return
        import h5py
        # `self._planes_dataset_name`: 'planes_packed' oder 'planes' (RAM-
        # Optimierung v21, Bitpacking) -- selbstbeschreibend am Cache
        # bestimmt, kein zusaetzlicher Zustand noetig.
        with h5py.File(self._planes_h5_path, "r") as hf:
            arr = hf[self._planes_dataset_name][:]
        self._planes_eager_tensor = torch.from_numpy(arr)
        gb = self._planes_eager_tensor.element_size() * self._planes_eager_tensor.nelement() / 1e9
        print(f"Planes komplett ins RAM geladen ({tuple(self._planes_eager_tensor.shape)}, {gb:.2f} GB"
              f"{', gepackt' if self.bitpacked else ''}).")

    def __len__(self): return len(self.states)

    def apply_value_target_lambda(self, lam: float, wdl: bool = False) -> float:
        """λ-Misch-Value-Target-Experiment (Willemsen et al. 2021, "soft-Z"):
        mischt ein Value-Target IN-PLACE mit dem rohen Root-Suchwert
        `self.root_q` ueberall dort, wo `self.root_q_mask` 1 ist --
        `target = lam*target + (1-lam)*root_q(-Skala je nach Zweig)`.
        Samples ohne root_q (Maske 0, z.B. Ein-Aktion-Zuege oder Dateien ohne
        das Feld) bleiben unveraendert (identisch zu lam=1.0), unabhaengig
        von `lam`.

        KORREKTHEITS-FIX (Koordinator-Befund 2026-08-08): frueher mischte
        diese Methode IMMER `self.values` (tanh-Ziel), auch wenn train.py
        mit `--value-head wdl` gegen `self.values_wdl` trainierte -- die
        Mischung lief damit fuer WDL-Laeufe komplett ins Leere (Metriken
        eines λ<1.0-Laufs waren bit-nah identisch zu λ=1.0). `wdl` waehlt
        jetzt explizit das tatsaechlich trainierte Zielfeld:

        - `wdl=False` (Default/Bestandsverhalten): mischt `self.values`
          (tanh-Ziel, Skala [-1,1]) -- fuer diesen Zweig ist nichts anders
          als vorher, `lam=1.0` laesst `self.values` weiterhin KOMPLETT
          UNVERAENDERT (frueher Return-Pfad, keine Tensor-Operation).
        - `wdl=True`: mischt stattdessen `self.values_wdl` (WDL-Ziel, Skala
          [0,1]). SKALEN-DETAIL: `self.root_q` liegt im Cache remapped auf
          [-1,1] (Cache-Bau: `root_q_l.append(float(rq) * 2.0 - 1.0)`),
          `values_wdl` dagegen auf [0,1] (Gewinnwahrscheinlichkeit). Vor der
          Mischung wird root_q daher zurueckgerechnet: `p_root = (root_q+1)/2`
          -- sonst liefe ein [-1,1]-Rohwert direkt in ein [0,1]-Ziel und das
          Ergebnis koennte aus [0,1] herauslaufen (z.B. root_q=-1 wuerde ohne
          Remap ein Ziel von -1 statt 0 mischen). `self.values` bleibt im
          `wdl=True`-Zweig unangetastet, `self.values_wdl` bleibt im
          `wdl=False`-Zweig unangetastet -- jeder Aufruf ruehrt GENAU eines
          der beiden Zielfelder an.

        λ wirkt hier bewusst VOR/unabhaengig von `--wdl-hard-only`
        (trainiert stattdessen auf dem rohen `wdl_outcome`, siehe train.py)
        und `_destretch_wdl_target` (entstaucht `targets_v_wdl` erst im
        Trainings-Loop) -- diese Methode mischt nur das Cache-Feld, das
        `--wdl-hard-only`/destretch als Eingabe sehen.

        Aufrufer (train.py) ruft dies EINMALIG je Dataset (Train- UND
        Val-Split) direkt NACH dem Laden auf, VOR dem `DataLoader`-Wrap --
        jeder Batch liest danach automatisch aus dem gemischten Zielfeld,
        keine Aenderung an `__getitem__`/der Tupel-Form noetig.

        Rueckgabe: Anteil der Samples mit `root_q_mask==1` (Praesenz-Anteil,
        NICHT abhaengig von `lam`/`wdl`) -- fuer das train.py-Logging (PREREG
        verlangt den Misch-Anteil dokumentiert, auch bei lam=1.0 informativ)."""
        if not (0.0 <= lam <= 1.0):
            raise ValueError(
                f"value_target_lambda={lam!r} ausserhalb [0,1] -- harter Abbruch "
                f"statt stillem Clamp (siehe train.py --load-Footgun-Historie)."
            )
        n = len(self.values)
        if n == 0:
            return 0.0
        frac = float(self.root_q_mask.mean().item())
        if lam < 1.0:
            mask_col = self.root_q_mask.unsqueeze(1).bool()  # [N] -> [N,1], matcht self.values/values_wdl
            root_q_col = self.root_q.unsqueeze(1)
            if wdl:
                # Skalen-Fix: root_q ([-1,1]) zurueck auf [0,1] wie values_wdl.
                p_root_col = (root_q_col + 1.0) / 2.0
                mixed = lam * self.values_wdl + (1.0 - lam) * p_root_col
                # Defensiv geclampt: lam in [0,1] und p_root_col in [0,1] (da
                # root_q in [-1,1]) garantieren eine Konvexkombination in
                # [0,1] nur MATHEMATISCH exakt -- Float-Rundung koennte
                # hauchduenn drueber/drunter landen; klare Grenze statt
                # stillem Downstream-Effekt auf die BCE-Loss (Log(0) o.ae.).
                mixed = mixed.clamp(0.0, 1.0)
                self.values_wdl = torch.where(mask_col, mixed, self.values_wdl)
            else:
                mixed = lam * self.values + (1.0 - lam) * root_q_col
                self.values = torch.where(mask_col, mixed, self.values)
        return frac

    def _open_planes_h5(self):
        """Öffnet lazy einen HDF5-Handle für Pro-Index-Planes-Zugriff -- NUR
        genutzt, wenn `MOSAIC_PLANES_LAZY=1` gesetzt ist (`_maybe_load_planes_eager`);
        Standardpfad ist seit 2026-07-31 `self._planes_eager_tensor` (siehe
        dort für die Begründung: lazy Pro-Index-Zugriff ist gemessen
        ~400.000x langsamer, kein Speichervorteil, der das rechtfertigt --
        3,6 GB/Split passen komfortabel ins RAM). Bleibt im Code für echt
        knappe RAM-Verhältnisse. Nur der Dateipfad steht in
        `self._planes_h5_path`, der offene Handle entsteht PRO PROZESS beim
        ersten Zugriff.

        Vorsicht bei künftigem `DataLoader(..., num_workers>0)` unter
        Windows: ein gepickeltes offenes `h5py.File` ist zwischen Prozessen
        nicht sicher teilbar. `__getstate__`/`__setstate__` unten lassen den
        Handle beim Pickeln (Worker-Start) bewusst aus, jeder Worker öffnet
        sich seinen eigenen -- aktuell nutzt `train.py` `num_workers=0`
        (Default, kein expliziter Wert), daher unkritisch, aber vorbereitet."""
        if self._planes_h5_file is None:
            import h5py
            self._planes_h5_file = h5py.File(self._planes_h5_path, "r")
        return self._planes_h5_file

    def _get_planes_tensor(self, idx):
        # RAM-Optimierung v20: uint8 bleibt bis NACH dem Device-Move erhalten
        # (train.py castet batchweise) -- spart 4x Collate-/Transfer-Volumen
        # gegenueber dem frueheren Per-Sample-`.float()`.
        # RAM-Optimierung v21 (Bitpacking): ist `self.bitpacked` True, liefert
        # dies ein FLACHES [419]-Byte-Sample statt [79,6,6] -- das Entpacken
        # passiert NICHT hier (pro Sample), sondern EINMAL pro Batch in
        # train.py (`unpack_planes_batch`, siehe Benchmark-Kommentar dort).
        if self._planes_eager_tensor is not None:
            return self._planes_eager_tensor[idx]
        hf = self._open_planes_h5()
        arr = hf[self._planes_dataset_name][idx]  # EIN Sample -- kein Voll-Array-Read
        return torch.from_numpy(arr)

    def __getstate__(self):
        """Siehe `_open_planes_h5` -- der offene h5py-Handle darf nicht mit-
        gepickelt werden, nur der Pfad überlebt."""
        state = self.__dict__.copy()
        state["_planes_h5_file"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __getitem__(self, idx):
        base = (self.states[idx], self.policies[idx], self.values[idx], self.masks[idx],
                self.moon_order_targets[idx], self.policy_weights[idx], self.points_forecast[idx],
                self.rounds[idx], self.ownership[idx],
                # Task #28 (PREREG_task28_aggression.md): additiv ANS ENDE
                # angehaengt -- Aufrufer, die dieses 9-Tupel noch kennen (z.B.
                # `tools/diagnosis.py`s `*_`-Catch-all), bleiben unberuehrt,
                # solange sie nicht die letzten 2 Elemente per Index erwarten.
                self.opp_points_forecast[idx], self.opp_points_mask[idx],
                # Task #34: erneut additiv ANS ENDE angehaengt (gleiches
                # Muster) -- `values_wdl` (TD-geblendetes WDL-Trainingsziel)
                # + `wdl_outcome` (roher, ungeblendeter Ausgang fuer den
                # arm-uebergreifend vergleichbaren Brier-Score, siehe train.py).
                self.values_wdl[idx], self.wdl_outcome[idx],
                # Schema 18 (PREREG_plate_intervention.md): additiv ANS
                # ENDE, gleiches Muster -- exakter R5-Wurzelwert + Maske.
                self.endgame_margin[idx], self.endgame_mask[idx],
                # Schema 19 (Task #35b, RANKING_CACHE_FIELDS): additiv ANS
                # ENDE, gleiches Muster -- Top-K Geschwister-Aktions-IDs +
                # Q-Werte + Verfuegbarkeits-/pol_w-Maske fuer den paarweisen
                # Policy-Ranking-Loss in train.py (`--ranking-loss-weight`).
                self.ranking_action_ids[idx], self.ranking_child_q[idx], self.ranking_mask[idx])
        # Task #11 Phase 2: bei encoder="2d" wird `planes` ALS ERSTES Element
        # vorangestellt -- `encoder="flat"` (Standard) behaelt exakt die
        # bisherige Tupel-FORM/-POSITION fuer Aufrufer, die den `encoder`-
        # Parameter nicht kennen. Der masks-INHALT (Element 4, `base[3]`) ist
        # seit RAM-Optimierung v21 aber ggf. bitgepackt (siehe `bitpacked`-
        # Doku im Klassen-Docstring) -- Konsumenten muessen `self.bitpacked`
        # pruefen, statt sich auf die Elementform zu verlassen.
        if self.encoder == "2d":
            return (self._get_planes_tensor(idx),) + base
        return base
