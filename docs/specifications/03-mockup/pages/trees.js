// ========================================
// Driver Tree Pages
// ========================================

const treePages = {
    // ドライバーツリー一覧
    trees: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上分析プロジェクト</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">ドライバーツリー</span>
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
            <div class="card-body p-0">
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
        </div>
    `,

    // ツリー作成
    'tree-new': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#trees">ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">新規作成</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ドライバーツリー作成</h1>
        </div>

        <div class="tree-new-grid">
            <!-- メインコンテンツ -->
            <div class="tree-new-main">
                <!-- テンプレート選択 -->
                <div class="card mb-5">
                    <div class="card-header">
                        <h3 class="card-title">テンプレートから作成</h3>
                    </div>
                    <div class="card-body">
                        <!-- 業種フィルター -->
                        <div class="template-filters mb-4">
                            <div class="filter-group">
                                <span class="filter-label">業種:</span>
                                <button class="filter-chip active">すべて</button>
                                <button class="filter-chip">小売・EC</button>
                                <button class="filter-chip">製造業</button>
                                <button class="filter-chip">サービス業</button>
                                <button class="filter-chip">SaaS</button>
                            </div>
                            <div class="filter-group mt-3">
                                <span class="filter-label">分析タイプ:</span>
                                <button class="filter-chip active">すべて</button>
                                <button class="filter-chip">売上分析</button>
                                <button class="filter-chip">コスト分析</button>
                                <button class="filter-chip">利益分析</button>
                            </div>
                        </div>

                        <!-- テンプレートカード -->
                        <div class="template-cards">
                            <div class="template-card selected">
                                <div class="template-card-header">
                                    <span class="template-icon">📈</span>
                                    <span class="template-badge">人気</span>
                                </div>
                                <div class="template-card-body">
                                    <h4 class="template-name">売上分解モデル（基本）</h4>
                                    <p class="template-description">顧客数 × 顧客単価で売上を分解する基本モデル</p>
                                    <div class="template-meta">
                                        <span class="template-tag">小売・EC</span>
                                        <span class="template-tag">売上分析</span>
                                    </div>
                                    <div class="template-stats">
                                        <span>ノード: 8</span>
                                        <span>利用実績: 150+</span>
                                    </div>
                                </div>
                            </div>

                            <div class="template-card">
                                <div class="template-card-header">
                                    <span class="template-icon">🛒</span>
                                </div>
                                <div class="template-card-body">
                                    <h4 class="template-name">EC売上モデル</h4>
                                    <p class="template-description">訪問者数 × CVR × AOVでEC売上を分析</p>
                                    <div class="template-meta">
                                        <span class="template-tag">小売・EC</span>
                                        <span class="template-tag">売上分析</span>
                                    </div>
                                    <div class="template-stats">
                                        <span>ノード: 12</span>
                                        <span>利用実績: 80+</span>
                                    </div>
                                </div>
                            </div>

                            <div class="template-card">
                                <div class="template-card-header">
                                    <span class="template-icon">🔄</span>
                                </div>
                                <div class="template-card-body">
                                    <h4 class="template-name">SaaS MRR分解モデル</h4>
                                    <p class="template-description">新規MRR、チャーン、拡張MRRでSaaS収益を分析</p>
                                    <div class="template-meta">
                                        <span class="template-tag">SaaS</span>
                                        <span class="template-tag">売上分析</span>
                                    </div>
                                    <div class="template-stats">
                                        <span>ノード: 15</span>
                                        <span>利用実績: 45+</span>
                                    </div>
                                </div>
                            </div>

                            <div class="template-card">
                                <div class="template-card-header">
                                    <span class="template-icon">🏭</span>
                                </div>
                                <div class="template-card-body">
                                    <h4 class="template-name">製造コスト構造モデル</h4>
                                    <p class="template-description">直接費・間接費の内訳でコスト構造を分析</p>
                                    <div class="template-meta">
                                        <span class="template-tag">製造業</span>
                                        <span class="template-tag">コスト分析</span>
                                    </div>
                                    <div class="template-stats">
                                        <span>ノード: 18</span>
                                        <span>利用実績: 35+</span>
                                    </div>
                                </div>
                            </div>

                            <div class="template-card">
                                <div class="template-card-header">
                                    <span class="template-icon">💰</span>
                                </div>
                                <div class="template-card-body">
                                    <h4 class="template-name">利益率分析モデル</h4>
                                    <p class="template-description">粗利・営業利益をドライバー別に分解</p>
                                    <div class="template-meta">
                                        <span class="template-tag">全業種</span>
                                        <span class="template-tag">利益分析</span>
                                    </div>
                                    <div class="template-stats">
                                        <span>ノード: 14</span>
                                        <span>利用実績: 60+</span>
                                    </div>
                                </div>
                            </div>

                            <div class="template-card template-blank">
                                <div class="template-card-header">
                                    <span class="template-icon">➕</span>
                                </div>
                                <div class="template-card-body">
                                    <h4 class="template-name">空のツリーから作成</h4>
                                    <p class="template-description">テンプレートを使用せず、ゼロからツリーを構築します</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- サイドバー：基本情報入力 -->
            <div class="tree-new-sidebar">
                <div class="card sticky-card">
                    <div class="card-header">
                        <h3 class="card-title">基本情報</h3>
                    </div>
                    <div class="card-body">
                        <form>
                            <div class="form-group">
                                <label class="form-label">
                                    ツリー名 <span class="required">*</span>
                                </label>
                                <input type="text" class="form-input" placeholder="ツリー名を入力">
                            </div>

                            <div class="form-group">
                                <label class="form-label">説明</label>
                                <textarea class="form-textarea" rows="3" placeholder="ツリーの説明を入力"></textarea>
                            </div>

                            <div class="form-group">
                                <label class="form-label">選択中のテンプレート</label>
                                <div class="selected-template-info">
                                    <div class="selected-template-icon">📈</div>
                                    <div class="selected-template-name">売上分解モデル（基本）</div>
                                </div>
                            </div>

                            <!-- テンプレートプレビュー -->
                            <div class="template-preview">
                                <div class="template-preview-title">構造プレビュー</div>
                                <div class="template-preview-tree">
                                    <div class="preview-node root">売上高</div>
                                    <div class="preview-children">
                                        <div class="preview-node">顧客数</div>
                                        <div class="preview-node">顧客単価</div>
                                    </div>
                                </div>
                            </div>

                            <div class="d-flex gap-3 mt-5">
                                <button type="button" class="btn btn-secondary flex-1" onclick="navigateTo('trees')">キャンセル</button>
                                <button type="submit" class="btn btn-primary flex-1">作成して編集</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `,

    // ツリー編集
    'tree-edit': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#trees">ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上ドライバーツリー</span>
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
            <button class="tab" onclick="navigateTo('tree-data-binding')">データ紐付け</button>
            <button class="tab" onclick="navigateTo('tree-results')">計算結果</button>
        </div>

        <div class="tree-canvas">
            <div class="tree-toolbar">
                <button class="btn btn-sm btn-primary">ノード追加</button>
                <button class="btn btn-sm btn-secondary">リレーション追加</button>
                <button class="btn btn-sm btn-secondary">整列</button>
                <button class="btn btn-sm btn-secondary">ズームイン</button>
                <button class="btn btn-sm btn-secondary">ズームアウト</button>
            </div>

            <!-- ツリーノードのビジュアル表現 -->
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

                <!-- 接続線 -->
                <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                    <line x1="50%" y1="55" x2="30%" y2="120" stroke="var(--color-primary-600)" stroke-width="2"/>
                    <line x1="50%" y1="55" x2="65%" y2="120" stroke="var(--color-primary-600)" stroke-width="2"/>
                    <line x1="30%" y1="155" x2="15%" y2="220" stroke="var(--color-primary-600)" stroke-width="2"/>
                    <line x1="30%" y1="155" x2="35%" y2="220" stroke="var(--color-primary-600)" stroke-width="2"/>
                    <line x1="65%" y1="155" x2="55%" y2="220" stroke="var(--color-primary-600)" stroke-width="2"/>
                    <line x1="65%" y1="155" x2="75%" y2="220" stroke="var(--color-primary-600)" stroke-width="2"/>
                </svg>
            </div>
        </div>

        <!-- ノード編集パネル -->
        <div class="card mt-5">
            <div class="card-header">
                <h3 class="card-title">選択中のノード: 購入頻度</h3>
            </div>
            <div class="card-body">
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
        </div>
    `,

    // 施策設定画面
    'tree-policies': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#trees">ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#tree-edit">売上ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">施策設定</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">施策設定</h1>
            <div class="page-actions">
                <button class="btn btn-primary" onclick="openModal('policy-modal')">
                    <span>➕</span> 新規施策
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab" onclick="navigateTo('tree-edit')">ツリー編集</button>
            <button class="tab active">施策設定</button>
            <button class="tab">データ紐付け</button>
            <button class="tab">計算結果</button>
        </div>

        <div class="alert alert-info mb-5">
            <span class="alert-icon">💡</span>
            <div class="alert-content">
                <div class="alert-title">施策について</div>
                <div class="alert-text">施策はドライバーツリーの特定ノードに対して影響を与えるアクションです。施策を設定すると、シミュレーション時に効果を確認できます。</div>
            </div>
        </div>

        <!-- 施策一覧 -->
        <div class="policy-list">
            <!-- 施策カード1 -->
            <div class="policy-card">
                <div class="policy-card-header">
                    <div class="policy-card-header-info">
                        <div class="policy-icon">📈</div>
                        <div>
                            <h3 class="policy-title">新規顧客獲得キャンペーン</h3>
                            <div class="policy-node">対象ノード: 新規顧客</div>
                        </div>
                    </div>
                    <div class="policy-card-actions">
                        <button class="btn btn-sm btn-secondary">編集</button>
                        <button class="btn btn-sm btn-danger">削除</button>
                    </div>
                </div>
                <div class="policy-card-body">
                    <p class="policy-description">
                        デジタルマーケティングを強化し、新規顧客の獲得を促進します。SNS広告、リスティング広告の出稿増加を計画。
                    </p>
                    <div class="policy-metrics">
                        <div class="policy-metric">
                            <div class="policy-metric-label">影響値</div>
                            <div class="policy-metric-value positive">+15%</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">コスト</div>
                            <div class="policy-metric-value">¥5,000,000</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">期間</div>
                            <div class="policy-metric-value">3ヶ月</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">ステータス</div>
                            <span class="badge badge-success">適用中</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 施策カード2 -->
            <div class="policy-card">
                <div class="policy-card-header">
                    <div class="policy-card-header-info">
                        <div class="policy-icon">🔄</div>
                        <div>
                            <h3 class="policy-title">リピート購入促進プログラム</h3>
                            <div class="policy-node">対象ノード: 購入頻度</div>
                        </div>
                    </div>
                    <div class="policy-card-actions">
                        <button class="btn btn-sm btn-secondary">編集</button>
                        <button class="btn btn-sm btn-danger">削除</button>
                    </div>
                </div>
                <div class="policy-card-body">
                    <p class="policy-description">
                        既存顧客のリピート購入を促進するためのロイヤルティプログラムを導入。ポイント制度とメール配信の強化。
                    </p>
                    <div class="policy-metrics">
                        <div class="policy-metric">
                            <div class="policy-metric-label">影響値</div>
                            <div class="policy-metric-value positive">+8%</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">コスト</div>
                            <div class="policy-metric-value">¥2,000,000</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">期間</div>
                            <div class="policy-metric-value">6ヶ月</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">ステータス</div>
                            <span class="badge badge-warning">計画中</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 施策カード3 -->
            <div class="policy-card">
                <div class="policy-card-header">
                    <div class="policy-card-header-info">
                        <div class="policy-icon">💰</div>
                        <div>
                            <h3 class="policy-title">プレミアム商品ラインナップ拡充</h3>
                            <div class="policy-node">対象ノード: 平均購入額</div>
                        </div>
                    </div>
                    <div class="policy-card-actions">
                        <button class="btn btn-sm btn-secondary">編集</button>
                        <button class="btn btn-sm btn-danger">削除</button>
                    </div>
                </div>
                <div class="policy-card-body">
                    <p class="policy-description">
                        高単価商品のラインナップを拡充し、顧客単価の向上を目指します。プレミアムブランドとの提携も検討。
                    </p>
                    <div class="policy-metrics">
                        <div class="policy-metric">
                            <div class="policy-metric-label">影響値</div>
                            <div class="policy-metric-value positive">+12%</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">コスト</div>
                            <div class="policy-metric-value">¥8,000,000</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">期間</div>
                            <div class="policy-metric-value">12ヶ月</div>
                        </div>
                        <div class="policy-metric">
                            <div class="policy-metric-label">ステータス</div>
                            <span class="badge badge-neutral">下書き</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 施策追加モーダル -->
        <div id="policy-modal" class="modal">
            <div class="modal-content modal-lg">
                <div class="modal-header">
                    <h2 class="modal-title">新規施策を追加</h2>
                    <button class="modal-close" onclick="closeModal('policy-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form>
                        <div class="policy-form-grid">
                            <div class="form-group">
                                <label class="form-label">
                                    施策名 <span class="required">*</span>
                                </label>
                                <input type="text" class="form-input" placeholder="施策名を入力してください">
                            </div>
                            <div class="form-group">
                                <label class="form-label">
                                    対象ノード <span class="required">*</span>
                                </label>
                                <select class="form-select">
                                    <option value="">ノードを選択...</option>
                                    <option value="sales">売上高</option>
                                    <option value="customers">顧客数</option>
                                    <option value="new_customers">新規顧客</option>
                                    <option value="existing_customers">既存顧客</option>
                                    <option value="frequency">購入頻度</option>
                                    <option value="price">平均購入額</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">
                                    影響値 (%) <span class="required">*</span>
                                </label>
                                <input type="number" class="form-input" placeholder="例: 15">
                                <div class="form-help">正の値は増加、負の値は減少を表します</div>
                            </div>
                            <div class="form-group">
                                <label class="form-label">
                                    コスト (円)
                                </label>
                                <input type="number" class="form-input" placeholder="例: 5000000">
                            </div>
                            <div class="form-group">
                                <label class="form-label">
                                    実施期間
                                </label>
                                <select class="form-select">
                                    <option value="1">1ヶ月</option>
                                    <option value="3">3ヶ月</option>
                                    <option value="6">6ヶ月</option>
                                    <option value="12">12ヶ月</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">説明</label>
                                <textarea class="form-textarea" placeholder="施策の詳細を入力してください" rows="4"></textarea>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('policy-modal')">キャンセル</button>
                    <button class="btn btn-primary" onclick="closeModal('policy-modal'); showToast('success', '施策を追加しました', '新規施策が正常に作成されました。');">追加</button>
                </div>
            </div>
        </div>
    `,

    // データ紐付け画面
    'tree-data-binding': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#trees">ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#tree-edit">売上ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">データ紐付け</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">データ紐付け</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>🔄</span> データ更新
                </button>
                <button class="btn btn-primary">
                    <span>💾</span> 保存
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab" onclick="navigateTo('tree-edit')">ツリー編集</button>
            <button class="tab" onclick="navigateTo('tree-policies')">施策設定</button>
            <button class="tab active">データ紐付け</button>
            <button class="tab" onclick="navigateTo('tree-results')">計算結果</button>
        </div>

        <div class="alert alert-info mb-5">
            <span class="alert-icon">💡</span>
            <div class="alert-content">
                <div class="alert-title">データ紐付けについて</div>
                <div class="alert-text">各ノードにExcelデータの列を紐付けることで、実データに基づいた計算とシミュレーションが可能になります。</div>
            </div>
        </div>

        <div class="data-binding-grid">
            <!-- データソース選択 -->
            <div class="card mb-5">
                <div class="card-header">
                    <h3 class="card-title">データソース</h3>
                </div>
                <div class="card-body">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">ファイル</label>
                            <select class="form-select">
                                <option value="1" selected>sales_2025q4.xlsx</option>
                                <option value="2">monthly_report.csv</option>
                                <option value="3">customer_data.xlsx</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">シート</label>
                            <select class="form-select">
                                <option value="1" selected>Sheet1 - 売上データ</option>
                                <option value="2">Sheet2 - 商品マスタ</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">期間</label>
                            <select class="form-select">
                                <option value="latest" selected>最新データ</option>
                                <option value="2025q4">2025年Q4</option>
                                <option value="2025q3">2025年Q3</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ノード別紐付け設定 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ノード別データ紐付け</h3>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ノード</th>
                                <th>タイプ</th>
                                <th>データ列</th>
                                <th>集計方法</th>
                                <th>現在値</th>
                                <th>ステータス</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>🎯 売上高</strong></td>
                                <td><span class="badge badge-danger">ルート</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="">（計算値）</option>
                                    </select>
                                </td>
                                <td>-</td>
                                <td class="text-right font-semibold">¥41,500,000</td>
                                <td><span class="badge badge-success">計算済</span></td>
                            </tr>
                            <tr>
                                <td><strong>├─ 顧客数</strong></td>
                                <td><span class="badge badge-info">計算</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="">（計算値）</option>
                                    </select>
                                </td>
                                <td>-</td>
                                <td class="text-right font-semibold">8,300</td>
                                <td><span class="badge badge-success">計算済</span></td>
                            </tr>
                            <tr>
                                <td><strong>│  ├─ 新規顧客</strong></td>
                                <td><span class="badge badge-success">データ</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="">列を選択...</option>
                                        <option value="new_customers" selected>new_customers</option>
                                        <option value="customer_count">customer_count</option>
                                    </select>
                                </td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="sum" selected>合計</option>
                                        <option value="avg">平均</option>
                                        <option value="last">最新</option>
                                    </select>
                                </td>
                                <td class="text-right font-semibold">1,200</td>
                                <td><span class="badge badge-success">紐付済</span></td>
                            </tr>
                            <tr>
                                <td><strong>│  └─ 既存顧客</strong></td>
                                <td><span class="badge badge-success">データ</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="">列を選択...</option>
                                        <option value="existing_customers" selected>existing_customers</option>
                                        <option value="repeat_customers">repeat_customers</option>
                                    </select>
                                </td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="sum" selected>合計</option>
                                        <option value="avg">平均</option>
                                        <option value="last">最新</option>
                                    </select>
                                </td>
                                <td class="text-right font-semibold">7,100</td>
                                <td><span class="badge badge-success">紐付済</span></td>
                            </tr>
                            <tr>
                                <td><strong>└─ 顧客単価</strong></td>
                                <td><span class="badge badge-info">計算</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="">（計算値）</option>
                                    </select>
                                </td>
                                <td>-</td>
                                <td class="text-right font-semibold">¥5,000</td>
                                <td><span class="badge badge-success">計算済</span></td>
                            </tr>
                            <tr>
                                <td><strong>   ├─ 購入頻度</strong></td>
                                <td><span class="badge badge-success">データ</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="">列を選択...</option>
                                        <option value="purchase_frequency" selected>purchase_frequency</option>
                                        <option value="order_count">order_count</option>
                                    </select>
                                </td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="sum">合計</option>
                                        <option value="avg" selected>平均</option>
                                        <option value="last">最新</option>
                                    </select>
                                </td>
                                <td class="text-right font-semibold">2.5回</td>
                                <td><span class="badge badge-success">紐付済</span></td>
                            </tr>
                            <tr>
                                <td><strong>   └─ 平均購入額</strong></td>
                                <td><span class="badge badge-warning">未設定</span></td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="" selected>列を選択...</option>
                                        <option value="avg_purchase">avg_purchase</option>
                                        <option value="order_amount">order_amount</option>
                                    </select>
                                </td>
                                <td>
                                    <select class="form-select form-select-sm">
                                        <option value="sum">合計</option>
                                        <option value="avg">平均</option>
                                        <option value="last">最新</option>
                                    </select>
                                </td>
                                <td class="text-right text-muted">-</td>
                                <td><span class="badge badge-warning">未紐付</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // 計算結果画面
    'tree-results': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#trees">ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#tree-edit">売上ドライバーツリー</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">計算結果</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">計算結果</h1>
            <div class="page-actions">
                <button class="btn btn-secondary">
                    <span>📥</span> エクスポート
                </button>
                <button class="btn btn-primary">
                    <span>🔄</span> 再計算
                </button>
            </div>
        </div>

        <div class="tabs mb-5">
            <button class="tab" onclick="navigateTo('tree-edit')">ツリー編集</button>
            <button class="tab" onclick="navigateTo('tree-policies')">施策設定</button>
            <button class="tab" onclick="navigateTo('tree-data-binding')">データ紐付け</button>
            <button class="tab active">計算結果</button>
        </div>

        <!-- 結果サマリー -->
        <div class="results-summary mb-5">
            <div class="results-summary-card">
                <div class="results-summary-label">現在の売上高</div>
                <div class="results-summary-value">¥41,500,000</div>
                <div class="results-summary-change neutral">基準値</div>
            </div>
            <div class="results-summary-card">
                <div class="results-summary-label">施策適用後</div>
                <div class="results-summary-value">¥48,130,000</div>
                <div class="results-summary-change positive">+16.0%</div>
            </div>
            <div class="results-summary-card">
                <div class="results-summary-label">増加額</div>
                <div class="results-summary-value">¥6,630,000</div>
                <div class="results-summary-change positive">+¥6.6M</div>
            </div>
            <div class="results-summary-card">
                <div class="results-summary-label">施策コスト合計</div>
                <div class="results-summary-value">¥15,000,000</div>
                <div class="results-summary-change">3施策</div>
            </div>
        </div>

        <div class="results-grid">
            <!-- 計算結果テーブル -->
            <div class="card mb-5">
                <div class="card-header">
                    <h3 class="card-title">ノード別計算結果</h3>
                </div>
                <div class="card-body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ノード</th>
                                <th class="text-right">現在値</th>
                                <th class="text-right">施策後</th>
                                <th class="text-right">変化率</th>
                                <th>適用施策</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="font-semibold" style="background-color: var(--color-primary-50);">
                                <td>🎯 売上高</td>
                                <td class="text-right">¥41,500,000</td>
                                <td class="text-right">¥48,130,000</td>
                                <td class="text-right text-success">+16.0%</td>
                                <td>-</td>
                            </tr>
                            <tr>
                                <td>├─ 顧客数</td>
                                <td class="text-right">8,300</td>
                                <td class="text-right">9,545</td>
                                <td class="text-right text-success">+15.0%</td>
                                <td><span class="badge badge-info">新規顧客獲得</span></td>
                            </tr>
                            <tr>
                                <td>│  ├─ 新規顧客</td>
                                <td class="text-right">1,200</td>
                                <td class="text-right">1,380</td>
                                <td class="text-right text-success">+15.0%</td>
                                <td><span class="badge badge-info">新規顧客獲得</span></td>
                            </tr>
                            <tr>
                                <td>│  └─ 既存顧客</td>
                                <td class="text-right">7,100</td>
                                <td class="text-right">8,165</td>
                                <td class="text-right text-success">+15.0%</td>
                                <td>-</td>
                            </tr>
                            <tr>
                                <td>└─ 顧客単価</td>
                                <td class="text-right">¥5,000</td>
                                <td class="text-right">¥5,040</td>
                                <td class="text-right text-success">+0.8%</td>
                                <td>-</td>
                            </tr>
                            <tr>
                                <td>   ├─ 購入頻度</td>
                                <td class="text-right">2.5回</td>
                                <td class="text-right">2.7回</td>
                                <td class="text-right text-success">+8.0%</td>
                                <td><span class="badge badge-info">リピート促進</span></td>
                            </tr>
                            <tr>
                                <td>   └─ 平均購入額</td>
                                <td class="text-right">¥2,000</td>
                                <td class="text-right">¥2,000</td>
                                <td class="text-right">0%</td>
                                <td>-</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 施策効果比較 -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">施策効果比較</h3>
                </div>
                <div class="card-body">
                    <div class="policy-effect-list">
                        <div class="policy-effect-item">
                            <div class="policy-effect-header">
                                <div class="policy-effect-name">📈 新規顧客獲得キャンペーン</div>
                                <div class="policy-effect-impact positive">+¥3,225,000</div>
                            </div>
                            <div class="policy-effect-bar">
                                <div class="policy-effect-bar-fill" style="width: 48.6%; background-color: var(--color-success-500);"></div>
                            </div>
                            <div class="policy-effect-meta">
                                <span>コスト: ¥5,000,000</span>
                                <span>ROI: 64.5%</span>
                            </div>
                        </div>
                        <div class="policy-effect-item">
                            <div class="policy-effect-header">
                                <div class="policy-effect-name">🔄 リピート購入促進プログラム</div>
                                <div class="policy-effect-impact positive">+¥2,075,000</div>
                            </div>
                            <div class="policy-effect-bar">
                                <div class="policy-effect-bar-fill" style="width: 31.3%; background-color: var(--color-success-500);"></div>
                            </div>
                            <div class="policy-effect-meta">
                                <span>コスト: ¥2,000,000</span>
                                <span>ROI: 103.8%</span>
                            </div>
                        </div>
                        <div class="policy-effect-item">
                            <div class="policy-effect-header">
                                <div class="policy-effect-name">💰 プレミアム商品ラインナップ拡充</div>
                                <div class="policy-effect-impact positive">+¥1,330,000</div>
                            </div>
                            <div class="policy-effect-bar">
                                <div class="policy-effect-bar-fill" style="width: 20.1%; background-color: var(--color-success-500);"></div>
                            </div>
                            <div class="policy-effect-meta">
                                <span>コスト: ¥8,000,000</span>
                                <span>ROI: 16.6%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
};