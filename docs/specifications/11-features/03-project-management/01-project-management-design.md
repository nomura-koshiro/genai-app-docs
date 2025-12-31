# プロジェクト管理 統合設計書（P-001〜PF-006）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのプロジェクト管理機能（ユースケースP-001〜PF-006）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | ユースケースID | 機能概要 |
|---------|---------------|---------|
| プロジェクト基本操作 | P-001 | プロジェクトを作成する |
| | P-002 | プロジェクト情報を更新する |
| | P-003 | プロジェクトを無効化する（論理削除） |
| | P-004 | プロジェクトを有効化する |
| | P-005 | プロジェクト一覧を取得する |
| | P-006 | プロジェクト詳細を取得する |
| | P-007 | プロジェクトコードで検索する |
| プロジェクトメンバー管理 | PM-001 | メンバーをプロジェクトに追加する |
| | PM-002 | メンバーをプロジェクトから削除する |
| | PM-003 | メンバーのロールを変更する |
| | PM-004 | プロジェクトメンバー一覧を取得する |
| | PM-005 | ユーザーが参加しているプロジェクト一覧を取得する |
| | PM-006 | メンバーの権限を確認する |
| プロジェクトファイル管理 | PF-001 | ファイルをアップロードする |
| | PF-002 | ファイルをダウンロードする |
| | PF-003 | ファイルを削除する |
| | PF-004 | プロジェクトのファイル一覧を取得する |
| | PF-005 | ファイル詳細を取得する |
| | PF-006 | ファイルのアップロード者を確認する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 3テーブル（project, project_member, project_file） |
| APIエンドポイント | 18エンドポイント |
| Pydanticスキーマ | 20スキーマ |
| サービス | 3サービス |
| フロントエンド画面 | 6画面 |

---

## 2. データベース設計

### 2.1 project（プロジェクト）

**対応ユースケース**: P-001〜P-007

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(255) | NO | プロジェクト名 |
| code | VARCHAR(50) | NO | プロジェクトコード（ユニーク） |
| description | TEXT | YES | プロジェクト説明 |
| is_active | BOOLEAN | NO | アクティブフラグ（デフォルト: true） |
| created_by | UUID | YES | 作成者ユーザーID |
| start_date | DATE | YES | プロジェクト開始日 |
| end_date | DATE | YES | プロジェクト終了日 |
| budget | NUMERIC(15,2) | YES | プロジェクト予算 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

**インデックス**:

- `idx_projects_code` ON (code) UNIQUE

### 2.2 project_member（プロジェクトメンバー）

**対応ユースケース**: PM-001〜PM-006

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| project_id | UUID | NO | プロジェクトID（FK: project） |
| user_id | UUID | NO | ユーザーID（FK: user_account） |
| role | VARCHAR(50) | NO | プロジェクトロール |
| joined_at | TIMESTAMP | NO | 参加日時 |
| added_by | UUID | YES | 追加者ユーザーID |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

**プロジェクトロール**:

- `project_manager`: プロジェクト管理者（全操作可能）
- `project_moderator`: モデレーター（コンテンツ管理）
- `member`: 一般メンバー（作成・編集可能）
- `viewer`: 閲覧者（閲覧のみ）

**インデックス**:

- `idx_project_member_project` ON (project_id)
- `idx_project_member_user` ON (user_id)
- `uq_project_member` ON (project_id, user_id) UNIQUE

### 2.3 project_file（プロジェクトファイル）

**対応ユースケース**: PF-001〜PF-006

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| project_id | UUID | NO | プロジェクトID（FK: project） |
| filename | VARCHAR(255) | NO | 保存ファイル名 |
| original_filename | VARCHAR(255) | NO | 元のファイル名 |
| file_path | VARCHAR(500) | NO | ファイルパス |
| file_size | BIGINT | NO | ファイルサイズ（バイト） |
| mime_type | VARCHAR(100) | YES | MIMEタイプ |
| uploaded_by | UUID | NO | アップロード者ID |
| version | INTEGER | NO | バージョン番号（デフォルト: 1） |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

**インデックス**:

- `idx_project_file_project` ON (project_id)
- `idx_project_file_uploaded_by` ON (uploaded_by)

---

## 3. APIエンドポイント設計

### 3.1 プロジェクト基本操作

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project` | プロジェクト一覧取得 | 認証済 | P-005, PM-005 |
| GET | `/api/v1/project/{project_id}` | プロジェクト詳細取得 | メンバー | P-006 |
| GET | `/api/v1/project/code/{code}` | コードでプロジェクト検索 | メンバー | P-007 |
| POST | `/api/v1/project` | プロジェクト作成 | 認証済 | P-001 |
| PATCH | `/api/v1/project/{project_id}` | プロジェクト更新 | PM/Admin | P-002, P-003, P-004 |
| DELETE | `/api/v1/project/{project_id}` | プロジェクト削除 | PM | - |

### 3.2 プロジェクトメンバー管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project/{project_id}/member` | メンバー一覧取得 | メンバー | PM-004 |
| GET | `/api/v1/project/{project_id}/member/me` | 自分のロール取得 | メンバー | PM-006 |
| POST | `/api/v1/project/{project_id}/member` | メンバー追加 | PM | PM-001 |
| POST | `/api/v1/project/{project_id}/member/bulk` | メンバー一括追加 | PM | PM-001 |
| PATCH | `/api/v1/project/{project_id}/member/{member_id}` | ロール更新 | PM | PM-003 |
| DELETE | `/api/v1/project/{project_id}/member/{member_id}` | メンバー削除 | PM | PM-002 |
| DELETE | `/api/v1/project/{project_id}/member/me` | プロジェクト退出 | メンバー | - |

### 3.3 プロジェクトファイル管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project/{project_id}/file` | ファイル一覧取得 | メンバー | PF-004 |
| GET | `/api/v1/project/{project_id}/file/{file_id}` | ファイル詳細取得 | メンバー | PF-005, PF-006 |
| GET | `/api/v1/project/{project_id}/file/{file_id}/download` | ファイルダウンロード | メンバー | PF-002 |
| POST | `/api/v1/project/{project_id}/file` | ファイルアップロード | メンバー | PF-001 |
| DELETE | `/api/v1/project/{project_id}/file/{file_id}` | ファイル削除 | PM/Mod | PF-003 |

### 3.4 主要レスポンス定義

#### ProjectDetailResponse

```json
{
  "id": "uuid",
  "name": "string",
  "code": "string",
  "description": "string",
  "isActive": true,
  "createdBy": "uuid",
  "startDate": "date",
  "endDate": "date",
  "budget": "decimal",
  "createdAt": "datetime",
  "updatedAt": "datetime",
  "stats": {
    "memberCount": 5,
    "fileCount": 10,
    "sessionCount": 2,
    "treeCount": 1
  }
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 プロジェクトスキーマ

| スキーマ名 | 用途 |
|-----------|------|
| ProjectBase | 基底スキーマ |
| ProjectCreate | 作成リクエスト |
| ProjectUpdate | 更新リクエスト |
| ProjectResponse | レスポンス |
| ProjectListResponse | 一覧レスポンス |
| ProjectDetailResponse | 詳細レスポンス |
| ProjectStatsResponse | 統計情報 |

### 4.2 メンバースキーマ

| スキーマ名 | 用途 |
|-----------|------|
| ProjectMemberCreate | 追加リクエスト |
| ProjectMemberBulkCreate | 一括追加リクエスト |
| ProjectMemberUpdate | 更新リクエスト |
| ProjectMemberDetailResponse | 詳細レスポンス |
| ProjectMemberListResponse | 一覧レスポンス |
| UserRoleResponse | ロール確認レスポンス |

### 4.3 ファイルスキーマ

| スキーマ名 | 用途 |
|-----------|------|
| ProjectFileResponse | レスポンス |
| ProjectFileListResponse | 一覧レスポンス |
| ProjectFileUploadResponse | アップロードレスポンス |
| ProjectFileDeleteResponse | 削除レスポンス |
| ProjectFileVersionHistoryResponse | バージョン履歴 |

---

## 5. サービス層設計

### 5.1 ProjectService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `create_project(data, user_id)` | プロジェクト作成 | P-001 |
| `update_project(project_id, data)` | プロジェクト更新 | P-002 |
| `list_user_projects(user_id, skip, limit, is_active)` | ユーザーのプロジェクト一覧 | P-005, PM-005 |
| `get_project(project_id)` | プロジェクト詳細取得 | P-006 |
| `get_project_by_code(code)` | コードで検索 | P-007 |
| `delete_project(project_id)` | プロジェクト削除 | - |

### 5.2 ProjectMemberService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `add_member(project_id, user_id, role, added_by)` | メンバー追加 | PM-001 |
| `add_members_bulk(project_id, members, added_by)` | 一括追加 | PM-001 |
| `remove_member(project_id, member_id)` | メンバー削除 | PM-002 |
| `update_member_role(project_id, member_id, role)` | ロール更新 | PM-003 |
| `list_members(project_id, skip, limit)` | メンバー一覧 | PM-004 |
| `get_user_role(project_id, user_id)` | ユーザーロール取得 | PM-006 |
| `leave_project(project_id, user_id)` | プロジェクト退出 | - |

### 5.3 ProjectFileService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `upload_file(project_id, file, user_id)` | ファイルアップロード | PF-001 |
| `download_file(project_id, file_id)` | ファイルダウンロード | PF-002 |
| `delete_file(project_id, file_id)` | ファイル削除 | PF-003 |
| `list_files(project_id, skip, limit, mime_type)` | ファイル一覧 | PF-004 |
| `get_file(project_id, file_id)` | ファイル詳細 | PF-005, PF-006 |

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| projects | プロジェクト一覧 | `/projects` | プロジェクト一覧表示・検索 |
| project-new | プロジェクト作成 | `/projects/new` | 新規プロジェクト作成フォーム |
| project-detail | プロジェクト詳細 | `/projects/{id}` | プロジェクト詳細・統計表示 |
| members | メンバー管理 | `/projects/{id}/members` | メンバー一覧・追加・削除 |
| files | ファイル管理 | `/projects/{id}/files` | ファイル一覧・アップロード |
| upload | ファイルアップロード | `/projects/{id}/upload` | ファイルアップロード画面 |

### 6.2 コンポーネント構成

```text
pages/projects/
├── index.tsx              # プロジェクト一覧
├── new.tsx                # プロジェクト作成
└── [id]/
    ├── index.tsx          # プロジェクト詳細
    ├── members.tsx        # メンバー管理
    ├── files.tsx          # ファイル管理
    └── upload.tsx         # ファイルアップロード
```

---

## 7. 画面項目・APIマッピング

### 7.1 プロジェクト一覧画面（projects）

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

### 7.2 プロジェクト作成画面（project-new）

#### 入力項目

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| プロジェクト名 | テキスト | ✓ | `POST /api/v1/project` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | - |
| 開始日 | 日付 | - | 同上 | `startDate` | - |
| 終了予定日 | 日付 | - | 同上 | `endDate` | 開始日以降 |
| 初期メンバー | 複数選択 | - | 別途メンバー追加API | - | - |

### 7.3 プロジェクト詳細画面（project-detail）

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

#### 統計セクション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| セッション数 | 数値 | `GET /api/v1/project/{id}` | `stats.sessionCount` | - |
| スナップショット数 | 数値 | 同上 | 別途計算 | - |
| ツリー数 | 数値 | 同上 | `stats.treeCount` | - |
| ファイル数 | 数値 | 同上 | `stats.fileCount` | - |

### 7.4 メンバー管理画面（members）

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー（アイコン+名前） | アイコン+テキスト | `GET /api/v1/project/{id}/member` | `members[].user.displayName` | - |
| メールアドレス | テキスト | 同上 | `members[].user.email` | - |
| ロール | バッジ | 同上 | `members[].role` | ロール名→バッジ色 |
| 追加日 | 日付 | 同上 | `members[].joinedAt` | ISO8601→YYYY/MM/DD |
| ロール変更 | セレクト | `PATCH .../member/{id}` | `role` | PM以外表示 |
| 削除ボタン | ボタン | `DELETE .../member/{id}` | - | 作成者は削除不可 |

#### ロール色マッピング

| ロール | バッジ色 | 説明 |
|--------|---------|------|
| project_manager | info | プロジェクト管理者 |
| project_moderator | warning | モデレーター |
| member | success | 一般メンバー |
| viewer | neutral | 閲覧者 |

#### メンバー追加モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ユーザー選択 | セレクト | ✓ | `POST /api/v1/project/{id}/member` | `userId` | 既存メンバー除外 |
| ロール | セレクト | ✓ | 同上 | `role` | 有効なロール値 |

### 7.5 ファイル管理サイドバー

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

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| P-001 | プロジェクトを作成する | `POST /project` | project-new | 実装済 |
| P-002 | プロジェクト情報を更新する | `PATCH /project/{id}` | project-detail | 実装済 |
| P-003 | プロジェクトを無効化する | `PATCH /project/{id}` | projects | 実装済 |
| P-004 | プロジェクトを有効化する | `PATCH /project/{id}` | projects | 実装済 |
| P-005 | プロジェクト一覧を取得する | `GET /project` | projects | 実装済 |
| P-006 | プロジェクト詳細を取得する | `GET /project/{id}` | project-detail | 実装済 |
| P-007 | プロジェクトコードで検索する | `GET /project/code/{code}` | - | 実装済 |
| PM-001 | メンバーを追加する | `POST /project/{id}/member` | members | 実装済 |
| PM-002 | メンバーを削除する | `DELETE /project/{id}/member/{id}` | members | 実装済 |
| PM-003 | メンバーのロールを変更する | `PATCH /project/{id}/member/{id}` | members | 実装済 |
| PM-004 | メンバー一覧を取得する | `GET /project/{id}/member` | members | 実装済 |
| PM-005 | 参加プロジェクト一覧を取得する | `GET /project` | projects | 実装済 |
| PM-006 | メンバーの権限を確認する | `GET /project/{id}/member/me` | - | 実装済 |
| PF-001 | ファイルをアップロードする | `POST /project/{id}/file` | upload | 実装済 |
| PF-002 | ファイルをダウンロードする | `GET /project/{id}/file/{id}/download` | files | 実装済 |
| PF-003 | ファイルを削除する | `DELETE /project/{id}/file/{id}` | files | 実装済 |
| PF-004 | ファイル一覧を取得する | `GET /project/{id}/file` | files, project-detail | 実装済 |
| PF-005 | ファイル詳細を取得する | `GET /project/{id}/file/{id}` | files | 実装済 |
| PF-006 | アップロード者を確認する | `GET /project/{id}/file/{id}` | files | 実装済 |

---

## 9. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/projects.js](../../03-mockup/pages/projects.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **対象ソースコード**:
  - モデル: `src/app/models/project/`
  - スキーマ: `src/app/schemas/project/`
  - API: `src/app/api/routes/v1/project/`
