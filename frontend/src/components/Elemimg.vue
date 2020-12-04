<template>
    <div id="imagebox" v-on:click="handleSelect" :style="{'border-color':bordercolor, 'border-width':borderwidth}">
    </div>
</template>

<script>

export default {
	name: "Elemimg",
    props: ['elemid'],
    data() {
        return {
        }
    },
    computed:{
        isChecked:function(){
            return this.$store.getters.isElemSelected(this.elemid);
        },
        borderwidth:function(){
            if(this.isChecked==true){
                return '2px';
            }else{
                return '1px';
            }
        },
        bordercolor:function(){
            if(this.isChecked==true){
                return 'green';
            }else{
                return 'gray';
            }
        },
    },
    mounted() {
    },
    beforeDestroy() {
    },
    methods: {
        handleSelect(){
            this.$store.commit("changeElemSelected", this.elemid);
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
</style>
