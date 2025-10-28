# API仕様書

バックエンドAPIの完全なエンドポイント仕様とリクエスト/レスポンス形式を記載します。

## 目次

- [基本情報](#基本情報)
- [認証](#認証)
- [エンドポイント一覧](#エンドポイント一覧)
- [エージェントAPI](#エージェントapi)
- [ファイルAPI](#ファイルapi)
- [ヘルスチェック](#ヘルスチェック)
- [エラーレスポンス](#エラーレスポンス)

---

## 基本情報

### ベースURL

```text
開発環境: http://localhost:8000
本番環境: https://api.your-domain.com
```

### コンテンツタイプ

```text
Content-Type: application/json
```

### レート制限

- デフォルト: 100リクエスト/分
- レート制限ヘッダー:
  - `X-RateLimit-Limit`: 期間内の最大リクエスト数
  - `X-RateLimit-Remaining`: 残りリクエスト数
  - `X-RateLimit-Reset`: リセット時刻（Unixタイムスタンプ）

---

## 認証

現在の実装では、オプションの認証をサポートしています。

### 認証方式

#### Bearer Token（JWT）

```http
Authorization: Bearer <your_jwt_token>
```

### トークン取得

POST `/api/v1/sample-users/sample-login` でメールアドレスとパスワードを送信することで、
JWTアクセストークンとリフレッシュトークンを取得できます。

---

## エンドポイント一覧

| メソッド | エンドポイント | 説明 | 認証 |
|---------|--------------|------|------|
| GET | `/` | ルートエンドポイント | 不要 |
| GET | `/health` | ヘルスチェック | 不要 |
| POST | `/api/v1/sample-users` | ユーザー登録 | 不要 |
| POST | `/api/v1/sample-users/sample-login` | ログイン | 不要 |
| POST | `/api/v1/sample-users/refresh` | トークンリフレッシュ | 不要 |
| GET | `/api/v1/sample-users/sample-me` | 現在のユーザー情報取得 | 必須 |
| POST | `/api/v1/sample-users/api-key` | APIキー生成 | 必須 |
| GET | `/api/v1/sample-users/{user_id}` | 特定ユーザー取得（管理者のみ） | 必須 |
| GET | `/api/v1/sample-users` | ユーザー一覧取得（管理者のみ） | 必須 |
| POST | `/api/v1/sample-agents/sample-chat` | AIエージェントとチャット | オプション |
| GET | `/api/v1/sample-agents/sample-sessions/{session_id}` | セッション情報取得 | オプション |
| DELETE | `/api/v1/sample-agents/sample-sessions/{session_id}` | セッション削除 | オプション |
| POST | `/api/v1/sample-files/sample-upload` | ファイルアップロード | オプション |
| GET | `/api/v1/sample-files/sample-download/{file_id}` | ファイルダウンロード | オプション |
| DELETE | `/api/v1/sample-files/sample-{file_id}` | ファイル削除 | オプション |
| GET | `/api/v1/sample-files/sample-list` | ファイル一覧取得 | オプション |

---

## ユーザーAPI

### ユーザー登録 - POST /api/v1/sample-users

新しいユーザーアカウントを作成します。

#### リクエスト

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

#### レスポンス（201 Created）

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-10-22T00:00:00Z",
  "updated_at": "2025-10-22T00:00:00Z"
}
```

---

### ログイン - POST /api/v1/sample-users/sample-login

メールアドレスとパスワードで認証し、JWTトークンを取得します。

#### リクエスト

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### レスポンス（200 OK）

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**セキュリティ機能:**

- ログイン失敗5回でアカウントロック（1時間）
- ログイン監査（last_login_at, last_login_ip）

---

### トークンリフレッシュ - POST /api/v1/sample-users/refresh

リフレッシュトークンを使用して新しいアクセストークンを取得します。

#### リクエスト

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### レスポンス（200 OK）

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**注意:**

- リフレッシュトークンの有効期限は7日間です
- データベースに保存されたトークンと照合されます

---

### APIキー生成 - POST /api/v1/sample-users/api-key

認証済みユーザーのAPIキーを生成します（認証必須）。

#### リクエスト

リクエストボディなし。`Authorization: Bearer <token>` ヘッダーが必要です。

#### レスポンス（200 OK）

```json
{
  "api_key": "dGhpcyBpcyBhIHNlY3VyZSByYW5kb20gYXBpIGtleQ...",
  "created_at": "2025-10-22T00:00:00Z",
  "message": "APIキーは一度しか表示されません。安全に保管してください。"
}
```

**注意:**

- APIキーは一度しか表示されません
- 既存のAPIキーがある場合は上書きされます

---

### 現在のユーザー情報取得 - GET /api/v1/sample-users/sample-me

認証済みユーザー自身の情報を取得します（認証必須）。

#### レスポンス（200 OK）

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-10-22T00:00:00Z",
  "updated_at": "2025-10-22T00:00:00Z"
}
```

---

## エージェントAPI

**実装状況**: 現在はMVP（最低限実装）として、エコーバック機能を提供しています。
将来的にLangChain/LangGraphを使用した本格的なAI統合に置き換え可能です。

### チャット - POST /api/v1/sample-agents/sample-chat

AIエージェントとチャットします。

#### リクエスト

```json
{
  "message": "こんにちは、今日の天気を教えてください",
  "session_id": "session_abc123",
  "context": {
    "location": "Tokyo",
    "user_preference": "detailed"
  }
}
```

#### パラメータ

| フィールド | 型 | 必須 | 説明 |
|----------|---|------|------|
| message | string | ○ | ユーザーメッセージ（1-10000文字） |
| session_id | string | × | セッション識別子（新規の場合は省略） |
| context | object | × | 追加コンテキスト情報 |

#### レスポンス

#### 成功（200 OK）

```json
{
  "response": "エコー: こんにちは、今日の天気を教えてください",
  "session_id": "session_abc123",
  "tokens_used": 150,
  "model": "echo-v1"
}
```

**注意**: 現在の実装はエコーバック機能（入力メッセージに「エコー: 」を付けて返す）です。

#### レスポンスフィールド

| フィールド | 型 | 説明 |
|----------|---|------|
| response | string | エージェントの応答メッセージ |
| session_id | string | セッション識別子 |
| tokens_used | integer | 使用されたトークン数（オプション） |
| model | string | 使用されたモデル名（オプション） |

#### cURLサンプル

```bash
curl -X POST "http://localhost:8000/api/v1/sample-agents/sample-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "こんにちは",
    "session_id": null,
    "context": {}
  }'
```

---

### セッション取得 - GET /api/v1/sample-agents/sample-sessions/{session_id}

セッション情報と会話履歴を取得します。

#### パスパラメータ

| パラメータ | 型 | 説明 |
|----------|---|------|
| session_id | string | セッション識別子 |

#### レスポンス

#### 成功（200 OK）

```json
{
  "session_id": "session_abc123",
  "created_at": "2025-10-14T10:30:00Z",
  "updated_at": "2025-10-14T11:45:00Z",
  "messages": [
    {
      "role": "user",
      "content": "こんにちは",
      "timestamp": "2025-10-14T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "こんにちは！何かお手伝いできますか？",
      "timestamp": "2025-10-14T10:30:05Z"
    }
  ],
  "metadata": {
    "location": "Tokyo"
  }
}
```

#### cURLサンプル

```bash
curl -X GET "http://localhost:8000/api/v1/sample-agents/sample-sessions/session_abc123"
```

---

### セッション削除 - DELETE /api/v1/sample-agents/sample-sessions/{session_id}

セッションと関連するメッセージを削除します。

#### パスパラメータ

| パラメータ | 型 | 説明 |
|----------|---|------|
| session_id | string | セッション識別子 |

#### レスポンス

#### 成功（200 OK）

```json
{
  "message": "Session session_abc123 deleted successfully"
}
```

#### cURLサンプル

```bash
curl -X DELETE "http://localhost:8000/api/v1/sample-agents/sample-sessions/session_abc123"
```

---

## ファイルAPI

### ファイルアップロード - POST /api/v1/sample-files/sample-upload

ファイルをアップロードします。

#### リクエスト

**Content-Type:** `multipart/form-data`

```text
file: (binary)
```

#### レスポンス

#### 成功（200 OK）

```json
{
  "file_id": "file_xyz789",
  "filename": "document.pdf",
  "size": 1048576,
  "content_type": "application/pdf",
  "message": "File uploaded successfully"
}
```

#### レスポンスフィールド

| フィールド | 型 | 説明 |
|----------|---|------|
| file_id | string | 一意のファイル識別子 |
| filename | string | 元のファイル名 |
| size | integer | ファイルサイズ（バイト） |
| content_type | string | ファイルのMIMEタイプ |
| message | string | 成功メッセージ |

#### 制限事項

- **最大ファイルサイズ**: 10MB
- **許可されているファイルタイプ**:
  - テキスト: `text/plain`, `text/csv`, `application/json`
  - 画像: `image/png`, `image/jpeg`, `image/gif`
  - ドキュメント: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **保存先**: ローカルファイルシステム（`./uploads` ディレクトリ）

#### cURLサンプル

```bash
curl -X POST "http://localhost:8000/api/v1/sample-files/sample-upload" \
  -F "file=@/path/to/document.pdf"
```

---

### ファイルダウンロード - GET /api/v1/sample-files/sample-download/{file_id}

ファイルをダウンロードします。

#### パスパラメータ

| パラメータ | 型 | 説明 |
|----------|---|------|
| file_id | string | ファイル識別子 |

#### レスポンス

#### 成功（200 OK）

バイナリストリームとして返却

#### レスポンスヘッダー

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"
```

#### cURLサンプル

```bash
curl -X GET "http://localhost:8000/api/v1/sample-files/sample-download/file_xyz789" \
  -o downloaded_file.pdf
```

---

### ファイル削除 - DELETE /api/v1/sample-files/sample-{file_id}

ファイルを削除します。

#### パスパラメータ

| パラメータ | 型 | 説明 |
|----------|---|------|
| file_id | string | ファイル識別子 |

#### レスポンス

#### 成功（200 OK）

```json
{
  "file_id": "file_xyz789",
  "message": "File file_xyz789 deleted successfully"
}
```

#### cURLサンプル

```bash
curl -X DELETE "http://localhost:8000/api/v1/sample-files/sample-file_xyz789"
```

---

### ファイル一覧取得 - GET /api/v1/sample-files/sample-list

アップロードされたファイル一覧を取得します。

#### クエリパラメータ

| パラメータ | 型 | デフォルト | 説明 |
|----------|---|----------|------|
| skip | integer | 0 | スキップするファイル数 |
| limit | integer | 100 | 返す最大ファイル数 |

#### レスポンス

#### 成功（200 OK）

```json
{
  "files": [
    {
      "file_id": "file_xyz789",
      "filename": "document.pdf",
      "size": 1048576,
      "content_type": "application/pdf",
      "created_at": "2025-10-14T10:30:00Z"
    },
    {
      "file_id": "file_abc456",
      "filename": "image.png",
      "size": 524288,
      "content_type": "image/png",
      "created_at": "2025-10-14T11:00:00Z"
    }
  ],
  "total": 2
}
```

#### cURLサンプル

```bash
curl -X GET "http://localhost:8000/api/v1/sample-files/sample-list?skip=0&limit=10"
```

---

## ヘルスチェック

### ルートエンドポイント - GET /

アプリケーション情報を返します。

#### レスポンス

```json
{
  "message": "Welcome to camp-backend",
  "version": "0.1.0",
  "docs": "/docs"
}
```

---

### ヘルスチェック - GET /health

アプリケーションのヘルス状態を確認します。データベースとRedisの接続状態も含まれます。

#### レスポンス

```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T12:00:00.000000Z",
  "version": "0.1.0",
  "environment": "development",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

#### レスポンスフィールド

| フィールド | 型 | 説明 |
|----------|---|------|
| status | string | 全体のステータス（"healthy" または "degraded"） |
| timestamp | string | チェック実行時刻（ISO 8601形式、UTC） |
| version | string | アプリケーションバージョン |
| environment | string | 実行環境（development/staging/production） |
| services | object | 各サービスの個別ステータス |
| services.database | string | データベース接続状態（"healthy" または "unhealthy"） |
| services.redis | string | Redis接続状態（"healthy", "unhealthy", "disabled"） |

---

## エラーレスポンス

### エラーフォーマット

すべてのエラーレスポンスは以下の形式で返却されます。

```json
{
  "error": "エラーメッセージ",
  "details": {
    "field": "追加情報"
  }
}
```

### HTTPステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 400 | 不正なリクエスト |
| 401 | 認証エラー |
| 403 | 認可エラー（権限不足） |
| 404 | リソースが見つからない |
| 422 | バリデーションエラー |
| 429 | レート制限超過 |
| 500 | サーバーエラー |
| 502 | 外部サービスエラー |

### エラー例

#### 404 Not Found

```json
{
  "error": "Resource not found",
  "details": {
    "resource": "session",
    "id": "session_invalid"
  }
}
```

#### 422 Validation Error

```json
{
  "error": "Validation error",
  "details": {
    "loc": ["body", "message"],
    "msg": "ensure this value has at least 1 characters",
    "type": "value_error.any_str.min_length"
  }
}
```

#### 429 Rate Limit Exceeded

```json
{
  "error": "Rate limit exceeded",
  "details": {
    "retry_after": 60
  }
}
```

---

## OpenAPI/Swagger仕様

### 自動生成ドキュメント

FastAPIは自動的にOpenAPI仕様を生成します。

**Swagger UI**: `http://localhost:8000/docs`
**ReDoc**: `http://localhost:8000/redoc`
**OpenAPI JSON**: `http://localhost:8000/openapi.json`

### OpenAPIスキーマのダウンロード

```bash
curl -X GET "http://localhost:8000/openapi.json" -o openapi.json
```

---

## APIクライアント例

### Python

```python
import requests

# チャットAPI
response = requests.post(
    "http://localhost:8000/api/v1/sample-agents/sample-chat",
    json={
        "message": "こんにちは",
        "session_id": None
    }
)
data = response.json()
print(data["response"])

# ファイルアップロード
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/api/v1/sample-files/sample-upload",
        files=files
    )
    file_data = response.json()
    print(f"Uploaded: {file_data['file_id']}")
```

### JavaScript

```javascript
// チャットAPI
const response = await fetch('http://localhost:8000/api/v1/sample-agents/sample-chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'こんにちは',
    session_id: null
  })
});
const data = await response.json();
console.log(data.response);

// ファイルアップロード
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/api/v1/sample-files/sample-upload', {
  method: 'POST',
  body: formData
});
const fileData = await uploadResponse.json();
console.log('Uploaded:', fileData.file_id);
```

---

## 参考リンク

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [OpenAPI仕様](https://swagger.io/specification/)
- [HTTPステータスコード](https://developer.mozilla.org/ja/docs/Web/HTTP/Status)
