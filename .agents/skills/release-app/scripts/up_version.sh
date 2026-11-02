#!/bin/bash

# up_version.sh
# Bumps semantic version in job_filter/__init__.py, job_filter/config.py, and static/index.html
# Usage: ./up_version.sh [patch|minor|major] (defaults to patch)

set -e

BUMP_TYPE="${1:-patch}"

INIT_FILE="job_filter/__init__.py"
CONFIG_FILE="job_filter/config.py"
HTML_FILE="static/index.html"

if [ ! -f "$INIT_FILE" ]; then
    echo "Error: Could not find $INIT_FILE"
    exit 1
fi

CURRENT_VERSION=$(grep -E '^__version__\s*=' "$INIT_FILE" | awk -F '"' '{print $2}')

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not extract __version__ from $INIT_FILE"
    exit 1
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
MAJOR=${MAJOR:-0}
MINOR=${MINOR:-0}
PATCH=${PATCH:-0}

case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "Unknown bump type: $BUMP_TYPE (use: patch, minor, major)"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"

# Update job_filter/__init__.py (macOS and Linux compatible sed)
sed -i '' "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" "$INIT_FILE"

# Update job_filter/config.py if present
if [ -f "$CONFIG_FILE" ]; then
    sed -i '' "s/APP_VERSION = \"$CURRENT_VERSION\"/APP_VERSION = \"$NEW_VERSION\"/" "$CONFIG_FILE"
fi

# Update static/index.html if present
if [ -f "$HTML_FILE" ]; then
    sed -i '' "s/v$CURRENT_VERSION/v$NEW_VERSION/g" "$HTML_FILE"
fi

echo "Bumped version from $CURRENT_VERSION to $NEW_VERSION ($BUMP_TYPE)"
