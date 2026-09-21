#!/usr/bin/env bash
#
# Build "Health Ledger.app" and wrap it in a .dmg for download.
#
#   packaging/build_macos.sh
#
# Output: dist/HealthLedger-<version>-macOS-<arch>.dmg
#
# The build uses its own virtual environment (build/venv) so the project's
# ./venv, which has the test tooling and WeasyPrint in it, cannot leak into
# the bundle.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"
BUILD_VENV="$ROOT/build/venv"
PY="$BUILD_VENV/bin/python"

# config.py writes APP_VERSION with double quotes, so cut on those.
VERSION="$(grep -m1 '^APP_VERSION' config.py | cut -d'"' -f2)"
[ -n "$VERSION" ] || { echo "Could not read APP_VERSION from config.py"; exit 1; }
ARCH="$(uname -m)"
DMG_NAME="HealthLedger-${VERSION}-macOS-${ARCH}"

echo "==> Health Ledger ${VERSION} for macOS (${ARCH})"

if [ ! -x "$PY" ]; then
    echo "==> Creating the build environment in build/venv"
    python3 -m venv "$BUILD_VENV"
fi

echo "==> Installing build requirements"
"$PY" -m pip install -q --disable-pip-version-check --upgrade pip
# WeasyPrint is stripped from the runtime list: the bundle cannot carry its
# Pango/GTK libraries, and the app falls back to the browser's print dialog.
grep -v -i '^weasyprint' requirements.txt > "$ROOT/build/requirements-runtime.txt"
"$PY" -m pip install -q --disable-pip-version-check \
    -r "$ROOT/build/requirements-runtime.txt" \
    -r packaging/requirements-build.txt

echo "==> Drawing the icons"
"$PY" packaging/make_icons.py

echo "==> Building the app bundle"
rm -rf "$ROOT/dist/Health Ledger.app" "$ROOT/build/Health Ledger"
"$PY" -m PyInstaller packaging/health_ledger.spec --noconfirm \
    --distpath "$ROOT/dist" --workpath "$ROOT/build/pyinstaller"

APP="$ROOT/dist/Health Ledger.app"
[ -d "$APP" ] || { echo "Build produced no app bundle at $APP"; exit 1; }

# An unsigned app is quarantined by Gatekeeper on the machine that downloads
# it. Ad-hoc signing does not avoid that (only a paid Developer ID does), but
# it does keep macOS from refusing to run the app locally, and it makes the
# bundle's own contents consistent.
echo "==> Ad-hoc signing"
codesign --force --deep --sign - "$APP" 2>/dev/null || \
    echo "    (codesign unavailable; the app is unsigned)"

echo "==> Building the disk image"
STAGE="$(mktemp -d)"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cp "$ROOT/LICENSE" "$STAGE/LICENSE.txt" 2>/dev/null || true
rm -f "$ROOT/dist/${DMG_NAME}.dmg"
hdiutil create -volname "Health Ledger" -srcfolder "$STAGE" -ov -format UDZO \
    "$ROOT/dist/${DMG_NAME}.dmg" >/dev/null
rm -rf "$STAGE"

echo
echo "==> Done: dist/${DMG_NAME}.dmg"
du -h "$ROOT/dist/${DMG_NAME}.dmg" | cut -f1 | sed 's/^/    size: /'
echo
echo "    The app is not notarized, so the first launch needs right-click ->"
echo "    Open. INSTALL.md tells the person that."
