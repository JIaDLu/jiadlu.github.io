# Personal site

Homepage content and design were revised on 20 September 2026. The site remains
static GitHub Pages on `furbish`; no framework, external fonts, or browser runtime
is needed for the homepage.

## Content and maintenance

The primary factual source is the author's English `resume_ng_en/main.tex`,
updated 17 September 2026. The compiled `main.pdf` is copied unchanged to
`assets/cv/Resume_Lujiadong.pdf`, preserving the existing public CV URL.

The homepage uses a personal introduction, links to the two notebooks, selected
work grouped by employer, two selected publications, and education. Role names,
dates, degrees, authorship and reported outcomes follow the resume. Keep internal
evaluation names and their meaning next to results: Excellent-Bench measures
alignment with expert sales behaviour; the paediatric failure rate uses a rolling
set of production conversations. Do not relabel these as general benchmarks or
clinical outcomes. Do not infer a graduate research appointment from enrolment.

Undergraduate background is folded into education and selected research. Its
standalone HTML and entry link have been removed, with no replacement page or
redirect at `/undergraduate/`. The two existing paper-framework images are
retained as small, uncropped thumbnails linked to their full-size files. Awards,
software copyrights and patents are summarised in prose; certificate and
transcript images are not displayed. Historical assets remain in the repository.
Citation counts and journal rankings are omitted to avoid stale badges.

`index.html` is the editable homepage, not generated from the CV. Update it when
professional facts change. Knowledge and Ideas retain their own source data,
builders and daily publishing workflows; the homepage links to them rather than
keeping duplicate excerpts or activity totals.

## Shared design

- `assets/css/site.css`: single source for base colour/font tokens, site width,
  global navigation, secondary navigation, footer, and focus treatment.
- `assets/css/home.css`: homepage typography and responsive content layouts.
- Product CSS: each system's reading, feed, calendar and tree layouts.

The shared stylesheet loads **after** product CSS, so its shell and token values
win over historical product defaults. The shared maximum width is 1120px, with
32px desktop and 20px mobile minimum gutters. System sans-serif text, restrained
serif display titles, thin rules and a muted olive accent connect the three
surfaces. Product-specific layouts are deliberately independent.

All global headers expose Home / Knowledge / Ideas. The active product is marked
with `aria-current`; local navigation separately exposes the learning calendar /
tree or Ideas feed / archive, including in demos. Header markup lives in
`index.html` and the two Python shell templates. Navigation changes must keep all
three in sync; the integration test verifies the generated page types.

Both product builders include shared CSS in their cache key and deployment
revision. After changing shared CSS, run both builds and commit their generated
views. Daily content publishers stop if shared CSS has uncommitted changes, so
content cannot be published against an unpublished design. Homepage stylesheet URLs use a version query: bump both versions in
`index.html` when changing homepage/shared CSS. Updating the downloadable CV also
requires a new query version in its homepage link.

Design references reviewed for information organisation:

- [Andrej Karpathy](https://karpathy.ai/): compact introduction, chronological
  experience and concrete work, with simple text-and-image presentation.
- [Hamel Husain](https://hamel.dev/): direct professional introduction and clear
  routes into ongoing writing.
- [Simon Willison](https://simonwillison.net/about/): an explicit personal bio
  alongside a separately maintained writing space.

These informed the structure; the homepage copy and design are original to this
site. Full-screen heroes, decorative blobs, reveal animations, visit counters,
contribution widgets and certificate galleries were removed from the homepage.

## Verification

```sh
python3 scripts/knowledge.py validate
python3 scripts/knowledge.py build
python3 scripts/ideas.py validate
python3 scripts/ideas.py build
python3 -m unittest discover -s tests -v
node --check knowledge/assets/app.js
node --check ideas/assets/app.js
python3 scripts/knowledge_dom_check.py
python3 scripts/ideas_dom_check.py
```

The site integration checks validate homepage local links and anchors, shared
navigation, removed undergraduate routing, and cache invalidation after shared
CSS changes. DOM checks cover the existing product interactions. Also inspect
phone and desktop layouts in a connected browser when available; DOM tests do
not validate rendered geometry.
