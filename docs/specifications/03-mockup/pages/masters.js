// ========================================
// Master Data Management Pages
// ========================================

const masterPages = {
    // カテゴリマスタ管理
    categories: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">ドライバーツリー</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">カテゴリマスタ管理</span>
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
            <div class="card-body">
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

                <div class="table-container">
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
                                    <button class="btn btn-sm btn-secondary" onclick="navigateTo('category-edit')">編集</button>
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
                                    <button class="btn btn-sm btn-secondary" onclick="navigateTo('category-edit')">編集</button>
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
                                    <button class="btn btn-sm btn-secondary" onclick="navigateTo('category-edit')">編集</button>
                                    <button class="btn btn-sm btn-danger">削除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // カテゴリマスタ編集画面
    'category-edit': `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#categories">カテゴリマスタ管理</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上分解モデル v2</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">カテゴリマスタ編集: 売上分解モデル v2</h1>
            <div class="page-actions">
                <button class="btn btn-secondary" onclick="navigateTo('categories')">キャンセル</button>
                <button class="btn btn-primary" onclick="showToast('success', '保存しました', 'カテゴリマスタが更新されました。')">
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
                            <label class="form-label">カテゴリ名 <span class="required">*</span></label>
                            <input type="text" class="form-input" value="売上分解モデル v2">
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">業界分類 <span class="required">*</span></label>
                                <select class="form-select">
                                    <option value="all" selected>全業種共通</option>
                                    <option value="manufacturing">製造業</option>
                                    <option value="retail">小売業</option>
                                    <option value="service">サービス業</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">ドライバータイプ <span class="required">*</span></label>
                                <select class="form-select">
                                    <option value="revenue" selected>Revenue</option>
                                    <option value="cost">Cost</option>
                                    <option value="profit">Profit</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">説明</label>
                            <textarea class="form-textarea" rows="3">売上を顧客数と顧客単価に分解し、さらに細分化するための標準モデルです。多くの業種で利用可能な汎用的な構造を持っています。</textarea>
                        </div>
                    </div>
                </div>

                <!-- 含まれる数式 -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">含まれる数式 (5)</h3>
                        <button class="btn btn-sm btn-primary">
                            <span>➕</span> 数式を追加
                        </button>
                    </div>
                    <div class="card-body p-0">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>順序</th>
                                    <th>KPI</th>
                                    <th>計算式</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>1</td>
                                    <td><strong>売上高</strong></td>
                                    <td><code style="background: var(--color-neutral-100); padding: 2px 6px; border-radius: 4px;">顧客数 × 顧客単価</code></td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-secondary">編集</button>
                                        <button class="btn btn-sm btn-danger">削除</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>2</td>
                                    <td><strong>顧客数</strong></td>
                                    <td><code style="background: var(--color-neutral-100); padding: 2px 6px; border-radius: 4px;">新規顧客 + 既存顧客</code></td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-secondary">編集</button>
                                        <button class="btn btn-sm btn-danger">削除</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>3</td>
                                    <td><strong>顧客単価</strong></td>
                                    <td><code style="background: var(--color-neutral-100); padding: 2px 6px; border-radius: 4px;">購入頻度 × 平均購入額</code></td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-secondary">編集</button>
                                        <button class="btn btn-sm btn-danger">削除</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>4</td>
                                    <td><strong>新規顧客</strong></td>
                                    <td><code style="background: var(--color-neutral-100); padding: 2px 6px; border-radius: 4px;">（リーフノード）</code></td>
                                    <td class="actions">
                                        <button class="btn btn-sm btn-secondary">編集</button>
                                        <button class="btn btn-sm btn-danger">削除</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>5</td>
                                    <td><strong>既存顧客</strong></td>
                                    <td><code style="background: var(--color-neutral-100); padding: 2px 6px; border-radius: 4px;">（リーフノード）</code></td>
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

            <!-- サイドバー -->
            <div class="issue-sidebar">
                <div class="card issue-settings-card">
                    <div class="card-header">
                        <h3 class="card-title">メタ情報</h3>
                    </div>
                    <div class="card-body">
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">作成日</span>
                            <span class="issue-setting-value">2025/09/15</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">更新日</span>
                            <span class="issue-setting-value">2025/12/20</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">作成者</span>
                            <span class="issue-setting-value">管理者 太郎</span>
                        </div>
                        <div class="issue-setting-row">
                            <span class="issue-setting-label">使用ツリー数</span>
                            <span class="issue-setting-value">12</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">ツリー構造プレビュー</h3>
                    </div>
                    <div class="card-body">
                        <div style="font-family: var(--font-family-mono); font-size: var(--font-size-xs); line-height: 1.8;">
                            <div>📊 売上高</div>
                            <div style="padding-left: 16px;">├─ 👥 顧客数</div>
                            <div style="padding-left: 32px;">├─ 🆕 新規顧客</div>
                            <div style="padding-left: 32px;">└─ 🔄 既存顧客</div>
                            <div style="padding-left: 16px;">└─ 💰 顧客単価</div>
                            <div style="padding-left: 32px;">├─ 📈 購入頻度</div>
                            <div style="padding-left: 32px;">└─ 💵 平均購入額</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
};