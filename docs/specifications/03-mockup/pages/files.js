// ========================================
// File Management Pages
// ========================================

const filePages = {
    // ファイル一覧
    files: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#projects">プロジェクト一覧</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">売上分析プロジェクト</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">ファイル管理</span>
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
            <div class="card-body">
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

                <div class="table-container">
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
                                    <div class="d-flex items-center gap-2">
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
                                    <div class="d-flex items-center gap-2">
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
                                    <div class="d-flex items-center gap-2">
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
            </div>
        </div>
    `,

    // アップロード
    upload: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
            <span class="breadcrumb-separator">/</span>
            <a href="#files">ファイル管理</a>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">アップロード</span>
        </div>
        <div class="page-header">
            <h1 class="page-title">ファイルアップロード</h1>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="file-upload">
                    <div class="file-upload-icon">📁</div>
                    <div class="file-upload-text">
                        ファイルをドラッグ＆ドロップ<br>
                        または
                    </div>
                    <button class="btn btn-primary mt-3">ファイルを選択</button>
                    <div class="file-upload-hint">
                        対応フォーマット: Excel (.xlsx, .xls), CSV (.csv), JSON (.json)<br>
                        最大ファイルサイズ: 50MB
                    </div>
                </div>

                <!-- アップロード中のファイル -->
                <div class="mt-5">
                    <h4 class="mb-3">アップロード中</h4>
                    <div class="p-3 rounded-lg" style="background-color: var(--color-neutral-50);">
                        <div class="d-flex justify-between items-center mb-2">
                            <span>new_data.xlsx</span>
                            <span class="text-sm">75%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar" style="width: 75%;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
};
