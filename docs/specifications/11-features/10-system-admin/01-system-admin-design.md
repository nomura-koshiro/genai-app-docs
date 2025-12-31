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

---

## 2. データベース設計

### 2.1 user_activity（ユーザー操作履歴）

**対応ユースケース**: SA-001〜SA-006

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | YES | 操作ユーザー（FK: user_account）※未認証リクエストはNULL |
| action_type | VARCHAR(50) | NO | 操作種別（CREATE/READ/UPDATE/DELETE/LOGIN/LOGOUT等） |
| resource_type | VARCHAR(50) | YES | リソース種別（PROJECT/SESSION/TREE等） |
| resource_id | UUID | YES | 操作対象リソースID |
| endpoint | VARCHAR(255) | NO | APIエンドポイント |
| method | VARCHAR(10) | NO | HTTPメソッド |
| request_body | JSONB | YES | リクエストボディ（機密情報除外） |
| response_status | INTEGER | NO | HTTPレスポンスステータス |
| error_message | TEXT | YES | エラーメッセージ（エラー時のみ） |
| error_code | VARCHAR(50) | YES | エラーコード |
| ip_address | VARCHAR(45) | YES | クライアントIPアドレス |
| user_agent | VARCHAR(500) | YES | ユーザーエージェント |
| duration_ms | INTEGER | NO | 処理時間（ミリ秒） |
| created_at | TIMESTAMP | NO | 作成日時 |

**インデックス**:

- `idx_user_activity_user_id` ON (user_id)
- `idx_user_activity_action_type` ON (action_type)
- `idx_user_activity_resource` ON (resource_type, resource_id)
- `idx_user_activity_created_at` ON (created_at DESC)
- `idx_user_activity_status` ON (response_status)
- `idx_user_activity_error` ON (created_at DESC) WHERE error_message IS NOT NULL

---

### 2.2 audit_log（監査ログ）

**対応ユースケース**: SA-012〜SA-016

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | YES | 操作ユーザー |
| event_type | VARCHAR(50) | NO | イベント種別（DATA_CHANGE/ACCESS/SECURITY） |
| action | VARCHAR(50) | NO | アクション（CREATE/UPDATE/DELETE/LOGIN_SUCCESS/LOGIN_FAILED等） |
| resource_type | VARCHAR(50) | NO | リソース種別 |
| resource_id | UUID | YES | リソースID |
| old_value | JSONB | YES | 変更前の値 |
| new_value | JSONB | YES | 変更後の値 |
| changed_fields | JSONB | YES | 変更されたフィールド一覧 |
| ip_address | VARCHAR(45) | YES | IPアドレス |
| user_agent | VARCHAR(500) | YES | ユーザーエージェント |
| severity | VARCHAR(20) | NO | 重要度（INFO/WARNING/CRITICAL） |
| metadata | JSONB | YES | 追加メタデータ |
| created_at | TIMESTAMP | NO | 作成日時 |

**インデックス**:

- `idx_audit_log_user_id` ON (user_id)
- `idx_audit_log_event_type` ON (event_type)
- `idx_audit_log_resource` ON (resource_type, resource_id)
- `idx_audit_log_severity` ON (severity)
- `idx_audit_log_created_at` ON (created_at DESC)

---

### 2.3 system_setting（システム設定）

**対応ユースケース**: SA-017〜SA-020

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| category | VARCHAR(50) | NO | カテゴリ（GENERAL/SECURITY/MAINTENANCE） |
| key | VARCHAR(100) | NO | 設定キー |
| value | JSONB | NO | 設定値 |
| value_type | VARCHAR(20) | NO | 値の型（STRING/NUMBER/BOOLEAN/JSON） |
| description | TEXT | YES | 説明 |
| is_secret | BOOLEAN | NO | 機密設定フラグ（デフォルト: false） |
| is_editable | BOOLEAN | NO | 編集可能フラグ（デフォルト: true） |
| updated_by | UUID | YES | 更新者 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

**ユニーク制約**: `uq_system_setting_category_key` ON (category, key)

**初期データ例**:

```json
[
  {"category": "GENERAL", "key": "max_file_size_mb", "value": "100", "value_type": "NUMBER"},
  {"category": "GENERAL", "key": "session_timeout_minutes", "value": "60", "value_type": "NUMBER"},
  {"category": "SECURITY", "key": "max_login_attempts", "value": "5", "value_type": "NUMBER"},
  {"category": "SECURITY", "key": "password_expiry_days", "value": "90", "value_type": "NUMBER"},
  {"category": "MAINTENANCE", "key": "maintenance_mode", "value": "false", "value_type": "BOOLEAN"},
  {"category": "MAINTENANCE", "key": "maintenance_message", "value": "\"\"", "value_type": "STRING"}
]
```

---

### 2.4 system_announcement（システムお知らせ）

**対応ユースケース**: SA-033〜SA-034

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| title | VARCHAR(200) | NO | タイトル |
| content | TEXT | NO | 本文 |
| announcement_type | VARCHAR(30) | NO | 種別（INFO/WARNING/MAINTENANCE） |
| priority | INTEGER | NO | 優先度（1が最高、デフォルト: 5） |
| start_at | TIMESTAMP | NO | 表示開始日時 |
| end_at | TIMESTAMP | YES | 表示終了日時（NULLは無期限） |
| is_active | BOOLEAN | NO | 有効フラグ（デフォルト: true） |
| target_roles | JSONB | YES | 対象ロール（NULLまたは空配列は全員） |
| created_by | UUID | NO | 作成者 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

**インデックス**:

- `idx_announcement_active` ON (is_active, start_at, end_at)

---

### 2.6 notification_template（通知テンプレート）

**対応ユースケース**: SA-032

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(100) | NO | テンプレート名 |
| event_type | VARCHAR(50) | NO | イベント種別（PROJECT_CREATED/MEMBER_ADDED等） |
| subject | VARCHAR(200) | NO | 件名テンプレート |
| body | TEXT | NO | 本文テンプレート |
| variables | JSONB | NO | 利用可能変数リスト |
| is_active | BOOLEAN | NO | 有効フラグ（デフォルト: true） |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

---

### 2.7 system_alert（システムアラート設定）

**対応ユースケース**: SA-031

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(100) | NO | アラート名 |
| condition_type | VARCHAR(50) | NO | 条件種別（ERROR_RATE/STORAGE_USAGE/INACTIVE_USERS等） |
| threshold | JSONB | NO | 閾値設定 |
| comparison_operator | VARCHAR(10) | NO | 比較演算子（GT/GTE/LT/LTE/EQ） |
| notification_channels | JSONB | NO | 通知先（EMAIL/SLACK等） |
| is_enabled | BOOLEAN | NO | 有効フラグ（デフォルト: true） |
| last_triggered_at | TIMESTAMP | YES | 最終発火日時 |
| trigger_count | INTEGER | NO | 発火回数（デフォルト: 0） |
| created_by | UUID | NO | 作成者 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

---

### 2.8 user_session（ユーザーセッション）

**対応ユースケース**: SA-035〜SA-036

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | NO | ユーザーID（FK: user_account） |
| session_token_hash | VARCHAR(64) | NO | セッショントークンハッシュ（SHA-256） |
| ip_address | VARCHAR(45) | YES | IPアドレス |
| user_agent | VARCHAR(500) | YES | ユーザーエージェント |
| device_info | JSONB | YES | デバイス情報（OS、ブラウザ等） |
| login_at | TIMESTAMP | NO | ログイン日時 |
| last_activity_at | TIMESTAMP | NO | 最終アクティビティ日時 |
| expires_at | TIMESTAMP | NO | 有効期限 |
| is_active | BOOLEAN | NO | アクティブフラグ（デフォルト: true） |
| logout_at | TIMESTAMP | YES | ログアウト日時 |
| logout_reason | VARCHAR(50) | YES | ログアウト理由（MANUAL/FORCED/EXPIRED/SESSION_LIMIT） |

**インデックス**:

- `idx_user_session_user_id` ON (user_id)
- `idx_user_session_active` ON (is_active, expires_at)
- `idx_user_session_token` ON (session_token_hash)

---

## 3. API設計

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

## 4. ミドルウェア設計

### 4.1 ActivityTrackingMiddleware（操作履歴記録）

全APIリクエストを自動的に記録するミドルウェア。

```python
class ActivityTrackingMiddleware:
    """
    ユーザー操作履歴を自動記録するミドルウェア。
    - 全リクエストの基本情報を記録
    - エラー発生時もエラー情報を含めて記録
    - 除外パスは記録をスキップ
    """

    EXCLUDE_PATHS = [
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico"
    ]

    EXCLUDE_PATTERNS = [
        r"^/static/",
        r"^/assets/"
    ]

    async def __call__(self, request: Request, call_next):
        # 除外パスチェック
        if self._should_skip(request.url.path):
            return await call_next(request)

        start_time = time.time()
        response_status = 200
        error_message = None
        error_code = None

        # リクエストボディの取得（機密情報をマスク）
        request_body = await self._get_masked_request_body(request)

        try:
            response = await call_next(request)
            response_status = response.status_code

            # エラーレスポンスの場合、エラー情報を抽出
            if response_status >= 400:
                error_message, error_code = await self._extract_error_info(response)

            return response

        except HTTPException as e:
            response_status = e.status_code
            error_message = e.detail
            raise

        except Exception as e:
            response_status = 500
            error_message = str(e)
            raise

        finally:
            # 成功・失敗に関わらず記録
            duration_ms = int((time.time() - start_time) * 1000)

            await self._record_activity(
                request=request,
                request_body=request_body,
                response_status=response_status,
                error_message=error_message,
                error_code=error_code,
                duration_ms=duration_ms
            )

    async def _record_activity(self, ...):
        """操作履歴をDBに記録"""
        # URLパターンからresource_type, resource_idを抽出
        resource_type, resource_id = self._extract_resource_info(request.url.path)

        # action_typeをHTTPメソッドから推定
        action_type = self._infer_action_type(request.method, response_status)

        activity = UserActivity(
            user_id=request.state.user.id if hasattr(request.state, 'user') else None,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=request.url.path,
            method=request.method,
            request_body=request_body,
            response_status=response_status,
            error_message=error_message,
            error_code=error_code,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            duration_ms=duration_ms
        )

        # 非同期でDB保存（レスポンスをブロックしない）
        await self.activity_repository.create(activity)

    def _extract_resource_info(self, path: str) -> tuple[str, UUID]:
        """
        URLパスからリソース情報を抽出
        例: /api/v1/projects/123 -> ("PROJECT", "123")
        """
        patterns = {
            r"/api/v1/projects/([^/]+)": "PROJECT",
            r"/api/v1/analysis/session/([^/]+)": "ANALYSIS_SESSION",
            r"/api/v1/driver-tree/tree/([^/]+)": "DRIVER_TREE",
            r"/api/v1/user_accounts/([^/]+)": "USER",
        }
        # パターンマッチング処理...

    def _infer_action_type(self, method: str, status: int) -> str:
        """HTTPメソッドとステータスからアクション種別を推定"""
        if status >= 400:
            return "ERROR"

        mapping = {
            "GET": "READ",
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE"
        }
        return mapping.get(method, "OTHER")

    def _get_masked_request_body(self, body: dict) -> dict:
        """機密情報をマスク"""
        sensitive_keys = ["password", "token", "secret", "api_key", "credential"]
        # マスク処理...
```

### 4.2 除外パスの設定

```python
# 除外するパス（操作履歴に記録しない）
EXCLUDE_PATHS = [
    "/health",           # ヘルスチェック
    "/metrics",          # Prometheusメトリクス
    "/docs",             # Swagger UI
    "/openapi.json",     # OpenAPI仕様
    "/redoc",            # ReDoc
    "/favicon.ico",      # ファビコン
]

# パターンで除外
EXCLUDE_PATTERNS = [
    r"^/static/",        # 静的ファイル
    r"^/assets/",        # アセット
]
```

---

## 5. フロントエンド画面設計

### 5.1 画面一覧

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

### 5.2 サイドバー構成

```text
システム管理
├─ ユーザー管理 (users) [既存]
├─ ロール管理 (roles) [既存]
├─ 検証カテゴリ (verifications) [既存]
└─ 課題マスタ (issues) [既存]

監視・運用 [新規セクション]
├─ システム統計 (admin-statistics)
├─ 操作履歴 (admin-activity-logs)
├─ 監査ログ (admin-audit-logs)
└─ 全プロジェクト (admin-projects)

システム運用 [新規セクション]
├─ システム設定 (admin-settings)
├─ 通知管理 (admin-notifications)
├─ セキュリティ (admin-security)
├─ 一括操作 (admin-bulk-operations)
├─ データ管理 (admin-data-management)
└─ サポートツール (admin-support-tools)
```

---

### 5.3 admin-activity-logs（操作履歴）

**レイアウト**: タブ付きテーブルビュー

#### フィルターセクション

| 項目 | 型 | API対応 |
|-----|---|--------|
| ユーザー選択 | select | user_id |
| 操作種別 | select | action_type |
| リソース種別 | select | resource_type |
| 日時範囲（開始） | datetime | start_date |
| 日時範囲（終了） | datetime | end_date |
| エラーのみ | checkbox | has_error |
| 検索ボタン | button | - |
| エクスポートボタン | button | /export |

#### タブ

| タブ名 | フィルタ条件 |
|-------|------------|
| 全ての操作 | なし |
| エラー履歴 | has_error=true |

#### テーブルカラム

| カラム | 表示内容 | ソート |
|-------|---------|-------|
| 日時 | created_at | 可 |
| ユーザー | user_name + アバター | 可 |
| 操作種別 | action_type（バッジ） | 可 |
| リソース | resource_type + resource_id | - |
| エンドポイント | endpoint | - |
| ステータス | response_status（色分けバッジ） | 可 |
| 処理時間 | duration_ms | 可 |
| 詳細 | 詳細モーダル表示ボタン | - |

#### 詳細モーダル

| セクション | 項目 |
|-----------|-----|
| 基本情報 | 日時、ユーザー、操作種別、リソース |
| リクエスト情報 | メソッド、エンドポイント、リクエストボディ（JSON表示） |
| レスポンス情報 | ステータス、エラーメッセージ、エラーコード |
| 環境情報 | IPアドレス、ユーザーエージェント、処理時間 |

---

### 5.4 admin-projects（全プロジェクト管理）

**レイアウト**: 統計カード + フィルター + テーブル

#### 統計カード

| カード | 表示値 | API |
|-------|-------|-----|
| 総プロジェクト数 | statistics.total_projects | /projects |
| アクティブ数 | statistics.active_projects | /projects |
| 総ストレージ使用量 | statistics.total_storage_display | /projects |
| 非アクティブ数（30日以上） | 別途取得 | /projects/inactive |

#### フィルター

| 項目 | 型 | API対応 |
|-----|---|--------|
| ステータス | select | status |
| オーナー | select | owner_id |
| 非アクティブ日数 | number | inactive_days |
| ソート | select | sort_by |
| プロジェクト名検索 | text | search |

#### テーブルカラム

| カラム | 表示内容 |
|-------|---------|
| チェックボックス | 一括選択用 |
| プロジェクト名 | name（詳細リンク） |
| オーナー | owner.name + アバター |
| ステータス | status（バッジ） |
| メンバー数 | member_count |
| ストレージ使用量 | storage_used_display + プログレスバー |
| 最終アクティビティ | last_activity_at |
| 作成日 | created_at |
| 操作 | ドロップダウン（詳細/アーカイブ/削除） |

#### 一括操作

| ボタン | 機能 |
|-------|-----|
| 一括アーカイブ | 選択項目をアーカイブ |

---

### 5.5 admin-audit-logs（監査ログ）

**レイアウト**: タブ + フィルター + テーブル + 詳細パネル

#### タブ

| タブ名 | event_type |
|-------|-----------|
| データ変更 | DATA_CHANGE |
| アクセスログ | ACCESS |
| セキュリティ | SECURITY |

#### フィルター

| 項目 | 型 | API対応 |
|-----|---|--------|
| ユーザー | select | user_id |
| 重要度 | select | severity |
| リソース種別 | select | resource_type |
| 日時範囲 | datetime-range | start_date, end_date |
| エクスポート | button | /export |

#### テーブルカラム

| カラム | 表示内容 |
|-------|---------|
| 日時 | created_at |
| ユーザー | user_name + アバター |
| イベント種別 | event_type（バッジ） |
| アクション | action（バッジ） |
| リソース | resource_type + resource_id |
| 重要度 | severity（色分けバッジ） |
| 詳細 | 詳細パネル展開ボタン |

#### 詳細パネル（展開時）

| セクション | 項目 |
|-----------|-----|
| 変更内容 | old_value / new_value（JSON diff表示） |
| 変更フィールド | changed_fields |
| 環境情報 | ip_address, user_agent |

---

### 5.6 admin-settings（システム設定）

**レイアウト**: カテゴリタブ + 設定フォーム

#### カテゴリタブ

| タブ名 | category |
|-------|---------|
| 一般設定 | GENERAL |
| セキュリティ | SECURITY |
| メンテナンス | MAINTENANCE |

#### 一般設定フォーム

| 項目 | キー | 型 |
|-----|-----|---|
| 最大ファイルサイズ（MB） | max_file_size_mb | number |
| セッションタイムアウト（分） | session_timeout_minutes | number |

#### セキュリティ設定フォーム

| 項目 | キー | 型 |
|-----|-----|---|
| パスワード有効期限（日） | password_expiry_days | number |
| ログイン試行回数上限 | max_login_attempts | number |
| 2要素認証必須 | require_2fa | toggle |
| IPホワイトリスト | ip_whitelist | textarea |

#### メンテナンス設定

| 項目 | キー | 型 |
|-----|-----|---|
| メンテナンスモード | maintenance_mode | toggle |
| メンテナンスメッセージ | maintenance_message | textarea |
| 管理者アクセス許可 | allow_admin_access | toggle |

---

### 5.7 admin-statistics（システム統計ダッシュボード）

**レイアウト**: 期間セレクタ + 統計カード + グラフ群

#### 期間セレクタ

| 項目 | 型 |
|-----|---|
| 期間 | select（日/週/月/年） |
| カスタム期間 | date-range |

#### 統計カード（6枚）

| カード | 値 |
|-------|---|
| 総ユーザー数 | users.total |
| アクティブユーザー(今日) | users.active_today |
| 総プロジェクト数 | projects.total |
| 総ストレージ使用量 | storage.total_display |
| APIリクエスト(今日) | api.requests_today |
| エラー率(今日) | api.error_rate_percentage |

#### グラフ

| グラフ | 種類 | データソース |
|-------|-----|-------------|
| アクティブユーザー推移 | 折れ線グラフ | /statistics/users |
| ストレージ使用量推移 | 面グラフ | /statistics/storage |
| APIリクエスト推移 | 棒グラフ | /statistics/api-requests |
| エラー発生率推移 | 折れ線グラフ | /statistics/errors |
| リソース別使用状況 | 円グラフ | /statistics/overview |

#### アラートセクション

| 項目 | 表示内容 |
|-----|---------|
| 現在のアラート | アクティブなアラート一覧 |

---

### 5.8 admin-bulk-operations（一括操作）

**レイアウト**: 操作カード選択 + フォーム + プレビュー

#### 操作カード

| カード | 説明 | API |
|-------|-----|-----|
| ユーザー一括インポート | CSVからユーザー登録 | /bulk/users/import |
| ユーザー一括エクスポート | ユーザー情報CSV出力 | /bulk/users/export |
| ユーザー一括無効化 | 非アクティブユーザー無効化 | /bulk/users/deactivate |
| プロジェクト一括アーカイブ | 古いプロジェクトアーカイブ | /bulk/projects/archive |

#### インポートフォーム

| 項目 | 型 |
|-----|---|
| ファイル選択 | file（CSV） |
| テンプレートダウンロード | button |
| プレビュー | table |
| インポート実行 | button |

#### エクスポートフォーム

| 項目 | 型 |
|-----|---|
| フィルター条件 | multi-select |
| 出力形式 | select（CSV/Excel） |
| エクスポート実行 | button |

#### 無効化フォーム

| 項目 | 型 |
|-----|---|
| 非アクティブ日数 | number |
| 対象プレビュー | table |
| 実行 | button（確認ダイアログ付き） |

#### アーカイブフォーム

| 項目 | 型 |
|-----|---|
| 非アクティブ日数 | number |
| 対象プレビュー | table |
| 実行 | button（確認ダイアログ付き） |

---

### 5.9 admin-notifications（通知管理）

**レイアウト**: タブ + リスト/フォーム

#### タブ

| タブ名 | 機能 |
|-------|-----|
| システムお知らせ | お知らせ管理 |
| 通知テンプレート | テンプレート管理 |
| アラート設定 | アラート管理 |

#### お知らせ一覧テーブル

| カラム | 表示内容 |
|-------|---------|
| タイトル | title |
| 種別 | announcement_type（バッジ） |
| 表示期間 | start_at 〜 end_at |
| ステータス | is_active（バッジ） |
| 操作 | 編集/削除ボタン |

#### お知らせ作成フォーム

| 項目 | 型 |
|-----|---|
| タイトル | text |
| 種別 | select（INFO/WARNING/MAINTENANCE） |
| 本文 | rich-text |
| 表示開始 | datetime |
| 表示終了 | datetime |
| 対象ロール | multi-select（空=全員） |
| 有効 | toggle |

#### テンプレート一覧テーブル

| カラム | 表示内容 |
|-------|---------|
| テンプレート名 | name |
| イベント種別 | event_type（バッジ） |
| ステータス | is_active（バッジ） |
| 操作 | 編集ボタン |

#### テンプレート編集フォーム

| 項目 | 型 |
|-----|---|
| 名前 | text |
| イベント種別 | select |
| 件名テンプレート | text |
| 本文テンプレート | textarea |
| 利用可能変数 | chips（読み取り専用） |

#### アラート一覧テーブル

| カラム | 表示内容 |
|-------|---------|
| アラート名 | name |
| 条件種別 | condition_type（バッジ） |
| 閾値 | threshold |
| ステータス | is_enabled（トグル） |
| 最終発火 | last_triggered_at |
| 操作 | 編集/削除ボタン |

#### アラート作成フォーム

| 項目 | 型 |
|-----|---|
| 名前 | text |
| 条件種別 | select |
| 閾値 | number/text |
| 比較演算子 | select |
| 通知先 | multi-select（EMAIL/SLACK等） |

---

### 5.10 admin-security（セキュリティ管理）

**レイアウト**: 統計カード + フィルター + セッションテーブル

#### 統計カード

| カード | 値 |
|-------|---|
| アクティブセッション数 | statistics.active_sessions |
| 本日のログイン数 | statistics.logins_today |
| 疑わしいアクティビティ | 別途取得 |

#### フィルター

| 項目 | 型 |
|-----|---|
| ユーザー検索 | text |
| IPアドレス | text |
| ログイン日時 | date-range |

#### セッション一覧テーブル

| カラム | 表示内容 |
|-------|---------|
| ユーザー | user.name + アバター |
| IPアドレス | ip_address |
| デバイス | device_info（OS、ブラウザ） |
| ログイン日時 | login_at |
| 最終アクティビティ | last_activity_at |
| ステータス | is_active（バッジ） |
| 操作 | 強制ログアウトボタン |

#### ユーザー詳細（モーダル）

| セクション | 項目 |
|-----------|-----|
| 現在のセッション | セッション一覧 |
| 全セッション終了 | button |
| ログイン履歴 | 過去のログイン一覧 |

---

### 5.11 admin-data-management（データ管理）

**レイアウト**: タブ + フォーム/テーブル

#### タブ

| タブ名 | 機能 |
|-------|-----|
| データクリーンアップ | 古いデータ削除 |
| 孤立ファイル | 参照なしファイル削除 |
| 保持ポリシー | ポリシー設定 |
| マスタインポート | マスタ一括登録 |

#### クリーンアップフォーム

| 項目 | 型 |
|-----|---|
| 対象データ種別 | multi-select |
| 保持期間（日） | number |
| プレビュー | table |
| 削除実行 | button（確認付き） |

#### 孤立ファイルテーブル

| カラム | 表示内容 |
|-------|---------|
| 選択 | checkbox |
| ファイル名 | name |
| サイズ | size_display |
| 作成日 | created_at |
| 一括削除 | button |

#### 保持ポリシーフォーム

| 項目 | キー | 型 |
|-----|-----|---|
| 操作履歴保持期間（日） | activity_logs_days | number |
| 監査ログ保持期間（日） | audit_logs_days | number |
| 削除プロジェクト保持期間（日） | deleted_projects_days | number |
| セッションログ保持期間（日） | session_logs_days | number |
| 保存 | - | button |

#### マスタインポートフォーム

| 項目 | 型 |
|-----|---|
| インポート対象 | select（検証/課題/カテゴリ等） |
| ファイル選択 | file（CSV/JSON） |
| プレビュー | table |
| 実行 | button |

---

### 5.12 admin-support-tools（サポートツール）

**レイアウト**: ツールカード群

#### ユーザー代行セクション

| 項目 | 型 |
|-----|---|
| ユーザー検索 | autocomplete |
| 代行理由 | text（必須） |
| 代行開始 | button |
| 現在の代行状態 | alert（代行中表示） |
| 代行終了 | button |

#### デバッグモードセクション

| 項目 | 型 |
|-----|---|
| 現在のステータス | badge（ON/OFF） |
| デバッグ有効化 | button |
| デバッグ無効化 | button |
| ログレベル | select（DEBUG/INFO/WARNING） |

#### ヘルスチェックセクション

| 項目 | 型 |
|-----|---|
| 実行 | button |
| 結果サマリー | cards |
| 詳細結果 | accordion |

#### ヘルスチェック結果詳細

| 項目 | 表示内容 |
|-----|---------|
| DB接続 | status + response_time_ms |
| キャッシュ接続 | status + response_time_ms |
| ストレージ接続 | status + response_time_ms |
| 外部API接続 | status + response_time_ms |
| レスポンスタイム | 各項目の応答時間グラフ |

---

## 6. バックエンド実装ファイル一覧

### 6.1 モデル（8ファイル追加）

```text
src/app/models/
├── audit/
│   ├── __init__.py
│   ├── user_activity.py          # UserActivity
│   └── audit_log.py              # AuditLog
├── system/
│   ├── __init__.py
│   ├── system_setting.py         # SystemSetting
│   ├── system_announcement.py    # SystemAnnouncement
│   ├── notification_template.py  # NotificationTemplate
│   └── system_alert.py           # SystemAlert
└── user_account/
    └── user_session.py           # UserSession（追加）
```

### 6.2 スキーマ（16ファイル追加）

```text
src/app/schemas/admin/
├── activity_log.py           # 操作履歴スキーマ
├── audit_log.py              # 監査ログスキーマ
├── system_setting.py         # システム設定スキーマ
├── statistics.py             # 統計情報スキーマ
├── bulk_operation.py         # 一括操作スキーマ
├── announcement.py           # お知らせスキーマ
├── notification_template.py  # 通知テンプレートスキーマ
├── system_alert.py           # アラートスキーマ
├── security.py               # セキュリティスキーマ
├── data_management.py        # データ管理スキーマ
├── support_tools.py          # サポートツールスキーマ
├── project_admin.py          # 管理者用プロジェクトスキーマ
├── user_session.py           # ユーザーセッションスキーマ
├── impersonation.py          # なりすましスキーマ
└── health_check.py           # ヘルスチェックスキーマ
```

### 6.3 サービス（8ファイル追加）

```text
src/app/services/admin/
├── __init__.py
├── activity_tracking_service.py   # 操作履歴記録・検索
├── audit_log_service.py           # 監査ログ管理
├── system_setting_service.py      # システム設定管理
├── statistics_service.py          # 統計情報集計
├── notification_service.py        # 通知・お知らせ管理
├── session_management_service.py  # セッション管理
├── bulk_operation_service.py      # 一括操作実行
└── support_tools_service.py       # サポートツール
```

### 6.4 リポジトリ（8ファイル追加）

```text
src/app/repositories/admin/
├── __init__.py
├── user_activity_repository.py
├── audit_log_repository.py
├── system_setting_repository.py
├── announcement_repository.py
├── notification_template_repository.py
├── system_alert_repository.py
└── user_session_repository.py
```

### 6.5 ルーター（10ファイル追加）

```text
src/app/api/routes/v1/admin/
├── activity_logs.py      # 操作履歴API
├── audit_logs.py         # 監査ログAPI
├── projects_admin.py     # 管理者用プロジェクトAPI
├── settings.py           # システム設定API
├── statistics.py         # 統計API
├── bulk_operations.py    # 一括操作API
├── notifications.py      # 通知管理API
├── security.py           # セキュリティAPI
├── data_management.py    # データ管理API
└── support_tools.py      # サポートツールAPI
```

### 6.6 ミドルウェア（1ファイル追加）

```text
src/app/api/middlewares/
└── activity_tracking.py   # 操作履歴記録ミドルウェア
```

### 6.7 マイグレーション（1ファイル追加）

```text
alembic/versions/
└── xxxx_add_system_admin_tables.py  # 8テーブル追加
```

---

## 7. 実装優先順位

### Phase 1: 基盤（優先度: 高）

1. データベーステーブル作成（8テーブル）
2. ActivityTrackingMiddleware実装
3. 基本的なリポジトリ・サービス

### Phase 2: 監視系（優先度: 高）

1. システム統計API + 画面
2. 操作履歴API + 画面
3. 監査ログAPI + 画面

### Phase 3: 管理系（優先度: 中）

1. システム設定API + 画面
2. 全プロジェクト管理API + 画面
3. セキュリティ管理API + 画面

### Phase 4: 運用系（優先度: 低）

1. 通知管理API + 画面
2. 一括操作API + 画面
3. データ管理API + 画面
4. サポートツールAPI + 画面

---

## 8. 注意事項

### 8.1 セキュリティ考慮事項

- 全管理者APIにSystemAdmin権限チェックを実装
- 操作履歴の機密情報（パスワード等）はマスク
- 代行操作は監査ログに必ず記録
- 強制ログアウトは監査ログに記録

### 8.2 パフォーマンス考慮事項

- 操作履歴の記録は非同期で実行（レスポンスをブロックしない）
- 統計情報は適切なキャッシュを実装
- 大量データのエクスポートはストリーミング対応

### 8.3 データ保持

- 操作履歴: デフォルト90日
- 監査ログ: デフォルト365日
- 削除プロジェクト: デフォルト30日
- セッションログ: デフォルト30日
