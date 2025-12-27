"""AnalysisSession シーダー。"""

import uuid
from typing import Any

from app.models import Project, ProjectFile, UserAccount
from app.models.analysis.analysis_file import AnalysisFile
from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
from app.models.analysis.analysis_session import AnalysisSession
from app.models.analysis.analysis_snapshot import AnalysisSnapshot
from app.models.analysis.analysis_step import AnalysisStep
from app.models.analysis.analysis_validation_master import AnalysisValidationMaster

from .project import ProjectSeederMixin


class AnalysisSessionSeederMixin(ProjectSeederMixin):
    """AnalysisSession作成用Mixin。"""

    async def create_validation_master(
        self,
        *,
        name: str = "Test Validation",
        validation_order: int = 1,
    ) -> AnalysisValidationMaster:
        """分析検証マスタを作成。"""
        validation = AnalysisValidationMaster(
            name=name,
            validation_order=validation_order,
        )
        self.db.add(validation)
        await self.db.flush()
        await self.db.refresh(validation)
        return validation

    async def create_issue_master(
        self,
        *,
        validation: AnalysisValidationMaster,
        name: str = "Test Issue",
        issue_order: int = 1,
        description: str | None = None,
    ) -> AnalysisIssueMaster:
        """分析課題マスタを作成。"""
        issue = AnalysisIssueMaster(
            validation_id=validation.id,
            name=name,
            issue_order=issue_order,
            description=description,
        )
        self.db.add(issue)
        await self.db.flush()
        await self.db.refresh(issue)
        return issue

    async def create_analysis_session(
        self,
        *,
        project: Project,
        creator: UserAccount,
        issue: AnalysisIssueMaster,
        current_snapshot_id: uuid.UUID | None = None,
        status: str = "draft",
    ) -> AnalysisSession:
        """分析セッションを作成。"""
        session = AnalysisSession(
            project_id=project.id,
            creator_id=creator.id,
            issue_id=issue.id,
            current_snapshot_id=current_snapshot_id,
            status=status,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def create_analysis_snapshot(
        self,
        *,
        session: AnalysisSession,
        snapshot_order: int = 0,
    ) -> AnalysisSnapshot:
        """分析スナップショットを作成。"""
        snapshot = AnalysisSnapshot(
            session_id=session.id,
            snapshot_order=snapshot_order,
        )
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def create_analysis_file(
        self,
        *,
        session: AnalysisSession,
        project_file: ProjectFile,
        sheet_name: str = "Sheet1",
        axis_config: dict[str, Any] | None = None,
        data: list[dict[str, Any]] | None = None,
    ) -> AnalysisFile:
        """分析ファイルを作成。"""
        analysis_file = AnalysisFile(
            session_id=session.id,
            project_file_id=project_file.id,
            sheet_name=sheet_name,
            axis_config=axis_config or {},
            data=data or [],
        )
        self.db.add(analysis_file)
        await self.db.flush()
        await self.db.refresh(analysis_file)
        return analysis_file

    async def create_analysis_step(
        self,
        *,
        snapshot: AnalysisSnapshot,
        name: str = "Test Step",
        step_order: int = 0,
        step_type: str = "summary",
        input_ref: str = "original",
        config: dict[str, Any] | None = None,
    ) -> AnalysisStep:
        """分析ステップを作成。"""
        step = AnalysisStep(
            snapshot_id=snapshot.id,
            name=name,
            step_order=step_order,
            type=step_type,
            input=input_ref,
            config=config or {},
        )
        self.db.add(step)
        await self.db.flush()
        await self.db.refresh(step)
        return step

    async def seed_analysis_session_dataset(
        self,
        *,
        project: Project | None = None,
        owner: UserAccount | None = None,
    ) -> dict[str, Any]:
        """分析セッション用テストデータセットをシード。"""
        if project is None or owner is None:
            project, owner = await self.create_project_with_owner()

        validation = await self.create_validation_master()
        issue = await self.create_issue_master(validation=validation)

        session = await self.create_analysis_session(
            project=project,
            creator=owner,
            issue=issue,
        )

        snapshot = await self.create_analysis_snapshot(session=session)

        await self.db.commit()

        return {
            "project": project,
            "owner": owner,
            "validation": validation,
            "issue": issue,
            "session": session,
            "snapshot": snapshot,
        }
