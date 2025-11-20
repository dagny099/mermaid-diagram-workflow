from pathlib import Path
from typing import List, Optional

from .models import Diagram, DiagramSequenceInfo
from .metadata import load_frontmatter


def scan_diagrams(root: Path, repo: Optional[str] = None) -> List[Diagram]:
    """
    Scan a repo root for .mmd files under ./diagrams and
    return Diagram objects with metadata populated from frontmatter.
    """
    diagrams_dir = root / "diagrams"
    if not diagrams_dir.exists():
        return []

    diagrams: List[Diagram] = []

    for path in diagrams_dir.glob("*.mmd"):
        meta = load_frontmatter(path)

        seq_meta = meta.get("sequence", {}) or {}
        sequence = DiagramSequenceInfo(
            group=seq_meta.get("group"),
            order=seq_meta.get("order"),
        )

        diag = Diagram(
            id=meta.get("id", path.stem),
            title=meta.get("title", path.stem),
            project=meta.get("project", root.name),
            path=path,
            repo=repo,
            visibility=meta.get("visibility", "private"),
            status=meta.get("status", "draft"),
            tags=list(meta.get("tags", []) or []),
            last_updated=meta.get("last_updated"),
            description=meta.get("description"),
            sequence=sequence,
            raw_metadata=meta,
        )
        diagrams.append(diag)

    return diagrams
