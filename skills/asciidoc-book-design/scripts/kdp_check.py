#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf"]
# ///
"""Check a print-interior PDF against Amazon KDP's published requirements.

Requirements come from data/kdp.json (sources and check date inside). Re-verify them on
KDP's help pages before final submission advice. The PDF is read as a print file: PDF page 1
is a right-hand (recto) page. Also estimates page counts and code columns at every KDP trim.
"""
import argparse
import json
import re
from pathlib import Path
from statistics import median

SPEC = Path(__file__).with_name('data') / 'kdp.json'
INKS = ['black-white', 'black-cream', 'black-groundwood', 'standard-color-white', 'premium-color-white']
MONO_FONT = re.compile(r'mono|code|courier|consol|menlo|cascadia|mplus1mn|inconsolata', re.I)
TOL = 1.5  # points
STATUS_ORDER = {'fail': 0, 'warn': 1, 'info': 2, 'pass': 3}


def trim_name(trim):
    return '%gx%g' % tuple(trim)


def gutter_for(spec, pages):
    return next((row['inside'] for row in spec['gutter_in'] if pages <= row['max_pages']), None)


def limits(entry, ink):
    return entry['pages'][INKS.index(ink)] if entry else None


def fit(entry, ink, low, high):
    if entry is None:
        return 'n/a'
    lim = limits(entry, ink)
    if lim is None:
        return 'not offered'
    if lim[0] <= low and high <= lim[1]:
        return 'yes'
    return 'maybe' if low <= lim[1] else 'no'


def find_trim(spec, binding, width, height):
    bw, bh = spec['bleed_in']['width'] * 72, spec['bleed_in']['height'] * 72
    for entry in spec[binding]:
        tw, th = entry['trim'][0] * 72, entry['trim'][1] * 72
        if abs(width - tw) <= TOL and abs(height - th) <= TOL:
            return entry, False
        if abs(width - tw - bw) <= TOL and abs(height - th - bh) <= TOL:
            return entry, True
    return None, None


def rgb(value):
    if isinstance(value, int):
        return ((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255
    return tuple(value[:3]) if value and len(value) >= 3 else (value[0],) * 3 if value else None


def luminance(color):
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in color]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def hexcolor(color):
    return '#%02x%02x%02x' % tuple(round(c * 255) for c in color)


def pages_list(pages, limit=20):
    pages = sorted(set(pages))
    return pages[:limit] + (['…%d more' % (len(pages) - limit)] if len(pages) > limit else [])


def analyze(fitz, pdf):
    """Collect per-page content geometry and the facts the checks need."""
    out = []
    for i, page in enumerate(pdf):
        rect, area = page.rect, page.rect.width * page.rect.height
        boxes, background, text_boxes = [], False, []
        for b in page.get_text('blocks'):
            if str(b[4]).strip():
                boxes.append(fitz.Rect(b[:4]) & rect)
                text_boxes.append(fitz.Rect(b[:4]) & rect)
        images = page.get_image_info()
        boxes += [fitz.Rect(img['bbox']) & rect for img in images]
        drawings = page.get_drawings()
        for d in drawings:
            r = d['rect']
            if r.width * r.height >= 0.95 * area:
                background = background or (d.get('fill') is not None and min(d['fill']) < 0.99)
            elif not r.is_empty or r.width or r.height:
                boxes.append(fitz.Rect(r) & rect)
        spans = [s for b in page.get_text('dict')['blocks'] for l in b.get('lines', []) for s in l['spans'] if s['text'].strip()]
        folios = [w[4] for w in page.get_text('words') if w[4].isdigit() and (w[1] > rect.height * 0.92 or w[3] < rect.height * 0.08)]
        out.append({'index': i, 'rect': rect, 'boxes': [b for b in boxes if not b.is_empty or b.width or b.height],
                    'text_boxes': text_boxes, 'background': background, 'images': images, 'drawings': drawings,
                    'spans': spans, 'folios': folios})
    return out


def touches_edge(box, rect):
    return box.x0 <= TOL or box.y0 <= TOL or box.x1 >= rect.width - TOL or box.y1 >= rect.height - TOL


def margins(info):
    """(inside, outside, top, bottom) in points for a page, treating even indexes as recto.

    Elements touching the page edge are bleed elements; the bleed check reports them instead.
    """
    w, h = info['rect'].width, info['rect'].height
    boxes = [b for b in info['boxes'] if not touches_edge(b, info['rect'])]
    if not boxes:
        return None
    x0 = min(b.x0 for b in boxes); x1 = max(b.x1 for b in boxes)
    y0 = min(b.y0 for b in boxes); y1 = max(b.y1 for b in boxes)
    left, right = x0, w - x1
    recto = info['index'] % 2 == 0
    return (left, right, y0, h - y1) if recto else (right, left, y0, h - y1)


def check(spec, pdf, pages, args, file_size):
    results = []
    add = lambda status, cid, message, evidence=None: results.append({'status': status, 'check': cid, 'message': message, 'pages': evidence or []})
    width, height = pages[0]['rect'].width, pages[0]['rect'].height
    if any(abs(p['rect'].width - width) > TOL or abs(p['rect'].height - height) > TOL for p in pages):
        add('fail', 'page-size', 'pages have different sizes; KDP needs one size and orientation throughout',
            [p['index'] + 1 for p in pages if abs(p['rect'].width - width) > TOL or abs(p['rect'].height - height) > TOL])
    entry, bleed = find_trim(spec, args.binding, width, height)
    if entry:
        add('pass', 'trim', '%.2f x %.2fin matches KDP %s trim %s%s%s' % (width / 72, height / 72, args.binding, trim_name(entry['trim']),
                                                                   ' with bleed' if bleed else ' without bleed', ' (large trim)' if entry['large'] else ''))
    else:
        add('fail', 'trim', '%.2f x %.2fin is not a KDP %s trim size (with or without bleed)' % (width / 72, height / 72, args.binding))
    count = len(pdf) + len(pdf) % 2
    lim = limits(entry, args.ink)
    if entry and lim is None:
        add('fail', 'page-count', '%s is not offered for %s %s' % (args.ink, args.binding, trim_name(entry['trim'])))
    elif lim and not lim[0] <= count <= lim[1]:
        add('fail', 'page-count', '%d pages (rounded to even) outside the %d-%d allowed for this trim/ink/paper' % (count, *lim))
    elif lim:
        add('pass', 'page-count', '%d pages (rounded to even) within %d-%d' % (count, *lim))
    gutter = gutter_for(spec, count)
    if gutter is None:
        add('fail', 'gutter', 'no KDP gutter defined for %d pages' % count)
    outside_min = spec['outside_min_in']['bleed' if bleed else 'no_bleed'] * 72
    short = {'inside': [], 'outside': [], 'top': [], 'bottom': []}
    for p in pages:
        m = margins(p)
        if not m:
            continue
        # distances from the trim line: bleed adds the width bleed outside and half the height bleed top and bottom
        offset = {'inside': 0, 'outside': spec['bleed_in']['width'] * 72, 'top': spec['bleed_in']['height'] * 36, 'bottom': spec['bleed_in']['height'] * 36}
        for side, value in zip(('inside', 'outside', 'top', 'bottom'), m):
            if bleed:
                value -= offset[side]
            need = (gutter or 0) * 72 if side == 'inside' else outside_min
            if value < need - 0.5:
                short[side].append((p['index'] + 1, value))
    if gutter is not None:
        for side in ('inside', 'outside', 'top', 'bottom'):
            need = gutter if side == 'inside' else outside_min / 72
            if short[side]:
                values = [v for _, v in short[side]]
                add('fail', 'margin-' + side, '%s margin below the KDP minimum of %.3fin on %d pages (typically %.2fin, smallest %.2fin); all content, including running heads and page numbers, must sit inside it'
                    % (side, need, len(values), median(values) / 72, min(values) / 72), pages_list(pg for pg, _ in short[side]))
            else:
                add('pass', 'margin-' + side, '%s margin meets the %.3fin minimum%s' % (side, need, ' for %d pages' % count if side == 'inside' else ''))
    edge = [p['index'] + 1 for p in pages if any(touches_edge(b, p['rect']) for b in p['boxes'])]
    backgrounds = [p['index'] + 1 for p in pages if p['background']]
    if not bleed and (edge or backgrounds):
        add('fail', 'bleed', 'content reaches the page edge or fills the page background but the file has no bleed; if one page bleeds, set up the whole file with bleed', pages_list(edge + backgrounds))
    fonts = {}
    for i, page in enumerate(pdf):
        for xref, ext, kind, name, *_ in page.get_fonts(full=True):
            if ext in ('n/a', ''):
                fonts.setdefault(name.split('+')[-1], set()).add(i + 1)
    for name, where in fonts.items():
        add('fail', 'fonts', 'font %s is not embedded' % name, pages_list(where))
    if not fonts:
        add('pass', 'fonts', 'all fonts embedded')
    small = [p['index'] + 1 for p in pages if any(s['size'] < spec['min_font_size_pt'] - 0.05 for s in p['spans'])]
    smallest = min((s['size'] for p in pages for s in p['spans']), default=0)
    add('warn' if small else 'pass', 'font-size', 'text below %gpt on %d pages (smallest %.1fpt)' % (spec['min_font_size_pt'], len(small), smallest) if small
        else 'no text below %gpt' % spec['min_font_size_pt'], pages_list(small))
    thin = {}
    for p in pages:
        for d in p['drawings']:
            if d.get('color') is not None and d.get('width') is not None and d['width'] < spec['min_line_weight_pt'] - 0.01:
                thin.setdefault(round(d['width'], 2), set()).add(p['index'] + 1)
    if thin:
        common = sorted(thin, key=lambda w: -len(thin[w]))[:4]
        add('warn', 'line-weight', 'lines thinner than %gpt on %d pages; most common: %s' % (spec['min_line_weight_pt'], len(set().union(*thin.values())),
            ', '.join('%gpt (%d pages)' % (w, len(thin[w])) for w in common)), pages_list(set().union(*thin.values())))
    else:
        add('pass', 'line-weight', 'no lines thinner than %gpt' % spec['min_line_weight_pt'])
    low_dpi, high_dpi = {}, set()
    for p in pages:
        for img in p['images']:
            bw, bh = img['bbox'][2] - img['bbox'][0], img['bbox'][3] - img['bbox'][1]
            if bw <= 0 or bh <= 0:
                continue
            dpi = min(img['width'] / (bw / 72), img['height'] / (bh / 72))
            if dpi < spec['min_image_dpi']:
                low_dpi[p['index'] + 1] = min(low_dpi.get(p['index'] + 1, dpi), dpi)
            elif dpi > spec['max_image_dpi_recommended'] * 1.5:
                high_dpi.add(p['index'] + 1)
    if low_dpi:
        add('fail', 'image-dpi', 'raster images below %d DPI at printed size (lowest %d DPI)' % (spec['min_image_dpi'], min(low_dpi.values())), pages_list(low_dpi))
    else:
        add('pass', 'image-dpi', 'all raster images at least %d DPI at printed size' % spec['min_image_dpi'])
    if high_dpi:
        add('info', 'image-dpi', 'images well above the recommended %d DPI maximum; downsampling reduces file size' % spec['max_image_dpi_recommended'], pages_list(high_dpi))
    blank = [not p['boxes'] for p in pages]
    runs, start = [], None
    for i, b in enumerate(blank + [False]):
        if b and start is None:
            start = i
        elif not b and start is not None:
            runs.append((start, i - 1)); start = None
    limit = spec['max_consecutive_blank_pages']
    bad = [r for r in runs if (r[1] - r[0] + 1) > (limit['end'] if r[1] == len(pages) - 1 else limit['start_or_middle'])]
    add('fail' if bad else 'pass', 'blank-pages', 'too many consecutive blank pages (max %d at start/middle, %d at end)' % (limit['start_or_middle'], limit['end']) if bad
        else '%d blank pages, no runs over the limits' % sum(blank), [r[0] + 1 for r in bad])
    if args.ink.startswith('black'):
        colors, weak = {}, {}
        for p in pages:
            for s in p['spans']:
                c = rgb(s['color'])
                if max(c) - min(c) > 0.06:
                    colors.setdefault(hexcolor(c), set()).add(p['index'] + 1)
                contrast = 1.05 / (luminance(c) + 0.05)
                if contrast < 4.5:
                    weak.setdefault(hexcolor(c), set()).add(p['index'] + 1)
        if colors:
            add('warn', 'color-text', '%d text colors print as grey with black ink; check that meaning (syntax highlighting, links) survives: %s'
                % (len(colors), ', '.join(sorted(colors, key=lambda k: -len(colors[k]))[:8])), pages_list(set().union(*colors.values())))
        if weak:
            add('warn', 'gray-contrast', '%d text colors fall below 4.5:1 on white paper once printed in grey: %s' % (len(weak), ', '.join(
                '%s (%d pages)' % (c, len(weak[c])) for c in sorted(weak, key=lambda k: -len(weak[k]))[:6])), pages_list(set().union(*weak.values())))
        fills = {}
        for p in pages:
            for d in p['drawings']:
                f = rgb(d.get('fill'))
                if f and 0 < (1 - luminance(f)) * 100 < spec['min_gray_fill_percent_black_ink']:
                    fills.setdefault(hexcolor(f), set()).add(p['index'] + 1)
        if fills:
            add('warn', 'gray-fill', 'fills lighter than %d%% grey (KDP recommends at least %d%% for grey backgrounds with black ink): %s' % (
                spec['min_gray_fill_percent_black_ink'], spec['min_gray_fill_percent_black_ink'], ', '.join('%s ~%d%% (%d pages)' % (
                    c, round((1 - luminance(rgb(int(c[1:], 16)))) * 100), len(fills[c])) for c in sorted(fills, key=lambda k: -len(fills[k]))[:5])),
                pages_list(set().union(*fills.values())))
        color_images = [p['index'] + 1 for p in pages if any(img.get('colorspace', 1) > 1 for img in p['images'])]
        if color_images:
            add('info', 'color-images', 'color raster images print in greyscale; check screenshots and charts still read', pages_list(color_images))
    if pdf.get_toc():
        add('warn', 'bookmarks', 'PDF has %d bookmarks; KDP guidelines say files should not contain bookmarks (asciidoctor-pdf: -a outline!)' % len(pdf.get_toc()))
    links = sum(len(page.get_links()) for page in pdf)
    if links:
        add('warn', 'annotations', '%d link annotations; KDP guidelines say files should not contain annotations, and printed links need their URLs visible (media=print or prepress shows them)' % links)
    if pdf.is_encrypted or pdf.needs_pass:
        add('fail', 'encryption', 'PDF is encrypted or locked')
    if file_size > spec['max_file_size_mb'] * 1024 * 1024:
        add('fail', 'file-size', 'file is %.0fMB, above the %dMB limit' % (file_size / 1048576, spec['max_file_size_mb']))
    numbered = [(p['index'], int(p['folios'][0])) for p in pages if len(p['folios']) == 1]
    wrong = [i + 1 for i, n in numbered if (n % 2 == 1) != (i % 2 == 0)]
    if numbered and len(wrong) > len(numbered) / 2:
        add('fail', 'folios', 'even page numbers fall on right-hand pages (KDP needs even numbers on the left); screen builds use virtual folios, build print with media=prepress', pages_list(wrong))
    elif numbered:
        add('pass', 'folios', 'page numbers follow print parity (odd on right-hand pages)')
    first = pages[0]
    if not first['spans'] and any((img['bbox'][2] - img['bbox'][0]) * (img['bbox'][3] - img['bbox'][1]) > 0.9 * first['rect'].width * first['rect'].height for img in first['images']):
        add('warn', 'cover', 'page 1 is a full-page image, likely the cover; KDP takes the cover as a separate file (recommendation, not a stated KDP rule)', [1])
    if count != len(pdf):
        add('info', 'page-count', 'KDP rounds %d pages up to %d' % (len(pdf), count))
    return results, entry, bleed


def estimate(spec, pdf, pages, args):
    """Rough page counts at each trim from the body text area; assumes the same type sizes and leading."""
    body = []
    for p in pages:
        h = p['rect'].height
        boxes = [b for b in p['text_boxes'] if h * 0.08 < b.y0 and b.y1 < h * 0.92]
        if len(boxes) >= 3:
            body.append((min(b.x0 for b in boxes), p['rect'].width - max(b.x1 for b in boxes), min(b.y0 for b in boxes), h - max(b.y1 for b in boxes)))
    if not body:
        return None
    left, right, top, bottom = (median(v) / 72 for v in zip(*body))
    w, h = pages[0]['rect'].width / 72, pages[0]['rect'].height / 72
    area = (w - left - right) * (h - top - bottom)
    widths = [s['bbox'][2] - s['bbox'][0] for p in pages for s in p['spans'] if MONO_FONT.search(s['font']) and len(s['text']) >= 10]
    lens = [len(s['text']) for p in pages for s in p['spans'] if MONO_FONT.search(s['font']) and len(s['text']) >= 10]
    char = median(wd / n for wd, n in zip(widths, lens)) / 72 if widths else None
    outside = max(min(left, right), spec['outside_min_in']['no_bleed'])
    rows = []
    for entry in spec['paperback']:
        tw, th = entry['trim']
        est = len(pdf)
        for _ in range(3):  # the gutter grows with the page count
            inside = max(gutter_for(spec, est) or spec['gutter_in'][-1]['inside'], max(left, right))
            text_w = tw - inside - outside
            est = round(len(pdf) * area / (text_w * (th - top - bottom))) if text_w > 0 else 0
        hard = next((e for e in spec['hardcover'] if e['trim'] == entry['trim']), None)
        low, high = round(est * 0.85), round(est * 1.15)
        rows.append({'trim': trim_name(entry['trim']), 'large': entry['large'], 'pages_low': low, 'pages_high': high,
                     'text_width_in': round(text_w, 2), 'code_columns': int(text_w / char) if char else None,
                     'paperback': fit(entry, args.ink, low, high), 'hardcover': fit(hard, args.ink, low, high)})
    return {'measured_margins_in': {'left': round(left, 2), 'right': round(right, 2), 'top': round(top, 2), 'bottom': round(bottom, 2)},
            'current_text_width_in': round(w - left - right, 2), 'current_code_columns': int((w - left - right) / char) if char else None,
            'assumptions': 'same type sizes and leading; margins as measured, inside margin at least the KDP gutter; +/-15%; recto chapter starts in prepress builds add pages',
            'trims': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pdf')
    parser.add_argument('--binding', choices=['paperback', 'hardcover'], default='paperback')
    parser.add_argument('--ink', choices=INKS, default='black-white', help='ink and paper option (default: black-white)')
    parser.add_argument('--estimate', action='store_true', help='Estimate page counts and code columns at every KDP trim')
    parser.add_argument('--json', dest='json_out')
    args = parser.parse_args()
    try:
        import pymupdf as fitz
    except ImportError:
        parser.error('PyMuPDF required: run with `uv run`, or pip install pymupdf')
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    pdf = fitz.open(args.pdf)
    pages = analyze(fitz, pdf)
    results, entry, bleed = check(spec, pdf, pages, args, Path(args.pdf).stat().st_size)
    results.sort(key=lambda r: STATUS_ORDER[r['status']])
    report = {'file': args.pdf, 'spec_checked': spec['checked'], 'sources': spec['sources'], 'binding': args.binding, 'ink': args.ink,
              'trim': trim_name(entry['trim']) if entry else None, 'bleed': bleed, 'page_count': len(pdf), 'checks': results}
    if args.estimate:
        report['estimate'] = estimate(spec, pdf, pages, args)
    print('KDP %s, %s ink/paper; requirements checked %s (re-verify: %s)' % (args.binding, args.ink, spec['checked'], spec['sources']['submission_guidelines']))
    for r in results:
        print('  %-5s %-14s %s%s' % (r['status'].upper(), r['check'], r['message'], ('  pages: %s' % ', '.join(map(str, r['pages']))) if r['pages'] else ''))
    est = report.get('estimate')
    if est:
        print('\nEstimated at each paperback trim (%s)' % est['assumptions'])
        print('  current: text width %.2fin, ~%s code columns' % (est['current_text_width_in'], est['current_code_columns']))
        print('  %-11s %-6s %-11s %-11s %-8s %-10s %s' % ('trim', 'large', 'pages', 'text width', 'code col', 'paperback', 'hardcover'))
        for row in est['trims']:
            print('  %-11s %-6s %-11s %-11s %-8s %-10s %s' % (row['trim'], 'yes' if row['large'] else 'no', '%d-%d' % (row['pages_low'], row['pages_high']),
                                                          '%.2fin' % row['text_width_in'], row['code_columns'], row['paperback'], row['hardcover']))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, default=list) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
