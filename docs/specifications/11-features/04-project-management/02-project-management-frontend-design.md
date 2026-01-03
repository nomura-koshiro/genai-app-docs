# プロジェクト管理 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| projects | プロジェクト一覧 | `/projects` | プロジェクト一覧表示・検索 |
| project-new | プロジェクト作成 | `/projects/new` | 新規プロジェクト作成フォーム |
| project-detail | プロジェクト詳細 | `/projects/{id}` | プロジェクト詳細・統計表示 |
| members | メンバー管理 | `/projects/{id}/members` | メンバー一覧・追加・削除 |
| files | ファイル管理 | `/projects/{id}/files` | ファイル一覧・アップロード |
| upload | ファイルアップロード | `/projects/{id}/upload` | ファイルアップロード画面 |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | プロジェクトカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `DataTable` | メンバー一覧、ファイル一覧 | 同上 |
| `Pagination` | ページネーション | 同上 |
| `Badge` | ステータスバッジ、ロールバッジ | 同上 |
| `Button` | 操作ボタン | 同上 |
| `Input` | 検索・フォーム入力 | 同上 |
| `Textarea` | 説明入力 | 同上 |
| `Select` | フィルタ、ロール選択 | 同上 |
| `Modal` | 編集モーダル、確認ダイアログ | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Tabs` | プロジェクト詳細タブ | 同上 |
| `DatePicker` | 開始日・終了日入力 | 同上 |
| `FileUpload` | ファイルアップロード | 同上 |
| `EmptyState` | データなし表示 | 同上 |

### 1.3 コンポーネント構成

```text
features/project-management/
├── api/
│   ├── get-projects.ts              # GET /api/v1/project
│   ├── get-project.ts               # GET /api/v1/project/{id}
│   ├── create-project.ts            # POST /api/v1/project
│   ├── update-project.ts            # PATCH /api/v1/project/{id}
│   ├── get-members.ts               # GET /api/v1/project/{id}/member
│   ├── create-member.ts             # POST /api/v1/project/{id}/member
│   ├── update-member.ts             # PATCH /api/v1/project/{id}/member/{memberId}
│   ├── delete-member.ts             # DELETE /api/v1/project/{id}/member/{memberId}
│   ├── get-files.ts                 # GET /api/v1/project/{id}/file
│   ├── upload-file.ts               # POST /api/v1/project/{id}/file
│   ├── delete-file.ts               # DELETE /api/v1/project/{id}/file/{fileId}
│   └── index.ts
├── components/
│   ├── project-card/
│   │   ├── project-card.tsx         # プロジェクトカード（Card使用）
│   │   └── index.ts
│   ├── project-filters/
│   │   ├── project-filters.tsx      # フィルター（Select使用）
│   │   └── index.ts
│   ├── project-form/
│   │   ├── project-form.tsx         # 作成・編集フォーム
│   │   └── index.ts
│   ├── project-stats/
│   │   ├── project-stats.tsx        # 統計情報
│   │   └── index.ts
│   ├── member-table/
│   │   ├── member-table.tsx         # メンバー一覧（DataTable使用）
│   │   └── index.ts
│   ├── member-invite-modal/
│   │   ├── member-invite-modal.tsx  # メンバー招待モーダル
│   │   └── index.ts
│   ├── file-list/
│   │   ├── file-list.tsx            # ファイル一覧（DataTable使用）
│   │   └── index.ts
│   ├── file-upload-area/
│   │   ├── file-upload-area.tsx     # アップロードエリア（FileUpload使用）
│   │   └── index.ts
│   └── index.ts
├── routes/
│   ├── project-list/
│   │   ├── project-list.tsx         # プロジェクト一覧コンテナ
│   │   ├── project-list.hook.ts     # プロジェクト一覧用hook
│   │   └── index.ts
│   ├── project-new/
│   │   ├── project-new.tsx          # プロジェクト作成コンテナ
│   │   ├── project-new.hook.ts      # プロジェクト作成用hook
│   │   └── index.ts
│   ├── project-detail/
│   │   ├── project-detail.tsx       # プロジェクト詳細コンテナ
│   │   ├── project-detail.hook.ts   # プロジェクト詳細用hook
│   │   └── index.ts
│   ├── members/
│   │   ├── members.tsx              # メンバー管理コンテナ
│   │   ├── members.hook.ts          # メンバー管理用hook
│   │   └── index.ts
│   └── files/
│       ├── files.tsx                # ファイル管理コンテナ
│       ├── files.hook.ts            # ファイル管理用hook
│       └── index.ts
├── types/
│   ├── api.ts                       # API入出力の型
│   ├── domain.ts                    # ドメインモデル（Project, Member, File等）
│   └── index.ts
└── index.ts

app/projects/
├── page.tsx               # プロジェクト一覧ページ → ProjectList
├── new/
│   └── page.tsx           # プロジェクト作成ページ → ProjectNew
└── [id]/
    ├── page.tsx           # プロジェクト詳細ページ → ProjectDetail
    ├── members/
    │   └── page.tsx       # メンバー管理ページ → Members
    └── files/
        └── page.tsx       # ファイル管理ページ → Files
```

---

## 2. 画面詳細設計

### 2.1 プロジェクト一覧画面（projects）

#### 検索・フィルタ項目

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|------------------|-----------------|------|
| プロジェクト名検索 | テキスト | `GET /api/v1/project` | - | フロントでフィルタ |
| ステータスフィルタ | セレクト | 同上 | `is_active` | true/false/null |

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | テキスト(strong) | `GET /api/v1/project` | `projects[].name` | - |
| 説明 | テキスト | 同上 | `projects[].description` | 切り詰め表示 |
| メンバー数 | 数値 | 同上 | `projects[].stats.memberCount` | - |
| ステータス | バッジ | 同上 | `projects[].isActive` | `true`→"有効"(success), `false`→"アーカイブ"(secondary) |
| 作成日 | 日付 | 同上 | `projects[].createdAt` | ISO8601→YYYY/MM/DD |
| 編集ボタン | ボタン | - | - | 編集モーダル表示 |
| アーカイブ/復元ボタン | ボタン | `PATCH /api/v1/project/{id}` | `isActive` | 状態により切替 |

#### ページネーション

| 画面項目 | 表示形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|------------------|-----------------|------|
| 表示件数選択 | セレクト | `GET /api/v1/project` | `limit` | 10/25/50/100件 |
| ページ番号 | ボタン | 同上 | `skip`, `limit` | `skip = (page - 1) × limit` |
| 前へ/次へボタン | ボタン | 同上 | `skip`, `limit` | ページ移動 |
| 総件数表示 | テキスト | 同上 | レスポンス `total` | "X件中Y-Z件を表示" |

### 2.2 プロジェクト作成画面（project-new）

#### 入力項目

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| プロジェクト名 | テキスト | ✓ | `POST /api/v1/project` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | - |
| 開始日 | 日付 | - | 同上 | `startDate` | - |
| 終了予定日 | 日付 | - | 同上 | `endDate` | 開始日以降 |
| 初期メンバー | 複数選択 | - | 別途メンバー追加API | - | - |

### 2.3 プロジェクト詳細画面（project-detail）

#### レイアウト構成

| エリア | 説明 | 幅 |
|--------|------|-----|
| メインエリア | プロジェクト概要・統計・セッション・ツリー一覧 | 70% |
| サイドバー | ファイル一覧・アップロード | 30% |

#### プロジェクト概要セクション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | タイトル | `GET /api/v1/project/{id}` | `name` | - |
| ステータス | バッジ | 同上 | `isActive` | boolean→バッジ |
| 説明 | テキスト | 同上 | `description` | - |
| 作成日 | 日付 | 同上 | `createdAt` | YYYY年MM月DD日 |
| 開始日 | 日付 | 同上 | `startDate` | YYYY年MM月DD日 |
| 終了予定日 | 日付 | 同上 | `endDate` | YYYY年MM月DD日 |
| 作成者 | テキスト | 同上 | `createdBy` | ユーザー名取得必要 |
| 編集ボタン | ボタン | - | - | 編集モーダル表示 |

#### 統計セクション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| セッション数 | 数値 | `GET /api/v1/project/{id}` | `stats.sessionCount` | - |
| スナップショット数 | 数値 | 同上 | 別途計算 | - |
| ツリー数 | 数値 | 同上 | `stats.treeCount` | - |
| ファイル数 | 数値 | 同上 | `stats.fileCount` | - |

#### 分析セッション一覧セクション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| セッション名 | テキスト(Link) | `GET /api/v1/project/{id}/session` | `sessions[].name` | クリックでセッション詳細へ |
| 現在の課題 | テキスト | 同上 | `sessions[].currentChallenge` | - |
| スナップショット数 | 数値 | 同上 | `sessions[].snapshotCount` | - |
| 更新日時 | 日付 | 同上 | `sessions[].updatedAt` | ISO8601→YYYY/MM/DD HH:mm |
| 詳細ボタン | ボタン | - | - | セッション詳細画面へ遷移 |

**API連携**:

- プロジェクト詳細取得時に `stats.sessionCount` で件数を表示
- セッション一覧は別途 `GET /api/v1/project/{project_id}/session` で取得
- 初期表示は最新5件、「すべて表示」でセッション一覧画面へ

#### ドライバーツリー一覧セクション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ツリー名 | テキスト(Link) | `GET /api/v1/project/{id}/tree` | `trees[].name` | クリックでツリー詳細へ |
| ノード数 | 数値 | 同上 | `trees[].nodeCount` | - |
| 施策数 | 数値 | 同上 | `trees[].actionCount` | - |
| 更新日時 | 日付 | 同上 | `trees[].updatedAt` | ISO8601→YYYY/MM/DD HH:mm |
| 詳細ボタン | ボタン | - | - | ツリー詳細画面へ遷移 |

**API連携**:

- プロジェクト詳細取得時に `stats.treeCount` で件数を表示
- ツリー一覧は別途 `GET /api/v1/project/{project_id}/tree` で取得
- 初期表示は最新5件、「すべて表示」でツリー一覧画面へ

#### プロジェクト編集モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| プロジェクト名 | テキスト | ✓ | `PATCH /api/v1/project/{id}` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | - |
| 開始日 | 日付 | - | 同上 | `startDate` | - |
| 終了予定日 | 日付 | - | 同上 | `endDate` | 開始日以降 |
| ステータス | トグル | - | 同上 | `isActive` | true/false |
| 保存ボタン | ボタン | - | - | - | 必須項目チェック |
| キャンセルボタン | ボタン | - | - | - | モーダル閉じる |

**モーダル動作**:

- 編集ボタンクリックで現在の値を設定して表示
- 保存時は `PATCH /api/v1/project/{id}` で更新
- 成功時はモーダルを閉じて詳細画面を再読み込み

### 2.4 メンバー管理画面（members）

#### タブ構成

| タブ名 | 説明 | デフォルト |
|--------|------|-----------|
| メンバー一覧 | 現在のプロジェクトメンバー一覧 | ✓ |
| 招待履歴 | メンバー招待・追加履歴 | - |

#### メンバー一覧タブ

##### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー（アイコン+名前） | アイコン+テキスト | `GET /api/v1/project/{id}/member` | `members[].user.displayName` | - |
| メールアドレス | テキスト | 同上 | `members[].user.email` | - |
| ロール | バッジ | 同上 | `members[].role` | ロール名→バッジ色 |
| 追加日 | 日付 | 同上 | `members[].joinedAt` | ISO8601→YYYY/MM/DD |
| ロール変更 | セレクト | `PATCH .../member/{id}` | `role` | PM以外表示 |
| 削除ボタン | ボタン | `DELETE .../member/{id}` | - | 作成者は削除不可 |

##### ロール色マッピング

| ロール | バッジ色 | 説明 |
|--------|---------|------|
| project_manager | info | プロジェクト管理者 |
| project_moderator | warning | モデレーター |
| member | success | 一般メンバー |
| viewer | neutral | 閲覧者 |

##### メンバー追加モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ユーザー選択 | セレクト | ✓ | `POST /api/v1/project/{id}/member` | `userId` | 既存メンバー除外 |
| ロール | セレクト | ✓ | 同上 | `role` | 有効なロール値 |

#### 招待履歴タブ

##### 履歴表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 追加者 | テキスト | `GET /api/v1/project/{id}/member/history` | `history[].addedBy.displayName` | - |
| 追加されたユーザー | テキスト | 同上 | `history[].user.displayName` | - |
| ロール | バッジ | 同上 | `history[].role` | ロール名→バッジ色 |
| 追加日時 | 日付 | 同上 | `history[].joinedAt` | ISO8601→YYYY/MM/DD HH:mm |
| ステータス | バッジ | 同上 | `history[].status` | active/removed |

**ステータス表示**:

- `active`: "現在のメンバー"（success）
- `removed`: "削除済み"（secondary）

**API連携**:

- メンバー追加履歴は `GET /api/v1/project/{project_id}/member/history` で取得
- 削除されたメンバーも履歴に含む
- 追加日時の降順でソート

### 2.5 ファイル管理サイドバー

#### ファイル一覧

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ファイルアイコン | アイコン | `GET /api/v1/project/{id}/file` | `files[].mimeType` | MIMEタイプ→アイコン |
| ファイル名 | テキスト | 同上 | `files[].originalFilename` | - |
| サイズ・日付 | テキスト | 同上 | `files[].fileSize`, `files[].createdAt` | バイト→KB/MB, MM/DD |

#### ファイルアイコンマッピング

| MIMEタイプ | アイコン |
|-----------|---------|
| application/vnd.* (Excel) | 📊 |
| text/csv | 📄 |
| application/pdf | 📕 |
| image/* | 🖼️ |
| その他 | 📎 |

---

## 3. 画面項目・APIマッピング

### 3.1 プロジェクト一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ステータスフィルタ | セレクト | - | `GET /api/v1/project` | `is_active` | true/false/null |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

### 3.2 プロジェクト作成

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| プロジェクト名 | テキスト | ✓ | `POST /api/v1/project` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | 任意 |
| 開始日 | 日付 | - | 同上 | `startDate` | ISO8601形式 |
| 終了予定日 | 日付 | - | 同上 | `endDate` | 開始日以降 |

### 3.3 メンバー管理

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ユーザー選択 | セレクト | ✓ | `POST /api/v1/project/{id}/member` | `userId` | UUID |
| ロール | セレクト | ✓ | 同上 | `role` | 有効なロール値 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| プロジェクト一覧ページ表示 | `GET /api/v1/project` | 初期ロード |
| フィルタ変更 | `GET /api/v1/project?is_active=` | - |
| プロジェクト詳細表示 | `GET /api/v1/project/{id}` | - |
| セッション一覧取得 | `GET /api/v1/project/{id}/session` | 詳細画面表示時 |
| ツリー一覧取得 | `GET /api/v1/project/{id}/tree` | 詳細画面表示時 |
| プロジェクト作成ボタン | `POST /api/v1/project` | フォーム送信時 |
| プロジェクト編集保存 | `PATCH /api/v1/project/{id}` | - |
| メンバー追加 | `POST /api/v1/project/{id}/member` | モーダル送信時 |
| メンバーロール変更 | `PATCH /api/v1/project/{id}/member/{memberId}` | - |
| メンバー削除 | `DELETE /api/v1/project/{id}/member/{memberId}` | 確認後 |
| ファイル一覧取得 | `GET /api/v1/project/{id}/file` | サイドバー表示時 |
| ファイルアップロード | `POST /api/v1/project/{id}/file` | - |
| ファイルダウンロード | `GET /api/v1/project/{id}/file/{fileId}/download` | - |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | プロジェクトが見つかりませんメッセージ表示 |
| 409 Conflict | プロジェクト名が重複していますメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| 詳細画面 | セッション・ツリー一覧は初期5件表示 |
| ファイルサイドバー | 遅延ロードで初期表示を高速化 |
| キャッシュ | React Query でプロジェクト一覧を5分間キャッシュ |
| 再レンダリング | useMemo でメンバー一覧フィルタを最適化 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| P-001 | プロジェクト一覧を取得する | `GET /projects` | projects | 実装済 |
| P-002 | プロジェクトを作成する | `POST /projects` | project-new | 実装済 |
| P-003 | プロジェクト情報を更新する | `PUT /projects/{id}` | project-detail | 実装済 |
| P-004 | プロジェクトをアーカイブする | `PUT /projects/{id}` | project-detail | 実装済 |
| P-005 | プロジェクト詳細を取得する | `GET /projects/{id}` | project-detail | 実装済 |
| PM-001 | メンバーを追加する | `POST /project/{id}/member` | members | 実装済 |
| PM-002 | メンバーを削除する | `DELETE /project/{id}/member/{id}` | members | 実装済 |
| PM-003 | メンバーのロールを変更する | `PATCH /project/{id}/member/{id}` | members | 実装済 |
| PM-004 | メンバー一覧を取得する | `GET /project/{id}/member` | members | 実装済 |
| PF-001 | ファイル一覧を取得する | `GET /project/{id}/file` | file-sidebar | 実装済 |
| PF-002 | ファイルをアップロードする | `POST /project/{id}/file` | file-sidebar | 実装済 |
| PF-003 | ファイルをダウンロードする | `GET /project/{id}/file/{id}/download` | file-sidebar | 実装済 |
| PF-004 | ファイルを削除する | `DELETE /project/{id}/file/{id}` | file-sidebar | 実装済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| ProjectCard | Default | プロジェクトカード表示 | 通常、アクティブ、アーカイブ済み、ローディング |
| ProjectFilters | Default | プロジェクトフィルタ | 通常、フィルタ適用済み |
| ProjectForm | Create | プロジェクト作成フォーム | 作成、編集、送信中、エラー |
| ProjectStats | Default | プロジェクト統計表示 | 通常、ローディング、空 |
| MemberTable | Default | メンバーテーブル表示 | 通常、空、ローディング、ロール変更 |
| MemberInviteModal | Open | メンバー招待モーダル | 開いた状態、送信中、エラー |
| FileList | Default | ファイル一覧表示 | 通常、空、ローディング |
| FileUploadArea | Default | ファイルアップロードエリア | 通常、アップロード中、成功、エラー |

### 8.2 ストーリー実装例

```tsx
// features/project-management/components/project-card/project-card.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { ProjectCard } from "./project-card";
import type { Project } from "../../types";

const baseProject: Project = {
  id: "1",
  name: "サンプルプロジェクト",
  description: "プロジェクトの説明文です",
  isActive: true,
  createdAt: "2024-01-01T00:00:00Z",
  stats: {
    memberCount: 5,
    sessionCount: 3,
    treeCount: 2,
    fileCount: 10,
  },
};

const meta = {
  title: "features/project-management/components/project-card",
  component: ProjectCard,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: "プロジェクトカードコンポーネント。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onEdit: fn(),
    onArchive: fn(),
    onRestore: fn(),
  },
} satisfies Meta<typeof ProjectCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    project: baseProject,
  },
};

export const Active: Story = {
  args: {
    project: { ...baseProject, isActive: true },
  },
};

export const Archived: Story = {
  args: {
    project: { ...baseProject, isActive: false },
  },
};

export const Loading: Story = {
  args: {
    project: baseProject,
    isLoading: true,
  },
};
```

```tsx
// features/project-management/components/member-table/member-table.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { MemberTable } from "./member-table";
import type { Member } from "../../types";

const mockMembers: Member[] = [
  {
    id: "1",
    user: { displayName: "山田太郎", email: "yamada@example.com" },
    role: "project_manager",
    joinedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "2",
    user: { displayName: "鈴木花子", email: "suzuki@example.com" },
    role: "member",
    joinedAt: "2024-01-15T00:00:00Z",
  },
];

const meta = {
  title: "features/project-management/components/member-table",
  component: MemberTable,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "プロジェクトメンバー一覧テーブルコンポーネント。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onRoleChange: fn(),
    onRemove: fn(),
  },
} satisfies Meta<typeof MemberTable>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    members: mockMembers,
    currentUserId: "1",
    onRoleChange: () => {},
    onRemove: () => {},
  },
};

export const Empty: Story = {
  args: {
    members: [],
    currentUserId: "1",
  },
};

export const Loading: Story = {
  args: {
    members: [],
    isLoading: true,
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | カード表示、フォーム操作、モーダル動作 |
| ユーティリティ | ユニットテスト | 90%以上 | hooks, utils, バリデーション |
| API連携 | 統合テスト | 70%以上 | API呼び出し、状態管理、エラーハンドリング |
| E2E | E2Eテスト | 主要フロー100% | プロジェクト作成、メンバー管理、ファイルアップロード |

### 9.2 ユニットテスト例

```typescript
// features/project-management/hooks/__tests__/use-project-form.test.ts
import { renderHook, act } from "@testing-library/react";
import { useProjectForm } from "../use-project-form";

describe("useProjectForm", () => {
  it("プロジェクト名のバリデーション", () => {
    const { result } = renderHook(() => useProjectForm());

    act(() => {
      result.current.setValue("name", "");
      result.current.trigger("name");
    });

    expect(result.current.errors.name?.message).toBe(
      "プロジェクト名は必須です"
    );
  });

  it("終了日が開始日より前の場合エラー", () => {
    const { result } = renderHook(() => useProjectForm());

    act(() => {
      result.current.setValue("startDate", "2024-12-01");
      result.current.setValue("endDate", "2024-01-01");
      result.current.trigger("endDate");
    });

    expect(result.current.errors.endDate?.message).toBe(
      "終了日は開始日以降を指定してください"
    );
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
// features/project-management/components/project-card/__tests__/project-card.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { ProjectCard } from "../project-card";
import type { Project } from "../../../types";

const mockProject: Project = {
  id: "1",
  name: "テストプロジェクト",
  description: "説明文",
  isActive: true,
  createdAt: "2024-01-01T00:00:00Z",
  stats: { memberCount: 3, sessionCount: 2, treeCount: 1, fileCount: 5 },
};

describe("ProjectCard", () => {
  it("プロジェクト情報を正しく表示する", () => {
    render(<ProjectCard project={mockProject} />);

    expect(screen.getByText("テストプロジェクト")).toBeInTheDocument();
    expect(screen.getByText("説明文")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument(); // メンバー数
  });

  it("編集ボタンクリックでonEditが呼ばれる", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(<ProjectCard project={mockProject} onEdit={onEdit} />);

    await user.click(screen.getByRole("button", { name: /編集/i }));
    expect(onEdit).toHaveBeenCalledWith(mockProject.id);
  });

  it("アクティブ状態でアーカイブボタンを表示", () => {
    render(<ProjectCard project={mockProject} />);

    expect(
      screen.getByRole("button", { name: /アーカイブ/i })
    ).toBeInTheDocument();
  });

  it("アーカイブ状態で復元ボタンを表示", () => {
    render(<ProjectCard project={{ ...mockProject, isActive: false }} />);

    expect(screen.getByRole("button", { name: /復元/i })).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
// e2e/project-management.spec.ts
import { test, expect } from "@playwright/test";

test.describe("プロジェクト管理", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects");
  });

  test("プロジェクト一覧が表示される", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "プロジェクト" })).toBeVisible();
    await expect(page.getByTestId("project-list")).toBeVisible();
  });

  test("新規プロジェクトを作成できる", async ({ page }) => {
    await page.getByRole("button", { name: "新規作成" }).click();
    await page.getByLabel("プロジェクト名").fill("E2Eテストプロジェクト");
    await page.getByLabel("説明").fill("E2Eテスト用のプロジェクトです");
    await page.getByRole("button", { name: "作成" }).click();

    await expect(page.getByText("プロジェクトを作成しました")).toBeVisible();
    await expect(page.getByText("E2Eテストプロジェクト")).toBeVisible();
  });

  test("メンバーを追加できる", async ({ page }) => {
    await page.getByTestId("project-card").first().click();
    await page.getByRole("link", { name: "メンバー管理" }).click();
    await page.getByRole("button", { name: "メンバー追加" }).click();

    await page.getByLabel("ユーザー").click();
    await page.getByRole("option", { name: "鈴木花子" }).click();
    await page.getByLabel("ロール").selectOption("member");
    await page.getByRole("button", { name: "追加" }).click();

    await expect(page.getByText("メンバーを追加しました")).toBeVisible();
  });

  test("ファイルをアップロードできる", async ({ page }) => {
    await page.getByTestId("project-card").first().click();

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles("./fixtures/test-file.xlsx");

    await expect(page.getByText("アップロード完了")).toBeVisible();
    await expect(page.getByText("test-file.xlsx")).toBeVisible();
  });
});
```

### 9.5 モックデータ

```typescript
// features/project-management/__mocks__/handlers.ts
import { http, HttpResponse } from "msw";

export const projectHandlers = [
  http.get("/api/v1/project", () => {
    return HttpResponse.json({
      projects: [
        {
          id: "1",
          name: "モックプロジェクト1",
          description: "テスト用プロジェクト",
          isActive: true,
          createdAt: "2024-01-01T00:00:00Z",
          stats: { memberCount: 5, sessionCount: 3, treeCount: 2, fileCount: 10 },
        },
        {
          id: "2",
          name: "モックプロジェクト2",
          description: "アーカイブ済みプロジェクト",
          isActive: false,
          createdAt: "2023-06-01T00:00:00Z",
          stats: { memberCount: 3, sessionCount: 1, treeCount: 1, fileCount: 5 },
        },
      ],
      total: 2,
    });
  }),

  http.post("/api/v1/project", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: "new-id",
      ...body,
      isActive: true,
      createdAt: new Date().toISOString(),
      stats: { memberCount: 1, sessionCount: 0, treeCount: 0, fileCount: 0 },
    });
  }),

  http.get("/api/v1/project/:id/member", () => {
    return HttpResponse.json({
      members: [
        {
          id: "m1",
          user: { displayName: "山田太郎", email: "yamada@example.com" },
          role: "project_manager",
          joinedAt: "2024-01-01T00:00:00Z",
        },
      ],
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-project-management-design.md](./01-project-management-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **モックアップ**: [../../03-mockup/pages/projects.js](../../03-mockup/pages/projects.js)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | PM-FRONTEND-001 |
| 対象ユースケース | P-001〜P-006, PM-001〜PM-006, PF-001〜PF-006 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/projects/` |
