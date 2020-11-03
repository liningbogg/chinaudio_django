<template>
  <div id="app">
    <div id="nav">
        <span class="pull-right">
            <span v-if="!this.$store.state.token">
                <router-link to="/login">登录</router-link>|
                <router-link to="/register">注册</router-link>
            </span>
            <span v-else>
                <router-link to="/target">音频</router-link>|
                <router-link to="/ocr">图像</router-link>|
                <span style="font-color:green">
                用户名:{{this.$store.state.username}}(已登录)
                </span>|
                <router-link to="/logout">Logout</router-link>
            </span>
        </span>

    </div>
    <div id="main">
      <router-view/>
    </div>
  </div>
</template>

<script>

export default {
    name: "Login",
    data() {
        return {
        }
    },

    mounted() {},
    beforeDestroy() {
    },
    methods: {
    }

};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  height:100%;
  left:0rem;
  width:100%;
}
#nav {
  position:absolute;
  height: 2rem;
  top:0rem;
  left:0rem;
  width:100%;
  text-align:right;
  font-size:1.5rem;
  float:right;
}
#main {
  position:absolute;
  width:100%;
  top:2rem;
  left:0rem;
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

