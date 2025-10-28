# 前提条件

camp_backendの開発を始める前に、必要な環境を確認します。

## 開発環境構成

このプロジェクトは**Windows環境**で直接開発します：

- Python 3.13
- PostgreSQL（ローカルインストール）
- Visual Studio Code
- uv（高速パッケージマネージャー）

この構成により：

- ✅ **シンプル**: 追加の仮想化レイヤーなし
- ✅ **直接実行**: Windows上でネイティブに動作
- ✅ **高速**: オーバーヘッドなし

## 必須要件

### Windows 10/11

- **Windows 10**: バージョン 2004以降推奨
- **Windows 11**: すべてのバージョン
- **管理者権限**: PostgreSQLのインストールに必要な場合あり

### Python 3.13

プログラミング言語。公式サイトからダウンロードしてインストールします。

**公式サイト**: <https://www.python.org/downloads/>

### PostgreSQL

データベースサーバー。ScoopまたはWindows公式インストーラーでインストールします。

**公式サイト**: <https://www.postgresql.org/download/windows/>

### Visual Studio Code

コードエディタ。

**公式サイト**: <https://code.visualstudio.com/>

**推奨拡張機能**:

- **Python** - Python開発サポート
- **Pylance** - 型チェック、コード解析
- **Ruff** - Linter/Formatter
- **SQLTools** - データベース管理

### uv

高速パッケージマネージャー。セットアップ時にインストールします。

**公式サイト**: <https://docs.astral.sh/uv/>

## 確認事項

開発を始める前に、以下を確認してください：

- [ ] Windows 10（2004以降）またはWindows 11を使用している
- [ ] 管理者権限でコマンドを実行できる（PostgreSQLインストール時）
- [ ] インターネット接続がある（パッケージダウンロード用）

## 次のステップ

以下の順序でセットアップを進めてください：

1. **[Windows環境セットアップ](./02-windows-setup.md)** - PostgreSQL、Python、uvのインストール
2. **[VSCodeセットアップ](./03-vscode-setup.md)** - エディタの設定
3. **[環境設定](./04-environment-config.md)** - 環境変数の設定
4. **[クイックスタート](./05-quick-start.md)** - アプリケーションの起動確認

**所要時間**: 合計約15-20分
