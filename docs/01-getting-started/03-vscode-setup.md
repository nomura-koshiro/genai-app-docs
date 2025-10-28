# VSCodeセットアップ（Windows）

Windows上でVisual Studio Codeを使用して開発します。

## 前提条件

- [WSL2 + Docker CEがインストール済み](./02-wsl2-docker-setup.md)

## Visual Studio Codeのインストール

### 1. VS Codeをダウンロード

公式サイトからインストーラーをダウンロードします:

**公式サイト**: <https://code.visualstudio.com/>

### 2. インストール

ダウンロードしたインストーラーを実行し、指示に従ってインストールします。

## プロジェクトを開く

### 1. VS Codeを起動

Windows上でVisual Studio Codeを起動します。

### 2. プロジェクトフォルダを開く

- `Ctrl+K Ctrl+O` でフォルダを開く
- または、「File」→「Open Folder」
- プロジェクトディレクトリ（例：`C:\developments\backend`）を選択

## 推奨VSCode拡張機能

プロジェクトには推奨拡張機能が定義されています（`.vscode/extensions.json`）。

### 自動インストール

VS Codeがプロジェクトを開いたときに、右下に通知が表示されます:

```text
このワークスペースには拡張機能の推奨事項があります。
[すべてインストール] [推奨事項を表示] [無視]
```

**[すべてインストール]** をクリックすると、推奨拡張機能が一括インストールされます。

### 手動インストール

通知が表示されなかった場合:

1. 拡張機能ビュー（`Ctrl+Shift+X`）を開く
2. 検索バーに `@recommended` と入力
3. 「ワークスペースの推奨事項」セクションに表示される拡張機能をインストール

### 主な拡張機能

- **Python** - Python開発サポート
- **Pylance** - 型チェック、コード解析
- **Ruff** - 高速なLinter/Formatter
- **SQLTools** - データベース管理
- **GitLens** - Git履歴とblame機能
- **Markdown All in One** - ドキュメント作成支援

## 次のステップ

VSCodeのセットアップが完了したら、次は以下に進んでください：

- [環境設定](./04-environment-config.md) - 環境変数の設定
- [クイックスタート](./05-quick-start.md) - アプリケーションの起動
