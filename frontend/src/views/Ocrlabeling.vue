<template>
    <div class="main">
        <div id="title">
            OCR标注:{{title}}
        </div>
        <div id="content">
            <!--图像信息-->
            <div id="imageinfo">
            </div>
            <!--图像标注-->
            <div id="pageimage" :style="{width:boxwidth}">
                <ocrailabel :currentframe="current_frame" @adjustDiv="adjustDiv"/>
            </div>
            <div id="tools" :style={left:toolleft,width:toolwidth}>
                <div id="ocrmodediv">
                    <ocrmode />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Ocrailabel from '@/components/Ocrailabel.vue'
import Ocrmode from '@/components/Ocrmode.vue'

export default {
    name: 'Ocrlabeling',
    components:{
        Ocrailabel,
        Ocrmode,
    },
    data() {
        return {
            title:null,
            docid:null,
            gMap:null,
            current_frame:null,
            is_vertical_pdf:null,
            msg:null,
            boxwidth:"calc(70% - 0.2rem)",
            toolleft:"calc(70% + 0.1rem)",
            toolwidth:"calc(30% - 0.2rem)",
        }
    },
    methods:{
        nextframeFromBackend(){
            this.axios.get('ocr/nextframe/?docid='+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.current_frame = response.data.body.current_frame;
                            this.is_vertical_pdf = response.data.body.is_vertical_pdf;
                        }else{
                            this.msg = "获取待标记帧号出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )
        },
        //响应子组件div调整"tools"请求
        adjustDiv(tar_width){
            console.log(tar_width);
            //let div_page = document.getElementById("pageimage");
            let div_total = document.getElementById("content");
            this.boxwidth = tar_width*100.0/div_total.offsetWidth+"%";
            this.toolleft = "calc("+tar_width*100.0/div_total.offsetWidth+"% + 0.3rem)";
            this.toolwidth = "calc("+(100-tar_width*100.0/div_total.offsetWidth)+"% - 0.4rem)";
        },
    },
    mounted(){
        this.title = this.$route.query.title;
        this.docid = this.$route.query.docid;
        console.log(this.title,this.docid);
        this.nextframeFromBackend();
    },
}
</script>
<style scoped lang="less">
.main{
    position:absolute;
    width: calc(100% - 0.1rem);
    height: calc(100% - 0.1rem);
}
#title{
    position:absolute;
    top:0rem;
    width:calc(80% -0.1rem);
    height:2rem;
}
#content{
    position:absolute;
    top:2.1rem;
    width:calc(100% -0.1rem);
    height:calc(100% - 2.2rem);
}
#imageinfo{
    position:absolute;
    left:0.1rem;
    width:calc(100% - 0.2rem);
    height:2rem;
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
#pageimage{
    position:absolute;
    left:0.1rem;
    top:2.1rem;
    height:calc(100% - 2.2rem);
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
#tools{
    position:absolute;
    top:2.1rem;
    left:70%;
    height:calc(100% - 2.2rem);
    width:calc(30% - 2.2rem);
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
#ocrmodediv{
    position:absolute;
    left:0.1rem;
    top:0.1rem;
    width:calc(50% - 0.2rem);
    height:calc(12% - 0.2rem);
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
}
</style>
