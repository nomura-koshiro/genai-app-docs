"""FastAPIアプリケーションのエントリーポイント。

このモジュールは、AIエージェントアプリケーションのバックエンドAPIサーバーを起動します。
FastAPIフレームワークを使用し、LangGraph AIエージェント、ファイル管理、
セッション管理などの機能を提供します。

起動方法:
    開発環境:
        $ uv run python -m app.main
        または
        $ uv run uvicorn app.main:app --reload

    本番環境:
        $ uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

環境変数:
    必須設定（.env ファイルまたは環境変数）:
        - DATABASE_URL: PostgreSQL接続文字列
        - SECRET_KEY: JWT署名用シークレットキー（32文字以上）
        - LLM_PROVIDER: "openai" | "azure_openai" | "anthropic"
        - {PROVIDER}_API_KEY: 対応するLLMプロバイダのAPIキー

    オプション設定:
        - REDIS_URL: Redis接続文字列（キャッシュ用、なくても動作）
        - ALLOWED_ORIGINS: CORS許可オリジン（本番環境では必須）
        - DEBUG: デバッグモード（デフォルト: False）

ドキュメント:
    起動後、以下のURLでAPIドキュメントを確認できます:
        - Swagger UI: http://localhost:8000/docs
        - ReDoc: http://localhost:8000/redoc
        - OpenAPI JSON: http://localhost:8000/openapi.json
"""

import sys

from app.core.app_factory import create_app
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

# ロギングを設定
setup_logging()
logger = get_logger(__name__)

# FastAPIアプリケーションインスタンスを作成
app = create_app()


def main() -> None:
    """Uvicornサーバーを起動します。

    開発環境では自動リロードが有効になります。
    本番環境では複数ワーカーで実行されます（WORKERS設定による）。

    起動設定:
        - host: バインドするホストアドレス（デフォルト: 0.0.0.0）
        - port: リスニングポート（デフォルト: 8000）
        - reload: DEBUGモードの場合、ファイル変更時に自動リロード
        - workers: 本番環境でのワーカー数（開発環境では常に1）

    使用方法:
        $ python -m app.main
        $ uv run uvicorn app.main:app --reload

    本番環境:
        $ python -m app.main  # WORKERS設定が適用される
        または
        $ uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

    Note:
        - reloadモードとworkersは同時に使用できません
        - 開発環境（DEBUG=True）では常にworkers=1で起動します

    Raises:
        SystemExit: サーバー起動に失敗した場合、終了コード1で終了します。
    """
    import uvicorn

    try:
        # ワーカー数の決定（reloadモードではworkers=1固定）
        workers = 1 if settings.DEBUG else settings.WORKERS

        logger.info(
            "サーバー起動中",
            host=settings.HOST,
            port=settings.PORT,
            environment=settings.ENVIRONMENT,
            debug=settings.DEBUG,
            workers=workers,
        )
        logger.info(f"ドキュメント: http://{settings.HOST}:{settings.PORT}/docs")

        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            workers=workers,
        )
    except Exception as e:
        logger.exception(
            "アプリケーション起動エラー",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
