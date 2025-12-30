// ========================================
// System Administration Pages
// ========================================

const adminPages = {
    // ユーザー管理
    users: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム管理</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">ユーザー管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ユーザー管理</h1>
        </div>

        <div class="alert alert-info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-text">ユーザーはAzure AD認証により自動作成されます。ここでは既存ユーザーの管理を行います。</div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="search-bar">
                    <input type="text" class="form-input search-input" placeholder="名前またはメールで検索...">
                    <select class="form-select" style="width: 150px;">
                        <option value="">全てのロール</option>
                        <option value="ADMIN">ADMIN</option>
                        <option value="SYSTEM_USER">SYSTEM_USER</option>
                    </select>
                    <select class="form-select" style="width: 150px;">
                        <option value="">全てのステータス</option>
                        <option value="active">有効</option>
                        <option value="inactive">無効</option>
                    </select>
                    <button class="btn btn-secondary">検索</button>
                </div>

                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ユーザー</th>
                                <th>メールアドレス</th>
                                <th>システムロール</th>
                                <th>ステータス</th>
                                <th>最終ログイン</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span class="text-2xl">👤</span>
                                        <strong>管理者 太郎</strong>
                                    </div>
                                </td>
                                <td>admin@example.com</td>
                                <td><span class="badge badge-danger">ADMIN</span></td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td>2025/12/25 10:00</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary" onclick="navigateTo('user-detail')">詳細</button>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span class="text-2xl">👤</span>
                                        <strong>山田 太郎</strong>
                                    </div>
                                </td>
                                <td>yamada@example.com</td>
                                <td><span class="badge badge-info">SYSTEM_USER</span></td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td>2025/12/25 10:30</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary" onclick="navigateTo('user-detail')">詳細</button>
                                    <button class="btn btn-sm btn-danger">無効化</button>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span class="text-2xl">👤</span>
                                        <strong>退職者 次郎</strong>
                                    </div>
                                </td>
                                <td>taishoku@example.com</td>
                                <td><span class="badge badge-info">SYSTEM_USER</span></td>
                                <td><span class="badge badge-danger">無効</span></td>
                                <td>2025/11/30 18:00</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary" onclick="navigateTo('user-detail')">詳細</button>
                                    <button class="btn btn-sm btn-primary">有効化</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pagination mt-5">
                    <button class="pagination-btn" disabled>◀ 前へ</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">次へ ▶</button>
                </div>
            </div>
        </div>
    `,

    // ロール管理
    roles: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム管理</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">ロール管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ロール管理</h1>
        </div>

        <div class="alert alert-info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-text">システムロールは定義済みです。各ロールの権限を確認できます。</div>
            </div>
        </div>

        <div class="card mb-5">
            <div class="card-header">
                <h3 class="card-title">システムロール</h3>
            </div>
            <div class="card-body p-0">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ロール名</th>
                            <th>説明</th>
                            <th>権限</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="badge badge-danger">ADMIN</span></td>
                            <td>システム管理者</td>
                            <td>全ての操作が可能。マスタ管理、ユーザー管理を含む</td>
                        </tr>
                        <tr>
                            <td><span class="badge badge-info">SYSTEM_USER</span></td>
                            <td>一般ユーザー</td>
                            <td>プロジェクト作成、分析セッション、ドライバーツリーの操作が可能</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">プロジェクトロール</h3>
            </div>
            <div class="card-body p-0">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ロール名</th>
                            <th>説明</th>
                            <th>権限</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="badge badge-danger">PROJECT_MANAGER</span></td>
                            <td>プロジェクト管理者</td>
                            <td>プロジェクトの全操作、メンバー管理、設定変更が可能</td>
                        </tr>
                        <tr>
                            <td><span class="badge badge-warning">MODERATOR</span></td>
                            <td>モデレーター</td>
                            <td>コンテンツ管理、ファイル削除、メンバー追加が可能</td>
                        </tr>
                        <tr>
                            <td><span class="badge badge-success">MEMBER</span></td>
                            <td>メンバー</td>
                            <td>分析セッション、ドライバーツリーの作成・編集が可能</td>
                        </tr>
                        <tr>
                            <td><span class="badge badge-neutral">VIEWER</span></td>
                            <td>閲覧者</td>
                            <td>閲覧のみ。編集・作成不可</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `,

    // 検証マスタ管理
    verifications: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム管理</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">検証マスタ管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">検証マスタ管理</h1>
            <div class="page-actions">
                <button class="btn btn-primary">
                    <span>➕</span> 新規作成
                </button>
            </div>
        </div>

        <div class="card">
            <div class="card-body p-0">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>検証名</th>
                            <th>説明</th>
                            <th>関連課題</th>
                            <th>ステータス</th>
                            <th>更新日</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>時系列分析</strong></td>
                            <td>時系列データの予測と分析</td>
                            <td>2</td>
                            <td><span class="badge badge-success">有効</span></td>
                            <td>2025/12/20</td>
                            <td class="actions">
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('verification-edit')">編集</button>
                                <button class="btn btn-sm btn-danger">削除</button>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>コスト最適化</strong></td>
                            <td>コスト構造の可視化と最適化提案</td>
                            <td>1</td>
                            <td><span class="badge badge-success">有効</span></td>
                            <td>2025/12/18</td>
                            <td class="actions">
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('verification-edit')">編集</button>
                                <button class="btn btn-sm btn-danger">削除</button>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>セグメンテーション</strong></td>
                            <td>顧客やデータのセグメント分析</td>
                            <td>1</td>
                            <td><span class="badge badge-success">有効</span></td>
                            <td>2025/12/15</td>
                            <td class="actions">
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('verification-edit')">編集</button>
                                <button class="btn btn-sm btn-danger">削除</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `,

    // 課題マスタ管理
    issues: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム管理</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">課題マスタ管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">課題マスタ管理</h1>
            <div class="page-actions">
                <button class="btn btn-primary">
                    <span>➕</span> 新規作成
                </button>
            </div>
        </div>

        <div class="card">
            <div class="card-body p-0">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>課題名</th>
                            <th>検証マスタ</th>
                            <th>プロンプト設定</th>
                            <th>初期メッセージ</th>
                            <th>ステータス</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>売上予測</strong></td>
                            <td>時系列分析</td>
                            <td><span class="badge badge-success">設定済</span></td>
                            <td><span class="badge badge-success">設定済</span></td>
                            <td><span class="badge badge-success">有効</span></td>
                            <td class="actions">
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">編集</button>
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">プロンプト</button>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>コスト分析</strong></td>
                            <td>コスト最適化</td>
                            <td><span class="badge badge-success">設定済</span></td>
                            <td><span class="badge badge-warning">未設定</span></td>
                            <td><span class="badge badge-success">有効</span></td>
                            <td class="actions">
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">編集</button>
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">プロンプト</button>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>顧客分析</strong></td>
                            <td>セグメンテーション</td>
                            <td><span class="badge badge-warning">未設定</span></td>
                            <td><span class="badge badge-warning">未設定</span></td>
                            <td><span class="badge badge-warning">下書き</span></td>
                            <td class="actions">
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">編集</button>
                                <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">プロンプト</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `,

    // ユーザー詳細画面
    'user-detail': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#users">ユーザー管理</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">山田 太郎</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ユーザー詳細</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>✉️</span> メッセージ送信
                </button>
                <button class="btn btn-danger">無効化</button>
            </div>
        </div>

        <!-- ユーザープロファイルカード -->
        <div class="card mb-5">
            <div class="user-profile-header">
                <div class="user-profile-avatar">👤</div>
                <div class="user-profile-info">
                    <h2 class="user-profile-name">山田 太郎</h2>
                    <p class="user-profile-email">yamada.taro@example.com</p>
                    <div class="user-profile-badges">
                        <span class="badge badge-info">SYSTEM_USER</span>
                        <span class="badge badge-success">有効</span>
                    </div>
                </div>
            </div>
            <div class="user-profile-meta">
                <div class="user-meta-item">
                    <div class="user-meta-value">5</div>
                    <div class="user-meta-label">参加プロジェクト</div>
                </div>
                <div class="user-meta-item">
                    <div class="user-meta-value">23</div>
                    <div class="user-meta-label">作成セッション</div>
                </div>
                <div class="user-meta-item">
                    <div class="user-meta-value">12</div>
                    <div class="user-meta-label">作成ツリー</div>
                </div>
            </div>
        </div>

        <div class="user-detail-grid">
            <!-- メインコンテンツ -->
            <div class="user-main">
                <!-- 参加プロジェクト一覧 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">参加プロジェクト</h3>
                    </div>
                    <div class="card-body p-0">
                        <div class="user-project-item">
                            <div class="user-project-icon">📁</div>
                            <div class="user-project-info">
                                <div class="user-project-name">売上分析プロジェクト</div>
                                <div class="user-project-meta">MEMBER • 参加日: 2025/10/15</div>
                            </div>
                            <span class="badge badge-success">アクティブ</span>
                        </div>
                        <div class="user-project-item">
                            <div class="user-project-icon">📁</div>
                            <div class="user-project-info">
                                <div class="user-project-name">コスト削減プロジェクト</div>
                                <div class="user-project-meta">PROJECT_MANAGER • 参加日: 2025/09/01</div>
                            </div>
                            <span class="badge badge-success">アクティブ</span>
                        </div>
                        <div class="user-project-item">
                            <div class="user-project-icon">📁</div>
                            <div class="user-project-info">
                                <div class="user-project-name">新規事業分析</div>
                                <div class="user-project-meta">MODERATOR • 参加日: 2025/11/20</div>
                            </div>
                            <span class="badge badge-success">アクティブ</span>
                        </div>
                        <div class="user-project-item">
                            <div class="user-project-icon">📁</div>
                            <div class="user-project-info">
                                <div class="user-project-name">顧客分析プロジェクト</div>
                                <div class="user-project-meta">MEMBER • 参加日: 2025/08/10</div>
                            </div>
                            <span class="badge badge-neutral">完了</span>
                        </div>
                        <div class="user-project-item">
                            <div class="user-project-icon">📁</div>
                            <div class="user-project-info">
                                <div class="user-project-name">市場調査プロジェクト</div>
                                <div class="user-project-meta">VIEWER • 参加日: 2025/07/05</div>
                            </div>
                            <span class="badge badge-neutral">アーカイブ</span>
                        </div>
                    </div>
                </div>

                <!-- 最近のアクティビティ -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">最近のアクティビティ</h3>
                    </div>
                    <div class="card-body p-0">
                        <div class="activity-list">
                            <div class="activity-item">
                                <div class="activity-icon" style="background-color: var(--color-primary-100);">📊</div>
                                <div class="activity-content">
                                    <div class="activity-text">
                                        <strong>Q4売上分析</strong>セッションを作成しました
                                    </div>
                                    <div class="activity-time">5分前 • 売上分析プロジェクト</div>
                                </div>
                            </div>
                            <div class="activity-item">
                                <div class="activity-icon" style="background-color: var(--color-success-100);">🌳</div>
                                <div class="activity-content">
                                    <div class="activity-text">
                                        <strong>コストドライバーツリー</strong>を更新しました
                                    </div>
                                    <div class="activity-time">2時間前 • コスト削減プロジェクト</div>
                                </div>
                            </div>
                            <div class="activity-item">
                                <div class="activity-icon" style="background-color: var(--color-info-100);">📄</div>
                                <div class="activity-content">
                                    <div class="activity-text">
                                        <strong>monthly_data.csv</strong>をアップロードしました
                                    </div>
                                    <div class="activity-time">昨日 • 売上分析プロジェクト</div>
                                </div>
                            </div>
                            <div class="activity-item">
                                <div class="activity-icon" style="background-color: var(--color-success-100);">✅</div>
                                <div class="activity-content">
                                    <div class="activity-text">
                                        <strong>11月度分析</strong>セッションを完了しました
                                    </div>
                                    <div class="activity-time">3日前 • 売上分析プロジェクト</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- サイドバー -->
            <div class="user-sidebar">
                <!-- アカウント情報 -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h3 class="card-title">アカウント情報</h3>
                    </div>
                    <div class="card-body">
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">Azure ID</span>
                            <span class="issue-setting-value">abc123-def456</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">登録日</span>
                            <span class="issue-setting-value">2025/06/15</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">最終ログイン</span>
                            <span class="issue-setting-value">2025/12/25 10:30</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">ログイン回数</span>
                            <span class="issue-setting-value">156回</span>
                        </div>
                    </div>
                </div>

                <!-- ロール変更 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">システムロール</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group mb-4">
                            <label class="form-label">現在のロール</label>
                            <select class="form-select">
                                <option value="SYSTEM_USER" selected>SYSTEM_USER</option>
                                <option value="ADMIN">ADMIN</option>
                            </select>
                            <div class="form-help">ロールを変更すると権限が即座に反映されます</div>
                        </div>
                        <button class="btn btn-primary w-full">ロールを更新</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // 課題マスタ編集画面
    'issue-edit': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#issues">課題マスタ管理</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上予測</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">課題マスタ編集: 売上予測</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="navigateTo('issues')">キャンセル</button>
                <button class="btn btn-primary" onclick="showToast('success', '保存しました', '課題マスタが更新されました。')">
                    <span>💾</span> 保存
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">基本設定</button>
            <button class="tab">プロンプト設定</button>
            <button class="tab">初期メッセージ</button>
            <button class="tab">ダミーデータ</button>
        </div>

        <div class="issue-edit-grid">
            <!-- メインエディタ -->
            <div class="issue-main">
                <!-- タブコンテンツ: 基本設定 -->
                <div class="tab-content active">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">基本情報</h3>
                        </div>
                        <div class="card-body">
                            <div class="form-group mb-4">
                                <label class="form-label">課題名 <span class="required">*</span></label>
                                <input type="text" class="form-input" value="売上予測">
                            </div>
                            <div class="form-group mb-4">
                                <label class="form-label">検証マスタ <span class="required">*</span></label>
                                <select class="form-select">
                                    <option value="1" selected>時系列分析</option>
                                    <option value="2">コスト最適化</option>
                                    <option value="3">セグメンテーション</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">説明</label>
                                <textarea class="form-textarea" rows="3">過去の売上データを基に将来の売上を予測する分析課題です。時系列分析手法を用いて、季節性やトレンドを考慮した予測を行います。</textarea>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- タブコンテンツ: プロンプト設定 -->
                <div class="tab-content">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">AIプロンプト設定</h3>
                            <span class="badge badge-success">設定済</span>
                        </div>
                        <div class="card-body p-0">
                            <div class="prompt-editor">
                                <div class="prompt-editor-header">
                                    <span class="prompt-editor-title">システムプロンプト</span>
                                    <button class="btn btn-sm btn-secondary">テンプレートから選択</button>
                                </div>
                                <div class="prompt-editor-body">
                                    <textarea class="prompt-textarea">あなたは売上データ分析の専門家です。ユーザーから提供されるデータを分析し、売上予測を行ってください。

以下の点に注意して分析を進めてください：
1. データの季節性を確認する
2. 過去のトレンドを分析する
3. 異常値や外れ値を検出する
4. 予測モデルを適用し、信頼区間を提示する

ユーザーのデータ: {{data}}
分析期間: {{period}}
予測対象期間: {{forecast_period}}</textarea>
                                </div>
                                <div class="prompt-variables">
                                    <div class="prompt-variables-title">利用可能な変数 (クリックで挿入)</div>
                                    <div class="prompt-variable-list">
                                        <span class="prompt-variable">{{data}}</span>
                                        <span class="prompt-variable">{{period}}</span>
                                        <span class="prompt-variable">{{forecast_period}}</span>
                                        <span class="prompt-variable">{{user_name}}</span>
                                        <span class="prompt-variable">{{project_name}}</span>
                                        <span class="prompt-variable">{{tree_context}}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- タブコンテンツ: 初期メッセージ -->
                <div class="tab-content">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">初期メッセージ設定</h3>
                            <span class="badge badge-success">設定済</span>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label class="form-label">セッション開始時の初期メッセージ</label>
                                <textarea class="form-textarea" rows="4">こんにちは！売上予測分析を始めましょう。

まず、分析対象の期間と予測したい期間を教えてください。また、売上データがある場合はアップロードしてください。

どのような売上予測を行いたいですか？</textarea>
                            </div>
                            <div class="initial-message-preview">
                                <div class="initial-message-preview-title">プレビュー</div>
                                <div class="initial-message-bubble">
                                    こんにちは！売上予測分析を始めましょう。<br><br>
                                    まず、分析対象の期間と予測したい期間を教えてください。また、売上データがある場合はアップロードしてください。<br><br>
                                    どのような売上予測を行いたいですか？
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- タブコンテンツ: ダミーデータ -->
                <div class="tab-content">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">ダミーデータ（デバッグ用）</h3>
                            <button class="btn btn-sm btn-secondary">
                                <span>➕</span> データ追加
                            </button>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-warning mb-4">
                                <span class="alert-icon">⚠️</span>
                                <div class="alert-content">
                                    <div class="alert-text">ダミーデータは開発・テスト環境でのみ使用されます。本番環境では実際のデータが使用されます。</div>
                                </div>
                            </div>

                            <div class="dummy-data-section">
                                <div class="dummy-data-header">
                                    <span class="dummy-data-title">登録済みダミーデータ</span>
                                </div>
                                <div class="dummy-data-body">
                                    <div class="dummy-data-item">
                                        <div class="dummy-data-info">
                                            <div class="dummy-data-icon">📊</div>
                                            <div>
                                                <div class="dummy-data-name">sample_sales_2024.csv</div>
                                                <div class="dummy-data-meta">2.4 MB • 2025/12/20 アップロード</div>
                                            </div>
                                        </div>
                                        <button class="btn btn-sm btn-danger">削除</button>
                                    </div>
                                    <div class="dummy-data-item">
                                        <div class="dummy-data-info">
                                            <div class="dummy-data-icon">📊</div>
                                            <div>
                                                <div class="dummy-data-name">sample_sales_2023.csv</div>
                                                <div class="dummy-data-meta">1.8 MB • 2025/12/15 アップロード</div>
                                            </div>
                                        </div>
                                        <button class="btn btn-sm btn-danger">削除</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- サイドバー -->
            <div class="issue-sidebar">
                <!-- ステータス -->
                <div class="card issue-settings-card">
                    <div class="card-header">
                        <h3 class="card-title">ステータス</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <select class="form-select">
                                <option value="draft">下書き</option>
                                <option value="active" selected>有効</option>
                                <option value="inactive">無効</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- 設定状況 -->
                <div class="card issue-settings-card">
                    <div class="card-header">
                        <h3 class="card-title">設定状況</h3>
                    </div>
                    <div class="card-body">
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">プロンプト</span>
                            <span class="badge badge-success">設定済</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">初期メッセージ</span>
                            <span class="badge badge-success">設定済</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">ダミーデータ</span>
                            <span class="badge badge-success">2件</span>
                        </div>
                    </div>
                </div>

                <!-- メタ情報 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">メタ情報</h3>
                    </div>
                    <div class="card-body">
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">作成日</span>
                            <span class="issue-setting-value">2025/11/01</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">更新日</span>
                            <span class="issue-setting-value">2025/12/25</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">作成者</span>
                            <span class="issue-setting-value">管理者 太郎</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">使用回数</span>
                            <span class="issue-setting-value">47回</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // 検証マスタ編集画面
    'verification-edit': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#verifications">検証マスタ管理</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">時系列分析</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">検証マスタ編集: 時系列分析</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="navigateTo('verifications')">キャンセル</button>
                <button class="btn btn-primary" onclick="showToast('success', '保存しました', '検証マスタが更新されました。')">
                    <span>💾</span> 保存
                </button>
            </div>
        </div>

        <div class="issue-edit-grid">
            <div class="issue-main">
                <!-- 基本情報 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">基本情報</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group mb-4">
                            <label class="form-label">検証名 <span class="required">*</span></label>
                            <input type="text" class="form-input" value="時系列分析">
                        </div>
                        <div class="form-group mb-4">
                            <label class="form-label">説明</label>
                            <textarea class="form-textarea" rows="3">時系列データの予測と分析を行うための検証マスタです。季節性、トレンド、周期性などを考慮した分析が可能です。</textarea>
                        </div>
                        <div class="form-group">
                            <label class="form-label">ステータス</label>
                            <select class="form-select" style="width: 200px;">
                                <option value="active" selected>有効</option>
                                <option value="inactive">無効</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- 関連する課題 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">関連する課題 (2)</h3>
                    </div>
                    <div class="card-body p-0">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>課題名</th>
                                    <th>プロンプト設定</th>
                                    <th>ステータス</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>売上予測</strong></td>
                                    <td><span class="badge badge-success">設定済</span></td>
                                    <td><span class="badge badge-success">有効</span></td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-secondary" onclick="navigateTo('issue-edit')">編集</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>需要予測</strong></td>
                                    <td><span class="badge badge-warning">未設定</span></td>
                                    <td><span class="badge badge-warning">下書き</span></td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-secondary">編集</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- サイドバー -->
            <div class="issue-sidebar">
                <div class="card issue-settings-card">
                    <div class="card-header">
                        <h3 class="card-title">統計</h3>
                    </div>
                    <div class="card-body">
                        <div class="mini-stats">
                            <div class="mini-stat">
                                <div class="mini-stat-value">2</div>
                                <div class="mini-stat-label">関連課題</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">45</div>
                                <div class="mini-stat-label">使用回数</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">メタ情報</h3>
                    </div>
                    <div class="card-body">
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">作成日</span>
                            <span class="issue-setting-value">2025/08/01</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">更新日</span>
                            <span class="issue-setting-value">2025/12/20</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">作成者</span>
                            <span class="issue-setting-value">管理者 太郎</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // ========================================
    // 新規システム管理画面（SA-001〜SA-043対応）
    // ========================================

    // 操作履歴（SA-001〜SA-006）
    'admin-activity-logs': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">監視・運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">操作履歴</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">操作履歴</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>📥</span> エクスポート
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">全ての操作</button>
            <button class="tab">エラー履歴</button>
        </div>

        <!-- タブコンテンツ: 全ての操作 -->
        <div class="tab-content active">
            <div class="card mb-5">
                <div class="card-body">
                    <div class="search-bar">
                        <select class="form-select" style="width: 180px;">
                            <option value="">全てのユーザー</option>
                            <option value="1">管理者 太郎</option>
                            <option value="2">山田 太郎</option>
                            <option value="3">佐藤 次郎</option>
                        </select>
                        <select class="form-select" style="width: 150px;">
                            <option value="">全ての操作</option>
                            <option value="CREATE">CREATE</option>
                            <option value="READ">READ</option>
                            <option value="UPDATE">UPDATE</option>
                            <option value="DELETE">DELETE</option>
                            <option value="LOGIN">LOGIN</option>
                            <option value="LOGOUT">LOGOUT</option>
                        </select>
                        <select class="form-select" style="width: 150px;">
                            <option value="">全てのリソース</option>
                            <option value="PROJECT">PROJECT</option>
                            <option value="ANALYSIS_SESSION">SESSION</option>
                            <option value="DRIVER_TREE">TREE</option>
                            <option value="USER">USER</option>
                        </select>
                        <input type="datetime-local" class="form-input" style="width: 200px;" placeholder="開始日時">
                        <input type="datetime-local" class="form-input" style="width: 200px;" placeholder="終了日時">
                        <button class="btn btn-primary">検索</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-body p-0">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>日時</th>
                                    <th>ユーザー</th>
                                    <th>操作種別</th>
                                    <th>リソース</th>
                                    <th>エンドポイント</th>
                                    <th>ステータス</th>
                                    <th>処理時間</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>2025/12/30 10:30:15</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-success">CREATE</span></td>
                                    <td>PROJECT</td>
                                    <td><code>/api/v1/projects</code></td>
                                    <td><span class="badge badge-success">201</span></td>
                                    <td>150ms</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary" onclick="showToast('info', '詳細', '操作履歴の詳細モーダルを表示します')">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 10:28:42</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-info">READ</span></td>
                                    <td>ANALYSIS_SESSION</td>
                                    <td><code>/api/v1/analysis/session/abc123</code></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>85ms</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 10:25:18</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>佐藤 次郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-warning">UPDATE</span></td>
                                    <td>DRIVER_TREE</td>
                                    <td><code>/api/v1/driver-tree/tree/def456</code></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>220ms</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr class="table-row-error">
                                    <td>2025/12/30 10:20:05</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-danger">ERROR</span></td>
                                    <td>PROJECT</td>
                                    <td><code>/api/v1/projects/invalid-id</code></td>
                                    <td><span class="badge badge-danger">404</span></td>
                                    <td>25ms</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 10:15:33</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>管理者 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-primary">LOGIN</span></td>
                                    <td>USER</td>
                                    <td><code>/api/v1/auth/login</code></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>350ms</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 10:10:22</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>佐藤 次郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-danger">DELETE</span></td>
                                    <td>PROJECT_FILE</td>
                                    <td><code>/api/v1/projects/abc/files/xyz</code></td>
                                    <td><span class="badge badge-success">204</span></td>
                                    <td>180ms</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="pagination mt-5 p-4">
                        <button class="pagination-btn" disabled>◀ 前へ</button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">2</button>
                        <button class="pagination-btn">3</button>
                        <span class="pagination-ellipsis">...</span>
                        <button class="pagination-btn">20</button>
                        <button class="pagination-btn">次へ ▶</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: エラー履歴 -->
        <div class="tab-content">
            <div class="card mb-5">
                <div class="card-body">
                    <div class="search-bar">
                        <select class="form-select" style="width: 180px;">
                            <option value="">全てのユーザー</option>
                            <option value="1">管理者 太郎</option>
                            <option value="2">山田 太郎</option>
                            <option value="3">佐藤 次郎</option>
                        </select>
                        <select class="form-select" style="width: 150px;">
                            <option value="">全てのエラーコード</option>
                            <option value="400">400 - Bad Request</option>
                            <option value="401">401 - Unauthorized</option>
                            <option value="403">403 - Forbidden</option>
                            <option value="404">404 - Not Found</option>
                            <option value="500">500 - Server Error</option>
                        </select>
                        <input type="datetime-local" class="form-input" style="width: 200px;" placeholder="開始日時">
                        <input type="datetime-local" class="form-input" style="width: 200px;" placeholder="終了日時">
                        <button class="btn btn-primary">検索</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-body p-0">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>日時</th>
                                    <th>ユーザー</th>
                                    <th>エンドポイント</th>
                                    <th>ステータス</th>
                                    <th>エラーコード</th>
                                    <th>エラーメッセージ</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="table-row-error">
                                    <td>2025/12/30 10:20:05</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><code>/api/v1/projects/invalid-id</code></td>
                                    <td><span class="badge badge-danger">404</span></td>
                                    <td>RESOURCE_NOT_FOUND</td>
                                    <td>Project not found</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr class="table-row-error">
                                    <td>2025/12/30 09:45:22</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>佐藤 次郎</span>
                                        </div>
                                    </td>
                                    <td><code>/api/v1/projects</code></td>
                                    <td><span class="badge badge-danger">400</span></td>
                                    <td>VALIDATION_ERROR</td>
                                    <td>Project name is required</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr class="table-row-error">
                                    <td>2025/12/30 09:30:10</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><code>/api/v1/analysis/session/abc</code></td>
                                    <td><span class="badge badge-danger">500</span></td>
                                    <td>INTERNAL_ERROR</td>
                                    <td>Unexpected error occurred</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="pagination mt-5 p-4">
                        <button class="pagination-btn" disabled>◀ 前へ</button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">2</button>
                        <button class="pagination-btn">次へ ▶</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // 全プロジェクト管理（SA-007〜SA-011）
    'admin-projects': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">監視・運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">全プロジェクト</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">全プロジェクト管理</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>📦</span> 一括アーカイブ
                </button>
            </div>
        </div>

        <!-- 統計カード -->
        <div class="stats-grid mb-5">
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-content">
                    <div class="stat-value">150</div>
                    <div class="stat-label">総プロジェクト数</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-value">120</div>
                    <div class="stat-label">アクティブ</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-content">
                    <div class="stat-value">100.0 GB</div>
                    <div class="stat-label">総ストレージ使用量</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⏸️</div>
                <div class="stat-content">
                    <div class="stat-value">15</div>
                    <div class="stat-label">非アクティブ（30日以上）</div>
                </div>
            </div>
        </div>

        <div class="card mb-5">
            <div class="card-body">
                <div class="search-bar">
                    <input type="text" class="form-input search-input" placeholder="プロジェクト名で検索...">
                    <select class="form-select" style="width: 150px;">
                        <option value="">全てのステータス</option>
                        <option value="active">アクティブ</option>
                        <option value="archived">アーカイブ済み</option>
                        <option value="deleted">削除済み</option>
                    </select>
                    <select class="form-select" style="width: 180px;">
                        <option value="">全てのオーナー</option>
                        <option value="1">山田 太郎</option>
                        <option value="2">佐藤 次郎</option>
                        <option value="3">田中 花子</option>
                    </select>
                    <input type="number" class="form-input" style="width: 150px;" placeholder="非アクティブ日数">
                    <select class="form-select" style="width: 150px;">
                        <option value="last_activity">最終アクティビティ</option>
                        <option value="storage">ストレージ使用量</option>
                        <option value="created_at">作成日</option>
                    </select>
                    <button class="btn btn-primary">検索</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body p-0">
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox"></th>
                                <th>プロジェクト名</th>
                                <th>オーナー</th>
                                <th>ステータス</th>
                                <th>メンバー数</th>
                                <th>ストレージ使用量</th>
                                <th>最終アクティビティ</th>
                                <th>作成日</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><input type="checkbox"></td>
                                <td><strong>売上分析プロジェクト</strong></td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <span>山田 太郎</span>
                                    </div>
                                </td>
                                <td><span class="badge badge-success">アクティブ</span></td>
                                <td>5</td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <div class="progress-bar" style="width: 100px;">
                                            <div class="progress-fill" style="width: 45%;"></div>
                                        </div>
                                        <span>4.5 GB</span>
                                    </div>
                                </td>
                                <td>2025/12/30 10:30</td>
                                <td>2025/10/01</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary">詳細</button>
                                    <button class="btn btn-sm btn-warning">アーカイブ</button>
                                </td>
                            </tr>
                            <tr>
                                <td><input type="checkbox"></td>
                                <td><strong>コスト削減プロジェクト</strong></td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <span>佐藤 次郎</span>
                                    </div>
                                </td>
                                <td><span class="badge badge-success">アクティブ</span></td>
                                <td>3</td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <div class="progress-bar" style="width: 100px;">
                                            <div class="progress-fill" style="width: 80%;"></div>
                                        </div>
                                        <span>8.0 GB</span>
                                    </div>
                                </td>
                                <td>2025/12/29 15:00</td>
                                <td>2025/09/15</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary">詳細</button>
                                    <button class="btn btn-sm btn-warning">アーカイブ</button>
                                </td>
                            </tr>
                            <tr class="table-row-warning">
                                <td><input type="checkbox"></td>
                                <td><strong>旧マーケティング分析</strong></td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <span>田中 花子</span>
                                    </div>
                                </td>
                                <td><span class="badge badge-warning">非アクティブ</span></td>
                                <td>2</td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <div class="progress-bar" style="width: 100px;">
                                            <div class="progress-fill" style="width: 25%;"></div>
                                        </div>
                                        <span>2.5 GB</span>
                                    </div>
                                </td>
                                <td>2025/10/15 09:00</td>
                                <td>2025/06/01</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary">詳細</button>
                                    <button class="btn btn-sm btn-warning">アーカイブ</button>
                                </td>
                            </tr>
                            <tr>
                                <td><input type="checkbox"></td>
                                <td><strong>2024年度決算分析</strong></td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <span>山田 太郎</span>
                                    </div>
                                </td>
                                <td><span class="badge badge-neutral">アーカイブ済み</span></td>
                                <td>4</td>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <div class="progress-bar" style="width: 100px;">
                                            <div class="progress-fill" style="width: 60%;"></div>
                                        </div>
                                        <span>6.0 GB</span>
                                    </div>
                                </td>
                                <td>2025/03/31 18:00</td>
                                <td>2024/12/01</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary">詳細</button>
                                    <button class="btn btn-sm btn-primary">復元</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pagination mt-5 p-4">
                    <button class="pagination-btn" disabled>◀ 前へ</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">3</button>
                    <button class="pagination-btn">次へ ▶</button>
                </div>
            </div>
        </div>
    `,

    // 監査ログ（SA-012〜SA-016）
    'admin-audit-logs': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">監視・運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">監査ログ</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">監査ログ</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>📥</span> エクスポート
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">データ変更</button>
            <button class="tab">アクセスログ</button>
            <button class="tab">セキュリティ</button>
        </div>

        <!-- タブコンテンツ: データ変更 -->
        <div class="tab-content active">
            <div class="card mb-5">
                <div class="card-body">
                    <div class="search-bar">
                        <select class="form-select" style="width: 180px;">
                            <option value="">全てのユーザー</option>
                            <option value="1">管理者 太郎</option>
                            <option value="2">山田 太郎</option>
                        </select>
                        <select class="form-select" style="width: 150px;">
                            <option value="">全てのリソース</option>
                            <option value="PROJECT">PROJECT</option>
                            <option value="USER">USER</option>
                            <option value="SETTINGS">SETTINGS</option>
                        </select>
                        <input type="datetime-local" class="form-input" style="width: 200px;">
                        <input type="datetime-local" class="form-input" style="width: 200px;">
                        <button class="btn btn-primary">検索</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-body p-0">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>日時</th>
                                    <th>ユーザー</th>
                                    <th>アクション</th>
                                    <th>リソース</th>
                                    <th>変更フィールド</th>
                                    <th>重要度</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>2025/12/30 10:30:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-warning">UPDATE</span></td>
                                    <td>PROJECT / abc-123</td>
                                    <td>name, description</td>
                                    <td><span class="badge badge-success">INFO</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 10:25:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>管理者 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-success">CREATE</span></td>
                                    <td>USER / def-456</td>
                                    <td>-</td>
                                    <td><span class="badge badge-success">INFO</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 10:10:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>管理者 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-danger">DELETE</span></td>
                                    <td>PROJECT_FILE / ghi-789</td>
                                    <td>-</td>
                                    <td><span class="badge badge-success">INFO</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="pagination mt-5 p-4">
                        <button class="pagination-btn" disabled>◀ 前へ</button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">2</button>
                        <button class="pagination-btn">次へ ▶</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: アクセスログ -->
        <div class="tab-content">
            <div class="card mb-5">
                <div class="card-body">
                    <div class="search-bar">
                        <select class="form-select" style="width: 180px;">
                            <option value="">全てのユーザー</option>
                            <option value="1">管理者 太郎</option>
                            <option value="2">山田 太郎</option>
                        </select>
                        <select class="form-select" style="width: 150px;">
                            <option value="">全てのアクション</option>
                            <option value="LOGIN_SUCCESS">ログイン成功</option>
                            <option value="LOGOUT">ログアウト</option>
                        </select>
                        <input type="datetime-local" class="form-input" style="width: 200px;">
                        <input type="datetime-local" class="form-input" style="width: 200px;">
                        <button class="btn btn-primary">検索</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-body p-0">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>日時</th>
                                    <th>ユーザー</th>
                                    <th>アクション</th>
                                    <th>IPアドレス</th>
                                    <th>ユーザーエージェント</th>
                                    <th>重要度</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>2025/12/30 10:20:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-primary">LOGIN_SUCCESS</span></td>
                                    <td>192.168.1.1</td>
                                    <td>Chrome 120 / Windows</td>
                                    <td><span class="badge badge-success">INFO</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/30 09:00:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>管理者 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-primary">LOGIN_SUCCESS</span></td>
                                    <td>192.168.1.100</td>
                                    <td>Firefox 121 / Mac</td>
                                    <td><span class="badge badge-success">INFO</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2025/12/29 18:00:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>佐藤 次郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-secondary">LOGOUT</span></td>
                                    <td>192.168.1.50</td>
                                    <td>Edge 120 / Windows</td>
                                    <td><span class="badge badge-success">INFO</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="pagination mt-5 p-4">
                        <button class="pagination-btn" disabled>◀ 前へ</button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">2</button>
                        <button class="pagination-btn">次へ ▶</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: セキュリティ -->
        <div class="tab-content">
            <div class="card mb-5">
                <div class="card-body">
                    <div class="search-bar">
                        <select class="form-select" style="width: 180px;">
                            <option value="">全てのユーザー</option>
                            <option value="1">管理者 太郎</option>
                            <option value="2">山田 太郎</option>
                        </select>
                        <select class="form-select" style="width: 150px;">
                            <option value="">全ての重要度</option>
                            <option value="WARNING">WARNING</option>
                            <option value="CRITICAL">CRITICAL</option>
                        </select>
                        <input type="datetime-local" class="form-input" style="width: 200px;">
                        <input type="datetime-local" class="form-input" style="width: 200px;">
                        <button class="btn btn-primary">検索</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-body p-0">
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>日時</th>
                                    <th>ユーザー</th>
                                    <th>アクション</th>
                                    <th>IPアドレス</th>
                                    <th>詳細</th>
                                    <th>重要度</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="table-row-warning">
                                    <td>2025/12/30 10:15:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>不明なユーザー</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-danger">LOGIN_FAILED</span></td>
                                    <td>192.168.1.200</td>
                                    <td>試行回数: 3</td>
                                    <td><span class="badge badge-warning">WARNING</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr class="table-row-danger">
                                    <td>2025/12/29 22:30:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>不明なユーザー</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-danger">BRUTE_FORCE</span></td>
                                    <td>10.0.0.100</td>
                                    <td>試行回数: 10</td>
                                    <td><span class="badge badge-danger">CRITICAL</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                                <tr class="table-row-warning">
                                    <td>2025/12/29 15:00:00</td>
                                    <td>
                                        <div class="d-flex items-center gap-2">
                                            <span>👤</span>
                                            <span>山田 太郎</span>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-warning">PASSWORD_EXPIRED</span></td>
                                    <td>192.168.1.1</td>
                                    <td>パスワード有効期限切れ</td>
                                    <td><span class="badge badge-warning">WARNING</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary">詳細</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="pagination mt-5 p-4">
                        <button class="pagination-btn" disabled>◀ 前へ</button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">次へ ▶</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // システム設定（SA-017〜SA-021）
    'admin-settings': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム設定</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">システム設定</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="showToast('success', '保存しました', 'システム設定が更新されました。')">
                    <span>💾</span> 保存
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">一般設定</button>
            <button class="tab">セキュリティ</button>
            <button class="tab">メンテナンス</button>
        </div>

        <!-- タブコンテンツ: 一般設定 -->
        <div class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">一般設定</h3>
                </div>
                <div class="card-body">
                    <div class="form-group mb-4">
                        <label class="form-label">最大ファイルサイズ（MB）</label>
                        <input type="number" class="form-input" style="width: 150px;" value="100">
                        <div class="form-help">アップロード可能なファイルの最大サイズ</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">セッションタイムアウト（分）</label>
                        <input type="number" class="form-input" style="width: 150px;" value="60">
                        <div class="form-help">非アクティブ状態が続いた場合に自動ログアウトする時間</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: セキュリティ -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">セキュリティ設定</h3>
                </div>
                <div class="card-body">
                    <div class="form-group mb-4">
                        <label class="form-label">パスワード有効期限（日）</label>
                        <input type="number" class="form-input" style="width: 150px;" value="90">
                        <div class="form-help">0を設定すると無期限になります</div>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label">ログイン試行回数上限</label>
                        <input type="number" class="form-input" style="width: 150px;" value="5">
                        <div class="form-help">この回数を超えるとアカウントが一時ロックされます</div>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label d-flex items-center gap-2">
                            <input type="checkbox"> 2要素認証を必須にする
                        </label>
                        <div class="form-help">全ユーザーに2要素認証を要求します</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">IPホワイトリスト</label>
                        <textarea class="form-textarea" rows="3" placeholder="1行に1つのIPアドレスまたはCIDR形式で入力">192.168.1.0/24
10.0.0.0/8</textarea>
                        <div class="form-help">空の場合は制限なし。設定するとリストにあるIPからのみアクセス可能</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: メンテナンス -->
        <div class="tab-content">
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="card-title">メンテナンスモード</h3>
                </div>
                <div class="card-body">
                    <div class="form-group mb-4">
                        <label class="form-label d-flex items-center gap-2">
                            <input type="checkbox"> メンテナンスモードを有効化
                        </label>
                        <div class="form-help">有効化するとユーザーはシステムにアクセスできなくなります</div>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label">メンテナンスメッセージ</label>
                        <textarea class="form-textarea" rows="3" placeholder="ユーザーに表示するメッセージ">システムメンテナンス中です。しばらくお待ちください。</textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label d-flex items-center gap-2">
                            <input type="checkbox" checked> 管理者のアクセスを許可
                        </label>
                    </div>
                </div>
            </div>

            <!-- 設定履歴 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近の変更</h3>
                </div>
                <div class="card-body p-0">
                    <div class="activity-list">
                        <div class="activity-item">
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>max_file_size_mb</strong> を 50 → 100 に変更
                                </div>
                                <div class="activity-time">管理者 太郎 • 2時間前</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>ai_suggestions</strong> を有効化
                                </div>
                                <div class="activity-time">管理者 太郎 • 1日前</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // システム統計ダッシュボード（SA-022〜SA-026）
    'admin-statistics': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">監視・運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム統計</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">システム統計ダッシュボード</h1>
            <div class="page-actions">
                <select class="form-select" style="width: 150px;">
                    <option value="day">今日</option>
                    <option value="week" selected>今週</option>
                    <option value="month">今月</option>
                    <option value="year">今年</option>
                </select>
            </div>
        </div>

        <!-- 統計カード -->
        <div class="stats-grid mb-5">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-content">
                    <div class="stat-value">500</div>
                    <div class="stat-label">総ユーザー数</div>
                    <div class="stat-change positive">+15 今月</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-value">120</div>
                    <div class="stat-label">アクティブユーザー（今日）</div>
                    <div class="stat-change positive">+5% 前日比</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-content">
                    <div class="stat-value">150</div>
                    <div class="stat-label">総プロジェクト数</div>
                    <div class="stat-change positive">+8 今月</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-content">
                    <div class="stat-value">100.0 GB</div>
                    <div class="stat-label">総ストレージ使用量</div>
                    <div class="stat-change">45.5% 使用中</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔄</div>
                <div class="stat-content">
                    <div class="stat-value">15,000</div>
                    <div class="stat-label">APIリクエスト（今日）</div>
                    <div class="stat-change">平均 150ms</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚠️</div>
                <div class="stat-content">
                    <div class="stat-value">0.5%</div>
                    <div class="stat-label">エラー率（今日）</div>
                    <div class="stat-change positive">-0.2% 前日比</div>
                </div>
            </div>
        </div>

        <div class="charts-grid">
            <!-- アクティブユーザー推移 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">アクティブユーザー推移</h3>
                </div>
                <div class="card-body">
                    <div class="chart-placeholder">
                        <div class="chart-bars">
                            <div class="chart-bar" style="height: 60%;"><span>月</span></div>
                            <div class="chart-bar" style="height: 75%;"><span>火</span></div>
                            <div class="chart-bar" style="height: 85%;"><span>水</span></div>
                            <div class="chart-bar" style="height: 70%;"><span>木</span></div>
                            <div class="chart-bar" style="height: 90%;"><span>金</span></div>
                            <div class="chart-bar" style="height: 40%;"><span>土</span></div>
                            <div class="chart-bar active" style="height: 80%;"><span>日</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- APIリクエスト推移 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">APIリクエスト推移</h3>
                </div>
                <div class="card-body">
                    <div class="chart-placeholder">
                        <div class="chart-bars">
                            <div class="chart-bar" style="height: 50%;"><span>月</span></div>
                            <div class="chart-bar" style="height: 65%;"><span>火</span></div>
                            <div class="chart-bar" style="height: 80%;"><span>水</span></div>
                            <div class="chart-bar" style="height: 75%;"><span>木</span></div>
                            <div class="chart-bar" style="height: 95%;"><span>金</span></div>
                            <div class="chart-bar" style="height: 30%;"><span>土</span></div>
                            <div class="chart-bar active" style="height: 70%;"><span>日</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ストレージ使用量推移 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ストレージ使用量推移</h3>
                </div>
                <div class="card-body">
                    <div class="chart-placeholder">
                        <div class="chart-line">
                            <div class="chart-area" style="clip-path: polygon(0 80%, 15% 75%, 30% 70%, 45% 65%, 60% 60%, 75% 55%, 90% 50%, 100% 45%, 100% 100%, 0 100%);"></div>
                        </div>
                        <div class="chart-labels">
                            <span>1週前</span>
                            <span>今日</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- エラー発生率推移 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">エラー発生率推移</h3>
                </div>
                <div class="card-body">
                    <div class="chart-placeholder">
                        <div class="chart-bars error-chart">
                            <div class="chart-bar" style="height: 15%;"><span>月</span></div>
                            <div class="chart-bar" style="height: 10%;"><span>火</span></div>
                            <div class="chart-bar" style="height: 25%;"><span>水</span></div>
                            <div class="chart-bar" style="height: 8%;"><span>木</span></div>
                            <div class="chart-bar" style="height: 12%;"><span>金</span></div>
                            <div class="chart-bar" style="height: 5%;"><span>土</span></div>
                            <div class="chart-bar active" style="height: 10%;"><span>日</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- アクティブなアラート -->
        <div class="card mt-5">
            <div class="card-header">
                <h3 class="card-title">アクティブなアラート</h3>
            </div>
            <div class="card-body">
                <div class="alert alert-warning mb-3">
                    <span class="alert-icon">⚠️</span>
                    <div class="alert-content">
                        <div class="alert-title">ストレージ使用量警告</div>
                        <div class="alert-text">ストレージ使用量が45%に達しました。80%を超えると警告が発生します。</div>
                    </div>
                    <div class="alert-time">2時間前</div>
                </div>
                <div class="alert alert-info">
                    <span class="alert-icon">ℹ️</span>
                    <div class="alert-content">
                        <div class="alert-title">定期バックアップ完了</div>
                        <div class="alert-text">本日のバックアップが正常に完了しました。</div>
                    </div>
                    <div class="alert-time">6時間前</div>
                </div>
            </div>
        </div>
    `,

    // 一括操作（SA-027〜SA-030）
    'admin-bulk-operations': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">一括操作</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">一括操作</h1>
        </div>

        <div class="alert alert-warning mb-5">
            <span class="alert-icon">⚠️</span>
            <div class="alert-content">
                <div class="alert-text">一括操作は取り消しできない場合があります。実行前に必ずプレビューで確認してください。</div>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">ユーザーインポート</button>
            <button class="tab">ユーザーエクスポート</button>
            <button class="tab">ユーザー無効化</button>
            <button class="tab">プロジェクトアーカイブ</button>
        </div>

        <!-- タブコンテンツ: ユーザーインポート -->
        <div class="tab-content active">
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="card-title">ユーザー一括インポート</h3>
                </div>
                <div class="card-body">
                    <p class="mb-4">CSVファイルからユーザーを一括登録します。</p>
                    <div class="form-group mb-4">
                        <label class="form-label">CSVファイルを選択</label>
                        <input type="file" class="form-input" accept=".csv">
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-secondary">テンプレートをダウンロード</button>
                        <button class="btn btn-primary">プレビュー</button>
                    </div>
                </div>
            </div>

            <!-- プレビュー結果 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">プレビュー結果</h3>
                    <span class="badge badge-info">5件</span>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th style="width: 40px;"></th>
                                <th>メールアドレス</th>
                                <th>氏名</th>
                                <th>ロール</th>
                                <th>ステータス</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><span class="text-success">✓</span></td>
                                <td>tanaka@example.com</td>
                                <td>田中 一郎</td>
                                <td>Viewer</td>
                                <td><span class="badge badge-success">新規登録</span></td>
                            </tr>
                            <tr>
                                <td><span class="text-success">✓</span></td>
                                <td>suzuki@example.com</td>
                                <td>鈴木 花子</td>
                                <td>Editor</td>
                                <td><span class="badge badge-success">新規登録</span></td>
                            </tr>
                            <tr>
                                <td><span class="text-warning">!</span></td>
                                <td>yamada@example.com</td>
                                <td>山田 太郎</td>
                                <td>Admin</td>
                                <td><span class="badge badge-warning">既存（スキップ）</span></td>
                            </tr>
                            <tr>
                                <td><span class="text-success">✓</span></td>
                                <td>sato@example.com</td>
                                <td>佐藤 次郎</td>
                                <td>Viewer</td>
                                <td><span class="badge badge-success">新規登録</span></td>
                            </tr>
                            <tr>
                                <td><span class="text-danger">✗</span></td>
                                <td>invalid-email</td>
                                <td>エラー 太郎</td>
                                <td>Viewer</td>
                                <td><span class="badge badge-danger">エラー: 無効なメール形式</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="card-footer d-flex justify-between items-center">
                    <div class="text-secondary">
                        新規登録: 3件 / スキップ: 1件 / エラー: 1件
                    </div>
                    <button class="btn btn-primary">インポート実行</button>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: ユーザーエクスポート -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ユーザー一括エクスポート</h3>
                </div>
                <div class="card-body">
                    <p class="mb-4">ユーザー情報をCSV/Excel形式でエクスポートします。</p>
                    <div class="form-group mb-4">
                        <label class="form-label">出力形式</label>
                        <select class="form-select">
                            <option value="csv">CSV</option>
                            <option value="xlsx">Excel</option>
                        </select>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label">フィルター条件</label>
                        <select class="form-select">
                            <option value="">全てのユーザー</option>
                            <option value="active">有効なユーザーのみ</option>
                            <option value="inactive">無効なユーザーのみ</option>
                        </select>
                    </div>
                    <button class="btn btn-primary">エクスポート</button>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: ユーザー無効化 -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ユーザー一括無効化</h3>
                </div>
                <div class="card-body">
                    <p class="mb-4">指定期間ログインしていないユーザーを一括で無効化します。</p>
                    <div class="form-group mb-4">
                        <label class="form-label">非アクティブ日数</label>
                        <input type="number" class="form-input" style="width: 150px;" value="90" min="30">
                        <div class="form-help">最終ログインからの経過日数</div>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-secondary">対象を確認</button>
                        <button class="btn btn-danger">一括無効化</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: プロジェクトアーカイブ -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">プロジェクト一括アーカイブ</h3>
                </div>
                <div class="card-body">
                    <p class="mb-4">指定期間更新のないプロジェクトを一括でアーカイブします。</p>
                    <div class="form-group mb-4">
                        <label class="form-label">非アクティブ日数</label>
                        <input type="number" class="form-input" style="width: 150px;" value="180" min="30">
                        <div class="form-help">最終更新からの経過日数</div>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-secondary">対象を確認</button>
                        <button class="btn btn-warning">一括アーカイブ</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // 通知管理（SA-031〜SA-034）
    'admin-notifications': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">通知管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">通知管理</h1>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">システムお知らせ</button>
            <button class="tab">通知テンプレート</button>
            <button class="tab">アラート設定</button>
        </div>

        <!-- タブコンテンツ: システムお知らせ -->
        <div class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">システムお知らせ</h3>
                    <button class="btn btn-primary">
                        <span>➕</span> 新規作成
                    </button>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>タイトル</th>
                                <th>種別</th>
                                <th>表示期間</th>
                                <th>対象</th>
                                <th>ステータス</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>システムメンテナンスのお知らせ</strong></td>
                                <td><span class="badge badge-warning">MAINTENANCE</span></td>
                                <td>2025/12/28 〜 2025/12/31</td>
                                <td><span class="badge badge-info">全員</span></td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>新機能リリースのお知らせ</strong></td>
                                <td><span class="badge badge-info">INFO</span></td>
                                <td>2025/12/20 〜 無期限</td>
                                <td><span class="badge badge-info">全員</span></td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>セキュリティアップデートのお知らせ</strong></td>
                                <td><span class="badge badge-danger">WARNING</span></td>
                                <td>2025/12/15 〜 2025/12/20</td>
                                <td><span class="badge badge-danger">ADMIN</span></td>
                                <td><span class="badge badge-neutral">終了</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: 通知テンプレート -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">通知テンプレート</h3>
                    <button class="btn btn-primary">
                        <span>➕</span> 新規作成
                    </button>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>テンプレート名</th>
                                <th>イベント種別</th>
                                <th>件名</th>
                                <th>ステータス</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>プロジェクト作成通知</strong></td>
                                <td><span class="badge badge-success">PROJECT_CREATED</span></td>
                                <td>【CAMP】新しいプロジェクト「{{project_name}}」が作成されました</td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>メンバー追加通知</strong></td>
                                <td><span class="badge badge-info">MEMBER_ADDED</span></td>
                                <td>【CAMP】プロジェクト「{{project_name}}」に追加されました</td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>セッション完了通知</strong></td>
                                <td><span class="badge badge-primary">SESSION_COMPLETED</span></td>
                                <td>【CAMP】分析セッション「{{session_name}}」が完了しました</td>
                                <td><span class="badge badge-success">有効</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: アラート設定 -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">アラート設定</h3>
                    <button class="btn btn-primary">
                        <span>➕</span> 新規作成
                    </button>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>アラート名</th>
                                <th>条件種別</th>
                                <th>閾値</th>
                                <th>通知先</th>
                                <th>ステータス</th>
                                <th>最終発火</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>エラー率アラート</strong></td>
                                <td><span class="badge badge-danger">ERROR_RATE</span></td>
                                <td>&gt; 5%</td>
                                <td>EMAIL</td>
                                <td>
                                    <label class="toggle">
                                        <input type="checkbox" checked>
                                        <span class="toggle-slider"></span>
                                    </label>
                                </td>
                                <td>2025/12/29 15:00</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>ストレージ使用量アラート</strong></td>
                                <td><span class="badge badge-warning">STORAGE_USAGE</span></td>
                                <td>&gt;= 80%</td>
                                <td>EMAIL, SLACK</td>
                                <td>
                                    <label class="toggle">
                                        <input type="checkbox" checked>
                                        <span class="toggle-slider"></span>
                                    </label>
                                </td>
                                <td>-</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>非アクティブユーザーアラート</strong></td>
                                <td><span class="badge badge-info">INACTIVE_USERS</span></td>
                                <td>&gt; 100人</td>
                                <td>EMAIL</td>
                                <td>
                                    <label class="toggle">
                                        <input type="checkbox">
                                        <span class="toggle-slider"></span>
                                    </label>
                                </td>
                                <td>-</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // セキュリティ管理（SA-035〜SA-036）
    'admin-security': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">セキュリティ管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">セキュリティ管理</h1>
        </div>

        <!-- 統計カード -->
        <div class="stats-grid mb-5">
            <div class="stat-card">
                <div class="stat-icon">🔐</div>
                <div class="stat-content">
                    <div class="stat-value">120</div>
                    <div class="stat-label">アクティブセッション数</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-value">85</div>
                    <div class="stat-label">本日のログイン数</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚠️</div>
                <div class="stat-content">
                    <div class="stat-value">3</div>
                    <div class="stat-label">疑わしいアクティビティ</div>
                </div>
            </div>
        </div>

        <div class="card mb-5">
            <div class="card-body">
                <div class="search-bar">
                    <input type="text" class="form-input search-input" placeholder="ユーザー名で検索...">
                    <input type="text" class="form-input" style="width: 180px;" placeholder="IPアドレス">
                    <input type="datetime-local" class="form-input" style="width: 200px;">
                    <input type="datetime-local" class="form-input" style="width: 200px;">
                    <button class="btn btn-primary">検索</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">アクティブセッション一覧</h3>
            </div>
            <div class="card-body p-0">
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ユーザー</th>
                                <th>IPアドレス</th>
                                <th>デバイス</th>
                                <th>ログイン日時</th>
                                <th>最終アクティビティ</th>
                                <th>ステータス</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <div>
                                            <div><strong>山田 太郎</strong></div>
                                            <div class="text-sm text-muted">yamada@example.com</div>
                                        </div>
                                    </div>
                                </td>
                                <td>192.168.1.100</td>
                                <td>
                                    <div>Windows 11</div>
                                    <div class="text-sm text-muted">Chrome 120</div>
                                </td>
                                <td>2025/12/30 08:00</td>
                                <td>2025/12/30 10:30</td>
                                <td><span class="badge badge-success">アクティブ</span></td>
                                <td>
                                    <button class="btn btn-sm btn-danger">強制ログアウト</button>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <div>
                                            <div><strong>佐藤 次郎</strong></div>
                                            <div class="text-sm text-muted">sato@example.com</div>
                                        </div>
                                    </div>
                                </td>
                                <td>192.168.1.101</td>
                                <td>
                                    <div>macOS 14</div>
                                    <div class="text-sm text-muted">Safari 17</div>
                                </td>
                                <td>2025/12/30 09:15</td>
                                <td>2025/12/30 10:28</td>
                                <td><span class="badge badge-success">アクティブ</span></td>
                                <td>
                                    <button class="btn btn-sm btn-danger">強制ログアウト</button>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <div>
                                            <div><strong>田中 花子</strong></div>
                                            <div class="text-sm text-muted">tanaka@example.com</div>
                                        </div>
                                    </div>
                                </td>
                                <td>10.0.0.50</td>
                                <td>
                                    <div>Windows 10</div>
                                    <div class="text-sm text-muted">Edge 120</div>
                                </td>
                                <td>2025/12/30 07:30</td>
                                <td>2025/12/30 09:00</td>
                                <td><span class="badge badge-warning">アイドル</span></td>
                                <td>
                                    <button class="btn btn-sm btn-danger">強制ログアウト</button>
                                </td>
                            </tr>
                            <tr class="table-row-warning">
                                <td>
                                    <div class="d-flex items-center gap-2">
                                        <span>👤</span>
                                        <div>
                                            <div><strong>管理者 太郎</strong></div>
                                            <div class="text-sm text-muted">admin@example.com</div>
                                        </div>
                                    </div>
                                </td>
                                <td>203.0.113.50</td>
                                <td>
                                    <div>Linux</div>
                                    <div class="text-sm text-muted">Firefox 121</div>
                                </td>
                                <td>2025/12/30 10:15</td>
                                <td>2025/12/30 10:20</td>
                                <td><span class="badge badge-danger">要確認</span></td>
                                <td>
                                    <button class="btn btn-sm btn-danger">強制ログアウト</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pagination mt-5 p-4">
                    <button class="pagination-btn" disabled>◀ 前へ</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">3</button>
                    <button class="pagination-btn">次へ ▶</button>
                </div>
            </div>
        </div>
    `,

    // データ管理（SA-037〜SA-040）
    'admin-data-management': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">データ管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">データ管理</h1>
        </div>

        <div class="tabs mb-5">
            <button class="tab active">データクリーンアップ</button>
            <button class="tab">孤立ファイル</button>
            <button class="tab">保持ポリシー</button>
            <button class="tab">マスタインポート</button>
        </div>

        <!-- タブコンテンツ: データクリーンアップ -->
        <div class="tab-content active">
            <div class="data-management-grid">
                <!-- データクリーンアップ設定 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">クリーンアップ設定</h3>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-warning mb-4">
                            <span class="alert-icon">⚠️</span>
                            <div class="alert-content">
                                <div class="alert-text">削除されたデータは復元できません。実行前に必ずプレビューで確認してください。</div>
                            </div>
                        </div>

                        <div class="form-group mb-4">
                            <label class="form-label">削除対象</label>
                            <div class="checkbox-group">
                                <label class="d-flex items-center gap-2">
                                    <input type="checkbox" checked> 操作履歴（activity_logs）
                                </label>
                                <label class="d-flex items-center gap-2">
                                    <input type="checkbox"> 監査ログ（audit_logs）
                                </label>
                                <label class="d-flex items-center gap-2">
                                    <input type="checkbox" checked> 削除済みプロジェクト（deleted_projects）
                                </label>
                                <label class="d-flex items-center gap-2">
                                    <input type="checkbox"> セッションログ（session_logs）
                                </label>
                            </div>
                        </div>

                        <div class="form-group mb-4">
                            <label class="form-label">保持期間（日）</label>
                            <input type="number" class="form-input" style="width: 150px;" value="90" min="30">
                            <div class="form-help">この日数より古いデータが削除対象になります</div>
                        </div>

                        <div class="d-flex gap-2">
                            <button class="btn btn-secondary">プレビュー</button>
                            <button class="btn btn-danger">削除実行</button>
                        </div>
                    </div>
                </div>

                <!-- プレビュー結果 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">プレビュー結果</h3>
                    </div>
                    <div class="card-body p-0">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>対象種別</th>
                                    <th>レコード数</th>
                                    <th>推定サイズ</th>
                                    <th>最古のレコード</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>操作履歴</td>
                                    <td>15,000件</td>
                                    <td>50.0 MB</td>
                                    <td>2025/06/01</td>
                                </tr>
                                <tr>
                                    <td>削除済みプロジェクト</td>
                                    <td>5件</td>
                                    <td>100.0 MB</td>
                                    <td>2025/08/15</td>
                                </tr>
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td><strong>合計</strong></td>
                                    <td><strong>15,005件</strong></td>
                                    <td><strong>150.0 MB</strong></td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: 孤立ファイル -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">孤立ファイル</h3>
                    <div class="d-flex items-center gap-2">
                        <span class="text-muted">合計: 6.0 MB</span>
                        <button class="btn btn-danger btn-sm">選択項目を削除</button>
                    </div>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox"></th>
                                <th>ファイル名</th>
                                <th>サイズ</th>
                                <th>作成日</th>
                                <th>最終アクセス</th>
                                <th>元プロジェクト</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><input type="checkbox"></td>
                                <td>old_data_2024.csv</td>
                                <td>5.0 MB</td>
                                <td>2025/06/15</td>
                                <td>2025/08/01</td>
                                <td><span class="text-muted">削除済みプロジェクト</span></td>
                            </tr>
                            <tr>
                                <td><input type="checkbox"></td>
                                <td>temp_upload_abc123.xlsx</td>
                                <td>1.0 MB</td>
                                <td>2025/11/20</td>
                                <td>-</td>
                                <td><span class="text-muted">-</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: 保持ポリシー -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">データ保持ポリシー</h3>
                    <button class="btn btn-primary" onclick="showToast('success', '保存しました', 'データ保持ポリシーが更新されました。')">
                        <span>💾</span> 保存
                    </button>
                </div>
                <div class="card-body">
                    <div class="policy-grid">
                        <div class="form-group">
                            <label class="form-label">操作履歴保持期間（日）</label>
                            <input type="number" class="form-input" style="width: 150px;" value="90">
                        </div>
                        <div class="form-group">
                            <label class="form-label">監査ログ保持期間（日）</label>
                            <input type="number" class="form-input" style="width: 150px;" value="365">
                        </div>
                        <div class="form-group">
                            <label class="form-label">削除プロジェクト保持期間（日）</label>
                            <input type="number" class="form-input" style="width: 150px;" value="30">
                        </div>
                        <div class="form-group">
                            <label class="form-label">セッションログ保持期間（日）</label>
                            <input type="number" class="form-input" style="width: 150px;" value="30">
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- タブコンテンツ: マスタインポート -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">マスタデータインポート</h3>
                </div>
                <div class="card-body">
                    <div class="form-group mb-4">
                        <label class="form-label">インポート対象</label>
                        <select class="form-select" style="width: 300px;">
                            <option value="">選択してください</option>
                            <option value="users">ユーザーマスタ</option>
                            <option value="categories">カテゴリマスタ</option>
                            <option value="issues">課題マスタ</option>
                            <option value="verifications">検証カテゴリマスタ</option>
                        </select>
                    </div>

                    <div class="form-group mb-4">
                        <label class="form-label">ファイル選択</label>
                        <div class="file-upload-area">
                            <div class="file-upload-icon">📁</div>
                            <div class="file-upload-text">
                                CSVファイルをドラッグ＆ドロップ<br>
                                または<button class="btn btn-link">ファイルを選択</button>
                            </div>
                        </div>
                        <div class="form-help">対応形式: CSV（UTF-8）</div>
                    </div>

                    <div class="d-flex gap-2">
                        <button class="btn btn-secondary">テンプレートダウンロード</button>
                        <button class="btn btn-primary" disabled>インポート実行</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // サポートツール（SA-041〜SA-043）
    'admin-support-tools': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">システム運用</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">サポートツール</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">サポートツール</h1>
        </div>

        <!-- タブナビゲーション -->
        <div class="tabs mb-5">
            <button class="tab active">ユーザー代行</button>
            <button class="tab">デバッグ</button>
            <button class="tab">ヘルスチェック</button>
        </div>

        <!-- ユーザー代行タブ -->
        <div class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ユーザー代行操作</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-warning mb-4">
                        <span class="alert-icon">⚠️</span>
                        <div class="alert-content">
                            <div class="alert-text">ユーザー代行操作は監査ログに記録されます。サポート目的以外での使用は禁止されています。</div>
                        </div>
                    </div>

                    <div class="form-group mb-4">
                        <label class="form-label">対象ユーザー</label>
                        <input type="text" class="form-input" placeholder="ユーザー名またはメールアドレスで検索...">
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label">代行理由 <span class="required">*</span></label>
                        <textarea class="form-textarea" rows="3" placeholder="代行操作の理由を入力してください（必須）"></textarea>
                    </div>
                    <button class="btn btn-primary">代行開始</button>
                </div>
            </div>

            <!-- 代行操作履歴 -->
            <div class="card mt-5">
                <div class="card-header">
                    <h3 class="card-title">代行操作履歴</h3>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>日時</th>
                                <th>管理者</th>
                                <th>対象ユーザー</th>
                                <th>理由</th>
                                <th>操作時間</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>2025/12/30 09:00</td>
                                <td>管理者 太郎</td>
                                <td>山田 太郎</td>
                                <td>パスワードリセット対応</td>
                                <td>5分</td>
                            </tr>
                            <tr>
                                <td>2025/12/28 14:30</td>
                                <td>管理者 太郎</td>
                                <td>鈴木 花子</td>
                                <td>プロジェクト権限設定サポート</td>
                                <td>12分</td>
                            </tr>
                            <tr>
                                <td>2025/12/25 10:15</td>
                                <td>管理者 次郎</td>
                                <td>田中 一郎</td>
                                <td>ファイルアップロードエラー調査</td>
                                <td>8分</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- デバッグタブ -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">デバッグモード設定</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-info mb-4">
                        <span class="alert-icon">ℹ️</span>
                        <div class="alert-content">
                            <div class="alert-text">デバッグモードを有効にすると、詳細なログが出力されます。パフォーマンスに影響する可能性があるため、調査完了後は必ず無効化してください。</div>
                        </div>
                    </div>

                    <div class="form-group mb-4">
                        <label class="form-label">現在のステータス</label>
                        <div>
                            <span class="badge badge-neutral badge-lg">OFF</span>
                        </div>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label">ログレベル</label>
                        <select class="form-select" style="width: 200px;">
                            <option value="DEBUG">DEBUG</option>
                            <option value="INFO" selected>INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                        </select>
                    </div>
                    <div class="form-group mb-4">
                        <label class="form-label">自動無効化（分）</label>
                        <input type="number" class="form-input" style="width: 150px;" value="30">
                        <div class="form-hint">指定時間後に自動的にデバッグモードを無効化します</div>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-warning">デバッグ有効化</button>
                        <button class="btn btn-secondary" disabled>デバッグ無効化</button>
                    </div>
                </div>
            </div>

            <!-- デバッグ操作履歴 -->
            <div class="card mt-5">
                <div class="card-header">
                    <h3 class="card-title">デバッグ操作履歴</h3>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>日時</th>
                                <th>管理者</th>
                                <th>操作</th>
                                <th>ログレベル</th>
                                <th>継続時間</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>2025/12/29 15:30</td>
                                <td>管理者 太郎</td>
                                <td><span class="badge badge-warning">有効化</span></td>
                                <td>DEBUG</td>
                                <td>25分</td>
                            </tr>
                            <tr>
                                <td>2025/12/27 11:00</td>
                                <td>管理者 次郎</td>
                                <td><span class="badge badge-warning">有効化</span></td>
                                <td>INFO</td>
                                <td>15分</td>
                            </tr>
                            <tr>
                                <td>2025/12/20 09:45</td>
                                <td>管理者 太郎</td>
                                <td><span class="badge badge-warning">有効化</span></td>
                                <td>DEBUG</td>
                                <td>30分（自動終了）</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ヘルスチェックタブ -->
        <div class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">システムヘルスチェック</h3>
                    <button class="btn btn-primary btn-sm" onclick="showToast('success', 'ヘルスチェック完了', '全てのシステムは正常に動作しています。')">
                        <span>🔄</span> 実行
                    </button>
                </div>
                <div class="card-body">
                    <div class="mb-4">
                        <span class="text-muted">最終実行: 2025/12/30 10:00</span>
                    </div>
                    <div class="health-check-results">
                        <div class="health-check-item">
                            <div class="health-check-status success">✅</div>
                            <div class="health-check-info">
                                <div class="health-check-name">データベース接続</div>
                                <div class="health-check-detail">応答時間: 5ms • 接続プール: 10/20</div>
                            </div>
                        </div>
                        <div class="health-check-item">
                            <div class="health-check-status success">✅</div>
                            <div class="health-check-info">
                                <div class="health-check-name">キャッシュ（Redis）</div>
                                <div class="health-check-detail">応答時間: 2ms • メモリ使用率: 45%</div>
                            </div>
                        </div>
                        <div class="health-check-item">
                            <div class="health-check-status success">✅</div>
                            <div class="health-check-info">
                                <div class="health-check-name">ストレージ（Azure Blob）</div>
                                <div class="health-check-detail">応答時間: 50ms • 空き容量: 500 GB</div>
                            </div>
                        </div>
                        <div class="health-check-item">
                            <div class="health-check-status success">✅</div>
                            <div class="health-check-info">
                                <div class="health-check-name">外部API（Azure AD）</div>
                                <div class="health-check-detail">応答時間: 100ms</div>
                            </div>
                        </div>
                        <div class="health-check-item">
                            <div class="health-check-status success">✅</div>
                            <div class="health-check-info">
                                <div class="health-check-name">外部API（OpenAI）</div>
                                <div class="health-check-detail">応答時間: 250ms</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ヘルスチェック履歴 -->
            <div class="card mt-5">
                <div class="card-header">
                    <h3 class="card-title">ヘルスチェック履歴</h3>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>日時</th>
                                <th>実行者</th>
                                <th>結果</th>
                                <th>詳細</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>2025/12/30 10:00</td>
                                <td>管理者 太郎</td>
                                <td><span class="badge badge-success">正常</span></td>
                                <td>全5項目 OK</td>
                            </tr>
                            <tr>
                                <td>2025/12/29 14:00</td>
                                <td>管理者 太郎</td>
                                <td><span class="badge badge-success">正常</span></td>
                                <td>全5項目 OK</td>
                            </tr>
                            <tr>
                                <td>2025/12/28 09:00</td>
                                <td>システム（自動）</td>
                                <td><span class="badge badge-warning">警告</span></td>
                                <td>OpenAI API 応答遅延（1200ms）</td>
                            </tr>
                            <tr>
                                <td>2025/12/27 09:00</td>
                                <td>システム（自動）</td>
                                <td><span class="badge badge-success">正常</span></td>
                                <td>全5項目 OK</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,
};
