<template>
<div id="main">
    <div id="doctable" ref="doc">
        <el-table :data="docs" ref="docsTable" min-height="99.6%" :height="tableHeight">
            <el-table-column type="selection" min-width="4%"/>
            <el-table-column prop="title" label="文档" align="center" min-width="16%"></el-table-column>
            <el-table-column prop="frameNum" label="帧数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="currentframe" label="当前帧" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="labelNum" label="样本总数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="userlabelNum" label="用户样本数" min-width="10%" align="center"></el-table-column>
            <el-table-column prop="assist" label="协助勾选" min-width="10%" align="center">
                <template slot-scope="scope">
                    <el-select v-model="scope.row.assistselected"  multiple collapse-tags style="width:100%;height:100%;" placeholder="请选择协助数据" @change="updateFrameSelected(scope.row)">
                        <el-option
                                v-for="item in scope.row.assist"
                                :key="item.id"
                                :label="item.name"
                                :value="item.id">
                        </el-option>
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column prop="frameselected" label="帧选择" min-width="26%" align="center">
                <template slot-scope="scope">
                    <el-input v-model="scope.row.frameselected" :data="scope.row.frameselected" ></el-input>
                </template>
            </el-table-column>
        </el-table>
    </div>
    <div id="sampleconf">
        <div class="contain" id="is_resize">
            <el-form :inline="true" class="demo-form-inline" style="height:100%;width:100%;">
                <el-form-item style="position:absolute;left:0%;width:25%;height:100%;line-height:100%;text-align:center;">
                    <el-switch
                        v-model="isresize"
                        active-text="resize">
                    </el-switch>
                </el-form-item>
                <el-form-item label="width" style="position:absolute;left:25%;width:25%;height:100%;line-height:100%;text-align:center;" v-if="isresize">
                    <el-input type="number" v-model.number="image_width" placeholder="width" ></el-input>
                </el-form-item>
                <el-form-item label="height" style="position:absolute;left:50%;width:25%;height:100%;line-height:100%;text-align:center;" v-if="isresize">
                    <el-input type="number" v-model.number="image_height"  placeholder="height"></el-input>
                </el-form-item>
                <el-form-item label="fit" style="position:absolute;left:75%;width:25%;height:100%;line-height:100%;text-align:center;" v-if="isresize">
                    <el-select v-model="fittype"  placeholder="填充方式"  style="height:100%;">
                        <el-option
                            key= "fill"
                            label="fill"
                            value="fill">
                        </el-option>
                        <el-option
                            key= "contain"
                            label="contain"
                            value="contain">
                        </el-option>
                    </el-select>
                </el-form-item>
            </el-form>
        </div>
        <div class="contain" id="is_rotate">
            <el-switch
                v-model="isrotate"
                active-text="rotate"
                style="position:absolute;width:100%;left:0;"
            >
            </el-switch>
        </div>
        <div class="contain" id="is_split">
            <el-form :inline="true" class="demo-form-inline" style="height:100%;width:100%;font-size:1.5rem">
                <el-form-item style="position:absolute;left:0%;width:25%;height:100%;line-height:100%;text-align:center;">
                    <el-switch
                        v-model="issplit"
                        active-text="split">
                    </el-switch>
                </el-form-item>
                <el-form-item label="width" style="position:absolute;left:25%;width:25%;height:100%;line-height:100%;text-align:center;" v-if="issplit">
                    <el-input type="number" v-model.number="split_width" placeholder="width" ></el-input>
                </el-form-item>
                <el-form-item label="height" style="position:absolute;left:50%;width:25%;height:100%;line-height:100%;text-align:center;" v-if="issplit">
                    <el-input type="number" v-model.number="split_height"  placeholder="height"></el-input>
                </el-form-item>
                <el-form-item label="overlap" style="position:absolute;left:75%;width:25%;height:100%;line-height:100%;text-align:center;" v-if="issplit">
                    <el-input type="number" v-model.number="split_overlap" placeholder="overlap"></el-input>
                </el-form-item>
            </el-form>
        </div>
    </div>

    <div id="trainconf">
        <el-form :inline="true" class="demo-form-inline" style="height:100%;width:100%;">
            <el-form-item label="trainsize" style="position:absolute;left:0%;width:12%;height:100%;line-height:100%;text-align:center;">
                <el-input type="number" v-model.number="trainsize"  placeholder="trainsize" ></el-input>
            </el-form-item>
            <el-form-item label="epoches" style="position:absolute;left:12.5%;width:12%;height:100%;line-height:100%;text-align:center;">
                <el-input type="number" v-model.number="trainepoches"  placeholder="epoches" step=100 min=100 max=100000></el-input>
            </el-form-item>
            <el-form-item label="batch" style="position:absolute;left:25%;width:12%;height:100%;line-height:100%;text-align:center;">
                <el-input type="number" v-model.number="trainbatch"  placeholder="batchsize" ></el-input>
            </el-form-item>
            <el-form-item label="modelscale" style="position:absolute;left:37.5%;width:12%;height:100%;line-height:100%;text-align:center;">
                <el-select v-model="modelscale"  placeholder="模型选择"  style="height:100%;">
                    <el-option
                        key= "yolov5s"
                        label="yolov5s"
                        value="yolov5s">
                    </el-option>
                    <el-option
                        key= "yolov5m"
                        label="yolov5m"
                        value="yolov5m">
                    </el-option>
                    <el-option
                        key= "yolov5l"
                        label="yolov5l"
                        value="yolov5l">
                    </el-option>
                    <el-option
                        key= "yolov5x"
                        label="yolov5x"
                        value="yolov5x">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="device" style="position:absolute;left:50%;width:12%;height:100%;line-height:100%;text-align:center;">
                <el-select v-model="traindevice"  placeholder="模型选择"  style="height:100%;">
                    <el-option
                        key= "gpu"
                        label="gpu"
                        value="gpu">
                    </el-option>
                    <el-option
                        key= "cpu"
                        label="cpu"
                        value="cpu">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="" style="position:absolute;left:62.5%;width:12%;height:100%;line-height:100%;text-align:center;">
                    <el-switch
                        v-model="contented"
                        active-text="contented"
                        @change="handleContented()"
                        >
                    </el-switch>
            </el-form-item>
            <el-form-item label="" style="position:absolute;left:75%;width:9.5%;height:100%;line-height:100%;text-align:center;">
                <el-input  v-model="trainname" placeholder="训练名称" style="width:100%;height:100%;">
                </el-input>
            </el-form-item>
            <el-form-item label="" style="position:absolute;left:85%;height:100%;width:12.5%;">
                <el-button
                    type="text"
                    icon="el-icon-s-data"
                    @click="handleTrain()"
                    >
                    开始训练
                </el-button>
            </el-form-item>
        </el-form>
    </div>
</div>
</template>

<script>

export default {
	name: "Traindoctable",
    data() {
        return {
            docs:null,
            tableHeight:null,
            isresize:false,
            issplit:false,
            isrotate:false,
            modelscale:"yolov5m",
            traindevice:"gpu",
            trainsize:640,
            trainepoches:4000,
            trainbatch:12,
            image_width:640,
            image_height:640,
            split_overlap:0.25,
            split_width:640,
            split_height:640,
            trainname:"",
            contented:true,
            fittype:"contain",
        }
    },
    mounted() {
        this.ocrmodelid = this.$route.query.ocrmodelid;
        this.ocrmodelname = this.$route.query.ocrmodelname;
        this.tableHeight=this.$refs.doc.offsetHeight*0.95;
        this.traindocsFromBackend();
    },

    beforeDestroy() {
    },
    methods: {
        handleTrain(){
            let confirmstr = "isrotate:"+this.isrotate+
                "<br/>isresize:"+this.isresize+
                "<br/>issplit:"+this.issplit+
                "<br/>trainsize:"+this.trainsize+
                "<br/>trainbatch:"+this.trainbatch+
                "<br/>trainepoches:"+this.trainepoches+
                "<br/>scale:"+this.modelscale+
                "<br/>device:"+this.traindevice+
                "<br/>trainname:"+this.trainname+
                "<br/>检查以上内容，开始训练请按确认。";
            this.$confirm(confirmstr, '训练信息确认', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                dangerouslyUseHTMLString: true,
                type: 'info'
                }
            ).then(() => {
                // 向后端发送训练任务
                let docs=Array()
                for(let doc of this.docs){
                    docs.push({'docid':doc.id, 'frameselected':doc.frameselected, 'assistselected':doc.assistselected});
                }
                this.axios.get('ocr/trainSubmit/?ocrmodelid='+this.ocrmodelid+'&isrotate='+this.isrotate+'&isresize='+this.isresize+'&image_width='+this.image_width+'&image_height='+this.image_height+'&fittype='+this.fittype+'&is_split='+this.issplit+'&split_width='+this.split_width+'&split_height='+this.split_height+'&split_overlap='+this.split_overlap+'&trainsize='+this.trainsize+'&trainbatch='+this.trainbatch+'&trainepoches='+this.trainepoches+'&scale='+this.modelscale+'&device='+this.traindevice+'&docs='+JSON.stringify(docs)+'&trainname='+this.trainname).then(
                    (response) => {
                        if(response){
                            console.log(response.data);
                            if(response.data.status=="success"){
                                this.$message({
                                    type: 'success',
                                    message: '训练已经提交，将跳转至训练页!'
                                });
                                this.$router.push({
                                    path:'/trainlist',
                                });

                            }else{
                                this.msg = "提交训练出错,原因:"+response.data.tip;
                                console.log(this.msg);
                            }
                        }   
                    }
                ) 

            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        },
        updateFrameSelected(docinfo){
            console.log(docinfo);
            this.axios.get('ocr/getDocframelist/?docid='+docinfo.id+"&assistselected="+JSON.stringify(docinfo.assistselected)+"&contented="+this.contented).then(
                (response) => {
                    if(response){
                        console.log(response.data);
                        if(response.data.status=="success"){
                            docinfo.frameselected = response.data.body.frameselected;
                        }else{
                            this.msg = "获取frame列表信息出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },
        handleContented(){
            for(let doc of this.docs){
                this.updateFrameSelected(doc);
            }
        },
        traindocsFromBackend(){
            this.axios.get('ocr/get_traindocs/?ocrmodelid='+this.ocrmodelid).then(
                (response) => {
                    if(response){
                        console.log(response.data);
                        if(response.data.status=="success"){
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
#doctable{
    height:100%;
    width:100%;
    overflow-y:auto;
}
#doctable{
    position:absolute;
    height:79%;
    width:100%;
    overflow-y:auto;
}
#sampleconf{
    position:absolute;
    top:80%;
    height:8%;
    width:100%;
}
#is_resize{
    position:absolute;
    top:0;
    left:8%;
    height:100%;
    width:42%;
}
#is_rotate{
    position:absolute;
    top:0;
    height:100%;
    left:0%;
    width:6%;
}
#is_split{
    position:absolute;
    top:0;
    height:100%;
    left:52%;
    width:42%;
}
#trainconf{
    position:absolute;
    top:90%;
    height:8%;
    width:100%;
}
.el-switch{
    height:100%;
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
/deep/ .el-table td, .el-table th{
    padding:0;
}
.el-input{
    height:100%;
}
/deep/ .el-select>.el-input {
    height:100%;
    line-height:100%;
}
/deep/ .el-form-item{
    margin-bottom:0;
    height:100%;
    line-height:100%;
}
/deep/ .el-form--inline .el-form-item {
    margin-right: 0;
    height:100%;
    line-height:100%;
}
/deep/ .el-form--inline .el-form-item__label{
    float:left;
    height:100%;
    line-height:100%;
    text-align:right;
    padding:0;
}
/deep/ .el-form-item__label{
    max-width:40%;
    line-height:100%;
    height:100%;
    text-align: right;
    display: grid;
    align-items: center;
}
/deep/ .el-form-item__content{
    max-width:59.5%;
    line-height:100%;
    height:100%;
}
/deep/ .el-form-item .el-input__inner{
    height:100%;
    line-height:100%;
}
</style>
