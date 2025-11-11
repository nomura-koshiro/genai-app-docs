"""分析データ管理サービス。

このモジュールは、データのアップロード、削除、ソースデータの取得など、
分析データの管理機能を提供します。

主な機能:
    - データファイルのアップロード（upload_data）
    - データファイルの削除（delete_data）
    - 元データフレームの設定（set_source_data）
    - ソースデータの取得（get_source_data）

使用例:
    >>> from app.services.analysis.agent.data_manager import AnalysisDataManager
    >>>
    >>> async with get_db() as db:
    ...     data_manager = AnalysisDataManager(db, session_id)
    ...
    ...     # データアップロード
    ...     await data_manager.upload_data({
    ...         "id": str(file_id),
    ...         "file_name": "sales.csv",
    ...         "table_name": "売上データ",
    ...         "table_axis": ["地域", "商品"],
    ...         "data": df
    ...     })
    ...
    ...     # 元データ設定
    ...     await data_manager.set_source_data(df)
    ...
    ...     # ソースデータ取得
    ...     source_df = await data_manager.get_source_data(step_index=0)
"""

import uuid
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.analysis_file import AnalysisFileRepository
from app.repositories.analysis_step import AnalysisStepRepository
from app.services.analysis.agent.storage import AnalysisStorageService

logger = get_logger(__name__)


class AnalysisDataManager:
    """分析データ管理クラス。

    データのアップロード、削除、ソースデータの取得などの
    データ管理機能を提供します。

    Attributes:
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): セッションID
        file_repository (AnalysisFileRepository): ファイルリポジトリ
        step_repository (AnalysisStepRepository): ステップリポジトリ
        storage_service (AnalysisStorageService): ストレージサービス

    Example:
        >>> async with get_db() as db:
        ...     data_manager = AnalysisDataManager(db, session_id)
        ...     await data_manager.set_source_data(df)
    """

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """分析データ管理を初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
            session_id (uuid.UUID): セッションのUUID

        Note:
            - セッションの存在確認は行わないため、呼び出し側で確認すること
        """
        self.db = db
        self.session_id = session_id
        self.file_repository = AnalysisFileRepository(db)
        self.step_repository = AnalysisStepRepository(db)
        self.storage_service = AnalysisStorageService()

        logger.info(
            "分析データ管理を初期化しました",
            session_id=str(session_id),
        )

    @measure_performance
    async def upload_data(self, upload_file: dict[str, Any]) -> None:
        """アップロードされたデータを登録します。

        camp-backend-code-analysis互換のメソッド。
        AnalysisFileレコードとしてDBに保存します。

        このメソッドは以下の処理を実行します：
        1. 必須フィールドの検証（id, file_name, table_name, table_axis, data）
        2. DataFrameの型検証
        3. ストレージへの保存（CSV形式）
        4. メタデータのDB保存（AnalysisFileテーブル）

        Args:
            upload_file (dict[str, Any]): アップロードされたファイルの情報
                - id (str): 一意なファイルID（UUID文字列）
                - file_name (str): ファイル名（例: "sales.csv"）
                - table_name (str): テーブル名（例: "売上データ"）
                - table_axis (list[str]): 軸候補のリスト（例: ["地域", "商品"]）
                - data (pd.DataFrame): データフレーム

        Raises:
            ValidationError: 以下の場合に発生
                - 必須フィールドが欠けている
                - dataがDataFrameでない
                - ストレージ保存に失敗
                - DB保存に失敗

        Example:
            >>> await data_manager.upload_data({
            ...     "id": str(uuid.uuid4()),
            ...     "file_name": "sales.csv",
            ...     "table_name": "売上データ",
            ...     "table_axis": ["地域", "商品"],
            ...     "data": df
            ... })

        Note:
            - データはストレージに保存されます（files/プレフィックス）
            - メタデータはAnalysisFileテーブルに保存されます
            - ストレージパス: {session_id}/files/file_{file_id}.csv
            - 既存のファイルIDがある場合はスキップされます
        """
        logger.info(
            "データをアップロード中",
            session_id=str(self.session_id),
            file_name=upload_file.get("file_name"),
            table_name=upload_file.get("table_name"),
            action="upload_data",
        )

        try:
            # 必須フィールドの検証
            required_fields = ["id", "file_name", "table_name", "table_axis", "data"]
            for field in required_fields:
                if field not in upload_file:
                    raise ValidationError(
                        f"upload_fileに必須フィールドが欠けています: {field}",
                        details={"missing_field": field},
                    )

            # DataFrameの検証
            if not isinstance(upload_file["data"], pd.DataFrame):
                raise ValidationError(
                    "upload_file['data']はpd.DataFrameである必要があります",
                    details={"type": type(upload_file["data"]).__name__},
                )

            df = upload_file["data"]

            # ストレージに保存
            file_id = uuid.UUID(upload_file["id"])
            storage_path = await self.storage_service.save_dataframe(
                session_id=self.session_id,
                filename=f"file_{file_id}",
                df=df,
                prefix="files",
            )

            logger.debug(
                "ファイルをストレージに保存しました",
                session_id=str(self.session_id),
                storage_path=storage_path,
            )

            # DBに保存（既存チェック）
            existing_file = await self.file_repository.get(file_id)
            if not existing_file:
                # ユーザーIDは後で設定されるため、仮のUUIDを使用
                await self.file_repository.create(
                    session_id=self.session_id,
                    uploaded_by=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # 仮
                    file_name=upload_file["file_name"],
                    table_name=upload_file["table_name"],
                    storage_path=storage_path,
                    file_size=0,  # サイズは後で更新可能
                    content_type="text/csv",
                    table_axis=upload_file["table_axis"],
                    metadata={
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "columns": list(df.columns),
                    },
                    is_active=True,
                )
                await self.db.flush()

            logger.info(
                "データアップロードが完了しました",
                session_id=str(self.session_id),
                file_id=str(file_id),
                storage_path=storage_path,
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "データアップロード中にエラーが発生しました",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def delete_data(self, id: str) -> None:
        """指定されたIDのアップロードデータを削除します。

        このメソッドは以下の処理を実行します：
        1. ファイルの存在確認
        2. ストレージからファイル削除
        3. DBからレコード削除
        4. original.csvの削除チェック

        Args:
            id (str): 削除するデータのID（UUID文字列）

        Raises:
            NotFoundError: 以下の場合に発生
                - 指定されたIDのファイルが見つからない
            Exception: 以下の場合に発生
                - ストレージからの削除に失敗
                - DBからの削除に失敗

        Example:
            >>> await data_manager.delete_data(str(file_id))

        Note:
            - original_dfが削除された場合、original.csvも削除されます
            - ストレージとDBの両方から削除されます
            - 論理削除ではなく物理削除されます
        """
        logger.info(
            "データを削除中",
            session_id=str(self.session_id),
            file_id=id,
            action="delete_data",
        )

        try:
            file_id = uuid.UUID(id)
            file = await self.file_repository.get(file_id)

            if not file:
                logger.warning(
                    "ファイルが見つかりません",
                    session_id=str(self.session_id),
                    file_id=id,
                )
                raise NotFoundError(
                    f"ファイルが見つかりません: {id}",
                    details={"file_id": id},
                )

            # ストレージから削除
            await self.storage_service.delete_file(file.storage_path)

            # DBから削除
            await self.file_repository.delete(file_id)
            await self.db.flush()

            # original.csvの削除チェック
            original_path = self.storage_service.generate_path(
                self.session_id, "original.csv"
            )
            if file.storage_path == original_path:
                logger.info(
                    "元データが削除されました",
                    session_id=str(self.session_id),
                )

            logger.info(
                "データ削除が完了しました",
                session_id=str(self.session_id),
                file_id=id,
            )

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "データ削除中にエラーが発生しました",
                session_id=str(self.session_id),
                file_id=id,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def set_source_data(self, data: pd.DataFrame) -> None:
        """アップロードされたデータを元に、元のデータフレームを設定します。

        元データは "original.csv" としてストレージに保存されます。
        このメソッドは分析の起点となるデータを設定するために使用されます。

        Args:
            data (pd.DataFrame): 元のデータフレーム

        Raises:
            ValueError: 以下の場合に発生
                - dataがDataFrameでない
            Exception: 以下の場合に発生
                - ストレージへの保存に失敗

        Example:
            >>> df = pd.DataFrame({"地域": ["東京"], "売上": [1000]})
            >>> await data_manager.set_source_data(df)

        Note:
            - ストレージパス: {session_id}/original.csv
            - 既存のoriginal.csvがある場合は上書きされます
            - プレフィックスなしで保存されます
        """
        logger.info(
            "元データを設定中",
            session_id=str(self.session_id),
            action="set_source_data",
        )

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame.")

        try:
            # ストレージに保存
            storage_path = await self.storage_service.save_dataframe(
                session_id=self.session_id,
                filename="original",
                df=data,
                prefix=None,
            )

            logger.info(
                "元データを保存しました",
                session_id=str(self.session_id),
                storage_path=storage_path,
                rows=len(data),
                columns=len(data.columns),
            )

        except Exception as e:
            logger.error(
                "元データ設定中にエラーが発生しました",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_source_data(self, step_index: int | None = None) -> pd.DataFrame:
        """ステップのデータソースを取得します。

        step_indexがNoneまたはdata_source='original'の場合はoriginal.csvから読み込み、
        それ以外の場合は指定されたステップの結果データから読み込みます。

        処理フロー:
            1. step_indexがNone → original.csvを返す
            2. step_indexのdata_source='original' → original.csvを返す
            3. step_indexのdata_source='step_N' → step_Nの結果データを返す

        Args:
            step_index (int | None): ステップのインデックス
                - None: original.csvから読み込み
                - 0以上: 該当ステップのdata_sourceに従う

        Returns:
            pd.DataFrame: ソースデータ

        Raises:
            NotFoundError: 以下の場合に発生
                - ソースデータが見つからない
                - ストレージにファイルが存在しない
            ValidationError: 以下の場合に発生
                - data_sourceの形式が不正（'original'または'step_N'でない）
                - data_sourceのインデックスが範囲外
                - 参照先のステップに結果データがない

        Example:
            >>> # 元データを取得
            >>> df = await data_manager.get_source_data(None)
            >>>
            >>> # ステップ0のソースデータを取得
            >>> df = await data_manager.get_source_data(0)
            >>>
            >>> # ステップ1のソースデータを取得
            >>> df = await data_manager.get_source_data(1)

        Note:
            - original.csvが存在しない場合はNotFoundErrorが発生します
            - ステップの結果データが存在しない場合はValidationErrorが発生します
            - data_sourceが'step_N'形式の場合、Nはステップインデックスを示します
        """
        logger.debug(
            "ソースデータを取得中",
            session_id=str(self.session_id),
            step_index=step_index,
        )

        try:
            # ステップ一覧を取得
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )

            # original を取得
            if step_index is None or all_steps[step_index].data_source == "original":
                original_path = self.storage_service.generate_path(
                    self.session_id, "original.csv"
                )
                df = await self.storage_service.load_dataframe(original_path)

                logger.debug(
                    "元データを読み込みました",
                    session_id=str(self.session_id),
                    rows=len(df),
                )

                return df

            # ステップの結果から取得
            step = all_steps[step_index]
            data_source = step.data_source

            if not data_source.startswith("step_"):
                raise ValidationError(
                    f"data_sourceの形式が不正です: {data_source}",
                    details={"data_source": data_source},
                )

            source_step_index = int(data_source.split("_")[1])

            if source_step_index < 0 or source_step_index >= len(all_steps):
                raise ValidationError(
                    f"無効なdata_sourceインデックス: {source_step_index}",
                    details={
                        "source_step_index": source_step_index,
                        "step_index": step_index,
                    },
                )

            source_step = all_steps[source_step_index]

            if not source_step.result_data_path:
                raise ValidationError(
                    f"ステップ{source_step_index}の結果データがありません",
                    details={"source_step_index": source_step_index},
                )

            df = await self.storage_service.load_dataframe(source_step.result_data_path)

            logger.debug(
                "ステップ結果データを読み込みました",
                session_id=str(self.session_id),
                source_step_index=source_step_index,
                rows=len(df),
            )

            return df

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ソースデータ取得中にエラーが発生しました",
                session_id=str(self.session_id),
                step_index=step_index,
                error=str(e),
                exc_info=True,
            )
            raise
