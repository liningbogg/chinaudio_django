<template>
  <div id="app">
    <div id="nav">
        <span class="pull-right">
            <span v-if="!this.$store.state.token">
                <router-link to="/login">登录</router-link>|
                <router-link to="/register">注册</router-link>
            </span>
            <span v-else>
                <img src="/static/img/userImage.jpg" style="border-radius:50%;width:2rem"/>
                <span>用户名:{{this.$store.state.username}}(已登录)</span>|
                <router-link to="/logout">Logout</router-link>
            </span>
        </span>

    </div>
    <div id="main">
      <router-view/>
    </div>
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
#nav {
  height: 2rem;
  float:top;
  float:right;
}
#main {
  height: calc(100% - 2rem);
}
#nav a {
  font-weight: bold;
  color: #2c3e50;
}
#nav a.router-link-exact-active {
  color: #42b983;
}
</style>

