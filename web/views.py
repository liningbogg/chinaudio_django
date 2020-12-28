from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.contrib import *
from .forms import *
from web.models import *
from pitch.check_auth import check_login
import traceback
import smtplib
import jwt
from django.http import JsonResponse
from email.mime.text import MIMEText
import logging
import random
from django.core.cache import cache

class WebView(View):
    msg_from = '1214397815@qq.com'  # 发送方邮箱
    passwd = 'ruzdcenkznfhhijf'  # 填入发送方邮箱的授权码
    msg_to = '1214397815@qq.com'  # 收件人邮箱
    logger = logging.getLogger('pitch')

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
                pitch_user =PitchUser.objects.get(username=username)
                session_key = pitch_user.session_key
                if session_key:
                    request.session.delete(session_key)
                auth.login(request, user)
                pitch_user.session_key=request.session.session_key
                pitch_user.save()
                request.session['is_login'] = True
                encoded_jwt = jwt.encode({'username':username},'815563',algorithm='HS256')  # token
                result = {"status":"success", "username":username, "tip":"用户登录成功:"+username, "token":str(encoded_jwt, encoding='utf-8')}
                print(encoded_jwt)
                print(result["token"])
                print(pitch_user.session_key)
                return JsonResponse(result)
            else:
                result = {"status":"failure", "username":username, "tip":"登录失败,用户名或密码错误"}
                return JsonResponse(result)

        except Exception as e:
            traceback.print_exc()
            result = {"status":"failure", "username":username, "tip":"登录失败,服务器内部错误"}
            return JsonResponse(result)

    def retrieve(self, request):
        try:
            body = None
            username = str(request.GET.get("username"))
            users = PitchUser.objects.filter(username=username)
            if users.count()>0:
                seed = '23456789abcdefghijkmnpqrstuvwxyz'
                checkcode = ''.join(random.choice(seed) for _ in range(6))
                # 将验证信息写入redis
                retrieve_key = "retrieve_%s" % username
                cache.set(retrieve_key, checkcode, nx=True)
                cache.expire(retrieve_key, 300)
                user=users[0]
                email = user.email
                msg = MIMEText('验证码:'+checkcode+'(请不要泄漏给任何人，验证码将用来重设密码, 5分钟内有效。)','plain','utf-8')
                msg['Subject'] = "古琴数据库验证码"+checkcode
                msg['From'] = self.msg_from
                msg['To'] = email
                self.sender = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
                self.sender.login(self.msg_from, self.passwd)
                self.sender.sendmail(self.msg_from, email, msg.as_string())
                email = email[0:5]+"***"+email[-8:]
                body = {"email": email}
                result = {"status":"success", "username":str(request.user), "tip":"获取邮箱缩略信息成功", "body":body}
                return JsonResponse(result)
            else:
                WebView.logger.error(e)
                result = {"status":"failure", "username":str(request.user), "tip":"用户名不存在"}
                return JsonResponse(result)

        except Exception as e:
            WebView.logger.error(e)
            result = {"status":"failure", "username":str(request.user), "tip":"获取邮箱缩略新信息错误"}
            return JsonResponse(result)


    def password_reset(self, request):
        try:
            body = None
            username = str(request.GET.get("username"))
            password = str(request.GET.get("password"))
            checkcode = str(request.GET.get("checkcode"))
            users = PitchUser.objects.filter(username=username)
            retrieve_key = "retrieve_%s" % username
            codepre = cache.get(retrieve_key)
            if codepre==checkcode:
                if users.count()>0:
                    user=users[0]
                    user.set_password(password)
                    user.save()
                    result = {"status":"success", "username":str(request.user), "tip":"获取邮箱缩略信息成功", "body":body}
                    return JsonResponse(result)
                else:
                    WebView.logger.info("用户名不存在")
                    result = {"status":"failure", "username":str(request.user), "tip":"用户名不存在"}
                    return JsonResponse(result)
            else:
                WebView.logger.info("验证码错误");
                result = {"status":"failure", "username":str(request.user), "tip":"验证码错误"}
                return JsonResponse(result)

        except Exception as e:
            WebView.logger.error(e)
            result = {"status":"failure", "username":str(request.user), "tip":"获取邮箱缩略新信息错误"}
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

