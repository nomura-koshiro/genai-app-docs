---
title: Create Backend Tests
description: FastAPIエンドポイントとビジネスロジックの包括的なテストを作成
tools: [Write, Edit, MultiEdit, Read, Bash]
---

@backend-developer

「$ARGUMENTS」のバックエンドテストを作成してください。

## FastAPI テスト戦略

### 1. テスト構成
```
apps/backend/tests/
├── api/v1/
│   └── test_$ARGUMENTS.py        # APIエンドポイントテスト
├── crud/
│   └── test_crud_$ARGUMENTS.py   # CRUD操作テスト
├── models/
│   └── test_$ARGUMENTS.py        # モデル・バリデーションテスト
├── utils/
│   ├── utils.py                  # テストユーティリティ
│   └── fixtures.py               # テストフィクスチャ
└── conftest.py                   # pytest設定
```

### 2. APIエンドポイントテスト (`tests/api/v1/test_$ARGUMENTS.py`)

#### 基本構造
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.utils import random_lower_string
from app.tests.utils.$ARGUMENTS import create_random_$ARGUMENTS

class Test$ARGUMENTSEndpoints:
    """$ARGUMENTS APIエンドポイントテスト"""
    
    def test_create_$ARGUMENTS_success(
        self, 
        client: TestClient, 
        superuser_token_headers: dict[str, str]
    ) -> None:
        """正常系：$ARGUMENTS作成成功"""
        data = {
            "name": random_lower_string(),
            "description": random_lower_string(),
            "is_active": True
        }
        response = client.post(
            f"{settings.API_V1_STR}/$ARGUMENTS/",
            headers=superuser_token_headers,
            json=data,
        )
        
        assert response.status_code == 201
        content = response.json()
        assert content["name"] == data["name"]
        assert content["description"] == data["description"]
        assert content["is_active"] == data["is_active"]
        assert "id" in content
        assert "created_at" in content
        assert "updated_at" in content

    def test_create_$ARGUMENTS_invalid_data(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str]
    ) -> None:
        """異常系：無効なデータでの$ARGUMENTS作成"""
        data = {
            "name": "",  # 空文字（無効）
            "description": "a" * 1001,  # 長すぎる説明（無効）
        }
        response = client.post(
            f"{settings.API_V1_STR}/$ARGUMENTS/",
            headers=superuser_token_headers,
            json=data,
        )
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(error["loc"] == ["name"] for error in errors)
        assert any(error["loc"] == ["description"] for error in errors)

    def test_get_$ARGUMENTS_list(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session
    ) -> None:
        """正常系：$ARGUMENTS一覧取得"""
        # テストデータ作成
        $ARGUMENTS_1 = create_random_$ARGUMENTS(db)
        $ARGUMENTS_2 = create_random_$ARGUMENTS(db)
        
        response = client.get(
            f"{settings.API_V1_STR}/$ARGUMENTS/",
            headers=superuser_token_headers,
        )
        
        assert response.status_code == 200
        content = response.json()
        assert len(content) >= 2
        
        # 作成した$ARGUMENTSが含まれることを確認
        ids = [item["id"] for item in content]
        assert $ARGUMENTS_1.id in ids
        assert $ARGUMENTS_2.id in ids

    def test_get_$ARGUMENTS_by_id(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session
    ) -> None:
        """正常系：ID による$ARGUMENTS取得"""
        $ARGUMENTS_obj = create_random_$ARGUMENTS(db)
        
        response = client.get(
            f"{settings.API_V1_STR}/$ARGUMENTS/{$ARGUMENTS_obj.id}",
            headers=superuser_token_headers,
        )
        
        assert response.status_code == 200
        content = response.json()
        assert content["id"] == $ARGUMENTS_obj.id
        assert content["name"] == $ARGUMENTS_obj.name

    def test_get_$ARGUMENTS_not_found(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str]
    ) -> None:
        """異常系：存在しない$ARGUMENTSの取得"""
        response = client.get(
            f"{settings.API_V1_STR}/$ARGUMENTS/999999",
            headers=superuser_token_headers,
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_$ARGUMENTS_success(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session
    ) -> None:
        """正常系：$ARGUMENTS更新成功"""
        $ARGUMENTS_obj = create_random_$ARGUMENTS(db)
        
        update_data = {
            "name": random_lower_string(),
            "description": "Updated description",
            "is_active": False
        }
        
        response = client.put(
            f"{settings.API_V1_STR}/$ARGUMENTS/{$ARGUMENTS_obj.id}",
            headers=superuser_token_headers,
            json=update_data,
        )
        
        assert response.status_code == 200
        content = response.json()
        assert content["id"] == $ARGUMENTS_obj.id
        assert content["name"] == update_data["name"]
        assert content["description"] == update_data["description"]
        assert content["is_active"] == update_data["is_active"]

    def test_delete_$ARGUMENTS_success(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session
    ) -> None:
        """正常系：$ARGUMENTS削除成功"""
        $ARGUMENTS_obj = create_random_$ARGUMENTS(db)
        
        response = client.delete(
            f"{settings.API_V1_STR}/$ARGUMENTS/{$ARGUMENTS_obj.id}",
            headers=superuser_token_headers,
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # 削除確認
        get_response = client.get(
            f"{settings.API_V1_STR}/$ARGUMENTS/{$ARGUMENTS_obj.id}",
            headers=superuser_token_headers,
        )
        assert get_response.status_code == 404

    def test_unauthorized_access(self, client: TestClient) -> None:
        """異常系：認証なしでのアクセス"""
        response = client.get(f"{settings.API_V1_STR}/$ARGUMENTS/")
        assert response.status_code == 401
```

### 3. CRUD操作テスト (`tests/crud/test_crud_$ARGUMENTS.py`)

```python
import pytest
from sqlalchemy.orm import Session

from app.crud.crud_$ARGUMENTS import $ARGUMENTS
from app.schemas.$ARGUMENTS import $ARGUMENTSCreate, $ARGUMENTSUpdate
from app.tests.utils.utils import random_lower_string

class TestCRUD$ARGUMENTS:
    """$ARGUMENTS CRUD操作テスト"""
    
    def test_create_$ARGUMENTS(self, db: Session) -> None:
        """$ARGUMENTS作成テスト"""
        name = random_lower_string()
        description = random_lower_string()
        $ARGUMENTS_in = $ARGUMENTSCreate(
            name=name,
            description=description,
            is_active=True
        )
        
        $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        assert $ARGUMENTS_obj.name == name
        assert $ARGUMENTS_obj.description == description
        assert $ARGUMENTS_obj.is_active is True
        assert $ARGUMENTS_obj.id is not None

    def test_get_$ARGUMENTS(self, db: Session) -> None:
        """$ARGUMENTS取得テスト"""
        name = random_lower_string()
        $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
        $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        stored_$ARGUMENTS = $ARGUMENTS.get(db=db, id=$ARGUMENTS_obj.id)
        
        assert stored_$ARGUMENTS
        assert stored_$ARGUMENTS.id == $ARGUMENTS_obj.id
        assert stored_$ARGUMENTS.name == name

    def test_get_$ARGUMENTS_by_name(self, db: Session) -> None:
        """名前による$ARGUMENTS取得テスト"""
        name = random_lower_string()
        $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
        $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        stored_$ARGUMENTS = $ARGUMENTS.get_by_name(db=db, name=name)
        
        assert stored_$ARGUMENTS
        assert stored_$ARGUMENTS.id == $ARGUMENTS_obj.id
        assert stored_$ARGUMENTS.name == name

    def test_update_$ARGUMENTS(self, db: Session) -> None:
        """$ARGUMENTS更新テスト"""
        name = random_lower_string()
        $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
        $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        new_name = random_lower_string()
        $ARGUMENTS_update = $ARGUMENTSUpdate(name=new_name, is_active=False)
        $ARGUMENTS_updated = $ARGUMENTS.update(
            db=db, 
            db_obj=$ARGUMENTS_obj, 
            obj_in=$ARGUMENTS_update
        )
        
        assert $ARGUMENTS_updated.id == $ARGUMENTS_obj.id
        assert $ARGUMENTS_updated.name == new_name
        assert $ARGUMENTS_updated.is_active is False

    def test_delete_$ARGUMENTS(self, db: Session) -> None:
        """$ARGUMENTS削除テスト"""
        name = random_lower_string()
        $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
        $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        $ARGUMENTS_deleted = $ARGUMENTS.remove(db=db, id=$ARGUMENTS_obj.id)
        $ARGUMENTS_get = $ARGUMENTS.get(db=db, id=$ARGUMENTS_obj.id)
        
        assert $ARGUMENTS_deleted == $ARGUMENTS_obj.id
        assert $ARGUMENTS_get is None

    def test_get_multi_$ARGUMENTS(self, db: Session) -> None:
        """複数$ARGUMENTS取得テスト"""
        # 複数の$ARGUMENTSを作成
        $ARGUMENTS_list = []
        for _ in range(3):
            name = random_lower_string()
            $ARGUMENTS_in = $ARGUMENTSCreate(name=name)
            $ARGUMENTS_obj = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
            $ARGUMENTS_list.append($ARGUMENTS_obj)
        
        stored_$ARGUMENTS = $ARGUMENTS.get_multi(db=db, skip=0, limit=10)
        
        assert len(stored_$ARGUMENTS) >= 3
        stored_ids = [item.id for item in stored_$ARGUMENTS]
        for $ARGUMENTS_obj in $ARGUMENTS_list:
            assert $ARGUMENTS_obj.id in stored_ids

    def test_search_$ARGUMENTS_by_name(self, db: Session) -> None:
        """名前検索テスト"""
        search_term = "test_search"
        
        # 検索対象の$ARGUMENTSを作成
        $ARGUMENTS_in = $ARGUMENTSCreate(name=f"{search_term}_item1")
        $ARGUMENTS_obj1 = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        $ARGUMENTS_in = $ARGUMENTSCreate(name=f"{search_term}_item2")
        $ARGUMENTS_obj2 = $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        # 検索対象外の$ARGUMENTSを作成
        $ARGUMENTS_in = $ARGUMENTSCreate(name="other_item")
        $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)
        
        # 検索実行
        search_results = $ARGUMENTS.search_by_name(db=db, query=search_term)
        
        assert len(search_results) == 2
        result_ids = [item.id for item in search_results]
        assert $ARGUMENTS_obj1.id in result_ids
        assert $ARGUMENTS_obj2.id in result_ids
```

### 4. モデル・バリデーションテスト (`tests/models/test_$ARGUMENTS.py`)

```python
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.$ARGUMENTS import $ARGUMENTS
from app.schemas.$ARGUMENTS import $ARGUMENTSCreate, $ARGUMENTSUpdate
from app.tests.utils.utils import random_lower_string

class Test$ARGUMENTSModel:
    """$ARGUMENTS モデルテスト"""
    
    def test_$ARGUMENTS_model_creation(self, db: Session) -> None:
        """$ARGUMENTSモデル作成テスト"""
        name = random_lower_string()
        description = random_lower_string()
        
        $ARGUMENTS_obj = $ARGUMENTS(
            name=name,
            description=description,
            is_active=True
        )
        
        db.add($ARGUMENTS_obj)
        db.commit()
        db.refresh($ARGUMENTS_obj)
        
        assert $ARGUMENTS_obj.id is not None
        assert $ARGUMENTS_obj.name == name
        assert $ARGUMENTS_obj.description == description
        assert $ARGUMENTS_obj.is_active is True
        assert $ARGUMENTS_obj.created_at is not None
        assert $ARGUMENTS_obj.updated_at is not None

    def test_$ARGUMENTS_repr(self, db: Session) -> None:
        """$ARGUMENTS __repr__ メソッドテスト"""
        name = random_lower_string()
        $ARGUMENTS_obj = $ARGUMENTS(name=name)
        
        db.add($ARGUMENTS_obj)
        db.commit()
        db.refresh($ARGUMENTS_obj)
        
        expected = f"<$ARGUMENTS(id={$ARGUMENTS_obj.id}, name='{name}')>"
        assert repr($ARGUMENTS_obj) == expected

class Test$ARGUMENTSSchema:
    """$ARGUMENTS スキーマテスト"""
    
    def test_$ARGUMENTS_create_schema_valid(self) -> None:
        """$ARGUMENTSCreate 正常バリデーション"""
        data = {
            "name": "Test $ARGUMENTS",
            "description": "Test description",
            "is_active": True
        }
        
        schema = $ARGUMENTSCreate(**data)
        
        assert schema.name == data["name"]
        assert schema.description == data["description"]
        assert schema.is_active == data["is_active"]

    def test_$ARGUMENTS_create_schema_invalid_name(self) -> None:
        """$ARGUMENTSCreate 無効な名前"""
        data = {
            "name": "",  # 空文字
            "description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            $ARGUMENTSCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_$ARGUMENTS_create_schema_long_description(self) -> None:
        """$ARGUMENTSCreate 長すぎる説明"""
        data = {
            "name": "Test Name",
            "description": "a" * 1001  # 1000文字制限を超過
        }
        
        with pytest.raises(ValidationError) as exc_info:
            $ARGUMENTSCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_$ARGUMENTS_update_schema_partial(self) -> None:
        """$ARGUMENTSUpdate 部分更新"""
        data = {
            "name": "Updated name"
            # description と is_active は省略
        }
        
        schema = $ARGUMENTSUpdate(**data)
        
        assert schema.name == data["name"]
        assert schema.description is None
        assert schema.is_active is None
```

### 5. テストユーティリティ (`tests/utils/$ARGUMENTS.py`)

```python
from sqlalchemy.orm import Session

from app.crud.crud_$ARGUMENTS import $ARGUMENTS
from app.models.$ARGUMENTS import $ARGUMENTS as $ARGUMENTSModel
from app.schemas.$ARGUMENTS import $ARGUMENTSCreate
from app.tests.utils.utils import random_lower_string

def create_random_$ARGUMENTS(db: Session) -> $ARGUMENTSModel:
    """ランダムな$ARGUMENTSを作成"""
    name = random_lower_string()
    description = random_lower_string()
    
    $ARGUMENTS_in = $ARGUMENTSCreate(
        name=name,
        description=description,
        is_active=True
    )
    
    return $ARGUMENTS.create(db=db, obj_in=$ARGUMENTS_in)

def create_random_$ARGUMENTS_data() -> dict:
    """ランダムな$ARGUMENTSデータを作成"""
    return {
        "name": random_lower_string(),
        "description": random_lower_string(),
        "is_active": True
    }
```

### 6. テスト実行・検証

#### テスト実行コマンド
```bash
# 全テスト実行
cd apps/backend && python -m pytest

# 特定モジュールのテスト
cd apps/backend && python -m pytest tests/api/v1/test_$ARGUMENTS.py -v

# カバレッジ測定
cd apps/backend && python -m pytest --cov=app --cov-report=html

# 並列実行（高速化）
cd apps/backend && python -m pytest -n auto
```

#### カバレッジ目標
- **ライン カバレッジ**: 90% 以上
- **ブランチ カバレッジ**: 85% 以上  
- **重要機能**: 100% カバレッジ

### 7. パフォーマンステスト

```python
import time
import pytest
from fastapi.testclient import TestClient

def test_$ARGUMENTS_list_performance(
    client: TestClient, 
    superuser_token_headers: dict[str, str],
    db: Session
) -> None:
    """$ARGUMENTS一覧取得のパフォーマンステスト"""
    # 大量データ作成
    for _ in range(100):
        create_random_$ARGUMENTS(db)
    
    start_time = time.time()
    response = client.get(
        f"{settings.API_V1_STR}/$ARGUMENTS/",
        headers=superuser_token_headers,
    )
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 1.0  # 1秒以内でレスポンス
```

### 8. テスト品質チェック

#### 実行確認
```bash
# テスト実行
cd apps/backend && python -m pytest tests/ -v

# カバレッジレポート生成
cd apps/backend && python -m pytest --cov=app --cov-report=html
# htmlcov/index.html でレポート確認

# パフォーマンステスト
cd apps/backend && python -m pytest tests/ -k "performance" -v
```

#### 品質基準
- [ ] 全テストが成功すること
- [ ] カバレッジが目標値を満たすこと
- [ ] パフォーマンステストが基準を満たすこと
- [ ] テストの実行時間が適切であること

テスト作成完了後、CI/CDパイプラインでの自動実行も設定してください。