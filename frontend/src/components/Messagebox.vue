<template>
    <div id="messagebox">
    </div>
</template>

<script>

export default {
	name: "Messagebox",
    data() {
        return {
        }
    },
    mounted() {
    },
    computed: {
        messagecontent:function(){
            return this.$store.getters.getMessagetip;
        },
    },
    beforeDestroy() {
    },
    methods: {
    },
    watch: {
        messagecontent:{
            handler:(value) => {
                let divmessage = document.getElementById('messagebox');
                divmessage.innerHTML =value;
                divmessage.scrollTop = divmessage.scrollHeight;
            },
        },
    },

};
</script>

<style scoped>
#messagebox{
    top:0rem;
    width:100%;
    height:100%;
    text-align:left;
    word-wrap:break-word;
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
    overflow-y:auto;
    overflow-x:auto;
}
</style>
