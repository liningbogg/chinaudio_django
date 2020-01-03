from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.contrib import *
from .forms import *
from web.models import *

# Create your views here.

class WebView(View):

    @classmethod
    @method_decorator(login_required)
    def index(cls, request):
        context = {"info":"test"}
        return render(request, 'web_index.html', context)

    @classmethod
    def login(cls, request):
        file_next = request.GET.get('next', "")
        if request.method == 'GET':
            if request.user is not None and request.user.is_active:
                return redirect("/web/index/")
            form = UserFormWithoutCaptcha()
            return render(request, 'login.html', {'login_form': form, })
        else:
            form = UserFormWithoutCaptcha(request.POST)
            if form.is_valid():
                username = request.POST.get('username', '')
                password = request.POST.get('password', '')
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    pitch_user =PitchUser.objects.filter(username=username)
                    session_key = pitch_user.first().session_key
                    if session_key:
                        request.session.delete(session_key)
                    auth.login(request, user)
                    pitch_user.update(session_key=request.session.session_key)
                    if file_next == "":
                        return redirect("/web/index/")
                    else:
                        return redirect(file_next)
                else:
                    message = "用户名或者密码错误"
                    return render(request, 'login.html', {'login_form': form, 'message': message})
            else:
                message = "表单数据错误"
                return render(request, 'login.html', {'login_form': form, 'message': message})

    @classmethod
    def logout(cls, request):
        auth.logout(request)
        return redirect("/web/accounts/login/")

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

