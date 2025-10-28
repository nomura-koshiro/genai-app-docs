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
        """実行時間が測定されログに記録されることをテスト。"""

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

    @pytest.mark.asyncio
    async def test_performance_measurement_with_error(self):
        """エラー発生時も実行時間が記録されることをテスト。"""

        @measure_performance
        async def test_func():
            await asyncio.sleep(0.05)
            raise ValueError("エラー")

        with patch("app.api.decorators.basic.logger") as mock_logger:
            with pytest.raises(ValueError):
                await test_func()

            # エラー発生でもfinallyブロックでログ記録される
            assert mock_logger.info.called


class TestLogExecution:
    """log_executionデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_basic_logging(self):
        """基本的なログ記録がされることをテスト。"""

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

    @pytest.mark.asyncio
    async def test_logging_with_args(self):
        """引数付きログ記録がされることをテスト。"""

        class TestService:
            @log_execution(level="info", include_args=True)
            async def test_method(self, arg1: int, arg2: str):
                return f"{arg1}:{arg2}"

        with patch("app.api.decorators.basic.logger") as mock_logger:
            service = TestService()
            result = await service.test_method(123, "test")

            assert result == "123:test"
            # 引数がログに含まれている（selfは除外）
            first_call_extra = mock_logger.info.call_args_list[0][1]["extra"]
            assert "args" in first_call_extra

    @pytest.mark.asyncio
    async def test_logging_with_result(self):
        """戻り値付きログ記録がされることをテスト。"""

        @log_execution(level="debug", include_result=True)
        async def test_func():
            return {"result": "data"}

        with patch("app.api.decorators.basic.logger") as mock_logger:
            result = await test_func()

            assert result == {"result": "data"}
            # 戻り値がログに含まれている
            second_call_extra = mock_logger.debug.call_args_list[1][1]["extra"]
            assert "result" in second_call_extra


class TestAsyncTimeout:
    """async_timeoutデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_successful_execution_within_timeout(self):
        """タイムアウト時間内に正常終了する場合、結果が返却されることをテスト。"""

        @async_timeout(1.0)
        async def test_func():
            await asyncio.sleep(0.1)
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_raises_validation_error(self):
        """タイムアウト時にValidationErrorが送出されることをテスト。"""

        @async_timeout(0.1)
        async def test_func():
            await asyncio.sleep(1.0)
            return "should not reach"

        with pytest.raises(ValidationError) as exc_info:
            await test_func()

        assert "タイムアウト" in exc_info.value.message
        assert exc_info.value.details["timeout_seconds"] == 0.1
        assert exc_info.value.details["function"] == "test_func"

    @pytest.mark.asyncio
    async def test_timeout_logs_error(self):
        """タイムアウト時にエラーログが記録されることをテスト。"""

        @async_timeout(0.05)
        async def test_func():
            await asyncio.sleep(0.5)
            return "should not reach"

        with patch("app.api.decorators.basic.logger") as mock_logger:
            with pytest.raises(ValidationError):
                await test_func()

            # エラーログが記録されている
            assert mock_logger.error.called
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "async_timeout_exceeded"
            assert call_args[1]["function"] == "test_func"
            assert call_args[1]["timeout_seconds"] == 0.05

    @pytest.mark.asyncio
    async def test_different_timeout_durations(self):
        """異なるタイムアウト時間が正しく適用されることをテスト。"""

        @async_timeout(0.2)
        async def fast_func():
            await asyncio.sleep(0.1)
            return "fast"

        @async_timeout(0.05)
        async def slow_func():
            await asyncio.sleep(0.2)
            return "slow"

        # fast_funcは成功
        result = await fast_func()
        assert result == "fast"

        # slow_funcはタイムアウト
        with pytest.raises(ValidationError):
            await slow_func()

    @pytest.mark.asyncio
    async def test_timeout_with_exception_in_function(self):
        """関数内で例外が発生した場合、タイムアウト前に例外が送出されることをテスト。"""

        @async_timeout(1.0)
        async def test_func():
            await asyncio.sleep(0.05)
            raise ValueError("関数内エラー")

        with pytest.raises(ValueError, match="関数内エラー"):
            await test_func()
