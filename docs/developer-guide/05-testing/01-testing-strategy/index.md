# テスト戦略

## 概要

このドキュメントでは、バックエンドAPIの包括的なテスト戦略について説明します。効果的なテスト戦略により、コードの品質を維持し、バグを早期に発見し、リファクタリングを安全に行うことができます。

## テストピラミッド

テストピラミッドは、異なるレベルのテストをバランス良く実装するための指針です。

```text
        ┌───────────────┐
       ╱    E2Eテスト    ╲  ← 少数（遅い・高コスト）
      ╱─────────────────╲
     ╱  統合テスト         ╲  ← 中程度
    ╱─────────────────────╲
   ╱   ユニットテスト        ╲  ← 多数（速い・低コスト）
  └─────────────────────────┘
```

### 各レベルの役割

#### 1. ユニットテスト（Unit Tests）

- **目的**: 個別の関数やメソッドの動作を検証
- **範囲**: 単一のクラス・関数
- **速度**: 非常に高速（ミリ秒）
- **割合**: 全体の70%
- **実装箇所**:
  - ユーティリティ関数
  - ビジネスロジック
  - バリデーション
  - データ変換

```python
# 例: ユーティリティ関数のテスト
def test_generate_file_id():
    """ファイルIDの生成をテスト"""
    file_id = generate_file_id()
    assert len(file_id) == 36  # UUID形式
    assert file_id.count("-") == 4
```

#### 2. 統合テスト（Integration Tests）

- **目的**: 複数のコンポーネントの連携を検証
- **範囲**: API + データベース、外部サービス
- **速度**: 中程度（数秒）
- **割合**: 全体の20%
- **実装箇所**:
  - APIエンドポイント
  - データベース操作
  - サービス層
  - ミドルウェア

```python
# 例: APIエンドポイントの統合テスト
async def test_create_file_endpoint(client, db_session):
    """ファイル作成エンドポイントをテスト"""
    response = await client.post(
        "/api/sample-files",
        files={"file": ("test.txt", b"content", "text/plain")}
    )
    assert response.status_code == 201
    # データベースにファイルが保存されているか確認
    file = await get_file_from_db(db_session, response.json()["id"])
    assert file is not None
```

#### 3. E2Eテスト（End-to-End Tests）

- **目的**: ユーザーシナリオ全体を検証
- **範囲**: フロントエンド + バックエンド + データベース
- **速度**: 遅い（数十秒〜数分）
- **割合**: 全体の10%
- **実装箇所**:
  - 重要なユーザーフロー
  - クリティカルパス

```python
# 例: ファイルアップロード〜ダウンロードの完全フロー
async def test_file_upload_download_flow(client, auth_token):
    """ファイルのアップロードからダウンロードまでのフロー"""
    # 1. ファイルアップロード
    upload_response = await client.post(
        "/api/sample-files",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.txt", b"test content", "text/plain")}
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]

    # 2. ファイル情報取得
    info_response = await client.get(f"/api/sample-files/{file_id}")
    assert info_response.status_code == 200

    # 3. ファイルダウンロード
    download_response = await client.get(f"/api/sample-files/{file_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == b"test content"
```

## カバレッジ目標

### 全体カバレッジ目標

| カテゴリ | 目標カバレッジ | 説明 |
|---------|--------------|------|
| **全体** | 80%以上 | プロジェクト全体のコードカバレッジ |
| **コアロジック** | 90%以上 | ビジネスロジック、重要な処理 |
| **APIエンドポイント** | 100% | 全てのエンドポイントをテスト |
| **ユーティリティ** | 95%以上 | 共通関数、ヘルパー関数 |
| **モデル** | 80%以上 | データモデル、バリデーション |

### カバレッジの測定

```powershell
# カバレッジレポートの生成
pytest --cov=app --cov-report=html --cov-report=term

# 特定のディレクトリのみ
pytest tests\unit\ --cov=app\core --cov-report=term

# カバレッジ不足の詳細表示
pytest --cov=app --cov-report=term-missing
```

### カバレッジレポートの確認

```powershell
# HTMLレポートを開く
start htmlcov\index.html
```

## テストレベルの詳細

### レベル1: ユニットテスト

**対象**:

- `app/core/`: セキュリティ、ロギング、例外処理
- `app/services/`: ビジネスロジック（モック使用）
- `app/schemas/`: Pydanticモデルのバリデーション
- `app/utils/`: ユーティリティ関数

**特徴**:

- 外部依存なし（モックを使用）
- データベース不要
- 非常に高速
- 並列実行可能

**ディレクトリ構造**:

```text
tests/
├── __init__.py
├── conftest.py                  # 共通フィクスチャとテスト設定
└── app/                         # src/app/ のミラー構造
    ├── api/                     # APIレイヤーのテスト
│       ├── core/                    # 🆕 APIコア機能のテスト
│       │   ├── test_dependencies.py    # 依存性注入のテスト
│       │   └── test_exception_handlers.py # 例外ハンドラーのテスト
│       ├── decorators/              # 🆕 デコレータのテスト
│       │   ├── test_basic.py           # 基本デコレータのテスト (10テスト)
│       │   ├── test_security.py        # セキュリティデコレータのテスト (15テスト)
│       │   ├── test_data_access.py     # データアクセスデコレータのテスト (6テスト)
│       │   └── test_reliability.py     # 信頼性デコレータのテスト (4テスト)
│       ├── middlewares/             # ミドルウェアのテスト
│       │   ├── test_error_handler.py       # エラーハンドリングミドルウェア (7テスト)
│       │   ├── test_logging.py             # ロギングミドルウェア (6テスト)
│       │   ├── test_metrics.py             # Prometheusメトリクスミドルウェア (7テスト)
│       │   ├── test_rate_limit.py          # レート制限とCORS (2テスト)
│       │   └── test_security_headers.py    # セキュリティヘッダーミドルウェア (4テスト)
│       └── routes/                  # エンドポイントのテスト
│           ├── system/              # システムエンドポイント
│           │   ├── test_health.py      # ヘルスチェックエンドポイント (3テスト)
│           │   ├── test_metrics.py     # Prometheusメトリクスエンドポイント (5テスト)
│           │   └── test_root.py        # ルートエンドポイント (7テスト)
│           └── v1/                  # APIバージョン1
│               ├── test_sample_agents.py   # エージェントチャットAPI (3テスト)
│               ├── test_sample_files.py    # ファイルアップロードAPI (2テスト)
│               ├── test_sample_sessions.py # セッション管理API (3テスト)
│               └── test_sample_users.py    # ユーザー管理・認証API (4テスト)
    ├── core/                        # コア機能のテスト
│   │   └── security/                # セキュリティ関連のテスト
│   │       ├── test_password.py     # パスワードハッシング・検証
│   │       ├── test_jwt.py          # JWT認証
│   │       └── test_api_key.py      # APIキー生成
    ├── models/                      # モデル層のテスト
    │   └── test_sample_user.py
    ├── repositories/                # リポジトリ層のテスト
    │   └── test_sample_user.py
    └── services/                    # サービス層のテスト
        └── test_sample_user.py
```

**設計原則**: テストディレクトリは `src/app/` のディレクトリ構造を完全にミラーリングします（`tests/app/`）。これにより、テスト対象のファイルを見つけやすく、保守性が向上します。

**APIレイヤーのテスト構造**:

`tests/app/api/`配下は、`src/app/api/`の構造を完全に反映しています：

- **`core/`**: 依存性注入と例外ハンドラーのテスト
  - データベースセッション、サービス層、認証の依存性注入が正しく動作することを検証
  - カスタム例外が適切なHTTPレスポンスに変換されることを検証

- **`decorators/`**: デコレータのテスト（35テスト、4ファイルに分割）
  - `test_basic.py` (10テスト): `@log_execution`, `@measure_performance`, `@async_timeout`
  - `test_security.py` (15テスト): `@validate_permissions`, `@handle_service_errors`
  - `test_data_access.py` (6テスト): `@transactional`, `@cache_result`
  - `test_reliability.py` (4テスト): `@retry_on_error`

- **`middlewares/`**: ミドルウェアのテスト（25テスト、5ファイル）
  - `test_error_handler.py` (7テスト): 例外の捕捉とエラーレスポンス変換
  - `test_logging.py` (6テスト): リクエスト/レスポンスログとX-Process-Timeヘッダー
  - `test_metrics.py` (7テスト): Prometheusメトリクス収集と/metricsエンドポイント
  - `test_rate_limit.py` (2テスト): レート制限とCORSヘッダー
  - `test_security_headers.py` (4テスト): セキュリティヘッダー (XSS, HSTS, CSP等)

- **`routes/`**: エンドポイントのテスト
  - `system/` (15テスト、3ファイル): システムエンドポイント
    - `test_health.py` (3テスト): ヘルスチェック、データベース接続確認
    - `test_metrics.py` (5テスト): Prometheusメトリクスの公開形式とContent-Type
    - `test_root.py` (7テスト): ウェルカムメッセージ、バージョン情報、ドキュメントリンク
  - `v1/` (12テスト、4ファイル): ビジネスAPIエンドポイント
    - `test_sample_agents.py` (3テスト): チャットエンドポイント、セッション管理
    - `test_sample_files.py` (2テスト): ファイルアップロード、バリデーション
    - `test_sample_sessions.py` (3テスト): セッション一覧、ページネーション
    - `test_sample_users.py` (4テスト): ユーザー登録、ログイン、重複チェック

### レベル2: 統合テスト

**対象**:

- `app/api/routes/`: APIエンドポイント
- `app/api/middlewares/`: ミドルウェア
- `app/models/`: データベースモデル
- `app/services/`: サービス層（実際のDB使用）

**特徴**:

- テストデータベース使用
- トランザクションロールバック
- FastAPIのTestClient使用
- 中程度の速度

**現在の実装**:

統合テストは `tests/api/routes/` および `tests/services/` に含まれています。

```python
# tests/api/routes/v1/test_sample_agents.py の例
async def test_chat_endpoint_guest(client):
    """ゲストユーザーでのチャット統合テスト"""
    response = await client.post(
        "/api/v1/agents/chat",
        json={"message": "こんにちは"}
    )
    assert response.status_code == 200
```

### レベル3: E2Eテスト

**対象**:

- 重要なユーザーシナリオ
- 複数のエンドポイントを跨ぐフロー
- 認証が必要な一連の操作

**特徴**:

- 実際のアプリケーションフロー
- 全てのコンポーネントが連携
- 実行時間が長い
- 最も重要な機能のみ

**ディレクトリ構造**:

```text
tests/
└── e2e/  # 将来実装予定
    ├── test_file_management_flow.py
    ├── test_agent_conversation_flow.py
    └── test_user_registration_flow.py
```

**注意**: E2Eテストは現在未実装です。重要なユーザーフローについては、将来的に追加を検討してください。

## テスト実行戦略

### 開発時

```powershell
# 変更したファイルに関連するテストのみ
pytest tests\services\test_sample_user.py

# 特定のテストケースのみ
pytest tests\services\test_sample_user.py::test_create_user_success

# 特定のディレクトリのテストのみ
pytest tests\api\routes\v1\

# 失敗したテストのみ再実行
pytest --lf  # last-failed

# 最後に失敗したテストを優先的に実行
pytest --ff  # failed-first
```

### コミット前

```powershell
# 全テストを実行
pytest tests\

# 高速テストのみ（将来的にマーカーを追加した場合）
pytest -m "not slow"
```

### CI/CD

```powershell
# 全テスト実行
pytest tests\

# カバレッジレポート付き
pytest --cov=app --cov-report=xml --cov-report=term

# 並列実行
pytest -n auto  # CPU数に応じて自動調整
```

## テストマーカーの活用

### マーカーの定義

```python
# pytest.ini
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "unit: unit tests",
    "integration: integration tests",
    "e2e: end-to-end tests",
    "db: tests that require database",
    "external: tests that call external APIs",
]
```

### マーカーの使用

```python
import pytest

@pytest.mark.unit
def test_calculate_discount():
    """ユニットテスト"""
    pass

@pytest.mark.integration
@pytest.mark.db
async def test_create_user(db_session):
    """統合テスト（DB使用）"""
    pass

@pytest.mark.slow
@pytest.mark.e2e
async def test_full_user_journey(client):
    """E2Eテスト（時間がかかる）"""
    pass

@pytest.mark.external
@pytest.mark.skip(reason="外部APIが利用不可")
async def test_external_api_call():
    """外部APIを呼び出すテスト"""
    pass
```

### マーカーでのテスト選択

```powershell
# ユニットテストのみ実行
pytest -m unit

# データベーステスト以外を実行
pytest -m "not db"

# 統合テストかつ遅くないテスト
pytest -m "integration and not slow"

# 外部APIテストをスキップ
pytest -m "not external"
```

## テスト環境の構成

### 環境変数の管理

```python
# tests/conftest.py
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """テスト環境変数をセットアップ"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["DEBUG"] = "true"
    yield
    # クリーンアップ
    if os.path.exists("test.db"):
        os.remove("test.db")
```

### テスト用設定ファイル

```python
# app/core/config.py に追加
class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    @property
    def is_testing(self) -> bool:
        """テスト環境かどうか"""
        return self.ENVIRONMENT == "testing"

    model_config = SettingsConfigDict(
        env_file=".env.test" if os.getenv("ENVIRONMENT") == "testing" else ".env",
        case_sensitive=True,
    )
```

## よくある間違いとその対処法

### 1. テストが相互に依存している

❌ **悪い例**:

```python
# test_user.py
def test_create_user():
    global user_id
    user = create_user("test@example.com")
    user_id = user.id

def test_update_user():
    # 前のテストに依存
    update_user(user_id, {"name": "Updated"})
```

✅ **良い例**:

```python
@pytest.fixture
def user(db_session):
    """各テストで新しいユーザーを作成"""
    user = create_user("test@example.com")
    db_session.add(user)
    db_session.commit()
    return user

def test_update_user(user, db_session):
    """独立したテスト"""
    update_user(user.id, {"name": "Updated"})
    db_session.refresh(user)
    assert user.name == "Updated"
```

### 2. テストデータの漏洩

❌ **悪い例**:

```python
def test_create_file(db_session):
    file = File(filename="test.txt")
    db_session.add(file)
    db_session.commit()
    # ロールバックせずに終了
```

✅ **良い例**:

```python
@pytest.fixture
async def db_session():
    """トランザクションを使用してロールバック"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

### 3. 外部サービスへの実際の呼び出し

❌ **悪い例**:

```python
def test_send_email():
    # 実際にメールを送信してしまう
    send_email("test@example.com", "Test")
```

✅ **良い例**:

```python
def test_send_email(mocker):
    """外部サービスをモック"""
    mock_send = mocker.patch("app.services.email.send_email")
    send_email("test@example.com", "Test")
    mock_send.assert_called_once()
```

## ベストプラクティス

### 1. テストの命名規則

```python
# パターン: test_<対象>_<条件>_<期待結果>
def test_create_user_with_valid_data_returns_user():
    """有効なデータでユーザー作成が成功する"""
    pass

def test_create_user_with_duplicate_email_raises_error():
    """重複したメールアドレスでエラーが発生する"""
    pass

def test_authenticate_with_invalid_password_returns_none():
    """無効なパスワードで認証が失敗する"""
    pass
```

### 2. テストの構造化（AAA Pattern）

```python
def test_file_upload():
    # Arrange（準備）
    file_content = b"test content"
    file_name = "test.txt"

    # Act（実行）
    result = upload_file(file_name, file_content)

    # Assert（検証）
    assert result.filename == file_name
    assert result.size == len(file_content)
```

### 3. テストデータの管理

```python
# tests/factories.py
class UserFactory:
    """ユーザーのテストデータを生成"""

    @staticmethod
    def create(**kwargs):
        defaults = {
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "username": f"user{random.randint(1000, 9999)}",
            "is_active": True,
        }
        defaults.update(kwargs)
        return User(**defaults)

# テストでの使用
def test_user_creation():
    user = UserFactory.create(email="specific@example.com")
    assert user.email == "specific@example.com"
```

### 4. テストの並列実行

```bash
# pytest-xdist を使用
pip install pytest-xdist

# 並列実行
pytest -n auto  # CPU数に応じて自動
pytest -n 4     # 4プロセスで実行
```

### 5. テスト失敗時のデバッグ

```python
# より詳細な出力
pytest -vv

# 標準出力を表示
pytest -s

# デバッガーを起動
pytest --pdb

# 最初の失敗で停止
pytest -x

# N個失敗で停止
pytest --maxfail=3
```

### 6. Parametrizeによるテスト効率化

`@pytest.mark.parametrize`を活用することで、テストコードの重複を削減し、保守性を向上させます。

```python
# ❌ Before: 個別のテスト関数（保守困難）
def test_validate_email_valid():
    assert validate_email("user@example.com") == True

def test_validate_email_invalid():
    assert validate_email("invalid") == False

def test_validate_email_no_domain():
    assert validate_email("user@") == False


# ✅ After: Parametrize化（保守容易）
@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("invalid", False),
    ("user@", False),
    ("@example.com", False),
], ids=["valid", "no_at", "no_domain", "no_local"])
def test_validate_email(email, expected):
    assert validate_email(email) == expected
```

**効果**:
- テスト関数数の削減（4関数 → 1関数）
- テストケースの一覧性向上
- 新しいケース追加が容易
- 失敗時にどのケースが失敗したか明確

詳細は[ベストプラクティス: Parametrizeパターン](./06-best-practices/index.md#parametrizeパターンテストの効率化)を参照してください。

## 継続的な改善

### テストの定期的なレビュー

- **月次**: テストカバレッジレポートのレビュー
- **四半期**: テスト戦略の見直し
- **新機能追加時**: テストケースの追加

### メトリクスの追跡

```powershell
# カバレッジの推移を記録
pytest --cov=app --cov-report=json
# coverage.json を保存してトレンドを確認
```

### テストの健全性チェック

```powershell
# Mutation testing（変異テスト）
pip install mutmut
mutmut run

# テストの実行時間分析
pytest --durations=10  # 最も遅い10個のテストを表示
```

## 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

## 次のステップ

- [ユニットテスト](./02-unit-testing.md) - pytest基礎とユニットテストの書き方
- [APIテスト](./03-api-testing.md) - FastAPIエンドポイントのテスト
- [データベーステスト](./04-database-testing.md) - SQLAlchemyとテストDB
- [モックとフィクスチャ](./05-mocks-fixtures.md) - テストデータとモックの管理
- [ベストプラクティス](./06-best-practices.md) - より良いテストを書くために
