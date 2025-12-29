# CAMPシステム ユースケース一覧

本文書は、ER図から抽出したユースケースを分類別にまとめたものです。

---

## 1. ユーザー管理

### 1.1 認証・アカウント管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| U-001 | Azure ADでログインする | UserAccount |
| U-002 | ユーザーアカウントを作成する | UserAccount |
| U-003 | ユーザー情報を更新する | UserAccount |
| U-004 | ユーザーを無効化する（論理削除） | UserAccount |
| U-005 | ユーザーを有効化する | UserAccount |
| U-006 | 最終ログイン日時を記録する | UserAccount |
| U-007 | ユーザー一覧を取得する | UserAccount |
| U-008 | ユーザー詳細を取得する | UserAccount |

### 1.2 ロール管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| U-009 | システムロールを付与する | UserAccount |
| U-010 | システムロールを剥奪する | UserAccount |
| U-011 | ユーザーのロールを確認する | UserAccount |

---

## 2. プロジェクト管理

### 2.1 プロジェクト基本操作

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| P-001 | プロジェクトを作成する | Project |
| P-002 | プロジェクト情報を更新する | Project |
| P-003 | プロジェクトを無効化する（論理削除） | Project |
| P-004 | プロジェクトを有効化する | Project |
| P-005 | プロジェクト一覧を取得する | Project |
| P-006 | プロジェクト詳細を取得する | Project |
| P-007 | プロジェクトコードで検索する | Project |

### 2.2 プロジェクトメンバー管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| PM-001 | メンバーをプロジェクトに追加する | ProjectMember, UserAccount, Project |
| PM-002 | メンバーをプロジェクトから削除する | ProjectMember |
| PM-003 | メンバーのロールを変更する | ProjectMember |
| PM-004 | プロジェクトメンバー一覧を取得する | ProjectMember, UserAccount |
| PM-005 | ユーザーが参加しているプロジェクト一覧を取得する | ProjectMember, Project |
| PM-006 | メンバーの権限を確認する | ProjectMember |

### 2.3 プロジェクトファイル管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| PF-001 | ファイルをアップロードする | ProjectFile, Project |
| PF-002 | ファイルをダウンロードする | ProjectFile |
| PF-003 | ファイルを削除する | ProjectFile |
| PF-004 | プロジェクトのファイル一覧を取得する | ProjectFile |
| PF-005 | ファイル詳細を取得する | ProjectFile |
| PF-006 | ファイルのアップロード者を確認する | ProjectFile, UserAccount |

---

## 3. 個別施策分析

### 3.1 マスタ管理（検証マスタ）

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AVM-001 | 検証マスタを作成する | AnalysisValidationMaster |
| AVM-002 | 検証マスタを更新する | AnalysisValidationMaster |
| AVM-003 | 検証マスタを削除する | AnalysisValidationMaster |
| AVM-004 | 検証マスタ一覧を取得する | AnalysisValidationMaster |
| AVM-005 | 検証マスタの表示順を変更する | AnalysisValidationMaster |

### 3.2 マスタ管理（課題マスタ）

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AIM-001 | 課題マスタを作成する | AnalysisIssueMaster, AnalysisValidationMaster |
| AIM-002 | 課題マスタを更新する | AnalysisIssueMaster |
| AIM-003 | 課題マスタを削除する | AnalysisIssueMaster |
| AIM-004 | 課題マスタ一覧を取得する | AnalysisIssueMaster |
| AIM-005 | 検証別の課題一覧を取得する | AnalysisIssueMaster, AnalysisValidationMaster |
| AIM-006 | エージェントプロンプトを設定する | AnalysisIssueMaster |
| AIM-007 | 初期メッセージを設定する | AnalysisIssueMaster |
| AIM-008 | ダミーヒント・入力データを設定する | AnalysisIssueMaster |

### 3.3 マスタ管理（グラフ軸マスタ）

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AGM-001 | グラフ軸マスタを作成する | AnalysisGraphAxisMaster, AnalysisIssueMaster |
| AGM-002 | グラフ軸マスタを更新する | AnalysisGraphAxisMaster |
| AGM-003 | グラフ軸マスタを削除する | AnalysisGraphAxisMaster |
| AGM-004 | 課題別のグラフ軸一覧を取得する | AnalysisGraphAxisMaster |

### 3.4 マスタ管理（ダミー数式・チャート）

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| ADM-001 | ダミー数式マスタを作成する | AnalysisDummyFormulaMaster, AnalysisIssueMaster |
| ADM-002 | ダミー数式マスタを更新する | AnalysisDummyFormulaMaster |
| ADM-003 | ダミー数式マスタを削除する | AnalysisDummyFormulaMaster |
| ADM-004 | 課題別のダミー数式一覧を取得する | AnalysisDummyFormulaMaster |
| ADM-005 | ダミーチャートマスタを作成する | AnalysisDummyChartMaster, AnalysisIssueMaster |
| ADM-006 | ダミーチャートマスタを更新する | AnalysisDummyChartMaster |
| ADM-007 | ダミーチャートマスタを削除する | AnalysisDummyChartMaster |
| ADM-008 | 課題別のダミーチャート一覧を取得する | AnalysisDummyChartMaster |

### 3.5 分析セッション管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AS-001 | 分析セッションを作成する | AnalysisSession, Project, UserAccount, AnalysisIssueMaster |
| AS-002 | 分析セッションを削除する | AnalysisSession |
| AS-003 | プロジェクト別の分析セッション一覧を取得する | AnalysisSession, Project |
| AS-004 | ユーザー別の分析セッション一覧を取得する | AnalysisSession, UserAccount |
| AS-005 | 分析セッション詳細を取得する | AnalysisSession |
| AS-006 | 入力ファイルを設定する | AnalysisSession, AnalysisFile |
| AS-007 | 現在のスナップショット番号を更新する | AnalysisSession |

### 3.6 分析ファイル管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AF-001 | 分析ファイルを作成する | AnalysisFile, AnalysisSession, ProjectFile |
| AF-002 | 分析ファイルを更新する | AnalysisFile |
| AF-003 | 分析ファイルを削除する | AnalysisFile |
| AF-004 | セッション別の分析ファイル一覧を取得する | AnalysisFile |
| AF-005 | 軸設定を更新する | AnalysisFile |
| AF-006 | データを更新する | AnalysisFile |

### 3.7 スナップショット管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| ASN-001 | スナップショットを作成する | AnalysisSnapshot, AnalysisSession |
| ASN-002 | スナップショットを削除する | AnalysisSnapshot |
| ASN-003 | セッション別のスナップショット一覧を取得する | AnalysisSnapshot |
| ASN-004 | スナップショット詳細を取得する | AnalysisSnapshot |
| ASN-005 | 過去のスナップショットに戻る | AnalysisSnapshot, AnalysisSession |

### 3.8 チャット管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AC-001 | チャットメッセージを送信する | AnalysisChat, AnalysisSnapshot |
| AC-002 | チャット履歴を取得する | AnalysisChat |
| AC-003 | チャットメッセージを削除する | AnalysisChat |

### 3.9 分析ステップ管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| AST-001 | 分析ステップを作成する | AnalysisStep, AnalysisSnapshot |
| AST-002 | 分析ステップを更新する | AnalysisStep |
| AST-003 | 分析ステップを削除する | AnalysisStep |
| AST-004 | スナップショット別のステップ一覧を取得する | AnalysisStep |
| AST-005 | ステップの設定を変更する | AnalysisStep |
| AST-006 | ステップの順序を変更する | AnalysisStep |

---

## 4. ドライバーツリー

### 4.1 カテゴリ・数式マスタ管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DTC-001 | カテゴリマスタを作成する | DriverTreeCategory |
| DTC-002 | カテゴリマスタを更新する | DriverTreeCategory |
| DTC-003 | カテゴリマスタを削除する | DriverTreeCategory |
| DTC-004 | カテゴリマスタ一覧を取得する | DriverTreeCategory |
| DTC-005 | 業界分類で絞り込む | DriverTreeCategory |
| DTC-006 | 業界名で絞り込む | DriverTreeCategory |
| DTC-007 | ドライバー型で絞り込む | DriverTreeCategory |
| DTF-001 | 数式マスタを作成する | DriverTreeFormula, DriverTreeCategory |
| DTF-002 | 数式マスタを更新する | DriverTreeFormula |
| DTF-003 | 数式マスタを削除する | DriverTreeFormula |
| DTF-004 | ドライバー型別の数式一覧を取得する | DriverTreeFormula |
| DTF-005 | KPIで数式を検索する | DriverTreeFormula |

### 4.2 ドライバーツリー基本操作

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DT-001 | ドライバーツリーを作成する | DriverTree, Project |
| DT-002 | ドライバーツリーを更新する | DriverTree |
| DT-003 | ドライバーツリーを削除する | DriverTree |
| DT-004 | プロジェクト別のドライバーツリー一覧を取得する | DriverTree, Project |
| DT-005 | ドライバーツリー詳細を取得する | DriverTree |
| DT-006 | ルートノードを設定する | DriverTree, DriverTreeNode |
| DT-007 | 数式マスタを紐付ける | DriverTree, DriverTreeFormula |
| DT-008 | 数式マスタの紐付けを解除する | DriverTree |

### 4.3 ノード管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DTN-001 | ノードを作成する | DriverTreeNode |
| DTN-002 | ノードを更新する | DriverTreeNode |
| DTN-003 | ノードを削除する | DriverTreeNode |
| DTN-004 | ノードの位置を変更する | DriverTreeNode |
| DTN-005 | ノードのラベルを変更する | DriverTreeNode |
| DTN-006 | ノードのタイプを変更する | DriverTreeNode |
| DTN-007 | ノードにデータフレームを紐付ける | DriverTreeNode, DriverTreeDataFrame |
| DTN-008 | ノードのデータフレーム紐付けを解除する | DriverTreeNode |

### 4.4 リレーションシップ管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DTR-001 | リレーションシップを作成する | DriverTreeRelationship, DriverTree, DriverTreeNode |
| DTR-002 | リレーションシップを更新する | DriverTreeRelationship |
| DTR-003 | リレーションシップを削除する | DriverTreeRelationship |
| DTR-004 | ツリー別のリレーションシップ一覧を取得する | DriverTreeRelationship |
| DTR-005 | 演算子を変更する | DriverTreeRelationship |
| DTR-006 | 親ノードを変更する | DriverTreeRelationship, DriverTreeNode |

### 4.5 リレーションシップ子ノード管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DTRC-001 | 子ノードを追加する | DriverTreeRelationshipChild, DriverTreeRelationship, DriverTreeNode |
| DTRC-002 | 子ノードを削除する | DriverTreeRelationshipChild |
| DTRC-003 | 子ノードの順序を変更する | DriverTreeRelationshipChild |
| DTRC-004 | リレーションシップ別の子ノード一覧を取得する | DriverTreeRelationshipChild |

### 4.6 ファイル・データフレーム管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DTFL-001 | ドライバーツリーファイルを作成する | DriverTreeFile, ProjectFile |
| DTFL-002 | ドライバーツリーファイルを更新する | DriverTreeFile |
| DTFL-003 | ドライバーツリーファイルを削除する | DriverTreeFile |
| DTFL-004 | ファイル一覧を取得する | DriverTreeFile |
| DTFL-005 | 軸設定を更新する | DriverTreeFile |
| DTDF-001 | データフレームを作成する | DriverTreeDataFrame, DriverTreeFile |
| DTDF-002 | データフレームを更新する | DriverTreeDataFrame |
| DTDF-003 | データフレームを削除する | DriverTreeDataFrame |
| DTDF-004 | ファイル別のデータフレーム一覧を取得する | DriverTreeDataFrame |
| DTDF-005 | 列名でデータフレームを検索する | DriverTreeDataFrame |

### 4.7 施策管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| DTP-001 | 施策を作成する | DriverTreePolicy, DriverTreeNode |
| DTP-002 | 施策を更新する | DriverTreePolicy |
| DTP-003 | 施策を削除する | DriverTreePolicy |
| DTP-004 | ノード別の施策一覧を取得する | DriverTreePolicy |
| DTP-005 | 施策の値を変更する | DriverTreePolicy |
| DTP-006 | 施策のラベルを変更する | DriverTreePolicy |

---

## 5. ダッシュボード・統計

### 5.1 ダッシュボード

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| D-001 | ダッシュボード統計情報を取得する | Project, AnalysisSession, DriverTree, UserAccount |
| D-002 | 最近のアクティビティ一覧を取得する | RoleHistory, Project, AnalysisSession, DriverTree, ProjectFile |
| D-003 | 分析アクティビティチャートを取得する | AnalysisSession, AnalysisSnapshot |
| D-004 | プロジェクト進捗情報を取得する | Project, AnalysisSession |
| D-005 | プロジェクト分布チャートを取得する | Project |
| D-006 | ユーザーアクティビティチャートを取得する | UserAccount, RoleHistory |

---

## 6. テンプレート機能

### 6.1 ツリーテンプレート

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| TM-001 | テンプレート一覧を取得する | AnalysisTemplate |
| TM-002 | テンプレートを業種で絞り込む | AnalysisTemplate |
| TM-003 | テンプレートを分析タイプで絞り込む | AnalysisTemplate |
| TM-004 | テンプレート詳細をプレビューする | AnalysisTemplate |
| TM-005 | テンプレートからツリーを作成する | DriverTree, AnalysisTemplate |

---

## 7. 複製・エクスポート機能

### 7.1 複製機能

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| CP-001 | 分析セッションを複製する | AnalysisSession, AnalysisSnapshot, AnalysisStep |
| CP-002 | ドライバーツリーを複製する | DriverTree, DriverTreeNode, DriverTreePolicy |

### 7.2 エクスポート・レポート機能（将来実装予定）

> **注記**: 以下のユースケースはフロントエンド機能として将来実装予定です。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| EX-001 | セッション結果をレポート出力する | AnalysisSession, AnalysisSnapshot | 将来実装 |
| EX-002 | ツリー計算結果をエクスポートする | DriverTree, DriverTreeNode | 将来実装 |
| EX-003 | セッション結果を共有する | AnalysisSession | 将来実装 |

---

## 8. ファイルバージョン管理

### 8.1 バージョン管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| FV-001 | ファイルの新バージョンをアップロードする | ProjectFile |
| FV-002 | ファイルのバージョン履歴を取得する | ProjectFile |
| FV-003 | 過去のバージョンをダウンロードする | ProjectFile |
| FV-004 | 最新バージョンを確認する | ProjectFile |

---

## 9. システム管理（管理者専用）

> **注記**: 以下のユースケースはシステム管理者（SystemAdmin）ロールを持つユーザーのみが実行可能です。

### 9.1 ユーザー操作履歴追跡

ユーザーからの問い合わせ対応やトラブルシューティングのため、操作履歴を追跡します。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-001 | ユーザー操作履歴を検索する | UserActivity, UserAccount | 将来実装 |
| SA-002 | 日時・ユーザーで操作履歴を絞り込む | UserActivity | 将来実装 |
| SA-003 | エラー履歴を取得する | UserActivity | 将来実装 |
| SA-004 | 操作履歴の詳細を確認する | UserActivity | 将来実装 |
| SA-005 | UI操作イベントを記録する | UserActivity | 将来実装 |
| SA-006 | API呼び出しを自動記録する | UserActivity | 将来実装 |

### 9.2 全プロジェクト閲覧

システム管理者が全プロジェクトを横断的に閲覧・管理します。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-007 | 全プロジェクト一覧を取得する | Project | 将来実装 |
| SA-008 | プロジェクトをステータスで絞り込む | Project | 将来実装 |
| SA-009 | プロジェクトをオーナーで絞り込む | Project, UserAccount | 将来実装 |
| SA-010 | プロジェクトのストレージ使用量を確認する | Project, ProjectFile | 将来実装 |
| SA-011 | 非アクティブプロジェクトを一覧取得する | Project | 将来実装 |

### 9.3 詳細監査ログ

セキュリティ監査やコンプライアンス対応のための詳細なログ管理を行います。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-012 | データ変更履歴を取得する | AuditLog | 将来実装 |
| SA-013 | アクセスログを取得する | AuditLog | 将来実装 |
| SA-014 | セキュリティイベントを取得する | AuditLog | 将来実装 |
| SA-015 | 監査ログをエクスポートする | AuditLog | 将来実装 |
| SA-016 | 特定リソースの変更履歴を追跡する | AuditLog | 将来実装 |

### 9.4 システム設定

アプリケーションの動作設定やメンテナンス管理を行います。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-017 | アプリケーション設定を取得する | SystemSetting | 将来実装 |
| SA-018 | アプリケーション設定を更新する | SystemSetting | 将来実装 |
| SA-019 | メンテナンスモードを有効化する | SystemSetting | 将来実装 |
| SA-020 | メンテナンスモードを無効化する | SystemSetting | 将来実装 |
| SA-021 | 機能フラグを管理する | SystemSetting | 将来実装 |

### 9.5 システム統計ダッシュボード

システム全体の利用状況や健全性を監視します。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-022 | システム全体の統計情報を取得する | UserAccount, Project, AnalysisSession | 将来実装 |
| SA-023 | アクティブユーザー推移を取得する | UserAccount, UserActivity | 将来実装 |
| SA-024 | ストレージ使用量推移を取得する | ProjectFile | 将来実装 |
| SA-025 | APIリクエスト統計を取得する | UserActivity | 将来実装 |
| SA-026 | エラー発生率を監視する | UserActivity | 将来実装 |

### 9.6 一括操作

大量データの効率的な処理を行います。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-027 | ユーザーを一括インポートする | UserAccount | 将来実装 |
| SA-028 | ユーザー情報を一括エクスポートする | UserAccount | 将来実装 |
| SA-029 | 非アクティブユーザーを一括無効化する | UserAccount | 将来実装 |
| SA-030 | 古いプロジェクトを一括アーカイブする | Project | 将来実装 |

### 9.7 通知・アラート管理

システムアラートやユーザーへの通知を管理します。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-031 | システムアラートを設定する | SystemAlert | 将来実装 |
| SA-032 | 通知テンプレートを管理する | NotificationTemplate | 将来実装 |
| SA-033 | システムお知らせを配信する | SystemAnnouncement | 将来実装 |
| SA-034 | メンテナンス予告を登録する | MaintenanceNotice | 将来実装 |

### 9.8 セキュリティ管理

セッション管理やセキュリティイベントの監視を行います。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-035 | アクティブセッション一覧を取得する | UserSession, UserAccount | 将来実装 |
| SA-036 | ユーザーを強制ログアウトする | UserSession | 将来実装 |

### 9.9 データ管理・クリーンアップ

データのライフサイクル管理とクリーンアップを行います。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-037 | 古いデータを一括削除する | 全エンティティ | 将来実装 |
| SA-038 | 孤立ファイルをクリーンアップする | ProjectFile | 将来実装 |
| SA-039 | データ保持ポリシーを設定する | SystemSetting | 将来実装 |
| SA-040 | マスタデータを一括インポートする | 各マスタエンティティ | 将来実装 |

### 9.10 サポートツール

ユーザーサポートやシステム診断のためのツールを提供します。

| ID | ユースケース | 関連エンティティ | 実装状態 |
|----|-------------|-----------------|---------|
| SA-041 | ユーザーとして操作を代行する | UserAccount | 将来実装 |
| SA-042 | デバッグモードを有効化する | SystemSetting | 将来実装 |
| SA-043 | システムヘルスチェックを実行する | - | 将来実装 |

---

## 10. 横断的ユースケース

### 10.1 検索・フィルタリング

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| X-001 | ユーザーをメールアドレスで検索する | UserAccount |
| X-002 | ユーザーをAzure OIDで検索する | UserAccount |
| X-003 | プロジェクトを名前で検索する | Project |
| X-004 | プロジェクトをコードで検索する | Project |
| X-005 | ファイルをMIMEタイプで絞り込む | ProjectFile |
| X-006 | アクティブなプロジェクトのみ取得する | Project |
| X-007 | アクティブなユーザーのみ取得する | UserAccount |
| X-017 | セッションを課題別に絞り込む | AnalysisSession, AnalysisIssueMaster |
| X-018 | カテゴリを業界分類で絞り込む | DriverTreeCategory |

### 10.2 権限・アクセス制御

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| X-008 | ユーザーのプロジェクト権限を確認する | ProjectMember, UserAccount, Project |
| X-009 | プロジェクトマネージャー権限を確認する | ProjectMember |
| X-010 | システム管理者権限を確認する | UserAccount |
| X-011 | ファイル操作権限を確認する | ProjectMember, ProjectFile |

### 10.3 監査・履歴

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| X-012 | 作成日時を記録する | 全エンティティ |
| X-013 | 更新日時を記録する | 全エンティティ |
| X-014 | 作成者を記録する | Project, AnalysisSession |
| X-015 | アップロード者を記録する | ProjectFile |
| X-016 | メンバー追加者を記録する | ProjectMember |

---

## 11. 統計情報

### ユースケース数サマリー

| 分類 | ユースケース数 |
|-----|--------------|
| ユーザー管理 | 11 |
| プロジェクト管理 | 20 |
| 個別施策分析（マスタ） | 25 |
| 個別施策分析（セッション） | 24 |
| ドライバーツリー | 41 |
| ダッシュボード・統計 | 6 |
| テンプレート機能 | 5 |
| 複製・エクスポート機能 | 5 |
| ファイルバージョン管理 | 4 |
| システム管理（管理者専用） | 43 |
| 横断的ユースケース | 18 |
| **合計** | **202** |

---

## 12. 関連ドキュメント

- **ER図**: `../05-database/02-er-diagram.md`
- **データベース設計書**: `../05-database/01-database-design.md`
- **API仕様書**: `../07-api/01-api-specifications.md`

---

### ドキュメント管理情報

- **作成日**: 2025年12月24日
- **更新日**: 2025年12月29日
- **抽出元**: ER図（02-er-diagram.md）、モックアップ仕様（03-mockup）
- **抽出方法**: エンティティとリレーションシップから導出、モックアップUI分析
