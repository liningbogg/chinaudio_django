<template>
    <div id="pitchecharts">
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
  name: 'Referencepitch',
  props: ['currentframe'],
  data(){
    return{
        pitchChart:null,
        indexArr:null,

        pitchchartOption: {
            backgroundColor:"#f0f0f0",
            title : {
                show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                x:'center',
                y:'top',
                textAlign:'left',
                text:"reference",//主标题文本，'\n'指定换行
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
    drawCharts(referencepitch, start, stop){
        this.pitchchartOption.xAxis.data=this.indexArr.slice(start, stop);
        for(let pitchname in referencepitch){
            let data=referencepitch[pitchname];
            let seriesItem={
                data: data,
                name: pitchname,
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
                        {"xAxis":this.currentframe-start},
                    ],
                    lineStyle: {
                        show: true,
                        type: 'solid'
                    },
                    label:{
                        show: false,
                        formatter: (params) => {
                            let str = this.currentframe+params.data.value;
                            return str;
                        },
                    },
                },
            }
            this.pitchchartOption.series.push(seriesItem);
        }
        console.log(this.pitchchartOption);
        this.pitchChart.setOption(this.pitchchartOption);
        this.pitchChart.resize();

    },
    dataFromBackend(){
        this.axios.get('target/getReferencepitch/?waveid='+this.waveid+"&currentframe="+this.currentframe).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let referenceinfo = JSON.parse(response.data.body);
                        let referencepitch = referenceinfo.referencepitch;
                        let start = referenceinfo.start;
                        let stop = referenceinfo.stop;
                        this.drawCharts(referencepitch, start, stop);
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
    this.pitchChart = echarts.init(document.getElementById("pitchecharts"), 'macarons');

    /*window.addEventListener('resize', () => {
        console.log('窗口发生变化');
        if(this.pitchChart){
            this.pitchChart.resize();
        }else{
            console.log("图形不存在");
        }
    })*/
    let erd = elementResizeDetectorMaker();
    erd.listenTo(document.getElementById("pitchecharts"), ()=> {
        //执行操作
        this.pitchChart.resize();
    });

  },
  beforeDestroy() {
    this.pitchChart.clear();
  },
  watch: {
    currentframe:{
        handler:function(value){
            console.log(value);
            this.dataFromBackend();
        },
    }
  },
    
}
</script>
<style scoped lang="less">
#pitchecharts{
    position:absolute;
    left:0rem;
    top:0;
    height:calc(100% - 0.1rem);
    width:calc(100% - 0.1rem);
}
</style>
