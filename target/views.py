#encoding = utf-8
import time
import json
import pickle
import smtplib
from datetime import timedelta
from email.mime.application import MIMEApplication
from io import BytesIO
import threading
import librosa
import numpy as np
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
import wave as waveout
from pydub import AudioSegment
from django.db.models import Q
import os
import shutil
from target.models import Clip
from target.models import MarkedPhrase
from target.models import Tone
from target.models import Wave
from target.models import Labeling
from target.models import Stft
from target.models import AlgorithmsClips
from target.models import AlgorithmsMediums
from target.models import LabelingAlgorithmsConf
from target.models import Tune
from target.models import TargetUser
from target.models import OcrPDF
from target.models import PDFImage
from target.models import OcrAssistRequest
from target.models import OcrAssist
from target.models import OcrLabelingPolygon
from .forms import RegisterForm
from chin import Chin
from .forms import UserFormWithoutCaptcha
from abc import abstractmethod
import scipy
import scipy.signal.windows
import scipy.signal as signal
from target.targetTools import targetTools
from baseFrqComb import BaseFrqDetector
from scipy.interpolate import interp1d
from scipy.fftpack import fft
import multiprocessing
from django.core.cache import cache
import sys
import soundfile
import base64
import redis
import fitz
import io
from target.np_encoder import NpEncoder
from PIL import Image

# 归一化函数
def maxminnormalization(x, minv, maxv):
    min_val = np.min(x)
    max_val = np.max(x)
    y = (x - min_val) / (max_val - min_val + 0.0000000001) * (maxv - minv) + minv
    return y


# filter by basefrq
def filter_by_base(src, basefrq, width, nfft, fs):
    width = width*nfft/fs
    basefrq = basefrq*nfft/fs
    tar = np.copy(src)
    num = min(int(len(src) / basefrq), 30)
    for i in np.arange(num):
        frq = i * basefrq
        tar[int(frq - width):int(frq + width)] = min(src[int(frq - width)], src[int(frq + width)])
    return tar


# 缓存类基类
class MemItem:
    """
    曲目条目定义类
    """
    @abstractmethod
    def get_subwave(self, start, end):
        """
        访问wave子数据
        :param start: 其实位置
        :param end: 中止位置，不包括end
        :return: 返回子数组（float数组）
        """
        pass


# wave类
class MemitemWave(MemItem):
    """
    曲目缓存定义类
    """

    def __init__(self, user_id, title, fs, nfft, frame_init, frame_num, wave):
        self.user_id = user_id
        self.title = title
        self.fs = fs
        self.nfft = nfft
        self.wave = wave
        self.frame_init = frame_init
        self.frame_num = frame_num

    def get_subwave(self, start, end):
        """
        访问wave子数据
        :param start: 起始位置
        :param end: 终止位置，不包括end
        :return: 返回子数组（float数组）
        """
        sub = np.copy(self.wave[start: end])
        return sub


class WaveMemWave:
    
    @staticmethod
    def get_cache_name_list(user_id, title, fs, nfft, start, end):
        cache_name_list = []  # 程序目的输出　字典列表
        try:
            labeling = Labeling.objects.get(create_user_id=user_id, title=title)  # 用户标记数据
            cache_block_size = labeling.cache_block_size
            first_block_index = int(start / cache_block_size)  # 第一块缓存索引
            last_block_index = int(end / cache_block_size)  # 最后一块缓存索引
            for i in range(first_block_index, last_block_index + 1):
                cache_name = str(user_id) + "_" + str(title) + "_" + "wave_" + str(fs) +"_"+str(cache_block_size)+ "_" + str(i)
                cache_name = str(cache_name)
                start_pos = max(i * cache_block_size, start)
                end_pos = min((i + 1) * cache_block_size, end)  # 右侧区间开
                cache_name_list.append(
                    {
                        "name": cache_name,
                        "block_frame_init": i * cache_block_size,  # 缓存块起始地址
                        "block_frame_num": cache_block_size,  # 缓存块长度
                        "start_pos": start_pos,
                        "end_pos": end_pos,
                    }
                )
        except Exception as e:
            print(e)
        finally:
            return cache_name_list
    
    def achieve(self, user_id, title, fs, nfft, start, end):
        """
        获取制定片段，原始wave波形
        :param title:名称
        :param nfft: 帧长度
        :param start: 起始帧
        :param end: 终止帧
        :param user_id 用户id
        :param fs: 采样率
        :return: float32array
        """
        index = 0
        sub_wave = []
        try:
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            chche_info = self.get_cache_name_list(user_id, title, fs, nfft, start, end)  # 获取缓存块信息
            for item in chche_info:
                chche_block = cache.get(item["name"])
                block_init = item["block_frame_init"]*wave.nfft  # 缓存初始
                block_len = item["block_frame_num"]*wave.nfft  # 缓存持续
                if chche_block is None:
                    stream ,sr = soundfile.read(wave.waveFile, start=block_init, frames=block_len)
                    stream = stream[:,0]
                    if sr != fs:
                        length = len(stream)
                        result_num = int(length*fs/sr)
                        stream = signal.resample(stream, result_num)
                    stream = np.ascontiguousarray(stream, dtype=np.float32) 
                    mem_item = MemitemWave(
                        user_id,
                        title,
                        fs,  # 重新采样率
                        nfft,  # 重采样后的frame长
                        item["block_frame_init"],
                        item["block_frame_num"],
                        stream
                    )
                    cache.set(item["name"], pickle.dumps(mem_item),nx=True)
                    cache.expire(item["name"], 3600)
                    sub_wave_item = mem_item.get_subwave(
                        (item["start_pos"]-item["block_frame_init"])*nfft,
                        (item["end_pos"]-item["block_frame_init"])*nfft
                    )
                    # 分段wave
                    sub_wave.extend(sub_wave_item)
                else:
                    sub_wave_item = pickle.loads(chche_block).get_subwave(
                        (item["start_pos"]-item["block_frame_init"]) * nfft,
                        (item["end_pos"]-item["block_frame_init"]) * nfft
                    )
                    sub_wave.extend(sub_wave_item)
        except Exception as e:
            print(e)
        finally:
            return sub_wave

# Create your views here.
class TargetView(View):
    msg_from = '1214397815@qq.com'  # 发送方邮箱
    passwd = 'ruzdcenkznfhhijf'  # 填入发送方邮箱的授权码
    msg_to = '1214397815@qq.com'  # 收件人邮箱

    def __init__(self):
        """
        重载初始化函数
        """
        super(View, self).__init__()
        self.wave_mem_wave = WaveMemWave()  # 构建缓存对象
        # self.wave_mem_stft = WaveMemStft(self.wave_mem_wave, 512)
        # self.wave_mem_spectrumEntropy = WaveMemSpectrumEntropy(self.wave_mem_stft, 512)
        # self.wave_mem_rmse = WaveMemRmse(self.wave_mem_wave, 512)
        self.sender = None
        self.redis_pool=redis.ConnectionPool(host='localhost', port=6379,db=0, password='1a2a3a', encoding='utf-8')

    @classmethod
    @method_decorator(login_required)
    def index(cls, request):
        """
        主要索引视图
        :param request:
        :return:
        """
        waves = Wave.objects.filter(create_user_id=request.user)
        for wave in waves:
            clips = Clip.objects.filter(title=wave.title, create_user_id=request.user)
            if clips.count() == 0:
                completion = 0
            else:
                candidate_frame = clips.aggregate(Max('startingPos'))['startingPos__max']
                candidate_frame_num = wave.frameNum  # 待测总帧数
                completion = round(candidate_frame / candidate_frame_num * 100, 1)
                completion = min(100, completion)
            wave.completion = completion
            wave.save(update_fields=["completion"])
        waves = Wave.objects.filter(create_user_id=request.user).order_by('frameNum')
        tunes = None
        try:
            tunes = Tune.objects.filter(create_user_id=request.user)
        except Exception as e:
            print(e)
        context = {'waves': waves, 'tunes': tunes}
        return render(request, 'index.html', context)

    @classmethod
    @method_decorator(login_required)
    def digital(cls,request):
        """
        古琴数字化数据库首页
        
        """
        user_id = str(request.user)
        ocrPDFList = OcrPDF.objects.filter(create_user_id=request.user)
        assist_request_in_set = OcrAssistRequest.objects.filter(owner=user_id,status="pushed")
        assist_request_out_set = OcrAssistRequest.objects.filter(create_user_id=user_id)
        ocr_assist_set = OcrAssist.objects.filter(assist_user_name=user_id)
        context = {'ocrPDFList':ocrPDFList,"assist_request_in_set":assist_request_in_set,"assist_request_out_set":assist_request_out_set,"ocr_assist_set":ocr_assist_set}
        return render(request,'digital.html',context)


    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request(cls, request):
        """
        申请协助其他用户进行标注
        :param request:
        :return:
        """
        try:
            user_id = str(request.user)
            pdfs_set = OcrPDF.objects.filter(~Q(create_user_id=user_id))
            pdfs_dict = {}
            for pdf in pdfs_set:
                pdfs_dict[pdf.id]={"title":pdf.title,"create_user_id":pdf.create_user_id,"assist_num":pdf.assist_num}
            assist_set = OcrAssist.objects.filter(create_user_id=user_id)
            for assist in assist_set:
                if assist.ocrPDF in pdfs_dict:
                    pdfs_dict.pop(assist.ocrPDF)
        except Exception as e:
            print(e)
        context = {'pdfs': pdfs_dict}
        return render(request, 'ocrPDF_assist_request.html', context)

    @method_decorator(login_required)
    def sub_and_execute_assist_ocr(self,request):
        try:
            user_id = str(request.user)
            pdfs_selected = json.loads(request.GET.get("pdfs_selected"))
            context_str="request pushed."
            success_str="\nsuccess:"
            fault_str="\nfault:"
            for pdf in pdfs_selected:
                owner_name = pdf["user_name"]
                pdf_title = pdf["pdf_title"]
                try:
                    OcrAssistRequest(owner=owner_name,title=pdf_title,create_user_id=user_id,status="pushed").save()
                    success_str=success_str+"\n    "+owner_name+"/"+pdf_title+";";
                except Exception as e:
                    print(e)
                    fault_str=fault_str+"\n   "+owner_name+"/"+pdf_title+";"
            return HttpResponse(context_str+success_str+fault_str)
        except Exception as e:
            return HttpResponse("err")


    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request_accept(cls, request):
        """
        通过其他用户的协助申请
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            assert user_name == request.GET.get("owner")
            assist_user_name = request.GET.get("create_user_id")
            pdf_title = request.GET.get("title")
            ocrPDF = OcrPDF.objects.get(create_user_id=user_name,title=pdf_title)
            ocrAssist = OcrAssist(ocrPDF=ocrPDF,current_frame=0,assist_user_name=assist_user_name,create_user_id=user_name)
            ocrPDF.assist_num=ocrPDF.assist_num+1
            ocrPDF.save()
            ocrAssist.save()
            ocrAssistRequest = OcrAssistRequest.objects.get(owner=user_name,create_user_id=assist_user_name,title=pdf_title)
            ocrAssistRequest.status="accepted"
            ocrAssistRequest.save()
        except Exception as e:
            print(e)
        finally:
            return redirect('/digital')
    

    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request_deny(cls, request):
        """
        拒绝其他用户的协助申请
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            assert user_name == request.GET.get("owner")
            assist_user_name = request.GET.get("create_user_id")
            pdf_title = request.GET.get("title")
            ocrAssistRequest = OcrAssistRequest.objects.get(owner=user_name,create_user_id=assist_user_name,title=pdf_title)
            ocrAssistRequest.status="denied"
            ocrAssistRequest.save()
            
        except Exception as e:
            print(e)
        finally:
            return redirect('/digital')

    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request_delete(cls, request):
        """
        拒绝其他用户的协助申请
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            owner = request.GET.get("owner")
            assist_user_name = request.GET.get("create_user_id")
            pdf_title = request.GET.get("title")
            ocrAssistRequest = OcrAssistRequest.objects.get(owner=owner,create_user_id=assist_user_name,title=pdf_title)
            ocrAssistRequest.status="deleted"
            ocrAssistRequest.delete()
            
        except Exception as e:
            print(e)
        finally:
            return redirect('/digital')

    @method_decorator(login_required)
    def add_tune(self, request):
        tune_name = str(request.GET.get('tune_name'))
        a4_hz = request.GET.get('a4_hz')

        do = str(request.GET.get('do'))
        note1 = str(request.GET.get('note1'))
        note2 = str(request.GET.get('note2'))
        note3 = str(request.GET.get('note3'))
        note4 = str(request.GET.get('note4'))
        note5 = str(request.GET.get('note5'))
        note6 = str(request.GET.get('note6'))
        note7 = str(request.GET.get('note7'))
        try:
            Tune.objects.update_or_create(
                create_user_id=request.user,
                tune_name=tune_name,
                defaults={
                    'a4_hz': a4_hz,
                    'do': do,
                    'note1': note1,
                    'note2': note2,
                    'note3': note3,
                    'note4': note4,
                    'note5': note5,
                    'note6': note6,
                    'note7': note7
                },
            )
        except Exception as e:
            print(e)
            return HttpResponse("err")
        return HttpResponse("ok")

    @method_decorator(login_required)
    def strings_reset(self, request):
        strings_str = request.GET.get('strings')
        do = request.GET.get('do')
        a4_hz = float(request.GET.get('a4_hz'))
        f_list = strings_str.split(',')
        strings = []
        for item in f_list:
            strings.append(float(item))
        try:
            wave_id = request.GET.get('wave_id')
            wave = Wave.objects.get(id=wave_id)
            chin = Chin()
            chin.set_ahz(a4_hz)
            chin.set_do(do)
            chin.set_hzes(strings)
            wave.chin = pickle.dumps(chin)
            wave.save()
        except Exception as e:
            print(e)
            return HttpResponse(e)
        return HttpResponse("ok")

    @classmethod
    def handle_upload_file(cls, upload_file, path, user_id):
        if not os.path.exists(path):
            os.makedirs(path)
            print("文件夹已经创建:"+path)
        file_name = path + upload_file.name
        wave_name = upload_file.name.split(".")[0]
        already = Wave.objects.filter(create_user_id=user_id, title=wave_name)  # 已经存在的wave
        if already.count() == 0:
            try:
                destination = open(file_name, 'wb+')
                for chunk in upload_file.chunks():
                    destination.write(chunk)
                destination.close()
                # 插入数据库
                stream, stream_fs = librosa.load(file_name, mono=False, sr=None)
                duration = librosa.core.get_duration(y=stream[0], sr=stream_fs)
                nfft = round(stream_fs / 10)
                speech_stft, phase = librosa.magphase(
                    librosa.stft(stream[0], n_fft=nfft, hop_length=nfft, window=scipy.signal.windows.hann))
                speech_stft = np.transpose(speech_stft)  # stft转置
                frame_num = np.size(speech_stft, 0)
                # chin 设置
                chin = Chin()
                chin.set_ahz(440)
                wave = Wave(
                    create_user_id=user_id,
                    title=wave_name,
                    waveFile=file_name,
                    frameNum=frame_num,
                    duration=duration,
                    chin=pickle.dumps(chin),
                    fs=stream_fs,
                    nfft=nfft,
                    completion=0
                )
                wave.save()
                return "success"
            except Exception as e:
                print(e)
                return "err"
        else:
            print(wave_name + " already existed")
            return "err"

    def handle_upload_file_pdf(self, upload_file, path, user_id):
        if not os.path.exists(path):
            os.makedirs(path)
            print("文件夹已经创建:"+path)
        file_name = path + upload_file.name
        base_name = upload_file.name.split(".")[0]
        already = OcrPDF.objects.filter(create_user_id=user_id, title=base_name)  # 已经存在的pdf
        if already.count() == 0:
            try:
                destination = open(file_name, 'wb+')
                for chunk in upload_file.chunks():
                    destination.write(chunk)
                destination.close()
                # 插入数据库
                ocrPDFItem = OcrPDF(
                    create_user_id=user_id,
                    title=base_name,
                    file_name=file_name,

                )
                ocrPDFItem.save()
                # 解压pdf
                args={
                    "create_user_id":user_id,
                    "title":base_name,
                    "file_name":file_name,
                    "ocrPDF_id":ocrPDFItem.id
                }
                red = redis.Redis(connection_pool=self.redis_pool)
                red.rpush("pdfUnpackTask", json.dumps(args))  # 此处不做重复性检查
                '''doc = fitz.open(file_name)
                count=0
                for page in doc:
                    pix = page.getPixmap()
                    if pix:
                        dataPNG=pix.getPNGData()  # png图片二进制流
                        pdfImage=PDFImage(
                            ocrPDF=ocrPDFItem,
                            frame_id=count,
                            data_byte=dataPNG,
                            data_type="png",
                            height=pix.height,
                            width=pix.width
                        )
                        pdfImage.save()
                        count=count+1
                ocrPDFItem.frame_num=count
                ocrPDFItem.save()
                '''


            except Exception as e:
                print(e)
                return "err"
        else:
            print(base_name + " already existed")
            return "err"

    @classmethod
    @method_decorator(login_required)
    def addwaves(cls, request):
        if request.method == 'POST':
            content = request.FILES.getlist("upload_wave")
            if not content:
                return HttpResponse("没有上传内容")
            user_id = str(request.user)
            path = "/home/liningbo/waveFiles/"+user_id+"/"
            for wave in content:
                cls.handle_upload_file(wave, path, user_id)
        return HttpResponse("add waves done")

    @method_decorator(login_required)
    def addpdfs(self,request):
        if request.method == 'POST':
            content = request.FILES.getlist("upload_pdf")
            if not content:
                return HttpResponse("没有上传内容")
            user_id = str(request.user)
            path = "/home/liningbo/pdfFiles/"+user_id+"/"
            for pdf in content:
                self.handle_upload_file_pdf(pdf, path, user_id)
        return HttpResponse("add pdfs done")

    @classmethod
    @method_decorator(login_required)
    def copywaves(cls, request):
        """
        从其他用户获取wave,然后复制至特定用户
        :param request:
        :return:
        """
        user_id = str(request.user)
        waves = Wave.objects.filter(~Q(create_user_id=user_id)).values('id', 'title', 'create_user_id')
        wave_name_already = Wave.objects.filter(create_user_id=user_id).values('title')
        name_exist = set()
        waves_filter = []
        for wave_name in wave_name_already:
            name_exist.add(wave_name["title"])
        for wave in waves:
            if wave['title'] not in name_exist:
                waves_filter.append(wave)

        context = {'waves': waves_filter}
        return render(request, 'copywaves.html', context)

    @staticmethod
    def sub_and_execute_copywaves(request):
        user_id = str(request.user)
        waves_selected = json.loads(request.GET.get("waves_selected"))

        for wave in waves_selected:
            create_user = wave["user_id"]
            title = wave["wave_title"]
            try:
                wave_item = Wave.objects.get(create_user_id=create_user, title=title)
                wave_item.save()
                wave_item.pk = None
                newfilepath_arr = wave_item.waveFile.split("/")
                newfilepath_arr.remove("")
                newfilepath_arr[len(newfilepath_arr)-2] = user_id
                file_name = ""
                path_name = ""
                counter = 0
                for path_item in newfilepath_arr:
                    file_name = file_name+"/"+path_item
                    if counter < len(newfilepath_arr)-1:
                        path_name = path_name+"/"+path_item
                    counter = counter+1
                if os.path.exists(path_name) is False:
                    os.mkdir(path_name)
                shutil.copyfile(wave_item.waveFile, file_name)
                wave_item.waveFile = file_name
                wave_item.create_user_id = user_id
                wave_item.save()
            except Exception as e:
                print(e)
        return HttpResponse("copy completed")

    @method_decorator(login_required)
    def labeling(self, request):
        title = request.GET.get('title')
        user_id = str(request.user)
        wave = Wave.objects.get(create_user_id=user_id, title=title)
        wave_id = wave.id
        fs = wave.fs
        nfft = wave.nfft
        end = wave.frameNum
        try:
            labelinfo = Labeling.objects.get(create_user_id=user_id, title=title)
        except Exception as e:
            Labeling(title=title, create_user_id=user_id, nfft=nfft, frameNum=wave.frameNum).save()
            labelinfo = Labeling.objects.get(create_user_id=user_id, title=title)
        thrart_ee = labelinfo.vad_thrart_EE
        thrart_rmse = labelinfo.vad_thrart_RMSE
        throp = labelinfo.vad_throp_EE
        tone_extend_rad = labelinfo.tone_extend_rad
        manual_pos = labelinfo.manual_pos
        if manual_pos < 0:
            # 计算位置
            clips = Clip.objects.filter(title=title, create_user_id=request.user, nfft=nfft)
            if clips.count()==0:
                current_frame = 0
            else:
                candidate_frame = clips.aggregate(Max('startingPos'))['startingPos__max']
                current_frame = candidate_frame+1
                current_frame = min(wave.frameNum-1, current_frame)
        else:
            # 指定位置
            labelinfo.manual_pos = -1  # 指定位置只生效一次
            current_frame = manual_pos
            pass            
        labelinfo.current_frame = current_frame
        labelinfo.save()
        extend_rad = labelinfo.extend_rad

        try:
            ee = pickle.loads(wave.ee)[max(current_frame-extend_rad, 0): min(current_frame+extend_rad, end)]
            ee = list(ee)
        except Exception as e:
            ee = list()
        try:
            rmse = pickle.loads(wave.rmse)[max(current_frame-extend_rad, 0): min(current_frame+extend_rad, end)]
            rmse = list(rmse)
            vadrs = targetTools.vad(ee, rmse, thrart_ee, thrart_rmse, throp)
        except Exception as e:
            rmse = list()
            vadrs = { 
                'info':None,
                'clipStart':None ,
                'clipStop': None,
                'startPos': None,
                'stopPos': None,
                'ee_diff': None
            }
        # 收集tones
        tones_start = max(current_frame-tone_extend_rad, 0)
        tones_end = min(current_frame+tone_extend_rad, wave.frameNum)
        tones_local_set = Tone.objects.filter(
            title=title,
            create_user_id=user_id,
            pos__range=(tones_start, tones_end-1)
        )
        tones_local = serializers.serialize("json", tones_local_set)

        # comb及combDescan音高参考
        reference = {}  # 算法支撑数据
        labeling_algorithms_conf = labelinfo.labelingalgorithmsconf_set.all()  # 算法支持数据配置
        start_ref = max(current_frame - extend_rad, 0)  # 起始位置
        end_ref = min(current_frame + extend_rad, end)  # 终止位置
        for algorithmsConf in labeling_algorithms_conf:
            reference_name = algorithmsConf.algorithms
            local_reference_clips = labelinfo.algorithmsclips_set.filter(
                algorithms=reference_name,
                startingPos__range=(current_frame-extend_rad, current_frame+extend_rad-1),
                length=1
            )
            primary_arr = np.zeros(end_ref-start_ref)  # 算法主数据
            for reference_clip in local_reference_clips:
                primary_arr[reference_clip.startingPos-start_ref] = pickle.loads(reference_clip.tar)[0]
            reference.update({reference_name: list(primary_arr)})
            if algorithmsConf.is_filter is True:
                reference_name = reference_name+"_filter"
                filter_arr = np.zeros(end_ref - start_ref)  # 算法主数据
                for reference_clip in local_reference_clips:
                    filter_arr[reference_clip.startingPos-start_ref] = pickle.loads(reference_clip.tar)[1]
                reference.update({reference_name: list(filter_arr)})
        target = [[0] * (end_ref-start_ref), [0] * (end_ref-start_ref), [0] * (end_ref-start_ref)]  # 存储前三个音高的二维数组
        try:
            clips = Clip.objects.filter(
                title=title, create_user_id=request.user,
                startingPos__range=(current_frame-extend_rad, current_frame+extend_rad-1)
            )
            for clip in clips:
                pos = clip.startingPos
                tar = pickle.loads(clip.tar)
                index = 0
                for pitch in tar:
                    target[index][pos-start_ref] = pitch
                    index = index+1
        except Exception as e:
            pass
        # fft及中间结果
        # fft_range=list(range(extend_rad*2))
        try:
            src_fft = pickle.loads(labelinfo.stft_set.get(startingPos=current_frame, length=1).src)
            src_fft[0:int(30 * nfft / fs)] = 0  # 清空30hz以下信号
            filter_rad = labelinfo.filter_rad  # 过滤带宽半径
            current_clip = labelinfo.algorithmsclips_set.get(
                algorithms=labelinfo.primary_ref,
                startingPos=current_frame,
                length=1
            )
            #
            labeling_algorithms_conf_primary = labelinfo.labelingalgorithmsconf_set.get(
                algorithms=labelinfo.primary_ref
            )
            if labeling_algorithms_conf_primary.is_filter is True:
                current_tar = pickle.loads(current_clip.tar)  # 当前帧主音高估计
            else:
                current_tar = [pickle.loads(current_clip.tar)[0]]
            if current_tar[0] > 40:
                filter_fft = filter_by_base(src_fft, current_tar[0], filter_rad, nfft, fs)  # 过滤后fft
                filter_fft = [round(i, 4) for i in filter_fft]
            else:
                filter_fft = []
            medium = pickle.loads(
                labelinfo.algorithmsmediums_set.get(
                    algorithms=labelinfo.primary_ref,
                    startingPos=current_frame,
                    length=1
                ).medium
            )
            # 重新采样(降低采样), 只降低中间结果
            is_resampling = labelinfo.medium_resampling
            if is_resampling is True:
                processing_x = np.arange(0, len(medium))
                len_processing_x = len(processing_x)
                processing_y = medium
                finterp = interp1d(processing_x, processing_y, kind="linear")

                x_pred = np.linspace(
                    0, processing_x[len_processing_x - 1] * 1.0,
                    int(processing_x[len_processing_x - 1] / 10) + 1
                )
                resampling_y = finterp(x_pred)
                medium = resampling_y
                src_fft = [round(i, 4) for i in src_fft]
                medium = [round(i, 4) for i in medium]
        except Exception as e:
            medium = []
            src_fft = []
            filter_fft = []
            current_tar = [0]
            filter_rad = 0
            print(e)
        # 可能的位置
        chin = None
        string_hzes = None
        string_notes = None
        string_do = None
        pitch_scaling = None
        a4_hz = None
        if wave.chin is not None:
            # 获得chin class
            try:
                chin = pickle.loads(wave.chin)
                a4_hz = chin.get_ahz()
                string_hzes = chin.get_hzes()
                string_notes = chin.get_notes()
                string_do = chin.get_do()
                pitch_scaling = chin.get_scaling()
            except Exception as e:
                pitch_scaling = 1
        else:
            # chin class 不存在
            chin = None
        possible_pos = list()
        if chin is not None:
            try:
                possible_list = chin.cal_possiblepos(current_tar)[1]
                for possible in possible_list:
                    possible_pos.append(possible.replace("\n", "<br>"))
            except Exception as e:
                print(e)
        else:
            possible_pos.append("尚未设置chin信息")
        while len(possible_pos)<2:
            possible_pos.append("")
        clips_local_ori = Clip.objects.filter(
            title=title, create_user_id=user_id,
            startingPos__range=(current_frame-extend_rad, current_frame+extend_rad-1)
        )
        clips_local = []
        try:
            for clip in clips_local_ori:
                clips_local.append({
                    "id": clip.id,
                    "startingPos": clip.startingPos,
                    "length": clip.length,
                    "tar": list(pickle.loads(clip.tar))
                })
        except Exception as e:
            print(e)
        tunes = None
        try:
            tunes = Tune.objects.filter(create_user_id=request.user)
        except Exception as e:
            print(e)
        context = {
            'title': title,
            'fs': fs,
            'nfft': nfft,
            'ee': ee,
            'rmse': rmse,
            'stopPos': vadrs['stopPos'],
            'tunes': tunes,
            'manual_pos': manual_pos,
            'tones_local': tones_local,
            'target': target,
            'reference': reference,
            'primary_ref': labelinfo.primary_ref,
            'startPos': vadrs['startPos'],
            'ee_diff': vadrs['ee_diff'],
            # "fft_range":list(fft_range),
            "src_fft": list(src_fft),
            "medium": list(medium),
            'filter_fft': list(filter_fft),
            'current_tar': current_tar[0],
            "filter_rad": filter_rad,
            'a4_hz': a4_hz,
            'wave_id': wave_id,
            'string_hzes': string_hzes,
            'string_notes': string_notes,
            'string_do': string_do,
            'pitch_scaling': pitch_scaling,
            "current_frame": current_frame,
            "extend_rad": extend_rad,
            "labeling_id": labelinfo.id,
            'play_fs': labelinfo.play_fs,
            "tone_extend_rad": tone_extend_rad,
            "frame_num": end,
            'vad_thrart_ee': thrart_ee,
            "clips_local": clips_local,
            'vad_thrart_RMSE': thrart_rmse,
            'vad_throp_EE': throp,
            'create_user_id': user_id,
            'possible_pos': possible_pos
        }
        return render(request, 'labeling.html', context)

    @method_decorator(login_required)
    def get_spectrogram(self, request):
        labeling_id = int(request.GET.get('labeling_id'))
        current_frame = int(request.GET.get('current_frame'))
        try:
            labelinfo = Labeling.objects.get(id=labeling_id)
            extend_rad = labelinfo.extend_rad
            nfft = labelinfo.nfft
            fs = labelinfo.fs
            stft_set=labelinfo.stft_set.filter(startingPos__range=(current_frame-extend_rad,current_frame+extend_rad-1),length=1)
            counter=0
            fft_range=list(range(stft_set.count()))
            for stft in stft_set:
                stft_src=list(pickle.loads(stft.src)[0:int(4000*nfft/fs)])
                stft_src = [round(i, 4) for i in stft_src]
                fft_range[counter]=stft_src
                counter=counter+1
            max_fft_range_medium=max(fft_range)
            max_fft_range = max(max_fft_range_medium)
            min_fft_range_medium=min(fft_range)
            min_fft_range = min(min_fft_range_medium)
            context = {
                'number': int(counter),
                'length': int(4000*nfft/fs),
                "spectrogram": fft_range,
                "max_fft_range": max_fft_range,
                "min_fft_range": min_fft_range
            }
            return HttpResponse(json.dumps(context, cls=NpEncoder))
        except Exception as e:
            print(e)
            return None

    @method_decorator(login_required)
    def cal_pitch_pos(self, request):
        title = request.GET.get('title')
        user_id = str(request.user)
        primary_pitch = float(request.GET.get('primary_pitch'))
        wave = Wave.objects.get(create_user_id=user_id, title=title)
        pitch_array = []
        pitch_array.append(primary_pitch)
        if wave.chin is not None:
            # 获得chin class
            chin = pickle.loads(wave.chin)
        else:
            # chin class 不存在
            chin = None
        if chin is not None:
            possible_pos = chin.cal_possiblepos(pitch_array)[1][0].replace("\n", "<br>")
        else:
            possible_pos = "尚未设置chin信息"
        return HttpResponse(possible_pos)

    @method_decorator(login_required)
    def tune_reset(self, request):
        try:
            wave_id = request.GET.get('wave_id')
            tune_id = request.GET.get('tune_id')
            tune = Tune.objects.get(id=tune_id)
            wave = Wave.objects.get(id=wave_id)
            chin = Chin()
            chin.set_ahz(tune.a4_hz)
            chin.set_do(tune.do)

            notes = [tune.note1, tune.note2, tune.note3, tune.note4, tune.note5, tune.note6, tune.note7]
            chin.set_notes(notes)
            wave.chin = pickle.dumps(chin)
            wave.save()
        except Exception as e:
            print(e)
            return HttpResponse(e)
        return HttpResponse("ok")

    @method_decorator(login_required)
    def filter_fft(self, request):
        current_pos = int(request.GET.get('current_pos'))
        labeling_id = int(request.GET.get('labeling_id'))
        filter_frq = float(request.GET.get('filter_frq'))
        filter_width = float(request.GET.get('filter_width'))
        nfft = int(request.GET.get('nfft'))
        fs = int(request.GET.get('fs'))
        try:
            labeling = Labeling.objects.get(id=labeling_id)
            src_fft = pickle.loads(labeling.stft_set.get(startingPos=current_pos, length=1).src)
            src_fft[0:int(30 * nfft / fs)] = 0  # 清空30hz以下信号
            fft_filtered = filter_by_base(src_fft, filter_frq, filter_width, nfft, fs).tolist()  # 过滤后fft
            fft_filtered_round = [round(i, 2) for i in fft_filtered]
            return HttpResponse(json.dumps(fft_filtered_round))
        except Exception as e:
            print(e)
            return None

    # 自定义重新采样函数
    @staticmethod
    def resampling(src, target_len):
        processing_x = np.arange(0, len(src))
        len_processing_x = len(processing_x)
        processing_y = src
        finterp = interp1d(processing_x, processing_y, kind="linear")
        x_pred = np.linspace(0, processing_x[len_processing_x - 1] * 1.0, int(target_len) + 1)
        resampling_y = finterp(x_pred)
        return resampling_y

    @method_decorator(login_required)
    def cal_custom_pitch(self, request):
        title = request.GET.get('title')
        user_id = str(request.user)
        nfft = int(request.GET.get('nfft'))
        fs = int(request.GET.get('fs'))
        start = int(request.GET.get('start'))
        end = int(request.GET.get('end'))
        labeling_id = int(request.GET.get('labeling_id'))
        try:
            pitch=[]
            possible_pos=[]
            wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  #
            wave_len = len(wave_arr)
            wave_fft_src = fft(wave_arr)  # 自定义序列的fft
            wave_fft = abs(wave_fft_src)[0:int((len(wave_fft_src)+1)/2)]
            target_len = 2205
            labeling = Labeling.objects.get(id=labeling_id)
            algorithms_name = labeling.primary_ref
            detector = None
            
            if algorithms_name == "combDescan":
                detector = BaseFrqDetector(True)  # 去扫描线算法
            if algorithms_name == "comb":
                detector = BaseFrqDetector(False)  # 不去扫描线算法
            reference_pitch_allinfo = detector.getpitch(wave_fft, fs, wave_len, False)
            src = TargetView.resampling(wave_fft, target_len)[0:int(4000*4410/fs)]  # 重新采样后的适合显示的fft
            primary_pitch = reference_pitch_allinfo[0]  # 主音高
            medium = reference_pitch_allinfo[2]  # 中间结果
            pitch.append(primary_pitch)
            is_resampling = labeling.medium_resampling
            if is_resampling is True:
                medium = TargetView.resampling(medium, int(len(medium)/10))
            if primary_pitch > 40:
                filter_fft = filter_by_base(src, primary_pitch, labeling.filter_rad, nfft, fs)  # 过滤后fft
                filter_pith_allinfo = detector.getpitch(filter_fft, fs, wave_len, False)
                pitch.append(filter_pith_allinfo[0])
                filter_fft = [round(i, 4) for i in filter_fft]
            else:
                filter_fft = []
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            if wave.chin is not None:
                chin = pickle.loads(wave.chin)
            else:
                chin = None
            possible_pos_set = chin.cal_possiblepos(pitch)[1]
            for pos in possible_pos_set:
                possible_pos.append(pos.replace("\n", "<br>"))
            while(len(possible_pos)<2):
                possible_pos.append("")
            context = {
                'primary_pitch': primary_pitch, 'src': list(src), 'filter_fft': filter_fft,
                'medium': list(medium),
                "possible_pos": list(possible_pos)
            }
            return HttpResponse(json.dumps(context))
        except Exception as e:
            print(e)
            return None

    @method_decorator(login_required)
    def algorithm_select(self, request):
        algorithms_name = request.GET.get('algorithm_name')
        labeling_id = int(request.GET.get('labeling_id'))
        labeling = Labeling.objects.get(id=labeling_id)
        clips = labeling.algorithmsclips_set.filter(algorithms=algorithms_name)
        clips_num = clips.count()
        frame_num = labeling.frameNum
        context = {'clips_num': clips_num, 'frame_num': frame_num}
        return HttpResponse(json.dumps(context))

    @method_decorator(login_required)
    def algorithm_clear(self, request):
        clips_num = 0
        try:
            algorithms_name = request.GET.get('algorithm_name')
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            clips_all = labeling.algorithmsclips_set.filter(algorithms=algorithms_name)
            clips_num = clips_all.count()
            clips_all.delete()
        except Exception as e:
            print(e)
        context = {'clips_num_delete': clips_num}
        return HttpResponse(json.dumps(context))

    @staticmethod
    def algorithm_cal_thread(labeling, detector, stft_arr, rmse_arr, fs, nfft, algorithms_name, pool):
        for i in range(len(stft_arr)):
            stft = np.copy(stft_arr[i])
            stft[0:int(30*nfft/fs)] = 0
            args={
                "create_user_id":labeling.create_user_id,
                "title":labeling.title,
                "detector":detector,
                "stft_arr":stft, 
                "rmse":rmse_arr[i], 
                "fs":fs, 
                "nfft":nfft, 
                "algorithms_name":algorithms_name,
                "index":i,
                "labeling_id":labeling.id
            }

            # key = "ref_"+str(labeling.title)+"_"+str(algorithms_name)+"_"+str(fs)+"_"+str(nfft)+"_"+str(i)
            # cache.set(key, args, nx=True)
            # cache.expire(key, 3600*72)
            red = redis.Redis(connection_pool=pool)
            red.rpush("refTask", pickle.dumps(args))  # 此处不做重复性检查


    @method_decorator(login_required)
    def algorithm_cal(self, request):
        try:
            clips_num_oncreate = 0
            algorithms_name = request.GET.get('algorithm_name')
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)

            clips_all = labeling.algorithmsclips_set.filter(algorithms=algorithms_name)
            clips_num = clips_all.count()
            clips_all.delete()
            # print("删除算法参考数据"+str(algorithms_name)+str(clips_num)+"条")
            medium_all = labeling.algorithmsmediums_set.filter(algorithms=algorithms_name)
            medium_all.delete()
            # print("删除算法中间结果" + str(algorithms_name) + str(clips_num) + "条")
            # 创建数据
            clips_num_oncreate = labeling.frameNum  # 需要创建数据总条目
            user_id = labeling.create_user_id
            title = labeling.title
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            fs = labeling.fs
            nfft = labeling.nfft
            # stft_arr = self.wave_mem_stft.achieve(user_id, title, fs, nfft, 0, 0)  # 短时傅里叶谱
            # 获取原始左声道波形
            # 获取stft
            stream ,sr = soundfile.read(wave.waveFile)
            stream = stream[:,0]
            stream = np.ascontiguousarray(stream, dtype=np.float32)
            stft_arr, phase = librosa.magphase(
                librosa.stft(
                    stream, n_fft=wave.nfft,
                    hop_length=wave.nfft,
                    window=scipy.signal.windows.hann,
                    center=False
                )
            )
            stft_arr = np.transpose(stft_arr)  # stft转置'''a
            rmse_arr = librosa.feature.rmse(
                y=stream,
                S=None,
                frame_length=nfft,
                hop_length=nfft,
                center=False
            )[0]
            detector = None
            rmse_arr = maxminnormalization(rmse_arr, 0, 1)
            if algorithms_name == "combDescan":
                detector = BaseFrqDetector(True)  # 去扫描线算法
            if algorithms_name == "comb":
                detector = BaseFrqDetector(False)  # 不去扫描线算法
            thread = threading.Thread(
                target=self.algorithm_cal_thread,
                args=(labeling, detector, stft_arr, rmse_arr, fs, nfft, algorithms_name, self.redis_pool)
            )  # 创建监视线程
            thread.setDaemon(True)  # 设置为守护线程， 一旦用户线程消失，此线程自动回收
            thread.start()
        except Exception as e:
            print(e)
            return HttpResponse("")
        finally:
            context = {'clips_num_oncreate': clips_num_oncreate}
            return HttpResponse(json.dumps(context))

    @method_decorator(login_required)
    def reference_select(self, request):
        algorithms_name = request.GET.get('algorithm_name')
        labeling_id = int(request.GET.get('labeling_id'))
        labeling = Labeling.objects.get(id=labeling_id)
        algorithms_clips = labeling.labelingalgorithmsconf_set.filter(algorithms=algorithms_name)
        algorithms_num = algorithms_clips.count()
        context = {'algorithms_num': algorithms_num}
        return HttpResponse(json.dumps(context))

    @method_decorator(login_required)
    def add_reference(self, request):
        try:
            algorithms_name = request.GET.get('algorithm_name')
            labeling_id = int(request.GET.get('labeling_id'))
            is_filter = int(request.GET.get('is_filter'))
            if is_filter == 0:
                is_filter = False
            if is_filter == 1:
                is_filter = True
            labeling = Labeling.objects.get(id=labeling_id)
            newlabeling_algorithms_conf = LabelingAlgorithmsConf(
                labeling=labeling,
                algorithms=algorithms_name,
                is_filter=is_filter
            )
            newlabeling_algorithms_conf.save()
        except Exception as e:
            print(e)
        return HttpResponse("reference added ")

    # 删除算法支持数据配置
    @method_decorator(login_required)
    def del_reference(self, request):
        try:
            algorithms_name = request.GET.get('algorithm_name')
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            labeling_algorithms_conf = labeling.LabelingAlgorithmsConf_set.get(algorithms=algorithms_name)
            labeling_algorithms_conf.delete()
        except Exception as e:
            print(e)
        return HttpResponse("reference deleted ")

    @method_decorator(login_required)
    def cal_stft(self, request):
        try:
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            labeling.stft_set.all().delete()
            user_id = str(request.user)
            # wave_key = user_id + "_" + labeling.title + "_" + "stft"  # 例子 pi_秋风词_stft
            wave = Wave.objects.get(create_user_id=user_id, title=labeling.title)
            # 获取原始左声道波形
            # stream = librosa.load(wave.waveFile, mono=False, sr=wave.fs, res_type="kaiser_fast")[0][0]  # 以Fs重新采样
            stream ,sr = soundfile.read(wave.waveFile)
            stream = stream[:,0]
            stream = np.ascontiguousarray(stream, dtype=np.float32) 
            # 获取stft
            speech_stft, phase = librosa.magphase(
                librosa.stft(
                    stream,
                    n_fft=wave.nfft,
                    hop_length=wave.nfft,
                    window=scipy.signal.windows.hann,
                    center=False
                )
            )
            speech_stft = np.transpose(speech_stft)  # stft转置
            # 此处的stft仅仅为了求谱熵等，因此不需要特别长的生存时间，谱熵缓存可设置长一点
            '''mem_item = MemItemStft(
                user_id,
                labeling.title,
                labeling.fs,
                labeling.nfft,
                speech_stft,
                timedelta(minutes=5)
            )
            self.wave_mem_stft.container.set(wave_key, mem_item)'''

            stft_arr = speech_stft
            # 短时傅里叶谱
            list_stft = []
            for i in range(len(stft_arr)):
                stft = Stft(startingPos=i, length=1, labeling=labeling, src=pickle.dumps(stft_arr[i]))
                list_stft.append(stft)
            labeling.stft_set.bulk_create(list_stft)
            labeling.frameNum = len(stft_arr)
            labeling.save()
            wave.frameNum = len(stft_arr)
            wave.save(update_fields=["frameNum"])
        except Exception as e:
            print(e)
            return HttpResponse("STFT ERR")
        return HttpResponse("STFT calculated ")

    @method_decorator(login_required)
    def cal_ee(self, request):
        try:
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            user_id = labeling.create_user_id
            title = labeling.title
            fs = labeling.fs
            nfft = labeling.nfft
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            # 获取原始左声道波形
            # stream = self.wave_mem_wave.achieve(user_id, title, fs, nfft, 0, 0)
            # stream = librosa.load(wave.waveFile, mono=False, sr=fs, res_type="kaiser_fast")[0][0]  # 以Fs重新采样
            stream ,sr = soundfile.read(wave.waveFile)
            stream = stream[:,0]
            stream = np.ascontiguousarray(stream, dtype=np.float32) 
            # 获取stft
            speech_stft, phase = librosa.magphase(
                librosa.stft(
                    stream,
                    n_fft=nfft,
                    hop_length=nfft,
                    window=scipy.signal.windows.hann,
                    center=False
                )
            )
            stft_ori = speech_stft  # stft转置
            # 计算谱熵
            stft_for_ee = np.copy(stft_ori[0:np.int(nfft / fs * 4000)])  # 4000hz以下信号用于音高检测
            speech_stft_enp = stft_for_ee[1:-1]
            speech_stft_prob = speech_stft_enp / (np.sum(speech_stft_enp, axis=0) + 0.00000000000000001)
            spectrum_entropy = np.sum(
                -np.log(speech_stft_prob + 0.0000000000000001) * speech_stft_prob,
                axis=0
            )
            spectrum_entropy = maxminnormalization(spectrum_entropy, 0, 1)
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            wave.ee = pickle.dumps(spectrum_entropy)
            wave.save(update_fields=["ee"])

        except Exception as e:
            print(e)
            return HttpResponse("EE ERR")
        return HttpResponse("EE calculated ")

    @method_decorator(login_required)
    def cal_rmse(self, request):
        try:
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            user_id = labeling.create_user_id
            title = labeling.title
            fs = labeling.fs
            nfft = labeling.nfft
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            # stream = self.wave_mem_wave.achieve(user_id, title, fs, nfft, 0, 0)
            #stream = librosa.load(wave.waveFile, mono=False, sr=fs, res_type="kaiser_fast")[0][0]  # 以Fs重新采样
            stream ,sr = soundfile.read(wave.waveFile)
            stream = stream[:,0]
            stream = np.ascontiguousarray(stream, dtype=np.float32) 
            rmse = librosa.feature.rmse(
                y=stream,
                S=None,
                frame_length=nfft,
                hop_length=nfft,
                center=False
            )[0]
            rmse = maxminnormalization(rmse, 0, 1)
            wave = Wave.objects.get(create_user_id=user_id, title=title)
            wave.rmse = pickle.dumps(rmse)
            wave.frameNum = len(rmse)
            wave.save(update_fields=["rmse", "frameNum"])
            labeling.frameNum = len(rmse)
            labeling.save(update_fields=["frameNum"])
        except Exception as e:
            print(e)
            return HttpResponse("RMSE ERR")
        return HttpResponse("RMSE calculated ")

    @method_decorator(login_required)
    def set_primary(self, request):
        try:
            algorithms_name = request.GET.get('algorithm_name')
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            labeling.primary_ref = algorithms_name
            labeling.save()
        except Exception as e:
            print(e)
        return HttpResponse("primary set ")

    @method_decorator(login_required)
    def set_ref_filter(self, request):
        try:
            algorithms_name = request.GET.get('algorithm_name')
            labeling_id = int(request.GET.get('labeling_id'))
            is_filter = int(request.GET.get('is_filter'))
            if is_filter == 0:
                is_filter = False
            if is_filter == 1:
                is_filter = True
            labeling = Labeling.objects.get(id=labeling_id)
            labeling_conf = labeling.labelingalgorithmsconf_set.get(algorithms=algorithms_name)
            labeling_conf.is_filter = is_filter
            labeling_conf.save()
        except Exception as e:
            print(e)
        return HttpResponse("primary filter configure set ")

    @method_decorator(login_required)
    def set_manual_pos(self, request):
        try:
            manual_pos = int(request.GET.get('manual_pos'))
            labeling_id = int(request.GET.get('labeling_id'))
            labeling = Labeling.objects.get(id=labeling_id)
            labeling.manual_pos = manual_pos
            labeling.save(update_fields=['manual_pos'])
        except Exception as e:
            print(e)
            return HttpResponse("err")
        return HttpResponse("ok")

    @classmethod
    @method_decorator(login_required)
    def wave_view(cls, request):
        """
        曲目视图
        此函数返回统计过的pitches数组
        :return:
        """
        class Item:
            title = ""
            length = 0
            tar = None
        title = request.GET.get('title')
        create_user = str(request.user)
        wave = Wave.objects.get(create_user_id=create_user, title=title)
        clips = Clip.objects.filter(
            title=title,
            create_user_id=request.user,
            startingPos__lt=wave.frameNum
        ).order_by('startingPos')
        marked_phrases = MarkedPhrase.objects.filter(create_user_id=create_user, title=title)
        tones = Tone.objects.filter(create_user_id=create_user, title=title).order_by('pos')
        # 返回的clips
        items = []
        # 存储前三个音高的二维数组
        pitches_arr = [[0] * wave.frameNum, [0] * wave.frameNum, [0] * wave.frameNum]
        # pitches_arr = [pitches_arr]

        if wave.chin is not None:
            chin = pickle.loads(wave.chin)
        else:
            chin = None

        for clip in clips:
            item = Item()
            item.title = clip.title
            item.startingPos = clip.startingPos
            item.tar = pickle.loads(clip.tar)
            for index in np.arange(len(item.tar)):
                item.tar[index] = round(item.tar[index], 2)
            item.possible_pos = chin.cal_possiblepos(item.tar)[1][0].replace("\n", "<br>")
            item.id = clip.id
            for index in np.arange(len(item.tar)):
                try:
                    pitches_arr[index][clip.startingPos] = item.tar[index]  # 收集已经标定的音高
                except Exception as e:
                    print(e)
            items.append(item)
        string_notes = None
        string_hzes = None
        string_do = None
        if wave.chin is not None:
            try:
                string_hzes = chin.get_hzes()
                string_notes = chin.get_notes()
                string_do = chin.get_do()
            except Exception as e:
                string_hzes = None
                string_notes = None
                string_do = None
                print(e)

        context = {
            'clips': items, 'wave': wave, 'pitches': pitches_arr, 'marked_phrases': marked_phrases,
            'tones': tones, 'string_hzes': string_hzes, 'string_notes': string_notes,
            'string_do': string_do
        }
        return render(request, 'wave.html', context)

    def get_phrase(self, request):
        """
        获取音乐片段
        :return:音乐片段wav格式2进制流
        """
        try:
            user_id = str(request.user)
            title = request.GET.get('title')
            start = int(request.GET.get('start'))
            end = int(request.GET.get('end'))
            nfft = int(request.GET.get('nfft'))
            fs = int(request.GET.get('fs'))

            # self.wave_mem.add_mem(title)  # 试图将完整曲目加入缓存
            wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  # 获取音频信号
            wave_arr = np.array(wave_arr) * 32767
            wave_arr = wave_arr.astype(np.int16)
            io_stream = BytesIO()  # 内存文件

            f = waveout.open(io_stream, 'wb')  # 定位于内存镜像
            f.setnchannels(1)  # 设置为单通道
            f.setsampwidth(2)  # 16位采样
            f.setframerate(fs)  # 设置采样率
            # 将wav_data转换为二进制数据写入文件
            f.writeframes(wave_arr.tostring())  # 写入音频信息
            f.close()  # 关闭写入流
            seg = AudioSegment.from_wav(io_stream)
            io_stream_flac = BytesIO()  # 内存文件
            seg.export(io_stream_flac, format='wav')
            blob_ori = io_stream_flac.getvalue()
            return HttpResponse(blob_ori)

        except Exception as e:
            print(e)
            return None

    def post_phrase(self, request):
        """
        获取音乐片段
        :return:音乐片段wav格式2进制流
        """
        user_id = str(request.user)
        title = request.GET.get('title')
        start = int(request.GET.get('start'))
        end = int(request.GET.get('end'))
        nfft = int(request.GET.get('nfft'))
        fs = int(request.GET.get('fs'))
        email_file_name = request.GET.get('file_name')
        # self.wave_mem.add_mem(title)  # 试图将完整曲目加入缓存
        wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  # 获取音频信号
        wave_arr = np.array(wave_arr) * 32767
        wave_arr = wave_arr.astype(np.int16)
        io_stream = BytesIO()  # 内存文件
        f = waveout.open(io_stream, 'wb')  # 定位于内存镜像
        f.setnchannels(1)  # 设置为单通道
        f.setsampwidth(2)  # 16位采样
        f.setframerate(fs)  # 设置采样率
        # 将wav_data转换为二进制数据写入文件
        f.writeframes(wave_arr.tostring())  # 写入音频信息
        f.close()  # 关闭写入流"""
        subject = email_file_name  # 主题
        wav_patch = MIMEApplication(io_stream.getvalue())
        wav_patch.add_header(
            'Content-Disposition', 'attachment',
            filename=('gbk', '', email_file_name + '.wav')
        )
        msg = wav_patch
        msg['Subject'] = subject
        msg['From'] = self.msg_from
        msg['To'] = self.msg_to
        self.sender = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
        self.sender.login(self.msg_from, self.passwd)
        self.sender.sendmail(self.msg_from, self.msg_to, msg.as_string())
        return HttpResponse("posted")

    @method_decorator(login_required)
    def labeling_reset(self, request):
        wave_title = request.GET.get('title')
        extend_rad = int(request.GET.get('extend_rad'))
        tone_extend_rad= int(request.GET.get('tone_extend_rad'))
        vad_thrart_ee= float(request.GET.get('vad_thrart_ee'))
        vad_throp_ee= float(request.GET.get('vad_throp_ee'))
        vad_thrart_rmse= float(request.GET.get('vad_thrart_rmse'))
        user_id = request.GET.get('create_user_id')
        labeling = Labeling.objects.get(create_user_id=user_id,title=wave_title)
        labeling.extend_rad=extend_rad
        labeling.tone_extend_rad=tone_extend_rad
        labeling.vad_thrart_EE=vad_thrart_ee
        labeling.vad_throp_EE=vad_throp_ee
        labeling.vad_thrart_RMSE=vad_thrart_rmse
        labeling.save()
        return HttpResponse("labeling reset done")

    @classmethod
    def db_access(cls, request):
        operation = request.GET.get('operation')  # 操作类型
        class_name = request.GET.get('class')  # 数据类型
        item_id = request.GET.get('id')  # 数据id
        rs = "ok"
        # 删除操作
        if operation == "delete":
            if class_name == "tone":
                item = Tone.objects.get(id=item_id)
                item.delete()
            if class_name == "clip":
                if request.user.has_perm('target.delete_clip'):  # 检查用户是否具有delete权限
                    item = Clip.objects.get(id=item_id)
                    item.delete()
                else:
                    rs = "err"
        return HttpResponse(rs)

    @classmethod
    def get_clip_fft(cls, request):
        clip_id = request.GET.get('id')  # clip_id
        fs = int(request.GET.get('fs'))  # fs
        nfft = int(request.GET.get('nfft'))  # nfft
        try:
            clip = Clip.objects.get(id=clip_id)
        except Exception as e:
            return HttpResponse(e)

        cutoff = int(4200 * nfft / fs)  # src 截断位置
        src = pickle.loads(clip.src)
        src = src.tolist()[0:cutoff]
        return HttpResponse(json.dumps(src))

    @staticmethod
    def cal_size(w, h, w_box, h_box):
        '''
        resize a pil_image object so it will fit into
        a box of size w_box times h_box, but retain aspect ratio
        对一个pil_image对象进行缩放，让它在一个矩形框内，还能保持比例
        '''
        if ((w-h)*(w_box-h_box))<0:
            w_box,h_box=h_box,w_box    
        f1 = 1.0*w_box/w # 1.0 forces float division in Python2
        f2 = 1.0*h_box/h
        factor = min([f1, f2])
        #print(f1, f2, factor) # test
        # use best down-sizing filter
        width = int(w*factor)
        height = int(h*factor)
        return [width, height]

    @method_decorator(login_required)
    def ocr_labeling(self, request):
        try:
            ocrpdf_id = request.GET.get('id')  # ocrpdf_id
            ocrpdf = OcrPDF.objects.get(id=ocrpdf_id)
            current_frame = 0
            if ocrpdf.create_user_id == str(request.user):
                current_frame = ocrpdf.current_frame
            else:
                current_frame = ocrpdf.ocrassist_set.get(assist_user_name=str(request.user)).current_frame
            ocrimage = ocrpdf.pdfimage_set.get(frame_id=current_frame)
            polygon_set = ocrimage.ocrlabelingpolygon_set.all()
            create_user_id_set = polygon_set.values("create_user_id").distinct()  # achieve distinct create_user_id 
            # build a dictionary with create_user_id as its key and polygon list as its value
            polygon_dict = dict()
            for create_user_id in create_user_id_set:
                polygon_dict[create_user_id["create_user_id"]] = list()  # initialized as an empty list
                
            for polygon in polygon_set:
                polygon_dict[polygon.create_user_id].append(
                    {
                        "polygon_id":polygon.id,
                        "image_id":polygon.pdfImage.id,
                        "create_user_id":polygon.create_user_id,  # redundant data for a verification
                        "points":str(polygon.polygon,'utf-8')
                    }
                )
            
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0})
            context={
                "image_id":ocrimage.id,
                "title":ocrpdf.title,
                "ocr_pdf_id":ocrpdf.id,
                "frame_id":ocrimage.frame_id,
                "frame_num":ocrpdf.frame_num,
                "ori_width":ocrimage.width,
                "ori_height":ocrimage.height,
                "polygon_dict":json.dumps(polygon_dict),
                "current_rotate":image_user_conf.rotate_degree
            }
            return render(request, 'ocr_labeling.html', context)
        except Exception as e:
            print("ocr_labeling:"+str(e))
            return render(request, 'ocr_labeling.html', None)

    @method_decorator(login_required)
    def ocr_get_image(self, request):
        try:
            ocrimage=PDFImage.objects.get(id=request.GET['frame_id'])        
            tar_width = int(request.GET.get('tar_width'))
            tar_height = int(request.GET.get('tar_height'))
            data_stream=io.BytesIO(ocrimage.data_byte)
            pil_image = Image.open(data_stream)
            width, height = pil_image.size
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0})
            if abs(image_user_conf.rotate_degree)>0.0001:
                image_rotated = pil_image.rotate(image_user_conf.rotate_degree)
            else:
                image_rotated = pil_image
            image_resized = image_rotated.resize((tar_width, tar_height), Image.ANTIALIAS)
            trans_width,trans_height=image_resized.size
            new_imageIO = BytesIO() 
            image_resized.save(new_imageIO,"JPEG")
            data_byte=new_imageIO.getvalue()
            return HttpResponse(data_byte, 'image/jpeg')
            
        except Exception as e:
            print(e)
            return None

    @method_decorator(login_required)
    def ocr_move_page(self, request):
        try:
            page_apointed = int(request.GET.get("page_apointed"))
            ocr_pdf_id = int(request.GET.get("ocr_pdf"))
            ocr_pdf=OcrPDF.objects.get(id=ocr_pdf_id)
            if str(request.user) == ocr_pdf.create_user_id:
                ocr_pdf.current_frame = page_apointed
                ocr_pdf.save()
            else:
                ocr_assist = ocr_pdf.ocrassist_set.get(assist_user_name=str(request.user))
                ocr_assist.current_frame = page_apointed
                ocr_assist.save()
            
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @method_decorator(login_required)
    def add_labeling_polygon(self, request):
        try:
            pointsStr = request.GET.get("points")
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            polygon = OcrLabelingPolygon(pdfImage=image, polygon=pointsStr.encode("utf-8"), create_user_id=str(request.user))
            polygon.save()
            polygon_id = polygon.id
            polygon_create_user_id = polygon.create_user_id
            context = {"polygon_id":polygon_id,"polygon_create_user_id":polygon_create_user_id}
            return HttpResponse(json.dumps(context))
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @staticmethod
    def get_rect_info(point_a, point_b):
        try:
             x = min(point_a['x'], point_b['x'])
             x_ = max(point_a['x'], point_b['x'])
             y = min(point_a['y'], point_b['y'])
             y_ = max(point_a['y'], point_b['y'])
             w = abs(x_-x)
             h = abs(y_-y)
             area = w*h
             return {'x':x, 'y':y, 'x_':x_, 'y_':y_, 'w':w, 'h':h, 'area':area}
        except Exception as e:
            print(e)

    # caculate intersection ratio
    @staticmethod
    def cal_intersection_ratio(rect_a, rect_b):
        try:
            dist_x = max(rect_a['x_'], rect_b['x_']) - min(rect_a['x'], rect_b['x'])
            dist_y = max(rect_a['y_'], rect_b['y_']) - min(rect_a['y'], rect_b['y'])
            w_intersection = max(rect_a['w']+rect_b['w']-dist_x , 0)
            h_intersection = max(rect_a['h']+rect_b['h']-dist_y , 0)
            area_intersection = w_intersection * h_intersection
            intersection_ratio_a = area_intersection / (rect_a['area']*1.0)
            intersection_ratio_b = area_intersection / (rect_b['area']*1.0)
            return {'ratio_a':intersection_ratio_a, 'ratio_b':intersection_ratio_b, 'area':area_intersection}
        except Exception as e:
            print(e)
    
    # delete labeles relate to an apointed region
    @method_decorator(login_required)
    def delete_region(self, request):
        delete_info = []
        try:
            select_pointsStr = request.GET.get("select_points")
            select_points = json.loads(select_pointsStr)  # region to be deleted
            image_id = request.GET.get("image_id")  # related picture
            image = PDFImage.objects.get(id=image_id) 
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user
            rect_region = TargetView.get_rect_info(select_points[0], select_points[2])

            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                rect_candidate = TargetView.get_rect_info(points[0], points[2])
                intersection = TargetView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                print(intersection_ratio)
                if intersection_ratio > 0.75:
                    delete_info.append({'polygon_id':polygon.id, 'rect_info':rect_candidate})
                    polygon.delete()
            return HttpResponse(json.dumps(delete_info))
        except Exception as e:
            print(e)
            return HttpResponse("err")


    # 删除当前当前用户进行的制定页面的标注
    @method_decorator(login_required)
    def delete_all_polygon(self, request):
        try:
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            item_delete = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))
            count = item_delete.count()
            item_delete.delete()
            return HttpResponse(count)
        except Exception as e:
            print(e)
            return HttpResponse("err")


    # rotate degree reset
    @method_decorator(login_required)
    def rotate_degree_reset(self, request):
        try:
            image_id = request.GET.get("image_id")
            rotate_degree = request.GET.get("rotate_degree")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            image_user_conf, isCreate = image.imageuserconf_set.get_or_create(create_user_id=str(request.user), defaults={"rotate_degree":rotate_degree})
            if isCreate==False:
                image_user_conf.rotate_degree=rotate_degree
                image_user_conf.save()
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @classmethod
    def login(cls, request):
        file_next = request.GET.get('next', "")
        if request.method == 'GET':
            if request.user is not None and request.user.is_active:
                return redirect("/index/")
            form = UserFormWithoutCaptcha()
            return render(request, 'login.html', {'login_form': form, })
        else:
            form = UserFormWithoutCaptcha(request.POST)
            if form.is_valid():
                username = request.POST.get('username', '')
                password = request.POST.get('password', '')
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    auth.login(request, user)
                    if file_next == "":
                        return redirect("/index/")
                    else:
                        return redirect(file_next)
                else:
                    message = "用户名或者密码错误"
                    return render(request, 'login.html', {'login_form': form, 'message': message})
            else:
                message = "表单数据错误"
                return render(request, 'login.html', {'login_form': form, 'message': message})

    @classmethod
    def logout(cls, request):
        auth.logout(request)
        return redirect("/login/")

    @classmethod
    def register(cls, request):
        message = ""
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            message = "请检查填写的内容！"
            if form.is_valid():
                # 获得表单数据
                username = form.cleaned_data['username']
                password = form.cleaned_data['password1']

                # 判断用户是否存在
                user = auth.authenticate(username=username, password=password)
                if user:
                    message = "用户已经存在"
                    return render(request, 'register.html', {'register_form': form, 'message': message})
                # 添加到数据库（还可以加一些字段的处理）
                user = TargetUser.objects.create_user(username=username, password=password)
                user.save()
                # 添加到session
                request.session['username'] = username
                # 调用auth登录
                auth.login(request, user)
                # 重定向到首页
                return redirect('/index')
            else:
                pass

        else:
            form = RegisterForm()
        # 将req 、页面 、以及context{}（要传入html文件中的内容包含在字典里）返回
        return render(request, 'register.html',  {'register_form': form, 'message': message})
