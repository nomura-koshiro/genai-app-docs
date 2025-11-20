"""開発環境用の管理者ユーザーをセットアップするスクリプト。

このスクリプトは開発モード認証用の管理者ユーザーを作成または更新します。

主な機能:
    - ユーザーが存在しない場合: 新規作成 + SystemAdminロール付与
    - ユーザーが存在する場合: SystemAdminロールを追加（必要な場合のみ）

使用方法:
    uv run python scripts/setup_dev_admin.py

実行タイミング:
    - 開発環境の初回セットアップ時
    - データベースをリセットした後
    - 管理者専用エンドポイントをテストする前

環境変数:
    DEV_MOCK_USER_OID: 開発ユーザーのAzure Object ID (デフォルト: dev-azure-oid-12345)
    DEV_MOCK_USER_EMAIL: 開発ユーザーのメールアドレス (デフォルト: dev.user@example.com)
    DEV_MOCK_USER_NAME: 開発ユーザーの表示名 (デフォルト: Development User)
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.services.user_account.user_account import UserAccountService  # noqa: E402


async def setup_dev_admin():
    """開発環境用の管理者ユーザーをセットアップします。"""
    print("=" * 60)
    print("開発管理者セットアップ")
    print("=" * 60)
    print()

    # 環境変数から開発ユーザー情報を取得
    dev_azure_oid = settings.DEV_MOCK_USER_OID
    dev_email = settings.DEV_MOCK_USER_EMAIL
    dev_name = settings.DEV_MOCK_USER_NAME

    print("対象ユーザー:")
    print(f"  Azure OID: {dev_azure_oid}")
    print(f"  Email: {dev_email}")
    print(f"  Display Name: {dev_name}")
    print()

    db_gen = get_db()
    db = await db_gen.__anext__()

    try:
        user_service = UserAccountService(db)

        # ユーザーを取得または作成（既存ロールは保持）
        user = await user_service.get_or_create_by_azure_oid(
            azure_oid=dev_azure_oid,
            email=dev_email,
            display_name=dev_name,
            roles=None,  # 既存ロールを保持
        )

        print("取得/作成後:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Display Name: {user.display_name}")
        print(f"  現在のRoles: {user.roles}")
        print()

        # SystemAdminロールを確実に付与
        if "SystemAdmin" not in user.roles:
            print("SystemAdminロールを追加中...")
            user.roles = ["SystemAdmin", "User"]
            await db.commit()
            await db.refresh(user)
            print("[SUCCESS] SystemAdminロールを追加しました！")
        else:
            print("[INFO] 既にSystemAdminロールが付与されています")

        print()
        print("最終状態:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Display Name: {user.display_name}")
        print(f"  Roles: {user.roles}")
        print(f"  Updated At: {user.updated_at}")
        print("=" * 60)

    except Exception as e:
        await db.rollback()
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(setup_dev_admin())
