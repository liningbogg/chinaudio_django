<template>
    <div class="home">
        <div class="entrance">
            <div class="entrance_target">
                <router-link to="/target">古琴音频数据库</router-link>
            </div>
            <div class="entrance_ocr">
                <router-link to="/ocr">古琴OCR数据库</router-link>
            </div>
        </div>
    </div>
</template>

<script>

export default {
    name: 'Home',
}
</script>
<style scoped lang="less">
.home{
    height:100%;
    width:100%;
}
.entrance{
    left: calc(50% - 12rem);
    top: calc(16% - 4rem);
    height:3rem;
    width:24rem;
    position:absolute;
    font-size:2rem;
}
#entrance a {
  font-weight: bold;
  color: #2c3e50;
}
#entrance a.router-link-exact-active {
  color: #42b983;
}

</style>
