"""PPT Generator API v1 エンドポイント。

このパッケージには、PowerPoint生成機能用のエンドポイントが含まれています。

提供される機能:
    - PPTファイルのアップロード
    - スライドの画像変換
    - スライドのエクスポート
    - PPTファイルのダウンロード
    - 質問データのダウンロード

使用例:
    >>> # PPTアップロード
    >>> POST /api/v1/ppt-generator/upload
    >>> {"project_id": "...", "file_data": "base64..."}
    >>>
    >>> # スライド画像変換
    >>> POST /api/v1/ppt-generator/slide-image
    >>> {"project_id": "...", "slide_number": 1}
"""

from app.api.routes.v1.back.ppt_generator.ppt_generator import ppt_generator_router

__all__ = ["ppt_generator_router"]
