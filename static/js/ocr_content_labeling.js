/*操作反馈信息*/
function add_log(log_message, message_type){
    switch(message_type){
        case "message":
            tip = document.getElementById("log");
            tip.innerHTML="<font color=\"green\">m:"+log_message+"<br></font>"+tip.innerHTML;
            break;
        case "err":
            tip = document.getElementById("log");
            tip.innerHTML="<font color=\"red\">e:"+log_message+"<br></font>"+tip.innerHTML;
            break;
        case "warning":
            tip = document.getElementById("log");
            tip.innerHTML="<font color=\"blue\">w:"+log_message+"<br></font>"+tip.innerHTML;
            break;
        default:
            break
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

function get_box_from_feature(points, tar_width, tar_height, ori_width, ori_height, x_shift, y_shift){
    let select_points = gdbox2img_map(points, tar_width, tar_height,ori_width,ori_height);
    var box=[select_points[0]['x']+x_shift, select_points[0]['y']+y_shift, select_points[2]['x']+x_shift, select_points[2]['y']+y_shift];
    console.log(box);
    return box;
}

function add_elem(image_id, degree_to_rotate, points, size, x_shift, y_shift){
    var desc = document.getElementById("elem_desc").value;
    box = get_box_from_feature(points, 512, 512, size, size, x_shift, y_shift);
    elem_box = JSON.stringify(box);

    console.log(elem_box);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'add_elem/?'+"image_id="+image_id+"&degree_to_rotate="+degree_to_rotate+"&elem_box="+elem_box+"&desc="+desc, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            if(context!="err"){
                result = JSON.parse(context);
                console.log(result);
                add_log("添加偏旁部首成功,id="+result.id,"message");
            }else{
                console.log(context);
                add_log("添加偏旁部首出错","err");
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


/*获得偏旁部首页面信息*/
function getElemPage_info(div_width, div_height, size){
    var image_width = Math.floor(div_width / size) * size;
    var image_height = Math.floor(div_height / size) * size;
    row = Math.floor(div_height / size);
    col = Math.floor(div_width / size);
    //xhr.open('GET', 'get_elem_page/?page_name='+page+"&row="row+"&col="+col, true);
    return {'row': row,'col': col};
}

/*获取偏旁部首页的id并且在image上显示矩形框*/
function achieve_elem_id(elem_fea_layer, elem_fea_style, page_index, row, col){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'achieve_elem_id/?'+"page_index="+page_index+"&row="+row+"&col="+col, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            var img_size = 64;
            if(context!="err"){
                id_set = JSON.parse(context);

                for(elem in id_set){
                    id = id_set[elem].id;
                    height = id_set[elem].height
                    width = id_set[elem].width
                    let col_index=elem % col;
                    let row_index=Math.floor(elem*1.0 / col);

                    let points=[{'x':col_index*img_size,'y':row_index*img_size},{'x':(col_index+1)*img_size-1,'y':row_index*img_size},
                    {'x':(col_index+1)*img_size-1,'y':(row_index+1)*img_size-1},{'x':col_index*img_size,'y':(row_index+1)*img_size-1}];
                    gdbox_points = img2gdbox_map(points, col*img_size, row*img_size, col*img_size, row*img_size);
                    let size={"height":height, "width":width};
                    size_str=JSON.stringify(size);
                    add_polygon_disp(elem_fea_layer, elem_fea_style, gdbox_points, id, size_str);
                }
                elem_fea_layer.renew();
                add_log("获取偏旁总览ID成功","message");
            }else{
                console.log(context);
                add_log("获取偏旁总览ID失败","err");
            }
            
        }
    };

}

/*删除特定id的elem*/
function delete_elem_by_id(id, gMap_elem_total, elem_fea_layer, elem_fea_style, gImageLayer_elem_total, row, col){
    gMap_elem_total.mLayer.removeAllMarkers();
    elem_fea_layer.removeAllFeatures();
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'delete_elem_by_id/?elem_id='+id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            if(context!="err"){
                // 删除的关联的标注关系
                delete_info = JSON.parse(context);
                characterelem_delete_num = delete_info.characterelem_delete_num;
                polygonelem_delete_num = delete_info.polygonelem_delete_num;
                add_log("删除偏旁总览ID成功","message");
                add_log("删除偏旁对应标注数目:"+polygonelem_delete_num,"message");
                add_log("删除偏旁对应汉字数目:"+characterelem_delete_num,"message");

                //gMap_elem_total.removeLayer(gImageLayer_elem_total);
                for(gImageLayer_key in gMap_elem_total.oLayers){
                    let gImageLayer = gMap_elem_total.oLayers[gImageLayer_key];
                    if(gImageLayer.id=="img_elem_total"){
                        gMap_elem_total.removeLayer(gImageLayer);
                        break;
                    }
                }
                gImageLayer_elem_total = new gDBox.Layer.Image('img_elem_total', "/ocr/content_labeling/get_elem_page/?page_index=0&row="+row+"&col="+col+"&date="+ (new Date()), {w: col*64, h: row*64}, {zIndex: 1});
                gMap_elem_total.addLayer(gImageLayer_elem_total);
                achieve_elem_id(elem_fea_layer, elem_fea_style, 0, row, col);
            }else{
                console.log(context);
                add_log("删除偏旁总览ID失败","err");
            }
            
        }
    };

}
