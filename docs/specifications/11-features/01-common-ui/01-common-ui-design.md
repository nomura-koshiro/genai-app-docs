# 共通UI バックエンド設計書（UI-001〜UI-011）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムの共通UIコンポーネント（ヘッダー、サイドバー）に関するバックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **サイドバー** | UI-001 | 権限に応じたメニューを表示する |
| | UI-002 | 参画プロジェクト数に応じて遷移先を切り替える |
| **ヘッダー（コンテキスト）** | UI-003 | ユーザーコンテキスト情報を取得する |
| **ヘッダー（検索）** | UI-004 | プロジェクト・セッション・ファイル・ツリーを横断検索する |
| | UI-005 | 検索結果をフィルタリングする |
| **ヘッダー（通知）** | UI-006 | 未読通知一覧を取得する |
| | UI-007 | 通知詳細を取得する |
| | UI-008 | 通知を既読にする |
| | UI-009 | すべての通知を既読にする |
| | UI-010 | 通知を削除する |
| | UI-011 | 未読通知バッジを表示する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 1テーブル（user_notification） |
| APIエンドポイント | 7エンドポイント |
| Pydanticスキーマ | 16スキーマ |
| サービス | 3サービス |

---

## 2. データベース設計

### 2.1 関連テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| user_notification | ユーザー通知 |

### 2.2 テーブル定義

#### user_notification

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|---|------|----------|------|
| id | UUID | NO | gen_random_uuid() | 主キー |
| user_id | UUID | NO | - | 対象ユーザーID（FK: user_account.id） |
| type | VARCHAR(50) | NO | - | 通知タイプ |
| title | VARCHAR(255) | NO | - | 通知タイトル |
| message | TEXT | YES | - | 通知メッセージ |
| icon | VARCHAR(10) | YES | - | 通知アイコン（絵文字） |
| link_url | VARCHAR(500) | YES | - | 遷移先URL |
| reference_type | VARCHAR(50) | YES | - | 参照タイプ（project/session/file/tree） |
| reference_id | UUID | YES | - | 参照ID |
| is_read | BOOLEAN | NO | false | 既読フラグ |
| read_at | TIMESTAMP | YES | - | 既読日時 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 作成日時 |

**インデックス**:

| インデックス名 | カラム | 説明 |
|---------------|-------|------|
| ix_user_notification_user_id | user_id | ユーザーID検索 |
| ix_user_notification_user_unread | user_id, is_read | 未読通知検索 |
| ix_user_notification_created_at | created_at DESC | 新着順ソート |

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/user_account/me/context` | ユーザーコンテキスト取得 | 認証済 | UI-001〜UI-003, UI-011 |
| GET | `/api/v1/search` | グローバル検索 | 認証済 | UI-004, UI-005 |
| GET | `/api/v1/notifications` | 通知一覧取得 | 認証済 | UI-006 |
| GET | `/api/v1/notifications/{notification_id}` | 通知詳細取得 | 認証済 | UI-007 |
| PATCH | `/api/v1/notifications/{notification_id}/read` | 通知を既読にする | 認証済 | UI-008 |
| PATCH | `/api/v1/notifications/read-all` | すべて既読にする | 認証済 | UI-009 |
| DELETE | `/api/v1/notifications/{notification_id}` | 通知削除 | 認証済 | UI-010 |

### 3.2 リクエスト/レスポンス定義

#### GET /api/v1/user_account/me/context（ユーザーコンテキスト取得）

ログイン直後およびページリロード時に呼び出され、UIの動的表示に必要な情報をまとめて返却する。

**レスポンス**: `UserContextResponse`

```json
{
  "user": {
    "id": "uuid",
    "displayName": "田中 太郎",
    "email": "tanaka@example.com",
    "roles": ["user"]
  },
  "permissions": {
    "isSystemAdmin": false,
    "canAccessAdminPanel": false,
    "canManageUsers": false,
    "canManageMasters": false,
    "canViewAuditLogs": false
  },
  "navigation": {
    "projectCount": 1,
    "defaultProjectId": "uuid",
    "defaultProjectName": "売上分析プロジェクト",
    "projectNavigationType": "detail"
  },
  "notifications": {
    "unreadCount": 3
  },
  "sidebar": {
    "visibleSections": ["dashboard", "project", "analysis", "driver-tree", "file"],
    "hiddenSections": ["system-admin", "monitoring", "operations"]
  }
}
```

#### GET /api/v1/search（グローバル検索）

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| q | string | ○ | 検索クエリ（2文字以上） |
| type | string | - | 検索対象タイプ（project/session/file/tree）、カンマ区切りで複数指定可 |
| project_id | UUID | - | プロジェクトIDで絞り込み |
| limit | int | - | 取得件数（デフォルト: 20、最大: 100） |

**レスポンス**: `SearchResponse`

```json
{
  "results": [
    {
      "type": "project",
      "id": "uuid",
      "name": "売上分析プロジェクト",
      "description": "Q4売上の分析...",
      "matchedField": "name",
      "highlightedText": "<mark>売上</mark>分析プロジェクト",
      "projectId": null,
      "projectName": null,
      "updatedAt": "datetime",
      "url": "/projects/uuid"
    }
  ],
  "total": 15,
  "query": "売上",
  "types": ["project", "session", "file", "tree"]
}
```

#### GET /api/v1/notifications（通知一覧取得）

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| is_read | boolean | - | 既読/未読フィルター |
| skip | int | - | スキップ数（デフォルト: 0） |
| limit | int | - | 取得件数（デフォルト: 20、最大: 100） |

**レスポンス**: `NotificationListResponse`

```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "member_added",
      "title": "新しいメンバーが追加されました",
      "message": "佐藤 次郎が売上分析プロジェクトに追加されました",
      "icon": "👥",
      "linkUrl": "/projects/uuid/members",
      "referenceType": "project",
      "referenceId": "uuid",
      "isRead": false,
      "createdAt": "datetime"
    }
  ],
  "total": 10,
  "unreadCount": 3,
  "skip": 0,
  "limit": 20
}
```

#### PATCH /api/v1/notifications/{notification_id}/read（既読にする）

**レスポンス**: `NotificationInfo`

#### PATCH /api/v1/notifications/read-all（すべて既読にする）

**レスポンス**: `ReadAllResponse`

```json
{
  "updatedCount": 5
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class SearchTypeEnum(str, Enum):
    """検索対象タイプ"""
    project = "project"
    session = "session"
    file = "file"
    tree = "tree"

class NotificationTypeEnum(str, Enum):
    """通知タイプ"""
    member_added = "member_added"
    member_removed = "member_removed"
    session_complete = "session_complete"
    file_uploaded = "file_uploaded"
    tree_updated = "tree_updated"
    project_invitation = "project_invitation"
    system_announcement = "system_announcement"

class ReferenceTypeEnum(str, Enum):
    """参照タイプ"""
    project = "project"
    session = "session"
    file = "file"
    tree = "tree"
```

### 4.2 Info/Dataスキーマ

```python
# ユーザーコンテキスト関連
class UserContextInfo(CamelCaseModel):
    """ユーザー基本情報"""
    id: UUID
    display_name: str
    email: str
    roles: list[str]

class PermissionsInfo(CamelCaseModel):
    """権限情報"""
    is_system_admin: bool
    can_access_admin_panel: bool
    can_manage_users: bool
    can_manage_masters: bool
    can_view_audit_logs: bool

class NavigationInfo(CamelCaseModel):
    """ナビゲーション情報"""
    project_count: int
    default_project_id: UUID | None = None
    default_project_name: str | None = None
    project_navigation_type: Literal["list", "detail"]

class NotificationBadgeInfo(CamelCaseModel):
    """通知バッジ情報"""
    unread_count: int

class SidebarInfo(CamelCaseModel):
    """サイドバー表示情報"""
    visible_sections: list[str]
    hidden_sections: list[str]

# 検索関連
class SearchResultInfo(CamelCaseModel):
    """検索結果情報"""
    type: SearchTypeEnum
    id: UUID
    name: str
    description: str | None = None
    matched_field: str
    highlighted_text: str
    project_id: UUID | None = None
    project_name: str | None = None
    updated_at: datetime
    url: str

# 通知関連
class NotificationInfo(CamelCaseModel):
    """通知情報"""
    id: UUID
    type: NotificationTypeEnum
    title: str
    message: str | None = None
    icon: str | None = None
    link_url: str | None = None
    reference_type: ReferenceTypeEnum | None = None
    reference_id: UUID | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime
```

### 4.3 Request/Responseスキーマ

```python
# ユーザーコンテキスト
class UserContextResponse(CamelCaseModel):
    user: UserContextInfo
    permissions: PermissionsInfo
    navigation: NavigationInfo
    notifications: NotificationBadgeInfo
    sidebar: SidebarInfo

# 検索
class SearchQuery(CamelCaseModel):
    q: str = Field(..., min_length=2, max_length=100)
    type: list[SearchTypeEnum] | None = None
    project_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)

class SearchResponse(CamelCaseModel):
    results: list[SearchResultInfo]
    total: int
    query: str
    types: list[SearchTypeEnum]

# 通知
class NotificationListResponse(CamelCaseModel):
    notifications: list[NotificationInfo]
    total: int
    unread_count: int
    skip: int
    limit: int

class ReadAllResponse(CamelCaseModel):
    updated_count: int
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| UserContextService | ユーザーコンテキスト情報の集約・生成 |
| GlobalSearchService | 横断検索、結果マージ、ハイライト生成 |
| NotificationService | 通知CRUD、既読管理、通知生成 |

### 5.2 主要メソッド

#### UserContextService

```python
class UserContextService:
    async def get_user_context(user_id: UUID) -> UserContextResponse
    def _build_permissions(roles: list[str]) -> PermissionsInfo
    async def _build_navigation(user_id: UUID) -> NavigationInfo
    def _build_sidebar(permissions: PermissionsInfo) -> SidebarInfo
```

#### GlobalSearchService

```python
class GlobalSearchService:
    async def search(
        query: str,
        types: list[SearchTypeEnum] | None,
        project_id: UUID | None,
        user_id: UUID,
        limit: int = 20
    ) -> SearchResponse

    async def _search_projects(query: str, user_id: UUID, limit: int) -> list[SearchResultInfo]
    async def _search_sessions(query: str, user_id: UUID, project_id: UUID | None, limit: int) -> list[SearchResultInfo]
    async def _search_files(query: str, user_id: UUID, project_id: UUID | None, limit: int) -> list[SearchResultInfo]
    async def _search_trees(query: str, user_id: UUID, project_id: UUID | None, limit: int) -> list[SearchResultInfo]
    def _highlight_text(text: str, query: str) -> str
    def _merge_results(results: list[list[SearchResultInfo]], limit: int) -> list[SearchResultInfo]
```

#### NotificationService

```python
class NotificationService:
    async def list_notifications(user_id: UUID, is_read: bool | None, skip: int, limit: int) -> list[UserNotification]
    async def count_notifications(user_id: UUID, is_read: bool | None) -> int
    async def count_unread(user_id: UUID) -> int
    async def get_notification(notification_id: UUID, user_id: UUID) -> UserNotification | None
    async def mark_as_read(notification_id: UUID, user_id: UUID) -> UserNotification
    async def mark_all_as_read(user_id: UUID) -> int
    async def create_notification(data: NotificationCreate) -> UserNotification
    async def delete_notification(notification_id: UUID, user_id: UUID) -> None
```

### 5.3 ビジネスロジック

#### 権限判定ロジック

```python
def _build_permissions(roles: list[str]) -> PermissionsInfo:
    is_admin = "system_admin" in roles
    return PermissionsInfo(
        is_system_admin=is_admin,
        can_access_admin_panel=is_admin,
        can_manage_users=is_admin,
        can_manage_masters=is_admin,
        can_view_audit_logs=is_admin,
    )
```

#### ナビゲーション判定ロジック

```python
async def _build_navigation(user_id: UUID) -> NavigationInfo:
    projects = await project_member_repo.get_user_projects(user_id, status="active")
    project_count = len(projects)

    if project_count == 1:
        return NavigationInfo(
            project_count=1,
            default_project_id=projects[0].id,
            default_project_name=projects[0].name,
            project_navigation_type="detail",
        )
    else:
        return NavigationInfo(
            project_count=project_count,
            default_project_id=None,
            default_project_name=None,
            project_navigation_type="list",
        )
```

#### サイドバー表示判定ロジック

```python
SIDEBAR_SECTIONS = {
    "dashboard": {"roles": ["user", "system_admin"]},
    "project": {"roles": ["user", "system_admin"]},
    "analysis": {"roles": ["user", "system_admin"]},
    "driver-tree": {"roles": ["user", "system_admin"]},
    "file": {"roles": ["user", "system_admin"]},
    "system-admin": {"roles": ["system_admin"]},
    "monitoring": {"roles": ["system_admin"]},
    "operations": {"roles": ["system_admin"]},
}
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [共通UI フロントエンド設計書](./02-common-ui-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| UI-001 | 権限に応じたメニューを表示する | `GET /user_account/me/context` | sidebar | 設計済 |
| UI-002 | 参画プロジェクト数に応じて遷移先を切り替える | `GET /user_account/me/context` | sidebar | 設計済 |
| UI-003 | ユーザーコンテキスト情報を取得する | `GET /user_account/me/context` | header | 設計済 |
| UI-004 | プロジェクト・セッション・ファイル・ツリーを横断検索する | `GET /search` | header-search | 設計済 |
| UI-005 | 検索結果をフィルタリングする | `GET /search?type=` | header-search | 設計済 |
| UI-006 | 未読通知一覧を取得する | `GET /notifications` | header-notification | 設計済 |
| UI-007 | 通知詳細を取得する | `GET /notifications/{id}` | header-notification | 設計済 |
| UI-008 | 通知を既読にする | `PATCH /notifications/{id}/read` | header-notification | 設計済 |
| UI-009 | すべての通知を既読にする | `PATCH /notifications/read-all` | header-notification | 設計済 |
| UI-010 | 通知を削除する | `DELETE /notifications/{id}` | header-notification | 設計済 |
| UI-011 | 未読通知バッジを表示する | `GET /user_account/me/context` | header | 設計済 |

---

## 8. 関連ドキュメント

- **ユーザー管理**: [../03-user-management/01-user-management-design.md](../03-user-management/01-user-management-design.md)
- **モックアップ**: [../../03-mockup/index.html](../../03-mockup/index.html)
- **API共通仕様**: [../02-api-overview/01-api-overview.md](../02-api-overview/01-api-overview.md)
- **システム管理（管理者通知）**: [../11-system-admin/01-system-admin-design.md](../11-system-admin/01-system-admin-design.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | COMMON-UI-DESIGN-001 |
| 対象ユースケース | UI-001〜UI-011 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/schemas/common/user_context.py` |
|  | `src/app/schemas/search/search.py` |
|  | `src/app/schemas/notification/notification.py` |
|  | `src/app/api/routes/v1/user_accounts/context.py` |
|  | `src/app/api/routes/v1/search/search.py` |
|  | `src/app/api/routes/v1/notifications/notification.py` |
|  | `src/app/services/common/user_context_service.py` |
|  | `src/app/services/search/global_search.py` |
|  | `src/app/services/notification/notification_service.py` |
