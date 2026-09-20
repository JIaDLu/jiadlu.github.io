# Repository guidance

This is Jiadong's static GitHub Pages site. The live branch is `furbish`.
Knowledge is a separate visual and data system; do not inherit the old homepage theme.

## Shared site design

Read `docs/site/README.md` for homepage content sources and design decisions.
`assets/css/site.css` owns shared tokens, page width and global navigation;
product layouts stay in their own CSS. After changing shared CSS, build and
verify both Knowledge and Ideas, and bump the homepage stylesheet query version.
The Undergraduate standalone page has been removed; keep its selected research
and background on the homepage without reintroducing the route or certificates.

## Learning workflow

When the user says **收工** to end a learning or discussion session, read and execute
[the project skill](.agents/skills/shougong/SKILL.md). The same skill can be invoked
as `$shougong`. This instruction routes the literal Chinese command even in a
session whose skill catalog was loaded before the skill was created. Classify each
part of the discussion: learned concepts, mechanisms, and examples go to Knowledge;
the user’s comments, judgments, questions, rants, and brainstorms go to Ideas.
If both are present, organize and publish both separately. Read the Ideas editor
skill for that stream, preserving the user’s voice. Explicit scope or draft-only
requests override the default; do not invent content for an empty stream.

Learning sources live in `content/knowledge/`; generated public views live in
`knowledge/`. Read `docs/knowledge/README.md` and `docs/knowledge/schema.md` before
changing the schema or archiving learning. Do not manually maintain duplicate
knowledge in the generated views. Demonstrations belong only in
`docs/knowledge/examples/` and `knowledge/demo/`, never real learning history.

When a substantial learning discussion has reached a conclusion, keep a concise
checkpoint for **this session only** under `.knowledge-local/` when useful for
later context recovery: concepts covered, the actual examples, corrections,
open questions, and learning date. This folder is ignored by Git and is not a
public data source. A checkpoint supplements the conversation; it does not
justify claiming complete recall when context is missing.

## Verification

Run `python3 scripts/knowledge.py validate`, `python3 scripts/knowledge.py build`,
`python3 -m unittest discover -s tests -v`, and
`node --check knowledge/assets/app.js` for Knowledge changes. Commit generated
pages with their source so branch-based GitHub Pages works without extra setup.
The existing Pages deployment remains the publisher; the Knowledge integrity
workflow checks consistency and does not change repository Pages settings.

## Ideas / personal expression

Ideas records **What I think**, separately from Knowledge's **What I learned**.
When the user asks to follow AI developments, draft current ideas, says **记一笔**,
or invokes `$ideas-editor`, read `.agents/skills/ideas-editor/SKILL.md`.
“记一笔” means edit and publish; “先整理成草稿” stays local; following news alone
never authorizes publication. “收工” authorizes automatic routing and publication
of the eligible Knowledge and Ideas from this session via the unified skill.

Read `docs/ideas/README.md`, `docs/ideas/schema.md`, and the editorial guidance
before archiving Ideas. Published sources live in `content/ideas/`; public views
in `ideas/` are generated. `.ideas-local/` holds private drafts, exact user voice
anchors, and current-session checkpoints. Never publish or commit that folder.
Do not attribute AI-originated opinions or invented experiences to Jiadong.
Keep demo content under `docs/ideas/examples/` and `ideas/demo/` only.

For Ideas changes run `python3 scripts/ideas.py validate`,
`python3 scripts/ideas.py build`, `python3 -m unittest discover -s tests -v`,
`node --check ideas/assets/app.js`, and `python3 scripts/ideas_dom_check.py`.
Commit generated pages with the source. Use the dedicated publisher for future
content updates so unrelated workspace changes are not staged or pushed.
