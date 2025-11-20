"""分析ステップモデル。

このモジュールは、分析セッション内の個別ステップを管理するモデルを定義します。

主な機能:
    - 分析ステップの基本情報管理
    - ステップタイプの管理（filter/aggregate/transform/summary）
    - ステップ設定の保存（JSONB）
    - 分析結果の保存（データパス、チャート、数式）

テーブル設計:
    - テーブル名: analysis_steps
    - プライマリキー: id (UUID)
    - 外部キー: session_id (analysis_sessions)

使用例:
    >>> from app.models.analysis import AnalysisStep
    >>> step = AnalysisStep(
    ...     session_id=session_id,
    ...     step_name="売上フィルタリング",
    ...     step_type="filter",
    ...     step_order=0,
    ...     config={"category_filter": {"地域": ["東京", "大阪"]}}
    ... )
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_session import AnalysisSession


class AnalysisStep(Base, TimestampMixin):
    """分析ステップモデル。

    分析セッション内の個別のデータ処理ステップを管理します。
    各ステップは特定のタイプ（filter/aggregate/transform/summary）を持ち、
    独自の設定と結果データを保持します。

    Attributes:
        id (UUID): プライマリキー（UUID）
        session_id (UUID): セッションID（外部キー）
        step_name (str): ステップ名（日本語で分かりやすい名前）
        step_type (str): ステップタイプ
            - "filter": データフィルタリング
            - "aggregate": データ集計
            - "transform": データ変換
            - "summary": 結果サマリー
        step_order (int): ステップの順序（0から開始）
        data_source (str): データソース
            - "original": 元データ
            - "step_0", "step_1", ...: 前のステップの結果
        config (dict): ステップ設定（タイプごとに異なる構造）
        result_data_path (str | None): 結果データのストレージパス
        result_chart (dict | None): 結果チャート（Plotly JSON）
        result_formula (list[dict] | None): 結果数式のリスト
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    Relationships:
        session (AnalysisSession): 所属セッション

    インデックス:
        - idx_analysis_steps_session: session_id
        - idx_analysis_steps_order: session_id, step_order
    """

    __tablename__ = "analysis_step"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ステップID（主キー）",
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="セッションID（外部キー）",
    )

    step_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ステップ名（ユーザーフレンドリー）",
    )

    step_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ステップタイプ: filter/aggregate/transform/summary",
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ステップ順序（0から開始）",
    )

    data_source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="original",
        comment="データソース: original/step_0/step_1/...",
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="ステップ設定（タイプ固有の構造）",
    )

    result_data_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="結果データ保存パス（CSVファイルパス）",
    )

    result_chart: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="結果チャート（Plotly JSON形式）",
    )

    result_formula: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="結果式（AnalysisResultFormulaのリストを辞書形式で保存）",
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="アクティブフラグ",
    )

    # リレーションシップ
    session: Mapped["AnalysisSession"] = relationship(
        "AnalysisSession",
        back_populates="steps",
    )

    # インデックス
    __table_args__ = (
        Index("idx_analysis_steps_session", "session_id"),
        Index("idx_analysis_steps_order", "session_id", "step_order"),
    )

    def __repr__(self) -> str:
        """分析ステップオブジェクトの文字列表現。

        Returns:
            str: "<AnalysisStep(id=..., name=..., type=...)>" 形式

        Example:
            >>> step = AnalysisStep(
            ...     id=uuid.uuid4(),
            ...     step_name="売上フィルタ",
            ...     step_type="filter"
            ... )
            >>> print(repr(step))
            '<AnalysisStep(id=..., name=売上フィルタ, type=filter)>'
        """
        return f"<AnalysisStep(id={self.id}, name={self.step_name}, type={self.step_type})>"
