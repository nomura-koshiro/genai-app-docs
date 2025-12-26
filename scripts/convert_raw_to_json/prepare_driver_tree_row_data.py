"""ドライバーツリーカテゴリ・数式データの準備スクリプト。

dt_category.txtとdriver_trees.jsonを読み込み、
seed_loader.pyで使用できるJSON形式に変換します。
"""

import json
from pathlib import Path

# ドライバー型マッピング（ID → 名称）
DRIVER_TYPE_MAPPING = {
    1: "キャパシティ×稼働率型①",
    2: "キャパシティ×稼働率型②",
    3: "キャパシティ×稼働率×回転率型",
    4: "輸送可能量×充填率型",
    5: "人材数×稼働率型①",
    6: "人材数×稼働率型②",
    7: "採取数量×出荷率型",
    8: "生産_製造数量×出荷率型",
    9: "仕入数量×出荷率型",
    10: "店舗数×来客数×CVR×単価型",
    11: "店舗数×来客数×単価型",
    12: "契約数×契約期間型①",
    13: "契約数×契約期間型②",
    14: "契約数×契約単価型①",
    15: "契約数×契約単価型②",
    16: "契約数×契約単価型③",
    17: "利用量×単価型①",
    18: "利用量×単価型②",
    19: "インプレッション数×単価型①",
    20: "インプレッション数×単価型②",
    21: "決済額×手数料割合型①",
    22: "決済額×手数料割合型②",
    23: "運用額×手数料割合型",
    24: "貸出額×利率型",
    99: "売上_原価_販管費の概念が存在しない",
}


def parse_categories(source_dir: Path) -> list[dict]:
    """dt_category.txtを解析してカテゴリデータを生成。"""
    categories = []
    tsv_path = source_dir / "dt_category.txt"

    with open(tsv_path, encoding="utf-8") as f:
        lines = f.readlines()

    # ヘッダーをスキップ
    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.strip().split("\t")
        if len(parts) < 7:
            continue

        category_id = int(parts[0])
        category_name = parts[1]
        industry_id = int(parts[2])
        industry_name = parts[3]

        # 3つの対応式を処理
        for i in range(3):
            driver_type_id_col = 4 + (i * 2)

            if driver_type_id_col >= len(parts):
                break

            driver_type_id_str = parts[driver_type_id_col]

            # "-" または空の場合はスキップ
            if not driver_type_id_str or driver_type_id_str == "-":
                continue

            driver_type_id = int(driver_type_id_str)
            driver_type = DRIVER_TYPE_MAPPING.get(driver_type_id, "不明")

            categories.append(
                {
                    "category_id": category_id,
                    "category_name": category_name,
                    "industry_id": industry_id,
                    "industry_name": industry_name,
                    "driver_type_id": driver_type_id,
                    "driver_type": driver_type,
                }
            )

    return categories


def parse_formulas(source_dir: Path) -> list[dict]:
    """driver_trees.jsonを解析して数式データを生成。"""
    formulas = []
    json_path = source_dir / "driver_trees.json"

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # driver_type → KPI → formulas の構造
    for driver_type, kpi_data in data.items():
        # driver_type_id を逆引き
        driver_type_id = None
        for type_id, type_name in DRIVER_TYPE_MAPPING.items():
            if type_name == driver_type:
                driver_type_id = type_id
                break

        if driver_type_id is None:
            print(f"警告: ドライバー型が見つかりません: {driver_type}")
            continue

        for kpi, formula_list in kpi_data.items():
            # NaN をフィルタリング
            clean_formulas = [f for f in formula_list if f == f]  # NaN は f != f

            if not clean_formulas:
                continue

            formulas.append(
                {
                    "driver_type_id": driver_type_id,
                    "driver_type": driver_type,
                    "kpi": kpi,
                    "formulas": clean_formulas,
                }
            )

    return formulas


def main():
    """メイン処理。"""
    # パス設定（rawフォルダからの相対パス）
    source_dir = Path(__file__).parent  # raw フォルダ
    output_dir = Path(__file__).parent.parent  # driver_tree フォルダ

    print("カテゴリデータを解析中...")
    categories = parse_categories(source_dir)
    print(f"カテゴリデータ: {len(categories)} 件")

    print("数式データを解析中...")
    formulas = parse_formulas(source_dir)
    print(f"数式データ: {len(formulas)} 件")

    # JSON出力（driver_treeフォルダに出力）
    with open(output_dir / "driver_tree_category.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

    with open(output_dir / "driver_tree_formula.json", "w", encoding="utf-8") as f:
        json.dump(formulas, f, ensure_ascii=False, indent=2)

    print("\n出力完了:")
    print(f"  - {output_dir / 'driver_tree_category.json'}")
    print(f"  - {output_dir / 'driver_tree_formula.json'}")


if __name__ == "__main__":
    main()
