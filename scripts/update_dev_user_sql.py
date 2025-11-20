"""開発モードユーザーをSystemAdminに昇格するスクリプト（SQLAlchemy ORM使用）。

ユーザーが存在しない場合は自動作成し、SystemAdminロールを付与します。
既存ユーザーの場合は、SystemAdminロールを追加します。
"""

import asyncio
import sys
from pathlib import Path

from app.core.config import settings
from app.core.database import get_db
from app.services.user_account.user_account import UserAccountService

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def update_dev_user_roles():
    """開発ユーザーを取得または作成し、SystemAdminロールを付与します。"""
    print("=" * 60)
    print("開発モードユーザー昇格（get_or_create使用）")
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
    asyncio.run(update_dev_user_roles())
