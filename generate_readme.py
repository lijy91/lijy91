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
    python3 generate_readme.py

The script will output the generated tables to the console.
Copy the tables and paste them into the appropriate README files.
"""

import re
from typing import Dict, List, Any


def load_yaml(file_path: str) -> Dict[str, Any]:
    """Load YAML configuration file (simple parser for our specific format)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {'categories': [], 'entities': []}
    
    # Parse categories
    categories_match = re.search(r'categories:\s*\n((?:  -.*\n(?:    .*\n)*)*)', content)
    if categories_match:
        categories_text = categories_match.group(1)
        # Split by category markers (lines starting with "  - id:")
        category_blocks = re.split(r'\n(?=  - id:)', categories_text)
        
        for block in category_blocks:
            if not block.strip():
                continue
            
            category = {}
            
            # Extract id
            id_match = re.search(r'id:\s*(\S+)', block)
            if id_match:
                category['id'] = id_match.group(1)
            
            # Extract name
            name_match = re.search(r'name:\s*(.+?)(?=\n|$)', block)
            if name_match:
                category['name'] = name_match.group(1).strip()
            
            # Extract description
            desc_match = re.search(r'description:\s*(.+?)(?=\n  |$)', block, re.DOTALL)
            if desc_match:
                category['description'] = desc_match.group(1).strip()
            
            if category.get('id'):
                data['categories'].append(category)
    
    # Parse entities
    entities_match = re.search(r'entities:\s*\n((?:  #.*\n|  -.*\n(?:    .*\n)*)*)', content, re.DOTALL)
    if entities_match:
        entities_text = entities_match.group(1)
        # Split by entity markers (lines starting with "  - ")
        entity_blocks = re.split(r'\n(?=  - )', entities_text)
        
        for block in entity_blocks:
            if not block.strip() or block.strip().startswith('#'):
                continue
            
            entity = {}
            
            # Extract pub_id
            pub_id_match = re.search(r'pub_id:\s*(\S+)', block)
            if pub_id_match:
                entity['pub_id'] = pub_id_match.group(1)
            
            # Extract name
            name_match = re.search(r'name:\s*(\S+)', block)
            if name_match:
                entity['name'] = name_match.group(1)
            
            # Extract github_id
            github_id_match = re.search(r'github_id:\s*(\S+)', block)
            if github_id_match:
                entity['github_id'] = github_id_match.group(1)
            
            # Extract category
            category_match = re.search(r'category:\s*(\S+)', block)
            if category_match:
                entity['category'] = category_match.group(1)
            
            if entity.get('github_id'):
                data['entities'].append(entity)
    
    return data


def get_project_name(entity: Dict[str, Any]) -> str:
    """Get project name from entity (pub_id or name)"""
    return entity.get('pub_id') or entity.get('name', '')


def generate_table_row(entity: Dict[str, Any]) -> str:
    """Generate a single table row for an entity"""
    project_name = get_project_name(entity)
    github_id = entity['github_id']
    
    # Generate markdown row with badges
    row = f"| [{project_name}](https://github.com/{github_id}) "
    row += f"| [![Stars](https://img.shields.io/github/stars/{github_id})](https://github.com/{github_id}/stargazers) "
    row += f"| [![Forks](https://img.shields.io/github/forks/{github_id})](https://github.com/{github_id}/network/members) "
    row += f"| [![Issues](https://img.shields.io/github/issues/{github_id})](https://github.com/{github_id}/issues) "
    row += f"| [![Pull requests](https://img.shields.io/github/issues-pr/{github_id})](https://github.com/{github_id}/pulls) |"
    
    return row


def generate_category_table(category: Dict[str, Any], entities: List[Dict[str, Any]]) -> str:
    """Generate a complete table for a category"""
    # Filter entities for this category
    category_entities = [e for e in entities if e.get('category') == category['id']]
    
    if not category_entities:
        return ""
    
    # Sort entities by project name
    category_entities.sort(key=lambda e: get_project_name(e).lower())
    
    # Table header
    table = "| 📂 Projects | ⭐ Stars | 🍴 Forks | 🚧 Issues | 📬 Pull requests |\n"
    table += "| ----------- | -------- | -------- | --------- | ---------------- |\n"
    
    # Table rows
    for entity in category_entities:
        table += generate_table_row(entity) + "\n"
    
    return table


def generate_category_table_zh(category: Dict[str, Any], entities: List[Dict[str, Any]]) -> str:
    """Generate a complete table for a category (Chinese version)"""
    # Filter entities for this category
    category_entities = [e for e in entities if e.get('category') == category['id']]
    
    if not category_entities:
        return ""
    
    # Sort entities by project name
    category_entities.sort(key=lambda e: get_project_name(e).lower())
    
    # Table header (Chinese)
    table = "| 📂 项目 | ⭐ Stars | 🍴 Forks | 🚧 Issues | 📬 Pull requests |\n"
    table += "| ------- | -------- | -------- | --------- | ---------------- |\n"
    
    # Table rows
    for entity in category_entities:
        table += generate_table_row(entity) + "\n"
    
    return table


def generate_all_tables(categories: List[Dict[str, Any]], entities: List[Dict[str, Any]], lang: str = 'en') -> str:
    """Generate all tables for all categories"""
    output = []
    
    for category in categories:
        category_entities = [e for e in entities if e.get('category') == category['id']]
        if not category_entities:
            continue
        
        output.append(f"#### {category['name']}\n")
        
        # Add description if available
        if category.get('description'):
            output.append(f"{category['description']}\n")
        
        if lang == 'zh':
            table = generate_category_table_zh(category, entities)
        else:
            table = generate_category_table(category, entities)
        
        if table:
            output.append(table)
    
    return '\n'.join(output)


def update_readme_file(readme_path: str, new_content: str, start_marker: str, end_marker: str) -> bool:
    """Update README file between markers"""
    try:
        # Read the current README
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the markers
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            print(f"Warning: Markers not found in {readme_path}")
            print(f"Please add the following markers to your README:")
            print(f"  {start_marker}")
            print(f"  {end_marker}")
            return False
        
        # Replace content between markers
        before = content[:start_idx + len(start_marker)]
        after = content[end_idx:]
        new_readme = before + '\n' + new_content + '\n' + after
        
        # Write back to file
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme)
        
        return True
    except Exception as e:
        print(f"Error updating {readme_path}: {e}")
        return False


def main():
    """Main function"""
    import sys
    
    # Markers for auto-generation
    START_MARKER = '<!-- AUTO-GENERATED:START -->'
    END_MARKER = '<!-- AUTO-GENERATED:END -->'
    
    # Parse command line arguments
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
    
    # Load YAML data
    data = load_yaml('projects.yaml')
    
    categories = data.get('categories', [])
    entities = data.get('entities', [])
    
    # Generate tables
    en_tables = generate_all_tables(categories, entities, 'en')
    zh_tables = generate_all_tables(categories, entities, 'zh')
    
    if update_files:
        print("Updating README files...\n")
        print("=" * 80)
        
        # Update English README
        if update_readme_file('README.md', en_tables, START_MARKER, END_MARKER):
            print("✓ README.md updated successfully!")
        else:
            print("✗ Failed to update README.md")
        
        print()
        
        # Update Chinese README
        if update_readme_file('README-ZH.md', zh_tables, START_MARKER, END_MARKER):
            print("✓ README-ZH.md updated successfully!")
        else:
            print("✗ Failed to update README-ZH.md")
        
        print("\n" + "=" * 80)
        print("\nREADME files have been updated!")
    else:
        print("Generating tables from projects.yaml...\n")
        print("=" * 80)
        
        # Display English version
        print("\n### ENGLISH VERSION ###\n")
        print(en_tables)
        
        print("\n" + "=" * 80)
        
        # Display Chinese version
        print("\n### CHINESE VERSION ###\n")
        print(zh_tables)
        
        print("\n" + "=" * 80)
        print("\nTables generated successfully!")
        print("\nTo automatically update README files, run:")
        print("  python3 generate_readme.py --update")
        print("\nOr copy the tables above and paste them into README.md and README-ZH.md")


if __name__ == '__main__':
    main()

