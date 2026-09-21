#!/usr/bin/env python3
"""
Draw the application icon in the three shapes a packaged build needs.

    python3 packaging/make_icons.py

Writes, beside this file:

    icon.svg    the mark itself, the thing to edit
    icon.png    1024px master, and what the menu-bar icon uses
    icon.icns   macOS app bundle (built with iconutil, so macOS only)
    icon.ico    Windows executable

The mark is the arrow avatar -- the same silhouette the sidebar and the
footer use, read straight out of static/images/avatar_small_sidebar.svg so
the two cannot drift apart -- over Lucide's heartline, in the brand red, on
the near-black ground. A person and a vital sign: what the app is for.

The SVG is rasterised by headless Chrome rather than a Python SVG library,
because the avatar is a real vector path and nothing in requirements.txt can
render one. Chrome is already required to be on the machine for nothing else
here, so if it is missing the PNG is left alone and only the sizes derived
from it are rebuilt -- commit icon.png and a build without Chrome still works.
"""

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AVATAR_SVG = ROOT / 'static' / 'images' / 'avatar_small_sidebar.svg'

# All three from static/css/design-system/tokens/colors.css.
GROUND = '#171717'      # --color-gray-900
BRAND_RED = '#dc2626'   # the brand red
MARK = '#f5f5f5'        # the light the avatar is inverted to on dark ground

MASTER_SIZE = 1024
ICNS_SIZES = (16, 32, 64, 128, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)

# Lucide "heart-pulse": the heart with the trace through it. Drawn on a
# 24x24 grid. node_modules/lucide -> HeartPulse, copied rather than imported
# so building the icons does not need npm install.
#
# The outline is FILLED here rather than stroked, and the pulse is knocked
# out of it in the ground colour. A stroked heart at this scale is a 1px
# hairline in a 64px icon and disappears; a solid shape with a notch in it
# survives all the way down.
HEART_PATH = (
    'M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5'
    'c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5'
)
PULSE_PATH = 'M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27'

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# The digest of the icon.svg that the committed icon.png was rendered from.
# A fresh clone gets whatever mtimes git felt like writing, so "is the PNG
# newer than the SVG" is a coin flip on a build machine -- and losing it
# means the icon in a release is whatever that runner's Chrome drew rather
# than the drawing that was reviewed. The digest does not care about clocks.
RENDER_STAMP_NAME = 'icon.svg.sha256'


def avatar_paths() -> list:
    """The silhouette's path data, from the file the app itself renders."""
    svg = AVATAR_SVG.read_text(encoding='utf-8')
    # \sd=" and not d=", or the d inside id="HEAD" matches first.
    return re.findall(r'\sd="([^"]+)"', svg)


def build_svg(size: int = MASTER_SIZE) -> str:
    """
    The mark, as SVG.

    Laid out on a 1024 grid: a rounded square ground, the avatar centred in
    the upper two thirds at the size the footer gives it, and the heartline
    across the lower third, full width between the margins so it reads as a
    trace rather than a small glyph.
    """
    paths = avatar_paths()
    body = '\n'.join(
        f'      <path d="{d}" fill="{MARK}"/>' for d in paths)

    # Arrow dominates: the avatar is the mark, and the heart is layered over
    # its shoulder rather than sitting under it as a second, separate object.
    # The avatar's own viewBox is 288x356.
    avatar_h = 790
    avatar_scale = avatar_h / 356
    avatar_w = 288 * avatar_scale
    avatar_x = 150
    avatar_y = 95

    # heart_x is set so the notch between the heart's two lobes sits on
    # Arrow's back contour: measured from an avatar-only render, that
    # contour is at x=694 at the dip's height, and the dip is at
    # heart_x + heart_w/2.
    # The heart overlaps the silhouette's lower right. Where it crosses the
    # white it needs separation, so it carries a ring of the ground colour
    # drawn beneath its own fill (paint-order), and the pulse is knocked out
    # of it in the same colour.
    heart_w = 370
    heart_scale = heart_w / 24
    heart_x = 508
    heart_y = 588

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}"
     viewBox="0 0 1024 1024" role="img" aria-label="Health Ledger">
  <rect x="16" y="16" width="992" height="992" rx="225" fill="{GROUND}"/>
  <g transform="translate({avatar_x:.1f} {avatar_y}) scale({avatar_scale:.4f})">
{body}
  </g>
  <g transform="translate({heart_x:.1f} {heart_y}) scale({heart_scale:.4f})">
    <path d="{HEART_PATH}" fill="{BRAND_RED}" stroke="{GROUND}" stroke-width="2.6"
          stroke-linejoin="round" paint-order="stroke"/>
    <path d="{PULSE_PATH}" fill="none" stroke="{GROUND}" stroke-width="1.9"
          stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>
'''


def write_svg(path: Path) -> None:
    """
    Write the drawing, but only when it has actually changed.

    Rewriting an identical file still moves its mtime, and render_png skips
    the Chrome pass by comparing icon.svg's mtime against icon.png's. Writing
    unconditionally here made the SVG newer on every single run, so the skip
    could never fire and every build re-rendered the icon.
    """
    svg = build_svg()
    if path.is_file() and path.read_text(encoding='utf-8') == svg:
        print(f'{path.relative_to(ROOT)} unchanged')
        return
    path.write_text(svg, encoding='utf-8')
    print(f'wrote {path.relative_to(ROOT)}')


def svg_digest(svg_text: str) -> str:
    return hashlib.sha256(svg_text.encode('utf-8')).hexdigest()


def render_png(svg_path: Path, png_path: Path) -> bool:
    """
    Rasterise with headless Chrome. False when nothing was rendered.

    Only when the drawing has actually changed, judged by the digest of the
    SVG rather than by file times: every build runs this script, and
    re-rendering each time would make the icon in a release depend on
    whichever Chrome the build machine happens to have.
    """
    stamp = svg_path.parent / RENDER_STAMP_NAME
    digest = svg_digest(svg_path.read_text(encoding='utf-8'))
    if (png_path.is_file() and stamp.is_file()
            and stamp.read_text(encoding='utf-8').strip() == digest):
        print('icon.png was rendered from this exact drawing; keeping it')
        return True
    if not Path(CHROME).exists():
        print('skipping icon.png (needs Google Chrome to rasterise the SVG); '
              'the committed one is kept')
        return False
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / 'icon.html'
        page.write_text(
            '<!doctype html><meta charset=utf-8>'
            '<style>html,body{margin:0;padding:0;background:transparent}</style>'
            + svg_path.read_text(encoding='utf-8'), encoding='utf-8')
        subprocess.run([
            CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
            '--hide-scrollbars', f'--user-data-dir={tmp}/profile',
            '--default-background-color=00000000',
            f'--window-size={MASTER_SIZE},{MASTER_SIZE}',
            '--virtual-time-budget=4000',
            f'--screenshot={png_path}', str(page),
        ], check=True, capture_output=True)
    stamp.write_text(digest + '\n', encoding='utf-8')
    print(f'wrote {png_path.relative_to(ROOT)} and {stamp.relative_to(ROOT)}')
    return True


def write_ico(png_path: Path, path: Path) -> None:
    Image.open(png_path).convert('RGBA').save(
        path, format='ICO', sizes=[(s, s) for s in ICO_SIZES])
    print(f'wrote {path.relative_to(ROOT)}')


def write_icns(png_path: Path, path: Path) -> None:
    """macOS only: iconutil turns an .iconset folder into an .icns."""
    if sys.platform != 'darwin' or not shutil.which('iconutil'):
        print('skipping icon.icns (needs macOS and iconutil)')
        return
    master = Image.open(png_path).convert('RGBA')
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / 'icon.iconset'
        iconset.mkdir()
        for size in ICNS_SIZES:
            scaled = master.resize((size, size), Image.LANCZOS)
            scaled.save(iconset / f'icon_{size}x{size}.png')
            half = size // 2
            if half in ICNS_SIZES:
                scaled.save(iconset / f'icon_{half}x{half}@2x.png')
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(path)],
                       check=True)
    print(f'wrote {path.relative_to(ROOT)}')


def main() -> int:
    svg = HERE / 'icon.svg'
    png = HERE / 'icon.png'
    write_svg(svg)
    if not render_png(svg, png) and not png.is_file():
        print('no icon.png to work from; cannot build the other sizes')
        return 1
    write_ico(png, HERE / 'icon.ico')
    write_icns(png, HERE / 'icon.icns')
    return 0


if __name__ == '__main__':
    sys.exit(main())
