"""Azure AD認証用ユーザーモデルのデータアクセスリポジトリ。

このモジュールは、Azure AD認証に対応したUserモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、Azure OID検索、メール検索、アクティブユーザー取得などの
ユーザー固有のクエリメソッドを追加しています。

主な機能:
    - Azure OIDによるユーザー検索（Azure AD認証時に使用）
    - メールアドレスによるユーザー検索
    - アクティブユーザーの一覧取得
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.user.user import UserRepository
    >>>
    >>> async with get_db() as db:
    ...     user_repo = UserRepository(db)
    ...     user = await user_repo.get_by_azure_oid("azure-oid-12345")
    ...     if user:
    ...         print(f"Found user: {user.email}")
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, uuid.UUID]):
    """Azure AD認証用Userモデルのリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    Azure AD認証に特化したクエリメソッドを提供します。

    ユーザー検索機能:
        - get_by_azure_oid(): Azure OIDによる検索（Azure AD認証で使用）
        - get_by_email(): メールアドレスによる検索
        - get_active_users(): アクティブユーザーのみを取得

    継承されるメソッド（BaseRepositoryから）:
        - get(id): UUIDによるユーザー取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規ユーザー作成
        - update(): ユーザー情報更新
        - delete(): ユーザー削除
        - count(): ユーザー数カウント

    Example:
        >>> async with get_db() as db:
        ...     user_repo = UserRepository(db)
        ...
        ...     # Azure OIDでユーザーを検索
        ...     user = await user_repo.get_by_azure_oid("azure-oid-12345")
        ...
        ...     # アクティブユーザーの一覧取得
        ...     active_users = await user_repo.get_active_users(limit=50)
        ...
        ...     # 新規ユーザー作成
        ...     new_user = await user_repo.create(
        ...         azure_oid="azure-oid-67890",
        ...         email="new@example.com",
        ...         display_name="New User",
        ...         is_active=True
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - ユーザー削除時、CASCADE設定により関連データ（ProjectMember）も削除されます
        - プライマリキーはUUID型です（整数ではありません）
    """

    def __init__(self, db: AsyncSession):
        """ユーザーリポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
                - DIコンテナから自動的に注入されます
                - トランザクションスコープはリクエスト単位で管理されます

        Note:
            - 親クラス（BaseRepository）の__init__を呼び出し、
              Userモデルとセッションを設定します
            - このコンストラクタは通常、FastAPIの依存性注入システムにより
              自動的に呼び出されます
        """
        super().__init__(User, db)

    async def get_by_azure_oid(self, azure_oid: str) -> User | None:
        """Azure AD Object IDによりユーザーを検索します。

        このメソッドは、Azure AD認証時に最も頻繁に使用されます。
        Azure OIDはAzure ADから提供される一意の識別子であり、
        データベースでUNIQUE制約が設定されているため、最大1件のみが返されます。

        クエリの最適化:
            - User.azure_oidにインデックスが設定されているため高速です
            - scalar_one_or_none()により、0件または1件のみを保証

        Args:
            azure_oid (str): Azure AD Object ID
                - Azure ADから提供される一意の識別子
                - 例: "12345678-1234-1234-1234-123456789abc"

        Returns:
            User | None: 該当するユーザーインスタンス、見つからない場合はNone
                - User: Azure OIDに一致するユーザーモデル
                - None: 該当するユーザーが存在しない

        Example:
            >>> user_repo = UserRepository(db)
            >>> user = await user_repo.get_by_azure_oid("azure-oid-12345")
            >>> if user:
            ...     print(f"Found user: {user.email}")
            ... else:
            ...     print("User not found")
            Found user: user@example.com
            >>>
            >>> # Azure AD認証処理での使用例
            >>> azure_user = await get_current_azure_user()
            >>> user = await user_repo.get_by_azure_oid(azure_user.oid)
            >>> if not user:
            ...     # 初回ログイン時はユーザーを作成
            ...     user = await user_service.create_from_azure(azure_user)

        Note:
            - Azure OIDはUNIQUE制約により重複しません
            - このメソッドはAzure AD認証処理のクリティカルパスであり、パフォーマンスが重要です
            - Azure OIDは変更されないため、キャッシュ可能です
        """
        result = await self.db.execute(select(User).where(User.azure_oid == azure_oid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスによりユーザーを検索します。

        このメソッドは、メールアドレスによるユーザー検索や、
        ユーザー登録時の重複チェックに使用されます。メールアドレスは
        データベースでUNIQUE制約が設定されているため、最大1件のみが返されます。

        クエリの最適化:
            - User.emailにインデックスが設定されているため高速です
            - scalar_one_or_none()により、0件または1件のみを保証

        使用ケース:
            - メール検索機能
            - ユーザー登録時の重複チェック
            - 管理画面でのユーザー検索

        Args:
            email (str): 検索対象のメールアドレス
                - 大文字小文字を区別します（データベース設定による）
                - 正規化されたメールアドレスを渡すことを推奨
                - 例: "user@example.com"

        Returns:
            User | None: 該当するユーザーインスタンス、見つからない場合はNone
                - User: メールアドレスに一致するユーザーモデル
                - None: 該当するユーザーが存在しない

        Example:
            >>> user_repo = UserRepository(db)
            >>> user = await user_repo.get_by_email("john@example.com")
            >>> if user:
            ...     print(f"Found user: {user.display_name}")
            ... else:
            ...     print("User not found")
            Found user: John Doe
            >>>
            >>> # ユーザー登録時の重複チェック
            >>> existing_user = await user_repo.get_by_email(new_email)
            >>> if existing_user:
            ...     raise ValueError("Email already registered")

        Note:
            - メールアドレスはUNIQUE制約により重複しません
            - 大文字小文字の扱いはデータベース設定に依存します
            - PostgreSQLの場合、CITEXT型を使用すると大文字小文字を区別しない検索が可能
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """アクティブなユーザーの一覧を取得します（N+1クエリ対策付き）。

        このメソッドは、is_active=Trueのユーザーのみをフィルタリングして取得します。
        管理画面でのユーザー一覧表示や、アクティブユーザーの統計取得に使用されます。
        BaseRepositoryのget_multi()メソッドを活用した便利メソッドです。

        パフォーマンス最適化:
            - selectinloadによりproject_membershipsを事前ロード（N+1クエリ対策）
            - ユーザーとプロジェクトメンバーシップを2回のクエリで効率的に取得

        使用ケース:
            - 管理画面でのアクティブユーザー一覧表示
            - アクティブユーザー数の統計取得
            - プロジェクトメンバー選択時の候補ユーザーリスト取得
            - ユーザー選択ドロップダウンの選択肢取得

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
                ページネーション: page=2, limit=10 → skip=10
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
                推奨: 1000以下に制限

        Returns:
            list[User]: アクティブユーザーのリスト
                - is_active=Trueのユーザーのみ
                - データベース順でソートされます
                - 0件の場合は空のリストを返します
                - project_memberships が事前ロード済み（追加クエリなし）

        Example:
            >>> user_repo = UserRepository(db)
            >>> # アクティブユーザーの最初の10件を取得
            >>> active_users = await user_repo.get_active_users(skip=0, limit=10)
            >>> print(f"Active users: {len(active_users)}")
            Active users: 10
            >>>
            >>> # プロジェクトメンバーシップにアクセス（追加クエリなし）
            >>> for user in active_users:
            ...     print(f"{user.email}: {len(user.project_memberships)} projects")
            >>>
            >>> # ページネーション実装例
            >>> page = 2
            >>> page_size = 20
            >>> users = await user_repo.get_active_users(
            ...     skip=(page - 1) * page_size,
            ...     limit=page_size
            ... )

        Note:
            - このメソッドは BaseRepository.get_multi() のラッパーです
            - 内部的に is_active=True フィルタを自動適用します
            - selectinloadによりproject_membershipsが事前ロードされます
            - N+1クエリ問題を回避するため、必ずこのメソッドを使用してください
            - ソート順はデータベースのデフォルト順（通常はid順）です
            - カスタムソートが必要な場合は get_multi() を直接使用してください
            - 総件数が必要な場合は count(is_active=True) を使用してください
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            is_active=True,
            load_relations=["project_memberships"],
        )

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """UUIDによりユーザーを検索します。

        このメソッドは、UUIDプライマリキーによるユーザー取得の便利メソッドです。
        BaseRepository.get()メソッドと同じ機能ですが、型ヒントを明示的に提供します。

        Args:
            user_id (uuid.UUID): ユーザーのUUID
                - UUID型のプライマリキー
                - 例: uuid.UUID("12345678-1234-1234-1234-123456789abc")

        Returns:
            User | None: 該当するユーザーインスタンス、見つからない場合はNone

        Example:
            >>> import uuid
            >>> user_repo = UserRepository(db)
            >>> user_id = uuid.UUID("12345678-1234-1234-1234-123456789abc")
            >>> user = await user_repo.get_by_id(user_id)
            >>> if user:
            ...     print(f"Found user: {user.email}")

        Note:
            - このメソッドは BaseRepository.get(id) のエイリアスです
            - プライマリキー検索は最も高速なクエリです
        """
        return await self.get(user_id)
