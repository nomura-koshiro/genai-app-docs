"""プロジェクトファイル管理のビジネスロジックサービス。

このモジュールは、プロジェクトファイルのアップロード、ダウンロード、削除などのビジネスロジックを提供します。

主な機能:
    - ファイルアップロード（権限チェック、サイズ・MIMEタイプ検証）
    - ファイル取得（権限チェック）
    - ファイル一覧取得（権限チェック）
    - ファイルダウンロード（権限チェック）
    - ファイル削除（権限チェック）

使用例:
    >>> from app.services.project.file import ProjectFileService
    >>> async with get_db() as db:
    ...     file_service = ProjectFileService(db)
    ...     file = await file_service.upload_file(
    ...         project_id, upload_file, uploaded_by=user_id
    ...     )
"""

import os
import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import ProjectFile, ProjectRole
from app.repositories import ProjectFileRepository, ProjectMemberRepository

logger = get_logger(__name__)

# アップロードを許可するMIMEタイプ
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
}

# 最大ファイルサイズ（バイト）
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class ProjectFileService:
    """プロジェクトファイル管理のビジネスロジックを提供するサービスクラス。

    このサービスは、プロジェクトファイルのアップロード、ダウンロード、削除などの操作を提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        repository: ProjectFileRepositoryインスタンス（ファイルメタデータアクセス用）
        member_repository: ProjectMemberRepositoryインスタンス（権限チェック用）
        upload_dir: アップロードディレクトリのPath
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトファイルサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = ProjectFileRepository(db)
        self.member_repository = ProjectMemberRepository(db)
        self.upload_dir = Path(settings.LOCAL_STORAGE_PATH)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def _check_member_role(self, project_id: uuid.UUID, user_id: uuid.UUID, required_roles: list[ProjectRole]) -> None:
        """ユーザーのプロジェクトメンバーシップと権限をチェックします。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID
            required_roles: 必要なロールのリスト

        Raises:
            AuthorizationError: ユーザーがメンバーでない、または権限が不足している場合
        """
        member = await self.member_repository.get_by_project_and_user(project_id, user_id)
        if not member:
            raise AuthorizationError(
                "You are not a member of this project",
                details={"project_id": str(project_id), "user_id": str(user_id)},
            )

        if member.role not in required_roles:
            raise AuthorizationError(
                f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}",
                details={"user_role": member.role.value, "required_roles": [r.value for r in required_roles]},
            )

    def _generate_file_path(self, project_id: uuid.UUID, file_id: uuid.UUID, filename: str) -> Path:
        """ファイルの保存パスを生成します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            filename: ファイル名

        Returns:
            Path: ファイルの保存パス
        """
        project_dir = self.upload_dir / "projects" / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir / f"{file_id}_{filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名をサニタイズします（パストラバーサル攻撃対策）。

        Args:
            filename: 元のファイル名

        Returns:
            str: サニタイズされたファイル名
        """
        # ファイル名から危険な文字を削除
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        # 先頭・末尾の空白とドットを削除
        filename = filename.strip(". ")
        # 空の場合はデフォルト名を使用
        if not filename:
            filename = "unnamed_file"
        return filename

    @measure_performance
    @async_timeout(60.0)
    @transactional
    async def upload_file(self, project_id: uuid.UUID, file: UploadFile, uploaded_by: uuid.UUID) -> ProjectFile:
        """プロジェクトにファイルをアップロードします。

        このメソッドは以下の処理を実行します：
        1. プロジェクトメンバーシップ確認（MEMBER以上）
        2. ファイル名の検証
        3. MIMEタイプの検証
        4. ファイルサイズの検証
        5. ファイル名のサニタイズ
        6. ファイルの物理保存
        7. メタデータのデータベース保存

        Args:
            project_id: プロジェクトID
            file: アップロードするファイル
            uploaded_by: アップロード者のユーザーID

        Returns:
            ProjectFile: 作成されたファイルメタデータ

        Raises:
            AuthorizationError: ユーザーがメンバーでない、または権限が不足している場合
            ValidationError: ファイルが無効な場合
        """
        logger.info(
            "ファイルアップロード開始",
            project_id=str(project_id),
            filename=file.filename,
            content_type=file.content_type,
            uploaded_by=str(uploaded_by),
        )

        # 権限チェック（MEMBER以上）
        await self._check_member_role(project_id, uploaded_by, [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER])

        # ファイル名の検証
        if not file.filename:
            raise ValidationError("ファイル名が必要です")

        # MIMEタイプの検証
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"許可されていないファイルタイプです: {file.content_type}",
                details={
                    "content_type": file.content_type,
                    "allowed_types": list(ALLOWED_MIME_TYPES),
                },
            )

        # ファイルサイズの検証
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                f"ファイルサイズが大きすぎます（最大: {MAX_FILE_SIZE / 1024 / 1024}MB）",
                details={"size": file_size, "max_size": MAX_FILE_SIZE},
            )

        # ファイル名のサニタイズ
        safe_filename = self._sanitize_filename(file.filename)
        file_id = uuid.uuid4()
        filepath = self._generate_file_path(project_id, file_id, safe_filename)

        # ファイルを保存
        try:
            with open(filepath, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.exception(
                "ファイル保存エラー",
                filename=safe_filename,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise ValidationError(f"ファイルの保存に失敗しました: {str(e)}") from e

        # データベースに保存
        file_metadata = await self.repository.create(
            id=file_id,
            project_id=project_id,
            filename=safe_filename,
            original_filename=file.filename,
            file_path=str(filepath),
            file_size=file_size,
            mime_type=file.content_type,
            uploaded_by=uploaded_by,
        )

        await self.db.commit()

        logger.info(
            "ファイルアップロード完了",
            file_id=str(file_id),
            filename=safe_filename,
            size=file_size,
        )

        return file_metadata

    @measure_performance
    async def get_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectFile:
        """ファイルメタデータを取得します。

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            ProjectFile: ファイルメタデータ

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        file = await self.repository.get(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            file.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        return file

    @measure_performance
    async def list_project_files(
        self, project_id: uuid.UUID, requester_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[ProjectFile], int]:
        """プロジェクトのファイル一覧を取得します。

        Args:
            project_id: プロジェクトID
            requester_id: リクエスター（ユーザー）ID
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            tuple[list[ProjectFile], int]: ファイルリストと総件数のタプル

        Raises:
            AuthorizationError: 権限が不足している場合
        """
        logger.debug("ファイル一覧取得", project_id=str(project_id), skip=skip, limit=limit)

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        files = await self.repository.list_by_project(project_id, skip, limit)
        total = await self.repository.count_by_project(project_id)

        logger.debug("ファイル一覧取得完了", count=len(files), total=total)

        return files, total

    @measure_performance
    @async_timeout(30.0)
    async def download_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> Path:
        """ファイルをダウンロードします（ファイルパスを返却）。

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            Path: ファイルのパス

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        file = await self.get_file(file_id, requester_id)

        # ファイルの存在確認
        filepath = Path(file.file_path)
        if not filepath.exists():
            logger.error(
                "ファイルがディスク上に存在しません",
                file_id=str(file_id),
                filepath=str(filepath),
            )
            raise NotFoundError(
                f"ファイルがディスク上に存在しません: {file_id}",
                details={"file_id": str(file_id)},
            )

        return filepath

    @measure_performance
    @async_timeout(30.0)
    @transactional
    async def delete_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> bool:
        """ファイルを削除します。

        このメソッドは以下の処理を実行します：
        1. ファイルの存在確認
        2. 権限チェック（アップロード者本人、またはADMIN/OWNER）
        3. ディスクからファイル削除
        4. データベースからメタデータ削除

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            bool: 削除成功の場合True

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.info("ファイル削除", file_id=str(file_id), requester_id=str(requester_id))

        file = await self.repository.get(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（アップロード者本人、またはADMIN/OWNER）
        member = await self.member_repository.get_by_project_and_user(file.project_id, requester_id)
        if not member:
            raise AuthorizationError(
                "You are not a member of this project",
                details={"project_id": str(file.project_id), "user_id": str(requester_id)},
            )

        # アップロード者本人、またはADMIN/OWNERのみ削除可能
        if file.uploaded_by != requester_id and member.role not in [ProjectRole.PROJECT_MANAGER]:
            raise AuthorizationError(
                "Only the file uploader or project admin/owner can delete this file",
                details={
                    "file_id": str(file_id),
                    "uploaded_by": str(file.uploaded_by),
                    "requester_id": str(requester_id),
                    "requester_role": member.role.value,
                },
            )

        # ディスクからファイルを削除
        try:
            filepath = Path(file.file_path)
            if filepath.exists():
                os.remove(filepath)
        except Exception as e:
            logger.exception(
                "ファイル削除エラー",
                file_id=str(file_id),
                filepath=str(file.file_path),
                error_type=type(e).__name__,
                error_message=str(e),
            )

        # データベースから削除
        await self.repository.delete(file_id)
        await self.db.commit()

        logger.info("ファイル削除完了", file_id=str(file_id))

        return True
