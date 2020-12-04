<template>
    <div id="main">
        <div id="elembox">
            <div class="elemitem"
                v-for="item in elemset" :key="item.elemid" :style="item.style" v-show="item.show"
            >
                <elemimg :elemid="item.elemid" />
            </div>
        </div>
        <div id="pagenavi">

        </div>
    </div>
</template>

<script>
import Elemimg from '@/components/Elemimg.vue'

export default {
	name: "Elemlist",
    props: ['currentframe', 'polygonid'],
    components:{
        Elemimg,
    },
    data() {
        return {
            elemset:[],
            pageid:0,
        }
    },
    mounted() {
        this.elemFromBackend();
    },
    beforeDestroy() {
    },
    methods: {
        elemselectedFromBackend(){
            this.axios.get('ocr/getElemselected/?polygonid='+this.polygonid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let elemselected = response.data.body.elemselected;
                            console.log(elemselected);
                            this.$store.commit("initElemSelected",elemselected);

                        }else{
                            this.msg = "获取elemselected出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },
        elemFromBackend(){
            this.axios.get('ocr/getElemset/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let elems = response.data.body.elemset;
                            for(let key in elems){
                                let _left = key % 80 % 10 * 4.5;
                                let _top = Math.floor(key % 80 / 10) * 4.5;
                                let show = Math.floor(key / 80)==this.pageid?true:false;
                                this.elemset.push({"elemid":elems[key], "style":"left:"+_left+"rem;top:"+_top+"rem;", "show":show})
                            }

                            console.log(this.elemset);
                        }else{
                            this.msg = "获取elem出错,原因:"+response.data.tip;
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
        } 
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
    height:36rem;
    width:100%;
}
.elemitem{
    position:absolute;
    height:4.5rem;
    width:4.5rem;
}
#pagenavi{
    position:absolute;
    left:0rem;
    top:calc(36rem + 2px);
    height:28px;
    width:100%;
    border-color:red;
    border-width:0.01rem;
    border-style:solid;
}

</style>
