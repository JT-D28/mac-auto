import traceback

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2 import configs
from homepage.models import Jacoco_report
from manager.cm import getchild
from manager.context import getRunningInfo, setRunningInfo
from manager.core import simplejson
from manager.models import Plan


@csrf_exempt
def queryallplan(request):
	if configs.dbtype == 'mysql':
		sql = '''SELECT plan.id,CONCAT(pro.description,'-',plan.description) as planname
		FROM `manager_plan` plan,manager_product pro,manager_order o WHERE pro.id=o.main_id AND plan.id=o.follow_id order by pro.id'''
	else:
		sql = '''SELECT plan.id, pro.description||'-'||plan.description as planname  FROM `manager_plan` plan,manager_product pro,manager_order o WHERE pro.id=o.main_id AND plan.id=o.follow_id order by pro.id   '''
	
	with connection.cursor() as cursor:
		cursor.execute(sql)
		desc = cursor.description
		rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	return JsonResponse({'code': 0, 'data': rows})


@csrf_exempt
def queryplan(request):
	code, msg = 0, ''
	pid = request.POST.get('id')
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
	
	jacocoset = Jacoco_report.objects.values().filter(productid=pid) if pid != '' else None
	service = [{'id': 0, 'name': '总计'}]
	if jacocoset:
		try:
			jobnames = jacocoset[0]['jobname']
			jobs = jobnames.split(";") if not jobnames.endswith(';') else jobnames.split(";")[:-1]
			for job in jobs:
				service.append({
					'id': job.split(":")[1],
					'name': job.split(":")[0]
				})
		except:
			pass
	datanode = []
	try:
		plans = getchild('product_plan', pid)
		for plan in plans:
			datanode.append({
				'id': 'plan_%s' % plan.id,
				'name': '%s' % plan.description,
			})
		return JsonResponse(
			simplejson(code=0, msg='操作成功', data=datanode, rate=str(success_rate)[0:5], total=total, service=service),
			safe=False)
	except:
		print(traceback.format_exc())
		code = 4
		msg = '查询数据库列表信息异常'
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)
	
	
@csrf_exempt
def queryPlanState(request):
	planid = request.POST.get('id')[5:]
	# if request.POST.get('refresh'):
	# 	while 1:
	# 		is_running = getRunningInfo('',planid,'isrunning')
	# 		if is_running in (0, '0'):
	# 			return JsonResponse({'data': 1})
	is_running = getRunningInfo('',planid,'isrunning')
	return JsonResponse({'data': is_running})


@csrf_exempt
def planforceStop(request):
	planid = request.POST.get('id')[5:]
	try:
		setRunningInfo(request.session.get("username"), planid, getRunningInfo('', planid, 'isrunning'), 0)
		code = 0
		msg = 'success'
	except:
		code = 1
		msg = 'stop_error'
	return JsonResponse({'code': code, 'msg': msg})
