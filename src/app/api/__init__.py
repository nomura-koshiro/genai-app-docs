"""FastAPI層の実装。

このパッケージは、FastAPIを使用したWeb API層を提供します。

パッケージ構成:
    - routes: APIエンドポイント定義
        - system: システムエンドポイント（ヘルスチェック等）
        - v1: API v1 ビジネスロジックエンドポイント
    - core: API層のコア機能
        - dependencies: 依存性注入
        - exception_handlers: グローバル例外ハンドラー
    - middlewares: カスタムミドルウェア
        - error_handler: エラーハンドリング
        - logging: リクエストロギング
        - metrics: Prometheusメトリクス
        - rate_limit: レート制限
        - security_headers: セキュリティヘッダー
    - decorators: 横断的関心事のデコレータ
        - basic: ログ記録、パフォーマンス測定
        - security: 権限検証、エラーハンドリング
        - data_access: トランザクション、キャッシュ
        - reliability: リトライロジック

アーキテクチャ:
    FastAPIのルーター、依存性注入、ミドルウェアを活用し、
    クリーンで保守性の高いAPI層を構築します。

Note:
    メインアプリケーションはapp.main.pyで定義されています。
"""
