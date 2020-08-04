import threading
import traceback
import time
import jenkins
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from homepage.models import Jenkins
from homepage.views.charts import dealJacocoJobName
from manager.context import getRunningInfo
from manager.core import gettaskid
from manager.models import Plan


@csrf_exempt
def jenkinsJobRun(request):
    jobs = request.POST.getlist('jobnames[]')
    action = request.POST.get('action')
    res = ''
    try:
        jacocoset = Jenkins.objects.get(productid=request.POST.get('productid'))
        jobnames = dealJacocoJobName(jacocoset.jobname, jobs)
    except:
        return JsonResponse({'code': 1, 'data': '产品没有相应的代码覆盖率配置！'})

    # 测试连接
    try:
        server = jenkins.Jenkins(jacocoset.jenkinsurl, username=jacocoset.authname, password=jacocoset.authpwd)
        server.get_whoami()
    except:
        print(traceback.format_exc())
        return JsonResponse({'code': 1, 'data': '用户名或密码错误，请检查！'})

    # 任务运行状态检查
    msg = ''
    for job in jobnames:
        buildinfo = server.get_build_info(job, server.get_job_info(job)['lastBuild']['number'])
        if buildinfo['building']:
            msg += '%s:已经在运行了，请稍后再试<br>' % (job)
    if msg != '':
        return JsonResponse({'code': 1, 'data': msg})

    if action == 'jacocoMany':
        buildnumber0 = {}
        buildnumber1 = {}
        for index, job in enumerate(jobnames):
            buildnumber0[index] = server.get_job_info(job)['lastBuild']['number']  # 上次构建号
            server.build_job(job)
        while True:
            for index, job in enumerate(jobnames):
                buildnumber1[index] = server.get_job_info(job)['lastBuild']['number']
                if buildnumber1[index] == buildnumber0[index] + 1:
                    x = "构建中" if server.get_build_info(job, buildnumber1[index])['building'] else "启动失败"
                    res += '%s:%s<br>' % (job, x)
                if len(res.split("<br>")) - 1 == len(jobnames):
                    return JsonResponse({'code': 0, 'data': res})
                time.sleep(3)

    if action == 'jacocoOne':
        jobstr = ','.join(i for i in jobnames)
        job = 'tfp-cmbc-mysql-uat-report'
        print(server.get_job_config('tfp-cmbc-mysql-uat-report1'))
        try:
            if server.job_exists(job):
                server.delete_job(job)
                print('删除已有的执行任务')
            with open('./JenkinsConfig.xml') as f:
                config = f.read() % jobstr
            server.create_job(job, config)
            server.build_job(job)
            return JsonResponse({'code': 0, 'data': '任务已开始执行'})
        except:
            return JsonResponse({'code': 1, 'data': "可能出现了问题，可以前往jenkins检查"})


@csrf_exempt
def runforJacoco(request):
    productid = request.POST.get('productid')
    callername = request.session.get('username')
    try:
        jacocoConfig = Jenkins.objects.get(productid=productid)
        runningPlans=[]
        for i in jacocoConfig.buildplans.split(','):
            planid= i[5:]
            if getRunningInfo(planid, 'isrunning')!='0':
                planname = Plan.objects.get(id=planid).description
                runningPlans.append('【%s】'%planname)
        if runningPlans:
            msg = '计划'+'，'.join(runningPlans)+'当前正在运行，稍后再试'
            return JsonResponse({'code': 1, 'data': msg})
        threading.Thread(target=manyRun, args=(jacocoConfig, callername)).start()
    except:
        print(traceback.format_exc())
        return JsonResponse({'code': 1, 'data': '提交失败'})

    return JsonResponse({'code': 0, 'data': '提交成功'})


def manyRun(jacocoConfig, callername):
    url = jacocoConfig.jenkinsurl
    name = jacocoConfig.authname
    pwd = jacocoConfig.authpwd
    clearjob = jacocoConfig.clearjob
    buildplans = jacocoConfig.buildplans
    # 1.执行清理
    jenkinsBuild(url, name, pwd, [clearjob])
    # 2.运行me2自动化计划
    time.sleep(3)
    from manager.invoker import runplan
    for i in buildplans.split(','):
        planid = i[5:]
        try:
            plan = Plan.objects.get(id=planid)
            taskid = gettaskid(planid)
            print('开始执行计划【%s】' % plan.description)
            runplan(callername, taskid, planid, '1',planid)
        except:
            pass
    jobs=[]
    for job in jacocoConfig.jobname.split(";"):
        jobs.append(job.split(":")[0])
    jenkinsBuild(url, name, pwd, jobs)
    time.sleep(3 * 60)


def jenkinsBuild(jenkinsurl, name, pwd, jobs,parameters=None):
    server = jenkins.Jenkins(jenkinsurl, username=name, password=pwd)
    for job in jobs:
        if job != '':
            if parameters:
                server.build_job(job,parameters)
            else:
                server.build_job(job)