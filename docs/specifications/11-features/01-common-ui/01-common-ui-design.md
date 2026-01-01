# 共通UI バックエンド設計書（UI-001〜UI-004）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムの共通UIコンポーネント（ヘッダー、サイドバー）の動的表示に必要なバックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **サイドバー** | UI-001 | 権限に応じたメニューを表示する |
| | UI-002 | 参画プロジェクト数に応じて遷移先を切り替える |
| **ヘッダー** | UI-003 | ユーザーコンテキスト情報を取得する |
| | UI-004 | 未読通知バッジを表示する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| APIエンドポイント | 1エンドポイント |
| Pydanticスキーマ | 4スキーマ |
| サービス | 1サービス |

---

## 2. APIエンドポイント設計

### 2.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/user_account/me/context` | ユーザーコンテキスト取得 | 認証済 | UI-001〜UI-004 |

### 2.2 リクエスト/レスポンス定義

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
    "visibleSections": [
      "dashboard",
      "project",
      "analysis",
      "driver-tree",
      "file"
    ],
    "hiddenSections": [
      "system-admin",
      "monitoring",
      "operations"
    ]
  }
}
```

**レスポンス例（管理者の場合）**:

```json
{
  "user": {
    "id": "uuid",
    "displayName": "管理者",
    "email": "admin@example.com",
    "roles": ["system_admin", "user"]
  },
  "permissions": {
    "isSystemAdmin": true,
    "canAccessAdminPanel": true,
    "canManageUsers": true,
    "canManageMasters": true,
    "canViewAuditLogs": true
  },
  "navigation": {
    "projectCount": 5,
    "defaultProjectId": null,
    "defaultProjectName": null,
    "projectNavigationType": "list"
  },
  "notifications": {
    "unreadCount": 0
  },
  "sidebar": {
    "visibleSections": [
      "dashboard",
      "project",
      "analysis",
      "driver-tree",
      "file",
      "system-admin",
      "monitoring",
      "operations"
    ],
    "hiddenSections": []
  }
}
```

---

## 3. Pydanticスキーマ設計

### 3.1 Info/Dataスキーマ

```python
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
```

### 3.2 Responseスキーマ

```python
class UserContextResponse(CamelCaseModel):
    """ユーザーコンテキストレスポンス"""
    user: UserContextInfo
    permissions: PermissionsInfo
    navigation: NavigationInfo
    notifications: NotificationBadgeInfo
    sidebar: SidebarInfo
```

---

## 4. サービス層設計

### 4.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| UserContextService | ユーザーコンテキスト情報の集約・生成 |

### 4.2 主要メソッド

```python
class UserContextService:
    async def get_user_context(user_id: UUID) -> UserContextResponse:
        """ユーザーコンテキストを取得"""
        pass

    def _build_permissions(roles: list[str]) -> PermissionsInfo:
        """権限情報を構築"""
        pass

    async def _build_navigation(user_id: UUID) -> NavigationInfo:
        """ナビゲーション情報を構築"""
        pass

    def _build_sidebar(permissions: PermissionsInfo) -> SidebarInfo:
        """サイドバー表示情報を構築"""
        pass
```

### 4.3 ビジネスロジック

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
    # ユーザーが参画しているアクティブなプロジェクト数を取得
    projects = await project_member_repo.get_user_projects(user_id, status="active")
    project_count = len(projects)

    if project_count == 1:
        # 1つのプロジェクトのみ → 詳細画面に直接遷移
        return NavigationInfo(
            project_count=1,
            default_project_id=projects[0].id,
            default_project_name=projects[0].name,
            project_navigation_type="detail",
        )
    else:
        # 0または複数のプロジェクト → 一覧画面に遷移
        return NavigationInfo(
            project_count=project_count,
            default_project_id=None,
            default_project_name=None,
            project_navigation_type="list",
        )
```

#### サイドバー表示判定ロジック

```python
# セクション定義
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

def _build_sidebar(permissions: PermissionsInfo) -> SidebarInfo:
    visible = []
    hidden = []

    for section, config in SIDEBAR_SECTIONS.items():
        if permissions.is_system_admin or "user" in config["roles"]:
            visible.append(section)
        else:
            hidden.append(section)

    return SidebarInfo(
        visible_sections=visible,
        hidden_sections=hidden,
    )
```

---

## 5. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [共通UI フロントエンド設計書](./02-common-ui-frontend-design.md)

---

## 6. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| UI-001 | 権限に応じたメニューを表示する | `GET /user_account/me/context` | sidebar | 設計済 |
| UI-002 | 参画プロジェクト数に応じて遷移先を切り替える | `GET /user_account/me/context` | sidebar | 設計済 |
| UI-003 | ユーザーコンテキスト情報を取得する | `GET /user_account/me/context` | header | 設計済 |
| UI-004 | 未読通知バッジを表示する | `GET /user_account/me/context` | header | 設計済 |

---

## 7. 関連ドキュメント

- **ユーザー管理**: [../03-user-management/01-user-management-design.md](../03-user-management/01-user-management-design.md)
- **通知**: [../12-notification/01-notification-design.md](../12-notification/01-notification-design.md)
- **モックアップ**: [../../03-mockup/index.html](../../03-mockup/index.html)

---

## 8. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | COMMON-UI-DESIGN-001 |
| 対象ユースケース | UI-001〜UI-004 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/schemas/common/user_context.py` |
|  | `src/app/api/routes/v1/user_accounts/context.py` |
|  | `src/app/services/common/user_context_service.py` |
