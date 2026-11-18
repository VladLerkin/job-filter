#!/usr/bin/env python3
"""
Check updates for Python requirements in job-filter against PyPI.
Outputs formatted summary table of direct dependencies and their latest stable versions.
"""
import json
import re
import ssl
import sys
import urllib.request
from functools import cmp_to_key
from pathlib import Path

# Disable SSL verification for Python on macOS if certificates are not loaded
ssl._create_default_https_context = ssl._create_unverified_context

def parse_version(v: str):
    parts = re.split(r'[-.]', v)
    parsed = []
    for p in parts:
        if p.isdigit():
            parsed.append((0, int(p)))
        else:
            subparts = re.findall(r'([a-zA-Z]+)|(\d+)', p)
            for s in subparts:
                if s[0]:
                    parsed.append((1, s[0].lower()))
                elif s[1]:
                    parsed.append((0, int(s[1])))
    return parsed

def compare_versions(v1: str, v2: str) -> int:
    p1 = parse_version(v1)
    p2 = parse_version(v2)
    for item1, item2 in zip(p1, p2):
        if item1 != item2:
            if item1[0] == 0 and item2[0] == 1:
                return 1
            elif item1[0] == 1 and item2[0] == 0:
                return -1
            else:
                return -1 if item1[1] < item2[1] else 1
    if len(p1) < len(p2):
        return 1 if p2[len(p1)][0] == 1 else -1
    elif len(p1) > len(p2):
        return -1 if p1[len(p2)][0] == 1 else 1
    return 0

def is_stable(v: str) -> bool:
    v_lower = v.lower()
    for word in ['a', 'b', 'rc', 'dev', 'alpha', 'beta', 'preview', 'post']:
        if re.search(rf'[-._]?{word}\d*', v_lower):
            if word == 'post':
                continue
            return False
    return True

def fetch_pypi_versions(package_name: str):
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            releases = list(data.get("releases", {}).keys())
            latest_stable = data.get("info", {}).get("version", "")
            return releases, latest_stable
    except Exception:
        return [], ""

def get_installed_packages():
    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(proc.stdout)
        return {item["name"].lower(): item["version"] for item in data}
    except Exception:
        return {}

def parse_requirements_file(path: Path):
    packages = []
    if not path.exists():
        return packages
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-r"):
                continue
            name = re.split(r'[<>=~]', line)[0].strip()
            if name:
                packages.append(name)
    return packages

def main():
    # script is in .agents/skills/check-updates/scripts/check_updates.py
    root = Path(__file__).resolve().parents[4]
    req_file = root / "requirements.txt"
    req_dev_file = root / "requirements-dev.txt"

    direct_pkgs = parse_requirements_file(req_file)
    dev_pkgs = parse_requirements_file(req_dev_file)
    all_target_pkgs = []
    seen = set()
    for p in direct_pkgs + dev_pkgs:
        low = p.lower()
        if low not in seen:
            seen.add(low)
            all_target_pkgs.append(p)

    installed = get_installed_packages()

    print("Checking updates for job-filter dependencies against PyPI...\n")
    print(f"{'Package':<22} | {'Current':<12} | {'Latest Stable':<15} | {'Status':<15}")
    print("-" * 72)

    has_updates = False
    for pkg in all_target_pkgs:
        curr = installed.get(pkg.lower(), "not installed")
        releases, latest_info = fetch_pypi_versions(pkg)

        if not latest_info and not releases:
            print(f"{pkg:<22} | {curr:<12} | {'Unknown':<15} | {'Error':<15}")
            continue

        stables = [r for r in releases if is_stable(r)]
        if stables:
            stables.sort(key=cmp_to_key(compare_versions))
            latest_stable = stables[-1]
        else:
            latest_stable = latest_info

        if curr == "not installed":
            status = "Missing"
        elif curr == latest_stable:
            status = "Up-to-date"
        elif compare_versions(latest_stable, curr) > 0:
            status = "Update Avail"
            has_updates = True
        else:
            status = "Up-to-date"

        print(f"{pkg:<22} | {curr:<12} | {latest_stable:<15} | {status:<15}")

    print("-" * 72)
    return 0

if __name__ == "__main__":
    sys.exit(main())
