# サービス層（Services）

ビジネスロジックの実装について説明します。

## 概要

サービス層は、ビジネスロジックを実装し、複数のリポジトリを調整します。

**責務**:

- ビジネスルールの実装
- 複数のリポジトリの調整
- トランザクション境界の定義
- ドメインロジックのオーケストレーション

---

## 基本的なサービス

```python
# src/app/services/sample_user.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.sample_user import SampleUser
from app.repositories.sample_user import SampleUserRepository
from app.schemas.sample_user import SampleUserCreate


class SampleUserService:
    """ユーザー関連のビジネスロジック用サービス。"""

    def __init__(self, db: AsyncSession):
        self.repository = SampleUserRepository(db)

    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        """新しいユーザーを作成。"""
        # バリデーション
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError(
                "User already exists",
                details={"email": user_data.email}
            )

        existing_username = await self.repository.get_by_username(user_data.username)
        if existing_username:
            raise ValidationError(
                "Username already taken",
                details={"username": user_data.username}
            )

        # パスワードハッシュ化
        hashed_password = hash_password(user_data.password)

        # ユーザー作成
        user = await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        return user

    async def authenticate(self, email: str, password: str) -> SampleUser:
        """ユーザーを認証。"""
        user = await self.repository.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    async def get_user(self, user_id: int) -> SampleUser:
        """ユーザーを取得。"""
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError("User not found", details={"user_id": user_id})
        return user

    async def update_user(
        self,
        user_id: int,
        update_data: dict[str, Any],
        current_user_roles: list[str],
    ) -> SampleUser:
        """ユーザー情報を更新。

        このメソッドは、権限チェックとビジネスロジックをカプセル化し、
        API層からビジネスロジックを分離します（SOLID原則のSRP準拠）。

        Args:
            user_id: 更新対象ユーザーID
            update_data: 更新データ（display_name, roles, is_active等）
            current_user_roles: 実行ユーザーのロール（権限チェック用）

        Returns:
            更新されたユーザーインスタンス

        Raises:
            ValidationError: 権限不足（roles/is_activeの更新にSystemAdminが必要）
            NotFoundError: ユーザーが存在しない
        """
        if ("roles" in update_data or "is_active" in update_data):
            if "SystemAdmin" not in current_user_roles:
                raise ValidationError(
                    "rolesまたはis_activeの更新には管理者権限が必要です",
                    details={"required_role": "SystemAdmin"},
                )

        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError("User not found", details={"user_id": user_id})

        updated_user = await self.repository.update(user, **update_data)
        return updated_user

    async def count_users(self, is_active: bool | None = None) -> int:
        """ユーザー総数を取得。

        ページネーションのtotal値として使用します。
        オプションでアクティブフラグによるフィルタリングが可能です。

        Args:
            is_active: アクティブフラグフィルタ
                - True: アクティブユーザーのみ
                - False: 非アクティブユーザーのみ
                - None: 全ユーザー（デフォルト）

        Returns:
            条件に一致するユーザー総数
        """
        if is_active is not None:
            return await self.repository.count(is_active=is_active)
        return await self.repository.count()
```

---

## 複数リポジトリの調整

```python
class SessionService:
    """セッションサービス。"""

    def __init__(self, db: AsyncSession):
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)
        self.user_repo = SampleUserRepository(db)

    async def create_session_with_message(
        self,
        user_id: int | None,
        initial_message: str
    ) -> Session:
        """セッションを作成し、初期メッセージを追加。"""
        # ユーザー存在確認（オプション）
        if user_id:
            user = await self.user_repo.get(user_id)
            if not user:
                raise NotFoundError("User not found")

        # セッション作成
        session = await self.session_repo.create(
            session_id=str(uuid.uuid4()),
            user_id=user_id
        )

        # 初期メッセージ追加
        await self.message_repo.create(
            session_id=session.id,
            role="user",
            content=initial_message
        )

        return session
```

---

## トランザクション管理

```python
# データベースセッションの提供
# src/app/core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # commitはサービス層または@transactionalデコレータが責任を持つ
        except Exception:
            await session.rollback()  # エラー時にロールバック
            raise
        finally:
            await session.close()
```

**設計思想**:
- `get_db()`はセッションの提供のみを担当
- トランザクション境界（commit/rollback）はサービス層が定義
- `@transactional`デコレータ（将来実装予定）または明示的なcommitで管理

---

## ベストプラクティス

1. **ビジネスロジックはサービス層に**

   ```python
   # ✅ サービス層でバリデーション
   async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
       if await self.repository.get_by_email(user_data.email):
           raise ValidationError("Email already exists")
       return await self.repository.create(...)
   ```

2. **リポジトリを通じてデータアクセス**

   ```python
   # ✅ リポジトリ使用
   user = await self.repository.get(user_id)

   # ❌ 直接DBアクセス
   user = await self.db.get(SampleUser, user_id)
   ```

3. **カスタム例外を使用**

   ```python
   if not user:
       raise NotFoundError("User not found", details={"user_id": user_id})
   ```

---

次のセクション: [05-api.md](./05-api.md)
