"""OpenAPI/Swaggerドキュメント生成スクリプト。

FastAPIアプリケーションからOpenAPIスキーマを抽出し、
HTML形式でドキュメントを自動生成します。

生成されるファイル:
    - docs/api/openapi.json - OpenAPI 3.1.0 スキーマ（JSON形式）
    - docs/api/api-docs.html - Swagger UIを含むスタンドアロンHTML
    - docs/api/redoc.html - ReDocを含むスタンドアロンHTML

使用方法:
    $ cd C:/developments/genai-app-docs
    $ uv run python scripts/generate_openapi_docs.py

    または
    $ uv run hatch run generate-docs

前提条件:
    - FastAPIアプリケーションが正常に起動できること
    - .envファイルが設定されていること（DATABASE_URLなど）
"""

import io
import json
import sys
from pathlib import Path

# Windows環境でのUnicode出力を有効化
if sys.platform == "win32":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8")

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(project_root))

from app.core.app_factory import create_app  # noqa: E402


def generate_openapi_docs() -> None:
    """OpenAPI/SwaggerドキュメントをHTML/JSON形式で生成します。

    出力先:
        - docs/api/openapi.json
        - docs/api/api-docs.html (Swagger UI)
        - docs/api/redoc.html (ReDoc)

    Raises:
        Exception: ドキュメント生成に失敗した場合
    """
    print("=" * 60)
    print("OpenAPIドキュメント生成")
    print("=" * 60)
    print()

    print("📚 FastAPIアプリケーションを読み込んでいます...")

    # FastAPIアプリケーションを作成
    app = create_app()

    # OpenAPIスキーマを取得
    openapi_schema = app.openapi()

    # 出力ディレクトリを作成
    docs_dir = Path(__file__).parent.parent / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 出力先: {docs_dir.relative_to(Path(__file__).parent.parent)}")
    print()

    # 1. OpenAPI JSONを出力
    print("🔄 OpenAPI JSONを生成中...")
    openapi_json_path = docs_dir / "openapi.json"
    with open(openapi_json_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {openapi_json_path.relative_to(Path(__file__).parent.parent)}")

    # 2. Swagger UI HTMLを生成
    print("🔄 Swagger UIを生成中...")
    swagger_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{openapi_schema.get("info", {}).get("title", "API")} - Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui.css">
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const spec = {json.dumps(openapi_schema, ensure_ascii=False)};

            SwaggerUIBundle({{
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>"""

    swagger_html_path = docs_dir / "api-docs.html"
    with open(swagger_html_path, "w", encoding="utf-8") as f:
        f.write(swagger_html)
    print(f"   ✅ {swagger_html_path.relative_to(Path(__file__).parent.parent)}")

    # 3. ReDoc HTMLを生成
    print("🔄 ReDocを生成中...")
    redoc_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{openapi_schema.get("info", {}).get("title", "API")} - ReDoc</title>
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <redoc spec-url="openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    <script>
        const spec = {json.dumps(openapi_schema, ensure_ascii=False)};
        Redoc.init(spec, {{}}, document.querySelector('redoc'));
    </script>
</body>
</html>"""

    redoc_html_path = docs_dir / "redoc.html"
    with open(redoc_html_path, "w", encoding="utf-8") as f:
        f.write(redoc_html)
    print(f"   ✅ {redoc_html_path.relative_to(Path(__file__).parent.parent)}")

    print()
    print("=" * 60)
    print("🎉 ドキュメント生成完了")
    print("=" * 60)
    print()
    print("📖 生成されたファイル:")
    print(f"   - {openapi_json_path.relative_to(Path(__file__).parent.parent)}")
    print(f"   - {swagger_html_path.relative_to(Path(__file__).parent.parent)}")
    print(f"   - {redoc_html_path.relative_to(Path(__file__).parent.parent)}")
    print()
    print("💡 ブラウザで開くには:")
    print(f"   {swagger_html_path}")


if __name__ == "__main__":
    try:
        generate_openapi_docs()
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ エラーが発生しました")
        print("=" * 60)
        print(f"   {type(e).__name__}: {e}")
        import traceback

        print()
        print("詳細:")
        traceback.print_exc()
        sys.exit(1)
