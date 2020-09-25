<template>
    <div id="nav" style="height:2rem;font-size:1.5rem;">
        <router-link to="/">主页</router-link> |
        <span class="pull-right">
            <span v-if="!this.$store.state.token">
                <router-link to="/login">登录</router-link>|
                <router-link to="/register">注册</router-link>
            </span>
            <span v-else>
                <img src="/static/img/userImage.jpg" style="border-radius:50%;width:2rem"/>
                <span>
                    用户名:{{this.$store.state.username}}(已登录)
                </span> |
                <router-link to="/logout">Logout</router-link>
            </span>
        </span>
    </div>
</template>

<style lang="less">
#nav {
    float:right;
    float:top;
    a {
        font-weight: bold;
        color: #2c3e50;
        &.router-link-exact-active {
            color: #42b983;
        }
    }
}
</style>

