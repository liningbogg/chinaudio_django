<template>
<div id="main">
    <div id="calstft">
        <el-button type="primary" @click="stft_recalculate">stft计算</el-button>
    </div>
<div>
</template>
<script>
export default {
	name: "Localcal",
    data() {
        return {
            waveid:null,
        }
    },
    mounted() {
        this.waveid = this.$route.query.waveid;
    },
    beforeDestroy() {
    },
    methods: {
        stft_recalculate(){
            this.axios.get('target/calStft/?waveid='+this.waveid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let frameNum = response.data.body.frameNum;
                            alert("生成stft帧数:"+frameNum);
                        }else{
                            let msg = "计算stft出错,原因:"+response.data.tip;
                            alert(msg);
                        }
                    }   
                }
            ) 
        },
        
    },
};
</script>

<style scoped lang="less">
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
#calstft{
    top:0rem;
    position:absolute;
    height:100%;
    width:calc(24% - 0.2rem);
}
</style>
