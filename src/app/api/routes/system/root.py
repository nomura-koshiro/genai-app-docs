"""ルートエンドポイント。

このモジュールは、APIのルートパス（/）にアクセスした際の
ウェルカムメッセージとバージョン情報を提供します。

Endpoints:
    GET /: アプリケーション基本情報
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    """ルートエンドポイント - APIの基本情報を返します。

    アプリケーションのウェルカムメッセージとバージョン情報、
    ドキュメントへのリンクを提供します。APIが正常に起動しているかの
    簡易チェックにも使用できます。

    Returns:
        dict: アプリケーション基本情報
            - message (str): ウェルカムメッセージ
            - version (str): アプリケーションバージョン（例: "0.1.0"）
            - docs (str): Swagger UIドキュメントのパス（"/docs"）

    Example:
        >>> # cURLでアクセス
        >>> $ curl http://localhost:8000/
        >>> {
        >>>   "message": "Welcome to AI Agent App",
        >>>   "version": "0.1.0",
        >>>   "docs": "/docs"
        >>> }

    Note:
        - 認証不要のパブリックエンドポイントです
        - ロードバランサーのヘルスチェックには /health を使用してください
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
    }
