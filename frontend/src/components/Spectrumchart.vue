<template>
    <div id="spectrum_tf">
        <v-chart theme="ovilia-green" :options="spectrumchartOption" style="height:100%;width:100%" autoresize="true"/>
    </div>
</template>

<script>
export default {
  name: 'Spectrumchart',
  props: ['currentframe'],
  data(){
    return{
        indexArr:null,
        waveid:null,
        start:0,
        spectrumchartOption: {
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

            series: [{
                name: "time_frq",
                type: 'heatmap',
                data: null,
                emphasis: {
                    itemStyle: {
                        borderColor: '#333',
                        borderWidth: 0,
                    }
                },
                progressive: 10000,
                animation: false
            }],

            tooltip: {
                trigger:'item',
                position: function (pos, params, el, elRect, size) {
                    var obj = {top: 10};
                    obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                    return obj;
                },
                extraCssText: "width: 30%;height: 10%",
                formatter:  (params) => {
                    let tooltipString = [];
                    const cont = params.value[0]+this.start + ' ' + params.value[1] + ': ' + params.value[2] + '<br/>';
                    return cont;
                },
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
        this.spectrumchartOption.series[0].data = data;
    },
    dataFromBackend(){
        this.axios.get('target/getSpectrum/?waveid='+this.waveid+"&currentframe="+this.currentframe).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let context = JSON.parse(response.data.body);
                        this.start=context["start"];
                        let length=context["length"];
                        let spectrogram=context["spectrogram"];
                        let max_fft_range=context["max_fft_range"];
                        let min_fft_range=context["min_fft_range"];
                        let framenumber=spectrogram.length;
                        let data=[];
                        let xData=[];
                        let yData=[];
                        for(let i=0;i<framenumber;i++){
                            for(let j=0;j<length;j++){
                                data.push([i,j,spectrogram[i][j]]);
                            }
                            xData.push(i+context["start"]);
                        }
                        for(let j=0;j<length;j++)
                        {
                            yData.push(j);
                        }
                        this.drawCharts(xData, yData, min_fft_range, max_fft_range, data);
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
    this.indexArr=new Array(10000);
    for(var i=0;i<9999;i++){
        this.indexArr[i]=i;
    }

    console.log("check");
  },
  beforeDestroy() {
  },
  watch: {
    currentframe:{
        handler:function(value){
            this.waveid = this.$route.query.waveid;
            console.log(value);
            this.dataFromBackend();
        },
        immediate: true,
    }
  },
    
}
</script>
<style scoped lang="less">
#spectrum_tf{
    position:absolute;
    left:0rem;
    top:0;
    height:calc(100% - 0.1rem);
    width:calc(100% - 0.1rem);
}
</style>
