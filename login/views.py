from django.shortcuts import render, redirect, render_to_response
from django.conf import settings
from . import forms
from manager import models
from login import models as md

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from manager.core import *
from django.db.models import Q


# Create your views here

def global_setting(request):
    content = {
        'BASE_URL': settings.BASE_URL
    }
    return content


def page_not_found(request, exception, **kwargs):
    return render_to_response('manager/404.html')


def page_error(rquest):
    return render_to_response('manager/500.html')


def index(request):
    if request.session.get('is_login', None):
        username = request.session.get("username", None)
        return render(request, 'manager/index.html', locals())

    else:
        return redirect("/account/login/")


@csrf_exempt
def login(request):
    if request.method == 'POST':
        login_form = forms.UserForm(request.POST)
        message = ''
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')

            try:
                user = md.User.objects.get(name=username)
            except:
                message = '用户不存在'
                return render(request, 'login/login.html', locals())

            if EncryptUtils.md5_encrypt(password) == user.password:
                request.session.set_expiry(14400)
                request.session['is_login'] = True
                request.session['username'] = username
                print('登陆成功')

                return redirect("/manager/index/")
            else:
                message = '密码错误'
                return render(request, 'login/login.html', locals())
    login_form = forms.UserForm(request.POST)
    return render(request, 'login/login.html', locals())


def logout(request):
    request.session.flush()
    return redirect("/account/login/")


@csrf_exempt
def account(request):
    return render(request, 'login/account.html')


def queryaccount(request):
    searchvalue = request.GET.get('searchvalue')
    print("searchvalue=>", searchvalue)
    res = None
    if searchvalue:
        print("变量查询条件=>")
        res = list(md.User.objects.filter(Q(name__icontains=searchvalue)))
    else:
        res = list(md.User.objects.all())

    limit = request.GET.get('limit')
    page = request.GET.get('page')
    res, total = getpagedata(res, page, limit)

    jsonstr = json.dumps(res, cls=UserEncoder, total=total)
    return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def addaccount(request):
    code, msg = 0, ''
    try:

        user = md.User()
        user.name = request.POST.get('username')
        user.password = EncryptUtils.md5_encrypt(request.POST.get('password'))
        user.save()

        msg = '操作成功'
    except:
        print(traceback.format_exc())
        code = 1
        msg = '操作失败'

    return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def delaccount(request):
    code, msg = 0, ''
    try:
        ids = request.POST.get('ids').split(',')
        for id_ in ids:
            user = md.User.objects.get(id=id_)
            user.delete()

        msg = '操作成功'


    except:
        error = traceback.format_exc()
        code = 4
        msg = '操作异常[%s]' % error

    return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def queryoneaccount(request):
    code, msg = 0, ''
    try:
        id_ = request.POST.get('uid')
        user = md.User.objects.get(id=id_)
        jsonstr = json.dumps(user, cls=UserEncoder)
        return JsonResponse(jsonstr, safe=False)


    except:
        msg = '操作异常[%s]' % traceback.format_exc()
        return JsonResponse(simplejson(code=4, msg=msg), safe=False)


@csrf_exempt
def editaccount(request):
    code, msg = 0, ''
    try:
        user = md.User.objects.get(id=request.POST.get('uid'))
        user.name = request.POST.get('username')
        user.password = request.POST.get('password')
        user.save()
        msg = '操作成功'
    except:
        code = 4
        msg = '操作异常[%s]' % traceback.format_exc()

    return JsonResponse(simplejson(code=code, msg=msg), safe=False)


##测试接口
'''
测试表达式
'''


@csrf_exempt
def testexpress(request):
    return JsonResponse({'code': 1, 'bool': True, 'str': 'hhh', 'nullstr': None, 'spacestr': '', 'array': [],
                         'data': [{'token': 'tokenyyeyye'}], 'qibastr': '10,203.30'}, safe=False)

# '''
# 测试特殊返回字符串
# '''
# @csrf_exempt
# def testqipa(request):
# 	return JsonResponse({'qibastr':'10,203.30'},safe=False)
