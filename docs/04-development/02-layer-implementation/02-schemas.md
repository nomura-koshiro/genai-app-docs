# スキーマ層（Schemas）

Pydanticを使用したデータバリデーションとシリアライゼーションについて説明します。

## 概要

スキーマ層は、APIの入出力データの構造定義とバリデーションを担当します。

**責務**:

- リクエスト/レスポンスデータの構造定義
- 入力バリデーション
- データ変換とシリアライゼーション
- ドキュメント自動生成のための情報提供

---

## 基本的なスキーマ定義

```python
# src/app/schemas/sample_user.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SampleUserBase(BaseModel):
    """ベースユーザースキーマ。"""

    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="ユーザー名"
    )


class SampleUserCreate(SampleUserBase):
    """ユーザー作成スキーマ。"""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="ユーザーパスワード"
    )


class SampleUserUpdate(BaseModel):
    """ユーザー更新スキーマ。"""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None


class SampleUserResponse(SampleUserBase):
    """ユーザーレスポンススキーマ。"""

    id: int = Field(..., description="ユーザーID")
    is_active: bool = Field(..., description="アクティブ状態")
    created_at: datetime = Field(..., description="作成日時")

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemyモデルから変換可能
```

---

## バリデーション

### フィールドバリデーション

```python
from pydantic import BaseModel, Field, field_validator


class SampleUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """パスワードの強度を検証。"""
        if not any(char.isdigit() for char in v):
            raise ValueError("パスワードには数字を含める必要があります")
        if not any(char.isupper() for char in v):
            raise ValueError("パスワードには大文字を含める必要があります")
        return v
```

### モデルバリデーション

```python
from pydantic import model_validator


class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRange":
        """日付範囲を検証。"""
        if self.start_date >= self.end_date:
            raise ValueError("開始日は終了日より前でなければなりません")
        return self

```

---

## ベストプラクティス

### 1. スキーマの継承

```python
# ベーススキーマ
class SampleUserBase(BaseModel):
    email: EmailStr
    username: str

# 作成用（パスワード追加）
class SampleUserCreate(SampleUserBase):
    password: str

# 更新用（すべてオプショナル）
class SampleUserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None

# レスポンス用（ID追加、パスワード除外）
class SampleUserResponse(SampleUserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemyモデルから変換可能
```

### 2. Fieldでメタデータを提供

```python
class SampleUserCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="ユーザーのメールアドレス",
        examples=["user@example.com"]
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="一意のユーザー名",
        examples=["john_doe"]
    )
```

---

## 参考リンク

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)

---

次のセクション: [03-repositories.md](./03-repositories.md)
