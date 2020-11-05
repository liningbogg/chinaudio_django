<template>
    <div>
        <div id="customize">
            <el-form :inline="true" :model="formInline" class="demo-form-inline" style="height:100%">
                <el-form-item label="起始" style="position:absolute;left:0;width:25%">
                    <el-input v-model="formInline.start" placeholder="起始位置"></el-input>
                </el-form-item>
                <el-form-item label="终止" style="position:absolute;left:25%;width:25%;height:100%">
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
        <div id="stftecharts" class="chart">
        </div>
        <div id="mediumecharts" class="chart">
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
var echarts = require("echarts/lib/echarts");
require("echarts/lib/chart/line");
require("echarts/lib/component/title");
require("echarts/lib/component/legend");
require("echarts/lib/component/tooltip");
require("echarts/lib/component/toolbox");
require("echarts/lib/component/dataZoom");
require("echarts/lib/component/markLine");
import elementResizeDetectorMaker from 'element-resize-detector'
export default {
  name: 'Stft',
  props: ['currentframe'],
  data(){
    return{
        stftChart:null,
        mediumChart:null,
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

        mediumchartOption: {
            backgroundColor:"#f0f0f0",
            title : {
                show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                x:'center',
                y:'top',
                textAlign:'left',
                text:"medium",//主标题文本，'\n'指定换行
            },
            dataZoom:[
                {
                    type: 'inside',
                },
            ],
            xAxis: {
                data: null,
            },
            yAxis: {
                scale: 'true',
                axisLabel:{
                    rotate:-30,
                },
            },
            series: [
                {
                    data: null,
                    name: "medium",
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
            ],
            grid:{
                left:'5%',
                right:'5%',
                top:'15%',
                bottom:'15%',
                containLabel: true
            },
            toolbox: {
                show:true,
                feature:{
                    dataZoom: {
                        yAxisIndex:"none"
                    },
                }
            },
            tooltip: {
                trigger: 'axis',
            },
            color:[
                '#0000ff',
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
        chartOption: {
            backgroundColor:"#f0f0f0",
            title : {
                show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                x:'center',
                y:'top',
                textAlign:'left',
                text:"stft",//主标题文本，'\n'指定换行
            },
            dataZoom:[
                {
                    type: 'inside',
                },
            ],
            xAxis: {
                data: null,
            },
            yAxis: {
                scale: 'true',
                axisLabel:{
                    rotate:-30,
                },
            },
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
            ],
            grid:{
                left:'5%',
                right:'5%',
                top:'15%',
                bottom:'15%',
                containLabel: true
            },
            toolbox: {
                show:true,
                feature:{
                    dataZoom: {
                        yAxisIndex:"none"
                    },
                }
            },
            tooltip: {
                trigger: 'axis',
            },
            color:[
                '#0000ff',
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
        this.chartOption.xAxis.data=xAxis;
        this.chartOption.series[0].data=stft;

        xAxis = new Array(medium.length);
        for(let key=0; key<xAxis.length; key++){
            xAxis[key]=key;
        }
        this.mediumchartOption.xAxis.data=xAxis;
        this.mediumchartOption.series[0].data=medium;
        this.stftChart.clear();
        this.mediumChart.clear();
        this.stftChart.setOption(this.chartOption);
        this.mediumChart.setOption(this.mediumchartOption);
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
    this.stftChart = echarts.init(document.getElementById("stftecharts"), 'macarons');
    this.mediumChart = echarts.init(document.getElementById("mediumecharts"), 'macarons');

    /*window.addEventListener('resize', () => {
        console.log('窗口发生变化');
        if(this.stftChart){
            this.stftChart.resize();
            this.mediumChart.resize();
        }else{
            console.log("图形不存在");
        }
    })*/
    let erd = elementResizeDetectorMaker();
    erd.listenTo(document.getElementById("stftecharts"), ()=> {
        //执行操作
        this.stftChart.resize();
    });
    erd.listenTo(document.getElementById("mediumecharts"), ()=> {
        //执行操作
        this.mediumChart.resize();
    });

  },
  beforeDestroy() {
    this.stftChart.clear();
    this.mediumecharts.clear();
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
    left:0rem;
    top:0rem;
    height:calc(10% - 0.1rem);
    width:calc(100% - 0.1rem);
}
#stftecharts{
    position:absolute;
    left:0rem;
    top:10%;
    height:calc(50% - 0.1rem);
    width:calc(50% - 0.1rem);
}
#mediumecharts{
    position:absolute;
    left:50%;
    top:10%;
    height:calc(50% - 0.1rem);
    width:calc(50% - 0.1rem);
}
#possible{
    position:absolute;
    left:0rem;
    top:60%;
    height:calc(40% - 0.1rem);
    width:calc(100% - 0.1rem);
}
</style>
