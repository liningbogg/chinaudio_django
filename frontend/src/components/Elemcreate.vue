<template>
    <div id="main">
        <div id="elembox" ref="elemboxa" :style="boxstyle">
            <img :src="imgpath">
        </div>
    </div>
</template>

<script>

export default {
	name: "Elemcreate",
    components:{
    },
    computed: {
        imgpath:function(){
            let roi = this.$store.getters.getRoi;
            if(roi){
                return "/ocr/getSubImage/?imageid="+roi.imageid+"&current_rotate="+roi.current_rotate+"&points="+roi.image_points_str+"&padding=true&time="+new Date().getTime();
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
