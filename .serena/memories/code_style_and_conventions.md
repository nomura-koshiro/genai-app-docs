# Training Tracker - コードスタイルと規約

## フロントエンド (TypeScript/React)

### ファイル・ディレクトリ命名
- **ファイル名**: kebab-case (`user-profile.tsx`)
- **コンポーネント名**: PascalCase (`UserProfile`)
- **ディレクトリ名**: kebab-case (`user-profile/`)
- **フック名**: camelCase with `use` prefix (`useUserProfile`)

### コード規約
- **インデント**: 2スペース
- **クォート**: ダブルクォート (`"`)
- **セミコロン**: 必須
- **行末改行**: 必須
- **最大行長**: 100文字

### TypeScript
- **厳密モード**: 有効
- **型注釈**: 明示的に記述
- **インターフェース**: PascalCase (`UserProfile`)
- **型エイリアス**: PascalCase (`UserId`)

### React
- **関数コンポーネント**: Arrow function推奨
- **Props**: インターフェース定義必須
- **Export**: Named export + default export
- **forwardRef**: UI コンポーネントで使用

### スタイリング
- **Tailwind CSS**: ユーティリティファースト
- **CVA**: バリアント管理
- **cn()**: クラス名結合ユーティリティ

## バックエンド (Python)

### ファイル・ディレクトリ命名
- **ファイル名**: snake_case (`user_profile.py`)
- **クラス名**: PascalCase (`UserProfile`)
- **関数名**: snake_case (`get_user_profile`)
- **変数名**: snake_case (`user_id`)

### コード規約
- **インデント**: 4スペース
- **行末**: LF
- **最大行長**: 100文字
- **文字列**: ダブルクォート推奨

### Python
- **型ヒント**: 必須 (typing モジュール)
- **Docstring**: Google スタイル
- **非同期**: async/await 使用

### FastAPI
- **ルーター**: 機能別分割
- **依存性注入**: Depends() 使用
- **バリデーション**: Pydantic スキーマ
- **エラーハンドリング**: HTTPException

## 共通規約

### Git
- **コミットメッセージ**: 英語、現在形、動詞始まり
- **ブランチ名**: feature/task-description, fix/bug-description

### ドキュメント
- **README**: 日本語
- **コメント**: 日本語（必要最小限）
- **JSDoc/Docstring**: 英語

### テスト
- **命名**: `describe` + `it` パターン
- **ファイル名**: `*.test.{ts,tsx,py}`
- **カバレッジ**: 80%以上目標