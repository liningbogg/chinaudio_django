"""
音高人工标记
输入：fft数据，原始未有差值的傅里叶频谱
标签:不定数目音高，倍频 高音优先，其他的强信号优先
"""

from __future__ import print_function

import math
import os
import pickle
import sys
from datetime import datetime

import django
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import scipy
from django.db.models import Max
from scipy import signal
from scipy.interpolate import interp1d

import baseFrqCombScan
from chin import Chin
from findPeaks import findpeaks

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pitch.settings")  # project_name 项目名称django.setup()
django.setup()
from target.models import Clip
from target.models import Wave
from target.models import Tone
from target.models import Log
from target.models import MarkedPhrase
from scipy.fftpack import fft
import json
import jsonlines
from django.contrib import auth


# 播放波形
def playwave(dataplay):
    p = pyaudio.PyAudio()
    streamplay = p.open(format=pyaudio.paFloat32, channels=1, rate=Fs, output=True)  # 播放采用单声道
    streamplay.write(dataplay, num_frames=len(dataplay))  # 此处不是帧数的意思
    streamplay.stop_stream()
    streamplay.close()
    p.terminate()


# 取得指定后缀名的dir列表
def filterListDir(path, fmt):
    dirList = os.listdir(path)
    filteredList = []
    for namefile in dirList:
        spilted = os.path.splitext(namefile)
        if spilted[1] == fmt:
            filteredList.append(namefile)
    return filteredList


class1_path = "../dataFiltered/guqin9/"  # target路径
class1_list = filterListDir(class1_path, '.flac')  # 暂时测试这一种格式,后期有待修改
class1_listLen = len(class1_list)  # 文件列表长度
Fs = 44100  # 采样率
nfft = int(4410)  # 窗口尺寸
hopLength = int(nfft)  # 步长，目前暂时设置的跟nfft一样
rmseS = 1  # 是否显示瞬时能量
rmseDS = 0  # 是否显示瞬时能量diff
EES = 1  # 是否显示谱熵
EEDS = 1  # 是否显示谱熵梯度
MergeEEDS = 1  # 融合区域后的EEDS
showTestView = 0  # 是否逐帧显示fft过程,需要把所有弹出窗口均关闭，然后关闭一个fft窗口 就会弹出下一个（只会这么整了）
pitchExtend = 4  # 为了标注音高延申的数据长度，单位秒
toneShowWidth = 10  # 音高标记显示宽度


def addChche(pitch, pitchFilter, inputV, mediumV, initPos, length, file):
    """
    添加缓存
    :param pitch:候选音高数列
    :param inputV:原始输入数列
    :param mediumV:中间结果序列
    :param initPos:起始位置
    :param length:帧数
    :param file:输入文件
    :return:无返回
    """
    for indexcache in np.arange(initPos, initPos + length):
        try:
            if pitchFilter is None:
                listV = pickle.load(file)  # 解码序列
                pitch[indexcache] = listV[0]
                inputV[indexcache] = listV[1]
                mediumV[indexcache] = listV[2]
            else:
                listV = pickle.load(file)  # 解码序列
                oriData = listV[0]
                filteredData = listV[1]
                pitch[indexcache] = oriData[0]
                inputV[indexcache] = oriData[1]
                mediumV[indexcache] = oriData[2]
                pitchFilter[indexcache] = filteredData
        except EOFError:
            print('文件结束！%d' % indexcache)
            break


def deleteCache(pitch, pitchFiltered, inputV, mediumV, initPos, length):
    """
    卸载缓存
    :param pitch:待清理的音高数列
    :param inputV:待清理的输入数列
    :param mediumV:待清理的中间数列
    :param initPos:待清理的初始位置
    :param length:待清理数列的长度
    :return:
    """
    for delcache in np.arange(initPos, initPos + length):
        pitch[delcache] = []
        inputV[delcache] = []
        mediumV[delcache] = []
        if pitchFiltered is not None:
            pitchFiltered[delcache] = []


def merge(src, rmse):
    """
    #用于积分的累积求和
    :param src:eedf
    :param rmse:辅助判断端点
    :return:
    """
    x = np.copy(src)
    length = len(x)  # eedf数组长度
    currentSum = 0
    currentInit = 0
    maxRmse = 0
    maxEEPos = 0
    info = []
    for i in np.arange(length):
        if (currentSum * x[i]) < 0:
            try:
                # 当前区域结束,设置区域值
                maxRmse = max(rmse[currentInit:i])
                maxEEPos = np.argmax(abs(x[currentInit:i])) + currentInit
                x[currentInit:i] = currentSum
                info.append([currentInit, i, currentSum, maxRmse, maxEEPos])
                currentSum = x[i]
                currentInit = i
            except Exception:
                maxRmse = 0
                info.append([currentInit, len(src), currentSum, maxRmse, maxEEPos])
        else:
            currentSum = currentSum + x[i]
    x[currentInit:-1] = currentSum  # 补充最后一组
    try:
        maxRmse = max(rmse[currentInit:i])
    except Exception:
        maxRmse = 0
    info.append([currentInit, len(src), currentSum, maxRmse, maxEEPos])
    return [x, info]


# 用于线性拟合的函数
def func(p, x):
    return p * x


def error(p, x, y):
    return (func(p, x) - y) * (func(p, x) - y)


def pitchCorrection(pitch, can, thrCent):
    """
    频率（泛频）矫正
    :param pitch: 输入
    :param candidate: 参考
    :return:输出音高4
    """
    candidate = can
    times = np.round(max(pitch, candidate) / min(pitch, candidate))  # 频率倍数
    if pitch < candidate:
        times = 1.0 / times
    candidate = times * candidate
    if abs(math.log((pitch / candidate), 2.0 ** (1.0 / 12))) < thrCent:
        return candidate
    else:
        return pitch


# 归一化函数
def MaxMinNormalization(x, minv, maxv):
    Min = np.min(x)
    Max = np.max(x)
    y = (x - Min) / (Max - Min + 0.0000000001) * (maxv - minv) + minv
    return y


# filter by basefrq
def filterByBasefrq(src, basefrq, width):
    peaksPos = findpeaks(src, spacing=50, limit=max(src) * 0.05)
    peaks = src[peaksPos]  # 峰值大小
    tar = np.copy(src)
    num = min(int(len(src) / basefrq), 30)
    for i in np.arange(num):
        frq = i * basefrq
        tar[frq - width:frq + width] = min(src[frq - width], src[frq + width])
    return tar


# 目标标记程序流程
thrarta = 0.15
thrartb = 0.2
throp = 0.15
# 默认基频过滤参数
defaultFltWidth = int(300)  # 默认频率过滤宽度 30hz
thrResPow = 0.2  # 过滤残余能量阈值 50%
isFilterShow = True  # 是否显示过滤后的基频
lastestPos = []
index = 0
while True:
    username=input("username:")
    password=input("password:")
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        break
    else:
        print("账号或者密码错误")


while True:
    # 选择曲目
    for i in range(0, class1_listLen):
        candidateName = os.path.splitext(class1_list[i])[0]
        candidateFrame = 0
        candidateCent = 0
        if Clip.objects.filter(title=os.path.splitext(class1_list[i])[0]).count() == 0:
            candidateFrame = 0
        else:
            candidateFrame = \
                Clip.objects.filter(title=os.path.splitext(class1_list[i])[0]).aggregate(Max('startingPos'))[
                    'startingPos__max']
        # 计算进度
        setWave = Wave.objects.filter(title=candidateName)
        if setWave.count() > 0:
            candidateFrameNum = setWave[0].frameNum  # 待测总帧数
            candidateCent = candidateFrame / candidateFrameNum * 1.0
        print("[%02d]%s:%.2f" % (i, candidateName, candidateCent))
    songID = input("选择曲目:")
    index = int(songID)
    # 正式标记流程

    print(class1_list[index])
    referencePitch = []
    referencePitchInput = []
    referencePitchMedium = []
    referencePitchDeScan = []
    referencePitchDeScanInput = []
    referencePitchDeScanMedium = []
    referencePitchDeScanFilter = []
    songName = class1_path + class1_list[index]
    stream = librosa.load(songName, mono=False, sr=None)  # 以Fs重新采样
    baseName = os.path.splitext(class1_list[index])[0]

    # 引入预处理文件前缀
    pitchPrepPathDeScan = class1_path + baseName + '_%d' % Fs + '_%d/' % nfft + '_%d' % Fs + '_%d' % nfft + '_descan_'
    pitchPrepPathComb = class1_path + baseName + '_%d' % Fs + '_%d/' % nfft + '_%d' % Fs + '_%d' % nfft + '_comb_'
    # 读入标记记录文件
    x = stream[0]
    print('sampling rate:', stream[1])  # 采样率
    plt.figure(figsize=(12, 8))
    plt.plot(x[0])
    plt.xlabel('sample')
    plt.ylabel('amp')
    speech_stft, phase = librosa.magphase(
        librosa.stft(x[0], n_fft=nfft, hop_length=hopLength, window=scipy.signal.hamming))
    frameNum = len(speech_stft[0])

    if Clip.objects.filter(title=baseName).count() == 0:
        frame = 0
    else:
        print(Clip.objects.filter(title=baseName).aggregate(Max('startingPos')))
        # 更新pos
        frame = Clip.objects.filter(title=baseName).aggregate(Max('startingPos'))['startingPos__max'] + 1

    wavenum = Wave.objects.filter(title=baseName).count()
    if wavenum == 0:
        waveItem = Wave(title=baseName, waveFile=os.path.abspath(songName), frameNum=frameNum, fs=Fs,
                        duration=frameNum * 1.0 * nfft / Fs, completion=0)
        waveItem.save()
    wave = Wave.objects.get(title=baseName)
    if wave.chin is None:
        chin = Chin()
    else:
        chin = pickle.loads(wave.chin)
    # 显示定弦调式列表,以供选择
    print(chin.get_notes())
    tunes = []
    count = 0
    with open("../config/tune.json", "r", encoding="utf8") as f:
        for item in jsonlines.Reader(f):
            print("%02d:%s" % (count, item))
            tunes.append(item)
            count = count + 1
    notesstr = input("是否保留notes，是则y，否则直接键入notes：")
    if notesstr != "y":
        notes = [n for n in notesstr.split()]
        if len(notes) == 1:
            # 显示所选列表选项
            tune_index = int(notes[0])
            while tune_index >= len(tunes):
                tune_index = int(input("索引错误,重新输入"))
            consure = input("选择了%s,是否确认设置(y/n):" % tunes[tune_index]['name'])
            if consure == "y":
                # 保存调式
                chin.set_notes(tunes[tune_index]['notes'])
                chin.set_do(tunes[tune_index]['do'])
            else:
                # 放弃
                pass
        else:
            chin.set_notes(notes)
    if chin is not None:
        print("hzes", chin.get_hzes())
        print("a4hz", chin.get_ahz())
        print("do:", chin.get_do())
        print('scaling:', chin.get_scaling())
    dostr = input("是否保留do，是则y，否则直接键入do：")
    if dostr != "y":
        do = dostr
        chin.set_do(do)

    wave.chin = pickle.dumps(chin)
    wave.save(update_fields=["chin"])

    for i in np.arange(frameNum):
        referencePitch.append([])
        referencePitchInput.append([])
        referencePitchMedium.append([])
        referencePitchDeScan.append([])  # de scan 结果
        referencePitchDeScanInput.append([])  # src输入
        referencePitchDeScanMedium.append([])  # 中间结果
        referencePitchDeScanFilter.append([])  # 过滤后频率
    tarArray = np.zeros((frameNum, 5))

    print(['初始位置:', frame])

    plt.figure(figsize=(12, 8))
    fftForPitch = np.copy(speech_stft[0:np.int(nfft / Fs * 4000)])  # 4000hz以下信号用于音高检测
    librosa.display.specshow(fftForPitch, sr=Fs, hop_length=nfft)
    rmse = \
        librosa.feature.rmse(y=x[0], S=None, frame_length=nfft, hop_length=hopLength, center=True, pad_mode='reflect')[
            0]
    times = librosa.frames_to_time(np.arange(len(rmse)), sr=Fs, hop_length=hopLength, n_fft=nfft)
    rmse = MaxMinNormalization((rmse), 0, 1)
    plt.figure(figsize=(12, 8))
    if rmseS == 1:
        plt.plot(times, rmse, label='rmse_hop')
    # 求功率熵
    speech_stft_Enp = speech_stft[1:-1]
    speech_stft_prob = speech_stft_Enp / np.sum(speech_stft_Enp, axis=0)
    EE = np.sum(-np.log(speech_stft_prob) * speech_stft_prob, axis=0)
    EE = MaxMinNormalization(EE, 0, 1)
    if EES == 1:
        plt.plot(times, EE, label='EE')
    EEdiff = np.diff(EE)
    EEdiff = np.insert(EEdiff, 0, 0, None)
    if EEDS == 1:
        # plt.plot(times, EEdiff)
        # plt.plot(times, EEdiffacc)
        test = EEdiff * rmse
        plt.plot(times, test)
        EEdiff2 = np.diff(EEdiff)
        EEdiff2 = np.insert(EEdiff2, 0, 0, None) * rmse
        # plt.plot(times, EEdiff2)
        plt.axhline(0, color='r', alpha=0.5)
    RMSEdiff = np.diff(rmse)
    RMSEdiff = np.insert(RMSEdiff, 0, 0, None)
    if rmseDS == 1:
        plt.plot(times, RMSEdiff)

    [mergeEED, mergeEEDINFO] = np.array(merge(EEdiff, rmse))

    clipStop = [i for i in mergeEEDINFO if (i[2] > throp)]
    clipStart = [i for i in mergeEEDINFO if (i[2] < (-1 * thrarta) and i[3] > thrartb)]

    if MergeEEDS == 1:
        plt.plot(times, mergeEED, label='MEEDS')

    plt.legend()
    speech_stft = np.transpose(speech_stft)
    plt.show()
    pre = 0
    pitchs = []
    extendFrames = int(pitchExtend * Fs / nfft)  # 向前扩展的帧数

    speech_stft_pitch = np.copy(speech_stft)  # 求音高用短时傅里叶频谱
    framePerFile = int(60 * Fs / nfft)  # 1分钟每个文件
    cacheFile = []
    stopFile = math.ceil(len(speech_stft) * 1.0 / framePerFile)
    # target文件
    isfilterBybasefrq = False
    filterBasefrq = []
    filterWidth = []
    tmpShow = False
    while (frame < len(speech_stft)):
        plt.figure(figsize=[12, 8])
        tmpShow = False
        print("时刻:%.2f 进度:%.2f" % (frame * nfft / Fs, frame / len(speech_stft) * 100.0))  # 当前时刻
        currentID = int(frame / framePerFile)
        # 如果当前帧导致文件替换则更新先关音高缓存数据
        newSet = np.arange(currentID - 1, currentID + 2)  # 当前应该设置的缓存文件集合
        newSet = [i for i in newSet if (i > -1 and i < stopFile)]  # 应该添加的缓存文件
        addSet = [i for i in newSet if (i not in cacheFile and i > -1 and i < stopFile)]  # 应该添加的缓存文件

        if addSet != []:
            # 添加缓存
            for i in addSet:
                initPos = i * framePerFile
                length = framePerFile
                file = open(pitchPrepPathComb + '%02d' % i + '.txt', 'rb')
                addChche(referencePitch, None, referencePitchInput, referencePitchMedium, initPos, length,
                         file)  # 通过文件增加缓存并做校验
                file.close()
                file = open(pitchPrepPathDeScan + '%02d' % i + '.txt', 'rb')
                addChche(referencePitchDeScan, referencePitchDeScanFilter, referencePitchDeScanInput, \
                         referencePitchDeScanMedium, initPos, length, file)  # 通过文件增加缓存并做校验
                file.close()
        deleteSet = [i for i in cacheFile if i not in newSet]  # 应该删去的缓存

        if deleteSet != []:
            # 删除缓存
            for i in deleteSet:
                initPos = i * framePerFile
                length = framePerFile
                deleteCache(referencePitch, None, referencePitchInput, referencePitchMedium, initPos, length)  # 删除缓存
                deleteCache(referencePitchDeScan, referencePitchDeScanFilter, referencePitchDeScanInput,
                            referencePitchDeScanMedium, initPos, length)  # 删除缓存
        cacheFile = newSet
        dataClip = np.copy(speech_stft[frame])
        dataClip[0:int(30 * nfft / Fs)] = 0  # 清零30hz以下信号
        # 线性内插重新采样
        processingX = np.arange(0, int(nfft / Fs * 4000))  # 最大采集到4000Hz,不包括最大值，此处为尚未重采样的原始频谱
        processingY = dataClip[processingX]  # 重采样的fft
        lenProcessingX = len(processingX)  # 待处理频谱长度
        finterp = interp1d(processingX, processingY, kind='linear')  # 线性内插配置
        x_pred = np.linspace(0, processingX[lenProcessingX - 1] * 1.0,
                             int(processingX[lenProcessingX - 1] * 441000 / nfft) + 1)
        maxProcessingX = x_pred[len(x_pred) - 1]
        resampY = finterp(x_pred)

        lenResampY = len(resampY)
        # 显示局部输入数据，便于人工标记
        # 初步设置显示2s以内的数据
        extendClips = np.arange(max(0, frame - extendFrames), min(frame + extendFrames, len(rmse)))  # 延长的帧ID

        referenceRmse = np.copy(rmse[extendClips])
        referenceEE = np.copy(EE[extendClips])
        referenceMEED = np.copy(mergeEED[extendClips])
        referenceMEED = np.insert(referenceMEED, 0, 0, None)
        referenceTimes = librosa.frames_to_time(extendClips, sr=Fs, hop_length=hopLength, n_fft=nfft) - 0.05
        # plt.close()
        plt.subplot(221)
        plt.plot(referenceTimes, referenceRmse, label='rmse')
        plt.plot(referenceTimes, referenceEE, label='EE')
        plt.plot(referenceTimes, referenceMEED[0:len(referenceTimes)], label='MEED')
        plt.axvline((frame) * hopLength / Fs, color='r')
        plt.axhline(0, color='r')
        plt.annotate('%.2f' % EE[frame], xy=(frame, EE[frame]), xytext=((frame - 0.5) * hopLength / Fs, EE[frame]))
        plt.annotate('%.2f' % rmse[frame], xy=(frame, rmse[frame]),
                     xytext=((frame - 0.5) * hopLength / Fs, rmse[frame]))
        plt.legend()
        plt.subplot(223)
        plt.axvline((frame) * hopLength / Fs, color='r')
        plt.axhline(0, color='r')
        currentClipStart = np.array(
            [i[4] for i in clipStart if (i[0] < frame + extendFrames and i[0] > frame - extendFrames)])
        currentClipStart = currentClipStart.astype(np.int32)
        for startPos in currentClipStart:
            # 提前一格,防止起振阶段被忽略
            plt.axvline((startPos - 1) * hopLength / Fs, color='b', ls="--")
            plt.annotate('(%.2f,%.2f)' % (startPos - 1, referencePitchDeScan[startPos - 1]), \
                         xy=((startPos - 0.5 - 1) * hopLength / Fs, \
                             referencePitchDeScan[startPos - 1]), \
                         xytext=((startPos - 0.5 - 1) * hopLength / Fs, referencePitchDeScan[startPos - 1]))
        currentClipStop = np.array(
            [i[4] for i in clipStop if (i[0] < frame + extendFrames and i[0] > frame - extendFrames)])
        currentClipStop = currentClipStop.astype(np.int32)
        for stopPos in currentClipStop:
            plt.axvline((stopPos - 1) * hopLength / Fs, color='r', ls="--")
        plt.plot(referenceTimes, referencePitchDeScan[max(0, frame - extendFrames):frame + extendFrames],
                 label='pitchDeScan')
        if isFilterShow:
            print(referencePitchDeScan[max(0, frame - extendFrames):frame + extendFrames])
            plt.plot(referenceTimes, referencePitchDeScanFilter[max(0, frame - extendFrames):frame + extendFrames],
                     label='pitchDSFilter', ls="--")
        plt.plot(referenceTimes, referencePitch[max(0, frame - extendFrames):frame + extendFrames], label='pitch')
        # 从数据库获取标记的主音高
        candidate_clips = Clip.objects.filter(title=baseName, startingPos__range=(
            max(0, frame - extendFrames), frame + extendFrames))  # 参考音高条目
        for candidate_clip in candidate_clips:
            candidate_tarstr = candidate_clip.tar  # 原始tar数据
            candidate_tar = pickle.loads(candidate_tarstr)
            candidate_pos = candidate_clip.startingPos
            tarArray[candidate_pos] = candidate_tar[0]  # 更新要显示的标记主音
        plt.legend()
        plt.plot(referenceTimes, tarArray[max(0, frame - extendFrames):frame + extendFrames, 0], label='tar0',
                 color='y')

        plt.subplot(222)
        plt.plot(np.arange(len(referencePitchDeScanInput[frame])), referencePitchDeScanInput[frame], label='ori')
        plt.subplot(224)
        plt.plot(np.arange(len(referencePitchDeScanMedium[frame])), referencePitchDeScanMedium[frame], label='medium')
        resPitch = []  # 残余基频
        if isfilterBybasefrq == True:
            # 待过滤数据
            referencePitchDeScanInputFilter = np.copy(referencePitchDeScanInput[frame])
            for i in np.arange(len(filterBasefrq)):
                # 过滤基频
                referencePitchDeScanInputFilter = filterByBasefrq(referencePitchDeScanInputFilter, filterBasefrq[i],
                                                                  filterWidth[i])
                # 显示过滤后的残余
                plt.subplot(222)
                plt.plot(np.arange(len(referencePitchDeScanInputFilter)), referencePitchDeScanInputFilter,
                         label='filter%d' % i)
                # 显示残余基频
                test = baseFrqCombScan.getPitchDeScan(referencePitchDeScanInputFilter, Fs, Fs * 10, 0)
                resPitch.append(test[0])
                print("残余基频%d：%.2f" % (i + 1, test[0]))

        else:  # 默认过滤
            # 待过滤数据
            referencePitchDeScanInputFilter = np.copy(referencePitchDeScanInput[frame])
            resPow = sum(referencePitchDeScanInputFilter)  # 残余能量
            resCent = 1.0  # 残余比例
            fltPitch = referencePitchDeScan[frame]  # 默认音高
            index = 1  # 残余索引
            pre = 1.0
            while fltPitch > 40:
                # 过滤基频 (频率乘以10是因为分辨率为0.1hz)
                referencePitchDeScanInputFilter = \
                    filterByBasefrq(referencePitchDeScanInputFilter, int(fltPitch * 10), defaultFltWidth)
                # 显示过滤后的残余
                plt.subplot(222)
                plt.plot(np.arange(len(referencePitchDeScanInputFilter)), referencePitchDeScanInputFilter,
                         label='filter%d' % index)
                resCent = sum(referencePitchDeScanInputFilter) / resPow
                # 显示残余基频
                test = baseFrqCombScan.getPitchDeScan(referencePitchDeScanInputFilter, Fs, Fs * 10, 0)
                if (pre - resCent) < thrResPow:
                    break
                print("残余基频%d：%.2f s:%s  残余:%.2f" \
                      % (index, test[0], librosa.hz_to_note(test[0] * chin.get_scaling(), cents=True), resCent))
                fltPitch = test[0]  # 更新过滤基音
                if resCent > thrResPow:
                    resPitch.append(fltPitch)
                index = index + 1
                pre = resCent
        if isfilterBybasefrq == True:
            for pitchFlt in filterBasefrq:
                pitchFlt = pitchFlt / 10.0
                print("默认基频 :%.2f notes:%s" % (pitchFlt, librosa.hz_to_note(pitchFlt * chin.get_scaling(), cents=True)))
                print(chin.cal_possiblepos([pitchFlt])[1])

        else:
            if referencePitchDeScan[frame] > 40:
                print("\033[0;32;0m 默认基频 : %.2f \033[0m notes:%s" \
                      % (referencePitchDeScan[frame],
                         librosa.hz_to_note(referencePitchDeScan[frame] * chin.get_scaling(), cents=True)))
                print(chin.cal_possiblepos([referencePitchDeScan[frame]])[1])

        if resPitch != []:
            str_yinwei = chin.cal_possiblepos(resPitch)[1]
            set_yinwei = chin.cal_possiblepos(resPitch)[0]
            print(str_yinwei)
        fanyin_recommend = ""
        for res in resPitch:
            if isfilterBybasefrq:
                pitch_fanyin = filterBasefrq[0] / 10.0
            else:
                pitch_fanyin = referencePitchDeScan[frame]
            r = pitch_fanyin / res
            # if r < 1.5:
            # continue
            cand = round(r)
            err = abs(r - cand)
            if err < 0.1:
                try:
                    print("\033[0;35;0m推荐泛音弦位：%d\033[0m" % chin.cal_sanyinpred(res, 0.2)[0][0])
                except Exception as e:
                    print(e)
        isfilterBybasefrq = False
        filterBasefrq = []
        filterWidth = []
        # 显示前后5s的tone标注
        toneShowFramesNum = int((Fs * 1.0 / nfft) * toneShowWidth)  # 前后扩展的帧数
        toneShow = Tone.objects.filter(title=baseName,
                                       pos__range=(frame - toneShowFramesNum, frame + toneShowFramesNum))
        showstr = "历史音高标记:"
        for toneitem in toneShow:
            showstr = showstr + "\033[0;32m%s\033[0m,%s,%s-%d |" % (
                toneitem.tone, toneitem.note, toneitem.pos, int(toneitem.length) + int(toneitem.pos) - 1)
        print(showstr)
        plt.legend()
        plt.show()
        cycFlag = True
        while cycFlag:
            pitchinfo = input("cmd:")
            Log(title=baseName, content=pitchinfo, timestamp=datetime.now()).save()
            try:
                cmds = pitchinfo.split(';')

                for cmd in cmds:
                    item = cmd.split()  # 命令行及其参数
                    cmdstr = item[0]  # 命令字
                    if cmdstr == "mt":
                        time = int(item[1])
                        if time >= frameNum:
                            print("跳转位置超过帧数目,重新输入")
                            break
                        frame = time  # 调整当前帧位置
                        tmpShow = True
                        cycFlag = False
                    if cmdstr == "dt":
                        time = int(item[1])
                        if (time <= frame):
                            YESNO = input("设置时间小于等于当前时间，是否确认修改？是键入Y,否则N:")
                            if YESNO == "Y":
                                frame = time  # 调整当前帧位置
                            else:
                                print("放弃当前设置")
                        else:
                            frame = time  # 调整当前帧位置
                        Clip.objects.filter(title=baseName, startingPos__gte=frame).delete()
                        tmpShow = True
                        cycFlag = False
                    if cmdstr == "thrart":
                        a = float(item[1])
                        b = float(item[2])
                        if a > 0:
                            thrarta = a
                        if b > 0:
                            thrartb = b
                        # 重新计算起始位置
                        clipStart = [i for i in mergeEEDINFO if (i[2] < (-1 * thrarta) and i[3] > thrartb)]

                    if cmdstr == "throp":
                        thr = float(item[1])
                        if thr > 0:
                            throp = thr
                        clipStop = [i for i in mergeEEDINFO if (i[2] > throp)]

                    if cmdstr == "ef":
                        extendFrames = int(item[1])
                    if cmdstr == "tw":  # tone width
                        toneShowWidth = float(item[1])
                    if cmdstr == "pl":
                        start = int(item[1])
                        stop = int(item[2])
                        data = np.copy(x[0][start * nfft:stop * nfft])
                        playwave(data)
                    if cmdstr == "mark":
                        start = int(item[1])
                        stop = int(item[2])
                        length = (stop - start) * 1.0 * nfft / Fs  # 单位是时间
                        start = start * nfft * 1.0 / Fs
                        markstr = item[3]

                        MarkedPhrase(title=baseName, start=start, length=length, mark=markstr).save()

                    if cmdstr == "ptt":
                        start = int(item[1])
                        end = int(item[2])

                        # 如果time<0,认为自动移动一帧
                        lastestPos = []

                        for i in np.arange(start, end):
                            name = baseName
                            init = i
                            lenClip = 1
                            src = np.copy(speech_stft[i])
                            tar = item[3:]
                            tar = [float(p) for p in tar]
                            candidate = referencePitchDeScan[i]
                            tar = np.array(tar)
                            # 如果频率小于0则以候选频率替代, 如果是候选频的倍数则替换为候选频的整数倍， 暂定阈值15音分
                            # tar = np.where(tar < 0.0, candidate*abs(tar), pitchCorrection(tar, candidate, 0.15))
                            for p in np.arange(len(tar)):
                                if tar[p] < 0.0:
                                    tar[p] = candidate * abs(tar[p])
                                else:
                                    tar[p] = pitchCorrection(tar[p], candidate, 0.15)

                            # 写入数据库
                            srcstr = pickle.dumps(src)
                            tarstr = pickle.dumps(tar)
                            dbitem = Clip(title=name, startingPos=init, length=lenClip, src=srcstr, tar=tarstr
                                          , nfft=nfft)
                            lastestPos.append(init)
                            dbitem.save()

                            # frame = frame+1
                            cycFlag = False

                    if cmdstr == "pt":
                        time = int(item[1])
                        # 如果time<0,认为自动移动一帧
                        lastestPos = []
                        if time <= frame:
                            time = frame + 1
                            print("time小于当前帧，自动移动一帧。")
                        for i in np.arange(frame, time):
                            name = baseName
                            init = i
                            lenClip = 1
                            src = np.copy(speech_stft[i])
                            tar = item[2:]
                            tar = [float(p) for p in tar]
                            candidate = referencePitchDeScan[i]
                            tar = np.array(tar)
                            # 如果频率小于0则以候选频率替代, 如果是候选频的倍数则替换为候选频的整数倍， 暂定阈值15音分
                            # tar = np.where(tar < 0.0, candidate*abs(tar), pitchCorrection(tar, candidate, 0.15))
                            for p in np.arange(len(tar)):
                                if tar[p] < 0.0:
                                    tar[p] = candidate * abs(tar[p])
                                else:
                                    tar[p] = pitchCorrection(tar[p], candidate, 0.15)

                            # 写入数据库
                            srcstr = pickle.dumps(src)
                            tarstr = pickle.dumps(tar)
                            dbitem = Clip(title=name, startingPos=init, length=lenClip, src=srcstr, tar=tarstr
                                          , nfft=nfft, create_user_id= username)
                            lastestPos.append(init)
                            dbitem.save()
                            # frame = frame+1
                            cycFlag = False

                    if cmdstr == "anote":
                        if lastestPos != []:
                            for pos in lastestPos:
                                lastItem = Clip.objects.get(title=baseName, startingPos=pos)
                                if len(item) > 1:
                                    lastItem.anote = item[1]
                                else:
                                    lastItem.anote = ""
                                lastItem.save()
                        else:
                            print("没有最新条目")

                    if cmdstr == "flt":
                        filterBasefrq = []
                        filterWidth = []
                        for i in np.arange(1, len(item)):
                            if i % 2 == 1:
                                filterBasefrq.append(int(float(item[i]) * 10))
                            else:
                                filterWidth.append(int(float(item[i]) * 10))
                        if len(filterBasefrq) != len(filterWidth) or len(filterBasefrq) < 1:
                            break
                        isfilterBybasefrq = True
                        cycFlag = False

                    # 设置唱名条目
                    if cmdstr == "tone":
                        startTone = int(item[1])  # tone 起始位置
                        length = int(item[2]) - startTone  # 不包括item[2]
                        pitchTone = float(item[3])  # 这里都不用-1
                        noteTone = librosa.hz_to_note(pitchTone / chin.get_scaling())  # 用于测量tone的note，不求百分数
                        tone = chin.note2tone(noteTone)  # 计算音高 ，因为程序编写费时间，不提供直接设置tone的方式
                        tonestr = '%.1f_%d' % (tone[0], tone[1])  # tone[0] 是音高， tone[1]是grade
                        if len(item) == 5:
                            anoteTone = item[4]
                        else:
                            anoteTone = ""
                        Tone(title=baseName, pos=startTone, length=length, \
                             pitch=pitchTone, note=librosa.hz_to_note(pitchTone / chin.get_scaling(), cents=True), \
                             tone=tonestr, anote=anoteTone).save()

                    # 删除指定的唱名条目
                    if cmdstr == "dtone":
                        deleteTime = int(item[1])  # 删除时刻
                        Tone.objects.filter(title=baseName, pos__gte=deleteTime).delete()  # 删除time后的条目

                    # 描述可能的音位
                    if cmdstr == "desc":
                        pitchDesc = float(item[1])
                        print(librosa.hz_to_note(pitchDesc / chin.get_scaling(), cents=True))
                        print(chin.cal_possiblepos([pitchDesc])[1])

                    # custom 自定义区域检测, 只为验证短时频率是否精确
                    if cmdstr == "custom":
                        initP = int(item[1])  # 初始帧
                        stopP = int(item[2])  # 结束帧 （不包括此帧）
                        dataSrc = np.copy(x[0][initP * nfft:stopP * nfft])  # 原始数据
                        fftnum = len(dataSrc)  # fft长度
                        fullFFT = fft(dataSrc)
                        dataFFT = abs(fullFFT)[0:int((len(fullFFT) + 1) / 2)]
                        pitch = baseFrqCombScan.getPitchDeScan(dataFFT, Fs, fftnum, showTestView)
                        print("自定义区域音高检测!Fs:%d  fft_num:%d  pitch:%.2f" % (Fs, fftnum, pitch[0]))

                    # 设置a4
                    if cmdstr == "a42hz":
                        a4 = float(item[1])
                        YESNO = input("如此将放弃之前的hz，继续则键入Y")
                        if YESNO == "Y":
                            chin.set_ahz(a4)
                            chin.updateHzesFromNotes()
                            wave.chin = pickle.dumps(chin)
                            wave.save(update_fields=["chin"])
                        else:
                            print("放弃当前设置")
                    if cmdstr == "a42note":
                        a4 = float(item[1])
                        doHz = librosa.note_to_hz(chin.get_do()) * chin.get_scaling()
                        chin.set_ahz(a4)
                        chin.updateNotesFromHzes()
                        chin.set_do(librosa.hz_to_note(doHz / chin.get_scaling()))
                        wave.chin = pickle.dumps(chin)
                        wave.save(update_fields=["chin"])

                    # 设置指定弦的音高
                    if cmdstr == "hz":
                        strID = int(item[1]) - 1  # 从0开始标号
                        tune = float(item[2])
                        chin.set_hz(strID, tune)
                        wave.chin = pickle.dumps(chin)
                        wave.save(update_fields=["chin"])

                    # 查询定弦和谐信息
                    if cmdstr == "harmony":
                        chin.cal_harmony()
                        harmony_info = chin.get_harmony()
                        if harmony_info is None:
                            break
                        score_sanyin = harmony_info['ScoreS']
                        score_fanyin = harmony_info['ScoreF']
                        harmony_list = harmony_info['T']
                        un_harmony_list = harmony_info['F']
                        print("sanyin score:%.2f" % score_sanyin)
                        print("fanyin score:%.2f" % score_fanyin)
                        for line in harmony_list:
                            if line[0] == 's':
                                print("\033[0;32m 散音:%d弦， %d弦， 偏差 %.2f \033[0m" % (line[1] + 1, line[2] + 1, line[3]))
                            if line[0] == 'f':
                                print("\033[0;32m 泛音:%d弦%d徽， %d弦%d徽， 偏差 %.2f \033[0m" \
                                      % (line[1][0] + 1, line[1][1] + 1, line[2][0] + 1, line[2][1] + 1, line[3]))
                        for line in un_harmony_list:
                            if line[0] == 's':
                                print("\033[0;31m 散音:%d弦， %d弦， 偏差 %.2f \033[0m" % (line[1] + 1, line[2] + 1, line[3]))
                            if line[0] == 'f':
                                print("\033[0;31m 泛音:%d弦%d徽， %d弦%d徽， 偏差 %.2f \033[0m" \
                                      % (line[1][0] + 1, line[1][1] + 1, line[2][0] + 1, line[2][1] + 1, line[3]))
                        print(chin.get_hzes())
                    # 显示 添加曲调列表
                    if cmdstr == "append_tune":
                        if len(item) != 10:
                            print("输入长度有错误!")
                        else:
                            tune_name = item[1]  # 曲调名称
                            tune_notes = []  # 曲调notes
                            for i in np.arange(7):
                                tune_notes.append(item[i + 2])
                            tune = {'name': tune_name, 'notes': tune_notes, 'do': item[9]}
                            with open("../config/tune.json", "a") as f:
                                f.write(json.dumps(tune) + "\n")
                                print("曲调写入完成...")
                    if cmdstr == "exit":
                        sys.exit(0)


            except Exception as e:
                print(e)
                print('请重新输入:')
                cycFlag = True
                break

        # 更新pos
        if tmpShow == False:
            lastest = Clip.objects.filter(title=baseName)

            frame = lastest.aggregate(Max('startingPos'))['startingPos__max']
            if frame is not None:
                frame = frame + 1
            else:
                frame = 0
            print(["test", frame])
