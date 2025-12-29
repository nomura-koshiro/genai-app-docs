# Azure パイプラインドキュメント

## Overview / 概要

このパイプラインは、CAMPバックエンドアプリケーションのビルド、テスト、デプロイメントプロセスを自動化するために設計されています。複数の環境に対応したステージを含み、特定のブランチとパス条件に基づいてトリガーされます。

## トリガー条件

### ブランチ

- main
- development

### パス

- src/*
- tests/*
- pyproject.toml

## パイプライン変数

- `projectRoot`: System.DefaultWorkingDirectory (repository root)
- `imageRepository`: "quickstart" (ACR repository name)
- `azureSubscription`: "PJ925-Azure-ServiceConnection"
- `imageTag`: uses `$(Build.BuildId)` (ビルドごとに生成)
  - Note: `imageRepository` と `AcrName`は`.azure/pipelines/variables`配下の変数ファイルにて定義

## パイプラインステージ

### 1. ビルドステージ

**表示名**: "Build, Test and Push Image"
**目的**: 静的チェック、テスト、ACRへのビルド/プッシュ
**テンプレート**: .azure/pipelines/templates/build-template.yml

**`build-template.yml` の詳細:**

- エージェント: `ubuntu-latest`（Linuxビルドホスト）
- テンプレートパラメータ: `azureSubscription`
- `imageTag` は `$(Build.BuildId)` を使用
- `.python-version` で指定したPythonバージョンを設定
- Cache@2 を利用して仮想環境とpipキャッシュを保存し、CIを高速化
- プロジェクトの `uv` ヘルパーで仮想環境を作成し依存関係をインストール（`[dev]` extras が無ければフォールバック）
- `pytest` でテスト
- `AzureCLI@2` による ACR ログイン（`AcrName` 変数を使用）
- Azure CLI によるイメージビルドとプッシュを実行し、ターゲットは `$AcrName.azurecr.io/$(imageRepository):$(imageTag)`

### 2. 開発環境デプロイステージ

**表示名**: "Deploy to Development"
**条件**: development ブランチでのみ実行
**環境**: dev
**テンプレート**: .azure/pipelines/templates/deploy-template.yml
**変数**: .azure/pipelines/variables/dev.yml、Azure DevOps Piepline Library(Back-dev)

### 3. 本番環境デプロイステージ

**表示名**: "Deploy to Production"
**条件**: main ブランチでのみ実行し、開発環境デプロイ成功後に実行
**環境**: prod
**テンプレート**: .azure/pipelines/templates/deploy-template.yml
**変数**: .azure/pipelines/variables/prod.yml、Azure DevOps Piepline Library(Back-prod)

## Pipeline Flow / パイプラインフロー

::: mermaid
graph TD
    A[Code Push] --> |ビルドステージ開始| B[静的チェック＋テスト]
    B -->|テストをパス| C[ビルド]
    C --> |ビルド完了| D[開発環境のACRにPush]
    D --> E{Branch 確認}
    E -->|development or main| F[開発環境にデプロイ]
    F --> G{Branch 確認}
    G -->|main| H[本番環境にデプロイ]
    F -->|その他| J[終了]
    G -->|development| J
:::

## デプロイメント戦略

開発環境と本番環境の両方のデプロイメントで使用:

- デプロイメントタイプ: runOnce
- プラットフォーム: Azure Container Apps (ACA)
- 環境固有の変数
- テンプレートを使用した自動デプロイ

`deploy-template.yml`に関する備忘:

- デプロイテンプレートは `environmentName` と `azureSubscription` を受け取ります。
- `AzureCLI@2` タスクで `az containerapp update` を実行し、Container App のイメージを書き換えます。
- デプロイ時に使われるイメージは `${AcrName}.azurecr.io/${imageRepository}:${Build.BuildId}` です。
- `AcrName`, `imageRepository`, `ContainerAppName`, `ResourceGroupName` は環境変数ファイルで定義する必要があります。
- デプロイ時に `min-replicas`/`max-replicas`/`cpu`/`memory` といった実行設定、`ENVIRONMENT` や `DATABASE_URL` の環境変数をセットします（`DATABASE_URL` はライブラリのシークレット参照）。

## セキュリティ考慮事項

1. 環境固有の承認はAzure DevOpsで設定可能
2. 機密変数はAzure DevOps変数グループで管理
3. サービス接続（PJ925-Azure-ServiceConnection）がAzure認証を管理
4. 開発環境と本番環境で異なる変数ファイルを使用

## 環境変数ファイル

`.azure/pipelines/variables/` に環境ごとの変数定義があり、例として以下のように定義しています。実際の本番環境ではこれらを本番用に切り替えてください。

```yaml
variables:
    AcrName: "campdevjpeplatacr"  # ACR name (no FQDN)
    imageRepository: "quickstart"

    ResourceGroupName: "camp-dev-jpe-app-rg"
    ContainerAppName: "camp-dev-jpe-back-aca"
    ContainerAppEnvironment: "camp-dev-jpe-back-aca-env"
```

## ベストプラクティス

1. 再利用可能なパイプラインコンポーネントにテンプレートを使用
2. 環境ごとに別々の設定
3. 明確なステージの依存関係と条件
4. 関連する変更のみに対するパストリガー
