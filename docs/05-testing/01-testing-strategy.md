# テスト戦略

## 概要

このドキュメントでは、バックエンドAPIの包括的なテスト戦略について説明します。効果的なテスト戦略により、コードの品質を維持し、バグを早期に発見し、リファクタリングを安全に行うことができます。

## テストピラミッド

テストピラミッドは、異なるレベルのテストをバランス良く実装するための指針です。

```
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
        "/api/files",
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
        "/api/files",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.txt", b"test content", "text/plain")}
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]

    # 2. ファイル情報取得
    info_response = await client.get(f"/api/files/{file_id}")
    assert info_response.status_code == 200

    # 3. ファイルダウンロード
    download_response = await client.get(f"/api/files/{file_id}/download")
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

```bash
# カバレッジレポートの生成
pytest --cov=app --cov-report=html --cov-report=term

# 特定のディレクトリのみ
pytest tests/unit/ --cov=app/core --cov-report=term

# カバレッジ不足の詳細表示
pytest --cov=app --cov-report=term-missing
```

### カバレッジレポートの確認

```bash
# HTMLレポートを開く
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
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
```
tests/
├── __init__.py
├── conftest.py          # 共通フィクスチャとテスト設定
├── test_models.py       # モデル層のテスト
├── test_repositories.py # リポジトリ層のテスト
├── test_services.py     # サービス層のテスト（統合テスト）
└── test_api.py          # APIエンドポイントのテスト
```

**注意**: 現在の実装ではフラット構造を採用しています。将来的にテスト数が増加した場合は、`unit/`, `integration/`, `e2e/` などのサブディレクトリに分割することを検討してください。

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

統合テストは `test_api.py` と `test_services.py` に含まれています。

```python
# test_api.py の例
async def test_chat_endpoint_guest(client):
    """ゲストユーザーでのチャット統合テスト"""
    response = await client.post(
        "/api/agents/chat",
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
```
tests/
└── e2e/  # 将来実装予定
    ├── test_file_management_flow.py
    ├── test_agent_conversation_flow.py
    └── test_user_registration_flow.py
```

**注意**: E2Eテストは現在未実装です。重要なユーザーフローについては、将来的に追加を検討してください。

## テスト実行戦略

### 開発時

```bash
# 変更したファイルに関連するテストのみ
pytest tests/test_services.py

# 特定のテストケースのみ
pytest tests/test_services.py::test_create_user_success

# 失敗したテストのみ再実行
pytest --lf  # last-failed

# 最後に失敗したテストを優先的に実行
pytest --ff  # failed-first
```

### コミット前

```bash
# 全テストを実行
pytest tests/

# 高速テストのみ（将来的にマーカーを追加した場合）
pytest -m "not slow"
```

### CI/CD

```bash
# 全テスト実行
pytest tests/

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

```bash
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
# app/config.py に追加
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

## 継続的な改善

### テストの定期的なレビュー

- **月次**: テストカバレッジレポートのレビュー
- **四半期**: テスト戦略の見直し
- **新機能追加時**: テストケースの追加

### メトリクスの追跡

```bash
# カバレッジの推移を記録
pytest --cov=app --cov-report=json
# coverage.json を保存してトレンドを確認
```

### テストの健全性チェック

```bash
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
