"""ロール関連のEnum定義。

このモジュールは、システムロールとプロジェクトロールをEnumで定義します。
"""

from enum import StrEnum


class SystemUserRole(StrEnum):
    """システムレベルのロール定義。

    Values:
        SYSTEM_ADMIN: システム管理者（全プロジェクトアクセス可能、システム設定変更可能）
        USER: 一般ユーザー（デフォルト、プロジェクト単位でアクセス制御）
    """

    SYSTEM_ADMIN = "system_admin"
    USER = "user"


class ProjectRole(StrEnum):
    """プロジェクトレベルのロール定義。

    Values:
        PROJECT_MANAGER: プロジェクトマネージャー（最高権限）
            - プロジェクト削除
            - プロジェクト設定変更
            - メンバー追加・削除・ロール変更（全ロール）
            - ファイルのアップロード・ダウンロード・削除
        PROJECT_MODERATOR: 権限管理者（メンバー管理担当）
            - メンバー追加・削除
            - ロール変更（VIEWER/MEMBER/PROJECT_MODERATORのみ）
            - ファイルのアップロード・ダウンロード
            - プロジェクト内の編集
        MEMBER: 一般メンバー（編集可能）
            - ファイルのアップロード・ダウンロード
            - プロジェクト内の編集
        VIEWER: 閲覧者（閲覧のみ）
            - ファイルの閲覧・ダウンロードのみ
    """

    PROJECT_MANAGER = "project_manager"
    PROJECT_MODERATOR = "project_moderator"
    MEMBER = "member"
    VIEWER = "viewer"
