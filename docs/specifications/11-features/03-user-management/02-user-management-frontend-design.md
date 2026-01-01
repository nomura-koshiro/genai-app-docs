# ユーザー管理 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| users | ユーザー一覧 | `/admin/users` | ユーザー一覧表示・検索・フィルタ |
| user-detail | ユーザー詳細 | `/admin/users/{id}` | ユーザー詳細表示・編集 |
| roles | ロール管理 | `/admin/roles` | システムロール・プロジェクトロール一覧 |

### 1.2 コンポーネント構成

```text
pages/admin/
├── users/
│   ├── index.tsx          # ユーザー一覧
│   └── [id].tsx           # ユーザー詳細
└── roles/
    └── index.tsx          # ロール管理
```

---

## 2. 画面詳細設計

### 2.1 ユーザー一覧画面（users）

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

### 2.2 ユーザー詳細画面（user-detail）

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

### 2.3 ロール管理画面（roles）

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

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| U-003 | ユーザー情報を更新する | `PATCH /user_account/me` | user-detail | 実装済 |
| U-004 | ユーザーを無効化する | `PATCH /user_account/{id}/deactivate` | users, user-detail | 実装済 |
| U-005 | ユーザーを有効化する | `PATCH /user_account/{id}/activate` | users, user-detail | 実装済 |
| U-007 | ユーザー一覧を取得する | `GET /user_account` | users | 実装済 |
| U-008 | ユーザー詳細を取得する | `GET /user_account/{id}` | user-detail | 実装済 |
| U-009 | システムロールを付与する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-010 | システムロールを剥奪する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-011 | ユーザーのロールを確認する | `GET /user_account/{id}/role_history` | user-detail | 実装済 |

---

## 8. 関連ドキュメント

- **バックエンド設計書**: [01-user-management-design.md](./01-user-management-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **モックアップ**: [../../03-mockup/pages/admin.js](../../03-mockup/pages/admin.js)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | UM-FRONTEND-001 |
| 対象ユースケース | U-003〜U-011 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `pages/admin/users/` |
|  | `pages/admin/roles/` |
