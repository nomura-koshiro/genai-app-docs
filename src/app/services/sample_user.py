"""ビジネスロジック用のユーザーサービス。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import cache_result, measure_performance, transactional
from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models.sample_user import SampleUser
from app.repositories.sample_user import SampleUserRepository
from app.schemas.sample_user import SampleUserCreate

logger = get_logger(__name__)


class SampleUserService:
    """ユーザー関連のビジネスロジックを提供するサービスクラス。

    このサービスは、ユーザーの作成、認証、取得などの操作を提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        repository: UserRepositoryインスタンス（データベースアクセス用）

    Example:
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>> from app.services.sample_user import SampleUserService
        >>> from app.schemas.sample_user import SampleUserCreate
        >>>
        >>> async with get_db() as db:
        ...     user_service = SampleUserService(db)
        ...     user_data = SampleUserCreate(
        ...         email="user@example.com",
        ...         username="testuser",
        ...         password="SecurePass123!"
        ...     )
        ...     user = await user_service.create_user(user_data)
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
        self.repository = SampleUserRepository(db)

    @measure_performance
    @transactional
    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        """新しいユーザーアカウントを作成します。

        このメソッドは以下の処理を実行します：
        1. メールアドレスの重複チェック
        2. ユーザー名の重複チェック
        3. パスワードのbcryptハッシュ化
        4. データベースへのユーザーレコード保存
        5. 作成イベントのロギング

        Args:
            user_data (SampleUserCreate): ユーザー作成用のPydanticスキーマ
                - email: ユーザーのメールアドレス（一意制約）
                - username: ユーザー名（一意制約、最大50文字）
                - password: パスワード（平文、ハッシュ化されて保存）

        Returns:
            SampleUser: 作成されたユーザーモデルインスタンス
                - id: 自動生成されたユーザーID
                - email, username: 入力値
                - hashed_password: bcryptでハッシュ化されたパスワード
                - is_active: True（デフォルト）
                - created_at, updated_at: 自動生成されたタイムスタンプ

        Raises:
            ValidationError: 以下の場合に発生
                - メールアドレスが既に使用されている
                - ユーザー名が既に使用されている
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> user_data = SampleUserCreate(
            ...     email="newuser@example.com",
            ...     username="newuser",
            ...     password="SecurePass123!"
            ... )
            >>> user = await user_service.create_user(user_data)
            >>> print(f"Created user: {user.email}")
            Created user: newuser@example.com

        Note:
            - パスワードはbcryptでハッシュ化され、平文では保存されません
            - メールアドレスとユーザー名は一意である必要があります
            - 作成されたユーザーはデフォルトでアクティブ状態です
            - すべての操作は構造化ログに記録されます
        """
        logger.info(
            "ユーザーを作成中",
            email=user_data.email,
            username=user_data.username,
            action="user_creation",
        )

        try:
            # ユーザーが既に存在するかチェック
            existing_user = await self.repository.get_by_email(user_data.email)
            if existing_user:
                logger.warning(
                    "ユーザー作成失敗: メールアドレスが既に存在します",
                    email=user_data.email,
                )
                raise ValidationError(
                    "このメールアドレスは既に使用されています",
                    details={"email": user_data.email},
                )

            existing_username = await self.repository.get_by_username(user_data.username)
            if existing_username:
                logger.warning(
                    "ユーザー作成失敗: ユーザー名が既に使用されています",
                    username=user_data.username,
                )
                raise ValidationError("このユーザー名は既に使用されています", details={"username": user_data.username})

            # ハッシュ化されたパスワードでユーザーを作成
            hashed_password = hash_password(user_data.password)
            user = await self.repository.create(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
            )

            # トランザクションをコミット（@transactionalデコレータで自動化）
            # await self.db.commit()  # デコレータが自動実行
            await self.db.refresh(user)

            logger.info(
                "ユーザーを正常に作成しました",
                user_id=user.id,
                email=user.email,
                username=user.username,
            )

            return user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "ユーザー作成中に予期しないエラーが発生しました",
                email=user_data.email,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def authenticate(self, email: str, password: str, client_ip: str | None = None) -> SampleUser:
        """メールアドレスとパスワードでユーザーを認証します。

        このメソッドは以下の検証を実行します：
        1. メールアドレスでユーザーを検索
        2. ユーザーの存在確認
        3. アカウントロック状態の確認
        4. bcryptによるパスワード検証
        5. アカウントのアクティブ状態確認
        6. ログイン失敗カウントの管理
        7. 認証イベントのロギング

        Args:
            email (str): ユーザーのメールアドレス
            password (str): ユーザーのパスワード（平文）
            client_ip (str | None): クライアントのIPアドレス（ロギング用）

        Returns:
            SampleUser: 認証されたユーザーモデルインスタンス
                - すべてのユーザー属性を含む
                - is_active: True（認証済みユーザーは必ずアクティブ）

        Raises:
            AuthenticationError: 以下の場合に発生
                - メールアドレスに対応するユーザーが存在しない
                - パスワードが一致しない
                - アカウントが無効化されている（is_active=False）
                - アカウントがロックされている（5回連続失敗）
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> user = await user_service.authenticate(
            ...     email="user@example.com",
            ...     password="SecurePass123!",
            ...     client_ip="192.168.1.1"
            ... )
            >>> print(f"Authenticated: {user.username}")
            Authenticated: testuser

        Note:
            - セキュリティ上、エラーメッセージは汎用的な内容を返します
            - 認証失敗の具体的な理由（ユーザー不存在 vs パスワード不一致）は
              ログに記録されますが、クライアントには開示されません
            - すべての認証試行は監査ログに記録されます
            - 5回連続失敗でアカウントは1時間ロックされます
        """
        from datetime import UTC, datetime, timedelta

        logger.info(
            "ユーザー認証を試行中",
            email=email,
            client_ip=client_ip,
            action="authentication",
        )

        try:
            user = await self.repository.get_by_email(email)
            if not user:
                logger.warning("認証失敗: ユーザーが見つかりません", email=email)
                raise AuthenticationError("メールアドレスまたはパスワードが正しくありません")

            # アカウントロック状態をチェック
            if user.locked_until and user.locked_until > datetime.now(UTC):
                logger.warning(
                    "認証失敗: アカウントがロックされています",
                    email=email,
                    user_id=user.id,
                    locked_until=user.locked_until.isoformat(),
                )
                lock_time = user.locked_until.strftime("%Y-%m-%d %H:%M:%S")
                raise AuthenticationError(f"アカウントがロックされています。{lock_time}以降に再試行してください")

            # パスワード検証
            if not verify_password(password, user.hashed_password):
                # ログイン失敗カウントをインクリメント
                user.failed_login_attempts += 1

                # 設定値に基づいてアカウントをロック
                if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    lock_duration = timedelta(hours=settings.ACCOUNT_LOCK_DURATION_HOURS)
                    locked_until_time = datetime.now(UTC) + lock_duration
                    user.locked_until = locked_until_time
                    await self.db.commit()
                    logger.warning(
                        f"認証失敗: {settings.MAX_LOGIN_ATTEMPTS}回連続失敗によりアカウントをロックしました",
                        email=email,
                        user_id=user.id,
                        locked_until=locked_until_time.isoformat(),
                    )
                    raise AuthenticationError(
                        f"ログイン失敗回数が上限に達しました。アカウントは{settings.ACCOUNT_LOCK_DURATION_HOURS}時間ロックされます"
                    )

                await self.db.commit()
                logger.warning(
                    "認証失敗: パスワードが無効です",
                    email=email,
                    user_id=user.id,
                    failed_attempts=user.failed_login_attempts,
                )
                raise AuthenticationError("メールアドレスまたはパスワードが正しくありません")

            # アカウントアクティブ状態をチェック
            if not user.is_active:
                logger.warning(
                    "認証失敗: ユーザーアカウントが無効化されています",
                    email=email,
                    user_id=user.id,
                )
                raise AuthenticationError("このアカウントは無効化されています")

            # 認証成功 - ログイン失敗カウントをリセット、ログイン情報を更新
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.now(UTC)
            if client_ip:
                user.last_login_ip = client_ip
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(
                "ユーザー認証に成功しました",
                user_id=user.id,
                email=user.email,
                username=user.username,
                client_ip=client_ip,
            )

            return user

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(
                "認証中に予期しないエラーが発生しました",
                email=email,
                error=str(e),
                exc_info=True,
            )
            raise

    @cache_result(ttl=3600, key_prefix="user")
    @measure_performance
    async def get_user(self, user_id: int) -> SampleUser | None:
        """ユーザーIDでユーザー情報を取得します。

        Args:
            user_id (int): 取得対象のユーザーID（主キー）

        Returns:
            SampleUser | None: 該当するユーザーモデルインスタンス、存在しない場合はNone
                - すべてのユーザー属性を含む
                - リレーションシップは遅延ロードされます

        Example:
            >>> user = await user_service.get_user(user_id=1)
            >>> if user:
            ...     print(f"Found user: {user.email}")
            ... else:
            ...     print("User not found")
            Found user: user@example.com

        Note:
            - 取得操作はDEBUGレベルでログに記録されます
            - 存在しないユーザーの場合、WARNINGログが記録されNoneを返します
        """
        logger.debug("ユーザーIDでユーザーを取得中", user_id=user_id, action="get_user")

        user = await self.repository.get(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=user_id)
            return None

        logger.debug("ユーザーを正常に取得しました", user_id=user.id, email=user.email)
        return user

    async def get_user_by_email(self, email: str) -> SampleUser:
        """メールアドレスでユーザー情報を取得します。

        Args:
            email (str): 検索対象のメールアドレス（一意制約フィールド）

        Returns:
            SampleUser: 該当するユーザーモデルインスタンス
                - すべてのユーザー属性を含む
                - リレーションシップは遅延ロードされます

        Raises:
            NotFoundError: 指定されたメールアドレスのユーザーが存在しない場合

        Example:
            >>> user = await user_service.get_user_by_email("user@example.com")
            >>> print(f"Found user ID: {user.id}")
            Found user ID: 1

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

        logger.debug("ユーザーを正常に取得しました", user_id=user.id, email=user.email)
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[SampleUser]:
        """ページネーション付きでユーザーの一覧を取得します。

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
                最大値: データベースの制限に依存

        Returns:
            list[SampleUser]: ユーザーモデルインスタンスのリスト
                - created_at順でソートされます（リポジトリの実装に依存）
                - リレーションシップは遅延ロードされます

        Example:
            >>> # 最初の10件を取得
            >>> users = await user_service.list_users(skip=0, limit=10)
            >>> print(f"Found {len(users)} users")
            Found 10 users
            >>>
            >>> # 次の10件を取得（ページネーション）
            >>> users = await user_service.list_users(skip=10, limit=10)

        Note:
            - 取得操作はDEBUGレベルでログに記録されます
            - 大量のレコードを取得する場合は、適切なlimitを設定してください
            - 総件数が必要な場合は、別途countメソッドを実装する必要があります
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
