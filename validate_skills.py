#!/usr/bin/env python3
"""validate_skills.py - 检查所有 SKILL.md 是否符合 Agent Skills spec。

验证项:
1. YAML frontmatter 存在
2. name 字段：(a) 存在 (b) 与目录名一致 (c) 仅小写字母/数字/连字符 (d) 1-64 字符
3. description 字段：(a) 存在 (b) 1-1024 字符
4. SKILL.md ≤ 500 行

用法:
    python validate_skills.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILLS_ROOT = Path("skills")
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def validate_skill(skill_md: Path) -> list[str]:
    errors: list[str] = []
    if not skill_md.exists():
        return [f"{skill_md}: file not found"]

    text = skill_md.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_PATTERN.match(text)
    if not fm_match:
        return [f"{skill_md}: missing YAML frontmatter (must start with '---' line)"]

    fm = fm_match.group(1)

    # name
    name_m = re.search(r"^name:\s*(\S+)\s*$", fm, re.MULTILINE)
    if not name_m:
        errors.append("missing 'name' field")
    else:
        name = name_m.group(1).strip().strip('"').strip("'")
        dir_name = skill_md.parent.name
        if name != dir_name:
            errors.append(f"name {name!r} != directory {dir_name!r}")
        if not NAME_PATTERN.match(name):
            errors.append(
                f"name {name!r} invalid (must be lowercase alphanumeric + hyphens; "
                "cannot start/end with hyphen or have consecutive --)"
            )
        if len(name) > 64:
            errors.append(f"name {name!r} too long ({len(name)} > 64)")

    # description
    desc_m = re.search(r"^description:\s*(.+?)(?=^[a-z_]+:\s|\Z)", fm, re.MULTILINE | re.DOTALL)
    if not desc_m:
        errors.append("missing 'description' field")
    else:
        desc = " ".join(desc_m.group(1).split())
        if len(desc) < 20:
            errors.append(f"description too short ({len(desc)} < 20 chars)")
        if len(desc) > 1024:
            errors.append(f"description too long ({len(desc)} > 1024 chars)")

    # size
    line_count = len(text.splitlines())
    if line_count > 500:
        errors.append(f"SKILL.md too long ({line_count} > 500 lines); move detail to references/")

    return errors


def main() -> int:
    if not SKILLS_ROOT.exists():
        print(f"error: {SKILLS_ROOT}/ directory not found", file=sys.stderr)
        return 1

    skill_files = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
    if not skill_files:
        print(f"warn: no SKILL.md files under {SKILLS_ROOT}/", file=sys.stderr)
        return 1

    total_errors: list[str] = []
    for sf in skill_files:
        errors = validate_skill(sf)
        if errors:
            for e in errors:
                total_errors.append(f"{sf.parent.name}: {e}")
        else:
            print(f"OK    {sf.parent.name}")

    if total_errors:
        print("\nFAILED", file=sys.stderr)
        for e in total_errors:
            print(f"  ERROR  {e}", file=sys.stderr)
        return 1

    print(f"\nvalidated {len(skill_files)} skill(s) successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
