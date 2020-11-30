<template>
<div id="main">
    <div id="recommentchart">
        <v-chart  :options="chartOption" style="height:100%;width:100%" autoresize="true"/>
    </div>
    <div id="optionSet">
        <div id="projection_easing">
            <div class="tip">easing</div>
            <el-input v-model="projection_thr_easing" placeholder="proj_easing" type="number" step="0.01" @change="set_easing"></el-input>
        </div>
        <div id="projection_strict">
            <div class="tip">strict</div>
            <el-input v-model="projection_thr_strict" placeholder="proj_strict" type="number" step="0.01" @change="set_strict"></el-input>
        </div>
        <div id="entropy">
            <div class="tip">entropy</div>
            <el-input v-model="entropy_thr" placeholder="entropy_thr" type="number" step="0.01" @change="set_entropy"></el-input>
        </div>
    </div>
</div>
</template>

<script>

export default {
	name: "Recommenttip",
    props: ['currentframe'],
    data() {
        return {
            projection_thr_strict:null,
            projection_thr_easing:null,
            entropy_thr:null,
        }
    },
    mounted() {
    },
    beforeDestroy() {
    },
    methods: {
        set_easing(){
            //设置project_thr_easing
            this.axios.get('ocr/setRoughThrEasing/?currentframe='+this.currentframe+"&docid="+this.docid+"&projection_thr_easing="+this.projection_thr_easing).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let projection_thr_easing = response.data.body.projection_thr_easing;
                            let message={
                                "type":"notice",
                                "text":"粗标注Easing阈值修改为:"+projection_thr_easing,
                            }
                            this.$store.commit("addMessagetip",message);
                        }else{
                            this.msg = "设置粗标注阈值easing出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )

        },
        set_strict(){
            //设置project_thr_easing
            this.axios.get('ocr/setRoughThrStrict/?currentframe='+this.currentframe+"&docid="+this.docid+"&projection_thr_strict="+this.projection_thr_strict).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let projection_thr_strict = response.data.body.projection_thr_strict;
                            let message={
                                "type":"notice",
                                "text":"粗标注Strict阈值修改为:"+projection_thr_strict,
                            }
                            this.$store.commit("addMessagetip",message);
                        }else{
                            this.msg = "设置粗标注阈值Strict出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )

        },
        set_entropy(){
            //设置project_thr_easing
            this.axios.get('ocr/setRoughThrEntropy/?currentframe='+this.currentframe+"&docid="+this.docid+"&entropy_thr="+this.entropy_thr).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let entropy_thr = response.data.body.entropy_thr;
                            let message={
                                "type":"notice",
                                "text":"粗标注Entropy阈值修改为:"+entropy_thr,
                            }
                            this.$store.commit("addMessagetip",message);
                        }else{
                            this.msg = "设置粗标注阈值Entropy出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )

        },
        getRoughThr(){
            console.log(this.currentframe, this.docid);
            this.axios.get('ocr/getRoughThr/?currentframe='+this.currentframe+"&docid="+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let thrinfo = response.data.body;
                            this.projection_thr_strict = thrinfo.projection_thr_strict;
                            this.projection_thr_easing = thrinfo.projection_thr_easing;
                            this.entropy_thr= thrinfo.entropy_thr;
                            console.log(response.data.body);
                        }else{
                            this.msg = "获取粗标注阈值出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )
        },
    },
    computed: {
        chartOption:function(){
            return this.$store.getters.getRecommenttip_option;
        },
        docid:function(){
            return this.$route.query.docid;
        },
    },
    watch: {
        currentframe:{
            handler:function(value){
                console.log(value);
                this.getRoughThr();
            },
        },

    },
};
</script>

<style scoped>
#main{
    position:absolute;
    top:0rem;
    width:100%;
    height:100%;
}
#recommentchart{
    position:absolute;
    top:0rem;
    width:100%;
    height:88%;
}
#optionSet{
    position:absolute;
    top:88%;
    width:100%;
    height:12%;
}
.tip{
    position:absolute;
    width:34%;
    height:100%;
    display: grid;
    align-items: center;
    text-align:right;
    font-size:1.2rem;
}
/deep/ .el-input__inner{
    height:100%;
    padding:0;
    font-size:1.2rem;
}
.el-input{
    position:absolute;
    left:34%;
    width:65.5%;
    height:100%;
}
#projection_easing{
    position:absolute;
    top:0;
    width:30%;
    height:100%;
}
#projection_strict{
    position:absolute;
    top:0;
    left:33.4%;
    width:30%;
    height:100%;
}
#entropy{
    position:absolute;
    top:0;
    left:66.67%;
    width:30%;
    height:100%;
}
</style>
