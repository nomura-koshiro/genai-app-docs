# ユニットテスト

## 概要

ユニットテストは、個別の関数やメソッドが期待通りに動作するかを検証します。このドキュメントでは、pytestを使用したユニットテストの基礎から応用まで、実践的な例とともに説明します。

## pytest基礎

### pytestとは

pytestは、Pythonで最も人気のあるテストフレームワークです。シンプルな構文、強力な機能、豊富なプラグインエコシステムを提供します。

### 基本的なテストの書き方

```python
# tests/unit/test_basic.py
def test_addition():
    """基本的な加算のテスト"""
    assert 1 + 1 == 2

def test_string_concatenation():
    """文字列の結合をテスト"""
    result = "hello" + " " + "world"
    assert result == "hello world"

def test_list_operations():
    """リスト操作をテスト"""
    items = [1, 2, 3]
    items.append(4)
    assert len(items) == 4
    assert 4 in items
```

### テストの実行

```bash
# 全てのテストを実行
pytest

# 特定のファイルを実行
pytest tests/unit/test_basic.py

# 特定のテスト関数を実行
pytest tests/unit/test_basic.py::test_addition

# 詳細な出力
pytest -v

# より詳細な出力
pytest -vv

# 標準出力も表示
pytest -s
```

## アサーション（検証）

### 基本的なアサーション

```python
def test_various_assertions():
    """様々なアサーションの例"""
    # 等価性
    assert 2 + 2 == 4
    assert "hello" == "hello"

    # 不等価
    assert 3 != 4
    assert "a" != "b"

    # 真偽値
    assert True
    assert not False
    assert bool([1, 2, 3])  # 空でないリストはTrue
    assert not bool([])  # 空のリストはFalse

    # 比較
    assert 5 > 3
    assert 2 < 10
    assert 5 >= 5
    assert 3 <= 3

    # メンバーシップ
    assert "a" in ["a", "b", "c"]
    assert 5 not in [1, 2, 3]

    # 型チェック
    assert isinstance(42, int)
    assert isinstance("hello", str)
```

### 例外のテスト

```python
import pytest
from app.core.exceptions import ValidationError, NotFoundError

def test_exception_raised():
    """例外が発生することをテスト"""
    with pytest.raises(ValueError):
        int("not a number")

def test_exception_with_message():
    """例外メッセージもテスト"""
    with pytest.raises(ValueError, match="invalid literal"):
        int("not a number")

def test_custom_exception():
    """カスタム例外をテスト"""
    def validate_age(age: int):
        if age < 0:
            raise ValidationError("Age cannot be negative")

    with pytest.raises(ValidationError) as exc_info:
        validate_age(-1)

    assert "cannot be negative" in str(exc_info.value)
```

## フィクスチャ（Fixtures）

フィクスチャは、テストに必要なセットアップやリソースを提供する仕組みです。

### 基本的なフィクスチャ

```python
import pytest

@pytest.fixture
def sample_user():
    """テスト用ユーザーデータを提供"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
    }

def test_user_email(sample_user):
    """ユーザーのメールアドレスをテスト"""
    assert sample_user["email"] == "test@example.com"

def test_user_active(sample_user):
    """ユーザーがアクティブかテスト"""
    assert sample_user["is_active"] is True
```

### フィクスチャのスコープ

```python
# function: 各テスト関数ごとに実行（デフォルト）
@pytest.fixture(scope="function")
def function_fixture():
    print("Setup: function")
    yield "function data"
    print("Teardown: function")

# class: 各テストクラスごとに実行
@pytest.fixture(scope="class")
def class_fixture():
    print("Setup: class")
    yield "class data"
    print("Teardown: class")

# module: 各モジュールごとに実行
@pytest.fixture(scope="module")
def module_fixture():
    print("Setup: module")
    yield "module data"
    print("Teardown: module")

# session: テストセッション全体で1回だけ実行
@pytest.fixture(scope="session")
def session_fixture():
    print("Setup: session")
    yield "session data"
    print("Teardown: session")
```

### セットアップとティアダウン

```python
import pytest
import tempfile
import os

@pytest.fixture
def temp_file():
    """一時ファイルを作成し、テスト後に削除"""
    # Setup
    fd, path = tempfile.mkstemp()
    os.write(fd, b"test content")
    os.close(fd)

    yield path  # テストに値を渡す

    # Teardown
    if os.path.exists(path):
        os.remove(path)

def test_file_operations(temp_file):
    """一時ファイルを使用したテスト"""
    with open(temp_file, "r") as f:
        content = f.read()
    assert content == "test content"
```

### フィクスチャの組み合わせ

```python
@pytest.fixture
def user_data():
    """ユーザーデータを提供"""
    return {
        "username": "testuser",
        "email": "test@example.com",
    }

@pytest.fixture
def user_with_password(user_data):
    """パスワード付きユーザーデータ（別のフィクスチャを使用）"""
    from app.core.security import hash_password
    user_data["password"] = hash_password("testpassword123")
    return user_data

def test_user_authentication(user_with_password):
    """認証をテスト"""
    from app.core.security import verify_password
    assert verify_password("testpassword123", user_with_password["password"])
```

## パラメータ化テスト

同じテストロジックを異なるデータで実行する際に有効です。

### 基本的なパラメータ化

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_double(input, expected):
    """数値を2倍にする関数のテスト"""
    def double(x):
        return x * 2

    assert double(input) == expected
```

### 複数のパラメータ

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 1, 2),
    (2, 3, 5),
    (10, 20, 30),
    (-1, 1, 0),
])
def test_addition(a, b, expected):
    """加算のテスト"""
    assert a + b == expected
```

### パラメータのID指定

```python
@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("invalid.email", False),
    ("@example.com", False),
    ("user@", False),
], ids=["valid", "no-at", "no-local", "no-domain"])
def test_email_validation(email, is_valid):
    """メールアドレスのバリデーション"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    assert bool(re.match(pattern, email)) == is_valid
```

### 複雑なパラメータ化

```python
import pytest

# テストケースを辞書で定義
test_cases = [
    {
        "id": "valid_user",
        "input": {"username": "john", "email": "john@example.com"},
        "expected": True,
    },
    {
        "id": "missing_email",
        "input": {"username": "john"},
        "expected": False,
    },
    {
        "id": "invalid_email",
        "input": {"username": "john", "email": "invalid"},
        "expected": False,
    },
]

@pytest.mark.parametrize("test_case", test_cases, ids=[tc["id"] for tc in test_cases])
def test_user_validation(test_case):
    """ユーザーデータのバリデーション"""
    def validate_user(data):
        if "email" not in data:
            return False
        if "@" not in data["email"]:
            return False
        return True

    result = validate_user(test_case["input"])
    assert result == test_case["expected"]
```

## 実践例：セキュリティ機能のテスト

### パスワードハッシュ化のテスト

```python
# tests/unit/core/test_security.py
import pytest
from app.core.security import hash_password, verify_password

class TestPasswordHashing:
    """パスワードハッシュ化のテストスイート"""

    def test_hash_password_returns_string(self):
        """パスワードのハッシュ化が文字列を返す"""
        hashed = hash_password("mypassword123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """同じパスワードでも異なるハッシュが生成される"""
        password = "mypassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # ソルト付きハッシュなので異なる

    def test_verify_password_with_correct_password(self):
        """正しいパスワードで検証が成功する"""
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password(self):
        """間違ったパスワードで検証が失敗する"""
        password = "mypassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    @pytest.mark.parametrize("password", [
        "short",
        "verylongpasswordwithmanychars123456789",
        "パスワード123",  # 日本語
        "p@ssw0rd!#$%",  # 特殊文字
    ])
    def test_hash_various_passwords(self, password):
        """様々なパスワードをハッシュ化できる"""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
```

### JWTトークンのテスト

```python
# tests/unit/core/test_security.py
import pytest
from datetime import timedelta
from app.core.security import create_access_token, decode_access_token

class TestJWTToken:
    """JWTトークンのテストスイート"""

    def test_create_access_token(self):
        """アクセストークンの作成"""
        data = {"sub": "123"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """アクセストークンのデコード"""
        data = {"sub": "123", "username": "testuser"}
        token = create_access_token(data)
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"
        assert "exp" in payload  # 有効期限が含まれている

    def test_decode_invalid_token(self):
        """無効なトークンのデコードは失敗する"""
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_token_expiration(self):
        """トークンの有効期限"""
        import time
        data = {"sub": "123"}
        # 1秒で期限切れ
        token = create_access_token(data, expires_delta=timedelta(seconds=1))

        # すぐにデコード（成功）
        payload = decode_access_token(token)
        assert payload is not None

        # 2秒待ってからデコード（失敗）
        time.sleep(2)
        payload = decode_access_token(token)
        assert payload is None

    def test_token_with_custom_data(self):
        """カスタムデータを含むトークン"""
        data = {
            "sub": "123",
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)
        payload = decode_access_token(token)

        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
```

## 実践例：ユーティリティ関数のテスト

### ファイル関連のテスト

```python
# tests/unit/utils/test_file_utils.py
import pytest
import os
from pathlib import Path

class TestFileUtils:
    """ファイルユーティリティのテストスイート"""

    @pytest.fixture
    def temp_directory(self, tmp_path):
        """一時ディレクトリを提供"""
        return tmp_path

    def test_generate_file_id(self):
        """ファイルIDの生成"""
        from uuid import UUID

        def generate_file_id():
            import uuid
            return str(uuid.uuid4())

        file_id = generate_file_id()
        assert isinstance(file_id, str)
        # UUIDとして有効か確認
        assert UUID(file_id)

    def test_sanitize_filename(self):
        """ファイル名のサニタイゼーション"""
        def sanitize_filename(filename: str) -> str:
            import re
            # 危険な文字を削除
            filename = re.sub(r'[<>:"/\\|?*]', '', filename)
            # スペースをアンダースコアに
            filename = filename.replace(' ', '_')
            return filename

        assert sanitize_filename("test file.txt") == "test_file.txt"
        assert sanitize_filename("test/file.txt") == "testfile.txt"
        assert sanitize_filename("test<>file.txt") == "testfile.txt"

    @pytest.mark.parametrize("filename,expected", [
        ("document.pdf", "pdf"),
        ("image.jpg", "jpg"),
        ("archive.tar.gz", "gz"),
        ("noextension", ""),
        (".hidden", ""),
    ])
    def test_get_file_extension(self, filename, expected):
        """ファイル拡張子の取得"""
        def get_extension(filename: str) -> str:
            return Path(filename).suffix.lstrip('.')

        assert get_extension(filename) == expected

    def test_calculate_file_size(self, temp_directory):
        """ファイルサイズの計算"""
        test_file = temp_directory / "test.txt"
        content = "Hello World" * 100
        test_file.write_text(content)

        assert test_file.stat().st_size == len(content)

    def test_file_mime_type_detection(self):
        """MIMEタイプの検出"""
        import mimetypes

        def get_mime_type(filename: str) -> str:
            mime_type, _ = mimetypes.guess_type(filename)
            return mime_type or "application/octet-stream"

        assert get_mime_type("document.pdf") == "application/pdf"
        assert get_mime_type("image.jpg") == "image/jpeg"
        assert get_mime_type("script.py") == "text/x-python"
```

### データ変換のテスト

```python
# tests/unit/utils/test_converters.py
import pytest
from datetime import datetime, timezone

class TestDataConverters:
    """データ変換のテストスイート"""

    def test_convert_bytes_to_human_readable(self):
        """バイト数を人間が読みやすい形式に変換"""
        def format_bytes(size: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} PB"

        assert format_bytes(500) == "500.00 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024 * 1024) == "1.00 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"

    @pytest.mark.parametrize("input_date,expected_format", [
        (datetime(2024, 1, 1, 12, 0, 0), "2024-01-01T12:00:00"),
        (datetime(2024, 12, 31, 23, 59, 59), "2024-12-31T23:59:59"),
    ])
    def test_datetime_to_iso_format(self, input_date, expected_format):
        """日時をISO形式に変換"""
        def to_iso_format(dt: datetime) -> str:
            return dt.strftime("%Y-%m-%dT%H:%M:%S")

        assert to_iso_format(input_date) == expected_format

    def test_dict_to_query_string(self):
        """辞書をクエリ文字列に変換"""
        from urllib.parse import urlencode

        params = {
            "page": 1,
            "size": 10,
            "search": "test query",
        }
        query_string = urlencode(params)
        assert "page=1" in query_string
        assert "size=10" in query_string
        assert "search=test" in query_string
```

## よくある間違いとその対処法

### 1. テスト間の状態の共有

❌ **悪い例**:

```python
# グローバル変数を使用（テストが相互依存）
counter = 0

def test_increment():
    global counter
    counter += 1
    assert counter == 1

def test_another_increment():
    global counter
    counter += 1
    assert counter == 2  # 前のテストに依存
```

✅ **良い例**:

```python
@pytest.fixture
def counter():
    """各テストで新しいカウンターを提供"""
    return {"value": 0}

def test_increment(counter):
    counter["value"] += 1
    assert counter["value"] == 1

def test_another_increment(counter):
    counter["value"] += 1
    assert counter["value"] == 1  # 独立
```

### 2. 外部依存のあるテスト

❌ **悪い例**:

```python
def test_get_current_time():
    """現在時刻のテスト（時間依存）"""
    from datetime import datetime
    now = datetime.now()
    assert now.hour == 15  # 15時にしか成功しない
```

✅ **良い例**:

```python
def test_get_current_time(mocker):
    """現在時刻のテスト（モック使用）"""
    from datetime import datetime
    mock_now = datetime(2024, 1, 1, 15, 0, 0)
    mocker.patch("datetime.datetime.now", return_value=mock_now)

    now = datetime.now()
    assert now.hour == 15  # 常に成功
```

### 3. 具体的でないアサーション

❌ **悪い例**:

```python
def test_create_user():
    user = create_user("test@example.com")
    assert user  # 何をテストしているか不明確
```

✅ **良い例**:

```python
def test_create_user():
    email = "test@example.com"
    user = create_user(email)
    assert user.email == email
    assert user.is_active is True
    assert user.created_at is not None
```

## ベストプラクティス

### 1. テストの命名

```python
# パターン: test_<機能>_<条件>_<期待結果>

def test_hash_password_with_valid_input_returns_string():
    """有効な入力でパスワードハッシュが文字列を返す"""
    pass

def test_verify_password_with_wrong_password_returns_false():
    """間違ったパスワードで検証がFalseを返す"""
    pass
```

### 2. AAA Pattern（Arrange-Act-Assert）

```python
def test_user_creation():
    # Arrange: テストデータの準備
    email = "test@example.com"
    username = "testuser"

    # Act: 実際の処理を実行
    user = User(email=email, username=username)

    # Assert: 結果を検証
    assert user.email == email
    assert user.username == username
```

### 3. テストの独立性

```python
# 各テストが独立して実行可能
@pytest.fixture
def clean_state():
    """各テストでクリーンな状態を提供"""
    setup()
    yield
    cleanup()

def test_feature_a(clean_state):
    """機能Aのテスト"""
    pass

def test_feature_b(clean_state):
    """機能Bのテスト"""
    pass
```

### 4. テストの可読性

```python
def test_user_authentication_flow():
    """ユーザー認証フローのテスト

    1. ユーザーを作成
    2. パスワードをハッシュ化
    3. 認証を試みる
    4. 認証が成功することを確認
    """
    # 1. ユーザーを作成
    user = create_user("test@example.com", "password123")

    # 2. パスワードは自動的にハッシュ化される
    assert user.password != "password123"

    # 3. 認証を試みる
    authenticated = authenticate(user.email, "password123")

    # 4. 認証が成功することを確認
    assert authenticated is True
```

## 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest parametrize](https://docs.pytest.org/en/stable/parametrize.html)
- [効果的なpytestの書き方](https://docs.pytest.org/en/stable/goodpractices.html)

## 次のステップ

- [APIテスト](./03-api-testing.md) - FastAPIエンドポイントのテスト方法
- [データベーステスト](./04-database-testing.md) - データベースを使用したテスト
- [モックとフィクスチャ](./05-mocks-fixtures.md) - 高度なモックとフィクスチャの使用
