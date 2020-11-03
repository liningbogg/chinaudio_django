<template>
    <div class="main">
        <div id="title">
            <h1>古琴音频分析数据库</h1>
        </div>
        <div id="content">
            <!--标注曲目列表-->
            <div id="wave_table">
                <wavetable />
            </div>
            <!--定弦音调-->
            <div id="tune_table">
                <tunetable />
            </div>
        </div>
    </div>
</template>

<script>
import Wavetable from '@/components/Wavetable.vue'
import Tunetable from '@/components/Tunetable.vue'

export default {
    name: 'Target',
    components:{
        Wavetable,
        Tunetable,
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
#wave_table{
    position:absolute;
    left:4rem;
    width:calc(60% - 4.2rem);
    height:calc(100% - 0.2rem);
}
#tune_table{
    position:absolute;
    left:calc(60% + 0.4rem);
    width:calc(40% - 0.4rem);
    height:calc(100% - 0.2rem);
}
</style>
