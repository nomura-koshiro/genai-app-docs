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

from app.core.app_factory import create_app
from app.core.config import settings
from app.core.logging import setup_logging

# ロギングを設定
setup_logging()

# FastAPIアプリケーションインスタンスを作成
app = create_app()


def main():
    """コマンドライン（CLI）からアプリケーションを起動するエントリーポイント。

    Uvicornサーバーを使用してFastAPIアプリケーションを起動します。
    開発環境では自動リロード（--reload）が有効になります。

    起動設定（app.config.settingsから取得）:
        - host: バインドするホストアドレス（デフォルト: 0.0.0.0）
        - port: リスニングポート（デフォルト: 8000）
        - reload: DEBUGモードの場合、ファイル変更時に自動リロード

    使用方法:
        コマンドラインから実行:
            $ python -m app.main
            または
            $ uv run python -m app.main

        または、Uvicornを直接使用（推奨）:
            $ uvicorn app.main:app --reload
            $ uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

    Note:
        - この関数は if __name__ == "__main__" ブロックから呼び出されます
        - 本番環境では uvicorn コマンドを直接使用し、ワーカー数を指定してください:
          $ uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
        - 開発中は `uvicorn app.main:app --reload` が便利です
        - Dockerコンテナ内では --host 0.0.0.0 を指定してください（デフォルト設定済み）
    """
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
