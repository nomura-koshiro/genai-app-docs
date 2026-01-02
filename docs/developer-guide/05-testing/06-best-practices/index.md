# テストのベストプラクティス

## 概要

このドキュメントでは、高品質で保守性の高いテストを書くためのベストプラクティスを紹介します。これらの原則を守ることで、テストの価値を最大化し、長期的な保守コストを削減できます。

## AAA Pattern（Arrange-Act-Assert）

### 基本原則

AAA Patternは、テストを3つの明確なセクションに分割する標準的なパターンです。

```python
def test_user_creation():
    # Arrange（準備）: テストに必要なデータとコンテキストを準備
    email = "test@example.com"
    username = "testuser"
    password = "password123"

    # Act（実行）: テスト対象の操作を実行
    user = create_user(email=email, username=username, password=password)

    # Assert（検証）: 結果を検証
    assert user.email == email
    assert user.username == username
    assert user.id is not None
    assert user.is_active is True
```

### より複雑な例

```python
@pytest.mark.asyncio
async def test_file_upload_with_authentication():
    """認証付きファイルアップロードのテスト"""

    # Arrange: テストデータとコンテキストの準備
    # - ユーザーを作成
    user = await UserFactory.create_and_save(
        db_session,
        email="uploader@example.com"
    )
    # - 認証トークンを生成
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    # - アップロードするファイルを準備
    file_content = b"test file content"
    file_name = "test.txt"

    # Act: ファイルアップロードを実行
    response = await client.post(
        "/api/sample-files/upload",
        files={"file": (file_name, file_content, "text/plain")},
        headers=headers
    )

    # Assert: レスポンスとデータベースの状態を検証
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == file_name
    assert data["size"] == len(file_content)

    # データベースにファイルが保存されているか確認
    file = await get_file_from_db(db_session, data["file_id"])
    assert file is not None
    assert file.user_id == user.id
```

### コメントの活用

```python
def test_complex_business_logic():
    # Arrange
    # シナリオ: 会員ユーザーが割引クーポンを使用して商品を購入
    user = create_premium_user()  # プレミアム会員
    product = create_product(price=1000)  # 1000円の商品
    coupon = create_coupon(discount_rate=0.2)  # 20%割引クーポン

    # Act
    # 購入処理を実行
    order = purchase_with_coupon(user, product, coupon)

    # Assert
    # 期待される金額: 1000円 * (1 - 0.2) = 800円
    assert order.total_amount == 800
    assert order.discount_applied == 200
    assert order.status == "completed"
```

## テストの命名規則

### 説明的な命名

テスト名は、テストの目的と期待される動作を明確に表現する必要があります。

```python
# ❌ 悪い例: 何をテストしているか不明
def test_user():
    pass

def test_1():
    pass

def test_function():
    pass

# ✅ 良い例: テストの内容が明確
def test_create_user_with_valid_data_returns_user_object():
    """有効なデータでユーザー作成が成功する"""
    pass

def test_create_user_with_duplicate_email_raises_validation_error():
    """重複したメールアドレスでバリデーションエラーが発生する"""
    pass

def test_authenticate_user_with_wrong_password_returns_none():
    """間違ったパスワードで認証が失敗する"""
    pass
```

### 命名パターン

```python
# パターン1: test_<対象>_<条件>_<期待結果>
def test_upload_file_with_valid_format_succeeds():
    pass

def test_upload_file_with_too_large_size_fails():
    pass

# パターン2: test_should_<期待される動作>_when_<条件>
def test_should_return_404_when_file_not_found():
    pass

def test_should_create_user_when_valid_data_provided():
    pass

# パターン3: test_<動作>_<正常/異常系>
def test_file_download_success():
    pass

def test_file_download_unauthorized():
    pass

def test_file_download_not_found():
    pass
```

### テストクラスでの整理

```python
class TestUserAuthentication:
    """ユーザー認証のテストスイート"""

    class TestLogin:
        """ログイン機能のテスト"""

        def test_with_valid_credentials_succeeds(self):
            """有効な認証情報でログイン成功"""
            pass

        def test_with_invalid_password_fails(self):
            """無効なパスワードでログイン失敗"""
            pass

        def test_with_nonexistent_email_fails(self):
            """存在しないメールアドレスでログイン失敗"""
            pass

        def test_with_inactive_user_fails(self):
            """非アクティブユーザーでログイン失敗"""
            pass

    class TestLogout:
        """ログアウト機能のテスト"""

        def test_with_valid_token_succeeds(self):
            """有効なトークンでログアウト成功"""
            pass

        def test_with_expired_token_fails(self):
            """期限切れトークンでログアウト失敗"""
            pass
```

## テストの独立性

### 各テストは独立して実行可能であるべき

```python
# ❌ 悪い例: テストが相互に依存
class TestUserWorkflow:
    user_id = None

    def test_1_create_user(self):
        """ユーザーを作成（他のテストが依存）"""
        user = create_user("test@example.com")
        TestUserWorkflow.user_id = user.id  # クラス変数に保存

    def test_2_update_user(self):
        """ユーザーを更新（test_1に依存）"""
        update_user(TestUserWorkflow.user_id, {"name": "Updated"})

    def test_3_delete_user(self):
        """ユーザーを削除（test_1とtest_2に依存）"""
        delete_user(TestUserWorkflow.user_id)

# ✅ 良い例: 各テストが独立
class TestUserOperations:
    @pytest.fixture
    def test_user(self, db_session):
        """各テストで新しいユーザーを作成"""
        user = create_user("test@example.com")
        db_session.add(user)
        db_session.commit()
        yield user
        # クリーンアップ
        db_session.delete(user)
        db_session.commit()

    def test_create_user(self, db_session):
        """ユーザー作成のテスト"""
        user = create_user("new@example.com")
        assert user.email == "new@example.com"

    def test_update_user(self, test_user, db_session):
        """ユーザー更新のテスト"""
        update_user(test_user.id, {"username": "updated"})
        db_session.refresh(test_user)
        assert test_user.username == "updated"

    def test_delete_user(self, test_user, db_session):
        """ユーザー削除のテスト"""
        delete_user(test_user.id)
        assert get_user(test_user.id) is None
```

### テストの実行順序に依存しない

```powershell
# pytest は任意の順序でテストを実行できる
pytest tests\  # ランダムな順序でも成功する
pytest tests\ --randomly  # ランダム実行でも成功する
```

## テストのデータ管理

### テストデータの明示性

```python
# ❌ 悪い例: マジックナンバーとマジックストリング
def test_discount_calculation():
    price = 1000
    discount = 0.2
    result = calculate_discount(price, discount)
    assert result == 800

# ✅ 良い例: 意味のある変数名と明確な計算
def test_discount_calculation():
    """20%割引クーポンの適用"""
    original_price = 1000
    discount_rate = 0.2  # 20%割引
    expected_discounted_price = original_price * (1 - discount_rate)  # 800円

    actual_price = calculate_discount(original_price, discount_rate)

    assert actual_price == expected_discounted_price
```

### テストデータの生成

```python
# ファクトリを使用してテストデータを生成
@pytest.fixture
def sample_users():
    """テスト用ユーザーのサンプルセット"""
    return [
        UserFactory.create(email=f"user{i}@example.com", username=f"user{i}")
        for i in range(5)
    ]

def test_user_list(sample_users):
    """ユーザー一覧の取得"""
    users = get_user_list()
    assert len(users) == len(sample_users)
```

### テストデータのクリーンアップ

```python
@pytest.fixture
async def uploaded_file(client, db_session):
    """ファイルをアップロードし、テスト後に削除"""
    # セットアップ
    response = await client.post(
        "/api/sample-files/upload",
        files={"file": ("test.txt", b"content", "text/plain")}
    )
    file_data = response.json()

    yield file_data

    # クリーンアップ
    try:
        await client.delete(f"/api/sample-files/{file_data['file_id']}")
    except Exception:
        pass  # 削除に失敗しても続行
```

## テストのカバレッジ

### 重要なパスを優先

```python
class TestFileUpload:
    """ファイルアップロードのテスト"""

    # 1. ハッピーパス（最も重要）
    def test_upload_valid_file_succeeds(self):
        """正常なファイルアップロード"""
        pass

    # 2. エッジケース
    def test_upload_empty_file(self):
        """空ファイルのアップロード"""
        pass

    def test_upload_very_large_file(self):
        """非常に大きなファイルのアップロード"""
        pass

    # 3. エラーケース
    def test_upload_invalid_file_type(self):
        """無効なファイルタイプ"""
        pass

    def test_upload_without_authentication(self):
        """認証なしでアップロード"""
        pass

    def test_upload_exceeds_quota(self):
        """ストレージクォータ超過"""
        pass
```

### バウンダリバリューテスト

```python
@pytest.mark.parametrize("file_size,should_succeed", [
    (0, False),                    # 最小値以下
    (1, True),                     # 最小値
    (1024 * 1024, True),          # 通常値
    (10 * 1024 * 1024 - 1, True), # 最大値 - 1
    (10 * 1024 * 1024, True),     # 最大値
    (10 * 1024 * 1024 + 1, False),# 最大値 + 1
])
def test_file_size_limits(file_size, should_succeed):
    """ファイルサイズの境界値テスト"""
    file_content = b"x" * file_size
    result = validate_file_size(file_content)
    assert result == should_succeed
```

---

## Parametrizeパターン（テストの効率化）

`@pytest.mark.parametrize`を活用することで、テストコードの重複を削減し、保守性を向上させます。

### 基本パターン：入力と期待値のペア

```python
@pytest.mark.parametrize("input_value,expected", [
    ("valid@example.com", True),
    ("invalid-email", False),
    ("@example.com", False),
    ("user@", False),
])
def test_email_validation(input_value, expected):
    """メールアドレスバリデーションのパラメータ化テスト"""
    result = validate_email(input_value)
    assert result == expected
```

### IDsパターン：テストケースに名前を付ける

```python
@pytest.mark.parametrize("status_code,expected_message", [
    (400, "Bad Request"),
    (401, "Unauthorized"),
    (403, "Forbidden"),
    (404, "Not Found"),
    (500, "Internal Server Error"),
], ids=["bad_request", "unauthorized", "forbidden", "not_found", "internal_error"])
def test_error_responses(status_code, expected_message):
    """エラーレスポンスのテスト（IDsで可読性向上）"""
    response = create_error_response(status_code)
    assert response.message == expected_message
```

### 辞書パターン：複雑なテストケース

```python
# テストケースを辞書で定義（可読性向上）
VALIDATION_TEST_CASES = [
    {
        "id": "valid_user",
        "input": {"email": "user@example.com", "age": 25},
        "expected_valid": True,
    },
    {
        "id": "invalid_email",
        "input": {"email": "invalid", "age": 25},
        "expected_valid": False,
    },
    {
        "id": "underage_user",
        "input": {"email": "user@example.com", "age": 17},
        "expected_valid": False,
    },
]

@pytest.mark.parametrize(
    "test_case",
    VALIDATION_TEST_CASES,
    ids=[tc["id"] for tc in VALIDATION_TEST_CASES]
)
def test_user_validation(test_case):
    """ユーザーバリデーションの複雑なテストケース"""
    result = validate_user(test_case["input"])
    assert result == test_case["expected_valid"]
```

### 例外テストのParametrize化

```python
from app.core.exceptions import ValidationError, NotFoundError, AuthorizationError

@pytest.mark.parametrize("exception_class,expected_status,expected_message", [
    (ValidationError, 422, "Validation error"),
    (NotFoundError, 404, "Resource not found"),
    (AuthorizationError, 403, "Insufficient permissions"),
])
def test_exception_handling(exception_class, expected_status, expected_message):
    """例外クラスのステータスコードとメッセージをテスト"""
    exc = exception_class(expected_message)
    assert exc.status_code == expected_status
    assert exc.message == expected_message
```

### 複数のParametrizeの組み合わせ

```python
@pytest.mark.parametrize("user_role", ["admin", "user", "guest"])
@pytest.mark.parametrize("resource_type", ["file", "folder", "share"])
def test_permission_matrix(user_role, resource_type):
    """ロールとリソースタイプの全組み合わせをテスト（3 x 3 = 9テスト）"""
    result = check_permission(user_role, resource_type)
    # 期待される権限をマトリクスで確認
    expected = PERMISSION_MATRIX[user_role][resource_type]
    assert result == expected
```

### Parametrizeのベストプラクティス

```python
# ✅ 良い例：関連するテストケースをグループ化
@pytest.mark.parametrize("password,is_valid,reason", [
    # 有効なパスワード
    ("SecurePass123!", True, "valid"),
    ("MyP@ssw0rd", True, "valid"),
    # 長さ不足
    ("Short1!", False, "too_short"),
    # 大文字なし
    ("lowercase123!", False, "no_uppercase"),
    # 数字なし
    ("NoNumbers!", False, "no_digit"),
])
def test_password_validation(password, is_valid, reason):
    """パスワードバリデーション（理由も含めて検証）"""
    result, error = validate_password(password)
    assert result == is_valid
    if not is_valid:
        assert reason in error


# ❌ 悪い例：個別のテスト関数を大量に作成
def test_password_valid():
    assert validate_password("SecurePass123!")[0] == True

def test_password_too_short():
    assert validate_password("Short1!")[0] == False

def test_password_no_uppercase():
    assert validate_password("lowercase123!")[0] == False
# ... 以下大量の似たようなテスト
```

### テスト数削減の効果

Parametrizeを活用することで、テストの保守性が大幅に向上します：

| アプローチ | テスト関数数 | テストケース数 | 保守性 |
|-----------|------------|--------------|-------|
| 個別関数 | 10個 | 10ケース | 低（重複コード多い） |
| Parametrize | 1個 | 10ケース | 高（1箇所で管理） |

```python
# Before: 10個の似たテスト関数（保守困難）
def test_validate_email_valid(): ...
def test_validate_email_no_at(): ...
def test_validate_email_no_domain(): ...
# ... 7個続く

# After: 1個のParametrize化テスト（保守容易）
@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("invalid", False),
    ("@example.com", False),
    # ... 7ケース追加
], ids=["valid", "no_at", "no_local", ...])
def test_validate_email(email, is_valid):
    assert validate_email(email) == is_valid
```

## アサーションのベストプラクティス

### 1つのテストに1つの概念

```python
# ❌ 悪い例: 複数の概念を1つのテストで検証
def test_user_operations():
    # ユーザー作成
    user = create_user("test@example.com")
    assert user.email == "test@example.com"

    # ユーザー更新
    update_user(user.id, {"username": "updated"})
    assert user.username == "updated"

    # ユーザー削除
    delete_user(user.id)
    assert get_user(user.id) is None

# ✅ 良い例: 各概念を別々のテストで検証
def test_create_user():
    """ユーザー作成"""
    user = create_user("test@example.com")
    assert user.email == "test@example.com"

def test_update_user():
    """ユーザー更新"""
    user = create_user("test@example.com")
    update_user(user.id, {"username": "updated"})
    assert user.username == "updated"

def test_delete_user():
    """ユーザー削除"""
    user = create_user("test@example.com")
    delete_user(user.id)
    assert get_user(user.id) is None
```

### 具体的なアサーション

```python
# ❌ 悪い例: 曖昧なアサーション
def test_user_creation():
    user = create_user("test@example.com")
    assert user  # 何を検証しているか不明確

# ✅ 良い例: 具体的なアサーション
def test_user_creation():
    email = "test@example.com"
    user = create_user(email)

    # 各属性を明示的に検証
    assert user.id is not None, "ユーザーIDが設定されていない"
    assert user.email == email, f"メールアドレスが一致しない: {user.email}"
    assert user.is_active is True, "ユーザーがアクティブでない"
    assert user.created_at is not None, "作成日時が設定されていない"
    assert isinstance(user.created_at, datetime), "作成日時の型が正しくない"
```

### カスタムアサーションメッセージ

```python
def test_file_upload():
    response = client.post("/api/sample-files/upload", files={"file": ...})

    assert response.status_code == 201, (
        f"ファイルアップロードが失敗: "
        f"ステータスコード {response.status_code}, "
        f"レスポンス: {response.json()}"
    )

    data = response.json()
    assert "file_id" in data, "レスポンスにfile_idが含まれていない"
    assert data["size"] > 0, f"ファイルサイズが不正: {data['size']}"
```

## テストのパフォーマンス

### 高速なテストを書く

```python
# ❌ 遅い: 実際のファイルシステムを使用
def test_file_processing():
    with open("/tmp/test.txt", "w") as f:
        f.write("content")
    result = process_file("/tmp/test.txt")
    os.remove("/tmp/test.txt")

# ✅ 速い: インメモリ処理
def test_file_processing():
    from io import StringIO
    file_content = StringIO("content")
    result = process_file(file_content)
```

### 並列実行の活用

```powershell
# pytest-xdist を使用して並列実行
pytest -n auto  # CPU数に応じて自動調整
pytest -n 4     # 4プロセスで実行
```

### テストのグループ化

```python
# pytest.ini
[tool.pytest.ini_options]
markers = [
    "slow: 遅いテスト",
    "integration: 統合テスト",
    "unit: ユニットテスト",
]
```

```powershell
# 高速なテストのみ実行
pytest -m "not slow"

# ユニットテストのみ実行
pytest -m unit
```

## テストの保守性

### DRY原則の適用

```python
# ❌ 悪い例: 重複したセットアップコード
def test_user_creation():
    db = create_test_db()
    db.connect()
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
    db.disconnect()

def test_user_update():
    db = create_test_db()
    db.connect()
    user = create_user("test@example.com")
    update_user(user.id, {"username": "updated"})
    db.disconnect()

# ✅ 良い例: フィクスチャで共通コードを抽出
@pytest.fixture
def db_connection():
    db = create_test_db()
    db.connect()
    yield db
    db.disconnect()

@pytest.fixture
def test_user(db_connection):
    return create_user("test@example.com")

def test_user_creation(test_user):
    assert test_user.email == "test@example.com"

def test_user_update(test_user):
    update_user(test_user.id, {"username": "updated"})
    assert test_user.username == "updated"
```

### テストヘルパー関数

```python
# tests/helpers.py
async def create_authenticated_client(user=None):
    """認証済みクライアントを作成"""
    if user is None:
        user = await UserFactory.create_and_save()

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    return TestClient(app), headers, user

# テストでの使用
async def test_protected_endpoint():
    client, headers, user = await create_authenticated_client()

    response = client.get("/api/sample-users/sample-me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == user.email
```

## テストドキュメント

### docstringの活用

```python
def test_file_upload_with_authentication():
    """認証付きファイルアップロードのテスト

    シナリオ:
        1. ユーザーを作成して認証トークンを取得
        2. 認証ヘッダー付きでファイルをアップロード
        3. アップロードが成功することを確認
        4. ファイルがユーザーに紐付けられていることを確認

    期待される結果:
        - ステータスコード: 201
        - レスポンスにfile_idが含まれる
        - ファイルがデータベースに保存される
        - ファイルのuser_idが正しい
    """
    pass
```

### テストの目的を明確に

```python
class TestRateLimiting:
    """レート制限機能のテスト

    このテストスイートは、APIレート制限が正しく動作することを検証します。
    レート制限により、悪意のあるユーザーによるAPI濫用を防ぎます。

    テスト対象:
        - 制限内のリクエストは成功する
        - 制限を超えるとHTTP 429エラーが返される
        - 時間経過後に制限がリセットされる
        - 異なるエンドポイントで独立した制限が適用される
    """

    def test_within_rate_limit(self):
        """レート制限内のリクエスト"""
        pass

    def test_exceeds_rate_limit(self):
        """レート制限を超えるリクエスト"""
        pass
```

## よくあるアンチパターン

### 1. テストの相互依存

```python
# ❌ アンチパターン
class TestSequence:
    def test_step_1(self):
        self.result = perform_step_1()

    def test_step_2(self):
        perform_step_2(self.result)  # step_1に依存
```

### 2. 外部サービスへの実際の呼び出し

```python
# ❌ アンチパターン
def test_send_email():
    send_email_via_smtp("test@example.com", "Test")  # 実際にメール送信

# ✅ 修正
def test_send_email(mocker):
    mock_smtp = mocker.patch("smtplib.SMTP")
    send_email_via_smtp("test@example.com", "Test")
    mock_smtp.assert_called_once()
```

### 3. 時刻依存のテスト

```python
# ❌ アンチパターン
def test_current_hour():
    now = datetime.now()
    assert now.hour == 14  # 14時にしか成功しない

# ✅ 修正
def test_current_hour(mocker):
    mock_now = datetime(2024, 1, 1, 14, 0, 0)
    mocker.patch("datetime.datetime.now", return_value=mock_now)
    now = datetime.now()
    assert now.hour == 14
```

### 4. 過度に複雑なテスト

```python
# ❌ アンチパターン
def test_everything():
    # 100行以上のテストコード
    # 複数の概念を検証
    # 理解が困難

# ✅ 修正
def test_specific_behavior():
    # 1つの明確な概念をテスト
    # シンプルで読みやすい
```

## テストレビューのチェックリスト

### コードレビュー時の確認項目

- [ ] テスト名は説明的か？
- [ ] AAA Patternに従っているか？
- [ ] テストは独立しているか？
- [ ] アサーションは具体的か？
- [ ] エッジケースをカバーしているか？
- [ ] モックは適切に使用されているか？
- [ ] テストデータはクリーンアップされているか？
- [ ] 非同期処理は正しく扱われているか？
- [ ] テストは高速に実行されるか？
- [ ] docstringは適切か？

## 参考リンク

- [Test Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [xUnit Test Patterns](http://xunitpatterns.com/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Effective Unit Testing](https://effectivesoftwaretesting.com/)
- [Testing Patterns](https://testdesign.org/)

## まとめ

良いテストは、以下の特徴を持ちます：

1. **読みやすい**: 誰でも理解できる明確なコード
2. **保守しやすい**: 変更が容易で、壊れにくい
3. **高速**: 頻繁に実行できる速度
4. **信頼できる**: 一貫した結果を返す
5. **独立している**: 他のテストに依存しない
6. **意味がある**: 実際のバグを見つけられる

これらの原則に従うことで、長期的に価値のあるテストスイートを構築できます。

## 次のステップ

- [テスト戦略](./01-testing-strategy.md) - 全体的なテスト戦略
- [ユニットテスト](./02-unit-testing.md) - pytest基礎
- [APIテスト](./03-api-testing.md) - FastAPIのテスト
- [データベーステスト](./04-database-testing.md) - SQLAlchemyのテスト
- [モックとフィクスチャ](./05-mocks-fixtures.md) - 高度なテスト技法
