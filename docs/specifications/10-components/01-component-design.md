# コンポーネント設計書

## 1. 概要

本文書は、genai-app-docsシステムの主要コンポーネントの設計を定義します。
再利用可能で保守性の高いコンポーネントにより、効率的な開発を実現します。

### 1.1 コンポーネント設計方針

- **DRY（Don't Repeat Yourself）**: 重複コードの排除
- **単一責任の原則**: 1つのコンポーネントは1つの責務
- **高凝集・低結合**: コンポーネント間の依存を最小化
- **型安全性**: Genericsによる型安全な実装

---

## 2. コンポーネント全体図

::: mermaid
graph TB
    subgraph "Data Access Layer"
        BaseRepo[BaseRepository<T, ID><br/>汎用CRUD]
        ProjectRepo[ProjectRepository]
        UserRepo[UserAccountRepository]
    end

    subgraph "Service Layer"
        ProjectService[ProjectService]
        UserService[UserAccountService]
        StorageService[StorageService<br/>Strategy Pattern]
    end

    subgraph "Decorators"
        Basic[Basic Decorators<br/>@measure_performance<br/>@handle_service_errors]
        DataAccess[Data Access Decorators<br/>@database_transaction<br/>@cache_result]
        Reliability[Reliability Decorators<br/>@async_timeout<br/>@retry]
        Security[Security Decorators<br/>@require_permissions<br/>@audit_log]
    end

    subgraph "Utilities"
        Cache[CacheManager<br/>Redis]
        Logger[StructuredLogger<br/>structlog]
    end

    ProjectRepo --> BaseRepo
    UserRepo --> BaseRepo

    ProjectService --> ProjectRepo
    UserService --> UserRepo
    ProjectService --> StorageService

    ProjectService --> Basic
    ProjectService --> DataAccess
    ProjectService --> Reliability
    ProjectService --> Security

    DataAccess --> Cache
    Basic --> Logger

    style BaseRepo fill:#4CAF50
    style StorageService fill:#2196F3
    style DataAccess fill:#FF9800
:::

---

## 3. BaseRepository（汎用リポジトリ）

### 3.1 アーキテクチャ

::: mermaid
graph LR
    Service[Service Layer] --> BaseRepo[BaseRepository<T, ID>]
    BaseRepo --> ORM[SQLAlchemy 2.0<br/>AsyncSession]
    ORM --> DB[(PostgreSQL)]

    BaseRepo --> CRUD[CRUD Operations]
    BaseRepo --> Filter[Filter Support]
    BaseRepo --> Relations[N+1 Prevention]

    style BaseRepo fill:#4CAF50
    style CRUD fill:#8BC34A
    style Filter fill:#AED581
:::

### 3.2 実装

**実装**: `src/app/repositories/base.py` (486行)

```python
from typing import Generic, TypeVar, Type, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

ModelType = TypeVar("ModelType")
IDType = TypeVar("IDType")

class BaseRepository(Generic[ModelType, IDType]):
    """汎用リポジトリ基底クラス"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(
        self,
        db: AsyncSession,
        id: IDType
    ) -> ModelType | None:
        """ID取得"""
        return await db.get(self.model, id)

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        load_relations: list[str] | None = None,
        **filters
    ) -> list[ModelType]:
        """複数取得（N+1対策付き）"""
        stmt = select(self.model)

        # リレーションシップの事前読み込み（N+1対策）
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    stmt = stmt.options(
                        selectinload(getattr(self.model, relation))
                    )

        # フィルタ適用（セキュリティ：不正なキーは無視）
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
            else:
                logger.warning(f"Invalid filter key: {key}")

        # ソート
        if order_by and hasattr(self.model, order_by):
            stmt = stmt.order_by(getattr(self.model, order_by))

        # ページネーション
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        **obj_in
    ) -> ModelType:
        """作成（flush()のみ、commit()は呼び出し側）"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        **update_data
    ) -> ModelType:
        """更新"""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        id: IDType
    ) -> None:
        """削除"""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()

    async def count(
        self,
        db: AsyncSession,
        **filters
    ) -> int:
        """カウント"""
        stmt = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await db.execute(stmt)
        return result.scalar()
:::

### 3.3 主要機能

::: mermaid
mindmap
  root((BaseRepository))
    CRUD操作
      get: ID取得
      get_multi: 複数取得
      create: 作成
      update: 更新
      delete: 削除
      count: カウント
    N+1対策
      selectinload
      joinedload
      load_relations引数
    セキュリティ
      不正フィルタキー無視
      属性検証
      警告ログ出力
    ページネーション
      skip/limit
      order_by
    型安全性
      Generics<ModelType, IDType>
      型推論
:::

### 3.4 使用例

```python
# リポジトリ定義
class ProjectRepository(BaseRepository[Project, UUID]):
    def __init__(self):
        super().__init__(Project)

# 使用
repo = ProjectRepository()

# ID取得
project = await repo.get(db, project_id)

# 複数取得（N+1対策付き）
projects = await repo.get_multi(
    db,
    skip=0,
    limit=20,
    load_relations=["members", "files"],  # N+1対策
    is_active=True  # フィルタ
)

# 作成
project = await repo.create(
    db,
    name="New Project",
    code="NEW_PROJECT"
)

# 更新
project = await repo.update(
    db,
    db_obj=project,
    name="Updated Name"
)
```

---

## 4. デコレータ

### 4.1 デコレータ全体図

::: mermaid
graph TB
    Function[Service Function]

    Function --> Basic[Basic Decorators]
    Function --> DataAccess[Data Access Decorators]
    Function --> Reliability[Reliability Decorators]
    Function --> Security[Security Decorators]

    Basic --> Perf[@measure_performance<br/>実行時間計測]
    Basic --> Error[@handle_service_errors<br/>エラーハンドリング]

    DataAccess --> Tx[@database_transaction<br/>トランザクション管理]
    DataAccess --> Cache[@cache_result<br/>Redisキャッシュ]

    Reliability --> Timeout[@async_timeout<br/>タイムアウト制御]
    Reliability --> Retry[@retry<br/>リトライ機構]

    Security --> Perm[@require_permissions<br/>権限チェック]
    Security --> RateLimit[@rate_limit<br/>レート制限]
    Security --> Audit[@audit_log<br/>監査ログ]

    style Basic fill:#4CAF50
    style DataAccess fill:#2196F3
    style Reliability fill:#FF9800
    style Security fill:#F44336
:::

### 4.2 Basic Decorators

**実装**: `src/app/api/decorators/basic.py` (8,826バイト)

#### 4.2.1 @measure_performance

```python
import time
from functools import wraps
from app.core.logging import logger

def measure_performance(func):
    """実行時間計測デコレータ"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                f"{func.__name__} completed",
                function=func.__name__,
                duration_ms=round(duration_ms, 2)
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                f"{func.__name__} failed",
                function=func.__name__,
                duration_ms=round(duration_ms, 2),
                error=str(e)
            )
            raise

    return wrapper
:::

**使用例:**

```python
@measure_performance
async def get_projects(db: AsyncSession, skip: int = 0, limit: int = 100):
    """プロジェクト一覧取得（パフォーマンス計測付き）"""
    return await project_repo.get_multi(db, skip=skip, limit=limit)
```

#### 4.2.2 @handle_service_errors

```python
from fastapi import HTTPException, status

def handle_service_errors(func):
    """サービスエラーハンドリング（RFC 9457準拠）"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

        except BusinessRuleViolationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except PermissionDeniedError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )

        except Exception as e:
            logger.exception("Unhandled service error", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    return wrapper
```

---

### 4.3 Data Access Decorators

**実装**: `src/app/api/decorators/data_access.py` (7,699バイト)

#### 4.3.1 @database_transaction

```python
def database_transaction(func):
    """データベーストランザクション管理デコレータ"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # dbセッション取得（引数またはkwargs）
        db = kwargs.get("db") or next(
            (arg for arg in args if isinstance(arg, AsyncSession)),
            None
        )

        if not db:
            raise ValueError("AsyncSession not found in arguments")

        try:
            result = await func(*args, **kwargs)
            await db.commit()
            return result

        except Exception as e:
            await db.rollback()
            logger.error("Transaction rolled back", error=str(e))
            raise

    return wrapper
```

**使用例:**

```python
@database_transaction
async def create_project_with_member(
    db: AsyncSession,
    project_data: ProjectCreate,
    creator_id: UUID
) -> Project:
    """プロジェクトとメンバーを同一トランザクションで作成"""

    # プロジェクト作成（flush）
    project = await project_repo.create(db, **project_data.dict())

    # メンバー追加（flush）
    await member_repo.create(
        db,
        project_id=project.id,
        user_id=creator_id,
        project_role=ProjectRole.PROJECT_MANAGER
    )

    # デコレータが自動commit
    return project
```

#### 4.3.2 @cache_result

```python
import json
import hashlib
from redis import asyncio as redis

def cache_result(ttl: int = 300):
    """Redisキャッシュデコレータ（TTL秒）"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュキー生成
            cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # キャッシュチェック
            cached_value = await redis_client.get(cache_key)
            if cached_value:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached_value)

            # 関数実行
            result = await func(*args, **kwargs)

            # キャッシュ保存
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )

            logger.debug(f"Cache set: {cache_key}, TTL: {ttl}s")
            return result

        return wrapper
    return decorator

def _generate_cache_key(func_name: str, args, kwargs) -> str:
    """キャッシュキー生成"""
    key_data = {
        "function": func_name,
        "args": str(args),
        "kwargs": str(sorted(kwargs.items()))
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return f"cache:{hashlib.md5(key_str.encode()).hexdigest()}"
```

**使用例:**

```python
@cache_result(ttl=600)  # 10分間キャッシュ
async def get_project_summary(db: AsyncSession, project_id: UUID) -> dict:
    """プロジェクト概要取得（キャッシュ付き）"""
    project = await project_repo.get(db, project_id)
    members = await member_repo.get_by_project(db, project_id)

    return {
        "project": project,
        "member_count": len(members),
        "file_count": await file_repo.count(db, project_id=project_id)
    }
```

---

### 4.4 Reliability Decorators

**実装**: `src/app/api/decorators/reliability.py` (4,756バイト)

#### 4.4.1 @async_timeout

```python
import asyncio

def async_timeout(seconds: int = 30):
    """非同期タイムアウトデコレータ"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"{func.__name__} timed out",
                    function=func.__name__,
                    timeout_seconds=seconds
                )
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Operation timed out after {seconds} seconds"
                )

        return wrapper
    return decorator
```

#### 4.4.2 @retry

```python
import asyncio
from typing import Type

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
):
    """リトライデコレータ（指数バックオフ）"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts",
                            function=func.__name__,
                            error=str(e)
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed, retrying",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        next_delay=current_delay
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1

        return wrapper
    return decorator
```

**使用例:**

```python
@retry(max_attempts=3, delay=1.0, backoff=2.0)
@async_timeout(seconds=30)
async def call_external_api(url: str) -> dict:
    """外部API呼び出し（リトライ + タイムアウト）"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

---

### 4.5 Security Decorators

**実装**: `src/app/api/decorators/security.py` (13,357バイト)

#### 4.5.1 @require_permissions

```python
from functools import wraps

def require_permissions(
    required_roles: list[ProjectRole]
):
    """権限チェックデコレータ"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_user取得
            current_user = kwargs.get("current_user")
            project_id = kwargs.get("project_id")

            if not current_user or not project_id:
                raise ValueError("current_user and project_id required")

            # システム管理者は全権限
            if current_user.system_role == SystemUserRole.SYSTEM_ADMIN:
                return await func(*args, **kwargs)

            # プロジェクトメンバーシップチェック
            member = await member_repo.get_by_project_and_user(
                db, project_id=project_id, user_id=current_user.id
            )

            if not member:
                raise PermissionDeniedError("Not a member of this project")

            # ロールチェック
            if member.project_role not in required_roles:
                raise PermissionDeniedError(
                    f"Requires one of: {', '.join(required_roles)}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

**使用例:**

```python
@require_permissions([ProjectRole.PROJECT_MANAGER])
async def delete_project(
    db: AsyncSession,
    project_id: UUID,
    current_user: UserAccount
) -> None:
    """プロジェクト削除（PROJECT_MANAGERのみ）"""
    await project_repo.delete(db, project_id)
```

#### 4.5.2 @audit_log

```python
def audit_log(action: str):
    """監査ログデコレータ"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            # 操作前ログ
            logger.info(
                f"Audit: {action} started",
                action=action,
                user_id=current_user.id if current_user else None,
                function=func.__name__
            )

            try:
                result = await func(*args, **kwargs)

                # 操作成功ログ
                logger.info(
                    f"Audit: {action} succeeded",
                    action=action,
                    user_id=current_user.id if current_user else None
                )

                return result

            except Exception as e:
                # 操作失敗ログ
                logger.error(
                    f"Audit: {action} failed",
                    action=action,
                    user_id=current_user.id if current_user else None,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator
```

---

## 5. StorageService（Strategy パターン）

### 5.1 アーキテクチャ

::: mermaid
graph TB
    Service[ProjectFileService] --> Strategy{StorageService}

    Strategy -->|STORAGE_BACKEND=local| Local[LocalStorageService]
    Strategy -->|STORAGE_BACKEND=azure| Azure[AzureStorageService]

    Local --> LocalFS[Local File System<br/>uploads/]
    Azure --> AzureBlob[Azure Blob Storage<br/>Container]

    Local --> Operations[共通操作]
    Azure --> Operations

    Operations --> Upload[upload<br/>ファイルアップロード]
    Operations --> Download[download<br/>ファイルダウンロード]
    Operations --> Delete[delete<br/>ファイル削除]
    Operations --> Exists[exists<br/>存在確認]

    style Strategy fill:#2196F3
    style Local fill:#4CAF50
    style Azure fill:#03A9F4
:::

### 5.2 実装

**実装**: `src/app/services/storage/` ディレクトリ（Strategyパターン）

- `__init__.py` - get_storage_service() ファクトリ関数
- `base.py` - StorageService 抽象基底クラス
- `local.py` - LocalStorageService（開発環境）
- `azure.py` - AzureStorageService（本番環境）
- `validation.py` - ファイル検証
- `excel.py` - Excel操作ユーティリティ

#### 5.2.1 プロトコル定義

```python
from typing import Protocol
from fastapi import UploadFile

class StorageService(Protocol):
    """ストレージサービスインターフェース"""

    async def upload(
        self,
        file: UploadFile,
        path: str
    ) -> str:
        """ファイルアップロード"""
        ...

    async def download(
        self,
        path: str
    ) -> bytes:
        """ファイルダウンロード"""
        ...

    async def delete(
        self,
        path: str
    ) -> None:
        """ファイル削除"""
        ...

    async def exists(
        self,
        path: str
    ) -> bool:
        """存在確認"""
        ...
:::

#### 5.2.2 ローカルストレージ実装

```python
import aiofiles
from pathlib import Path

class LocalStorageService:
    """ローカルファイルシステム実装"""

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        file: UploadFile,
        path: str
    ) -> str:
        """ファイルアップロード"""
        full_path = self.base_path / path

        # ディレクトリ作成
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 非同期ファイル書き込み
        async with aiofiles.open(full_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        return str(full_path)

    async def download(
        self,
        path: str
    ) -> bytes:
        """ファイルダウンロード"""
        full_path = self.base_path / path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(
        self,
        path: str
    ) -> None:
        """ファイル削除"""
        full_path = self.base_path / path

        if full_path.exists():
            full_path.unlink()

    async def exists(
        self,
        path: str
    ) -> bool:
        """存在確認"""
        full_path = self.base_path / path
        return full_path.exists()
```

#### 5.2.3 Azureストレージ実装

```python
from azure.storage.blob.aio import BlobServiceClient

class AzureStorageService:
    """Azure Blob Storage実装"""

    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER

    async def upload(
        self,
        file: UploadFile,
        path: str
    ) -> str:
        """ファイルアップロード"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=self.container_name,
                blob=path
            )

            content = await file.read()
            await blob_client.upload_blob(content, overwrite=True)

            return f"https://{blob_service.account_name}.blob.core.windows.net/{self.container_name}/{path}"

    async def download(
        self,
        path: str
    ) -> bytes:
        """ファイルダウンロード"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=self.container_name,
                blob=path
            )

            stream = await blob_client.download_blob()
            return await stream.readall()

    async def delete(
        self,
        path: str
    ) -> None:
        """ファイル削除"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=self.container_name,
                blob=path
            )

            await blob_client.delete_blob()

    async def exists(
        self,
        path: str
    ) -> bool:
        """存在確認"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=self.container_name,
                blob=path
            )

            return await blob_client.exists()
```

#### 5.2.4 ファクトリ関数

```python
def get_storage_service() -> StorageService:
    """設定に応じてストレージ実装を返す"""

    if settings.STORAGE_BACKEND == "azure":
        return AzureStorageService()
    else:
        return LocalStorageService()
```

---

## 6. CacheManager

### 6.1 アーキテクチャ

::: mermaid
graph LR
    Service[Service Layer] --> CacheManager[CacheManager]

    CacheManager --> Strategy{Backend}

    Strategy -->|Redis利用可能| Redis[Redis Cache<br/>分散キャッシュ]
    Strategy -->|Redis利用不可| Memory[Memory Cache<br/>ローカルキャッシュ]

    Redis --> Operations[共通操作]
    Memory --> Operations

    Operations --> Get[get<br/>値取得]
    Operations --> Set[set<br/>値設定]
    Operations --> Delete[delete<br/>削除]
    Operations --> Clear[clear<br/>全削除]

    style CacheManager fill:#F44336
    style Redis fill:#D32F2F
    style Memory fill:#FF5252
:::

### 6.2 実装

**実装**: `src/app/core/cache.py`

```python
from redis import asyncio as redis
from typing import Any
import json

class CacheManager:
    """キャッシュマネージャー"""

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.memory_cache: dict[str, Any] = {}

    async def initialize(self):
        """初期化（Redis接続試行）"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis unavailable, using memory cache: {e}")
            self.redis_client = None

    async def get(
        self,
        key: str
    ) -> Any | None:
        """値取得"""
        if self.redis_client:
            value = await self.redis_client.get(key)
            return json.loads(value) if value else None
        else:
            return self.memory_cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> None:
        """値設定（TTL秒）"""
        if self.redis_client:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        else:
            self.memory_cache[key] = value
            # メモリキャッシュはTTL未対応（簡易実装）

    async def delete(
        self,
        key: str
    ) -> None:
        """削除"""
        if self.redis_client:
            await self.redis_client.delete(key)
        else:
            self.memory_cache.pop(key, None)

    async def clear(
        self,
        pattern: str = "*"
    ) -> None:
        """全削除（パターンマッチ）"""
        if self.redis_client:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        else:
            self.memory_cache.clear()

# グローバルインスタンス
cache_manager = CacheManager()
:::

---

## 7. まとめ

### 7.1 コンポーネント設計の特徴

✅ **BaseRepository**: Genericsによる型安全な汎用CRUD
✅ **デコレータ**: 横断的関心事の分離（4カテゴリ、10種類）
✅ **StorageService**: Strategy パターンによるストレージ抽象化
✅ **CacheManager**: Redis/Memoryの自動切り替え
✅ **高凝集・低結合**: 明確な責務分離
✅ **再利用性**: 複数のサービスで利用可能

### 7.2 今後の拡張提案

- **QueryBuilder**: 複雑なクエリの構築支援
- **EventBus**: イベント駆動アーキテクチャ
- **TaskQueue**: バックグラウンドジョブ（Celery等）
- **Notification**: 通知システム（Email、Slack等）

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - データベース設計書: `02-database/01-database-design.md`
  - テスト戦略書: `05-testing/01-test-strategy.md`
