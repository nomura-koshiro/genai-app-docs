# テスト方針・ベストプラクティス

## テストピラミッド

```
        /\
       /E2E\        ← 少数の重要フロー
      /------\
     /Integration\  ← API・サービス連携
    /--------------\
   /   Unit Tests   \ ← 多数のユニットテスト
  /------------------\
```

## テスト種別

| 種別 | ツール | 対象 | カバレッジ目標 |
|------|--------|------|---------------|
| ユニット | pytest | 関数、サービス、リポジトリ | 70% |
| 統合 | pytest + TestClient | APIエンドポイント | 25% |
| E2E | pytest | ユーザーフロー | 5% |

## テスト構成

```
tests/
├── api/v1/
│   └── test_users.py        # APIエンドポイントテスト
├── crud/
│   └── test_crud_users.py   # CRUD操作テスト
├── models/
│   └── test_users.py        # モデル・バリデーションテスト
├── services/
│   └── test_user_service.py # サービス層テスト
├── utils/
│   ├── utils.py             # テストユーティリティ
│   └── fixtures.py          # テストフィクスチャ
└── conftest.py              # pytest設定
```

## APIテスト例

```python
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

class TestUserEndpoints:
    """ユーザーAPIエンドポイントテスト"""

    def test_create_user_success(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str]
    ) -> None:
        """正常系：ユーザー作成成功"""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )

        assert response.status_code == 201
        content = response.json()
        assert content["email"] == data["email"]
        assert "id" in content

    def test_get_user_not_found(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str]
    ) -> None:
        """異常系：存在しないユーザーの取得"""
        response = client.get(
            f"{settings.API_V1_STR}/users/999999",
            headers=superuser_token_headers,
        )

        assert response.status_code == 404
```

## サービステスト例

```python
import pytest
from unittest.mock import Mock, patch

from app.services.user_service import UserService
from app.schemas.user import UserCreate

class TestUserService:
    """ユーザーサービステスト"""

    def test_create_user(self, db_session):
        """ユーザー作成テスト"""
        service = UserService(db_session)
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="password123"
        )

        user = service.create(user_data)

        assert user.email == user_data.email
        assert user.name == user_data.name
```

## フィクスチャ例

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.api.deps import get_db

SQLALCHEMY_DATABASE_URL = "postgresql://localhost/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
```

## テスト実行コマンド

```bash
# 全テスト実行
cd apps/backend && python -m pytest

# 詳細出力
cd apps/backend && python -m pytest -v -s

# 特定ファイル
cd apps/backend && python -m pytest tests/api/v1/test_users.py

# カバレッジ測定
cd apps/backend && python -m pytest --cov=app --cov-report=html

# 並列実行
cd apps/backend && python -m pytest -n auto

# 失敗時に停止
cd apps/backend && python -m pytest -x
```

## ベストプラクティス

1. **AAA パターン**: Arrange → Act → Assert
2. **テストの独立性**: 各テストは独立して実行可能
3. **テストデータの分離**: テスト用DBを使用
4. **モック最小限**: 必要な場合のみモック
5. **明確なテスト名**: テスト対象と期待結果を明示

## ドキュメント参照

詳細は以下のドキュメントを参照：

- [テスト戦略](docs/developer-guide/05-testing/01-testing-strategy/index.md)
- [ユニットテスト](docs/developer-guide/05-testing/02-unit-testing/index.md)
- [APIテスト](docs/developer-guide/05-testing/03-api-testing/index.md)
- [データベーステスト](docs/developer-guide/05-testing/04-database-testing/index.md)
- [モック・フィクスチャ](docs/developer-guide/05-testing/05-mocks-fixtures/index.md)
- [ベストプラクティス](docs/developer-guide/05-testing/06-best-practices/index.md)
