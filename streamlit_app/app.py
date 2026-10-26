"""
Streamlit UI for the Mermaid Diagram Workflow helper.

This app is a companion to the blog post “Taming Mermaid Diagrams Across Projects.”
It reinforces a simple, scalable way to store, find, and reuse Mermaid diagrams.

FEATURES (v1.1):
- Checklist / reminders aligned to the blog post
- Diagram Explorer with filters and SVG previews
- Usage snippets for embedding diagrams in docs
- Diagram Sequences view (teaching/storytelling arcs)
- Diagram Types & Naming cheat sheet
- NEW: "New Diagram" Wizard that generates a correct .mmd file with metadata + skeleton

Best-practice alignment:
- Lazy initialization of session state at top of app
- Unique widget keys per tab to avoid bleed/conflicts
- No st.rerun() loops; state updates happen in one pass
- Progressive disclosure (filters in expander; previews inside expanders)

Dependencies:
    pip install streamlit pyyaml

Expected repo layout (relative to this file):

    mermaid-diagram-workflow/
        diagrams/
            *.mmd
            *.svg
        diagram_index/
            index.yaml
        scripts/
            render_diagrams.sh
        streamlit_app/
            app.py  <-- this file
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import date

import streamlit as st
import yaml


# -------------------------------------------------------------------
# CONFIGURATION (easy-to-edit dropdown sources)
# -------------------------------------------------------------------

# You can evolve these lists over time (or load from a config file).
VISIBILITY_OPTIONS = ["public", "internal", "private"]
STATUS_OPTIONS = ["draft", "stable", "deprecated"]

# Diagram types shown in the wizard + types tab.
# Each tuple: (label_shown_to_user, filename_fragment, short_description)
DIAGRAM_TYPE_OPTIONS: List[Tuple[str, str, str]] = [
    ("Data flows", "data_flow", "How data moves through systems, ETL, APIs"),
    ("Technical workflows", "workflow", "Step-by-step processes (ingest/train/deploy/eval)"),
    ("Decision trees / routing", "decision_tree", "If/else logic, classification, branching"),
    ("Architecture diagrams", "architecture", "High-level components/services and links"),
    ("Sequence diagrams", "sequence", "Requests/responses over time"),
    ("State diagrams", "state_machine", "States and transitions"),
    ("ER / schema diagrams", "schema", "Entities/tables and relationships"),
    ("Knowledge graph / concept maps", "kg_view", "Concepts/entities across domains"),
    ("Timelines / chronologies", "timeline", "Time-ordered events, releases, arcs"),
    ("UI flows / user journeys", "ui_flow", "Screens, actions, navigation paths"),
    ("ML pipelines & evaluation", "ml_eval_flow", "Training/eval loops, metrics, comparisons"),
]

DEFAULT_VERSION = "0.1"  # Wizard default for new diagrams

# Mermaid skeletons used by the wizard.
DIAGRAM_SKELETONS: Dict[str, str] = {
    "data_flow": """flowchart LR
    A[Source] --> B[Transform]
    B --> C[Destination]
""",
    "workflow": """flowchart TB
    Start((Start)) --> Step1[Step 1]
    Step1 --> Step2[Step 2]
    Step2 --> End((End))
""",
    "decision_tree": """flowchart TB
    Start((Start)) --> Q{Decision?}
    Q -->|Yes| A[Path A]
    Q -->|No| B[Path B]
""",
    "architecture": """flowchart LR
    SubsystemA[Service A] --> SubsystemB[Service B]
    SubsystemB --> Storage[(Data Store)]
""",
    "sequence": """sequenceDiagram
    participant U as User
    participant S as System
    U->>S: Request
    S-->>U: Response
""",
    "state_machine": """stateDiagram-v2
    [*] --> State1
    State1 --> State2
    State2 --> [*]
""",
    "schema": """erDiagram
    ENTITY_A ||--o{ ENTITY_B : relates_to
    ENTITY_A {
      string id
      string name
    }
    ENTITY_B {
      string id
      string entity_a_id
    }
""",
    "kg_view": """flowchart LR
    A((Entity A)) -- relates_to --> B((Entity B))
    B -- influenced_by --> C((Entity C))
""",
    "timeline": """flowchart LR
    T1[Phase 1] --> T2[Phase 2] --> T3[Phase 3]
""",
    "ui_flow": """flowchart LR
    Home[Home Screen] --> Action{User Action}
    Action -->|Path 1| Screen1[Screen 1]
    Action -->|Path 2| Screen2[Screen 2]
""",
    "ml_eval_flow": """flowchart TB
    Data[Dataset] --> Train[Train Model]
    Train --> Eval[Evaluate]
    Eval --> Compare[Compare Metrics]
""",
}


# -------------------------------------------------------------------
# PATHS & BASIC SETUP
# -------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT_DIR / "diagrams"
INDEX_PATH = ROOT_DIR / "diagram_index" / "index.yaml"


# -------------------------------------------------------------------
# LAZY SESSION STATE INITIALIZATION (best practice)
# -------------------------------------------------------------------

def init_session_state() -> None:
    """Initialize all session state keys used across tabs."""
    if "last_created_diagram" not in st.session_state:
        st.session_state.last_created_diagram = None  # type: Optional[Path]
    if "newdiag_project" not in st.session_state:
        st.session_state.newdiag_project = ""
    if "newdiag_topic" not in st.session_state:
        st.session_state.newdiag_topic = ""
    if "newdiag_version" not in st.session_state:
        st.session_state.newdiag_version = DEFAULT_VERSION
    if "newdiag_visibility" not in st.session_state:
        st.session_state.newdiag_visibility = "private"
    if "newdiag_status" not in st.session_state:
        st.session_state.newdiag_status = "draft"
    if "newdiag_sequence_group" not in st.session_state:
        st.session_state.newdiag_sequence_group = ""
    if "newdiag_sequence_order" not in st.session_state:
        st.session_state.newdiag_sequence_order = 1
    if "newdiag_description" not in st.session_state:
        st.session_state.newdiag_description = ""
    if "newdiag_type_fragment" not in st.session_state:
        st.session_state.newdiag_type_fragment = DIAGRAM_TYPE_OPTIONS[0][1]


# -------------------------------------------------------------------
# DOMAIN MODELS
# -------------------------------------------------------------------

@dataclass
class SequenceInfo:
    group: Optional[str] = None
    order: Optional[int] = None


@dataclass
class Diagram:
    id: str
    title: str
    project: str
    path: Path
    repo: Optional[str] = None
    visibility: str = "private"
    status: str = "draft"
    tags: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    description: Optional[str] = None
    sequence: SequenceInfo = field(default_factory=SequenceInfo)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def svg_path(self) -> Path:
        return DIAGRAMS_DIR / self.path.name.replace(".mmd", ".svg")


# -------------------------------------------------------------------
# LOADING & PARSING
# -------------------------------------------------------------------

def load_index(index_path: Path = INDEX_PATH) -> List[Diagram]:
    """Load diagrams from diagram_index/index.yaml into Diagram objects."""
    if not index_path.exists():
        return []

    data = yaml.safe_load(index_path.read_text()) or {}
    items = data.get("diagrams", []) or []

    diagrams: List[Diagram] = []
    for item in items:
        raw_path = item.get("path", "")
        path = (ROOT_DIR / raw_path).resolve()

        seq_meta = item.get("sequence", {}) or {}
        sequence = SequenceInfo(
            group=seq_meta.get("group"),
            order=seq_meta.get("order"),
        )

        diagrams.append(
            Diagram(
                id=item.get("id", path.stem),
                title=item.get("title", path.stem),
                project=item.get("project", ROOT_DIR.name),
                path=path,
                repo=item.get("repo"),
                visibility=item.get("visibility", "private"),
                status=item.get("status", "draft"),
                tags=list(item.get("tags", []) or []),
                last_updated=item.get("last_updated"),
                description=item.get("description"),
                sequence=sequence,
                raw=item,
            )
        )

    return diagrams


def get_distinct_values(diagrams: List[Diagram], attr: str) -> List[str]:
    values = {getattr(d, attr) for d in diagrams if getattr(d, attr)}
    return sorted(values)


# -------------------------------------------------------------------
# UI HELPERS
# -------------------------------------------------------------------

def inject_css() -> None:
    """A touch of CSS for nicer chips and badges."""
    css = """
    <style>
    .tag-chip {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        margin: 0 0.2rem 0.2rem 0;
        border-radius: 999px;
        border: 1px solid #ccc;
        font-size: 0.75rem;
        background-color: #f7f7f7;
    }
    .badge {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        margin-right: 0.35rem;
        border-radius: 999px;
        font-size: 0.7rem;
        color: white;
    }
    .badge-status-draft { background-color: #6c757d; }
    .badge-status-stable { background-color: #198754; }
    .badge-status-deprecated { background-color: #dc3545; }

    .badge-visibility-public { background-color: #0d6efd; }
    .badge-visibility-internal { background-color: #6f42c1; }
    .badge-visibility-private { background-color: #495057; }

    .diagram-card {
        padding: 0.6rem 0.8rem;
        border-radius: 0.6rem;
        border: 1px solid #e0e0e0;
        background-color: #fcfcfc;
    }
    .small-muted { color: #666; font-size: 0.85rem; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_tags(tags: List[str]) -> None:
    if not tags:
        return
    html = " ".join(f'<span class="tag-chip">{t}</span>' for t in tags)
    st.markdown(html, unsafe_allow_html=True)


def render_status_and_visibility(diagram: Diagram) -> None:
    status_class = f"badge-status-{diagram.status}"
    vis_class = f"badge-visibility-{diagram.visibility}"
    html = f"""
        <span class="badge {status_class}">{diagram.status}</span>
        <span class="badge {vis_class}">{diagram.visibility}</span>
    """
    st.markdown(html, unsafe_allow_html=True)


def relpath_posix(p: Path) -> str:
    """Return a nice repo-relative POSIX path for embedding snippets."""
    try:
        return p.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return p.as_posix()


# -------------------------------------------------------------------
# NEW DIAGRAM WIZARD HELPERS
# -------------------------------------------------------------------

def slugify(text: str) -> str:
    """Very small slugifier for filenames."""
    return (
        text.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def build_filename(domain: str, diagram_type: str, topic: str, version: str) -> str:
    """
    Build a filename matching the blog convention:
        {domain}_{diagram_type}_{topic}_v{version}.mmd
    """
    bits = [slugify(b) for b in [domain, diagram_type, topic] if b.strip()]
    stem = "_".join(bits) if bits else "diagram"
    return f"{stem}_v{version}.mmd"


def build_frontmatter(
    diagram_id: str,
    title: str,
    project: str,
    visibility: str,
    status: str,
    tags: List[str],
    last_updated: str,
    description: str,
    sequence_group: str,
    sequence_order: Optional[int],
    supersedes: str = "",
) -> str:
    """Create YAML frontmatter string."""
    meta: Dict[str, Any] = {
        "id": diagram_id,
        "title": title,
        "project": project,
        "visibility": visibility,
        "status": status,
        "last_updated": last_updated,
        "tags": tags,
    }

    if description.strip():
        meta["description"] = description.strip()
    if supersedes.strip():
        meta["supersedes"] = supersedes.strip()
    if sequence_group.strip():
        meta["sequence"] = {
            "group": sequence_group.strip(),
            "order": sequence_order,
        }

    yaml_block = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{yaml_block}\n---\n"


def build_mmd_file(frontmatter: str, skeleton: str) -> str:
    """Combine frontmatter + Mermaid skeleton.

    A .mmd file is raw Mermaid: no ```mermaid fences, which mmdc would try to parse as diagram code.
    """
    return f"{frontmatter}{skeleton.rstrip()}\n"


# -------------------------------------------------------------------
# VIEWS / TABS
# -------------------------------------------------------------------

def overview_tab(diagrams: List[Diagram]) -> None:
    st.subheader("Overview")
    if not diagrams:
        st.info(
            "No diagrams found in the index yet. "
            "Add entries to `diagram_index/index.yaml` to get started."
        )
        return

    projects = {d.project for d in diagrams}
    seq_groups = {d.sequence.group for d in diagrams if d.sequence.group}

    col1, col2, col3 = st.columns(3)
    col1.metric("Total diagrams", len(diagrams))
    col2.metric("Projects", len(projects))
    col3.metric("Sequence groups", len(seq_groups))

    st.markdown(
        """
        This helper app is a lightweight interface over your Mermaid library.

        - Index source of truth: `diagram_index/index.yaml`
        - Diagram sources & SVG previews: `./diagrams/`
        - Sequences support teaching/storytelling arcs
        """
    )


def checklist_tab() -> None:
    st.subheader("Workflow Checklist")

    st.markdown(
        """
        1. **Centralize** diagrams in `/diagrams/`  
        2. **Name** diagrams predictably (domain + type + topic + version)  
        3. **Add YAML frontmatter metadata**  
        4. **Render** `.mmd → .svg` with `scripts/render_diagrams.sh`  
        5. **Index** important diagrams in `diagram_index/index.yaml`  
        6. **Use sequences** for teaching/storytelling arcs  
        """
    )

    st.markdown("### Metadata frontmatter template")
    st.code(
        """---
id: my_diagram_id_v1
title: My Diagram Title
project: my_project
visibility: private            # public | internal | private
status: draft                  # draft | stable | deprecated
last_updated: 2025-11-19
tags: [etl, pipeline, mermaid]
sequence:
  group: "my-story-arc"
  order: 1
description: >
  One-sentence summary of what this diagram shows.
---
""",
        language="yaml",
    )

    st.markdown("### Render-all script reminder")
    st.code(
        """#!/usr/bin/env bash
set -euo pipefail

for f in diagrams/*.mmd; do
  base="${f%.mmd}"
  npx mmdc -i "$f" -o "${base}.svg"
done
""",
        language="bash",
    )


def explorer_tab(diagrams: List[Diagram]) -> None:
    st.subheader("Diagram Explorer")

    if not diagrams:
        st.info("No diagrams found in the index yet.")
        return

    projects = ["any"] + get_distinct_values(diagrams, "project")
    visibilities = ["any"] + get_distinct_values(diagrams, "visibility")
    statuses = ["any"] + get_distinct_values(diagrams, "status")

    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            project_filter = st.selectbox("Project", projects, key="expl_project")
        with c2:
            visibility_filter = st.selectbox("Visibility", visibilities, key="expl_visibility")
        with c3:
            status_filter = st.selectbox("Status", statuses, key="expl_status")

        search_text = st.text_input(
            "Search (title, id, tags)",
            placeholder="e.g. evaluation, routing, fitness…",
            key="expl_search",
        ).strip().lower()

    filtered: List[Diagram] = []
    for d in diagrams:
        if project_filter != "any" and d.project != project_filter:
            continue
        if visibility_filter != "any" and d.visibility != visibility_filter:
            continue
        if status_filter != "any" and d.status != status_filter:
            continue
        if search_text:
            haystack = " ".join([d.title, d.id, " ".join(d.tags)]).lower()
            if search_text not in haystack:
                continue
        filtered.append(d)

    st.write(f"**{len(filtered)}** diagram(s) match filters.")
    if not filtered:
        return

    filtered.sort(key=lambda d: (d.project, d.title))

    for diagram in filtered:
        label = f"{diagram.title}  ·  `{diagram.id}`"
        with st.expander(label, expanded=False):
            st.markdown('<div class="diagram-card">', unsafe_allow_html=True)
            col_meta, col_preview = st.columns([2, 3])

            with col_meta:
                st.markdown(f"**Project:** `{diagram.project}`")
                st.markdown(f"**Source:** `{relpath_posix(diagram.path)}`")
                render_status_and_visibility(diagram)
                render_tags(diagram.tags)

                if diagram.last_updated:
                    st.markdown(f"**Last updated:** {diagram.last_updated}")
                if diagram.description:
                    st.markdown(f"**Description:** {diagram.description}")

            with col_preview:
                if diagram.svg_path.exists():
                    st.markdown("**Preview:**")
                    st.image(str(diagram.svg_path))
                else:
                    st.warning(
                        f"SVG missing at `{relpath_posix(diagram.svg_path)}`. "
                        "Run `./scripts/render_diagrams.sh`."
                    )

            # --- Usage snippets (NEW) ---
            st.markdown("---")
            st.markdown("**Usage snippets**")
            svg_rel = relpath_posix(diagram.svg_path)
            mmd_rel = relpath_posix(diagram.path)

            md_embed = f"![{diagram.title}]({svg_rel})"
            md_link_source = f"[Mermaid source]({mmd_rel})"
            jekyll_include = (
                f'{{% include diagram.html src="{svg_rel}" alt="{diagram.title}" %}}'
            )

            st.code(md_embed, language="markdown")
            st.code(md_link_source, language="markdown")
            st.code(jekyll_include, language="liquid")

            st.markdown("</div>", unsafe_allow_html=True)


def sequences_tab(diagrams: List[Diagram]) -> None:
    st.subheader("Diagram Sequences")

    sequences: Dict[str, List[Diagram]] = {}
    for d in diagrams:
        if d.sequence.group:
            sequences.setdefault(d.sequence.group, []).append(d)

    if not sequences:
        st.info(
            "No diagrams with sequence metadata yet. "
            "Add `sequence.group` and `sequence.order` in frontmatter."
        )
        return

    group_names = sorted(sequences.keys())
    group = st.selectbox("Sequence group", group_names, key="seq_group")

    seq_items = sorted(
        sequences[group],
        key=lambda d: d.sequence.order if d.sequence.order is not None else 0,
    )

    st.markdown(
        "Sequences are great for **teaching**, **storytelling**, and **archiving**. "
        "Each group acts like a storyboard."
    )

    for d in seq_items:
        order = d.sequence.order if d.sequence.order is not None else "?"
        st.markdown(f"### Step {order}: {d.title}")
        st.markdown(f"`{d.id}`  ·  Project: `{d.project}`")
        render_status_and_visibility(d)
        render_tags(d.tags)

        if d.description:
            st.markdown(d.description)

        if d.svg_path.exists():
            st.image(str(d.svg_path))
        else:
            st.warning(
                f"SVG missing at `{relpath_posix(d.svg_path)}`. "
                "Run `./scripts/render_diagrams.sh`."
            )

        st.markdown("---")


def diagram_types_tab() -> None:
    st.subheader("Diagram Types & Templates")

    st.markdown(
        "A quick reference of Mermaid-friendly diagram types, what they’re good for, "
        "and suggested filename fragments."
    )

    st.table(
        {
            "Diagram type": [t[0] for t in DIAGRAM_TYPE_OPTIONS],
            "Good for": [t[2] for t in DIAGRAM_TYPE_OPTIONS],
            "Suggested fragment": [t[1] for t in DIAGRAM_TYPE_OPTIONS],
        }
    )

    st.markdown("### Naming pattern reminder")
    st.code(
        "{domain_or_area}_{diagram_type}_{topic}_v{major}.{minor}.mmd",
        language="text",
    )

    st.markdown("### Examples")
    st.code(
        "\n".join(
            [
                "etl_data_flow_core_v1.0.mmd",
                "llm_decision_tree_routing_v0.3.mmd",
                "platform_architecture_high_level_v1.1.mmd",
                "ml_evaluation_workflow_v1.0.mmd",
            ]
        ),
        language="text",
    )


def new_diagram_tab(diagrams: List[Diagram]) -> None:
    """NEW: Wizard for generating a new .mmd file with metadata + skeleton."""
    st.subheader("New Diagram Wizard")

    # Ensure diagrams folder exists (safe side-effect)
    DIAGRAMS_DIR.mkdir(exist_ok=True)

    # Populate projects dropdown from existing index
    known_projects = sorted({d.project for d in diagrams}) if diagrams else []
    project_options = ["(new project)"] + known_projects

    # Format func for diagram type dropdown
    def type_label(idx: int) -> str:
        return DIAGRAM_TYPE_OPTIONS[idx][0]

    with st.form("new_diagram_form", clear_on_submit=False):
        c1, c2 = st.columns([2, 3])

        with c1:
            project_choice = st.selectbox(
                "Project",
                project_options,
                index=0,
                key="newdiag_project_choice",
                help="Pick an existing project or choose '(new project)'.",
            )
            project_text = st.text_input(
                "New project name (if applicable)",
                value=st.session_state.newdiag_project,
                key="newdiag_project_text",
                help="Only used when Project = (new project).",
            )

            diagram_type_idx = st.selectbox(
                "Diagram type",
                list(range(len(DIAGRAM_TYPE_OPTIONS))),
                format_func=type_label,
                key="newdiag_type_idx",
            )
            diagram_type_fragment = DIAGRAM_TYPE_OPTIONS[diagram_type_idx][1]
            st.caption(DIAGRAM_TYPE_OPTIONS[diagram_type_idx][2])

            topic = st.text_input(
                "Topic",
                value=st.session_state.newdiag_topic,
                key="newdiag_topic_input",
                help="Short descriptor, e.g. core, routing, onboarding.",
            )

        with c2:
            version = st.text_input(
                "Version",
                value=st.session_state.newdiag_version,
                key="newdiag_version_input",
                help="Semantic-ish version for the filename, e.g. 0.1, 1.0.",
            )

            visibility = st.selectbox(
                "Visibility",
                VISIBILITY_OPTIONS,
                index=VISIBILITY_OPTIONS.index(st.session_state.newdiag_visibility),
                key="newdiag_visibility_select",
            )

            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(st.session_state.newdiag_status),
                key="newdiag_status_select",
            )

            tags_text = st.text_input(
                "Tags (comma-separated)",
                key="newdiag_tags_text",
                help="Optional. Example: etl, pipeline, mermaid",
            )

            description = st.text_area(
                "Description",
                value=st.session_state.newdiag_description,
                key="newdiag_description_area",
                height=100,
                help="Optional one-paragraph summary.",
            )

        st.markdown("**Optional sequence metadata**")
        c3, c4 = st.columns(2)
        with c3:
            seq_group = st.text_input(
                "Sequence group",
                value=st.session_state.newdiag_sequence_group,
                key="newdiag_seq_group_input",
                help="Use to chain diagrams into a teaching/story arc.",
            )
        with c4:
            seq_order = st.number_input(
                "Sequence order",
                min_value=0,
                value=int(st.session_state.newdiag_sequence_order),
                step=1,
                key="newdiag_seq_order_input",
            )

        submitted = st.form_submit_button("Create diagram file")

    # Handle submit OUTSIDE form (single-pass state update; no rerun loops)
    if submitted:
        # Determine project name
        project_name = (
            project_text.strip()
            if project_choice == "(new project)"
            else project_choice
        )
        if not project_name:
            st.error("Please provide a project name.")
            return

        if not topic.strip():
            st.error("Please provide a topic.")
            return

        # Parse tags
        tags = [slugify(t) for t in tags_text.split(",") if t.strip()]

        # Build filename and paths
        filename = build_filename(project_name, diagram_type_fragment, topic, version)
        file_path = DIAGRAMS_DIR / filename

        # Frontmatter fields
        diag_id = file_path.stem  # reasonable default id aligned to filename
        title = f"{DIAGRAM_TYPE_OPTIONS[diagram_type_idx][0]} — {topic.strip()}"

        frontmatter = build_frontmatter(
            diagram_id=diag_id,
            title=title,
            project=project_name,
            visibility=visibility,
            status=status,
            tags=tags,
            last_updated=str(date.today()),
            description=description,
            sequence_group=seq_group,
            sequence_order=int(seq_order) if seq_group.strip() else None,
        )

        skeleton = DIAGRAM_SKELETONS.get(diagram_type_fragment, "flowchart LR\n    A --> B\n")
        mmd_content = build_mmd_file(frontmatter, skeleton)

        # Preview before write (progressive disclosure)
        with st.expander("Preview file content", expanded=True):
            st.markdown(f"**Will create:** `{relpath_posix(file_path)}`")
            st.code(mmd_content, language="markdown")

        # Write file (idempotent behavior)
        if file_path.exists():
            st.warning(f"File already exists: `{relpath_posix(file_path)}`. Not overwritten.")
        else:
            file_path.write_text(mmd_content)
            st.session_state.last_created_diagram = file_path
            st.success(f"Created new diagram file: `{relpath_posix(file_path)}`")
            st.info("Next steps: open it in your editor, fill in the diagram, then run `./scripts/render_diagrams.sh`.")


# -------------------------------------------------------------------
# MAIN ENTRYPOINT
# -------------------------------------------------------------------

def main() -> None:
    init_session_state()

    st.set_page_config(
        page_title="Mermaid Diagram Workflow Helper",
        layout="wide",
        page_icon="🧠",
    )
    inject_css()

    st.title("Mermaid Diagram Workflow Helper")
    st.caption(
        "A companion app for organizing, creating, and teaching with Mermaid diagrams."
    )

    diagrams = load_index(INDEX_PATH)

    # Sidebar: paths + stats
    st.sidebar.markdown("### Paths")
    st.sidebar.write(f"**Root:** `{ROOT_DIR}`")
    st.sidebar.write(f"**Diagrams:** `{DIAGRAMS_DIR.relative_to(ROOT_DIR)}`")
    st.sidebar.write(f"**Index:** `{INDEX_PATH.relative_to(ROOT_DIR)}`")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick stats")
    st.sidebar.write(f"Diagrams in index: **{len(diagrams)}**")

    if st.session_state.last_created_diagram:
        st.sidebar.markdown("### Last created")
        st.sidebar.write(f"`{relpath_posix(st.session_state.last_created_diagram)}`")

    # Tabs (NEW tab added)
    (
        tab_overview,
        tab_checklist,
        tab_explorer,
        tab_sequences,
        tab_types,
        tab_newdiag,
    ) = st.tabs(
        [
            "Overview",
            "Checklist",
            "Diagram Explorer",
            "Sequences",
            "Diagram Types & Templates",
            "New Diagram",
        ]
    )

    with tab_overview:
        overview_tab(diagrams)
    with tab_checklist:
        checklist_tab()
    with tab_explorer:
        explorer_tab(diagrams)
    with tab_sequences:
        sequences_tab(diagrams)
    with tab_types:
        diagram_types_tab()
    with tab_newdiag:
        new_diagram_tab(diagrams)


if __name__ == "__main__":
    main()
