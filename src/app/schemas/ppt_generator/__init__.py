"""PPT Generator関連のPydanticスキーマ。

このモジュールは、PowerPoint生成機能に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    - PPTUploadRequest: PPTアップロードリクエスト
    - PPTUploadResponse: PPTアップロードレスポンス
    - PPTDownloadRequest: PPTダウンロードリクエスト
    - PPTSlideExportRequest: スライドエクスポートリクエスト
    - PPTSlideImageRequest: スライド画像変換リクエスト
    - QuestionDownloadRequest: 質問ダウンロードリクエスト

使用例:
    >>> from app.schemas.ppt_generator import PPTUploadRequest
    >>> upload_request = PPTUploadRequest(
    ...     project_id=project_id,
    ...     file_data="base64_encoded_ppt_data"
    ... )
"""

from app.schemas.ppt_generator.ppt_generator import (
    PPTDownloadRequest,
    PPTSlideExportRequest,
    PPTSlideImageRequest,
    PPTUploadRequest,
    PPTUploadResponse,
    QuestionDownloadRequest,
)

__all__ = [
    "PPTDownloadRequest",
    "PPTSlideExportRequest",
    "PPTSlideImageRequest",
    "PPTUploadRequest",
    "PPTUploadResponse",
    "QuestionDownloadRequest",
]
