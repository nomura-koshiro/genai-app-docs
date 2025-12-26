"""シードデータ管理モジュール。

このモジュールは、開発・テスト環境用の初期データ投入機能を提供します。
"""

from app.seeds.seed_loader import load_seed_data

__all__ = ["load_seed_data"]
