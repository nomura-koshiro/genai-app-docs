# ステップ4-5: スキーマとリポジトリ

このドキュメントでは、Pydanticスキーマとリポジトリの作成方法について説明します。

[← 前へ: データモデルとマイグレーション](./03-add-feature-models.md) | [↑ 機能モジュール追加ガイド](./03-add-feature.md)

## 目次

- [ステップ4: Pydanticスキーマの作成](#ステップ4-pydanticスキーマの作成)
- [ステップ5: リポジトリの作成](#ステップ5-リポジトリの作成)

## ステップ4: Pydanticスキーマの作成

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

## ステップ5: リポジトリの作成

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

## 次のステップ

スキーマとリポジトリの準備が完了したら、次はサービス層とAPI層を作成します。

**[→ 次へ: ステップ6-9 サービスとAPI](./03-add-feature-services-api.md)**

## 参考リンク

- [Pydantic](https://docs.pydantic.dev/)
- [リポジトリパターン](../02-architecture/03-layers.md)
- [機能モジュール追加ガイド](./03-add-feature.md)
