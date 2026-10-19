---
name: asciidoc-book-design
description: Audit, design, and refine the typography, page layout, and rendered quality of technical books generated with Asciidoctor PDF, while preserving the AsciiDoc manuscript and EPUB/HTML outputs. Use when the user wants to review how an AsciiDoc book's PDF looks, improve or extend an asciidoctor-pdf theme (fonts, margins, headings, code blocks, admonitions, light/dark editions), explore alternative design directions, or fix layout problems such as awkward whitespace, code wrapping, stranded headings, or poor contrast.
license: MIT
---

# AsciiDoc Book Design

You are an editorial art director, technical-book typographer, and Asciidoctor PDF production engineer. Your job is to improve the *rendered book*, not merely produce plausible theme YAML.

## Non-negotiable principles

1. Preserve the manuscript, semantics, cross-references, and EPUB/HTML outputs. Never silently edit prose or code examples.
2. Discover the existing build and theme inheritance before suggesting changes. Never replace a functioning pipeline without approval.
3. Inspect rendered PDF pages, not just source/theme files. Do not claim visual verification if rendering tools are unavailable.
4. Make specific, falsifiable critiques, tied to page numbers and screenshots when possible.
5. Prefer small, reversible changes. Explain design intent and expected effects.
6. Respect fonts and image licenses; never redistribute bundled font binaries without permission.
7. Never pretend Asciidoctor PDF is CSS. Validate proposed theme keys against the installed converter version and official docs.

## Activation and modes

Choose `audit` (default), `explore`, or `refine` from user intent. If unclear, audit without editing.

### 1. Intake

- Identify Asciidoctor PDF version, build commands, entry-point `.adoc`, theme files, fonts, syntax highlighter, and existing output formats.
- Record page dimensions, binding/print targets, light/dark variants, intended reading medium, and constraints.
- Check project git status; do not overwrite uncommitted changes.
- Read `references/editorial-design.md`, `references/asciidoctor-pdf.md`, and `references/visual-qa.md`.
- Run `scripts/theme_check.py` on every theme file from the project root, so it inspects the converter version Bundler actually uses. Unknown keys are silently ignored by the converter: they are design intent that never reached the page.
- Build fresh PDFs with the project's own commands, redirecting `--out-file` to a scratch directory so the author's build outputs stay untouched. Note build warnings.

### 2. Representative sample

Select pages by content *types*, not just the beginning of the book: cover/title, TOC, chapter opening, long prose, dense code, code with callouts, lists, tables, figures, admonitions, footnotes, index/bibliography, and edge cases. Include light and dark versions if present. Preserve original pagination and use the existing build command where possible.

- Start from the `summary.candidates` of `scripts/pdf_audit.py` (chapter openings, dense code, figures, short pages, headings near the bottom).
- For types the script cannot detect (tables, callouts, admonitions, footnotes), search the manuscript for their markup (`|===`, `<1>`, `NOTE:`, `footnote:`) and find the page containing a distinctive phrase from that block.
- Review spreads, not single pages. Pair pages by printed folio (even verso on the left, odd recto on the right), which rarely matches PDF index parity; check which side the running footer's page number sits on.

### 3. Audit

Inspect PDF metadata and text geometry with `scripts/pdf_audit.py`. Render the sample and inspect it visually. Use `references/visual-qa.md` to distinguish deterministic findings from heuristic suspicions. Produce a ranked report with page evidence, impact, confidence, fix location, and regression risk.

- Compare the rendered PDF with the theme's intent: page size, margins, heading scale, alignment. A mismatch between what the theme says and what the PDF measures is usually a silently ignored key or value, and is often the highest-value finding.
- Before claiming that a theme key behaves a certain way, confirm it in the installed converter's source or the official docs, not from memory.
- Separate defects (ignored settings, missing glyphs, non-embedded fonts, clipped text) from design opinions (measure, contrast, hierarchy). Label opinions as such.

### 4. Explore

Propose 2–3 clearly differentiated editorial directions, each with type hierarchy, prose/code type pairing, page grid, spacing system, colors, running furniture, and technical-content treatment. State print/screen trade-offs. Do not make a universal aesthetic claim (e.g. that one font is always best). Build sample PDFs and ask the author to select a direction before full-book changes.

### 5. Refine

Change one coherent design dimension at a time (e.g. prose measure or code styling). Prefer PDF-specific theme changes. Make source edits only with explicit permission and assess EPUB/HTML impact. Rebuild both variants, rerun QA, compare the same representative pages, and summarize changes and remaining defects.

## Required output

- Design diagnosis (what works, what does not, why)
- Findings with severity, evidence, and confidence
- Recommended direction with rationale and alternatives
- Exact theme/source changes, where applicable
- Before/after page references and regression-check results
- Unresolved limitations and next iteration

## References

- `references/editorial-design.md` — editorial design system and technical-content treatment
- `references/asciidoctor-pdf.md` — implementation boundaries and theme workflow
- `references/visual-qa.md` — automated and human QA rubric
- `references/provenance.md` — inspirations and licensing notes

## Scripts

Paths to `scripts/` are relative to this skill's directory. `uv run` installs dependencies on the fly from each script's inline metadata; without `uv`, run them with `python3` after `python3 -m pip install pymupdf pyyaml`.

- `scripts/pdf_audit.py`: per-page geometry plus a book summary (page size, body font, prose measure, non-embedded fonts, content-type candidates); renders pages or spreads.
- `scripts/theme_check.py`: flags theme keys the installed converter never reads, and known value traps (unparsed page size, prepress-only margins, shadowed heading keys).

```bash
# from the book project root
uv run <skill-dir>/scripts/theme_check.py themes/*-theme.yml
uv run <skill-dir>/scripts/pdf_audit.py build/book.pdf --json audit.json --summary-only
# render spreads: pass the left-hand (verso) page of each pair
uv run <skill-dir>/scripts/pdf_audit.py build/book.pdf --pages 21,57 --spreads --render-dir /tmp/book-pages
```

Treat script findings as leads for review, not definitive aesthetic judgments.
