"""分析テンプレートデータシードスクリプト。

validation.ymlとdummy/chart/*.jsonからデータを読み込み、
データベースにインポートします。

使用方法:
    $ cd C:/developments/genai-app-docs
    $ uv run python scripts/seed_templates.py

    オプション:
        --clear: 既存データをクリアしてから新規追加（デフォルト: True）
        --no-clear: 既存データを残して追加のみ

前提条件:
    - PostgreSQLが起動していること
    - Alembicマイグレーションが適用されていること（alembic upgrade head）
    - .envファイルが設定されていること
"""

import argparse
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.utils.template_seeder import seed_templates  # noqa: E402


async def main(clear_existing: bool = True):
    """メイン処理。

    Args:
        clear_existing (bool): 既存データをクリアするか
    """
    print("=" * 60)
    print("分析テンプレートデータシード")
    print("=" * 60)

    if clear_existing:
        print("⚠️  既存データをクリアしてから新規追加します")
    else:
        print("📝 既存データを残して追加のみ行います")

    print()

    try:
        async with AsyncSessionLocal() as db:
            print("🔄 データをインポートしています...")
            result = await seed_templates(db, clear_existing=clear_existing)

            print()
            print("=" * 60)
            print("✅ インポート完了")
            print("=" * 60)
            print(f"📊 テンプレート作成数: {result['templates_created']}")
            print(f"📈 チャート作成数: {result['charts_created']}")

            if clear_existing:
                print(f"🗑️  テンプレート削除数: {result['templates_deleted']}")
                print(f"🗑️  チャート削除数: {result['charts_deleted']}")

            print()
            print("💾 データベースに正常に保存されました")

    except FileNotFoundError as e:
        print()
        print("=" * 60)
        print("❌ エラー: ファイルが見つかりません")
        print("=" * 60)
        print(f"   {e}")
        sys.exit(1)

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ エラーが発生しました")
        print("=" * 60)
        print(f"   {type(e).__name__}: {e}")
        import traceback

        print()
        print("詳細:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="分析テンプレートデータをデータベースにシードします",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="既存データをクリアせずに追加のみ行う",
    )

    args = parser.parse_args()

    asyncio.run(main(clear_existing=not args.no_clear))
