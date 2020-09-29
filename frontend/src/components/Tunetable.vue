<template>
    <div class="tunetable" ref="tune">
        <el-table :data="tunes"  ref="tunesTable" min-height="99.6%" border :height="tableHeight" highlight-current-row cell-style="padding:0px;border-color:blue;border-width:0.05rem;border-style:solid;">
            <el-table-column prop="tunename" label="音调"  min-width="16%"  style="margin:0px;padding:0px">
                <template slot-scope="scope" >
                    <el-input v-model="scope.row.tunename" :data="scope.row.tunename" style="margin-left:0px;width:100%;border-color:blue;border-width:0.05rem;border-style:solid;"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="do" label="do" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.do" :data="scope.row.do" ></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note1" label="1弦" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note1" :data="scope.row.note1" size="large"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note2" label="2弦" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note2" :data="scope.row.note2"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note3" label="3弦" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note3" :data="scope.row.note3"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note4" label="4弦" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note4" :data="scope.row.note4"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note5" label="5弦" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note5" :data="scope.row.note5"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note6" label="6" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note6" :data="scope.row.note6"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="note7" label="7弦" min-width="8%">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.note7" :data="scope.row.note7"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="a4" label="a4" min-width="8%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.a4" :data="scope.row.a4"></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作" min-width="10%" align="center">
                <template slot-scope="scope">
                    <el-button
                        v-if="scope.row != {}"
                        type="text"
                        icon="el-icon-update"
                        @click="handleUpdate(scope.row)"
                        >
                        更新
                    </el-button>
                    <el-button
                        v-if="scope.row == {}"
                        type="text"
                        icon="el-icon-add"
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
        const that = this;
    },

    beforeDestroy() {
    },
    methods: {
        tunesFromBackend(){
            this.axios.get('target/tunes').then(
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

<style scoped lang="less">
.tunetable{
    height:100%;
    overflow-y:auto;
}

</style>
