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
                <!-- 基本情報 -->
                <div class="card mb-5">
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

                <!-- プロンプト設定 -->
                <div class="card mb-5">
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

                <!-- 初期メッセージ設定 -->
                <div class="card mb-5">
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

                <!-- ダミーデータ設定 -->
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
};
