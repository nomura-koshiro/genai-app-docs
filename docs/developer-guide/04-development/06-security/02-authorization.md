# 認可制御

ロールベースおよびパーミッションベースの認可について説明します。

## ロールベースアクセス制御（RBAC）

### モデル定義

```python
# src/app/models/sample_user.py
class SampleUser(Base):
    __tablename__ = "sample_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 認可依存性

```python
# src/app/api/dependencies.py
from fastapi import Depends, HTTPException


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> SampleUser:
    """アクティブユーザーのみ許可。"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> SampleUser:
    """スーパーユーザーのみ許可。"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


CurrentSampleUserDep = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuserDep = Annotated[User, Depends(get_current_superuser)]
```

### エンドポイントでの使用

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: CurrentSuperuserDep,  # スーパーユーザーのみ許可
    user_service: SampleUserServiceDep,
):
    """ユーザー削除（管理者のみ）。"""
    await user_service.delete_user(user_id)
    return {"message": f"User {user_id} deleted"}


@router.get("/me")
async def get_me(
    current_user: CurrentSampleUserDep,  # 認証済みユーザーのみ
):
    """自分の情報取得。"""
    return SampleUserResponse.model_validate(current_user)
```

## リソース所有者チェック

```python
@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    data: SessionUpdate,
    current_user: CurrentSampleUserDep,
    session_service: SampleSessionServiceDep,
):
    """セッション更新（所有者のみ）。"""
    session = await session_service.get_session(session_id)

    # 所有者チェック
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to modify this session"
        )

    return await session_service.update_session(session_id, data)
```

## パーミッションベースアクセス制御

```python
from enum import Enum


class Permission(str, Enum):
    """パーミッション定義。"""
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    SESSION_READ = "session:read"
    SESSION_WRITE = "session:write"


def require_permission(permission: Permission):
    """パーミッションチェック依存性。"""
    async def permission_checker(current_user: CurrentSampleUserDep) -> SampleUser:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission {permission} required"
            )
        return current_user
    return permission_checker


def has_permission(user: SampleUser, permission: Permission) -> bool:
    """ユーザーがパーミッションを持っているかチェック。"""
    # スーパーユーザーはすべてのパーミッションを持つ
    if user.is_superuser:
        return True

    # ユーザーのパーミッションをチェック
    # （実際にはDBから取得）
    return permission in user.permissions


# 使用例
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    _: Annotated[User, Depends(require_permission(Permission.USER_DELETE))],
    user_service: SampleUserServiceDep,
):
    """ユーザー削除。"""
    await user_service.delete_user(user_id)
    return {"message": "User deleted"}
```

## 参考リンク

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [RBAC Explanation](https://en.wikipedia.org/wiki/Role-based_access_control)
