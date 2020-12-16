<template>
    <div id="main">
        <div id="elembox">
            <div class="elemitem" v-for="item in elemrelated" :key="item.id" :style="item.style">
                <elemimg :elemid="item.id" :polygonid="polygonid" />
            </div>
        </div>
        <div id="assistcharacter">
            <el-input
                type="textarea"
                :rows=1
                v-model="characters"
                ref="characters"
            >
            </el-input>
        </div>
    </div>
</template>

<script>
import Elemimg from '@/components/Elemimg.vue'

export default {
	name: "Elemassist",
    props: ['currentframe', 'polygonid'],
    components:{
        Elemimg,
    },
    data() {
        return {
            elemrelated:[],
            characters:"",
        }
    },
    mounted() {
        this.$refs.characters.focus();
    },
    beforeDestroy() {
    },
    computed:{
    },
    methods: {
        elemrelatedFromBackend(){
            if(this.characters==""){
                this.elemrelated=[];
            }
            this.axios.get('ocr/getElemRelated/?characters='+this.characters).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.elemrelated=[];
                            let elemrelated = JSON.parse(response.data.body.elemrelated_str);
                            for(let index in elemrelated){
                                let _left = index * 4.8;
                                this.elemrelated.push({"id":elemrelated[index], "style":"left:"+_left+"rem;top:0;"});
                            }
                            console.log(elemrelated);
                        }else{
                            this.msg = "获取elem related出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },

    },
    
    watch: {
        currentframe:{
            handler:function(value){
                console.log(value);
            },
            immediate: true,
        }, 
        polygonid:{
            handler:function(value){
                if(value!=null){
                    console.log("当前polygonid:"+value);
                    //应该清空
                    this.characters="";
                }
            },
            immediate: true,
        }, 
        characters:{
            handler:function(value){
                this.elemrelatedFromBackend();
            },
            immediate: true,
        }, 
    },
};
</script>

<style scoped>
#main{
    top:0rem;
    width:100%;
    height:100%;
}
#elembox{
    position:absolute;
    left:0rem;
    top:0rem;
    height:4.5rem;
    width:100%;
}
.elemitem{
    position:absolute;
    height:4.5rem;
    width:4.5rem;
}
#assistcharacter{
    position:absolute;
    left:0rem;
    top:4.6rem;
    height:2.5rem;
    width:100%;
}
.el-input{
    height:100%;
}
/deep/ .el-textarea__inner,
.el-textarea {
    height: 100% !important;
    font-size: 1.5rem;
    line-height: normal;
}

</style>
