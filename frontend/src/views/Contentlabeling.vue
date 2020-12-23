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
                <div style="left:0;width:12.5%;height:100%;line-height:100%;position:absolute;top:0;display:grid;align-items:center;">
                    currentframe:{{currentframe}}
                </div>
                <div style="left:12.5%;width:12.5%;height:100%;line-height:100%;position:absolute;top:0;display:grid;align-items:center;">
                    framenum:{{framenum}}
                </div>
                <div style="left:25%;width:12.5%;height:100%;line-height:100%;position:absolute;top:0;display:grid;align-items:center;">
                    polygonid:{{polygonid}}
                </div>
                <div style="left:37.5%;width:12.5%;height:100%;line-height:100%;position:absolute;top:0;display:grid;align-items:center;">
                    tarwidth:{{tarwidth}}
                </div>
                <div style="left:50%;width:12.5%;height:100%;line-height:100%;position:absolute;top:0;display:grid;align-items:center;">
                    tarheight:{{tarheight}}
                </div>
            </div>
            <!--图像标注-->
            <div id="pageimage">
                <polygonadjust :polygonid="polygonid" ref="adjust" @nextPolygonFromBackend="nextPolygonFromBackend"/>
            </div>
            <!-- 标注翻页 -->
            <div id="polygonpagetool">
                <polygonpagetool :polygonid="polygonid" @nextPolygonFromBackend="nextPolygonFromBackend" @updateDone="updateDone" @setDone="setDone"/>
            </div>
            <!-- 偏旁部首列表 -->
            <div id="elemdisp">
                <!--分页的elem-->
                <div id="elempage">
                    <elemlist :currentframe="currentframe" :polygonid="polygonid" :docid="docid"/>
                </div>
                <div id="elemcreate">
                    <elemcreate />
                </div>
                <div id="elemconfigure">
                    <elemconfigure />
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
                <div id="elemassist">
                    <elemassist :currentframe="currentframe" :polygonid="polygonid"/>
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
import Elemassist from '@/components/Elemassist.vue'
import Polygonpagetool from '@/components/Polygonpagetool.vue'
import Elemconfigure from '@/components/Elemconfigure.vue'
import Elemcreate from '@/components/Elemcreate.vue'

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
        Elemassist,
        Polygonpagetool,
        Elemconfigure,
        Elemcreate,
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
        updateDone(isDone){
            this.$refs.adjust.updateDone(isDone);
        },
        setDone(){
            this.$refs.adjust.setDone();
        },
        nextPolygonFromBackend(){
            this.axios.get('ocr/nextpolygoninfo/?docid='+this.docid+"&current_frame="+this.currentframe).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let polygoninfo = response.data.body;
                            this.polygonid = polygoninfo.polygonid;
                            let message={
                                "type":"notice",
                                "text":"当前polygonid:"+this.polygonid,
                            }
                            this.$store.commit("addMessagetip",message);
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
        this.framenum = this.$route.query.framenum;
        this.is_vertical_pdf = this.$route.query.is_vertical_pdf;
        this.docid = this.$route.query.docid;
        this.title = this.$route.query.title;
        this.nextPolygonFromBackend();
        let div_page = document.getElementById("pageimage");
        if(div_page){
            this.tarwidth = div_page.offsetWidth;
            this.tarheight = div_page.offsetHeight;
        }
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
    width:30rem;
    height:30rem;
    border-color:red;
    border-width:0.01rem;
    border-style:solid;
}
#polygonpagetool{
    position:absolute;
    left:0.1rem;
    top:34.2rem;
    width:30rem;
    height:3rem;
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
#elemcreate{
    position:absolute;
    left:0;
    top:calc(36rem + 36px);
    height:calc(50% - 18rem -20px);
    width:100%;
    border-color:red;
    border-width:0.01rem;
    border-style:solid;
}
#elemconfigure{
    position:absolute;
    left:0;
    top:calc(50% + 18rem + 18px);
    height:calc(50% - 18rem -20px);
    width:100%;
    border-color:green;
    border-width:0.01rem;
    border-style:solid;
}

#tools{
    position:absolute;
    top:2.1rem;
    left:75.3rem;
    height:calc(100% - 2.2rem);
    width:calc(100% - 75.4rem);
}
#contentmodediv{
    position:absolute;
    left:0.1rem;
    top:0.1rem;
    width:calc(100% - 0.2rem);
    height:2rem;
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
#elemassist{
    position:absolute;
    left:0.1rem;
    top:calc(12%+ 7rem);
    width:calc(100% - 0.2rem);
    height:7.3rem;
}
#statistic{
    position:absolute;
    left:0.1rem;
    top:calc(76%+ 0.1rem);
    width:calc(100% - 0.2rem);
    height:calc(24% - 0.2rem);
}
</style>
