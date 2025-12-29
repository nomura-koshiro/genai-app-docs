# Backend Skills ドキュメント

このディレクトリには、バックエンド開発に関する詳細なガイドラインが含まれています。
各スキル実行時に自動的に参照されます。

## ドキュメント一覧

| ファイル | 内容 |
|---------|------|
| [project-overview.md](project-overview.md) | プロジェクト概要・技術スタック |
| [architecture.md](architecture.md) | レイヤードアーキテクチャ |
| [coding-standards.md](coding-standards.md) | コーディング規約・命名規則 |
| [api-design.md](api-design.md) | API設計ガイドライン |
| [testing.md](testing.md) | テスト方針・ベストプラクティス |

## 参照ドキュメント

詳細なドキュメントは `docs/` ディレクトリを参照：

### 開発ガイド

- [クイックスタート](docs/developer-guide/01-getting-started/05-quick-start.md)
- [プロジェクト構造](docs/developer-guide/02-architecture/01-project-structure.md)
- [レイヤードアーキテクチャ](docs/developer-guide/02-architecture/02-layered-architecture.md)
- [コーディング規約](docs/developer-guide/04-development/01-coding-standards/)
- [レイヤー別実装](docs/developer-guide/04-development/02-layer-implementation/)
- [API設計](docs/developer-guide/04-development/05-api-design/)
- [テスト](docs/developer-guide/05-testing/)

### 設計仕様書

- [システムアーキテクチャ](docs/specifications/04-architecture/01-system-architecture.md)
- [データベース設計](docs/specifications/05-database/01-database-design.md)
- [セキュリティ](docs/specifications/06-security/)
- [API仕様](docs/specifications/07-api/01-api-specifications.md)

### APIリファレンス

- [OpenAPI仕様](docs/api/openapi.json)
- [Swagger UI](docs/api/api-docs.html)
- [ReDoc](docs/api/redoc.html)

## 使用方法

スキルから参照する場合：

```markdown
詳細は `.claude/skills/backend/api-design.md` を参照
```

ドキュメントを参照する場合：

```markdown
詳細は `docs/developer-guide/04-development/05-api-design/` を参照
```
