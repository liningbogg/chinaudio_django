<template>
    <div class="login-wrap">
        <div class="ms-login">
            <div class="ms-title">古琴深度学习系统</div>
            <el-form :model="ruleForm" :rules="rules" ref="ruleForm" label-width="0rem" class="ms-content">
                <el-form-item prop="name" label="">
                    <el-input v-model="ruleForm.name" placeholder="name">
                    </el-input>
                </el-form-item>
                <el-form-item prop="password" label="">
                    <el-input
                        type="password" placeholder="password" v-model="ruleForm.password" @keyup.enter.native="submitForm('ruleForm')"
                    >
                    </el-input>
                </el-form-item>
                <el-form-item prop="operator" label="">
                    <el-button type="primary" @click="submitForm('ruleForm')" style="width:100%">登录</el-button>
                </el-form-item>
                <p class="login-tips">Tips : 未注册用户请先注册。</p>
            </el-form>
        </div>
    </div>
</template>

<script>

export default {
	name: "Login",
    data() {
        return {
            ruleForm: {
                name: '',
                password: '',
            },
            rules: { //验证规则
                name:[{ required: true, message: '请输入用户名', trigger: 'blur' },],
                password:[
                    { required: true, message: '请输入密码', trigger: 'blur' },
                    { min:6 , max:16, message : '请输入6到16位字母、英文符号或数字',trigger : 'blur'}
                ],
            }
        }
    },

    mounted() {},
    beforeDestroy() {
    },
    methods: {
        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    let param = {//可能还有验证码或者其他，这里只写两个
                        username: this.ruleForm.name,
                        password: this.ruleForm.password,
                    }
                    this.axios.get('web/login?username='+param.username+'&password='+param.password).then(
                        response => {
                            if(response){
                                let status = response.data.status;
                                let tip = response.data.tip;
                                if(status=="failure"){
                                    alert(tip);
                                }
                                if(status=="success"){
                                    let token = response.data.token;
                                    this.$store.state.token = token;
                                    this.$store.state.username = response.data.username;
                                    localStorage.setItem("username", response.data.username);
                                    localStorage.setItem("token", token);
                                    if(this.$route.query.redirect){
                                        let redirect = this.$route.query.redirect;
                                        this.$router.push(redirect);
                                    }else{
                                        this.$router.push("/");
                                    }
                                }
                            }
                        }
                    )

                } else {
                    console.log('error submit!!');
                    return false;
                }
            });
        },
    }
    
};
</script>

<style scoped>
.login-wrap {
    position: absolute;
    top:2rem;
    left:0rem;
    width: 100%;
    height: calc(100% - 2rem);
    background-image: url(login-bg.jpg);
    background-size: 100%;
}
.ms-title {
    width: 100%;
    line-height: 2rem;
    text-align: center;
    font-size: 1.5rem;
    color: blue;
    border-bottom: 1px solid #ddd;
}
.ms-login {
    position: absolute;
    left: 40%;
    top: 0%;
    width: 25rem;
    margin: 10rem 0 0 -5rem;
    border-radius: 0.25rem;
    background: rgba(255, 255, 255, 0.3);
    overflow: hidden;
}
.ms-content {
    padding: 1rem 1rem;
}
.login-tips {
    font-size: 0.5rem;
    line-height: 1rem;
    color: #fff;
}
</style>
