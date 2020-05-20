from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2 import settings
from manager.context import getRunningInfo
from manager.core import simplejson, EncryptUtils
from manager.models import ResultDetail, Plan


@csrf_exempt
def querytaskid(request):  # 查询验证任务最新id
	code = 0
	msg = ''
	# taskids = []
	is_running = ''
	username = request.session.get("username")
	action = request.POST.get('action')

	if action == 'plan':
		planid = request.POST.get('planid')
		taskid = getRunningInfo(username, planid, 'verify_taskid')
		is_running= getRunningInfo(username, planid, 'isrunning')
	elif action == 'lastest':
		taskid = getRunningInfo(username, '', 'lastest_taskid')
		print("控制台获取的最新taskid", taskid)
	
	# if taskid is None:
	# 	print('内存中查找不到taskid，从数据库中找')
	# 	try:
	# 		if action == 'lastest':
	# 			sql = '''SELECT taskid FROM `manager_resultdetail` order by createtime desc LIMIT 1'''
	# 			with connection.cursor() as cursor:
	# 				cursor.execute(sql)
	# 				row = cursor.fetchone()
	# 				taskid = row[0]
	# 		elif action == 'plan':
	# 			planid = request.POST.get('planid')
	# 			plan = Plan.objects.get(id=planid)
	# 			is_running = plan.is_running
	# 			print('3333333',is_running)
	# 			taskids = list(
	# 				ResultDetail.objects.values('taskid').filter(plan=plan, is_verify=1).order_by('-createtime'))
	# 			if taskids:
	# 				taskid = taskids[0]["taskid"]
	# 			else:
	# 				code = 1
	# 				msg = "任务还没有运行过！"
	# 	except:
	# 		code = 1
	# 		msg = "出错了！"
	return JsonResponse(simplejson(code=code, msg=msg, data=taskid, is_running=is_running), safe=False)


@csrf_exempt
def query_third_call(request):
	me2url = request.get_raw_uri().replace(request.path,'')
	planid = request.POST.get('planid')
	dbscheme = request.POST.get('dbscheme')
	callername = Plan.objects.get(id=planid).author.name
	mwstr = 'callername=%s&taskid=%s' % (callername, planid)
	is_verify_url = '%s/manager/third_party_call/?v=%s&is_verify=%s&planid=%s&scheme=%s' % (
		me2url, EncryptUtils.base64_encrypt(EncryptUtils.des_encrypt(mwstr)), 1, planid, dbscheme)
	debug_url = '%s/manager/third_party_call/?v=%s&is_verify=%s&planid=%s&scheme=%s' % (
		settings.BASE_URL, EncryptUtils.base64_encrypt(EncryptUtils.des_encrypt(mwstr)), 0, planid, dbscheme)
	return JsonResponse({'is_verify_url': is_verify_url, 'debug_url': debug_url})


@csrf_exempt
def gettaskidplan(request):
	planid= request.POST.get('planid')
	print(planid)
	with connection.cursor() as cursor:
		cursor.execute('''SELECT min(DATE_FORMAT(r.createtime,'%%m-%%d %%H:%%i')) AS time,taskid
		FROM manager_resultdetail r where plan_id=%s GROUP BY taskid ORDER BY time DESC LIMIT 10''',[planid])
		desc = cursor.description
		rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	return JsonResponse({'code':0,'taskids':rows})
