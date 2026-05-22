#!/usr/bin/env bash
# Export docs/diagrams/architecture_business.svg → PNG for slide decks.
# No Homebrew required — see fallbacks below.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$ROOT/docs/diagrams/architecture_business.svg"
OUT="$ROOT/docs/diagrams/architecture_business.png"

export_png() {
  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 2200 "$SVG" -o "$OUT"
    return 0
  fi
  if command -v inkscape >/dev/null 2>&1; then
    inkscape "$SVG" --export-type=png --export-filename="$OUT" -w 2200
    return 0
  fi
  # macOS built-in Quick Look (no brew)
  if [[ "$(uname -s)" == Darwin ]] && command -v qlmanage >/dev/null 2>&1; then
    tmpdir="$(mktemp -d)"
    qlmanage -t -s 2200 -o "$tmpdir" "$SVG" >/dev/null 2>&1 || true
    generated="$(find "$tmpdir" -maxdepth 1 -name '*.png' | head -1)"
    if [[ -n "$generated" && -f "$generated" ]]; then
      mv "$generated" "$OUT"
      rm -rf "$tmpdir"
      return 0
    fi
    rm -rf "$tmpdir"
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$SVG" "$OUT" <<'PY' && return 0
import sys
svg_path, out_path = sys.argv[1], sys.argv[2]
try:
    import cairosvg
except ImportError:
    sys.exit(1)
cairosvg.svg2png(url=svg_path, write_to=out_path, output_width=2200)
PY
  fi
  return 1
}

if export_png; then
  echo "Wrote $OUT"
  exit 0
fi

cat >&2 <<'EOF'
Could not export PNG. You do NOT need PNG for GitHub — use the SVG directly in README/slides.

Optional installs (pick one, no Homebrew required):
  macOS (built-in):  qlmanage -t -s 2200 -o docs/diagrams docs/diagrams/architecture_business.svg
                     then: mv docs/diagrams/architecture_business.svg.png docs/diagrams/architecture_business.png
  Debian/Ubuntu:     sudo apt install librsvg2-bin
  Fedora:            sudo dnf install librsvg2-tools
  Windows:           winget install Inkscape.Inkscape
  Python (any OS):   pip install cairosvg   # may need system cairo libraries
  Manual:            Open the SVG in a browser → screenshot or Print to PDF

Or drag docs/diagrams/architecture_business.svg into Google Slides / PowerPoint (vector stays sharp).
EOF
exit 1
