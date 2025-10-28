"""デコレータパッケージ。

すべてのデコレータをここから一括エクスポートします。
横断的関心事(ログ記録、キャッシュ、トランザクション、権限検証など)を
デコレータとして提供し、コードの重複を削減します。
"""

from app.api.decorators.basic import async_timeout, log_execution, measure_performance
from app.api.decorators.data_access import cache_result, transactional
from app.api.decorators.reliability import retry_on_error
from app.api.decorators.security import handle_service_errors, validate_permissions

__all__ = [
    # Basic - 基本機能
    "log_execution",
    "measure_performance",
    "async_timeout",
    # Security - セキュリティ
    "validate_permissions",
    "handle_service_errors",
    # Data Access - データアクセス
    "transactional",
    "cache_result",
    # Reliability - 信頼性向上
    "retry_on_error",
]
