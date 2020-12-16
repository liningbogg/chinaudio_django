<template>
    <div id="polygonbox">
    </div>
</template>
<script>
import gDBox from "@/lib/gDBox.pkg.min.js"

export default {
	name: "Polygonadjust",
    props: ['polygonid'],
    data() {
        return {
        }
    },
    mounted() {
        this.updatebox();
    },
    computed: {
        contentlabelingmode:function(){
            return this.$store.getters.getContentlabelingmode;
        },
    },
    beforeDestroy() {
    },
    methods: {
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
        alter_polygon_by_id(points){
            let image_points = this.gdbox2img_map(points, this.tar_width, this.tar_height, this.ori_width, this.ori_height);
            image_points[0]['x'] += this.shiftx;
            image_points[1]['x'] += this.shiftx;
            image_points[2]['x'] += this.shiftx;
            image_points[3]['x'] += this.shiftx;
            image_points[0]['y'] += this.shifty;
            image_points[1]['y'] += this.shifty;
            image_points[2]['y'] += this.shifty;
            image_points[3]['y'] += this.shifty;
            let rotate_points = this.rotate_polygon(image_points, -1.0*this.current_rotate, this.image_width, this.image_height);
            let rotate_points_str = JSON.stringify(rotate_points);
            this.axios.get('ocr/alterPolygonById/?polygonid='+this.polygonid+'&points='+rotate_points_str).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            console.log(response.data.body);
                        }else{
                            this.msg = "更改多边形出错,原因:"+response.data.tip;
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
            console.log(gFeatureLayer);
            gFeatureLayer.addFeature(fea);
            return fea;
        },

        initMap(){
            const gFetureStyle = new gDBox.Style({strokeColor: '#0000FF', lineWeight: 1});
            // js声明-容器声明（参数：zoom: 缩放比; {cx: cy:}：初始中心点位置；zoomMax、zoomMin：缩放的比例限制）
            this.gMap = new gDBox.Map('polygonbox', {w: this.tar_width , zoom:this.tar_width, cx: 0, cy: 0, zoomMax: this.tar_width * 10, zoomMin: this.tar_width / 10, autoFeatureSelect: true});
            //this.gdboxConfigure = new GdboxConfigure(this.username, this.gMap);
            this.gMap.setMode('drawRect', gFetureStyle);
            // 图片层实例\添加
            const gImageLayer = new gDBox.Layer.Image('img', "ocr/getPolygonImage/?polygonid="+this.polygonid+"&tar_width="+this.tar_width+"&tar_height="+this.tar_height+"&is_extend=true&time="+new Date().getTime(), {w: this.tar_width, h: this.tar_height}, {zIndex: 1});
            this.gMap.addLayer(gImageLayer);
            let relative_points = [
                {'x':this.relative_box[0], 'y':this.relative_box[1]},
                {'x':this.relative_box[2], 'y':this.relative_box[1]},
                {'x':this.relative_box[2], 'y':this.relative_box[3]},
                {'x':this.relative_box[0], 'y':this.relative_box[3]},
            ];
            let polygon_map = this.img2gdbox_map(relative_points, this.tar_width, this.tar_height, this.ori_width, this.ori_height);
            console.log(polygon_map);
            // 标注容器
            let feature_layer = new gDBox.Layer.Feature(this.polygonid, {zIndex: 2, transparent: true});
            this.gMap.addLayer(feature_layer);
            let style_modify = new gDBox.Style({strokeColor: "#0000ff", lineWeight: 1});  // 未标记样式
            let style_modify_done = new gDBox.Style({strokeColor: "#00ff00", lineWeight: 1});  // 已经标记样式
            let style_elem = new gDBox.Style({strokeColor: "#ff0000", lineWeight: 1});  // 偏旁部首配置样式
            if(this.isDone){
                this.fea_modify = this.add_polygon_disp(feature_layer, style_modify_done, polygon_map, this.polygonid, "modify");
            }else{
                this.fea_modify = this.add_polygon_disp(feature_layer, style_modify, polygon_map, this.polygonid, "modify");
            }
            this.fea_elem = this.add_polygon_disp(feature_layer, style_elem, polygon_map, this.polygonid, "elem");
            if(this.contentlabelingmode == "labeling"){
                this.fea_modify.show()
                this.fea_elem.hide()
            }else{
                this.fea_modify.hide()
                this.fea_elem.show()
            }
            this.gMap.events.on('geometryEditDone', (type, feature, points) => {
                feature.update({points});
                feature.show();
                if(feature.data.create_user_id=="modify"){
                    this.alter_polygon_by_id(points);
                }
                if(feature.data.create_user_id=="elem"){
                }
            });

            /*this.gMap.events.on('geometryEditing', (type, feature, points) => {
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
            });*/
            this.gMap.events.on('featureStatusReset', () => {
                this.gMap.mLayer.removeAllMarkers();
            });
            window.onresize = function () {
                this.gMap && this.gMap.resize();
            };

        },
        // 获取image信息，然后调整box大小
        updatebox(){
            if(this.polygonid==null){
                return;
            }
            let div_img=document.getElementById("polygonbox");
            this.tar_width=div_img.offsetWidth;
            this.tar_height=div_img.offsetHeight;
            this.axios.get('ocr/getPolygonImageInfo/?polygonid='+this.polygonid).then(
                response => {
                    if(response){
                        if(response.data.status==="success"){
                            let imageinfo = response.data.body;
                            if(this.gMap!=null){
                                this.clearMap();
                            }
                            this.username = imageinfo.username;
                            this.current_rotate=imageinfo.current_rotate;
                            this.relative_box = imageinfo.relative_box;
                            this.ori_height=imageinfo.ori_height;
                            this.ori_width=imageinfo.ori_width;
                            this.image_height = imageinfo.image_height;
                            this.image_width = imageinfo.image_width;
                            this.shiftx = imageinfo.shiftx;
                            this.shifty = imageinfo.shifty;
                            this.shiftxWithPadding = imageinfo.shiftxWithPadding;
                            this.shiftyWithPadding = imageinfo.shiftyWithPadding;
                            this.isDone = imageinfo.isDone;
                            this.initMap();
                        }else{
                            this.msg = "获取polygon image信息出错,原因:"+response.data.tip;
                        }
                    }   
                }
            ) 
        },
    },
    
    watch: {
        polygonid:{
            handler:function(value){
                console.log(value);
                if(value){
                    this.updatebox();
                }
            },
        }, 
        contentlabelingmode:{
            handler:function(value){
                if(value!="labeling"){
                    if(this.fea_modify && this.fea_elem){
                        this.fea_modify.hide();
                        this.fea_elem.show();
                    }
                }
                if(value!="configure"){
                    if(this.fea_elem && this.fea_modify){
                        this.fea_elem.hide();
                        this.fea_modify.show();
                    }
                }
            },
        }, 
        
    },
};
</script>

<style scoped>
#polygonbox{
    top:0rem;
    position:relative;
    width:100%;
    height:100%;
}
</style>
