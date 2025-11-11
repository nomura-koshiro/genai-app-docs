"""認可ロジックを一元管理するサービス。

このモジュールは、リソースへのアクセス権限を検証する認可（Authorization）ロジックを
提供します。認証（Authentication）とは異なり、ユーザーが特定のリソースにアクセスする
権限を持っているかを判断します。

主な認可パターン:
    1. 管理者権限の検証（スーパーユーザーのみ）

使用例:
    >>> from app.services.sample.sample_authorization import SampleAuthorizationService
    >>> from app.models.sample.sample_user import SampleUser
    >>>
    >>> # 管理者権限を検証
    >>> auth_service = SampleAuthorizationService()
    >>> auth_service.check_admin_access(current_user)
"""

from app.core.exceptions import AuthorizationError
from app.models.sample.sample_user import SampleUser


class SampleAuthorizationService:
    """リソースへのアクセス権限を管理する認可サービスクラス。

    このクラスは、アプリケーション全体で使用される認可ロジックを一元管理します。
    すべてのメソッドは静的メソッドとして実装され、状態を持たないため、
    依存性注入なしで直接呼び出すことができます。

    設計原則:
        - 単一責任の原則（SRP）: 認可ロジックのみを担当
        - オープン・クローズドの原則（OCP）: 新しい認可ルールの追加が容易
        - 依存性逆転の原則（DIP）: モデルの抽象化に依存

    Example:
        >>> from app.services.sample.sample_authorization import SampleAuthorizationService
        >>>
        >>> # 静的メソッドとして呼び出し
        >>> SampleAuthorizationService.check_admin_access(user)
        >>>
        >>> # または、インスタンス化して使用（どちらでも可）
        >>> auth = SampleAuthorizationService()
        >>> auth.check_admin_access(user)
    """

    @staticmethod
    def check_admin_access(current_user: SampleUser) -> None:
        """管理者（スーパーユーザー）権限を検証します。

        ユーザーがスーパーユーザーでない場合、例外を発生させます。
        管理者専用の危険な操作（全ユーザー削除、システム設定変更など）を
        実行する前に必ず呼び出してください。

        認可ルール:
            - current_user.is_superuser == True の場合のみアクセス許可

        Args:
            current_user (SampleUser): 現在の認証ユーザー

        Raises:
            AuthorizationError: ユーザーがスーパーユーザーでない場合

        Example:
            >>> # スーパーユーザーのアクセス
            >>> admin = SampleUser(id=1, is_superuser=True, ...)
            >>> SampleAuthorizationService.check_admin_access(admin)
            >>> # 例外なし
            >>>
            >>> # 一般ユーザーのアクセス
            >>> regular_user = SampleUser(id=2, is_superuser=False, ...)
            >>> SampleAuthorizationService.check_admin_access(regular_user)
            AuthorizationError: Superuser permission required

        Note:
            - 管理者権限は慎重に付与してください
            - 管理者専用エンドポイントには必ずこのチェックを実装してください
            - current_userは認証済み（is_active=True）であることが前提です
        """
        if not current_user.is_superuser:
            raise AuthorizationError("管理者権限が必要です", details={"user_id": current_user.id})
