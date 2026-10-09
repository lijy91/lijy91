#!/usr/bin/env python3
"""
Generate README tables from projects.yaml

This script reads the projects.yaml file and generates markdown tables
for both English (README.md) and Chinese (README-ZH.md) versions.

The tables include:
- Project name with GitHub link
- Stars badge
- Forks badge
- Issues badge
- Pull requests badge

Usage:
    python3 generate_readme.py           - Display generated tables
    python3 generate_readme.py --update  - Update README files in place

projects.yaml format (flat key/value lists, no external YAML dependency):

    categories:
      - id: apps
        name: Apps
        name_zh: 应用
        description: ...
        description_zh: ...
        collapsed: true        # optional: wrap the table in <details>
        summary: Show all      # optional: <summary> text when collapsed
        summary_zh: 展开
    entities:
      - name: project          # or pub_id: for pub.dev packages
        github_id: owner/repo
        category: apps
"""

from typing import Dict, List, Any


def load_yaml(file_path: str) -> Dict[str, Any]:
    """Load the project config (minimal line-based parser for our specific format)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    data: Dict[str, Any] = {'categories': [], 'entities': []}
    section = None
    current: Dict[str, str] = {}

    def flush():
        nonlocal current
        if section and current:
            data[section].append(current)
        current = {}

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Top-level section header, e.g. "categories:" / "entities:"
        if not line.startswith(' ') and stripped.endswith(':'):
            flush()
            key = stripped[:-1]
            section = key if key in data else None
            continue

        if section is None:
            continue

        # New list item: "  - key: value"
        if stripped.startswith('- '):
            flush()
            stripped = stripped[2:].strip()

        if ':' not in stripped:
            continue
        key, _, value = stripped.partition(':')
        current[key.strip()] = value.strip()

    flush()

    data['entities'] = [e for e in data['entities'] if e.get('github_id')]
    data['categories'] = [c for c in data['categories'] if c.get('id')]
    return data


def get_project_name(entity: Dict[str, Any]) -> str:
    """Get project name from entity (pub_id or name)"""
    return entity.get('pub_id') or entity.get('name', '')


def generate_table_row(entity: Dict[str, Any]) -> str:
    """Generate a single table row for an entity"""
    project_name = get_project_name(entity)
    github_id = entity['github_id']

    row = f"| [{project_name}](https://github.com/{github_id}) "
    row += f"| [![Stars](https://img.shields.io/github/stars/{github_id})](https://github.com/{github_id}/stargazers) "
    row += f"| [![Forks](https://img.shields.io/github/forks/{github_id})](https://github.com/{github_id}/network/members) "
    row += f"| [![Issues](https://img.shields.io/github/issues/{github_id})](https://github.com/{github_id}/issues) "
    row += f"| [![Pull requests](https://img.shields.io/github/issues-pr/{github_id})](https://github.com/{github_id}/pulls) |"

    return row


TABLE_HEADERS = {
    'en': (
        "| 📂 Projects | ⭐ Stars | 🍴 Forks | 🚧 Issues | 📬 Pull requests |\n"
        "| ----------- | -------- | -------- | --------- | ---------------- |\n"
    ),
    'zh': (
        "| 📂 项目 | ⭐ Stars | 🍴 Forks | 🚧 Issues | 📬 Pull requests |\n"
        "| ------- | -------- | -------- | --------- | ---------------- |\n"
    ),
}


def generate_category_table(category: Dict[str, Any], entities: List[Dict[str, Any]], lang: str = 'en') -> str:
    """Generate a complete table for a category"""
    category_entities = [e for e in entities if e.get('category') == category['id']]

    if not category_entities:
        return ""

    category_entities.sort(key=lambda e: get_project_name(e).lower())

    table = TABLE_HEADERS[lang]
    for entity in category_entities:
        table += generate_table_row(entity) + "\n"

    return table


def localized(category: Dict[str, Any], key: str, lang: str) -> str:
    """Pick the localized field (e.g. name_zh) and fall back to the default one."""
    if lang != 'en':
        value = category.get(f'{key}_{lang}')
        if value:
            return value
    return category.get(key, '')


def generate_all_tables(categories: List[Dict[str, Any]], entities: List[Dict[str, Any]], lang: str = 'en') -> str:
    """Generate all tables for all categories"""
    output = []

    for category in categories:
        table = generate_category_table(category, entities, lang)
        if not table:
            continue

        output.append(f"### {localized(category, 'name', lang)}\n")

        description = localized(category, 'description', lang)
        if description:
            output.append(f"{description}\n")

        if category.get('collapsed', '').lower() == 'true':
            summary = localized(category, 'summary', lang) or 'Show all'
            output.append(f"<details>\n<summary>{summary}</summary>\n")
            output.append(table)
            output.append("</details>\n")
        else:
            output.append(table)

    return '\n'.join(output)


def update_readme_file(readme_path: str, new_content: str, start_marker: str, end_marker: str) -> bool:
    """Update README file between markers"""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            print(f"Warning: Markers not found in {readme_path}")
            print(f"Please add the following markers to your README:")
            print(f"  {start_marker}")
            print(f"  {end_marker}")
            return False

        before = content[:start_idx + len(start_marker)]
        after = content[end_idx:]
        new_readme = before + '\n' + new_content + '\n' + after

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme)

        return True
    except Exception as e:
        print(f"Error updating {readme_path}: {e}")
        return False


def main():
    """Main function"""
    import sys

    START_MARKER = '<!-- AUTO-GENERATED:START -->'
    END_MARKER = '<!-- AUTO-GENERATED:END -->'

    update_files = '--update' in sys.argv or '-u' in sys.argv
    show_help = '--help' in sys.argv or '-h' in sys.argv

    if show_help:
        print("README Generator - Generate tables from projects.yaml")
        print("\nUsage:")
        print("  python3 generate_readme.py           - Display generated tables")
        print("  python3 generate_readme.py --update  - Update README files automatically")
        print("  python3 generate_readme.py -u        - Same as --update")
        print("  python3 generate_readme.py --help    - Show this help")
        print("\nMarkers:")
        print(f"  Start: {START_MARKER}")
        print(f"  End:   {END_MARKER}")
        print("\nAdd these markers to your README.md and README-ZH.md files")
        print("to enable automatic updates.")
        return

    data = load_yaml('projects.yaml')

    categories = data.get('categories', [])
    entities = data.get('entities', [])

    en_tables = generate_all_tables(categories, entities, 'en')
    zh_tables = generate_all_tables(categories, entities, 'zh')

    if update_files:
        print("Updating README files...\n")
        print("=" * 80)

        if update_readme_file('README.md', en_tables, START_MARKER, END_MARKER):
            print("✓ README.md updated successfully!")
        else:
            print("✗ Failed to update README.md")

        print()

        if update_readme_file('README-ZH.md', zh_tables, START_MARKER, END_MARKER):
            print("✓ README-ZH.md updated successfully!")
        else:
            print("✗ Failed to update README-ZH.md")

        print("\n" + "=" * 80)
        print("\nREADME files have been updated!")
    else:
        print("Generating tables from projects.yaml...\n")
        print("=" * 80)

        print("\n### ENGLISH VERSION ###\n")
        print(en_tables)

        print("\n" + "=" * 80)

        print("\n### CHINESE VERSION ###\n")
        print(zh_tables)

        print("\n" + "=" * 80)
        print("\nTables generated successfully!")
        print("\nTo automatically update README files, run:")
        print("  python3 generate_readme.py --update")
        print("\nOr copy the tables above and paste them into README.md and README-ZH.md")


if __name__ == '__main__':
    main()
