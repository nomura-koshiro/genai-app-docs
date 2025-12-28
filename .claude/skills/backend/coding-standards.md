# コーディング規約

## 基本原則

- **型安全性**: すべての関数に型ヒントを付与
- **単一責任**: 1つの関数/クラスは1つの責務
- **DRY**: コードの重複を排除
- **KISS**: シンプルな設計を維持

## 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| ファイル | snake_case | `user_service.py` |
| クラス | PascalCase | `UserService` |
| 関数・変数 | snake_case | `get_user`, `user_name` |
| 定数 | UPPER_SNAKE_CASE | `API_VERSION` |
| プライベート | _prefix | `_internal_method` |

## Python規約

### 型ヒント

```python
from typing import Optional, List
from pydantic import BaseModel

def get_user(user_id: int) -> Optional[User]:
    """ユーザーをIDで取得"""
    ...

def get_users(skip: int = 0, limit: int = 100) -> List[User]:
    """ユーザー一覧を取得"""
    ...
```

### Pydanticスキーマ

```python
from pydantic import BaseModel, Field, ConfigDict

class UserBase(BaseModel):
    """ユーザー基本スキーマ"""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., description="メールアドレス")

class UserCreate(UserBase):
    """ユーザー作成スキーマ"""
    password: str = Field(..., min_length=8)

class User(UserBase):
    """ユーザーレスポンススキーマ"""
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### SQLAlchemyモデル

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class User(Base):
    """ユーザーモデル"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    posts = relationship("Post", back_populates="author")
```

## FastAPI規約

### エンドポイント

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps

router = APIRouter()

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Item:
    """
    アイテムを取得

    - **item_id**: アイテムID
    """
    item = item_service.get(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item
```

### エラーハンドリング

```python
from fastapi import HTTPException, status

# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# 400 Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid input data"
)

# 403 Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions"
)
```

## ツール設定

```bash
# リント実行
ruff check app/ --fix

# フォーマット
ruff format app/

# 型チェック
mypy app/ --strict

# セキュリティチェック
bandit -r app/
```

## ドキュメント参照

詳細は以下のドキュメントを参照：

- [基本原則](docs/developer-guide/04-development/01-coding-standards/01-basic-principles.md)
- [設計原則](docs/developer-guide/04-development/01-coding-standards/02-design-principles.md)
- [リーダブルコード](docs/developer-guide/04-development/01-coding-standards/03-readable-code.md)
- [命名規則](docs/developer-guide/04-development/01-coding-standards/04-naming-conventions.md)
- [Python規約](docs/developer-guide/04-development/01-coding-standards/05-python-rules.md)
- [FastAPI規約](docs/developer-guide/04-development/01-coding-standards/06-fastapi-rules.md)
