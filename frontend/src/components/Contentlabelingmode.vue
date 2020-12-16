<template>
    <div id="main">
        <div id="labelmode">
            <div id="drawdiv">
                <el-radio v-model="contentLabelingmode" label="labeling">labeling(ctrl+e)</el-radio>
            </div>
            <div id="pandiv">
                <el-radio v-model="contentLabelingmode" label="configure">configure(ctrl+c)</el-radio>
            </div>
        </div>
        <div id="tip">
            {{modeinfo}}
        </div>
    </div>
</template>

<script>

export default {
	name: "Contentlabelingmode",
    data() {
        return {
            modeinfo:null,
            contentLabelingmode:null,
        }
    },
    computed:{
    },
    mounted() {
        this.contentLabelingmode=this.$store.getters.getContentlabelingmode;
        window.addEventListener('keydown', this.capMode, true);
    },
    beforeDestroy() {
        window.removeEventListener('keydown', this.capMode, true);
    },
    methods: {
        capMode(event){
            const e = event||window.event||arguments.callee.caller.arguments[0];
            if(!e) return;
            const {ctrlKey, key} = e;
            if(ctrlKey && key=='l'){
                this.contentLabelingmode="labeling";
                e.preventDefault();
            }
            if(ctrlKey && key=='c'){
                this.contentLabelingmode="configure";
                e.preventDefault();
            }
        },
    },
    watch: {
        contentLabelingmode:{
            handler:function(value){
                this.$store.commit("setContentlabelingmode",value);
                let message={
                    "type":"notice",
                    "text":"模式:"+value,
                }
                this.$store.commit("addMessagetip",message);
                if(value == "labeling"){
                    this.modeinfo = "标注模式";
                }else{
                    this.modeinfo = "配置模式";
                }
            },
        },
    },
};
</script>

<style scoped>
.el-button{
    top:0rem;
    left:0rem;
    width:100%;
    height:100%;
    padding:0;
}
#main{
    position:absolute;
    top:0rem;
    width:100%;
    height:100%;
}
#labelmode{
    position:absolute;
    top:0;
    left:0;
    width:60%;
    height:100%;
}
#drawdiv{
    position:absolute;
    width:50%;
    height:100%;
}
#pandiv{
    position:absolute;
    left:50%;
    width:50%;
    height:100%;
}
#tip{
    position:absolute;
    top:0;
    left:60%;
    width:40%;
    height:100%;
    line-height:2rem;
}
/deep/ .el-radio{
    top: calc(50% - 0.75rem);
    height:1.5rem;
}
/deep/ .el-radio__label{
    font-size: 1.2rem;
}
</style>
