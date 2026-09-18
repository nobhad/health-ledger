#!/bin/bash
# Sync the design-system token layer from no-bhad-codes into this project.
#
# The files under static/css/design-system/ are VENDORED copies of the
# no-bhad-codes design system (its tokens, reset, fonts and layer order).
# Re-run this script to pull a newer version. Do not hand-edit the vendored
# files; if something needs to change, change it upstream and re-sync.
#
# Two patches are applied on copy, and only these two:
#   1. fonts.css     -> font URLs point at Flask's /static/fonts/ instead of /fonts/
#   2. portal-theme.css, buttons.css
#                    -> the portal surface selector [data-page="client"] becomes
#                       [data-page="ledger"], which is what base.html sets on <body>
set -euo pipefail

SRC="${NO_BHAD_CODES_DIR:-$HOME/Projects/Development/Active/no-bhad-codes}"
DST="$(cd "$(dirname "$0")/.." && pwd)/static/css/design-system"
FONTS_DST="$(cd "$(dirname "$0")/.." && pwd)/static/fonts"

if [ ! -d "$SRC/src/design-system/tokens" ]; then
  echo "no-bhad-codes not found at $SRC (set NO_BHAD_CODES_DIR)" >&2
  exit 1
fi

mkdir -p "$DST/tokens" "$FONTS_DST/Inconsolata"

cp "$SRC/src/design-system/tokens/"*.css "$DST/tokens/"
cp "$SRC/src/design-system/index.css"      "$DST/index.css"
cp "$SRC/src/styles/core/layer-order.css"  "$DST/layer-order.css"
cp "$SRC/src/styles/base/reset.css"        "$DST/reset.css"
cp "$SRC/src/styles/base/fonts.css"        "$DST/fonts.css"
cp "$SRC/public/fonts/Inconsolata/Inconsolata-Regular.woff2" "$FONTS_DST/Inconsolata/"
cp "$SRC/public/fonts/Inconsolata/Inconsolata-Bold.woff2"    "$FONTS_DST/Inconsolata/"
mkdir -p "$FONTS_DST/Acme" "$(dirname "$FONTS_DST")/images"
cp "$SRC/public/fonts/Acme/Acme-Regular.woff2" "$SRC/public/fonts/Acme/Acme-Regular.ttf" "$FONTS_DST/Acme/"
# The footer band reuses the site's avatar art
cp "$SRC/public/images/avatar.svg" "$(dirname "$FONTS_DST")/images/avatar.svg"
# The sidebar brand mark (masked with the current text colour)
cp "$SRC/public/images/avatar_small_sidebar.svg" "$(dirname "$FONTS_DST")/images/avatar_small_sidebar.svg"

# Patch 1: font paths
sed -i '' 's|url("/fonts/|url("/static/fonts/|g' "$DST/fonts.css"

# Patch 2: portal surface selector
sed -i '' 's/data-page="client"/data-page="ledger"/g' "$DST/tokens/portal-theme.css" "$DST/tokens/buttons.css"

REV="$(git -C "$SRC" log -1 --format='%h (%ci)')"
cat > "$DST/VENDORED.md" <<MD
# Vendored design system

Copied from no-bhad-codes at commit ${REV} by \`scripts/sync_design_system.sh\`.
Do not edit these files by hand. Re-run the script to update.

Contents: \`tokens/\` (the 11 token files plus \`portal-theme.css\`), \`index.css\`,
\`layer-order.css\`, \`reset.css\`, \`fonts.css\`. Fonts live in \`static/fonts/\`.

Patches applied on copy (see the script): font URLs use \`/static/fonts/\`, and the
portal surface selector \`[data-page="client"]\` is renamed to \`[data-page="ledger"]\`.

Health Ledger's own stylesheets live beside this directory and only ever
reference tokens defined here.
MD
echo "synced from $REV"
