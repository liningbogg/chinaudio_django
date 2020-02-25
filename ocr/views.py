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
from PIL import Image
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import *
from ocr.models import *
import copy

# 归一化函数
def maxminnormalization(x, minv, maxv):
    min_val = np.min(x)
    max_val = np.max(x)
    y = (x - min_val) / (max_val - min_val + 0.0000000001) * (maxv - minv) + minv
    return y

# Create your views here.
class OcrView(View):

    def __init__(self):
        super(View, self).__init__()
        self.redis_pool=redis.ConnectionPool(host='localhost', port=6379,db=0, password='1a2a3a', encoding='utf-8')


    @classmethod
    @method_decorator(login_required)
    def index(cls, request):
        """
        古琴数字化数据库首页
        """
        user_id = str(request.user)
        ocrPDFList = OcrPDF.objects.filter(create_user_id=request.user, is_deleted=False)
        assist_request_in_set = OcrAssistRequest.objects.filter(owner=user_id,status="pushed")
        assist_request_out_set = OcrAssistRequest.objects.filter(create_user_id=user_id)
        ocr_assist_set = OcrAssist.objects.filter(assist_user_name=user_id, is_deleted=False)
        statistic = []
        for ocrpdf in ocrPDFList:
            count_all = 0
            count_user = 0
            image_set = ocrpdf.pdfimage_set.all()
            for image in image_set:
                count_all = count_all+ image.ocrlabelingpolygon_set.all().count()
                count_user = count_user+  image.ocrlabelingpolygon_set.filter(create_user_id =user_id).count()
            data = {"id":ocrpdf.id,"title":ocrpdf.title,"frame_num":ocrpdf.frame_num,"current_frame":ocrpdf.current_frame,"assist_num":ocrpdf.assist_num ,"count_all":count_all,"count_user":count_user}
            statistic.append(data)

        context = {"assist_request_in_set":assist_request_in_set,"assist_request_out_set":assist_request_out_set,"ocr_assist_set":ocr_assist_set,"statistic":statistic}
        return render(request,'ocr_index.html',context)

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
                        "polygon_id":polygon.id,
                        "image_id":polygon.pdfImage.id,
                        "create_user_id":polygon.create_user_id,  # redundant data for a verification
                        "points":str(polygon.polygon,'utf-8')
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
            data_stream=io.BytesIO(ocrimage.data_byte)
            pil_image = Image.open(data_stream)
            width, height = pil_image.size
            (image_user_conf,isCreate) = ocrimage.imageuserconf_set.get_or_create(create_user_id=str(request.user),defaults={"rotate_degree":0})
            if abs(image_user_conf.rotate_degree)>0.0001:
                image_rotated = pil_image.rotate(image_user_conf.rotate_degree)
            else:
                image_rotated = pil_image
            image_resized = image_rotated.resize((tar_width, tar_height), Image.ANTIALIAS)
            '''
            gray_image = image_resized.convert('L')
            array_image = 255-np.asarray(gray_image)
            map_row = array_image.sum(axis=0)/255.0/tar_height
            print(map_row)
            '''
            trans_width,trans_height=image_resized.size
            new_imageIO = BytesIO()
            image_resized.save(new_imageIO,"JPEG")
            data_byte=new_imageIO.getvalue()
            return HttpResponse(data_byte, 'image/jpeg')

        except Exception as e:
            print(e)
            return None

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


    # 设置filter_size
    @method_decorator(login_required)
    def set_filter_size(self, request):
        try:
            filter_size = int(request.GET.get("filter_size"))
            image_user_conf_id = request.GET.get("image_user_conf_id")
            if filter_size>0 and filter_size<10240:
                image_user_conf = ImageUserConf.objects.get(id=image_user_conf_id)  # 被标注的图片
                image_user_conf.filter_size = filter_size
                image_user_conf.save()
                return HttpResponse("ok")
            else:
                return HttpResponse("err")
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
            data_stream=io.BytesIO(image.data_byte)
            pil_image = Image.open(data_stream)
            gray_image = pil_image.convert('F')
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


    @method_decorator(login_required)
    def add_labeling_polygon(self, request):
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
    def rough_labeling(self, request):
        try:
            points_rotate_str = request.GET.get("rotate_points_str")
            points_rotate = json.loads(points_rotate_str)
            image_id = request.GET.get("image_id")
            image = PDFImage.objects.get(id=image_id)
            conf = image.imageuserconf_set.get(create_user_id=str(request.user))
            w = image.width
            h = image.height
            # 旋转后矩形框为竖直
            OcrView.rotate_points(points_rotate, conf.rotate_degree, w, h)
            delete_info = []
            user_polygon_set = image.ocrlabelingpolygon_set.filter(create_user_id=str(request.user))  # all related label belonging to this user
            rect_region = OcrView.get_rect_info(points_rotate[0], points_rotate[2])
            h_w_ratio = abs(rect_region['h']*1.0/rect_region['w'])  # 高宽比
            is_vertical = True
            filter_size = conf.filter_size
            if h_w_ratio>2:
                is_vertical = True
            elif h_w_ratio<0.5:
                is_vertical = False
            elif h_w_ratio>=0.5 and h_w_ratio<=2:
                is_vertical = conf.is_vertical
            else:
                pass
            # 删除当前用户下与候选区域相交的标注
            for polygon in user_polygon_set:
                points = json.loads(polygon.polygon)
                OcrView.rotate_points(points,conf.rotate_degree,w,h)
                rect_candidate = OcrView.get_rect_info(points[0], points[2])
                intersection = OcrView.cal_intersection_ratio(rect_region, rect_candidate)
                intersection_ratio = intersection['ratio_b']
                if intersection_ratio > 0.75:
                    delete_info.append({'polygon_id':polygon.id, 'rect_info':rect_candidate})
                    polygon.delete()

            # rect = OcrView.get_rect_info(points_rotate[0],points_rotate[2])
            data_stream=io.BytesIO(image.data_byte)
            pil_image = Image.open(data_stream)
            gray_image = pil_image.convert('F')
            if abs(conf.rotate_degree)>0.0001:
                image_rotated = gray_image.rotate(conf.rotate_degree)
            else:
                image_rotated = gray_image
            box = (rect_region['x'],rect_region['y'],rect_region['x_'],rect_region['y_'])
            region_select = image_rotated.crop(box)
            array_image = 1-np.asarray(region_select)/255.0  # 选定区域图片数组
            # get projection
            if is_vertical is True:
                projection = array_image.sum(axis=1)/rect_region['w']
                projection = projection*2
            else:
                projection = array_image.sum(axis=0)/rect_region['h']
                projection = projection*2

            # get entropy
            gray_mean = (1-np.asarray(gray_image)/255.0).mean()  # 区域灰度平均值
            background_modification = max(0,0.16-gray_mean)
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
            entropy_thr = 0.9  # 熵阈
            projection_thr_strict = 0.6 # 投影阈
            projection_thr_easing = 0.01 # 宽松投影阈
            # 分割第一维
            interval_dim1 = OcrView.cal_interval(entropy, entropy_thr, projection, projection_thr_strict, projection_thr_easing)
            # 文字融合暂缺
            # 文字第二维定位
            text_rect = []
            for item in interval_dim1["text_interval"]:
                start_dim1 = item["start"]
                end_dim1 = item["end"]
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
                        interval_dim3 = OcrView.cal_interval(entropy3, 0.9, projection3, projection_thr_strict, projection_thr_easing)
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
                        projection3 = text_slice3.sum(axis=0)/abs(end_dim1 - start_dim1)  # 第三维投影
                        projection3 = projection3 * 2
                        probability3 = text_slice3/text_slice3.sum(axis=0, keepdims=True)  # 投影归一化
                        entropy_src3 = -probability3*np.log(probability3)  # 熵计算
                        entropy3 = entropy_src3.sum(axis=0)
                        entropy3 = maxminnormalization(entropy3, 0, 1)
                        entropy3_diff = list(np.diff(entropy3))
                        entropy3_diff.insert(0, 0)
                        interval_dim3 = OcrView.cal_interval(entropy3, 0.9, projection3, projection_thr_strict, projection_thr_easing)
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
                OcrView.rotate_points(rect, -conf.rotate_degree, w, h)
                polygon = OcrLabelingPolygon(pdfImage=image, polygon=json.dumps(rect).encode("utf-8"), create_user_id=str(request.user))
                polygon.save()
                polygon_add.append({
                    "image_id":image_id,
                    "create_user_id":str(request.user),
                    "polygon_id":polygon.id,
                    "points":str(polygon.polygon,"utf-8")
                })

            rough_labeling_info = {
                "projection":projection.tolist(),
                "entropy":entropy.tolist(),
                "entropy_diff":entropy_diff,
                "gray_mean":float(gray_mean),
                # "array_image":array_image.tolist(),
                "text_interval":interval_dim1["text_interval"],
                "start_pos":interval_dim1["start_pos"],
                "stop_pos":interval_dim1["stop_pos"],
                "delete_info":delete_info,
                "polygon_add":polygon_add,
            }
            return HttpResponse(json.dumps(rough_labeling_info, cls=NpEncoder))
        except Exception as e:
            print(e)
            return HttpResponse("err")


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

