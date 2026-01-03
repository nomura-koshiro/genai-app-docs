# システム管理 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| admin-activity-logs | 操作履歴 | /admin/activity-logs | 操作ログの記録・検索・エラー追跡 |
| admin-projects | 全プロジェクト管理 | /admin/projects | 管理者による全プロジェクト管理 |
| admin-audit-logs | 監査ログ | /admin/audit-logs | データ変更・アクセス・セキュリティログ |
| admin-settings | システム設定 | /admin/settings | アプリ設定・メンテナンス |
| admin-statistics | システム統計 | /admin/statistics | ダッシュボード・統計情報 |
| admin-bulk-operations | 一括操作 | /admin/bulk-operations | ユーザー/プロジェクトの一括処理 |
| admin-notifications | 通知管理 | /admin/notifications | お知らせ・アラート・テンプレート |
| admin-security | セキュリティ管理 | /admin/security | セッション管理・強制ログアウト |
| admin-data-management | データ管理 | /admin/data-management | クリーンアップ・保持ポリシー |
| admin-support-tools | サポートツール | /admin/support-tools | 代行操作・デバッグ・ヘルスチェック |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | 統計カード、設定カード、ヘルスチェックカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `DataTable` | ログ一覧、プロジェクト一覧、セッション一覧 | 同上 |
| `Pagination` | 各種一覧ページネーション | 同上 |
| `Badge` | ステータスバッジ、重要度バッジ、種別バッジ | 同上 |
| `Button` | 各種操作ボタン | 同上 |
| `Input` | 検索入力、設定値入力 | 同上 |
| `Textarea` | お知らせ本文、メンテナンスメッセージ | 同上 |
| `Select` | 各種フィルタ、設定選択 | 同上 |
| `Modal` | 詳細モーダル、確認ダイアログ | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Tabs` | カテゴリタブ、監査ログタブ | 同上 |
| `DatePicker` | 日時範囲フィルタ | 同上 |
| `Progress` | インポート/エクスポート進捗 | 同上 |
| `Avatar` | ユーザーアイコン | 同上 |
| `FileUpload` | CSVインポート | 同上 |
| `Skeleton` | ローディング表示 | 同上 |

### 1.3 コンポーネント構成

```text
features/system-admin/
├── api/
│   ├── get-activity-logs.ts         # GET /admin/activity-logs
│   ├── get-audit-logs.ts            # GET /admin/audit-logs
│   ├── get-settings.ts              # GET /admin/settings
│   ├── update-setting.ts            # PATCH /admin/settings/{category}/{key}
│   ├── get-statistics.ts            # GET /admin/statistics/*
│   ├── get-sessions.ts              # GET /admin/sessions
│   ├── terminate-session.ts         # POST /admin/sessions/{id}/terminate
│   ├── get-projects.ts              # GET /admin/projects
│   ├── bulk-archive-projects.ts     # POST /admin/bulk/projects/archive
│   ├── bulk-import-users.ts         # POST /admin/bulk/users/import
│   ├── bulk-export-users.ts         # GET /admin/bulk/users/export
│   ├── get-announcements.ts         # GET /admin/announcements
│   ├── create-announcement.ts       # POST /admin/announcements
│   ├── get-cleanup-preview.ts       # GET /admin/data/cleanup/preview
│   ├── execute-cleanup.ts           # POST /admin/data/cleanup/execute
│   ├── get-health-check.ts          # GET /admin/health-check/detailed
│   ├── impersonate-user.ts          # POST /admin/impersonate/{user_id}
│   └── index.ts
├── components/
│   ├── activity-log-table/
│   │   ├── activity-log-table.tsx   # 操作履歴テーブル（DataTable使用）
│   │   └── index.ts
│   ├── activity-log-filters/
│   │   ├── activity-log-filters.tsx # フィルタ（Select, DatePicker使用）
│   │   └── index.ts
│   ├── activity-log-detail-modal/
│   │   ├── activity-log-detail-modal.tsx # 詳細モーダル（Modal使用）
│   │   └── index.ts
│   ├── admin-project-table/
│   │   ├── admin-project-table.tsx  # プロジェクト一覧（DataTable使用）
│   │   └── index.ts
│   ├── project-stats-cards/
│   │   ├── project-stats-cards.tsx  # 統計カード群（Card使用）
│   │   └── index.ts
│   ├── audit-log-table/
│   │   ├── audit-log-table.tsx      # 監査ログテーブル（DataTable, Tabs使用）
│   │   └── index.ts
│   ├── audit-log-filters/
│   │   ├── audit-log-filters.tsx    # フィルタ（Select, DatePicker使用）
│   │   └── index.ts
│   ├── audit-log-detail-panel/
│   │   ├── audit-log-detail-panel.tsx # 詳細パネル（Card使用）
│   │   └── index.ts
│   ├── settings-form/
│   │   ├── settings-form.tsx        # 設定フォーム（Input, Select使用）
│   │   ├── settings-category-tabs.tsx # カテゴリタブ（Tabs使用）
│   │   ├── maintenance-mode-toggle.tsx # メンテナンス切替（Modal使用）
│   │   └── index.ts
│   ├── stats-overview-cards/
│   │   ├── stats-overview-cards.tsx # 統計カード群（Card使用）
│   │   └── index.ts
│   ├── user-trend-chart/
│   │   ├── user-trend-chart.tsx     # ユーザー推移グラフ
│   │   └── index.ts
│   ├── storage-chart/
│   │   ├── storage-chart.tsx        # ストレージグラフ
│   │   └── index.ts
│   ├── api-request-chart/
│   │   ├── api-request-chart.tsx    # APIリクエストグラフ
│   │   └── index.ts
│   ├── user-import-form/
│   │   ├── user-import-form.tsx     # インポート（FileUpload, Progress使用）
│   │   └── index.ts
│   ├── user-export-form/
│   │   ├── user-export-form.tsx     # エクスポート（Select, Button使用）
│   │   └── index.ts
│   ├── bulk-deactivate-form/
│   │   ├── bulk-deactivate-form.tsx # 一括無効化（Input, Button使用）
│   │   └── index.ts
│   ├── announcement-list/
│   │   ├── announcement-list.tsx    # お知らせ一覧（DataTable使用）
│   │   └── index.ts
│   ├── announcement-form/
│   │   ├── announcement-form.tsx    # お知らせ作成（Input, Textarea, Select使用）
│   │   └── index.ts
│   ├── alert-config-form/
│   │   ├── alert-config-form.tsx    # アラート設定（Input, Select使用）
│   │   └── index.ts
│   ├── session-table/
│   │   ├── session-table.tsx        # セッション一覧（DataTable, Avatar使用）
│   │   └── index.ts
│   ├── session-stats-cards/
│   │   ├── session-stats-cards.tsx  # 統計カード（Card使用）
│   │   └── index.ts
│   ├── force-logout-modal/
│   │   ├── force-logout-modal.tsx   # 強制ログアウト（Modal使用）
│   │   └── index.ts
│   ├── cleanup-preview/
│   │   ├── cleanup-preview.tsx      # クリーンアップ（Card, Select使用）
│   │   └── index.ts
│   ├── retention-policy-form/
│   │   ├── retention-policy-form.tsx # 保持ポリシー（Input使用）
│   │   └── index.ts
│   ├── impersonate-form/
│   │   ├── impersonate-form.tsx     # 代行操作（Input, Button使用）
│   │   └── index.ts
│   ├── debug-mode-toggle/
│   │   ├── debug-mode-toggle.tsx    # デバッグモード（Button使用）
│   │   └── index.ts
│   ├── health-check-cards/
│   │   ├── health-check-cards.tsx   # ヘルスチェック（Card, Badge使用）
│   │   └── index.ts
│   └── index.ts
├── routes/
│   ├── activity-logs/
│   │   ├── activity-logs.tsx        # 操作履歴コンテナ
│   │   ├── activity-logs.hook.ts    # 操作履歴用hook
│   │   └── index.ts
│   ├── admin-projects/
│   │   ├── admin-projects.tsx       # 全プロジェクト管理コンテナ
│   │   ├── admin-projects.hook.ts   # 全プロジェクト管理用hook
│   │   └── index.ts
│   ├── admin-project-detail/
│   │   ├── admin-project-detail.tsx # プロジェクト詳細コンテナ
│   │   ├── admin-project-detail.hook.ts # プロジェクト詳細用hook
│   │   └── index.ts
│   ├── audit-logs/
│   │   ├── audit-logs.tsx           # 監査ログコンテナ
│   │   ├── audit-logs.hook.ts       # 監査ログ用hook
│   │   └── index.ts
│   ├── settings/
│   │   ├── settings.tsx             # システム設定コンテナ
│   │   ├── settings.hook.ts         # システム設定用hook
│   │   └── index.ts
│   ├── statistics/
│   │   ├── statistics.tsx           # システム統計コンテナ
│   │   ├── statistics.hook.ts       # システム統計用hook
│   │   └── index.ts
│   ├── bulk-operations/
│   │   ├── bulk-operations.tsx      # 一括操作コンテナ
│   │   ├── bulk-operations.hook.ts  # 一括操作用hook
│   │   └── index.ts
│   ├── notifications/
│   │   ├── notifications.tsx        # 通知管理コンテナ
│   │   ├── notifications.hook.ts    # 通知管理用hook
│   │   └── index.ts
│   ├── security/
│   │   ├── security.tsx             # セキュリティ管理コンテナ
│   │   ├── security.hook.ts         # セキュリティ管理用hook
│   │   └── index.ts
│   ├── data-management/
│   │   ├── data-management.tsx      # データ管理コンテナ
│   │   ├── data-management.hook.ts  # データ管理用hook
│   │   └── index.ts
│   └── support-tools/
│       ├── support-tools.tsx        # サポートツールコンテナ
│       ├── support-tools.hook.ts    # サポートツール用hook
│       └── index.ts
├── types/
│   ├── api.ts                       # API入出力の型
│   ├── domain.ts                    # ドメインモデル（ActivityLog, AuditLog, Setting等）
│   └── index.ts
└── index.ts

app/admin/
├── activity-logs/
│   └── page.tsx                     # 操作履歴画面 → ActivityLogs
├── projects/
│   ├── page.tsx                     # 全プロジェクト管理画面 → AdminProjects
│   └── [id]/
│       └── page.tsx                 # プロジェクト詳細 → AdminProjectDetail
├── audit-logs/
│   └── page.tsx                     # 監査ログ画面 → AuditLogs
├── settings/
│   └── page.tsx                     # システム設定画面 → Settings
├── statistics/
│   └── page.tsx                     # システム統計ダッシュボード → Statistics
├── bulk-operations/
│   └── page.tsx                     # 一括操作画面 → BulkOperations
├── notifications/
│   └── page.tsx                     # 通知管理画面 → Notifications
├── security/
│   └── page.tsx                     # セキュリティ管理画面 → Security
├── data-management/
│   └── page.tsx                     # データ管理画面 → DataManagement
└── support-tools/
    └── page.tsx                     # サポートツール画面 → SupportTools
```

---

## 2. 画面詳細設計

### 2.1 admin-activity-logs（操作履歴）

#### 詳細モーダル

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|-----------------|-------------------|---------|
| リクエストボディ | JSON | GET /api/v1/admin/activity-logs/{id} | request_body | JSON整形 |
| エラーメッセージ | テキスト | GET /api/v1/admin/activity-logs/{id} | error_message | - |
| エラーコード | テキスト | GET /api/v1/admin/activity-logs/{id} | error_code | - |
| IPアドレス | テキスト | GET /api/v1/admin/activity-logs/{id} | ip_address | - |
| ユーザーエージェント | テキスト | GET /api/v1/admin/activity-logs/{id} | user_agent | - |

---

### 2.2 admin-projects（全プロジェクト管理）

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
| 一括アーカイブ | button | POST /api/v1/admin/bulk/projects/archive | project_ids[] | 選択項目のID配列 |

---

### 2.3 admin-audit-logs（監査ログ）

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

### 2.4 admin-settings（システム設定）

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

### 2.5 admin-statistics（システム統計）

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

### 2.6 admin-bulk-operations（一括操作）

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

### 2.7 admin-notifications（通知管理）

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

### 2.8 admin-security（セキュリティ管理）

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

### 2.9 admin-data-management（データ管理）

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

### 2.10 admin-support-tools（サポートツール）

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

## 3. 画面項目・APIマッピング

### 3.1 操作履歴

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ユーザーフィルタ | セレクト | - | `GET /admin/activity-logs` | `user_id` | UUID |
| アクションフィルタ | セレクト | - | 同上 | `action_type` | - |
| 日時範囲 | 日付範囲 | - | 同上 | `start_date`, `end_date` | ISO8601 |

### 3.2 一括操作

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| CSVファイル | ファイル選択 | ✓ | `POST /admin/bulk/users/import` | `file` | CSV形式 |
| プレビューのみ | チェックボックス | - | 同上 | `dry_run` | boolean |

### 3.3 システム設定

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 設定値 | 動的 | ✓ | `PATCH /admin/settings/{category}/{key}` | `value` | value_typeに応じた検証 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| 操作履歴ページ表示 | `GET /admin/activity-logs` | 初期ロード |
| 監査ログページ表示 | `GET /admin/audit-logs` | 初期ロード |
| システム統計ページ表示 | `GET /admin/statistics/overview` | 初期ロード |
| 統計グラフ期間変更 | `GET /admin/statistics/users` 等 | 再取得 |
| 設定ページ表示 | `GET /admin/settings` | カテゴリ一覧取得 |
| 設定値変更 | `PATCH /admin/settings/{category}/{key}` | - |
| メンテナンスモード切替 | `POST /admin/settings/maintenance/enable` | - |
| セッション一覧表示 | `GET /admin/sessions` | - |
| 強制ログアウト | `POST /admin/sessions/{id}/terminate` | - |
| クリーンアッププレビュー | `GET /admin/data/cleanup/preview` | - |
| クリーンアップ実行 | `POST /admin/data/cleanup/execute` | 確認後 |
| ヘルスチェック | `GET /admin/health-check/detailed` | - |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | 管理者権限が必要ですメッセージ表示 |
| 404 Not Found | リソースが見つかりませんメッセージ表示 |
| 409 Conflict | 操作が競合していますメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| メンテナンス中 | メンテナンス中画面を表示 |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| ログ一覧 | ページネーションで件数制限、日時範囲フィルタ |
| 統計グラフ | 集計済みデータをAPIから取得、クライアント計算を最小化 |
| 一括操作 | プログレス表示、バックグラウンド処理 |
| キャッシュ | React Query で統計データを5分間キャッシュ |
| 再レンダリング | useMemo でグラフデータを最適化 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| SA-001〜SA-006 | 操作履歴管理 | `GET/POST /admin/activity-logs` | admin-activity-logs | 設計済 |
| SA-007〜SA-011 | 全プロジェクト管理 | `GET/PATCH /admin/projects` | admin-projects | 設計済 |
| SA-012〜SA-016 | 監査ログ管理 | `GET /admin/audit-logs` | admin-audit-logs | 設計済 |
| SA-017〜SA-021 | システム設定 | `GET/PATCH /admin/settings` | admin-settings | 設計済 |
| SA-022〜SA-026 | システム統計 | `GET /admin/statistics` | admin-statistics | 設計済 |
| SA-027〜SA-030 | 一括操作 | `POST /admin/bulk-operations` | admin-bulk-operations | 設計済 |
| SA-031〜SA-034 | 通知管理 | `GET/POST /admin/notifications` | admin-notifications | 設計済 |
| SA-035〜SA-036 | セキュリティ管理 | `GET/POST /admin/security` | admin-security | 設計済 |
| SA-037〜SA-040 | データ管理 | `GET/POST /admin/data` | admin-data-management | 設計済 |
| SA-041〜SA-043 | サポートツール | `POST /admin/impersonate` | admin-support-tools | 設計済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| ActivityLogTable | Default | 操作履歴テーブル表示 | 通常、空、エラーログ表示 |
| ActivityLogFilters | Default | 操作履歴フィルター | 初期状態、選択状態 |
| ActivityLogDetailModal | Default | 操作履歴詳細モーダル | 通常、エラー情報付き |
| AdminProjectTable | Default | 管理者プロジェクト一覧 | 通常、選択状態 |
| ProjectStatsCards | Default | プロジェクト統計カード群 | 通常 |
| AuditLogTable | Default | 監査ログテーブル | 通常、変更ログタブ、セキュリティログタブ |
| AuditLogDetailPanel | Default | 監査ログ詳細パネル | 通常、JSON差分表示 |
| SettingsForm | Default | システム設定フォーム | 通常、メンテナンス設定 |
| MaintenanceModeToggle | Default | メンテナンスモード切替 | 有効、無効 |
| StatsOverviewCards | Default | 統計概要カード群 | 通常 |
| UserTrendChart | Default | ユーザー推移グラフ | 通常 |
| StorageChart | Default | ストレージ使用量グラフ | 通常 |
| SessionTable | Default | セッション一覧テーブル | 通常、統計付き |
| ForceLogoutModal | Default | 強制ログアウトモーダル | 通常 |
| CleanupPreview | Default | クリーンアッププレビュー | 通常 |
| HealthCheckCards | Default | ヘルスチェックカード群 | 正常、異常 |
| ImpersonateForm | Default | 代行操作フォーム | 通常、代行中 |

### 8.2 ストーリー実装例

```tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { HealthCheckCards } from "./health-check-cards";
import type { HealthCheckStatus } from "../../types";

const healthyChecks: HealthCheckStatus = {
  database: { status: "healthy", responseTime: 12 },
  cache: { status: "healthy", responseTime: 3 },
  storage: { status: "healthy", responseTime: 45 },
  externalApis: {
    openai: { status: "healthy", responseTime: 150 },
  },
};

const meta = {
  title: "features/system-admin/components/health-check-cards",
  component: HealthCheckCards,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "ヘルスチェック状態を表示するカード群コンポーネント。",
      },
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof HealthCheckCards>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Healthy: Story = {
  args: {
    status: "healthy",
    checks: healthyChecks,
  },
};

export const Unhealthy: Story = {
  args: {
    status: "unhealthy",
    checks: {
      ...healthyChecks,
      cache: { status: "unhealthy", responseTime: null, error: "Connection refused" },
      externalApis: {
        openai: { status: "degraded", responseTime: 2500 },
      },
    },
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | テーブル表示、フィルタ動作、モーダル操作 |
| ユーティリティ | ユニットテスト | 90%以上 | 日時フォーマット、統計計算、バリデーション |
| 統合 | コンポーネントテスト | 70%以上 | ログ検索、設定変更、セッション管理 |
| E2E | E2Eテスト | 主要フロー | 管理操作、一括処理、ヘルスチェック |

### 9.2 ユニットテスト例

```typescript
import { describe, it, expect } from "vitest";
import { formatRelativeTime, getSeverityColor, parseDeviceInfo } from "./admin-utils";

describe("formatRelativeTime", () => {
  it("数秒前を正しく表示する", () => {
    const date = new Date(Date.now() - 30 * 1000);
    expect(formatRelativeTime(date)).toBe("30秒前");
  });

  it("数分前を正しく表示する", () => {
    const date = new Date(Date.now() - 5 * 60 * 1000);
    expect(formatRelativeTime(date)).toBe("5分前");
  });

  it("数時間前を正しく表示する", () => {
    const date = new Date(Date.now() - 3 * 60 * 60 * 1000);
    expect(formatRelativeTime(date)).toBe("3時間前");
  });
});

describe("getSeverityColor", () => {
  it("INFOに青色を返す", () => {
    expect(getSeverityColor("INFO")).toBe("blue");
  });

  it("WARNINGに黄色を返す", () => {
    expect(getSeverityColor("WARNING")).toBe("yellow");
  });

  it("CRITICALに赤色を返す", () => {
    expect(getSeverityColor("CRITICAL")).toBe("red");
  });
});

describe("parseDeviceInfo", () => {
  it("ユーザーエージェントからデバイス情報を抽出する", () => {
    const ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0";
    const result = parseDeviceInfo(ua);
    expect(result.os).toBe("Windows 10");
    expect(result.browser).toBe("Chrome 120");
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { SessionTable } from "./session-table";
import type { Session } from "../../types";

describe("SessionTable", () => {
  const mockSessions: Session[] = [
    {
      id: "session-1",
      user: { name: "山田 太郎", email: "yamada@example.com" },
      ipAddress: "192.168.1.1",
      deviceInfo: "Windows 10 / Chrome 120",
      loginAt: "2026-01-01T10:00:00Z",
      lastActivityAt: "2026-01-01T11:30:00Z",
    },
    {
      id: "session-2",
      user: { name: "鈴木 花子", email: "suzuki@example.com" },
      ipAddress: "192.168.1.2",
      deviceInfo: "macOS / Safari 17",
      loginAt: "2026-01-01T09:00:00Z",
      lastActivityAt: "2026-01-01T11:00:00Z",
    },
  ];

  it("セッション一覧を表示する", () => {
    render(<SessionTable sessions={mockSessions} onTerminate={vi.fn()} />);

    expect(screen.getByText("山田 太郎")).toBeInTheDocument();
    expect(screen.getByText("鈴木 花子")).toBeInTheDocument();
    expect(screen.getByText("192.168.1.1")).toBeInTheDocument();
  });

  it("強制ログアウトボタンを表示する", () => {
    render(<SessionTable sessions={mockSessions} onTerminate={vi.fn()} />);

    const terminateButtons = screen.getAllByRole("button", { name: "強制ログアウト" });
    expect(terminateButtons).toHaveLength(2);
  });

  it("強制ログアウトボタンクリックでonTerminateを呼び出す", async () => {
    const user = userEvent.setup();
    const onTerminate = vi.fn();
    render(<SessionTable sessions={mockSessions} onTerminate={onTerminate} />);

    const terminateButtons = screen.getAllByRole("button", { name: "強制ログアウト" });
    await user.click(terminateButtons[0]);

    // 確認モーダルが表示される
    expect(screen.getByText("このセッションを強制終了しますか？")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "終了する" }));

    await waitFor(() => {
      expect(onTerminate).toHaveBeenCalledWith("session-1");
    });
  });

  it("空の状態を表示する", () => {
    render(<SessionTable sessions={[]} onTerminate={vi.fn()} />);

    expect(screen.getByText("アクティブなセッションはありません")).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
import { test, expect } from "@playwright/test";

test.describe("システム管理機能", () => {
  test.beforeEach(async ({ page }) => {
    // 管理者としてログイン
    await page.goto("/admin/login");
    await page.getByLabel("メールアドレス").fill("admin@example.com");
    await page.getByLabel("パスワード").fill("admin-password");
    await page.getByRole("button", { name: "ログイン" }).click();
  });

  test("操作履歴を検索できる", async ({ page }) => {
    await page.goto("/admin/activity-logs");

    // フィルタ適用
    await page.getByLabel("ユーザー").selectOption("user-1");
    await page.getByLabel("アクション").selectOption("LOGIN");

    // 結果確認
    await expect(page.getByTestId("activity-log-row")).toHaveCount(5);
  });

  test("システム設定を変更できる", async ({ page }) => {
    await page.goto("/admin/settings");

    // 一般設定タブ
    await page.getByRole("tab", { name: "一般" }).click();

    // 設定値変更
    await page.getByLabel("セッションタイムアウト").fill("60");
    await page.getByRole("button", { name: "保存" }).click();

    // 成功メッセージ
    await expect(page.getByText("設定を保存しました")).toBeVisible();
  });

  test("メンテナンスモードを有効化できる", async ({ page }) => {
    await page.goto("/admin/settings");

    // メンテナンス設定
    await page.getByRole("tab", { name: "メンテナンス" }).click();
    await page.getByRole("button", { name: "メンテナンスモード有効化" }).click();

    // 確認モーダル
    await page.getByLabel("メンテナンスメッセージ").fill("システムメンテナンス中です");
    await page.getByRole("button", { name: "有効化" }).click();

    // 成功メッセージ
    await expect(page.getByText("メンテナンスモードを有効化しました")).toBeVisible();
  });

  test("セッションを強制終了できる", async ({ page }) => {
    await page.goto("/admin/security");

    // セッション終了
    await page.getByTestId("session-row-1").getByRole("button", { name: "強制ログアウト" }).click();

    // 確認ダイアログ
    await page.getByLabel("理由").fill("セキュリティ上の理由");
    await page.getByRole("button", { name: "終了する" }).click();

    // 成功メッセージ
    await expect(page.getByText("セッションを終了しました")).toBeVisible();
  });

  test("ヘルスチェックを実行できる", async ({ page }) => {
    await page.goto("/admin/support-tools");

    // ヘルスチェック実行
    await page.getByRole("button", { name: "ヘルスチェック実行" }).click();

    // 結果確認
    await expect(page.getByTestId("health-status")).toBeVisible();
    await expect(page.getByText("データベース")).toBeVisible();
    await expect(page.getByText("キャッシュ")).toBeVisible();
  });

  test("データクリーンアップをプレビューできる", async ({ page }) => {
    await page.goto("/admin/data-management");

    // クリーンアップ対象選択
    await page.getByLabel("操作履歴").check();
    await page.getByLabel("保持期間（日）").fill("90");

    // プレビュー
    await page.getByRole("button", { name: "プレビュー" }).click();

    // 結果確認
    await expect(page.getByText("削除対象レコード数")).toBeVisible();
  });
});
```

### 9.5 モックデータ

```typescript
// src/testing/mocks/handlers/system-admin.ts
import { http, HttpResponse } from "msw";

export const systemAdminHandlers = [
  http.get("/api/admin/activity-logs", ({ request }) => {
    const url = new URL(request.url);
    const userId = url.searchParams.get("user_id");
    const actionType = url.searchParams.get("action_type");

    const logs = [
      {
        id: "log-1",
        userId: "user-1",
        userName: "山田 太郎",
        actionType: "LOGIN",
        resourceType: "SESSION",
        ipAddress: "192.168.1.1",
        createdAt: "2026-01-01T10:00:00Z",
        isError: false,
      },
      {
        id: "log-2",
        userId: "user-2",
        userName: "鈴木 花子",
        actionType: "UPDATE",
        resourceType: "PROJECT",
        ipAddress: "192.168.1.2",
        createdAt: "2026-01-01T09:30:00Z",
        isError: false,
      },
    ];

    let filtered = logs;
    if (userId) {
      filtered = filtered.filter((l) => l.userId === userId);
    }
    if (actionType) {
      filtered = filtered.filter((l) => l.actionType === actionType);
    }

    return HttpResponse.json({ items: filtered, total: filtered.length });
  }),

  http.get("/api/admin/sessions", () => {
    return HttpResponse.json({
      items: [
        {
          id: "session-1",
          user: { name: "山田 太郎", email: "yamada@example.com" },
          ipAddress: "192.168.1.1",
          deviceInfo: "Windows 10 / Chrome 120",
          loginAt: "2026-01-01T10:00:00Z",
          lastActivityAt: "2026-01-01T11:30:00Z",
        },
      ],
      statistics: {
        activeSessions: 15,
        loginsToday: 42,
      },
    });
  }),

  http.post("/api/admin/sessions/:id/terminate", () => {
    return HttpResponse.json({ success: true });
  }),

  http.get("/api/admin/settings", () => {
    return HttpResponse.json({
      categories: {
        GENERAL: [
          { key: "session_timeout", value: 30, valueType: "number", description: "セッションタイムアウト（分）" },
          { key: "max_upload_size", value: 50, valueType: "number", description: "最大アップロードサイズ（MB）" },
        ],
        SECURITY: [
          { key: "password_min_length", value: 8, valueType: "number", description: "パスワード最小長" },
        ],
        MAINTENANCE: [
          { key: "maintenance_mode", value: false, valueType: "boolean", description: "メンテナンスモード" },
        ],
      },
    });
  }),

  http.patch("/api/admin/settings/:category/:key", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ success: true, value: body.value });
  }),

  http.get("/api/admin/health-check/detailed", () => {
    return HttpResponse.json({
      status: "healthy",
      checks: {
        database: { status: "healthy", responseTime: 12 },
        cache: { status: "healthy", responseTime: 3 },
        storage: { status: "healthy", responseTime: 45 },
        externalApis: {
          openai: { status: "healthy", responseTime: 150 },
        },
      },
    });
  }),

  http.get("/api/admin/statistics/overview", () => {
    return HttpResponse.json({
      users: { total: 1250, activeToday: 87 },
      projects: { total: 340, active: 280 },
      storage: { totalDisplay: "1.2 TB", usedPercent: 45 },
      api: { requestsToday: 125000, errorRatePercentage: 0.5 },
    });
  }),

  http.get("/api/admin/data/cleanup/preview", ({ request }) => {
    const url = new URL(request.url);
    const targetTypes = url.searchParams.get("target_types");

    return HttpResponse.json({
      preview: [
        {
          targetType: "activity_logs",
          targetTypeDisplay: "操作履歴",
          recordCount: 15000,
          estimatedSizeDisplay: "120 MB",
        },
      ],
    });
  }),

  http.post("/api/admin/impersonate/:userId", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      success: true,
      impersonatedUser: { id: "user-1", name: "山田 太郎" },
      reason: body.reason,
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-system-admin-design.md](./01-system-admin-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | SA-FRONTEND-001 |
| 対象ユースケース | SA-001〜SA-043 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/admin/` |
