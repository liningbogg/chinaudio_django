import threading
import numpy as np


class RWLock(object):
    """
    读写锁封装
    这里读者锁临界资源无关写操作本身，因此不会阻塞其他读者
    """
    def __init__(self):
        self.rlock = threading.Lock()
        self.wlock = threading.Lock()
        self.reader = 0  # 读者数目


class targetTools:
    """
    工具类
    """

    @staticmethod
    def vad(ee, rmse, thrartEE, thrartRmse, throp):
        eearray = np.array(ee)
        ee_diff = np.diff(ee)
        ee_diff = np.insert(ee_diff, 0, 0, None)
        length = len(ee_diff)  # eedf数组长度
        currentSum = 0  # 当前ee累积和
        currentInit = 0  # 当前累积区域起始位置
        tmp = np.copy(ee_diff)
        maxRmse = 0  # 当前累计区域最大rmse
        maxEEPos = 0  # 当前最大EE位置
        info = []
        for i in np.arange(length):
            if (currentSum * ee_diff[i]) < 0:
                try:
                    # 当前区域结束,设置区域值
                    maxRmse = max(rmse[currentInit:i])
                    maxEEPos = np.argmax(abs(eearray[currentInit:i])) + currentInit
                    ee_diff[currentInit:i] = currentSum
                    info.append([currentInit, i, currentSum, maxRmse, maxEEPos])
                    currentSum = ee_diff[i]
                    currentInit = i
                except Exception as e:
                    print(e)
                    maxRmse = 0
                    info.append([currentInit, length, currentSum, maxRmse, maxEEPos])
            else:
                currentSum = currentSum + ee_diff[i]

        ee_diff[currentInit:-1] = currentSum  # 补充最后一组
        try:
            maxRmse = max(rmse[currentInit:i])
        except Exception as e:
            print(e)
            maxRmse = 0
        info.append([currentInit, length, currentSum, maxRmse, maxEEPos])
        clipStop = [item for item in info if (item[2] > throp)]
        clipStart = [item for item in info if (item[2] < (-1 * thrartEE) and item[3] > thrartRmse)]
        startPosOri = np.array([x[0]-1 for x in clipStart])
        startPosOri = startPosOri.astype(np.int32)
        stopPosOri = np.array([x[0]-1 for x in clipStop])  # 也要存储
        stopPosOri = stopPosOri.astype(np.int32)
        vadrs = {'info': info, 'clipStart': clipStart,
                  'clipStop': clipStop, 'startPos': startPosOri, 'stopPos': stopPosOri, 'ee_diff': ee_diff}  # 融合后的ee区域，未进行rmse加权。(最后要输出)

        return vadrs
