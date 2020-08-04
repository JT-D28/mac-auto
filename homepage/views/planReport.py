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

from homepage.Gitlab import GitlabAPI
from homepage.models import Jenkins
from manager.models import Order, Case, Step, BusinessData, Plan
from manager.operate.mongoUtil import Mongo
from numpy import *

def planreport(request):
	return render(request, 'planreport.html')


@csrf_exempt
def planrunnum(request):
	planid = request.POST.get('id')
	# 当前周期
	starttime = int(request.POST.get('starttime'))
	endtime = int(request.POST.get('endtime'))

	# 上一个周期起始时间
	laststarttime = 2 * starttime - endtime - 1
	lastendtime = starttime - 1
	# print(strftime(laststarttime), strftime(lastendtime), strftime(starttime), strftime(endtime))

	currentRunNum = Mongo.taskinfo().find({'planid': int(planid), 'timestamp': {'$lt': endtime, '$gt': starttime}}).count()
	lastRunNum = Mongo.taskinfo().find({'planid': int(planid), 'timestamp': {'$lt': lastendtime, '$gt': laststarttime}}).count()

	return JsonResponse({'code': 0, 'currentRunNum': currentRunNum, 'lastRunNum': lastRunNum})


@csrf_exempt
def planpassrate(request):
	planid = request.POST.get('id')
	starttime = int(request.POST.get('starttime'))
	endtime = int(request.POST.get('endtime'))

	# 上一个周期起始时间
	laststarttime = 2 * starttime - endtime - 1
	lastendtime = starttime - 1

	currentinfo = Mongo.taskinfo().find({'planid': int(planid), 'timestamp': {'$lt': endtime, '$gt': starttime}},{'info.rate':1,'_id':0})
	lastinfo = Mongo.taskinfo().find({'planid': int(planid), 'timestamp': {'$lt': lastendtime, '$gt': laststarttime}},{'info.rate': 1, '_id': 0})

	currentrate =[]
	lastrate = []
	for i in currentinfo:
		rate = i['info']['rate']
		currentrate.append(rate)
	for i in lastinfo:
		rate = i['info']['rate']
		lastrate.append(rate)
	lastPassRate = round(mean(lastrate),2)  if lastrate else 0
	currentPassRate = round(mean(currentrate),2) if currentrate else 0

	return JsonResponse({'code': 0, 'currentPassRate': currentPassRate, 'lastPassRate': lastPassRate})


@csrf_exempt
def planRunChart(request):
	planid = request.POST.get('id')
	starttime = int(request.POST.get('starttime'))
	endtime = int(request.POST.get('endtime'))
	info = list(Mongo.taskinfo().find({'planid': int(planid), 'timestamp': {'$lt': endtime, '$gt': starttime}},
	                                  {'info': 1, '_id': 0, 'time': 1}).sort('timestamp').limit(10))
	infolist = []
	for i in info:
		x = i['info']
		x['time'] = i.get('time', '')
		infolist.append(x)
	return JsonResponse({'info': infolist})

@csrf_exempt
def planBusinessNum(request):
	planid = request.POST.get('id')
	currentBusinessNum = 0
	currentRunBusiness = 0
	getbusinessnum(planid,currentBusinessNum,currentRunBusiness)

	return JsonResponse({'currentBusinessNum': currentBusinessNum,'currentRunBusiness':currentRunBusiness})

@csrf_exempt
def HasJacoco(request):
	productid = request.POST.get('productid')
	try:
		service=[]
		jacocoset = Jenkins.objects.values().get(productid=productid)

		jobnames = jacocoset['jobname']
		jobs = jobnames.split(";") if not jobnames.endswith(';') else jobnames.split(";")[:-1]
		for job in jobs:
			servicenames = job.split(":[")[1][:-1]
			for i,v in enumerate(servicenames.split(",")):
				service.append({'id': job.split(":[")[0]+':::'+str(v),'name': v})
		return JsonResponse({'has': '1',"service":service})
	except:
		return JsonResponse({'has':'0'})

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
		lastres[i] =  {'covered': 0, 'missed': 0, 'percentage': 0, 'percentagefloat': 0, 'total': 0}
	maps ={}
	with connection.cursor() as cursor:
		for i in list(jobmap.keys()):
			print(i)
			sql = """
			SELECT  * from homepage_jacoco_data where jobname = %s Order by (jobnum+0) DESC LIMIT 2
			"""
			cursor.execute(sql,[i])
			desc = cursor.description
			maps[i] = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	print(maps)
	for jobname,temp in maps.items():
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
	timelist = [int(i[0]['time']) if i[0]['time'] not in [None,''] else 0 for i in maps.values()]
	time = max(timelist)
	timelist = [int(i[1]['time']) if i[1]['time'] not in [None,''] else 0 for i in maps.values()]
	oldtime = max(timelist)
	return JsonResponse({'res': res, 'lastres': lastres,'time':strftime(time),'oldtime':strftime(oldtime)})




@csrf_exempt
def queryGitCommit(request):
	productid = request.POST.get('productid')
	gitconfig = Jenkins.objects.get(productid=productid)
	info = []
	if gitconfig.gitlaburl:
		client = gitlab.Gitlab(gitconfig.gitlaburl,private_token=gitconfig.gitlabtoken,timeout = 2, api_version = '4')
		client.auth()
		starttime = datetime.datetime.utcfromtimestamp(int(request.POST.get('starttime')))
		endtime = datetime.datetime.utcfromtimestamp(int(request.POST.get('endtime')))
		for path in gitconfig.gitpath.split(";"):
			try:
				project = client.projects.get(path)
				commits = project.commits.list(query_parameters={'since':starttime,'until':endtime,'ref_name':gitconfig.gitbranch},all=True)

				for c in commits:
					# commit = project.commits.get(c.id)
					# diff = commit.diff()
					# print(diff)
					info.append({"time":genTime(c.created_at[0:19]),"who":c.committer_name,"message":c.message})
			except:
				print(traceback.format_exc())
				pass
	return JsonResponse({'data': info})


@csrf_exempt
def queryJenkinsUpdatetimes(request):
	productid = request.POST.get('productid')
	jenkinsconfig = Jenkins.objects.get(productid=productid)
	authname, authpwd, jenkinsurl = jenkinsconfig.authname, jenkinsconfig.authname, jenkinsconfig.jenkinsurl
	server = jenkins.Jenkins(jenkinsurl, username=authname, password=authpwd)
	if jenkinsconfig.projectjob:
		for job in jenkinsconfig.projectjob.split(";"):
			pass
	return JsonResponse({'data': 1})





def strftime(timestamp, format_string='%Y-%m-%d %H:%M:%S'):
	return time.strftime(format_string, time.localtime(timestamp))


def genTime(timestr, format_string='%Y-%m-%d %H:%M:%S'):
	timestamp = time.mktime(time.strptime(timestr, '%Y-%m-%dT%H:%M:%S'))
	return time.strftime(format_string, time.localtime(timestamp))
