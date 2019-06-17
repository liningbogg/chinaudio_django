"""
音高数据集获取,数据库转文件采用pickle
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pitch.settings")  # project_name 项目名称django.setup()
django.setup()
from target.models import Clip  # 数据条目
import pickle
import numpy as np
from scipy.interpolate import interp1d  # 用于线性插值
import math
from keras.models import Sequential
from keras.layers import Dense, Dropout

fs = 44100  # 采样率常量
init_frq = 40  # 低频截断40hz
cutoff_frq = 4000  # 截断频率
extend_frq = 4100  # 保障截断频率的延伸截断频率
base = 55  # 音高基础频率
times = 5  # 最大音高阶数
simi_num = 12  # 半音数目
resultion = 50 * simi_num  # 分辨率, 一个半音切分50份


# 获取样本输入及其输出
def achieve_src_tar(clips):
    src = []  # 网络输入
    tar = []  # 网络输出
    tar_pitch = []  # 原始输出
    for clip in clips:
        # 获取src
        src_ori = pickle.loads(clip.src)
        extend_num = int(extend_frq*clip.nfft/fs)  # 延伸输入的数目
        # 在延伸片段上做插值,扩展至fs对应的分辨率(1 hz)
        extendx = np.arange(0, extend_num)  # 原始x坐标
        extendy = src_ori[extendx]  # 原始y坐标
        finterp = interp1d(extendx, extendy, kind='linear')  # 线性内插配置
        x_pred = np.linspace(0, extendx[extend_num - 1] * 1.0,
                             int(extendx[extend_num - 1] * fs / clip.nfft) + 1)  # 插值输入,不代表实际频率
        y_pred = finterp(x_pred)  # 重采样延功率谱
        src_resampled = y_pred[0:cutoff_frq]  # 重采样并且截断频率的样本src
        src_resampled[0:init_frq] = 0  # 截断低频
        src.append(src_resampled)

        # 获取tar
        tar_nodes = times*resultion  # 输出节点数目
        tar_item = np.zeros(tar_nodes)  # 样本输入
        tar_ori = pickle.loads(clip.tar)
        for pitch in tar_ori:
            index_pitch = round(math.log(pitch/base, 2)/times*tar_nodes)  # 音高索引
            tar_item[index_pitch] = 1
        tar.append(tar_item)
        tar_pitch.append(tar_ori)
    return {"src": src, "tar": tar, "tar_pitch":tar_pitch }


clips = Clip.objects.all()  # 获取所有待处理样本
print("共有 "+str(clips.count()) + " 样本.")
src_tar = achieve_src_tar(clips)  # 获取样本输入及其输出
src = src_tar["src"]
tar = src_tar["tar"]
tar_pitch = src_tar["tar_pitch"]
# create model
model = Sequential()
model.add(Dense(units=len(tar[0]), input_dim=len(src[0]), kernel_initializer='uniform', activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(units=len(tar[0]), kernel_initializer='uniform', activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(units=len(tar[0]), kernel_initializer='uniform', activation='sigmoid'))
# Compile model
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
# Fit the model
model.fit(np.array(src[0:2000]), np.array(tar[0:2000]), epochs=60, batch_size=32,  verbose=2)
# calculate predictions
predictions = model.predict(np.array(src[2000:-1]))
count = 0
for pitch in predictions:
    print(base*math.pow(2,np.argmax(pitch)/(times*resultion)*5), tar_pitch[2000+count])
    count = count+1
