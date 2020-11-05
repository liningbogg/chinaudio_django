<template>
    <div id="graph" class="chart">
    </div>
</template>

<script>
var echarts = require("echarts/lib/echarts");
require("echarts/lib/chart/line");
require("echarts/lib/component/title");
require("echarts/lib/component/legend");
require("echarts/lib/component/tooltip");
require("echarts/lib/component/markLine");
require("echarts/lib/component/toolbox");
require("echarts/lib/component/dataZoom");
import elementResizeDetectorMaker from 'element-resize-detector'

export default {
  name: 'Vad',
  props: ['currentframe'],
  data(){
    return{
        vadChart:null,
        waveid:null,
        indexArr:null,
        chartOption: {
            backgroundColor:"#f0f0f0",
            color:['#ff0000','#0000ff'],
            title : {
                show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                x:'center',
                y:'top',
                textAlign:'left',
                text:"vad",//主标题文本，'\n'指定换行
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
                    name: "rmse",
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
                },
                {
                    data: null,
                    name: "ee",
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
                            type: 'dashed'
                        },
                        label:{
                            show: false,
                            formatter: (params) => {
                                let str = this.currentframe+params.data.value;                                            
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
    vadFromBackend(){
        this.axios.get('target/getVad/?waveid='+this.waveid+"&current_frame="+this.currentframe).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let vadinfo = JSON.parse(response.data.body);
                        console.log(vadinfo);
                        this.chartOption.xAxis.data=this.indexArr.slice(vadinfo.graphstart,vadinfo.graphend);
                        this.chartOption.series[0].data=vadinfo.rmse;
                        this.chartOption.series[1].data=vadinfo.ee;
                        /*start*/
                        let startpos=vadinfo.startPos;
                        for(var key in startpos){
                            let position = startpos[key];
                            this.chartOption.series[0].markLine.data.push({"xAxis":position});
                        }
                        /*current*/
                        this.chartOption.series[0].markLine.data.push({
                            "xAxis":this.currentframe-vadinfo.graphstart,
                            "lineStyle": {
                                "show": true,
                                "color": '#00ff00',
                                "type": 'solid',
                                "width":2,
                            },
                            "label":{
                                "show": false,
                                "formatter": (params) => {
                                    let str = this.currentframe+params.data.value;                                            
                                    return str;
                                },
                            },
                            
                        });
                        /*stop*/
                        let stoppos=vadinfo.stopPos;
                        for(key in stoppos){
                            let position = stoppos[key];
                            this.chartOption.series[1].markLine.data.push({"xAxis":position});
                        }


                        console.log(this.chartOption);
                        this.vadChart.setOption(this.chartOption);
                        this.vadChart.resize();


                    }else{
                        this.msg = "获取标注配置信息出错,原因:"+response.data.tip;
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
    this.vadChart = echarts.init(document.getElementById("graph"), 'macarons');

    /*window.addEventListener('resize', () => {
        console.log('窗口发生变化');
        if(this.vadChart){
            this.vadChart.resize();
        }else{
            console.log("图形不存在");
        }
    });*/
    let erd = elementResizeDetectorMaker();
    erd.listenTo(document.getElementById("graph"), ()=> {
        //执行操作
        this.vadChart.resize();
    });
  },
  beforeDestroy() {
    this.vadChart.clear();
  },
  watch: {
    currentframe:{
        handler:function(value){
            this.vadFromBackend();
            console.log(value);
        },
    }
  },
    
}
</script>
<style scoped >
#graph{
    position:absolute;
    left:0rem;
    top:0rem;
    height:100%;
    width:100%;
}

</style>
