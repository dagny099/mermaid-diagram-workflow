#!/usr/bin/env bash
# Render every Mermaid file in diagrams/ to an SVG next to it.
set -euo pipefail

echo "Rendering all Mermaid diagrams in ./diagrams"
for f in diagrams/*.mmd; do
  out="${f%.mmd}.svg"
  echo "  - $f -> $out"
  npx mmdc -i "$f" -o "$out" --quiet
done
echo "Done!"
