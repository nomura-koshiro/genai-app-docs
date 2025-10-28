# ユーティリティ関数リファレンス

バックエンドで使用される共通ユーティリティ関数とヘルパークラスの詳細を記載します。

## 目次

- [概要](#概要)
- [セキュリティユーティリティ](#セキュリティユーティリティ)
- [ロギングユーティリティ](#ロギングユーティリティ)
- [例外処理](#例外処理)
- [ストレージバックエンド](#ストレージバックエンド)
- [データベースユーティリティ](#データベースユーティリティ)

---

## 概要

### ユーティリティモジュールの場所

```text
src/app/
├── core/
│   ├── security.py       # セキュリティ関連
│   ├── logging.py        # ロギング設定
│   └── exceptions.py     # カスタム例外
└── storage/
    ├── base.py           # ストレージ基底クラス
    ├── local.py          # ローカルストレージ
    └── azure_blob.py     # Azureストレージ
```

---

## セキュリティユーティリティ

`app/core/security/`

認証・認可のためのセキュリティ関連関数（password.py, jwt.py, api_key.py）。

### パスワードハッシュ化

#### hash_password()

パスワードをbcryptでハッシュ化します。

##### シグネチャ

```python
def hash_password(password: str) -> str
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| password | str | 平文パスワード |

##### 戻り値

- `str`: ハッシュ化されたパスワード

##### 使用例

```python
from app.core.security import hash_password

# パスワードをハッシュ化
hashed = hash_password("my_secure_password")
print(hashed)  # $2b$12$...
```

---

#### verify_password()

パスワードをハッシュ化されたパスワードと照合します。

##### シグネチャ

```python
def verify_password(plain_password: str, hashed_password: str) -> bool
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| plain_password | str | 平文パスワード |
| hashed_password | str | ハッシュ化されたパスワード |

##### 戻り値

- `bool`: パスワードが一致する場合True

##### 使用例

```python
from app.core.security import verify_password

# パスワード検証
is_valid = verify_password("my_password", user.hashed_password)
if is_valid:
    print("認証成功")
else:
    print("認証失敗")
```

---

### JWTトークン管理

#### create_access_token()

JWTアクセストークンを作成します。

##### シグネチャ

```python
def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| data | dict[str, Any] | トークンにエンコードするデータ |
| expires_delta | timedelta \| None | トークンの有効期限（省略時は15分） |

##### 戻り値

- `str`: エンコードされたJWTトークン

##### 例外

- `ImportError`: python-joseがインストールされていない場合

##### 使用例

```python
from app.core.security import create_access_token
from datetime import timedelta

# トークン作成
token = create_access_token(
    data={"sub": "user@example.com", "role": "user"},
    expires_delta=timedelta(minutes=30)
)
print(token)  # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

#### decode_access_token()

JWTアクセストークンをデコードします。

##### シグネチャ

```python
def decode_access_token(token: str) -> dict[str, Any] | None
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| token | str | デコードするJWTトークン |

##### 戻り値

- `dict[str, Any] | None`: デコードされたペイロード、無効な場合はNone

##### 例外

- `ImportError`: python-joseがインストールされていない場合

##### 使用例

```python
from app.core.security import decode_access_token

# トークンデコード
payload = decode_access_token(token)
if payload:
    user_email = payload.get("sub")
    print(f"ユーザー: {user_email}")
else:
    print("無効なトークン")
```

---

#### generate_api_key()

ランダムなAPIキーを生成します。

##### シグネチャ

```python
def generate_api_key() -> str
```

##### 戻り値

- `str`: ランダムなAPIキー文字列（URL-safe Base64）

##### 使用例

```python
from app.core.security import generate_api_key

# APIキー生成
api_key = generate_api_key()
print(api_key)  # xrZvO8QN7rTUJc4KwYxPdE9vL2fB5gHh...
```

---

## ロギングユーティリティ

`app/core/logging.py`

アプリケーション全体のロギング設定。

### setup_logging()

アプリケーションのロギング設定をセットアップします。

#### シグネチャ

```python
def setup_logging() -> None
```

##### 機能

- コンソールハンドラーの設定（カラー出力）
- ファイルハンドラーの設定（本番環境）
- ログレベルの設定（DEBUG/INFO）
- サードパーティライブラリのログレベル調整

##### 使用例

```python
from app.core.logging import setup_logging

# アプリケーション起動時に呼び出す
setup_logging()
```

---

### get_logger()

指定された名前のロガーインスタンスを取得します。

#### シグネチャ

```python
def get_logger(name: str) -> logging.Logger
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| name | str | ロガー名（通常は`__name__`） |

##### 戻り値

- `logging.Logger`: ロガーインスタンス

##### 使用例

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# ログ出力
logger.debug("デバッグメッセージ")
logger.info("情報メッセージ")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
logger.critical("重大なエラー")
```

---

### ColoredFormatter

コンソール出力用のカラーログフォーマッター。

#### 機能

- ログレベルに応じた色付き出力
- DEBUG: シアン
- INFO: グリーン
- WARNING: イエロー
- ERROR: レッド
- CRITICAL: マゼンタ

##### 使用例

```python
from app.core.logging import ColoredFormatter
import logging

# カスタムハンドラーに適用
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
```

---

## 例外処理

`app/core/exceptions.py`

アプリケーション全体で使用するカスタム例外クラス。

### AppException

アプリケーション基底例外。

#### シグネチャ

```python
class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    )
```

##### 属性

| 名前 | 型 | 説明 |
|-----|---|------|
| message | str | エラーメッセージ |
| status_code | int | HTTPステータスコード |
| details | dict | 追加情報 |

##### 使用例

```python
from app.core.exceptions import AppException

raise AppException(
    message="Something went wrong",
    status_code=500,
    details={"error_code": "INTERNAL_ERROR"}
)
```

---

### NotFoundError

リソース未検出例外（404 Not Found）。

#### シグネチャ

```python
class NotFoundError(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None
    )
```

##### 使用例

```python
from app.core.exceptions import NotFoundError

user = await get_user(user_id)
if not user:
    raise NotFoundError(
        message=f"User with id {user_id} not found",
        details={"user_id": user_id}
    )
```

---

### ValidationError

バリデーションエラー例外（422 Unprocessable Entity）。

#### シグネチャ

```python
class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None
    )
```

##### 使用例

```python
from app.core.exceptions import ValidationError

if len(password) < 8:
    raise ValidationError(
        message="Password must be at least 8 characters",
        details={"field": "password", "min_length": 8}
    )
```

---

### AuthenticationError

認証エラー例外（401 Unauthorized）。

#### シグネチャ

```python
class AuthenticationError(AppException):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None
    )
```

##### 使用例

```python
from app.core.exceptions import AuthenticationError

if not verify_password(password, user.hashed_password):
    raise AuthenticationError(
        message="Invalid credentials",
        details={"reason": "password_mismatch"}
    )
```

---

### AuthorizationError

認可エラー例外（403 Forbidden）。

#### シグネチャ

```python
class AuthorizationError(AppException):
    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None
    )
```

##### 使用例

```python
from app.core.exceptions import AuthorizationError

if not user.is_superuser:
    raise AuthorizationError(
        message="Admin access required",
        details={"required_role": "admin"}
    )
```

---

### DatabaseError

データベース操作エラー例外（500 Internal Server Error）。

#### シグネチャ

```python
class DatabaseError(AppException):
    def __init__(
        self,
        message: str = "Database operation failed",
        details: dict[str, Any] | None = None
    )
```

##### 使用例

```python
from app.core.exceptions import DatabaseError
from sqlalchemy.exc import IntegrityError

try:
    await db.commit()
except IntegrityError as e:
    raise DatabaseError(
        message="Failed to save data",
        details={"error": str(e)}
    )
```

---

### ExternalServiceError

外部サービスエラー例外（502 Bad Gateway）。

#### シグネチャ

```python
class ExternalServiceError(AppException):
    def __init__(
        self,
        message: str = "External service error",
        details: dict[str, Any] | None = None
    )
```

##### 使用例

```python
from app.core.exceptions import ExternalServiceError
import httpx

try:
    response = await client.get("https://api.example.com")
    response.raise_for_status()
except httpx.HTTPError as e:
    raise ExternalServiceError(
        message="Failed to fetch data from external API",
        details={"service": "example.com", "error": str(e)}
    )
```

---

## ストレージバックエンド

`app/storage/`

ファイルストレージの抽象化レイヤー。

### StorageBackend（基底クラス）

`app/storage/base.py`

すべてのストレージバックエンドの基底クラス。

#### メソッド

| メソッド | 説明 |
|---------|------|
| upload() | ファイルをアップロード |
| download() | ファイルをダウンロード |
| delete() | ファイルを削除 |
| exists() | ファイルの存在確認 |
| list_files() | ファイル一覧取得 |

---

#### upload()

ファイルをアップロードします。

##### シグネチャ

```python
async def upload(self, file_path: Path, content: bytes) -> str
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| file_path | Path | ファイルパス |
| content | bytes | ファイル内容 |

##### 戻り値

- `str`: ファイル識別子

---

#### download()

ファイルをダウンロードします。

##### シグネチャ

```python
async def download(self, file_id: str) -> bytes
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| file_id | str | ファイル識別子 |

##### 戻り値

- `bytes`: ファイル内容

##### 例外

- `FileNotFoundError`: ファイルが存在しない場合

---

#### delete()

ファイルを削除します。

##### シグネチャ

```python
async def delete(self, file_id: str) -> None
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| file_id | str | ファイル識別子 |

##### 例外

- `FileNotFoundError`: ファイルが存在しない場合

---

#### exists()

ファイルの存在を確認します。

##### シグネチャ

```python
async def exists(self, file_id: str) -> bool
```

##### パラメータ

| 名前 | 型 | 説明 |
|-----|---|------|
| file_id | str | ファイル識別子 |

##### 戻り値

- `bool`: ファイルが存在する場合True

---

#### list_files()

すべてのファイルを一覧表示します。

##### シグネチャ

```python
async def list_files(self) -> list[dict[str, str]]
```

##### 戻り値

- `list[dict[str, str]]`: ファイル情報のリスト

---

### LocalStorageBackend

`app/storage/local.py`

ローカルファイルシステムストレージの実装。

#### 使用例

```python
from pathlib import Path
from app.storage.local import LocalStorageBackend

# 初期化
storage = LocalStorageBackend(base_path="./uploads")

# ファイルアップロード
file_path = Path("documents/report.pdf")
content = b"PDF content here..."
file_id = await storage.upload(file_path, content)

# ファイルダウンロード
content = await storage.download(file_id)

# ファイル存在確認
exists = await storage.exists(file_id)

# ファイル削除
await storage.delete(file_id)

# ファイル一覧
files = await storage.list_files()
for file_info in files:
    print(f"{file_info['filename']}: {file_info['size']} bytes")
```

---

### AzureBlobStorageBackend

`app/storage/azure_blob.py`

Azure Blob Storageの実装。

#### 使用例

```python
from app.storage.azure_blob import AzureBlobStorageBackend

# 接続文字列で初期化
storage = AzureBlobStorageBackend(
    connection_string="DefaultEndpointsProtocol=https;...",
    container_name="uploads"
)

# または Managed Identity で初期化
storage = AzureBlobStorageBackend(
    connection_string=None,  # DefaultAzureCredentialを使用
    container_name="uploads"
)

# ファイルアップロード
file_path = Path("documents/report.pdf")
content = b"PDF content here..."
file_id = await storage.upload(file_path, content)

# ファイルダウンロード
content = await storage.download(file_id)

# ファイル削除
await storage.delete(file_id)

# ファイル一覧
files = await storage.list_files()
```

---

## データベースユーティリティ

`app/database.py`

データベース接続とセッション管理。

### init_db()

データベースを初期化します。

#### シグネチャ

```python
async def init_db() -> None
```

##### 機能

- データベーステーブルの作成
- 非同期エンジンの初期化

##### 使用例

```python
from app.database import init_db

# アプリケーション起動時
await init_db()
```

---

### close_db()

データベース接続を閉じます。

#### シグネチャ

```python
async def close_db() -> None
```

##### 使用例

```python
from app.database import close_db

# アプリケーション終了時
await close_db()
```

---

### get_db()

データベースセッションを取得します（依存性注入用）。

#### シグネチャ

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]
```

##### 使用例

```python
from fastapi import Depends
from app.database import get_db

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SampleUser))
    users = result.scalars().all()
    return users
```

---

## 使用例の統合

### 完全なエンドポイント例

セキュリティ、ロギング、例外処理を統合した例。

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.logging import get_logger
from app.core.exceptions import NotFoundError, AuthenticationError
from app.core.security import verify_password, create_access_token

router = APIRouter()
logger = get_logger(__name__)

@router.post("/login")
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Login attempt for {email}")

    # ユーザー取得
    result = await db.execute(select(SampleUser).where(SampleUser.email == email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User not found: {email}")
        raise NotFoundError(message="User not found")

    # パスワード検証
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password for {email}")
        raise AuthenticationError(message="Invalid credentials")

    # トークン作成
    token = create_access_token(data={"sub": user.email})
    logger.info(f"Login successful for {email}")

    return {"access_token": token, "token_type": "bearer"}
```

---

## パフォーマンス最適化

### 非同期処理

すべてのI/O操作は非同期で実装されています。

```python
# 良い例：非同期処理
async def process_file(file_id: str):
    content = await storage.download(file_id)
    result = await process_content(content)
    return result

# 悪い例：同期処理（ブロッキング）
def process_file_sync(file_id: str):
    content = storage.download(file_id)  # ブロッキング
    result = process_content(content)
    return result
```

---

## 参考リンク

- [Passlib公式ドキュメント](https://passlib.readthedocs.io/)
- [python-jose公式ドキュメント](https://python-jose.readthedocs.io/)
- [Pythonロギング公式ドキュメント](https://docs.python.org/ja/3/library/logging.html)
- [Azure Storage Python SDK](https://learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python)
