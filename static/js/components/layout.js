// 统一布局组件文件

// ==========================================
// 1. 前台布局组件 (Front Layout - 保持不变)
// ==========================================
Vue.component('front-layout', {
    props: { activeMenu: { type: String, default: '1' } },
    data() { return { userInfo: null, menuItems: LayoutConfig.frontMenu, systemConfig: LayoutConfig.system } },
    mounted() { this.checkAuth(); this.setActiveMenu(); window.addEventListener('userInfoUpdated', this.handleUserInfoUpdate); },
    beforeDestroy() { window.removeEventListener('userInfoUpdated', this.handleUserInfoUpdate); },
    methods: {
        checkAuth() {
            const token = localStorage.getItem('token') || sessionStorage.getItem('token');
            const userInfo = localStorage.getItem('userInfo') || sessionStorage.getItem('userInfo');
            if (token && userInfo) { try { this.userInfo = JSON.parse(userInfo); } catch (e) { this.userInfo = null; } } else { this.userInfo = null; }
        },
        setActiveMenu() {
            const path = window.location.pathname;
            const menuItem = this.menuItems.find(item => path.includes(item.path.split('/').pop()));
            if (menuItem) { this.$emit('update:activeMenu', menuItem.index); }
        },
        handleMenuClick(index) {
            const menuItem = this.menuItems.find(item => item.index === index);
            if (menuItem) { window.location.href = menuItem.path; }
        },
        handleLogout() {
            this.$confirm('确定要退出登录吗？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }).then(() => {
                localStorage.removeItem('token'); localStorage.removeItem('userInfo');
                sessionStorage.removeItem('token'); sessionStorage.removeItem('userInfo');
                this.userInfo = null; window.location.href = '/login';
            });
        },
        handleCommand(command) {
            if (command === 'profile') window.location.href = '/front/profile.html';
            else if (command === 'admin') window.location.href = '/admin/index.html';
            else if (command === 'users') window.location.href = '/admin/users.html';
            else if (command === 'logout') this.handleLogout();
        },
        goToLogin() { window.location.href = '/login'; },
        goToRegister() { window.location.href = '/register'; },
        handleUserInfoUpdate(event) { this.userInfo = event.detail.userInfo; }
    },
    template: `
        <div id="front-layout">
            <el-header class="header">
                <div class="header-content">
                    <div class="logo"><h2>{{ systemConfig.title }}</h2></div>
                    <div class="nav-menu">
                        <el-menu mode="horizontal" :default-active="activeMenu" @select="handleMenuClick">
                            <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index"><i :class="item.icon"></i>{{ item.title }}</el-menu-item>
                        </el-menu>
                    </div>
                    <div class="user-info" v-if="userInfo">
                        <theme-switcher></theme-switcher>
                        <el-dropdown @command="handleCommand">
                            <span class="el-dropdown-link"><el-avatar :src="userInfo.avatar || systemConfig.defaultAvatar" size="small"></el-avatar><span class="username">{{ userInfo.nickname || userInfo.username }}</span><i class="el-icon-arrow-down el-icon--right"></i></span>
                            <el-dropdown-menu slot="dropdown">
                                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                                <el-dropdown-item v-if="userInfo.role === 'admin'" command="admin">后台管理</el-dropdown-item>
                                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                            </el-dropdown-menu>
                        </el-dropdown>
                    </div>
                    <div class="auth-buttons" v-else>
                        <theme-switcher></theme-switcher>
                        <el-button type="text" @click="goToLogin">登录</el-button>
                        <el-button type="primary" @click="goToRegister">注册</el-button>
                    </div>
                </div>
            </el-header>
            <div class="main-content"><slot></slot></div>
            <el-footer class="footer"><div class="footer-content"><p>&copy; 2026 {{ systemConfig.title }}. All rights reserved.</p></div></el-footer>
        </div>
    `
});

// ==========================================
// 2. 后台布局组件 (Admin Layout - 终极质感版)
// ==========================================
Vue.component('admin-layout', {
    props: {
        activeMenu: { type: String, default: 'dashboard' }
    },
    data() {
        return {
            userInfo: null, isCollapse: false, menuItems: LayoutConfig.adminMenu, filteredMenuItems: [], systemConfig: LayoutConfig.system
        }
    },
    mounted() {
        this.checkAuth();
        window.addEventListener('userInfoUpdated', this.handleUserInfoUpdate);
        this.injectMagicStyles();
    },
    beforeDestroy() {
        window.removeEventListener('userInfoUpdated', this.handleUserInfoUpdate);
    },
    methods: {
        injectMagicStyles() {
            const styleId = 'magic-aurora-theme';
            if (!document.getElementById(styleId)) {
                const style = document.createElement('style');
                style.id = styleId;
                style.innerHTML = `
                    /* 左侧边栏底色 */
                    html body .admin-container .sidebar {
                        background: linear-gradient(180deg, #dbeafe 0%, #fce7f3 100%) !important;
                        border-right: 2px solid #ffffff !important;
                        box-shadow: 3px 0 15px rgba(161, 196, 253, 0.2) !important;
                    }
                    html body .admin-container .logo-container {
                        height: 70px !important; line-height: 70px !important; text-align: center !important;
                        border-bottom: 2px dashed rgba(255, 255, 255, 0.6) !important;
                        background-color: transparent !important;
                    }

                    /* 菜单项基础样式 */
                    html body .admin-container .el-menu { background-color: transparent !important; border: none !important; padding-top: 10px !important; }
                    html body .el-menu--collapse { background-color: transparent !important; }

                    /* 未选中状态 */
                    html body .admin-container .el-menu-item, html body .admin-container .el-submenu__title {
                        background-color: transparent !important; border-radius: 12px !important; margin: 6px 12px !important; width: calc(100% - 24px) !important;
                        height: 48px !important; line-height: 48px !important; transition: all 0.3s ease !important;
                    }
                    html body .admin-container .el-menu-item span, html body .admin-container .el-submenu__title span {
                        color: #4b8ae6 !important; font-weight: 700 !important; text-shadow: 0 1px 1px rgba(255, 255, 255, 0.5) !important; transition: color 0.3s !important;
                    }
                    html body .admin-container .el-menu-item i, html body .admin-container .el-submenu__title i { color: #f78da7 !important; font-size: 18px !important; transition: all 0.3s !important; }

                    /* 悬浮状态 */
                    html body .admin-container .el-menu-item:hover, html body .admin-container .el-submenu__title:hover {
                        background-color: rgba(255, 255, 255, 0.85) !important; transform: translateY(-2px) !important; box-shadow: 0 4px 10px rgba(161, 196, 253, 0.15) !important;
                    }
                    html body .admin-container .el-menu-item:hover span, html body .admin-container .el-submenu__title:hover span { color: #f56e8d !important; }

                    /* 选中状态 */
                    html body .admin-container .el-menu-item.is-active {
                        background: linear-gradient(135deg, #74aeff 0%, #ff8fa3 100%) !important; transform: scale(1.02) !important;
                        box-shadow: 0 4px 12px rgba(255, 143, 163, 0.35) !important; border: 1px solid rgba(255, 255, 255, 0.9) !important;
                    }
                    html body .admin-container .el-menu-item.is-active span { color: #ffffff !important; font-weight: 800 !important; text-shadow: 0 1px 3px rgba(255, 117, 140, 0.8) !important; }
                    html body .admin-container .el-menu-item.is-active i { color: #ffffff !important; animation: none !important; filter: drop-shadow(0 1px 2px rgba(255, 117, 140, 0.6)) !important; }

                    /* 顶部栏 */
                    html body .admin-container .header { background-color: rgba(255,255,255,0.95) !important; backdrop-filter: blur(10px) !important; box-shadow: 0 2px 10px rgba(161, 196, 253, 0.08) !important; z-index: 10 !important; border-bottom: none !important;}

                    /* ====================================================== */
                    /* ★ 核心修改：右侧主内容区底色及卡片立体化 ★ */
                    /* ====================================================== */
                    /* 1. 把右侧底色变成绝美高级的淡淡浅蓝浅粉渐变 */
                    html body .admin-container .main-content {
                        background: linear-gradient(135deg, #f0f7ff 0%, #fff2f6 100%) !important;
                        padding: 25px !important;
                    }

                    /* 2. 强行接管所有卡片，让卡片保持纯白并带柔和悬浮阴影，立体感拉满！ */
                    html body .admin-container .main-content .el-card,
                    html body .admin-container .main-content .stats-card,
                    html body .admin-container .main-content .activity-card {
                        background-color: #ffffff !important;
                        border: none !important;
                        border-radius: 16px !important; /* 卡片圆角更柔和 */
                        box-shadow: 0 8px 24px rgba(161, 196, 253, 0.12) !important;
                        transition: all 0.3s ease !important;
                    }

                    /* 3. 鼠标放上卡片时的互动效果 */
                    html body .admin-container .main-content .el-card:hover,
                    html body .admin-container .main-content .stats-card:hover,
                    html body .admin-container .main-content .activity-card:hover {
                        box-shadow: 0 12px 32px rgba(161, 196, 253, 0.2) !important;
                        transform: translateY(-3px) !important;
                    }
                `;
                document.head.appendChild(style);
            }
        },
        checkAuth() {
            const token = localStorage.getItem('token') || sessionStorage.getItem('token');
            const userInfo = localStorage.getItem('userInfo') || sessionStorage.getItem('userInfo');
            if (token && userInfo) { try { this.userInfo = JSON.parse(userInfo); this.filterMenuByRole(); } catch (e) { this.userInfo = null; this.filteredMenuItems = []; } } else { this.userInfo = null; this.filteredMenuItems = []; }
        },
        filterMenuByRole() {
            if (!this.userInfo || !this.userInfo.role) { this.filteredMenuItems = []; return; }
            this.filteredMenuItems = this.filterMenuItems(this.menuItems, this.userInfo.role);
        },
        filterMenuItems(menuItems, userRole) {
            return menuItems.filter(item => {
                if (item.roles && item.roles.length > 0 && !item.roles.includes(userRole)) return false;
                if (item.children && item.children.length > 0) {
                    item.children = this.filterMenuItems(item.children, userRole);
                    return item.children.length > 0;
                }
                return true;
            });
        },
        handleMenuClick(index) {
            const menuItem = this.findMenuItemByIndex(this.menuItems, index);
            if (menuItem && menuItem.path) window.location.href = menuItem.path;
        },
        findMenuItemByIndex(menuItems, index) {
            for (const item of menuItems) {
                if (item.index === index) return item;
                if (item.children && item.children.length > 0) { const found = this.findMenuItemByIndex(item.children, index); if (found) return found; }
            }
            return null;
        },
        handleLogout() {
            this.$confirm('确定要离开星空魔法屋吗？', '提示', { confirmButtonText: '对呀', cancelButtonText: '点错啦', type: 'warning' }).then(() => {
                localStorage.removeItem('token'); localStorage.removeItem('userInfo');
                sessionStorage.removeItem('token'); sessionStorage.removeItem('userInfo');
                this.userInfo = null; window.location.href = '/login';
            });
        },
        toggleCollapse() { this.isCollapse = !this.isCollapse; },
        handleCommand(command) {
            if (command === 'profile') window.location.href = '/admin/profile.html';
            else if (command === 'front') window.location.href = '/front/index.html';
            else if (command === 'users') window.location.href = '/admin/users.html';
            else if (command === 'logout') this.handleLogout();
        },
        handleUserInfoUpdate(event) { this.userInfo = event.detail.userInfo; this.filterMenuByRole(); }
    },
    template: `
        <el-container class="admin-container" style="height: 100vh;">
            <el-aside :width="isCollapse ? '80px' : '220px'" class="sidebar">
                <div class="logo-container">
                    <h3 v-if="!isCollapse" style="margin: 0; font-size: 20px; font-weight: 800; background: linear-gradient(90deg, #4b8ae6, #f56e8d); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        <i class="el-icon-odometer" style="margin-right: 5px; color: #ff8fa3;"></i>幸福大屏
                    </h3>
                    <i v-else class="el-icon-odometer" style="font-size: 24px; color: #6baaff;"></i>
                </div>

                <el-menu
                    :default-active="activeMenu"
                    :collapse="isCollapse"
                    unique-opened
                    @select="handleMenuClick">

                    <template v-for="item in filteredMenuItems">
                        <el-submenu v-if="item.children && item.children.length > 0" :key="item.index" :index="item.index">
                            <template slot="title"><i :class="item.icon"></i><span>{{ item.title }}</span></template>
                            <el-menu-item v-for="child in item.children" :key="child.index" :index="child.index"><i :class="child.icon"></i><span slot="title">{{ child.title }}</span></el-menu-item>
                        </el-submenu>
                        <el-menu-item v-else :key="item.index" :index="item.index">
                            <i :class="item.icon"></i><span slot="title">{{ item.title }}</span>
                        </el-menu-item>
                    </template>
                </el-menu>
            </el-aside>

            <el-container>
                <el-header class="header" height="65px">
                    <div class="header-left" style="display: flex; align-items: center; height: 100%;">
                        <el-button type="text" @click="toggleCollapse" style="color: #6c9ce3; font-size: 24px; margin-right: 20px; padding: 0; transition: color 0.3s;" onmouseover="this.style.color='#ff8fa3'" onmouseout="this.style.color='#6c9ce3'">
                            <i :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'"></i>
                        </el-button>
                        <el-breadcrumb separator="/">
                            <el-breadcrumb-item style="font-weight: 700; color:#6c9ce3;">首页</el-breadcrumb-item>
                            <el-breadcrumb-item style="font-weight: 700; color:#ff8fa3;">{{ menuItems.find(item => item.index === activeMenu)?.title || '控制面板' }}</el-breadcrumb-item>
                        </el-breadcrumb>
                    </div>

                    <div class="header-right" style="display: flex; align-items: center; height: 100%;">
                        <el-dropdown @command="handleCommand">
                            <span class="user-dropdown" style="cursor: pointer; display: flex; align-items: center; background: rgba(255,255,255,0.9); padding: 5px 15px; border-radius: 20px; border: 1px solid rgba(161, 196, 253, 0.4); transition: all 0.3s;" onmouseover="this.style.backgroundColor='#fff0f3'" onmouseout="this.style.backgroundColor='rgba(255,255,255,0.9)'">
                                <el-avatar :src="userInfo && userInfo.avatar ? userInfo.avatar : systemConfig.defaultAvatar" size="small"></el-avatar>
                                <span style="color: #4b8ae6; font-weight: 700; margin-left: 8px; margin-right: 5px;">{{ userInfo && userInfo.nickname ? userInfo.nickname : '探索者' }}</span>
                                <i class="el-icon-arrow-down" style="color: #ff8fa3;"></i>
                            </span>
                            <el-dropdown-menu slot="dropdown" style="border-radius: 12px; border: 1px solid #f0f8ff; padding: 5px; box-shadow: 0 4px 15px rgba(161, 196, 253, 0.15);">
                                <el-dropdown-item command="profile" style="color: #4b8ae6; border-radius: 6px; margin-bottom: 2px;">🎈 个人中心</el-dropdown-item>
                                <el-dropdown-item v-if="userInfo && userInfo.role === 'admin'" command="users" style="color: #ff8fa3; border-radius: 6px; margin-bottom: 2px;">👑 用户管理</el-dropdown-item>
                                <el-dropdown-item divided command="logout" style="color: #f56c6c; border-radius: 6px;">👋 退出登录</el-dropdown-item>
                            </el-dropdown-menu>
                        </el-dropdown>
                    </div>
                </el-header>

                <el-main class="main-content">
                    <slot name="content"></slot>
                </el-main>
            </el-container>
        </el-container>
    `
});