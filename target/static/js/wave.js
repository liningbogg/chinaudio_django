//曲线颜色列表
const color_chart=["red","blue","black"];

//播放器列表
var audios=new Array();
var pitchesArray=new Array();
//临时用inc数组
var index=new Array(100000);
for(var i=0;i<99999;i++){
    index[i]=i;
}

//设置异步传输
$.ajaxSetup({
        async : true
    });

//添加曲线的高层封装
function addChart(title, data, MyDiv,start, end){
    //曲线参数设置
    var options = {
        chart: {
            zoomType: 'xy' //xy方向均可缩放
        },
        boost: {
            useGPUTranslations: true
        },
        title: {
            text: title
        },
        xAxis: {
            categories: index.slice(start,end)
        },
        tooltip: {
            valueDecimals: 2  //显示精度
        },
        legend: {
			enabled: false
		},
		tooltip: {
			crosshairs: true,
			shared: true
		},
		plotOptions: {
			series: {
				marker: {
					enabled: false
				}
			},
		}, 
        series: []
    };
    options.series = new Array();
    //有待找到更规范的判断嵌套层数的方法 2019-01-31 12:44:35 李宁波
    if (data.length<10){
        for (var i=0;i<pitchesArray.length;i++){
            options.series[i] = new Object();
            options.series[i].color = color_chart[i];
            options.series[i].lineWidth = 1;
            options.series[i].name = MyDiv+i;
            options.series[i].data = data[i];
        }
    }else{
        options.series[0]=new Object();
        options.series[0].color = color_chart[0];
        options.series[0].lineWidth = 1;
        options.series[0].name = MyDiv;
        options.series[0].data = data
    }
        // 生成chart
    Highcharts.chart(MyDiv,options);
}

// 添加wave标记音高曲线, 最多显示三个主要音高
function AddWavePitchesChart(title, pitchesArray, MyDiv){
    addChart(null, pitchesArray, MyDiv,0,pitchesArray[0].length);
}

// 添加wave标记音高曲线, 最多显示三个主要音高,局部视图
function AddWavePitchesChartLocal(title, pitchesArray, MyDiv, start, end){
    addChart(title, pitchesArray, MyDiv,start,end);
}

// 添加wave标记音高曲线, 最多显示三个主要音高,局部视图
function AddFFT(title, pitchesArray, MyDiv, start, end){
    addChart(title, pitchesArray, MyDiv,start,end);
}

//添加wave播放
function add_wave(waveFile){
    var file_path = waveFile;  // 绝对路径
    var spilt_arr = file_path.split(str="/");
    var file_name=spilt_arr[spilt_arr.length-1];  // 获取文件名
    var user_name=spilt_arr[spilt_arr.length-2];
    console.log(user_name);
    var wave_audio= document.getElementById("song");  //获取播放器
    wave_audio.src = "/static/"+user_name+"/"+file_name;  // 设置播放资源url
    audios.push(wave_audio);  // 加入播放器队列
    wave_audio.addEventListener("play", pauseAll.bind(wave_audio));  // 互斥播放监听
}

//指定的div下添加音频播放器, 且申请动态数据, 采用动态长度参数列表
function playPhrase(MyDiv, opt){
    var phrase=new Audio();  // 音乐片段播放器
    phrase.controls=true;  // 设置显示播放控件
    phrase.load();  // 未证实加载是否有效 2019-01-31 09:43:25
    audios.push(phrase);  //加入播放器队列, 便于进行播放控制
    MyDiv.appendChild(phrase);
    phrase.addEventListener("play", pauseAll.bind(phrase));  //添加播放监视,用于单例播放
    var start = opt["start"];  //初始位置  // 起始帧位置
    var end = opt["end"];  // 终止帧位置(不包括)
    var blob_wav;  //曲目二进制流
    var nfft=opt["nfft"];  //默认nfft
    var fs = opt["fs"];  //当前默认采样率
    var title = opt["title"]  //当前曲目名称
    // pharse存储的是时间,这里要转换帧
    start = Math.round(start*fs/nfft);
    end = Math.round(end*fs/nfft);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'get_phrase/?'+"title="+title+"&start="+start+"&end="+end+"&nfft="+nfft+"&fs="+fs, true);
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

// 播放暂停函数,用于互斥播放
function pauseAll(audio) {
    var self = this;
    [].forEach.call(audios, function (i) {
        // 将audios中其他的audio全部暂停
        i !== self && i.pause();
    })
}

//选中clip后的处理函数
function selectClip(title, frame, id, possible_info, Fs,nfft,frameNum){
    //显示pitches
    var time=frame*nfft/Fs;//当前时间
    time = time.toFixed(2);
    var start=Math.round(Math.max(0,frame-50));
    var end=Math.round(Math.min(frame+50,frameNum));
    var pitches_slice=new Array();
    for (var i=0;i<pitchesArray.length;i++){
        pitches_slice[i]=pitchesArray[i].slice(start,end);
    }
    AddWavePitchesChartLocal(start+" - "+end+"LOCAL PITCH", pitches_slice, "pitch", start, end)
    //显示possible info
    document.getElementById("info").innerHTML=possible_info;
    //显示fft, 此处需要get数据
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'get_clipFFT/?'+"id="+id +"&fs="+Fs+"&nfft="+nfft, true);
    xhr.send(null)
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            try{
                var src = JSON.parse(xhr.response);
                //显示FFT频谱
                AddFFT(time+"s fft", src, "fft",0,src.length);
            }catch(err){
                alert(xhr.response)
            }
        }
    };
}

//下载片段
function download_phrase(title,start,end,fileName,fs,nfft){
    var xhr = new XMLHttpRequest();
    start=Math.round(start*fs/nfft);
    end=Math.round(end*fs/nfft);
    xhr.open('GET', 'get_phrase/?'+"title="+title+"&start="+start+"&end="+end+"&nfft="+nfft+"&fs="+fs, true);
    xhr.responseType = 'blob';
    xhr.send(null);
    //请求成功回调函数
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            //获取blob对象
            var blob_wav = xhr.response;
            var url= URL.createObjectURL(blob_wav);  // 获取音频blob url
            var eleLink = document.createElement('a');
            eleLink.download = fileName+".wav";
            eleLink.style.display = 'none';
            // 字符内容转变成blob地址
            eleLink.href = url;
            document.body.appendChild(eleLink);
            // 触发点击
            eleLink.click();
            // 然后移除
            document.body.removeChild(eleLink);
        }
    };
}

//邮件发送片段
function post_phrase(title,start,end,fileName, fs,nfft){
    var xhr = new XMLHttpRequest();
    start=Math.round(start*fs/nfft);
    end=Math.round(end*fs/nfft);
    xhr.open('GET', 'post_phrase/?'+"title="+title+"&start="+start+"&end="+end+"&nfft="+nfft+"&fs="+fs+"&fileName="+fileName, true);
    xhr.send(null);
    //请求成功回调函数
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            //获取对象
            alert("文件已经发送");
        }
    };
}

//删除Tone函数
function deleteTone(oper_class, item_class, id){
    var msg = "确定要删除？\n\n请确认！";
    if (confirm(msg)==false){
        return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'access/?'+"operation="+oper_class+"&class="+item_class+"&id="+id, true);
    xhr.send(null);
    //请求成功回调函数
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 &&xhr.status ==200) {//请求成功
            var result = xhr.response;
            //是否成功删除
            console.log(result);
            if(result == "ok"){
                //刷新界面
                window.location.reload();
            }else{
                alert("删除失败,请确认拥有权限!");//提示信息
            }

        }
    };
}

