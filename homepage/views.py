from django.db import connection
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from manager.invoker import gettaskresult, MainSender
from . import rpechart
from manager import cm
from manager.core import *

# Create your views here.
from manager.models import Product, Plan, ResultDetail
import json
from random import randrange




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
    taskids = []
    try:
        planid = request.POST.get('planid')
        plan = Plan.objects.get(id=planid)
        taskids = list(ResultDetail.objects.values('taskid').filter(plan=plan).order_by('-createtime'))
        if taskids:
            taskids = taskids[0]["taskid"]
        else:
            code = 2
            msg = "任务还没有运行过！"
    except:
        code = 1
        msg = "出错了！"

    return JsonResponse(simplejson(code=code, msg=msg, data=taskids), safe=False)


@csrf_exempt
def process(request):
    taskid = request.POST.get('taskid')
    code = 0
    log_text = ''
    is_done = 'no'
    done_msg = '结束计划'
    logname = "./logs/" + taskid + ".log"
    try:
        if os.path.exists(logname):
            with open(logname, 'r') as f:
                log_text = f.read()
        if done_msg in log_text:
            is_done = 'yes'
            print('日志执行结束', is_done)
    except:
        code = 1
        msg = "出错了！"
    return JsonResponse(simplejson(code=code, msg=is_done, data=log_text), safe=False)


@csrf_exempt
def globalsetting(request):
    code = 0
    msg = ''
    if request.method == 'POST':
        me2url = request.POST.get('me2url')
        redisurl = request.POST.get('redisurl')
        p = re.compile(
            '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)\:([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{4}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$')
        if p.match(me2url) and p.match(redisurl):
            data = {
                'me2url': me2url,
                'redisip': redisurl.split(':')[0],
                'redisport': redisurl.split(':')[1]
            }
            try:
                config = open("config", "w")
                config.write(json.dumps(data))
                config.close
                msg = "保存成功！"
            except:
                code = 1
                msg = '出错了！'
        else:
            code = 1
            msg = "请检查填写的地址是否正确！"
        return JsonResponse(simplejson(code=code, msg=msg), safe=False)
    else:
        try:
            config = open("config", "r")
            configtext = config.read()
            config.close
        except:
            code = 1
            msg = '出错了！'
        print(type(configtext))
        return JsonResponse(simplejson(code=code, msg=msg, data=json.loads(configtext)), safe=False)


def restart(request):
    taskid = request.POST.get('taskid')
    code = 0
    log_text = ''
    is_done = 'no'
    done_msg = '结束计划'
    logname = "./logs/" + taskid + ".log"
    try:
        if os.path.exists(logname):
            with open(logname, 'r') as f:
                log_text = f.read()
                f.close()
        if done_msg in log_text:
            is_done = 'yes'
            print('日志执行结束', is_done)
    except:
        code = 1
        msg = "出错了！"
    return JsonResponse(simplejson(code=code, msg=is_done, data=log_text), safe=False)


@csrf_exempt
def sendreport(request):
    code = 0
    msg = ''
    planid = request.POST.get('planid')
    plan = Plan.objects.get(id=planid)
    user = request.session.get("username", None)
    detail = list(ResultDetail.objects.filter(plan=plan).order_by('-createtime'))
    if detail is None:
        msg = "任务还没有运行过！"
    else:
        taskids = detail[0].taskid

    mail_res = MainSender.dingding(taskids, user, mail_config)

    url = 'https://oapi.dingtalk.com/robot/send?access_token=a39ed3fdf3d48d674afc5addb602ffe35330ee94bb736d447fcd6511cac70c25'
    pagrem = {
        "msgtype": "markdown",
        "markdown": {
            "title": "你的自动化测试报告已生成",
            "text": "#### 你的自动化测试报告已生成\n" +
                    "> 9度，西北风1级，空气良89，相对温度73%\n\n" +
                    "> ###### 10点20分发布 [天气](http://www.thinkpage.cn/) \n"
        },
        "at": {
            "isAtAll": True
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }
    requests.post(url, data=json.dumps(pagrem), headers=headers)
    return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def reportchart(request):
    planid = request.POST.get("planid")
    code = 0
    taskids = list(ResultDetail.objects.values('taskid').filter(plan_id=planid))
    if taskids:
        sql = ('''
        SELECT
            *,
            ( success * 100 / total ) rate,
            ( total - success - FAIL - skip ) error 
        FROM
            (
        SELECT
            plan_id,
            manager_plan.description,
            sum( CASE WHEN result = "success" THEN 1 ELSE 0 END ) AS success,
            sum( CASE WHEN result = "fail" THEN 1 ELSE 0 END ) AS FAIL,
            sum( CASE WHEN result = "skip" THEN 1 ELSE 0 END ) AS skip,
            count( result ) AS total,
            taskid,
            strftime('%%m-%%d %%H:%%M',manager_resultdetail.createtime) as time
        FROM
            manager_resultdetail
            LEFT JOIN manager_plan ON manager_resultdetail.plan_id = manager_plan.id 
            WHERE plan_id = %s 
        GROUP BY
            taskid 
            ) AS m  ORDER BY time DESC  LIMIT 10 
            ''')
        with connection.cursor() as cursor:
            cursor.execute(sql, [planid])
            row = cursor.fetchall()
            print(row)
        return JsonResponse(simplejson(code=code, data=row), safe=False)
    else:
        return JsonResponse(simplejson(code=1, data="任务还没有运行过！"), safe=False)


def add(num):
    _report = {}
    result = gettaskresult(num)
    _report[num] = {
        "planname": result["planname"],
        "success": result["success"],
        "fail": result["fail"],
        "skip": result["skip"],
        "total": result["total"],
        "error": result["error"],
        "success_rate": result["success_rate"],
        "reporttime": result["reporttime"],
    }
    return _report


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
