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

## Cross-format integrity
Prefer PDF theme changes over changing shared `.adoc` structure. If changing document attributes, macros, diagrams, or includes, check EPUB and HTML outputs too. Keep a record of which output format each change affects.

## Font safety
Check actual font license, embedding permission, italic/bold faces, and Unicode coverage. Do not copy proprietary font files into the skill.
