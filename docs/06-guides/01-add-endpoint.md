# 新しいエンドポイントの追加

このガイドでは、バックエンドAPIに新しいエンドポイントを追加する手順を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [ステップバイステップ](#ステップバイステップ)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)
- [参考リンク](#参考リンク)

## 概要

新しいエンドポイントを追加する際は、以下のコンポーネントを作成・修正する必要があります：

1. **Pydanticスキーマ** - リクエスト/レスポンスのバリデーション
2. **サービスクラス** - ビジネスロジックの実装
3. **APIルート** - エンドポイントの定義
4. **依存性注入** - サービスの注入設定
5. **ルーターの登録** - main.pyへの登録

## 前提条件

- プロジェクト構造の理解
- FastAPIの基礎知識
- Pydanticスキーマの理解
- 依存性注入（Dependency Injection）の理解

## ステップバイステップ

### 例: 商品（Product）管理エンドポイントの追加

この例では、商品を管理するためのCRUDエンドポイントを追加します。

### ステップ 1: Pydanticスキーマの作成

`src/app/schemas/product.py`を作成：

```python
"""商品関連のPydanticスキーマ。"""

from datetime import datetime
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """ベース商品スキーマ。"""

    name: str = Field(..., min_length=1, max_length=200, description="商品名")
    description: str | None = Field(None, max_length=1000, description="商品説明")
    price: float = Field(..., gt=0, description="商品価格")
    stock: int = Field(0, ge=0, description="在庫数")


class ProductCreate(ProductBase):
    """商品作成リクエストスキーマ。"""

    pass


class ProductUpdate(BaseModel):
    """商品更新リクエストスキーマ。"""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    price: float | None = Field(None, gt=0)
    stock: int | None = Field(None, ge=0)


class ProductResponse(ProductBase):
    """商品レスポンススキーマ。"""

    id: int = Field(..., description="商品ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        """Pydantic設定。"""

        from_attributes = True


class ProductListResponse(BaseModel):
    """商品リストレスポンススキーマ。"""

    products: list[ProductResponse] = Field(..., description="商品リスト")
    total: int = Field(..., description="総商品数")
```

**ポイント:**
- `BaseModel`を継承してスキーマを定義
- `Field`でバリデーションルールと説明を追加
- Create/Update/Responseで分ける（責務の分離）
- `from_attributes = True`でORMモデルからの変換を有効化

### ステップ 2: サービスクラスの作成

既にモデルとリポジトリがある場合、`src/app/services/product.py`を作成：

```python
"""商品ビジネスロジック用サービス。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """商品関連のビジネスロジック用サービス。"""

    def __init__(self, db: AsyncSession):
        """商品サービスを初期化します。

        Args:
            db: データベースセッション
        """
        self.repository = ProductRepository(db)

    async def create_product(self, product_data: ProductCreate) -> Product:
        """新しい商品を作成します。

        Args:
            product_data: 商品作成データ

        Returns:
            作成された商品インスタンス

        Raises:
            ValidationError: データが無効な場合
        """
        # ビジネスロジックの検証
        if product_data.price < 0:
            raise ValidationError("Price must be positive")

        # リポジトリを使って作成
        product = await self.repository.create(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            stock=product_data.stock,
        )
        return product

    async def get_product(self, product_id: int) -> Product:
        """IDで商品を取得します。

        Args:
            product_id: 商品ID

        Returns:
            商品インスタンス

        Raises:
            NotFoundError: 商品が見つからない場合
        """
        product = await self.repository.get(product_id)
        if not product:
            raise NotFoundError(
                "Product not found",
                details={"product_id": product_id}
            )
        return product

    async def list_products(
        self, skip: int = 0, limit: int = 100
    ) -> list[Product]:
        """商品リストを取得します。

        Args:
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            商品のリスト
        """
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def update_product(
        self, product_id: int, product_data: ProductUpdate
    ) -> Product:
        """商品を更新します。

        Args:
            product_id: 商品ID
            product_data: 更新データ

        Returns:
            更新された商品インスタンス

        Raises:
            NotFoundError: 商品が見つからない場合
        """
        product = await self.get_product(product_id)

        # Noneでない値のみを更新
        update_data = product_data.model_dump(exclude_unset=True)
        if update_data:
            product = await self.repository.update(product, **update_data)

        return product

    async def delete_product(self, product_id: int) -> bool:
        """商品を削除します。

        Args:
            product_id: 商品ID

        Returns:
            削除された場合はTrue

        Raises:
            NotFoundError: 商品が見つからない場合
        """
        product = await self.get_product(product_id)
        await self.repository.delete(product.id)
        return True

    async def count_products(self) -> int:
        """商品の総数を取得します。

        Returns:
            商品の総数
        """
        return await self.repository.count()
```

**ポイント:**
- ビジネスロジックをサービス層に集約
- カスタム例外（NotFoundError、ValidationError）を使用
- リポジトリパターンでデータアクセスを分離
- エラー処理を適切に実装

### ステップ 3: 依存性注入の設定

`src/app/api/dependencies.py`に追加：

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.product import ProductService

# 既存のコード...


async def get_product_service(
    db: AsyncSession = Depends(get_db),
) -> ProductService:
    """商品サービスの依存性を提供します。

    Args:
        db: データベースセッション

    Returns:
        ProductServiceインスタンス
    """
    return ProductService(db)


# Type alias for dependency injection
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
```

**ポイント:**
- `Annotated`を使用して型安全な依存性注入
- `get_db`依存性を注入してサービスを作成
- 再利用可能な型エイリアスを定義

### ステップ 4: APIルートの作成

`src/app/api/routes/products.py`を作成：

```python
"""商品APIルート。"""

from fastapi import APIRouter, Query, status

from app.api.dependencies import ProductServiceDep
from app.schemas.common import MessageResponse
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="商品を作成",
    description="新しい商品を作成します。",
)
async def create_product(
    product_data: ProductCreate,
    product_service: ProductServiceDep,
) -> ProductResponse:
    """
    新しい商品を作成します。

    Args:
        product_data: 商品作成データ
        product_service: 商品サービスインスタンス

    Returns:
        作成された商品情報
    """
    product = await product_service.create_product(product_data)
    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="商品を取得",
    description="IDで商品を取得します。",
)
async def get_product(
    product_id: int,
    product_service: ProductServiceDep,
) -> ProductResponse:
    """
    IDで商品を取得します。

    Args:
        product_id: 商品ID
        product_service: 商品サービスインスタンス

    Returns:
        商品情報
    """
    product = await product_service.get_product(product_id)
    return ProductResponse.model_validate(product)


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="商品リストを取得",
    description="ページネーション付きで商品リストを取得します。",
)
async def list_products(
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
    product_service: ProductServiceDep = None,
) -> ProductListResponse:
    """
    商品リストを取得します。

    Args:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        product_service: 商品サービスインスタンス

    Returns:
        商品リストと総数
    """
    products = await product_service.list_products(skip=skip, limit=limit)
    total = await product_service.count_products()

    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="商品を更新",
    description="既存の商品を更新します。",
)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    product_service: ProductServiceDep,
) -> ProductResponse:
    """
    既存の商品を更新します。

    Args:
        product_id: 商品ID
        product_data: 更新データ
        product_service: 商品サービスインスタンス

    Returns:
        更新された商品情報
    """
    product = await product_service.update_product(product_id, product_data)
    return ProductResponse.model_validate(product)


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="商品を削除",
    description="商品を削除します。",
)
async def delete_product(
    product_id: int,
    product_service: ProductServiceDep,
) -> MessageResponse:
    """
    商品を削除します。

    Args:
        product_id: 商品ID
        product_service: 商品サービスインスタンス

    Returns:
        成功メッセージ
    """
    await product_service.delete_product(product_id)
    return MessageResponse(message=f"Product {product_id} deleted successfully")
```

**ポイント:**
- RESTful APIの命名規則に従う
- 適切なHTTPステータスコードを使用
- `Query`でクエリパラメータのバリデーション
- 詳細なdocstringとOpenAPI用のメタデータ
- 型ヒントを完全に使用

### ステップ 5: ルーターの登録

`src/app/main.py`を更新：

```python
from app.api.routes import agents, files, products  # 追加

# 既存のコード...

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(products.router, prefix="/api/products", tags=["products"])  # 追加
```

**ポイント:**
- `prefix`でAPIバージョニングとグループ化
- `tags`でOpenAPIドキュメントのグループ化

### ステップ 6: テストの作成

`tests/api/test_products.py`を作成：

```python
"""商品APIのテスト。"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    """商品作成のテスト。"""
    response = await client.post(
        "/api/products/",
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "stock": 10,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 99.99


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, db: AsyncSession):
    """商品取得のテスト。"""
    # Create test product
    from app.repositories.product import ProductRepository

    repo = ProductRepository(db)
    product = await repo.create(
        name="Test Product",
        description="Test",
        price=99.99,
        stock=10,
    )
    await db.commit()

    # Get product
    response = await client.get(f"/api/products/{product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product.id
    assert data["name"] == "Test Product"


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    """商品リスト取得のテスト。"""
    response = await client.get("/api/products/")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, db: AsyncSession):
    """商品更新のテスト。"""
    # Create test product
    from app.repositories.product import ProductRepository

    repo = ProductRepository(db)
    product = await repo.create(
        name="Test Product",
        price=99.99,
        stock=10,
    )
    await db.commit()

    # Update product
    response = await client.patch(
        f"/api/products/{product.id}",
        json={"price": 149.99},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 149.99


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, db: AsyncSession):
    """商品削除のテスト。"""
    # Create test product
    from app.repositories.product import ProductRepository

    repo = ProductRepository(db)
    product = await repo.create(
        name="Test Product",
        price=99.99,
        stock=10,
    )
    await db.commit()

    # Delete product
    response = await client.delete(f"/api/products/{product.id}")
    assert response.status_code == 200

    # Verify deletion
    response = await client.get(f"/api/products/{product.id}")
    assert response.status_code == 404
```

## チェックリスト

エンドポイント追加時のチェックリスト：

- [ ] Pydanticスキーマを作成（Create/Update/Response）
- [ ] サービスクラスを作成・更新
- [ ] 依存性注入を設定（dependencies.py）
- [ ] APIルートを作成
- [ ] 適切なHTTPメソッドとステータスコードを使用
- [ ] バリデーションとエラー処理を実装
- [ ] ルーターをmain.pyに登録
- [ ] 詳細なdocstringを追加
- [ ] 型ヒントを完全に使用
- [ ] ユニットテストを作成
- [ ] 統合テストを作成
- [ ] OpenAPIドキュメント（/docs）で確認
- [ ] 手動テストを実施

## よくある落とし穴

### 1. スキーマの検証不足

```python
# 悪い例
class ProductCreate(BaseModel):
    name: str
    price: float  # 負の値を許可してしまう

# 良い例
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0, description="Must be positive")
```

### 2. エラー処理の不足

```python
# 悪い例
async def get_product(product_id: int):
    product = await repository.get(product_id)
    return product  # Noneが返る可能性

# 良い例
async def get_product(product_id: int):
    product = await repository.get(product_id)
    if not product:
        raise NotFoundError(f"Product {product_id} not found")
    return product
```

### 3. ルーターの登録忘れ

```python
# main.pyへの登録を忘れずに！
app.include_router(products.router, prefix="/api/products", tags=["products"])
```

### 4. 依存性注入の型アノテーション

```python
# 悪い例
async def create_product(
    product_data: ProductCreate,
    product_service,  # 型ヒントなし
):
    pass

# 良い例
async def create_product(
    product_data: ProductCreate,
    product_service: ProductServiceDep,
):
    pass
```

### 5. レスポンスモデルの指定忘れ

```python
# 悪い例
@router.get("/{product_id}")
async def get_product(product_id: int):
    pass

# 良い例
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int) -> ProductResponse:
    pass
```

## ベストプラクティス

### 1. RESTful API設計

```python
# 良い命名規則
POST   /api/products/          # 作成
GET    /api/products/{id}      # 取得
GET    /api/products/          # リスト
PATCH  /api/products/{id}      # 部分更新
PUT    /api/products/{id}      # 完全更新
DELETE /api/products/{id}      # 削除
```

### 2. 適切なステータスコード

```python
@router.post("/", status_code=status.HTTP_201_CREATED)  # 作成時は201
@router.get("/")  # 取得は200（デフォルト）
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)  # 削除は204も可
```

### 3. バリデーションの層別化

```python
# Pydanticスキーマ: 基本的なバリデーション
class ProductCreate(BaseModel):
    price: float = Field(..., gt=0)

# サービス層: ビジネスロジックのバリデーション
async def create_product(self, data: ProductCreate):
    if data.price > 10000:
        raise ValidationError("Price too high for new products")
```

### 4. ドキュメンテーション

```python
@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="商品を作成",  # 短い要約
    description="新しい商品を作成します。在庫は0以上である必要があります。",  # 詳細な説明
    response_description="作成された商品情報",  # レスポンスの説明
)
async def create_product(...):
    """
    詳細なdocstring。

    Args:
        product_data: 商品作成データ
        product_service: 商品サービスインスタンス

    Returns:
        作成された商品情報

    Raises:
        ValidationError: データが無効な場合
    """
```

### 5. 依存性の再利用

```python
# 共通の依存性を型エイリアスで定義
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

# 複数のエンドポイントで再利用
@router.post("/")
async def create_product(
    product_service: ProductServiceDep,
    current_user: CurrentUserDep,
):
    pass
```

## 参考リンク

### 公式ドキュメント

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)
- [FastAPI Path Operations](https://fastapi.tiangolo.com/tutorial/path-params/)
- [HTTP Status Codes](https://fastapi.tiangolo.com/tutorial/response-status-code/)

### プロジェクト内リンク

- [アーキテクチャ概要](../02-architecture/01-overview.md)
- [依存性注入パターン](../03-core-concepts/02-dependency-injection.md)
- [エラーハンドリング](../03-core-concepts/04-error-handling.md)
- [テスト作成ガイド](../05-testing/01-unit-testing.md)

### 関連ガイド

- [新しいモデル追加](./02-add-model.md)
- [新しい機能モジュール追加](./03-add-feature.md)
