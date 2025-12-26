"""分析テンプレートサービス。

このモジュールは、分析テンプレート（施策・課題）のビジネスロジックを提供します。

主な機能:
    - テンプレート一覧取得
    - テンプレート詳細取得
"""

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.analysis import AnalysisIssueRepository, AnalysisValidationRepository
from app.schemas.analysis import (
    AnalysisDummyChartResponse,
    AnalysisDummyFormulaResponse,
    AnalysisGraphAxisResponse,
    AnalysisIssueCatalogResponse,
    AnalysisIssueDetailResponse,
)

logger = get_logger(__name__)


class AnalysisTemplateService:
    """分析テンプレート管理のビジネスロジックを提供するサービスクラス。

    施策課題一覧の取得、課題詳細の取得を提供します。
    """

    def __init__(self, db: AsyncSession):
        """分析テンプレートサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.validation_repository = AnalysisValidationRepository(db)
        self.issue_repository = AnalysisIssueRepository(db)

    async def list_templates(
        self,
        project_id: uuid.UUID | None = None,
    ) -> list[AnalysisIssueCatalogResponse]:
        """施策課題一覧を取得します。

        施策名、課題名、施策order、課題orderを含む一覧を返します。

        Args:
            project_id: プロジェクトID（将来のプロジェクト固有テンプレート対応用）

        Returns:
            list[AnalysisIssueCatalogResponse]: テンプレート一覧
        """
        # TODO: project別テンプレート対応

        validation_issue = await self.validation_repository.list_with_issues()
        response = []
        for validation in validation_issue:
            for issue in validation.issues:
                response.append(
                    AnalysisIssueCatalogResponse(
                        validation_id=validation.id,  # 施策ID
                        validation=validation.name,  # 施策名
                        validation_order=validation.validation_order,  # 施策order
                        id=issue.id,  # 課題ID
                        name=issue.name,  # 課題名
                        issue_order=issue.issue_order,  # 課題order
                        created_at=issue.created_at,  # 作成日時
                        updated_at=issue.updated_at,  # 更新日時
                    )
                )
        return response

    async def get_template(
        self,
        issue_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
    ) -> AnalysisIssueDetailResponse:
        """指定した施策課題の分析テンプレート詳細を取得します。

        施策名、課題名、施策order、課題order、
        課題アプローチ説明、AIプロンプト、初期軸設定、
        ダミー入力、ダミー入力ヒント、ダミー計算式、ダミーチャートを含む。

        Args:
            issue_id: 課題ID
            project_id: プロジェクトID（将来のプロジェクト固有テンプレート対応用）

        Returns:
            AnalysisIssueDetailResponse: テンプレート詳細

        Raises:
            NotFoundError: 課題が見つからない場合
        """
        # TODO: project別テンプレート対応
        issue = await self.issue_repository.get_with_details(issue_id)

        if not issue:
            raise NotFoundError("指定された課題のテンプレートが見つかりません。")
        else:
            initial_axis_response = [
                AnalysisGraphAxisResponse(
                    issue_id=issue.id,
                    id=axis.id,
                    name=axis.name,
                    axis_order=axis.axis_order,
                    option=axis.option,
                    multiple=axis.multiple,
                    created_at=axis.created_at,
                    updated_at=axis.updated_at,
                )
                for axis in issue.graph_axes
            ]

            dummy_formula_response = [
                AnalysisDummyFormulaResponse(
                    issue_id=issue.id,
                    id=formula.id,
                    name=formula.name,
                    formula_order=formula.formula_order,
                    value=formula.value,
                    created_at=formula.created_at,
                    updated_at=formula.updated_at,
                )
                for formula in issue.dummy_formulas
            ]

            dummy_chart_response = [
                AnalysisDummyChartResponse(
                    issue_id=issue.id,
                    id=chart.id,
                    chart_order=chart.chart_order,
                    chart=json.loads(chart.chart.decode("utf-8")) if chart.chart else {},
                    created_at=chart.created_at,
                    updated_at=chart.updated_at,
                )
                for chart in issue.dummy_charts
            ]

            dummy_input_response = json.loads(issue.dummy_input.decode("utf-8")) if issue.dummy_input else []

            response = AnalysisIssueDetailResponse(
                id=issue.id,
                name=issue.name,
                issue_order=issue.issue_order,
                validation_id=issue.validation.id,
                validation=issue.validation.name,
                validation_order=issue.validation.validation_order,
                description=issue.description,
                agent_prompt=issue.agent_prompt,
                initial_axis=initial_axis_response,
                initial_msg=issue.initial_msg,
                dummy_input=dummy_input_response,
                dummy_hint=issue.dummy_hint,
                dummy_formula=dummy_formula_response,
                dummy_chart=dummy_chart_response,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
            )

            return response
