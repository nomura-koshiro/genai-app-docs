"""基本デコレータのテスト。

このテストは、basic.pyの基本的なデコレータ機能を検証します。
データベース接続を必要としません。
"""

import asyncio
from unittest.mock import patch

import pytest

from app.api.decorators import async_timeout, log_execution, measure_performance
from app.core.exceptions import ValidationError

# データベース不要のユニットテストとしてマーク
pytestmark = pytest.mark.skip_db


# セッションスコープのフィクスチャをオーバーライドしてデータベースセットアップをスキップ
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """デコレータテストではデータベースセットアップをスキップ。"""
    yield


class TestMeasurePerformance:
    """measure_performanceデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_performance_measurement(self):
        """[test_basic-001] 実行時間が測定されログに記録されることをテスト。"""

        @measure_performance
        async def test_func():
            await asyncio.sleep(0.1)
            return "result"

        with patch("app.api.decorators.basic.logger") as mock_logger:
            result = await test_func()

            assert result == "result"
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args
            # structlog形式: logger.info("event_name", key=value, ...)
            assert call_args[0][0] == "performance_measurement"
            assert call_args[1]["function"] == "test_func"
            assert call_args[1]["duration_seconds"] >= 0.1


class TestLogExecution:
    """log_executionデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_basic_logging(self):
        """[test_basic-002] 基本的なログ記録がされることをテスト。"""

        @log_execution(level="info")
        async def test_func():
            return "result"

        with patch("app.api.decorators.basic.logger") as mock_logger:
            result = await test_func()

            assert result == "result"
            assert mock_logger.info.call_count == 2  # Executing と Completed
            calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert "Executing: test_func" in calls[0]
            assert "Completed: test_func" in calls[1]


class TestAsyncTimeout:
    """async_timeoutデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_successful_execution_within_timeout(self):
        """[test_basic-003] タイムアウト時間内に正常終了する場合、結果が返却されることをテスト。"""

        @async_timeout(1.0)
        async def test_func():
            await asyncio.sleep(0.1)
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_raises_validation_error(self):
        """[test_basic-004] タイムアウト時にValidationErrorが送出されることをテスト。"""

        @async_timeout(0.1)
        async def test_func():
            await asyncio.sleep(1.0)
            return "should not reach"

        with pytest.raises(ValidationError) as exc_info:
            await test_func()

        assert "タイムアウト" in exc_info.value.message
        assert exc_info.value.details["timeout_seconds"] == 0.1
        assert exc_info.value.details["function"] == "test_func"
