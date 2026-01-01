# ユーザー通知 バックエンド設計書（N-001〜N-005）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのユーザー通知機能（ユースケースN-001〜N-005）の実装に必要なバックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **通知取得** | N-001 | 未読通知一覧を取得する |
| | N-002 | 通知詳細を取得する |
| **通知管理** | N-003 | 通知を既読にする |
| | N-004 | すべての通知を既読にする |
| | N-005 | 通知を削除する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 1テーブル（user_notification） |
| APIエンドポイント | 5エンドポイント |
| Pydanticスキーマ | 6スキーマ |
| サービス | 1サービス |
| フロントエンド画面 | 0画面（ヘッダー内コンポーネント） |

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
| GET | `/api/v1/notifications` | 通知一覧取得 | 認証済 | N-001 |
| GET | `/api/v1/notifications/{notification_id}` | 通知詳細取得 | 認証済 | N-002 |
| PATCH | `/api/v1/notifications/{notification_id}/read` | 通知を既読にする | 認証済 | N-003 |
| PATCH | `/api/v1/notifications/read-all` | すべて既読にする | 認証済 | N-004 |
| DELETE | `/api/v1/notifications/{notification_id}` | 通知削除 | 認証済 | N-005 |

### 3.2 リクエスト/レスポンス定義

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

```json
{
  "id": "uuid",
  "type": "member_added",
  "title": "新しいメンバーが追加されました",
  "message": "佐藤 次郎が売上分析プロジェクトに追加されました",
  "icon": "👥",
  "linkUrl": "/projects/uuid/members",
  "referenceType": "project",
  "referenceId": "uuid",
  "isRead": true,
  "readAt": "datetime",
  "createdAt": "datetime"
}
```

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
class NotificationTypeEnum(str, Enum):
    """通知タイプ"""
    member_added = "member_added"          # メンバー追加
    member_removed = "member_removed"      # メンバー削除
    session_complete = "session_complete"  # セッション処理完了
    file_uploaded = "file_uploaded"        # ファイルアップロード
    tree_updated = "tree_updated"          # ツリー更新
    project_invitation = "project_invitation"  # プロジェクト招待
    system_announcement = "system_announcement"  # システムお知らせ

class ReferenceTypeEnum(str, Enum):
    """参照タイプ"""
    project = "project"
    session = "session"
    file = "file"
    tree = "tree"
```

### 4.2 Info/Dataスキーマ

```python
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
class NotificationListResponse(CamelCaseModel):
    """通知一覧レスポンス"""
    notifications: list[NotificationInfo]
    total: int
    unread_count: int
    skip: int
    limit: int

class ReadAllResponse(CamelCaseModel):
    """全既読レスポンス"""
    updated_count: int

class NotificationCreate(CamelCaseModel):
    """通知作成（内部用）"""
    user_id: UUID
    type: NotificationTypeEnum
    title: str
    message: str | None = None
    icon: str | None = None
    link_url: str | None = None
    reference_type: ReferenceTypeEnum | None = None
    reference_id: UUID | None = None
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| NotificationService | 通知CRUD、既読管理、通知生成 |

### 5.2 主要メソッド

#### NotificationService

```python
class NotificationService:
    # 通知取得
    async def list_notifications(
        user_id: UUID,
        is_read: bool | None,
        skip: int,
        limit: int
    ) -> list[UserNotification]
    async def count_notifications(user_id: UUID, is_read: bool | None) -> int
    async def count_unread(user_id: UUID) -> int
    async def get_notification(notification_id: UUID, user_id: UUID) -> UserNotification | None

    # 既読管理
    async def mark_as_read(notification_id: UUID, user_id: UUID) -> UserNotification
    async def mark_all_as_read(user_id: UUID) -> int

    # 通知作成（内部用）
    async def create_notification(data: NotificationCreate) -> UserNotification
    async def create_bulk_notifications(data_list: list[NotificationCreate]) -> list[UserNotification]

    # 通知削除
    async def delete_notification(notification_id: UUID, user_id: UUID) -> None

    # 通知ヘルパー（イベント駆動で呼び出し）
    async def notify_member_added(project_id: UUID, added_user_name: str, target_users: list[UUID]) -> None
    async def notify_session_complete(session_id: UUID, session_name: str, user_id: UUID) -> None
    async def notify_file_uploaded(file_id: UUID, filename: str, project_id: UUID, uploader_name: str) -> None
    async def notify_tree_updated(tree_id: UUID, tree_name: str, project_id: UUID) -> None
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [ユーザー通知 フロントエンド設計書](./02-notification-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| N-001 | 未読通知一覧を取得する | `GET /notifications` | header-notification | 設計済 |
| N-002 | 通知詳細を取得する | `GET /notifications/{id}` | header-notification | 設計済 |
| N-003 | 通知を既読にする | `PATCH /notifications/{id}/read` | header-notification | 設計済 |
| N-004 | すべての通知を既読にする | `PATCH /notifications/read-all` | header-notification | 設計済 |
| N-005 | 通知を削除する | `DELETE /notifications/{id}` | header-notification | 設計済 |

---

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/index.html](../../03-mockup/index.html)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **システム管理（管理者通知）**: [../12-system-admin/01-system-admin-design.md](../12-system-admin/01-system-admin-design.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | NOTIF-DESIGN-001 |
| 対象ユースケース | N-001〜N-005 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/models/notification/user_notification.py` |
|  | `src/app/schemas/notification/notification.py` |
|  | `src/app/api/routes/v1/notifications/notification.py` |
|  | `src/app/services/notification/notification_service.py` |
