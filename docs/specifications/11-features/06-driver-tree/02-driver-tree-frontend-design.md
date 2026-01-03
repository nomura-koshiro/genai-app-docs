# ドライバーツリー フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| trees | ドライバーツリー一覧 | /projects/{id}/trees | ツリー一覧表示 |
| tree-new | ツリー作成 | /projects/{id}/trees/new | テンプレート選択・新規作成 |
| tree-edit | ツリー編集 | /projects/{id}/trees/{treeId} | ツリー編集画面 |
| tree-policies | 施策設定 | /projects/{id}/trees/{treeId}/policies | 施策一覧・編集 |
| tree-data-binding | データ紐付け | /projects/{id}/trees/{treeId}/data-binding | データ紐付け設定 |
| tree-results | 計算結果 | /projects/{id}/trees/{treeId}/results | 計算結果・シミュレーション |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | ツリーカード、施策カード、サマリカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `DataTable` | ノード一覧テーブル、計算結果テーブル | 同上 |
| `Badge` | ノードタイプバッジ、ステータスバッジ | 同上 |
| `Button` | 各種操作ボタン | 同上 |
| `Input` | テキスト入力（ツリー名、ノードラベル等） | 同上 |
| `Textarea` | 説明入力 | 同上 |
| `Select` | ノードタイプ選択、データ列選択 | 同上 |
| `Modal` | 施策追加/編集モーダル、確認ダイアログ | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Tabs` | ツリー編集タブナビゲーション | 同上 |
| `Progress` | 計算進捗表示 | 同上 |
| `Skeleton` | ローディング表示 | 同上 |
| `EmptyState` | ツリーなし状態、施策なし状態 | 同上 |

### 1.3 コンポーネント構成

```text
features/driver-tree/
├── api/
│   ├── get-trees.ts              # GET /driver-tree/tree
│   ├── get-tree.ts               # GET /driver-tree/tree/{id}
│   ├── create-tree.ts            # POST /driver-tree/tree
│   ├── update-tree.ts            # PUT /driver-tree/tree/{id}
│   ├── delete-tree.ts            # DELETE /driver-tree/tree/{id}
│   ├── create-node.ts            # POST /driver-tree/tree/{id}/node
│   ├── update-node.ts            # PATCH /driver-tree/node/{id}
│   ├── delete-node.ts            # DELETE /driver-tree/node/{id}
│   ├── create-policy.ts          # POST /driver-tree/node/{id}/policy
│   ├── update-policy.ts          # PATCH /driver-tree/policy/{id}
│   ├── delete-policy.ts          # DELETE /driver-tree/policy/{id}
│   ├── get-tree-data.ts          # GET /driver-tree/tree/{id}/data
│   └── index.ts
├── components/
│   ├── tree-table/
│   │   ├── tree-table.tsx            # ツリー一覧（DataTable使用）
│   │   └── index.ts
│   ├── tree-canvas/
│   │   ├── tree-canvas.tsx           # ツリーキャンバス（React Flow）
│   │   ├── tree-node.tsx             # ノードコンポーネント（Badge使用）
│   │   ├── tree-connection.tsx       # 接続線（SVG）
│   │   ├── tree-toolbar.tsx          # ツールバー（Button使用）
│   │   └── index.ts
│   ├── node-editor/
│   │   ├── node-editor.tsx           # ノード編集パネル（Input, Select使用）
│   │   ├── node-type-selector.tsx    # ノードタイプ選択（Select使用）
│   │   └── index.ts
│   ├── policy-card/
│   │   ├── policy-card.tsx           # 施策カード（Card, Badge使用）
│   │   └── index.ts
│   ├── policy-modal/
│   │   ├── policy-modal.tsx          # 施策追加/編集（Modal, Input使用）
│   │   └── index.ts
│   ├── data-source-selector/
│   │   ├── data-source-selector.tsx  # データソース選択（Select使用）
│   │   └── index.ts
│   ├── node-binding-table/
│   │   ├── node-binding-table.tsx    # ノード紐付けテーブル（DataTable使用）
│   │   └── index.ts
│   ├── results-summary/
│   │   ├── results-summary.tsx       # サマリカード群（Card使用）
│   │   └── index.ts
│   ├── node-calculation-table/
│   │   ├── node-calculation-table.tsx # 計算結果テーブル（DataTable使用）
│   │   └── index.ts
│   ├── policy-effect-chart/
│   │   ├── policy-effect-chart.tsx   # 施策効果チャート
│   │   └── index.ts
│   ├── template-grid/
│   │   ├── template-grid.tsx         # テンプレートグリッド
│   │   ├── template-card.tsx         # テンプレートカード（Card, Badge使用）
│   │   ├── template-preview.tsx      # テンプレートプレビュー
│   │   └── index.ts
│   └── index.ts
├── routes/
│   ├── tree-list/
│   │   ├── tree-list.tsx             # ツリー一覧コンテナ
│   │   ├── tree-list.hook.ts         # ツリー一覧用hook
│   │   └── index.ts
│   ├── tree-new/
│   │   ├── tree-new.tsx              # ツリー作成コンテナ
│   │   ├── tree-new.hook.ts          # ツリー作成用hook
│   │   └── index.ts
│   ├── tree-edit/
│   │   ├── tree-edit.tsx             # ツリー編集コンテナ
│   │   ├── tree-edit.hook.ts         # ツリー編集用hook
│   │   └── index.ts
│   ├── tree-policies/
│   │   ├── tree-policies.tsx         # 施策設定コンテナ
│   │   ├── tree-policies.hook.ts     # 施策設定用hook
│   │   └── index.ts
│   ├── tree-data-binding/
│   │   ├── tree-data-binding.tsx     # データ紐付けコンテナ
│   │   ├── tree-data-binding.hook.ts # データ紐付け用hook
│   │   └── index.ts
│   └── tree-results/
│       ├── tree-results.tsx          # 計算結果コンテナ
│       ├── tree-results.hook.ts      # 計算結果用hook
│       └── index.ts
├── types/
│   ├── api.ts                    # API入出力の型
│   ├── domain.ts                 # ドメインモデル（Tree, Node, Policy等）
│   └── index.ts
└── index.ts

app/projects/[id]/trees/
├── page.tsx               # ツリー一覧ページ → TreeList
├── new/
│   └── page.tsx           # ツリー作成ページ → TreeNew
└── [treeId]/
    ├── page.tsx           # ツリー編集ページ → TreeEdit
    ├── policies/
    │   └── page.tsx       # 施策設定ページ → TreePolicies
    ├── data-binding/
    │   └── page.tsx       # データ紐付けページ → TreeDataBinding
    └── results/
        └── page.tsx       # 計算結果ページ → TreeResults
```

---

## 2. 画面詳細設計

### 2.1 ドライバーツリー一覧画面（trees）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ツリー名 | テキスト（リンク） | GET /driver-tree/tree | trees[].name | - |
| 数式マスタ | テキスト | GET /driver-tree/tree | trees[].formulaName | formulaId→名前解決 |
| ノード数 | 数値 | GET /driver-tree/tree | trees[].nodeCount | - |
| 施策数 | 数値 | GET /driver-tree/tree | trees[].policyCount | - |
| 更新日時 | 日時 | GET /driver-tree/tree | trees[].updatedAt | ISO8601→YYYY/MM/DD HH:mm |
| 編集ボタン | ボタン | - | - | tree-edit画面へ遷移 |
| 複製ボタン | ボタン | POST /driver-tree/tree/{id}/duplicate | - | 確認ダイアログ後実行 |
| 新規作成ボタン | ボタン | - | - | tree-new画面へ遷移 |

### 2.2 ツリー作成画面（tree-new）

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| 業種フィルター | チップ選択 | - | GET /driver-tree/category | （クエリ用） | - |
| 分析タイプフィルター | チップ選択 | - | GET /driver-tree/category | （クエリ用） | - |
| テンプレートカード | 選択カード | - | GET /driver-tree/category | - | - |
| テンプレート人気バッジ | バッジ | - | - | - | 人気テンプレートに表示 |
| テンプレート利用実績 | テキスト | - | - | - | "利用実績: n+" 形式 |
| ツリー名 | テキスト入力 | ○ | POST /driver-tree/tree | name | 1-255文字 |
| 説明 | テキストエリア | - | POST /driver-tree/tree | description | 任意 |
| 選択中のテンプレート | 表示 | - | - | - | テンプレート名とアイコン |
| 構造プレビュー | ツリービュー | - | - | - | テンプレートのノード構造 |
| キャンセルボタン | ボタン | - | - | - | ツリー一覧に戻る |
| 作成して編集ボタン | ボタン | - | POST /driver-tree/tree + POST /import | - | - |

### 2.3 ツリー編集画面（tree-edit）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集（アクティブ） |
| 施策設定 | tree-policies | 施策の追加・編集 |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け |
| 計算結果 | tree-results | 計算結果とシミュレーション |

#### 画面項目

| 画面項目 | 入力/表示形式 | APIエンドポイント | フィールド | 変換処理/バリデーション |
|---------|-------------|------------------|-----------|----------------------|
| ツリー名 | 表示 | GET /driver-tree/tree/{id} | tree.name | - |
| ツールバー（ノード追加） | ボタン | POST /driver-tree/tree/{id}/node | label, nodeType, positionX, positionY | - |
| ツールバー（リレーション追加） | ボタン | - | - | リレーション作成モード |
| ツールバー（整列） | ボタン | - | - | ノード自動配置 |
| ツールバー（ズームイン） | ボタン | - | - | キャンバス拡大 |
| ツールバー（ズームアウト） | ボタン | - | - | キャンバス縮小 |
| ノード（ビジュアル） | キャンバス | GET /driver-tree/tree/{id} | tree.nodes[] | position_x/y→座標 |
| 接続線 | SVG | GET /driver-tree/tree/{id} | tree.relationships[] | 親子座標から算出 |
| ノードラベル | テキスト入力 | PATCH /driver-tree/node/{id} | label | 1-255文字 |
| ノードタイプ | セレクト | PATCH /driver-tree/node/{id} | nodeType | driver/kpi/metric |
| データフレーム紐付け | セレクト | PATCH /driver-tree/node/{id} | dataFrameId | - |
| 保存ボタン | ボタン | PATCH /driver-tree/node/{id} | - | - |
| データ取込ボタン | ボタン | - | - | tree-data-binding画面へ |

### 2.4 施策設定画面（tree-policies）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集 |
| 施策設定 | tree-policies | 施策の追加・編集（アクティブ） |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け |
| 計算結果 | tree-results | 計算結果とシミュレーション |

#### 画面項目

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理/バリデーション |
|---------|-------------|------------------|-----------|----------------------|
| 施策カード一覧 | カードリスト | GET /driver-tree/tree/{id}/policy | policies[] | - |
| 施策アイコン | アイコン | - | - | 施策タイプに応じた絵文字 |
| 施策名 | テキスト | GET/PATCH | policies[].label | - |
| 対象ノード | テキスト | GET | policies[].nodeLabel | nodeId→ラベル解決 |
| 影響値 | 数値+% | GET/PATCH | policies[].value | 正負で色分け |
| コスト | 通貨表示 | GET/PATCH | policies[].cost | ¥フォーマット |
| 期間 | テキスト | GET/PATCH | policies[].durationMonths | n + "ヶ月" |
| ステータス | バッジ | GET/PATCH | policies[].status | planned/in_progress/completed |
| 編集ボタン | ボタン | - | - | モーダル表示 |
| 削除ボタン | ボタン | DELETE /driver-tree/node/{id}/policy/{id} | - | 確認ダイアログ |
| 新規施策ボタン | ボタン | POST /driver-tree/node/{id}/policy | name, value | モーダルフォーム |

#### 施策追加モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| 施策名 | テキスト | ○ | `POST /driver-tree/node/{id}/policy` | name | 1-255文字 |
| 対象ノード | セレクト | ○ | 同上 | nodeId（パス） | ノード一覧から選択 |
| 影響値 | 数値 | ○ | 同上 | value | 数値（正負可） |
| コスト | 数値 | - | 同上 | cost | 正の数値 |
| 実施期間 | セレクト | - | 同上 | durationMonths | 1/3/6/12 |
| 説明 | テキストエリア | - | 同上 | description | 任意 |

### 2.5 データ紐付け画面（tree-data-binding）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集 |
| 施策設定 | tree-policies | 施策の追加・編集 |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け（アクティブ） |
| 計算結果 | tree-results | 計算結果とシミュレーション |

#### 画面項目

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理/バリデーション |
|---------|-------------|------------------|-----------|----------------------|
| ファイル選択 | セレクト | GET /driver-tree/file | files[] | - |
| シート選択 | セレクト | GET /driver-tree/file | files[].sheets[] | - |
| 期間選択 | セレクト | - | - | フロントエンドフィルター |
| ノード一覧テーブル | テーブル | GET /driver-tree/tree/{id} | tree.nodes[] | - |
| ノード名 | テキスト | - | nodes[].label | 階層インデント |
| タイプ | バッジ | - | nodes[].nodeType | root/計算/データ/未設定 |
| データ列 | セレクト | GET /driver-tree/sheet | columns[] | シートのカラム一覧 |
| 集計方法 | セレクト | PATCH | - | 合計/平均/最新 |
| 現在値 | 数値 | GET /driver-tree/tree/{id}/data | - | 計算結果表示 |
| ステータス | バッジ | - | - | 紐付済/計算済/未紐付 |
| データ更新ボタン | ボタン | POST /sheet/{id}/refresh | - | - |
| 保存ボタン | ボタン | PATCH /driver-tree/file/{id}/sheet/{id}/column | columns[] | - |

### 2.6 計算結果画面（tree-results）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集 |
| 施策設定 | tree-policies | 施策の追加・編集 |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け |
| 計算結果 | tree-results | 計算結果とシミュレーション（アクティブ） |

#### 画面項目

| 画面項目 | 表示形式 | APIエンドポイント | フィールド | 変換処理 |
|---------|---------|------------------|-----------|---------|
| 現在の売上高 | サマリカード | GET /driver-tree/tree/{id}/data | calculatedDataList[0] | ルートノード値 |
| 施策適用後 | サマリカード | GET /driver-tree/tree/{id}/data | （計算値） | シミュレーション結果 |
| 増加額 | サマリカード | - | - | 施策後 - 現在 |
| 施策コスト合計 | サマリカード | GET /driver-tree/tree/{id}/policy | sum(policies[].cost) | ¥フォーマット |
| ノード別計算結果テーブル | テーブル | GET /driver-tree/tree/{id}/data | calculatedDataList[] | - |
| 施策効果比較 | 棒グラフ | GET /driver-tree/tree/{id}/policy | policies[] + 計算 | ROI算出 |
| エクスポートボタン | ボタン | GET /driver-tree/tree/{id}/output | - | ファイルダウンロード |
| 再計算ボタン | ボタン | GET /driver-tree/tree/{id}/data | - | 最新データで再計算 |

---

## 3. 画面項目・APIマッピング

### 3.1 ツリー一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| スキップ | 数値 | - | `GET /driver-tree/tree` | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

### 3.2 ツリー作成

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ツリー名 | テキスト | ✓ | `POST /driver-tree/tree` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | 任意 |
| テンプレートID | 非表示 | - | `POST /driver-tree/tree/import` | `templateId` | UUID |

### 3.3 ノード操作

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ノードラベル | テキスト | ✓ | `POST /driver-tree/tree/{id}/node` | `label` | 1-255文字 |
| ノードタイプ | セレクト | ✓ | 同上 | `nodeType` | driver/kpi/metric |
| X座標 | 数値 | ✓ | 同上 | `positionX` | 0以上 |
| Y座標 | 数値 | ✓ | 同上 | `positionY` | 0以上 |

### 3.4 施策操作

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 施策名 | テキスト | ✓ | `POST /driver-tree/node/{id}/policy` | `name` | 1-255文字 |
| 影響値 | 数値 | ✓ | 同上 | `value` | 数値（正負可） |
| コスト | 数値 | - | 同上 | `cost` | 正の数値 |
| 実施期間 | セレクト | - | 同上 | `durationMonths` | 1/3/6/12 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| ツリー一覧ページ表示 | `GET /driver-tree/tree` | 初期ロード |
| テンプレート選択画面表示 | `GET /driver-tree/category` | カテゴリ・テンプレート取得 |
| ツリー作成ボタン | `POST /driver-tree/tree` | - |
| テンプレート適用 | `POST /driver-tree/tree/import` | - |
| ツリー編集画面表示 | `GET /driver-tree/tree/{id}` | ノード・リレーション取得 |
| ノード追加 | `POST /driver-tree/tree/{id}/node` | - |
| ノード更新 | `PATCH /driver-tree/node/{id}` | - |
| ノード削除 | `DELETE /driver-tree/node/{id}` | 確認後 |
| リレーション作成 | `POST /driver-tree/tree/{id}/relationship` | - |
| 施策追加 | `POST /driver-tree/node/{id}/policy` | モーダル送信時 |
| 施策更新 | `PATCH /driver-tree/policy/{id}` | - |
| 施策削除 | `DELETE /driver-tree/policy/{id}` | 確認後 |
| データ紐付け保存 | `PATCH /driver-tree/file/{id}/sheet/{id}/column` | - |
| 計算結果取得 | `GET /driver-tree/tree/{id}/data` | 結果画面表示時 |
| エクスポート | `GET /driver-tree/tree/{id}/output` | ダウンロード |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | ツリーが見つかりませんメッセージ表示 |
| 409 Conflict | 循環参照が検出されましたメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| 計算エラー | "計算中にエラーが発生しました"メッセージ表示 |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| ツリーキャンバス | React Flow でノード描画を最適化 |
| ノード移動 | デバウンスで座標更新API呼び出しを最適化 |
| 計算結果 | useMemo で計算表示を最適化 |
| キャッシュ | React Query でツリーデータを5分間キャッシュ |
| データ紐付け | 遅延ロードでシート一覧を効率的に取得 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| DTC-001 | ツリー一覧を取得する | `GET /driver-tree/tree` | trees | 実装済 |
| DTC-002 | ツリーを作成する | `POST /driver-tree/tree` | tree-new | 実装済 |
| DTC-003 | ツリー情報を更新する | `PUT /driver-tree/tree/{id}` | tree-edit | 実装済 |
| DTC-004 | ツリーを削除する | `DELETE /driver-tree/tree/{id}` | trees | 実装済 |
| DTN-001 | ノードを追加する | `POST /driver-tree/tree/{id}/node` | tree-edit | 実装済 |
| DTN-002 | ノードを更新する | `PATCH /driver-tree/node/{id}` | tree-edit | 実装済 |
| DTN-003 | ノードを削除する | `DELETE /driver-tree/node/{id}` | tree-edit | 実装済 |
| DTR-001 | リレーションを作成する | `POST /driver-tree/tree/{id}/relationship` | tree-edit | 実装済 |
| DTP-001 | 施策を追加する | `POST /driver-tree/tree/{id}/policy` | tree-policies | 実装済 |
| DTP-002 | 施策を更新する | `PATCH /driver-tree/policy/{id}` | tree-policies | 実装済 |
| DTP-003 | 施策を削除する | `DELETE /driver-tree/policy/{id}` | tree-policies | 実装済 |
| DTD-001 | データを紐付ける | `PATCH /driver-tree/file/{id}/sheet/{id}/column` | tree-data-binding | 実装済 |
| DTD-002 | 計算結果を取得する | `GET /driver-tree/tree/{id}/data` | tree-results | 実装済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| TreeTable | Default | ツリー一覧テーブル表示 | 通常、空、ローディング |
| TreeCanvas | Default | ツリーキャンバス表示 | 通常、ノードあり、空、編集中 |
| TreeNode | Driver | ツリーノード表示 | ドライバー、KPI、メトリクス、選択済み |
| NodeEditor | Default | ノード編集エディタ | 通常、編集中、エラー |
| PolicyCard | Default | 施策カード表示 | 通常、計画中、進行中、完了 |
| PolicyModal | Create | 施策モーダル | 作成、編集、送信中 |
| DataSourceSelector | Default | データソース選択 | 通常、選択済み |
| NodeBindingTable | Default | ノードバインディングテーブル | 通常、バインド済み、未バインド |
| ResultsSummary | Default | 結果サマリー表示 | 通常、ローディング、施策あり |
| TemplateGrid | Default | テンプレートグリッド表示 | 通常、フィルタあり、ローディング |

### 8.2 ストーリー実装例

```tsx
// features/driver-tree/components/tree-canvas/tree-canvas.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { TreeCanvas } from "./tree-canvas";
import type { TreeNode, TreeRelationship } from "../../types";

const mockNodes: TreeNode[] = [
  { id: "1", label: "売上高", nodeType: "root", positionX: 400, positionY: 50 },
  { id: "2", label: "客数", nodeType: "driver", positionX: 200, positionY: 150 },
  { id: "3", label: "客単価", nodeType: "driver", positionX: 600, positionY: 150 },
  { id: "4", label: "新規客数", nodeType: "kpi", positionX: 100, positionY: 250 },
  { id: "5", label: "リピート客数", nodeType: "kpi", positionX: 300, positionY: 250 },
];

const mockRelationships: TreeRelationship[] = [
  { id: "r1", parentNodeId: "1", childNodeId: "2" },
  { id: "r2", parentNodeId: "1", childNodeId: "3" },
  { id: "r3", parentNodeId: "2", childNodeId: "4" },
  { id: "r4", parentNodeId: "2", childNodeId: "5" },
];

const meta = {
  title: "features/driver-tree/components/tree-canvas",
  component: TreeCanvas,
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: "ドライバーツリーキャンバスコンポーネント。ノードとリレーションを描画。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onNodeClick: fn(),
    onNodeMove: fn(),
    onNodeAdd: fn(),
    onRelationshipAdd: fn(),
  },
} satisfies Meta<typeof TreeCanvas>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    nodes: mockNodes,
    relationships: mockRelationships,
  },
};

export const WithNodes: Story = {
  args: {
    nodes: mockNodes,
    relationships: mockRelationships,
    selectedNodeId: "2",
  },
};

export const Empty: Story = {
  args: {
    nodes: [],
    relationships: [],
  },
};

export const Editing: Story = {
  args: {
    nodes: mockNodes,
    relationships: mockRelationships,
    isEditing: true,
  },
};
```

```tsx
// features/driver-tree/components/policy-card/policy-card.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { PolicyCard } from "./policy-card";
import type { Policy } from "../../types";

const basePolicy: Policy = {
  id: "1",
  name: "新規顧客獲得キャンペーン",
  nodeLabel: "新規客数",
  value: 15,
  cost: 500000,
  durationMonths: 3,
  status: "planned",
};

const meta = {
  title: "features/driver-tree/components/policy-card",
  component: PolicyCard,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "施策カードコンポーネント。施策の詳細を表示。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onEdit: fn(),
    onDelete: fn(),
  },
} satisfies Meta<typeof PolicyCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    policy: basePolicy,
  },
};

export const Planned: Story = {
  args: {
    policy: { ...basePolicy, status: "planned" },
  },
};

export const InProgress: Story = {
  args: {
    policy: { ...basePolicy, status: "in_progress" },
  },
};

export const Completed: Story = {
  args: {
    policy: { ...basePolicy, status: "completed" },
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | ツリー表示、ノード編集、施策カード |
| ユーティリティ | ユニットテスト | 90%以上 | hooks, utils, 計算ロジック |
| API連携 | 統合テスト | 70%以上 | API呼び出し、状態管理、エラーハンドリング |
| E2E | E2Eテスト | 主要フロー100% | ツリー作成、ノード操作、施策管理 |

### 9.2 ユニットテスト例

```typescript
// features/driver-tree/hooks/__tests__/use-tree-calculation.test.ts
import { renderHook } from "@testing-library/react";
import { useTreeCalculation } from "../use-tree-calculation";

describe("useTreeCalculation", () => {
  it("ノードの値を正しく計算する", () => {
    const nodes = [
      { id: "1", label: "売上高", nodeType: "root", value: null },
      { id: "2", label: "客数", nodeType: "driver", value: 1000 },
      { id: "3", label: "客単価", nodeType: "driver", value: 500 },
    ];
    const relationships = [
      { parentNodeId: "1", childNodeId: "2", operator: "*" },
      { parentNodeId: "1", childNodeId: "3", operator: "*" },
    ];

    const { result } = renderHook(() =>
      useTreeCalculation({ nodes, relationships })
    );

    expect(result.current.calculatedValues["1"]).toBe(500000);
  });

  it("施策の影響を計算に反映する", () => {
    const nodes = [
      { id: "1", label: "売上高", nodeType: "root", value: null },
      { id: "2", label: "客数", nodeType: "driver", value: 1000 },
    ];
    const relationships = [{ parentNodeId: "1", childNodeId: "2" }];
    const policies = [{ nodeId: "2", value: 10 }]; // 10%増加

    const { result } = renderHook(() =>
      useTreeCalculation({ nodes, relationships, policies })
    );

    expect(result.current.calculatedValues["2"]).toBe(1100);
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
// features/driver-tree/components/policy-card/__tests__/policy-card.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { PolicyCard } from "../policy-card";
import type { Policy } from "../../../types";

const mockPolicy: Policy = {
  id: "1",
  name: "テスト施策",
  nodeLabel: "客数",
  value: 10,
  cost: 100000,
  durationMonths: 3,
  status: "planned",
};

describe("PolicyCard", () => {
  it("施策情報を正しく表示する", () => {
    render(<PolicyCard policy={mockPolicy} />);

    expect(screen.getByText("テスト施策")).toBeInTheDocument();
    expect(screen.getByText("客数")).toBeInTheDocument();
    expect(screen.getByText("+10%")).toBeInTheDocument();
    expect(screen.getByText("¥100,000")).toBeInTheDocument();
  });

  it("編集ボタンクリックでonEditが呼ばれる", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(<PolicyCard policy={mockPolicy} onEdit={onEdit} />);

    await user.click(screen.getByRole("button", { name: /編集/i }));
    expect(onEdit).toHaveBeenCalledWith(mockPolicy.id);
  });

  it("ステータスに応じたバッジを表示", () => {
    render(<PolicyCard policy={{ ...mockPolicy, status: "in_progress" }} />);

    expect(screen.getByText("進行中")).toBeInTheDocument();
  });

  it("負の影響値はマイナス表示", () => {
    render(<PolicyCard policy={{ ...mockPolicy, value: -5 }} />);

    expect(screen.getByText("-5%")).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
// e2e/driver-tree.spec.ts
import { test, expect } from "@playwright/test";

test.describe("ドライバーツリー", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects/1/trees");
  });

  test("ツリー一覧が表示される", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "ドライバーツリー" })
    ).toBeVisible();
    await expect(page.getByTestId("tree-table")).toBeVisible();
  });

  test("新規ツリーを作成できる", async ({ page }) => {
    await page.getByRole("button", { name: "新規作成" }).click();

    // テンプレート選択
    await page.getByTestId("template-card-sales").click();

    // ツリー情報入力
    await page.getByLabel("ツリー名").fill("E2Eテストツリー");
    await page.getByRole("button", { name: "作成して編集" }).click();

    await expect(page.getByText("ツリーを作成しました")).toBeVisible();
    await expect(page.getByTestId("tree-canvas")).toBeVisible();
  });

  test("ノードを追加・編集できる", async ({ page }) => {
    await page.getByTestId("tree-row").first().click();

    // ノード追加
    await page.getByRole("button", { name: "ノード追加" }).click();
    await page.getByTestId("tree-canvas").click({ position: { x: 300, y: 200 } });

    // ノード編集
    await page.getByLabel("ラベル").fill("新規ノード");
    await page.getByLabel("タイプ").selectOption("kpi");
    await page.getByRole("button", { name: "保存" }).click();

    await expect(page.getByText("新規ノード")).toBeVisible();
  });

  test("施策を追加できる", async ({ page }) => {
    await page.getByTestId("tree-row").first().click();
    await page.getByRole("tab", { name: "施策設定" }).click();

    await page.getByRole("button", { name: "施策追加" }).click();
    await page.getByLabel("施策名").fill("テスト施策");
    await page.getByLabel("対象ノード").selectOption("客数");
    await page.getByLabel("影響値").fill("10");
    await page.getByRole("button", { name: "追加" }).click();

    await expect(page.getByText("施策を追加しました")).toBeVisible();
    await expect(page.getByText("テスト施策")).toBeVisible();
  });

  test("計算結果を表示できる", async ({ page }) => {
    await page.getByTestId("tree-row").first().click();
    await page.getByRole("tab", { name: "計算結果" }).click();

    await expect(page.getByTestId("results-summary")).toBeVisible();
    await expect(page.getByTestId("calculation-table")).toBeVisible();
  });
});
```

### 9.5 モックデータ

```typescript
// features/driver-tree/__mocks__/handlers.ts
import { http, HttpResponse } from "msw";

export const driverTreeHandlers = [
  http.get("/api/v1/driver-tree/tree", () => {
    return HttpResponse.json({
      trees: [
        {
          id: "1",
          name: "売上分析ツリー",
          formulaName: "乗算式",
          nodeCount: 5,
          policyCount: 3,
          updatedAt: "2024-01-15T10:30:00Z",
        },
      ],
      total: 1,
    });
  }),

  http.get("/api/v1/driver-tree/tree/:id", ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: "売上分析ツリー",
      nodes: [
        { id: "n1", label: "売上高", nodeType: "root", positionX: 400, positionY: 50 },
        { id: "n2", label: "客数", nodeType: "driver", positionX: 200, positionY: 150 },
        { id: "n3", label: "客単価", nodeType: "driver", positionX: 600, positionY: 150 },
      ],
      relationships: [
        { id: "r1", parentNodeId: "n1", childNodeId: "n2" },
        { id: "r2", parentNodeId: "n1", childNodeId: "n3" },
      ],
    });
  }),

  http.post("/api/v1/driver-tree/node/:id/policy", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: "new-policy",
      ...body,
      status: "planned",
      createdAt: new Date().toISOString(),
    });
  }),

  http.get("/api/v1/driver-tree/tree/:id/data", () => {
    return HttpResponse.json({
      calculatedDataList: [
        { nodeId: "n1", value: 500000, label: "売上高" },
        { nodeId: "n2", value: 1000, label: "客数" },
        { nodeId: "n3", value: 500, label: "客単価" },
      ],
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-driver-tree-design.md](./01-driver-tree-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **モックアップ**: [../../03-mockup/pages/trees.js](../../03-mockup/pages/trees.js)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | DT-FRONTEND-001 |
| 対象ユースケース | DTC-001〜DTC-007, DTN-001〜DTN-008, DTR-001〜DTR-006, DTP-001〜DTP-006 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/projects/[id]/trees/` |
