# 基本的なテスト

このセクションでは、実装したコードをテストする基本的な方法を学びます。

---

## なぜテストが必要か

テストを書くことで以下のメリットがあります:

- **バグの早期発見**: コードが正しく動作することを確認
- **リファクタリングの安全性**: 変更後も動作が保証される
- **仕様の明確化**: テストがドキュメントの役割を果たす
- **開発速度の向上**: 手動テストの時間を削減

---

## テストの基本概念

### テストピラミッド

```text
       ┌─────────────┐
       │   E2E       │  ← 少ない（遅い・高コスト）
       ├─────────────┤
       │ Integration │  ← 中程度
       ├─────────────┤
       │   Unit      │  ← 多い（速い・低コスト）
       └─────────────┘
```

このプロジェクトでは主に:

- **ユニットテスト**: 関数やクラス単体のテスト
- **APIテスト**: エンドポイントのテスト（統合テスト）

を使用します。

---

## 最初のテストを書いてみる

### 1. ユニットテスト例

**対象コード** (`src/app/core/security/password.py`):

```python
def validate_password_strength(password: str) -> tuple[bool, str]:
    """パスワード強度をチェック"""
    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"
    # ...
    return True, ""
```

**テストコード** (`tests/unit/test_security_password.py`):

```python
from app.core.security import validate_password_strength

def test_password_too_short():
    """短すぎるパスワードは拒否される"""
    is_valid, error = validate_password_strength("short")
    assert is_valid is False
    assert "8文字以上" in error

def test_password_valid():
    """要件を満たすパスワードは受け入れられる"""
    is_valid, error = validate_password_strength("SecurePass123")
    assert is_valid is True
    assert error == ""
```

### 2. テストの実行

```bash
# 特定のテストファイルを実行
uv run pytest tests/unit/test_security_password.py

# すべてのテストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=src/app
```

---

## APIテストの基本

### APIエンドポイントのテスト例

**対象エンドポイント**: `POST /api/v1/sample-users/register`

**テストコード** (`tests/api/test_sample_users.py`):

```python
from httpx import AsyncClient

async def test_register_user(client: AsyncClient):
    """ユーザー登録が成功する"""
    response = await client.post(
        "/api/v1/sample-users/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "password" not in data  # パスワードは返されない

async def test_register_duplicate_email(client: AsyncClient):
    """重複メールアドレスでの登録は失敗する"""
    # 1回目: 成功
    await client.post(
        "/api/v1/sample-users/register",
        json={
            "email": "test@example.com",
            "username": "user1",
            "password": "SecurePass123!"
        }
    )

    # 2回目: 同じメールアドレスで失敗
    response = await client.post(
        "/api/v1/sample-users/register",
        json={
            "email": "test@example.com",
            "username": "user2",
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 400
    assert "既に登録されています" in response.json()["detail"]
```

---

## テストを書く際のポイント

### 1. テスト名は説明的に

```python
# ❌ 悪い例
def test_user():
    ...

# ✅ 良い例
def test_register_user_with_valid_data_succeeds():
    ...
```

### 2. AAA パターン

テストは3つの部分に分けて書く:

```python
def test_something():
    # Arrange: テストの準備
    user_data = {"email": "test@example.com", ...}

    # Act: 実際の操作
    response = await client.post("/api/v1/sample-users/register", json=user_data)

    # Assert: 結果の検証
    assert response.status_code == 201
```

### 3. 1つのテストで1つのことを確認

```python
# ❌ 悪い例：複数のことをテスト
def test_user_operations():
    test_create()
    test_update()
    test_delete()

# ✅ 良い例：分離
def test_create_user(): ...
def test_update_user(): ...
def test_delete_user(): ...
```

---

## よく使うpytestの機能

### フィクスチャ（共通の準備処理）

```python
import pytest

@pytest.fixture
async def test_user(client: AsyncClient):
    """テスト用ユーザーを作成"""
    response = await client.post(
        "/api/v1/sample-users/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    return response.json()

async def test_login_with_created_user(client: AsyncClient, test_user):
    """作成したユーザーでログインできる"""
    response = await client.post(
        "/api/v1/sample-users/login",
        json={
            "email": test_user["email"],
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 200
```

### パラメータ化（同じテストを複数のデータで実行）

```python
import pytest

@pytest.mark.parametrize("password,expected_valid", [
    ("short", False),
    ("nouppercase123", False),
    ("NOLOWERCASE123", False),
    ("NoNumbers!", False),
    ("ValidPass123!", True),
])
def test_password_validation(password, expected_valid):
    is_valid, _ = validate_password_strength(password)
    assert is_valid == expected_valid
```

---

## 実践: 自分のコードをテストしてみよう

### ステップ1: テスト対象を選ぶ

まずは単純な関数から始めましょう:

- バリデーション関数
- データ変換関数
- ユーティリティ関数

### ステップ2: テストファイルを作成

```bash
# ユニットテスト
tests/unit/test_[モジュール名].py

# APIテスト
tests/api/test_[機能名].py
```

### ステップ3: 正常系と異常系を書く

```python
# 正常系: 期待通りに動作するか
def test_function_with_valid_input(): ...

# 異常系: エラーケースを正しく処理するか
def test_function_with_invalid_input(): ...
def test_function_raises_error_when_...(): ...
```

### ステップ4: テストを実行

```bash
uv run pytest tests/unit/test_[ファイル名].py -v
```

---

## 次のステップ

基本的なテストを理解したら、以下の詳細なドキュメントに進んでください:

- **[テスト戦略](../../05-testing/01-testing-strategy/index.md)** - テスト全体の方針
- **[ユニットテスト詳細](../../05-testing/02-unit-testing/index.md)** - ユニットテストのベストプラクティス
- **[APIテスト詳細](../../05-testing/03-api-testing/index.md)** - APIテストの詳細
- **[データベーステスト](../../05-testing/04-database-testing/index.md)** - DBテストのパターン

---

## 参考: テスト実行の便利なオプション

```bash
# 失敗したテストだけ再実行
uv run pytest --lf

# 詳細な出力
uv run pytest -v

# 特定のテストだけ実行
uv run pytest tests/api/test_sample_users.py::test_register_user

# カバレッジレポート生成
uv run pytest --cov=src/app --cov-report=html
# htmlcov/index.html を開く
```
