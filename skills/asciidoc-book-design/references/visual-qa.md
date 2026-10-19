# Visual QA rubric

## Deterministic checks (where PDF extraction permits)
- Page count and size consistency; font list and embedded-font metadata
- Text outside the media/crop box; page text bounds
- Unexpected blank pages (some are intentional for recto starts)
- Repeated running heads/footers, text overlap candidates, exceptionally low text coverage
- PDF build warnings, missing glyphs, unresolved references, broken assets

## Heuristic checks requiring confirmation
- Low-density pages and extreme whitespace
- Very short final lines, awkward page endings, stranded headings
- Code wrapping, poor code/comment contrast, uneven visual hierarchy
- Figure/caption separation and inconsistent table treatment
- Light/dark edition readability and layout parity

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
