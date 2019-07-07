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
            valueDecimals: 2,  //显示精度
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
        options.series[i].color = color_chart[i];
        options.series[i].lineWidth = 1;
        options.series[i].name = key;
        options.series[i].data = dictSeries[key].slice(start,end);
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
                document.getElementById('ref_info').innerHTML=pitch_pos;
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
    xhr.open('GET', 'filter_fft/?'+"title="+title+"&currentPos="+currentPos +"&nfft="+nfft +"&fs="+fs
        +"&filter_frq="+filter_frq+"&filter_width="+filter_width+"&labeling_id="+labeling_id, true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            try{
                var fft_filtered = JSON.parse(xhr.response);
                //在html上显示图形
                var srcChartDictSeries={"fft":srcFFT,"filter_fft":fft_filtered};
	            srcChartDictLine=[];
                addChart("",srcChartDictSeries,srcChartDictLine,440*nfft/fs,"sampling_fft",0,parseInt(4000*nfft/fs));
            }catch(err){
                //alert(xhr.response);
                alert(err)
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
    xhr.open('GET', 'get_phrase/?'+"title="+title+"&start="+play_start+"&end="+play_end+"&nfft="+nfft+"&fs="+fs, true);
    xhr.responseType = 'blob';
    xhr.send(null)
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            //获取blob对象
            var blob_wav = xhr.response;
            console.log(blob_wav)
            var url= URL.createObjectURL(blob_wav);  // 获取音频blob url
            phrase.src=url;  //设置播放路径
        }
    };
}

//设置strings
function sub_strings(title)
{
    var test = document.getElementById("strings_set_table");
    console.log(test);
    console.log(test.rows[1].cells[1].getElementsByTagName("INPUT")[0].value);
}

/*算法选择触发函数*/
function algorithm_selectFunc(algorithm_name,labeling_id)
{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'algorithm_select/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name , true);
    xhr.send(null);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var context = JSON.parse(xhr.response);
            try{
                var algorithm_string = "";
                algorithm_string+="总帧数:"+context["frame_num"]+" 已完成:"+context["clips_num"];
                algorithm_string+='  <input type="button" value="计算" onclick="cal_algorithm(\''+algorithm_name+'\',\''+labeling_id+'\')"></input>';
                algorithm_string+='&nbsp<input type="button" value="清空" onclick="clear_algorithm(\''+algorithm_name+'\',\''+labeling_id+'\')"></input>';
                algorithm_string+='&nbsp<input type="button" value="刷新" onclick="algorithm_selectFunc(\''+algorithm_name+'\',\''+labeling_id+'\')"></input>';
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
    xhr.open('GET', 'addReference/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name+"&isFilter="+isFilter , true);
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
    xhr.open('GET', 'setRefFilter/?'+"labeling_id="+labeling_id+"&algorithm_name="+algorithm_name+"&isFilter="+isFilter, true);
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
                    var div_string='<select id="add_reference_select"><option value="1">过滤</option><option value="0">不过滤</option></select>';
                    div_string+='&nbsp&nbsp&nbsp<input type="button" value="添加" onclick="add_reference(\''+algorithm_name+'\',\''+labeling_id+'\')"/>';
                    document.getElementById('reference_opt').innerHTML=div_string;

                }else{
                    //显示重置　删除
                    var div_string='<select id="del_reference_select" onclick="set_refFilter(\''+algorithm_name+'\',\''+labeling_id+'\')"'+'><option value="1" >过滤</option><option value="0">不过滤</option></select>';
                    div_string+='&nbsp<input type="button" value="删除" onclick="del_reference(\''+algorithm_name+'\',\''+labeling_id+'\')"/>';
                    div_string+='&nbsp<input type="button" value="设置主参考" onclick="set_primary(\''+algorithm_name+'\',\''+labeling_id+'\')"/>';
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

/*移动到制定位置*/
function move2Pos(labeling_id)
{
    manual_pos=document.getElementById("table_clips_local");
    rowsNum=manual_pos.rows.length;
    manualPos=manual_pos.rows[rowsNum-1].cells[0].getElementsByTagName("INPUT")[0].value;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'setManualPos/?'+"labeling_id="+labeling_id+"&manualPos="+manualPos, true);
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

}