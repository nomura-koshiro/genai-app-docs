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

**実装**: `src/app/repositories/base.py` (489行)

```python
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.base import Base

class BaseRepository[ModelType: Base, IDType: (int, uuid.UUID)]:
    """汎用リポジトリ基底クラス（Python 3.12+ 型パラメータ構文）"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        """リポジトリを初期化（DIでセッション注入）"""
        self.model = model
        self.db = db

    async def get(self, id: IDType) -> ModelType | None:
        """ID取得"""
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        load_relations: list[str] | None = None,
        **filters: Any
    ) -> list[ModelType]:
        """複数取得（N+1対策付き）"""
        query = select(self.model)

        # Eager loading（N+1クエリ対策）
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    query = query.options(
                        selectinload(getattr(self.model, relation))
                    )
                else:
                    logger.warning("無効なリレーション指定", relation=relation)

        # フィルタ適用（セキュリティ：不正なキーは無視）
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
            else:
                logger.warning("無効なフィルタキー指定", filter_key=key)

        # ソート
        if order_by:
            if hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
            else:
                logger.warning("無効なorder_byキー指定", order_by=order_by)

        # ページネーション
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **obj_in: Any) -> ModelType:
        """作成（flush()のみ、commit()は呼び出し側）"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        **update_data: Any
    ) -> ModelType:
        """更新"""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: IDType) -> bool:
        """削除（成功: True, 見つからない: False）"""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False

    async def count(self, **filters: Any) -> int:
        """カウント"""
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one()
```

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
# リポジトリ定義（DIでセッション注入）
class ProjectRepository(BaseRepository[Project, UUID]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

# FastAPI依存性注入で使用
async def get_project_repository(
    db: AsyncSession = Depends(get_db)
) -> ProjectRepository:
    return ProjectRepository(db)

# サービス層での使用
class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    async def get_project(self, project_id: UUID) -> Project | None:
        # ID取得（self.dbは不要）
        return await self.repo.get(project_id)

    async def list_projects(self) -> list[Project]:
        # 複数取得（N+1対策付き）
        return await self.repo.get_multi(
            skip=0,
            limit=20,
            load_relations=["members", "files"],  # N+1対策
            is_active=True  # フィルタ
        )

    async def create_project(self, data: ProjectCreate) -> Project:
        # 作成
        project = await self.repo.create(
            name=data.name,
            code=data.code
        )
        await self.db.commit()  # サービス層でコミット
        return project

    async def update_project(
        self, project: Project, data: ProjectUpdate
    ) -> Project:
        # 更新
        updated = await self.repo.update(
            db_obj=project,
            name=data.name
        )
        await self.db.commit()
        return updated

    async def delete_project(self, project_id: UUID) -> bool:
        # 削除（成功/失敗をboolで返却）
        success = await self.repo.delete(project_id)
        if success:
            await self.db.commit()
        return success
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
    Function --> ErrorHandling[Error Handling]

    Basic --> Log[@log_execution<br/>実行ログ記録]
    Basic --> Perf[@measure_performance<br/>実行時間計測]
    Basic --> Timeout[@async_timeout<br/>タイムアウト制御]

    DataAccess --> Tx[@transactional<br/>トランザクション管理]
    DataAccess --> Cache[@cache_result<br/>Redisキャッシュ]

    Reliability --> Retry[@retry_on_error<br/>リトライ機構]

    ErrorHandling --> Error[@handle_service_errors<br/>エラーハンドリング]

    style Basic fill:#4CAF50
    style DataAccess fill:#2196F3
    style Reliability fill:#FF9800
    style ErrorHandling fill:#F44336
:::

> **Note**: 権限チェック（認可）は `app.api.core.dependencies.authorization` でFastAPI Dependency方式で提供されています。

### 4.2 Basic Decorators

**実装**: `src/app/api/decorators/basic.py`

#### 4.2.1 @log_execution

```python
def log_execution(
    level: str = "info",
    include_args: bool = False,
    include_result: bool = False,
):
    """関数の実行をログに記録するデコレータ。

    Args:
        level: ログレベル（"debug", "info", "warning", "error"）
        include_args: 引数をログに含めるか（デフォルト: False）
        include_result: 戻り値をログに含めるか（デフォルト: False）

    Note:
        - 構造化ログ（extra）にメタデータを記録
        - self引数は自動的にログから除外
        - 本番環境では include_args=False を推奨（機密情報保護）
    """
```

**使用例:**

```python
@log_execution(level="info", include_args=True)
async def process_payment(user_id: int, amount: float):
    # 決済処理
    return {"status": "success", "transaction_id": "12345"}

# ログ出力:
# INFO: Executing: process_payment
#       extra={'function': 'process_payment', 'args': '(123, 100.0)', ...}
# INFO: Completed: process_payment
```

#### 4.2.2 @measure_performance

```python
import time
from functools import wraps
from app.core.logging import get_logger

logger = get_logger(__name__)

def measure_performance[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """非同期関数の実行時間を測定するデコレータ。

    パフォーマンスボトルネックの特定やレスポンス時間の監視に使用します。
    time.perf_counter() を使用して高精度な時間測定を実行します。
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(
                "performance_measurement",
                function=func.__name__,
                duration_seconds=elapsed,
                module=func.__module__,
                performance_metric=True,
            )

    return wrapper
```

**使用例:**

```python
@measure_performance
async def get_projects(skip: int = 0, limit: int = 100):
    """プロジェクト一覧取得（パフォーマンス計測付き）"""
    return await project_repo.get_multi(skip=skip, limit=limit)

# ログ出力（structlog形式）:
# {"event": "performance_measurement", "function": "get_projects",
#  "duration_seconds": 0.0234, "module": "...", "performance_metric": true}
```

#### 4.2.3 @async_timeout

```python
import asyncio
from app.core.exceptions import ValidationError

def async_timeout(seconds: float):
    """非同期関数にタイムアウトを設定するデコレータ。

    長時間実行される処理（AIエージェント、外部API、ファイルアップロード等）に
    タイムアウトを設定し、ハングアップを防ぎます。

    推奨タイムアウト値:
        - AIエージェント実行: 300秒（5分）
        - ファイルアップロード: 30秒
        - 外部API呼び出し: 10秒
        - データベースクエリ: 5秒

    Raises:
        ValidationError: タイムアウト時（ユーザー向けエラーメッセージ）
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except TimeoutError:
                logger.error(
                    "async_timeout_exceeded",
                    function=func.__name__,
                    timeout_seconds=seconds,
                )
                raise ValidationError(
                    f"処理がタイムアウトしました（{seconds}秒）"
                ) from None

        return wrapper
    return decorator
```

**使用例:**

```python
# AIエージェント実行に5分のタイムアウト
@async_timeout(300.0)
async def execute_agent(self, prompt: str):
    return await self.agent.ainvoke(prompt)

# ファイルアップロードに30秒のタイムアウト
@async_timeout(30.0)
async def upload_to_blob(self, file_data: bytes):
    return await self.storage.upload(file_data)
```

---

### 4.3 Data Access Decorators

**実装**: `src/app/api/decorators/data_access.py`

#### 4.3.1 @transactional

```python
def transactional[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """データベーストランザクションを自動管理するデコレータ。

    関数が正常終了した場合は自動的にコミット、例外が発生した場合は
    自動的にロールバックすることで、トランザクション管理を簡素化します。

    対象オブジェクト:
        - 関数の第1引数（self）が db または _db 属性を持つ必要がある
        - db属性が存在しない場合は通常の関数として実行（デコレータ無効）
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        # 最初の引数がselfで、dbセッションを持っていると仮定
        instance = args[0] if args else None
        db = getattr(instance, "db", None)
        if db is None:
            db = getattr(instance, "_db", None)

        if db is None:
            # dbがない場合は通常実行（トランザクション管理なし）
            return await func(*args, **kwargs)

        try:
            result = await func(*args, **kwargs)
            await db.commit()
            return result
        except Exception as e:
            await db.rollback()
            logger.error(
                "transaction_rolled_back",
                function=func.__name__,
                error_type=type(e).__name__,
            )
            raise

    return wrapper
```

**使用例:**

```python
class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.member_repo = MemberRepository(db)

    @transactional
    async def create_project_with_member(
        self,
        project_data: ProjectCreate,
        creator_id: UUID
    ) -> Project:
        """プロジェクトとメンバーを同一トランザクションで作成"""

        # プロジェクト作成（flush）
        project = await self.project_repo.create(**project_data.dict())

        # メンバー追加（flush）
        await self.member_repo.create(
            project_id=project.id,
            user_id=creator_id,
            project_role=ProjectRole.PROJECT_MANAGER
        )

        # デコレータが自動commit（self.db.commit()）
        return project
```

#### 4.3.2 @cache_result

```python
import hashlib
from app.core.cache import cache_manager

def cache_result(ttl: int = 300, key_prefix: str = "func"):
    """関数の結果をRedisにキャッシュするデコレータ。

    頻繁にアクセスされる読み取り専用データ（ユーザー情報、設定情報など）に
    キャッシュを適用し、データベースクエリやAPI呼び出しを削減します。

    キャッシュ戦略:
        - Cache-Aside パターン
        - キャッシュヒット: Redisから即座に返却
        - キャッシュミス: 関数実行後にRedisに保存

    Args:
        ttl: キャッシュの有効期限（秒、デフォルト: 300秒）
        key_prefix: キャッシュキーのプレフィックス（デフォルト: "func"）

    Note:
        - Redis未接続時は通常の関数として動作（グレースフルデグラデーション）
        - キャッシュキーはSHA256ハッシュの先頭16文字を使用
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュキー生成（関数名 + 引数のハッシュ）
            args_str = f"{args}:{kwargs}"
            args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:16]
            cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"

            # キャッシュから取得試行
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                logger.debug("cache_hit", cache_key=cache_key)
                return cached

            # キャッシュミスの場合は実行
            logger.debug("cache_miss", cache_key=cache_key)
            result = await func(*args, **kwargs)

            # 結果をキャッシュに保存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
```

**使用例:**

```python
@cache_result(ttl=600, key_prefix="project")  # 10分間キャッシュ
async def get_project_summary(project_id: UUID) -> dict:
    """プロジェクト概要取得（キャッシュ付き）"""
    project = await project_repo.get(project_id)
    members = await member_repo.get_by_project(project_id)

    return {
        "project": project,
        "member_count": len(members),
        "file_count": await file_repo.count(project_id=project_id)
    }
```

---

### 4.4 Reliability Decorators

**実装**: `src/app/api/decorators/reliability.py`

#### 4.4.1 @retry_on_error

```python
import asyncio

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """エラー時に自動リトライするデコレータ。

    外部API呼び出し、ネットワークエラー、一時的なデータベース接続エラーなど、
    リトライで回復可能なエラーに対して自動的に再試行を行います。

    リトライ戦略:
        - Exponential Backoff: リトライごとに待機時間が指数的に増加
        - デフォルト: 1秒 → 2秒 → 4秒 → 8秒...

    リトライ対象外の例外:
        - ValidationError: バリデーションエラーは再試行不要
        - AuthenticationError: 認証エラーは再試行不要
        - NotFoundError: リソース不在は再試行不要

    Args:
        max_retries: 最大リトライ回数（デフォルト: 3回）
        delay: 初回リトライまでの待機時間（秒、デフォルト: 1.0秒）
        backoff: リトライごとの待機時間の倍率（デフォルト: 2.0）
        exceptions: リトライ対象の例外タプル

    Warning:
        - 冪等性のない操作（決済処理など）には使用しない
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            next_delay=current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "all_retries_failed",
                            function=func.__name__,
                            max_retries=max_retries,
                        )

            raise last_exception

        return wrapper
    return decorator
```

**使用例:**

```python
@retry_on_error(
    max_retries=3,
    delay=1.0,
    backoff=2.0,
    exceptions=(ConnectionError, TimeoutError)
)
@async_timeout(seconds=30)
async def call_external_api(url: str) -> dict:
    """外部API呼び出し（リトライ + タイムアウト）"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

---

### 4.5 Error Handling Decorators

**実装**: `src/app/api/decorators/error_handling.py`

#### 4.5.1 @handle_service_errors

```python
from fastapi import HTTPException, status
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    PermissionDeniedError,
    BusinessRuleViolationError,
)

def handle_service_errors(func):
    """サービスエラーをHTTPExceptionに変換するデコレータ。

    サービス層で発生するビジネスエラーを適切なHTTPステータスコードに
    マッピングし、一貫したエラーレスポンスを提供します。

    エラーマッピング:
        - NotFoundError → 404 Not Found
        - ValidationError → 400 Bad Request
        - PermissionDeniedError → 403 Forbidden
        - BusinessRuleViolationError → 400 Bad Request
        - その他 → 500 Internal Server Error
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

        except (ValidationError, BusinessRuleViolationError) as e:
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
            logger.exception("Unhandled service error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    return wrapper
```

**使用例:**

```python
@handle_service_errors
async def get_project(project_id: UUID) -> Project:
    """プロジェクト取得（エラーハンドリング付き）"""
    project = await project_repo.get(project_id)
    if not project:
        raise NotFoundError(f"Project {project_id} not found")
    return project
```

---

### 4.6 認可（権限チェック）

権限チェックはデコレータではなく、FastAPI Dependency方式で実装されています。

**実装**: `src/app/api/core/dependencies/authorization.py`

```python
from fastapi import Depends

async def require_project_role(
    project_id: UUID,
    required_roles: list[ProjectRole],
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """プロジェクトロールを検証するFastAPI依存性。

    システム管理者は全権限を持ち、それ以外はプロジェクトメンバーシップと
    ロールを確認します。
    """
    # システム管理者は全権限
    if current_user.system_role == SystemUserRole.SYSTEM_ADMIN:
        return

    # プロジェクトメンバーシップチェック
    member = await member_repo.get_by_project_and_user(
        db, project_id=project_id, user_id=current_user.id
    )

    if not member:
        raise PermissionDeniedError("Not a member of this project")

    if member.project_role not in required_roles:
        raise PermissionDeniedError(
            f"Requires one of: {', '.join(r.value for r in required_roles)}"
        )
```

**使用例:**

```python
@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: UserAccount = Depends(get_current_user),
    _: None = Depends(
        lambda: require_project_role(
            project_id, [ProjectRole.PROJECT_MANAGER]
        )
    ),
):
    """プロジェクト削除（PROJECT_MANAGERのみ）"""
    await project_service.delete(project_id)
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
    Operations --> ListBlobs[list_blobs<br/>ファイル一覧]
    Operations --> TempDownload[download_to_temp_file<br/>一時ファイル]

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

#### 5.2.1 抽象基底クラス定義

```python
from abc import ABC, abstractmethod

class StorageService(ABC):
    """ストレージサービスの抽象基底クラス。

    ファイルストレージ操作の共通インターフェースを定義します。
    具体的な実装（ローカル、Azure）は、このクラスを継承して実装されます。
    """

    @abstractmethod
    async def upload(
        self,
        container: str,
        path: str,
        data: bytes
    ) -> bool:
        """ファイルアップロード"""
        pass

    @abstractmethod
    async def download(
        self,
        container: str,
        path: str
    ) -> bytes:
        """ファイルダウンロード"""
        pass

    @abstractmethod
    async def delete(
        self,
        container: str,
        path: str
    ) -> bool:
        """ファイル削除"""
        pass

    @abstractmethod
    async def exists(
        self,
        container: str,
        path: str
    ) -> bool:
        """存在確認"""
        pass

    @abstractmethod
    async def list_blobs(
        self,
        container: str,
        prefix: str = ""
    ) -> list[str]:
        """コンテナ内のファイル一覧を取得"""
        pass

    @abstractmethod
    def get_file_path(
        self,
        container: str,
        path: str
    ) -> str:
        """ファイルの完全パスを取得"""
        pass

    @abstractmethod
    async def download_to_temp_file(
        self,
        container: str,
        path: str
    ) -> str:
        """ファイルを一時ファイルにダウンロードし、パスを返す"""
        pass
```

#### 5.2.2 ローカルストレージ実装

```python
import aiofiles
from pathlib import Path

class LocalStorageService(StorageService):
    """ローカルファイルシステム実装（開発環境用）"""

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        container: str,
        path: str,
        data: bytes
    ) -> bool:
        """ファイルアップロード"""
        full_path = self.base_path / container / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)
        return True

    async def download(
        self,
        container: str,
        path: str
    ) -> bytes:
        """ファイルダウンロード"""
        full_path = self.base_path / container / path

        if not full_path.exists():
            raise NotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(
        self,
        container: str,
        path: str
    ) -> bool:
        """ファイル削除"""
        full_path = self.base_path / container / path

        if full_path.exists():
            full_path.unlink()
            return True
        raise NotFoundError(f"File not found: {path}")

    async def exists(
        self,
        container: str,
        path: str
    ) -> bool:
        """存在確認"""
        full_path = self.base_path / container / path
        return full_path.exists()

    async def list_blobs(
        self,
        container: str,
        prefix: str = ""
    ) -> list[str]:
        """コンテナ内のファイル一覧を取得"""
        container_path = self.base_path / container
        if not container_path.exists():
            return []

        files = []
        for file_path in container_path.rglob(f"{prefix}*"):
            if file_path.is_file():
                files.append(str(file_path.relative_to(container_path)))
        return files

    def get_file_path(
        self,
        container: str,
        path: str
    ) -> str:
        """ファイルの完全パスを取得"""
        return str(self.base_path / container / path)

    async def download_to_temp_file(
        self,
        container: str,
        path: str
    ) -> str:
        """ローカルストレージの場合は既存パスを返す"""
        full_path = self.base_path / container / path
        if not full_path.exists():
            raise NotFoundError(f"File not found: {path}")
        return str(full_path)
```

#### 5.2.3 Azureストレージ実装

```python
import tempfile
from azure.storage.blob.aio import BlobServiceClient

class AzureStorageService(StorageService):
    """Azure Blob Storage実装（本番環境用）"""

    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING

    async def upload(
        self,
        container: str,
        path: str,
        data: bytes
    ) -> bool:
        """ファイルアップロード"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=container,
                blob=path
            )
            await blob_client.upload_blob(data, overwrite=True)
            return True

    async def download(
        self,
        container: str,
        path: str
    ) -> bytes:
        """ファイルダウンロード"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=container,
                blob=path
            )

            if not await blob_client.exists():
                raise NotFoundError(f"File not found: {path}")

            stream = await blob_client.download_blob()
            return await stream.readall()

    async def delete(
        self,
        container: str,
        path: str
    ) -> bool:
        """ファイル削除"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=container,
                blob=path
            )

            if not await blob_client.exists():
                raise NotFoundError(f"File not found: {path}")

            await blob_client.delete_blob()
            return True

    async def exists(
        self,
        container: str,
        path: str
    ) -> bool:
        """存在確認"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            blob_client = blob_service.get_blob_client(
                container=container,
                blob=path
            )
            return await blob_client.exists()

    async def list_blobs(
        self,
        container: str,
        prefix: str = ""
    ) -> list[str]:
        """コンテナ内のファイル一覧を取得"""
        async with BlobServiceClient.from_connection_string(
            self.connection_string
        ) as blob_service:
            container_client = blob_service.get_container_client(container)
            blobs = []
            async for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append(blob.name)
            return blobs

    def get_file_path(
        self,
        container: str,
        path: str
    ) -> str:
        """Azure Blob URLを取得"""
        return f"https://{settings.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{container}/{path}"

    async def download_to_temp_file(
        self,
        container: str,
        path: str
    ) -> str:
        """ファイルを一時ファイルにダウンロードし、パスを返す"""
        data = await self.download(container, path)

        # 一時ファイルに書き込み
        suffix = Path(path).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(data)
            return f.name
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

    CacheManager --> Redis[Redis Cache<br/>分散キャッシュ]

    Redis --> Operations[共通操作]

    Operations --> Get[get<br/>値取得]
    Operations --> Set[set<br/>値設定]
    Operations --> Delete[delete<br/>削除]
    Operations --> Exists[exists<br/>存在確認]
    Operations --> Clear[clear<br/>パターン削除]

    subgraph "レート制限用"
        Operations --> ZAdd[zadd<br/>Sorted Set追加]
        Operations --> ZCard[zcard<br/>要素数取得]
        Operations --> ZRemRange[zremrangebyscore<br/>範囲削除]
    end

    style CacheManager fill:#F44336
    style Redis fill:#D32F2F
:::

> **Note**: Redis未接続時はグレースフルデグラデーション（キャッシュなしモード）で動作します。

### 6.2 実装

**実装**: `src/app/core/cache.py`

```python
import json
from typing import Any
from redis.asyncio import Redis
from app.core.config import settings

class CacheManager:
    """Redisベースのキャッシュ管理クラス。

    グレースフルデグラデーション設計により、
    Redis接続エラー時もアプリケーションは正常に動作します。

    キープレフィックス構造:
        {APP_NAME}:{ENVIRONMENT}:{key_prefix}:{key}
        例: "training-tracker:development:app:user:123"
    """

    def __init__(self, key_prefix: str = "app"):
        self._redis: Redis[str] | None = None
        self.key_prefix = f"{settings.APP_NAME}:{settings.ENVIRONMENT}:{key_prefix}"

    def _make_key(self, key: str) -> str:
        """プレフィックス付きの完全なキーを生成"""
        return f"{self.key_prefix}:{key}"

    async def connect(self) -> None:
        """Redisサーバーへの接続を確立"""
        if settings.REDIS_URL:
            self._redis = await Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Redisサーバーへの接続を切断"""
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Any | None:
        """キャッシュからデータを取得（Redis未接続時はNone）"""
        if not self._redis:
            return None

        full_key = self._make_key(key)
        try:
            value = await self._redis.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.exception("キャッシュ取得エラー", cache_key=full_key)
            return None  # エラー時はキャッシュなしとして動作

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """データをキャッシュに保存"""
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            ttl = expire if expire is not None else settings.CACHE_TTL

            if ttl > 0:
                await self._redis.setex(full_key, ttl, serialized)
            else:
                await self._redis.set(full_key, serialized)
            return True
        except Exception as e:
            logger.exception("キャッシュ設定エラー", cache_key=full_key)
            return False

    async def delete(self, key: str) -> bool:
        """キャッシュからデータを削除"""
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            await self._redis.delete(full_key)
            return True
        except Exception as e:
            logger.exception("キャッシュ削除エラー", cache_key=full_key)
            return False

    async def exists(self, key: str) -> bool:
        """キャッシュキーが存在するかチェック"""
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            return await self._redis.exists(full_key) > 0
        except Exception as e:
            logger.exception("キャッシュ存在確認エラー", cache_key=full_key)
            return False

    async def clear(self, pattern: str = "*") -> bool:
        """パターンに一致するキャッシュをすべて削除"""
        if not self._redis:
            return False

        full_pattern = self._make_key(pattern)
        try:
            async for key in self._redis.scan_iter(match=full_pattern):
                await self._redis.delete(key)
            return True
        except Exception as e:
            logger.exception("キャッシュクリアエラー", pattern=full_pattern)
            return False

    # ========================================================================
    # レート制限用 Sorted Set 操作
    # ========================================================================

    def is_redis_available(self) -> bool:
        """Redis接続が利用可能かを確認"""
        return self._redis is not None

    async def zadd(self, key: str, mapping: dict[str | bytes, float]) -> int:
        """Sorted Setに要素を追加"""
        if not self._redis:
            return 0
        full_key = self._make_key(key)
        return await self._redis.zadd(full_key, mapping)

    async def zcard(self, key: str) -> int:
        """Sorted Setの要素数を取得"""
        if not self._redis:
            return 0
        full_key = self._make_key(key)
        return await self._redis.zcard(full_key)

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Sorted Setから指定スコア範囲の要素を削除"""
        if not self._redis:
            return 0
        full_key = self._make_key(key)
        return await self._redis.zremrangebyscore(full_key, min_score, max_score)

    async def expire_key(self, key: str, seconds: int) -> bool:
        """キーにTTLを設定"""
        if not self._redis:
            return False
        full_key = self._make_key(key)
        return await self._redis.expire(full_key, seconds)


# グローバルキャッシュマネージャーインスタンス
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """FastAPI依存性注入用ヘルパー関数"""
    return cache_manager
```

---

## 7. まとめ

### 7.1 コンポーネント設計の特徴

✅ **BaseRepository**: Python 3.12+ 型パラメータ構文による型安全な汎用CRUD（DIでセッション注入）
✅ **デコレータ**: 横断的関心事の分離（4カテゴリ、7種類）

- Basic: `@log_execution`, `@measure_performance`, `@async_timeout`
- Data Access: `@transactional`, `@cache_result`
- Reliability: `@retry_on_error`
- Error Handling: `@handle_service_errors`
✅ **認可**: FastAPI Dependency方式による権限チェック（`authorization.py`）
✅ **StorageService**: Strategy パターンによるストレージ抽象化（container/path形式）
✅ **CacheManager**: Redisベース + グレースフルデグラデーション + レート制限サポート
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
- **最終更新日**: 2026年1月（実装との整合性更新）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - データベース設計書: `02-database/01-database-design.md`
  - テスト戦略書: `05-testing/01-test-strategy.md`
