---
title: Fix Backend Issues
description: Python、FastAPI、データベース、またはデプロイ問題を修正
tools: [Read, Edit, MultiEdit, Bash, Grep]
---

@backend-developer

バックエンドの問題「$ARGUMENTS」を修正してください。

## 問題診断・修正手順

### 1. 問題分析フェーズ

#### Python・FastAPI エラーの場合

```bash
# 構文・型エラーチェック
cd apps/backend && python -m py_compile app/main.py
cd apps/backend && mypy app/ --show-error-codes

# 依存関係チェック
cd apps/backend && pip check

# FastAPI サーバー起動確認
cd apps/backend && uvicorn app.main:app --reload --log-level debug
```

#### データベース関連エラー

```bash
# データベース接続確認
cd apps/backend && python -c "from app.db.session import engine; print('DB Connection OK')"

# マイグレーション状態確認
cd apps/backend && alembic current
cd apps/backend && alembic history

# テーブル状態確認
cd apps/backend && python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.reflect(bind=engine); print(list(Base.metadata.tables.keys()))"
```

#### テスト失敗の場合

```bash
# 詳細なテスト実行
cd apps/backend && python -m pytest -v -s --tb=long

# 特定テストの実行
cd apps/backend && python -m pytest tests/api/v1/test_users.py::test_create_user -v -s
```

### 2. 一般的な問題と修正方法

#### ImportError / ModuleNotFoundError

```python
# ❌ 問題のあるインポート
from models.user import User  # 相対インポート問題
from .schemas import UserCreate  # パッケージ構造問題

# ✅ 修正後
from app.models.user import User  # 絶対インポート
from app.schemas.user import UserCreate  # 明確なパス
```

#### SQLAlchemy エラー

```python
# ❌ よくある問題
# 1. セッション管理エラー
def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    return user  # セッションが閉じられていない

# 2. リレーションシップエラー
user.posts  # LazyLoadingError - セッション外でのアクセス

# ✅ 修正方法
# 1. 適切なセッション管理
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# 2. Eager Loading
def get_user_with_posts(db: Session, user_id: int):
    return db.query(User).options(joinedload(User.posts)).filter(User.id == user_id).first()
```

#### Pydantic バリデーションエラー

```python
# ❌ 問題のあるスキーマ
class UserCreate(BaseModel):
    email: str  # バリデーション不足
    age: int    # 範囲チェックなし

# ✅ 修正後
from pydantic import EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="有効なメールアドレス")
    age: int = Field(..., ge=0, le=150, description="年齢（0-150）")

    @field_validator('email')
    @classmethod
    def validate_email_not_empty(cls, v):
        if not v.strip():
            raise ValueError('メールアドレスは必須です')
        return v.strip()
```

#### FastAPI ルーティングエラー

```python
# ❌ よくある問題
@router.get("/users/{user_id}")
@router.get("/users/me")  # パスの競合

# ✅ 修正方法（順序を変更）
@router.get("/users/me")  # より具体的なパスを先に定義
@router.get("/users/{user_id}")
```

### 3. データベース問題の修正

#### マイグレーションエラー

```bash
# マイグレーション履歴の確認
cd apps/backend && alembic history --verbose

# 問題のあるマイグレーションをロールバック
cd apps/backend && alembic downgrade -1

# マイグレーションファイルの再生成
cd apps/backend && alembic revision --autogenerate -m "Fix migration"

# 手動でマイグレーションファイル編集後
cd apps/backend && alembic upgrade head
```

#### 外部キー制約エラー

```python
# ❌ 問題：外部キー制約違反
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    db.delete(user)  # 関連データが存在する場合エラー
    db.commit()

# ✅ 修正：関連データの処理
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 関連データを先に削除またはnullに設定
    db.query(Post).filter(Post.user_id == user_id).delete()

    db.delete(user)
    db.commit()
    return user
```

### 4. パフォーマンス問題の修正

#### N+1クエリ問題

```python
# ❌ N+1問題
def get_users_with_posts():
    users = db.query(User).all()
    for user in users:
        posts = user.posts  # 各ユーザーごとにクエリ実行
        print(f"{user.name}: {len(posts)} posts")

# ✅ 修正：Eager Loading
def get_users_with_posts():
    users = db.query(User).options(joinedload(User.posts)).all()
    for user in users:
        print(f"{user.name}: {len(user.posts)} posts")
```

#### 大量データ処理

```python
# ❌ メモリ使用量が多い
def process_all_users():
    users = db.query(User).all()  # 全データをメモリにロード
    for user in users:
        process_user(user)

# ✅ 修正：バッチ処理
def process_all_users():
    batch_size = 1000
    offset = 0

    while True:
        users = db.query(User).offset(offset).limit(batch_size).all()
        if not users:
            break

        for user in users:
            process_user(user)

        offset += batch_size
```

### 5. 認証・セキュリティ問題の修正

#### JWT トークンエラー

```python
# ❌ 問題：トークンデコードエラー
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # エラーハンドリング不足

# ✅ 修正：適切なエラーハンドリング
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user
```

#### SQLインジェクション対策

```python
# ❌ 危険：SQLインジェクション脆弱性
def search_users(name: str):
    query = f"SELECT * FROM users WHERE name = '{name}'"
    return db.execute(query).fetchall()

# ✅ 安全：ORMまたはパラメータ化クエリ
def search_users(db: Session, name: str):
    return db.query(User).filter(User.name == name).all()

# またはパラメータ化クエリ
def search_users_raw(name: str):
    query = "SELECT * FROM users WHERE name = :name"
    return db.execute(text(query), {"name": name}).fetchall()
```

### 6. 環境・設定問題の修正

#### 環境変数の問題

```python
# ❌ 問題：環境変数が読み込まれない
DATABASE_URL = os.getenv("DATABASE_URL")  # Noneの可能性

# ✅ 修正：デフォルト値とバリデーション
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/training_tracker"
    secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

#### CORS設定エラー

```python
# ❌ 問題：CORS エラー
app = FastAPI()

# ✅ 修正：適切なCORS設定
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7. テスト関連問題の修正

#### テストデータベース分離

```python
# conftest.py での適切な設定
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base

# テスト用データベース
SQLALCHEMY_DATABASE_URL = "postgresql://localhost/training_tracker_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)
```

### 8. デプロイ・本番環境問題

#### ログ設定

```python
# ❌ 問題：適切でないログ設定
print("User created")  # 本番で使うべきでない

# ✅ 修正：構造化ログ
import structlog

logger = structlog.get_logger(__name__)

def create_user(user_data: UserCreate):
    user = User(**user_data.dict())
    db.add(user)
    db.commit()

    logger.info(
        "User created successfully",
        user_id=user.id,
        email=user.email,
        action="user_create"
    )
    return user
```

### 9. 修正後の検証

#### 自動テスト実行

```bash
# 型チェック
cd apps/backend && mypy app/

# リント実行
cd apps/backend && ruff check app/ --fix

# 全テスト実行
cd apps/backend && python -m pytest

# セキュリティチェック
cd apps/backend && bandit -r app/

# パフォーマンステスト
cd apps/backend && python -m pytest tests/ -k "performance"
```

#### 手動確認

```bash
# サーバー起動確認
cd apps/backend && uvicorn app.main:app --reload

# API ドキュメント確認
# http://localhost:8000/docs にアクセス

# ヘルスチェック
curl http://localhost:8000/api/v1/health
```

### 10. 修正内容の文書化

修正完了後、以下を記録してください：

- **問題の原因**: 根本的な原因
- **修正内容**: 具体的な変更点
- **影響範囲**: 修正による影響
- **テスト結果**: 修正後のテスト実行結果
- **防止策**: 同様の問題を防ぐための対策

修正内容と根本原因の分析結果を報告してください。
