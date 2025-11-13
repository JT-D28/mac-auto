import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from homepage.models import Jenkins
from manager.cm import getchild
from manager.core import simplejson
from manager.models import Product, Plan


@csrf_exempt
def queryproduct(request):
    code, msg = 0, ''
    res = []
    try:
        list_ = list(Product.objects.filter(isdelete=0))
        for x in list_:
            o = dict()
            o['id'] = x.id
            o['description'] = x.description
            res.append(o)
        return JsonResponse(simplejson(code=0, msg='操作成功', data=res), safe=False)
    except:
        print(traceback.format_exc())
        code = 4
        msg = '查询数据库列表信息异常'
        return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def queryProductAndPlan(request):
    list_ = list(Product.objects.filter(isdelete=0))
    data = []
    try:
        for i, x in enumerate(list_):
            o = dict()
            o['value'] = str(x.id)
            o['label'] = x.description
            p = []
            plans = getchild('product_plan', x.id)
            for plan in plans:
                p.append({'value': str(plan.id), 'label': plan.description})
            o['children'] = p
            data.append(o)
        return JsonResponse({'code': 0, 'data': data})
    except:
        print(traceback.format_exc())
        return JsonResponse({'code': 1, 'data': '获取计划失败'})


@csrf_exempt
def queryProductSet(request):
    productid = request.POST.get('productid')
    try:
        jacocoset = list(
            Jenkins.objects.values('jenkinsurl', 'jobname', 'authname', 'authpwd', 'clearjob',
                                         'buildplans','gitpath','gitlaburl','gitlabtoken','projectjob','gitbranch').filter(productid=productid))
        if jacocoset:
            res = jacocoset[0]
            plans = res.get('buildplans').split(',')
            rmplans=[]
            finplans=[]
            for i in plans:
                if i !='':
                    try:
                        name = Plan.objects.get(id=i[5:]).description
                        finplans.append({'id':i,'name':name})
                    except:
                        rmplans.append(i)
            if rmplans:
                for j in rmplans:
                    plans.remove(j)
                jacoco = Jenkins.objects.get(productid=productid)
                jacoco.buildplans=','.join(plans)
                jacoco.save()
            res['buildplans']=finplans
        else:
            res = ''
        return JsonResponse({'code': '0', 'msg': 'success', 'data': res})
    except:
        print(traceback.format_exc())
        return JsonResponse({'code': '1', 'msg': '查询设置出错'})


@csrf_exempt
def editProductSet(request):
    productid = request.POST.get('productid')
    msg = ''
    try:
        if not Jenkins.objects.filter(productid=productid).exists():
            config = Jenkins()
            config.jenkinsurl = request.POST.get('jenkinsurl')
            config.authname = request.POST.get('authname')
            config.authpwd = request.POST.get('authpwd')
            config.jobname = request.POST.get('jobname')
            config.productid = request.POST.get('productid')
            config.clearjob = request.POST.get('jacocoClearJob')
            config.buildplans = request.POST.get('buildplans')
            config.projectjob = request.POST.get('projectjob')
            config.gitlabtoken = request.POST.get('gitlabtoken')
            config.gitlaburl = request.POST.get('gitlaburl')
            config.gitpath = request.POST.get('gitpath')
            config.gitbranch = request.POST.get('gitbranch')
            config.save()
            msg = '保存成功'
        else:
            config = Jenkins.objects.get(productid=request.POST.get('productid'))
            config.jenkinsurl = request.POST.get('jenkinsurl')
            config.authname = request.POST.get('authname')
            config.authpwd = request.POST.get('authpwd')
            config.jobname = request.POST.get('jobname')
            config.clearjob = request.POST.get('jacocoClearJob')
            config.buildplans = request.POST.get('buildplans')
            config.projectjob = request.POST.get('projectjob')
            config.gitlabtoken = request.POST.get('gitlabtoken')
            config.gitlaburl = request.POST.get('gitlaburl')
            config.gitpath = request.POST.get('gitpath')
            config.gitbranch = request.POST.get('gitbranch')
            config.save()
            msg = '编辑成功'
        return JsonResponse({'code': '0', 'msg': '保存成功'})
    except:
        print(traceback.format_exc())
        return JsonResponse({'code': '1', 'msg': traceback.format_exc()})


