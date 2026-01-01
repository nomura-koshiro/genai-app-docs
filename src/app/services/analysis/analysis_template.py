"""分析テンプレートサービス。

このモジュールは、分析テンプレート（施策・課題）のビジネスロジックを提供します。

主な機能:
    - テンプレート一覧取得
    - テンプレート詳細取得
    - テンプレート作成（セッションから）
    - テンプレート削除
"""

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.repositories.analysis import (
    AnalysisIssueRepository,
    AnalysisSessionRepository,
    AnalysisTemplateRepository,
    AnalysisValidationRepository,
)
from app.schemas.analysis import (
    AnalysisDummyChartResponse,
    AnalysisDummyFormulaResponse,
    AnalysisGraphAxisResponse,
    AnalysisIssueCatalogResponse,
    AnalysisIssueDetailResponse,
    AnalysisTemplateCreateRequest,
    AnalysisTemplateCreateResponse,
    AnalysisTemplateDeleteResponse,
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
        self.template_repository = AnalysisTemplateRepository(db)
        self.session_repository = AnalysisSessionRepository(db)

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

    async def create_template(
        self,
        project_id: uuid.UUID,
        request: AnalysisTemplateCreateRequest,
        user_id: uuid.UUID,
    ) -> AnalysisTemplateCreateResponse:
        """セッションからテンプレートを作成します。

        Args:
            project_id: プロジェクトID
            request: テンプレート作成リクエスト
            user_id: 作成者ユーザーID

        Returns:
            作成されたテンプレート情報

        Raises:
            NotFoundError: 元セッションが見つからない
        """
        # 元セッションの取得
        source_session = await self.session_repository.get(request.source_session_id)
        if not source_session:
            raise NotFoundError("元セッションが見つかりません")

        # プロジェクトIDの検証
        if source_session.project_id != project_id:
            raise ForbiddenError("他のプロジェクトのセッションからテンプレートを作成できません")

        # テンプレート設定を抽出（簡易版）
        template_config = {
            "initialPrompt": source_session.custom_system_prompt or "",
            "initialMessage": source_session.initial_message or "",
            "issueName": source_session.issue.name if source_session.issue else "",
        }

        # テンプレート作成
        template = await self.template_repository.create(
            project_id=project_id if not request.is_public else None,  # 公開テンプレートはグローバル
            name=request.name,
            description=request.description,
            template_type="session",
            template_config=template_config,
            source_session_id=request.source_session_id,
            is_public=request.is_public,
            created_by=user_id,
        )

        logger.info(
            "分析テンプレート作成完了",
            template_id=str(template.id),
            project_id=str(project_id),
            user_id=str(user_id),
        )

        return AnalysisTemplateCreateResponse(
            template_id=template.id,
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            template_config=template.template_config,
            created_at=template.created_at,
        )

    async def delete_template(
        self,
        project_id: uuid.UUID,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AnalysisTemplateDeleteResponse:
        """テンプレートを削除します。

        Args:
            project_id: プロジェクトID
            template_id: テンプレートID
            user_id: リクエストユーザーID

        Returns:
            削除レスポンス

        Raises:
            NotFoundError: テンプレートが見つからない
            ForbiddenError: 削除権限がない
        """
        # テンプレートの取得
        template = await self.template_repository.get_by_id(template_id)
        if not template:
            raise NotFoundError("テンプレートが見つかりません")

        # 権限チェック: プロジェクト固有テンプレートの場合、同じプロジェクトであること
        if template.project_id and template.project_id != project_id:
            raise ForbiddenError("他のプロジェクトのテンプレートは削除できません")

        # 作成者のみ削除可能
        if template.created_by != user_id:
            raise ForbiddenError("テンプレートの作成者のみ削除できます")

        # 削除実行
        deleted = await self.template_repository.delete(template_id)
        if not deleted:
            raise NotFoundError("テンプレートが見つかりません")

        logger.info(
            "分析テンプレート削除完了",
            template_id=str(template_id),
            project_id=str(project_id),
            user_id=str(user_id),
        )

        return AnalysisTemplateDeleteResponse(
            success=True,
            deleted_at=datetime.now(UTC),
        )
