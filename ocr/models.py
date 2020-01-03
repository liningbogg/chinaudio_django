from django.db import models

# Create your models here.
class BaseModel(models.Model):
    """模型类基类"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', help_text='添加时间')
    create_user_id = models.CharField(max_length=255, null=False, verbose_name='创建人id', help_text='创建人id')
    is_deleted = models.BooleanField(default=False, null=False)

    class Meta:
        abstract = True

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
    projection_thr_strict = models.FloatField(default=0.6,null=False)
    projection_thr_easing = models.FloatField(default=0.1,null=False)

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

