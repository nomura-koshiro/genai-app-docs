# エンドポイント設計

RESTful APIのエンドポイント設計原則について説明します。

## RESTful原則

### リソースベースのURL

```python
# ✅ 良い例：リソース名は複数形、HTTPメソッドでアクションを表現
GET    /api/sample-users           # ユーザー一覧
POST   /api/sample-users           # ユーザー作成
GET    /api/sample-users/{id}      # ユーザー詳細
PUT    /api/sample-users/{id}      # ユーザー更新
DELETE /users/{id}      # ユーザー削除

# ❌ 悪い例：URLにアクションを含める
GET    /api/getUsers
POST   /api/createUser
POST   /api/updateUser
POST   /api/deleteUser
```

### HTTPメソッドの使い分け

| メソッド | 用途 | 冪等性 |
|---------|------|--------|
| GET | リソース取得 | ○ |
| POST | リソース作成 | × |
| PUT | リソース更新（全体） | ○ |
| PATCH | リソース更新（部分） | △ |
| DELETE | リソース削除 | ○ |

### ネストされたリソース

```python
# サブリソース
GET /api/sample-users/{user_id}/sessions           # ユーザーのセッション一覧
GET /api/sample-users/{user_id}/sessions/{session_id}  # 特定セッション
POST /api/sample-users/{user_id}/files             # ユーザーのファイルアップロード

# ネストは2階層まで
GET /api/sample-users/{user_id}/sessions/{session_id}/messages  # OK
GET /api/a/{id}/b/{id}/c/{id}/d/{id}  # ❌ 深すぎる
```

## HTTPステータスコード

```python
from fastapi import status

# 成功
@router.post("/users", status_code=status.HTTP_201_CREATED)  # 201: 作成成功
@router.get("/users")  # 200: 取得成功（デフォルト）
@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)  # 204: 削除成功（コンテンツなし）

# エラー
# 400: Bad Request（不正なリクエスト）
# 401: Unauthorized（認証が必要）
# 403: Forbidden（権限不足）
# 404: Not Found（リソース未発見）
# 422: Unprocessable Entity（バリデーションエラー）
# 500: Internal Server Error（サーバーエラー）
```

## エンドポイント定義の配置順序

### RESTful標準順序

ファイル内でエンドポイントを定義する際は、**RESTful標準順序**に従います。

**標準順序:** GET → POST → PATCH → DELETE → OTHER

### 実装例

```python
# src/app/api/routes/v1/projects.py
from fastapi import APIRouter, status

router = APIRouter()


# ========================================
# GET エンドポイント
# ========================================

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    project_service: ProjectServiceDep = None,
) -> list[ProjectResponse]:
    """プロジェクト一覧を取得。"""
    projects = await project_service.list_projects(skip=skip, limit=limit)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    """プロジェクト詳細を取得。"""
    project = await project_service.get_project(project_id)
    return ProjectResponse.model_validate(project)


@router.get("/code/{code}", response_model=ProjectResponse)
async def get_project_by_code(
    code: str,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    """プロジェクトコードで検索。"""
    project = await project_service.get_project_by_code(code)
    return ProjectResponse.model_validate(project)


# ========================================
# POST エンドポイント
# ========================================

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    """プロジェクトを作成。"""
    project = await project_service.create_project(project_data, current_user)
    return ProjectResponse.model_validate(project)


# ========================================
# PATCH エンドポイント
# ========================================

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    project_data: ProjectUpdate,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    """プロジェクト情報を更新。"""
    project = await project_service.update_project(project_id, project_data, current_user)
    return ProjectResponse.model_validate(project)


# ========================================
# DELETE エンドポイント
# ========================================

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> None:
    """プロジェクトを削除。"""
    await project_service.delete_project(project_id, current_user)
```

### 順序を守るメリット

1. **予測可能性**
   - どのファイルも同じ構造
   - 新しいエンドポイントの追加位置が明確

2. **可読性**
   - HTTPメソッドごとにグループ化
   - コードレビューが容易

3. **RESTful設計との整合性**
   - HTTPメソッドの意味と配置が一致
   - API設計のベストプラクティスに準拠

4. **保守性**
   - エンドポイントの検索が容易
   - チーム全体で一貫した構造

### サブリソースの場合

サブリソース（ネストされたエンドポイント）も同じ順序で配置します。

```python
# src/app/api/routes/v1/project_members.py
router = APIRouter()

# ========================================
# GET エンドポイント
# ========================================

@router.get("/", response_model=ProjectMemberListResponse)
async def list_project_members(): pass

@router.get("/me", response_model=UserRoleResponse)
async def get_my_role(): pass

# ========================================
# POST エンドポイント
# ========================================

@router.post("/", response_model=ProjectMemberResponse)
async def add_member(): pass

@router.post("/bulk", response_model=ProjectMemberBulkResponse)
async def add_members_bulk(): pass

# ========================================
# PATCH エンドポイント
# ========================================

@router.patch("/{member_id}", response_model=ProjectMemberResponse)
async def update_member_role(): pass

@router.patch("/bulk", response_model=ProjectMemberBulkUpdateResponse)
async def update_members_bulk(): pass

# ========================================
# DELETE エンドポイント
# ========================================

@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(): pass

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_project(): pass
```

---

## 参考リンク

- [REST API Tutorial](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)
- [RESTful API Design Best Practices](https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/)
