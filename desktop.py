#!/usr/bin/env python3
"""
Health Ledger as a desktop application.

This is what the packaged Mac ``.app`` and Windows ``.exe`` run. It does what
``start.sh`` does for a checkout -- start the local server, open a browser --
without a Terminal window, and it adds the one thing a double-clicked app
needs that a terminal does not: a way to quit. A menu-bar icon (macOS) or
system-tray icon (Windows, Linux) carries "Open Health Ledger" and "Quit".

The server is the same Flask app as ``python3 app.py``. It binds to 127.0.0.1
and nothing else, so nothing off this machine can reach it.

    python3 desktop.py              # server, browser and the menu-bar icon
    python3 desktop.py --no-tray    # server and browser only, Ctrl+C to stop
    python3 desktop.py --no-browser # do not open a browser
    python3 desktop.py --port 5005  # ask for a particular port
"""

import argparse
import errno
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import config
from config import APP_NAME, APP_VERSION, DEFAULT_PORT, HOST, get_logger

logger = get_logger('desktop')

# How long to wait for the server to answer before opening the browser anyway.
STARTUP_TIMEOUT_SECONDS = 20.0
STARTUP_POLL_SECONDS = 0.1
# Ports tried after the default one is found busy.
PORT_SEARCH_ATTEMPTS = 20


def find_free_port(preferred: int = DEFAULT_PORT) -> int:
    """
    The port to serve on: the preferred one when it is free, otherwise the
    next free one after it, otherwise whatever the OS hands out.

    A person who double-clicks an app cannot be told to pass a different port
    on the command line, and on macOS the obvious ones are often taken (5000
    by AirPlay Receiver). So the app finds its own instead of refusing to
    start.
    """
    for candidate in range(preferred, preferred + PORT_SEARCH_ATTEMPTS):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((HOST, candidate))
            except OSError as exc:
                if exc.errno in (errno.EADDRINUSE, errno.EACCES):
                    continue
                raise
            return candidate
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((HOST, 0))
        return probe.getsockname()[1]


def serve(port: int) -> None:
    """
    Run the WSGI app until the process ends.

    Waitress when it is installed: it is pure Python, so it bundles into the
    packaged app without a compiler, and it does not print the development
    server warning at somebody who only wanted to open their records. The
    Werkzeug server is the fallback, which is what a plain checkout uses.
    """
    from app import app as flask_app

    try:
        from waitress import serve as waitress_serve
    except ImportError:
        logger.info("waitress not installed; using the Werkzeug server")
        flask_app.run(debug=False, host=HOST, port=port, threaded=True,
                      use_reloader=False)
        return
    waitress_serve(flask_app, host=HOST, port=port, threads=8, _quiet=True)


def wait_until_up(url: str, timeout: float = STARTUP_TIMEOUT_SECONDS) -> bool:
    """
    True once the server answers. Polling beats sleeping for a fixed couple of
    seconds: a first run that has to create the database is slower than that,
    and every later run is much faster.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except urllib.error.HTTPError:
            # An error status still means something is listening and routing.
            return True
        except (urllib.error.URLError, OSError, ConnectionError):
            time.sleep(STARTUP_POLL_SECONDS)
    return False


def _tray_image():
    """
    The menu-bar image: the app icon if it was bundled, otherwise a mark drawn
    on the spot so a missing file cannot stop the app from starting.
    """
    from PIL import Image, ImageDraw

    icon_path = config.BASE_DIR / 'packaging' / 'icon.png'
    if icon_path.is_file():
        try:
            return Image.open(icon_path).convert('RGBA').resize((64, 64))
        except OSError:
            logger.warning("Could not read %s; drawing the mark instead", icon_path)

    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, size - 3, size - 3), radius=12, fill=(23, 23, 23, 255))
    # Three ledger rules, the middle one in the brand red.
    for index, top in enumerate((20, 30, 40)):
        colour = (220, 38, 38, 255) if index == 1 else (245, 245, 245, 255)
        draw.rounded_rectangle((16, top, size - 17, top + 4), radius=2, fill=colour)
    return image


def run_tray(url: str, stop: threading.Event) -> None:
    """
    Show the menu-bar / tray icon. Must be called on the main thread: that is
    a macOS requirement for anything that touches the status bar.
    """
    import pystray

    def on_open(_icon=None, _item=None):
        webbrowser.open(url)

    def on_quit(icon, _item=None):
        stop.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(f'Open {APP_NAME}', on_open, default=True),
        pystray.MenuItem(f'{APP_NAME} {APP_VERSION} — {url}', None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Quit', on_quit),
    )
    pystray.Icon(APP_NAME, _tray_image(), APP_NAME, menu).run()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f'{APP_NAME} desktop launcher')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'port to serve on (default {DEFAULT_PORT}, or the next free one)')
    parser.add_argument('--no-browser', action='store_true', help='do not open a browser')
    parser.add_argument('--no-tray', action='store_true', help='do not show the menu-bar icon')
    args = parser.parse_args(argv)

    port = find_free_port(args.port)
    url = f'http://{HOST}:{port}'

    logger.info("%s %s starting on %s", APP_NAME, APP_VERSION, url)
    logger.info("Records folder: %s", config.DATA_ROOT)

    stop = threading.Event()
    server = threading.Thread(target=serve, args=(port,), name='health-ledger-server',
                              daemon=True)
    server.start()

    if not wait_until_up(url):
        logger.error("The server did not answer on %s within %.0f seconds.",
                     url, STARTUP_TIMEOUT_SECONDS)
        return 1

    if not args.no_browser:
        webbrowser.open(url)

    if args.no_tray:
        print(f'{APP_NAME} is running at {url}  (Ctrl+C to stop)')
        try:
            while not stop.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        return 0

    try:
        run_tray(url, stop)
    except ImportError:
        # pystray is not installed, or there is no display to put an icon on
        # (a headless Linux box). Serving without a way to quit beats not
        # serving; the terminal still has Ctrl+C.
        logger.info("No menu-bar icon available; running until interrupted.")
        print(f'{APP_NAME} is running at {url}  (Ctrl+C to stop)')
        try:
            while not stop.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
