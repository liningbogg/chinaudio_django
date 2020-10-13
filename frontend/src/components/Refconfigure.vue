<template>
<div id="main">
    <div id="refselect">
        <el-select v-model="referenceselect" placeholder="参考算法"  @change="handleSelect" style="width:100%">
            <el-option key="0" label="comb" value="comb"></el-option>
            <el-option key="1" label="combDescan" value="combDescan"></el-option>
        </el-select>
    </div>
    <div id="refinfo">
        <div id="all">
        应有{{formInline.all}}帧
        </div>
    </div>
<div>
</template>

<script>

export default {
	name: "Refconfigure",
    data() {
        return {
            waveid:null,
            referenceselect:null,
            formInline:{
                all:14,
                done:null,
            }
        }
    },
    mounted() {
        this.waveid = this.$route.query.waveid;
    },
    beforeDestroy() {
    },
    methods: {
        configureFromBackend(){
            this.axios.get('target/getLabelingconfigure/?waveid='+this.waveid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.configure = response.data.body;
                            this.title = this.configure[0].title;
                            this.configure[0].currentframe=this.currentframe;
                        }else{
                            this.msg = "获取标注配置信息出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },

    },
};
</script>

<style scoped lang="less">
/deep/ .el-input--suffix .el-input__inner{
    height:2rem;
}
/deep/ .el-input__icon{
    line-height:100%;
}
#main{
    top:0rem;
    left:0rem;
    width:100%;
    height:100%;
}
#refselect{
    top:0rem;
    position:absolute;
    height:100%;
    width:calc(20% - 0.2rem);
    border-color:black;
    border-width:0.05rem;
    border-style:solid;
}
#refinfo{
    top:0rem;
    position:absolute;
    left:20%;
    height:100%;
    text-align:left;
    width:calc(80% - 0.2rem);
    border-color:pink;
    border-width:0.05rem;
    border-style:solid;
}
#all{
    top:0rem;
    left:0rem;
    position:absolute;
    height:100%;
    width:calc(25% - 0.2rem);
    line-height:2rem;
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
</style>
