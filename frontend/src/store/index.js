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
    },
    getters: {
        getAILabelmode(state){
            return state.AILabelmode
        },
        getAIToolmode(state){
            return state.AIToolmode
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
    },
    mutations: {
        setAILabelmode(state, AILabelmode){
            state.AILabelmode=AILabelmode
        },
        setAIToolmode(state, AIToolmode){
            state.AIToolmode=AIToolmode
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
    },
    actions: {
    },
    modules: {
    }
})
