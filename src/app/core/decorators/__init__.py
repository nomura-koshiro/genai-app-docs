"""デコレータパッケージ。

すべてのデコレータをここから一括エクスポートします。
横断的関心事(ログ記録、キャッシュ、トランザクション、エラーハンドリングなど)を
デコレータとして提供し、コードの重複を削減します。

Note:
    権限検証（認可）は app.api.core.dependencies.authorization で
    FastAPI Dependency方式で提供されています。
"""

from app.core.decorators.basic import async_timeout, log_execution, measure_performance
from app.core.decorators.data_access import cache_result, transactional
from app.core.decorators.error_handling import handle_service_errors
from app.core.decorators.reliability import retry_on_error

__all__ = [
    # Basic - 基本機能
    "log_execution",
    "measure_performance",
    "async_timeout",
    # Security - セキュリティ（エラーハンドリング）
    "handle_service_errors",
    # Data Access - データアクセス
    "transactional",
    "cache_result",
    # Reliability - 信頼性向上
    "retry_on_error",
]
