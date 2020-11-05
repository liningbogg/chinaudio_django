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
export default {
    name: 'Vad',
    props: ['currentframe'],
    data(){
        return{
            vadChart:null,
            waveid:null,
            indexArr:null,
            vadchartOption: {
                backgroundColor:"#f0f0f0",
                color:['#ff0000','#0000ff'],
                title : {
                    show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                    x:'center',
                    y:'top',
                    textAlign:'left',
                    text:"邻域信息",//主标题文本，'\n'指定换行
                },
                dataZoom:[
                    {
                        show: true,
                        realtime: true,
                        start: 0,
                        end: 100,
                        xAxisIndex: [0, 1, 2]
                    },
                    {
                        type: 'inside',
                        realtime: true,
                        start: 0,
                        end: 100,
                        xAxisIndex: [0, 1, 2]
                    }
                ],
                xAxis: [
                    {
                        data: null,
                    },
                    {
                        data: null,
                        gridIndex: 1,
                    },
                    {
                        data: null,
                        gridIndex: 2,
                    },
                ]
                yAxis: [
                    {
                        scale: 'true',
                        name: '端点',
                        axisLabel:{
                            rotate:-30,
                        },
                    },
                    {
                        gridIndex: 1,
                        name: '参考',
                        scale: 'true',
                        axisLabel:{
                            rotate:-30,
                        },
                    },
                    {
                        gridIndex: 2,
                        name: '标记',
                        scale: 'true',
                        axisLabel:{
                            rotate:-30,
                        },
                    },
                ]
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
                ],
                grid:[
                    {
                        left:'5%',
                        right:'5%',
                        top:'5%',
                        height:'27%',
                        containLabel: true
                    },
                    {
                        left:'5%',
                        right:'5%',
                        top:'38%',
                        height:'27%',
                        containLabel: true
                    },
                    {
                        left:'5%',
                        right:'5%',
                        top:'71%',
                        height:'27%',
                        containLabel: true
                    },
                ]
                toolbox: {
                    feature: {
                        dataZoom: {
                            yAxisIndex: 'none'
                        },
                        restore: {},
                        saveAsImage: {}
                    }
                },
                tooltip: {
                    igger: 'axis',
                    axisPointer: {
                        animation: false
                    }
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
    window.addEventListener('resize', () => {
        console.log('窗口发生变化');
        if(this.vadChart){
            this.vadChart.resize();
        }else{
            console.log("图形不存在");
        }
    })
  },
  beforeDestroy() {
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
<style scoped lang="less">
#graph{
    position:absolute;
    left:0rem;
    top:0rem;
    height:100%;
    width:100%;
}
</style>
