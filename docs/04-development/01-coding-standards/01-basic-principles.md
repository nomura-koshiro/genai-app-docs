# 基本原則

バックエンドAPI開発における基本的なコーディング原則について説明します。

## 概要

本プロジェクトでは、保守性・可読性・拡張性の高いコードを書くために、以下の基本原則を遵守します：

- **型安全性（Type Safety）**
- **単一責任の原則（Single Responsibility Principle）**
- **DRY原則（Don't Repeat Yourself）**
- **KISS原則（Keep It Simple, Stupid）**

これらの原則を守ることで、バグの少ない、理解しやすい、変更に強いコードベースを維持できます。

---

## 1. 型安全性（Type Safety）

### 原則

Pythonの型ヒントを徹底的に使用し、静的型チェックによって実行時エラーを事前に防ぎます。

### コード例

#### 良い例

```python
from typing import Optional
from datetime import datetime

def get_user_by_id(user_id: int) -> Optional[User]:
    """IDによってユーザーを取得します。

    Args:
        user_id: ユーザーID

    Returns:
        ユーザーインスタンス、見つからない場合はNone
    """
    return db.query(User).filter(User.id == user_id).first()


def calculate_total_price(
    base_price: float,
    tax_rate: float = 0.1,
    discount: float = 0.0
) -> float:
    """合計金額を計算します。

    Args:
        base_price: 基本価格
        tax_rate: 税率（デフォルト: 0.1）
        discount: 割引額（デフォルト: 0.0）

    Returns:
        税込み合計金額
    """
    subtotal = base_price - discount
    return subtotal * (1 + tax_rate)
```

#### 悪い例

```python
# 型ヒントがない
def get_user_by_id(user_id):
    return db.query(User).filter(User.id == user_id).first()


# 戻り値の型が不明確
def calculate_total_price(base_price, tax_rate=0.1, discount=0.0):
    subtotal = base_price - discount
    return subtotal * (1 + tax_rate)
```

### 現在のプロジェクトでの実装例

```python
# src/app/repositories/base.py
from typing import Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """共通のCRUD操作を持つベースリポジトリ。"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        """IDによってレコードを取得します。"""
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """複数のレコードを取得します。"""
        # ... 実装
```

### ベストプラクティス

1. **すべての関数シグネチャに型ヒントを追加**
   - 引数の型
   - 戻り値の型
   - デフォルト値がある場合もその型を明示

2. **OptionalとUnion型を適切に使用**
   ```python
   from typing import Optional, Union

   # None を返す可能性がある場合
   def find_user(email: str) -> Optional[User]:
       pass

   # 複数の型を返す可能性がある場合（Python 3.10+）
   def get_value(key: str) -> str | int | None:
       pass
   ```

3. **Genericsを活用**
   - 再利用可能なコンポーネントには `TypeVar` と `Generic` を使用

4. **型チェッカーを活用**
   - `mypy` や `pyright` で静的型チェックを実施

---

## 2. 単一責任の原則（Single Responsibility Principle）

### 原則

1つのクラス、関数、モジュールは1つの責任のみを持つべきです。変更の理由は1つであるべきです。

### コード例

#### 良い例：責任が分離されている

```python
# src/app/services/user.py
class UserService:
    """ユーザー関連のビジネスロジック。"""

    async def create_user(self, user_data: UserCreate) -> User:
        """新しいユーザーを作成します。"""
        # バリデーション
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("User already exists")

        # パスワードハッシュ化
        hashed_password = hash_password(user_data.password)

        # ユーザー作成
        user = await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        return user


# src/app/core/security.py
def hash_password(password: str) -> str:
    """パスワードをハッシュ化します。"""
    return pwd_context.hash(password)
```

#### 悪い例：複数の責任が混在

```python
# ユーザーサービスが暗号化の詳細まで知っている
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        # バリデーション
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("User already exists")

        # パスワードハッシュ化の詳細をサービス層に記述（悪い）
        import bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(
            user_data.password.encode('utf-8'),
            salt
        ).decode('utf-8')

        # データベースアクセスの詳細も直接記述（悪い）
        query = "INSERT INTO users (email, password) VALUES (?, ?)"
        await self.db.execute(query, (user_data.email, hashed_password))

        return user
```

### 現在のプロジェクトでの層分離

```
API層 (routes/)       -> リクエスト/レスポンス処理
  ↓
サービス層 (services/) -> ビジネスロジック
  ↓
リポジトリ層 (repositories/) -> データアクセス
  ↓
モデル層 (models/)     -> データ構造定義
```

### ベストプラクティス

1. **1つのクラスは1つの役割**
   - UserService: ユーザーのビジネスロジック
   - UserRepository: ユーザーのデータアクセス
   - User Model: ユーザーのデータ構造

2. **関数は1つのことだけを行う**
   ```python
   # 良い例：各関数が1つの責任
   def validate_email(email: str) -> bool:
       """メールアドレスの形式を検証"""
       pass

   def check_email_exists(email: str) -> bool:
       """メールアドレスの存在を確認"""
       pass

   # 悪い例：複数の責任を持つ
   def validate_and_check_email(email: str) -> tuple[bool, bool]:
       """形式検証と存在確認を同時に行う"""
       pass
   ```

3. **ファイルの責任範囲を明確に**
   - 1ファイルは関連する機能のみを含む
   - 大きくなりすぎたら分割を検討

---

## 3. DRY原則（Don't Repeat Yourself）

### 原則

同じコードや知識を複数箇所に書かない。重複を避け、再利用可能なコンポーネントを作成します。

### コード例

#### 良い例：BaseRepositoryで共通処理を集約

```python
# src/app/repositories/base.py
class BaseRepository(Generic[ModelType]):
    """共通のCRUD操作を持つベースリポジトリ。"""

    async def get(self, id: int) -> ModelType | None:
        """IDによってレコードを取得します。"""
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """複数のレコードを取得します。"""
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


# 具体的なリポジトリは継承するだけ
class UserRepository(BaseRepository[User]):
    """ユーザーリポジトリ。"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
```

#### 悪い例：各リポジトリで同じコードを重複

```python
class UserRepository:
    async def get(self, id: int) -> User | None:
        return await self.db.get(User, id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[User]:
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class SessionRepository:
    # 同じコードを繰り返し（悪い）
    async def get(self, id: int) -> Session | None:
        return await self.db.get(Session, id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[Session]:
        query = select(Session).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

### ベストプラクティス

1. **共通ロジックを抽出**
   - Base クラスに共通メソッドを実装
   - ユーティリティ関数として切り出し

2. **設定値を一元管理**
   ```python
   # src/app/config.py
   class Settings(BaseSettings):
       """アプリケーション設定。"""
       DATABASE_URL: str
       SECRET_KEY: str
       ALGORITHM: str = "HS256"
       ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

   settings = Settings()
   ```

3. **マジックナンバーを定数化**
   ```python
   # 良い例
   MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
   DEFAULT_PAGE_SIZE = 20

   if file_size > MAX_UPLOAD_SIZE:
       raise ValidationError("File too large")

   # 悪い例
   if file_size > 10485760:  # この数字は何？
       raise ValidationError("File too large")
   ```

---

## 4. KISS原則（Keep It Simple, Stupid）

### 原則

シンプルに保つ。複雑な実装よりも、シンプルで理解しやすい実装を優先します。

### コード例

#### 良い例：シンプルで明確

```python
async def authenticate(self, email: str, password: str) -> User:
    """ユーザーを認証します。"""
    # ユーザー取得
    user = await self.repository.get_by_email(email)
    if not user:
        raise AuthenticationError("Invalid email or password")

    # パスワード検証
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    # アクティブ確認
    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    return user
```

#### 悪い例：不必要に複雑

```python
async def authenticate(self, email: str, password: str) -> User:
    """ユーザーを認証します。"""
    # 複雑なワンライナー（悪い）
    user = (await self.repository.get_by_email(email)) \
           if (user := await self.repository.get_by_email(email)) \
           and verify_password(password, user.hashed_password) \
           and user.is_active \
           else None

    if not user:
        raise AuthenticationError("Authentication failed")

    return user
```

### ベストプラクティス

1. **1行の長さを適切に保つ**
   - 1行は79-100文字以内
   - 長い式は適切に改行

2. **ネストを浅く保つ**
   ```python
   # 良い例：早期リターンでネストを浅く
   async def process_user(self, user_id: int) -> User:
       user = await self.get_user(user_id)
       if not user:
           raise NotFoundError("User not found")

       if not user.is_active:
           raise ValidationError("User is inactive")

       return user

   # 悪い例：ネストが深い
   async def process_user(self, user_id: int) -> User:
       user = await self.get_user(user_id)
       if user:
           if user.is_active:
               return user
           else:
               raise ValidationError("User is inactive")
       else:
           raise NotFoundError("User not found")
   ```

3. **関数を小さく保つ**
   - 1つの関数は20-30行以内を目安
   - 長くなったら分割を検討

4. **明確な命名**
   - 変数名、関数名は意図が明確に
   - 略語を避け、完全な単語を使用

---

## よくある間違いとその対処法

### 間違い1: 型ヒントの省略

```python
# 悪い例
def create_user(data):
    return User(**data)

# 良い例
def create_user(data: dict[str, Any]) -> User:
    return User(**data)
```

**対処法**: エディタのリンターや型チェッカーを設定し、警告を確認する。

### 間違い2: God Classの作成

```python
# 悪い例：1つのクラスが何でもやる
class UserManager:
    def create_user(self): pass
    def authenticate_user(self): pass
    def send_email(self): pass
    def hash_password(self): pass
    def validate_email(self): pass
    # ... さらに多数のメソッド
```

**対処法**: 責任ごとにクラスを分割する（UserService, EmailService, SecurityService等）。

### 間違い3: ハードコードされた値

```python
# 悪い例
if user_age < 18:
    return False

# 良い例
MINIMUM_AGE = 18
if user_age < MINIMUM_AGE:
    return False
```

**対処法**: 定数を定義し、設定ファイルで管理する。

### 間違い4: 過度に複雑な実装

```python
# 悪い例：ワンライナーで全てを行う
result = [user for user in users if user.is_active and user.age >= 18 and user.email_verified and user.last_login > datetime.now() - timedelta(days=30)]

# 良い例：段階的に処理
active_users = [user for user in users if user.is_active]
adult_users = [user for user in active_users if user.age >= 18]
verified_users = [user for user in adult_users if user.email_verified]
recent_users = [
    user for user in verified_users
    if user.last_login > datetime.now() - timedelta(days=30)
]
```

**対処法**: 複雑な処理は段階的に分解し、中間変数を使用する。

---

## 参考リンク

- [Python Type Hints - Official Documentation](https://docs.python.org/3/library/typing.html)
- [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [Clean Code in Python](https://github.com/zedr/clean-code-python)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [The Zen of Python (PEP 20)](https://www.python.org/dev/peps/pep-0020/)

---

次のセクション: [02-design-principles.md](./02-design-principles.md)
