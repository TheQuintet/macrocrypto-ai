#!/usr/bin/env python3
# Path: add_path_comments.py
"""
Add relative path comments to Python files (except __init__.py).

This script recursively finds all .py files in the current directory,
skips __init__.py files, and adds a comment at the top with the relative
path from the current directory.

Safe to run multiple times - will update existing comments without duplication.
"""

import os
import sys
import re
from pathlib import Path


def get_python_files(start_dir='.'):
    """
    Recursively find all Python files in the directory tree.
    Skips __init__.py files.
    """
    python_files = []
    
    for root, dirs, files in os.walk(start_dir):
        # Skip hidden directories and common virtual environment directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', 'virtualenv', '__pycache__']]
        
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                full_path = os.path.join(root, file)
                python_files.append(full_path)
    
    return python_files


def get_relative_path(filepath, start_dir='.'):
    """Get the relative path from start_dir to filepath."""
    abs_start = os.path.abspath(start_dir)
    abs_file = os.path.abspath(filepath)
    
    try:
        rel_path = os.path.relpath(abs_file, abs_start)
        return rel_path
    except ValueError:
        # Handle case where files are on different drives (Windows)
        return abs_file


def has_path_comment(content):
    """Check if the file already has a path comment."""
    lines = content.split('\n')
    
    # Check first non-empty line for path comment
    for line in lines:
        if line.strip():
            return line.strip().startswith('# Path:')
    
    return False


def remove_existing_path_comment(content):
    """
    Remove any existing path comment from the beginning of the file.
    Preserves shebang if present.
    """
    lines = content.split('\n')
    
    # Check if first line is shebang
    has_shebang = lines and lines[0].strip().startswith('#!')
    
    if has_shebang:
        # Check if second line is a path comment
        if len(lines) > 1 and lines[1].strip().startswith('# Path:'):
            # Remove the second line
            return lines[0] + '\n' + '\n'.join(lines[2:])
        return content
    else:
        # Check if first line is a path comment
        if lines and lines[0].strip().startswith('# Path:'):
            # Remove the first line
            return '\n'.join(lines[1:])
        return content


def add_path_comment(filepath, rel_path):
    """
    Add a path comment at the top of the file.
    Removes any existing path comment first to avoid duplicates.
    Returns True if modified, False if already has correct comment.
    """
    comment_line = f"# Path: {rel_path}"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the file is empty
        if not content.strip():
            # Write just the comment for empty files
            new_content = comment_line + '\n'
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Added to empty file: {rel_path}")
            return True
        
        # Check if the correct comment already exists
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and line.strip().startswith('# Path:'):
                if line.strip() == comment_line:
                    print(f"✓ Already up to date: {rel_path}")
                    return False
                break
        
        # Remove any existing path comment
        content = remove_existing_path_comment(content)
        
        # Add the new comment at the top
        # Check if file has shebang
        lines = content.split('\n')
        if lines and lines[0].strip().startswith('#!'):
            # Keep shebang as first line, insert comment after
            shebang = lines[0]
            rest = '\n'.join(lines[1:])
            # Remove any empty lines between shebang and content
            if rest and not rest.strip():
                new_content = shebang + '\n' + comment_line + '\n'
            else:
                new_content = shebang + '\n' + comment_line + '\n' + rest
        else:
            # Add comment at the very beginning
            if content and not content.startswith('\n'):
                new_content = comment_line + '\n' + content
            else:
                new_content = comment_line + '\n' + content.lstrip('\n')
        
        # Write the updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Updated: {rel_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing {rel_path}: {e}")
        return False


def preview_changes(python_files):
    """Preview what changes will be made without actually modifying files."""
    print("\n📋 Preview of changes to be made:\n")
    
    for filepath in python_files:
        rel_path = get_relative_path(filepath)
        print(f"  • {rel_path}")
        
        # Check current status
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if has_path_comment(content):
                print(f"    └─ Will update existing path comment")
            else:
                print(f"    └─ Will add new path comment")
        except:
            print(f"    └─ Error reading file")
    
    print()


def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Add relative path comments to Python files (except __init__.py)'
    )
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--dir', '-d',
        default='.',
        help='Target directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    current_dir = args.dir
    
    print("🔍 Finding Python files...")
    python_files = get_python_files(current_dir)
    
    if not python_files:
        print("No Python files found (excluding __init__.py).")
        return
    
    print(f"Found {len(python_files)} Python file(s) to process.\n")
    
    if args.preview:
        preview_changes(python_files)
        print("This was a preview. Run without --preview to apply changes.")
        return
    
    # Confirm before proceeding
    print(f"This will modify {len(python_files)} file(s).")
    response = input("Continue? (y/n): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        return
    
    print()
    modified_count = 0
    
    for filepath in python_files:
        rel_path = get_relative_path(filepath, current_dir)
        if add_path_comment(filepath, rel_path):
            modified_count += 1
    
    print(f"\n✅ Done! Modified {modified_count} file(s).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)