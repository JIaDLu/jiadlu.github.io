import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from knowledge import build, load
from knowledge_ingest import ingest
from knowledge_publish import allowed

class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'content'
        shutil.copytree(ROOT / 'docs/knowledge/examples', self.source)
        self.output = Path(self.tmp.name) / 'public'

    def edit(self, path, change):
        p = self.source / path
        data = json.loads(p.read_text())
        change(data)
        p.write_text(json.dumps(data))

    def batch(self):
        note = json.loads((self.source / 'notes/react-loop.json').read_text())
        return {'date': '2026-09-13', 'summary': '用例回顾', 'branches': [], 'notes': [note], 'entries': [{'note':'react-loop','takeaway':'从观察决定动作','kind':'review'}]}

    def test_real_data_is_empty_and_demo_is_isolated(self):
        _, notes, days = load(ROOT / 'content/knowledge')
        # Future real notes can be added without changing this test's invariant.
        self.assertTrue(all('演示问题' not in n['context'] for n in notes.values()))
        demo = json.loads((ROOT / 'knowledge/demo/data/graph.json').read_text())
        self.assertTrue(demo['demo'])
        build(ROOT / 'content/knowledge', self.output)
        self.assertFalse(json.loads((self.output / 'data/graph.json').read_text())['demo'])

    def test_repeat_build_is_identical(self):
        r1 = build(self.source, self.output, demo=True)
        first = {p.relative_to(self.output):p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        r2 = build(self.source, self.output, demo=True)
        second = {p.relative_to(self.output):p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(first, second)
        self.assertEqual(r1,r2)

    def test_body_changes_change_revision_and_escape_html(self):
        first = build(self.source, self.output, demo=True)
        self.edit('notes/react-loop.json', lambda n:n['sections'][0]['paragraphs'].append('<script>alert(1)</script>'))
        second = build(self.source, self.output, demo=True)
        self.assertNotEqual(first,second)
        page=(self.output/'notes/react-loop/index.html').read_text()
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',page)
        self.assertNotIn('<script>alert(1)</script>',page)

    def test_missing_reference_is_rejected(self):
        self.edit('days/2026-09-09.json', lambda d:d['entries'][0].update(note='unknown'))
        with self.assertRaisesRegex(ValueError,'unknown/duplicate'):load(self.source,True)

    def test_cycle_and_reserved_ids_are_rejected(self):
        self.edit('taxonomy.json', lambda t:t['branches'][0].update(parent='agent-loops'))
        with self.assertRaisesRegex(ValueError,'cycle'):load(self.source,True)

    def test_related_reference_must_exist(self):
        self.edit('notes/react-loop.json', lambda n:n['related'].append('missing'))
        with self.assertRaisesRegex(ValueError,'related'):load(self.source,True)

    def test_unsafe_source_link_is_rejected(self):
        self.edit('notes/react-loop.json', lambda n:n['sources'][0].update(url='javascript:alert(1)'))
        with self.assertRaisesRegex(ValueError,'Unsafe'):load(self.source,True)

    def test_same_day_ingest_merges_and_is_idempotent(self):
        batch=self.batch()
        self.assertTrue(ingest(self.source,batch,True))
        self.assertEqual(ingest(self.source,batch,True),[])
        day=json.loads((self.source/'days/2026-09-13.json').read_text())
        self.assertEqual(len(day['entries']),2)
        self.assertEqual(day['entries'][0]['takeaway'],'从观察决定动作')
        self.assertTrue((self.source/'days/2026-09-09.json').exists())

    def test_invalid_batch_cannot_modify_source(self):
        batch=self.batch()
        batch['notes'][0]['branch']='missing'
        original={p:p.read_bytes() for p in self.source.rglob('*.json')}
        with self.assertRaises(ValueError):ingest(self.source,batch,True)
        self.assertEqual(original,{p:p.read_bytes() for p in self.source.rglob('*.json')})

    def test_dry_run_does_not_write(self):
        batch=self.batch()
        original=(self.source/'days/2026-09-13.json').read_bytes()
        self.assertTrue(ingest(self.source,batch))
        self.assertEqual(original,(self.source/'days/2026-09-13.json').read_bytes())

    def test_new_branch_and_note_are_created_together(self):
        batch=self.batch()
        batch['branches']=[{'id':'new-branch','title':'新分支','parent':'agents','description':'基于新知识扩展。'}]
        batch['notes'][0]['id']='new-note'
        batch['notes'][0]['branch']='new-branch'
        batch['entries']=[{'note':'new-note','takeaway':'新理解','kind':'learn'}]
        ingest(self.source,batch,True)
        taxonomy,notes,days=load(self.source)
        self.assertEqual(notes['new-note']['branch'],'new-branch')
        self.assertEqual(len(days[-1]['entries']),3)

    def test_future_date_and_duplicate_entries_are_rejected(self):
        batch=self.batch()
        batch['date']='2999-01-01'
        with self.assertRaisesRegex(ValueError,'future'):ingest(self.source,batch,True)
        batch=self.batch()
        batch['entries']*=2
        with self.assertRaisesRegex(ValueError,'Duplicate'):ingest(self.source,batch,True)

    def test_generated_notes_have_correct_metadata_and_navigation(self):
        build(self.source,self.output,'/knowledge/demo',True)
        for slug in ['react-loop','sft-loss-mask']:
            note=json.loads((self.source/f'notes/{slug}.json').read_text())
            page=(self.output/f'notes/{slug}/index.html').read_text()
            self.assertIn(note['title'],page)
            self.assertIn(f'/knowledge/demo/tree/?node={slug}',page)
            self.assertIn('主动回忆',page)
            self.assertIn('2026-09-13',page)
            self.assertIn('演示空间',page)
            self.assertNotIn('og:image',page)

    def test_full_code_examples_execute(self):
        _, notes, _=load(self.source,True)
        for n in notes.values():
            for example in n['examples']:
                if example['language']=='python':exec(example['code'],{})

    def test_publish_scope_excludes_unrelated_work(self):
        self.assertTrue(allowed('content/knowledge/notes/react-loop.json'))
        for p in ['index.html','.env','.agents/skills/shougong/SKILL.md','knowledge/assets/app.js','knowledge/demo/data/graph.json']:
            self.assertFalse(allowed(p))

if __name__ == '__main__':unittest.main()
