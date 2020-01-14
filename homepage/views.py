from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
# from pyecharts.faker import Faker

from manager.invoker import gettaskresult
from . import rpechart
from manager import cm
from manager.core import *

# Create your views here.
from manager.models import Product, Plan, ResultDetail
import json
from random import randrange

from django.http import HttpResponse


# from pyecharts.faker import Faker
# from pyecharts import options as opts
# from pyecharts.charts import Pie, Bar, TreeMap, Line


@csrf_exempt
def homepage(request):
    return render(request, 'home1page.html')


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
    taskids = []
    try:
        planid = request.POST.get('planid')
        plan = Plan.objects.get(id=planid)
        detail = list(ResultDetail.objects.filter(plan=plan).order_by('-createtime'))
        if detail is None:
            msg = "任务还没有运行过！"
        else:
            taskids = detail[0].taskid
    except:
        code = 1
        msg = "出错了！"

    return JsonResponse(simplejson(code=code, msg=msg, data=taskids), safe=False)

@csrf_exempt
def process(request):
    code = 0
    msg = ''
    str=''
    try:
        taskid = request.POST.get('taskid')
        f = open("./logs/" + taskid + ".log", 'r')
        for line in f:
            str +=line
        f.close()
    except:
        code = 1
        msg = "出错了！"
    return JsonResponse(simplejson(code=code, msg=msg, data=str), safe=False)

# @csrf_exempt
# def reportone(request):
#     gettaskresult
#
#     pie = (
#         Pie()
#             .add("", [(1, 3)])
#             .set_colors(["green", "yellow"])
#             .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
#             .dump_options_with_quotes()
#     )
#
#     return rpechart.json_response(json.loads(pie))


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
