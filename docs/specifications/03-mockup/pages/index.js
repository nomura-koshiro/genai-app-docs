// ========================================
// CAMPシステム ページテンプレート統合
// ========================================

// 全ページテンプレートを統合
const pageTemplates = {
    ...authPages,
    ...dashboardPages,
    ...projectPages,
    ...sessionPages,
    ...treePages,
    ...filePages,
    ...adminPages,
    ...masterPages,
};

// デバッグ用：利用可能なページ一覧をコンソールに出力
console.log('利用可能なページ:', Object.keys(pageTemplates));
