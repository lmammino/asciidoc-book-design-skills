# AsciiDoc Book Design Skills

Agent skills for improving the design of technical books generated with [AsciiDoc](https://asciidoc.org/) and [Asciidoctor PDF](https://docs.asciidoctor.org/pdf-converter/latest/): editorial design, typography, theme work, and rendered-PDF quality review.

The skills follow the [Agent Skills specification](https://agentskills.io), so they work with Claude Code, Codex, Cursor, OpenCode, and the other agents supported by the [`skills` CLI](https://github.com/vercel-labs/skills).

## Skills

| Skill | What it does |
| --- | --- |
| [`asciidoc-book-design`](skills/asciidoc-book-design/SKILL.md) | Audits, explores, and refines the rendered design of an Asciidoctor PDF book (type, page grid, code blocks, light/dark editions) without touching the manuscript or breaking EPUB/HTML outputs. |

## Install

With the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
# into the current project (e.g. your book repository)
npx skills add lmammino/asciidoc-book-design-skills

# or globally, for every project
npx skills add lmammino/asciidoc-book-design-skills -g

# list available skills without installing
npx skills add lmammino/asciidoc-book-design-skills --list
```

As a Claude Code plugin:

```text
/plugin marketplace add lmammino/asciidoc-book-design-skills
/plugin install asciidoc-book-design@asciidoc-book-design-skills
```

Or manually: copy `skills/asciidoc-book-design/` into your agent's skills directory (e.g. `~/.claude/skills/` or `.agents/skills/`).

## Usage

Ask your agent from inside the book's repository, for example:

> Use the asciidoc-book-design skill to audit this project's light and dark PDFs and propose improvements. Do not modify files yet.

The skill has three modes, picked from your request:

- **audit** (default): ranked findings with page evidence, severity, and confidence. Read-only.
- **explore**: two or three differentiated editorial directions, each built as sample pages for you to choose from.
- **refine**: changes one design dimension at a time, rebuilding and re-checking both editions after each step.

### Requirements

- An existing Asciidoctor PDF build (the skill uses your build commands; it does not replace them).
- [`uv`](https://docs.astral.sh/uv/) for the bundled scripts, which declare their dependencies inline. Alternatively: `python3 -m pip install pymupdf pyyaml`.
- Bundler or RubyGems able to locate the installed `asciidoctor-pdf` gem, for the theme checker.
- An agent that can view images, for visual inspection of rendered pages.

## Status

Early version, test-driven against a real 421-page technical book with light and dark editions (Asciidoctor PDF 2.3.21). That run produced the bundled scripts and the verified list of silent theme failures in [`asciidoctor-pdf.md`](skills/asciidoc-book-design/references/asciidoctor-pdf.md). Script findings are leads for review, not verdicts.

### Bundled scripts

- `pdf_audit.py`: page geometry, non-embedded fonts, prose measure, content-type page candidates, and page or spread rendering.
- `theme_check.py`: theme keys the installed converter never reads, plus value traps such as an unparsed page size or prepress-only margins.

## Credits

Inspired by the editorial workflow described in [onepixelaway/frontend-textbooks](https://github.com/onepixelaway/frontend-textbooks). The text here is written independently; see [provenance](skills/asciidoc-book-design/references/provenance.md). No fonts or third-party assets are bundled.

## License

[MIT](LICENSE)
