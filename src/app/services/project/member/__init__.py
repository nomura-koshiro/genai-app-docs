"""プロジェクトメンバー管理サービスモジュール。

このモジュールは、プロジェクトメンバーの管理に関する全てのビジネスロジックを提供します。
各機能は責任ごとに分割されたクラスで実装されています。

モジュール構成:
    - service: ファサードサービス（推奨）
    - authorization: 権限チェック専門サービス
    - adder: メンバー追加専門サービス
    - updater: メンバー更新専門サービス
    - remover: メンバー削除・退出専門サービス

使用例:
    >>> from app.services.project.member import ProjectMemberService
    >>> from app.schemas.project.member import ProjectMemberCreate
    >>>
    >>> async with get_db() as db:
    ...     member_service = ProjectMemberService(db)
    ...     member = await member_service.add_member(
    ...         project_id, member_data, added_by=manager_id
    ...     )
"""

from app.services.project.member.adder import ProjectMemberAdder
from app.services.project.member.authorization import (
    ProjectMemberAuthorizationChecker,
)
from app.services.project.member.remover import ProjectMemberRemover
from app.services.project.member.service import ProjectMemberService
from app.services.project.member.updater import ProjectMemberUpdater

__all__ = [
    "ProjectMemberService",
    "ProjectMemberAuthorizationChecker",
    "ProjectMemberAdder",
    "ProjectMemberUpdater",
    "ProjectMemberRemover",
]
