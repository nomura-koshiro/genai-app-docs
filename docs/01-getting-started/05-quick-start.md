# クイックスタートガイド

最速でcamp-backendを起動し、動作を確認する方法を説明します。

## 前提条件

[WSL2 + Docker CEセットアップ](./02-wsl2-docker-setup.md)が完了していることを確認してください。

## 起動方法

### VS Codeで起動

1. VS Codeでプロジェクトを開く
2. **F5キー**を押す

これだけです！以下が自動実行されます：

- ✅ Docker起動
- ✅ PostgreSQL & Redis起動
- ✅ FastAPI起動

### 起動確認

ブラウザで以下にアクセス：

- **APIドキュメント**: <http://localhost:8000/docs>
- **ヘルスチェック**: <http://localhost:8000/health>

起動成功！

## Swagger UIでのテスト

### 1. エンドポイントの確認

<http://localhost:8000/docs> にアクセスすると、すべてのAPIエンドポイントが表示されます。

### 2. ヘルスチェックのテスト

1. `GET /health` エンドポイントをクリック
2. 「Try it out」ボタンをクリック
3. 「Execute」ボタンをクリック

レスポンス例：

```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T08:00:00.000000",
  "version": "0.1.0",
  "environment": "development"
}
```

### 3. その他のエンドポイントをテスト

同様に、他のエンドポイントも「Try it out」→「Execute」で簡単にテストできます。

## curlでのテスト

コマンドラインからもテストできます：

```bash
# ヘルスチェック
curl http://localhost:8000/health

# JSON整形して表示
curl http://localhost:8000/health | python -m json.tool
```

## Pythonコードでのテスト

```python
import requests

# ヘルスチェック
response = requests.get("http://localhost:8000/health")
print(response.json())
```

## 停止方法

VS Codeで **Shift+F5** を押すか、ターミナルで **Ctrl+C** を押してください。

## 次のステップ

- [データベース基礎](./07-database-basics.md) - データベース管理
- [環境設定](./04-environment-config.md) - ステージング・本番環境の設定
- [プロジェクト構造](../02-architecture/01-project-structure.md) - コードベースの理解

---

## 詳細情報

### 手動起動（WSL2内）

```bash
# Dockerサービス起動
sudo service docker start

# PostgreSQL起動
docker compose up -d postgres

# アプリケーション起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ログレベルの変更

`.env.local`ファイルで設定：

```bash
DEBUG=true
```

### ホットリロード

F5で起動すると、コード変更時に自動的にサーバーが再起動します。

---

## トラブルシューティング

### ポート8000が使用中

別のアプリケーションがポート8000を使用しています。

`.env.local`ファイルで変更：

```bash
PORT=8001
```

### データベース接続エラー

PostgreSQLが起動していない可能性があります。

```bash
# Dockerサービス起動
sudo service docker start

# PostgreSQL起動
docker compose up -d postgres

# 確認
docker compose ps
```

### Swagger UIが表示されない

アプリケーションが起動していることを確認：

```bash
curl http://localhost:8000/health
```

起動していない場合はF5を押してください。

### 環境が壊れた・依存関係を更新したい

環境を完全に作り直します：

```bash
# WSL2内で実行
bash /mnt/c/developments/genai-app-docs/scripts/setup-wsl2.sh --clean
```

このコマンドは：

- 既存のプロジェクトディレクトリを削除
- Dockerコンテナとボリュームを削除
- PATH設定をクリーンアップ
- クリーンな状態から再構築

所要時間: 約2-3分
