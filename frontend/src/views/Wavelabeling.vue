<template>
    <div class="main">
        <!--左侧图表，主要是标记片段的信息-->
        <div id="clipinfo">
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
        </div>
    </div>
</template>

<script>
import Waveconfigure from '@/components/Waveconfigure.vue'
import Refconfigure from '@/components/Refconfigure.vue'

export default {
    name: 'Wavelabeling',
    components:{
        Waveconfigure,
        Refconfigure,
    },
    data() {
        return {
            waveid:null,
            current_frame:null,
        }
    },
    mounted(){
        this.waveid = this.$route.query.waveid;
        this.nextframeFromBackend();
    },
    methods:{
        nextframeFromBackend(){
            this.axios.get('target/nextframe/?waveid='+this.waveid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.current_frame = response.data.body;
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
<style scoped lang="less">
.main{
    position:absolute;
    width: calc(100% - 0.1rem);
    height: calc(100% - 0.1rem);
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
#clipinfo{
    position:absolute;
    left:1rem;
    width:calc(60% - 1.2rem);
    height:calc(100% - 0.2rem);
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
#labeling{
    position:absolute;
    left:calc(60% + 0.4rem);
    width:calc(40% - 0.5rem);
    height:calc(100% - 0.2rem);
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
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
    height:6.2rem;
    border-color:cyan;
    border-width:0.05rem;
    border-style:solid;
}
</style>
