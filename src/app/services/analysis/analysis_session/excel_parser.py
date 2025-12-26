"""Excel解析ユーティリティ。

階層ヘッダー形式のExcelファイルを解析し、正規化されたデータに変換します。

期待される入力形式:
    - ヘッダー部分（複数行の軸定義）
    - 空白行（セパレータ）
    - データ部分（科目と値）
"""

import pandas as pd

from app.services.storage.excel import find_separator_row, split_by_separator


def parse_hierarchical_excel(
    raw_df: pd.DataFrame,
) -> tuple[list[tuple[str, set[str]]], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """階層ヘッダー形式のExcelデータをパースして正規化する。

    Args:
        raw_df: ヘッダーなしで読み込んだExcelのDataFrame

    Returns:
        tuple containing:
            - axis_info: [(軸名, {値のセット}), ...] 軸の順序付きリスト（最後は科目軸）
            - values_df: 正規化されたDataFrame（軸名が列名、'値'列に数値）
            - header_section: ヘッダー部分のDataFrame
            - data_section: データ部分のDataFrame

    Raises:
        ValidationError: 空白行セパレータが見つからない場合
        ValueError: 重複データがある場合
    """
    separator_index = find_separator_row(raw_df)
    header_section, data_section = split_by_separator(raw_df, separator_index)

    column_header_mappings = _extract_column_header_mappings(header_section, data_section)
    axis_info, axis_order = _build_axis_info(column_header_mappings)

    item_names = _extract_item_names(data_section)
    axis_info.append(("科目", item_names))

    records = _build_records(data_section, column_header_mappings, axis_order)

    column_order = axis_order + ["科目", "値"]
    records_df = pd.DataFrame(records)
    values_df: pd.DataFrame = records_df[column_order]  # type: ignore[assignment]

    return axis_info, values_df, header_section, data_section


def _extract_column_header_mappings(header_section: pd.DataFrame, data_section: pd.DataFrame) -> list[list[tuple[str, str]]]:
    """各データ列に対応するヘッダー情報（軸名と値のペア）を抽出する。

    Args:
        header_section: ヘッダー部分のDataFrame
        data_section: データ部分のDataFrame（列数の決定に使用）

    Returns:
        各列のヘッダー情報リスト。例: [[("年度", "2023"), ("部門", "営業")], ...]
    """
    max_data_cols = len(data_section.columns) - 1  # 最初の列は科目名
    column_mappings: list[list[tuple[str, str]]] = []

    for col_idx in range(1, max_data_cols + 1):
        axis_values_for_column: list[tuple[str, str]] = []

        for _, row in header_section.iterrows():
            axis_name = row.iloc[0]
            if pd.notna(axis_name) and col_idx < len(row):
                axis_value = row.iloc[col_idx]
                if pd.notna(axis_value):
                    axis_values_for_column.append((str(axis_name), str(axis_value)))

        column_mappings.append(axis_values_for_column)

    return column_mappings


def _build_axis_info(column_mappings: list[list[tuple[str, str]]]) -> tuple[list[tuple[str, set[str]]], list[str]]:
    """軸情報を構築する（順序を保持）。

    Args:
        column_mappings: 各列のヘッダー情報

    Returns:
        (axis_info, axis_order) のタプル
            - axis_info: [(軸名, {値のセット}), ...]
            - axis_order: 軸名の順序リスト
    """
    axis_value_sets: dict[str, set[str]] = {}
    axis_order: list[str] = []

    for mappings in column_mappings:
        for axis_name, axis_value in mappings:
            if axis_name not in axis_value_sets:
                axis_value_sets[axis_name] = set()
                axis_order.append(axis_name)
            axis_value_sets[axis_name].add(axis_value)

    axis_info = [(name, axis_value_sets[name]) for name in axis_order]
    return axis_info, axis_order


def _extract_item_names(data_section: pd.DataFrame) -> set[str]:
    """データ部分から科目名（行ラベル）を抽出する。

    Args:
        data_section: データ部分のDataFrame

    Returns:
        科目名のセット
    """
    item_names: set[str] = set()

    for _, row in data_section.iterrows():
        item_name = row.iloc[0]
        if pd.notna(item_name):
            item_names.add(str(item_name))

    return item_names


def _build_records(
    data_section: pd.DataFrame,
    column_mappings: list[list[tuple[str, str]]],
    axis_order: list[str],
) -> list[dict[str, str | float | None]]:
    """正規化されたレコードを構築する。

    Args:
        data_section: データ部分のDataFrame
        column_mappings: 各列のヘッダー情報
        axis_order: 軸名の順序リスト

    Returns:
        正規化されたレコードのリスト

    Raises:
        ValueError: 重複するデータ組み合わせがある場合
    """
    unique_combinations: set[tuple] = set()
    records: list[dict[str, str | float | None]] = []

    for _, row in data_section.iterrows():
        item_name = row.iloc[0]
        if pd.isna(item_name):
            continue

        item_name_str = str(item_name)

        for col_idx in range(1, len(row)):
            mapping_idx = col_idx - 1
            if mapping_idx >= len(column_mappings):
                continue

            cell_value = row.iloc[col_idx]
            if pd.isna(cell_value):
                continue

            record = _create_record(
                column_mappings[mapping_idx],
                axis_order,
                item_name_str,
                cell_value,
            )

            unique_key = _create_unique_key(record, axis_order, item_name_str)
            _validate_uniqueness(unique_key, unique_combinations, axis_order, item_name_str)

            unique_combinations.add(unique_key)
            records.append(record)

    return records


def _create_record(
    column_mapping: list[tuple[str, str]],
    axis_order: list[str],
    item_name: str,
    cell_value: float,
) -> dict[str, str | float | None]:
    """1つのセルから正規化レコードを作成する。

    Args:
        column_mapping: この列のヘッダー情報
        axis_order: 軸名の順序リスト
        item_name: 科目名
        cell_value: セルの値

    Returns:
        正規化されたレコード辞書
    """
    record: dict[str, str | float | None] = dict.fromkeys(axis_order)

    for axis_name, axis_value in column_mapping:
        record[axis_name] = axis_value

    record["科目"] = item_name
    record["値"] = cell_value

    return record


def _create_unique_key(
    record: dict[str, str | float | None],
    axis_order: list[str],
    item_name: str,
) -> tuple:
    """レコードの一意性チェック用キーを作成する。

    Args:
        record: レコード辞書
        axis_order: 軸名の順序リスト
        item_name: 科目名

    Returns:
        一意性チェック用のタプル
    """
    key_elements = [record.get(name) for name in axis_order]
    key_elements.append(item_name)
    return tuple(key_elements)


def _validate_uniqueness(
    unique_key: tuple,
    existing_keys: set[tuple],
    axis_order: list[str],
    item_name: str,
) -> None:
    """データの一意性を検証する。

    Args:
        unique_key: チェック対象のキー
        existing_keys: 既存のキーセット
        axis_order: 軸名の順序リスト
        item_name: 科目名

    Raises:
        ValueError: 重複がある場合
    """
    if unique_key not in existing_keys:
        return

    key_description = []
    for idx, axis_name in enumerate(axis_order):
        if unique_key[idx] is not None:
            key_description.append(f"{axis_name}={unique_key[idx]}")
    key_description.append(f"item={item_name}")

    raise ValueError(f"重複した組み合わせが見つかりました: {', '.join(key_description)}")
