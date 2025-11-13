# バリデーション

Pydanticを使用したデータバリデーションについて説明します。

## 基本的なバリデーション

```python
from pydantic import BaseModel, EmailStr, Field, field_validator


class SampleUserCreate(BaseModel):
    email: EmailStr = Field(..., description="メールアドレス")
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")
    password: str = Field(..., min_length=8, description="パスワード")
    age: int = Field(..., gt=0, le=150, description="年齢")


# カスタムバリデーション
class SampleUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """パスワードの強度を検証。"""
        if not any(c.isdigit() for c in v):
            raise ValueError("数字を含める必要があります")
        if not any(c.isupper() for c in v):
            raise ValueError("大文字を含める必要があります")
        return v
```

## クエリパラメータのバリデーション

```python
from fastapi import Query

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0, description="スキップ件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    email: str | None = Query(None, regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
):
    pass
```

## 参考リンク

- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
