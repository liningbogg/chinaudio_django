<template>
    <div id="main">
        <div id="elembox">
            <div class="elemitem"
                v-for="item in elemselected" :key="item.id" :style="item.style"
            >
                <elemimg :elemid="item.id" :polygonid="polygonid" />
            </div>
        </div>
    </div>
</template>

<script>
import Elemimg from '@/components/Elemimg.vue'

export default {
	name: "Elemselected",
    props: ['currentframe', 'polygonid'],
    components:{
        Elemimg,
    },
    data() {
        return {
            elemselected:[],
        }
    },
    mounted() {
        
    },
    beforeDestroy() {
    },
    computed:{
        _elemselected:function(){
            return this.$store.getters.getElemSelected;
        },
    },
    methods: {
        elemselectedFromBackend(){
            this.axios.get('ocr/getElemselected/?polygonid='+this.polygonid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let elemselected = response.data.body.elemselected;
                            this.$store.commit("initElemSelected",elemselected);

                        }else{
                            this.msg = "获取elemselected出错,原因:"+response.data.tip;
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
                    this.elemselectedFromBackend();
                }
            },
            immediate: true,
        }, 
        _elemselected:{
            handler:function(value){
                if(value!=null){
                    // 将下边这句改为 带有style的字典数组
                    this.elemselected = new Array();
                    for(let index in value){
                        let _left = index * 4.8;
                        this.elemselected.push({"id":value[index], "style":"left:"+_left+"rem;top:0;"});
                    }
                    console.log(this.elemselected);
                }
            },
            deep: true,
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
</style>
