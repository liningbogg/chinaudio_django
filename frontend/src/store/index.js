import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
    strict: true,
    state: {
        AILabelmode:"draw",
        AIToolmode:"manual",
        Recommenttip_option:null,
        Messagetip:[],
        Elemselected:[],
        Contentlabelingmode:"labeling",  // labeling:标注模式;configure:配置模式  内容标注模块
    },
    getters: {

        getAILabelmode(state){
            return state.AILabelmode
        },
        getAIToolmode(state){
            return state.AIToolmode
        },
        getContentlabelingmode(state){
            return state.Contentlabelingmode
        },
        getMessagetip(state){
            let tip="";
            const color={
                "warning":"#ff00ff",
                "success":"green",
                "err":"red",
                "notice":"blue",
            };
            for(let elem of state.Messagetip){
                tip+="<span style='color:"+color[elem.type]+"'>"+elem.text+"</span><br>";
            }
            return tip;
        },
        getRecommenttip_option(state){
            return state.Recommenttip_option;
        },
        isElemSelected(state){
            return function (args) {
                if(args==null) return false;
                if(state.Elemselected.indexOf(args)<0){
                    return false;
                }else{
                    return true;
                }
            };
        },
    },
    mutations: {
        setAILabelmode(state, AILabelmode){
            state.AILabelmode=AILabelmode
        },
        setAIToolmode(state, AIToolmode){
            state.AIToolmode=AIToolmode
        },
        setContentlabelingmode(state, Contentlabelingmode){
            state.Contentlabelingmode=Contentlabelingmode
        },
        addMessagetip(state, Message){
            if(state.Messagetip.length>19){
                state.Messagetip.shift();
            }
            state.Messagetip.push(Message);
        },
        setRecommenttip_option(state, option){
            state.Recommenttip_option=option;
        },
        changeElemSelected(state, item){
            let isSelect = item.isSelect;
            let elem = item.elem
            let index = state.Elemselected.indexOf(elem);
            console.log(isSelect, index);
            if(isSelect==true){
                if(index<0){
                    state.Elemselected.push(elem);
                }
            }else{
                if(index>=0){
                    state.Elemselected.splice(index, 1);
                }
            }
        },
        initElemSelected(state, elemset){
            state.Elemselected.splice(0,state.Elemselected.length);
            for(let elem of elemset){
                state.Elemselected.push(elem);
            }
        },
    },
    actions: {
    },
    modules: {
    }
})
