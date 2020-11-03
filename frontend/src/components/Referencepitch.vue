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
    drawCharts(referencepitch, start, end){
        console.log(start, end);
        this.pitchchartOption.xAxis.data=this.indexArr.slice(start, end);
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
                        let end = referenceinfo.end;
                        this.drawCharts(referencepitch, start, end);
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

    window.addEventListener('resize', () => {
        console.log('窗口发生变化');
        if(this.pitchChart){
            this.pitchChart.resize();
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
            console.log(value);
            this.dataFromBackend();
        },
    }
  },
    
}
</script>
<style scoped lang="less">
#stftecharts{
    position:absolute;
    left:0rem;
    top:0;
    height:calc(50% - 0.1rem);
    width:calc(100% - 0.1rem);
}
</style>
