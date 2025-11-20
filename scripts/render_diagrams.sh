# scripts/render_diagrams.sh
for f in diagrams/*.mmd; do
  base="${f%.mmd}"
  npx mmdc -i "$f" -o "${base}.svg"
  echo "Rendered $f -> ${base}.svg"
done
