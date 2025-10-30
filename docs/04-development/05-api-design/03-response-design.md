# レスポンス設計

APIレスポンスの統一フォーマットについて説明します。

## 基本的なレスポンス

```python
from pydantic import BaseModel, ConfigDict


class SampleUserResponse(BaseModel):
    """ユーザーレスポンス。"""
    id: int
    email: str
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemyモデルから変換


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス。"""
    message: str


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int):
    # 削除処理
    return MessageResponse(message=f"User {user_id} deleted successfully")
```

## リストレスポンス

```python
from pydantic import BaseModel, ConfigDict


class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンス。"""
    items: list[SampleUserResponse]
    total: int
    skip: int
    limit: int


@router.get("/users", response_model=PaginatedResponse)
async def list_users(skip: int = 0, limit: int = 100):
    users = await service.list_users(skip, limit)
    total = await service.count_users()
    return PaginatedResponse(
        items=[SampleUserResponse.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit
    )
```

## エラーレスポンス

```python
# カスタム例外
class AppException(Exception):
    def __init__(self, message: str, status_code: int, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}


# エラーハンドラー
from fastapi import Request
from fastapi.responses import JSONResponse

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )
```

---

## 実際のレスポンス例

このセクションでは、実装されているエンドポイントの実際のレスポンス例を提供します。

### 成功レスポンスの実例

#### ユーザー詳細取得 (GET /api/v1/users/me)

**リクエスト**:
```http
GET /api/v1/users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (200 OK)**:
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

**特徴**:
- このエンドポイントを呼び出すたびに `last_login` が更新されます
- クライアントIPアドレスは監査ログに記録されます

#### プロジェクト一覧取得 (GET /api/v1/projects)

**リクエスト**:
```http
GET /api/v1/projects?skip=0&limit=10 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (200 OK)**:
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
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "name": "Webアプリケーション",
    "code": "WEB-002",
    "description": "Webアプリ開発",
    "is_active": true,
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-09-15T08:00:00Z",
    "updated_at": "2025-10-18T12:00:00Z"
  }
]
```

**特徴**:
- 自分がメンバーとして所属するプロジェクトのみ表示されます
- レスポンスは配列形式です（ページネーション情報は含まれません）

#### ユーザー一覧取得 (GET /api/v1/users)

**リクエスト**:
```http
GET /api/v1/users?skip=0&limit=10 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (200 OK)**:
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
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "azure_oid": "azure-oid-67890",
      "email": "admin@example.com",
      "display_name": "佐藤花子",
      "roles": ["SystemAdmin", "User"],
      "is_active": true,
      "created_at": "2025-09-01T08:00:00Z",
      "updated_at": "2025-10-29T16:00:00Z",
      "last_login": "2025-10-29T18:30:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 10
}
```

**特徴**:
- SystemAdmin権限が必要です
- ページネーション情報（total, skip, limit）が含まれます

#### プロジェクトメンバー一覧取得 (GET /api/v1/projects/{project_id}/members)

**リクエスト**:
```http
GET /api/v1/projects/660e8400-e29b-41d4-a716-446655440001/members?skip=0&limit=10 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (200 OK)**:
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
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "role": "member",
      "joined_at": "2025-10-05T14:30:00Z",
      "added_by": "550e8400-e29b-41d4-a716-446655440000",
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "member@example.com",
        "display_name": "メンバー",
        "azure_oid": "azure-oid-member",
        "roles": ["User"],
        "is_active": true,
        "created_at": "2025-09-15T10:00:00Z",
        "updated_at": "2025-10-25T11:00:00Z",
        "last_login": "2025-10-29T16:45:00Z"
      }
    }
  ],
  "total": 5,
  "project_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**特徴**:
- ユーザー情報がネストされた形式で含まれます
- `added_by` はプロジェクト作成時のオーナーの場合は `null` です

#### ファイル一覧取得 (GET /api/v1/projects/{project_id}/files)

**リクエスト**:
```http
GET /api/v1/projects/660e8400-e29b-41d4-a716-446655440001/files?skip=0&limit=10 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (200 OK)**:
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
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440005",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "a3b2c1d0-image.png",
      "original_filename": "screenshot.png",
      "file_path": "/uploads/projects/660e8400/a3b2c1d0-image.png",
      "file_size": 512000,
      "mime_type": "image/png",
      "uploaded_by": "550e8400-e29b-41d4-a716-446655440001",
      "uploaded_at": "2025-10-29T15:30:00Z"
    }
  ],
  "total": 12,
  "project_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**特徴**:
- `filename` はサーバー側で管理される一意のファイル名です
- `original_filename` はユーザーがアップロードした元のファイル名です

---

### エラーレスポンスの実例（RFC 9457準拠）

このプロジェクトは **RFC 9457 Problem Details for HTTP APIs** 標準に準拠したエラーレスポンスを採用しています。

**Content-Type**: `application/problem+json`

詳細は [エラーレスポンス設計](./05-error-responses.md) を参照してください。

#### 400 Bad Request - バリデーションエラー

**リクエスト**:
```http
PATCH /api/v1/users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "invalid-email"
}
```

**レスポンス (400 Bad Request)**:
```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "バリデーションエラー",
  "instance": "/api/v1/users/me",
  "errors": {
    "email": ["有効なメールアドレスを入力してください"]
  }
}
```

**原因**:
- リクエストボディのバリデーションに失敗しました
- `email` フィールドが不正な形式です

**対処法**:
- 正しい形式のメールアドレスを送信してください

#### 401 Unauthorized - 認証エラー

**リクエスト**:
```http
GET /api/v1/users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer invalid-token
```

**レスポンス (401 Unauthorized)**:
```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "認証に失敗しました",
  "instance": "/api/v1/users/me"
}
```

**原因**:
- 認証トークンが無効または期限切れです
- Authorizationヘッダーが欠落しています

**対処法**:
- 有効なAzure ADトークンを取得してください
- 開発環境では、正しいモックトークンを使用してください

#### 403 Forbidden - 権限エラー

**リクエスト**:
```http
PATCH /api/v1/projects/660e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "更新されたプロジェクト名"
}
```

**レスポンス (403 Forbidden)**:
```json
{
  "type": "about:blank",
  "title": "Forbidden",
  "status": 403,
  "detail": "この操作を実行する権限がありません",
  "instance": "/api/v1/projects/660e8400-e29b-41d4-a716-446655440001",
  "required_role": "owner",
  "user_role": "member"
}
```

**原因**:
- 必要なプロジェクトロール（OWNER/ADMIN）を持っていません
- プロジェクトのメンバーではありません

**対処法**:
- プロジェクトオーナーに権限の変更を依頼してください
- 自分が所属するプロジェクトのみ操作してください

#### 404 Not Found - リソースなし

**リクエスト**:
```http
GET /api/v1/projects/999e8400-e29b-41d4-a716-446655440999 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (404 Not Found)**:
```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "プロジェクトが見つかりません",
  "instance": "/api/v1/projects/999e8400-e29b-41d4-a716-446655440999",
  "project_id": "999e8400-e29b-41d4-a716-446655440999"
}
```

**原因**:
- 指定されたIDのリソースが存在しません
- リソースが削除されている可能性があります

**対処法**:
- IDを確認してください
- リソース一覧を取得して、存在するIDを使用してください

#### 422 Unprocessable Entity - セマンティックエラー

**リクエスト**:
```http
PATCH /api/v1/users/550e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "roles": ["SystemAdmin"]
}
```

**レスポンス (422 Unprocessable Entity)**:
```json
{
  "type": "about:blank",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "rolesまたはis_activeの更新には管理者権限が必要です",
  "instance": "/api/v1/users/550e8400-e29b-41d4-a716-446655440001",
  "required_role": "SystemAdmin",
  "user_roles": ["User"]
}
```

**原因**:
- ビジネスロジックの制約に違反しています
- 管理者権限が必要なフィールドを更新しようとしています

**対処法**:
- 管理者に依頼してください
- 一般ユーザーが更新可能なフィールドのみ変更してください

#### 409 Conflict - 重複エラー

**リクエスト**:
```http
POST /api/v1/projects HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "新しいプロジェクト",
  "code": "AI-001"
}
```

**レスポンス (409 Conflict)**:
```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "プロジェクトコードが既に存在します",
  "instance": "/api/v1/projects",
  "code": "AI-001",
  "field": "code"
}
```

**原因**:
- 一意制約に違反しています
- プロジェクトコードが既に使用されています

**対処法**:
- 異なるプロジェクトコードを使用してください

#### 500 Internal Server Error - サーバーエラー

**リクエスト**:
```http
GET /api/v1/users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**レスポンス (500 Internal Server Error)**:
```json
{
  "type": "about:blank",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "予期しないエラーが発生しました",
  "instance": "/api/v1/users/me"
}
```

**原因**:
- サーバー側で予期しないエラーが発生しました
- データベース接続エラー、外部サービスエラーなど

**対処法**:
- しばらく待ってから再試行してください
- 問題が続く場合は管理者に連絡してください
- エラーの詳細はサーバーログに記録されています

---

## レスポンス設計のベストプラクティス

### 1. 一貫性のあるフィールド名

- **snake_case** を使用（例: `created_at`, `display_name`）
- JSONレスポンスはPythonのモデルから自動生成されます

### 2. 日時フィールドの形式

- **ISO 8601形式** を使用（例: `2025-10-30T09:15:00Z`）
- タイムゾーンは常にUTC（`Z`サフィックス）

### 3. UUID形式

- すべてのIDは **UUID v4形式** の文字列（例: `550e8400-e29b-41d4-a716-446655440000`）

### 4. ページネーション

- `total`: 総件数を常に含める
- `skip`, `limit`: リクエストパラメータをエコーバック

### 5. エラーレスポンス

- **RFC 9457準拠** の形式を使用
- カスタムフィールドで詳細情報を提供
- `detail` フィールドは人間が読める日本語メッセージ

## 参考リンク

- [API仕様概要](./01-api-overview.md)
- [エラーレスポンス設計](./05-error-responses.md)
- [ページネーション設計](./04-pagination.md)
- [RFC 9457 Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
