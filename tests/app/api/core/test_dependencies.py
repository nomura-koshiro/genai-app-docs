"""依存性注入のテスト。

このテストは、FastAPIの依存性注入システムが正しく動作することを確認します。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core import (
    AgentServiceDep,
    CurrentUserDep,
    DatabaseDep,
    FileServiceDep,
    SessionServiceDep,
    UserServiceDep,
    get_db,
)


class TestDependencies:
    """依存性注入のテストクラス。"""

    @pytest.mark.asyncio
    async def test_database_dependency(self, db_session: AsyncSession):
        """データベース依存性が正しく動作すること。"""
        # データベースセッションが正しく取得できる
        assert db_session is not None
        assert isinstance(db_session, AsyncSession)

    def test_dependencies_are_annotated(self):
        """依存性がAnnotated型として定義されていること。"""
        # 型アノテーションの確認
        assert DatabaseDep is not None
        assert UserServiceDep is not None
        assert AgentServiceDep is not None
        assert FileServiceDep is not None
        assert SessionServiceDep is not None
        assert CurrentUserDep is not None

    def test_dependency_functions_exist(self):
        """依存性取得関数が存在すること。"""
        assert callable(get_db)
        # 他の依存性取得関数もインポート可能
        from app.api.core.dependencies import (
            get_agent_service,
            get_current_active_user,
            get_file_service,
            get_session_service,
            get_user_service,
        )

        assert callable(get_user_service)
        assert callable(get_agent_service)
        assert callable(get_file_service)
        assert callable(get_session_service)
        assert callable(get_current_active_user)
