// ========================================
// CAMPシステム ワイヤーフレーム アプリケーション
// ========================================

// 現在のページ
let currentPage = 'dashboard';

// ========================================
// ページ遷移
// ========================================

function navigateTo(page) {
    // メニューのアクティブ状態を更新
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });

    // ページコンテンツを更新
    const pageContent = document.getElementById('page-content');
    if (pageTemplates[page]) {
        pageContent.innerHTML = pageTemplates[page];
        currentPage = page;

        // URLハッシュを更新
        window.location.hash = page;

        // タブの初期化
        initTabs();

        // レイアウト更新（ログイン画面対応）
        updateLayout(page);
    } else {
        pageContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🚧</div>
                <div class="empty-state-title">ページが見つかりません</div>
                <div class="empty-state-text">このページは準備中です。</div>
                <button class="btn btn-primary" onclick="navigateTo('dashboard')">ダッシュボードに戻る</button>
            </div>
        `;
    }

    // ページトップにスクロール
    window.scrollTo(0, 0);

    // 全てのドロップダウンを閉じる
    closeAllDropdowns();
}

// ========================================
// モーダル
// ========================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ========================================
// タブ
// ========================================

function initTabs() {
    document.querySelectorAll('.tabs').forEach(tabsContainer => {
        const tabs = tabsContainer.querySelectorAll('.tab');
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', function() {
                // タブのアクティブ状態を更新
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // タブコンテンツの表示を更新（もしあれば）
                // まず親要素から探し、見つからなければページ全体から探す
                let tabContents = tabsContainer.parentElement.querySelectorAll(':scope > .tab-content');
                if (tabContents.length === 0) {
                    // 親要素の直下になければ、より広い範囲で検索
                    const pageContent = document.getElementById('page-content');
                    if (pageContent) {
                        tabContents = pageContent.querySelectorAll('.tab-content');
                    }
                }
                if (tabContents.length > 0) {
                    tabContents.forEach(content => content.classList.remove('active'));
                    if (tabContents[index]) {
                        tabContents[index].classList.add('active');
                    }
                }
            });
        });
    });
}

// ========================================
// ドロップダウン
// ========================================

function toggleDropdown(panelId) {
    const panel = document.getElementById(panelId);
    if (panel) {
        const isActive = panel.classList.contains('active');
        closeAllDropdowns();
        if (!isActive) {
            panel.classList.add('active');
        }
    }
}

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-panel').forEach(panel => {
        panel.classList.remove('active');
    });
}

// ========================================
// トースト通知
// ========================================

function showToast(type, title, message, duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '✅',
        warning: '⚠️',
        danger: '❌',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast(this)">&times;</button>
    `;

    container.appendChild(toast);

    // 自動削除
    if (duration > 0) {
        setTimeout(() => {
            closeToast(toast.querySelector('.toast-close'));
        }, duration);
    }
}

function closeToast(button) {
    const toast = button.closest('.toast');
    if (toast) {
        toast.classList.add('hiding');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// ========================================
// ローディング
// ========================================

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// ========================================
// 確認ダイアログ
// ========================================

function confirmDialog(title, message, onConfirm) {
    if (confirm(`${title}\n\n${message}`)) {
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    }
}

// ========================================
// デモ用アクション
// ========================================

function demoAction(action, itemName) {
    switch (action) {
        case 'delete':
            confirmDialog(
                '削除の確認',
                `「${itemName}」を削除してもよろしいですか？`,
                () => showToast('success', '削除完了', `「${itemName}」を削除しました。`)
            );
            break;
        case 'save':
            showLoading();
            setTimeout(() => {
                hideLoading();
                showToast('success', '保存完了', `${itemName}を保存しました。`);
            }, 1000);
            break;
        case 'copy':
            showToast('success', 'コピー完了', `「${itemName}」を複製しました。`);
            break;
        default:
            showToast('info', 'アクション', `${action}: ${itemName}`);
    }
}

// ========================================
// ログイン画面用
// ========================================

function demoLogin() {
    showLoading();
    setTimeout(() => {
        hideLoading();
        showToast('success', 'ログイン成功', 'Microsoftアカウントでログインしました。');
        navigateTo('dashboard');
    }, 1500);
}

// ========================================
// レイアウト制御（ログイン画面用）
// ========================================

function updateLayout(page) {
    const header = document.querySelector('.header');
    const sidebar = document.getElementById('sidebar');
    const mainContainer = document.querySelector('.main-container');
    const footer = document.querySelector('.footer');

    // ログイン関連ページではヘッダー・サイドバー・フッターを非表示
    const authPages = ['login', 'logout', 'auth-error'];
    const isAuthPage = authPages.includes(page);

    if (header) header.style.display = isAuthPage ? 'none' : '';
    if (sidebar) sidebar.style.display = isAuthPage ? 'none' : '';
    if (footer) footer.style.display = isAuthPage ? 'none' : '';
    if (mainContainer) {
        if (isAuthPage) {
            mainContainer.style.marginTop = '0';
            mainContainer.style.minHeight = '100vh';
        } else {
            mainContainer.style.marginTop = '';
            mainContainer.style.minHeight = '';
        }
    }

    // メインコンテンツのmarginを調整
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        if (isAuthPage) {
            mainContent.style.marginLeft = '0';
            mainContent.style.padding = '0';
        } else {
            mainContent.style.marginLeft = '';
            mainContent.style.padding = '';
        }
    }
}

// ========================================
// グローバル検索
// ========================================

// サンプル検索データ
const searchData = {
    projects: [
        { id: 1, name: '売上分析プロジェクト', meta: '3名のメンバー • 作成: 2025/12/01', page: 'project-detail' },
        { id: 2, name: 'コスト削減プロジェクト', meta: '5名のメンバー • 作成: 2025/11/15', page: 'project-detail' },
        { id: 3, name: 'Q4業績分析', meta: '2名のメンバー • 作成: 2025/10/20', page: 'project-detail' },
        { id: 4, name: '新規事業計画', meta: '4名のメンバー • 作成: 2025/09/05', page: 'project-detail' },
    ],
    sessions: [
        { id: 1, name: 'Q4売上分析セッション', meta: '売上分析プロジェクト • 完了', page: 'session-detail' },
        { id: 2, name: '月次レポート作成', meta: 'コスト削減プロジェクト • 処理中', page: 'session-detail' },
        { id: 3, name: '年間予測分析', meta: 'Q4業績分析 • 処理中', page: 'session-detail' },
        { id: 4, name: '競合分析セッション', meta: '新規事業計画 • 完了', page: 'session-detail' },
    ],
    files: [
        { id: 1, name: 'sales_data_2024.xlsx', meta: '売上分析プロジェクト • 2.3MB', page: 'files' },
        { id: 2, name: 'cost_report_q4.csv', meta: 'コスト削減プロジェクト • 1.1MB', page: 'files' },
        { id: 3, name: '業績データ_2024.xlsx', meta: 'Q4業績分析 • 4.5MB', page: 'files' },
        { id: 4, name: 'market_analysis.pdf', meta: '新規事業計画 • 8.2MB', page: 'files' },
    ],
    trees: [
        { id: 1, name: '売上ドライバーツリー', meta: '売上分析プロジェクト • 12ノード', page: 'tree-edit' },
        { id: 2, name: 'コスト構造ツリー', meta: 'コスト削減プロジェクト • 8ノード', page: 'tree-edit' },
        { id: 3, name: '利益分析ツリー', meta: 'Q4業績分析 • 15ノード', page: 'tree-edit' },
    ]
};

const searchConfig = {
    projects: { icon: '📁', label: 'プロジェクト', iconClass: 'project' },
    sessions: { icon: '💬', label: 'セッション', iconClass: 'session' },
    files: { icon: '📄', label: 'ファイル', iconClass: 'file' },
    trees: { icon: '🌳', label: 'ドライバーツリー', iconClass: 'tree' }
};

let searchSelectedIndex = -1;
let searchResults = [];

function initGlobalSearch() {
    const searchInput = document.getElementById('global-search-input');
    const searchDropdown = document.getElementById('search-dropdown');
    const headerSearch = document.getElementById('header-search');

    if (!searchInput || !searchDropdown) return;

    // 入力イベント
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length >= 1) {
            performSearch(query);
            showSearchDropdown();
        } else {
            hideSearchDropdown();
        }
    });

    // フォーカスイベント
    searchInput.addEventListener('focus', function() {
        if (this.value.trim().length >= 1) {
            showSearchDropdown();
        }
    });

    // キーボードナビゲーション
    searchInput.addEventListener('keydown', function(e) {
        if (!searchDropdown.classList.contains('active')) {
            if (e.key === 'ArrowDown' && this.value.trim().length >= 1) {
                performSearch(this.value.trim());
                showSearchDropdown();
                e.preventDefault();
            }
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                navigateSearchResults(1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                navigateSearchResults(-1);
                break;
            case 'Enter':
                e.preventDefault();
                selectSearchResult();
                break;
            case 'Escape':
                hideSearchDropdown();
                searchInput.blur();
                break;
        }
    });

    // 外部クリックで閉じる
    document.addEventListener('click', function(e) {
        if (!headerSearch.contains(e.target)) {
            hideSearchDropdown();
        }
    });

    // Ctrl+K ショートカット
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    });
}

function performSearch(query) {
    const lowerQuery = query.toLowerCase();
    searchResults = [];
    searchSelectedIndex = -1;

    // 各カテゴリで検索
    Object.keys(searchData).forEach(category => {
        const matches = searchData[category].filter(item =>
            item.name.toLowerCase().includes(lowerQuery) ||
            item.meta.toLowerCase().includes(lowerQuery)
        );
        matches.forEach(item => {
            searchResults.push({ ...item, category });
        });
    });

    renderSearchResults(query);
}

function renderSearchResults(query) {
    const searchResultsContainer = document.getElementById('search-results');
    const searchEmpty = document.getElementById('search-empty');
    const searchResultCount = document.getElementById('search-result-count');

    if (searchResults.length === 0) {
        searchResultsContainer.innerHTML = '';
        searchResultsContainer.style.display = 'none';
        searchEmpty.style.display = 'block';
        searchResultCount.textContent = '0件';
        return;
    }

    searchEmpty.style.display = 'none';
    searchResultsContainer.style.display = 'block';
    searchResultCount.textContent = `${searchResults.length}件`;

    // カテゴリ別にグループ化
    const grouped = {};
    searchResults.forEach((item, index) => {
        if (!grouped[item.category]) {
            grouped[item.category] = [];
        }
        grouped[item.category].push({ ...item, globalIndex: index });
    });

    let html = '';
    Object.keys(grouped).forEach(category => {
        const config = searchConfig[category];
        html += `
            <div class="search-result-group">
                <div class="search-result-group-title">${config.label}</div>
                ${grouped[category].map(item => `
                    <div class="search-result-item" data-index="${item.globalIndex}" data-page="${item.page}">
                        <div class="search-result-icon ${config.iconClass}">${config.icon}</div>
                        <div class="search-result-content">
                            <div class="search-result-name">${highlightMatch(item.name, query)}</div>
                            <div class="search-result-meta">${item.meta}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    });

    searchResultsContainer.innerHTML = html;

    // クリックイベント
    searchResultsContainer.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            navigateTo(page);
            hideSearchDropdown();
            document.getElementById('global-search-input').value = '';
        });
    });
}

function highlightMatch(text, query) {
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function navigateSearchResults(direction) {
    const items = document.querySelectorAll('.search-result-item');
    if (items.length === 0) return;

    // 現在の選択を解除
    if (searchSelectedIndex >= 0 && items[searchSelectedIndex]) {
        items[searchSelectedIndex].classList.remove('selected');
    }

    // 新しいインデックスを計算
    searchSelectedIndex += direction;
    if (searchSelectedIndex < 0) {
        searchSelectedIndex = items.length - 1;
    } else if (searchSelectedIndex >= items.length) {
        searchSelectedIndex = 0;
    }

    // 新しい選択を適用
    items[searchSelectedIndex].classList.add('selected');
    items[searchSelectedIndex].scrollIntoView({ block: 'nearest' });
}

function selectSearchResult() {
    const items = document.querySelectorAll('.search-result-item');
    if (searchSelectedIndex >= 0 && items[searchSelectedIndex]) {
        const page = items[searchSelectedIndex].dataset.page;
        navigateTo(page);
        hideSearchDropdown();
        document.getElementById('global-search-input').value = '';
    }
}

function showSearchDropdown() {
    const dropdown = document.getElementById('search-dropdown');
    if (dropdown) {
        dropdown.classList.add('active');
    }
}

function hideSearchDropdown() {
    const dropdown = document.getElementById('search-dropdown');
    if (dropdown) {
        dropdown.classList.remove('active');
    }
    searchSelectedIndex = -1;
}

// ========================================
// 初期化
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // URLハッシュからページを取得
    const hash = window.location.hash.slice(1);
    const initialPage = hash && pageTemplates[hash] ? hash : 'dashboard';

    // 初期ページを表示
    navigateTo(initialPage);

    // グローバル検索の初期化
    initGlobalSearch();

    // サイドバーのクリックイベント
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            if (page) {
                navigateTo(page);
            }
        });
    });

    // モーダル外クリックで閉じる
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('active');
            document.body.style.overflow = '';
        }
    });

    // ドロップダウン外クリックで閉じる
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.header-dropdown')) {
            closeAllDropdowns();
        }
    });

    // 通知ボタンのクリック
    const notificationBtn = document.getElementById('notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleDropdown('notification-panel');
        });
    }

    // ユーザーメニューのクリック
    const userMenuBtn = document.getElementById('user-menu-btn');
    if (userMenuBtn) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleDropdown('user-dropdown');
        });
    }

    // ハッシュ変更イベント
    window.addEventListener('hashchange', function() {
        const hash = window.location.hash.slice(1);
        if (hash && pageTemplates[hash] && hash !== currentPage) {
            navigateTo(hash);
        }
    });

    // Escキーでモーダル・ドロップダウンを閉じる
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            });
            closeAllDropdowns();
        }
    });

    // デモ用：初期トースト表示
    setTimeout(() => {
        showToast('info', 'ようこそ', 'CAMPシステムのワイヤーフレームへようこそ！');
    }, 1000);
});

// デバッグ用：コンソールにページ一覧を表示
console.log('CAMPシステム ワイヤーフレーム');
console.log('利用可能なページ:', Object.keys(pageTemplates));
console.log('ヒント: showToast("success", "タイトル", "メッセージ") でトースト表示');
