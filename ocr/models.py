# -*- coding: utf-8 -*-

from django.db import models
from datetime import datetime

# Create your models here.
class BaseModel(models.Model):
    """模型类基类"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加时间')
    update_time = models.DateTimeField(verbose_name='更新时间', default=datetime.now, help_text='更新时间')
    create_user_id = models.CharField(max_length=255, null=False, verbose_name='创建人id', help_text='创建人id')
    is_deleted = models.BooleanField(default=False, null=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.update_time = datetime.now()
        return super(BaseModel,self).save(*args,**kwargs)

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
    data_byte = models.CharField(max_length=255,null=True,default = "")
    data_type = models.CharField(max_length=255)
    height = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    class Meta:
        unique_together = ["ocrPDF", "frame_id"]

class ImageUserConf(BaseModel):
    """
    image:对应的图片
    rotate_degree:image角度
    polygon_id_thr:标记id起点，不包括边界
    """
    image = models.ForeignKey('PDFImage', on_delete=models.CASCADE)
    rotate_degree = models.FloatField(default=0,null=False)
    is_vertical = models.BooleanField(default=False)  # 文字排列方向
    filter_size = models.IntegerField(default=16, null=False)
    entropy_thr = models.FloatField(default=0.9,null=False)
    projection_thr_strict = models.FloatField(default=0.6,null=False)
    projection_thr_easing = models.FloatField(default=0.1,null=False)
    center_x = models.FloatField(default=0, null=False)
    center_y = models.FloatField(default=0, null=False)
    zoom_scale = models.FloatField(default=1, null=False)
    polygon_id_thr = models.IntegerField(default=-1, null=False)


    class Meta:
        unique_together = ["image", "create_user_id"]

class OcrLabelingPolygon(BaseModel):
    """
    ocr 的多边形标注数据
    pdfImage: 所属图片
    polygon: 标注多边形
    edit_count: 修正次数
    labeling_count: 标注文本内容的次数
    labeling_content: 是否标注了内容
    """
    pdfImage = models.ForeignKey('PDFImage', on_delete=models.CASCADE)  # 对应的PDF IMAGE
    polygon = models.BinaryField(null=True)  # json编码
    edit_count = models.IntegerField(default=0,null=False)
    labeling_count = models.IntegerField(default=0,null=False)
    labeling_content = models.BooleanField(null=False, default=False)


class Ocrmodel(BaseModel):
    name  =  models.CharField(max_length=255, null=False)
    desc  =  models.CharField(max_length=255, null=False)
    class Meta:
        unique_together = ["name", "create_user_id"]
    

class Modeldoc(BaseModel):
    """
    ocrmodel: 对应的模型
    doc: 对应的文档
    """
    ocrmodel = models.ForeignKey('Ocrmodel', on_delete=models.CASCADE) 
    doc = models.ForeignKey('OcrPDF', on_delete=models.CASCADE) 
    class Meta:
        unique_together = ["ocrmodel", "doc"]

class ChineseElem(BaseModel):
    """
    组成汉字的元素
    image_bytes: 元素实例图像
    desc: 相关描述
    """
    ocrmodel = models.ForeignKey('Ocrmodel', null=True, on_delete=models.CASCADE)
    image_bytes = models.CharField(max_length=256, null=True)
    height = models.IntegerField(null=False, default=128)
    width = models.IntegerField(null=False, default=128)
    desc_info = models.TextField(null=False, default="")
    

class CharacterElem(BaseModel):
    """
    character: 对应的汉字
    elem: 对应的偏旁
    """
    character  =  models.CharField(max_length=16, null=True)
    elem = models.ForeignKey('ChineseElem', on_delete=models.CASCADE) 
    class Meta:
        unique_together = ["character", "elem", "create_user_id"]


class PolygonElem(BaseModel):
    """
    标签对应的偏旁部首
    polygon:关系中的标注矩形
    elem:标注对应的偏旁部首
    """
    polygon = models.ForeignKey('OcrLabelingPolygon', on_delete=models.CASCADE)
    elem = models.ForeignKey('ChineseElem', on_delete=models.CASCADE)
    desc_info = models.TextField(null=True, default="")
    class Meta:
        unique_together = ["polygon", "elem", "create_user_id"]

class Training(BaseModel):
    trainmodel = models.ForeignKey('Ocrmodel', on_delete=models.CASCADE, null=False) 
    docs = models.TextField(blank=True, null=False)
    name  =  models.CharField(max_length=255, null=False)
    status = models.TextField(blank=True, null=False)
    isrotated = models.BooleanField(null=False, default=False)
    isresized = models.BooleanField(null=False, default=False)
    imagewidth = models.IntegerField(null=False, default=640)
    imageheight = models.IntegerField(null=False, default=640)
    fittype  =  models.CharField(max_length=32, null=False, default="contain")
    issplit = models.BooleanField(null=False, default=False)
    splitwidth = models.IntegerField(null=False, default=640)
    splitheight = models.IntegerField(null=False, default=640)
    splitoverlap = models.FloatField(null=False, default=0.25)  
    trainsize = models.IntegerField(null=False, default=640)
    trainbatch = models.IntegerField(null=False, default=8)
    trainepoch = models.IntegerField(null=False, default=4000)
    trainscale = models.CharField(null=False, default="yolov5m", max_length=32)
    device = models.CharField(null=False, default="gpu", max_length=32)

    
    class Meta:
        unique_together = ["trainmodel", "name", "create_user_id"]
