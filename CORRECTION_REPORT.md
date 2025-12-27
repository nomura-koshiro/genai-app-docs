# 修正レポート

モックアップ・ユースケース分析に基づく実装修正計画書

---

## 概要

本レポートは以下の分析結果を統合し、必要な修正項目を優先度別に整理したものです：

1. **API差異分析** (`API_GAP_ANALYSIS.md`) - モックアップ仕様と現行実装の差異
2. **ユースケース分析** (`docs/specifications/01-usercases/`) - 137ユースケースから抽出された要件
3. **DBスキーマ改善提案** - ユースケースフロー分析から特定された設計課題

---

## 1. データベーススキーマ修正（実装完了）

### 1.1 高優先度：データ整合性の確保 ✅ 完了

| # | 修正内容 | 対象テーブル | 状態 |
|---|---------|-------------|------|
| 1 | `parent_snapshot_id` カラム追加 | `analysis_snapshots` | ✅ 実装済み |
| 2 | `driver_tree_id` FK追加 | `driver_tree_nodes` | ✅ 実装済み |
| 3 | `current_snapshot_id` UUID FK化 | `analysis_sessions` | ✅ 実装済み |
| 4 | `category_id` FK追加 | `driver_tree_formulas` | ✅ 実装済み |

### 1.2 中優先度：状態管理の改善 ✅ 完了

| # | 修正内容 | 対象テーブル | 状態 |
|---|---------|-------------|------|
| 1 | `status` カラム追加 | `analysis_sessions` | ✅ 実装済み |
| 2 | `status` カラム追加 | `driver_trees` | ✅ 実装済み |
| 3 | `triggered_by_chat_id` FK追加 | `analysis_steps` | ✅ 実装済み |
| 4 | `order_index` UNIQUE制約追加 | `analysis_steps` | ✅ 実装済み |

### 1.3 低優先度：拡張機能サポート

| # | 修正内容 | 対象テーブル | 状態 |
|---|---------|-------------|------|
| 1 | ロール履歴テーブル追加 | 新規テーブル | ✅ 実装済み |
| 2 | ファイルバージョニング | `project_files` | ✅ 実装済み |
| 3 | テンプレートテーブル追加 | 新規テーブル | ✅ 実装済み |

---

## 2. 新規API実装（機能追加）

### 2.1 高優先度：コア機能 ✅ 完了

#### 2.1.1 ダッシュボードAPI ✅ 実装済み

```
GET  /api/v1/dashboard/stats        - 統計情報取得 ✅
GET  /api/v1/dashboard/activities   - アクティビティログ取得 ✅
GET  /api/v1/dashboard/charts       - チャートデータ取得 ✅
```

#### 2.1.2 チャットメッセージ履歴 ✅ 実装済み

```
GET    /api/v1/project/{project_id}/analysis/session/{session_id}/messages ✅
DELETE /api/v1/project/{project_id}/analysis/session/{session_id}/messages/{chat_id} ✅ NEW
```

#### 2.1.3 スナップショット管理 ✅ 実装済み

```
POST /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots ✅
GET  /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots ✅
POST /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots/{id}/restore ✅
```

### 2.2 中優先度：ユーティリティ機能 ✅ 完了

#### 2.2.1 複製機能 ✅ 実装済み

```
POST /api/v1/project/{project_id}/analysis/session/{session_id}/duplicate ✅
POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/duplicate ✅
```

#### 2.2.2 管理機能CRUD ✅ 実装済み

```
# カテゴリマスタ
GET    /api/v1/admin/category ✅
GET    /api/v1/admin/category/{id} ✅
POST   /api/v1/admin/category ✅
PUT    /api/v1/admin/category/{id} ✅
DELETE /api/v1/admin/category/{id} ✅

# 検証マスタ
GET    /api/v1/admin/validation ✅
GET    /api/v1/admin/validation/{id} ✅
POST   /api/v1/admin/validation ✅
PUT    /api/v1/admin/validation/{id} ✅
DELETE /api/v1/admin/validation/{id} ✅

# 課題マスタ
GET    /api/v1/admin/issue ✅
GET    /api/v1/admin/issue/{id} ✅
POST   /api/v1/admin/issue ✅
PUT    /api/v1/admin/issue/{id} ✅
DELETE /api/v1/admin/issue/{id} ✅

# グラフ軸マスタ ✅ NEW
GET    /api/v1/admin/graph-axis ✅
GET    /api/v1/admin/graph-axis/{id} ✅
POST   /api/v1/admin/graph-axis ✅
PATCH  /api/v1/admin/graph-axis/{id} ✅
DELETE /api/v1/admin/graph-axis/{id} ✅

# ロール一覧
GET    /api/v1/admin/role ✅
```

#### 2.2.3 ユーザー管理拡張 ✅ 実装済み

```
PATCH /api/v1/user_account/{id}/activate ✅
PATCH /api/v1/user_account/{id}/deactivate ✅
PUT   /api/v1/user_account/{id}/role ✅
```

### 2.3 低優先度：品質向上 ✅ 完了

#### 2.3.1 データ紐付け更新 ✅ 実装済み

```
POST /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}/refresh ✅
```

#### 2.3.2 ロール一覧API ✅ 実装済み

```
GET /api/v1/admin/role ✅
```

---

## 3. 既存API拡張

### 3.1 プロジェクトAPI拡張 ✅ 完了

| フィールド | 状態 | 備考 |
|-----------|------|------|
| `start_date` | ✅ 実装済み | プロジェクト開始日（スキーマ・モデルに追加済み） |
| `end_date` | ✅ 実装済み | プロジェクト終了日（スキーマ・モデルに追加済み） |
| `stats.member_count` | ✅ 実装済み | メンバー数統計 |
| `stats.file_count` | ✅ 実装済み | ファイル数統計 |
| `stats.session_count` | ✅ 実装済み | セッション数統計 |
| `stats.tree_count` | ✅ 実装済み | ツリー数統計 |

### 3.2 ファイルAPI拡張

| フィールド | 状態 | 備考 |
|-----------|------|------|
| `usage.session_count` | ✅ 実装済み | ファイル使用状況 |
| `usage.tree_count` | ✅ 実装済み | ファイル使用状況 |

### 3.3 施策API拡張 ✅ 完了

| フィールド | 状態 | 備考 |
|-----------|------|------|
| `description` | ✅ 実装済み | 施策説明 |
| `cost` | ✅ 実装済み | コスト |
| `duration_months` | ✅ 実装済み | 実施期間（月） |
| `status` | ✅ 実装済み | 状態（planned/in_progress/completed） |

### 3.4 計算結果API拡張 ✅ 完了

| フィールド | 状態 | 備考 |
|-----------|------|------|
| `summary.total_nodes` | ✅ 実装済み | 総ノード数 |
| `summary.calculated_nodes` | ✅ 実装済み | 計算ノード数 |
| `summary.error_nodes` | ✅ 実装済み | エラーノード数 |
| `policy_effects` | ✅ 実装済み | 施策効果 |

### 3.5 ユーザー詳細API拡張 ✅ 完了

| フィールド | 状態 | 備考 |
|-----------|------|------|
| `stats.project_count` | ✅ 実装済み | 参加プロジェクト数 |
| `stats.session_count` | ✅ 実装済み | 作成セッション数 |
| `stats.last_login_at` | ✅ 実装済み | 最終ログイン日時 |
| `projects` | ✅ 実装済み | 参加プロジェクト一覧 |
| `activities` | ✅ 実装済み | アクティビティログ |

---

## 4. パス命名規則の統一

v2 APIは削除済み。すべてのエンドポイントを `/api/v1` に統一。

| パス | 状態 |
|-----|------|
| `/api/v1/project` | ✅ 使用中 |
| `/api/v1/user_account` | ✅ 使用中 |
| `/api/v1/admin/*` | ✅ 使用中 |
| `/api/v1/dashboard/*` | ✅ 使用中 |

---

## 5. 実装優先度サマリー

### Phase 1: 必須修正（MVP）✅ 完了

| # | カテゴリ | 項目 | 状態 |
|---|---------|-----|------|
| 1 | DB | スナップショット分岐履歴カラム追加 | ✅ 完了 |
| 2 | DB | セッション/ツリー状態カラム追加 | ✅ 完了 |
| 3 | API | ダッシュボード統計API | ✅ 完了 |
| 4 | API | チャットメッセージ履歴取得 | ✅ 完了 |
| 5 | API | スナップショット手動保存・復元 | ✅ 完了 |

### Phase 2: 機能拡充 ✅ 完了

| # | カテゴリ | 項目 | 状態 |
|---|---------|-----|------|
| 1 | API | セッション/ツリー複製機能 | ✅ 完了 |
| 2 | API | 管理機能CRUD（カテゴリ/検証/課題） | ✅ 完了 |
| 3 | API | ユーザー有効化/無効化 | ✅ 完了 |
| 4 | 拡張 | プロジェクトフィールド追加 | ✅ 完了 |
| 5 | 拡張 | 施策フィールド追加 | ✅ 完了 |

### Phase 3: 品質向上 ✅ 完了

| # | カテゴリ | 項目 | 状態 |
|---|---------|-----|------|
| 1 | DB | ロール履歴テーブル追加 | ✅ 完了 |
| 2 | 拡張 | ファイル使用状況追加 | ✅ 完了 |
| 3 | 拡張 | 計算結果サマリー追加 | ✅ 完了 |
| 4 | 拡張 | ユーザー詳細情報追加 | ✅ 完了 |
| 5 | API | パス命名規則統一（v2削除） | ✅ 完了 |

---

## 6. ユースケースカバレッジ（2024年12月28日更新）

分析したユースケース159件に対する現行実装のカバレッジ：

| カテゴリ | ユースケース数 | 実装済み | 部分実装 | 未実装 | カバレッジ% |
|---------|--------------|---------|---------|-------|----------|
| ユーザー管理 | 11 | 11 | 0 | 0 | **100%** |
| プロジェクト管理 | 20 | 20 | 0 | 0 | **100%** |
| 分析マスタ管理 | 25 | 25 | 0 | 0 | **100%** |
| 分析セッション | 24 | 24 | 0 | 0 | **100%** |
| ドライバーツリー | 41 | 41 | 0 | 0 | **100%** |
| ダッシュボード・統計 | 6 | 6 | 0 | 0 | **100%** |
| 横断機能 | 18 | 18 | 0 | 0 | **100%** |
| 複製・エクスポート機能 | 5 | 2 | 3 | 0 | **40%** |
| テンプレート機能 | 5 | 5 | 0 | 0 | **100%** |
| ファイルバージョン管理 | 4 | 4 | 0 | 0 | **100%** |
| **合計** | **159** | **156 (98%)** | **3 (2%)** | **0 (0%)** | **98%** |

### 新規追加ユースケース（2024/12/28 モックアップ分析より）

| カテゴリ | 追加数 | 内容 |
|---------|--------|------|
| ダッシュボード・統計 | 6 | 統計情報、アクティビティ、チャート取得 |
| 横断機能 | 2 | セッション課題別絞り込み、カテゴリ業界絞り込み |
| 複製・エクスポート機能 | 5 | セッション/ツリー複製、レポート出力、エクスポート |
| テンプレート機能 | 5 | テンプレート一覧、絞り込み、プレビュー、作成 |
| ファイルバージョン管理 | 4 | バージョンアップロード、履歴、ダウンロード |

### 部分実装項目（3件）

| ID | ユースケース | 状態 |
|----|-------------|------|
| EX-001 | セッション結果をレポート出力する | API未実装（フロントエンド機能） |
| EX-002 | ツリー計算結果をエクスポートする | API未実装（フロントエンド機能） |
| EX-003 | セッション結果を共有する | API未実装（フロントエンド機能） |

### 前回比較

| 指標 | 前回（2024/12/27） | 今回（2024/12/28） | 改善 |
|-----|-------------------|------------------|------|
| ユースケース総数 | 137 | 159 | **+22件** |
| 実装済み | 137 (100%) | 156 (98%) | +19件 |
| 部分実装 | 0 (0%) | 3 (2%) | +3件（新規追加分） |
| 未実装 | 0 (0%) | 0 (0%) | - |

---

## 7. 実装完了項目一覧

### 7.1 全項目実装完了

すべての項目（137件）が実装完了しました。

### 7.2 新規実装完了項目（2024年12月27日追加）

#### 分析マスタ管理（4件）✅ 完了

- グラフ軸マスタ管理（AGM-001～AGM-004）
  - 作成、更新、削除、課題別一覧

#### 分析セッション（1件）✅ 完了

- AC-003: チャットメッセージ削除

#### 横断機能（5件）✅ 完了

- X-002: ユーザーをAzure OIDで検索 ✅
- X-005: ファイルをMIMEタイプで絞り込む ✅
- X-013/X-014: 更新日時・作成者を記録する ✅
  - DriverTree: created_by追加
  - DriverTreeFile: added_by追加
  - AnalysisFile: added_by追加
- X-015/X-016: アップロード者/追加者を記録する ✅
  - ProjectFileは既にuploaded_by実装済み

#### ドライバーツリー（1件）✅ 完了

- ツリー複製時の施策（ポリシー）の完全な引き継ぎ ✅
  - `duplicate_tree`メソッドで施策（DriverTreePolicy）をコピーするよう実装

### 7.3 部分実装 → 実装完了（0件）

以下の項目はすべて実装完了しています：

- プロジェクト詳細情報の拡張（start_date, end_date, stats） ✅ 実装済み
- ダッシュボード統計機能（stats, activities, charts API） ✅ 実装済み
  - アクティビティログ機能は空レスポンスで準備中（将来データソース接続予定）
- 検索・フィルタ機能の統一 ✅ 実装済み
  - 共通フィルタスキーマ（`app.schemas.common.filters`）
  - PaginationParams、SortParams、DateRangeFilter、DateTimeRangeFilter、ListQueryParams
  - SearchParams、StatusFilter、ActiveFilter、FilterResult
  - PaginatedResponseベースクラス
- エージェントプロンプト・初期メッセージ設定 ✅ 実装済み
  - AnalysisSessionモデルにcustom_system_prompt、initial_messageカラム追加（Line 97-107）
  - セッション作成・更新APIでプロンプト設定可能
  - AnalysisAgentクラスがカスタムプロンプトを使用

### 7.4 追加完了項目（2024年12月27日）

- ダミー数式・チャートマスタ管理 ✅
  - ダミー数式マスタCRUD API（/api/v1/admin/dummy-formula）
  - ダミーチャートマスタCRUD API（/api/v1/admin/dummy-chart）
- ファイルバージョニング機能 ✅
  - モデル拡張（version, parent_file_id, is_latest カラム追加）
  - バージョン履歴API（GET /api/v1/project/{project_id}/file/{file_id}/versions）
  - 新バージョンアップロードAPI（POST /api/v1/project/{project_id}/file/{file_id}/version）

---

## 8. 推奨アクションプラン

### 即時対応不要

Phase 1～3の主要機能はすべて実装完了しました。全ユースケース（137件）の実装が完了し、カバレッジ100%を達成しました。

### 今後の対応（オプション）

1. **アクティビティログ機能のデータソース接続**
   - 優先度: 低
   - 工数: 中
   - 現状: APIエンドポイント実装済み（空レスポンス）、データソース接続は将来対応

---

## 関連ドキュメント

- [API仕様書](./API_SPECIFICATION.md) - 完全なAPI仕様
- [API差異分析](./API_GAP_ANALYSIS.md) - 実装差異詳細
- [ユースケース一覧](./docs/specifications/01-usercases/01-usecases.md) - 159ユースケース
- [ユースケースフロー分析](./docs/specifications/01-usercases/02-usecase-flow-analysis.md) - DB改善提案

---

*本レポートは2024年12月28日時点の分析に基づいています。*
*モックアップ分析により22件のユースケースを追加。159件中156件実装済み（98%）。*

## 更新履歴

| 日付 | 内容 |
|-----|------|
| 2024/12/27 | グラフ軸マスタAPI（AGM-001～004）、チャットメッセージ削除API（AC-003）、監査フィールド追加、MIMEタイプフィルタ（X-005）、Azure OID検索（X-002）を実装 |
| 2024/12/27 | ツリー複製時の施策（ポリシー）コピー機能を実装 |
| 2024/12/27 | プロジェクト統計情報（stats）をプロジェクト詳細APIに追加（member_count, file_count, session_count, tree_count） |
| 2024/12/27 | ダミー数式・チャートマスタCRUD API（/api/v1/admin/dummy-formula、/api/v1/admin/dummy-chart）を実装 |
| 2024/12/27 | Pylanceエラー修正（current_snapshot型、chat_list/step_list修正、chat_repository.delete修正等）|
| 2024/12/27 | ファイルバージョニング機能を実装（version, parent_file_id, is_latest、バージョン履歴API、新バージョンアップロードAPI） |
| 2024/12/27 | 全項目の実装状況確認・更新（ruffチェック通過、未実装項目0件達成） |
| 2024/12/27 | 検索・フィルタ機能の統一（共通スキーマ `app.schemas.common.filters` 追加）、エージェントプロンプト・初期メッセージ設定機能を実装 |
| 2024/12/27 | 実装状況調査完了：全ユースケース（137件）の実装完了を確認、カバレッジ100%達成 |
| 2024/12/28 | モックアップ仕様（03-mockup）との差異分析を実施 |
| 2024/12/28 | ユースケースに22件追加（ダッシュボード6件、横断機能2件、複製・エクスポート5件、テンプレート5件、ファイルバージョン4件） |
| 2024/12/28 | ダッシュボードアクティビティログ機能を実装（RoleHistory, Project, AnalysisSession, DriverTree, ProjectFileからデータ集約） |
| 2024/12/28 | テストファイルをtests/app/に整理、ダッシュボードサービス・APIのテストを追加 |
