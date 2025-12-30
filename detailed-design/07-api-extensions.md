# API拡張詳細設計（API_BACKEND_REQUEST対応）

## 1. 概要

本ドキュメントでは、フロントエンドから要求されているAPI拡張（`API_BACKEND_REQUEST.md`）の詳細設計を定義する。

### 1.1 対象機能

| カテゴリ | 要求内容 | 優先度 |
|---------|---------|--------|
| 分析セッション | カテゴリ情報追加、インサイト、関連セッション、スナップショット復元 | 高〜低 |
| 検証マスタ | description、issueCount、statusフィールド追加 | 高 |
| ドライバーツリー | テンプレート拡張、施策一覧、計算結果詳細、カラム情報 | 高〜中 |
| ファイル管理 | 使用状況サマリー拡張 | 中 |
| カテゴリマスタ | formulaCount追加 | 中 |
| ダッシュボード | プロジェクト進捗API | 低 |

---

## 2. 分析セッション拡張

### 2.1 カテゴリ（Validation）情報の追加

**対象**: `GET /api/v1/project/{project_id}/analysis/session/{session_id}`, `GET /api/v1/project/{project_id}/analysis/session`

#### 2.1.1 スキーマ変更

```python
# src/app/schemas/analysis/analysis_session.py に追加

class ValidationInfo(BaseCamelCaseModel):
    """検証カテゴリ情報（リレーション展開用）。

    セッション詳細で検証カテゴリ名を表示するために使用します。

    Attributes:
        id (uuid.UUID): 検証カテゴリID
        name (str): 検証カテゴリ名
    """

    id: uuid.UUID = Field(..., description="検証カテゴリID")
    name: str = Field(..., description="検証カテゴリ名")


# AnalysisSessionResponse を更新
class AnalysisSessionResponse(BaseCamelCaseORMModel):
    """分析セッションレスポンススキーマ。"""

    # ... 既存フィールド ...

    # 追加フィールド
    validation: ValidationInfo | None = Field(
        default=None,
        description="検証カテゴリ情報（リレーション展開）"
    )
```

#### 2.1.2 リポジトリ変更

```python
# src/app/repositories/analysis/analysis_session.py

from sqlalchemy.orm import selectinload

class AnalysisSessionRepository(BaseRepository[AnalysisSession, uuid.UUID]):
    """分析セッションリポジトリ。"""

    async def get_with_relations(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """リレーション情報を含めてセッションを取得します。"""
        stmt = (
            select(AnalysisSession)
            .options(
                selectinload(AnalysisSession.issue).selectinload(AnalysisIssueMaster.validation),
                selectinload(AnalysisSession.creator),
                selectinload(AnalysisSession.input_file),
            )
            .where(AnalysisSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list_with_relations(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> tuple[list[AnalysisSession], int]:
        """リレーション情報を含めてセッション一覧を取得します。"""
        # ベースクエリ
        base_query = select(AnalysisSession).where(
            AnalysisSession.project_id == project_id
        )

        if status:
            base_query = base_query.where(AnalysisSession.status == status)

        # カウント
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = await self.session.scalar(count_stmt) or 0

        # データ取得（リレーション含む）
        stmt = (
            base_query
            .options(
                selectinload(AnalysisSession.issue).selectinload(AnalysisIssueMaster.validation),
                selectinload(AnalysisSession.creator),
                selectinload(AnalysisSession.input_file),
            )
            .order_by(AnalysisSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())

        return sessions, total
```

#### 2.1.3 サービス変更

```python
# src/app/services/analysis/session/crud.py

async def get_session_with_validation(
    self,
    session_id: uuid.UUID,
) -> AnalysisSessionResponse:
    """検証カテゴリ情報を含めてセッションを取得します。"""
    session = await self.repository.get_with_relations(session_id)
    if not session:
        raise NotFoundError("セッションが見つかりません")

    # ValidationInfo を構築
    validation_info = None
    if session.issue and session.issue.validation:
        validation_info = ValidationInfo(
            id=session.issue.validation.id,
            name=session.issue.validation.name,
        )

    return AnalysisSessionResponse(
        # ... 既存フィールド ...
        validation=validation_info,
    )
```

---

### 2.2 インサイト情報

**対象**: `GET /api/v1/project/{project_id}/analysis/session/{session_id}`

#### 2.2.1 スキーマ追加

```python
# src/app/schemas/analysis/analysis_session.py に追加

class InsightItem(BaseCamelCaseModel):
    """インサイトアイテム。

    分析結果から抽出されたインサイト情報。

    Attributes:
        id (str): インサイトID
        title (str): インサイトタイトル
        description (str): インサイト説明
        type (str): インサイトタイプ（trend/anomaly/correlation/summary）
    """

    id: str = Field(..., description="インサイトID")
    title: str = Field(..., description="インサイトタイトル")
    description: str = Field(..., description="インサイト説明")
    type: str = Field(..., description="インサイトタイプ")


class InsightCard(BaseCamelCaseModel):
    """インサイトカード。

    ダッシュボード表示用のインサイトカード情報。

    Attributes:
        icon (str): アイコン名
        label (str): ラベル
        value (str): 値
        change (str | None): 変化量
        is_positive (bool | None): ポジティブな変化かどうか
    """

    icon: str = Field(..., description="アイコン名")
    label: str = Field(..., description="ラベル")
    value: str = Field(..., description="値")
    change: str | None = Field(default=None, description="変化量")
    is_positive: bool | None = Field(default=None, description="ポジティブな変化かどうか")


class SessionInsightsResponse(BaseCamelCaseModel):
    """セッションインサイトレスポンス。

    Attributes:
        session_id (uuid.UUID): セッションID
        insights (list[InsightItem]): インサイトリスト
        insight_cards (list[InsightCard]): インサイトカードリスト
        generated_at (datetime): 生成日時
    """

    session_id: uuid.UUID = Field(..., description="セッションID")
    insights: list[InsightItem] = Field(default_factory=list, description="インサイトリスト")
    insight_cards: list[InsightCard] = Field(default_factory=list, description="インサイトカードリスト")
    generated_at: datetime = Field(..., description="生成日時")
```

#### 2.2.2 API追加

```python
# src/app/api/routes/v1/analysis/analysis_session.py に追加

@analysis_session_router.get(
    "/{session_id}/insights",
    response_model=SessionInsightsResponse,
    summary="セッションインサイト取得",
    description="""
    分析セッションから抽出されたインサイト情報を取得します。

    インサイトは分析ステップの結果から自動生成されます。
    """,
)
@handle_service_errors
async def get_session_insights(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    analysis_service: AnalysisSessionServiceDep,
    current_user: CurrentUserAccountDep,
) -> SessionInsightsResponse:
    """セッションインサイトを取得します。"""
    return await analysis_service.get_session_insights(
        session_id=session_id,
        project_id=project_id,
    )
```

#### 2.2.3 サービス実装

```python
# src/app/services/analysis/session/insights.py（新規）

from datetime import datetime, UTC

class SessionInsightsService:
    """セッションインサイトサービス。"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_repository = AnalysisSessionRepository(session)

    async def get_session_insights(
        self,
        session_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> SessionInsightsResponse:
        """セッションのインサイト情報を取得します。"""
        # セッション取得
        session = await self.session_repository.get_with_snapshots(session_id)
        if not session:
            raise NotFoundError("セッションが見つかりません")

        # 現在のスナップショットからステップ結果を取得
        current_snapshot = session.current_snapshot
        if not current_snapshot:
            return SessionInsightsResponse(
                session_id=session_id,
                insights=[],
                insight_cards=[],
                generated_at=datetime.now(UTC),
            )

        # ステップ結果からインサイトを抽出
        insights = self._extract_insights_from_steps(current_snapshot.steps)
        insight_cards = self._generate_insight_cards(current_snapshot.steps)

        return SessionInsightsResponse(
            session_id=session_id,
            insights=insights,
            insight_cards=insight_cards,
            generated_at=datetime.now(UTC),
        )

    def _extract_insights_from_steps(
        self,
        steps: list[AnalysisStep],
    ) -> list[InsightItem]:
        """ステップ結果からインサイトを抽出します。"""
        insights = []

        for step in steps:
            if step.type == "summary" and step.result_formula:
                for i, formula in enumerate(step.result_formula):
                    insights.append(InsightItem(
                        id=f"{step.id}-{i}",
                        title=formula.get("name", ""),
                        description=f"{formula.get('value', '')} {formula.get('unit', '')}",
                        type="summary",
                    ))

        return insights

    def _generate_insight_cards(
        self,
        steps: list[AnalysisStep],
    ) -> list[InsightCard]:
        """インサイトカードを生成します。"""
        cards = []

        for step in steps:
            if step.type == "summary" and step.result_formula:
                for formula in step.result_formula:
                    icon = self._get_icon_for_metric(formula.get("name", ""))
                    cards.append(InsightCard(
                        icon=icon,
                        label=formula.get("name", ""),
                        value=f"{formula.get('value', '')} {formula.get('unit', '')}",
                        change=formula.get("change"),
                        is_positive=formula.get("is_positive"),
                    ))

        return cards

    def _get_icon_for_metric(self, metric_name: str) -> str:
        """メトリクス名に応じたアイコンを返します。"""
        icon_mapping = {
            "売上": "TrendingUp",
            "利益": "DollarSign",
            "成長率": "Percent",
            "顧客数": "Users",
        }
        return icon_mapping.get(metric_name, "BarChart2")
```

---

### 2.3 関連セッション

**対象**: 新規エンドポイント `GET /api/v1/project/{project_id}/analysis/session/{session_id}/related`

#### 2.3.1 スキーマ追加

```python
# src/app/schemas/analysis/analysis_session.py に追加

class RelatedSessionItem(BaseCamelCaseModel):
    """関連セッションアイテム。

    Attributes:
        id (uuid.UUID): セッションID
        name (str): セッション名
        date (date): 作成日
        status (str): セッション状態
        relation_type (str): 関連タイプ（same_issue/same_file/same_creator）
    """

    id: uuid.UUID = Field(..., description="セッションID")
    name: str = Field(..., description="セッション名")
    date: date = Field(..., description="作成日")
    status: str = Field(..., description="セッション状態")
    relation_type: str = Field(..., description="関連タイプ")


class RelatedSessionsResponse(BaseCamelCaseModel):
    """関連セッションレスポンス。

    Attributes:
        session_id (uuid.UUID): 基準セッションID
        related_sessions (list[RelatedSessionItem]): 関連セッションリスト
        total (int): 総件数
    """

    session_id: uuid.UUID = Field(..., description="基準セッションID")
    related_sessions: list[RelatedSessionItem] = Field(
        default_factory=list,
        description="関連セッションリスト"
    )
    total: int = Field(..., description="総件数")
```

#### 2.3.2 API追加

```python
# src/app/api/routes/v1/analysis/analysis_session.py に追加

@analysis_session_router.get(
    "/{session_id}/related",
    response_model=RelatedSessionsResponse,
    summary="関連セッション取得",
    description="""
    同じ課題や同じファイルを使用している関連セッションを取得します。
    """,
)
@handle_service_errors
async def get_related_sessions(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    analysis_service: AnalysisSessionServiceDep,
    current_user: CurrentUserAccountDep,
    limit: int = Query(10, ge=1, le=50, description="取得件数"),
) -> RelatedSessionsResponse:
    """関連セッションを取得します。"""
    return await analysis_service.get_related_sessions(
        session_id=session_id,
        project_id=project_id,
        limit=limit,
    )
```

#### 2.3.3 リポジトリ追加

```python
# src/app/repositories/analysis/analysis_session.py に追加

async def get_related_sessions(
    self,
    session_id: uuid.UUID,
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    input_file_id: uuid.UUID | None,
    limit: int = 10,
) -> list[AnalysisSession]:
    """関連セッションを取得します。"""
    # 同じ課題のセッション、または同じファイルを使用しているセッション
    conditions = [
        AnalysisSession.project_id == project_id,
        AnalysisSession.id != session_id,
    ]

    # 同じ課題 OR 同じファイルの条件
    or_conditions = [AnalysisSession.issue_id == issue_id]
    if input_file_id:
        or_conditions.append(AnalysisSession.input_file_id == input_file_id)

    stmt = (
        select(AnalysisSession)
        .where(and_(*conditions))
        .where(or_(*or_conditions))
        .order_by(AnalysisSession.created_at.desc())
        .limit(limit)
    )

    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

---

### 2.4 スナップショット説明文追加

**対象**: スナップショット関連エンドポイント

#### 2.4.1 モデル変更

```python
# src/app/models/analysis/analysis_snapshot.py

class AnalysisSnapshot(Base, TimestampMixin):
    """分析スナップショット。"""

    # ... 既存カラム ...

    # 追加カラム
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="スナップショット名",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="スナップショット説明",
    )
```

#### 2.4.2 マイグレーション

```python
# alembic/versions/xxx_add_snapshot_description.py

def upgrade() -> None:
    op.add_column(
        "analysis_snapshot",
        sa.Column("name", sa.String(255), nullable=True, comment="スナップショット名")
    )
    op.add_column(
        "analysis_snapshot",
        sa.Column("description", sa.Text(), nullable=True, comment="スナップショット説明")
    )


def downgrade() -> None:
    op.drop_column("analysis_snapshot", "description")
    op.drop_column("analysis_snapshot", "name")
```

#### 2.4.3 スキーマ変更

```python
# src/app/schemas/analysis/analysis_session.py

class AnalysisSnapshotResponse(BaseCamelCaseORMModel):
    """分析スナップショットレスポンススキーマ。"""

    # ... 既存フィールド ...

    # 追加フィールド
    name: str | None = Field(default=None, description="スナップショット名")
    description: str | None = Field(default=None, description="スナップショット説明")
```

---

### 2.5 スナップショット復元API

**対象**: 新規エンドポイント `POST /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots/{snapshot_id}/restore`

#### 2.5.1 スキーマ追加

```python
# src/app/schemas/analysis/analysis_session.py に追加

class SnapshotRestoreResponse(BaseCamelCaseModel):
    """スナップショット復元レスポンス。

    Attributes:
        success (bool): 成功フラグ
        restored_snapshot (AnalysisSnapshotResponse): 復元されたスナップショット
        session (AnalysisSessionResponse): 更新されたセッション
        restored_at (datetime): 復元日時
    """

    success: bool = Field(..., description="成功フラグ")
    restored_snapshot: AnalysisSnapshotResponse = Field(..., description="復元されたスナップショット")
    session: AnalysisSessionResponse = Field(..., description="更新されたセッション")
    restored_at: datetime = Field(..., description="復元日時")
```

#### 2.5.2 API追加

```python
# src/app/api/routes/v1/analysis/analysis_session.py に追加

@analysis_session_router.post(
    "/{session_id}/snapshots/{snapshot_id}/restore",
    response_model=SnapshotRestoreResponse,
    summary="スナップショット復元",
    description="""
    指定したスナップショットの状態にセッションを復元します。

    現在の状態は新しいスナップショットとして保存されます。
    """,
)
@handle_service_errors
async def restore_snapshot(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    analysis_service: AnalysisSessionServiceDep,
    current_user: CurrentUserAccountDep,
) -> SnapshotRestoreResponse:
    """スナップショットを復元します。"""
    return await analysis_service.restore_snapshot(
        session_id=session_id,
        snapshot_id=snapshot_id,
        project_id=project_id,
        user_id=current_user.id,
    )
```

#### 2.5.3 サービス実装

```python
# src/app/services/analysis/session/snapshot.py に追加

@transactional
async def restore_snapshot(
    self,
    session_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> SnapshotRestoreResponse:
    """スナップショットを復元します。"""
    # セッション取得
    session = await self.session_repository.get(session_id)
    if not session:
        raise NotFoundError("セッションが見つかりません")

    if session.project_id != project_id:
        raise AuthorizationError("このプロジェクトのセッションではありません")

    # スナップショット取得
    snapshot = await self.snapshot_repository.get(snapshot_id)
    if not snapshot or snapshot.session_id != session_id:
        raise NotFoundError("スナップショットが見つかりません")

    # 現在のスナップショットを保存
    if session.current_snapshot_id and session.current_snapshot_id != snapshot_id:
        # 現在の状態を新しいスナップショットとして保存（オプション）
        pass

    # セッションのcurrent_snapshot_idを更新
    session.current_snapshot_id = snapshot_id
    await self.session_repository.update(session)

    # 更新後のセッションを取得
    updated_session = await self.session_repository.get_with_relations(session_id)

    return SnapshotRestoreResponse(
        success=True,
        restored_snapshot=AnalysisSnapshotResponse.model_validate(snapshot),
        session=AnalysisSessionResponse.model_validate(updated_session),
        restored_at=datetime.now(UTC),
    )
```

---

## 3. 検証マスタ（Validation）拡張

### 3.1 フィールド追加

**対象**: `GET /api/v1/admin/validation`, `GET /api/v1/admin/validation/{validation_id}`

#### 3.1.1 モデル変更

```python
# src/app/models/analysis/analysis_validation_master.py

class AnalysisValidationMaster(Base, TimestampMixin):
    """分析検証マスタ。"""

    # ... 既存カラム ...

    # 追加カラム
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="検証カテゴリの説明",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="有効フラグ",
    )
```

#### 3.1.2 マイグレーション

```python
# alembic/versions/xxx_add_validation_fields.py

def upgrade() -> None:
    op.add_column(
        "analysis_validation_master",
        sa.Column("description", sa.Text(), nullable=True, comment="検証カテゴリの説明")
    )
    op.add_column(
        "analysis_validation_master",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true", comment="有効フラグ")
    )


def downgrade() -> None:
    op.drop_column("analysis_validation_master", "is_active")
    op.drop_column("analysis_validation_master", "description")
```

#### 3.1.3 スキーマ変更

```python
# src/app/schemas/admin/validation.py

class AnalysisValidationResponse(BaseCamelCaseORMModel):
    """検証マスタレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="ID")
    name: str = Field(..., description="検証名")
    validation_order: int = Field(..., description="表示順序")

    # 追加フィールド
    description: str | None = Field(default=None, description="検証カテゴリの説明")
    issue_count: int = Field(default=0, description="関連課題数")
    status: str = Field(default="active", description="ステータス（active/inactive）")

    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnalysisValidationCreate(AnalysisValidationBase):
    """検証マスタ作成スキーマ。"""

    description: str | None = Field(default=None, description="検証カテゴリの説明")


class AnalysisValidationUpdate(BaseCamelCaseModel):
    """検証マスタ更新スキーマ。"""

    name: str | None = Field(default=None, max_length=255, description="検証名")
    validation_order: int | None = Field(default=None, description="表示順序")
    description: str | None = Field(default=None, description="検証カテゴリの説明")
    is_active: bool | None = Field(default=None, description="有効フラグ")
```

#### 3.1.4 リポジトリ変更

```python
# src/app/repositories/admin/validation.py

async def get_with_issue_count(self, validation_id: uuid.UUID) -> dict | None:
    """関連課題数を含めて検証マスタを取得します。"""
    stmt = (
        select(
            AnalysisValidationMaster,
            func.count(AnalysisIssueMaster.id).label("issue_count"),
        )
        .outerjoin(AnalysisIssueMaster)
        .where(AnalysisValidationMaster.id == validation_id)
        .group_by(AnalysisValidationMaster.id)
    )

    result = await self.session.execute(stmt)
    row = result.first()

    if not row:
        return None

    validation, issue_count = row
    return {
        "validation": validation,
        "issue_count": issue_count,
    }


async def get_list_with_issue_counts(
    self,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    """関連課題数を含めて検証マスタ一覧を取得します。"""
    # ベースクエリ
    base_query = select(AnalysisValidationMaster)

    if is_active is not None:
        base_query = base_query.where(AnalysisValidationMaster.is_active == is_active)

    # カウント
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = await self.session.scalar(count_stmt) or 0

    # データ取得（課題数含む）
    stmt = (
        select(
            AnalysisValidationMaster,
            func.count(AnalysisIssueMaster.id).label("issue_count"),
        )
        .outerjoin(AnalysisIssueMaster)
        .group_by(AnalysisValidationMaster.id)
        .order_by(AnalysisValidationMaster.validation_order)
        .offset(skip)
        .limit(limit)
    )

    if is_active is not None:
        stmt = stmt.where(AnalysisValidationMaster.is_active == is_active)

    result = await self.session.execute(stmt)
    rows = result.all()

    return [{"validation": row[0], "issue_count": row[1]} for row in rows], total
```

---

## 4. ドライバーツリー拡張

### 4.1 テンプレート情報の拡張

**対象**: `GET /api/v1/project/{project_id}/driver-tree/category`

#### 4.1.1 スキーマ変更

```python
# src/app/schemas/driver_tree/common.py に追加

class CategoryInfoExtended(BaseCamelCaseModel):
    """カテゴリ情報（拡張版）。

    Attributes:
        category_id (int): カテゴリID
        industry_name (str): 業界名
        driver_type (str): ドライバー型
        node_count (int): テンプレートのノード数
        usage_count (int): 使用回数
    """

    category_id: int = Field(..., description="カテゴリID")
    industry_name: str = Field(..., description="業界名")
    driver_type: str = Field(..., description="ドライバー型")
    node_count: int = Field(default=0, description="テンプレートのノード数")
    usage_count: int = Field(default=0, description="使用回数")
```

#### 4.1.2 リポジトリ追加

```python
# src/app/repositories/driver_tree/category.py

async def get_categories_with_stats(self) -> list[dict]:
    """統計情報を含めてカテゴリ一覧を取得します。"""
    # カテゴリごとのノード数と使用回数を集計
    stmt = (
        select(
            DriverTreeCategory,
            func.count(distinct(DriverTreeFormula.id)).label("formula_count"),
            func.count(distinct(DriverTree.id)).label("usage_count"),
        )
        .outerjoin(
            DriverTreeFormula,
            DriverTreeFormula.category_id == DriverTreeCategory.id
        )
        .outerjoin(
            DriverTree,
            DriverTree.formula_id == DriverTreeFormula.id
        )
        .group_by(DriverTreeCategory.id)
        .order_by(DriverTreeCategory.category_id)
    )

    result = await self.session.execute(stmt)
    rows = result.all()

    categories = []
    for row in rows:
        category, formula_count, usage_count = row
        # 数式からノード数を推定（数式数 × 平均ノード数）
        node_count = formula_count * 5  # 仮の計算

        categories.append({
            "category": category,
            "node_count": node_count,
            "usage_count": usage_count,
        })

    return categories
```

---

### 4.2 ツリー全体の施策一覧

**対象**: 新規エンドポイント `GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/policy`

#### 4.2.1 スキーマ追加

```python
# src/app/schemas/driver_tree/driver_tree.py に追加

class TreePolicyItem(BaseCamelCaseModel):
    """ツリー施策アイテム。

    Attributes:
        node_id (uuid.UUID): ノードID
        node_name (str): ノード名
        policy_id (uuid.UUID): 施策ID
        name (str): 施策名
        value (float): 施策値
        status (str): 施策状態（planned/active/completed）
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    node_name: str = Field(..., description="ノード名")
    policy_id: uuid.UUID = Field(..., description="施策ID")
    name: str = Field(..., description="施策名")
    value: float = Field(..., description="施策値")
    status: str = Field(default="planned", description="施策状態")


class TreePoliciesResponse(BaseCamelCaseModel):
    """ツリー施策一覧レスポンス。

    Attributes:
        tree_id (uuid.UUID): ツリーID
        policies (list[TreePolicyItem]): 施策リスト
        total (int): 総件数
    """

    tree_id: uuid.UUID = Field(..., description="ツリーID")
    policies: list[TreePolicyItem] = Field(default_factory=list, description="施策リスト")
    total: int = Field(..., description="総件数")
```

#### 4.2.2 API追加

```python
# src/app/api/routes/v1/driver_tree/driver_tree.py に追加

@driver_tree_router.get(
    "/tree/{tree_id}/policy",
    response_model=TreePoliciesResponse,
    summary="ツリー施策一覧取得",
    description="""
    ツリー全体に紐づく全ノードの施策を一括取得します。
    """,
)
@handle_service_errors
async def get_tree_policies(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    driver_tree_service: DriverTreeServiceDep,
    current_user: CurrentUserAccountDep,
) -> TreePoliciesResponse:
    """ツリー施策一覧を取得します。"""
    return await driver_tree_service.get_tree_policies(
        tree_id=tree_id,
        project_id=project_id,
    )
```

#### 4.2.3 リポジトリ追加

```python
# src/app/repositories/driver_tree/policy.py に追加

async def get_policies_by_tree(self, tree_id: uuid.UUID) -> list[dict]:
    """ツリーに属する全施策を取得します。"""
    stmt = (
        select(
            DriverTreePolicy,
            DriverTreeNode.id.label("node_id"),
            DriverTreeNode.label.label("node_name"),
        )
        .join(DriverTreeNode, DriverTreePolicy.node_id == DriverTreeNode.id)
        .where(DriverTreeNode.driver_tree_id == tree_id)
        .order_by(DriverTreeNode.label, DriverTreePolicy.name)
    )

    result = await self.session.execute(stmt)
    rows = result.all()

    return [
        {
            "policy": row[0],
            "node_id": row[1],
            "node_name": row[2],
        }
        for row in rows
    ]
```

---

### 4.3 計算結果の詳細データ

**対象**: `GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/data`

#### 4.3.1 スキーマ変更

```python
# src/app/schemas/driver_tree/driver_tree.py に追加

class CalculationSummary(BaseCamelCaseModel):
    """計算サマリー。

    Attributes:
        total_nodes (int): 総ノード数
        calculated_nodes (int): 計算済みノード数
        error_nodes (int): エラーノード数
        last_calculated_at (datetime | None): 最終計算日時
    """

    total_nodes: int = Field(..., description="総ノード数")
    calculated_nodes: int = Field(..., description="計算済みノード数")
    error_nodes: int = Field(..., description="エラーノード数")
    last_calculated_at: datetime | None = Field(default=None, description="最終計算日時")


class KpiSummary(BaseCamelCaseModel):
    """KPIサマリー。

    Attributes:
        target_kpi (str): 対象KPI名
        base_value (float): 基準値
        simulated_value (float): シミュレーション値
        change_rate (float): 変化率
    """

    target_kpi: str = Field(..., description="対象KPI名")
    base_value: float = Field(..., description="基準値")
    simulated_value: float = Field(..., description="シミュレーション値")
    change_rate: float = Field(..., description="変化率")


# DriverTreeCalculatedDataResponse を拡張
class DriverTreeCalculatedDataExtendedResponse(BaseCamelCaseModel):
    """計算データ拡張レスポンス。

    Attributes:
        calculated_data_list (list): 計算データ一覧
        summary (CalculationSummary): 計算サマリー
        kpi_summary (KpiSummary | None): KPIサマリー
    """

    calculated_data_list: list[DriverTreeNodeCalculatedData] = Field(
        ...,
        description="計算データ一覧"
    )
    summary: CalculationSummary = Field(..., description="計算サマリー")
    kpi_summary: KpiSummary | None = Field(default=None, description="KPIサマリー")
```

---

### 4.4 カラム情報取得

**対象**: `GET /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}`

#### 4.4.1 スキーマ追加

```python
# src/app/schemas/driver_tree/driver_tree_file.py に追加

class ColumnInfo(BaseCamelCaseModel):
    """カラム情報。

    Attributes:
        name (str): カラム名（内部名）
        display_name (str): 表示名
        data_type (str): データ型（string/number/datetime/boolean）
        role (str | None): 役割（推移/値/カテゴリ等）
    """

    name: str = Field(..., description="カラム名")
    display_name: str = Field(..., description="表示名")
    data_type: str = Field(..., description="データ型")
    role: str | None = Field(default=None, description="役割")


class SheetDetailResponse(BaseCamelCaseModel):
    """シート詳細レスポンス。

    Attributes:
        sheet_id (uuid.UUID): シートID
        sheet_name (str): シート名
        columns (list[ColumnInfo]): カラム情報リスト
        row_count (int): 行数
        sample_data (list[dict]): サンプルデータ（最初の10行）
    """

    sheet_id: uuid.UUID = Field(..., description="シートID")
    sheet_name: str = Field(..., description="シート名")
    columns: list[ColumnInfo] = Field(default_factory=list, description="カラム情報リスト")
    row_count: int = Field(..., description="行数")
    sample_data: list[dict[str, Any]] = Field(default_factory=list, description="サンプルデータ")
```

#### 4.4.2 API追加

```python
# src/app/api/routes/v1/driver_tree/driver_tree_file.py に追加

@driver_tree_file_router.get(
    "/file/{file_id}/sheet/{sheet_id}",
    response_model=SheetDetailResponse,
    summary="シート詳細取得",
    description="""
    シートのカラム情報とサンプルデータを取得します。
    """,
)
@handle_service_errors
async def get_sheet_detail(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    sheet_id: uuid.UUID,
    driver_tree_file_service: DriverTreeFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> SheetDetailResponse:
    """シート詳細を取得します。"""
    return await driver_tree_file_service.get_sheet_detail(
        file_id=file_id,
        sheet_id=sheet_id,
        project_id=project_id,
    )
```

#### 4.4.3 サービス実装

```python
# src/app/services/driver_tree/file.py に追加

async def get_sheet_detail(
    self,
    file_id: uuid.UUID,
    sheet_id: uuid.UUID,
    project_id: uuid.UUID,
) -> SheetDetailResponse:
    """シート詳細を取得します。"""
    # ファイル取得
    file = await self.file_repository.get(file_id)
    if not file:
        raise NotFoundError("ファイルが見つかりません")

    # シート取得
    sheet = await self.sheet_repository.get(sheet_id)
    if not sheet or sheet.file_id != file_id:
        raise NotFoundError("シートが見つかりません")

    # カラム情報を解析
    columns = self._analyze_columns(sheet.data)

    # サンプルデータを取得
    sample_data = sheet.data[:10] if sheet.data else []

    return SheetDetailResponse(
        sheet_id=sheet.id,
        sheet_name=sheet.name,
        columns=columns,
        row_count=len(sheet.data) if sheet.data else 0,
        sample_data=sample_data,
    )

def _analyze_columns(self, data: list[dict]) -> list[ColumnInfo]:
    """データからカラム情報を解析します。"""
    if not data:
        return []

    columns = []
    first_row = data[0]

    for key, value in first_row.items():
        data_type = self._infer_data_type(value)
        role = self._infer_role(key, data_type)

        columns.append(ColumnInfo(
            name=key,
            display_name=key,
            data_type=data_type,
            role=role,
        ))

    return columns

def _infer_data_type(self, value: Any) -> str:
    """値からデータ型を推定します。"""
    if value is None:
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, datetime):
        return "datetime"
    # 文字列から日付を推定
    if isinstance(value, str):
        try:
            datetime.fromisoformat(value)
            return "datetime"
        except ValueError:
            pass
    return "string"

def _infer_role(self, column_name: str, data_type: str) -> str | None:
    """カラム名とデータ型から役割を推定します。"""
    name_lower = column_name.lower()

    if "date" in name_lower or "日付" in name_lower or data_type == "datetime":
        return "推移"
    if data_type == "number":
        return "値"
    return "カテゴリ"
```

---

## 5. ファイル管理拡張

### 5.1 ファイル使用状況サマリー

**対象**: `GET /api/v1/project/{project_id}/file/{file_id}/usage`

#### 5.1.1 スキーマ確認・変更不要

既存の`ProjectFileUsageResponse`に`analysis_session_count`と`driver_tree_count`は既に含まれている。フロントエンドが期待する`sessionCount`と`treeCount`はcamelCase変換で対応済み。

サービス層でカウントを正しく集計することを確認。

```python
# src/app/services/project/file/usage.py

async def get_file_usage(
    self,
    file_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ProjectFileUsageResponse:
    """ファイル使用状況を取得します。"""
    file = await self.file_repository.get(file_id)
    if not file:
        raise NotFoundError("ファイルが見つかりません")

    # 分析セッションでの使用を取得
    session_usages = await self.analysis_file_repository.get_by_project_file(file_id)

    # ドライバーツリーでの使用を取得
    tree_usages = await self.tree_file_repository.get_by_project_file(file_id)

    # 使用情報を構築
    usages = []

    for usage in session_usages:
        usages.append(FileUsageItem(
            usage_type="analysis_session",
            target_id=usage.session_id,
            target_name=usage.session.name if usage.session else "",
            sheet_name=usage.sheet_name,
            used_at=usage.created_at,
        ))

    for usage in tree_usages:
        usages.append(FileUsageItem(
            usage_type="driver_tree",
            target_id=usage.tree_id,
            target_name=usage.tree.name if usage.tree else "",
            sheet_name=usage.sheet_name,
            used_at=usage.created_at,
        ))

    return ProjectFileUsageResponse(
        file_id=file_id,
        filename=file.original_filename,
        analysis_session_count=len(session_usages),
        driver_tree_count=len(tree_usages),
        total_usage_count=len(usages),
        usages=usages,
    )
```

---

## 6. カテゴリマスタ拡張

### 6.1 関連数式数追加

**対象**: `GET /api/v1/admin/category`, `GET /api/v1/admin/category/{category_id}`

#### 6.1.1 スキーマ変更

```python
# src/app/schemas/admin/category.py

class DriverTreeCategoryResponse(BaseCamelCaseORMModel):
    """カテゴリレスポンススキーマ。"""

    id: int = Field(..., description="ID")
    category_id: int = Field(..., description="業界分類ID")
    category_name: str = Field(..., description="業界分類名")
    industry_id: int = Field(..., description="業界名ID")
    industry_name: str = Field(..., description="業界名")
    driver_type_id: int = Field(..., description="ドライバー型ID")
    driver_type: str = Field(..., description="ドライバー型")

    # 追加フィールド
    formula_count: int = Field(default=0, description="関連数式数")

    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
```

#### 6.1.2 リポジトリ変更

```python
# src/app/repositories/admin/category.py

async def get_with_formula_count(self, category_id: int) -> dict | None:
    """関連数式数を含めてカテゴリを取得します。"""
    stmt = (
        select(
            DriverTreeCategory,
            func.count(DriverTreeFormula.id).label("formula_count"),
        )
        .outerjoin(
            DriverTreeFormula,
            DriverTreeFormula.category_id == DriverTreeCategory.id
        )
        .where(DriverTreeCategory.id == category_id)
        .group_by(DriverTreeCategory.id)
    )

    result = await self.session.execute(stmt)
    row = result.first()

    if not row:
        return None

    category, formula_count = row
    return {
        "category": category,
        "formula_count": formula_count,
    }


async def get_list_with_formula_counts(
    self,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[dict], int]:
    """関連数式数を含めてカテゴリ一覧を取得します。"""
    # カウント
    count_stmt = select(func.count(DriverTreeCategory.id))
    total = await self.session.scalar(count_stmt) or 0

    # データ取得
    stmt = (
        select(
            DriverTreeCategory,
            func.count(DriverTreeFormula.id).label("formula_count"),
        )
        .outerjoin(
            DriverTreeFormula,
            DriverTreeFormula.category_id == DriverTreeCategory.id
        )
        .group_by(DriverTreeCategory.id)
        .order_by(DriverTreeCategory.category_id)
        .offset(skip)
        .limit(limit)
    )

    result = await self.session.execute(stmt)
    rows = result.all()

    return [{"category": row[0], "formula_count": row[1]} for row in rows], total
```

---

## 7. ダッシュボード拡張

### 7.1 プロジェクト進捗API

**対象**: 新規エンドポイント `GET /api/v1/dashboard/progress`

#### 7.1.1 スキーマ追加

```python
# src/app/schemas/dashboard/dashboard.py に追加

class ProjectProgressItem(BaseCamelCaseModel):
    """プロジェクト進捗アイテム。

    Attributes:
        id (uuid.UUID): プロジェクトID
        name (str): プロジェクト名
        progress (int): 進捗率（0-100）
        total_sessions (int): 総セッション数
        completed_sessions (int): 完了セッション数
        total_trees (int): 総ツリー数
        completed_trees (int): 完了ツリー数
    """

    id: uuid.UUID = Field(..., description="プロジェクトID")
    name: str = Field(..., description="プロジェクト名")
    progress: int = Field(..., ge=0, le=100, description="進捗率")
    total_sessions: int = Field(default=0, description="総セッション数")
    completed_sessions: int = Field(default=0, description="完了セッション数")
    total_trees: int = Field(default=0, description="総ツリー数")
    completed_trees: int = Field(default=0, description="完了ツリー数")


class DashboardProgressResponse(BaseCamelCaseModel):
    """ダッシュボード進捗レスポンス。

    Attributes:
        project_progress (list[ProjectProgressItem]): プロジェクト進捗リスト
        total (int): 総プロジェクト数
        generated_at (datetime): 生成日時
    """

    project_progress: list[ProjectProgressItem] = Field(
        default_factory=list,
        description="プロジェクト進捗リスト"
    )
    total: int = Field(..., description="総プロジェクト数")
    generated_at: datetime = Field(..., description="生成日時")
```

#### 7.1.2 API追加

```python
# src/app/api/routes/v1/dashboard/dashboard.py に追加

@dashboard_router.get(
    "/progress",
    response_model=DashboardProgressResponse,
    summary="プロジェクト進捗取得",
    description="""
    ユーザーが所属するプロジェクトの進捗情報を取得します。
    """,
)
@handle_service_errors
async def get_project_progress(
    dashboard_service: DashboardServiceDep,
    current_user: CurrentUserAccountDep,
    limit: int = Query(10, ge=1, le=50, description="取得件数"),
) -> DashboardProgressResponse:
    """プロジェクト進捗を取得します。"""
    return await dashboard_service.get_project_progress(
        user_id=current_user.id,
        limit=limit,
    )
```

#### 7.1.3 サービス実装

```python
# src/app/services/dashboard/progress.py（新規）

class DashboardProgressService:
    """ダッシュボード進捗サービス。"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repository = ProjectRepository(session)
        self.session_repository = AnalysisSessionRepository(session)
        self.tree_repository = DriverTreeRepository(session)

    async def get_project_progress(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> DashboardProgressResponse:
        """プロジェクト進捗を取得します。"""
        # ユーザーが所属するプロジェクトを取得
        projects = await self.project_repository.get_user_projects(
            user_id=user_id,
            limit=limit,
        )

        progress_items = []

        for project in projects:
            # セッション統計
            session_stats = await self._get_session_stats(project.id)

            # ツリー統計
            tree_stats = await self._get_tree_stats(project.id)

            # 進捗率計算
            total_items = session_stats["total"] + tree_stats["total"]
            completed_items = session_stats["completed"] + tree_stats["completed"]
            progress = (
                int((completed_items / total_items) * 100)
                if total_items > 0
                else 0
            )

            progress_items.append(ProjectProgressItem(
                id=project.id,
                name=project.name,
                progress=progress,
                total_sessions=session_stats["total"],
                completed_sessions=session_stats["completed"],
                total_trees=tree_stats["total"],
                completed_trees=tree_stats["completed"],
            ))

        return DashboardProgressResponse(
            project_progress=progress_items,
            total=len(progress_items),
            generated_at=datetime.now(UTC),
        )

    async def _get_session_stats(self, project_id: uuid.UUID) -> dict:
        """セッション統計を取得します。"""
        stmt = (
            select(
                func.count(AnalysisSession.id).label("total"),
                func.count(
                    case(
                        (AnalysisSession.status == "completed", 1),
                        else_=None,
                    )
                ).label("completed"),
            )
            .where(AnalysisSession.project_id == project_id)
        )

        result = await self.session.execute(stmt)
        row = result.first()

        return {
            "total": row.total if row else 0,
            "completed": row.completed if row else 0,
        }

    async def _get_tree_stats(self, project_id: uuid.UUID) -> dict:
        """ツリー統計を取得します。"""
        stmt = (
            select(
                func.count(DriverTree.id).label("total"),
                func.count(
                    case(
                        (DriverTree.status == "completed", 1),
                        else_=None,
                    )
                ).label("completed"),
            )
            .where(DriverTree.project_id == project_id)
        )

        result = await self.session.execute(stmt)
        row = result.first()

        return {
            "total": row.total if row else 0,
            "completed": row.completed if row else 0,
        }
```

---

## 8. マイグレーション一覧

| ファイル名 | 内容 |
|-----------|------|
| `xxx_add_snapshot_description.py` | analysis_snapshotにname, descriptionカラム追加 |
| `xxx_add_validation_fields.py` | analysis_validation_masterにdescription, is_activeカラム追加 |

---

## 9. 実装優先度

| 優先度 | 項目 | 理由 |
|--------|------|------|
| 高 | 2.1 カテゴリ情報追加 | セッション詳細の基本情報、既存コード変更のみ |
| 高 | 3.1 Validationフィールド追加 | マスタ管理の基本機能 |
| 高 | 4.4 カラム情報取得 | ツリー編集の必須機能 |
| 中 | 2.4 スナップショット説明文 | UX向上、マイグレーション必要 |
| 中 | 4.2 ツリー施策一覧 | 施策管理画面に必要 |
| 中 | 5.1 ファイル使用状況 | 既存実装の確認のみ |
| 中 | 6.1 カテゴリ数式数 | マスタ管理のUX向上 |
| 低 | 2.2 インサイト情報 | 将来的な分析機能 |
| 低 | 2.3 関連セッション | 将来的な機能 |
| 低 | 2.5 スナップショット復元 | 将来的な機能 |
| 低 | 7.1 プロジェクト進捗 | ダッシュボード拡張 |

---

## 10. 実装時の注意事項

### 10.1 既存APIへの影響

- 既存レスポンスへのフィールド追加は後方互換性あり
- 新規フィールドはデフォルト値を設定

### 10.2 パフォーマンス

- リレーション展開は`selectinload`でN+1を防止
- 集計クエリは適切なインデックスを活用

### 10.3 テスト

- 新規フィールドの有無でAPIレスポンスが正常に動作することを確認
- 既存テストが破壊されないことを確認
