# レイヤードアーキテクチャ

## 設計原則

- **4層アーキテクチャ**: API層 → サービス層 → リポジトリ層 → モデル層
- **SOLID原則**: 単一責任、開放閉鎖、依存性逆転
- **DRY/KISS**: コード重複排除・シンプル設計

## レイヤー構造

```
┌─────────────────────────────────────┐
│           API Layer                 │  ← エンドポイント、リクエスト/レスポンス
│      (api/v1/endpoints/)            │
├─────────────────────────────────────┤
│         Service Layer               │  ← ビジネスロジック
│          (services/)                │
├─────────────────────────────────────┤
│       Repository Layer              │  ← データアクセス、CRUD操作
│        (repositories/)              │
├─────────────────────────────────────┤
│         Model Layer                 │  ← SQLAlchemyモデル、Pydanticスキーマ
│      (models/, schemas/)            │
└─────────────────────────────────────┘
```

## 各層の責務

### API層 (`api/v1/endpoints/`)

- HTTPリクエスト/レスポンス処理
- リクエストバリデーション（Pydantic）
- 認証・認可の適用
- OpenAPI/Swaggerドキュメント生成

### サービス層 (`services/`)

- ビジネスロジックの実装
- トランザクション管理
- 複数リポジトリの連携
- 外部サービス（AI等）との連携

### リポジトリ層 (`repositories/`)

- データアクセスの抽象化
- CRUD操作の実装
- クエリの最適化
- N+1問題の回避

### モデル層 (`models/`, `schemas/`)

- SQLAlchemyモデル定義
- Pydanticスキーマ定義
- バリデーションルール
- リレーションシップ定義

## 依存性注入

```python
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    repository = UserRepository(db)
    service = UserService(repository)
    return service.get_user(user_id)
```

## データフロー

```
Request → API Layer → Service Layer → Repository Layer → Database
                                                              ↓
Response ← API Layer ← Service Layer ← Repository Layer ← Result
```

## ドキュメント参照

詳細は以下のドキュメントを参照：

- [プロジェクト構造](docs/developer-guide/02-architecture/01-project-structure.md)
- [レイヤードアーキテクチャ](docs/developer-guide/02-architecture/02-layered-architecture.md)
- [依存性注入](docs/developer-guide/02-architecture/03-dependency-injection.md)
- [コードリーディングガイド](docs/developer-guide/02-architecture/04-code-reading-guide.md)
- [システムアーキテクチャ設計](docs/specifications/04-architecture/01-system-architecture.md)
