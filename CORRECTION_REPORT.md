# 修正レポート

モックアップ・ユースケース分析に基づく実装修正計画書

---

## 概要

本レポートは以下の分析結果を統合し、必要な修正項目を優先度別に整理したものです：

1. **API差異分析** (`API_GAP_ANALYSIS.md`) - モックアップ仕様と現行実装の差異
2. **ユースケース分析** (`docs/specifications/01-usercases/`) - 137ユースケースから抽出された要件
3. **DBスキーマ改善提案** - ユースケースフロー分析から特定された設計課題

---

## 1. データベーススキーマ修正（最優先）

### 1.1 高優先度：データ整合性の確保

| # | 修正内容 | 対象テーブル | 理由 |
|---|---------|-------------|------|
| 1 | `parent_snapshot_id` カラム追加 | `analysis_snapshots` | スナップショットの分岐履歴管理のため |
| 2 | `driver_tree_id` FK追加 | `driver_tree_nodes` | ノードの所有ツリー明確化のため |
| 3 | `current_snapshot_id` UUID FK化 | `analysis_sessions` | 現在スナップショットの整合性保証のため |
| 4 | `category_id` FK追加 | `driver_tree_formulas` | カテゴリ-数式関係の明確化のため |

**スキーマ変更例**:

```sql
-- 1. スナップショット分岐履歴
ALTER TABLE analysis_snapshots
ADD COLUMN parent_snapshot_id UUID REFERENCES analysis_snapshots(id);

-- 2. ノードのツリー所有関係
ALTER TABLE driver_tree_nodes
ADD COLUMN driver_tree_id UUID NOT NULL REFERENCES driver_trees(id);

-- 3. 現在スナップショットFK
ALTER TABLE analysis_sessions
ADD CONSTRAINT fk_current_snapshot
FOREIGN KEY (current_snapshot_id) REFERENCES analysis_snapshots(id);

-- 4. 数式のカテゴリ関係
ALTER TABLE driver_tree_formulas
ADD COLUMN category_id UUID REFERENCES driver_tree_categories(id);
```

### 1.2 中優先度：状態管理の改善

| # | 修正内容 | 対象テーブル | 理由 |
|---|---------|-------------|------|
| 1 | `status` カラム追加 | `analysis_sessions` | セッション状態（draft/active/completed）管理 |
| 2 | `status` カラム追加 | `driver_trees` | ツリー状態管理 |
| 3 | `triggered_by_chat_id` FK追加 | `analysis_steps` | チャット-ステップ関係の追跡 |
| 4 | `order_index` UNIQUE制約追加 | `analysis_steps` | ステップ順序の一意性保証 |

**スキーマ変更例**:

```sql
-- セッション状態
ALTER TABLE analysis_sessions
ADD COLUMN status VARCHAR(20) DEFAULT 'draft'
CHECK (status IN ('draft', 'active', 'completed', 'archived'));

-- ツリー状態
ALTER TABLE driver_trees
ADD COLUMN status VARCHAR(20) DEFAULT 'draft'
CHECK (status IN ('draft', 'active', 'completed'));

-- チャット-ステップ関係
ALTER TABLE analysis_steps
ADD COLUMN triggered_by_chat_id UUID REFERENCES analysis_chats(id);

-- ステップ順序一意性
ALTER TABLE analysis_steps
ADD CONSTRAINT uq_step_order UNIQUE (snapshot_id, order_index);
```

### 1.3 低優先度：拡張機能サポート

| # | 修正内容 | 対象テーブル | 理由 |
|---|---------|-------------|------|
| 1 | ロール履歴テーブル追加 | 新規テーブル | 監査証跡の記録 |
| 2 | ファイルバージョニング | `project_files` | ファイル版管理 |
| 3 | テンプレートテーブル追加 | 新規テーブル | ツリーテンプレート管理 |

---

## 2. 新規API実装（機能追加）

### 2.1 高優先度：コア機能

#### 2.1.1 ダッシュボードAPI

```
GET  /api/v1/dashboard/stats        - 統計情報取得
GET  /api/v1/dashboard/activities   - アクティビティログ取得
GET  /api/v1/dashboard/charts       - チャートデータ取得
```

**必要な実装**:
- 統計集計サービスの実装
- アクティビティログモデルとリポジトリ
- 日付範囲フィルタリング機能

#### 2.1.2 チャットメッセージ履歴

```
GET  /api/v1/sessions/{session_id}/messages  - メッセージ履歴取得
```

**必要な実装**:
- メッセージ永続化（現在は準備中状態）
- ページネーション対応
- メッセージタイプ（user/assistant/system）の区別

#### 2.1.3 スナップショット管理

```
POST /api/v1/sessions/{session_id}/snapshots     - 手動スナップショット保存
GET  /api/v1/snapshots/{id}                       - スナップショット詳細取得
POST /api/v1/snapshots/{id}/restore               - スナップショット復元
```

**必要な実装**:
- スナップショット手動保存エンドポイント
- 復元機能（セッション状態のロールバック）
- 分岐履歴の可視化対応

### 2.2 中優先度：ユーティリティ機能

#### 2.2.1 複製機能

```
POST /api/v1/sessions/{id}/duplicate  - セッション複製
POST /api/v1/trees/{id}/duplicate     - ツリー複製
```

**必要な実装**:
- 深いコピー（関連エンティティ含む）
- 名前の自動サフィックス付与
- 複製元への参照（オプション）

#### 2.2.2 管理機能CRUD

```
# カテゴリマスタ
GET    /api/v1/admin/categories
POST   /api/v1/admin/categories
PUT    /api/v1/admin/categories/{id}
DELETE /api/v1/admin/categories/{id}

# 検証マスタ
GET    /api/v1/admin/validations
POST   /api/v1/admin/validations
PUT    /api/v1/admin/validations/{id}
DELETE /api/v1/admin/validations/{id}

# 課題マスタ
GET    /api/v1/admin/issues
POST   /api/v1/admin/issues
PUT    /api/v1/admin/issues/{id}
DELETE /api/v1/admin/issues/{id}
```

**必要な実装**:
- 管理者権限チェック
- 参照整合性の検証（使用中のマスタ削除防止）
- バリデーション強化

#### 2.2.3 ユーザー管理拡張

```
PATCH /api/v1/admin/users/{id}/activate    - ユーザー有効化
PATCH /api/v1/admin/users/{id}/deactivate  - ユーザー無効化
PUT   /api/v1/admin/users/{id}/role        - ロール変更
```

### 2.3 低優先度：品質向上

#### 2.3.1 データ紐付け更新

```
POST /api/v1/trees/{tree_id}/bindings/refresh  - データ再読み込み
```

#### 2.3.2 ロール一覧API

```
GET /api/v1/roles  - システムロール一覧
```

---

## 3. 既存API拡張

### 3.1 プロジェクトAPI拡張

**現行フィールド**:
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "is_active": "boolean"
}
```

**追加が必要なフィールド**:
```json
{
  "start_date": "date",      // プロジェクト開始日
  "end_date": "date",        // プロジェクト終了日
  "stats": {                 // 統計情報
    "member_count": "integer",
    "file_count": "integer",
    "session_count": "integer",
    "tree_count": "integer"
  }
}
```

**修正対象ファイル**:
- `src/app/models/project.py` - モデル拡張
- `src/app/schemas/project.py` - スキーマ拡張
- `src/app/repositories/project.py` - リポジトリ拡張

### 3.2 ファイルAPI拡張

**追加が必要なフィールド**:
```json
{
  "usage": {                 // 使用状況
    "session_count": "integer",
    "tree_count": "integer",
    "sessions": ["session_id"],
    "trees": ["tree_id"]
  }
}
```

### 3.3 施策API拡張

**現行フィールド**:
```json
{
  "id": "uuid",
  "name": "string",
  "value": "number"
}
```

**追加が必要なフィールド**:
```json
{
  "description": "string",       // 施策説明
  "cost": "number",              // コスト
  "duration_months": "integer",  // 実施期間（月）
  "status": "string"             // 状態（planned/in_progress/completed）
}
```

### 3.4 計算結果API拡張

**追加が必要なフィールド**:
```json
{
  "summary": {                   // 要約情報
    "total_nodes": "integer",
    "calculated_nodes": "integer",
    "error_nodes": "integer"
  },
  "policy_effects": [            // 施策効果
    {
      "policy_id": "uuid",
      "original_value": "number",
      "projected_value": "number",
      "difference": "number"
    }
  ]
}
```

### 3.5 ユーザー詳細API拡張

**追加が必要なフィールド**:
```json
{
  "stats": {
    "project_count": "integer",
    "session_count": "integer",
    "last_login_at": "datetime"
  },
  "projects": ["project_summary"],
  "activities": ["activity_log"]
}
```

---

## 4. パス命名規則の統一（オプション）

現行実装とAPI仕様でパス命名規則に差異があります。統一する場合の修正計画：

| 現行パス | 推奨パス（REST規約） | 影響範囲 |
|---------|-------------------|---------|
| `/project` | `/projects` | 中（複数エンドポイント） |
| `/member` | `/members` | 小 |
| `/file` | `/files` | 小 |
| `/analysis/session` | `/sessions` | 中 |
| `/driver-tree/tree` | `/trees` | 中 |
| `/user_account` | `/users` または `/admin/users` | 小 |

**注意**: パス変更は破壊的変更となるため、バージョニング（`/api/v2/`）または移行期間の設定が必要です。

---

## 5. 実装優先度サマリー

### Phase 1: 必須修正（MVP）

| # | カテゴリ | 項目 | 工数目安 |
|---|---------|-----|---------|
| 1 | DB | スナップショット分岐履歴カラム追加 | 小 |
| 2 | DB | セッション/ツリー状態カラム追加 | 小 |
| 3 | API | ダッシュボード統計API | 中 |
| 4 | API | チャットメッセージ履歴取得 | 中 |
| 5 | API | スナップショット手動保存・復元 | 大 |

### Phase 2: 機能拡充

| # | カテゴリ | 項目 | 工数目安 |
|---|---------|-----|---------|
| 1 | API | セッション/ツリー複製機能 | 中 |
| 2 | API | 管理機能CRUD（カテゴリ/検証/課題） | 大 |
| 3 | API | ユーザー有効化/無効化 | 小 |
| 4 | 拡張 | プロジェクトフィールド追加 | 小 |
| 5 | 拡張 | 施策フィールド追加 | 中 |

### Phase 3: 品質向上

| # | カテゴリ | 項目 | 工数目安 |
|---|---------|-----|---------|
| 1 | DB | ロール履歴テーブル追加 | 中 |
| 2 | 拡張 | ファイル使用状況追加 | 小 |
| 3 | 拡張 | 計算結果サマリー追加 | 中 |
| 4 | 拡張 | ユーザー詳細情報追加 | 中 |
| 5 | API | パス命名規則統一（v2） | 大 |

---

## 6. ユースケースカバレッジ

分析したユースケース137件に対する現行実装のカバレッジ：

| カテゴリ | ユースケース数 | 実装済み | 部分実装 | 未実装 |
|---------|--------------|---------|---------|-------|
| ユーザー管理 | 11 | 8 | 2 | 1 |
| プロジェクト管理 | 20 | 16 | 3 | 1 |
| 分析マスタ管理 | 25 | 5 | 5 | 15 |
| 分析セッション | 24 | 14 | 6 | 4 |
| ドライバーツリー | 41 | 30 | 7 | 4 |
| 横断機能 | 16 | 4 | 4 | 8 |
| **合計** | **137** | **77 (56%)** | **27 (20%)** | **33 (24%)** |

---

## 7. 推奨アクションプラン

### 即時対応（1週間以内）

1. DBマイグレーション準備
   - スナップショット分岐履歴カラム追加
   - セッション/ツリー状態カラム追加

2. ダッシュボードAPI基盤実装
   - 統計集計サービス骨格
   - アクティビティログモデル

### 短期対応（2-4週間）

1. スナップショット管理機能実装
2. チャットメッセージ履歴永続化
3. 管理機能CRUD実装

### 中期対応（1-2ヶ月）

1. 複製機能実装
2. フィールド拡張対応
3. ユーザー管理拡張

### 長期対応（要検討）

1. パス命名規則統一（v2 API）
2. ロール履歴・監査ログ機能
3. ファイルバージョニング

---

## 関連ドキュメント

- [API仕様書](./API_SPECIFICATION.md) - 完全なAPI仕様
- [API差異分析](./API_GAP_ANALYSIS.md) - 実装差異詳細
- [ユースケース一覧](./docs/specifications/01-usercases/01-usecases.md) - 137ユースケース
- [ユースケースフロー分析](./docs/specifications/01-usercases/02-usecase-flow-analysis.md) - DB改善提案

---

*本レポートは2024年12月27日時点の分析に基づいています。*
