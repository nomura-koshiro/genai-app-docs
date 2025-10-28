# セキュリティ - データ保護

このドキュメントでは、camp-backendにおけるデータレベルのセキュリティ保護機能について説明します。

## 目次

- [データベースセキュリティ](#データベースセキュリティ)
- [ファイルアップロードセキュリティ](#ファイルアップロードセキュリティ)

---

## データベースセキュリティ

### 1. SQLインジェクション対策

**実装場所**: `src/app/database.py`

#### SQLAlchemy ORM使用

- **パラメータ化クエリ**: 自動防御
- **非同期エンジン**: `create_async_engine()`使用
- **生SQLの使用なし**: すべてのクエリはORM経由

#### 接続プール設定

**実装場所**: `src/app/database.py:27-37`, `src/app/config.py:286-301`

接続プール設定は環境変数で設定可能です：

```python
# src/app/config.py
class Settings(BaseSettings):
    # データベース接続プール設定
    DB_POOL_SIZE: int = Field(default=5, description="通常時の接続プールサイズ")
    DB_MAX_OVERFLOW: int = Field(default=10, description="ピーク時の追加接続数")
    DB_POOL_RECYCLE: int = Field(default=1800, description="接続リサイクル時間（秒）")
    DB_POOL_PRE_PING: bool = Field(default=True, description="接続前のPINGチェック")
```

```python
# src/app/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # 設定から読み込み
    pool_size=settings.DB_POOL_SIZE,          # 設定から読み込み
    max_overflow=settings.DB_MAX_OVERFLOW,    # 設定から読み込み
    pool_recycle=settings.DB_POOL_RECYCLE,    # 設定から読み込み
    pool_timeout=30,
)
```

**設定方法**（環境変数または.envファイル）:

```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
```

### 2. リポジトリパターン

**実装場所**: `src/app/repositories/sample_user.py`

```python
# SQLAlchemy ORMを使用（安全）
async def get_by_email(self, email: str) -> SampleUser | None:
    result = await self.db.execute(
        select(SampleUser).where(SampleUser.email == email)
    )
    return result.scalar_one_or_none()
```

**セキュリティ効果**:

- すべてのクエリはSQLAlchemy ORMを経由
- パラメータバインディング自動適用
- SQLインジェクション攻撃を防止

### 2-2. N+1クエリ対策（Eager Loading）

**実装場所**: `src/app/repositories/base.py:83-97`

リポジトリの`get_multi()`メソッドに`load_relations`パラメータを追加し、
N+1クエリ問題を防止します。

```python
from sqlalchemy.orm import selectinload

async def get_multi(
    self,
    skip: int = 0,
    limit: int = 100,
    order_by: str | None = None,
    load_relations: list[str] | None = None,  # Eager loading用
    **filters: Any,
) -> list[ModelType]:
    query = select(self.model)

    # Eager loading（N+1クエリ対策）
    if load_relations:
        for relation in load_relations:
            if hasattr(self.model, relation):
                query = query.options(selectinload(getattr(self.model, relation)))

    # フィルタ、ソート、ページネーション...
    result = await self.db.execute(query)
    return list(result.scalars().all())
```

**使用例**:

```python
# N+1クエリが発生する場合（悪い例）
users = await user_repository.get_multi(limit=100)
for user in users:
    # 各ユーザーごとにクエリが発生（100+1クエリ）
    posts = user.posts

# Eager loadingで1クエリで取得（良い例）
users = await user_repository.get_multi(
    limit=100,
    load_relations=["posts"]  # postsを事前読み込み
)
for user in users:
    # 既に読み込まれている（追加クエリなし）
    posts = user.posts
```

**パフォーマンス効果**:

- リレーションデータを事前に一括取得
- N+1クエリ問題を防止
- データベース負荷を大幅削減

### 3. トランザクション管理

**実装場所**: `src/app/database.py:169-177`

#### 自動ロールバック

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()  # エラー時は自動ロールバック
            raise
        finally:
            await session.close()
```

**セキュリティ効果**:

- 例外発生時の自動ロールバック
- データ整合性の維持
- トランザクションリークの防止

---

## ファイルアップロードセキュリティ

**実装場所**: `src/app/api/routes/files.py`

### セキュリティ対策のまとめ

#### 1. ファイル拡張子チェック（50行目）

```python
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".dll"}
```

#### 2. MIME typeチェック（52-61行目）

```python
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "text/plain", "text/markdown",
    "application/zip",
}
```

#### 3. ファイルサイズ制限

- デフォルト: 10MB
- 環境変数で設定可能: `MAX_UPLOAD_SIZE`

#### 4. ファイル名サニタイゼーション（64-95行目）

```python
def sanitize_filename(filename: str) -> str:
    filename = re.sub(r"[^\w\s\-\.]", "", filename)
    filename = Path(filename).name
    return filename
```

#### 5. セキュアなファイルダウンロード（252行目）

```python
response.headers["X-Content-Type-Options"] = "nosniff"
```

**セキュリティ効果**:

- 悪意のある実行可能ファイルのアップロードを防止
- パストラバーサル攻撃を防止
- コンテンツスニッフィング攻撃を防止

---

## 関連ドキュメント

- [セキュリティ概要](./03-security.md) - セキュリティ機能の全体像
- [認証・認可](./03-security-authentication.md) - パスワードハッシュ化、JWT認証
- [リクエスト保護](./03-security-request-protection.md) - CORS、レート制限、入力バリデーション
- [インフラストラクチャ](./03-security-infrastructure.md) - エラーハンドリング、環境設定
- [ベストプラクティス](./03-security-best-practices.md) - セキュリティ強化の推奨事項

---
