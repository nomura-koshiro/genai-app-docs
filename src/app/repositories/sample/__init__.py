"""サンプルリポジトリ。

このパッケージには、サンプルアプリケーション用のリポジトリクラスが含まれています。
データアクセス層の実装パターンの参考として利用できます。

提供されるリポジトリ:
    - SampleUserRepository: ユーザーデータのCRUD操作
    - SampleSessionRepository: セッションデータのCRUD操作
    - SampleFileRepository: ファイルメタデータのCRUD操作

アーキテクチャパターン:
    リポジトリパターンを採用し、データアクセスロジックをビジネスロジックから分離。
    各リポジトリは非同期SQLAlchemy操作を提供し、トランザクション管理を簡素化します。

使用例:
    >>> from app.repositories.sample import SampleUserRepository
    >>>
    >>> async with get_db() as db:
    ...     user_repo = SampleUserRepository(db)
    ...     user = await user_repo.get_by_email("user@example.com")

Note:
    これらはサンプル実装です。本番環境に適用する際は、
    プロジェクトの要件に合わせてカスタマイズしてください。
"""

from app.repositories.sample.sample_file import SampleFileRepository
from app.repositories.sample.sample_session import SampleSessionRepository
from app.repositories.sample.sample_user import SampleUserRepository

__all__ = [
    "SampleFileRepository",
    "SampleSessionRepository",
    "SampleUserRepository",
]
