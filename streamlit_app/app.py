import yaml
from pathlib import Path

import streamlit as st


INDEX_PATH = Path(__file__).resolve().parents[1] / "diagram_index" / "index.yaml"
DIAGRAMS_DIR = Path(__file__).resolve().parents[1] / "diagrams"


def load_index():
    if not INDEX_PATH.exists():
        return []
    data = yaml.safe_load(INDEX_PATH.read_text()) or {}
    return data.get("diagrams", [])


def main():
    st.set_page_config(page_title="Mermaid Diagram Workflow Helper", layout="wide")

    st.title("Mermaid Diagram Workflow Helper")
    st.caption("A small companion app for organizing and exploring Mermaid diagrams")

    tabs = st.tabs(["Checklist", "Diagram Explorer", "Sequences"])

    # --- Checklist tab ---
    with tabs[0]:
        st.subheader("Workflow Checklist")
        st.markdown(
            """
            Use this as a quick reminder of the core steps:

            1. **Centralize** diagrams in a `/diagrams/` folder.
            2. **Name** files with a clear pattern (domain + type + topic + version).
            3. **Add metadata** frontmatter (`id`, `project`, `visibility`, `status`, `tags`, etc.).
            4. **Render** all `.mmd` to `.svg` with `scripts/render_diagrams.sh`.
            5. **Index** important diagrams in `diagram_index/index.yaml`.
            6. **Use sequences** (`sequence.group` + `sequence.order`) for teaching/storytelling.
            """
        )

    # --- Diagram Explorer tab ---
    with tabs[1]:
        st.subheader("Diagram Explorer")
        diagrams = load_index()

        if not diagrams:
            st.info("No diagrams found in index.yaml yet.")
        else:
            projects = sorted({d["project"] for d in diagrams})
            visibilities = ["any"] + sorted({d.get("visibility", "private") for d in diagrams})
            statuses = ["any"] + sorted({d.get("status", "draft") for d in diagrams})

            col1, col2, col3 = st.columns(3)
            with col1:
                project_filter = st.selectbox("Project", ["any"] + projects)
            with col2:
                visibility_filter = st.selectbox("Visibility", visibilities)
            with col3:
                status_filter = st.selectbox("Status", statuses)

            filtered = []
            for d in diagrams:
                if project_filter != "any" and d["project"] != project_filter:
                    continue
                if visibility_filter != "any" and d.get("visibility", "private") != visibility_filter:
                    continue
                if status_filter != "any" and d.get("status", "draft") != status_filter:
                    continue
                filtered.append(d)

            st.write(f"{len(filtered)} diagram(s) match the filters.")

            for d in filtered:
                with st.expander(f"{d['title']} ({d['id']})"):
                    st.json(d)
                    svg_path = DIAGRAMS_DIR / Path(d["path"]).name.replace(".mmd", ".svg")
                    if svg_path.exists():
                        st.markdown("**Preview:**")
                        st.image(str(svg_path))
                    else:
                        st.warning(f"SVG not found at {svg_path}. Run render_diagrams.sh?")

    # --- Sequences tab ---
    with tabs[2]:
        st.subheader("Diagram Sequences")
        diagrams = load_index()

        if not diagrams:
            st.info("No diagrams in index.yaml yet.")
        else:
            # Group by sequence.group
            sequences = {}
            for d in diagrams:
                seq = d.get("sequence") or {}
                group = seq.get("group")
                order = seq.get("order", 0)
                if not group:
                    continue
                sequences.setdefault(group, []).append((order, d))

            if not sequences:
                st.info("No diagrams with sequence information yet.")
            else:
                group_names = sorted(sequences.keys())
                group = st.selectbox("Sequence group", group_names)

                seq_items = sorted(sequences[group], key=lambda x: x[0])
                for order, d in seq_items:
                    st.markdown(f"### {order}: {d['title']}")
                    st.write(f"ID: `{d['id']}`")
                    svg_path = DIAGRAMS_DIR / Path(d["path"]).name.replace(".mmd", ".svg")
                    if svg_path.exists():
                        st.image(str(svg_path))
                    else:
                        st.warning(f"SVG not found at {svg_path}")
                    st.markdown("---")


if __name__ == "__main__":
    main()
