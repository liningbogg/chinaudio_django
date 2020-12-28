<template>
    <div class="login-wrap">
        <div class="ms-login">
            <div class="ms-title">密码找回</div>
            <el-form :model="ruleForm" :rules="rules" ref="ruleForm" label-width="8rem" class="ms-content">
                <el-form-item prop="name" label="用户名">
                    <el-input v-model="ruleForm.name" placeholder="name" readonly>
                    </el-input>
                </el-form-item>
                <el-form-item prop="verification" label="验证码">
                    <el-input v-model="ruleForm.verification" placeholder="verification" style="position:absolute;left:0;width:40%">
                    </el-input>
                    <el-button type="text" style="position:absolute;left:40.5%;widht:59%" @click="push()" :disabled="isPushDisable">
                        {{pushmessage}}
                    </el-button>
                </el-form-item>
                <el-form-item prop="password" label="新密码">
                    <el-input
                        type="password" placeholder="password" v-model="ruleForm.password"
                    >
                    </el-input>
                </el-form-item>
                <el-form-item prop="conform" label="密码确认">
                    <el-input
                        type="password" placeholder="password" v-model="ruleForm.conform"
                    >
                    </el-input>
                </el-form-item>
                <el-form-item prop="operator" label="">
                    <el-button type="primary" @click="submitForm('ruleForm')" style="width:100%"> 提交</el-button>
                </el-form-item>
            </el-form>
        </div>
    </div>
</template>

<script>

export default {
	name: "Retrieve",
    data() {
        return {
            pushmessage:"",
            isPushDisable:false,
            timer:null,
            ruleForm: {
                name: '',
                password: '',
                conform: '',
                verification: '',
            },
            rules: { //验证规则
                name:[{ required: true, message: '请输入用户名', trigger: 'blur' },],
                verification:[
                    { required: true, message: '请输入验证码', trigger: 'blur' },
                    { min:6 , max:6, message : '请输入6位数字',trigger : 'blur'}
                ],
                password:[
                    { required: true, message: '请输入密码', trigger: 'blur' },
                    { min:6 , max:16, message : '请输入6到16位字母、英文符号或数字',trigger : 'blur'}
                ],
                conform:[
                    { required: true, message: '请确认密码', trigger: 'blur' },
                    { min:6 , max:16, message : '请输入6到16位字母、英文符号或数字',trigger : 'blur'},
                    {
                        validator:(rule,value,callback)=>{
                            if(value===''){
                                callback(new Error('请再次输入密码'))
                            }else if(value!==this.ruleForm.password){
                                callback(new Error('两次输入密码不一致'))
                            }else{
                                callback( )
                            }
                        },
                        trigger: 'blur'
                    },
                ],
            }
        }
    },

    mounted() {
        this.ruleForm.name = this.$route.query.name;
        this.pushmessage = "获取验证码";
    },
    computed:{
    },
    beforeDestroy() {
    },
    methods: {
        updatePushMessage(){
            this.timercount--;
            this.pushmessage="已发送至"+this.email+"("+this.timercount+"s)";
            if(this.timercount<=0){
                clearInterval(this.timer);
                this.isPushDisable=false;
                this.pushmessage = "获取验证码";
            }
        },
        push() {
            this.axios.get('web/accounts/retrieve?username='+this.ruleForm.name).then(
                response => {
                    if(response){
                        let status = response.data.status;
                        let tip = response.data.tip;
                        if(status=="failure"){
                            alert("用户名或者密码错误");
                        }
                        if(status=="success"){
                            console.log(response.data.body);
                            this.email = response.data.body.email;
                            this.isPushDisable=true;
                            this.timercount=60;
                            this.timer = setInterval(this.updatePushMessage, 1000);
                        }
                    }
                }
            );

        },
        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.axios.get('web/accounts/passwordReset?username='+this.ruleForm.name+'&password='+this.ruleForm.password+"&checkcode="+this.ruleForm.verification).then(
                        response => {
                            if(response){
                                let status = response.data.status;
                                let tip = response.data.tip;
                                if(status=="failure"){
                                    alert("请检查输入项:"+tip);
                                }
                                if(status=="success"){
                                    alert("密码已经重置，请重新登录。");
                                    this.$router.push("/login");
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

<style scopeVerification d>
.login-wrap {
    position:absolute;
    left:0rem;
    width: 100%;
    height:100%;
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
    position:absolute;
    left:35%;
    top: 0%;
    width: 40rem;
    margin: 10rem 0 0 -5rem;
    border-radius: 0.25rem;
    background: rgba(255, 255, 255, 1);
    overflow: hidden;
}
.ms-content {
    padding: 1rem 1rem;
}
</style>
