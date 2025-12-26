"""ユーザーアカウント認証サービス。

このモジュールは、Azure AD認証関連のビジネスロジックを提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import UserAccount
from app.services.user_account.user_account.base import UserAccountServiceBase

logger = get_logger(__name__)


class UserAccountAuthService(UserAccountServiceBase):
    """ユーザーアカウント認証サービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ユーザーアカウント認証サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @measure_performance
    @transactional
    async def get_or_create_by_azure_oid(
        self,
        azure_oid: str,
        email: str,
        display_name: str | None = None,
        roles: list[str] | None = None,
    ) -> UserAccount:
        """Azure OIDでユーザーを取得、または新規作成します。

        Azure AD認証後、Azure Object IDをキーにしてユーザーを検索し、
        存在しない場合は自動的に新しいユーザーアカウントを作成します。
        既存ユーザーの場合、メール/表示名が変更されていれば更新します。

        Args:
            azure_oid: Azure AD Object ID（一意識別子）
            email: メールアドレス
            display_name: 表示名（オプション）
            roles: システムレベルのロール（オプション）

        Returns:
            UserAccount: 取得または作成されたユーザーモデルインスタンス

        Raises:
            ValidationError: メールアドレスの重複など、検証エラーが発生した場合
            Exception: データベース操作で予期しないエラーが発生した場合
        """
        logger.info(
            "Azure OIDでユーザーを取得または作成中",
            azure_oid=azure_oid,
            email=email,
            action="get_or_create_by_azure_oid",
        )

        try:
            # Azure OIDで検索
            user: UserAccount | None = await self.repository.get_by_azure_oid(azure_oid)

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

            new_user = UserAccount(
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
    async def update_last_login(self, user_id: uuid.UUID, client_ip: str | None = None) -> UserAccount:
        """ユーザーの最終ログイン情報を更新します。

        Args:
            user_id: ユーザーのUUID
            client_ip: クライアントのIPアドレス（オプション）

        Returns:
            UserAccount: 更新されたユーザーモデルインスタンス

        Raises:
            NotFoundError: 指定されたユーザーIDが存在しない場合
            Exception: データベース操作で予期しないエラーが発生した場合
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
