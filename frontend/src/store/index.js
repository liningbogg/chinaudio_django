import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
    strict: true,
    state: {
        AILabelmode:"draw",
        AIToolmode:"manual",
    },
    getters: {
        getAILabelmode(state){
            return state.AILabelmode
        },
        getAIToolmode(state){
            return state.AIToolmode
        },
    },
    mutations: {
        setAILabelmode(state, AILabelmode){
            state.AILabelmode=AILabelmode
        },
        setAIToolmode(state, AIToolmode){
            state.AIToolmode=AIToolmode
        }
    },
    actions: {
    },
    modules: {
    }
})
