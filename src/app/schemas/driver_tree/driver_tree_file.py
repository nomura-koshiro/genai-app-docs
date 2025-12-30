import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel
from app.schemas.driver_tree.common import (
    DriverTreeColumnInfo,
    DriverTreeColumnRoleEnum,
    DriverTreeFileListItem,
    DriverTreeUploadedFileItem,
)

# Request


class DriverTreeSheetSelectRequest(BaseCamelCaseModel):
    """シート選択リクエスト。

    Request Body:
        - sheet_id: str - シートID（必須）
    """

    sheet_id: str = Field(..., description="シートID")


class DriverTreeColumnSetupItem(BaseCamelCaseModel):
    """カラム設定アイテム（Request用）。

    Request時に送信するカラム情報（column_idとroleのみ）。

    Attributes:
        - column_id: uuid - カラムID（必須、一意識別子）
        - role: DriverTreeColumnRoleEnum - カラムの役割（デフォルト: 利用しない）
    """

    column_id: uuid.UUID = Field(..., description="カラムID（一意識別子）")
    role: DriverTreeColumnRoleEnum = Field(default=DriverTreeColumnRoleEnum.UNUSED, description="カラムの役割")


class DriverTreeColumnSetupRequest(BaseCamelCaseModel):
    """カラム設定リクエスト。

    Request Body:
        - columns: list[DriverTreeColumnSetupItem] - カラム設定リスト
    """

    columns: list[DriverTreeColumnSetupItem] = Field(..., description="カラム情報のリスト")


# Response


class DriverTreeFileUploadResponse(BaseCamelCaseModel):
    """ファイルアップロードレスポンス。

    Response:
        - files: list[DriverTreeUploadedFileItem] - アップロード済みファイル一覧（columns なし）
    """

    files: list[DriverTreeUploadedFileItem] = Field(default_factory=list, description="ファイル一覧")


class DriverTreeFileDeleteResponse(BaseCamelCaseModel):
    """ファイル削除レスポンス。

    Response:
        - files: list[DriverTreeUploadedFileItem] - 削除後のアップロード済みファイル一覧
    """

    files: list[DriverTreeUploadedFileItem] = Field(default_factory=list, description="ファイル一覧")


class DriverTreeSheetSelectResponse(BaseCamelCaseModel):
    """シート選択レスポンス。

    Response:
        - success: bool - 成功フラグ
        - files: list[DriverTreeFileListItem] - 選択済みシート一覧（columns あり）
    """

    success: bool = Field(..., description="成功フラグ")
    files: list[DriverTreeFileListItem] = Field(default_factory=list, description="ファイル一覧")


class DriverTreeSheetDeleteResponse(BaseCamelCaseModel):
    """シート削除レスポンス。

    Response:
        - success: bool - 成功フラグ
        - files: list[DriverTreeFileListItem] - 削除後の選択済みシート一覧（columns あり）
    """

    success: bool = Field(..., description="成功フラグ")
    files: list[DriverTreeFileListItem] = Field(default_factory=list, description="ファイル一覧")


class DriverTreeUploadedFileListResponse(BaseCamelCaseModel):
    """アップロード済みファイル一覧レスポンス。

    Response:
        - files: list[DriverTreeUploadedFileItem] - アップロード済みファイル一覧（columns なし）
    """

    files: list[DriverTreeUploadedFileItem] = Field(default_factory=list, description="ファイル一覧")


class DriverTreeSelectedSheetListResponse(BaseCamelCaseModel):
    """選択済みシート一覧レスポンス。

    Response:
        - files: list[DriverTreeFileListItem] - 選択済みシート一覧（columns あり）
    """

    files: list[DriverTreeFileListItem] = Field(default_factory=list, description="ファイル一覧")


class DriverTreeColumnSetupResponse(BaseCamelCaseModel):
    """カラム設定レスポンス。

    Response:
        - success: bool - 成功フラグ
        - columns: list[DriverTreeColumnInfo] - カラム情報のリスト
            - column_name: str - カラム名
            - role: str - カラムの役割
            - items: list[str] - 項目例
    """

    success: bool = Field(..., description="成功フラグ")
    columns: list[DriverTreeColumnInfo] = Field(default_factory=list, description="カラム情報のリスト")


class DriverTreeSheetRefreshResponse(BaseCamelCaseModel):
    """シートデータ更新レスポンス。

    元ファイルからデータを再読み込みして更新した結果を返します。

    Response:
        - success: bool - 成功フラグ
        - updated_at: datetime - 更新日時
        - files: list[DriverTreeFileListItem] - 更新後の選択済みシート一覧（columns あり）
    """

    success: bool = Field(..., description="成功フラグ")
    updated_at: datetime = Field(..., description="更新日時")
    files: list[DriverTreeFileListItem] = Field(default_factory=list, description="ファイル一覧")


class ColumnInfo(BaseCamelCaseModel):
    """カラム情報。

    Attributes:
        name (str): カラム名（内部名）
        display_name (str): 表示名
        data_type (str): データ型（string/number/datetime/boolean）
        role (str | None): 役割（推移/値/カテゴリ等）
    """

    name: str = Field(..., description="カラム名")
    display_name: str = Field(..., description="表示名")
    data_type: str = Field(..., description="データ型")
    role: str | None = Field(default=None, description="役割")


class SheetDetailResponse(BaseCamelCaseModel):
    """シート詳細レスポンス。

    Attributes:
        sheet_id (uuid.UUID): シートID
        sheet_name (str): シート名
        columns (list[ColumnInfo]): カラム情報リスト
        row_count (int): 行数
        sample_data (list[dict]): サンプルデータ（最初の10行）
    """

    sheet_id: uuid.UUID = Field(..., description="シートID")
    sheet_name: str = Field(..., description="シート名")
    columns: list[ColumnInfo] = Field(default_factory=list, description="カラム情報リスト")
    row_count: int = Field(..., description="行数")
    sample_data: list[dict[str, Any]] = Field(default_factory=list, description="サンプルデータ")
