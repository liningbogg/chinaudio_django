<template>
    <div id="graph" class="chart">
        <v-chart theme="ovilia-green" :options="chartOption" style="height:100%;width:100%" autoresize="true"/>
    </div>
</template>

<script>
export default {
    name: 'Vad',
    props: ['currentframe'],
    data(){
        return{
            vadChart:null,
            waveid:null,
            indexArr:null,
            seriesAll: {
                "rmse":0,
                "ee":1,
                "combDescan":2,
                "combDescan_filter":3,
                "comb":4,
                "comb_filter":5,
                "pitch0":6,
                "pitch1":7,
                "pitch2":8,
            },
            chartOption: {
                backgroundColor:"#f0f0f0",
                color:['#ff0000','#0000ff', '#000000', '#ff34b3', '#8b8b00','#aa00ff','#006464', '#00008b', '#8b0000'],
                title : [
                    {
                        show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                        left:'center',
                        text:"Vad",//主标题文本，'\n'指定换行
                    },
                    {
                        show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                        top: "32%",
                        left:'center',
                        text:"Reference",//主标题文本，'\n'指定换行
                    },
                    {
                        show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                        top: "61%",
                        left:'center',
                        text:"Labeling",//主标题文本，'\n'指定换行
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
                    {
                        data: null,
                        type: 'category',
                        axisLine: {onZero: true},
                        gridIndex: 2,
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
                    {
                        gridIndex: 2,
                        scale: 'true',
                    },
                ],
                series: [
                ],
                dataZoom: [
                    {
                        type: 'inside',
                        realtime: true,
                        xAxisIndex: [0, 1, 2]
                    }
                ],
                grid:[
                    {
                        left:'5%',
                        right:'5%',
                        top:'6%',
                        height:'20%',
                    },
                    {
                        left:'5%',
                        right:'5%',
                        top:'36%',
                        height:'20%',
                    },
                    {
                        left:'5%',
                        right:'5%',
                        top:'66%',
                        height:'20%',
                    },
                ],
                toolbox: {
                    feature: {
                        dataZoom: {
                            yAxisIndex: 'none'
                        },
                        restore: {},
                        saveAsImage: {}
                    }
                },
                axisPointer: {
                    link: {xAxisIndex: 'all'}
                },
                tooltip: {
                    trigger: 'axis',
                    formatter:  (params) => {  // params为悬浮框上的全部数据
                        let newParams = [];
                        let tooltipString = [];
                        newParams = [...params];
                        newParams.sort((a,b) => {
                            return this.seriesAll[a.seriesName] - this.seriesAll[b.seriesName]
                        });
                        newParams.forEach((p) => {
                            const cont = p.marker + ' ' + p.seriesName + ': ' + p.value + '<br/>';
                            tooltipString.push(cont);
                        });
                        return tooltipString.join('');
                    },
                    axisPointer: {
                        animation: false
                    }
                },
                legend: {
                    show: true,
                    x:"left",
                    y:"bottom",
                    orient:'horizontal',
                    data:[
                        "rmse",
                        "ee",
                        "combDescan",
                        "combDescan_filter",
                        "comb",
                        "comb_filter",
                        "pitch0",
                        "pitch1",
                        "pitch2",
                    ],
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
                        this.chartOption.xAxis[0].data=this.indexArr.slice(vadinfo.graphstart,vadinfo.graphend);
                        let vaddata={
                            "rmse":vadinfo.rmse,
                            "ee":vadinfo.ee,
                        };
                        for(let key in vaddata){
                            let seriesitem = {
                                data: vaddata[key],
                                name: key,
                                type: 'line',
                                lineStyle:{
                                    normal:{
                                        width:1,
                                    },
                                },
                                symbol: 'none',
                                xAxisIndex: 0,
                                yAxisIndex: 0,
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
                            };
                            /*start*/
                            let startpos=vadinfo.startPos;
                            for(let key in startpos){
                                let position = startpos[key];
                                seriesitem.markLine.data.push({
                                    "xAxis":position,
                                    "lineStyle": {
                                        "show": true,
                                        "color": '#0000ff',
                                        "type": 'solid',
                                        "width":1,
                                    },
                                });
                            }
                            /*current*/
                            seriesitem.markLine.data.push({
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
                            for(let key in stoppos){
                                let position = stoppos[key];
                                seriesitem.markLine.data.push({
                                    "xAxis":position,
                                    "lineStyle": {
                                        "show": true,
                                        "color": '#ff0000',
                                        "type": 'solid',
                                        "width":1,
                                    },
                                });
                            }
                            this.chartOption.series.push(seriesitem);
                        }
                    }else{
                        this.msg = "获取标注配置信息出错,原因:"+response.data.tip;
                        console.log(this.msg);
                    }
                }
            }
        )
    },
    referencepitchFrombackend(){
        this.axios.get('target/getReferencepitch/?waveid='+this.waveid+"&currentframe="+this.currentframe).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let referenceinfo = JSON.parse(response.data.body);
                        let referencepitch = referenceinfo.referencepitch;
                        let start = referenceinfo.start;
                        let stop = referenceinfo.stop;
                        this.chartOption.xAxis[1].data=this.indexArr.slice(start, stop);
                        for(let pitchname in referencepitch){
                            let data=referencepitch[pitchname];
                            let seriesItem={
                                data: data,
                                name: pitchname,
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
                            this.chartOption.series.push(seriesItem);
                        }
                    }else{
                        this.msg = "获取basefrq失败,原因:"+response.data.tip;
                        console.log(this.msg);
                    }
                }
            }
        )
    },
    labelingpitchFrombackend(){
        this.axios.get('target/getLabelingpitch/?waveid='+this.waveid+"&currentframe="+this.currentframe).then(
            response => {
                if(response){
                    if(response.data.status==="success"){
                        let labelinginfo = JSON.parse(response.data.body);
                        let labelingpitch = labelinginfo.labelingpitch;
                        let start = labelinginfo.start;
                        let stop = labelinginfo.stop;
                        this.chartOption.xAxis[2].data=this.indexArr.slice(start, stop);
                        for(let pitchname in labelingpitch){
                            let data=labelingpitch[pitchname];
                            let seriesItem={
                                data: data,
                                name: pitchname,
                                type: 'line',
                                xAxisIndex: 2,
                                yAxisIndex: 2,
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
                            this.chartOption.series.push(seriesItem);
                        }
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
  },
  beforeDestroy() {
  },
  watch: {
    currentframe:{
        handler:function(value){
            this.vadFromBackend();
            this.referencepitchFrombackend();
            this.labelingpitchFrombackend();
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
