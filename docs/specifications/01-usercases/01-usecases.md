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

## 6. 横断的ユースケース

### 6.1 検索・フィルタリング

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

### 6.2 権限・アクセス制御

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| X-008 | ユーザーのプロジェクト権限を確認する | ProjectMember, UserAccount, Project |
| X-009 | プロジェクトマネージャー権限を確認する | ProjectMember |
| X-010 | システム管理者権限を確認する | UserAccount |
| X-011 | ファイル操作権限を確認する | ProjectMember, ProjectFile |

### 6.3 監査・履歴

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| X-012 | 作成日時を記録する | 全エンティティ |
| X-013 | 更新日時を記録する | 全エンティティ |
| X-014 | 作成者を記録する | Project, AnalysisSession |
| X-015 | アップロード者を記録する | ProjectFile |
| X-016 | メンバー追加者を記録する | ProjectMember |

---

## 7. 複製・エクスポート機能

### 7.1 複製機能

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| CP-001 | 分析セッションを複製する | AnalysisSession, AnalysisSnapshot, AnalysisStep |
| CP-002 | ドライバーツリーを複製する | DriverTree, DriverTreeNode, DriverTreePolicy |

### 7.2 エクスポート・レポート機能

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| EX-001 | セッション結果をレポート出力する | AnalysisSession, AnalysisSnapshot |
| EX-002 | ツリー計算結果をエクスポートする | DriverTree, DriverTreeNode |
| EX-003 | セッション結果を共有する | AnalysisSession |

---

## 8. テンプレート機能

### 8.1 ツリーテンプレート

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| TM-001 | テンプレート一覧を取得する | AnalysisTemplate |
| TM-002 | テンプレートを業種で絞り込む | AnalysisTemplate |
| TM-003 | テンプレートを分析タイプで絞り込む | AnalysisTemplate |
| TM-004 | テンプレート詳細をプレビューする | AnalysisTemplate |
| TM-005 | テンプレートからツリーを作成する | DriverTree, AnalysisTemplate |

---

## 9. ファイルバージョン管理

### 9.1 バージョン管理

| ID | ユースケース | 関連エンティティ |
|----|-------------|-----------------|
| FV-001 | ファイルの新バージョンをアップロードする | ProjectFile |
| FV-002 | ファイルのバージョン履歴を取得する | ProjectFile |
| FV-003 | 過去のバージョンをダウンロードする | ProjectFile |
| FV-004 | 最新バージョンを確認する | ProjectFile |

---

## 10. 統計情報

### ユースケース数サマリー

| 分類 | ユースケース数 |
|-----|--------------|
| ユーザー管理 | 11 |
| プロジェクト管理 | 20 |
| 個別施策分析（マスタ） | 25 |
| 個別施策分析（セッション） | 24 |
| ドライバーツリー | 41 |
| ダッシュボード・統計 | 6 |
| 横断的ユースケース | 18 |
| 複製・エクスポート機能 | 5 |
| テンプレート機能 | 5 |
| ファイルバージョン管理 | 4 |
| **合計** | **159** |

---

## 11. 関連ドキュメント

- **ER図**: `../03-database/02-er-diagram.md`
- **データベース設計書**: `../03-database/01-database-design.md`
- **API仕様書**: `../05-api/01-api-specifications.md`

---

### ドキュメント管理情報

- **作成日**: 2025年12月24日
- **更新日**: 2025年12月28日
- **抽出元**: ER図（02-er-diagram.md）、モックアップ仕様（03-mockup）
- **抽出方法**: エンティティとリレーションシップから導出、モックアップUI分析
