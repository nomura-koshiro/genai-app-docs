# デコレータ使用例

このドキュメントでは、`app.core.decorators` モジュールで提供されるデコレータの使用例を示します。

> **Note**: デコレータは `app.api.decorators` から `app.core.decorators` に移動しました。
> API層に依存しない横断的関心事として、coreレイヤーに配置されています。

## 目次

### 1. 基本機能

- [log_execution](#log_execution) - ログ記録の自動化
- [measure_performance](#measure_performance) - パフォーマンス測定
- [async_timeout](#async_timeout) - タイムアウト保護

### 2. セキュリティ

- [validate_permissions](#validate_permissions) - リソースベース権限検証
- [handle_service_errors](#handle_service_errors) - エラーハンドリングの統一

### 3. データアクセス

- [transactional](#transactional) - トランザクション管理
- [cache_result](#cache_result) - キャッシュ管理

### 4. 信頼性向上

- [retry_on_error](#retry_on_error) - リトライ処理

### 5. 実践例

- [デコレータの組み合わせ](#デコレータの組み合わせ)
- [ベストプラクティス](#ベストプラクティス)

---

## 1. 基本機能

### log_execution

関数の実行をログに記録します。

```python
from app.core.decorators import log_execution

class PaymentService:
    @log_execution(level="info", include_args=True)
    async def process_payment(self, user_id: int, amount: float):
        """決済処理のトレーシング。

        ログ出力:
        INFO: Executing: process_payment
              extra={'function': 'process_payment', 'args': '(123, 100.0)', ...}
        INFO: Completed: process_payment
        """
        # 決済処理
        return {"status": "success"}

    @log_execution(level="debug", include_args=True, include_result=True)
    async def calculate_fee(self, amount: float):
        """開発環境でのデバッグログ。

        引数と戻り値の両方をログに記録。
        """
        fee = amount * 0.03
        return fee
```

#### 本番環境での使用例

```python
class SecurityService:
    @log_execution(level="warning", include_args=False)
    async def validate_credentials(self, email: str, password: str):
        """機密情報を含む引数はログに記録しない。

        include_args=False により、パスワードがログに残らない。
        """
        # 認証処理
        return is_valid
```

### measure_performance

非同期関数の実行時間を測定し、ログに記録します。

```python
from app.core.decorators import measure_performance

class SampleUserService:
    @measure_performance
    async def create_user(self, user_data: UserCreate):
        """実行時間が自動的にINFOレベルでログに記録される。

        ログ出力例:
        INFO: Performance: create_user took 0.0234s
              extra={'function': 'create_user', 'duration_seconds': 0.0234, ...}
        """
        # ユーザー作成処理
        return user
```

#### パフォーマンスボトルネックの特定

```python
class AnalyticsService:
    @measure_performance
    async def generate_report(self, user_id: int):
        """時間のかかる処理のパフォーマンス測定。"""
        # 複雑な集計処理
        data = await self.aggregate_user_data(user_id)
        report = await self.create_report(data)
        return report

    @measure_performance
    async def aggregate_user_data(self, user_id: int):
        """個別処理の測定も可能。"""
        # データ集計
        return data
```

---

## 2. エラーハンドリング

### handle_service_errors

サービス層のエラーを統一的にHTTPExceptionに変換します。

```python
from app.core.decorators import handle_service_errors
from fastapi import APIRouter

router = APIRouter()

@router.post("/users", response_model=UserResponse)
@handle_service_errors
async def create_user(
    user_data: UserCreate,
    service: UserServiceDep,
) -> UserResponse:
    """ユーザー作成エンドポイント。

    変換ルール:
    ValidationError → 400
    AuthenticationError → 401
    AuthorizationError → 403
    NotFoundError → 404
    その他のException → 500
    """
    user = await service.create_user(user_data)
    return UserResponse.model_validate(user)
```

---

## 3. データアクセス

### transactional

データベーストランザクションを自動管理します。

```python
from app.core.decorators import transactional

class SampleUserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    @transactional
    async def create_user(self, user_data: UserCreate):
        """成功時: 自動コミット
        失敗時: 自動ロールバック
        """
        user = await self.repository.create(user_data)
        # コミット処理は不要（デコレータが自動実行）
        return user

    @transactional
    async def transfer_points(self, from_user_id: int, to_user_id: int, points: int):
        """複数操作を1トランザクションで実行。"""
        # ポイント減算
        await self.repository.decrease_points(from_user_id, points)

        # ポイント加算
        await self.repository.increase_points(to_user_id, points)

        # 両方成功 → 自動コミット
        # どちらか失敗 → 自動ロールバック
```

#### トランザクション管理の改善前後

```python
# Before: 手動トランザクション管理
async def create_user(self, user_data: UserCreate):
    try:
        user = await self.repository.create(user_data)
        await self.db.commit()
        return user
    except Exception:
        await self.db.rollback()
        raise

# After: デコレータによる自動管理
@transactional
async def create_user(self, user_data: UserCreate):
    user = await self.repository.create(user_data)
    return user  # コミット/ロールバック自動
```

### cache_result

関数の結果をRedisにキャッシュします。

```python
from app.core.decorators import cache_result

class SampleUserService:
    @cache_result(ttl=3600, key_prefix="user")
    async def get_user(self, user_id: int):
        """ユーザー情報を1時間キャッシュ。

        1回目: データベースから取得 → キャッシュに保存
        2回目以降: キャッシュから即座に返却
        """
        user = await self.repository.get(user_id)
        return user

    @cache_result(ttl=86400, key_prefix="config")
    async def get_system_config(self):
        """システム設定を24時間キャッシュ。"""
        config = await self.repository.get_config()
        return config
```

#### キャッシュの無効化

```python
from app.core.cache import cache_manager

class SampleUserService:
    @cache_result(ttl=3600, key_prefix="user")
    async def get_user(self, user_id: int):
        return await self.repository.get(user_id)

    async def update_user(self, user_id: int, data: UserUpdate):
        """ユーザー更新時にキャッシュを削除。"""
        user = await self.repository.update(user_id, data)

        # キャッシュ無効化
        await cache_manager.delete(f"user:get_user:{user_id}")

        return user
```

---

## 4. 高度な処理

### retry_on_error

エラー時に自動リトライします（Exponential Backoff）。

```python
from app.core.decorators import retry_on_error

class ExternalAPIService:
    @retry_on_error(
        max_retries=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(ConnectionError, TimeoutError)
    )
    async def call_external_api(self, url: str):
        """外部API呼び出しを最大3回リトライ。

        リトライ間隔: 1秒 → 2秒 → 4秒

        対象外の例外:
        - ValidationError
        - AuthenticationError
        - NotFoundError
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            return response.json()
```

#### データベース接続エラーのリトライ

```python
from sqlalchemy.exc import OperationalError

class DatabaseService:
    @retry_on_error(
        max_retries=5,
        delay=0.5,
        backoff=1.5,
        exceptions=(OperationalError,)
    )
    async def execute_query(self, query: str):
        """一時的なDB接続エラーをリトライ。"""
        result = await self.db.execute(query)
        return result
```

---

## 5. 実践例

### デコレータの組み合わせ

#### 基本的な組み合わせ

```python
class SampleUserService:
    @measure_performance
    @transactional
    async def create_user(self, user_data: UserCreate):
        """パフォーマンス測定 + トランザクション管理。"""
        user = await self.repository.create(user_data)
        return user

    @cache_result(ttl=3600, key_prefix="user")
    @measure_performance
    async def get_user(self, user_id: int):
        """キャッシュ + パフォーマンス測定。"""
        user = await self.repository.get(user_id)
        return user
```

#### 高度な組み合わせ

```python
class ExternalAPIService:
    @cache_result(ttl=600, key_prefix="api")
    @retry_on_error(max_retries=3, exceptions=(ConnectionError,))
    @measure_performance
    @log_execution(level="info")
    async def fetch_user_data(self, user_id: int):
        """フルスタックデコレータ:

        1. ログ記録（実行開始）
        2. パフォーマンス測定開始
        3. キャッシュチェック → ヒットなら即座に返却
        4. キャッシュミス → リトライ付き外部API呼び出し
        5. パフォーマンス測定終了
        6. ログ記録（実行完了）
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/users/{user_id}")
            return response.json()
```

#### APIエンドポイントでの使用

```python
from fastapi import APIRouter
from app.core.decorators import handle_service_errors, measure_performance

router = APIRouter()

@router.post("/users", response_model=UserResponse)
@handle_service_errors
@measure_performance
async def create_user(
    user_data: UserCreate,
    service: UserServiceDep,
):
    """エンドポイントレベルでのデコレータ使用。

    - エラーハンドリング: 自動的にHTTPエラーに変換
    - パフォーマンス測定: エンドポイント全体の実行時間を記録
    """
    user = await service.create_user(user_data)
    return UserResponse.model_validate(user)
```

### ベストプラクティス

#### 1. デコレータの順序

デコレータは下から上に実行されるため、順序が重要です。

```python
# 推奨順序（下から上に実行）
@cache_result(ttl=3600, key_prefix="user")      # 5. キャッシュチェック（最初）
@retry_on_error(max_retries=3)                   # 4. リトライ
@measure_performance                             # 3. パフォーマンス測定
@transactional                                   # 2. トランザクション管理
@log_execution(level="info")                     # 1. ログ記録（最後）
async def complex_operation():
    pass
```

#### 2. キャッシュとトランザクションの組み合わせ

```python
class SampleUserService:
    # ❌ 非推奨: キャッシュと書き込み操作
    @cache_result(ttl=3600)
    @transactional
    async def create_user(self, user_data):
        # 書き込み操作にキャッシュは不要
        pass

    # ✅ 推奨: キャッシュは読み取り専用に
    @cache_result(ttl=3600)
    async def get_user(self, user_id: int):
        # 読み取り操作にキャッシュを適用
        pass

    # ✅ 推奨: 書き込み操作にトランザクション管理
    @transactional
    async def update_user(self, user_id: int, data):
        # 書き込み操作にトランザクション管理
        pass
```

#### 3. リトライと冪等性

```python
class PaymentService:
    # ❌ 危険: 冪等でない操作にリトライ
    @retry_on_error(max_retries=3)
    async def charge_credit_card(self, amount: float):
        # 決済が重複実行される可能性
        pass

    # ✅ 安全: 冪等な操作にリトライ
    @retry_on_error(max_retries=3)
    async def check_payment_status(self, transaction_id: str):
        # 何度実行しても同じ結果
        pass
```

#### 4. ログレベルの使い分け

```python
class SampleUserService:
    # 本番環境: INFO
    @log_execution(level="info", include_args=False)
    async def create_user(self, user_data):
        pass

    # 開発環境: DEBUG
    @log_execution(level="debug", include_args=True, include_result=True)
    async def debug_operation(self, data):
        pass

    # 重要操作: WARNING
    @log_execution(level="warning", include_args=True)
    async def delete_user(self, user_id: int):
        pass
```

## まとめ

デコレータを使用することで:

- **コードの重複削減**: 共通処理を1箇所で管理
- **可読性向上**: ビジネスロジックに集中
- **保守性向上**: 横断的関心事の分離
- **パフォーマンス改善**: キャッシュと測定により最適化が容易

適切にデコレータを組み合わせることで、効率的で保守しやすいコードを実現できます。
