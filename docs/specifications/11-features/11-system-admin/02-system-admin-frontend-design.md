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

### 1.2 コンポーネント構成

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
| 一括アーカイブ | button | POST /api/v1/admin/projects/bulk-archive | project_ids[] | 選択項目のID配列 |

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

## 8. 関連ドキュメント

- **バックエンド設計書**: [01-system-admin-design.md](./01-system-admin-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | SA-FRONTEND-001 |
| 対象ユースケース | SA-001〜SA-043 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `pages/admin/` |
