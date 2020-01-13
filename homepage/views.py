from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from manager import cm
from manager.core import *

# Create your views here.
from manager.models import Product, Plan, ResultDetail


@csrf_exempt
def homepage(request):
    return render(request, 'homepage.html')


@csrf_exempt
def queryproduct(request):
    code, msg = 0, ''
    res = []
    try:
        list_ = list(Product.objects.all())
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
def queryplan(request):
    code, msg = 0, ''
    res = []
    datanode = []
    try:
        plans = cm.getchild('product_plan', request.POST.get('id'))
        for plan in plans:
            datanode.append({
                'id': 'plan_%s' % plan.id,
                'name': '%s' % plan.description,
            })
        return JsonResponse(simplejson(code=0, msg='操作成功', data=datanode), safe=False)

    except:
        print(traceback.format_exc())
        code = 4
        msg = '查询数据库列表信息异常'
        return JsonResponse(simplejson(code=code, msg=msg), safe=False)

@csrf_exempt
def querytaskid(request):
    code = 0
    msg = ''
    taskids = None
    try:
        planid = request.POST.get('planid')
        plan = Plan.objects.get(id=planid)
        detail = list(ResultDetail.objects.filter(plan=plan).order_by('-createtime'))
        taskid = detail[0].taskid
        print(taskid)
    except Exception as e:
        code = 1
        msg = str(e)

    return JsonResponse(simplejson(code=code, msg=msg, data=taskid), safe=False)


@csrf_exempt
def jenkins_add(request):
    code, msg = 0, ''
    s = requests.session()
    s.auth = ('tfp-test', 'tfp-test')
    try:
        jenkinsurl = request.POST.get('jenkinsurl')
        servicename = request.POST.get('servicename')
        jobname = request.POST.get('jobname')

        jsond = json.loads(s.get(jenkinsurl + "/job/" + jobname + "/lastBuild/jacoco/api/python?pretty=true").text)
        del jsond["_class"]
        del jsond["previousResult"]
        print(jsond)
        for kind in jsond:
            con = Jacoco_report()
            con.kind = kind
            con.covered = jsond[kind]["covered"]
            con.percentage = jsond[kind]["percentage"]
            con.percentageFloat = jsond[kind]["percentageFloat"]
            con.total = jsond[kind]["total"]
            con.missed = jsond[kind]["missed"]
            con.jenkinsurl = jenkinsurl
            con.servicename = servicename
            con.jobname = jobname
            con.save()
        msg = '添加成功'
    except:
        print(traceback.format_exc())
        code = 1
        msg = '添加异常'
    return JsonResponse(simplejson(code=code, msg=msg), safe=False)
