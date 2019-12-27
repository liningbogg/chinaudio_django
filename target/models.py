from django.db import models
from django.contrib.auth.models import AbstractUser

class BaseModel(models.Model):
    """模型类基类"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加时间')
    create_user_id = models.CharField(max_length=255, null=False, verbose_name='创建人id', help_text='创建人id')
    is_deleted = models.BooleanField(default=False, null=False)

    class Meta:
        abstract = True


# Create your models here.
class TargetUser(AbstractUser):
    wavefileRoot= models.CharField(max_length=255, default="/home/liningbo/waveFiles")
    test = models.CharField(max_length=255,null=True)

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
    objects = models.Manager()
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
    objects = models.Manager()
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
    objects = models.Manager()
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
    filter_rad = models.FloatField(default=30.0)
    cache_block_size = models.IntegerField(default=600)  # 缓存块大小，单位s
    fs = models.IntegerField(default=44100)
    play_fs = models.IntegerField(default=44100)  # 用于记录当前片段播放的fs
    primary_ref = models.CharField(max_length=255, default="combDescan")  # 主导算法数据
    medium_resampling = models.BooleanField(default=True)
    objects = models.Manager()

    class Meta:
        unique_together = ["title", "create_user_id", "nfft"]


class Stft(BaseModel):
    labeling = models.ForeignKey('Labeling', on_delete=models.CASCADE)  # 对应的labeling
    startingPos = models.IntegerField()
    length = models.IntegerField()
    src = models.BinaryField(null=True)
    objects = models.Manager()
    class Meta:
        unique_together = ["labeling", "startingPos", "length"]

class LabelingAlgorithmsConf(BaseModel):
    labeling = models.ForeignKey('Labeling', on_delete=models.CASCADE)  # 对应的labeling
    algorithms = models.CharField(max_length=255)  # 对应的算法
    is_filter = models.BooleanField(default=True)  # 是否采纳过滤后的频率
    anote = models.CharField(max_length=255,null=True)  # 注释
    objects = models.Manager()
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
    objects = models.Manager()


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
    objects = models.Manager()

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
    objects = models.Manager()

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
    objects = models.Manager()


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
    objects = models.Manager()


class OcrPDF(BaseModel):
    """
    用以ocr识别的pdf文件信息
    title:pdf名称
    file_name:pdf文件名
    file_size:pdf文件尺寸，单位KB
    frame_num:pdf帧数
    current_frame:当前帧标记位置
    manual_pos:如果指定位置则标记至指定值，否则为-1自动计算当前位置
    """
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_size = models.FloatField(default=0.0)
    frame_num = models.IntegerField(default=0)
    current_frame = models.IntegerField(default=0)
    is_vertical = models.BooleanField(default=False)  # 文字排列方向
    assist_num = models.IntegerField(default=0)
    objects = models.Manager()

    class Meta:
        unique_together = ["title", "create_user_id"]


class OcrAssist(BaseModel):
    """
    ocrPDF:OCRPDF源
    """
    ocrPDF = models.ForeignKey('OcrPDF', on_delete=models.CASCADE)  # 对应的OCRPDF
    current_frame = models.IntegerField(default=0)
    assist_user_name = models.CharField(max_length=255,null=True)
    is_vertical = models.BooleanField(default=False)  # 文字排列方向
    objects = models.Manager()
    class Meta:
        unique_together = ["ocrPDF", "assist_user_name"]    

class OcrAssistRequest(BaseModel):
    """
    """
    owner = models.CharField(max_length=255,null=True)
    title = models.CharField(max_length=255,null=True)
    status = models.CharField(max_length=255,null=True)
    class Meta:
        unique_together = ["owner", "create_user_id","title"]    

class PDFImage(BaseModel):
    """
    ocrPDF:对应的PDF
    frame_id:当前帧数
    data_byte:数据
    data_type:数据类型
    """
    ocrPDF = models.ForeignKey('OcrPDF', on_delete=models.CASCADE)  # 对应的PDF
    frame_id = models.IntegerField(default=-1)
    data_byte = models.BinaryField(null=True)
    data_type = models.CharField(max_length=255)
    height = models.IntegerField(default=0)
    width = models.IntegerField(default=0) 
    class Meta:
        unique_together = ["ocrPDF", "frame_id"]    

class ImageUserConf(BaseModel):
    """
    image:对应的图片 
    rotate_degree:image角度
    """
    image = models.ForeignKey('PDFImage', on_delete=models.CASCADE)
    rotate_degree = models.FloatField(default=0,null=False)
    is_vertical = models.BooleanField(default=False)  # 文字排列方向
    entropy_thr = models.FloatField(default=0.9,null=False)
    projection_thr = models.FloatField(default=0.35,null=False)

    class Meta:
        unique_together = ["image", "create_user_id"]

class OcrLabelingPolygon(BaseModel):
    """
    ocr 的多边形标注数据
    pdfImage: 所属图片
    polygon: 标注多边形
    """
    pdfImage = models.ForeignKey('PDFImage', on_delete=models.CASCADE)  # 对应的PDF IMAGE
    polygon = models.BinaryField(null=True)  # json编码
    is_fine = models.BooleanField(default=False)
