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
    return {'row': row,'col': col};
}

/*获取偏旁部首页的id并且在image上显示矩形框*/
function achieve_elem_id(elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected, page_index, row, col){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'achieve_elem_id/?'+"page_index="+page_index+"&row="+row+"&col="+col, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            let fea_style_str = JSON.stringify(elem_fea_style);
            let fea_style_str_selected = JSON.stringify(elem_fea_style_selected);

            console.log(elem_selected);
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
                    if(elem_selected.has(id)){
                        let fea_style = JSON.parse(fea_style_str_selected);
                        add_polygon_disp(elem_fea_layer, fea_style, gdbox_points, id, size_str);
                    }else{
                        let fea_style = JSON.parse(fea_style_str);
                        add_polygon_disp(elem_fea_layer, fea_style, gdbox_points, id, size_str);
                    }
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
function delete_elem_by_id(id, gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected, gImageLayer_elem_total, row, col){
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
                achieve_elem_id(elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected, 0, row, col);
            }else{
                console.log(context);
                add_log("删除偏旁总览ID失败","err");
            }
         
        }
    };

}
/*获取指定偏旁部首对应的汉字集合*/
function getCharacterListFromElem(elem_id){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'achieve_characters_from_elem/?elem_id='+elem_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            if(context!="err"){
                document.getElementById("character_operator_info").innerHTML="关联字符集合:"+context;
                add_log("获取偏旁对应汉字集合成功", "message");
            }else{
                add_log("获取偏旁对应字符失败","err");
            }
            
        }
    };
    
}
// 获取已经选择的偏旁图片
function achieveElemSelected(elem_selected, gMap_elem_selected, elem_selected_fea_layer, elem_selected_fea_style, width){
    var elem_selected_str = JSON.stringify(elem_selected);
    console.log(elem_selected_str);
    gMap_elem_selected.mLayer.removeAllMarkers();
    elem_selected_fea_layer.removeAllFeatures();
    for(gImageLayer_key in gMap_elem_selected.oLayers){
        let gImageLayer = gMap_elem_selected.oLayers[gImageLayer_key];
        if(gImageLayer.id=="img_elem_selected"){
            gMap_elem_selected.removeLayer(gImageLayer);
            break;
        }
    }
    gImageLayer_elem_selected = new gDBox.Layer.Image('img_elem_selected', "/ocr/content_labeling/get_elem_selected/?elem_selected_str="+elem_selected_str+"&width="+width, {w: width, h: 64}, {zIndex: 1});
    gMap_elem_selected.addLayer(gImageLayer_elem_selected);
    gMap_elem_selected.mLayer.removeAllMarkers();
    elem_selected_fea_layer.removeAllFeatures();
    var index=0;
    for(elem in elem_selected){
        let elem_id = elem_selected[elem];
        let points=[{'x':index*64,'y':0},{'x':(index+1)*64-1,'y':0},{'x':(index+1)*64-1,'y':64-1},{'x':index*64,'y':64-1}];
        console.log(points);
        let gdbox_points = img2gdbox_map(points, width, 64, width, 64);
        console.log(gdbox_points);
        add_polygon_disp(elem_selected_fea_layer, elem_selected_fea_style, gdbox_points, elem_id, "elem_selected");
        index++;
    }


    //achieve_elem_id(elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected, 0, row, col);
}

function add_elem(image_id, degree_to_rotate, points, size, x_shift, y_shift, gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected){
    var desc = document.getElementById("elem_desc").value;
    box = get_box_from_feature(points, 512, 512, size, size, x_shift, y_shift);
    elem_box = JSON.stringify(box);
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
                gMap_elem_total.mLayer.removeAllMarkers();
                elem_fea_layer.removeAllFeatures();
                for(gImageLayer_key in gMap_elem_total.oLayers){
                    let gImageLayer = gMap_elem_total.oLayers[gImageLayer_key];
                    if(gImageLayer.id=="img_elem_total"){
                        gMap_elem_total.removeLayer(gImageLayer);
                        break;
                    }
                }
                gImageLayer_elem_total = new gDBox.Layer.Image('img_elem_total', "/ocr/content_labeling/get_elem_page/?page_index=0&row="+row+"&col="+col+"&date="+ (new Date()), {w: col*64, h: row*64}, {zIndex: 1});
                gMap_elem_total.addLayer(gImageLayer_elem_total);
                achieve_elem_id(elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected, 0, row, col);
            }else{
                console.log(context);
                add_log("添加偏旁部首出错","err");
            }
            
        }
    };

}

function add_character(elem_id){
    var desc = document.getElementById("character_desc").value;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'add_character/?elem_id='+elem_id+"&desc="+desc, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context!="err"){
                add_log("添加汉字偏旁部首关系成功:"+context,"message");
                getCharacterListFromElem(elem_id);

            }else{
                console.log(context);
                add_log("添加汉字偏旁部首关系出错","err");
            }
        }
    };

}

function delete_character(elem_id){
    var desc = document.getElementById("character_delete").value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'delete_character/?elem_id='+elem_id+"&desc="+desc, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context!="err"){
                add_log("删除汉字偏旁部首关系成功:"+context,"message");
                getCharacterListFromElem(elem_id);

            }else{
                console.log(context);
                add_log("删除汉字偏旁部首关系出错","err");
            }
        }
    };

}

function character_assist_check(gMap_elem_assist, elem_assist_fea_layer, elem_assist_fea_style, elem_assist_fea_style_selected, elem_selected){
    let text_input = document.getElementById("assist_text_input").value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'character_assist_check/?character='+text_input, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            let elem_assist_fea_style_str = JSON.stringify(elem_assist_fea_style);
            let elem_assist_fea_style_str_selected = JSON.stringify(elem_assist_fea_style_selected);
            if(context!="err"){
                add_log("获取偏旁部首提示:"+context,"message");
                elem_assist = JSON.parse(context)
                gMap_elem_assist.mLayer.removeAllMarkers();
                elem_assist_fea_layer.removeAllFeatures();
                for(gImageLayer_key in gMap_elem_assist.oLayers){
                    let gImageLayer = gMap_elem_assist.oLayers[gImageLayer_key];
                    if(gImageLayer.id=="img_elem_assist"){
                        gMap_elem_assist.removeLayer(gImageLayer);
                        break;
                    }
                }
                let elem_selected_str = context;
                let width = document.getElementById("assist_image_disp").offsetWidth;
                gImageLayer_elem_assist = new gDBox.Layer.Image('img_elem_assist', "/ocr/content_labeling/get_elem_selected/?elem_selected_str="+elem_selected_str+"&width="+width, {w: width, h: 64}, {zIndex: 1});
                gMap_elem_assist.addLayer(gImageLayer_elem_assist);
                var index=0;
                for(elem in elem_assist){
                    let elem_id = elem_assist[elem];
                    let points=[{'x':index*64,'y':0},{'x':(index+1)*64-1,'y':0},{'x':(index+1)*64-1,'y':64-1},{'x':index*64,'y':64-1}];
                    let gdbox_points = img2gdbox_map(points, width, 64, width, 64);

                    if(elem_selected.has(elem_id)){
                        add_polygon_disp(elem_assist_fea_layer, JSON.parse(elem_assist_fea_style_str_selected), gdbox_points, elem_id, "elem_assist");
                    }else{
                        add_polygon_disp(elem_assist_fea_layer, JSON.parse(elem_assist_fea_style_str), gdbox_points, elem_id, "elem_assist"); }
                    index++;
                }

            }else{
                add_log("获取偏旁部首提示关系出错","err");
            }
        }
    }
}

function elem_selected_add(elem_id, polygon_id){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'elem_selected_add/?polygon_id='+polygon_id+"&elem_id="+elem_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context == "ok"){
                add_log("标注添加成功:"+elem_id,"message");
            }else{
                add_log(context,"err");
            }
        }
    }
    
}


function elem_selected_delete(elem_id, polygon_id){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'elem_selected_delete/?polygon_id='+polygon_id+"&elem_id="+elem_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context == "ok"){
                add_log("标注删除成功:"+elem_id,"message");
            }else{
                add_log(context,"err");
            }
        }
    }
    
}

/*更新偏旁总览页数信息*/
function update_elem_page_info(){
   var xhr = new XMLHttpRequest();
   xhr.open('GET', 'get_elem_number', true);
   xhr.send(null);
   xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context == "err"){
                add_log("获取用户偏旁数目失败","err");
            }else{
                add_log("获取用户偏旁数目:"+context, "message");
                let elem_number = Number(context);
                let elem_page_info_input = document.getElementById("elem_page_info");
                let elem_div = document.getElementById("elem_total");
                let elem_width = elem_div.offsetWidth;
                let elem_height = elem_div.offsetHeight;
                let elem_row_col = getElemPage_info(elem_width, elem_height, 64);
                let elem_num_per_page = elem_row_col.row * elem_row_col.col;
                let page_num = 1 + Math.floor((elem_number-1) / elem_num_per_page) ;
                elem_page_info_input.value = "偏旁数目:"+elem_number+", 页数:"+page_num;

            }
        }
   }
}

/*设置当前偏旁页*/
function set_elem_page(gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'get_elem_number', true);
    xhr.send(null);
    xhr.onreadystatechange = function(){
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context == "err"){
                add_log("获取用户偏旁数目失败","err");
            }else{
                add_log("获取用户偏旁数目:"+context, "message");
                let elem_number = Number(context);
                let elem_page_info_input = document.getElementById("elem_page_info");
                let elem_div = document.getElementById("elem_total");
                let elem_width = elem_div.offsetWidth;
                let elem_height = elem_div.offsetHeight;
                let elem_row_col = getElemPage_info(elem_width, elem_height, 64);
                let elem_num_per_page = elem_row_col.row * elem_row_col.col;
                let page_num = 1 + Math.floor((elem_number-1) / elem_num_per_page) ;
                elem_page_info_input.value = "偏旁数目:"+elem_number+", 页数:"+page_num;
                let div_cur_page = document.getElementById("elem_current");
                let page_appointed = div_cur_page.value;
                if(page_appointed<0){
                    page_appointed=0;
                    div_cur_page.value = page_appointed;
                }
                if(page_appointed>=page_num){
                    page_appointed = page_num -1;
                    div_cur_page.value = page_appointed;
                }

                gMap_elem_total.mLayer.removeAllMarkers();
                elem_fea_layer.removeAllFeatures();
                for(gImageLayer_key in gMap_elem_total.oLayers){
                    let gImageLayer = gMap_elem_total.oLayers[gImageLayer_key];
                    if(gImageLayer.id=="img_elem_total"){
                        gMap_elem_total.removeLayer(gImageLayer);
                        break;
                    }
                }
                gImageLayer_elem_total = new gDBox.Layer.Image('img_elem_total', "/ocr/content_labeling/get_elem_page/?page_index="+page_appointed+"&row="+elem_row_col.row+"&col="+elem_row_col.col+"&date="+ (new Date()), {w: col*64, h: row*64}, {zIndex: 1});
                gMap_elem_total.addLayer(gImageLayer_elem_total);
                achieve_elem_id(elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected, page_appointed, elem_row_col.row, elem_row_col.col);
                
            }
        }
    }

}


/*偏旁上一页*/
function set_elem_prior(gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected){
    let div_elem_cur = document.getElementById("elem_current");
    div_elem_cur.value=div_elem_cur.value-1;
    set_elem_page(gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected);
}

/*偏旁下一页*/
function set_elem_next(gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected){
    let div_elem_cur = document.getElementById("elem_current");
    div_elem_cur.value=div_elem_cur.value+1;
    set_elem_page(gMap_elem_total, elem_fea_layer, elem_fea_style, elem_fea_style_selected, elem_selected);
}


function change_check_status(feature_layer, fea, polygon_id){
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'change_check_status/?polygon_id='+polygon_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200){
            var context = xhr.response;
            if(context != "err"){
                if (context == "false"){
                    fea.style.strokeColor="#0000ff";
                    feature_layer.renew();
                }
                if (context == "true"){
                    fea.style.strokeColor="#00ff00";
                    feature_layer.renew();
                }
                add_log("更改check:"+context,"message");
            }else{
                add_log("更改check出错","err");
            }
        }
    }
    
}

/*编辑特定IP的标注框*/
function alter_polygon_by_id(polygon_id, points, tar_width, tar_height, ori_width, ori_height, current_rotate, x_shift, y_shift){
    var xhr = new XMLHttpRequest();
    image_points = gdbox2img_map(points, tar_width, tar_height,ori_width,ori_height);
    console.log(image_points);
    image_points[0]['x'] += x_shift;
    image_points[0]['y'] += y_shift;
    image_points[1]['x'] += x_shift;
    image_points[1]['y'] += y_shift;
    image_points[2]['x'] += x_shift;
    image_points[2]['y'] += y_shift;
    image_points[3]['x'] += x_shift;
    image_points[3]['y'] += y_shift;
    console.log(image_points);
    rotate_points = rotate_polygon(image_points, -1*current_rotate, ori_width, ori_height);
    rotate_points_str = JSON.stringify(rotate_points);
    console.log(rotate_points_str);
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

