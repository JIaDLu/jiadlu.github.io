"""Integration checks for the site's shared shell and homepage navigation."""
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ideas
import knowledge


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.references = []
        self.ids = []
        self.header_links = []
        self.in_header = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'header' and 'site-header' in attrs.get('class', '').split():
            self.in_header = True
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('src', 'href'):
            if key in attrs:
                self.references.append(attrs[key])
        if self.in_header and tag == 'a':
            self.header_links.append(attrs.get('href'))

    def handle_endtag(self, tag):
        if tag == 'header':
            self.in_header = False


class SiteTests(unittest.TestCase):
    def test_homepage_links_assets_and_fragments_resolve(self):
        page = Page((ROOT / 'index.html').read_text())
        self.assertEqual(len(page.ids), len(set(page.ids)), 'Duplicate anchor IDs')
        for ref in page.references:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            with self.subTest(ref=ref):
                target = ROOT / unquote(url.path).lstrip('/') if url.path else ROOT / 'index.html'
                if target.is_dir():
                    target /= 'index.html'
                self.assertTrue(target.is_file(), f'Missing local target: {ref}')
                if url.fragment:
                    self.assertIn(unquote(url.fragment), Page(target.read_text()).ids)
        self.assertFalse((ROOT / 'undergraduate/index.html').exists())

    def test_shared_navigation_and_styles_reach_all_page_types(self):
        paths = [ROOT / 'index.html', *sorted((ROOT / 'knowledge').rglob('index.html')), *sorted((ROOT / 'ideas').rglob('index.html'))]
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                page = Page(path.read_text())
                self.assertEqual(set(page.header_links), {'/', '/knowledge/', '/ideas/'})
                self.assertTrue(any(urlsplit(ref).path == '/assets/css/site.css' for ref in page.references))
                self.assertFalse(any(urlsplit(ref).path.startswith('/undergraduate/') for ref in page.references))

    def test_shared_css_changes_invalidate_both_product_revisions(self):
        # Work entirely in a temporary root; shared-style edits must invalidate
        # both the page's CSS URL and the deployment revision, without data edits.
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ('knowledge/assets', 'ideas/assets'):
                shutil.copytree(ROOT / relative, root / relative)
            (root / 'assets/css').mkdir(parents=True)
            shared = root / 'assets/css/site.css'
            shared.write_bytes((ROOT / 'assets/css/site.css').read_bytes())
            for module, product in ((knowledge, 'knowledge'), (ideas, 'ideas')):
                with self.subTest(product=product), patch.object(module, 'ROOT', root):
                    output = root / f'{product}-public'
                    source = ROOT / f'docs/{product}/examples'
                    before = module.build(source, output, demo=True)
                    page_before = (output / 'index.html').read_text()
                    shared.write_text(shared.read_text() + '\n/* Changed shared design */\n')
                    after = module.build(source, output, demo=True)
                    page_after = (output / 'index.html').read_text()
                    self.assertNotEqual(before, after)
                    styles_before = [ref for ref in Page(page_before).references if '/assets/css/site.css?' in ref]
                    styles_after = [ref for ref in Page(page_after).references if '/assets/css/site.css?' in ref]
                    self.assertNotEqual(styles_before, styles_after)


if __name__ == '__main__':
    unittest.main()
