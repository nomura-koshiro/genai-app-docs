"""テストデータシーダーパッケージ。"""

from sqlalchemy.ext.asyncio import AsyncSession

from .analysis_session import AnalysisSessionSeederMixin
from .base import TestDataSet
from .driver_tree import DriverTreeSeederMixin
from .project_file import ProjectFileSeederMixin
from .system_setting import SystemSettingSeederMixin


class TestDataSeeder(
    AnalysisSessionSeederMixin,
    DriverTreeSeederMixin,
    ProjectFileSeederMixin,
    SystemSettingSeederMixin,
):
    """テストデータの統合シーダークラス。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)


__all__ = ["TestDataSeeder", "TestDataSet"]
