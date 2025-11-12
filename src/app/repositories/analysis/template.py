"""分析テンプレートモデル用のデータアクセスリポジトリ。

このモジュールは、AnalysisTemplateモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、テンプレート検索機能（施策別・課題別検索、
チャートデータを含む詳細取得など）を追加しています。

主な機能:
    - 施策（policy）別のテンプレート一覧取得
    - 施策・課題（policy + issue）によるテンプレート検索
    - チャートデータを含むテンプレート詳細取得
    - アクティブなテンプレートの取得
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.analysis import AnalysisTemplateRepository
    >>>
    >>> async with get_db() as db:
    ...     template_repo = AnalysisTemplateRepository(db)
    ...     templates = await template_repo.list_by_policy("市場拡大")
    ...     for template in templates:
    ...         print(f"Template: {template.issue}")
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models import AnalysisTemplate
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisTemplateRepository(BaseRepository[AnalysisTemplate, uuid.UUID]):
    """AnalysisTemplateモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    分析テンプレート管理に特化したクエリメソッドを提供します。

    テンプレート検索機能:
        - list_by_policy(): 施策別のテンプレート一覧
        - get_by_policy_issue(): 施策・課題による特定テンプレート取得
        - get_with_charts(): チャートデータを含む詳細取得
        - list_active(): アクティブなテンプレートのみを取得

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるテンプレート取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規テンプレート作成
        - update(): テンプレート情報更新
        - delete(): テンプレート削除
        - count(): テンプレート数カウント

    Example:
        >>> async with get_db() as db:
        ...     template_repo = AnalysisTemplateRepository(db)
        ...
        ...     # 施策別のテンプレート一覧
        ...     templates = await template_repo.list_by_policy("市場拡大")
        ...
        ...     # 施策・課題による特定テンプレート取得
        ...     template = await template_repo.get_by_policy_issue(
        ...         policy="市場拡大",
        ...         issue="新規参入"
        ...     )
        ...
        ...     # チャートデータを含む詳細取得
        ...     template_with_charts = await template_repo.get_with_charts(template.id)
        ...     print(f"Charts: {len(template_with_charts.charts)}")

    Note:
        - get_with_charts()はN+1問題を防ぐためselectinloadを使用
        - 施策・課題の組み合わせはユニーク制約により一意性が保証される
    """

    def __init__(self, db: AsyncSession) -> None:
        """AnalysisTemplateRepositoryを初期化します。

        Args:
            db (AsyncSession): 非同期データベースセッション
        """
        super().__init__(model=AnalysisTemplate, db=db)

    async def list_by_policy(
        self,
        policy: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisTemplate]:
        """指定された施策に紐づくテンプレート一覧を取得します。

        Args:
            policy (str): 施策名
            skip (int): スキップする件数（デフォルト: 0）
            limit (int): 最大取得件数（デフォルト: 100）

        Returns:
            list[AnalysisTemplate]: テンプレートのリスト

        Example:
            >>> templates = await template_repo.list_by_policy(
            ...     "市場拡大",
            ...     skip=0,
            ...     limit=10
            ... )
            >>> print(f"Found {len(templates)} templates")
        """
        stmt = select(self.model).where(self.model.policy == policy).order_by(self.model.display_order).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_policy_issue(
        self,
        policy: str,
        issue: str,
    ) -> AnalysisTemplate | None:
        """施策・課題の組み合わせでテンプレートを取得します。

        Args:
            policy (str): 施策名
            issue (str): 課題名

        Returns:
            AnalysisTemplate | None: 該当するテンプレート（存在しない場合はNone）

        Example:
            >>> template = await template_repo.get_by_policy_issue(
            ...     policy="市場拡大",
            ...     issue="新規参入"
            ... )
            >>> if template:
            ...     print(f"Found: {template.description}")
        """
        stmt = select(self.model).where(
            self.model.policy == policy,
            self.model.issue == issue,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_charts(self, template_id: uuid.UUID) -> AnalysisTemplate | None:
        """チャートデータを含むテンプレート詳細を取得します。

        Args:
            template_id (uuid.UUID): テンプレートID

        Returns:
            AnalysisTemplate | None: チャートデータを含むテンプレート（存在しない場合はNone）

        Example:
            >>> template = await template_repo.get_with_charts(template_id)
            >>> if template:
            ...     for chart in template.charts:
            ...         print(f"Chart: {chart.chart_name}")

        Note:
            N+1問題を防ぐためselectinloadを使用しています。
        """
        stmt = select(self.model).where(self.model.id == template_id).options(selectinload(self.model.charts))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisTemplate]:
        """アクティブなテンプレート一覧を取得します。

        Args:
            skip (int): スキップする件数（デフォルト: 0）
            limit (int): 最大取得件数（デフォルト: 100）

        Returns:
            list[AnalysisTemplate]: アクティブなテンプレートのリスト

        Example:
            >>> templates = await template_repo.list_active(limit=50)
            >>> print(f"Active templates: {len(templates)}")
        """
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)  # noqa: E712
            .order_by(self.model.display_order)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all_with_charts(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisTemplate]:
        """チャートデータを含むテンプレート一覧を取得します。

        Args:
            skip (int): スキップする件数（デフォルト: 0）
            limit (int): 最大取得件数（デフォルト: 100）

        Returns:
            list[AnalysisTemplate]: チャートデータを含むテンプレートのリスト

        Example:
            >>> templates = await template_repo.list_all_with_charts(limit=20)
            >>> for template in templates:
            ...     print(f"{template.policy} - {template.issue}: {len(template.charts)} charts")

        Note:
            N+1問題を防ぐためselectinloadを使用しています。
        """
        stmt = select(self.model).options(selectinload(self.model.charts)).order_by(self.model.display_order).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
