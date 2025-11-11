"""プロジェクトメンバー管理サービスモジュール。

このモジュールは、プロジェクトメンバーの管理に関する全てのビジネスロジックを提供します。
各機能は責任ごとに分割されたクラスで実装されています。

モジュール構成:
    - member_facade: ファサードサービス（推奨）
    - authorization_checker: 権限チェック専門サービス
    - member_adder: メンバー追加専門サービス
    - member_updater: メンバー更新専門サービス
    - member_remover: メンバー削除・退出専門サービス

使用例:
    >>> from app.services.project_member import ProjectMemberService
    >>> from app.schemas.project_member import ProjectMemberCreate
    >>>
    >>> async with get_db() as db:
    ...     member_service = ProjectMemberService(db)
    ...     member = await member_service.add_member(
    ...         project_id, member_data, added_by=manager_id
    ...     )
"""

from app.services.project_member.authorization_checker import (
    ProjectMemberAuthorizationChecker,
)
from app.services.project_member.member_adder import ProjectMemberAdder
from app.services.project_member.member_facade import ProjectMemberService
from app.services.project_member.member_remover import ProjectMemberRemover
from app.services.project_member.member_updater import ProjectMemberUpdater

__all__ = [
    "ProjectMemberService",
    "ProjectMemberAuthorizationChecker",
    "ProjectMemberAdder",
    "ProjectMemberUpdater",
    "ProjectMemberRemover",
]
