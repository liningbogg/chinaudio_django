<template>
<div id="main">
    <div id="refselect">
        <el-select v-model="referenceselected" placeholder="参考算法"  @change="handleSelect" style="width:100%">
            <el-option key="0" label="all" value="all"></el-option>
            <el-option key="1" label="comb" value="comb"></el-option>
            <el-option key="2" label="combDescan" value="combDescan"></el-option>
        </el-select>
    </div>
    <div id="refinfo">
        <div id="framenum">
        应有{{formInline.framenumAll}}帧,现有{{formInline.framenumDone}}帧。
        </div>
        <div id="recalculate" v-if="this.referenceselected!='all'">
            <el-button type="primary" @click="recalculate()">计算</el-button>
        </div>
        <div id="refresh" v-if="this.referenceselected!='all'">
        </div>
        <div id="enable" v-if="this.referenceselected!='all'">
            <el-switch
                v-model="formInline.enable"
                active-text="启用"
                @change="handleEnable($event)"
            >
            </el-switch>
        </div>
        <div id="hasfilter" v-if="this.formInline.enable==true">
            <el-switch
                v-model="formInline.hasfilter"
                active-text="过滤"
                @change="handleFilter($event)"
            >
            </el-switch>
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
            referenceselected:"all",
            timer:null,
            formInline:{
                framenumAll:0,
                framenumDone:0,
                hasfilter:false,
                enable:false,
            }
        }
    },
    mounted() {
        this.waveid = this.$route.query.waveid;
        this.referenceinfoFromBackend();
    },
    beforeDestroy() {
    },
    methods: {
        handleSelect(){
            this.referenceinfoFromBackend();
        },
        calWatch(){
            if(this.formInline.framenumAll==this.formInline.framenumDone){
                clearInterval(this.timer);
            }else{
                this.referenceinfoFromBackend();
                console.log(this.formInline.framenumDone);
            }
        },

        handleEnable(val){
            let algorithm = this.referenceselected;
            if (val==true){
                this.axios.get('target/enableAlgorithm/?waveid='+this.waveid+"&algorithm="+algorithm).then(
                    response => {
                        if(response){
                            if(response.data.status==="success"){
                                console.log(response.data.body);
                            }else{
                                let msg = "启用算法出错,原因:"+response.data.tip;
                                console.log(msg);
                            }
                            this.referenceinfoFromBackend();
                        }   
                    }
                )    
            }else{
                this.axios.get('target/disableAlgorithm/?waveid='+this.waveid+"&algorithm="+algorithm).then(
                    response => {
                        if(response){
                            if(response.data.status==="success"){
                                console.log(response.data.body);
                            }else{
                                let msg = "禁用算法出错,原因:"+response.data.tip;
                                console.log(msg);
                            }
                            this.referenceinfoFromBackend();
                        }   
                    }
                )    
            }

        },

        recalculate(){
            let algorithm = this.referenceselected;
            this.axios.get('target/refRecalculate/?waveid='+this.waveid+"&algorithm="+algorithm).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.referenceinfoFromBackend();
                            this.timer = setInterval(this.calWatch, 1000);
                            setTimeout(() => {
                                clearInterval(this.timer)
                            }, 120000);
                        }else{
                            let msg = "计算ref出错,原因:"+response.data.tip;
                            console.log(msg);
                            this.referenceinfoFromBackend();
                        }
                    }   
                }
            ) 
        },
        
        handleFilter(val){
            console.log(val);
            let has_filter = val;
            let algorithm = this.referenceselected;
            this.axios.get('target/setReferenceFilter/?waveid='+this.waveid+"&algorithm="+algorithm+"&has_filter="+has_filter).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            console.log(response.data.body);
                        }else{
                            let msg = "设置ref过滤出错,原因:"+response.data.tip;
                            console.log(msg);
                        }
                        this.referenceinfoFromBackend();
                    }   
                }
            ) 
        },

        referenceinfoFromBackend(){
            let selected=new Array();
            if(this.referenceselected=="all"){
                selected.push("comb");
                selected.push("combDescan");
            }else{
                selected.push(this.referenceselected);
            }
            this.axios.get('target/getReferenceinfo/?waveid='+this.waveid+"&referenceselected="+JSON.stringify(selected)).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.formInline=response.data.body;
                        }else{
                            this.msg = "获取参考算法信息出错,原因:"+response.data.tip;
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
.el-button{
    top:0rem;
    left:0rem;
    width:100%;
    height:100%;
    padding:0;
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
    width:calc(24% - 0.2rem);
}
#refinfo{
    top:0rem;
    position:absolute;
    left:24%;
    height:100%;
    text-align:left;
    width:calc(76% - 0.2rem);
}
#framenum{
    top:0rem;
    left:0rem;
    position:absolute;
    height:100%;
    width:calc(40% - 0.2rem);
    line-height:2rem;
}
#recalculate{
    top:0rem;
    left:40%;
    position:absolute;
    height:100%;
    width:calc(14% - 0.2rem);
    line-height:2rem;
}
#refresh{
    top:0rem;
    left:54%;
    position:absolute;
    height:100%;
    width:calc(10% - 0.2rem);
    line-height:2rem;
}
#enable{
    top:0rem;
    left:64%;
    position:absolute;
    height:100%;
    width:calc(18% - 0.2rem);
    line-height:2rem;
}
#hasfilter{
    top:0rem;
    left:82%;
    position:absolute;
    height:100%;
    width:calc(18% - 0.2rem);
    line-height:2rem;
}
</style>
