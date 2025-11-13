# ステップ6-9: サービスとAPI

このドキュメントでは、サービス層の実装、依存性注入の設定、APIルートの作成方法について説明します。

[← 前へ: スキーマとリポジトリ](./03-add-feature-schemas-repos.md) | [↑ 機能モジュール追加ガイド](./03-add-feature.md)

## 目次

- [ステップ6: サービスの作成](#ステップ6-サービスの作成)
- [ステップ7: 依存性注入の設定](#ステップ7-依存性注入の設定)
- [ステップ8: APIルートの作成](#ステップ8-apiルートの作成)
- [ステップ9: ルーターの登録](#ステップ9-ルーターの登録)

## ステップ6: サービスの作成

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

## ステップ7: 依存性注入の設定

`src/app/api/dependencies.py`を更新：

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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

## ステップ8: APIルートの作成

`src/app/api/routes/tasks.py`を作成：

```python
"""タスクAPIルート。"""

from fastapi import APIRouter, Query, status

from app.api.core import CurrentSampleUserDep, TaskServiceDep
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
    current_user: CurrentSampleUserDep,
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
    current_user: CurrentSampleUserDep,
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
    current_user: CurrentSampleUserDep = None,
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
    current_user: CurrentSampleUserDep,
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
    current_user: CurrentSampleUserDep,
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
    current_user: CurrentSampleUserDep,
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
    current_user: CurrentSampleUserDep = None,
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

## ステップ9: ルーターの登録

`src/app/main.py`を更新：

```python
from app.api.routes import agents, files, tasks  # 追加

# Include routers
app.include_router(agents.router, prefix="/api/sample-agents", tags=["agents"])
app.include_router(files.router, prefix="/api/sample-files", tags=["files"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])  # 追加
```

## 次のステップ

サービスとAPIの実装が完了したら、次はテストを作成してベストプラクティスを確認します。

**[→ 次へ: ステップ10 テストとベストプラクティス](./03-add-feature-testing.md)**

## 参考リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [依存性注入](../03-core-concepts/03-dependency-injection.md)
- [機能モジュール追加ガイド](./03-add-feature.md)
