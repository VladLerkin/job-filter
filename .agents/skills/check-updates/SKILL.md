---
name: check-updates
description: Check for Python dependency updates against PyPI, update requirements and verify tests
---

# Check Updates Skill for Job Filter

1. Run the update check script using the project's virtual environment:
   ```bash
   ./.venv/bin/python .agents/skills/check-updates/scripts/check_updates.py
   ```
2. Review the summary table for packages marked as `Update Avail`.
3. Check for stable releases only (ignoring alphas, betas, pre-releases).
4. Update packages in the virtual environment:
   ```bash
   ./.venv/bin/pip install --upgrade <package_name>
   ```
5. Run tests to ensure no regressions:
   ```bash
   ./.venv/bin/pytest tests/
   ```
6. If any requirements file pins versions, update the pinned versions in `requirements.txt` or `requirements-dev.txt`.
