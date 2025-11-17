"""Driver Tree PKLファイルの内容確認スクリプト。

camp-backend-code-analysisから移行するデータの構造を確認します。
"""

import pickle
from pathlib import Path
from pprint import pprint

# PKLファイルのパス
CATEGORIES_PKL = Path("C:/developments/camp-backend-code-analysis/dev_db/local_blob_storage/driver-tree/driver_tree_categories.pkl")
TREES_PKL = Path("C:/developments/camp-backend-code-analysis/dev_db/local_blob_storage/driver-tree/driver_trees.pkl")


def inspect_categories():
    """カテゴリーデータを確認します。"""
    print("=" * 80)
    print("driver_tree_categories.pkl の内容:")
    print("=" * 80)

    if not CATEGORIES_PKL.exists():
        print(f"ファイルが見つかりません: {CATEGORIES_PKL}")
        return

    with open(CATEGORIES_PKL, "rb") as f:
        categories = pickle.load(f)

    print(f"\nデータ型: {type(categories)}")
    print(f"要素数: {len(categories) if hasattr(categories, '__len__') else 'N/A'}")

    if isinstance(categories, dict):
        print("\nキー一覧:")
        for key in list(categories.keys())[:5]:  # 最初の5つのキーを表示
            print(f"  - {key}")

        # 最初の要素のサンプルを表示
        if categories:
            first_key = list(categories.keys())[0]
            print(f"\nサンプルデータ（キー: {first_key}）:")
            pprint(categories[first_key], depth=3)

    elif isinstance(categories, list):
        print("\nリストの最初の要素:")
        if categories:
            pprint(categories[0], depth=3)


def inspect_trees():
    """ツリーデータを確認します。"""
    print("\n" + "=" * 80)
    print("driver_trees.pkl の内容:")
    print("=" * 80)

    if not TREES_PKL.exists():
        print(f"ファイルが見つかりません: {TREES_PKL}")
        return

    with open(TREES_PKL, "rb") as f:
        trees = pickle.load(f)

    print(f"\nデータ型: {type(trees)}")
    print(f"要素数: {len(trees) if hasattr(trees, '__len__') else 'N/A'}")

    if isinstance(trees, dict):
        print("\nキー一覧:")
        for key in list(trees.keys())[:5]:  # 最初の5つのキーを表示
            print(f"  - {key}")

        # 最初の要素のサンプルを表示
        if trees:
            first_key = list(trees.keys())[0]
            print(f"\nサンプルデータ（キー: {first_key}）:")
            pprint(trees[first_key], depth=3)

    elif isinstance(trees, list):
        print("\nリストの最初の要素:")
        if trees:
            pprint(trees[0], depth=3)


if __name__ == "__main__":
    inspect_categories()
    inspect_trees()
