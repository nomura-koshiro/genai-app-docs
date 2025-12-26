"""Pydanticスキーマの共通ベースモデル。

このモジュールは、snake_case（Python）とcamelCase（JavaScript/TypeScript）間の
自動変換を提供する共通ベースモデルを定義します。

主なクラス:
    - BaseCamelCaseModel: キャメルケース変換を行う基本モデル
    - BaseCamelCaseORMModel: ORM変換対応のキャメルケースモデル

使用方法:
    >>> from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel
    >>>
    >>> # 通常のリクエスト/レスポンス用
    >>> class UserRequest(BaseCamelCaseModel):
    ...     user_name: str
    ...     created_at: datetime
    >>>
    >>> # ORMモデルから変換する場合
    >>> class UserResponse(BaseCamelCaseORMModel):
    ...     user_name: str
    ...     created_at: datetime

変換例:
    - リクエスト: {"userName": "John"} → Python内部: user_name = "John"
    - レスポンス: user_name = "John" → {"userName": "John"}
"""

from humps import camelize
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """snake_caseをcamelCaseに変換する。

    Args:
        string: 変換対象の文字列（snake_case）

    Returns:
        camelCaseに変換された文字列

    Example:
        >>> to_camel("user_name")
        'userName'
        >>> to_camel("created_at")
        'createdAt'
    """
    return camelize(string)


class BaseCamelCaseModel(BaseModel):
    """キャメルケース変換を行う共通ベースモデル。

    フロントエンド（TypeScript/JavaScript）との通信において、
    snake_case（Python）とcamelCase（JS）間の自動変換を提供します。

    Features:
        - alias_generator: snake_case → camelCase 自動変換
        - populate_by_name: snake_caseでのフィールドアクセスも許可

    使用方法:
        >>> class CreateUserRequest(BaseCamelCaseModel):
        ...     user_name: str
        ...     email_address: str
        >>>
        >>> # camelCaseでリクエストを受け取り可能
        >>> data = {"userName": "John", "emailAddress": "john@example.com"}
        >>> user = CreateUserRequest(**data)
        >>> user.user_name  # "John"

    Note:
        レスポンス時は `model_dump(by_alias=True)` または
        FastAPIのresponse_model_by_alias設定を使用してください。
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class BaseCamelCaseORMModel(BaseCamelCaseModel):
    """ORM変換対応のキャメルケース共通ベースモデル。

    SQLAlchemy ORMモデルからの変換に対応した共通ベースモデルです。
    BaseCamelCaseModelの機能に加え、from_attributes=Trueを有効にしています。

    Features:
        - alias_generator: snake_case → camelCase 自動変換
        - populate_by_name: snake_caseでのフィールドアクセスも許可
        - from_attributes: ORMモデルからの直接変換対応

    使用方法:
        >>> class UserResponse(BaseCamelCaseORMModel):
        ...     id: uuid.UUID
        ...     user_name: str
        ...     created_at: datetime
        >>>
        >>> # ORMモデルから直接変換
        >>> orm_user = session.query(User).first()
        >>> response = UserResponse.model_validate(orm_user)

    Note:
        レスポンス時は `model_dump(by_alias=True)` または
        FastAPIのresponse_model_by_alias設定を使用してください。
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
