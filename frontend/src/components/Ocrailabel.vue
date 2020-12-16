<template>
    <div id="imagebox">
    </div>
</template>
<script>
import gDBox from "@/lib/gDBox.pkg.min.js"
class GdboxConfigure {
    constructor(current_user, gMap){
        this.current_user=current_user;
        this.gMap=gMap;
        this.lineWeight=1;
        this.current_user_color_noncontent="#0000ff";
        this.current_user_color_hascontent="#00ff00";
        //new gDBox.Layer.Feature('featureLayer', {zIndex: 2, transparent: true})  // color assing to current_user (blue)
        this.nonactive_current_index=0;  // color index assign to non-active user
        this.nonactive_color_list=[
            {"color_name":"red","color_value":"#ff0000"},
            {"color_name":"green","color_value":"#00ff00"},
        ];
        // user_name feature_style map
        this.feature_style_set={
        };
        this.feature_style_set["current_user_noncontent"] = new gDBox.Style({strokeColor: this.current_user_color_noncontent, lineWeight: this.lineWeight});
        this.feature_style_set["current_user_hascontent"] = new gDBox.Style({strokeColor: this.current_user_color_hascontent, lineWeight: this.lineWeight});
        // user_name layer map
        this.layer_set={
        };
        this.layer_set[this.current_user]= new gDBox.Layer.Feature(this.current_user, {zIndex: 2, transparent: true});
        this.gMap.addLayer(this.layer_set[current_user]);

    }
    get_style(user_name, has_content){
        if(user_name!=this.current_user){
            //non-activate user
            if(Object.prototype.hasOwnProperty.call(this.feature_style_set, user_name)){
                return this.feature_style_set[user_name];
            }else{
                this.feature_style_set[user_name] =new gDBox.Style(
                    {
                        strokeColor: this.nonactive_color_list[this.nonactive_current_index]["color_value"],
                        lineWeight: this.lineWeight
                    }
                );

                return this.feature_style_set[user_name];
            }
        }else{
            //current user
            if(has_content==true){
                return this.feature_style_set["current_user_hascontent"];
            }else{
                return this.feature_style_set["current_user_noncontent"];
            }
        }
    }
    get_layer(user_name){
        if(user_name!=this.current_user){
            if(Object.prototype.hasOwnProperty.call(this.layer_set, user_name)){
                return this.layer_set[user_name];
            }else{
                this.layer_set[user_name] = new gDBox.Layer.Feature(user_name, {zIndex: 2, transparent: true, opacity: false});
                this.gMap.addLayer(this.layer_set[user_name]);
                return this.layer_set[user_name];
            }
        }else{
            return this.layer_set[user_name];
        }
    }

}

export default {
	name: "Ocrailabel",
    props: ['currentframe'],
    data() {
        return {
            docid:null,
        }
    },
    mounted() {
        this.docid = this.$route.query.docid;
        let div_img=document.getElementById("imagebox");
        this.divwidthmax=div_img.offsetWidth;
        this.divheightmax=div_img.offsetHeight;
        this.indexArr=new Array(100000);
        for(var i=0;i<99999;i++){
            this.indexArr[i]=i;
        }

    },
    computed: {
        labelmode:function(){
            return this.$store.getters.getAILabelmode;
        },
        toolmode:function(){
            return this.$store.getters.getAIToolmode;
        },
    },
    beforeDestroy() {
    },
    methods: {
        //w_box为div原始尺寸
        cal_size(w_box,h_box,w,h,is_vertical){
            let height=0;
            let width=0;
            if(is_vertical ==true){
                height = h_box;
                width=Math.round(w*1.0/h*height);
            }else{
                width = w_box;
                height = Math.round(h*1.0/w*width);
            }
            return {"width":width,"height":height};
        },
        ploygonFromBackend(){
            this.axios.get('ocr/getPloygons/?currentframe='+this.currentframe+"&docid="+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            console.log(response.data.body);
                        }else{
                            this.msg = "获取标注矩形出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ) 
        },
        clearMap(){
            //销毁标注图层
            if(this.gMap!=null){
                this.gMap.destroy();
                console.log("清空标注图层");
            }
            //销毁相关数据
            this.polygonList=[];
        },
        img2gdbox_map(points, width, height,width_ori,height_ori){
            let points_img=new Array();
            for(let point of points){
                let mapx=Math.round(-width/2.0 + point["x"]*1.0*width/width_ori);
                let mapy=Math.round(height/2.0 - point["y"]*1.0*height/height_ori);
                points_img.push({"x":mapx,"y":mapy});
            }
            return points_img;
        },
        /*gdbox-图像矩阵坐标映射*/
        gdbox2img_map(points, width, height,width_ori,height_ori){
            let points_img=new Array();
            for(let point of points){
                let mapx=Math.round((width/2.0 + point["x"])*width_ori/width);
                let mapy=Math.round((height/2.0 - point["y"])*height_ori/height);
                points_img.push({"x":mapx,"y":mapy});
            }
            return points_img;
        },

        rotate_polygon(polygon_points, current_rotate, width, height){
            let polygon_rotated = Array();
            for(let point_index in polygon_points){
                let point = polygon_points[point_index];
                let x = point['x'];
                let y = point['y'];
                let x_shift = x-width/2.0;
                let y_shift = y-height/2.0;
                let rotate_rad = current_rotate/180.0*Math.PI;
                let nx = x_shift*Math.cos(rotate_rad)+y_shift*Math.sin(rotate_rad)+width/2.0;
                let ny = -x_shift*Math.sin(rotate_rad)+y_shift*Math.cos(rotate_rad)+height/2.0;
                polygon_rotated.push({'x':nx,'y':ny});
            }
            return polygon_rotated;
        },
        /*区域删除*/
        region_delete(image_id, points, gFeatureLayer){
            let pointsStr=JSON.stringify(points);
            this.axios.get('ocr/regionDelete/?image_id='+image_id+"&rotate_points_str="+pointsStr).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let info_delete = response.data.body.delete_info;
                            for(let polygon_id in info_delete){
                                gFeatureLayer.removeFeatureById(polygon_id+"");
                            }
                            let message={
                                "type":"notice",
                                "text":"区域删除:"+Object.keys(info_delete).length+"个polygon被删除",
                            }
                            this.$store.commit("addMessagetip",message);
                        }else{
                            this.msg = "区域删除出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ); 
        },
        /*融合*/
        merge_labeling(image_id, points, gFeatureLayer, gFetureStyle){
            let pointsStr=JSON.stringify(points);
            this.axios.get('ocr/merge_labeling/?image_id='+image_id+"&rotate_points_str="+pointsStr).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let delete_info = response.data.body.delete_info;
                            let polygon_add = response.data.body.polygon_add;
                            let polygon_points = JSON.parse(polygon_add.points);
                            let polygon_id = polygon_add.polygon_id;
                            //rotate the label
                            let rotate=this.current_rotate;
                            let polygon_rotated = this.rotate_polygon(polygon_points,rotate,this.ori_width,this.ori_height);
                            //map it into feature layer
                            let polygon_map = this.img2gdbox_map(polygon_rotated, this.tar_width, this.tar_height, this.ori_width, this.ori_height);
                            this.add_polygon_disp(gFeatureLayer, gFetureStyle, polygon_map, polygon_id, polygon_add.create_user_id);
                            for(let elem of delete_info){
                                //delete feature related
                                gFeatureLayer.removeFeatureById(elem.polygon_id+"");
                                //在polygon_dict中移除元素
                                delete this.polygonList[elem.polygon_id];
                            }

                        }else{
                            this.msg = "区域融合出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }
                }
            );
        },

        /*粗标注*/
        rough_labeling(image_id, points, gFeatureLayer, gFetureStyle){
            let pointsStr=JSON.stringify(points);
            this.axios.get('ocr/rough_labeling/?image_id='+image_id+"&rotate_points_str="+pointsStr).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let info_rough = response.data.body;
                            console.log(info_rough);
                            for(let elem of info_rough.delete_info){
                                //delete feature related
                                gFeatureLayer.removeFeatureById(elem.polygon_id+"");
                                //在polygon_dict中移除元素
                                delete this.polygonList[elem.polygon_id];
                            }
                            let polygon_add = info_rough.polygon_add;
                            for(let polygon in polygon_add){
                                let elem = polygon_add[polygon];
                                let polygon_points = JSON.parse(elem['points']);
                                let polygon_id = elem['polygon_id'];
                                //rotate the label
                                let rotate=this.current_rotate;
                                let polygon_rotated = this.rotate_polygon(polygon_points,rotate,this.ori_width,this.ori_height);
                                //map it into feature layer
                                console.log(polygon_rotated, this.tar_width, this.tar_height, this.ori_width,this.ori_height);
                                let polygon_map = this.img2gdbox_map(polygon_rotated, this.tar_width, this.tar_height, this.ori_width, this.ori_height);
                                console.log(polygon_map, polygon_id, elem['create_user_id']);
                                this.add_polygon_disp(gFeatureLayer, gFetureStyle, polygon_map, polygon_id, elem['create_user_id']);
                            }
                            //设置粗标注图形option
                            let projection = JSON.parse(info_rough.projection);
                            let entropy = JSON.parse(info_rough.entropy);
                            let entropy_diff = JSON.parse(info_rough.entropy_diff);
                            let chartOption = {
                                backgroundColor:"#f0f0f0",
                                color:['#ff0000','#0000ff', '#000000', '#ff34b3', '#8b8b00','#aa00ff','#006464', '#00008b', '#8b0000'],
                                title : 
                                {
                                    show:true,//显示策略，默认值true,可选为：true（显示） | false（隐藏）
                                    left:'center',
                                    text:"粗标注过程信息",//主标题文本，'\n'指定换行
                                    textStyle:{
                                        fontSize:16
                                    }
                                },
                                xAxis:
                                {
                                    data: this.indexArr.slice(0, projection.length),
                                    type: 'category',
                                    axisLine: {onZero: true},
                                },
                                yAxis: 
                                {
                                    scale: 'true',
                                },
                                series: [
                                    {
                                        data: projection,
                                        name: "projection",
                                        type: 'line',
                                        lineStyle:{
                                            normal:{
                                                width:1,
                                            },
                                        },
                                        markLine: {
                                            symbol: 'none',
                                            silent: true,
                                            data: [
                                            ],
                                        },
                                        symbol: 'none',
                                    },
                                    {
                                        data: entropy,
                                        name: "entropy",
                                        type: 'line',
                                        lineStyle:{
                                            normal:{
                                                width:1,
                                            },
                                        },
                                        markLine: {
                                            symbol: 'none',
                                            silent: true,
                                            data: [
                                            ],
                                        },
                                        symbol: 'none',
                                    },
                                    {
                                        data: entropy_diff,
                                        name: "entropy_diff",
                                        type: 'line',
                                        lineStyle:{
                                            normal:{
                                                width:1,
                                            },
                                        },
                                        markLine: {
                                            symbol: 'none',
                                            silent: true,
                                            data: [
                                            ],
                                        },
                                        symbol: 'none',
                                    },
                                ],
                                dataZoom: [
                                    {
                                        type: 'inside',
                                        realtime: true,
                                    }
                                ],
                                grid:
                                {
                                    left:'5%',
                                    right:'5%',
                                    top:'6%',
                                    height:'75%',
                                    containLabel: true,
                                },
                                toolbox: {
                                    feature: {
                                        dataZoom: {
                                            yAxisIndex: 'none'
                                        },
                                        restore: {},
                                        saveAsImage: {}
                                    }
                                },
                                axisPointer: {
                                    link: {xAxisIndex: 'all'}
                                },
                                tooltip: {
                                    trigger: 'axis',
                                    axisPointer: {
                                        animation: false
                                    }
                                },
                                legend: {
                                    show: true,
                                    x:"left",
                                    y:"bottom",
                                    orient:'horizontal',
                                    textStyle:{
                                    }
                                },
                            }
                            for(let series of chartOption.series){
                                for(let start_pos of info_rough.start_pos){
                                    series.markLine.data.push({
                                        "xAxis":start_pos,
                                        "lineStyle": {
                                            "show": true,
                                            "color": '#0000ff',
                                            "type": 'solid',
                                            "width":1,
                                        },
                                    });
                                }
                                for(let end_pos of info_rough.stop_pos){
                                    series.markLine.data.push({
                                        "xAxis":end_pos,
                                        "lineStyle": {
                                            "show": true,
                                            "color": '#ff0000',
                                            "type": 'solid',
                                            "width":1,
                                        },
                                    });
                                }
                                series.markLine.data.push({
                                    "yAxis":info_rough.projection_thr_easing,
                                    "lineStyle": {
                                        "show": true,
                                        "color": '#0000ff',
                                        "type": 'solid',
                                        "width":0.5,
                                    },
                                });
                                series.markLine.data.push({
                                    "yAxis":info_rough.projection_thr_strict,
                                    "lineStyle": {
                                        "show": true,
                                        "color": '#ff0000',
                                        "type": 'solid',
                                        "width":0.5,
                                    },
                                });
                                series.markLine.data.push({
                                    "yAxis":info_rough.entropy_thr,
                                    "lineStyle": {
                                        "show": true,
                                        "color": '#ff00ff',
                                        "type": 'solid',
                                        "width":0.5,
                                    },
                                });
                            }
                            console.log(chartOption);
                            this.$store.commit("setRecommenttip_option",chartOption);

                        }else{
                            this.msg = "粗标注出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ); 
        },
        /*增加多边形*/
        add_labeling_polygon(image_id, points, fea_points, gFeatureLayer, gFetureStyle){
            const time = new Date().getTime();
            let fea = this.add_polygon_disp(gFeatureLayer,gFetureStyle, fea_points, time, time);
            let pointsStr=JSON.stringify(points);
            this.axios.get('ocr/addLabelingPolygon/?image_id='+image_id+"&points="+pointsStr).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let info_polygon = response.data.body;
                            fea.id=info_polygon.polygonAdd.polygon_id+"";
                            fea.data.create_user_id=info_polygon.polygonAdd.create_user_id;
                            //在polygon_dict中增加元素
                            this.polygonList[fea.id]=info_polygon.polygonAdd;

                            for(let polygon_id in info_polygon.delete_info){
                                //delete feature related
                                gFeatureLayer.getFeatureById(polygon_id+"");
                                gFeatureLayer.removeFeatureById(polygon_id+"");
                                //在polygon_dict中移除元素
                                delete this.polygonList.polygon_id;
                            }

                        }else{
                            this.msg = "添加多边形出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ); 
        },
        /*删除多边形*/
        delete_polygon_by_id(polygon_id, gFeatureLayer, gMap){
            this.axios.get('ocr/deletePolygonById/?polygon_id='+polygon_id).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            gFeatureLayer.removeFeatureById(polygon_id+"");
                            gMap.mLayer.removeAllMarkers();
                        }else{
                            this.msg = "删除多边形出错,原因:"+response.data.tip;
                            console.log(this.msg);
                        }
                    }   
                }
            ); 
        },
        add_polygon_disp(gFeatureLayer,gFetureStyle,points, polygon_id, create_user_id){
            // 元素添加展示
            let fea = new gDBox.Feature.Polygon(
                    polygon_id+"",
                    points,
                    {
                        create_user_id: create_user_id
                    },
                    gFetureStyle
                );
            gFeatureLayer.addFeature(fea);
            return fea;
        },
        initMap(image_id, tar_width, tar_height, ori_width, ori_height, zoom_scale, center_x, center_y){
            const gFetureStyle = new gDBox.Style({strokeColor: '#0000FF', lineWeight: 1});
            // js声明-容器声明（参数：zoom: 缩放比; {cx: cy:}：初始中心点位置；zoomMax、zoomMin：缩放的比例限制）
            this.gMap = new gDBox.Map('imagebox', {w: tar_width , zoom: zoom_scale*tar_width, cx: center_x*tar_width, cy: center_y*tar_height, zoomMax: tar_width * 10, zoomMin: tar_width / 10, autoFeatureSelect: true});
            this.gdboxConfigure = new GdboxConfigure(this.username, this.gMap);
            this.gMap.setMode('drawRect', gFetureStyle);
            // 图片层实例\添加
            const gImageLayer = new gDBox.Layer.Image('img', "ocr/getImage/?image_id="+image_id+"&tar_width="+tar_width+"&tar_height="+tar_height+"&time="+new Date().getTime(), {w: tar_width, h: tar_height}, {zIndex: 1});
            this.gMap.addLayer(gImageLayer);
            this.gMap.events.on('geometryDrawDone', (type, points) => {
                let select_points = this.gdbox2img_map(points, tar_width, tar_height,ori_width,ori_height);
                let rotate_points = this.rotate_polygon(select_points, -1*this.current_rotate, ori_width, ori_height);
                switch(this.toolmode){
                    case "manual":
                    {
                        this.add_labeling_polygon(image_id, rotate_points, points, this.gdboxConfigure.get_layer(this.username),this.gdboxConfigure.get_style(this.username, false));
                        break;
                    }
                    case "recomment":
                    {
                        this.rough_labeling(image_id, rotate_points, this.gdboxConfigure.get_layer(this.username), this.gdboxConfigure.get_style(this.username, false));
                        break;
                    }
                    case "delete":
                    {
                        this.region_delete(image_id, rotate_points, this.gdboxConfigure.get_layer(this.username));
                        break;
                    }
                    case "merge":
                    {
                        this.merge_labeling(image_id, rotate_points, this.gdboxConfigure.get_layer(this.username), this.gdboxConfigure.get_style(this.username, false));
                        break;
                    }

                    default:
                        alert("labeling_mode err!");
                }

            });
            this.gMap.events.on('geometryEditDone', (type, activeFeature, points) => {
                activeFeature.update({points});
                activeFeature.show();
            });
            this.gMap.events.on('geometryEditing', (type, feature, points) => {
                if (!this.gMap.mLayer) return;
                const marker = this.gMap.mLayer.getMarkerById(`marker-${feature.id}`);
                if (!marker) return;
                const bounds = gDBox.Util.getBounds(points);
                const leftTopPoint = bounds[0]; // 边界坐上角坐标
                marker.update({x: leftTopPoint.x, y: leftTopPoint.y});
            });
            this.gMap.events.on('featureSelected', (feature) => {
                let cFeature = feature;
                // 删除按钮添加
                const featureBounds = cFeature.getBounds();
                const leftTopPoint = featureBounds[0]; // 边界坐上角坐标
                let deleteMarker = new gDBox.Marker(`marker-${cFeature.id}`,
                    {
                        src: "/delete.png",
                        x: leftTopPoint.x,
                        y: leftTopPoint.y,
                        offset: {
                            x: 0,
                            y: 0
                        },
                        featureId: cFeature.id
                    }
                );
                this.gMap.mLayer.addMarker(deleteMarker);
                deleteMarker.regEvent('click',() => {
                    // 执行选中元素删除
                    this.delete_polygon_by_id(cFeature.id, this.gdboxConfigure.get_layer(this.username), this.gMap);
                });
            });
            this.gMap.events.on('featureStatusReset', () => {
                this.gMap.mLayer.removeAllMarkers();
            });
            window.onresize = function () {
                this.gMap && this.gMap.resize();
            };

            for(let user_polygon in this.polygonList){
                let layer = this.gdboxConfigure.get_layer(user_polygon);
                for(let polygon in this.polygonList[user_polygon]){
                    let elem = this.polygonList[user_polygon][polygon];
                    let polygon_points = JSON.parse(elem['points']);
                    let polygon_id = elem['polygon_id'];
                    let has_content = elem['labeling_content'];
                    let style = this.gdboxConfigure.get_style(user_polygon, has_content);
                    //rotate the label
                    let polygon_rotated = this.rotate_polygon(polygon_points,this.current_rotate,ori_width,ori_height);
                    //map it into feature layer
                    let polygon_map = this.img2gdbox_map(polygon_rotated, tar_width,tar_height,ori_width,ori_height);
                    this.add_polygon_disp(layer, style, polygon_map, polygon_id, user_polygon);
                }

            }


        },
        // 获取image信息，然后调整box大小
        adjustbox(){
            this.axios.get('ocr/getImageinfo/?currentframe='+this.currentframe+"&docid="+this.docid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let imageinfo = response.data.body;
                            if(this.gMap!=null){
                                this.clearMap();
                            }
                            this.username=imageinfo.username;
                            this.current_rotate=imageinfo.current_rotate;
                            this.polygonList = JSON.parse(imageinfo.polygon_dict);
                            this.ori_height=imageinfo.ori_height;
                            this.ori_width=imageinfo.ori_width;
                            let tar_size= this.cal_size(this.divwidthmax, this.divheightmax, imageinfo.ori_width, imageinfo.ori_height, imageinfo.is_vertical);
                            //只修改宽度, 牵涉父组件，这里只发送消息
                            this.$emit('adjustDiv',Math.min(tar_size.width,this.divwidthmax));
                            this.initMap(imageinfo.image_id, tar_size.width, tar_size.height, imageinfo.ori_width, imageinfo.ori_height, imageinfo.zoom_scale, imageinfo.center_x, imageinfo.center_y);
                            this.tar_width = tar_size.width;
                            this.tar_height = tar_size.height;
                        }else{
                            this.msg = "获取image信息出错,原因:"+response.data.tip;
                        }
                    }   
                }
            ) 
        },
    },
    
    watch: {
        currentframe:{
            handler:function(value){
                console.log(value);
                this.adjustbox();
            },
        }, 
        labelmode:{
            handler:function(value){
                const gFetureStyle = new gDBox.Style({strokeColor: '#0000FF', lineWeight: 1});
                if(value=="draw"){
                    this.gMap.setMode("drawRect",gFetureStyle);
                }else{
                    this.gMap.setMode("pan",gFetureStyle);
                }
            },
        },
        toolmode:{
            handler:function(value){
                console.log(value);
            },
            immediate: true,
        },
    },
};
</script>

<style scoped>
#imagebox{
    top:0rem;
    position:relative;
    width:100%;
    height:100%;
}
</style>
