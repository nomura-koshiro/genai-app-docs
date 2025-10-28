# WSL2 + Docker CEセットアップ（完全Linux環境）

**推奨構成**: すべての開発をWSL2（Linux）で完結させます。

この構成により：

- ✅ **高速**: ファイルI/Oが高速（Windowsとの往復なし）
- ✅ **シンプル**: Linuxパスのみ、環境が統一
- ✅ **軽量**: Docker Desktopが不要
- ✅ **本番と同じ**: 本番環境（Linux）と完全一致

**VSCodeについて**: Windows側のVSCodeで編集できます（Remote-WSL拡張を使用）。

## 前提条件

- Windows 10 バージョン 2004以降、またはWindows 11
- 管理者権限

## セットアップ手順

### ステップ1: WSL2のインストール（Windows側）

PowerShellを管理者権限で起動：

```powershell
# WSL2をインストール
wsl --install

# コンピューターを再起動
```

再起動後、Ubuntuが自動起動します：

- ユーザー名を入力
- パスワードを設定

### ステップ2: WSL2の設定（Windows側）

`.wslconfig`を作成（`C:\Users\<ユーザー名>\.wslconfig`）：

```ini
[wsl2]
localhostForwarding=true
```

WSL2を再起動：

```powershell
wsl --shutdown
```

### ステップ3: WSL2に入る

```powershell
wsl
```

以降はすべてWSL2内で作業します。

### ステップ4: Dockerのインストール（WSL2内）

```bash
# パッケージ更新
sudo apt update

# Dockerインストール（docker-composeは不要 - Docker CEに組み込まれています）
sudo apt install -y docker.io

# ユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# グループ変更を反映
newgrp docker

# Dockerサービスを起動
sudo service docker start

# 確認
docker ps
```

### ステップ5: プロジェクトのセットアップ（WSL2内）

#### 方法A: 自動セットアップ（推奨）

セットアップスクリプトを使用します：

```bash
# プロジェクトをWSL2にコピー（初回のみ）
# WindowsからWSL2へコピーする場合
bash /mnt/c/developments/genai-app-docs/scripts/setup-wsl2.sh

# 環境を作り直す場合（既存環境を削除してから再構築）
bash /mnt/c/developments/genai-app-docs/scripts/setup-wsl2.sh --clean

# ヘルプを表示
bash /mnt/c/developments/genai-app-docs/scripts/setup-wsl2.sh --help
```

**スクリプトが自動実行する内容**:

1. Docker & Dockerサービス確認
2. プロジェクトをWSL2にコピー（.venv除外で高速化）
3. uvのインストールとPATH設定（永続化）
4. Python依存関係のインストール
5. 環境変数ファイルの作成
6. PostgreSQLの起動

**--cleanオプション**:

- 既存のプロジェクトディレクトリを削除
- Dockerコンテナとボリュームを削除
- PATH設定をクリーンアップ
- クリーンな状態から再構築

環境が壊れた時や依存関係を更新する時に便利です。

#### 方法B: 手動セットアップ

自動セットアップがうまくいかない場合、手動で実行できます：

```bash
# ホームディレクトリに移動
cd ~

# プロジェクトディレクトリを作成
mkdir -p projects
cd projects

# Windowsからコピー（またはgit clone）
rsync -av --exclude='.venv' --exclude='.pytest_cache' \
  --exclude='__pycache__' --exclude='*.pyc' \
  /mnt/c/developments/genai-app-docs ./

# プロジェクトに移動
cd genai-app-docs

# uvのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# PATHを永続化
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 依存関係のインストール
uv sync

# 環境変数ファイルを作成
cp .env.local.example .env.local
```

### ステップ6: 完了確認

```bash
# PostgreSQL起動
cd ~/projects/genai-app-docs
docker compose up -d postgres

# テスト実行
uv run pytest tests/models/test_sample_user.py -v
```

すべてのテストがパスすれば完了です！

---

## VSCodeの設定（Windows側で編集する場合）

### Remote-WSL拡張をインストール

VSCode（Windows側）で以下の拡張をインストール：

- **Remote - WSL** (Microsoft)
  - <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl>

### WSL2からVSCodeを開く

WSL2のターミナルで：

```bash
cd ~/projects/genai-app-docs
code .
```

VSCodeが開き、左下に「**WSL: Ubuntu**」と表示されます。

これで**Windows側のVSCode**で**WSL2のコード**を編集できます！

---

## トラブルシューティング

### Ubuntuが起動しない

**症状:**

```text
Linux 用 Windows サブシステムにインストールされているディストリビューションはありません。
```

**解決方法:**

```powershell
wsl --install -d Ubuntu
```

### 仮想化が有効になっていないエラー

**症状:**

```text
仮想化サポートが無効になっています
```

**解決方法:**

1. BIOSで仮想化（Intel VT-x / AMD-V）を有効化
2. Windows機能「仮想マシンプラットフォーム」を有効化:

   ```powershell
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

### Linuxカーネル更新プログラムエラー

公式サイトから最新のWSL2 Linuxカーネル更新プログラムをダウンロードしてインストール:

- <https://aka.ms/wsl2kernel>

### WSL2が繰り返し再起動する

**症状:**

- WSL2が20〜180秒ごとに自動的に再起動する
- Dockerコンテナが`Exited (255)`ステータスで停止する

**原因:**

- `.wslconfig`で`swap=0`を設定している
- メモリ不足時にWSL2がクラッシュする

**解決方法:**

1. `.wslconfig`の内容を確認：

   ```powershell
   cat C:\Users\<ユーザー名>\.wslconfig
   ```

2. `swap=0`の行を削除するか、ファイルを最小限の設定に変更：

   ```ini
   [wsl2]
   localhostForwarding=true
   ```

3. WSL2を再起動：

   ```powershell
   wsl --shutdown
   ```

### Dockerサービスが起動しない

**症状:**

```bash
sudo service docker status
# Docker is not running
```

**解決方法:**

```bash
sudo service docker start
```

### permission deniedエラー

**症状:**

```text
permission denied while trying to connect to the Docker daemon socket
```

**解決方法:**

ユーザーがdockerグループに追加されていない可能性があります。WSLを再起動：

```bash
exit
```

PowerShellから：

```powershell
wsl --shutdown
wsl -d Ubuntu
```

### Windows側からDockerコンテナに接続できない

**症状:**

- `OSError: [Errno 10061] Connect call failed ('127.0.0.1', 5432)`
- VS CodeからPostgreSQLに接続できない

**解決方法:**

1. `.wslconfig`に`localhostForwarding=true`が設定されているか確認

2. WSL2を再起動（PowerShellから）：

   ```powershell
   wsl --shutdown
   ```

3. Dockerコンテナを再起動（WSL2内）：

   ```bash
   cd ~/projects/genai-app-docs
   docker compose restart
   ```

4. Windows側からポート接続を確認（PowerShellから）：

   ```powershell
   Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
   ```

### WSL2内でDockerサービスが自動起動しない

**解決方法（毎回起動）:**

```bash
sudo service docker start
```

**解決方法（自動起動設定）:**

`~/.bashrc`または`~/.zshrc`に追加：

```bash
# Docker自動起動
if ! service docker status > /dev/null 2>&1; then
    sudo service docker start > /dev/null 2>&1
fi
```

### docker-compose互換性エラー

**症状:**

```text
KeyError: 'ContainerConfig'
```

または

```text
Traceback (most recent call last):
  File "/usr/bin/docker-compose", line 33, in <module>
```

**原因:**

古い`docker-compose`（Python実装、v1.x）とDocker CE 28以降の非互換性問題。

**解決方法:**

Docker組み込みの`docker compose`コマンド（スペース区切り）を使用してください：

```bash
# ❌ 古い方法（使わない）
docker-compose up -d

# ✅ 新しい方法（推奨）
docker compose up -d
```

もし古いdocker-composeをインストールしてしまった場合は削除：

```bash
# 古いdocker-composeを削除
sudo apt remove docker-compose

# Dockerが正しく動作することを確認
docker compose version
```

### コンテナ名の競合

**症状:**

```text
Error response from daemon: Conflict. The container name "/backend-postgres" is already in use
```

**原因:**

以前のコンテナが残っていて、同じ名前のコンテナを作成しようとしている。

**解決方法:**

既存のコンテナを削除してから再起動：

```bash
# 既存のPostgreSQLコンテナを確認
docker ps -a | grep postgres

# コンテナを削除
docker rm -f backend-postgres

# または、すべてのコンテナとボリュームをクリーンアップ
cd ~/projects/genai-app-docs
docker compose down -v

# 再起動
docker compose up -d postgres
```

---

## 次のステップ

WSL2とDocker CEのセットアップが完了したら、次は [VSCodeセットアップ](./03-vscode-setup.md) に進んでください。
