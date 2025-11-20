from pathlib import Path
from typing import Dict, Any

import frontmatter  # pip install python-frontmatter


def load_frontmatter(path: Path) -> Dict[str, Any]:
    """
    Parse YAML frontmatter from a .mmd file.
    Returns a dict of metadata keys/values.
    If no frontmatter is found, returns {}.
    """
    post = frontmatter.load(path)
    # If there was frontmatter, it's in post.metadata; content is post.content.
    return dict(post.metadata or {})
