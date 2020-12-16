<template>
    <div id="polygonpage">
        <div id="prior">
            <el-button
                type="text"
                icon="el-icon-arrow-left"
                @click="prior()"
                size="medium"
                >
                上一页
            </el-button>
        </div>
        <div id="current">
            <span style="font-color:blue">
            {{polygonid}}
            </span>
        </div>
        <div id="next">
            <el-button
                type="text"
                icon="el-icon-arrow-right"
                @click="next()"
                size="medium"
                >
                下一页
            </el-button>
        </div>
    </div>
</template>

<script>

export default {
	name: "Polygonpagetool",
    props: ['polygonid'],
    data() {
        return {
        }
    },
    mounted() {
        window.addEventListener('keydown', this.capMove, true);
    },
    beforeDestroy() {
        window.removeEventListener('keydown', this.capMove, true);
    },
    methods: {
        capMove(event){
            const e = event||window.event||arguments.callee.caller.arguments[0];
            if(!e) return;
            if(e.repeat){
                return ;
            }
            const {ctrlKey, key} = e;
            if(ctrlKey && key=='ArrowLeft'){
                this.prior();
                e.preventDefault();
            }
            if(ctrlKey && key=='ArrowRight'){
                this.next();
                e.preventDefault();
            }
        },
        prior(){
            this.axios.get('ocr/polygonidPrior/?polygonid='+this.polygonid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.$emit('nextPolygonFromBackend');
                        }else{
                            this.msg = "切换polygon出错,原因:"+response.data.tip;
                            let message={
                                "type":"notice",
                                "text":this.msg,
                            }
                            this.$store.commit("addMessagetip",message);
                        }
                    }   
                }
            ) 
        },
        next(){
            this.axios.get('ocr/polygonidNext/?polygonid='+this.polygonid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            this.$emit('nextPolygonFromBackend');
                        }else{
                            this.msg = "切换polygon出错,原因:"+response.data.tip;
                            let message={
                                "type":"notice",
                                "text":this.msg,
                            }
                            this.$store.commit("addMessagetip",message);
                        }
                    }   
                }
            ) 
        },

    },
    
    watch: {
        polygonid:{
            handler:function(value){
                console.log(value);
            },
        } 
    },
};
</script>

<style scoped>
#polygonpage{
    top:0rem;
    width:100%;
    height:100%;
}
#prior{
    top:0rem;
    width:40%;
    height:100%;
    position:absolute;
}
#current{
    top:0rem;
    width:20%;
    left:40%;
    height:100%;
    line-height:100%;
    position:absolute;
    display:grid;
    align-items: center;
}
#next{
    top:0rem;
    left:60%;
    width:40%;
    height:100%;
    position:absolute;
}
.el-button{
    width:100%;
    height:100%;
}
</style>
