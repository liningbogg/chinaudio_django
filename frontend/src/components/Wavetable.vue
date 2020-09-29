<template>
    <div class="wavetable">
        <el-table :data="waves"  ref="wavesTable" min-height="99.6%">
            <el-table-column prop="title" label="标题" align="center" min-width="32%"></el-table-column>
            <el-table-column prop="frameTotal" label="总帧数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="frameLabeled" label="已标记帧数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="percentLabeled" label="已标记比例" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="frameCurrent" label="当前帧号" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="nfft" label="nfft" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="waveid" label="操作" min-width="16%" align="center">
                <template slot-scope="scope">
                    <router-link :to="{path:'/Wavelabeling',query: {waveid: scope.row.waveid}}">标注</router-link>
                </template>
            </el-table-column>
        </el-table>
    </div>
</template>

<script>

export default {
	name: "Wavetable",
    data() {
        return {
            waves:null,
        }
    },
    mounted() {
        this.wavesFromBackend();
    },

    beforeDestroy() {
    },
    methods: {
        wavesFromBackend(){
            this.axios.get('target/waves').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.waves = response.data.body;
                        }else{
                            this.msg = "获取wave列表信息出错,原因:"+response.data.tip;
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
.wavetable{
    height:100%;
    overflow-y:auto;
}
</style>
