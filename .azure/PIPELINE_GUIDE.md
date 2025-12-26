# Azure DevOps パイプライン構成ガイド

## 概要

このプロジェクトのCI/CDパイプラインは、**コードのプッシュから本番環境へのデプロイまでを自動化**します。
Webアプリ開発の経験がある方向けに、従来の手動デプロイフローと対比しながら説明します。

### 従来の手動デプロイフロー vs パイプライン
| 手動デプロイ                      | パイプラインの自動化                               |
| --------------------------------- | -------------------------------------------------- |
| 1. ローカルでコードを修正         | 1. Gitにpush                                       |
| 2. テストを手動実行               | 2. 自動でテスト実行（現在はコメントアウト）        |
| 3. Dockerイメージをビルド         | 3. 自動でDockerイメージビルド                      |
| 4. レジストリにプッシュ           | 4. 自動でACR（Azure Container Registry）にプッシュ |
| 5. サーバーにデプロイコマンド実行 | 5. 自動でContainer Appにデプロイ                   |

---

## ディレクトリ構成

```
.azure/
├── pipelines/
│   ├── variables/
│   │   ├── dev.yml          # 開発環境の変数（ACR名、リソース名など）
│   │   └── prod.yml         # 本番環境の変数
│   └── templates/
│       ├── build-template.yml   # ビルド処理のテンプレート
│       └── deploy-template.yml  # デプロイ処理のテンプレート
│
azure-pipelines.yml          # メインのパイプライン定義（全体の流れ）
```

---

## パイプラインの全体フロー

### 1. トリガー（いつ動くか）
```yaml
trigger:
  branches:
    include:
      - main
      - development
  paths:
    include:
      - src/*
      - tests/*
      - pyproject.toml
```

**意味**: 上記ブランチに`src/`、`tests/`、`pyproject.toml`が変更されたコードがプッシュされると自動実行

---

### 2. ステージ構成（3段階）

パイプラインは3つのステージで構成されています：

```
┌─────────────────┐
│  1. Build       │  ← 常に実行（どのブランチでも）
│  ビルド＆プッシュ  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. DeployToDev │  ← development ブランチのみ
│  開発環境デプロイ  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. DeployToProd│  ← main ブランチのみ
│  本番環境デプロイ  │
└─────────────────┘
```

---

## 各ステージの詳細

### ステージ1: Build（ビルド）

**ファイル**: `.azure/pipelines/templates/build-template.yml`

#### 何をするか
1. Python 3.13の環境をセットアップ
2. 依存関係をインストール（uvを使用）
3. Dockerイメージをビルド
4. Dev ACRにプッシュ

#### 実行内容
```bash
# 1. uvインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# Python環境構築
uv python install

# 3. 依存関係インストール
uv sync --frozen

# 4. 静的チェック（Ruff）
uv run ruff check src tests
uv run ruff format --check src tests


# 4. Dockerイメージビルド＆プッシュ
IMAGE_NAME="${{ parameters.AcrName }}.azurecr.io/${{ parameters.ImageRepo }}:$(Build.BuildId)"

az acr build \
  --registry "${{ parameters.AcrName }}" \
  --image "${{ parameters.ImageRepo }}:$(Build.BuildId)" \
  .
```

**イメージタグ**: `$(Build.BuildId)` = Azure DevOpsが自動的に振るビルド番号（例: 123, 124...）

#### 現在コメントアウトされている機能
- テスト実行（pytest）

→ 必要に応じて42-44行目のコメントを外せば有効化できます

---

### ステージ2: DeployToDev（開発環境デプロイ）

**実行条件**: `development`ブランチへのpush時のみ

**ファイル**: `.azure/pipelines/templates/deploy-template.yml`

#### 使用される変数（`.azure/pipelines/variables/dev.yml`）
```yaml
AcrName: "campdevjpeplatacr"
ResourceGroupName: "camp-dev-jpe-app-rg"
ContainerAppName: "camp-dev-jpe-back-aca"
```
※その他環境変数をAzure DevOps Pipeline Libraryに別途設定する必要があります

#### デプロイコマンド
```bash
az containerapp update \
  --name "$(ContainerAppName)" \
  --resource-group "$(ResourceGroupName)" \
  --image "$IMAGE" \
  --set-env-vars \
      ENVIRONMENT=${ENVIRONMENT} \
      DATABASE_URL=$(DATABASE_URL) \
      REDIS_URL=$(REDIS_URL) \
      AZURE_TENANT_ID=${AZURE_TENANT_ID} \
      AZURE_CLIENT_ID=${AZURE_CLIENT_ID} \
      USE_MANAGED_IDENTITY=${USE_MANAGED_IDENTITY}
```

**Webアプリでの類似作業**: 開発サーバーに`git pull`して`docker-compose up -d --build`するのと同等

---

### ステージ3: DeployToProduction（本番環境デプロイ）

**実行条件**: `main`ブランチへのpush時のみ + DeployToDevが成功していること

#### 特徴: イメージのインポート
本番環境では、開発環境で既にテストされたイメージを使うため、**Dev ACRからProd ACRへイメージをコピー**します。

```bash
# Dev ACRから本番ACRへイメージをインポート
az acr import \
  --name campdevjpeplatacr \  # 本番ACR（※現在はdev ACRと同じ名前になっている）
  --source campdevjpeplatacr.azurecr.io/quickstart:<BuildId> \
  --image quickstart:<BuildId>
```

**注意**: 現在、`prod.yml`と`dev.yml`のACR名が同じになっています。
本番環境用に別のACRを使う場合は、`prod.yml`の`AcrName`を変更してください。

その後、開発環境と同じ`deploy-template.yml`を使ってデプロイします。

---

## 環境変数とシークレット管理

### 公開情報（Gitにコミット可能）
- ACR名
- リソースグループ名
- Container App名
- CPUとメモリの設定

→ `.azure/pipelines/variables/*.yml`に記述

### シークレット情報（Gitにコミット不可）
- データベース接続文字列（`DATABASE_URL`）
- APIキー

→ Azure DevOpsの **ライブラリ（Variable Groups）** または **Key Vault** で管理
→ `$(DevDatabaseUrl)`のように参照

**設定場所**: Azure DevOps → Pipelines → Library

---

## よくある操作

### 新しい環境変数を追加したい
1. `.azure/pipelines/variables/dev.yml` or `prod.yml`に追加 or Azure DevOps Pipeline Libraryに追加
2. `deploy-template.yml`の`--set-env-vars`に追記

例：
```yaml
# dev.yml
AppVersion: "v1.2.0"
```

```bash
# deploy-template.yml
--set-env-vars \
  ENVIRONMENT=${{ parameters.environmentName }} \
  ...
  APP_VERSION=$(AppVersion)
```

### テストを有効化したい
`build-template.yml`の42-44行目のコメントを外す

### 本番デプロイのCPU/メモリを増やしたい
`deploy-template.yml`の19-29行目を変更
```yaml
--cpu 1.0 \      # 0.5 → 1.0
--memory 2Gi \   # 1Gi → 2Gi
```
※Terraformでも管理している箇所のため、Terraform側の編集も可

### 別のブランチでもデプロイしたい
`azure-pipelines.yml`の36行目の条件を変更
```yaml
condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/your-branch'))
```

---

## トラブルシューティング

### パイプラインが実行されない
- トリガーのブランチとパスを確認
- Azure DevOpsのPipelines画面で手動実行を試す

### ビルドは成功するがデプロイされない
- ブランチ名を確認（`development`または`main`か？）
- Azure DevOpsの環境承認設定を確認（環境に承認が必要な場合がある）

### 環境変数が反映されない
- Azure DevOpsのライブラリで変数が定義されているか確認
- `$(変数名)`の記述が正しいか確認

### イメージがプッシュできない
- Service Connection（`PJ925-Azure-ServiceConnection`）の権限を確認
- ACRへのアクセス権があるか確認

---

## まとめ

| ブランチ                       | ビルド | 開発デプロイ | 本番デプロイ                |
| ------------------------------ | ------ | ------------ | --------------------------- |
| `feature/ado-pipeline-backend` | ✓      | ✓            | ×                           |
| `main`                         | ✓      | ×            | ✓（開発が成功した場合のみ） |
| その他                         | ✓      | ×            | ×                           |

このパイプラインにより、コードをプッシュするだけで自動的にビルド・デプロイが実行されます。
