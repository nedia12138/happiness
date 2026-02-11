// 统一布局组件文件

// 前台布局组件
Vue.component('front-layout', {
    props: {
        activeMenu: {
            type: String,
            default: '1'
        }
    },
    data() {
        return {
            userInfo: null,
            menuItems: LayoutConfig.frontMenu,
            systemConfig: LayoutConfig.system
        }
    },
    mounted() {
        this.checkAuth();
        this.setActiveMenu();
        
        // 监听用户信息更新事件
        window.addEventListener('userInfoUpdated', this.handleUserInfoUpdate);
    },
    beforeDestroy() {
        // 移除事件监听
        window.removeEventListener('userInfoUpdated', this.handleUserInfoUpdate);
    },
    methods: {
        checkAuth() {
            // 基于本地缓存检查登录状态
            const token = localStorage.getItem('token') || sessionStorage.getItem('token');
            const userInfo = localStorage.getItem('userInfo') || sessionStorage.getItem('userInfo');
            
            if (token && userInfo) {
                try {
                    this.userInfo = JSON.parse(userInfo);
                } catch (e) {
                    console.error('解析用户信息失败:', e);
                    this.userInfo = null;
                }
            } else {
                this.userInfo = null;
            }
        },
        setActiveMenu() {
            const path = window.location.pathname;
            const menuItem = this.menuItems.find(item => path.includes(item.path.split('/').pop()));
            if (menuItem) {
                this.$emit('update:activeMenu', menuItem.index);
            }
        },
        handleMenuClick(index) {
            const menuItem = this.menuItems.find(item => item.index === index);
            if (menuItem) {
                window.location.href = menuItem.path;
            }
        },
        handleLogout() {
            this.$confirm('确定要退出登录吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                // 清除所有本地缓存数据
                localStorage.removeItem('token');
                localStorage.removeItem('userInfo');
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('userInfo');
                
                // 清除用户信息
                this.userInfo = null;
                
                this.$message.success('退出登录成功');
                window.location.href = '/login';
            });
        },
        handleCommand(command) {
            if (command === 'profile') {
                window.location.href = '/front/profile.html';
            } else if (command === 'admin') {
                window.location.href = '/admin/index.html';
            } else if (command === 'users') {
                window.location.href = '/admin/users.html';
            } else if (command === 'logout') {
                this.handleLogout();
            }
        },
        goToLogin() {
            window.location.href = '/login';
        },
        goToRegister() {
            window.location.href = '/register';
        },
        handleUserInfoUpdate(event) {
            // 更新用户信息
            this.userInfo = event.detail.userInfo;
        }
    },
    template: `
        <div id="front-layout">
            <!-- 顶部导航栏 -->
            <el-header class="header">
                <div class="header-content">
                    <div class="logo">
                        <h2>{{ systemConfig.title }}</h2>
                    </div>
                    <div class="nav-menu">
                        <el-menu mode="horizontal" :default-active="activeMenu" @select="handleMenuClick">
                            <el-menu-item 
                                v-for="item in menuItems" 
                                :key="item.index"
                                :index="item.index">
                                <i :class="item.icon"></i>
                                {{ item.title }}
                            </el-menu-item>
                        </el-menu>
                    </div>
                    <div class="user-info" v-if="userInfo">
                        <theme-switcher></theme-switcher>
                        <el-dropdown @command="handleCommand">
                            <span class="el-dropdown-link">
                                <el-avatar :src="userInfo.avatar || systemConfig.defaultAvatar" size="small"></el-avatar>
                                <span class="username">{{ userInfo.nickname || userInfo.username }}</span>
                                <i class="el-icon-arrow-down el-icon--right"></i>
                            </span>
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

            <!-- 主要内容区域 -->
            <div class="main-content">
                <slot></slot>
            </div>

            <!-- 底部 -->
            <el-footer class="footer">
                <div class="footer-content">
                    <p>&copy; 2030 {{ systemConfig.title }}. All rights reserved.</p>
                </div>
            </el-footer>
        </div>
    `
});

// 后台布局组件
Vue.component('admin-layout', {
    props: {
        activeMenu: {
            type: String,
            default: 'dashboard'
        }
    },
    data() {
        return {
            userInfo: null,
            isCollapse: false,
            menuItems: LayoutConfig.adminMenu,
            filteredMenuItems: [],
            systemConfig: LayoutConfig.system
        }
    },
    mounted() {
        this.checkAuth();
        
        // 监听用户信息更新事件
        window.addEventListener('userInfoUpdated', this.handleUserInfoUpdate);
    },
    beforeDestroy() {
        // 移除事件监听
        window.removeEventListener('userInfoUpdated', this.handleUserInfoUpdate);
    },
    methods: {
        checkAuth() {
            // 基于本地缓存检查登录状态
            const token = localStorage.getItem('token') || sessionStorage.getItem('token');
            const userInfo = localStorage.getItem('userInfo') || sessionStorage.getItem('userInfo');

            if (token && userInfo) {
                try {
                    this.userInfo = JSON.parse(userInfo);
                    // 根据用户角色过滤菜单
                    this.filterMenuByRole();
                } catch (e) {
                    console.error('解析用户信息失败:', e);
                    this.userInfo = null;
                    this.filteredMenuItems = [];
                }
            } else {
                this.userInfo = null;
                this.filteredMenuItems = [];
            }
        },
        filterMenuByRole() {
            // 根据用户角色过滤菜单项
            if (!this.userInfo || !this.userInfo.role) {
                this.filteredMenuItems = [];
                return;
            }

            const userRole = this.userInfo.role;
            this.filteredMenuItems = this.filterMenuItems(this.menuItems, userRole);
        },
        filterMenuItems(menuItems, userRole) {
            return menuItems.filter(item => {
                // 检查当前菜单项是否有角色限制
                if (item.roles && item.roles.length > 0) {
                    if (!item.roles.includes(userRole)) {
                        return false;
                    }
                }

                // 如果有子菜单，递归过滤子菜单
                if (item.children && item.children.length > 0) {
                    item.children = this.filterMenuItems(item.children, userRole);
                    // 如果过滤后没有子菜单了，隐藏父菜单
                    return item.children.length > 0;
                }

                return true;
            });
        },
        handleMenuClick(index) {
            const menuItem = this.findMenuItemByIndex(this.menuItems, index);
            if (menuItem && menuItem.path) {
                window.location.href = menuItem.path;
            }
        },
        findMenuItemByIndex(menuItems, index) {
            for (const item of menuItems) {
                if (item.index === index) {
                    return item;
                }
                if (item.children && item.children.length > 0) {
                    const found = this.findMenuItemByIndex(item.children, index);
                    if (found) {
                        return found;
                    }
                }
            }
            return null;
        },
        handleLogout() {
            this.$confirm('确定要退出登录吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                // 清除所有本地缓存数据
                localStorage.removeItem('token');
                localStorage.removeItem('userInfo');
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('userInfo');
                
                // 清除用户信息
                this.userInfo = null;
                
                this.$message.success('退出登录成功');
                window.location.href = '/login';
            });
        },
        toggleCollapse() {
            this.isCollapse = !this.isCollapse;
        },
        handleCommand(command) {
            if (command === 'profile') {
                window.location.href = '/admin/profile.html';
            } else if (command === 'front') {
                window.location.href = '/front/index.html';
            }else if (command === 'users') {
                window.location.href = '/admin/users.html';
            }  else if (command === 'logout') {
                this.handleLogout();
            }
        },
        handleUserInfoUpdate(event) {
            // 更新用户信息
            this.userInfo = event.detail.userInfo;
            // 重新过滤菜单
            this.filterMenuByRole();
        }
    },
    template: `
        <el-container class="admin-container">
            <!-- 左侧菜单 -->
            <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
                <div class="logo-container">
                    <h3 v-if="!isCollapse">{{ systemConfig.title }}</h3>
                    <i v-else class="el-icon-s-platform"></i>
                </div>
                
                <el-menu
                    :default-active="activeMenu"
                    :collapse="isCollapse"
                    background-color="#5e8ed9"
                    text-color="#ffffff"
                    active-text-color="#333333"
                    @select="handleMenuClick"
                    unique-opened
                    router>

                    <template v-for="item in filteredMenuItems">
                        <!-- 有子菜单的项目 -->
                        <el-submenu
                            v-if="item.children && item.children.length > 0"
                            :key="item.index"
                            :index="item.index">
                            <template slot="title">
                                <i :class="item.icon"></i>
                                <span>{{ item.title }}</span>
                            </template>
                            <el-menu-item
                                v-for="child in item.children"
                                :key="child.index"
                                :index="child.index">
                                <i :class="child.icon"></i>
                                <span slot="title">{{ child.title }}</span>
                            </el-menu-item>
                        </el-submenu>

                        <!-- 无子菜单的项目 -->
                        <el-menu-item
                            v-else
                            :key="item.index"
                            :index="item.index">
                            <i :class="item.icon"></i>
                            <span slot="title">{{ item.title }}</span>
                        </el-menu-item>
                    </template>
                </el-menu>
            </el-aside>

            <!-- 主要内容区域 -->
            <el-container>
                <!-- 顶部导航栏 -->
                <el-header class="header">
                    <div class="header-left">
                        <el-button 
                            type="text" 
                            @click="toggleCollapse"
                            class="collapse-btn">
                            <i :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'"></i>
                        </el-button>
                        <el-breadcrumb separator="/">
                            <el-breadcrumb-item>首页</el-breadcrumb-item>
                            <el-breadcrumb-item>{{ menuItems.find(item => item.index === activeMenu)?.title || '页面' }}</el-breadcrumb-item>
                        </el-breadcrumb>
                    </div>
                    
                    <div class="header-right">
                        <el-dropdown @command="handleCommand">
                            <span class="user-dropdown">
                                <el-avatar :src="userInfo && userInfo.avatar ? userInfo.avatar : systemConfig.defaultAvatar" size="small"></el-avatar>
                                <span class="username">{{ userInfo && userInfo.nickname ? userInfo.nickname : '用户' }}</span>
                                <i class="el-icon-arrow-down el-icon--right"></i>
                            </span>
                            <el-dropdown-menu slot="dropdown">
                                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                                <el-dropdown-item command="users">用户管理</el-dropdown-item>
                                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                            </el-dropdown-menu>
                        </el-dropdown>
                    </div>
                </el-header>

                <!-- 内容区域 -->
                <el-main class="main-content">
                    <slot name="content"></slot>
                </el-main>
            </el-container>
        </el-container>
    `
});
