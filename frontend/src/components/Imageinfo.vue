<template>
    <div id="imageinfo">
        <div id="tarwidth">
            tarwidth:{{tarwidth}}
        </div>
        <div id="tarheight">
            tarheight:{{tarheight}}
        </div>
        <div id="polygonnumall">
            polygon_all:{{polygonnumall}}
        </div>
        <div id="polygonnumuser">
            polygon_user:{{polygonnumuser}}
        </div>
    </div>
</template>

<script>

export default {
	name: "Imageinfo",
    props: ['currentframe', 'tarwidth', 'tarheight'],
    data() {
        return {
            docid:null,
            timer:null,
            polygonnumuser:0,
            polygonnumall:0,
        }
    },
    beforeDestroy() {
        if(this.timer){
            clearInterval(this.timer);
        }
    },
    methods: {
        polygonnumFromBackend(){
            this.axios.get('ocr/getPolygonNum/?currentframe='+this.currentframe+"&docid="+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            console.log(response.data.body);
                            let polygonnumInfo = response.data.body;
                            this.polygonnumuser = polygonnumInfo.polygonnumuser;
                            this.polygonnumall = polygonnumInfo.polygonnumall;
                        }else{
                            this.msg = "获取标注矩形出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },

    },
    
    mounted() {
        this.docid = this.$route.query.docid;
        this.timer = setInterval(this.polygonnumFromBackend, 5000);
    },
    watch: {
        currentframe:{
            handler:function(value){
                console.log(value);
                this.polygonnumFromBackend();
            },
        } 
    },

}
</script>

<style scoped>
#imageinfo{
    top:0rem;
    width:100%;
    height:100%;
}
#tarwidth{
    position:absolute;
    top:0rem;
    left:0rem;
    width:10%;
    height:100%;
    line-height:100%;
    display: grid;
    align-items: center;
}
#tarheight{
    position:absolute;
    top:0rem;
    left:10%;
    width:10%;
    line-height:100%;
    height:100%;
    display: grid;
    align-items: center;
}
#polygonnumall{
    position:absolute;
    top:0rem;
    left:20%;
    width:10%;
    line-height:100%;
    height:100%;
    display: grid;
    align-items: center;
}
#polygonnumuser{
    position:absolute;
    top:0rem;
    left:30%;
    width:10%;
    line-height:100%;
    height:100%;
    display: grid;
    align-items: center;
}
</style>
