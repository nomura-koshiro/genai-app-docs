# トラブルシューティング

このガイドでは、よくある問題とその解決方法、デバッグ手法を説明します。

## 目次

- [概要](#概要)
- [一般的な問題](#一般的な問題)
- [データベース関連](#データベース関連)
- [API関連](#api関連)
- [ファイルアップロード関連](#ファイルアップロード関連)
- [デプロイメント関連](#デプロイメント関連)
- [パフォーマンス問題](#パフォーマンス問題)
- [デバッグ手法](#デバッグ手法)
- [参考リンク](#参考リンク)

## 概要

トラブルシューティングの基本アプローチ：

1. **エラーメッセージの確認** - ログやスタックトレースを読む
2. **再現手順の特定** - 問題を再現できるか確認
3. **環境の確認** - 開発/ステージング/本番環境の違い
4. **ログの確認** - アプリケーションログ、データベースログ
5. **段階的なデバッグ** - 問題を分離して特定

## 一般的な問題

### 問題 1: アプリケーションが起動しない

**症状:**
```
Error: Application startup failed
```

**原因と解決策:**

#### 原因 1: 環境変数の不足

```bash
# エラーメッセージ
KeyError: 'DATABASE_URL'
```

**解決策:**
```bash
# .envファイルを確認
cat .env

# 必要な環境変数を設定
cp .env.example .env
# .envファイルを編集して値を設定
```

#### 原因 2: ポートが既に使用されている

```bash
# エラーメッセージ
OSError: [Errno 48] Address already in use
```

**解決策:**
```bash
# 使用中のポートを確認（Linux/Mac）
lsof -i :8000

# プロセスを終了
kill -9 <PID>

# または別のポートを使用
uvicorn app.main:app --port 8001
```

#### 原因 3: 依存パッケージのインストール不足

```bash
# エラーメッセージ
ModuleNotFoundError: No module named 'fastapi'
```

**解決策:**
```bash
# Poetry使用時
poetry install

# pip使用時
pip install -r requirements.txt

# 仮想環境の確認
which python
poetry env info
```

### 問題 2: ImportError

**症状:**
```python
ImportError: cannot import name 'app' from 'app.main'
```

**原因と解決策:**

#### 原因: PYTHONPATHが正しく設定されていない

**解決策:**
```bash
# PYTHONPATHを設定
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# または、起動コマンドを修正
cd src
uvicorn app.main:app --reload

# pyproject.tomlでパスを確認
```

### 問題 3: 循環インポート

**症状:**
```python
ImportError: cannot import name 'User' from partially initialized module 'app.models.user'
```

**原因と解決策:**

**解決策:**
```python
# 悪い例
# models/user.py
from app.models.task import Task

class User(Base):
    tasks: Mapped[list[Task]] = relationship("Task")

# models/task.py
from app.models.user import User

class Task(Base):
    user: Mapped[User] = relationship("User")

# 良い例（TYPE_CHECKINGを使用）
# models/user.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.task import Task

class User(Base):
    tasks: Mapped[list["Task"]] = relationship("Task")
```

## データベース関連

### 問題 4: データベース接続エラー

**症状:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**原因と解決策:**

#### 原因 1: データベースサーバーが起動していない

**解決策:**
```bash
# PostgreSQL起動確認（Linux/Mac）
pg_isready -h localhost -p 5432

# PostgreSQL起動（Docker）
docker-compose up postgres

# PostgreSQL起動（システムサービス）
sudo systemctl start postgresql
```

#### 原因 2: 接続文字列が間違っている

**解決策:**
```bash
# 接続文字列の確認
echo $DATABASE_URL

# 正しい形式
# PostgreSQL
postgresql+asyncpg://user:password@localhost:5432/dbname

# SQLite
sqlite+aiosqlite:///./app.db

# .envファイルを確認して修正
```

#### 原因 3: データベースが存在しない

**解決策:**
```bash
# PostgreSQLでデータベース作成
createdb appdb

# または psql で
psql -U postgres
CREATE DATABASE appdb;
\q

# Docker Compose使用時
docker-compose exec postgres createdb -U postgres appdb
```

### 問題 5: マイグレーションエラー

**症状:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**原因と解決策:**

#### 解決策 1: マイグレーション履歴の確認

```bash
# 現在のマイグレーションバージョン確認
alembic current

# マイグレーション履歴確認
alembic history

# 最新に更新
alembic upgrade head

# 1つ前に戻す
alembic downgrade -1
```

#### 解決策 2: マイグレーションのリセット

```bash
# 注意: 開発環境のみ実行

# データベースを削除
dropdb appdb
createdb appdb

# マイグレーション再実行
alembic upgrade head
```

### 問題 6: N+1問題

**症状:**
- APIレスポンスが遅い
- 大量のSQLクエリが実行される

**診断:**
```python
# SQLログを有効化
import logging

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**解決策:**
```python
# 悪い例（N+1問題）
users = await session.execute(select(User))
for user in users.scalars():
    print(user.tasks)  # 各ユーザーごとにクエリ実行

# 良い例（joinedloadを使用）
from sqlalchemy.orm import joinedload

users = await session.execute(
    select(User).options(joinedload(User.tasks))
)
for user in users.scalars():
    print(user.tasks)  # 1回のクエリで取得

# または、リレーションシップでlazy="selectin"を設定
class User(Base):
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        lazy="selectin",  # 自動的に効率的に読み込む
    )
```

## API関連

### 問題 7: 422 Validation Error

**症状:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**原因と解決策:**

#### 解決策: リクエストボディの確認

```python
# スキーマの確認
class UserCreate(BaseModel):
    email: EmailStr  # 必須フィールド
    username: str
    password: str

# リクエスト例（正しい）
{
  "email": "user@example.com",
  "username": "testuser",
  "password": "password123"
}

# リクエスト例（エラー）
{
  "username": "testuser",  # emailが不足
  "password": "password123"
}

# デバッグ方法
# 1. OpenAPI docs（/docs）でスキーマを確認
# 2. リクエストボディをログ出力
@router.post("/users")
async def create_user(user_data: UserCreate):
    logger.info(f"Received: {user_data}")
    # ...
```

### 問題 8: 401 Unauthorized

**症状:**
```json
{
  "detail": "Not authenticated"
}
```

**原因と解決策:**

#### 解決策 1: トークンの確認

```bash
# リクエストヘッダーにトークンを含める
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/protected

# トークンの検証
python -c "
from app.core.security import decode_token
token = 'your-token-here'
payload = decode_token(token)
print(payload)
"
```

#### 解決策 2: トークンの有効期限

```python
# トークンが期限切れの場合、新しいトークンを取得
# ログイン
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# 新しいトークンを取得
```

### 問題 9: 500 Internal Server Error

**症状:**
```json
{
  "detail": "Internal server error"
}
```

**診断方法:**

```bash
# ログを確認
tail -f logs/app.log

# または標準出力
uvicorn app.main:app --reload --log-level debug

# エラー詳細を表示（開発環境のみ）
# config.py
DEBUG = True
```

**一般的な原因:**

```python
# 原因 1: 例外が処理されていない
async def get_user(user_id: int):
    user = await db.get(User, user_id)
    return user.name  # userがNoneの場合にエラー

# 解決策
async def get_user(user_id: int):
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user.name

# 原因 2: データベースセッションの不適切な使用
# （詳細はデータベース関連セクションを参照）
```

## ファイルアップロード関連

### 問題 10: ファイルアップロード失敗

**症状:**
```
413 Request Entity Too Large
```

**原因と解決策:**

#### 解決策 1: ファイルサイズ制限の調整

```python
# config.py
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Nginx設定も確認
client_max_body_size 50M;
```

#### 解決策 2: タイムアウト設定

```python
# Uvicorn起動時
uvicorn app.main:app --timeout-keep-alive 300

# Nginx設定
proxy_read_timeout 300s;
```

### 問題 11: ファイルが見つからない

**症状:**
```
FileNotFoundError: File not found: abc123.jpg
```

**診断方法:**

```python
# ストレージの確認
async def debug_storage():
    storage = get_storage_backend()

    # ファイルの存在確認
    exists = await storage.exists("abc123.jpg")
    print(f"File exists: {exists}")

    # 全ファイルのリスト
    files = await storage.list_files()
    print(f"Files: {files}")

# ローカルストレージの場合
import os
print(os.listdir("./uploads"))
```

## デプロイメント関連

### 問題 12: Dockerコンテナが起動しない

**症状:**
```
Error: Container exited with code 1
```

**診断方法:**

```bash
# ログを確認
docker logs <container-id>

# コンテナに入る
docker exec -it <container-id> /bin/bash

# ビルドログを確認
docker build -t app:latest . --progress=plain

# docker-composeログ
docker-compose logs -f app
```

**一般的な原因:**

```dockerfile
# 原因 1: 不足している依存関係
RUN apt-get update && apt-get install -y \
    required-package

# 原因 2: 不正なCMD/ENTRYPOINT
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]

# 原因 3: 環境変数の不足
ENV PYTHONPATH=/app/src
```

### 問題 13: Azure App Serviceでアプリが起動しない

**症状:**
- アプリケーションエラー
- コンテナが起動と停止を繰り返す

**診断方法:**

```bash
# ログストリームを確認
az webapp log tail \
  --name ai-agent-app \
  --resource-group ai-agent-rg

# コンテナログをダウンロード
az webapp log download \
  --name ai-agent-app \
  --resource-group ai-agent-rg

# SSH接続
az webapp ssh \
  --name ai-agent-app \
  --resource-group ai-agent-rg
```

**一般的な原因:**

```bash
# 原因 1: 環境変数の不足
az webapp config appsettings list \
  --name ai-agent-app \
  --resource-group ai-agent-rg

# 原因 2: ヘルスチェックの失敗
# /healthエンドポイントが正しく応答しているか確認

# 原因 3: ポート設定
# App Serviceは8000ポートを期待
EXPOSE 8000
```

## パフォーマンス問題

### 問題 14: APIレスポンスが遅い

**診断方法:**

```python
# 1. ログにタイムスタンプを追加
import time

@router.get("/slow-endpoint")
async def slow_endpoint():
    start = time.time()

    # 処理1
    result1 = await some_operation()
    logger.info(f"Operation 1: {time.time() - start}s")

    # 処理2
    result2 = await another_operation()
    logger.info(f"Operation 2: {time.time() - start}s")

    return result

# 2. プロファイリング
import cProfile

cProfile.run('your_function()')

# 3. SQLクエリのログ
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**一般的な原因と解決策:**

```python
# 原因 1: N+1問題
# → joinedload/selectinloadを使用

# 原因 2: 同期ブロッキング処理
# 悪い例
def slow_function():
    time.sleep(5)  # ブロック
    return result

# 良い例
async def fast_function():
    await asyncio.sleep(5)  # 非ブロック
    return result

# 原因 3: 不要なデータの取得
# 悪い例
users = await session.execute(select(User))  # 全カラム

# 良い例
users = await session.execute(
    select(User.id, User.name)  # 必要なカラムのみ
)
```

### 問題 15: メモリ使用量が多い

**診断方法:**

```python
# メモリ使用量の監視
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / 1024 / 1024  # MB

logger.info(f"Memory usage: {get_memory_usage():.2f} MB")
```

**一般的な原因:**

```python
# 原因 1: 大きなファイルをメモリに読み込む
# 悪い例
contents = await file.read()  # 全体をメモリに

# 良い例（チャンク処理）
async def process_file_chunks(file):
    while chunk := await file.read(1024 * 1024):  # 1MB
        process_chunk(chunk)

# 原因 2: データベースセッションのリーク
# 必ずセッションをクローズする
async with AsyncSession(engine) as session:
    # 処理
    pass  # 自動クローズ
```

## デバッグ手法

### 1. ログの活用

```python
# ログレベルの設定
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 開発環境
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 詳細なログ
logger.debug(f"Processing request: {request}")
logger.info(f"User {user_id} created")
logger.warning(f"Rate limit approaching for {ip}")
logger.error(f"Failed to process: {error}")
logger.exception("Unexpected error")  # スタックトレース付き
```

### 2. インタラクティブデバッガー

```python
# pdbを使用
import pdb

@router.get("/debug")
async def debug_endpoint():
    data = {"key": "value"}
    pdb.set_trace()  # ここでブレークポイント
    return data

# VS Codeデバッガー設定
# .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "jinja": true
    }
  ]
}
```

### 3. テストでの問題の再現

```python
# 問題を再現するテストを作成
import pytest

@pytest.mark.asyncio
async def test_reproduce_issue():
    """Issue #123: User creation fails with email"""
    # 再現手順
    user_data = {"email": "test@example.com", "username": "test"}

    # 期待される動作
    response = await client.post("/api/users", json=user_data)
    assert response.status_code == 201
```

### 4. プロファイリング

```python
# line_profilerを使用
from line_profiler import LineProfiler

profiler = LineProfiler()

@profiler
async def slow_function():
    # 処理
    pass

profiler.print_stats()
```

### 5. リクエスト/レスポンスのロギング

```python
# ミドルウェアでログ記録
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    # リクエストログ
    logger.info(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    # レスポンスログ
    duration = time.time() - start
    logger.info(
        f"Response: {response.status_code} "
        f"Duration: {duration:.2f}s"
    )

    return response
```

## 参考リンク

### 公式ドキュメント

- [FastAPI Debugging](https://fastapi.tiangolo.com/tutorial/debugging/)
- [SQLAlchemy Error Messages](https://docs.sqlalchemy.org/en/20/errors.html)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Docker Debugging](https://docs.docker.com/config/containers/logging/)

### プロジェクト内リンク

- [ログ設定](../03-core-concepts/03-logging.md)
- [エラーハンドリング](../03-core-concepts/04-error-handling.md)
- [テスト](../05-testing/01-unit-testing.md)
- [デプロイメント](./06-deployment.md)

### ツール

- [httpie](https://httpie.io/) - コマンドラインHTTPクライアント
- [Postman](https://www.postman.com/) - APIテストツール
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL管理ツール
- [Azure Monitor](https://azure.microsoft.com/services/monitor/) - 監視ツール

## サポート

問題が解決しない場合：

1. **ログを確認** - 詳細なエラーメッセージとスタックトレース
2. **環境情報を収集** - OS、Pythonバージョン、依存パッケージバージョン
3. **再現手順を作成** - 最小限のコードで問題を再現
4. **Issue作成** - GitHubで問題を報告
5. **ドキュメント確認** - 関連ドキュメントを再確認
