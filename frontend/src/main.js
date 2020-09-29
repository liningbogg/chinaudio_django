import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import { Button, Form, FormItem, Input, Table, TableColumn} from 'element-ui';
import axios from 'axios'
import VueAxios from 'vue-axios'
Vue.use(Button);
Vue.use(Form);
Vue.use(FormItem);
Vue.use(Table);
Vue.use(TableColumn);
Vue.use(Input);
Vue.use(VueAxios, axios);
Vue.config.productionTip = false


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
                if(to.path === redirect){
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

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
