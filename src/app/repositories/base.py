"""共通のCRUD操作を提供するベースリポジトリクラス。

このモジュールは、Repository パターンを実装し、データアクセスロジックを
カプセル化します。ジェネリック型を使用して型安全性を確保し、
すべてのモデルで共通のCRUD操作を提供します。

設計原則:
    - Repository パターン: データアクセスロジックの抽象化
    - DRY原則: 共通CRUD操作の一元化
    - 型安全性: ジェネリック型による厳密な型チェック
    - トランザクション管理: flush()のみ実行、commit()は呼び出し側の責任
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.base import Base

logger = get_logger(__name__)


class BaseRepository[ModelType: Base, IDType: (int, uuid.UUID)]:
    """SQLAlchemyモデルの共通CRUD操作を提供するベースリポジトリクラス。

    このクラスは、すべてのリポジトリで共通のデータベース操作を実装します。
    ジェネリック型を使用して、型安全性を確保しながら再利用可能なコードを提供します。

    トランザクション管理:
        - create(), update(), delete() は flush() のみ実行
        - commit() は呼び出し側（サービス層）の責任
        - これによりトランザクションのスコープを柔軟に制御可能

    Attributes:
        model (type[ModelType]): SQLAlchemyモデルクラス
        db (AsyncSession): 非同期データベースセッション

    Example:
        >>> class UserAccountRepository(BaseRepository[User]):
        ...     def __init__(self, db: AsyncSession):
        ...         super().__init__(User, db)
        ...
        ...     async def get_by_email(self, email: str) -> User | None:
        ...         result = await self.db.execute(
        ...             select(User).where(User.email == email)
        ...         )
        ...         return result.scalar_one_or_none()
    """

    def __init__(self, model: type[ModelType], db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            model (type[ModelType]): SQLAlchemyモデルクラス
            db (AsyncSession): 非同期データベースセッション

        Note:
            - モデルクラスはSQLAlchemy 2.0のMapped型を使用している必要があります
            - データベースセッションはDIコンテナから注入されます
        """
        self.model = model
        self.db = db

    async def get(self, id: IDType) -> ModelType | None:
        """IDによってレコードを取得します。

        SQLAlchemyの`Session.get()`を使用して、プライマリキーによる
        高速な単一レコード取得を実行します。このメソッドは、
        セッションのアイデンティティマップを利用するため効率的です。

        Args:
            id (IDType): レコードのプライマリキー（intまたはUUID）
                - データベースに存在しないIDの場合はNoneを返します

        Returns:
            ModelType | None: 該当するモデルインスタンス、見つからない場合はNone
                - モデルの全フィールドが読み込まれます
                - リレーションシップは遅延ロードされます

        Example:
            >>> user_repo = UserAccountRepository(db)
            >>> user = await user_repo.get(1)
            >>> if user:
            ...     print(f"Found: {user.username}")
            ... else:
            ...     print("User not found")
            Found: john_doe

        Note:
            - このメソッドはデータベースへのクエリを実行しますが、
              セッションのアイデンティティマップに既にロードされている場合は
              データベースアクセスをスキップします
            - 存在しないIDに対してエラーは発生せず、Noneが返されます
        """
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        load_relations: list[str] | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        """オプションのフィルタリングで複数のレコードを取得します（N+1クエリ対策付き）。

        このメソッドは、ページネーション、フィルタリング、ソート、
        リレーションシップのeager loadingをサポートする柔軟なクエリビルダーです。
        フィルタは等価比較（==）のみサポートし、より複雑なクエリは各リポジトリで
        カスタムメソッドを実装してください。

        セキュリティ機能:
            - 不正なフィルタキーやorder_byキー（モデルに存在しない属性）は
              自動的にスキップされ、警告ログに記録されます
            - SQLインジェクション対策として、SQLAlchemyのORM機能を使用

        パフォーマンス最適化:
            - load_relations を使用してN+1クエリ問題を回避
            - selectinload でリレーションシップを事前ロード

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
                ページネーション: page=2, limit=10 → skip=10
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
                推奨: 1000以下に制限してパフォーマンスを確保
            order_by (str | None): ソート対象のカラム名（モデルの属性名のみ有効）
                デフォルト: None（ソートなし、データベース順）
                例: "created_at", "username", "id"
            load_relations (list[str] | None): Eager loadするリレーションシップ名のリスト
                デフォルト: None（リレーションシップをロードしない）
                例: ["sessions", "files"] - N+1クエリ問題を回避
            **filters (Any): フィルタ条件（モデルの属性名のみ有効）
                キー: モデルの属性名
                値: 一致させる値（等価比較）
                例: is_active=True, role="admin"

        Returns:
            list[ModelType]: モデルインスタンスのリスト
                - 指定されたフィルタ、ソート、ページネーションが適用されます
                - 結果が0件の場合は空のリストを返します

        Example:
            >>> # ページネーション付きで取得
            >>> users = await user_repo.get_multi(skip=0, limit=10)
            >>> print(f"First 10 users: {len(users)}")
            First 10 users: 10
            >>>
            >>> # フィルタとソート付きで取得
            >>> active_users = await user_repo.get_multi(
            ...     is_active=True,
            ...     order_by="created_at",
            ...     limit=20
            ... )
            >>> print(f"Active users: {len(active_users)}")
            Active users: 15
            >>>
            >>> # Eager loading でN+1クエリ問題を回避
            >>> users = await user_repo.get_multi(
            ...     limit=10,
            ...     load_relations=["sessions", "files"]
            ... )
            >>> # リレーションシップが事前ロード済み（追加クエリなし）
            >>> for user in users:
            ...     print(f"{user.username}: {len(user.sessions)} sessions")
            >>>
            >>> # 無効なフィルタキーは警告ログ付きでスキップ
            >>> users = await user_repo.get_multi(invalid_field="value")
            WARNING - Invalid filter key 'invalid_field' for model User. Skipping.

        Note:
            - 不正なフィルタキーやorder_byキーは警告ログを出力してスキップされます
            - フィルタは等価比較（==）のみサポートします
            - 範囲検索、部分一致、複雑な条件は各リポジトリでカスタムメソッドを実装してください
            - order_byは単一カラムのみサポート（複数カラムソートは非対応）
            - 大量データの取得時はlimitを適切に設定してください
        """
        from sqlalchemy.orm import selectinload

        query = select(self.model)

        # Eager loading（N+1クエリ対策）
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))
                else:
                    logger.warning(
                        "無効なリレーション指定",
                        model=self.model.__name__,
                        relation=relation,
                        action="skip",
                    )

        # フィルタを適用（モデル属性のみ）
        for key, value in filters.items():
            if not hasattr(self.model, key):
                logger.warning(
                    "無効なフィルタキー指定",
                    model=self.model.__name__,
                    filter_key=key,
                    action="skip",
                )
                continue

            attr = getattr(self.model, key)
            query = query.where(attr == value)

        # ソート順を適用
        if order_by:
            if hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
            else:
                logger.warning(
                    "無効なorder_byキー指定",
                    model=self.model.__name__,
                    order_by=order_by,
                    action="skip",
                )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **obj_in: Any) -> ModelType:
        """新しいレコードを作成します。

        このメソッドは以下の処理を実行します：
        1. モデルインスタンスを生成（キーワード引数からフィールドを設定）
        2. セッションに追加（add）
        3. flush()でデータベースに書き込み（IDなど自動生成フィールドを取得）
        4. refresh()でデータベースから最新状態を再読み込み
        5. インスタンスを返却（commit()は実行しない）

        トランザクション管理の重要な注意:
            - この関数は flush() のみ実行し、commit() は実行しません
            - commit() は呼び出し側（サービス層）の責任です
            - これにより複数の操作を1つのトランザクションにまとめることができます
            - 例外が発生した場合、呼び出し側でrollback()を実行してください

        Args:
            **obj_in (Any): オブジェクトデータ（モデルのフィールド名をキーとする）
                - モデルのフィールド名と一致するキーのみ有効
                - 無効なフィールド名は TypeError を発生させます
                - 必須フィールドが不足している場合は IntegrityError が発生します
                例: name="John", email="john@example.com", is_active=True

        Returns:
            ModelType: 作成されたモデルインスタンス
                - id: データベースで自動生成されたプライマリキー
                - created_at, updated_at: 自動生成されたタイムスタンプ
                - その他すべてのフィールドが読み込まれた状態

        Raises:
            TypeError: モデルに存在しないフィールド名を指定した場合
            IntegrityError: 一意制約違反、外部キー違反、NULL制約違反など

        Example:
            >>> # 単一レコード作成
            >>> async with get_db() as db:
            ...     user_repo = UserAccountRepository(db)
            ...     user = await user_repo.create(
            ...         email="john@example.com",
            ...         username="john_doe",
            ...         hashed_password="...",
            ...         is_active=True
            ...     )
            ...     await db.commit()  # 呼び出し側でcommit
            ...     print(f"Created user with ID: {user.id}")
            Created user with ID: 1
            >>>
            >>> # 複数操作を1つのトランザクションで実行
            >>> async with get_db() as db:
            ...     user_repo = UserAccountRepository(db)
            ...     user1 = await user_repo.create(email="user1@example.com", ...)
            ...     user2 = await user_repo.create(email="user2@example.com", ...)
            ...     await db.commit()  # 両方まとめてcommit

        Note:
            - flush()実行後、obj_in に指定していない自動生成フィールド（id, created_atなど）も
              refresh()により取得できます
            - リレーションシップは遅延ロードされます（必要に応じてjoinedloadを使用）
            - commit()を忘れると変更が永続化されません
            - 例外発生時は自動的にrollback()されます（AsyncSessionの動作）
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, **update_data: Any) -> ModelType:
        """既存レコードを更新します。

        このメソッドは以下の処理を実行します：
        1. update_dataの各フィールドについて、モデルに存在するか検証
        2. 存在するフィールドのみsetattr()で更新（存在しないフィールドは無視）
        3. flush()でデータベースに変更を書き込み
        4. refresh()でデータベースから最新状態を再読み込み
        5. 更新されたインスタンスを返却（commit()は実行しない）

        セキュリティ機能:
            - モデルに存在しないフィールドは自動的にスキップされます
            - これによりマスアサインメント攻撃を部分的に防止できます
            - ただし、更新可能フィールドの制限はサービス層で行うべきです

        Args:
            db_obj (ModelType): 更新するデータベースオブジェクト
                - get()などで取得した既存のモデルインスタンス
                - セッションにアタッチされている必要があります
            **update_data (Any): 更新データ（フィールド名をキーとする）
                - モデルに存在するフィールドのみ更新されます
                - 存在しないフィールドは警告なしでスキップされます
                例: email="new@example.com", is_active=False

        Returns:
            ModelType: 更新されたモデルインスタンス
                - 指定されたフィールドが更新された状態
                - updated_atなどのタイムスタンプも自動更新されます
                - refresh()により最新のデータベース状態を反映

        Example:
            >>> # ユーザー情報を更新
            >>> async with get_db() as db:
            ...     user_repo = UserAccountRepository(db)
            ...     user = await user_repo.get(1)
            ...     updated_user = await user_repo.update(
            ...         user,
            ...         email="newemail@example.com",
            ...         is_active=False
            ...     )
            ...     await db.commit()  # 呼び出し側でcommit
            ...     print(f"Updated: {updated_user.email}")
            Updated: newemail@example.com
            >>>
            >>> # 存在しないフィールドは無視される
            >>> updated_user = await user_repo.update(
            ...     user,
            ...     email="valid@example.com",
            ...     invalid_field="ignored"  # スキップされる
            ... )

        Note:
            - flush()のみ実行し、commit()は呼び出し側の責任です
            - 存在しないフィールドはエラーなしでスキップされます
            - プライマリキー（id）の更新は技術的に可能ですが推奨されません
            - updated_atなどのタイムスタンプフィールドは自動更新されます（モデル定義による）
            - 部分更新（一部フィールドのみ）が可能です
        """
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: IDType) -> bool:
        """レコードを削除します。

        このメソッドは以下の処理を実行します：
        1. get()でIDによりレコードを取得
        2. レコードが存在すればdelete()でマーク
        3. flush()でデータベースから削除
        4. 成功した場合はTrue、レコードが存在しなかった場合はFalseを返す

        CASCADE削除の注意:
            - データベースのCASCADE制約により、関連レコードも削除される可能性があります
            - 例: Userを削除すると、そのユーザーのSessionやFileも削除される
            - CASCADE設定はモデルのリレーションシップ定義で確認してください

        Args:
            id (IDType): 削除するレコードのプライマリキー（intまたはUUID）
                - 存在しないIDの場合はFalseを返します（エラーは発生しません）

        Returns:
            bool: 削除が成功した場合はTrue、レコードが見つからない場合はFalse
                - True: レコードが存在し、削除がflush()された
                - False: 指定されたIDのレコードが存在しない

        Example:
            >>> # レコードを削除
            >>> async with get_db() as db:
            ...     user_repo = UserAccountRepository(db)
            ...     success = await user_repo.delete(user_id)
            ...     if success:
            ...         await db.commit()  # 呼び出し側でcommit
            ...         print("User deleted")
            ...     else:
            ...         print("User not found")
            User deleted
            >>>
            >>> # 存在しないIDを削除しようとした場合
            >>> success = await user_repo.delete(99999)
            >>> print(f"Deletion success: {success}")
            Deletion success: False

        Note:
            - flush()のみ実行し、commit()は呼び出し側の責任です
            - 存在しないIDに対してエラーは発生せず、Falseが返されます
            - CASCADE削除により関連レコードも削除される可能性があります
            - 論理削除（ソフトデリート）が必要な場合は、update()で
              is_deleted=Trueなどのフラグを更新してください
            - 削除後はdb_objへのアクセスは推奨されません（デタッチされた状態）
        """
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False

    async def count(self, **filters: Any) -> int:
        """オプションのフィルタリングでレコードの総数を取得します。

        このメソッドは、SQLのCOUNT()関数を使用して効率的にレコード数を取得します。
        フィルタ条件を指定することで、特定の条件に一致するレコード数のみを
        カウントできます。ページネーションのtotal値として使用されることが多いです。

        パフォーマンス特性:
            - COUNT(*)クエリは通常高速ですが、大規模テーブルでは遅くなる可能性があります
            - PostgreSQLでは概算カウントが必要な場合はpg_class.reltupleを検討
            - フィルタなしのカウントはインデックスを活用できます

        Args:
            **filters (Any): フィルタ条件（モデルの属性名をキーとする）
                - モデルに存在する属性のみ有効
                - 存在しない属性は無視されます（警告なし）
                - 等価比較（==）のみサポート
                例: is_active=True, role="admin"

        Returns:
            int: 条件に一致するレコードの総数
                - フィルタなしの場合: テーブルの全レコード数
                - フィルタありの場合: 条件に一致するレコード数
                - レコードが0件の場合は0を返します

        Example:
            >>> # 全ユーザー数を取得
            >>> user_repo = UserAccountRepository(db)
            >>> total_users = await user_repo.count()
            >>> print(f"Total users: {total_users}")
            Total users: 150
            >>>
            >>> # アクティブユーザー数を取得
            >>> active_count = await user_repo.count(is_active=True)
            >>> print(f"Active users: {active_count}")
            Active users: 120
            >>>
            >>> # 複数条件でカウント
            >>> admin_count = await user_repo.count(
            ...     is_active=True,
            ...     is_superuser=True
            ... )
            >>> print(f"Active admins: {admin_count}")
            Active admins: 5
            >>>
            >>> # ページネーションと組み合わせて使用
            >>> total = await user_repo.count()
            >>> users = await user_repo.get_multi(skip=0, limit=10)
            >>> print(f"Showing {len(users)} of {total} users")
            Showing 10 of 150 users

        Note:
            - 存在しないフィールドは警告なしでスキップされます
            - フィルタは等価比較（==）のみサポートします
            - 範囲条件（>, <）や部分一致は各リポジトリでカスタムメソッドを実装してください
            - 大規模テーブルでのCOUNT(*)は遅い場合があります
            - get_multi()と組み合わせてページネーション機能を実装できます
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        # フィルタを適用
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one()
