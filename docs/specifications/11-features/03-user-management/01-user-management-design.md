# ユーザー管理 バックエンド設計書（U-001〜U-013）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのユーザー管理機能（ユースケースU-001〜U-013）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **認証・アカウント管理** | U-001 | Azure ADでログインする |
| | U-002 | ユーザーアカウントを作成する |
| | U-003 | ユーザー情報を更新する |
| | U-004 | ユーザーを無効化する（論理削除） |
| | U-005 | ユーザーを有効化する |
| | U-006 | 最終ログイン日時を記録する |
| | U-007 | ユーザー一覧を取得する |
| | U-008 | ユーザー詳細を取得する |
| **ロール管理** | U-009 | システムロールを付与する |
| | U-010 | システムロールを剥奪する |
| | U-011 | ユーザーのロールを確認する |
| **ユーザー設定** | U-012 | ユーザー設定を取得する |
| | U-013 | ユーザー設定を更新する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 3テーブル（user_account, role_history, user_settings） |
| APIエンドポイント | 12エンドポイント |
| Pydanticスキーマ | 14スキーマ |
| サービス | 3サービス |
| フロントエンド画面 | 4画面 |

---

## 2. データベース設計

データベース設計の詳細は以下を参照してください：

- [データベース設計書 - 3.2 ユーザー管理](../../../06-database/01-database-design.md#32-ユーザー管理)

### 2.1 関連テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| user_account | ユーザーアカウント情報 |
| role_history | ロール変更履歴 |
| user_settings | ユーザー設定（テーマ、通知、表示設定） |

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/user_account` | ユーザー一覧取得 | system_admin | U-007 |
| GET | `/api/v1/user_account/me` | 現在のユーザー情報取得 | 認証済 | U-008, U-006 |
| GET | `/api/v1/user_account/{user_id}` | 特定ユーザー情報取得 | system_admin | U-008 |
| POST | `/api/v1/user_account/logout` | ログアウト | 認証済 | - |
| PATCH | `/api/v1/user_account/me` | 現在のユーザー情報更新 | 認証済 | U-003 |
| PATCH | `/api/v1/user_account/{user_id}/activate` | ユーザー有効化 | system_admin | U-005 |
| PATCH | `/api/v1/user_account/{user_id}/deactivate` | ユーザー無効化 | system_admin | U-004 |
| PUT | `/api/v1/user_account/{user_id}/role` | ユーザーロール更新 | system_admin | U-009, U-010 |
| DELETE | `/api/v1/user_account/{user_id}` | ユーザー削除 | system_admin | - |
| GET | `/api/v1/user_account/{user_id}/role_history` | ロール変更履歴取得 | system_admin/本人 | U-011 |
| GET | `/api/v1/user_account/me/settings` | ユーザー設定取得 | 認証済 | U-012 |
| PATCH | `/api/v1/user_account/me/settings` | ユーザー設定更新 | 認証済 | U-013 |

### 3.2 リクエスト/レスポンス定義

#### GET /api/v1/user_account（ユーザー一覧取得）

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| skip | int | - | スキップ数（デフォルト: 0） |
| limit | int | - | 取得件数（デフォルト: 100、最大: 1000） |
| azure_id | string | - | Azure AD Object IDで検索 |
| email | string | - | メールアドレスで検索 |

**レスポンス**: `UserAccountListResponse`

```json
{
  "users": [
    {
      "id": "uuid",
      "azureId": "string",
      "email": "string",
      "displayName": "string",
      "roles": ["string"],
      "isActive": true,
      "createdAt": "datetime",
      "updatedAt": "datetime",
      "lastLogin": "datetime",
      "loginCount": 0
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

#### POST /api/v1/user_account/logout（ログアウト）

クライアント側のセッション終了を記録します（Azure ADトークンの無効化はクライアント側で行う）。

**レスポンス (200 OK)**:

```json
{
  "message": "ログアウトしました"
}
```

**備考**:
- サーバー側ではログアウトイベントを記録
- 実際のトークン無効化はAzure AD/フロントエンドで処理

---

#### PUT /api/v1/user_account/{user_id}/role（ロール更新）

**リクエストボディ**: `UserAccountRoleUpdate`

```json
{
  "roles": ["system_admin", "user"]
}
```

**レスポンス**: `UserAccountResponse`

#### GET /api/v1/user_account/me/settings（ユーザー設定取得）

**レスポンス**: `UserSettingsResponse`

```json
{
  "theme": "light",
  "language": "ja",
  "timezone": "Asia/Tokyo",
  "notifications": {
    "emailEnabled": true,
    "projectInvite": true,
    "sessionComplete": true,
    "treeUpdate": true,
    "systemAnnouncement": true
  },
  "display": {
    "itemsPerPage": 20,
    "defaultProjectView": "grid",
    "showWelcomeMessage": true
  }
}
```

#### PATCH /api/v1/user_account/me/settings（ユーザー設定更新）

**リクエストボディ**: `UserSettingsUpdate`

```json
{
  "theme": "dark",
  "language": "ja",
  "timezone": "Asia/Tokyo",
  "notifications": {
    "emailEnabled": false,
    "projectInvite": true,
    "sessionComplete": true,
    "treeUpdate": false,
    "systemAnnouncement": true
  },
  "display": {
    "itemsPerPage": 50,
    "defaultProjectView": "list",
    "showWelcomeMessage": false
  }
}
```

**レスポンス**: `UserSettingsResponse`

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class SystemRoleEnum(str, Enum):
    """システムロール"""
    system_admin = "system_admin"  # システム管理者
    user = "user"                  # 一般ユーザー

class ThemeEnum(str, Enum):
    """テーマ設定"""
    light = "light"
    dark = "dark"
    system = "system"  # システム設定に従う

class LanguageEnum(str, Enum):
    """言語設定"""
    ja = "ja"  # 日本語
    en = "en"  # 英語

class ProjectViewEnum(str, Enum):
    """プロジェクト表示形式"""
    grid = "grid"   # グリッド表示
    list = "list"   # リスト表示
```

### 4.2 Info/Dataスキーマ

```python
class UserAccountInfo(CamelCaseModel):
    """ユーザーアカウント情報"""
    id: UUID
    azure_id: str
    email: str
    display_name: str | None = None
    roles: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    login_count: int = 0

class UserActivityStats(CamelCaseModel):
    """ユーザー統計情報"""
    project_count: int
    session_count: int
    tree_count: int

class ProjectParticipationInfo(CamelCaseModel):
    """参加プロジェクト情報"""
    project_id: UUID
    project_name: str
    project_role: str
    joined_at: datetime
    status: str

class RecentActivityInfo(CamelCaseModel):
    """最近のアクティビティ情報"""
    activity_type: str
    activity_detail: str
    activity_at: datetime
    project_name: str | None = None

class RoleHistoryInfo(CamelCaseModel):
    """ロール変更履歴情報"""
    id: UUID
    user_id: UUID
    old_roles: list[str] | None = None
    new_roles: list[str]
    changed_by: UUID | None = None
    reason: str | None = None
    created_at: datetime

class NotificationSettingsInfo(CamelCaseModel):
    """通知設定情報"""
    email_enabled: bool = True
    project_invite: bool = True
    session_complete: bool = True
    tree_update: bool = True
    system_announcement: bool = True

class DisplaySettingsInfo(CamelCaseModel):
    """表示設定情報"""
    items_per_page: int = Field(default=20, ge=10, le=100)
    default_project_view: ProjectViewEnum = ProjectViewEnum.grid
    show_welcome_message: bool = True

class UserSettingsInfo(CamelCaseModel):
    """ユーザー設定情報"""
    theme: ThemeEnum = ThemeEnum.light
    language: LanguageEnum = LanguageEnum.ja
    timezone: str = "Asia/Tokyo"
    notifications: NotificationSettingsInfo
    display: DisplaySettingsInfo
```

### 4.3 Request/Responseスキーマ

```python
# ユーザー更新
class UserAccountUpdate(CamelCaseModel):
    display_name: str | None = Field(None, max_length=255)
    roles: list[str] | None = None
    is_active: bool | None = None

# ロール更新
class UserAccountRoleUpdate(CamelCaseModel):
    roles: list[str] = Field(..., min_length=1)

# ユーザー一覧レスポンス
class UserAccountListResponse(CamelCaseModel):
    users: list[UserAccountInfo]
    total: int
    skip: int
    limit: int

# ユーザー詳細レスポンス
class UserAccountDetailResponse(CamelCaseModel):
    id: UUID
    azure_id: str
    email: str
    display_name: str | None = None
    roles: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    login_count: int = 0
    stats: UserActivityStats
    projects: list[ProjectParticipationInfo]
    recent_activities: list[RecentActivityInfo]

# ロール履歴レスポンス
class RoleHistoryListResponse(CamelCaseModel):
    histories: list[RoleHistoryInfo]
    total: int
    skip: int
    limit: int

# ユーザー設定更新
class NotificationSettingsUpdate(CamelCaseModel):
    email_enabled: bool | None = None
    project_invite: bool | None = None
    session_complete: bool | None = None
    tree_update: bool | None = None
    system_announcement: bool | None = None

class DisplaySettingsUpdate(CamelCaseModel):
    items_per_page: int | None = Field(None, ge=10, le=100)
    default_project_view: ProjectViewEnum | None = None
    show_welcome_message: bool | None = None

class UserSettingsUpdate(CamelCaseModel):
    theme: ThemeEnum | None = None
    language: LanguageEnum | None = None
    timezone: str | None = None
    notifications: NotificationSettingsUpdate | None = None
    display: DisplaySettingsUpdate | None = None

# ユーザー設定レスポンス
class UserSettingsResponse(CamelCaseModel):
    theme: ThemeEnum
    language: LanguageEnum
    timezone: str
    notifications: NotificationSettingsInfo
    display: DisplaySettingsInfo
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| UserAccountService | ユーザーCRUD、認証、ロール管理 |
| RoleHistoryService | ロール変更履歴管理 |
| UserSettingsService | ユーザー設定の取得・更新 |

### 5.2 主要メソッド

#### UserAccountService

```python
class UserAccountService:
    # ユーザー一覧・取得
    async def list_users(skip: int, limit: int) -> list[UserAccount]
    async def count_users() -> int
    async def get_user(user_id: UUID) -> UserAccount | None
    async def get_user_by_azure_id(azure_id: str) -> UserAccount | None
    async def get_user_by_email(email: str) -> UserAccount | None

    # ユーザー詳細情報取得
    async def get_user_stats(user_id: UUID) -> UserActivityStats
    async def get_user_projects(user_id: UUID) -> list[ProjectParticipationInfo]
    async def get_user_recent_activities(user_id: UUID, limit: int = 10) -> list[RecentActivityInfo]

    # ユーザー更新
    async def update_user(user_id: UUID, update_data: UserAccountUpdate, current_user_roles: list[str]) -> UserAccount
    async def update_last_login(user_id: UUID, client_ip: str | None = None) -> UserAccount

    # 有効化・無効化
    async def activate_user(user_id: UUID) -> UserAccount
    async def deactivate_user(user_id: UUID) -> UserAccount

    # ロール管理
    async def update_user_role(user_id: UUID, roles: list[str], changed_by: UUID, reason: str | None = None) -> UserAccount

    # 削除
    async def delete_user(user_id: UUID) -> None
```

#### RoleHistoryService

```python
class RoleHistoryService:
    # 履歴取得
    async def get_user_role_history(user_id: UUID, skip: int, limit: int) -> list[RoleHistory]
    async def count_user_role_history(user_id: UUID) -> int

    # 履歴作成
    async def create_role_history(
        user_id: UUID,
        old_roles: list[str] | None,
        new_roles: list[str],
        changed_by: UUID | None,
        reason: str | None = None
    ) -> RoleHistory
```

#### UserSettingsService

```python
class UserSettingsService:
    # 設定取得
    async def get_user_settings(user_id: UUID) -> UserSettings
    async def get_or_create_default_settings(user_id: UUID) -> UserSettings

    # 設定更新
    async def update_user_settings(user_id: UUID, update_data: UserSettingsUpdate) -> UserSettings

    # 個別設定更新
    async def update_notification_settings(user_id: UUID, settings: NotificationSettingsUpdate) -> UserSettings
    async def update_display_settings(user_id: UUID, settings: DisplaySettingsUpdate) -> UserSettings
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [ユーザー管理 フロントエンド設計書](./02-user-management-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| U-001 | Azure ADでログインする | Azure AD認証 | - | 実装済 |
| U-002 | ユーザーアカウントを作成する | 初回ログイン時自動作成 | - | 実装済 |
| U-003 | ユーザー情報を更新する | `PATCH /user_account/me` | user-detail | 実装済 |
| U-004 | ユーザーを無効化する | `PATCH /user_account/{id}/deactivate` | users, user-detail | 実装済 |
| U-005 | ユーザーを有効化する | `PATCH /user_account/{id}/activate` | users, user-detail | 実装済 |
| U-006 | 最終ログイン日時を記録する | `GET /user_account/me` | - | 実装済 |
| U-007 | ユーザー一覧を取得する | `GET /user_account` | users | 実装済 |
| U-008 | ユーザー詳細を取得する | `GET /user_account/{id}` | user-detail | 実装済 |
| U-009 | システムロールを付与する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-010 | システムロールを剥奪する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-011 | ユーザーのロールを確認する | `GET /user_account/{id}/role_history` | user-detail | 実装済 |
| U-012 | ユーザー設定を取得する | `GET /user_account/me/settings` | settings | 設計済 |
| U-013 | ユーザー設定を更新する | `PATCH /user_account/me/settings` | settings | 設計済 |

---

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/admin.js](../../03-mockup/pages/admin.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | UM-DESIGN-001 |
| 対象ユースケース | U-001〜U-011 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/models/user_account/user_account.py` |
|  | `src/app/schemas/user_account/user_account.py` |
|  | `src/app/api/routes/v1/user_accounts/user_account.py` |
