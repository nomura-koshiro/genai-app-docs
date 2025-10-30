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

## 参考リンク

- [REST API Tutorial](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)
