// ========================================
// Dashboard Pages
// ========================================

const dashboardPages = {
    // ダッシュボード
    dashboard: `
        <div class="breadcrumb">
            <a href="#dashboard">ホーム</a>
        </div>
        <div class="page-header">
            <h1 class="page-title">ダッシュボード</h1>
            <div class="page-actions">
                <select class="form-select" style="width: 150px;">
                    <option value="7">過去7日間</option>
                    <option value="30" selected>過去30日間</option>
                    <option value="90">過去90日間</option>
                </select>
            </div>
        </div>

        <!-- 統計カード -->
        <div class="stats-grid mb-6">
            <div class="stat-card stat-card-icon">
                <div class="stat-icon" style="background-color: var(--color-primary-100); color: var(--color-primary-600);">📁</div>
                <div class="stat-body">
                    <div class="stat-label">参加プロジェクト</div>
                    <div class="stat-value">12</div>
                    <div class="stat-change positive">
                        <span>↑</span> +2 今月
                    </div>
                </div>
            </div>
            <div class="stat-card stat-card-icon">
                <div class="stat-icon" style="background-color: var(--color-success-100); color: var(--color-success-600);">📊</div>
                <div class="stat-body">
                    <div class="stat-label">進行中セッション</div>
                    <div class="stat-value">5</div>
                    <div class="stat-change neutral">
                        アクティブ
                    </div>
                </div>
            </div>
            <div class="stat-card stat-card-icon">
                <div class="stat-icon" style="background-color: var(--color-warning-100); color: var(--color-warning-600);">🌳</div>
                <div class="stat-body">
                    <div class="stat-label">ドライバーツリー</div>
                    <div class="stat-value">8</div>
                    <div class="stat-change positive">
                        <span>↑</span> +1 今週
                    </div>
                </div>
            </div>
            <div class="stat-card stat-card-icon">
                <div class="stat-icon" style="background-color: var(--color-info-100); color: var(--color-info-600);">📄</div>
                <div class="stat-body">
                    <div class="stat-label">アップロードファイル</div>
                    <div class="stat-value">47</div>
                    <div class="stat-change neutral">
                        合計
                    </div>
                </div>
            </div>
        </div>

        <!-- チャートセクション -->
        <div class="dashboard-charts">
            <!-- 分析アクティビティチャート -->
            <div class="card chart-card">
                <div class="card-header">
                    <h3 class="card-title">分析アクティビティ</h3>
                    <div class="chart-legend">
                        <span class="legend-item"><span class="legend-dot" style="background-color: var(--color-primary-500);"></span> セッション</span>
                        <span class="legend-item"><span class="legend-dot" style="background-color: var(--color-success-500);"></span> スナップショット</span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <!-- 簡易バーチャート -->
                        <div class="bar-chart">
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/19</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 40%;"></div>
                                    <div class="bar bar-success" style="width: 60%;"></div>
                                </div>
                                <div class="bar-chart-value">4 / 6</div>
                            </div>
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/20</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 60%;"></div>
                                    <div class="bar bar-success" style="width: 80%;"></div>
                                </div>
                                <div class="bar-chart-value">6 / 8</div>
                            </div>
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/21</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 30%;"></div>
                                    <div class="bar bar-success" style="width: 50%;"></div>
                                </div>
                                <div class="bar-chart-value">3 / 5</div>
                            </div>
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/22</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 20%;"></div>
                                    <div class="bar bar-success" style="width: 30%;"></div>
                                </div>
                                <div class="bar-chart-value">2 / 3</div>
                            </div>
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/23</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 50%;"></div>
                                    <div class="bar bar-success" style="width: 70%;"></div>
                                </div>
                                <div class="bar-chart-value">5 / 7</div>
                            </div>
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/24</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 80%;"></div>
                                    <div class="bar bar-success" style="width: 100%;"></div>
                                </div>
                                <div class="bar-chart-value">8 / 10</div>
                            </div>
                            <div class="bar-chart-row">
                                <div class="bar-chart-label">12/25</div>
                                <div class="bar-chart-bars">
                                    <div class="bar bar-primary" style="width: 70%;"></div>
                                    <div class="bar bar-success" style="width: 90%;"></div>
                                </div>
                                <div class="bar-chart-value">7 / 9</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- プロジェクト進捗 -->
            <div class="card chart-card">
                <div class="card-header">
                    <h3 class="card-title">プロジェクト進捗</h3>
                </div>
                <div class="card-body">
                    <div class="progress-list">
                        <div class="progress-item">
                            <div class="progress-item-header">
                                <span class="progress-item-name">売上分析プロジェクト</span>
                                <span class="progress-item-value">75%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar" style="width: 75%; background-color: var(--color-success-500);"></div>
                            </div>
                        </div>
                        <div class="progress-item">
                            <div class="progress-item-header">
                                <span class="progress-item-name">コスト削減プロジェクト</span>
                                <span class="progress-item-value">45%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar" style="width: 45%; background-color: var(--color-primary-500);"></div>
                            </div>
                        </div>
                        <div class="progress-item">
                            <div class="progress-item-header">
                                <span class="progress-item-name">新規事業分析</span>
                                <span class="progress-item-value">20%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar" style="width: 20%; background-color: var(--color-warning-500);"></div>
                            </div>
                        </div>
                        <div class="progress-item">
                            <div class="progress-item-header">
                                <span class="progress-item-name">顧客分析プロジェクト</span>
                                <span class="progress-item-value">90%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar" style="width: 90%; background-color: var(--color-success-500);"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 下部セクション -->
        <div class="dashboard-bottom">
            <!-- 最近のアクティビティ -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近のアクティビティ</h3>
                    <a href="#" class="btn btn-link btn-sm">すべて見る</a>
                </div>
                <div class="card-body p-0">
                    <div class="activity-list">
                        <div class="activity-item">
                            <div class="activity-icon" style="background-color: var(--color-primary-100);">📊</div>
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>山田 太郎</strong>が<strong>Q4売上分析</strong>セッションを作成しました
                                </div>
                                <div class="activity-time">5分前 • 売上分析プロジェクト</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-icon" style="background-color: var(--color-success-100);">🌳</div>
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>鈴木 花子</strong>が<strong>売上ドライバーツリー</strong>を更新しました
                                </div>
                                <div class="activity-time">15分前 • 売上分析プロジェクト</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-icon" style="background-color: var(--color-info-100);">📄</div>
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>田中 一郎</strong>が<strong>monthly_report.csv</strong>をアップロードしました
                                </div>
                                <div class="activity-time">1時間前 • コスト削減プロジェクト</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-icon" style="background-color: var(--color-warning-100);">👥</div>
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>佐藤 次郎</strong>が<strong>新規事業分析</strong>プロジェクトに参加しました
                                </div>
                                <div class="activity-time">3時間前 • 新規事業分析</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-icon" style="background-color: var(--color-success-100);">✅</div>
                            <div class="activity-content">
                                <div class="activity-text">
                                    <strong>山田 太郎</strong>が<strong>コスト分析</strong>セッションを完了しました
                                </div>
                                <div class="activity-time">5時間前 • コスト削減プロジェクト</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- クイックアクセス -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">クイックアクセス</h3>
                </div>
                <div class="card-body">
                    <div class="quick-actions">
                        <a href="#project-new" class="quick-action-item" onclick="navigateTo('project-new'); return false;">
                            <div class="quick-action-icon">📁</div>
                            <div class="quick-action-text">新規プロジェクト</div>
                        </a>
                        <a href="#session-new" class="quick-action-item" onclick="navigateTo('session-new'); return false;">
                            <div class="quick-action-icon">📊</div>
                            <div class="quick-action-text">分析開始</div>
                        </a>
                        <a href="#tree-new" class="quick-action-item" onclick="navigateTo('tree-new'); return false;">
                            <div class="quick-action-icon">🌳</div>
                            <div class="quick-action-text">ツリー作成</div>
                        </a>
                        <a href="#upload" class="quick-action-item" onclick="navigateTo('upload'); return false;">
                            <div class="quick-action-icon">⬆️</div>
                            <div class="quick-action-text">ファイルアップロード</div>
                        </a>
                    </div>

                    <div class="divider"></div>

                    <h4 class="text-sm font-semibold mb-3">最近のプロジェクト</h4>
                    <div class="recent-projects">
                        <a href="#" class="recent-project-item" onclick="navigateTo('sessions'); return false;">
                            <div class="recent-project-icon">📁</div>
                            <div class="recent-project-info">
                                <div class="recent-project-name">売上分析プロジェクト</div>
                                <div class="recent-project-meta">5人のメンバー • 更新: 10分前</div>
                            </div>
                        </a>
                        <a href="#" class="recent-project-item" onclick="navigateTo('sessions'); return false;">
                            <div class="recent-project-icon">📁</div>
                            <div class="recent-project-info">
                                <div class="recent-project-name">コスト削減プロジェクト</div>
                                <div class="recent-project-meta">3人のメンバー • 更新: 2時間前</div>
                            </div>
                        </a>
                        <a href="#" class="recent-project-item" onclick="navigateTo('sessions'); return false;">
                            <div class="recent-project-icon">📁</div>
                            <div class="recent-project-info">
                                <div class="recent-project-name">新規事業分析</div>
                                <div class="recent-project-meta">4人のメンバー • 更新: 1日前</div>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `,
};
