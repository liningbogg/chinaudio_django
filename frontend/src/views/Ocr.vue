<template>
    <div class="main">
        <div id="title">
            <h1>文档OCR标注数据库</h1>
        </div>
        <div id="content">
            <!--标注文档列表-->
            <div id="doc_table">
                <doctable />
            </div>
            <div id="docassist_table">
                <docassisttable />
            </div>
            <div id="model_table">
                <ocrmodeltable />
            </div>
        </div>
    </div>
</template>

<script>
import Doctable from '@/components/Doctable.vue'
import Docassisttable from '@/components/Docassisttable.vue'
import Ocrmodeltable from '@/components/Ocrmodeltable.vue'

export default {
    name: 'Ocr',
    components:{
        Doctable,
        Docassisttable,
        Ocrmodeltable,
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
    width:calc(50% - 4.2rem);
    height:calc(50% - 0.2rem);
}
#docassist_table{
    position:absolute;
    left:4rem;
    top:50%;
    width:calc(50% - 4.2rem);
    height:calc(30% - 0.2rem);
}
#model_table{
    position:absolute;
    left:calc(50% + 0.1rem);
    top:0;
    width:calc(50% - 0.2rem);
    height:calc(80% - 0.2rem);
}
</style>
