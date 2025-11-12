"""PPT Generator機能用のPydanticスキーマ定義。

このモジュールは、PPTファイルの生成・ダウンロード・画像エクスポート機能に関連する
リクエスト/レスポンススキーマを定義します。

主なスキーマ:
    - PPTDownloadRequest: PPTダウンロードリクエスト
    - PPTSlideExportRequest: 選択されたスライドのエクスポートリクエスト
    - PPTSlideImageRequest: スライド画像取得リクエスト
    - QuestionDownloadRequest: 質問データダウンロードリクエスト

使用例:
    >>> from app.schemas.ppt_generator import PPTDownloadRequest
    >>>
    >>> request = PPTDownloadRequest(
    ...     package="market-analysis",
    ...     phase="phase1",
    ...     template="template_a"
    ... )
"""

from pydantic import BaseModel, Field


class PPTDownloadRequest(BaseModel):
    """PPTファイルダウンロードリクエスト。

    Attributes:
        package: パッケージ名（例: "market-analysis"）
        phase: フェーズ名（例: "phase1", "phase2"）
        template: テンプレート名（例: "template_a"）

    Example:
        >>> request = PPTDownloadRequest(
        ...     package="market-analysis",
        ...     phase="phase1",
        ...     template="template_a"
        ... )
        >>> print(request.package)
        market-analysis
    """

    package: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="パッケージ名",
        examples=["market-analysis"],
    )
    phase: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="フェーズ名",
        examples=["phase1"],
    )
    template: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="テンプレート名",
        examples=["template_a"],
    )

    class Config:
        """Pydantic設定。"""

        json_schema_extra = {
            "example": {
                "package": "market-analysis",
                "phase": "phase1",
                "template": "template_a",
            }
        }


class PPTSlideExportRequest(BaseModel):
    """選択されたスライドのエクスポートリクエスト。

    Attributes:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        slide_numbers: スライド番号のカンマ区切り文字列（例: "1,3,5,7"）

    Example:
        >>> request = PPTSlideExportRequest(
        ...     package="market-analysis",
        ...     phase="phase1",
        ...     template="template_a",
        ...     slide_numbers="1,3,5,7"
        ... )
        >>> print(request.slide_numbers)
        1,3,5,7
    """

    package: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="パッケージ名",
    )
    phase: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="フェーズ名",
    )
    template: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="テンプレート名",
    )
    slide_numbers: str = Field(
        ...,
        pattern=r"^\d+(,\d+)*$",
        description="スライド番号のカンマ区切り文字列（例: '1,3,5,7'）",
        examples=["1,3,5,7"],
    )

    class Config:
        """Pydantic設定。"""

        json_schema_extra = {
            "example": {
                "package": "market-analysis",
                "phase": "phase1",
                "template": "template_a",
                "slide_numbers": "1,3,5,7",
            }
        }


class PPTSlideImageRequest(BaseModel):
    """スライド画像取得リクエスト。

    Attributes:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        slide_number: スライド番号（1から開始）

    Example:
        >>> request = PPTSlideImageRequest(
        ...     package="market-analysis",
        ...     phase="phase1",
        ...     template="template_a",
        ...     slide_number=5
        ... )
        >>> print(request.slide_number)
        5
    """

    package: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="パッケージ名",
    )
    phase: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="フェーズ名",
    )
    template: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="テンプレート名",
    )
    slide_number: int = Field(
        ...,
        ge=1,
        le=1000,
        description="スライド番号（1から開始）",
        examples=[5],
    )

    class Config:
        """Pydantic設定。"""

        json_schema_extra = {
            "example": {
                "package": "market-analysis",
                "phase": "phase1",
                "template": "template_a",
                "slide_number": 5,
            }
        }


class QuestionDownloadRequest(BaseModel):
    """質問データダウンロードリクエスト。

    Attributes:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        question_type: 質問タイプ（Excelシート名）

    Example:
        >>> request = QuestionDownloadRequest(
        ...     package="market-analysis",
        ...     phase="phase1",
        ...     template="template_a",
        ...     question_type="customer_survey"
        ... )
        >>> print(request.question_type)
        customer_survey
    """

    package: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="パッケージ名",
    )
    phase: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="フェーズ名",
    )
    template: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="テンプレート名",
    )
    question_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="質問タイプ（Excelシート名）",
        examples=["customer_survey"],
    )

    class Config:
        """Pydantic設定。"""

        json_schema_extra = {
            "example": {
                "package": "market-analysis",
                "phase": "phase1",
                "template": "template_a",
                "question_type": "customer_survey",
            }
        }


class PPTUploadRequest(BaseModel):
    """PPTファイルアップロードリクエスト。

    Attributes:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        file_name: ファイル名

    Example:
        >>> request = PPTUploadRequest(
        ...     package="market-analysis",
        ...     phase="phase1",
        ...     template="template_a",
        ...     file_name="presentation.pptx"
        ... )
        >>> print(request.file_name)
        presentation.pptx
    """

    package: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="パッケージ名",
    )
    phase: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="フェーズ名",
    )
    template: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="テンプレート名",
    )
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="ファイル名",
        examples=["presentation.pptx"],
    )

    class Config:
        """Pydantic設定。"""

        json_schema_extra = {
            "example": {
                "package": "market-analysis",
                "phase": "phase1",
                "template": "template_a",
                "file_name": "presentation.pptx",
            }
        }


class PPTUploadResponse(BaseModel):
    """PPTファイルアップロードレスポンス。

    Attributes:
        success: アップロード成功フラグ
        file_path: アップロードされたファイルのストレージパス
        file_size: ファイルサイズ（バイト）

    Example:
        >>> response = PPTUploadResponse(
        ...     success=True,
        ...     file_path="market-analysis/phase1/template_a/presentation.pptx",
        ...     file_size=1024000
        ... )
        >>> print(response.success)
        True
    """

    success: bool = Field(..., description="アップロード成功フラグ")
    file_path: str = Field(..., description="ストレージパス")
    file_size: int = Field(..., ge=0, description="ファイルサイズ（バイト）")

    class Config:
        """Pydantic設定。"""

        json_schema_extra = {
            "example": {
                "success": True,
                "file_path": "market-analysis/phase1/template_a/presentation.pptx",
                "file_size": 1024000,
            }
        }
