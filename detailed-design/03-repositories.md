# システム管理機能 詳細設計書 - リポジトリ層

## 1. 概要

本ドキュメントでは、システム管理機能（SA-001〜SA-043）で追加するリポジトリの詳細設計を定義する。

### 1.1 既存パターンへの準拠

既存のリポジトリ実装パターンに従い、以下の規約を適用する：

- `BaseRepository[ModelType, IDType]` を継承
- `flush()` のみ実行（`commit()` はサービス層の責任）
- `selectinload` でN+1問題を回避
- 複雑なクエリは専用メソッドで実装

### 1.2 ファイル構成

```
src/app/repositories/admin/
├── __init__.py
├── user_activity_repository.py      # 操作履歴
├── audit_log_repository.py          # 監査ログ
├── system_setting_repository.py     # システム設定
├── announcement_repository.py       # お知らせ
├── notification_template_repository.py  # 通知テンプレート
├── system_alert_repository.py       # アラート
└── user_session_repository.py       # ユーザーセッション
```

---

## 2. リポジトリ詳細設計

### 2.1 UserActivityRepository（操作履歴リポジトリ）

**ファイル**: `src/app/repositories/admin/user_activity_repository.py`

**対応ユースケース**: SA-001〜SA-006

```python
"""操作履歴リポジトリ。

このモジュールは、ユーザー操作履歴のデータアクセスを提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit.user_activity import UserActivity
from app.repositories.base import BaseRepository


class UserActivityRepository(BaseRepository[UserActivity, uuid.UUID]):
    """操作履歴リポジトリ。

    ユーザー操作履歴のCRUD操作と検索機能を提供します。

    メソッド:
        - get_with_user: ユーザー情報付きで取得
        - list_with_filters: フィルタ付き一覧取得
        - list_errors: エラーのみ取得
        - count_with_filters: フィルタ付きカウント
        - get_statistics: 統計情報取得
        - delete_old_records: 古いレコード削除
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(UserActivity, db)

    async def get_with_user(self, id: uuid.UUID) -> UserActivity | None:
        """ユーザー情報付きで操作履歴を取得します。

        Args:
            id: 操作履歴ID

        Returns:
            UserActivity | None: 操作履歴（ユーザー情報付き）
        """
        query = (
            select(UserActivity)
            .options(selectinload(UserActivity.user))
            .where(UserActivity.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        user_id: uuid.UUID | None = None,
        action_type: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        has_error: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserActivity]:
        """フィルタ付きで操作履歴一覧を取得します。

        Args:
            user_id: ユーザーID
            action_type: 操作種別
            resource_type: リソース種別
            start_date: 開始日時
            end_date: 終了日時
            has_error: エラーのみ
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserActivity]: 操作履歴リスト
        """
        query = select(UserActivity).options(selectinload(UserActivity.user))

        # フィルタ条件を構築
        conditions = []

        if user_id:
            conditions.append(UserActivity.user_id == user_id)
        if action_type:
            conditions.append(UserActivity.action_type == action_type)
        if resource_type:
            conditions.append(UserActivity.resource_type == resource_type)
        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)
        if has_error is True:
            conditions.append(UserActivity.error_message.isnot(None))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(UserActivity.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_errors(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserActivity]:
        """エラー履歴のみを取得します。

        Args:
            start_date: 開始日時
            end_date: 終了日時
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserActivity]: エラー履歴リスト
        """
        return await self.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            has_error=True,
            skip=skip,
            limit=limit,
        )

    async def count_with_filters(
        self,
        *,
        user_id: uuid.UUID | None = None,
        action_type: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        has_error: bool | None = None,
    ) -> int:
        """フィルタ付きでカウントを取得します。

        Args:
            user_id: ユーザーID
            action_type: 操作種別
            resource_type: リソース種別
            start_date: 開始日時
            end_date: 終了日時
            has_error: エラーのみ

        Returns:
            int: レコード数
        """
        query = select(func.count()).select_from(UserActivity)

        conditions = []

        if user_id:
            conditions.append(UserActivity.user_id == user_id)
        if action_type:
            conditions.append(UserActivity.action_type == action_type)
        if resource_type:
            conditions.append(UserActivity.resource_type == resource_type)
        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)
        if has_error is True:
            conditions.append(UserActivity.error_message.isnot(None))

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_statistics(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """統計情報を取得します。

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            dict: 統計情報
                - total_count: 総件数
                - error_count: エラー件数
                - average_duration_ms: 平均処理時間
        """
        conditions = []

        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        # 総件数
        total_query = select(func.count()).select_from(UserActivity).where(where_clause)
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar_one()

        # エラー件数
        error_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(and_(where_clause, UserActivity.error_message.isnot(None)))
        )
        error_result = await self.db.execute(error_query)
        error_count = error_result.scalar_one()

        # 平均処理時間
        avg_query = (
            select(func.avg(UserActivity.duration_ms))
            .select_from(UserActivity)
            .where(where_clause)
        )
        avg_result = await self.db.execute(avg_query)
        average_duration_ms = avg_result.scalar_one() or 0

        return {
            "total_count": total_count,
            "error_count": error_count,
            "average_duration_ms": float(average_duration_ms),
        }

    async def delete_old_records(self, before_date: datetime) -> int:
        """古いレコードを削除します。

        Args:
            before_date: この日付より前のレコードを削除

        Returns:
            int: 削除件数
        """
        from sqlalchemy import delete

        query = delete(UserActivity).where(UserActivity.created_at < before_date)
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount
```

---

### 2.2 AuditLogRepository（監査ログリポジトリ）

**ファイル**: `src/app/repositories/admin/audit_log_repository.py`

**対応ユースケース**: SA-012〜SA-016

```python
"""監査ログリポジトリ。

このモジュールは、監査ログのデータアクセスを提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog, uuid.UUID]):
    """監査ログリポジトリ。

    監査ログのCRUD操作と検索機能を提供します。

    メソッド:
        - get_with_user: ユーザー情報付きで取得
        - list_with_filters: フィルタ付き一覧取得
        - list_by_event_type: イベント種別で取得
        - list_by_resource: リソースで取得
        - count_with_filters: フィルタ付きカウント
        - delete_old_records: 古いレコード削除
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(AuditLog, db)

    async def get_with_user(self, id: uuid.UUID) -> AuditLog | None:
        """ユーザー情報付きで監査ログを取得します。

        Args:
            id: 監査ログID

        Returns:
            AuditLog | None: 監査ログ（ユーザー情報付き）
        """
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        event_type: str | None = None,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        severity: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """フィルタ付きで監査ログ一覧を取得します。

        Args:
            event_type: イベント種別
            user_id: ユーザーID
            resource_type: リソース種別
            resource_id: リソースID
            severity: 重要度
            start_date: 開始日時
            end_date: 終了日時
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AuditLog]: 監査ログリスト
        """
        query = select(AuditLog).options(selectinload(AuditLog.user))

        conditions = []

        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if severity:
            conditions.append(AuditLog.severity == severity)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_event_type(
        self,
        event_type: str,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """イベント種別で監査ログを取得します。

        Args:
            event_type: イベント種別（DATA_CHANGE/ACCESS/SECURITY）
            start_date: 開始日時
            end_date: 終了日時
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AuditLog]: 監査ログリスト
        """
        return await self.list_with_filters(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """リソースで監査ログを取得します。

        Args:
            resource_type: リソース種別
            resource_id: リソースID
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AuditLog]: 監査ログリスト
        """
        return await self.list_with_filters(
            resource_type=resource_type,
            resource_id=resource_id,
            skip=skip,
            limit=limit,
        )

    async def count_with_filters(
        self,
        *,
        event_type: str | None = None,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        severity: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """フィルタ付きでカウントを取得します。

        Args:
            event_type: イベント種別
            user_id: ユーザーID
            resource_type: リソース種別
            resource_id: リソースID
            severity: 重要度
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            int: レコード数
        """
        query = select(func.count()).select_from(AuditLog)

        conditions = []

        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if severity:
            conditions.append(AuditLog.severity == severity)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def delete_old_records(self, before_date: datetime) -> int:
        """古いレコードを削除します。

        Args:
            before_date: この日付より前のレコードを削除

        Returns:
            int: 削除件数
        """
        from sqlalchemy import delete

        query = delete(AuditLog).where(AuditLog.created_at < before_date)
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount
```

---

### 2.3 SystemSettingRepository（システム設定リポジトリ）

**ファイル**: `src/app/repositories/admin/system_setting_repository.py`

**対応ユースケース**: SA-017〜SA-020

```python
"""システム設定リポジトリ。

このモジュールは、システム設定のデータアクセスを提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system.system_setting import SystemSetting
from app.repositories.base import BaseRepository


class SystemSettingRepository(BaseRepository[SystemSetting, uuid.UUID]):
    """システム設定リポジトリ。

    システム設定のCRUD操作を提供します。

    メソッド:
        - get_by_category_and_key: カテゴリとキーで取得
        - list_by_category: カテゴリで一覧取得
        - list_all_grouped: カテゴリ別にグループ化して取得
        - get_value: 設定値を取得
        - set_value: 設定値を設定
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(SystemSetting, db)

    async def get_by_category_and_key(
        self,
        category: str,
        key: str,
    ) -> SystemSetting | None:
        """カテゴリとキーで設定を取得します。

        Args:
            category: カテゴリ
            key: 設定キー

        Returns:
            SystemSetting | None: システム設定
        """
        query = select(SystemSetting).where(
            SystemSetting.category == category,
            SystemSetting.key == key,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_category(self, category: str) -> list[SystemSetting]:
        """カテゴリで設定一覧を取得します。

        Args:
            category: カテゴリ

        Returns:
            list[SystemSetting]: システム設定リスト
        """
        query = (
            select(SystemSetting)
            .where(SystemSetting.category == category)
            .order_by(SystemSetting.key)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all_grouped(self) -> dict[str, list[SystemSetting]]:
        """全設定をカテゴリ別にグループ化して取得します。

        Returns:
            dict[str, list[SystemSetting]]: カテゴリ別設定
        """
        query = select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
        result = await self.db.execute(query)
        settings = list(result.scalars().all())

        grouped: dict[str, list[SystemSetting]] = {}
        for setting in settings:
            if setting.category not in grouped:
                grouped[setting.category] = []
            grouped[setting.category].append(setting)

        return grouped

    async def get_value(
        self,
        category: str,
        key: str,
        default: any = None,
    ) -> any:
        """設定値を取得します。

        Args:
            category: カテゴリ
            key: 設定キー
            default: デフォルト値

        Returns:
            any: 設定値
        """
        setting = await self.get_by_category_and_key(category, key)
        if setting is None:
            return default
        return setting.value

    async def set_value(
        self,
        category: str,
        key: str,
        value: any,
        updated_by: uuid.UUID | None = None,
    ) -> SystemSetting:
        """設定値を設定します。

        Args:
            category: カテゴリ
            key: 設定キー
            value: 設定値
            updated_by: 更新者ID

        Returns:
            SystemSetting: 更新された設定
        """
        setting = await self.get_by_category_and_key(category, key)
        if setting is None:
            raise ValueError(f"Setting not found: {category}/{key}")

        setting.value = value
        if updated_by:
            setting.updated_by = updated_by

        await self.db.flush()
        await self.db.refresh(setting)
        return setting
```

---

### 2.4 AnnouncementRepository（お知らせリポジトリ）

**ファイル**: `src/app/repositories/admin/announcement_repository.py`

**対応ユースケース**: SA-033〜SA-034

```python
"""お知らせリポジトリ。

このモジュールは、システムお知らせのデータアクセスを提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.system.system_announcement import SystemAnnouncement
from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository[SystemAnnouncement, uuid.UUID]):
    """お知らせリポジトリ。

    システムお知らせのCRUD操作と検索機能を提供します。

    メソッド:
        - get_with_creator: 作成者情報付きで取得
        - list_active: アクティブなお知らせを取得
        - list_for_user: ユーザー向けお知らせを取得
        - list_all: 全お知らせを取得（管理用）
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(SystemAnnouncement, db)

    async def get_with_creator(self, id: uuid.UUID) -> SystemAnnouncement | None:
        """作成者情報付きでお知らせを取得します。

        Args:
            id: お知らせID

        Returns:
            SystemAnnouncement | None: お知らせ（作成者情報付き）
        """
        query = (
            select(SystemAnnouncement)
            .options(selectinload(SystemAnnouncement.creator))
            .where(SystemAnnouncement.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        current_time: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAnnouncement]:
        """アクティブなお知らせを取得します。

        Args:
            current_time: 基準時刻（デフォルト: 現在時刻）
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAnnouncement]: お知らせリスト
        """
        if current_time is None:
            current_time = datetime.now(UTC)

        query = (
            select(SystemAnnouncement)
            .options(selectinload(SystemAnnouncement.creator))
            .where(
                and_(
                    SystemAnnouncement.is_active == True,
                    SystemAnnouncement.start_at <= current_time,
                    or_(
                        SystemAnnouncement.end_at.is_(None),
                        SystemAnnouncement.end_at >= current_time,
                    ),
                )
            )
            .order_by(SystemAnnouncement.priority, SystemAnnouncement.start_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_user(
        self,
        user_roles: list[str],
        *,
        current_time: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAnnouncement]:
        """ユーザー向けお知らせを取得します。

        対象ロールが空の場合は全員向け、指定がある場合はユーザーのロールに一致するもののみ。

        Args:
            user_roles: ユーザーのロールリスト
            current_time: 基準時刻
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAnnouncement]: お知らせリスト
        """
        if current_time is None:
            current_time = datetime.now(UTC)

        # target_roles が空または NULL の場合は全員向け
        # それ以外はユーザーのロールに一致するもの
        query = (
            select(SystemAnnouncement)
            .where(
                and_(
                    SystemAnnouncement.is_active == True,
                    SystemAnnouncement.start_at <= current_time,
                    or_(
                        SystemAnnouncement.end_at.is_(None),
                        SystemAnnouncement.end_at >= current_time,
                    ),
                    or_(
                        SystemAnnouncement.target_roles.is_(None),
                        SystemAnnouncement.target_roles == [],
                        # JSONBの配列と重複チェック
                        SystemAnnouncement.target_roles.op("?|")(user_roles),
                    ),
                )
            )
            .order_by(SystemAnnouncement.priority, SystemAnnouncement.start_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAnnouncement]:
        """全お知らせを取得します（管理用）。

        Args:
            is_active: アクティブフィルタ
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAnnouncement]: お知らせリスト
        """
        query = select(SystemAnnouncement).options(
            selectinload(SystemAnnouncement.creator)
        )

        if is_active is not None:
            query = query.where(SystemAnnouncement.is_active == is_active)

        query = query.order_by(SystemAnnouncement.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
```

---

### 2.5 NotificationTemplateRepository（通知テンプレートリポジトリ）

**ファイル**: `src/app/repositories/admin/notification_template_repository.py`

**対応ユースケース**: SA-032

```python
"""通知テンプレートリポジトリ。

このモジュールは、通知テンプレートのデータアクセスを提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system.notification_template import NotificationTemplate
from app.repositories.base import BaseRepository


class NotificationTemplateRepository(BaseRepository[NotificationTemplate, uuid.UUID]):
    """通知テンプレートリポジトリ。

    通知テンプレートのCRUD操作を提供します。

    メソッド:
        - get_by_event_type: イベント種別で取得
        - list_active: アクティブなテンプレートを取得
        - list_all: 全テンプレートを取得
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(NotificationTemplate, db)

    async def get_by_event_type(self, event_type: str) -> NotificationTemplate | None:
        """イベント種別でテンプレートを取得します。

        Args:
            event_type: イベント種別

        Returns:
            NotificationTemplate | None: 通知テンプレート
        """
        query = select(NotificationTemplate).where(
            NotificationTemplate.event_type == event_type
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationTemplate]:
        """アクティブなテンプレートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[NotificationTemplate]: テンプレートリスト
        """
        query = (
            select(NotificationTemplate)
            .where(NotificationTemplate.is_active == True)
            .order_by(NotificationTemplate.event_type)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationTemplate]:
        """全テンプレートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[NotificationTemplate]: テンプレートリスト
        """
        query = (
            select(NotificationTemplate)
            .order_by(NotificationTemplate.event_type)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

---

### 2.6 SystemAlertRepository（システムアラートリポジトリ）

**ファイル**: `src/app/repositories/admin/system_alert_repository.py`

**対応ユースケース**: SA-031

```python
"""システムアラートリポジトリ。

このモジュールは、システムアラートのデータアクセスを提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.system.system_alert import SystemAlert
from app.repositories.base import BaseRepository


class SystemAlertRepository(BaseRepository[SystemAlert, uuid.UUID]):
    """システムアラートリポジトリ。

    システムアラートのCRUD操作を提供します。

    メソッド:
        - get_with_creator: 作成者情報付きで取得
        - list_enabled: 有効なアラートを取得
        - list_by_condition_type: 条件種別でアラートを取得
        - list_all: 全アラートを取得
        - update_trigger_info: 発火情報を更新
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(SystemAlert, db)

    async def get_with_creator(self, id: uuid.UUID) -> SystemAlert | None:
        """作成者情報付きでアラートを取得します。

        Args:
            id: アラートID

        Returns:
            SystemAlert | None: アラート（作成者情報付き）
        """
        query = (
            select(SystemAlert)
            .options(selectinload(SystemAlert.creator))
            .where(SystemAlert.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_enabled(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAlert]:
        """有効なアラートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAlert]: アラートリスト
        """
        query = (
            select(SystemAlert)
            .options(selectinload(SystemAlert.creator))
            .where(SystemAlert.is_enabled == True)
            .order_by(SystemAlert.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_condition_type(
        self,
        condition_type: str,
        *,
        enabled_only: bool = True,
    ) -> list[SystemAlert]:
        """条件種別でアラートを取得します。

        Args:
            condition_type: 条件種別
            enabled_only: 有効なアラートのみ

        Returns:
            list[SystemAlert]: アラートリスト
        """
        query = select(SystemAlert).where(SystemAlert.condition_type == condition_type)

        if enabled_only:
            query = query.where(SystemAlert.is_enabled == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAlert]:
        """全アラートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAlert]: アラートリスト
        """
        query = (
            select(SystemAlert)
            .options(selectinload(SystemAlert.creator))
            .order_by(SystemAlert.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_trigger_info(
        self,
        alert_id: uuid.UUID,
        triggered_at: datetime,
    ) -> SystemAlert | None:
        """発火情報を更新します。

        Args:
            alert_id: アラートID
            triggered_at: 発火日時

        Returns:
            SystemAlert | None: 更新されたアラート
        """
        alert = await self.get(alert_id)
        if alert is None:
            return None

        alert.last_triggered_at = triggered_at
        alert.trigger_count += 1

        await self.db.flush()
        await self.db.refresh(alert)
        return alert
```

---

### 2.7 UserSessionRepository（ユーザーセッションリポジトリ）

**ファイル**: `src/app/repositories/admin/user_session_repository.py`

**対応ユースケース**: SA-035〜SA-036

```python
"""ユーザーセッションリポジトリ。

このモジュールは、ユーザーセッションのデータアクセスを提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_account.user_session import UserSession
from app.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession, uuid.UUID]):
    """ユーザーセッションリポジトリ。

    ユーザーセッションのCRUD操作を提供します。

    メソッド:
        - get_with_user: ユーザー情報付きで取得
        - get_by_token_hash: トークンハッシュで取得
        - list_active: アクティブセッションを取得
        - list_by_user: ユーザーのセッションを取得
        - count_active: アクティブセッション数を取得
        - count_logins_today: 本日のログイン数を取得
        - terminate_session: セッションを終了
        - terminate_all_user_sessions: ユーザーの全セッションを終了
        - cleanup_expired: 期限切れセッションをクリーンアップ
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(UserSession, db)

    async def get_with_user(self, id: uuid.UUID) -> UserSession | None:
        """ユーザー情報付きでセッションを取得します。

        Args:
            id: セッションID

        Returns:
            UserSession | None: セッション（ユーザー情報付き）
        """
        query = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(UserSession.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        """トークンハッシュでセッションを取得します。

        Args:
            token_hash: トークンハッシュ

        Returns:
            UserSession | None: セッション
        """
        query = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                and_(
                    UserSession.session_token_hash == token_hash,
                    UserSession.is_active == True,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserSession]:
        """アクティブセッションを取得します。

        Args:
            user_id: ユーザーID
            ip_address: IPアドレス
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserSession]: セッションリスト
        """
        now = datetime.now(UTC)

        query = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > now,
                )
            )
        )

        if user_id:
            query = query.where(UserSession.user_id == user_id)
        if ip_address:
            query = query.where(UserSession.ip_address == ip_address)

        query = query.order_by(UserSession.last_activity_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserSession]:
        """ユーザーのセッションを取得します。

        Args:
            user_id: ユーザーID
            active_only: アクティブのみ
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserSession]: セッションリスト
        """
        query = select(UserSession).where(UserSession.user_id == user_id)

        if active_only:
            now = datetime.now(UTC)
            query = query.where(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > now,
                )
            )

        query = query.order_by(UserSession.last_activity_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_active(self) -> int:
        """アクティブセッション数を取得します。

        Returns:
            int: アクティブセッション数
        """
        now = datetime.now(UTC)

        query = (
            select(func.count())
            .select_from(UserSession)
            .where(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > now,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_logins_today(self) -> int:
        """本日のログイン数を取得します。

        Returns:
            int: 本日のログイン数
        """
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(func.count())
            .select_from(UserSession)
            .where(UserSession.login_at >= today_start)
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def terminate_session(
        self,
        session_id: uuid.UUID,
        reason: str,
    ) -> UserSession | None:
        """セッションを終了します。

        Args:
            session_id: セッションID
            reason: 終了理由

        Returns:
            UserSession | None: 終了したセッション
        """
        session = await self.get(session_id)
        if session is None:
            return None

        now = datetime.now(UTC)
        session.is_active = False
        session.logout_at = now
        session.logout_reason = reason

        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def terminate_all_user_sessions(
        self,
        user_id: uuid.UUID,
        reason: str,
    ) -> int:
        """ユーザーの全セッションを終了します。

        Args:
            user_id: ユーザーID
            reason: 終了理由

        Returns:
            int: 終了したセッション数
        """
        now = datetime.now(UTC)

        query = (
            update(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                )
            )
            .values(
                is_active=False,
                logout_at=now,
                logout_reason=reason,
            )
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount

    async def cleanup_expired(self, before_date: datetime) -> int:
        """期限切れセッションをクリーンアップします。

        非アクティブかつ指定日より前のセッションを削除します。

        Args:
            before_date: この日付より前のセッションを削除

        Returns:
            int: 削除件数
        """
        from sqlalchemy import delete

        query = delete(UserSession).where(
            and_(
                UserSession.is_active == False,
                UserSession.logout_at < before_date,
            )
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount
```

---

## 3. __init__.py ファイル

### 3.1 admin/__init__.py

```python
"""システム管理リポジトリ。"""

from app.repositories.admin.announcement_repository import AnnouncementRepository
from app.repositories.admin.audit_log_repository import AuditLogRepository
from app.repositories.admin.notification_template_repository import (
    NotificationTemplateRepository,
)
from app.repositories.admin.system_alert_repository import SystemAlertRepository
from app.repositories.admin.system_setting_repository import SystemSettingRepository
from app.repositories.admin.user_activity_repository import UserActivityRepository
from app.repositories.admin.user_session_repository import UserSessionRepository

__all__ = [
    "UserActivityRepository",
    "AuditLogRepository",
    "SystemSettingRepository",
    "AnnouncementRepository",
    "NotificationTemplateRepository",
    "SystemAlertRepository",
    "UserSessionRepository",
]
```

---

## 4. 注意事項

### 4.1 トランザクション管理

- すべてのリポジトリメソッドは `flush()` のみ実行
- `commit()` はサービス層の責任
- 複数の操作を1つのトランザクションにまとめることが可能

### 4.2 N+1問題対策

- 関連エンティティを取得する場合は `selectinload` を使用
- `get_with_user` 等の専用メソッドで明示的にロード

### 4.3 パフォーマンス考慮

- 大量データの一括削除は `delete()` 文を使用
- カウントクエリは `func.count()` で効率化
- インデックスを活用したクエリ設計

### 4.4 日時の扱い

- すべての日時はUTCで統一
- `datetime.now(UTC)` を使用
- タイムゾーン付きdatetimeを期待
