#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf"]
# ///
"""Lightweight PDF geometry audit; requires PyMuPDF (`uv run` installs it, or `pip install pymupdf`).

Reports per-page geometry plus a book-level summary: non-embedded fonts, prose measure,
and candidate pages per content type (chapter openings, dense code, figures, short pages,
headings near the page bottom) to pick a representative sample from.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from statistics import median

ICON_FONT = re.compile(r'awesome|icon|symbol|dingbat|emoji', re.I)
MONO_FONT = re.compile(r'mono|code|courier|consol|menlo|cascadia|mplus1mn|inconsolata', re.I)
NOTES = [
    'All page numbers are 1-based PDF page indexes, not printed folios.',
    'Low text coverage, blank pages, and content-type candidates are heuristic flags; manually verify intentional design.',
    'Pages with images but no text (covers, full-page figures) are reported as image_only, not possibly_blank.',
    'Icon fonts (e.g. admonition icons) are excluded from heading-size and measure detection.',
    'measure_chars is the median length of full-width lines in the dominant body font; it includes spaces.',
]


def spans(page):
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            text = ''.join(s['text'] for s in line['spans']).strip()
            if text:
                yield line, line['spans'][0], text


def page_info(page):
    height = page.rect.height
    blocks = [b for b in page.get_text('blocks') if len(b) > 4 and str(b[4]).strip()]
    out = []
    for b in blocks:
        x0, y0, x1, y1 = b[:4]
        if x0 < -1 or y0 < -1 or x1 > page.rect.width + 1 or y1 > height + 1:
            out.append([round(v, 1) for v in (x0, y0, x1, y1)])
    characters = sum(len(str(b[4]).strip()) for b in blocks)
    images = len(page.get_images(full=True))
    lines = [(line, span, text) for line, span, text in spans(page) if not ICON_FONT.search(span['font'])]
    mono = sum(len(text) for _, span, text in lines if MONO_FONT.search(span['font']))
    # ignore running content in the bottom 6% when locating where the body text ends
    body = [line['bbox'][3] for line, _, _ in lines if line['bbox'][3] < height * 0.94]
    return {
        'width_pt': round(page.rect.width, 1), 'height_pt': round(height, 1), 'characters': characters, 'images': images,
        'drawings': len(page.get_drawings()), 'possibly_blank': characters == 0 and images == 0, 'image_only': characters == 0 and images > 0,
        'low_text_coverage': 0 < characters < 120, 'mono_share': round(mono / characters, 2) if characters else 0,
        'max_text_size': round(max((span['size'] for _, span, _ in lines), default=0), 1),
        'body_bottom': round(max(body, default=0) / height, 3), 'out_of_page_blocks': out,
        'fonts': sorted({str(f[3]) for f in page.get_fonts(full=True)}),
    }, lines


def summarize(pdf, pages, page_lines):
    fonts, sizes, body_font = {}, Counter(), Counter()
    for i, page in enumerate(pdf):
        for xref, ext, kind, name, *_ in page.get_fonts(full=True):
            fonts.setdefault(name.split('+')[-1], {'type': kind, 'embedded': ext not in ('n/a', ''), 'pages': set()})['pages'].add(i + 1)
        for _, span, text in page_lines[i]:
            body_font[(span['font'], round(span['size'], 1))] += len(text)
    base_font, base_size = body_font.most_common(1)[0][0] if body_font else (None, 0)
    for lines in page_lines:
        sizes.update({round(span['size']) for _, span, _ in lines})
    # chapter titles: the largest text size used on at least three pages
    chapter_size = max((size for size, count in sizes.items() if count >= 3 and size > base_size * 1.5), default=None)
    full_lines = []
    for lines in page_lines:
        prose = [(line, text) for line, span, text in lines if (span['font'], round(span['size'], 1)) == (base_font, base_size)]
        widest = max((line['bbox'][2] - line['bbox'][0] for line, _ in prose), default=0)
        full_lines += [len(text) for line, text in prose if line['bbox'][2] - line['bbox'][0] > widest * 0.95]
    bottoms = sorted(p['body_bottom'] for p in pages if p['body_bottom'])
    text_bottom = bottoms[int(len(bottoms) * 0.95) - 1] if bottoms else 0
    is_opening = lambda p: chapter_size is not None and round(p['max_text_size']) == chapter_size
    candidates = {
        'chapter_openings': [p['page'] for p in pages if is_opening(p)],
        'code_dense': [p['page'] for p in pages if p['mono_share'] >= 0.5],
        'figures': [p['page'] for p in pages if p['images'] or p['drawings'] >= 40],
        'short_pages_mid_chapter': [p['page'] for n, p in zip(pages[1:] + [None], pages)
                                    if 0 < p['body_bottom'] < text_bottom * 0.6 and n and not is_opening(n)],
        'headings_near_bottom': sorted({i + 1 for i, lines in enumerate(page_lines) for line, span, _ in lines
                                        if span['size'] >= base_size * 1.2 and line['bbox'][1] / pdf[i].rect.height > text_bottom - 0.06}),
    }
    return {
        'page_sizes_pt': sorted({(p['width_pt'], p['height_pt']) for p in pages}),
        'body_font': {'name': base_font, 'size_pt': base_size},
        'measure_chars': round(median(full_lines)) if full_lines else None,
        'chapter_title_size_pt': chapter_size,
        'non_embedded_fonts': {name: sorted(f['pages']) for name, f in fonts.items() if not f['embedded']},
        'fonts': {name: {'type': f['type'], 'embedded': f['embedded'], 'page_count': len(f['pages'])} for name, f in sorted(fonts.items())},
        'candidates': candidates,
    }


def render(fitz, pdf, target, numbers, spreads):
    target.mkdir(parents=True, exist_ok=True)
    zoom = fitz.Matrix(2, 2)
    for i in numbers:
        if not spreads:
            pdf[i].get_pixmap(matrix=zoom, alpha=False).save(str(target / f'page-{i+1:04}.png'))
            continue
        pair = [pdf[i].get_pixmap(matrix=zoom, alpha=False)] + ([pdf[i + 1].get_pixmap(matrix=zoom, alpha=False)] if i + 1 < len(pdf) else [])
        gap = 24
        sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, sum(p.width for p in pair) + gap * (len(pair) - 1), pair[0].height), False)
        sheet.clear_with(128)
        for k, pix in enumerate(pair):
            pix.set_origin(k * (pair[0].width + gap), 0)
            sheet.copy(pix, pix.irect)
        sheet.save(str(target / f'spread-{i+1:04}-{i+len(pair):04}.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pdf')
    parser.add_argument('--json', dest='json_out')
    parser.add_argument('--pages', help='1-based page numbers, comma-separated')
    parser.add_argument('--render-dir', help='Render selected pages at 144 dpi')
    parser.add_argument('--spreads', action='store_true', help='Render each selected page next to the following one; select the left-hand (verso) page')
    parser.add_argument('--summary-only', action='store_true', help='Omit per-page details from the printed report')
    args = parser.parse_args()
    try:
        import pymupdf as fitz
    except ImportError:
        parser.error('PyMuPDF required: run with `uv run`, or pip install pymupdf')
    pdf = fitz.open(args.pdf)
    requested = [int(x) - 1 for x in args.pages.split(',')] if args.pages else []
    if any(x < 0 or x >= len(pdf) for x in requested):
        parser.error('Requested page outside PDF range')
    pages, page_lines = [], []
    for i, page in enumerate(pdf):
        info, lines = page_info(page)
        pages.append({'page': i + 1, **info})
        page_lines.append(lines)
    report = {'file': str(args.pdf), 'page_count': len(pdf), 'summary': summarize(pdf, pages, page_lines), 'pages': pages, 'notes': NOTES}
    if args.render_dir:
        render(fitz, pdf, Path(args.render_dir), requested or range(min(len(pdf), 12)), args.spreads)
    result = json.dumps(report, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(result + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'pages'}, indent=2) if args.summary_only else result)


if __name__ == '__main__':
    main()
