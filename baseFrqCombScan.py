from __future__ import print_function

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

from findPeaks import findpeaks

'''
本文件的基频检测算法为传统的梳状算法；
减去轨迹线subpeakAmpLimiting
用于对深度学习数据进行人工标注；
不作为基频检测的最后结果
对数据的人工标注为：输入 40000个数据 输出 最容易识别的最强基频 先暂时标注频率值 待找到合适编码机制在编码
'''
showTestView = 0  # 是否逐帧显示fft过程,需要把所有弹出窗口均关闭，然后关闭一个fft窗口 就会弹出下一个（只会这么整了）


# 用于线性拟合的函数
def func(p, x):
    return p * x


def error(p, x, y):
    return (func(p, x) - y) * (func(p, x) - y)


# 归一化函数
def MaxMinNormalization(x, minv, maxv):
    Min = np.min(x)
    Max = np.max(x)
    y = (x - Min) / (Max - Min + 0.0000000001) * (maxv - minv) + minv;
    return y


# 次峰限幅
def subpeakAmpLimiting(dataClip, space, limit):
    peaks = findpeaks(dataClip, spacing=space, limit=max(dataClip) * limit)
    if len(peaks) == 0:
        return dataClip
    dots = np.copy(dataClip[peaks])
    dots[np.argmax(dots)] = 0
    maxval = max(dots)
    # 如果等于0 说明只有一个峰
    if maxval > 0:
        # dataClip = 3
        np.where(dataClip < maxval, dataClip, maxval)
    return dataClip


# 获得范围内最大峰
'''
trueTrans:采样变换向量
combTransPeaks:波峰位置
peaks:波峰向量
n:预期波峰
combThr:梳子宽度
preBaseFrq:上次寻峰位置
decThr:容许能量降低的阈值
'''


def getNearPeaks(trueTrans, combTransPeaks, peaks, n, combThr, preBaseFrq, decThr, showTestView):
    if showTestView:
        print(['preBaseFrq', preBaseFrq])
        print(['n', n])
        print(['combThr', combThr])
        print(['combTransPeaks', combTransPeaks])
    a = np.where(combTransPeaks > (n - combThr))[0]
    b = np.where(combTransPeaks < (n + combThr))[0]
    selectPeaks = [v for v in a if v in b]
    if showTestView:
        print(['a', a])
        print(['b', b])
        print(['test', selectPeaks])

    if len(selectPeaks) > 0:
        candidacy = combTransPeaks[selectPeaks[np.argmax(peaks[selectPeaks])]]
        if showTestView:
            print(['selectPeaks[np.argmax(peaks[selectPeaks])]', selectPeaks[np.argmax(peaks[selectPeaks])]])
            print(['trueTrans[candidacy ]', trueTrans[candidacy]])
            print(['trueTrans[preBaseFrq]', trueTrans[preBaseFrq]])
        if (trueTrans[candidacy] / trueTrans[preBaseFrq]) > decThr:
            return candidacy
        else:
            return -1
    else:
        return -1


# 获取最左侧扫描交点
def getScanDot(deSamp, height):
    biasShift = deSamp - height
    lenDesamp = len(deSamp)
    a = biasShift[0:lenDesamp - 2]
    b = biasShift[1:lenDesamp - 1]
    c = a * b
    jiaodian = np.where(c <= 0)
    try:
        x1 = jiaodian[0][0]
    except Exception as e:
        print(e)
        return []
    x2 = x1 + 1
    y1 = deSamp[x1]
    y2 = deSamp[x2]
    x = ((height - y1) / (y2 - y1) + x1)
    return [x, height]


# 横向扫描求轮廓
def getBaseLineFromScan(deSamp, num):
    minval = min(deSamp[20:-1])  # 最小值
    maxval = np.mean(deSamp[16:26])  # 最大值
    if (maxval - minval) < 1:
        return np.zeros(num)
    intercept = (maxval - minval) / 1000.0
    heights = np.arange(minval + intercept, maxval, intercept)
    x = []
    y = []
    pos = -1
    for i in heights:
        dot = getScanDot(deSamp[0:pos], i)
        if dot == []:
            return np.zeros(num)
        x.append(dot[0] * 10.0)
        y.append(dot[1])
        pos = int(dot[0]) + 20
    x.append(0)
    y.append(0)
    x.append(num)
    y.append(0)
    finterp = interp1d(x, y, kind='linear')  # 线性内插配置
    x_pred = np.arange(0, num, 1)
    resampY = finterp(x_pred)
    return resampY


def getPitchDeScan(dataClip, Fs, nfft, showTestView):
    pitch = 0
    dataClip[0:int(30 * nfft / Fs)] = 0
    dataClip = subpeakAmpLimiting(dataClip, int(30.0 / Fs * nfft), 0.1)  # 次峰限幅
    if showTestView:
        plt.subplot(231)
        plt.plot(np.arange(len(dataClip)), dataClip, label='amp-frq')
    lowCutoff = int(40 * 441000.0 / Fs)  # 最低截止频率对应的坐标
    highCutoff = int(1400 * 441000.0 / Fs)  # 最高截止频率对应的坐标
    peakSearchPixes = int(3 * 441000 / Fs)  # 寻峰间距
    peakSearchAmp = 0.1  # 寻峰高度
    # 线性内插重新采样
    processingX = np.arange(0, min(int(nfft / Fs * 4000), len(dataClip)))  # 最大采集到4000Hz,不包括最大值，此处为尚未重采样的原始频谱
    processingY = dataClip[processingX]  # 重采样的fft
    lenProcessingX = len(processingX)  # 待处理频谱长度
    finterp = interp1d(processingX, processingY, kind='linear')  # 线性内插配置
    x_pred = np.linspace(0, processingX[lenProcessingX - 1] * 1.0,
                         int(processingX[lenProcessingX - 1] * 441000 / nfft) + 1)
    maxProcessingX = x_pred[len(x_pred) - 1]
    resampY = finterp(x_pred)
    lenResampY = len(resampY)
    # print(len(resampY))
    if showTestView == 1:
        plt.subplot(232)
        plt.plot(np.arange(len(resampY)), resampY, label='rs_Amp-frq')
    maxResampY = max(resampY[lowCutoff:-1]) / 2  # 待测频率内的最大值
    # 测试梳状变换
    # pixes=10
    num = highCutoff  # 栅栏变换后的长度
    combTrans = np.zeros(num)  # 存放栅栏变换的结果
    indexComb = np.arange(lowCutoff, highCutoff, 0.1)  # 栅栏变换索引
    for k in np.arange(1, highCutoff, 1):
        combTrans[k] = np.sum([resampY[i] for i in np.arange(0, lenResampY - 1, k)])
    if showTestView == 1:
        plt.subplot(233)
        plt.plot(np.arange(len(combTrans)), combTrans, label='combTrans')
    deSamp = [combTrans[m] for m in np.arange(0, len(combTrans), 10)]  # 10倍数降采样
    deSamp[0] = 1000
    if showTestView == 1:
        plt.subplot(234)
        plt.plot(np.arange(len(deSamp)), deSamp, label='DsCombTrans')
    baseLine = getBaseLineFromScan(deSamp, num)  # 通过扫描线算法求基准曲线
    if showTestView == 1:
        plt.subplot(235)
        plt.plot(np.arange(len(baseLine)), baseLine, label='baseline')
    trueTrans = combTrans - baseLine
    trueTrans[0:lowCutoff] = 0
    if showTestView == 1:
        plt.subplot(236)
        plt.plot(np.arange(len(trueTrans)), trueTrans, label='trueTrans')
    if (sum(dataClip) < 1):
        return [0 / 10.0, resampY, trueTrans]
    pitch = max(trueTrans) / sum(dataClip)

    # 频率采样变换后寻峰
    combTransPeaks = findpeaks(trueTrans, spacing=peakSearchPixes, limit=max(trueTrans) * peakSearchAmp)
    peaks = trueTrans[combTransPeaks]  # 峰值大小
    if (len(peaks) == 0):
        return [0 / 10.0, resampY, trueTrans]
    maxindex = np.argmax(peaks)
    maxfrq = combTransPeaks[maxindex]  # 最高峰值位置

    # 寻找1hz以内的最大的峰
    combThr = 6 * 441000 / Fs  # 寻峰宽度
    decThr = 0.65  # 递减阈值
    preBaseFrq = maxfrq
    for n in range(2, 10, 1):
        newfrq = getNearPeaks(trueTrans, combTransPeaks, peaks, n * maxfrq, combThr, preBaseFrq, decThr, showTestView)
        if (newfrq > 0):
            preBaseFrq = newfrq
        else:
            continue
    pitch = preBaseFrq;
    if showTestView == 1:
        plt.scatter(combTransPeaks, trueTrans[combTransPeaks], color='', marker='o', edgecolors='r', s=100)
        plt.show()
    return [pitch / 10.0, resampY, trueTrans]
