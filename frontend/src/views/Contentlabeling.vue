<template>
    <div class="main">
        <div id="title">
            内容标注:{{title}}
        </div>
        <div id="contentlabeling">
            <router-link :to="{path:'/Ocrlabeling',query: {docid: this.docid, currentframe:this.current_frame, title:this.title}}">返回</router-link>
        </div>
        <div id="content">
            <!--图像信息-->
            <div id="imageinfo">
            </div>
            <!--图像标注-->
            <div id="pageimage">
                <polygonadjust :polygonid="polygonid" />
            </div>
            <!-- 偏旁部首列表 -->
            <div id="elemdisp">
                <!--分页的elem-->
                <div id="elempage">
                    <elemlist :currentframe="currentframe" :polygonid="polygonid"/>
                </div>
            </div>
            <!-- 工具页 -->
            <div id="tools">
                <div id="contentmodediv">
                    <contentlabelingmode />
                </div>
                <div id="processtip">
                    <messagebox />
                </div>
                <div id="elemselected">
                    <elemselected :currentframe="currentframe" :polygonid="polygonid"/>
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
import Ocrmode from '@/components/Ocrmode.vue'
import Messagebox from '@/components/Messagebox.vue'
import Recommenttip from '@/components/Recommenttip.vue'
import Imageinfo from '@/components/Imageinfo.vue'
import Elemlist from '@/components/Elemlist.vue'
import Polygonadjust from '@/components/Polygonadjust.vue'
import Contentlabelingmode from '@/components/Contentlabelingmode.vue'
import Elemselected from '@/components/Elemselected.vue'

export default {
    name: 'Contentlabeling',
    components:{
        Ocrmode,
        Messagebox,
        Recommenttip,
        Imageinfo,
        Elemlist,
        Polygonadjust,
        Contentlabelingmode,
        Elemselected,
    },
    data() {
        return {
            title:null,
            gMap:null,
            framenum:null,
            is_vertical_pdf:null,
            msg:null,
            boxwidth:"calc(70% - 0.2rem)",
            toolleft:"calc(70% + 0.1rem)",
            toolwidth:"calc(30% - 0.2rem)",
            tarwidth:0,
            tarheight:0,
            polygonid:null,
            currentframe:null,
            docid:null,
        }
    },
    computed:{
    },
    methods:{
        nextPolygonFromBackend(){
            this.axios.get('ocr/nextpolygoninfo/?docid='+this.docid+"&current_frame="+this.currentframe).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let polygoninfo = response.data.body;
                            this.polygonid = polygoninfo.polygonid;
                            console.log(this.polygonid);
                        }else{
                            this.msg = "获取标记polygonid出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )
        },
    },
    mounted(){
        this.currentframe = this.$route.query.currentframe;
        this.docid = this.$route.query.docid;
        this.title = this.$route.query.title;
        console.log(this.currentframe, this.docid, this.title);
        this.nextPolygonFromBackend();
        let div_page = document.getElementById("pageimage");
        this.tarwidth = div_page.offsetWidth;
        this.tarheight = div_page.offsetHeight;
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
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
#pageimage{
    position:absolute;
    left:0.1rem;
    top:2.1rem;
    width:30rem;
    height:30rem;
    border-color:red;
    border-width:0.01rem;
    border-style:solid;
}
#elemdisp{
    position:absolute;
    left:30.2rem;
    top:2.1rem;
    width:45rem;
    height:calc(100% - 2.2rem);
}
#elempage{
    position:absolute;
    left:0;
    top:0;
    width:100%;
    height:calc(36rem + 32px);
}

#tools{
    position:absolute;
    top:2.1rem;
    left:75.3rem;
    height:calc(100% - 2.2rem);
    width:calc(100% - 75.4rem);
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
#contentmodediv{
    position:absolute;
    left:0.1rem;
    top:0.1rem;
    width:calc(100% - 0.2rem);
    height:2rem;
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
}
#processtip{
    position:absolute;
    left:0.1rem;
    top:2.2rem;
    width:calc(100% - 0.2rem);
    height:calc(12% - 0.2rem);
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
#elemselected{
    position:absolute;
    left:0.1rem;
    top:calc(12%+ 2.2rem);
    width:calc(100% - 0.2rem);
    height: 4.6rem;
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
