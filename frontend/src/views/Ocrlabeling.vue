<template>
    <div class="main">
        <div id="title">
            OCR标注:{{title}}
        </div>
        <div id="contentlabeling">
            <router-link :to="{path:'/Contentlabeling',query: {docid: this.docid,currentframe:this.current_frame, title:this.title, framenum:this.framenum}}" >内容标注</router-link>
        </div>
        <div id="content">
            <!--图像信息-->
            <div id="imageinfo">
                <imageinfo :tarwidth="tarwidth" :tarheight="tarheight" :currentframe="current_frame"/>
            </div>
            <!--图像标注-->
            <div id="pageimage" :style="{width:boxwidth}">
                <ocrailabel :currentframe="current_frame" @adjustDiv="adjustDiv"/>
            </div>
            <div id="page_navi" :style="{width:boxwidth}">
                <el-pagination
                    background
                    @current-change="handleCurrentChange"
                    :current-page="current_frame+1"
                    :page-sizes="1"
                    :page-size="1"
                    layout="total, prev, pager, next, jumper"
                    :total="framenum">
                    style="height:100%"
                </el-pagination>
            </div>
            <div id="tools" :style="{left:toolleft,width:toolwidth}">
                <div id="ocrmodediv">
                    <ocrmode />
                </div>
                <div id="processtip">
                    <messagebox />
                </div>
                <div id="recomment">
                    <recommenttip :currentframe="current_frame"/>                    
                </div>
                <div id="rotation">
                </div>
                <div id="statistic">
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Ocrailabel from '@/components/Ocrailabel.vue'
import Ocrmode from '@/components/Ocrmode.vue'
import Messagebox from '@/components/Messagebox.vue'
import Recommenttip from '@/components/Recommenttip.vue'
import Imageinfo from '@/components/Imageinfo.vue'

export default {
    name: 'Ocrlabeling',
    components:{
        Ocrailabel,
        Ocrmode,
        Messagebox,
        Recommenttip,
        Imageinfo,
    },
    data() {
        return {
            title:null,
            docid:null,
            gMap:null,
            current_frame:null,
            framenum:null,
            msg:null,
            boxwidth:"calc(70% - 0.2rem)",
            toolleft:"calc(70% + 0.1rem)",
            toolwidth:"calc(30% - 0.2rem)",
            tarwidth:0,
            tarheight:0,
        }
    },
    computed:{
    },
    methods:{
        handleCurrentChange(val){
           this.current_frame = val-1; 
        },
        nextframeFromBackend(){
            this.axios.get('ocr/nextframe/?docid='+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.current_frame = response.data.body.current_frame;
                            this.framenum = response.data.body.framenum;
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
            let div_page = document.getElementById("pageimage");
            this.tarwidth = div_page.offsetWidth;
            this.tarheight = div_page.offsetHeight;

        },
    },
    mounted(){
        this.title = this.$route.query.title;
        this.docid = this.$route.query.docid;
        console.log(this.title,this.docid);
        this.nextframeFromBackend();
        let div_page = document.getElementById("pageimage");
        this.tarwidth = div_page.offsetWidth;
        this.tarheight = div_page.offsetHeight;
    },
    watch: {
        current_frame:{
            handler:function(value){
                this.axios.get('ocr/setCurrent/?ocr_pdf='+this.docid+"&page_apointed="+value).then(
                    response => {
                        if(response){
                            if(response.data.status==="success"){
                                let message={
                                    "type":"notice",
                                    "text":"修改当前页为:"+value,
                                }
                                this.$store.commit("addMessagetip",message);
                            }else{
                                this.msg = "设置待标记帧号出错,原因:"+response.data.tip;
                                console.log(this.msg);
                            }
                        }
                    }
                );
            },
        },

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
    line-height:2rem;
    font-size:1.8rem;
    color:blue;
    font-weight:bold;
}
#contentlabeling{
    position:absolute;
    top:0rem;
    left:80%;
    width:calc(20% -0.1rem);
    height:2rem;
    line-height:2rem;
    font-size:1.5rem;
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
}
#pageimage{
    position:absolute;
    left:0.1rem;
    top:2.1rem;
    height:calc(100% - 2.1rem - 32px);
    border-color:red;
    border-width:0.01rem;
    border-style:solid;
}
#page_navi{
    position:absolute;
    left:0.1rem;
    top:calc(100% - 30px);
    height:28px;
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
    height:calc(24% - 0.2rem);
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
}
#processtip{
    position:absolute;
    left:calc(50% + 0.1rem);
    top:0.1rem;
    width:calc(50% - 0.2rem);
    height:calc(24% - 0.2rem);
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
}
#recomment{
    position:absolute;
    left:0.1rem;
    top:calc(24%+ 0.1rem);
    width:calc(100% - 0.2rem);
    height:calc(28% - 0.2rem);
}
#rotation{
    position:absolute;
    left:0.1rem;
    top:calc(52%+ 0.1rem);
    width:calc(100% - 0.2rem);
    height:calc(24% - 0.2rem);
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
#statistic{
    position:absolute;
    left:0.1rem;
    top:calc(76%+ 0.1rem);
    width:calc(100% - 0.2rem);
    height:calc(24% - 0.2rem);
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
</style>
