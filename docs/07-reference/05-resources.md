# リソース・外部リンク

バックエンド開発に役立つ外部リソース、公式ドキュメント、学習リソースを記載します。

## 目次

- [公式ドキュメント](#公式ドキュメント)
- [フレームワーク](#フレームワーク)
- [データベース](#データベース)
- [LLM・AI](#llmai)
- [クラウドサービス](#クラウドサービス)
- [開発ツール](#開発ツール)
- [学習リソース](#学習リソース)
- [コミュニティ](#コミュニティ)

---

## 公式ドキュメント

### FastAPI

高性能な非同期Webフレームワーク。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://fastapi.tiangolo.com/ | メインドキュメント |
| チュートリアル | https://fastapi.tiangolo.com/tutorial/ | ステップバイステップガイド |
| 高度なトピック | https://fastapi.tiangolo.com/advanced/ | 上級機能解説 |
| GitHubリポジトリ | https://github.com/tiangolo/fastapi | ソースコード |

**重要なセクション**

- [依存性注入](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [セキュリティ](https://fastapi.tiangolo.com/tutorial/security/)
- [非同期SQL](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
- [ミドルウェア](https://fastapi.tiangolo.com/tutorial/middleware/)

---

### Pydantic

データバリデーションとスキーマ定義。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://docs.pydantic.dev/ | メインドキュメント |
| バリデーション | https://docs.pydantic.dev/latest/concepts/validators/ | カスタムバリデーション |
| Settings管理 | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ | 環境変数管理 |
| GitHubリポジトリ | https://github.com/pydantic/pydantic | ソースコード |

**重要なセクション**

- [モデル定義](https://docs.pydantic.dev/latest/concepts/models/)
- [フィールドタイプ](https://docs.pydantic.dev/latest/concepts/fields/)
- [バリデーションエラー](https://docs.pydantic.dev/latest/concepts/errors/)

---

## フレームワーク

### SQLAlchemy

Python ORM（非同期対応）。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://docs.sqlalchemy.org/en/20/ | SQLAlchemy 2.0ドキュメント |
| ORMクイックスタート | https://docs.sqlalchemy.org/en/20/orm/quickstart.html | ORM入門 |
| 非同期I/O | https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html | 非同期サポート |
| GitHubリポジトリ | https://github.com/sqlalchemy/sqlalchemy | ソースコード |

**重要なセクション**

- [宣言的マッピング](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html)
- [リレーションシップ](https://docs.sqlalchemy.org/en/20/orm/relationships.html)
- [クエリAPI](https://docs.sqlalchemy.org/en/20/orm/queryguide/)

---

### Alembic

データベースマイグレーションツール。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://alembic.sqlalchemy.org/ | メインドキュメント |
| チュートリアル | https://alembic.sqlalchemy.org/en/latest/tutorial.html | 入門ガイド |
| 自動生成 | https://alembic.sqlalchemy.org/en/latest/autogenerate.html | マイグレーション自動生成 |
| GitHubリポジトリ | https://github.com/sqlalchemy/alembic | ソースコード |

---

### LangChain & LangGraph

LLMアプリケーション開発フレームワーク。

| リソース | URL | 説明 |
|---------|-----|------|
| LangChain公式 | https://python.langchain.com/ | LangChainドキュメント |
| LangGraph公式 | https://langchain-ai.github.io/langgraph/ | LangGraphドキュメント |
| コンセプトガイド | https://python.langchain.com/docs/concepts/ | 基本概念 |
| GitHubリポジトリ | https://github.com/langchain-ai/langchain | ソースコード |

**重要なセクション**

- [Chains](https://python.langchain.com/docs/modules/chains/)
- [Agents](https://python.langchain.com/docs/modules/agents/)
- [Memory](https://python.langchain.com/docs/modules/memory/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)

---

## データベース

### PostgreSQL

本番環境推奨のRDBMS。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://www.postgresql.org/docs/ | メインドキュメント |
| チュートリアル | https://www.postgresql.org/docs/current/tutorial.html | PostgreSQL入門 |
| パフォーマンス最適化 | https://www.postgresql.org/docs/current/performance-tips.html | パフォーマンスチューニング |
| ダウンロード | https://www.postgresql.org/download/ | インストーラ |

**日本語リソース**

- [PostgreSQL日本語ドキュメント](https://www.postgresql.jp/document/)

---

### SQLite

開発環境用の軽量DB。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式サイト | https://www.sqlite.org/ | メインサイト |
| ドキュメント | https://www.sqlite.org/docs.html | 公式ドキュメント |
| SQLリファレンス | https://www.sqlite.org/lang.html | SQL構文リファレンス |

---

## LLM・AI

### Anthropic Claude

高性能なLLM（Large Language Model）。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式サイト | https://www.anthropic.com/ | Anthropic公式 |
| API ドキュメント | https://docs.anthropic.com/ | Claude APIドキュメント |
| Console | https://console.anthropic.com/ | APIキー管理 |
| Python SDK | https://github.com/anthropics/anthropic-sdk-python | Python SDK |

**重要なセクション**

- [クイックスタート](https://docs.anthropic.com/claude/docs/quickstart-guide)
- [プロンプトエンジニアリング](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [ビジョン機能](https://docs.anthropic.com/claude/docs/vision)

---

### OpenAI

ChatGPTとGPTモデルの提供元。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式サイト | https://openai.com/ | OpenAI公式 |
| API ドキュメント | https://platform.openai.com/docs/ | APIドキュメント |
| Playground | https://platform.openai.com/playground | API実験環境 |
| Python SDK | https://github.com/openai/openai-python | Python SDK |

**重要なセクション**

- [Chat Completions](https://platform.openai.com/docs/guides/chat-completions)
- [Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

### Azure OpenAI Service

Azureで提供されるOpenAI API。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://learn.microsoft.com/azure/cognitive-services/openai/ | Azure OpenAI ドキュメント |
| クイックスタート | https://learn.microsoft.com/azure/cognitive-services/openai/quickstart | 入門ガイド |
| Pricing | https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/ | 料金 |

---

### LangSmith

LLMアプリケーションのトレーシングとデバッグ。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式サイト | https://www.langchain.com/langsmith | LangSmith公式 |
| ドキュメント | https://docs.smith.langchain.com/ | ドキュメント |
| Console | https://smith.langchain.com/ | トレーシングダッシュボード |

---

## クラウドサービス

### Microsoft Azure

クラウドプラットフォーム。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://learn.microsoft.com/azure/ | Azureドキュメント |
| Blob Storage | https://learn.microsoft.com/azure/storage/blobs/ | Blob Storageドキュメント |
| Python SDK | https://learn.microsoft.com/azure/developer/python/ | Azure SDK for Python |
| Portal | https://portal.azure.com/ | Azure Portal |

**重要なサービス**

- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python)
- [Azure Database for PostgreSQL](https://learn.microsoft.com/azure/postgresql/)
- [Azure App Service](https://learn.microsoft.com/azure/app-service/)

---

### AWS (Amazon Web Services)

代替クラウドプラットフォーム。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://docs.aws.amazon.com/ | AWSドキュメント |
| S3 | https://docs.aws.amazon.com/s3/ | S3ドキュメント |
| Python SDK (Boto3) | https://boto3.amazonaws.com/v1/documentation/api/latest/index.html | AWS SDK for Python |

---

### Google Cloud Platform (GCP)

代替クラウドプラットフォーム。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://cloud.google.com/docs | GCPドキュメント |
| Cloud Storage | https://cloud.google.com/storage/docs | Cloud Storageドキュメント |
| Python SDK | https://cloud.google.com/python | Google Cloud Client Libraries |

---

## 開発ツール

### Python

プログラミング言語。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式サイト | https://www.python.org/ | Python公式 |
| ドキュメント | https://docs.python.org/3/ | 公式ドキュメント |
| PEP 8 | https://peps.python.org/pep-0008/ | Pythonコーディング規約 |
| PyPI | https://pypi.org/ | Pythonパッケージリポジトリ |

**日本語リソース**

- [Python公式ドキュメント日本語版](https://docs.python.org/ja/3/)

---

### uv

高速なPythonパッケージマネージャー。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://docs.astral.sh/uv/ | uvドキュメント |
| GitHubリポジトリ | https://github.com/astral-sh/uv | ソースコード |

---

### Ruff

高速なPython linter/formatter。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://docs.astral.sh/ruff/ | Ruffドキュメント |
| ルール一覧 | https://docs.astral.sh/ruff/rules/ | リンタールール |
| GitHubリポジトリ | https://github.com/astral-sh/ruff | ソースコード |

---

### Docker

コンテナプラットフォーム。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://docs.docker.com/ | Dockerドキュメント |
| Docker Compose | https://docs.docker.com/compose/ | Composeドキュメント |
| Docker Hub | https://hub.docker.com/ | コンテナレジストリ |

---

### Git

バージョン管理システム。

| リソース | URL | 説明 |
|---------|-----|------|
| 公式ドキュメント | https://git-scm.com/doc | Gitドキュメント |
| Pro Git Book | https://git-scm.com/book/ja/v2 | 無料オンラインブック（日本語） |
| GitHub Docs | https://docs.github.com/ | GitHubドキュメント |

---

## 学習リソース

### チュートリアル

FastAPIとPythonの学習リソース。

| リソース | URL | 説明 |
|---------|-----|------|
| FastAPI公式チュートリアル | https://fastapi.tiangolo.com/tutorial/ | ステップバイステップガイド |
| Real Python | https://realpython.com/ | Python学習サイト |
| Python公式チュートリアル | https://docs.python.org/ja/3/tutorial/ | Python入門 |

---

### ビデオコース

| プラットフォーム | URL | 説明 |
|---------------|-----|------|
| YouTube - FastAPI | https://www.youtube.com/results?search_query=fastapi+tutorial | FastAPIチュートリアル動画 |
| Udemy | https://www.udemy.com/ | オンライン学習プラットフォーム |
| Coursera | https://www.coursera.org/ | 大学レベルのコース |

---

### ブログ・記事

| リソース | URL | 説明 |
|---------|-----|------|
| Real Python Blog | https://realpython.com/ | Python技術記事 |
| TestDriven.io | https://testdriven.io/ | テスト駆動開発記事 |
| Qiita（日本語） | https://qiita.com/ | 技術情報共有サイト |
| Zenn（日本語） | https://zenn.dev/ | エンジニアのための情報共有サイト |

---

### 書籍

推奨書籍（日本語）

| 書籍名 | 説明 |
|-------|------|
| Pythonではじめる機械学習 | 機械学習入門 |
| FastAPI実践入門 | FastAPI詳解 |
| SQLアンチパターン | データベース設計のベストプラクティス |
| リーダブルコード | コードの可読性向上 |

---

## コミュニティ

### フォーラム・Q&A

| リソース | URL | 説明 |
|---------|-----|------|
| Stack Overflow | https://stackoverflow.com/ | プログラミングQ&Aサイト |
| FastAPI Discussions | https://github.com/tiangolo/fastapi/discussions | FastAPI公式ディスカッション |
| Reddit - Python | https://www.reddit.com/r/Python/ | Pythonコミュニティ |
| Reddit - FastAPI | https://www.reddit.com/r/FastAPI/ | FastAPIコミュニティ |

---

### Discord・Slack

| コミュニティ | 説明 |
|------------|------|
| FastAPI Discord | FastAPI公式Discordサーバー |
| Python Discord | Pythonコミュニティ |
| LangChain Discord | LangChainコミュニティ |

---

### 日本語コミュニティ

| リソース | URL | 説明 |
|---------|-----|------|
| Python.jp | https://www.python.jp/ | 日本Pythonユーザ会 |
| PyCon JP | https://www.pycon.jp/ | 日本最大のPythonカンファレンス |
| Qiita | https://qiita.com/ | 技術情報共有サイト |
| Zenn | https://zenn.dev/ | エンジニア向けプラットフォーム |

---

## API参考実装

### FastAPIプロジェクト例

参考になるオープンソースプロジェクト。

| プロジェクト | URL | 説明 |
|------------|-----|------|
| Full Stack FastAPI Template | https://github.com/tiangolo/full-stack-fastapi-template | FastAPI公式フルスタックテンプレート |
| FastAPI Best Practices | https://github.com/zhanymkanov/fastapi-best-practices | ベストプラクティス集 |
| FastAPI Realworld | https://github.com/nsidnev/fastapi-realworld-example-app | RealWorld実装例 |

---

## セキュリティ

### セキュリティガイド

| リソース | URL | 説明 |
|---------|-----|------|
| OWASP Top 10 | https://owasp.org/www-project-top-ten/ | Webアプリケーションセキュリティリスク |
| FastAPI Security | https://fastapi.tiangolo.com/tutorial/security/ | FastAPIセキュリティガイド |
| Python Security | https://python.readthedocs.io/en/stable/library/security_warnings.html | Pythonセキュリティ |

---

## パフォーマンス

### ベンチマーク・最適化

| リソース | URL | 説明 |
|---------|-----|------|
| FastAPI Benchmarks | https://www.techempower.com/benchmarks/ | Webフレームワークベンチマーク |
| Python Performance | https://wiki.python.org/moin/PythonSpeed/PerformanceTips | Pythonパフォーマンスチップス |
| PostgreSQL Performance | https://www.postgresql.org/docs/current/performance-tips.html | PostgreSQL最適化 |

---

## CI/CD

### デプロイメント

| リソース | URL | 説明 |
|---------|-----|------|
| GitHub Actions | https://docs.github.com/actions | CI/CD自動化 |
| Docker Deploy | https://docs.docker.com/get-started/ | Dockerデプロイメント |
| Azure DevOps | https://learn.microsoft.com/azure/devops/ | Azure CI/CD |

---

## モニタリング

### 監視・ログ管理

| リソース | URL | 説明 |
|---------|-----|------|
| Prometheus | https://prometheus.io/ | メトリクス収集 |
| Grafana | https://grafana.com/ | メトリクス可視化 |
| Sentry | https://sentry.io/ | エラートラッキング |
| Azure Monitor | https://learn.microsoft.com/azure/azure-monitor/ | Azureモニタリング |

---

## その他のツール

### 便利なツール

| ツール | URL | 説明 |
|-------|-----|------|
| Postman | https://www.postman.com/ | API開発・テストツール |
| Insomnia | https://insomnia.rest/ | REST/GraphQLクライアント |
| DBeaver | https://dbeaver.io/ | データベースGUIツール |
| pgAdmin | https://www.pgadmin.org/ | PostgreSQL管理ツール |

---

## ライセンス・法務

### オープンソースライセンス

| リソース | URL | 説明 |
|---------|-----|------|
| Choose a License | https://choosealicense.com/ | ライセンス選択ガイド |
| SPDX License List | https://spdx.org/licenses/ | 標準ライセンス一覧 |

---

## まとめ

このリファレンスドキュメントには、バックエンド開発に必要な主要なリソースをまとめました。

### 優先的に確認すべきリソース

1. **FastAPI公式ドキュメント** - フレームワークの基本
2. **SQLAlchemy 2.0ドキュメント** - データベース操作
3. **LangChain公式ドキュメント** - LLMアプリケーション開発
4. **Pydantic公式ドキュメント** - データバリデーション

### 問題解決の流れ

1. **公式ドキュメント**を確認
2. **Stack Overflow**で類似問題を検索
3. **GitHub Issues**で既知の問題を確認
4. **コミュニティ**に質問

---

## 更新履歴

このドキュメントは定期的に更新されます。最新情報は各公式サイトで確認してください。
