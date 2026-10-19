# Visual QA rubric

## Deterministic checks (where PDF extraction permits)
- Page count and size consistency; font list and embedded-font metadata
- Text outside the media/crop box; page text bounds
- Unexpected blank pages (some are intentional for recto starts)
- Repeated running heads/footers, text overlap candidates, exceptionally low text coverage
- PDF build warnings, missing glyphs, unresolved references, broken assets
- Rendered page size and side margins match what the theme intends (see silent failures in `asciidoctor-pdf.md`)
- Every font embedded: print-on-demand services commonly reject PDFs with non-embedded fonts, typically base-14 Helvetica pulled in by SVG diagrams
- Theme keys and values the converter actually reads (`scripts/theme_check.py`)
- Prose measure in characters per line (`summary.measure_chars`) at the real page size
- Contrast ratios computed from the theme's hex colors for body text, links, inline code, code comments, and running furniture, in each edition

## Heuristic checks requiring confirmation
- Low-density pages and extreme whitespace
- Very short final lines, awkward page endings, stranded headings
- Code wrapping, poor code/comment contrast, uneven visual hierarchy
- Figure/caption separation and inconsistent table treatment
- Light/dark edition readability and layout parity
- Raster screenshots: UI text shrunk below legible size at column width, and light-mode screenshots glaring in a dark edition
- Justified text with wide word gaps, especially in narrow boxes (admonitions, sidebars) and around long inline code or URLs

## Pitfalls of automated detection
- Icon fonts (admonition icons) are often the largest text on a page; exclude them before inferring headings from font size.
- Pages with vector diagrams have no images but many drawing operations; tables and code boxes also produce drawings.
- Chapter-ending pages are legitimately short; only short pages followed by more of the same chapter are suspicious.
- A heading low on the page is not stranded if two or more lines follow it; check the rendered page.
- Zero-padded or slashed glyphs may be a typeface feature or caption format, not corruption; check the extracted text before reporting.

## Visual inspection procedure
1. Generate a contact sheet plus full-resolution samples.
2. Inspect chapter starts, dense technical pages, and flagged pages.
3. Compare facing-page spreads and the same page before/after changes.
4. Assign severity (critical/major/minor), confidence, exact page, and evidence.
5. Do not classify intentional blank verso pages as defects without context.

## Acceptance gates
- No clipped or missing text, broken references, or unintended blank pages.
- Code remains semantically identical and readable.
- Body and code contrast is appropriate in both variants.
- No new regressions in page furniture, figure placement, or EPUB/HTML builds.
- Any subjective design claim is supported by a rendered example and rationale.
