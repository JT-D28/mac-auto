import datetime
import json
import time
import traceback
import gitlab
import jenkins

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from homepage.models import Jenkins
from login.views import getbusinessnum
from manager.models import Order, Case, Step, BusinessData, Plan
from manager.operate.mongoUtil import Mongo
from numpy import *


@csrf_exempt
def HasJacoco(request):
	productid = request.POST.get('productid')
	try:
		service = []
		jacocoset = Jenkins.objects.values().get(productid=productid)
		
		jobnames = jacocoset['jobname']
		jobs = jobnames.split(";") if not jobnames.endswith(';') else jobnames.split(";")[:-1]
		for job in jobs:
			servicenames = job.split(":[")[1][:-1]
			for i, v in enumerate(servicenames.split(",")):
				service.append({'id': job.split(":[")[0] + ':::' + str(v), 'name': v})
		return JsonResponse({'has': '1', "service": service})
	except:
		return JsonResponse({'has': '0'})


@csrf_exempt
def HasGit(request):
	productid = request.POST.get('productid')
	try:
		service = []
		gitset = Jenkins.objects.get(productid=productid)
		if gitset.gitlaburl and gitset.gitlabtoken and gitset.gitpath:
			return JsonResponse({'hasGit': '1'})
		else:
			return JsonResponse({'hasGit': '0'})
	except:
		return JsonResponse({'hasGit': '0'})


@csrf_exempt
def queryCoveryInfo(request):
	productid = request.POST.get('productid')
	jacocoset = Jenkins.objects.get(productid=productid)
	jobmap = {}
	jobs = jacocoset.jobname
	for job in jobs.split(";"):
		if job:
			jobnum = len(jobs.split(";"))
			jobname = job.split(":")[0]
			jobmap[jobname] = ['all']
	coveragelist = ['classes', 'method', 'line', 'branch', 'instruction',
	                'complexity']
	items = ['covered', 'missed', 'percentage', 'percentagefloat', 'total']
	res = {}
	lastres = {}
	for i in coveragelist:
		res[i] = {'covered': 0, 'missed': 0, 'percentage': 0, 'percentagefloat': 0, 'total': 0}
		lastres[i] = {'covered': 0, 'missed': 0, 'percentage': 0, 'percentagefloat': 0, 'total': 0}
	maps = {}
	with connection.cursor() as cursor:
		for i in list(jobmap.keys()):
			print(i)
			sql = """
			SELECT  * from homepage_jacoco_data where jobname = %s Order by (jobnum+0) DESC LIMIT 2
			"""
			cursor.execute(sql, [i])
			desc = cursor.description
			maps[i] = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	for jobname, temp in maps.items():
		try:
			data = json.loads(temp[0]['coverydata'].replace("'", '"'))
			for j in jobmap[jobname]:
				jsond = data[j]
				for m in coveragelist:
					for k in items:
						if k in ['percentage', 'percentagefloat']:
							jsond[m][k] = round(res[m][k] + jsond[m][k] / jobnum, 2)
						else:
							jsond[m][k] = res[m][k] + jsond[m][k]
				res = jsond.copy()
		except:
			pass
		try:
			data1 = json.loads(temp[1]['coverydata'].replace("'", '"'))
			for j in jobmap[jobname]:
				jsond1 = data1[j]
				for m in coveragelist:
					for k in items:
						if k in ['percentage', 'percentagefloat']:
							jsond1[m][k] = round(lastres[m][k] + jsond1[m][k] / jobnum, 2)
						else:
							jsond1[m][k] = lastres[m][k] + jsond1[m][k]
				lastres = jsond1.copy()
		except:
			pass
	timelist = [int(i[0]['time']) if i[0]['time'] not in [None, ''] else 0 for i in maps.values()]
	time = max(timelist)
	timelist = [int(i[1]['time']) if i[1]['time'] not in [None, ''] else 0 for i in maps.values()]
	oldtime = max(timelist)
	return JsonResponse({'res': res, 'lastres': lastres, 'time': strftime(time), 'oldtime': strftime(oldtime)})


@csrf_exempt
def queryGitCommit(request):
	productid = request.POST.get('productid')
	gitconfig = Jenkins.objects.get(productid=productid)
	info = []
	if gitconfig.gitlaburl:
		client = gitlab.Gitlab(gitconfig.gitlaburl, private_token=gitconfig.gitlabtoken, timeout=2, api_version='4')
		client.auth()
		starttime = datetime.datetime.utcfromtimestamp(int(request.POST.get('starttime')))
		endtime = datetime.datetime.utcfromtimestamp(int(request.POST.get('endtime')))
		for path in gitconfig.gitpath.split(";"):
			try:
				project = client.projects.get(path)
				commits = project.commits.list(
					query_parameters={'since': starttime, 'until': endtime, 'ref_name': gitconfig.gitbranch}, all=True)
				
				for c in commits:
					# commit = project.commits.get(c.id)
					# diff = commit.diff()
					# print(diff)
					info.append({"time": genTime(c.created_at[0:19]), "who": c.committer_name, "message": c.message})
			except:
				print(traceback.format_exc())
				pass
	return JsonResponse({'data': info})


@csrf_exempt
def queryJenkinsUpdatetimes(request):
	productid = request.POST.get('productid')
	starttime = int(request.POST.get('starttime'))
	endtime = int(request.POST.get('endtime'))
	
	jenkinsconfig = Jenkins.objects.get(productid=productid)
	authname, authpwd, jenkinsurl = jenkinsconfig.authname, jenkinsconfig.authname, jenkinsconfig.jenkinsurl
	server = jenkins.Jenkins(jenkinsurl, username=authname, password=authpwd)
	if jenkinsconfig.projectjob:
		for job in jenkinsconfig.projectjob.split(";"):
			pass
	planidlist = list(
		Order.objects.values_list('follow_id', flat=True).filter(main_id=productid, kind='product_plan', isdelete=0))
	jobcovertimes = 0
	aspend = []
	totalcount = 0
	for id in planidlist:
		timeSpent = 0
		query = {'planid': int(id), 'info.runkind': {'$in': ['1', '3']},
		         'timestamp': {'$lt': endtime, '$gt': starttime}}
		jobcovertimes += Mongo.taskinfo().find(query).count()
		ms = Mongo.taskinfo().find(query)
		for m in ms:
			print(m['info']['spend'] / 60)
			timeSpent += m['info']['spend'] / 60
		totalcount += ms.count()
		aspend.append(timeSpent * ms.count())
	averageTimeSpent = round(sum(aspend) / totalcount, 2)
	return JsonResponse({'jenkinsUpdatetimes': 1, 'jobcovertimes': jobcovertimes, 'averageTimeSpent': averageTimeSpent})


def strftime(timestamp, format_string='%Y-%m-%d %H:%M:%S'):
	return time.strftime(format_string, time.localtime(timestamp))


def genTime(timestr, format_string='%Y-%m-%d %H:%M:%S'):
	timestamp = time.mktime(time.strptime(timestr, '%Y-%m-%dT%H:%M:%S'))
	return time.strftime(format_string, time.localtime(timestamp))


def queryApiTestReportByTaskId(request):
	taskId = request.POST.get("taskId")
	planId = request.POST.get("planId")
	r = Mongo.taskResult().find_one({'planid':int(planId),"taskid":taskId},{"_id":0})
	return JsonResponse({"code": 0, "data":r})


def queryApiTaskRangeDate(request):
	planId = int(request.POST.get("planId"))
	startDate = int(request.POST.get("startDate"))
	endDate = int(request.POST.get("endDate"))
	runkind = [int(i) for i in request.POST.get("runkind", "").split(",") if i != ""]
	
	res = list(Mongo.taskResult().find(
		{'planid': planId, 'kind': {'$in': runkind}, "timestamp": {"$lt": endDate, "$gt": startDate}},
		{"_id": 0, "time": 1, "info": 1, "taskid": 1, "statistics": 1}).sort("_id", -1))
	return JsonResponse({"code": 0, "data": {"tasks": res, "total": len(res)}})


def deleteTask(request):
	taskid = request.POST.get("taskid")
	Mongo.taskRecords().delete_many({"taskid": taskid})
	Mongo.taskreport().delete_many({"taskid": taskid})
	Mongo.taskResult().delete_many({"taskid": taskid})
	Mongo.logsplit(taskid).drop()
	Mongo.tasklog(taskid).drop()
	return JsonResponse({"code": 0, "msg": "删除成功"})


@csrf_exempt
def get_task_data(request):
	taskid = request.POST.get('taskid')
	node = request.POST.get('node')
	x = Mongo.taskRecords().find_one({"taskid": taskid})
	result = Mongo.taskResult().find_one({"taskid": taskid})
	try:
		x = x["node"]
		casesdata = []
		if node:
			type, id = node.split("_")
			if type == 'plan':
				casesdata = x['root']
			elif type == 'business':
				stepid = Order.objects.get(follow_id=id, kind='step_business', isdelete=0).main_id
				tps = x['step_' + str(stepid)]
				for tp in tps:
					tpid = tp['id'].split("_")[1]
					if str(tpid) == str(id):
						casesdata = [tp]
						break
			else:
				casesdata = x[node]
		else:
			casesdata = x['root']
		if request.POST.get('viewkind') == 'fail':
			for i in range(len(casesdata) - 1, -1, -1):
				if casesdata[i].get('rate', 0) == 100.0 or casesdata[i].get('state', '') == 'omit':
					casesdata.pop(i)
	except:
		return JsonResponse(
			{'code': 1, 'info': "等待结果生成...", "statistics": result["statistics"], 'casesdata': []})
	return JsonResponse({'code': 0, 'info': result["info"], "statistics": result["statistics"], 'casesdata': casesdata})


@csrf_exempt
def getnodes(request):
	nodeid = request.POST.get('nodeid')
	kind = request.POST.get('kind')
	taskid = request.POST.get('taskid')
	try:
		key = "%s_%s"%(kind,nodeid)
		data =Mongo.taskRecords().find_one({"taskid": taskid})["node"][key]
		print(data)
		if request.POST.get('viewkind') == 'fail':
			for i in range(len(data) - 1, -1, -1):
				state = data[i].get('state', None)
				rate = data[i].get('rate', None)
				print(state, rate)
				if rate == 100.0:
					data.pop(i)
				elif state in ['omit', 'success']:
					data.pop(i)
	except:
		print(traceback.format_exc())
		data = []
	return JsonResponse({'code': 0, 'data': data})


@csrf_exempt
def getBusinessLog(request):
	id = request.POST.get('id')
	taskid = request.POST.get('taskid')
	type = request.POST.get('type')
	code = 0
	try:
		if type == "0":
			log = Mongo.logsplit(taskid).find_one({'path.businessid': int(id)})["result"]["details"]["log"]
		else:
			data = Mongo.logsplit(taskid).find_one({'path.businessid': int(id)})["result"]["details"]
			return JsonResponse({"code": code, "data": data})
	except:
		print(traceback.format_exc())
		info = "日志查找失败"
		code = 1
	return JsonResponse({'code': code, 'data': log})


def queryFailBusiness(request):
	taskid = request.POST.get('taskid')
	oldCount = request.POST.get('oldCount')
	if oldCount:
		res = Mongo.logsplit(taskid).find({'result.state': {"$in":["fail","error"]}},{"_id":0}).limit(10).skip(int(oldCount))
	else:
		res = Mongo.logsplit(taskid).find({'result.state': {"$in": ["fail", "error"]}}, {"_id": 0})
	return JsonResponse({'code': 0, 'data': list(res)})
	