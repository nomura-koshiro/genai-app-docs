# 命名規則

一貫性のある命名規則により、コードの可読性と保守性を向上させます。

## 概要

本プロジェクトでは、Pythonの標準的な命名規則（PEP 8）に従い、さらに独自の規約を追加しています：

- **ファイル命名規則**
- **変数命名規則**
- **関数命名規則**
- **クラス命名規則**
- **定数命名規則**

---

## 1. ファイル命名規則

### 基本ルール

- すべて小文字
- 単語はアンダースコア（`_`）で区切る（snake_case）
- 意味のある名前を使用
- 複数形・単数形を適切に使い分ける

### ディレクトリ構造と命名

```
src/app/
├── api/
│   ├── routes/          # 複数のルートを含むので複数形
│   │   ├── agents.py    # エージェント関連のエンドポイント（複数のエンドポイント）
│   │   ├── files.py     # ファイル関連のエンドポイント
│   │   └── users.py     # ユーザー関連のエンドポイント
│   ├── middlewares/     # 複数のミドルウェアを含む
│   │   ├── error_handler.py
│   │   ├── logging.py
│   │   └── rate_limit.py
│   └── dependencies.py  # 依存性注入の定義
├── models/              # 複数のモデルを含む
│   ├── user.py          # Userモデル（単一のモデル定義）
│   ├── session.py       # SessionとMessageモデル
│   └── file.py          # Fileモデル
├── repositories/        # 複数のリポジトリを含む
│   ├── base.py          # 基底クラス
│   ├── user.py          # ユーザーリポジトリ
│   └── session.py       # セッションリポジトリ
├── services/            # 複数のサービスを含む
│   ├── user.py          # ユーザーサービス
│   ├── session.py       # セッションサービス
│   └── file.py          # ファイルサービス
├── schemas/             # 複数のスキーマを含む
│   ├── common.py        # 共通スキーマ
│   ├── user.py          # ユーザースキーマ
│   └── agent.py         # エージェントスキーマ
├── core/                # コア機能モジュール
│   ├── exceptions.py    # 例外定義
│   ├── security.py      # セキュリティユーティリティ
│   └── logging.py       # ロギング設定
├── config.py            # 設定ファイル
├── database.py          # データベース設定
└── main.py              # アプリケーションエントリーポイント
```

### 命名パターン

| ファイルタイプ | 命名例 | 説明 |
|--------------|--------|------|
| モデル | `user.py`, `session.py` | エンティティ名（単数形） |
| スキーマ | `user.py`, `agent.py` | エンティティ名（単数形） |
| サービス | `user.py`, `file.py` | エンティティ名（単数形） |
| リポジトリ | `user.py`, `session.py` | エンティティ名（単数形） |
| APIルート | `users.py`, `agents.py` | エンドポイント名（通常複数形） |
| ユーティリティ | `security.py`, `logging.py` | 機能名 |
| 設定 | `config.py`, `database.py` | 目的名 |

---

## 2. 変数命名規則

### 基本ルール

- snake_case を使用
- 意味のある名前を使用
- 略語は避ける（一般的なもの除く）
- ブール値は `is_`, `has_`, `can_` などのプレフィックス

### 実装例

```python
# ✅ 良い例
user_id = 123
user_email = "user@example.com"
is_active = True
has_permission = False
can_edit = True
total_count = 100
max_retry_count = 3
created_at = datetime.now()

# ❌ 悪い例
u = 123                    # 短すぎる
usrEmail = "..."           # camelCase（Pythonでは使わない）
active = True              # ブール値であることが不明確
tot = 100                  # 略語
maxRetryCnt = 3            # camelCase + 略語
ct = datetime.now()        # 意味不明


# ✅ Pydanticスキーマでの使用例
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_active: bool = True
    is_superuser: bool = False


# ✅ SQLAlchemyモデルでの使用例
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(50))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

### 特殊なケース

#### プライベート変数

```python
class UserService:
    def __init__(self, db: AsyncSession):
        self._db = db                    # プライベート変数（1つのアンダースコア）
        self.__internal_cache = {}       # 名前マングリング（2つのアンダースコア）
```

#### 定数

```python
# ✅ 大文字のSNAKE_CASE
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_PAGE_SIZE = 20
MIN_PASSWORD_LENGTH = 8
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# config.py での使用例
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

#### ループ変数

```python
# ✅ 短い名前も許容される
for i in range(10):
    print(i)

for user in users:
    print(user.email)

# ❌ インデックスとして使わない変数を _ で始める
for _ in range(10):  # 値を使わない場合
    do_something()

# ✅ 辞書のループ
for key, value in user_dict.items():
    print(f"{key}: {value}")
```

---

## 3. 関数命名規則

### 基本ルール

- snake_case を使用
- 動詞で始める（アクションを表す）
- 意味のある名前を使用
- 長すぎない（3〜4単語程度）

### 命名パターン

| パターン | 例 | 用途 |
|---------|-----|------|
| `get_*` | `get_user`, `get_by_email` | データ取得 |
| `create_*` | `create_user`, `create_session` | データ作成 |
| `update_*` | `update_user`, `update_profile` | データ更新 |
| `delete_*` | `delete_user`, `delete_session` | データ削除 |
| `is_*` | `is_active`, `is_valid` | ブール値を返す |
| `has_*` | `has_permission`, `has_access` | ブール値を返す |
| `can_*` | `can_edit`, `can_delete` | ブール値を返す |
| `validate_*` | `validate_email`, `validate_password` | バリデーション |
| `calculate_*` | `calculate_total`, `calculate_price` | 計算 |
| `process_*` | `process_file`, `process_data` | 処理 |
| `send_*` | `send_email`, `send_notification` | 送信 |

### 実装例

```python
# ✅ リポジトリ層
class UserRepository(BaseRepository[User]):
    async def get(self, id: int) -> User | None:
        """IDでユーザーを取得。"""
        return await self.db.get(User, id)

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得。"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """複数のユーザーを取得。"""
        return await super().get_multi(skip=skip, limit=limit)

    async def create(self, **kwargs) -> User:
        """ユーザーを作成。"""
        return await super().create(**kwargs)


# ✅ サービス層
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        """新しいユーザーを作成。"""
        pass

    async def authenticate(self, email: str, password: str) -> User:
        """ユーザーを認証。"""
        pass

    async def update_profile(self, user_id: int, data: UserUpdate) -> User:
        """ユーザープロファイルを更新。"""
        pass

    async def delete_user(self, user_id: int) -> bool:
        """ユーザーを削除。"""
        pass

    async def is_email_taken(self, email: str) -> bool:
        """メールアドレスが使用済みかチェック。"""
        pass

    async def has_permission(self, user_id: int, permission: str) -> bool:
        """ユーザーが権限を持っているかチェック。"""
        pass


# ✅ ユーティリティ関数
def hash_password(password: str) -> str:
    """パスワードをハッシュ化。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証。"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWTアクセストークンを作成。"""
    pass


def decode_access_token(token: str) -> dict | None:
    """JWTトークンをデコード。"""
    pass
```

### 非同期関数

```python
# ✅ async関数も同じ命名規則
async def get_user(user_id: int) -> User:
    """非同期でユーザーを取得。"""
    pass


async def process_file(file: UploadFile) -> FileResponse:
    """非同期でファイルを処理。"""
    pass
```

---

## 4. クラス命名規則

### 基本ルール

- PascalCase（CapitalizedWords）を使用
- 名詞または名詞句を使用
- 意味のある名前を使用

### 命名パターン

| パターン | 例 | 用途 |
|---------|-----|------|
| エンティティ | `User`, `Session`, `File` | ドメインモデル |
| スキーマ | `UserCreate`, `UserResponse`, `SessionResponse` | Pydanticスキーマ |
| サービス | `UserService`, `FileService`, `SessionService` | ビジネスロジック |
| リポジトリ | `UserRepository`, `SessionRepository` | データアクセス |
| 例外 | `ValidationError`, `AuthenticationError`, `NotFoundError` | カスタム例外 |
| ミドルウェア | `ErrorHandlerMiddleware`, `LoggingMiddleware` | ミドルウェア |
| 設定 | `Settings`, `DatabaseConfig` | 設定クラス |

### 実装例

```python
# ✅ モデル
class User(Base):
    """ユーザーモデル。"""
    __tablename__ = "users"


class Session(Base):
    """セッションモデル。"""
    __tablename__ = "sessions"


class Message(Base):
    """メッセージモデル。"""
    __tablename__ = "messages"


# ✅ スキーマ
class UserBase(BaseModel):
    """ベースユーザースキーマ。"""
    pass


class UserCreate(UserBase):
    """ユーザー作成スキーマ。"""
    password: str


class UserUpdate(UserBase):
    """ユーザー更新スキーマ。"""
    pass


class UserResponse(UserBase):
    """ユーザーレスポンススキーマ。"""
    id: int
    created_at: datetime


# ✅ サービス
class UserService:
    """ユーザーサービス。"""
    pass


class SessionService:
    """セッションサービス。"""
    pass


# ✅ リポジトリ
class BaseRepository(Generic[ModelType]):
    """ベースリポジトリ。"""
    pass


class UserRepository(BaseRepository[User]):
    """ユーザーリポジトリ。"""
    pass


# ✅ 例外
class AppException(Exception):
    """アプリケーション基底例外。"""
    pass


class NotFoundError(AppException):
    """リソース未検出例外。"""
    pass


class ValidationError(AppException):
    """バリデーションエラー例外。"""
    pass


class AuthenticationError(AppException):
    """認証エラー例外。"""
    pass
```

### 抽象基底クラス

```python
from abc import ABC, abstractmethod

# ✅ ABC を継承
class StorageBackend(ABC):
    """ストレージの抽象基底クラス。"""

    @abstractmethod
    async def upload(self, file_path: str, content: bytes) -> str:
        pass

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        pass


class LocalStorage(StorageBackend):
    """ローカルストレージ実装。"""
    pass


class AzureBlobStorage(StorageBackend):
    """Azure Blob Storage実装。"""
    pass
```

---

## 5. テーブル名とカラム名

### テーブル名

- 小文字
- snake_case
- 複数形

```python
class User(Base):
    __tablename__ = "users"       # 複数形


class Session(Base):
    __tablename__ = "sessions"    # 複数形


class Message(Base):
    __tablename__ = "messages"    # 複数形


class File(Base):
    __tablename__ = "files"       # 複数形
```

### カラム名

- 小文字
- snake_case
- 外部キーは `{table_name}_id`

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(50))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_superuser: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE")  # 外部キー
    )
    metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

---

## 6. APIエンドポイント命名規則

### RESTful命名規則

```python
# ✅ リソースベースの命名
@router.get("/users")              # ユーザー一覧
@router.post("/users")             # ユーザー作成
@router.get("/users/{user_id}")    # ユーザー詳細
@router.put("/users/{user_id}")    # ユーザー更新
@router.delete("/users/{user_id}") # ユーザー削除

# ✅ サブリソース
@router.get("/users/{user_id}/sessions")              # ユーザーのセッション一覧
@router.get("/users/{user_id}/sessions/{session_id}") # 特定セッション

# ✅ アクション（動詞が必要な場合）
@router.post("/users/register")    # ユーザー登録
@router.post("/users/login")       # ログイン
@router.post("/users/logout")      # ログアウト
@router.post("/sessions/{session_id}/archive")  # セッションをアーカイブ

# ❌ 悪い例
@router.get("/getUsers")           # 動詞を含めない
@router.post("/createUser")        # 動詞を含めない
@router.get("/user-list")          # ハイフン使用（アンダースコアかスラッシュを使用）
```

---

## よくある間違いとその対処法

### 間違い1: camelCaseの使用

```python
# ❌ 悪い例
def getUserById(userId: int) -> User:
    pass

# ✅ 良い例
def get_user_by_id(user_id: int) -> User:
    pass
```

### 間違い2: 短すぎる変数名

```python
# ❌ 悪い例
u = get_user(123)
s = Session()
r = requests.get(url)

# ✅ 良い例
user = get_user(123)
session = Session()
response = requests.get(url)
```

### 間違い3: 一貫性のない命名

```python
# ❌ 悪い例：混在した命名
class User(Base):
    emailAddress: str  # camelCase
    user_name: str     # snake_case
    IsActive: bool     # PascalCase

# ✅ 良い例：一貫したsnake_case
class User(Base):
    email_address: str
    user_name: str
    is_active: bool
```

### 間違い4: 意味のない名前

```python
# ❌ 悪い例
data = get_data()
result = process(data)
output = transform(result)

# ✅ 良い例
user_data = get_user_data()
validated_user = validate_user(user_data)
user_response = transform_to_response(validated_user)
```

---

## 参考リンク

- [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 -- Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [RESTful API Naming Conventions](https://restfulapi.net/resource-naming/)

---

次のセクション: [05-python-rules.md](./05-python-rules.md)
