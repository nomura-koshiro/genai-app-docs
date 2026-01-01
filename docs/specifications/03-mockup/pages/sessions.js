// ========================================
// Analysis Session Pages
// ========================================

const sessionPages = {
    // 分析セッション一覧
    sessions: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上分析プロジェクト</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">分析セッション</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">分析セッション一覧</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="navigateTo('session-new')">
                    <span>➕</span> 新規セッション
                </button>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="search-bar">
                    <input type="text" class="form-input search-input" placeholder="セッション名で検索...">
                    <select class="form-select" style="width: 150px;">
                        <option value="">全ての課題</option>
                        <option value="1">売上予測</option>
                        <option value="2">コスト分析</option>
                    </select>
                    <button class="btn btn-secondary">検索</button>
                </div>

                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>セッション名</th>
                                <th>課題</th>
                                <th>入力ファイル</th>
                                <th>スナップショット</th>
                                <th>作成者</th>
                                <th>更新日時</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr onclick="navigateTo('analysis')">
                                <td><strong>Q4売上分析</strong></td>
                                <td>売上予測</td>
                                <td>sales_2025q4.xlsx</td>
                                <td>5</td>
                                <td>山田 太郎</td>
                                <td>2025/12/25 10:30</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-primary">開く</button>
                                    <button class="btn btn-sm btn-secondary">複製</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>月次レポート分析</strong></td>
                                <td>コスト分析</td>
                                <td>monthly_report.csv</td>
                                <td>3</td>
                                <td>鈴木 花子</td>
                                <td>2025/12/24 15:00</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-primary">開く</button>
                                    <button class="btn btn-sm btn-secondary">複製</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // 新規セッション作成
    'session-new': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#sessions">分析セッション</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">新規作成</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">新規セッション作成</h1>
        </div>

        <div class="session-new-grid">
            <!-- メインフォーム -->
            <div class="session-new-main">
                <!-- STEP 1: 分析テーマ選択 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">STEP 1: 分析テーマ選択</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group mb-4">
                            <label class="form-label">
                                検証カテゴリ <span class="required">*</span>
                            </label>
                            <div class="category-cards">
                                <div class="category-card selected">
                                    <div class="category-card-icon">📈</div>
                                    <div class="category-card-content">
                                        <div class="category-card-title">時系列分析</div>
                                        <div class="category-card-desc">トレンド、季節性、予測分析</div>
                                    </div>
                                </div>
                                <div class="category-card">
                                    <div class="category-card-icon">📊</div>
                                    <div class="category-card-content">
                                        <div class="category-card-title">比較分析</div>
                                        <div class="category-card-desc">グループ比較、A/Bテスト</div>
                                    </div>
                                </div>
                                <div class="category-card">
                                    <div class="category-card-icon">🔍</div>
                                    <div class="category-card-content">
                                        <div class="category-card-title">相関分析</div>
                                        <div class="category-card-desc">因果関係、相関係数分析</div>
                                    </div>
                                </div>
                                <div class="category-card">
                                    <div class="category-card-icon">👥</div>
                                    <div class="category-card-content">
                                        <div class="category-card-title">セグメント分析</div>
                                        <div class="category-card-desc">顧客分類、クラスタリング</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label">
                                分析課題 <span class="required">*</span>
                            </label>
                            <select class="form-select">
                                <option value="">課題を選択してください...</option>
                                <option value="1" selected>売上予測 - 時系列分析による売上予測</option>
                                <option value="2">需要予測 - 商品別需要予測</option>
                                <option value="3">トレンド分析 - 長期的なトレンドの把握</option>
                            </select>
                            <div class="form-help">選択したカテゴリに関連する課題が表示されます</div>
                        </div>
                    </div>
                </div>

                <!-- STEP 2: データ準備 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">STEP 2: データ準備</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group mb-4">
                            <label class="form-label">
                                入力ファイル <span class="required">*</span>
                            </label>
                            <select class="form-select">
                                <option value="">ファイルを選択してください...</option>
                                <option value="1" selected>sales_2025q4.xlsx (アップロード: 2025/12/20)</option>
                                <option value="2">monthly_report.csv (アップロード: 2025/12/18)</option>
                                <option value="3">customer_data.xlsx (アップロード: 2025/12/15)</option>
                            </select>
                        </div>

                        <div class="form-group mb-4">
                            <label class="form-label">
                                対象シート <span class="required">*</span>
                            </label>
                            <select class="form-select">
                                <option value="">シートを選択してください...</option>
                                <option value="1" selected>Sheet1 - 売上データ (15,230行)</option>
                                <option value="2">Sheet2 - 商品マスタ (1,200行)</option>
                                <option value="3">Sheet3 - 顧客データ (8,500行)</option>
                            </select>
                        </div>

                        <div class="divider"></div>

                        <div class="form-group mb-4">
                            <label class="form-label">
                                軸の設定 <span class="required">*</span>
                            </label>
                            <div class="form-help mb-3">分析に使用する軸（次元）を設定してください</div>

                            <div class="axis-settings">
                                <div class="axis-setting-row">
                                    <div class="axis-setting-label">
                                        <span class="axis-icon">📅</span>
                                        時間軸
                                    </div>
                                    <select class="form-select">
                                        <option value="">列を選択...</option>
                                        <option value="date" selected>日付 (date)</option>
                                        <option value="month">月 (month)</option>
                                        <option value="year">年 (year)</option>
                                    </select>
                                </div>
                                <div class="axis-setting-row">
                                    <div class="axis-setting-label">
                                        <span class="axis-icon">📊</span>
                                        分析対象値
                                    </div>
                                    <select class="form-select">
                                        <option value="">列を選択...</option>
                                        <option value="sales" selected>売上金額 (sales_amount)</option>
                                        <option value="quantity">販売数量 (quantity)</option>
                                        <option value="profit">利益 (profit)</option>
                                    </select>
                                </div>
                                <div class="axis-setting-row">
                                    <div class="axis-setting-label">
                                        <span class="axis-icon">🏷️</span>
                                        グループ化（任意）
                                    </div>
                                    <select class="form-select">
                                        <option value="" selected>なし</option>
                                        <option value="category">カテゴリ (category)</option>
                                        <option value="region">地域 (region)</option>
                                        <option value="product">商品 (product_name)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- STEP 3: 確認 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">STEP 3: 確認</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group mb-4">
                            <label class="form-label">セッション名（オプション）</label>
                            <input type="text" class="form-input" placeholder="セッション名を入力（空白の場合は自動生成）" value="Q4売上予測分析">
                        </div>

                        <div class="confirm-summary">
                            <div class="confirm-summary-title">設定内容</div>
                            <div class="confirm-summary-grid">
                                <div class="confirm-item">
                                    <div class="confirm-item-label">検証カテゴリ</div>
                                    <div class="confirm-item-value">時系列分析</div>
                                </div>
                                <div class="confirm-item">
                                    <div class="confirm-item-label">分析課題</div>
                                    <div class="confirm-item-value">売上予測</div>
                                </div>
                                <div class="confirm-item">
                                    <div class="confirm-item-label">入力ファイル</div>
                                    <div class="confirm-item-value">sales_2025q4.xlsx</div>
                                </div>
                                <div class="confirm-item">
                                    <div class="confirm-item-label">対象シート</div>
                                    <div class="confirm-item-value">Sheet1 - 売上データ</div>
                                </div>
                                <div class="confirm-item">
                                    <div class="confirm-item-label">時間軸</div>
                                    <div class="confirm-item-value">日付 (date)</div>
                                </div>
                                <div class="confirm-item">
                                    <div class="confirm-item-label">分析対象値</div>
                                    <div class="confirm-item-value">売上金額 (sales_amount)</div>
                                </div>
                            </div>
                        </div>

                        <div class="d-flex gap-3 justify-end mt-5">
                            <button type="button" class="btn btn-secondary" onclick="navigateTo('sessions')">キャンセル</button>
                            <button type="button" class="btn btn-primary" onclick="navigateTo('analysis')">
                                <span>🚀</span> 分析を開始
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- サイドバー -->
            <div class="session-new-sidebar">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">選択した課題について</h3>
                    </div>
                    <div class="card-body">
                        <h4 class="text-base font-semibold mb-2">売上予測</h4>
                        <p class="text-sm text-muted mb-3">
                            時系列データから将来の売上を予測します。季節性やトレンドを考慮した高精度な予測が可能です。
                        </p>
                        <div class="divider"></div>
                        <div class="text-sm">
                            <div class="mb-2"><strong>推奨データ:</strong></div>
                            <ul class="ml-4">
                                <li>日次または月次の売上データ</li>
                                <li>最低6ヶ月以上のデータ</li>
                                <li>日付と金額を含む列</li>
                            </ul>
                        </div>
                        <div class="divider"></div>
                        <div class="text-sm">
                            <div class="mb-2"><strong>分析でできること:</strong></div>
                            <ul class="ml-4">
                                <li>将来の売上予測</li>
                                <li>季節性パターンの検出</li>
                                <li>トレンド分析</li>
                                <li>予測精度の評価</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // 分析画面
    analysis: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#sessions">分析セッション</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">Q4売上分析</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">Q4売上分析</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="navigateTo('snapshots')">
                    <span>📸</span> スナップショット履歴
                </button>
                <button class="btn btn-primary">
                    <span>💾</span> スナップショット保存
                </button>
            </div>
        </div>

        <div class="alert alert-info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-title">現在のスナップショット: #5</div>
                <div class="alert-text">入力ファイル: sales_2025q4.xlsx | 課題: 売上予測</div>
            </div>
        </div>

        <div class="analysis-layout">
            <div class="analysis-main">
                <div class="chat-container">
                    <div class="chat-messages">
                        <div class="chat-message">
                            <div class="chat-avatar">🤖</div>
                            <div class="chat-bubble">
                                こんにちは！売上予測分析を開始します。<br>
                                アップロードされたデータを確認しました。2025年Q4の売上データですね。<br>
                                どのような分析を行いますか？
                            </div>
                        </div>
                        <div class="chat-message user">
                            <div class="chat-avatar">👤</div>
                            <div class="chat-bubble">
                                まず、月別の売上推移を見せてください。
                            </div>
                        </div>
                        <div class="chat-message">
                            <div class="chat-avatar">🤖</div>
                            <div class="chat-bubble">
                                承知しました。月別売上推移のグラフを作成しました。<br>
                                10月: ¥12,500,000<br>
                                11月: ¥13,200,000<br>
                                12月: ¥15,800,000（予測）<br><br>
                                12月は前月比19.7%増の見込みです。詳細な分析を続けますか？
                            </div>
                        </div>
                        <div class="chat-message user">
                            <div class="chat-avatar">👤</div>
                            <div class="chat-bubble">
                                カテゴリ別の内訳も分析してください。
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-area">
                        <input type="text" class="chat-input" placeholder="メッセージを入力...">
                        <button class="chat-send-btn">送信</button>
                    </div>
                </div>
            </div>

            <div class="analysis-sidebar">
                <div class="steps-panel">
                    <div class="steps-header">
                        ステップ一覧
                    </div>
                    <div class="steps-list">
                        <div class="step-item completed">
                            <div class="step-number">1</div>
                            <div class="step-info">
                                <div class="step-title">データ読み込み</div>
                                <div class="step-meta">完了 - 10:30</div>
                            </div>
                        </div>
                        <div class="step-item completed">
                            <div class="step-number">2</div>
                            <div class="step-info">
                                <div class="step-title">月別売上集計</div>
                                <div class="step-meta">完了 - 10:32</div>
                            </div>
                        </div>
                        <div class="step-item completed">
                            <div class="step-number">3</div>
                            <div class="step-info">
                                <div class="step-title">グラフ生成</div>
                                <div class="step-meta">完了 - 10:33</div>
                            </div>
                        </div>
                        <div class="step-item" style="background-color: var(--color-primary-50);">
                            <div class="step-number">4</div>
                            <div class="step-info">
                                <div class="step-title">カテゴリ別分析</div>
                                <div class="step-meta">実行中...</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-5">
                    <div class="card-header">
                        <h3 class="card-title">ファイル情報</h3>
                    </div>
                    <div class="card-body text-sm">
                        <p class="mb-2"><strong>ファイル名:</strong> sales_2025q4.xlsx</p>
                        <p class="mb-2"><strong>サイズ:</strong> 2.4 MB</p>
                        <p class="mb-2"><strong>行数:</strong> 15,230</p>
                        <p><strong>列数:</strong> 12</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    // スナップショット履歴
    snapshots: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#sessions">分析セッション</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#analysis">Q4売上分析</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">スナップショット履歴</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">スナップショット履歴</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="navigateTo('analysis')">
                    分析画面に戻る
                </button>
            </div>
        </div>

        <div class="alert alert-warning">
            <span class="alert-icon">⚠️</span>
            <div class="alert-content">
                <div class="alert-text">過去のスナップショットに戻ると、そこから新しい分岐が作成されます。</div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="snapshot-timeline">
                    <div class="snapshot-item current">
                        <div class="snapshot-header">
                            <span class="snapshot-title">スナップショット #5（現在）</span>
                            <span class="snapshot-date">2025/12/25 10:45</span>
                        </div>
                        <p class="text-sm mb-2">カテゴリ別分析を実行中</p>
                        <div>
                            <span class="badge badge-success">現在地</span>
                        </div>
                    </div>

                    <div class="snapshot-item">
                        <div class="snapshot-header">
                            <span class="snapshot-title">スナップショット #4</span>
                            <span class="snapshot-date">2025/12/25 10:33</span>
                        </div>
                        <p class="text-sm mb-2">月別売上グラフ生成完了</p>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-primary">この時点に戻る</button>
                            <button class="btn btn-sm btn-secondary">詳細を見る</button>
                        </div>
                    </div>

                    <div class="snapshot-item">
                        <div class="snapshot-header">
                            <span class="snapshot-title">スナップショット #3</span>
                            <span class="snapshot-date">2025/12/25 10:32</span>
                        </div>
                        <p class="text-sm mb-2">月別売上集計完了</p>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-primary">この時点に戻る</button>
                            <button class="btn btn-sm btn-secondary">詳細を見る</button>
                        </div>
                    </div>

                    <div class="snapshot-item">
                        <div class="snapshot-header">
                            <span class="snapshot-title">スナップショット #2</span>
                            <span class="snapshot-date">2025/12/25 10:31</span>
                        </div>
                        <p class="text-sm mb-2">データ読み込み完了</p>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-primary">この時点に戻る</button>
                            <button class="btn btn-sm btn-secondary">詳細を見る</button>
                        </div>
                    </div>

                    <div class="snapshot-item">
                        <div class="snapshot-header">
                            <span class="snapshot-title">スナップショット #1（初期）</span>
                            <span class="snapshot-date">2025/12/25 10:30</span>
                        </div>
                        <p class="text-sm mb-2">セッション開始</p>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-primary">この時点に戻る</button>
                            <button class="btn btn-sm btn-secondary">詳細を見る</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // セッション詳細（結果閲覧）画面
    'session-detail': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#sessions">分析セッション</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">Q4売上分析</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">Q4売上分析</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="navigateTo('analysis')">
                    <span>💬</span> 分析を続ける
                </button>
                <button class="btn btn-secondary">
                    <span>📥</span> レポート出力
                </button>
            </div>
        </div>

        <!-- ステータスバナー -->
        <div class="session-status-banner completed mb-5">
            <div class="session-status-icon">✅</div>
            <div class="session-status-content">
                <div class="session-status-title">分析完了</div>
                <div class="session-status-meta">完了日時: 2025/12/25 11:30 | スナップショット: 5件</div>
            </div>
        </div>

        <div class="session-detail-grid">
            <!-- メインコンテンツ -->
            <div class="session-detail-main">
                <!-- 分析結果サマリー -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">分析結果サマリー</h3>
                    </div>
                    <div class="card-body">
                        <div class="insight-cards">
                            <div class="insight-card">
                                <div class="insight-card-icon">📈</div>
                                <div class="insight-card-content">
                                    <div class="insight-card-label">予測売上（12月）</div>
                                    <div class="insight-card-value">¥15,800,000</div>
                                    <div class="insight-card-change positive">前月比 +19.7%</div>
                                </div>
                            </div>
                            <div class="insight-card">
                                <div class="insight-card-icon">🎯</div>
                                <div class="insight-card-content">
                                    <div class="insight-card-label">予測精度</div>
                                    <div class="insight-card-value">92.3%</div>
                                    <div class="insight-card-change">信頼区間 95%</div>
                                </div>
                            </div>
                            <div class="insight-card">
                                <div class="insight-card-icon">📊</div>
                                <div class="insight-card-content">
                                    <div class="insight-card-label">Q4累計</div>
                                    <div class="insight-card-value">¥41,500,000</div>
                                    <div class="insight-card-change positive">前年比 +12.5%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- キーインサイト -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">キーインサイト</h3>
                    </div>
                    <div class="card-body">
                        <div class="insights-list">
                            <div class="insight-item">
                                <div class="insight-number">1</div>
                                <div class="insight-content">
                                    <h4 class="insight-title">12月売上は過去最高を更新する見込み</h4>
                                    <p class="insight-description">季節性とトレンドを考慮した予測モデルによると、12月の売上は¥15,800,000に達する見込みです。これは前年同月比で23%の増加となります。</p>
                                </div>
                            </div>
                            <div class="insight-item">
                                <div class="insight-number">2</div>
                                <div class="insight-content">
                                    <h4 class="insight-title">カテゴリAが売上の48%を占める</h4>
                                    <p class="insight-description">商品カテゴリ別分析の結果、カテゴリAが全体売上の約半数を占めていることが判明しました。特に新商品の貢献が大きく、前月比で35%成長しています。</p>
                                </div>
                            </div>
                            <div class="insight-item">
                                <div class="insight-number">3</div>
                                <div class="insight-content">
                                    <h4 class="insight-title">週末の売上が平日の1.8倍</h4>
                                    <p class="insight-description">曜日別の分析から、週末の売上が平日を大きく上回っていることが確認されました。週末限定のプロモーション強化を推奨します。</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 生成されたグラフ -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">分析グラフ</h3>
                    </div>
                    <div class="card-body">
                        <div class="chart-grid">
                            <div class="chart-placeholder">
                                <div class="chart-placeholder-icon">📈</div>
                                <div class="chart-placeholder-title">月別売上推移</div>
                                <div class="chart-placeholder-desc">10月〜12月の売上トレンド</div>
                            </div>
                            <div class="chart-placeholder">
                                <div class="chart-placeholder-icon">🥧</div>
                                <div class="chart-placeholder-title">カテゴリ別構成比</div>
                                <div class="chart-placeholder-desc">売上構成の可視化</div>
                            </div>
                            <div class="chart-placeholder">
                                <div class="chart-placeholder-icon">📊</div>
                                <div class="chart-placeholder-title">曜日別売上</div>
                                <div class="chart-placeholder-desc">曜日ごとの売上パターン</div>
                            </div>
                            <div class="chart-placeholder">
                                <div class="chart-placeholder-icon">📉</div>
                                <div class="chart-placeholder-title">予測 vs 実績</div>
                                <div class="chart-placeholder-desc">予測精度の検証</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AI対話履歴 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">分析履歴（主要な質問と回答）</h3>
                        <button class="btn btn-sm btn-link" onclick="navigateTo('snapshots')">全履歴を見る</button>
                    </div>
                    <div class="card-body p-0">
                        <div class="conversation-summary">
                            <div class="conversation-item">
                                <div class="conversation-q">
                                    <span class="conversation-label">Q</span>
                                    月別の売上推移を見せてください
                                </div>
                                <div class="conversation-a">
                                    <span class="conversation-label">A</span>
                                    10月: ¥12.5M、11月: ¥13.2M、12月予測: ¥15.8M。12月は前月比19.7%増の見込み。
                                </div>
                            </div>
                            <div class="conversation-item">
                                <div class="conversation-q">
                                    <span class="conversation-label">Q</span>
                                    カテゴリ別の内訳も分析してください
                                </div>
                                <div class="conversation-a">
                                    <span class="conversation-label">A</span>
                                    カテゴリA: 48%、カテゴリB: 32%、カテゴリC: 15%、その他: 5%。カテゴリAの成長が顕著。
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- サイドバー -->
            <div class="session-detail-sidebar">
                <!-- セッション情報 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">セッション情報</h3>
                    </div>
                    <div class="card-body">
                        <div class="session-info-list">
                            <div class="session-info-item">
                                <div class="session-info-label">課題</div>
                                <div class="session-info-value">売上予測</div>
                            </div>
                            <div class="session-info-item">
                                <div class="session-info-label">検証カテゴリ</div>
                                <div class="session-info-value">時系列分析</div>
                            </div>
                            <div class="session-info-item">
                                <div class="session-info-label">入力ファイル</div>
                                <div class="session-info-value">sales_2025q4.xlsx</div>
                            </div>
                            <div class="session-info-item">
                                <div class="session-info-label">作成者</div>
                                <div class="session-info-value">山田 太郎</div>
                            </div>
                            <div class="session-info-item">
                                <div class="session-info-label">作成日</div>
                                <div class="session-info-value">2025/12/25 10:30</div>
                            </div>
                            <div class="session-info-item">
                                <div class="session-info-label">完了日</div>
                                <div class="session-info-value">2025/12/25 11:30</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- アクション -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">アクション</h3>
                    </div>
                    <div class="card-body">
                        <div class="action-buttons">
                            <button class="btn btn-secondary w-full mb-2">
                                <span>📋</span> セッションを複製
                            </button>
                            <button class="btn btn-secondary w-full mb-2">
                                <span>🔗</span> 結果を共有
                            </button>
                            <button class="btn btn-danger w-full">
                                <span>🗑️</span> セッションを削除
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 関連セッション -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">関連セッション</h3>
                    </div>
                    <div class="card-body p-0">
                        <div class="related-sessions">
                            <div class="related-session-item">
                                <div class="related-session-name">商品カテゴリ分析</div>
                                <div class="related-session-meta">2025/12/23 • 完了</div>
                            </div>
                            <div class="related-session-item">
                                <div class="related-session-name">顧客セグメント分析</div>
                                <div class="related-session-meta">2025/12/20 • 完了</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
};
