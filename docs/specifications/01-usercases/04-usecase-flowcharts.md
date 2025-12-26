# CAMPシステム ユースケース フロー図（ビジネス向け）

本文書は、CAMPシステムの主要な業務フローを図解したものです。
技術的な詳細を省き、ビジネスプロセスの流れを理解することを目的としています。

---

## 目次

1. [システム全体の概要](#1-システム全体の概要)
2. [ユーザー管理](#2-ユーザー管理)
3. [プロジェクト管理](#3-プロジェクト管理)
4. [個別施策分析](#4-個別施策分析)
5. [ドライバーツリー分析](#5-ドライバーツリー分析)
6. [データの流れ](#6-データの流れ)

---

## 1. システム全体の概要

### 1.1 CAMPシステムでできること

::: mermaid
graph TB
    subgraph CAMP["🏢 CAMPシステム"]
        direction TB

        subgraph 基盤["📋 基盤機能"]
            U["👤 ユーザー管理"]
            P["📁 プロジェクト管理"]
            F["📄 ファイル管理"]
        end

        subgraph 分析["📊 分析機能"]
            A["🔍 個別施策分析"]
            D["🌳 ドライバーツリー分析"]
        end

        基盤 --> 分析
    end

    style CAMP fill:#e8f4f8
    style 基盤 fill:#fff3cd
    style 分析 fill:#d4edda
:::

### 1.2 ユーザーの役割

::: mermaid
graph LR
    subgraph roles["👥 ユーザーの役割"]
        SA["🔧 システム管理者<br/>システム全体の管理"]
        PM["👔 プロジェクトマネージャー<br/>プロジェクトの責任者"]
        MOD["🛡️ モデレーター<br/>メンバー管理担当"]
        MEM["👤 メンバー<br/>分析作業者"]
        VIEW["👁️ 閲覧者<br/>結果の確認のみ"]
    end

    SA -.->|システム設定| PM
    PM -->|権限付与| MOD
    PM -->|権限付与| MEM
    MOD -->|権限付与| MEM
    MEM -.->|権限縮小| VIEW

    style SA fill:#ff6b6b,color:#fff
    style PM fill:#4ecdc4,color:#fff
    style MOD fill:#45b7d1,color:#fff
    style MEM fill:#96ceb4
    style VIEW fill:#dfe6e9
:::

---

## 2. ユーザー管理

### 2.1 初めてのログイン

::: mermaid
graph TD
    Start([🚀 CAMPにアクセス]) --> Login[🔐 Microsoft アカウントでログイン]
    Login --> Check{初めての<br/>ログイン？}

    Check -->|はい| Create[📝 アカウント自動作成]
    Create --> Welcome[🎉 ようこそ！<br/>ダッシュボード表示]

    Check -->|いいえ| Active{アカウント<br/>有効？}
    Active -->|はい| Welcome
    Active -->|いいえ| Error[⚠️ アカウント無効<br/>管理者に連絡]

    style Start fill:#4ecdc4,color:#fff
    style Welcome fill:#96ceb4
    style Error fill:#ff6b6b,color:#fff
:::

### 2.2 ユーザー権限の管理

::: mermaid
graph TD
    subgraph admin["🔧 システム管理者の操作"]
        A1[ユーザー一覧を確認] --> A2[対象ユーザーを選択]
        A2 --> A3{何をする？}

        A3 -->|権限付与| A4[✅ ロールを追加]
        A3 -->|権限剥奪| A5[❌ ロールを削除]
        A3 -->|無効化| A6[🚫 アカウント停止]
        A3 -->|有効化| A7[✅ アカウント復活]
    end

    style admin fill:#fff3cd
:::

---

## 3. プロジェクト管理

### 3.1 プロジェクトの始め方

::: mermaid
graph TD
    Start([💡 新しいプロジェクトを始めたい]) --> Create

    subgraph Create["📁 STEP 1: プロジェクト作成"]
        C1[プロジェクト名を入力]
        C2[プロジェクトコードを設定]
        C3[説明を記入]
        C1 --> C2 --> C3
    end

    Create --> Member

    subgraph Member["👥 STEP 2: メンバー招待"]
        M1[メンバーを検索]
        M2[役割を選択]
        M3[招待を送信]
        M1 --> M2 --> M3
    end

    Member --> File

    subgraph File["📄 STEP 3: ファイル準備"]
        F1[Excelファイルをアップロード]
        F2[データの確認]
        F1 --> F2
    end

    File --> Ready([🎯 分析開始準備完了！])

    style Start fill:#4ecdc4,color:#fff
    style Ready fill:#96ceb4
    style Create fill:#e8f4f8
    style Member fill:#fff3cd
    style File fill:#d4edda
:::

### 3.2 メンバーの役割と権限

::: mermaid
graph TB
    subgraph roles["📋 プロジェクト内の役割"]
        PM["👔 プロジェクトマネージャー"]
        MOD["🛡️ モデレーター"]
        MEM["👤 メンバー"]
        VIEW["👁️ 閲覧者"]
    end

    subgraph actions["🔧 できること"]
        A1["プロジェクト設定変更"]
        A2["メンバー管理"]
        A3["ファイルアップロード"]
        A4["分析の実行"]
        A5["結果の閲覧"]
    end

    PM --> A1 & A2 & A3 & A4 & A5
    MOD --> A2 & A3 & A4 & A5
    MEM --> A3 & A4 & A5
    VIEW --> A5

    style PM fill:#4ecdc4,color:#fff
    style MOD fill:#45b7d1,color:#fff
    style MEM fill:#96ceb4
    style VIEW fill:#dfe6e9
:::

### 3.3 ファイル管理の流れ

::: mermaid
graph LR
    subgraph upload["📤 アップロード"]
        U1[ファイル選択] --> U2[アップロード]
    end

    subgraph use["📊 利用"]
        U3[個別施策分析で使用]
        U4[ドライバーツリーで使用]
    end

    subgraph manage["🗂️ 管理"]
        U5[ファイル一覧確認]
        U6[不要なファイル削除]
    end

    upload --> use
    upload --> manage

    U2 -.-> U3
    U2 -.-> U4

    style upload fill:#d4edda
    style use fill:#e8f4f8
    style manage fill:#fff3cd
:::

---

## 4. 個別施策分析

### 4.1 分析の全体フロー

::: mermaid
graph TD
    Start([🎯 施策を分析したい]) --> Select

    subgraph Select["📋 STEP 1: 分析テーマ選択"]
        S1[検証カテゴリを選ぶ]
        S2[分析課題を選ぶ]
        S1 --> S2
    end

    Select --> Data

    subgraph Data["📄 STEP 2: データ準備"]
        D1[分析対象ファイルを選択]
        D2[シートを指定]
        D3[軸の設定]
        D1 --> D2 --> D3
    end

    Data --> Analysis

    subgraph Analysis["🤖 STEP 3: AI分析"]
        A1[AIに質問・指示]
        A2[分析結果を確認]
        A3[追加の質問]
        A1 --> A2 --> A3
        A3 -.-> A1
    end

    Analysis --> Result

    subgraph Result["📊 STEP 4: 結果活用"]
        R1[グラフ・数式の確認]
        R2[インサイトの抽出]
        R3[レポート作成]
        R1 --> R2 --> R3
    end

    Result --> End([✅ 分析完了])

    style Start fill:#4ecdc4,color:#fff
    style End fill:#96ceb4
    style Select fill:#fff3cd
    style Data fill:#e8f4f8
    style Analysis fill:#d4edda
    style Result fill:#ffeaa7
:::

### 4.2 AIとの対話フロー

::: mermaid
graph TD
    subgraph chat["💬 AIチャット分析"]
        User1[👤 質問を入力] --> AI1[🤖 AIが分析]
        AI1 --> Result1[📊 結果表示]
        Result1 --> Check{満足？}

        Check -->|もっと深掘り| User2[👤 追加の質問]
        User2 --> AI1

        Check -->|別の観点で| Branch[🔀 過去の状態に戻る]
        Branch --> User3[👤 別の質問をする]
        User3 --> AI2[🤖 新しい分析]
        AI2 --> Result2[📊 別の結果]

        Check -->|OK| Save[💾 結果を保存]
    end

    style chat fill:#e8f4f8
:::

### 4.3 スナップショット（履歴）機能

::: mermaid
graph TD
    subgraph timeline["📸 分析の履歴管理"]
        S1["📸 スナップショット1<br/>最初の質問"]
        S2["📸 スナップショット2<br/>深掘り質問"]
        S3["📸 スナップショット3<br/>さらに深掘り"]
        S4["📸 スナップショット4<br/>結論"]

        S1 --> S2 --> S3 --> S4

        S2 -.->|ここに戻って<br/>別の質問| S5["📸 スナップショット5<br/>別のアプローチ"]
        S5 --> S6["📸 スナップショット6<br/>別の結論"]
    end

    Note1[💡 いつでも過去の状態に<br/>戻って別の分析ができます]

    style timeline fill:#fff3cd
    style S5 fill:#d4edda
    style S6 fill:#d4edda
:::

---

## 5. ドライバーツリー分析

### 5.1 ドライバーツリーとは

::: mermaid
graph TD
    subgraph tree["🌳 ドライバーツリーの例：売上分析"]
        Root["💰 売上<br/>= 単価 × 数量"]

        Price["💵 単価"]
        Quantity["📦 数量<br/>= 新規 + 既存"]

        New["🆕 新規顧客数"]
        Existing["🔄 既存顧客数"]

        Root --> Price
        Root --> Quantity
        Quantity --> New
        Quantity --> Existing
    end

    Explain["💡 KPIを要素分解して<br/>どこを改善すべきか<br/>可視化するツール"]

    style tree fill:#e8f4f8
    style Root fill:#ff6b6b,color:#fff
    style Price fill:#4ecdc4,color:#fff
    style Quantity fill:#4ecdc4,color:#fff
    style New fill:#96ceb4
    style Existing fill:#96ceb4
:::

### 5.2 ツリー作成の流れ

::: mermaid
graph TD
    Start([🎯 KPIを分解したい]) --> Template

    subgraph Template["📋 STEP 1: テンプレート選択"]
        T1[業界を選択]
        T2[ドライバー型を選択]
        T3[数式テンプレートを選択]
        T1 --> T2 --> T3
    end

    Template --> Build

    subgraph Build["🔧 STEP 2: ツリー構築"]
        B1[ルートノード設定<br/>（目標KPI）]
        B2[子ノード追加<br/>（構成要素）]
        B3[計算式設定<br/>（+, -, ×, ÷）]
        B1 --> B2 --> B3
        B3 -.-> B2
    end

    Build --> Data

    subgraph Data["📊 STEP 3: データ紐付け"]
        D1[Excelデータを選択]
        D2[各ノードにデータを割当]
        D3[計算結果を確認]
        D1 --> D2 --> D3
    end

    Data --> Policy

    subgraph Policy["🎯 STEP 4: 施策検討"]
        P1[施策を追加]
        P2[効果をシミュレーション]
        P3[最適な施策を特定]
        P1 --> P2 --> P3
    end

    Policy --> End([✅ 改善ポイント特定完了])

    style Start fill:#4ecdc4,color:#fff
    style End fill:#96ceb4
    style Template fill:#fff3cd
    style Build fill:#e8f4f8
    style Data fill:#d4edda
    style Policy fill:#ffeaa7
:::

### 5.3 ノードの構築

::: mermaid
graph LR
    subgraph nodes["🔧 ノードの種類"]
        Root["🎯 ルートノード<br/>最終目標のKPI"]
        Calc["🔢 計算ノード<br/>他のノードから計算"]
        Data["📊 データノード<br/>実データを参照"]
        Input["✏️ 入力ノード<br/>手動で値を設定"]
    end

    subgraph ops["➗ 計算式"]
        Add["➕ 加算"]
        Sub["➖ 減算"]
        Mul["✖️ 乗算"]
        Div["➗ 除算"]
    end

    style nodes fill:#e8f4f8
    style ops fill:#fff3cd
:::

### 5.4 施策シミュレーション

::: mermaid
graph TD
    subgraph simulation["🎯 施策シミュレーション"]
        Current["📊 現状<br/>売上: 1,000万円"]

        subgraph policies["💡 施策案"]
            P1["施策A: 単価10%UP<br/>→ 売上: 1,100万円"]
            P2["施策B: 新規顧客20%UP<br/>→ 売上: 1,120万円"]
            P3["施策A+B 併用<br/>→ 売上: 1,232万円"]
        end

        Current --> policies

        Best["🏆 最適施策の選定"]
        policies --> Best
    end

    style simulation fill:#e8f4f8
    style Current fill:#dfe6e9
    style P1 fill:#fff3cd
    style P2 fill:#fff3cd
    style P3 fill:#d4edda
    style Best fill:#96ceb4
:::

---

## 6. データの流れ

### 6.1 システム全体のデータフロー

::: mermaid
graph TD
    subgraph input["📥 入力"]
        Excel["📊 Excelファイル"]
        User["👤 ユーザー入力"]
    end

    subgraph storage["💾 データ保管"]
        PF["📁 プロジェクトファイル"]
        Session["📋 分析セッション"]
        Tree["🌳 ドライバーツリー"]
    end

    subgraph process["⚙️ 処理"]
        AI["🤖 AI分析"]
        Calc["🔢 ツリー計算"]
    end

    subgraph output["📤 出力"]
        Chart["📊 グラフ"]
        Report["📝 レポート"]
        Insight["💡 インサイト"]
    end

    Excel --> PF
    User --> Session
    User --> Tree

    PF --> Session
    PF --> Tree

    Session --> AI
    Tree --> Calc

    AI --> Chart
    AI --> Insight
    Calc --> Chart
    Calc --> Report

    style input fill:#d4edda
    style storage fill:#e8f4f8
    style process fill:#fff3cd
    style output fill:#ffeaa7
:::

### 6.2 ファイルの利用関係

::: mermaid
graph TD
    subgraph upload["📤 ファイルアップロード"]
        F1["📊 売上データ.xlsx"]
        F2["📊 顧客データ.xlsx"]
    end

    subgraph usage["📊 利用先"]
        subgraph analysis["🔍 個別施策分析"]
            A1["分析セッション1"]
            A2["分析セッション2"]
        end

        subgraph driver["🌳 ドライバーツリー"]
            D1["売上ツリー"]
            D2["顧客ツリー"]
        end
    end

    F1 --> A1
    F1 --> A2
    F1 --> D1

    F2 --> A2
    F2 --> D2

    Note1["💡 1つのファイルを<br/>複数の分析で<br/>使いまわせます"]

    style upload fill:#d4edda
    style analysis fill:#e8f4f8
    style driver fill:#fff3cd
:::

### 6.3 プロジェクト終了までの流れ

::: mermaid
graph TD
    Start([🚀 プロジェクト開始]) --> Active

    subgraph Active["🟢 アクティブ状態"]
        Work["日々の分析作業"]
        Add["メンバー追加"]
        Upload["ファイル追加"]
    end

    Active --> Complete{プロジェクト<br/>完了？}

    Complete -->|継続| Active
    Complete -->|完了| Archive

    subgraph Archive["🟡 アーカイブ状態"]
        View["結果の閲覧のみ"]
        NoEdit["編集・追加は不可"]
    end

    Archive --> Reopen{再開する？}
    Reopen -->|はい| Active
    Reopen -->|いいえ| End([📦 プロジェクト保管])

    style Start fill:#4ecdc4,color:#fff
    style Active fill:#d4edda
    style Archive fill:#fff3cd
    style End fill:#dfe6e9
:::

---

## 7. よくある業務シナリオ

### 7.1 新商品の売上分析

::: mermaid
graph TD
    Scenario["📋 シナリオ：新商品Aの売上が目標未達"]

    Scenario --> Step1

    subgraph Step1["STEP 1: データ準備"]
        S1A["売上データをアップロード"]
        S1B["顧客データをアップロード"]
    end

    Step1 --> Step2

    subgraph Step2["STEP 2: 個別施策分析"]
        S2A["AIに質問：なぜ売上が低い？"]
        S2B["AIの回答：購入率が低い傾向"]
        S2C["深掘り：どの顧客層？"]
        S2D["回答：30代女性の購入率が特に低い"]
    end

    Step2 --> Step3

    subgraph Step3["STEP 3: ドライバーツリー"]
        S3A["売上を要素分解"]
        S3B["30代女性の購入率を改善した場合をシミュレーション"]
        S3C["効果：売上15%向上の見込み"]
    end

    Step3 --> Action["🎯 アクション：30代女性向けプロモーション実施"]

    style Scenario fill:#ff6b6b,color:#fff
    style Step1 fill:#e8f4f8
    style Step2 fill:#d4edda
    style Step3 fill:#fff3cd
    style Action fill:#96ceb4
:::

### 7.2 複数メンバーでの協業

::: mermaid
graph LR
    subgraph team["👥 チーム構成"]
        PM["👔 田中さん<br/>PM"]
        Ana1["👤 佐藤さん<br/>分析担当"]
        Ana2["👤 鈴木さん<br/>分析担当"]
        View["👁️ 山田さん<br/>報告先"]
    end

    subgraph work["📊 作業分担"]
        W1["プロジェクト作成"]
        W2["売上分析"]
        W3["顧客分析"]
        W4["結果確認"]
    end

    PM --> W1
    Ana1 --> W2
    Ana2 --> W3
    View --> W4

    W2 --> W4
    W3 --> W4

    style team fill:#e8f4f8
    style work fill:#fff3cd
:::

---

## 8. 用語集

| 用語 | 説明 |
|------|------|
| **プロジェクト** | 分析作業をまとめる単位。メンバーやファイルを管理します |
| **分析セッション** | 1つの分析課題に取り組む作業単位 |
| **スナップショット** | 分析の途中状態を保存したもの。いつでも戻れます |
| **ドライバーツリー** | KPIを構成要素に分解した図 |
| **ノード** | ドライバーツリーの各要素（箱） |
| **施策** | ノードに設定する改善案とその効果値 |
| **検証マスタ** | 分析テーマの大分類 |
| **課題マスタ** | 具体的な分析課題の定義 |

---

## 9. 困ったときは

### 9.1 よくある質問

::: mermaid
graph TD
    Q1["❓ ファイルをアップロードできない"]
    A1["✅ ファイル形式を確認<br/>（Excel形式のみ対応）"]

    Q2["❓ 分析結果がおかしい"]
    A2["✅ スナップショットで<br/>過去の状態に戻って<br/>別の質問を試す"]

    Q3["❓ メンバーを追加できない"]
    A3["✅ 自分の権限を確認<br/>（PMまたはモデレーター<br/>のみ追加可能）"]

    Q4["❓ プロジェクトが見つからない"]
    A4["✅ アーカイブ済みの<br/>可能性を確認"]

    Q1 --> A1
    Q2 --> A2
    Q3 --> A3
    Q4 --> A4

    style Q1 fill:#ff6b6b,color:#fff
    style Q2 fill:#ff6b6b,color:#fff
    style Q3 fill:#ff6b6b,color:#fff
    style Q4 fill:#ff6b6b,color:#fff
    style A1 fill:#96ceb4
    style A2 fill:#96ceb4
    style A3 fill:#96ceb4
    style A4 fill:#96ceb4
:::

---

##### ドキュメント管理情報

- **作成日**: 2025年12月24日
- **対象読者**: ビジネスメンバー、プロジェクト参加者
- **目的**: CAMPシステムの業務フローの理解促進
