"""テストデータシーダー基盤。"""

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectFile, ProjectMember, UserAccount


@dataclass
class TestDataSet:
    """テストデータセットを保持するコンテナ。"""

    users: list[UserAccount] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    members: list[ProjectMember] = field(default_factory=list)
    files: list[ProjectFile] = field(default_factory=list)


class BaseSeeder:
    """シーダー基底クラス。"""

    db: AsyncSession
    _created_data: TestDataSet

    def __init__(self, db: AsyncSession):
        self.db = db
        self._created_data = TestDataSet()

    @property
    def created_data(self) -> TestDataSet:
        """作成されたテストデータを取得。"""
        return self._created_data
