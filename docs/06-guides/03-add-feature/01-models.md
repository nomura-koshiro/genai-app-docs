# ステップ1-3: データモデルとマイグレーション

このドキュメントでは、新しい機能モジュールを追加する際のデータモデル設計とマイグレーション作成について説明します。

[← 機能モジュール追加ガイドに戻る](./03-add-feature.md)

## 目次

- [ステップ1: 要件定義](#ステップ1-要件定義)
- [ステップ2: データモデルの設計](#ステップ2-データモデルの設計)
- [ステップ3: マイグレーションの作成と適用](#ステップ3-マイグレーションの作成と適用)

## ステップ1: 要件定義

機能の要件を明確にします：

**タスク管理機能の要件:**

- タスクの作成、読み取り、更新、削除（CRUD）
- タスクの優先度設定（低、中、高）
- タスクのステータス管理（未着手、進行中、完了）
- ユーザーごとのタスク管理
- タスクの期限設定
- タスクの検索とフィルタリング

## ステップ2: データモデルの設計

### 2.1 エンティティの定義

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
        ForeignKey("sample_users.id", ondelete="CASCADE"),
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
    user: Mapped["SampleUser"] = relationship("SampleUser", back_populates="tasks")

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

### 2.2 既存モデルの更新

`src/app/models/sample_user.py`にリレーションシップを追加：

```python
# Relationships
tasks: Mapped[list["Task"]] = relationship(
    "Task",
    back_populates="user",
    cascade="all, delete-orphan",
)
```

### 2.3 モデルのインポート

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

## ステップ3: マイグレーションの作成と適用

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

## 次のステップ

データモデルとマイグレーションの準備が完了したら、次はPydanticスキーマとリポジトリを作成します。

**[→ 次へ: ステップ4-5 スキーマとリポジトリ](./03-add-feature-schemas-repos.md)**

## 参考リンク

- [新しいモデル追加](./02-add-model.md)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [機能モジュール追加ガイド](./03-add-feature.md)
