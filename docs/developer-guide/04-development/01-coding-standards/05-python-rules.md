# Python規約

PEP 8準拠のPythonコーディング規約と、本プロジェクト固有のルールについて説明します。

## 概要

本プロジェクトでは以下のPython規約を遵守します：

- **PEP 8準拠**
- **型ヒントの徹底使用**
- **Docstringの記述**
- **Import文の整理**
- **エラーハンドリング**

---

## 1. PEP 8準拠

### インデント

- スペース4つを使用
- タブは使用しない

```python
# ✅ 良い例
def calculate_total(
    base_price: float,
    tax_rate: float = 0.1,
    discount: float = 0.0
) -> float:
    subtotal = base_price - discount
    tax = subtotal * tax_rate
    return subtotal + tax


# ❌ 悪い例（タブ使用）
def calculate_total(base_price, tax_rate=0.1):
→   subtotal = base_price  # タブは使用しない
→   return subtotal * (1 + tax_rate)
```

### 行の長さ

- 1行は79〜100文字以内
- 長い行は適切に改行

```python
# ✅ 良い例：長い引数リストを改行
def create_user(
    email: str,
    username: str,
    password: str,
    is_active: bool = True,
    is_superuser: bool = False,
) -> SampleUser:
    pass


# ✅ 良い例：長いクエリを改行
query = (
    select(SampleUser)
    .where(SampleUser.is_active == True)
    .where(SampleUser.created_at > start_date)
    .order_by(SampleUser.created_at.desc())
    .limit(10)
)


# ✅ 良い例：長い文字列を改行
error_message = (
    "ユーザーの作成に失敗しました。"
    "メールアドレスが既に使用されているか、"
    "入力値が不正です。"
)


# ❌ 悪い例：1行が長すぎる
query = select(SampleUser).where(SampleUser.is_active == True).where(SampleUser.created_at > start_date).order_by(SampleUser.created_at.desc()).limit(10)
```

### 空白行

- トップレベルの関数/クラス定義の間：2行
- クラス内のメソッド定義の間：1行
- 関数内の論理的なセクション：1行

```python
# ✅ 良い例
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class SampleSampleUserService:
    """ユーザーサービス。"""

    def __init__(self, db: AsyncSession):
        self.repository = SampleUserRepository(db)

    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        """ユーザーを作成。"""
        # バリデーション
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("User already exists")

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
            raise AuthenticationError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")

        return user


class SessionService:
    """セッションサービス。"""
    pass
```

---

## 2. 型ヒントの徹底使用

### 基本的な型ヒント

すべての関数・メソッドに型ヒントを追加します。

```python
from typing import Optional, Any
from datetime import datetime

# ✅ 良い例：すべてに型ヒント
def get_user(user_id: int) -> SampleUser | None:
    """ユーザーを取得。"""
    pass


def create_user(
    email: str,
    username: str,
    password: str,
    is_active: bool = True,
) -> SampleUser:
    """ユーザーを作成。"""
    pass


def calculate_total(
    items: list[dict[str, Any]],
    tax_rate: float = 0.1,
) -> float:
    """合計金額を計算。"""
    pass


# ❌ 悪い例：型ヒントなし
def get_user(user_id):
    pass


def create_user(email, username, password, is_active=True):
    pass
```

### Python 3.10+ の型ヒント

Python 3.10以降の新しい型ヒント構文を使用します。

```python
# ✅ Python 3.10+ の構文
def get_user(user_id: int) -> SampleUser | None:
    """Union型は | を使用。"""
    pass


def get_value(key: str) -> str | int | float:
    """複数の型を返す可能性がある場合。"""
    pass


# ❌ 古い構文（使用しない）
from typing import Optional, Union

def get_user(user_id: int) -> Optional[SampleUser]:
    pass


def get_value(key: str) -> Union[str, int, float]:
    pass
```

### ジェネリック型

本プロジェクトでは **Python 3.12+** の新しいジェネリック構文を使用します。

#### Python 3.12+ の新しい構文（推奨）

**必須要件**: Python 3.12以上

```python
from sqlalchemy.ext.asyncio import AsyncSession

# ✅ Python 3.12+: class定義でのジェネリック
class BaseRepository[ModelType: Base]:
    """ジェネリック型を使用した基底リポジトリ。

    Note:
        Python 3.12+の新しいジェネリック構文を使用しています。
        TypeVarとGenericの明示的な使用が不要になりました。
    """

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


# ✅ Python 3.12+: 関数定義でのジェネリック
def verify_active_user[UserType: (SampleUser, UserAccount)](
    user: UserType
) -> UserType:
    """ユーザーのアクティブ状態を検証します。

    この関数はSampleUserとUserAccountの両方で使用できます（DRY原則）。

    Args:
        user: 検証対象のユーザー（SampleUser または UserAccount）

    Returns:
        アクティブなユーザー（同じ型）

    Raises:
        HTTPException: ユーザーが無効化されている場合（403エラー）

    Note:
        Python 3.12+の新しいジェネリック構文を使用しています。
        型制約はタプルで複数指定可能です。
    """
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="アカウントが無効化されています",
        )
    return user


# 具体的な型を指定
class SampleUserRepository(BaseRepository[SampleUser]):
    pass
```

**新しい構文の利点**:

- `TypeVar`と`Generic`の明示的なインポートが不要
- より簡潔で読みやすいコード
- 関数でもジェネリックが使用可能
- 複数の型制約をタプルで指定可能

#### 従来の構文（Python 3.10/3.11互換）

Python 3.12未満の環境では従来の構文を使用します：

```python
from typing import Generic, TypeVar, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Python 3.10/3.11: TypeVarとGenericを明示的に使用
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """ジェネリック型を使用した基底リポジトリ（従来構文）。"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        return await self.db.get(self.model, id)


# 具体的な型を指定
class SampleUserRepository(BaseRepository[SampleUser]):
    pass
```

**本プロジェクトの方針**: Python 3.13を標準としているため、新しいコードでは**Python 3.12+構文を使用**してください。

### TypeAlias

```python
from typing import TypeAlias

# 型エイリアスを定義
UserId: TypeAlias = int
Email: TypeAlias = str
JsonDict: TypeAlias = dict[str, Any]


def get_user(user_id: UserId) -> SampleUser | None:
    pass


def send_email(email: Email, subject: str, body: str) -> bool:
    pass


def process_data(data: JsonDict) -> JsonDict:
    pass
```

---

## 3. Docstringの記述

### Google Style Docstring

本プロジェクトではGoogle Styleのdocstringを使用します。

```python
def create_user(
    email: str,
    username: str,
    password: str,
    is_active: bool = True,
) -> SampleUser:
    """新しいユーザーを作成します。

    Args:
        email: ユーザーのメールアドレス
        username: ユーザー名
        password: 平文パスワード（ハッシュ化されます）
        is_active: ユーザーがアクティブかどうか（デフォルト: True）

    Returns:
        作成されたユーザーインスタンス

    Raises:
        ValidationError: メールアドレスまたはユーザー名が既に使用されている場合
        DatabaseError: データベース操作に失敗した場合

    Example:
        >>> user = await create_user(
        ...     email="user@example.com",
        ...     username="testuser",
        ...     password="password123"
        ... )
        >>> print(user.email)
        user@example.com
    """
    pass
```

### クラスのDocstring

```python
class SampleSampleUserService:
    """ユーザー関連のビジネスロジックを提供するサービス。

    このクラスはユーザーの作成、更新、削除、認証などの
    ビジネスロジックを実装します。

    Attributes:
        repository: ユーザーリポジトリインスタンス
    """

    def __init__(self, db: AsyncSession):
        """UserServiceを初期化します。

        Args:
            db: データベースセッション
        """
        self.repository = SampleUserRepository(db)
```

### モジュールのDocstring

```python
"""ユーザー関連のビジネスロジック用のサービスモジュール。

このモジュールはユーザーの作成、認証、プロファイル管理などの
ビジネスロジックを提供します。

Example:
    >>> from app.services.sample_user import SampleUserService
    >>> service = SampleUserService(db)
    >>> user = await service.create_user(user_data)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AuthenticationError, ValidationError
# ... 以下実装
```

---

## 4. Import文の整理

### Import順序

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルアプリケーション

各グループの間は1行空ける。

```python
# ✅ 良い例
# 標準ライブラリ
from datetime import datetime, timedelta, timezone
from typing import Any

# サードパーティライブラリ
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ローカルアプリケーション
from app.api.core import CurrentSampleUserDep, DatabaseDep
from app.core.exceptions import NotFoundError, ValidationError
from app.models.sample_user import SampleUser
from app.repositories.sample_user import SampleUserRepository
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse


# ❌ 悪い例：順序が混在
from app.models.sample_user import SampleUser
from datetime import datetime
from fastapi import APIRouter
from app.schemas.sample_user import SampleUserCreate
from typing import Any
```

### 絶対インポートを使用

相対インポートではなく、絶対インポートを使用します。

```python
# ✅ 良い例：絶対インポート
from app.models.sample_user import SampleUser
from app.repositories.sample_user import SampleUserRepository
from app.services.sample_user import SampleUserService


# ❌ 悪い例：相対インポート
from ..models.user import User
from ..repositories.sample_user import SampleUserRepository
from .sample_user import SampleUserService
```

### ワイルドカードインポートを避ける

```python
# ✅ 良い例：必要なものだけインポート
from app.core.exceptions import NotFoundError, ValidationError


# ❌ 悪い例：ワイルドカードインポート
from app.core.exceptions import *
```

---

## 5. エラーハンドリング

### 具体的な例外をキャッチ

```python
# ✅ 良い例：具体的な例外をキャッチ
async def get_user(user_id: int) -> SampleUser:
    """ユーザーを取得。"""
    try:
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user
    except SQLAlchemyError as e:
        raise DatabaseError(f"Database error: {str(e)}") from e


# ❌ 悪い例：すべての例外をキャッチ
async def get_user(user_id: int) -> SampleUser:
    try:
        user = await self.repository.get(user_id)
        return user
    except Exception:  # 広すぎる
        return None
```

### カスタム例外を使用

```python
# src/app/core/exceptions.py
class AppException(Exception):
    """アプリケーション基底例外。"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """リソース未検出例外。"""

    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=404, details=details)


class ValidationError(AppException):
    """バリデーションエラー例外。"""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=422, details=details)


# 使用例
async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
    """ユーザーを作成。"""
    existing_user = await self.repository.get_by_email(user_data.email)
    if existing_user:
        raise ValidationError(
            "User already exists",
            details={"email": user_data.email}
        )

    return await self.repository.create(**user_data.model_dump())
```

### 例外チェーン

```python
# ✅ 良い例：例外チェーンを使用
async def process_file(file_path: str) -> dict:
    """ファイルを処理。"""
    try:
        content = await read_file(file_path)
        return parse_content(content)
    except FileNotFoundError as e:
        raise NotFoundError(
            f"File not found: {file_path}",
            details={"file_path": file_path}
        ) from e  # 元の例外を保持
    except ValueError as e:
        raise ValidationError(
            f"Invalid file content: {file_path}",
            details={"error": str(e)}
        ) from e
```

---

## 6. 非同期処理

### async/await の使用

```python
# ✅ 良い例
async def get_user(self, user_id: int) -> SampleUser:
    """非同期でユーザーを取得。"""
    user = await self.repository.get(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    return user


async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
    """非同期でユーザーを作成。"""
    # バリデーション
    existing = await self.repository.get_by_email(user_data.email)
    if existing:
        raise ValidationError("Email already exists")

    # 作成
    return await self.repository.create(**user_data.model_dump())


# ❌ 悪い例：awaitを忘れる
async def get_user(self, user_id: int) -> SampleUser:
    user = self.repository.get(user_id)  # awaitがない
    return user
```

### 複数の非同期操作

```python
import asyncio

# ✅ 並列実行
async def get_user_data(user_id: int) -> dict:
    """ユーザーデータを並列取得。"""
    # 並列実行
    user, sessions, files = await asyncio.gather(
        self.user_repo.get(user_id),
        self.session_repo.get_by_user(user_id),
        self.file_repo.get_by_user(user_id),
    )

    return {
        "user": user,
        "sessions": sessions,
        "files": files,
    }


# ❌ 悪い例：逐次実行（遅い）
async def get_user_data(user_id: int) -> dict:
    user = await self.user_repo.get(user_id)
    sessions = await self.session_repo.get_by_user(user_id)
    files = await self.file_repo.get_by_user(user_id)
    return {"user": user, "sessions": sessions, "files": files}
```

---

## 7. コンテキストマネージャー

### with文の使用

```python
# ✅ 良い例：コンテキストマネージャー使用
async def read_file(file_path: str) -> bytes:
    """ファイルを読み込み。"""
    async with aiofiles.open(file_path, "rb") as f:
        return await f.read()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッション取得。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ❌ 悪い例：手動でクローズ
async def read_file(file_path: str) -> bytes:
    f = await aiofiles.open(file_path, "rb")
    content = await f.read()
    await f.close()  # 例外時にクローズされない可能性
    return content
```

---

## よくある間違いとその対処法

### 間違い1: 型ヒントの省略

```python
# ❌ 悪い例
def create_user(data):
    return User(**data)

# ✅ 良い例
def create_user(data: SampleUserCreate) -> SampleUser:
    return User(**data.model_dump())
```

### 間違い2: Docstringの欠如

```python
# ❌ 悪い例
async def authenticate(email, password):
    user = await get_by_email(email)
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError()
    return user

# ✅ 良い例
async def authenticate(self, email: str, password: str) -> SampleUser:
    """ユーザーを認証します。

    Args:
        email: ユーザーのメールアドレス
        password: 平文パスワード

    Returns:
        認証されたユーザーインスタンス

    Raises:
        AuthenticationError: 認証に失敗した場合
    """
    user = await self.repository.get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid credentials")
    return user
```

### 間違い3: 広すぎる例外キャッチ

```python
# ❌ 悪い例
try:
    user = await create_user(data)
except Exception:  # 広すぎる
    pass

# ✅ 良い例
try:
    user = await create_user(data)
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    raise
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise
```

---

## 8. ロギング（structlog）

本プロジェクトでは、構造化ロギングライブラリ **structlog** を使用します。

### ロガーの取得

各モジュールで `get_logger(__name__)` を使用してロガーを取得します。

```python
# ✅ 良い例：structlogのロガー使用
from app.core.logging import get_logger

logger = get_logger(__name__)

class SampleSampleUserService:
    """ユーザーサービス。"""

    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        """ユーザーを作成します。"""
        logger.info("user_creation_started", email=user_data.email)

        user = await self.repository.create(user_data)

        logger.info(
            "user_created_successfully",
            user_id=user.id,
            email=user.email
        )
        return user


# ❌ 悪い例：標準loggingの使用
import logging

logger = logging.getLogger(__name__)  # structlogを使用すること
```

### 構造化ログの書き方

ログメッセージは**イベント名**として記述し、詳細情報は**キーワード引数**で渡します。

```python
# ✅ 良い例：構造化ログ（キー-値ペア）
logger.info("user_logged_in", user_id=123, ip_address="192.168.1.1")
logger.error("database_connection_failed", error="timeout", retry_count=3)
logger.warning("rate_limit_exceeded", user_id=456, limit=100)

# ❌ 悪い例：文字列補間
logger.info(f"User {user_id} logged in from {ip_address}")
logger.info("User logged in", extra={"user_id": user_id})  # extraは使わない
```

### コンテキストバインディング

永続的なフィールド（request_id等）は `bind()` で追加します。

```python
# ✅ 良い例：コンテキストバインディング
from app.core.logging import get_logger

logger = get_logger(__name__)

async def process_api_request(request_id: str, user_id: int):
    """APIリクエストを処理します。"""
    # リクエストIDとユーザーIDをバインド
    request_logger = logger.bind(request_id=request_id, user_id=user_id)

    request_logger.info("api_request_started", endpoint="/api/v1/users")
    # 以降のログに自動的に request_id と user_id が付与される

    result = await fetch_data()
    request_logger.info("data_fetched", record_count=len(result))

    request_logger.info("api_request_completed", status_code=200)
```

### 例外ログ

例外情報を含める場合は `exception()` メソッドを使用します。

```python
# ✅ 良い例：例外ログ
try:
    result = 1 / 0
except ZeroDivisionError:
    logger.exception(
        "division_error",
        operation="divide",
        numerator=1,
        denominator=0
    )
```

### ログレベルの使い分け

```python
# DEBUG: 詳細なデバッグ情報（開発環境のみ）
logger.debug("query_execution", sql=query, params=params)

# INFO: 通常の情報ログ
logger.info("user_created", user_id=123)

# WARNING: 警告（処理は継続）
logger.warning("cache_miss", key="user:123")

# ERROR: エラー（処理失敗）
logger.error("api_call_failed", endpoint="/api/v1/users", status_code=500)

# 例外情報付きエラー
try:
    await risky_operation()
except Exception:
    logger.exception("operation_failed", operation="risky_operation")
```

### ログ出力形式

**開発環境** (DEBUG=True):

```text
user_logged_in user_id=123 ip_address='192.168.1.1'
```

**本番環境** (ENVIRONMENT=production):

```json
{
  "event": "user_logged_in",
  "user_id": 123,
  "ip_address": "192.168.1.1",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "info",
  "logger": "app.services.user"
}
```

### 注意事項

- **機密情報をログに含めない**: パスワード、トークン、APIキーは絶対にログに出力しない
- **構造化を徹底**: 文字列補間ではなくキーワード引数を使用
- **イベント名は明確に**: `user_logged_in`, `payment_processed` など動作を表す名前
- **コンテキストバインディング活用**: リクエストID、ユーザーIDなど複数ログで共通する情報

---

## 参考リンク

- [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 -- Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [PEP 484 -- Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

---

次のセクション: [06-fastapi-rules.md](./06-fastapi-rules.md)
