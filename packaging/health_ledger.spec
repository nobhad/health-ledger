# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the packaged Health Ledger.

    pyinstaller packaging/health_ledger.spec --noconfirm

Built as a one-folder app on both platforms, not a one-file executable: a
one-file build unpacks the whole bundle into a temporary directory on every
launch, which is slow and is what antivirus software tends to object to on
Windows. The folder is what gets wrapped -- in a .dmg on macOS, a .zip on
Windows -- so the person still downloads a single file.

WeasyPrint is deliberately excluded. Its Python package installs anywhere,
but it is a binding onto Pango/GTK, which are C libraries that are not
redistributable inside a bundle without shipping and relocating half of
Homebrew. The app already degrades without it: Doctor Docs offers "Open
printable version" and the browser's own print dialog saves the PDF. See
pdf_generator.pdf_unavailable_reason.
"""

import sys
from pathlib import Path

# SPECPATH is set by PyInstaller to the directory holding this spec file.
HERE = Path(SPECPATH).resolve()
ROOT = HERE.parent

APP_NAME = 'Health Ledger'
# Windows and Linux dislike spaces in an executable name; macOS wraps the
# binary in a .app whose name is what people actually see.
EXE_NAME = 'Health Ledger' if sys.platform == 'darwin' else 'HealthLedger'
BUNDLE_ID = 'codes.nobhad.health-ledger'


def _version() -> str:
    """Read APP_VERSION out of config.py without importing it (importing
    config has side effects: it reads a .env and creates loggers)."""
    for line in (ROOT / 'config.py').read_text(encoding='utf-8').splitlines():
        if line.startswith('APP_VERSION'):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    return '0.0.0'


VERSION = _version()

# Everything the running app reads off disk. Templates and static files are
# found through config.BASE_DIR, which resolves to the unpack directory.
datas = [
    (str(ROOT / 'templates'), 'templates'),
    (str(ROOT / 'static'), 'static'),
    (str(ROOT / 'genetic_profile_db_schema.sql'), '.'),
    (str(HERE / 'icon.png'), 'packaging'),
]

# Modules reached only through a string or a late import, which the analysis
# cannot see from the source.
hiddenimports = [
    'waitress',
    'pystray',
    'PIL.Image',
    'PIL.ImageDraw',
]
if sys.platform == 'darwin':
    hiddenimports += ['pystray._darwin']
elif sys.platform == 'win32':
    hiddenimports += ['pystray._win32']
else:
    hiddenimports += ['pystray._xorg']

excludes = [
    # See the note at the top: a C binding that cannot travel in the bundle.
    'weasyprint',
    # Test and build tooling that analysis picks up through dev installs.
    'pytest', 'unittest', '_pytest', 'pyinstaller',
    # Large scientific stacks pulled in by the optional extras only.
    'tkinter', 'numpy', 'matplotlib', 'cv2', 'Bio', 'pydicom', 'pytesseract',
]

a = Analysis(
    [str(ROOT / 'desktop.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # console=False: double-clicking the app must not open a terminal. The
    # menu-bar icon in desktop.py is how it is quit instead.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(HERE / ('icon.icns' if sys.platform == 'darwin' else 'icon.ico')),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=EXE_NAME,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=str(HERE / 'icon.icns'),
        bundle_identifier=BUNDLE_ID,
        version=VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'NSHighResolutionCapable': True,
            # The app keeps a Dock icon as well as the menu-bar one. A
            # menu-bar-only app (LSUIElement) would leave someone with no way
            # to quit at all on a machine where the status item fails to
            # appear.
            'LSUIElement': False,
            'LSMinimumSystemVersion': '11.0',
            'NSHumanReadableCopyright': (
                'Health Ledger. Source-available; see LICENSE. '
                'Not a medical device and not a substitute for professional '
                'medical advice.'
            ),
        },
    )
