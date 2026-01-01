# システム管理機能 統合設計書（SA-001〜SA-043）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのシステム管理者向け機能（ユースケースSA-001〜SA-043）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | ユースケース | 機能概要 |
|---------|-------------|---------|
| ユーザー操作履歴追跡 | SA-001〜SA-006 | 操作ログの記録・検索・エラー追跡 |
| 全プロジェクト閲覧 | SA-007〜SA-011 | 管理者による全プロジェクト管理 |
| 詳細監査ログ | SA-012〜SA-016 | データ変更・アクセス・セキュリティログ |
| システム設定 | SA-017〜SA-020 | アプリ設定・メンテナンス |
| システム統計 | SA-022〜SA-026 | ダッシュボード・統計情報 |
| 一括操作 | SA-027〜SA-030 | ユーザー/プロジェクトの一括処理 |
| 通知・アラート管理 | SA-031〜SA-034 | お知らせ・アラート・テンプレート |
| セキュリティ管理 | SA-035〜SA-036 | セッション管理・強制ログアウト |
| データ管理 | SA-037〜SA-040 | クリーンアップ・保持ポリシー |
| サポートツール | SA-041〜SA-043 | 代行操作・デバッグ・ヘルスチェック |

### 1.3 追加コンポーネント数

| レイヤー | 追加項目数 |
|---------|----------|
| データベーステーブル | 8テーブル |
| APIエンドポイント | 40エンドポイント |
| Pydanticスキーマ | 16ファイル |
| サービス | 8サービス |
| フロントエンド画面 | 10画面 |

### 1.4 機能カテゴリ一覧

| カテゴリ | 対応UC | エンドポイント数 |
|---------|--------|-----------------|
| 操作履歴API | SA-001〜SA-006 | 4エンドポイント |
| 全プロジェクト管理API | SA-007〜SA-011 | 5エンドポイント |
| 監査ログAPI | SA-012〜SA-016 | 6エンドポイント |
| システム設定API | SA-017〜SA-021 | 5エンドポイント |
| 統計API | SA-022〜SA-026 | 5エンドポイント |
| 一括操作API | SA-027〜SA-030 | 4エンドポイント |
| 通知管理API | SA-031〜SA-034 | alerts, templates, announcements |
| セキュリティ管理API | SA-035〜SA-036 | 4エンドポイント |
| データ管理API | SA-037〜SA-040 | 4エンドポイント |
| サポートツールAPI | SA-041〜SA-043 | 6エンドポイント |

---

## 2. データベース設計

データベースの詳細設計は以下のドキュメントを参照してください：

- [データベース設計書 - システム管理](../../../06-database/01-database-design.md#36-システム管理)

### 2.1 関連テーブル一覧

| テーブル名 | 対応ユースケース | 説明 |
|-----------|----------------|------|
| user_activity | SA-001〜SA-006 | ユーザー操作履歴 |
| audit_log | SA-012〜SA-016 | 監査ログ |
| system_setting | SA-017〜SA-020 | システム設定 |
| system_announcement | SA-033〜SA-034 | システムお知らせ |
| notification_template | SA-032 | 通知テンプレート |
| system_alert | SA-031 | システムアラート設定 |
| user_session | SA-035〜SA-036 | ユーザーセッション |

---

## 3. APIエンドポイント設計

### 3.1 操作履歴API（SA-001〜SA-006）

#### GET /api/v1/admin/activity-logs

操作履歴一覧を取得する。

**権限**: SystemAdmin

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| user_id | UUID | NO | ユーザーIDで絞り込み |
| action_type | string | NO | 操作種別で絞り込み |
| resource_type | string | NO | リソース種別で絞り込み |
| start_date | datetime | NO | 開始日時 |
| end_date | datetime | NO | 終了日時 |
| has_error | boolean | NO | エラーのみ取得 |
| page | integer | NO | ページ番号（デフォルト: 1） |
| limit | integer | NO | 取得件数（デフォルト: 50、最大: 100） |

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_name": "山田 太郎",
      "action_type": "CREATE",
      "resource_type": "PROJECT",
      "resource_id": "uuid",
      "endpoint": "/api/v1/projects",
      "method": "POST",
      "response_status": 201,
      "error_message": null,
      "error_code": null,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "duration_ms": 150,
      "created_at": "2025-12-30T10:00:00Z"
    }
  ],
  "total": 1000,
  "page": 1,
  "limit": 50,
  "total_pages": 20
}
```

#### GET /api/v1/admin/activity-logs/{id}

操作履歴の詳細を取得する。

**レスポンス**:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "user_name": "山田 太郎",
  "user_email": "yamada@example.com",
  "action_type": "CREATE",
  "resource_type": "PROJECT",
  "resource_id": "uuid",
  "endpoint": "/api/v1/projects",
  "method": "POST",
  "request_body": {
    "name": "新規プロジェクト",
    "description": "プロジェクトの説明"
  },
  "response_status": 201,
  "error_message": null,
  "error_code": null,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "duration_ms": 150,
  "created_at": "2025-12-30T10:00:00Z"
}
```

#### GET /api/v1/admin/activity-logs/errors

エラー履歴のみを取得する。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_name": "山田 太郎",
      "action_type": "ERROR",
      "resource_type": "PROJECT",
      "resource_id": "uuid",
      "endpoint": "/api/v1/projects/invalid-id",
      "method": "GET",
      "response_status": 404,
      "error_message": "Project not found",
      "error_code": "RESOURCE_NOT_FOUND",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "duration_ms": 25,
      "created_at": "2025-12-30T10:05:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 50,
  "total_pages": 1
}
```

#### GET /api/v1/admin/activity-logs/export

操作履歴をCSV形式でエクスポートする。

**レスポンス**: CSVファイル（Content-Type: text/csv）

---

### 3.2 全プロジェクト管理API（SA-007〜SA-011）

#### GET /api/v1/admin/projects

全プロジェクト一覧を取得する。

**権限**: SystemAdmin

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| status | string | NO | ステータス（active/archived/deleted） |
| owner_id | UUID | NO | オーナーで絞り込み |
| inactive_days | integer | NO | 指定日数以上非アクティブ |
| search | string | NO | プロジェクト名検索 |
| sort_by | string | NO | ソート項目（storage/last_activity/created_at） |
| sort_order | string | NO | ソート順（asc/desc） |
| page | integer | NO | ページ番号 |
| limit | integer | NO | 取得件数 |

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "売上分析プロジェクト",
      "owner": {
        "id": "uuid",
        "name": "山田 太郎"
      },
      "status": "active",
      "member_count": 5,
      "storage_used_bytes": 1073741824,
      "storage_used_display": "1.0 GB",
      "last_activity_at": "2025-12-30T10:00:00Z",
      "created_at": "2025-10-01T00:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "statistics": {
    "total_projects": 150,
    "active_projects": 120,
    "archived_projects": 25,
    "deleted_projects": 5,
    "total_storage_bytes": 107374182400,
    "total_storage_display": "100.0 GB"
  }
}
```

#### GET /api/v1/admin/projects/{id}

プロジェクト詳細を取得する（管理者ビュー）。

#### GET /api/v1/admin/projects/storage

プロジェクト別ストレージ使用量を取得する。

#### GET /api/v1/admin/projects/inactive

非アクティブプロジェクト一覧を取得する。

#### POST /api/v1/admin/projects/bulk-archive

複数プロジェクトを一括アーカイブする。

---

### 3.3 監査ログAPI（SA-012〜SA-016）

#### GET /api/v1/admin/audit-logs

監査ログ一覧を取得する。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| event_type | string | NO | イベント種別（DATA_CHANGE/ACCESS/SECURITY） |
| user_id | UUID | NO | ユーザーID |
| resource_type | string | NO | リソース種別 |
| resource_id | UUID | NO | リソースID |
| severity | string | NO | 重要度 |
| start_date | datetime | NO | 開始日時 |
| end_date | datetime | NO | 終了日時 |
| page | integer | NO | ページ番号 |
| limit | integer | NO | 取得件数 |

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_name": "山田 太郎",
      "user_email": "yamada@example.com",
      "event_type": "DATA_CHANGE",
      "action": "UPDATE",
      "resource_type": "PROJECT",
      "resource_id": "uuid",
      "old_value": {
        "name": "旧プロジェクト名",
        "description": "旧説明"
      },
      "new_value": {
        "name": "新プロジェクト名",
        "description": "新説明"
      },
      "changed_fields": ["name", "description"],
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "severity": "INFO",
      "metadata": null,
      "created_at": "2025-12-30T10:00:00Z"
    }
  ],
  "total": 500,
  "page": 1,
  "limit": 50,
  "total_pages": 10
}
```

#### GET /api/v1/admin/audit-logs/changes

データ変更履歴を取得する（event_type=DATA_CHANGE）。

**レスポンス**: 上記と同じ形式（event_type=DATA_CHANGEでフィルタ済み）

#### GET /api/v1/admin/audit-logs/access

アクセスログを取得する（event_type=ACCESS）。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_name": "山田 太郎",
      "user_email": "yamada@example.com",
      "event_type": "ACCESS",
      "action": "LOGIN_SUCCESS",
      "resource_type": "USER",
      "resource_id": "uuid",
      "old_value": null,
      "new_value": null,
      "changed_fields": null,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "severity": "INFO",
      "metadata": {
        "login_method": "AZURE_AD"
      },
      "created_at": "2025-12-30T08:00:00Z"
    }
  ],
  "total": 200,
  "page": 1,
  "limit": 50,
  "total_pages": 4
}
```

#### GET /api/v1/admin/audit-logs/security

セキュリティイベントを取得する（event_type=SECURITY）。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_name": "山田 太郎",
      "user_email": "yamada@example.com",
      "event_type": "SECURITY",
      "action": "LOGIN_FAILED",
      "resource_type": "USER",
      "resource_id": "uuid",
      "old_value": null,
      "new_value": null,
      "changed_fields": null,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "severity": "WARNING",
      "metadata": {
        "failure_reason": "INVALID_PASSWORD",
        "attempt_count": 3
      },
      "created_at": "2025-12-30T09:30:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 50,
  "total_pages": 1
}
```

#### GET /api/v1/admin/audit-logs/resource/{resource_type}/{resource_id}

特定リソースの変更履歴を追跡する。

**レスポンス**: 上記と同じ形式（指定リソースでフィルタ済み）

#### GET /api/v1/admin/audit-logs/export

監査ログをエクスポートする（CSV/JSON）。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| format | string | NO | 出力形式（csv/json、デフォルト: csv） |
| event_type | string | NO | イベント種別フィルタ |
| start_date | datetime | NO | 開始日時 |
| end_date | datetime | NO | 終了日時 |

**レスポンス**: CSV/JSONファイル（Content-Disposition: attachment）

---

### 3.4 システム設定API（SA-017〜SA-021）

#### GET /api/v1/admin/settings

全システム設定を取得する。

**レスポンス**:

```json
{
  "categories": {
    "GENERAL": [
      {
        "key": "max_file_size_mb",
        "value": 100,
        "value_type": "NUMBER",
        "description": "最大ファイルサイズ（MB）",
        "is_editable": true
      },
      {
        "key": "session_timeout_minutes",
        "value": 60,
        "value_type": "NUMBER",
        "description": "セッションタイムアウト（分）",
        "is_editable": true
      }
    ],
    "SECURITY": [...],
    "MAINTENANCE": [...]
  }
}
```

#### GET /api/v1/admin/settings/{category}

カテゴリ別設定を取得する。

#### PATCH /api/v1/admin/settings/{category}/{key}

設定を更新する。

**リクエスト**:

```json
{
  "value": "new_value"
}
```

#### POST /api/v1/admin/settings/maintenance/enable

メンテナンスモードを有効化する。

**リクエスト**:

```json
{
  "message": "システムメンテナンス中です。しばらくお待ちください。",
  "allow_admin_access": true
}
```

#### POST /api/v1/admin/settings/maintenance/disable

メンテナンスモードを無効化する。

---

### 3.5 システム統計API（SA-022〜SA-026）

#### GET /api/v1/admin/statistics/overview

システム統計概要を取得する。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| period | string | NO | 期間（day/week/month/year） |
| start_date | date | NO | 開始日 |
| end_date | date | NO | 終了日 |

**レスポンス**:

```json
{
  "users": {
    "total": 500,
    "active_today": 120,
    "new_this_month": 15
  },
  "projects": {
    "total": 150,
    "active": 120,
    "created_this_month": 8
  },
  "storage": {
    "total_bytes": 107374182400,
    "total_display": "100.0 GB",
    "used_percentage": 45.5
  },
  "api": {
    "requests_today": 15000,
    "average_response_ms": 150,
    "error_rate_percentage": 0.5
  }
}
```

#### GET /api/v1/admin/statistics/users

ユーザー統計（アクティブユーザー推移）を取得する。

#### GET /api/v1/admin/statistics/storage

ストレージ使用量推移を取得する。

#### GET /api/v1/admin/statistics/api-requests

APIリクエスト統計を取得する。

#### GET /api/v1/admin/statistics/errors

エラー発生率統計を取得する。

---

### 3.6 一括操作API（SA-027〜SA-030）

#### POST /api/v1/admin/bulk/users/import

ユーザーを一括インポートする。

**リクエスト**: multipart/form-data

| フィールド | 型 | 必須 | 説明 |
|-----------|---|------|------|
| file | file | YES | CSVファイル |
| dry_run | boolean | NO | プレビューのみ（デフォルト: false） |

**レスポンス**:

```json
{
  "success": true,
  "imported_count": 50,
  "skipped_count": 2,
  "errors": [
    {"row": 15, "error": "Invalid email format"}
  ]
}
```

#### GET /api/v1/admin/bulk/users/export

ユーザー情報を一括エクスポートする。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| status | string | NO | ステータスフィルタ |
| role | string | NO | ロールフィルタ |
| format | string | NO | 出力形式（csv/xlsx） |

#### POST /api/v1/admin/bulk/users/deactivate

非アクティブユーザーを一括無効化する。

**リクエスト**:

```json
{
  "inactive_days": 90,
  "dry_run": false
}
```

#### POST /api/v1/admin/bulk/projects/archive

古いプロジェクトを一括アーカイブする。

**リクエスト**:

```json
{
  "inactive_days": 180,
  "dry_run": false
}
```

---

### 3.7 通知管理API（SA-031〜SA-034）

#### GET /api/v1/admin/alerts

システムアラート一覧を取得する。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "エラー率アラート",
      "condition_type": "ERROR_RATE",
      "threshold": {"value": 5},
      "comparison_operator": "GT",
      "notification_channels": ["EMAIL"],
      "is_enabled": true,
      "last_triggered_at": "2025-12-29T15:00:00Z",
      "trigger_count": 3,
      "created_by": "uuid",
      "created_at": "2025-12-01T00:00:00Z",
      "updated_at": "2025-12-29T15:00:00Z"
    },
    {
      "id": "uuid",
      "name": "ストレージ使用量アラート",
      "condition_type": "STORAGE_USAGE",
      "threshold": {"value": 80, "unit": "percent"},
      "comparison_operator": "GTE",
      "notification_channels": ["EMAIL", "SLACK"],
      "is_enabled": true,
      "last_triggered_at": null,
      "trigger_count": 0,
      "created_by": "uuid",
      "created_at": "2025-12-15T00:00:00Z",
      "updated_at": "2025-12-15T00:00:00Z"
    }
  ],
  "total": 2
}
```

#### POST /api/v1/admin/alerts

システムアラートを作成する。

**リクエスト**:

```json
{
  "name": "エラー率アラート",
  "condition_type": "ERROR_RATE",
  "threshold": {"value": 5},
  "comparison_operator": "GT",
  "notification_channels": ["EMAIL"],
  "is_enabled": true
}
```

#### PATCH /api/v1/admin/alerts/{id}

システムアラートを更新する。

#### DELETE /api/v1/admin/alerts/{id}

システムアラートを削除する。

#### GET /api/v1/admin/notification-templates

通知テンプレート一覧を取得する。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "プロジェクト作成通知",
      "event_type": "PROJECT_CREATED",
      "subject": "【CAMP】新しいプロジェクト「{{project_name}}」が作成されました",
      "body": "{{user_name}}さんが新しいプロジェクト「{{project_name}}」を作成しました。\n\n詳細はこちら: {{project_url}}",
      "variables": ["project_name", "user_name", "project_url", "created_at"],
      "is_active": true,
      "created_at": "2025-10-01T00:00:00Z",
      "updated_at": "2025-12-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "メンバー追加通知",
      "event_type": "MEMBER_ADDED",
      "subject": "【CAMP】プロジェクト「{{project_name}}」に追加されました",
      "body": "{{inviter_name}}さんがあなたをプロジェクト「{{project_name}}」に追加しました。\n\nロール: {{role}}\n\n詳細はこちら: {{project_url}}",
      "variables": ["project_name", "inviter_name", "role", "project_url"],
      "is_active": true,
      "created_at": "2025-10-01T00:00:00Z",
      "updated_at": "2025-10-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

#### POST /api/v1/admin/notification-templates

通知テンプレートを作成する。

**リクエスト**:

```json
{
  "name": "セッション完了通知",
  "event_type": "SESSION_COMPLETED",
  "subject": "【CAMP】分析セッション「{{session_name}}」が完了しました",
  "body": "分析セッション「{{session_name}}」の処理が完了しました。\n\n結果を確認してください: {{session_url}}",
  "variables": ["session_name", "session_url", "completed_at"],
  "is_active": true
}
```

#### PATCH /api/v1/admin/notification-templates/{id}

通知テンプレートを更新する。

#### GET /api/v1/admin/announcements

システムお知らせ一覧を取得する。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "システムメンテナンスのお知らせ",
      "content": "12月31日 23:00〜翌1:00にシステムメンテナンスを実施します。この間、システムをご利用いただけません。",
      "announcement_type": "MAINTENANCE",
      "priority": 1,
      "start_at": "2025-12-28T00:00:00Z",
      "end_at": "2025-12-31T23:59:59Z",
      "is_active": true,
      "target_roles": [],
      "created_by": "uuid",
      "created_by_name": "管理者 太郎",
      "created_at": "2025-12-25T00:00:00Z",
      "updated_at": "2025-12-25T00:00:00Z"
    },
    {
      "id": "uuid",
      "title": "新機能リリースのお知らせ",
      "content": "ドライバーツリーの新機能「施策シミュレーション」をリリースしました。",
      "announcement_type": "INFO",
      "priority": 3,
      "start_at": "2025-12-20T00:00:00Z",
      "end_at": null,
      "is_active": true,
      "target_roles": [],
      "created_by": "uuid",
      "created_by_name": "管理者 太郎",
      "created_at": "2025-12-20T00:00:00Z",
      "updated_at": "2025-12-20T00:00:00Z"
    }
  ],
  "total": 2
}
```

#### POST /api/v1/admin/announcements

システムお知らせを作成する。

**リクエスト**:

```json
{
  "title": "システムメンテナンスのお知らせ",
  "content": "12月31日 23:00〜翌1:00にシステムメンテナンスを実施します。",
  "announcement_type": "MAINTENANCE",
  "priority": 1,
  "start_at": "2025-12-30T00:00:00Z",
  "end_at": "2025-12-31T23:59:59Z",
  "target_roles": []
}
```

#### PATCH /api/v1/admin/announcements/{id}

システムお知らせを更新する。

#### DELETE /api/v1/admin/announcements/{id}

システムお知らせを削除する。

---

### 3.8 セキュリティ管理API（SA-035〜SA-036）

#### GET /api/v1/admin/sessions

アクティブセッション一覧を取得する。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| user_id | UUID | NO | ユーザーID |
| ip_address | string | NO | IPアドレス |
| page | integer | NO | ページ番号 |
| limit | integer | NO | 取得件数 |

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "name": "山田 太郎",
        "email": "yamada@example.com"
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "device_info": {
        "os": "Windows 11",
        "browser": "Chrome 120"
      },
      "login_at": "2025-12-30T08:00:00Z",
      "last_activity_at": "2025-12-30T10:30:00Z",
      "expires_at": "2025-12-30T18:00:00Z",
      "is_active": true
    }
  ],
  "total": 120,
  "statistics": {
    "active_sessions": 120,
    "logins_today": 85
  }
}
```

#### GET /api/v1/admin/sessions/user/{user_id}

特定ユーザーのセッション一覧を取得する。

#### POST /api/v1/admin/sessions/{id}/terminate

特定セッションを終了（強制ログアウト）する。

**リクエスト**:

```json
{
  "reason": "FORCED"
}
```

#### POST /api/v1/admin/sessions/user/{user_id}/terminate-all

特定ユーザーの全セッションを終了する。

---

### 3.9 データ管理API（SA-037〜SA-040）

#### GET /api/v1/admin/data/cleanup/preview

削除対象データのプレビューを取得する。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| target_types | string[] | YES | 対象種別（activity_logs/audit_logs/deleted_projects等） |
| retention_days | integer | YES | 保持日数 |

**レスポンス**:

```json
{
  "preview": [
    {
      "target_type": "activity_logs",
      "target_type_display": "操作履歴",
      "record_count": 15000,
      "oldest_record_at": "2025-06-01T00:00:00Z",
      "newest_record_at": "2025-09-30T23:59:59Z",
      "estimated_size_bytes": 52428800,
      "estimated_size_display": "50.0 MB"
    },
    {
      "target_type": "deleted_projects",
      "target_type_display": "削除済みプロジェクト",
      "record_count": 5,
      "oldest_record_at": "2025-08-15T00:00:00Z",
      "newest_record_at": "2025-11-01T00:00:00Z",
      "estimated_size_bytes": 104857600,
      "estimated_size_display": "100.0 MB"
    }
  ],
  "total_record_count": 15005,
  "total_estimated_size_bytes": 157286400,
  "total_estimated_size_display": "150.0 MB",
  "retention_days": 90,
  "cutoff_date": "2025-10-01T00:00:00Z"
}
```

#### POST /api/v1/admin/data/cleanup/execute

古いデータを一括削除する。

**リクエスト**:

```json
{
  "target_types": ["activity_logs", "deleted_projects"],
  "retention_days": 90,
  "dry_run": false
}
```

**レスポンス**:

```json
{
  "success": true,
  "results": [
    {
      "target_type": "activity_logs",
      "deleted_count": 15000,
      "freed_bytes": 52428800
    },
    {
      "target_type": "deleted_projects",
      "deleted_count": 5,
      "freed_bytes": 104857600
    }
  ],
  "total_deleted_count": 15005,
  "total_freed_bytes": 157286400,
  "total_freed_display": "150.0 MB",
  "executed_at": "2025-12-30T10:00:00Z"
}
```

#### GET /api/v1/admin/data/orphan-files

孤立ファイル一覧を取得する。

**レスポンス**:

```json
{
  "items": [
    {
      "id": "uuid",
      "file_name": "old_data_2024.csv",
      "file_path": "/storage/orphan/old_data_2024.csv",
      "size_bytes": 5242880,
      "size_display": "5.0 MB",
      "mime_type": "text/csv",
      "created_at": "2025-06-15T00:00:00Z",
      "last_accessed_at": "2025-08-01T00:00:00Z",
      "original_project_id": "uuid",
      "original_project_name": "削除済みプロジェクト"
    },
    {
      "id": "uuid",
      "file_name": "temp_upload_abc123.xlsx",
      "file_path": "/storage/orphan/temp_upload_abc123.xlsx",
      "size_bytes": 1048576,
      "size_display": "1.0 MB",
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "created_at": "2025-11-20T00:00:00Z",
      "last_accessed_at": null,
      "original_project_id": null,
      "original_project_name": null
    }
  ],
  "total": 2,
  "total_size_bytes": 6291456,
  "total_size_display": "6.0 MB"
}
```

#### POST /api/v1/admin/data/orphan-files/cleanup

孤立ファイルを削除する。

**リクエスト**:

```json
{
  "file_ids": ["uuid1", "uuid2"],
  "delete_all": false
}
```

**レスポンス**:

```json
{
  "success": true,
  "deleted_count": 2,
  "freed_bytes": 6291456,
  "freed_display": "6.0 MB"
}
```

#### GET /api/v1/admin/data/retention-policy

データ保持ポリシーを取得する。

**レスポンス**:

```json
{
  "activity_logs_days": 90,
  "audit_logs_days": 365,
  "deleted_projects_days": 30,
  "session_logs_days": 30
}
```

#### PATCH /api/v1/admin/data/retention-policy

データ保持ポリシーを更新する。

#### POST /api/v1/admin/data/master/import

マスタデータを一括インポートする。

---

### 3.10 サポートツールAPI（SA-041〜SA-043）

#### POST /api/v1/admin/impersonate/{user_id}

ユーザー代行操作を開始する。

**リクエスト**:

```json
{
  "reason": "ユーザーサポート対応"
}
```

**レスポンス**:

```json
{
  "impersonation_token": "xxx",
  "target_user": {
    "id": "uuid",
    "name": "山田 太郎"
  },
  "expires_at": "2025-12-30T11:00:00Z"
}
```

#### POST /api/v1/admin/impersonate/end

ユーザー代行操作を終了する。

#### POST /api/v1/admin/debug/enable

デバッグモードを有効化する。

#### POST /api/v1/admin/debug/disable

デバッグモードを無効化する。

#### GET /api/v1/admin/health-check

簡易ヘルスチェックを実行する。

#### GET /api/v1/admin/health-check/detailed

詳細ヘルスチェックを実行する。

**レスポンス**:

```json
{
  "status": "healthy",
  "timestamp": "2025-12-30T10:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "details": {"connection_pool": "10/20"}
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "storage": {
      "status": "healthy",
      "response_time_ms": 50,
      "details": {"available_space_gb": 500}
    },
    "external_apis": {
      "azure_ad": {
        "status": "healthy",
        "response_time_ms": 100
      }
    }
  }
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class ActionTypeEnum(str, Enum):
    """操作種別"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ERROR = "ERROR"
    OTHER = "OTHER"

class ResourceTypeEnum(str, Enum):
    """リソース種別"""
    PROJECT = "PROJECT"
    ANALYSIS_SESSION = "ANALYSIS_SESSION"
    DRIVER_TREE = "DRIVER_TREE"
    USER = "USER"
    SYSTEM_SETTING = "SYSTEM_SETTING"
    NOTIFICATION = "NOTIFICATION"

class EventTypeEnum(str, Enum):
    """監査ログイベント種別"""
    DATA_CHANGE = "DATA_CHANGE"
    ACCESS = "ACCESS"
    SECURITY = "SECURITY"

class SeverityEnum(str, Enum):
    """重要度"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SystemSettingCategoryEnum(str, Enum):
    """システム設定カテゴリ"""
    GENERAL = "GENERAL"
    SECURITY = "SECURITY"
    MAINTENANCE = "MAINTENANCE"

class ProjectStatusEnum(str, Enum):
    """プロジェクトステータス"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
```

### 4.2 Info/Dataスキーマ

```python
class ActivityLogInfo(CamelCaseModel):
    """操作履歴情報"""
    id: UUID
    user_id: UUID | None = None
    user_name: str | None = None
    action_type: str
    resource_type: str
    resource_id: UUID | None = None
    endpoint: str
    method: str
    response_status: int
    error_message: str | None = None
    error_code: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    duration_ms: int
    created_at: datetime

class ActivityLogDetailInfo(ActivityLogInfo):
    """操作履歴詳細情報"""
    user_email: str | None = None
    request_body: dict | None = None

class AuditLogInfo(CamelCaseModel):
    """監査ログ情報"""
    id: UUID
    user_id: UUID | None = None
    user_name: str
    user_email: str
    event_type: str
    action: str
    resource_type: str
    resource_id: UUID | None = None
    old_value: dict | None = None
    new_value: dict | None = None
    changed_fields: list[str] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    severity: str
    metadata: dict | None = None
    created_at: datetime

class SystemSettingInfo(CamelCaseModel):
    """システム設定情報"""
    id: UUID
    category: str
    key: str
    value: str
    description: str | None = None
    is_public: bool = False
    updated_by: UUID | None = None
    updated_at: datetime

class ProjectAdminInfo(CamelCaseModel):
    """管理者用プロジェクト情報"""
    id: UUID
    name: str
    owner: dict  # {"id": UUID, "name": str}
    status: str
    member_count: int
    storage_used_bytes: int
    storage_used_display: str
    last_activity_at: datetime | None = None
    created_at: datetime

class ProjectStatisticsInfo(CamelCaseModel):
    """プロジェクト統計情報"""
    total_projects: int
    active_projects: int
    archived_projects: int
    deleted_projects: int
    total_storage_bytes: int
    total_storage_display: str

class SystemStatisticsInfo(CamelCaseModel):
    """システム統計情報"""
    users: dict  # {"total": int, "active_today": int}
    projects: dict  # {"total": int}
    storage: dict  # {"total_display": str}
    api: dict  # {"requests_today": int, "error_rate_percentage": float}

class UserSessionInfo(CamelCaseModel):
    """ユーザーセッション情報"""
    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    ip_address: str | None = None
    user_agent: str | None = None
    last_activity_at: datetime
    created_at: datetime

class SystemAnnouncementInfo(CamelCaseModel):
    """システムお知らせ情報"""
    id: UUID
    title: str
    content: str
    severity: str
    start_date: datetime
    end_date: datetime | None = None
    is_active: bool
    created_by: UUID
    created_at: datetime
```

### 4.3 Request/Responseスキーマ

```python
# 操作履歴
class ActivityLogListResponse(CamelCaseModel):
    items: list[ActivityLogInfo]
    total: int
    page: int
    limit: int
    total_pages: int

class ActivityLogDetailResponse(CamelCaseModel):
    """操作履歴詳細レスポンス"""
    __root__: ActivityLogDetailInfo

# 監査ログ
class AuditLogListResponse(CamelCaseModel):
    items: list[AuditLogInfo]
    total: int
    page: int
    limit: int
    total_pages: int

# 全プロジェクト管理
class ProjectAdminListResponse(CamelCaseModel):
    items: list[ProjectAdminInfo]
    total: int
    page: int
    limit: int
    statistics: ProjectStatisticsInfo

class BulkArchiveRequest(CamelCaseModel):
    project_ids: list[UUID] = Field(..., min_length=1)

# システム設定
class SystemSettingUpdate(CamelCaseModel):
    value: str = Field(..., min_length=1)

class SystemSettingListResponse(CamelCaseModel):
    settings: list[SystemSettingInfo]
    total: int

# システム統計
class SystemStatisticsResponse(CamelCaseModel):
    statistics: SystemStatisticsInfo

# ユーザーセッション
class UserSessionListResponse(CamelCaseModel):
    sessions: list[UserSessionInfo]
    total: int

class ForceLogoutRequest(CamelCaseModel):
    user_id: UUID
    reason: str | None = None

# システムお知らせ
class SystemAnnouncementCreate(CamelCaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    severity: str
    start_date: datetime
    end_date: datetime | None = None

class SystemAnnouncementUpdate(CamelCaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = None
    severity: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None

class SystemAnnouncementListResponse(CamelCaseModel):
    announcements: list[SystemAnnouncementInfo]
    total: int
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| ActivityTrackingService | 操作履歴の記録・検索・エクスポート |
| AuditLogService | 監査ログ管理、データ変更・アクセス・セキュリティログ |
| SystemSettingService | システム設定の取得・更新・カテゴリ管理 |
| StatisticsService | システム統計情報の集計・分析 |
| NotificationService | 通知・お知らせ・アラート・テンプレート管理 |
| SessionManagementService | ユーザーセッション管理・強制ログアウト |
| BulkOperationService | ユーザー・プロジェクトの一括操作実行 |
| SupportToolsService | 代行操作・デバッグ・ヘルスチェック |

### 5.2 主要メソッド

#### ActivityTrackingService

```python
class ActivityTrackingService:
    # 操作履歴検索
    async def list_activity_logs(
        user_id: UUID | None,
        action_type: str | None,
        resource_type: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        has_error: bool | None,
        page: int,
        limit: int
    ) -> tuple[list[UserActivity], int]

    async def get_activity_log_detail(activity_id: UUID) -> UserActivity | None

    async def get_error_logs(
        page: int,
        limit: int
    ) -> tuple[list[UserActivity], int]

    # 操作履歴記録
    async def record_activity(
        user_id: UUID | None,
        action_type: str,
        resource_type: str,
        resource_id: UUID | None,
        endpoint: str,
        method: str,
        request_body: dict | None,
        response_status: int,
        error_message: str | None,
        error_code: str | None,
        ip_address: str | None,
        user_agent: str | None,
        duration_ms: int
    ) -> UserActivity

    # エクスポート
    async def export_activity_logs_csv(
        filters: dict
    ) -> bytes
```

#### AuditLogService

```python
class AuditLogService:
    # 監査ログ検索
    async def list_audit_logs(
        event_type: str | None,
        user_id: UUID | None,
        resource_type: str | None,
        resource_id: UUID | None,
        severity: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        page: int,
        limit: int
    ) -> tuple[list[AuditLog], int]

    async def get_data_change_logs(
        page: int,
        limit: int
    ) -> tuple[list[AuditLog], int]

    async def get_access_logs(
        page: int,
        limit: int
    ) -> tuple[list[AuditLog], int]

    async def get_security_logs(
        page: int,
        limit: int
    ) -> tuple[list[AuditLog], int]

    # 監査ログ記録
    async def log_data_change(
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        old_value: dict,
        new_value: dict,
        changed_fields: list[str],
        ip_address: str | None,
        user_agent: str | None
    ) -> AuditLog

    async def log_access(
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        metadata: dict | None,
        ip_address: str | None,
        user_agent: str | None
    ) -> AuditLog

    async def log_security_event(
        user_id: UUID | None,
        action: str,
        severity: str,
        metadata: dict | None,
        ip_address: str | None,
        user_agent: str | None
    ) -> AuditLog

    # エクスポート
    async def export_audit_logs_csv(filters: dict) -> bytes
```

#### SystemSettingService

```python
class SystemSettingService:
    # 設定取得
    async def get_settings_by_category(category: str) -> list[SystemSetting]

    async def get_setting(category: str, key: str) -> SystemSetting | None

    async def get_setting_value(category: str, key: str) -> str | None

    async def get_all_settings() -> list[SystemSetting]

    async def get_public_settings() -> list[SystemSetting]

    # 設定更新
    async def update_setting(
        category: str,
        key: str,
        value: str,
        updated_by: UUID
    ) -> SystemSetting

    async def bulk_update_settings(
        settings: list[dict],
        updated_by: UUID
    ) -> list[SystemSetting]

    # メンテナンスモード
    async def enable_maintenance_mode(
        message: str,
        allow_admin_access: bool,
        updated_by: UUID
    ) -> SystemSetting

    async def disable_maintenance_mode(updated_by: UUID) -> SystemSetting

    async def is_maintenance_mode() -> bool
```

#### StatisticsService

```python
class StatisticsService:
    # システム統計
    async def get_system_statistics() -> dict

    async def get_user_statistics() -> dict

    async def get_project_statistics() -> dict

    async def get_storage_statistics() -> dict

    async def get_api_statistics() -> dict

    # 期間別統計
    async def get_daily_statistics(date: datetime) -> dict

    async def get_weekly_statistics(start_date: datetime) -> dict

    async def get_monthly_statistics(year: int, month: int) -> dict

    # グラフデータ
    async def get_user_activity_trend(
        start_date: datetime,
        end_date: datetime
    ) -> list[dict]

    async def get_api_request_trend(
        start_date: datetime,
        end_date: datetime
    ) -> list[dict]

    async def get_storage_usage_trend(
        start_date: datetime,
        end_date: datetime
    ) -> list[dict]
```

#### NotificationService

```python
class NotificationService:
    # お知らせ管理
    async def list_announcements(
        is_active: bool | None,
        page: int,
        limit: int
    ) -> tuple[list[SystemAnnouncement], int]

    async def get_active_announcements() -> list[SystemAnnouncement]

    async def create_announcement(
        title: str,
        content: str,
        severity: str,
        start_date: datetime,
        end_date: datetime | None,
        created_by: UUID
    ) -> SystemAnnouncement

    async def update_announcement(
        announcement_id: UUID,
        update_data: dict
    ) -> SystemAnnouncement

    async def delete_announcement(announcement_id: UUID) -> None

    # 通知テンプレート管理
    async def list_notification_templates() -> list[NotificationTemplate]

    async def get_notification_template(template_id: UUID) -> NotificationTemplate | None

    async def update_notification_template(
        template_id: UUID,
        update_data: dict
    ) -> NotificationTemplate

    # アラート管理
    async def list_system_alerts() -> list[SystemAlert]

    async def create_system_alert(alert_data: dict) -> SystemAlert

    async def update_system_alert(
        alert_id: UUID,
        update_data: dict
    ) -> SystemAlert

    async def delete_system_alert(alert_id: UUID) -> None
```

#### SessionManagementService

```python
class SessionManagementService:
    # セッション一覧
    async def list_active_sessions(
        user_id: UUID | None,
        page: int,
        limit: int
    ) -> tuple[list[UserSession], int]

    async def get_user_sessions(user_id: UUID) -> list[UserSession]

    async def get_session_detail(session_id: UUID) -> UserSession | None

    # セッション管理
    async def force_logout_user(
        user_id: UUID,
        reason: str | None,
        admin_user_id: UUID
    ) -> int  # 終了したセッション数

    async def force_logout_session(
        session_id: UUID,
        reason: str | None,
        admin_user_id: UUID
    ) -> None

    async def terminate_all_sessions_except(
        user_id: UUID,
        current_session_id: UUID
    ) -> int

    # セッション統計
    async def get_active_session_count() -> int

    async def get_login_statistics_today() -> dict
```

#### BulkOperationService

```python
class BulkOperationService:
    # プロジェクト一括操作
    async def bulk_archive_projects(
        project_ids: list[UUID],
        admin_user_id: UUID
    ) -> dict  # {"success_count": int, "failed_ids": list[UUID]}

    async def bulk_delete_projects(
        project_ids: list[UUID],
        admin_user_id: UUID
    ) -> dict

    # ユーザー一括操作
    async def bulk_activate_users(
        user_ids: list[UUID],
        admin_user_id: UUID
    ) -> dict

    async def bulk_deactivate_users(
        user_ids: list[UUID],
        admin_user_id: UUID
    ) -> dict

    async def bulk_update_user_roles(
        user_ids: list[UUID],
        roles: list[str],
        admin_user_id: UUID
    ) -> dict

    # データクリーンアップ
    async def cleanup_old_data(
        data_type: str,
        retention_days: int,
        dry_run: bool = True
    ) -> dict  # {"count": int, "items": list[dict]}

    async def cleanup_orphaned_files(
        dry_run: bool = True
    ) -> dict
```

#### SupportToolsService

```python
class SupportToolsService:
    # ユーザー代行
    async def start_impersonation(
        admin_user_id: UUID,
        target_user_id: UUID,
        reason: str
    ) -> dict  # {"token": str, "expires_at": datetime}

    async def end_impersonation(
        admin_user_id: UUID
    ) -> None

    async def get_current_impersonation(
        admin_user_id: UUID
    ) -> dict | None

    # デバッグモード
    async def enable_debug_mode(
        admin_user_id: UUID,
        log_level: str,
        duration_minutes: int | None
    ) -> dict

    async def disable_debug_mode(admin_user_id: UUID) -> None

    async def get_debug_mode_status() -> dict

    # ヘルスチェック
    async def run_health_check() -> dict

    async def check_database_health() -> dict

    async def check_cache_health() -> dict

    async def check_storage_health() -> dict

    async def check_external_api_health() -> dict
```

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | 対応ユースケース |
|--------|-------|----------------|
| admin-activity-logs | 操作履歴 | SA-001〜SA-006 |
| admin-projects | 全プロジェクト管理 | SA-007〜SA-011 |
| admin-audit-logs | 監査ログ | SA-012〜SA-016 |
| admin-settings | システム設定 | SA-017〜SA-021 |
| admin-statistics | システム統計 | SA-022〜SA-026 |
| admin-bulk-operations | 一括操作 | SA-027〜SA-030 |
| admin-notifications | 通知管理 | SA-031〜SA-034 |
| admin-security | セキュリティ管理 | SA-035〜SA-036 |
| admin-data-management | データ管理 | SA-037〜SA-040 |
| admin-support-tools | サポートツール | SA-041〜SA-043 |

### 6.2 コンポーネント構成

```text
pages/admin/
├── activity-logs/
│   └── index.tsx                    # 操作履歴画面
├── projects/
│   ├── index.tsx                    # 全プロジェクト管理画面
│   └── [id].tsx                     # プロジェクト詳細（管理者ビュー）
├── audit-logs/
│   └── index.tsx                    # 監査ログ画面
├── settings/
│   └── index.tsx                    # システム設定画面
├── statistics/
│   └── index.tsx                    # システム統計ダッシュボード
├── bulk-operations/
│   └── index.tsx                    # 一括操作画面
├── notifications/
│   └── index.tsx                    # 通知管理画面
├── security/
│   └── index.tsx                    # セキュリティ管理画面
├── data-management/
│   └── index.tsx                    # データ管理画面
└── support-tools/
    └── index.tsx                    # サポートツール画面
```

---

## 7. 画面項目・APIマッピング

### 7.1 admin-activity-logs（操作履歴）

#### 詳細モーダル

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| リクエストボディ | JSON | GET /api/v1/admin/activity-logs/{id} | request_body | JSON整形 |
| エラーメッセージ | テキスト | GET /api/v1/admin/activity-logs/{id} | error_message | - |
| エラーコード | テキスト | GET /api/v1/admin/activity-logs/{id} | error_code | - |
| IPアドレス | テキスト | GET /api/v1/admin/activity-logs/{id} | ip_address | - |
| ユーザーエージェント | テキスト | GET /api/v1/admin/activity-logs/{id} | user_agent | - |

---

### 7.2 admin-projects（全プロジェクト管理）

#### 統計カード

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| 総プロジェクト数 | 数値 | GET /api/v1/admin/projects | statistics.total_projects | - |
| アクティブ数 | 数値 | GET /api/v1/admin/projects | statistics.active_projects | - |
| 総ストレージ使用量 | テキスト | GET /api/v1/admin/projects | statistics.total_storage_display | - |
| 非アクティブ数 | 数値 | GET /api/v1/admin/projects/inactive | total | - |

#### フィルターセクション

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|-----------------|----------------|------|
| ステータス | select | GET /api/v1/admin/projects | status | active/archived/deleted |
| オーナー | select | GET /api/v1/admin/projects | owner_id | UUID |
| 非アクティブ日数 | number | GET /api/v1/admin/projects | inactive_days | 整数 |
| ソート | select | GET /api/v1/admin/projects | sort_by | storage/last_activity/created_at |
| プロジェクト名検索 | text | GET /api/v1/admin/projects | search | 部分一致 |

#### 一覧表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| プロジェクト名 | リンク | GET /api/v1/admin/projects | items[].name | 詳細画面へ遷移 |
| オーナー | テキスト+アバター | GET /api/v1/admin/projects | items[].owner.name | - |
| ステータス | バッジ | GET /api/v1/admin/projects | items[].status | バッジ色分け |
| メンバー数 | 数値 | GET /api/v1/admin/projects | items[].member_count | - |
| ストレージ使用量 | プログレスバー | GET /api/v1/admin/projects | items[].storage_used_display | - |
| 最終アクティビティ | テキスト | GET /api/v1/admin/projects | items[].last_activity_at | 相対時間 |

#### 一括操作

| 画面項目 | 操作 | APIエンドポイント | リクエストボディ | 備考 |
|---------|-----|-----------------|----------------|------|
| 一括アーカイブ | button | POST /api/v1/admin/projects/bulk-archive | project_ids[] | 選択項目のID配列 |

---

### 7.3 admin-audit-logs（監査ログ）

#### フィルターセクション

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|-----------------|----------------|------|
| タブ選択 | tab | GET /api/v1/admin/audit-logs/* | - | changes/access/security |
| ユーザー | select | GET /api/v1/admin/audit-logs | user_id | UUID |
| 重要度 | select | GET /api/v1/admin/audit-logs | severity | INFO/WARNING/CRITICAL |
| リソース種別 | select | GET /api/v1/admin/audit-logs | resource_type | PROJECT/USER等 |
| 日時範囲 | datetime-range | GET /api/v1/admin/audit-logs | start_date, end_date | ISO 8601 |

#### 一覧表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| 日時 | テキスト | GET /api/v1/admin/audit-logs | items[].created_at | 日時フォーマット |
| ユーザー | テキスト+アバター | GET /api/v1/admin/audit-logs | items[].user_name | - |
| イベント種別 | バッジ | GET /api/v1/admin/audit-logs | items[].event_type | バッジ色分け |
| アクション | バッジ | GET /api/v1/admin/audit-logs | items[].action | - |
| 重要度 | バッジ | GET /api/v1/admin/audit-logs | items[].severity | INFO青/WARNING黄/CRITICAL赤 |

#### 詳細パネル

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| 変更前の値 | JSON | GET /api/v1/admin/audit-logs | items[].old_value | JSON diff表示 |
| 変更後の値 | JSON | GET /api/v1/admin/audit-logs | items[].new_value | JSON diff表示 |
| 変更フィールド | chips | GET /api/v1/admin/audit-logs | items[].changed_fields | 配列表示 |

---

### 7.4 admin-settings（システム設定）

#### 設定一覧取得

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| カテゴリタブ | tab | GET /api/v1/admin/settings | categories.* | GENERAL/SECURITY/MAINTENANCE |
| 設定キー | ラベル | GET /api/v1/admin/settings/{category} | [].key | - |
| 設定値 | 入力フィールド | GET /api/v1/admin/settings/{category} | [].value | value_typeに応じた表示 |
| 説明 | テキスト | GET /api/v1/admin/settings/{category} | [].description | - |

#### 設定更新

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|-----------------|-------------------|---------------|
| 設定値 | 動的 | YES | PATCH /api/v1/admin/settings/{category}/{key} | value | value_typeに応じた検証 |

#### メンテナンスモード

| 画面項目 | 入力形式 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----------------|-------------------|------|
| メンテナンスメッセージ | textarea | POST /api/v1/admin/settings/maintenance/enable | message | - |
| 管理者アクセス許可 | toggle | POST /api/v1/admin/settings/maintenance/enable | allow_admin_access | boolean |

---

### 7.5 admin-statistics（システム統計）

#### 統計カード

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| 総ユーザー数 | 数値 | GET /api/v1/admin/statistics/overview | users.total | - |
| アクティブユーザー(今日) | 数値 | GET /api/v1/admin/statistics/overview | users.active_today | - |
| 総プロジェクト数 | 数値 | GET /api/v1/admin/statistics/overview | projects.total | - |
| 総ストレージ使用量 | テキスト | GET /api/v1/admin/statistics/overview | storage.total_display | - |
| APIリクエスト(今日) | 数値 | GET /api/v1/admin/statistics/overview | api.requests_today | カンマ区切り |
| エラー率 | パーセント | GET /api/v1/admin/statistics/overview | api.error_rate_percentage | %表示 |

#### グラフ

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| ユーザー推移 | 折れ線グラフ | GET /api/v1/admin/statistics/users | data[] | Chart.js形式 |
| ストレージ推移 | 面グラフ | GET /api/v1/admin/statistics/storage | data[] | Chart.js形式 |
| APIリクエスト推移 | 棒グラフ | GET /api/v1/admin/statistics/api-requests | data[] | Chart.js形式 |
| エラー発生率推移 | 折れ線グラフ | GET /api/v1/admin/statistics/errors | data[] | Chart.js形式 |

---

### 7.6 admin-bulk-operations（一括操作）

#### ユーザーインポート

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|-----------------|-------------------|---------------|
| CSVファイル | file | YES | POST /api/v1/admin/bulk/users/import | file | CSV形式 |
| プレビューのみ | checkbox | NO | POST /api/v1/admin/bulk/users/import | dry_run | boolean |

#### ユーザーエクスポート

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|-----------------|----------------|------|
| ステータスフィルタ | select | GET /api/v1/admin/bulk/users/export | status | - |
| ロールフィルタ | select | GET /api/v1/admin/bulk/users/export | role | - |
| 出力形式 | select | GET /api/v1/admin/bulk/users/export | format | csv/xlsx |

#### 一括無効化

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|-----------------|-------------------|---------------|
| 非アクティブ日数 | number | YES | POST /api/v1/admin/bulk/users/deactivate | inactive_days | 正の整数 |
| プレビューのみ | checkbox | NO | POST /api/v1/admin/bulk/users/deactivate | dry_run | boolean |

---

### 7.7 admin-notifications（通知管理）

#### お知らせ一覧

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| タイトル | テキスト | GET /api/v1/admin/announcements | items[].title | - |
| 種別 | バッジ | GET /api/v1/admin/announcements | items[].announcement_type | INFO/WARNING/MAINTENANCE |
| 対象 | テキスト | GET /api/v1/admin/announcements | items[].target_roles | 空=全員 |
| 表示期間 | テキスト | GET /api/v1/admin/announcements | items[].start_at, end_at | 日付範囲表示 |

#### お知らせ作成/編集

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|-----------------|-------------------|---------------|
| タイトル | text | YES | POST /api/v1/admin/announcements | title | 最大200文字 |
| 種別 | select | YES | POST /api/v1/admin/announcements | announcement_type | INFO/WARNING/MAINTENANCE |
| 本文 | rich-text | YES | POST /api/v1/admin/announcements | content | - |
| 表示開始 | datetime | YES | POST /api/v1/admin/announcements | start_at | ISO 8601 |
| 表示終了 | datetime | NO | POST /api/v1/admin/announcements | end_at | ISO 8601 |
| 対象ロール | multi-select | NO | POST /api/v1/admin/announcements | target_roles | 空=全員 |

#### アラート設定

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|-----------------|-------------------|---------------|
| アラート名 | text | YES | POST /api/v1/admin/alerts | name | 最大100文字 |
| 条件種別 | select | YES | POST /api/v1/admin/alerts | condition_type | ERROR_RATE/STORAGE_USAGE等 |
| 閾値 | number | YES | POST /api/v1/admin/alerts | threshold | 正の数値 |
| 比較演算子 | select | YES | POST /api/v1/admin/alerts | comparison_operator | GT/GTE/LT/LTE/EQ |
| 通知先 | multi-select | YES | POST /api/v1/admin/alerts | notification_channels | EMAIL/SLACK等 |

---

### 7.8 admin-security（セキュリティ管理）

#### 統計カード

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| アクティブセッション数 | 数値 | GET /api/v1/admin/sessions | statistics.active_sessions | - |
| 本日のログイン数 | 数値 | GET /api/v1/admin/sessions | statistics.logins_today | - |

#### セッション一覧

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| ユーザー | テキスト+アバター | GET /api/v1/admin/sessions | items[].user.name | - |
| IPアドレス | テキスト | GET /api/v1/admin/sessions | items[].ip_address | - |
| デバイス | テキスト | GET /api/v1/admin/sessions | items[].device_info | OS+ブラウザ |
| ログイン日時 | テキスト | GET /api/v1/admin/sessions | items[].login_at | 日時フォーマット |
| 最終アクティビティ | テキスト | GET /api/v1/admin/sessions | items[].last_activity_at | 相対時間 |

#### セッション操作

| 画面項目 | 操作 | APIエンドポイント | リクエストボディ | 備考 |
|---------|-----|-----------------|----------------|------|
| 強制ログアウト | button | POST /api/v1/admin/sessions/{id}/terminate | reason | FORCED |
| 全セッション終了 | button | POST /api/v1/admin/sessions/user/{user_id}/terminate-all | - | ユーザー指定 |

---

### 7.9 admin-data-management（データ管理）

#### クリーンアップ

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエスト/パラメータ | バリデーション |
|---------|---------|-----|-----------------|---------------------|---------------|
| 対象データ種別 | multi-select | YES | GET /api/v1/admin/data/cleanup/preview | target_types | activity_logs/audit_logs/deleted_projects |
| 保持期間（日） | number | YES | GET /api/v1/admin/data/cleanup/preview | retention_days | 正の整数 |
| 削除実行 | button | - | POST /api/v1/admin/data/cleanup/execute | target_types, retention_days | - |

#### プレビュー表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| 対象種別 | テキスト | GET /api/v1/admin/data/cleanup/preview | preview[].target_type_display | - |
| レコード数 | 数値 | GET /api/v1/admin/data/cleanup/preview | preview[].record_count | カンマ区切り |
| 推定サイズ | テキスト | GET /api/v1/admin/data/cleanup/preview | preview[].estimated_size_display | - |

#### 保持ポリシー

| 画面項目 | 入力形式 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----------------|-------------------|------|
| 操作履歴保持期間 | number | PATCH /api/v1/admin/data/retention-policy | activity_logs_days | 日数 |
| 監査ログ保持期間 | number | PATCH /api/v1/admin/data/retention-policy | audit_logs_days | 日数 |
| 削除プロジェクト保持期間 | number | PATCH /api/v1/admin/data/retention-policy | deleted_projects_days | 日数 |

---

### 7.10 admin-support-tools（サポートツール）

#### ユーザー代行

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|-----------------|-------------------|---------------|
| ユーザー選択 | autocomplete | YES | POST /api/v1/admin/impersonate/{user_id} | - | パスパラメータ |
| 代行理由 | text | YES | POST /api/v1/admin/impersonate/{user_id} | reason | 必須入力 |
| 代行終了 | button | - | POST /api/v1/admin/impersonate/end | - | - |

#### デバッグモード

| 画面項目 | 操作 | APIエンドポイント | 備考 |
|---------|-----|-----------------|------|
| デバッグ有効化 | button | POST /api/v1/admin/debug/enable | - |
| デバッグ無効化 | button | POST /api/v1/admin/debug/disable | - |

#### ヘルスチェック

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| 全体ステータス | バッジ | GET /api/v1/admin/health-check/detailed | status | healthy緑/unhealthy赤 |
| DB接続 | カード | GET /api/v1/admin/health-check/detailed | checks.database.status | ステータス+応答時間 |
| キャッシュ接続 | カード | GET /api/v1/admin/health-check/detailed | checks.cache.status | ステータス+応答時間 |
| ストレージ接続 | カード | GET /api/v1/admin/health-check/detailed | checks.storage.status | ステータス+応答時間 |
| 外部API接続 | カード | GET /api/v1/admin/health-check/detailed | checks.external_apis.* | ステータス+応答時間 |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| SA-001〜SA-006 | ユーザー操作履歴追跡 | GET /admin/activity-logs | admin-activity-logs | 実装済 |
| SA-007〜SA-011 | 全プロジェクト閲覧 | GET /admin/projects | admin-projects | 実装済 |
| SA-012〜SA-016 | 詳細監査ログ | GET /admin/audit-logs | admin-audit-logs | 実装済 |
| SA-017〜SA-020 | システム設定 | GET/PATCH /admin/settings | admin-settings | 実装済 |
| SA-022〜SA-026 | システム統計 | GET /admin/statistics | admin-statistics | 実装済 |
| SA-027〜SA-030 | 一括操作 | POST /admin/bulk/* | admin-bulk-operations | 実装済 |
| SA-031〜SA-034 | 通知・アラート管理 | /admin/alerts, announcements | admin-notifications | 実装済 |
| SA-035〜SA-036 | セキュリティ管理 | GET /admin/sessions | admin-security | 実装済 |
| SA-037〜SA-040 | データ管理 | /admin/data/* | admin-data-management | 部分実装 |
| SA-041〜SA-043 | サポートツール | /admin/impersonate, debug, health | admin-support-tools | 実装済 |

カバレッジ: 40/43 = 93%（API実装済）

---

## 9. 関連ドキュメント

| ドキュメント | 説明 |
|-------------|------|
| [データベース設計書](../../../06-database/01-database-design.md#36-システム管理) | システム管理関連テーブル定義 |
| [ユースケース定義書](../../../02-usecase/01-usecase-definition.md) | SA-001〜SA-043 ユースケース定義 |
| [API設計書](../../../05-api-design/01-api-endpoints.md) | 管理者API エンドポイント一覧 |
| [認証・認可設計書](../../../08-security/01-authentication.md) | SystemAdmin権限の定義 |
| [ミドルウェア設計書](../../../09-middleware/01-middleware-design.md) | ActivityTrackingMiddleware、AuditLogMiddleware 等 |

---

## 10. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | SA-DESIGN-001 |
| 対象ユースケース | SA-001〜SA-043 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/api/routes/v1/admin/` |
|  | `src/app/services/admin/` |
|  | `src/app/repositories/admin/` |
|  | `src/app/schemas/admin/` |
|  | `src/app/models/audit/` |
|  | `src/app/models/system/` |
|  | `src/app/api/middlewares/activity_tracking.py` |