"""分析ステップ操作サービス。

分析ステップの作成、更新、削除を提供します。
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.analysis import AnalysisStepResponse
from app.services.analysis.analysis_session.base import AnalysisSessionServiceBase

logger = get_logger(__name__)


class AnalysisSessionStepService(AnalysisSessionServiceBase):
    """分析ステップ操作機能を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """分析ステップ操作サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    async def create_step(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        step_name: str,
        step_type: str,
        data_source: str,
        config: dict[str, Any] | None = None,
    ) -> AnalysisStepResponse:
        """最新snapshotに新しい分析ステップを作成します。

        - ステップタイプ: filter/aggregate/transform/summary
        - step_orderは自動採番されます（0から開始）
        - data_sourceにはoriginalまたは別のステップID（step_0など）を指定

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            step_name: ステップ名
            step_type: ステップタイプ
            data_source: データソース
            config: ステップ設定（JSONB）

        Returns:
            AnalysisStepResponse: 作成されたステップ情報

        Raises:
            NotFoundError: セッションが見つからない場合
            ValidationError: 不正なステップ設定の場合
        """
        # セッションを取得（リレーション含む）
        session = await self._get_session_with_full_relations(session_id)

        # state構築、ステップを追加・適用
        state = self._build_state(session)
        state.add_step(name=step_name, type=step_type, data=data_source)
        state.apply(step_index=-1, include_following=False)
        new_step = state.all_steps[-1]

        # dbに保存
        current_snapshot_order = session.current_snapshot.snapshot_order if session.current_snapshot else 0
        created_step = await self.step_repository.create(
            snapshot_id=session.snapshots[current_snapshot_order].id,
            name=step_name,
            step_order=len(state.all_steps) - 1,  # 最後のインデックス
            type=step_type,
            input=data_source,
            config=new_step["config"],
        )
        await self.db.commit()

        # レスポンス構築
        if new_step["result_data"] is not None:
            result_data = new_step["result_data"].to_dict(orient="records")
        else:
            result_data = None
        if new_step["result_table"] is not None and hasattr(new_step["result_table"], "to_dict"):
            result_table = new_step["result_table"].to_dict(orient="records")
        else:
            result_table = new_step["result_table"]
        return AnalysisStepResponse(
            id=created_step.id,
            snapshot_id=created_step.snapshot_id,
            name=created_step.name,
            step_order=created_step.step_order,
            type=created_step.type,
            input=created_step.input,
            config=created_step.config,
            result_data=result_data,
            result_formula=new_step["result_formula"],
            result_chart=new_step["result_chart"],
            result_table=result_table,
            created_at=created_step.created_at,
            updated_at=created_step.updated_at,
        )

    async def update_step(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        step_id: uuid.UUID,
        step_name: str | None = None,
        step_type: str | None = None,
        data_source: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> AnalysisStepResponse:
        """最新snapshotの既存分析ステップを更新します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            step_id: ステップID
            step_name: ステップ名（オプション）
            step_type: ステップタイプ（オプション）
            data_source: データソース（オプション）
            config: ステップ設定（オプション）

        Returns:
            AnalysisStepResponse: 更新されたステップ情報

        Raises:
            NotFoundError: セッションまたはステップが見つからない場合
        """
        # セッションを取得（リレーション含む）
        session = await self._get_session_with_full_relations(session_id)

        # ステップを探す
        current_snapshot_order = session.current_snapshot.snapshot_order if session.current_snapshot else 0
        target_step = None
        step_index = -1
        for step in session.snapshots[current_snapshot_order].steps:
            if step.id == step_id:
                target_step = step
                step_index = step.step_order
                break

        if target_step is None or step_index == -1:
            raise NotFoundError("ステップが見つかりません")

        # 更新する値を決定（Noneの場合は既存値を使用）
        updated_name = step_name if step_name is not None else target_step.name
        updated_type = step_type if step_type is not None else target_step.type
        updated_data_source = data_source if data_source is not None else target_step.input
        updated_config = config if config is not None else target_step.config

        # state構築、ステップを更新・適用
        state = self._build_state(session)
        state.all_steps[step_index]["name"] = updated_name
        state.all_steps[step_index]["type"] = updated_type
        state.all_steps[step_index]["data_source"] = updated_data_source

        if updated_type == "filter":
            state.set_filter(step_index, updated_config)
        elif updated_type == "aggregate":
            state.set_aggregation(step_index, updated_config)
        elif updated_type == "transform":
            state.set_transform(step_index, updated_config)
        elif updated_type == "summary":
            state.set_summary(step_index, updated_config)
        else:
            raise ValueError(
                f"無効なステップタイプです: {updated_type}。filter, aggregate, transform, summaryのいずれかを指定してください。"
            )

        # dbに保存
        new_step = state.all_steps[step_index]
        updated_config = new_step["config"]
        updated_step = await self.step_repository.update(
            target_step,
            name=updated_name,
            type=updated_type,
            input=updated_data_source,
            config=updated_config,
        )
        await self.db.commit()
        await self.db.refresh(updated_step)

        # レスポンス構築
        if new_step["result_data"] is not None:
            result_data = new_step["result_data"].to_dict(orient="records")
        else:
            result_data = None
        if new_step["result_table"] is not None and hasattr(new_step["result_table"], "to_dict"):
            result_table = new_step["result_table"].to_dict(orient="records")
        else:
            result_table = new_step["result_table"]
        return AnalysisStepResponse(
            id=updated_step.id,
            snapshot_id=updated_step.snapshot_id,
            name=updated_step.name,
            step_order=updated_step.step_order,
            type=updated_step.type,
            input=updated_step.input,
            config=updated_step.config,
            result_data=result_data,
            result_formula=new_step["result_formula"],
            result_chart=new_step["result_chart"],
            result_table=result_table,
            created_at=updated_step.created_at,
            updated_at=updated_step.updated_at,
        )

    async def delete_step(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        step_id: uuid.UUID,
    ) -> None:
        """最新snapshotの指定されたステップを削除します。

        物理削除されます（論理削除ではありません）。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            step_id: ステップID

        Raises:
            NotFoundError: セッションまたはステップが見つからない場合
        """
        # セッションを取得（リレーション含む）
        session = await self._get_session_with_full_relations(session_id)

        # スナップショット、ステップを探す
        snap_idx, step_idx = -1, -1
        for s_idx, snap in enumerate(session.snapshots):
            for st_idx, step in enumerate(snap.steps):
                if step.id == step_id:
                    snap_idx = s_idx
                    step_idx = st_idx
                    break
            if snap_idx != -1:
                break
        if snap_idx == -1 or step_idx == -1:
            raise NotFoundError("ステップが見つかりません")
        current_snapshot_order = session.current_snapshot.snapshot_order if session.current_snapshot else 0
        if snap_idx != current_snapshot_order:
            raise ValueError("現在のスナップショットのステップのみ削除できます")
        if step_idx != len(session.snapshots[snap_idx].steps) - 1:
            raise ValueError("スナップショットの最後のステップのみ削除できます")

        # ステップを削除
        await self.step_repository.delete(step_id)
        await self.db.commit()
        return
