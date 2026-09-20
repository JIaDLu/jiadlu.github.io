import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import ideas
from ideas_ingest import ingest
import ideas_publish


class IdeasTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'source'
        shutil.copytree(ROOT/'docs/ideas/examples',self.source)
        self.output=Path(self.tmp.name)/'public'

    def edit(self,name,change):
        path=self.source/name
        record=json.loads(path.read_text())
        change(record)
        path.write_text(json.dumps(record))

    def batch(self):
        post=json.loads((self.source/'posts/demo-question-first.json').read_text())
        post['id']='a-real-idea'
        return {'posts':[post],'tags':[],'voice':[{'post':post['id'],'anchors':[{'quote':'我想知道自己更应该练什么。','supports':[0]}]}], 'review':{'voice_preserved':True,'facts_checked':True,'privacy_checked':True}}

    def test_real_posts_do_not_depend_on_empty_state(self):
        settings,posts=ideas.load(ROOT/'content/ideas')
        ideas.build(ROOT/'content/ideas',self.output)
        manifest=json.loads((self.output/'data/index.json').read_text())
        self.assertFalse(manifest['demo'])
        self.assertEqual(len(manifest['posts']),len(posts))
        self.assertNotIn('演示空间',(self.output/'index.html').read_text().split('<main')[0])

    def test_stable_build_and_revision_tracks_body(self):
        first=ideas.build(self.source,self.output,demo=True)
        files={p.relative_to(self.output):p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(ideas.build(self.source,self.output,demo=True),first)
        self.assertEqual(files,{p.relative_to(self.output):p.read_bytes() for p in self.output.rglob('*') if p.is_file()})
        self.edit('posts/demo-question-first.json',lambda p:p['blocks'].append({'type':'paragraph','text':'新想法'}))
        self.assertNotEqual(ideas.build(self.source,self.output,demo=True),first)

    def test_unsafe_html_is_text_and_unsafe_urls_rejected(self):
        self.edit('posts/demo-question-first.json',lambda p:p['blocks'][0].update(text='<script>alert(1)</script>'))
        ideas.build(self.source,self.output,demo=True)
        rendered=(self.output/'posts/demo-question-first/index.html').read_text()
        self.assertIn('&lt;script&gt;',rendered)
        self.assertNotIn('<script>alert(1)</script>',rendered)
        self.edit('posts/demo-after-the-demo.json',lambda p:p['sources'][0].update(url='javascript:alert(1)'))
        with self.assertRaisesRegex(ValueError,'URL'):ideas.load(self.source,True)

    def test_drafts_unknown_fields_and_future_dates_rejected(self):
        self.edit('posts/demo-question-first.json',lambda p:p.update(status='draft'))
        with self.assertRaisesRegex(ValueError,'fields'):ideas.load(self.source,True)
        self.edit('posts/demo-question-first.json',lambda p:p.pop('status'))
        self.edit('posts/demo-question-first.json',lambda p:p.update(date='2999-01-01',updated='2999-01-01'))
        with self.assertRaisesRegex(ValueError,'Future'):ideas.load(self.source)

    def test_references_and_tags_must_exist(self):
        self.edit('posts/demo-question-first.json',lambda p:p['blocks'][0].update(refs=['missing']))
        with self.assertRaisesRegex(ValueError,'reference'):ideas.load(self.source,True)
        self.edit('posts/demo-question-first.json',lambda p:p['blocks'][0].pop('refs'))
        self.edit('posts/demo-question-first.json',lambda p:p['tags'].append('nonexistent'))
        with self.assertRaisesRegex(ValueError,'tag'):ideas.load(self.source,True)

    def test_short_and_long_reading_layouts_and_atom(self):
        ideas.build(self.source,self.output,'/ideas/demo',True)
        short=(self.output/'posts/demo-boring-is-good/index.html').read_text()
        long=(self.output/'posts/demo-after-the-demo/index.html').read_text()
        self.assertNotIn('class="toc"',short)
        self.assertIn('class="toc"',long)
        self.assertIn('id="source-engineering"',long)
        self.assertIn('href="#source-engineering"',long)
        self.assertIn('name="robots" content="noindex,follow"',long)
        self.assertIn('看完一个漂亮的 Agent 演示',long)
        self.assertIn('/ideas/demo/posts/demo-after-the-demo/',long)
        feed=ET.parse(self.output/'feed.xml')
        self.assertEqual(len(feed.findall('{http://www.w3.org/2005/Atom}entry')),4)

    def test_feed_pagination_and_stale_cleanup(self):
        original=json.loads((self.source/'posts/demo-question-first.json').read_text())
        for i in range(26):
            p=copy.deepcopy(original);p['id']=f'test-{i}'
            (self.source/'posts'/f'{p["id"]}.json').write_text(json.dumps(p))
        ideas.build(self.source,self.output,demo=True)
        self.assertTrue((self.output/'page/3/index.html').exists())
        self.assertEqual((self.output/'index.html').read_text().count('data-post='),12)
        for path in (self.source/'posts').glob('test-*.json'):path.unlink()
        ideas.build(self.source,self.output,demo=True)
        self.assertFalse((self.output/'page/3/index.html').exists())
        self.assertFalse((self.output/'posts/test-0/index.html').exists())

    def test_ingest_is_idempotent_and_voice_is_private(self):
        batch=self.batch()
        original={p:p.read_bytes() for p in self.source.rglob('*.json')}
        self.assertTrue(ingest(self.source,batch))
        self.assertEqual(original,{p:p.read_bytes() for p in self.source.rglob('*.json')})
        self.assertTrue(ingest(self.source,batch,True))
        self.assertEqual(ingest(self.source,batch,True),[])
        ideas.build(self.source,self.output,demo=True)
        for path in [*(self.source.rglob('*.json')),*(self.output.rglob('*'))]:
            if path.is_file():self.assertNotIn('我想知道自己更应该练什么。',path.read_text())

    def test_missing_voice_or_review_blocks_apply(self):
        batch=self.batch();batch['voice']=[]
        with self.assertRaisesRegex(ValueError,'AI-only'):ingest(self.source,batch,True)
        self.assertFalse((self.source/'posts/a-real-idea.json').exists())
        batch=self.batch();batch['review']['voice_preserved']=False
        with self.assertRaisesRegex(ValueError,'review'):ingest(self.source,batch,True)

    def test_published_views_need_append_only_updates(self):
        batch=self.batch();ingest(self.source,batch,True)
        batch['posts'][0]['blocks'][0]['text']='想法变了'
        with self.assertRaisesRegex(ValueError,'update note'):ingest(self.source,batch,True)
        batch['posts'][0]['updates']=[{'date':'2026-09-16','text':'补充一个不同角度。'}]
        batch['posts'][0]['updated']='2026-09-16'
        ingest(self.source,batch,True)
        batch['posts'][0]['updates']=[]
        with self.assertRaisesRegex(ValueError,'history'):ingest(self.source,batch,True)

    def test_invalid_candidate_never_changes_existing_source(self):
        original={p:p.read_bytes() for p in self.source.rglob('*.json')}
        batch=self.batch();batch['posts'][0]['tags']=['missing']
        with self.assertRaises(ValueError):ingest(self.source,batch,True)
        self.assertEqual(original,{p:p.read_bytes() for p in self.source.rglob('*.json')})

    def test_publish_scope_and_unrelated_history(self):
        self.assertTrue(ideas_publish.allowed('content/ideas/posts/my-thought.json'))
        self.assertTrue(ideas_publish.allowed('ideas/page/2/index.html'))
        for p in ['content/knowledge/days/2026-09-20.json','.ideas-local/draft.json','ideas/assets/app.js','ideas/demo/index.html','content/ideas/posts/private.txt']:
            self.assertFalse(ideas_publish.allowed(p))
        with patch.object(ideas_publish,'git',return_value='index.html'):
            with self.assertRaisesRegex(ValueError,'unrelated'):ideas_publish.check_history(['abc'])

if __name__=='__main__':unittest.main()
