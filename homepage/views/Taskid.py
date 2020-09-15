from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from manager.operate.mongoUtil import Mongo
from ME2 import settings
from manager.context import getRunningInfo
from manager.core import simplejson, EncryptUtils
from manager.models import ResultDetail, Plan


@csrf_exempt
def querytaskid(request):  # 查询验证任务最新id
	code = 0
	msg = ''
	is_running = ''
	username = request.session.get("username")
	action = request.POST.get('action')

	if action == 'plan':
		planid = request.POST.get('planid')
		taskid = getRunningInfo(planid, 'verify_taskid')
		is_running= getRunningInfo(planid, 'isrunning')
		print(taskid,is_running)
	elif action == 'lastest':
		taskid = request.session.get('console_taskid','')
		print("控制台获取的最新taskid", taskid)
	return JsonResponse(simplejson(code=code, msg=msg, data=taskid, is_running=is_running), safe=False)


@csrf_exempt
def query_third_call(request):
	planid = request.POST.get('planid')
	dbscheme = request.POST.get('dbscheme')
	is_verify_url = '%s/manager/third_party_call/?is_verify=%s&planid=%s&scheme=%s' % (
		settings.BASE_URL, 1, planid, dbscheme)
	debug_url = '%s/manager/third_party_call/?is_verify=%s&planid=%s&scheme=%s' % (
		settings.BASE_URL,0, planid, dbscheme)
	return JsonResponse({'is_verify_url': is_verify_url, 'debug_url': debug_url})


@csrf_exempt
def gettaskidplan(request):
	planid= request.POST.get('planid')
	runkind = request.POST.getlist('runkind[]')
	if not runkind:
		runkind = request.POST.get('runkind').split(',')
	res = list(Mongo.taskinfo().find({'planid':int(planid),'info.runkind': {'$in':runkind}},{'time':1,'taskid':1,'_id':0}).sort('timestamp',-1).limit(10))
	return JsonResponse({'code':0,'taskids':res})
