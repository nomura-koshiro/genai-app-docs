# Azure マネージドID による PostgreSQL 接続

このドキュメントは、Azure マネージドID を使用して PostgreSQL に接続する実装方法の調査結果をまとめたものです。

## 調査概要

- **調査日**: 2025-11-21
- **目的**: AzureのマネージドIDでPostgreSQLに接続し、ローカル環境では使用しない実装の検討
- **結論**: ✅ **実装可能**

## 現在の実装状況

### 1. データベース接続

**ファイル**: `src/app/core/database.py:68-77`

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # 接続前のPINGチェック
    pool_size=settings.DB_POOL_SIZE,           # 接続プールサイズ
    max_overflow=settings.DB_MAX_OVERFLOW,     # プールが満杯の場合の追加接続数
    pool_recycle=settings.DB_POOL_RECYCLE,     # 接続リサイクル時間（秒）
    pool_timeout=30,
)
```

- `create_async_engine(settings.DATABASE_URL)` でPostgreSQL接続
- 接続プール設定あり（pool_size=5, max_overflow=10）
- 接続リサイクル: 1800秒（30分）

### 2. 設定管理

**ファイル**: `src/app/core/config.py:273`

```python
DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"
```

- `DATABASE_URL` は環境変数から読み込み
- デフォルト: ローカル開発用の接続文字列

### 3. 依存関係

**ファイル**: `pyproject.toml:29`

```toml
dependencies = [
    ...
    "azure-identity>=1.19.0",  # ✅ すでにインストール済み
    ...
]
```

- ✅ **`azure-identity>=1.19.0` がすでにインストール済み**（実装に必要なライブラリ）

## Azure マネージドID 認証の仕組み

### 認証フロー

```python
from azure.identity import DefaultAzureCredential

# 1. トークン取得
credential = DefaultAzureCredential()
token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

# 2. トークンをパスワードとして使用
DATABASE_URL = f"postgresql+asyncpg://{username}:{token.token}@{host}/{database}"

# 3. SQLAlchemyで接続
engine = create_async_engine(DATABASE_URL)
```

### 重要なポイント

| 項目 | 説明 |
|------|------|
| **DefaultAzureCredential()** | Azure環境ではマネージドID、ローカルではAzure CLI認証を自動選択 |
| **スコープURL** | `https://ossrdbms-aad.database.windows.net/.default` (固定値) |
| **トークン形式** | `token.token` で文字列として取得 |
| **トークン有効期限** | 24時間（自動更新が必要） |

### Azure サンプルコード

Azure公式サンプル（[azure-postgres-pgvector-python](https://github.com/Azure-Samples/azure-postgres-pgvector-python/blob/main/examples/asyncpg_items.py)）から抜粋:

```python
from azure.identity import DefaultAzureCredential
import asyncpg

# トークン取得
azure_credential = DefaultAzureCredential()
token = azure_credential.get_token(
    "https://ossrdbms-aad.database.windows.net/.default"
)
POSTGRES_PASSWORD = token.token

# 接続文字列構築
DATABASE_URI = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"

# 非同期接続
conn = await asyncpg.connect(DATABASE_URI)
```

## 実装方針

### 1. ローカル/Azure環境の判定方法

実装可能な判定方法を比較:

| 方法 | メリット | デメリット | 推奨度 |
|------|----------|-----------|--------|
| **①環境変数フラグ** | 明示的で制御しやすい<br>意図が明確<br>テストしやすい | 設定が1つ増える | ⭐⭐⭐ |
| ②ホスト名判定 | 自動判定可能<br>設定不要 | ロジックが複雑<br>保守性が低い | ⭐⭐ |
| ③パスワード空判定 | シンプル | 意図が不明瞭<br>エラーハンドリング困難 | ⭐ |

### 2. 推奨実装（環境変数フラグ方式）

#### 環境変数設定

**ローカル環境（.env.local）:**

```bash
# マネージドID無効
USE_MANAGED_IDENTITY=false
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db
```

**本番環境（.env.production）:**

```bash
# マネージドID有効
USE_MANAGED_IDENTITY=true
DATABASE_URL=postgresql+asyncpg://appuser@prod-db.postgres.database.azure.com/camp_backend_db
```

**ステージング環境（.env.staging）:**

```bash
# マネージドID有効
USE_MANAGED_IDENTITY=true
DATABASE_URL=postgresql+asyncpg://appuser@staging-db.postgres.database.azure.com/camp_backend_db_staging
```

### 3. トークン更新戦略

| 項目 | 設定値 | 説明 |
|------|--------|------|
| **トークン有効期限** | 24時間 | Azure Entra IDが発行 |
| **接続リサイクル** | 1800秒（30分） | `DB_POOL_RECYCLE`で設定済み |
| **接続前チェック** | 有効 | `DB_POOL_PRE_PING=true`で設定済み |

**結論**: 現在の接続プール設定（30分リサイクル）により、トークン有効期限（24時間）内で自動更新される。追加の実装は不要。

## 実装案

### 修正が必要なファイル

#### 1. src/app/core/config.py - 設定追加

```python
class Settings(BaseSettings):
    # ... 既存の設定 ...

    # データベースマネージド ID認証設定
    USE_MANAGED_IDENTITY: bool = Field(
        default=False,
        description="Azure Managed Identity を使用したDB認証を有効化",
    )
```

#### 2. src/app/core/database.py - 接続ロジック修正

```python
from urllib.parse import urlparse, urlunparse
from azure.identity import DefaultAzureCredential
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_database_url() -> str:
    """環境に応じたDATABASE_URLを取得します.

    Azure Managed Identity が有効な場合、トークンを取得してパスワード部分に設定します。
    ローカル環境では通常のパスワード認証を使用します。

    Returns:
        str: データベース接続URL
    """
    if not settings.USE_MANAGED_IDENTITY:
        logger.info("データベース接続: パスワード認証を使用")
        return settings.DATABASE_URL

    logger.info("データベース接続: Azure Managed Identity を使用")

    try:
        # トークン取得
        credential = DefaultAzureCredential()
        token = credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        )

        # URLをパース
        parsed = urlparse(settings.DATABASE_URL)

        # パスワード部分にトークンを設定
        # 形式: postgresql+asyncpg://username:token@host:port/database
        netloc = f"{parsed.username}:{token.token}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"

        # URL再構築
        db_url = urlunparse(
            parsed._replace(netloc=netloc)
        )

        logger.info(
            "マネージドIDトークン取得成功",
            username=parsed.username,
            host=parsed.hostname,
        )
        return db_url

    except Exception as e:
        logger.error(
            "マネージドIDトークン取得失敗",
            error=str(e),
            exc_info=True,
        )
        raise


# 非同期エンジンを作成（環境別の接続プール設定）
engine = create_async_engine(
    get_database_url(),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=30,
)
```

#### 3. .env.production.example - 環境変数追加

```bash
# ==============================================================================
# Azure Managed Identity設定
# ==============================================================================
# Azure環境でのマネージドID認証を有効化
USE_MANAGED_IDENTITY=true

# マネージドID使用時はパスワード部分を省略
# 形式: postgresql+asyncpg://username@host.database.azure.com/database
DATABASE_URL=postgresql+asyncpg://appuser@prod-db.postgres.database.azure.com/camp_backend_db
```

#### 4. .env.staging.example - 環境変数追加

```bash
# ==============================================================================
# Azure Managed Identity設定
# ==============================================================================
USE_MANAGED_IDENTITY=true
DATABASE_URL=postgresql+asyncpg://appuser@staging-db.postgres.database.azure.com/camp_backend_db_staging
```

#### 5. .env.local.example - コメント追加

```bash
# ==============================================================================
# データベース設定（PostgreSQL）
# ==============================================================================
# ローカル開発環境ではマネージドIDを使用しない
USE_MANAGED_IDENTITY=false
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db
```

## セキュリティ考慮事項

### 1. ローカル環境での保護

| 項目 | 設定 | 理由 |
|------|------|------|
| **USE_MANAGED_IDENTITY** | `false` | ローカルではパスワード認証を使用 |
| **Azure認証情報** | 不要 | ローカルDBは通常のパスワード認証 |
| **環境分離** | 明示的 | フラグで明確に制御 |

### 2. 本番環境での保護

| 項目 | 設定 | 理由 |
|------|------|------|
| **USE_MANAGED_IDENTITY** | `true` | マネージドID認証を強制 |
| **パスワード不要** | DATABASE_URLにパスワード不要 | トークンベース認証 |
| **トークン自動更新** | 接続プール設定で対応 | 30分ごとにリサイクル |

### 3. トークン管理

- ✅ トークン有効期限: 24時間
- ✅ 接続リサイクル: 30分（有効期限内）
- ✅ 接続前チェック: `pool_pre_ping=true`で自動検証
- ⚠️ トークンはメモリ内のみ（ログ出力禁止）

## Azure PostgreSQL 側の設定要件

### 1. Entra ID 認証の有効化

Azure Database for PostgreSQL で Microsoft Entra ID（旧Azure AD）認証を有効化する必要があります。

**Azure Portal での設定:**

1. Azure Database for PostgreSQL リソースに移動
2. **設定** → **認証** を選択
3. **Microsoft Entra 認証** を有効化
4. Entra ID 管理者を設定

### 2. マネージドID のデータベースユーザー作成

```sql
-- 1. Azure Entra ID管理者でPostgreSQLに接続

-- 2. マネージドIDのユーザーを作成
-- マネージドID名を使用（例: my-app-managed-identity）
CREATE ROLE "my-app-managed-identity" WITH LOGIN;

-- 3. 必要な権限を付与
GRANT CONNECT ON DATABASE camp_backend_db TO "my-app-managed-identity";
GRANT USAGE ON SCHEMA public TO "my-app-managed-identity";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "my-app-managed-identity";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "my-app-managed-identity";

-- 4. 将来作成されるテーブルへの権限も付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "my-app-managed-identity";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "my-app-managed-identity";
```

### 3. Azure App Service でのマネージドID設定

**システム割り当てマネージドIDの有効化:**

1. Azure App Service リソースに移動
2. **設定** → **ID** を選択
3. **システム割り当て済み** タブで **状態** を **オン** に設定
4. **保存** をクリック

**DATABASE_URL環境変数の設定:**

App Service の **構成** → **アプリケーション設定** で以下を追加:

```
USE_MANAGED_IDENTITY=true
DATABASE_URL=postgresql+asyncpg://my-app-managed-identity@prod-db.postgres.database.azure.com/camp_backend_db
```

## テスト方法

### 1. ローカル環境でのテスト

```bash
# .env.local を確認
USE_MANAGED_IDENTITY=false
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db

# アプリケーション起動
uv run python -m uvicorn app.main:app --reload

# ログで接続方法を確認
# "データベース接続: パスワード認証を使用" が表示されるはず
```

### 2. Azure環境でのテスト（ステージング）

```bash
# Azure App Service にデプロイ

# アプリケーション設定を確認
USE_MANAGED_IDENTITY=true

# アプリケーションログを確認
az webapp log tail --name <app-name> --resource-group <resource-group>

# 期待されるログ:
# "データベース接続: Azure Managed Identity を使用"
# "マネージドIDトークン取得成功"
```

### 3. 接続テスト用エンドポイント（オプション）

開発・デバッグ用に接続確認エンドポイントを追加できます:

```python
# src/app/api/routes/system/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health/db")
async def check_database_health(db: AsyncSession = Depends(get_db)):
    """データベース接続をチェック"""
    try:
        result = await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "auth_method": "managed_identity" if settings.USE_MANAGED_IDENTITY else "password",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. トークン取得エラー

**エラー**: `DefaultAzureCredential failed to retrieve a token`

**原因**:
- マネージドIDが有効化されていない
- Azure環境で実行されていない（ローカルでマネージドID使用）

**解決方法**:
```bash
# ローカル環境の場合
USE_MANAGED_IDENTITY=false

# Azure環境の場合
# App Service の ID 設定を確認
# システム割り当てマネージドIDが「オン」になっているか確認
```

#### 2. PostgreSQL接続エラー

**エラー**: `password authentication failed for user "appuser"`

**原因**:
- PostgreSQL側でマネージドIDユーザーが作成されていない
- Entra ID認証が有効化されていない

**解決方法**:
```sql
-- Entra ID管理者として接続
CREATE ROLE "my-app-managed-identity" WITH LOGIN;
GRANT CONNECT ON DATABASE camp_backend_db TO "my-app-managed-identity";
```

#### 3. トークン有効期限切れ

**エラー**: 長時間実行後に接続エラー

**原因**:
- トークンの有効期限（24時間）切れ
- 接続プールのリサイクルが機能していない

**解決方法**:
```python
# database.py で接続プール設定を確認
pool_recycle=1800,  # 30分（1800秒）
pool_pre_ping=True,  # 接続前チェック有効
```

#### 4. ローカルで誤ってマネージドIDを使用

**エラー**: ローカル環境でトークン取得失敗

**原因**:
- `USE_MANAGED_IDENTITY=true` が設定されている

**解決方法**:
```bash
# .env.local を確認・修正
USE_MANAGED_IDENTITY=false
```

## まとめ

### 実装可能性

✅ **実装可能** - 以下の理由から実装は十分可能です:

1. **依存関係**: `azure-identity` がすでにインストール済み
2. **接続プール**: トークン自動更新に対応する設定が既に存在
3. **環境分離**: 環境変数で簡単にローカル/Azure環境を切り替え可能

### 推奨実装順序

1. **設定追加** - `config.py` に `USE_MANAGED_IDENTITY` フラグ追加
2. **接続ロジック修正** - `database.py` に `get_database_url()` 関数実装
3. **環境変数更新** - `.env.*.example` ファイルに設定追加
4. **Azure設定** - PostgreSQL で Entra ID 認証有効化
5. **ユーザー作成** - マネージドID用のデータベースユーザー作成
6. **テスト** - ローカル→ステージング→本番の順でテスト

### メリット

| メリット | 説明 |
|---------|------|
| **セキュリティ向上** | パスワード不要、トークンベース認証 |
| **運用簡素化** | パスワードローテーション不要 |
| **環境分離** | ローカルは通常認証、AzureはマネージドID |
| **自動更新** | 接続プール設定でトークン自動更新 |

### 注意点

| 注意点 | 対策 |
|--------|------|
| **トークン有効期限** | 接続プール設定（30分リサイクル）で対応済み |
| **Azure依存** | 環境変数フラグで切り替え可能 |
| **初期設定** | PostgreSQL側でEntra ID認証とユーザー作成が必要 |

## 参考資料

- [Azure Database for PostgreSQL - Managed Identity 接続](https://learn.microsoft.com/ja-jp/azure/postgresql/flexible-server/security-connect-with-managed-identity)
- [Azure Identity SDK for Python](https://learn.microsoft.com/ja-jp/python/api/overview/azure/identity-readme)
- [Azure Samples - PostgreSQL with Python](https://github.com/Azure-Samples/azure-postgres-pgvector-python)
- [SQLAlchemy - Async Engine](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

**最終更新**: 2025-11-21
**ステータス**: 調査完了 - 実装待ち
