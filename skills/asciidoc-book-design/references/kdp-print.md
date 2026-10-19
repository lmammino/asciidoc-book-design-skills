# Print on demand with Amazon KDP

Read this when the author mentions print, paperback, hardcover, trim size, or Amazon KDP. KDP's requirements live in `scripts/data/kdp.json` with their sources and the date they were checked. They change over time: re-verify on KDP's help pages before giving final submission advice, and update the data file when they differ.

## Intake
Record, or ask when it changes the advice:
- Binding: paperback, hardcover, or both. Hardcover allows 75 to 550 pages and only five trims.
- Ink and paper: black ink on white, cream, or groundwood paper; standard color; or premium color. Black ink is the cheapest. Standard color requires 72 to 600 pages.
- Whether any page needs bleed (images to the edge). Most technical books do not.
- Whether screen editions (light/dark PDF, EPUB, HTML) stay as they are. They should: print is an extra build, not a replacement.

## Choosing a trim size
- Run `scripts/kdp_check.py <current.pdf> --estimate` to shortlist trims. It projects page counts from the current text area and shows how many code columns fit at the current code size. The estimate holds type sizes constant and is roughly ±15%. Prepress builds add blank pages before recto chapter starts.
- Weigh page count against limits and cost. Large trims (wider than 6.12in or taller than 9in) cost more to print. A book near 550 pages loses the hardcover option.
- Code decides more than prose does. Compare the code columns at each trim with the book's long listings (measure them in the PDF or the included sources). Too few columns means wrapped code on every page, and shrinking the code font below about 8.5pt trades one problem for another.
- Many technical books use 7×10in or 7.5×9.25in. Treat that as a starting point to test, not a rule. Build two or three trims in `explore` mode and compare the same pages (dense code, tables, a diagram, a chapter opening).

## The print build
Keep print as a separate theme that extends the screen theme, so screen editions are unaffected:

```yaml
extends: ./basic-theme.yml   # the existing screen theme
page:
  size: [7in, 10in]            # an array or a name; "7in x 10in" is not parsed in a theme
  margin: [0.75in, 0.75in, 0.9in, 0.75in]
  margin-inner: 0.875in         # at least the KDP gutter for the final page count, plus comfort
  margin-outer: 0.6in
```

Build it with `-a media=prepress` (inner/outer margins, print folios, recto chapter starts, and visible link URLs, since non-screen media show them) and `-a outline!` (no PDF bookmarks). For black ink, also choose a monochrome syntax style. Pygments ships `bw`, `algol_nu`, and `friendly_grayscale`; check what the installed highlighter offers. Every value above is an example to test with `kdp_check.py`, not a recommendation.

## What `kdp_check.py` verifies, and how to fix failures
- **Trim and page count** against the table for the binding and ink.
- **Margins** for all content, including running heads and page numbers, measured from the trim line. The required inside margin (gutter) grows with the page count. Asciidoctor PDF draws running content inside the page margin, so the footer can sit closer to the edge than the margin suggests. Adjust the bottom margin or the footer's height and padding, then re-check.
- **Bleed**: content touching the edge, or a full-page background color, requires a bleed setup for the whole file. A colored page background (dark editions) is a screen-only design.
- **Fonts** all embedded. SVG diagrams are the usual culprit: see "SVG text fonts" in `asciidoctor-pdf.md`.
- **Text at least 7pt.** SVG diagram text shrinks when a smaller trim narrows the column, so re-check after changing trims.
- **Lines at least 0.75pt.** Theme defaults for footer rules, table grids, and admonition rules are often thinner; raise them in the print theme. Fine lines inside diagrams have to be fixed at the source.
- **Images at least 300 DPI** at printed size. Screenshots are often both low resolution and illegible when shrunk; crop them.
- **Black ink**: colors print as grey. The check flags text colors that drop below 4.5:1 on white once grey (line numbers, light comments, orange or cyan tokens) and fills under KDP's 10% grey recommendation (pale admonition and highlight backgrounds).
- **Blank pages**: at most 4 consecutive at the start or middle and 10 at the end.
- **Folios**: even page numbers on left-hand pages. Screen builds use virtual folios and fail this check, so build print with `media=prepress`.
- **Bookmarks and annotations**: KDP's guidelines say files should not contain them. `-a outline!` removes bookmarks. Link annotations need a post-processing step, for example with PyMuPDF: `for page in doc: [page.delete_link(l) for l in page.get_links()]`, then save.
- **Cover**: a full-page image on page 1 is probably the cover. KDP takes the cover as a separate one-page file, a full wrap whose spine width comes from KDP's cover calculator for the final page count and paper. Do not compute the spine width from memory.

## Limits of on-screen review
Paper, ink density, grey fills, and how thin lines actually print cannot be judged from a PDF. Recommend ordering a printed proof before publishing, and never claim print quality was verified on screen. The Kindle eBook is a separate (EPUB-based) product and outside this workflow.
