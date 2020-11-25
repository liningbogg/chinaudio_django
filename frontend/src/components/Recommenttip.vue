<template>
<div id="main">
    <div id="recommentchart">
        <v-chart  :options="chartOption" style="height:100%;width:100%" autoresize="true"/>
    </div>
    <div id="optionSet">
        <div id="projection_easing">
            <div class="tip">easing</div>
            <el-input v-model="projection_thr_easing" placeholder="proj_easing" type="number" @change="set_easing"></el-input>
        </div>
        <div id="projection_strict">
            <div class="tip">strict</div>
            <el-input v-model="projection_thr_strict" placeholder="proj_strict" type="number" @change="set_strict"></el-input>
        </div>
        <div id="entropy">
            <div class="tip">entropy</div>
            <el-input v-model="entropy_thr" placeholder="entropy_thr" type="number" @change="set_entropy"></el-input>
        </div>
    </div>
</div>
</template>

<script>

export default {
	name: "Recommenttip",
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
    },
    computed: {
        chartOption:function(){
            return this.$store.getters.getRecommenttip_option;
        },
    },
    watch: {

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
    width:33.3%;
    height:100%;
}
#projection_strict{
    position:absolute;
    top:0;
    left:33.4%;
    width:33.3%;
    height:100%;
}
#entropy{
    position:absolute;
    top:0;
    left:66.67%;
    width:33.25%;
    height:100%;
}
</style>
