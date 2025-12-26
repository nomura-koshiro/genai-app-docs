"""ProjectFile シーダー。"""

from app.models import Project, ProjectFile, UserAccount

from .base import BaseSeeder


class ProjectFileSeederMixin(BaseSeeder):
    """ProjectFile作成用Mixin。"""

    async def create_project_file(
        self,
        *,
        project: Project,
        uploader: UserAccount,
        filename: str = "test_file.xlsx",
        original_filename: str = "original_test_file.xlsx",
        file_path: str = "/uploads/test_file.xlsx",
        file_size: int = 1024,
        mime_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ) -> ProjectFile:
        """プロジェクトファイルを作成。"""
        project_file = ProjectFile(
            project_id=project.id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=uploader.id,
        )
        self.db.add(project_file)
        await self.db.flush()
        await self.db.refresh(project_file)
        self._created_data.files.append(project_file)
        return project_file
