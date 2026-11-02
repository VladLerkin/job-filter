#!/bin/bash

# release_app.sh
# Automates the release process for Job Filter:
# 1. Verifies test suite passes
# 2. Checks current version
# 3. Commits all changes with "Release vX.Y.Z"
# 4. Tags the release with annotated release notes from RELEASE_NOTES.md
# 5. Pushes commit and tag to origin

set -e

INIT_FILE="job_filter/__init__.py"
NOTES_FILE="RELEASE_NOTES.md"

if [ ! -f "$INIT_FILE" ]; then
    echo "Error: Could not find $INIT_FILE"
    exit 1
fi

CURRENT_VERSION=$(grep -E '^__version__\s*=' "$INIT_FILE" | awk -F '"' '{print $2}')

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not read version from $INIT_FILE"
    exit 1
fi

TAG_NAME="v$CURRENT_VERSION"
echo "🚀 Preparing release for: $TAG_NAME"

# Optional: Run test suite before releasing
if [ -f ".venv/bin/pytest" ]; then
    echo "🧪 Running pytest suite..."
    .venv/bin/pytest tests/ -q
elif command -v pytest >/dev/null 2>&1; then
    echo "🧪 Running pytest suite..."
    pytest tests/ -q
fi

# Stage and commit
git add .
git commit -m "Release $TAG_NAME" || echo "Nothing new to commit before tagging"

# Extract release notes for this version from RELEASE_NOTES.md
# Looks for "## vCURRENT_VERSION" up to next "## v"
RELEASE_NOTES=""
if [ -f "$NOTES_FILE" ]; then
    RELEASE_NOTES=$(awk "/^## v$CURRENT_VERSION/ {flag=1; next} /^## v/ {flag=0} flag" "$NOTES_FILE" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
fi

# Tag release
if [ -n "$RELEASE_NOTES" ]; then
    git tag -a "$TAG_NAME" -m "Release $TAG_NAME" -m "$RELEASE_NOTES"
    echo "🏷️ Committed and created annotated tag: $TAG_NAME with release notes."
else
    git tag "$TAG_NAME"
    echo "🏷️ Committed and tagged: $TAG_NAME (no release notes found in $NOTES_FILE)."
fi

# Push to origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📤 Pushing branch '$CURRENT_BRANCH' and tag '$TAG_NAME' to origin..."
git push origin "$CURRENT_BRANCH"
git push origin "$TAG_NAME"

echo "🎉 Release $TAG_NAME completed and pushed successfully!"
