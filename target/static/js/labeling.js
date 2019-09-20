//临时用inc数组
var indexArr=new Array(100000);
for(var i=0;i<99999;i++){
    indexArr[i]=i;
}
//曲线颜色列表
const color_chart=["red","blue","black","green","yellow","gray"];
//播放器容器
var audios=new Array();
//设置异步传输
$.ajaxSetup({
        async : true
    });

// 播放暂停函数,用于互斥播放
function pauseAll(audio) {
    var self = this;
    [].forEach.call(audios, function (i) {
        // 将audios中其他的audio全部暂停
        i !== self && i.pause();
    })
}

//添加曲线的高层封装,data字典中包含lengend 以及数据
function addChart(title, dictSeries, dictLine, currentPos, MyDiv,start, end){
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
            categories: indexArr.slice(start,end),

            tickInterval:10
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
function cal_pitch_pos(title)
{
    var  primary_pitch=document.getElementById('primary_pitch').value;
    //取得重新计算的音位可能性
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'cal_pitch_pos/?'+"title="+title +"&primary_pitch="+primary_pitch, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            try{
                var pitch_pos = xhr.response;
                //在html上显示信息
                document.getElementById('ref_info_a').innerHTML=pitch_pos;
            }catch(err){
                alert(xhr.response);
            }
        }
    };
}

//重新过滤ｆｆｔ
function filter_fft(srcFFT,title,currentPos,nfft,fs,labeling_id)
{
    var filter_frq=document.getElementById('filter_frq').value;
    var filter_width=document.getElementById('filter_width').value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'filter_fft/?'+"title="+title+"&current_pos="+currentPos +"&nfft="+nfft +"&fs="+fs
        +"&filter_frq="+filter_frq+"&filter_width="+filter_width+"&labeling_id="+labeling_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            try{
                var fft_filtered = JSON.parse(xhr.response);
                //在html上显示图形
                var srcChartDictSeries={
                    "fft":{"list":srcFFT,"visible":true},
                    "filter_fft":{"list":fft_filtered,"visible":true}
                };
	            srcChartDictLine=[];
                addChart("",srcChartDictSeries,srcChartDictLine,440*nfft/fs,"sampling_fft",0,parseInt(4000*nfft/fs));
            }catch(err){
                //alert(xhr.response);
                alert(err)
            }
        }
    };
}

//计算自定义片段的音高
function cal_customRef(title,nfft,fs,labeling_id)
{
    var start=document.getElementById('custom_start').value;
    var end=document.getElementById('custom_end').value;
    console.log(title,nfft,start,end);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'calCustomPitch/?'+"title="+title+"&start="+start+"&end="+end+"&nfft="+nfft+"&fs="+fs+"&labeling_id="+labeling_id, true);
    xhr.send(null)
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            try{
                var context = JSON.parse(xhr.response);
                var primaryPitch=context["primaryPitch"];
                var src = context["src"];
                var filter_fft = context["filter_fft"];
                var medium = context["medium"];
                var srcChartDictSeries={
                    "fft":{"list":src,"visible":true},
                    "filter_fft":{"list":filter_fft,"visible":true}
                };
                var possible_pos = context["possible_pos"];

	            srcChartDictLine=[];
                addChart("",srcChartDictSeries,srcChartDictLine,440*nfft/fs,"sampling_fft",0,parseInt(4000*4410/fs));
                srcChartDictSeries={"medium":{"list":medium,"visible":true}};
	            srcChartDictLine=[];
	            //此处的４４０要跟随是否降低采样变化，尚未实现
                addChart("",srcChartDictSeries,srcChartDictLine,4400*medium.length/14000,"sampling_medium",0,medium.length);
                document.getElementById('ref_info').innerHTML=possible_pos;
            }catch(err){
                console.log(err);
            }
        }
    };
}

//播放片段
function play_clips(title,nfft)
{
    var play_start=document.getElementById('play_start').value;
    var play_end=document.getElementById('play_end').value;
    var fs = document.getElementById('play_fs').value;
    nfft=nfft*fs/44100;
    console.log(nfft);
    var phrase=new Audio();  // 音乐片段播放器
    phrase.controls=false;  // 设置显示播放控件
    phrase.autoplay="autoplay";
    phrase.load();  // 未证实加载是否有效 2019-01-31 09:43:25
    audios.push(phrase);  //加入播放器队列, 便于进行播放控制
    document.getElementById('play_clips').appendChild(phrase);
    phrase.addEventListener("play", pauseAll.bind(phrase));  //添加播放监视,用于单例播放
    var blob_wav;  //曲目二进制流
    // pharse存储的是时间,这里要转换帧
    //start = Math.round(play_start*fs/nfft);
    //end = Math.round(play_end*fs/nfft);
    var xhr = new XMLHttpRequest();
    console.log(play_start);
    xhr.open('GET', 'get_phrase/?'+"title="+title+"&start="+play_start+"&end="+play_end+"&nfft="+nfft+"&fs="+fs, true);
    xhr.responseType = 'blob';
    xhr.send(null)
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            //获取blob对象
            var blob_wav = xhr.response;
            var url= URL.createObjectURL(blob_wav);  // 获取音频blob url
            phrase.src=url;  //设置播放路径
        }
    };
}

//设置strings
function sub_strings(title,wave_id)
{
    var test = document.getElementById("strings_set_table");
    var strings=new Array(7);
    for(var i=0;i<7;++i){
        strings[i]=test.rows[1].cells[i].getElementsByTagName("INPUT")[0].value;
    }
    var _do=test.rows[1].cells[7].getElementsByTagName("INPUT")[0].value;
    var a4_hz=test.rows[1].cells[8].getElementsByTagName("INPUT")[0].value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'strings_reset/?'+"strings="+strings+"&do="+_do+"&a4_hz="+a4_hz+"&wave_id="+wave_id , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context);
                location.reload();
            }catch(e)
            {
                console.log(e);
            }

        }
    };
}

function tune_reset(wave_id){
    var iscontinue= confirm("确定执行危险操作吗?");
    if(iscontinue==true){
        tune_id=document.getElementById('select_tune').value;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'tune_reset/?'+"tune_id="+tune_id+"&wave_id="+wave_id , true);
        xhr.send(null);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
                var context = xhr.response;
                try{
                    console.log(context);
                    location.reload();
                }catch(e)
                {
                    console.log(e);
                }

            }
        };
    }
}

/*算法选择触发函数*/
function algorithm_selectFunc(algorithm_name, labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'algorithm_select/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = JSON.parse(xhr.response);
            try{
                var algorithm_string = "";
                algorithm_string+="All:"+context["frame_num"]+" Done:"+context["clips_num"];
                algorithm_string+='  <input type="button" value="cal" onclick="cal_algorithm(\''+algorithm_name+'\',\''+labeling_id+'\')"></input>';
                algorithm_string+='&nbsp<input type="button" value="clear" onclick="clear_algorithm(\''+algorithm_name+'\',\''+labeling_id+'\')"></input>';
                algorithm_string+='&nbsp<input type="button" value="update" onclick="algorithm_selectFunc(\''+algorithm_name+'\',\''+labeling_id+'\')"></input>';
                document.getElementById('algorithm_opt').innerHTML=algorithm_string;
            }catch(e)
            {
                console.log(e);
            }

        }
    };
}
//计算某个算法的数据
function cal_algorithm(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'algorithm_cal/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = JSON.parse(xhr.response);
            try{
                console.log(context)
                alert(algorithm_name+"算法正在形成计算数据"+context["clips_num_oncreate"]+"条数据将被创建");
            }catch(e)
            {
                console.log(e);
            }

        }
    };
}
//清空labeling下某个算法的数据
function clear_algorithm(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'algorithm_clear/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = JSON.parse(xhr.response);
            try{
                console.log(context)
                alert(algorithm_name+"算法数据被清空,共删除"+context["clips_num_delete"]+"条数据");
            }catch(e)
            {
                console.log(e);
            }

        }
    };
}
/*添加参考算法数据*/
function add_reference(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    var isFilter = document.getElementById('add_reference_select').value;
    xhr.open('GET', 'addReference/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name+"&is_filter="+isFilter , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }

        }
    };
}

/*删除参考算法数据*/
function del_reference(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'delReference/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}

/*设置主要参考音高*/
function set_primary(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'setPrimary/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}

/*更改算法是否过滤*/
function set_refFilter(algorithm_name,labeling_id)
{
    isFilter=document.getElementById("del_reference_select").value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'setRefFilter/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name+"&is_filter="+isFilter, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}
/*算法配置选择*/
function reference_selectFunc(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'reference_select/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = JSON.parse(xhr.response);
            try{
                //根据查询得到的配置情况，提供不同的显示界面
                var algorithm_num=context["algorithms_num"];
                if(algorithm_num<1){
                    //显示添加
                    var div_string='<select id="add_reference_select"><option value="1">Filter</option><option value="0">WithoutFilter</option></select>';
                    div_string+='&nbsp&nbsp&nbsp<input type="button" value="add" onclick="add_reference(\''+algorithm_name+'\',\''+labeling_id+'\')"/>';
                    document.getElementById('reference_opt').innerHTML=div_string;

                }else{
                    //显示重置　删除
                    var div_string='<select id="del_reference_select" onclick="set_refFilter(\''+algorithm_name+'\',\''+labeling_id+'\')"'+'><option value="1" >filter</option><option value="0">without_filter</option></select>';
                    div_string+='&nbsp<input type="button" value="delete" onclick="del_reference(\''+algorithm_name+'\',\''+labeling_id+'\')"/>';
                    div_string+='&nbsp<input type="button" value="set as primary" onclick="set_primary(\''+algorithm_name+'\',\''+labeling_id+'\')"/>';
                    document.getElementById('reference_opt').innerHTML=div_string;
                }
            }catch(e)
            {
                console.log(e);
            }

        }
    };
}
/*重新计算stft作为输入*/
function cal_Stft(labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'calStft/?'+"labeling_id="+labeling_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}

/*重新计算rmse作为输入*/
function cal_Rmse(labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'calRmse/?'+"labeling_id="+labeling_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}

/*重新计算EE作为输入*/
function cal_EE(labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'calEE/?'+"labeling_id="+labeling_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = xhr.response;
            try{
                console.log(context)
            }catch(e)
            {
                console.log(e);
            }
        }
    };
}

/*计算stft ee rmse*/
function cal_allInput(labeling_id)
{
    cal_Stft(labeling_id);
    cal_Rmse(labeling_id);
    cal_EE(labeling_id);

}

/*移动到制定位置*/
function move2Pos(labeling_id)
{
    manual_pos=document.getElementById("table_clips_local");
    rowsNum=manual_pos.rows.length;
    manualPos=manual_pos.rows[rowsNum-1].cells[0].getElementsByTagName("INPUT")[0].value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'setManualPos/?'+"labeling_id="+labeling_id+"&manual_pos="+manualPos, true);
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



/*刷新前提交*/
window.onbeforeunload = function(){
    var table_info = document.getElementById("table_info");
    var title = table_info.rows[1].cells[1].getElementsByTagName("INPUT")[0].value;
    var frameNum = table_info.rows[2].cells[1].getElementsByTagName("INPUT")[0].value;
    var current_frame = table_info.rows[3].cells[1].getElementsByTagName("INPUT")[0].value;
    var manual_pos = table_info.rows[4].cells[1].getElementsByTagName("INPUT")[0].value;
    var nfft = table_info.rows[5].cells[1].getElementsByTagName("INPUT")[0].value;
    var extend_rad = table_info.rows[6].cells[1].getElementsByTagName("INPUT")[0].value;
    var tone_extend_rad = table_info.rows[7].cells[1].getElementsByTagName("INPUT")[0].value;
    var vad_thrart_ee = table_info.rows[8].cells[1].getElementsByTagName("INPUT")[0].value;
    var vad_throp_ee = table_info.rows[9].cells[1].getElementsByTagName("INPUT")[0].value;
    var vad_thrart_rmse = table_info.rows[10].cells[1].getElementsByTagName("INPUT")[0].value;
    var create_user_id = table_info.rows[11].cells[1].getElementsByTagName("INPUT")[0].value;
    var primary_ref = table_info.rows[12].cells[1].getElementsByTagName("INPUT")[0].value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'labeling_reset/?'+'title='+title+'&frameNum='+frameNum+'&current_frame='+current_frame+"&manual_pos="+manual_pos+"&nfft="+nfft+"&extend_rad="+extend_rad+"&tone_extend_rad="+tone_extend_rad+"&vad_thrart_ee="+vad_thrart_ee+"&vad_throp_ee="+vad_throp_ee+"&vad_thrart_rmse="+vad_thrart_rmse+"&create_user_id="+create_user_id+"&primary_ref="+primary_ref, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
        }
    }
}
