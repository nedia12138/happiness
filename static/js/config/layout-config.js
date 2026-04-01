// 统一布局配置文件
const LayoutConfig = {
    // 前台菜单配置
    frontMenu: [],

    // 后台菜单配置
    adminMenu: [
        // 1. 问卷数据表：仅管理员可见
        {
            index: 'happiness_survey',
            title: '原始问卷数据',
            path: '/admin/happiness_survey.html',
            icon: 'el-icon-s-data',
            roles: ['admin']
        },
        // 2. 全域数据大屏：仅管理员可见（宏观隔离）
        {
            index: 'data_analysis',
            title: '全域数据洞察',
            path: '/admin/data_analysis.html',
            icon: 'el-icon-s-marketing',
            roles: ['admin']
        },
        // 3. 预测系统：管理员和普通用户都可见！
        {
            index: 'happiness_prediction',
            title: '幸福感在线预测',
            path: '/admin/happiness_prediction.html',
            icon: 'el-icon-magic-stick',
            roles: ['admin', 'user']
        }
    ],

    // 角色选项配置 (全局统一配置)
    roleOptions: [
        { label: '超级管理员 (Admin)', value: 'admin' },
        { label: '普通用户 (User)', value: 'user' }
    ],

    // 系统配置
    system: {
        title: '幸福感智能分析系统',
        logo: '/static/image/logo.png',
        defaultAvatar: '/static/image/profile.png'
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LayoutConfig;
}