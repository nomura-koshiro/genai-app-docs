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

### 1.2 コンポーネント構成

```text
features/driver-tree/
├── components/
│   ├── TreeList/
│   │   ├── TreeList.tsx
│   │   └── TreeListItem.tsx
│   ├── TreeCanvas/
│   │   ├── TreeCanvas.tsx
│   │   ├── TreeNode.tsx
│   │   ├── TreeConnection.tsx
│   │   └── TreeToolbar.tsx
│   ├── NodeEditor/
│   │   ├── NodeEditor.tsx
│   │   └── NodeTypeSelector.tsx
│   ├── PolicyEditor/
│   │   ├── PolicyList.tsx
│   │   ├── PolicyCard.tsx
│   │   └── PolicyModal.tsx
│   ├── DataBinding/
│   │   ├── DataSourceSelector.tsx
│   │   ├── NodeBindingTable.tsx
│   │   └── ColumnRoleSelector.tsx
│   ├── Results/
│   │   ├── ResultsSummary.tsx
│   │   ├── NodeCalculationTable.tsx
│   │   └── PolicyEffectChart.tsx
│   └── TemplateSelector/
│       ├── TemplateGrid.tsx
│       ├── TemplateCard.tsx
│       └── TemplatePreview.tsx
├── hooks/
│   ├── useDriverTree.ts
│   ├── useDriverTreeNodes.ts
│   ├── useDriverTreePolicies.ts
│   ├── useDriverTreeFiles.ts
│   └── useTreeCalculation.ts
├── api/
│   ├── driverTreeApi.ts
│   ├── driverTreeNodeApi.ts
│   └── driverTreeFileApi.ts
└── types/
    └── driverTree.ts
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

| 画面項目 | 入力形式 | 必須 | リクエストフィールド | バリデーション |
|---------|---------|------|---------------------|---------------|
| 施策名 | テキスト | ○ | name | 1-255文字 |
| 対象ノード | セレクト | ○ | nodeId（パス） | ノード一覧から選択 |
| 影響値 | 数値 | ○ | value | 数値（正負可） |
| コスト | 数値 | - | cost | 正の数値 |
| 実施期間 | セレクト | - | durationMonths | 1/3/6/12 |
| 説明 | テキストエリア | - | description | 任意 |

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

## 8. 関連ドキュメント

- **バックエンド設計書**: [01-driver-tree-design.md](./01-driver-tree-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **モックアップ**: [../../03-mockup/pages/trees.js](../../03-mockup/pages/trees.js)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | DT-FRONTEND-001 |
| 対象ユースケース | DTC-001〜DTC-007, DTN-001〜DTN-008, DTR-001〜DTR-006, DTP-001〜DTP-006 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `pages/projects/[id]/trees/` |
