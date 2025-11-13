import json
import traceback
import time

import jenkins
import requests
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2 import configs
from homepage.models import Jenkins, Jacoco_data
from manager.core import simplejson
from manager.models import ResultDetail
from manager.operate.mongoUtil import Mongo


@csrf_exempt
def reportchart(request):
	planid = request.POST.get("planid")
	res = list(Mongo.taskResult().find({'planid': int(planid), 'kind': {'$in': [1, 3]}},
	                                 {'time': 1, 'taskid': 1, 'statistics': 1, '_id': 0}).sort('timestamp', -1).limit(12))
	chartList = []
	for r in res:
		info = r.get("statistics")
		chartList.append(
			[info["success"], info["fail"], info["skip"], info["error"], info["total"], r["time"],
			 info["successrate"], r["taskid"]])
	
	pipeline = [
		{'$match': {'planid': int(planid), 'kind': {'$in': [1, 3]}}},
		{'$group': {'_id': "$planid", "rate": {"$avg": "$statistics.successrate"}, "total": {"$sum": 1}}}
	]
	planAggregate = list(Mongo.taskResult().aggregate(pipeline))
	print(planAggregate)
	if len(planAggregate) == 0:
		total = 0
		rate = 0
	else:
		total = planAggregate[0]["total"]
		rate = round(planAggregate[0]["rate"], 2)
	return JsonResponse({"code": 0, "data": chartList, "total": total, "rate": rate})


@csrf_exempt
def jacocoreport(request):
	code, msg = 0, ''
	try:
		jacocoset = Jenkins.objects.get(productid=request.POST.get('productid'))
	except:
		return JsonResponse({'code': 1, 'msg': '没有配置'})
	jobs = request.POST.getlist('jobname[]')
	if not jobs:
		jobs = request.POST.get('jobname').split(',')
	jobmap = {}
	if jobs != ['0']:
		jobnum = len(jobs)
		for i in jobs:
			jobname, servicename = i.split(":::")
			if not jobmap.get(jobname, []):
				jobmap[jobname] = []
			jobmap[jobname].append(servicename)
	else:
		jobs = jacocoset.jobname
		jobnum = len(jobs.split(";"))
		for job in jobs.split(";"):
			if job:
				jobname = job.split(":")[0]
				jobmap[jobname] = ['all']
	jobnames = []
	res = {}
	
	coveragelist = ['classes', 'method', 'line', 'branch', 'instruction',
	                'complexity']
	items = ['covered', 'missed', 'percentage', 'percentagefloat', 'total']
	for i in coveragelist:
		res[i] = {'covered': 0, 'missed': 0, 'percentage': 0, 'percentagefloat': 0, 'total': 0}
	
	try:
		authname, authpwd, jenkinsurl = jacocoset.authname, jacocoset.authname, jacocoset.jenkinsurl
		jobnames = jacocoset.jobname.split(";")
		if request.POST.get('s') == 'get':
			print('库中获取覆盖率')
			with connection.cursor() as cursor:
				cursor.execute('''SELECT a.jobname,coverydata from (SELECT max(jobnum+0) AS num,jobname FROM `homepage_jacoco_data` a
				GROUP BY jobname ) a , homepage_jacoco_data b where a.num = b.jobnum and a.jobname=b.jobname
				and a.jobname in %s
				''', [list(jobmap.keys())])
				desc = cursor.description
				rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
			for i in rows:
				print(i)
				data = json.loads(i['coverydata'].replace("'", '"'))
				for j in jobmap[i['jobname']]:
					jsond = data[j]
					for m in coveragelist:
						for k in items:
							if k in ['percentage', 'percentagefloat']:
								jsond[m][k] = round(res[m][k] + jsond[m][k] / jobnum, 2)
							else:
								jsond[m][k] = res[m][k] + jsond[m][k]
					res = jsond.copy()
		elif request.POST.get('s') == 'update':
			print(jobmap)
			if len(authname) & len(authpwd) != 0:
				# 先判断下任务有没有在运行
				num = {}
				timemap = {}
				server = jenkins.Jenkins(jacocoset.jenkinsurl, username=jacocoset.authname, password=jacocoset.authpwd)
				for jobname in jobmap.keys():
					num[jobname] = server.get_job_info(jobname)['lastBuild']['number']
					buildinfo = server.get_build_info(jobname, num[jobname])
					if buildinfo['building']:
						msg += '%s:正在运行<br>' % (jobname)
					elif buildinfo['result'] != 'SUCCESS':
						msg += '%s:上次构建失败<br>' % (jobname)
					timemap[jobname] = buildinfo['timestamp']
				if msg != '':
					return JsonResponse(simplejson(code=1, msg=msg), safe=False)
				s = requests.session()
				s.auth = (authname, authpwd)
				for jobname, servicenames in jobmap.items():
					try:
						url = jenkinsurl + "/job/" + jobname + "/jacoco/json?all"
						jsonres = json.loads(s.get(url).text)
						if not Jacoco_data.objects.filter(jobnum=num[jobname], jobname=jobname).exists():
							data = Jacoco_data()
							data.jobnum = num[jobname]
							data.jobname = jobname
							data.coverydata = jsonres
							data.time = int(timemap[jobname] / 1000)
							data.save()
							print('%s第%s次构建的覆盖率数据保存成功' % (jobname, num[jobname]))
						for l in servicenames:
							jsond = jsonres[l]
							for i in coveragelist:
								for k in items:
									if k in ['percentage', 'percentagefloat']:
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
    in ('error','fail') and r.is_verify in (1,3) and r.step_id=s.id GROUP BY s.url order by 次数 desc limit 10
    '''
	with connection.cursor() as cursor:
		cursor.execute(sql, [productid])
		desc = cursor.description
		rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	return JsonResponse({"code": 0, "data": 13})
