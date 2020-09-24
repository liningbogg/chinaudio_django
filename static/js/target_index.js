/*添加tune*/
function add_tune(i)
{
    var tune_table=document.getElementById('tune_table')
    var rowsNum=tune_table.rows.length;
    if(i==-1){
        rowsindex=rowsNum-1;
    }else{
        rowsindex=i;
    }
    var tune_name=tune_table.rows[rowsindex].cells[0].getElementsByTagName("INPUT")[0].value;
    var a4_hz=tune_table.rows[rowsindex].cells[1].getElementsByTagName("INPUT")[0].value;
    _do=tune_table.rows[rowsindex].cells[2].getElementsByTagName("INPUT")[0].value;
    note1=tune_table.rows[rowsindex].cells[3].getElementsByTagName("INPUT")[0].value;
    note2=tune_table.rows[rowsindex].cells[4].getElementsByTagName("INPUT")[0].value;
    note3=tune_table.rows[rowsindex].cells[5].getElementsByTagName("INPUT")[0].value;
    note4=tune_table.rows[rowsindex].cells[6].getElementsByTagName("INPUT")[0].value;
    note5=tune_table.rows[rowsindex].cells[7].getElementsByTagName("INPUT")[0].value;
    note6=tune_table.rows[rowsindex].cells[8].getElementsByTagName("INPUT")[0].value;
    note7=tune_table.rows[rowsindex].cells[9].getElementsByTagName("INPUT")[0].value;
    console.log(note5);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '../addTune/?'+"tune_name="+tune_name+"&a4_hz="+a4_hz+"&do="+_do
    +"&note1="+note1+"&note2="+note2+"&note3="+note3+"&note4="+note4
    +"&note5="+note5
    +"&note6="+note6
    +"&note7="+note7
    , true);
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
