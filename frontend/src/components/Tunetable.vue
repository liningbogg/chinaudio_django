<template>
    <div class="tunetable" ref="tune">
        <el-table :data="tunes"  ref="tunesTable" min-height="99.6%"  :height="tableHeight" highlight-current-row cell-style="margin:0px;padding:0px;width=100%" size="mini">
            <el-table-column prop="tunename" label="音调"  min-width="12%" align="center">
                <template slot-scope="scope" >
                    <el-input v-model="scope.row.tunename" :data="scope.row.tunename" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="do" label="do" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.do" :data="scope.row.do" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note1" label="1弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note1" :data="scope.row.note1" size="mini" style="padding-left:0px;margin:0"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note2" label="2弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note2" :data="scope.row.note2" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note3" label="3弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note3" :data="scope.row.note3" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note4" label="4弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note4" :data="scope.row.note4" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note5" label="5弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note5" :data="scope.row.note5" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note6" label="6弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note6" :data="scope.row.note6" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note7" label="7弦" min-width="7%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note7" :data="scope.row.note7" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="a4" label="a4" min-width="10%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.a4" :data="scope.row.a4" size="mini"></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作" min-width="20%" align="center">
                <template slot-scope="scope">
                    <el-button
                        v-if="scope.row.status=='edit'"
                        type="text"
                        icon="el-icon-refresh"
                        @click="handleUpdate(scope.row)"
                        size="mini"
                        >
                        更新
                    </el-button>
                    <el-button
                        v-if="scope.row.status=='edit'"
                        type="text"
                        icon="el-icon-delete"
                        @click="handleDelete(scope.row)"
                        size="mini"
                        >
                        删除
                    </el-button>
                    <el-button
                        v-if="scope.row.status=='add'"
                        type="text"
                        icon="el-icon-plus"
                        size="mini"
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
	name: "Tunetable",
    data() {
        return {
            tunes:null,
            tableHeight:null,
        }
    },
    mounted() {
        this.tableHeight=this.$refs.tune.offsetHeight*0.95;
        console.log(this.tableHeight);
        this.tunesFromBackend();
    },

    beforeDestroy() {
    },
    methods: {
        tunesFromBackend(){
            this.axios.get('target/tunes/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.tunes = response.data.body;
                            console.log(this.tunes)
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

.tunetable{
    height:100%;
    overflow-y:auto;
}
</style>
