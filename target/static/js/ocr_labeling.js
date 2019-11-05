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
