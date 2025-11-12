"""PPT Generator関連のビジネスロジックサービス。

このモジュールは、PowerPointプレゼンテーション生成機能に関連するビジネスロジックを提供します。

主なサービス:
    - PPTGeneratorService: PPT生成サービス（スライド作成、画像変換、ダウンロード）

使用例:
    >>> from app.services.ppt_generator import PPTGeneratorService
    >>> from app.schemas.ppt_generator import PPTUploadRequest
    >>>
    >>> async with get_db() as db:
    ...     ppt_service = PPTGeneratorService(db)
    ...     result = await ppt_service.upload_ppt(
    ...         project_id=project_id,
    ...         upload_request=PPTUploadRequest(...)
    ...     )
"""

from app.services.ppt_generator.ppt_generator import PPTGeneratorService

__all__ = ["PPTGeneratorService"]
