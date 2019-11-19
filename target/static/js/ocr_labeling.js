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
function add_labeling_polygon(image_id, points){
    var xhr = new XMLHttpRequest();
    var pointsStr=JSON.stringify(points);
    xhr.open('GET', 'add_labeling_polygon/?'+"image_id="+image_id+"&points="+pointsStr, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
                return context;
            }catch(e)
            {
                console.log(e);
                return str(e);
            }
        }
    };
}

/*多边形显示*/
function add_polygon_disp(gFeatureLayer,gFetureStyle,points, polygon_id){
    const timestamp = new Date().getTime();
    // 元素添加展示
    let fea = new gDBox.Feature.Polygon(
            `feature-${timestamp}`,
            points,
            {
                polygon_id: polygon_id
            },
            gFetureStyle
        );
    gFeatureLayer.addFeature(fea);
    //console.log(fea.data['polygon_id']);
    console.log(gFeatureLayer);
}
/*删除用户下所有与页面相关的标注*/
function delete_all_polygon(image_id){
    var msg = "确定要删除整页标注？？\n\n请确认危险操作！";
    if (confirm(msg)==false){
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

/**/
function set_labeling_mode(mode){
    labeling_mode=mode;
}
