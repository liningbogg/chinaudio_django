from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
import os
from io import BytesIO
import io
import numpy as np
import math
from pitch.np_encoder import NpEncoder
import json
import redis
from PIL import Image, ImageOps
from django.db.models import Max
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.contrib import *
from ocr.models import *
from django import db
import datetime
import copy
import time
import cv2 as cv
from django.core.cache import cache
import pickle
from pitch.np_encoder import NpEncoder
from pitch.check_auth import check_login
from PIL import Image
import traceback


# 归一化函数
def maxminnormalization(x, minv, maxv):
    min_val = np.min(x)
    max_val = np.max(x)
    y = (x - min_val) / (max_val - min_val + 0.0000000001) * (maxv - minv) + minv
    return y


def cal_rotate_angle(x0, y0, x3, y3):

    """
    calulate rotate angle from new position
    x0, y0: position 0 rotated
    x3, y3: position 3 rotated
    """
    try:
        angle = -math.atan((x0-x3)*1.0/(y0-y3))*180/math.pi
        return angle
    except Exception as e:
        return 0


def rotate_points(points, rotate_degree, w, h):
    for point in points:
        x = point['x']
        y = point['y']
        x_shift = x - w/2.0
        y_shift = y - h/2.0
        rotate_rad = rotate_degree/180.0*math.pi
        nx = x_shift*math.cos(rotate_rad)+y_shift*math.sin(rotate_rad)+w/2.0
        ny = -x_shift*math.sin(rotate_rad)+y_shift*math.cos(rotate_rad)+h/2.0
        point['x']=nx
        point['y']=ny


def bounding_points(points):
    x_min = 10000000
    y_min = 10000000
    x_max = -10000000
    y_max = -10000000
    for point in points:
        x = point["x"]
        y = point["y"]
        x_min = min(x_min, x)
        x_max = max(x_max, x)
        y_min = min(y_min, y)
        y_max = max(y_max, y)
    points[0]["x"] = x_min
    points[0]["y"] = y_min
    points[1]["x"] = x_max
    points[1]["y"] = y_min
    points[2]["x"] = x_max
    points[2]["y"] = y_max
    points[3]["x"] = x_min
    points[3]["y"] = y_max


# Create your views here.
class OcrView(View):

    def __init__(self):
        super(View, self).__init__()
        self.redis_pool=redis.ConnectionPool(host='localhost', port=6379,db=0, password='1a2a3a', encoding='utf-8')

    @staticmethod
    def saveData():
        try:
            query = ChineseElem.objects.all()
            all_num = query.count()
            print(all_num)
            delete_count = 0
            for elem in query:
                create_user = elem.create_user_id
                user_list = ['root', 'pi', 'test']

                path = "/home/liningbo/data_chinaudio/elemimage/%s_%d.jpg" % ("elemimage", elem.id)

                blob = elem.image_bytes
                file_blob = open(path,"wb")
                file_blob.write(blob)
                file_blob.close()
                print(path)

        except Exception as e:
            print(e)

    @staticmethod
    def moveData():
        try:
            query = ChineseElem.objects.all()
            all_num = query.count()
            print(all_num)
            delete_count = 0
            for elem in query:
                create_user = elem.create_user_id
                user_list = ['root', 'pi', 'test']

                path = "/home/liningbo/data_chinaudio/elemimage/%s_%d.jpg" % ("elemimage", elem.id)
                elem.image_bytes=path
                elem.save()
                print(path)

        except Exception as e:
            print(e)

    @method_decorator(check_login)
    def get_docs(self, request):
        """
        :param request:
        :return:
        """
        try:
            body = []
            userid = str(request.user)
            ocrDocList = OcrPDF.objects.filter(create_user_id=userid, is_deleted=False)
            for ocrdoc in ocrDocList.iterator():
                count_all = 0
                count_user = 0
                image_set = PDFImage.objects.filter(ocrPDF=ocrdoc).values("id")
                for image in image_set.iterator():
                    count_all_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"]).count()
                    count_all = count_all_inc + count_all
                    if count_all_inc > 0:
                        count_user_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"], create_user_id = userid).count()
                        count_user = count_user + count_user_inc
                data = {"id":ocrdoc.id,"title":ocrdoc.title,"frameNum":ocrdoc.frame_num,"currentframe":ocrdoc.current_frame,"assistnum":ocrdoc.assist_num ,"labelNum":count_all,"userlabelNum":count_user}
                body.append(data)
            
            result = {"status":"success" , "username":str(request.user), "tip": "获取docs成功", "body":body}
            return JsonResponse(result)
        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def get_docsassist(self, request):
        """
        :param request:
        :return:
        """
        try:
            body = []
            userid = str(request.user)
            ocr_assist_set = OcrAssist.objects.filter(assist_user_name=userid, is_deleted=False)
            for ocrassist in ocr_assist_set:
                ocrdoc = ocrassist.ocrPDF
                count_all = 0
                count_user = 0
                image_set = PDFImage.objects.filter(ocrPDF=ocrdoc).values("id")
                for image in image_set.iterator():
                    count_all_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"]).count()
                    count_all = count_all_inc + count_all
                    if count_all_inc > 0:
                        count_user_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"], create_user_id = userid).count()
                        count_user = count_user + count_user_inc
                data = {"id":ocrdoc.id,"title":ocrdoc.title,"frameNum":ocrdoc.frame_num,"currentframe":ocrdoc.current_frame,"assistnum":ocrdoc.assist_num ,"labelNum":count_all,"userlabelNum":count_user}
                body.append(data)

            result = {"status":"success" , "username":str(request.user), "tip": "获取docs成功", "body":body}
            return JsonResponse(result)
        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @classmethod
    @method_decorator(login_required)
    def index(cls, request):
        """
        古琴数字化数据库首页
        """
        try:
            user_id = str(request.user)
            ocrPDFList = OcrPDF.objects.filter(create_user_id=request.user, is_deleted=False)
            assist_request_in_set = OcrAssistRequest.objects.filter(owner=user_id,status="pushed")
            assist_request_out_set = OcrAssistRequest.objects.filter(create_user_id=user_id)
            ocr_assist_set = OcrAssist.objects.filter(assist_user_name=user_id, is_deleted=False)
            statistic = []
            for ocrpdf in ocrPDFList.iterator():
                count_all = 0
                count_user = 0
                image_set = PDFImage.objects.filter(ocrPDF=ocrpdf).values("id")
                for image in image_set.iterator():
                    count_all_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"]).count()
                    count_all = count_all_inc + count_all
                    if count_all_inc > 0:
                        count_user_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"], create_user_id = user_id).count()
                        count_user = count_user + count_user_inc
                data = {"id":ocrpdf.id,"title":ocrpdf.title,"frame_num":ocrpdf.frame_num,"current_frame":ocrpdf.current_frame,"assist_num":ocrpdf.assist_num ,"count_all":count_all,"count_user":count_user}
                statistic.append(data)

            context = {"assist_request_in_set":assist_request_in_set,"assist_request_out_set":assist_request_out_set,"ocr_assist_set":ocr_assist_set,"statistic":statistic}
            return render(request,'ocr_index.html',context)
        except Exception as e:
            print(e)


    @method_decorator(check_login)
    def get_polygon_num(self, request):
        """
        :param request:
        :return:
        """
        try:
            body=None
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('currentframe'))
            doc = OcrPDF.objects.get(id=docid)
            image = doc.pdfimage_set.get(frame_id=currentframe)
            polygonnumall = image.ocrlabelingpolygon_set.all().count()
            polygonnumuser = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user)).count()

            body={
                "polygonnumall":polygonnumall,
                "polygonnumuser":polygonnumuser,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "获取帧号成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(login_required)
    def get_polygon_elem_statistic(self, request):
        try:
            username = str(request.user)
            latest_number_polygon = 0  # 最近1小时的数据量
            latest_number_elem = 0  # 最近1小时的数据量
            count_all_polygon = 0  # polygon总数
            count_all_elem = 0  # elem总数
            now_time = datetime.datetime.now()
            datetime_from = now_time - datetime.timedelta(hours=1)
            latest_distribute_polygon = np.zeros(60)  # 最近一小时标注量分布
            latest_distribute_elem = np.zeros(60)  # 最近一小时标注量分布
            count_all_polygon = OcrLabelingPolygon.objects.filter(create_user_id=username, labeling_content=True).count()
            count_all_elem = PolygonElem.objects.filter(create_user_id=username).count()

            latest_set_polygon = OcrLabelingPolygon.objects.filter(create_user_id=username, labeling_content=True, update_time__range=(datetime_from, now_time)).values("update_time")
            for item in latest_set_polygon:
                latest_distribute_polygon[59 - (now_time-item["update_time"]).seconds //60] += 1
            latest_set_elem = PolygonElem.objects.filter(create_user_id=username, update_time__range=(datetime_from, now_time)).values("update_time")
            for item in latest_set_elem:
                latest_distribute_elem[59 - (now_time-item["update_time"]).seconds //60] += 1
            latest_number_polygon = latest_set_polygon.count()
            latest_number_elem = latest_set_elem.count()
            context = {"count_all_polygon":count_all_polygon, "count_all_elem":count_all_elem ,"latest_number_polygon":latest_number_polygon, "latest_number_elem":latest_number_elem, "latest_distribute_polygon": list(latest_distribute_polygon), "latest_distribute_elem": list(latest_distribute_elem)}
            return HttpResponse(json.dumps(context))

        except Exception as e:
            print(e)


    @classmethod
    @method_decorator(login_required)
    def get_polygon_statistic(cls, request):
        try:
            user_id = str(request.user)
            image_id = request.GET.get("image_id")
            pdfimage = PDFImage.objects.get(id=image_id)
            pdf = pdfimage.ocrPDF
            count_all = 0
            count_user = 0
            latest_number = 0
            now_time = datetime.datetime.now()
            datetime_from = now_time-datetime.timedelta(hours=1)
            image_set = PDFImage.objects.filter(ocrPDF=pdf).values("id")
            latest_distribute = np.zeros(60)
            for image in image_set.iterator():
                count_all_inc = OcrLabelingPolygon.objects.filter(pdfImage=image["id"]).count()
                count_all = count_all + count_all_inc
                if count_all_inc > 0:
                    count_user_inc =  OcrLabelingPolygon.objects.filter(pdfImage=image["id"],create_user_id = user_id).count()
                    count_user = count_user + count_user_inc
                    if count_user_inc > 0:
                        # 标注速率统计
                        latest_set = OcrLabelingPolygon.objects.filter(pdfImage=image["id"], create_user_id=user_id, create_time__range=(datetime_from, now_time)).values("create_time")
                        latest_number += len(latest_set)
                        for item in latest_set:
                            latest_distribute[59 - (now_time-item["create_time"]).seconds //60] += 1

                        
            context = {"count_all":count_all,"count_user":count_user, "latest_number":latest_number, "latest_distribute": list(latest_distribute)}
            return HttpResponse(json.dumps(context))
        except Exception as e:
            print(e)
            return HttpResponse("err")

    def getYolov3DataDDG(self, request):
        try:
            class_type = [
                "anus",
                "bybby",
                "dildo",
                "vulva",
            ]
            username = "DDG"
            labeling_dict = {}
            polygon_set = OcrLabelingPolygon.objects.filter(create_user_id=username, labeling_content=True)
            for polygon in polygon_set:
                elem_set = polygon.polygonelem_set.all()
                if elem_set.count() == 0:
                    continue
                polygonelem = elem_set[0]    
                classtype = polygonelem.elem.desc_info
                image = polygon.pdfImage.data_byte
                if image not in labeling_dict:
                    labeling_dict[image]={
                        "polygon_list":[]
                    }
                else:
                    pass

                polygonarr = json.loads(polygon.polygon)
                elem = {
                    "class": classtype, 
                    "box":[
                        polygonarr[0]['x'],
                        polygonarr[0]['y'],
                        polygonarr[2]['x'],
                        polygonarr[2]['y'],
                    ]
                }
                labeling_dict[image]["polygon_list"].append(elem)
            with open("/home/liningbo/yolov3/data/train.txt", "w") as file_train:
                for labeling in labeling_dict:
                    filename = os.path.split(labeling)[1].split(".")[0]
                    pathname = "./data/image_split/%s.jpg" % filename
                    file_train.write(pathname)
                    polygon_list = labeling_dict[labeling]["polygon_list"]
                    for polygon in polygon_list:
                        class_index = class_type.index(polygon['class'])
                        box = polygon['box']
                        line = " %d,%d,%d,%d,%d" % (box[0], box[1], box[2], box[3], class_index)
                        file_train.write(line)
                    file_train.write("\n")

                    args={
                        "path": labeling,
                    }
                    red = redis.Redis(connection_pool=self.redis_pool)
                    red.rpush("yolov3AchieveTask", json.dumps(args))  # 此处不做重复性检查
            return HttpResponse("/home/liningbo/yolov3/data")
        except Exception as e:
            print(e)
            print(e.__traceback__.tb_lineno)
            return HttpResponse("获取yolov3数据失败.")
            
    def getYolov3Data(self, request):
        try:
            class_type = [
                "melon",
                "pea2",   
                "torch",  
                "Flower", 
                "pea1",   
                "cushaw", 
                "nuts",   
                "pumpkin",
                "pepper", 
                "nutl",   
                "zombi0",
                "sun",
                "ball",
                "dolly",
                "dead0",
                "shovel",
                "block",
                "head0",
                "zombiBlock",
                "fireBall"
            ]
            username = "pvz0"
            labeling_dict = {}
            polygon_set = OcrLabelingPolygon.objects.filter(create_user_id=username, labeling_content=True)
            for polygon in polygon_set:
                elem_set = polygon.polygonelem_set.all()
                if elem_set.count() == 0:
                    continue
                polygonelem = elem_set[0]    
                classtype = polygonelem.elem.desc_info
                image = polygon.pdfImage.data_byte
                if image not in labeling_dict:
                    labeling_dict[image]={
                        "polygon_list":[]
                    }
                else:
                    pass

                polygonarr = json.loads(polygon.polygon)
                elem = {
                    "class": classtype, 
                    "box":[
                        polygonarr[0]['x'],
                        polygonarr[0]['y'],
                        polygonarr[2]['x'],
                        polygonarr[2]['y'],
                    ]
                }
                labeling_dict[image]["polygon_list"].append(elem)
            with open("/home/liningbo/yolov3/data/train.txt", "w") as file_train:
                for labeling in labeling_dict:
                    filename = os.path.split(labeling)[1].split(".")[0]
                    pathname = "./data/image_split/%s.jpg" % filename
                    file_train.write(pathname)
                    polygon_list = labeling_dict[labeling]["polygon_list"]
                    for polygon in polygon_list:
                        class_index = class_type.index(polygon['class'])
                        box = polygon['box']
                        line = " %d,%d,%d,%d,%d" % (box[0], box[1], box[2], box[3], class_index)
                        file_train.write(line)
                    file_train.write("\n")

                    args={
                        "path": labeling,
                    }
                    red = redis.Redis(connection_pool=self.redis_pool)
                    red.rpush("yolov3AchieveTask", json.dumps(args))  # 此处不做重复性检查
            return HttpResponse("/home/liningbo/yolov3/data")
        except Exception as e:
            print(e)
            print(e.__traceback__.tb_lineno)
            return HttpResponse("获取yolov3数据失败.")

    def getYolov3DataOld(self, request):
        try:
            class_type = [
                "melon",
                "pea2",   
                "torch",  
                "Flower", 
                "pea1",   
                "cushaw", 
                "nuts",   
                "pumpkin",
                "pepper", 
                "nutl",   
                "zombi0",
                "sun",
                "ball",
                "dolly",
                "dead0",
                "shovel",
                "block",
                "head0",
                "zombiBlock",
                "fireBall"
            ]
            username = "pvz0"
            shape_size = json.loads(request.GET.get("shape_size"))
            labeling_dict = {}
            polygon_set = OcrLabelingPolygon.objects.filter(create_user_id=username, labeling_content=True)
            print(polygon_set.count())
            for polygon in polygon_set:
                elem_set = polygon.polygonelem_set.all()
                if elem_set.count() == 0:
                    continue
                polygonelem = elem_set[0]    
                classtype = polygonelem.elem.desc_info
                image = polygon.pdfImage.data_byte
                if image not in labeling_dict:
                    padding_l=0
                    padding_r=0
                    padding_t=0
                    padding_b=0
                    resize_height = 0
                    resize_width = 0
                    height = polygon.pdfImage.height
                    width = polygon.pdfImage.width
                    ratio = shape_size*1.0/max(height, width)
                    if height > width:
                        resize_height = shape_size
                        resize_width = int(width*ratio)
                        padding_w = shape_size-resize_width
                        padding_l = padding_w //2
                        padding_r = padding_w - padding_l
                    else:
                        resize_height = int(height*ratio)
                        resize_width = shape_size
                        padding_h = shape_size-resize_height
                        padding_t = padding_h // 2
                        padding_b = padding_h - padding_t
                    labeling_dict[image]={
                        "resize_height": resize_height,
                        "resize_width": resize_width,
                        "padding_l": padding_l,
                        "padding_t": padding_t,
                        "padding_r": padding_r,
                        "padding_b": padding_b,
                        "shape_size": shape_size,
                        "ratio": ratio,
                        "polygon_list":[]
                    }
                else:
                    pass

                padding_l = labeling_dict[image]["padding_l"]    
                padding_t = labeling_dict[image]["padding_t"]    
                ratio = labeling_dict[image]["ratio"]    
                polygonarr = json.loads(polygon.polygon)
                print(class_type)
                elem = {
                    "class": classtype, 
                    "box":[
                        polygonarr[0]['x']*ratio + padding_l,
                        polygonarr[0]['y']*ratio + padding_t,
                        polygonarr[2]['x']*ratio + padding_l,
                        polygonarr[2]['y']*ratio + padding_t,
                    ]
                }
                labeling_dict[image]["polygon_list"].append(elem)
            with open("/home/liningbo/yolov3/data/train.txt", "w") as file_train:
                for labeling in labeling_dict:
                    filename = os.path.split(labeling)[1].split(".")[0]
                    pathname = "./data/image_split/%s.jpg" % filename
                    file_train.write(pathname)
                    polygon_list = labeling_dict[labeling]["polygon_list"]
                    for polygon in polygon_list:
                        class_index = class_type.index(polygon['class'])
                        print(class_index)
                        box = polygon['box']
                        line = " %d,%d,%d,%d,%d" % (box[0], box[1], box[2], box[3], class_index)
                        file_train.write(line)
                    file_train.write("\n")

                    args={
                        "path": labeling,
                        "resize_height": labeling_dict[labeling]["resize_height"],
                        "resize_width": labeling_dict[labeling]["resize_width"],
                        "padding_l": labeling_dict[labeling]["padding_l"],
                        "padding_t": labeling_dict[labeling]["padding_t"],
                        "padding_r": labeling_dict[labeling]["padding_r"],
                        "padding_b": labeling_dict[labeling]["padding_b"],
                    }
                    red = redis.Redis(connection_pool=self.redis_pool)
                    red.rpush("yolov3AchieveTask", json.dumps(args))  # 此处不做重复性检查
            return HttpResponse("/home/liningbo/yolov3/data")
        except Exception as e:
            print(e)
            print(e.__traceback__.tb_lineno)
            return HttpResponse("获取yolov3数据失败.")
    
    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request(cls, request):
        """
        申请协助其他用户进行标注
        :param request:
        :return:
        """
        pdfs_dict = {}
        try:
            user_id = str(request.user)
            pdfs_set = OcrPDF.objects.filter(~Q(create_user_id=user_id))
            for pdf in pdfs_set:
                pdfs_dict[pdf.id]={"title":str(pdf.title),"create_user_id":pdf.create_user_id,"assist_num":pdf.assist_num}
            assist_set = OcrAssist.objects.filter(create_user_id=user_id)
            for assist in assist_set:
                if assist.ocrPDF in pdfs_dict:
                    pdfs_dict.pop(assist.ocrPDF)
        except Exception as e:
            print(e)
        context = {'pdfs': pdfs_dict}
        return render(request, 'ocr_ocrPDF_assist_request.html', context)

    @method_decorator(login_required)
    def sub_and_execute_assist_ocr(self,request):
        try:
            user_id = str(request.user)
            pdfs_selected = json.loads(request.GET.get("pdfs_selected"))
            context_str="request pushed."
            success_str="\nsuccess:"
            fault_str="\nfault:"
            for pdf in pdfs_selected:
                owner_name = pdf["user_name"]
                pdf_title = pdf["pdf_title"]
                try:
                    OcrAssistRequest(owner=owner_name,title=pdf_title,create_user_id=user_id,status="pushed").save()
                    success_str=success_str+"\n    "+owner_name+"/"+pdf_title+";";
                except Exception as e:
                    print(e)
                    fault_str=fault_str+"\n   "+owner_name+"/"+pdf_title+";"
            return HttpResponse(context_str+success_str+fault_str)
        except Exception as e:
            return HttpResponse("err")

    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request_accept(cls, request):
        """
        通过其他用户的协助申请
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            assert user_name == request.GET.get("owner")
            assist_user_name = request.GET.get("create_user_id")
            pdf_title = request.GET.get("title")
            ocrPDF = OcrPDF.objects.get(create_user_id=user_name,title=pdf_title)
            ocrAssist = OcrAssist(ocrPDF=ocrPDF,current_frame=0,assist_user_name=assist_user_name,create_user_id=user_name)
            ocrPDF.assist_num=ocrPDF.assist_num+1
            ocrPDF.save()
            ocrAssist.save()
            ocrAssistRequest = OcrAssistRequest.objects.get(owner=user_name,create_user_id=assist_user_name,title=pdf_title)
            ocrAssistRequest.status="accepted"
            ocrAssistRequest.save()
        except Exception as e:
            print(e)
        finally:
            return redirect('/ocr/index')

    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request_deny(cls, request):
        """
        拒绝其他用户的协助申请
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            assert user_name == request.GET.get("owner")
            assist_user_name = request.GET.get("create_user_id")
            pdf_title = request.GET.get("title")
            ocrAssistRequest = OcrAssistRequest.objects.get(owner=user_name,create_user_id=assist_user_name,title=pdf_title)
            ocrAssistRequest.status="denied"
            ocrAssistRequest.save()

        except Exception as e:
            print(e)
        finally:
            return redirect('/ocr/index')

    @classmethod
    @method_decorator(login_required)
    def delete_ocr_labeling(cls, request):
        """
        删除pdf或者协助
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            class_id = request.GET.get("id")
            class_type = request.GET.get("class_type")
            if class_type == "ocr_pdf":
                ocrpdf = OcrPDF.objects.get(id=class_id)
                ocrpdf.is_deleted = True
                ocrpdf.save()
            elif class_type == "ocr_assist":
                ocrassistuser = OcrAssist.objects.get(id=class_id)
                ocrassistuser.is_deleted = True
                ocrassistuser.save()
            else:
                print(class_type)
        except Exception as e:
            print(e)
        finally:
            return redirect('/ocr/index')

    @classmethod
    @method_decorator(login_required)
    def ocrPDF_assist_request_delete(cls, request):
        """
        拒绝其他用户的协助申请
        :param request:
        :return:
        """
        try:
            user_name = str(request.user)  # 当前用户名
            owner = request.GET.get("owner")
            assist_user_name = request.GET.get("create_user_id")
            pdf_title = request.GET.get("title")
            ocrAssistRequest = OcrAssistRequest.objects.get(owner=owner,create_user_id=assist_user_name,title=pdf_title)
            ocrAssistRequest.status="deleted"
            ocrAssistRequest.delete()

        except Exception as e:
            print(e)
        finally:
            return redirect('/ocr/index')
    
    def handle_upload_file_pdf(self, upload_file, path, user_id):
        if not os.path.exists(path):
            os.makedirs(path)
            print("文件夹已经创建:"+path)
        file_name = path + upload_file.name
        base_name = upload_file.name.split(".")[0]
        already = OcrPDF.objects.filter(create_user_id=user_id, title=base_name)  # 已经存在的pdf
        if already.count() == 0:
            try:
                destination = open(file_name, 'wb+')
                for chunk in upload_file.chunks():
                    destination.write(chunk)
                destination.close()
                # 插入数据库
                ocrPDFItem = OcrPDF(
                    create_user_id=user_id,
                    title=base_name,
                    file_name=file_name,

                )
                ocrPDFItem.save()
                # 解压pdf
                args={
                    "create_user_id":user_id,
                    "title":base_name,
                    "file_name":file_name,
                    "ocrPDF_id":ocrPDFItem.id
                }
                red = redis.Redis(connection_pool=self.redis_pool)
                red.rpush("pdfUnpackTask", json.dumps(args))  # 此处不做重复性检查

            except Exception as e:
                print(e)
                return "err"
        else:
            print(base_name + " already existed")
            return "err"


    @method_decorator(login_required)
    def addpdfs(self,request):
        if request.method == 'POST':
            content = request.FILES.getlist("upload_pdf")
            if not content:
                return HttpResponse("没有上传内容")
            user_id = str(request.user)
            path = "/home/liningbo/pdfFiles/"+user_id+"/"
            for pdf in content:
                self.handle_upload_file_pdf(pdf, path, user_id)
        return HttpResponse("add pdfs done")


    @method_decorator(check_login)
    def nextpolygoninfo(self, request):
        """
        :param request:
        :return:
        """
        try:
            body=None
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('current_frame'))
            doc = OcrPDF.objects.get(id=docid)
            image = doc.pdfimage_set.get(frame_id=currentframe)
            imageuserconf = image.imageuserconf_set.get(create_user_id=str(request.user))
            non_label_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user), id__gt=imageuserconf.polygon_id_thr)
            if non_label_set.count() == 0:
                result = {"status":"failure" , "username":str(request.user), "tip":"没要要进行的标注"}
                return JsonResponse(result)
            else:
                polygon = non_label_set[0]
                body={
                    "polygonid": polygon.id,
                }
                result = {"status":"success" , "username":str(request.user), "tip": "获取polygonid成功", "body":body}
                return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def get_elemselected(self, request):
        """
        :param request:
        :return:
        """
        try:
            body=None
            polygonid = int(request.GET.get('polygonid'))
            polygon_label = OcrLabelingPolygon.objects.get(id=polygonid)
            elem_selected = []
            polygonElemSet = polygon_label.polygonelem_set.filter(create_user_id=str(request.user))
            for polygonElem in polygonElemSet:
                elem_selected.append(polygonElem.elem.id)
            body={
                "elemselected":elem_selected,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "获取elemselected成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(login_required)
    def content_labeling(self, request):
        try:
            image_id = request.GET.get('image_id')  # image_id
            image_user_conf_id = request.GET.get('image_user_conf_id')
            conf = ImageUserConf.objects.get(id=image_user_conf_id)
            polygon_id_pre = conf.polygon_id_thr
            pdfimage = PDFImage.objects.get(id=image_id)
            pdf = pdfimage.ocrPDF
            image_width = pdfimage.width
            padding_size = 128
            image_height = pdfimage.height
            non_label_set = pdfimage.ocrlabelingpolygon_set.filter(create_user_id=str(request.user), id__gt=polygon_id_pre)
            if non_label_set.count() == 0:
                return HttpResponse("当页不存在要进行的标注")
            else:
                elem_selected = []
                polygon_label = non_label_set[0]
                polygonElemSet = polygon_label.polygonelem_set.all()
                for polygonElem in polygonElemSet:
                    elem_selected.append(polygonElem.elem.id)
                polygon_id = polygon_label.id
                polygon = str(polygon_label.polygon,'utf-8')
                points = json.loads(polygon)
                # 获取旋转角度
                degree_to_rotate = cal_rotate_angle(points[0]['x'], points[0]['y'], points[3]['x'], points[3]['y'])
                # 旋转
                
                rotate_points(points, degree_to_rotate, image_width, image_height)
                # 外接
                bounding_points(points)

                rotate_image_key = "%s_%s_%.2f" % (str(request.user), image_id, degree_to_rotate)
                image_rotate = cache.get(rotate_image_key)
                if image_rotate is None:
                    #读取原始图像
                    pil_image = Image.open(pdfimage.data_byte)
                    width, height = pil_image.size
                    if abs(degree_to_rotate)>0.000001:
                        image_rotate = pil_image.rotate(degree_to_rotate)
                    else:
                        image_rotate = pil_image
                    cache.set(rotate_image_key, pickle.dumps(image_rotate), nx=True) 
                    cache.expire(rotate_image_key, 3600)
                else:
                    image_rotate = pickle.loads(image_rotate)
                
                rect_info = OcrView.get_rect_info(points[0], points[2])
                rect = (round(rect_info['x']), round(rect_info['y']), round(rect_info['x_']), round(rect_info['y_']))
                area = (rect_info['x_']-rect_info['x'])*(rect_info['y_']-rect_info['y'])
                if area <= 0:
                    polygon_label.delete()
                    return HttpResponse("标注矩形错误，已经删除请刷新。")
                image_crop = image_rotate.crop(rect)
                image_crop = image_crop.convert("L")
                width ,height = image_crop.size
                width_ocr = 64
                height_ocr = 64
                ratio_w =width*1.0/width_ocr
                ratio_h =height*1.0/height_ocr
                ratio = max(ratio_w, ratio_h)
                tar_width = min(int(width/ratio),width_ocr)
                tar_height = min(int(height/ratio),height_ocr)
                if tar_width*tar_height <=0 :
                    polygon_label.delete()
                    return HttpResponse("标注矩形过小，已删除，请刷新。")

                image_resized = image_crop.resize((tar_width, tar_height), Image.ANTIALIAS)
                tar_width, tar_height = image_resized.size
                w_extend = width_ocr - tar_width
                h_extend = height_ocr - tar_height
                w_l_extend = w_extend // 2
                w_r_extend = w_extend -w_l_extend
                h_t_extend = h_extend // 2
                h_b_extend = h_extend -h_t_extend

                image_padding = ImageOps.expand(image_resized, border=(w_l_extend, h_t_extend, w_r_extend, h_b_extend) ,fill=0)
                image_flat = list(image_padding.getdata())
                # algorithm = ['dot_64bit', 'resnet_withoutdot']
                algorithm = ['resnet_withdot']

                args={
                    "create_user_id":str(request.user),
                    "image_id":image_id,
                    "polygon_id":polygon_id,
                    "image":image_flat,
                    "algorithm":algorithm
                }
                red = redis.Redis(connection_pool=self.redis_pool)
                red.rpush("aiocr", json.dumps(args))  # 此处不做重复性检查
                


                for point in points:
                    point['x'] = round(point['x']) + padding_size
                    point['y'] = round(point['y']) + padding_size
                # 求取偏移
                w = abs(points[1]['x']-points[0]['x'])
                h = abs(points[3]['y']-points[0]['y'])
                size = max(h, w)
                size = max(size*2, 9)
                relative_l = (size-w) // 2
                relative_t = (size-h) // 2
                relative_r = int(relative_l + w)
                relative_b = int(relative_t + h)
                relative_box = (relative_l, relative_t, relative_r, relative_b)
                
                # 循环查看redis结果，最多20*10ms
                rs_key = "%s_%s_%s_%s" % ("rs_aiocr", str(request.user), image_id, polygon_id)
                ai_ocr = []
                for i in range(20):
                    if red.exists(rs_key):
                        ai_ocr = json.loads(red.get(rs_key))
                        red.delete(rs_key)
                        break
                    else:
                        time.sleep(0.01)
                    

                context = {
                    "title":pdf.title,
                    "image_id":image_id,
                    "polygon_id":polygon_id,
                    "polygon":polygon,
                    "relative_box":json.dumps(relative_box),
                    "size":size,
                    "frame_id":pdfimage.frame_id,
                    "image_width":image_width,
                    "degree_to_rotate":degree_to_rotate,
                    "image_height":image_height,
                    "frame_num":pdf.frame_num,
                    "x_shift":points[0]['x'] - ((size-w) // 2) ,
                    "y_shift":points[0]['y'] - ((size-h) // 2) ,
                    "x_shift_without_padding":points[0]['x'] - ((size-w) // 2) - padding_size,
                    "y_shift_without_padding":points[0]['y'] - ((size-h) // 2) - padding_size,
                    "elem_selected":elem_selected,
                    "is_check":polygon_label.labeling_content,
                    "image_user_conf_id":image_user_conf_id,
                    "ai_ocr": ai_ocr
                }
                return render(request, 'ocr_content_labeling.html', context)
        except Exception as e:
            print(e)
            return render(request, 'ocr_content_labeling.html',None)

    @method_decorator(check_login)
    def nextframe(self, request):
        """
        :param request:
        :return:
        """
        try:
            body=None
            docid = request.GET.get('docid')
            doc = OcrPDF.objects.get(id=docid)
            if doc.create_user_id == str(request.user):
                current_frame = doc.current_frame
                framenum = doc.frame_num
            else:
                assist = doc.ocrassist_set.get(assist_user_name=str(request.user))
                current_frame = assist.current_frame
                framenum = assist.ocrPDF.frame_num
            body={
                "current_frame": current_frame,
                "framenum": framenum,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "获取帧号成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def get_roughthr(self, request):
        """
        :param request:
        :return:
        """
        try:
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('currentframe'))
            doc = OcrPDF.objects.get(id=docid)
            if doc.create_user_id == str(request.user):
                is_vertical_pdf = doc.is_vertical
            else:
                assist = doc.ocrassist_set.get(assist_user_name=str(request.user))
                is_vertical_pdf = assist.is_vertical
            ocrimage = doc.pdfimage_set.get(frame_id=currentframe)
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0, "is_vertical":is_vertical_pdf, "entropy_thr":0.9, "projection_thr_strict":0.6,"projection_thr_easing":0.1})
            body={
                "projection_thr_strict":image_user_conf.projection_thr_strict,
                "projection_thr_easing":image_user_conf.projection_thr_easing,
                "entropy_thr":image_user_conf.entropy_thr,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "获取粗标注信息成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def set_roughthr_easing(self, request):
        """
        :param request:
        :return:
        """
        try:
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('currentframe'))
            projection_thr_easing = float(request.GET.get('projection_thr_easing'))
            doc = OcrPDF.objects.get(id=docid)
            if doc.create_user_id == str(request.user):
                is_vertical_pdf = doc.is_vertical
            else:
                assist = doc.ocrassist_set.get(assist_user_name=str(request.user))
                is_vertical_pdf = assist.is_vertical
            ocrimage = doc.pdfimage_set.get(frame_id=currentframe)
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0, "is_vertical":is_vertical_pdf, "entropy_thr":0.9, "projection_thr_strict":0.6,"projection_thr_easing":0.1})
            image_user_conf.projection_thr_easing=projection_thr_easing
            image_user_conf.save()
            body={
                "projection_thr_easing":image_user_conf.projection_thr_easing,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "设置粗标注阈值easing成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def set_roughthr_strict(self, request):
        """
        :param request:
        :return:
        """
        try:
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('currentframe'))
            projection_thr_strict = float(request.GET.get('projection_thr_strict'))
            doc = OcrPDF.objects.get(id=docid)
            if doc.create_user_id == str(request.user):
                is_vertical_pdf = doc.is_vertical
            else:
                assist = doc.ocrassist_set.get(assist_user_name=str(request.user))
                is_vertical_pdf = assist.is_vertical
            ocrimage = doc.pdfimage_set.get(frame_id=currentframe)
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0, "is_vertical":is_vertical_pdf, "entropy_thr":0.9, "projection_thr_strict":0.6,"projection_thr_easing":0.1})
            image_user_conf.projection_thr_strict=projection_thr_strict
            image_user_conf.save()
            body={
                "projection_thr_strict":image_user_conf.projection_thr_strict,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "设置粗标注阈值strict成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def set_roughthr_entropy(self, request):
        """
        :param request:
        :return:
        """
        try:
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('currentframe'))
            entropy_thr = float(request.GET.get('entropy_thr'))
            doc = OcrPDF.objects.get(id=docid)
            if doc.create_user_id == str(request.user):
                is_vertical_pdf = doc.is_vertical
            else:
                assist = doc.ocrassist_set.get(assist_user_name=str(request.user))
                is_vertical_pdf = assist.is_vertical
            ocrimage = doc.pdfimage_set.get(frame_id=currentframe)
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0, "is_vertical":is_vertical_pdf, "entropy_thr":0.9, "projection_thr_strict":0.6,"projection_thr_easing":0.1})
            image_user_conf.entropy_thr = entropy_thr
            image_user_conf.save()
            body={
                "entropy_thr" : image_user_conf.entropy_thr,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "设置粗标注阈值entropy成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(check_login)
    def get_imageinfo(self, request):
        """
        :param request:
        :return:
        """
        try:
            docid = request.GET.get('docid')
            currentframe = int(request.GET.get('currentframe'))
            doc = OcrPDF.objects.get(id=docid)
            ocrimage = doc.pdfimage_set.get(frame_id=currentframe)
            polygon_set = ocrimage.ocrlabelingpolygon_set.all()
            create_user_id_set = polygon_set.values("create_user_id").distinct()  # achieve distinct create_user_id
            if doc.create_user_id == str(request.user):
                is_vertical_pdf = doc.is_vertical
            else:
                assist = doc.ocrassist_set.get(assist_user_name=str(request.user))
                is_vertical_pdf = assist.is_vertical
            # build a dictionary with create_user_id as its key and polygon list as its value
            polygon_dict = dict()
            for create_user_id in create_user_id_set:
                polygon_dict[create_user_id["create_user_id"]] = dict()  # initialized as an empty list
            for polygon in polygon_set:
                polygon_dict[polygon.create_user_id][polygon.id]= {
                    "polygon_id":polygon.id,
                    "image_id":polygon.pdfImage.id,
                    "create_user_id":polygon.create_user_id,  # redundant data for a verification
                    "points":str(polygon.polygon,'utf-8'),
                    "labeling_content":polygon.labeling_content
                }
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0, "is_vertical":is_vertical_pdf, "entropy_thr":0.9, "projection_thr_strict":0.6,"projection_thr_easing":0.1})
            body={
                "ori_width":ocrimage.width,
                "image_id":ocrimage.id,
                "ori_height":ocrimage.height,
                "polygon_dict":json.dumps(polygon_dict),
                "current_rotate":image_user_conf.rotate_degree,
                "is_vertical":image_user_conf.is_vertical,
                "center_x":image_user_conf.center_x,
                "center_y":image_user_conf.center_y,
                "zoom_scale":image_user_conf.zoom_scale,
                "username":str(request.user),
            }
            result = {"status":"success" , "username":str(request.user), "tip": "获取image信息成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    @method_decorator(login_required)
    def get_image(self, request):
        try:
            ocrimage=PDFImage.objects.get(id=request.GET['image_id'])
            tar_width = int(request.GET.get('tar_width'))
            tar_height = int(request.GET.get('tar_height'))
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0})
            image_rotated = OcrView.achieveImageRotated(str(request.user), ocrimage, image_user_conf.rotate_degree, width=tar_width, height=tar_height)
            print(image_rotated.shape)
            img_encode = cv.imencode('.jpg', image_rotated)  # 可以看出第二个元素是矩阵 print(img_encode)
            data_encode = np.array(img_encode[1])
            str_encode = data_encode.tostring()
            data_byte = BytesIO(str_encode).getvalue()
            return HttpResponse(data_byte, 'image/jpeg')

        except Exception as e:
            traceback.print_exc()
            return None

    @method_decorator(login_required)
    def labeling(self, request):
        try:
            ocrpdf_id = request.GET.get('id')  # ocrpdf_id
            ocrpdf = OcrPDF.objects.get(id=ocrpdf_id)
            current_frame = 0
            is_vertical_pdf = False

            if ocrpdf.create_user_id == str(request.user):
                current_frame = ocrpdf.current_frame
                is_vertical_pdf = ocrpdf.is_vertical
            else:
                assist = ocrpdf.ocrassist_set.get(assist_user_name=str(request.user))
                current_frame = assist.current_frame
                is_vertical_pdf = assist.is_vertical

            ocrimage = ocrpdf.pdfimage_set.get(frame_id=current_frame)
            polygon_set = ocrimage.ocrlabelingpolygon_set.all()
            create_user_id_set = polygon_set.values("create_user_id").distinct()  # achieve distinct create_user_id
            # build a dictionary with create_user_id as its key and polygon list as its value
            polygon_dict = dict()
            for create_user_id in create_user_id_set:
                polygon_dict[create_user_id["create_user_id"]] = list()  # initialized as an empty list

            for polygon in polygon_set:
                polygon_dict[polygon.create_user_id].append(
                    {
                        "image_id":ocrimage.id,
                        "polygon_id":polygon.id,
                        "image_id":polygon.pdfImage.id,
                        "create_user_id":polygon.create_user_id,  # redundant data for a verification
                        "points":str(polygon.polygon,'utf-8'),
                        "labeling_content":polygon.labeling_content
                    }
                )
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0, "is_vertical":is_vertical_pdf, "entropy_thr":0.9, "projection_thr_strict":0.6,"projection_thr_easing":0.1})
            context={
                "image_id":ocrimage.id,
                "title":ocrpdf.title,
                "ocr_pdf_id":ocrpdf.id,
                "frame_id":ocrimage.frame_id,
                "frame_num":ocrpdf.frame_num,
                "ori_width":ocrimage.width,
                "ori_height":ocrimage.height,
                "polygon_dict":json.dumps(polygon_dict),
                "current_rotate":image_user_conf.rotate_degree,
                "is_vertical":json.dumps(image_user_conf.is_vertical),
                "entropy_thr":image_user_conf.entropy_thr,
                "projection_thr_strict":image_user_conf.projection_thr_strict,
                "projection_thr_easing":image_user_conf.projection_thr_easing,
                "center_x":image_user_conf.center_x,
                "center_y":image_user_conf.center_y,
                "zoom_scale":image_user_conf.zoom_scale,
                "image_user_conf_id":image_user_conf.id,
                "filter_size":image_user_conf.filter_size
            }
            return render(request, 'ocr_labeling.html', context)
        except Exception as e:
            print("ocr_labeling:"+str(e))
            return render(request, 'ocr_labeling.html', None)

    @method_decorator(login_required)
    def ocr_get_image(self, request):
        try:
            ocrimage=PDFImage.objects.get(id=request.GET['frame_id'])
            tar_width = int(request.GET.get('tar_width'))
            tar_height = int(request.GET.get('tar_height'))
            pil_image = Image.open(ocrimage.data_byte)
            width, height = pil_image.size
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0})
            if abs(image_user_conf.rotate_degree)>0.0001:
                image_rotated = pil_image.rotate(image_user_conf.rotate_degree)
            else:
                image_rotated = pil_image
            image_resized = image_rotated.resize((tar_width, tar_height), Image.ANTIALIAS)
            trans_width,trans_height=image_resized.size
            new_imageIO = BytesIO()
            image_resized.save(new_imageIO,"JPEG")
            data_byte=new_imageIO.getvalue()
            return HttpResponse(data_byte, 'image/jpeg')

        except Exception as e:
            print(e)
            return None

    @method_decorator(login_required)
    def get_polygon_image(self, request):
        try:
            polygon_id = request.GET.get("polygon_id")
            image_id = request.GET.get("image_id")
            tar_width = int(request.GET.get("tar_width"))
            tar_height = int(request.GET.get("tar_height"))
            is_extend = str(request.GET.get("is_extend"))
            ocrimage = PDFImage.objects.get(id=image_id)
            polygon_item = OcrLabelingPolygon.objects.get(id=polygon_id)
            points = json.loads(str(polygon_item.polygon, 'utf-8'))
            padding_size = 128
            image_width = ocrimage.width
            image_height = ocrimage.height
            # 需要旋转的角度
            degree_to_rotate = cal_rotate_angle(points[0]['x'], points[0]['y'], points[3]['x'], points[3]['y'])
            # 旋转后的points
            rotate_points(points, degree_to_rotate, image_width, image_height)
            # 确保旋转后是矩形的外接操作
            bounding_points(points)
            for point in points:
                point['x'] = round(point['x']) + padding_size
                point['y'] = round(point['y']) + padding_size
            # 求取偏移
            w = abs(points[1]['x']-points[0]['x'])
            h = abs(points[3]['y']-points[0]['y'])
            if is_extend == "true":
                size = max(h, w)
                size = max(size*2, 9)
                relative_l = points[0]['x']-((size-w) // 2)
                relative_t = points[0]['y']-((size-h) // 2)
                relative_r = int(relative_l + size -1)
                relative_b = int(relative_t + size -1)
                # padding image中的box位置
                relative_box = (relative_l, relative_t, relative_r, relative_b)
            else:
                relative_box = (points[0]['x'], points[0]['y'], points[2]['x'], points[2]['y'])
                ratio_w = w*1.0/tar_width
                ratio_h = h*1.0/tar_height
                ratio = max(ratio_w, ratio_h) 
                tar_width = int(w // ratio)
                tar_height = int(h // ratio)
            # 获取旋转过的padding图像
            rotate_image_key = "%s_%s_%.2f_%d" % (str(request.user), image_id, degree_to_rotate, padding_size)
            image_rotate_padding = cache.get(rotate_image_key)
            if image_rotate_padding is None:
                #读取原始图像
                pil_image = Image.open(ocrimage.data_byte)
                width, height = pil_image.size
                if abs(degree_to_rotate)>0.000001:
                    image_rotate_padding = pil_image.rotate(degree_to_rotate)
                else:
                    image_rotate_padding = pil_image
                w_l_extend = padding_size
                w_r_extend = padding_size
                h_t_extend = padding_size
                h_b_extend = padding_size
                # expend
                image_rotate_padding = ImageOps.expand(image_rotate_padding, border=(w_l_extend, h_t_extend, w_r_extend, h_b_extend) ,fill=0)
                cache.set(rotate_image_key, pickle.dumps(image_rotate_padding), nx=True) 
                cache.expire(rotate_image_key, 3600)
            else:
                image_rotate_padding = pickle.loads(image_rotate_padding)
            image_crop = image_rotate_padding.crop(relative_box)
            image_map = image_crop.resize((tar_width, tar_height), Image.ANTIALIAS)

            # 最终文件流
            mapIO = BytesIO()
            image_map.save(mapIO, "JPEG")
            map_bytes = mapIO.getvalue()
            return HttpResponse(map_bytes, 'image/jpeg')

        except Exception as e:
            print(e)
            return None


    @method_decorator(login_required)
    def get_elem_selected(self, request):
        try:
            elem_selected_str=request.GET.get("elem_selected_str")
            elem_selected=json.loads(elem_selected_str)
            width=int(request.GET.get("width"))
            size = 64
            image = Image.new("RGB", (width, size), "#FFFFFF")

            index = 0
            for elem_id in elem_selected:
                col_index = index * size
                # 获取elem图片
                elem_image_key = "elem_%d_%d_%d" % (elem_id, size, size)
                image_elem = cache.get(elem_image_key)
                if image_elem is None:
                    #读取原始图像
                    elem = ChineseElem.objects.get(id=elem_id)
                    image_stream = io.BytesIO(elem.image_bytes)
                    pil_image = Image.open(image_stream)
                    width, height = pil_image.size
                    ratio_w =width*1.0/size
                    ratio_h =height*1.0/size
                    ratio = max(ratio_w, ratio_h)
                    tar_width = int(width/ratio)
                    tar_height = int(height/ratio)
                    image_elem = pil_image.resize((tar_width, tar_height), Image.ANTIALIAS)
                    cache.set(elem_image_key, pickle.dumps(image_elem), nx=True) 
                    cache.expire(elem_image_key, 3600)
                else:
                    image_elem = pickle.loads(image_elem)
                # 粘贴
                (w, h) = image_elem.size
                x_init=col_index
                y_init=0
                x_shift=0
                y_shift=0
                if w<h:
                    x_shift=(size-w) // 2
                else:
                    y_shift=(size-h) // 2
                image.paste(image_elem, (x_init+x_shift, y_init+y_shift))
                index += 1

            mapIO = BytesIO()
            image.save(mapIO, "JPEG")
            map_bytes = mapIO.getvalue()
            return HttpResponse(map_bytes, 'image/jpeg')

        except Exception as e:
            print(e)
            return None


    @method_decorator(check_login)
    def get_elemset(self, request):
        """
        :param request:
        :return:
        """
        try:
            elemset = ChineseElem.objects.filter(create_user_id=str(request.user))
            elemids=[]
            for elem in elemset:
                elemids.append(elem.id)
            body={
                "elemset":elemids,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "获取elemset成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)

    @method_decorator(login_required)
    def get_elem_page(self, request):
        try:
            size = 64
            page_index = int(request.GET.get("page_index"))
            row = int(request.GET.get("row"))
            col = int(request.GET.get("col"))
            elem_per_page = row*col
            w = col * size
            h = row * size
            image = Image.new("RGB", (w, h), "#FFFFFF")
            elem_set = ChineseElem.objects.filter(create_user_id=str(request.user))
            elem_count = elem_set.count()
            init_index = page_index * elem_per_page
            elem_num_of_this_page = min(elem_count-init_index, elem_per_page)
            clip_set = elem_set[init_index:(init_index+elem_num_of_this_page)]
            index = 0
            for elem in clip_set:
                row_index = index // col
                col_index = index % col
                # 获取elem图片
                elem_image_key = "elem_%d_%d_%d" % (elem.id, size, size)
                image_elem = cache.get(elem_image_key)
                if image_elem is None:
                    #读取原始图像
                    image_stream = io.BytesIO(elem.image_bytes)
                    pil_image = Image.open(image_stream)
                    width, height = pil_image.size
                    ratio_w =width*1.0/size
                    ratio_h =height*1.0/size
                    ratio = max(ratio_w, ratio_h)
                    tar_width = int(width/ratio)
                    tar_height = int(height/ratio)
                    image_elem = pil_image.resize((tar_width, tar_height), Image.ANTIALIAS)
                    cache.set(elem_image_key, pickle.dumps(image_elem), nx=True) 
                    cache.expire(elem_image_key, 3600)
                else:
                    image_elem = pickle.loads(image_elem)
                # 粘贴
                (w, h) = image_elem.size
                x_init=col_index*size
                y_init=row_index*size
                x_shift=0
                y_shift=0
                if w<h:
                    x_shift=(size-w) // 2
                else:
                    y_shift=(size-h) // 2
                image.paste(image_elem, (x_init+x_shift, y_init+y_shift))
                index += 1


            # 最终文件流
            mapIO = BytesIO()
            image.save(mapIO, "JPEG")
            map_bytes = mapIO.getvalue()
            return HttpResponse(map_bytes, 'image/jpeg')
        except Exception as e:
            print(e)
            return None


    @method_decorator(login_required)
    def achieve_elem_id(self, request):
        try:
            size = 64
            page_index = int(request.GET.get("page_index"))
            row = int(request.GET.get("row"))
            col = int(request.GET.get("col"))
            elem_per_page = row*col
            elem_set = ChineseElem.objects.filter(create_user_id=str(request.user))
            elem_count = elem_set.count()
            init_index = page_index * elem_per_page
            elem_num_of_this_page = min(elem_count-init_index, elem_per_page)
            clip_set = elem_set[init_index:(init_index+elem_num_of_this_page)]
            index = 0
            id_set = []
            for elem in clip_set:
                row_index = index // col
                col_index = index % col
                id_set.append({"id": elem.id, "height":elem.height, "width":elem.width})
                index += 1

            return HttpResponse(json.dumps(id_set))
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @method_decorator(login_required)
    def get_elem_image(self, request):
        try:
            image_id = request.GET.get("image_id")
            ocrimage = PDFImage.objects.get(id=image_id)
            degree_to_rotate = float(request.GET.get("degree_to_rotate"))
            tar_width = int(request.GET.get("tar_width"))
            tar_height = int(request.GET.get("tar_height"))
            relative_box_str = str(request.GET.get("elem_box"))
            relative_box = json.loads(relative_box_str)
            relative_box = (relative_box[0], relative_box[1], relative_box[2], relative_box[3])
            padding_size = 128
            w = relative_box[2]-relative_box[0]
            h = relative_box[3]-relative_box[1]
            ratio_w = w*1.0/tar_width
            ratio_h = h*1.0/tar_height
            ratio = max(ratio_w, ratio_h) 
            tar_width = int(w // ratio)
            tar_height = int(h // ratio)
            # 获取旋转过的padding图像
            rotate_image_key = "%s_%s_%.2f_%d" % (str(request.user), image_id, degree_to_rotate, padding_size)
            image_rotate_padding = cache.get(rotate_image_key)
            if image_rotate_padding is None:
                #读取原始图像
                pil_image = Image.open(ocrimage.data_byte)
                width, height = pil_image.size
                if abs(degree_to_rotate)>0.000001:
                    image_rotate_padding = pil_image.rotate(degree_to_rotate)
                else:
                    image_rotate_padding = pil_image
                w_l_extend = padding_size
                w_r_extend = padding_size
                h_t_extend = padding_size
                h_b_extend = padding_size
                # expend
                image_rotate_padding = ImageOps.expand(image_rotate_padding, border=(w_l_extend, h_t_extend, w_r_extend, h_b_extend) ,fill=0)
                cache.set(rotate_image_key, pickle.dumps(image_rotate_padding), nx=True) 
                cache.expire(rotate_image_key, 3600)
            else:
                image_rotate_padding = pickle.loads(image_rotate_padding)
            image_crop = image_rotate_padding.crop(relative_box)
            image_map = image_crop.resize((tar_width, tar_height), Image.ANTIALIAS)

            # 最终文件流
            mapIO = BytesIO()
            image_map.save(mapIO, "JPEG")
            map_bytes = mapIO.getvalue()
            
            return HttpResponse(map_bytes, 'image/jpeg')

        except Exception as e:
            print(e)
            return None


    @method_decorator(login_required)
    def get_character_image(self, request):
        try:
            elem_id = request.GET.get("elem_id")
            tar_width = int(request.GET.get("tar_width"))
            tar_height = int(request.GET.get("tar_height"))
            elem = ChineseElem.objects.get(id=elem_id)
            # 获取elem图片
            elem_image_key = "elem_%d_%d_%d" % (int(elem_id),tar_width,tar_height)
            image_elem = cache.get(elem_image_key)
            if image_elem is None:
                #读取原始图像
                image_stream = io.BytesIO(elem.image_bytes)
                pil_image = Image.open(image_stream)
                (w, h) = pil_image.size
                ratio_w =w*1.0/tar_width
                ratio_h =h*1.0/tar_height
                ratio = max(ratio_w, ratio_h)
                tar_width = int(w/ratio)
                tar_height = int(h/ratio)
                image_elem = pil_image.resize((tar_width, tar_height), Image.ANTIALIAS)
                cache.set(elem_image_key, pickle.dumps(image_elem), nx=True) 
                cache.expire(elem_image_key, 3600)
            else:
                image_elem = pickle.loads(image_elem)
        
            # 最终文件流
            mapIO = BytesIO()
            image_elem.save(mapIO, "JPEG")
            map_bytes = mapIO.getvalue()
            return HttpResponse(map_bytes, 'image/jpeg')
        except Exception as e:
            print(e)
            return None

    @method_decorator(login_required)
    def add_character(self, request):
        try:
            elem_id = request.GET.get("elem_id")
            desc = request.GET.get("desc")
            elem = ChineseElem.objects.get(id=elem_id)
            character_add = ""
            for character in desc:
                if character!= " ":
                    try:
                        CharacterElem(elem=elem, character=character, create_user_id=str(request.user)).save()
                        character_add+=character
                    except Exception as e:
                        pass
            return HttpResponse(character_add)
            
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @method_decorator(login_required)
    def character_assist_check(self, request):
        try:
            characters = request.GET.get("character")
            elem_list = []
            for character in characters:
                if character!= " ":
                    try:
                        characterelem_set = CharacterElem.objects.filter(create_user_id = str(request.user), character=character)
                        if characterelem_set.count() >0:
                            for characterelem in characterelem_set:
                                elem_list.append(characterelem.elem.id)
                    except Exception as e:
                        print(e)

            return HttpResponse(json.dumps(elem_list))

        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(login_required)
    def delete_character(self, request):
        try:
            elem_id = request.GET.get("elem_id")
            desc = request.GET.get("desc")
            elem = ChineseElem.objects.get(id=elem_id)
            character_add = ""

            for character in desc:
                if character!= " ":
                    try:
                        elem.characterelem_set.get(character=character).delete()
                        character_add+=character
                    except Exception as e:
                        return HttpResponse("err")
            return HttpResponse(character_add)
            
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(login_required)
    def achieve_characters_from_elem(self, request):
        try:
            character_str = ""
            elem_id = request.GET.get("elem_id")
            elem = ChineseElem.objects.get(id=elem_id)
            characterset = elem.characterelem_set.all()
            for character_elem in characterset:
                character_str += character_elem.character
            return HttpResponse(character_str)
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(login_required)
    def get_elem_number(self, request):
        try:
            elem_set = ChineseElem.objects.filter(create_user_id=str(request.user))
            return HttpResponse(elem_set.count())
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(login_required)
    def update_polygon_id_thr_prior(self, request):
        try:
            image_user_conf_id = request.GET.get("image_user_conf_id")
            image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)
            polygon_id = request.GET.get("polygon_id")
            image = image_user_conf.image
            id_max = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user), id__lt=polygon_id).aggregate(Max('id'))
            print(type(id_max))
            print(id_max)
            if(id_max['id__max'] is None):
                return HttpResponse("已经是最前边的标注")
            else:
                image_user_conf.polygon_id_thr=id_max['id__max']-1
                image_user_conf.save()
                return HttpResponse("ok");
        except Exception as e:
            print(e)
            return HttpResponse(str(e))


    @method_decorator(login_required)
    def update_polygon_id_thr_next(self, request):
        try:
            image_user_conf_id = request.GET.get("image_user_conf_id")
            polygon_id = request.GET.get("polygon_id")
            image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)
            image = image_user_conf.image
            id_set_num = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user), id__gt=polygon_id).count()
            if id_set_num<1:
                return HttpResponse("已经是最后一个标注")
            else:
                image_user_conf.polygon_id_thr=polygon_id
                image_user_conf.save()
                return HttpResponse("ok");
        except Exception as e:
            print(e)
            return HttpResponse(str(e))


    @method_decorator(login_required)
    def elem_selected_add(self, request):
        try:
            elem_id = request.GET.get("elem_id")
            polygon_id = request.GET.get("polygon_id")
            polygon = OcrLabelingPolygon.objects.get(id=polygon_id)
            elem = ChineseElem.objects.get(id=elem_id)
            PolygonElem(polygon=polygon, elem=elem, create_user_id=str(request.user), desc_info="created_auto").save()
            return HttpResponse("ok")
        except Exception as e:
            return HttpResponse(str(e))


    @method_decorator(login_required)
    def elem_selected_delete(self, request):
        try:
            elem_id = request.GET.get("elem_id")
            polygon_id = request.GET.get("polygon_id")
            polygon = OcrLabelingPolygon.objects.get(id=polygon_id)
            elem = ChineseElem.objects.get(id=elem_id)
            PolygonElem.objects.get(polygon=polygon,elem=elem).delete()

            return HttpResponse("ok")
        except Exception as e:
            return HttpResponse(str(e))


    @method_decorator(login_required)
    def add_elem(self, request):
        try:
            image_id = request.GET.get("image_id")
            ocrimage = PDFImage.objects.get(id=image_id)
            degree_to_rotate = float(request.GET.get("degree_to_rotate"))
            relative_box_str = str(request.GET.get("elem_box"))
            desc = str(request.GET.get("desc"))
            relative_box = json.loads(relative_box_str)
            relative_box = (relative_box[0], relative_box[1], relative_box[2], relative_box[3])
            padding_size = 128
            w = relative_box[2]-relative_box[0]
            h = relative_box[3]-relative_box[1]
            # 获取旋转过的padding图像
            rotate_image_key = "%s_%s_%.2f_%d" % (str(request.user), image_id, degree_to_rotate, padding_size)
            image_rotate_padding = cache.get(rotate_image_key)
            if image_rotate_padding is None:
                #读取原始图像
                pil_image = Image.open(ocrimage.data_byte)
                width, height = pil_image.size
                if abs(degree_to_rotate)>0.000001:
                    image_rotate_padding = pil_image.rotate(degree_to_rotate)
                else:
                    image_rotate_padding = pil_image
                w_l_extend = padding_size
                w_r_extend = padding_size
                h_t_extend = padding_size
                h_b_extend = padding_size
                # expend
                image_rotate_padding = ImageOps.expand(image_rotate_padding, border=(w_l_extend, h_t_extend, w_r_extend, h_b_extend) ,fill=0)
                cache.set(rotate_image_key, pickle.dumps(image_rotate_padding), nx=True) 
                cache.expire(rotate_image_key, 3600)
            else:
                image_rotate_padding = pickle.loads(image_rotate_padding)
            image_crop = image_rotate_padding.crop(relative_box)

            # 最终文件流
            mapIO = BytesIO()
            image_crop.save(mapIO, "png")
            map_bytes = mapIO.getvalue()
            # 创建elem
            (w, h) = image_crop.size
            elem = ChineseElem(image_bytes=map_bytes, width=w, height=h, desc_info=desc, create_user_id=str(request.user))
            elem.save()
            context = {'id':elem.id}
            return HttpResponse(json.dumps(context))

        except Exception as e:
            return HttpResponse("err")

    # 设置文字方向
    @method_decorator(login_required)
    def direction_select(self, request):
        try:
            direction = request.GET.get("direction")
            image_user_conf_id = request.GET.get("image_user_conf_id")
            image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)  # 被标注的图片
            if direction == "vertical":
                image_user_conf.is_vertical = True
            else:
                image_user_conf.is_vertical = False
            image_user_conf.save()
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")



    # 更改标注偏旁完成状态
    @method_decorator(login_required)
    def change_check_status(self, request):
        try:
            polygon_id = request.GET.get("polygon_id")
            polygon = OcrLabelingPolygon.objects.get(id=polygon_id)
            if polygon.create_user_id == str(request.user):
                if polygon.labeling_content is False:
                    polygon.labeling_content = True
                    polygon.save()
                    return HttpResponse("true")

                if polygon.labeling_content is True:
                    polygon.labeling_content = False
                    polygon.save()
                    return HttpResponse("false")
            else:
                return HttpResponse("err")
        except Exception as e:
            print(e)
            return HttpResponse("err")


    # 设置filter_size
    @method_decorator(login_required)
    def set_filter_size(self, request):
        try:
            filter_size = int(request.GET.get("filter_size"))
            image_user_conf_id = request.GET.get("image_user_conf_id")
            if filter_size>=0 and filter_size<10240:
                image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)  # 被标注的图片
                image_user_conf.filter_size = filter_size
                image_user_conf.save()
                return HttpResponse("ok")
            else:
                return HttpResponse("err")
        except Exception as e:
            print(e)
            return HttpResponse("err")
            

    # 设置entropy_thr
    @method_decorator(login_required)
    def set_entropy_thr(self, request):
        try:
            entropy_thr = float(request.GET.get("entropy_thr"))
            image_user_conf_id = request.GET.get("image_user_conf_id")
            if entropy_thr<1:
                image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)  # 被标注的图片
                image_user_conf.entropy_thr = entropy_thr
                image_user_conf.save()
                return HttpResponse("ok")
            else:
                return HttpResponse("err")
        except Exception as e:
            print(e)
            return HttpResponse("err")


    # 设置锚点
    @method_decorator(login_required)
    def save_anchor(self, request):
        try:
            center_x = float(request.GET.get("center_x"))
            center_y = float(request.GET.get("center_y"))
            zoom_scale = float(request.GET.get("zoom_scale"))
            image_user_conf_id = request.GET.get("image_user_conf_id")
            image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)  # 被标注的图片
            image_user_conf.center_x = center_x
            image_user_conf.center_y = center_y
            image_user_conf.zoom_scale = zoom_scale
            image_user_conf.save()
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(login_required)
    def ocr_move_page(self, request):
        try:
            page_apointed = int(request.GET.get("page_apointed"))
            ocr_pdf_id = int(request.GET.get("ocr_pdf"))
            ocr_pdf=OcrPDF.objects.get(id=ocr_pdf_id)
            if str(request.user) == ocr_pdf.create_user_id:
                ocr_pdf.current_frame = page_apointed
                ocr_pdf.save()
            else:
                ocr_assist = ocr_pdf.ocrassist_set.get(assist_user_name=str(request.user))
                ocr_assist.current_frame = page_apointed
                ocr_assist.save()

            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")

    # 设置当前帧
    @method_decorator(check_login)
    def set_current(self, request):
        """
        :param request:
        :return:
        """
        try:
            body=None
            page_apointed = int(request.GET.get("page_apointed"))
            ocr_pdf_id = int(request.GET.get("ocr_pdf"))
            ocr_pdf=OcrPDF.objects.get(id=ocr_pdf_id)
            if str(request.user) == ocr_pdf.create_user_id:
                ocr_pdf.current_frame = page_apointed
                ocr_pdf.save()
            else:
                ocr_assist = ocr_pdf.ocrassist_set.get(assist_user_name=str(request.user))
                ocr_assist.current_frame = page_apointed
                ocr_assist.save()
            result = {"status":"success" , "username":str(request.user), "tip": "设置当前页成功", "body":body}
            return JsonResponse(result)
        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    # PDF设置文字方向
    @method_decorator(login_required)
    def direction_pdf(self, request):
        try:
            is_vertical = request.GET.get("is_vertical")
            ocr_pdf_id = request.GET.get("ocr_pdf_id")
            ocr_pdf = OcrPDF.objects.get(id=ocr_pdf_id)
            if ocr_pdf.create_user_id != str(request.user):
                conf = ocr_pdf.ocrassist_set.get(assist_user_name=str(request.user))
                if is_vertical == "true":
                    conf.is_vertical = True
                else:
                    conf.is_vertical = False
                conf.save()
            else:
                if is_vertical == "true":
                    ocr_pdf.is_vertical = True
                else:
                    ocr_pdf.is_vertical = False
                ocr_pdf.save()
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @method_decorator(login_required)
    def rotate_degree_evaluate(self, request):
        try:
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            pil_image = Image.open(image.data_byte)
            gray_image = pil_image.convert('L')
            width, height = gray_image.size
            gray_mean = (1-np.asarray(gray_image)/255.0).mean()
            background_modification = max(0,0.16-gray_mean)
            is_vertical = image.imageuserconf_set.get(create_user_id=str(request.user)).is_vertical

            project_entropy_list = list()
            for rotate_degree in range(-50,50,5):
                rotate_degree_true = rotate_degree/10.0
                image_rotated = gray_image.rotate(rotate_degree_true)
                rotate_rad = 5/180.0*math.pi
                d_w = 0.5*height*abs(math.tan(rotate_rad))
                d_h = 0.5*width*abs(math.tan(rotate_rad))
                box = (d_w, d_h, width-d_w, height-d_h)
                region_select = image_rotated.crop(box)
                width_crop, height_crop = region_select.size
                array_image = 1-np.asarray(region_select)/255.0 + background_modification
                # get projection
                if is_vertical is True:
                    projection = array_image.sum(axis=0)
                else:
                    projection = array_image.sum(axis=1)
                # get entropy
                probability = projection/projection.sum()
                entropy_src = -probability*np.log(probability)
                entropy = entropy_src.sum()
                project_entropy_list.append(entropy)
            evaluate_info={
                "projection_entropy":project_entropy_list,
                "slope":0.5,
                "bias":-5.0,
            }
            return HttpResponse(json.dumps(evaluate_info, cls=NpEncoder))
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @staticmethod
    def rotate_points(points, rotate_degree, w, h):
        for point in points:
            x = point['x']
            y = point['y']
            x_shift = x - w/2.0
            y_shift = y - h/2.0
            rotate_rad = rotate_degree/180.0*math.pi
            nx = x_shift*math.cos(rotate_rad)+y_shift*math.sin(rotate_rad)+w/2.0
            ny = -x_shift*math.sin(rotate_rad)+y_shift*math.cos(rotate_rad)+h/2.0
            point['x']=nx
            point['y']=ny

    # rotate degree reset
    @method_decorator(login_required)
    def rotate_degree_reset(self, request):
        try:
            image_id = request.GET.get("image_id")
            rotate_degree = request.GET.get("rotate_degree")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            image_user_conf, isCreate = image.imageuserconf_set.get_or_create(create_user_id=str(request.user), defaults={"rotate_degree":rotate_degree})
            if isCreate==False:
                image_user_conf.rotate_degree=rotate_degree
                image_user_conf.save()
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(check_login)
    def add_labeling_polygon(self, request):
        """
        :param request:
        :return:
        """
        try:
            pointsStr = request.GET.get("points")
            points_rotate = json.loads(pointsStr.encode("utf-8"))
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            delete_info = dict()
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user
            rect_region = OcrView.get_rect_info(points_rotate[0], points_rotate[2])
            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info[polygon.id]={'polygon_id':polygon.id, 'rect_info':rect_candidate}
                    polygon.delete()
            polygon = OcrLabelingPolygon(pdfImage=image, polygon=pointsStr.encode("utf-8"), create_user_id=str(request.user))
            polygon.save()
            polygonAdd = {
                "polygon_id":polygon.id,
                "image_id":polygon.pdfImage.id,
                "create_user_id":polygon.create_user_id,  # redundant data for a verification
                "points":str(polygon.polygon,'utf-8'),
                "labeling_content":polygon.labeling_content
            }

            body={
                "polygonAdd":polygonAdd,
                "delete_info":delete_info,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "添加标注成功", "body":body}
            print(result)
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)

    @method_decorator(login_required)
    def add_labeling_polygon_old(self, request):
        try:
            pointsStr = request.GET.get("points")
            points_rotate = json.loads(pointsStr.encode("utf-8"))
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            delete_info = []
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user
            rect_region = OcrView.get_rect_info(points_rotate[0], points_rotate[2])
            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info.append({'polygon_id':polygon.id, 'rect_info':rect_candidate})
                    polygon.delete()

            polygon = OcrLabelingPolygon(pdfImage=image, polygon=pointsStr.encode("utf-8"), create_user_id=str(request.user))
            polygon.save()
            polygon_id = polygon.id
            polygon_create_user_id = polygon.create_user_id
            context = {"polygon_id":polygon_id,"polygon_create_user_id":polygon_create_user_id, "delete_info":delete_info}
            return HttpResponse(json.dumps(context))
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @staticmethod
    def get_rect_info(point_a, point_b):
        try:
             
             x = min(point_a['x'], point_b['x'])
             x_ = max(point_a['x'], point_b['x'])
             y = min(point_a['y'], point_b['y'])
             y_ = max(point_a['y'], point_b['y'])
             x = round(x)
             y = round(y)
             x_ = round(x_)
             y_ = round(y_)
             w = abs(x_-x)
             h = abs(y_-y)
             area = w*h
             return {'x':x, 'y':y, 'x_':x_, 'y_':y_, 'w':w, 'h':h, 'area':area}
        except Exception as e:
            print(e)

    # caculate intersection ratio
    @staticmethod
    def cal_intersection_ratio(rect_a, rect_b):
        try:
            dist_x = max(rect_a['x_'], rect_b['x_']) - min(rect_a['x'], rect_b['x'])
            dist_y = max(rect_a['y_'], rect_b['y_']) - min(rect_a['y'], rect_b['y'])
            w_intersection = max(rect_a['w']+rect_b['w']-dist_x , 0)
            h_intersection = max(rect_a['h']+rect_b['h']-dist_y , 0)
            area_intersection = w_intersection * h_intersection
            intersection_ratio_a = area_intersection / (rect_a['area']*1.0)
            intersection_ratio_b = area_intersection / (rect_b['area']*1.0)
            return {'ratio_a':intersection_ratio_a, 'ratio_b':intersection_ratio_b, 'area':area_intersection}
        except Exception as e:
            print(rect_a)
            print(rect_b)
            print("cal_intersection_ratio")
            return {'ratio_a':0, 'ratio_b':0, 'area':0}

    
    # 删除当前当前用户进行的制定页面的标注
    @method_decorator(login_required)
    def delete_all_polygon(self, request):
        try:
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            item_delete = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))
            count = item_delete.count()
            item_delete.delete()
            return HttpResponse(count)
        except Exception as e:
            print(e)
            return HttpResponse("err")

    
    # entropy threshold reset
    @method_decorator(login_required)
    def entropy_thr_reset(self, request):
        try:
            image_id = request.GET.get("image_id")
            entropy_thr = request.GET.get("entropy_thr")
            image = PDFImage.objects.get(id=image_id)  # 被标注的图片
            image_user_conf, isCreate = image.imageuserconf_set.get_or_create(create_user_id=str(request.user), defaults={"entropy_thr":entropy_thr})
            if isCreate==False:
                image_user_conf.entropy_thr=entropy_thr
                image_user_conf.save()
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse(e)

    # 修改指定IP的多边形标注
    @method_decorator(login_required)
    def alter_polygon_by_id(self, request):
        try:
            polygon_id = request.GET.get("polygon_id")
            points = request.GET.get("points")
            item_alter = OcrLabelingPolygon.objects.get(id=polygon_id)
            if str(request.user)!=item_alter.create_user_id:
                return HttpResponse("ploygon不属于当前用户")
            else:
                item_alter.polygon = points.encode("utf-8")
                item_alter.save()
                return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse(e)


    # 删除指定IP的多边形标注
    @method_decorator(login_required)
    def delete_polygon_by_id(self, request):
        try:
            polygon_id = request.GET.get("polygon_id")
            item_delete = OcrLabelingPolygon.objects.get(id=polygon_id)
            if str(request.user)!=item_delete.create_user_id:
                return HttpResponse("ploygon不属于当前用户")
            else:
                item_delete.delete()
                return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse(e)

    # 删除指定ip的多边形标注
    @method_decorator(check_login)
    def delete_polygon(self, request):
        """
        :param request:
        :return:
        """
        try:
            body=None
            polygon_id = request.GET.get("polygon_id")
            item_delete = OcrLabelingPolygon.objects.get(id=polygon_id)
            if str(request.user)!=item_delete.create_user_id:
                result = {"status":"failure" , "username":str(request.user), "tip":"polygon不属于当前用户"}
                return JsonResponse(result)
            else:
                item_delete.delete()
                result = {"status":"success" , "username":str(request.user), "tip": "删除polygon成功", "body":body}
                return JsonResponse(result)
        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)

    # 删除指定IP的偏旁部首
    @method_decorator(login_required)
    def delete_elem_by_id(self, request):
        try:
            elem_id = request.GET.get("elem_id")
            elem_delete = ChineseElem.objects.get(id=elem_id)
            if str(request.user)!=elem_delete.create_user_id:
                return HttpResponse("ploygon不属于当前用户")
            else:
                # 删除对应的已经标注的polygon信息
                polygonelem_set = elem_delete.polygonelem_set.all()
                polygonelem_delete_num = polygonelem_set.count()
                for polygonelem in polygonelem_set:
                    polygonelem.delete()
                # 删除对应的汉字-偏旁关系
                characterelem_set = elem_delete.characterelem_set.all()
                characterelem_delete_num = characterelem_set.count()
                for characterelem in characterelem_set:
                    characterelem.delete()

                elem_delete.delete()
                context = {
                    "polygonelem_delete_num":polygonelem_delete_num,
                    "characterelem_delete_num":characterelem_delete_num
                }
                return HttpResponse(json.dumps(context))
        except Exception as e:
            print(e)
            return HttpResponse(e)


    # delete labeles relate to an apointed region
    @method_decorator(login_required)
    def delete_region(self, request):
        delete_info = []
        try:
            select_pointsStr = request.GET.get("rotate_points_str")
            select_points = json.loads(select_pointsStr)  # region to be deleted
            image_id = request.GET.get("image_id")  # related picture
            image = PDFImage.objects.get(id=image_id) 
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user
            rect_region = OcrView.get_rect_info(select_points[0], select_points[2])

            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info.append({'polygon_id':polygon.id, 'rect_info':rect_candidate})
                    polygon.delete()
            return HttpResponse(json.dumps(delete_info))
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @method_decorator(check_login)
    def region_delete(self, request):
        """
        :param request:
        :return:
        """
        try:
            delete_info = dict()
            select_pointsStr = request.GET.get("rotate_points_str")
            select_points = json.loads(select_pointsStr)  # region to be deleted
            image_id = request.GET.get("image_id")  # related picture
            image = PDFImage.objects.get(id=image_id) 
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belong to user
            rect_region = OcrView.get_rect_info(select_points[0], select_points[2])
            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info[polygon.id]=rect_candidate
                    polygon.delete()
            body={
                "delete_info":delete_info,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "区域删除成功", "body":body}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)
            
    @staticmethod
    def merge_rects(rect_array):
        x_min=10240000
        x_max=-10240000
        y_min=10240000
        y_max=-10240000
        rect_merged = []
        for elem in rect_array:
            rect_info = elem['rect_info']
            x_min = min(x_min,min(rect_info['x'],rect_info['x_']))
            x_max = max(x_max,max(rect_info['x'],rect_info['x_']))
            y_min = min(y_min,min(rect_info['y'],rect_info['y_']))
            y_max = max(y_max,max(rect_info['y'],rect_info['y_']))
        rect_merged= [
            {'x':x_min, 'y':y_min},
            {'x':x_max, 'y':y_min},
            {'x':x_max, 'y':y_max},
            {'x':x_min, 'y':y_max}
        ]
        return rect_merged

    # 融合选定区域内的标注
    @method_decorator(login_required)
    def merge_labeling(self, request):
        try:
            delete_info = None
            polygon_add = None
            tip = []
            points_rotate_str = request.GET.get("rotate_points_str")
            points_rotate = json.loads(points_rotate_str)
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)
            delete_info = []
            conf = image.imageuserconf_set.get(create_user_id=str(request.user))
            w = image.width
            h = image.height
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user
            rect_region = OcrView.get_rect_info(points_rotate[0], points_rotate[2])
            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                OcrView.rotate_points(points,conf.rotate_degree,w,h)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info.append({'polygon_id':polygon.id, 'rect_info':copy.deepcopy(rect_candidate)})
                    polygon.delete()
            if delete_info != []:
                rect_merged = OcrView.merge_rects(delete_info)
                OcrView.rotate_points(rect_merged, -conf.rotate_degree, w, h)
                polygon = OcrLabelingPolygon(pdfImage=image, polygon=json.dumps(rect_merged).encode("utf-8"), create_user_id=str(request.user))
                polygon.save()
                polygon_add= {
                    "image_id":image_id,
                    "create_user_id":str(request.user),
                    "polygon_id":polygon.id,
                    "points":str(polygon.polygon,"utf-8"),
                }
            merge_labeling_info = {
                "delete_info":delete_info,
                "polygon_add":polygon_add,
            }
            return HttpResponse(json.dumps(merge_labeling_info))
        except Exception as e:
            print(e)
            return HttpResponse("err")


    @method_decorator(login_required)
    def yolo_labeling(self, request):
        try:
            class_type = [
                "melon",
                "pea2",   
                "torch",  
                "Flower", 
                "pea1",   
                "cushaw", 
                "nuts",   
                "pumpkin",
                "pepper", 
                "nutl",   
                "zombi0",
                "sun",
                "ball",
                "dolly",
                "dead0",
                "shovel",
                "block",
                "head0",
                "zombiBlock",
                "fireBall"
            ]
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)
            pil_image = Image.open(image.data_byte)
            args={
                "create_user_id":str(request.user),
                "image_id":image_id,
                "image":pil_image,
            }
            red = redis.Redis(connection_pool=self.redis_pool)
            print("kaka")
            red.rpush("pvzocr", pickle.dumps(args))  # 此处不做重复性检查
            pvz_ocr = []
            rs_key = "%s_%s_%s" % ("rs_pvzocr", str(request.user), image_id)
            time.sleep(0.5)
            for i in range(50):
                if red.exists(rs_key):
                    pvz_ocr = json.loads(red.get(rs_key))
                    for item in pvz_ocr:
                        class_index = item['class_index']
                        top = item['top']
                        bottom = item['bottom']
                        left = item['left']
                        right = item['right']
                        rect = [
                            {'x':left, 'y':top},
                            {'x':right, 'y':top},
                            {'x':right, 'y':bottom},
                            {'x':left, 'y':bottom},
                        ]
                        polygon = OcrLabelingPolygon(pdfImage=image, polygon=json.dumps(rect).encode("utf-8"), create_user_id=str(request.user))
                        polygon.save()
                        elem = ChineseElem.objects.get(desc_info=class_type[class_index])
                        PolygonElem(polygon=polygon, elem=elem, create_user_id=str(request.user), desc_info="created_auto").save()

                    red.delete(rs_key)
                    break
                else:
                    time.sleep(0.01)

            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponse("err")

    @staticmethod
    def achieveImageRotated(user, image, degree_to_rotate, width=0, height=0):
        rotate_image_key = "image_rotated_resized_%s_%s_%.2f_%d_%d" % (user, image.id, degree_to_rotate,width,height)
        image_rotate_str = cache.get(rotate_image_key)
        if image_rotate_str is None:
            #读取原始图像
            cv_image = cv.imread(image.data_byte)
            if height==0 or width==0:
                height, width = cv_image.shape
            if abs(degree_to_rotate)>0.000001:
                matrotate = cv.getRotationMatrix2D((cv_image.shape[1]*0.5, cv_image.shape[0]*0.5), degree_to_rotate, 1)
                image_rotated = cv.warpAffine(cv_image, matrotate, (cv_image.shape[1], cv_image.shape[0]))
            else:
                image_rotated = cv_image
            image_resized = cv.resize(image_rotated, (width, height), interpolation=cv.INTER_LINEAR)
            cache.set(rotate_image_key, pickle.dumps(image_resized), nx=True) 
            cache.expire(rotate_image_key, 3600)
            print("set cache:%s" % rotate_image_key)
            return image_rotated
        else:
            print("bingo:%s" % rotate_image_key)
            return pickle.loads(image_rotate_str)

    @staticmethod
    def achieveGrayImageRotated(user, image, degree_to_rotate, width=0, height=0):
        rotate_image_key = "gray_image_rotated_resized_%s_%s_%.2f_%d_%d" % (user, image.id, degree_to_rotate,width,height)
        image_rotate_str = cache.get(rotate_image_key)
        if image_rotate_str is None:
            #读取原始图像
            cv_image = cv.imread(image.data_byte)
            cv_gray = cv.cvtColor(cv_image, cv.COLOR_RGB2GRAY)
            if height==0 or width==0:
                height, width = cv_gray.shape
            if abs(degree_to_rotate)>0.000001:
                matrotate = cv.getRotationMatrix2D((cv_gray.shape[1]*0.5, cv_gray.shape[0]*0.5), degree_to_rotate, 1)
                image_rotated = cv.warpAffine(cv_gray, matrotate, (cv_gray.shape[1], cv_gray.shape[0]))
            else:
                image_rotated = cv_gray
            image_resized = cv.resize(image_rotated, (width, height), interpolation=cv.INTER_LINEAR)
            cache.set(rotate_image_key, pickle.dumps(image_resized), nx=True) 
            cache.expire(rotate_image_key, 3600)
            print("set cache:%s" % rotate_image_key)
            return image_rotated
        else:
            print("bingo:%s" % rotate_image_key)
            return pickle.loads(image_rotate_str)


    @method_decorator(login_required)
    def rough_labeling(self, request):
        try:
            points_rotate_str = request.GET.get("rotate_points_str")
            points_rotate = json.loads(points_rotate_str)
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)
            conf = image.imageuserconf_set.get(create_user_id=str(request.user))
            conf_is_vertical = conf.is_vertical
            rotate_degree = conf.rotate_degree
            filter_size = conf.filter_size
            conf_entropy_thr = conf.entropy_thr
            w = image.width
            h = image.height
            # 旋转后矩形框为竖直
            OcrView.rotate_points(points_rotate, rotate_degree, w, h)
            delete_info = []
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user

            rect_region = OcrView.get_rect_info(points_rotate[0], points_rotate[2])
            h_w_ratio = abs(rect_region['h']*1.0/rect_region['w'])  # 高宽比
            is_vertical = True
            if h_w_ratio>2:
                is_vertical = True
            elif h_w_ratio<0.5:
                is_vertical = False
            elif h_w_ratio>=0.5 and h_w_ratio<=2:
                is_vertical = conf_is_vertical
            else:
                pass

            # 删除当前用户下与候选区域相交的标注
            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                OcrView.rotate_points(points,rotate_degree,w,h)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info.append({'polygon_id':polygon.id, 'rect_info':rect_candidate})
                    polygon.delete()

            # 应加入缓存机制
            image_rotated = OcrView.achieveGrayImageRotated(str(request.user), image, rotate_degree, width=0, height=0)
            box = (rect_region['x'],rect_region['y'],rect_region['x_'],rect_region['y_'])
            print(box)
            region_select = image_rotated[box[1]:box[3],box[0]:box[2]]
            print(region_select)
            array_image = 1-region_select/255.0  # 选定区域图片数组
            # get projection
            if is_vertical is True:
                projection = array_image.sum(axis=1)/rect_region['w']
                projection = projection*2
            else:
                projection = array_image.sum(axis=0)/rect_region['h']
                projection = projection*2

            # get entropy
            gray_mean = (1-image_rotated/255.0).mean()  # 区域灰度平均值
            background_modification = max(0.0000000001,0.16-gray_mean)
            array_image = array_image + background_modification  # Background entropy solidification
            if is_vertical is True:
                probability = array_image/array_image.sum(axis=1, keepdims=True)
            else:
                probability = array_image/array_image.sum(axis=0, keepdims=True)

            entropy_src = -probability*np.log(probability)
            if is_vertical is True:
                entropy = entropy_src.sum(axis=1)
            else:
                entropy = entropy_src.sum(axis=0)
            entropy = maxminnormalization(entropy,0,1)
            entropy_diff = list(np.diff(entropy))
            entropy_diff.insert(0,0)
            entropy_thr = conf_entropy_thr  # 熵阈
            projection_thr_easing =  conf.projection_thr_easing# 宽松影阈
            projection_thr_strict = conf.projection_thr_strict # 投影阈
            # 分割第一维
            interval_dim1 = OcrView.cal_interval(entropy, entropy_thr, projection, projection_thr_strict, projection_thr_easing)
            # 文字融合暂缺
            # 文字第二维定位
            text_rect = []
            for item in interval_dim1["text_interval"]:
                start_dim1 = item["start"]
                end_dim1 = item["end"]+1
                if is_vertical is True:
                    text_slice = array_image[start_dim1:end_dim1, :]
                else:
                    text_slice = array_image[:,start_dim1:end_dim1]

                height, width = text_slice.shape
                if is_vertical is True:
                    projection_dim2 = text_slice.sum(axis=0)/(end_dim1*1.0-start_dim1)
                    probability_dim2 =  text_slice/text_slice.sum(axis=0, keepdims=True)
                    entropy_src_dim2 = -probability_dim2*np.log(probability_dim2)
                    entropy_dim2 = entropy_src_dim2.sum(axis=0)
                else:
                    projection_dim2 = text_slice.sum(axis=1)/(end_dim1*1.0-start_dim1)
                    probability_dim2 =  text_slice/text_slice.sum(axis=1, keepdims=True)
                    entropy_src_dim2 = -probability_dim2*np.log(probability_dim2)
                    entropy_dim2 = entropy_src_dim2.sum(axis=1)
                entropy_dim2 = maxminnormalization(entropy_dim2,0,1)

                area_thr = filter_size
                interval_dim2 = OcrView.cal_interval(entropy_dim2, entropy_thr, projection_dim2, projection_thr_strict, projection_thr_easing)
                if is_vertical is True:
                    for item_dim2 in interval_dim2["text_interval"]:
                        start_dim2 = item_dim2["start"]
                        end_dim2 = item_dim2["end"]
                        area = abs(end_dim2-start_dim2) * abs(end_dim1-start_dim1)
                        if area < area_thr or area>1000000:
                            continue
                        text_slice3 = array_image[start_dim1:end_dim1, start_dim2:end_dim2]
                        height3, width3 = text_slice3.shape
                        projection3 = text_slice3.sum(axis=1)/abs(end_dim2-start_dim2)  # 第三维投影
                        projection3 = projection3*2
                        probability3 =  text_slice3/text_slice3.sum(axis=1, keepdims=True)  # 投影归一化
                        entropy_src3 = -probability3*np.log(probability3)  # 熵计算
                        entropy3 = entropy_src3.sum(axis=1)
                        entropy3 = maxminnormalization(entropy3,0,1)
                        entropy3_diff = list(np.diff(entropy3))
                        entropy3_diff.insert(0, 0)
                        interval_dim3 = OcrView.cal_interval(entropy3, entropy_thr, projection3, projection_thr_strict, projection_thr_easing)
                        for item_dim3 in interval_dim3["text_interval"]:
                            start_dim3 = item_dim3["start"]
                            end_dim3 = item_dim3["end"]
                            area3 = abs(end_dim3-start_dim3)*abs(end_dim2-start_dim2)
                            if area3 <1:
                                continue
                            text_rect.append([
                                {'x':start_dim2+points_rotate[0]['x'], 'y':start_dim1+points_rotate[0]['y']+start_dim3},
                                {'x':end_dim2+points_rotate[0]['x'],'y':start_dim1+points_rotate[0]['y']+start_dim3},
                                {'x':end_dim2+points_rotate[0]['x'],'y':start_dim1+points_rotate[0]['y']+end_dim3},
                                {'x':start_dim2+points_rotate[0]['x'], 'y':start_dim1+points_rotate[0]['y']+end_dim3}
                            ])
                else:
                    for item_dim2 in interval_dim2["text_interval"]:
                        start_dim2 = item_dim2["start"]
                        end_dim2 = item_dim2["end"]
                        area = abs(end_dim2-start_dim2) * abs(end_dim1-start_dim1)
                        if area < area_thr or area>1000000:
                            continue
                        text_slice3 = array_image[start_dim2:end_dim2, start_dim1:end_dim1]
                        height3, width3 = text_slice3.shape
                        projection3 = text_slice3.sum(axis=0)/abs(end_dim2 - start_dim2)  # 第三维投影
                        projection3 = projection3 * 2
                        probability3 = text_slice3/text_slice3.sum(axis=0, keepdims=True)  # 投影归一化
                        entropy_src3 = -probability3*np.log(probability3)  # 熵计算
                        entropy3 = entropy_src3.sum(axis=0)
                        entropy3 = maxminnormalization(entropy3, 0, 1)
                        entropy3_diff = list(np.diff(entropy3))
                        entropy3_diff.insert(0, 0)
                        interval_dim3 = OcrView.cal_interval(entropy3, entropy_thr, projection3, projection_thr_strict, projection_thr_easing)
                        for item_dim3 in interval_dim3["text_interval"]:
                            start_dim3 = item_dim3["start"]
                            end_dim3 = item_dim3["end"]
                            area3 = abs(end_dim3-start_dim3)*abs(end_dim2-start_dim2)
                            if area3<area_thr:
                                continue
                            text_rect.append([
                                {'x':start_dim3+start_dim1+points_rotate[0]['x'], 'y':points_rotate[0]['y']+start_dim2},
                                {'x':end_dim3+points_rotate[0]['x']+start_dim1+1,'y':points_rotate[0]['y']+start_dim2},
                                {'x':end_dim3+points_rotate[0]['x']+start_dim1+1,'y':end_dim2+points_rotate[0]['y']},
                                {'x':start_dim3+start_dim1+points_rotate[0]['x'], 'y':points_rotate[0]['y']+end_dim2}
                            ])


            # add rect
            polygon_add = []
            for rect in text_rect:
                OcrView.rotate_points(rect, -rotate_degree, w, h)
                polygon = OcrLabelingPolygon(pdfImage=image, polygon=json.dumps(rect).encode("utf-8"), create_user_id=str(request.user))
                polygon.save()
                polygon_add.append({
                    "image_id":image_id,
                    "create_user_id":str(request.user),
                    "polygon_id":polygon.id,
                    "points":str(polygon.polygon,"utf-8")
                })

            body = {
                "projection":json.dumps(projection.tolist(),cls=NpEncoder),
                "entropy":json.dumps(entropy.tolist(),cls=NpEncoder),
                "entropy_diff":json.dumps(entropy_diff,cls=NpEncoder),
                "gray_mean":float(gray_mean),
                "text_interval":interval_dim1["text_interval"],
                "start_pos":interval_dim1["start_pos"],
                "stop_pos":interval_dim1["stop_pos"],
                "delete_info":delete_info,
                "polygon_add":polygon_add,
                "projection_thr_easing":projection_thr_easing,
                "projection_thr_strict":projection_thr_strict,
                "entropy_thr":entropy_thr,
            }
            result = {"status":"success" , "username":str(request.user), "tip": "粗标注成功", "body":body}
            return JsonResponse(result)
        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure" , "username":str(request.user), "tip":"内部错误"}
            return JsonResponse(result)


    # calculate intervals of a line
    @staticmethod
    def cal_interval(entropy,entropy_thr, projection, projection_thr_strict, projection_thr_easing):
        text_interval = []
        has_head = False
        start_pos = []  
        stop_pos = []
        interval_head_tmp = -1
        for i,val in enumerate(entropy):
            if has_head == False:
                if val < entropy_thr or projection[i]>projection_thr_strict:
                    has_head = True
                    start_pos.append(i)
                    interval_head_tmp = i
            else:
                if (val > entropy_thr and projection[i]<projection_thr_strict):
                    has_head = False
                    stop_pos.append(i)
                    text_interval.append({"start":interval_head_tmp,"end":i})
        if has_head is True:
            text_interval.append({"start":interval_head_tmp,"end":len(entropy)-1})
            stop_pos.append(len(entropy)-1)
        return {"text_interval":text_interval, "start_pos":start_pos, "stop_pos":stop_pos}   

