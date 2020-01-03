var indexArr=new Array(100000);
for(var i=0;i<99999;i++){
    indexArr[i]=i;
}
//曲线颜色列表
const color_chart=["red","blue","black","green","yellow","gray"];

/*操作反馈信息*/
function add_log(log_message, message_type){
    switch(message_type){
        case "message":
            tip = document.getElementById("page_image_tool_tip");
            tip.innerHTML="<font color=\"green\">m:"+log_message+"<br></font>"+tip.innerHTML;
            break;
        case "err":
            tip = document.getElementById("page_image_tool_tip");
            tip.innerHTML="<font color=\"red\">e:"+log_message+"<br></font>"+tip.innerHTML;
            break;
        case "warning":
            tip = document.getElementById("page_image_tool_tip");
            tip.innerHTML="<font color=\"blue\">w:"+log_message+"<br></font>"+tip.innerHTML;
            break;
        default:
            break
    }
}

/*跳转指定页*/
function move_page(ocr_pdf, page_apointed){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', './move_page/?ocr_pdf='+ocr_pdf+"&page_apointed="+page_apointed, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                if(context=="ok"){
                    location.reload();
                }else{
                    alert(context);
                }
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}

/*向后翻页*/
function move2next(ocr_pdf, frame_id, frame_num){
    page_apointed = frame_id+1;
    if(page_apointed<frame_num){
       move_page(ocr_pdf,page_apointed); 
    }
}

/*向前翻页*/
function move2prior(ocr_pdf, frame_id, frame_num){
    page_apointed = frame_id-1;
    if(page_apointed>-1){
       move_page(ocr_pdf,page_apointed); 
    }
}

/*跳转*/
function jump_page(ocr_pdf,frame_num){
    page_apointed = document.getElementById("input_page_id").value;
    if(page_apointed>-1 && page_apointed<frame_num){
        move_page(ocr_pdf,page_apointed);
    }
}

/*gdbox-图像矩阵坐标映射*/
function gdbox2img_map(points, width, height,width_ori,height_ori){
    var points_img=new Array();
    for(var point of points){
        mapx=Math.round((width/2.0 + point["x"])*width_ori/width);
        mapy=Math.round((height/2.0 - point["y"])*height_ori/height);
        points_img.push({"x":mapx,"y":mapy});
    }
    return points_img;
}

/*gdbox-矩阵图像坐标映射*/
function img2gdbox_map(points, width, height,width_ori,height_ori){
    var points_img=new Array();
    for(var point of points){
        mapx=Math.round(-width/2.0 + point["x"]*1.0*width/width_ori);
        mapy=Math.round(height/2.0 - point["y"]*1.0*height/height_ori);
        points_img.push({"x":mapx,"y":mapy});
    }
    return points_img;
}

/*计算图片大小*/
function cal_size(w_box,h_box,w,h,is_vertical){
    if(is_vertical ==true){
        height = h_box;
        width=Math.round(w*1.0/h*height);
    }else{
        width = w_box;
        height = Math.round(h*1.0/w*width);
    }
    return {"width":width,"height":height};
}

/*增加多边形*/
function add_labeling_polygon(image_id, points, fea_points, gFeatureLayer, gFetureStyle){
    const time = new Date().getTime(); 
    fea = add_polygon_disp(gFeatureLayer,gFetureStyle, fea_points, time, time);
    var xhr = new XMLHttpRequest();
    var pointsStr=JSON.stringify(points);
    xhr.open('GET', 'add_labeling_polygon/?'+"image_id="+image_id+"&points="+pointsStr, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            let info_polygon = JSON.parse(context);
            console.log(info_polygon);
            let id = info_polygon["polygon_id"];
            let create_user_id = info_polygon["polygon_create_user_id"];
            fea.id=id;
            fea.data.create_user_id=create_user_id;
            let length_delete = info_polygon.delete_info.length;
            for(index=0;index<length_delete;++index){
                let polygon_id = info_polygon.delete_info[index]['polygon_id'];
                //delete feature related
                gFeatureLayer.removeFeatureById(polygon_id);
            }
        }
    };
}

/*多边形显示*/
function add_polygon_disp(gFeatureLayer,gFetureStyle,points, polygon_id, create_user_id){
    // 元素添加展示
    let fea = new gDBox.Feature.Polygon(
            polygon_id,
            points,
            {
                create_user_id: create_user_id
            },
            gFetureStyle
        );
    gFeatureLayer.addFeature(fea);
    return fea;
}

/*删除用户下所有与页面相关的标注*/
function delete_all_polygon(image_id){
    var msg = "要删除整页标注？？\n\n请输入image_id以确认危险操作！";
    prompt_str = prompt(msg);
    if(!prompt_str){
        alert("删除操作已经取消");
        return;
    }
    if(prompt_str!=image_id){
        alert("整页删除失败,输入的image_id="+prompt_str);
        return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'delete_all_polygon/?'+"image_id="+image_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            if(context!="err"){
                alert(context+" 个标注框被删除.");
                location.reload();
            }else{
                alert(context);
            }
        }
    };
}

/*删除特定IP的标注框*/
function delete_polygon_by_id(polygon_id, gFeatureLayer, feature_id, gMap)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'delete_polygon_by_id/?'+"polygon_id="+polygon_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            if(context=="ok"){
                gFeatureLayer.removeFeatureById(feature_id);
                // 对应删除标注层中删除（x）icon
                gMap.mLayer.removeAllMarkers();
                let log_message="1个标注被删除,IP:"+polygon_id;
                add_log(log_message,"message");
            }else{
                let log_message=context;
                add_log(log_message,"warning");
            }

        }
    };

}

/*编辑特定IP的标注框*/
function alter_polygon_by_id(polygon_id, points, tar_width, tar_height, ori_width, ori_height, current_rotate){
    var xhr = new XMLHttpRequest();
    image_points = gdbox2img_map(points, tar_width, tar_height,ori_width,ori_height);
    rotate_points = rotate_polygon(image_points, -1*current_rotate, ori_width, ori_height);
    rotate_points_str = JSON.stringify(rotate_points);
    xhr.open('GET', 'alter_polygon_by_id/?'+"polygon_id="+polygon_id+"&points="+rotate_points_str, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            if(context=="ok"){
                let log_message="1个标注被修改,IP:"+polygon_id;
                add_log(log_message,"message");
            }else{
                add_log(context,"error");
            }

        }
    };
    
}

/*delete all labeles related to a region */
function delete_region(image_id, select_points, gFeatureLayer){    
    var xhr = new XMLHttpRequest();
    select_points_str = JSON.stringify(select_points);
    xhr.open('GET', 'delete_region/?'+"image_id="+image_id+"&rotate_points_str="+select_points_str, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                add_log("删除出错","error");
            }else{
                let delete_info = JSON.parse(context);
                let length_delete = delete_info.length;
                for(index=0;index<length_delete;++index){
                    let polygon_id = delete_info[index]['polygon_id'];
                    //delete feature related
                    gFeatureLayer.removeFeatureById(polygon_id);
                }
                let log_message=length_delete+"个标注被删除.";
                add_log(log_message,"message");
            }
        }
    };
}

/*设置gdbox模式*/
function set_gdbox_mode(mode,gFetureStyle){
    switch(mode){
        case "pan":
            var manual_select = document.getElementById("manual_select");
            manual_select.disabled=true;
            var recommend_select = document.getElementById("recommend_select");
            recommend_select.disabled=true;
            var merge_select = document.getElementById("merge_select");
            merge_select.disabled=true;
            var clear_select = document.getElementById("clear_select");
            clear_select.disabled=true;
            gMap.setMode("pan",gFetureStyle);
            add_log("pan模式","message");
            break;
        case "draw_rect":
            var manual_select = document.getElementById("manual_select");
            manual_select.disabled=false;
            var recommend_select = document.getElementById("recommend_select");
            recommend_select.disabled=false;
            var merge_select = document.getElementById("merge_select");
            merge_select.disabled=false;
            var clear_select = document.getElementById("clear_select");
            clear_select.disabled=false;
            gMap.setMode("drawRect",gFetureStyle);
            add_log("draw模式","message");
            break;
        default:
            alert("未知模式");
    }
}

/*rotate a polygon*/
function  rotate_polygon(polygon_points, current_rotate, width, height){
    let polygon_rotated = Array();
    for(point_index in polygon_points){
        point = polygon_points[point_index];
        x = point['x'];
        y = point['y'];
        x_shift = x-width/2.0;
        y_shift = y-height/2.0;
        rotate_rad = current_rotate/180.0*Math.PI;
        nx = x_shift*Math.cos(rotate_rad)+y_shift*Math.sin(rotate_rad)+width/2.0;
        ny = -x_shift*Math.sin(rotate_rad)+y_shift*Math.cos(rotate_rad)+height/2.0;
        polygon_rotated.push({'x':nx,'y':ny});
    }
    return polygon_rotated;
}

/*reset rotate degree*/
function rotate_degree_reset(image_id){
    let xhr = new XMLHttpRequest();
    let rotate_degree = document.getElementById("rotate_degree").value;
    xhr.open('GET', 'rotate_degree_reset/?'+"image_id="+image_id+"&rotate_degree="+rotate_degree, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                add_log("重设倾角失败","err");
            }else{
                location.reload();
            }
        }
    }
}


/*reset entropy threshold*/
function entropy_thr_reset(image_id){
    let xhr = new XMLHttpRequest();
    let entropy_thr = document.getElementById("entropy_thr").value;
    xhr.open('GET', 'entropy_thr_reset/?'+"image_id="+image_id+"&entropy_thr="+entropy_thr, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context != "ok"){
                alert(context);    
                location.reload();
            }else{

                location.reload();
            }
        }
    }
}

/*重设文字方向*/
function direction_select(direction, image_user_conf_id){
    let xhr = new XMLHttpRequest();
    xhr.open('GET', 'direction_select/?'+"direction="+direction+"&image_user_conf_id="+image_user_conf_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                location.reload();
            }else{
                location.reload();
            }
        }
    }
}


/*重设文字方向_pdf*/
function direction_pdf(ocr_pdf_id, is_vertical){
    let xhr = new XMLHttpRequest();
    xhr.open('GET', 'direction_pdf/?'+"ocr_pdf_id="+ocr_pdf_id+"&is_vertical="+is_vertical, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            console.log(context);
            if(context == "err"){
                location.reload();
            }else{
                location.reload();
            }
        }
    }
}
//添加曲线的高层封装,data字典中包含lengend 以及数据
function addChart(title, dictSeries, dictLine, currentPos, MyDiv,start, end, slope, bias){
    let xAxis_c = indexArr.slice(start,end)
    for (key in xAxis_c){
        xAxis_c[key]=xAxis_c[key]*slope+bias;
    }
    //曲线参数设置
    var  options = {
        chart: {
            type: 'line',
            zoomType: 'xy', //xy方向均可缩放
            marginLeft: 80, // Keep all charts left aligned
            marginRight: 80, // Keep all charts right aligned
            animation: false,
        },
        boost: {
            useGPUTranslations: true
        },
        title: {
            text: title
        },
        exporting: {
            enabled:false
        },
        xAxis: {
            categories: xAxis_c,

            tickInterval:10*slope
        },
        yAxis: {
            tickInterval: 0.05
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle',
            enabled: true
        },
    tooltip: {
            valueDecimals: 3,  //显示精度
            shared: true
        },
        plotOptions: {
            series: {
                marker: {
                    enabled: false
                },

            },
        },
    };
    options.series = new Array();
    var i=0;
    for(key in dictSeries){
        options.series[i] = new Object();
        options.series[i].visible = dictSeries[key]["visible"];
        options.series[i].color = color_chart[i];
        options.series[i].lineWidth = 1;
        options.series[i].name = key;
        options.series[i].data = dictSeries[key]["list"].slice(start,end);
        i++;
    }
    var chart = Highcharts.chart(MyDiv,options);
    i=0;
    for(key in dictLine){
        for(h in dictLine[key]){
             chart.xAxis[0].addPlotLine({           //在x轴上增加
                value:dictLine[key][h]-start,                           //在值为2的地方
                width:1, //标示线的宽度为2px
                color: color_chart[i]//标示线的颜色
            });
        }
        i++;
    }
    chart.xAxis[0].addPlotLine({           //在x轴上增加
        value:currentPos-start,                           //在值为2的地方
        width:2, //标示线的宽度为2px
        color: "green"//标示线的颜色
    });

}

/*labeling merge*/
function merge_labeling(image_id, rotate_points, gFeatureLayer, gFetureStyle, current_rotate, ori_width, ori_height, tar_width, tar_height){
    let xhr = new XMLHttpRequest();
    rotate_points_str = JSON.stringify(rotate_points);/*maping then rotated*/
    xhr.open('GET', 'merge_labeling/?'+"image_id="+image_id+"&rotate_points_str="+rotate_points_str, true);
    xhr.send(null)
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                alert("标注融合错误");
            }else{
                let merge_labeling_info = JSON.parse(context);
                if(merge_labeling_info.delete_info!=null){
                    let length_delete = merge_labeling_info.delete_info.length;
                    for(index=0;index<length_delete;++index){
                        let polygon_id = merge_labeling_info.delete_info[index]['polygon_id'];
                        //delete feature related
                        gFeatureLayer.removeFeatureById(polygon_id);
                    }
                }
                let polygon_add=merge_labeling_info.polygon_add;
                if(polygon_add==null){
                    let log_warning ="融合得到0个标注框。";
                    add_log(log_warning,"warning"); 
                }else{
                    // 显示新加标注框
                    let polygon_points = JSON.parse(polygon_add['points']);
                    let polygon_id = polygon_add['polygon_id'];
                    //rotate the label
                    let rotate=current_rotate;
                    let polygon_rotated = rotate_polygon(polygon_points,rotate,ori_width,ori_height);
                    //map it into feature layer
                    polygon_map = img2gdbox_map(polygon_rotated, tar_width,tar_height, ori_width, ori_height);
                    add_polygon_disp(gFeatureLayer, gFetureStyle, polygon_map, polygon_id, polygon_add['create_user_id']);
                    let log_message = "融合ID:"+polygon_id;
                    add_log(log_message,"message"); 

                }

            }
        }
    }
    
}


/*labeling roughly*/
function rough_labeling(image_id, rotate_points, gFeatureLayer, gFetureStyle, current_rotate, ori_width, ori_height, tar_width, tar_height){
    let xhr = new XMLHttpRequest();
    rotate_points_str = JSON.stringify(rotate_points);
    xhr.open('GET', 'rough_labeling/?'+"image_id="+image_id+"&rotate_points_str="+rotate_points_str, true);
    xhr.send(null)
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                let log_message="粗标注错误。";
                add_log(log_message,"err"); 
            }else{
                let rough_labeling_info = JSON.parse(context);
                let length_delete = rough_labeling_info.delete_info.length;
                for(index=0;index<length_delete;++index){
                    let polygon_id = rough_labeling_info.delete_info[index]['polygon_id'];
                    //delete feature related
                    gFeatureLayer.removeFeatureById(polygon_id);
                }

                var projectionChartDictSeries={
                    "projection":{"list":rough_labeling_info.projection,"visible":true},
                    "entropy":{"list":rough_labeling_info.entropy,"visible":true},
                    "entropy_diff":{"list":rough_labeling_info.entropy_diff,"visible":true}
                };
                projectionChartDictLine={
                    "start_pos":rough_labeling_info.start_pos,
                    "stop_pos":rough_labeling_info.stop_pos
                };
                addChart(
                    "",
                    projectionChartDictSeries,
                    projectionChartDictLine,
                    0,
                    "projection",
                    0,
                    projectionChartDictSeries["projection"]["list"].length,
                    1.0,
                    0
                );

                // 显示新加标注框
                let polygon_add = rough_labeling_info.polygon_add;
                for(polygon in polygon_add){
                    let elem = polygon_add[polygon];
                    let polygon_points = JSON.parse(elem['points']);
                    let polygon_id = elem['polygon_id'];
                    //rotate the label
                    let rotate=current_rotate;
                    polygon_rotated = rotate_polygon(polygon_points,rotate,ori_width,ori_height);
                    //map it into feature layer
                    polygon_map = img2gdbox_map(polygon_rotated, tar_width,tar_height, ori_width, ori_height);
                    add_polygon_disp(gFeatureLayer, gFetureStyle, polygon_map, polygon_id, elem['create_user_id']);
                }

                let log_message="完成粗标注，生成标注框"+polygon_add.length+"个。";
                add_log(log_message,"message"); 
            }
        }
    }
}

/*rotate degree evaluation*/
function rotate_degree_evaluate(image_id){
    let xhr = new XMLHttpRequest();
    xhr.open('GET', 'rotate_degree_evaluate/?'+"image_id="+image_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                alert("倾斜角度评估错误");
            }else{
                let evaluate_info = JSON.parse(context);
                let projection_entropy = evaluate_info["projection_entropy"];
                let slope = evaluate_info["slope"];
                let bias = evaluate_info["bias"];
                console.log(slope);
                console.log( bias);
                //draw chart
                var projectionEntropyChartDictSeries={
                    "projection_entropy":{"list":projection_entropy,"visible":true},
                };
                projectionEntropyChartDictLine=[];
                addChart(
                    "",
                    projectionEntropyChartDictSeries,
                    projectionEntropyChartDictLine,
                    0,
                    "projection",
                    0,
                    projectionEntropyChartDictSeries["projection_entropy"]["list"].length,
                    slope,
                    bias
                );
                add_log("倾斜评估完成","message");
            }
        }
    }
}
