<template>
    <div>
        <h1>
            {{message}}
        </h1>
    </div>
</template>
<script>

export default {
    name: "Logout",
    data() {
        return {
            message:"准备退出",
        }
    },
    mounted() {
        this.logout();
    },
    methods: {
        logout() {
            this.axios.get('web/accounts/logout').then(
                response => {
                    if(response){
                        let status = response.data.status;
                        if(status=="success"){
                            this.message = "用户 " + this.$store.state.username + " 已经退出登录";
                            this.$store.state.username="";
                            this.$store.state.token="";
                            localStorage.setItem("username", "");
                            localStorage.setItem("token", "");
                            this.$router.push("/login")
                        }
                        if(status=="failure"){
                            this.message = "用户 " + this.$store.state.username + "退出失败，原因:"+response.data.tip;
                        }
                    }

                }
            )
        },
    }
}
</script>

<style scoped lang="less">
</style>
