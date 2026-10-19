#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""Check Asciidoctor PDF theme files against the installed converter's source.

Flags keys the converter never reads (silently ignored) and a few verified value traps.
Run from the book project so the gem resolved by Bundler is the one that builds the book,
or pass --gem-dir. Results are leads: confirm with a rebuild before relying on them.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

SKIP = ('extends', 'font_catalog', 'font_fallbacks')
NAMED_SIZE = re.compile(r'^[a-z]+\d*$', re.I)


def find_gem(gem_dir):
    if gem_dir:
        if not (Path(gem_dir) / 'lib' / 'asciidoctor' / 'pdf' / 'converter.rb').is_file():
            sys.exit(f'{gem_dir} does not look like an asciidoctor-pdf gem directory')
        return Path(gem_dir)
    for cmd in (['bundle', 'info', '--path', 'asciidoctor-pdf'], ['gem', 'contents', 'asciidoctor-pdf']):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            continue
        for line in out:
            path = Path(line.strip())
            if (path / 'lib' / 'asciidoctor' / 'pdf' / 'converter.rb').is_file():
                return path
            if path.name == 'converter.rb' and path.parent.name == 'pdf':
                return path.parents[3]
    sys.exit('Could not locate the asciidoctor-pdf gem; run from the book project or pass --gem-dir')


def flatten(data, path=(), out=None):
    out = {} if out is None else out
    for key, value in (data or {}).items():
        segments = path + (str(key),)
        flat = '_'.join(s.replace('-', '_').lower() for s in segments)
        if flat.startswith(SKIP):
            continue
        if isinstance(value, dict):
            flatten(value, segments, out)
        else:
            out[flat] = ('.'.join(segments), value)
    return out


class Converter:
    def __init__(self, root):
        self.root = root
        self.version = re.sub(r'^asciidoctor-pdf-', '', root.name)
        self.src = '\n'.join(p.read_text(encoding='utf-8') for p in sorted((root / 'lib').rglob('*.rb')))
        self.known = {}
        for theme in sorted((root / 'data' / 'themes').glob('*.yml')):
            self.known.update(flatten(yaml.safe_load(theme.read_text(encoding='utf-8'))))
        self.default = flatten(yaml.safe_load((root / 'data' / 'themes' / 'default-theme.yml').read_text(encoding='utf-8')))
        # suffixes read for any category by generic helpers such as theme_font and theme_fill_and_stroke_block
        self.generic = set(re.findall(r'%\(#\{(?:category|hlevel_category)\}_([a-z0-9_]+)\)', self.src))
        self.categories = set(re.findall(r':([a-z][a-z0-9_]*)\b', self.src)) | {k.rsplit('_', 1)[0] for k in self.known}
        # composed categories such as quote_cite or image_caption, built as %(#{category}_cite)
        self.compound = set(re.findall(r'theme_font %\(#\{\w+\}_([a-z0-9_]+)\)', self.src)) | set(re.findall(r'%\(#\{category\}_([a-z0-9_]+)\) : ', self.src))
        self.compound_suffixes = self.generic | set(re.findall(r'%\(#\{category_\w+\}_([a-z0-9_]+)\)', self.src))
        self.patterns = [re.compile('^%s[a-z0-9_]+%s$' % (pre, suf))
                         for pre, suf in re.findall(r'%\(([a-z][a-z0-9_]*_)#\{[^}]+\}([a-z0-9_]*)\)', self.src)]
        self.icon_keys = set(re.findall(r'icon_data\[:([a-z_]+)\]', self.src)) | set(re.findall(r'admonition_icon_#\{\w+\}\)\] \|\| \{\}\)\[:([a-z_]+)\]', self.src))

    def status(self, key):
        if key.startswith('admonition_icon_'):
            sub = key[len('admonition_icon_'):].split('_', 1)
            return 'ok' if len(sub) == 2 and sub[1] in self.icon_keys else 'unknown'
        if key in self.known or re.search(r'\b%s\b' % re.escape(key), self.src):
            return 'ok'
        if any(key.endswith('_' + s) and key[:-len(s) - 1] in self.categories for s in self.generic):
            return 'ok'
        for c in self.compound:
            prefix, _, rest = key.partition(f'_{c}_')
            if rest and prefix in self.categories and rest in self.compound_suffixes:
                return 'ok'
        if any(p.match(key) for p in self.patterns):
            return 'dynamic'
        return 'unknown'


def value_rules(keys, conv):
    found = []
    size = keys.get('page_size')
    if size and isinstance(size[1], str) and not NAMED_SIZE.match(size[1].strip()):
        found.append(('error', size[0], f'{size[1]!r} is not a named size; the theme only parses arrays like [8.5in, 11in] or names like Letter, so the converter falls back to A4'))
    for side in ('page_margin_inner', 'page_margin_outer'):
        if side in keys:
            found.append(('warn', keys[side][0], 'only applied when the media attribute is prepress (e.g. -a media=prepress); ignored otherwise'))
    for key, (path, _) in keys.items():
        prop = key[len('heading_'):] if key.startswith('heading_') and not re.match(r'heading_h\d_', key) else None
        shadowing = [f'heading_h{n}_{prop}' for n in range(1, 7) if prop and f'heading_h{n}_{prop}' in conv.default and f'heading_h{n}_{prop}' not in keys]
        if shadowing:
            found.append(('warn', path, f'overridden by per-level keys inherited from the default theme ({", ".join(shadowing)}); set heading-h<n>-{prop.replace("_", "-")} instead'))
    if 'base_font_size' in keys and not any(f'heading_h{n}_font_size' in keys for n in range(1, 7)):
        found.append(('info', keys['base_font_size'][0], 'per-level heading sizes inherited from the default theme were computed from its own base font size, not this one'))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('themes', nargs='+', help='Theme YAML files (*-theme.yml)')
    parser.add_argument('--gem-dir', help='asciidoctor-pdf gem directory (default: resolve via bundle, then gem)')
    parser.add_argument('--json', dest='json_out', help='Also write the report as JSON')
    args = parser.parse_args()
    conv = Converter(find_gem(args.gem_dir))
    report = {'asciidoctor_pdf': conv.version, 'gem_dir': str(conv.root), 'themes': []}
    print(f'asciidoctor-pdf {conv.version} ({conv.root})')
    for theme in args.themes:
        keys = flatten(yaml.safe_load(Path(theme).read_text(encoding='utf-8')))
        checks = [(conv.status(k), path) for k, (path, _) in keys.items()]
        result = {
            'theme': theme, 'keys_checked': len(keys),
            'unknown': [p for s, p in checks if s == 'unknown'],
            'dynamic': [p for s, p in checks if s == 'dynamic'],
            'findings': [{'level': lvl, 'key': path, 'message': msg} for lvl, path, msg in value_rules(keys, conv)],
        }
        report['themes'].append(result)
        print(f'\n## {theme} ({len(keys)} keys)')
        for path in result['unknown']:
            print(f'  unknown  {path}: not read by this converter version; likely ignored')
        for path in result['dynamic']:
            print(f'  dynamic  {path}: matches an interpolated lookup; confirm in the docs or a rebuild')
        for f in result['findings']:
            print(f"  {f['level']:<8} {f['key']}: {f['message']}")
        if not (result['unknown'] or result['dynamic'] or result['findings']):
            print('  no issues found')
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
