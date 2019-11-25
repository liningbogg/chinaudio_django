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
function delete_region(image_id, select_points){    
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
                console.log(delete_info);
            }
        }
    };
}
