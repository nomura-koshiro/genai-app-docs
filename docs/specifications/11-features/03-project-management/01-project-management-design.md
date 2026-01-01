# プロジェクト管理 バックエンド設計書（P-001〜PF-006）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのプロジェクト管理機能（ユースケースP-001〜PF-006）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **プロジェクト基本操作** | P-001 | プロジェクトを作成する |
| | P-002 | プロジェクト情報を更新する |
| | P-003 | プロジェクトを無効化する（論理削除） |
| | P-004 | プロジェクトを有効化する |
| | P-005 | プロジェクト一覧を取得する |
| | P-006 | プロジェクト詳細を取得する |
| | P-007 | プロジェクトコードで検索する |
| **プロジェクトメンバー管理** | PM-001 | メンバーをプロジェクトに追加する |
| | PM-002 | メンバーをプロジェクトから削除する |
| | PM-003 | メンバーのロールを変更する |
| | PM-004 | プロジェクトメンバー一覧を取得する |
| | PM-005 | ユーザーが参加しているプロジェクト一覧を取得する |
| | PM-006 | メンバーの権限を確認する |
| **プロジェクトファイル管理** | PF-001 | ファイルをアップロードする |
| | PF-002 | ファイルをダウンロードする |
| | PF-003 | ファイルを削除する |
| | PF-004 | プロジェクトのファイル一覧を取得する |
| | PF-005 | ファイル詳細を取得する |
| | PF-006 | ファイルのアップロード者を確認する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 3テーブル（project, project_member, project_file） |
| APIエンドポイント | 21エンドポイント |
| Pydanticスキーマ | 20スキーマ |
| サービス | 3サービス |
| フロントエンド画面 | 6画面 |

---

## 2. データベース設計

データベース設計の詳細は以下を参照してください：

- [データベース設計書 - 3.3 プロジェクト管理](../../../06-database/01-database-design.md#33-プロジェクト管理)

### 2.1 関連テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| project | プロジェクト基本情報 |
| project_member | プロジェクトメンバー管理 |
| project_file | プロジェクトファイル管理 |

---

## 3. APIエンドポイント設計

### 3.1 プロジェクト基本操作

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project` | プロジェクト一覧取得 | 認証済 | P-005, PM-005 |
| GET | `/api/v1/project/{project_id}` | プロジェクト詳細取得 | メンバー | P-006 |
| GET | `/api/v1/project/code/{code}` | コードでプロジェクト検索 | メンバー | P-007 |
| POST | `/api/v1/project` | プロジェクト作成 | 認証済 | P-001 |
| PATCH | `/api/v1/project/{project_id}` | プロジェクト更新 | PM/Admin | P-002, P-003, P-004 |
| DELETE | `/api/v1/project/{project_id}` | プロジェクト削除 | PM | - |

### 3.2 プロジェクトメンバー管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project/{project_id}/member` | メンバー一覧取得 | メンバー | PM-004 |
| GET | `/api/v1/project/{project_id}/member/me` | 自分のロール取得 | メンバー | PM-006 |
| POST | `/api/v1/project/{project_id}/member` | メンバー追加 | PM | PM-001 |
| POST | `/api/v1/project/{project_id}/member/bulk` | メンバー一括追加 | PM | PM-001 |
| PATCH | `/api/v1/project/{project_id}/member/{member_id}` | ロール更新 | PM | PM-003 |
| DELETE | `/api/v1/project/{project_id}/member/{member_id}` | メンバー削除 | PM | PM-002 |
| DELETE | `/api/v1/project/{project_id}/member/me` | プロジェクト退出 | メンバー | - |

### 3.3 プロジェクトファイル管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project/{project_id}/file` | ファイル一覧取得 | メンバー | PF-004 |
| GET | `/api/v1/project/{project_id}/file/{file_id}` | ファイル詳細取得 | メンバー | PF-005, PF-006 |
| GET | `/api/v1/project/{project_id}/file/{file_id}/download` | ファイルダウンロード | メンバー | PF-002 |
| GET | `/api/v1/project/{project_id}/file/{file_id}/usage` | ファイル使用状況取得 | メンバー | - |
| GET | `/api/v1/project/{project_id}/file/{file_id}/versions` | バージョン履歴取得 | メンバー | - |
| POST | `/api/v1/project/{project_id}/file` | ファイルアップロード | メンバー | PF-001 |
| POST | `/api/v1/project/{project_id}/file/{file_id}/version` | 新バージョンアップロード | メンバー | - |
| DELETE | `/api/v1/project/{project_id}/file/{file_id}` | ファイル削除 | PM/Mod | PF-003 |

### 3.4 主要レスポンス定義

#### ProjectDetailResponse

```json
{
  "id": "uuid",
  "name": "string",
  "code": "string",
  "description": "string",
  "isActive": true,
  "createdBy": "uuid",
  "startDate": "date",
  "endDate": "date",
  "budget": "decimal",
  "createdAt": "datetime",
  "updatedAt": "datetime",
  "stats": {
    "memberCount": 5,
    "fileCount": 10,
    "sessionCount": 2,
    "treeCount": 1
  }
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class ProjectRoleEnum(str, Enum):
    """プロジェクトロール"""
    project_manager = "project_manager"      # プロジェクト管理者
    project_moderator = "project_moderator"  # モデレーター
    member = "member"                        # 一般メンバー
    viewer = "viewer"                        # 閲覧者
```

### 4.2 Info/Dataスキーマ

```python
class ProjectInfo(CamelCaseModel):
    """プロジェクト情報"""
    id: UUID
    name: str
    code: str
    description: str | None = None
    is_active: bool
    created_by: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = None
    created_at: datetime
    updated_at: datetime

class ProjectStats(CamelCaseModel):
    """プロジェクト統計情報"""
    member_count: int
    file_count: int
    session_count: int
    tree_count: int

class ProjectMemberInfo(CamelCaseModel):
    """プロジェクトメンバー情報"""
    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectRoleEnum
    joined_at: datetime
    added_by: UUID | None = None
    last_activity_at: datetime | None = None
    user: UserAccountInfo | None = None

class ProjectFileInfo(CamelCaseModel):
    """プロジェクトファイル情報"""
    id: UUID
    project_id: UUID
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str | None = None
    uploaded_by: UUID
    uploaded_at: datetime
    version: int = 1
    parent_file_id: UUID | None = None
    is_latest: bool = True
```

### 4.3 Request/Responseスキーマ

```python
# プロジェクト作成
class ProjectCreate(CamelCaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = None

# プロジェクト更新
class ProjectUpdate(CamelCaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = None
    is_active: bool | None = None

# プロジェクト一覧レスポンス
class ProjectListResponse(CamelCaseModel):
    projects: list[ProjectInfo]
    total: int
    skip: int
    limit: int

# プロジェクト詳細レスポンス
class ProjectDetailResponse(CamelCaseModel):
    id: UUID
    name: str
    code: str
    description: str | None = None
    is_active: bool
    created_by: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = None
    created_at: datetime
    updated_at: datetime
    stats: ProjectStats

# メンバー追加
class ProjectMemberCreate(CamelCaseModel):
    user_id: UUID
    role: ProjectRoleEnum = ProjectRoleEnum.member

# メンバー一括追加
class ProjectMemberBulkCreate(CamelCaseModel):
    members: list[ProjectMemberCreate]

# メンバー更新
class ProjectMemberUpdate(CamelCaseModel):
    role: ProjectRoleEnum

# メンバー一覧レスポンス
class ProjectMemberListResponse(CamelCaseModel):
    members: list[ProjectMemberInfo]
    total: int
    skip: int
    limit: int

# ファイル一覧レスポンス
class ProjectFileListResponse(CamelCaseModel):
    files: list[ProjectFileInfo]
    total: int
    skip: int
    limit: int

# ファイルバージョン履歴
class ProjectFileVersionHistoryResponse(CamelCaseModel):
    versions: list[ProjectFileInfo]
    total: int
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| ProjectService | プロジェクトCRUD、統計 |
| ProjectMemberService | メンバー管理、ロール制御 |
| ProjectFileService | ファイルアップロード/ダウンロード/削除 |

### 5.2 主要メソッド

#### ProjectService

```python
class ProjectService:
    # プロジェクトCRUD
    async def create_project(data: ProjectCreate, user_id: UUID) -> Project
    async def update_project(project_id: UUID, data: ProjectUpdate) -> Project
    async def delete_project(project_id: UUID) -> None

    # プロジェクト取得
    async def list_user_projects(
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None
    ) -> list[Project]
    async def count_user_projects(user_id: UUID, is_active: bool | None = None) -> int
    async def get_project(project_id: UUID) -> Project | None
    async def get_project_by_code(code: str) -> Project | None

    # 統計
    async def get_project_stats(project_id: UUID) -> ProjectStats
```

#### ProjectMemberService

```python
class ProjectMemberService:
    # メンバー管理
    async def add_member(
        project_id: UUID,
        user_id: UUID,
        role: ProjectRoleEnum,
        added_by: UUID
    ) -> ProjectMember
    async def add_members_bulk(
        project_id: UUID,
        members: list[ProjectMemberCreate],
        added_by: UUID
    ) -> list[ProjectMember]
    async def remove_member(project_id: UUID, member_id: UUID) -> None
    async def update_member_role(
        project_id: UUID,
        member_id: UUID,
        role: ProjectRoleEnum
    ) -> ProjectMember

    # メンバー取得
    async def list_members(
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[ProjectMember]
    async def count_members(project_id: UUID) -> int
    async def get_user_role(project_id: UUID, user_id: UUID) -> ProjectRoleEnum | None

    # 退出
    async def leave_project(project_id: UUID, user_id: UUID) -> None
```

#### ProjectFileService

```python
class ProjectFileService:
    # ファイル操作
    async def upload_file(
        project_id: UUID,
        file: UploadFile,
        user_id: UUID
    ) -> ProjectFile
    async def upload_new_version(
        project_id: UUID,
        file_id: UUID,
        file: UploadFile,
        user_id: UUID
    ) -> ProjectFile
    async def download_file(project_id: UUID, file_id: UUID) -> StreamingResponse
    async def delete_file(project_id: UUID, file_id: UUID) -> None

    # ファイル取得
    async def list_files(
        project_id: UUID,
        skip: int = 0,
        limit: int = 100,
        mime_type: str | None = None
    ) -> list[ProjectFile]
    async def count_files(project_id: UUID) -> int
    async def get_file(project_id: UUID, file_id: UUID) -> ProjectFile | None
    async def get_file_versions(project_id: UUID, file_id: UUID) -> list[ProjectFile]
    async def get_file_usage(project_id: UUID, file_id: UUID) -> dict
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [プロジェクト管理 フロントエンド設計書](./02-project-management-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| P-001 | プロジェクトを作成する | `POST /project` | project-new | 実装済 |
| P-002 | プロジェクト情報を更新する | `PATCH /project/{id}` | project-detail | 実装済 |
| P-003 | プロジェクトを無効化する | `PATCH /project/{id}` | projects | 実装済 |
| P-004 | プロジェクトを有効化する | `PATCH /project/{id}` | projects | 実装済 |
| P-005 | プロジェクト一覧を取得する | `GET /project` | projects | 実装済 |
| P-006 | プロジェクト詳細を取得する | `GET /project/{id}` | project-detail | 実装済 |
| P-007 | プロジェクトコードで検索する | `GET /project/code/{code}` | - | 実装済 |
| PM-001 | メンバーを追加する | `POST /project/{id}/member` | members | 実装済 |
| PM-002 | メンバーを削除する | `DELETE /project/{id}/member/{id}` | members | 実装済 |
| PM-003 | メンバーのロールを変更する | `PATCH /project/{id}/member/{id}` | members | 実装済 |
| PM-004 | メンバー一覧を取得する | `GET /project/{id}/member` | members | 実装済 |
| PM-005 | 参加プロジェクト一覧を取得する | `GET /project` | projects | 実装済 |
| PM-006 | メンバーの権限を確認する | `GET /project/{id}/member/me` | - | 実装済 |
| PF-001 | ファイルをアップロードする | `POST /project/{id}/file` | upload | 実装済 |
| PF-002 | ファイルをダウンロードする | `GET /project/{id}/file/{id}/download` | files | 実装済 |
| PF-003 | ファイルを削除する | `DELETE /project/{id}/file/{id}` | files | 実装済 |
| PF-004 | ファイル一覧を取得する | `GET /project/{id}/file` | files, project-detail | 実装済 |
| PF-005 | ファイル詳細を取得する | `GET /project/{id}/file/{id}` | files | 実装済 |
| PF-006 | アップロード者を確認する | `GET /project/{id}/file/{id}` | files | 実装済 |

---

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/projects.js](../../03-mockup/pages/projects.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | PM-DESIGN-001 |
| 対象ユースケース | P-001〜P-011, PM-001〜PM-006, PF-001〜PF-006 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/models/project/` |
|  | `src/app/schemas/project/` |
|  | `src/app/api/routes/v1/project/` |
