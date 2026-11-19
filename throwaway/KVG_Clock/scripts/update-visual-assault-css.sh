#!/usr/bin/env bash
# Re-vendor VisualAssault's CSS themes at a pinned tag.
set -euo pipefail
TAG="${1:-v0.2.0}"
OUT="$(dirname "$0")/../src/renderer/themes.css"
{
  echo "/* Vendored from gerp93/VisualAssault packages/css/themes.css @ ${TAG} — re-vendor via scripts/update-visual-assault-css.sh */"
  curl -fsSL "https://raw.githubusercontent.com/gerp93/VisualAssault/${TAG}/packages/css/themes.css"
} > "$OUT"
