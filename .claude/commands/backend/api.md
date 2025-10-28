---
title: Create API Endpoint
description: 適切な構造とバリデーションを持つFastAPIエンドポイントを作成
tools: [Write, Edit, MultiEdit, Bash]
---

@backend-developer

新しいAPIエンドポイント「$ARGUMENTS」を作成してください。

## FastAPI エンドポイント作成要件

### 1. ファイル構成
```
apps/backend/app/
├── api/v1/endpoints/
│   └── $ARGUMENTS.py          # エンドポイント実装
├── crud/
│   └── crud_$ARGUMENTS.py     # CRUD操作
├── models/
│   └── $ARGUMENTS.py          # SQLAlchemy モデル
├── schemas/
│   └── $ARGUMENTS.py          # Pydantic スキーマ
└── tests/
    └── api/v1/test_$ARGUMENTS.py  # APIテスト
```

### 2. エンドポイント実装 (`api/v1/endpoints/$ARGUMENTS.py`)

#### 基本構造
```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_$ARGUMENTS import $ARGUMENTS
from app.models.$ARGUMENTS import $ARGUMENTS as $ARGUMENTSModel
from app.schemas.$ARGUMENTS import $ARGUMENTS, $ARGUMENTSCreate, $ARGUMENTSUpdate

router = APIRouter()

@router.get("/", response_model=List[$ARGUMENTS])
def read_$ARGUMENTS(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_user),
) -> List[$ARGUMENTSModel]:
    """
    $ARGUMENTS一覧を取得
    """
    items = $ARGUMENTS.get_multi(db=db, skip=skip, limit=limit)
    return items

@router.post("/", response_model=$ARGUMENTS, status_code=status.HTTP_201_CREATED)
def create_$ARGUMENTS(
    *,
    db: Session = Depends(deps.get_db),
    $ARGUMENTS_in: $ARGUMENTSCreate,
    current_user = Depends(deps.get_current_active_user),
) -> $ARGUMENTSModel:
    """
    新しい$ARGUMENTSを作成
    """
    $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
    return $ARGUMENTS_obj

@router.get("/{id}", response_model=$ARGUMENTS)
def read_$ARGUMENTS_by_id(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_user),
) -> $ARGUMENTSModel:
    """
    IDによる$ARGUMENTS取得
    """
    $ARGUMENTS_obj = $ARGUMENTS.get(db=db, id=id)
    if not $ARGUMENTS_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="$ARGUMENTS not found"
        )
    return $ARGUMENTS_obj

@router.put("/{id}", response_model=$ARGUMENTS)
def update_$ARGUMENTS(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    $ARGUMENTS_in: $ARGUMENTSUpdate,
    current_user = Depends(deps.get_current_active_user),
) -> $ARGUMENTSModel:
    """
    $ARGUMENTSを更新
    """
    $ARGUMENTS_obj = $ARGUMENTS.get(db=db, id=id)
    if not $ARGUMENTS_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="$ARGUMENTS not found"
        )
    $ARGUMENTS_obj = $ARGUMENTS.update(db=db, db_obj=$ARGUMENTS_obj, obj_in=$ARGUMENTS_in)
    return $ARGUMENTS_obj

@router.delete("/{id}")
def delete_$ARGUMENTS(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_user),
) -> dict:
    """
    $ARGUMENTSを削除
    """
    $ARGUMENTS_obj = $ARGUMENTS.get(db=db, id=id)
    if not $ARGUMENTS_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="$ARGUMENTS not found"
        )
    $ARGUMENTS.remove(db=db, id=id)
    return {"message": "$ARGUMENTS deleted successfully"}
```

### 3. 必須実装項目

#### Pydantic スキーマ (`schemas/$ARGUMENTS.py`)
- [ ] Base スキーマ
- [ ] Create スキーマ（バリデーション付き）
- [ ] Update スキーマ
- [ ] Response スキーマ
- [ ] 適切な型アノテーション

#### SQLAlchemy モデル (`models/$ARGUMENTS.py`)
- [ ] テーブル定義
- [ ] リレーションシップ
- [ ] インデックス設定
- [ ] 制約設定

#### CRUD操作 (`crud/crud_$ARGUMENTS.py`)
- [ ] 基本CRUD操作（作成、取得、更新、削除）
- [ ] 検索・フィルタリング
- [ ] ページネーション
- [ ] エラーハンドリング

#### APIテスト (`tests/api/v1/test_$ARGUMENTS.py`)
- [ ] 正常系テスト（CRUD操作）
- [ ] 異常系テスト（バリデーション、権限）
- [ ] エッジケーステスト
- [ ] パフォーマンステスト

### 4. 品質要件

#### セキュリティ
- [ ] 認証・認可の実装
- [ ] 入力値検証
- [ ] SQLインジェクション対策
- [ ] Rate limiting検討

#### パフォーマンス
- [ ] データベースクエリ最適化
- [ ] N+1問題の回避
- [ ] 適切なインデックス
- [ ] キャッシュ戦略

#### ドキュメンテーション
- [ ] OpenAPI/Swagger自動生成
- [ ] 詳細なdocstring
- [ ] 例外処理の文書化
- [ ] 使用例の提供

### 5. 完了後の確認事項

```bash
# テスト実行
cd apps/backend && python -m pytest tests/api/v1/test_$ARGUMENTS.py -v

# 型チェック
cd apps/backend && mypy app/api/v1/endpoints/$ARGUMENTS.py

# リント実行  
cd apps/backend && ruff check app/api/v1/endpoints/$ARGUMENTS.py

# 開発サーバー起動確認
cd apps/backend && uvicorn app.main:app --reload
```

### 6. API router 登録

完了後、`app/api/v1/api.py` にルーターを追加してください：

```python
from app.api.v1.endpoints import $ARGUMENTS

api_router.include_router($ARGUMENTS.router, prefix="/$ARGUMENTS", tags=["$ARGUMENTS"])
```

実装完了後、OpenAPIドキュメント（http://localhost:8000/docs）で動作確認してください。