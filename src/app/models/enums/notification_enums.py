"""通知関連のEnum定義。

このモジュールは、通知機能で使用する定数をEnumで定義します。
"""

from enum import StrEnum


class NotificationTypeEnum(StrEnum):
    """通知タイプ。

    Values:
        MEMBER_ADDED: メンバー追加
        MEMBER_REMOVED: メンバー削除
        SESSION_COMPLETE: セッション完了
        FILE_UPLOADED: ファイルアップロード
        TREE_UPDATED: ツリー更新
        PROJECT_INVITATION: プロジェクト招待
        SYSTEM_ANNOUNCEMENT: システムお知らせ
    """

    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    SESSION_COMPLETE = "session_complete"
    FILE_UPLOADED = "file_uploaded"
    TREE_UPDATED = "tree_updated"
    PROJECT_INVITATION = "project_invitation"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class ReferenceTypeEnum(StrEnum):
    """参照タイプ。

    Values:
        PROJECT: プロジェクト
        SESSION: セッション
        FILE: ファイル
        TREE: ツリー
    """

    PROJECT = "project"
    SESSION = "session"
    FILE = "file"
    TREE = "tree"
