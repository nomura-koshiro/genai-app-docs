# テックスタック - AI・開発ツール

このドキュメントでは、camp-backendのAI機能と開発ツールで使用している技術について説明します。

## 目次

- [LangChain / LangGraph](#langchain--langgraph)
- [uv](#uv---パッケージマネージャー)
- [Ruff](#ruff---リンターとフォーマッター)
- [pytest](#pytest---テストフレームワーク)
- [Prometheus](#prometheus---メトリクス収集)

---

## LangChain / LangGraph

**バージョン**:

- LangChain: 0.3.0+
- LangGraph: 0.2.0+

LangChainは、LLMアプリケーションを構築するためのフレームワークです。
LangGraphは、ステートフルなマルチアクターアプリケーションを構築するためのライブラリです。

### 主な特徴

- **チェーン構築**: 複数のLLM呼び出しを連鎖
- **エージェント**: ツールを使用する自律的なAI
- **メモリ**: 会話履歴の管理
- **ツール**: 外部システムとの統合

### LangGraphの使用

```python
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from typing import TypedDict

class AgentState(TypedDict):
    """エージェントの状態。"""
    messages: list[dict]
    next_action: str

# LLMの初期化
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

def process_message(state: AgentState) -> AgentState:
    """メッセージを処理する。"""
    messages = state["messages"]
    response = llm.invoke(messages)
    messages.append({"role": "assistant", "content": response.content})
    return {"messages": messages, "next_action": "end"}

# グラフの構築
workflow = StateGraph(AgentState)
workflow.add_node("process", process_message)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

# コンパイル
app = workflow.compile()

# 実行
result = app.invoke({
    "messages": [{"role": "user", "content": "Hello!"}],
    "next_action": ""
})
```

### セキュリティとベストプラクティス

- **入力検証**: すべてのユーザー入力をサニタイズ
- **レート制限**: LLM API呼び出しの制限
- **エラーハンドリング**: ツール実行失敗時の適切な処理
- **ログ記録**: すべてのツール呼び出しとLLM応答をログ
- **タイムアウト**: 長時間実行の防止

### 公式ドキュメント

- LangChain: <https://python.langchain.com/>
- LangGraph: <https://langchain-ai.github.io/langgraph/>

---

## uv - パッケージマネージャー

**公式サイト**: <https://github.com/astral-sh/uv>

uvは、Rustで実装された超高速Pythonパッケージマネージャーです。

### 主な特徴

- **高速**: pipの10-100倍速い
- **信頼性**: ロックファイルによる再現可能なインストール
- **互換性**: pip、pip-tools、poetryと互換
- **簡単**: 設定なしで使用可能

### 基本コマンド

```powershell
# 依存関係のインストール
uv sync

# パッケージの追加
uv add fastapi

# 開発依存関係の追加
uv add --dev pytest

# パッケージの削除
uv remove fastapi

# コマンドの実行
uv run python script.py
uv run pytest

# 仮想環境の作成
uv venv

# ロックファイルの更新
uv lock
```

---

## Ruff - リンターとフォーマッター

**公式サイト**: <https://github.com/astral-sh/ruff>

Ruffは、Rustで実装された超高速Pythonリンターとフォーマッターです。

### 主な特徴

- **高速**: Flake8やBlackの10-100倍速い
- **統合**: リントとフォーマットを1つのツールで
- **互換性**: Flake8、Black、isortと互換
- **設定簡単**: pyproject.tomlで設定

### 設定

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 使用方法

```powershell
# コードのフォーマット
uv run ruff format .

# リント
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# 特定のファイルのみ
uv run ruff check src\app\main.py
```

---

## pytest - テストフレームワーク

**バージョン**: 8.3.0+

pytestは、Pythonの標準的なテストフレームワークです。

### 主な特徴

- **シンプル**: アサーションが簡単
- **フィクスチャ**: テストデータの管理
- **プラグイン**: 豊富なプラグインエコシステム
- **非同期**: pytest-asyncioで非同期テスト

### テストの作成

```python
# tests/test_user_service.py
import pytest
from app.services.sample_user import SampleUserService
from app.schemas.sample_user import SampleUserCreate

@pytest.mark.asyncio
async def test_create_user(db_session):
    """ユーザー作成のテスト。"""
    service = SampleUserService(db_session)

    user_data = SampleUserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    user = await service.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.id is not None

@pytest.mark.asyncio
async def test_duplicate_email(db_session):
    """重複メールアドレスのテスト。"""
    service = SampleUserService(db_session)

    user_data = SampleUserCreate(
        email="test@example.com",
        username="testuser1",
        password="password123"
    )

    await service.create_user(user_data)

    # 同じメールアドレスで2回目の作成
    with pytest.raises(ValidationError):
        await service.create_user(user_data)
```

### フィクスチャ

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.database import Base

@pytest.fixture(scope="function")
async def db_engine():
    """テスト用PostgreSQLエンジン。"""
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # テーブルを作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # テーブルを削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """テスト用データベースセッション。"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()
```

### 実行

```powershell
# すべてのテストを実行
uv run pytest

# 特定のファイルを実行
uv run pytest tests\test_services.py

# 詳細出力
uv run pytest -v

# カバレッジ（HTML形式）
uv run pytest --cov=app --cov-report=html

# カバレッジ（ターミナル出力）
uv run pytest --cov=app --cov-report=term
```

### 追加プラグイン

このプロジェクトでは以下のpytestプラグインを使用しています：

- **pytest-asyncio**: 非同期テストのサポート
- **pytest-cov**: テストカバレッジの測定
- **httpx**: APIテスト用の非同期HTTPクライアント

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_endpoint(client: AsyncClient):
    """チャットエンドポイントのテスト."""
    response = await client.post(
        "/api/sample-agents/chat",
        json={"message": "こんにちは"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
```

### 公式ドキュメント

- <https://docs.pytest.org/>
- <https://pytest-asyncio.readthedocs.io/>
- <https://www.python-httpx.org/>

---

## Prometheus - メトリクス収集

**バージョン**: 0.23.1+ (prometheus-client)

Prometheusは、オープンソースのモニタリングシステムです。

### 主な特徴

- **時系列データ**: メトリクスの時系列管理
- **柔軟なクエリ**: PromQL
- **アラート**: Alertmanagerと連携
- **可視化**: Grafanaと連携

### メトリクスの定義

```python
from prometheus_client import Counter, Histogram

# HTTPリクエスト総数
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# リクエスト処理時間
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# チャットメッセージ総数
chat_messages_total = Counter(
    "chat_messages_total",
    "Total chat messages processed",
    ["role"],
)
```

### ミドルウェアでの使用

```python
from app.api.middlewares.metrics import PrometheusMetricsMiddleware

app.add_middleware(PrometheusMetricsMiddleware)

# メトリクスエンドポイント
@app.get("/metrics")
async def metrics():
    """Prometheusメトリクスエンドポイント."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 公式ドキュメント

- <https://prometheus.io/>
- <https://prometheus.github.io/client_python/>

---

## 関連ドキュメント

- [テックスタック概要](./01-tech-stack.md) - 技術スタック全体像
- [Webフレームワーク](./01-tech-stack-web.md) - FastAPI、Pydantic、Alembic
- [データレイヤー](./01-tech-stack-data.md) - PostgreSQL、SQLAlchemy、Redis

---
