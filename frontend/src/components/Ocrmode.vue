<template>
    <div id="main">
        <div id="toolmode">
        </div>
        <div id="labelmode">
            <div id="drawdiv">
                <el-radio v-model="ocrlabelmode" label="draw">draw</el-radio>
            </div>
            <div id="pandiv">
                <el-radio v-model="ocrlabelmode" label="pan">pan</el-radio>
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
        }
    },
    mounted() {
    },
    beforeDestroy() {
    },
    methods: {
    },
    watch: {
        ocrlabelmode:{
            handler:function(value){
                this.$store.commit("setAILabelmode",value);
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
#toolmode{
    position:absolute;
    top:0rem;
    width:100%;
    height:50%;
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;

}
#labelmode{
    position:absolute;
    top:50%;
    width:100%;
    height:50%;
    border-color:red;
    border-width:0.05rem;
    border-style:solid;

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
    top: calc(50% - 6px);
}
</style>
