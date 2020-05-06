import json
import os
import re
import time
from random import random

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from ME2.settings import BASE_DIR
from manager import cm
from manager.models import ResultDetail, Case, Order, BusinessData, Plan, F, Step

from manager.invoker import gettaskresult
from django.views.decorators.csrf import csrf_exempt
from manager.context import Me2Log as logger


def statisticalAnalysis(request):
	return render(request, 'analysis.html', locals())


@csrf_exempt
def getplandata(request):
	planid = request.POST.get('planid')
	taskid = request.POST.get('taskid')
	orders = Order.objects.filter(kind='plan_case', main_id=planid)
	casesdata = []
	logname = BASE_DIR + "/logs/taskinfo/" + taskid + ".log"
	with open(logname, 'r', encoding='utf-8') as f:
		x = json.load(f)
		casesdata = x['root']
	# for order in orders:
	# 	case = Case.objects.get(id=order.follow_id)
	# 	num, successnum = get_business_num(order.follow_id, taskid=taskid)
	# 	casesdata.append(
	# 		{'id': case.id, 'name': case.description, 'hasChildren': 'true',
	# 		 'case_success_rate': round(successnum * 100 / num, 2),
	# 		 'success': successnum,
	# 		 'total': num, 'type': 'case', 'icon': 'el-icon-s-release'})
	
	return JsonResponse({'code': 0, 'casesdata': casesdata})



@csrf_exempt
def getnodes(request):
	kind = request.POST.get('kind')
	id = request.POST.get('nodeid')
	taskid = request.POST.get('taskid')
	logname = BASE_DIR + "/logs/taskinfo/" + taskid + ".log"
	with open(logname, 'r', encoding='utf-8') as f:
		x = json.load(f)
		data = x[kind+'_'+id]

	print(data)
	return JsonResponse({'code': 0, 'data': data})



@csrf_exempt
def geterrorinfo(request):
	id = request.POST.get('id')
	state = request.POST.get('state')
	taskid = request.POST.get('taskid')
	bname = request.POST.get('name')
	logname = BASE_DIR + "/logs/deal/" + taskid + ".log"
	stepid = Order.objects.get(follow_id=id,kind__contains='step_business').main_id
	stepname = Step.objects.get(id=stepid).description
	if os.path.exists(logname):
		with open(logname, 'r', encoding='utf-8') as f:
			res = f.read()
		ress = res.split("========")
		pattern = re.compile('开始执行步骤.*?' + stepname + '.*?测试点\[.*?' + bname + '.*?<br>')
		pattern1 = re.compile('步骤执行结果.*?{}'.format(state))
		res = '未匹配到日志记录，你可以试试下载并且查看完整日志！' if state!='skip' else '该测试点被跳过'
		for i in ress:
			if pattern.search(i) and pattern1.search(i):
				res = i
				break
	else:
		res = '日志可能还没处理完成，请稍等！'
	return JsonResponse({'code':0,'data':res})
#
# @csrf_exempt
# def getnodes(request):
# 	data = []
# 	kind = request.POST.get('kind')
# 	id = request.POST.get('nodeid')
# 	taskid = request.POST.get('taskid')
# 	if kind == 'case':
# 		orders = Order.objects.filter(main_id=id, kind__contains='case_').extra(
# 			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
# 		for order in orders:
# 			kind = order.kind
# 			if kind == 'case_case':
# 				case = Case.objects.get(id=order.follow_id)
# 				num, successnum = get_business_num(order.follow_id, taskid=taskid)
# 				data.append(
# 					{'id': case.id, 'name': case.description, 'hasChildren': True,
# 					 'case_success_rate': round(successnum * 100 / num, 2),
# 					 'success': successnum,
# 					 'total': num, 'type': 'case', 'icon': 'el-icon-s-release'})
# 			elif kind == 'case_step':
# 				step = Step.objects.get(id=order.follow_id)
# 				bnum = Order.objects.filter(main_id=order.follow_id, kind__contains='step_business').count()
#
# 				getsuccess = '''SELECT count(DISTINCT businessdata_id) FROM `manager_resultdetail` where taskid=%s and result='success'  and step_id=%s '''
# 				with connection.cursor() as cursor:
# 					cursor.execute(getsuccess, [taskid, order.follow_id])
# 					successnum = cursor.fetchone()[0]
# 				case_success_rate = round(successnum * 100 / bnum, 2) if bnum!=0 else 0
# 				data.append(
# 					{'id': step.id, 'name': step.description, 'hasChildren': True,
# 					 'case_success_rate': case_success_rate,
# 					 'success': successnum,
# 					 'total': bnum, 'type': 'step', 'icon': 'el-icon-s-check'})
# 	elif kind == 'step':
# 		orders = Order.objects.filter(main_id=id, kind__contains='step_business').extra(
# 			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
# 		for order in orders:
# 			businessdata = BusinessData.objects.get(id=order.follow_id)
# 			print('3：：：',order.follow_id)
# 			state = ResultDetail.objects.filter(taskid=taskid,businessdata_id=order.follow_id)[0].result
# 			data.append(
# 				{'id': businessdata.id, 'name': businessdata.businessname, 'hasChildren': False, 'type': 'business',
# 				 'icon': 'el-icon-info', 'state': state})
# 		print(data)
# 	return JsonResponse({'code': 0, 'data': data})
#
#
# def get_business_num(id, taskid='', num=0, successnum=0):
# 	orders = Order.objects.filter(main_id=id, kind__contains='case_')
# 	for o in orders:
# 		kind = o.kind
# 		if kind == 'case_step':
# 			os = Order.objects.filter(main_id=o.follow_id, kind__contains='step_business')
# 			getsuccess = '''SELECT count(DISTINCT businessdata_id) FROM `manager_resultdetail` where taskid=%s and result='success'  and businessdata_id=%s '''
# 			for o in os:
# 				with connection.cursor() as cursor:
# 					cursor.execute(getsuccess, [taskid, o.follow_id])
# 					successnum += cursor.fetchone()[0]
# 			num += os.count()
# 		elif kind == 'case_case':
# 			num, successnum = get_business_num(o.follow_id, taskid, num, successnum)
# 	return num, successnum


@csrf_exempt
def getReportBytaskid(request):
	taskid = ResultDetail.objects.values('taskid').distinct().order_by('-createtime')[0:10]
	data = gettaskresult(taskid[0]['taskid'])
	return JsonResponse({'code': 0, 'data': data})


def gettaskresult(taskid):
	bset = set()
	bmap = {}
	detail = {}
	spend_total = 0
	res = ResultDetail.objects.filter(taskid=taskid).order_by('createtime')
	plan = list(res)[0].plan
	time = list(res)[0].createtime.strftime("%m-%d %H:%M")
	detail = {
		'planname': plan.description,
		'taskid': taskid,
		'time': time,
		'cases': [],
		'success': 0,
		'fail': 0,
		'skip': 0,
		'error': 0,
		'min': 99999,
		'max': 0,
		'average': 0
	}
	
	caseids_temp = [r.case.id for r in res]
	caseids = list(set(caseids_temp))
	caseids.sort(key=caseids_temp.index)
	cases = [Case.objects.get(id=caseid) for caseid in caseids]
	
	for case in cases:
		caseobj = {}
		caseobj['casename'] = _get_full_case_name(case.id, case.description)
		if caseobj.get("steps", None) is None:
			caseobj['steps'] = {}
		
		step_query = list(ResultDetail.objects.filter(taskid=taskid, case=case))
		
		for x in step_query:
			business = x.businessdata
			status, step = BusinessData.gettestdatastep(business.id)
			if isinstance(step, (str,)): continue;
			step_weight = Order.objects.get(main_id=case.id, follow_id=step.id, kind='case_step').value
			business_index = \
				Order.objects.get(main_id=step.id, follow_id=business.id, kind='step_business').value.split('.')[1]
			businessobj = {'num': '%s_%s' % (step_weight, business_index)}
			stepname = business.businessname
			result = x.result
			if 'omit' != result:
				if 'success' == result:
					detail['success'] = detail['success'] + 1
				elif 'fail' == result:
					detail['fail'] = detail['fail'] + 1
				elif 'skip' == result:
					detail['skip'] = detail['skip'] + 1
				elif 'error' == result:
					detail['error'] = detail['error'] + 1
				error = x.error
				businessobj['businessname'] = x.businessdata.businessname
				businessobj['result'] = result
				businessobj['error'] = error
				stepinst = None
				error, stepinst = BusinessData.gettestdatastep(business.id)
				if stepinst.url:
					businessobj['stepname'] = stepinst.description
					matcher = [a for a in stepinst.url.split('/') if
					           not a.__contains__("{{") and not a.__contains__(':')]
					api = '/'.join(matcher)
					if not api.startswith('/'):
						api = '/' + api
					businessobj['api'] = api
				else:
					businessobj['stepname'] = stepinst.description
					businessobj['api'] = stepinst.body.strip()
				
				businessobj['itf_check'] = business.itf_check
				businessobj['db_check'] = business.db_check
				businessobj['spend'] = x.spend
				spend_total += int(businessobj['spend'])
				if int(businessobj['spend']) <= int(detail['min']):
					detail['min'] = businessobj['spend']
				
				if int(businessobj['spend']) > int(detail['max']):
					detail['max'] = businessobj['spend']
				
				if x.businessdata.id in bset:
					bcount = bmap.get(str(x.businessdata.id), 0)
					bcount = bcount + 1
					bmap[str(x.businessdata.id)] = bcount
					L = caseobj.get('steps').get(str(bcount), [])
					L.append(businessobj)
					caseobj['steps'][str(bcount)] = L
				else:
					bset.add(x.businessdata.id)
					bcount = bmap.get(str(x.businessdata.id), 0)
					bcount = bcount + 1
					bmap[str(x.businessdata.id)] = bcount
					L = caseobj.get('steps').get(str(bcount), [])
					L.append(businessobj)
					caseobj['steps'][str(bcount)] = L
		detail.get("cases").append(caseobj)
	detail['total'] = detail['success'] + detail['fail'] + detail['skip'] + detail['error']
	if detail['success'] == detail['total']:
		detail['result'] = 'success'
	else:
		detail['result'] = 'fail'
	try:
		detail['average'] = int(spend_total / detail['total'])
	except:
		detail['average'] = '-1'
	try:
		detail['success_rate'] = str("%.2f" % (detail['success'] / detail['total']))
	except:
		detail['success_rate'] = '-1'
	return detail


def _get_full_case_name(case_id, curent_case_name):
	case0 = Case.objects.get(id=case_id)
	# fullname=case0.description
	olist = list(Order.objects.filter(follow_id=case_id, kind='case_case'))
	if len(olist) == 0:
		return curent_case_name
	
	else:
		cname = Case.objects.get(id=olist[0].main_id).description
		curent_case_name = "%s_%s" % (cname, curent_case_name)
		return _get_full_case_name(olist[0].main_id, curent_case_name)
