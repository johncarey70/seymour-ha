#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.1.0"
    exit 1
fi

VERSION="$1"
TAG="v${VERSION}"
MANIFEST="custom_components/seymour/manifest.json"

if [[ ! -f "$MANIFEST" ]]; then
    echo "Manifest not found: $MANIFEST"
    exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Tag already exists locally: $TAG"
    exit 1
fi

if git ls-remote --tags origin "refs/tags/$TAG" | grep -q "$TAG"; then
    echo "Tag already exists on origin: $TAG"
    exit 1
fi

python3 - "$VERSION" "$MANIFEST" <<'PY'
import json
import sys
from pathlib import Path

version = sys.argv[1]
manifest = Path(sys.argv[2])

data = json.loads(manifest.read_text())
data["version"] = version
manifest.write_text(json.dumps(data, indent=2) + "\n")

print(f"Updated {manifest} to version {version}")
PY

git add .
git commit -m "Release ${TAG}"
git push origin main
git tag "$TAG"
git push origin "$TAG"

echo
echo "Release ${TAG} pushed."
echo "GitHub Actions should create the GitHub release automatically."
