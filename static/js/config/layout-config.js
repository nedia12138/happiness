// 统一布局配置文件
const LayoutConfig = {
    // 前台菜单配置
    frontMenu: [
    ],
    
    // 后台菜单配置
    adminMenu: [
        // {
        //     index: 'user_management',
        //     title: '用户管理',
        //     icon: 'el-icon-user',
        //     roles: ['admin'], // 只有管理员可以访问
        //     children: [
        //         {
        //             index: 'users',
        //             title: '用户列表',
        //             path: '/admin/users.html',
        //             icon: 'el-icon-user-solid',
        //             roles: ['admin'] // 只有管理员可以访问
        //         }
        //     ]
        // },  
        {
            index: 'happiness_survey',
            title: '幸福感调查表',
            path: '/admin/happiness_survey.html',
            icon: 'el-icon-s-data',
            roles: ['admin', 'operation'] // 管理员和操作员都可以访问
        },
        {
            index: 'data_analysis',
            title: '数据分析',
            path: '/admin/data_analysis.html',
            icon: 'el-icon-s-marketing',
            roles: ['admin', 'operation'] // 管理员和操作员都可以访问
        },
        {
            index: 'happiness_prediction',
            title: '幸福感预测',
            path: '/admin/happiness_prediction.html',
            icon: 'el-icon-magic-stick',
            roles: ['admin', 'operation'] // 管理员和操作员都可以访问
        } 
    ],

    // 角色选项配置
    roleOptions: [
        { label: '管理员', value: 'admin' }
    ],

    // 系统配置
    system: {
        title: '幸福感数据挖掘系统',
        logo: '/static/image/logo.png',
        defaultAvatar: '/static/image/profile.png'
    } 
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LayoutConfig;
}
