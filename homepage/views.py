import threading

from django.db import connection
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2 import configs
from manager.invoker import gettaskresult, MainSender
from manager import cm
from manager.core import *

# Create your views here.
from manager.models import Product, Plan, ResultDetail, MailConfig, Order
import json
from .dealinfo import doDebugInfo



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
            with open(logname, 'r', encoding='utf-8') as f:
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
    threading.Thread(target=sendmail, args=(request,)).start()
    return JsonResponse(simplejson(code=code, msg="发送中！"), safe=False)


def sendmail(request):
    planid = request.POST.get('planid')
    plan = Plan.objects.get(id=planid)
    username = request.session.get("username", None)
    detail = list(ResultDetail.objects.filter(plan=plan).order_by('-createtime'))
    if detail is None:
        msg = "任务还没有运行过！"
    else:
        taskid = detail[0].taskid

    config_id = plan.mail_config_id
    if config_id:
        mail_config = MailConfig.objects.get(id=config_id)
        user = User.objects.get(name=username)
        MainSender.send(taskid, user, mail_config)
        MainSender.dingding(taskid, user, mail_config)



@csrf_exempt
def reportchart(request):
    planid = request.POST.get("planid")
    code = 0
    taskids = list(ResultDetail.objects.values('taskid').filter(plan_id=planid,is_verify=1))
    if taskids:
        sql1 = '''
        SELECT x.plan_id,m.description,CONCAT(success),CONCAT(FAIL),CONCAT(skip),CONCAT(total),x.taskid,DATE_FORMAT(TIME,'%%m-%%d %%H:%%i') AS time,
        CONCAT(success*100/total) ,CONCAT(error) FROM (
        SELECT DISTINCT manager_resultdetail.taskid,plan_id FROM manager_resultdetail) AS x JOIN (
        SELECT taskid,sum(CASE WHEN result="success" THEN 1 ELSE 0 END) AS success,
        sum(CASE WHEN result="fail" THEN 1 ELSE 0 END) AS FAIL,
        sum(CASE WHEN result="error" THEN 1 ELSE 0 END) AS error,
        sum(CASE WHEN result="skip" THEN 1 ELSE 0 END) AS skip,
        sum(CASE WHEN result!="OMIT" THEN 1 ELSE 0 END) AS total,max(createtime) AS time 
        FROM manager_resultdetail GROUP BY taskid) AS n JOIN manager_plan m 
        ON x.taskid=n.taskid AND x.plan_id=m.id WHERE is_verify=1 and plan_id=%s ORDER BY time DESC LIMIT 10
        '''

        # sqlite3
        sql2 = '''
        SELECT plan_id,description,success,fail,skip,total,taskid,time,(success*100/total) rate,(total-success-FAIL-skip) error FROM (
        SELECT plan_id,manager_plan.description,sum(CASE WHEN result="success" THEN 1 ELSE 0 END) AS success,
        sum(CASE WHEN result="fail" THEN 1 ELSE 0 END) AS FAIL,sum(CASE WHEN result="skip" THEN 1 ELSE 0 END) AS skip,
        sum(CASE WHEN result="omit" THEN 1 ELSE 0 END) AS omit,sum(CASE WHEN result!="omit" THEN 1 ELSE 0 END) AS total,taskid,
        strftime('%%m-%%d %%H:%%M',manager_resultdetail.createtime) AS time FROM manager_resultdetail LEFT JOIN 
        manager_plan ON manager_resultdetail.plan_id=manager_plan.id WHERE plan_id=%s and is_verify=1 GROUP BY taskid) AS m ORDER BY time DESC LIMIT 10
        '''

        sql = sql2 if configs.dbtype == 'sqlite' else sql2

        with connection.cursor() as cursor:
            cursor.execute(sql, [planid])
            row = cursor.fetchall()
        print(row)
        return JsonResponse(simplejson(code=code, data=row), safe=False)
    else:
        return JsonResponse(simplejson(code=1, data="任务还没有运行过！"), safe=False)





@csrf_exempt
def badresult(request):

    taskid=request.POST.get("taskid")
    sql2 = '''
    SELECT manager_case.description as casename,manager_step.description as stepname,
    manager_businessdata.businessname as businessname,manager_businessdata.itf_check as itfcheck,
    manager_businessdata.db_check as dbcheck ,manager_resultdetail.result as result,manager_resultdetail.error as failresult 
    from manager_case,manager_step,manager_businessdata,manager_resultdetail where manager_resultdetail.result in('fail','error') 
    and manager_resultdetail.taskid=%s and manager_resultdetail.case_id=manager_case.id and manager_resultdetail.is_verify=1
    and manager_resultdetail.step_id=manager_step.id and manager_resultdetail.businessdata_id=manager_businessdata.id 
    order by manager_resultdetail.createtime 
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql2, [taskid])
        desc = cursor.description
        row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    result= {"code":0,"msg":"","count":len(row),"data":row}
    return JsonResponse(result)








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



@csrf_exempt
def plandebug(request): #调试日志
    res, type, taskid,code = doDebugInfo(request)
    return JsonResponse({"code":code, "type": type, "data": res, "taskid": taskid})


@csrf_exempt
def querybuglog(request): #历史缺陷
    productid=request.POST.get('productid')
    print(request.POST.get('time').split(" - ")[1])
    res=[]
    sql = '''
    SELECT b.id as bussiness_id,p.description as '计划名', c.description as '用例名' ,s.description as '步骤名',s.headers as headers,
    s.body as body ,s.url as url ,b.businessname as '测试点',b.itf_check as '接口校验',b.db_check as 'db校验', b.params as '参数信息',
    r.error as '失败原因' from manager_resultdetail r,manager_plan p,manager_case c,manager_step s,
    manager_businessdata b WHERE r.plan_id in (SELECT follow_id FROM manager_order where main_id=%s) 
    and r.result in ('error','fail') and r.is_verify=1 and r.plan_id=p.id and r.case_id=c.id 
    and r.step_id=s.id and r.businessdata_id=b.id and r.createtime BETWEEN %s and %s
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql, [productid,request.POST.get('time').split(" - ")[0],request.POST.get('time').split(" - ")[1]])
        desc = cursor.description
        rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    for i in range(len(rows)):
        res.append({'路径':rows[i-1]['计划名']+'-'+rows[i-1]['用例名']+'-'+rows[i-1]['步骤名'],'接口':rows[i-1]['url'],'测试点':rows[i-1]['测试点'],'参数信息':rows[i-1]['参数信息'],'失败原因':rows[i-1]['失败原因']})
    print(res)
    return JsonResponse({"code":0, "data": res})

