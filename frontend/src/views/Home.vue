<template>
    <div class="home" style="">
        <div class="content">
            <router-view>
            </router-view>
        </div>
    </div>
</template>

<script>

export default {
    name: 'Home',
}
</script>
<style scoped lang="less">
.content{
    position:relative;
    width: 100rem;
    height: 80%;
    float:right;
    overflow-y:auto;
}
</style>
