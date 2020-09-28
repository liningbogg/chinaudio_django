<template>
    <div class="main">
        <div id="title">
        </div>
        <div id="content">
        </div>
    </div>
</template>

<script>

export default {
    name: 'Target',
    data() {
        return {
        }
    },

}
</script>
<style scoped lang="less">
.main{
    position:absolute;
    width: calc(100% - 0.1rem);
    height: calc(100% - 0.1rem);
}
#title{
    position:absolute;
    top:0rem;
    width:calc(100% -0.1rem);
    height:6rem;
    border-color:green;
    border-width:0.05rem;
    border-style:solid;
}
#content{
    position:absolute;
    top:6rem;
    width:calc(100% -0.1rem);
    height:calc(100% - 6.2rem);
    border-color:blue;
    border-width:0.05rem;
    border-style:solid;
}
</style>
