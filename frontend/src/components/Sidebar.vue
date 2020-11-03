<template>
    <div class="sidebar">
        <el-menu
            class="el-menu-vertical-demo"
            :background-color=bardata.background_color
            :text-color=bardata.text_color
            :active-text-color=bardata.active_text_color
            :default-active="$route.path"
        >
        <template v-for="item in bardata.menulist">
            <router-link :to="item.url" :key="item.id">
                <el-menu-item :index="item.id.toString()">
                    <i :class="item.icon"></i>
                    <span slot="title">{{item.name}}</span>
                </el-menu-item>
            </router-link>
        </template>
        </el-menu>

    </div>
</template>

<script>

export default {
	name: "Sidebar",
    data() {
        return {
        }
    },
    props: ['bardata'], 
    mounted() {
        console.log(this.bardata);
    },

    beforeDestroy() {
    },
    methods: {
    },
    
};
</script>

<style scoped>
.sidebar{
    height:100%;
}
.el-menu-vertical-demo{
    height:100%;
}
</style>
