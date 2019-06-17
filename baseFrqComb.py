from __future__ import print_function

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

from findPeaks import findpeaks

'''
本文件的基频检测算法为传统的梳状算法；
减去轨迹线subpeak_amplimiting
用于对深度学习数据进行人工标注；
不作为基频检测的最后结果
对数据的人工标注为：输入 40000个数据 输出 最容易识别的最强基频 先暂时标注频率值 待找到合适编码机制在编码
'''


class BaseFrqDetector:

    def __init__(self, isdescan):
        self._showtestview = 0  # 是否显示fft过程,需要把所有弹出窗口均关闭，然后关闭一个fft窗口 就会弹出下一个（只会这么整了）
        self._isdescan = isdescan  # 是否去扫描线

    @property
    def showtestview(self):
        return self._showtestview

    @showtestview.setter
    def showtestview(self, value):
        self._showtestview = value

    @property
    def isdescan(self):
        return self._isdescan

    @isdescan.setter
    def isdescan(self, value):
        self._isdescan = value

    # 用于线性拟合的函数
    @staticmethod
    def func(p, x):
        """

        :param p: 拟合系数
        :param x: 拟合输入
        :return: 预测输出
        """
        return p * x

    # 误差评估函数
    @staticmethod
    def error(p, x, y):
        """

        :param p: 系数
        :param x: 输入
        :param y: 输出
        :return: 误差估计
        """
        return (BaseFrqDetector.func(p, x) - y) * (BaseFrqDetector.func(p, x) - y)

    # 归一化函数
    @staticmethod
    def maxminnormalization(x, minv, maxv):
        """

        :param x: 输入
        :param minv: 最小预期
        :param maxv: 最大预期
        :return: 归一化结果
        """
        minval = np.min(x)
        maxval = np.max(x)
        y = (x - minval) / (maxval - minval + 0.0000000001) * (maxv - minv) + minv
        return y
    
    # 次峰限幅
    @staticmethod
    def subpeak_amplimiting(dataclip, space, limit):
        """

        :param dataclip:输入
        :param space:寻峰宽度
        :param limit:寻峰阈值
        :return:次高峰值限制幅度结果
        """
        peaks = findpeaks(dataclip, spacing=space, limit=max(dataclip)*limit)
        if len(peaks) == 0:
            return dataclip
        dots = np.copy(dataclip[peaks])
        dots[np.argmax(dots)] = 0
        maxval = max(dots)
        # 如果等于0 说明只有一个峰
        if maxval > 0:
            dataclip = np.where(dataclip < maxval, dataclip, maxval)
        return dataclip

    # 获得范围内最大峰
    @staticmethod
    def getnearpeaks(truetrans, combtranspeaks, peaks, n, combthr, prebasefrq, decthr, showtestview):
        """
        获得范围内最大峰
        :param truetrans:采样变换向量
        :param combtranspeaks:波峰位置
        :param peaks:波峰向量
        :param n:预期波峰
        :param combthr:梳子宽度
        :param prebasefrq:上次寻峰位置
        :param decthr:容许能量降低的阈值
        :param showtestview:是否显示图形
        :return:输出候选频率,-1代表未寻找到期望频率,其他情况返回频率值
        """
        if showtestview:
            print(['prebasefrq', prebasefrq])
            print(['n', n])
            print(['combthr', combthr])
            print(['combtranspeaks', combtranspeaks])
        a = np.where(combtranspeaks > (n - combthr))[0]
        b = np.where(combtranspeaks < (n + combthr))[0]
        selectpeaks = [v for v in a if v in b]
        if showtestview:
            print(['a', a])
            print(['b', b])
            print(['test', selectpeaks])

        if len(selectpeaks) > 0:
            candidacy = combtranspeaks[selectpeaks[np.argmax(peaks[selectpeaks])]]
            if showtestview:
                print(['selectpeaks[np.argmax(peaks[selectpeaks])]', selectpeaks[np.argmax(peaks[selectpeaks])]])
                print(['truetrans[candidacy ]', truetrans[candidacy]])
                print(['truetrans[prebasefrq]', truetrans[prebasefrq]])
            if (truetrans[candidacy] / truetrans[prebasefrq]) > decthr:
                return candidacy
            else:
                return -1
        else:
            return -1

    # 获取最左侧扫描交点
    @staticmethod
    def getscandot(desamp, height):
        """

        :param desamp:降采样后的梳状统计曲线
        :param height:预期高度直线
        :return:左侧交点
        """
        biasshift = desamp - height
        lendesamp = len(desamp)
        a = biasshift[0:lendesamp - 2]
        b = biasshift[1:lendesamp - 1]
        c = a * b
        jiaodian = np.where(c <= 0)
        try:
            x1 = jiaodian[0][0]
        except Exception as e:
            print(e)
            return []
        x2 = x1 + 1
        y1 = desamp[x1]
        y2 = desamp[x2]
        x = ((height - y1) / (y2 - y1) + x1)
        return [x, height]

    # 横向扫描求轮廓
    @staticmethod
    def getbaselinefromscan(desamp, num):
        """

        :param desamp: 梳状曲线
        :param num: 恢复采样数量,插值数量
        :return: 基线向量
        """
        minval = min(desamp[20:-1])  # 最小值
        maxval = np.mean(desamp[16:26])  # 最大值
        if (maxval - minval) < 1:
            return np.zeros(num)
        intercept = (maxval - minval) / 1000.0
        heights = np.arange(minval + intercept, maxval, intercept)
        x = []
        y = []
        pos = -1
        for i in heights:
            dot = BaseFrqDetector.getscandot(desamp[0:pos], i)
            if not dot:
                return np.zeros(num)
            x.append(dot[0] * 10.0)
            y.append(dot[1])
            pos = int(dot[0]) + 20
        x.append(0)
        y.append(0)
        x.append(num)  # 保证不溢出
        y.append(0)
        finterp = interp1d(x, y, kind='linear')  # 线性内插配置
        x_pred = np.arange(0, num, 1)
        resampy = finterp(x_pred) 
        return resampy

    @staticmethod
    def filterbybasefrq(src, basefrq, width, fs, nfft):
        """
        通过基频进行过滤
        :param src:待过滤信号
        :param basefrq:基频 单位是hz
        :param width:频宽
        :param fs:采样率
        :param nfft:窗口宽度
        :return:过滤后信号
        """
        basefrq = int(basefrq * nfft / fs)
        width = int(width * nfft / fs)
        tar = np.copy(src)
        num = min(int(len(src) / basefrq), 30)  # 最多过滤30个波峰
        for i in np.arange(num):
            frq = i * basefrq
            tar[frq - width:frq + width] = min(src[frq - width], src[frq + width])
        return tar

    def getpitch(self, dataclip, fs, nfft, showtestview):
        """
        音高估计
        :param dataclip:输入fft
        :param fs:采样率
        :param nfft:窗口大小
        :param showtestview:是否显示figure
        :return:频率,插值采样后的输入,梳状统计向量
        """
        dataclip[0:int(30 * nfft / fs)] = 0
        dataclip = BaseFrqDetector.subpeak_amplimiting(dataclip, int(30.0 / fs * nfft), 0.1)  # 次峰限幅
        if self.showtestview:
            plt.subplot(231)
            plt.plot(np.arange(len(dataclip)), dataclip, label='amp-frq')
        lowcutoff = int(32.5 * 441000.0 / fs)  # 最低截止频率对应的坐标
        highcutoff = int(1400 * 441000.0 / fs)  # 最高截止频率对应的坐标
        peaksearchpixes = int(3 * 441000 / fs)  # 寻峰间距
        peaksearchamp = 0.1  # 寻峰高度
        # 线性内插重新采样
        processingx = np.arange(0, min(int(nfft / fs * 4000), len(dataclip)))  # 最大采集到4000Hz,不包括最大值，此处为尚未重采样的原始频谱
        processingy = dataclip[processingx]  # 重采样的fft
        lenprocessingx = len(processingx)  # 待处理频谱长度
        finterp = interp1d(processingx, processingy, kind='linear')  # 线性内插配置
        x_pred = np.linspace(0, processingx[lenprocessingx - 1] * 1.0,
                             int(processingx[lenprocessingx - 1] * 441000 / nfft) + 1)
        resampy = finterp(x_pred)
        lenresampy = len(resampy)
        if self.showtestview == 1:
            plt.subplot(232)
            plt.plot(np.arange(len(resampy)), resampy, label='rs_Amp-frq')

        # pixes=10
        num = highcutoff  # 栅栏变换后的长度
        combtrans = np.zeros(num)  # 存放栅栏变换的结果

        # 梳状变换, 2019-03-10 16:54:45

        for k in np.arange(1, highcutoff, 1):
            combtrans[k] = sum([resampy[i] for i in np.arange(0, lenresampy - 1, k)])
        if self.showtestview == 1:
            plt.subplot(233)
            plt.plot(np.arange(len(combtrans)), combtrans, label='combtrans')

        # 如果有去扫描参数,则去扫描
        if self.isdescan is True:
            # 用于降低采样
            desamp = [combtrans[m] for m in np.arange(0, len(combtrans), 10)]  # 10倍数降采样
            desamp[0] = np.max(desamp)
            if self.showtestview == 1:
                plt.subplot(234)
                plt.plot(np.arange(len(desamp)), desamp, label='Dscombtrans')
            baseline = BaseFrqDetector.getbaselinefromscan(desamp, num)  # 通过扫描线算法求基准曲线
            if self.showtestview == 1:
                plt.subplot(235)
                plt.plot(np.arange(len(baseline)), baseline, label='baseline')
            truetrans = combtrans-baseline
        else:
            truetrans = combtrans

        truetrans[0:lowcutoff] = 0
        if self.showtestview == 1:
            plt.subplot(236)
            plt.plot(np.arange(len(truetrans)), truetrans, label='truetrans')
        if sum(dataclip) < 1:
            return [0 / 10.0, resampy, truetrans]

        # 频率采样变换后寻峰
        combtranspeaks = findpeaks(truetrans, spacing=peaksearchpixes, limit=max(truetrans) * peaksearchamp)
        peaks = truetrans[combtranspeaks]  # 峰值大小
        if len(peaks) == 0:
            return [0 / 10.0, resampy, truetrans]
        maxindex = np.argmax(peaks)
        maxfrq = combtranspeaks[maxindex]  # 最高峰值位置

        # 寻找1hz以内的最大的峰
        combthr = 6 * 441000 / fs  # 寻峰宽度
        decthr = 0.65  # 递减阈值
        prebasefrq = maxfrq
        for n in range(2, 10, 1):
            newfrq = BaseFrqDetector.getnearpeaks(truetrans, combtranspeaks, peaks,
                                                  n * maxfrq, combthr, prebasefrq, decthr, showtestview)
            if newfrq > 0:
                prebasefrq = newfrq
            else:
                continue
        pitch = prebasefrq
        if self.showtestview == 1:
            plt.scatter(combtranspeaks, truetrans[combtranspeaks], color='', marker='o', edgecolors='r', s=100)
            plt.show()
        return [pitch / 10.0, resampy, truetrans]
