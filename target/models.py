from django.db import models


class BaseModel(models.Model):
    """模型类基类"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加时间')
    create_user_id = models.CharField(max_length=255, null=False, verbose_name='创建人id', help_text='创建人id')

    class Meta:
        abstract = True


# Create your models here.


class Clip(BaseModel):
    """
    title:曲名
    startingPos:数据起始位置
    length:数据长度,单位帧数
    src:数据源（fft）
    tar:标签
    """
    title = models.CharField(max_length=255)
    startingPos = models.IntegerField()
    length = models.IntegerField()
    src = models.BinaryField(null=True)
    tar = models.BinaryField(null=True)
    anote = models.CharField(max_length=255)
    nfft = models.IntegerField()
    
    class Meta:
        unique_together = ["title", "startingPos", "length", "create_user_id", "nfft"]


# 参考算法的中间结果
class AlgorithmsMediums(BaseModel):
    labeling = models.ForeignKey('Labeling', on_delete=models.CASCADE)  # 对应的labeling
    algorithms = models.CharField(max_length=255)
    startingPos = models.IntegerField()
    length = models.IntegerField()
    medium = models.BinaryField(null=True)
    anote = models.CharField(max_length=255)

    class Meta:
        unique_together = ["labeling", "algorithms", "startingPos", "length"]


class AlgorithmsClips(BaseModel):
    """
    算法形成的数据
    title:曲名
    startingPos:数据起始位置
    algorithms:算法名称
    length:数据长度,单位帧数
    fs:帧率
    nfft:短时傅里叶帧长
    tar:标签
    """
    labeling = models.ForeignKey('Labeling', on_delete=models.CASCADE)  # 对应的labeling
    algorithms = models.CharField(max_length=255)
    startingPos = models.IntegerField()
    length = models.IntegerField()
    tar = models.BinaryField(null=True)
    anote = models.CharField(max_length=255)

    class Meta:
        unique_together = ["labeling", "algorithms", "startingPos", "length"]


class Labeling(BaseModel):
    title = models.CharField(max_length=255)
    frameNum = models.IntegerField(default=0)
    nfft = models.IntegerField(default=4410)
    current_frame = models.IntegerField(default=0)  # 当前帧的计算，在labeling启动时候调用
    manual_pos = models.IntegerField(default=-1)  # 如果小于0，认为是自动位置，否则是指定位置，此时不计算current，此轮结束改回-1.
    extend_rad = models.IntegerField(default=60)  # 延展半径
    tone_extend_rad = models.IntegerField(default=60)  # 音调延展半径
    vad_thrart_EE = models.FloatField(default=0.1)
    vad_thrart_RMSE = models.FloatField(default=0.1)
    vad_throp_EE = models.FloatField(default=0.1)
    filter_rad = models.FloatField(default=30)
    fs = models.IntegerField(default=44100)
    play_fs = models.IntegerField(default=44100)  # 用于记录当前片段播放的fs
    primary_ref = models.CharField(max_length=255,default="combDescan")  # 主导算法数据
    medium_resampling = models.BooleanField(default=True)
    class Meta:
        unique_together = ["title", "create_user_id", "nfft"]

class Stft(BaseModel):
    labeling = models.ForeignKey('Labeling', on_delete=models.CASCADE)  # 对应的labeling
    startingPos = models.IntegerField()
    length = models.IntegerField()
    src = models.BinaryField(null=True)
    class Meta:
        unique_together = ["labeling", "startingPos", "length"]

class LabelingAlgorithmsConf(BaseModel):
    labeling = models.ForeignKey('Labeling', on_delete=models.CASCADE)  # 对应的labeling
    algorithms = models.CharField(max_length=255)  # 对应的算法
    is_filter = models.BooleanField(default=True)  # 是否采纳过滤后的频率
    anote = models.CharField(max_length=255,null=True)  # 注释
    class Meta:
        unique_together = ["labeling", "algorithms"]

class Tone(BaseModel):
    """
    pos:起始帧
    lengh:长度
    pitch：音高
    note:十二平均律标注
    tone:唱名 5-3 6+2 7 1+1 1-1
    anote:指法注释 s2 f7h9 a6h7.94
    """

    title = models.CharField(max_length=255)
    pos = models.IntegerField()
    length = models.IntegerField()
    pitch = models.FloatField()
    note = models.CharField(max_length=16)
    tone = models.CharField(max_length=16)
    anote = models.CharField(max_length=255)


class Wave(BaseModel):
    title = models.CharField(max_length=255)
    waveFile = models.CharField(max_length=255)
    frameNum = models.IntegerField(default=0)
    duration = models.FloatField()
    chin = models.BinaryField(null=True)
    ee = models.BinaryField(null=True)
    rmse = models.BinaryField(null=True)
    fs = models.IntegerField()
    nfft = models.IntegerField(default=4410)
    completion = models.FloatField()

    class Meta:
        unique_together = ["title", "create_user_id", "nfft"]

class Tune(BaseModel):
    tune_name = models.CharField(max_length=255)
    a4_hz = models.FloatField(default=440.0)
    do = models.CharField(max_length=16)
    note1 = models.CharField(max_length=16)
    note2 = models.CharField(max_length=16)
    note3 = models.CharField(max_length=16)
    note4 = models.CharField(max_length=16)
    note5 = models.CharField(max_length=16)
    note6 = models.CharField(max_length=16)
    note7 = models.CharField(max_length=16)
    class Meta:
        unique_together = ["tune_name", "create_user_id"]

class Log(BaseModel):
    """
    target操作记录
    title:与操作相关的曲目名称
    content:记录内容
    timestamp：时间戳
    """
    title = models.CharField(max_length=255)
    content = models.CharField(max_length=255)
    timestamp = models.DateTimeField()


class MarkedPhrase(BaseModel):
    """
    需要关注的音乐片段
    title:乐曲名称
    mark:标注
    """
    title = models.CharField(max_length=255)
    mark = models.CharField(max_length=255)
    start = models.FloatField()
    length = models.FloatField()
