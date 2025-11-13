"""サンプルAPI v1 エンドポイント。

このパッケージには、サンプルアプリケーション用のエンドポイントが含まれています。
実装の参考例として、基本的なCRUD操作、認証、ファイル管理、エージェント機能を提供します。

提供されるエンドポイント:
    - sample_users: ユーザー認証と管理
    - sample_files: ファイルアップロードと管理
    - sample_sessions: セッション管理とメッセージング
    - sample_agents: AIエージェントチャット機能

Note:
    これらはサンプル実装です。本番環境に適用する際は、
    プロジェクトの要件に合わせてカスタマイズしてください。
"""

from app.api.routes.v1.sample.sample_agents import sample_agents_router
from app.api.routes.v1.sample.sample_files import sample_files_router
from app.api.routes.v1.sample.sample_sessions import sample_sessions_router
from app.api.routes.v1.sample.sample_users import sample_users_router

__all__ = [
    "sample_agents_router",
    "sample_files_router",
    "sample_sessions_router",
    "sample_users_router",
]
