# サービス層（Services）

ビジネスロジックの実装について説明します。

## 概要

サービス層は、ビジネスロジックを実装し、複数のリポジトリを調整します。

**責務**:

- ビジネスルールの実装
- 複数のリポジトリの調整
- トランザクション境界の定義
- ドメインロジックのオーケストレーション

---

## サービス層の構造

サービス層は**Facadeパターン**を採用し、機能ごとにサブサービスに分割されています。

```text
services/
├── __init__.py                      # 全サービスの統合エクスポート
├── storage/                         # Strategyパターンでストレージを抽象化
├── analysis/
│   ├── analysis_session/            # 分析セッション（機能別分割）
│   │   ├── __init__.py              # AnalysisSessionService（Facade）
│   │   ├── service.py
│   │   ├── session_crud.py
│   │   └── ...
│   └── analysis_template.py
├── project/
│   ├── project/                     # プロジェクト管理（機能別分割）
│   │   ├── __init__.py              # ProjectService（Facade）
│   │   ├── base.py
│   │   └── crud.py
│   ├── project_file/                # ファイル管理（機能別分割）
│   └── project_member/              # メンバー管理（機能別分割）
└── user_account/
    └── user_account/                # ユーザー管理（機能別分割）
        ├── __init__.py              # UserAccountService（Facade）
        ├── auth.py
        └── crud.py
```

---

## 基本的なサービス（Facadeパターン）

```python
# src/app/services/project/project/__init__.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.project.project.crud import ProjectCrudService


class ProjectService:
    """プロジェクト管理のビジネスロジックを提供するサービスクラス。

    各機能は専用のサービスクラスに委譲されます（Facadeパターン）。
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._crud_service = ProjectCrudService(db)

    async def create_project(
        self,
        project_data: ProjectCreate,
        creator_id: uuid.UUID,
    ) -> Project:
        """新しいプロジェクトを作成します。"""
        return await self._crud_service.create_project(project_data, creator_id)

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """プロジェクトIDでプロジェクト情報を取得します。"""
        return await self._crud_service.get_project(project_id)

    async def update_project(
        self,
        project_id: uuid.UUID,
        update_data: ProjectUpdate,
        user_id: uuid.UUID,
    ) -> Project:
        """プロジェクト情報を更新します。"""
        return await self._crud_service.update_project(project_id, update_data, user_id)

    async def delete_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトを削除します。"""
        return await self._crud_service.delete_project(project_id, user_id)
```

---

## サブサービスの実装

```python
# src/app/services/project/project/crud.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Project
from app.repositories import ProjectRepository
from app.services.project.project.base import ProjectBaseService


class ProjectCrudService(ProjectBaseService):
    """プロジェクトのCRUD操作を提供するサービス。"""

    async def create_project(
        self,
        project_data: ProjectCreate,
        creator_id: uuid.UUID,
    ) -> Project:
        """新しいプロジェクトを作成します。"""
        # プロジェクトコードの重複チェック
        existing = await self.project_repo.get_by_code(project_data.code)
        if existing:
            raise ValidationError(
                "プロジェクトコードが既に使用されています",
                details={"code": project_data.code}
            )

        # プロジェクト作成
        project = await self.project_repo.create(
            name=project_data.name,
            code=project_data.code,
            description=project_data.description,
            created_by=creator_id,
        )

        # 作成者をOWNERとして追加
        await self.member_repo.create(
            project_id=project.id,
            user_id=creator_id,
            role=ProjectRole.OWNER,
        )

        await self.db.commit()
        return project
```

---

## 複数リポジトリの調整

ベースクラスで複数のリポジトリを初期化し、サブサービスで利用します。

```python
# src/app/services/project/project/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import ProjectRepository, ProjectMemberRepository


class ProjectBaseService:
    """プロジェクトサービスの共通ベースクラス。

    複数のリポジトリを初期化し、サブサービスで共有します。
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.member_repo = ProjectMemberRepository(db)
```

```python
# src/app/services/project/project_member/crud.py
class ProjectMemberCrudService(ProjectMemberBaseService):
    """メンバーのCRUD操作を提供するサービス。"""

    async def add_member(
        self,
        project_id: uuid.UUID,
        member_data: ProjectMemberCreate,
        added_by: uuid.UUID,
    ) -> ProjectMember:
        """プロジェクトに新しいメンバーを追加します。"""
        # プロジェクト存在確認
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("プロジェクトが見つかりません")

        # 権限チェック
        requester_role = await self._get_user_role(project_id, added_by)
        if requester_role not in [ProjectRole.OWNER, ProjectRole.ADMIN]:
            raise ValidationError("メンバー追加の権限がありません")

        # 重複チェック
        existing = await self.member_repo.get_by_project_and_user(
            project_id, member_data.user_id
        )
        if existing:
            raise ValidationError("このユーザーは既にメンバーです")

        # メンバー追加
        member = await self.member_repo.create(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
            added_by=added_by,
        )

        await self.db.commit()
        return member
```

---

## トランザクション管理

```python
# データベースセッションの提供
# src/app/core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # commitはサービス層または@transactionalデコレータが責任を持つ
        except Exception:
            await session.rollback()  # エラー時にロールバック
            raise
        finally:
            await session.close()
```

**設計思想**:

- `get_db()`はセッションの提供のみを担当
- トランザクション境界（commit/rollback）はサービス層が定義
- `@transactional`デコレータ（実装済み）または明示的なcommitで管理

---

## ベストプラクティス

1. **ビジネスロジックはサービス層に**

   ```python
   # ✅ サービス層でバリデーション
   async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
       if await self.repository.get_by_email(user_data.email):
           raise ValidationError("Email already exists")
       return await self.repository.create(...)
   ```

2. **リポジトリを通じてデータアクセス**

   ```python
   # ✅ リポジトリ使用
   user = await self.repository.get(user_id)

   # ❌ 直接DBアクセス
   user = await self.db.get(SampleUser, user_id)
   ```

3. **カスタム例外を使用**

   ```python
   if not user:
       raise NotFoundError("User not found", details={"user_id": user_id})
   ```

---

次のセクション: [05-api.md](./05-api.md)
