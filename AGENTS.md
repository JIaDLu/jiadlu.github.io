# Repository guidance

This is Jiadong's static GitHub Pages site. The live branch is `furbish`.
Knowledge is a separate visual and data system; do not inherit the old homepage theme.

## Learning workflow

When the user says **收工** to end a learning session, read and execute
[the project skill](.agents/skills/shougong/SKILL.md). The same skill can be invoked
as `$shougong`. This instruction routes the literal Chinese command even in a
session whose skill catalog was loaded before the skill was created.

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
