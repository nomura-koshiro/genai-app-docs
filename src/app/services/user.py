"""ビジネスロジック用のユーザーサービス。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class UserService:
    """ユーザー関連のビジネスロジック用サービス。"""

    def __init__(self, db: AsyncSession):
        """ユーザーサービスを初期化します。

        Args:
            db: データベースセッション
        """
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """新しいユーザーを作成します。

        Args:
            user_data: ユーザー作成データ

        Returns:
            作成されたユーザーインスタンス

        Raises:
            ValidationError: ユーザーが既に存在する場合
        """
        # Check if user already exists
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError(
                "User already exists", details={"email": user_data.email}
            )

        existing_username = await self.repository.get_by_username(user_data.username)
        if existing_username:
            raise ValidationError(
                "Username already taken", details={"username": user_data.username}
            )

        # Create user with hashed password
        hashed_password = hash_password(user_data.password)
        user = await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

        return user

    async def authenticate(self, email: str, password: str) -> User:
        """ユーザーを認証します。

        Args:
            email: ユーザーのメールアドレス
            password: ユーザーのパスワード

        Returns:
            認証されたユーザーインスタンス

        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        user = await self.repository.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    async def get_user(self, user_id: int) -> User:
        """IDによってユーザーを取得します。

        Args:
            user_id: ユーザーID

        Returns:
            ユーザーインスタンス

        Raises:
            NotFoundError: ユーザーが見つからない場合
        """
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError("User not found", details={"user_id": user_id})
        return user

    async def get_user_by_email(self, email: str) -> User:
        """メールアドレスによってユーザーを取得します。

        Args:
            email: ユーザーのメールアドレス

        Returns:
            ユーザーインスタンス

        Raises:
            NotFoundError: ユーザーが見つからない場合
        """
        user = await self.repository.get_by_email(email)
        if not user:
            raise NotFoundError("User not found", details={"email": email})
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """ユーザーの一覧を取得します。

        Args:
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            ユーザーのリスト
        """
        return await self.repository.get_multi(skip=skip, limit=limit)
