<template>
    <div id="imagebox">
    </div>
</template>

<script>

export default {
	name: "Waveconfigure",
    props: ['currentframe'],
    data() {
        return {
            docid:null,
        }
    },
    mounted() {
        this.docid = this.$route.query.docid;
    },
    beforeDestroy() {
    },
    methods: {
        ploygonFromBackend(){
            this.axios.get('ocr/getPloygons/?currentframe='+this.currentframe+"&docid="+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                        }else{
                            this.msg = "获取标注矩形出错,原因:"+response.data.tip;
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
                this.ploygonFromBackend();
                console.log(value);
            },
        } 
    },
};
</script>

<style scoped>
#imagebox{
    top:0rem;
    width:100%;
    height:100%;
}
</style>
