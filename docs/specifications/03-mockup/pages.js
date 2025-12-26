// ========================================
// CAMPシステム ワイヤーフレーム ページテンプレート
// ========================================

const pageTemplates = {
    // ダッシュボード
    dashboard: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
        </div>
        <div class="page-header">
            <h1 class="page-title">ダッシュボード</h1>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">参加プロジェクト</div>
                <div class="stat-value">12</div>
                <div class="stat-change positive">+2 今月</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">進行中セッション</div>
                <div class="stat-value">5</div>
                <div class="stat-change">アクティブ</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">ドライバーツリー</div>
                <div class="stat-value">8</div>
                <div class="stat-change positive">+1 今週</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">アップロードファイル</div>
                <div class="stat-value">47</div>
                <div class="stat-change">合計</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">最近のアクティビティ</h3>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>日時</th>
                        <th>プロジェクト</th>
                        <th>アクション</th>
                        <th>ユーザー</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>2025/12/25 10:30</td>
                        <td>売上分析プロジェクト</td>
                        <td>セッション作成</td>
                        <td>山田 太郎</td>
                    </tr>
                    <tr>
                        <td>2025/12/25 09:15</td>
                        <td>コスト削減プロジェクト</td>
                        <td>ツリー更新</td>
                        <td>鈴木 花子</td>
                    </tr>
                    <tr>
                        <td>2025/12/24 16:45</td>
                        <td>新規事業分析</td>
                        <td>ファイルアップロード</td>
                        <td>田中 一郎</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // プロジェクト一覧
    projects: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>プロジェクト一覧</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">プロジェクト一覧</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="navigateTo('project-new')">
                    <span>➕</span> 新規作成
                </button>
            </div>
        </div>

        <div class="card">
            <div class="search-bar">
                <input type="text" class="form-input search-input" placeholder="プロジェクト名で検索...">
                <select class="form-select" style="width: 150px;">
                    <option value="">全てのステータス</option>
                    <option value="active">有効</option>
                    <option value="inactive">無効</option>
                </select>
                <button class="btn btn-secondary">検索</button>
            </div>

            <table class="data-table">
                <thead>
                    <tr>
                        <th>プロジェクト名</th>
                        <th>説明</th>
                        <th>メンバー数</th>
                        <th>ステータス</th>
                        <th>作成日</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr onclick="navigateTo('project-detail')">
                        <td><strong>売上分析プロジェクト</strong></td>
                        <td>2025年度の売上データ分析</td>
                        <td>5</td>
                        <td><span class="badge badge-success">有効</span></td>
                        <td>2025/12/01</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">無効化</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>コスト削減プロジェクト</strong></td>
                        <td>製造コストの最適化分析</td>
                        <td>3</td>
                        <td><span class="badge badge-success">有効</span></td>
                        <td>2025/11/15</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">無効化</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>旧プロジェクト</strong></td>
                        <td>アーカイブ済みプロジェクト</td>
                        <td>2</td>
                        <td><span class="badge badge-danger">無効</span></td>
                        <td>2025/10/01</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-primary">有効化</button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="pagination">
                <button class="pagination-btn" disabled>◀ 前へ</button>
                <button class="pagination-btn active">1</button>
                <button class="pagination-btn">2</button>
                <button class="pagination-btn">3</button>
                <button class="pagination-btn">次へ ▶</button>
            </div>
        </div>
    `,

    // プロジェクト作成
    'project-new': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span>/</span>
            <span>新規作成</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">プロジェクト作成</h1>
        </div>

        <div class="card">
            <form>
                <div class="form-group">
                    <label class="form-label">
                        プロジェクト名 <span class="required">*</span>
                    </label>
                    <input type="text" class="form-input" placeholder="プロジェクト名を入力">
                </div>

                <div class="form-group">
                    <label class="form-label">説明</label>
                    <textarea class="form-textarea" placeholder="プロジェクトの説明を入力"></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">開始日</label>
                        <input type="date" class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label">終了予定日</label>
                        <input type="date" class="form-input">
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">初期メンバー（オプション）</label>
                    <select class="form-select" multiple style="height: 100px;">
                        <option value="1">鈴木 花子</option>
                        <option value="2">田中 一郎</option>
                        <option value="3">佐藤 次郎</option>
                    </select>
                    <div class="form-help">Ctrlキーを押しながらクリックで複数選択</div>
                </div>

                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" onclick="navigateTo('projects')">キャンセル</button>
                    <button type="submit" class="btn btn-primary">作成</button>
                </div>
            </form>
        </div>
    `,

    // メンバー管理
    members: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span>/</span>
            <span>売上分析プロジェクト</span>
            <span>/</span>
            <span>メンバー管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">メンバー管理</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="openModal('add-member-modal')">
                    <span>➕</span> メンバー追加
                </button>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active">メンバー一覧</button>
            <button class="tab">招待履歴</button>
        </div>

        <div class="card">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ユーザー</th>
                        <th>メールアドレス</th>
                        <th>ロール</th>
                        <th>追加日</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 24px;">👤</span>
                                <strong>山田 太郎</strong>
                            </div>
                        </td>
                        <td>yamada@example.com</td>
                        <td><span class="badge badge-info">PROJECT_MANAGER</span></td>
                        <td>2025/12/01</td>
                        <td class="actions">
                            <span style="color: var(--text-secondary);">（作成者）</span>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 24px;">👤</span>
                                <strong>鈴木 花子</strong>
                            </div>
                        </td>
                        <td>suzuki@example.com</td>
                        <td><span class="badge badge-warning">MODERATOR</span></td>
                        <td>2025/12/05</td>
                        <td class="actions">
                            <select class="form-select" style="width: 140px; padding: 4px 8px;">
                                <option>MODERATOR</option>
                                <option>MEMBER</option>
                                <option>VIEWER</option>
                            </select>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 24px;">👤</span>
                                <strong>田中 一郎</strong>
                            </div>
                        </td>
                        <td>tanaka@example.com</td>
                        <td><span class="badge badge-success">MEMBER</span></td>
                        <td>2025/12/10</td>
                        <td class="actions">
                            <select class="form-select" style="width: 140px; padding: 4px 8px;">
                                <option>MEMBER</option>
                                <option>MODERATOR</option>
                                <option>VIEWER</option>
                            </select>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- メンバー追加モーダル -->
        <div class="modal-overlay" id="add-member-modal">
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title">メンバー追加</h3>
                    <button class="modal-close" onclick="closeModal('add-member-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">ユーザー選択 <span class="required">*</span></label>
                        <select class="form-select">
                            <option value="">ユーザーを選択...</option>
                            <option value="1">佐藤 次郎 (sato@example.com)</option>
                            <option value="2">高橋 三郎 (takahashi@example.com)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">ロール <span class="required">*</span></label>
                        <select class="form-select">
                            <option value="MEMBER">MEMBER - 一般メンバー</option>
                            <option value="MODERATOR">MODERATOR - モデレーター</option>
                            <option value="VIEWER">VIEWER - 閲覧のみ</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('add-member-modal')">キャンセル</button>
                    <button class="btn btn-primary">追加</button>
                </div>
            </div>
        </div>
    `,

    // 分析セッション一覧
    sessions: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span>/</span>
            <span>売上分析プロジェクト</span>
            <span>/</span>
            <span>分析セッション</span>
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
            <div class="search-bar">
                <input type="text" class="form-input search-input" placeholder="セッション名で検索...">
                <select class="form-select" style="width: 150px;">
                    <option value="">全ての課題</option>
                    <option value="1">売上予測</option>
                    <option value="2">コスト分析</option>
                </select>
                <button class="btn btn-secondary">検索</button>
            </div>

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
    `,

    // 新規セッション作成
    'session-new': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span>/</span>
            <a href="#sessions">分析セッション</a>
            <span>/</span>
            <span>新規作成</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">新規セッション作成</h1>
        </div>

        <div class="card">
            <form>
                <div class="form-group">
                    <label class="form-label">
                        課題を選択 <span class="required">*</span>
                    </label>
                    <select class="form-select">
                        <option value="">課題を選択してください...</option>
                        <option value="1">売上予測 - 時系列分析による売上予測</option>
                        <option value="2">コスト分析 - コスト構造の可視化と最適化</option>
                        <option value="3">顧客分析 - 顧客セグメンテーション</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="form-label">
                        入力ファイル <span class="required">*</span>
                    </label>
                    <select class="form-select">
                        <option value="">ファイルを選択してください...</option>
                        <option value="1">sales_2025q4.xlsx (アップロード: 2025/12/20)</option>
                        <option value="2">monthly_report.csv (アップロード: 2025/12/18)</option>
                        <option value="3">customer_data.xlsx (アップロード: 2025/12/15)</option>
                    </select>
                    <div class="form-help">プロジェクトにアップロード済みのファイルから選択してください</div>
                </div>

                <div class="form-group">
                    <label class="form-label">セッション名（オプション）</label>
                    <input type="text" class="form-input" placeholder="セッション名を入力（空白の場合は自動生成）">
                </div>

                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" onclick="navigateTo('sessions')">キャンセル</button>
                    <button type="submit" class="btn btn-primary">作成して開始</button>
                </div>
            </form>
        </div>
    `,

    // 分析画面
    analysis: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#sessions">分析セッション</a>
            <span>/</span>
            <span>Q4売上分析</span>
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
                入力ファイル: sales_2025q4.xlsx | 課題: 売上予測
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
                        <div class="step-item">
                            <div class="step-number">1</div>
                            <div class="step-info">
                                <div class="step-title">データ読み込み</div>
                                <div class="step-meta">完了 - 10:30</div>
                            </div>
                        </div>
                        <div class="step-item">
                            <div class="step-number">2</div>
                            <div class="step-info">
                                <div class="step-title">月別売上集計</div>
                                <div class="step-meta">完了 - 10:32</div>
                            </div>
                        </div>
                        <div class="step-item">
                            <div class="step-number">3</div>
                            <div class="step-info">
                                <div class="step-title">グラフ生成</div>
                                <div class="step-meta">完了 - 10:33</div>
                            </div>
                        </div>
                        <div class="step-item" style="background-color: #eff6ff;">
                            <div class="step-number">4</div>
                            <div class="step-info">
                                <div class="step-title">カテゴリ別分析</div>
                                <div class="step-meta">実行中...</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        <h3 class="card-title">ファイル情報</h3>
                    </div>
                    <div style="font-size: 14px;">
                        <p><strong>ファイル名:</strong> sales_2025q4.xlsx</p>
                        <p><strong>サイズ:</strong> 2.4 MB</p>
                        <p><strong>行数:</strong> 15,230</p>
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
            <span>/</span>
            <a href="#sessions">分析セッション</a>
            <span>/</span>
            <a href="#analysis">Q4売上分析</a>
            <span>/</span>
            <span>スナップショット履歴</span>
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
                過去のスナップショットに戻ると、そこから新しい分岐が作成されます。
            </div>
        </div>

        <div class="card">
            <div class="snapshot-timeline">
                <div class="snapshot-item current">
                    <div class="snapshot-header">
                        <span class="snapshot-title">スナップショット #5（現在）</span>
                        <span class="snapshot-date">2025/12/25 10:45</span>
                    </div>
                    <p>カテゴリ別分析を実行中</p>
                    <div style="margin-top: 8px;">
                        <span class="badge badge-success">現在地</span>
                    </div>
                </div>

                <div class="snapshot-item">
                    <div class="snapshot-header">
                        <span class="snapshot-title">スナップショット #4</span>
                        <span class="snapshot-date">2025/12/25 10:33</span>
                    </div>
                    <p>月別売上グラフ生成完了</p>
                    <div style="margin-top: 8px;">
                        <button class="btn btn-sm btn-primary">この時点に戻る</button>
                        <button class="btn btn-sm btn-secondary">詳細を見る</button>
                    </div>
                </div>

                <div class="snapshot-item">
                    <div class="snapshot-header">
                        <span class="snapshot-title">スナップショット #3</span>
                        <span class="snapshot-date">2025/12/25 10:32</span>
                    </div>
                    <p>月別売上集計完了</p>
                    <div style="margin-top: 8px;">
                        <button class="btn btn-sm btn-primary">この時点に戻る</button>
                        <button class="btn btn-sm btn-secondary">詳細を見る</button>
                    </div>
                </div>

                <div class="snapshot-item">
                    <div class="snapshot-header">
                        <span class="snapshot-title">スナップショット #2</span>
                        <span class="snapshot-date">2025/12/25 10:31</span>
                    </div>
                    <p>データ読み込み完了</p>
                    <div style="margin-top: 8px;">
                        <button class="btn btn-sm btn-primary">この時点に戻る</button>
                        <button class="btn btn-sm btn-secondary">詳細を見る</button>
                    </div>
                </div>

                <div class="snapshot-item">
                    <div class="snapshot-header">
                        <span class="snapshot-title">スナップショット #1（初期）</span>
                        <span class="snapshot-date">2025/12/25 10:30</span>
                    </div>
                    <p>セッション開始</p>
                    <div style="margin-top: 8px;">
                        <button class="btn btn-sm btn-primary">この時点に戻る</button>
                        <button class="btn btn-sm btn-secondary">詳細を見る</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // ドライバーツリー一覧
    trees: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span>/</span>
            <span>売上分析プロジェクト</span>
            <span>/</span>
            <span>ドライバーツリー</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ドライバーツリー一覧</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="navigateTo('tree-new')">
                    <span>➕</span> 新規作成
                </button>
            </div>
        </div>

        <div class="card">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ツリー名</th>
                        <th>数式マスタ</th>
                        <th>ノード数</th>
                        <th>施策数</th>
                        <th>更新日時</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr onclick="navigateTo('tree-edit')">
                        <td><strong>売上ドライバーツリー</strong></td>
                        <td>売上分解モデル v2</td>
                        <td>12</td>
                        <td>3</td>
                        <td>2025/12/25 09:00</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-primary">編集</button>
                            <button class="btn btn-sm btn-secondary">複製</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>コストドライバーツリー</strong></td>
                        <td>コスト構造モデル</td>
                        <td>8</td>
                        <td>5</td>
                        <td>2025/12/24 14:30</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-primary">編集</button>
                            <button class="btn btn-sm btn-secondary">複製</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // ツリー作成
    'tree-new': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#trees">ドライバーツリー</a>
            <span>/</span>
            <span>新規作成</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ドライバーツリー作成</h1>
        </div>

        <div class="card">
            <form>
                <div class="form-group">
                    <label class="form-label">
                        ツリー名 <span class="required">*</span>
                    </label>
                    <input type="text" class="form-input" placeholder="ツリー名を入力">
                </div>

                <div class="form-group">
                    <label class="form-label">数式マスタ（オプション）</label>
                    <select class="form-select">
                        <option value="">数式マスタを選択...</option>
                        <option value="1">売上分解モデル v2</option>
                        <option value="2">コスト構造モデル</option>
                        <option value="3">利益率分析モデル</option>
                    </select>
                    <div class="form-help">数式マスタを選択すると、定義済みの構造が適用されます</div>
                </div>

                <div class="form-group">
                    <label class="form-label">説明</label>
                    <textarea class="form-textarea" placeholder="ツリーの説明を入力"></textarea>
                </div>

                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" onclick="navigateTo('trees')">キャンセル</button>
                    <button type="submit" class="btn btn-primary">作成して編集</button>
                </div>
            </form>
        </div>
    `,

    // ツリー編集
    'tree-edit': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#trees">ドライバーツリー</a>
            <span>/</span>
            <span>売上ドライバーツリー</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">売上ドライバーツリー</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>📥</span> データ取込
                </button>
                <button class="btn btn-primary">
                    <span>💾</span> 保存
                </button>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active">ツリー編集</button>
            <button class="tab" onclick="navigateTo('tree-policies')">施策設定</button>
            <button class="tab">データ紐付け</button>
            <button class="tab">計算結果</button>
        </div>

        <div class="tree-canvas">
            <div class="tree-toolbar">
                <button class="btn btn-sm btn-primary">ノード追加</button>
                <button class="btn btn-sm btn-secondary">リレーション追加</button>
                <button class="btn btn-sm btn-secondary">整列</button>
                <button class="btn btn-sm btn-secondary">ズームイン</button>
                <button class="btn btn-sm btn-secondary">ズームアウト</button>
            </div>

            <!-- ツリーノードのビジュアル表現（簡易版） -->
            <div style="padding: 40px; min-height: 400px; position: relative;">
                <div class="tree-node root" style="top: 20px; left: 50%; transform: translateX(-50%);">
                    売上高
                </div>

                <div class="tree-node" style="top: 120px; left: 25%;">
                    顧客数
                </div>

                <div class="tree-node" style="top: 120px; left: 55%;">
                    顧客単価
                </div>

                <div class="tree-node" style="top: 220px; left: 10%;">
                    新規顧客
                </div>

                <div class="tree-node" style="top: 220px; left: 30%;">
                    既存顧客
                </div>

                <div class="tree-node selected" style="top: 220px; left: 50%;">
                    購入頻度
                </div>

                <div class="tree-node" style="top: 220px; left: 70%;">
                    平均購入額
                </div>

                <!-- 接続線（SVGで描画するのが理想だが、簡易表現） -->
                <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                    <line x1="50%" y1="55" x2="30%" y2="120" stroke="#2563eb" stroke-width="2"/>
                    <line x1="50%" y1="55" x2="65%" y2="120" stroke="#2563eb" stroke-width="2"/>
                    <line x1="30%" y1="155" x2="15%" y2="220" stroke="#2563eb" stroke-width="2"/>
                    <line x1="30%" y1="155" x2="35%" y2="220" stroke="#2563eb" stroke-width="2"/>
                    <line x1="65%" y1="155" x2="55%" y2="220" stroke="#2563eb" stroke-width="2"/>
                    <line x1="65%" y1="155" x2="75%" y2="220" stroke="#2563eb" stroke-width="2"/>
                </svg>
            </div>
        </div>

        <!-- ノード編集パネル -->
        <div class="card" style="margin-top: 20px;">
            <div class="card-header">
                <h3 class="card-title">選択中のノード: 購入頻度</h3>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">ラベル</label>
                    <input type="text" class="form-input" value="購入頻度">
                </div>
                <div class="form-group">
                    <label class="form-label">ノードタイプ</label>
                    <select class="form-select">
                        <option value="driver">ドライバー</option>
                        <option value="kpi" selected>KPI</option>
                        <option value="metric">メトリクス</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">データフレーム紐付け</label>
                <select class="form-select">
                    <option value="">紐付けなし</option>
                    <option value="1">sales_data.購入頻度</option>
                    <option value="2">customer_data.frequency</option>
                </select>
            </div>
        </div>
    `,

    // ファイル一覧
    files: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span>/</span>
            <span>売上分析プロジェクト</span>
            <span>/</span>
            <span>ファイル管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ファイル管理</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="navigateTo('upload')">
                    <span>⬆️</span> アップロード
                </button>
            </div>
        </div>

        <div class="card">
            <div class="search-bar">
                <input type="text" class="form-input search-input" placeholder="ファイル名で検索...">
                <select class="form-select" style="width: 150px;">
                    <option value="">全てのタイプ</option>
                    <option value="xlsx">Excel (.xlsx)</option>
                    <option value="csv">CSV (.csv)</option>
                    <option value="json">JSON (.json)</option>
                </select>
                <button class="btn btn-secondary">検索</button>
            </div>

            <table class="data-table">
                <thead>
                    <tr>
                        <th>ファイル名</th>
                        <th>タイプ</th>
                        <th>サイズ</th>
                        <th>アップロード者</th>
                        <th>アップロード日</th>
                        <th>使用状況</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span>📊</span>
                                <strong>sales_2025q4.xlsx</strong>
                            </div>
                        </td>
                        <td>Excel</td>
                        <td>2.4 MB</td>
                        <td>山田 太郎</td>
                        <td>2025/12/20</td>
                        <td>
                            <span class="badge badge-info">セッション: 2</span>
                            <span class="badge badge-info">ツリー: 1</span>
                        </td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">ダウンロード</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span>📄</span>
                                <strong>monthly_report.csv</strong>
                            </div>
                        </td>
                        <td>CSV</td>
                        <td>856 KB</td>
                        <td>鈴木 花子</td>
                        <td>2025/12/18</td>
                        <td>
                            <span class="badge badge-info">セッション: 1</span>
                        </td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">ダウンロード</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span>📊</span>
                                <strong>customer_data.xlsx</strong>
                            </div>
                        </td>
                        <td>Excel</td>
                        <td>1.2 MB</td>
                        <td>田中 一郎</td>
                        <td>2025/12/15</td>
                        <td>
                            <span class="badge badge-warning">未使用</span>
                        </td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">ダウンロード</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // アップロード
    upload: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <a href="#files">ファイル管理</a>
            <span>/</span>
            <span>アップロード</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ファイルアップロード</h1>
        </div>

        <div class="card">
            <div class="file-upload">
                <div class="file-upload-icon">📁</div>
                <div class="file-upload-text">
                    ファイルをドラッグ＆ドロップ<br>
                    または<br>
                    <button class="btn btn-primary" style="margin-top: 12px;">ファイルを選択</button>
                </div>
            </div>

            <div style="margin-top: 20px;">
                <p style="font-size: 14px; color: var(--text-secondary);">
                    対応フォーマット: Excel (.xlsx, .xls), CSV (.csv), JSON (.json)<br>
                    最大ファイルサイズ: 50MB
                </p>
            </div>

            <!-- アップロード中のファイル -->
            <div style="margin-top: 20px;">
                <h4 style="margin-bottom: 12px;">アップロード中</h4>
                <div style="padding: 12px; background-color: var(--background-color); border-radius: 8px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span>new_data.xlsx</span>
                        <span>75%</span>
                    </div>
                    <div style="background-color: var(--border-color); height: 8px; border-radius: 4px;">
                        <div style="background-color: var(--primary-color); height: 100%; width: 75%; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // ユーザー管理
    users: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>システム管理</span>
            <span>/</span>
            <span>ユーザー管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ユーザー管理</h1>
        </div>

        <div class="alert alert-info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                ユーザーはAzure AD認証により自動作成されます。ここでは既存ユーザーの管理を行います。
            </div>
        </div>

        <div class="card">
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
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 24px;">👤</span>
                                <strong>管理者 太郎</strong>
                            </div>
                        </td>
                        <td>admin@example.com</td>
                        <td><span class="badge badge-danger">ADMIN</span></td>
                        <td><span class="badge badge-success">有効</span></td>
                        <td>2025/12/25 10:00</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">詳細</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 24px;">👤</span>
                                <strong>山田 太郎</strong>
                            </div>
                        </td>
                        <td>yamada@example.com</td>
                        <td><span class="badge badge-info">SYSTEM_USER</span></td>
                        <td><span class="badge badge-success">有効</span></td>
                        <td>2025/12/25 10:30</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">詳細</button>
                            <button class="btn btn-sm btn-danger">無効化</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 24px;">👤</span>
                                <strong>退職者 次郎</strong>
                            </div>
                        </td>
                        <td>taishoku@example.com</td>
                        <td><span class="badge badge-info">SYSTEM_USER</span></td>
                        <td><span class="badge badge-danger">無効</span></td>
                        <td>2025/11/30 18:00</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">詳細</button>
                            <button class="btn btn-sm btn-primary">有効化</button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="pagination">
                <button class="pagination-btn" disabled>◀ 前へ</button>
                <button class="pagination-btn active">1</button>
                <button class="pagination-btn">2</button>
                <button class="pagination-btn">次へ ▶</button>
            </div>
        </div>
    `,

    // 数式マスタ管理
    formulas: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>ドライバーツリー</span>
            <span>/</span>
            <span>数式マスタ管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">数式マスタ管理</h1>
            <div class="page-actions">
                <button class="btn btn-primary">
                    <span>➕</span> 新規作成
                </button>
            </div>
        </div>

        <div class="card">
            <div class="search-bar">
                <input type="text" class="form-input search-input" placeholder="KPIまたは数式で検索...">
                <select class="form-select" style="width: 180px;">
                    <option value="">全てのカテゴリ</option>
                    <option value="1">売上系</option>
                    <option value="2">コスト系</option>
                    <option value="3">利益系</option>
                </select>
                <button class="btn btn-secondary">検索</button>
            </div>

            <table class="data-table">
                <thead>
                    <tr>
                        <th>KPI</th>
                        <th>カテゴリ</th>
                        <th>ドライバータイプ</th>
                        <th>数式</th>
                        <th>更新日</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>売上高</strong></td>
                        <td>売上系</td>
                        <td>Revenue</td>
                        <td><code>顧客数 × 顧客単価</code></td>
                        <td>2025/12/20</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>顧客単価</strong></td>
                        <td>売上系</td>
                        <td>Revenue</td>
                        <td><code>購入頻度 × 平均購入額</code></td>
                        <td>2025/12/20</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>粗利益</strong></td>
                        <td>利益系</td>
                        <td>Profit</td>
                        <td><code>売上高 - 売上原価</code></td>
                        <td>2025/12/18</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // カテゴリマスタ管理
    categories: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>ドライバーツリー</span>
            <span>/</span>
            <span>カテゴリマスタ管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">カテゴリマスタ管理</h1>
            <div class="page-actions">
                <button class="btn btn-primary">
                    <span>➕</span> 新規作成
                </button>
            </div>
        </div>

        <div class="card">
            <div class="search-bar">
                <input type="text" class="form-input search-input" placeholder="カテゴリ名で検索...">
                <select class="form-select" style="width: 180px;">
                    <option value="">全ての業界分類</option>
                    <option value="1">製造業</option>
                    <option value="2">小売業</option>
                    <option value="3">サービス業</option>
                </select>
                <button class="btn btn-secondary">検索</button>
            </div>

            <table class="data-table">
                <thead>
                    <tr>
                        <th>カテゴリ名</th>
                        <th>業界分類</th>
                        <th>ドライバータイプ</th>
                        <th>数式数</th>
                        <th>更新日</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>売上分解モデル v2</strong></td>
                        <td>全業種共通</td>
                        <td>Revenue</td>
                        <td>5</td>
                        <td>2025/12/20</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>コスト構造モデル</strong></td>
                        <td>製造業</td>
                        <td>Cost</td>
                        <td>8</td>
                        <td>2025/12/18</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>利益率分析モデル</strong></td>
                        <td>小売業</td>
                        <td>Profit</td>
                        <td>4</td>
                        <td>2025/12/15</td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // 課題マスタ管理
    issues: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>システム管理</span>
            <span>/</span>
            <span>課題マスタ管理</span>
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
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-secondary">プロンプト</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>コスト分析</strong></td>
                        <td>コスト最適化</td>
                        <td><span class="badge badge-success">設定済</span></td>
                        <td><span class="badge badge-warning">未設定</span></td>
                        <td><span class="badge badge-success">有効</span></td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-secondary">プロンプト</button>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>顧客分析</strong></td>
                        <td>セグメンテーション</td>
                        <td><span class="badge badge-warning">未設定</span></td>
                        <td><span class="badge badge-warning">未設定</span></td>
                        <td><span class="badge badge-warning">下書き</span></td>
                        <td class="actions">
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-secondary">プロンプト</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // 検証マスタ管理
    verifications: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>システム管理</span>
            <span>/</span>
            <span>検証マスタ管理</span>
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
                            <button class="btn btn-sm btn-secondary">編集</button>
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
                            <button class="btn btn-sm btn-secondary">編集</button>
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
                            <button class="btn btn-sm btn-secondary">編集</button>
                            <button class="btn btn-sm btn-danger">削除</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,

    // ロール管理
    roles: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span>/</span>
            <span>システム管理</span>
            <span>/</span>
            <span>ロール管理</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ロール管理</h1>
        </div>

        <div class="alert alert-info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                システムロールは定義済みです。各ロールの権限を確認できます。
            </div>
        </div>

        <div class="card">
            <h3 class="card-title" style="margin-bottom: 16px;">システムロール</h3>
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

        <div class="card">
            <h3 class="card-title" style="margin-bottom: 16px;">プロジェクトロール</h3>
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
                        <td><span class="badge badge-secondary" style="background-color: #e2e8f0; color: #475569;">VIEWER</span></td>
                        <td>閲覧者</td>
                        <td>閲覧のみ。編集・作成不可</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `,
};
