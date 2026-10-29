#!/usr/bin/env python3
"""Fail when the skill folders, catalog, and plugin list disagree."""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
NEEDLE = "mcp" + "Servers"


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def yaml_name(skill_md: Path) -> str:
    text = skill_md.read_text()
    if not text.startswith("---"):
        fail(f"{skill_md} has no YAML frontmatter")
    end = text.find("\n---", 3)
    front = text[3:end]
    for line in front.splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    fail(f"{skill_md} has no YAML name")


def allowed(url):
    if not isinstance(url, str) or not url.strip():
        return False
    parts = urlparse(url.strip())
    return parts.scheme == "https" and parts.hostname == "markzware.com"


def normalize(path):
    return str(path).removeprefix("./").rstrip("/")


def collect_skills(value, found):
    if isinstance(value, dict):
        skills = value.get("skills")
        if isinstance(skills, str):
            found.append(normalize(skills))
        elif isinstance(skills, list):
            found.extend(normalize(item) for item in skills if isinstance(item, str))
        for item in value.values():
            collect_skills(item, found)
    elif isinstance(value, list):
        for item in value:
            collect_skills(item, found)


def main():
    skill_dirs = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    if not skill_dirs:
        fail("no skill folders")
    folder_names = set()
    for folder in skill_dirs:
        if (folder / "__pycache__").exists() or (folder / "config.json").exists():
            fail(f"{folder.name} contains __pycache__ or config.json")
        if list(folder.rglob("*.pyc")) or list(folder.rglob("__pycache__")):
            fail(f"{folder.name} contains __pycache__ or a .pyc file")
        name = yaml_name(folder / "SKILL.md")
        if name != folder.name:
            fail(f"{folder.name} YAML name is {name}")
        folder_names.add(folder.name)

    catalog = json.loads((ROOT / "skills.json").read_text())
    ids = {row["id"] for row in catalog["skills"]}
    if ids != folder_names:
        fail(f"catalog ids {sorted(ids)} differ from folders {sorted(folder_names)}")
    for row in catalog["skills"]:
        if not allowed(row.get("tutorial_url")) or not allowed(row.get("zip_url")):
            fail(f"{row.get('id')} catalog URL is not https on markzware.com")

    listed = []
    for rel in (".claude-plugin/marketplace.json", ".codex-plugin/plugin.json"):
        collect_skills(json.loads((ROOT / rel).read_text()), listed)
    if set(listed) != {f"skills/{name}" for name in folder_names}:
        fail(f"plugin skill list {sorted(set(listed))} differs from folders")

    banned_name = "." + "mcp.json"
    for path in ROOT.rglob("*"):
        if path.name == banned_name or banned_name in path.parts:
            fail("repository contains a remote MCP config file")
        if path.is_file() and NEEDLE.encode() in path.read_bytes():
            fail(f"{path.relative_to(ROOT)} contains a remote MCP server entry")
    print("ok")


if __name__ == "__main__":
    main()
