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

    UserAccount[/api/v1/user_account ユーザー管理]
    Project[/api/v1/project プロジェクト管理]
    ProjectMember[/api/v1/project/:id/member メンバー管理]
    ProjectFile[/api/v1/project/:id/file ファイル管理]
    AnalysisSession[/api/v1/analysis/session 分析セッション]
    AnalysisTemplate[/api/v1/analysis/template テンプレート]
    DriverTreeFile[/api/v1/driver-tree/file ファイル管理]
    DriverTreeTree[/api/v1/driver-tree/tree ツリー管理]
    DriverTreeNode[/api/v1/driver-tree/node ノード管理]
    Dashboard[/api/v1/dashboard ダッシュボード]
    Admin[/api/v1/admin システム管理]

    Root --> Health
    Root --> Metrics
    Root --> APIv1

    APIv1 --> UserAccount
    APIv1 --> Project
    Project --> ProjectMember
    Project --> ProjectFile
    APIv1 --> AnalysisSession
    APIv1 --> AnalysisTemplate
    APIv1 --> DriverTreeFile
    APIv1 --> DriverTreeTree
    APIv1 --> DriverTreeNode
    APIv1 --> Dashboard
    APIv1 --> Admin

    style Root fill:#E8F5E9
    style APIv1 fill:#C5E1A5
    style UserAccount fill:#AED581
    style Project fill:#9CCC65
    style AnalysisSession fill:#8BC34A
    style DriverTreeTree fill:#7CB342
:::

### 2.2 エンドポイント一覧

| カテゴリ | エンドポイント | 説明 | 詳細設計書 |
|---------|---------------|------|-----------|
| **システム** | `GET /` | ルート（アプリ情報） | - |
| | `GET /health` | ヘルスチェック | - |
| | `GET /metrics` | Prometheusメトリクス | - |
| **ユーザー** | `/api/v1/user_account/*` | ユーザー管理 | [03-user-management](../03-user-management/) |
| **プロジェクト** | `/api/v1/project/*` | プロジェクト管理 | [04-project-management](../04-project-management/) |
| **メンバー** | `/api/v1/project/{id}/member/*` | プロジェクトメンバー管理 | [04-project-management](../04-project-management/) |
| **ファイル** | `/api/v1/project/{id}/file/*` | プロジェクトファイル管理 | [04-project-management](../04-project-management/) |
| **分析セッション** | `/api/v1/analysis/session/*` | 分析セッション管理 | [05-analysis](../05-analysis/) |
| **分析テンプレート** | `/api/v1/analysis/template/*` | 分析テンプレート | [08-template](../08-template/) |
| **ドライバーツリーファイル** | `/api/v1/driver-tree/file/*` | ファイル管理 | [06-driver-tree](../06-driver-tree/) |
| **ドライバーツリー** | `/api/v1/driver-tree/tree/*` | ツリー管理 | [06-driver-tree](../06-driver-tree/) |
| **ドライバーツリーノード** | `/api/v1/driver-tree/node/*` | ノード管理 | [06-driver-tree](../06-driver-tree/) |
| **ダッシュボード** | `/api/v1/dashboard/*` | ダッシュボード | [07-dashboard](../07-dashboard/) |
| **検索** | `/api/v1/search` | グローバル検索 | [02-common-ui](../02-common-ui/) |
| **通知** | `/api/v1/notifications/*` | ユーザー通知 | [02-common-ui](../02-common-ui/) |
| **システム管理** | `/api/v1/admin/*` | システム管理 | [11-system-admin](../11-system-admin/) |

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
  "type": "about:blank",
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
  "type": "about:blank",
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

| コード | 説明 | 使用ケース | Exception |
|-------|------|----------|-----------|
| **200** | OK | 成功（取得、更新） | - |
| **201** | Created | リソース作成成功 | - |
| **204** | No Content | 削除成功 | - |
| **400** | Bad Request | リクエストの形式エラー | `BadRequestError` |
| **401** | Unauthorized | 認証エラー | `AuthenticationError` |
| **403** | Forbidden | 権限不足 | `AuthorizationError` |
| **404** | Not Found | リソース未発見 | `NotFoundError` |
| **409** | Conflict | リソース競合 | `ConflictError` |
| **413** | Payload Too Large | ファイルサイズ超過 | `PayloadTooLargeError` |
| **415** | Unsupported Media Type | 非対応ファイル形式 | `UnsupportedMediaTypeError` |
| **422** | Unprocessable Entity | バリデーションエラー | `ValidationError` |
| **429** | Too Many Requests | レート制限超過 | `RateLimitExceededError` |
| **500** | Internal Server Error | サーバーエラー | `DatabaseError` |
| **502** | Bad Gateway | 外部サービスエラー | `ExternalServiceError` |
| **503** | Service Unavailable | サービス一時停止 | `ServiceUnavailableError` |

### 4.3 Exception階層

```
AppException（基底クラス）
├── BadRequestError (400) - リクエスト形式エラー
├── AuthenticationError (401) - 認証失敗
├── AuthorizationError (403) - 権限不足
├── NotFoundError (404) - リソース未検出
├── ConflictError (409) - リソース競合
├── PayloadTooLargeError (413) - ペイロードサイズ超過
├── UnsupportedMediaTypeError (415) - 非対応ファイルタイプ
├── ValidationError (422) - バリデーションエラー
├── RateLimitExceededError (429) - レート制限超過
├── DatabaseError (500) - データベース操作エラー
├── ExternalServiceError (502) - 外部サービスエラー
└── ServiceUnavailableError (503) - サービス一時停止
```

**実装**: `src/app/core/exceptions.py`

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

## 6. ページネーション

### 6.1 ページネーション仕様

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

## 7. リクエスト制限

### 7.1 レート制限

- **デフォルト**: 100リクエスト/分
- **ヘッダー情報**:
  - `X-RateLimit-Limit`: 制限値
  - `X-RateLimit-Remaining`: 残りリクエスト数
  - `X-RateLimit-Reset`: リセット時刻

### 7.2 ファイルサイズ制限

| 対象 | 最大サイズ | 超過時 |
|------|----------|--------|
| ドライバーツリーファイル | 50MB | 413 Payload Too Large |
| プロジェクトファイル | 100MB | 413 Payload Too Large |

---

## 8. バリデーション

### 8.1 共通バリデーションルール

| フィールド | ルール | 説明 |
|----------|--------|------|
| **UUID** | uuid4形式 | `550e8400-e29b-41d4-a716-446655440000` |
| **email** | RFC 5322準拠 | `user@example.com` |
| **code** | `^[A-Z0-9_]+$` | 大文字英数字とアンダースコアのみ |
| **name** | 1-255文字 | 任意の文字列 |
| **is_active** | boolean | `true` or `false` |
| **datetime** | ISO 8601 | `2025-01-15T12:00:00Z` |

---

## 9. まとめ

### 9.1 API設計の特徴

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

- **更新日**: 2025年1月1日
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - RBAC設計書: `03-security/01-rbac-design.md`
  - 認証・認可設計書: `03-security/02-authentication-design.md`
