// ========================================
// Project Management Pages
// ========================================

const projectPages = {
    // プロジェクト一覧
    projects: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">プロジェクト一覧</span>
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
            <div class="card-body">
                <div class="search-bar">
                    <input type="text" class="form-input search-input" placeholder="プロジェクト名で検索...">
                    <select class="form-select" style="width: 150px;">
                        <option value="">全てのステータス</option>
                        <option value="active">有効</option>
                        <option value="archived">アーカイブ</option>
                    </select>
                    <button class="btn btn-secondary">検索</button>
                </div>

                <div class="table-container">
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
                                    <button class="btn btn-sm btn-warning">アーカイブ</button>
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
                                    <button class="btn btn-sm btn-warning">アーカイブ</button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>旧プロジェクト</strong></td>
                                <td>アーカイブ済みプロジェクト</td>
                                <td>2</td>
                                <td><span class="badge badge-secondary">アーカイブ</span></td>
                                <td>2025/10/01</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-secondary">編集</button>
                                    <button class="btn btn-sm btn-primary">復元</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pagination mt-5">
                    <button class="pagination-btn" disabled>◀ 前へ</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">3</button>
                    <button class="pagination-btn">次へ ▶</button>
                </div>
            </div>
        </div>
    `,

    // プロジェクト作成
    'project-new': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">新規作成</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">プロジェクト作成</h1>
        </div>

        <div class="card">
            <div class="card-body">
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

                    <div class="d-flex gap-3 justify-end">
                        <button type="button" class="btn btn-secondary" onclick="navigateTo('projects')">キャンセル</button>
                        <button type="submit" class="btn btn-primary">作成</button>
                    </div>
                </form>
            </div>
        </div>
    `,

    // プロジェクト詳細
    'project-detail': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上分析プロジェクト</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">売上分析プロジェクト</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="openModal('edit-project-modal')">
                    <span>✏️</span> 編集
                </button>
                <button class="btn btn-danger" onclick="demoAction('delete', 'プロジェクト')">
                    <span>🗑️</span> 削除
                </button>
            </div>
        </div>

        <!-- プロジェクト情報カード -->
        <div class="project-detail-grid">
            <div class="project-main">
                <!-- 概要 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">プロジェクト概要</h3>
                        <span class="badge badge-success">有効</span>
                    </div>
                    <div class="card-body">
                        <div class="project-description">
                            <p>2025年度の売上データを分析し、来期の売上予測と改善施策を検討するプロジェクトです。</p>
                            <p class="mt-3">主な目標：</p>
                            <ul class="mt-2" style="margin-left: var(--spacing-5);">
                                <li>四半期ごとの売上トレンド分析</li>
                                <li>商品カテゴリ別の売上構成比分析</li>
                                <li>顧客セグメント別の購買行動分析</li>
                                <li>来期売上予測モデルの構築</li>
                            </ul>
                        </div>

                        <div class="divider"></div>

                        <div class="project-meta-grid">
                            <div class="project-meta-item">
                                <div class="project-meta-label">作成日</div>
                                <div class="project-meta-value">2025年12月1日</div>
                            </div>
                            <div class="project-meta-item">
                                <div class="project-meta-label">開始日</div>
                                <div class="project-meta-value">2025年12月1日</div>
                            </div>
                            <div class="project-meta-item">
                                <div class="project-meta-label">終了予定日</div>
                                <div class="project-meta-value">2026年3月31日</div>
                            </div>
                            <div class="project-meta-item">
                                <div class="project-meta-label">作成者</div>
                                <div class="project-meta-value">山田 太郎</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 分析セッション -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">分析セッション</h3>
                        <button class="btn btn-sm btn-primary" onclick="navigateTo('session-new')">
                            <span>➕</span> 新規セッション
                        </button>
                    </div>
                    <div class="card-body p-0">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>セッション名</th>
                                    <th>課題</th>
                                    <th>スナップショット</th>
                                    <th>更新日時</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr onclick="navigateTo('analysis')">
                                    <td><strong>Q4売上分析</strong></td>
                                    <td>売上予測</td>
                                    <td>5</td>
                                    <td>2025/12/25 10:30</td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-primary">開く</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>商品カテゴリ分析</strong></td>
                                    <td>売上予測</td>
                                    <td>3</td>
                                    <td>2025/12/23 15:00</td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-primary">開く</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- ドライバーツリー -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">ドライバーツリー</h3>
                        <button class="btn btn-sm btn-primary" onclick="navigateTo('tree-new')">
                            <span>➕</span> 新規ツリー
                        </button>
                    </div>
                    <div class="card-body p-0">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>ツリー名</th>
                                    <th>ノード数</th>
                                    <th>施策数</th>
                                    <th>更新日時</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr onclick="navigateTo('tree-edit')">
                                    <td><strong>売上ドライバーツリー</strong></td>
                                    <td>12</td>
                                    <td>3</td>
                                    <td>2025/12/25 09:00</td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-primary">編集</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="project-sidebar">
                <!-- メンバー -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">メンバー (5)</h3>
                        <button class="btn btn-sm btn-link" onclick="navigateTo('members')">管理</button>
                    </div>
                    <div class="card-body p-0">
                        <div class="member-list">
                            <div class="member-item">
                                <div class="member-avatar">👤</div>
                                <div class="member-info">
                                    <div class="member-name">山田 太郎</div>
                                    <div class="member-role">PROJECT_MANAGER</div>
                                </div>
                            </div>
                            <div class="member-item">
                                <div class="member-avatar">👤</div>
                                <div class="member-info">
                                    <div class="member-name">鈴木 花子</div>
                                    <div class="member-role">MODERATOR</div>
                                </div>
                            </div>
                            <div class="member-item">
                                <div class="member-avatar">👤</div>
                                <div class="member-info">
                                    <div class="member-name">田中 一郎</div>
                                    <div class="member-role">MEMBER</div>
                                </div>
                            </div>
                            <div class="member-item">
                                <div class="member-avatar">👤</div>
                                <div class="member-info">
                                    <div class="member-name">佐藤 次郎</div>
                                    <div class="member-role">MEMBER</div>
                                </div>
                            </div>
                            <div class="member-item">
                                <div class="member-avatar">👤</div>
                                <div class="member-info">
                                    <div class="member-name">高橋 三郎</div>
                                    <div class="member-role">VIEWER</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ファイル -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">ファイル (3)</h3>
                        <button class="btn btn-sm btn-link" onclick="navigateTo('files')">すべて見る</button>
                    </div>
                    <div class="card-body p-0">
                        <div class="file-list">
                            <div class="file-item">
                                <div class="file-icon">📊</div>
                                <div class="file-info">
                                    <div class="file-name">sales_2025q4.xlsx</div>
                                    <div class="file-meta">2.4 MB • 12/20</div>
                                </div>
                            </div>
                            <div class="file-item">
                                <div class="file-icon">📄</div>
                                <div class="file-info">
                                    <div class="file-name">monthly_report.csv</div>
                                    <div class="file-meta">856 KB • 12/18</div>
                                </div>
                            </div>
                            <div class="file-item">
                                <div class="file-icon">📊</div>
                                <div class="file-info">
                                    <div class="file-name">customer_data.xlsx</div>
                                    <div class="file-meta">1.2 MB • 12/15</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-sm btn-secondary w-full" onclick="navigateTo('upload')">
                            <span>⬆️</span> ファイルをアップロード
                        </button>
                    </div>
                </div>

                <!-- 統計 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">統計</h3>
                    </div>
                    <div class="card-body">
                        <div class="mini-stats">
                            <div class="mini-stat">
                                <div class="mini-stat-value">2</div>
                                <div class="mini-stat-label">セッション</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">8</div>
                                <div class="mini-stat-label">スナップショット</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">1</div>
                                <div class="mini-stat-label">ツリー</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">3</div>
                                <div class="mini-stat-label">ファイル</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 編集モーダル -->
        <div class="modal-overlay" id="edit-project-modal">
            <div class="modal modal-lg">
                <div class="modal-header">
                    <h3 class="modal-title">プロジェクト編集</h3>
                    <button class="modal-close" onclick="closeModal('edit-project-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">プロジェクト名 <span class="required">*</span></label>
                        <input type="text" class="form-input" value="売上分析プロジェクト">
                    </div>
                    <div class="form-group">
                        <label class="form-label">説明</label>
                        <textarea class="form-textarea">2025年度の売上データを分析し、来期の売上予測と改善施策を検討するプロジェクトです。</textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">開始日</label>
                            <input type="date" class="form-input" value="2025-12-01">
                        </div>
                        <div class="form-group">
                            <label class="form-label">終了予定日</label>
                            <input type="date" class="form-input" value="2026-03-31">
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">ステータス</label>
                        <select class="form-select">
                            <option value="active" selected>有効</option>
                            <option value="archived">アーカイブ</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('edit-project-modal')">キャンセル</button>
                    <button class="btn btn-primary" onclick="closeModal('edit-project-modal'); showToast('success', '保存完了', 'プロジェクト情報を更新しました。')">保存</button>
                </div>
            </div>
        </div>
    `,

    // メンバー管理
    members: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上分析プロジェクト</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">メンバー管理</span>
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
            <div class="card-body p-0">
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
                                <div class="d-flex items-center gap-2">
                                    <span class="text-2xl">👤</span>
                                    <strong>山田 太郎</strong>
                                </div>
                            </td>
                            <td>yamada@example.com</td>
                            <td><span class="badge badge-info">PROJECT_MANAGER</span></td>
                            <td>2025/12/01</td>
                            <td class="actions">
                                <span class="text-secondary">（作成者）</span>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <div class="d-flex items-center gap-2">
                                    <span class="text-2xl">👤</span>
                                    <strong>鈴木 花子</strong>
                                </div>
                            </td>
                            <td>suzuki@example.com</td>
                            <td><span class="badge badge-warning">MODERATOR</span></td>
                            <td>2025/12/05</td>
                            <td class="actions">
                                <select class="form-select form-input-sm" style="width: 140px;">
                                    <option>MODERATOR</option>
                                    <option>MEMBER</option>
                                    <option>VIEWER</option>
                                </select>
                                <button class="btn btn-sm btn-danger">削除</button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <div class="d-flex items-center gap-2">
                                    <span class="text-2xl">👤</span>
                                    <strong>田中 一郎</strong>
                                </div>
                            </td>
                            <td>tanaka@example.com</td>
                            <td><span class="badge badge-success">MEMBER</span></td>
                            <td>2025/12/10</td>
                            <td class="actions">
                                <select class="form-select form-input-sm" style="width: 140px;">
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
};
