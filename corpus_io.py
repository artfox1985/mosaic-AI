# -*- coding: utf-8 -*-
"""Lesen und Schreiben der Korpus-Dateien, transparent komprimiert.

ANLASS (2026-08-26, Nutzer-Frage nach doppeltem Speicherplatz): der hv2-Korpus
belegt 32,9 GB als `.pkl`, der daraus gebaute Cache nur 0,83 GB. Die pkl sind
hochredundant -- gemessen an 12 ordnungsfrei gezogenen Dateien komprimiert
gzip-6 sie um **Faktor 35,4** (Spanne 35,1-35,7), also 32,9 GB auf 0,93 GB.
Entpacken kostet 9 ms je Datei, Packen 0,06 s.

**Warum der Dateiname .pkl BLEIBT und nicht .pkl.gz wird** -- drei Dinge
haengen am Namen, und alle drei wuerden STILL brechen:

1. Der Cache-Schluessel enthaelt die Dateiliste (`neural_net.py`): andere
   Namen => anderer Schluessel => Voll-Neubau jedes bestehenden Caches.
2. `MOSAIC_DATA_EXCLUDE`-Regexe enden auf `\\.pkl$` -- sie wuerden `.pkl.gz`
   nicht mehr treffen und stillschweigend nichts mehr ausschliessen. Genau
   dafuer ist der Filter da (Fenster-Pinning waehrend laufender Generierung).
3. Auswertungen und Zaehlungen globben `*.pkl`.

Erkannt wird deshalb am INHALT: gzip beginnt mit den Magic-Bytes 1f 8b. Eine
unkomprimierte Bestandsdatei wird weiterhin gelesen, ohne dass irgendwo ein
Schalter gesetzt werden muss.

**Die pkl bleiben der Rohstand und werden NICHT durch den Cache ersetzt.** Der
Cache haengt an einem Merkmals-Schema; als `INPUT_SIZE` am 2026-08-25 von 708
auf 714 ging, war jeder bestehende Cache unbrauchbar und nur die pkl erlaubten
den Neubau. Offene Preregs (Spezialfeld-Eingaben, Slot-Ziel,
Huellen-Gewichtung) wuerden dasselbe wieder ausloesen.
"""
import glob
import gzip
import os
import pickle

GZIP_MAGIC = b"\x1f\x8b"
# gzip-6: Faktor 35,4 gemessen. Stufe 1 braeuchte 0,0 s und schafft 10,8x --
# der Unterschied im Packen ist 0,06 s je Datei, der im Ergebnis Faktor 3.
COMPRESS_LEVEL = 6


def is_compressed(path) -> bool:
    """True, wenn die Datei gzip-Inhalt hat -- unabhaengig von der Endung."""
    with open(path, "rb") as f:
        return f.read(2) == GZIP_MAGIC


def load_records(path):
    """Laedt eine Korpus-Datei, komprimiert oder nicht."""
    with open(path, "rb") as f:
        if f.read(2) == GZIP_MAGIC:
            f.seek(0)
            with gzip.open(f, "rb") as g:
                return pickle.load(g)
        f.seek(0)
        return pickle.load(f)


def load_records_fh(fh):
    """Wie `load_records`, aber auf einem bereits offenen Handle.

    Gibt es, damit Aufrufer ihren `with open(...)`-Block behalten koennen --
    in `neural_net.py` haengen rund 490 Zeilen darunter, und ein Dedent waere
    ein Riesendiff ohne Gegenwert.
    """
    header = fh.read(2)
    fh.seek(0)
    if header == GZIP_MAGIC:
        with gzip.open(fh, "rb") as g:
            return pickle.load(g)
    return pickle.load(fh)


def _temp_path_for(path) -> str:
    """Temporaerer Name im SELBEN Ordner (os.replace ist nur innerhalb eines
    Dateisystems atomar). Fuehrender Punkt und Endung `.tmp`: der Name trifft
    weder `*.pkl` (corpus_files, Cache-Schluessel, MOSAIC_DATA_EXCLUDE) noch
    die Zaehlungen der Ketten (`ls data/ | grep -c "^selfplay_..."`). Die PID
    trennt parallele Schreiber derselben Zieldatei."""
    directory, name = os.path.split(os.fspath(path))
    return os.path.join(directory, f".{name}.{os.getpid()}.tmp")


def dump_records(path, obj, compress=True) -> None:
    """Schreibt eine Korpus-Datei. Standard komprimiert, Name bleibt `.pkl`.

    ATOMAR (Code-Review 2026-09-26 #23): erst in eine temporaere Datei daneben,
    dann `os.replace`. Vorher schrieb `open(path, "wb")` direkt -- ein Abbruch
    mitten im Schreiben (Kill, Standby, voller Datentraeger) hinterliess eine
    abgeschnittene `.pkl` unter dem endgueltigen Namen, die jeder Glob als
    fertigen Korpus mitnahm. Jetzt gibt es die Datei entweder vollstaendig oder
    gar nicht; ein Rest bleibt hoechstens als `.<name>.<pid>.tmp` liegen und
    wird bei einem Fehler hier selbst entfernt. Inhalt und Bytes unveraendert."""
    tmp = _temp_path_for(path)
    try:
        with open(tmp, "wb") as f:
            if compress:
                # filename=: der gzip-Kopf traegt den Dateinamen (FNAME, ohne
                # Pfad). Ohne diese Angabe nahme GzipFile ihn aus `f.name`, also
                # den temporaeren Namen samt PID -- die Bytes wichen dann vom
                # Bestand ab und zwischen zwei Laeufen voneinander.
                with gzip.GzipFile(filename=os.fspath(path), fileobj=f, mode="wb",
                                   compresslevel=COMPRESS_LEVEL,
                                   # mtime=0: sonst steckt die Uhrzeit im gzip-Kopf und
                                   # zwei Laeufe mit gleichem Inhalt ergaeben
                                   # verschiedene Bytes. Reproduzierbarkeit vor Kosmetik.
                                   mtime=0) as g:
                    pickle.dump(obj, g)
            else:
                pickle.dump(obj, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def corpus_files(data_dir, pattern="*.pkl"):
    """Sortierte Korpus-Dateiliste. Endung unveraendert -- siehe Modul-Doku."""
    return sorted(glob.glob(os.path.join(data_dir, pattern)))
