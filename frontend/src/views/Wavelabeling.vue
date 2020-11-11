<template>
    <div class="main">
        <!--左侧图表，主要是标记片段的信息-->
        <div id="clipinfo">
            <div id="localinfo">
                <localinfo :currentframe="current_frame"/>
            </div>
            <div id="spectrum">
                <framesrc :currentframe="current_frame" ref="framesrc" @spectrogramOn="handleSpectrogramOn"/>
            </div>
        </div>
        <div id="spectrogram" v-if="hasSpectrogram">
            <spectrumchart :currentframe="current_frame" />
        </div>
        <!--右侧标注,主要是wave配置以及标注-->
        <div id="labeling">
            <!--标注参考-->
            <div id="ref">
                <refconfigure></refconfigure>
            </div>
            <!--配置信息-->
            <div id="configue">
                <waveconfigure :currentframe="current_frame"> </waveconfigure>
            </div>
            <!--夜跳转信息-->
            <div id="pages">
            </div>
        </div>
    </div>
</template>

<script>
import Waveconfigure from '@/components/Waveconfigure.vue'
import Refconfigure from '@/components/Refconfigure.vue'
import Localinfo from '@/components/Localinfo.vue'
import Framesrc from '@/components/Framesrc.vue'
import Spectrumchart from '@/components/Spectrumchart.vue'

export default {
    name: 'Wavelabeling',
    components:{
        Waveconfigure,
        Refconfigure,
        Spectrumchart,
        Localinfo,
        Framesrc,
    },
    data() {
        return {
            waveid:null,
            playstatusCustom:"el-icon-video-play",
            hasSpectrogram:false,
            current_frame:null,
            formInline:{
                start:null,
                end:null,
            },
        }
    },
    mounted(){
        this.waveid = this.$route.query.waveid;
        this.nextframeFromBackend();
    },
    methods:{
        onEvaluate(){
            this.$refs.framesrc.customEvaluate(this.formInline.start, this.formInline.end);
        },
        handleSpectrogramOn(isEnable){
            let spectrogramOn=isEnable;
            console.log(spectrogramOn);
            if(spectrogramOn){
                //压缩div空间
                let divclipinfo=document.getElementById("clipinfo");
                divclipinfo.style.width="calc(45% - 1.2rem)";
                let divlabeling=document.getElementById("labeling");
                divlabeling.style.width="calc(35% - 0.5rem)";
                divlabeling.style.left="calc(65% + 0.4rem)";
                this.hasSpectrogram=spectrogramOn;

            }else{
                this.hasSpectrogram=spectrogramOn;
                //恢复div尺寸
                let divclipinfo=document.getElementById("clipinfo");
                divclipinfo.style.width="calc(55% - 1.2rem)";
                let divlabeling=document.getElementById("labeling");
                divlabeling.style.width="calc(45% - 0.5rem)";
                divlabeling.style.left="calc(55% + 0.4rem)";

            }
        },
        nextframeFromBackend(){
            this.axios.get('target/nextframe/?waveid='+this.waveid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.current_frame = response.data.body;
                            this.formInline.start=this.current_frame;
                            this.formInline.end=this.current_frame+1;
                        }else{
                            this.msg = "获取待标记帧号出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            )
        },

    },

}
</script>
<style scoped >

/deep/ .el-form--inline .el-form-item {
    margin-right: 0;
    height:100%;
}
/deep/ .el-form-item {
    margin-bottom: 0;
}
/deep/ .el-form-item__label{
    text-align: right;
    float: left;
    color: #606266;
    height:100%;
    line-height:normal;
    width:30%;
    padding: 0 0 0 0;
    box-sizing: border-box;
    font-size:1rem;
}
/deep/ .el-form-item__content{
    line-height:100%;
    width:69%;
    height:100%;
}
/deep/ .el-input__inner{
    line-height:100%;
    text-align: center;
    height:100%;
    font-size:1rem;
}
.el-button{
    height:100%;
    width:100%;
    padding:0;
}
.el-input{
    height:100%;
}
#main{
    position:absolute;
    width: calc(100% - 0.1rem);
    height: calc(100% - 0.1rem);
}
#clipinfo{
    position:absolute;
    left:1rem;
    width:calc(55% - 1.2rem);
    height:calc(100% - 0.2rem);
}
#localinfo{
    position:absolute;
    left:0rem;
    width:calc(100% - 0.5rem);
    height:calc(60% - 0.2rem);
}
#spectrum{
    position:absolute;
    left:0rem;
    top:60%;
    width:calc(100% - 0.5rem);
    height:calc(40% - 0.2rem);
}
#stftchart{
    position:absolute;
    left:0;
    top:0;
    width:calc(50% - 0.1rem);
    height:calc(100% - 0.1rem);
}
#medium{
    position:absolute;
    left:50%;
    top:0;
    width:calc(50% - 0.1rem);
    height:calc(100% - 0.1rem);
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
#spectrogram{
    position:absolute;
    left:calc(45% + 0.4rem);
    width:calc(20% - 0.5rem);
    height:calc(100% - 0.2rem);
}
#labeling{
    position:absolute;
    left:calc(55% + 0.4rem);
    width:calc(45% - 0.5rem);
    height:calc(100% - 0.2rem);
}
#ref{
    position:absolute;
    left:0.2rem;
    width:calc(100% - 0.4rem);
    height:2rem;
}
#configue{
    position:absolute;
    left:0.2rem;
    width:calc(100% - 0.4rem);
    top:2.2rem;
    height:5.2rem;
}
#pages{
    position:absolute;
    left:0.2rem;
    width:calc(100% - 0.4rem);
    top:7.45rem;
    height:1.8rem;
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
</style>
