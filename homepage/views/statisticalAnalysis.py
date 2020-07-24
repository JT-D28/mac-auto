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

from django.views.decorators.csrf import csrf_exempt
from manager.context import Me2Log as logger
from manager.operate.mongoUtil import Mongo


def statisticalAnalysis(request):
	return render(request, 'analysis.html', locals())


@csrf_exempt
def get_task_data(request):
	taskid = request.POST.get('taskid')
	node = request.POST.get('node')
	x = Mongo.taskinfo()[taskid].find_one()
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



@csrf_exempt
def getnodes(request):
	kind, id = request.POST.get('nodeid').split("_")
	taskid = request.POST.get('taskid')
	x = Mongo.taskinfo()[taskid].find_one()
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
	taskid = request.POST.get('taskid')
	stepid = Order.objects.get(follow_id=id, kind__contains='step_business', isdelete=0).main_id
	res = Mongo.logspilt()[taskid].find_one({'businessid':id,'stepid':str(stepid)})['info']
	return JsonResponse({'code': 0, 'data': res})
