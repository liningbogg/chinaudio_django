<template>
    <div id="spectrum_tf">
    </div>
</template>

<script>
var echarts = require("echarts/lib/echarts");
require("echarts/lib/chart/heatmap");
require("echarts/lib/component/title");
require("echarts/lib/component/legend");
require("echarts/lib/component/tooltip");
require("echarts/lib/component/toolbox");
require("echarts/lib/component/dataZoom");
require("echarts/lib/component/markLine");
import elementResizeDetectorMaker from 'element-resize-detector'
export default {
  name: 'Spectrumchart',
  props: ['currentframe'],
  data(){
    return{
        spectrumChart:null,
        indexArr:null,

        spectrumchartOption: {
            backgroundColor:"#f0f0f0",
            animation: false,
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
                type: 'category',
                data: null,
            },
            yAxis: {
                type: 'category',
                data: null,
            },
            visualMap: {
                min: null,
                max: null,
                calculable: true,
                realtime: false,
                inRange: {
                    color: ['#000000', '#ffffff']
                }
            },

            grid:{
                x: "10%",
                y: "1%",
                x2: "1%",
                y2: "4%",
                containLabel: true
            },
            series: [{
                name: "时频图",
                type: 'heatmap',
                data: null,
                itemStyle: {
                    emphasis: {
                        borderColor: '#333',
                        borderWidth: 0
                    }
                },
                progressive: 1000,
                animation: false
            }],

            toolbox: {
                feature:
                {
                    dataZoom:
                    {
                        show: true,

                    }
                }
            },
            tooltip: {
                trigger:'item',
                position: function (pos, params, el, elRect, size) {
                    var obj = {top: 10};
                    obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                    return obj;
                },
                extraCssText: "width: 30%;height: 10%",
                formatter:'{a}<br>{c}'
            },
        },
    }
  },
  methods:{
    drawCharts(xData, yData, min_data, max_data, data){
        this.spectrumchartOption.xAxis.data = xData;
        this.spectrumchartOption.yAxis.data = yData;
        this.spectrumchartOption.visualMap.min = min_data;
        this.spectrumchartOption.visualMap.max = max_data;
        this.spectrumchartOption.series.data = data;
        this.spectrumChart.setOption(this.spectrumchartOption);
        this.spectrumChart.resize();
    },
    dataFromBackend(){
        this.axios.get('target/getSpectrum/?waveid='+this.waveid+"&currentframe="+this.currentframe).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let context = JSON.parse(response.data.body);
                        console.log(context);
                        let length=context["length"];
                        let spectrogram=context["spectrogram"];
                        let max_fft_range=context["max_fft_range"];
                        let min_fft_range=context["min_fft_range"];
                        let framenumber=spectrogram.length();
                        console.log("hello", framenumber);
                        let data=[];
                        let xData=[];
                        let yData=[];
                        for(let i=0;i<framenumber;i++){
                            for(let j=0;j<length;j++){
                                data.push([i,j,spectrogram[i][j]]);
                            }
                            xData.push(i);
                        }
                        for(let j=0;j<length;j++)
                        {
                            yData.push(j);
                        }
                        this.drawCharts(xData, yData, min_fft_range, max_fft_range, spectrogram);
                    }else{
                        this.msg = "获取时频图失败,原因:"+response.data.tip;
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
    this.spectrumChart = echarts.init(document.getElementById("spectrum_tf"), 'macarons');

    let erd = elementResizeDetectorMaker();
    erd.listenTo(document.getElementById("spectrum_tf"), ()=> {
        //执行操作
        this.spectrumChart.resize();
    });
    console.log("check");
  },
  beforeDestroy() {
  },
  watch: {
    currentframe:{
        handler:function(value){
            console.log("ahha");
            console.log(value);
            this.dataFromBackend();
        },
    }
  },
    
}
</script>
<style scoped lang="less">
#spectrum{
    position:absolute;
    left:0rem;
    top:0;
    height:calc(100% - 0.1rem);
    width:calc(100% - 0.1rem);
}
</style>
