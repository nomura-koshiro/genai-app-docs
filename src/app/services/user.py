"""Azure AD認証用ユーザーサービス。

このモジュールは、Azure AD認証に対応したユーザー管理のビジネスロジックを提供します。
パスワード認証は含まず、Azure AD Object IDをキーとしたユーザー管理に特化しています。

主な機能:
    - Azure OIDによるユーザー取得・作成
    - ユーザー情報の取得・更新
    - 最終ログイン情報の更新
    - アクティブユーザーの一覧取得

使用例:
    >>> from app.services.user import UserService
    >>>
    >>> async with get_db() as db:
    ...     user_service = UserService(db)
    ...     user = await user_service.get_or_create_by_azure_oid(
    ...         azure_oid="azure-oid-12345",
    ...         email="user@company.com",
    ...         display_name="John Doe"
    ...     )
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import cache_result, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class UserService:
    """Azure AD認証用ユーザーサービスクラス。

    このサービスは、Azure AD認証に対応したユーザー管理のビジネスロジックを提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        repository: UserRepositoryインスタンス（データベースアクセス用）

    Example:
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>> from app.services.user import UserService
        >>>
        >>> async with get_db() as db:
        ...     user_service = UserService(db)
        ...     user = await user_service.get_or_create_by_azure_oid(
        ...         azure_oid="azure-oid-12345",
        ...         email="user@company.com",
        ...         display_name="John Doe"
        ...     )
        ...     print(f"User: {user.email}")
    """

    def __init__(self, db: AsyncSession):
        """ユーザーサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.repository = UserRepository(db)

    @measure_performance
    @transactional
    async def get_or_create_by_azure_oid(
        self,
        azure_oid: str,
        email: str,
        display_name: str | None = None,
        roles: list[str] | None = None,
    ) -> User:
        """Azure OIDでユーザーを取得、または新規作成します。

        Azure AD認証後、Azure Object IDをキーにしてユーザーを検索し、
        存在しない場合は自動的に新しいユーザーアカウントを作成します。
        既存ユーザーの場合、メール/表示名が変更されていれば更新します。

        Args:
            azure_oid (str): Azure AD Object ID（一意識別子）
                - Azure ADから提供される一意の識別子
                - 例: "12345678-1234-1234-1234-123456789abc"
            email (str): メールアドレス
                - Azure ADから取得したメールアドレス
                - UNIQUE制約あり
            display_name (str | None): 表示名（オプション）
                - Azure ADのdisplayName属性
                - Noneの場合は設定されません
            roles (list[str] | None): システムレベルのロール（オプション）
                - 例: ["SystemAdmin", "User"]
                - Noneの場合は空のリストが設定されます

        Returns:
            User: 取得または作成されたユーザーモデルインスタンス
                - id: UUID型のプライマリキー
                - azure_oid: Azure AD Object ID
                - email: メールアドレス
                - display_name: 表示名
                - roles: システムレベルのロール
                - is_active: True（デフォルト）
                - created_at, updated_at: タイムスタンプ

        Raises:
            ValidationError: メールアドレスの重複など、検証エラーが発生した場合
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> # 新規ユーザー作成
            >>> user = await user_service.get_or_create_by_azure_oid(
            ...     azure_oid="azure-oid-12345",
            ...     email="user@company.com",
            ...     display_name="John Doe",
            ...     roles=["User"]
            ... )
            >>> print(f"Created user: {user.email}")
            Created user: user@company.com
            >>>
            >>> # 既存ユーザー取得（情報が変更されていれば更新）
            >>> user = await user_service.get_or_create_by_azure_oid(
            ...     azure_oid="azure-oid-12345",
            ...     email="newemail@company.com",  # メールアドレス変更
            ...     display_name="John Smith"  # 表示名変更
            ... )
            >>> print(f"Updated user: {user.email}")
            Updated user: newemail@company.com

        Note:
            - Azure OIDで検索し、存在すればそのユーザーを返します
            - 既存ユーザーのメール/表示名が変更されていれば自動更新します
            - 新規ユーザーの場合、自動的にUUID主キーが生成されます
            - すべての操作はトランザクション内で実行されます
            - 作成/更新イベントはINFOレベルでログに記録されます
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "Azure OIDでユーザーを取得または作成中",
            azure_oid=azure_oid,
            email=email,
            action="get_or_create_by_azure_oid",
        )

        try:
            # Azure OIDで検索
            user: User | None = await self.repository.get_by_azure_oid(azure_oid)

            if user:
                # 既存ユーザーの情報を更新（メール/表示名が変わった場合）
                updated = False

                if user.email != email:
                    # メールアドレスの重複チェック
                    existing_email_user = await self.repository.get_by_email(email)
                    if existing_email_user and existing_email_user.id != user.id:
                        logger.warning(
                            "メールアドレスが既に別のユーザーに使用されています",
                            azure_oid=azure_oid,
                            email=email,
                            existing_user_id=str(existing_email_user.id),
                        )
                        raise ValidationError(
                            "このメールアドレスは既に使用されています",
                            details={"email": email},
                        )

                    logger.info(
                        "ユーザーのメールアドレスを更新中",
                        user_id=str(user.id),
                        old_email=user.email,
                        new_email=email,
                    )
                    user.email = email
                    updated = True

                if display_name and user.display_name != display_name:
                    logger.info(
                        "ユーザーの表示名を更新中",
                        user_id=str(user.id),
                        old_display_name=user.display_name,
                        new_display_name=display_name,
                    )
                    user.display_name = display_name
                    updated = True

                if roles is not None and user.roles != roles:
                    logger.info(
                        "ユーザーのロールを更新中",
                        user_id=str(user.id),
                        old_roles=user.roles,
                        new_roles=roles,
                    )
                    user.roles = roles
                    updated = True

                if updated:
                    await self.db.flush()
                    await self.db.refresh(user)
                    logger.info(
                        "ユーザー情報を更新しました",
                        user_id=str(user.id),
                        email=user.email,
                        display_name=user.display_name,
                    )

                logger.debug("既存ユーザーを取得しました", user_id=str(user.id), email=user.email)
                return user

            # 新規ユーザーを作成
            # メールアドレスの重複チェック
            existing_email_user = await self.repository.get_by_email(email)
            if existing_email_user:
                logger.warning(
                    "メールアドレスが既に使用されています",
                    azure_oid=azure_oid,
                    email=email,
                    existing_user_id=str(existing_email_user.id),
                )
                raise ValidationError(
                    "このメールアドレスは既に使用されています",
                    details={"email": email},
                )

            new_user = User(
                azure_oid=azure_oid,
                email=email,
                display_name=display_name,
                roles=roles or [],
                is_active=True,
            )
            self.db.add(new_user)
            await self.db.flush()
            await self.db.refresh(new_user)

            logger.info(
                "新規ユーザーを作成しました（Azure AD）",
                user_id=str(new_user.id),
                email=new_user.email,
                display_name=new_user.display_name,
                azure_oid=azure_oid,
            )

            return new_user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Azure OIDによるユーザー取得/作成中に予期しないエラーが発生しました",
                azure_oid=azure_oid,
                email=email,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    @transactional
    async def update_last_login(self, user_id: uuid.UUID, client_ip: str | None = None) -> User:
        """ユーザーの最終ログイン情報を更新します。

        このメソッドは、ユーザーがログインした際に呼び出され、
        最終ログイン日時（とオプションでIPアドレス）を記録します。

        Args:
            user_id (uuid.UUID): ユーザーのUUID
            client_ip (str | None): クライアントのIPアドレス（オプション）
                - IPv4/IPv6両方サポート
                - ロギング用途

        Returns:
            User: 更新されたユーザーモデルインスタンス
                - last_login: 現在のUTC日時に更新されます

        Raises:
            NotFoundError: 指定されたユーザーIDが存在しない場合
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> user = await user_service.update_last_login(
            ...     user_id=uuid.UUID("12345678-1234-1234-1234-123456789abc"),
            ...     client_ip="192.168.1.1"
            ... )
            >>> print(f"Last login: {user.last_login}")
            Last login: 2024-01-15 10:30:00+00:00

        Note:
            - last_loginはUTCタイムゾーンで記録されます
            - @transactionalデコレータにより自動コミットされます
            - 監査ログにINFOレベルで記録されます
        """
        logger.info(
            "ユーザーの最終ログイン情報を更新中",
            user_id=str(user_id),
            client_ip=client_ip,
            action="update_last_login",
        )

        try:
            user = await self.repository.get_by_id(user_id)
            if not user:
                logger.warning("ユーザーが見つかりません", user_id=str(user_id))
                raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

            user.last_login = datetime.now(UTC)
            await self.db.flush()
            await self.db.refresh(user)

            # refreshの後、明示的に設定した値は必ず存在するはず
            # ローカル変数に代入することでPylanceの型ナローイングを確実にする
            last_login = user.last_login
            if last_login is None:
                raise RuntimeError("last_loginはNoneであってはならない")

            logger.info(
                "最終ログイン情報を更新しました",
                user_id=str(user.id),
                email=user.email,
                client_ip=client_ip,
                last_login=last_login.isoformat(),
            )

            return user

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "最終ログイン情報更新中に予期しないエラーが発生しました",
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @cache_result(ttl=3600, key_prefix="user")
    @measure_performance
    async def get_user(self, user_id: uuid.UUID) -> User | None:
        """ユーザーIDでユーザー情報を取得します。

        Args:
            user_id (uuid.UUID): 取得対象のユーザーUUID（主キー）

        Returns:
            User | None: 該当するユーザーモデルインスタンス、存在しない場合はNone
                - すべてのユーザー属性を含む
                - リレーションシップ（project_memberships）は遅延ロードされます

        Example:
            >>> user_id = uuid.UUID("12345678-1234-1234-1234-123456789abc")
            >>> user = await user_service.get_user(user_id)
            >>> if user:
            ...     print(f"Found user: {user.email}")
            ... else:
            ...     print("User not found")
            Found user: user@example.com

        Note:
            - 取得操作はDEBUGレベルでログに記録されます
            - 存在しないユーザーの場合、WARNINGログが記録されNoneを返します
            - @cache_resultデコレータにより1時間キャッシュされます
        """
        logger.debug("ユーザーIDでユーザーを取得中", user_id=str(user_id), action="get_user")

        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            return None

        logger.debug("ユーザーを正常に取得しました", user_id=str(user.id), email=user.email)
        return user

    @measure_performance
    async def get_user_by_email(self, email: str) -> User:
        """メールアドレスでユーザー情報を取得します。

        Args:
            email (str): 検索対象のメールアドレス（一意制約フィールド）

        Returns:
            User: 該当するユーザーモデルインスタンス
                - すべてのユーザー属性を含む
                - リレーションシップは遅延ロードされます

        Raises:
            NotFoundError: 指定されたメールアドレスのユーザーが存在しない場合

        Example:
            >>> user = await user_service.get_user_by_email("user@example.com")
            >>> print(f"Found user ID: {user.id}")
            Found user ID: 12345678-1234-1234-1234-123456789abc

        Note:
            - メールアドレスにはインデックスが設定されており、高速な検索が可能です
            - 取得操作はDEBUGレベルでログに記録されます
            - 存在しないユーザーの場合、WARNINGログが記録されます
        """
        logger.debug(
            "メールアドレスでユーザーを取得中",
            email=email,
            action="get_user_by_email",
        )

        user = await self.repository.get_by_email(email)
        if not user:
            logger.warning("ユーザーが見つかりません", email=email)
            raise NotFoundError("ユーザーが見つかりません", details={"email": email})

        logger.debug("ユーザーを正常に取得しました", user_id=str(user.id), email=user.email)
        return user

    @measure_performance
    async def get_user_by_azure_oid(self, azure_oid: str) -> User:
        """Azure OIDでユーザー情報を取得します。

        Args:
            azure_oid (str): Azure AD Object ID（一意識別子）

        Returns:
            User: 該当するユーザーモデルインスタンス
                - すべてのユーザー属性を含む
                - リレーションシップは遅延ロードされます

        Raises:
            NotFoundError: 指定されたAzure OIDのユーザーが存在しない場合

        Example:
            >>> user = await user_service.get_user_by_azure_oid("azure-oid-12345")
            >>> print(f"Found user: {user.email}")
            Found user: user@example.com

        Note:
            - Azure OIDにはインデックスが設定されており、高速な検索が可能です
            - 取得操作はDEBUGレベルでログに記録されます
            - 存在しないユーザーの場合、WARNINGログが記録されます
        """
        logger.debug(
            "Azure OIDでユーザーを取得中",
            azure_oid=azure_oid,
            action="get_user_by_azure_oid",
        )

        user = await self.repository.get_by_azure_oid(azure_oid)
        if not user:
            logger.warning("ユーザーが見つかりません", azure_oid=azure_oid)
            raise NotFoundError("ユーザーが見つかりません", details={"azure_oid": azure_oid})

        logger.debug("ユーザーを正常に取得しました", user_id=str(user.id), email=user.email)
        return user

    @measure_performance
    async def list_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """アクティブなユーザーの一覧を取得します。

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
                最大値: データベースの制限に依存

        Returns:
            list[User]: アクティブユーザーモデルインスタンスのリスト
                - is_active=Trueのユーザーのみ
                - リレーションシップは遅延ロードされます

        Example:
            >>> # 最初の10件を取得
            >>> users = await user_service.list_active_users(skip=0, limit=10)
            >>> print(f"Found {len(users)} active users")
            Found 10 active users
            >>>
            >>> # 次の10件を取得（ページネーション）
            >>> users = await user_service.list_active_users(skip=10, limit=10)

        Note:
            - 取得操作はDEBUGレベルでログに記録されます
            - 大量のレコードを取得する場合は、適切なlimitを設定してください
            - 総件数が必要な場合は、別途countメソッドを実装する必要があります
        """
        logger.debug("アクティブユーザー一覧を取得中", skip=skip, limit=limit, action="list_active_users")

        users = await self.repository.get_active_users(skip=skip, limit=limit)

        logger.debug(
            "アクティブユーザー一覧を正常に取得しました",
            count=len(users),
            skip=skip,
            limit=limit,
        )

        return users

    @measure_performance
    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """すべてのユーザーの一覧を取得します（アクティブ・非アクティブ両方）。

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
                最大値: データベースの制限に依存

        Returns:
            list[User]: ユーザーモデルインスタンスのリスト
                - アクティブ・非アクティブ両方を含む
                - リレーションシップは遅延ロードされます

        Example:
            >>> # 最初の10件を取得
            >>> users = await user_service.list_users(skip=0, limit=10)
            >>> print(f"Found {len(users)} users")
            Found 10 users

        Note:
            - 取得操作はDEBUGレベルでログに記録されます
            - 大量のレコードを取得する場合は、適切なlimitを設定してください
        """
        logger.debug("ユーザー一覧を取得中", skip=skip, limit=limit, action="list_users")

        users = await self.repository.get_multi(skip=skip, limit=limit)

        logger.debug(
            "ユーザー一覧を正常に取得しました",
            count=len(users),
            skip=skip,
            limit=limit,
        )

        return users

    @measure_performance
    async def count_users(self, is_active: bool | None = None) -> int:
        """ユーザー総数を取得します。

        このメソッドは、ページネーションのtotal値として使用されます。
        オプションでアクティブフラグによるフィルタリングが可能です。

        Args:
            is_active (bool | None): アクティブフラグフィルタ
                - True: アクティブユーザーのみ
                - False: 非アクティブユーザーのみ
                - None: 全ユーザー（デフォルト）

        Returns:
            int: 条件に一致するユーザー総数
                - フィルタなしの場合: 全ユーザー数
                - フィルタありの場合: 条件に一致するユーザー数

        Example:
            >>> # 全ユーザー数を取得
            >>> total = await user_service.count_users()
            >>> print(f"Total users: {total}")
            Total users: 150
            >>>
            >>> # アクティブユーザー数を取得
            >>> active_count = await user_service.count_users(is_active=True)
            >>> print(f"Active users: {active_count}")
            Active users: 120
            >>>
            >>> # ページネーションと組み合わせて使用
            >>> total = await user_service.count_users()
            >>> users = await user_service.list_users(skip=0, limit=10)
            >>> print(f"Showing {len(users)} of {total} users")
            Showing 10 of 150 users

        Note:
            - COUNT(*)クエリを使用するため効率的です
            - 取得操作はDEBUGレベルでログに記録されます
            - ページネーションのtotal値として推奨されます
        """
        logger.debug(
            "ユーザー総数を取得中",
            is_active=is_active,
            action="count_users",
        )

        if is_active is not None:
            total = await self.repository.count(is_active=is_active)
        else:
            total = await self.repository.count()

        logger.debug(
            "ユーザー総数を正常に取得しました",
            total=total,
            is_active=is_active,
        )

        return total

    @measure_performance
    @transactional
    async def update_user(
        self,
        user_id: uuid.UUID,
        update_data: dict[str, Any],
        current_user_roles: list[str],
    ) -> User:
        """ユーザー情報を更新します。

        このメソッドは、ユーザー情報の更新を行い、適切な権限チェックを実施します。
        roles および is_active フィールドの更新には SystemAdmin ロールが必要です。

        Args:
            user_id (uuid.UUID): 更新対象ユーザーID
            update_data (dict[str, Any]): 更新データ
                - display_name: 表示名（全ユーザー更新可能）
                - roles: システムレベルのロール（SystemAdmin のみ）
                - is_active: アクティブフラグ（SystemAdmin のみ）
            current_user_roles (list[str]): 実行ユーザーのロール（権限チェック用）
                - 例: ["User"], ["SystemAdmin", "User"]

        Returns:
            User: 更新されたユーザーモデルインスタンス
                - updated_at フィールドが自動更新されます
                - すべてのフィールドが最新の状態で返されます

        Raises:
            ValidationError: 権限不足（roles/is_active 更新時に SystemAdmin がない場合）
            NotFoundError: ユーザーが存在しない

        Example:
            >>> # 一般ユーザーが自分の表示名を更新
            >>> updated_user = await user_service.update_user(
            ...     user_id=current_user.id,
            ...     update_data={"display_name": "New Name"},
            ...     current_user_roles=["User"]
            ... )
            >>> print(f"Updated: {updated_user.display_name}")
            Updated: New Name
            >>>
            >>> # 管理者がユーザーのロールを更新
            >>> updated_user = await user_service.update_user(
            ...     user_id=target_user.id,
            ...     update_data={"roles": ["SystemAdmin", "User"]},
            ...     current_user_roles=["SystemAdmin"]
            ... )
            >>> print(f"Updated roles: {updated_user.roles}")
            Updated roles: ['SystemAdmin', 'User']

        Note:
            - @transactional デコレータにより自動コミットされます
            - roles/is_active の更新は SystemAdmin ロール必須です
            - 更新操作は INFO レベルでログに記録されます
            - 部分更新が可能です（指定されたフィールドのみ更新）
        """
        logger.info(
            "ユーザー情報を更新中",
            user_id=str(user_id),
            update_fields=list(update_data.keys()),
            current_user_roles=current_user_roles,
            action="update_user",
        )

        # 権限チェック: roles または is_active の更新は管理者のみ
        if ("roles" in update_data or "is_active" in update_data):
            if "SystemAdmin" not in current_user_roles:
                logger.warning(
                    "権限不足: rolesまたはis_activeの更新には管理者権限が必要です",
                    user_id=str(user_id),
                    current_user_roles=current_user_roles,
                    attempted_update=update_data,
                )
                raise ValidationError(
                    "rolesまたはis_activeの更新には管理者権限が必要です",
                    details={"required_role": "SystemAdmin"},
                )

        # ユーザー取得
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

        # 更新実行
        updated_user = await self.repository.update(user, **update_data)

        logger.info(
            "ユーザー情報を更新しました",
            user_id=str(updated_user.id),
            updated_fields=list(update_data.keys()),
        )

        return updated_user
