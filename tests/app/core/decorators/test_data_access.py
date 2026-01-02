"""データアクセスデコレータのテスト。

このテストは、data_access.pyのデータアクセス関連デコレータを検証します。
データベース接続を必要としません。
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.decorators import cache_result, transactional

# データベース不要のユニットテストとしてマーク
pytestmark = pytest.mark.skip_db


# セッションスコープのフィクスチャをオーバーライドしてデータベースセットアップをスキップ
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """デコレータテストではデータベースセットアップをスキップ。"""
    yield


class TestCacheResult:
    """cache_resultデコレータのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cache_state,expected_from_cache",
        [
            ("hit", True),
            ("miss", False),
        ],
        ids=["cache_hit", "cache_miss"],
    )
    async def test_cache_result_scenarios(self, cache_state, expected_from_cache):
        """[test_data_access-001,002] キャッシュの動作をテスト（ヒット/ミス）。"""
        # Arrange
        mock_cache = AsyncMock()
        if cache_state == "hit":
            mock_cache.get.return_value = {"cached": "data"}
        else:
            mock_cache.get.return_value = None  # キャッシュミス

        # Act
        with patch("app.core.decorators.data_access.cache_manager", mock_cache):

            @cache_result(ttl=300, key_prefix="test")
            async def test_func(arg1: int):
                return {"db": "data"}

            result = await test_func(123)

            # Assert
            if expected_from_cache:
                # キャッシュヒット時にキャッシュから返却される
                assert result == {"cached": "data"}
                assert mock_cache.get.called
                # キャッシュヒットなので関数は実行されない（dbデータは返らない）
            else:
                # キャッシュミス時に関数実行後キャッシュに保存される
                assert result == {"db": "data"}
                assert mock_cache.get.called
                assert mock_cache.set.called
                # setが正しい引数で呼ばれているか確認
                set_call_args = mock_cache.set.call_args
                assert set_call_args[0][1] == {"db": "data"}  # value
                assert set_call_args[0][2] == 300  # ttl


class TestTransactional:
    """transactionalデコレータのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "should_raise_error,expected_commit,expected_rollback",
        [
            (False, True, False),  # 正常終了時
            (True, False, True),   # 例外発生時
        ],
        ids=["success_commits", "error_rollbacks"],
    )
    async def test_transactional_scenarios(
        self, should_raise_error, expected_commit, expected_rollback
    ):
        """[test_data_access-003,004] トランザクションの動作をテスト（成功/失敗）。"""
        # Arrange
        mock_db = AsyncMock()

        class TestService:
            def __init__(self):
                self.db = mock_db

            @transactional
            async def test_method(self):
                if should_raise_error:
                    raise ValueError("エラー")
                return "success"

        service = TestService()

        # Act & Assert
        if should_raise_error:
            # 例外発生時にロールバックされる
            with pytest.raises(ValueError):
                await service.test_method()
        else:
            # 正常終了時にコミットされる
            result = await service.test_method()
            assert result == "success"

        # Assert
        assert mock_db.commit.called == expected_commit
        assert mock_db.rollback.called == expected_rollback
