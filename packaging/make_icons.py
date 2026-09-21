#!/usr/bin/env python3
"""
Draw the application icon in the three shapes a packaged build needs.

    python3 packaging/make_icons.py

Writes, beside this file:

    icon.png    1024px master, and what the menu-bar icon uses
    icon.icns   macOS app bundle (built with iconutil, so macOS only)
    icon.ico    Windows executable

The mark is deliberately plain: the ledger's rules on the brand's near-black
ground, the middle rule in the brand red. The two colours are the design
system's own (--color-gray-900 and the brand red named in
static/css/design-system/tokens/colors.css), so the icon cannot drift away
from the app it opens. Replace this file's drawing, not the generated
images, if the mark should change.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent

# Both from static/css/design-system/tokens/colors.css.
GROUND = (23, 23, 23, 255)        # --color-gray-900  #171717
BRAND_RED = (220, 38, 38, 255)    # the brand red     #dc2626
RULE = (245, 245, 245, 255)       # --color-gray-100-ish, the light rules

MASTER_SIZE = 1024
# Sizes macOS wants in an .icns, and Windows in an .ico.
ICNS_SIZES = (16, 32, 64, 128, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def draw_icon(size: int = MASTER_SIZE) -> Image.Image:
    """The mark, at any size. Every measurement is a fraction of `size` so
    the small renderings are the same drawing, not a resampled big one."""
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    inset = size * 0.02
    radius = size * 0.22
    draw.rounded_rectangle((inset, inset, size - inset, size - inset),
                           radius=radius, fill=GROUND)

    # Three rules, evenly spaced about the centre; the middle one is the red.
    rule_x0 = size * 0.24
    rule_x1 = size * 0.76
    rule_height = size * 0.065
    gap = size * 0.155
    centre = size / 2
    for index, offset in enumerate((-gap, 0.0, gap)):
        top = centre + offset - rule_height / 2
        colour = BRAND_RED if index == 1 else RULE
        # The middle rule is shorter, so the mark reads as a ledger entry
        # rather than three equal bars.
        x1 = rule_x1 - (size * 0.14 if index == 1 else 0)
        draw.rounded_rectangle((rule_x0, top, x1, top + rule_height),
                               radius=rule_height / 2, fill=colour)
    return image


def write_png(path: Path) -> None:
    draw_icon(MASTER_SIZE).save(path, format='PNG')
    print(f'wrote {path.relative_to(HERE.parent)}')


def write_ico(path: Path) -> None:
    draw_icon(MASTER_SIZE).save(
        path, format='ICO', sizes=[(s, s) for s in ICO_SIZES])
    print(f'wrote {path.relative_to(HERE.parent)}')


def write_icns(path: Path) -> None:
    """macOS only: iconutil turns an .iconset folder into an .icns."""
    if sys.platform != 'darwin' or not shutil.which('iconutil'):
        print('skipping icon.icns (needs macOS and iconutil)')
        return
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / 'icon.iconset'
        iconset.mkdir()
        for size in ICNS_SIZES:
            draw_icon(size).save(iconset / f'icon_{size}x{size}.png')
            # The @2x variant of the next size down, which is the same pixels.
            half = size // 2
            if half in ICNS_SIZES:
                draw_icon(size).save(iconset / f'icon_{half}x{half}@2x.png')
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(path)],
                       check=True)
    print(f'wrote {path.relative_to(HERE.parent)}')


def main() -> int:
    write_png(HERE / 'icon.png')
    write_ico(HERE / 'icon.ico')
    write_icns(HERE / 'icon.icns')
    return 0


if __name__ == '__main__':
    sys.exit(main())
