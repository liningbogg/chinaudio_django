<template>
    <div class="docassisttable" ref="docassist">
        <el-table :data="docsassist" ref="docsassistTable" min-height="99.6%" :height="tableHeight">
            <el-table-column prop="title" label="文档" align="center" min-width="26%"></el-table-column>
            <el-table-column prop="frameNum" label="帧数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="currentframe" label="当前帧" min-width="13%" align="center"></el-table-column>
            <el-table-column prop="labelNum" label="样本总数" min-width="13%" align="center"></el-table-column>
            <el-table-column prop="userlabelNum" label="用户样本数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="assistnum" label="协助数" min-width="10%" align="center"></el-table-column>
            <el-table-column  label="操作" min-width="16%" align="center">
                <template slot-scope="scope">
                    <router-link :to="{path:'/Ocrlabeling',query: {docid: scope.row.id}}">协助</router-link>
                </template>
            </el-table-column>
        </el-table>
        <!--
        <el-button
            type="text"
            icon="el-icon-update"
            @click="handleUpdate()"
            >
            更新
        </el-button>
        -->
    </div>
</template>

<script>

export default {
	name: "Docassisttable",
    data() {
        return {
            docsassist:null,
            tableHeight:null,
        }
    },
    mounted() {
        this.tableHeight=this.$refs.docassist.offsetHeight*0.95;
        this.docsassistFromBackend();
    },

    beforeDestroy() {
    },
    methods: {
        handleUpdate(){
            this.axios.get('ocr/testtmp/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            console.log(response.data.body);
                        }else{
                            this.msg = "临时测试出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
            
        },
        docsassistFromBackend(){
            this.axios.get('ocr/get_docsassist/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.docsassist = response.data.body;
                        }else{
                            this.msg = "获取doc协助列表信息出错,原因:"+response.data.tip;
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
.docassisttable{
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
