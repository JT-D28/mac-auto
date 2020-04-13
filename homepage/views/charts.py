import json
import traceback
import time

import jenkins
import requests
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2 import configs
from homepage.models import Jacoco_report, Jacoco_data
from manager.core import simplejson
from manager.models import ResultDetail


@csrf_exempt
def reportchart(request):
	s = time.time()
	planid = request.POST.get("planid")
	code = 0
	taskids = list(ResultDetail.objects.values('taskid').filter(plan_id=planid, is_verify=1))
	if taskids:
		sql1 = '''
        SELECT x.plan_id,m.description,CONCAT(success),CONCAT(FAIL),CONCAT(skip),CONCAT(total),x.taskid,DATE_FORMAT(TIME,'%%m-%%d %%H:%%i') AS time,
        ROUND(CONCAT(success*100/total),1) ,CONCAT(error) FROM (
        SELECT DISTINCT manager_resultdetail.taskid,plan_id,is_verify FROM manager_resultdetail) AS x JOIN (
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
		
		sql = sql2 if configs.dbtype == 'sqlite3' else sql1
		
		with connection.cursor() as cursor:
			cursor.execute(sql, [planid])
			row = cursor.fetchall()
		e = time.time()
		print(e - s)
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
	jobs = request.POST.getlist('jobname[]')
	jobnames = []
	res = {}
	coveragelist = ['branchCoverage', 'classCoverage', 'complexityScore', 'instructionCoverage', 'lineCoverage',
	                'methodCoverage']
	items = ['covered', 'missed', 'percentage', 'percentageFloat', 'total']
	for i in coveragelist:
		res[i] = {'covered': 0, 'missed': 0, 'percentage': 0, 'percentageFloat': 0, 'total': 0}
	
	try:
		jacocoset = Jacoco_report.objects.get(productid=request.POST.get('productid'))
		authname, authpwd, jenkinsurl = jacocoset.authname, jacocoset.authname, jacocoset.jenkinsurl
		jobnames = dealJacocoJobName(jacocoset.jobname, jobs)
		jobnum = len(jobnames)
		if request.POST.get('s') == 'get':
			print('库中获取覆盖率')
			with connection.cursor() as cursor:
				cursor.execute('''SELECT branchCoverage,classCoverage,complexityScore,instructionCoverage,
				lineCoverage,methodCoverage from (SELECT max(jobnum) AS num,jobname FROM `homepage_jacoco_data` a
				GROUP BY jobname ) a , homepage_jacoco_data b where a.num = b.jobnum and a.jobname=b.jobname
				and a.jobname in %s
				''', [jobnames])
				desc = cursor.description
				rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
				print(rows)
			for jsond in rows:
				for i in coveragelist:
					jsond[i] = json.loads(jsond[i].replace("'", '"'))
					for k in items:
						if k in ['percentage', 'percentageFloat']:
							jsond[i][k] = round(res[i][k] + jsond[i][k] / jobnum, 2)
						else:
							jsond[i][k] = res[i][k] + jsond[i][k]
				res = jsond.copy()
		elif request.POST.get('s') == 'update':
			if len(authname) & len(authpwd) != 0:
				# 先判断下任务有没有在运行
				num = {}
				server = jenkins.Jenkins(jacocoset.jenkinsurl, username=jacocoset.authname, password=jacocoset.authpwd)
				for i, job in enumerate(jobnames):
					num[job] = server.get_job_info(job)['lastBuild']['number']
					buildinfo = server.get_build_info(job, num[job])
					if buildinfo['building']:
						msg += '%s:正在运行<br>' % (job)
					elif buildinfo['result'] != 'SUCCESS':
						msg += '%s:上次构建失败<br>' % (job)
				if msg != '':
					return JsonResponse(simplejson(code=1, msg=msg), safe=False)
				s = requests.session()
				s.auth = (authname, authpwd)
				for index, jobname in enumerate(jobnames):
					try:
						url = jenkinsurl + "/job/" + jobname + "/lastBuild/jacoco/api/python?pretty=true"
						jsond = json.loads(s.get(url).text)
						del jsond['_class']
						del jsond['previousResult']
						if not Jacoco_data.objects.filter(jobnum=num[jobname], jobname=jobname).exists():
							data = Jacoco_data()
							data.jobnum = num[jobname]
							data.jobname = jobname
							data.branchCoverage = jsond['branchCoverage']
							data.classCoverage = jsond['classCoverage']
							data.complexityScore = jsond['complexityScore']
							data.instructionCoverage = jsond['instructionCoverage']
							data.lineCoverage = jsond['lineCoverage']
							data.methodCoverage = jsond['methodCoverage']
							data.save()
							print('%s第%s次构建的覆盖率数据保存成功' % (jobname, num[jobname]))
						# threading.Thread(target=dealJacocoData, args=(jsond.copy(), jobname, num[jobname])).start()
						for i in coveragelist:
							for k in items:
								if k in ['percentage', 'percentageFloat']:
									jsond[i][k] = round(res[i][k] + jsond[i][k] / jobnum, 2)
								else:
									jsond[i][k] = res[i][k] + jsond[i][k]
						res = jsond.copy()
					except:
						print(traceback.format_exc())
						code = 1
						msg = '查询异常'
	except:
		print(traceback.format_exc())
		return JsonResponse(simplejson(code=2, msg='没有进行代码覆盖率配置', data=res), safe=False)
	return JsonResponse(simplejson(code=code, msg=msg, data=res), safe=False)


def dealJacocoJobName(jacocojobname, jobs):
	jobnames = []
	if '0' in jobs:
		jobs = jacocojobname.split(";")[:-1] if jacocojobname.endswith(";") else jacocojobname.split(";")
		for i in jobs:
			jobnames.append(i.split(":")[1])
	else:
		jobnames = [x for x in jobs]
	return jobnames


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
