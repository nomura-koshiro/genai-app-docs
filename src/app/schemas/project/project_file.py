"""プロジェクトファイル関連のスキーマ。

このモジュールは、プロジェクトファイル管理のリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    - ProjectFileUploadRequest: ファイルアップロードリクエスト
    - ProjectFileUploadResponse: ファイルアップロード成功レスポンス
    - ProjectFileResponse: ファイル情報レスポンス（uploader情報含む）
    - ProjectFileListResponse: ファイル一覧レスポンス
    - ProjectFileDeleteResponse: ファイル削除レスポンス

使用例:
    >>> from app.schemas.project.file import ProjectFileResponse
    >>> file_response = ProjectFileResponse(
    ...     id=uuid.uuid4(),
    ...     project_id=project_id,
    ...     filename="document.pdf",
    ...     file_size=1024000
    ... )
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel
from app.schemas.user_account.user_account import UserAccountResponse


class ProjectFileUploadRequest(BaseCamelCaseModel):
    """ファイルアップロードリクエストスキーマ。

    multipart/form-dataでファイルをアップロードする際のスキーマです。
    OpenAPIドキュメント生成用に定義しています。

    Attributes:
        file (bytes): アップロードするファイル（バイナリ）

    Example:
        >>> # multipart/form-data でファイルをアップロード
        >>> files = {"file": ("document.pdf", file_content, "application/pdf")}
        >>> response = await client.post(url, files=files)
    """

    file: bytes = Field(..., description="アップロードするファイル（バイナリ）")


class ProjectFileUploadResponse(BaseCamelCaseModel):
    """ファイルアップロード成功レスポンススキーマ。

    ファイルアップロード直後に返却される基本情報を含みます。

    Attributes:
        id (uuid.UUID): ファイルID（UUID）
        project_id (uuid.UUID): プロジェクトID
        filename (str): 保存ファイル名
        original_filename (str): 元のファイル名
        file_path (str): ファイルパス
        file_size (int): ファイルサイズ（バイト）
        mime_type (str | None): MIMEタイプ
        uploaded_by (uuid.UUID): アップロード者のユーザーID
        uploaded_at (datetime): アップロード日時
        message (str): 成功メッセージ

    Example:
        >>> response = ProjectFileUploadResponse(
        ...     id=uuid.uuid4(),
        ...     project_id=project_id,
        ...     filename="doc_12345.pdf",
        ...     original_filename="document.pdf",
        ...     file_path="uploads/projects/proj-id/doc_12345.pdf",
        ...     file_size=1024000,
        ...     mime_type="application/pdf",
        ...     uploaded_by=user_id,
        ...     uploaded_at=datetime.now(UTC),
        ...     message="File uploaded successfully"
        ... )
    """

    id: uuid.UUID = Field(..., description="ファイルID（UUID）")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    filename: str = Field(..., description="保存ファイル名")
    original_filename: str = Field(..., description="元のファイル名")
    file_path: str = Field(..., description="ファイルパス")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")
    mime_type: str | None = Field(default=None, description="MIMEタイプ")
    uploaded_by: uuid.UUID = Field(..., description="アップロード者のユーザーID")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    message: str = Field(default="File uploaded successfully", description="成功メッセージ")


class ProjectFileResponse(BaseCamelCaseORMModel):
    """プロジェクトファイル情報レスポンススキーマ。

    アップロード者情報を含む詳細なファイル情報を返却します。

    Attributes:
        id (uuid.UUID): ファイルID（UUID）
        project_id (uuid.UUID): プロジェクトID
        filename (str): 保存ファイル名
        original_filename (str): 元のファイル名
        file_path (str): ファイルパス
        file_size (int): ファイルサイズ（バイト）
        mime_type (str | None): MIMEタイプ
        uploaded_by (uuid.UUID): アップロード者のユーザーID
        uploaded_at (datetime): アップロード日時
        uploader (UserAccountResponse | None): アップロード者のユーザー情報

    Example:
        >>> file_response = ProjectFileResponse(
        ...     id=uuid.uuid4(),
        ...     project_id=project_id,
        ...     filename="doc_12345.pdf",
        ...     original_filename="document.pdf",
        ...     file_path="uploads/projects/proj-id/doc_12345.pdf",
        ...     file_size=1024000,
        ...     mime_type="application/pdf",
        ...     uploaded_by=user_id,
        ...     uploaded_at=datetime.now(UTC),
        ...     uploader=UserAccountResponse(...)
        ... )

    Note:
        - from_attributesを有効にしているため、ORMモデルから直接変換可能です
        - uploaderフィールドはリレーションシップから自動的に解決されます
    """

    id: uuid.UUID = Field(..., description="ファイルID（UUID）")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    filename: str = Field(..., description="保存ファイル名")
    original_filename: str = Field(..., description="元のファイル名")
    file_path: str = Field(..., description="ファイルパス")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")
    mime_type: str | None = Field(default=None, description="MIMEタイプ")
    uploaded_by: uuid.UUID = Field(..., description="アップロード者のユーザーID")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    uploader: UserAccountResponse | None = Field(default=None, description="アップロード者のユーザー情報")


class ProjectFileListResponse(BaseCamelCaseModel):
    """プロジェクトファイル一覧レスポンススキーマ。

    プロジェクトに属するファイル一覧とメタデータを返却します。

    Attributes:
        files (list[ProjectFileResponse]): ファイルのリスト
        total (int): 総ファイル数
        project_id (uuid.UUID): プロジェクトID

    Example:
        >>> response = ProjectFileListResponse(
        ...     files=[file1, file2, file3],
        ...     total=3,
        ...     project_id=project_id
        ... )

    Note:
        - ページネーション情報は別途クエリパラメータで管理されます
        - total はプロジェクト全体のファイル数を示します
    """

    files: list[ProjectFileResponse] = Field(..., description="ファイルのリスト")
    total: int = Field(..., description="総ファイル数")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")


class ProjectFileDeleteResponse(BaseCamelCaseModel):
    """ファイル削除成功レスポンススキーマ。

    ファイル削除操作の成功を示すレスポンスです。

    Attributes:
        file_id (uuid.UUID): 削除されたファイルのID
        message (str): 成功メッセージ

    Example:
        >>> response = ProjectFileDeleteResponse(
        ...     file_id=uuid.uuid4(),
        ...     message="File deleted successfully"
        ... )
    """

    file_id: uuid.UUID = Field(..., description="削除されたファイルのID")
    message: str = Field(..., description="削除成功メッセージ")


class FileUsageItem(BaseCamelCaseModel):
    """ファイル使用情報アイテム。

    ファイルがどこで使用されているかの個別情報。

    Attributes:
        usage_type (str): 使用タイプ（analysis_session/driver_tree）
        target_id (uuid.UUID): 使用先のID
        target_name (str): 使用先の名前
        sheet_name (str | None): シート名
        used_at (datetime): 使用日時
    """

    usage_type: str = Field(..., description="使用タイプ（analysis_session/driver_tree）")
    target_id: uuid.UUID = Field(..., description="使用先のID")
    target_name: str = Field(..., description="使用先の名前")
    sheet_name: str | None = Field(default=None, description="シート名")
    used_at: datetime = Field(..., description="使用日時")


class ProjectFileUsageResponse(BaseCamelCaseModel):
    """プロジェクトファイル使用状況レスポンススキーマ。

    ファイルの使用状況を返却します。

    Attributes:
        file_id (uuid.UUID): ファイルID
        filename (str): ファイル名
        analysis_session_count (int): 分析セッションでの使用数
        driver_tree_count (int): ドライバーツリーでの使用数
        total_usage_count (int): 総使用数
        usages (list[FileUsageItem]): 使用情報リスト

    Example:
        >>> response = ProjectFileUsageResponse(
        ...     file_id=uuid.uuid4(),
        ...     filename="data.xlsx",
        ...     analysis_session_count=2,
        ...     driver_tree_count=1,
        ...     total_usage_count=3,
        ...     usages=[...]
        ... )
    """

    file_id: uuid.UUID = Field(..., description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    analysis_session_count: int = Field(default=0, description="分析セッションでの使用数")
    driver_tree_count: int = Field(default=0, description="ドライバーツリーでの使用数")
    total_usage_count: int = Field(default=0, description="総使用数")
    usages: list[FileUsageItem] = Field(default_factory=list, description="使用情報リスト")
