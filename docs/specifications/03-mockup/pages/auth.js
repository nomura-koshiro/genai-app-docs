// ========================================
// Authentication Pages
// ========================================

const authPages = {
    // ログイン画面
    login: `
        <div class="login-page">
            <div class="login-container">
                <div class="login-card">
                    <!-- ロゴセクション -->
                    <div class="login-header">
                        <div class="login-logo">
                            <div class="logo-icon">
                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                                    <rect width="48" height="48" rx="12" fill="var(--color-primary-600)"/>
                                    <path d="M14 24C14 18.477 18.477 14 24 14V14C29.523 14 34 18.477 34 24V24C34 29.523 29.523 34 24 34V34" stroke="white" stroke-width="3" stroke-linecap="round"/>
                                    <circle cx="24" cy="24" r="4" fill="white"/>
                                </svg>
                            </div>
                            <h1 class="login-title">CAMP</h1>
                        </div>
                        <p class="login-subtitle">Collaborative Analysis & Management Platform</p>
                    </div>

                    <!-- ログインボタンセクション -->
                    <div class="login-body">
                        <div class="login-description">
                            <p>データ分析・ドライバーツリー管理のための統合プラットフォームです。</p>
                            <p>組織のMicrosoftアカウントでログインしてください。</p>
                        </div>

                        <button class="btn-azure-login" onclick="demoLogin()">
                            <svg width="20" height="20" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
                                <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                                <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                                <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                                <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                            </svg>
                            <span>Microsoftアカウントでログイン</span>
                        </button>

                        <div class="login-info">
                            <div class="login-info-item">
                                <span class="info-icon">🔒</span>
                                <span>Azure Active Directory認証を使用</span>
                            </div>
                            <div class="login-info-item">
                                <span class="info-icon">🏢</span>
                                <span>組織のアカウントのみアクセス可能</span>
                            </div>
                        </div>
                    </div>

                    <!-- フッター -->
                    <div class="login-footer">
                        <p>&copy; 2025 CAMP System. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    // ログアウト完了画面
    logout: `
        <div class="login-page">
            <div class="login-container">
                <div class="login-card">
                    <div class="login-header">
                        <div class="login-logo">
                            <div class="logo-icon">
                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                                    <rect width="48" height="48" rx="12" fill="var(--color-primary-600)"/>
                                    <path d="M14 24C14 18.477 18.477 14 24 14V14C29.523 14 34 18.477 34 24V24C34 29.523 29.523 34 24 34V34" stroke="white" stroke-width="3" stroke-linecap="round"/>
                                    <circle cx="24" cy="24" r="4" fill="white"/>
                                </svg>
                            </div>
                            <h1 class="login-title">CAMP</h1>
                        </div>
                    </div>

                    <div class="login-body">
                        <div class="logout-message">
                            <div class="logout-icon">✓</div>
                            <h2>ログアウトしました</h2>
                            <p>セッションが正常に終了しました。</p>
                        </div>

                        <button class="btn-azure-login" onclick="navigateTo('login')">
                            <svg width="20" height="20" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
                                <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                                <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                                <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                                <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                            </svg>
                            <span>再度ログイン</span>
                        </button>
                    </div>

                    <div class="login-footer">
                        <p>&copy; 2025 CAMP System. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    // 認証エラー画面
    'auth-error': `
        <div class="login-page">
            <div class="login-container">
                <div class="login-card">
                    <div class="login-header">
                        <div class="login-logo">
                            <div class="logo-icon">
                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                                    <rect width="48" height="48" rx="12" fill="var(--color-primary-600)"/>
                                    <path d="M14 24C14 18.477 18.477 14 24 14V14C29.523 14 34 18.477 34 24V24C34 29.523 29.523 34 24 34V34" stroke="white" stroke-width="3" stroke-linecap="round"/>
                                    <circle cx="24" cy="24" r="4" fill="white"/>
                                </svg>
                            </div>
                            <h1 class="login-title">CAMP</h1>
                        </div>
                    </div>

                    <div class="login-body">
                        <div class="error-message">
                            <div class="error-icon">⚠️</div>
                            <h2>認証エラー</h2>
                            <p>ログイン中にエラーが発生しました。</p>
                            <ul class="error-details">
                                <li>組織のアカウントでログインしているか確認してください</li>
                                <li>アクセス権限がない場合は管理者にお問い合わせください</li>
                                <li>問題が続く場合はサポートにご連絡ください</li>
                            </ul>
                        </div>

                        <button class="btn-azure-login" onclick="navigateTo('login')">
                            <svg width="20" height="20" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
                                <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                                <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                                <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                                <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                            </svg>
                            <span>再度ログインを試す</span>
                        </button>

                        <a href="mailto:support@example.com" class="support-link">サポートに問い合わせる</a>
                    </div>

                    <div class="login-footer">
                        <p>&copy; 2025 CAMP System. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </div>
    `,
};
