"""
Mosaic-AI — Standalone-Launcher (Task #96)

Startet den Flask-Server (server.py) auf einem freien Port und öffnet
anschließend automatisch den Standard-Browser. Gedacht als PyInstaller-
Einstiegspunkt (onedir-Bundle) für Empfänger ohne Python/Rust-Installation.

Verhalten im normalen Repo-Betrieb: `python run_mosaic.py` funktioniert
genauso wie im gebauten Bundle (nur ohne PyInstaller-Frozen-Pfade).
"""

import socket
import sys
import threading
import time
import webbrowser

PREFERRED_PORT = 5000


def _find_free_port(preferred: int) -> int:
    """Gibt `preferred` zurück, falls frei, sonst den ersten freien Port
    danach (bis zu 50 Versuche)."""
    for port in [preferred] + list(range(preferred + 1, preferred + 51)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Kein freier Port im Bereich "
                        f"{preferred}-{preferred + 50} gefunden.")


def _open_browser_delayed(url: str) -> None:
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass  # Kein Browser gefunden -- Nutzer kann die URL manuell öffnen.


def main() -> None:
    port = _find_free_port(PREFERRED_PORT)
    url = f"http://127.0.0.1:{port}"

    # server.py erst hier importieren (nicht auf Modulebene), damit der
    # Port-Scan bereits abgeschlossen ist, bevor Flask/Rust-Engine geladen
    # werden -- hält die Fehlerausgabe bei Portproblemen übersichtlich.
    import server  # noqa: E402  (bewusst spät importiert)

    print("=" * 60)
    print("  Mosaic-AI")
    print("=" * 60)
    if port != PREFERRED_PORT:
        print(f"  Port {PREFERRED_PORT} war belegt -- verwende Port {port} stattdessen.")
    print(f"  Spiel läuft unter: {url}")
    print("  Der Browser sollte sich gleich automatisch öffnen.")
    print("  Beenden: dieses Fenster schließen oder Strg+C drücken.")
    print("=" * 60)

    threading.Thread(target=_open_browser_delayed, args=(url,), daemon=True).start()

    try:
        server.app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nMosaic-AI beendet.")
        sys.exit(0)


if __name__ == "__main__":
    main()
