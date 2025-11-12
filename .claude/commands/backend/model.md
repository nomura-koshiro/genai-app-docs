---
title: Create Database Model
description: 適切なリレーションと制約を持つSQLAlchemyモデルを作成
tools: [Write, Edit, MultiEdit, Bash]
---

@backend-developer

新しいデータベースモデル「$ARGUMENTS」を作成してください。

## SQLAlchemy モデル作成要件

### 1. ファイル構成

```
apps/backend/app/
├── models/
│   └── $ARGUMENTS.py          # SQLAlchemy モデル
├── schemas/
│   └── $ARGUMENTS.py          # Pydantic スキーマ
├── crud/
│   └── crud_$ARGUMENTS.py     # CRUD操作
├── alembic/versions/
│   └── xxxx_create_$ARGUMENTS_table.py  # マイグレーション
└── tests/
    └── crud/test_crud_$ARGUMENTS.py      # CRUDテスト
```

### 2. SQLAlchemy モデル実装 (`models/$ARGUMENTS.py`)

#### 基本構造

```python
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class $ARGUMENTS(Base):
    """
    $ARGUMENTS モデル

    Attributes:
        id: 主キー
        # その他属性の説明
    """
    __tablename__ = "$ARGUMENTS"

    # 主キー
    id = Column(Integer, primary_key=True, index=True)

    # 必須フィールド
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 状態管理
    is_active = Column(Boolean, default=True, nullable=False)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 外部キー（必要に応じて）
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # リレーションシップ（必要に応じて）
    # user = relationship("User", back_populates="$ARGUMENTS")

    def __repr__(self) -> str:
        return f"<$ARGUMENTS(id={self.id}, name='{self.name}')>"
```

### 3. Pydantic スキーマ実装 (`schemas/$ARGUMENTS.py`)

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# 共通フィールド
class $ARGUMENTSBase(BaseModel):
    """$ARGUMENTS 基本スキーマ"""
    name: str = Field(..., min_length=1, max_length=255, description="$ARGUMENTS名")
    description: Optional[str] = Field(None, max_length=1000, description="説明")
    is_active: bool = Field(True, description="アクティブ状態")

# 作成時スキーマ
class $ARGUMENTSCreate($ARGUMENTSBase):
    """$ARGUMENTS 作成スキーマ"""
    pass

# 更新時スキーマ
class $ARGUMENTSUpdate(BaseModel):
    """$ARGUMENTS 更新スキーマ"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

# データベースから読み込む際のスキーマ
class $ARGUMENTSInDBBase($ARGUMENTSBase):
    """$ARGUMENTS データベース基本スキーマ"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# APIレスポンス用スキーマ
class $ARGUMENTS($ARGUMENTSInDBBase):
    """$ARGUMENTS レスポンススキーマ"""
    pass

# データベース内部用スキーマ
class $ARGUMENTSInDB($ARGUMENTSInDBBase):
    """$ARGUMENTS データベーススキーマ"""
    pass
```

### 4. CRUD操作実装 (`crud/crud_$ARGUMENTS.py`)

```python
from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.$ARGUMENTS import $ARGUMENTS
from app.schemas.$ARGUMENTS import $ARGUMENTSCreate, $ARGUMENTSUpdate

class CRUD$ARGUMENTS(CRUDBase[$ARGUMENTS, $ARGUMENTSCreate, $ARGUMENTSUpdate]):
    """$ARGUMENTS のCRUD操作"""

    def get_by_name(self, db: Session, *, name: str) -> Optional[$ARGUMENTS]:
        """名前による$ARGUMENTS取得"""
        return db.query(self.model).filter(self.model.name == name).first()

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[$ARGUMENTS]:
        """アクティブな$ARGUMENTSの取得"""
        return (
            db.query(self.model)
            .filter(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_name(self, db: Session, *, query: str, skip: int = 0, limit: int = 100) -> List[$ARGUMENTS]:
        """名前による$ARGUMENTS検索"""
        return (
            db.query(self.model)
            .filter(self.model.name.ilike(f"%{query}%"))
            .filter(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

$ARGUMENTS = CRUD$ARGUMENTS($ARGUMENTS)
```

### 5. マイグレーション作成

```bash
# マイグレーションファイル生成
cd apps/backend && alembic revision --autogenerate -m "Create $ARGUMENTS table"

# マイグレーション実行
cd apps/backend && alembic upgrade head
```

### 6. テスト実装 (`tests/crud/test_crud_$ARGUMENTS.py`)

```python
import pytest
from sqlalchemy.orm import Session

from app.crud.crud_$ARGUMENTS import $ARGUMENTS
from app.schemas.$ARGUMENTS import $ARGUMENTSCreate, $ARGUMENTSUpdate
from app.tests.utils.utils import random_lower_string

def test_create_$ARGUMENTS(db: Session) -> None:
    """$ARGUMENTS作成テスト"""
    name = random_lower_string()
    description = random_lower_string()
    $ARGUMENTS_in = $ARGUMENTSCreate(name=name, description=description)
    $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)

    assert $ARGUMENTS_obj.name == name
    assert $ARGUMENTS_obj.description == description
    assert $ARGUMENTS_obj.is_active is True

def test_get_$ARGUMENTS(db: Session) -> None:
    """$ARGUMENTS取得テスト"""
    name = random_lower_string()
    $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
    $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)

    stored_$ARGUMENTS = $ARGUMENTS.get(db=db, id=$ARGUMENTS_obj.id)
    assert stored_$ARGUMENTS
    assert stored_$ARGUMENTS.id == $ARGUMENTS_obj.id
    assert stored_$ARGUMENTS.name == name

def test_update_$ARGUMENTS(db: Session) -> None:
    """$ARGUMENTS更新テスト"""
    name = random_lower_string()
    $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
    $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)

    new_name = random_lower_string()
    $ARGUMENTS_update = $ARGUMENTSUpdate(name=new_name)
    $ARGUMENTS_updated = $ARGUMENTS.update(db=db, db_obj=$ARGUMENTS_obj, obj_in=$ARGUMENTS_update)

    assert $ARGUMENTS_updated.id == $ARGUMENTS_obj.id
    assert $ARGUMENTS_updated.name == new_name

def test_delete_$ARGUMENTS(db: Session) -> None:
    """$ARGUMENTS削除テスト"""
    name = random_lower_string()
    $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
    $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)

    $ARGUMENTS_deleted = $ARGUMENTS.remove(db=db, id=$ARGUMENTS_obj.id)
    $ARGUMENTS_get = $ARGUMENTS.get(db=db, id=$ARGUMENTS_obj.id)

    assert $ARGUMENTS_get is None
```

### 7. 設計考慮事項

#### データベース制約

- [ ] 適切な NULL/NOT NULL 設定
- [ ] ユニーク制約の設定
- [ ] 外部キー制約の設定
- [ ] チェック制約の設定

#### インデックス最適化

- [ ] 主キーインデックス
- [ ] 頻繁に検索されるカラムのインデックス
- [ ] 複合インデックスの検討
- [ ] 部分インデックスの活用

#### パフォーマンス

- [ ] N+1問題の回避（eager loading）
- [ ] クエリ最適化
- [ ] バッチ処理対応
- [ ] ページネーション対応

### 8. 完了後確認

```bash
# テスト実行
cd apps/backend && python -m pytest tests/crud/test_crud_$ARGUMENTS.py -v

# マイグレーション確認
cd apps/backend && alembic current
cd apps/backend && alembic history

# モデル登録確認
cd apps/backend && python -c "from app.models import $ARGUMENTS; print('Model imported successfully')"
```

### 9. 他モデルとの関連設定

必要に応じて `app/db/base.py` でモデルをインポートし、`app/models/__init__.py` に追加してください。

実装完了後、データベーステーブルが正しく作成されていることを確認してください。
