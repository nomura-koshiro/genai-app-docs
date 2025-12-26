# API仕様書

## 1. 概要

本文書は、CAMPシステムのREST API仕様を定義します。
FastAPIフレームワークを使用し、OpenAPI 3.0準拠のAPIを提供しています。

### 1.1 API基本情報

- **ベースURL**: `http://localhost:8000` (開発環境)
- **プロトコル**: HTTP/HTTPS
- **認証方式**: Bearer Token (JWT / Azure AD)
- **コンテンツタイプ**: application/json
- **文字コード**: UTF-8
- **日時形式**: ISO 8601 (UTC)
- **ページネーション**: offset/limit方式

### 1.2 API ドキュメント

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## 2. APIエンドポイント全体図

### 2.1 エンドポイント構造

::: mermaid
graph TB
    Root[/ Root]
    Health[/health Health Check]
    Metrics[/metrics Prometheus Metrics]

    APIv1[/api/v1 API Version 1]

    UserAccounts[/api/v1/user_accounts ユーザー管理]
    Projects[/api/v1/projects プロジェクト管理]
    ProjectMembers[/api/v1/projects/:id/members メンバー管理]
    ProjectFiles[/api/v1/projects/:id/files ファイル管理]
    AnalysisSession[/api/v1/analysis/session 分析セッション]
    AnalysisTemplate[/api/v1/analysis/template テンプレート]
    DriverTreeFile[/api/v1/driver-tree/file ファイル管理]
    DriverTreeTree[/api/v1/driver-tree/tree ツリー管理]
    DriverTreeNode[/api/v1/driver-tree/node ノード管理]

    Root --> Health
    Root --> Metrics
    Root --> APIv1

    APIv1 --> UserAccounts
    APIv1 --> Projects
    Projects --> ProjectMembers
    Projects --> ProjectFiles
    APIv1 --> AnalysisSession
    APIv1 --> AnalysisTemplate
    APIv1 --> DriverTreeFile
    APIv1 --> DriverTreeTree
    APIv1 --> DriverTreeNode

    style Root fill:#E8F5E9
    style APIv1 fill:#C5E1A5
    style UserAccounts fill:#AED581
    style Projects fill:#9CCC65
    style AnalysisSession fill:#8BC34A
    style DriverTreeTree fill:#7CB342
:::

### 2.2 エンドポイント一覧

| カテゴリ | エンドポイント | 説明 |
|---------|---------------|------|
| **システム** | `GET /` | ルート（アプリ情報） |
| | `GET /health` | ヘルスチェック |
| | `GET /metrics` | Prometheusメトリクス |
| **ユーザー** | `/api/v1/user_accounts/*` | ユーザー管理 |
| **プロジェクト** | `/api/v1/projects/*` | プロジェクト管理 |
| **メンバー** | `/api/v1/projects/{id}/members/*` | プロジェクトメンバー管理 |
| **ファイル** | `/api/v1/projects/{id}/files/*` | プロジェクトファイル管理 |
| **分析セッション** | `/api/v1/analysis/session/*` | 分析セッション管理 |
| **分析テンプレート** | `/api/v1/analysis/template/*` | 分析テンプレート |
| **ドライバーツリーファイル** | `/api/v1/driver-tree/file/*` | ファイル管理 |
| **ドライバーツリー** | `/api/v1/driver-tree/tree/*` | ツリー管理 |
| **ドライバーツリーノード** | `/api/v1/driver-tree/node/*` | ノード管理 |

---

## 3. 認証・認可

### 3.1 認証フロー

::: mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth as Authentication Service
    participant AzureAD as Azure AD
    participant DB as Database

    alt 本番モード (AUTH_MODE=production)
        Client->>API: Request + Bearer Token
        API->>AzureAD: JWT検証（署名、有効期限、発行者）
        AzureAD-->>API: 検証結果（azure_oid等）
        API->>DB: UserAccount取得/作成
        DB-->>API: UserAccount
    else 開発モード (AUTH_MODE=development)
        Client->>API: Request + Mock Token
        API->>Auth: モックトークン検証
        Auth-->>API: モックユーザー情報
        API->>DB: UserAccount取得/作成
        DB-->>API: UserAccount
    end

    API->>API: 認可チェック（RBAC）
    API-->>Client: Response
:::

### 3.2 認証ヘッダー

**本番モード:**

```http
Authorization: Bearer <Azure_AD_JWT_Token>
```

**開発モード:**

```http
Authorization: Bearer mock-access-token-dev-12345
```

### 3.3 認証エラーレスポンス

```json
{
  "type": "https://httpstatuses.com/401",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid or expired token",
  "instance": "/api/v1/projects/123"
}
```

---

## 4. エラーレスポンス（RFC 9457準拠）

### 4.1 エラーレスポンス形式

すべてのエラーレスポンスは RFC 9457（Problem Details for HTTP APIs）に準拠します。

```json
{
  "type": "https://httpstatuses.com/{status_code}",
  "title": "エラータイトル",
  "status": 400,
  "detail": "詳細なエラーメッセージ",
  "instance": "/api/v1/resource/123",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

### 4.2 HTTPステータスコード一覧

| コード | 説明 | 使用ケース |
|-------|------|----------|
| **200** | OK | 成功（取得、更新） |
| **201** | Created | リソース作成成功 |
| **204** | No Content | 削除成功 |
| **400** | Bad Request | リクエストの形式エラー |
| **401** | Unauthorized | 認証エラー |
| **403** | Forbidden | 権限不足 |
| **404** | Not Found | リソース未発見 |
| **409** | Conflict | リソース競合 |
| **422** | Unprocessable Entity | バリデーションエラー |
| **429** | Too Many Requests | レート制限超過 |
| **500** | Internal Server Error | サーバーエラー |

---

## 5. システムエンドポイント

### 5.1 ルート

#### GET /

アプリケーションの基本情報を返します。

**実装**: `src/app/api/routes/system/root.py`

**レスポンス (200 OK):**

```json
{
  "message": "Welcome to camp-backend",
  "version": "0.1.0",
  "docs": "/docs"
}
```

### 5.2 ヘルスチェック

#### GET /health

システムの稼働状態を確認します。

**実装**: `src/app/api/routes/system/health.py`

**レスポンス (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T12:00:00Z",
  "version": "0.1.0",
  "environment": "development",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 5.3 メトリクス

#### GET /metrics

Prometheusメトリクスを取得します。

**実装**: `src/app/api/routes/system/metrics.py`

**レスポンス (200 OK):**

```text
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status_code="200"} 42.0
```

---

## 6. ユーザー管理API（/api/v1/user_accounts）

**実装**: `src/app/api/routes/v1/user_accounts/user_accounts.py`

### 6.1 ユーザー一覧取得

#### GET /api/v1/user_accounts

**権限**: SystemAdmin ロール必須

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| skip | integer | No | オフセット（デフォルト: 0） |
| limit | integer | No | 取得件数（デフォルト: 100、最大: 1000） |

**レスポンス (200 OK):**

```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "azure_oid": "12345678-1234-1234-1234-123456789abc",
      "email": "user@example.com",
      "display_name": "山田 太郎",
      "roles": ["User"],
      "is_active": true,
      "last_login": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

### 6.2 現在のユーザー情報取得

#### GET /api/v1/user_accounts/me

**権限**: 認証済みユーザー

**レスポンス (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "azure_oid": "12345678-1234-1234-1234-123456789abc",
  "email": "user@example.com",
  "display_name": "山田 太郎",
  "roles": ["User"],
  "is_active": true,
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### 6.3 特定ユーザー情報取得

#### GET /api/v1/user_accounts/{user_id}

**権限**: SystemAdmin ロール必須

**レスポンス (200 OK):** ユーザー情報オブジェクト

### 6.4 ユーザー情報更新

#### PATCH /api/v1/user_accounts/me

**権限**: 認証済みユーザー（自分自身のみ）

**リクエスト:**

```json
{
  "display_name": "山田 花子"
}
```

**レスポンス (200 OK):** 更新後のユーザー情報オブジェクト

### 6.5 ユーザー削除

#### DELETE /api/v1/user_accounts/{user_id}

**権限**: SystemAdmin ロール必須

**レスポンス (204 No Content)**

---

## 7. プロジェクト管理API（/api/v1/projects）

**実装**: `src/app/api/routes/v1/project/projects.py`

### 7.1 プロジェクト一覧取得

#### GET /api/v1/projects

**権限**: 認証済みユーザー（自分がメンバーのプロジェクトのみ）

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| skip | integer | No | オフセット（デフォルト: 0） |
| limit | integer | No | 取得件数（デフォルト: 100、最大: 1000） |

**レスポンス (200 OK):**

```json
{
  "projects": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "プロジェクトA",
      "code": "PROJECT_A",
      "description": "説明文",
      "is_active": true,
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-10T00:00:00Z",
      "updated_at": "2025-01-15T00:00:00Z"
    }
  ],
  "total": 10
}
```

### 7.2 プロジェクト詳細取得

#### GET /api/v1/projects/{project_id}

**権限**: プロジェクトメンバー

**レスポンス (200 OK):** プロジェクト情報オブジェクト

### 7.3 プロジェクトコードで取得

#### GET /api/v1/projects/code/{code}

**権限**: プロジェクトメンバー

**レスポンス (200 OK):** プロジェクト情報オブジェクト

### 7.4 プロジェクト作成

#### POST /api/v1/projects

**権限**: 認証済みユーザー

**リクエスト:**

```json
{
  "name": "新規プロジェクト",
  "code": "NEW_PROJECT",
  "description": "プロジェクトの説明"
}
```

**レスポンス (201 Created):** 作成されたプロジェクト情報

### 7.5 プロジェクト更新

#### PATCH /api/v1/projects/{project_id}

**権限**: PROJECT_MANAGER

**レスポンス (200 OK):** 更新後のプロジェクト情報

### 7.6 プロジェクト削除

#### DELETE /api/v1/projects/{project_id}

**権限**: PROJECT_MANAGER

**レスポンス (204 No Content)**

---

## 8. プロジェクトメンバー管理API（/api/v1/projects/{project_id}/members）

**実装**: `src/app/api/routes/v1/project/project_members.py`

### 8.1 メンバー一覧取得

#### GET /api/v1/projects/{project_id}/members

**権限**: プロジェクトメンバー

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| skip | integer | No | オフセット（デフォルト: 0） |
| limit | integer | No | 取得件数（デフォルト: 100、最大: 1000） |

**レスポンス (200 OK):**

```json
{
  "members": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "project_manager",
      "joined_at": "2025-01-10T00:00:00Z",
      "added_by": null,
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "display_name": "山田 太郎"
      }
    }
  ],
  "total": 5,
  "project_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### 8.2 自分のロール取得

#### GET /api/v1/projects/{project_id}/members/me

**権限**: プロジェクトメンバー

**レスポンス (200 OK):**

```json
{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "project_manager",
  "is_owner": true,
  "is_admin": true
}
```

### 8.3 メンバー追加

#### POST /api/v1/projects/{project_id}/members

**権限**: PROJECT_MANAGER

**リクエスト:**

```json
{
  "user_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "role": "member"
}
```

**レスポンス (201 Created):** 追加されたメンバー情報

### 8.4 メンバー一括追加

#### POST /api/v1/projects/{project_id}/members/bulk

**権限**: PROJECT_MANAGER

**リクエスト:**

```json
{
  "members": [
    {"user_id": "user1-uuid", "role": "member"},
    {"user_id": "user2-uuid", "role": "viewer"}
  ]
}
```

**レスポンス (201 Created):**

```json
{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "added": [...],
  "failed": [...],
  "total_requested": 2,
  "total_added": 1,
  "total_failed": 1
}
```

### 8.5 メンバーロール更新

#### PATCH /api/v1/projects/{project_id}/members/{member_id}

**権限**: PROJECT_MANAGER

**リクエスト:**

```json
{
  "role": "member"
}
```

**レスポンス (200 OK):** 更新されたメンバー情報

### 8.6 メンバー削除

#### DELETE /api/v1/projects/{project_id}/members/{member_id}

**権限**: PROJECT_MANAGER

**レスポンス (204 No Content)**

### 8.7 プロジェクト退出

#### DELETE /api/v1/projects/{project_id}/members/me

**権限**: 任意のプロジェクトメンバー

**レスポンス (204 No Content)**

---

## 9. プロジェクトファイル管理API（/api/v1/projects/{project_id}/files）

**実装**: `src/app/api/routes/v1/project/project_files.py`

### 9.1 ファイル一覧取得

#### GET /api/v1/projects/{project_id}/files

**権限**: プロジェクトメンバー

**レスポンス (200 OK):**

```json
{
  "files": [
    {
      "id": "cc0e8400-e29b-41d4-a716-446655440007",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "file_name": "data.csv",
      "file_size": 1048576,
      "content_type": "text/csv",
      "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-15T16:00:00Z"
    }
  ],
  "total": 10,
  "project_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### 9.2 ファイル情報取得

#### GET /api/v1/projects/{project_id}/files/{file_id}

**権限**: プロジェクトメンバー

**レスポンス (200 OK):** ファイル情報オブジェクト

### 9.3 ファイルダウンロード

#### GET /api/v1/projects/{project_id}/files/{file_id}/download

**権限**: プロジェクトメンバー

**レスポンス (200 OK):** ファイルバイナリ（StreamingResponse）

### 9.4 ファイルアップロード

#### POST /api/v1/projects/{project_id}/files

**権限**: プロジェクトメンバー

**リクエスト:** `multipart/form-data`

**レスポンス (201 Created):** 作成されたファイル情報

### 9.5 ファイル削除

#### DELETE /api/v1/projects/{project_id}/files/{file_id}

**権限**: プロジェクトメンバー

**レスポンス (204 No Content)**

---

## 10. 分析セッションAPI（/api/v1/analysis/session）

**実装**: `src/app/api/routes/v1/analysis/analysis_sessions.py`

### 10.1 セッション一覧取得

#### GET /api/v1/analysis/session

**権限**: プロジェクトメンバー

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| project_id | uuid | Yes | プロジェクトID |
| skip | integer | No | オフセット（デフォルト: 0） |
| limit | integer | No | 取得件数（デフォルト: 100、最大: 1000） |
| is_active | boolean | No | アクティブフラグフィルタ |

**レスポンス (200 OK):** セッション一覧

### 10.2 セッション作成

#### POST /api/v1/analysis/session

**権限**: プロジェクトメンバー

**リクエスト:**

```json
{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "validation_id": "validation-uuid",
  "issue_id": "issue-uuid"
}
```

**レスポンス (201 Created):**

```json
{
  "session_id": "ee0e8400-e29b-41d4-a716-446655440009",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "created_at": "2025-01-15T17:00:00Z"
}
```

### 10.3 セッション詳細取得

#### GET /api/v1/analysis/session/{session_id}

**権限**: プロジェクトメンバー

**レスポンス (200 OK):** セッション詳細（ステップ、ファイル、チャット履歴を含む）

### 10.4 セッション削除

#### DELETE /api/v1/analysis/session/{session_id}

**権限**: プロジェクトメンバー

**レスポンス (204 No Content)**

### 10.5 ファイル管理

#### GET /api/v1/analysis/session/{session_id}/file

**説明**: 登録済ファイル一覧取得

#### POST /api/v1/analysis/session/{session_id}/file

**説明**: ファイル登録

#### PATCH /api/v1/analysis/session/{session_id}/file/{file_id}/config

**説明**: シート選択/データカラム設定

### 10.6 入力ファイル選択

#### POST /api/v1/analysis/session/{session_id}/input

**説明**: 分析に使用するファイルを選択

### 10.7 分析結果取得

#### GET /api/v1/analysis/session/{session_id}/result

**説明**: 最新snapshotの分析結果を取得

### 10.8 AIチャット実行

#### POST /api/v1/analysis/session/{session_id}/chat

**権限**: プロジェクトメンバー
**タイムアウト**: 10分

**リクエスト:**

```json
{
  "message": "売上が100万円以上のデータを抽出してください"
}
```

**レスポンス (200 OK):** AIレスポンス

### 10.9 スナップショット復元

#### POST /api/v1/analysis/session/{session_id}/snapshot/{snapshot_id}

**説明**: 指定したスナップショットに状態を復元

### 10.10 分析ステップ管理

#### POST /api/v1/analysis/session/{session_id}/step

**説明**: 新規分析ステップ作成

#### PATCH /api/v1/analysis/session/{session_id}/step/{step_id}

**説明**: 分析ステップ更新

#### DELETE /api/v1/analysis/session/{session_id}/step/{step_id}

**説明**: 分析ステップ削除

---

## 11. 分析テンプレートAPI（/api/v1/analysis/template）

**実装**: `src/app/api/routes/v1/analysis/analysis_templates.py`

### 11.1 テンプレート一覧取得

#### GET /api/v1/analysis/template

**権限**: 認証済みユーザー

**レスポンス (200 OK):**

```json
[
  {
    "validation_id": "validation-uuid",
    "validation_name": "施策名",
    "validation_order": 1,
    "issue_id": "issue-uuid",
    "issue_name": "課題名",
    "issue_order": 1
  }
]
```

### 11.2 テンプレート詳細取得

#### GET /api/v1/analysis/template/{issue_id}

**権限**: 認証済みユーザー

**レスポンス (200 OK):** テンプレート詳細（課題アプローチ説明、AIプロンプト、初期軸設定、ダミーデータ等）

---

## 12. ドライバーツリーファイルAPI（/api/v1/driver-tree/file）

**実装**: `src/app/api/routes/v1/driver_tree/driver_tree_files.py`

### 12.1 アップロードファイル一覧取得

#### GET /api/v1/driver-tree/file

**権限**: 認証済みユーザー（自分のファイルのみ）

**レスポンス (200 OK):**

```json
{
  "files": [
    {
      "file_id": "file-uuid",
      "filename": "data.xlsx",
      "sheet_id": "sheet-uuid",
      "sheet_name": "Sheet1",
      "columns": [
        {
          "columns_id": "column-uuid",
          "columns_name": "売上",
          "items": ["1000", "2000", "3000"]
        }
      ],
      "uploaded_at": "2025-01-15T16:00:00Z"
    }
  ]
}
```

### 12.2 ファイルアップロード

#### POST /api/v1/driver-tree/file

**権限**: 認証済みユーザー
**最大ファイルサイズ**: 50MB

**リクエスト:** `multipart/form-data` (Excel .xlsx/.xls)

**レスポンス (201 Created):**

```json
{
  "file_id": "file-uuid",
  "filename": "data.xlsx",
  "sheets": [
    {"sheet_id": "sheet-uuid", "name": "Sheet1"}
  ]
}
```

### 12.3 シート選択

#### POST /api/v1/driver-tree/file/{file_id}/sheet

**リクエスト:**

```json
{
  "sheet_id": "sheet-uuid"
}
```

**レスポンス (200 OK):** `{"success": true}`

### 12.4 データカラム設定

#### PATCH /api/v1/driver-tree/file/{file_id}/{sheet_id}/column

**リクエスト:**

```json
{
  "columns": [
    {"column_id": "column-uuid", "role": "推移"},
    {"column_id": "column-uuid", "role": "軸"}
  ]
}
```

**レスポンス (200 OK):** `{"success": true}`

---

## 13. ドライバーツリー管理API（/api/v1/driver-tree）

**実装**: `src/app/api/routes/v1/driver_tree/driver_tree_trees.py`

### 13.1 ツリー作成

#### POST /api/v1/driver-tree/tree

**権限**: 認証済みユーザー

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| project_id | uuid | Yes | プロジェクトID（クエリ） |

**リクエスト:**

```json
{
  "name": "ツリー名",
  "description": "説明"
}
```

**レスポンス (201 Created):**

```json
{
  "tree_id": "tree-uuid",
  "name": "ツリー名",
  "description": "説明",
  "created_at": "2025-01-15T17:00:00Z"
}
```

### 13.2 ツリー一覧取得

#### GET /api/v1/driver-tree/tree

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| project_id | uuid | Yes | プロジェクトID（クエリ） |

**レスポンス (200 OK):**

```json
{
  "trees": [
    {
      "tree_id": "tree-uuid",
      "name": "ツリー名",
      "description": "説明",
      "created_at": "2025-01-15T17:00:00Z",
      "updated_at": "2025-01-15T17:00:00Z"
    }
  ]
}
```

### 13.3 ツリー取得

#### GET /api/v1/driver-tree/tree/{tree_id}

**レスポンス (200 OK):**

```json
{
  "tree_id": "tree-uuid",
  "name": "ツリー名",
  "description": "説明",
  "root": {},
  "nodes": [
    {
      "node_id": "node-uuid",
      "label": "ノード名",
      "node_type": "入力",
      "position_x": 100,
      "position_y": 100,
      "data": {}
    }
  ],
  "relationship": [
    {
      "parent_id": "parent-uuid",
      "operator": "+",
      "child_id_list": ["child1-uuid", "child2-uuid"]
    }
  ]
}
```

### 13.4 数式/データインポート

#### POST /api/v1/driver-tree/tree/{tree_id}

**リクエスト:**

```json
{
  "position_x": 100,
  "position_y": 100,
  "formulas": ["売上 = 単価 * 数量", "利益 = 売上 - コスト"],
  "sheet_id": "sheet-uuid"
}
```

### 13.5 ツリーリセット

#### POST /api/v1/driver-tree/{tree_id}/reset

**説明**: ツリーを初期状態にリセット（構造は維持）

### 13.6 ツリー削除

#### DELETE /api/v1/driver-tree/{tree_id}/delete

**レスポンス (200 OK):** `{"success": true, "deleted_at": "..."}`

### 13.7 カテゴリ取得

#### GET /api/v1/driver-tree/category

**説明**: 業界分類/業界/ドライバーツリー型/KPI選択肢を取得

### 13.8 数式取得

#### GET /api/v1/driver-tree/formula

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| driver_tree | string | Yes | ドライバーツリー型 |
| KPI | string | Yes | KPI |

**レスポンス (200 OK):** `{"formulas": ["式1", "式2"]}`

### 13.9 計算結果取得

#### GET /api/v1/driver-tree/tree/{tree_id}/data

**説明**: ツリー全体の計算結果を取得

### 13.10 シミュレーションファイルダウンロード

#### GET /api/v1/driver-tree/tree/{tree_id}/output

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| format | string | No | 出力形式（xlsx/csv、デフォルト: xlsx） |

**レスポンス (200 OK):** Excel/CSVファイル（StreamingResponse）

---

## 14. ドライバーツリーノードAPI（/api/v1/driver-tree/node）

**実装**: `src/app/api/routes/v1/driver_tree/driver_tree_nodes.py`

### 14.1 ノード作成

#### POST /api/v1/driver-tree/tree/{tree_id}/node

**リクエスト:**

```json
{
  "label": "ノード名",
  "node_type": "入力",
  "position_x": 100,
  "position_y": 100
}
```

**レスポンス (201 Created):**

```json
{
  "tree": {},
  "created_node_id": "node-uuid"
}
```

### 14.2 ノード詳細取得

#### GET /api/v1/driver-tree/node/{node_id}

**レスポンス (200 OK):**

```json
{
  "node_id": "node-uuid",
  "label": "ノード名",
  "position_x": 100,
  "position_y": 100,
  "node_type": "入力",
  "data": {},
  "relationship": {}
}
```

### 14.3 ノード更新

#### PATCH /api/v1/driver-tree/node/{node_id}

**リクエスト:**

```json
{
  "label": "新しいノード名",
  "operator": "+",
  "children_id_list": ["child1-uuid", "child2-uuid"]
}
```

### 14.4 ノード削除

#### DELETE /api/v1/driver-tree/node/{node_id}

**レスポンス (200 OK):** `{"tree": {}}`

### 14.5 ノードプレビューダウンロード

#### GET /api/v1/driver-tree/node/{node_id}/preview/output

**レスポンス (200 OK):** CSVファイル（StreamingResponse）

### 14.6 施策管理

#### POST /api/v1/driver-tree/node/{node_id}/policy

**リクエスト:**

```json
{
  "name": "施策名",
  "value": 1.5
}
```

#### GET /api/v1/driver-tree/node/{node_id}/policy

**説明**: 施策一覧取得

#### PATCH /api/v1/driver-tree/node/{node_id}/policy/{policy_id}

**説明**: 施策更新

#### DELETE /api/v1/driver-tree/node/{node_id}/policy/{policy_id}

**説明**: 施策削除

---

## 15. ページネーション

### 15.1 ページネーション仕様

すべての一覧取得APIはoffset/limit方式のページネーションをサポートします。

**共通クエリパラメータ:**

| パラメータ | 型 | デフォルト | 最大値 | 説明 |
|----------|-----|-----------|--------|------|
| skip | integer | 0 | - | スキップする件数 |
| limit | integer | 100 | 1000 | 取得件数 |

**レスポンス構造例:**

```json
{
  "items": [],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

---

## 16. リクエスト制限

### 16.1 レート制限

- **デフォルト**: 100リクエスト/分
- **ヘッダー情報**:
  - `X-RateLimit-Limit`: 制限値
  - `X-RateLimit-Remaining`: 残りリクエスト数
  - `X-RateLimit-Reset`: リセット時刻

### 16.2 ファイルサイズ制限

- **ドライバーツリーファイル**: 50MB
- **プロジェクトファイル**: 100MB

---

## 17. バリデーション

### 17.1 共通バリデーションルール

| フィールド | ルール | 説明 |
|----------|--------|------|
| **UUID** | uuid4形式 | `550e8400-e29b-41d4-a716-446655440000` |
| **email** | RFC 5322準拠 | `user@example.com` |
| **code** | `^[A-Z0-9_]+$` | 大文字英数字とアンダースコアのみ |
| **name** | 1-255文字 | 任意の文字列 |
| **is_active** | boolean | `true` or `false` |
| **datetime** | ISO 8601 | `2025-01-15T12:00:00Z` |

---

## 18. まとめ

### 18.1 API設計の特徴

- **REST原則準拠**: リソースベースURL、HTTPメソッドの適切な使用
- **RFC 9457準拠**: 統一されたエラーレスポンス形式
- **Pydanticバリデーション**: 型安全なリクエスト/レスポンス
- **OpenAPI自動生成**: Swagger UI/ReDocによるドキュメント
- **ページネーション**: offset/limit方式
- **レート制限**: 100req/min
- **RBAC統合**: エンドポイント単位の権限制御
- **非同期処理**: 高速なレスポンス

---

**ドキュメント管理情報:**

- **更新日**: 2025年11月29日
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - RBAC設計書: `03-security/01-rbac-design.md`
  - 認証・認可設計書: `03-security/02-authentication-design.md`
