"""分析 API v1 エンドポイント。

このパッケージには、分析機能用のエンドポイントが含まれています。

提供されるルーター:
    - analysis_templates_router: 分析テンプレート管理（課題カタログ取得）
    - analysis_sessions_router: 分析セッション管理（作成、更新、削除、一覧取得）

主な機能:
    テンプレート:
        - 課題カタログ一覧の取得
        - 課題詳細の取得

    セッション:
        - 分析セッションの作成・更新・削除
        - セッション一覧の取得
        - セッション詳細の取得
        - ステップの作成・更新・削除
        - スナップショットの保存・取得
        - ファイルのアップロード・削除

使用例:
    >>> # 課題カタログ取得
    >>> GET /api/v1/analysis/templates
    >>>
    >>> # セッション作成
    >>> POST /api/v1/analysis/sessions
    >>> {"project_id": "...", "issue_id": "..."}
"""

from app.api.routes.v1.analysis.analysis_session import analysis_sessions_router
from app.api.routes.v1.analysis.analysis_template import analysis_templates_router

__all__ = ["analysis_templates_router", "analysis_sessions_router"]
