<template>
    <div id="main">
        <div id="toolmode">
            <div id="manual">
                <el-radio v-model="ocrtoolmode" label="manual" :disabled="ocrlabelmode==='pan'?true:false">manual(ctrl-f)</el-radio>
            </div>
            <div id="recomment">
                <el-radio v-model="ocrtoolmode" label="recomment" :disabled="ocrlabelmode==='pan'?true:false">recomment(ctrl-a)</el-radio>
            </div>
            <div id="merge">
                <el-radio v-model="ocrtoolmode" label="merge" :disabled="ocrlabelmode==='pan'?true:false">merge(ctrl-c)</el-radio>
            </div>
            <div id="delete">
                <el-radio v-model="ocrtoolmode" label="delete" :disabled="ocrlabelmode==='pan'?true:false">delete(ctrl-d)</el-radio>
            </div>
            <div id="clear">
                <el-button type="danger" @click="clear_page">page clear</el-button>
            </div>
        </div>
        <div id="labelmode">
            <div id="drawdiv">
                <el-radio v-model="ocrlabelmode" label="draw">draw(ctrl-e)</el-radio>
            </div>
            <div id="pandiv">
                <el-radio v-model="ocrlabelmode" label="pan">pan(ctrl-p)</el-radio>
            </div>
        </div>
    </div>
</template>

<script>

export default {
	name: "Ocrmode",
    data() {
        return {
            ocrlabelmode:"draw",
            ocrtoolmode:"manual",
        }
    },
    props: ['currentframe', 'docid'],
    computed() {
    },
    mounted() {
        this.ocrlabelmode=this.$store.getters.getAILabelmode;
        this.ocrtoolmode=this.$store.getters.getAIToolmode;
        window.addEventListener('keydown', this.capMode, true);
    },
    beforeDestroy() {
        window.removeEventListener('keydown', this.capMode, true);
    },
    methods: {
        yolo_labeling(){
            this.axios.get('ocr/yoloLabeling/?docid='+this.docid+"&currentframe="+this.currentframe).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            console.log(response.data.body);
                            // 通知父组件已经更新标注
                            this.$emit('refresh');
                        }else{
                            this.msg = "yolo labeling出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )
        },

        capMode(event){
            const e = event||window.event||arguments.callee.caller.arguments[0];
            if(!e) return;
            if(e.repeat){
                return ;
            }
            const {ctrlKey, key} = e;
            if(ctrlKey && key=='f'){
                if(this.ocrlabelmode=="pan"){
                    let message={
                        "type":"warning",
                        "text":"pan模式禁用tool切换,请先切换draw模式",
                    }
                    this.$store.commit("addMessagetip",message);
                }else{
                    this.ocrtoolmode="manual";
                }
                e.preventDefault();
            }
            if(ctrlKey && key=='a'){
                if(this.ocrlabelmode=="pan"){
                    let message={
                        "type":"warning",
                        "text":"pan模式禁用tool切换,请先切换draw模式",
                    }
                    this.$store.commit("addMessagetip",message);
                }else{
                    this.ocrtoolmode="recomment";
                }
                e.preventDefault();
            }
            if(ctrlKey && key=='c'){
                if(this.ocrlabelmode=="pan"){
                    let message={
                        "type":"warning",
                        "text":"pan模式禁用tool切换,请先切换draw模式",
                    }
                    this.$store.commit("addMessagetip",message);
                }else{
                    this.ocrtoolmode="merge";
                }
                e.preventDefault();
            }
            if(ctrlKey && key=='d'){
                if(this.ocrlabelmode=="pan"){
                    let message={
                        "type":"warning",
                        "text":"pan模式禁用tool切换,请先切换draw模式",
                    }
                    this.$store.commit("addMessagetip",message);
                }else{
                    this.ocrtoolmode="delete";
                }
                e.preventDefault();
            }
            if(ctrlKey && key=='p'){
                this.ocrlabelmode="pan";
                e.preventDefault();
            }
            if(ctrlKey && key=='e'){
                this.ocrlabelmode="draw";
                e.preventDefault();
            }
            if(ctrlKey && key=='y'){
                this.yolo_labeling();
                e.preventDefault();
            }
        },
    },
    watch: {
        ocrlabelmode:{
            handler:function(value){
                this.$store.commit("setAILabelmode",value);
                let message={
                    "type":"notice",
                    "text":"指针模式:"+value,
                }
                this.$store.commit("addMessagetip",message);
            },
        },
        ocrtoolmode:{
            handler:function(value){
                this.$store.commit("setAIToolmode",value);
                let message={
                    "type":"notice",
                    "text":"标注模式:"+value,
                }
                this.$store.commit("addMessagetip",message);
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
#toolmode{
    position:absolute;
    top:0rem;
    width:100%;
    height:83.33%;
}
#manual{
    position:absolute;
    top:0%;
    width:calc(100% - 1rem);
    height:20%;
    text-align:left;
    left: 0.5rem;
}
#recomment{
    position:absolute;
    top:20%;
    width:calc(100% - 1rem);
    height:20%;
    text-align:left;
    left: 0.5rem;
}
#merge{
    position:absolute;
    top:40%;
    width:calc(100% - 1rem);
    height:20%;
    text-align:left;
    left: 0.5rem;
}
#delete{
    position:absolute;
    top:60%;
    height:20%;
    width:calc(100% - 1rem);
    text-align:left;
    left: 0.5rem;

}
#clear{
    position:absolute;
    top:80%;
    height:20%;
    width:calc(100% - 1rem);
    text-align:left;
    left: 0.5rem;

}
#labelmode{
    position:absolute;
    top:83.34%;
    width:100%;
    height:16.66%;

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
/deep/ .el-radio{
    top: calc(50% - 0.75rem);
    height:1.5rem;
}
/deep/ .el-radio__label{
    font-size: 1.2rem;
}
</style>
