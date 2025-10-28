# リーダブルコード原則

『リーダブルコード』の原則に基づいた、読みやすく保守しやすいPython/FastAPIコードの書き方について説明します。

## 目次

1. [第1章: 理解しやすいコード](#第1章-理解しやすいコード)
2. [第2章: 名前に情報を詰め込む](#第2章-名前に情報を詰め込む)
3. [第3章: 誤解されない名前](#第3章-誤解されない名前)
4. [第4章: 美しさ](#第4章-美しさ)
5. [第5章: コメントすべきことを知る](#第5章-コメントすべきことを知る)
6. [第6章: コメントは正確で簡潔に](#第6章-コメントは正確で簡潔に)
7. [第7章: 制御フローを読みやすく](#第7章-制御フローを読みやすく)
8. [第8章: 巨大な式を分割](#第8章-巨大な式を分割)
9. [第9章: 変数と読みやすさ](#第9章-変数と読みやすさ)
10. [第10章: 無関係の下位問題を抽出](#第10章-無関係の下位問題を抽出)
11. [第11章: 一度に1つのことを](#第11章-一度に1つのことを)
12. [第12章: コードに思いを込める](#第12章-コードに思いを込める)
13. [第13章: 短いコードを書く](#第13章-短いコードを書く)
14. [第14章: テストと読みやすさ](#第14章-テストと読みやすさ)

---

## 第1章: 理解しやすいコード

**原則:** コードは他の人が最短時間で理解できるように書く。

```python
# ❌ Bad: 変数名が不明確
from datetime import datetime

d = datetime.now()
t = d.timestamp()

# ✅ Good: 変数名が意図を明確に表現
from datetime import datetime

current_datetime = datetime.now()
timestamp_in_seconds = current_datetime.timestamp()
```

**なぜ悪いのか:**

- `d`や`t`だけでは何を表すか分からない
- コードを読む人が文脈を推測する必要がある

**改善方法:**

- 変数名は明確で具体的にする
- 省略形は広く知られているもの以外使わない（`db`, `id`, `url`など）
- 単文字変数はループのインデックス以外では使わない

---

## 第2章: 名前に情報を詰め込む

**原則:** 名前には最大限の情報を詰め込む。

```python
# ❌ Bad: 単位や制約が不明
class ProductSchema(BaseModel):
    size: int
    delay: float
    limit: int

# ✅ Good: 単位や制約を明確に
class ProductSchema(BaseModel):
    size_in_megabytes: int
    delay_in_seconds: float
    max_retry_limit: int
```

**なぜ悪いのか:**

- `size`や`delay`だけでは単位が分からない
- 値の範囲や制約が不明確

**改善方法:**

- 単位を名前に含める（`_in_seconds`、`_in_bytes`など）
- 最小値・最大値を示す接頭辞を使う（`max_`、`min_`など）

```python
# ❌ Bad: booleanの名前が曖昧
read = True

# ✅ Good: is/has/canなどの接頭辞で意図を明確に
is_readable = True
has_permission = True
can_edit = False
```

**Python特有のベストプラクティス:**

```python
# ✅ Good: 型ヒントと組み合わせる
from typing import List

def get_active_users(
    user_ids: List[int],
    max_count: int = 100,
    include_deleted: bool = False,
) -> List[SampleUser]:
    """アクティブなユーザーを取得する."""
    pass
```

---

## 第3章: 誤解されない名前

**原則:** 名前が他の意味と間違えられることはないか?

```python
# ❌ Bad: filterは「除外する」とも「抽出する」とも取れる
def filter_users(users: List[SampleUser]) -> List[SampleUser]:
    pass

# ✅ Good: 明確な動詞を使用
def select_active_users(users: List[SampleUser]) -> List[SampleUser]:
    """アクティブなユーザーを抽出する."""
    return [user for user in users if user.is_active]

def exclude_inactive_users(users: List[SampleUser]) -> List[SampleUser]:
    """非アクティブなユーザーを除外する."""
    return [user for user in users if user.is_active]
```

**なぜ悪いのか:**

- `filter`は文脈によって「抽出」と「除外」の両方の意味を持つ
- 読み手が誤解する可能性がある

**改善方法:**

- `select`（選択）、`exclude`（除外）、`find`（検索）など明確な動詞を使う
- コメントではなく名前で意図を伝える

```python
# ❌ Bad: 範囲が不明確（境界を含む？含まない？）
def is_in_range(value: float, min_val: float, max_val: float) -> bool:
    return min_val <= value <= max_val

# ✅ Good: 境界を明確に
def is_in_range_inclusive(value: float, min_val: float, max_val: float) -> bool:
    """valueがmin_val以上、max_val以下かチェック（境界を含む）."""
    return min_val <= value <= max_val

def is_in_range_exclusive(value: float, min_val: float, max_val: float) -> bool:
    """valueがmin_valより大きく、max_valより小さいかチェック（境界を含まない）."""
    return min_val < value < max_val
```

---

## 第4章: 美しさ

**原則:** 一貫性のあるレイアウトで読みやすくする。

```python
# ❌ Bad: レイアウトが不揃い
class SampleUser(Base):
    __tablename__ = "sample_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean)
    role: Mapped[str] = mapped_column(String(20))

# ✅ Good: 関連する項目をグループ化
class SampleUser(Base):
    """ユーザーモデル."""

    __tablename__ = "sample_users"

    # 識別情報
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # ステータス
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
```

**なぜ悪いのか:**

- 関連する項目が離れていると全体像が把握しにくい
- 視覚的な整理がないと読みにくい

**改善方法:**

- 関連する項目をグループ化する
- 空行とコメントで区切りを明確にする
- 一貫したインデントと整列を使う

---

## 第5章: コメントすべきことを知る

**原則:** コードから読み取れることをコメントに書かない。

```python
# ❌ Bad: コードを繰り返すだけのコメント
# ユーザーIDを取得する
user_id = user.id

# ✅ Good: コードから読み取れない「なぜ」を説明
# パフォーマンス最適化: 頻繁にアクセスされるため事前にキャッシュ
cached_user_id = user.id

# ❌ Bad: 実装の詳細をコメント
# iを1ずつ増やして配列をループ
for i in range(len(users)):
    process_user(users[i])

# ✅ Good: 意図や理由をコメント
# 新しいユーザーから順に処理（作成日時の降順）
sorted_users = sorted(users, key=lambda u: u.created_at, reverse=True)
for user in sorted_users:
    process_user(user)
```

**なぜ悪いのか:**

- コードを繰り返すだけのコメントは価値がない
- メンテナンスコストが増える（コードとコメントの二重管理）

**改善方法:**

- 「なぜ」を説明する（「何を」ではなく）
- コードで表現できることはコメントしない
- 定数には定義の理由を書く

```python
# ✅ Good: 定数の理由を説明
# APIレート制限を回避するため、リトライ間隔を指数関数的に増加
MAX_RETRY_DELAY_SECONDS = 32

# データベースの接続プール制限に合わせる
MAX_CONCURRENT_REQUESTS = 10

# LangChain APIのタイムアウト（公式ドキュメント推奨値）
LANGCHAIN_TIMEOUT_SECONDS = 300
```

**Docstringの使用:**

```python
# ✅ Good: 関数のdocstringは「何を」と「なぜ」を説明
async def get_user_with_retry(
    user_id: int,
    max_retries: int = 3,
) -> SampleUser:
    """
    ユーザーを取得する（リトライ機能付き）.

    ネットワークエラーやタイムアウトが発生する可能性があるため、
    自動的にリトライを行う。

    Args:
        user_id: ユーザーID
        max_retries: 最大リトライ回数（デフォルト: 3）

    Returns:
        ユーザーオブジェクト

    Raises:
        NotFoundError: ユーザーが見つからない場合
        DatabaseError: リトライ後もデータベース接続に失敗した場合
    """
    pass
```

---

## 第6章: コメントは正確で簡潔に

**原則:** コメントは情報密度を高く、簡潔に書く。

```python
# ❌ Bad: 冗長なコメント
# この関数は、ユーザーのリストを受け取り、その中からアクティブなユーザーだけを
# 抽出して、新しいリストとして返す関数です。
def get_active_users(users: List[SampleUser]) -> List[SampleUser]:
    return [user for user in users if user.is_active]

# ✅ Good: 簡潔で情報密度の高いコメント
def get_active_users(users: List[SampleUser]) -> List[SampleUser]:
    """アクティブなユーザーのみを抽出."""
    return [user for user in users if user.is_active]
```

**なぜ悪いのか:**

- 冗長なコメントは読むのに時間がかかる
- 重要な情報が埋もれる

**改善方法:**

- 1行で済ませる（docstringの概要行）
- 具体的な例を示す
- 曖昧な代名詞（それ、これ）を避ける

```python
# ✅ Good: 具体的な例を示す
def parse_date(date_string: str) -> datetime:
    """
    日付文字列をdatetimeオブジェクトに変換.

    サポート形式: 'YYYY-MM-DD', 'YYYY/MM/DD'

    例:
        >>> parse_date('2024-01-15')
        datetime(2024, 1, 15, 0, 0)
    """
    pass
```

---

## 第7章: 制御フローを読みやすく

**原則:** 条件やループは自然な順序で書く。

```python
# ❌ Bad: 否定形と条件の順序が不自然
if 10 < length:
    process()

if not is_admin:
    return

# ✅ Good: 肯定形と自然な順序
if length > 10:
    process()

if is_admin:
    # 管理者の処理
    admin_process()
else:
    # 一般ユーザーの処理
    user_process()
```

**なぜ悪いのか:**

- 否定形は理解に時間がかかる
- 不自然な順序は混乱を招く

**改善方法:**

- 肯定形を優先する
- 変数は左、定数は右（`length > 10`）
- 単純な条件を先に書く

```python
# ❌ Bad: 深いネスト
async def process_user(user: SampleUser | None) -> str:
    if user:
        if user.is_active:
            if user.email:
                return await send_email(user.email)
            else:
                return "メールアドレスなし"
        else:
            return "ユーザーが無効"
    else:
        return "ユーザーが存在しない"

# ✅ Good: 早期リターンでネストを減らす（ガード節）
async def process_user(user: SampleUser | None) -> str:
    """ユーザーを処理し、メールを送信する."""
    if not user:
        return "ユーザーが存在しない"

    if not user.is_active:
        return "ユーザーが無効"

    if not user.email:
        return "メールアドレスなし"

    return await send_email(user.email)
```

**FastAPI特有のパターン:**

```python
# ✅ Good: HTTPExceptionで早期リターン
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: SampleUserServiceDep,
) -> SampleUserResponse:
    """ユーザーを取得."""
    user = await service.get_user(user_id)

    # ガード節で早期リターン
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="無効なユーザーです")

    return SampleUserResponse.from_orm(user)
```

---

## 第8章: 巨大な式を分割

**原則:** 巨大な式は説明変数で分割する。

```python
# ❌ Bad: 巨大で理解しにくい式
from datetime import datetime, timedelta

if (
    user.role == "admin"
    and user.is_active
    and "write" in user.permissions
    and datetime.now() - user.last_login_at < timedelta(days=7)
):
    allow_edit()

# ✅ Good: 説明変数で分割
from datetime import datetime, timedelta

is_admin = user.role == "admin"
is_active = user.is_active
has_write_permission = "write" in user.permissions
last_login_within_week = datetime.now() - user.last_login_at < timedelta(days=7)

if is_admin and is_active and has_write_permission and last_login_within_week:
    allow_edit()

# さらに良い: 意図を表す関数に抽出
def can_edit_content(user: SampleUser) -> bool:
    """ユーザーがコンテンツを編集できるかチェック."""
    is_admin = user.role == "admin"
    is_active = user.is_active
    has_write_permission = "write" in user.permissions
    last_login_within_week = (
        datetime.now() - user.last_login_at < timedelta(days=7)
    )

    return is_admin and is_active and has_write_permission and last_login_within_week

if can_edit_content(user):
    allow_edit()
```

**なぜ悪いのか:**

- 複雑な条件式は読解に時間がかかる
- デバッグが困難
- 再利用できない

**改善方法:**

- 説明変数で式を分割する
- 意味のある名前をつける
- 関数に抽出して再利用可能にする

---

## 第9章: 変数と読みやすさ

**原則:** 変数のスコープを狭く、書き込み回数を減らす。

```python
# ❌ Bad: スコープが広く、変数が何度も書き換えられる
def calculate_total(items: List[Item]) -> float:
    result = 0.0
    temp = 0.0
    i = 0

    for i in range(len(items)):
        temp = items[i].price * items[i].quantity
        result = result + temp

    return result

# ✅ Good: スコープを狭く、不変性を保つ
def calculate_total(items: List[Item]) -> float:
    """商品の合計金額を計算."""
    total = 0.0

    for item in items:
        item_total = item.price * item.quantity
        total += item_total

    return total

# さらに良い: 組み込み関数を使用
def calculate_total(items: List[Item]) -> float:
    """商品の合計金額を計算."""
    return sum(item.price * item.quantity for item in items)
```

**なぜ悪いのか:**

- 変数のスコープが広いと、どこで値が変更されるか追いにくい
- 一時変数が多いとコードの意図が不明確になる

**改善方法:**

- 変数のスコープをできるだけ狭くする
- 不必要な変数の再代入を避ける
- 一時変数は意味のある名前をつける

**Pythonの内包表記を活用:**

```python
# ✅ Good: リスト内包表記
active_users = [user for user in users if user.is_active]

# ✅ Good: 辞書内包表記
user_map = {user.id: user for user in users}

# ✅ Good: ジェネレーター式（メモリ効率）
total = sum(item.price for item in items if item.is_available)
```

---

## 第10章: 無関係の下位問題を抽出

**原則:** プロジェクト固有のコードと汎用的なコードを分離する。

```python
# ❌ Bad: ビジネスロジックと汎用的なユーティリティが混在
async def process_orders(orders: List[Order]) -> None:
    for order in orders:
        # 日付フォーマット処理（汎用的）
        year = order.created_at.year
        month = str(order.created_at.month).zfill(2)
        day = str(order.created_at.day).zfill(2)
        formatted_date = f"{year}-{month}-{day}"

        # ビジネスロジック
        print(f"注文日: {formatted_date}, 合計: {order.total}")

# ✅ Good: 汎用的な処理をユーティリティ関数に抽出
from datetime import datetime

def format_date(date: datetime, format: str = "%Y-%m-%d") -> str:
    """日付を指定フォーマットで文字列化."""
    return date.strftime(format)

async def process_orders(orders: List[Order]) -> None:
    """注文を処理する."""
    for order in orders:
        formatted_date = format_date(order.created_at)
        print(f"注文日: {formatted_date}, 合計: {order.total}")
```

**なぜ悪いのか:**

- ビジネスロジックと汎用処理が混在すると可読性が下がる
- 汎用処理が再利用できない
- テストが困難

**改善方法:**

- 汎用的な処理はユーティリティモジュールに抽出
- プロジェクト固有のロジックと分離
- ユーティリティ関数は`app/core/utils.py`などに配置

```python
# app/core/utils.py
from datetime import datetime
from typing import Optional

def format_datetime(
    dt: datetime,
    format: str = "%Y-%m-%d %H:%M:%S",
    timezone: Optional[str] = None,
) -> str:
    """datetimeを文字列にフォーマット."""
    # 汎用的な処理
    pass

def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式に変換."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
```

---

## 第11章: 一度に1つのことを

**原則:** 関数は1つのことだけを行う。

```python
# ❌ Bad: 複数のことを一度に行う
async def update_user_profile(
    user_id: int,
    data: UpdateData,
    db: AsyncSession,
) -> None:
    # バリデーション
    if "@" not in data.email:
        raise ValueError("無効なメール")

    # データ取得
    user = await db.get(SampleUser, user_id)

    # データ更新
    user.email = data.email
    user.name = data.name

    # 保存
    await db.commit()

    # 通知
    await send_email(user.email, "更新完了")

    # ログ
    logger.info(f"ユーザー {user_id} が更新されました")

# ✅ Good: 1つのことに集中した関数に分割
def validate_email(email: str) -> None:
    """メールアドレスをバリデーション."""
    if "@" not in email:
        raise ValidationError("無効なメールアドレス")

async def update_user(
    user_id: int,
    data: UpdateData,
    db: AsyncSession,
) -> SampleUser:
    """ユーザー情報を更新."""
    user = await db.get(SampleUser, user_id)
    if not user:
        raise NotFoundError("ユーザーが見つかりません")

    user.email = data.email
    user.name = data.name
    await db.commit()
    await db.refresh(user)

    return user

async def notify_user_update(email: str) -> None:
    """ユーザー更新通知を送信."""
    await send_email(email, "更新完了")

async def update_user_profile(
    user_id: int,
    data: UpdateData,
    db: AsyncSession,
) -> None:
    """ユーザープロフィールを更新（オーケストレーション）."""
    validate_email(data.email)

    updated_user = await update_user(user_id, data, db)

    await notify_user_update(updated_user.email)

    logger.info(f"ユーザー {user_id} が更新されました")
```

**なぜ悪いのか:**

- 関数が長く、理解しにくい
- テストが困難
- 再利用できない

**改善方法:**

- 各タスクを個別の関数に分割
- 各関数は1つの責任のみを持つ（単一責任の原則）
- メイン関数は各タスクを組み合わせる（オーケストレーション）

---

## 第12章: コードに思いを込める

**原則:** コードを声に出して説明し、それをコードにする。

```python
# ❌ Bad: 実装の詳細が不明確
def process(items: List[Item]) -> List[Item]:
    return [
        {**item, "processed": True}
        for item in items
        if item["status"] == 1 and item["count"] > 0
    ]

# ✅ Good: 意図を明確に表現
def mark_active_items_with_stock_as_processed(items: List[Item]) -> List[Item]:
    """
    アクティブで在庫のある商品を処理済みにする.

    処理対象:
    - status == 1 (アクティブ)
    - count > 0 (在庫あり)
    """
    ACTIVE_STATUS = 1

    def is_processable(item: Item) -> bool:
        """商品が処理可能かチェック."""
        is_active = item.status == ACTIVE_STATUS
        has_stock = item.count > 0
        return is_active and has_stock

    active_items_with_stock = [item for item in items if is_processable(item)]

    return [
        {**item, "processed": True}
        for item in active_items_with_stock
    ]
```

**なぜ悪いのか:**

- コードの意図が伝わらない
- マジックナンバー（`1`）の意味が不明
- 処理の目的が分からない

**改善方法:**

- 処理を声に出して説明し、その説明を関数名にする
- マジックナンバーを定数に置き換える
- 複雑な条件は説明変数や関数で分割

```python
# ✅ Good: Enumを使用
from enum import Enum

class ItemStatus(Enum):
    """商品ステータス."""
    INACTIVE = 0
    ACTIVE = 1
    ARCHIVED = 2

def is_processable_item(item: Item) -> bool:
    """商品が処理可能かチェック."""
    return item.status == ItemStatus.ACTIVE and item.count > 0
```

---

## 第13章: 短いコードを書く

**原則:** 不要なコードを削除し、標準ライブラリを活用する。

```python
# ❌ Bad: 車輪の再発明
def unique(items: List[str]) -> List[str]:
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result

# ✅ Good: 標準機能を活用
def unique(items: List[str]) -> List[str]:
    """重複を削除してユニークなリストを返す."""
    return list(set(items))

# さらに良い: 順序を保持
def unique_ordered(items: List[str]) -> List[str]:
    """順序を保持しつつ重複を削除."""
    return list(dict.fromkeys(items))

# ❌ Bad: 使われていない機能
def format_user(
    user: SampleUser,
    include_email: bool = False,
    include_phone: bool = False,
    include_address: bool = False,
) -> str:
    # 実際にはinclude_emailしか使われていない
    pass

# ✅ Good: 必要な機能のみ実装（YAGNI原則）
def format_user_with_email(user: SampleUser) -> str:
    """ユーザー情報をメールアドレス付きでフォーマット."""
    return f"{user.name} ({user.email})"
```

**なぜ悪いのか:**

- 既存の標準機能を再実装するとバグの温床になる
- 使われない機能はメンテナンスコストを増やす

**改善方法:**

- 標準ライブラリやよく使われるライブラリを活用
- 必要になってから実装する（YAGNI原則）
- 不要なコードは削除する

**Python標準ライブラリの活用:**

```python
# ✅ Good: collectionsモジュール
from collections import defaultdict, Counter

# デフォルト値付き辞書
user_counts = defaultdict(int)
user_counts["user1"] += 1

# 要素のカウント
word_counts = Counter(words)

# ✅ Good: itertoolsモジュール
from itertools import groupby, chain

# グループ化
grouped = groupby(sorted_items, key=lambda x: x.category)

# 複数のイテラブルを結合
all_items = list(chain(list1, list2, list3))
```

---

## 第14章: テストと読みやすさ

**原則:** テストは読みやすく、保守しやすくする。

```python
# ❌ Bad: テストの意図が不明確
def test_user():
    u = {"id": 1, "name": "Test", "is_active": True}
    r = process_user(u)
    assert r == True

# ✅ Good: テストの意図が明確（AAA pattern）
async def test_process_user_with_active_user():
    """アクティブなユーザーは処理が成功する."""
    # Arrange（準備）
    active_user = User(
        id=1,
        name="Test User",
        email="test@example.com",
        is_active=True,
    )

    # Act（実行）
    result = await process_user(active_user)

    # Assert（検証）
    assert result is True

async def test_process_user_with_inactive_user():
    """非アクティブなユーザーは処理が失敗する."""
    # Arrange
    inactive_user = User(
        id=2,
        name="Inactive User",
        email="inactive@example.com",
        is_active=False,
    )

    # Act
    result = await process_user(inactive_user)

    # Assert
    assert result is False

# ✅ Good: パラメータ化テスト
import pytest

@pytest.mark.parametrize(
    "is_active,expected_result",
    [
        (True, True),
        (False, False),
    ],
)
async def test_process_user_by_status(
    is_active: bool,
    expected_result: bool,
):
    """ユーザーのステータスに応じた処理結果を検証."""
    # Arrange
    user = User(
        id=1,
        name="Test User",
        email="test@example.com",
        is_active=is_active,
    )

    # Act
    result = await process_user(user)

    # Assert
    assert result == expected_result
```

**なぜ悪いのか:**

- テストの意図が分からない
- 失敗時に原因が特定しにくい
- メンテナンスが困難

**改善方法:**

- テスト名は「何をテストするか」を明確に（日本語でも可）
- AAA パターン（Arrange-Act-Assert）を使う
- 1つのテストで1つのことをテスト
- パラメータ化テストで重複を減らす

```python
# ✅ Good: フィクスチャを活用
import pytest

@pytest.fixture
def sample_user() -> SampleUser:
    """テスト用のサンプルユーザー."""
    return User(
        id=1,
        name="Test User",
        email="test@example.com",
        is_active=True,
    )

async def test_get_user_success(sample_user: SampleUser):
    """ユーザーの取得に成功する."""
    # フィクスチャを使用して準備を簡潔に
    result = await get_user(sample_user.id)

    assert result.id == sample_user.id
    assert result.email == sample_user.email
```

---

## まとめ

リーダブルコードの14の原則をPython/FastAPIに適用することで、以下が実現できます：

1. **理解しやすいコード** - 明確な命名と型ヒント
2. **保守しやすいコード** - 適切な抽象化と関数分割
3. **テストしやすいコード** - 単一責任の原則
4. **バグの少ないコード** - 早期リターンと明確な制御フロー

## 関連リンク

- [基本原則](./01-basic-principles.md) - 型安全性と単一責任
- [設計原則](./02-design-principles.md) - SOLID、DRY、KISS、YAGNI
- [命名規則](./04-naming-conventions.md) - 命名のガイドライン
- [Python規約](./05-python-rules.md) - PEP 8、型ヒント
- [FastAPI規約](./06-fastapi-rules.md) - エンドポイント、依存性注入
- [リーダブルコード（書籍）](https://www.oreilly.co.jp/books/9784873115658/)

---

次のセクション: [04-naming-conventions.md](./04-naming-conventions.md)
