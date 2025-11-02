"""ファイル関連のリポジトリ。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.sample_file import SampleFile
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class SampleFileRepository(BaseRepository[SampleFile, int]):
    """サンプル: ファイルリポジトリ。

    ファイルのCRUD操作を提供します。
    """

    def __init__(self, db: AsyncSession):
        """ファイルリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(SampleFile, db)

    async def get_by_file_id(self, file_id: str) -> SampleFile | None:
        """file_idでファイルを取得します。

        Args:
            file_id: ファイル識別子

        Returns:
            SampleFile | None: ファイルオブジェクト、存在しない場合はNone
        """
        result = await self.db.execute(select(SampleFile).filter(SampleFile.file_id == file_id))
        return result.scalar_one_or_none()

    async def list_files(self, user_id: int | None = None, skip: int = 0, limit: int = 100) -> list[SampleFile]:
        """ファイル一覧を取得します。

        Args:
            user_id: ユーザーID（指定した場合、そのユーザーのファイルのみ）
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            list[SampleFile]: ファイルのリスト
        """
        query = select(SampleFile).order_by(SampleFile.created_at.desc())

        if user_id is not None:
            query = query.filter(SampleFile.user_id == user_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_file(
        self,
        file_id: str,
        filename: str,
        filepath: str,
        size: int,
        content_type: str,
        user_id: int | None = None,
    ) -> SampleFile:
        """新しいファイルメタデータを作成します。

        Args:
            file_id: ファイル識別子
            filename: 元のファイル名
            filepath: サーバー上のファイルパス
            size: ファイルサイズ（バイト）
            content_type: ファイルのMIMEタイプ
            user_id: ユーザーID（オプション）

        Returns:
            SampleFile: 作成されたファイルメタデータ
        """
        file = SampleFile(
            file_id=file_id,
            filename=filename,
            filepath=filepath,
            size=size,
            content_type=content_type,
            user_id=user_id,
        )
        self.db.add(file)
        await self.db.flush()
        return file

    async def delete_file(self, file_id: str) -> bool:
        """ファイルメタデータを削除します。

        Args:
            file_id: ファイル識別子

        Returns:
            bool: 削除成功の場合True、ファイルが存在しない場合False
        """
        file = await self.get_by_file_id(file_id)
        if not file:
            return False

        await self.db.delete(file)
        await self.db.flush()
        return True
