# 新しいモデルの追加

このガイドでは、データベースに新しいモデル（テーブル）を追加する手順を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [ステップバイステップ](#ステップバイステップ)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)
- [参考リンク](#参考リンク)

## 概要

新しいモデルを追加する際は、以下の作業が必要です：

1. **SQLAlchemyモデル** - データベーステーブルの定義
2. **Alembicマイグレーション** - データベーススキーマの変更
3. **リポジトリクラス** - データアクセス層の実装
4. **Pydanticスキーマ** - API用のバリデーションスキーマ
5. **インデックスと制約** - パフォーマンスとデータ整合性

## 前提条件

- SQLAlchemyの基礎知識
- Alembicマイグレーションツールの理解
- リレーショナルデータベースの基礎
- Pythonの型ヒントの理解

## ステップバイステップ

### 例: 商品（Product）モデルの追加

### ステップ 1: SQLAlchemyモデルの作成

`src/app/models/product.py`を作成：

```python
"""商品モデル。"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.category import Category


class Product(Base):
    """商品データベースモデル。"""

    __tablename__ = "products"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic fields
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="商品名",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="商品説明",
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="価格",
    )
    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="在庫数",
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="商品コード",
    )

    # Foreign keys
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        # ForeignKeyは後で追加（カテゴリモデル作成後）
        nullable=True,
        comment="カテゴリID",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="作成日時",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新日時",
    )

    # Relationships
    # category: Mapped["Category"] = relationship(
    #     "Category",
    #     back_populates="products",
    # )

    def __repr__(self) -> str:
        """文字列表現。"""
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"

    def __str__(self) -> str:
        """文字列表現（ユーザー向け）。"""
        return f"{self.name} (¥{self.price})"
```

**ポイント:**

- `Mapped[型]`を使用した型安全なカラム定義
- `mapped_column()`でカラムオプションを指定
- `nullable`、`unique`、`index`などの制約を適切に設定
- `comment`でカラムの説明を追加（データベースレベル）
- タイムゾーン対応の`DateTime(timezone=True)`
- `__repr__`と`__str__`で可読性向上

### ステップ 2: モデルのインポート設定

`src/app/models/__init__.py`を更新：

```python
"""モデルパッケージ。"""

from app.models.file import File
from app.models.message import Message
from app.models.product import Product  # 追加
from app.models.session import Session
from app.models.user import User

__all__ = [
    "File",
    "Message",
    "Product",  # 追加
    "Session",
    "User",
]
```

**重要:** Alembicが自動的にモデルを検出できるように、`__init__.py`にインポートを追加します。

### ステップ 3: Alembicマイグレーションの生成

#### 3.1 マイグレーションファイルを自動生成

```bash
# 開発環境でマイグレーションを生成
alembic revision --autogenerate -m "add_product_table"
```

これにより、`alembic/versions/xxxx_add_product_table.py`が生成されます。

#### 3.2 生成されたマイグレーションを確認・編集

```python
"""add_product_table

Revision ID: xxxx
Revises: yyyy
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "xxxx"
down_revision: Union[str, None] = "yyyy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """テーブルを作成します。"""
    # Productsテーブル作成
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, comment="商品名"),
        sa.Column("description", sa.Text(), nullable=True, comment="商品説明"),
        sa.Column("price", sa.Float(), nullable=False, comment="価格"),
        sa.Column("stock", sa.Integer(), nullable=False, comment="在庫数"),
        sa.Column("sku", sa.String(length=100), nullable=False, comment="商品コード"),
        sa.Column("category_id", sa.Integer(), nullable=True, comment="カテゴリID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="更新日時",
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="商品テーブル",
    )

    # インデックス作成
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)

    # 複合インデックス（必要に応じて）
    op.create_index(
        "ix_products_category_price",
        "products",
        ["category_id", "price"],
        unique=False,
    )


def downgrade() -> None:
    """テーブルを削除します。"""
    # インデックス削除
    op.drop_index("ix_products_category_price", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_id", table_name="products")

    # テーブル削除
    op.drop_table("products")
```

**ポイント:**
- `upgrade()`と`downgrade()`の両方を実装
- インデックスを適切に作成
- コメントを追加してドキュメント化

#### 3.3 マイグレーションを適用

```bash
# マイグレーションを適用
alembic upgrade head

# 確認
alembic current
```

#### 3.4 ロールバックのテスト

```bash
# 1つ前に戻す
alembic downgrade -1

# 再度適用
alembic upgrade head
```

### ステップ 4: リポジトリクラスの作成

`src/app/repositories/product.py`を作成：

```python
"""商品リポジトリ。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """商品データアクセス用リポジトリ。"""

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: データベースセッション
        """
        super().__init__(Product, db)

    async def get_by_sku(self, sku: str) -> Product | None:
        """SKUで商品を取得します。

        Args:
            sku: 商品コード

        Returns:
            商品インスタンス、見つからない場合はNone
        """
        query = select(Product).where(Product.sku == sku)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """カテゴリIDで商品を取得します。

        Args:
            category_id: カテゴリID
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            商品のリスト
        """
        query = (
            select(Product)
            .where(Product.category_id == category_id)
            .offset(skip)
            .limit(limit)
            .order_by(Product.name)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_low_stock(
        self,
        threshold: int = 10,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """在庫が少ない商品を取得します。

        Args:
            threshold: 在庫閾値
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            在庫が少ない商品のリスト
        """
        query = (
            select(Product)
            .where(Product.stock <= threshold)
            .offset(skip)
            .limit(limit)
            .order_by(Product.stock)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_by_name(
        self,
        name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """名前で商品を検索します（部分一致）。

        Args:
            name: 検索する名前
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            検索結果の商品リスト
        """
        query = (
            select(Product)
            .where(Product.name.ilike(f"%{name}%"))
            .offset(skip)
            .limit(limit)
            .order_by(Product.name)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_stock(
        self,
        product_id: int,
        quantity: int,
    ) -> Product | None:
        """在庫を更新します。

        Args:
            product_id: 商品ID
            quantity: 増減する数量（負の値で減少）

        Returns:
            更新された商品、見つからない場合はNone
        """
        product = await self.get(product_id)
        if product:
            product.stock += quantity
            await self.db.flush()
            await self.db.refresh(product)
        return product
```

**ポイント:**
- `BaseRepository`を継承して基本的なCRUD操作を継承
- モデル固有のクエリメソッドを追加
- 適切な型ヒントを使用
- `ilike`で大文字小文字を区別しない検索

### ステップ 5: リポジトリのインポート設定

`src/app/repositories/__init__.py`を更新：

```python
"""リポジトリパッケージ。"""

from app.repositories.base import BaseRepository
from app.repositories.file import FileRepository
from app.repositories.product import ProductRepository  # 追加
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "FileRepository",
    "ProductRepository",  # 追加
    "SessionRepository",
    "UserRepository",
]
```

### ステップ 6: リレーションシップの追加（オプション）

他のモデルとの関連を追加する場合：

#### 6.1 外部キー制約の追加

```python
# src/app/models/product.py

from sqlalchemy import ForeignKey

class Product(Base):
    # ...
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),  # 追加
        nullable=True,
    )
```

#### 6.2 リレーションシップの定義

```python
# src/app/models/product.py

class Product(Base):
    # ...
    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
        lazy="selectin",  # N+1問題を回避
    )
```

```python
# src/app/models/category.py

class Category(Base):
    # ...
    # Relationships
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
    )
```

#### 6.3 マイグレーションの追加

```bash
# 外部キー制約を追加するマイグレーション
alembic revision --autogenerate -m "add_product_category_fk"
alembic upgrade head
```

## チェックリスト

モデル追加時のチェックリスト：

- [ ] SQLAlchemyモデルを作成
- [ ] `models/__init__.py`にインポート追加
- [ ] 適切な型ヒント（`Mapped[型]`）を使用
- [ ] Primary keyを定義
- [ ] 必要なインデックスを追加
- [ ] 制約（unique、nullable）を設定
- [ ] タイムスタンプフィールドを追加
- [ ] `__repr__`と`__str__`を実装
- [ ] Alembicマイグレーションを生成
- [ ] マイグレーションの内容を確認・編集
- [ ] `upgrade()`と`downgrade()`の両方を実装
- [ ] マイグレーションを適用（`alembic upgrade head`）
- [ ] ロールバックをテスト（`alembic downgrade -1`）
- [ ] リポジトリクラスを作成
- [ ] `repositories/__init__.py`にインポート追加
- [ ] モデル固有のクエリメソッドを実装
- [ ] リレーションシップを定義（必要な場合）
- [ ] Pydanticスキーマを作成（API用）
- [ ] ユニットテストを作成

## よくある落とし穴

### 1. マイグレーションの生成前にインポート忘れ

```python
# models/__init__.py にインポートを追加しないと、
# Alembicがモデルを検出できない

# 悪い例（インポートなし）
# product.pyファイルだけ作成

# 良い例
from app.models.product import Product

__all__ = ["Product", ...]
```

### 2. 型ヒントの誤り

```python
# 悪い例
name: Mapped[str] = mapped_column(nullable=True)  # strは常にNone不可

# 良い例
name: Mapped[str | None] = mapped_column(nullable=True)
```

### 3. インデックスの不足

```python
# 悪い例（頻繁に検索されるカラムにインデックスなし）
email: Mapped[str] = mapped_column(String(255))

# 良い例
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
```

### 4. タイムゾーン対応忘れ

```python
# 悪い例
created_at: Mapped[datetime] = mapped_column(DateTime)

# 良い例
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
)
```

### 5. downgrade()の実装忘れ

```python
def downgrade() -> None:
    """必ず実装する！"""
    op.drop_table("products")
    # インデックスやFKも削除
```

### 6. N+1問題

```python
# 悪い例（N+1問題が発生）
products = await repo.get_multi()
for product in products:
    print(product.category.name)  # 各productごとにクエリ実行

# 良い例
# リレーションシップでlazy="selectin"を使用
category: Mapped["Category"] = relationship(
    "Category",
    lazy="selectin",  # joinedloadを使用
)
```

## ベストプラクティス

### 1. カラム定義のパターン

```python
class Product(Base):
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 必須フィールド
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # オプショナルフィールド
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # デフォルト値付き
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ユニーク制約
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    # 外部キー
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
```

### 2. マイグレーション命名規則

```bash
# 良い命名例
alembic revision --autogenerate -m "add_product_table"
alembic revision --autogenerate -m "add_product_category_fk"
alembic revision --autogenerate -m "add_product_sku_unique_index"
alembic revision --autogenerate -m "remove_product_old_field"
```

### 3. インデックス戦略

```python
# 単一カラムインデックス（検索頻度が高い）
name: Mapped[str] = mapped_column(String(200), index=True)

# ユニークインデックス
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

# 複合インデックス（マイグレーションで定義）
op.create_index(
    "ix_products_category_price",
    "products",
    ["category_id", "price"],  # よく一緒に検索される
)
```

### 4. カスケード設定

```python
# 親が削除されたら子も削除
user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE")
)

# 親が削除されたらNULLに設定
category_id: Mapped[int | None] = mapped_column(
    ForeignKey("categories.id", ondelete="SET NULL"),
    nullable=True,
)

# 親の削除を制限
user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="RESTRICT")
)
```

### 5. リポジトリメソッドのパターン

```python
class ProductRepository(BaseRepository[Product]):
    # 単一取得
    async def get_by_sku(self, sku: str) -> Product | None:
        pass

    # リスト取得
    async def get_by_category(self, category_id: int) -> list[Product]:
        pass

    # カウント
    async def count_by_category(self, category_id: int) -> int:
        pass

    # 検索
    async def search(self, query: str) -> list[Product]:
        pass

    # 更新
    async def update_stock(self, product_id: int, quantity: int) -> Product:
        pass
```

### 6. マイグレーションのテスト

```bash
# 開発環境でテスト
alembic upgrade head    # 最新に更新
alembic downgrade -1    # 1つ戻す
alembic upgrade +1      # 1つ進める
alembic current         # 現在のバージョン確認
alembic history         # 履歴確認
```

## 参考リンク

### 公式ドキュメント

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy Mapped Column](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

### プロジェクト内リンク

- [データベース設定](../03-core-concepts/01-database.md)
- [リポジトリパターン](../02-architecture/03-data-access.md)
- [マイグレーション管理](../04-development/03-migrations.md)

### 関連ガイド

- [新しいエンドポイント追加](./01-add-endpoint.md)
- [新しい機能モジュール追加](./03-add-feature.md)
