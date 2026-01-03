# ファイル管理・バージョン管理 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| files | ファイル一覧 | /projects/{id}/files | プロジェクト全体のファイル一覧 |
| upload | ファイルアップロード | /projects/{id}/files/upload | 新規ファイルアップロード |
| file-versions | バージョン履歴 | /projects/{id}/files/{fileId}/versions | ファイルのバージョン一覧・操作 |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | ファイルカード、バージョンカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `DataTable` | ファイル一覧テーブル | 同上 |
| `Pagination` | ファイル一覧ページネーション | 同上 |
| `Badge` | ファイルタイプバッジ、現在バージョンバッジ | 同上 |
| `Button` | ダウンロード、アップロード、復元ボタン | 同上 |
| `Input` | 検索入力、コメント入力 | 同上 |
| `Select` | ファイルタイプフィルタ、バージョン選択 | 同上 |
| `Modal` | バージョンアップロードモーダル、比較モーダル | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Progress` | アップロード進捗表示 | 同上 |
| `FileUpload` | ドラッグ&ドロップエリア | 同上 |
| `Skeleton` | ローディング表示 | 同上 |
| `EmptyState` | ファイルなし状態 | 同上 |

### 1.3 コンポーネント構成

#### コンポーネント階層

```text
features/file-management/
├── api/
│   ├── get-files.ts                  # GET /project/{id}/files
│   ├── get-file.ts                   # GET /file/{id}
│   ├── upload-file.ts                # POST /project/{id}/files
│   ├── get-versions.ts               # GET /file/{id}/version
│   ├── upload-version.ts             # POST /file/{id}/version
│   ├── restore-version.ts            # POST /version/{id}/restore
│   ├── compare-versions.ts           # GET /file/{id}/version/compare
│   ├── download-version.ts           # GET /file/{id}/version/{versionId}
│   └── index.ts
├── components/
│   ├── file-table/
│   │   ├── file-table.tsx            # ファイル一覧テーブル（DataTable使用）
│   │   └── index.ts
│   ├── file-search-bar/
│   │   ├── file-search-bar.tsx       # 検索・フィルタバー（Input使用）
│   │   └── index.ts
│   ├── file-type-filter/
│   │   ├── file-type-filter.tsx      # ファイルタイプフィルタ（Select使用）
│   │   └── index.ts
│   ├── drop-zone/
│   │   ├── drop-zone.tsx             # ドラッグ&ドロップエリア（FileUpload使用）
│   │   └── index.ts
│   ├── upload-progress/
│   │   ├── upload-progress.tsx       # アップロード進捗（Progress使用）
│   │   └── index.ts
│   ├── version-list/
│   │   ├── version-list.tsx          # バージョン一覧（Card使用）
│   │   ├── version-item.tsx          # バージョン項目（Card, Badge使用）
│   │   ├── version-timeline.tsx      # タイムライン表示
│   │   └── index.ts
│   ├── version-upload-modal/
│   │   ├── version-upload-modal.tsx  # バージョンアップロードモーダル（Modal使用）
│   │   ├── version-comment-input.tsx # コメント入力（Input使用）
│   │   └── index.ts
│   ├── version-compare-modal/
│   │   ├── version-compare-modal.tsx # 比較モーダル（Modal使用）
│   │   ├── version-selector.tsx      # バージョン選択（Select使用）
│   │   ├── comparison-result.tsx     # 比較結果表示（Card使用）
│   │   └── index.ts
│   ├── download-button/
│   │   ├── download-button.tsx       # ダウンロードボタン（Button使用）
│   │   └── index.ts
│   ├── restore-button/
│   │   ├── restore-button.tsx        # 復元ボタン（Button使用）
│   │   └── index.ts
│   └── index.ts
├── routes/
│   ├── file-list/
│   │   ├── file-list.tsx             # ファイル一覧コンテナ
│   │   ├── file-list.hook.ts         # ファイル一覧用hook
│   │   └── index.ts
│   ├── file-upload/
│   │   ├── file-upload.tsx           # アップロードコンテナ
│   │   ├── file-upload.hook.ts       # アップロード用hook
│   │   └── index.ts
│   └── file-versions/
│       ├── file-versions.tsx         # バージョン履歴コンテナ
│       ├── file-versions.hook.ts     # バージョン履歴用hook
│       └── index.ts
├── types/
│   ├── api.ts                        # API入出力の型
│   ├── domain.ts                     # ドメインモデル（File, Version等）
│   └── index.ts
└── index.ts

app/projects/[id]/files/
├── page.tsx                          # ファイル一覧ページ → FileList
├── upload/
│   └── page.tsx                      # アップロードページ → FileUpload
└── [fileId]/
    └── versions/
        └── page.tsx                  # バージョン履歴ページ → FileVersions
```

#### 画面遷移フロー

```text
[ファイル一覧 (files)]
    │
    ├─→ [ファイルアップロード (upload)]
    │       │
    │       └─→ アップロード完了 → [ファイル一覧]
    │
    └─→ ファイル名クリック → [バージョン履歴 (file-versions)]
            │
            ├─→ [新規バージョンアップロード]
            │       │
            │       └─→ アップロード完了 → [バージョン履歴]
            │
            ├─→ [バージョン比較モーダル]
            │       │
            │       └─→ 閉じる → [バージョン履歴]
            │
            └─→ [バージョン復元]
                    │
                    └─→ 復元完了 → [バージョン履歴]（新バージョンとして追加）
```

**主要な遷移:**

1. **ファイル一覧 → アップロード画面**: 「新規アップロード」ボタンから遷移
2. **ファイル一覧 → バージョン履歴**: ファイル名クリックで該当ファイルのバージョン履歴画面へ
3. **バージョン履歴 → 比較モーダル**: 「比較」ボタンでモーダル表示
4. **バージョン履歴 → 復元**: 「復元」ボタンで確認ダイアログ表示後、復元実行

#### UI設計

##### ファイル一覧画面

```text
┌────────────────────────────────────────────────────────────────┐
│  プロジェクトファイル                      [新規アップロード]  │
├────────────────────────────────────────────────────────────────┤
│  検索: [____________]  種別: [すべて ▼]                        │
├────────────────────────────────────────────────────────────────┤
│  ファイル名          │ タイプ │ サイズ │ 更新者   │ 更新日時    │
├──────────────────────┼────────┼────────┼──────────┼────────────┤
│  📄 sales_data.xlsx  │ Excel  │ 1.0MB  │ 山田太郎 │ 2026/01/01 │
│  (v3)                │        │        │          │ 10:00      │
│  [ダウンロード] [履歴]                                          │
├──────────────────────┼────────┼────────┼──────────┼────────────┤
│  📄 proposal.pdf     │ PDF    │ 2.5MB  │ 鈴木花子 │ 2025/12/28 │
│  (v1)                │        │        │          │ 15:30      │
│  [ダウンロード] [履歴]                                          │
├──────────────────────┼────────┼────────┼──────────┼────────────┤
│  📄 design.psd       │ 画像   │ 15MB   │ 佐藤次郎 │ 2025/12/25 │
│  (v2)                │        │        │          │ 09:15      │
│  [ダウンロード] [履歴]                                          │
└────────────────────────────────────────────────────────────────┘
```

**機能:**

1. **検索・フィルタ**: ファイル名検索（部分一致）、ファイルタイプフィルタ
2. **テーブル項目**: ファイル名、現在バージョン、タイプ、サイズ、更新者、更新日時
3. **操作**: ダウンロード、履歴表示

##### アップロード画面

```text
┌────────────────────────────────────────────────────────────────┐
│  ファイルアップロード                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   ┌────────────────────────────────────────────────────────┐  │
│   │          📁  ここにファイルをドラッグ&ドロップ         │  │
│   │                  または                                │  │
│   │              [ファイルを選択]                          │  │
│   └────────────────────────────────────────────────────────┘  │
│                                                                │
│   対応フォーマット: Excel (.xlsx, .xls), PDF, Word, 画像      │
│   最大ファイルサイズ: 50MB                                    │
│                                                                │
│   選択ファイル:                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  📄 sales_report_2026.xlsx                           │    │
│   │  サイズ: 1.2MB                                       │    │
│   │  [×]                                                 │    │
│   └──────────────────────────────────────────────────────┘    │
│                                                                │
│   コメント: [_____________________________________]            │
│                                                                │
│                                   [キャンセル] [アップロード]  │
└────────────────────────────────────────────────────────────────┘
```

**機能:**

1. **ドラッグ&ドロップエリア**: ファイル選択、対応フォーマット表示
2. **ファイル選択**: ファイルプレビュー、選択解除
3. **アップロード進捗**: プログレスバー、キャンセル機能
4. **コメント入力**: 任意コメント入力

##### バージョン履歴画面

```text
┌────────────────────────────────────────────────────────┐
│  sales_data.xlsx のバージョン履歴                       │
│  現在: v3                                    [新規 ▲]  │
├────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐   │
│  │ ● v3 (現在)                     2026/01/01    │   │
│  │   Q4データ追加                                  │   │
│  │   山田 太郎 • 1.0 MB                           │   │
│  │   [ダウンロード]                               │   │
│  └────────────────────────────────────────────────┘   │
│        │                                               │
│  ┌────────────────────────────────────────────────┐   │
│  │ ○ v2                           2025/12/15     │   │
│  │   Q3データ修正                                  │   │
│  │   鈴木 花子 • 512 KB                           │   │
│  │   [ダウンロード] [復元] [比較]                   │   │
│  └────────────────────────────────────────────────┘   │
│        │                                               │
│  ┌────────────────────────────────────────────────┐   │
│  │ ○ v1                           2025/12/01     │   │
│  │   初回アップロード                              │   │
│  │   山田 太郎 • 256 KB                           │   │
│  │   [ダウンロード] [復元] [比較]                   │   │
│  └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

##### バージョン比較モーダル

```text
┌────────────────────────────────────────────────────────┐
│  バージョン比較                              [×]       │
├────────────────────────────────────────────────────────┤
│  比較元: [v2 ▼]  →  比較先: [v3 ▼]                    │
├────────────────────────────────────────────────────────┤
│  ファイルサイズ: 512 KB → 1.0 MB (+100%)              │
├────────────────────────────────────────────────────────┤
│  シート別変更:                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Sheet1                                           │ │
│  │   行: +150行 / -0行                              │ │
│  │   列: +2列 / -0列                                │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Sheet2                                           │ │
│  │   行: +50行 / -10行                              │ │
│  │   列: 変更なし                                   │ │
│  └──────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────┤
│                                         [閉じる]       │
└────────────────────────────────────────────────────────┘
```

---

## 2. 画面詳細設計

### 2.1 ファイル一覧画面（files）

#### 画面項目・APIマッピング

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ファイル名 | テキスト | GET /project/{id}/files | files[].name | - |
| 現在バージョン | テキスト | GET /project/{id}/files | files[].currentVersion | "v" + n |
| ファイルタイプ | テキスト | GET /project/{id}/files | files[].fileType | アイコン表示 |
| ファイルサイズ | テキスト | GET /project/{id}/files | files[].fileSize | KB/MB変換 |
| 最終更新者 | テキスト | GET /project/{id}/files | files[].updatedByName | - |
| 最終更新日時 | 日時 | GET /project/{id}/files | files[].updatedAt | YYYY/MM/DD HH:mm形式 |
| 検索入力 | テキスト | GET /project/{id}/files?search= | search | クエリパラメータ |
| タイプフィルタ | セレクト | GET /project/{id}/files?fileType= | fileType | クエリパラメータ |
| ダウンロードボタン | ボタン | GET /project/{id}/file/{fileId}/download | - | ファイルDL |
| 履歴ボタン | リンク | - | - | バージョン履歴画面へ遷移 |

#### 必要なAPI

##### GET /api/v1/project/{project_id}/files

プロジェクト内の全ファイル一覧を取得

**クエリパラメータ:**

- search: ファイル名検索（部分一致）
- fileType: ファイルタイプフィルタ（excel, pdf, image, other）
- page, limit: ページネーション

**レスポンス:**

```json
{
  "files": [
    {
      "fileId": "uuid",
      "name": "sales_data.xlsx",
      "fileType": "excel",
      "fileSize": 1048576,
      "currentVersion": 3,
      "updatedBy": "uuid",
      "updatedByName": "山田 太郎",
      "updatedAt": "2026-01-01T10:00:00Z",
      "createdAt": "2025-12-01T00:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20
}
```

### 2.2 アップロード画面（upload）

#### 画面項目・APIマッピング

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| ファイル | ファイル選択 | ○ | POST /project/{id}/files | file | 最大50MB、対応フォーマット |
| コメント | テキスト | - | POST /project/{id}/files | comment | 最大500文字 |
| アップロードボタン | ボタン | - | POST /project/{id}/files | - | - |

#### 必要なAPI

##### POST /api/v1/project/{project_id}/files

新規ファイルをアップロード

**リクエスト:**

- Content-Type: multipart/form-data
- file: File（必須）
- comment: string（任意）

**レスポンス:**

```json
{
  "fileId": "uuid",
  "name": "sales_report_2026.xlsx",
  "fileType": "excel",
  "fileSize": 1258291,
  "currentVersion": 1,
  "comment": "2026年売上レポート",
  "uploadedBy": "uuid",
  "uploadedByName": "山田 太郎",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

### 2.3 バージョン履歴画面（file-versions）

#### 画面項目・APIマッピング

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ファイル名 | テキスト | GET /file/{id}/version | fileName | - |
| 現在バージョン | テキスト | GET /file/{id}/version | currentVersion | "v" + n |
| バージョン番号 | テキスト | GET /file/{id}/version | versions[].versionNumber | "v" + n |
| 現在フラグ | バッジ | GET /file/{id}/version | versions[].isCurrent | "現在" バッジ |
| 日時 | 日時 | GET /file/{id}/version | versions[].createdAt | YYYY/MM/DD形式 |
| コメント | テキスト | GET /file/{id}/version | versions[].comment | - |
| アップロード者 | テキスト | GET /file/{id}/version | versions[].uploadedByName | - |
| ファイルサイズ | テキスト | GET /file/{id}/version | versions[].fileSize | KB/MB変換 |
| ダウンロードボタン | ボタン | GET /file/{id}/version/{versionId} | - | ファイルDL |
| 復元ボタン | ボタン | POST /version/{id}/restore | - | 確認ダイアログ |
| 比較ボタン | ボタン | - | - | 比較モーダル表示 |

#### 新規バージョンアップロード

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| ファイル | ファイル選択 | ○ | POST /file/{id}/version | file | 同名・同形式のみ |
| コメント | テキスト | - | POST /file/{id}/version | comment | 最大500文字 |
| アップロードボタン | ボタン | - | POST /file/{id}/version | - | - |

### 2.4 バージョン比較モーダル

#### 画面項目・APIマッピング

| 画面項目 | 入力/表示形式 | APIエンドポイント | パラメータ/フィールド | 変換処理 |
|---------|-------------|------------------|---------------------|---------|
| 比較元バージョン | セレクト | GET /file/{id}/version/compare | version1 | - |
| 比較先バージョン | セレクト | GET /file/{id}/version/compare | version2 | - |
| サイズ変更 | テキスト | GET /compare | comparison.sizeChange | +n KB / -n KB |
| サイズ変更率 | テキスト | GET /compare | comparison.sizeChangePercent | +n% / -n% |
| シート変更一覧 | リスト | GET /compare | comparison.sheetChanges[] | - |
| 行追加数 | テキスト | GET /compare | sheetChanges[].rowsAdded | +n行 |
| 行削除数 | テキスト | GET /compare | sheetChanges[].rowsRemoved | -n行 |

---

## 3. 画面項目・APIマッピング

### 3.1 ファイル一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ファイル名検索 | テキスト | - | `GET /project/{id}/files` | `search` | 部分一致 |
| タイプフィルタ | セレクト | - | 同上 | `fileType` | excel/pdf/image/other |
| ページ | 数値 | - | 同上 | `page` | 1以上 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20 |

### 3.2 ファイルアップロード

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ファイル | ファイル選択 | ✓ | `POST /project/{id}/files` | `file` | 最大50MB |
| コメント | テキスト | - | 同上 | `comment` | 最大500文字 |

### 3.3 バージョン操作

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 新規バージョンファイル | ファイル選択 | ✓ | `POST /file/{id}/version` | `file` | 同名・同形式 |
| コメント | テキスト | - | 同上 | `comment` | 最大500文字 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| ファイル一覧ページ表示 | `GET /project/{id}/files` | 初期ロード |
| 検索実行 | `GET /project/{id}/files?search=` | デバウンス300ms |
| タイプフィルタ変更 | `GET /project/{id}/files?fileType=` | 再取得 |
| アップロードボタン | `POST /project/{id}/files` | multipart/form-data |
| ファイル名クリック | - | バージョン履歴画面へ遷移 |
| バージョン履歴表示 | `GET /file/{id}/version` | - |
| 新規バージョンアップロード | `POST /file/{id}/version` | multipart/form-data |
| バージョン復元 | `POST /version/{id}/restore` | 確認後 |
| バージョン比較 | `GET /file/{id}/version/compare` | モーダル表示 |
| ダウンロード | `GET /file/{id}/version/{versionId}` | ファイルDL |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | ファイルが見つかりませんメッセージ表示 |
| 413 Payload Too Large | ファイルサイズが制限を超えていますメッセージ表示 |
| 415 Unsupported Media Type | 対応していないファイル形式ですメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| アップロード | プログレス表示、チャンクアップロード対応 |
| ダウンロード | ストリーミングダウンロードで大容量ファイル対応 |
| 検索 | 300msデバウンスでAPI呼び出しを最適化 |
| キャッシュ | React Query でファイル一覧を5分間キャッシュ |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| FV-001 | バージョン一覧表示 | `GET /file/{id}/version` | file-versions | 設計済 |
| FV-002 | 新規バージョンアップロード | `POST /file/{id}/version` | VersionUploadModal | 設計済 |
| FV-003 | バージョン復元 | `POST /version/{id}/restore` | file-versions | 設計済 |
| FV-004 | バージョン比較 | `GET /file/{id}/version/compare` | VersionCompareModal | 設計済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| FileTable | Default | ファイル一覧テーブル表示 | 通常、空、ローディング、フィルタ適用 |
| DropZone | Default | ドラッグ&ドロップエリア | 通常、ドラッグオーバー、ファイル選択済み、エラー |
| UploadProgress | Default | アップロード進捗表示 | 通常、完了、エラー |
| VersionList | Default | バージョン一覧表示 | 通常、単一バージョン |
| VersionItem | Current | バージョン項目表示 | 現在バージョン、過去バージョン |
| VersionUploadModal | Default | バージョンアップロードモーダル | 通常、アップロード中 |
| VersionCompareModal | Default | バージョン比較モーダル | 通常、比較結果表示 |

### 8.2 ストーリー実装例

```tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { DropZone } from "./drop-zone";
import type { SelectedFile } from "../../types";

const selectedFile: SelectedFile = {
  name: "sales_report_2026.xlsx",
  size: 1258291,
};

const meta = {
  title: "features/file-version/components/drop-zone",
  component: DropZone,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "ファイルドロップゾーンコンポーネント。ドラッグ＆ドロップでファイルを選択。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onFileDrop: fn(),
  },
  argTypes: {
    isDragOver: { control: "boolean" },
    hasError: { control: "boolean" },
  },
} satisfies Meta<typeof DropZone>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    accept: ".xlsx,.xls,.pdf,.docx,.png,.jpg",
    maxSize: 50 * 1024 * 1024,
  },
};

export const DragOver: Story = {
  args: {
    accept: ".xlsx,.xls,.pdf,.docx,.png,.jpg",
    maxSize: 50 * 1024 * 1024,
    isDragOver: true,
  },
};

export const WithFile: Story = {
  args: {
    accept: ".xlsx,.xls,.pdf,.docx,.png,.jpg",
    maxSize: 50 * 1024 * 1024,
    selectedFile,
  },
};

export const Error: Story = {
  args: {
    accept: ".xlsx,.xls,.pdf,.docx,.png,.jpg",
    maxSize: 50 * 1024 * 1024,
    hasError: true,
    errorMessage: "ファイルサイズが制限を超えています",
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | ドロップゾーン動作、バージョン表示、進捗表示 |
| ユーティリティ | ユニットテスト | 90%以上 | ファイルサイズ変換、バリデーション |
| 統合 | コンポーネントテスト | 70%以上 | アップロードフロー、バージョン操作 |
| E2E | E2Eテスト | 主要フロー | ファイルアップロード、バージョン復元、比較 |

### 9.2 ユニットテスト例

```typescript
import { describe, it, expect } from "vitest";
import { formatFileSize, validateFile, getFileTypeIcon } from "./file-utils";

describe("formatFileSize", () => {
  it("バイトをKB単位で表示する", () => {
    expect(formatFileSize(1024)).toBe("1.0 KB");
  });

  it("バイトをMB単位で表示する", () => {
    expect(formatFileSize(1048576)).toBe("1.0 MB");
  });

  it("小数点以下を正しく表示する", () => {
    expect(formatFileSize(1536)).toBe("1.5 KB");
  });
});

describe("validateFile", () => {
  it("許可されたファイル形式を通す", () => {
    const file = new File([""], "test.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    const result = validateFile(file, { accept: ".xlsx,.pdf", maxSize: 50 * 1024 * 1024 });
    expect(result.valid).toBe(true);
  });

  it("サイズ制限を超えたファイルを拒否する", () => {
    const file = new File(["x".repeat(100)], "test.xlsx");
    const result = validateFile(file, { accept: ".xlsx", maxSize: 50 });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("サイズ");
  });

  it("許可されていない形式を拒否する", () => {
    const file = new File([""], "test.exe", { type: "application/x-msdownload" });
    const result = validateFile(file, { accept: ".xlsx,.pdf", maxSize: 50 * 1024 * 1024 });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("形式");
  });
});

describe("getFileTypeIcon", () => {
  it("Excelファイルに正しいアイコンを返す", () => {
    expect(getFileTypeIcon("excel")).toBe("📊");
  });

  it("PDFファイルに正しいアイコンを返す", () => {
    expect(getFileTypeIcon("pdf")).toBe("📄");
  });

  it("不明なタイプにデフォルトアイコンを返す", () => {
    expect(getFileTypeIcon("unknown")).toBe("📁");
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { DropZone } from "./drop-zone";
import type { SelectedFile } from "../../types";

describe("DropZone", () => {
  it("ドロップゾーンを表示する", () => {
    render(<DropZone onFileDrop={vi.fn()} />);

    expect(screen.getByText("ここにファイルをドラッグ&ドロップ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ファイルを選択" })).toBeInTheDocument();
  });

  it("ドラッグオーバー時にスタイルが変わる", () => {
    render(<DropZone onFileDrop={vi.fn()} />);

    const dropZone = screen.getByTestId("drop-zone");
    // ドラッグ&ドロップイベントはfireEventで十分（userEventは未対応）
    fireEvent.dragOver(dropZone);

    expect(dropZone).toHaveClass("drag-over");
  });

  it("ファイルドロップでonFileDropを呼び出す", async () => {
    const onFileDrop = vi.fn();
    render(<DropZone onFileDrop={onFileDrop} accept=".xlsx" />);

    const file = new File([""], "test.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    const dropZone = screen.getByTestId("drop-zone");

    // ドラッグ&ドロップイベントはfireEventで十分（userEventは未対応）
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(onFileDrop).toHaveBeenCalledWith(file);
    });
  });

  it("選択済みファイルを表示する", () => {
    const selectedFile: SelectedFile = { name: "sales_report.xlsx", size: 1258291 };
    render(
      <DropZone
        onFileDrop={vi.fn()}
        selectedFile={selectedFile}
      />
    );

    expect(screen.getByText("sales_report.xlsx")).toBeInTheDocument();
    expect(screen.getByText("1.2 MB")).toBeInTheDocument();
  });

  it("エラーメッセージを表示する", () => {
    render(
      <DropZone
        onFileDrop={vi.fn()}
        hasError
        errorMessage="ファイルサイズが制限を超えています"
      />
    );

    expect(screen.getByText("ファイルサイズが制限を超えています")).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
import { test, expect } from "@playwright/test";
import path from "path";

test.describe("ファイル管理機能", () => {
  test("ファイルをアップロードできる", async ({ page }) => {
    await page.goto("/projects/1/files/upload");

    // ファイル選択
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "fixtures/test.xlsx"));

    // コメント入力
    await page.getByLabel("コメント").fill("2026年売上レポート");

    // アップロード実行
    await page.getByRole("button", { name: "アップロード" }).click();

    // 成功メッセージ
    await expect(page.getByText("ファイルをアップロードしました")).toBeVisible();

    // 一覧に表示される
    await page.goto("/projects/1/files");
    await expect(page.getByText("test.xlsx")).toBeVisible();
  });

  test("新規バージョンをアップロードできる", async ({ page }) => {
    await page.goto("/projects/1/files/file-1/versions");

    // 新規バージョンボタン
    await page.getByRole("button", { name: "新規" }).click();

    // ファイル選択
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "fixtures/test_v2.xlsx"));

    // コメント入力
    await page.getByLabel("コメント").fill("Q4データ追加");

    // アップロード実行
    await page.getByRole("button", { name: "アップロード" }).click();

    // 成功メッセージ
    await expect(page.getByText("新しいバージョンをアップロードしました")).toBeVisible();

    // バージョンが追加される
    await expect(page.getByText("v2")).toBeVisible();
  });

  test("バージョンを復元できる", async ({ page }) => {
    await page.goto("/projects/1/files/file-1/versions");

    // v1の復元ボタンクリック
    await page.getByTestId("version-v1").getByRole("button", { name: "復元" }).click();

    // 確認ダイアログ
    await expect(page.getByText("このバージョンを復元しますか？")).toBeVisible();
    await page.getByRole("button", { name: "復元" }).click();

    // 成功メッセージ
    await expect(page.getByText("バージョンを復元しました")).toBeVisible();

    // 新しいバージョンとして追加される
    await expect(page.getByText("v3")).toBeVisible();
  });

  test("バージョンを比較できる", async ({ page }) => {
    await page.goto("/projects/1/files/file-1/versions");

    // 比較ボタンクリック
    await page.getByTestId("version-v1").getByRole("button", { name: "比較" }).click();

    // 比較モーダル
    await expect(page.getByText("バージョン比較")).toBeVisible();

    // バージョン選択
    await page.getByLabel("比較元").selectOption("v1");
    await page.getByLabel("比較先").selectOption("v2");

    // 比較結果を確認
    await expect(page.getByText("ファイルサイズ")).toBeVisible();
    await expect(page.getByText("シート別変更")).toBeVisible();
  });

  test("ファイル一覧を検索・フィルタできる", async ({ page }) => {
    await page.goto("/projects/1/files");

    // 検索
    await page.getByPlaceholder("ファイル名で検索").fill("sales");
    await expect(page.getByText("sales_data.xlsx")).toBeVisible();

    // タイプフィルタ
    await page.getByLabel("種別").selectOption("excel");
    const rows = page.getByTestId("file-row");
    await expect(rows).toHaveCount(2);
  });
});
```

### 9.5 モックデータ

```typescript
// src/testing/mocks/handlers/file-management.ts
import { http, HttpResponse } from "msw";

export const fileManagementHandlers = [
  http.get("/api/project/:projectId/files", ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get("search");
    const fileType = url.searchParams.get("fileType");

    const files = [
      {
        fileId: "file-1",
        name: "sales_data.xlsx",
        fileType: "excel",
        fileSize: 1048576,
        currentVersion: 3,
        updatedByName: "山田 太郎",
        updatedAt: "2026-01-01T10:00:00Z",
      },
      {
        fileId: "file-2",
        name: "proposal.pdf",
        fileType: "pdf",
        fileSize: 2621440,
        currentVersion: 1,
        updatedByName: "鈴木 花子",
        updatedAt: "2025-12-28T15:30:00Z",
      },
    ];

    let filtered = files;
    if (search) {
      filtered = filtered.filter((f) => f.name.includes(search));
    }
    if (fileType) {
      filtered = filtered.filter((f) => f.fileType === fileType);
    }

    return HttpResponse.json({ files: filtered, total: filtered.length });
  }),

  http.post("/api/project/:projectId/files", async () => {
    return HttpResponse.json({
      fileId: "new-file-id",
      name: "uploaded_file.xlsx",
      fileType: "excel",
      fileSize: 1258291,
      currentVersion: 1,
      createdAt: new Date().toISOString(),
    });
  }),

  http.get("/api/file/:fileId/version", () => {
    return HttpResponse.json({
      fileName: "sales_data.xlsx",
      currentVersion: 3,
      versions: [
        {
          versionId: "v3",
          versionNumber: 3,
          isCurrent: true,
          comment: "Q4データ追加",
          uploadedByName: "山田 太郎",
          fileSize: 1048576,
          createdAt: "2026-01-01T10:00:00Z",
        },
        {
          versionId: "v2",
          versionNumber: 2,
          isCurrent: false,
          comment: "Q3データ修正",
          uploadedByName: "鈴木 花子",
          fileSize: 524288,
          createdAt: "2025-12-15T00:00:00Z",
        },
        {
          versionId: "v1",
          versionNumber: 1,
          isCurrent: false,
          comment: "初回アップロード",
          uploadedByName: "山田 太郎",
          fileSize: 262144,
          createdAt: "2025-12-01T00:00:00Z",
        },
      ],
    });
  }),

  http.post("/api/file/:fileId/version", async () => {
    return HttpResponse.json({
      versionId: "new-version-id",
      versionNumber: 4,
      createdAt: new Date().toISOString(),
    });
  }),

  http.post("/api/version/:versionId/restore", () => {
    return HttpResponse.json({
      newVersionId: "restored-version-id",
      versionNumber: 4,
      createdAt: new Date().toISOString(),
    });
  }),

  http.get("/api/file/:fileId/version/compare", ({ request }) => {
    const url = new URL(request.url);
    const version1 = url.searchParams.get("version1");
    const version2 = url.searchParams.get("version2");

    return HttpResponse.json({
      version1,
      version2,
      comparison: {
        sizeChange: 524288,
        sizeChangePercent: 100,
        sheetChanges: [
          { sheetName: "Sheet1", rowsAdded: 150, rowsRemoved: 0, colsAdded: 2, colsRemoved: 0 },
          { sheetName: "Sheet2", rowsAdded: 50, rowsRemoved: 10, colsAdded: 0, colsRemoved: 0 },
        ],
      },
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-file-version-design.md](./01-file-version-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **プロジェクト管理設計書**: [../04-project-management/01-project-management-design.md](../04-project-management/01-project-management-design.md)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | FV-FRONTEND-001 |
| 対象ユースケース | FV-001〜FV-004 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/projects/[id]/files/` |
