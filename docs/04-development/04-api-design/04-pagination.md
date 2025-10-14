# ページネーション

大量データの効率的な取得方法について説明します。

## Offset/Limit方式

```python
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="スキップ件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
):
    """
    Offset/Limit方式のページネーション。

    - skip=0, limit=10: 最初の10件
    - skip=10, limit=10: 11〜20件目
    """
    users = await service.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


# リポジトリ実装
async def get_multi(self, skip: int = 0, limit: int = 100) -> list[User]:
    query = select(User).offset(skip).limit(limit)
    result = await self.db.execute(query)
    return list(result.scalars().all())
```

## カーソルベース方式

```python
@router.get("/users", response_model=CursorPaginatedResponse)
async def list_users(
    cursor: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    カーソルベースのページネーション。

    大量データに適している。
    """
    query = select(User).order_by(User.created_at.desc()).limit(limit)

    if cursor:
        query = query.where(User.created_at < cursor)

    result = await db.execute(query)
    users = list(result.scalars().all())

    next_cursor = users[-1].created_at if users else None

    return CursorPaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        next_cursor=next_cursor,
        limit=limit
    )
```

## ページネーション情報付きレスポンス

```python
class PaginatedResponse(BaseModel):
    items: list[UserResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


@router.get("/users", response_model=PaginatedResponse)
async def list_users(skip: int = 0, limit: int = 100):
    users = await service.list_users(skip, limit)
    total = await service.count_users()

    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )
```
