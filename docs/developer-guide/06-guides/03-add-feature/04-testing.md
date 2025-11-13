# ステップ10: テストとベストプラクティス

このドキュメントでは、テストの作成方法、チェックリスト、よくある落とし穴、ベストプラクティスについて説明します。

[← 前へ: サービスとAPI](./03-add-feature-services-api.md) | [↑ 機能モジュール追加ガイド](./03-add-feature.md)

## 目次

- [ステップ10: テストの作成](#ステップ10-テストの作成)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)

## ステップ10: テストの作成

### サービステスト

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

### APIテスト

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
from app.models.sample_user import SampleUser  # 直接インポート

# 良い例
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.sample_user import SampleUser  # 型チェック時のみ
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

## 完了

おめでとうございます！完全な機能モジュールの追加が完了しました。

**[← 機能モジュール追加ガイドに戻る](./03-add-feature.md)**

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
