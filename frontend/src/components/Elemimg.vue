<template>
    <div id="imagebox" v-on:click="handleSelect" :style="{'border-color':bordercolor, 'border-width':borderwidth}">
        <img :src="imgpath">
    </div>
</template>

<script>

export default {
	name: "Elemimg",
    props: ['elemid', 'polygonid'],
    data() {
        return {
        }
    },
    computed:{
        contentlabelingmode:function(){
            return this.$store.getters.getContentlabelingmode;
        },
        isChecked:function(){
            return this.$store.getters.isElemSelected(this.elemid);
        },
        imgpath:function(){
            return "/ocr/getElemImage/?elemid="+this.elemid+"&time="+new Date().getTime();
        },
        borderwidth:function(){
            if(this.isChecked==true){
                return '3px';
            }else{
                return '1px';
            }
        },
        bordercolor:function(){
            if(this.isChecked==true){
                return 'blue';
            }else{
                return '#d3d3d3';
            }
        },
    },
    mounted() {
    },
    beforeDestroy() {
    },
    methods: {
        handleSelect(){
            if(this.contentlabelingmode=="labeling"){
                let elem_list = new Array();
                if(this.isChecked == true){
                    elem_list.push({"elemid":this.elemid, "oper":"remove"});
                }else{
                    elem_list.push({"elemid":this.elemid, "oper":"add"});
                }
                this.axios.get('ocr/alter_elem_selected/?polygonid='+this.polygonid+"&elem_list="+JSON.stringify(elem_list)).then(
                    response => {
                        if(response){
                            if(response.data.status==="success"){
                                let alter_info = response.data.body;
                                let elem_add = alter_info.elem_add;
                                let elem_remove = alter_info.elem_remove;
                                console.log(elem_add);
                                console.log(elem_remove);
                                for(let elem of elem_add){
                                    this.$store.commit("changeElemSelected", {"elem":elem, "isSelect":true});
                                }
                                for(let elem of elem_remove){
                                    this.$store.commit("changeElemSelected", {"elem":elem, "isSelect":false});
                                }
                            }else{
                                this.msg = "增添elem出错,原因:"+response.data.tip;
                                console.log(this.msg);
                            }
                        }   
                    }
                ) 
                return;
            }
            if(this.contentlabelingmode=="configure"){
                this.$store.commit("setElemtoconfigure", this.elemid);
                return;
            }
        },
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
        isChecked:{
            handler:(value) => {
                console.log(value);
            },
        } 
    },
};
</script>

<style scoped>
#imagebox{
    position:absolute;
    top:0.2rem;
    left:0.2rem;
    width:4rem;
    height:4rem;
    border-color:gray;
    border-style:solid;
}
div img{
    width: 100%;
    height: 100%;
    object-fit:contain;
}
</style>
