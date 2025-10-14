# 新しい機能モジュールの追加

このガイドでは、完全な機能モジュール（モデル、リポジトリ、サービス、API）を追加する手順を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [ステップバイステップ](#ステップバイステップ)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)
- [参考リンク](#参考リンク)

## 概要

完全な機能モジュールには以下のコンポーネントが含まれます：

```
タスク管理機能
├── モデル層（models/task.py）
├── リポジトリ層（repositories/task.py）
├── サービス層（services/task.py）
├── スキーマ層（schemas/task.py）
├── API層（api/routes/tasks.py）
├── マイグレーション（alembic/versions/xxx_add_task_table.py）
└── テスト（tests/）
```

## 前提条件

- [新しいモデル追加](./02-add-model.md)の理解
- [新しいエンドポイント追加](./01-add-endpoint.md)の理解
- プロジェクトのアーキテクチャパターンの理解
- FastAPIとSQLAlchemyの基礎知識

## ステップバイステップ

### 例: タスク管理機能の追加

完全なCRUD機能を持つタスク管理モジュールを追加します。

### ステップ 1: 要件定義

機能の要件を明確にします：

**タスク管理機能の要件:**
- タスクの作成、読み取り、更新、削除（CRUD）
- タスクの優先度設定（低、中、高）
- タスクのステータス管理（未着手、進行中、完了）
- ユーザーごとのタスク管理
- タスクの期限設定
- タスクの検索とフィルタリング

### ステップ 2: データモデルの設計

#### 2.1 エンティティの定義

`src/app/models/task.py`を作成：

```python
"""タスクモデル。"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, Enum):
    """タスクステータス列挙型。"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    """タスク優先度列挙型。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    """タスクデータベースモデル。"""

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic fields
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="タスクタイトル",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="タスク説明",
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.TODO,
        nullable=False,
        index=True,
        comment="タスクステータス",
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True,
        comment="タスク優先度",
    )

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ユーザーID",
    )

    # Timestamps
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="期限",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完了日時",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="作成日時",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新日時",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        """文字列表現。"""
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

    def mark_completed(self) -> None:
        """タスクを完了としてマークします。"""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now(timezone.utc)

    def is_overdue(self) -> bool:
        """期限が過ぎているかチェックします。"""
        if not self.due_date:
            return False
        return (
            self.status != TaskStatus.DONE
            and self.due_date < datetime.now(timezone.utc)
        )
```

#### 2.2 既存モデルの更新

`src/app/models/user.py`にリレーションシップを追加：

```python
# Relationships
tasks: Mapped[list["Task"]] = relationship(
    "Task",
    back_populates="user",
    cascade="all, delete-orphan",
)
```

#### 2.3 モデルのインポート

`src/app/models/__init__.py`を更新：

```python
from app.models.task import Task, TaskPriority, TaskStatus

__all__ = [
    # ...
    "Task",
    "TaskPriority",
    "TaskStatus",
]
```

### ステップ 3: マイグレーションの作成と適用

```bash
# マイグレーション生成
alembic revision --autogenerate -m "add_task_table"

# マイグレーション確認（生成されたファイルを確認）
# alembic/versions/xxxx_add_task_table.py

# マイグレーション適用
alembic upgrade head

# 確認
alembic current
```

### ステップ 4: Pydanticスキーマの作成

`src/app/schemas/task.py`を作成：

```python
"""タスク関連のPydanticスキーマ。"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """ベースタスクスキーマ。"""

    title: str = Field(..., min_length=1, max_length=200, description="タスクタイトル")
    description: str | None = Field(None, max_length=2000, description="タスク説明")
    priority: TaskPriority = Field(
        TaskPriority.MEDIUM, description="タスク優先度"
    )
    due_date: datetime | None = Field(None, description="期限")


class TaskCreate(TaskBase):
    """タスク作成リクエストスキーマ。"""

    pass


class TaskUpdate(BaseModel):
    """タスク更新リクエストスキーマ。"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus | None = Field(None)
    priority: TaskPriority | None = Field(None)
    due_date: datetime | None = Field(None)


class TaskResponse(TaskBase):
    """タスクレスポンススキーマ。"""

    id: int = Field(..., description="タスクID")
    status: TaskStatus = Field(..., description="タスクステータス")
    user_id: int = Field(..., description="ユーザーID")
    completed_at: datetime | None = Field(None, description="完了日時")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    is_overdue: bool = Field(False, description="期限切れかどうか")

    class Config:
        """Pydantic設定。"""

        from_attributes = True


class TaskListResponse(BaseModel):
    """タスクリストレスポンススキーマ。"""

    tasks: list[TaskResponse] = Field(..., description="タスクリスト")
    total: int = Field(..., description="総タスク数")


class TaskStatsResponse(BaseModel):
    """タスク統計レスポンススキーマ。"""

    total: int = Field(..., description="総タスク数")
    todo: int = Field(..., description="未着手タスク数")
    in_progress: int = Field(..., description="進行中タスク数")
    done: int = Field(..., description="完了タスク数")
    overdue: int = Field(..., description="期限切れタスク数")
```

`src/app/schemas/__init__.py`を更新：

```python
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    TaskUpdate,
)

__all__ = [
    # ...
    "TaskCreate",
    "TaskListResponse",
    "TaskResponse",
    "TaskStatsResponse",
    "TaskUpdate",
]
```

### ステップ 5: リポジトリの作成

`src/app/repositories/task.py`を作成：

```python
"""タスクリポジトリ。"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """タスクデータアクセス用リポジトリ。"""

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: データベースセッション
        """
        super().__init__(Task, db)

    async def get_user_tasks(
        self,
        user_id: int,
        status: TaskStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """ユーザーのタスクを取得します。

        Args:
            user_id: ユーザーID
            status: オプションのステータスフィルタ
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            タスクのリスト
        """
        query = select(Task).where(Task.user_id == user_id)

        if status:
            query = query.where(Task.status == status)

        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_tasks(
        self,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """期限切れタスクを取得します。

        Args:
            user_id: オプションのユーザーID
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            期限切れタスクのリスト
        """
        now = datetime.now(timezone.utc)
        query = (
            select(Task)
            .where(Task.status != TaskStatus.DONE)
            .where(Task.due_date < now)
        )

        if user_id:
            query = query.where(Task.user_id == user_id)

        query = query.offset(skip).limit(limit).order_by(Task.due_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, user_id: int) -> dict[TaskStatus, int]:
        """ステータス別のタスク数を取得します。

        Args:
            user_id: ユーザーID

        Returns:
            ステータスごとのカウント辞書
        """
        query = (
            select(Task.status, func.count(Task.id))
            .where(Task.user_id == user_id)
            .group_by(Task.status)
        )

        result = await self.db.execute(query)
        counts = {status: count for status, count in result.all()}

        # すべてのステータスを含める
        return {
            TaskStatus.TODO: counts.get(TaskStatus.TODO, 0),
            TaskStatus.IN_PROGRESS: counts.get(TaskStatus.IN_PROGRESS, 0),
            TaskStatus.DONE: counts.get(TaskStatus.DONE, 0),
        }

    async def search_tasks(
        self,
        user_id: int,
        query_text: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """タスクを検索します。

        Args:
            user_id: ユーザーID
            query_text: 検索クエリ
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            検索結果のタスクリスト
        """
        query = (
            select(Task)
            .where(Task.user_id == user_id)
            .where(
                Task.title.ilike(f"%{query_text}%")
                | Task.description.ilike(f"%{query_text}%")
            )
            .offset(skip)
            .limit(limit)
            .order_by(Task.created_at.desc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
```

`src/app/repositories/__init__.py`を更新：

```python
from app.repositories.task import TaskRepository

__all__ = [
    # ...
    "TaskRepository",
]
```

### ステップ 6: サービスの作成

`src/app/services/task.py`を作成：

```python
"""タスクビジネスロジック用サービス。"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models.task import Task, TaskStatus
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskStatsResponse, TaskUpdate


class TaskService:
    """タスク関連のビジネスロジック用サービス。"""

    def __init__(self, db: AsyncSession):
        """タスクサービスを初期化します。

        Args:
            db: データベースセッション
        """
        self.repository = TaskRepository(db)

    async def create_task(self, user_id: int, task_data: TaskCreate) -> Task:
        """新しいタスクを作成します。

        Args:
            user_id: ユーザーID
            task_data: タスク作成データ

        Returns:
            作成されたタスクインスタンス

        Raises:
            ValidationError: データが無効な場合
        """
        # ビジネスロジックの検証
        if task_data.due_date and task_data.due_date < datetime.now(timezone.utc):
            raise ValidationError("Due date must be in the future")

        # タスク作成
        task = await self.repository.create(
            user_id=user_id,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            due_date=task_data.due_date,
        )

        return task

    async def get_task(self, task_id: int, user_id: int) -> Task:
        """タスクを取得します（権限チェック付き）。

        Args:
            task_id: タスクID
            user_id: ユーザーID

        Returns:
            タスクインスタンス

        Raises:
            NotFoundError: タスクが見つからない場合
            PermissionDeniedError: 権限がない場合
        """
        task = await self.repository.get(task_id)
        if not task:
            raise NotFoundError("Task not found", details={"task_id": task_id})

        if task.user_id != user_id:
            raise PermissionDeniedError("You don't have permission to access this task")

        return task

    async def list_user_tasks(
        self,
        user_id: int,
        status: TaskStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """ユーザーのタスクリストを取得します。

        Args:
            user_id: ユーザーID
            status: オプションのステータスフィルタ
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            タスクのリスト
        """
        return await self.repository.get_user_tasks(
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    async def update_task(
        self, task_id: int, user_id: int, task_data: TaskUpdate
    ) -> Task:
        """タスクを更新します。

        Args:
            task_id: タスクID
            user_id: ユーザーID
            task_data: 更新データ

        Returns:
            更新されたタスクインスタンス

        Raises:
            NotFoundError: タスクが見つからない場合
            PermissionDeniedError: 権限がない場合
        """
        task = await self.get_task(task_id, user_id)

        # Noneでない値のみを更新
        update_data = task_data.model_dump(exclude_unset=True)
        if not update_data:
            return task

        # ステータスが完了に変更された場合、completed_atを設定
        if update_data.get("status") == TaskStatus.DONE and task.status != TaskStatus.DONE:
            update_data["completed_at"] = datetime.now(timezone.utc)

        task = await self.repository.update(task, **update_data)
        return task

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """タスクを削除します。

        Args:
            task_id: タスクID
            user_id: ユーザーID

        Returns:
            削除された場合はTrue

        Raises:
            NotFoundError: タスクが見つからない場合
            PermissionDeniedError: 権限がない場合
        """
        task = await self.get_task(task_id, user_id)
        await self.repository.delete(task.id)
        return True

    async def get_task_stats(self, user_id: int) -> TaskStatsResponse:
        """タスク統計を取得します。

        Args:
            user_id: ユーザーID

        Returns:
            タスク統計
        """
        # ステータス別カウント
        counts = await self.repository.count_by_status(user_id)

        # 期限切れタスク
        overdue_tasks = await self.repository.get_overdue_tasks(user_id)

        return TaskStatsResponse(
            total=sum(counts.values()),
            todo=counts[TaskStatus.TODO],
            in_progress=counts[TaskStatus.IN_PROGRESS],
            done=counts[TaskStatus.DONE],
            overdue=len(overdue_tasks),
        )

    async def search_tasks(
        self,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """タスクを検索します。

        Args:
            user_id: ユーザーID
            query: 検索クエリ
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            検索結果のタスクリスト
        """
        if not query or len(query) < 2:
            raise ValidationError("Search query must be at least 2 characters")

        return await self.repository.search_tasks(
            user_id=user_id,
            query_text=query,
            skip=skip,
            limit=limit,
        )
```

`src/app/services/__init__.py`を更新：

```python
from app.services.task import TaskService

__all__ = [
    # ...
    "TaskService",
]
```

### ステップ 7: 依存性注入の設定

`src/app/api/dependencies.py`を更新：

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.task import TaskService

# ... 既存のコード ...


async def get_task_service(
    db: AsyncSession = Depends(get_db),
) -> TaskService:
    """タスクサービスの依存性を提供します。

    Args:
        db: データベースセッション

    Returns:
        TaskServiceインスタンス
    """
    return TaskService(db)


# Type alias for dependency injection
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
```

### ステップ 8: APIルートの作成

`src/app/api/routes/tasks.py`を作成：

```python
"""タスクAPIルート。"""

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUserDep, TaskServiceDep
from app.models.task import TaskStatus
from app.schemas.common import MessageResponse
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    TaskUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="タスクを作成",
)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
) -> TaskResponse:
    """
    新しいタスクを作成します。

    Args:
        task_data: タスク作成データ
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        作成されたタスク情報
    """
    task = await task_service.create_task(current_user.id, task_data)
    task_response = TaskResponse.model_validate(task)
    task_response.is_overdue = task.is_overdue()
    return task_response


@router.get("/{task_id}", response_model=TaskResponse, summary="タスクを取得")
async def get_task(
    task_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
) -> TaskResponse:
    """
    タスクを取得します。

    Args:
        task_id: タスクID
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        タスク情報
    """
    task = await task_service.get_task(task_id, current_user.id)
    task_response = TaskResponse.model_validate(task)
    task_response.is_overdue = task.is_overdue()
    return task_response


@router.get("/", response_model=TaskListResponse, summary="タスクリストを取得")
async def list_tasks(
    status: TaskStatus | None = Query(None, description="ステータスフィルタ"),
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
    current_user: CurrentUserDep = None,
    task_service: TaskServiceDep = None,
) -> TaskListResponse:
    """
    ユーザーのタスクリストを取得します。

    Args:
        status: オプションのステータスフィルタ
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        タスクリストと総数
    """
    tasks = await task_service.list_user_tasks(
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit,
    )

    task_responses = []
    for task in tasks:
        task_response = TaskResponse.model_validate(task)
        task_response.is_overdue = task.is_overdue()
        task_responses.append(task_response)

    return TaskListResponse(tasks=task_responses, total=len(task_responses))


@router.patch("/{task_id}", response_model=TaskResponse, summary="タスクを更新")
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
) -> TaskResponse:
    """
    タスクを更新します。

    Args:
        task_id: タスクID
        task_data: 更新データ
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        更新されたタスク情報
    """
    task = await task_service.update_task(task_id, current_user.id, task_data)
    task_response = TaskResponse.model_validate(task)
    task_response.is_overdue = task.is_overdue()
    return task_response


@router.delete("/{task_id}", response_model=MessageResponse, summary="タスクを削除")
async def delete_task(
    task_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
) -> MessageResponse:
    """
    タスクを削除します。

    Args:
        task_id: タスクID
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        成功メッセージ
    """
    await task_service.delete_task(task_id, current_user.id)
    return MessageResponse(message=f"Task {task_id} deleted successfully")


@router.get(
    "/stats/summary",
    response_model=TaskStatsResponse,
    summary="タスク統計を取得",
)
async def get_task_stats(
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
) -> TaskStatsResponse:
    """
    タスク統計を取得します。

    Args:
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        タスク統計
    """
    return await task_service.get_task_stats(current_user.id)


@router.get(
    "/search/",
    response_model=TaskListResponse,
    summary="タスクを検索",
)
async def search_tasks(
    q: str = Query(..., min_length=2, description="検索クエリ"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CurrentUserDep = None,
    task_service: TaskServiceDep = None,
) -> TaskListResponse:
    """
    タスクを検索します。

    Args:
        q: 検索クエリ
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        current_user: 現在のユーザー
        task_service: タスクサービスインスタンス

    Returns:
        検索結果のタスクリスト
    """
    tasks = await task_service.search_tasks(
        user_id=current_user.id,
        query=q,
        skip=skip,
        limit=limit,
    )

    task_responses = []
    for task in tasks:
        task_response = TaskResponse.model_validate(task)
        task_response.is_overdue = task.is_overdue()
        task_responses.append(task_response)

    return TaskListResponse(tasks=task_responses, total=len(task_responses))
```

### ステップ 9: ルーターの登録

`src/app/main.py`を更新：

```python
from app.api.routes import agents, files, tasks  # 追加

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])  # 追加
```

### ステップ 10: テストの作成

`tests/services/test_task_service.py`を作成：

```python
"""タスクサービスのテスト。"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task import TaskService


@pytest.mark.asyncio
async def test_create_task(db: AsyncSession, test_user):
    """タスク作成のテスト。"""
    service = TaskService(db)
    task_data = TaskCreate(
        title="Test Task",
        description="Test Description",
        priority=TaskPriority.HIGH,
    )

    task = await service.create_task(test_user.id, task_data)
    await db.commit()

    assert task.title == "Test Task"
    assert task.user_id == test_user.id
    assert task.status == TaskStatus.TODO


@pytest.mark.asyncio
async def test_create_task_with_past_due_date(db: AsyncSession, test_user):
    """過去の期限でタスク作成のテスト（エラー）。"""
    service = TaskService(db)
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    task_data = TaskCreate(
        title="Test Task",
        due_date=past_date,
    )

    with pytest.raises(ValidationError):
        await service.create_task(test_user.id, task_data)


@pytest.mark.asyncio
async def test_get_task(db: AsyncSession, test_user, test_task):
    """タスク取得のテスト。"""
    service = TaskService(db)
    task = await service.get_task(test_task.id, test_user.id)

    assert task.id == test_task.id
    assert task.title == test_task.title


@pytest.mark.asyncio
async def test_get_task_permission_denied(db: AsyncSession, test_user, test_task, other_user):
    """他のユーザーのタスク取得のテスト（権限エラー）。"""
    service = TaskService(db)

    with pytest.raises(PermissionDeniedError):
        await service.get_task(test_task.id, other_user.id)
```

`tests/api/test_tasks.py`を作成：

```python
"""タスクAPIのテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers):
    """タスク作成APIのテスト。"""
    response = await client.post(
        "/api/tasks/",
        json={"title": "Test Task", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_headers):
    """タスクリスト取得APIのテスト。"""
    response = await client.get("/api/tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
```

## チェックリスト

完全な機能モジュール追加のチェックリスト：

### 計画・設計
- [ ] 機能要件の定義
- [ ] データモデルの設計
- [ ] API仕様の設計
- [ ] エラーハンドリング戦略の検討

### 実装
- [ ] SQLAlchemyモデルの作成
- [ ] Enum型の定義（必要な場合）
- [ ] モデルのインポート設定
- [ ] リレーションシップの定義
- [ ] マイグレーションの生成と適用
- [ ] Pydanticスキーマの作成（Create/Update/Response）
- [ ] スキーマのインポート設定
- [ ] リポジトリクラスの作成
- [ ] カスタムクエリメソッドの実装
- [ ] リポジトリのインポート設定
- [ ] サービスクラスの作成
- [ ] ビジネスロジックの実装
- [ ] バリデーションとエラー処理
- [ ] サービスのインポート設定
- [ ] 依存性注入の設定
- [ ] APIルートの作成
- [ ] ルーターの登録

### テスト
- [ ] ユニットテスト（サービス層）
- [ ] 統合テスト（API層）
- [ ] エッジケースのテスト
- [ ] 権限チェックのテスト

### ドキュメント
- [ ] APIドキュメント（OpenAPI）の確認
- [ ] コード内のdocstringの追加
- [ ] 使用例の作成

## よくある落とし穴

### 1. 循環インポート

```python
# 悪い例
# models/task.py
from app.models.user import User  # 直接インポート

# 良い例
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User  # 型チェック時のみ
```

### 2. 権限チェックの欠如

```python
# 悪い例
async def get_task(self, task_id: int):
    return await self.repository.get(task_id)

# 良い例
async def get_task(self, task_id: int, user_id: int):
    task = await self.repository.get(task_id)
    if task.user_id != user_id:
        raise PermissionDeniedError("Access denied")
    return task
```

### 3. トランザクション管理

```python
# 悪い例
async def create_task(self, data):
    task = await self.repository.create(**data)
    await self.db.commit()  # サービス層でcommitしない

# 良い例
async def create_task(self, data):
    task = await self.repository.create(**data)
    # commitはエンドポイント層で自動実行される
    return task
```

## ベストプラクティス

### 1. レイヤー分離

各層の責務を明確に分離：

- **モデル層**: データ構造とリレーション
- **リポジトリ層**: データアクセスのみ
- **サービス層**: ビジネスロジックと検証
- **API層**: リクエスト/レスポンスの変換

### 2. エラーハンドリング

```python
# カスタム例外を使用
raise NotFoundError("Task not found")
raise PermissionDeniedError("Access denied")
raise ValidationError("Invalid data")
```

### 3. 型安全性

```python
# 完全な型ヒントを使用
async def get_task(self, task_id: int, user_id: int) -> Task:
    pass

# Enum型を活用
status: TaskStatus = TaskStatus.TODO
```

### 4. テスタビリティ

```python
# フィクスチャを活用
@pytest.fixture
async def test_task(db, test_user):
    task = Task(title="Test", user_id=test_user.id)
    db.add(task)
    await db.commit()
    return task
```

## 参考リンク

### プロジェクト内リンク

- [新しいモデル追加](./02-add-model.md)
- [新しいエンドポイント追加](./01-add-endpoint.md)
- [アーキテクチャ概要](../02-architecture/01-overview.md)
- [テスト戦略](../05-testing/01-unit-testing.md)

### 公式ドキュメント

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic](https://docs.pydantic.dev/)
