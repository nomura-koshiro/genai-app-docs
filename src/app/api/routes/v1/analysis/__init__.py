"""分析API v1 エンドポイント。

このパッケージには、データ分析機能用のエンドポイントが含まれています。

提供されるルーター:
    - analysis_router: 分析セッション管理、ファイルアップロード、ステップ実行、チャット
    - analysis_templates_router: 分析テンプレート管理（施策・課題テンプレート）

主な機能:
    - 分析セッションの作成・管理
    - CSVファイルのアップロードと解析
    - フィルタ、集計、変換、サマリーステップの実行
    - AIエージェントとのチャット
    - 分析テンプレートの管理

使用例:
    >>> # 分析セッション作成
    >>> POST /api/v1/analysis/sessions
    >>> {"project_id": "...", "validation_config": {...}}
    >>>
    >>> # ファイルアップロード
    >>> POST /api/v1/analysis/sessions/{session_id}/files
    >>> {"file_name": "data.csv", "file_data": "base64..."}
"""

from app.api.routes.v1.analysis.analysis import analysis_router
from app.api.routes.v1.analysis.templates import analysis_templates_router

__all__ = ["analysis_router", "analysis_templates_router"]
