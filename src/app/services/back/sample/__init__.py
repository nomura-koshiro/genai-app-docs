"""サンプルビジネスロジックサービス。

このパッケージには、サンプルアプリケーション用のサービスクラスが含まれています。
ビジネスロジック層の実装パターンの参考として利用できます。

提供されるサービス:
    - SampleUserService: ユーザー管理とパスワード認証
    - SampleSessionService: セッションとメッセージ管理
    - SampleFileService: ファイルアップロードと保存
    - SampleAgentService: AIエージェントチャット機能
    - SampleAuthorizationService: リソースアクセス権限チェック

アーキテクチャパターン:
    サービス層は、複数のリポジトリを組み合わせて複雑なビジネスロジックを実装します。
    トランザクション境界、バリデーション、認可チェックなどを担当します。

使用例:
    >>> from app.services.sample import SampleUserService
    >>> from app.schemas.sample import SampleUserCreate
    >>>
    >>> async with get_db() as db:
    ...     user_service = SampleUserService(db)
    ...     user = await user_service.create_user(
    ...         SampleUserCreate(email="user@example.com", password="...")
    ...     )

Note:
    これらはサンプル実装です。本番環境に適用する際は、
    プロジェクトの要件に合わせてカスタマイズしてください。
"""

from app.services.sample.sample_agent import SampleAgentService
from app.services.sample.sample_authorization import SampleAuthorizationService
from app.services.sample.sample_file import SampleFileService
from app.services.sample.sample_session import SampleSessionService
from app.services.sample.sample_user import SampleUserService

__all__ = [
    "SampleAgentService",
    "SampleAuthorizationService",
    "SampleFileService",
    "SampleSessionService",
    "SampleUserService",
]
