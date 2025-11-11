"""サンプルデータベースモデル。

このパッケージには、サンプルアプリケーション用のデータベースモデルが含まれています。
SQLAlchemyを使用したモデル定義の参考実装として利用できます。

提供されるモデル:
    - SampleUser: サンプルユーザーモデル（認証機能付き）
    - SampleSession: セッション管理モデル
    - SampleMessage: メッセージ管理モデル
    - SampleFile: ファイルメタデータモデル

使用例:
    >>> from app.models.sample import SampleUser, SampleSession
    >>>
    >>> # ユーザー作成
    >>> user = SampleUser(email="user@example.com", hashed_password="...")
    >>>
    >>> # セッション作成
    >>> session = SampleSession(user_id=user.id, title="New Session")

Note:
    これらはサンプル実装です。本番環境に適用する際は、
    プロジェクトの要件に合わせてカスタマイズしてください。
"""

from app.models.sample.sample_file import SampleFile
from app.models.sample.sample_session import SampleMessage, SampleSession
from app.models.sample.sample_user import SampleUser

__all__ = [
    "SampleFile",
    "SampleMessage",
    "SampleSession",
    "SampleUser",
]
