---
name: release-app
description: Release a new version of Job Filter (Bump version, Update Release Notes, Run Tests, Commit, Tag, Push)
---

# Release App Skill

When the user asks to release a new version of Job Filter, follow these steps strictly:

## 1. Pre-flight & Test Verification
Run pytest to ensure all test suites pass before releasing:
```bash
./.venv/bin/pytest tests/
```
If any test fails, resolve the issue before proceeding with the release.

## 2. Bump Version
Run the version increment script from the project root:
```bash
.agents/skills/release-app/scripts/up_version.sh [patch|minor|major]
```
*(Default is `patch` if no argument is passed. Use `minor` for new features or `major` for breaking architectural changes)*.
This script automatically synchronizes the version across:
- `job_filter/__init__.py` (`__version__ = "X.Y.Z"`)
- `job_filter/config.py` (`APP_VERSION = "X.Y.Z"`)
- `static/index.html` (header version badge)

Note the new version output by the script (e.g. `1.1.0`).

## 3. Draft Release Notes
Review recent git commits to generate a structured summary of changes:
```bash
git log --oneline -n 25
```
Group changes into clear sections:
- **Features & Architecture**
- **Integrations & Scraping**
- **UI & Usability**
- **Bug Fixes & Maintenance**

## 4. Update `RELEASE_NOTES.md`
Update `RELEASE_NOTES.md` in the project root by prepending a new section right below the `# Release Notes` heading:
```markdown
## vX.Y.Z
**Release Date:** Month Day, Year

### Features & Improvements
- Description of feature 1
- Description of feature 2

### Bug Fixes
- Description of bug fix
```

## 5. Publish Release
Run the automated release script from the project root:
```bash
.agents/skills/release-app/scripts/release_app.sh
```
This script will:
1. Re-verify the test suite.
2. Commit all updated files with `Release vX.Y.Z`.
3. Extract the release notes for `## vX.Y.Z` from `RELEASE_NOTES.md`.
4. Create an annotated git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z" -m "<release-notes>"`.
5. Push both the branch commit and the annotated tag to the remote repository (`origin`).

