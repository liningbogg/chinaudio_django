<template>
    <div class="doctable" ref="doc">
        <el-table :data="docs" ref="docsTable" min-height="99.6%" :height="tableHeight">
            <el-table-column prop="title" label="文档" align="center" min-width="26%"></el-table-column>
            <el-table-column prop="frameNum" label="帧数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="currentframe" label="当前帧" min-width="13%" align="center"></el-table-column>
            <el-table-column prop="labelNum" label="样本总数" min-width="13%" align="center"></el-table-column>
            <el-table-column prop="userlabelNum" label="用户样本数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="assistnum" label="协助数" min-width="10%" align="center"></el-table-column>
            <el-table-column  label="操作" min-width="16%" align="center">
                <template slot-scope="scope">
                    <router-link :to="{path:'/Ocrlabeling',query: {docid: scope.row.id, title: scope.row.title}}">标注</router-link>
                </template>
            </el-table-column>
        </el-table>
    </div>
</template>

<script>

export default {
	name: "Doctable",
    data() {
        return {
            docs:null,
            tableHeight:null,
        }
    },
    mounted() {
        this.tableHeight=this.$refs.doc.offsetHeight*0.95;
        this.docsFromBackend();
    },

    beforeDestroy() {
    },
    methods: {
        docsFromBackend(){
            this.axios.get('ocr/get_docs/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.docs = response.data.body;
                        }else{
                            this.msg = "获取doc列表信息出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },

    },
    
};
</script>

<style scoped>
.doctable{
    height:100%;
    overflow-y:auto;
}

/deep/ .el-table__body tr td .cell{
    padding-right:0rem;
    padding-left:0rem;
}
/deep/ .el-input__inner{
    padding:0rem;
    border-radius:0rem;
    text-align:center;
}

</style>
