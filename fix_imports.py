#!/usr/bin/env python3
"""深いインポートを浅いインポートに修正するスクリプト"""

import re
import sys
from pathlib import Path

# 修正対象のディレクトリ
TARGET_DIRS = [
    "src/app/services",
    "src/app/repositories",
    "src/app/api/routes",
    "tests",
]

# 除外するファイル
EXCLUDE_FILES = {
    "__init__.py",
}

# 修正パターン（深いインポート -> 浅いインポート）
PATTERNS = [
    # Models
    (r'^from app\.models\.(\w+)\.(\w+) import (.+)$', r'from app.models import \3'),
    # Repositories
    (r'^from app\.repositories\.(\w+)\.(\w+) import (.+)$', r'from app.repositories import \3'),
    # Services
    (r'^from app\.services\.(\w+)\.(\w+) import (.+)$', r'from app.services import \3'),
    # Schemas (Service層での使用のみ)
    (r'^from app\.schemas\.(\w+)\.(\w+) import (.+)$', r'from app.schemas import \3'),
]

def should_skip_file(filepath: Path) -> bool:
    """ファイルをスキップするか判定"""
    # __init__.py はスキップ
    if filepath.name in EXCLUDE_FILES:
        return True

    # app/schemas/配下の実装ファイルはスキップ (Schema間の相互参照を維持)
    if "app/schemas/" in str(filepath) and not ("app/services/" in str(filepath) or "app/api/" in str(filepath)):
        # schemas配下の __init__.py 以外の実装ファイルはスキップ
        if "src/app/schemas/" in str(filepath).replace("\\", "/"):
            return True

    # app/models/配下の実装ファイルはスキップ (Model間の相互参照を維持)
    if "src/app/models/" in str(filepath).replace("\\", "/") and filepath.name != "__init__.py":
        return True

    return False

def fix_imports_in_file(filepath: Path) -> tuple[bool, int]:
    """ファイル内のインポートを修正"""
    if should_skip_file(filepath):
        return False, 0

    try:
        content = filepath.read_text(encoding="utf-8")
        original_content = content
        lines = content.split("\n")
        modified_count = 0

        new_lines = []
        for line in lines:
            # TYPE_CHECKING内のインポートはスキップ
            if "TYPE_CHECKING" in line:
                new_lines.append(line)
                continue

            modified_line = line
            for pattern, replacement in PATTERNS:
                match = re.match(pattern, line)
                if match:
                    modified_line = re.sub(pattern, replacement, line)
                    if modified_line != line:
                        modified_count += 1
                        break

            new_lines.append(modified_line)

        if modified_count > 0:
            new_content = "\n".join(new_lines)
            filepath.write_text(new_content, encoding="utf-8")
            return True, modified_count

        return False, 0

    except Exception as e:
        print(f"エラー: {filepath}: {e}", file=sys.stderr)
        return False, 0

def main():
    """メイン処理"""
    root = Path("C:/developments/genai-app-docs")

    total_files = 0
    modified_files = 0
    total_modifications = 0

    for target_dir in TARGET_DIRS:
        dir_path = root / target_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            if should_skip_file(py_file):
                continue

            total_files += 1
            was_modified, mod_count = fix_imports_in_file(py_file)

            if was_modified:
                modified_files += 1
                total_modifications += mod_count
                print(f"✓ {py_file.relative_to(root)} ({mod_count}箇所)")

    print("\n=== 修正完了 ===")
    print(f"対象ファイル数: {total_files}")
    print(f"修正したファイル数: {modified_files}")
    print(f"修正箇所数: {total_modifications}")

if __name__ == "__main__":
    main()
