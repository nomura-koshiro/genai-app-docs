"""ユーザーモデル用のデータアクセスリポジトリ。

このモジュールは、Userモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、ユーザー固有のクエリメソッド（メール検索、
ユーザー名検索、アクティブユーザー取得など）を追加しています。

主な機能:
    - メールアドレスによるユーザー検索（認証時に使用）
    - ユーザー名による検索（ユニーク制約検証に使用）
    - アクティブユーザーの一覧取得（管理機能で使用）
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> import uuid
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.sample.sample_user import SampleUserRepository
    >>>
    >>> async with get_db() as db:
    ...     user_repo = SampleUserRepository(db)
    ...     user = await user_repo.get_by_email("user@example.com")
    ...     if user:
    ...         print(f"Found user: {user.username}")
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SampleUser
from app.repositories.base import BaseRepository


class SampleUserRepository(BaseRepository[SampleUser, uuid.UUID]):
    """サンプル: Userモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    ユーザー管理に特化したクエリメソッドを提供します。

    ユーザー検索機能:
        - get_by_email(): メールアドレスによる検索（ログイン認証で使用）
        - get_by_username(): ユーザー名による検索（重複チェックで使用）
        - get_active_users(): アクティブユーザーのみを取得

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるユーザー取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規ユーザー作成
        - update(): ユーザー情報更新
        - delete(): ユーザー削除
        - count(): ユーザー数カウント

    Example:
        >>> async with get_db() as db:
        ...     user_repo = SampleUserRepository(db)
        ...
        ...     # メールでユーザーを検索
        ...     user = await user_repo.get_by_email("john@example.com")
        ...
        ...     # アクティブユーザーの一覧取得
        ...     active_users = await user_repo.get_active_users(limit=50)
        ...
        ...     # 新規ユーザー作成
        ...     new_user = await user_repo.create(
        ...         email="new@example.com",
        ...         username="newuser",
        ...         hashed_password="...",
        ...         is_active=True
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - ユーザー削除時、CASCADE設定により関連データ（Session, File）も削除されます
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
        super().__init__(SampleUser, db)

    async def get_by_email(self, email: str) -> SampleUser | None:
        """メールアドレスによりユーザーを検索します。

        このメソッドは、ユーザーのログイン認証時に最も頻繁に使用されます。
        メールアドレスはデータベースでUNIQUE制約が設定されているため、
        最大1件のレコードのみが返されます。

        クエリの最適化:
            - User.emailにインデックスが設定されているため高速です
            - scalar_one_or_none()により、0件または1件のみを保証

        Args:
            email (str): 検索対象のメールアドレス
                - 大文字小文字を区別します（データベース設定による）
                - 正規化されたメールアドレスを渡すことを推奨
                - 例: "user@example.com"

        Returns:
            SampleUser | None: 該当するユーザーインスタンス、見つからない場合はNone
                - SampleUser: メールアドレスに一致するユーザーモデル
                - None: 該当するユーザーが存在しない

        Example:
            >>> user_repo = SampleUserRepository(db)
            >>> user = await user_repo.get_by_email("john@example.com")
            >>> if user:
            ...     print(f"Found user: {user.username}")
            ... else:
            ...     print("User not found")
            Found user: john_doe
            >>>
            >>> # 認証処理での使用例
            >>> user = await user_repo.get_by_email(login_email)
            >>> if user and verify_password(password, user.hashed_password):
            ...     return create_access_token(user.id)

        Note:
            - メールアドレスはUNIQUE制約により重複しません
            - 大文字小文字の扱いはデータベース設定に依存します
            - PostgreSQLの場合、CITEXT型を使用すると大文字小文字を区別しない検索が可能
            - このメソッドは認証処理のクリティカルパスであり、パフォーマンスが重要です
        """
        result = await self.db.execute(select(SampleUser).where(SampleUser.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> SampleUser | None:
        """ユーザー名によりユーザーを検索します。

        このメソッドは、主にユーザー登録時のユーザー名重複チェックや、
        ユーザー名によるプロフィール検索に使用されます。ユーザー名は
        データベースでUNIQUE制約が設定されているため、最大1件のみが返されます。

        使用ケース:
            - ユーザー登録時の重複チェック
            - ユーザー名によるプロフィール検索
            - 管理画面でのユーザー検索

        Args:
            username (str): 検索対象のユーザー名
                - 大文字小文字を区別します
                - 空白文字や特殊文字は含まれないことを想定
                - 例: "john_doe", "user123"

        Returns:
            SampleUser | None: 該当するユーザーインスタンス、見つからない場合はNone
                - SampleUser: ユーザー名に一致するユーザーモデル
                - None: 該当するユーザーが存在しない

        Example:
            >>> user_repo = SampleUserRepository(db)
            >>> user = await user_repo.get_by_username("john_doe")
            >>> if user:
            ...     print(f"User email: {user.email}")
            ... else:
            ...     print("Username is available")
            User email: john@example.com
            >>>
            >>> # ユーザー登録時の重複チェック
            >>> existing_user = await user_repo.get_by_username(new_username)
            >>> if existing_user:
            ...     raise ValueError("Username already taken")
            ... else:
            ...     new_user = await user_repo.create(username=new_username, ...)

        Note:
            - ユーザー名はUNIQUE制約により重複しません
            - 大文字小文字を区別するため、"John"と"john"は別のユーザー名です
            - ユーザー名の正規化（小文字化など）はサービス層で実装することを推奨
            - インデックスが設定されている場合、検索は高速です
        """
        result = await self.db.execute(select(SampleUser).where(SampleUser.username == username))
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[SampleUser]:
        """アクティブなユーザーの一覧を取得します。

        このメソッドは、is_active=Trueのユーザーのみをフィルタリングして取得します。
        管理画面でのユーザー一覧表示や、アクティブユーザーの統計取得に使用されます。
        BaseRepositoryのget_multi()メソッドを活用した便利メソッドです。

        使用ケース:
            - 管理画面でのアクティブユーザー一覧表示
            - アクティブユーザー数の統計取得
            - メール送信対象ユーザーのリスト取得
            - ユーザー選択ドロップダウンの選択肢取得

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
                ページネーション: page=2, limit=10 → skip=10
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
                推奨: 1000以下に制限

        Returns:
            list[SampleUser]: アクティブユーザーのリスト
                - is_active=Trueのユーザーのみ
                - データベース順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> user_repo = SampleUserRepository(db)
            >>> # アクティブユーザーの最初の10件を取得
            >>> active_users = await user_repo.get_active_users(skip=0, limit=10)
            >>> print(f"Active users: {len(active_users)}")
            Active users: 10
            >>>
            >>> # すべてのアクティブユーザーを取得（大量データ注意）
            >>> all_active = await user_repo.get_active_users(limit=10000)
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
            - ソート順はデータベースのデフォルト順（通常はid順）です
            - カスタムソートが必要な場合は get_multi() を直接使用してください
            - 総件数が必要な場合は count(is_active=True) を使用してください
        """
        return await self.get_multi(skip=skip, limit=limit, is_active=True)
