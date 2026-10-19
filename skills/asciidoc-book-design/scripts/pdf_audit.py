#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf"]
# ///
"""Lightweight PDF geometry audit; requires PyMuPDF (`uv run` installs it, or `pip install pymupdf`)."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf')
    parser.add_argument('--json', dest='json_out')
    parser.add_argument('--pages', help='1-based page numbers, comma-separated')
    parser.add_argument('--render-dir', help='Render selected pages at 144 dpi')
    args = parser.parse_args()
    try:
        import fitz
    except ImportError:
        parser.error('PyMuPDF required: run with `uv run`, or pip install pymupdf')
    pdf = fitz.open(args.pdf)
    requested = [int(x) - 1 for x in args.pages.split(',')] if args.pages else []
    if any(x < 0 or x >= len(pdf) for x in requested):
        parser.error('Requested page outside PDF range')
    report = {'file': str(args.pdf), 'page_count': len(pdf), 'pages': [], 'notes': ['Low text coverage and blank pages are heuristic flags; manually verify intentional design.', 'Pages with images but no text (covers, full-page figures) are reported as image_only, not possibly_blank.']}
    for i, page in enumerate(pdf):
        blocks = [b for b in page.get_text('blocks') if len(b) > 4 and str(b[4]).strip()]
        out = []
        for b in blocks:
            x0, y0, x1, y1 = b[:4]
            if x0 < -1 or y0 < -1 or x1 > page.rect.width + 1 or y1 > page.rect.height + 1:
                out.append([round(v, 1) for v in (x0, y0, x1, y1)])
        characters = sum(len(str(b[4]).strip()) for b in blocks)
        fonts = sorted({str(f[3]) for f in page.get_fonts(full=True)})
        images = len(page.get_images(full=True))
        report['pages'].append({'page': i + 1, 'width_pt': round(page.rect.width, 1), 'height_pt': round(page.rect.height, 1), 'characters': characters, 'images': images, 'possibly_blank': characters == 0 and images == 0, 'image_only': characters == 0 and images > 0, 'low_text_coverage': 0 < characters < 120, 'out_of_page_blocks': out, 'fonts': fonts})
    if args.render_dir:
        target = Path(args.render_dir)
        target.mkdir(parents=True, exist_ok=True)
        for i in (requested or range(min(len(pdf), 12))):
            pdf[i].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(str(target / f'page-{i+1:04}.png'))
    result = json.dumps(report, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(result + '\n', encoding='utf-8')
    print(result)


if __name__ == '__main__':
    main()
