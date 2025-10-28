# テックスタック - Webフレームワーク

このドキュメントでは、camp-backendのWebフレームワーク層で使用している技術について説明します。

## 目次

- [FastAPI](#fastapi)
- [Pydantic](#pydantic)
- [Alembic](#alembic)

---

## FastAPI

**バージョン**: 0.115.0+

FastAPIは、現代的で高速なPython Webフレームワークです。

### 主な特徴

- **高速**: NodeJS並みの高いパフォーマンス
- **自動ドキュメント生成**: Swagger UI / ReDoc
- **型ヒントベース**: Pydanticによる自動バリデーション
- **非同期サポート**: async/awaitのネイティブサポート
- **依存性注入**: 組み込みのDIシステム

### 基本的な使い方

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="camp-backend",
    version="0.1.0",
    description="camp-backend with file management",
)

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
async def root():
    """ルートエンドポイント。"""
    return {"message": "Hello World"}

@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    """アイテムを作成する。"""
    return item

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """アイテムを取得する。"""
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

### ミドルウェア

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# カスタムミドルウェア
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # リクエスト前の処理
        print(f"Request: {request.method} {request.url}")

        response = await call_next(request)

        # レスポンス後の処理
        print(f"Response: {response.status_code}")
        return response

app.add_middleware(CustomMiddleware)
```

### 公式ドキュメント

- <https://fastapi.tiangolo.com/>

---

## Pydantic

**バージョン**: 2.6.0+

Pydanticは、Pythonの型ヒントを使用したデータバリデーションライブラリです。

### 主な特徴

- **型安全**: 自動的な型変換とバリデーション
- **高速**: Rustで実装されたコア
- **エラーメッセージ**: わかりやすいバリデーションエラー
- **JSON Schema**: 自動生成

### スキーマ定義

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

class SampleUserCreate(BaseModel):
    """ユーザー作成リクエスト。"""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """ユーザー名は英数字のみ許可。"""
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

class SampleUserResponse(BaseModel):
    """ユーザーレスポンス。"""

    id: int
    email: str
    username: str
    created_at: datetime

    # ORMモデルから変換を許可
    model_config = {"from_attributes": True}

class SampleUserUpdate(BaseModel):
    """ユーザー更新リクエスト。"""

    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)

    # すべてのフィールドがオプショナル
```

### バリデーションの使用

```python
from pydantic import ValidationError

# 正常なケース
user_data = SampleUserCreate(
    email="user@example.com",
    username="testuser",
    password="password123"
)
print(user_data.email)  # user@example.com

# エラーケース
try:
    invalid_user = SampleUserCreate(
        email="invalid-email",  # 無効なメールアドレス
        username="ab",  # 短すぎる
        password="123"  # 短すぎる
    )
except ValidationError as e:
    print(e.json())  # 詳細なエラー情報
```

### 設定管理

```python
from pydantic_settings import BaseSettings
import os
from pathlib import Path

def get_env_file() -> tuple[str, ...]:
    """環境に応じた.envファイルのパスを取得"""
    environment = os.getenv("ENVIRONMENT", "development")
    env_mapping = {
        "development": "local",
        "staging": "staging",
        "production": "production",
    }
    env_name = env_mapping.get(environment, "local")
    env_specific = Path(f".env.{env_name}")
    return (str(env_specific),) if env_specific.exists() else (".env",)

class Settings(BaseSettings):
    """アプリケーション設定。"""

    APP_NAME: str = "camp-backend"
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

    model_config = {
        "env_file": get_env_file(),  # 環境別ファイルを動的に読み込み
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

# 環境変数から自動読み込み
settings = Settings()
```

### 公式ドキュメント

- <https://docs.pydantic.dev/>

---

## Alembic

**バージョン**: 1.13.0+

Alembicは、SQLAlchemyのためのデータベースマイグレーションツールです。

### 主な特徴

- **バージョン管理**: データベーススキーマの履歴管理
- **自動生成**: モデルから自動的にマイグレーション生成
- **ロールバック**: 以前のバージョンに戻すことが可能
- **ブランチ**: 複数の開発ブランチをサポート

### 基本的な使い方

```powershell
# 初期化
alembic init alembic

# マイグレーションの自動生成
alembic revision --autogenerate -m "Add users table"

# マイグレーションの適用
alembic upgrade head

# ロールバック
alembic downgrade -1

# 現在のバージョンを確認
alembic current

# 履歴を表示
alembic history
```

### マイグレーションファイル

```python
# alembic/versions/xxxx_add_users_table.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """アップグレード処理。"""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sample_users_email', 'users', ['email'], unique=True)

def downgrade():
    """ダウングレード処理。"""
    op.drop_index('ix_sample_users_email', 'users')
    op.drop_table('users')
```

### 公式ドキュメント

- <https://alembic.sqlalchemy.org/>

---

## 関連ドキュメント

- [テックスタック概要](./01-tech-stack.md) - 技術スタック全体像
- [データレイヤー](./01-tech-stack-data.md) - PostgreSQL、SQLAlchemy、Redis
- [AI・開発ツール](./01-tech-stack-ai-tools.md) - LangChain/LangGraph、uv、Ruff、pytest、Prometheus

---
