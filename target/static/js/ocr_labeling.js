var indexArr=new Array(100000);
for(var i=0;i<99999;i++){
    indexArr[i]=i;
}
//曲线颜色列表
const color_chart=["red","blue","black","green","yellow","gray"];

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
function cal_size(w_box,h_box,w,h){
    if ((w-h)*(w_box-h_box)<0){
        var t;
        t=w_box;
        w_box=h_box;
        h_box=t;
    }
    f1 = 1.0*w_box/w ;
    f2 = 1.0*h_box/h;
    factor = Math.min(f1, f2);
    // use best down-sizing filter
    width = Math.round(w*factor);
    height = Math.round(h*factor);
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
            let id = info_polygon["polygon_id"];
            let create_user_id = info_polygon["polygon_create_user_id"];
            fea.id=id;
            fea.data.create_user_id=create_user_id;
            console.log(fea);
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

/*delete all labeles related to a region */
function delete_region(image_id, select_points, gFeatureLayer){    
    var xhr = new XMLHttpRequest();
    select_points_str = JSON.stringify(select_points);
    xhr.open('GET', 'delete_region/?'+"image_id="+image_id+"&select_points="+select_points_str, true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                alert("删除过程出错,网页刷新");
                location.reload();
            }else{
                let delete_info = JSON.parse(context);
                let length_delete = delete_info.length;
                for(index=0;index<length_delete;++index){
                    let polygon_id = delete_info[index]['polygon_id'];
                    //delete feature related
                    gFeatureLayer.removeFeatureById(polygon_id);
                }
            }
        }
    };
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
                alert("旋转角度设置错误");
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

/*labeling roughly*/
function rough_labeling(image_id, rotate_points){
    let xhr = new XMLHttpRequest();
    rotate_points_str = JSON.stringify(rotate_points);
    console.log(rotate_points)
    xhr.open('GET', 'rough_labeling/?'+"image_id="+image_id+"&rotate_points_str="+rotate_points_str, true);
    xhr.send(null)
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200) {
            let context = xhr.response;
            if(context == "err"){
                alert("粗标注错误");
            }else{
                let rough_labeling_info = JSON.parse(context);
                var projectionChartDictSeries={
                    "projection":{"list":rough_labeling_info.projection,"visible":true},
                    "entropy":{"list":rough_labeling_info.entropy,"visible":true}
                };
                projectionChartDictLine=[];
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

                console.log(rough_labeling_info);
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

            }
        }
    }
}
