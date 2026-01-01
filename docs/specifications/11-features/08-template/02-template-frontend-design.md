# テンプレート フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| templates | テンプレート一覧 | /projects/{id}/templates | テンプレート管理画面 |
| template-select | テンプレート選択 | - | モーダル/ドロワー（tree-new内） |

### 1.2 コンポーネント構成

```text
features/templates/
├── components/
│   ├── TemplateList/
│   │   ├── TemplateList.tsx          # テンプレート一覧表示
│   │   ├── TemplateCard.tsx          # テンプレートカード
│   │   └── TemplateFilters.tsx       # フィルター機能
│   ├── TemplateSelector/
│   │   ├── TemplateSelector.tsx      # テンプレート選択UI（tree-new内で使用）
│   │   ├── TemplatePreview.tsx       # プレビュー表示
│   │   └── CategoryFilter.tsx        # 業種・分析タイプフィルター
│   └── TemplateForm/
│       ├── CreateTemplateModal.tsx   # テンプレート作成モーダル
│       └── TemplateFormFields.tsx    # フォームフィールド
├── hooks/
│   ├── useAnalysisTemplates.ts       # 分析テンプレートフック
│   └── useDriverTreeTemplates.ts     # ツリーテンプレートフック
├── api/
│   └── templateApi.ts                # テンプレートAPI呼び出し
└── types/
    └── template.ts                   # 型定義
```

**テンプレート選択UI（tree-new画面内）**

既存のtree-new画面内のテンプレート選択部分は、`TemplateSelector`コンポーネントを使用してdriver_tree_templateテーブルのデータを表示します。

```text
┌────────────────────────────────────────────────────────┐
│  テンプレートから作成                                    │
├────────────────────────────────────────────────────────┤
│  業種: [すべて] [小売・EC] [製造業] [サービス業] [SaaS]  │
│  分析タイプ: [すべて] [売上分析] [コスト分析] [利益分析] │
├────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 📈       │ │ 🛒       │ │ 🔄       │ │ 🏭       │  │
│  │ 売上分解 │ │ EC売上   │ │ SaaS MRR │ │ 製造コスト│  │
│  │ モデル   │ │ モデル   │ │ 分解     │ │ 構造     │  │
│  │ ノード:8 │ │ ノード:12│ │ ノード:15│ │ ノード:18│  │
│  │ 利用:150+│ │ 利用:80+ │ │ 利用:45+ │ │ 利用:35+ │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                        │
│  ┌──────────┐                                          │
│  │ ➕       │                                          │
│  │ 空の     │                                          │
│  │ ツリー   │                                          │
│  └──────────┘                                          │
└────────────────────────────────────────────────────────┘
```

---

## 2. 画面詳細設計

### 2.1 テンプレート選択画面（tree-new内）

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理 |
|---------|-------------|------------------|-----------|---------|
| 業種フィルター | チップ選択 | GET /driver-tree/template | query: category | - |
| テンプレートカード | カードグリッド | GET /driver-tree/template | templates[] | - |
| テンプレート名 | テキスト | GET /driver-tree/template | templates[].name | - |
| テンプレートアイコン | アイコン | - | - | カテゴリ→アイコン変換 |
| ノード数 | テキスト | GET /driver-tree/template | templates[].nodeCount | "ノード: n" |
| 利用実績 | テキスト | GET /driver-tree/template | templates[].usageCount | "利用実績: n+" |
| 人気バッジ | バッジ | GET /driver-tree/template | templates[].usageCount | >100で表示 |

### 2.2 テンプレート作成モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| テンプレート名 | テキスト | ○ | POST /driver-tree/template | name | 1-255文字 |
| 説明 | テキストエリア | - | POST /driver-tree/template | description | 任意 |
| カテゴリ | セレクト | - | POST /driver-tree/template | category | 業種選択 |
| 公開設定 | トグル | - | POST /driver-tree/template | isPublic | true/false |
| 元ツリー | 非表示 | ○ | POST /driver-tree/template | sourceTreeId | 現在のツリーID |

### 2.3 テンプレート一覧画面

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| テンプレート名 | テキスト | GET /template | templates[].name | - |
| 説明 | テキスト | GET /template | templates[].description | - |
| タイプ | バッジ | GET /template | templates[].templateType | session/tree |
| 公開状態 | アイコン | GET /template | templates[].isPublic | 公開/非公開アイコン |
| 使用回数 | 数値 | GET /template | templates[].usageCount | - |
| 作成者 | テキスト | GET /template | templates[].createdByName | - |
| 作成日時 | 日時 | GET /template | templates[].createdAt | YYYY/MM/DD形式 |
| 削除ボタン | ボタン | DELETE /template/{id} | - | 確認ダイアログ |

---

## 3. 画面項目・APIマッピング

### 3.1 テンプレート一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| カテゴリフィルタ | セレクト | - | `GET /driver-tree/template` | `category` | 業種選択 |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

### 3.2 テンプレート作成

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| テンプレート名 | テキスト | ✓ | `POST /driver-tree/template` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | 任意 |
| カテゴリ | セレクト | - | 同上 | `category` | 業種選択 |
| 公開設定 | トグル | - | 同上 | `isPublic` | true/false |
| 元ツリーID | 非表示 | ✓ | 同上 | `sourceTreeId` | UUID |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| テンプレート一覧ページ表示 | `GET /template` | 初期ロード |
| ツリー作成画面表示 | `GET /driver-tree/template` | テンプレート選択用 |
| カテゴリフィルタ変更 | `GET /driver-tree/template?category=` | 再取得 |
| テンプレート作成ボタン | `POST /driver-tree/template` | モーダル送信時 |
| テンプレート選択 | `POST /driver-tree/tree/import` | テンプレート適用 |
| テンプレート削除 | `DELETE /template/{id}` | 確認後 |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | テンプレートが見つかりませんメッセージ表示 |
| 409 Conflict | 同名のテンプレートが存在しますメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| テンプレートカード | useMemo でフィルタ結果を最適化 |
| キャッシュ | React Query でテンプレート一覧を5分間キャッシュ |
| プレビュー | 遅延ロードでテンプレート詳細を取得 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| TM-001 | テンプレート一覧表示 | `GET /template` | templates, tree-new | 設計済 |
| TM-002 | テンプレート作成（セッションから） | `POST /analysis/template` | session-detail | 設計済 |
| TM-003 | テンプレート作成（ツリーから） | `POST /driver-tree/template` | tree-edit | 設計済 |
| TM-004 | テンプレート適用 | `POST /session`, `POST /tree/import` | session-new, tree-new | 設計済 |
| TM-005 | テンプレート削除 | `DELETE /template/{id}` | templates | 設計済 |

---

## 8. 関連ドキュメント

- **バックエンド設計書**: [01-template-design.md](./01-template-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | TM-FRONTEND-001 |
| 対象ユースケース | TM-001〜TM-005 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `pages/templates/` |
