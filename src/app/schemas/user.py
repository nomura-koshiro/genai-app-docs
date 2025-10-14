"""ユーザー関連のPydanticスキーマ."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """ベースユーザースキーマ."""

    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")


class UserCreate(UserBase):
    """新規ユーザー作成スキーマ."""

    password: str = Field(..., min_length=8, max_length=100, description="ユーザーパスワード")


class UserLogin(BaseModel):
    """ユーザーログインスキーマ."""

    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    password: str = Field(..., description="ユーザーパスワード")


class UserResponse(UserBase):
    """ユーザーレスポンススキーマ."""

    id: int = Field(..., description="ユーザーID")
    is_active: bool = Field(..., description="ユーザーがアクティブかどうか")
    is_superuser: bool = Field(False, description="ユーザーがスーパーユーザーかどうか")
    created_at: datetime = Field(..., description="ユーザー作成時刻")

    class Config:
        """Pydantic設定."""

        from_attributes = True


class Token(BaseModel):
    """JWTトークンレスポンス."""

    access_token: str = Field(..., description="JWTアクセストークン")
    token_type: str = Field("bearer", description="トークンタイプ")


class TokenPayload(BaseModel):
    """JWTトークンペイロード."""

    sub: str = Field(..., description="サブジェクト（ユーザーID）")
    exp: int = Field(..., description="有効期限タイムスタンプ")
