# Mermaid Diagram Workflow (Meta Example)

This repo accompanies the blog post [**How I Organized My Mermaid Life**](https://barbhs.com/blog/taming-mermaid-diagrams/).

It contains:

- `blog/` – drafts and outlines for the post and its follow-ups
- `diagrams/` – the example Mermaid diagrams used in the post, each with YAML front matter metadata, plus their rendered SVGs
- `diagram_index/index.yaml` – a small cross-project diagram index
- `diagram_hub/` – early code for scanning diagrams and reading their metadata
- `streamlit_app/app.py` – a small Streamlit app to explore the index and generate new diagrams
- `scripts/render_diagrams.sh` – script to render all `.mmd` → `.svg`

## Quickstart

```bash
# 1. Install the Mermaid CLI (once)
npm install

# 2. Render the example diagrams
./scripts/render_diagrams.sh

# 3. Install Python deps
pip install streamlit pyyaml python-frontmatter

# 4. Run the Streamlit app
streamlit run streamlit_app/app.py
```

## Metadata lives in front matter

Each `.mmd` file starts with a YAML block between `---` lines, followed by the diagram:

```text
---
id: per_project_workflow_v1
title: Per-Project Diagram Workflow
tags: [workflow, mermaid, documentation]
---
flowchart LR
    Edit[Edit .mmd file] --> Render[Run render_diagrams.sh]
```

Mermaid ignores keys it doesn't know, so the file still renders. One exception: Mermaid reads `title` itself and draws it above the diagram. The `---` lines matter: without them, Mermaid treats the metadata as diagram code and fails with "No diagram type detected."
