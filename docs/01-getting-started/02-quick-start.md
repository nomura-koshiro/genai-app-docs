# クイックスタートガイド

このガイドでは、AI Agent Appを最速で起動し、基本的なAPI操作を行う方法を説明します。

## 最速で起動する

### 1. 必要最小限のセットアップ

```bash
# 1. 依存関係のインストール
uv sync

# 2. 環境変数ファイルの作成
cp .env.example .env

# 3. APIキーの設定（.envファイルを編集）
# ANTHROPIC_API_KEY=your_key_here

# 4. アプリケーション起動
uv run ai-agent-app
```

### 2. 起動確認

アプリケーションが起動すると、以下のメッセージが表示されます：

```
Starting AI Agent App v0.1.0
Environment: development
Database: sqlite+aiosqlite:///./app.db
Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

ブラウザで http://localhost:8000 にアクセスして動作を確認します。

## APIドキュメントの確認

FastAPIは自動的に対話型APIドキュメントを生成します。

### Swagger UI（推奨）

最も使いやすい対話型ドキュメント：

**URL**: http://localhost:8000/docs

**特徴**:
- すべてのエンドポイントを一覧表示
- 各エンドポイントの詳細説明とパラメータ
- 「Try it out」ボタンで直接APIをテスト可能
- リクエスト/レスポンスの例を表示

### ReDoc

読みやすいドキュメント：

**URL**: http://localhost:8000/redoc

**特徴**:
- より読みやすいレイアウト
- 印刷やPDF化に適している
- スキーマの詳細表示

## 基本的なAPI呼び出し例

### 1. ヘルスチェック

アプリケーションの状態を確認します。

```bash
curl http://localhost:8000/health
```

**レスポンス**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-14T08:00:00.000000",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2. ユーザー登録（認証なし）

新しいユーザーを作成します（実装されている場合）。

```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

### 3. ファイルアップロード

ファイルをアップロードします。

```bash
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/path/to/your/file.txt"
```

**レスポンス例**:
```json
{
  "id": 1,
  "filename": "file.txt",
  "content_type": "text/plain",
  "size": 1024,
  "storage_path": "uploads/abc123/file.txt",
  "created_at": "2025-10-14T08:00:00"
}
```

### 4. ファイル一覧取得

アップロードされたファイルの一覧を取得します。

```bash
curl -X GET http://localhost:8000/api/files/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**レスポンス例**:
```json
{
  "files": [
    {
      "id": 1,
      "filename": "file.txt",
      "content_type": "text/plain",
      "size": 1024,
      "created_at": "2025-10-14T08:00:00"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### 5. AI Agentとのチャット

AI Agentにメッセージを送信します。

```bash
curl -X POST http://localhost:8000/api/agents/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "message": "こんにちは！",
    "session_id": "optional-session-id"
  }'
```

**レスポンス例**:
```json
{
  "response": "こんにちは！どのようにお手伝いできますか？",
  "session_id": "abc123",
  "message_id": "msg_456"
}
```

## Pythonでの使用例

### requests ライブラリを使用

```python
import requests

BASE_URL = "http://localhost:8000"

# ヘルスチェック
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# ファイルアップロード
with open("test.txt", "rb") as f:
    files = {"file": f}
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    response = requests.post(
        f"{BASE_URL}/api/files/upload",
        files=files,
        headers=headers
    )
    print(response.json())

# AI Agentとのチャット
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}
data = {
    "message": "Hello!",
    "session_id": "test-session"
}
response = requests.post(
    f"{BASE_URL}/api/agents/chat",
    json=data,
    headers=headers
)
print(response.json())
```

### httpx ライブラリを使用（非同期）

```python
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient() as client:
        # ヘルスチェック
        response = await client.get(f"{BASE_URL}/health")
        print(response.json())

        # AI Agentとのチャット
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_TOKEN"
        }
        data = {"message": "Hello!", "session_id": "test"}
        response = await client.post(
            f"{BASE_URL}/api/agents/chat",
            json=data,
            headers=headers
        )
        print(response.json())

asyncio.run(main())
```

## Swagger UIでのテスト手順

### 1. エンドポイントの選択

1. http://localhost:8000/docs にアクセス
2. テストしたいエンドポイント（例: `POST /api/agents/chat`）をクリック
3. 「Try it out」ボタンをクリック

### 2. パラメータの入力

リクエストボディやパラメータを入力します：

```json
{
  "message": "こんにちは！",
  "session_id": "test-session"
}
```

### 3. 認証の設定（必要な場合）

1. ページ上部の「Authorize」ボタンをクリック
2. トークンを入力: `Bearer YOUR_TOKEN_HERE`
3. 「Authorize」をクリック

### 4. リクエストの実行

1. 「Execute」ボタンをクリック
2. レスポンスが表示されます
   - ステータスコード
   - レスポンスボディ
   - レスポンスヘッダー

## よくある使用パターン

### パターン1: ファイルベースの質問応答

```bash
# 1. ファイルをアップロード
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# レスポンスからfile_idを取得
# {"id": 123, "filename": "document.pdf", ...}

# 2. ファイルについて質問
curl -X POST http://localhost:8000/api/agents/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "このドキュメントの要約を教えてください",
    "session_id": "doc-session",
    "file_ids": [123]
  }'
```

### パターン2: 継続的な会話

```bash
# 最初のメッセージ
curl -X POST http://localhost:8000/api/agents/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Pythonについて教えてください"
  }'

# session_idを保存して次の質問
curl -X POST http://localhost:8000/api/agents/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "それの具体的な例を教えてください",
    "session_id": "SESSION_ID_FROM_PREVIOUS_RESPONSE"
  }'
```

## 開発時の便利なTips

### 1. ホットリロードの有効化

コード変更時に自動的にサーバーを再起動：

```bash
uv run uvicorn app.main:app --reload
```

### 2. ログレベルの変更

詳細なログを表示：

```bash
# .envファイルで設定
DEBUG=true

# または環境変数で設定
DEBUG=true uv run ai-agent-app
```

### 3. JSONレスポンスの整形

curlのレスポンスを読みやすく表示：

```bash
curl http://localhost:8000/health | python -m json.tool

# またはjqを使用（インストールが必要）
curl http://localhost:8000/health | jq
```

### 4. リクエストの詳細表示

curlで詳細情報を表示：

```bash
curl -v http://localhost:8000/health
```

## 次のステップ

基本的な使い方を理解したら、以下のドキュメントで詳細を学習してください：

- [データベースセットアップ](./03-database-setup.md) - マイグレーションの管理
- [プロジェクト構造](../02-architecture/01-project-structure.md) - コードの構成を理解
- [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md) - アーキテクチャの理解

## トラブルシューティング

### 401 Unauthorized エラー

認証トークンが必要なエンドポイントにアクセスしている場合：

1. まずユーザー登録/ログインしてトークンを取得
2. リクエストヘッダーに`Authorization: Bearer YOUR_TOKEN`を追加

### 422 Validation Error

リクエストボディのバリデーションエラー：

1. Swagger UIでスキーマを確認
2. 必須フィールドがすべて含まれているか確認
3. データ型が正しいか確認

### 500 Internal Server Error

サーバー側のエラー：

1. サーバーのログを確認（コンソール出力）
2. 環境変数が正しく設定されているか確認
3. データベース接続を確認
