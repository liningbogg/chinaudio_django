<template>
    <div id="main">
        <div id="elembox" ref="elemboxa" :style="boxstyle">
            <img :src="imgpath">
        </div>
    </div>
</template>

<script>

export default {
	name: "Elemconfigure",
    props: ['currentframe', 'polygonid'],
    components:{
    },
    computed: {
        imgpath:function(){
            let elemid = this.$store.getters.getElemtoconfigure;
            if(elemid){
                return "/ocr/getElemImage/?elemid="+elemid+"&time="+new Date().getTime();
            }else{
                return null;
            }
        }
    },
    data() {
        return {
            boxstyle:{
                width:null,
            }
        }
    },
    mounted() {
        this.setWidth();
        window.addEventListener(
            'resize',
            () => { 
                this.setWidth();
            },
            false
        )
    },
    beforeDestroy() {
    },
    methods: {
        setWidth(){
            this.boxstyle.width = this.$refs.elemboxa.offsetHeight+"px";
        },
        elemFromBackend(){
            this.axios.get('ocr/getElemset/').then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let elems = response.data.body.elemset;
                            this.elemnum = elems.length;
                            let elemset = new Array();
                            for(let key in elems){
                                let _left = key % 80 % 10 * 4.5;
                                let _top = Math.floor(key % 80 / 10) * 4.5;
                                let show = Math.floor(key / 80)==(this.pageid-1)?true:false;
                                elemset.push({"elemid":elems[key], "style":"left:"+_left+"rem;top:"+_top+"rem;", "show":show})
                            }
                            this.elemset=elemset;
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
        boxheight:{
            handler:function(value){
                alert(value);
                console.log(value);
            },
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
    height:100%;
    border-color:red;
    border-width:0.05rem;
    border-style:solid;
}
div img{
    width: 100%;
    height: 100%;
    object-fit:contain;
}


</style>
