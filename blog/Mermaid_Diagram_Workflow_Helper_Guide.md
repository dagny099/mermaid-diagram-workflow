# Mermaid Diagram Workflow Helper — User Guide

This Streamlit app is a companion to the blog post **“Taming Mermaid Diagrams Across Projects.”**
It reinforces a simple, scalable way to store, find, and reuse Mermaid diagrams.

The repo is a meta‑example of the workflow:

```
mermaid-diagram-workflow/
  diagrams/                  # .mmd sources + rendered .svg previews
  diagram_index/index.yaml   # cross-project index
  scripts/render_diagrams.sh # render all .mmd -> .svg
  streamlit_app/app.py       # this app
  blog/mermaid-diagram-workflow.md
```

---

## Quickstart

1. **Install dependencies**

```bash
pip install streamlit pyyaml
```

2. **Render example diagrams**

```bash
./scripts/render_diagrams.sh
```

3. **Run the app**

```bash
streamlit run streamlit_app/app.py
```

---

## What the app helps you do

- Remember the per‑project Mermaid workflow (Checklist tab)
- Browse diagrams by project, status, visibility, and tags (Diagram Explorer tab)
- View *diagram sequences* in teaching / storytelling order (Sequences tab)
- Recall which diagram types to create and how to name them (Diagram Types & Templates tab)
- **Create new diagrams correctly** using a wizard (New Diagram tab)

---

## Tabs

### 1) Overview
A fast “health check” of your library:
- total diagrams in index
- number of projects represented
- number of sequence groups
- short reminder of what the app is doing behind the scenes

If this tab shows **0 diagrams**, you probably haven’t added entries to
`diagram_index/index.yaml` yet.

---

### 2) Checklist
A narrative + concrete reminder of the workflow:

1. Put *every* Mermaid diagram in `/diagrams/`
2. Name files with a stable convention
3. Add YAML frontmatter metadata
4. Render SVGs in batch with `render_diagrams.sh`
5. Index important diagrams in `diagram_index/index.yaml`
6. Use sequences for teaching / storytelling

The tab includes:
- a ready‑to‑copy **frontmatter template**
- a ready‑to‑copy **render script**

---

### 3) Diagram Explorer
This is your searchable library view.

**Filters**
- **Project**: one repo, one domain, or “any”
- **Visibility**: public / internal / private
- **Status**: draft / stable / deprecated
- **Search box**: matches against title, id, or tags

**Each diagram card shows**
- title + id
- project + file path
- status and visibility badges
- tags as chips
- description & last updated
- SVG preview (if found)

**Usage snippets**
At the bottom of each card you get copy‑paste snippets for embedding diagrams in docs:

- Markdown image embed
- Markdown link to the source `.mmd`
- A Jekyll‑friendly include snippet

If an SVG preview is missing, the card will suggest running:

```bash
./scripts/render_diagrams.sh
```

---

### 4) Sequences
Sequences let you chain diagrams into a narrative arc (great for blog posts, talks, onboarding).

To use them, put this in the diagram’s YAML frontmatter:

```yaml
sequence:
  group: "my-story-arc"
  order: 1
```

**In this tab**
- Choose a sequence group
- Diagrams display in order
- Each step shows metadata + preview

---

### 5) Diagram Types & Templates
A compact table that answers:

> “What kinds of Mermaid diagrams should I be creating, and what are they good for?”

You’ll also see:
- the recommended filename pattern
- concrete examples to copy

---

### 6) New Diagram (Wizard)
This is the fastest way to create diagrams correctly.

**Steps**
1. Choose a *project* (or type a new one)
2. Pick a *diagram type* (data flow, workflow, decision tree, architecture, etc.)
3. Enter a short *topic*
4. Set *version*, *visibility*, and *status*
5. Optionally add:
   - sequence group + order
   - description
6. Click **Create diagram file**

**What happens**
- The app writes a new `.mmd` file under `/diagrams/`
- It includes YAML frontmatter with your selections
- It inserts a Mermaid starter skeleton based on the selected type
- It displays the full path to the created file

After creation, open the file in your editor, fill in the real diagram, then batch‑render SVGs.

---

## Customizing dropdown options

At the top of `streamlit_app/app.py` you’ll find configuration blocks such as:

- `DIAGRAM_TYPE_OPTIONS`
- `VISIBILITY_OPTIONS`
- `STATUS_OPTIONS`
- `DEFAULT_VERSION`

Edit those lists/dicts to reflect your personal diagram vocabulary.

You can also add or tweak Mermaid skeleton templates in:

- `DIAGRAM_SKELETONS`

---

## Troubleshooting

**No diagrams show up**
- Check that `diagram_index/index.yaml` exists
- Ensure it has a top‑level `diagrams:` list
- Confirm each entry includes at least: `id`, `title`, `project`, `path`

**SVG previews missing**
- Run:

```bash
./scripts/render_diagrams.sh
```

**Weird filter behavior**
- Make sure `visibility` and `status` values in index.yaml match the allowed options.
- If you add new custom options, update the configuration at the top of `app.py`.

---

## Next milestones (roadmap)
This app is intentionally lightweight. Potential future upgrades:

1. **Rescan & Sync Index button**
2. **Gentle lint warnings** for filename/metadata drift
3. **Contextual sequence views** for blogs/talks
4. **Cross‑repo gallery generation**

---

If you extend the app, keep the spirit:
**low friction, high clarity, and diagrams as first‑class visual code.**
