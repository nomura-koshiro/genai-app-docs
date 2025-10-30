# API仕様概要

このドキュメントは、実装されているAPIエンドポイントの仕様を詳述します。すべての仕様は実装から抽出されています。

## エンドポイント一覧

### ユーザー管理 (/api/v1/users)

| メソッド | パス | 説明 | 認証 | ロール |
|---------|------|------|------|--------|
| GET | /me | 現在のユーザー情報取得 | 必須 | - |
| PATCH | /me | 現在のユーザー情報更新 | 必須 | - |
| GET | / | ユーザー一覧取得 | 必須 | SystemAdmin |
| GET | /{user_id} | ユーザー詳細取得 | 必須 | SystemAdmin |
| DELETE | /{user_id} | ユーザー削除 | 必須 | SystemAdmin |

#### GET /api/v1/users/me - 現在のユーザー情報取得

**説明**: Azure AD認証されたユーザー自身の情報を取得します。同時に、最終ログイン情報を更新します。

**認証**: 必須（Azure AD Bearer認証）

**レスポンス**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "azure_oid": "azure-oid-12345",
  "email": "user@example.com",
  "display_name": "山田太郎",
  "roles": ["User"],
  "is_active": true,
  "created_at": "2025-10-15T10:30:00Z",
  "updated_at": "2025-10-28T14:22:00Z",
  "last_login": "2025-10-30T09:15:00Z"
}
```

**注意事項**:

- このエンドポイントを呼び出すたびに `last_login` が更新されます
- クライアントIPアドレスは監査ログに記録されます

#### PATCH /api/v1/users/me - 現在のユーザー情報更新

**説明**: 現在のユーザー情報を更新します。一部のフィールドの更新には管理者権限が必要です。

**認証**: 必須

**更新可能なフィールド**:

- `display_name`: 表示名（全ユーザー）
- `roles`: システムレベルのロール（SystemAdminのみ）
- `is_active`: アクティブフラグ（SystemAdminのみ）

**リクエストボディ**:

```json
{
  "display_name": "山田 太郎"
}
```

**レスポンス**: 更新されたユーザー情報（GET /me と同じ形式）

**注意事項**:

- `email` と `azure_oid` は更新できません（Azure ADで管理）
- `roles` や `is_active` の更新を試みた場合、SystemAdmin権限がないと403エラー

#### GET /api/v1/users - ユーザー一覧取得

**説明**: 登録されているすべてのユーザーの一覧を取得します。

**認証**: 必須

**権限**: SystemAdmin

**クエリパラメータ**:

- `skip`: スキップするレコード数（デフォルト: 0）
- `limit`: 取得する最大レコード数（デフォルト: 100、最大: 1000）

**レスポンス**:

```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "azure_oid": "azure-oid-12345",
      "email": "user@example.com",
      "display_name": "山田太郎",
      "roles": ["User"],
      "is_active": true,
      "created_at": "2025-10-15T10:30:00Z",
      "updated_at": "2025-10-28T14:22:00Z",
      "last_login": "2025-10-30T09:15:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

#### GET /api/v1/users/{user_id} - ユーザー詳細取得

**説明**: 指定されたIDのユーザー情報を取得します。

**認証**: 必須

**権限**: SystemAdmin

**パスパラメータ**:

- `user_id`: ユーザーID（UUID形式）

**レスポンス**: GET /me と同じ形式

#### DELETE /api/v1/users/{user_id} - ユーザー削除

**説明**: 指定されたIDのユーザーを削除します。

**認証**: 必須

**権限**: SystemAdmin

**パスパラメータ**:

- `user_id`: ユーザーID（UUID形式）

**レスポンス**: 204 No Content

**注意事項**:

- 削除は物理削除です（データベースから完全に削除されます）
- CASCADE設定により、関連する ProjectMember も自動削除されます
- 自分自身を削除することはできません
- この操作は取り消せません

---

### プロジェクト管理 (/api/v1/projects)

| メソッド | パス | 説明 | 認証 | ロール |
|---------|------|------|------|--------|
| POST | / | プロジェクト作成 | 必須 | - |
| GET | / | プロジェクト一覧取得 | 必須 | - |
| GET | /{project_id} | プロジェクト詳細取得 | 必須 | メンバー |
| GET | /code/{code} | プロジェクトコード検索 | 必須 | メンバー |
| PATCH | /{project_id} | プロジェクト更新 | 必須 | Owner/Admin |
| DELETE | /{project_id} | プロジェクト削除 | 必須 | Owner |

#### POST /api/v1/projects - プロジェクト作成

**説明**: 新しいプロジェクトを作成します。作成者は自動的にOWNERロールとして追加されます。

**認証**: 必須

**リクエストボディ**:

```json
{
  "name": "AIプロジェクト",
  "code": "AI-001",
  "description": "AI開発プロジェクト"
}
```

**フィールド説明**:

- `name`: プロジェクト名（必須、最大255文字）
- `code`: プロジェクトコード（必須、最大50文字、一意）
- `description`: プロジェクト説明（オプション）

**レスポンス** (201 Created):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "AIプロジェクト",
  "code": "AI-001",
  "description": "AI開発プロジェクト",
  "is_active": true,
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-01T09:00:00Z",
  "updated_at": "2025-10-01T09:00:00Z"
}
```

#### GET /api/v1/projects - プロジェクト一覧取得

**説明**: 認証されたユーザーが所属するプロジェクトの一覧を取得します。

**認証**: 必須

**クエリパラメータ**:

- `skip`: スキップするレコード数（デフォルト: 0）
- `limit`: 取得する最大レコード数（デフォルト: 100、最大: 1000）
- `is_active`: アクティブフラグフィルタ（オプション）

**レスポンス**:

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "AIプロジェクト",
    "code": "AI-001",
    "description": "AI開発プロジェクト",
    "is_active": true,
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-10-01T09:00:00Z",
    "updated_at": "2025-10-20T15:30:00Z"
  }
]
```

**注意事項**:

- 自分がメンバーとして所属するプロジェクトのみ表示されます
- ロール（OWNER/ADMIN/MEMBER/VIEWER）に関係なく全て取得されます

#### GET /api/v1/projects/{project_id} - プロジェクト詳細取得

**説明**: 指定されたIDのプロジェクト情報を取得します。

**認証**: 必須

**権限**: プロジェクトメンバー

**パスパラメータ**:

- `project_id`: プロジェクトID（UUID形式）

**レスポンス**: POST /api/v1/projects と同じ形式

#### GET /api/v1/projects/code/{code} - プロジェクトコード検索

**説明**: 指定されたコードのプロジェクト情報を取得します。

**認証**: 必須

**権限**: プロジェクトメンバー

**パスパラメータ**:

- `code`: プロジェクトコード

**レスポンス**: POST /api/v1/projects と同じ形式

#### PATCH /api/v1/projects/{project_id} - プロジェクト更新

**説明**: プロジェクト情報を更新します。

**認証**: 必須

**権限**: OWNER/ADMIN

**パスパラメータ**:

- `project_id`: プロジェクトID（UUID形式）

**更新可能なフィールド**:

- `name`: プロジェクト名
- `description`: プロジェクト説明
- `is_active`: アクティブフラグ

**リクエストボディ**:

```json
{
  "name": "AIプロジェクト（更新版）",
  "description": "更新された説明"
}
```

**レスポンス**: 更新されたプロジェクト情報

**注意事項**:

- `code`（プロジェクトコード）は更新できません

#### DELETE /api/v1/projects/{project_id} - プロジェクト削除

**説明**: プロジェクトを削除します。

**認証**: 必須

**権限**: OWNER

**パスパラメータ**:

- `project_id`: プロジェクトID（UUID形式）

**レスポンス**: 204 No Content

**注意事項**:

- 削除は物理削除です（データベースから完全に削除されます）
- CASCADE設定により、関連する ProjectMember と ProjectFile も自動削除されます
- この操作は取り消せません

---

### プロジェクトメンバー (/api/v1/projects/{project_id}/members)

| メソッド | パス | 説明 | 認証 | ロール |
|---------|------|------|------|--------|
| POST | / | メンバー追加 | 必須 | Owner/Admin |
| GET | / | メンバー一覧取得 | 必須 | メンバー |
| GET | /me | 自分のロール取得 | 必須 | メンバー |
| PATCH | /{member_id} | メンバーロール更新 | 必須 | Owner/Admin |
| DELETE | /{member_id} | メンバー削除 | 必須 | Owner/Admin |
| DELETE | /me | プロジェクト退出 | 必須 | メンバー |

#### POST /api/v1/projects/{project_id}/members - メンバー追加

**説明**: プロジェクトに新しいメンバーを追加します。

**認証**: 必須

**権限**: ADMIN以上

**リクエストボディ**:

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "member"
}
```

**ロール種別**:

- `owner`: プロジェクトオーナー
- `admin`: 管理者
- `member`: メンバー
- `viewer`: 閲覧者

**レスポンス** (201 Created):

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "member",
  "joined_at": "2025-10-15T10:30:00Z",
  "added_by": "660e8400-e29b-41d4-a716-446655440003",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "山田太郎",
    "azure_oid": "azure-oid-12345",
    "roles": ["User"],
    "is_active": true,
    "created_at": "2025-10-15T10:30:00Z",
    "updated_at": "2025-10-28T14:22:00Z",
    "last_login": "2025-10-30T09:15:00Z"
  }
}
```

**注意事項**:

- OWNER ロールの追加は OWNER のみが実行可能
- 重複するメンバーは追加できません

#### GET /api/v1/projects/{project_id}/members - メンバー一覧取得

**説明**: プロジェクトのメンバー一覧を取得します。

**認証**: 必須

**権限**: メンバー以上

**クエリパラメータ**:

- `skip`: スキップするレコード数（デフォルト: 0）
- `limit`: 取得する最大レコード数（デフォルト: 100、最大: 1000）

**レスポンス**:

```json
{
  "members": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "owner",
      "joined_at": "2025-10-01T09:00:00Z",
      "added_by": null,
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "owner@example.com",
        "display_name": "プロジェクトオーナー",
        "azure_oid": "azure-oid-owner",
        "roles": ["User"],
        "is_active": true,
        "created_at": "2025-10-01T08:00:00Z",
        "updated_at": "2025-10-28T14:22:00Z",
        "last_login": "2025-10-30T09:15:00Z"
      }
    }
  ],
  "total": 5,
  "project_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

#### GET /api/v1/projects/{project_id}/members/me - 自分のロール取得

**説明**: プロジェクトにおける自分のロールを取得します。

**認証**: 必須

**権限**: メンバー以上

**レスポンス**:

```json
{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "admin",
  "is_owner": false,
  "is_admin": true
}
```

#### PATCH /api/v1/projects/{project_id}/members/{member_id} - メンバーロール更新

**説明**: プロジェクトメンバーのロールを更新します。

**認証**: 必須

**権限**: OWNER/ADMIN

**パスパラメータ**:

- `member_id`: メンバーシップID（UUID形式）

**リクエストボディ**:

```json
{
  "role": "admin"
}
```

**レスポンス**: POST /api/v1/projects/{project_id}/members と同じ形式

**注意事項**:

- OWNER ロールの変更は OWNER のみが実行可能
- 最後の OWNER は降格できません

#### DELETE /api/v1/projects/{project_id}/members/{member_id} - メンバー削除

**説明**: プロジェクトからメンバーを削除します。

**認証**: 必須

**権限**: OWNER/ADMIN

**パスパラメータ**:

- `member_id`: メンバーシップID（UUID形式）

**レスポンス**: 204 No Content

**注意事項**:

- 自分自身は削除できません（プロジェクト退出を使用）
- 最後の OWNER は削除できません

#### DELETE /api/v1/projects/{project_id}/members/me - プロジェクト退出

**説明**: プロジェクトから自分自身を退出します。

**認証**: 必須

**権限**: 任意のメンバー

**レスポンス**: 204 No Content

**注意事項**:

- 最後の OWNER は退出できません

---

### ファイル管理 (/api/v1/projects/{project_id}/files)

| メソッド | パス | 説明 | 認証 | ロール |
|---------|------|------|------|--------|
| POST | /projects/{project_id}/files | ファイルアップロード | 必須 | メンバー |
| GET | /projects/{project_id}/files | ファイル一覧取得 | 必須 | メンバー |
| GET | /projects/{project_id}/files/{file_id} | ファイル詳細取得 | 必須 | メンバー |
| GET | /projects/{project_id}/files/{file_id}/download | ファイルダウンロード | 必須 | メンバー |
| DELETE | /projects/{project_id}/files/{file_id} | ファイル削除 | 必須 | Owner/Admin/投稿者 |

#### POST /api/v1/projects/{project_id}/files - ファイルアップロード

**説明**: プロジェクトにファイルをアップロードします。

**認証**: 必須

**権限**: MEMBER以上

**リクエスト**: `multipart/form-data`

- `file`: アップロードするファイル（バイナリ）

**制限事項**:

- 最大ファイルサイズ: 50MB
- 許可されるMIMEタイプ: image/*, application/pdf, text/*, .docx, .xlsx

**レスポンス** (201 Created):

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440004",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "filename": "d5f3c1a0-document.pdf",
  "original_filename": "document.pdf",
  "file_path": "/uploads/projects/660e8400/d5f3c1a0-document.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
  "uploaded_at": "2025-10-30T10:00:00Z",
  "message": "File uploaded successfully"
}
```

#### GET /api/v1/projects/{project_id}/files - ファイル一覧取得

**説明**: プロジェクトのファイル一覧を取得します。

**認証**: 必須

**権限**: VIEWER以上

**クエリパラメータ**:

- `skip`: スキップするレコード数（デフォルト: 0）
- `limit`: 取得する最大レコード数（デフォルト: 100）

**レスポンス**:

```json
{
  "files": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440004",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "d5f3c1a0-document.pdf",
      "original_filename": "document.pdf",
      "file_path": "/uploads/projects/660e8400/d5f3c1a0-document.pdf",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
      "uploaded_at": "2025-10-30T10:00:00Z"
    }
  ],
  "total": 12,
  "project_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

#### GET /api/v1/projects/{project_id}/files/{file_id} - ファイル詳細取得

**説明**: プロジェクトのファイル情報を取得します。

**認証**: 必須

**権限**: VIEWER以上

**パスパラメータ**:

- `file_id`: ファイルID（UUID形式）

**レスポンス**: ファイル一覧のファイルオブジェクトと同じ形式

#### GET /api/v1/projects/{project_id}/files/{file_id}/download - ファイルダウンロード

**説明**: プロジェクトのファイルをダウンロードします。

**認証**: 必須

**権限**: VIEWER以上

**パスパラメータ**:

- `file_id`: ファイルID（UUID形式）

**レスポンス**: ファイルのバイナリストリーム

**ヘッダー**:

- `Content-Type`: ファイルのMIMEタイプ
- `Content-Disposition`: `attachment; filename="original_filename.pdf"`

#### DELETE /api/v1/projects/{project_id}/files/{file_id} - ファイル削除

**説明**: プロジェクトのファイルを削除します。

**認証**: 必須

**権限**: ファイルのアップロード者本人、またはプロジェクトADMIN/OWNER

**パスパラメータ**:

- `file_id`: ファイルID（UUID形式）

**レスポンス**:

```json
{
  "file_id": "880e8400-e29b-41d4-a716-446655440004",
  "message": "File 880e8400-e29b-41d4-a716-446655440004 deleted successfully"
}
```

---

## 共通仕様

### 認証

**Azure AD Bearer認証** (本番環境):

```http
Authorization: Bearer <Azure_AD_Token>
```

**モック認証** (開発環境):

```http
Authorization: Bearer mock-access-token-dev-12345
```

詳細は [環境設定ガイド](../../01-getting-started/04-environment-config.md) を参照してください。

### ページネーション

全ての一覧取得APIは以下のクエリパラメータをサポート:

| パラメータ | 型 | デフォルト | 最大値 | 説明 |
|-----------|---|----------|-------|------|
| `skip` | integer | 0 | - | スキップする件数 |
| `limit` | integer | 100 | 1000 | 取得する最大件数 |

**レスポンス形式**（ユーザー一覧の例）:

```json
{
  "users": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

詳細は [ページネーション設計](./05-pagination.md) を参照してください。

### エラーレスポンス (RFC 9457)

すべてのエラーレスポンスは **RFC 9457 Problem Details for HTTP APIs** に準拠しています。

**Content-Type**: `application/problem+json`

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "プロジェクトが見つかりません",
  "instance": "/api/v1/projects/123",
  "project_id": "123"
}
```

**必須フィールド**:

- `type`: 問題タイプを識別するURI
- `title`: HTTPステータスコードに対応する短い要約
- `status`: HTTPステータスコード

**オプションフィールド**:

- `detail`: 具体的な説明
- `instance`: リクエストパス
- カスタムフィールド: 追加の詳細情報

詳細は [エラーレスポンス設計](./06-error-responses.md) を参照してください。

### ステータスコード

| コード | 説明 | 使用例 |
|-------|------|--------|
| 200 | 成功 | GET, PATCH |
| 201 | 作成成功 | POST |
| 204 | 成功（レスポンスボディなし） | DELETE |
| 400 | リクエストエラー | バリデーションエラー |
| 401 | 認証エラー | トークン無効/期限切れ |
| 403 | 権限エラー | 必要なロールがない |
| 404 | リソースなし | 存在しないID |
| 422 | セマンティックエラー | ビジネスロジック違反 |
| 500 | サーバーエラー | 予期しないエラー |

## 参考リンク

- [レスポンス設計](./04-response-design.md)
- [バリデーション](./03-validation.md)
- [エンドポイント設計](./02-endpoint-design.md)
