<template>
    <div class="ocrmodeltable" ref="ocrmodel">
        <el-table :data="ocrmodels"  ref="tunesTable" min-height="99.6%"  :height="tableHeight" highlight-current-row cell-style="margin:0px;padding:0px;width=100%" >
            <el-table-column prop="name" label="名称"  min-width="18%" align="center">
                <template slot-scope="scope" >
                    <el-input v-model="scope.row.name" :data="scope.row.name" ></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="desc" label="描述" min-width="32%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.desc" :data="scope.row.desc"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="pdfselect" label="PDF集合" min-width="30%" align="center">
                <template slot-scope="scope">
                    <el-select v-model="scope.row.pdfselected"  multiple collapse-tags style="width:100%;" placeholder="请选择PDF" @change="handleChange">
                        <el-option
                                v-for="item in scope.row.pdfs"
                                :key="item.id"
                                :label="item.title"
                                :value="item.id">
                        </el-option>
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column label="操作" min-width="20%" align="center">
                <template slot-scope="scope">
                    <el-button
                        v-if="scope.row.status=='edit'"
                        type="text"
                        icon="el-icon-update"
                        @click="handleUpdate(scope.row)"
                        >
                        更新
                    </el-button>
                    <el-button
                        v-if="scope.row.status=='edit'"
                        type="text"
                        icon="el-icon-delete"
                        @click="handleDelete(scope.row)"
                        >
                        删除
                    </el-button>
                    <el-button
                        v-if="scope.row.status=='add'"
                        type="text"
                        icon="el-icon-plus"
                        @click="handleAdd()"
                        >
                        添加
                    </el-button>
                </template>
            </el-table-column>

        </el-table>
    </div>
</template>

<script>

export default {
	name: "Ocrmodeltable",
    data() {
        return {
            ocrmodels:null,
            tableHeight:null,
        }
    },
    mounted() {
        this.tableHeight=this.$refs.ocrmodel.offsetHeight*0.95;
        this.ocrmodelsFromBackend();
    },

    beforeDestroy() {
    },
    methods: {
        handleChange(){
            console.log(this.ocrmodels);
        },
        handleUpdate(item){
            let pdfselected = JSON.stringify(item.pdfselected);
            this.axios.get('ocr/updateOcrmodel/?name='+item.name+'&desc='+item.desc+"&id="+item.id+"&pdfselected="+pdfselected).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            alert(item.name+"已被更新");
                        }else{
                            this.msg = "更新模型列表信息出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            );
        },
        handleAdd(){
            let ocrmodel = this.ocrmodels[this.ocrmodels.length - 1];
            this.axios.get('ocr/createOcrmodel/?name='+ocrmodel.name+'&desc='+ocrmodel.desc).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.ocrmodelsFromBackend();
                        }else{
                            this.msg = "创建模型列表信息出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            );
        },
        ocrmodelsFromBackend(){
            this.axios.get('ocr/getOcrmodels/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.ocrmodels = response.data.body;
                            console.log(this.ocrmodels)
                        }else{
                            this.msg = "获取模型列表信息出错,原因:"+response.data.tip;
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
/deep/ .el-table__body tr td .cell{
    padding-right:0rem;
    padding-left:0rem;
}
/deep/ .el-input__inner{
    padding:0rem;
    border-radius:0rem;
    text-align:center;
}

.ocrmodeltable{
    height:100%;
    overflow-y:auto;
}
</style>
