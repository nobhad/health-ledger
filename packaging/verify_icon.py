#!/usr/bin/env python3
"""
Check that a built .icns really carries the icon that was reviewed.

    python3 packaging/verify_icon.py "<app>/Contents/Resources/icon.icns" \
        packaging/icon.png

An .icns is a container, and iconutil varies its metadata and compression
between macOS versions and even between runs, so comparing two .icns files
byte for byte reports differences that do not exist in the image. That kind
of false mismatch is worse than no check: it argues for rebuilding a release
that was fine. This unpacks the container and compares pixels.

Run by the release workflow on the macOS job, so a build whose icon is not
the committed one fails instead of being published.
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageChops

icns = Path(sys.argv[1])
master = Path(sys.argv[2])

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / 'x.iconset'
    subprocess.run(['iconutil', '-c', 'iconset', str(icns), '-o', str(out)],
                   check=True, capture_output=True)
    pngs = sorted(out.glob('*.png'), key=lambda p: p.stat().st_size)
    if not pngs:
        print('no PNGs inside the icns'); sys.exit(2)
    biggest = pngs[-1]
    a = Image.open(biggest).convert('RGBA')
    b = Image.open(master).convert('RGBA')
    print(f'largest inside icns : {biggest.name}  {a.size}')
    print(f'committed master    : {master.name}  {b.size}')
    if a.size != b.size:
        b = b.resize(a.size, Image.LANCZOS)
        print('  (master resized for comparison)')
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if bbox is None:
        print('IDENTICAL pixels'); sys.exit(0)
    # how different, in case it is just antialiasing
    stats = diff.convert('L').getextrema()
    changed = sum(1 for px in diff.convert('L').getdata() if px > 8)
    print(f'DIFFERS: bbox={bbox}  max channel delta={stats[1]}  '
          f'pixels over threshold={changed} of {a.size[0]*a.size[1]}')
    sys.exit(1)
