<template>
    <div>
        <div id="customize">
            <el-form :inline="true" :model="formInline" class="demo-form-inline" style="height:100%">
                <el-form-item label="起始" style="position:absolute;left:25%;width:12%">
                    <el-input v-model="formInline.start" placeholder="起始位置"></el-input>
                </el-form-item>
                <el-form-item label="终止" style="position:absolute;left:37.5%;width:12%;height:100%">
                    <el-input v-model="formInline.end" placeholder="终止位置"></el-input>
                </el-form-item>
                <el-form-item style="position:absolute;left:50%;width:16%;">
                    <el-button type="primary" @click="customEvaluate" style="position:absolute;width:100%;height:100%">评估</el-button>
                </el-form-item>
                <el-form-item style="position:absolute;left:66%;width:16%;">
                    <el-button type="primary" @click="onPlaycustom" style="position:absolute;width:100%;height:100%" icon="el-icon-video-play" v-if="playstatusReady">播放</el-button>
                    <el-button type="primary" @click="onStopplay" style="position:absolute;width:100%;height:100%" icon="el-icon-video-pause" v-else>停止</el-button>
                </el-form-item>
                <el-form-item style="position:absolute;left:82%;width:17%;">
                    <el-switch
                        v-model="spectrogramOn"
                        active-text="时频图"
                        @change="handleEnable($event)"
                        >
                    </el-switch>
                </el-form-item>
            </el-form>
        </div>
        <div id="charts">
            <v-chart theme="ovilia-green" :options="chartOption" style="height:100%;width:100%" autoresize="true"/>
        </div>
        <div id="possible">
            <el-input
                type="textarea"
                :rows=8
                :readonly="true"
                v-model="possible_pos"
            >
            </el-input>
        </div>
    </div>
</template>

<script>
export default {
  name: 'Framesrc',
  props: ['currentframe'],
  data(){
    return{
        waveid:null,
        indexArr:null,
        possible_pos:null,
        phrase:null,
        playstatusReady:true,
        spectrogramOn:false,
        formInline:{
            start:null,
            end:null,
        },

        chartOption: {
            backgroundColor:"#f0f0f0",
            title : [
                {
                    show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                    left:'15%',

                    text:"Stft",//主标题文本，'\n'指定换行
                },
                {
                    show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                    left:'65%',
                    text:"Medium",//主标题文本，'\n'指定换行
                },
            ],

            dataZoom:[
                {
                    type: 'inside',
                    realtime: true,
                },
            ],
            xAxis: [
                {
                    data: null,
                    type: 'category',
                    axisLine: {onZero: true},
                },
                {
                    data: null,
                    type: 'category',
                    axisLine: {onZero: true},
                    gridIndex: 1,
                },
            ],
            yAxis: [
                {
                    scale: 'true',
                },
                {
                    gridIndex: 1,
                    scale: 'true',
                },
            ],

            series: [
                {
                    data: null,
                    name: "stft",
                    type: 'line',
                    lineStyle:{
                        normal:{
                            width:1,
                        },
                    },
                    symbol: 'none',
                    markLine: {
                        symbol: 'none',
                        silent: true,
                        data: [
                        ],
                        lineStyle: {
                            show: true,
                            color: '#0000ff',
                            type: 'solid',
                            width:0.5,
                        },
                        label:{
                            show: false,
                            formatter: (params) => {
                                let str = params.data.value;                                            
                                return str;
                            },
                        },
                    },
                },
                {
                    data: null,
                    name: "medium",
                    type: 'line',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    lineStyle:{
                        normal:{
                            width:1,
                        },
                    },
                    symbol: 'none',
                    markLine: {
                        symbol: 'none',
                        silent: true,
                        data: [
                        ],
                        lineStyle: {
                            show: true,
                            color: '#0000ff',
                            type: 'solid',
                            width:0.5,
                        },
                        label:{
                            show: false,
                            formatter: (params) => {
                                let str = params.data.value;                                            
                                return str;
                            },
                        },
                    },
                },
            ],
            grid:[
                {
                    left:'5%',
                    width:'40%',
                    top:'10%',
                    bottom:'15%',
                },
                {
                    left:'55%',
                    width:'40%',
                    top:'10%',
                    bottom:'15%',

                },
            ],
            toolbox: {
                show:true,
                feature:{
                    dataZoom: {
                        yAxisIndex:"none"
                    },
                    restore: {},
                    saveAsImage: {},
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    animation: false
                }
            },
            color:[
                '#ff0000',
                '#0000ff', 
                '#000000', 
                '#00ff00', 
                '#00ffff',
                '#ff00ff',
                '#006400',
                '#00008b',
                '#8b0000'
            ],

            legend: {
                show: true,
                x:"left",
                y:"bottom",
                orient:'horizontal',
                textStyle:{
                }
            },

        },

    }
  },
  methods:{
    drawCharts(nfft, fs, basefrq, stft, medium){
        let harmonics=new Array();
        basefrq=basefrq[0];
        console.log(basefrq);
        if(basefrq>60){
            for(let derivative=1;derivative<=Math.floor(4000.0/basefrq);derivative++){
                harmonics.push({"xAxis":derivative*basefrq*nfft/fs});
            }
        }
        /*mark*/
        this.chartOption.series[0].markLine.data=harmonics;

        let xAxis = new Array(stft.length);
        for(let key=0; key<xAxis.length; key++){
            xAxis[key]=key*fs/nfft;
        }
        this.chartOption.xAxis[0].data=xAxis;
        this.chartOption.series[0].data=stft;

        xAxis = new Array(medium.length);
        for(let key=0; key<xAxis.length; key++){
            xAxis[key]=key;
        }
        this.chartOption.xAxis[1].data=xAxis;
        this.chartOption.series[1].data=medium;
    },
    dataFromBackend(){
        this.axios.get('target/getPrimaryrefinfo/?waveid='+this.waveid+"&currentframe="+this.currentframe+"&cutoff=4000").then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let refinfo = response.data.body;
                        console.log(refinfo);
                        this.possible_pos = refinfo.possible_pos;
                        console.log(this.possible_pos);
                        this.drawCharts(refinfo.nfft, refinfo.fs, refinfo.basefrq, refinfo.stft, refinfo.medium);
                    }else{
                        this.msg = "获取basefrq失败,原因:"+response.data.tip;
                        console.log(this.msg);
                    }
                }
            }
        )
    },
    onPlaycustom(){
        this.axios.get('target/getPhrase/?waveid='+this.waveid+'&start='+this.formInline.start+'&end='+this.formInline.end,{
            responseType: "blob"
        }).then(
            response => {
                if(response){
                    let blobwav = response.data;
                    let url= window.URL.createObjectURL(blobwav);  // 获取音频blob url
                    this.phrase=new Audio();  // 音乐片段播放器
                    this.phrase.controls=false;  // 设置显示播放控件
                    this.phrase.autoplay="autoplay";
                    this.phrase.load();  // 未证实加载是否有效 2019-01-31 09:43:25
                    this.phrase.src = url;
                    this.playstatusReady=false;
                    this.phrase.addEventListener(
                        'ended', 
                        () => {
                            this.playstatusReady=true;
                        },
                        false
                    );
                }
            }
        )
    },
    onStopplay(){
        if(this.phrase!=null){
            this.phrase.pause();
            this.playstatusReady=true;
        }
    },
    handleEnable(){
        console.log(this.spectrogramOn);
        this.$emit('spectrogramOn',this.spectrogramOn);

    },
    customEvaluate(){
        this.axios.get('target/getBasefrqCustom/?waveid='+this.waveid+"&framestart="+this.formInline.start+"&frameend="+this.formInline.end).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let refinfo = response.data.body;
                        this.possible_pos = refinfo.possible_pos;
                        this.drawCharts(refinfo.nfft, refinfo.fs, refinfo.basefrq, refinfo.stft, refinfo.medium);
                    }else{
                        this.msg = "获取basefrq失败,原因:"+response.data.tip;
                        console.log(this.msg);
                    }
                }
            }
        )
    },
    
  },
  components:{
  },
  mounted(){
    this.waveid = this.$route.query.waveid;
    this.indexArr=new Array(100000);
    for(var i=0;i<99999;i++){
        this.indexArr[i]=i;
    }

    /*window.addEventListener('resize', () => {
        console.log('窗口发生变化');
        if(this.stftChart){
            this.stftChart.resize();
            this.mediumChart.resize();
        }else{
            console.log("图形不存在");
        }
    })*/
  },
  beforeDestroy() {
  },
  watch: {
    currentframe:{
        handler:function(value){
            this.dataFromBackend();
            this.formInline.start=value;
            this.formInline.end=value+1;
        },
    }
  },
    
}
</script>
<style scoped lang="less">
/deep/ .el-textarea__inner,
.el-textarea {
    height: 100% !important;
    font-size: 0.875rem;
    line-height: normal;
}
/deep/ .el-form-item__label{
    height: 100% !important;
    font-size: 1rem;
    line-height: normal;
}
.el-button{
    padding:0;
}
.el-input{
    height:100%;
}
#customize{
    position:absolute;
    background:#00f0f0;
    left:0rem;
    top:0rem;
    height:calc(6% - 0.1rem);
    width:calc(100% - 0.1rem);
}
#charts{
    position:absolute;
    left:0rem;
    top:6%;
    height:calc(54% - 0.1rem);
    width:calc(100% - 0.1rem);
}
#possible{
    position:absolute;
    left:0rem;
    top:60%;
    height:calc(40% - 0.1rem);
    width:calc(100% - 0.1rem);
}
</style>
