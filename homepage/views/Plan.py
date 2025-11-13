import json
import traceback

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import time
from ME2 import configs
from homepage.models import Jenkins
from manager.models import Order,Plan
from manager.cm import getchild
from manager.context import getRunningInfo, setRunningInfo
from manager.core import simplejson
from manager.models import Plan


@csrf_exempt
def queryplanlist(request):
	productid = request.POST.get('id')

	planidlist = Order.objects.values_list('follow_id',flat=True).filter(kind='product_plan',main_id=productid,isdelete=0).extra(
		select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
	planlist = []
	for planid in planidlist:
		try:
			description = Plan.objects.get(id=planid).description
			planlist.append({
				'id': str(planid),
				'name': description,
			})
		except:
			pass
	return JsonResponse({'code': 0, 'data': planlist})

@csrf_exempt
def queryallplan(request):
	if configs.dbtype == 'mysql':
		sql = '''SELECT plan.id,CONCAT(pro.description,'-',plan.description) as planname
		FROM `manager_plan` plan,manager_product pro,manager_order o WHERE pro.id=o.main_id AND plan.id=o.follow_id and kind='product_plan' and plan.isdelete=0  order by pro.id'''
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
	
	# sql = '''
    # SELECT COUNT(DISTINCT taskid) as 'total',sum(CASE WHEN r.result='success' THEN 1 ELSE 0 END) AS '成功数' ,count(*) as '总数'
    # FROM manager_resultdetail r WHERE r.plan_id IN (SELECT follow_id FROM manager_order WHERE main_id=%s)
    # AND r.result NOT IN ('omit') AND r.is_verify in (1,3)
    # '''
	# with connection.cursor() as cursor:
	# 	cursor.execute(sql, [pid])
	# 	desc = cursor.description
	# 	rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	# success_rate = rows[0]['成功数'] / rows[0]['总数'] * 100 if rows[0]['总数'] != 0 else 0
	# total = rows[0]['total'] if rows[0]['total'] is not None else 0
	
	
	
	
	jacocoset = Jenkins.objects.values().filter(productid=pid) if pid != '' else None
	service = [{'id': 0, 'name': '总计'}]
	if jacocoset:
		try:
			jobnames = jacocoset[0]['jobname']
			jobs = jobnames.split(";") if not jobnames.endswith(';') else jobnames.split(";")[:-1]
			for job in jobs:
				servicenames = job.split(":[")[1][:-1]
				for i,v in enumerate(servicenames.split(",")):
					service.append({'id': job.split(":[")[0]+':::'+str(v),'name': v})
		except:
			print(traceback.format_exc())
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
			simplejson(code=0, msg='操作成功', data=datanode, service=service),
			safe=False)
	except:
		print(traceback.format_exc())
		code = 4
		msg = '查询数据库列表信息异常'
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)
	
	
@csrf_exempt
def queryPlanState(request):
	planid = request.POST.get('id')
	if planid.startswith('plan_'):
		planid = request.POST.get('id')[5:]
	type = request.POST.get('type')
	if type:
		fl = getRunningInfo(planid, 'isrunning')
		taskid = getRunningInfo(planid, 'debug_taskid')
		return JsonResponse({'running': fl,'taskid':taskid})
	runkind = getRunningInfo(planid,'isrunning')
	msg = {0:"未运行",1: "验证", 2: "调试", 3: "定时"}[runkind]
	return JsonResponse({'data': msg})


@csrf_exempt
def planforceStop(request):
	planid = request.POST.get('id')[5:]
	try:
		setRunningInfo(planid,'','0')
		code = 0
		msg = 'success'
	except:
		code = 1
		msg = 'stop_error'
	return JsonResponse({'code': code, 'msg': msg})
