# API仕様書

## 1. 概要

本文書は、genai-app-docsシステムのREST API仕様を定義します。
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

```mermaid
graph TB
    Root[/ Root]
    Health[/health Health Check]
    Metrics[/metrics Prometheus Metrics]

    APIv1[/api/v1 API Version 1]

    Users[/api/v1/users ユーザー管理]
    Projects[/api/v1/projects プロジェクト管理]
    ProjectMembers[/api/v1/projects/:id/members メンバー管理]
    ProjectFiles[/api/v1/projects/:id/files ファイル管理]
    Analysis[/api/v1/analysis 分析セッション]
    AnalysisTemplates[/api/v1/analysis/templates テンプレート]
    PPT[/api/v1/ppt PPT生成]
    DriverTree[/api/v1/driver-tree ドライバーツリー]

    Sample[/api/v1/sample-* サンプル機能]

    Root --> Health
    Root --> Metrics
    Root --> APIv1

    APIv1 --> Users
    APIv1 --> Projects
    Projects --> ProjectMembers
    Projects --> ProjectFiles
    APIv1 --> Analysis
    Analysis --> AnalysisTemplates
    APIv1 --> PPT
    APIv1 --> DriverTree
    APIv1 --> Sample

    style Root fill:#E8F5E9
    style APIv1 fill:#C5E1A5
    style Users fill:#AED581
    style Projects fill:#9CCC65
    style Analysis fill:#8BC34A
```

### 2.2 エンドポイント一覧

| カテゴリ | エンドポイント | 説明 |
|---------|---------------|------|
| **システム** | `GET /` | ルート（リダイレクト） |
| | `GET /health` | ヘルスチェック |
| | `GET /metrics` | Prometheusメトリクス |
| **ユーザー** | `/api/v1/users/*` | ユーザー管理 |
| **プロジェクト** | `/api/v1/projects/*` | プロジェクト管理 |
| **メンバー** | `/api/v1/projects/{id}/members/*` | プロジェクトメンバー管理 |
| **ファイル** | `/api/v1/projects/{id}/files/*` | プロジェクトファイル管理 |
| **分析** | `/api/v1/analysis/*` | 分析セッション管理 |
| **テンプレート** | `/api/v1/analysis/templates/*` | 分析テンプレート |
| **PPT生成** | `/api/v1/ppt/*` | PowerPoint生成 |
| **ドライバーツリー** | `/api/v1/driver-tree/*` | ドライバーツリー管理 |
| **サンプル** | `/api/v1/sample-*/*` | サンプル機能（旧実装） |

---

## 3. 認証・認可

### 3.1 認証フロー

```mermaid
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
```

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

```mermaid
graph LR
    subgraph "2xx Success"
        S200[200 OK]
        S201[201 Created]
        S204[204 No Content]
    end

    subgraph "4xx Client Errors"
        E400[400 Bad Request]
        E401[401 Unauthorized]
        E403[403 Forbidden]
        E404[404 Not Found]
        E409[409 Conflict]
        E422[422 Unprocessable Entity]
        E429[429 Too Many Requests]
    end

    subgraph "5xx Server Errors"
        E500[500 Internal Server Error]
        E503[503 Service Unavailable]
    end

    style S200 fill:#4CAF50
    style E400 fill:#FF9800
    style E500 fill:#F44336
```

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
| **503** | Service Unavailable | サービス停止中 |

---

## 5. システムエンドポイント

### 5.1 ルート

#### GET /

```mermaid
sequenceDiagram
    Client->>API: GET /
    API-->>Client: 302 Redirect to /docs
```

**リクエスト:**

```http
GET / HTTP/1.1
Host: localhost:8000
```

**レスポンス:**

```http
HTTP/1.1 302 Found
Location: /docs
```

### 5.2 ヘルスチェック

#### GET /health

システムの稼働状態を確認します。

**実装**: `src/app/api/routes/system/health.py`

**レスポンス:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

### 5.3 メトリクス

#### GET /metrics

Prometheusメトリクスを取得します。

**実装**: `src/app/api/routes/system/metrics.py`

**レスポンス:**

```text
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/projects",status="200"} 1234

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 800
http_request_duration_seconds_bucket{le="0.5"} 950
http_request_duration_seconds_bucket{le="1.0"} 990
http_request_duration_seconds_bucket{le="+Inf"} 1000
```

---

## 6. ユーザー管理API

### 6.1 ユーザー一覧取得

#### GET /api/v1/users

**実装**: `src/app/api/routes/v1/users/users.py`
**権限**: システム管理者のみ (SYSTEM_ADMIN)

**リクエスト:**

```http
GET /api/v1/users?skip=0&limit=20&is_active=true HTTP/1.1
Authorization: Bearer <token>
```

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| skip | integer | No | オフセット（デフォルト: 0） |
| limit | integer | No | 取得件数（デフォルト: 100、最大: 1000） |
| is_active | boolean | No | アクティブフラグフィルタ |
| system_role | string | No | システムロールフィルタ |

**レスポンス (200 OK):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "azure_oid": "12345678-1234-1234-1234-123456789abc",
      "email": "user@example.com",
      "display_name": "山田 太郎",
      "system_role": "user",
      "is_active": true,
      "last_login": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

### 6.2 現在のユーザー情報取得

#### GET /api/v1/users/me

**権限**: 認証済みユーザー

**リクエスト:**

```http
GET /api/v1/users/me HTTP/1.1
Authorization: Bearer <token>
```

**レスポンス (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "azure_oid": "12345678-1234-1234-1234-123456789abc",
  "email": "user@example.com",
  "display_name": "山田 太郎",
  "system_role": "user",
  "is_active": true,
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### 6.3 ユーザー情報更新

#### PATCH /api/v1/users/me

**権限**: 認証済みユーザー（自分自身のみ）

**リクエスト:**

```http
PATCH /api/v1/users/me HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "display_name": "山田 花子"
}
```

**レスポンス (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "display_name": "山田 花子",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

---

## 7. プロジェクト管理API

### 7.1 プロジェクト一覧取得

#### GET /api/v1/projects

**実装**: `src/app/api/routes/v1/projects/projects.py`
**権限**: 認証済みユーザー（自分がメンバーのプロジェクトのみ）

**リクエスト:**

```http
GET /api/v1/projects?skip=0&limit=20&is_active=true HTTP/1.1
Authorization: Bearer <token>
```

**レスポンス (200 OK):**

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "プロジェクトA",
      "code": "PROJECT_A",
      "description": "説明文",
      "is_active": true,
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-10T00:00:00Z",
      "updated_at": "2025-01-15T00:00:00Z",
      "member_count": 5,
      "file_count": 12,
      "user_role": "project_manager"
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 20
}
```

### 7.2 プロジェクト作成

#### POST /api/v1/projects

**権限**: 認証済みユーザー

**リクエスト:**

```http
POST /api/v1/projects HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "新規プロジェクト",
  "code": "NEW_PROJECT",
  "description": "プロジェクトの説明"
}
```

**レスポンス (201 Created):**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "新規プロジェクト",
  "code": "NEW_PROJECT",
  "description": "プロジェクトの説明",
  "is_active": true,
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

### 7.3 プロジェクト詳細取得

#### GET /api/v1/projects/{project_id}

**権限**: プロジェクトメンバー、またはシステム管理者

**リクエスト:**

```http
GET /api/v1/projects/660e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Authorization: Bearer <token>
```

**レスポンス (200 OK):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "プロジェクトA",
  "code": "PROJECT_A",
  "description": "説明文",
  "is_active": true,
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-10T00:00:00Z",
  "updated_at": "2025-01-15T00:00:00Z",
  "members": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "user@example.com",
      "user_display_name": "山田 太郎",
      "project_role": "project_manager",
      "joined_at": "2025-01-10T00:00:00Z"
    }
  ],
  "files": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "file_name": "data.csv",
      "file_size": 1048576,
      "content_type": "text/csv",
      "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-12T00:00:00Z"
    }
  ]
}
```

### 7.4 プロジェクト更新

#### PATCH /api/v1/projects/{project_id}

**権限**: PROJECT_MANAGER、またはシステム管理者

**リクエスト:**

```http
PATCH /api/v1/projects/660e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "プロジェクトA（更新）",
  "description": "更新された説明"
}
```

**レスポンス (200 OK):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "プロジェクトA（更新）",
  "description": "更新された説明",
  "updated_at": "2025-01-15T13:00:00Z"
}
```

### 7.5 プロジェクト削除

#### DELETE /api/v1/projects/{project_id}

**権限**: PROJECT_MANAGER、またはシステム管理者

**リクエスト:**

```http
DELETE /api/v1/projects/660e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Authorization: Bearer <token>
```

**レスポンス (204 No Content)**

---

## 8. プロジェクトメンバー管理API

### 8.1 データフロー

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant RBAC as RBAC Check
    participant Service
    participant DB

    Client->>API: POST /api/v1/projects/{id}/members
    API->>RBAC: 権限チェック<br/>(PROJECT_MANAGER/MODERATOR)
    RBAC-->>API: OK

    API->>Service: メンバー追加
    Service->>DB: ProjectMember作成
    Service->>DB: UserAccount取得
    DB-->>Service: メンバー情報
    Service-->>API: 成功レスポンス
    API-->>Client: 201 Created
```

### 8.2 メンバー一覧取得

#### GET /api/v1/projects/{project_id}/members

**権限**: プロジェクトメンバー、またはシステム管理者

**レスポンス (200 OK):**

```json
{
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "user@example.com",
      "user_display_name": "山田 太郎",
      "project_role": "project_manager",
      "joined_at": "2025-01-10T00:00:00Z",
      "created_at": "2025-01-10T00:00:00Z",
      "updated_at": "2025-01-10T00:00:00Z"
    }
  ],
  "total": 5
}
```

### 8.3 メンバー追加

#### POST /api/v1/projects/{project_id}/members

**権限**: PROJECT_MANAGER、PROJECT_MODERATOR、またはシステム管理者

**リクエスト:**

```http
POST /api/v1/projects/660e8400-e29b-41d4-a716-446655440001/members HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "project_role": "member"
}
```

**レスポンス (201 Created):**

```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "user_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "project_role": "member",
  "joined_at": "2025-01-15T14:00:00Z"
}
```

### 8.4 メンバーロール変更

#### PATCH /api/v1/projects/{project_id}/members/{member_id}

**権限**: PROJECT_MANAGER、PROJECT_MODERATOR、またはシステム管理者

**リクエスト:**

```http
PATCH /api/v1/projects/660e8400-e29b-41d4-a716-446655440001/members/880e8400-e29b-41d4-a716-446655440003 HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_role": "project_moderator"
}
```

**レスポンス (200 OK):**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "project_role": "project_moderator",
  "updated_at": "2025-01-15T15:00:00Z"
}
```

### 8.5 メンバー削除

#### DELETE /api/v1/projects/{project_id}/members/{member_id}

**権限**: PROJECT_MANAGER、PROJECT_MODERATOR、またはシステム管理者

**レスポンス (204 No Content)**

---

## 9. プロジェクトファイル管理API

### 9.1 ファイルアップロード

#### POST /api/v1/projects/{project_id}/files/upload

**実装**: `src/app/api/routes/v1/projects/files.py`
**権限**: MEMBER以上（VIEWER除く）

**リクエスト:**

```http
POST /api/v1/projects/660e8400-e29b-41d4-a716-446655440001/files/upload HTTP/1.1
Authorization: Bearer <token>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="data.csv"
Content-Type: text/csv

<バイナリデータ>
------WebKitFormBoundary--
```

**レスポンス (201 Created):**

```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "file_name": "data.csv",
  "file_path": "projects/660e8400-e29b-41d4-a716-446655440001/data.csv",
  "file_size": 1048576,
  "content_type": "text/csv",
  "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T16:00:00Z"
}
```

### 9.2 ファイル情報取得

#### GET /api/v1/projects/{project_id}/files/{file_id}

**権限**: プロジェクトメンバー、またはシステム管理者

**レスポンス (200 OK):**

```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "file_name": "data.csv",
  "file_path": "projects/660e8400-e29b-41d4-a716-446655440001/data.csv",
  "file_size": 1048576,
  "content_type": "text/csv",
  "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T16:00:00Z"
}
```

### 9.3 ファイルダウンロード

#### GET /api/v1/projects/{project_id}/files/{file_id}/download

**権限**: プロジェクトメンバー、またはシステム管理者

**レスポンス (200 OK):**

```http
HTTP/1.1 200 OK
Content-Type: text/csv
Content-Disposition: attachment; filename="data.csv"
Content-Length: 1048576

<バイナリデータ>
```

### 9.4 ファイル削除

#### DELETE /api/v1/projects/{project_id}/files/{file_id}

**権限**: MEMBER以上（アップロードユーザー、またはPROJECT_MANAGER）

**レスポンス (204 No Content)**

---

## 10. 分析機能API

### 10.1 分析セッションフロー

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AnalysisService
    participant AIAgent
    participant LLM

    Client->>API: POST /api/v1/analysis/sessions<br/>セッション作成
    API->>AnalysisService: セッション作成
    AnalysisService->>AIAgent: エージェント初期化
    AIAgent-->>AnalysisService: 初期化完了
    AnalysisService-->>API: セッションID
    API-->>Client: 201 Created

    Client->>API: POST /api/v1/analysis/sessions/{id}/chat<br/>チャット送信
    API->>AnalysisService: メッセージ処理
    AnalysisService->>AIAgent: エージェント実行
    AIAgent->>LLM: LLM API呼び出し
    LLM-->>AIAgent: レスポンス
    AIAgent->>AIAgent: ツール実行<br/>(filter/aggregate/transform)
    AIAgent-->>AnalysisService: 実行結果
    AnalysisService->>API: レスポンス
    API-->>Client: 200 OK
```

### 10.2 分析セッション作成

#### POST /api/v1/analysis/sessions

**実装**: `src/app/api/routes/v1/analysis/analysis.py`
**権限**: MEMBER以上

**リクエスト:**

```http
POST /api/v1/analysis/sessions HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "original_file_id": "cc0e8400-e29b-41d4-a716-446655440007",
  "template_id": "dd0e8400-e29b-41d4-a716-446655440008"
}
```

**レスポンス (201 Created):**

```json
{
  "id": "ee0e8400-e29b-41d4-a716-446655440009",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "creator_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_file_id": "cc0e8400-e29b-41d4-a716-446655440007",
  "template_id": "dd0e8400-e29b-41d4-a716-446655440008",
  "created_at": "2025-01-15T17:00:00Z"
}
```

### 10.3 チャット送信

#### POST /api/v1/analysis/sessions/{session_id}/chat

**権限**: セッション作成者、またはPROJECT_MANAGER

**リクエスト:**

```http
POST /api/v1/analysis/sessions/ee0e8400-e29b-41d4-a716-446655440009/chat HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "売上が100万円以上のデータを抽出してください"
}
```

**レスポンス (200 OK):**

```json
{
  "session_id": "ee0e8400-e29b-41d4-a716-446655440009",
  "message": "売上が100万円以上のデータを抽出しました。該当件数: 42件",
  "steps_executed": [
    {
      "step_type": "filter",
      "parameters": {
        "column": "sales",
        "operator": "gte",
        "value": 1000000
      },
      "affected_rows": 42
    }
  ],
  "timestamp": "2025-01-15T17:05:00Z"
}
```

### 10.4 スナップショット作成

#### POST /api/v1/analysis/sessions/{session_id}/snapshots

**権限**: セッション作成者、またはPROJECT_MANAGER

**リクエスト:**

```http
POST /api/v1/analysis/sessions/ee0e8400-e29b-41d4-a716-446655440009/snapshots HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "フィルタ後のデータ"
}
```

**レスポンス (201 Created):**

```json
{
  "snapshot_id": "ff0e8400-e29b-41d4-a716-446655440010",
  "session_id": "ee0e8400-e29b-41d4-a716-446655440009",
  "name": "フィルタ後のデータ",
  "created_at": "2025-01-15T17:10:00Z"
}
```

---

## 11. 分析テンプレートAPI

### 11.1 テンプレート一覧取得

#### GET /api/v1/analysis/templates

**実装**: `src/app/api/routes/v1/analysis/templates.py`
**権限**: 認証済みユーザー

**レスポンス (200 OK):**

```json
{
  "items": [
    {
      "id": "dd0e8400-e29b-41d4-a716-446655440008",
      "name": "売上分析テンプレート",
      "description": "売上データの標準分析テンプレート",
      "is_active": true,
      "charts": [
        {
          "chart_type": "line",
          "chart_config": {
            "title": "月別売上推移",
            "x_axis": "month",
            "y_axis": "sales"
          },
          "display_order": 1
        }
      ],
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 5
}
```

### 11.2 テンプレート詳細取得

#### GET /api/v1/analysis/templates/{template_id}

**レスポンス (200 OK):**

```json
{
  "id": "dd0e8400-e29b-41d4-a716-446655440008",
  "name": "売上分析テンプレート",
  "description": "売上データの標準分析テンプレート",
  "default_config": {
    "validation_rules": [
      {
        "field": "sales",
        "rule": "required|numeric"
      }
    ]
  },
  "is_active": true,
  "charts": [
    {
      "id": "gg0e8400-e29b-41d4-a716-446655440011",
      "chart_type": "line",
      "chart_config": {
        "title": "月別売上推移",
        "x_axis": "month",
        "y_axis": "sales"
      },
      "display_order": 1
    }
  ],
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## 12. ページネーション

### 12.1 ページネーション仕様

すべての一覧取得APIはoffset/limit方式のページネーションをサポートします。

**共通クエリパラメータ:**

| パラメータ | 型 | デフォルト | 最大値 | 説明 |
|----------|-----|-----------|--------|------|
| skip | integer | 0 | - | スキップする件数 |
| limit | integer | 100 | 1000 | 取得件数 |

**レスポンス構造:**

```json
{
  "items": [],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

### 12.2 ページネーション計算

```mermaid
graph LR
    A[total: 42件] --> B[limit: 20]
    B --> C[Page 1: skip=0<br/>items 1-20]
    B --> D[Page 2: skip=20<br/>items 21-40]
    B --> E[Page 3: skip=40<br/>items 41-42]

    style C fill:#C8E6C9
    style D fill:#A5D6A7
    style E fill:#81C784
```

**ページ計算例:**

```python
# 総ページ数
total_pages = (total + limit - 1) // limit

# 次のページ
next_skip = skip + limit if skip + limit < total else None

# 前のページ
prev_skip = max(skip - limit, 0) if skip > 0 else None
```

---

## 13. リクエスト制限

### 13.1 レート制限

すべてのAPIエンドポイントはレート制限の対象です。

**制限値:**

- **デフォルト**: 100リクエスト/分
- **ヘッダー情報**:
  - `X-RateLimit-Limit`: 制限値
  - `X-RateLimit-Remaining`: 残りリクエスト数
  - `X-RateLimit-Reset`: リセット時刻（UNIXタイムスタンプ）

**レート制限超過時のレスポンス:**

```json
{
  "type": "https://httpstatuses.com/429",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit exceeded. Please retry after 60 seconds.",
  "instance": "/api/v1/projects"
}
```

### 13.2 ファイルサイズ制限

**アップロード制限:**

- **最大ファイルサイズ**: 100MB
- **対象エンドポイント**: `/api/v1/projects/{id}/files/upload`

**制限超過時のレスポンス:**

```json
{
  "type": "https://httpstatuses.com/413",
  "title": "Payload Too Large",
  "status": 413,
  "detail": "File size exceeds 100MB limit",
  "instance": "/api/v1/projects/660e8400-e29b-41d4-a716-446655440001/files/upload"
}
```

---

## 14. バリデーション

### 14.1 リクエストバリデーション

すべてのリクエストボディはPydanticスキーマでバリデーションされます。

**バリデーションエラーレスポンス (422 Unprocessable Entity):**

```json
{
  "type": "https://httpstatuses.com/422",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed",
  "instance": "/api/v1/projects",
  "errors": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "code"],
      "msg": "string does not match regex '^[A-Z0-9_]+$'",
      "type": "value_error.str.regex",
      "ctx": {
        "pattern": "^[A-Z0-9_]+$"
      }
    }
  ]
}
```

### 14.2 共通バリデーションルール

| フィールド | ルール | 説明 |
|----------|--------|------|
| **UUID** | uuid4形式 | `550e8400-e29b-41d4-a716-446655440000` |
| **email** | RFC 5322準拠 | `user@example.com` |
| **code** | `^[A-Z0-9_]+$` | 大文字英数字とアンダースコアのみ |
| **name** | 1-255文字 | 任意の文字列 |
| **is_active** | boolean | `true` or `false` |
| **datetime** | ISO 8601 | `2025-01-15T12:00:00Z` |

---

## 15. まとめ

### 15.1 API設計の特徴

✅ **REST原則準拠**: リソースベースURL、HTTPメソッドの適切な使用
✅ **RFC 9457準拠**: 統一されたエラーレスポンス形式
✅ **Pydanticバリデーション**: 型安全なリクエスト/レスポンス
✅ **OpenAPI自動生成**: Swagger UI/ReDocによるドキュメント
✅ **ページネーション**: offset/limit方式
✅ **レート制限**: 100req/min
✅ **RBAC統合**: エンドポイント単位の権限制御
✅ **非同期処理**: 高速なレスポンス

### 15.2 今後の拡張提案

- WebSocket対応（リアルタイム分析）
- GraphQL API追加
- API バージョニング戦略（v2以降）
- Webhook対応
- Batch API（一括操作）

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - RBAC設計書: `03-security/01-rbac-design.md`
  - 認証・認可設計書: `03-security/02-authentication-design.md`
