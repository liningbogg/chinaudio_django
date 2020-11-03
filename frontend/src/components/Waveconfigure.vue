<template>
<div id="main">
    <div id="titleview">
        {{title}}
    </div>
    <div class="configuretable" ref="waveconfigure">
        <el-table :data="configure"  min-height="99.6%"  :height="tableHeight" highlight-current-row cell-style="margin:0px;padding:0px;width=100%" size="mini">
            <el-table-column prop="framenum" label="帧数"  min-width="10%" align="center">
            </el-table-column>
            <el-table-column prop="currentframe" label="当前帧" min-width="10%" align="center">
            </el-table-column>
            <el-table-column prop="nfft" label="nfft" min-width="10%" align="center">
            </el-table-column>
            <el-table-column prop="extend_rad" label="extend" min-width="9%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.extend_rad" :data="scope.row.extend_rad" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="toneextend_rad" label="tone_ext" min-width="11%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.toneextend_rad" :data="scope.row.toneextend_rad" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="nn_art" label="NNART" min-width="9%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.nn_art" :data="scope.row.nn_art" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="nn_op" label="NNOP" min-width="9%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.nn_op" :data="scope.row.nn_op" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="rmse" label="RMSE" min-width="9%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.rmse" :data="scope.row.rmse" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="pri_ref" label="主参考" min-width="15%" align="center">
            </el-table-column>
        </el-table>
    </div>
<div>
</template>

<script>

export default {
	name: "Waveconfigure",
    props: ['currentframe'],
    data() {
        return {
            waveid:null,
            configure:null,
            tableHeight:null,
            title:null,
        }
    },
    mounted() {
        this.waveid = this.$route.query.waveid;
        this.tableHeight=this.$refs.waveconfigure.offsetHeight*0.95;
        window.addEventListener('resize', () => {
            this.tableHeight=this.$refs.waveconfigure.offsetHeight*0.95;
        })
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
    
    watch: {
        currentframe:{
            handler:function(value){
                this.configureFromBackend();
                console.log(value);
            },
        } 
    },
};
</script>

<style scoped>
/deep/ .el-table__body tr td{
    padding:0rem;
    padding-right:0rem;
    padding-left:0rem;
}
/deep/ .el-table__body tr td .cell{
    padding:0rem;
    padding-right:0rem;
    padding-left:0rem;
}
/deep/ .el-table th>.cell {
    padding-right:0rem;
    padding-left:0rem;
    height:100%;
    text-align:center;
}
/deep/ .el-input__mini{
    padding:0rem;
    border-radius:0rem;
    text-align:center;
}
/deep/ .el-input__inner{
    padding:0rem;
    border-radius:0rem;
    text-align:center;
    height:100%;
    line-height:100%;
    font-size:2.0rem;
}
/deep/ .el-table--mini tr{
    padding:0rem;
}
/deep/ .el-table--mini th{
    padding:0rem;
}
/deep/ .el-input--mini{
    font-size:1rem;
}
/deep/ .el-table--mini{
    font-size:1rem;
}
/deep/ .el-table .cell{
    height:100%;
    line-height:100%;
}
#main{
    top:0rem;
    width:100%;
    height:100%;
}
#titleview{
    top:0rem;
    height:1.5rem;
    width:100%;
    font-size:1rem;

}
.h3{
    text-align:center;
    padding:0rem;
    margin:0rem;
}
.configuretable{
    top:1.5rem;
    height:calc(100% - 1.5rem);
    width:100%;
    overflow-y:auto;
}
</style>
