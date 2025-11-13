"""分析テンプレートモデル。

このモジュールは、分析の施策・課題テンプレートを管理するモデルを定義します。
validation.yml の内容をデータベースに格納し、動的な管理を可能にします。

主な機能:
    - 施策（policy）と課題（issue）の組み合わせ管理
    - AIエージェントプロンプトの保存
    - 初期設定（initial_axis, dummy_formula等）の管理
    - ダミーチャートデータとの関連付け

テーブル設計:
    - テーブル名: analysis_templates
    - プライマリキー: id (UUID)
    - ユニーク制約: (policy, issue)

使用例:
    >>> from app.models.analysis import AnalysisTemplate
    >>> template = AnalysisTemplate(
    ...     policy="市場拡大",
    ...     issue="新規参入",
    ...     description="新規市場への参入効果を分析します",
    ...     agent_prompt="...",
    ...     initial_axis=[{"name": "横軸", "option": "科目", "multiple": False}]
    ... )
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.template_chart import AnalysisTemplateChart


class AnalysisTemplate(Base, TimestampMixin):
    """分析テンプレートモデル。

    validation.yml の施策・課題テンプレートをデータベースに格納します。
    各テンプレートは複数のダミーチャートを持つことができます。

    Attributes:
        id (UUID): プライマリキー（UUID）
        policy (str): 施策名（例: "施策①：不採算製品の撤退"）
        issue (str): 課題名（例: "不採算製品から撤退した場合の利益改善効果は​？"）
        description (str): テンプレートの説明
        agent_prompt (str): AIエージェント用のプロンプト
        initial_msg (str): 初期メッセージ
        initial_axis (list[dict]): 初期軸設定（JSONB）
            - name (str): 軸名
            - option (str): オプション名
            - multiple (bool): 複数選択可能か
        dummy_formula (list[dict] | None): ダミー計算式（JSONB）
            - name (str): 計算式名
            - value (str): 計算式の値
        dummy_input (list[str] | None): ダミー入力データ（JSONB）
        dummy_hint (str | None): ダミーヒント
        is_active (bool): アクティブフラグ
        display_order (int): 表示順序
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    Relationships:
        charts (list[AnalysisTemplateChart]): 関連するダミーチャートリスト

    インデックス:
        - uq_analysis_template_policy_issue: (policy, issue) - ユニーク制約
        - ix_analysis_template_policy_issue: (policy, issue) - 複合インデックス
        - ix_analysis_templates_policy: policy
        - ix_analysis_templates_issue: issue
    """

    __tablename__ = "analysis_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Template ID (Primary Key)",
    )

    policy: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Policy name (施策名)",
    )

    issue: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Issue name (課題名)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Template description",
    )

    agent_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI agent prompt for this analysis",
    )

    initial_msg: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Initial message for user",
    )

    initial_axis: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Initial axis configuration (list[AnalysisInitialAxisConfig] as dict)",
    )

    dummy_formula: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Dummy formula settings (list of formula definitions)",
    )

    dummy_input: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Dummy input data (list of input strings)",
    )

    dummy_hint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Dummy hint text",
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Active flag (False = archived)",
    )

    display_order: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Display order for UI",
    )

    # リレーションシップ
    charts: Mapped[list["AnalysisTemplateChart"]] = relationship(
        "AnalysisTemplateChart",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="AnalysisTemplateChart.chart_order",
    )

    # インデックス・制約
    __table_args__ = (
        UniqueConstraint("policy", "issue", name="uq_analysis_template_policy_issue"),
        Index("ix_analysis_template_policy_issue", "policy", "issue"),
    )

    def __repr__(self) -> str:
        """分析テンプレートオブジェクトの文字列表現。

        Returns:
            str: "<AnalysisTemplate(id=..., policy=..., issue=...)>" 形式

        Example:
            >>> template = AnalysisTemplate(id=uuid.uuid4(), policy="市場拡大", issue="新規参入")
            >>> print(repr(template))
            '<AnalysisTemplate(id=..., policy=市場拡大, issue=新規参入)>'
        """
        return f"<AnalysisTemplate(id={self.id}, policy={self.policy}, issue={self.issue})>"
