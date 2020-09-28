from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.contrib import *
from .forms import *
from web.models import *
import traceback
import jwt
from django.http import JsonResponse

# Create your views here.

class WebView(View):

    @classmethod
    def index(cls, request):
        context = {"info":"test"}
        return render(request, 'index.html', context)

    def login(self, request):
        try:
            username = request.GET.get("username")
            password = request.GET.get("password")
            user = auth.authenticate(username=username, password=password)  # 用户认证
            if user and user.is_active:
                pitch_user =PitchUser.objects.filter(username=username)
                session_key = pitch_user.first().session_key
                if session_key:
                    request.session.delete(session_key)
                auth.login(request, user)
                pitch_user.update(session_key=request.session.session_key)
                request.session['is_login'] = True
                encoded_jwt = jwt.encode({'username':username},'secret_key',algorithm='HS256')  # token
                result = {"status":"success", "username":username, "tip":"用户登录成功:"+username, "token":str(encoded_jwt, encoding='utf-8')}
                return JsonResponse(result)
            else:
                result = {"status":"failure", "username":username, "tip":"登录失败,用户名或密码错误"}
                return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure", "username":username, "tip":"登录失败,服务器内部错误"}
            return JsonResponse(result)

    # 用户退出登录
    def logout(self, request):
        try:
            auth.logout(request)
            result = {"status":"success", "username":str(request.user), "tip":"退出登录成功"}
            return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure", "username":str(request.user), "tip":"退出登录失败,内>部错误"}
            return JsonResponse(result)

    @classmethod
    def register(cls, request):
        message = ""
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            message = "请检查填写的内容！"
            if form.is_valid():
                # 获得表单数据
                username = form.cleaned_data['username']
                password = form.cleaned_data['password1']

                # 判断用户是否存在
                user = auth.authenticate(username=username, password=password)
                if user:
                    message = "用户已经存在"
                    return render(request, 'register.html', {'register_form': form, 'message': message})
                # 添加到数据库（还可以加一些字段的处理）
                user = PitchUser.objects.create_user(username=username, password=password)
                user.save()
                # 添加到session
                request.session['username'] = username
                # 调用auth登录
                auth.login(request, user)
                # 重定向到首页
                return redirect('/web/index')
            else:
                pass

        else:
            form = RegisterForm()
        # 将req 、页面 、以及context{}（要传入html文件中的内容包含在字典里）返回
        return render(request, 'register.html',  {'register_form': form, 'message': message})

