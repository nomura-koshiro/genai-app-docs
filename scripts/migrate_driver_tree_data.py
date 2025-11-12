"""Driver Treeデータ移行スクリプト。

camp-backend-code-analysisのPKLファイルから、
genai-app-docsのPostgreSQLデータベースにデータを移行します。

使用方法:
    $ cd C:/developments/genai-app-docs/src
    $ python -m scripts.migrate_driver_tree_data

前提条件:
    - PostgreSQLが起動していること
    - Alembicマイグレーションが適用されていること（alembic upgrade head）
    - .envファイルが設定されていること
"""

import asyncio
import pickle
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(project_root))

from sqlalchemy import text  # noqa: E402

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models import DriverTreeCategory  # noqa: E402

# PKLファイルのパス
CATEGORIES_PKL = Path("C:/developments/camp-backend-code-analysis/dev_db/local_blob_storage/driver-tree/driver_tree_categories.pkl")
TREES_PKL = Path("C:/developments/camp-backend-code-analysis/dev_db/local_blob_storage/driver-tree/driver_trees.pkl")


async def load_pkl_data():
    """PKLファイルからデータを読み込みます。

    Returns:
        tuple: (categories, driver_trees) のタプル
    """
    print("📂 PKLファイルを読み込んでいます...")

    if not CATEGORIES_PKL.exists():
        raise FileNotFoundError(f"カテゴリーファイルが見つかりません: {CATEGORIES_PKL}")

    if not TREES_PKL.exists():
        raise FileNotFoundError(f"ツリーファイルが見つかりません: {TREES_PKL}")

    with open(CATEGORIES_PKL, "rb") as f:
        categories = pickle.load(f)

    with open(TREES_PKL, "rb") as f:
        driver_trees = pickle.load(f)

    print(f"✅ カテゴリー数: {len(categories)}")
    print(f"✅ ツリータイプ数: {len(driver_trees)}")

    return categories, driver_trees


def transform_data(categories: dict, driver_trees: dict) -> list[dict]:
    """PKLデータをDriverTreeCategoryモデル用に変換します。

    Args:
        categories: カテゴリー辞書 {業種大分類: {業種: [ツリータイプ, ...]}}
        driver_trees: ツリー辞書 {ツリータイプ: {KPI: [数式, ...]}}

    Returns:
        list[dict]: DriverTreeCategory用のデータリスト
    """
    print("\n🔄 データを変換しています...")

    result = []

    for industry_class, industries in categories.items():
        for industry, tree_types in industries.items():
            for tree_type in tree_types:
                # このツリータイプのKPIと数式を取得
                if tree_type not in driver_trees:
                    print(f"⚠️  警告: ツリータイプ '{tree_type}' が driver_trees に存在しません")
                    continue

                kpi_formulas = driver_trees[tree_type]

                for kpi, formulas in kpi_formulas.items():
                    # NaNやNoneを除外
                    clean_formulas = [f for f in formulas if f and isinstance(f, str)]

                    if not clean_formulas:
                        print(f"⚠️  警告: {industry_class}/{industry}/{tree_type}/{kpi} の数式が空です")
                        continue

                    result.append(
                        {
                            "industry_class": industry_class,
                            "industry": industry,
                            "tree_type": tree_type,
                            "kpi": kpi,
                            "formulas": clean_formulas,
                            "metadata": {},
                        }
                    )

    print(f"✅ 変換完了: {len(result)} 件のレコード")
    return result


async def migrate_to_database(records: list[dict]):
    """変換したデータをデータベースに挿入します。

    Args:
        records: DriverTreeCategory用のデータリスト
    """
    print("\n💾 データベースに挿入しています...")

    async with AsyncSessionLocal() as session:
        # 既存のデータを削除（再実行時のため）
        await session.execute(text("DELETE FROM driver_tree_categories"))
        print("🗑️  既存データを削除しました")

        # 新しいデータを挿入
        for i, record in enumerate(records, 1):
            category = DriverTreeCategory(**record)
            session.add(category)

            if i % 10 == 0:
                print(f"  ... {i}/{len(records)} 件挿入済み")

        await session.commit()
        print(f"✅ {len(records)} 件のレコードを挿入しました")


async def main():
    """メイン処理。"""
    print("=" * 80)
    print("Driver Tree データ移行スクリプト")
    print("=" * 80)

    try:
        # 1. PKLファイルを読み込む
        categories, driver_trees = await load_pkl_data()

        # 2. データを変換する
        records = transform_data(categories, driver_trees)

        if not records:
            print("❌ 変換可能なデータがありません")
            return

        # 3. データベースに挿入する
        await migrate_to_database(records)

        print("\n" + "=" * 80)
        print("✅ 移行完了！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
