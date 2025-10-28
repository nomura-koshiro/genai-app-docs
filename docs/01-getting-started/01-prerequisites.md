# 前提条件

camp-backendの開発を始める前に、必要な環境を確認します。

## 開発環境構成

このプロジェクトは**WSL2完結型環境**で開発します：

- **Windows側**: WSL2、Visual Studio Code（Remote-WSL拡張）のみ
- **WSL2側**: すべての開発ツール（Python、uv、Git、Docker CE、ソースコード）

この構成により：

- ✅ **高速**: ファイルI/Oが高速（Windowsとの往復なし）
- ✅ **シンプル**: 環境が統一され、パスの問題なし
- ✅ **軽量**: Docker Desktopが不要
- ✅ **本番と同じ**: 本番環境（Linux）と完全一致

## 必須要件

### Windows 10/11

- **Windows 10**: バージョン 2004以降
- **Windows 11**: すべてのバージョン
- **管理者権限**: WSL2のインストールに必要

### Visual Studio Code（Windows側）

コードエディタ。Remote-WSL拡張を使用してWSL2内のコードを編集します。

**公式サイト**: <https://code.visualstudio.com/>

**必須拡張機能**:

- **Remote - WSL** - WSL2内のコードを編集
- **Python** - Python開発サポート
- **Ruff** - Linter/Formatter

## WSL2側のツール（自動インストール）

以下はすべて**セットアップスクリプトで自動インストール**されます：

- **Python 3.13** - プログラミング言語
- **uv** - 高速パッケージマネージャー
- **Git** - バージョン管理（通常プリインストール済み）
- **Docker CE** - コンテナ実行環境
- **PostgreSQL** - データベース（Dockerコンテナ）

手動でインストールする必要はありません。

## 確認事項

開発を始める前に、以下を確認してください：

- [ ] Windows 10（2004以降）またはWindows 11を使用している
- [ ] 管理者権限でコマンドを実行できる
- [ ] Visual Studio Codeをインストール済み（またはこれからインストール）

## 次のステップ

以下の順序でセットアップを進めてください：

1. **[WSL2 + Docker CEセットアップ](./02-wsl2-docker-setup.md)** - WSL2とDockerの自動セットアップ
2. **[VSCodeセットアップ](./03-vscode-setup.md)** - エディタの設定
3. **[クイックスタート](./05-quick-start.md)** - アプリケーションの起動確認

**所要時間**: 合計約10-15分
