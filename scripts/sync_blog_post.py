#!/usr/bin/env python3
"""
DESCRIPTION: 
Sync a blog post + diagram assets from the current project
into a Jekyll site (dagny099.github.io).

Features:
1. Copy all .svg files from the current project into:
   /Users/bhs/PROJECTS/dagny099.github.io/assets/diagrams

2. Copy a single markdown file from ./blog/<filename>
   into:
   /Users/bhs/PROJECTS/dagny099.github.io/_posts

3. While copying the markdown file, rewrite image paths
   for .svg / .png to point to /assets/diagrams/<filename>,
   and copy those referenced images into assets/diagrams.

SAMPLE USAGE: 
> ./sync_blog_post.py mermaid-diagram-workflow.md
or
> python sync_blog_post.py mermaid-diagram-workflow.md

"""

import argparse
import re
import shutil
from pathlib import Path


# Adjust if your Jekyll root ever changes
JEKYLL_ROOT = Path("/Users/bhs/PROJECTS/dagny099.github.io")
JEKYLL_DIAGRAMS_DIR = JEKYLL_ROOT / "assets" / "diagrams"
JEKYLL_POSTS_DIR = JEKYLL_ROOT / "_posts"


def copy_all_svgs(project_root: Path) -> None:
    """
    Copy all .svg files under project_root into JEKYLL_DIAGRAMS_DIR.
    Preserves only the filename (flattens structure).
    """
    JEKYLL_DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

    #svg_files = list(project_root.rglob("*.svg"))
    svg_files = list((project_root / "diagrams").glob("*.svg"))

    print(f"Found {len(svg_files)} .svg files under {project_root}")

    for svg in svg_files:
        target = JEKYLL_DIAGRAMS_DIR / svg.name
        print(f"Copying SVG: {svg} -> {target}")
        shutil.copy2(svg, target)


def rewrite_and_copy_images_in_markdown(
    src_md: Path,
    dest_md: Path,
    project_root: Path,
) -> None:
    """
    Read src_md, find image references to .svg/.png,
    copy those images into JEKYLL_DIAGRAMS_DIR,
    and rewrite the paths in the markdown to /assets/diagrams/<filename>.

    Writes the modified markdown to dest_md.
    """

    JEKYLL_DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

    text = src_md.read_text(encoding="utf-8")

    # Regex for markdown images: ![alt](path "title")
    img_pattern = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')

    def replace_match(match: re.Match) -> str:
        original_path = match.group(1).strip()

        # Ignore URLs and already-absolute /assets paths
        if original_path.startswith("http://") or original_path.startswith("https://"):
            return match.group(0)
        if original_path.startswith("/assets/"):
            return match.group(0)

        # Strip any optional title: path "title"
        if " " in original_path and not original_path.startswith(("./", "../")):
            # naive split: path "title"
            possible_path = original_path.split(" ")[0]
        else:
            possible_path = original_path

        ext = Path(possible_path).suffix.lower()
        if ext not in {".svg", ".png"}:
            return match.group(0)

        # Try to resolve the source image path
        # 1) relative to the markdown file
        src_candidate = (src_md.parent / possible_path).resolve()

        # 2) fallback: relative to project root
        if not src_candidate.exists():
            src_candidate = (project_root / possible_path).resolve()

        if not src_candidate.exists():
            print(f"WARNING: image not found for path: {original_path} (resolved: {src_candidate})")
            return match.group(0)

        # Copy into JEKYLL_DIAGRAMS_DIR with just the filename
        dest_img = JEKYLL_DIAGRAMS_DIR / src_candidate.name
        print(f"Copying image: {src_candidate} -> {dest_img}")
        shutil.copy2(src_candidate, dest_img)

        
        # New path in Liquid 
        new_path = "{{ '/assets/diagrams/" + src_candidate.name + "' | relative_url }}"
        #new_path = f"/assets/diagrams/{src_candidate.name}" # New path in markdown

        # Reconstruct the markdown image with the updated path
        alt_text_match = re.match(r'!\[([^\]]*)\]\([^)]+\)', match.group(0))
        alt_text = alt_text_match.group(1) if alt_text_match else ""

        return f"![{alt_text}]({new_path})"

    new_text = img_pattern.sub(replace_match, text)

    dest_md.parent.mkdir(parents=True, exist_ok=True)
    dest_md.write_text(new_text, encoding="utf-8")
    print(f"Wrote updated markdown to: {dest_md}")


def main():
    parser = argparse.ArgumentParser(
        description="Sync a blog post and diagram assets into dagny099.github.io"
    )
    parser.add_argument(
        "markdown_filename",
        help="Name of the markdown file in ./blog (e.g., my-post.md)",
    )
    args = parser.parse_args()

    project_root = Path.cwd()
    blog_dir = project_root / "blog"
    src_md = blog_dir / args.markdown_filename

    if not src_md.exists():
        raise SystemExit(f"Markdown file not found: {src_md}")

    if not JEKYLL_ROOT.exists():
        raise SystemExit(f"Jekyll root not found: {JEKYLL_ROOT}")

    # 1) Copy all SVGs from this project
    print("=== Copying all SVG diagrams from current project ===")
    copy_all_svgs(project_root)

    # 2) Rewrite markdown image paths and copy referenced images
    dest_md = JEKYLL_POSTS_DIR / args.markdown_filename
    print("\n=== Rewriting markdown + copying referenced images ===")
    rewrite_and_copy_images_in_markdown(src_md, dest_md, project_root)

    print("\nDone. You may want to:")
    print(f"  - run `bundle exec jekyll serve` in {JEKYLL_ROOT}")
    print("  - check that the post renders and images load correctly.")


if __name__ == "__main__":
    main()
