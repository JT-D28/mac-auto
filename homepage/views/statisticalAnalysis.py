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
def get_task_data(request):
	planid = request.POST.get('planid')
	taskid = request.POST.get('taskid')
	node = request.POST.get('node')
	logname = BASE_DIR + "/logs/taskinfo/" + taskid + ".log"
	if os.path.exists(logname):
		with open(logname, 'r', encoding='utf-8') as f:
			x = json.load(f)
		if node:
			type, id = node.split("_")
			if type == 'plan':
				casesdata = x['root']
			elif type == 'business':
				stepid = Order.objects.get(follow_id=id, kind='step_business', isdelete=0).main_id
				tps = x['step_' + str(stepid)]
				for tp in tps:
					tpid = tp['id']
					if str(tpid) == str(id):
						casesdata = [tp]
						break
			else:
				casesdata = x[node]
		else:
			casesdata = x['root']
		if request.POST.get('viewkind') == 'fail':
			for i in range(len(casesdata) - 1, -1, -1):
				if casesdata[i].get('case_success_rate', 0) == 100.0 or casesdata[i].get('state', '') == 'omit':
					casesdata.pop(i)

		return JsonResponse({'code': 0, 'taskinfo': x['info'], 'casesdata': casesdata})
	else:
		return JsonResponse({'code': 1, 'casesdata': ''})


@csrf_exempt
def getnodes(request):
	kind, id = request.POST.get('nodeid').split("_")
	taskid = request.POST.get('taskid')
	logname = BASE_DIR + "/logs/taskinfo/" + taskid + ".log"
	with open(logname, 'r', encoding='utf-8') as f:
		x = json.load(f)
		data = x[kind + '_' + id]
	if request.POST.get('viewkind') == 'fail':
		for i in range(len(data) - 1, -1, -1):
			state = data[i].get('state', None)
			rate = data[i].get('case_success_rate', None)
			print(state, rate)
			if rate == 100.0:
				data.pop(i)
			elif state in ['omit', 'success']:
				data.pop(i)
	return JsonResponse({'code': 0, 'data': data})


@csrf_exempt
def geterrorinfo(request):
	id = request.POST.get('id').split("_")[1]
	state = request.POST.get('state')
	taskid = request.POST.get('taskid')
	bname = request.POST.get('name')
	logname = BASE_DIR + "/logs/deal/" + taskid + ".log"
	stepid = Order.objects.get(follow_id=id, kind__contains='step_business', isdelete=0).main_id
	stepname = Step.objects.get(id=stepid).description
	if os.path.exists(logname):
		with open(logname, 'r', encoding='utf-8') as f:
			res = f.read()
		ress = res.split("========")
		pattern = re.compile('开始执行步骤.*?' + stepname.replace('(', '\(').replace(')', '\)').replace('[','\[') + '.*?测试点\[.*?id=\'business_' + id + '.*?' + bname.replace(
			'(', '\(').replace(')', '\)').replace('[', '\[') + '.*?<br>')
		pattern1 = re.compile('步骤执行结果.*?{}'.format(state))
		res = '未匹配到日志记录，你可以试试下载并且查看完整日志！' if state != 'skip' else '该测试点被跳过'
		for i in ress:
			if pattern.search(i) and pattern1.search(i):
				res = i
				break
	else:
		res = '日志可能还没处理完成，请稍等！'
	return JsonResponse({'code': 0, 'data': res})
