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

from app.api.routes.v1.sample import (
    sample_agents,
    sample_files,
    sample_sessions,
    sample_users,
)

__all__ = [
    "sample_agents",
    "sample_files",
    "sample_sessions",
    "sample_users",
]
