# ユーザー管理 統合設計書（U-001〜U-011）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのユーザー管理機能（ユースケースU-001〜U-011）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | ユースケースID | 機能概要 |
|---------|---------------|---------|
| 認証・アカウント管理 | U-001 | Azure ADでログインする |
| | U-002 | ユーザーアカウントを作成する |
| | U-003 | ユーザー情報を更新する |
| | U-004 | ユーザーを無効化する（論理削除） |
| | U-005 | ユーザーを有効化する |
| | U-006 | 最終ログイン日時を記録する |
| | U-007 | ユーザー一覧を取得する |
| | U-008 | ユーザー詳細を取得する |
| ロール管理 | U-009 | システムロールを付与する |
| | U-010 | システムロールを剥奪する |
| | U-011 | ユーザーのロールを確認する |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 2テーブル（user_account, role_history） |
| APIエンドポイント | 9エンドポイント |
| Pydanticスキーマ | 8スキーマ |
| サービス | 2サービス |
| フロントエンド画面 | 3画面 |

---

## 2. データベース設計

### 2.1 user_account（ユーザーアカウント）

**対応ユースケース**: U-001〜U-008

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| azure_id | VARCHAR(255) | NO | Azure AD Object ID（ユニーク） |
| email | VARCHAR(255) | NO | メールアドレス（ユニーク） |
| display_name | VARCHAR(255) | YES | 表示名 |
| roles | JSON | NO | システムロール（例: ["system_admin", "user"]） |
| is_active | BOOLEAN | NO | アクティブフラグ（デフォルト: true） |
| last_login | TIMESTAMP | YES | 最終ログイン日時 |
| login_count | INTEGER | NO | ログイン回数（デフォルト: 0） |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

**インデックス**:

- `idx_users_azure_id` ON (azure_id) UNIQUE
- `idx_users_email` ON (email) UNIQUE

### 2.2 role_history（ロール変更履歴）

**対応ユースケース**: U-009〜U-011

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | NO | ユーザーID（FK: user_account） |
| old_roles | JSON | YES | 変更前ロール |
| new_roles | JSON | NO | 変更後ロール |
| changed_by | UUID | YES | 変更者ID（FK: user_account） |
| reason | TEXT | YES | 変更理由 |
| created_at | TIMESTAMP | NO | 作成日時 |

**インデックス**:

- `idx_role_history_user_id` ON (user_id)
- `idx_role_history_created_at` ON (created_at DESC)

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/user_account` | ユーザー一覧取得 | system_admin | U-007 |
| GET | `/api/v1/user_account/me` | 現在のユーザー情報取得 | 認証済 | U-008, U-006 |
| GET | `/api/v1/user_account/{user_id}` | 特定ユーザー情報取得 | system_admin | U-008 |
| PATCH | `/api/v1/user_account/me` | 現在のユーザー情報更新 | 認証済 | U-003 |
| PATCH | `/api/v1/user_account/{user_id}/activate` | ユーザー有効化 | system_admin | U-005 |
| PATCH | `/api/v1/user_account/{user_id}/deactivate` | ユーザー無効化 | system_admin | U-004 |
| PUT | `/api/v1/user_account/{user_id}/role` | ユーザーロール更新 | system_admin | U-009, U-010 |
| DELETE | `/api/v1/user_account/{user_id}` | ユーザー削除 | system_admin | - |
| GET | `/api/v1/user_account/{user_id}/role_history` | ロール変更履歴取得 | system_admin/本人 | U-011 |

### 3.2 リクエスト/レスポンス定義

#### GET /api/v1/user_account（ユーザー一覧取得）

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| skip | int | - | スキップ数（デフォルト: 0） |
| limit | int | - | 取得件数（デフォルト: 100、最大: 1000） |
| azure_id | string | - | Azure AD Object IDで検索 |
| email | string | - | メールアドレスで検索 |

**レスポンス**: `UserAccountListResponse`

```json
{
  "users": [
    {
      "id": "uuid",
      "azureId": "string",
      "email": "string",
      "displayName": "string",
      "roles": ["string"],
      "isActive": true,
      "createdAt": "datetime",
      "updatedAt": "datetime",
      "lastLogin": "datetime",
      "loginCount": 0
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

#### PUT /api/v1/user_account/{user_id}/role（ロール更新）

**リクエストボディ**: `UserAccountRoleUpdate`

```json
{
  "roles": ["system_admin", "user"]
}
```

**レスポンス**: `UserAccountResponse`

---

## 4. Pydanticスキーマ設計

| スキーマ名 | 用途 | フィールド |
|-----------|------|-----------|
| UserAccountBase | 基底スキーマ | email, display_name, roles |
| UserAccountUpdate | 更新リクエスト | display_name?, roles?, is_active? |
| UserAccountResponse | レスポンス | id, azure_id, email, display_name, roles, is_active, created_at, updated_at, last_login, login_count |
| UserAccountListResponse | 一覧レスポンス | users, total, skip, limit |
| UserAccountRoleUpdate | ロール更新リクエスト | roles |
| UserActivityStats | 統計情報 | project_count, session_count, tree_count |
| ProjectParticipationResponse | 参加プロジェクト | project_id, project_name, project_role, joined_at, status |
| RecentActivityResponse | 最近のアクティビティ | activity_type, activity_detail, activity_at, project_name |
| UserAccountDetailResponse | 詳細レスポンス | UserAccountResponse + stats + projects + recent_activities |
| RoleHistoryListResponse | ロール履歴一覧 | histories, total, skip, limit |

---

## 5. サービス層設計

### 5.1 UserAccountService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `list_users(skip, limit)` | ユーザー一覧取得 | U-007 |
| `count_users()` | ユーザー総数取得 | U-007 |
| `get_user(user_id)` | ユーザー取得 | U-008 |
| `get_user_by_azure_id(azure_id)` | Azure IDでユーザー取得 | U-001 |
| `get_user_by_email(email)` | メールでユーザー取得 | U-007 |
| `get_user_stats(user_id)` | ユーザー統計情報取得 | U-008 |
| `get_user_projects(user_id)` | ユーザー参加プロジェクト取得 | U-008 |
| `get_user_recent_activities(user_id, limit)` | ユーザー最近のアクティビティ取得 | U-008 |
| `update_user(user_id, update_data, current_user_roles)` | ユーザー情報更新 | U-003 |
| `update_last_login(user_id, client_ip)` | 最終ログイン更新 | U-006 |
| `activate_user(user_id)` | ユーザー有効化 | U-005 |
| `deactivate_user(user_id)` | ユーザー無効化 | U-004 |
| `update_user_role(user_id, roles)` | ロール更新 | U-009, U-010 |
| `delete_user(user_id)` | ユーザー削除 | - |

### 5.2 RoleHistoryService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `get_user_role_history(user_id, skip, limit)` | ロール変更履歴取得 | U-011 |
| `create_role_history(user_id, old_roles, new_roles, changed_by, reason)` | 履歴作成 | U-009, U-010 |

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| users | ユーザー一覧 | `/admin/users` | ユーザー一覧表示・検索・フィルタ |
| user-detail | ユーザー詳細 | `/admin/users/{id}` | ユーザー詳細表示・編集 |
| roles | ロール管理 | `/admin/roles` | システムロール・プロジェクトロール一覧 |

### 6.2 コンポーネント構成

```text
pages/admin/
├── users/
│   ├── index.tsx          # ユーザー一覧
│   └── [id].tsx           # ユーザー詳細
└── roles/
    └── index.tsx          # ロール管理
```

---

## 7. 画面項目・APIマッピング

### 7.1 ユーザー一覧画面（users）

#### 検索・フィルタ項目

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|------------------|-----------------|------|
| 名前/メール検索 | テキスト | `GET /api/v1/user_account` | `email` | 完全一致 |
| ロールフィルタ | セレクト | 同上 | - | フロントでフィルタ |
| ステータスフィルタ | セレクト | 同上 | - | フロントでフィルタ |

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー（アイコン+名前） | アイコン+テキスト | `GET /api/v1/user_account` | `users[].displayName` | アイコンは固定表示 |
| メールアドレス | テキスト | 同上 | `users[].email` | - |
| システムロール | バッジ | 同上 | `users[].roles` | `system_admin`→"ADMIN"(danger), `user`→"SYSTEM_USER"(info) |
| ステータス | バッジ | 同上 | `users[].isActive` | `true`→"有効"(success), `false`→"無効"(danger) |
| 最終ログイン | 日時 | 同上 | `users[].lastLogin` | ISO8601→YYYY/MM/DD HH:mm |
| 詳細ボタン | ボタン | - | - | user-detail画面へ遷移 |
| 無効化/有効化ボタン | ボタン | `PATCH .../activate` or `deactivate` | - | isActiveにより切替 |

#### ページネーション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ページ番号 | ボタン群 | `GET /api/v1/user_account` | `total`, `skip`, `limit` | `Math.ceil(total / limit)` でページ数計算 |

### 7.2 ユーザー詳細画面（user-detail）

#### アカウント情報

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザーID | テキスト | `GET /api/v1/user_account/{id}` | `id` | UUID表示 |
| Azure ID | テキスト | 同上 | `azureId` | - |
| メールアドレス | テキスト | 同上 | `email` | - |
| 表示名 | テキスト | 同上 | `displayName` | - |
| システムロール | バッジ群 | 同上 | `roles` | 配列をバッジ群として表示 |
| ステータス | バッジ | 同上 | `isActive` | boolean→バッジ変換 |
| 作成日時 | 日時 | 同上 | `createdAt` | ISO8601→YYYY/MM/DD HH:mm:ss |
| 更新日時 | 日時 | 同上 | `updatedAt` | ISO8601→YYYY/MM/DD HH:mm:ss |
| 最終ログイン | 日時 | 同上 | `lastLogin` | ISO8601→YYYY/MM/DD HH:mm:ss |
| ログイン回数 | 数値 | 同上 | `loginCount` | 数値表示 |

#### 統計情報

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 参加プロジェクト数 | 数値 | `GET /api/v1/user_account/{id}` | `stats.projectCount` | 数値表示 |
| 作成セッション数 | 数値 | 同上 | `stats.sessionCount` | 数値表示 |
| 作成ツリー数 | 数値 | 同上 | `stats.treeCount` | 数値表示 |

#### 参加プロジェクト一覧

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | リンク | `GET /api/v1/user_account/{id}` | `projects[].projectName` | プロジェクト詳細画面へのリンク |
| プロジェクトロール | バッジ | 同上 | `projects[].projectRole` | ロールに応じたバッジ表示 |
| 参加日 | 日時 | 同上 | `projects[].joinedAt` | ISO8601→YYYY/MM/DD |
| ステータス | バッジ | 同上 | `projects[].status` | `active`→"アクティブ"(success) |

#### 最近のアクティビティ

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| アクティビティ内容 | テキスト | `GET /api/v1/user_account/{id}` | `recentActivities[].activityType` + `activityDetail` | "セッション作成: セッション名" など |
| 時刻 | 日時 | 同上 | `recentActivities[].activityAt` | ISO8601→YYYY/MM/DD HH:mm |
| プロジェクト名 | テキスト | 同上 | `recentActivities[].projectName` | プロジェクト名表示 |

#### 編集項目

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 表示名 | テキスト | - | `PATCH /api/v1/user_account/me` | `displayName` | 最大255文字 |
| システムロール | セレクト（単一選択） | ✓ | `PUT /api/v1/user_account/{id}/role` | `roles` | system_admin または user を選択 |

#### アクション

| 画面項目 | 操作 | APIエンドポイント | 備考 |
|---------|-----|------------------|------|
| 有効化ボタン | クリック | `PATCH /api/v1/user_account/{id}/activate` | 無効ユーザーのみ表示 |
| 無効化ボタン | クリック | `PATCH /api/v1/user_account/{id}/deactivate` | 有効ユーザーかつ自分以外 |
| 削除ボタン | クリック | `DELETE /api/v1/user_account/{id}` | 確認ダイアログ表示 |

### 7.3 ロール管理画面（roles）

#### システムロール一覧

| 画面項目 | 表示形式 | データソース | 備考 |
|---------|---------|-------------|------|
| ロール名 | バッジ | 固定値 | ADMIN, SYSTEM_USER |
| 説明 | テキスト | 固定値 | 定義済み説明文 |
| 権限 | テキスト | 固定値 | 権限説明文 |

#### プロジェクトロール一覧

| 画面項目 | 表示形式 | データソース | 備考 |
|---------|---------|-------------|------|
| ロール名 | バッジ | 固定値 | PROJECT_MANAGER, MODERATOR, MEMBER, VIEWER |
| 説明 | テキスト | 固定値 | 定義済み説明文 |
| 権限 | テキスト | 固定値 | 権限説明文 |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| U-001 | Azure ADでログインする | Azure AD認証 | - | 実装済 |
| U-002 | ユーザーアカウントを作成する | 初回ログイン時自動作成 | - | 実装済 |
| U-003 | ユーザー情報を更新する | `PATCH /user_account/me` | user-detail | 実装済 |
| U-004 | ユーザーを無効化する | `PATCH /user_account/{id}/deactivate` | users, user-detail | 実装済 |
| U-005 | ユーザーを有効化する | `PATCH /user_account/{id}/activate` | users, user-detail | 実装済 |
| U-006 | 最終ログイン日時を記録する | `GET /user_account/me` | - | 実装済 |
| U-007 | ユーザー一覧を取得する | `GET /user_account` | users | 実装済 |
| U-008 | ユーザー詳細を取得する | `GET /user_account/{id}` | user-detail | 実装済 |
| U-009 | システムロールを付与する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-010 | システムロールを剥奪する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-011 | ユーザーのロールを確認する | `GET /user_account/{id}/role_history` | user-detail | 実装済 |

---

## 9. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/admin.js](../../03-mockup/pages/admin.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **対象ソースコード**:
  - モデル: `src/app/models/user_account/user_account.py`
  - スキーマ: `src/app/schemas/user_account/user_account.py`
  - API: `src/app/api/routes/v1/user_accounts/user_account.py`
