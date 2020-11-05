import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import { Button, Form, FormItem, Input, Table, TableColumn, Select, Option, Switch} from 'element-ui';
import axios from 'axios'
import VueAxios from 'vue-axios'
import ECharts from "vue-echarts";
import 'echarts/lib/chart/line'
import 'echarts/lib/chart/heatmap'
import 'echarts/lib/component/markLine'
import 'echarts/lib/component/visualMap'
import 'echarts/lib/component/legend'
import 'echarts/lib/component/title'

Vue.component('v-chart', ECharts)

Vue.use(Button);
Vue.use(Form);
Vue.use(FormItem);
Vue.use(Table);
Vue.use(TableColumn);
Vue.use(Input);
Vue.use(Select);
Vue.use(Switch);
Vue.use(Option);
Vue.use(VueAxios, axios);
Vue.config.productionTip = false;

axios.interceptors.request.use(config =>{
  /*为请求头对象添加Token验证的Authorization对象，就不用每次都在要传送的字段上加token了*/
    config.headers.Authorization=localStorage.getItem('token')
    return config
})

router.beforeEach((to, from, next) => {
    if (to.meta.requireAuth) {
        let token =  localStorage.getItem("token");
        let username =  localStorage.getItem("username");
        let state_super =  localStorage.getItem("super");
        store.state.token = token;
        store.state.username = username;
        store.state.super = state_super;

        if (store.state.token) {
            // 此处添加代码向服务端请求用户实际登录状态
            //
            if(Object.keys(from.query).length === 0){
                next();
            }else{
                let redirect = from.query.redirect;
                console.log(to.path);
                console.log(redirect);
                if(!redirect || to.path === redirect.split("?")[0]){
                    next();  //避免重复循环
                }else{
                    next({path:redirect})  //跳转到目的路由
                }
            }
        } else {

            if(to.path === "/login"){
                next();
            }else{
                next({
                    path:"/login",
                    query: {redirect: to.fullPath}//将目的路由地址存入login的query中
                });
            }
        }
    } else {
        next();
    }
    return
}),
// http response 拦截器
axios.interceptors.response.use(
    response => {
        return response;
    },
    error => {
        if (error.response) {
            switch (error.response.status) {
                case 401:
                alert(error.response.data)
                router.replace({
                    path: '/login',
                    query: {redirect: router.currentRoute.fullPath}//登录成功后跳入浏览的当前页面
                })
            }
        }
        return Promise.reject(error.response.data)
    }
);

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
