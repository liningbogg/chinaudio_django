<template>
    <div class="main">
        <div id="title">
            <h1>文档OCR训练</h1>
        </div>
        <div id="content">
            <!--标注文档列表-->
            <div id="doc_table">
                <traindoctable />
            </div>
        </div>
    </div>
</template>

<script>
import Traindoctable from '@/components/Traindoctable.vue'

export default {
    name: 'Ocr',
    components:{
        Traindoctable,
    },
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
    width:calc(60% -0.1rem);
    height:6rem;
}
#content{
    position:absolute;
    top:6rem;
    width:calc(100% -0.1rem);
    height:calc(100% - 6.2rem);
}
#doc_table{
    position:absolute;
    left:4rem;
    width:calc(99% - 4.2rem);
    height:calc(50% - 0.2rem);
}
</style>
