# Asciidoctor PDF implementation notes

Official references:
- https://docs.asciidoctor.org/pdf-converter/latest/theme/
- https://docs.asciidoctor.org/pdf-converter/latest/theme/create-theme/
- https://docs.asciidoctor.org/pdf-converter/latest/theme/language/
- https://docs.asciidoctor.org/pdf-converter/latest/theme/apply-theme/

## Discover first
Run `asciidoctor-pdf --version` if installed. Locate themes, theme inheritance, `pdf-theme`, `pdf-themesdir`, `pdf-fontsdir`, document attributes, Rouge/Pygments configuration, custom extensions, and actual build scripts. Do not assume default commands are sufficient for a multi-file book.

## Theme boundaries
YAML themes can control many font, color, spacing, page, and running-content properties. They are not CSS and have limited control over positioning and pagination. For unsupported layout requirements, investigate documented converter extensions, or record as a limitation. Never invent theme keys. Theme files use `-theme.yml` convention; extending a working theme is safer than starting from scratch.

## Example: small, intentionally conservative override
```yaml
extends: default
base:
  font-color: '#24272B'
heading:
  font-color: '#182D3A'
link:
  font-color: '#155E91'
```
This is a demonstration, not a recommended universal aesthetic. Verify the installed version, render, and compare.

## Silent failures (verified against asciidoctor-pdf 2.3.x source)
The converter ignores unknown keys and unparseable values without warnings. These traps were confirmed by reading the converter and measuring the rendered PDF; re-check them if the installed version differs.

- **Unknown keys do nothing.** For example, there is no `admonition-text-align` or `sidebar-align`: admonition and sidebar paragraphs inherit `base-text-align`, so a justified base makes them justified too. `scripts/theme_check.py` lists such keys.
- **`page-size` string form.** In a theme, `size: 8.5in x 11in` is not parsed and falls back to A4. Use `size: [8.5in, 11in]` or a name such as `Letter`. The `W x H` form only works for the `pdf-page-size` document attribute.
- **Inner/outer margins need prepress.** `page-margin-inner` and `page-margin-outer` apply only when `media=prepress`. Otherwise the side margins come from `page-margin`. Prepress also changes folio placement and blank-page handling, so build and review it as a separate variant.
- **Heading sizes are per level.** `heading-font-size` is a fallback that the default theme's `heading-h1-font-size` to `heading-h6-font-size` override. Those inherited sizes were computed from the default theme's own base size, so changing `base-font-size` does not rescale headings. Set the per-level keys explicitly.
- **Keeping headings with content.** `heading-min-height-after: auto` keeps a heading with its whole first block, not just a minimum height. Check that it does not create large gaps before long code blocks.
- **SVG text fonts.** prawn-svg resolves an SVG's `font-family` list against the theme's font catalog, maps generic families (`sans-serif`, `serif`, `monospace`) to the non-embedded PDF base-14 fonts (Helvetica, Times, Courier), and only uses `svg-fallback-font-family` when nothing matches. Diagrams exported by tools such as Excalidraw (`Excalifont, …, sans-serif`) therefore render in non-embedded Helvetica, unlike the HTML edition. Fix options, to be verified by rebuilding and checking fonts: register the named font in the catalog if its license allows, register a catalog entry named after the generic family, or convert diagram text to paths.

## Cross-format integrity
Prefer PDF theme changes over changing shared `.adoc` structure. If changing document attributes, macros, diagrams, or includes, check EPUB and HTML outputs too. Keep a record of which output format each change affects.

## Font safety
Check actual font license, embedding permission, italic/bold faces, and Unicode coverage. Do not copy proprietary font files into the skill.
