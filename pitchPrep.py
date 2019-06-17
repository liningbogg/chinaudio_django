'''
音高人工标记
音高参考信息预处理
为了节约标记时间

'''

from __future__ import print_function

import os
import pickle
import sys
from datetime import datetime

import django
import librosa.display
import numpy as np
import scipy
from scipy import signal

from baseFrqComb import BaseFrqDetector

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pitch.settings")  # project_name 项目名称django.setup()
django.setup()
from target.models import Clip
from django.contrib import auth

import multiprocessing


# 取得指定格式的dir列表
def filterListDir(path,fmt):
    dirList=os.listdir(path)
    filteredList=[]
    for name in dirList:
        spilted=os.path.splitext(name)
        if(spilted[1]==fmt):
            filteredList.append(name)
    return filteredList


np.set_printoptions(threshold=sys.maxsize, linewidth=np.nan)
class1_path = "/home/liningbo/文档/waveFiles/comb/"
class1_list=filterListDir(class1_path, '.flac')
class1_listLen=len(class1_list)
Fs = 44100
nfft = int(4410)  # 窗口尺寸
hopLength = int(nfft)  # 步长

showTestView = 0  # 是否逐帧显示fft过程,需要把所有弹出窗口均关闭，然后关闭一个fft窗口 就会弹出下一个（只会这么整了）
username1 = "comb"
username2 = "combDescan"
while True:
    password=input("passwordComb:")
    user1 = auth.authenticate(username=username1, password=password)

    if user1 is not None and user1.is_active:
        break
    else:
        print("密码错误")

while True:
    password = input("passwordoCombDescan:")
    user2 = auth.authenticate(username=username2, password=password)

    if user2 is not None and user2.is_active:
        break
    else:
        print("密码错误")

detectorDescan = BaseFrqDetector(True)  # 去扫描线算法
detector = BaseFrqDetector(False)  # 不去扫描线算法

# 目标标记程序流程
for index in range(0,class1_listLen):
    print(class1_list[index])
    startTime=datetime.now() 
    baseName=os.path.splitext(class1_list[index])[0]
    stream=librosa.load(class1_path+class1_list[index], mono=False, sr=Fs)#以Fs重新采样
    
    x=stream[0]
    print('sampling rate:',stream[1])#采样率
    speech_stft,phase = librosa.magphase(librosa.stft(x[0], n_fft=nfft, hop_length=hopLength, window=scipy.signal.hamming))
    rmse = \
    librosa.feature.rmse(y=x[0], S=None, frame_length=nfft, hop_length=hopLength, center=True, pad_mode='reflect')[0]
    rmse=BaseFrqDetector.maxminnormalization(rmse, 0, 1)
    speech_stft=np.transpose(speech_stft)
    referencePitch=[]
    referencePitchDeScan=[]
    filePath=baseName+'_%d'%Fs+'_%d/'%nfft

    for frame in np.arange(len(speech_stft)):
        print(baseName,[frame*nfft/Fs,"%.2f"%(frame/len(speech_stft)*100.0)]) #当前时刻
        dataClip=np.copy(speech_stft[frame])
        dataClip[0:int(30*nfft/Fs)] = 0  # 清零30hz以下信号
        pool = multiprocessing.Pool(processes=2)
        result1 = pool.apply_async(detector.getpitch, args=(dataClip, Fs, nfft, showTestView,))
        result2 = pool.apply_async(detectorDescan.getpitch, args=(dataClip, Fs, nfft, showTestView,))
        pool.close()
        pool.join()
        referencePitch = result1.get()
        referencePitchDeScan = result2.get()
        referencePitchDeScanFiltered = 0
        if referencePitchDeScan[0] > 65 and rmse[frame] > 0.1:
            filteredSGN = BaseFrqDetector.filterbybasefrq(dataClip, referencePitchDeScan[0], 30, Fs, nfft)
            Filtered = detector.getpitch(filteredSGN, Fs, nfft, showTestView)
            referencePitchDeScanFiltered = Filtered[0]
        DeScan = [referencePitchDeScan, referencePitchDeScanFiltered]  # 去扫描频率及其过滤后剩余频率
        try:
            tar = []
            tar.append(referencePitch[0])
            clip=Clip.objects.get(create_user_id=username1, title=baseName, startingPos=frame, length=1, nfft=nfft)
            clip.anote = "机器人_COMB"
            clip.tar = pickle.dumps(np.array(tar))
            clip.save(update_fields=["tar","anote"])
        except Clip.DoesNotExist:
            tar = []
            tar.append(referencePitch[0])
            newclip = Clip(create_user_id=username1, title=baseName, startingPos=frame, length=1, nfft=nfft)
            newclip.src = pickle.dumps(dataClip)
            newclip.anote = "机器人_COMB"
            newclip.tar = pickle.dumps(np.array(tar))
            newclip.save()

        try:
            tar = []
            tar.append(referencePitchDeScan[0])
            tar.append(referencePitchDeScanFiltered)
            clip=Clip.objects.get(create_user_id=username2, title=baseName, startingPos=frame, length=1, nfft=nfft)
            clip.anote = "机器人_COMBDESCAN"
            clip.tar = pickle.dumps(np.array(tar))
            clip.save(update_fields=["tar", "anote"])
        except Clip.DoesNotExist:
            tar = []
            tar.append(referencePitchDeScan[0])
            tar.append(referencePitchDeScanFiltered)
            newclip = Clip(create_user_id=username2, title=baseName, startingPos=frame, length=1, nfft=nfft)
            newclip.src = pickle.dumps(dataClip)
            newclip.anote = "机器人_COMBDESCAN"
            newclip.tar = pickle.dumps(np.array(tar))
            newclip.save()



    print(' 音高参考信息写入完毕')
    endTime = datetime.now()
    print('用时%d;' % (endTime-startTime).seconds
          + '帧数:%d;' % len(speech_stft)
          + 'spf:%f;' % ((endTime-startTime).seconds*1.0/len(speech_stft))
          + 'speed:%f' % ((endTime-startTime).seconds*1.0/(len(speech_stft))*Fs/nfft))
