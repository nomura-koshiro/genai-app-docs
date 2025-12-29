"""シードデータローダー。

このモジュールは、CSVファイルからシードデータを読み込み、
データベースに投入する機能を提供します。

開発・テスト環境専用です。本番環境では使用しないでください。
"""

import csv
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import (
    AnalysisChat,
    AnalysisDummyChartMaster,
    AnalysisDummyFormulaMaster,
    AnalysisFile,
    AnalysisGraphAxisMaster,
    AnalysisIssueMaster,
    AnalysisSession,
    AnalysisSnapshot,
    AnalysisStep,
    AnalysisValidationMaster,
    DriverTree,
    DriverTreeCategory,
    DriverTreeDataFrame,
    DriverTreeFile,
    DriverTreeFormula,
    DriverTreeNode,
    DriverTreePolicy,
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
    Project,
    ProjectFile,
    ProjectMember,
    UserAccount,
)
from app.models.project.project_member import ProjectRole

logger = get_logger(__name__)

# シードデータディレクトリのパス
SEED_DATA_DIR = Path(__file__).parent / "data"
MASTER_DIR = SEED_DATA_DIR / "master"
TRANSACTION_DIR = SEED_DATA_DIR / "transaction"


def parse_uuid(value: str) -> uuid.UUID | None:
    """UUID文字列をパースします。空文字列の場合はNoneを返します。"""
    if not value or value.strip() == "":
        return None
    return uuid.UUID(value)


def parse_bool(value: str) -> bool:
    """ブール値をパースします。"""
    return value.lower() in ("true", "1", "yes")


def parse_json(value: str) -> Any:
    """JSON文字列をパースします。"""
    if not value or value.strip() == "":
        return None
    return json.loads(value)


def parse_int(value: str) -> int | None:
    """整数値をパースします。空文字列の場合はNoneを返します。"""
    if not value or value.strip() == "":
        return None
    return int(value)


def parse_float(value: str) -> float | None:
    """浮動小数点数をパースします。空文字列の場合はNoneを返します。"""
    if not value or value.strip() == "":
        return None
    return float(value)


def parse_date(value: str) -> "date | None":
    """日付文字列をパースします。空文字列の場合はNoneを返します。"""
    from datetime import date as date_type

    if not value or value.strip() == "":
        return None
    # YYYY-MM-DD形式
    return date_type.fromisoformat(value)


def parse_datetime(value: str) -> "datetime | None":
    """日時文字列をパースします。空文字列の場合はNoneを返します。"""
    if not value or value.strip() == "":
        return None
    # ISO 8601形式（末尾のZはUTCを示す）
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def parse_decimal(value: str) -> "Decimal | None":
    """Decimal値をパースします。空文字列の場合はNoneを返します。"""
    from decimal import Decimal

    if not value or value.strip() == "":
        return None
    return Decimal(value)


def read_csv(file_path: Path) -> list[dict[str, str]]:
    """CSVファイルを読み込みます。"""
    if not file_path.exists():
        logger.warning(f"CSVファイルが見つかりません: {file_path}")
        return []

    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_json(file_path: Path) -> list[dict] | dict:
    """JSONファイルを読み込みます。"""
    if not file_path.exists():
        logger.warning(f"JSONファイルが見つかりません: {file_path}")
        return []

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


async def load_user_accounts(session: AsyncSession) -> int:
    """ユーザーアカウントを読み込みます。"""
    rows = read_csv(MASTER_DIR / "user_account.csv")
    count = 0

    for row in rows:
        user_id = parse_uuid(row["id"])
        # 既存チェック
        existing = await session.execute(select(UserAccount).where(UserAccount.id == user_id))
        if existing.scalar_one_or_none():
            continue

        user = UserAccount(
            id=user_id,
            azure_oid=row["azure_oid"],
            email=row["email"],
            display_name=row["display_name"],
            roles=parse_json(row["roles"]),
            is_active=parse_bool(row["is_active"]),
        )
        session.add(user)
        count += 1

    return count


async def load_analysis_validation_masters(session: AsyncSession) -> int:
    """分析検証マスタを読み込みます。"""
    rows = read_csv(MASTER_DIR / "analysis_validation_master.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisValidationMaster).where(AnalysisValidationMaster.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisValidationMaster(
            id=record_id,
            name=row["name"],
            validation_order=int(row["validation_order"]),
        )
        session.add(record)
        count += 1

    return count


def load_dummy_input_json(record_id: uuid.UUID) -> bytes | None:
    """ダミー入力JSONファイルを読み込みます。"""
    json_file_path = MASTER_DIR / "analysis_issue_master_dummy_input" / f"{record_id}.json"
    if not json_file_path.exists():
        return None

    with open(json_file_path, encoding="utf-8") as f:
        content = f.read()
    return content.encode("utf-8")


def load_dummy_chart_json(file_name: str) -> bytes | None:
    """ダミーチャートJSONファイルを読み込みます。"""
    json_file_path = MASTER_DIR / "analysis_issue_master_dummy_chart" / f"{file_name}"
    if not json_file_path.exists():
        return None

    with open(json_file_path, encoding="utf-8") as f:
        content = f.read()
    return content.encode("utf-8")


async def load_analysis_issue_masters(session: AsyncSession) -> int:
    """分析課題マスタを読み込みます。"""
    rows = read_csv(MASTER_DIR / "analysis_issue_master.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        if record_id is None:
            continue

        existing = await session.execute(select(AnalysisIssueMaster).where(AnalysisIssueMaster.id == record_id))
        if existing.scalar_one_or_none():
            continue

        # ダミー入力JSONファイルを読み込む
        dummy_input_data = load_dummy_input_json(record_id)

        record = AnalysisIssueMaster(
            id=record_id,
            validation_id=parse_uuid(row["validation_id"]),
            name=row["name"],
            description=row.get("description") or None,
            agent_prompt=row.get("agent_prompt") or None,
            initial_msg=row.get("initial_msg") or None,
            dummy_hint=row.get("dummy_hint") or None,
            dummy_input=dummy_input_data,
            issue_order=int(row["issue_order"]),
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_graph_axis_masters(session: AsyncSession) -> int:
    """分析グラフ軸マスタを読み込みます。"""
    rows = read_csv(MASTER_DIR / "analysis_graph_axis_master.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisGraphAxisMaster).where(AnalysisGraphAxisMaster.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisGraphAxisMaster(
            id=record_id,
            issue_id=parse_uuid(row["issue_id"]),
            name=row["name"],
            option=row["option"],
            multiple=parse_bool(row["multiple"]),
            axis_order=int(row["axis_order"]),
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_dummy_formula_masters(session: AsyncSession) -> int:
    """分析ダミー数式マスタを読み込みます。"""
    rows = read_csv(MASTER_DIR / "analysis_dummy_formula_master.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisDummyFormulaMaster).where(AnalysisDummyFormulaMaster.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisDummyFormulaMaster(
            id=record_id,
            issue_id=parse_uuid(row["issue_id"]),
            name=row["name"],
            value=row["value"],
            formula_order=int(row["formula_order"]),
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_dummy_chart_masters(session: AsyncSession) -> int:
    """分析ダミーチャートマスタを読み込みます。"""
    rows = read_csv(MASTER_DIR / "analysis_dummy_chart_master.csv")
    count = 0
    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisDummyChartMaster).where(AnalysisDummyChartMaster.id == record_id))
        if existing.scalar_one_or_none():
            continue
        issue_id = parse_uuid(row["issue_id"])
        chart_file = row["chart_file"]
        chart_order = int(row["chart_order"])
        chart_data = load_dummy_chart_json(chart_file)

        record = AnalysisDummyChartMaster(
            id=record_id,
            issue_id=issue_id,
            chart=chart_data,
            chart_order=chart_order,
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_categories(session: AsyncSession) -> int:
    """ドライバーツリーカテゴリマスタを読み込みます。"""
    records = read_json(MASTER_DIR / "driver_tree" / "driver_tree_category.json")
    count = 0

    for record_data in records:
        # 既存チェック（category_id + industry_id + driver_type_id の組み合わせ）
        existing = await session.execute(
            select(DriverTreeCategory).where(
                DriverTreeCategory.category_id == record_data["category_id"],
                DriverTreeCategory.industry_id == record_data["industry_id"],
                DriverTreeCategory.driver_type_id == record_data["driver_type_id"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeCategory(
            category_id=record_data["category_id"],
            category_name=record_data["category_name"],
            industry_id=record_data["industry_id"],
            industry_name=record_data["industry_name"],
            driver_type_id=record_data["driver_type_id"],
            driver_type=record_data["driver_type"],
            description=record_data.get("description"),
            created_by=parse_uuid(record_data.get("created_by", "")),
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_formulas(session: AsyncSession) -> int:
    """ドライバーツリー数式マスタを読み込みます。"""
    records = read_json(MASTER_DIR / "driver_tree" / "driver_tree_formula.json")
    count = 0

    for record_data in records:
        # 既存チェック（driver_type_id + kpi の組み合わせ）
        existing = await session.execute(
            select(DriverTreeFormula).where(
                DriverTreeFormula.driver_type_id == record_data["driver_type_id"],
                DriverTreeFormula.kpi == record_data["kpi"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeFormula(
            driver_type_id=record_data["driver_type_id"],
            driver_type=record_data["driver_type"],
            kpi=record_data["kpi"],
            formulas=record_data["formulas"],
        )
        session.add(record)
        count += 1

    return count


async def load_projects(session: AsyncSession) -> int:
    """プロジェクトを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "project.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(Project).where(Project.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = Project(
            id=record_id,
            name=row["name"],
            code=row["code"],
            description=row.get("description") or None,
            is_active=parse_bool(row["is_active"]),
            created_by=parse_uuid(row["created_by"]),
            start_date=parse_date(row.get("start_date", "")),
            end_date=parse_date(row.get("end_date", "")),
            budget=parse_decimal(row.get("budget", "")),
        )
        session.add(record)
        count += 1

    return count


async def load_project_members(session: AsyncSession) -> int:
    """プロジェクトメンバーを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "project_member.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(ProjectMember).where(ProjectMember.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = ProjectMember(
            id=record_id,
            project_id=parse_uuid(row["project_id"]),
            user_id=parse_uuid(row["user_id"]),
            role=ProjectRole(row["role"]),
            added_by=parse_uuid(row["added_by"]) if row.get("added_by") else None,
            last_activity_at=parse_datetime(row.get("last_activity_at", "")),
        )
        session.add(record)
        count += 1

    return count


async def load_project_files(session: AsyncSession) -> int:
    """プロジェクトファイルを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "project_file.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(ProjectFile).where(ProjectFile.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = ProjectFile(
            id=record_id,
            project_id=parse_uuid(row["project_id"]),
            filename=row["filename"],
            original_filename=row["original_filename"],
            file_path=row["file_path"],
            file_size=int(row["file_size"]),
            mime_type=row.get("mime_type") or None,
            uploaded_by=parse_uuid(row["uploaded_by"]),
            uploaded_at=datetime.now(UTC),
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_nodes(session: AsyncSession) -> int:
    """ドライバーツリーノードを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree_node.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTreeNode).where(DriverTreeNode.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeNode(
            id=record_id,
            label=row["label"],
            position_x=parse_int(row["position_x"]),
            position_y=parse_int(row["position_y"]),
            node_type=row["node_type"],
            data_frame_id=parse_uuid(row["data_frame_id"]) if row.get("data_frame_id") else None,
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_files(session: AsyncSession) -> int:
    """ドライバーツリーファイルを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree_file.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTreeFile).where(DriverTreeFile.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeFile(
            id=record_id,
            project_file_id=parse_uuid(row["project_file_id"]),
            sheet_name=row["sheet_name"],
            axis_config=parse_json(row["axis_config"]),
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_data_frames(session: AsyncSession) -> int:
    """ドライバーツリーデータフレームを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree_data_frame.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTreeDataFrame).where(DriverTreeDataFrame.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeDataFrame(
            id=record_id,
            driver_tree_file_id=parse_uuid(row["driver_tree_file_id"]),
            column_name=row["column_name"],
            data=parse_json(row["data"]) if row.get("data") else None,
        )
        session.add(record)
        count += 1

    return count


async def load_driver_trees(session: AsyncSession) -> int:
    """ドライバーツリーを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTree).where(DriverTree.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTree(
            id=record_id,
            project_id=parse_uuid(row["project_id"]),
            name=row["name"],
            description=row.get("description") or "",
            root_node_id=parse_uuid(row["root_node_id"]) if row.get("root_node_id") else None,
            formula_id=parse_uuid(row["formula_id"]) if row.get("formula_id") else None,
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_relationships(session: AsyncSession) -> int:
    """ドライバーツリーリレーションシップを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree_relationship.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTreeRelationship).where(DriverTreeRelationship.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeRelationship(
            id=record_id,
            driver_tree_id=parse_uuid(row["driver_tree_id"]),
            parent_node_id=parse_uuid(row["parent_node_id"]),
            operator=row.get("operator") or None,
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_relationship_children(session: AsyncSession) -> int:
    """ドライバーツリーリレーションシップ子ノードを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree_relationship_child.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTreeRelationshipChild).where(DriverTreeRelationshipChild.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTreeRelationshipChild(
            id=record_id,
            relationship_id=parse_uuid(row["relationship_id"]),
            child_node_id=parse_uuid(row["child_node_id"]),
            order_index=int(row["order_index"]),
        )
        session.add(record)
        count += 1

    return count


async def load_driver_tree_policies(session: AsyncSession) -> int:
    """ドライバーツリー施策を読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "driver_tree_policy.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(DriverTreePolicy).where(DriverTreePolicy.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = DriverTreePolicy(
            id=record_id,
            node_id=parse_uuid(row["node_id"]),
            label=row["label"],
            value=parse_float(row["value"]) or 0.0,
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_sessions(session: AsyncSession) -> int:
    """分析セッションを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "analysis_session.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisSession).where(AnalysisSession.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisSession(
            id=record_id,
            name=row.get("name", ""),
            issue_id=parse_uuid(row["issue_id"]),
            creator_id=parse_uuid(row["creator_id"]),
            project_id=parse_uuid(row["project_id"]),
            input_file_id=parse_uuid(row["input_file_id"]) if row.get("input_file_id") else None,
            current_snapshot=int(row["current_snapshot"]),
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_files(session: AsyncSession) -> int:
    """分析ファイルを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "analysis_file.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisFile).where(AnalysisFile.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisFile(
            id=record_id,
            session_id=parse_uuid(row["session_id"]),
            project_file_id=parse_uuid(row["project_file_id"]),
            sheet_name=row["sheet_name"],
            axis_config=parse_json(row["axis_config"]),
            data=parse_json(row["data"]),
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_snapshots(session: AsyncSession) -> int:
    """分析スナップショットを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "analysis_snapshot.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisSnapshot).where(AnalysisSnapshot.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisSnapshot(
            id=record_id,
            session_id=parse_uuid(row["session_id"]),
            snapshot_order=int(row["snapshot_order"]),
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_chats(session: AsyncSession) -> int:
    """分析チャットを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "analysis_chat.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisChat).where(AnalysisChat.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisChat(
            id=record_id,
            snapshot_id=parse_uuid(row["snapshot_id"]),
            chat_order=int(row["chat_order"]),
            role=row["role"],
            message=row.get("message") or None,
        )
        session.add(record)
        count += 1

    return count


async def load_analysis_steps(session: AsyncSession) -> int:
    """分析ステップを読み込みます。"""
    rows = read_csv(TRANSACTION_DIR / "analysis_step.csv")
    count = 0

    for row in rows:
        record_id = parse_uuid(row["id"])
        existing = await session.execute(select(AnalysisStep).where(AnalysisStep.id == record_id))
        if existing.scalar_one_or_none():
            continue

        record = AnalysisStep(
            id=record_id,
            snapshot_id=parse_uuid(row["snapshot_id"]),
            config=parse_json(row["config"]),
            name=row["name"],
            step_order=int(row["step_order"]),
            type=row["type"],
            input=row["input"],
        )
        session.add(record)
        count += 1

    return count


async def load_seed_data(session: AsyncSession) -> dict[str, int]:
    """すべてのシードデータを読み込みます。

    Args:
        session: データベースセッション

    Returns:
        dict[str, int]: テーブル名と投入件数のマッピング
    """
    results: dict[str, int] = {}

    # 投入順序（外部キー制約を考慮）
    # "flush" エントリはその時点でflushを実行するマーカー
    loaders: list[tuple[str, Any]] = [
        # マスタ系（依存なし）
        ("user_account", load_user_accounts),
        ("analysis_validation_master", load_analysis_validation_masters),
        ("driver_tree_category", load_driver_tree_categories),
        ("driver_tree_formula", load_driver_tree_formulas),
        # マスタ系（依存あり）
        ("analysis_issue_master", load_analysis_issue_masters),
        ("analysis_graph_axis_master", load_analysis_graph_axis_masters),
        ("analysis_dummy_formula_master", load_analysis_dummy_formula_masters),
        ("analysis_dummy_chart_master", load_analysis_dummy_chart_masters),
        # トラン系（基盤）
        ("project", load_projects),
        ("project_member", load_project_members),
        ("project_file", load_project_files),
        ("driver_tree_node", load_driver_tree_nodes),
        ("driver_tree_file", load_driver_tree_files),
        ("driver_tree_data_frame", load_driver_tree_data_frames),
        # トラン系（セッション）
        ("analysis_session", load_analysis_sessions),
        # NOTE: analysis_fileはanalysis_sessionを外部キー参照するため、先にflushが必要
        ("flush", None),
        ("analysis_file", load_analysis_files),
        ("analysis_snapshot", load_analysis_snapshots),
        ("analysis_chat", load_analysis_chats),
        ("analysis_step", load_analysis_steps),
        # トラン系（ドライバーツリー）
        ("driver_tree", load_driver_trees),
        ("driver_tree_relationship", load_driver_tree_relationships),
        ("driver_tree_relationship_child", load_driver_tree_relationship_children),
        ("driver_tree_policy", load_driver_tree_policies),
    ]

    for table_name, loader in loaders:
        # flushマーカーの場合はflushを実行
        if table_name == "flush":
            await session.flush()
            continue
        try:
            count = await loader(session)
            results[table_name] = count
            if count > 0:
                logger.info(f"シードデータ投入: {table_name} ({count}件)")
        except Exception as e:
            logger.error(f"シードデータ投入エラー: {table_name}", error=str(e))
            raise

    # コミット
    await session.commit()

    total = sum(results.values())
    logger.info(f"シードデータ投入完了: 合計 {total} 件")

    return results
