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
from .models import Jacoco_report


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
    pid=request.POST.get('id')
    sql = '''
    SELECT COUNT(DISTINCT taskid) as 'total',sum(CASE WHEN r.result='success' THEN 1 ELSE 0 END) AS '成功数' ,count(*) as '总数'  
    FROM manager_resultdetail r WHERE r.plan_id IN (SELECT follow_id FROM manager_order WHERE main_id=%s) 
    AND r.result NOT IN ('omit') AND r.is_verify=1
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql, [pid])
        desc = cursor.description
        rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    success_rate = rows[0]['成功数'] / rows[0]['总数'] * 100 if rows[0]['总数'] != 0 else 0
    total = rows[0]['total'] if rows[0]['total'] is not None else 0

    # jacocoset = Jacoco_report.objects.values().filter(productid=pid) if pid != '' else None
    # if jacocoset:
    #     try:
    #         jobdess = []
    #         jobnames = jacocoset[0]['jobname']
    #         jobs = jobnames.split(";") if not jobnames.endswith(';') else jobnames.split(";")[:-1]
    #         for job in jobs:
    #             jobdess.append({
    #                 'id': job.split(":")[1],
    #                 'name': job.split(":")[0]
    #             })
    #     except:
    #         pass

    # else:
    #     jobdess = ''

    datanode = []
    try:
        plans = cm.getchild('product_plan', pid)
        for plan in plans:
            datanode.append({
                'id': 'plan_%s' % plan.id,
                'name': '%s' % plan.description,
            })
        return JsonResponse(
            simplejson(code=0, msg='操作成功', data=datanode, rate=str(success_rate)[0:5], total=total), safe=False)

    except:
        print(traceback.format_exc())
        code = 4
        msg = '查询数据库列表信息异常'
        return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def querytaskid(request):  # 查询验证任务最新id
    code = 0
    msg = ''
    taskids = []
    try:
        planid = request.POST.get('planid')
        plan = Plan.objects.get(id=planid)
        taskids = list(ResultDetail.objects.values('taskid').filter(plan=plan, is_verify=1).order_by('-createtime'))
        if taskids:
            taskids = taskids[0]["taskid"]
        else:
            code = 1
            msg = "任务还没有运行过！"
    except:
        code = 1
        msg = "出错了！"

    return JsonResponse(simplejson(code=code, msg=msg, data=taskids), safe=False)

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
    username = request.session.get("username", None)
    detail = list(ResultDetail.objects.filter(plan=plan, is_verify=1).order_by('-createtime'))
    config_id = plan.mail_config_id
    if detail is None:
        msg = "任务还没有运行过！"
    elif plan.is_running in ('1', 1):
        msg = "任务运行中，请稍后！"
    else:
        taskid = detail[0].taskid
        threading.Thread(target=sendmail, args=(config_id, username, taskid)).start()
        msg = '发送中...'
    return JsonResponse(simplejson(code=code, msg=msg), safe=False)


def sendmail(config_id, username, taskid):
    if config_id:
        mail_config = MailConfig.objects.get(id=config_id)
        user = User.objects.get(name=username)
        MainSender.send(taskid, user, mail_config)
        MainSender.dingding(taskid, user, mail_config)


@csrf_exempt
def reportchart(request):
    planid = request.POST.get("planid")
    code = 0
    taskids = list(ResultDetail.objects.values('taskid').filter(plan_id=planid, is_verify=1))
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
    taskid = request.POST.get("taskid")
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
    result = {"code": 0, "msg": "", "count": len(row), "data": row}
    return JsonResponse(result)


@csrf_exempt
def jacocoreport(request):
    code, msg = 0, ''
    s = requests.session()
    re = ''
    productid = request.POST.get('productid')
    jobname = request.POST.get('jobname')
    jacocoset = Jacoco_report.objects.values().filter(productid=productid)
    if jacocoset:
        authname, authpwd = jacocoset[0]['authpwd'], jacocoset[0]['authname']
    else:
        authname, authpwd = '', ''
    if len(authname) & len(authpwd) != 0 and jobname in jacocoset[0]['jobname']:
        s.auth = (jacocoset[0]['authname'], jacocoset[0]['authpwd'])
        try:
            jenkinsurl = jacocoset[0]['jenkinsurl']
            jsond = json.loads(s.get(jenkinsurl + "/job/" + jobname + "/lastBuild/jacoco/api/python?pretty=true").text)
            re = {
                'branchCoverage': jsond['branchCoverage']['percentage'],
                'classCoverage': jsond['classCoverage']['percentage'],
                'complexityScore': jsond['complexityScore']['percentage'],
                'instructionCoverage': jsond['instructionCoverage']['percentage'],
                'lineCoverage': jsond['lineCoverage']['percentage'],
                'methodCoverage': jsond['methodCoverage']['percentage'],
            }
        except:
            print(traceback.format_exc())
            code = 1
            msg = '查询异常'
            re = ''
    return JsonResponse(simplejson(code=code, msg=msg, data=re), safe=False)


@csrf_exempt
def plandebug(request):  # 调试日志
    res, type, taskid, code = doDebugInfo(request)
    return JsonResponse({"code": code, "type": type, "data": res, "taskid": taskid})


@csrf_exempt
def querybuglog(request):  # 历史缺陷
    gettime = request.POST.get("time")
    timestart = gettime.split(";")[0];
    timeend = gettime.split(";")[1];
    taskid=request.POST.get('taskid')
    res = []
    if taskid=='omit':
        #根据日期和任务id查询
        sql = '''
        SELECT r.taskid as '任务id', r.plan_id,r.createtime, b.id AS bussiness_id,p.description AS '计划名',c.description AS '用例名',
        s.description AS '步骤名',s.headers AS headers,s.body AS body,s.url AS url,
        b.businessname AS '测试点',b.itf_check AS '接口校验',b.db_check AS 'db校验',b.params AS '参数信息',
        r.error AS '失败原因' FROM manager_resultdetail r,manager_plan p,manager_case c,manager_step s,
        manager_businessdata b WHERE r.result IN ('error','fail') AND r.is_verify=1 AND r.plan_id=p.id AND r.case_id=c.id AND r.step_id=s.id
        AND r.businessdata_id=b.id AND  r.createtime  BETWEEN %s and %s 
        '''
        sql = sql if request.POST.get('planid') == '' else sql + 'and r.plan_id=' + request.POST.get('planid').split("_")[1]
        with connection.cursor() as cursor:
            cursor.execute(sql, [timestart, timeend + '23:59:59'])
            desc = cursor.description
            rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    else:
        #根据taskid查找
        sql = '''
        select * from (SELECT r.taskid AS '任务id',r.plan_id,r.createtime,b.id AS bussiness_id,p.description AS '计划名',
        c.description AS '用例名',s.description AS '步骤名',s.headers AS headers,s.body AS body,s.url AS url,b.businessname 
        AS '测试点',b.itf_check AS '接口校验',b.db_check AS 'db校验',b.params AS '参数信息',r.error AS '失败原因' FROM 
        manager_resultdetail r,manager_plan p,manager_case c,manager_step s,manager_businessdata b WHERE r.result 
        IN ('error','fail') AND r.is_verify=1 AND r.plan_id=p.id AND r.case_id=c.id AND r.step_id=s.id AND 
        r.businessdata_id=b.id AND r.taskid=%s) ORDER BY createtime
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql, [taskid])
            desc = cursor.description
            rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    for i in range(len(rows)):
        res.append(
            {'createtime':rows[i]['createtime'],'路径': rows[i]['用例名'] + '-' + rows[i]['步骤名'], '接口': rows[i]['url'],
             '测试点': rows[i]['测试点'], '参数信息': rows[i]['参数信息'], '失败原因': rows[i]['失败原因'],
             '任务id': rows[i]['任务id']})
    res, total = getpagedata(res, request.POST.get('page'), request.POST.get('limit'))

    return JsonResponse({"code": 0, 'count': total, "data": res})


@csrf_exempt
def initbugcount(request):  # 缺陷统计
    productid = request.POST.get('productid')

    sql = '''
    SELECT url as '接口' ,count(*) as '次数' from manager_resultdetail r ,manager_step s
    WHERE r.plan_id in (SELECT follow_id FROM manager_order WHERE main_id=%s) and r.result 
    in ('error','fail') and r.is_verify=1 and r.step_id=s.id GROUP BY s.url order by 次数 desc limit 10
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql, [productid])
        desc = cursor.description
        rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    return JsonResponse({"code": 0, "data": 13})


@csrf_exempt
def downloadlog(request):
    logname = './logs/deal/' + request.POST.get('taskid') + '.log'
    # file = open(logname, 'rb')
    with open(logname, 'r', encoding='utf-8') as f:
        log_text = f.read()
    log_text = log_text.replace("<span style='color:#FF3399'>", '').replace("</xmp>", '').replace(
        "<xmp style='color:#009999;'>", '').replace(
        "<span class='layui-bg-green'>", '').replace("<span class='layui-bg-red'>", '').replace(
        "<span class='layui-bg-orange'>", '').replace("</span>", '').replace(
        "<span style='color:#009999;'>", '').replace('<br>', '').replace(
        "'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
        '')
    response = HttpResponse(log_text)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename=%s.log' % request.POST.get('taskid')
    return response


@csrf_exempt
def queryProductSet(request):
    productid = request.POST.get('productid')
    try:
        jacocoset = list(
            Jacoco_report.objects.values('jenkinsurl', 'jobname', 'authname', 'authpwd').filter(productid=productid))
        res = jacocoset[0] if jacocoset else ''
        return JsonResponse({'code': '0', 'msg': 'success', 'data': res})
    except:
        return JsonResponse({'code': '1', 'msg': '查询设置出错'})


@csrf_exempt
def editProductSet(request):
    productid = request.POST.get('productid')
    msg = ''
    try:
        # jacoco相关配置，和项目关联
        if not Jacoco_report.objects.filter(productid=request.POST.get('productid')).exists():
            jacocoset = Jacoco_report()
            jacocoset.jenkinsurl = request.POST.get('jenkinsurl')
            jacocoset.authname = request.POST.get('authname')
            jacocoset.authpwd = request.POST.get('authpwd')
            jacocoset.jobname = request.POST.get('jobname')
            jacocoset.productid = request.POST.get('productid')
            jacocoset.save()
            msg = '保存成功'
        else:
            if re.search(r'(.*:.*(;)?)', request.POST.get('jobname')):
                jacocoset = Jacoco_report.objects.get(productid=request.POST.get('productid'))
                jacocoset.jenkinsurl = request.POST.get('jenkinsurl')
                jacocoset.authname = request.POST.get('authname')
                jacocoset.authpwd = request.POST.get('authpwd')
                jacocoset.jobname = request.POST.get('jobname')
                jacocoset.save()
            msg = '编辑成功'
        return JsonResponse({'code': '0', 'msg': '保存成功'})
    except:
        return JsonResponse({'code': '1', 'msg': '查询设置出错'})


@csrf_exempt
def downloadReport(request):
    reportname = './local_reports/report_' + request.POST.get("taskid") + '.html'
    if os.path.exists(reportname):
        with open(reportname, 'r', encoding='GBK') as f:
            text = f.read()
        response = HttpResponse(text)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename=%s.html' % request.POST.get('taskid')
        return response
    else:return JsonResponse({'msg': ''})

@csrf_exempt
def queryPlanState(request):
    planid=request.POST.get('id')[5:]
    plan=Plan.objects.get(id=planid)
    return JsonResponse({'data':plan.is_running})

@csrf_exempt
def planforceStop(request):
    planid=request.POST.get('id')[5:]
    plan=Plan.objects.get(id=planid)
    try:
        plan.is_running=0
        code=0
        msg='success'
    except:
        code = 1
        msg='stop_error'
    return JsonResponse({'code':code,'msg':msg})

@csrf_exempt
def query_third_call(request):
    planid = request.POST.get('planid')
    callername = models.Plan.objects.get(id=planid).author.name
    mwstr = 'callername=%s&taskid=%s' % (callername,planid)
    is_verify_url='%s/manager/third_party_call/?v=%s&is_verify=%s&planid=%s' % (settings.BASE_URL, EncryptUtils.base64_encrypt(EncryptUtils.des_encrypt(mwstr)), 1,planid)
    debug_url='%s/manager/third_party_call/?v=%s&is_verify=%s&planid=%s' % (settings.BASE_URL, EncryptUtils.base64_encrypt(EncryptUtils.des_encrypt(mwstr)), 0,planid)
    return JsonResponse({'is_verify_url':is_verify_url,'debug_url':debug_url})