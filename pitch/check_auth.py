import jwt
from django.http import HttpResponse
def check_login(fn):
    def wrapper(request,*args,**kwargs):
        if request.session.get('is_login', False):
            # 可添加验证token的代码
            try:
                token = request.META.get("HTTP_AUTHORIZATION")
                jwt.decode(token,"815563",algorithm='HS256')
                return fn(request,*args,*kwargs)
            except jwt.InvalidTokenError as ite:
                return HttpResponse('token签名错误,请重新登录', status=401)
            except jwt.ExpiredSignatureError as ese:
                return HttpResponse('token超时,请重新登录', status=401)
            except Exception as e:
                return HttpResponse('token验证失败,请重新登录', status=401)
        else:
            # 获取用户当前访问的url，并传递给/user/login/
            return HttpResponse('登录失效,请重新登录', status=401)
    return wrapper

