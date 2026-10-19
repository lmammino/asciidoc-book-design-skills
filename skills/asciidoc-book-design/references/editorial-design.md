# Editorial design principles for technical books

## Design from content
Read the book's intended audience, reading mode, subject matter, and chapter structure. A technical reference and a narrative tutorial need different densities and navigational affordances. Preserve authorial voice and content hierarchy.

## Typography
- Establish a coherent type system for body, display headings, code, captions, running heads, and marginal elements.
- Test body size and line length at actual physical page size. As a *starting hypothesis*, evaluate roughly 55–80 characters per prose line; adjust based on typeface, page width, language, and audience.
- Check x-height, glyph differentiation (1/l/I, 0/O), punctuation, italics, Unicode, ligatures, and syntax highlighting.
- Choose a deliberate vertical rhythm: line height, paragraph spacing, heading proximity, and separation between examples and explanations.
- Prefer a restrained number of font families; justify additional families by functional role.

## Page architecture
- Consider trim, inner/outer margins, binding, running furniture, page numbers, recto/verso symmetry, and chapter openings.
- Use whitespace purposefully. Distinguish deliberate breathing room from awkward empty space caused by pagination.
- Avoid stranded headings and cramped bottoms of pages; inspect spreads, not just isolated pages.
- Keep captions associated with figures, and avoid splitting conceptual units without a clear reason.

## Technical material
- Code is primary reading content: prioritize legibility, indentation, line numbering (if useful), and line-wrap semantics over decorative treatments.
- Evaluate long lines and callout anchors separately. Never silently change code to make it fit.
- Tables need clear headers, sufficient row spacing, and readable multi-page continuation.
- Admonitions should be recognizable without relying solely on color. Diagrams should remain legible at actual print size.
- Screenshots: estimate the rendered size of their smallest meaningful text (source pixel height × display width ÷ source width). If it is far below caption size, crop to the relevant region, enlarge, or annotate instead of shrinking a full window. Dark editions need dark-mode captures or a deliberate frame.
- Inline code competes with prose when it is both bold and filled; one emphasis signal is usually enough, and long inline literals wrap poorly in justified text and table cells.
- Running furniture can be quieter than body text, but keep it readable: in dark editions low-contrast grey footers fall off quickly.
- Syntax highlighting needs adequate contrast in both light and dark editions; test representative tokens and subdued comments.

## Design exploration
For each proposed direction specify: descriptive name, editorial intent, type hierarchy, font pairing, page measure, palette, treatment of code/tables/figures, chapter-opening rhythm, and implementation feasibility. Render comparable sample pages; avoid making decisions from moodboards alone.
